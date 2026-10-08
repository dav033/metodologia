# metodologia — Summary

## Purpose
The user's own working method as a skill for Claude Code and Codex: requirements by prioritized rounds →
approved plan → autonomous executor; engineering standards; subagent roles; per-project bitácora; local web UI;
tools/infra registry. Repo: `github.com/dav033/metodologia` (private), `skill/` + `bitacora/`.

## Current state
Built and installed on the main machine (2026-10-08): always-on (CLAUDE.md @import; Codex via hooks), hooks
(SessionStart/Stop/SessionEnd/PostToolUse 500-line guard), HQ + launcher (Windows Terminal, claude
--dangerously-skip-permissions /loop, codex --yolo /goal), web UI on 127.0.0.1:8765, workspaces of several repos
(maros, eventos), multi-machine sync. Not yet exercised end to end on a real requirement (P-002).

## Active focus
- Batch 2026-10-08: secret scanning (gitleaks), trace graph + lint, graph view, review-and-merge page, skill evals,
  optional CodeGraph MCP.

## Top pending (see PENDING.md)
- P-002 real end-to-end test · P-003 web UI visual review · P-001 executor status/notifications (future)

## Recent decisions (see DECISIONS.md)
- D-001 no guard hook · D-002 one private monorepo · D-003 hefesto retired · D-004 graphs derived from IDs

## Known issues
- Codex hooks need one-time approval with `/hooks` on each machine.

_Last updated: 2026-10-08_
