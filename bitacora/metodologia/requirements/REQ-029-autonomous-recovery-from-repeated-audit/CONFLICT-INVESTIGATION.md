# Structural integration conflict recovery — investigation

## Owner request

The owner asks for a special automatic system protocol for recurring plan-level integration conflicts. REQ-027 T15a clashes with T3/T15 contracts and T15b shared web files; repeated minimal-rebuild notes did not resolve it. The goal is system recovery, not coordinator-written product fixes or manual CLI procedures.

## Live state verified on 2026-10-20

- REQ-027 r9: T15a blocked, 8 attempts, decision T15a:8; no active attempt. Error is `integration gate: T6+T7+T15a vs T15b for T15c` with shared README, snapshot fixture, mock gateway, CSS and further paths truncated by the card. Full official evidence must be read before choosing a correction.
- Cached agent diagnosis identifies plan/task ownership conflict and recommends stop, ownership/order changes, freeze and revise. The actual decision offers only retry, retry_with_note and stop; revise is not offered.
- REQ-029 r1: T1–T3 accepted, T4 att-0004 was active. The owner paused the Codex goal. Both Scheduler runs are now on hold; T4 was cancelled explicitly to honor the pause, with its isolated worktree/evidence preserved. No task has been manually repaired and no plan revision has been applied.

## Confirmed source gaps

- `bt_block_diagnosis.CONFLICT` recognizes only `INTEGRATION_CONFLICT:`. M6 emits `integration gate:` for the same class; the rules then classify the repeat as code/retry_with_note.
- `bt_scheduler_integrator._merge` clips conflict evidence to six files and 170 characters before raising. A new protocol must persist full structured evidence before presenting a short summary.
- Live M1 state confirms `gates.max_reworks=2`, T15b completed with reworks=2, T6 completed with reworks=3, T7 completed with reworks=0, T15a blocked with reworks=1. For the current pair, `_dependents_to_redo` selects only T15b, so `rework_problem` returns `limit: T15b was already sent back 2 time(s)`. The adapter discards that reason.
- The quality adapter `_dependents_to_redo` returns no correction targets if `core.rework_problem` refuses the accepted other side; delivery then rejects the candidate again as an integration gate failure. Persist the refusal reason and route this branch to structural recovery.
- M5 policy blocks `integration_conflict` as a permanent/unknown cause; verification rejections may enter ordinary retry and eventually same_cause_limit.
- Existing conflict resolution/rework and integration gates handle stale-result rebuilding, but no durable executable protocol repairs repeated structural ownership/dependency collisions.
- Verified PLAN r9 already orders `T3 -> T15 -> T15a -> T15b -> T15c` (T15c also follows T7). T15/T15a/T15b/T15c each declare broad `remote/web/**`, while T3 owns contracts/docs. Thus a structural ownership defect is a hypothesis, not proven by overlapping paths alone; stale accepted descendants and actual scope escape must be distinguished.
- Adding an ordering edge alone does not prove that already accepted conflicting snapshots integrate. Recovery must produce and verify a converged snapshot preserving both accepted behaviors, or identify a real semantic/product conflict.

## Red-capable reproduction (executed, exit 1)

Run from repository root:

```python
import sys
sys.path.insert(0, 'skill/scripts')
import bt_block_diagnosis as diagnosis
error = 'integration gate: T6+T7+T15a vs T15b for T15c: remote/web/README.md, remote/web/src/app/globals.css'
request = {'task': 'T15a', 'reason': 'same_cause_limit', 'error': error,
           'options': [{'id': 'retry'}, {'id': 'retry_with_note'}, {'id': 'stop'}]}
result, _ = diagnosis.explain(request, {}, failures=[error], repeats=2, req='REQ-027')
assert result['kind'] == 'conflict'
```

Observed: `kind=code`, `option=retry_with_note`, headline `Los últimos 2 intentos fallaron exactamente igual`; AssertionError, exit 1. This reproduces misclassification only, not automatic repair readiness.

## Required protocol boundary for the amendment

Reuse REQ-029 M5/Planner/M1 recovery machinery, not another supervisor. Capture full structured conflict evidence and source identities; separate stale-result integration from ownership/order defects and genuine incompatible product requirements. Stop unchanged retries for this case; retain unrelated accepted work and permit independent work where safe. Propose a bounded scope-preserving ownership/order/convergence revision through Planner; validate DAG, paths, criteria, permission and verification coverage. M1 alone applies an idempotent revision with preserved counters and rollback. A new order must be followed by a verified integrated convergence result; never discard an accepted side or treat a schema-only revision as success. Reuse the approved bounded-cycle policy; no fabricated owner decision or unbounded retry. Replay T15a:8 through real CLI/Scheduler/verification entrypoints with external providers replaced by controlled fixtures. Semantic conflicts or insufficient authority/evidence stop with a specific question.

## Current execution constraint

The owner goal is paused. Prepare a reviewed candidate revision under `conflict-amendment/`; do not modify canonical SPEC/PLAN or immutable r1, freeze, rebase or resume either run until the owner resumes and approves the concrete scope change.
