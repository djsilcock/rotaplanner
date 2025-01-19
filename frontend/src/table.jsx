import {
  createEffect,
  createReaction,
  createSignal,
  For,
  onCleanup,
  Show,
  Suspense,
  createMemo,
  Switch,
} from "solid-js";
import { differenceInCalendarDays, addDays, parseISO } from "date-fns";
import { createQuery, useQueryClient } from "@tanstack/solid-query";
import styles from "./table.module.css";
import { Batcher } from "./utils/batcher";
import { useParams } from "@solidjs/router";
import { createStore, produce, unwrap } from "solid-js/store";
import { create, debounce } from "lodash";
import { dndzone, TRIGGERS } from "solid-dnd-directive";
import Menu from "@suid/material/Menu";
import MenuItem from "@suid/material/MenuItem";
import { Match } from "solid-js";

const epoch = new Date(2021, 0, 1);

/**
 * Converts a date to its ordinal representation based on a fixed epoch.
 * @param {Date} date - The date to convert.
 * @returns {number} - The ordinal representation of the date.
 */
export function toOrdinal(date) {
  return differenceInCalendarDays(date, epoch);
}

/**
 * TableSegment component to render a segment of the table.
 * @param {Object} props - The properties passed to the component.
 * @param {Date} props.startdate - The start date of the segment.
 * @param {number} props.segmentWidth - The width of the segment in days.
 * @param {Function} props.editRenderedElements - Function to edit rendered elements.
 * @param {Object} props.observer - Intersection observer to observe the segment.
 * @param {Map} props.elementsMap - Map to store references to elements.
 * @param {Array} props.y_axis - Array of y-axis data.
 * @param {string} props.y_axis_type - Type of y-axis data.
 * @returns {JSX.Element} - The rendered TableSegment component.
 */
function TableSegment(props) {
  const dates = () =>
    Array.from({ length: props.segmentWidth }, (x, i) =>
      addDays(props.startdate, i)
    );
  return (
    <div
      class={styles.rotaSegment}
      data-startdate={toOrdinal(props.startdate)}
      style={{ "grid-column": `span ${props.segmentWidth}` }}
      ref={props.ref}
    >
      <For each={dates()}>
        {(date) => (
          <>
            <div
              classList={{
                [styles.columnHeader]: true,
                [styles.weekend]: date.getDay() === 0 || date.getDay() === 6,
              }}
            >
              {date.toLocaleDateString("en-GB", {
                day: "2-digit",
                month: "short",
                year: "numeric",
              })}
            </div>
            <Show
              when={props.visible}
              fallback={<div style={{ "grid-row": "2/-1" }}>...</div>}
            >
              <For each={props.y_axis}>
                {(staff_or_location, index) => (
                  <ActivityCell
                    staff_or_location={staff_or_location.id}
                    y_axis_type={props.y_axis_type}
                    i={index()}
                    date={date}
                    active={props.visible}
                    isScrolling={props.isScrolling}
                  />
                )}
              </For>
              <ActivityCell
                date={date}
                i={props.y_axis?.length}
                active={props.visible}
                isScrolling={props.isScrolling}
                staff_or_location={undefined}
                y_axis_type={props.y_axis_type}
              />
            </Show>
          </>
        )}
      </For>
    </div>
  );
}
const [activeMenu, setActiveMenu] = createSignal(null);

