---
id: REQ-026
status: in-progress
created: 2026-10-18
track: standard
demo: true
---
# REQ-026 — DEMO — Illustrative plan with every plan feature (test only)

> DEMO requirement. It exists only so the plans pages have a complete, half-finished plan to display.

## Problem & goal
The owner wants to see what a plan looks like when it is half done: several milestones, tasks in every state, dependencies, retries and blocked work.

**Success looks like:** the plans pages show milestones, tasks, difficulty, models, accounts and attempt history for this plan.

## Users / actors / stakeholders
- The owner, who reviews the web UI.

## Scope (in)
### US-1 (P1, Must) — See a plan in every state
As the owner, I want a sample plan with completed, running, blocked and pending work so that I can judge the plans pages.
**Acceptance:**
- Given the sample plan, when I open it, then I see four milestones and nine tasks with their states.

## Out of scope
- Running the plan. No agent executes it; its run state is simulated.

## Requirements
- R1. When the plan is opened, the system shall list its milestones and tasks with state and difficulty.
- R2. When a task was retried, the system shall show each attempt with its model and account.
- R3. If a task is blocked, then the system shall show it as blocked and keep its dependants pending.
- R4. While the run is paused, the system shall show no task as running except the one that was in progress.

## Edge cases & errors
- A plan whose tasks are all pending shows 0 of N done.

## Constraints
Illustrative only; delete when no longer needed.

## Priorities & phases
MVP only.

## Timeline & dependencies
None.

## Assumptions
The scenario (a theme toggle and a plan health line) is invented to give the tasks plausible content.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
