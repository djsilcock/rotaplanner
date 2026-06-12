import datetime

import dominate.tags as tags
from logging import getLogger

from .types import Activity, Location, Staff

logger = getLogger(__name__)


def table(
    dates: list[datetime.date],
    rows: list[Location] | list[Staff] | None = None,
):
    with tags.div(cls="pywry-scroll-container") as scroll_container:
        with tags.table(id="table"):
            tags.thead(
                tags.tr(
                    tags.td(),
                    *[tags.td(date.isoformat(), cls="column-header") for date in dates],
                )
            )
            with tags.tbody():
                for row in rows:
                    tr = tags.tr()
                    with tr:
                        tags.td(row.name, _class="row-header")
                        for date in dates:
                            tags.td(
                                _class="activity-cell table-cell",
                                id=f"cell--{date.isoformat()}--{row.id}",
                            )
                                

        return scroll_container


def table_cell(row_id, date, cell, table_type):
    cell_activities = []
    tracks = []
    for activity in cell:
        for i, track_end in enumerate(tracks):
            if activity.activity_start >= track_end:
                tracks[i] = activity.activity_finish
                cell_activities.append((activity, i))
                break
        else:
            tracks.append(activity.activity_finish)
            cell_activities.append((activity, len(tracks) - 1))
    with tags.div(
        style=f"position: relative; padding-top: {len(tracks) * 5 + 5}px;",
    ) as cell:
        for activity, track in cell_activities:
            if table_type == "location":
                location_activity(activity, track)
            elif table_type == "staff":
                person_activity(activity, row_id, track)
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
    activity_div = tags.div(cls=f"activity-wrapper {activity.status}")
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
                with tags.div(cls="role"):
                    tags.div(role.name, cls="role-name")
                    for assignment in role.assignments:
                        tags.div(
                            assignment.staff.name,
                            cls="assigned-staff",
                            data_draggable=".table-activity",
                            id=f"assn--{assignment.id}--{assignment.staff.id}",
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
            if staff_id:
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
