# dev — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: YYYY-MM-DD (set only after the owner confirms; otherwise write `not yet confirmed`).

## Current state
REQ-027 r9 is under the repaired Scheduler; T18 is blocked on owner decision T18:11 after findings F2, F19 and F20. REQ-020 r2 has T5 att-0011 running. `/flow` intentionally folds M4 provider detail and informational incidents into per-attempt digests (D-085); REQ-027 currently has 5,703 provider events and 966 info incidents folded, with two medium connection errors visible.

## Active focus
- REQ-027: wait for owner direction on T18:11, then continue the audit/rework flow from current evidence.
- Pictures REQ-020: monitor T5 att-0011 and downstream work; T4 is no longer the live attempt.
- 2026-10-18 Relay C2 marathon retirement completed: obsolete tests removed, shared coverage retained, remaining launch/orchestration tests migrated, and three Scheduler-only launch regressions fixed. Targeted tests passed (207 cases plus quality_metrics 24); migration package/entrypoint/inventory 45 passed. Compile/imports/CLI/wheel/sdist passed. Collection retains pre-existing relay_run 52 -> 48 failure; scoped lint retains 12 pre-existing F401 findings, no new findings. C3 documentation/overall removal reconciliation remains under P-001; P-002 unchanged. Owner's dirty/staged tree preserved; no commits or full-suite rerun.

- Local plans server is now enabled at user login via `bitacora-web.service`; active and HTTP 200 at http://127.0.0.1:8765/plans. See TOOLS.md for status/log/restart commands.

## Top pending (see PENDING.md)
-

## Recent decisions (see DECISIONS.md)
-

## Known issues
-

_Last updated: 2026-10-20_
