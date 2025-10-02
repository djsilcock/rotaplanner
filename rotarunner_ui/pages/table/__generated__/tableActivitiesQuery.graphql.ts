/**
 * @generated SignedSource<<22b8ae9d0b544fc09ebce2059cfca545>>
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
    readonly activityFinish: string;
    readonly activityStart: string;
    readonly assignments: ReadonlyArray<{
      readonly staff: {
        readonly id: string;
      };
    }>;
    readonly id: string;
    readonly name: string;
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
v2 = [
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
      {
        "alias": null,
        "args": null,
        "kind": "ScalarField",
        "name": "name",
        "storageKey": null
      },
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
            "selections": [
              (v1/*: any*/)
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
    "selections": (v2/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "tableActivitiesQuery",
    "selections": (v2/*: any*/)
  },
  "params": {
    "cacheID": "cca04d425f46aee9c0793707b5a55dbd",
    "id": null,
    "metadata": {},
    "name": "tableActivitiesQuery",
    "operationKind": "query",
    "text": "query tableActivitiesQuery(\n  $end: String!\n  $start: String!\n) {\n  activities(endDate: $end, startDate: $start) {\n    id\n    name\n    activityStart\n    activityFinish\n    assignments {\n      staff {\n        id\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "e6018c66f7fd50081dc9f06891fa6de5";

export default node;
