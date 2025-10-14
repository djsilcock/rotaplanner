/**
 * @generated SignedSource<<84c4128997b7c94c8d22debcf897c181>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableAssignmentFragment$data = {
  readonly timeslot: {
    readonly activity: {
      readonly id: string;
      readonly name: string;
    };
    readonly assignments: ReadonlyArray<{
      readonly staff: {
        readonly id: string;
        readonly name: string;
      };
    }>;
    readonly finish: string;
    readonly start: string;
  };
  readonly " $fragmentType": "LocationTableAssignmentFragment";
};
export type LocationTableAssignmentFragment$key = {
  readonly " $data"?: LocationTableAssignmentFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"LocationTableAssignmentFragment">;
};

const node: ReaderFragment = (function(){
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
];
return {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "LocationTableAssignmentFragment",
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
        },
        {
          "alias": null,
          "args": null,
          "concreteType": "Activity",
          "kind": "LinkedField",
          "name": "activity",
          "plural": false,
          "selections": (v0/*: any*/),
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
              "selections": (v0/*: any*/),
              "storageKey": null
            }
          ],
          "storageKey": null
        }
      ],
      "storageKey": null
    }
  ],
  "type": "StaffAssignment",
  "abstractKey": null
};
})();

(node as any).hash = "1d50f954f384edc5c9acc1c5b39ff92d";

export default node;
