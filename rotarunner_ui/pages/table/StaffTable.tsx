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
  untrack,
} from "solid-js";
import {
  differenceInCalendarDays,
  parseISO,
  eachDayOfInterval,
  startOfDay,
} from "date-fns";

import styles from "./table.module.css";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import { graphql, GraphQLTaggedNode } from "relay-runtime";
import {
  createFragment,
  createLazyLoadQuery,
  createMutation,
} from "solid-relay";
import type { tableConfigQuery as TableConfigQuery } from "./__generated__/tableConfigQuery.graphql";
import type { tableActivitiesQuery } from "./__generated__/tableActivitiesQuery.graphql";

import { create, groupBy } from "lodash";
import { tableActivityFragment$key } from "./__generated__/tableActivityFragment.graphql";
import {
  LocationTableQuery,
  LocationTableQuery$data,
} from "./__generated__/LocationTableQuery.graphql";
import {
  StaffTableQuery,
  StaffTableQuery$data,
} from "./__generated__/StaffTableQuery.graphql";
import {
  StaffTableAssignmentFragment$data,
  StaffTableAssignmentFragment$key,
} from "./__generated__/StaffTableAssignmentFragment.graphql";
import {
  LocationTableStaffTableQuery,
  LocationTableStaffTableQuery$data,
} from "./__generated__/LocationTableStaffTableQuery.graphql";
import { Dynamic } from "solid-js/web";
import BaseTable from "./BaseTable";
import { B } from "../../dist/assets/index-C7tjXJkK";
import {
  LocationTableActivityFragment$data,
  LocationTableActivityFragment$key,
} from "./__generated__/LocationTableActivityFragment.graphql";
import { StaffTableTimeslotFragment$key } from "./__generated__/StaffTableTimeslotFragment.graphql";

const EditActivityModal = lazy(() => import("../edit_activity"));
const epoch = new Date(2021, 0, 1);

/**
 * Converts a date to its ordinal representation based on a fixed epoch.
 * @param {Date} date - The date to convert.
 * @returns {number} - The ordinal representation of the date.
 */
export function toOrdinal(date: Date): number {
  return differenceInCalendarDays(date, epoch);
}

const assignmentsByStaffQuery = graphql`
  query StaffTableQuery($start: String!, $end: String!) {
    daterange {
      start
      end
    }
    rows: staff {
      id
      name
    }
    content: activities(startDate: $start, endDate: $end) {
      __id
      edges {
        node {
          ...StaffTableActivityFragment
          id
          activityStart
          timeslots {
            ...StaffTableTimeslotFragment
            start
            id
            assignments {
              id
              staff {
                id
              }
            }
          }
        }
      }
    }
  }
`;

function StaffTable() {
  return (
    <>
      <BaseTable
        query={assignmentsByStaffQuery as GraphQLTaggedNode}
        cellComponent={ActivityCell}
      />
    </>
  );
}

interface DraggableActivity {
  id: string;
  activity: LocationTableQuery$data["content"][0];
}

