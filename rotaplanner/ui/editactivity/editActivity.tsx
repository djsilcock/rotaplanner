import {
  createEffect,
  createSignal,
  For,
  Show,
  createMemo,
  createResource,
  Switch,
  Match,
} from "solid-js";

import type { Activity, EditActivityApi, StaffAssignment } from "./types";

//polyfill for Temporal API
import { Temporal } from "@js-temporal/polyfill";
import {
  Combobox,
  TextField,
  ModularMultiCombobox,
  DateField,
} from "../ui/formComponents";
import {
  createForm,
  Field,
  FormStore,
  getValue,
  getValues,
  custom,
  remove,
  insert,
  submit,
  FieldArrayStore,
  FieldArray,
} from "@modular-forms/solid";

import { createSubscribedSignal, getTypedApi } from "../../utils";
import { F } from "../../../rotarunner_ui/dist/assets/index-Di3oCNSn";

const api = getTypedApi<EditActivityApi>();

import { RuleBuilder } from "./rule_builder";

export default function EditActivityWrapper() {
  const [activityId] = createSubscribedSignal<string>("activityId");
  const [activity] = createResource(activityId, (id: string) =>
    api().get_activity(id),
  );
  return (
    <Show when={activity()} fallback={<div>Loading...</div>}>
      <EditActivity
        activity={activity()!}
        onClose={() => window.history.back()}
        locationOptions={[]}
      />
    </Show>
  );
}

