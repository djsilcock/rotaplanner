import {
  createEffect,
  createReaction,
  createSignal,
  Signal,
  For,
  onCleanup,
  Show,
  Suspense,
  createMemo,
  Switch,
  createResource,
  JSX,
  Component,
} from "solid-js";
import { differenceInCalendarDays, addDays, parseISO } from "date-fns";
import { createQuery, useQueryClient } from "@tanstack/solid-query";
import styles from "./table.module.css";
import { Batcher } from "./utils/batcher";
import { useParams } from "@solidjs/router";
import { createStore, produce ,unwrap,reconcile} from "solid-js/store";
import { create, debounce, get, set } from "lodash";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import Menu from "@suid/material/Menu";
import MenuItem from "@suid/material/MenuItem";
import { Match } from "solid-js";

import {
  activitiesByDate,
  tableConfig as getTableConfig,
  moveActivityInLocationGrid,
  moveActivityInStaffGrid,
  
} from "./client/sdk.gen";
import { LabelledUuid ,ActivityResponse} from "./client/types.gen";
import {
  activitiesByDateOptions,
  activitiesByDateQueryKey,
  tableConfigOptions,
} from "./client/@tanstack/solid-query.gen";

const epoch = new Date(2021, 0, 1);

/**
 * Converts a date to its ordinal representation based on a fixed epoch.
 * @param {Date} date - The date to convert.
 * @returns {number} - The ordinal representation of the date.
 */
export function toOrdinal(date:Date): number {
  return differenceInCalendarDays(date, epoch);
}

interface TableSegmentProps{
  date: Date;
  activities: Array<ActivityResponse>;
  y_axis: Array<LabelledUuid>;
  y_axis_type: string;
}
/**
 * TableSegment component to render a column of the table.
 * @param {Object} props - The properties passed to the component.
 * @param {Date} props.date - The date for the segment.
 * @param {Array} props.activities - Array of activities for the segment.
 * @param {Array} props.y_axis - Array of y-axis data.
 * @param {string} props.y_axis_type - Type of y-axis data.
 * @returns {JSX.Element} - The rendered TableSegment component.
 */
const TableSegment: Component<TableSegmentProps> = (props): JSX.Element => {
  const activitiesByRow = createMemo(() => {
    return Object.fromEntries((props.y_axis || []).map((staff_or_location) => {
      return [
        staff_or_location.id,
        props.activities.filter((activity) => {
          if (props.y_axis_type === "staff") {
            return activity.staff_assignments.some(
              (assignment) => assignment.staff.id === staff_or_location.id
            );
          } else if (props.y_axis_type === "location") {
            return activity.location?.id === staff_or_location.id;
          }
          return false;
        }),
      ];
    }));
  })
  const unassignedActivities = createMemo(() => {
    return props.activities.filter((activity) => {
      if (props.y_axis_type === "staff") {
        return activity.staff_assignments.length === 0;
      } else if (props.y_axis_type === "location") {
        return !activity.location;
      }
      return false;
    });
   })
  return (
    <div class={styles.rotaSegment}>
      <div
        classList={{
          [styles.columnHeader]: true,
          [styles.weekend]:
            props.date.getDay() === 0 || props.date.getDay() === 6,
        }}
      >
        {props.date.toLocaleDateString("en-GB", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        })}
      </div>

      <For each={props.y_axis}>
        {(staff_or_location, index) => (
          <ActivityCell
            staff_or_location={staff_or_location.id}
            activities={activitiesByRow()[staff_or_location.id]}
            staff={props.y_axis_type == "staff" ? staff_or_location.id : null}
            location={
              props.y_axis_type == "location" ? staff_or_location.id : null
            }
            y_axis_type={props.y_axis_type}
            i={index()}
            date={props.date}
          />
        )}
      </For>
      <ActivityCell
        date={props.date}
        activities={unassignedActivities()}
        i={props.y_axis?.length}
        staff_or_location={undefined}
        y_axis_type={props.y_axis_type}
      />
    </div>
  );
}

interface ActiveMenuInfo {
  ref: HTMLElement;
  date: string;
  staff_or_location: string;
  items: any[];
}
const [activeMenu, setActiveMenu] = createSignal<ActiveMenuInfo|null>(null);

const DEFAULT_SEGMENT_WIDTH = 1;

async function throwIfError<T>(resource: Promise<{ data: T; error: any }>):Promise<T> { 
  const { data, error } = await resource;
  if (error) {
    throw error;
  }
  return data;
}
function createDeepSignal<T>(value: T): Signal<T> {
  const [store, setStore] = createStore({
    value,
  })
  return [
    () => store.value,
    (v: T) => {
      const unwrapped = unwrap(store.value)
      typeof v === "function" && (v = v(unwrapped))
      setStore("value", reconcile(v))
      return store.value
    },
  ] as Signal<T>
}

