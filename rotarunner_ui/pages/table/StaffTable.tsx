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

import { assign, create, groupBy } from "lodash";
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
import { StaffTableActivityFragment$key } from "./__generated__/StaffTableActivityFragment.graphql";

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
          name
          timeslots {
            ...StaffTableTimeslotFragment
            start
            finish
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

function* splitActivitiesIntoTimeslots(
  activities: StaffTableQuery$data["content"]["edges"]
) {
  for (const activity of activities) {
    const timeslots = activity.node.timeslots.map((timeslot) => ({
      id: timeslot.id,
      start: parseISO(timeslot.start),
      end: parseISO(timeslot.finish),
      assignments: timeslot.assignments,
      activity: activity.node,
    }));
    yield* timeslots;
  }
}

function* groupTimeslotsByActivity({ timeslots, prefix = "" }) {
  let currentActivityId: string | null = null;
  let currentActivityTimeslots: any[] = [];
  let currentActivityTimeslotIDs: string[] = [prefix];

  for (const timeslot of timeslots) {
    if (timeslot.activity.id !== currentActivityId) {
      if (currentActivityId) {
        yield {
          id: currentActivityTimeslotIDs.join("|"), //string id just to identify for dndzone
          activityId: currentActivityId,
          timeslots: currentActivityTimeslots,
        };
      }
      currentActivityId = timeslot.activity.id;
      currentActivityTimeslots = [];
      currentActivityTimeslotIDs = [prefix];
    }
    currentActivityTimeslots.push(timeslot);
    currentActivityTimeslotIDs.push(timeslot.id);
  }
  if (currentActivityId) {
    yield {
      id: currentActivityTimeslotIDs.join("|"), //string id just to identify for dndzone
      activityId: currentActivityId,
      timeslots: currentActivityTimeslots,
    };
  }
}
type TimeSlots =
  StaffTableQuery$data["content"]["edges"][number]["node"]["timeslots"];
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
  });
  const makeTimeslotFilterByRowId = (rowId: string) => {
    if (rowId == "unallocated") {
      return (timeslots: TimeSlots) => timeslots;
    }
    return (timeslots: TimeSlots) => {
      return timeslots.filter((ts) =>
        ts.assignments.some((assignment) => assignment.staff.id == props.row_id)
      );
    };
  };
  const items = createMemo(
    () =>
      _items() ??
      props.data
        .filter((edge) => edge.node.activityStart.startsWith(isoDate()))
        .map(({ node }) => {
          const { timeslots, ...rest } = node;
          return {
            node: {
              timeslots: makeTimeslotFilterByRowId(props.row_id!)(timeslots),
              ...rest,
            },
          };
        })
        .filter(
          ({ node }) =>
            props.row_id == "unallocated" ||
            node.timeslots.some((ts) =>
              ts.assignments.some((ass) => ass.staff.id == props.row_id)
            )
        )
        .toSorted((a, b) => {
          if (a.node.activityStart == b.node.activityStart) {
            return a.node.name < b.node.name ? -1 : 1;
          }
          return a.node.activityStart < b.node.activityStart ? -1 : 1;
        })

        .map(mapAssignmentToDraggable)
  );

  const handleMove = ({ detail }) => {
    setItems(
      detail.items
        .filter((act) => act.activity)
        .toSorted((a, b) => {
          if (a.activity.id === b.activity.id) {
            return a.timeslot.start < b.timeslot.start ? -1 : 1;
          }
          if (a.activity.activityStart == b.activity.activityStart) {
            return a.activity.name < b.activity.name ? -1 : 1;
          }
          return a.activity.activityStart < b.activity.activityStart ? -1 : 1;
        })
    );
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
      >
        <For each={items()} fallback={<div>&nbsp;</div>}>
          {(act) => (
            <>
              <Activity
                activity_def={act.activity}
                timeslot={act.timeslot}
                seenBefore={act.seenBefore}
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
    activityStart
    location {
      id
      name
    }

    timeslots {
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
let draggedAssignments: string[] = [];
/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {Object} props.timeslot - The timeslot information.
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Timeslot component.
 */
export function Activity(props): JSX.Element {
  const data = createFragment<StaffTableActivityFragment$key>(
    activityFragment,
    () => props.activity_def
  );
  const assignmentsHere = createMemo(() => {
    if (props.staff_or_location == "unallocated") {
      return data()!.timeslots.flatMap((ts) => ts.id);
    }
    return data()!.timeslots.flatMap((ts) =>
      ts.assignments
        .filter((assignment) => assignment.staff.id == props.staff_or_location)
        .map((assignment) => assignment.id)
    );
  });
  return (
    <div
      draggable="true"
      class={styles.activity}
      data-activity-id={data()!.id}
      id={`activity-${data()!.id}`}
      ondragstart={(e) => {
        draggedAssignments = data()!.timeslots.flatMap((ts) =>
          ts.assignments.map((assignment) => assignment.id)
        );
        console.log(
          "Drag started for activity:",
          data()!.id,
          "with assignments:",
          assignmentsHere(),
          "on row_id:",
          props.staff_or_location
        );
      }}
    >
      <div class={styles.activityName}>{data()!.name}</div>

      <hr />
      <div>
        <For each={data()!.timeslots}>
          {(timeslot) => (
            <div draggable="true">
              <div class={styles.activityTime}>
                {timeslot.start.slice(11, 16)} - {timeslot.finish.slice(11, 16)}
                {timeslot.id}
              </div>
              <For each={timeslot.assignments}>
                {(assignment) => (
                  <div>
                    <Show
                      when={assignment.staff.id !== props.staff_or_location}
                    >
                      <div class={styles.assignedStaff}>
                        {assignment.staff.name}
                      </div>
                    </Show>
                  </div>
                )}
              </For>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}

export default StaffTable;
