---
req: REQ-020
status: approved
created: 2026-10-15
---
# Plan — REQ-020 — Scheduler M2 learning and quota optimization

## Approach
Extend the existing M2 package and its methodology adapter. Keep provider catalogs, authorization, quota collectors, M1 reservations and M5 recovery policy in their existing owners. Build account-aware window observations, strictly correlated outcome learning, deterministic batch selection and redacted, replayable evidence. Preserve Laya's current disabled gate and use offline fixtures for comparison.

## Global constraints
- `SOURCE-PLAN.md`, `SPEC.md` and `CONTRACTS.md` are the scope and contract authorities; do not narrow their acceptance.
- M1 owns task/run/attempt state and reservations; M2 proposes only; M5 acts only through M1.
- Reuse current providers, profile authorization, account IDs, quota caches and telemetry. No network/cache refresh in M2 selection.
- Never infer quota remaining, task success, quota consumption, cost, or calibrated future success from missing or synthetic evidence.
- Keep M2 importable without M4/M6 or Laya. Do not activate Laya without the existing gate and new measured evidence.
- Preserve all primary-worktree M4/M5/Pictures changes. Work in `/home/david/dev/metodologia-m2`; M5 writes only in its separate worktree. Shared integration files have one integrator.
- No provider experiment without separate explicit owner authorization; no commits, push, merge, deploy or credential changes.

## Tasks

