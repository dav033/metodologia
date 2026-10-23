---
req: REQ-020
status: done
created: 2026-10-15
---
# Plan — Scheduler M6 Quality & Integration

## Approval and approach

Approved by David's explicit request to implement and independently test the complete source proposal on
2026-10-15. Preserve every M6 T01–T20, Q01–Q20 and AC01–AC13. Build an isolated, standard-library M6 package with
one adapter to the existing M1/M3 public interfaces. Run approved checks only against a verified copy of the M3
snapshot, in a bubblewrap OS sandbox with network and host home unavailable. Use M1's current binary verdict safely:
PASS/FAIL submit correlated verdicts; NEEDS_REVIEW remains pending for a named human decision. No shared contract,
M1 core, M3 executor, M5 package or central wiring edits are planned.

## Global constraints

- Work only in `/home/david/dev/metodologia-m6-quality` on `feat/scheduler-m6-quality`; preserve the dirty author
  worktree and its M4/M5 changes.
- M1 remains the only owner of task state and the only receiver of verdicts. M6 never assigns, starts, retries,
  merges, changes a plan, modifies M3 artifacts, pushes, deploys or mutates production.
- Keep `bt_scheduler_quality` dependent only on the Python standard library. Isolate external check processes with
  bubblewrap; refuse execution when a real sandbox cannot be established.
- Orders and handoff data are external input until validated. Never trust agent reports, environment, artifact paths
  or repository paths from JSON without bounded runtime validation.
- Preserve user data and all unrelated files. Do not commit, push, merge, install or delete user-owned paths.
- Verify changed behavior with deterministic tests. Paid-provider tests stay opt-in and are not run.

## Verification seams

1. M6 public engine / result store — order validation, idempotence, policy, evidence and recovery across restart.
2. M6 public runner — a disposable Git snapshot, a real bubblewrap process, bounded output/deadline and denied host
   filesystem/network access.
3. M1 `SchedulerCore` public `VerificationPort`/`submit_verdict` — only an exact independent verdict completes or
   rejects the current attempt; unknown evidence does neither.
4. M3 `AgentExecutor.describe()` and actual handoff manifest — committed, dirty and untracked snapshot provenance;
   repository and source worktree remain unchanged.
5. Existing `PredecessorIntegrator` tests and a temporary multi-task repository — compatible ancestors share the
   resolved base; conflicts/missing snapshots are not reimplemented or turned into PASS.
6. Simulated M5 `RecoveryPort` in E2E — an M6 rejection reaches M1 recovery while independent branches continue.

## M6-H0 — Baseline, contract and decision

- [x] **M6-T01 — Audit current code and baselines.** Record M1 `VerifyOrder`, `Verdict`, `submit_verdict`, M3
  handoff/description and `PredecessorIntegrator`, plus the existing audit/quality modules. Run M1 and M3 reference
  suites in the clean M6 worktree. Evidence: `INVENTORY.md` and actual test totals.
- [x] **M6-T02 — Formalize M6 specification.** Record authority, scope, PASS/FAIL/NEEDS_REVIEW, risks and separation
  from M1/M3/M5 in `SPEC.md` and D-042. Verify no ownership or contract change.
- [x] **M6-T03 — Freeze interfaces and fixtures.** Document exact M1/M3 adapter inputs, output schemas, failures,
  sample `VerifyOrder`/handoff/result and the M5 simulator boundary. Verify both packages can exercise each other
  through public contracts only.

## M6-H1 — Deterministic verification core

- [x] **M6-T04 — Isolated package.** Add `skill/scripts/bt_scheduler_quality/` contracts, policy, engine, evidence,
  runner, identity, store and simulators, focused tests and README. Package imports only itself and stdlib.
- [x] **M6-T05 — Order validation and idempotence.** Validate full identity, criteria, checks, content hashes and
  idempotency; persist one request/result and reject a reused key with different content. Verify duplicate request
  does not run checks again.
- [x] **M6-T06 — M3 snapshot resolver.** Validate M3's bounded handoff manifest, repository identity, snapshot and
  base commits; reconstruct the tracked + dirty + untracked snapshot in an isolated temporary directory. Verify
  primary checkout, unrelated worktrees and original handoff are unchanged.
