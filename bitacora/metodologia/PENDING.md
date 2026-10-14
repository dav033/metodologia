# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-002 · First real end-to-end test (HQ → rounds → web approval → executor loop → bitácora) · urgency: high · complexity: M · added 2026-10-08 · session
- P-013 · Live bitácora (~/bitacora) has no remote and no backup (local git repo since `b49b8c7`): decide how it is synced and backed up · urgency: high · complexity: M · added 2026-10-13 · user: "tenemos un problema" (GitHub review)
  - Context: since remote commit `4cfd74f` the bitácora lives outside the repo (D-007). Its legacy history reached GitHub with `a67371f`. The silent push failure no longer applies, because nothing pushes the live copy.
  - Options: (1) a private remote for `~/bitacora` with `push_async` plus a push-failure log (`.state/push.log`, warning at SessionStart), the approved fix; (2) local git plus a scheduled backup; (3) no sync, single machine. The session-end commit creates a local git repo in `~/bitacora` (`ensure_repo`).
- P-017 · REQ-007 migration: T2 closed by D-015; T5/T6 done; remaining: wire driver (T7), T8 scheduling, src/ move (sdist + pip install, sys.executable in generated commands, parity gaps), F-M1-01 config drops unknown data, then M3 · urgency: high · complexity: L · added 2026-10-13 · independent spec review
  - Context: see migracion/CONTINUE.md and the PLAN progress log. No commit/push authorized.
- P-003 · Visual review of the local web UI · urgency: med · complexity: S · added 2026-10-08 · session
- P-016 · Fix Antigravity provider defects found by `test_agy.py` · urgency: med · complexity: S · added 2026-10-13 · delegated test audit
  - `bt_agy.capacity()` can return a reset from stale cache; `bt_runsettle.parse_output()` loses top-level Antigravity result fields; audit routing still selects Gemini at 90% usage.
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
_None_
