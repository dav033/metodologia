# metodologia — Summary

## Purpose
The user's own working method, as a skill for Claude Code and Codex: requirements by prioritized rounds → approved
plan → autonomous executor; engineering standards; subagent roles; per-project bitácora; local web UI; tools and infra
registry. The repo `github.com/dav033/metodologia` (private) holds `skill/`, `evals/`, `install.py` and bitácora copies
(D-008, D-009, D-011), and since D-012 the pictures bitácora itself. The rest of the live bitácora is `~/bitacora`.

## Current state
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
- REQ-008 approved and executing: M1 complete; T3 foreground lifecycle passed 21/21 and final standards review. T4 structured runtime/rotation is in progress; recovery council and whole-flow audits remain T5–T8. See `requirements/REQ-008-fresh-milestone-orchestration-and-bounde/PLAN.md` and `ACCEPTANCE-MATRIX.md`. No commits, push, global installation or current-client replacement authorized.
- REQ-007: proposed platform migration documented in [migracion/README.md](migracion/README.md), with M0–M9, preservation inventory and acceptance/rollback gates. Planning only; implementation not started.
- The other computer's agent cleans up the bitácora in `main` (D-011, P-015). Then decide how the live bitácora is
  synced and backed up (P-013).

## Top pending (see PENDING.md)
- P-013 bitácora sync and backup decision · P-015 verify the other computer's cleanup ·
  P-014 prune closed items (low)

## Recent decisions (see DECISIONS.md)
- D-012 the pictures bitácora is a junction into `metodologia` · D-011 the live bitácora is published to `main` over the
  other clone's copies · D-010 (superseded) · D-009 the other clone's bitácora integrated into the repo · D-008 pictures
  bitácora copied into the repo (superseded by D-012) · D-007 bitácora lives in `~/bitacora` (partly superseded)

## Known issues
- Codex hooks need one-time approval with `/hooks` on each machine.
- Push failures stay silent in `bt_vcs.push_async`. Nothing pushes the live bitácora (P-013).
- Pictures changes must be committed by hand in `metodologia` (D-012).
- The other computer pushes to `main` while we work. A push can be rejected until we fetch and rebase.
- The bitácora web server started before the migration runs old code until it restarts.

_Last updated: 2026-10-13_
