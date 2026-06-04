import datetime

import dominate.tags as tags
from logging import getLogger

from rotaplanner.ui.common_types import Activity, Location, Role, Staff, StaffAssignment
from rotaplanner.database import database_connection

logger = getLogger(__name__)


def table_row(row_name, row_id, dates, cells, activities, table_type):
    tr = tags.tr()
    with tr:
        tags.td(row_name, _class="row-header")
        for date in dates:
            table_cell(row_id, date, cells, activities, table_type)
    return tr


def table_cell(row, date, cells, activities: dict[str, Activity], table_type):
    with tags.td(
        _class="activity-cell table-cell",
        id=f"cell--{date.isoformat()}--{row}",
        style=f"position: relative; padding-top: {len(cells.get(date, {}).get(row, [])) * 5 + 5}px;",
    ) as cell:
        cell_activities = []
        tracks = []
        for activity_id in cells.get((date.isoformat(), row), []):
            activity = activities.get(activity_id)
            if not activity:
                logger.warning(
                    f"Activity with id {activity_id} not found in activities data"
                )
                continue
            for i, track_end in enumerate(tracks):
                if activity.activity_start >= track_end:
                    tracks[i] = activity.activity_finish
                    cell_activities.append((activity, i))
                    break
            else:
                tracks.append(activity.activity_finish)
                cell_activities.append((activity, len(tracks) - 1))
        for activity, track in cell_activities:
            if table_type == "location":
                location_activity(activity, track)
            elif table_type == "staff":
                if row:
                    person_activity(activity, row, track)
                else:
                    activity_without_allocated_staff(activity, track)
            else:
                logger.warning(f"!{table_type}")
    return cell


def timeline_bar(activity, track):
    start = int(activity.activity_start.isoformat()[11:13])
    end = int(activity.activity_finish.isoformat()[11:13])
    duration = end - start
    return tags.div(
        " ",
        _class="timeline-bar",
        style=f"position: absolute; left: {(start/24)*100}%; width: {(duration/24)*100}%; top: {track*5}px;",
    )


def location_activity(activity: Activity, track):
    activity_div = tags.div(cls="activity-wrapper")
    with activity_div:
        timeline_bar(activity, track)
        with tags.div(
            cls="activity", id=f"act--{activity.id}", data_draggable=".table-cell"
        ):
            tags.div(activity.name, cls="activity-name", title=str(activity))
            tags.div(
                f"{activity.activity_start.isoformat()[11:16]} - {activity.activity_finish.isoformat()[11:16]}",
                cls="activity-time",
            )
            tags.hr()
            for role in activity.roles:
                tags.div(cls="role")
                tags.div(role.name, cls="role-name")
                for assignment in role.assignments:
                    tags.div(
                        assignment.staff.name,
                        cls="assigned-staff",
                        data_draggable=".table-activity",
                        id=f"assn--{assignment.id}--{assignment.staff.id}",
                    )
    return activity_div


def activity_without_allocated_staff(activity, track):
    activity_div = tags.div(cls="activity-wrapper")
    with activity_div:
        timeline_bar(activity, track)
        with tags.div(
            cls="activity", id=f"act--{activity.id}", data_draggable=".table-cell"
        ):
            tags.div(activity.name, cls="activity-name", title=str(activity))
            tags.div(
                f"{activity.activity_start.isoformat()[11:16]} - {activity.activity_finish.isoformat()[11:16]}",
                cls="activity-time",
            )

    return activity_div


def person_activity(activity: Activity, staff_id, track):
    activity_div = tags.div(cls="activity-wrapper")
    with activity_div:
        timeline_bar(activity, track)
        with tags.div(
            cls="activity", id=f"act--{activity.id}", data_draggable=".table-cell"
        ):
            tags.div(activity.name, cls="activity-name", title=str(activity))
            tags.div(
                f"{activity.activity_start.isoformat()[11:16]} - {activity.activity_finish.isoformat()[11:16]}",
                cls="activity-time",
            )
            tags.hr()
            with tags.select(
                id=f"role-select--{activity.id}--{staff_id}", cls="role-select"
            ):
                for role in activity.roles:
                    tags.option(
                        role.name,
                        value=role.id,
                        selected=any(
                            assn.staff == staff_id and assn.role == role.id
                            for assn in role.assignments
                        ),
                    )
            for assignment in activity.assignments:
                if (
                    assignment.staff != staff_id
                ):  # only show other staff assigned to the same activity
                    tags.div(
                        assignment.staff.name,
                        cls="assigned-staff",
                        data_draggable=".table-cell",
                        id=f"assn--{assignment.id}--{assignment.staff}",
                    )
    return activity_div


def table(dates, cells, activities, locations=None, staff=None):
    with tags.div(cls="pywry-scroll-container") as scroll_container:
        with tags.table(id="table"):
            tags.thead(
                tags.tr(
                    tags.td(),
                    *[tags.td(date.isoformat(), cls="column-header") for date in dates],
                )
            )
            with tags.tbody():
                for row in (locations if locations is not None else staff):
                    table_row(
                        row.name,
                        row.id,
                        dates,
                        cells,
                        activities,
                        "location" if locations is not None else "staff",
                    )

        return scroll_container
