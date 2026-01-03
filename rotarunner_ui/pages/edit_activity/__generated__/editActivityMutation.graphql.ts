/**
 * @generated SignedSource<<959d1a6190b4f3814dfc4d53284795c5>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
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
export type editActivityMutation$variables = {
  input: ActivityInput;
};
export type editActivityMutation$data = {
  readonly editActivity: {
    readonly id: string;
    readonly name: string;
  } | null | undefined;
};
export type editActivityMutation = {
  response: editActivityMutation$data;
  variables: editActivityMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "input"
  }
],
v1 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "activity",
        "variableName": "input"
      }
    ],
    "concreteType": "Activity",
    "kind": "LinkedField",
    "name": "editActivity",
    "plural": false,
    "selections": [
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "id",
        "storageKey": null
      },
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "name",
        "storageKey": null
      }
    ],
    "storageKey": null
  }
];
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "editActivityMutation",
    "selections": (v1/*: any*/),
    "type": "Mutation",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "editActivityMutation",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "cb224b6bddb09e348f6bb4ff8d88c2cd",
    "id": null,
    "metadata": {},
    "name": "editActivityMutation",
    "operationKind": "mutation",
    "text": "mutation editActivityMutation(\n  $input: ActivityInput!\n) {\n  editActivity(activity: $input) {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "1ac820b05b3acab7aa96dc8ed720cb32";

export default node;
