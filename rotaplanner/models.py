import datetime
import itertools
import uuid
from dataclasses import dataclass, field
from enum import Enum

from ortools.sat.python import cp_model


from pydantic import BaseModel, Field

from rotaplanner.date_rules import RuleGroup, RuleRoot, GroupType, Schedule

from functools import reduce
from typing import Annotated, Union, Literal

MIN_DATE = datetime.date(1900, 1, 1)
MAX_DATE = datetime.date(2100, 12, 31)


class RequirementType(Enum):
    AND = "AND"
    OR = "OR"


class Skill(BaseModel):
    id: uuid.UUID
    name: str


class Staff(BaseModel):
    id: uuid.UUID
    name: str
    skills: list[Skill]
    assignments: list["StaffAssignment"]


class Location(BaseModel):
    id: uuid.UUID
    name: str


class Requirement(BaseModel):
    rule_or_group: Literal["rule"] = "rule"
    mandatory: int = 1  # required number of people
    optional: int = 1  # optional extra people
    skills: list[Skill]


class RequirementGroup(BaseModel):
    rule_or_group: Literal["group"] = "group"
    group_type: RequirementType
    requirements: list[
        Annotated[
            Union[Requirement, "RequirementGroup"], Field(discriminator="rule_or_group")
        ]
    ]


class ActivityTag(BaseModel):
    id: uuid.UUID
    name: str


class AssignmentTag(BaseModel):
    id: uuid.UUID
    name: str


class TimeSlot(BaseModel):
    start: datetime.datetime
    finish: datetime.datetime


class ActivityType(Enum):
    TEMPLATE = "template"
    CONCRETE = "concrete"


class ActivityBase(BaseModel):
    id: uuid.UUID
    type: ActivityType
    name: str
    activity_tags: list[ActivityTag]
    location_id: uuid.UUID | None = None
    timeslots: list[TimeSlot] | None = None
    requirements: RequirementGroup | None = None


class ActivityTemplate(ActivityBase):
    "activity template"

    type: Literal[ActivityType.TEMPLATE] = ActivityType.TEMPLATE
    recurrence_rules: RuleGroup | None = None
    start_time: datetime.time | None
    duration: datetime.timedelta | None

    def materialise(self, activity_date: datetime.date, force=False) -> "Activity":
        if not force:
            if self.recurrence_rules is not None:
                if not self.recurrence_rules.matches(activity_date):
                    raise ValueError("activity_date does not match recurrence rules")
        return Activity.from_template(self, activity_date=activity_date)


class Activity(ActivityBase):
    "activity concrete"

    type: Literal[ActivityType.CONCRETE] = ActivityType.CONCRETE
    template_id: uuid.UUID | None = None
    staff_assignments: list["StaffAssignment"] = []
    activity_start: datetime.datetime
    activity_finish: datetime.datetime

    @classmethod
    def from_template(
        cls,
        template: ActivityTemplate,
        activity_date: datetime.date | None = None,
        activity_start: datetime.datetime | None = None,
        activity_finish: datetime.datetime | None = None,
        location_id: uuid.UUID | None = None,
    ):
        if activity_date is None and activity_start is None:
            raise ValueError("activity_date or activity_start must be provided")
        if activity_start is None:
            activity_start = datetime.datetime.combine(
                activity_date, template.start_time
            )
        if activity_finish is None:
            if template.duration is None:
                raise ValueError("activity_finish or duration must be provided")
            activity_finish = activity_start + template.duration
        if activity_finish < activity_start:
            raise ValueError("activity_finish must be after activity_start")

        return cls(
            id=uuid.uuid4(),
            type=ActivityType.CONCRETE,
            template_id=template.id,
            name=template.name,
            activity_tags=[at for at in template.activity_tags],
            location_id=location_id or template.location_id,
            requirements=template.requirements.model_copy(),
            staff_assignments=[],
            activity_start=activity_start,
            activity_finish=activity_finish,
        )


class StaffAssignment(BaseModel):
    "staff assignment"

    activity: Activity
    staff: Staff
    attendance: int = 100
    tags: list[AssignmentTag]
    start_time: datetime.datetime | None
    finish_time: datetime.datetime | None


