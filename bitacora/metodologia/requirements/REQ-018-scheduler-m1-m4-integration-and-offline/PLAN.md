---
req: REQ-018
status: done
created: 2026-10-15
---
# Plan — REQ-018 — Scheduler M1-M4 integration and offline monitor recovery

## Approach
Keep the four modules isolated and compose them at the methodology adapter boundary. M3's FIFO remains bounded; M4 normalizes and commits allowlisted records before acknowledging queued frames, while its incident outbox and metric reader preserve M1/M2 ownership. P-038 uses a no-overwrite archive plus a verified staged candidate; it never edits a live store. Run P-036 separately from fixture-only verification after an immediate quota refresh.

## Global constraints
- M1 owns task and attempt state; M2 selects routes; M3 owns provider processes and raw output; M4 remains advisory.
- Preserve existing uncommitted work and module contracts. Do not activate the Scheduler globally, commit, push, deploy, or modify a live M4 store.
- Fixture verification is offline and uses fake providers. P-036 is a separate, bounded subscription-backed smoke with fresh eligible profiles only.
- M4 persistence is allowlisted and bounded. Any VACUUM receives the full explicit `sqlite_temp_dirs` list and checks free space.

## Tasks
<!-- Small, verifiable steps (one session each), in dependency order. Mark parallelizable ones with ∥.
- [ ] T1 — <what> · files: <paths> · verify: `<command>` · covers: R1, US-1
- [ ] T2 — <what> · repo: backend · after: T1 · verify: `npm test -- orders` · covers: R2
- [ ] T3 — <hard design problem> · level: architecture · after: T1 · verify: `<command>` · covers: R3
Plans for the scheduler also carry a classified `PLAN.json` (references/plan-contract.md): `bitacora.py plan-json init|check REQ-NNN`.
Marathon mode parses these lines: repo:, after: (task ids), verify: and level: are optional; verify is run by the
supervisor only when it is a command inside backticks; level: architecture starts the task on opus (effort xhigh)
instead of haiku. Keep each task to one session of work. -->

### M1 — Stream ingestion boundary
- [x] T1 — Convert M3 frames to durable allowlisted M4 events, metrics and gaps with retry-safe cursor acknowledgement · repo: skill · level: architecture · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p 'test_scheduler_monitor_runtime.py' -v` · covers: R1, R2, R3, US-1

### M2 — Full fixture flow
- [x] T2 — Exercise frozen Planner plan through M1/M2/M3 fake execution and M4 store/outbox in one test · repo: skill · after: T1 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p 'test_scheduler_m1_m4_e2e.py' -v` · covers: R3, R7, US-2

### M3 — Offline recovery
- [x] T3 — Implement no-overwrite M4 archive, integrity manifest and safe staged recovery candidate for P-038 · repo: skill · after: T1 · level: architecture · verify: `cd skill/scripts && python3 -m unittest discover -s bt_scheduler_monitor/tests -p 'test_recovery.py' -v` · covers: R4, R5, US-3

### M4 — Conditional live route smoke
- [x] T4 — Run P-036 with fresh quota evidence and two eligible profiles in a separate disposable real-provider smoke · repo: skill · after: T2 · verify: `cd skill/scripts && BITACORA_LIVE_SCHEDULER_SMOKE=1 python3 -m unittest discover -s tests -p 'test_scheduler_m2_live_smoke.py' -v` · covers: R6, US-4

### M5 — Acceptance and handoff
- [x] T5 — Run the Scheduler module suites, package install regression and focused integrated flow; record actual outcomes and close eligible pending items · repo: skill · after: T3, T4 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p 'test_scheduler*.py' -v` · covers: R1, R2, R3, R4, R5, R6, R7

## Verification
Run the M1, M2, M3 and M4 module suites plus the new M1–M4 fixture E2E and recovery tests. Run the package install test to verify the adapter/module are included. Keep P-036 in its own command/log segment: refresh quota immediately before launch; run only if at least two profiles are fresh, verified and eligible. Report a skipped/blocked live smoke as pending, never as passed.

## Rulings
- Keep M4 opt-in and call `Wiring.drain_stream()` from the owning M1 loop — this preserves the approved no-global-activation boundary and M1 run identity; cost if missed: queued frames can overflow or be lost on restart.
- Recovery creates a verified candidate but never replaces the source — this protects the live evidence and requires operator review; cost if wrong: restore remains a separate downtime action.

## Progress log
- 2026-10-15 16:45 plan APPROVED (terminal)
- 2026-10-15 17:34 T1 complete: M3 FIFO → bounded adapter → M4 normalized events/gaps with cursor commit before ACK; M2 metrics read-only; M1 incidents audit-only. Runtime integration: 4 passed; package-boundary checks passed.
- 2026-10-15 17:34 T2 complete: frozen Planner → M1 → M2 → fake M3 → M4 SQLite evidence and incident outbox; independent verifier passed; M4 metric read did not mutate the store or M1 task state (1 passed).
- 2026-10-15 17:34 T3 complete: no-overwrite archive/manifest, integrity verification, and bounded disposable candidate; source store preserved (8 recovery tests passed).
- 2026-10-15 17:34 T4 complete: P-036 quota gate admitted fresh Claude and Antigravity profiles; real smoke completed in 34.353 s with Claude selected, M1 completed, M3 exit 0, and independent verification passed. Private result: `~/.local/share/bt-scheduler-p036/smoke-wmo0gpu1/result.json` (0600).
- 2026-10-15 17:34 T5 complete: M1 248, M2 65, M3 276, M4 135; Scheduler wildcard 236 passed / 4 skipped; installed-package suite 15 passed; focused E2E 1, runtime 4, recovery 8 passed; scoped Ruff and compilation passed.
- 2026-10-15 17:36 T5 closeout audit: focused integration Ruff and post-cleanup route/executor/stream/E2E regressions passed. Broader Ruff found 83 style findings only in the pre-existing M4 package; tracked separately as P-039.
- 2026-10-15 17:37 Closeout: PLAN.json sync check passed; trace lint found no REQ-018 or related D/P findings (145 unrelated project-wide findings remain).
