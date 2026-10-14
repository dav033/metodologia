---
id: REQ-012
status: in-progress
created: 2026-10-14
track: quick
---
# REQ-012 — Planner phase 1 closure: strict PLAN sync, launch gate, evidence, real planning trials

Source: owner's `/goal` of 2026-10-14 closing PLAN-PLANNER-001 (`PLAN-SUPERIA-FASE-1-PLANES.md`) after REQ-009/010.
No interview: the goal states scope, constraints and acceptance; ambiguities were settled with the defaults below.

## Problem & goal
The planner contract (REQ-009/010) accepts plans whose PLAN.md and PLAN.json disagree on anything but ids, milestones
and `after`; launches that bypass `bt_launch` (foreground) do not validate or freeze; classifications are bare labels.
A future scheduler would trust all three. Goal: a planner whose output a scheduler can rely on.

**Success looks like:** the five points of the goal verified by automated tests and by real planning trials.

## Scope (in)
- US-1 PLAN.md ↔ PLAN.json sync: duplicate ids (both sides) and contradictions in titles, repositories, dependencies and
  verifications are rejected.
- US-2 Every launch path validates and freezes exactly the approved revision.
- US-3 Classifications carry justification and evidence (complexity, scope, duration, risk, coupling, confidence).
- US-4 Real planning trials with representative requirements, judged on quality, coherence, dependencies, classification.
- US-5 Suites, docs, plan state and acceptance criteria updated.

## Out of scope
The scheduler and its modules (`bt_scheduler_core`), historical `RUN.json`, publishing/deploying, pushing, migrating
historical plans (REQ-013/015/016 stay as they are; compat is read-only).

## Requirements
- R1. If PLAN.md defines a task id twice, or PLAN.json does, the plan shall be rejected naming both lines.
- R2. If a task's title, `repo`, `after`, stated `verify` or milestone title in PLAN.md differs from PLAN.json, `check`
  shall fail naming task and field. What PLAN.md does not state is not a contradiction.
- R3. When a plan is approved through `plan approve`/web/handoff, PLAN.json shall be validated and frozen at that moment.
- R4. Standard, web, handoff, foreground and the new-run entry shall all refuse a plan that is invalid, unapproved
  (unless an explicit `--force`) or different from the latest frozen revision; none shall freeze an unreviewed edit.
- R5. From schema 1.1.0 each task shall carry per-dimension justification and typed evidence; weak, placeholder,
  duplicated or assumption-only (for `confidence: high`) evidence shall be an error; schema 1.0.0 documents keep loading.
- R6. Tasks that nothing orders and that share a path or resource shall not be classified `coupling: low`.
- R7. Existing frozen revisions, `RUN.json` files and the Scheduler shall be unchanged.

## Constraints
Stdlib only inside `bt_planner`; methodology reaches it only through `bt_plan_adapter.py`; no push, no publish.

## Assumptions
- Manual `status: approved` edits have no approval record; the first launch freezes what it validates (documented gap,
  closed by `plan approve`/`plan-json freeze`).
- Evidence is judged textually (structure, strength, existence of referenced files/specs/tasks), never by a model.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Scope / out of scope | Covered |
| Acceptance criteria | Covered (R1–R7) |
| Constraints | Covered |
