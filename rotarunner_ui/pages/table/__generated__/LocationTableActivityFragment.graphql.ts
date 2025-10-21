/**
 * @generated SignedSource<<ca23026aa8f79343c7491b63a3008f77>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableActivityFragment$data = {
  readonly activityFinish: string;
  readonly activityStart: string;
  readonly assignments: ReadonlyArray<{
    readonly staff: {
      readonly id: string;
      readonly name: string;
    };
    readonly timeslot: {
      readonly finish: string;
      readonly start: string;
    };
  }>;
  readonly id: string;
  readonly location: {
    readonly id: string;
    readonly name: string;
  } | null | undefined;
  readonly name: string;
  readonly " $fragmentType": "LocationTableActivityFragment";
};
export type LocationTableActivityFragment$key = {
  readonly " $data"?: LocationTableActivityFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment">;
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
  "name": "LocationTableActivityFragment",
  "selections": [
    (v0/*: any*/),
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
      "kind": "ScalarField",
      "name": "activityFinish",
      "storageKey": null
    },
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
        },
        {
          "alias": null,
          "args": null,
          "concreteType": "TimeSlot",
          "kind": "LinkedField",
          "name": "timeslot",
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
              "name": "finish",
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

(node as any).hash = "6b83e460b56cf33c15fddbfffcc3cebe";

export default node;
