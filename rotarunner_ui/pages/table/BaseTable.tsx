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
  row_id: string;
  row_name: string;
  i?: number;
  dates: Date[];
  columns: Record<
    string,
    | LocationTableQuery$data["content"]
    | LocationTableStaffTableQuery$data["content"]
  >;
  cellComponent?: (props: ActivityCellProps) => JSX.Element;
}

function TableRow(props: TableRowProps): JSX.Element {
  return (
    <tr>
      <td class={styles.rowHeader}>{props.row_name}</td>
      <For each={props.dates} fallback={<td></td>}>
        {(date) => (
          <td>
            <Dynamic
              component={props.cellComponent}
              activities={props.columns[date.toISOString().slice(0, 10)] ?? []}
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

function EditActivityWrapper(props: { children?: JSX.Element }) {
  const [editActivity, setEditActivity] = createSignal<string | null>(null);
  return (
    <div on:editactivity={(e) => setEditActivity(e.detail.activityId)}>
      <Show when={editActivity()} fallback={<div></div>}>
        <EditActivityModal
          activity={editActivity()}
          onClose={() => setEditActivity(null)}
        />
      </Show>
      {props.children}
    </div>
  );
}

interface TableProps {
  children?: JSX.Element;
  cellComponent?: (props: ActivityCellProps) => JSX.Element;
  query?: GraphQLTaggedNode;
  getCells: (
    data:
      | LocationTableQuery$data["content"]
      | LocationTableStaffTableQuery$data["content"]
  ) => Record<
    string,
    Record<
      string,
      | LocationTableQuery$data["content"]
      | LocationTableStaffTableQuery$data["content"]
    >
  >;
}

function BaseTable(props: TableProps): JSX.Element {
  const tableQueryResult = createLazyLoadQuery<
    LocationTableQuery | LocationTableStaffTableQuery
  >(() => props.query!, { start: "2021-01-01", end: "2100-01-01" });

  const dates = createMemo(() => {
    if (!tableQueryResult()?.daterange)
      return eachDayOfInterval({
        start: new Date("2021-01-01"),
        end: new Date("2021-12-31"),
      });
    const start = parseISO(tableQueryResult()!.daterange.start);
    const end = parseISO(tableQueryResult()!.daterange.end);
    return eachDayOfInterval({ start, end });
  });

  let parentRef;

  const rows = createMemo(() => {
    return props.getCells(tableQueryResult()?.content ?? []) as ReturnType<
      typeof props.getCells
    >;
  });

  createEffect(() => {
    console.log("Rows updated:", rows());
  });
  return (
    <Show when={tableQueryResult()} fallback={<div>Loading...</div>}>
      top
      <EditActivityWrapper>
        bla
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
            <For each={tableQueryResult()?.rows} fallback={<tr></tr>}>
              {(row, index) => (
                <TableRow
                  cellComponent={props.cellComponent}
                  columns={rows()[row.id] ?? []}
                  row_id={row.id}
                  row_name={row.name}
                  i={index()}
                  dates={dates()}
                />
              )}
            </For>
            <TableRow
              cellComponent={props.cellComponent}
              columns={rows()?.unallocated ?? []}
              row_id={"unallocated"}
              row_name={"Unallocated"}
              i={tableQueryResult()?.rows.length}
              dates={dates()}
            />
          </tbody>
        </table>
      </EditActivityWrapper>
    </Show>
  );
}

export default BaseTable;
