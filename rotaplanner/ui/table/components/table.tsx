import {
  createEffect,
  createSignal,
  createResource,
  For,
  Show,
  createMemo,
  JSX,
  Component,
  useContext,
  createContext,
  Accessor,
  Match,
  Switch,
} from "solid-js";
import { createStore, reconcile } from "solid-js/store";
import { parseISO } from "date-fns";
import { ReactiveSet } from "@solid-primitives/set";
import styles from "./table.module.css";
import {
  TableApi,
  TableDataResult,
  UpdateLocationRequest,
  UpdateStaffRequest,
} from "../types";
import { registerDraggable } from "../dragdrop";
import { Temporal } from "@js-temporal/polyfill";
import { createSubscribedSignal, getTypedApi } from "../../../utils";

const api = getTypedApi<TableApi>();

function getTableData() {
  return api().data();
}
function postUpdateLocation(payload: UpdateLocationRequest) {
  return api().update_location(payload);
}
function postUpdateStaff(payload: UpdateStaffRequest) {
  return api().update_staff(payload);
}

type Activity = TableDataResult["activities"][number];

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
const TableQueryContext = createContext<TableDataResult>();

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
  const cell = createMemo<
    (Activity & { track: number; totalTracks: () => number })[]
  >(() => {
    const tracks: string[] = [];

    return (props.cells?.[props.date]?.[props.row] ?? [])
      .map((activityId) => {
        const activity = props.activities[activityId];
        if (!activity) {
          console.warn(
            `Activity with id ${activityId} not found in activities data`,
          );
          return null;
        }
        for (let i = 0; i < tracks.length; i++) {
          if (activity.activity_start >= tracks[i]) {
            tracks[i] = activity.activity_finish;
            return { ...activity, track: i, totalTracks: () => tracks.length };
          }
        }
        tracks.push(activity.activity_finish);
        return {
          ...activity,
          track: tracks.length - 1,
          totalTracks: () => tracks.length,
        };
      })
      .filter((activity) => activity !== null) as (Activity & {
      track: number;
      totalTracks: () => number;
    })[];
  });

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
      style={{
        position: "relative",
        "padding-top": `${cell()?.[0]?.totalTracks() * 5 + 5}px`,
      }}
    >
      <For each={cell()}>
        {(activity) => (
          <Switch>
            <Match when={props.tableType === "location"}>
              <LocationActivity activity={activity} />
            </Match>
            <Match when={props.tableType === "staff"}>
              <Switch>
                <Match when={props.row}>
                  <PersonActivity
                    activity={activity}
                    staff_id={props.row}
                    date={props.date}
                  />
                </Match>
                <Match when={!props.row}>
                  <ActivityWithoutAllocatedStaff
                    activity={activity}
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
function TimelineBar(props: { activity: Activity }): JSX.Element {
  const start = parseISO(props.activity.activity_start).getHours();
  const end = parseISO(props.activity.activity_finish).getHours();
  const duration = end - start;
  return (
    <div
      class={styles.timelineBar}
      style={{
        left: `${(start / 24) * 100}%`,
        width: `${(duration / 24) * 100}%`,
        top: `${props.activity.track * 5}px`,
      }}
    >
      &nbsp;
    </div>
  );
}
function LocationActivity(props: {
  activity: Activity & { track: number; totalTracks: () => number };
}): JSX.Element {
  const dragged = useContext(DragContext);
  const droptarget = useContext(DropTargetContext);
  const selection = useContext(SelectionContext);
  const tableQuery = useContext(TableQueryContext);
  let el: HTMLElement | null = null;
  return (
    <div class={styles.activityWrapper}>
      <TimelineBar activity={props.activity} />
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
          <For each={props.activity.roles}>
            {(role) => (
              <div class={styles.role}>
                <div class={styles.roleName}>{role.name}</div>
                <For each={role.assignments}>
                  {(assignment) => (
                    <div
                      class={styles.assignedStaff}
                      data-draggable="'.table-activity'"
                      id={`assn--${assignment.id}--${assignment.staff}`}
                      ref={(el) => registerDraggable(el, () => ".activity")}
                    >
                      {tableQuery?.staffData?.[assignment.staff]?.name ??
                        assignment.staff}
                    </div>
                  )}
                </For>
              </div>
            )}
          </For>
        </div>
      </div>
    </div>
  );
}

function ActivityWithoutAllocatedStaff(props: {
  activity: Activity & { track: number; totalTracks: () => number };
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

    for (const assignment of activity.assignments!) {
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

    if (unallocated) {
      ((activitiesByCell[activityDate] ??= {})["null"] ??= []).push(
        activity.id,
      );
    }
  }
  return activitiesByCell;
}

export default function Table() {
  const [dragged, setDragged] = createSignal<HTMLElement | null>(null);
  const [droptarget, setDroptarget] = createSignal<HTMLElement | null>(null);
  const [initial, setInitial] = createSignal<HTMLElement | null>(null);
  const [qualifier, setQualifier] = createSignal<{
    shiftKey: boolean;
    altKey: boolean;
    ctrlKey: boolean;
  }>({ shiftKey: false, altKey: false, ctrlKey: false });
  const selection = new ReactiveSet<HTMLElement>();
  const [tableQueryResult, setTableQueryResult] = createStore<TableDataResult>(
    null as unknown as TableDataResult,
  );
  const [activitiesByCell, setActivitiesByCell] = createStore<
    Record<string, any>
  >({});
  const [activities, updateActivities] = createStore<Record<string, Activity>>(
    {},
  );
  const [editingActivity, setEditingActivity] = createSignal<string | null>(
    null,
  );
  const [tableType, setTableType] = createSubscribedSignal("tableType");
  const [version, setVersion] = createSubscribedSignal("version");

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
  function processTableData(newdata: TableDataResult) {
    setTableQueryResult(reconcile(newdata));
    const newActivities: Record<string, TableDataResult["activities"][number]> =
      {};
    for (const activity of newdata.activities ?? []) {
      newActivities[activity.id] = activity;
    }
    console.log("Fetched activities", newActivities);
    updateActivities(reconcile(newActivities));
  }
  const [tableData] = createResource(version, () => getTableData());

  createEffect(() => {
    if (tableData()) {
      processTableData(tableData()!);
    }
  });

  createEffect(() => {
    if (tableType() === "location") {
      setActivitiesByCell(reconcile(activitiesByLocationCell(activities)));
    } else if (tableType() === "staff") {
      setActivitiesByCell(reconcile(activitiesByStaffCell(activities)));
    } else {
      console.warn(
        `Unknown table type: ${tableType()}, cannot compute activities by cell`,
      );
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
      if (tableType() !== "location" && tableType() !== "staff") {
        console.error(
          `Unknown table type: ${tableType()}, cannot process drop`,
        );
        return;
      }
      (tableType() === "location"
        ? postUpdateLocation(payload)
        : postUpdateStaff(payload)
      )
        .then((newdata) => setTableQueryResult(reconcile(newdata)))
        .catch((err) => {
          console.error("Error updating assignment", err);
        })
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
        api().open_activity_editor(activityId);
      }
    });
  };

  return (
    <TableQueryContext.Provider value={tableQueryResult}>
      <SelectionContext.Provider value={selection}>
        <div id="app" ref={attachListeners}>
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
                  ...((tableType() == "location"
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
                        tableType() == "location"
                          ? "locationsData"
                          : "staffData"
                      ]?.[row_header ?? "null"]?.name
                    }
                    i={i()}
                    dates={dates()}
                    cells={activitiesByCell}
                    activities={activities}
                    tableType={tableType()}
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
