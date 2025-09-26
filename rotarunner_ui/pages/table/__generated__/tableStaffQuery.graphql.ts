/**
 * @generated SignedSource<<18faf774a573cc02361c298432f2b740>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableStaffQuery$variables = Record<PropertyKey, never>;
export type tableStaffQuery$data = {
  readonly allStaff: ReadonlyArray<{
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
    "name": "allStaff",
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
    "cacheID": "c6cdb5e9e2c45e6771261e5016fd9e90",
    "id": null,
    "metadata": {},
    "name": "tableStaffQuery",
    "operationKind": "query",
    "text": "query tableStaffQuery {\n  allStaff {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "e67b1352bf6b6ac2bed8515c833f6e2f";

export default node;
