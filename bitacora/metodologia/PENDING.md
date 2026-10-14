# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-013 · Live bitácora backup: `~/bitacora` is now a symlink into the `metodologia` repo (origin = GitHub, 778 bitácora files already on `origin/main`), so a push is the backup; BUT the repo is PUBLIC (checked 2026-10-14 with `gh`) while these notes called it private: owner decision 2026-10-14: no push for now, work locally; revisit before any push (make the repo private first) · urgency: high · complexity: M · added 2026-10-13 · user: "tenemos un problema" (GitHub review)
  - Context: since remote commit `4cfd74f` the bitácora lives outside the repo (D-007). Its legacy history reached GitHub with `a67371f`. The silent push failure no longer applies, because nothing pushes the live copy.
  - Options: (1) a private remote for `~/bitacora` with `push_async` plus a push-failure log (`.state/push.log`, warning at SessionStart), the approved fix; (2) local git plus a scheduled backup; (3) no sync, single machine. The session-end commit creates a local git repo in `~/bitacora` (`ensure_repo`).
- P-017 · REQ-007 migration: T2 closed by D-015; T5/T6 done; T7 and F-M1-01 closed 2026-10-14; remaining: Windows/macOS matrix (deferred by the owner), src/ move (deferred by D-014), commits (owner decision) · urgency: high · complexity: L · added 2026-10-13 · independent spec review
  - Context: see migracion/CONTINUE.md and the PLAN progress log. Committed locally 2026-10-14 (cdf9ea7, b3954d1, 89f2021); push is the owner's call.
- P-003 · Visual review of the local web UI · urgency: med · complexity: S · added 2026-10-08 · session
- P-001 · Executor status/heartbeat + notifications (toast/ntfy) + resume of crashed executors · urgency: med · complexity: M · added 2026-10-08 · user: "no por ahora, documéntalo"
  - Ideas: STATUS.json written by the executor, stale-heartbeat flag + Resume button in the web UI, Notification/Stop/StopFailure hooks, `claude --bg` restarts.
  - Real Maros REQ-005 E2E remains in progress on 2026-10-14: M1/M2 accepted; T6 accepted as `a580d3e` after 38 min (13 suites/197 tests, tsc and ESLint clean); M3 is running. Follow `e2e-maros/FINDINGS.md`: F-24's read loop resolved before its 60 min timeout; F-25 audit/test receipt mismatch; F-26 task-kind substring routing fix locally verified. Finish M3–M5, audit and autonomy verdict before calling the run successful. Branch cleanup is a proposal only.
  - Relay follow-up F-23: fixed false "scheduled" success when no terminal client is controllable and added a one-second helper startup check; see `skill/scripts/bt_relay_handoff.py` and `skill/references/relay.md`. Confirmed 2026-10-14 by requesting `codex-luis`: no controllable client produced a saved handoff and exact manual command, with no false scheduled-success message. The command was not executed, so the successor did not start. Helper-start success path and broader behavioral tests remain unverified.
- P-018 · [paused by owner] REQ-008: T4 implementation verified; acceptance/default activation and T5–T8 remain; resume only on explicit request · urgency: med · complexity: L · added 2026-10-14 · owner pause; requirements/REQ-008-fresh-milestone-orchestration-and-bounde/REPORT.md
- P-005 · Prune SKILL.md after a few weeks of real use (eval-driven no-op test) · urgency: low · complexity: S · added 2026-10-08 · research
- P-006 · Marathon: pass the claude prompt via stdin instead of argv (cmd-shim 8191-char / newline risk) · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-007 · Marathon: `run --accept-plan` to adopt deliberate edits to frozen repo/after/verify fields · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-008 · Web run tab: reuse bt_runstate helpers instead of its own load/progress · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-009 · Marathon: handle a PLAN.md tick failure after verify (currently unhandled) · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-010 · Marathon autostart .cmd: escape % and keep non-ANSI characters in BITACORA_ROOT · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-011 · `task done/fail/escalate`: _own_task should also check the REQ, not only the task id · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-012 · Split tests/test_marathon.py (396 lines, over the 300-line target) · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-004 · Concurrent edits to central files (PENDING/DECISIONS) from several sessions/machines · urgency: low · complexity: M · added 2026-10-08 · review
- P-014 · Prune closed items older than 14 days into the month summary: the rule is written in the file header, but normalize never applies it, so Recently closed only grows · urgency: low · complexity: M · added 2026-10-13 · antagonist review of the pending fix
- P-021 · Optional: show PLAN.json classification in the web UI plan review and `bitacora.py run` status; enrich REQ-013/015/016 only if the owner wants them in the contract · urgency: low · complexity: M · added 2026-10-14 · REQ-009 proposal
  - Context: `artifacts/plan-contract-compat.md` lists what each historical plan lacks (no `### M` milestones in REQ-013/015, no repo/verify values).
