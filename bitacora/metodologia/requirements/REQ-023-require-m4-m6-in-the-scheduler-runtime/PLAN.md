---
req: REQ-023
status: review
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
- Preserve legacy `RUN.json` bytes and default launch behavior unless scope round 1 selects legacy migration.
- All module stores remain private, durable, separate and stable for resume.

## Tasks
- [ ] T1 — Require private M4/M5/M6 stores and ports in the Scheduler owner composition · files:
  `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_executor_wiring.py`,
  `skill/scripts/tests/test_scheduler_runtime.py` · level: architecture · risk: high · verify:
  `PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_runtime -v` · covers: R1, R2, R4, R5, R10
- [ ] T2 — Drive M4 stream ingestion and incident delivery from M1; reject intermediate-symlink FIFO escape · after: T1 · files:
  `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_executor_adapter.py`,
  `skill/scripts/bt_scheduler_stream_adapter.py`, `skill/scripts/tests/test_scheduler_stream_adapter.py`,
  `skill/scripts/tests/test_scheduler_runtime.py` · verify:
  `PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_stream_adapter test_scheduler_runtime -v` · covers: R3, R7
- [ ] T3 — Prove the standard runtime's M1→M6 rejection/recovery/pass flow; repair package coverage and update contracts/docs · after: T2 · files:
  `skill/scripts/tests/test_scheduler_m1_m6_e2e.py`, `skill/scripts/tests/test_scheduler_runtime.py`, `skill/scripts/bt_cli_scheduler_run.py`,
  `skill/scripts/bt_scheduler_executor_wiring.py`, `skill/scripts/bt_scheduler_monitor/README.md`,
  `skill/scripts/bt_scheduler_quality/README.md`, `skill/references/modules.md`, `pyproject.toml`,
  `bitacora/metodologia/DECISIONS.md`, `bitacora/metodologia/requirements/REQ-023-require-m4-m6-in-the-scheduler-runtime/REPORT.md` · verify:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest test_scheduler_m1_m6_e2e test_scheduler_runtime -v` · covers: R5, R6, R8, R9
- [ ] T4 — Run integrated Scheduler and installed-wheel acceptance, close project memory and audit the scoped diff · after: T3 · files:
  `skill/scripts/tests/`, `tests/migration/test_package_install.py`,
  `bitacora/metodologia/SUMMARY.md`, `bitacora/metodologia/PENDING.md` · verify:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests python3 -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` · covers: R1-R10

## Verification
The Scheduler owner's offline E2E uses a frozen Planner plan, M1/M2 and fake M3 child process, starts required M4/M5/M6
through the production composition, observes M4 stream persistence and incident delivery, M6 rejection→M5 bounded
retry→fresh M2 assignment→M6 PASS→M1 completion, and verifies resume/store identity. Run focused FIFO path regressions,
the full Scheduler discovery, migration package suite, scoped Ruff, Python compilation and `git diff --check`.
Do not start a provider, task, web server or autostart entry.

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
