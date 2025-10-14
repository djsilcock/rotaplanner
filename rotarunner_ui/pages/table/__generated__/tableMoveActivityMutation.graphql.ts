/**
 * @generated SignedSource<<2d1e0e709936ea222c16829147f484eb>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type RowType = "location" | "staff" | "%future added value";
export type tableMoveActivityMutation$variables = {
  activityId: string;
  fromRow: string;
  rowType: RowType;
  toRow: string;
};
export type tableMoveActivityMutation$data = {
  readonly moveActivity: {
    readonly " $fragmentSpreads": FragmentRefs<"tableActivityFragment">;
  } | null | undefined;
};
export type tableMoveActivityMutation = {
  response: tableMoveActivityMutation$data;
  variables: tableMoveActivityMutation$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "activityId"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "fromRow"
},
v2 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "rowType"
},
v3 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "toRow"
},
v4 = [
  {
    "kind": "Variable",
    "name": "activityId",
    "variableName": "activityId"
  },
  {
    "kind": "Variable",
    "name": "fromRow",
    "variableName": "fromRow"
  },
  {
    "kind": "Variable",
    "name": "rowType",
    "variableName": "rowType"
  },
  {
    "kind": "Variable",
    "name": "toRow",
    "variableName": "toRow"
  }
],
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v6 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v2/*: any*/),
      (v3/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "tableMoveActivityMutation",
    "selections": [
      {
        "alias": null,
        "args": (v4/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "moveActivity",
        "plural": false,
        "selections": [
          {
            "args": null,
            "kind": "FragmentSpread",
            "name": "tableActivityFragment"
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
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/),
      (v3/*: any*/),
      (v2/*: any*/)
    ],
    "kind": "Operation",
    "name": "tableMoveActivityMutation",
    "selections": [
      {
        "alias": null,
        "args": (v4/*: any*/),
        "concreteType": "Activity",
        "kind": "LinkedField",
        "name": "moveActivity",
        "plural": false,
        "selections": [
          (v5/*: any*/),
          (v6/*: any*/),
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
            "concreteType": "Location",
            "kind": "LinkedField",
            "name": "location",
            "plural": false,
            "selections": [
              (v5/*: any*/)
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
                  (v5/*: any*/)
                ],
                "storageKey": null
              },
              {
                "alias": null,
                "args": null,
                "concreteType": "Staff",
                "kind": "LinkedField",
                "name": "staff",
                "plural": false,
                "selections": [
                  (v5/*: any*/),
                  (v6/*: any*/)
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          }
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "a74d420cbd4a602b10dfe391b08774f6",
    "id": null,
    "metadata": {},
    "name": "tableMoveActivityMutation",
    "operationKind": "mutation",
    "text": "mutation tableMoveActivityMutation(\n  $activityId: String!\n  $fromRow: String!\n  $toRow: String!\n  $rowType: RowType!\n) {\n  moveActivity(activityId: $activityId, fromRow: $fromRow, toRow: $toRow, rowType: $rowType) {\n    ...tableActivityFragment\n    id\n  }\n}\n\nfragment tableActivityFragment on Activity {\n  id\n  name\n  activityStart\n  activityFinish\n  location {\n    id\n  }\n  assignments {\n    timeslot {\n      start\n      finish\n      id\n    }\n    staff {\n      id\n      name\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "7526f00d2f0bcaccabb3505f4ce69be3";

export default node;
