---
id: REQ-014
status: in-progress
created: 2026-10-14
track: deep
---
# REQ-014 — Scheduler M3 Agent Executor

## Problem & goal
M1 (`bt_scheduler_core`) decides which task is enabled, reserves capacity and hands an authorised, idempotent
`StartOrder` to an `ExecutionPort`; today only a simulator answers it. The methodology already has the pieces of a real
executor — provider argv builders and output normalisation (`bt_driver`), account profiles and the environment boundary
(`bt_profiles`), the model catalogue (`bt_agents`), durable worktrees (`bt_worktree`) — but nothing that turns an M1 order
plus an M2 route into a supervised, concurrent, restart-safe agent process whose work survives quota exhaustion,
connection loss, crashes and cancellation. M3 is that executor: it *runs* and *preserves*; it never decides who runs,
never judges success, never monitors streams for meaning and never chooses a retry.

**Success looks like:** an isolated module `bt_scheduler_executor` plugged into M1's `ExecutionPort` through one adapter,
that launches Claude Code, Codex and Gemini (Antigravity `agy`, the Gemini interface the methodology already supports)
in isolated worktrees, runs several attempts concurrently, emits technical events, keeps every artefact and a
recoverable handoff of the work (with or without commits) whatever way an agent ends, and survives its own restart,
proven by automated tests with simulated failures, plus opt-in, spend-bounded real-CLI smoke tests.

## Users / actors / stakeholders
- **M1 Scheduler Core** — authority over attempts, reservations, state and acceptance; calls `start/cancel/query`, ingests events.
- **M2 Decision Engine** (REQ-013, being implemented in parallel by another session) — owns the choice of
  provider/model/profile/effort and returns it as an opaque route reference in `StartOrder.executor`. M3 resolves it
  through a `RouteResolver` port and never edits M2 or the shared M1 contract.
- **M3 Agent Executor** — this requirement.
- **M4 Monitor** (future) — interprets streams and emits semantic events; M3 only exposes artefacts and technical events.
- **M5 Recovery** (future) — decides retry/switch; M3 only preserves the work and reports facts (cause class, reset time, handoff ref).
- **Independent verifier** — the only source of task completion (via M1's `VerificationPort`).
- David — operator; opts in, reviews artefacts and limits.

## Scope (in)
### US-1 (P1, Must) — Run an authorised order exactly once
As M1, I want `start(order)` to launch exactly one agent process for an idempotency key, so a retry, restart or duplicate
delivery never creates a second writer.
**Acceptance:** same key twice → one process, one worktree, second answer `duplicate`; same attempt id with a different
key or token is `rejected`; start delivered before and after an executor restart is still one process.

### US-2 (P1, Must) — Honour the M2 route, profile and model
As the operator, I want the agent launched with exactly the provider, model, effort and account profile M2 selected, so
quota and project policy are respected.
**Acceptance:** the executor resolves the route reference (unknown/stale/unresolvable → `rejected`, never a default
model); profile authorisation, work-only gate and launchable-provider checks run before any process; the child sees only
the profile's environment (other profiles' credentials removed); model must belong to the provider; no hard-coded model.

### US-3 (P1, Must) — Isolated concurrent worktrees
As M1, I want N attempts running at once without touching each other or the user's checkout.
**Acceptance:** each attempt gets its own git worktree+branch from a recorded base; concurrent attempts on one
repository never share a directory, index or branch; allocation races are serialised; nothing is written to the main
checkout; capacity beyond the executor's ceiling queues (bounded) instead of failing.

### US-4 (P1, Must) — Preserve the work, whatever happens
As the operator, I want the agent's work kept when it ends clean, fails, exhausts quota, loses its connection, times out,
is killed or is cancelled.
**Acceptance:** at every termination the executor writes a handoff: base sha, branch, head sha, committed commits,
uncommitted + untracked changes captured as a snapshot commit under a private ref and a binary-safe patch, log tail and
manifest — without altering the agent's branch, index or the base. A handoff exists for cases with commits only, dirty
tree only, both, and nothing (empty, stated as such). Reasoning of the agent is never claimed to transfer; the handoff is
code state + a brief a *different* agent can consume.

### US-5 (P1, Must) — Report facts, not verdicts
As M1/M4/M5, I want technical events with a classified cause so they can decide.
**Acceptance:** events map to M1's kinds (`execution_started`, `execution_finished`, `execution_failed`,
`execution_cancelled`, `heartbeat`) with deterministic ids (idempotent on replay), carrying cause class
(`quota_exhausted` with reset epoch when known, `connection_lost`, `agent_error`, `timeout`, `killed`, `incomplete_output`,
`start_failed`, `lost`), handoff reference and artefact paths. A clean exit is `execution_finished` = "the agent stopped",
never completion; the executor has no code path that completes a task.

