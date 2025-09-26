import {
  createEffect,
  createSignal,
  For,
  Show,
  Suspense,
  createMemo,
  createResource,
  JSX,
  Component,
  lazy,
} from "solid-js";
import { differenceInCalendarDays, addDays, parseISO } from "date-fns";
import { createQuery, useQueryClient } from "@tanstack/solid-query";
import styles from "./table.module.css";
import { createStore } from "solid-js/store";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import { graphql } from "relay-runtime";
import { createLazyLoadQuery } from "solid-relay";
import type { tableConfigQuery as TableConfigQuery } from "./__generated__/tableConfigQuery.graphql";
import {
  getActivitiesByDate,
  tableConfig as getTableConfig,
  moveActivityInLocationGrid,
  moveActivityInStaffGrid,
} from "../../generatedTypes/sdk.gen";
import {
  LabelledUuid,
  ActivityDisplay,
  ActivityResponse,
} from "../../generatedTypes/types.gen";

const EditActivityModal = lazy(() => import("../edit_activity"));
const epoch = new Date(2021, 0, 1);

function retry(
  fn: (...arg: any) => Promise<any>,
  { retries = 3, delay = 500 }
): () => Promise<any> {
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
  };
}

/**
 * Converts a date to its ordinal representation based on a fixed epoch.
 * @param {Date} date - The date to convert.
 * @returns {number} - The ordinal representation of the date.
 */
export function toOrdinal(date: Date): number {
  return differenceInCalendarDays(date, epoch);
}
const staffQuery = graphql`
  query tableStaffQuery {
    allStaff {
      id
      name
    }
  }
`;

const locationQuery = graphql`
  query tableLocationsQuery {
    allLocations {
      id
      name
    }
  }
`;

const DEFAULT_SEGMENT_WIDTH = 1;

function throwIfError<T>({ data, error }: { data: T; error: any }): T {
  if (error) {
    throw error;
  }
  return data;
}

interface TableProps {
  y_axis_type: "location" | "staff";
  children?: JSX.Element;
}
/**
 *
 * @param {object} props
 * @param {string} props.y_axis_type - Type of y-axis data (staff or location).
 * @returns {JSX.Element}
 * Table component to render the main table.
 */

const tableConfigQuery = graphql`
  query tableConfigQuery {
    allStaff {
      id
      name
    }
    allLocations {
      id
      name
    }
    daterange {
      start
      end
    }
  }
`;

const getActivitiesQuery = graphql`
  query tableActivitiesQuery($end: String!, $start: String!) {
    activities(endDate: $end, startDate: $start) {
      id
      name
      timeslots {
        start
        finish
      }
    }
  }
`;

function Table(props: TableProps): JSX.Element {
  const tableConfigResponse = createLazyLoadQuery<TableConfigQuery>(
    tableConfigQuery,
    {}
  );
  const tableConfig = (() => {
    const datesMemo = createMemo(() => {
      if (!tableConfigResponse()?.daterange) return [];
      // Generate dates from start to finish date in the date range
      const start = parseISO(tableConfigResponse()!.daterange.start);
      const finish = parseISO(tableConfigResponse()!.daterange.end);
      return Array.from(
        { length: differenceInCalendarDays(finish, start) + 1 },
        (_, i) => addDays(start, i)
      );
    });
    return {
      get staff() {
        return tableConfigResponse()?.allStaff ?? [];
      },
      get locations() {
        return tableConfigResponse()?.allLocations ?? [];
      },

      get dates() {
        return datesMemo();
      },
    };
  })();

  const [activitiesData, updateActivitiesData] = createStore({});
  const activitiesResult = createLazyLoadQuery(
    getActivitiesQuery,
    { end: tableConfig.dates.at(-1), start: tableConfig.dates.at(0) }
  const c = retry(
    (_) =>
      getActivitiesByDate({
        responseStyle: "data",
        query: {},
      }),
    { retries: 3 }
  )();
  c.then((data) => {
    console.log("Fetched activities data:", data);

    updateActivitiesData(data.data);
  });

  let parentRef;
  const [editActivity, setEditActivity] = createSignal<string | null>(null);
  const y_axis = createMemo(() => {
    if (props.y_axis_type === "staff") {
      return tableConfig.staff;
    } else if (props.y_axis_type === "location") {
      return tableConfig.locations;
    }
    return [];
  });

  return (
    <Show when={true} fallback={<div>Loading...</div>}>
      <Show when={editActivity()}>
        <EditActivityModal
          activity={editActivity()}
          onClose={() => setEditActivity(null)}
        />
      </Show>
      <table
        class={styles.rotaTable}
        on:dblclick={(e) => {
          console.log("Double click event:", e);
          const activityId =
            (e.target.closest("[data-activity-id]") as HTMLElement)?.dataset
              .activityId ??
            (e.target.closest("[data-cell-id]") as HTMLElement)?.dataset
              .cellId ??
            null;
          if (!activityId) return;
          setEditActivity(activityId);
        }}
      >
        <thead>
          <tr>
            <td></td>
            <For each={tableConfig.dates} fallback={<td></td>}>
              {(date) => <td>{date.toISOString().slice(0, 10)}</td>}
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
                      y_axis_type={props.y_axis_type}
                      i={index()}
                      date={date}
                      updateActivities={(newActivities: ActivityResponse) => {
                        updateActivitiesData(newActivities.data);
                      }}
                    />
                  )}
                </For>
              </tr>
            )}
          </For>
          <tr>
            <td class={styles.rowHeader}>Unallocated</td>
            <For each={tableConfig.dates} fallback={<td></td>}>
              {(date) => (
                <ActivityCell
                  activities={activitiesData}
                  row_id={null}
                  y_axis_type={props.y_axis_type}
                  date={date}
                  updateActivities={(newActivities: ActivityResponse) => {
                    updateActivitiesData(newActivities.data);
                  }}
                />
              )}
            </For>
          </tr>
        </tbody>
      </table>
    </Show>
  );
}