### M0 — Inventory, contract and baseline
- [x] T1 — Audit the live HEAD, M2 consumers, quota sources, telemetry, M1/M5 boundaries and dirty primary work · repo: methodology · risk: high
- [x] T2 — Freeze versioned M1/M2/M5 interfaces and file ownership in `CONTRACTS.md` · repo: methodology · after: T1 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest bt_scheduler_core.tests.test_ports test_scheduler_decision_contract` · risk: high
- [x] T3 — Capture the deterministic fixture baseline, hashes, selected routes, quota facts and exclusions · repo: methodology · after: T1 · verify: `python /home/david/bitacora/metodologia/requirements/REQ-020-scheduler-m2-learning-and-quota-optimiza/baseline.py --verify` · risk: medium
- [x] T4 — Create and validate this REQ SPEC/PLAN/PLAN.json with task coverage and a frozen revision · repo: methodology · after: T2, T3 · verify: `python skill/scripts/bitacora.py --project metodologia plan-json check REQ-020` · risk: high

### M1 — Observable, conservative quota inputs
- [x] T5 — Inventory account aliases, all provider/model windows, reset semantics and attribution gaps · repo: methodology · after: T4 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_subscription_usage test_agy` · risk: medium
- [ ] T6 — Normalize versioned `QuotaObservation` records from cached sources only · repo: methodology · after: T5 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_quota_windows` · risk: high
- [ ] T7 — Add a bounded demand/usage estimator with explicit observed, estimated and unknown provenance · repo: methodology · after: T6 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_quota_demand` · risk: high
- [ ] T8 — Model account-level pressure across every relevant window and shared profile · repo: methodology · after: T7 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_quota_windows bt_scheduler_decision.tests.test_batch` · risk: high

### M2 — Verified performance learning
- [ ] T9 — Normalize attempt evidence with plan/revision/task/attempt/decision/route identities and independent outcome state · repo: methodology · after: T8 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_performance_events` · risk: high
- [ ] T10 — Compute contextual aggregates, coverage and conservative fallback for sparse samples · repo: methodology · after: T9 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_performance_history` · risk: high
- [ ] T11 — Persist immutable, bounded learning snapshots and idempotent source fingerprints with the existing decision ledger · repo: methodology · after: T10 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_recorder` · risk: high
- [ ] T12 — Add prequential/temporal evaluation without data leakage or probability claims · repo: methodology · after: T11 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_performance_temporal` · risk: high

### M3 — Deterministic batch quota optimizer
- [ ] T13 — Enumerate real configured provider/model/profile/effort candidates and deduplicate effective accounts · repo: methodology · after: T12 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_sources` · risk: high
- [ ] T14 — Declare quality floors and lexicographic multi-objective policy after hard eligibility filters · repo: methodology · after: T13 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_policy` · risk: high
- [ ] T15 — Select a bounded READY batch deterministically against slots, shared accounts and known concurrency constraints · repo: methodology · after: T14 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_batch` · risk: high
- [ ] T16 — Extend the idempotent decision ledger with batch fingerprints, selected reasons, exclusions and no-assignment evidence · repo: methodology · after: T15 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_recorder` · risk: high
- [ ] T17 — Add an opt-in shadow policy that records comparisons without dispatch side effects · repo: methodology · after: T16 · verify: `PYTHONPATH=skill/scripts python -W error::ResourceWarning -m unittest bt_scheduler_decision.tests.test_shadow` · risk: medium

### M4 — M1/M3/M5 and telemetry integration
- [ ] T18 — Adapt the existing AssignmentPort/M3 route boundary without taking authority; preserve quota revalidation and hash binding · repo: methodology · after: T17 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_integration test_scheduler_route_resolution bt_scheduler_core.tests.test_ports` · risk: high
- [ ] T19 — Verify retry-approved reevaluation through M1/M5; exhausted account A may route to eligible B, and wait/block never loops · repo: methodology · after: T18 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_m1_m5_e2e` · risk: high
- [ ] T20 — Consume validated M4/M6 evidence when present while preserving deterministic operation when absent · repo: methodology · after: T19 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_metric_history` · risk: high
- [ ] T21 — Integrate once through the sole owner of shared core/wiring/package files and run M1/M2/M3/M5 contracts · repo: methodology · after: T20 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_m1_m5_e2e test_scheduler_m1_m4_e2e` · risk: high

### M5 — Adversarial validation and honest offline comparison
- [ ] T22 — Add deterministic adversarial/property cases for windows, shared accounts, resets, unknowns, auth, retries and external use · repo: methodology · after: T19 · verify: `PYTHONPATH=skill/scripts:skill/scripts/tests python -W error::ResourceWarning -m unittest test_scheduler_decision_adversarial` · risk: high
- [ ] T23 — Compare FIFO, eligible round-robin, legacy router, deterministic M2 and contextual M2 on identical frozen snapshots · repo: methodology · after: T22 · verify: `python skill/scripts/bt_scheduler_decision_benchmark.py --mode offline --json /tmp/req020-offline-benchmark.json` · risk: high
- [ ] T24 — Run the bounded real-provider experiment only after separate explicit owner authorization · repo: methodology · after: T21, T23 · risk: high
- [ ] T25 — Complete independent spec/standards/security audit and fix verified findings with regressions · repo: methodology · after: T24 · risk: high
- [ ] T26 — Deliver README, configuration/rollback, limits, metrics, HANDOFF and final evidence report · repo: methodology · after: T25 · verify: `python skill/scripts/bitacora.py --project metodologia trace --node REQ-020` · risk: medium

## Verification finish line
- Offline checks: M2 package, M1 core, Planner, M3 route resolution, M5 isolated policy, integrated fake-backed M1→M2→M3→M5 chain, package install, static checks and `git diff --check`.
- Deterministic benchmark: frozen fixtures and identical snapshots for every baseline; separate verified-quality, quota-window, attribution, duration, intervention, coverage and optimizer-cost measurements.
- Real experiment: manual gate T24 only; no provider usage without separate owner authorization. Without it, T24–T26 remain open and the report says so.

## Rulings
- D-042: preserve the existing per-task M2 API and add a versioned batch layer; M1 remains the only owner of reservations and retry decisions.
- M2 uses strict multi-window data. A provider source that cannot establish all relevant windows is unknown in strict automatic mode.
- Do not enable Laya based on the old synthetic corpus or the prior failed held-out result.
- T24 is an explicit authorization gate; "execute this plan" does not remove the plan's own conditional operator-authorization requirement.

## Progress log
- 2026-10-15 22:04: T1–T5 complete: T2 passed 26 contract tests; T3 reproduced its frozen baseline; T4 froze PLAN.json revision 2; T5 documented provider windows and attribution limits and passed 55 source tests. M5 remains isolated in its own worktree; primary M4/M5 changes remain untouched.
