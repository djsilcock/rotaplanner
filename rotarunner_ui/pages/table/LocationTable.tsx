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
import { graphql } from "relay-runtime";
import {
  createFragment,
  createLazyLoadQuery,
  createMutation,
} from "solid-relay";
import type { tableConfigQuery as TableConfigQuery } from "./__generated__/tableConfigQuery.graphql";
import type { tableActivitiesQuery } from "./__generated__/tableActivitiesQuery.graphql";

import { groupBy } from "lodash";
import { tableActivityFragment$key } from "./__generated__/tableActivityFragment.graphql";
import { LocationTableQuery } from "./__generated__/LocationTableQuery.graphql";
import { E } from "../../dist/assets/index-C7tjXJkK";

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
    rows: allLocations {
      id
      name
    }
    activities(start: $start, end: $end) {`;
const activitiesByLocationQuery2 = graphql`
  query LocationTableQuery($start: String!, $end: String!) {
    daterange {
      start
      end
    }
    rows: allLocations {
      id
      name
      activities(start: $start, end: $end) {
        ...LocationTableActivityFragment
        activityStart
      }
    }
    unallocated: activities(
      startDate: $start
      endDate: $end
      locationId: null
    ) {
      ...LocationTableActivityFragment
      activityStart
    }
  }
`;

const activityFragment = graphql`
  fragment LocationTableActivityFragment on Activity {
    id
    activityStart
    activityFinish
    timeslots {
      start
      finish
      staffAssigned {
        staff {
          id
          name
        }
      }
    }
  }
`;

/**
 *
 * @param props
 * @param props.activities  - Activities data.
 * @param props.row_id - Row identifier.
 * @param props.row_name - Row name.
 * @param props.y_axis_type - Type of y-axis data (staff or location).
 * @param props.i - Index of the row.
 * @param props.dates - Dates for the row.
 * @param props.updateActivities - Function to update activities data.
 * @returns JSX.Element
 * TableRow component to render a single row in the table.
 */
interface TableRowProps {
  activities: ({
    activityStart: string;
    id: string;
  } & tableActivityFragment$key)[]; // Adjusted type
  row_id: string;
  row_name: string;
  y_axis_type: "staff" | "location";
  i?: number;
  dates: Date[];
}

function TableRow(props: TableRowProps): JSX.Element {
  const activities = createMemo<Record<string, TableRowProps["activities"]>>(
    () => {
      return groupBy(props.activities, (activity) =>
        activity.activityStart.slice(0, 10)
      ) as Record<string, TableRowProps["activities"]>;
    }
  );

  return (
    <tr>
      <td class={styles.rowHeader}>{props.row_name}</td>
      <For each={props.dates} fallback={<td></td>}>
        {(date) => (
          <td>
            <ActivityCell
              activities={activities()[date.toISOString().slice(0, 10)] ?? []}
              date={date}
              row_id={props.row_id}
              y_axis_type={props.y_axis_type}
            />
          </td>
        )}
      </For>
    </tr>
  );
}
interface TableProps {
  y_axis_type: "location" | "staff";
  children?: JSX.Element;
}

function EditActivityWrapper(props: { children?: JSX.Element }) {
  const [editActivity, setEditActivity] = createSignal<string | null>(null);
  return (
    <div on:editactivity={(e) => setEditActivity(e.detail.activityId)}>
      <Show when={editActivity()} fallback={<div>{props.children}</div>}>
        <EditActivityModal
          activity={editActivity()}
          onClose={() => setEditActivity(null)}
        />
      </Show>
      {props.children}
    </div>
  );
}

/**
 *
 * @param {object} props
 * @param props.rowComponent
 * @param props.query
 * @returns {JSX.Element}
 * Table component to render the main table.
 */
function Table(props: TableProps): JSX.Element {
  const activitiesQueryResult = createLazyLoadQuery<LocationTableQuery>(
    activitiesByLocationQuery,
    { start: "2021-01-01", end: "2100-01-01" }
  );

  const dates = createMemo(() => {
    if (!activitiesQueryResult()?.daterange)
      return eachDayOfInterval({
        start: new Date("2021-01-01"),
        end: new Date("2021-12-31"),
      });
    const start = parseISO(activitiesQueryResult()!.daterange.start);
    const end = parseISO(activitiesQueryResult()!.daterange.end);
    return eachDayOfInterval({ start, end });
  });

  let parentRef;

  return (
    <Show when={activitiesQueryResult()} fallback={<div>Loading...</div>}>
      <EditActivityWrapper>
        <table class={styles.rotaTable}>
          <thead>
            <tr>
              <td></td>
              <For each={dates()} fallback={<td></td>}>
                {(date) => <td>{date.toISOString().slice(0, 10)}</td>}
              </For>
            </tr>
          </thead>
          <tbody>
            <For each={activitiesQueryResult()?.rows} fallback={<tr></tr>}>
              {(location, index) => (
                <TableRow
                  activities={location.activities}
                  row_id={location.id}
                  row_name={location.name}
                  i={index()}
                  dates={dates()}
                  updateActivities={() => {}}
                />
              )}
            </For>
            <TableRow
              activities={activitiesQueryResult()?.unallocated ?? []}
              row_id={"unallocated"}
              row_name={"Unallocated"}
              i={activitiesQueryResult()?.rows.length}
              dates={dates()}
            />
          </tbody>
        </table>
      </EditActivityWrapper>
    </Show>
  );
}

interface DraggableActivity {
  id: string;
  activity: tableActivityFragment$key;
}

interface ActivityCellProps {
  date: Date;
  y_axis_type: "staff" | "location";
  row_id?: string;
  i?: number;
  activities: ({
    activityStart: string;
    id: string;
  } & tableActivityFragment$key)[];
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
  const [moveActivity] = createMutation(graphql`
    mutation LocationTableMoveActivityMutation(
      $activityId: String!
      $fromRow: String!
      $toRow: String!
      $rowType: RowType!
    ) {
      moveActivity(
        activityId: $activityId
        fromRow: $fromRow
        toRow: $toRow
        rowType: $rowType
      ) {
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

      const variables = {
        activityId: movedItem.id,
        fromRow: (movedItem as any).rowId,
        toRow: props.row_id ?? "unallocated",
        rowType: props.y_axis_type,
      };
      console.log("Moving activity with variables:", variables);
      moveActivity({ variables });
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
  fragment LocationTableActivityFragment2 on Activity {
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
export function Activity(props: {
  activity_def: tableActivityFragment$key;
  staff_or_location?: string;
}): JSX.Element {
  const data = createFragment(tableActivityFragment, () => props.activity_def);
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

export default Table;
