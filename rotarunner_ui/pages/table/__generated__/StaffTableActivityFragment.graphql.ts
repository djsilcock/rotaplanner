/**
 * @generated SignedSource<<eca1a1c6f3e42505e24aa2b1ae8db2ef>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type StaffTableActivityFragment$data = {
  readonly activityStart: string;
  readonly id: string;
  readonly location: {
    readonly id: string;
    readonly name: string;
  } | null | undefined;
  readonly name: string;
  readonly timeslots: ReadonlyArray<{
    readonly assignments: ReadonlyArray<{
      readonly id: string;
      readonly staff: {
        readonly id: string;
        readonly name: string;
      };
    }>;
    readonly finish: string;
    readonly id: string;
    readonly start: string;
  }>;
  readonly " $fragmentType": "StaffTableActivityFragment";
};
export type StaffTableActivityFragment$key = {
  readonly " $data"?: StaffTableActivityFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"StaffTableActivityFragment">;
};

const node: ReaderFragment = (function(){
var v0 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v1 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "name",
  "storageKey": null
},
v2 = [
  (v0/*: any*/),
  (v1/*: any*/)
];
return {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "StaffTableActivityFragment",
  "selections": [
    (v0/*: any*/),
    (v1/*: any*/),
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "activityStart",
      "storageKey": null
    },
    {
      "alias": null,
      "args": null,
      "concreteType": "Location",
      "kind": "LinkedField",
      "name": "location",
      "plural": false,
      "selections": (v2/*: any*/),
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
        (v0/*: any*/),
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
            (v0/*: any*/),
            {
              "alias": null,
              "args": null,
              "concreteType": "Staff",
              "kind": "LinkedField",
              "name": "staff",
              "plural": false,
              "selections": (v2/*: any*/),
              "storageKey": null
            }
          ],
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "Activity",
  "abstractKey": null
};
})();

(node as any).hash = "5bec40985b71696e1298505e1dae6dc8";

export default node;
