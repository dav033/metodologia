---
status: final
---
# dev — Week 2026-10 W4 (2026-10-19 → 2026-10-25)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- First real Scheduler run (pictures REQ-019, 10-19): 35 attempts, 16 PASS / 9 FAIL; 14 engine defects found and fixed (D-002..D-017); report in `INFORME-REQ-019-primer-run-scheduler.md`.
- Engine hardening on live runs (10-20..22): watchdog, decision requests, attempt history (D-099), block diagnosis (D-097), integration line (REQ-028), coordinator for live checks (P-157), self-healing; merged to `main` 67c8a85c0.
- Engine v2 lead (10-23..24): schema 1.3.0 subplans, composition gates, 8 roles; F1-F5 closed and pushed, origin/main `53b83af55`, then `b7c847d11`; root suite 2,534 tests = 15 baseline + 3 P-189.
- Designer integrated across the flow (D-127, 10-24) and collaborative planning in the web UI (D-128, 10-25).
- Pictures REQ-020 advisor released to Vercel and VPS (10-25, main f8f8b9e8, acceptance 25/25; a9f3d6e5 33/33); REQ-027 done (10-22); david-ui wiped and its GitHub repo deleted.

## Done
- REQ-019 supervised end to end (10-19): routing fix D-002, M4/M6 fixes D-003..D-013, REQ-013 not launched (no PLAN.json).
- SUPERRR H0-H9 closed with independent reviews; `bitacora go REQ-NNN`, `bt_plan_gate` Stop-hook gate and agent presence on `/now` (10-19).
- `/flow` rewritten and redesigned (D-017, `flow.css`, travelling-dot map, "what the agent does now"); CPU at rest ~177 % to ~18 % (10-19/20).
- Reverse SSH tunnel unit `advin-bitacora-tunnel.service` exposes the panel on advin (10-19); `bitacora-web.service` restarted.
- Up to 3 parallel tasks (D-015); watchdog and operator commands (D-016); decision requests (D-020).
- Blocked-task diagnosis D-097, SessionStart pull stash incident fixed D-098, retry history D-099, carry-forward fix `fbec1973` (10-20).
- REQ-028 integration line (`c8acc8965`, `cad5f91df`, `3060105f2`), merged into feat/req-029 `2e42230f0`; flag `gates.integration_line` on globally (10-21).
- REQ-029 (autonomous recovery) implemented directly on main; its Scheduler run cancelled and plan deleted at owner request (10-22).
- REQ-020 live checks via the coordinator (`c03ad88a9`), P-159..P-164 engine fixes, verifier cache fix `53d6295be` (10-22).
- Three Codex branches merged (`e19f9b80d`); P0 cleanup of 585 worktrees and 598 branches, tag `pre-engine-v2` (D-123, 10-23).
- Engine v2 F2-C Implementer skills `b1aa50a2d` (D-021); F4-9a..j composition gates, benchmark F4-8 (legacy 48 vs subplans 36 attempts) (10-23/24).
- D-126: verification authority from operator files, never the plan (10-24); david-ui REQ-001 wiped (david-ui D-002).
- Pictures REQ-020: voice notes, guided conversation steps, emulated mobile acceptance (pictures D-065..D-068), released f8f8b9e8 (10-25).
- Disk freed twice at owner request (P-006 closed 10-19; installers and snapshot #1 on 10-25, /home 5.1 GiB free).

## Decisions
- metodologia D-002..D-020: routing, M4/M6 sandbox and monitor rules, REQ-019 plan revisions, agent limit 2 h (D-014), 3 parallel tasks (D-015), watchdog (D-016).
- D-097..D-100: diagnosis, SessionStart pull safety, attempt history, retry carry-forward (10-20).
- D-123..D-125: Engine v2 P0 cleanup, schema 1.3.0, lead decisions; D-021 Caveman license at pinned revision (10-23).
- D-126 external verification authority; D-127 Designer in the whole flow (owner approves each contract) (10-24).
- D-128: plan approval approves planning-time designs (10-25).
- pictures D-065 live Happia catalogue, D-066 emulated mobile acceptance, D-067 Diana's findings in three phases.
- Owner rule: plans with >~8 tasks run through the scheduler, not in-session (10-19); REQ-029 run replaced by direct implementation (10-22).

## Not done / dropped
- REQ-013 not launched (no PLAN.json, 32 tasks without a runnable verify) (10-19).
- Autonomous structural conflict convergence not buildable deterministically; REQ-029 R9 withdrawn (10-22). Parallel M6 checks not built (P-156 closed).
- Not ported from the /flow design: attempt-history chips, node badges, notifications (10-20).
- Mistake: Baldur's Gate 3 install (146 GB) deleted when the owner meant installers (P-129, 10-19).
- REQ-020 scheduler run held and finished by hand (10-25); david-ui REQ-001 replan awaits owner (r10, review).

## Carried over to next week
- P-129 Baldur's Gate 3: reinstall or `btrfs restore` (owner decision).
- P-143 REQ-027 T22 owner prerequisites (OAuth App, Telegram chat id).
- P-001 marathon removal: C3 documentation and acceptance reconciliation.
- Engine defects still open: P-139, P-140, P-141, P-142, P-138, P-130 (SIGBUS), P-128 (M4 store retention, owner call).
- P-131/P-132/P-133 (Telegram decision buttons, plan `needs` field, decision timeout).
- Pictures REQ-020 follow-ups (P-194/P-195 Gemini cap) and david-ui REQ-001 plan approval.
