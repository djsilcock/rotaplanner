import {
  createEffect,
  createSignal,
  For,
  Show,
  Suspense,
  createMemo,
  JSX,
  Component,
  lazy,
  useContext,
  createContext,
  Accessor,
  Match,
  Switch,
  createResource,
} from "solid-js";
import { createStore, produce, reconcile } from "solid-js/store";
import {
  differenceInCalendarDays,
  parseISO,
  eachDayOfInterval,
} from "date-fns";
import { applyPatch } from "fast-json-patch";
import { ReactiveSet } from "@solid-primitives/set";

import styles from "./table.module.css";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import { Dynamic } from "solid-js/web";
import {
  getTableData,
  GetTableDataResponse,
  postUpdateLocation,
  postUpdateStaff,
  getAvailableForTimeslot,
  AvailableForTimeslotResult,
} from "../../../generated/client";

type Activity = GetTableDataResponse["activities"][number];

import { registerDraggable } from "../dragdrop";
import { useParams, createAsyncStore } from "@solidjs/router";
import { create, get, set } from "lodash";
import { Dialog } from "../../ui/components";
import { assert } from "chai";

//polyfill for Temporal API
import { Temporal } from "@js-temporal/polyfill";
import { Combobox, TextField } from "../../ui/formComponents";
import {
  createForm,
  getValue,
  getValues,
  setValue,
  custom,
  remove,
  insert,
  Field,
} from "@modular-forms/solid";

function AddPersonPopup(props: {
  assignment?: any;
  timeslotId: number;
  onAdd: (value: any) => void;
}) {
  const [isOpen, setIsOpen] = createSignal(false);
  const [availablePeople] = createResource<AvailableForTimeslotResult[]>(
    () => props.timeslotId,
    (timeslotId: number) =>
      getAvailableForTimeslot({ query: { timeslot_id: timeslotId } }).then(
        (res) => res.data,
      ),
  );
  return (
    <>
      <button on:click={() => setIsOpen(true)}>Add person</button>
      <Dialog title="Add Person" onClose={props.onClose} open={isOpen()}>
        {props.timeslotId}
        <Show when={isOpen() && availablePeople()} keyed>
          {(timeslotId) => {
            const [form, { Field, Form }] = createForm<{
              staff: string;
              availabilityBasis: string;
            }>();
            const options = createMemo(
              () =>
                availablePeople()?.map((option) => ({
                  label: option.availability_type,
                  items: option.available_staff.map((staff) => ({
                    value: staff.id,
                    label: staff.name,
                  })),
                })) ?? [],
            );
            return (
              <Form
                onSubmit={(values) => {
                  props.onAdd?.(values);
                  setIsOpen(false);
                }}
              >
                <Field name="staff" type="string">
                  {(field, props) => (
                    <div>
                      <Combobox
                        options={options()}
                        field={field}
                        props={props}
                        label="Person"
                      />
                      <button>Add</button>
                    </div>
                  )}
                </Field>
                <Field name="availabilityBasis" type="string">
                  {(field, props) => (
                    <div>
                      <Combobox
                        options={[
                          { value: "Basis 1", label: "Basis 1" },
                          { value: "Basis 2", label: "Basis 2" },
                        ]}
                        field={field}
                        props={props}
                        label="Availability Basis"
                      />
                      <button>Add</button>
                    </div>
                  )}
                </Field>
              </Form>
            );
          }}
        </Show>
      </Dialog>
    </>
  );
}

