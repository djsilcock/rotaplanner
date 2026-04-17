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
import {
  getTableData,
  GetTableDataResponse,
  postUpdateLocation,
  postUpdateStaff,
} from "../../../generated/client";

type Activity = GetTableDataResponse["activities"][number];

import { registerDraggable } from "../dragdrop";
import { useParams, createAsyncStore } from "@solidjs/router";
import { create, get, set } from "lodash";
import { Dialog } from "../../ui/components";
import { assert } from "chai";

//polyfill for Temporal API
import { Temporal } from "@js-temporal/polyfill";
import { Combobox, TextField } from "../../ui/formComponents";
import { createForm, getValues } from "@modular-forms/solid";

import { EditActivityDialog } from "./editActivity";
export const title = "Rota Planner";

function assertCustomEvent<T extends Record<string, unknown>>(
  event: Event,
): asserts event is CustomEvent<T> {
  if (!(event instanceof CustomEvent)) {
    throw new Error("Event is not a CustomEvent");
  }
}

const DropTargetContext = createContext<Accessor<HTMLElement | null>>();
const DragContext = createContext<Accessor<HTMLElement | null>>();
const SelectionContext = createContext<ReactiveSet<HTMLElement> | null>();
const QualifierContext =
  createContext<
    Accessor<{ shiftKey: boolean; altKey: boolean; ctrlKey: boolean }>
  >();
const TableQueryContext = createContext<GetTableDataResponse>();

