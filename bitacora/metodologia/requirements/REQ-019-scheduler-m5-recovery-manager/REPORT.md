---
status: done
---
# REQ-019 — Scheduler M5 Recovery Manager report

Date: 2026-10-15  
Authority: the approved, unchanged `/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md`

## Result

M5 implementation and local integration through T19 are complete. The frozen test chain
Planner → M1 → M2 → M3 → M4 → M5 → M1-authorized retry passes with disposable repositories.
The separate REQ-021 integration now extends this through production M6 wiring: a real M6 FAIL
leaves the first M1 attempt rejected, M5 recommends retry, M2 records a new assignment, M3
continues the preserved handoff, and only a later M6 PASS completes M1. M4 events and source
checkout preservation are asserted. Restart coverage verifies durable recovery without
duplicating the attempt or decision.

T19 has now completed under its two-route <=50% quota gate. The private receipt at
`~/.local/share/bt-scheduler-m5-experiment/run-1wzkoyj6/result.json` records a 74.351-second run, two attempts,
two distinct providers, one controlled quota failure, two M5 decisions, one real provider CLI invocation, successful
M2 reassignment, continued M3 snapshot, independent acceptance, unchanged disposable source, and M1 completion.
The earlier preflight did not pass; a later fresh preflight passed, and the live harness rechecked the gate before
launch. One quota source returned HTTP 401 and was not admitted as quota evidence; the two eligible M2 candidates had
valid headroom evidence. The receipt contains no account references or credentials and is mode 0600 under a mode-0700
directory. The disposable project was cleaned after M3 quiescence. The fresh spec-axis audit approved T01–T19 and
AC01–AC12 without actionable findings. The independent T20 standards-axis audit also approved with no actionable
findings. The acceptance matrix and measured evidence below are the final handoff; REQ-019 T01–T20 is complete.
M6 integration remains separate in REQ-021 and opt-in under D-043.

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
  two-provider quota check. The preflight requires distinct provider and account references
  with at least 50% quota headroom. When launched, it is configured to run a no-credential local
  CLI child that emits a quota message with a short reset; M3's real provider classifier should
  report it, M5 should apply its quota wait and retry policy, and M2 should exclude that provider
  on reassignment before the authorized retry delegates to one real provider CLI invocation.
  The harness has a 300-second deadline, retains its disposable project unless M1 is terminal
  and M3 is confirmed idle, and writes a private sanitized receipt only if launched.

## Acceptance matrix

| Criterion | Result | Evidence / limit |
|---|---|---|
| AC01: real M1 contract and M5 specification | PASS | REQ-019 SPEC; M1 1.2.0 signatures retained. |
| AC02: M5 does not mutate M1 state or execute processes | PASS | Policy/store separation, RecoveryPort adapter, and integration tests. |
| AC03: operation without complete M2/M4 | PASS | Isolated M5 package tests; E2E also covers M4 omitted. |
| AC04: bounded and auditable retries, waits, quotas | PASS | Policy/history tests and read-only metrics. |
| AC05: no recovery of live, uncertain, stale or cancelled attempts | PASS | Guard and adapter failure tests. |
| AC06: preserve M3 handoff and data on failure | PASS | Snapshot continuation, failure and restart tests. |
| AC07: verification rejection cannot become success | PASS locally | REQ-021 Planner→M6 E2E observes M6 FAIL → M1 rejected → M5 retry → M6 PASS → M1 completed; M6 runs against the captured M3 snapshots. |
| AC08: crash/restart idempotency | PASS | M5 crash suite and restart-after-recovery E2E. |
| AC09: port failure isolation | PASS | Conservative adapter failure and independent-task tests. |
| AC10: no secrets or personal provider data in M5 telemetry | PASS | Opaque evidence refs, redaction regression, scoped standards audit. |
| AC11: E2E and measured report | PASS | T19 receipt records 74.351 s, two attempts, two M5 decisions, one real CLI invocation, snapshot continuation, source unchanged and M1 completion. |
| AC12: legacy and approved plan preserved | PASS | Original plan unchanged; legacy replay regression; disposable E2E checks source checkout and RUN fixture unchanged. |

## Verification run

