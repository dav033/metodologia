# M5 recovery manager

M5 turns verified failure facts into bounded `retry`, `wait`, or `block` recommendations.
It does not execute processes, change scheduler state, choose accounts, read provider logs,
modify worktrees, or accept rejected work. The policy uses only its immutable arguments;
the optional SQLite store records M5 decisions, never M1 task state.

## Public API and contracts

```python
from bt_scheduler_recovery import DecisionStore, Policy, RecoveryCase, propose

case = RecoveryCase(
    run_id="run-1", plan_id="plan-1", revision=1, plan_sha256="a" * 64,
    task_id="T-001", attempt_id="A-001", token=1, core_cause="execution_failed",
    technical_cause="connection_lost", confidence="reported",
    evidence_refs=("ledger:" + "b" * 64,), handoff_sha="c" * 64,
    execution_state="failed", current=True, identity_verified=True,
    transient_confirmed=True, max_attempts=3, failure_at=100, now=101,
)
assert propose(case).action == "retry"
with DecisionStore("/tmp/m5-example-private/decisions.db") as store:
    decision = store.decide(case, Policy())
```

Exports: `RecoveryError(code)`, `RecoveryCase`, `Policy`, `RecoveryDecision`,
`HistorySummary`, `DecisionStore`, `propose`, `inspect_store`.
`RecoveryCase.to_dict/from_dict` uses schema `m5.recovery-case/1`;
`RecoveryDecision.to_dict/from_dict` uses `m5.recovery-decision/1`.
Direct constructors and wire readers validate closed causes, enums, finite numbers,
bounded identifiers and opaque evidence refs. Unknown wire fields fail. Evidence refs
must have the form `scheme:<64 lowercase hex digits>`; hashes, never paths or raw logs.
The adapter is responsible for hashing/redacting evidence and proving identity, exact
plan SHA-256, revision, fencing token, current attempt, terminal state and handoff snapshot.

`propose(case, policy=Policy(), history=HistorySummary())` is pure and deterministic.
History counts **prior distinct attempts** of the same run/task/technical cause, not
the number of cooldown decisions on one attempt. `same_cause_attempts=2` blocks with
the default policy. A timeout permits only one retry. All transient cases require
explicit transience evidence, a verified handoff and attempt budget. Reported or
confirmed structured evidence is accepted; inferred/unknown evidence blocks.
Verification rejection additionally requires a verifier reference and finished
execution; it produces a retry recommendation and never an acceptance.

Safety and exclusivity guards precede evidence and budgets. Cancelled, live,
uncertain, stale, mismatched and unverified attempts cannot recover automatically.
Permanent/unknown causes block. Quota reset is never inferred: a known reset plus
margin must fit both wait and elapsed budgets. Backoff deadlines are absolute from
`failure_at`, so polling cannot move a cooldown forward forever. Policies do not
assign a route: `same_route` and `reevaluate` are hints for an authorized adapter/M2.

## Persistence, concurrency and crash behavior

`DecisionStore(path, max_decisions=10000, timeout_seconds=2)` supports context
management, `decide`, `latest(run_id=None, task_id=None)`, `metrics`, and `close`.
`BEGIN IMMEDIATE` serializes decision lookup, prior-attempt counting and insertion.
SQLite uses full synchronous commits. A crash before commit rolls back; a crash
after commit returns the existing decision on restart. Lock waits have a deadline.

Logical identity includes run, frozen plan hash and revision, task, attempt, token,
recovery round and the complete policy configuration. A repeated case returns the
same decision even if `now` advances. All other case facts must agree or
`CASE_CONFLICT` fails closed. **The adapter must check current identity, cancellation
and liveness before replaying stored advice.** Increment `recovery_round` only after
M1 has applied a wait; use the official number of waits, not a local retry counter.
This allows a later round to change `wait` into `retry` after the original cooldown.

