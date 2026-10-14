---
id: REQ-011
status: ready
created: 2026-10-14
track: standard
---
# REQ-011 — Scheduler Core M1: isolated deterministic module `bt_scheduler_core`

## Problem & goal
`PLAN-SCHEDULER-CORE-M1.md` (SCH-CORE-001, repo root) defines M1, the deterministic core of the Scheduler: it loads an
approved `PLAN.json`, resolves the task DAG, runs a transactional state machine, reserves capacity/resources atomically,
dispatches through ports, ingests events idempotently and reconciles after a restart. The owner's `/goal`: implement it
**as an independent module, easily testable and uncoupled** (same convention as `bt_planner`, `references/modules.md`).

**Success looks like:** `skill/scripts/bt_scheduler_core/` runs and passes its own suite alone (AST boundary test, lone-copy
isolation test, end-to-end CLI), covers SC-AC01..SC-AC20 with reproducible evidence, uses no AI, and the methodology
reaches it through one adapter without changing existing `RUN.json` history.

## Users / actors / stakeholders
- Owner (David); future sibling modules M2 Decision Engine, M3 Executor, M4 Monitor, M5 Recovery (they implement the ports).

## Scope (in)
The plan's SC-H1..SC-H5 / SC-T01..SC-T15, verbatim: plan loader (hash-bound approval), DAG + eligibility, task/attempt/
reservation state machines, transactional repository (in-memory + SQLite WAL) with an audit log, atomic reservations with
fencing, outbox dispatch, event loop without busy waiting, restart reconciliation, mock-able ports, simulators, CLI,
docs, one methodology adapter, compatibility tests over historical fixtures (read-only).

## Out of scope
Everything in the plan's §3.2 (model choice, real process launch, log parsing, retry strategy, replanning, dashboards,
distributed infra, deploys). No AI SDKs, prompts or provider names in the package.

## Requirements
- R1. The module imports only the standard library and itself; it names no other `bt_*`, bitácora path, `RUN.json`, env var.
- R2. A plan loads only when the caller supplies the sha256 of the approved revision; any mismatch, malformed JSON, bad
  DAG or unsupported major creates no state and no attempt (SC-AC03/04).
- R3. A task is eligible only when every `after` task is `completed` with an accepted verdict (SC-AC05); order in the plan
  or the milestone never adds dependencies.
- R4. At most one writer attempt per task; reservation is one atomic transaction over task, capacity and resources
  (SC-AC07/08); fencing tokens invalidate stale attempts (SC-AC12).
- R5. `completed` only through an independent verdict correlated to the current attempt; an agent's "finished" event
  only moves the attempt to `verifying` (SC-AC10).
- R6. Events are idempotent by `event_id`, stale/invalid ones are recorded and change nothing (SC-AC09/11/12).
- R7. Reservation + dispatch intent are persisted before any port call; delivery is idempotent; after a crash M1
  reconciles through the ports and never infers death from a PID/heartbeat (SC-AC13/15).
- R8. A failed or blocked task never stops independent branches (SC-AC14); the run is `completed` only when every task
  is completed (SC-AC17).
- R9. Unavailable or invalid M2/M5 answers leave state intact and fall back to explicit deterministic policies (SC-AC16).
- R10. Every transition, reservation and dispatch writes an audit entry with plan_id, task_id, attempt_id, kind, time (SC-AC19).

## Edge cases & errors
Duplicate, late, reordered events; lease expiry (not proof of death); crash between reserve and dispatch; executor
unreachable during reconcile (attempt `uncertain`, no second writer); approved plan replaced by another revision;
historical `RUN.json` must stay byte-identical.

## Constraints
Python ≥3.12 stdlib only; SQLite WAL is the only persistence; `PLAN.json` read-only; no push/deploy.

## Priorities & phases
All of SC-H1..SC-H5 are Must; milestones follow the plan.

## Timeline & dependencies
Depends on REQ-009/REQ-010 (`PLAN.json` contract, done).

## Assumptions
- The owner's `/goal` is the approval of the written plan; no extra interview (the plan is the spec).
- The module is a methodology module (`bt_scheduler_core`), not a separate repo/project, mirroring D-020.
- Plan §12 open questions are answered against the real code in `REPORT.md` (inspection by an explorer subagent).
- Approval of a plan = caller-provided sha256 of the frozen revision file (the planner's manifest already records it);
  "any valid JSON is approved" is explicitly rejected.
- Default configuration is conservative: `max_parallel_tasks=1`, `max_attempts=1` (no retry unless configured).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered (plan §5) |
| Edge cases | Covered |
| Acceptance criteria | Covered (SC-AC01..20) |
| Constraints | Covered |
| Priorities & phases | Covered |
| Timeline | Covered |

## Clarifications
- 2026-10-14 `/goal`: "implementa este plan, manéjalo como un módulo independiente fácilmente testeable y sin acoplamiento".
