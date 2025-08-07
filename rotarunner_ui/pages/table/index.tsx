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
import { Batcher } from "../../../frontend/src/utils/batcher";
import { useParams } from "@solidjs/router";
import { createStore, produce ,unwrap,reconcile} from "solid-js/store";
import { create, debounce, get, set } from "lodash";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import Menu from "@suid/material/Menu";
import MenuItem from "@suid/material/MenuItem";
import { Match } from "solid-js";


import {
  getActivitiesByDate,
  tableConfig as getTableConfig,
  moveActivityInLocationGrid,
  moveActivityInStaffGrid,
  
} from "../../generatedTypes/sdk.gen";
import { LabelledUuid ,ActivityDisplay,ActivityResponse} from "../../generatedTypes/types.gen";
import {
  activitiesByDateOptions,
  activitiesByDateQueryKey,
  tableConfigOptions,
} from "../../../frontend/src/client/@tanstack/solid-query.gen";
import { Celebration } from "@suid/icons-material";

const epoch = new Date(2021, 0, 1);

function retry(fn: (...arg:any) => Promise<any>, { retries = 3, delay = 500 }): () => Promise<any> {
  return async (...arg) => {
    let lastError;
    for (let i = 0; i < retries; i++) {
      try {
        return await fn(...arg);
      } catch (error) {
        lastError = error;
      }
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
    throw lastError;
  }
}

/**
 * Converts a date to its ordinal representation based on a fixed epoch.
 * @param {Date} date - The date to convert.
 * @returns {number} - The ordinal representation of the date.
 */
export function toOrdinal(date:Date): number {
  return differenceInCalendarDays(date, epoch);
}

function filterActivities(activities: ActivityResponse, date: Date, staff_or_location: string|undefined, y_axis_type: string): Array<ActivityDisplay> {
  const activitiesForDay=activities[date.toISOString().slice(0, 10)] || [];
  return activitiesForDay.filter((activity) => {
    if (y_axis_type === "staff") {
      if (!staff_or_location) {
        return activity.staff_assignments.length === 0;
      }
      return activity.staff_assignments.some(
        (assignment) => assignment.staff.id === staff_or_location
      );
    } else if (y_axis_type === "location") {
      return activity.location?.id === staff_or_location;
    }
    return false;
  });
}


interface ActiveMenuInfo {
  ref: HTMLElement;
  date: string;
  staff_or_location: string;
  items: any[];
}
const [activeMenu, setActiveMenu] = createSignal<ActiveMenuInfo|null>(null);

const DEFAULT_SEGMENT_WIDTH = 1;

function throwIfError<T>({ data, error}:{data:T,error:any}):T { 
  if (error) {
    throw error;
  }
  return data;
}


interface TableConfig {
  staff: LabelledUuid[];
  locations: LabelledUuid[];
  dates: Date[];
}
  
interface TableProps {
  y_axis_type: "location" | "staff";}
/**
 *
 * @param {object} props
 * @param {string} props.y_axis_type - Type of y-axis data (staff or location).
 * @returns {JSX.Element}
 * Table component to render the main table.
 */
function Table(props: TableProps): JSX.Element {
  const client = useQueryClient();
  const [tableConfigResponse, { refetch: refetchTableConfig }] = createResource(() => getTableConfig().then(throwIfError))
  const tableConfig: TableConfig = (() => {
    const datesMemo = createMemo(() => {
      if (!tableConfigResponse()?.date_range) return [];
      // Generate dates from start to finish date in the date range
      const start = parseISO(tableConfigResponse()?.date_range.start || "");
      const finish = parseISO(tableConfigResponse()?.date_range.finish || "");
      return Array.from(
        { length: differenceInCalendarDays(finish, start) + 1 },
        (_, i) => addDays(start, i)
      );
    })
    return {
      get staff() { return tableConfigResponse()?.staff ?? [] },
      get locations() { return tableConfigResponse()?.locations ?? [] },
    
      get dates() {
        return datesMemo();
      }
    }
  })()

  const [activitiesData, updateActivitiesData] = createStore({})
  
  const c = (retry(
    (_) => getActivitiesByDate({
      query: {},
    }), { retries: 3 }))()
  c.then(({ data, error }) => {
    if (error) {
      console.error("Error fetching activities:", error);
      return;
    }
    updateActivitiesData(data);
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
  const y_axis = createMemo(() => {
    if (props.y_axis_type === "staff") {
      return tableConfig.staff;
    }
    return tableConfig.locations;
  });

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
      <table class={styles.rotaTable}>
        <thead>
        <tr>
          <td></td>
          <For each={tableConfig.dates} fallback={<td></td>}>
            {(date) => (<td>{date.toISOString().slice(0, 10)}</td>)}
          </For>
          </tr>
        </thead>
        <tbody>
        <For each={y_axis()}>
          
          {(staff_or_location, index) => (
            <tr>
              <td class={styles.rowHeader}>{staff_or_location.name}</td>
              <For each={tableConfig.dates} fallback={<td></td>}>
                {(date) => (
                  <ActivityCell
                    activities={activitiesData}
                    row_id={staff_or_location?.id}
                    row_id={staff_or_location.id}
                    y_axis_type={props.y_axis_type}
                    i={index()}
                      date={date}
                      updateActivities={(newActivities: ActivityResponse) => {
                        updateActivitiesData(newActivities);
                      }}
                    />
                  )}
              </For>
            </tr>
            )}
        </For>
        </tbody>
      </table>
    </Show>
  );
}

function filterActivitiesStaffView(date:string, activities:ActivityDisplay[], staff:string|undefined) {
  //filter and map activities in staff view
  console.log("filterActivitiesStaffView", date, activities, staff);
  return (
    activities
      ?.filter((activity) => {
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
        id: `${item.activity_id}-${staff}`,
        activity_id: item.activity_id,
      })) ?? []
  );
}
interface DraggableActivity extends ActivityDisplay {
  original_date: string;
  original_staff?: string;
  original_location?: string;
  id: string; // Unique ID for the draggable item
}
function filterActivitiesLocationView(date:string, activities:ActivityDisplay[], location:string|undefined): DraggableActivity[] {
  //filter and map activities in location view

  return activities
    ?.filter((activity) => {
      if (location) {
        return activity.location?.id === location;
      }
      return !activity.location;
    })
    .map((item) => ({
      ...item,
      original_date: date,
      original_location: location,
      id: `${item.activity_id}-${location}`
    }));
}
interface ActivityCellProps {
  date: Date;
  y_axis_type: "staff" | "location";
  row_id?: string;
  i?: number;
  activities: ActivityResponse;
  updateActivities: (newActivities: ActivityResponse) => void;
}
type APIResponse<R> = { error: any; data: undefined } | { error: undefined; data: R };
export const ActivityCell:Component<ActivityCellProps>=(props)=>{
  const isoDate = () => props.date.toISOString().slice(0, 10);
  
  const [items, setItems] = createSignal<DraggableActivity[]>([]);
  const cellActivities = createMemo(() => ((props.y_axis_type == "staff" ? filterActivitiesStaffView : filterActivitiesLocationView)(isoDate(), props.activities[isoDate()], props.row_id)) ?? [])
  createEffect(() => {
    // Update items when cellActivities changes
    setItems(cellActivities());
  });
  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };
  const client = useQueryClient();
  const handleMoveResponse = ({ error, data }: APIResponse<ActivityResponse>) => {
          if (error) {
            console.error("Error moving activity:", error);
            return;
          }
          props.updateActivities(data as ActivityResponse);
        }
  const handleFinalMove = ({ detail }) => {
    setItems(detail.items);
    if (detail.info.trigger == TRIGGERS.DROPPED_INTO_ZONE) {
      console.log("Finalizing move", detail);
      const movedItem = detail.items.find((i) => i.id == detail.info.id);
      if (!movedItem) {
        console.error("Moved item not found in cellActivities", detail.info.id,detail.items);
        return;
      }
      if (props.y_axis_type == "staff") {
        moveActivityInStaffGrid({
          body: {
            from_cell: {
              date: movedItem.original_date,
              staff: movedItem.original_staff,
            },
            to_cell: {
              date: isoDate(),
              staff: props.row_id,
            },
            activity_id: movedItem.activity_id,
          },
          
        }).then();
      } else if (props.y_axis_type == "location") {
        moveActivityInLocationGrid({
          body: {
            from_cell: {
              date: movedItem.original_date,
              location: movedItem.original_location,
            },
            to_cell: {
              date: isoDate(),
              location: props.row_id,
            },
            activity_id: movedItem.activity_id,
          },
        }).then(handleMoveResponse);
      }
    }
  };

  let cellRef;
  const handlednd = (...args) => {
    console.log(args); return dndzone(...args)
  }
  return (
    <Suspense>
      <td>
      <div
        title={JSON.stringify(cellActivities())}
        classList={{
          [styles.activityCell]: !!props.row_id,
          [styles.unallocatedActivities]: !props.row_id,
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
            staff_or_location: props.row_id,
            items: props.activities[isoDate()],
          });
          e.preventDefault();
        }}
        ref={cellRef}
      >
        <For each={items()} fallback={<div>&nbsp;</div>}>
          {(act) => (
            <Activity
              activity_def={act}
              staff_or_location={props.row_id}
              show_staff={true}
            />
          )}
        </For>
      </div></td>
    </Suspense>
  );
}

/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Activity component.
 */
export function Activity(props: { activity_def: ActivityDisplay; staff_or_location?: string; }): JSX.Element {
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
          {props.activity_def.location?.name}
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