- P-023 · Evidence is judged textually: calibrate the rules against real plans and decide whether a model-assisted review of `classification_evidence` is worth adding (a fluent but false justification still passes: existence of files, specs, tasks, requirements, decisions, commits and executables is verified, truth is not) · urgency: low · complexity: M · added 2026-10-14 · REQ-012 limitation
  - Context: only structure, strength rules and existence of cited files/specs/tasks are verified; 6 trials (REQ-012 `planning-trials/`) are the calibration set so far.
- P-026 · Scheduler core adoption: opt-in switch in `launch --mode marathon` to create a scheduler-owned run (watch/web read `RUN.projection.json`), and enforce `plan_ref` on resume in the legacy supervisor (gap found in REQ-011 §12.5) · urgency: low · complexity: M · added 2026-10-14 · REQ-011 proposal
- P-020 · Scheduler (future): consume PLAN.json (`bt_plan_contract.load` / `bt_plan_revisions.load_revision`), calibrate `estimated_minutes` against real durations, own concurrency · urgency: low · complexity: L · added 2026-10-14 · REQ-009 proposal
  - 2026-10-14 owner ruling: M1 must never touch agents, sessions or the methodology flow; being inert until the future modules plug into its ports is intended, not a defect. Do not wire M1 into `launch`/supervisor ahead of those modules.
  - 2026-10-14 REQ-011 delivered M1 of the Scheduler (`bt_scheduler_core`, D-022): modules M2 (decision), M3 (executor), M4 (monitor), M5 (recovery) remain, as implementations of the core's ports (`requirements/REQ-011-*/REPORT.md`).
  - Context: explicitly out of scope of REQ-009; `references/plan-contract.md` §Consuming a plan lists the stable error codes.
- P-022 · Split further parts of the methodology into modules following `references/modules.md` (candidates to evaluate: requirements gate, marathon supervisor state/run, bitácora documents/index, agent routing) · urgency: low · complexity: L · added 2026-10-14 · REQ-010 proposal
  - Context: `bt_planner` is the first module and the template (boundary + isolation + adapter tests). Do one at a time, each with its own requirement and review; the owner picks the order.

## Blocked
_None_

## Recently closed
_None_

## Notes
- ✓ P-025 · Plans approved by hand had no approval record · closed 2026-10-14 · a launch never freezes anymore: `PLAN_NOT_FROZEN` until `plan approve` / `plan-json freeze` (explicit `--force` is recorded `launch-forced`); REQ-012, D-021.
- ✓ P-024 · REQ-009 PLAN.md M3 heading differed from its frozen PLAN.json title · closed 2026-10-14 · PLAN.md heading aligned to the frozen title (narrative only; frozen revision and history untouched); `plan-json check REQ-009` is OK again.
- ✓ P-019 · Freeze approved PLAN.json also in the foreground launch path · closed 2026-10-14 · REQ-012: one launch gate (`bt_plan_adapter.launch_problem` -> planner `bind_approved`) now guards standard, web, handoff, foreground (+ successor helper) and every NEW run; approval freezes the approved bytes; tests `LaunchPaths` (17). D-021.
- ✓ P-015 · Verify the other computer's bitácora cleanup after D-011 (`9d1b796`) · closed 2026-10-14 · no file under `bitacora/` was deleted or renamed between `9d1b796^` and `origin/main`, and `origin/main` has no bitácora file missing from the live tree (778 tracked files); `origin/main` has not moved since
- ✓ P-002 · First real end-to-end test · closed 2026-10-14 · `ops_flow_check.py --live`: RESULT OK, 24 PASS/0 FAIL (claude haiku builds, Antigravity Gemini flash low audits, learned preference honoured, 5 commits, nothing pushed); plus web path in a throwaway root: token-less POST 403, web plan approval launched the marathon, run done (T1 + M1-audit + FINAL), 3 commits. Limits: the HQ interview rounds were not driven through the web form, Linux only
- ✓ P-016 · Antigravity provider defects (stale quota reset, result parsing, 90% Gemini audit routing) · closed 2026-10-14 · fixed by the 2026-10-14 audit; `test_agy.py` 29, `test_audit_routing.py` 14, `test_subscription_usage.py` 20 pass, verified in session 790c0548
