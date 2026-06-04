import inspect
import typing
import types
import os
import sys
import pathlib
from functools import wraps
from pydantic import BaseModel, validate_call
from pydantic2ts import generate_typescript_defs
import json
from logging import getLogger

logger = getLogger(__name__)
# --- The Composer Logic ---


def pythonify(maybe_model):
    if isinstance(maybe_model, BaseModel):
        return maybe_model.model_dump(mode="json")
    elif isinstance(maybe_model, (list, tuple, set)):
        return [pythonify(item) for item in maybe_model]
    elif isinstance(maybe_model, dict):
        return {k: pythonify(v) for k, v in maybe_model.items()}
    else:
        return maybe_model


class JSApi:
    """Base class for all API namespaces"""

    parent = None
    name = None

    def __set_name__(self, owner, name):
        self.parent = owner
        self.name = name

    @property
    def _root(self):
        return self.parent._root if self.parent else self

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        new_attrs = {}
        for name, attr_value in cls.__dict__.items():
            if inspect.isroutine(attr_value) and not name.startswith("_"):

                def wrap_method(func, name=name):
                    wrapped = validate_call(func)

                    @wraps(func)
                    def wrapper(self, *args, **kwargs):
                        logger = getLogger(func.__module__)
                        logger.info(
                            "Called method: %s with args: %s kwargs: %s",
                            func.__qualname__,
                            repr(args),
                            repr(kwargs),
                        )
                        ret_value = pythonify(wrapped(self, *args, **kwargs))
                        logger.info("Return value: %s", json.dumps(ret_value, indent=2))
                        return ret_value

                    return wrapper

                new_attrs[name] = wrap_method(attr_value, name)
        for name, wrapped in new_attrs.items():
            setattr(cls, name, wrapped)


# --- The Generator Logic ---


def clean_doc(doc, indent=2):
    return f"{' '*indent}/** {inspect.cleandoc(doc)} */\n" if doc else ""


def parse_type(hint, models_set):

    logger.info(
        "Parsing type hint: %s (origin: %s, args: %s)",
        hint,
        typing.get_origin(hint),
        typing.get_args(hint),
    )
    origin = typing.get_origin(hint)
    args = typing.get_args(hint)

    # --- Handle Tuples ---
    if origin in (tuple, typing.Tuple):
        if not args:
            return "any[]"

        # Handle variable length: tuple[int, ...] -> number[]
        if len(args) == 2 and args[1] is Ellipsis:
            return f"{parse_type(args[0], models_set)}[]"

        # Handle fixed length: tuple[int, str] -> [number, string]
        ts_types = [parse_type(a, models_set) for a in args]
        return f"[{', '.join(ts_types)}]"

    # --- Handle Unions (Union[A, B] or A | B) ---
    if origin in (typing.Union, types.UnionType) or (
        sys.version_info >= (3, 10) and isinstance(hint, typing._UnionGenericAlias)
    ):
        ts_types = [parse_type(a, models_set) for a in args]
        return f'({" | ".join(ts_types)})'

    # --- Handle Lists ---
    if origin in (list, typing.List, set, typing.Set):
        inner = parse_type(args[0], models_set) if args else "any"
        return f"{inner}[]"

    # --- Handle Dicts ---
    if origin in (dict, typing.Dict):
        k = parse_type(args[0], models_set) if args else "string"
        v = parse_type(args[1], models_set) if args else "any"
        return f"Record<{k}, {v}>"

    # --- Leaf Nodes (BaseModels & Primitives) ---
    if inspect.isclass(hint) and issubclass(hint, BaseModel):
        models_set.add(hint)
        return hint.__name__

    type_map = {
        str: "string",
        int: "number",
        float: "number",
        bool: "boolean",
        type(None): "void",
    }
    return type_map.get(hint, "any")


def generate_typescript(api_instance, interface_name, *output_filename_parts):
    models = set()
    structure = {}
    output_filename = pathlib.Path(*output_filename_parts)

    # 1. Walk the composed instance
    def walk(obj, indent=2):
        members = []
        for name, func in inspect.getmembers(obj):
            if name.startswith("_"):
                continue
            elif isinstance(func, JSApi):
                v = {"doc": clean_doc(func.__doc__, indent + 2)}
                members.append(
                    f"{v['doc']}{' '*indent}  {name}:{walk(func, indent + 2)}"
                )
            elif inspect.isroutine(func):
                try:
                    hints = typing.get_type_hints(func)
                    logger.info("Processing %s with hints: %s", name, hints)
                except:
                    logger.warning(
                        "Failed to get type hints for %s. Defaulting to 'any'.", name
                    )
                    hints = {}
                method_args = []
                ret_type = "any"
                for arg_name, hint in hints.items():
                    ts_type = parse_type(hint, models)
                    if arg_name == "return":
                        ret_type = ts_type
                    else:
                        method_args.append(f"{arg_name}: {ts_type}")

                v = {
                    "args": ", ".join(method_args),
                    "ret": ret_type,
                    "doc": clean_doc(func.__doc__, indent + 2),
                }
                members.append(
                    f"{v['doc']}{' '*indent}  {name}({v['args']}): Promise<{v['ret']}>;"
                )
        return (
            f"{' '*indent}{{\n{'\n'.join(members)}\n{' '*indent}}}" if members else "{}"
        )

    ts_interface = walk(api_instance)

    # 3. Write Pydantic Models (via Hub)
    random_suffix = os.urandom(4).hex()
    temp_hub_filename = f"temp_hub_{random_suffix}.py"
    with open(temp_hub_filename, "w") as f:
        for m in models:
            f.write(f"from {m.__module__} import {m.__name__}\n")

    generate_typescript_defs(
        module=f"temp_hub_{random_suffix}",
        output=output_filename,
        json2ts_cmd="npx json2ts",
    )
    os.remove(temp_hub_filename)

    with open(output_filename, "a") as f:
        f.write(f"\nexport interface {interface_name} \n")
        f.write(ts_interface)
