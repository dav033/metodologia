# dev — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: YYYY-MM-DD (set only after the owner confirms; otherwise write `not yet confirmed`).

## Current state
2026-10-23: Engine v2 lead handoff prepared as `relay/RELAY-20261023-211009.md` for codex-2; manual continuation required. Main stays `48f45935e` with bitacora changes. Repairs/reviews and background tests remain pending; canonical checkpoint is `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTINUATION-01a16b88.md`. Held-run owner restrictions remain in force.
2026-10-23 19:10: Engine v2 F2-C Implementer adaptations committed (`b1aa50a2d`); full suite ran 2,404 tests with only the 15 baseline failures from RULES.md and 6 skips.
2026-10-23 11:38: david-ui REQ-001 in a full rework after its final audit (P-177, 5/32); REQ-020 regenerating T14a evidence before T15. Audit-readiness branch awaiting suites before merge.
2026-10-23 11:08: david-ui REQ-001 26/28 (over its 5 h window by ~30 min, P-175); REQ-020 in production, T15 repair T15.2 running (plan r15). Codex branches merged into main.
2026-10-23 08:57: david-ui REQ-001 running (14/27, parallel 3, window ends ~11:10); REQ-020 in production (c25a5f42), T15.1 repairing the audit checker (plan r14). Engine fixes P-165..P-174 in metodologia/PENDING.md; three Codex branches awaiting merge on integration/engine-fixes-0823.
REQ-029 r2 approved/frozen and running T3a att-0005 with accepted T1–T3 retained. REQ-027 r9 progressed through T15a/T15b; owner-requested T15d repair applied via T15d:7 rework_conflict, rebuilding stale T15c before T15d. No open decisions/blocked tasks at inspection; watchdog active. P-137 closed. Pictures REQ-020 continues separately; last inspected T7 att-0013 verifying. No relay or continuous monitoring requested.

## Active focus
- Engine v2: F2-C Implementer prompt/skills are ready for lead review at `b1aa50a2d`; see D-021 for the pinned Caveman license resolution.
- REQ-029: execute approved r2 through Scheduler, preserve T1–T3 and cancelled T4 evidence; no manual REQ-027 product fixes.
- Pictures REQ-020: independent Scheduler run continues; last inspected T7 att-0013 verifying with its own verifier decision.
- 2026-10-18 Relay C2 marathon retirement completed: obsolete tests removed, shared coverage retained, remaining launch/orchestration tests migrated, and three Scheduler-only launch regressions fixed. Targeted tests passed (207 cases plus quality_metrics 24); migration package/entrypoint/inventory 45 passed. Compile/imports/CLI/wheel/sdist passed. Collection retains pre-existing relay_run 52 -> 48 failure; scoped lint retains 12 pre-existing F401 findings, no new findings. C3 documentation/overall removal reconciliation remains under P-001; P-002 unchanged. Owner's dirty/staged tree preserved; no commits or full-suite rerun.

- Local plans server is now enabled at user login via `bitacora-web.service`; active and HTTP 200 at http://127.0.0.1:8765/plans. See TOOLS.md for status/log/restart commands.

## Top pending (see PENDING.md)
-

## Recent decisions (see DECISIONS.md)
- D-021: upstream provenance records the license at the fetched pinned revision.

## Known issues
-

_Last updated: 2026-10-23_
