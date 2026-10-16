---
id: REQ-020
status: in-progress
created: 2026-10-15
track: deep
---
# REQ-020 — Scheduler M2 learning and quota optimization

## Authority
David explicitly requested execution of the complete source plan on 2026-10-15. The plan is preserved unchanged in `SOURCE-PLAN.md`; this SPEC and `PLAN.md` make its scope and acceptance traceable through Bitácora. No second approval gate is needed for the approved local work.

## Problem and goal
M2 already filters configured routes, ranks one task at a time, reads a single aggregate quota pressure and summarizes route history. It does not yet learn from independently verified task outcomes by context or optimize several READY tasks against shared accounts and multiple quota windows. Extend the existing M2 package so M1 can receive safe, explainable batch recommendations while M1 remains the authority for reservations, task state and dispatch.

Success means a deterministic, replayable assignment plan for a bounded READY batch, using only authorized routes and fresh observed quota windows; contextual measurements use correlated verified outcomes and report uncertainty; unavailable evidence falls back to the current deterministic policy. M2 does not claim real quota savings until an honest comparison demonstrates them.

## Actors
- M1 Scheduler Core supplies approved plan identity, READY tasks and `free_slots`, then validates and reserves proposals.
- M2 Decision Engine filters routes, estimates evidence conservatively and proposes task-to-route assignments.
- Existing subscription readers, profiles, provider catalog and telemetry remain the sources of truth.
- M3 executes only M1-accepted assignments; M4/M6 facts are consumed only through validated adapters when available.
- M5 proposes `retry`, `wait` or `block` to M1; M1 may request a fresh M2 assignment after an approved retry.

## Scope
1. Normalize observed quota by effective account and all known relevant windows; preserve source, observation time, expiry and reset confidence.
2. Estimate demand only from comparable, attributable observations; keep provider tokens, quota percentages, forecasts and unknown values separate.
3. Learn contextual route measurements from independent, attempt-correlated PASS/FAIL evidence with sample counts, uncertainty, temporal separation and deterministic replay.
4. Enumerate supported configured routes without adding a second provider catalog or bypassing account/project/auth/runtime/work-only/cooldown filters.
5. Select a bounded READY batch against `free_slots`, shared-account observations and configured concurrency limits, with stable tie-breaking and no durable M2 reservation.
6. Persist versioned, redacted reasons and snapshots; support shadow comparisons and deterministic fallback.
7. Integrate through the existing M1 assignment boundary and M1-mediated retry flow. M2 must not call M5 or execute retries.

## Out of scope
- Owning or mutating M1 task, attempt, run, reservation or SQLite state.
- M3 process supervision/execution, M4 stream monitoring, M5 recovery policy, or M6 verification policy.
- Provider inference during ranking, synthetic provider inventories, converting subscription percentages to tokens/dollars, or global multi-project scheduling.
- Activating Laya without its existing quality gate and new evidence; changing credentials, installing live runtime components, pushing, merging, deploying, or paid/live experiments without explicit authorization.

## Requirements
- R1. For an M1 request, M2 considers only the supplied READY tasks and proposes at most `free_slots` distinct task assignments; M1 remains the final authority.
- R2. M2 deduplicates quota by opaque effective `account_ref`; each relevant fresh window is checked independently, including model-specific limits. Stale, unknown, malformed, exhausted or invalid-auth states are never treated as capacity.
- R3. Route enumeration comes from current configured catalogs and verified capabilities; project authorization, work-only policy, credentials, runtime, cooldown, workspace conflicts and known concurrency limits are hard filters before ranking.
- R4. Quota demand, reported tokens and utilization percentage have separate types and provenance. Unattributable or contaminated changes remain unknown; estimates carry sample count, interval/conservative bound and TTL.
- R5. Learning accepts success only when an independent PASS is correlated to the same plan revision, task, attempt, route and decision. Claims, exit code 0, unknown quality, infrastructure failure and synthetic fixtures never become verified successes.
- R6. Contextual aggregates expose raw counts, source quality, uncertainty and coverage; sparse or missing context falls back through exact context, nearby class, task family, route aggregate and existing baseline without claiming calibration.
- R7. Reprocessing is idempotent by stable attempt/verdict identity. Decision records include policy/schema, input and quota fingerprints, batch identity and learning cut-off/source digest; sensitive task text, secrets and raw provider output are not persisted.
- R8. Batch optimization is deterministic and bounded, observes shared accounts and declared concurrency limits, emits stable no-assignment reasons, and does not write durable reservations or move an active attempt.
- R9. M2 remains usable without M4/M6 and without Laya. Laya may only order already eligible routes; failure or an unpassed gate uses deterministic routing.
- R10. M5 and M2 are coupled only through M1. Following an M1-authorized retry, M2 reads current quota and proposes normally; `wait`/`block` never causes an M2 retry loop.
- R11. Offline fixture comparisons cover legacy, FIFO, eligible round-robin, deterministic M2 and contextual M2; report quality, quota coverage, attribution coverage, elapsed time and human-intervention coverage separately.
- R12. Any real 8–12 task experiment remains opt-in and requires a separate explicit owner authorization before provider processes consume subscription quota.

## Acceptance
The source plan's ten Definition-of-Done items remain binding. In particular: hard account/quota/quality filters pass; only independent correlated outcomes count as successes; missing data remains unknown; M1/M3/M5 contracts and M4/M6 fallbacks remain compatible; offline benchmarks are reproducible and honest; and the real experiment is explicitly marked pending unless authorized and completed.

## Constraints and compatibility
- Preserve the current M2 1.1.0 quota-evidence record fields already present in the dirty primary worktree; the M2 feature API evolves additively to 1.2.0 and reads existing 1.0.0/1.1.0 records.
- M1 contract changes are owned by one integrator only. M5's approved D-041 keeps `FailureContext` and `RecoveryProposal` semantics unchanged and remains isolated from M2 internals.
- Read cached subscription observations only; `propose()` performs no network calls, authentication refresh or cache writes.
- No new dependencies, paid services, provider catalog, direct database writes, commits, pushes or merges.
- Code and repository docs are in English; user reports are in Spanish.

## Source mapping
The M2-T01…M2-T26 identifiers and full technical details in `SOURCE-PLAN.md` map in order to T1…T26 in `PLAN.md`. The source plan is unchanged. See `CONTRACTS.md`, `INVENTORY.md` and `baseline-report.json` for the live contract, inspected state and frozen baseline.
