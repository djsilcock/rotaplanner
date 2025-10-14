/**
 * @generated SignedSource<<304c0442e95838d421e8da9c051b3fbe>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableConfigQuery$variables = Record<PropertyKey, never>;
export type tableConfigQuery$data = {
  readonly daterange: {
    readonly end: string;
    readonly start: string;
  };
  readonly locations: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
  readonly staff: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type tableConfigQuery = {
  response: tableConfigQuery$data;
  variables: tableConfigQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
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
v1 = [
  {
    "alias": null,
    "args": null,
    "concreteType": "Staff",
    "kind": "LinkedField",
    "name": "staff",
    "plural": true,
    "selections": (v0/*: any*/),
    "storageKey": null
  },
  {
    "alias": null,
    "args": null,
    "concreteType": "Location",
    "kind": "LinkedField",
    "name": "locations",
    "plural": true,
    "selections": (v0/*: any*/),
    "storageKey": null
  },
  {
    "alias": null,
    "args": null,
    "concreteType": "DateRange",
    "kind": "LinkedField",
    "name": "daterange",
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
        "name": "end",
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
    "name": "tableConfigQuery",
    "selections": (v1/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "tableConfigQuery",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "967c91d86fc5f7edf463e200dd58236f",
    "id": null,
    "metadata": {},
    "name": "tableConfigQuery",
    "operationKind": "query",
    "text": "query tableConfigQuery {\n  staff {\n    id\n    name\n  }\n  locations {\n    id\n    name\n  }\n  daterange {\n    start\n    end\n  }\n}\n"
  }
};
})();

(node as any).hash = "5539abccba4ce93069c2bf53162b1e35";

export default node;
