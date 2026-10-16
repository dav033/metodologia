# REQ-021 — Scheduler M5/M6 runtime integration

Date: 2026-10-15  
Authority: David's request to execute the approved M5 recovery plan and verify Planner through M6.

## Built

- Integrated the isolated M6 package into the shared checkout without copying its conflicting REQ/D identifiers.
- Added opt-in `quality_store_path` / `quality_policy` composition through the existing M1 `VerificationPort`. Existing
  injected verification remains available when M6 is omitted; M6 cannot be combined with a custom verifier.
- Kept M1 and M3 behind their public adapters. M6 validates the approved M1 order, verifies the matching captured M3
  snapshot in bubblewrap, stores durable private evidence, and submits correlated PASS/FAIL verdicts only through M1.
- Preserved M1's `NEEDS_REVIEW` behavior: no automatic verdict is sent and the task remains verifying until an
  operator resolves the review.
- Added fail-closed path/policy guards, construction-failure cleanup, ordered shutdown, and a real Planner→M1→M2→M3→M4→M5→M6
  local E2E. Fixed the audited shutdown race so `close(wait=True)` waits for the M6 dispatcher before its store closes.
- Updated module boundary, package metadata, installed-wheel checks, architecture notes, REQ-019 evidence, and P-040.

## Verification evidence

- M6 package: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_quality/tests -q`
  from `skill/scripts` — 67 passed.
- Integrated composition and real M3 handoff:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:tests python3 -m unittest test_scheduler_m1_m6_e2e test_scheduler_quality_real_integration -v`
  from `skill/scripts` — 6 passed (5 composition/full-chain tests plus 1 real-M3 integration test).
- Full Scheduler discovery: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q`
  — 271 tests run, 5 expected opt-in skips, all other tests passed.
- Supporting module suites passed: Planner 219; M1 250; M2 65; M3 279; M4 135; M5 recovery 33. The M5 recovery
  adapter/integration/crash set passed 19; M1 public boundary tests passed 6; installed package tests passed 17.
- The strict T19 preflight ran with `BITACORA_LIVE_SCHEDULER_M5_EXPERIMENT=1` and
  `BITACORA_LIVE_SCHEDULER_M5_PREFLIGHT_ONLY=1`: 7 tests, 6 passed and the live experiment skipped before launch
  because fewer than two distinct fresh provider/account routes met the <=50% observed quota-use gate. No provider
  process or paid CLI request started; this is not T19 live-experiment evidence.
- Scoped Ruff over the M6 package, adapter, composition and integration test passed. `git diff --check` passed.
- One initial focused test invocation from the M6 tests directory could not resolve project-root modules; rerunning
  from `skill/scripts` with the documented `PYTHONPATH` passed as listed above.

## Acceptance matrix

| Criterion | Result | Evidence / limit |
|---|---|---|
| AC01: M1 contract remains unchanged | PASS | M1 contract remains 1.2.0; public boundary suite 6 passed. |
| AC02: existing verifier injection remains usable | PASS | Opt-in guards and existing composition tests pass; omitting `quality_store_path` keeps caller-owned verification. |
| AC03: M6 verifies the approved order and corresponding M3 snapshot | PASS | Real-M3 handoff test and Planner/M1/M2/M3/M5/M6 E2E. |
| AC04: rejection, M5 recovery, fresh M2 route, snapshot continuation, later acceptance | PASS | Full chain proves FAIL → M1 recovery → M5 retry advice → new M2 decision → M3 continuation → M6 PASS → M1 completion. |
| AC05: failure, stale/missing evidence, sandbox failure, and `NEEDS_REVIEW` cannot falsely complete M1 | PASS locally | M6 package, real-M3 integration, and full-chain regressions. |
| AC06: construction and shutdown do not leak M6 resources or close M3 early | PASS | Composition-failure cleanup, slow-dispatcher/store-close regression, and M6/M5/stream/M3 shutdown-order test. |
| AC07: T19/T20 status reflects observed live gate | PASS | Later fresh gate passed; REQ-019 T19 completed in 74.351 s with one real alternate-provider CLI invocation; independent T20 spec and standards audits approved. |
| AC08: boundaries, package, scoped checks | PASS | Public adapter boundary 6, installed package 17, scoped Ruff, and `git diff --check`. |

## Rulings

- D-043 keeps M6 explicitly opt-in through `quality_store_path`, preserves M1 as the only state/verdict owner, and keeps
  `NEEDS_REVIEW` pending. M6 is not globally activated.
- The separate M5 T19 provider experiment required two distinct fresh provider/account routes at <=50% use; it
  completed under that gate and is recorded in the REQ-019 report and private receipt.

## Needs your eyes

- Review the verification boundary and opt-in composition in `skill/scripts/bt_scheduler_executor_wiring.py` and
  `skill/scripts/bt_scheduler_quality_adapter.py`.
- Review the sandbox runner and evidence handling in `skill/scripts/bt_scheduler_quality/runner.py` and
  `skill/scripts/bt_scheduler_quality/engine.py`.

## Proposals

- None.

## Pending

- No REQ-019 T19/T20 work remains. M6 remains opt-in under D-043; a caller must provide a private persistent quality
  store path and have bubblewrap available.

## Walkthrough

1. Planner freezes the approved plan; M1 binds its hash and owns task and attempt state.
2. M2 records a route decision; M3 executes it in an isolated worktree and captures the attempt snapshot.
3. M1 sends the approved verification order to M6 through the public composition adapter.
4. M6 checks that order against the frozen plan and resolves the matching M3 handoff before running sandboxed checks.
5. M6 persists results and evidence; its outbox submits a correlated verdict through M1's existing contract.
6. A FAIL enters M1 recovery; M5 recommends a bounded action, M2 supplies a new assignment, and M3 can continue the
   preserved snapshot before M6 verifies the new attempt.
7. `NEEDS_REVIEW` sends no verdict; the task stays verifying until an operator resolves it.
8. Shutdown waits for M6 dispatch and workers, then closes its store before M5, stream resources, and M3.

## Independent review

- Initial standards audit approved the composition, boundaries, sandbox, durable verdict delivery, and packaging.
- Initial spec audit found that the five-second dispatcher join could race M6 store closure. The implementation now
  joins the dispatcher without a timeout for `wait=True`, and `test_wiring_waits_for_slow_m6_dispatcher_before_closing_store`
  verifies store closure waits. Fresh spec and standards re-reviews approved the correction and report.
