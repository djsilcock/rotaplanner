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
}
export interface Activity {
  id: string;
  name: string;
  location: string | null;
  activity_start: string;
  activity_finish: string;
  roles?: Role[];
  requirements?: string[];
}
export interface Role {
  id: number;
  name: string;
  assignments?: StaffAssignment[];
  requirements?: string[];
}
export interface StaffAssignment {
  id?: number | null;
  staff: Staff;
  availability_type?: string;
  attendance?: number;
  flags?: string[];
}
export interface UpdateLocationRequest {
  draggedId: string;
  droptargetId: string;
  initialDropzoneId: string;
}
export interface UpdateStaffRequest {
  draggedId: string;
  droptargetId: string;
  initialDropzoneId: string;
  ctrlKey: boolean;
}

export interface TableApi 
  {
    available_for_timeslot(query_args: AvailableForTimeslotQuery): Promise<AvailableForTimeslotResult[]>;
    data(): Promise<TableDataResult>;
    open_activity_editor(activity_id: string): Promise<any>;
    update_location(payload: UpdateLocationRequest): Promise<TableDataResult>;
    update_staff(payload: UpdateStaffRequest): Promise<TableDataResult>;
  }