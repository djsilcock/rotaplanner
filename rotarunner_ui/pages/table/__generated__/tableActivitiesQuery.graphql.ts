/**
 * @generated SignedSource<<2f5e8e2163d3b1e0ce319bdf764ceef0>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableActivitiesQuery$variables = {
  end: string;
  start: string;
};
export type tableActivitiesQuery$data = {
  readonly activities: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
    readonly timeslots: ReadonlyArray<{
      readonly finish: string;
      readonly staffAssigned: ReadonlyArray<{
        readonly staff: {
          readonly id: string;
          readonly name: string;
        };
      }>;
      readonly start: string;
    }>;
  }>;
};
export type tableActivitiesQuery = {
  response: tableActivitiesQuery$data;
  variables: tableActivitiesQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "end"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "start"
  }
],
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v3 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "endDate",
        "variableName": "end"
      },
      {
        "kind": "Variable",
        "name": "startDate",
        "variableName": "start"
      }
    ],
    "concreteType": "Activity",
    "kind": "LinkedField",
    "name": "activities",
    "plural": true,
    "selections": [
      (v1/*: any*/),
      (v2/*: any*/),
      {
        "alias": null,
        "args": null,
        "concreteType": "TimeSlot",
        "kind": "LinkedField",
        "name": "timeslots",
        "plural": true,
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
          {
            "alias": null,
            "args": null,
            "concreteType": "StaffAssignment",
            "kind": "LinkedField",
            "name": "staffAssigned",
            "plural": true,
            "selections": [
              {
                "alias": null,
                "args": null,
                "concreteType": "Staff",
                "kind": "LinkedField",
                "name": "staff",
                "plural": false,
                "selections": [
                  (v1/*: any*/),
                  (v2/*: any*/)
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          }
        ],
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
    "name": "tableActivitiesQuery",
    "selections": (v3/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "tableActivitiesQuery",
    "selections": (v3/*: any*/)
  },
  "params": {
    "cacheID": "b393d8320e2786efd6ac6ab81d7d3637",
    "id": null,
    "metadata": {},
    "name": "tableActivitiesQuery",
    "operationKind": "query",
    "text": "query tableActivitiesQuery(\n  $end: String!\n  $start: String!\n) {\n  activities(endDate: $end, startDate: $start) {\n    id\n    name\n    timeslots {\n      start\n      finish\n      staffAssigned {\n        staff {\n          id\n          name\n        }\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "31cfcc5444eb95784e472491930375fb";

export default node;