const DEFAULT_SEGMENT_WIDTH = 30;
function Table() {
  const client = useQueryClient();
  const y_axis_type = createMemo(() => useParams().locationOrStaff);
  const tableConfigQuery = createQuery(() => ({
    queryKey: ["rota-grid", y_axis_type()],
    queryFn: (key) =>
      fetch(`${BACKEND_URL}/config/rota-grid/${y_axis_type()}`)
        .then((r) => r.json())
        .then((r) => {
          console.log(r);
          return r;
        }),
  }));

  const y_axis = () => tableConfigQuery.data?.y_axis;
  const dateRange = () => tableConfigQuery.data?.date_range;
  const [observer, setObserver] = createSignal(null);
  const [segments, editSegments] = createStore([]);
  const [isScrolling, setIsScrolling] = createSignal(false);
  const setupSegments = createReaction(() => {
    console.log(dateRange());
    editSegments(
      produce((segments) => {
        const initialDate = new Date(
          Math.min(parseISO(dateRange().start), new Date())
        );
        const finalDate = new Date(
          Math.max(parseISO(dateRange().finish), addDays(new Date(), 30))
        );
        for (
          let startdate = initialDate;
          startdate < finalDate;
          startdate = addDays(startdate, DEFAULT_SEGMENT_WIDTH)
        ) {
          segments.push({
            startdate,
            segmentWidth: DEFAULT_SEGMENT_WIDTH,
            ref: null,
            visible: undefined,
            isExtra: false,
          });
        }
      })
    );
  });
  setupSegments(() => !!dateRange());
  const [parentRef, setParentRef] = createSignal(null);

  const registerIO = createReaction(() => {
    if (!parentRef()) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const { target, isIntersecting } = entry;
          editSegments(
            produce((draft) => {
              (draft.find((el) => el.ref === target) ?? {}).visible =
                isIntersecting;
            })
          );
        });
      },
      { threshold: 0.0, root: parentRef(), rootMargin: "0px 200px" }
    );
    setObserver(observer);
    segments.forEach((s) => observer.observe(s.ref));
    onCleanup(() => observer.disconnect());
    const stopScrolling = debounce(() => setIsScrolling(false), 200);
    parentRef().addEventListener("scroll", () => {
      setIsScrolling(true);
      if (!("onscrollend" in parentRef())) {
        stopScrolling();
      }
    });
    parentRef().addEventListener("scrollend", () => {
      setIsScrolling(false);
    });
  });
  registerIO(() => parentRef());
  createEffect(() => {
    if (segments.length == 0) return;
    const firstSegment = segments.at(0);
    const lastSegment = segments.at(-1);
    if (firstSegment.visible == true) {
      console.warn("first segment is visible - should prepend another");
      parentRef().scrollBy(firstSegment.ref.scrollWidth, 0);
      editSegments(
        produce((draft) => {
          draft.unshift({
            startdate: addDays(firstSegment.startdate, -DEFAULT_SEGMENT_WIDTH),
            segmentWidth: DEFAULT_SEGMENT_WIDTH,
            ref: null,
            visible: undefined,
            isExtra: true,
          });
        })
      );
    }
    if (lastSegment.visible == true) {
      console.warn("last segment is visible - should append another");
      editSegments(
        produce((draft) => {
          draft.push({
            startdate: addDays(lastSegment.startdate, DEFAULT_SEGMENT_WIDTH),
            segmentWidth: DEFAULT_SEGMENT_WIDTH,
            ref: null,
            visible: undefined,
            isExtra: true,
          });
        })
      );
    }
    if (
      segments.length > 2 &&
      segments.at(0).isExtra &&
      segments.at(0).visible == false &&
      segments.at(1).visible == false
    ) {
      console.warn("removing redundant lead segment");
      parentRef().scrollBy(-firstSegment.ref.scrollWidth, 0);
      editSegments(
        produce((draft) => {
          draft.shift();
        })
      );
    }
    if (
      segments.length > 2 &&
      segments.at(-1).isExtra &&
      segments.at(-1).visible == false &&
      segments.at(-2).visible == false
    ) {
      console.warn("removing redundant tail segment");
      editSegments(
        produce((draft) => {
          draft.pop();
        })
      );
    }
  });
  createEffect(() => {
    console.log(activeMenu());
  });
  const reallocate = (itemid) => {
    fetch(`${BACKEND_URL}/activities/reallocate_activity`, {
      method: "POST",
      body: JSON.stringify({
        new_row: activeMenu().staff_or_location,
        activity_id: itemid,
      }),
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((r) => r.json())
      .then((r) => {
        console.log(r);
        if (r.error) {
          alert(r.error);
        }
        r.data.forEach((item) =>
          client.setQueryData(["activities", item.date], item.activities)
        );
      })
      .catch((e) => {
        console.error(e);
        alert("Server error");
      })
      .finally(() => setActiveMenu(null));
  };
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Menu
        open={!!activeMenu()}
        anchorEl={activeMenu()?.ref}
        onClose={() => setActiveMenu(null)}
      >
        <MenuItem>Create Activity</MenuItem>
        <For each={activeMenu()?.items}>
          {(item) => (
            <Switch>
              <Match when={useParams().locationOrStaff == "staff"}>
                <MenuItem
                  onClick={() => {
                    reallocate(item.id);
                  }}
                >
                  Allocate to {item.name}
                </MenuItem>
              </Match>

              <Match when={useParams().locationOrStaff == "location"}>
                <MenuItem
                  onClick={() => {
                    reallocate(item.id);
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
          "grid-template-rows": `repeat(${y_axis()?.length + 2},auto)`,
        }}
        ref={(el) => setParentRef(el)}
      >
        <div class={styles.rowHeader}></div>
        <For each={y_axis()}>
          {(staff_or_location, index) => (
            <div class={styles.rowHeader}>{staff_or_location.name}</div>
          )}
        </For>
        <div class={styles.rowHeader}></div>

        <For each={segments}>
          {(segment) => {
            const [segmentStore, editSegmentStore] = createStore(segment);

            return (
              <TableSegment
                startdate={segment.startdate}
                segmentWidth={segment.segmentWidth}
                ref={(el) => {
                  editSegmentStore("ref", el);
                  observer()?.observe(el);
                }}
                y_axis={y_axis()}
                y_axis_type={y_axis_type()}
                visible={segment.visible}
                isScrolling={isScrolling()}
              />
            );
          }}
        </For>
      </div>
    </Suspense>
  );
}

const activityFetcher = new Batcher({
  fetchFn: (keys) => {
    return fetch(`${BACKEND_URL}/activities/by_date`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ dates: keys.map((k) => k[1]) }),
    })
      .then((r) => r.json())
      .then((r) => {
        return r;
      });
  },
  handleMissingData: (key) => {
    return [];
  },
  handleAdditionalData: (key, data) => {
    console.log(`Additional data for ${key}: ${data}`);
  },
  processData: (data) => {
    const result = data.map((item) => [
      ["activities", item.date],
      item.activities,
    ]);
    console.log(result);
    return result;
  },
  timeout: 500,
});