export function EditActivity(props: {
  activity: Activity;
  onClose: () => void;
  locationOptions: { value: string; label: string }[];
}) {
  const [form, components] = createForm<Activity & Record<string, any>>({
    initialValues: props.activity,
  });
  createEffect(() => {
    console.log("Form values", getValues(form));
  });

  const startAsTemporal = createMemo(() => {
    const start = getValue(form, "activity_start");
    return start ? Temporal.PlainDateTime.from(start) : null;
  });
  const finishAsTemporal = createMemo(() => {
    const finish = getValue(form, "activity_finish");
    return finish ? Temporal.PlainDateTime.from(finish) : null;
  });
  const duration = createMemo(() => {
    const start = startAsTemporal();
    const finish = finishAsTemporal();
    if (!start || !finish) return 0;
    return start.until(finish, { largestUnit: "minutes" }).minutes;
  });
  const [availablePeople] = createResource(
    () => props.activity.id,
    (activityId: string) =>
      api().available_for_timeslot({ activity_id: activityId }),
  );
  return (
    <>
      <components.Form
        onSubmit={(values) => {
          console.log("Submitting form with values", values);
          api().update_activity(values);
        }}
      >
        <div>
          <components.Field name="id" type="string">
            {(field, props) => <input type="hidden" value={field.value} />}
          </components.Field>
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
        <components.Field name="activity_start" type="string" validateOn="blur">
          {(field, props) => (
            <TextField
              field={field}
              props={props}
              type="datetime-local"
              label="Activity start"
            />
          )}
        </components.Field>
        <components.Field
          name="activity_finish"
          type="string"
          validateOn="blur"
          validate={custom((value) => {
            const start = getValue(form, "activity_start");
            console.log("Validating activity finish", { value, start });
            if (!start || !value) return true;
            return Temporal.PlainDateTime.compare(value!, start!) > 0;
          }, "Activity finish must be after activity start")}
        >
          {(field, props) => (
            <TextField
              field={field}
              props={props}
              type="datetime-local"
              label="Activity finish"
            />
          )}
        </components.Field>
        Assignments:
        <div>
          <components.FieldArray name="assignments">
            {(assignmentFieldArray) => {
              const assignments = () =>
                (getValues(form, "assignments") || []).map(
                  (a) => a!.staff,
                ) as string[];
              createEffect(() => {
                console.log("Current assignments", assignments());
              });
              const options = createMemo(() => {
                const available: {
                  value: string;
                  label: string;
                  textValue?: string;
                }[] = [];
                const assigned: {
                  value: string;
                  label: string;
                  textValue?: string;
                  disabled?: boolean;
                }[] = [];
                availablePeople()?.forEach((option) => {
                  if (option.existing_activity) {
                    assigned.push({
                      textValue: option.staff.name,
                      label:
                        option.staff.name +
                        " (assigned to " +
                        option.existing_activity +
                        ")",
                      value: option.staff.id!,
                    });
                  } else {
                    available.push({
                      value: option.staff.id!,
                      label: option.staff.name,
                      textValue: option.staff.name,
                    });
                  }
                });
                return [
                  { label: "Available", options: available },
                  { label: "Assigned", options: assigned },
                ];
              });
              return (
                <table>
                  <For each={assignmentFieldArray.items}>
                    {(assignmentField, assignmentIndex) => (
                      <tr>
                        <td>
                          <components.Field
                            type="number"
                            name={`${assignmentFieldArray.name}.${assignmentIndex()}.id`}
                          >
                            {(field, props) => (
                              <input type="hidden" value={field.value} />
                            )}
                          </components.Field>

                          <components.Field
                            name={`${assignmentFieldArray.name}.${assignmentIndex()}.staff`}
                            type="string"
                          >
                            {(field, props) => (
                              <div>
                                <select {...props}>
                                  <For each={options()}>
                                    {(category) => (
                                      <optgroup label={category.label}>
                                        <For each={category.options}>
                                          {(option) => (
                                            <option
                                              value={option.value}
                                              disabled={
                                                option.value !== field.value &&
                                                assignments().includes(
                                                  option.value,
                                                )
                                              }
                                              selected={
                                                field.value === option.value
                                              }
                                            >
                                              {option.label}
                                            </option>
                                          )}
                                        </For>
                                      </optgroup>
                                    )}
                                  </For>
                                </select>
                              </div>
                            )}
                          </components.Field>
                        </td>
                        <td>
                          <components.Field
                            name={`${assignmentFieldArray.name}.${assignmentIndex()}.availability_type`}
                            type="string"
                          >
                            {(field, props) => {
                              const availabilityTypes = createMemo(
                                () =>
                                  availablePeople()?.find(
                                    (option) =>
                                      option.staff.id ===
                                      getValue(
                                        form,
                                        `${assignmentFieldArray.name}.${assignmentIndex()}.staff`,
                                      ),
                                  )?.availability_type || [],
                              );
                              return (
                                <select {...props}>
                                  <For each={availabilityTypes()}>
                                    {(type) => (
                                      <option
                                        value={type}
                                        selected={field.value === type}
                                      >
                                        {type}
                                      </option>
                                    )}
                                  </For>
                                </select>
                              );
                            }}
                          </components.Field>
                        </td>
                        <td>
                          <button
                            type="button"
                            onClick={() => {
                              remove(form, "assignments", {
                                at: assignmentIndex(),
                              });
                            }}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    )}
                  </For>
                </table>
              );
            }}
          </components.FieldArray>
        </div>
      </components.Form>

      <button
        on:click={() => {
          submit(form);
          console.log(getValues(form));
        }}
      >
        Save
      </button>
      <RuleBuilder />
    </>
  );
}

interface RuleGroupType {
  groupName: string;
  form: FormStore;
}

