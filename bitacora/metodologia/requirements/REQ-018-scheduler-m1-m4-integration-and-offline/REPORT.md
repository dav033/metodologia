# REQ-018 — Scheduler M1–M4 integration and offline monitor recovery

## Built

- Connected bounded M3 FIFO frames and loss summaries to M4's allowlisted durable event/gap store. Cursor movement and
  queue acknowledgement follow the M4 transaction; retries retain uncommitted frames and gaps.
- Added optional M4 runtime wiring at the methodology adapter boundary: M2 metric history is read-only, while M4
  incidents reach M1 as idempotent audit references. M1 remains authoritative for task and attempt state.
- Added an offline M4 archive, integrity manifest, verification, and bounded disposable recovery candidate. Existing
  outputs are never overwritten; the workflow does not activate a candidate or modify a live M4 store.
- Added a fixture E2E from frozen Planner plan through M1, M2 and fake M3 execution to M4 persistence and incident
  delivery. Completed P-036 using two fresh quota-valid provider profiles in a separate real-provider smoke.
- Recorded architecture decisions D-039 (caller-driven optional integration) and D-040 (verified offline recovery).
  P-036 and P-038 are closed.

## Verification evidence

| Check | Result |
|---|---:|
| `python3 -m unittest discover -s bt_scheduler_core/tests` (M1) | 248 passed |
| `python3 -m unittest discover -s bt_scheduler_decision/tests` (M2) | 65 passed |
| `python3 -m unittest discover -s bt_scheduler_executor/tests -v` (M3) | 276 passed |
| `python3 -m unittest discover -s bt_scheduler_monitor/tests` (M4) | 135 passed |
| `python3 -m unittest discover -s tests -p 'test_scheduler*.py'` | 236 passed, 4 skipped, 0 failed |
| `python3 -m unittest discover -s tests/migration -p 'test_package_install.py'` | 15 passed |
| Focused M4 runtime integration | 4 passed |
| Planner→M1→M2→M3→M4 fixture E2E | 1 passed |
| Offline archive/recovery | 8 passed |
| Scoped Ruff on REQ-018 integration files, Python compilation, package boundary checks | passed |
| `plan-json check REQ-018 --json` | `ok: true`, no errors or warnings |
| Trace lint for REQ-018 and D-039/D-040/P-036/P-038/P-039 | 0 findings |
| P-036 real multi-profile smoke | 1 passed in 34.353 s |

P-036 refreshed and checked quota immediately before launch. Claude and Antigravity were both fresh, verified, distinct
eligible profiles. Claude was selected; M1 completed; the public M2 binding matched; M3 used the selected provider,
profile and model, exited 0, and captured its handoff; the independent verifier passed and the disposable repository
was unchanged. The sanitized result is stored with mode `0600` at
`~/.local/share/bt-scheduler-p036/smoke-wmo0gpu1/result.json`.

The first live invocation reached successful M1 completion and independent verification, then failed a post-run
harness assertion because the audit lookup passed M1's `route:` wrapper to the public M2 resolver. The harness now
strips the wrapper before lookup and saves its result before assertions. The corrected second invocation passed; the
failed first invocation produced no retained artifact.

The M4 recovery tests used disposable stores. No live M4 store was opened or changed. The full Scheduler wildcard
(236 passed, 4 skipped) passed before the final error-type/import-style cleanup. After those small changes, the
affected route-resolution (23), executor-adapter (37), stream-adapter (4), M3 stream-wire (18), and M1–M4 E2E (1)
tests passed again; Python compilation and scoped integration lint also passed. The subscription-backed smoke was not
rerun after those changes.

A broader `ruff check` across the existing `bt_scheduler_monitor/` package reported 83 style findings (including
import ordering, exception-class suggestions, and modern Python idioms); every finding was inside that package. Its
implementation predates this requirement and was not changed here. The scoped integration lint passes; cleanup is
tracked separately as P-039.

The project-wide trace graph still reports 145 unrelated historical lint findings; none reference REQ-018, its tasks
or requirements, P-036/P-038/P-039, or D-039/D-040. No other trace findings were changed as part of this requirement.

## Rulings

- M4 is enabled only when the caller supplies `monitor_store_path`; the owning M1 loop invokes
  `Wiring.drain_stream(attempt_id, run_id)`. This preserves M1 identity/authority and avoids silently activating a
  global service. Consequence: callers must drain active attempts and terminal output; queued frames are not spooled
  across process restart.
- Recovery produces a verified candidate but leaves restore/activation to the operator. Consequence: recovery requires
  a separate reviewed restore window and additional disk space.

## Needs your eyes

No approval is required to use the tested opt-in adapter. Before any live activation, the caller must implement the
M1-owned drain and outbox retry cadence described in `skill/scripts/bt_scheduler_monitor/README.md`.

## Proposals

None.

## Pending

P-036 and P-038 are closed. P-039 tracks the broader M4 package lint cleanup. Global Scheduler activation and a
background polling loop were explicitly outside this requirement and remain inactive.

## Walkthrough

1. Freeze a Planner plan and pass it to the M1 adapter, which owns the run and attempt identity.
2. M2 persists a quota-checked route; M3 resolves that route and owns the provider process and bounded FIFO.
3. The M1 owner loop calls `Wiring.drain_stream(attempt_id, run_id)`. The bridge validates run identity and sends
   allowlisted normalized records and known gaps to M4; M4 commits its cursor before acknowledging the queue.
4. M2 may query compatible metrics from M4 without writing to the store. M4's incident outbox sends only a versioned,
   idempotent audit reference back to M1; it cannot change task state.
5. To recover a pressured M4 store, stop all writers, create and verify a full archive, then prepare and verify a
   separate bounded candidate. Review and any restore are operator-managed.