class PersonalPatternEntry(BaseModel):
    id: uuid.UUID
    dateoffset: int
    activity_tags: str


class PersonalPattern(BaseModel):
    "template of offers of cover"

    id: uuid.UUID
    staff: Staff
    ruleset: RuleGroup
    name: str
    entries: list[PersonalPatternEntry]

    def materialise(self, activities: dict[datetime.date, list["Activity"]]):
        first_date = min(activities, None)
        last_date = max(activities, None)
        if first_date is None:
            return
        date = first_date
        while date <= last_date:
            results = []
            if not self.ruleset.matches(date):
                continue
            for entry in self.entries:
                if date + datetime.timedelta(days=entry.dateoffset) not in activities:
                    break
                possibilities = set()
                # iterate through all activities on each day
                for activity in activities[
                    date + datetime.timedelta(days=entry.dateoffset)
                ]:
                    if not entry.activity_tags.isdisjoint(
                        activity.template.activity_tags
                    ):
                        # if any tags in the offer are in the activity, add as a possibility
                        possibilities.add(activity.id)
                    if activity.template.id in entry.activity_tags:
                        # if there is a specific offer to do this activity, then add to possibilities
                        possibilities.add(activity.id)
                if len(possibilities) == 0:
                    # no possibilities for this entry - abort
                    break
                results.append(possibilities)
            for combination in itertools.product(*results):
                combi = set(combination)
                if len(combi) == len(self.entries):  # exactly one activity per entry
                    yield combi
            date += datetime.timedelta(days=1)


# solver


@dataclass
class PotentialStaffAssignment:
    "staff assignment"

    activity_id: uuid.UUID
    staff_id: uuid.UUID
    requirement_id: int
    start_time: datetime.datetime
    finish_time: datetime.datetime
    location: str
    required_attendance: int
    model: cp_model.CpModel
    attendance: cp_model.IntVar = field(init=False)
    is_committed: cp_model.IntVar = field(init=False)
    tags: str

    def __post_init__(self):
        self.attendance = self.model.new_int_var(0, 100, repr(self) + "attendance")
        self.is_committed = self.model.new_bool_var(repr(self) + "committed")
        self.model.add_implication(self.is_committed == 0, self.attendance == 0)
        self.model.add_implication(
            self.is_committed == 1, self.attendance >= self.required_attendance
        )


