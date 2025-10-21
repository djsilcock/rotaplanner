/**
 * @generated SignedSource<<e134a14cec0876682bd7d3f6a7efe117>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type StaffTableTimeslotFragment$data = {
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
  readonly " $fragmentType": "StaffTableTimeslotFragment";
};
export type StaffTableTimeslotFragment$key = {
  readonly " $data"?: StaffTableTimeslotFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"StaffTableTimeslotFragment">;
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
  "name": "StaffTableTimeslotFragment",
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
  "type": "TimeSlot",
  "abstractKey": null
};
})();

(node as any).hash = "b8c1fb347b40a38f4a6c2dc0c13f3fed";

export default node;
