import {
  createEffect,
  createSignal,
  For,
  Show,
  Suspense,
  createMemo,
  JSX,
  Component,
  lazy,
  useContext,
  createContext,
  Accessor,
  Match,
  Switch,
} from "solid-js";
import { createStore, produce, reconcile } from "solid-js/store";
import {
  differenceInCalendarDays,
  parseISO,
  eachDayOfInterval,
} from "date-fns";
import { applyPatch } from "fast-json-patch";
import { ReactiveSet } from "@solid-primitives/set";

import styles from "./table.module.css";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import { Dynamic } from "solid-js/web";
import D from "../../../../rotarunner_ui/dist/assets/activity_templates-chdWMDqn";
import { registerDraggable } from "../dragdrop";
import { useParams, createAsyncStore } from "@solidjs/router";
import { create } from "lodash";
import { Dialog } from "../../ui";

export const title = "Rota Planner";

const DropTargetContext = createContext<Accessor<HTMLElement | null>>();
const DragContext = createContext<Accessor<HTMLElement | null>>();
const SelectionContext = createContext<ReactiveSet<HTMLElement> | null>();
const QualifierContext =
  createContext<
    Accessor<{ shiftKey: boolean; altKey: boolean; ctrlKey: boolean }>
  >();

interface TableRowProps {
  rowId: string;
  rowName: string;
  i?: number;
  dates: Date[];
  cells: Map<string, any>;
  tableType: string;
  activities: Record<string, any>;
}
function TableRow(props: TableRowProps): JSX.Element {
  return (
    <tr>
      <td class={styles.rowHeader}>{props.rowName}</td>
      <For each={props.dates}>
        {(date) => (
          <TableCell
            row={props.rowId}
            date={date}
            cells={props.cells}
            tableType={props.tableType}
            activities={props.activities}
          />
        )}
      </For>
    </tr>
  );
}
function TableCell(props: {
  row: string;
  date: string;
  cells: Record<string, any>;
  activities: Record<string, any>;
  tableType: string;
}): JSX.Element {
  const cell = () => props.cells?.[props.date]?.[props.row] ?? [];

  let el: HTMLTableCellElement = undefined as unknown as HTMLTableCellElement;
  return (
    <td
      ref={el}
      id={`cell--${props.row}--${props.date}`}
      classList={{
        [styles.activityCell]: true,
        "table-cell": true,
      }}
      data-date={props.date}
      title={JSON.stringify({ cell: cell(), date: props.date, row: props.row })}
    >
      <For each={cell()}>
        {(activity) => (
          <Switch>
            <Match when={props.tableType === "location"}>
              <LocationActivity activity={props.activities[activity]} />
            </Match>
            <Match when={props.tableType === "staff"}>
              <Switch>
                <Match when={props.row}>
                  <PersonActivity
                    activity={props.activities[activity]}
                    staff_id={props.row}
                    date={props.date}
                  />
                </Match>
                <Match when={!props.row}>
                  <ActivityWithoutAllocatedStaff
                    activity={props.activities[activity]}
                    date={props.date}
                  />
                </Match>
              </Switch>
            </Match>
            <Match when={true}>!{props.tableType}</Match>
          </Switch>
        )}
      </For>
    </td>
  );
}

