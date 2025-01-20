import { Show } from "solid-js/web";
import { MultiSelect, DateField } from "./ui";
import { createForm, getBy } from "@tanstack/solid-form";

import {
  children,
  createEffect,
  createMemo,
  createSignal,
  Index,
  onCleanup,
  splitProps,
} from "solid-js";

import styles from "./edit_activity_template.module.css";

const ordinal = (index) => {
  const ordinals = ["th", "st", "nd", "rd"];
  const v = index % 100;
  return index + (ordinals[(v - 20) % 10] || ordinals[v] || ordinals[0]);
};

function TextField(props) {
  return <InputField type="text" {...props} />;
}

function TimeField(props) {
  return <InputField type="time" {...props} />;
}
function InputField(props) {
  return (
    <props.form.Field name={props.name}>
      {(field) => (
        <div class={styles.formRow}>
          <label class={styles.fieldLabel}>
            {props.label}
            <input
              type={props.type}
              onBlur={(e) => field().handleBlur(e.target.value)}
              onChange={(e) => field().handleChange(e.target.value)}
              value={field().state.value}
            />
          </label>
          <Show when={field().state.meta.errors.length > 0}>
            <div class={styles.fieldError}>
              {field().state.meta.errors.join(",")}
            </div>
          </Show>
        </div>
      )}
    </props.form.Field>
  );
}
function SelectField(props) {
  const [local, remaining] = splitProps(props, ["multiple"]);
  return (
    <Show when={local.multiple} fallback={<SelectSingle {...remaining} />}>
      <MultiSelect {...remaining} />
    </Show>
  );
}
function SelectSingle(props) {
  const resolved = children(() => props.children);
  const options = createMemo(
    () =>
      props.options?.map((o) => <option value={o.value}>{o.label}</option>) ??
      resolved
  );
  return (
    <props.form.Field name={props.name}>
      {(field) => (
        <div class={styles.formRow}>
          <label class={styles.fieldLabel}>
            {props.label}
            <select
              type={props.type}
              onBlur={(e) => field().handleBlur(e.target.value)}
              onChange={(e) => field().handleChange(e.target.value)}
              value={field().state.value}
            >
              {options}
            </select>
          </label>
          <Show when={field().state.meta.errors.length > 0}>
            <div class={styles.fieldError}>
              {field().state.meta.errors.join(",")}
            </div>
          </Show>
        </div>
      )}
    </props.form.Field>
  );
}
function RuleGroup(props) {
  return (
    <div>
      <props.form.Field name={props.groupName}>
        {(groupField) => (
          <div className={styles.ruleBox}>
            <SelectField
              form={props.form}
              name={`${props.groupName}.groupType`}
              label="Type"
            >
              <option value="and">All of these rule must match</option>
              <option value="or">Any of these rules must match</option>
              <option value="not">None of these rules may match</option>
            </SelectField>
            <div>Groups</div>
            <props.form.Field name={`${props.groupName}.groups`} mode="array">
              {(field) => (
                <div>
                  <Index each={field().state.value} fallback={"No sub-groups"}>
                    {(_, groupNo) => (
                      <RuleGroup
                        groupName={`${props.groupName}.groups[${groupNo}]`}
                        index={groupNo}
                        form={props.form}
                      />
                    )}
                  </Index>

                  <button
                    type="button"
                    onClick={() =>
                      props.form.pushFieldValue(`${props.groupName}.groups`, {
                        groupType: "and",
                        groups: [],
                        rules: [],
                      })
                    }
                  >
                    Add group
                  </button>
                </div>
              )}
            </props.form.Field>
            <div>Rules</div>
            <props.form.Field
              name={`${props.groupName}.rules`}
              label="rules"
              mode="array"
            >
              {(field) => (
                <div>
                  <Index
                    each={field().state.value}
                    fallback="No rules declared"
                  >
                    {(_, ruleNo) => (
                      <Rule
                        ruleName={`${props.groupName}.rules[${ruleNo}]`}
                        index={ruleNo}
                        form={props.form}
                      />
                    )}
                  </Index>
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
              )}
            </props.form.Field>

            <div>
              <Show
                when={
                  groupField().state.value?.groups?.length +
                    groupField().state.value?.rules?.length ==
                  0
                }
              >
                <div>⚠️ This group has no members</div>
              </Show>
            </div>
          </div>
        )}
      </props.form.Field>
    </div>
  );
}

