import { Accessor, createEffect, createSignal } from "solid-js";

export function createSubscribedSignal<T>(
  stateKey: string,
): [Accessor<T>, (value: T) => void] {
  if (!(window as any).pywebview?.state) {
    throw new Error("window.pywebview.state is not defined");
  }
  const [signal, setSignal] = createSignal<T>(
    (window as any).pywebview.state[stateKey] as T,
  );
  createEffect(() => {
    if ((window as any).pywebview.state[stateKey] != signal()) {
      (window as any).pywebview.state[stateKey] = signal();
    }
  });

  (window as any).pywebview.state.addEventListener(
    "change",
    (event: CustomEvent) => {
      if (event.detail.key === stateKey) {
        setSignal((window as any).pywebview.state[stateKey]);
      }
    },
  );
  return [signal, setSignal];
}

export function getTypedApi<T>(): () => T {
  return () => {
    if (!(window as any).pywebview) {
      throw new Error("window.pywebview is not defined");
    }
    if (!(window as any).pywebview.api) {
      throw new Error("window.pywebview.api is not defined");
    }
    return (window as any).pywebview.api as T;
  };
}

export async function waitForApi(): Promise<any> {
  const { promise, resolve } = Promise.withResolvers();

  window.addEventListener("pywebviewready", () => {
    resolve((window as any).pywebview.api);
  });

  if ((window as any).pywebview?.api) {
    resolve((window as any).pywebview.api);
  }
  return promise;
}
