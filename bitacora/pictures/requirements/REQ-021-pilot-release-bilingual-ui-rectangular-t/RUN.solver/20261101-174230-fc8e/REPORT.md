# Solver 20261101-174230-fc8e: REQ-021 r39, SP-5 x SP-4 reconcile

**Trigger:** two reconcile resolutions (D-297): `.evidence/REQ-021/CG-4.integration.json` and `scripts/test/test-composicion-planes.ts`, both modify/delete (ours `-`, theirs = SP-4's edit of the virtual base's file).

**Origin:** SP-5's accumulated line (9263e355f) lacks both files and the `planes:test-composicion` npm script. An ancestry walk shows historical composer merges dropped them (`compose REQ-021.bt-r25 SP-4@v1`, `...r26 SP-4@v1`, `bt: T93 starts from SP-5's line`); no SP-5 task deletes them. The five criss-cross merge bases include snapshots that still hold them, so the virtual base resurrects them and git reports modify/delete.

**Fix:** both `.resolved` files hold SP-4's current content (`git cat-file -p 3b5fbb0bd...` and `b707c5f69...`, byte-identical). The selector the test uses (`data-account-row`) already exists in SP-5's `ListaCuentas.tsx`; `package.json` merges by key. No metodologia code changed, nothing integrated, no ref moved, no product commit.

**Rule:** D-088 in pictures' DECISIONS.md. Proposal: automate this case in `bt_verification_tree._settled`.

**Not done / watch:** the next engine pass may open further rounds for the other predecessors (CG-9 stays `RECONCILE_PENDING` until all lines fold); they come to this inbox.
