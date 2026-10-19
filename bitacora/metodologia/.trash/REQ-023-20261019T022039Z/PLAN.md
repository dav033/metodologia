---
req: REQ-023
status: done
created: 2026-10-16
---
# Plan — REQ-023 — Require M4-M6 in the Scheduler runtime

## Approach
Make M4–M6 mandatory at the shared Scheduler owner runtime (`scheduler-run` and `launch --scheduler`) while retaining
the low-level composition seam for isolated tests. Allocate stable, private stores per runtime identity; drive M4's
bounded stream and incident work from the M1 owner loop; initialize M5/M6 before attempts can dispatch. Preserve
M1 ownership, M2's current deterministic routing, M6's sandbox and operator-review rules, and the separate legacy path.
Supersede D-043/D-051 activation clauses with a new D-052, without changing M1 port contracts.

## Global constraints
- Preserve unrelated existing worktree changes; no commit, push, merge, real run, provider invocation or autostart change.
- Keep M1 the only task/run/verdict authority; do not bypass M1 for M4 incidents, M5 recovery or M6 verdicts.
- Keep M2 deterministic routing unchanged; do not feed experimental M4 metrics into route ranking.
- Fail closed on missing/unwritable required stores; M6 never runs commands outside bubblewrap and `NEEDS_REVIEW`
  stays operator-owned.
- Preserve legacy `RUN.json` bytes and default launch behavior; round 1 choice A keeps the legacy launcher separate.
- All module stores remain private, durable, separate and stable for resume.

## Tasks
- [x] T1 — Require private M4/M5/M6 stores and ports in the Scheduler owner composition · files:
  `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_executor_wiring.py`,
  `skill/scripts/tests/test_scheduler_runtime.py` · level: architecture · risk: high · verify:
  `test_scheduler_runtime` within the 350-test Scheduler discovery · covers: R1, R2, R4, R5, R10
- [x] T2 — Drive M4 stream ingestion and incident delivery from M1; reject intermediate-symlink FIFO escape · after: T1 · files:
  `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_executor_adapter.py`,
  `skill/scripts/bt_scheduler_m4_wiring.py`, `skill/scripts/bt_scheduler_stream_adapter.py`,
  `skill/scripts/bt_scheduler_executor/shim.py`, `skill/scripts/tests/test_scheduler_stream_adapter.py`,
  `skill/scripts/tests/test_scheduler_m3_stream_wire.py`, `skill/scripts/tests/test_scheduler_runtime.py` · verify:
  stream/FIFO regressions passed 34/34; runtime and terminal outbox-drain cases passed in full discovery · covers: R3, R7
- [x] T3 — Prove the standard runtime's M1→M6 rejection/recovery/pass flow; repair package coverage and update contracts/docs · after: T2 · files:
  `skill/scripts/tests/test_scheduler_m1_m6_e2e.py`, `skill/scripts/tests/test_scheduler_runtime.py`, `skill/scripts/bt_cli_scheduler_run.py`,
  `skill/scripts/bt_scheduler_executor_wiring.py`, `skill/scripts/bt_scheduler_monitor/README.md`,
  `skill/scripts/bt_scheduler_quality/README.md`, `skill/references/modules.md`, `pyproject.toml`,
  `bitacora/metodologia/DECISIONS.md`, `bitacora/metodologia/requirements/REQ-023-require-m4-m6-in-the-scheduler-runtime/REPORT.md` · verify:
  full Scheduler discovery includes the M1→M6 rejection→M5 recovery→M2 reroute→M6 PASS E2E; wheel audit 19/19 · covers: R5, R6, R8, R9
- [x] T4 — Run integrated Scheduler and installed-wheel acceptance, close project memory and audit the scoped diff · after: T3 · files:
  `skill/scripts/tests/`, `tests/migration/test_package_install.py`,
  `bitacora/metodologia/SUMMARY.md`, `bitacora/metodologia/PENDING.md` · verify:
  Scheduler discovery 350 tests, 6 skipped; installed-wheel suite 19/19; scoped Ruff, compileall, `git diff --check`, and independent spec/standards review passed · covers: R1-R10

## Verification
The Scheduler owner's offline E2E uses a frozen Planner plan, M1/M2 and fake M3 child process, starts required M4/M5/M6
through the production composition, observes M4 stream persistence and incident delivery, M6 rejection→M5 bounded
retry→fresh M2 assignment→M6 PASS→M1 completion, and verifies resume/store identity. Run focused FIFO path regressions,
the full Scheduler discovery, migration package suite, scoped Ruff, Python compilation and `git diff --check`.
Do not start a provider, task, web server or autostart entry.

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->
- M4 terminal streams are requeued across bounded owner polls until FIFO EOF and pending incidents reach zero; the owner does not return early and lose trailing evidence — required to make the existing bounded drain correct for larger outputs and outboxes — cost if wrong: high.
- The FIFO bridge walks each path component relative to a trusted directory descriptor with `O_NOFOLLOW` — prevents an intermediate symlink from escaping the attempt directory, including replacement races — cost if wrong: high.

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
- 2026-10-16 08:39 plan APPROVED (terminal)
- 2026-10-16 implementation completed; spec and standards reviews PASS; Scheduler discovery 350 passed / 6 skipped; wheel suite 19/19; documentation and P-042/P-043 reconciled.
