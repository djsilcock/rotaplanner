/**
 * @generated SignedSource<<8e61e23d8c1b22c30ffe2d7b7e0fbf4d>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type ActivityInput = {
  activityDate?: string | null | undefined;
  activityStart?: string | null | undefined;
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
export type StaffTableMoveMutation$variables = {
  activity: ActivityInput;
};
export type StaffTableMoveMutation$data = {
  readonly editActivity: {
    readonly id: string;
    readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment">;
  } | null | undefined;
};
export type StaffTableMoveMutation = {
  response: StaffTableMoveMutation$data;
  variables: StaffTableMoveMutation$variables;
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
},
v4 = [
  (v2/*: any*/),
  (v3/*: any*/)
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "StaffTableMoveMutation",
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
            "name": "LocationTableActivityFragment"
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
    "name": "StaffTableMoveMutation",
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
          (v3/*: any*/),
          {
            "alias": null,
            "args": null,
            "concreteType": "Location",
            "kind": "LinkedField",
            "name": "location",
            "plural": false,
            "selections": (v4/*: any*/),
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
                "concreteType": "Staff",
                "kind": "LinkedField",
                "name": "staff",
                "plural": false,
                "selections": (v4/*: any*/),
                "storageKey": null
              },
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
              (v2/*: any*/)
            ],
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "23468a9a71a5078e6ad05781151ec507",
    "id": null,
    "metadata": {},
    "name": "StaffTableMoveMutation",
    "operationKind": "mutation",
    "text": "mutation StaffTableMoveMutation(\n  $activity: ActivityInput!\n) {\n  editActivity(activity: $activity) {\n    id\n    ...LocationTableActivityFragment\n  }\n}\n\nfragment LocationTableActivityFragment on Activity {\n  id\n  activityStart\n  activityFinish\n  name\n  location {\n    id\n    name\n  }\n  assignments {\n    staff {\n      id\n      name\n    }\n    timeslot {\n      start\n      finish\n      id\n    }\n    id\n  }\n}\n"
  }
};
})();

(node as any).hash = "1496065cab48758cf158c21a5784d2a6";

export default node;