interface TableRowProps {
  rowId: string;
  rowName: string;
  i?: number;
  dates: string[];
  cells: Record<string, Record<string, string[]>>;
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
  cells: Record<string, Record<string, string[]>>;
  activities: Record<string, Activity>;
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
        [styles.selected]: selection!.has(el!),
      }}
      id={`act--${props.activity.id}`}
      ref={(el) => registerDraggable(el, () => ".table-cell")}
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
  let el: HTMLDivElement | null = null;
  const register = (elem: HTMLDivElement) => {
    registerDraggable(elem, () => `.table-cell[data-date='${props.date}']`);
    el = elem;
  };
  console.log("Rendering unallocated activity", JSON.stringify(props.activity));
  return (
    <div
      classList={{
        [styles.activity]: true,
        activity: true,
        [styles.selected]: selection!.has?.(el!),
      }}
      id={`act--${props.activity.id}`}
      ref={register}
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
                ref={(el) =>
                  registerDraggable(
                    el,
                    () => `.table-cell[data-date='${props.date}']`,
                  )
                }
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
  const register = (elem: HTMLElement) => {
    registerDraggable(elem, () => `.table-cell[data-date='${props.date}']`);
    el = elem;
  };

  return (
    <div
      classList={{
        activity: true,
        [styles.activity]: true,
        [styles.selected]: selection?.has?.(el!),
      }}
      id={`act--${props.activity.id}`}
      ref={register}
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
                    ref={(el) =>
                      registerDraggable(
                        el,
                        () => `.table-cell[data-date='${props.date}']`,
                      )
                    }
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
function activitiesByLocationCell(
  activities: Record<string, Activity>,
): Record<string, any> {
  const activitiesByCell: Record<string, any> = {};

  for (const activity of Object.values(activities ?? {}).toSorted((a, b) =>
    a.activity_start < b.activity_start ? -1 : 1,
  )) {
    const activityDate = activity.activity_start.slice(0, 10);
    const locationId = activity.location;

    ((activitiesByCell[activityDate] ??= {})[locationId ?? "null"] ??= []).push(
      activity.id,
    );
  }
  return activitiesByCell;
}

function activitiesByStaffCell(
  activities: Record<string, Activity>,
): Record<string, Record<string, Activity[]>> {
  const activitiesByCell: Record<string, any> = {};

  for (const activity of Object.values(activities ?? {}).toSorted((a, b) =>
    a.activity_start.localeCompare(b.activity_start),
  )) {
    const activityDate = activity.activity_start.slice(0, 10);
    let unallocated = true;
    for (const timeslot of activity.timeslots!) {
      for (const assignment of timeslot.assignments!) {
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
      ((activitiesByCell[activityDate] ??= {})["null"] ??= []).push(
        activity.id,
      );
    }
  }
  return activitiesByCell;
}

export default function Table() {
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
  const [tableQueryResult, setTableQueryResult] =
    createStore<GetTableDataResponse>(null as unknown as GetTableDataResponse);
  const [activitiesByCell, setActivitiesByCell] = createStore<
    Record<string, any>
  >({});
  const [activities, updateActivities] = createStore<Record<string, Activity>>(
    {},
  );
  const [editingActivity, setEditingActivity] = createSignal<string | null>(
    null,
  );

  const dates = createMemo(() => {
    if (!tableQueryResult.dateRange) {
      return [];
    }
    const minDate = Temporal.PlainDate.from(tableQueryResult.dateRange.start);
    const maxDate = Temporal.PlainDate.from(tableQueryResult.dateRange.end);
    const days: string[] = [];
    for (
      let d = minDate;
      Temporal.PlainDate.compare(d, maxDate) <= 0;
      d = d.add({ days: 1 })
    ) {
      days.push(d.toString());
    }
    return days;
  });
  function processTableData(newdata: {
    data?: GetTableDataResponse;
    error?: any;
  }) {
    if (newdata.data) {
      setTableQueryResult(reconcile(newdata.data));
      const newActivities: Record<
        string,
        GetTableDataResponse["activities"][number]
      > = {};
      for (const activity of newdata.data.activities ?? []) {
        newActivities[activity.id] = activity;
      }
      console.log("Fetched activities", newActivities);
      updateActivities(reconcile(newActivities));
    } else if (newdata.error) {
      console.error("Failed to fetch table data");
    }
  }

  createEffect(() => {
    getTableData().then((newdata) => {
      processTableData(newdata);
    });
  });

  createEffect(() => {
    if (params.tableType === "location") {
      setActivitiesByCell(reconcile(activitiesByLocationCell(activities)));
    } else if (params.tableType === "staff") {
      setActivitiesByCell(reconcile(activitiesByStaffCell(activities)));
    } else {
      console.warn(`Unknown table type: ${params.tableType}`);
      setActivitiesByCell(reconcile({}));
    }
  });

  const attachListeners = (el: HTMLElement) => {
    el.addEventListener("dropped", (evt) => {
      assertCustomEvent<{
        initialTarget: HTMLElement;
        droptarget: HTMLElement;
        shiftKey: boolean;
        altKey: boolean;
        ctrlKey: boolean;
      }>(evt);
      const tableType = params.tableType;
      const payload = {
        draggedId: (evt.target as HTMLElement).id,
        initialDropzoneId: evt.detail.initialTarget.id,
        droptargetId: evt.detail.droptarget.id,
        shiftKey: evt.detail.shiftKey,
        altKey: evt.detail.altKey,
        ctrlKey: evt.detail.ctrlKey,
      };
      if (payload.initialDropzoneId === payload.droptargetId) {
        console.log("Dropped in the same cell, ignoring", payload);
        return;
      }
      if (tableType !== "location" && tableType !== "staff") {
        console.error(`Unknown table type: ${tableType}`);
        return;
      }
      (tableType === "location"
        ? postUpdateLocation({ body: payload })
        : postUpdateStaff({ body: payload })
      )
        .then((newdata) =>
          newdata.data ? setTableQueryResult(reconcile(newdata.data)) : null,
        )
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
        setEditingActivity(activityId);
      }
    });
  };

  return (
    <TableQueryContext.Provider value={tableQueryResult}>
      <SelectionContext.Provider value={selection}>
        <div id="app" ref={attachListeners}>
          table
          <Show when={editingActivity()}>
            <EditActivityDialog
              activity={activities[editingActivity()!]}
              onClose={() => setEditingActivity(null)}
              locationOptions={Object.values(
                tableQueryResult.locationsData ?? {},
              ).map((loc) => ({ value: loc.id, label: loc.name }))}
            />
          </Show>
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
                    rowId={row_header ?? "null"}
                    rowName={
                      tableQueryResult[
                        (params.tableType as string) == "location"
                          ? "locationsData"
                          : "staffData"
                      ]?.[row_header ?? "null"]?.name
                    }
                    i={i()}
                    dates={dates()}
                    cells={activitiesByCell}
                    activities={activities}
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
