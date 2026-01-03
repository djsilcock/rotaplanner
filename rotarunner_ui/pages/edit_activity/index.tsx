import { Dynamic, Show } from "solid-js/web";
import { useParams } from "@solidjs/router";
import {
  For,
  Index,
  createMemo,
  createEffect,
  createSignal,
  createResource,
} from "solid-js";
import { Button } from "@suid/material";
import { Dialog, useDialogContext } from "../../ui/index.jsx";
import { SelectField, DateField, NumberField, TextField } from "../ui.jsx";
import { createForm, FormStore } from "@modular-forms/solid";
import styles from "./edit_activity_template.module.css";
import { createStore } from "solid-js/store";
import { FormRow } from "../ui.jsx";
import { createLazyLoadQuery } from "solid-relay";
import { graphql } from "relay-runtime";
import {
  editActivityQuery,
  editActivityQuery$data,
} from "./__generated__/editActivityQuery.graphql.js";
import {
  ActivityInput,
  DailyRecurrenceInput,
  editActivityMutation,
  MonthlyRecurrenceInput,
  RequirementInput,
  TimeSlotInput,
  WeekInMonthRecurrenceInput,
  WeeklyRecurrenceInput,
} from "./__generated__/editActivityMutation.graphql.js";
import * as fields from "../ui";

type DeepMutable<T> =
  // If T is a ReadonlyArray, make it mutable and recurse on its elements
  T extends ReadonlyArray<infer U>
    ? Array<DeepMutable<U>>
    : // If T is a readonly object, make all its properties mutable recursively
    T extends object
    ? { -readonly [K in keyof T]?: DeepMutable<T[K]> }
    : T; // Primitives remain unchanged

const ordinal = (index) => {
  const ordinals = ["th", "st", "nd", "rd"];
  const v = index % 100;
  return index + (ordinals[(v - 20) % 10] || ordinals[v] || ordinals[0]);
};

function RuleGroupA(props) {
  const form = useForm().form;
  const groupDef = form.registerField(props.name);
  let details;
  createEffect(() => {
    if (groupDef.isNew) {
      details.open = true;
      form().change(`${props.name}.isNew`, false);
    }
  });

  return (
    <div>
      <details ref={details}>
        <summary>
          <Field name={`${props.name}.groupType`}>
            {(field) => (
              <select
                onChange={(e) => field.change(e.target.value)}
                value={field.value}
              >
                <option value="and">All of these rule must match</option>
                <option value="or">Any of these rules must match</option>
                <option value="not">None of these rules may match</option>
              </select>
            )}
          </Field>
        </summary>
        <div class={styles.ruleBox}>
          <Index each={groupDef().value?.groups}>
            {(_, groupNo) => (
              <RuleGroup
                name={`${props.name}.groups.${groupNo}`}
                delete={() =>
                  form().mutators.remove(`${props.name}.groups`, groupNo)
                }
              />
            )}
          </Index>
          <Index each={groupDef().value?.rules}>
            {(_, ruleNo) => (
              <Rule
                name={`${props.name}.rules.${ruleNo}`}
                delete={() =>
                  form().mutators.remove(`${props.name}.groups`, groupNo)
                }
              />
            )}
          </Index>

          <div>
            <Show
              when={
                groupDef().value?.groups?.length +
                  groupDef().value?.rules?.length ==
                0
              }
            >
              <div>⚠️ This group has no members</div>
            </Show>
          </div>
          <div>
            <button
              type="button"
              onClick={() => {
                form().mutators.push(`${props.name}.groups`, {
                  groupType: "and",
                  rules: [],
                  groups: [],
                  isNew: true,
                });
              }}
            >
              Add group
            </button>
            <button
              type="button"
              onClick={() => {
                form().mutators.push(`${props.name}.rules`, {
                  isNew: true,
                  ruleType: "weekly",
                  cycleLength: 1,
                  weekdays: [1],
                  weekNumbers: [1],
                  months: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                });
              }}
            >
              Add rule
            </button>
          </div>
        </div>
      </details>
    </div>
  );
}

