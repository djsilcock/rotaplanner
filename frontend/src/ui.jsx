import {
  createSignal,
  createEffect,
  onCleanup,
  children,
  createMemo,
} from "solid-js";
import { For, Show } from "solid-js/web";
import {
  startOfDay,
  parse,
  isValid,
  format,
  eachWeekOfInterval,
  lastDayOfMonth,
  addDays,
} from "date-fns";

import styles from "./ui.module.css";

export function DateField(props) {
  const [dropdown, setDropdown] = createSignal(false);
  const [year, setYear] = createSignal(0);
  const [month, setMonth] = createSignal(0);
  const [ref, setRef] = createSignal(null);
  const [value, setValue] = createSignal(props.value || startOfDay(new Date()));
  let eventListener;
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
      console.log({ newValue, pattern, newDate });

      if (isValid(newDate)) {
        setValue(newDate);
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

    onCleanup(() => document.removeEventListener("click", e));
  });
  return (
    <props.form.Field name={props.name}>
      {(field) => (
        <div class={styles.formRow} ref={setRef}>
          <div class={styles.dropdownContainer}>
            <label class={styles.fieldLabel}>
              {props.label}
              <input
                type="text"
                onChange={handleChange}
                value={format(value(), "d/M/yyyy")}
              />
            </label>
            <Show when={dropdown()}>
              <div class={styles.dateDropdown}>
                <div>
                  <select
                    value={month()}
                    onChange={(e) => setMonth(e.target.value)}
                  >
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
                  <select
                    value={year()}
                    onChange={(e) => setYear(e.target.value)}
                  >
                    <For
                      each={[2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027]}
                    >
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
                        <For
                          each={[0, 1, 2, 3, 4, 5, 6].map((i) =>
                            addDays(wk, i)
                          )}
                        >
                          {(i) => (
                            <td
                              classList={{
                                [styles.dateCell]: true,
                                [styles.notThisMonth]: month() != i.getMonth(),
                                [styles.isToday]:
                                  i.valueOf() == value().valueOf(),
                              }}
                              title={`${value()} ${i}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                setDropdown(false);
                                setValue(i);
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
        </div>
      )}
    </props.form.Field>
  );
}
export function MultiSelect(props) {
  const resolved = children(() => props.children);
  const options = createMemo(() => props.options ?? resolved());
  const [dropdown, setDropdown] = createSignal(false);
  const [selected, setSelected] = createSignal(0);
  const [ref, setRef] = createSignal();
  createEffect(() => {
    const eventListener = (e) => {
      if (ref() && ref().contains(e.target)) {
        if (!dropdown()) {
          console.log("inside");
          setSelected(-1);
          setDropdown(true);
        }
      } else {
        console.log("outside");
        setDropdown(false);
      }
    };
    document.addEventListener("click", eventListener);

    onCleanup(() => document.removeEventListener("click", eventListener));
  });
  const [filtervalue, setFilter] = createSignal("");
  return (
    <props.form.Field name={props.name} type="array">
      {(field) => {
        createEffect((shouldNotRun) => {
          console.log("effect");
          ref();
          selected();
          if (shouldNotRun) return false;
          if (!ref()) return;
          if (selected() == -1) {
            ref().querySelector("input").focus();
            return;
          }
          console.log(
            ref(),
            `[data-value="${availableOptions()[selected()]?.value}"]`
          );
          ref()
            .querySelector(
              `[data-value="${availableOptions()[selected()]?.value}"]`
            )
            ?.focus();
          return;
        }, true);
        const selectedOptions = createMemo(() =>
          options()
            .filter((v) => field().state.value.includes(v.value))
            .map((o, i) => (
              <span class={styles.optionChip}>
                {o.innerText ?? o.label}
                <a
                  class={styles.closeButton}
                  onClick={() => field().removeValue(i)}
                >
                  {" "}
                  X
                </a>
              </span>
            ))
        );
        const availableOptions = createMemo(() =>
          options()
            .filter((v) => !field().state.value.includes(v.value))
            .filter((v) =>
              v.label?.toLowerCase().includes(filtervalue()?.toLowerCase())
            )
        );

        return (
          <div class={styles.formRow}>
            <label class={styles.fieldLabel} ref={setRef}>
              {props.label}
              <div
                onkeydown={(e) => {
                  if (
                    e.key == "ArrowDown" &&
                    selected() <= availableOptions().length
                  ) {
                    setSelected((s) => s + 1);
                  }
                  if (e.key == "ArrowUp" && selected() >= 0) {
                    setSelected((s) => s - 1);
                  }
                }}
              >
                <div class={styles.multiselectcontainer}>
                  {selectedOptions()}
                  <input
                    value={filtervalue()}
                    onkeydown={(e) => {
                      if (e.key == "Backspace") {
                        if (e.target.selectionStart == 0) {
                          field().removeValue(field().state.value.length - 1);
                        }
                      }
                    }}
                    oninput={(e) => {
                      setFilter(e.target.value);
                    }}
                  />

                  <div>
                    <Show when={dropdown()}>
                      <div class={styles.dateDropdown}>
                        <div>
                          <For each={availableOptions()}>
                            {(opt, i) => (
                              <div
                                tabIndex={-1}
                                class={styles.dropdownOption}
                                data-value={opt.value}
                                onClick={() => {
                                  field().pushValue(opt.value);
                                  setFilter("");
                                }}
                                onkeydown={(e) => {
                                  console.log(e.key);
                                  if (e.key == " " || e.key == "Enter") {
                                    field().pushValue(opt.value);
                                    setFilter("");
                                    ref().querySelector("input").focus();
                                  }
                                }}
                                innerHTML={opt.innerHTML ?? opt.label}
                              ></div>
                            )}
                          </For>
                        </div>
                      </div>
                    </Show>
                  </div>
                </div>
              </div>
            </label>
          </div>
        );
      }}
    </props.form.Field>
  );
}
