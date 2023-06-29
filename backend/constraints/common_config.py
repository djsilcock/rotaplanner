"Config forms common to many constraints"

import datetime

from sanic_wtf import SanicForm
from wtforms import DateField,FormField,BooleanField,HiddenField,FieldList,ValidationError

constraint_store = {}

MIN_DATE=datetime.date(1,1,1)
MAX_DATE=datetime.date(9999,12,31)

class DateRangeForm(SanicForm):
    "form for range of dates"
    startdate=DateField('From')
    enddate=DateField('To')
    def validate(self,extra_validators=None):
        supervalidate=super().validate(extra_validators)
        if not supervalidate:
            return False
        if (self.data['startdate'] or MIN_DATE)>(self.data['enddate'] or MAX_DATE):
            self.form_errors.append('Start date cannot be later than end date')
            return False
        return True

class CommonConfig(SanicForm):
    "common config form"
    daterange=FormField(DateRangeForm)
    exclusions=FieldList(FormField(DateRangeForm,label=""),'Exclusions')
    def validate_exclusions(self,exclusion_field):
        "inline validator"
        global_start=self.data['daterange']['startdate'] or datetime.date(1,1,1)
        global_end=self.data['daterange']['enddate'] or datetime.date(9999,1,1)
        for item in exclusion_field.data:
            exc_start=item['startdate'] or global_start
            exc_end=item['enddate'] or global_end
            if any([
                exc_start<global_start,
                exc_start>global_end,
                exc_end>global_end,
                exc_end<global_start]):
                raise ValidationError('Exclusion must be contained within date range')
            if exc_start>exc_end:
                raise ValidationError('Start of an exclusion must not be later than end')
    enabled=BooleanField('Rule enabled')
    constraint_type=HiddenField()
    rule_id=HiddenField()

class BaseConfigForm(SanicForm):
    "config form"
    common=FormField(CommonConfig)
