# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-002 · First real end-to-end test (HQ → rounds → web approval → executor loop → bitácora) · urgency: high · complexity: M · added 2026-10-08 · session
- P-013 · Bitácora pushes to GitHub silently failing since 2026-10-09 17:09 (228 local commits unpushed; `push_async` drops stderr) · urgency: high · complexity: M · added 2026-10-13 · user: "tenemos un problema" (GitHub review)
  - Evidence: no bitácora push reached the remote after 07a8113; `git push --dry-run` and a detached dry-run both succeed; no rulesets; gitleaks clean. Cause unknown until one real push shows stderr.
  - Fix: (1) one foreground push to read the error; (2) `bt_vcs.push_async` writes stderr to `.state/push.log` and SessionStart warns on failed pushes, not only on failed pulls.
  - Context: remote commit `4cfd74f` drops the embedded bitácora from the repo (the live copy is `~/bitacora`, a plain folder). Decide the layout first; this item may change shape. 112 bitácora files exist only locally.
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
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._
