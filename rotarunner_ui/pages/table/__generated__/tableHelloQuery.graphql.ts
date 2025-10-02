/**
 * @generated SignedSource<<f5c10cf569eac0f76957605d342866f0>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { greeting as queryGreetingResolverType } from "../index.tsx";
// Type assertion validating that `queryGreetingResolverType` resolver is correctly implemented.
// A type error here indicates that the type signature of the resolver module is incorrect.
(queryGreetingResolverType satisfies () => string | null | undefined);
export type tableHelloQuery$variables = Record<PropertyKey, never>;
export type tableHelloQuery$data = {
  readonly greeting: string | null | undefined;
};
export type tableHelloQuery = {
  response: tableHelloQuery$data;
  variables: tableHelloQuery$variables;
};

import {greeting as queryGreetingResolver} from '../index';

const node: ConcreteRequest = {
  "fragment": {
    "argumentDefinitions": [],
    "kind": "Fragment",
    "metadata": null,
    "name": "tableHelloQuery",
    "selections": [
      {
        "kind": "ClientExtension",
        "selections": [
          {
            "alias": null,
            "args": null,
            "fragment": null,
            "kind": "RelayResolver",
            "name": "greeting",
            "resolverModule": queryGreetingResolver,
            "path": "greeting"
          }
        ]
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [],
    "kind": "Operation",
    "name": "tableHelloQuery",
    "selections": [
      {
        "kind": "ClientExtension",
        "selections": [
          {
            "name": "greeting",
            "args": null,
            "fragment": null,
            "kind": "RelayResolver",
            "storageKey": null,
            "isOutputType": true
          }
        ]
      }
    ]
  },
  "params": {
    "cacheID": "a64d3a2f71245d16fb0d07a46dbc4e6c",
    "id": null,
    "metadata": {},
    "name": "tableHelloQuery",
    "operationKind": "query",
    "text": null
  }
};

(node as any).hash = "65e6ab52ad75357549ca0d08dcc5aeb0";

export default node;
