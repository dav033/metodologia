---
req: REQ-020
status: done
date: 2026-10-15
---
# REQ-020 — Scheduler M6 Quality & Integration

## Outcome

Implemented M6 as a standard-library package and a separately constructible M1/M3 adapter. M6 validates an approved
M1 order, resolves and copies the exact M3 snapshot, runs only approved commands inside bubblewrap, stores hashed
evidence and delivery state in its own private SQLite ledger, and sends a correlated verdict through M1. Unknown or
manual evidence remains `NEEDS_REVIEW`; M6 does not change M1/M3/M5 ownership or shared contracts.

The branch is `feat/scheduler-m6-quality` at base `8749e44`; work remains local and uncommitted. The package and
adapter are included in the Python wheel metadata. No central runtime wiring, M1/M3/M5 module, source checkout,
production service, or live database was changed.

## Verification record

| Check | Observed result |
|---|---|
| M6 package: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_quality/tests -v` from `skill/scripts` | **66 tests, OK**, 2.544 s after the final module split. Includes real bubblewrap, runner timeout/process cleanup, output cap/redaction, store/restart, adapter/M1 and review cases. |
| M6 with real M3: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s skill/scripts/tests -p 'test_scheduler_quality*' -v` from repository root | **1 E2E test, OK**, 0.993 s after the final module split. Six-task fixture, real M1/M3/CLI/PredecessorIntegrator, local fake provider and simulated M5. |
| M1 reference: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_core/tests -q` from `skill/scripts` | **239 tests, OK**, 20.455 s. |
| M3 reference: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s skill/scripts/bt_scheduler_executor/tests -q` from repository root | **272 tests, OK**, 155.369 s. Includes M3's lone-copy `python -I` suite. |
| M1 integration boundaries: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts/tests:skill/scripts python3 -m unittest test_scheduler_integration.Boundary -v` | **6 tests, OK**, 11.610 s, including isolated M1 suite and the M6 package/adapter wheel metadata assertion. |
| Ruff | `ruff check` and `ruff check --select C901` passed on the complete M6 package and adapter; `ruff format --check` passed on all 29 included files (28 Python files and the README). Ruff is available in the environment; the repository `pyproject.toml` does not declare Ruff settings. |
| Wheel | `setuptools.build_meta.build_wheel` built a wheel in a disposable copy; archive inspection confirmed all 21 expected M6 package/resource/adapter entries, and zip imports passed. `pip` is not installed in this Python environment, so the wheel was not installed. |
| Syntax and whitespace | Final Python AST/JSON/trailing-whitespace check passed for 28 Python and 8 JSON files; `git diff --check` passed. |

The final audit split handoff validation, tar extraction, Git tree verification, sandbox process ownership and output collection by responsibility. The initial full-suite rerun exposed a misplaced `QualityEngine.recover_interrupted` method; it was restored to the class, then the M6 suite, real-M3 E2E and integration boundary suite all passed on the final tree.

The remaining size review triggers are `store.py` (700 lines), `engine.py` (468) and the M1/M3 adapter (475). They each keep one current boundary: the SQLite ledger and its transaction rules, one verification use case, and one `VerificationPort` adapter with its bounded worker/reconciliation lifecycle. No function exceeds the complexity threshold (`C901` is clean). Splitting those files now would spread the same state transitions and persistence invariants across more modules without creating an independently owned component; revisit if another persistence backend, verifier flow or adapter consumer is added.

## M6-T01–T20 coverage

| Task | Evidence and disposition |
|---|---|
| T01 — baseline and inventory | [`INVENTORY.md`](INVENTORY.md); direct M1 239/239 and M3 272/272 suites passed. Existing contract owners and quality/audit facilities were inspected. |
| T02 — formal specification | [`SPEC.md`](SPEC.md), accepted D-042 in `bitacora/metodologia/DECISIONS.md`; M1's binary verdict and M3's base/snapshot ownership are unchanged. |
| T03 — frozen interfaces and fixtures | `bt_scheduler_quality/README.md`, `api-contract.json`, and `tests/fixtures/`; adapter tests consume public `VerifyOrder`, `SchedulerCore.submit_verdict`, `AgentExecutor.describe()` and M5 `RecoveryPort` behavior. |
| T04 — isolated package | `bt_scheduler_quality/`; `test_package_imports_only_its_own_modules_and_the_standard_library`; wheel check. |
| T05 — validation and idempotence | `test_contracts.py`, `test_reserves_idempotently_and_rejects_reused_key_with_new_content`, `test_duplicate_request_returns_persisted_result_without_rerunning_checks`. |
| T06 — M3 snapshot resolver | `test_snapshot.py`: dirty/untracked materialization, attempt mismatch, non-ancestor base, manifest/archive symlink, file cap, `export-ignore`, and `export-subst`; source refs, index, worktree and manifest are asserted unchanged. |
| T07 — sandbox runner | `test_runner.py` and `test_policy.py`: real host-home/network isolation, unavailable bubblewrap, timeout and child cleanup, output cap/redaction, no shell, protected environment, and path containment. |
| T08 — criteria evaluator | `test_engine.py`: exact purpose mapping, manual/unknown/ambiguous checks, mandatory nonzero exit, mapped and unmapped outcomes, and production-action review. |
| T09 — integration provenance | E2E uses real M3 `PredecessorIntegrator`, two compatible accepted ancestors and a conflicting shared contract; M6 records the pinned base and does not merge or write source refs. |
| T10 — optional independent review | `test_review.py` covers disabled-by-default review, missing reviewer, same-as-author identity, order binding, rejection and secret checks. No paid or remote reviewer ran. |
| T11 — durable evidence | `test_store.py`, `test_review.py`, and restart adapter tests cover content hashes, private paths, artifacts, redaction, rollback on artifact write failure and persisted outbox/review state. |
| T12 — metrics and defects | `test_metrics_count_only_the_check_that_was_not_run` and `test_metrics_do_not_claim_unmeasured_defects_are_zero`; README documents why M6 command outcomes are not `bt_quality` milestone-audit findings. `defect_count` stays `null` until measured. |
| T13 — M1 adapter | `test_ack_is_durable_admission_and_execution_finished_does_not_complete`, `test_empty_evidence_is_never_submitted_as_an_m1_verdict`, plan-diff rejection, and M1's `test_acceptance_needs_evidence_and_a_named_verifier`. |
| T14 — `NEEDS_REVIEW` | `test_needs_review_keeps_m1_verifying_until_explicit_operator_resolution`; review store tests require an operator, binary decision and rationale. |
| T15 — outbox/reconciliation | `test_restart_replays_persisted_verdict_without_rerunning_the_check`, `test_outbox_retries_the_same_verdict_id_after_m1_applied_but_ack_was_lost`, and `test_stale_m1_reply_marks_the_stored_result_and_stops_delivery`. |
| T16 — M5 compatibility | `test_failed_check_reaches_m5_while_an_independent_task_completes` and E2E assert M1 `verification_rejected`/`execution_failed`; M6 never requests a retry. |
| T17 — deterministic E2E | One six-task integration E2E includes committed, dirty and untracked snapshots, a genuine failing regression, independent branches and a contract collision. |
| T18 — negative/crash matrix | Covered by timeout/child-kill, output cap, stale M1 result, invalid/missing snapshot, path/symlink rejection, secret redaction, injected artifact-write rollback and restart recovery tests. The write failure is injected; the test does not exhaust a real filesystem. Restart recovery is deterministic state-reopen coverage; no OS `SIGKILL` is injected during a live verification. |
| T19 — real M3 / simulated M5 | E2E runs the real M3 executor and read-only `show --json` CLI with a local fake provider, then verifies and rejects through M1 with simulated M5. No live provider, paid call, deployment or production migration ran. |
| T20 — final audit and report | This report cross-checks the exact diff against SPEC, PLAN, Q and AC. A separate second-agent review was not run because the approved plan keeps this work sequential with no delegation; the audit is a documented read-only self-review, not a second-person approval. |

## Q01–Q20 scenario matrix

| ID | Evidence | Result |
|---|---|---|
| Q01 | `test_nonzero_required_check_produces_fail_not_a_pass`; E2E T3 regression | Completed nonzero check is FAIL; M1 does not complete it. |
| Q02 | `test_exactly_mapped_passing_check_produces_content_addressed_evidence`; E2E T1/T2/T4/T5 | PASS has correlated, non-empty, content-addressed evidence. |
| Q03 | E2E `test_real_m3_handoffs_run_m6_checks_and_keep_m1_m5_authority` | T3's `report.json` says `ready`; M6 still returns FAIL from the required regression check. |
| Q04 | `test_missing_handoff_returns_review_with_null_snapshot_ids`; snapshot validation tests | Missing or invalid provenance cannot PASS. |
| Q05 | `test_order_changed_from_approved_plan_is_rejected_before_reservation_or_execution` | Rejected before queue reservation or runner call. |
| Q06 | `test_duplicate_request_returns_persisted_result_without_rerunning_checks`; store key-reuse test | Same request reuses one result; key with changed input is rejected. |
| Q07 | `test_stale_m1_reply_marks_the_stored_result_and_stops_delivery`; M1 old-attempt/wrong-token verdict tests | Actual M1 `stale` response is persisted as M6 STALE; no replacement-attempt verdict is sent. |
| Q08 | `test_same_as_author_identity_is_not_an_independent_review` | Same identity cannot approve. |
| Q09 | E2E compatible T1/T2 ancestors and M3 `PredecessorIntegrator` | M3's pinned integrated base is used and recorded in M6 evidence. |
| Q10 | E2E T6 conflict and `INTEGRATION_CONFLICT` recovery assertion | M3 rejects the collision; no PASS or source merge. |
| Q11 | `test_times_out_and_kills_sandbox_children`; `test_caps_and_redacts_untrusted_output` | Deadline, process cleanup, output cap and redaction are observed. |
| Q12 | `test_runs_in_a_real_sandbox_without_host_home_or_network`; policy escape tests | Host home/network are unavailable; invalid work paths do not run. |
| Q13 | `test_restart_replays_persisted_verdict_without_rerunning_the_check` | Reopened store redelivers the same verdict ID without rerunning checks. |
| Q14 | `test_outbox_retries_the_same_verdict_id_after_m1_applied_but_ack_was_lost` and restart test | M1 outage/lost acknowledgment preserves a retryable outbox entry. |
| Q15 | `test_needs_review_keeps_m1_verifying_until_explicit_operator_resolution` | Manual criterion remains pending until named operator resolution. |
| Q16 | M6 `test_empty_evidence_is_never_submitted_as_an_m1_verdict`; M1 `test_acceptance_needs_evidence_and_a_named_verifier` | Empty evidence remains pending and is never submitted; M1 rejects empty accepted evidence. |
| Q17 | `test_failed_check_reaches_m5_while_an_independent_task_completes`; E2E independent branch | Failed work enters M1 recovery while independent work completes. |
| Q18 | `test_materializes_dirty_and_untracked_snapshot_without_mutating_source_or_manifest`; E2E dirty/untracked M3 handoffs | Dirty/untracked bytes are verified from preserved snapshots; source checkout is unchanged. |
| Q19 | `test_caps_and_redacts_untrusted_output`; `test_reviewer_evidence_cannot_persist_configured_secrets` | Registered secret values are redacted/rejected before evidence persistence. |
| Q20 | `test_production_deployment_or_migration_stays_for_operator_review` | Deployment and mutating migration commands are not launched. |

## M6-AC01–AC13 acceptance

| AC | Evidence | State |
|---|---|---|
| AC01 — formal scope without taking authority | SPEC, D-042, package boundary test | Met. |
| AC02 — `execution_finished` cannot complete M1 | Adapter acknowledgment test and M1 event tests | Met. |
| AC03 — exact plan/revision/task/attempt/token correlation | `VerifyRequest` contracts, verdict identity, adapter plan-diff and stale tests | Met for the existing public M1 contract. |
| AC04 — durable, verifiable, private evidence | Evidence/store hash, restart, permissions and redaction tests | Met. |
| AC05 — reproducible criteria and unknowns never PASS | Criteria/engine mapping and unknown tests | Met. |
| AC06 — demonstrated test/integration failure becomes FAIL | Nonzero check and E2E regression/conflict assertions | Met. |
| AC07 — `NEEDS_REVIEW` is never silently promoted | Adapter review lifecycle test | Met. |
| AC08 — source checkout, approved plan and previous M3 snapshots unchanged | Snapshot unit tests and E2E HEAD/branch/status/index assertions | Met in disposable fixtures. |
| AC09 — no merge/push/deploy or production migration | No invocation path; classified production action test; static diff | Met within the M6 scope. |
| AC10 — optional audit/review identity is separate | Reviewer identity and binding tests | Met for the opt-in local reviewer boundary; reviewer identity is audit metadata, not cryptographic authentication. |
| AC11 — restart/replay is idempotent | Store restart, stable verdict ID and lost-ack tests | Met. |
| AC12 — M5 integration uses public boundary only | M6 package import test, adapter and M5 simulated E2E | Met. |
| AC13 — E2E, negative limits and costs documented | This report and exact test outcomes above | Met; real filesystem exhaustion, live-provider costs and actual process-kill injection were not measured. |

## Limitations and rollback

- The adapter remains separately bindable; no central wiring was added. Do not instantiate it until an operator chooses
  an explicit M6 store path and project policy. Bubblewrap was tested on this host only and is required for checks;
  unsupported hosts fail closed.
- `NEEDS_REVIEW` operator identity is stored as provided and is not proof of an authenticated human account.
- The final code review was a self-review because the approved plan forbids delegation. A second-person review remains
  available before any future shared wiring or release.
- There was no live provider, paid evaluation, production database, deployment, migration, push, merge or installation.
- Rollback requires no data migration: leave the M6 `VerificationPort` unbound and revert the additive wheel entries
  if packaging is not wanted. M1/M3 contracts, stores, snapshots and repository refs need no rollback.
