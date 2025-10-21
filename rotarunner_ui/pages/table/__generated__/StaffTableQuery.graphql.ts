/**
 * @generated SignedSource<<2ede6cc75c3c31cadbb48ae966180c3a>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ConcreteRequest } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type StaffTableQuery$variables = {
  end: string;
  start: string;
};
export type StaffTableQuery$data = {
  readonly content: {
    readonly __id: string;
    readonly edges: ReadonlyArray<{
      readonly node: {
        readonly activityStart: string;
        readonly id: string;
        readonly timeslots: ReadonlyArray<{
          readonly assignments: ReadonlyArray<{
            readonly id: string;
            readonly staff: {
              readonly id: string;
            };
          }>;
          readonly id: string;
          readonly start: string;
          readonly " $fragmentSpreads": FragmentRefs<"StaffTableTimeslotFragment">;
        }>;
        readonly " $fragmentSpreads": FragmentRefs<"StaffTableActivityFragment">;
      };
    }>;
  };
  readonly daterange: {
    readonly end: string;
    readonly start: string;
  };
  readonly rows: ReadonlyArray<{
    readonly id: string;
    readonly name: string;
  }>;
};
export type StaffTableQuery = {
  response: StaffTableQuery$data;
  variables: StaffTableQuery$variables;
};

const node: ConcreteRequest = (function(){
var v0 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "end"
},
v1 = {
  "defaultValue": null,
  "kind": "LocalArgument",
  "name": "start"
},
v2 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "start",
  "storageKey": null
},
v3 = {
  "alias": null,
  "args": null,
  "concreteType": "DateRange",
  "kind": "LinkedField",
  "name": "daterange",
  "plural": false,
  "selections": [
    (v2/*: any*/),
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "end",
      "storageKey": null
    }
  ],
  "storageKey": null
},
v4 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v5 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v6 = [
  (v4/*: any*/),
  (v5/*: any*/)
],
v7 = {
  "alias": "rows",
  "args": null,
  "concreteType": "Staff",
  "kind": "LinkedField",
  "name": "staff",
  "plural": true,
  "selections": (v6/*: any*/),
  "storageKey": null
},
v8 = [
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
v9 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "activityStart",
  "storageKey": null
},
v10 = {
  "kind": "ClientExtension",
  "selections": [
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "__id",
      "storageKey": null
    }
  ]
};
return {
  "fragment": {
    "argumentDefinitions": [
      (v0/*: any*/),
      (v1/*: any*/)
    ],
    "kind": "Fragment",
    "metadata": null,
    "name": "StaffTableQuery",
    "selections": [
      (v3/*: any*/),
      (v7/*: any*/),
      {
        "alias": "content",
        "args": (v8/*: any*/),
        "concreteType": "ActivityConnection",
        "kind": "LinkedField",
        "name": "activities",
        "plural": false,
        "selections": [
          {
            "alias": null,
            "args": null,
            "concreteType": "ActivityEdge",
            "kind": "LinkedField",
            "name": "edges",
            "plural": true,
            "selections": [
              {
                "alias": null,
                "args": null,
                "concreteType": "Activity",
                "kind": "LinkedField",
                "name": "node",
                "plural": false,
                "selections": [
                  {
                    "args": null,
                    "kind": "FragmentSpread",
                    "name": "StaffTableActivityFragment"
                  },
                  (v4/*: any*/),
                  (v9/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "TimeSlot",
                    "kind": "LinkedField",
                    "name": "timeslots",
                    "plural": true,
                    "selections": [
                      {
                        "args": null,
                        "kind": "FragmentSpread",
                        "name": "StaffTableTimeslotFragment"
                      },
                      (v2/*: any*/),
                      (v4/*: any*/),
                      {
                        "alias": null,
                        "args": null,
                        "concreteType": "StaffAssignment",
                        "kind": "LinkedField",
                        "name": "assignments",
                        "plural": true,
                        "selections": [
                          (v4/*: any*/),
                          {
                            "alias": null,
                            "args": null,
                            "concreteType": "Staff",
                            "kind": "LinkedField",
                            "name": "staff",
                            "plural": false,
                            "selections": [
                              (v4/*: any*/)
                            ],
                            "storageKey": null
                          }
                        ],
                        "storageKey": null
                      }
                    ],
                    "storageKey": null
                  }
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          },
          (v10/*: any*/)
        ],
        "storageKey": null
      }
    ],
    "type": "Query",
    "abstractKey": null
  },
  "kind": "Request",
  "operation": {
    "argumentDefinitions": [
      (v1/*: any*/),
      (v0/*: any*/)
    ],
    "kind": "Operation",
    "name": "StaffTableQuery",
    "selections": [
      (v3/*: any*/),
      (v7/*: any*/),
      {
        "alias": "content",
        "args": (v8/*: any*/),
        "concreteType": "ActivityConnection",
        "kind": "LinkedField",
        "name": "activities",
        "plural": false,
        "selections": [
          {
            "alias": null,
            "args": null,
            "concreteType": "ActivityEdge",
            "kind": "LinkedField",
            "name": "edges",
            "plural": true,
            "selections": [
              {
                "alias": null,
                "args": null,
                "concreteType": "Activity",
                "kind": "LinkedField",
                "name": "node",
                "plural": false,
                "selections": [
                  (v4/*: any*/),
                  (v5/*: any*/),
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "Location",
                    "kind": "LinkedField",
                    "name": "location",
                    "plural": false,
                    "selections": (v6/*: any*/),
                    "storageKey": null
                  },
                  {
                    "alias": null,
                    "args": null,
                    "concreteType": "TimeSlot",
                    "kind": "LinkedField",
                    "name": "timeslots",
                    "plural": true,
                    "selections": [
                      (v4/*: any*/),
                      (v2/*: any*/),
                      {
                        "alias": null,
                        "args": null,
                        "kind": "ScalarField",
                        "name": "finish",
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
                          (v4/*: any*/),
                          {
                            "alias": null,
                            "args": null,
                            "concreteType": "Staff",
                            "kind": "LinkedField",
                            "name": "staff",
                            "plural": false,
                            "selections": (v6/*: any*/),
                            "storageKey": null
                          }
                        ],
                        "storageKey": null
                      }
                    ],
                    "storageKey": null
                  },
                  (v9/*: any*/)
                ],
                "storageKey": null
              }
            ],
            "storageKey": null
          },
          (v10/*: any*/)
        ],
        "storageKey": null
      }
    ]
  },
  "params": {
    "cacheID": "75093fc6414b979cc663984b10bc2307",
    "id": null,
    "metadata": {},
    "name": "StaffTableQuery",
    "operationKind": "query",
    "text": "query StaffTableQuery(\n  $start: String!\n  $end: String!\n) {\n  daterange {\n    start\n    end\n  }\n  rows: staff {\n    id\n    name\n  }\n  content: activities(startDate: $start, endDate: $end) {\n    edges {\n      node {\n        ...StaffTableActivityFragment\n        id\n        activityStart\n        timeslots {\n          ...StaffTableTimeslotFragment\n          start\n          id\n          assignments {\n            id\n            staff {\n              id\n            }\n          }\n        }\n      }\n    }\n  }\n}\n\nfragment StaffTableActivityFragment on Activity {\n  id\n  name\n  location {\n    id\n    name\n  }\n  timeslots {\n    ...StaffTableTimeslotFragment\n    start\n    finish\n    assignments {\n      staff {\n        id\n        name\n      }\n      id\n    }\n    id\n  }\n}\n\nfragment StaffTableTimeslotFragment on TimeSlot {\n  id\n  start\n  finish\n  assignments {\n    id\n    staff {\n      id\n      name\n    }\n  }\n}\n"
  }
};
})();

(node as any).hash = "e188f3a3f28cf63cf74151a7abdd429a";

export default node;
