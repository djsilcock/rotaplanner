/**
 * @generated SignedSource<<afe1e52bd00c59546f3900f7a4834731>>
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
  readonly timeslots: ReadonlyArray<{
    readonly finish: string;
    readonly staffAssigned: ReadonlyArray<{
      readonly staff: {
        readonly id: string;
        readonly name: string;
      };
    }>;
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
};
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
          "name": "staffAssigned",
          "plural": true,
          "selections": [
            {
              "alias": null,
              "args": null,
              "concreteType": "Staff",
              "kind": "LinkedField",
              "name": "staff",
              "plural": false,
              "selections": [
                (v0/*: any*/),
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

(node as any).hash = "252e0ace6406c5cf5e0460ca4e7e06ba";

export default node;
