# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-002 · First real end-to-end test (HQ → rounds → web approval → executor loop → bitácora) · urgency: high · complexity: M · added 2026-10-08 · session
- P-003 · Visual review of the local web UI · urgency: med · complexity: S · added 2026-10-08 · session
- P-001 · Executor status/heartbeat + notifications (toast/ntfy) + resume of crashed executors · urgency: med · complexity: M · added 2026-10-08 · user: "no por ahora, documéntalo"
  - Ideas: STATUS.json written by the executor, stale-heartbeat flag + Resume button in the web UI, Notification/Stop/StopFailure hooks, `claude --bg` restarts.
- P-005 · Prune SKILL.md after a few weeks of real use (eval-driven no-op test) · urgency: low · complexity: S · added 2026-10-08 · research
- P-006 · Marathon: pass the claude prompt via stdin instead of argv (cmd-shim 8191-char / newline risk) · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-007 · Marathon: `run --accept-plan` to adopt deliberate edits to frozen repo/after/verify fields · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-008 · Web run tab: reuse bt_runstate helpers instead of its own load/progress · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-009 · Marathon: handle a PLAN.md tick failure after verify (currently unhandled) · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-010 · Marathon autostart .cmd: escape % and keep non-ANSI characters in BITACORA_ROOT · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-011 · `task done/fail/escalate`: _own_task should also check the REQ, not only the task id · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-012 · Split tests/test_marathon.py (396 lines, over the 300-line target) · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-004 · Concurrent edits to central files (PENDING/DECISIONS) from several sessions/machines · urgency: low · complexity: M · added 2026-10-08 · review

## Blocked
_None_

## Recently closed
_None_

## Notes
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._
