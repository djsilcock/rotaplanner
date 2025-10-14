/**
 * @generated SignedSource<<a56360562ff685cc64b6e84db869ca9e>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableLocationsQuery$variables = Record<PropertyKey, never>;
export type tableLocationsQuery$data = {
  readonly locations: ReadonlyArray<{
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
    "name": "locations",
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
    "cacheID": "01002bc6aa86411fcfa7d6dabdcf983c",
    "id": null,
    "metadata": {},
    "name": "tableLocationsQuery",
    "operationKind": "query",
    "text": "query tableLocationsQuery {\n  locations {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "1fc5f983e2982929cf508e68562d5f28";

export default node;