New directories have mode 0700 and databases mode 0600. Existing database symlinks,
foreign schemas and public POSIX database permissions are refused. No history is
silently deleted: when the configured bound is reached, new decisions fail closed
with `STORE_FULL`, while existing logical keys remain available for idempotency.
An operator must stop the affected run, inspect/export its decisions and explicitly
choose a new dedicated store/capacity before resuming; M5 never removes its ledger.
Metrics report stored decision/action counts, not unmeasured interventions avoided.

Stable input/storage errors: `INVALID_INPUT`, `SCHEMA_MISMATCH`, `UNKNOWN_FIELD`,
`CASE_CONFLICT`, `STORE_FULL`, `STORE_BUSY`, `STORE_CLOSED`, `STORE_SCHEMA`,
`STORE_PATH`, `STORE_PERMISSIONS`, `STORE_MISSING`, `STORE_IO`.
Error text contains only the code, never untrusted facts or filesystem paths.

## Read-only operations

```bash
python -m bt_scheduler_recovery inspect --store /path/to/decisions.db --json
python -m bt_scheduler_recovery metrics --store /path/to/decisions.db --json
```

Inspection exposes the last decision, reason, absolute cooldown, waits remaining and
human intervention flag. Omit `--json` for text. Inspection never creates a database,
parent directory or schema; a missing file exits 2 with `STORE_MISSING`.
`inspect_store(path, metrics=False)` provides the same read-only API.

## Durable diagnostics and semantic progress

`DiagnosticStore` adds schema 2 transactionally while retaining every schema-1 decision row and the
existing `DecisionStore` retry/wait/block API. It stores `recovery-case/1` triggers, append-only
events, generation-fenced leases and application checkpoints. Replaying the same trigger and case
is idempotent; reusing its trigger with different case or proposal facts fails with
`CASE_CONFLICT`. A transition requires the current generation and an unexpired lease owned by the
caller, then appends its event and advances that generation in one transaction.

Finding occurrence identity is `<ledger_digest>:<local_finding_id>`. A cross-ledger semantic match
exists only as an explicit `same_finding` relation with evidence references; no F-number or prose
signature is used to infer continuity. `assess_progress(previous, current)` reports persisted,
fixed, new, regressed and uncertain occurrences, plus blocked prerequisite checks. Missing evidence
or an unmatched prior open finding remains uncertain. `RecoveryProposal.from_dict` accepts only
`recovery-proposal/1`. `VerificationMap` binds repository-relative changed paths and source digests
to owner tasks, existing owner commands, symptom-specific checks and opaque verdict references;
uncovered paths and checks remain explicit and cannot become an implicit pass.

## Independent verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python -m unittest discover \
  -s skill/scripts/bt_scheduler_recovery/tests -v
```

The suite covers hostile contracts, safety/cause matrices, absolute cooldowns,
bounded repeated rounds, twenty concurrent duplicate writers, transactional cause
limits, restart, crashes before and after commit, store limits, permissions, opaque
refs, read-only CLI and a copied package tested alone under `python -I` from an
unrelated directory. No providers, credentials, paid requests or real sleeps are used.
Cross-module acceptance, M1 application and the real executor handoff are adapter
integration responsibilities tested outside this independent package.


## Structural recovery (REQ-029)
M5 stays advice-only. REQ-029 adds, outside it: evidence capture (`bt_recovery_evidence`), conflict observations published before
clipping (`bt_recovery_conflicts`, `conflict_contracts/policy/delivery`), a constrained compiler and convergence work
(`bt_recovery_compiler`, `bt_recovery_convergence`), a run-scoped authorization ledger (`bt_recovery_authorization`), journaled
application through one generic M1 revision primitive (`bt_recovery_apply`) and the owner lifecycle (`bt_scheduler_recovery_lifecycle`).
One cycle per run and lineage, at most eight corrective tasks, ordinary counters never reset. Boundary, migration and rollback:
`reviews/req029-rollout.md`. The common stops are handled earlier by `bt_scheduler_healing` (`references/modules.md` §self-healing).
