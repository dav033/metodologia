# metodologia — Summary

## Purpose
The user's own working method, as a skill for Claude Code and Codex: requirements by prioritized rounds → approved
plan → autonomous executor; engineering standards; subagent roles; per-project bitácora; local web UI; tools and
infra registry. The repo `github.com/dav033/metodologia` (private) holds `skill/`, `evals/`, `install.py` and,
since D-008 and D-009, bitácora copies. The live bitácora is `~/bitacora` (D-007, partly superseded).

## Current state
- Repo `main` equals `origin/main` at `904a1e7`: a merge of the other clone's commits (`c683665`, `1a72518`) with our
  pictures commit (`c1e39c0`).
- The repo tip has `bitacora/`: pictures (our copy) and 16 top-level entries from the other clone (D-009). The repo
  copies of eventos, maros, metodologia and signature-extraction are kept as they are (D-010). They may differ from
  the live copies until the other agent's controlled merge is done (P-015).
- The live bitácora `~/bitacora` has nine projects. The four repo-only projects (`agentes-de-trabajo`, `escritorio`,
  `maros-lab`, `proposal-studio`) were copied in today; they are not committed yet.
- The live bitácora has one local commit (`b49b8c7`) and no remote (P-013).
- Skill fixes pushed earlier (`a67371f`): pending normalization and the ID high-water mark. Lint: 0 errors in the five
  live projects.
- Skill test suite: 358 tests. 5 fail on Windows and already failed on `origin/main` before this session. Not fixed.
- Installed on 2026-10-08: hooks, HQ and launcher, web UI on 127.0.0.1:8765, gitleaks, trace graph, review and merge,
  evals 10/10. The first end-to-end run is not done yet (P-002).

## Active focus
- The other agent runs the controlled merge (D-010, P-015). Then decide how the live bitácora is synced and backed up
  (P-013).

## Top pending (see PENDING.md)
- P-002 first end-to-end run · P-013 bitácora sync and backup decision · P-015 verify the controlled merge ·
  P-014 prune closed items (low)

## Recent decisions (see DECISIONS.md)
- D-010 keep the other clone's copies; the other agent merges · D-009 the other clone's bitácora is integrated into
  the repo · D-008 pictures bitácora copied into the repo · D-007 bitácora lives in `~/bitacora` (partly superseded)

## Known issues
- Codex hooks need one-time approval with `/hooks` on each machine.
- Push failures stay silent in `bt_vcs.push_async`. Nothing pushes the live bitácora (P-013).
- The other clone pushed bitácora straight to `origin/main`. Its next push should follow the controlled merge (D-010).
- The bitácora web server started before the migration runs old code until it restarts.

_Last updated: 2026-10-13_
