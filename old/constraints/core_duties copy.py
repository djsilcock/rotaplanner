"Define core duties and that one person is on for ICU"

from datetime import date
import operator
from calendar import SATURDAY, SUNDAY
from typing import NamedTuple,Callable

from signals import signal
from old.constraint_ctx import BaseConstraintConfig, DutyStore


clinical_duty_types = ('THEATRE', 'ICU')
apply_constraint = signal('apply_constraint')
build_output = signal('build_output')
register_urls = signal('register_urls')

class CoreDutiesConfig(NamedTuple):
    locations:tuple[str,...]
    tags:tuple[str,...]
    groups:dict[str,tuple[str,...]]
    rules:list[tuple|dict]

class CoreDuties(BaseConstraintConfig):
    constraint_name = 'core_duties'
    dutystore: DutyStore[tuple[str, date, str, str]]
    locations: tuple[str, ...]
    tags: tuple[str, ...]
    groups:dict[str,tuple[str,...]]
    rules: list[tuple | dict]

    @staticmethod
    def load_config():
        return CoreDutiesConfig(
            locations=('NA', 'ICU', 'THEATRE', 'LEAVE', 'TIMEBACK'),
            tags = ('CLINICAL', 'NONCLINICAL',
                     'JOBPLANNED', 'NOTJOBPLANNED',
                     'LEAVE_JP', 'LEAVE_NJP', 'NOT_LEAVE',
                     'EXTRA', 'QUOTA', 'LOCUM_PAY', 'TIMESHIFT'),
            groups = {
                '*EXTRA': ('LOCUM_PAY', 'TIMESHIFT'),
                '*CLINICAL': ('ICU', 'THEATRE'),
                '*NONCLINICAL': ('LEAVE', 'NA', 'TIMEBACK'),
                    },
            rules = [
                ('== 1', ('*CLINICAL', 'NONCLINICAL')),
                ('== 1', ('*NONCLINICAL', 'CLINICAL')),
                ('== 1', ('CLINICAL', 'NONCLINICAL')),
                ('== 1', ('NOTJOBPLANNED', 'LEAVE_JP', 'CLINICAL', 'TIMEBACK')),
                ('== 1', ('JOBPLANNED', 'NA', 'LEAVE_NJP', 'EXTRA', 'QUOTA')),
                ('== 1', ('JOBPLANNED', 'NOTJOBPLANNED')),
                ('== 1', ('LEAVE_JP', 'LEAVE_NJP', 'NOT_LEAVE')),
                ('== 1', ('LEAVE', 'NOT_LEAVE')),
                ('== 1', ('NOT_EXTRA', '*EXTRA')),
                ('== 1', ('EXTRA', 'NOT_EXTRA'))
            ]
            )

    def setup(self):
        self.dutystore = DutyStore(self.model)
        config=self.load_config()
        self.locations = config.locations
        self.tags = config.tags
        self.groups = config.groups
        self.rules = config.rules

    def allocated_for_duty(self, shift: str, day: date, staff: str, location: str):
        "is allocated for a given duty"
        if location not in self.locations and location not in self.tags:
            raise KeyError(f'{location} not recognised')
        return self.dutystore[(shift, day, staff, location)]

    def add_conditions(self, shift, day, staff, rules, *conditions):
        def expand(group):
            for g in group:
                if g in self.locations:
                    yield g
                elif g in self.tags:
                    yield g
                elif g in self.groups:
                    yield from expand(self.groups[g])
                else:
                    raise KeyError(
                        f'{g} is not a recognised location,tag or group')
        for rule in rules:
            match rule:
                case (str(cmp), *grp) if ' ' in cmp:
                    total = sum(self.allocated_for_duty(
                        shift, day, staff, loc) for loc in expand(grp))
                    match cmp.partition(' '):
                        case (op, ' ', length) if int(length):
                            length = int(length)
                            comparison = {'==': operator.eq,
                                          '!=': operator.ne,
                                          '>=': operator.ge,
                                          '<=': operator.le,
                                          '>': operator.gt,
                                          '<': operator.lt}[op](total, length)
                            r = self.model.Add(comparison)
                        case _:
                            raise ValueError(f'{cmp} not recognised')
                case ('ALL', *grp):
                    r = self.model.Add(
                        sum(self.allocated_for_duty(shift, day, staff, loc) for loc in expand(grp)) == len(grp))
                case {'IF': if_condition}:
                    if 'THEN' in rule:
                        self.add_conditions(shift,day,staff,rule['THEN'], self.allocated_for_duty(
                            shift, day, staff, if_condition) == 1, *conditions)
                    if 'ELSE' in rule:
                        self.add_conditions(shift,day,staff,rule['ELSE'], self.allocated_for_duty(
                            shift, day, staff, if_condition) == 0, *conditions)
                    continue
                case _:
                    raise ValueError()
            for c in conditions:
                assert r is not None  # just for the typechecker
                r.OnlyEnforceIf(c)

    def apply_constraint(self):
        "No multitasking"
        for day in self.core_config.days:
            for shift in self.core_config.shifts:
                # one person can only be doing one thing at a time
                for staff in self.ctx.core_config.staff:
                    self.model.Add(
                        sum(self.allocated_for_duty(shift, day, staff, duty_type)
                            for duty_type in self.locations) == 1)
                    self.add_conditions(shift, day, staff, self.rules)

    def result(self, staff, day, shift, sessionduty, solution):
        "core duties output"
        for loc in self.locations:
            if solution.Value(self.allocated_for_duty(shift, day, staff, loc)):
                sessionduty.duty = loc

