import { JSX, mergeProps, splitProps } from "solid-js";

import { Show } from "solid-js/web";

import { Field, FieldStore, FormStore } from "@modular-forms/solid";

import * as fields from "../ui/index.jsx";
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
interface InputFieldProps extends JSX.InputHTMLAttributes<HTMLInputElement> {
  name: string;
  field: FieldStore<any, any>;
  label?: string;
  placeholder?: string;
  type?: string;
}
export function InputField(props: InputFieldProps) {
  const [fieldProps, elementProps] = splitProps(props, [
    "name",
    "field",
    "label",
    "placeholder",
  ]);
  return (
    <fields.TextField
      {...elementProps}
      value={fieldProps.field.value}
      label={fieldProps.label || props.name}
      placeholder={fieldProps.placeholder}
    />
  );
}
export function SelectField(props) {
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