function RuleGroup(props) {
  const form = useForm().form;
  const [groupStore, setGroupStore] = createStore(props.group);
  let details;
  createEffect(() => {
    if (groupStore.isNew) {
      details.open = true;
      setGroupStore("isNew", false);
    }
  });

  return (
    <div>
      <details ref={details}>
        <summary>
          <select
            onChange={(e) => setGroupStore("groupType", e.target.value)}
            value={groupStore.groupType}
          >
            <option value="and">All of these rule must match</option>
            <option value="or">Any of these rules must match</option>
            <option value="not">None of these rules may match</option>
          </select>
          <Show when={props.delete}>
            <button onClick={() => props.delete()}>Delete group</button>
            <hr />
          </Show>
        </summary>
        <div class={styles.groupBox}>
          <Index each={groupStore.groups}>
            {(group, groupNo) => (
              <RuleGroup
                group={group()}
                delete={() =>
                  setGroupStore("groups", (grp) => grp.toSpliced(groupNo, 1))
                }
              />
            )}
          </Index>
          <Index each={groupStore.rules}>
            {(rule, ruleNo) => (
              <Rule
                rule={rule()}
                delete={() =>
                  setGroupStore("rules", (rules) => rules.toSpliced(ruleNo, 1))
                }
              />
            )}
          </Index>

          <Show when={groupStore.groups.length + groupStore.rules.length == 0}>
            <div>⚠️ This group has no members</div>
            <hr />
          </Show>

          <div>
            <button
              type="button"
              onClick={() => {
                setGroupStore("groups", groupStore.groups.length, {
                  groupType: "and",
                  rules: [],
                  groups: [],
                  isNew: true,
                });
              }}
            >
              Add group
            </button>
            <button
              type="button"
              onClick={() => {
                setGroupStore("rules", groupStore.rules.length, {
                  isNew: true,
                  ruleType: "weekly",
                  cycleLength: 1,
                  weekdays: [1],
                  weekNumbers: [1],
                  months: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                });
              }}
            >
              Add rule
            </button>
          </div>
        </div>
      </details>
    </div>
  );
}

