import { TextField as KTextField } from "@kobalte/core/text-field";
import cbstyles from "./combobox.module.css";
import dlgstyles from "./dialog.module.css";
import tfstyles from "./textfield.module.css";
import { createMemo, For, Show } from "solid-js";

/**
 * TextField component wraps Kobalte's TextField and provides a styled input field with label, error message, and description.
 *
 * @param {Object} props - The properties object.
 * @param {string} props.value - The current value of the text field.
 * @param {function} props.setValue - Callback function to update the value.
 * @param {string} props.label - The label text for the text field.
 * @param {string} [props.errorMessage] - Optional error message to display.
 * @param {string} [props.type] - The type of the input field (e.g., "text", "password").
 * @param {string} [props.description] - Optional description to display below the input.
 * @returns {JSX.Element} The rendered TextField component.
 */
export function TextField(props) {
  const [rootProps, inputProps] = splitProps(
    props,
    ["name", "value", "required", "disabled"],
    ["placeholder", "ref", "onInput", "onChange", "onBlur", "type"]
  );
  return (
    <KTextField
      {...rootProps}
      class={tfstyles.root}
      validationState={props.errorMessage ? "invalid" : "valid"}
    >
      <KTextField.Label class={tfstyles.label}>{props.label}</KTextField.Label>
      <KTextField.Input class={tfstyles.input} {...inputProps} />
      <KTextField.ErrorMessage>{props.errorMessage}</KTextField.ErrorMessage>
      <KTextField.Description>{props.description}</KTextField.Description>
    </KTextField>
  );
}

/**
 * Dialog component wraps Kobalte's Dialog and provides a styled modal dialog with title, close button, and content area.
 *
 * @param {Object} props - The properties object.
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {function} props.setOpen - Callback function to change the open state.
 * @param {React.ReactNode} props.trigger - The element that triggers the dialog to open.
 * @param {string} props.title - The title text for the dialog.
 * @param {React.ReactNode} props.children - The content to display inside the dialog.
 * @returns {JSX.Element} The rendered Dialog component.
 */
import { Dialog as KDialog } from "@kobalte/core/dialog";
export { useDialogContext } from "@kobalte/core/dialog";

export function Dialog(props) {
  return (
    <>
      <KDialog
        open={props.open}
        onOpenChange={(isOpen) => {
          props.setOpen?.(isOpen);
          if (!isOpen) props.onClose?.();
        }}
      >
        <KDialog.Trigger>{props.trigger}</KDialog.Trigger>
        <KDialog.Portal>
          <KDialog.Overlay class={dlgstyles.overlay} />
          <div class={dlgstyles.positioner}>
            <KDialog.Content class={dlgstyles.content}>
              <div class={dlgstyles.header}>
                <KDialog.Title class={dlgstyles.title}>
                  {props.title}
                </KDialog.Title>
                <KDialog.CloseButton class={dlgstyles.closeButton}>
                  X
                </KDialog.CloseButton>
              </div>

              <KDialog.Description class={dlgstyles.description}>
                {props.children}
              </KDialog.Description>
            </KDialog.Content>
          </div>
        </KDialog.Portal>
      </KDialog>
    </>
  );
}
import { Combobox as KCombobox } from "@kobalte/core/combobox";

/**
 * Combobox component wraps Kobalte's Combobox and provides a styled dropdown with search functionality.
 * @param {Object} props - The properties object.
 * @param {string} props.value - The current value of the combobox.
 * @param {string} props.label - The label text for the combobox.
 * @param {string} [props.errorMessage] - The error message to display.
 * @param {function} props.onChange - Callback function to update the value.
 * @param {Array} props.options - The options to display in the dropdown.
 * @param {string} props.placeholder - The placeholder text for the input.
 * @returns {JSX.Element} The rendered Combobox component.
 */

export function Combobox(props) {
  const value = createMemo(() =>
    props.multiple
      ? props.value?.map((val) => ({ value: val }))
      : props.value && { value: props.value }
  );
  return (
    <KCombobox
      class={cbstyles.root}
      label={props.label}
      value={value()}
      onChange={(val) =>
        props.onChange(props.multiple ? val?.map((v) => v.value) : val?.value)
      }
      options={props.options}
      placeholder={props.placeholder}
      optionValue="value"
      optionTextValue="label"
      optionLabel="label"
      optionDisabled="disabled"
      multiple={props.multiple}
      validationState={props.errorMessage ? "invalid" : "valid"}
      itemComponent={(props) => {
        console.log(props);

        return (
          <KCombobox.Item item={props.item} class={cbstyles.item}>
            <KCombobox.ItemLabel>
              {props.item.rawValue.label}

              <KCombobox.ItemIndicator class={cbstyles.itemIndicator}>
                ✓
              </KCombobox.ItemIndicator>
            </KCombobox.ItemLabel>
          </KCombobox.Item>
        );
      }}
    >
      <KCombobox.Label class={cbstyles.label}>{props.label}</KCombobox.Label>
      <KCombobox.Control class={cbstyles.control}>
        {(state) => (
          <>
            <Show when={props.multiple}>
              <For each={state.selectedOptions()}>
                {(option) => (
                  <span
                    class={cbstyles.chip}
                    onPointerDown={(e) => e.stopPropagation()}
                  >
                    {option.label}
                    <button onClick={() => state.remove(option)}>x</button>
                  </span>
                )}
              </For>
            </Show>
            <KCombobox.Input class={cbstyles.input} />
            <KCombobox.Trigger class={cbstyles.trigger}>▼</KCombobox.Trigger>
          </>
        )}
      </KCombobox.Control>
      <KCombobox.ErrorMessage class={cbstyles.errorMessage}>
        {props.errorMessage}
      </KCombobox.ErrorMessage>
      <KCombobox.Content class={cbstyles.content}>
        <KCombobox.Listbox class={cbstyles.listbox} />
      </KCombobox.Content>
    </KCombobox>
  );
}
