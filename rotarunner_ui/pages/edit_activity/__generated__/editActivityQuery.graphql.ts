/**
 * @generated SignedSource<<bc3ae87fdda7d375bba1d04799bc7641>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type editActivityQuery$variables = {
  id: string;
};
export type editActivityQuery$data = {
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
    } | null | undefined;
    readonly name?: string;
    readonly requirements?: any;
    readonly tags?: ReadonlyArray<{
      readonly id: string;
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
export type editActivityQuery = {
  response: editActivityQuery$data;
  variables: editActivityQuery$variables;
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
  "name": "requirements",
  "storageKey": null
},
v7 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "start",
  "storageKey": null
},
v8 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "finish",
  "storageKey": null
},
v9 = [
  (v3/*: any*/),
  (v2/*: any*/)
],
v10 = {
  "alias": null,
  "args": null,
  "concreteType": "Staff",
  "kind": "LinkedField",
  "name": "staff",
  "plural": false,
  "selections": (v9/*: any*/),
  "storageKey": null
},
v11 = [
  (v3/*: any*/)
],
v12 = {
  "alias": null,
  "args": null,
  "concreteType": "Location",
  "kind": "LinkedField",
  "name": "location",
  "plural": false,
  "selections": (v11/*: any*/),
  "storageKey": null
},
v13 = {
  "alias": null,
  "args": null,
  "concreteType": "ActivityTag",
  "kind": "LinkedField",
  "name": "tags",
  "plural": true,
  "selections": (v11/*: any*/),
  "storageKey": null
},
v14 = {
  "alias": null,
  "args": null,
  "concreteType": "ActivityTag",
  "kind": "LinkedField",
  "name": "activityTags",
  "plural": true,
  "selections": (v9/*: any*/),
  "storageKey": null
},
v15 = {
  "alias": null,
  "args": null,
  "concreteType": "Location",
  "kind": "LinkedField",
  "name": "locations",
  "plural": true,
  "selections": (v9/*: any*/),
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "editActivityQuery",
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
              (v6/*: any*/),
              {
                "alias": null,
                "args": null,
                "concreteType": "TimeSlot",
                "kind": "LinkedField",
                "name": "timeslots",
                "plural": true,
                "selections": [
                  (v7/*: any*/),
                  (v8/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "StaffAssignment",
                    "kind": "LinkedField",
                    "name": "assignments",
                    "plural": true,
                    "selections": [
                      (v10/*: any*/)
                    ],
                    "storageKey": null
                  }
                ],
                "storageKey": null
              },
              (v12/*: any*/),
              (v13/*: any*/)
            ],
            "type": "Activity",
            "abstractKey": null
          }
        ],
        "storageKey": null
      },
      (v14/*: any*/),
      (v15/*: any*/)
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "editActivityQuery",
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
              (v6/*: any*/),
              {
                "alias": null,
                "args": null,
                "concreteType": "TimeSlot",
                "kind": "LinkedField",
                "name": "timeslots",
                "plural": true,
                "selections": [
                  (v7/*: any*/),
                  (v8/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "StaffAssignment",
                    "kind": "LinkedField",
                    "name": "assignments",
                    "plural": true,
                    "selections": [
                      (v10/*: any*/),
                      (v3/*: any*/)
                    ],
                    "storageKey": null
                  },
                  (v3/*: any*/)
                ],
                "storageKey": null
              },
              (v12/*: any*/),
              (v13/*: any*/)
            ],
            "type": "Activity",
            "abstractKey": null
          }
        ],
        "storageKey": null
      },
      (v14/*: any*/),
      (v15/*: any*/)
    ]
  },
  "params": {
    "cacheID": "2f7d94ccf8650dda8ffcca5979380b99",
    "id": null,
    "metadata": {},
    "name": "editActivityQuery",
    "operationKind": "query",
    "text": "query editActivityQuery(\n  $id: ID!\n) {\n  node(id: $id) {\n    __typename\n    ... on Activity {\n      name\n      id\n      activityStart\n      activityFinish\n      requirements\n      timeslots {\n        start\n        finish\n        assignments {\n          staff {\n            id\n            name\n          }\n          id\n        }\n        id\n      }\n      location {\n        id\n      }\n      tags {\n        id\n      }\n    }\n    id\n  }\n  activityTags {\n    id\n    name\n  }\n  locations {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "60b8cbd3d9aa283135073939154319df";

export default node;
