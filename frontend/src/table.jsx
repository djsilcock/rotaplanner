import { For, Show } from "solid-js";
import { differenceInCalendarDays, addDays } from "date-fns";

const epoch = new Date(2000, 0, 1);

Date.prototype.toOrdinal = function () {
  return differenceInCalendarDays(this, epoch);
};

function Table(props) {
  return (
    <div
      id="rota-table"
      style={{
        "grid-template-rows": `repeat(${props.y_axis.length + 2},auto)`,
      }}
    >
      <div id="rota-names" class="spans-all-rows">
        <div></div>
        <For each={y_axis}>
          {(staff_or_location, index) => (
            <div class="row-header">{staff_or_location.name}</div>
          )}
        </For>
        <div class="row-header"></div>
      </div>

      <div id="rota-scrollable" class="spans-all-rows">
        <div id="grid-begin">&nbsp;</div>
        <For each={dates}>
          {(date) => (
            <>
              <div class="column-header">
                {date.toLocaleDateString("en-GB", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })}
              </div>
              <For each={y_axis}>
                {(staff_or_location, index) => (
                  <ActivityCell
                    staff_or_location={staff_or_location}
                    i={index}
                    date={date}
                    activities={activities}
                  />
                )}
              </For>
              <div
                class="unallocated-activities"
                id={`td-${date.toOrdinal()}-unalloc`}
              >
                <For each={activities[date]}>
                  {(act) => (
                    <Show when={show_in_unalloc(act)}>
                      <Activity activity_def={act} show_staff={false} />
                    </Show>
                  )}
                </For>
              </div>
            </>
          )}
        </For>
        <div id="grid-end">&nbsp;</div>
      </div>
    </div>
  );
}

function ActivityCell({ staff_or_location, i, date, activities }) {
  return (
    <div
      class="activitycell"
      data-date={date.toOrdinal()}
      data-yaxis={i}
      id={`td-${date.toOrdinal()}-${i}`}
      up-hungry
    >
      {activities[date].map((act) =>
        act.location === staff_or_location ? (
          <Activity
            act={act}
            staff_or_location={staff_or_location}
            show_location={false}
            show_staff={true}
          />
        ) : null
      )}
    </div>
  );
}

function Activity({
  activity_def,
  staff_or_location = null,
  show_location = true,
  show_staff = true,
}) {
  return (
    <div class="activity">
      <div class="activity-name">{activity_def.name}</div>
      <Show when={staff_or_location !== activity_def.location.id}>
        <div class="activity-location">{activity_def.location.name}</div>
      </Show>
      <Show when={show_staff}>
        <For each={activity_def.staff_assignments}>
          {(assignment) => (
            <Show when={assignment.staff !== staff_or_location}>
              <div class="assignment">
                {assignment.staff.name}
                <Show when={assignment.times}>{assignment.times}</Show>
              </div>
            </Show>
          )}
        </For>
      </Show>
    </div>
  );
}

export default Table;
