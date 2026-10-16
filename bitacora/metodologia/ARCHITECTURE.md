# metodologia — Architecture

_Living document: how the thing is built (or, for business projects, how the process/organization works).
Edit in place; record the *why* of changes in DECISIONS.md._

## Overview
The methodology Scheduler composes the Planner and six isolated modules through methodology adapters. A supervised
runtime is available only through the explicit `launch --mode marathon --scheduler` option; existing marathon launch
continues to use the legacy supervisor. The Scheduler owner binds one approved, frozen plan revision, opens durable M1
state, composes M2/M3, writes an atomic status projection and resumes the same run after restart. Optional capabilities
remain caller-controlled: M4 needs its monitor store and an owner-driven bounded stream drain, M5 needs its recovery
store, and M6 needs a private quality store path. M4 observes, M5 recommends recovery through M1, and M6 verifies
captured M3 snapshots; M1 remains the sole owner of task state and verdict acceptance.

## Components / actors
| Name | Responsibility | Where (path / owner) |
|---|---|---|
| Planner | Frozen plan contract and task order | `skill/scripts/bt_planner/` → `bt_plan_adapter.py` |
| Scheduler owner runtime | Opt-in process lifecycle, M1/M2/M3 composition, heartbeat projection, recovery and notification cadence | `bt_scheduler_run.py` → `scheduler-run` CLI |
| M1 Scheduler Core | Run authorization, task/attempt state, and projection | `skill/scripts/bt_scheduler_core/` → `bt_scheduler_adapter.py` |
| M2 Decision | Quota-aware provider/profile/model route selection and route metrics | `skill/scripts/bt_scheduler_decision/` → `bt_scheduler_decision_adapter.py` |
| M3 Executor | Provider CLI process, isolated worktree, lifecycle, and bounded FIFO stream | `skill/scripts/bt_scheduler_executor/` → `bt_scheduler_executor_adapter.py` |
| M4 Monitor | Normalized events, gaps, metric history, and audit incident outbox in its own SQLite WAL store | `skill/scripts/bt_scheduler_monitor/` → `bt_scheduler_monitor_adapter.py` |
| M3→M4 bridge | Converts bounded FIFO frames to allowlisted M4 records and acknowledges only after durable commit | `bt_scheduler_stream_adapter.py`, `bt_scheduler_m4_stream_bridge.py`, `bt_scheduler_m4_wiring.py` |
| M5 Recovery | Durable bounded recovery advice through M1; no task-state writes or provider launches | `skill/scripts/bt_scheduler_recovery/` → `bt_scheduler_recovery_adapter.py` |
| M6 Quality | Sandboxed checks against the matching captured M3 snapshot; durable evidence and correlated M1 verdict outbox | `skill/scripts/bt_scheduler_quality/` → `bt_scheduler_quality_adapter.py` |

## Data & integrations
- The frozen Planner plan is the input to M1; M2 persists route decisions consumed by M3. M1, M2, and M3 retain their
  own stores and authority.
- For a Scheduler-owned requirement, the M1 SQLite database is authoritative and `RUN.projection.json` is a read-only
  view containing plan identity, task status and heartbeat. The legacy `RUN.json` remains separate and is never
  rewritten or used as a fallback by Scheduler readers.
- M4 uses a separate project-owned SQLite WAL database. It stores allowlisted normalized evidence, never raw provider
  output. M3 frame/gap cursors advance only with the corresponding M4 commit.
- M2 reads M4 metric history through a read-only port. M4 incidents reach M1 as versioned, idempotent audit references;
  M1 alone changes task/attempt state.
- M5 recovery advice is persisted separately and submitted to M1's existing recovery port. M6 stores verification
  requests, results, review decisions, evidence manifests, and verdict delivery state in its own private database.
- The opt-in `quality_store_path` composes M6 through M1's existing `VerificationPort`; M6 verifies only the approved
  order and matching captured M3 snapshot. PASS/FAIL returns through M1's existing verdict contract. `NEEDS_REVIEW`
  stays pending in M1 until an explicit operator resolution.

## Key flows
- Launch and recovery: `launch --mode marathon --scheduler` requires the requirements readiness gate and an existing
  approved, frozen `PLAN.json`; the owner holds the shared non-blocking authority lock while composing M1/M2/M3. A
  `scheduler-run --resume` reuses that exact M1 run and asks M3 to reconcile; it does not accept a new plan revision.
- Status and controls: the owner writes an atomic heartbeat projection. `watch`, dashboard and requirement views read it
  only when M1's database owns the requirement, reject malformed projections, and report stale active state after two
  minutes with the exact resume command. Pause/resume/stop route to M1; stop maps to cancel. No view reads `RUN.json`
  for a Scheduler authority.
- Execution: frozen plan → M1 authorization/state → M2 route → M3 provider process. The M1 owner loop explicitly calls
  `Wiring.drain_stream(attempt_id, run_id)` to move one bounded M3 batch through the stream adapter and M4 bridge.
- Monitoring: M4 commits normalized events/gaps, exposes read-only metric snapshots to M2, and retains incident delivery
  in a retryable outbox for the owner-controlled M1 cadence. There is no global or automatic poller.
- Verification/recovery: M1's approved order and M3 handoff flow to M6; M6 runs checks in bubblewrap and delivers a
  durable correlated verdict to M1. A rejected verdict enters M1 recovery, M5 recommends an action, M2 supplies a
  fresh assignment, and M3 can continue the captured snapshot before M6 verifies the new attempt.
- Shutdown: M6's dispatcher and workers finish before its store closes; then M5, M4 stream resources, and M3 close.
- Offline M4 recovery: stop all writers → create a no-overwrite full archive and integrity manifest → verify → prepare
  and verify a bounded disposable candidate. No command modifies the source or activates the candidate.

## Conventions & constraints
- M1 owns run state and verdict acceptance; M2 owns routing; M3 owns child processes/raw capture; M4 is advisory;
  M5 recommends recovery; M6 verifies. Contracts are versioned and package boundaries are checked in isolation.
- The legacy supervisor remains the default. Scheduler startup, its per-user login resume entry, M1 database and
  status projection are opt-in; `--no-autostart` suppresses/removes the per-user entry. Notifications are deduplicated
  against M1's latest state-changing audit sequence and cannot stop the owner loop.
- M4, M5, and M6 remain opt-in. M6 requires bubblewrap and a private persistent store; there is no unsandboxed
  fallback and no global activation.
- M3→M4 buffering is bounded and in-memory. Callers drain while the attempt runs and once after terminal output; frames
  still queued at process restart can be lost, while durable cursor/gap records make known loss visible.
- M4's 512 MiB store ceiling and retention policy are hard bounds. Recovery requires explicit SQLite temp directories;
  restore/activation remains an operator-managed action after candidate inspection.

_Last updated: 2026-10-16_
