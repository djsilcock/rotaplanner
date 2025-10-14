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
} from "solid-js";
import {
  differenceInCalendarDays,
  parseISO,
  eachDayOfInterval,
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

import { groupBy } from "lodash";
import { tableActivityFragment$key } from "./__generated__/tableActivityFragment.graphql";
import {
  LocationTableQuery,
  LocationTableQuery$data,
} from "./__generated__/LocationTableQuery.graphql";
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
const activitiesByLocationQuery = graphql`
  query LocationTableQuery($start: String!, $end: String!) {
    daterange {
      start
      end
    }
    rows: locations {
      id
      name
    }
    content: activities(startDate: $start, endDate: $end) {
      ...LocationTableActivityFragment
      activityStart
      id
      location {
        id
      }
    }
  }
`;
const assignmentsByStaffQuery = graphql`
  query LocationTableStaffTableQuery($start: String!, $end: String!) {
    daterange {
      start
      end
    }
    rows: staff {
      id
      name
    }
    content: assignments(start: $start, end: $end) {
      ...LocationTableAssignmentFragment
      timeslot {
        start
      }
      staff {
        id
      }
    }
  }
`;

const activityFragment = graphql`
  fragment LocationTableActivityFragment on Activity {
    id
    activityStart
    activityFinish
    name
    location {
      id
      name
    }
    timeslots {
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

const assignmentFragment = graphql`
  fragment LocationTableAssignmentFragment on StaffAssignment {
    timeslot {
      start
      finish
      activity {
        id
        name
      }
      assignments {
        staff {
          id
          name
        }
      }
    }
  }
`;

function LocationTable() {
  const getCells = (
    data:
      | LocationTableQuery$data["content"]
      | LocationTableStaffTableQuery$data["content"]
  ) => {
    const datastore: Record<
      string,
      Record<
        string,
        | LocationTableQuery$data["content"]
        | LocationTableStaffTableQuery$data["content"]
      >
    > = {};
    for (let activity of data as LocationTableQuery$data["content"]) {
      const locId = activity.location?.id ?? "unallocated";
      if (!datastore[locId]) {
        datastore[locId] = {};
      }
      if (!datastore[locId][activity.activityStart.slice(0, 10)]) {
        datastore[locId][activity.activityStart.slice(0, 10)] = [];
      }
      datastore[locId][activity.activityStart.slice(0, 10)].push(activity);
    }
    return datastore;
  };

  return (
    <BaseTable
      query={activitiesByLocationQuery as unknown as GraphQLTaggedNode}
      getCells={getCells}
    />
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
  activities: LocationTableQuery$data["content"];
}
export const ActivityCell: Component<ActivityCellProps> = (props) => {
  const isoDate = () => props.date.toISOString().slice(0, 10);

  const [items, setItems] = createSignal<DraggableActivity[]>([]);
  const reset = () => {
    // Update items when cellActivities changes
    setItems(
      props.activities.map((activity) => ({
        id: activity.id,
        activity,
        rowId: props.row_id ?? "unallocated",
        originalDate: isoDate(),
      }))
    );
  };
  createEffect(() => {
    reset();
  });
  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };
  const [editActivity] = createMutation(graphql`
    mutation LocationTableMoveMutation($activity: ActivityInput!) {
      editActivity(activity: $activity) {
        id
        ...tableActivityFragment
      }
    }
  `);
  const handleFinalMove = async ({ detail }) => {
    setItems(detail.items);
    console.log("Final move detail:", detail);
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
        reset();
        return;
      }
      const variables = {};
      if (
        movedItem.originalDate === isoDate() &&
        movedItem.rowId === props.row_id
      ) {
        console.log("Item dropped back to original position, no action taken");
        reset();
        return;
      }
      if (movedItem.originalDate !== isoDate()) {
        console.log(
          `Item date changed from ${movedItem.originalDate} to ${isoDate()}`
        );
        Object.assign(variables, { activityStart: isoDate() });
      }
      if (movedItem.rowId !== props.row_id) {
        console.log(
          `Item row changed from ${movedItem.rowId} to ${
            props.row_id ?? "unallocated"
          }`
        );
        Object.assign(variables, { locationId: props.row_id });
      }
      console.log("Moving activity with variables:", variables);
      editActivity({ variables });
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
            flipDurationMs: 0,
            type:
              props.y_axis_type === "staff" ? isoDate() : "location-activities",
          }}
          on:consider={handleMove}
          on:finalize={handleFinalMove}
          ref={cellRef}
        >
          <For each={items()} fallback={<div>&nbsp;</div>}>
            {(act) => (
              <Activity
                activity_def={act.activity}
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
const tableActivityFragment = graphql`
  fragment LocationTableActivityFragment3 on Activity {
    id
    name
    activityStart
    activityFinish
    location {
      id
    }
    assignments {
      timeslot {
        start
        finish
      }
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
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Activity component.
 */
export function Activity(props): JSX.Element {
  const data = createFragment<LocationTableActivityFragment$key>(
    tableActivityFragment,
    () => props.activity_def
  );
  return (
    <div
      class={styles.activity}
      data-activity-id={data()!.id}
      id={`activity-${data()!.id}`}
    >
      <div class={styles.activityName}>{data()!.name}</div>
      <div class={styles.activityTime}>
        {data()!.activityStart.slice(11, 16)} -{" "}
        {data()!.activityFinish.slice(11, 16)}
      </div>
      <hr />
      <div>
        <For each={data()!.assignments}>
          {(assignment) => (
            <div>
              <Show when={assignment.staff.id !== props.staff_or_location}>
                <div class={styles.activityTime}>
                  {assignment.timeslot.start.slice(11, 16)} -{" "}
                  {assignment.timeslot.finish.slice(11, 16)}
                </div>
                <div class={styles.assignedStaff}>{assignment.staff.name}</div>
              </Show>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}

export default LocationTable;