function RuleGroup<F>(props: RuleGroupType) {
  return (
    <div>
      <Field
        of={props.form}
        name={`${props.groupName}.groupType`}
        type="string"
      >
        {(groupTypeField, props) => (
          <select {...props}>
            <option value="and" selected={groupTypeField.value === "and"}>
              All of these rule must match
            </option>
            <option value="or" selected={groupTypeField.value === "or"}>
              Any of these rules must match
            </option>
            <option value="not" selected={groupTypeField.value === "not"}>
              None of these rules may match
            </option>
          </select>
        )}
      </Field>
      <div>Rules</div>
      <FieldArray of={props.form} name={`${props.groupName}.rules`}>
        {(groupArray) => (
          <For each={groupArray.items} fallback={"No entries"}>
            {(group, index) => (
              <div>
                <Field
                  of={props.form}
                  name={`${props.groupName}.groups.${index()}.ruleType`}
                  type="string"
                >
                  {(ruleTypeField, props) => (
                    <select {...props}>
                      <option
                        value="WEEKLY"
                        selected={ruleTypeField.value === "WEEKLY"}
                      >
                        Weekly (Every n weeks)
                      </option>
                      <option
                        value="DAILY"
                        selected={ruleTypeField.value === "DAILY"}
                      >
                        Daily (Every n days)
                      </option>
                      <option
                        value="MONTHLY"
                        selected={ruleTypeField.value === "MONTHLY"}
                      >
                        Monthly (Every n months on fixed date)
                      </option>
                      <option
                        value="WEEKINMONTH"
                        selected={ruleTypeField.value === "WEEKINMONTH"}
                      >
                        Monthly (Every n months on weekday pattern eg 1st
                        Monday)
                      </option>
                      <option
                        value="DATETAG"
                        selected={ruleTypeField.value === "DATETAG"}
                      >
                        Tagged dates eg public holiday
                      </option>
                      <option
                        value="GROUP"
                        selected={ruleTypeField.value === "GROUP"}
                      >
                        Group
                      </option>
                    </select>
                  )}
                </Field>
                <Switch>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) === "GROUP"
                    }
                  >
                    <RuleGroup
                      groupName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) == "WEEKLY"
                    }
                  >
                    <WeeklyRule
                      ruleName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) == "DAILY"
                    }
                  >
                    <DailyRule
                      ruleName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) == "MONTHLY"
                    }
                  >
                    <MonthlyRule
                      ruleName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) == "WEEKINMONTH"
                    }
                  >
                    <WeekInMonthRule
                      ruleName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match
                    when={
                      getValue(
                        props.form,
                        `${props.groupName}.groups.${index()}.ruleType`,
                      ) == "DATETAG"
                    }
                  >
                    <DatetagRule
                      ruleName={`${props.groupName}.groups.${index()}`}
                      form={props.form}
                    />
                  </Match>
                  <Match when={true}>
                    <div>Unknown rule type</div>
                  </Match>
                </Switch>
              </div>
            )}
          </For>
        )}
      </FieldArray>
      <button
        type="button"
        onClick={() =>
          props.form.pushFieldValue(`${props.groupName}.rules`, {
            ruleType: "WEEKLY",
            weekdays: [],
            weekNumbers: [],
            months: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
          })
        }
      >
        Add rule
      </button>
    </div>
  );
}

function WeeklyRule(props: { ruleName: string; form: FormStore }) {
  const ruledef = createMemo(() => getValue(props.form, props.ruleName) || {});
  return (
    <div>
      <Field of={props.form} name={`${props.ruleName}.weekDay`} type="string">
        {(field, props) => (
          <select {...props}>
            <option value={0}>Monday</option>
            <option value={1}>Tuesday</option>
            <option value={2}>Wednesday</option>
            <option value={3}>Thursday</option>
            <option value={4}>Friday</option>
            <option value={5}>Saturday</option>
            <option value={6}>Sunday</option>
          </select>
        )}
      </Field>
      <Field of={props.form} name={`${props.ruleName}.repeats`}>
        {(field, props) => (
          <select {...props}>
            <option value={1}>1 week</option>
            <option value={2}>2 weeks</option>
            <option value={3}>3 weeks</option>
            <option value={4}>4 weeks</option>
            <option value={5}>5 weeks</option>
            <option value={6}>6 weeks</option>
            <option value={7}>7 weeks</option>
            <option value={8}>8 weeks</option>
          </select>
        )}
      </Field>
      <For
        each={Array.from(
          { length: getValue(props.form, `${props.ruleName}.repeats`) || 0 },
          (x, i) => i + 1,
        )}
      >
        {(index) => (
          <Field
            of={props.form}
            name={`${props.ruleName}.weekNumbers`}
            type="number[]"
          >
            {(field, props) => (
              <label>
                <input
                  {...props}
                  type="checkbox"
                  value={index}
                  checked={(field.value! as number[])?.includes(index)}
                />
                {index}
              </label>
            )}
          </Field>
        )}
      </For>
    </div>
  );
}
function MonthlyRule(props: { ruleName: string; form: FormStore }) {
  return (
    <div>
      <Field of={props.form} name={`${props.ruleName}.ruleType`} type="string">
        {(field, props) => (
          <select {...props}>
            <For each={Array.from({ length: 31 }, (x, i) => i + 1)}>
              {(day) => <option value={day}>{day}</option>}
            </For>
          </select>
        )}
      </Field>

      <Field of={props.form} name={`${props.ruleName}.repeats`}>
        {(field, props) => (
          <select {...props}>
            <option value={1}>1 month</option>
            <option value={2}>2 months</option>
            <option value={3}>3 months</option>
            <option value={4}>4 months</option>
            <option value={5}>5 months</option>
            <option value={6}>6 months</option>
            <option value={7}>7 months</option>
            <option value={8}>8 months</option>
            <option value={9}>9 months</option>
            <option value={10}>10 months</option>
            <option value={11}>11 months</option>
            <option value={12}>12 months</option>
          </select>
        )}
      </Field>
      <For
        each={Array.from(
          { length: getValue(props.form, `${props.ruleName}.repeats`) || 0 },
          (x, i) => i + 1,
        )}
      >
        {(index) => (
          <Field
            of={props.form}
            name={`${props.ruleName}.monthNumbers`}
            type="number[]"
          >
            {(field, props) => (
              <label>
                <input
                  {...props}
                  type="checkbox"
                  value={index}
                  checked={(field.value! as number[])?.includes(index)}
                />
                {index}
              </label>
            )}
          </Field>
        )}
      </For>
    </div>
  );
}