function Rule(props) {
  const ruleDescription = createMemo(() => {
    const rule = props.form.useStore((state) => {
      console.log(state, props.ruleName, getBy(state.values, props.ruleName));
      return getBy(state.values, props.ruleName);
    });
    console.log(rule().ruleType);
    return rule().ruleType;
  });
  return (
    <div>
      <details className="rule-definition" name="rule-definition-box">
        <summary className="description">{ruleDescription()}</summary>
        <div className={styles.ruleBox}>
          <SelectField
            form={props.form}
            label="Type"
            name={`${props.ruleName}.ruleType`}
          >
            <option value="DAILY">Every n days</option>
            <option value="WEEKLY">
              Days in week (eg every 3rd Monday; 1st Monday of month)
            </option>
            <option value="MONTHLY">
              Day in month (eg 1st of every month)
            </option>
            <option value="DATETAG">Tagged days</option>
          </SelectField>
          <props.form.Subscribe
            selector={(state) => {
              const { ruleType, cycleLength } = getBy(
                state.values,
                props.ruleName
              );
              return { ruleType, cycleLength };
            }}
          >
            {(ruledef) => (
              <Switch>
                <Match when={ruledef().ruleType == "WEEKLY"}>
                  <SelectField
                    form={props.form}
                    multiple
                    name={`${props.ruleName}.weekdays`}
                    label="Weekdays"
                  >
                    <option value={0}>Monday</option>
                    <option value={1}>Tuesday</option>
                    <option value={2}>Wednesday</option>
                    <option value={3}>Thursday</option>
                    <option value={4}>Friday</option>
                    <option value={5}>Saturday</option>
                    <option value={6}>Sunday</option>
                  </SelectField>
                  <SelectField
                    form={props.form}
                    name={`${props.ruleName}.cycleLength`}
                    label="Cycle Length"
                    options={[
                      { value: 0, label: "weeks of month" },
                      { value: 1, label: "every week" },
                      { value: 2, label: "every 2 weeks" },
                      { value: 3, label: "every 3 weeks" },
                      { value: 4, label: "every 4 weeks" },
                      { value: 5, label: "every 5 weeks" },
                      { value: 6, label: "every 6 weeks" },
                      { value: 7, label: "every 7 weeks" },
                      { value: 8, label: "every 8 weeks" },
                    ]}
                  />
                  <SelectField
                    form={props.form}
                    multiple
                    name={`${props.ruleName}.weekNumbers`}
                    label="Week Numbers"
                  >
                    <Index
                      each={Array.from(
                        { length: Number(ruledef().cycleLength) || 5 },
                        (x, i) => i + 1
                      )}
                    >
                      {(_, index) => (
                        <option value={index + 1}>{ordinal(index + 1)}</option>
                      )}
                    </Index>
                  </SelectField>
                  <SelectField
                    form={props.form}
                    multiple
                    name={`${props.ruleName}.months`}
                    label="Months"
                    options={[
                      { value: 0, label: "January" },
                      { value: 1, label: "February" },
                      { value: 2, label: "March" },
                      { value: 3, label: "April" },
                      { value: 4, value: "May" },
                      { value: 5, label: "June" },
                      { value: 6, label: "July" },
                      { value: 7, label: "August" },
                      { value: 8, label: "September" },
                      { value: 9, label: "October" },
                      { value: 10, label: "November" },
                      { value: 11, label: "December" },
                    ]}
                  />
                </Match>
              </Switch>
            )}
          </props.form.Subscribe>
          <Switch>
            <Match
              when={props.form.getFieldValue(`${props.ruleName}.ruleType`)}
            ></Match>
          </Switch>
          <div>
            <DateField form={props.form} name="fred" />
          </div>
          <div>bla</div>
          <div>bla</div>
          <div>bla</div>
          <button type="button">Delete this rule</button>
        </div>
      </details>
    </div>
  );
}