class RequiredCoverageConfig(NamedTuple):
    day:int
    shift:str
    duty:str
    op:Callable
    value:int

op_symbols={
            "==": operator.eq,
            ">=": operator.ge,
            "<=": operator.le,
            ">": operator.gt,
            "<": operator.lt
            }

class RequiredCoverage(BaseConstraintConfig):
    constraint_name = "required_coverage"

    @classmethod
    def load_config(cls):
        return [
        *(RequiredCoverageConfig(day, shift, 'ICU', operator.eq, 1) for day in range(7)
          for shift in ('am', 'pm', 'oncall')),
        *(RequiredCoverageConfig(day, 'oncall', 'THEATRE', operator.eq, 1) for day in range(7)),
        *(RequiredCoverageConfig(day, shift, 'THEATRE', operator.eq, 1)
          for day in (SATURDAY, SUNDAY) for shift in ('am', 'pm')),
        *(RequiredCoverageConfig(day, shift, 'THEATRE', operator.ge, 1) for day in range(5) for shift in ('am', 'pm'))
        ]
    @classmethod
    def validate_frontend_json(cls, json_config, orig_config):
        match json_config:
            case {'constraint':'required_coverage','requirements':[*requirements]}:
                coreconfig=CoreDuties.load_config()
                all_errors={}
                config:list[RequiredCoverageConfig]=[]
                for idx,(weekday,shift,duty,op,req) in enumerate(requirements):
                    errors={}
                    if weekday not in range(7):
                        errors['weekday']='Weekday must be in range 0-6'
                    if shift not in ('am','pm','oncall','eve','night'):
                        errors['shift']='Unrecognised shift name'
                    if duty not in (*coreconfig.locations,*coreconfig.tags,*coreconfig.groups):
                        errors['duty']=f'Unrecognised duty name:{duty}'
                    if op not in op_symbols:
                        errors['op']=f'Unrecognised operator:{op}'
                    if not isinstance(req,int):
                        errors['req']='Must be a number'
                    if len(errors)>0:
                        all_errors[idx]=errors
                    else:
                        config.append(RequiredCoverageConfig(
                            day=weekday,
                            shift=shift,
                            duty=duty,
                            op=op_symbols[op],
                            value=req
                        ))
                if len(all_errors)>0:
                    raise ValueError(all_errors)
                return config
            case _:
                return None

    
    def apply_constraint(self):
        cdctx = CoreDuties.from_context(self.ctx)
        for day in self.ctx.core_config.days:
            for (weekday, shift, dutytype, oper, requirement) in self.load_config():
                if day.weekday() == weekday:
                    self.model.Add(oper(sum(cdctx.allocated_for_duty(shift, day, staff, dutytype)
                                            for staff in self.core_config.staff), requirement))
