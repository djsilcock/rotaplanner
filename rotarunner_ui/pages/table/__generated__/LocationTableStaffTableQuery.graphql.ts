/**
 * @generated SignedSource<<53b32740970af6578402205ca512bcbc>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableStaffTableQuery$variables = {
  end: string;
  start: string;
};
export type LocationTableStaffTableQuery$data = {
  readonly assignments: ReadonlyArray<{
    readonly staff: {
      readonly id: string;
    };
    readonly timeslot: {
      readonly start: string;
    };
    readonly " $fragmentSpreads": FragmentRefs<"LocationTableAssignmentFragment">;
  }>;
  readonly daterange: {
    readonly end: string;
    readonly start: string;
  };
  readonly rows: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type LocationTableStaffTableQuery = {
  response: LocationTableStaffTableQuery$data;
  variables: LocationTableStaffTableQuery$variables;
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
v5 = [
  (v4/*: any*/),
  {
    "alias": null,
    "args": null,
    "kind": "ScalarField",
    "name": "name",
    "storageKey": null
  }
],
v6 = {
  "alias": "rows",
  "args": null,
  "concreteType": "Staff",
  "kind": "LinkedField",
  "name": "staff",
  "plural": true,
  "selections": (v5/*: any*/),
  "storageKey": null
},
v7 = [
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
v8 = {
  "alias": null,
  "args": null,
  "concreteType": "Staff",
  "kind": "LinkedField",
  "name": "staff",
  "plural": false,
  "selections": [
    (v4/*: any*/)
  ],
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "LocationTableStaffTableQuery",
    "selections": [
      (v3/*: any*/),
      (v6/*: any*/),
      {
        "alias": null,
        "args": (v7/*: any*/),
        "concreteType": "StaffAssignment",
        "kind": "LinkedField",
        "name": "assignments",
        "plural": true,
        "selections": [
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "LocationTableAssignmentFragment"
          },
          {
            "alias": null,
            "args": null,
            "concreteType": "TimeSlot",
            "kind": "LinkedField",
            "name": "timeslot",
            "plural": false,
            "selections": [
              (v2/*: any*/)
            ],
            "storageKey": null
          },
          (v8/*: any*/)
        ],
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
    "name": "LocationTableStaffTableQuery",
    "selections": [
      (v3/*: any*/),
      (v6/*: any*/),
      {
        "alias": null,
        "args": (v7/*: any*/),
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
                "concreteType": "Activity",
                "kind": "LinkedField",
                "name": "activity",
                "plural": false,
                "selections": (v5/*: any*/),
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
                    "selections": (v5/*: any*/),
                    "storageKey": null
                  }
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          },
          (v8/*: any*/)
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "fc27944486f55586f24cfe96ad209845",
    "id": null,
    "metadata": {},
    "name": "LocationTableStaffTableQuery",
    "operationKind": "query",
    "text": "query LocationTableStaffTableQuery(\n  $start: String!\n  $end: String!\n) {\n  daterange {\n    start\n    end\n  }\n  rows: staff {\n    id\n    name\n  }\n  assignments(start: $start, end: $end) {\n    ...LocationTableAssignmentFragment\n    timeslot {\n      start\n    }\n    staff {\n      id\n    }\n  }\n}\n\nfragment LocationTableAssignmentFragment on StaffAssignment {\n  timeslot {\n    start\n    finish\n    activity {\n      id\n      name\n    }\n    assignments {\n      staff {\n        id\n        name\n      }\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "8e6e48d4aca2ca51538d062a6237328c";

export default node;
