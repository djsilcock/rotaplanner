from sqlalchemy import select
from base import BaseConstraint
from constraints.constraint_store import register_constraint
from database import Base,Duty,Shift,Location,Staff
from datetime import timedelta

@register_constraint('config_ctx')
class ConfigureContext(BaseConstraint):
    async def apply_constraint(self):
        async with self.ctx.condition:
            db_session=self.ctx.get_db_session()
            with db_session.begin() as session:
                enddate=session.scalars(
                    select(Duty).order_by(Duty.date.desc())
                    .limit(1)).one().date
                self.ctx.shifts={shift.name for shift in session.scalars(select(Shift))}
                self.ctx.staff={staff.name for staff in session.scalars(select(Staff))}
                self.ctx.locations={location.name for location in session.scalars(select(Location))}
            
            rota_length=max(0,(enddate-self.ctx.startdate).days)
            def days(*filters):
                """returns iterator of days"""
                date_iter = (self.ctx.startdate+timedelta(days=daydelta)
                            for daydelta in range(rota_length))

                def filterfunc(d):
                    return all(f(d) for f in filters)
                return filter(filterfunc, date_iter)
            self.ctx.days=days
            self.ctx.condition.notify_all()
            