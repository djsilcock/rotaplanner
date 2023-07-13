"Define core duties and that one person is on for ICU"

from datetime import date
import operator
from calendar import SATURDAY, SUNDAY


from signals import signal
from constraint_ctx import BaseConstraintConfig


clinical_duty_types = ('THEATRE', 'ICU')
apply_constraint = signal('apply_constraint')
build_output = signal('build_output')
register_urls = signal('register_urls')


class CoreDuties(BaseConstraintConfig):
    constraint_name = 'core_duties'
    def allocated_for_duty(self, shift: str, day: date, staff: str, location: str):
        "is allocated for a given duty"
        if location not in self.locations and location not in self.groups:
            raise KeyError(f'{location} not recognised')
        return self.dutystore[('ALLOCATED_DUTY', shift, day, staff, location)]
    locations = ('NA', 'ICU', 'THEATRE', 'LEAVE')
    tags = ('CLINICAL','NONCLINICAL','JOBPLANNED','NOTJOBPLANNED','EXTRA')
    
    rules = [
        ('== 1', ('THEATRE', 'ICU', 'NONCLINICAL')),
        ('== 1', ('LEAVE', 'NA', 'CLINICAL')),
        ('== 1', ('CLINICAL', 'NONCLINICAL')),
        {'IF': 'JOBPLANNED', 'THEN': [('==1', ('CLINICAL', 'LEAVE'))]},
        {'IF': 'NOTJOBPLANNED','THEN':[('==1',('NA','LEAVE','EXTRA'))]},
        {'IF': 'OOH','THEN':[('==1',('QUOTA','LOCUM','NONCLINICAL'))]},
        ('== 1', ('JOBPLANNED', 'NOTJOBPLANNED','OOH'))
    ]

    def add_conditions(self, shift, day, staff, rules, *conditions):
        for rule in rules:
            match rule:
                case (str(cmp), *grp) if ' ' in cmp:
                    total=sum(self.allocated_for_duty(
                        shift, day, staff, loc) for loc in grp)
                    match cmp.partition(' '):
                        case (op,' ',length) if int(length):
                            length=int(length)
                            match op:
                                case '==':
                                    r = self.model.Add(total == length)
                                case ('!=',' ',int(length)):
                                    r = self.model.Add(total != length)
                                case ('>=',' ',int(length)):
                                    r = self.model.Add(total >= length)
                                case ('<=',' ',int(length)):
                                    r = self.model.Add(total <= length)
                                case ('>',' ',int(length)):
                                    r = self.model.Add(total >  length)
                                case ('<',' ',int(length)):
                                    r = self.model.Add(total <  length)
                                case _:
                                    raise ValueError(op)
                        case _:
                            raise ValueError()
                case ('ALL',*grp):
                    r = self.model.Add(
                        sum(self.allocated_for_duty(shift, day, staff, loc) for loc in grp) == len(grp))
                case {'IF': if_condition}:
                    if 'THEN' in rule:
                        self.add_conditions(rule['THEN'], self.allocated_for_duty(
                            shift, day, staff, if_condition) == 1, *conditions)
                    if 'ELSE' in rule:
                        self.add_conditions(rule['ELSE'], self.allocated_for_duty(
                            shift, day, staff, if_condition) == 0, *conditions)
                    continue
                case _:
                    raise ValueError()
            for c in conditions:
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


class RequiredCoverage(BaseConstraintConfig):
    constraint_name = "required_coverage"
    cover_requirements = [
        *((day, shift, 'ICU', "==", 1) for day in range(7)
          for shift in ('am', 'pm', 'oncall')),
        *((day, 'oncall', 'THEATRE', "==", 1) for day in range(7)),
        *((day, shift, 'THEATRE', "==", 1)
          for day in (SATURDAY, SUNDAY) for shift in ('am', 'pm')),
        *((day, shift, 'THEATRE', ">=", 1) for day in range(5) for shift in ('am', 'pm'))
    ]

    def apply_constraint(self):
        cdctx = CoreDuties.from_context(self.ctx)
        for day in self.ctx.core_config.days:
            for (weekday, shift, dutytype, op, requirement) in self.cover_requirements:
                if day.weekday() == weekday:
                    oper = {
                        "==": operator.eq,
                        ">=": operator.ge,
                        "<=": operator.le,
                        ">": operator.gt,
                        "<": operator.lt
                    }[op]
                    self.model.Add(oper(sum(cdctx.allocated_for_duty(shift, day, staff, dutytype)
                                            for staff in self.core_config.staff), requirement))