function EditActivityTemplate(props) {
  const renderLinklike = (field) => (
    <label className="linklike">
      {field({ "data-up-validate": true })}
      {field.label.text}
    </label>
  );
  const form = createForm(() => ({
    defaultValues: {
      ruleset: { groupType: "and", groups: [], rules: [] },
      activity_tags: [],
    },
    validators: {
      onChange(v) {
        console.log(v);
      },
    },
  }));
  createEffect(() => console.log(form.state));
  return (
    <main>
      <form method="post" id="edit-activity-form" data-up-submit>
        <h4>Edit activity</h4>
        <div id="template-editor-settings" class={styles.formContainer}>
          <TextField form={form} name="activity_name" label="Activity Name" />
          This activity occurs:
          <div id="ruleset-container">
            <RuleGroup groupName="ruleset" form={form} />
          </div>
          <hr />
          <TimeField form={form} label="Start time" name="start_time" />
          <TimeField form={form} label="Finish time" name="finish_time" />
          <MultiSelect
            form={form}
            name="activity_tags"
            value={field().state.value}
            label="Tags"
          >
            <option value="URO">Urology</option>
            <option value="ENT">ENT</option>
          </MultiSelect>
          <label className={styles.formRow}>
            Location
            <select label="Location">
              <option>Theatre 1</option>
              <option>Theatre 1</option>
              <option>Theatre 1</option>
              <option>Theatre 1</option>
            </select>
          </label>
          <hr />
          {`
          <div id="requirements-container" data-up-form-group>
            Requirements:
            {form.requirements.length > 0 ? (
              form.requirements.map((req, i) => (
                <details key={i} open={req.isOpen.data}>
                  <summary>Requirement</summary>
                  {req.reqId}
                  <table className="requirement">
                    <div style={{ display: "none" }}>{req.isOpen}</div>
                    {[
                      req.skills,
                      req.requirement,
                      req.optional,
                      req.attendance,
                      req.geofence,
                    ].map((field, j) => renderFormLine(field))}
                    <tr>
                      <td></td>
                      <td>
                        <label className="linklike">
                          {req.isDeleted}Delete rule
                        </label>
                      </td>
                    </tr>
                  </table>
                </details>
              ))
            ) : (
              <div>⚠️ No requirements have been set</div>
            )}
            {renderLinklike(form.shouldAddRequirement)}
          </div>`}
        </div>
        <button type="submit">Save template</button>
        <a>Cancel</a>
      </form>
    </main>
  );
}