function Rule(props) {
  let details;
  const [ruleDef, setRuleDef] = createStore(props.rule);
  const ruleDescription = createMemo(() => {
    switch (ruleDef.ruleType) {
      case "weekly":
        const days =
          ruleDef.weekdays
            .map(
              (day) =>
                [
                  "Monday",
                  "Tuesday",
                  "Wednesday",
                  "Thursday",
                  "Friday",
                  "Saturday",
                  "Sunday",
                ][day]
            )
            .join(", ") || "[no days selected]";
        if (ruleDef.cycleLength == 0) {
          return `${
            ruleDef.weekNumbers.map(ordinal).join(",") || "[no weeks selected]"
          } ${days}of the month`;
        } else if (ruleDef.cycleLength == 1) {
          return `Every ${days}`;
        } else {
          return `Week${
            ruleDef.weekNumbers.length > 1 ? "s" : ""
          } ${ruleDef.weekNumbers
            .map((n) => `${n}/${ruleDef.cycleLength}`)
            .join(",")}  weeks on ${days}`;
        }
      case "DAILY":
        return `Every ${ruleDef.cycleLength} days`;
      case "MONTHLY":
        return `Every ${ordinal(ruleDef.cycleLength)} day of the month`;
      case "DATETAG":
        return `Tagged days: ${ruleDef.tags.join(", ")}`;
      default:
        return "";
    }
  });
  createEffect(() => {
    if (ruleDef.isNew) {
      details.open = true;
      setRuleDef("isNew", undefined);
    }
  });

  return (
    <div>
      <details
        ref={details}
        className="rule-definition"
        name="rule-definition-box"
      >
        <summary className="description">
          {ruleDescription()}
          <button type="button" onClick={props.delete}>
            Delete this rule
          </button>
        </summary>
        <div className={styles.ruleBox}>
          <FormRow label="Type">
            <SelectField
              label="Type"
              onChange={(value) => setRuleDef("ruleType", value)}
              value={ruleDef.ruleType}
            >
              <option value="DAILY">Every n days</option>
              <option value="weekly">
                Days in week (eg every 3rd Monday; 1st Monday of month)
              </option>
              <option value="MONTHLY">
                Day in month (eg 1st of every month)
              </option>
              <option value="DATETAG">Tagged days</option>
            </SelectField>
          </FormRow>
          <Switch>
            <Match when={ruleDef.ruleType == "weekly"}>
              <FormRow label="Weekdays">
                <SelectField
                  multiple
                  label="Weekdays"
                  value={ruleDef.weekdays}
                  onChange={(v) => setRuleDef("weekdays", v)}
                  options={[
                    { value: 0, label: "Monday" },
                    { value: 1, label: "Tuesday" },
                    { value: 2, label: "Wednesday" },
                    { value: 3, label: "Thursday" },
                    { value: 4, label: "Friday" },
                    { value: 5, label: "Saturday" },
                    { value: 6, label: "Sunday" },
                  ]}
                  validators={{
                    onChange: ({ value }) =>
                      value.length > 0
                        ? undefined
                        : "Please select at least one weekday",
                  }}
                />
              </FormRow>
              <FormRow>
                <SelectField
                  onChange={(v) => setRuleDef("cycleLength", v)}
                  value={ruleDef.cycleLength}
                  label="Cycle Length"
                  options={[
                    { value: 0, label: "weeks of month" },
                    { value: 1, label: "every week" },
                    { value: 2, label: "2 weeks" },
                    { value: 3, label: "3 weeks" },
                    { value: 4, label: "4 weeks" },
                    { value: 5, label: "5 weeks" },
                    { value: 6, label: "6 weeks" },
                    { value: 7, label: "7 weeks" },
                    { value: 8, label: "8 weeks" },
                  ]}
                />
              </FormRow>
              <FormRow>
                <SelectField
                  multiple
                  onChange={(val) => setRuleDef("weekNumbers", val)}
                  value={ruleDef.weekNumbers}
                  label="Week Numbers"
                  validators={{
                    onChange: ({ value }) =>
                      value.length > 0
                        ? undefined
                        : "Please select at least one week",
                  }}
                  options={Array.from(
                    { length: Number(ruleDef.cycleLength) || 5 },
                    (_, index) => ({
                      value: index + 1,
                      label: ordinal(index + 1),
                    })
                  )}
                />
              </FormRow>
              <FormRow>
                <SelectField
                  multiple
                  onChange={(value) => setRuleDef("months", value)}
                  value={ruleDef.months}
                  label="Months"
                  validators={{
                    onChange: ({ value }) =>
                      value.length > 0
                        ? undefined
                        : "Please select at least one month",
                  }}
                  options={[
                    { value: 0, label: "January" },
                    { value: 1, label: "February" },
                    { value: 2, label: "March" },
                    { value: 3, label: "April" },
                    { value: 4, label: "May" },
                    { value: 5, label: "June" },
                    { value: 6, label: "July" },
                    { value: 7, label: "August" },
                    { value: 8, label: "September" },
                    { value: 9, label: "October" },
                    { value: 10, label: "November" },
                    { value: 11, label: "December" },
                  ]}
                />
              </FormRow>
            </Match>
          </Switch>
          <FormRow>
            <DateField
              label="Week 1 starts"
              name="fred"
              shouldDisable={(d) => d.getDay() != 1}
              value={ruleDef.anchorDate}
              onChange={(val) => setRuleDef("anchorDate", val)}
            />
          </FormRow>

          <div>bla</div>
          <div>bla</div>
          <div>bla</div>
        </div>
      </details>
    </div>
  );
}

