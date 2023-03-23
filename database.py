"Database utils"
from contextlib import contextmanager
from typing import List, TYPE_CHECKING
import datetime

import sqlalchemy
from sqlalchemy import Column,Table,select
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import relationship,Session,sessionmaker

from context import db_session

def get_sessionmaker():
    engine=sqlalchemy.create_engine('sqlite://')
    return sessionmaker(engine)

class Base(DeclarativeBase):
    pass

if TYPE_CHECKING:
    from constraints.base import BaseConstraint


class Flag(Base):
    __tablename__='flags'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]

class Location(Base):
    __tablename__='locations'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]
    duties: Mapped[list['Duty']]=relationship(back_populates='location')

class Shift(Base):
    __tablename__='shifts'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]

class Staff(Base):
    __tablename__ = 'staff'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    duties: Mapped[list['Duty']] = relationship(back_populates='staff')


duty_flag_assoc_table = Table(
    "dutyflag_assoc",
    Base.metadata,
    Column("duty_id", ForeignKey("duties.id")),
    Column("flag_id", ForeignKey("flags.id")),
)

class Duty(Base):
    __tablename__ = 'duties'
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime.date]
    shift_id: Mapped[int]=mapped_column(ForeignKey('shifts.id'))
    shift:Mapped[Shift]=relationship()
    location_id: Mapped[int]=mapped_column(ForeignKey('locations.id'))
    location: Mapped[Location]=relationship(back_populates="duties")
    staff_id: Mapped[int] = mapped_column(ForeignKey('staff.id'))
    staff: Mapped[Staff] = relationship(back_populates="duties")
    flags: Mapped[List[Flag]] = relationship(secondary=duty_flag_assoc_table)
    def save(self,session=None):
        if session is None:
            session=db_session.get()
        before_add_duty.send(session=session,duty=self)
        session.add(self)

def get_staff(session=None):
    "get all staff"
    if session is None:
        session=db_session.get()
    return session.scalars(select(Staff))

def get_locations(session=None):
    "get all locations"
    if session is None:
        session=db_session.get()
    return session.scalars(select(Location))

from blinker import signal

before_add_duty=signal('before_add_duty')
duty_is_changed=signal('duty_is_changed')


@before_add_duty.connect
def only_one_in_icu(sender,session,duty):
        for instance in session.scalars(select(Duty)
            .where(Duty.location==session.get(Location,'ICU'))
            .where(Duty.date==duty.date)
            .where(Duty.shift==duty.shift)):
            duty_is_changed.send(
                date=instance.date,
                shift=instance.shift,
                staff=instance.staff)
                
@before_add_duty.connect
def no_multitasking(sender,session,duty):
        for instance in session.scalars(select(Duty)
            .where(Duty.staff==duty.staff)
            .where(Duty.date==duty.date)
            .where(Duty.shift==duty.shift)):
            session.delete(instance)

def get_tallies_from_db(session,finishdate: datetime.date) -> dict[tuple[str, str], int]:
    tallies = {}
    duties=session.execute(
        select(Duty.date,Staff.name,Shift.name)
        .join(Duty.staff)
        .join(Duty.shift)
        .where(Duty.date<=finishdate))
    for (dutydate,staff,shift) in duties:
        print(dutydate,staff,shift)
        duty_weekday = dutydate.weekday()
        if shift == 'am':
            shift_type = 'wddt' if duty_weekday < 5 else 'wedt'
        elif shift == 'oncall':
            shift_type = 'wdoc' if duty_weekday < 4 else 'weoc'
        else:
            continue
        tallies[(staff, shift_type)] = tallies.get(
            (staff, shift_type), 0)+1
    return tallies



if __name__=='__main__':
    engine=sqlalchemy.create_engine('sqlite://',echo=True,future=True)
    Base.metadata.create_all(engine)
    sess=sessionmaker(engine,expire_on_commit=False)
    with sess.begin() as session:
        db_session.set(session)
        staff={'Fred':Staff(name='Fred')}
        shifts={k:Shift(name=k) for k in ('am','pm','oncall')}
        locations={k:Location(name=k) for k in ('icu','theatre')}
        session.add_all([*staff.values(),*shifts.values(),*locations.values()])
    with sess.begin() as session:
        db_session.set(session)
        #shifts={s.name:s for s in session.scalars(select(Shift))}
        #locations={l.name:l for l in session.scalars(select(Location))}
        #staff={s.name:s for s in session.scalars(select(Staff))}
        d=Duty(
            date=datetime.date.today(),
            shift=shifts['pm'],
            location=locations['icu'],
            staff=staff['Fred']
        )
        d.save()
        d2=Duty(
            date=datetime.date.today(),
            shift=shifts['pm'],
            location=locations['icu'],
            staff=staff['Fred']
        )
        d2.save()
        for inst in session.scalars(select(Duty)):
            print (inst)
        d3=Duty(
            date=datetime.date.today(),
            shift=shifts['am'],
            location=locations['icu'],
            staff=staff['Fred']
        )
        d3.save()
        d4=Duty(
            date=datetime.date.today(),
            shift=shifts['oncall'],
            location=locations['icu'],
            staff=staff['Fred']
        )
        d4.save()

    print(get_tallies_from_db(sess,datetime.date(2024,12,31)))
