---
req: REQ-031
status: in-progress
created: 2026-10-29
---
# Plan — REQ-031 — Solucionador: a full-access agent that fixes blocked runs at their origin

## Approach
A new rung `bt_durable.solver` on the engine's maintenance pass, right after D-167 healing and outside the workflows:
it collects triggers (decisions healing left for the owner, repeated signatures, stuck tasks, ERROR workflows), writes
a brief + context bundle to `RUN.solver/<id>/`, and starts one Claude Opus session per run in tmux
(`bit-<project>-<REQ>-solver`), reusing the Planner's launcher pattern (`bt_agent_terminal`: unattended account by
the router, Codex fallback, restart on quota). The session follows a versioned prompt (`agents/solver.md`) and does
production changes only through a new repo-owned `skill/scripts/bt_integrate.py` (regression + backup + ff-only +
push + restart + smoke, under a machine-wide lock) — the same procedure operators follow today by hand.

## Global constraints
- Never merge/stash/reset/checkout in `~/dev/metodologia` (live bitácora); ff-only there.
- Sequence changes in bt.run/bt.task behind DBOS.patch; no exactly-once claims; no user-data deletion.
- Launching happens in the maintenance pass, never inside a workflow step.
- Acceptance checks are never weakened; owner gates are never auto-approved.

## Tasks
- [ ] T1 — Repo-owned integration: move regress.py + dbos_backup.py into `skill/scripts/` (`bt_regress.py`, `bt_integrate.py`: worktree merge --no-ff → ff-only live → push → restart units by changed paths → smoke; machine-wide lock; known-flaky allowlist in config) · verify: `python -m unittest test_integrate` · covers: R5, US-3
- [ ] T2 — Solver role + prompt: `agents/solver.md` (mandate, context reading order, rules R6–R8, report/result contract), router role `solver`, installer · after: T1 · verify: `python -m unittest test_install_agents test_role_routing` · covers: R4, R7, R8, US-2
- [ ] T3 — Triggers + launcher `bt_durable/solver.py`: triggers from healing outcomes, repeated signature, stuck task, ERROR workflow; per-run single session + inbox; once per key; limits; brief/context bundle; tmux launch via `bt_agent_terminal`; quota restart; `max_minutes` watchdog; `result.json` handling · after: T2 · verify: `python -m unittest test_durable_solver` · covers: R1–R3, R9, US-1
- [ ] T4 — Wire into `service._heal_decisions` (healing returns "left for the owner" outcomes to the solver) + config keys `solver.*` · after: T3 · verify: `python -m unittest test_healing_durable_decisions test_durable_solver` · covers: R1, R10
- [ ] T5 — Panel card (running solver, trigger, since, report link) + activity lines · after: T3 · verify: `python -m unittest test_durable_panel` · covers: US-6, R10
- [ ] T6 — Docs: modules.md §Solver, execution.md ladder, D-NNN · after: T4 · verify: manual review · covers: US-5

## Verification
Full regression of the branch; then a live smoke on pictures REQ-021: inject a decision healing leaves for the owner on
a disposable test run (not REQ-021's real tasks), watch the solver start in tmux, read its brief, and see it write
`result.json`; check one session per run and once per key.

## Rulings

## Progress log
