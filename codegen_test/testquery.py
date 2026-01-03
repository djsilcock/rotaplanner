from typing import List, Optional

class LocationTableActivityFragmentLocation:
    _id: str
    name: str

class LocationTableActivityFragmentAssignmentsStaff:
    _id: str
    name: str

class LocationTableActivityFragmentAssignmentsTimeslot:
    start: str
    finish: str

class LocationTableActivityFragmentAssignments:
    staff: LocationTableActivityFragmentAssignmentsStaff
    timeslot: LocationTableActivityFragmentAssignmentsTimeslot

class LocationTableActivityFragment:
    # typename: Activity
    _id: str
    activity_start: str
    activity_finish: str
    name: str
    location: Optional[LocationTableActivityFragmentLocation]
    assignments: list[LocationTableActivityFragmentAssignments]

class LocationTableQueryResultDaterange:
    start: str
    end: str

class LocationTableQueryResultLocations:
    _id: str
    name: str

class LocationTableQueryResultActivitiesEdges:
    node: LocationTableActivityFragment

class LocationTableQueryResultActivities:
    edges: list[LocationTableQueryResultActivitiesEdges]

class LocationTableQueryResult:
    daterange: LocationTableQueryResultDaterange
    # alias for locations
    rows: list[LocationTableQueryResultLocations]
    # alias for activities
    content: LocationTableQueryResultActivities

class LocationTableQueryVariables:
    start: str
    end: str