type LocationTableActivityFragmentLocation = {
    _id: string
    name: string
}

type LocationTableActivityFragmentAssignmentsStaff = {
    _id: string
    name: string
}

type LocationTableActivityFragmentAssignmentsTimeslot = {
    start: string
    finish: string
}

type LocationTableActivityFragmentAssignments = {
    staff: LocationTableActivityFragmentAssignmentsStaff
    timeslot: LocationTableActivityFragmentAssignmentsTimeslot
}

type LocationTableActivityFragment = {
    _id: string
    activity_start: string
    activity_finish: string
    name: string
    location: LocationTableActivityFragmentLocation | undefined
    assignments: LocationTableActivityFragmentAssignments[]
}

type LocationTableQueryResultDaterange = {
    start: string
    end: string
}

type LocationTableQueryResultLocations = {
    _id: string
    name: string
}

type LocationTableQueryResultActivitiesEdges = {
    node: LocationTableActivityFragment
}

type LocationTableQueryResultActivities = {
    edges: LocationTableQueryResultActivitiesEdges[]
}

type LocationTableQueryResult = {
    daterange: LocationTableQueryResultDaterange
    // alias for locations
    rows: LocationTableQueryResultLocations[]
    // alias for activities
    content: LocationTableQueryResultActivities
}

type LocationTableQueryVariables = {
    start: string
    end: string
}