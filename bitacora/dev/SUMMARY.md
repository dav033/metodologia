2026-10-25 22:35: Pictures REQ-020 DONE: advisor on main (f8f8b9e8), one login, live on Vercel and the VPS, acceptance 25/25 on both. Gemini now uses one key (0770980b) everywhere; cap/plan unknown (owner to check ai.studio/spend, see cerebro note claves-gemini.md, P-194/P-195). Follow-ups: physical-phone check (D-066), key separation, P-193 venues in Happia, P-189/P-190 catalogue data.
2026-10-25 22:20: Pictures REQ-020 advisor released to main (f8f8b9e8): Vercel + VPS serve it, one login (original Demo Decoración), VPS acceptance 25/25. Vercel/local AI blocked by the shared Gemini key's monthly spending cap (P-194, owner action). REQ-020 stays open until Vercel acceptance reruns.
2026-10-25 18:25: Pictures REQ-020 advisor reworked by hand in worktree `login-redirect` (commits not pushed): voice notes (migration 003 applied), inspiration gallery and closed packages switched off, custom proposals from Happia services, theme-first ranking. Waiting for David to test localhost:3020, then gate/push/VPS release.
# dev — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: YYYY-MM-DD (set only after the owner confirms; otherwise write `not yet confirmed`).

## Current state
2026-10-25: Pictures REQ-020 r22 at 29/32: T15.11 live Happia catalogue released; T15.9 emulated mobile acceptance (D-066) running, then T15/T15b; advisor passwords changed to owner-chosen values on Vercel + VPS (verified). david-ui fully wiped incl. GitHub repo; REQ-001 r10 (1.3.0) awaits owner inputs 2–5 and approval.

2026-10-24 14:45: Pictures REQ-020 resumed on v2 (only active run, 28/31). david-ui wiped by owner order (david-ui D-002); GitHub repo pending `delete_repo` scope; REQ-001 being replanned on schema 1.3.0.

2026-10-24 14:30: Designer integrated across the whole flow (metodologia D-127; owner approves each contract via CLI/web; gate holds UI tasks until approved). origin/main `330a09dad`. Disk /home 3.5 GiB free.
2026-10-24 10:05: Engine v2 complete (session 1fbc12c7): F1–F5 closed and pushed, origin/main `b7c847d11`; default plan schema 1.3.0; 8 roles installed; temp worktrees/branches cleaned after archiving. Held runs (david-ui REQ-001, pictures REQ-020) still on owner hold. Details: metodologia day log 2026-10-24.
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
