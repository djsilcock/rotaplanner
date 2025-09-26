/**
 * @generated SignedSource<<8f5e926ae449b8efb7a9614064846c27>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
export type tableActivitiesQuery$variables = {
  end: string;
  start: string;
};
export type tableActivitiesQuery$data = {
  readonly activities: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type tableActivitiesQuery = {
  response: tableActivitiesQuery$data;
  variables: tableActivitiesQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = [
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "end"
  },
  {
    "defaultValue": null,
    "kind": "LocalArgument",
    "name": "start"
  }
],
v1 = [
  {
    "alias": null,
    "args": [
      {
        "kind": "Variable",
        "name": "endDate",
        "variableName": "end"
      },
      {
        "kind": "Variable",
        "name": "startDate",
        "variableName": "start"
      }
    ],
    "concreteType": "Activity",
    "kind": "LinkedField",
    "name": "activities",
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
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Fragment",
    "metadata": null,
    "name": "tableActivitiesQuery",
    "selections": (v1/*: any*/),
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": (v0/*: any*/),
    "kind": "Operation",
    "name": "tableActivitiesQuery",
    "selections": (v1/*: any*/)
  },
  "params": {
    "cacheID": "976cd42de3394ccc8d55092efaa85349",
    "id": null,
    "metadata": {},
    "name": "tableActivitiesQuery",
    "operationKind": "query",
    "text": "query tableActivitiesQuery(\n  $end: String!\n  $start: String!\n) {\n  activities(endDate: $end, startDate: $start) {\n    id\n    name\n  }\n}\n"
  }
};
})();

(node as any).hash = "da013236b75ca5393f56f727147bad17";

export default node;