function filterActivitiesStaffView(
  date: string,
  activities: ActivityDisplay[],
  staff: string | undefined
) {
  //filter and map activities in staff view

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
function filterActivitiesLocationView(
  date: string,
  activities: ActivityDisplay[],
  location: string | undefined
): DraggableActivity[] {
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
      id: `${item.activity_id}-${location}`,
    }));
}
interface ActivityCellProps {
  date: Date;
  y_axis_type: "staff" | "location";
  row_id?: string;
  i?: number;
  activities: ActivityResponse["data"];
  updateActivities: (newActivities: ActivityResponse) => void;
}
type APIResponse<R> =
  | { error: any; data: undefined }
  | { error: undefined; data: R };
export const ActivityCell: Component<ActivityCellProps> = (props) => {
  const isoDate = () => props.date.toISOString().slice(0, 10);

  const [items, setItems] = createSignal<DraggableActivity[]>([]);
  const cellActivities = createMemo(
    () =>
      (props.y_axis_type == "staff"
        ? filterActivitiesStaffView
        : filterActivitiesLocationView)(
        isoDate(),
        props.activities[isoDate()],
        props.row_id
      ) ?? []
  );
  createEffect(() => {
    // Update items when cellActivities changes
    setItems(cellActivities());
  });
  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };

  const handleMoveResponse = (data: ActivityResponse) => {
    if (data) {
      // Update the activities in the query cache

      if (data.toasts.length > 0) {
        data.toasts.forEach((toast) => {
          console.warn("Toast:", toast);
        });
      }
      props.updateActivities(data);
    }
  };
  const handleFinalMove = async ({ detail }) => {
    setItems(detail.items);
    if (detail.info.trigger == TRIGGERS.DROPPED_INTO_ZONE) {
      const movedItem = detail.items.find(
        (i: DraggableActivity) => i.id == detail.info.id
      );
      if (!movedItem) {
        console.error(
          "Moved item not found in cellActivities",
          detail.info.id,
          detail.items
        );
        setItems(cellActivities()); //undo changes
        return;
      }
      let data, error;
      if (props.y_axis_type == "staff") {
        ({ data, error } = await moveActivityInStaffGrid({
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
        }));
      } else if (props.y_axis_type == "location") {
        ({ data, error } = await moveActivityInLocationGrid({
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
        }));
      } else {
        console.error("Unknown y_axis_type", props.y_axis_type);
        setItems(cellActivities()); //undo changes
        return;
      }
      if (error) {
        console.error("Error moving activity:", error);
        setItems(cellActivities()); //undo changes
        return;
      }
      handleMoveResponse(data!);
    }
  };

  let cellRef;
  const handlednd = (...args) => {
    console.log(args);
    return dndzone(...args);
  };
  return (
    <td data-cell-id={`${isoDate()}--${props.row_id}`}>
      <Suspense>
        <div
          title={JSON.stringify(cellActivities())}
          classList={{
            [styles.activityCell]: !!props.row_id,
            [styles.unallocatedActivities]: !props.row_id,
            [styles.weekend]:
              props.date.getDay() === 0 || props.date.getDay() === 6,
          }}
          data-date={isoDate()}
          data-yaxis={props.i}
          data-row={props.row_id}
          id={`td-${toOrdinal(props.date)}-${props.i}`}
          use:dndzone={{
            items,
          }}
          on:consider={handleMove}
          on:finalize={handleFinalMove}
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
        </div>
      </Suspense>
    </td>
  );
};

/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Activity component.
 */
export function Activity(props: {
  activity_def: ActivityDisplay;
  staff_or_location?: string;
}): JSX.Element {
  return (
    <div
      class={styles.activity}
      data-activity-id={props.activity_def.activity_id}
      id={`activity-${props.activity_def.activity_id}`}
    >
      <div class={styles.activityName}>{props.activity_def.name}</div>

      <div>
        <For each={props.activity_def.timeslots}>
          {(timeslot) => (
            <div>
              <div class={styles.activityTime}>
                {timeslot.start.slice(11, 16)} - {timeslot.finish.slice(11, 16)}
              </div>
              <For each={timeslot.staff_assignments}>
                {(assignment) => (
                  <Show when={assignment.staff.id !== props.staff_or_location}>
                    <div class={styles.assignment}>{assignment.staff.name}</div>
                  </Show>
                )}
              </For>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}

export default Table;
