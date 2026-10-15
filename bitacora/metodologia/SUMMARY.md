# metodologia — Summary

## Purpose
The user's own working method, as a skill for Claude Code and Codex: requirements by prioritized rounds → approved
plan → autonomous executor; engineering standards; subagent roles; per-project bitácora; local web UI; tools and infra
registry. The repo `github.com/dav033/metodologia` (private) holds `skill/`, `evals/`, `install.py` and bitácora copies
(D-008, D-009, D-011), and since D-012 the pictures bitácora itself. The rest of the live bitácora is `~/bitacora`.

## Current state
- 2026-10-15 independent Codex audit of the supplied planner copy challenges phase-1 acceptance: C1/C2/C3/C5 have executed counterexamples; C4 legacy bytes/hash holds. Delegation D-20261015-084652-b103 RESULT.json links full reproductions; P-023/P-026 track triage against the live tree. Audit suite: 192/201 passed, 9 failures from missing scenario fixtures; no source fixes or commits.
- 2026-10-14 REQ-009 + REQ-010 done: planner contract `PLAN.json` (D-019) now an isolated module `skill/scripts/bt_planner/` reached only through `bt_plan_adapter.py` (D-020, convention `references/modules.md`). Suites: module 111, methodology 752, packaging 802 OK. Merged into `main` (`fe3735d`, pushed); see `requirements/REQ-010-*/REPORT.md`.
- 2026-10-14 REQ-011 done (uncommitted): Scheduler Core M1 `skill/scripts/bt_scheduler_core/` + `bt_scheduler_adapter.py` (D-022; one authority per requirement, approval = sha256, projection `RUN.projection.json`). Suites: module 234, integration 28, methodology 797, packaging 11 OK; see `requirements/REQ-011-*/REPORT.md`.
- 2026-10-14 REQ-014 done (uncommitted): Scheduler M3 Agent Executor `skill/scripts/bt_scheduler_executor/` + `bt_scheduler_executor_adapter.py` (D-024; worktree per attempt, shim-owned agents, recoverable handoff, restart reconcile; never decides). Suites: module 243, adapter+integration 132, methodology 880 OK; real Claude/Codex/Gemini smoke OK; see `requirements/REQ-014-*/REPORT.md`.
- 2026-10-14 REQ-013 done (uncommitted): Scheduler M2 `skill/scripts/bt_scheduler_decision/` + methodology adapter, pinned offline Laya worker and M1 integration (D-023). Laya ran on the RTX A3000/CUDA 13.2, but actual held-out results were 14% vs 21% deterministic and no checkpoint passed calibration; the exact-artifact allowlist stays empty and live recommendations remain deterministic. Suites: M2 64, Planner 199, M1 239, Plan/M1/M2 integration 89, package 13; full methodology 916 OK/3 skipped. See `requirements/REQ-013-*/REPORT.md`.
- REQ-015's route-quality plan remains pending approval; D-027 limits all remaining Scheduler Laya work to English tasks and the `english` checkpoint. The separate complexity diagnostic is 41.5% (66/159), equal to its majority baseline, with 0% recall for `low` and `extreme`; labels are provisional and already seen by Laya. No further training ran. See its SPEC/PLAN and `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/english-only-analysis-v1.md`.
- REQ-016 now separates the Planner complexity 85% target from M2 route quality. Its English-only 1000-case plan is in review; it requires two blinded human reviewers, a balanced locked test and at least 850/1000 exact, with a lower 95% bound above 85% for the stronger population claim. Training has not started.
- 2026-10-14 REQ-012 closes planner phase 1: PLAN.md↔PLAN.json sync compares ids/titles/repo/after/verify; one launch gate (`bind_approved`) on every path; schema 1.1.0 with argued classifications (D-021). Launch never freezes (D-021); suites: module 201, methodology 953 OK; 6 real trials 182/182 + 3 context-free planner plans 3/3 + Gemini audit C1-C4 hold. See `ACCEPTANCE.md`; see `requirements/REQ-012-*/REPORT.md`.
- 2026-10-14 strict audit repaired project/global learning, telemetry integrity and cross-agent continuation.
  Native review panel: `artifacts/revision-flujo.html`; detailed evidence and limitations: `artifacts/audit-2026-10-14.md`.
  Final suite: 823 tests pass without thread/resource warnings; three native diagrams pass visual checks.
  No commit/push authorized; preserve existing uncommitted migration work. Legacy lint and live-provider limits
  remain explicit in the audit report; existing migration work remains separate.
