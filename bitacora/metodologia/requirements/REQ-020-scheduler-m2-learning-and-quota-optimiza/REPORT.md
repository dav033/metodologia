---
status: in-progress
---
# REQ-020 — Scheduler M2 learning and quota optimization report

Date: 2026-10-16  
Authority: approved `SOURCE-PLAN.md`/`PLAN.md`, plus David's explicit T24 authorization on 2026-10-16.

## Result

The offline M2 learning, quota-window and batch-selection work through T23 is implemented and audited. The fake-backed
Planner → M1 → M2 → M3 → M4 → M5 → M6 test chain passes. The authorized T24 real-provider attempt did not meet its
eight-task acceptance: T2 timed out, T3/T4 were not independently verified, and T5–T8 were not dispatched. T24 remains
open; this report makes no quota-savings, quality-improvement or account-routing claim. T25 audits and the T26
documentation handoff are complete for the observed result, so the requirement itself remains `in-progress`.

## Built

- Implemented cached, account-deduplicated multi-window quota observations, attributed demand estimates, correlated
  verified-outcome history, immutable learning snapshots, deterministic batch matching, opt-in shadow comparison and
  M1/M3/M4/M5 integration while preserving M1 reservation authority.
- Kept Laya behind the existing quality gate. Its approved evidence allowlist remains empty; deterministic M2 routing
  stays active.
- Hardened the T24 verifier to check declared worktree paths, attribute attempts through M3's nested request or a
  unique M1 executor reference, and deliver cancellation before reconciling M1 to a terminal state. The opt-in live
  test is still a one-run acceptance harness and was not repeated after its failure.
- Added M2 runtime configuration and rollback instructions in `skill/scripts/bt_scheduler_decision/README.md`.

## Verification evidence

### Planner through M6

- `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m1_m6_e2e test_scheduler_m1_m5_e2e test_scheduler_m1_m4_e2e -q` — **13 passed**.
- Scheduler integration discovery, rerun at closeout with `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` — **305 tests run, 6 skipped, 0 failures**. Opt-in live-provider tests were skipped; no live opt-in variable was set for this check.
- Component suites from the preceding verification pass: Planner **219**, M1 **250**, M2 **165**, M3 **279**, M4 **135**, M5 **33**, M6 **67** passed.

### T24 harness and static checks

- `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m2_live_experiment_contracts -v` — **5 passed**, covering declared-path scope, nested/fallback attribution, ambiguous bindings and cancel/wait/reconcile order.
- `PYTHONPATH=skill/scripts:skill/scripts/tests python -m unittest test_scheduler_m2_live_experiment -v` — **1 opt-in provider test skipped** because `BITACORA_LIVE_SCHEDULER_M2_EXPERIMENT` was not set.
- `python -m py_compile` on the experiment harness and support modules, scoped Ruff, and `git diff --check` — passed.
- `python skill/scripts/bitacora.py --project metodologia trace --node REQ-020` — exit 0; the trace includes T24–T26, D-050 and P-041.
- `python skill/scripts/bitacora.py --project metodologia plan-json check REQ-020` — exit 0, publishable with existing warnings: T1 and T24 have no machine-checked verification command, and file evidence for the `methodology` repository could not be checked because that checkout is not registered here.
- `bitacora.py index` regenerated the project index and `bitacora.py pending` sorted PENDING.md.
- The independent spec follow-up found no remaining attribution issue. The standards follow-up approved the path-scope check, fail-closed reference matching and cancellation settlement. Neither audit invoked providers.

Earlier standalone M1/M3 concurrency suites emitted a Python 3.14 `ResourceWarning` for an unclosed SQLite connection
from a concurrency test process while exiting successfully. This closeout did not suppress or investigate that warning;
the Scheduler integration discovery and the Planner-through-M6 E2E command above both exited successfully.

### Bounded live T24 attempt

- Fresh preflight: two eligible Antigravity model routes, one effective account, 6% observed usage. Account-level route
  comparison was therefore unavailable. All four dispatched attempts selected `gemini-3.8-flash-low`.
- Runtime: **358.7 seconds** total, at most **2** active tasks, source checkout unchanged. T2 reached its **300-second**
  attempt timeout and the stop rule halted further dispatch.

| Task | Recorded result |
|---|---|
| T1 | M1 completed. The pre-fix verifier reported PASS after 9 tests and a passing behavior probe; it did not check all changed paths, so this does not prove the full declared-scope criterion. |
| T2 | Timed out at 300 seconds; executor returned code 1 without a terminal event. M1 entered its failure/cancellation path. |
| T3, T4 | Executor processes returned code 0 with terminal events, but M1 remained `active/verifying` after the harness stopped stepping. Neither received an independent verifier result. |
| T5–T8 | Not dispatched after the stop rule; their M1 rows were cancelled. |

The private receipt is `~/.local/share/bt-scheduler-m2-experiment/t24-nmg7xg5e/result.json`, mode `0600` in a mode
`0700` parent directory. It contains four attempts but stores `task_id: null` for each and `attempt_id: null` on all
task rows; the task/attempt mapping observed in the in-run ledger was lost by the old serializer. The receipt reports
**322,206 tokens** across the three completed attempts (117,930 + 84,835 + 119,441; the timed-out attempt has no usage
record), weekly quota moving **6%→7%**, and five-hour quota **0%→3%**. These are observed usage facts, not savings or
optimization evidence. The disposable workspace was removed after the run, so the old T1 worktree diff cannot be
retrospectively verified. The historical receipt is preserved unchanged.

The experiment therefore failed the required eight-task acceptance. No provider retry or follow-on attempt was made;
the controlled exhausted-quota case remained an in-memory no-call control.

## Rulings

- **D-050:** keep deterministic M2 routing active. This partial T24 result cannot justify activating optimization or
  claiming savings or better task quality. Any new live evidence needs a newly scoped bounded experiment, fresh quota
  preflight and separate explicit authorization.
- M6 remains opt-in through M1's `VerificationPort` under D-043; no default activation or production configuration was
  changed in this closeout.

## Needs your eyes

- No production/default activation was made. The only owner decision pending is whether to re-plan T24 for a new live
  evidence run (P-041); the existing failed registration must not be repeated.

## Proposals

- None beyond the pending T24 re-planning decision.

## Pending

- **T24 remains open.** P-041 records the option to prepare a new bounded plan and obtain a separate explicit gate. Keep
  the deterministic route reference active until accepted live evidence and an owner ruling exist.

## Walkthrough

1. Planner freezes the approved plan revision and SHA-256; M1 owns run, task, attempt and reservation state.
2. M1 supplies its READY tasks and free-slot count to M2; M2 reads cached quota, account identity and correlated history.
3. M2 returns a bounded route proposal; M1 revalidates and reserves it before M3 executes in an isolated worktree.
4. M4 observes execution streams and metrics without taking scheduler authority.
5. Optional M6 verifies the matching M3 snapshot and submits its correlated PASS/FAIL only through M1.
6. A failure reaches M5 through M1; only an M1-approved retry requests a fresh M2 assignment. Missing evidence keeps the
   deterministic fallback, and the local E2E suite covers this chain through M6.
