/**
 * @generated SignedSource<<6fffa3d1e3a417f3981df82fb30a37d4>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableActivityFragment3$data = {
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
  } | null | undefined;
  readonly name: string;
  readonly " $fragmentType": "LocationTableActivityFragment3";
};
export type LocationTableActivityFragment3$key = {
  readonly " $data"?: LocationTableActivityFragment3$data;
  readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment3">;
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
};
return {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "LocationTableActivityFragment3",
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
      "kind": "ScalarField",
      "name": "activityFinish",
      "storageKey": null
    },
    {
      "alias": null,
      "args": null,
      "concreteType": "Location",
      "kind": "LinkedField",
      "name": "location",
      "plural": false,
      "selections": [
        (v0/*: any*/)
      ],
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
        },
        {
          "alias": null,
          "args": null,
          "concreteType": "Staff",
          "kind": "LinkedField",
          "name": "staff",
          "plural": false,
          "selections": [
            (v0/*: any*/),
            (v1/*: any*/)
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

(node as any).hash = "3af9c95984270796bddcb92966900f88";

export default node;