function WeekInMonthRule(props: { ruleName: string; form: FormStore }) {
  return (
    <div>
      <Field of={props.form} name={`${props.ruleName}.weekDay`} type="string">
        {(field, props) => (
          <select {...props}>
            <option value={0}>Monday</option>
            <option value={1}>Tuesday</option>
            <option value={2}>Wednesday</option>
            <option value={3}>Thursday</option>
            <option value={4}>Friday</option>
            <option value={5}>Saturday</option>
            <option value={6}>Sunday</option>
          </select>
        )}
      </Field>
      <Field
        of={props.form}
        name={`${props.ruleName}.weekOfMonth`}
        type="number"
      >
        {(field, props) => (
          <select {...props}>
            <option value={1}>1st</option>
            <option value={2}>2nd</option>
            <option value={3}>3rd</option>
            <option value={4}>4th</option>
            <option value={5}>5th</option>
            <option value={-1}>Last</option>
            <option value={-2}>Second last</option>
            <option value={-3}>Third last</option>
            <option value={-4}>Fourth last</option>
          </select>
        )}
      </Field>
      <Field of={props.form} name={`${props.ruleName}.repeats`} type="number">
        {(field, props) => (
          <select {...props}>
            <option value={1}>1 month</option>
            <option value={2}>2 months</option>
            <option value={3}>3 months</option>
            <option value={4}>4 months</option>
            <option value={5}>5 months</option>
            <option value={6}>6 months</option>
            <option value={7}>7 months</option>
            <option value={8}>8 months</option>
            <option value={9}>9 months</option>
            <option value={10}>10 months</option>
            <option value={11}>11 months</option>
            <option value={12}>12 months</option>
          </select>
        )}
      </Field>
      <For
        each={Array.from(
          { length: getValue(props.form, `${props.ruleName}.repeats`) || 0 },
          (x, i) => i + 1,
        )}
      >
        {(index) => (
          <Field
            of={props.form}
            name={`${props.ruleName}.monthNumbers`}
            type="number[]"
          >
            {(field, props) => (
              <label>
                <input
                  {...props}
                  type="checkbox"
                  value={index}
                  checked={(field.value! as number[])?.includes(index)}
                />
                {index}
              </label>
            )}
          </Field>
        )}
      </For>
    </div>
  );
}
function DailyRule(props: { ruleName: string; form: FormStore }) {
  return (
    <div>
      <Field of={props.form} name={`${props.ruleName}.repeats`} type="number">
        {(field, props) => (
          <select {...props}>
            <option value={1}>Every day</option>
            <option value={2}>Every 2 days</option>
            <option value={3}>Every 3 days</option>
            <option value={4}>Every 4 days</option>
            <option value={5}>Every 5 days</option>
            <option value={6}>Every 6 days</option>
            <option value={7}>Every 7 days</option>
            <option value={14}>Every 14 days</option>
            <option value={30}>Every 30 days</option>
          </select>
        )}
      </Field>
    </div>
  );
}
function DatetagRule(props: { ruleName: string; form: FormStore }) {
  return (
    <div>
      <Field of={props.form} name={`${props.ruleName}.date`} type="string">
        {(field, props) => <input type="date" {...props} />}
      </Field>
    </div>
  );
}
