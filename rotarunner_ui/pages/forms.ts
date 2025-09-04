import { createFormHook } from "@tanstack/solid-form";

import { onCleanup } from "solid-js";

import { createStore, reconcile, Store } from "solid-js/store";

const { use };

export function createForm<T>(options: Config<T>) {
  const [formState, setFormState] = createStore({});
  const form = ff_createForm({ ...options, mutators: { ...mutators } });
  form.subscribe(
    (a) => setFormState(reconcile(a)),
    Object.fromEntries(formSubscriptionItems.map((i) => [i, true]))
  );
  const registerField = <F extends T[keyof T]>(
    name: keyof T,
    config: FieldConfig<F>
  ): Store<FieldState<T[keyof T]>> => {
    const [fieldState, setFieldState] = createStore({});
    const unsubscribe = form.registerField(
      name,
      (newstate) => setFieldState(reconcile(newstate)),
      Object.fromEntries(fieldSubscriptionItems.map((i) => [i, true]))
    );
    onCleanup(unsubscribe);
    return fieldState as Store<FieldState<T[keyof T]>>;
  };
  return { ...form, state: formState, registerField };
}