The following recorded commands completed:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/bt_scheduler_recovery/tests -q` — 33 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_recovery_adapter test_scheduler_recovery_sources test_scheduler_recovery_failures test_scheduler_recovery_crash test_scheduler_m1_m5_e2e -q` — 19 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/bt_scheduler_executor/tests -q` — 279 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest bt_scheduler_executor.tests.test_contracts bt_scheduler_executor.tests.test_start bt_scheduler_executor.tests.test_ledger -q` — 50 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` — 258 passed, 4 skipped. This discovery preceded addition of the opt-in T19 harness; that file was run separately.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m5_live_experiment -v` — 7 tests: 6 passed, 1 live CLI experiment skipped by default.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_recovery_adapter test_scheduler_recovery_sources test_scheduler_recovery_failures test_scheduler_recovery_crash test_scheduler_m1_m5_e2e test_scheduler_m5_live_experiment -q` — 26 passed, 1 opt-in live CLI experiment skipped.
- `BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1 BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m5_live_experiment -v` — current strict preflight skipped before launch: fewer than two fresh routes from distinct providers/accounts had <=50% quota use. No provider process or paid CLI request was started.
- `BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1 BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_m5_live_experiment -v` — 7 tests: 6 passed, live experiment skipped before launch because two distinct fresh routes/accounts with <=50% use were unavailable. No provider process or paid CLI request was started.
- Fresh quota preflight rerun with `BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY=1` — 7 tests: 6 passed; preflight passed with two eligible distinct provider/account routes and skipped before agent launch. One non-eligible quota source returned HTTP 401; M2 did not treat it as valid quota evidence.
- `BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_m5_live_experiment -v` — 7 tests passed in 74.427 s. The live test's private receipt records 74.351 s and confirms two attempts, one real CLI invocation, two M5 decisions, distinct providers, final M1 completion, snapshot continuation and unchanged source. Receipt permissions: directory 0700, file 0600; the disposable project was cleaned after quiescence.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:tests python3 -m unittest test_scheduler_m1_m6_e2e test_scheduler_quality_real_integration -v` from `skill/scripts` — 6 passed: five integrated composition/full-chain tests and one real-M3 handoff test.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_quality/tests -q` from `skill/scripts` — 67 passed, including the slow-dispatcher lifecycle regression.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` — 271 tests run, 5 expected opt-in skips, all other tests passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s skill/scripts/tests -p 'test_scheduler_quality_real_integration.py' -v` — 1 passed with real M3 handoffs.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_integration.Boundary -q` — 6 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests:tests/migration python3 -m unittest test_package_install -q` — 17 passed, including installed M6 package and adapter imports.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_recovery_adapter test_scheduler_recovery_sources test_scheduler_recovery_failures test_scheduler_recovery_crash test_scheduler_m1_m5_e2e -q` — 19 passed after lifecycle wiring changes.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest discover -s tests/migration -q` — 204 tests, 1 failure. The unchanged `skill/scripts/tests/test_relay_run.py` collects 48 tests while the existing collection baseline records 52. No migration baseline or test was changed to hide this discrepancy.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests:tests/migration python -m unittest test_package_install -q` — 16 passed.
- Scoped Ruff checks on M5/new files and focused import/syntax checks on the touched M3 files — passed. Broad default Ruff on legacy M3 files still reports pre-existing style findings outside the scoped checks.
- `git diff --check` — passed after fixing an extra EOF blank line.

Supporting upstream suites recorded during this task: M1 core 250 passed / 2 skipped, Planner 219 passed,
M2 decision 65 passed, and M4 monitor 135 passed.

## Independent review and closeout

The independent spec re-review confirmed the controlled quota path and approved T01–T19 and AC01–AC12 without
actionable findings. The fresh T20 standards-axis audit approved with no actionable findings. Earlier standards findings
about quota headroom and cleanup without confirmed process termination have been fixed: the harness requires two fresh
distinct provider/account routes at <=50% quota use, rejects a repeated retry provider, and preserves the disposable
project unless M1 is terminal, every M3 attempt is terminal and M3 confirms idle. The missing `preserve()` method
was added and regression-tested. T19 and T20 are complete, with the measured result and acceptance matrix recorded
above. REQ-021 proves the optional M6 verifier integration locally, but its opt-in wiring is not globally activated.
This REQ-019 turn did not run `git commit`, `push` or `fetch`. During the
work, local commit `570a314` appeared with message `maros: marathon REQ-005 S0021 T11 done`; it includes tracked
REQ-019 documentation and methodology memory updates. I did not attempt to undo that shared commit. The test harness
remains untracked. The local `origin/feat/scheduler-m4-agent-monitor` tracking ref points to the same commit, but this
turn did not verify the remote's current state. Existing unrelated dirty worktree changes were preserved.
