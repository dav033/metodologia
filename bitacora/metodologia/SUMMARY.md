# metodologia — Summary

## Purpose
The user's own working method, as a skill for Claude Code and Codex: requirements by prioritized rounds → approved
plan → autonomous executor; engineering standards; subagent roles; per-project bitácora; local web UI; tools and infra
registry. The repo `github.com/dav033/metodologia` (private) holds `skill/`, `evals/`, `install.py` and bitácora copies
(D-008, D-009, D-011), and since D-012 the pictures bitácora itself. The rest of the live bitácora is `~/bitacora`.

## Current state
- 2026-10-15 M3 P-033 is implemented: the shim records bounded descendant identities and settle uses pidfds for terminal-process cleanup. Verification: M3 module 272, adapter/integration 138, installed-wheel smoke 1, package/install suite 13 OK. The package now includes `bt_plan_adapter_evidence`, a Planner helper required by integrated M1/M3 wiring. P-001 remains deferred by its owner. REQ-017's M4 plan is owner-approved and PLAN.json revision 1 frozen; accepted architecture and retention decisions are recorded as D-030–D-034. Execution is active on `feat/scheduler-m4-agent-monitor` (12 tasks/6 milestones); no provider calls or live agent launches are part of the plan. See `requirements/REQ-017-scheduler-m4-agent-monitor/`.
- 2026-10-15 independent Codex audit (D-20261015-084652-b103) broke C1/C2/C3/C5 on the planner copy (underscore titles, r1 run vs approved r2, unfrozen prose, fake script/glob/precedent evidence, placeholder text, malformed Unicode/version/null/duplicate keys); all fixed with regression tests, planner module 211 tests; see REQ-012 REPORT §Fourth round.
- 2026-10-14 REQ-009 + REQ-010 done: planner contract `PLAN.json` (D-019) now an isolated module `skill/scripts/bt_planner/` reached only through `bt_plan_adapter.py` (D-020, convention `references/modules.md`). Suites: module 111, methodology 752, packaging 802 OK. Merged into `main` (`fe3735d`, pushed); see `requirements/REQ-010-*/REPORT.md`.
- 2026-10-14 REQ-011 done (uncommitted): Scheduler Core M1 `skill/scripts/bt_scheduler_core/` + `bt_scheduler_adapter.py` (D-022; one authority per requirement, approval = sha256, projection `RUN.projection.json`). Suites: module 234, integration 28, methodology 797, packaging 11 OK; see `requirements/REQ-011-*/REPORT.md`.
- 2026-10-14 REQ-014 M3 base committed locally on `feat/scheduler-m2-m3`; P-033 follow-up `9849dfe` and the local Planner/profile fixes were fast-forwarded and pushed to `main` at `939288d`. Scheduler M3 Agent Executor `skill/scripts/bt_scheduler_executor/` + `bt_scheduler_executor_adapter.py` (D-024; worktree per attempt, shim-owned agents, recoverable handoff, restart reconcile; never decides). Original evidence: module 243, adapter+integration 132, methodology 880 OK; real Claude/Codex/Gemini smoke OK. P-033 follow-up evidence is in `requirements/REQ-014-scheduler-m3-agent-executor/REPORT.md`.
- 2026-10-14 REQ-013 done (uncommitted): Scheduler M2 `skill/scripts/bt_scheduler_decision/` + methodology adapter, pinned offline Laya worker and M1 integration (D-023). Laya ran on the RTX A3000/CUDA 13.2, but actual held-out results were 14% vs 21% deterministic and no checkpoint passed calibration; the exact-artifact allowlist stays empty and live recommendations remain deterministic. Suites: M2 64, Planner 199, M1 239, Plan/M1/M2 integration 89, package 13; full methodology 916 OK/3 skipped. See `requirements/REQ-013-*/REPORT.md`.
- REQ-015's route-quality plan remains pending approval; D-027 limits all remaining Scheduler Laya work to English tasks and the `english` checkpoint. The separate complexity diagnostic is 41.5% (66/159), equal to its majority baseline, with 0% recall for `low` and `extreme`; labels are provisional and already seen by Laya. No further training ran. See its SPEC/PLAN and `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-015/human-review-batch-02-v1.2/english-only-analysis-v1.md`.
- REQ-016 separates the Planner complexity 85% target from M2 route quality (D-028). The synthetic English v4 suite is 1008 train / 400 development / 1000 locked test rows with 250 per class and family-disjoint splits. Its one-time locked test is complete: the selected Laya checkpoint scored 656/1000 (65.6%; family bootstrap 62.1–69.0%), deterministic Naive Bayes scored 787/1000 (78.7%; family bootstrap 74.1–83.2%), and base Laya scored 264/1000 (26.4%). No system met 85%; do not use the 84.75% development score as the final result. The key was read once after sealing all predictions; standalone audit passed without rereading it. Report: `/home/david/.local/share/bt-scheduler-laya/evaluation/REQ-016/REPORT-v4.md`.
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
- D-029 M3 predecessor hand-off, task-bound routes, and pidfd-safe terminal sweep · D-028 REQ-016 synthetic labels need no human-review gate · D-027 all remaining Scheduler Laya experiments use English tasks and the `english` checkpoint · D-026 narrower classifier-only scope superseded · D-025 M3 integration/binding decision superseded by D-029 · D-024 M3 agent executor stays a separate, non-routing module · D-023 Laya requires reviewed passing evidence ·
  D-022 M1 Scheduler Core is an isolated module · D-021 Planner phase 1 closes with schema 1.1.0 · D-020 methodology modules

## Known issues
- Codex hooks need one-time approval with `/hooks` on each machine.
- Push failures stay silent in `bt_vcs.push_async`. Nothing pushes the live bitácora (P-013).
- Pictures changes must be committed by hand in `metodologia` (D-012).
- The other computer pushes to `main` while we work. A push can be rejected until we fetch and rebase.
- The bitácora web server started before the migration runs old code until it restarts.

_Last updated: 2026-10-15_
