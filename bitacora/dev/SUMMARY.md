# dev — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: YYYY-MM-DD (set only after the owner confirms; otherwise write `not yet confirmed`).

## Current state
REQ-027 r3 resumed after repairing M6 SQLite lock loss and missing nested dependency mounts. T8 passed re-verification and completed; T15 restarted as att-0027. Its previous scaffold passes full npm run verify inside the repaired sandbox (lint, types, six tests, production build). No open decisions or blocked tasks at last check. Existing /flow controls and M6 log review remain available.

## Active focus
- REQ-027: monitor T15 att-0027 and downstream work; owner authorized repair and relaunch of T8/T15.
- 2026-10-18 Relay C2 marathon retirement completed: obsolete tests removed, shared coverage retained, remaining launch/orchestration tests migrated, and three Scheduler-only launch regressions fixed. Targeted tests passed (207 cases plus quality_metrics 24); migration package/entrypoint/inventory 45 passed. Compile/imports/CLI/wheel/sdist passed. Collection retains pre-existing relay_run 52 -> 48 failure; scoped lint retains 12 pre-existing F401 findings, no new findings. C3 documentation/overall removal reconciliation remains under P-001; P-002 unchanged. Owner's dirty/staged tree preserved; no commits or full-suite rerun.

- Local plans server is now enabled at user login via `bitacora-web.service`; active and HTTP 200 at http://127.0.0.1:8765/plans. See TOOLS.md for status/log/restart commands.

## Top pending (see PENDING.md)
-

## Recent decisions (see DECISIONS.md)
-

## Known issues
-

_Last updated: 2026-10-19_
