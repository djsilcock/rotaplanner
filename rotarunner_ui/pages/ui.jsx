import { mergeProps, splitProps } from "solid-js";

import { Show } from "solid-js/web";

import { createFormHook, createFormHookContexts } from "@tanstack/solid-form";

import { Field } from "@modular-forms/solid";

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
  props = mergeProps({ type: "checkbox" }, props);
  return (
    <Field name={props.name} of={props.form}>
      {(field, inputProps) => <input {...inputProps} checked={field.value} />}
    </Field>
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
  return (
    <Field name={props.name} of={props.form}>
      {(field, fieldProps) => (
        <fields.TextField
          {...fieldProps}
          value={field.value}
          label={props.label || props.name}
          placeholder={props.placeholder}
        />
      )}
    </Field>
  );
}
export function SelectField(props) {
  const field = useFieldContext();
  const [fieldProps, cbProps] = splitProps(mergeProps({ options: [] }, props), [
    "name",
    "form",
  ]);
  return (
    <Field name={fieldProps.name} of={fieldProps.form}>
      {(field, props) => (
        <fields.Combobox
          {...props}
          {...cbProps}
          format={(item, type) => (type === "option" ? item.label : item.label)}
          value={field.value}
          errorMessage={field.error}
        />
      )}
    </Field>
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
