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
const staffQuery = graphql`
  query tableStaffQuery {
    staff {
      id
      name
    }
  }
`;

const locationQuery = graphql`
  query tableLocationsQuery {
    locations {
      id
      name
    }
  }
`;

const tableConfigQuery = graphql`
  query tableConfigQuery {
    staff: staff {
      id
      name
    }
    locations: locations {
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
      ...tableRowSortingFragment
    }
  }
`;

const rowSortingFragment = graphql`
  fragment tableRowSortingFragment on Activity {
    id
    activityStart
    location {
      id
    }
    assignments {
      staff {
        id
      }
    }
    ...tableActivityFragment
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
/**
 *
 * @param {object} props
 * @param {string} props.y_axis_type - Type of y-axis data (staff or location).
 * @returns {JSX.Element}
 * Table component to render the main table.
 */
function Table(props: TableProps): JSX.Element {
  const tableConfig = createLazyLoadQuery<TableConfigQuery>(
    tableConfigQuery,
    {}
  );

  const activitiesQueryResult = createLazyLoadQuery<tableActivitiesQuery>(
    getActivitiesQuery,
    { start: "2021-01-01", end: "2100-01-01" }
  );
  const activitiesResult = createFragment(
    rowSortingFragment,
    activitiesQueryResult
  );
  const dates = createMemo(() => {
    if (!tableConfig()?.daterange)
      return eachDayOfInterval({
        start: new Date("2021-01-01"),
        end: new Date("2021-12-31"),
      });
    const start = parseISO(tableConfig()!.daterange.start);
    const end = parseISO(tableConfig()!.daterange.end);
    return eachDayOfInterval({ start, end });
  });

  const groupByLocation = () => {
    return groupBy(
      activitiesResult()?.activities ?? [],
      (activity) => activity.location?.id ?? "unallocated"
    );
  };
  const groupByStaff = () => {
    const byStaff: Record<
      string,
      ({ id: string; activityStart: string } & tableActivityFragment$key)[]
    > = {
      unallocated: [],
    };
    for (let activity of activitiesResult()!.activities) {
      if (activity.assignments.length == 0) {
        byStaff["unallocated"].push(activity);
      } else {
        activity.assignments.forEach((assignment) => {
          const staffId = assignment.staff.id;
          if (!byStaff[staffId]) {
            byStaff[staffId] = [];
          }

          byStaff[staffId].push(activity);
        });
      }
    }
    return byStaff;
  };
  const getRows = createMemo(() => {
    if (!activitiesResult()) return {};
    if (props.y_axis_type === "location") {
      return groupByLocation();
    } else if (props.y_axis_type === "staff") {
      return groupByStaff();
    }
  });

  createEffect(() => {
    console.log("Rows updated:", getRows());
  });
  let parentRef;
  const [editActivity, setEditActivity] = createSignal<string | null>(null);
  const y_axis = createMemo(() => {
    if (props.y_axis_type === "staff") {
      return tableConfig()?.staff ?? [];
    } else if (props.y_axis_type === "location") {
      return tableConfig()?.locations ?? [];
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
            <For each={dates()} fallback={<td></td>}>
              {(date) => <td>{date.toISOString().slice(0, 10)}</td>}
            </For>
          </tr>
        </thead>
        <tbody>
          <For each={y_axis()}>
            {(staff_or_location, index) => (
              <TableRow
                activities={getRows()?.[staff_or_location.id] ?? []}
                row_id={staff_or_location.id}
                row_name={staff_or_location.name}
                y_axis_type={props.y_axis_type}
                i={index()}
                dates={dates()}
                updateActivities={() => {}}
              />
            )}
          </For>
          <TableRow
            activities={getRows()?.unallocated ?? []}
            row_id={"unallocated"}
            row_name={"Unallocated"}
            y_axis_type={props.y_axis_type}
            i={y_axis().length}
            dates={dates()}
          />
        </tbody>
      </table>
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
    mutation tableMoveActivityMutation(
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
  fragment tableActivityFragment on Activity {
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