function LocationActivity(props: { activity: any }): JSX.Element {
  const dragged = useContext(DragContext);
  const droptarget = useContext(DropTargetContext);
  const selection = useContext(SelectionContext);
  const tableQuery = useContext(TableQueryContext);
  let el: HTMLElement | null = null;
  return (
    <div
      classList={{
        [styles.activity]: true,
        activity: true,
        [styles.selected]: selection!.has(el),
      }}
      id={`act--${props.activity.id}`}
      use:registerDraggable=".table-cell"
    >
      <div class={styles.activityName} title={JSON.stringify(props.activity)}>
        {props.activity.name}
      </div>
      <div class={styles.activityTime}>
        {props.activity.activity_start.slice(11, 16)} -{" "}
        {props.activity.activity_finish.slice(11, 16)}
      </div>
      <hr />
      <div>
        <For each={props.activity.timeslots}>
          {(timeslot) => (
            <div
              classList={{
                [styles.timeslot]: true,
              }}
              id={`timeslot--${timeslot.id}`}
            >
              <div class={styles.activityTime}>
                {timeslot.start.slice(11, 16)} - {timeslot.finish.slice(11, 16)}
              </div>
              <For each={timeslot.assignments}>
                {(assignment) => (
                  <div
                    class={styles.assignedStaff}
                    data-draggable="'.table-timeslot,.table-activity'"
                    id={`assn--${assignment.id}--${assignment.staff}`}
                  >
                    {tableQuery?.staffData?.[assignment.staff]?.name ??
                      assignment.staff}
                  </div>
                )}
              </For>
              <Show when={timeslot.assignments.length === 0}>...</Show>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}

function ActivityWithoutAllocatedStaff(props: {
  activity: any;
  date: string;
}): JSX.Element {
  const selection = useContext(SelectionContext);
  let el: HTMLDivElement = null;
  return (
    <div
      classList={{
        [styles.activity]: true,
        activity: true,
        [styles.selected]: selection!.has?.(el),
      }}
      id={`act--${props.activity.id}`}
      ref={el}
      use:registerDraggable=".table-cell"
    >
      <div class={styles.activityName}>{props.activity.name}</div>
      <div class={styles.activityTime}>
        {props.activity.activity_start.slice(11, 16)} -{" "}
        {props.activity.activity_finish.slice(11, 16)}
      </div>
      <hr />
      <div>
        <For each={props.activity.timeslots}>
          {(timeslot) => (
            <Show when={timeslot.assignments.length === 0}>
              <div
                classList={{
                  [styles.timeslot]: true,
                }}
                id={`timeslot--${timeslot.id}`}
                use:registerDraggable=".table-cell"
              >
                <div class={styles.activityTime}>
                  {timeslot.start.slice(11, 16)} -{" "}
                  {timeslot.finish.slice(11, 16)}
                </div>
              </div>
            </Show>
          )}
        </For>
      </div>
    </div>
  );
}

function PersonActivity(props: {
  activity: any;
  staff_id: string;
  date: string;
}): JSX.Element {
  const selection = useContext(SelectionContext);
  let el: HTMLElement | null = null;
  return (
    <div
      classList={{
        activity: true,
        [styles.activity]: true,
        [styles.selected]: selection.has?.(el),
      }}
      id={`act--${props.activity.id}`}
      ref={el}
      use:registerDraggable={`.table-cell[data-date='${props.date}']`}
    >
      <div class={styles.activityName}>{props.activity.name}</div>
      <div class={styles.activityTime}>
        {props.activity.activity_start.slice(11, 16)} -{" "}
        {props.activity.activity_finish.slice(11, 16)}
      </div>
      <hr />
      <div>
        <For each={props.activity.timeslots}>
          {(timeslot) => (
            <For each={timeslot.assignments}>
              {(assignment) => (
                <Show when={assignment.staff == props.staff_id}>
                  <div
                    classList={{
                      [styles.timeslot]: true,
                    }}
                    id={`timeslot--${timeslot.id}`}
                    use:registerDraggable={`.table-cell[data-date='${props.date}']`}
                  >
                    <div class={styles.activityTime}>
                      {timeslot.start.slice(11, 16)} -{" "}
                      {timeslot.finish.slice(11, 16)}
                    </div>
                  </div>
                </Show>
              )}
            </For>
          )}
        </For>
      </div>
    </div>
  );
}
function activitiesByLocationCell(tableQueryResult): Record<string, any> {
  const activitiesByCell: Record<string, any> = {};
  for (const date of (tableQueryResult.dates ?? []).map((d) =>
    d.slice(0, 10),
  )) {
    activitiesByCell[date] = {};
    for (const row_header of tableQueryResult.locations) {
      activitiesByCell[date][row_header] = [];
    }
    activitiesByCell[date][null] = [];
  }
  for (const activity of Object.values(
    tableQueryResult.activities ?? {},
  ).toSorted((a, b) => (a.activity_start < b.activity_start ? -1 : 1))) {
    const activityDate = activity.activity_start.slice(0, 10);
    const locationId = activity.location;

    ((activitiesByCell[activityDate] ??= {})[null] ??= []).push(activity.id);
  }
  return activitiesByCell;
}

function activitiesByStaffCell(tableQueryResult): Record<string, any> {
  const activitiesByCell: Record<string, any> = {};

  for (const activity of Object.values(
    tableQueryResult.activities ?? {},
  ).toSorted((a, b) => a.activity_start.localeCompare(b.activity_start))) {
    const activityDate = activity.activity_start.slice(0, 10);
    let unallocated = true;
    for (const timeslot of activity.timeslots) {
      for (const assignment of timeslot.assignments) {
        const staffId = assignment.staff;
        if (
          !((activitiesByCell[activityDate] ??= {})[staffId] ??= []).includes(
            activity.id,
          )
        ) {
          activitiesByCell[activityDate][staffId].push(activity.id);
          unallocated = false;
        }
      }
    }
    if (unallocated) {
      ((activitiesByCell[activityDate] ??= {})[null] ??= []).push(activity.id);
    }
  }
  return activitiesByCell;
}
const TableQueryContext = createContext();

export default function Table(props) {
  const params = useParams();
  const [dragged, setDragged] = createSignal<HTMLElement | null>(null);
  const [droptarget, setDroptarget] = createSignal<HTMLElement | null>(null);
  const [initial, setInitial] = createSignal<HTMLElement | null>(null);
  const [qualifier, setQualifier] = createSignal<{
    shiftKey: boolean;
    altKey: boolean;
    ctrlKey: boolean;
  }>({ shiftKey: false, altKey: false, ctrlKey: false });
  const selection = new ReactiveSet<HTMLElement>();
  const [tableQueryResult, setTableQueryResult] = createStore<any>({});
  const [activitiesByCell, setActivitiesByCell] = createStore<any>({});
  const dates = createMemo(() => {
    if (!tableQueryResult.dateRange) {
      return [];
    }
    const minDate = parseISO(tableQueryResult.dateRange?.start);
    const maxDate = parseISO(tableQueryResult.dateRange?.end);
    return eachDayOfInterval({ start: minDate, end: maxDate }).map((d) =>
      d.toISOString().slice(0, 10),
    );
  });
  createEffect(() => {
    fetch(`/api/table/data`)
      .then((res) => res.json())
      .then((newdata) => setTableQueryResult(reconcile(newdata)));
  });
  createEffect(() => {
    console.log("Recomputing activities by cell");
    if (!tableQueryResult.queryVersion) {
      console.log("no data yet");
      return;
    }
    if (params.tableType === "location") {
      setActivitiesByCell(
        reconcile(activitiesByLocationCell(tableQueryResult)),
      );
    } else if (params.tableType === "staff") {
      setActivitiesByCell(reconcile(activitiesByStaffCell(tableQueryResult)));
    } else {
      console.warn(`Unknown table type: ${params.tableType}`);
      setActivitiesByCell(reconcile({}));
    }
  });

  const attachListeners = (el: HTMLElement) => {
    el.addEventListener("dropped", (evt) => {
      const tableType = params.tableType;
      const payload = {
        draggedId: evt.target.id,
        initialDropzoneId: evt.detail.initialTarget?.id,
        droptargetId: evt.detail.droptarget?.id,
        shiftKey: evt.detail.shiftKey,
        altKey: evt.detail.altKey,
        ctrlKey: evt.detail.ctrlKey,
      };
      fetch(`/api/table/by_${tableType}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })
        .then((res) => res.json())
        .then((newdata) => setTableQueryResult(reconcile(newdata)))
        .finally(() => {
          setDroptarget(null);
          setDragged(null);
          setQualifier({ shiftKey: false, altKey: false, ctrlKey: false });
        });
    });
    el.addEventListener("dblclick", (evt) => {
      const target = (evt.target as HTMLElement).closest(
        ".activity",
      ) as HTMLElement;
      console.log("Double click on", target);
      if (target.classList.contains("activity")) {
        const activityId = target.id.split("--")[1];
        window.open(`/activity/${activityId}`, "_blank");
      }
    });
  };

  return (
    <TableQueryContext.Provider value={tableQueryResult}>
      <SelectionContext.Provider value={selection}>
        <div id="app" ref={attachListeners}>
          table
          <table
            classList={{
              [styles.rotaTable]: true,
            }}
          >
            <thead>
              <tr>
                <td></td>
                <For each={dates()}>
                  {(date) => <td class={styles.columnHeader}>{date}</td>}
                </For>
              </tr>
            </thead>
            <tbody>
              <For
                each={[
                  ...((params.tableType == "location"
                    ? tableQueryResult.locations
                    : tableQueryResult.staff) ?? []),
                  null,
                ]}
              >
                {(row_header, i) => (
                  <TableRow
                    rowId={row_header}
                    rowName={
                      tableQueryResult[
                        (params.tableType as string) == "location"
                          ? "locationsData"
                          : "staffData"
                      ]?.[row_header]?.name
                    }
                    i={i()}
                    dates={dates()}
                    cells={activitiesByCell}
                    activities={tableQueryResult.activities}
                    tableType={params.tableType as string}
                  />
                )}
              </For>
            </tbody>
          </table>
        </div>
      </SelectionContext.Provider>
    </TableQueryContext.Provider>
  );
}
