# Observed baseline — 2026-10-15

| Code | Observed behavior | Gap addressed by M5 |
|---|---|---|
| `bt_scheduler_core/contracts.py` | contract 1.2.0; RecoveryPort.propose(FailureContext) returns RecoveryProposal | No revision/token/technical cause in FailureContext; enrich from authorized read views |
| `bt_scheduler_core/recovery.py` | pending RECOVERING tasks; retry/wait/block; default retry until budget; holds capped | Nonfinite infinity passes wait validation; add narrow validation regression |
| `bt_scheduler_core/scheduler.py` | ports outside state transactions; validates/apply proposal afterward; cancellation/stale state guard | Keep sole state authority; no signatures changed |
| `bt_scheduler_executor/model.py`, `classify.py` | structured cause/reset/terminal states; separate handoff manifest | Consume public describe, never raw output parsing |
| `bt_scheduler_executor/settle.py` | stop/sweep, capture and terminal event; failed capture preserves worktree | Block if capture is missing/failed |
| `bt_scheduler_executor_adapter.py` | wire(recovery=...) exists; previous retry starts at base/predecessors | Add opt-in M5 factory, same-task snapshot continuation and safe brief |
| `bt_scheduler_integrator.py` | integrates only accepted predecessor snapshots | Keep unchanged; failed/rejected task snapshot never becomes predecessor acceptance |
| `bt_scheduler_m4_wiring.py` | optional normalized monitoring, read-only M2 metrics, audit incident outbox | No recovery authority added to monitor |
| `bt_planner` + chain test support | frozen hash-approved plan and M2 persisted route fixtures | Extend genuine chain with failure/retry and independent verification |

Git baseline: branch feat/scheduler-m4-agent-monitor, HEAD 7d7f7dc; significant existing dirty M4/integration,
quota and Pictures documentation edits. No M5 package exists at baseline. Snapshot of working state inspected
using git status/diff before edits. Module worker isolated at /tmp/metodologia-m5-module.
