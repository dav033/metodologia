---
req: REQ-014
status: approved
created: 2026-10-14
---
# Plan — REQ-014 — Scheduler M3 Agent Executor

## Approach
Build `bt_scheduler_executor` as a standard-library-only sibling module (convention `references/modules.md`). Its public
API is an `AgentExecutor` with the three M1 execution operations (`start`, `cancel`, `query`) expressed in the module's own
types, a durable SQLite ledger/outbox, a per-attempt artefact directory, and five ports it never implements itself:
`RouteResolver` (M2 route reference → provider/model/profile/effort), `BriefSource` (frozen plan task → prompt text),
`AgentDriver` (provider argv/env + output classification), `WorkspaceManager` (worktree allocation) and `EventSink`.
A single methodology adapter `bt_scheduler_executor_adapter.py` wires the ports to `bt_driver`, `bt_profiles`, `bt_agents`,
`bt_worktree` and `bt_plan_adapter`, translates the module's types to M1's `Ack`/`ExecutionStatus`/`Event`, and is the only
importer of the module.

Agents never run as direct children of the executor: a small detached **shim** (new session) owns the agent process
group, enforces the timeout, streams capped output and atomically writes `exit.json`. That makes restart reconciliation
possible: the executor can re-attach, finalise from `exit.json`, or declare `lost` after checking process identity.
Work preservation is independent of agent cooperation: a handoff snapshots committed + uncommitted + untracked state with
a temporary index and `commit-tree` into a private ref, never touching the attempt's branch or index.

## Global constraints
- Do not modify `bt_scheduler_core`, `bt_planner`, any M2 file (`bt_scheduler_decision*`) or any `RUN.json`; M2 runs in parallel in another session.
- No commit/push/merge/deploy by the executor outside attempt worktrees and `refs/m3/*`; no hosted-inference spend outside opt-in bounded smoke tests.
- Module imports only the standard library and itself; M3 never completes a task, never selects a model, never retries.
- Secrets never persisted; bounded memory/disk/time/concurrency everywhere; POSIX only (documented).
- Do not commit repo changes (the owner has not asked); record everything in the bitácora.

## Tasks