function EditActivityTemplate(props) {
  const [store, setStore] = createStore(
    props.activity == "new"
      ? {
          ruleset: { groupType: "and", groups: [], rules: [] },
          activity_tags: [],
        }
      : {}
  );

  return (
    <main>
      <pre>{JSON.stringify(store)}</pre>
      <Form onSubmit={(val) => console.log(val)}>
        <h4>Edit activity</h4>
        <div id="template-editor-settings" class={styles.formContainer}>
          <FormRow label="Activity Name">
            <input
              name="activity_name"
              value={store.activity_name}
              onchange={(e) => setStore("activity_name", e.target.value)}
            />
          </FormRow>
          <FormRow label="This activity occurs:">
            <div id="ruleset-container">
              <RuleGroup name="ruleset" group={store.ruleset} />
            </div>
          </FormRow>
          <FormRow label="Start time">
            <input
              type="time"
              value={store.start_time}
              onchange={(e) => setStore("start_time", e.target.value)}
            />
          </FormRow>
          <FormRow label="Finish time">
            <input
              type="time"
              value={store.start_time}
              onchange={(e) => setStore("start_time", e.target.value)}
            />
          </FormRow>
          <FormRow label="Tags">
            <MultiSelect
              name="activity_tags"
              value={store.activity_tags}
              onChange={(val) => setStore("activity_tags", val)}
            >
              <option value="URO">Urology</option>
              <option value="ENT">ENT</option>
            </MultiSelect>
          </FormRow>
          <FormRow label="Location">
            <SelectField
              value={store.location}
              onChange={(val) => setStore("location", val)}
            >
              <option>Theatre 1</option>
              <option>Theatre 1</option>
              <option>Theatre 1</option>
              <option>Theatre 1</option>
            </SelectField>
          </FormRow>
          <FormRow label="Requirements" element="div">
            <div>
              <For
                each={store.requirements}
                fallback={<div>⚠️ No requirements have been set</div>}
              >
                {(req, i) => {
                  const [thisReq, setThisReq] = createStore(req);
                  return (
                    <div className={styles.requirement}>
                      <pre>{JSON.stringify(req)}</pre>
                      <FormRow label="Skills">
                        <MultiSelect
                          value={req.skills}
                          onChange={(val) => setThisReq("skills", val)}
                          options={[
                            { value: "iac", label: "IAC" },
                            { value: "listrunner", label: "Listrunner" },
                            { value: "regional", label: "Regional" },
                            { value: "paediatric", label: "Paediatric" },
                          ]}
                        />
                      </FormRow>
                      <FormRow label="Required">
                        <input
                          type="number"
                          min={0}
                          value={req.required}
                          onChange={(e) =>
                            setThisReq("required", e.target.valueAsNumber)
                          }
                          name={`requirements[${i}].required`}
                          label="Requirement"
                        />
                      </FormRow>
                      <FormRow label="Optional">
                        <input
                          type="number"
                          min={0}
                          value={req.optional}
                          onChange={(e) =>
                            setThisReq("optional", e.target.valueAsNumber)
                          }
                        />
                      </FormRow>
                      <FormRow label="Attendance">
                        <input
                          type="number"
                          max={100}
                          min={0}
                          value={req.attendance}
                          onChange={(e) =>
                            setThisReq("attendance", e.target.valueAsNumber)
                          }
                        />
                      </FormRow>
                      <FormRow label="Geofence">
                        <select
                          value={req.geofence}
                          onChange={(e) =>
                            setThisReq("geofence", e.target.value)
                          }
                        >
                          <option value="immediate">Immediate</option>
                          <option value="local">Local</option>
                          <option value="remote">Remote</option>
                          <option value="distant">Distant</option>
                        </select>
                      </FormRow>

                      <div>
                        <div></div>
                        <div>
                          <button
                            type="button"
                            onclick={(e) => {
                              e.stopPropagation();
                              console.log("delete", i());
                              console.log(JSON.stringify(store.requirements));
                              setStore("requirements", (requirements) =>
                                requirements.toSpliced(i(), 1)
                              );
                              console.log(JSON.stringify(store.requirements));
                            }}
                          >
                            Delete rule
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                }}
              </For>
              <hr />
              <button
                type="button"
                onClick={(e) => {
                  console.log("appending", e);
                  e.stopPropagation();
                  setStore("requirements", (requirements) => [
                    ...(requirements ?? []),
                    {
                      skills: [],
                      required: 1,
                      optional: 0,
                      attendance: 100,
                      geofence: "immediate",
                    },
                  ]);
                }}
              >
                Add requirement
              </button>
            </div>
          </FormRow>
        </div>
        <button type="submit">Save template</button>
        <a>Cancel</a>
      </Form>
    </main>
  );
}

function RequirementDescription(props) {
  return (
    <div>
      {props.requirementSpec.required}{" "}
      {props.requirementSpec.optional > 0
        ? `- ${props.requirementSpec.optional + props.requirementSpec.required}`
        : ""}
      staff with {props.requirementSpec.skills.join(", ")} skills;{" "}
      {props.requirementSpec.attendance}% attendance required; Geofence:{" "}
      {props.requirementSpec.geofence}
    </div>
  );
}

function RequirementForm(props) {
  const dialogContext = useDialogContext();
  const [form, { Form }] = createForm({
    initialValues: props.requirementSpec || {
      skills: [],
      required: 1,
      optional: 0,
      attendance: 100,
      geofence: "immediate",
    },
  });
  return (
    <div>
      <pre>*{JSON.stringify(props.requirementSpec)}*</pre>

      <SelectField
        name="skills"
        form={form}
        multiple
        label="Skills"
        options={[
          { value: "iac", label: "IAC" },
          {
            value: "listrunner",
            label: "Listrunner",
          },
          { value: "regional", label: "Regional" },
          {
            value: "paediatric",
            label: "Paediatric",
          },
        ]}
      />

      <NumberField min={0} form={form} name="required" label="Required" />

      <NumberField min={0} form={form} name="optional" label="Optional" />

      <NumberField
        min={0}
        max={100}
        form={form}
        name="attendance"
        label="Attendance"
      />

      <field.SelectField
        form={form}
        name="geofence"
        label="Geofence"
        options={["Immediate", "Local", "Remote", "Distant"]}
      />

      <Button
        onClick={() => {
          form.handleSubmit().then(() => dialogContext.close());
        }}
      >
        Save
      </Button>
      <Button onClick={() => dialogContext.close()}>Close</Button>
    </div>
  );
}




function EditActivity(props) {
  const editActivityMutation = graphql`
    mutation editActivityMutation($input: ActivityInput!) {
      editActivity(activity: $input) {
        id
        name
      }
    }
  `;
  const activityForm = createLazyLoadQuery<editActivityQuery>(
    graphql`
      query editActivityQuery($id: ID!) {
        node(id: $id) {
          ... on Activity {
            name
            id
            activityStart
            activityFinish
            requirements
            timeslots {
              start
              finish
              assignments {
                staff {
                  id
                  name
                }
              }
            }
            location {
              id
              
            }
            tags {
              id
              
            }
          }
        }
        activityTags {
          id
          name
        }
        locations {
          id
          name
        }
      }
    `,
    () => ({ id: props.activity })
  );
  return <Show when={activityForm()} keyed>{(formData) => {
  const [form, { Form, Field }] = createForm<ActivityFormData>({initialValues:formData.node as unknown as ActivityFormData});

  return (
    <Dialog
      open={!!props.activity}
      title={props.activity?.includes("--") ? "New Activity" : "Edit Activity"}
      onClose={props.onClose}
    >
      <Form>
        <div id="template-editor-settings">
          <FormRow>
            <Field name="name">
              {(field, props) => <TextField field={field} {...props} label="Activity Name" />}
              </Field>
          </FormRow>
          
          <FormRow label="Tags">
            <Field name="activityTags">
              {(field,props) => (
                <fields.SelectField
                  label="Activity Tags"
                  multiple
                  options={activityForm()?.activity_tags ?? []}
                />
              )}
            </Field>
          </FormRow>
          <FormRow label="Location">
            <Field name="location">
              {(field) => (
                <field.SelectField
                  label="Location"
                  options={activityForm()?.locations || []}
                />
              )}
            </form.AppField>
          </FormRow>
          <FormRow label="Requirements" element="div">
            <form.AppField name="requirements">
              {(groupField) => (
                <div>
                  <Index
                    each={groupField().state.value}
                    fallback={<div>⚠️ No requirements have been set</div>}
                  >
                    {(req, i) => (
                      <form.AppField name={`requirements.${i}`}>
                        {(req) => {
                          const [open, setOpen] = createSignal(false);
                          return (
                            <div>
                              <RequirementDescription
                                requirementSpec={req().state.value}
                              />

                              <Button
                                onClick={(e) => {
                                  groupField().removeValue(i);
                                  e.stopPropagation();
                                  console.log("delete", i);
                                }}
                              >
                                Delete rule
                              </Button>
                              <Dialog
                                trigger={<Button>Edit rule</Button>}
                                title="Edit requirement"
                                open={open()}
                                setOpen={setOpen}
                              >
                                <RequirementForm
                                  requirementSpec={req().state.value}
                                  onSubmit={({ value }) => {
                                    groupField().replaceValue(i, value);
                                  }}
                                />
                              </Dialog>

                              <div></div>
                            </div>
                          );
                        }}
                      </form.AppField>
                    )}
                  </Index>
                  <hr />

                  <Dialog
                    title="Add requirement"
                    trigger={<Button>Add rule</Button>}
                  >
                    <RequirementForm
                      onSubmit={({ value }) => {
                        groupField().pushValue(value);
                      }}
                    />
                  </Dialog>
                </div>
              )}
            </form.AppField>
          </FormRow>
        </div>

        <div>
          <Button onClick={props.onClose}>Disagree</Button>
          <Button onClick={props.onClose} autoFocus>
            Agree
          </Button>
        </div>
      </Form>
      </Dialog>
      )}</Show>;
  
}
export default EditActivity;
