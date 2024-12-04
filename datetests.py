import dateutil
import datetime

import dateutil.rrule

today = datetime.datetime.today().replace(microsecond=0, hour=0, minute=0, second=0)

print(
    datetime.datetime(2024, 12, 27)
    in dateutil.rrule.rrule(
        dateutil.rrule.MONTHLY,
        byweekday=(dateutil.rrule.TH, dateutil.rrule.FR),
        bysetpos=-1,
        byhour=0,
        byminute=0,
        bysecond=0,
    )
)