export function ActivityCell(props) {
  const isoDate = () => props.date.toISOString().slice(0, 10);
  const selector = (data) => {
    const d = data
      ?.filter(
        (activity) =>
          // Show activities that are assigned to the staff or location
          activity.staff_assignments.some(
            (assignment) => assignment.staff.id === props.staff_or_location
          ) ||
          activity.location?.id === props.staff_or_location || // Show activities that are assigned to the location (including no location)
          (!props.staff_or_location && props.y_axis_type === "staff") // Show all activities in the unallocated row if in staff view
      )
      .map((item) => ({
        ...item,
        original_date: isoDate(),
        original_row: props.staff_or_location || null,
        id: `${item.id}-${props.staff_or_location}`,
        activity_id: item.id,
      }));
    console.log(d, props.staff_or_location, props.y_axis_type);
    return d;
  };
  const [items, setItems] = createSignal([]);
  const cellActivities = createQuery(() => ({
    queryKey: ["activities", isoDate()],
    queryFn: ({ queryKey }) => activityFetcher.fetch(queryKey),
    enabled: props.active && !props.isScrolling,
    staleTime: 1000 * 60 * 60,
  }));
  createEffect(() => {
    if (cellActivities.data) setItems(selector(cellActivities.data));
  });

  const handleMove = ({ detail }) => {
    setItems(detail.items);
  };
  const client = useQueryClient();
  const handleFinalMove = ({ detail }) => {
    console.log(detail);
    setItems(detail.items);
    if (detail.info.trigger == TRIGGERS.DROPPED_INTO_ZONE) {
      const movedItem = items().find((i) => i.id == detail.info.id);
      console.log(
        `attempted to move item from ${movedItem.original_date} ${
          movedItem.original_row
        } to ${isoDate()} ${props.staff_or_location}`
      );
      fetch(`${BACKEND_URL}/activities/reallocate_activity`, {
        method: "POST",
        body: JSON.stringify({
          original_date: movedItem.original_date,
          original_row: movedItem.original_row,
          new_date: isoDate(),
          new_row: props.staff_or_location,
          activity_id: movedItem.activity_id,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((r) => r.json())
        .then((r) => {
          console.log(r);
          if (r.error) {
            alert(r.error);
          }
          r.data.forEach((item) =>
            client.setQueryData(["activities", item.date], item.activities)
          );
        })
        .catch((e) => {
          console.error(e);
          alert("Server error");
        });
    }
  };

  createEffect(() => {
    if (cellActivities?.data?.length > 0) {
      console.log(cellActivities.data);
    }
  });
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
        up-hungry
        use:dndzone={{
          items,
        }}
        on:consider={handleMove}
        on:finalize={handleFinalMove}
        on:contextmenu={(e) => {
          console.log(e.target);
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
export function Activity(props) {
  return (
    <div class={styles.activity}>
      <div class={styles.activityName}>{props.activity_def.name}</div>
      <Show
        when={
          props.activity_def.location &&
          props.staff_or_location &&
          props.staff_or_location !== props.activity_def.location.id
        }
      >
        <div class="activity-location">{props.activity_def.location.name}</div>
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
