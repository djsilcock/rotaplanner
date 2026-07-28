import datetime

import dominate.tags as tags
from logging import getLogger

from .types import Activity, Location, Staff

logger = getLogger(__name__)


def table(
    dates: list[datetime.date],
    rows: list[Location] | list[Staff] | None = None,
    cells: dict[tuple[str, str], list[Activity]] | None = None,
):
    logger.info(f"Rendering table with dates: {dates}, rows: {rows}, cells: {cells}")
    with tags.div(cls="pywry-scroll-container") as scroll_container:
        with tags.table(id="table", tabindex="0"):
            tags.thead(
                tags.tr(
                    tags.td(),
                    *[tags.td(date.isoformat(), cls="column-header") for date in dates],
                )
            )
            with tags.tbody():
                for row_idx, row in enumerate(rows):
                    tr = tags.tr()
                    with tr:
                        tags.td(row.name, _class="row-header")
                        for col_idx, date in enumerate(dates):
                            with tags.td(
                                _class="activity-cell table-cell",
                                id=f"cell--{date.isoformat()}--{row.id}",
                                data_col=col_idx,
                                data_row=row_idx,
                                data_row_id=str(row.id),
                                data_col_id=date.isoformat(),
                            ):

                                table_cell(
                                    cells.get((date.isoformat(), row.id), []),
                                )

        return scroll_container


def table_cell(cell):
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
            if activity.render_type == "location":

                location_activity(activity, track)
            elif activity.render_type == "staff":
                person_activity(activity, track)
            else:
                logger.warning(f"!Unknown render type {activity.render_type}")
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
    activity_div = tags.div(
        cls=f"activity-wrapper {activity.status}", data_activity_id=activity.id
    )
    with activity_div:
        timeline_bar(activity, track)
        with tags.div(
            cls="activity deletable selectable",
            id=f"act--{activity.id}",
            data_draggable=".table-cell",
            data_activity_id=activity.id,
            data_dragtype="activity",
        ):
            tags.div(activity.name, cls="activity-name", title=str(activity))
            tags.div(
                f"{activity.activity_start.isoformat()[11:16]} - {activity.activity_finish.isoformat()[11:16]}",
                cls="activity-time",
            )
            tags.hr()
            roles_dict = {None: "Default"}
            roles_dict.update({role.id: role for role in activity.roles})
            assignments_by_role = {None: []}
            for assignment in activity.assignments:
                if assignment.role:
                    assignments_by_role.setdefault(assignment.role.id, []).append(
                        assignment
                    )
                else:
                    assignments_by_role.setdefault(None, []).append(assignment)

            for role_id, role_name in roles_dict.items():
                with tags.div(cls="role"):
                    tags.div(role_name, cls="role-name")
                    for assignment in assignments_by_role.get(role_id, []):
                        tags.div(
                            assignment.staff.name,
                            cls="assigned-staff",
                            data_draggable=".activity",
                            data_dragtype="assignment",
                            data_assignment_id=assignment.id,
                            id=f"assn--{assignment.id}--{assignment.staff.id}",
                        )
    return activity_div


def person_activity(activity: Activity, track):
    activity_div = tags.div(
        cls=f"activity-wrapper {activity.status}", data_activity_id=activity.id
    )
    staff_id = activity.cell[
        1
    ]  # Assuming the second element of the cell tuple is the staff ID
    activity_date = activity.cell[
        0
    ]  # Assuming the first element of the cell tuple is the date
    relevant_assignment = next(
        ((assn for assn in activity.assignments if assn.staff.id == staff_id)), None
    )
    with activity_div:
        timeline_bar(activity, track)
        with tags.div(
            cls="activity deletable selectable" if staff_id else "activity selectable",
            id=f"act--{activity.id}--{staff_id}",
            data_activity_id=activity.id,
            data_staff_id=staff_id or "None",
            data_draggable=f'.table-cell[data-col-id="{activity_date}"]',
            data_dragtype="activity",
        ):
            tags.div(activity.name, cls="activity-name", title=str(activity))
            tags.div(
                f"{activity.activity_start.isoformat()[11:16]} - {activity.activity_finish.isoformat()[11:16]}",
                cls="activity-time",
            )
            if staff_id:
                tags.hr()
                with tags.select(
                    id=f"role-select--{activity.id}--{staff_id}",
                    cls="role-select",
                    data_not_draggable="true",
                ):
                    tags.option(
                        "Default",
                        value="None",
                        selected=(relevant_assignment.role is None),
                    )
                    for role in activity.roles:
                        tags.option(
                            role.name,
                            value=role.id,
                            selected=(
                                relevant_assignment.role is not None
                                and relevant_assignment.role.id == role.id
                            ),
                        )
                for assignment in activity.assignments:
                    if (
                        assignment.staff.id != staff_id
                    ):  # only show other staff assigned to the same activity
                        tags.div(
                            assignment.staff.name,
                            cls="assigned-staff",
                            data_draggable=".table-cell",
                            id=f"assn--{assignment.id}--{assignment.staff.id}",
                        )
    return activity_div
