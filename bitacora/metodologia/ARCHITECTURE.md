# metodologia — Architecture

_Living document: how the thing is built (or, for business projects, how the process/organization works).
Edit in place; record the *why* of changes in DECISIONS.md._

## Overview
The methodology Scheduler composes the Planner and four isolated modules through methodology adapters. It remains
opt-in: the M1–M3 execution path is unchanged unless a caller supplies a separate M4 store and drains each attempt's
bounded stream from its owning M1 loop. M4 records normalized evidence and returns advisory metrics or incidents;
it never owns scheduling, provider processes, or recovery decisions.

## Components / actors
| Name | Responsibility | Where (path / owner) |
|---|---|---|
| Planner | Frozen plan contract and task order | `skill/scripts/bt_planner/` → `bt_plan_adapter.py` |
| M1 Scheduler Core | Run authorization, task/attempt state, and projection | `skill/scripts/bt_scheduler_core/` → `bt_scheduler_adapter.py` |
| M2 Decision | Quota-aware provider/profile/model route selection and route metrics | `skill/scripts/bt_scheduler_decision/` → `bt_scheduler_decision_adapter.py` |
| M3 Executor | Provider CLI process, isolated worktree, lifecycle, and bounded FIFO stream | `skill/scripts/bt_scheduler_executor/` → `bt_scheduler_executor_adapter.py` |
| M4 Monitor | Normalized events, gaps, metric history, and audit incident outbox in its own SQLite WAL store | `skill/scripts/bt_scheduler_monitor/` → `bt_scheduler_monitor_adapter.py` |
| M3→M4 bridge | Converts bounded FIFO frames to allowlisted M4 records and acknowledges only after durable commit | `bt_scheduler_stream_adapter.py`, `bt_scheduler_m4_stream_bridge.py`, `bt_scheduler_m4_wiring.py` |

## Data & integrations
- The frozen Planner plan is the input to M1; M2 persists route decisions consumed by M3. M1, M2, and M3 retain their
  own stores and authority.
- M4 uses a separate project-owned SQLite WAL database. It stores allowlisted normalized evidence, never raw provider
  output. M3 frame/gap cursors advance only with the corresponding M4 commit.
- M2 reads M4 metric history through a read-only port. M4 incidents reach M1 as versioned, idempotent audit references;
  M1 alone changes task/attempt state.

## Key flows
- Execution: frozen plan → M1 authorization/state → M2 route → M3 provider process. The M1 owner loop explicitly calls
  `Wiring.drain_stream(attempt_id, run_id)` to move one bounded M3 batch through the stream adapter and M4 bridge.
- Monitoring: M4 commits normalized events/gaps, exposes read-only metric snapshots to M2, and retains incident delivery
  in a retryable outbox for the owner-controlled M1 cadence. There is no global or automatic poller.
- Offline M4 recovery: stop all writers → create a no-overwrite full archive and integrity manifest → verify → prepare
  and verify a bounded disposable candidate. No command modifies the source or activates the candidate.

## Conventions & constraints
- M1 owns run state; M2 owns routing; M3 owns child processes/raw capture; M4 is advisory; M5 recovery policy remains
  future work. Contracts are versioned and package boundaries are checked in isolation.
- M3→M4 buffering is bounded and in-memory. Callers drain while the attempt runs and once after terminal output; frames
  still queued at process restart can be lost, while durable cursor/gap records make known loss visible.
- M4's 512 MiB store ceiling and retention policy are hard bounds. Recovery requires explicit SQLite temp directories;
  restore/activation remains an operator-managed action after candidate inspection.

_Last updated: 2026-10-15_
