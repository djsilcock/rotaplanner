/**
 * @generated SignedSource<<8e97ebfb8b545b88e42d7fccc54e81c6>>
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
  readonly content: ReadonlyArray<{
    readonly activityStart: string;
    readonly id: string;
    readonly location: {
      readonly id: string;
    } | null | undefined;
    readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment">;
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
  (v4/*: any*/),
  (v5/*: any*/)
],
v7 = {
  "alias": "rows",
  "args": null,
  "concreteType": "Location",
  "kind": "LinkedField",
  "name": "locations",
  "plural": true,
  "selections": (v6/*: any*/),
  "storageKey": null
},
v8 = [
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
v9 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "activityStart",
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
    "name": "LocationTableQuery",
    "selections": [
      (v3/*: any*/),
      (v7/*: any*/),
      {
        "alias": "content",
        "args": (v8/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
        "selections": [
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "LocationTableActivityFragment"
          },
          (v9/*: any*/),
          (v4/*: any*/),
          {
            "alias": null,
            "args": null,
            "concreteType": "Location",
            "kind": "LinkedField",
            "name": "location",
            "plural": false,
            "selections": [
              (v4/*: any*/)
            ],
            "storageKey": null
          }
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
    "name": "LocationTableQuery",
    "selections": [
      (v3/*: any*/),
      (v7/*: any*/),
      {
        "alias": "content",
        "args": (v8/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
        "selections": [
          (v4/*: any*/),
          (v9/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "activityFinish",
            "storageKey": null
          },
          (v5/*: any*/),
          {
            "alias": null,
            "args": null,
            "concreteType": "Location",
            "kind": "LinkedField",
            "name": "location",
            "plural": false,
            "selections": (v6/*: any*/),
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
                    "selections": (v6/*: any*/),
                    "storageKey": null
                  },
                  (v4/*: any*/)
                ],
                "storageKey": null
              },
              (v4/*: any*/)
            ],
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "ee5b0495b7c3ea13381e051bbe1925f6",
    "id": null,
    "metadata": {},
    "name": "LocationTableQuery",
    "operationKind": "query",
    "text": "query LocationTableQuery(\n  $start: String!\n  $end: String!\n) {\n  daterange {\n    start\n    end\n  }\n  rows: locations {\n    id\n    name\n  }\n  content: activities(startDate: $start, endDate: $end) {\n    ...LocationTableActivityFragment\n    activityStart\n    id\n    location {\n      id\n    }\n  }\n}\n\nfragment LocationTableActivityFragment on Activity {\n  id\n  activityStart\n  activityFinish\n  name\n  location {\n    id\n    name\n  }\n  timeslots {\n    start\n    finish\n    assignments {\n      staff {\n        id\n        name\n      }\n      id\n    }\n    id\n  }\n}\n"
  }
};
})();

(node as any).hash = "251043b10a8534721271e7ac0c9e9356";

export default node;