interface TableConfig {
    y_axis: LabelledUuid[];
    dates: Date[]
    
    activitiesByDate: Record<string, ActivityResponse[]> 
  }
/**
 *
 * @param {object} props
 * @param {string} props.y_axis_type - Type of y-axis data (staff or location).
 * @returns {JSX.Element}
 * Table component to render the main table.
 */
function Table(props: { y_axis_type: "location"|"staff"; }): JSX.Element {
  const client = useQueryClient();
  
  const [tableConfig, editTable] = createStore <TableConfig>({
    y_axis: [],
    dates: [],
    activitiesByDate: {},
  });
  
  createEffect(async () => {
    const tableConfig = await throwIfError(getTableConfig({
      path: { location_or_staff: props.y_axis_type }
    }));
    editTable("y_axis", tableConfig?.y_axis!);
    const dates = Array.from(
      { length: differenceInCalendarDays(parseISO(tableConfig?.date_range.finish!), parseISO(tableConfig?.date_range.start!)) },
      (_, i) => {
        return addDays(parseISO(tableConfig?.date_range.start!), i);
      }
    )
    editTable("dates", dates);
    const activitiesData = await throwIfError(activitiesByDate({
      query: { start_date: tableConfig?.date_range.start, finish_date: tableConfig?.date_range.finish },
    }));
    activitiesData?.forEach((item) => {
      editTable("activitiesByDate", item.date, item.activities);
    });
  });
  
  
  
  let parentRef;

  const allocateToStaff = (itemid:string) => {
    if (activeMenu()==null) return;
    moveActivityInStaffGrid({
      body: {
        new_staff: activeMenu()!.staff_or_location,
        activity_id: itemid,
      },
    }).then(handleMoveResponse);
  };
  const moveActivityHere = (itemid:string) => {
    throwIfError(moveActivityInLocationGrid({
      body: {
        new_location: activeMenu()!.staff_or_location,
        activity_id: itemid,
      },
    }));
  };
  const handleMoveResponse = (response) => {
    if (response.error) {
      alert(response.error);
    } else {
      response.data.data.forEach((item) =>
        client.setQueryData(
          activitiesByDateQueryKey({ query: { date: item.date } }),
          item.activities
        )
      );
    }
    setActiveMenu(null);
  };

  return (
    <Show when={true} fallback={<div>Loading...</div>}>
      <Menu
        open={!!activeMenu()}
        anchorEl={activeMenu()?.ref}
        onClose={() => setActiveMenu(null)}
      >
        <MenuItem>Create Activity</MenuItem>
        <For each={activeMenu()?.items}>
          {(item) => (
            <Switch>
              <Match when={props.y_axis_type == "staff"}>
                <MenuItem
                  onClick={() => {
                    allocateToStaff(item.id);
                  }}
                >
                  Allocate to {item.name}
                </MenuItem>
              </Match>

              <Match when={props.y_axis_type == "location"}>
                <MenuItem
                  onClick={() => {
                    moveActivityHere(item.id);
                  }}
                >
                  Move {item.name} here
                </MenuItem>
              </Match>
            </Switch>
          )}
        </For>
      </Menu>
      <div
        class={styles.rotaTable}
        style={{
          "grid-template-rows": `repeat(${tableConfig.y_axis.length + 2},auto)`,
        }}
      >
        <div class={styles.rowHeader}></div>
        <For each={tableConfig.y_axis} fallback={<div></div>}>
          {(staff_or_location, index) => (
            <div class={styles.rowHeader}>{staff_or_location.name}</div>
          )}
        </For>

        <For each={tableConfig.dates} fallback={<div></div>}>
          {(date) => {
            return (
              <TableSegment
                date={date}
                activities={tableConfig.activitiesByDate[date.toISOString().slice(0, 10)]}
                y_axis={tableConfig.y_axis}
                y_axis_type={props.y_axis_type}
              />
            );
          }}
        </For>
      </div>
    </Show>
  );
}

