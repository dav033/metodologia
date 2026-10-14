---
req: REQ-011
status: approved
created: 2026-10-14
---
# Plan — REQ-011 — Scheduler Core M1 (`bt_scheduler_core`)

## Approach
Build `skill/scripts/bt_scheduler_core/` as an isolated, stdlib-only package (convention `references/modules.md`):
pure engine over a serialisable `RunState`, a `StateRepository` port (in-memory + SQLite WAL, one transaction = one
state change + its audit rows), ports as `typing.Protocol`s with deterministic simulators, event-driven loop with an
injectable clock. Ports are called OUTSIDE transactions with write-ahead outbox rows. Methodology integrates through one
adapter `bt_scheduler_adapter.py`. The detailed SC-H/SC-T breakdown of `PLAN-SCHEDULER-CORE-M1.md` is mapped 1:1 below.
Alternative rejected: touching `bt_run*` in place (couples the core to the supervisor and risks live RUN.json).

## Global constraints
No AI/SDK/prompt in the package; `PLAN.json` and historical RUN.json read-only; one write authority per run; no push.

## Tasks

### M1 — Baseline and contracts (SC-H1)
- [x] T1 — Map the existing supervisor and answer plan §12 against the real code (explorer) (SC-T01)
- [ ] T2 — Freeze historical compatibility baseline: read-only hash fixtures of REQ-013..016 RUN.json/PLAN.md (SC-T02) · after: T1
- [ ] T3 — README with versioned port contracts + persistence decision; package skeleton and boundary test (SC-T03) · after: T1, T2

### M2 — Plan, DAG, state machine (SC-H2)
- [ ] T4 — Plan loader bound to approved sha256/plan_id/revision (SC-T04) · after: T3
- [ ] T5 — DAG resolution, eligibility, unreachable dependents (SC-T05) · after: T4
- [ ] T6 — Formal task/attempt state machine with guards and invariants (SC-T06) · after: T4

### M3 — Persistence, reservations, dispatch (SC-H3)
- [ ] T7 — Transactional repository (memory + SQLite WAL) and audit log (SC-T07) · after: T6
- [ ] T8 — Atomic reservations: capacity, resource claims, leases, fencing (SC-T08) · after: T5, T7
- [ ] T9 — Outbox dispatch with idempotent delivery against a fake executor (SC-T09) · after: T8

### M4 — Event loop and recovery boundary (SC-H4)
- [ ] T10 — Event ingestion, dedupe, verdict channel, event-driven loop (SC-T10) · after: T9
- [ ] T11 — Startup reconciliation and restart tests at every critical transition (SC-T11) · after: T10
- [ ] T12 — Decision/Recovery boundaries with mocks, deterministic fallbacks, completion semantics (SC-T12) · after: T10, T11

### M5 — Integration, evidence, delivery (SC-H5)
- [ ] T13 — Simulators, CLI `python -m bt_scheduler_core`, end-to-end and isolation tests; SC-AC01..20 evidence map (SC-T13) · after: T12
- [ ] T14 — Adapter + packaging + methodology integration/compat tests (SC-T14) · after: T11, T13
- [ ] T15 — Docs (`modules.md`, SKILL router), independent review (antagonist + reviewers), report, bitácora, D-021 (SC-T15) · after: T13, T14

## Verification
Module suite (`python -I -m unittest discover` from a lone copy), methodology suite incl. integration, packaging suite;
SC-AC evidence table in REPORT.md mapping each AC to a test.

## Rulings
<!-- Judgment calls made during execution without asking -->

## Progress log
<!-- One line per meaningful step -->
