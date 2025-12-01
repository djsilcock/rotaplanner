/**
 * @generated SignedSource<<4a74aad9d800630488ce15c64215c73f>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type editActivityActivityQuery$variables = {
  id: string;
};
export type editActivityActivityQuery$data = {
  readonly activityTags: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
  readonly locations: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
  readonly node: {
    readonly activityFinish?: string;
    readonly activityStart?: string;
    readonly id?: string;
    readonly location?: {
      readonly id: string;
      readonly name: string;
    } | null | undefined;
    readonly name?: string;
    readonly tags?: ReadonlyArray<{
      readonly id: string;
      readonly name: string;
    }>;
    readonly timeslots?: ReadonlyArray<{
      readonly assignments: ReadonlyArray<{
        readonly staff: {
          readonly id: string;
          readonly name: string;
        };
      }>;
      readonly finish: string;
      readonly start: string;
    }>;
  };
};
export type editActivityActivityQuery = {
  response: editActivityActivityQuery$data;
  variables: editActivityActivityQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "id"
  }
],
v1 = [
  {
    "kind": "Variable",
    "name": "id",
    "variableName": "id"
  }
],
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "activityStart",
  "storageKey": null
},
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "activityFinish",
  "storageKey": null
},
v6 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "start",
  "storageKey": null
},
v7 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "finish",
  "storageKey": null
},
v8 = [
  (v3/*: any*/),
  (v2/*: any*/)
],
v9 = {
  "alias": null,
  "args": null,
  "concreteType": "Staff",
  "kind": "LinkedField",
  "name": "staff",
  "plural": false,
  "selections": (v8/*: any*/),
  "storageKey": null
},
v10 = {
  "alias": null,
  "args": null,
  "concreteType": "Location",
  "kind": "LinkedField",
  "name": "location",
  "plural": false,
  "selections": (v8/*: any*/),
  "storageKey": null
},
v11 = {
  "alias": null,
  "args": null,
  "concreteType": "ActivityTag",
  "kind": "LinkedField",
  "name": "tags",
  "plural": true,
  "selections": (v8/*: any*/),
  "storageKey": null
},
v12 = {
  "alias": null,
  "args": null,
  "concreteType": "ActivityTag",
  "kind": "LinkedField",
  "name": "activityTags",
  "plural": true,
  "selections": (v8/*: any*/),
  "storageKey": null
},
v13 = {
  "alias": null,
  "args": null,
  "concreteType": "Location",
  "kind": "LinkedField",
  "name": "locations",
  "plural": true,
  "selections": (v8/*: any*/),
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "editActivityActivityQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "node",
        "plural": false,
        "selections": [
          {
            "kind": "InlineFragment",
            "selections": [
              (v2/*: any*/),
              (v3/*: any*/),
              (v4/*: any*/),
              (v5/*: any*/),
              {
                "alias": null,
                "args": null,
                "concreteType": "TimeSlot",
                "kind": "LinkedField",
                "name": "timeslots",
                "plural": true,
                "selections": [
                  (v6/*: any*/),
                  (v7/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "StaffAssignment",
                    "kind": "LinkedField",
                    "name": "assignments",
                    "plural": true,
                    "selections": [
                      (v9/*: any*/)
                    ],
                    "storageKey": null
                  }
                ],
                "storageKey": null
              },
              (v10/*: any*/),
              (v11/*: any*/)
            ],
            "type": "Activity",
            "abstractKey": null
          }
        ],
        "storageKey": null
      },
      (v12/*: any*/),
      (v13/*: any*/)
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "editActivityActivityQuery",
    "selections": [
      {
        "alias": null,
        "args": (v1/*: any*/),
        "concreteType": null,
        "kind": "LinkedField",
        "name": "node",
        "plural": false,
        "selections": [
          {
            "alias": null,
            "args": null,
            "kind": "ScalarField",
            "name": "__typename",
            "storageKey": null
          },
          (v3/*: any*/),
          {
            "kind": "InlineFragment",
            "selections": [
              (v2/*: any*/),
              (v4/*: any*/),
              (v5/*: any*/),
              {
                "alias": null,
                "args": null,
                "concreteType": "TimeSlot",
                "kind": "LinkedField",
                "name": "timeslots",
                "plural": true,
                "selections": [
                  (v6/*: any*/),
                  (v7/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "StaffAssignment",
                    "kind": "LinkedField",
                    "name": "assignments",
                    "plural": true,
                    "selections": [
                      (v9/*: any*/),
                      (v3/*: any*/)
                    ],
                    "storageKey": null
                  },
                  (v3/*: any*/)
                ],
                "storageKey": null
              },
              (v10/*: any*/),
              (v11/*: any*/)
            ],
            "type": "Activity",
            "abstractKey": null
          }
        ],
        "storageKey": null
      },
      (v12/*: any*/),
      (v13/*: any*/)
    ]
  },
  "params": {
    "cacheID": "790c3b8fca47d97d0bfdc2439d5015d6",
    "id": null,
    "metadata": {},
    "name": "editActivityActivityQuery",
    "operationKind": "query",
    "text": "query editActivityActivityQuery(\n  $id: ID!\n) {\n  node(id: $id) {\n    __typename\n    ... on Activity {\n      name\n      id\n      activityStart\n      activityFinish\n      timeslots {\n        start\n        finish\n        assignments {\n          staff {\n            id\n            name\n          }\n          id\n        }\n        id\n      }\n      location {\n        id\n        name\n      }\n      tags {\n        id\n        name\n      }\n    }\n    id\n  }\n  activityTags {\n    id\n    name\n  }\n  locations {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "7c63a587ea14cb8d730aeac8de4049ef";

export default node;
