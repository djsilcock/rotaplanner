import {
  createSignal,
  createEffect,
  onCleanup,
  children,
  createMemo,
  createContext,
  Index,
  splitProps,
  mergeProps,
  useContext,
  ErrorBoundary,
  onMount,
} from "solid-js";
import { createStore, reconcile } from "solid-js/store";
import { For, Show, Dynamic } from "solid-js/web";
import {
  startOfDay,
  parse,
  isValid,
  format,
  eachWeekOfInterval,
  lastDayOfMonth,
  addDays,
} from "date-fns";
import { createForm } from "./forms";
import { formSubscriptionItems } from "final-form";

import styles from "./ui.module.css";

export function Field(props) {
  const fieldstate = createMemo(() =>
    (
      props.form ||
      useForm()?.form ||
      console.warn("no form registered")
    ).registerField(props.name)
  );

  return (
    <Show when={fieldstate().name && fieldstate()} keyed>
      {props.children}
    </Show>
  );
}

export function TextField(props) {
  return <InputField type="text" {...props} />;
}

export function TimeField(props) {
  return <InputField type="time" {...props} />;
}
export function FormRow(props) {
  return (
    <div class={styles.formRow}>
      <Dynamic component={props.element || "label"} class={styles.fieldLabel}>
        <span>{props.label}</span>
        <div>{props.children}</div>
      </Dynamic>
    </div>
  );
}
function ErrorMessage(props) {
  return (
    <Show when={props.errors}>
      <div></div>
      <div class={styles.fieldError}>{props.errors.join(",")}</div>
    </Show>
  );
}

export function InputField(props) {
  return (
    <Field {...props}>
      {(field) => (
        <input
          type={props.type}
          onBlur={field.blur}
          onChange={(e) => field.change(e.target.value)}
          value={field.value}
        />
      )}
    </Field>
  );
}
export function SelectField(props) {
  const [local, remaining] = splitProps(props, ["multiple"]);
  return (
    <Show when={local.multiple} fallback={<SelectSingle {...remaining} />}>
      <MultiSelect {...remaining} />
    </Show>
  );
}
export function SelectSingle(props) {
  const resolved = children(() => props.children);
  const options = createMemo(
    () =>
      props.options?.map((o) => <option value={o.value}>{o.label}</option>) ??
      resolved
  );
  return (
    <select
      type={props.type}
      onBlur={(e) => props.onBlur?.(e.target.value)}
      onChange={(e) => props.onChange?.(e.target.value)}
      value={props.value}
    >
      {options}
    </select>
  );
}
const FormContext = createContext();
export function useForm() {
  const form = useContext(FormContext);
  console.log("form", form);
  return form;
}
export function Form(props) {
  const [local, rest] = splitProps(props, ["children"]);
  const [formState, setFormState] = createStore();
  const [formReady, setFormReady] = createSignal(false);
  const form = createForm(rest);
  const unsubscribe = form.subscribe((state) => {
    setFormState(reconcile(state));
    setFormReady(true);
  }, Object.fromEntries(formSubscriptionItems.map((i) => [i, true])));
  onCleanup(unsubscribe);
  return (
    <form>
      <FormContext.Provider value={{ form, state: formState }}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            form.submit();
          }}
        >
          <Show when={formReady() && { form, state: formState }} keyed>
            {local.children}
          </Show>
        </form>
      </FormContext.Provider>
    </form>
  );
}

