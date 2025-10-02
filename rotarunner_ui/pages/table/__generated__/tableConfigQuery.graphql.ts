/**
 * @generated SignedSource<<7a1e272b4c9544699b110bec29eba327>>
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
    "alias": "staff",
    "args": null,
    "concreteType": "Staff",
    "kind": "LinkedField",
    "name": "allStaff",
    "plural": true,
    "selections": (v0/*: any*/),
    "storageKey": null
  },
  {
    "alias": "locations",
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
    "cacheID": "f0f4df8b3de86f383d081682f592e6c4",
    "id": null,
    "metadata": {},
    "name": "tableConfigQuery",
    "operationKind": "query",
    "text": "query tableConfigQuery {\n  staff: allStaff {\n    id\n    name\n  }\n  locations: allLocations {\n    id\n    name\n  }\n  daterange {\n    start\n    end\n  }\n}\n"
  }
};
})();

(node as any).hash = "7504b9137fa9fe4a1ceaef5b2e2b9def";

export default node;
