import { createForm } from "./forms";
import { createEffect } from "solid-js";
import { unwrap } from "solid-js/store";

export default function TestForm(props) {
  const form = createForm({ onSubmit: (vals) => console.log(vals) });
  const field1 = form.registerField("some.deep.field1");
  const field2 = form.registerField("field2");
  createEffect(() => {
    console.log(unwrap(form.state.values));
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        form.submit();
      }}
    >
      <input onChange={(e) => field1.change(e.target.value)} />
      <input onChange={(e) => field2.change(e.target.value)} />
      <button>submit</button>
    </form>
  );
}