- Repo `main` equals `origin/main` at `cb40787`. The tip has `bitacora/`: pictures, the other clone's copies and the
  live copies of eventos, maros, metodologia, signature-extraction, `INDEX.md` and `TOOLS.md` (D-011).
- Pictures: `~/bitacora/pictures` is a junction to `metodologia/bitacora/pictures` (D-012). Changes there are
  uncommitted in `metodologia` until someone commits them. The old live folder is kept as `~/bitacora/pictures.live-old`.
- `~/bitacora` is a local git repo with no remote: commits `b49b8c7`, `f391319`, `a3bb68c` and `e06f0a2`. It no longer
  tracks `pictures/` (P-013).
- The four repo-only projects (`agentes-de-trabajo`, `escritorio`, `maros-lab`, `proposal-studio`) are in `main` and
  identical to the live copies.
- Skill fixes pushed earlier (`a67371f`): pending normalization and the ID high-water mark. Lint: 0 errors in the five
  live projects.
- Skill test suite: 358 tests. 5 fail on Windows and already failed on `origin/main` before this session. Not fixed.
- Installed on 2026-10-08: hooks, HQ and launcher, web UI on 127.0.0.1:8765, gitleaks, trace graph, review and merge,
  evals 10/10. The first end-to-end run passed on 2026-10-14 (P-002 closed).

## Active focus
- REQ-008 PAUSED by the owner at T4: M1/T3 complete; T4 runtime/recovery fixes pass 139 affected regressions and 10 package/install tests, plus scoped ruff. Defaults remain unchanged; T4 acceptance/default activation and T5–T8 remain. See `requirements/REQ-008-fresh-milestone-orchestration-and-bounde/REPORT.md` and HANDOFF.md; P-018 tracks explicit resume. No active task writer/test handle, commits, push, global install or current-client replacement by this session.
- REQ-007: proposed platform migration documented in [migracion/README.md](migracion/README.md), with M0–M9, preservation inventory and acceptance/rollback gates. Planning only; implementation not started.
- The other computer's agent cleans up the bitácora in `main` (D-011, P-015). Then decide how the live bitácora is
  synced and backed up (P-013).

## Top pending (see PENDING.md)
- P-013 bitácora sync and backup decision · P-015 verify the other computer's cleanup ·
  P-014 prune closed items (low)

## Recent decisions (see DECISIONS.md)
- D-027 all remaining Scheduler Laya experiments use English tasks and the `english` checkpoint · D-026 narrower classifier-only scope superseded · D-025 M3 prerequisite integration and routes are bound · D-024 M3 agent executor stays a separate, non-routing module · D-023 Laya requires reviewed passing evidence ·
  D-022 M1 Scheduler Core is an isolated module · D-021 Planner phase 1 closes with schema 1.1.0 · D-020 methodology modules

## Known issues
- Codex hooks need one-time approval with `/hooks` on each machine.
- Push failures stay silent in `bt_vcs.push_async`. Nothing pushes the live bitácora (P-013).
- Pictures changes must be committed by hand in `metodologia` (D-012).
- The other computer pushes to `main` while we work. A push can be rejected until we fetch and rebase.
- The bitácora web server started before the migration runs old code until it restarts.

_Last updated: 2026-10-15_
