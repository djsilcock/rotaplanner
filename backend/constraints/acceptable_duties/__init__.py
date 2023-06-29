"""contains rules to constrain the model"""
from collections import defaultdict
import datetime
from typing import Callable, TYPE_CHECKING
import dataclasses

from sqlalchemy import select

from constraints.utils import BaseConstraint
from constraints.core_duties import Clinical, NonClinical, allocated_for_duty
from constraints.constraint_store import register_constraint
from .enums import DutyBasis, RotationType
from .model import AcceptableDutiesEntry

if TYPE_CHECKING:
    from solver import GenericConfig
    from sqlalchemy.orm import Session

nonclinical_duties = set(NonClinical)
clinical_duties = set(Clinical)
duty_bases = set(DutyBasis)

def find(dct:dict,val):
    try:
        return next(k for k,v in dct.items() if v==val)
    except StopIteration:
        raise ValueError()

def allocation_basis(shift: str, day: datetime.date, staff: str, duty_basis: str):
    "is allocated on a certain basis"
    assert duty_basis in duty_bases
    return ('ALLOCATION_BASIS', shift, day, staff, duty_basis)


@dataclasses.dataclass
class AcceptableDutiesContext:
    "Context"
    


@register_constraint("acceptable_duties")
class Constraint(BaseConstraint):
    """Apply jobplan to staffmember"""
    name = "Apply jobplans"
    staff = None
    jobplanned_dcc: dict[tuple, set]
    rules: list[AcceptableDutiesEntry]

    def apply_constraint(self):
        """apply jobplans"""
        db_session=self.ctx.db_session
        self.jobplanned_dcc=defaultdict(set)
        self.rules=list(db_session.scalars(
                select(AcceptableDutiesEntry)
            ).all())

        def is_x_of_y(startdate: datetime.date, numerator, denominator, testdate: datetime.date):
            if startdate > testdate:
                return False
            week_num = ((testdate-startdate).days//7)  # will be zero-indexed
            if isinstance(numerator, int):
                return (week_num % denominator)+1 == numerator
            if isinstance(numerator, tuple):
                return (week_num % denominator)+1 in numerator
            raise TypeError('expected int or tuple for numerator')

        def is_x_of_month(numerator, testdate: datetime.date):
            week_num = testdate.day//7
            if isinstance(numerator, int):
                return numerator == week_num+1
            if isinstance(numerator, tuple):
                return week_num+1 in numerator
            raise TypeError('expected int or tuple for numerator')
        for entry in self.rules:
            for day in self.days(self.ctx):
                for shift in ('am', 'pm', 'oncall'):
                    shift_id = f"{'mon tue wed thu fri sat sun'.split()[day.weekday]}-{shift}"
                    if shift_id not in entry.sessions:
                        continue
                    match entry:
                        case AcceptableDutiesEntry(
                            rotation_type=RotationType.XINY,
                            weeks=weeks,
                            cycle=cycle
                        ):
                            if not is_x_of_y(entry.startdate, weeks, cycle, day):  # type: ignore
                                continue
                        case AcceptableDutiesEntry(
                                rotation_type=RotationType.XINMONTH,
                                weeks=weeks):
                            if not is_x_of_month(weeks, day):
                                continue
                    for duty_type in entry.acceptable_duties:
                        self.jobplanned_dcc[(self.staff, day, shift)].add(
                            (duty_type, entry.availability_basis))

        available_for = set()
        all_staff = set()
        all_days = set()
        all_shifts = set()
        for (staff, day, shift), duties in self.jobplanned_dcc.items():
            all_staff.add(staff)
            all_days.add(day)
            all_shifts.add(shift)
            is_jobplanned = any(duty[1] == DutyBasis.DCC for duty in duties)
            for duty_type, duty_basis in duties:
                if is_jobplanned and duty_basis != DutyBasis.DCC:
                    duty_basis = DutyBasis.DUTYCHANGE
                available_for.add((staff, day, shift, duty_type,
                                   duty_basis))
        for staff in all_staff:
            for day in all_days:
                for shift in all_shifts:
                    duty_atoms = [
                        self.ctx.dutystore[allocated_for_duty(
                            shift, day, staff, loc)]
                        for loc in self.ctx.locations
                    ]
                    basis_atoms = [
                        self.ctx.dutystore[allocation_basis(
                            shift, day, staff, basis)]
                        for basis in duty_bases
                    ]
                    self.ctx.model.AddExactlyOne(*duty_atoms)
                    self.ctx.model.AddExactlyOne(*basis_atoms)
                    for duty in self.ctx.locations:
                        for basis in duty_bases:
                            duty_atom = self.ctx.dutystore[allocated_for_duty(
                                shift, day, staff, duty)]
                            basis_atom = self.ctx.dutystore[allocation_basis(
                                shift, day, staff, basis)]
                            if (staff, day, shift, duty, basis) not in available_for:
                                self.ctx.model.AddForbiddenAssignments(
                                    [duty_atom, basis_atom], [(True, True)])
            self.ctx.model.Add(sum(self.ctx.dutystore[allocation_basis(shift, day, staff, DutyBasis.TIMESHIFT)]
                          for shift in all_shifts for day in all_days) <=
                          sum(self.ctx.dutystore[allocated_for_duty(shift, day, staff, find(self.ctx.locations,'TIMEBACK'))]
                          for shift in all_shifts for day in all_days))
