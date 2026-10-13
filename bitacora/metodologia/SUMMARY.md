# metodologia — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Canonical cross-harness workflow skill for David's software work: requirements, engineering execution, project memory, infrastructure and autonomous runs.
Last confirmed with owner: 2026-10-10.

## Current state
The skill now supports deep product-level workspace audits, evidence-based self-improvement, contextual feature discovery, safe agent orchestration, and durable multi-day execution. It is globally activated for Claude Code and Codex through user-level instructions and links to this working tree. REQ-001 and REQ-002 are implemented in the methodology working tree and awaiting owner review; changes are uncommitted. REQ-003 now integrates Caveman concision, optional RTK evidence recovery and Grill Me interviews; static validation and independent conversational simulations passed. Paid evals remain unverified; RTK runtime was measured under REQ-005. A two-agent A/B pilot measured 30.38% fewer total tokens and 3.03% fewer output tokens, with equivalent manual quality; final prose was slightly longer, and the total saving mainly reflects one fewer tool turn/cache reuse.

REQ-004 adds the exact benchmarked selective-context policy. Across six screening runs, median total tokens fell 5.55% and uncached input 27.99%; the held-out pair used 0.86% more total tokens. Quality criteria held in all eight trials; compact-entrypoint restructuring was rejected. Evidence: artifacts/metodologia-efficiency-2026-10-12/benchmark.md. No guaranteed cost saving is claimed.

REQ-005 integrates RTK into the parent repository with a pinned user-space installer and explicit-only setup options. Three-run output-token measurements range from -0.4% on a focused diff to -99.8% on verbose passing pytest; full recovery of a failing pytest log produced 1.9% more output than native. Installer tests 9/9 and exit/diagnostic preservation passed. Evidence: artifacts/metodologia-rtk-2026-10-12/.

## Active focus
- D-005: audit budget persisted and verified (Sonnet medium, Opus high escalation, Sol medium fallback), including generated reviewer defaults.
- D-006: hourly subscription collector installed/active; metadata-only 5h/weekly readings feed cached headroom into routing. Real route preview favors codex-luis (13% bottleneck) over codex-1 (57%). Claude personal succeeds; claude-work returns HTTP401, explicitly unavailable. 383 tests pass; independent review approved; no inference in the collector. Changes uncommitted.
- Antislop/Thermos selective integration (2026-10-13, D-004): on-demand interface/content quality and evidence-driven diff reviews, preserving existing permissions and axes. Three behavioral eval cases added; real paid evals not run.
- Review uncommitted REQ-001 through REQ-005 changes; collect normal-session feedback on selective context loading.

## Top pending (see PENDING.md)
- See PENDING.md for the current open items.

## Recent decisions (see DECISIONS.md)
- D-001: Adapt public orchestration patterns with attribution; keep methodology self-contained and retain existing approval/safety boundaries.

## Known issues
- The first full-suite attempt was launched twice concurrently and wrote generated `proj1`–`proj48` fixtures plus `INDEX.md` into the real bitácora. David authorized and the generated fixtures were removed; see today's log.
- A test also reset `PENDING.md`; its twelve captured items have been restored and recorded in today's log.

_Last updated: 2026-10-13_
