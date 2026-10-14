# REQ-008 — Paused checkpoint, not a completion report

Execution is paused at the owner's explicit request. The approved scope remains unchanged.
No task writer or test handle is active. New defaults, council and closing work are pending.

## Built

- M1: durable requirements revalidation, bounded milestone packages and checkpoint APIs.
- T3: owned foreground process groups in the same controlling terminal/SID, terminal
  restoration, containment and verified planning-parent transition/manual entry.
- T4 implementation: pinned Claude structured reasoning with capability/session validation;
  admitted actions; bounded worker delegation/verification/documentation; durable effects,
  context rotation, native worker identity and safe pidfd orphan handling.
- T4 corrections: recover FINAL through a run-bound report digest; reopen rejected finishes
  using proven supersession and archived checkpoint revisions; retain counters/history;
  preserve actual worker route/session after crash and legitimate early exits; suppress
  restricted worker hook pull/commit/push/day deletion; propagate SIGINT through reasoning,
  runtime verification and independent settlement verification without another child or
  an additional failed attempt.

The default entry behavior was not changed. Unmarked legacy plans retain their existing
workflow. The new foreground path is explicit opt-in and fails closed on missing authority,
TTY or verified capabilities. REQ-008's PLAN is paused to prevent ordinary accidental launch.
No live provider, installed wrapper update or current-session replacement is claimed.

## Verification evidence

| Check | Final result | Evidence |
| --- | --- | --- |
| Affected regression suite | 139 tests, OK, 47.998s, exit 0 | `/tmp/req008-t4-review-closure-regressions.log` |
| Wheel/package/install gate | 10 tests, OK, 2.947s, exit 0 | `/tmp/req008-t4-review-closure-package.log` |
| Scoped ruff | All checks passed, exit 0 | `/tmp/req008-t4-review-closure-ruff.log` |
| Scoped source/documentation diff check | Passed, exit 0 | Implementer closure and coordinator pause check |
| Final verification-interrupt / validation corrections | Reproduced red; four focused tests green, 4.799s, exit 0 | `/tmp/req008-t4-review-last-red.log`, `...-green.log` |

The coordinator inspected final logs and final stop/leaf-validation code. Independent spec
and standards reviewers confirmed the original fixes; their last two findings were then
corrected with the focused regressions above. No third broad phase review was launched.
T8's full regression and final integration audit have NOT been executed. No separate
typecheck is configured. Broad legacy ruff remains failing: 24 findings versus 25 on HEAD,
reported in `/tmp/req008-t4-review-legacy-ruff.log` and `...-baseline-ruff.log`; scoped
changes pass. Unrelated Maros whitespace failures in global diff check were left untouched.

For a future local verification, the behavioral suites live in
`skill/scripts/tests/test_orchestration_rotation.py`,
`test_orchestration_rotation_recovery.py`, `test_orchestration_terminal.py` and
`test_orchestration_contract_dependencies.py`. Package evidence is from
`tests/migration/test_package_install.py`. Do not start execution until the owner resumes.

## Rulings

- D-016/D-017 retain approval and the enforceable structured boundary.
- D-018 permits only validated completion supersession; history and counters remain intact.
- CHECKPOINT/ACTIONS retain schema 1. The optional `superseded` API argument leaves old
  callers' monotonic behavior unchanged. Rejection records, report bindings and dispatch
  identity have explicit schema-1 contracts. Invalid legacy recovery records fail closed.
- Context limits are byte policies, not exact model tokens: 16 KiB entry, 16 KiB runtime,
  8 KiB checkpoint; provider output cap 65,536 bytes and 128 durable reasoning decisions.
- Foreground defaults remain unactivated. Safe Luna reasoning remains unproven/ineligible;
  ordinary Codex workers are separate. No native-tool fallback is permitted.

## Needs your eyes

The work is intentionally paused before release acceptance. When resumed, inspect completion
supersession, restricted hooks and final CLI/web integration as part of the planned audits.
No new approval or infrastructure change is requested now.

## Proposals

None added outside the approved scope.

## Pending

- P-018: paused at the owner's request; resume explicitly.
- Complete coordinator T4 acceptance and M2 default activation. Address CLI/web consumers
  and the traced stale-heartbeat/live-supervisor duplicate guard before activation.
- T5/T6: exactly three cheap-medium proposals, bounded peer debate and evidence-based ruling;
  durable stall, quota, incomplete-panel, permission and stop handling without budget resets.
- T7/T8: complete end-to-end controlled-provider proof, final independent audits, regression,
  trace/evidence reconciliation and final documentation. REQ-008 is NOT complete.

## Walkthrough

The existing deterministic supervisor remains responsible for task selection and settlement.
A foreground reasoning child receives a bounded package and returns one validated action.
The host delegates scoped work, verifies it and stores compact receipts rather than forwarding
worker transcripts. Journals/checkpoints retain identity, budgets and completed effects.
Pressure creates a checkpoint and a fresh provider session. A rejected finish requires a
validated rejection and preserved prior checkpoint before work can reopen. FINAL is bound
to the exact report digest, so a crash can recover it and a changed report cannot reuse it.
Restricted children inherit a hook policy that prevents automatic VCS and document deletion.
Interruptions persist stop through the host; they do not silently launch the next child.
The three-agent recovery protocol and default workflow are still pending.
