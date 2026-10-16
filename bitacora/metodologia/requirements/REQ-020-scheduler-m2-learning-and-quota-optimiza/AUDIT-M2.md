# Independent milestone audit — M2

Date: 2026-10-15 23:00 -05

Scope: T9–T12 performance evidence, contextual history, immutable learning snapshots and prequential evaluation.

## Findings and resolution

The independent audit found two medium-severity (P2) defects in T12's first implementation:

1. `temporal.py` filtered events to the requested route before replay reduction. Conflicting applied projections for one attempt/verdict could therefore lose the other route and appear as a valid PASS/FAIL. The evaluator now partitions and reduces all routes first, then selects the requested route. `test_conflicting_applied_route_projections_are_reduced_before_route_filtering` covers the case.
2. Temporal partitioning used any non-null `applied_at`, including `stale`, `invalid` and `noop` deliveries. Such a record could mark an attempt known before a later valid M1 application. Only `application_status=applied` events with a valid timestamp now participate in temporal partitioning. `test_nonapplied_timestamp_cannot_hide_a_later_applied_outcome` covers stale delivery followed by later application.

The auditor reviewed the fix, confirmed both findings resolved, verified the fingerprint uses only pre-cutoff reduced events/contexts, and reported no additional defect. The explicit `learning_snapshots.cutoff_rule` remains a caller precondition; no consumer violating it was found.

## Verification

- T9 events: 18/18 passed.
- T10 contextual history: 12/12 passed.
- T11 recorder/snapshots: 20/20 passed.
- T12 temporal evaluation: 8/8 passed.
- Full M2 package: 139/139 passed.
- M1 ports/public contract: 30/30 passed.
- Auditor's `test_performance_*.py` selection: 38/38 passed.
- T12 scoped Ruff, Python compilation, API JSON parsing and `git diff --check`: passed.
- Full-package Ruff still reports the previously known UP047 in `engine.py`, outside T12.

No provider calls, commits, deployment or external effects were used.

## Independent milestone audit — T13 and T18–T23

Date: 2026-10-16

Scope: T13 effective-account identity and candidate enumeration; T18/T19 M1/M2/M3/M5 assignment and retry boundaries; T20 optional M4 metric evidence; T21 shared integration; T22 adversarial cases; and T23 offline benchmark.

### Findings and resolution

- T13: no P1–P3 findings. `_pool_account_identity()` normalizes provider account selectors for in-memory pool deduplication, resolves the known Claude/Codex default directories, preserves requested preference order and keeps providers distinct. The legacy persisted `account_key()` format remains unchanged. The regression covers `~` versus absolute paths, generic aliases and distinct quota-cache keys. D-049 records this boundary.
- T18/T19: no P1–P3 findings. The M1 assignment path retains route/hash/quota revalidation and reservation authority; retry decisions return through M1 for a fresh M2 proposal, while wait/block do not loop. The no-alternative reroute case remains blocked without a second launch.
- T20/T21: the first independent pass found one P2 defect: `bt_scheduler_decision_adapter.py` imported `MetricSample` from M4 at module load, so an installation without M4 could not import the M1/M2 adapter. The implementation now resolves the M4 type only when a non-empty metric collection is supplied. A subprocess regression blocks `bt_scheduler_monitor*` and `bt_scheduler_m4*`, then imports both M1 and M2 adapters and checks the empty-metric path. Re-review confirmed the finding resolved with no additional P1–P3 issues. Exact metric identity and comparability matching, preserved provenance, unknown quota as `None`, and M1 state ownership were confirmed.
- T22/T23: no P1–P3 findings. Adversarial cases fail closed for unknown/stale/exhausted windows, shared aliases, changing/crossed resets, external usage, auth errors and unconfirmed retry evidence. The offline benchmark uses the same frozen 100-case/500-candidate snapshot for all strategies and reports synthetic oracle/regret separately from unobserved live quota, attribution, verification and intervention metrics. Contextual M2 has no verified history in this fixture and therefore uses deterministic fallback; the fixture does not model cross-case concurrency or provider cost.

### Verification

- T13 sources: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_sources` — 12/12 passed; independent alias regression `test_agents.PoolAndRouteTests.test_pool_deduplicates_normalized_account_paths_without_changing_quota_keys` — 1/1 passed.
- T18 integration: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_integration test_scheduler_route_resolution bt_scheduler_core.tests.test_ports` — 46/46 passed.
- T19 E2E: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_m1_m5_e2e` — 7/7 passed; isolated no-alternative retry/reroute regression — 1/1 passed.
- T20 metric history: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_metric_history` — 5/5 passed after the optional-import fix.
- T21 E2E: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_m1_m5_e2e test_scheduler_m1_m4_e2e` — 8/8 passed after the fix.
- T22 adversarial tests — 6/6 passed; focused Ruff, Python compilation and scoped `git diff --check` passed.
- T23 exact offline command `python skill/scripts/bt_scheduler_decision_benchmark.py --mode offline --json /tmp/req020-offline-benchmark.json` — exit 0; emitted 100 held-out cases and snapshot hash `12f3048be9aaa3a5b3c325f4536494681bc07986ab5486ff8fd9e2780a18575e`. Full benchmark review confirmed no provider/network path.

No provider calls, live quota refresh, commits, deployment or external effects were used. T24–T26 remain open behind T24's separate explicit owner-authorization gate.
