from ast import For
from constraints.enforce_acceptable_deviation import AcceptableDeviationEntry
from database import Base, Location, Shift
from sqlalchemy import Column, Table
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Date
from sqlalchemy.orm import relationship,Mapped,mapped_column
from sqlalchemy.ext.hybrid import hybrid_property

def listproperty(propname,coerce=lambda x:x):
    def from_text(self):
        return [coerce(i) for i in getattr(self,propname).split()]
    def to_text(self,value):
        setattr(self,propname,' '.join(map(str,value)))
    return hybrid_property(from_text,to_text)

ade_location_assoc= Table(
    "ade_location_assoc",
    Base.metadata,
    Column("location_id", ForeignKey("locations.id")),
    Column("ade_id", ForeignKey("acceptable_duties.id")),
)
ade_location_assoc= Table(
    "ade_shifts_assoc",
    Base.metadata,
    Column("location_id", ForeignKey("locations.id")),
    Column("ade_id", ForeignKey("acceptable_duties.id")),
)
ade_avail_assoc= Table(
    "ade_avail_assoc",
    Base.metadata,
    Column("avail_id", ForeignKey("ade_availability.id")),
    Column("ade_id", ForeignKey("acceptable_duties.id")),
)
class ADE_Sessions(Base):
    __tablename__='ade_sessions'
    id:Mapped[int]=mapped_column(primary_key=True)
    ade_id:Mapped[int]=mapped_column(ForeignKey('acceptable_duties.id'))
    shift_id:Mapped[int]=mapped_column(ForeignKey('shifts.id'))
    shift:Mapped[Shift]=relationship()
    weekday:Mapped[int]

class ADE_Availability(Base):
    __tablename__='ade_availability'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]

class ADELocationAvailability(Base):
    ade_id:Mapped[int]=mapped_column(ForeignKey('acceptable_duties.id'))
    loc_id:Mapped[int]=mapped_column(ForeignKey('locations.id'))
    availability:Mapped[int]=mapped_column(ForeignKey('ade_availability.id'))


class AcceptableDutiesEntry(Base):
    __tablename__="acceptable_duties"
    id:Mapped[int]=mapped_column(primary_key=True)
    staff_id:Mapped[int]=mapped_column(ForeignKey('staff.id'))
    session_id:Mapped[int]=mapped_column(ForeignKey('shifts.id'))
    weekday:Mapped[int]
    location_id:Mapped[int]=mapped_column(ForeignKey('locations.id'))
    availability_basis_id:Mapped[int]=mapped_column(ForeignKey('ade_availability.id'))
    session:Mapped[Shift]=relationship()
    availability_basis:Mapped[ADE_Availability]=relationship()
    rotation_type=Column(String)
    weeks:Mapped[str]
    cycle = Column(Integer)
    startdate = Column(Date)
    enddate = Column(Date)