function filterActivitiesStaffView(date:string, activities:ActivityResponse[], staff:string|undefined) {
  //filter and map activities in staff view
  console.log("filterActivitiesStaffView", date, activities, staff);
  return (
    activities
      .filter((activity) => {
        try {
          if (staff) {
            return activity.staff_assignments.some(
              (assignment) => assignment.staff.id === staff
            );
          }
          return activity.staff_assignments.length == 0;
        } catch (e) {
          console.error(e, activity);
          return false;
        }
      })
      .map((item) => ({
        ...item,
        original_date: date,
        original_staff: staff,
        id: `${item.id}-${staff}`,
        activity_id: item.id,
      })) ?? []
  );
}
function filterActivitiesLocationView(date:string, activities:ActivityResponse[], location:string|undefined) {
  //filter and map activities in location view

  return activities
    .filter((activity) => {
      if (location) {
        return activity.location?.id === location;
      }
      return !activity.location;
    })
    .map((item) => ({
      ...item,
      original_date: date,
      original_location: location,
      id: `${item.id}-${location}`,
      activity_id: item.id,
    }));
}
interface ActivityCellProps {
  date: Date;
  y_axis_type: string;
  staff_or_location?: string;
  i?: number;
  activities: ActivityResponse[];
}
/**
 * ActivityCell component to render a cell in the table.
 * @param {Object} props - The properties passed to the component.
 * @param {Date} props.date - The date for the cell.
 * @param {string} props.y_axis_type - Type of y-axis data (staff or location).
 * @param {string} [props.staff_or_location] - The staff or location ID.
 * @param {number} [props.i] - Index of the cell.
 * @returns {JSX.Element} - The rendered ActivityCell component.
 */
export const ActivityCell:Component<ActivityCellProps>=(props)=>{
  const isoDate = () => props.date.toISOString().slice(0, 10);
  const selector = (data:ActivityResponse[]) => {
    if (props.y_axis_type === "staff") {
      return filterActivitiesStaffView(
        isoDate(),
        data,
        props.staff_or_location
      );
    }
    if (props.y_axis_type === "location") {
      return filterActivitiesLocationView(
        isoDate(),
        data,
        props.staff_or_location
      );
    }
    throw new Error("Invalid y_axis_type");
  };
  const [items, setItems] = createSignal([]);
  const cellActivities = createMemo(()=>selector(props.activities))
  createEffect(() => {
    if (cellActivities.data) setItems(selector(cellActivities.data));
  });

  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };
  const client = useQueryClient();
  const handleFinalMove = ({ detail }) => {
    setItems(detail.items);
    if (detail.info.trigger == TRIGGERS.DROPPED_INTO_ZONE) {
      const movedItem = items().find((i) => i.id == detail.info.id);
      if (props.y_axis_type == "staff") {
        moveActivityInStaffGrid({
          body: {
            original_date: movedItem.original_date,
            new_date: isoDate(),
            original_staff: movedItem.original_staff,
            new_staff: props.staff_or_location,
            activity_id: movedItem.activity_id,
          },
        }).then(handleMoveResponse);
      } else if (props.y_axis_type == "location") {
        moveActivityInLocationGrid({
          body: {
            original_date: movedItem.original_date,
            new_date: isoDate(),
            original_location: movedItem.original_location,
            new_location: props.staff_or_location,
            activity_id: movedItem.activity_id,
          },
        }).then(handleMoveResponse);
      }
    }
  };

  let cellRef;
  return (
    <Suspense fallback={<div></div>}>
      <div
        classList={{
          [styles.activityCell]: !!props.staff_or_location,
          [styles.unallocatedActivities]: !props.staff_or_location,
          [styles.weekend]:
            props.date.getDay() === 0 || props.date.getDay() === 6,
        }}
        data-date={toOrdinal(props.date)}
        data-yaxis={props.i}
        id={`td-${toOrdinal(props.date)}-${props.i}`}
        use:dndzone={{
          items,
        }}
        on:consider={handleMove}
        on:finalize={handleFinalMove}
        on:contextmenu={(e) => {
          setActiveMenu({
            ref: e.target,
            date: isoDate(),
            staff_or_location: props.staff_or_location,
            items: cellActivities.data,
          });
          e.preventDefault();
        }}
        ref={cellRef}
      >
        <For each={items()} fallback={<div>&nbsp;</div>}>
          {(act) => (
            <Activity
              activity_def={act}
              staff_or_location={props.staff_or_location}
              show_staff={true}
            />
          )}
        </For>
      </div>
    </Suspense>
  );
}

/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {Object} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Activity component.
 */
export function Activity(props: { activity_def: object; staff_or_location?: object; }): JSX.Element {
  return (
    <div class={styles.activity}>
      <div class={styles.activityName}>{props.activity_def.name}</div>
      <Show
        when={
          props.activity_def.location &&
          //props.staff_or_location &&
          props.staff_or_location !== props.activity_def.location.id
        }
      >
        <div class={styles.activityLocation}>
          {props.activity_def.location.name}
        </div>
      </Show>

      <For each={props.activity_def.staff_assignments}>
        {(assignment) => (
          <Show when={assignment.staff.id !== props.staff_or_location}>
            <div class={styles.assignment}>
              {assignment.staff.name}
              <Show when={assignment.times}>{assignment.times}</Show>
            </div>
          </Show>
        )}
      </For>
    </div>
  );
}

export default Table;
