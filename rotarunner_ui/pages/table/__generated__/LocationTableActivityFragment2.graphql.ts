/**
 * @generated SignedSource<<b2e00d70073e3bd0a61e9bac9fcb8cc4>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type LocationTableActivityFragment2$data = {
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
  readonly " $fragmentType": "LocationTableActivityFragment2";
};
export type LocationTableActivityFragment2$key = {
  readonly " $data"?: LocationTableActivityFragment2$data;
  readonly " $fragmentSpreads": FragmentRefs<"LocationTableActivityFragment2">;
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
  "name": "LocationTableActivityFragment2",
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

(node as any).hash = "0190b803ccbe431b5b68ece54c43e1f8";

export default node;
