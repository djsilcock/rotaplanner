from datetime import date
from enum import IntFlag, auto
import pytest
import sqlalchemy
from sqlalchemy.orm import Session,sessionmaker as sqla_sessmaker

from database import Location, Shift, Staff,Base,Duty,Flag,get_tallies_from_db


@pytest.fixture
def db():
    engine=sqlalchemy.create_engine('sqlite://',echo=True,future=True)
    Base.metadata.create_all(engine)
    sm=sqla_sessmaker(engine)
    with sm.begin() as session:
        session.add(Staff(name="Fred"))
        session.add(Staff(name="Barney"))
        session.add(Flag(name='is_locum'))
        session.add(Flag(name='confirmed'))
        session.add(Shift(name='am'))
        session.add(Shift(name='pm'))
        session.add(Shift(name='eve'))
        session.add(Location(name='icu'))
        session.add(Location(name='th'))
        
    return engine

@pytest.fixture
def sessionmaker(db):
    return sqla_sessmaker(db)

@pytest.fixture
def session(sessionmaker):
    with sessionmaker.begin() as sess:
        yield sess

def test_staff(session):
    staff={s.name:s for s in session.scalars(sqlalchemy.select(Staff))}
    shifts={s.name:s for s in session.scalars(sqlalchemy.select(Shift))}
    locations={l.name:l for l in session.scalars(sqlalchemy.select(Location))}
    flags={f.name:f for f in session.scalars(sqlalchemy.select(Flag))}
    fred=staff['Fred']
    am=shifts['am']
    pm=shifts['pm']
    eve=shifts['eve']
    icu=locations['icu']
    flag1=flags['is_locum']
    flag2=flags['confirmed']

    fred.duties=[
        duty1:=Duty(date=date.today(),shift=am,location=icu),
        duty2:=Duty(date=date.today(),shift=pm,location=icu),
        duty3:=Duty(date=date.today(),shift=eve,location=icu),
        
    ]
    duty1.flags.append(flag1)
    duty2.flags.append(flag2)
    duty3.flags.append(flag1)
    #session.commit()
    wilma=session.scalar(sqlalchemy.select(Staff).where(Staff.name=='Wilma'))
    assert wilma is None
    duties=session.scalars(sqlalchemy.select(Duty).where(Duty.flags.contains(flag1))).all()
    assert len(duties)==2

def test_upsert_duty(session):
    s = Staff(name="Joe Bloggs")
    session.add(s)

    shifts={s.name:s for s in session.scalars(sqlalchemy.select(Shift))}
    locations={l.name:l for l in session.scalars(sqlalchemy.select(Location))}
    pm=shifts['pm']
    icu=locations['icu']
    th=locations['th']
    
    d = Duty(
        date=date.today(),
        shift=pm,
        location=icu,
        staff=s
        )
    d2=Duty(
        date=date.today(),
        shift=pm,
        location=th,
        staff=s
        )
    d.save(session)
    d2.save(session)
    assert len(s.duties)==1

def test_tallies(session):
    staff={s.name:s for s in session.scalars(sqlalchemy.select(Staff))}
    shifts={s.name:s for s in session.scalars(sqlalchemy.select(Shift))}
    locations={l.name:l for l in session.scalars(sqlalchemy.select(Location))}
    flags={f.name:f for f in session.scalars(sqlalchemy.select(Flag))}
    d=Duty(
            date=date.today(),
            shift=shifts['pm'],
            location=locations['icu'],
            staff=staff['Fred']
        )
    d.save(session)
    d2=Duty(
        date=date.today(),
        shift=shifts['pm'],
        location=locations['icu'],
        staff=staff['Fred']
    )
    d2.save(session)
    for inst in session.scalars(sqlalchemy.select(Duty)):
        print (inst)
    d3=Duty(
        date=date.today(),
        shift=shifts['am'],
        location=locations['icu'],
        staff=staff['Fred']
    )
    d3.save(session)
    d4=Duty(
        date=date.today(),
        shift=shifts['eve'],
        location=locations['icu'],
        staff=staff['Fred']
    )
    d4.save(session)

    print(get_tallies_from_db(session,date(2024,12,31)))