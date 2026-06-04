import {
  createMemo,
  JSX,
  mergeProps,
  splitProps,
  createEffect,
} from "solid-js";

import { Show, For } from "solid-js/web";

import {
  Field,
  FieldStore,
  FormStore,
  FieldProps,
  setValue,
} from "@modular-forms/solid";

import * as fields from "./components.jsx";
import { TextField as KTextField } from "@kobalte/core/text-field";

import tfstyles from "./textfield.module.css";

type InputFieldProps = JSX.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  description?: string;
  props: {
    name: string;
    autofocus?: boolean;
    ref: (element: HTMLInputElement) => void;
    onInput: JSX.EventHandler<HTMLInputElement, InputEvent>;
    onChange: JSX.EventHandler<HTMLInputElement, Event>;
    onBlur: JSX.EventHandler<HTMLInputElement, FocusEvent>;
  };
  field: any;
};

export function InputField(props: InputFieldProps) {
  const [fieldProps, localProps, elementProps] = splitProps(
    props,
    ["field", "props"],
    ["label", "description", "inputType"],
  );
  return (
    <KTextField
      class={tfstyles.root}
      validationState={fieldProps.field.error ? "invalid" : "valid"}
      value={fieldProps.field.value}
    >
      <KTextField.Label class={tfstyles.label}>
        {localProps.label}
      </KTextField.Label>
      <KTextField.Input
        class={tfstyles.input}
        {...elementProps}
        {...fieldProps.props}
      />
      <KTextField.ErrorMessage>
        {fieldProps.field.error}
      </KTextField.ErrorMessage>
      <KTextField.Description>{localProps.description}</KTextField.Description>
    </KTextField>
  );
}

export function TextField(props: InputFieldProps) {
  return <InputField inputType="text" {...props} />;
}

export function TimeField(props: InputFieldProps) {
  return <InputField inputType="time" {...props} />;
}

export function DateField(props: InputFieldProps) {
  return <InputField inputType="date" {...props} />;
}

export function DateTimeField(props: InputFieldProps) {
  return <InputField inputType="datetime-local" {...props} />;
}
export function NumberField(props: InputFieldProps) {
  return <InputField inputType="number" {...props} />;
}

import { Combobox as KCombobox } from "@kobalte/core/combobox";
import cbstyles from "./combobox.module.css";

type Option = { value: any; label: string; disabled?: boolean };
export function Combobox(props) {
  const [fieldProps, localProps, rest] = splitProps(
    props,
    ["field", "props"],
    ["label", "description", "options", "multiple"],
  );
  createEffect(() => {
    console.log("Combobox value", fieldProps.field.value);
  });
  return (
    <KCombobox
      class={cbstyles.root}
      options={localProps.options}
      defaultValue={
        localProps.multiple
          ? (fieldProps.field.value?.map((v: any) => ({ value: v })) ?? [])
          : { value: fieldProps.field.value }
      }
      placeholder={props.placeholder}
      optionGroupChildren={
        (localProps.options as Array<any>).some((item) => item.items)
          ? "items"
          : undefined
      }
      optionValue={props.optionValue ?? "value"}
      optionTextValue={props.optionTextValue ?? "label"}
      optionLabel={props.optionLabel ?? "label"}
      optionDisabled={props.optionDisabled ?? "disabled"}
      multiple={localProps.multiple}
      validationState={fieldProps.field.error ? "invalid" : "valid"}
      itemComponent={(props) => {
        return (
          <KCombobox.Item item={props.item} class={cbstyles.item}>
            <KCombobox.ItemLabel>
              {(props.item.rawValue as Option).label}

              <KCombobox.ItemIndicator class={cbstyles.itemIndicator}>
                ✓
              </KCombobox.ItemIndicator>
            </KCombobox.ItemLabel>
          </KCombobox.Item>
        );
      }}
      sectionComponent={(props) => (
        <KCombobox.Section>{props.section.rawValue.label}</KCombobox.Section>
      )}
    >
      <KCombobox.Label class={cbstyles.label}>
        {localProps.label}
      </KCombobox.Label>
      <KCombobox.HiddenSelect {...fieldProps.props} />
      <KCombobox.Control class={cbstyles.control}>
        {(state) => (
          <>
            <div>
              <Show when={localProps.multiple}>
                <For each={state.selectedOptions()}>
                  {(option) => (
                    <span
                      class={cbstyles.chip}
                      onPointerDown={(e) => e.stopPropagation()}
                    >
                      {(option as Option).label}
                      <button onClick={() => state.remove(option)}>x</button>
                    </span>
                  )}
                </For>
              </Show>
              <KCombobox.Input class={cbstyles.input} />
            </div>
            <KCombobox.Trigger class={cbstyles.trigger}>▼</KCombobox.Trigger>
          </>
        )}
      </KCombobox.Control>
      <KCombobox.ErrorMessage class={cbstyles.errorMessage}>
        {fieldProps.field.error}
      </KCombobox.ErrorMessage>
      <KCombobox.Content class={cbstyles.content}>
        <KCombobox.Listbox class={cbstyles.listbox} />
      </KCombobox.Content>
    </KCombobox>
  );
}