export function EditActivityDialog(props: {
  activity: Activity;
  onClose: () => void;
  locationOptions: { value: string; label: string }[];
}) {
  const [form, components] = createForm<Activity>({
    initialValues: props.activity,
  });
  createEffect(() => {
    console.log("Form values", getValues(form));
  });
  createEffect(() => {
    const timeslots = getValues(form, "timeslots", { shouldActive: false });
    if (timeslots.length < 2) return;
    for (let i = 1; i < timeslots.length; i++) {
      const prevStart = getValue(form, `timeslots.${i - 1}.start`);
      const currentStart = getValue(form, `timeslots.${i}.start`);

      setValue(form, `timeslots.${i - 1}.finish`, currentStart);
      console.log("Auto-updating finish time", {
        currentStart,
        prevStart,
      });
    }
  });
  return (
    <Dialog title="Edit Activity" onClose={props.onClose} open={true}>
      <components.Form>
        <div>
          <components.Field name="name" type="string">
            {(field, props) => (
              <TextField field={field} props={props} label="Name" />
            )}
          </components.Field>
          <components.Field name="location" type="string">
            {(field, thisprops) => (
              <Combobox
                field={field}
                props={thisprops}
                label="Location"
                options={props.locationOptions}
              />
            )}
          </components.Field>
        </div>
        <components.Field name="option" type="string">
          {(field, props) => (
            <Combobox
              field={field}
              props={props}
              label="Activity"
              description="Select an activity"
              options={[
                { value: "Option 1", label: "Option 1" },
                { value: "Option 2", label: "Option 2" },
              ]}
            />
          )}
        </components.Field>
        <components.FieldArray name="timeslots">
          {(timeslotFieldArray) => (
            <For each={timeslotFieldArray.items}>
              {(field, index) => {
                const startAsTemporal = createMemo(() => {
                  const start = getValue(
                    form,
                    `${timeslotFieldArray.name}.${index()}.start`,
                  );
                  return start ? Temporal.PlainDateTime.from(start) : null;
                });
                const finishAsTemporal = createMemo(() => {
                  const finish = getValue(
                    form,
                    `${timeslotFieldArray.name}.${index()}.finish`,
                  );
                  return finish ? Temporal.PlainDateTime.from(finish) : null;
                });
                const duration = createMemo(() => {
                  const start = startAsTemporal();
                  const finish = finishAsTemporal();
                  if (!start || !finish) return 0;
                  return start.until(finish, { largestUnit: "minutes" })
                    .minutes;
                });
                return (
                  <div>
                    <div>
                      <hr />
                      <components.Field
                        name={`${timeslotFieldArray.name}.${index()}.id`}
                        type="number"
                      >
                        {(field, props) => (
                          <input type="hidden" value={field.value} />
                        )}
                      </components.Field>
                      <components.Field
                        name={`${timeslotFieldArray.name}.${index()}.start`}
                        type="string"
                        validateOn="blur"
                        validate={custom((value) => {
                          if (index() === 0) return true; // no need to validate the first timeslot
                          const prevStart = getValue(
                            form,
                            `${timeslotFieldArray.name}.${index() - 1}.start`,
                          );
                          console.log("Validating finish time", {
                            value,
                            prevStart,
                          });
                          return (
                            Temporal.PlainDateTime.compare(value!, prevStart!) >
                            0
                          );
                        }, "Timeslot must start after the previous timeslot")}
                      >
                        {(field, props) => (
                          <TextField
                            field={field}
                            props={props}
                            type="datetime-local"
                            label={`Timeslot ${index() + 1}/${timeslotFieldArray.items.length} start`}
                          />
                        )}
                      </components.Field>
                      <button
                        disabled={index() === 0}
                        on:click={() => {
                          const currentFinish = getValue(
                            form,
                            `${timeslotFieldArray.name}.${index()}.finish`,
                          );

                          setValue(
                            form,
                            `${timeslotFieldArray.name}.${index()}.start`,
                            currentFinish,
                          );
                          remove(form, timeslotFieldArray.name, {
                            at: index(),
                          });
                        }}
                      >
                        Merge with previous
                      </button>
                      <button
                        disabled={duration() <= 2}
                        on:click={() => {
                          const currentStart = startAsTemporal();
                          const currentFinish = finishAsTemporal();
                          const newValue = { id: -1, start: "", finish: "" };

                          //find the middle point between currentStart and currentFinish

                          const middle = currentStart?.add({
                            minutes: Math.floor(duration() / 2),
                          });

                          Object.assign(newValue, {
                            start: middle?.toString() ?? "",
                            id: -1,
                            finish: currentFinish?.toString() ?? "",
                          });

                          insert(form, timeslotFieldArray.name, {
                            at: index() + 1,
                            value: newValue,
                          });
                        }}
                      >
                        Split
                      </button>
                    </div>
                    Assignments:
                    <div>
                      <components.FieldArray
                        name={`${timeslotFieldArray.name}.${index()}.assignments`}
                      >
                        {(assignmentFieldArray) => (
                          <For each={assignmentFieldArray.items}>
                            {(assignmentField, assignmentIndex) => (
                              <components.Field
                                name={`${assignmentFieldArray.name}.${assignmentIndex()}.staff`}
                              >
                                {(field, props) => (
                                  <div>
                                    {field.value}{" "}
                                    <button
                                      type="button"
                                      on:click={() =>
                                        remove(
                                          form,
                                          assignmentFieldArray.name,
                                          {
                                            at: assignmentIndex(),
                                          },
                                        )
                                      }
                                    >
                                      X
                                    </button>
                                  </div>
                                )}
                              </components.Field>
                            )}
                          </For>
                        )}
                      </components.FieldArray>
                    </div>
                    <AddPersonPopup
                      assignment={getValues(
                        form,
                        `timeslots.${index()}.assignments`,
                      )}
                      timeslotId={getValue(form, `timeslots.${index()}.id`)}
                      onAdd={(value) => {
                        insert(
                          form,
                          `${timeslotFieldArray.name}.${index()}.assignments`,
                          {
                            value,
                          },
                        );
                      }}
                    />
                    <components.Field
                      name={`${timeslotFieldArray.name}.${index()}.finish`}
                      type="string"
                      validateOn="blur"
                      validate={custom((value) => {
                        if (index() === 0) return true; // no need to validate the first timeslot
                        const currentStart = getValue(
                          form,
                          `${timeslotFieldArray.name}.${index()}.start`,
                        );
                        console.log("Validating finish time", {
                          value,
                          currentStart,
                        });
                        return (
                          Temporal.PlainDateTime.compare(
                            value!,
                            currentStart!,
                          ) > 0
                        );
                      }, "Timeslot finish must be after the start")}
                    >
                      {(field, props) => (
                        <Switch>
                          <Match
                            when={
                              index() === timeslotFieldArray.items.length - 1
                            }
                          >
                            <TextField
                              field={field}
                              props={props}
                              type="datetime-local"
                              label="Activity finish"
                            />
                          </Match>
                          <Match
                            when={index() < timeslotFieldArray.items.length - 1}
                          >
                            <input
                              type="hidden"
                              value={field.value}
                              {...props}
                              readOnly
                            />
                          </Match>
                        </Switch>
                      )}
                    </components.Field>
                  </div>
                );
              }}
            </For>
          )}
        </components.FieldArray>
      </components.Form>
    </Dialog>
  );
}
