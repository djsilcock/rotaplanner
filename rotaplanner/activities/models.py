import datetime
import itertools
import uuid
from dataclasses import dataclass, field
from enum import Enum

from ortools.sat.python import cp_model
from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rotaplanner.database import db

from rotaplanner.date_rules import RuleGroup, RuleRoot, GroupType

from functools import reduce


MIN_DATE = datetime.date(1900, 1, 1)
MAX_DATE = datetime.date(2100, 12, 31)


class RequirementType(Enum):
    AND = "AND"
    OR = "OR"


class Skill(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]


class StaffSkill(db.Model):
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill.id"), primary_key=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id"), primary_key=True
    )


class Staff(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    skills: Mapped[list[Skill]] = relationship(secondary=StaffSkill.__table__)
    assignments: Mapped[list["StaffAssignment"]] = relationship(back_populates="staff")


class Location(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]


class SkillRequirement(db.Model):
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill.id"), primary_key=True
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("requirement.id"), primary_key=True
    )


class Requirement(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activity_base.id"))
    mandatory: Mapped[int] = mapped_column(default=1)  # required number of people
    optional: Mapped[int] = mapped_column(default=1)  # optional extra people
    attendance: Mapped[int] = mapped_column(
        default=100
    )  # required attendance for this role (eg remote supervisor=50%)
    geofence: Mapped[str] = mapped_column(
        default="_immediate"
    )  # must not clash with duty outside this zone (eg main theatre)
    skills: Mapped[list[Skill]] = relationship(
        secondary=SkillRequirement.__table__
    )  # must have these skills

    def clone(self):
        return Requirement(
            id=uuid.uuid4(),
            mandatory=self.mandatory,
            optional=self.optional,
            attendance=self.attendance,
            geofence=self.geofence,
            skills=[s for s in self.skills],
        )


class ActivityTag(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]


class ActivityTagAssoc(db.Model):
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_tag.id"), primary_key=True
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_base.id"), primary_key=True
    )


class AssignmentTag(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]


class AssignmentTagAssoc(db.Model):
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignment_tag.id"), primary_key=True
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint(
            ("activity_id", "staff_id"),
            ("staff_assignment.activity_id", "staff_assignment.staff_id"),
        ),
    )


class ActivityBase(RuleRoot):
    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_root.id"), primary_key=True)
    name: Mapped[str]
    activity_tags: Mapped[list[ActivityTag]] = relationship(
        secondary=ActivityTagAssoc.__table__
    )
    location: Mapped[Location] = relationship()
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("location.id"))
    requirements: Mapped[list[Requirement]] = relationship(cascade="all,delete")
    __mapper_args__ = {"polymorphic_identity": "base"}


class ActivityTemplate(ActivityBase):
    __mapper_args__ = {"polymorphic_identity": "template"}
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_base.id"), primary_key=True, default=uuid.uuid4
    )
    start_time: Mapped[datetime.time]
    finish_time: Mapped[datetime.time]
    group_type: Mapped[GroupType]

    def date_range(self):
        def maxmin(a, b):
            if a == (None, None):
                return (b, b)
            return min(a[0], b), max(a[1], b)

        result = reduce(
            maxmin,
            filter(
                lambda d: self.matches(d),
                (
                    MIN_DATE + datetime.timedelta(days=i)
                    for i in range((MAX_DATE - MIN_DATE).days + 1)
                ),
            ),
            (None, None),
        )
        return (
            None if result[0] == MIN_DATE else result[0],
            None if result[1] == MAX_DATE else result[1],
        )

    def materialise(self, date, force=False):
        "returns concrete activity for date. If force is false or not given then only returns if planned for that day"
        if force or self.ruleset.matches(date):
            return Activity(
                id=uuid.uuid4(),
                template_id=self.id,
                name=self.name,
                location=self.location,
                activity_start=datetime.datetime.combine(date, self.start_time),
                activity_finish=datetime.datetime.combine(date, self.finish_time)
                + datetime.timedelta(
                    days=(0 if self.finish_time > self.start_time else 1)
                ),
                activity_tags=[tag for tag in self.activity_tags],
                requirements=[req.clone() for req in self.requirements],
                location_id=self.location_id,
            )


class Activity(ActivityBase):
    "concrete activity class"
    __mapper_args__ = {"polymorphic_identity": "concrete"}
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_base.id"), primary_key=True
    )
    activity_start: Mapped[datetime.datetime]
    activity_finish: Mapped[datetime.datetime]
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activity_template.id")
    )
    staff_assignments: Mapped[list["StaffAssignment"]] = relationship()


class StaffAssignment(db.Model):
    "staff assignment"
    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity.id"), primary_key=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id"), primary_key=True
    )
    activity: Mapped["Activity"] = relationship(back_populates="staff_assignments")
    staff: Mapped[Staff] = relationship(back_populates="assignments")
    attendance: Mapped[int] = 100
    staff: Mapped[Staff] = relationship()
    tags: Mapped[list[AssignmentTag]] = relationship(
        secondary=AssignmentTagAssoc.__table__
    )
    start_time: Mapped[datetime.datetime | None]
    finish_time: Mapped[datetime.datetime | None]


class PersonalPatternEntry(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    dateoffset: Mapped[int]
    activity_tags: Mapped[str]
    template_id: Mapped[uuid.UUID]
    pattern_id: Mapped[int] = mapped_column(ForeignKey("personal_pattern.id"))


class PersonalPattern(db.Model):
    "template of offers of cover"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    staff: Mapped[str]
    ruleset_id: Mapped[int] = mapped_column(ForeignKey("rule_group.id"))
    ruleset: Mapped[RuleGroup] = relationship()
    name: Mapped[str]
    entries: Mapped[list[PersonalPatternEntry]] = relationship(cascade="all,delete")

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
