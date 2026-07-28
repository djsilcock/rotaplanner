import asyncio
import janus
import pydantic
from pydantic_core import ErrorDetails


class QuitRunner(Exception):
    """Custom exception to signal quitting the application."""


class TaskRunner:
    def __init__(self):
        self.task_queue = janus.Queue()
        self.task_group = None  # Will hold the asyncio.TaskGroup instance

    def wrap_callback(self, corofunction):
        def callback(*args, **kwargs):
            self.task_queue.sync_q.put(corofunction(*args, **kwargs))

        return callback

    def schedule(self, coroutine):
        self.task_queue.sync_q.put(coroutine)

    async def run(self):
        if self.task_group is not None:
            raise RuntimeError("TaskRunner is already running.")
        self.task_group = asyncio.TaskGroup()
        try:
            async with self.task_group as tg:
                while True:
                    task = await self.task_queue.async_q.get()
                    tg.create_task(task)
        except* QuitRunner:
            pass

    def abort(self):
        async def _abort():
            raise QuitRunner("TaskRunner aborted.")

        self.schedule(_abort())


def flatten(nested_dict_or_list, separator=".", tuple_keys=False):
    """
    Recursively flattens a nested dictionary or list into a flat dictionary with dot-separated keys.

    Args:
        nested_dict_or_list (dict or list): The nested dictionary or list to flatten.

    Returns:
        dict: A flat dictionary with dot-separated keys.
    """
    flat_dict = {}

    def _flatten(obj, *parent_keys):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _flatten(v, *parent_keys, k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _flatten(v, *parent_keys, i)
        else:
            if tuple_keys:
                flat_dict[tuple(parent_keys)] = obj
            else:
                flat_dict[separator.join(map(str, parent_keys))] = obj

    _flatten(nested_dict_or_list)
    return flat_dict


def unflatten(
    flat_dict, separator=".", convert_lists=True, fill_missing_indices_with_none=True
):
    """
    Converts a flat dictionary with dot-separated keys back into a nested dictionary.

    Args:
        flat_dict (dict): The flat dictionary to unflatten.

    Returns:
        dict: A nested dictionary.
    """
    nested_dict = {}
    for flat_key, value in flat_dict.items():
        if isinstance(flat_key, tuple):
            keys = flat_key
        else:
            keys = flat_key.split(separator)
        d = nested_dict
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value

    # crawl dictionary and convert any dicts with only integer keys to lists - some indices may be missing, so we need to fill in the gaps with None
    def _convert_to_list(d):
        if isinstance(d, dict):
            try:
                # Check if all keys are integers
                int_keys = sorted([int(k) for k in d.keys()])
                if fill_missing_indices_with_none:
                    int_keys = range(0, max(int_keys) + 1)

                return [_convert_to_list(d.get(str(i), None)) for i in int_keys]
            except ValueError:
                return {k: _convert_to_list(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [_convert_to_list(v) for v in d]
        else:
            return d

    if convert_lists:
        return _convert_to_list(nested_dict)
    return nested_dict


class ValidationResult[T: pydantic.BaseModel](pydantic.BaseModel):
    is_valid: bool
    errors: dict[tuple[int | str, ...], ErrorDetails] | None = None
    model_instance: T | None = None


def report_errors[T: pydantic.BaseModel](
    flat_dict: dict, schema: type[T]
) -> ValidationResult[T]:
    """
    Validates a flat dictionary against a Pydantic schema.

    Args:
        flat_dict (dict): The flat dictionary to validate.
        schema (type[T]): The Pydantic schema to validate against.

    Returns:
        ValidationResult: The result of the validation.
    """
    try:
        # Unflatten the flat dictionary
        nested_dict = unflatten(flat_dict)
        # Validate against the schema
        model_instance = schema.model_validate(nested_dict)
        return ValidationResult(is_valid=True, model_instance=model_instance)
    except pydantic.ValidationError as e:
        errors = {error["loc"]: error for error in e.errors()}
        return ValidationResult(is_valid=False, errors=errors)