- [x] **M6-T07 — Sandboxed check runner.** Accept only validated `argv` and contained `cwd`; use bubblewrap with no
  network, host home or inherited secrets. Bound runtime, processes, output, temp storage and concurrency; kill
  process trees; refuse if isolation fails. Exercise timeout, output flood and path escape.
- [x] **M6-T08 — Criteria evaluator.** Map `purpose` exactly to approved acceptance text; produce per-criterion
  `pass|fail|unknown` with evidence. Verify a missing/ambiguous/manual/ignored check cannot PASS and the
  PASS/FAIL/NEEDS_REVIEW truth table is deterministic.

## M6-H2 — Integration and durable evidence

- [x] **M6-T09 — Integration provenance.** Validate M3's pinned base and its ancestry in the exact attempt snapshot;
  rely on M3's existing `PredecessorIntegrator` for merge/conflict resolution. Test two compatible and conflicting
  accepted predecessors, shared files and base divergence without writing source refs.
- [x] **M6-T10 — Optional independent review.** Keep review disabled unless explicit policy requires it. Provide a
  separate reviewer identity/evidence boundary; missing or same-as-author identity becomes NEEDS_REVIEW. No paid
  provider or builder self-approval.
- [x] **M6-T11 — Durable evidence manifest.** Store exact input/base SHA, criteria/check hashes, verifier/policy
  version, command/argv, status, real exit/timing, bounded logs, artifact hashes and timestamps. Verify restart
  persistence, integrity and secret redaction; M1 evidence stays short.
- [x] **M6-T12 — Metrics and defects.** Reuse existing Bitácora quality/audit facilities where applicable. Keep
  not-run, unknown and unmeasured counts distinct from zero; prove missing defect count remains unknown and avoid
  duplicate accounting.

## M6-H3 — M1 adapter and resilience

- [x] **M6-T13 — `VerificationPort` adapter.** Add
  `skill/scripts/bt_scheduler_quality_adapter.py`; `Ack` records request admission only. Deliver PASS/FAIL through
  exact `SchedulerCore.submit_verdict` correlation and non-empty evidence. Verify `execution_finished` alone never
  completes a task.
- [x] **M6-T14 — NEEDS_REVIEW policy.** Persist the review item, keep M1 `VERIFYING`, expose inspect/resolve
  operations and explicit operator identity/reason. No automatic PASS, FAIL, retry or timeout transition.
- [x] **M6-T15 — Outbox and reconciliation.** Persist result before delivery; re-submit same verdict ID after
  crashes or M1 failure; make duplicate/stale replies observable and idempotent. Exercise crashes before and after
  local result commit and M1 submission.
- [x] **M6-T16 — M5 compatibility.** Use the existing `RecoveryPort` simulated by M1. A failed check produces
  M1's `verification_rejected` transition; M6 never calls M5 or requests retries. Verify independent tasks proceed.

## M6-H4 — Independent proof and closure

- [x] **M6-T17 — Deterministic E2E.** Build a disposable 3–6 task fixture with dependencies, committed + dirty
  snapshots, a genuine regression and a contract collision. Assert verdicts and zero source-checkout side effects.
- [x] **M6-T18 — Negative/crash matrix.** Cover runner hang, output flood, disk/store failure, absent or stale
  snapshot, late verdict, new attempt/token, secrets in output, hostile paths and sandbox escape attempts. No false
  acceptance, corrupted ledger or orphan process.
- [x] **M6-T19 — M3 real/M5 simulated.** Use the real M3 module and its bounded CLI with a fake local provider, then
  run M6; exercise one passing and one rejected task through M1 with M5 simulated. No live provider, production
  system, credential or network.
- [x] **M6-T20 — Independent final audit and report.** Review exact diff against SPEC/PLAN, document every AC/Q/T
  with observed evidence, residual limits and rollback; do not mark an unrun check as passing.

## Required scenario matrix

