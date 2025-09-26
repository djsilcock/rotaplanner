import { splitProps } from "solid-js";

import { Show } from "solid-js/web";

import { createFormHook, createFormHookContexts } from "@tanstack/solid-form";

import * as fields from "../ui/textfield.jsx";
export function TextField(props) {
  return <InputField type="text" {...props} />;
}

export function TimeField(props) {
  return <InputField type="time" {...props} />;
}

export function DateField(props) {
  return <InputField type="date" {...props} />;
}

export function DateTimeField(props) {
  return <InputField type="datetime-local" {...props} />;
}
export function NumberField(props) {
  return <InputField type="number" {...props} />;
}

export function CheckboxField(props) {
  const field = useFieldContext();
  const isChecked = () => {
    if (Array.isArray(field().state.value)) {
      return field().state.value.includes(props.value);
    }
    if (typeof field().state.value == "object") {
      return field().state.value[props.value] === true;
    }
    return field().state.value === (props.value ?? true);
  };
  const handleChange = (checked) => {
    if (Array.isArray(field().state.value)) {
      field().handleChange(
        checked
          ? [...field().state.value, props.value]
          : field().state.value.filter((v) => v !== props.value)
      );
    } else if (typeof field().state.value == "object") {
      field().handleChange({ ...field().state.value, [props.value]: checked });
    } else {
      field().handleChange(checked && props.value);
    }
  };
  return (
    <input
      name={field().name}
      type={props.type ?? "checkbox"}
      onBlur={field().blur}
      onChange={(e) => handleChange(e.target.checked)}
      checked={isChecked()}
    />
  );
}

export function RadioField(props) {
  return <CheckboxField type="radio" {...props} />;
}

export function FormRow(props) {
  return <div>{props.children}</div>;
}
export function ErrorMessage() {
  const field = useFieldContext();
  return (
    <Show when={!field().state.meta.isValid}>
      <em>{field().state.meta.errors.join(",")}</em>
    </Show>
  );
}

export function InputField(props) {
  const field = useFieldContext();
  return (
    <fields.TextField
      {...props}
      onBlur={field().blur}
      setValue={(e) => {
        field().handleChange(e);
      }}
      value={field().state.value}
      label={props.label || field().label || field().name}
      placeholder={props.placeholder || field().placeholder}
    />
  );
}
export function SelectField(props) {
  const field = useFieldContext();
  const [options, rest] = splitProps(props, ["options"]);

  return (
    <fields.Combobox
      {...rest}
      options={options.options || []}
      format={(item, type) => (type === "option" ? item.label : item.label)}
      onChange={(val) => {
        console.log(val);
        field().handleChange(val);
      }}
      value={field().state.value}
    />
  );
}
export const { fieldContext, formContext, useFieldContext } =
  createFormHookContexts();
export const { useAppForm, useFormContext, withForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents: {
    SelectField,
    InputField,
    TextField,
    TimeField,
    DateField,
    DateTimeField,
    NumberField,
    CheckboxField,
    RadioField,
  },
  formComponents: {},
});
