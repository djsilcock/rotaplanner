/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface AvailableForTimeslotQuery {
  activity_id: string;
}
export interface AvailableForTimeslotResult {
  staff: Staff;
  availability_type: string;
  existing_activity?: string | null;
}
export interface Staff {
  id: string | null;
  name: string;
  [k: string]: unknown;
}
export interface TableDataResult {
  queryVersion?: string;
  dateRange: DateRange;
  staff: string[];
  locations: string[];
  staffData: {
    [k: string]: Staff;
  };
  locationsData: {
    [k: string]: Location;
  };
  activities: Activity[];
}
export interface DateRange {
  start: string;
  end: string;
  [k: string]: unknown;
}
export interface Location {
  id: string | null;
  name: string;
  [k: string]: unknown;
}
export interface Activity {
  id: string;
  name: string;
  location: string | null;
  activity_start: string;
  activity_finish: string;
  assignments?: StaffAssignment[];
  [k: string]: unknown;
}
export interface StaffAssignment {
  id: number;
  staff: string;
  [k: string]: unknown;
}
export interface UpdateLocationRequest {
  draggedId: string;
  droptargetId: string;
  initialDropzoneId: string;
}

export interface PyWebviewApi {
  table: {
    available_for_timeslot(
      query_args: AvailableForTimeslotQuery,
    ): Promise<AvailableForTimeslotResult[]>;
    data(): Promise<TableDataResult>;
    update_location(payload: UpdateLocationRequest): Promise<TableDataResult>;
    update_staff(payload: any): Promise<TableDataResult>;
  };
}
