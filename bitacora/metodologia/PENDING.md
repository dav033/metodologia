# metodologia — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-003 · Visual review of the local web UI · urgency: med · complexity: S · added 2026-10-08 · session
- P-001 · Executor status/heartbeat + notifications (toast/ntfy) + resume of crashed executors · urgency: med · complexity: M · added 2026-10-08 · user: "no por ahora, documéntalo"
  - Ideas: STATUS.json written by the executor, stale-heartbeat flag + Resume button in the web UI, Notification/Stop/StopFailure hooks, `claude --bg` restarts.
- P-013 · Marathon: a session interrupted by a supervisor kill is not counted as an attempt (repeated kill/resume retries the same task and tier until max_sessions) — persist the active unit and route and settle a reaped session as one interrupted attempt · urgency: med · complexity: M · added 2026-10-12 · adversarial audit (codex-luis)
- P-015 · Marathon on macOS/Windows: an orphaned agent session cannot be proven or ended without /proc; a resume may start a second session on the same tree — add per-platform process identity (ps eww / Get-CimInstance) or refuse to resume while the pid is alive · urgency: med · complexity: M · added 2026-10-12 · adversarial audit (codex-luis)
- P-005 · Prune SKILL.md after a few weeks of real use (eval-driven no-op test) · urgency: low · complexity: S · added 2026-10-08 · research
- P-006 · Marathon: pass the claude prompt via stdin instead of argv (cmd-shim 8191-char / newline risk) · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-007 · Marathon: `run --accept-plan` to adopt deliberate edits to frozen repo/after/verify fields · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-008 · Web run tab: reuse bt_runstate helpers instead of its own load/progress · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-009 · Marathon: handle a PLAN.md tick failure after verify (currently unhandled) · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-010 · Marathon autostart .cmd: escape % and keep non-ANSI characters in BITACORA_ROOT · urgency: low · complexity: S · added 2026-10-09 · marathon review
- P-012 · Split tests/test_marathon.py (396 lines, over the 300-line target) · urgency: low · complexity: S · added 2026-10-09 · ladder review
- P-014 · Marathon: recover_claims settles with a synthetic info (no agent/profile) and records no telemetry row; a failed recovered claim neither updates last_route nor the stats — persist route+session at session start and reuse them · urgency: low · complexity: M · added 2026-10-12 · adversarial audit (codex-luis)
- P-016 · Verify commands still run with shell=True under the supervisor's permissions; the hand-off now sends risky ones to the owner (VERIFY_RISK), but an approved plan is trusted as written — consider a structured argv form or an allowlist · urgency: low · complexity: M · added 2026-10-12 · adversarial audit (codex-luis)
- P-017 · Marathon: a milestone whose member depends on a task of a LATER milestone is split in two sessions (unit_of takes what is ready now) — schedule the external dependency first or postpone the group · urgency: low · complexity: M · added 2026-10-13 · second adversarial audit

## Blocked
_None_

## Recently closed
- P-018 · CLOSED 2026-10-13: metodologia main pushed (29 commits, origin/main 4ed35b4) WITHOUT .github/workflows/portable-tests.yml, by the owner's choice (the gh token has no `workflow` scope). The file is kept at ~/bitacora/metodologia/pending-artifacts/portable-tests.yml and in branch backup/pre-workflow-removal-20261013 (local). To enable CI later: `gh auth refresh -h github.com -s workflow`, copy it back to .github/workflows/ and commit · urgency: low · complexity: S · added 2026-10-13 · owner decision
- P-002 · First real end-to-end test (HQ → rounds → web approval → executor loop → bitácora) · urgency: high · complexity: M · added 2026-10-08 · session · closed 2026-10-12: full flow run with a real Claude agent (ops_e2e_check.py)
- P-011 · `task done/fail/escalate`: _own_task should also check the REQ, not only the task id · urgency: low · complexity: S · added 2026-10-09 · ladder review · closed 2026-10-12: _own_task checks run, project and task
- P-004 · Concurrent edits to central files (PENDING/DECISIONS) from several sessions/machines · urgency: low · complexity: M · added 2026-10-08 · review · closed 2026-10-12: bt_lock serializes supervisor writes

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
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary.
