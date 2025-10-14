/**
 * @generated SignedSource<<6565addb4b62a17e3d8a2c616b1f1b58>>
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
  }>;
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
      "concreteType": "TimeSlot",
      "kind": "LinkedField",
      "name": "timeslots",
      "plural": true,
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

(node as any).hash = "5a447ad77af141cdc5886813a764cecd";

export default node;
