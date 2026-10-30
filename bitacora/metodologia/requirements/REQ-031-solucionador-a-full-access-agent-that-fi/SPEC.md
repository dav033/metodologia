---
id: REQ-031
status: in-progress
created: 2026-10-29
track: standard
---
# REQ-031 — Solucionador: a full-access agent that fixes blocked runs at their origin

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Every blocked task of a durable run is a system error (owner's mandate, 2026-10-29). Today the ladder stops early:
known rules (`bt_block_diagnosis`) → a cheap read-only diagnosis (`bt_block_agent`) → D-167 healing answers
`retry`/`retry_with_note` once per failure signature. Everything else — a repeated failure, a defect in metodologia's
own code, a plan defect, an engine error — waits for a person (on 2026-10-29 that person was an operator Claude
session doing by hand: find the origin, fix it in the system, regression, backup, integrate, restart, record a rule).

Goal: the system launches that operator itself. The **Solucionador** is a Claude Opus session with full access that
receives the run's context and decisions, finds the origin of the block, fixes it where it lives, integrates the fix,
answers the decision and leaves a rule (test/guard + decision record) so the same block cannot come back.

**Success looks like:** on pictures REQ-021, a block that D-167 leaves for the owner is picked up by a Solucionador
within one maintenance pass; it ends with the decision answered (or a precise owner question when the fix needs an
irreversible/external action), a D-NNN entry, a regression test, and — when it changed metodologia — a merge on
`main` that passed the full regression, with the units restarted and smoke-checked.

## Users / actors / stakeholders
- Owner (David): wants no blocked task waiting for him; reads what the Solucionador did in the panel/bitácora.
- Durable engine (`bt_durable.service` maintenance pass): detects and launches.
- Solucionador (Claude Opus, tmux `bit-<project>-<REQ>-solver`): diagnoses and fixes.
- Run Planner: receives plan changes from the Solucionador.

## Scope (in)
### US-1 (P1, Must) — Escalation to the Solucionador
As the owner, I want a block the cheaper rungs could not resolve to start a Solucionador automatically.
**Acceptance:**
- Given an open decision that D-167 left to the owner (limit reached, low confidence, diagnosis failed, plan blamed,
  option not offered), when the next maintenance pass runs, then a Solucionador session starts for that decision.
- Given the same failure signature reaching a second round, or a task with no state change for
  `solver.stuck_minutes` (default 45) while its workflow is PENDING, or a run workflow in ERROR, then it starts too.
- Given a Solucionador already working on that run, no second one starts; the new trigger is queued in its inbox.

### US-2 (P1, Must) — Full context
As the Solucionador, I start with everything an operator would read: the brief (trigger, decision, failure evidence,
attempt history, diagnosis), the run status, paths to SPEC/PLAN/PLAN.json, the project's and metodologia's
`DECISIONS.md`, recent day logs, the engine journal command, and the integration procedure.

### US-3 (P1, Must) — Fix at the origin, integrate, restart
As the owner, I want a fix in metodologia's code to reach production on its own, safely.
**Acceptance:**
- The Solucionador works in its own git worktree/branch, never in `~/dev/metodologia`'s checkout.
- Integration = repo-owned `scripts/regress.py` full regression (only the known-flaky allowlist may fail) → if engine
  code changed: DBOS backup + previous release noted → `merge --no-ff` in a separate worktree → `merge --ff-only` in
  the live checkout → push → restart `bt-durable`/`bitacora-web` as needed → smoke. A failed regression never
  integrates; the branch stays and the owner is told.
- One integration at a time machine-wide (lock), so two Solucionadores never race on `main`.

### US-4 (P1, Must) — Plan changes via the Planner
A plan defect is sent to the run's Planner as a precise change request; the Planner revises, validates and freezes a
new revision; the Solucionador follows it up to `stage join`. Acceptance criteria are never weakened.

### US-5 (P1, Must) — A rule so it does not come back
Every fix leaves: a regression test (or guard) reproducing the block, a `D-NNN` in metodologia's `DECISIONS.md` (or
the project's, for a project defect), an activity line in the run's panel, and a report in
`RUN.solver/<id>/REPORT.md` (trigger, origin, fix, commits, rule, how the decision was answered).

### US-6 (P2, Should) — Visible and controllable
The panel shows a running Solucionador (task, trigger, since, tmux name) and its report; config `solver.enabled`
turns the rung off.

## Out of scope
- Replacing D-167 or the diagnosis agent: they stay as cheaper rungs before the Solucionador.
- Fixing the user's external services or anything needing owner credentials/2FA/Cloudflare challenges.
- Auto-approving design directions or subplan confirmations (owner gates).

## Requirements
- R1. When the healing pass leaves a decision for the owner, the engine shall start (or queue to) a Solucionador.
- R2. When a failure signature repeats across rounds, a task makes no progress for `solver.stuck_minutes`, or a run
  workflow is in ERROR, the engine shall do the same.
- R3. At most one Solucionador per run and at most `solver.max_concurrent` (default 1) machine-wide; each trigger key
  (run, task, request, round) launches at most once; `solver.max_per_task` (default 3) bounds repeats.
- R4. The Solucionador shall run as Claude Opus, effort high, `--dangerously-skip-permissions`, on an account the
  router ranks first for role `solver` that runs unattended and has quota; Codex (`danger-full-access`) if none.
- R5. The Solucionador shall integrate metodologia changes only through the repo-owned integration script (regression,
  backup when engine code changed, ff-only, push, restart, smoke) under a machine-wide integration lock.
- R6. Changes to the order of steps in `bt.run`/`bt.task` shall go behind `DBOS.patch`.
- R7. The Solucionador shall never delete user data, rewrite published history, bypass the permission classifier,
  weaken an acceptance check, approve owner gates, or claim exactly-once.
- R8. When the fix needs an irreversible, external or security-sensitive action, the Solucionador shall stop and
  leave one precise question for the owner (panel + notification) instead of acting.
- R9. Each Solucionador shall finish by writing `REPORT.md` and a machine-readable `result.json`
  (`fixed|answered|asked_owner|gave_up`); a session that ends or exceeds `solver.max_minutes` (default 120) without
  one is marked `gave_up` and the decision is surfaced to the owner.
- R10. Every action shall be recorded in the run's activity (Spanish, panel) and its bitácora (English).

## UI / design contract (optional)
- UI scope / users: owner only; one card in the existing run panel (no new page). Not a UI subplan.

## Edge cases & errors
- Quota runs out mid-session → restarted on another account with the same brief + its notes (Planner pattern).
- The decision moves on while the Solucionador works (someone answered) → it finishes its fix but does not answer.
- Its own fix breaks the engine → smoke fails → it restores the noted previous release and reports.
- The Solucionador itself blocks (e.g. waits on a prompt) → `max_minutes` watchdog kills it and surfaces the trigger.
- Trigger storm (many tasks block at once) → one session per run handles them in order via its inbox.

## Constraints
- `~/bitacora` is a symlink into `~/dev/metodologia/bitacora` (live state): never merge/stash/reset/checkout there.
- Regression allowlist of known failures: test_plan_boundary, test_real_designer_kit, test_recovery_views,
  test_remote_panel (to be moved into the repo-owned script's config).
- Launch logic lives outside the workflows (maintenance pass), like D-167.

## Priorities & phases
MVP (Must): US-1..US-5. Then US-6.

## Timeline & dependencies
- Depends on D-165/D-166 and D-167/D-168 being on `main` (in progress today).

## Assumptions
- Claude accounts with `skipDangerousModePermissionPrompt` exist (claude-work, claude-luis) — same as the Planner.
- The regression and backup scripts now in a session scratchpad can be moved into `skill/scripts/` unchanged in spirit.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Confirmed |
| Users / actors | Confirmed |
| Scope | Confirmed |
| Out of scope | Assumed |
| Flows & behavior | Confirmed |
| Edge cases | Assumed |
| Acceptance criteria | Assumed |
| Constraints | Confirmed |
| UI / design direction | Assumed |
| Priorities & phases | Assumed |
| Timeline | Assumed |

## Clarifications
### Round 1 — 2026-10-29
- Q: How far does it go alone with metodologia code? → A: Integrates and restarts (regression + backup + ff-only + push + restart + smoke).
- Q: May it change the plan? → A: Via the run's Planner (new frozen revision; never weakens acceptance).
- Q: When does it launch? → A: Escalation ladder: rules → D-167 retry → Solucionador on repeat, system/plan blame or stuck.
- Q: Which agent? → A: Claude Opus (bypass permissions, tmux, account by quota); Codex as fallback.