### US-6 (P1, Must) — Cancel safely
As M1, I want `cancel(order)` to stop a running or queued attempt, idempotently and fenced by token.
**Acceptance:** queued → never spawned; running → SIGTERM to the process group, grace, SIGKILL, handoff preserved,
`execution_cancelled` emitted; a cancel after the attempt ended changes nothing; wrong token → `rejected`; duplicate cancel → `duplicate`.

### US-7 (P1, Must) — Reconcile after a restart
As M1, I want `query(attempt)` and the executor's own startup to tell the truth about processes that outlived or died
with their supervisor.
**Acceptance:** agent processes are owned by a detached shim that writes `exit.json`; after an executor restart: a live
shim is re-attached, an exited one is finalised from `exit.json` (events and handoff produced once), a vanished one with no
record becomes `lost` with the work preserved, a never-spawned accepted order is spawned once; unknown ids answer `not_found`.
Process identity is checked by start time so a recycled pid is never signalled.

### US-8 (P2, Should) — Real CLIs, opt-in and bounded
As the operator, I want a smoke test per available provider that proves the real command line is driven correctly, without
spending beyond a hard cap.
**Acceptance:** disabled unless `BITACORA_M3_REAL=1`; one tiny prompt per provider, short timeout, cheapest model, output
cap; results (or "provider unavailable") recorded in the report.

## Out of scope
- Choosing provider/model/profile (M2), reserving capacity or changing task/attempt state (M1), interpreting output
  semantically or detecting stalls beyond liveness (M4), retry/switch/continue policy (M5).
- Verifying acceptance criteria or completing tasks; transferring private reasoning between providers.
- Integrating/merging candidates into mainline, pushing, deploying, removing the user's files.
- Windows process control (documented limitation: POSIX sessions/process groups, `/proc` identity on Linux).
- Changing the Planificador schema, M1's state machine or contract version (M2 owns the v1.1.0 bump), any `RUN.json`.
- Standalone `gemini` CLI as a launch path (no profile/quota/catalogue support in the methodology); Gemini = Antigravity.

## Requirements
- R1. `bt_scheduler_executor` shall be an isolated module: standard library + itself only; no other `bt_*`; no methodology
  paths or provider knowledge. Providers, routes, briefs, workspaces and sinks arrive through ports defined in the module;
  one adapter `bt_scheduler_executor_adapter.py` is the only file importing it.
- R2. `start` shall be write-ahead idempotent: the order is persisted (SQLite WAL) before anything is spawned; the key is
  unique; attempt ids are unique; replays return the original receipt; conflicts are `rejected`.
- R3. Order validation shall precede any side effect: schema/types, route resolvable, provider launchable, model belongs
  to provider, effort valid for it, profile authorised for the project, repository known, base ref resolvable.
  Rejections are persisted with a stable code and never launch.
- R4. Each attempt shall run in its own worktree/branch allocated before spawn, under a per-repository lock for git
  administrative operations, with a durable journal; the agent's cwd is the worktree.
- R5. Agents shall run as children of a detached **shim** in a new session/process group; the shim enforces the timeout,
  caps and streams output (head cap + tail window, dropped-byte counter) and atomically writes `exit.json`
  (`returncode`, `signal`, `reason`, timestamps) and `shim.json` (pid, start-time identity) at start.
- R6. The executor shall bound concurrency (`max_running`), queue (`max_queued`), output size, handoff patch size,
  event backlog and heartbeat rate; exceeding the queue is a `rejected` receipt with code `queue_full`.
- R7. Every attempt end (clean/failed/limit/timeout/killed/cancelled/lost) shall produce a handoff (US-4) before the
  terminal event is delivered, and exactly one terminal event; terminal events are persisted write-ahead in an event
  outbox and delivered at-least-once with deterministic ids to an `EventSink`.
- R8. Output classification shall reuse the provider's own normaliser through the `AgentDriver` port (limit detection with
  reset epoch, terminal-event evidence, usage/cost as reported); connection loss uses a documented pattern set on failing
  exits only; `partial` (clean exit without end-of-turn evidence) is never `finished`.
- R9. `cancel` shall be fenced by token, idempotent and safe in every state (queued, spawning, running, terminal).
- R10. On construction the executor shall reconcile every non-terminal ledger row (US-7) before accepting new work;
  `query` shall reflect process reality, not just the ledger.
- R11. The child environment shall be built from the route's profile only (removals first, then sets); secrets never appear
  in the ledger, events, executor logs or handoff; prompt files hold task text only.
