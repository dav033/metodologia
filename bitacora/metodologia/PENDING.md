# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-013 · Live bitácora (~/bitacora) has no remote and no backup (local git repo since `b49b8c7`): decide how it is synced and backed up · urgency: high · complexity: M · added 2026-10-13 · user: "tenemos un problema" (GitHub review)
  - Context: since remote commit `4cfd74f` the bitácora lives outside the repo (D-007). Its legacy history reached GitHub with `a67371f`. The silent push failure no longer applies, because nothing pushes the live copy.
  - Options: (1) a private remote for `~/bitacora` with `push_async` plus a push-failure log (`.state/push.log`, warning at SessionStart), the approved fix; (2) local git plus a scheduled backup; (3) no sync, single machine. The session-end commit creates a local git repo in `~/bitacora` (`ensure_repo`).
- P-017 · REQ-007 migration: T2 closed by D-015; T5/T6 done; T7 and F-M1-01 closed 2026-10-14; remaining: Windows/macOS matrix (deferred by the owner), src/ move (deferred by D-014), commits (owner decision) · urgency: high · complexity: L · added 2026-10-13 · independent spec review
  - Context: see migracion/CONTINUE.md and the PLAN progress log. Committed locally 2026-10-14 (cdf9ea7, b3954d1, 89f2021); push is the owner's call.
- P-003 · Visual review of the local web UI · urgency: med · complexity: S · added 2026-10-08 · session
- P-001 · Executor status/heartbeat + notifications (toast/ntfy) + resume of crashed executors · urgency: med · complexity: M · added 2026-10-08 · user: "no por ahora, documéntalo"
  - Ideas: STATUS.json written by the executor, stale-heartbeat flag + Resume button in the web UI, Notification/Stop/StopFailure hooks, `claude --bg` restarts.
- P-015 · Verify the other computer's cleanup of the bitácora in `main` after D-011 (`9d1b796`): its copies merged with the live ones, and nothing lost · urgency: med · complexity: M · added 2026-10-13 · user decision
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

## Blocked
_None_

## Recently closed
- ✓ P-002 · First real end-to-end test · closed 2026-10-14 · `ops_flow_check.py --live`: RESULT OK, 24 PASS/0 FAIL (claude haiku builds, Antigravity Gemini flash low audits, learned preference honoured, 5 commits, nothing pushed); plus web path in a throwaway root: token-less POST 403, web plan approval launched the marathon, run done (T1 + M1-audit + FINAL), 3 commits. Limits: the HQ interview rounds were not driven through the web form, Linux only
- ✓ P-016 · Antigravity provider defects (stale quota reset, result parsing, 90% Gemini audit routing) · closed 2026-10-14 · fixed by the 2026-10-14 audit; `test_agy.py` 29, `test_audit_routing.py` 14, `test_subscription_usage.py` 20 pass, verified in session 790c0548
