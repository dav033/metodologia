# REQ-017 — Scheduler M4 Agent Monitor closeout

## Built

- Completed the isolated standard-library M4 monitor: bounded M3 output ingestion, provider normalizers, redaction, activity and advisory incident detection, SQLite WAL persistence, queries, retention, and the M1/M2 adapters.
- Added `bt_scheduler_monitor.providers` explicitly to the wheel package list after final package review found that the source tree's explicit setuptools package list omitted it; the installed-wheel test now exercises `JsonlCollector.feed` and confirms all four normalizers load from the isolated installation.
- Enforced the owner-approved 512 MiB database-plus-WAL ceiling with bounded retention writes. At zero headroom, M4 preserves remaining evidence, reports storage pressure, and does not acknowledge unpersisted frames.
- VACUUM preflight checks the database filesystem and every explicitly supplied SQLite temporary-directory candidate. With no complete candidate list, VACUUM is deferred; the monitor does not read process environment or change journal mode.
- Scoped the M3 executor import-boundary audit to production files while retaining its runtime isolation check; tests may import the executor directly.
- Updated the reproducible resource baseline and documented the recovery boundary in `skill/scripts/bt_scheduler_monitor/README.md`.
- Added `covers:` trace links to all twelve PLAN.md tasks. Owner approved PLAN.json revision 3 with the trace links and final T12 evidence; revisions 1 and 2 remain preserved.

## Verification evidence

- M4 package suite: **127 tests passed**. Focused retention-pressure suite: **6 passed**.
- Installed-wheel/package suite: **14 passed**, including runtime-module coverage and an isolated installed-wheel run of the M4 store, both adapters, CLI, and all four provider normalizers; P-035 is closed.
- From the repo root, `PYTHONPYCACHEPREFIX=/tmp/req-017-pycache python3 -m compileall -q skill/scripts/bt_scheduler_monitor skill/scripts/bt_scheduler_monitor_adapter.py skill/scripts/bt_scheduler_stream_adapter.py skill/scripts/bt_cli_scheduler_monitor.py skill/scripts/tests/test_scheduler_executor_integration.py tests/migration/test_package_install.py` passed. Scoped Ruff (`E4,E7,E9,F`) across the M4 package, both adapters, CLI, M3 boundary regression, and installed-wheel tests passed after removing seven unused/duplicate import findings.
- `python3 skill/scripts/bitacora.py plan-json check REQ-017 --json`: `ok: true`, no errors or warnings. `launch_problem(..., freeze=False)` returned `None`. Frozen revisions r1, r2, and r3 are preserved; REQ-017 trace lint has no uncovered, unknown-reference, dangling, empty-coverage, or open-task findings.
- Final independent spec and standards reviews: **APPROVE**, no remaining findings. The spec reviewer found the omitted provider subpackage on the first pass; the fix, installed-wheel regression, and clean follow-up review are complete.
- Final scope audit re-ran T9/T10: M1 incident-contract and adapter suites passed 9/9 and 5/5; M2 metric-history and adapter suites passed 4/4 and 6/6. They verify incident references leave M1 task/attempt/lease state unchanged and M2 reads validated provenance without mutating M4. REQ-017's M1/M2 integration is confined to T9/T10; T10's metric-history test is selected by its approved `test_metric*.py` verification command. Other uncommitted M1/M2 core changes in this shared worktree are separately tracked under delivered REQ-013 and were left untouched.
- Broad scheduler wildcard: **223 tests, 3 skipped, 0 failures**. The executor import-boundary regression now excludes test modules while retaining its production import check; the focused boundary test also passes. P-037 is closed.
- Fourteen preserved offline reports used 300 fixture events and three simulated producers, each with a 300-frame / 5,100-byte queue peak. Throughput was 823.60–961.40 events/s; p50 155.35–202.57 ms; p95 289.45–339.40 ms; CPU 0.309–0.361 s; sampled peak RSS 26,344–26,640 KiB. All had zero drops. The database measured 503,808 bytes before retention and 536,576 bytes after schema/health initialization; WAL was 0 bytes after checkpoint. The consumer was inactive while producers emitted events, so these measurements cover producer burst and consumer drain, not sustained SQLite contention. The direct-SQL check with no queued consumer is excluded. Repeated runs were slower and more variable than the first four, which is reflected in the budget. Reports: `/tmp/req-017-m4-benchmark-v3.json`, `-v3-repeat.json`, `-repeat.json`, `-final-a.json`, `-final-b.json`, `-benchmark.json`, and `/tmp/req-017-m4-repeat-1.json` through `-8.json`.
- The resulting same-host fixture budget is ≥800 events/s, p95 ≤350 ms, CPU ≤0.38 s, sampled RSS ≤27,000 KiB, and zero loss for this 300-event fixture. These rounded limits extend beyond the slower/higher observed edge and are not production SLOs.
- No provider calls, live agents, process signals, quota reads, deployments, commits, or pushes were made.

## Rulings

- D-030–D-034 remain the approved architecture, authority, data-minimization, retention, and detector decisions. The owner approved the offline recovery follow-up (P-038) on 2026-10-15; its implementation design is separate from REQ-017.
- Revision 3 changes only progress evidence and task-level trace coverage metadata; it does not alter scope, dependencies, verification commands, or task execution.
- D-038 corrects the preserved run count to fourteen; D-037's host-local fixture budget remains unchanged and does not claim production capacity.
- Keep the database-plus-WAL ceiling hard. At zero headroom or without enough space for a complete bounded operation, preserve data and surface pressure instead of raising the cap or changing SQLite journal mode.
- The M4 package stays isolated from runtime environment access. Its caller must pass the full set of writable SQLite temporary directories to enable VACUUM safely.

## Needs your eyes

- No further REQ-017 decision is awaiting owner review. The offline recovery proposal is approved for follow-up planning; its implementation has not started.

## Proposals

1. **P-038 — Add an offline M4 store recovery path (approved follow-up).** Define an owner-operated export/verification and safe reclaim or migration workflow for a database at the hard cap when no online retention batch can fit. The owner approved the proposal on 2026-10-15. It remains outside REQ-017 and is not implemented.

## Pending

- P-035 is closed after the installed-wheel/package suite passed 14/14, including M4 package, adapters, CLI, and provider normalizers from the installed wheel.
- P-036 remains open for the separate M2 real route-choice smoke requiring two fresh quota-valid profiles.
- P-037 is closed after the scheduler suite passed 223 tests with three expected opt-in skips and zero failures; the focused production-boundary test passed.
- P-038 is approved for separate requirements/planning work; no other REQ-017 implementation task remains.

## Walkthrough

- M3 owns provider processes and writes bounded, versioned stream frames to M4. The M4 adapter drains them into a bounded queue; provider-specific normalizers and redaction convert them to allowlisted records.
- M4 commits normalized events and source cursors together in its own SQLite WAL store. It persists incidents and a retryable outbox; M1 receives audit-only references, while M2 reads metric history.
- Retention compacts or deletes eligible records in batches of at most four and checks the projected database-plus-WAL size before each commit. Open incidents and undelivered outbox entries are preserved.
- When capacity is exhausted, M4 reports degraded storage and keeps unpersisted frames unacknowledged. After storage recovers, gaps remain explicit rather than claiming complete history.
- M4 observations never change task state or control a process: M1 remains authoritative and M3 owns process lifetime.
- VACUUM is the non-obvious recovery step: SQLite may place its temporary database outside the M4 database directory, so the caller must supply all eligible temporary paths and each filesystem must pass the free-space check.
