/**
 * @generated SignedSource<<ce98ebc3c31e56a604e2657363f4d268>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type tableActivitiesQuery$variables = {
  end: string;
  start: string;
};
export type tableActivitiesQuery$data = {
  readonly activities: ReadonlyArray<{
    readonly " $fragmentSpreads": FragmentRefs<"tableRowSortingFragment">;
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
v1 = [
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
    "name": "tableActivitiesQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
        "selections": [
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "tableRowSortingFragment"
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
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "tableActivitiesQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "activities",
        "plural": true,
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
                "concreteType": "Staff",
                "kind": "LinkedField",
                "name": "staff",
                "plural": false,
                "selections": [
                  (v2/*: any*/),
                  (v3/*: any*/)
                ],
                "storageKey": null
              },
              (v2/*: any*/),
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
              }
            ],
            "storageKey": null
          },
          (v3/*: any*/),
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "activityFinish",
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "4ad813ed318937431b60ee4047ae947e",
    "id": null,
    "metadata": {},
    "name": "tableActivitiesQuery",
    "operationKind": "query",
    "text": "query tableActivitiesQuery(\n  $end: String!\n  $start: String!\n) {\n  activities(endDate: $end, startDate: $start) {\n    ...tableRowSortingFragment\n    id\n  }\n}\n\nfragment tableActivityFragment on Activity {\n  id\n  name\n  activityStart\n  activityFinish\n  location {\n    id\n  }\n  assignments {\n    timeslot {\n      start\n      finish\n      id\n    }\n    staff {\n      id\n      name\n    }\n    id\n  }\n}\n\nfragment tableRowSortingFragment on Activity {\n  id\n  activityStart\n  location {\n    id\n  }\n  assignments {\n    staff {\n      id\n    }\n    id\n  }\n  ...tableActivityFragment\n}\n"
  }
};
})();

(node as any).hash = "62f455ca7b313aab488d227a4364a523";

export default node;
