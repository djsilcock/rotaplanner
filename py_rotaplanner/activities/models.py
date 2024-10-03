import datetime
import itertools
import uuid

from ortools.sat.python import cp_model
from pydantic import BaseModel, Field, RootModel
from sqlalchemy import types as sa_types
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel

try:
    from py_rotaplanner.date_rules import RuleGroup
except ImportError:
    import os
    import sys

    sys.path.append(os.path.realpath("."))
    from py_rotaplanner.date_rules import RuleGroup


class Requirement(BaseModel):
    mandatory: int = 1  # required number of people
    optional: int = 1  # optional extra people
    attendance: int = (
        100  # required attendance for this role (eg remote supervisor=50%)
    )
    geofence: str = (
        "_immediate"  # must not clash with duty outside this zone (eg main theatre)
    )
    skills: set[str] = Field(default_factory=set)  # must have these skills


class ActivityTemplate(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    ruleset: RuleGroup
    name: str
    activity_tags: set[str]
    start_time: datetime.time
    duration: datetime.timedelta
    location: str
    requirement: list[tuple[Requirement]] = Field(default_factory=list)

    def matches(self, date) -> bool:
        "returns true if activity planned to take place on given date"
        return self.ruleset.matches(date)

    def materialise(self, date, force=False):
        "returns concrete activity for date. If force is false or not given then only returns if planned for that day"
        if force or self.ruleset.matches(date):
            return Activity(
                template_id=self.id,
                name=self.name,
                location=self.location,
                activity_start=datetime.datetime.combine(date, self.start_time),
                activity_finish=datetime.datetime.combine(date, self.start_time)
                + self.duration,
            )


class Staff(SQLModel, table=True):
    id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    name: str
    skills: str = ""
    assignments: list["StaffAssignment"] = Relationship(back_populates="staff")


class StaffAssignment(SQLModel, table=True):
    "staff assignment"
    activity_id: uuid.UUID = SQLField(
        primary_key=True, foreign_key="activity.activity_id"
    )
    staff_id: uuid.UUID = SQLField(primary_key=True, foreign_key="staff.id")
    activity: "Activity" = Relationship(back_populates="staff_assignments")
    staff: Staff = Relationship(back_populates="assignments")
    attendance: int = 100
    staff: Staff = Relationship()
    tags: str = Field(default="")
    start_time: datetime.datetime | None
    finish_time: datetime.datetime | None


RequirementList = RootModel[list[tuple[Requirement]]]


class PydanticWrapper(sa_types.TypeDecorator):
    def __init_subclass__(cls, pydantic_type):
        cls.__pydantic_type = pydantic_type

    impl = sa_types.Unicode
    cache_ok = True

    def process_bind_param(self, value: RequirementList, dialect):
        return self.__pydantic_type(value).model_dump_json()

    def process_result_value(self, value, dialect):
        return self.__pydantic_type.model_validate_json(value)

    def copy(self, **kw):
        return type(self)(self.impl.length)


class DBRequirementList(PydanticWrapper, pydantic_type=RequirementList): ...


class Activity(SQLModel, table=True):
    "concrete activity class"
    activity_id: uuid.UUID = SQLField(default_factory=uuid.uuid4, primary_key=True)
    template_id: uuid.UUID
    name: str | None
    location: str
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    staff_assignments: list[StaffAssignment] = Relationship()
    requirement: RequirementList = SQLField(
        sa_type=DBRequirementList, default_factory=list
    )


class PersonalPatternEntry(BaseModel):
    dateoffset: int
    activity_tags: set[str]
    template_id: uuid.UUID


class PersonalPattern(BaseModel):
    "template of offers of cover"
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    staff: str
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


class PotentialStaffAssignment(BaseModel, arbitrary_types_allowed=True):
    "staff assignment"
    activity_id: uuid.UUID
    staff_id: uuid.UUID
    actual_location: str
    attendance: int
    tags: str = Field(default="")
    start_time: datetime.datetime | None
    finish_time: datetime.datetime | None
    is_active: cp_model.IntVar | None


class RequirementSet(BaseModel, arbitrary_types_allowed=True):
    is_active: cp_model.IntVar
    potential_assignments: list[PotentialStaffAssignment] = Field(default_factory=list)


def make_potential_assignments(model: cp_model.CpModel, offers):
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
    for activity in activities:
        req_sets = []
        for requirement_set in activity.requirement:
            req_set = RequirementSet(is_active=model.new_bool_var(""))
            for requirement in requirement_set:
                this_req = []
                for staff_member in staff:
                    if requirement.skills.issubset(set(staff_member.skills.split())):
                        req = PotentialStaffAssignment(
                            activity_id=activity.activity_id,
                            staff_id=staff_member.id,
                            actual_location=(
                                activity.location
                                if requirement.geofence == "_immediate"
                                else requirement.geofence
                            ),
                            attendance=requirement.attendance,
                            start_time=activity.activity_start,
                            finish_time=activity.activity_finish,
                            is_active=model.new_bool_var(""),
                        )
                        low_bound = activity.activity_start
                        while low_bound < activity.activity_finish:
                            high_bound = time_boundaries[low_bound]
                            key = (
                                staff_member.id,
                                req.actual_location,
                                low_bound,
                                high_bound,
                            )
                            if key not in geofences:
                                is_active = model.new_bool_var("")
                                geofences[key] = (
                                    model.new_optional_fixed_size_interval_var(
                                        low_bound.timestamp(),
                                        high_bound.timestamp() - low_bound.timestamp(),
                                        is_active,
                                    ),
                                    is_active,
                                )
                            interval, active = geofences[key]
                            model.add_implication(req.is_active, active)

                        model.add_implication(
                            req_set.is_active == 0, req.is_active == 0
                        )
                        this_req.append(req)
                        all_potential_assignments.append(req)
                model.add(
                    sum(psa.is_active for psa in this_req) >= requirement.mandatory
                )
                model.add(
                    sum(psa.is_active for psa in this_req)
                    <= (requirement.mandatory + requirement.optional)
                )
                req_set.potential_assignments.extend(this_req)
            req_sets.append(req_sets)
        model.add_at_most_one(reqset.is_active for reqset in req_sets)
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
    for is_active, staff_member, activityset in offers:
        for act in activityset:
            offers_by_activity_and_staff.setdefault((act, staff_member.id), []).append(
                is_active
            )
            model.add_at_least_one(
                psa.is_active for psa in by_activity_and_staff[(act, staff_member.id)]
            ).only_enforce_if(is_active)
    for act_id_staff_id, psalist in by_activity_and_staff.items():
        for psa in psalist:
            if act_id_staff_id not in offers_by_activity_and_staff:
                model.add(psa.is_active == 0)
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