interface ActivityCellProps {
  date: Date;
  y_axis_type: "staff" | "location";
  row_id?: string;
  i?: number;
  data: StaffTableQuery$data["content"]["edges"];
}
export const ActivityCell: Component<ActivityCellProps> = (props) => {
  const isoDate = () => props.date.toISOString().slice(0, 10);

  const [_items, setItems] = createSignal<DraggableActivity[] | null>(null);

  const mapAssignmentToDraggable = ({
    node: assignment,
  }: StaffTableQuery$data["content"]["edges"][number]) => ({
    id: assignment.id,
    activity: assignment,
    rowId: props.row_id ?? null,
    resetSource: () => {
      setItems(null);
    },
  });
  const items = createMemo(
    () =>
      _items() ??
      Array.from(
        (function* () {
          for (const { node: activity } of props.data) {
            if (activity.activityStart.slice(0, 10) !== isoDate()) {
              continue;
            }
            for (const timeslot of activity.timeslots) {
              if (props.row_id === "unallocated") {
                //should actually be all timeslots as they could still be allocated to someone else
                yield {
                  id: timeslot.id,
                  activity,
                  timeslot,
                  rowId: null,
                  resetSource: () => {
                    setItems(null);
                  },
                };
                continue;
              }

              for (const assignment of timeslot.assignments) {
                if (assignment.staff.id === props.row_id) {
                  yield {
                    id: assignment.id,
                    activity,
                    rowId: props.row_id,
                    timeslot,
                    staff: assignment.staff,
                  };
                }
              }
            }
          }
        })()
      )
  );
  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };
  const [editActivity] = createMutation(graphql`
    mutation StaffTableMoveMutation($activity: ActivityInput!) {
      editActivity(activity: $activity) {
        id
        ...LocationTableActivityFragment
      }
    }
  `);
  const handleFinalMove = async ({ detail }) => {
    console.log("Final move detail:", detail);
    if (detail.info.trigger == TRIGGERS.DROPPED_OUTSIDE_OF_ANY) {
      setItems(null);
      return;
    }
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

        return;
      }
      const activityInput = { id: movedItem.id };
      if (
        movedItem.originalDate === isoDate() &&
        movedItem.rowId === props.row_id
      ) {
        console.log("Item dropped back to original position, no action taken");

        return;
      }

      Object.assign(activityInput, { activityDate: isoDate() });

      Object.assign(activityInput, {
        staffId: props.row_id === "unallocated" ? null : props.row_id,
      });

      console.log("Moving activity with variables:", activityInput);
      editActivity({
        variables: { activity: activityInput },
        onError(error) {
          console.error("Error moving activity:", error);
          movedItem.resetSource();
          setItems(null);
        },
        onCompleted(data) {
          console.log("Activity moved successfully:", data);
          movedItem.resetSource();
          setItems(null);
        },
      });
    }
  };

  return (
    <td data-cell-id={`${isoDate()}--${props.row_id}`}>
      <div
        classList={{
          [styles.activityCell]: !!props.row_id,
          [styles.unallocatedActivities]: !props.row_id,
          [styles.weekend]:
            props.date.getDay() === 0 || props.date.getDay() === 6,
        }}
        data-date={isoDate()}
        data-yaxis={props.i}
        data-row={props.row_id}
        id={`td-${isoDate()}-${props.row_id}`}
        use:dndzone={{
          items,
          flipDurationMs: 0,
          type:
            props.y_axis_type === "staff" ? isoDate() : "location-activities",
        }}
        on:consider={handleMove}
        on:finalize={handleFinalMove}
      >
        <For each={items()} fallback={<div>&nbsp;</div>}>
          {(act) => (
            <>
              <Timeslot
                activity_def={act.activity}
                timeslot={act.timeslot}
                staff_or_location={props.row_id}
                show_staff={true}
              />
            </>
          )}
        </For>
      </div>
    </td>
  );
};

const activityFragment = graphql`
  fragment StaffTableActivityFragment on Activity {
    id
    name
    location {
      id
      name
    }

    timeslots {
      ...StaffTableTimeslotFragment
      start
      finish
      assignments {
        staff {
          id
          name
        }
      }
    }
  }
`;
const timeslotFragment = graphql`
  fragment StaffTableTimeslotFragment on TimeSlot {
    id
    start
    finish
    assignments {
      id
      staff {
        id
        name
      }
    }
  }
`;

/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {Object} props.timeslot - The timeslot information.
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Timeslot component.
 */
export function Timeslot(props): JSX.Element {
  const activityData = createFragment<LocationTableActivityFragment$key>(
    activityFragment,
    () => props.activity_def
  );
  const timeslotData = createFragment<StaffTableTimeslotFragment$key>(
    timeslotFragment,
    () => props.timeslot
  );
  createEffect(() => {
    console.log("Rendering Timeslot for activity:", activityData());
    console.log("Timeslot data:", timeslotData());
  });
  return (
    <div
      class={styles.activity}
      data-activity-id={activityData()!.id}
      id={`activity-${activityData()!.id}`}
    >
      <div class={styles.activityName}>{activityData()?.name}</div>
      <div class={styles.activityTime}>
        {timeslotData()?.start.slice(11, 16)} -{" "}
        {timeslotData()?.finish.slice(11, 16)}
      </div>
      <hr />
      <div>
        <For each={timeslotData()?.assignments}>
          {(assignment) => (
            <div>
              <Show when={assignment.staff.id !== props.staff_or_location}>
                <div class={styles.assignedStaff}>{assignment.staff.name}</div>
              </Show>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}

export default StaffTable;
