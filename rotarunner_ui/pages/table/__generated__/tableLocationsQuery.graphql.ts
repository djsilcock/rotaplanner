/**
 * @generated SignedSource<<e0286038d061a0b902c4babb1f69055a>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableLocationsQuery$variables = Record<PropertyKey, never>;
export type tableLocationsQuery$data = {
  readonly allLocations: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type tableLocationsQuery = {
  response: tableLocationsQuery$data;
  variables: tableLocationsQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "Location",
    "kind": "LinkedField",
    "name": "allLocations",
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
    "name": "tableLocationsQuery",
    "selections": (v0/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "tableLocationsQuery",
    "selections": (v0/*: any*/)
  },
  "params": {
    "cacheID": "9b9e5bff5b52d32b2bb6e007acb4d027",
    "id": null,
    "metadata": {},
    "name": "tableLocationsQuery",
    "operationKind": "query",
    "text": "query tableLocationsQuery {\n  allLocations {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "061c6a256ceda60fed531b8d35373180";

export default node;