- R12. The prompt for the agent shall be built from the frozen plan's task (title, objective, acceptance criteria,
  verification, expected paths) through a `BriefSource` port; it shall forbid push/merge/secrets and allow commits on the
  attempt branch; any report file the agent writes is stored as a *claim*.
- R13. Artefacts shall live under `<state root>/attempts/<attempt-id>/` (order, route, brief, prompt, output.log, output.tail,
  exit.json, events.jsonl, handoff/…); history is never deleted by M3; worktree cleanup only on explicit operator action.
- R14. Real-CLI tests shall be opt-in (`BITACORA_M3_REAL=1`), with per-provider cap on timeout/model/output, and never run in the default suites.
- R15. Existing suites (planner, M1 core, methodology, packaging) shall stay green; historical runs and `RUN.json` untouched;
  the executor is explicit opt-in (no existing command changes behaviour).
- R16. Documentation: module README (boundaries, ports, states, events, error codes, limits), module convention update,
  decision record, report with measured evidence and limitations.

## Edge cases & errors
- Agent commits nothing / commits and leaves dirty files / writes only untracked files / deletes files / binary files /
  paths with spaces / detached-HEAD base → handoff correct in each.
- Quota message with rc≠0 or stream `is_error`, or Codex absolute-time message → `quota_exhausted`, reset epoch only when the driver found one.
- Network drop mid-run (rc≠0, connection patterns) → `connection_lost`; the same text with rc 0 does not mark failure.
- Provider binary missing or not executable → `start_failed` event + persisted reason.
- Shim killed (SIGKILL) with the agent alive → on reconcile the orphan agent group is found by its recorded identity and
  terminated before the handoff (no second writer), reported as `lost`.
- Executor crash after ledger write but before spawn / after spawn but before recording → recovered, one process.
- Duplicate/late `cancel`, `cancel` racing with natural exit → single terminal event, handoff once.
- Unwritable artefact dir → attempt `failed` with `artifact_error`; never a silent success.
- Two attempts for one task over time → distinct worktrees/branches; earlier handoffs untouched.
- Sink raising or slow → events stay in the outbox and are redelivered; the ledger is the truth.

## Constraints
- Python ≥ 3.10 target consistent with the repo; stdlib only inside the module; POSIX processes.
- No hosted-inference spend except opt-in smoke tests (bounded); no push/merge/deploy; the executor only commits inside
  attempt worktrees/refs it owns (snapshot commits under `refs/m3/…`).
- Subscription/quota facts come from M2/profile sources; M3 only reports what the process printed.
- Must not modify M1 (`bt_scheduler_core`), the planner or M2 files; M2 is being implemented in parallel (contract v1.1.0)
  and must not be disturbed. Another process modifies `bitacora/maros/.../RUN.json`: never touched.

## Priorities & phases
Must: US-1..US-7, module + adapter + tests, honest report. Should: US-8. Won't: M4/M5 logic, Windows, standalone gemini.

## Timeline & dependencies
Milestones: contracts/ledger/idempotency → workspaces & handoff → shim/runner/events/cancel → reconcile & failure matrix
→ adapter, drivers, route/brief/profile enforcement, M1 end-to-end → audit, real opt-in, docs, regressions.
Depends on M1 1.0.0 contracts (types converted by the adapter), `bt_driver`, `bt_profiles`, `bt_agents`, `bt_worktree`,
`bt_plan_adapter`. M2 not yet available → `RouteResolver` port with an interim `direct:` reference grammar and a hook for M2's lookup.

## Assumptions
- The `/goal` says SPEC/PLAN/PLAN.json "approved for M3"; none existed. Authored here under the owner's explicit request to
  implement M3 completely and the standing technical-autonomy instruction (same precedent as REQ-013); recorded as a ruling.
- Gemini = Antigravity `agy` (catalogue/profiles, decision D-004), not the unsupported `gemini` binary.
- M1's ExecutionPort carries no task text; the brief comes from the frozen PLAN.json via `BriefSource`, keyed by plan/revision/task.
- M1's `Ack`/`ExecutionStatus`/`Event` classes are core-owned; the adapter translates the module's own types so isolation holds.
- Technical events enter M1 through the adapter's sink (`SchedulerCore.ingest`) because M4 does not exist yet; the sink is a port.
- Clean exit with evidence = `execution_finished`; Codex has no end-of-turn marker, so its clean exit with output counts
  (M1 still requires an independent verdict).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
| Constraints | Covered |
| Priorities | Covered |
| Success metrics | Covered (R-level tests + report) |
