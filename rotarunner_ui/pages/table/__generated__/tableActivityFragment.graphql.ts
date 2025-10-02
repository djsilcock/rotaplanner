/**
 * @generated SignedSource<<a8959c8bc51091d751e505305a1c5e1c>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type tableActivityFragment$data = {
  readonly activityFinish: string;
  readonly activityStart: string;
  readonly assignments: ReadonlyArray<{
    readonly staff: {
      readonly id: string;
    };
  }>;
  readonly id: string;
  readonly name: string;
  readonly " $fragmentType": "tableActivityFragment";
};
export type tableActivityFragment$key = {
  readonly " $data"?: tableActivityFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"tableActivityFragment">;
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
  "name": "tableActivityFragment",
  "selections": [
    (v0/*: any*/),
    {
      "alias": null,
      "args": null,
      "kind": "ScalarField",
      "name": "name",
      "storageKey": null
    },
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
          "selections": [
            (v0/*: any*/)
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

(node as any).hash = "5880ab8d71d9f46612863a050b2c9a12";

export default node;
