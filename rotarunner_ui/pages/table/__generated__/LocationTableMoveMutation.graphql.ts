/**
 * @generated SignedSource<<f081d91ffc5ec9a9df308d1ffa5a96fb>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type ActivityInput = {
  id?: string | null | undefined;
  locationId?: string | null | undefined;
  name?: string | null | undefined;
  recurrenceRules?: RecurrenceGroup | null | undefined;
  requirements?: ReadonlyArray<RequirementInput> | null | undefined;
  templateId?: string | null | undefined;
  timeslots?: ReadonlyArray<TimeSlotInput> | null | undefined;
};
export type RecurrenceGroup = {
  allOf: ReadonlyArray<RecurrenceRule>;
  anyOf: ReadonlyArray<RecurrenceRule>;
  noneOf: ReadonlyArray<RecurrenceRule>;
};
export type RecurrenceRule = {
  daily?: DailyRecurrenceInput | null | undefined;
  group?: RecurrenceGroup | null | undefined;
  monthly?: MonthlyRecurrenceInput | null | undefined;
  weekInMonth?: WeekInMonthRecurrenceInput | null | undefined;
  weekly?: WeeklyRecurrenceInput | null | undefined;
};
export type DailyRecurrenceInput = {
  interval: number;
};
export type WeeklyRecurrenceInput = {
  interval: number;
  weekday: number;
};
export type MonthlyRecurrenceInput = {
  dayInMonth: number;
  interval: number;
};
export type WeekInMonthRecurrenceInput = {
  interval: number;
  weekNo: number;
  weekday: number;
};
export type RequirementInput = {
  attendance: number;
  maximum: number;
  minimum: number;
  requirementId: string;
};
export type TimeSlotInput = {
  activityId: string;
  startTime: string;
};
export type LocationTableMoveMutation$variables = {
  activity: ActivityInput;
};
export type LocationTableMoveMutation$data = {
  readonly editActivity: {
    readonly id: string;
    readonly " $fragmentSpreads": FragmentRefs<"tableActivityFragment">;
  } | null | undefined;
};
export type LocationTableMoveMutation = {
  response: LocationTableMoveMutation$data;
  variables: LocationTableMoveMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "activity"
  }
],
v1 = [
  {
    "kind": "Variable",
    "name": "activity",
    "variableName": "activity"
  }
],
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "LocationTableMoveMutation",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "editActivity",
        "plural": false,
        "selections": [
          (v2/*: any*/),
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "tableActivityFragment"
          }
        ],
        "storageKey": null
      }
    ],
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "LocationTableMoveMutation",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "editActivity",
        "plural": false,
        "selections": [
          (v2/*: any*/),
          (v3/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "activityStart",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "activityFinish",
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "concreteType": "Location",
            "kind": "LinkedField",
            "name": "location",
            "plural": false,
            "selections": [
              (v2/*: any*/)
            ],
            "storageKey": null
          },
          {
            "alias": null,
            "args": null,
            "concreteType": "StaffAssignment",
            "kind": "LinkedField",
            "name": "assignments",
            "plural": true,
            "selections": [
              {
                "alias": null,
                "args": null,
                "concreteType": "TimeSlot",
                "kind": "LinkedField",
                "name": "timeslot",
                "plural": false,
                "selections": [
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "start",
                    "storageKey": null
                  },
                  {
                    "alias": null,
                    "args": null,
                    "kind": "ScalarField",
                    "name": "finish",
                    "storageKey": null
                  },
                  (v2/*: any*/)
                ],
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "concreteType": "Staff",
                "kind": "LinkedField",
                "name": "staff",
                "plural": false,
                "selections": [
                  (v2/*: any*/),
                  (v3/*: any*/)
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "f5721fa8f0cd99f0835a3a7bb713f871",
    "id": null,
    "metadata": {},
    "name": "LocationTableMoveMutation",
    "operationKind": "mutation",
    "text": "mutation LocationTableMoveMutation(\n  $activity: ActivityInput!\n) {\n  editActivity(activity: $activity) {\n    id\n    ...tableActivityFragment\n  }\n}\n\nfragment tableActivityFragment on Activity {\n  id\n  name\n  activityStart\n  activityFinish\n  location {\n    id\n  }\n  assignments {\n    timeslot {\n      start\n      finish\n      id\n    }\n    staff {\n      id\n      name\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "a34c7d972161d7f807921cc0e3f8b742";

export default node;
