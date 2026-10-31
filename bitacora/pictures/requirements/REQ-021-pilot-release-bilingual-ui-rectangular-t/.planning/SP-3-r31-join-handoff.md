# SP-3 table drag — r31 frozen; Solver join handoff

## Authority and result

The owner/operator requested only a D-241 bounded SP-3 repair and authorized Planner freeze,with Solver-owned later join. The normal command succeeded and produced frozen revision31. New tasks:T3.91(implementation/regressions),T3.92(real-browser checkpoint);only preexisting-task delta:T3.15.after gainsT3.92 and retainsT3.13. Every inherited criterion/check/path,subplan definition,interface and composition gate is unchanged in r31. The real confirmation is by policy D-241,not a fabricated owner confirmation.

## Why the approved view is separate

The working draft also contains owner-requested but unapproved SP-2 and SP-14 UI/contract amendments. Freezing that full draft under D-241 correctly refused STAGE_REPAIR_UNBOUNDED. Planner preserved those three working files,temporarily used the exact prior approved view plus only SP-3 repair,passed normal check/freeze with every guard active,and restored both UI proposals in finally. All Designers were settled during the brief publication transaction. UI amendments were never approved or discarded.

## Join via the normal command

The Solver,not the Planner,owns the join. The current working draft intentionally still contains UI amendments;it cannot itself be treated as a bounded-repair-only launch view. Use the captured approved publication view under /home/david/.local/tmp/req021-sp3-bounded-drag-20e2/publication/:approved-PLAN.json,approved-PLAN.md,approved-SPEC.md.

1. Capture FRESH current PLAN.json/PLAN.md/SPEC.md into a new durable recovery location with hashes and a restoration journal. Do not blindly restore the older pending-* backups;the owner may have made later edits. Avoid a live Designer reading a transient publication view.
2. For the command duration,expose the verified approved-r31 view only. Confirm its approved-stage projection matches plan-revisions/PLAN.r31.json and preserves the actual D-241 SP-3 digest. Keep design/flow/manifest authority files intact.
3. Run the normal authorized Solver command:no force,no manual confirmation or policy edit.

```sh
python ~/.claude/skills/metodologia/scripts/bitacora.py --project pictures stage run REQ-021 --repair-evidence evidence/owner-rejected/SP-3-v3.md --by solver
```

4. Restore the FRESH working proposals in finally,keeping their exact objects/edges and latest genuine revision metadata. Preserve the approved relative ordering of the two NEW repair tasks:T3.91,T3.92 follow the original tasks in r31. The policy digest is order-sensitive;do not repin or manually confirm it.
5. Read actual run binding/state after join;do not infer execution success from a session exit. New SP-3 implementation/tests/audit still must execute.

## Preserved review work

SP-2:owner selectedC;cuentas-admin@v2 revision2 is ready,with72/72ARIA/interactions and552render4width audit PASS;exact owner visual/subplan approval still pending. SP-14:planes@v2 has3ready card directions,normal comparison PASS;owner choice/final contract/subplan approval pending. P209/P211 remain open. These UI drafts are not part of frozen r31 and must not be confirmed under bounded repair.

## Evidence

Working folder:/home/david/.local/tmp/req021-sp3-bounded-drag-20e2/. freeze-success-readback.json proves the exact frozen delta;publication/journal.json records safe restoration;publication/freeze.txt and check.txt contain actual normal exits0. Original full-draft refusal remains freeze.txt at the working-folder root. Product code/tests were not executed by Planner.

## Update after owner SP-2 confirmation

The owner subsequently confirmed the exact new SP-2 contract/subplan through the web. SP-2 is now confirmed;only SP-14 is pending design selection/final confirmation. The web explicitly waits for SP-14 before reapproving the cumulative UI stage. This newer owner confirmation MUST NOT be replaced with the older v1 confirmation. The captured r31 publication view remains a proof of the valid immutable frozen repair,not authority to roll back current flow/design decisions. A normal stage run may now refuse even that historical view because the live SP-2 confirmation has legitimately advanced. Solver must revalidate current authority and use an officially supported join of the already-frozen r31 or coordinate the next cumulative stage within its authority;do not forge/reconfirm old owner input,force or modify policy to make a join pass. Planner has not launched or joined any run.
