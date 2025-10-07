/**
 * @generated SignedSource<<47f8d0cacde4efecbcfb6de34ee59871>>
 * @lightSyntaxTransform
 * @nogrep
 */

/* tslint:disable */
/* eslint-disable */
// @ts-nocheck

import { ReaderFragment } from 'relay-runtime';
import { FragmentRefs } from "relay-runtime";
export type tableRowSortingFragment$data = {
  readonly activityStart: string;
  readonly assignments: ReadonlyArray<{
    readonly staff: {
      readonly id: string;
    };
  }>;
  readonly id: string;
  readonly location: {
    readonly id: string;
  } | null | undefined;
  readonly " $fragmentSpreads": FragmentRefs<"tableActivityFragment">;
  readonly " $fragmentType": "tableRowSortingFragment";
};
export type tableRowSortingFragment$key = {
  readonly " $data"?: tableRowSortingFragment$data;
  readonly " $fragmentSpreads": FragmentRefs<"tableRowSortingFragment">;
};

const node: ReaderFragment = (function(){
var v0 = {
  "alias": null,
  "args": null,
  "kind": "ScalarField",
  "name": "id",
  "storageKey": null
},
v1 = [
  (v0/*: any*/)
];
return {
  "argumentDefinitions": [],
  "kind": "Fragment",
  "metadata": null,
  "name": "tableRowSortingFragment",
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
      "concreteType": "Location",
      "kind": "LinkedField",
      "name": "location",
      "plural": false,
      "selections": (v1/*: any*/),
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
          "selections": (v1/*: any*/),
          "storageKey": null
        }
      ],
      "storageKey": null
    },
    {
      "args": null,
      "kind": "FragmentSpread",
      "name": "tableActivityFragment"
    }
  ],
  "type": "Activity",
  "abstractKey": null
};
})();

(node as any).hash = "fb7b5b742d8845e36cbd873cc32032d2";

export default node;
