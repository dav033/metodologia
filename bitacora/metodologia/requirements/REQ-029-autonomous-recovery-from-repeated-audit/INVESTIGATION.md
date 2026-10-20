# Investigation — repeated audit recovery

## Recorded reproduction before implementation

Read-only command: `python3 bitacora.py --project metodologia scheduler-op REQ-027 status`.
Observed: no live attempt; T18 blocked; open decision `T18:11`. The decision reports `rework_limit`, T17 already returned twice, and F2/F19/F20 high. Exit 0 reports state; it does not demonstrate task completion.

Red-capable identity reproduction (scripts working directory):

```python
import bt_attempt_history
old = 'audit gate: 3 open blocking finding(s): F1 (high), F2 (high), F3 (high)'
new = 'audit gate: 3 open blocking finding(s): F2 (high), F19 (high), F20 (high)'
a, b = bt_attempt_history.signature(old), bt_attempt_history.signature(new)
assert a != b, 'Different audit finding sets collapse into the same repeat signature'
```

Observed: both signatures `a08812ca9aec`; `AssertionError`, exit 1. This is one defect; retaining numeric IDs alone would still fail when an auditor renumbers a real recurring defect.

Second red-capable reproduction uses official round-two F2 from `bt_remediation.history(rdir)[1]['findings']`, current approved task definitions and `bt_remediation._command_for(finding, tasks)`. Owners are T4a and T15c. The function selects `cd skill/scripts && python -m unittest discover -s tests -p test_remote_api.py`; T15c's required check is `cd remote/web && npm run verify`. Asserting that the selected check covers that web owner raises `AssertionError: Web finding owner verification is omitted by first-owner selection`, exit 1. This runs the actual selection function without changing product code or executing paid providers.

## Verified facts

1. M1 records eleven T18 attempts: seven rejected, two cancelled, two accepted and subsequently reopened. The owner-observed count is accurate, but these are not eleven identical failed audits. `EVIDENCE.json` captures these official records, ten handoff base/snapshot identities and nine historical finding sets read with `git show <snapshot>:remote/docs/audit.findings.json`.
2. Two remediation rounds generated T18.1–T18.4 and T18.5–T18.6. `bt_remediation.hook` returns false once its configured count is consumed; the gate falls back to named-task rework, which also reaches its configured count. There is no durable diagnostic-recovery stage beyond those paths.
3. `bt_attempt_history.signature` removes all numbers from error prose. Old and new finding sets become equivalent. `bt_remediation.record` retains local IDs/severity/owners but not complete finding evidence, semantic identity or a verified progress comparison. A warning in a prompt is the current response to repeated signatures.
4. The historical stale-base issue is real and addressed by D-100. The newest att-0202 audits a new base and marks Caddy F1 fixed. It finds F2 E2E fixture failures, F19 build/typecheck and F20 real OAuth session-response mismatch. Treating the 2→3 count change as no progress would be incorrect.
5. F19's build failure prevents the E2E setup from running its tests. Recovery must distinguish prerequisite failure from assertions never exercised and order corrections before re-audit. These descriptions are diagnosis inputs; this requirement does not patch the product defects.
6. M5's current adapter constructs bounded facts around opaque official verdict references. The diagnostic agent emits a headline/steps/option/note for an owner card. Neither currently produces an actionable, validated diagnostic correction strategy with durable application/progress state.
7. Verification selection missed a regression introduced by remediation itself: `bt_remediation._command_for` chooses the first command of the first named owner. T18.5 att-0196 was accepted after changing `remote/web/src/app/page.tsx`, while its frozen verifications run only backend/gateway commands. The immutable diff `git -C /home/david/dev/metodologia diff 569a1485062992dae9f8a61f28ef43ad8179f56e 255adcdb1bc0fb3814e0d448585551076183162c -- remote/web/src/app/page.tsx` adds the exact Attempt type predicate later rejected by F19 (TS2677/TS2322). The recovery system must include affected-surface checks, not inherit an arbitrary first command as proof.

## Proposed direction to validate in the plan

Keep M1 authoritative and M4 observational. Extend the existing recovery/Planner coordination with immutable evidence cases, a bounded diagnostic stage, constrained runtime-validated actions, idempotent revision/application, independent verification and progress assessment. Stop controls and genuine owner-only permissions remain explicit. Use offline replay first; do not resolve T18 by hand or reset its limits.

## Verification limits

No implementation changes or live recovery application were made during investigation. Existing gates correctly reject the current open blocking findings. System-generated successful remediation remains unverified until the new integration acceptance runs.
