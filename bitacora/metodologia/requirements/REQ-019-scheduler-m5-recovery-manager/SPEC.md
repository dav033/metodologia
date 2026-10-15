---
status: in-progress
---
# REQ-019 — Scheduler M5 Recovery Manager

Approved for local implementation and transversal verification by David on 2026-10-15:
`/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md`. That document is the complete acceptance source,
including T01–T20, R01–R18 and AC01–AC12; it remains unchanged.

## Contract and authority (D-041)

- Preserve M1 contract 1.2.0: `FailureContext` and `RecoveryProposal` signatures are unchanged.
- An isolated standard-library `bt_scheduler_recovery` owns deterministic policy and a private bounded
  decision ledger. Only `bt_scheduler_recovery_adapter.py` imports it from methodology production code.
- The adapter reads an atomic M1 state view through its public read callback and M3's public description.
  It checks active run/plan/hash/revision/task/attempt/token before proposing. It never opens M1's database.
- M3 terminal evidence is required for retry. Missing, uncertain, live, cancelled, stale or cross-boundary
  evidence cannot authorize another writer. Raw error text is never used to infer recoverability.
- RecoveryCase schema `m5.recovery-case/1` and policy 1.0.0 record only bounded identities, cause enums,
  timestamps and opaque SHA256 evidence references. M3/M6 raw logs and credentials are not persisted.
- M1 still enforces budgets and applies `retry|wait|block`. M2 receives a new normal assignment request
  on retry; internal routing hints are advisory only and never change accounts behind M1/M2.
- M5 is opt-in through the existing `wire()` adapter. M4 remains optional. No global daemon is activated.
- Retry continuation starts from the same task's preserved M3 snapshot and includes a sanitized continuation
  note in the next brief. Recheck M1/M3 identity and snapshot existence when allocating the next attempt.
  Never integrate a rejected attempt into another task or the primary checkout.
- Store failures produce an explicit conservative adapter block and M1 audit reference. A directly crashing
  third-party recovery port still follows M1's documented bounded fallback; invalid nonfinite proposals
  must fail validation. No new M1 public API or state migration is necessary.

## Verification seams

1. Pure policy API: hostile inputs, precedence, budgets, known/unknown reset, finite backoff and no optimism.
2. Public decision store/CLI: concurrency, durable idempotency, restart, bounded storage and private permissions.
3. `wire()` and Scheduler public operations: M3 facts, verification rejection, cancellation, stale tokens,
   crash checkpoints, unchanged legacy files and independent DAG branches.
4. Real Planner freeze → M1 → M2 → real M3 with fake provider processes → M4 → M5 retry:
   preserve partial/untracked files and require an independent verdict for completion.
5. Opt-in disposable real CLI experiment: explicit routes, strict time/budget bounds, controlled failure injection
   without exhausting any account. Never run provider tests implicitly in CI.

## Scope boundaries

Parent integrator owns shared adapter/wiring/packaging edits. Module worker uses a separate detached worktree
and owns only the new package. Independent reviewers are read-only. Existing uncommitted M4/REQ-018 and
Pictures work is preserved. No push, merge to main, live install/config/account change or file removal.

## Compatibility and rollback

Consumers: M1 RecoveryPort, optional M3 wiring, CLI inspection and package installation. M2/M4/M6 types do not
cross package boundaries. Existing `wire(recovery=...)` remains valid. Disable by omitting recovery_store_path;
keep the decision ledger and all M3 snapshots. No automatic cleanup or legacy RUN migration.
