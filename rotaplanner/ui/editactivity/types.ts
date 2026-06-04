/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

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
export interface Staff {
  id: string | null;
  name: string;
}
export interface AvailableForTimeslotQuery {
  activity_id: string;
}
export interface AvailableForTimeslotResult {
  staff: Staff;
  availability_type: string[];
  existing_activity?: string | null;
}
export interface Location {
  id: string | null;
  name: string;
}

export interface EditActivityApi 
  {
    available_for_timeslot(query_args: AvailableForTimeslotQuery): Promise<AvailableForTimeslotResult[]>;
    get_activity(activity_id: string): Promise<Activity>;
    get_locations(): Promise<Location[]>;
    update_activity(payload: Activity): Promise<boolean>;
  }