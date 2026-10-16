---
status: in-progress
---
# REQ-019 — Scheduler M5 Recovery Manager report

Date: 2026-10-15  
Authority: the approved, unchanged `/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md`

## Result

M5 implementation and local integration through T18 are complete. The frozen test chain
Planner → M1 → M2 → M3 → M4 → M5 → M1-authorized retry passes with disposable repositories
and fake verification. It preserves the rejected attempt's M3 handoff, asks M2 for a fresh
assignment, and only completes after a later accepted verdict. M4 can be omitted. Restart
coverage verifies durable recovery without duplicating the attempt or decision.

The task is not closed. T19 did not launch because the opt-in preflight could not find two
fresh, permitted providers from distinct providers; no agent or paid CLI request was started.
The production M6 verifier is also absent: the repository has the M1 `VerificationPort` and
test verifier doubles, but no production M6 implementation. The M6 boundary question sent to
the owner is still pending. The end-to-end result therefore proves the M5 contract with a
test verifier; it does not prove a production M6 integration.

## Delivered

- Added the isolated `bt_scheduler_recovery` package with validated/versioned contracts,
  deterministic bounded policy, conservative safety guards, a private durable idempotent
  decision store, metrics, and read-only text/JSON inspection.
- Added the optional M1 RecoveryPort adapter and `wire()` integration. M5 reads M1/M3 public
  facts; it does not write M1 state, execute processes, select accounts, or accept rejected
  work.
- Bound M3 attempt evidence to the approved plan SHA-256. The M3 request field is optional
  for old durable rows; hashless legacy rows can satisfy only a matching idempotent replay,
  not M5 recovery or snapshot continuation. Added cross-plan and legacy replay regressions.
- Added retry coverage proving M1 obtains a new M2 assignment while M3 resumes from the
  verified snapshot in a new worktree. The existing approved plan document remains unchanged.
- Added a real-CLI experiment harness gated behind explicit environment flags and a fresh
  two-provider quota check. It uses a disposable project, injects one controlled rejection,
  has a 300-second deadline, and writes a private sanitized receipt only if launched.

## Acceptance matrix

| Criterion | Result | Evidence / limit |
|---|---|---|
| AC01: real M1 contract and M5 specification | PASS | REQ-019 SPEC; M1 1.2.0 signatures retained. |
| AC02: M5 does not mutate M1 state or execute processes | PASS | Policy/store separation, RecoveryPort adapter, and integration tests. |
| AC03: operation without complete M2/M4 | PASS | Isolated M5 package tests; E2E also covers M4 omitted. |
| AC04: bounded and auditable retries, waits, quotas | PASS | Policy/history tests and read-only metrics. |
| AC05: no recovery of live, uncertain, stale or cancelled attempts | PASS | Guard and adapter failure tests. |
| AC06: preserve M3 handoff and data on failure | PASS | Snapshot continuation, failure and restart tests. |
| AC07: verification rejection cannot become success | PARTIAL | Rejected-verdict simulator and M5 E2E pass; production M6 verifier is not present. |
| AC08: crash/restart idempotency | PASS | M5 crash suite and restart-after-recovery E2E. |
| AC09: port failure isolation | PASS | Conservative adapter failure and independent-task tests. |
| AC10: no secrets or personal provider data in M5 telemetry | PASS | Opaque evidence refs, redaction regression, scoped standards audit. |
| AC11: E2E and measured report | PARTIAL | Local fake-verifier E2E is reproducible. T19 real CLI metrics were not collected because its preflight did not pass. |
| AC12: legacy and approved plan preserved | PASS | Original plan unchanged; legacy replay regression; disposable E2E checks source checkout and RUN fixture unchanged. |

## Verification run

The following recorded commands completed:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/bt_scheduler_recovery/tests -q` — 33 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_recovery_adapter test_scheduler_recovery_sources test_scheduler_recovery_failures test_scheduler_recovery_crash test_scheduler_m1_m5_e2e -q` — 19 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/bt_scheduler_executor/tests -q` — 279 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest bt_scheduler_executor.tests.test_contracts bt_scheduler_executor.tests.test_start bt_scheduler_executor.tests.test_ledger -q` — 50 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` — 258 passed, 4 skipped. This discovery preceded addition of the opt-in T19 harness; that file was run separately.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m5_live_experiment -v` — skipped by default as designed.
- `BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1 BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m5_live_experiment -v` — skipped before launch: two fresh, permitted providers were unavailable. No provider process was started.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest discover -s tests/migration -q` — 204 tests, 1 failure. The unchanged `skill/scripts/tests/test_relay_run.py` collects 48 tests while the existing collection baseline records 52. No migration baseline or test was changed to hide this discrepancy.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests:tests/migration python -m unittest test_package_install -q` — 16 passed.
- Scoped Ruff checks on M5/new files and focused import/syntax checks on the touched M3 files — passed. Broad default Ruff on legacy M3 files still reports pre-existing style findings outside the scoped checks.
- `git diff --check` — passed after fixing an extra EOF blank line.

Supporting upstream suites recorded during this task: M1 core 250 passed / 2 skipped, Planner 219 passed,
M2 decision 65 passed, and M4 monitor 135 passed.

## Independent review and remaining work

The final spec review inspected this report, execution plan and T19 harness. It confirmed that the
preflight did not launch an agent, the production M6 gap is explicit, AC07/AC11 are partial, and T19/T20
remain open. The final standards review of the T19 harness and report is in progress. T20 remains open
because the plan requires T19 first.

No M5 live CLI experiment ran. No production M6 verifier was implemented or tested. T19 and T20 remain
unchecked in the execution plan; the user's answer on the production M6 verifier boundary is required
before extending implementation into M6. No commit, push or merge was made. Existing unrelated dirty
worktree changes were preserved.
