import { Route, HashRouter as Router, useNavigate } from "@solidjs/router";
import { Show, createResource, createEffect } from "solid-js";
import { createSubscribedSignal } from "../../utils";
import Table from "../table/components/table";
import EditActivity from "../editactivity/editActivity";
import { waitForApi } from "../../utils";

/**
 * @typedef {Object} MenuItemProps
 * @property {string} href
 * @property {any} icon
 * @property {string} text
 */

function Layout(props) {
  const navigate = useNavigate();
  const [locationState, setLocation] = createSubscribedSignal("location");
  createEffect(() => {
    console.log("Location changed:", locationState());
    if (locationState()) navigate(locationState());
  });

  return (
    <div>
      <div style={{ padding: "1em" }}>{props.children}</div>
    </div>
  );
}

function IndexPage() {
  return <div>Hello!</div>;
}
function NotFound() {
  return <div>Not here!</div>;
}

export default function App() {
  const [apiReady] = createResource(waitForApi);
  return (
    <Show when={apiReady()} fallback={<div>Loading API...</div>}>
      <Router root={Layout}>
        <Route path="/" component={Table} />
        <Route path="/manage-activity-templates" component={NotFound} />
        <Route path="/edit-activity" component={EditActivity} />
        <Route path="*404" component={NotFound} />
      </Router>
    </Show>
  );
}
