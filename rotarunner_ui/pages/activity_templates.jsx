import styles from "./activity_templates.module.css";
import EditActivityTemplate from "./edit_activity";
import { Dialog } from "@suid/material";
import { createSignal, Show, For, createEffect } from "solid-js";

export default function ActivityTemplates(props) {
  const showTemplate = () => console.log("boo");
  const templates = [];
  const [editing, setEditing] = createSignal(null);
  let dialog;
  createEffect(() => {
    if (!!editing()) dialog.showModal();
  });
  return (
    <main>
      <dialog ref={dialog} onClose={() => setEditing(null)}>
        <Show when={!!editing()}>
          {editing()}
          <EditActivityTemplate activity={editing()} />
        </Show>
      </dialog>
      <div class={styles.templateContainerOuter}>
        <div class={styles.templateContainer}>
          <div class={styles.templateListHeader}>
            <div>Name</div>
            <div>From</div>
            <div>To</div>
          </div>
          <For
            each={templates}
            fallback={<div>No activity templates are currently defined</div>}
          >
            {(template) => (
              <a onclick={setEditing(template.id)} class={styles.templateEntry}>
                <div>{template.name}</div>
                <div>{template.date_range[0]}</div>
                <div>{template.date_range[1]}</div>
              </a>
            )}
          </For>
        </div>
      </div>
      <a onclick={() => setEditing("new")}>New template</a>
    </main>
  );
}
