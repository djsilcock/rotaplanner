/**
 * @generated SignedSource<<bc0702e842866e7e82e86c5299c9f36b>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableQuery$variables = {
  end: string;
  start: string;
};
export type LocationTableQuery$data = {
  readonly daterange: {
    readonly end: string;
    readonly start: string;
  };
  readonly rows: ReadonlyArray<{
    readonly activities: ReadonlyArray<{
      readonly activityStart: string;
      readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment">;
    }>;
    readonly id: string;
    readonly name: string;
  }>;
  readonly unallocated: ReadonlyArray<{
    readonly activityStart: string;
    readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment">;
  }>;
};
export type LocationTableQuery = {
  response: LocationTableQuery$data;
  variables: LocationTableQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "end"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "start"
},
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "start",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "concreteType": "DateRange",
  "kind": "LinkedField",
  "name": "daterange",
  "plural": false,
  "selections": [
    (v2/*: any*/),
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "end",
      "storageKey": null
    }
  ],
  "storageKey": null
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v6 = [
  {
    "kind": "Variable",
    "name": "end",
    "variableName": "end"
  },
  {
    "kind": "Variable",
    "name": "start",
    "variableName": "start"
  }
],
v7 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "activityStart",
  "storageKey": null
},
v8 = [
  {
    "args": null,
    "kind": "FragmentSpread",
    "name": "LocationTableActivityFragment"
  },
  (v7/*: any*/)
],
v9 = [
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
v10 = [
  (v4/*: any*/),
  (v7/*: any*/),
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
    "concreteType": "TimeSlot",
    "kind": "LinkedField",
    "name": "timeslots",
    "plural": true,
    "selections": [
      (v2/*: any*/),
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
              (v4/*: any*/),
              (v5/*: any*/)
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
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "LocationTableQuery",
    "selections": [
      (v3/*: any*/),
      {
        "alias": "rows",
        "args": null,
        "concreteType": "Location",
        "kind": "LinkedField",
        "name": "allLocations",
        "plural": true,
        "selections": [
          (v4/*: any*/),
          (v5/*: any*/),
          {
            "alias": null,
            "args": (v6/*: any*/),
            "concreteType": "Activity",
            "kind": "LinkedField",
            "name": "activities",
            "plural": true,
            "selections": (v8/*: any*/),
            "storageKey": null
          }
        ],
        "storageKey": null
      },
      {
        "alias": "unallocated",
        "args": (v9/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
        "selections": (v8/*: any*/),
        "storageKey": null
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "LocationTableQuery",
    "selections": [
      (v3/*: any*/),
      {
        "alias": "rows",
        "args": null,
        "concreteType": "Location",
        "kind": "LinkedField",
        "name": "allLocations",
        "plural": true,
        "selections": [
          (v4/*: any*/),
          (v5/*: any*/),
          {
            "alias": null,
            "args": (v6/*: any*/),
            "concreteType": "Activity",
            "kind": "LinkedField",
            "name": "activities",
            "plural": true,
            "selections": (v10/*: any*/),
            "storageKey": null
          }
        ],
        "storageKey": null
      },
      {
        "alias": "unallocated",
        "args": (v9/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
        "selections": (v10/*: any*/),
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "9d12c93bd1b2773098e931f1ffce03de",
    "id": null,
    "metadata": {},
    "name": "LocationTableQuery",
    "operationKind": "query",
    "text": "query LocationTableQuery(\n  $start: String!\n  $end: String!\n) {\n  daterange {\n    start\n    end\n  }\n  rows: allLocations {\n    id\n    name\n    activities(start: $start, end: $end) {\n      ...LocationTableActivityFragment\n      activityStart\n      id\n    }\n  }\n  unallocated: activities(startDate: $start, endDate: $end) {\n    ...LocationTableActivityFragment\n    activityStart\n    id\n  }\n}\n\nfragment LocationTableActivityFragment on Activity {\n  id\n  activityStart\n  activityFinish\n  timeslots {\n    start\n    finish\n    staffAssigned {\n      staff {\n        id\n        name\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "cf86ffbd104ce975e1118dd31b893c56";

export default node;
