"general utility functions for rotaplanner"

import dataclasses
from rotaplanner.database import Connection


@dataclasses.dataclass
class Location:
    id: str
    name: str


class Staff:
    id: str
    name: str


def get_locations(connection: Connection) -> dict[str, Location]:
    sql_query = """
    SELECT id, name
    FROM locations
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Location(id=str(row[0]), name=row[1]) for row in result}


def get_staff(connection: Connection) -> dict[str, Staff]:
    sql_query = """
    SELECT id, name
    FROM staff
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Staff(id=str(row[0]), name=row[1]) for row in result}