export default EditActivityTemplate;
/*
{%macro ordinal_options(first,last,name,value)%} {%for index in range(first,last+1)%}
<option value="{{index}}" {%if index==value %}selected{%endif%}>
    {%if index==1 %} Every {{name}} {%else%} Every {{ordinal(index)}} {{name}} {%endif%}
</option>
{%endfor%} {%endmacro%}

{%macro render_linklike(field)%}
<label class="linklike">
    {{field(**{'up-validate':true})}}{{field.label.text}}
</label>
{%endmacro%}

function TextField(props) {
    return <Field name={props.name}>{(field) => <TextField label={props.label} value={field().value} onBlur={field().handleBlur} onChange={field().handleChange } /> }</Field>
}

{%macro form_line(field)%}
<tr id="{{field.id}}-group" up-form-group {%if field.flags.usf%} up-show-for="{{field.flags.usf}}" {%endif%}>
    <td>{{field.label}}</td>
    <td>{%if field.errors%}
        <div class="ui negative message">
            {%for err in field.errors%}
            <div>{{err}}</div>
            {%endfor%}
        </div>
        {%endif%}
        {{field(**{"up-validate":true,"up-watch-event":"blur"})}}
    </td>
</tr>
{%endmacro%}


{%macro render_group(group,rule_types,is_root=false)%}
<li>
    <div id="{{group._prefix}}-container" class="rule-box">
        {{group.group_type}} <label class="linklike">{{group.should_add_rule}}Add rule</label> <label
            class="linklike">{{group.should_add_group}}Add rule
            group</label>
        {%if not is_root%}<label class="linklike">{{group.is_deleted}}Delete group</label>{%endif%}
        <ul id="{{group._prefix}}-ul" up-form-group>

            {%for subgroup in group.groups%}
            {{render_group(subgroup,rule_types)}}
            {%endfor%}
            {%for rule in group.rules%}
            {{render_rule(rule,rule_types)}}
            {%endfor%}
            {%if group.groups|length == 0 and group.rules|length==0 %}
            ⚠️This group has no members
            {%endif%}

        </ul>
    </div>
</li>
{%endmacro%}





{%macro render_rule(rule,rule_types)%}
<li>
    <details class="rule-definition" {%if rule.is_open.data%}open{%endif%} name="rule-definition-box">
        <summary class="description">(rule description)</summary>
        <div style="display:none">{{rule.is_open}}</div>
        {{rule.rule_id}}
        <table class="rule-box">
            <tbody>
                {{form_line(rule.rule_type)}}
                {{form_line(rule.day_interval)}}
                {{form_line(rule.week_interval)}}
                {{form_line(rule.month_interval)}}
                {{form_line(rule.start_date)}}
                {{form_line(rule.finish_date)}}
                {{form_line(rule.tag)}}
                {{form_line(rule.date_type)}}
                <tr>
                    <td></td>
                    <td>{{render_linklike(rule.is_deleted)}}
                </tr>
            </tbody>
        </table>

    </details>

</li>
{%endmacro%}

function EditActivityForm(props) {
    const form = createForm(() => ({
        onSubmit:(props=>console.log(props))
    }))
return <main>
    <form onSubmit={()=>form.handleSubmit()}>
        <h4>Edit activity</h4>
        <div id="template-editor-settings">
            <Field name="activity_name">{field => <div><TextField value={field().value} onBlur={field().handleBlur} onChange={field().handleChange } label="Activity Name"></TextField></div>}</Field>
            
            This activity occurs:
            <div id="ruleset-container" up-form-group>
                <ul>
                    {{render_group(form,rule_types,true)}}
                </ul>
            </div>
            <hr />
            <table>
                <tbody>
                    {{form_line(form.start_time)}}
                    {{form_line(form.finish_time)}}
                    {{form_line(form.activity_tags)}}
                    {{form_line(form.location)}}
                </tbody>
            </table>
            <hr />
            <div id="requirements-container" up-form-group>
                Requirements:
                {%for req in form.requirements%}
                <details {%if req.is_open.data%}open{%endif%}>
                    <summary>Requirement</summary>
                    {{req.req_id}}
                    <table class="requirement">
                        <div style="display:none">{{req.is_open}}</div>

                        {{form_line(req.skills)}}
                        {{form_line(req.requirement)}}
                        {{form_line(req.optional)}}
                        {{form_line(req.attendance)}}
                        {{form_line(req.geofence)}}
                        <tr>
                            <td></td>
                            <td><label class="linklike">
                                    {{req.is_deleted}}Delete rule
                                </label></td>
                        </tr>

                    </table>
                </details>
                {%else%}
                <div>⚠️No requirements have been set</div>
                {%endfor%}

                {{render_linklike(form.should_add_requirement)}}
            </div>
        </div>
        <button type="submit">Save template</button>
        <a href="{{url_for('activities.activity_templates')}}">Cancel</a>
    </form>
</main>
}*/