### M1 — Contracts, ledger and idempotent start
- [ ] T1 — Module skeleton, README stub, own types (`StartRequest`, `Route`, `Receipt`, `AttemptStatus`, `TechnicalEvent`), error codes, `Config` limits, ports (`RouteResolver`, `BriefSource`, `AgentDriver`, `WorkspaceManager`, `EventSink`) and boundary/import/no-AI tests · repo: skill · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_boundaries bt_scheduler_executor.tests.test_contracts` · covers: R1, R16
- [ ] T2 — SQLite WAL ledger: attempts keyed by unique attempt id and idempotency key, state machine, write-ahead event outbox, concurrent-writer safety · repo: skill · after: T1 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_ledger` · covers: R2, R7, R13
- [ ] T3 — Order validation and idempotent `start`/duplicate/conflict/`queue_full` semantics with persisted rejections before any side effect · repo: skill · after: T2 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_start` · covers: R2, R3, R6

### M2 — Isolated workspaces and recoverable handoff
- [ ] T4 — `GitWorkspaces`: per-attempt worktree+branch from a resolved base, per-repository lock, durable journal, concurrency-safe allocation · repo: skill · after: T1 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_workspace` · covers: R4
- [ ] T5 — Handoff snapshot: commits-only, dirty-only, both, empty, untracked, deleted, binary, spaces; snapshot commit under `refs/m3/`, binary patch, manifest, branch/index untouched, caps · repo: skill · after: T4 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_handoff` · covers: R7, R13, US-4

### M3 — Process supervision, events and cancellation
- [ ] T6 — Detached shim: new session, timeout, capped head+tail output, atomic `shim.json`/`exit.json`, signal forwarding, process identity helpers · repo: skill · after: T1 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_shim` · covers: R5, R6
- [ ] T7 — `AgentExecutor` run loop: queue + bounded workers, prepare→allocate→spawn, watcher, started/heartbeat/finished/failed events with deterministic ids, outbox delivery and redelivery · repo: skill · after: T3, T5, T6 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_executor bt_scheduler_executor.tests.test_events` · covers: R2, R5, R7, R8
- [ ] T8 — Failure classification matrix (clean, quota with/without reset, connection lost, agent error, timeout, killed, incomplete output, start failed) via the driver port and documented patterns · repo: skill · after: T7 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_classification` · covers: R8, US-5
- [ ] T9 — Safe cancellation in every state (queued, spawning, running, terminal, wrong token, duplicate, race with exit) with TERM→KILL grace and handoff · repo: skill · after: T7 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_cancel` · covers: R9, US-6

### M4 — Reconciliation and resilience
- [ ] T10 — Startup reconciliation and `query` from reality: re-attach live shim, finalise from `exit.json`, orphan-agent termination by identity, never-spawned accepted order, unknown id, pid-reuse safety · repo: skill · after: T8, T9 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_reconcile` · covers: R10, US-7
- [ ] T11 — Crash-at-every-step and fault-injection tests (kill executor after ledger/allocation/spawn/terminal, sink failure, disk errors), exactly-one-process and exactly-one-terminal-event invariants · repo: skill · after: T10 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_resilience` · covers: R2, R7, R10, US-1
- [ ] T12 — Concurrency isolation tests: N parallel attempts per repo and across repos, no shared dir/branch/index, lock contention, output isolation, queue bound · repo: skill · after: T7 · verify: `cd skill/scripts && python -I -m unittest bt_scheduler_executor.tests.test_concurrency` · covers: R4, R6, US-3

### M5 — Methodology adapter and M1 integration
- [ ] T13 — Adapter: M1 `Ack`/`ExecutionStatus`/`Event` translation, `RouteResolver` (interim `direct:` grammar + optional M2 lookup hook), `AgentDriver` over `bt_driver`/`bt_profiles`/`bt_agents` (authorise, gate_cwd, launchable, model↔provider, env boundary, Gemini=agy), `BriefSource` from the frozen plan, `WorkspaceManager` over `bt_worktree` · repo: skill · after: T7 · verify: `cd skill/scripts && python -m unittest tests.test_scheduler_executor_adapter` · covers: R1, R3, R11, R12, US-2
- [ ] T14 — End-to-end through the real `SchedulerCore` with fake provider binaries (3 providers, parallel plan, failure/quota/cancel/restart scenarios) and an independent stub verifier; legacy/historical runs byte-identical · repo: skill · after: T13, T10 · verify: `cd skill/scripts && python -m unittest tests.test_scheduler_executor_integration tests.test_scheduler_integration` · covers: R2, R7, R10, R15, US-1, US-5

### M6 — Audit, real CLIs, documentation and closure
- [ ] T15 — Opt-in bounded real-CLI smoke tests per available provider (`BITACORA_M3_REAL=1`), skipped by default · repo: skill · after: T13 · verify: `cd skill/scripts && python -m unittest tests.test_scheduler_executor_real` · covers: R14, US-8
- [ ] T16 — Independent spec/standards/adversarial reviews; fix every verified finding with a regression test · repo: skill · after: T11, T12, T14, T15 · verify: `cd skill/scripts && python -I -m unittest discover -s bt_scheduler_executor/tests` · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13
- [ ] T17 — README, `modules.md` section, packaging (`pyproject.toml`), decision record, full regression suites, final report with evidence and limitations · repo: skill · after: T16 · verify: `cd skill/scripts && python -m unittest tests.test_scheduler_executor_integration tests.test_scheduler_integration tests.test_plan_integration tests.migration.test_package_install` · covers: R15, R16

## Verification
1. `cd skill/scripts && python -W error::ResourceWarning -I -m unittest discover -s bt_scheduler_executor/tests` — module suite (boundaries, lone-copy isolation, CLI, every scenario above).
2. `cd skill/scripts && python -W error::ResourceWarning -m unittest tests.test_scheduler_executor_adapter tests.test_scheduler_executor_integration tests.test_scheduler_integration tests.test_plan_integration` — adapter + M1 end-to-end + regressions.
3. `cd skill/scripts && python -W error::ResourceWarning -m unittest discover -s bt_scheduler_core/tests` and `-s bt_planner/tests` — untouched modules still green.
4. `cd skill/scripts && python -m unittest discover -s tests` and `tests.migration.test_package_install` — methodology and packaging.
5. Opt-in `BITACORA_M3_REAL=1 python -m unittest tests.test_scheduler_executor_real` — real Claude/Codex/Antigravity with caps; results recorded verbatim.
6. `git diff --check`, `git status`: only M3 files + docs changed by this requirement; M1/M2/planner sources and every `RUN.json` unchanged by it.

## Rulings
- Plan authorship: the owner's `/goal` presupposed an approved M3 SPEC/PLAN/PLAN.json that did not exist; written here under the same explicit request/autonomy precedent as REQ-013 and approved on launch of the owner's goal.
- Ports: no sibling type crosses the module boundary; the adapter converts. This keeps M3 testable alone and independent of M1's pending contract bump by M2.
- Interim route grammar `direct:<provider>/<model>[@<profile>][#<effort>]` exists only so M3 can run before M2 exists; `route:<id>` is delegated to M2's lookup when present; anything else (including M1's FIFO label `local`) is `route_unresolvable` and rejected — M3 never picks a default.
- Gemini = Antigravity `agy` (D-004). Standalone `gemini` CLI is not supported.
- Shim over direct child: only way to keep exit status and output across an executor restart.

## Progress log
- 2026-10-14 — SPEC and PLAN written after inspecting M1 contracts (`contracts.py`, `dispatch.py`, adapter), `bt_driver`, `bt_worktree`, `bt_profiles`, `bt_agents`, `bt_delegate`. No source code changed yet.
- 2026-10-14 plan APPROVED (owner instruction: the /goal to implement M3 completely with technical autonomy; the approved SPEC/PLAN it presupposed did not exist and were written here)