export function DateField(props) {
  const [dropdown, setDropdown] = createSignal(false);
  const [year, setYear] = createSignal(0);
  const [month, setMonth] = createSignal(0);
  const [ref, setRef] = createSignal(null);
  const [value, setValue] = createSignal(props.value || startOfDay(new Date()));
  let eventListener;
  const notifyChange = () => {
    props.onChange?.(value());
  };
  const handleChange = (e) => {
    const oldValue = e.target.value;
    const newValue = oldValue.replace(/\W/g, "-");
    setDropdown(false);
    for (let pattern of [
      "yyyy-M-d",
      "d-M-yyyy",
      "d-M-yy",
      "d-MMM-yyyy",
      "d-MMM-yy",
      "do-MMM-yyyy",
      "do-MMM-yy",
    ]) {
      const newDate = parse(newValue, pattern, new Date());

      if (isValid(newDate)) {
        setValue(newDate);
        notifyChange();
        return;
      }
    }
    e.target.value = format(value(), "d/M/yyyy");
  };
  createEffect(() => {
    const eventListener = (e) => {
      if (ref() && ref().contains(e.target)) {
        if (!dropdown()) {
          setYear(value().getFullYear());
          setMonth(value().getMonth());
          setDropdown(true);
        }
      } else {
        setDropdown(false);
      }
    };
    document.addEventListener("click", eventListener);

    onCleanup(() => document.removeEventListener("click", eventListener));
  });
  return (
    <div class={styles.dropdownContainer} ref={setRef}>
      <input
        type="text"
        onChange={handleChange}
        value={format(value(), "d/M/yyyy")}
      />

      <Show when={dropdown()}>
        <div class={styles.dateDropdown}>
          <div>
            <select value={month()} onChange={(e) => setMonth(e.target.value)}>
              <For
                each={[
                  "Jan",
                  "Feb",
                  "Mar",
                  "Apr",
                  "May",
                  "Jun",
                  "Jul",
                  "Aug",
                  "Sep",
                  "Oct",
                  "Nov",
                  "Dec",
                ]}
              >
                {(month, i) => <option value={i()}>{month}</option>}
              </For>
            </select>
            <select value={year()} onChange={(e) => setYear(e.target.value)}>
              <For each={[2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]}>
                {(y) => <option value={y}>{y}</option>}
              </For>
            </select>
          </div>
          <table>
            <For
              each={eachWeekOfInterval({
                start: new Date(year(), month(), 1),
                end: lastDayOfMonth(new Date(year(), month(), 1)),
              })}
            >
              {(wk) => (
                <tr>
                  <For each={[0, 1, 2, 3, 4, 5, 6].map((i) => addDays(wk, i))}>
                    {(i) => (
                      <td
                        classList={{
                          [styles.dateCell]: !props.shouldDisable?.(i),
                          [styles.notThisMonth]: month() != i.getMonth(),
                          [styles.isToday]: i.valueOf() == value().valueOf(),
                          [styles.dateDisabled]: props.shouldDisable?.(i),
                        }}
                        title={`${value()} ${i}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setDropdown(false);
                          if (props.shouldDisable?.(i)) return;
                          setValue(i);
                          notifyChange();
                        }}
                      >
                        {i.getDate()}
                      </td>
                    )}
                  </For>
                </tr>
              )}
            </For>
          </table>
        </div>
      </Show>
    </div>
  );
}

export function MultiSelect(props) {
  const resolvedChildren = children(() => props.children);
  const options = createMemo(() => props.options || resolvedChildren());
  const [values, setValues] = createStore({});
  const notifyChange = () => {
    const newval = Object.keys(values).filter((k) => values[k]);
    console.log(newval);
    props.onChange?.(newval);
  };
  createEffect(() => {
    options().forEach((option) => {
      setValues(option.value, (props.value || []).includes(option.value));
    });
  });
  createEffect(() => console.log(JSON.stringify(values)));
  const optionChips = createMemo(() =>
    options().map((option) => (
      <div
        classList={{
          [styles.optionChip]: true,
          [styles.displayNone]: !values[option.value],
        }}
      >
        {option.innerText ?? option.label}
        <a
          class={styles.closeButton}
          onClick={() => {
            setValues(option.value, false);
            notifyChange();
          }}
        >
          {" "}
          X
        </a>
      </div>
    ))
  );
  const [dropdown, setDropdown] = createSignal(false);
  createEffect(() => console.log("dropdown", dropdown()));
  const [selected, setSelected] = createSignal(0);
  const [ref, setRef] = createSignal();

  const registerHandlers = (ref) => {
    setRef(ref);
    const clickaway = (e) => {
      if (!ref.contains(e.target)) {
        setDropdown(false);
      }
    };
    document.addEventListener("click", clickaway);
    onCleanup(() => document.removeEventListener("click", clickaway));
    ref.addEventListener("click", () => {
      if (!dropdown()) {
        setSelected(-1);
        setDropdown(true);
        props.onFocus?.();
      }
    });
    ref.addEventListener("keydown", (e) => {
      if (e.key == "ArrowDown") {
        if (ref().contains(document.activeElement)) {
          if (document.activeElement.matches("input")) {
            ref()
              .querySelector(
                `.${styles.dropdownOption}:not(.${styles.displayNone})`
              )
              ?.focus();
            return;
          }
          let currentElement = document.activeElement.nextElementSibling;
          while (currentElement?.matches(`.${styles.displayNone}`)) {
            currentElement = currentElement.nextElementSibling;
          }
          (currentElement ?? ref().querySelector("input")).focus?.();
        }
      }
      if (e.key == "ArrowUp") {
        if (ref().contains(document.activeElement)) {
          let currentElement = document.activeElement.previousElementSibling;
          while (currentElement?.matches(`.${styles.displayNone}`)) {
            currentElement = currentElement.previousElementSibling;
          }
          (currentElement ?? ref().querySelector("input")).focus?.();
        }
      }
    });
  };

  const [filtervalue, setFilter] = createSignal("");
  const dropdownOpts = createMemo(() =>
    options().map((option) => (
      <div
        tabIndex={-1}
        classList={{
          [styles.dropdownOption]: true,
          [styles.displayNone]:
            values[option.value] ||
            !option.label?.toLowerCase().includes(filtervalue()?.toLowerCase()),
        }}
        data-value={option.value}
        onClick={() => {
          setValues(option.value, true);
          notifyChange();
          setFilter("");
        }}
        onkeydown={(e) => {
          if (e.key == " " || e.key == "Enter") {
            setValues(option.value, true);
            notifyChange();
            setFilter("");
            ref().querySelector("input").focus();
          }
        }}
        innerHTML={option.innerHTML ?? option.label}
      />
    ))
  );

  return (
    <div ref={registerHandlers}>
      <select multiple style={{ display: "none" }} ref={props.ref}>
        <For each={options()}>
          {(option) => (
            <option value={option.value} selected={values[option.value]} />
          )}
        </For>
      </select>
      <div class={styles.multiselectcontainer}>
        {optionChips()}
        <input
          value={filtervalue()}
          oninput={(e) => {
            setFilter(e.target.value);
          }}
        />

        <div>
          <Show when={dropdown()}>
            <div class={styles.dateDropdown}>
              <div>{dropdownOpts()}</div>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
}