import { Component } from "solid-js";

export interface ComboboxOption {
  value: string;
  label: string;
}

interface ModularMultiComboboxProps {
  field: FieldStore<any, any>; // Passed from Modular Forms' <Field>
  props: JSX.HTMLAttributes<HTMLSelectElement>;
  options: ComboboxOption[];
  label?: string;
  placeholder?: string;
}

export const ModularMultiCombobox: Component<ModularMultiComboboxProps> = (
  props,
) => {
  return (
    <KCombobox<ComboboxOption>
      multiple
      options={props.options}
      optionValue="value"
      optionLabel="label"
      // 1. Initialize value from Modular Forms' current state (expects array of objects or empty array)
      defaultValue={props.options.filter((opt) =>
        props.field.value?.includes(opt.value),
      )}
      onChange={(value) => {
        // 3. Update Modular Forms state when selection changes
        const selectedValues = value.map((opt) => opt.value);
        console.log("Selected values:", selectedValues);
        //props.field.setValue(selectedValues);
      }}
      placeholder={props.placeholder}
      itemComponent={(props) => (
        <KCombobox.Item item={props.item} class="combobox__item">
          <KCombobox.ItemLabel>{props.item.textValue}</KCombobox.ItemLabel>
          <KCombobox.ItemIndicator class="combobox__item-indicator">
            ✓
          </KCombobox.ItemIndicator>
        </KCombobox.Item>
      )}
    >
      <Show when={props.label}>
        <KCombobox.Label class="combobox__label">{props.label}</KCombobox.Label>
      </Show>

      <div class="combobox__control">
        <KCombobox.Control
          aria-label={props.label}
          class="combobox__control-inner"
        >
          {/* Kobalte's built-in tag list rendering */}

          {(state) => (
            <>
              {state.selectedOptions().map((option) => (
                <span class="combobox__tag">
                  {option.label}
                  <button
                    type="button"
                    class="combobox__tag-remove"
                    onClick={() => state.remove(option)}
                  >
                    ×
                  </button>
                </span>
              ))}
              <KCombobox.Input class="combobox__input" />
              <KCombobox.Trigger class="combobox__trigger">
                <KCombobox.Icon class="combobox__icon">▼</KCombobox.Icon>
              </KCombobox.Trigger>
            </>
          )}
        </KCombobox.Control>
      </div>

      {/* 
        2. The HiddenSelect renders a native <select multiple> element.
        We hook Modular Forms directly into its attributes.
      */}
      <KCombobox.HiddenSelect
        name={props.field.name}
        ref={props.props.ref}
        onBlur={props.props.onBlur}
        onChange={props.props.onChange} // Use onInput or onChange to notify Modular Forms
      />

      <Show when={props.field.error}>
        <span class="combobox__error-message">{props.field.error}</span>
      </Show>

      <KCombobox.Portal>
        <KCombobox.Content class="combobox__content">
          <KCombobox.Listbox class="combobox__listbox" />
        </KCombobox.Content>
      </KCombobox.Portal>
    </KCombobox>
  );
};
