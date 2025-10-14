/**
 * @generated SignedSource<<5ecc776c6a1cd3c8425b393cefe6719e>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableStaffQuery$variables = Record<PropertyKey, never>;
export type tableStaffQuery$data = {
  readonly staff: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type tableStaffQuery = {
  response: tableStaffQuery$data;
  variables: tableStaffQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "Staff",
    "kind": "LinkedField",
    "name": "staff",
    "plural": true,
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
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "tableStaffQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "tableStaffQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "30f48efce3ee647397cd2302b48a26ad",
    "id": null,
    "metadata": {},
    "name": "tableStaffQuery",
    "operationKind": "query",
    "text": "query tableStaffQuery {\n  staff {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "81eaf58293aace2e73f6bc287e3ff7ac";

export default node;
