/**
 * @generated SignedSource<<48300d4a573ec224733c731bfd6d637d>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableConfigQuery$variables = Record<PropertyKey, never>;
export type tableConfigQuery$data = {
  readonly allLocations: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
  readonly allStaff: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
  readonly daterange: {
    readonly end: string;
    readonly start: string;
  };
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
    "name": "allStaff",
    "plural": true,
    "selections": (v0/*: any*/),
    "storageKey": null
  },
  {
    "alias": null,
    "args": null,
    "concreteType": "Location",
    "kind": "LinkedField",
    "name": "allLocations",
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
    "cacheID": "df115b2a44417976d1a98f7cb62e42b6",
    "id": null,
    "metadata": {},
    "name": "tableConfigQuery",
    "operationKind": "query",
    "text": "query tableConfigQuery {\n  allStaff {\n    id\n    name\n  }\n  allLocations {\n    id\n    name\n  }\n  daterange {\n    start\n    end\n  }\n}\n"
  }
};
})();

(node as any).hash = "7db50767e574539ca56cefa31fc70137";

export default node;
