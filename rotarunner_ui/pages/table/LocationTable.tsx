import {
  For,
  Show,
  createMemo,
  JSX,
  Component,
  lazy,
  createSignal,
} from "solid-js";
import { differenceInCalendarDays } from "date-fns";

import styles from "./table.module.css";

import { graphql, GraphQLTaggedNode } from "relay-runtime";
import { createFragment, createMutation } from "solid-relay";

import { LocationTableQuery$data } from "./__generated__/LocationTableQuery.graphql";

import BaseTable from "./BaseTable";

import { LocationTableActivityFragment$key } from "./__generated__/LocationTableActivityFragment.graphql";
import DragDrop from "../../dragdrop";
import { set } from "lodash";
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

const dragdrop = new DragDrop();
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
      edges {
        node {
          ...LocationTableActivityFragment
          activityStart
          id
          location {
            id
          }
        }
      }
    }
  }
`;

function LocationTable() {
  return (
    <>
      <BaseTable
        query={activitiesByLocationQuery as unknown as GraphQLTaggedNode}
        cellComponent={ActivityCell}
      />
    </>
  );
}

let draggedItemType: string | null = null;
let draggedItemId: string | null = null;

function activityDraggedOverCell(event: DragEvent) {
  if (draggedItemType !== "activity") {
    return;
  }
  event.preventDefault();
}

interface ActivityCellProps {
  date: Date;
  y_axis_type: "staff" | "location";
  row_id?: string;
  i?: number;
  data: LocationTableQuery$data["content"]["edges"] | null | undefined;
}
export const ActivityCell: Component<ActivityCellProps> = (props) => {
  const isoDate = () => props.date.toISOString().slice(0, 10);

  const items = createMemo(
    () =>
      props.data?.filter(({ node: activity }) => {
        const activityDate = activity.activityStart.slice(0, 10);
        const locId = activity.location?.id ?? "unallocated";
        return (
          activityDate == isoDate() && (locId ?? "unallocated") == props.row_id
        );
      }) ?? []
  );

  const [editActivity] = createMutation(graphql`
    mutation LocationTableMoveMutation($activity: ActivityInput!) {
      editActivity(activity: $activity) {
        id
        ...LocationTableActivityFragment
      }
    }
  `);
  const handleDrop = (info) => {
    const activity = info.draggedElementInfo;

    const rowId = props.row_id == "unallocated" ? null : props.row_id;

    const activityInput = {
      id: activity.id,
      activityDate: isoDate(),
      locationId: rowId,
    };

    console.log("Moving activity with variables:", activityInput);
    editActivity({
      variables: { activity: activityInput },
      onError(error) {
        console.error("Error moving activity:", error);
      },
      onCompleted(data) {
        console.log("Activity moved successfully:", data);
      },
    });
  };
  const registerDroptarget = (el: HTMLElement) => {
    dragdrop.registerDroptarget(el, { onDrop: handleDrop });
  };
  return (
    <td data-cell-id={`${isoDate()}--${props.row_id}`} ref={registerDroptarget}>
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
                activity_def={act.node}
                staff_or_location={props.row_id}
              />
            </>
          )}
        </For>
      </div>
    </td>
  );
};

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
    assignments {
      staff {
        id
        name
      }
      timeslot {
        start
        finish
      }
    }
  }
`;

interface ActivityProps {
  activity_def: LocationTableQuery$data["content"]["edges"][0]["node"];
  staff_or_location?: string | null;
}
/**
 * Activity component to render an activity.
 * @param {Object} props - The properties passed to the component.
 * @param {Object} props.activity_def - The activity definition.
 * @param {string|undefined} [props.staff_or_location=null] - The staff or location data.
 * @returns {JSX.Element} - The rendered Activity component.
 */

export function Activity(props: ActivityProps): JSX.Element {
  const data = createFragment<LocationTableActivityFragment$key>(
    activityFragment,
    () => props.activity_def
  );
  const registerDraggable = (el, info) => {
    dragdrop.registerDraggable(el, info);
  };
  const [isDragging, setIsDragging] = createSignal(false);
  return (
    <div
      use:registerDraggable={{
        setIsCurrentDrag: setIsDragging,
        data: data(),
      }}
      classList={{ [styles.activity]: true, [styles.dragging]: isDragging() }}
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
