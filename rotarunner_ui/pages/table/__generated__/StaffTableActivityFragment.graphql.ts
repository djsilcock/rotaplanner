/**
 * @generated SignedSource<<91df5902dbc49b1f4cc02cf4a30baed8>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type StaffTableActivityFragment$data = {
  readonly id: string;
  readonly location: {
    readonly id: string;
    readonly name: string;
  } | null | undefined;
  readonly name: string;
  readonly timeslots: ReadonlyArray<{
    readonly assignments: ReadonlyArray<{
      readonly staff: {
        readonly id: string;
        readonly name: string;
      };
    }>;
    readonly finish: string;
    readonly start: string;
    readonly " $fragmentSpreads": FragmentRefs<"StaffTableTimeslotFragment">;
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
        {
          "args": null,
          "kind": "FragmentSpread",
          "name": "StaffTableTimeslotFragment"
        },
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

(node as any).hash = "f19abb7417538f3481bcfea1fe847a8c";

export default node;