| ID | Scenario | Required observed result |
|---|---|---|
| Q01 | M3 exit 0 but required test fails | FAIL; M1 never completes |
| Q02 | Every required check and criterion passes | PASS with correlated, non-empty evidence |
| Q03 | Agent `report.json` says ready | No effect on verdict |
| Q04 | Snapshot missing or invalid | NEEDS_REVIEW; never PASS |
| Q05 | Check differs from frozen plan | Reject without execution |
| Q06 | Same idempotency key sent twice | One logical check set and verdict |
| Q07 | Old revision/token/attempt | Stale; no verdict for replacement attempt |
| Q08 | Builder and agent reviewer are same identity | Block auto-approval |
| Q09 | Compatible accepted predecessors | Use the exact M3 integrated base |
| Q10 | Predecessors conflict | Clear M3/M1 diagnosis; no main merge |
| Q11 | Runner hangs or floods output | Real deadline/cap and durable evidence |
| Q12 | Runner tries host HOME/repository escape | Denied by OS sandbox or no execution |
| Q13 | Crash after PASS persistence before delivery | Same verdict re-delivered |
| Q14 | M1 unavailable at delivery | Durable outbox retry, no lost result |
| Q15 | Human/non-automatable criterion | NEEDS_REVIEW and explicit resolution path |
| Q16 | Accepted verdict has empty evidence | M1 rejects; M6 never emits it |
| Q17 | Failure alongside independent branch | Independent branch still runs |
| Q18 | Dirty/untracked M3 work | Snapshot includes it; source remains unchanged |
| Q19 | Secret appears in output | Private/redacted artifact only |
| Q20 | Verification needs production deployment/migration | No production action; NEEDS_REVIEW |

## Verification commands

- M1 baseline: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_core/tests -q`
  from `skill/scripts`.
- M3 baseline: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s
  skill/scripts/bt_scheduler_executor/tests -q` from repository root.
- M6 package: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_quality/tests -v`
  from `skill/scripts`.
- Adapter/M1/M3 integration: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s
  skill/scripts/tests -p 'test_scheduler_quality*' -v` from repository root, plus explicitly named M1/M3 regression
  tests.
- Run the repository's configured Python formatter/linter and package-install checks if the final diff changes
  packaging. Report every command's actual result.

## Rulings

- **M6-T14:** M1 has binary `Verdict.accepted`; `NEEDS_REVIEW` stays in M6 and leaves the attempt `VERIFYING` until a
  human explicitly resolves it. This avoids invented M1 state and false retry/acceptance.
- **M6-T07:** a worktree alone is not isolation. Require real bubblewrap namespaces/mount restrictions; do not run
  any check if they cannot be established.
- **M6-T08:** no M1 schema change is needed for criterion mapping: accept only approved verification objects whose
  `purpose` exactly equals the acceptance criterion. All other cases remain unknown and need review.
- **M6-T09:** M3 has already called `PredecessorIntegrator` and stores the pinned `base_sha` in its attempt/handoff.
  M6 verifies that provenance and snapshot ancestry; conflict merging stays exclusively in M3, so verification
  cannot mutate repository refs.
- **M6-T13:** keep the M6 adapter separately constructible/bindable so callers can pass it through the existing
  `VerificationPort` seam; do not edit central M1/M3 wiring in parallel with active M4/M5 work.
- **M6-T19:** use a fake local provider binary in the real M3 executor. Live model credentials, deployment and real
  database migrations are out of scope and remain opt-in after separate authorization.

## Progress log

- 2026-10-15 — Created isolated M6 worktree at `8749e44`; audited M1/M3 contracts and wrote REQ-020. Clean
  baselines passed: M1 239/239, M3 272/272. A real bubblewrap preflight hid `/home/david` and denied external
  routing. D-042 records the binary verdict and conservative review policy.
- 2026-10-15 — Froze the M1 order projection, Planner verification subset, M3 handoff snapshot fields, M6 result schema,
  status mapping and stable error-code examples in `bt_scheduler_quality/README.md`, `api-contract.json` and fixtures.
  The public VerifyRequest behavior is covered by its first red/green unit slice (4/4). Cross-module compatibility
  remains open until T13/T16.
- 2026-10-15 — Completed T03–T20, added package/wheel metadata and updated the M1 boundary allowlist for the explicit
  M6 adapter. Final suites passed: M6 66/66, real-M3 E2E 1/1, M1 239/239, M3 272/272, and isolated M1 boundary
  suite 6/6. Ruff, format, wheel contents, contract packaging and whitespace checks passed. `REPORT.md` maps every
  T01–T20, Q01–Q20 and M6-AC01–AC13 and records limits: no actual ENOSPC/SIGKILL injection, no wheel installation
  because pip is unavailable, and no second-agent review under the approved no-delegation constraint.