def make_potential_assignments(
    model: cp_model.CpModel,
    offers: list[tuple[uuid.UUID, set[uuid.UUID]]],
    activities: list[Activity],
    staff: list[Staff],
):
    activities: list[Activity] = []
    staff: list[Staff] = []
    offers = [
        (model.new_bool_var(""), staff_id, activity_set)
        for staff_id, activity_set in offers
    ]
    all_potential_assignments: list[PotentialStaffAssignment] = []
    time_boundaries = {}
    for activity in activities:
        time_boundaries[activity.activity_start] = None
        time_boundaries[activity.activity_finish] = None
    time_boundaries[datetime.datetime(2099, 1, 1)] = None
    geofences: dict[
        tuple[uuid.UUID, str, datetime.datetime, datetime.datetime],
        tuple[cp_model.IntervalVar, cp_model.IntVar],
    ] = {}
    for boundary, next_bound in itertools.pairwise(sorted(time_boundaries)):
        time_boundaries[boundary] = next_bound

    active_requirements = {}

    def flatten_requirement(requirement_group, is_active: cp_model.IntVar):
        requirement_nodes = []
        for g in requirement_group.subgroups:
            new_node = model.new_bool_var(repr(requirement_group))
            requirement_nodes.append(new_node)
            yield from flatten_requirement(g, new_node)
        for req in requirement_group.requirements:
            active_requirements[req.id] = model.new_bool_var(repr(req))
            requirement_nodes.append(active_requirements[req.id])
        if requirement_group.group_type == RequirementType.AND:
            model.add_bool_and(requirement_nodes).only_enforce_if(is_active)
        elif requirement_group.group_type == RequirementType.OR:
            model.add_exactly_one(requirement_nodes).only_enforce_if(is_active)
        model.add(sum(requirement_nodes) == 0).only_enforce_if(is_active.negated())

    for activity in activities:
        activity_is_staffed = model.new_bool_var(repr(activity) + "staffed")
        req_set = list(flatten_requirement(activity.requirement, activity_is_staffed))
        for requirement in req_set:
            this_req: list[PotentialStaffAssignment] = []
            for staff_member in staff:
                if requirement.skills.issubset(set(staff_member.skills.split())):
                    req = PotentialStaffAssignment(
                        activity_id=activity.id,
                        staff_id=staff_member.id,
                        actual_location=(
                            activity.location
                            if requirement.geofence == "_immediate"
                            else requirement.geofence
                        ),
                        required_attendance=requirement.attendance,
                        requirement_id=requirement.id,
                        model=model,
                        start_time=activity.activity_start,
                        finish_time=activity.activity_finish,
                    )
                    low_bound = activity.activity_start
                    while low_bound < activity.activity_finish:
                        high_bound = time_boundaries[low_bound]
                        key = (
                            staff_member.id,
                            req.location,
                            low_bound,
                            high_bound,
                        )
                        if key not in geofences:
                            offer_active = model.new_bool_var("")
                            geofences[key] = (
                                model.new_optional_fixed_size_interval_var(
                                    low_bound.timestamp(),
                                    high_bound.timestamp() - low_bound.timestamp(),
                                    offer_active,
                                ),
                                offer_active,
                            )
                        interval, offer_active = geofences[key]
                        model.add_implication(req.is_committed, offer_active)
                    all_potential_assignments.append(req)
                    this_req.append(req)
            model.add(
                sum(psa.is_committed for psa in this_req) >= requirement.mandatory
            )
            model.add(
                sum(psa.is_committed for psa in this_req)
                <= (requirement.mandatory + requirement.optional)
            )

    by_activity_and_staff: dict[
        tuple[uuid.UUID, uuid.UUID], list[PotentialStaffAssignment]
    ] = {}
    for psa in all_potential_assignments:
        by_activity_and_staff.setdefault((psa.activity_id, psa.staff_id), []).append(
            psa
        )
    offers_by_activity_and_staff: dict[
        tuple[uuid.UUID, uuid.UUID], list[cp_model.IntVar]
    ] = {}

    for offer_active, staff_member, activityset in offers:
        for act in activityset:
            offers_by_activity_and_staff.setdefault((act, staff_member.id), []).append(
                offer_active
            )
            model.add_at_least_one(
                psa.is_committed
                for psa in by_activity_and_staff[(act, staff_member.id)]
            ).only_enforce_if(offer_active)
    for act_id_staff_id, psalist in by_activity_and_staff.items():
        for psa in psalist:
            if act_id_staff_id not in offers_by_activity_and_staff:
                model.add(psa.is_committed == 0)
            else:
                model.add_at_least_one(offers_by_activity_and_staff[act_id_staff_id])
    intervals_by_staff = {}
    for psa in all_potential_assignments:
        start_time = int(psa.start_time.timestamp())
        duration = int(psa.finish_time.timestamp()) - start_time
        intervals_by_staff.setdefault(psa.staff_id, []).append(
            (
                psa.attendance,
                model.new_optional_fixed_size_interval_var(
                    start_time, duration, psa.is_active
                ),
            )
        )
    for i in intervals_by_staff.values():
        demands, intervals = zip(*i)
        model.add_cumulative(intervals=intervals, demands=demands, capacity=100)
    geofence_dict = {}
    for key, (interval, active) in geofences.items():
        geofence_dict.setdefault(key[0], []).append(interval)
    for interval_list in geofence_dict.values():
        model.add_no_overlap(interval_list)
    return all_potential_assignments


def process_potential_assignments(
    solver: cp_model.CpSolver, potential_assignments: list[PotentialStaffAssignment]
):
    for psa in potential_assignments:
        if solver.value(psa.attendance) > 0:
            yield StaffAssignment(
                activity_id=psa.activity_id,
                staff_id=psa.staff_id,
                attendance=solver.value(psa.attendance),
                start_time=psa.start_time,
                finish_time=psa.finish_time,
                tags=psa.tags,
            )
