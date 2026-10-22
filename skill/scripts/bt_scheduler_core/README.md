# bt_scheduler_core — the deterministic core (M1) of the Scheduler

Part of the methodology, isolated by construction (`references/modules.md`). Given an **approved `PLAN.json`**, it
answers one question: *which tasks are enabled, in what state is each, which resources can be reserved, and which
authorised action comes next.* It loads the plan, resolves the task DAG, runs a task/attempt state machine on a
transactional store, reserves capacity and resources atomically, hands orders to a **port**, ingests events
idempotently and reconciles after a restart.

**It contains no AI**: nothing that calls, configures or names a model or a provider, no semantic reasoning about code,
no network, no process launching. Decisions about *who* runs a task (M2), the real launching (M3), reading agent
output (M4) and retry strategy (M5) live in sibling modules that implement the ports below; here they are simulated.

## Boundaries (enforced by `tests/test_boundaries.py`)

- Imports only the standard library and itself; no other `bt_*` module, no third-party package; no network, process,
  `importlib`, `pickle`, `asyncio` modules; no `sleep` (the loop waits on an event).
- Names no methodology path or file; reads no environment variable. It works on **the plan text you pass in** and on a
  `StateRepository` you give it. Only `sqlite_repository.py` touches files (the run database); the plan is opened
  read-only.
- Everything it needs travels inside the package: parser, states, repositories, simulators, CLI, tests.
- The rest of the methodology reaches it through one adapter, `skill/scripts/bt_scheduler_adapter.py`; the dependency
  points one way only: adapter → `bt_scheduler_core`.

## Layout

| File | Role |
|---|---|
| `errors.py`, `config.py` | the single error type with stable codes; explicit operating limits (`Config`) |
| `plan.py` | approved-plan loader (hash-bound), DAG validation, ancestors/descendants |
| `states.py` | task / attempt / run vocabularies and the transition tables |
| `model.py` | serialisable `RunState` (the one operational record) and `AuditEntry` |
| `contracts.py` | versioned messages and the five ports (`typing.Protocol`) |
| `repository.py`, `sqlite_repository.py` | `StateRepository` contract, in-memory and SQLite-WAL implementations |
| `views.py` | read models: run status, per-task view, unreachable set, attention list |
| `transitions.py` | the only place that changes a task/attempt state, hold or outbox row |
| `reservation.py`, `resources.py` | atomic claim; resource claims and their conflicts |
| `events.py`, `recovery.py`, `operations.py` | applying facts/verdicts, recovery decisions & reconciliation, operator actions |
| `dispatch.py` | outbox delivery (write-ahead) and reconciliation queries |
| `scheduler.py` | `SchedulerCore`: transactions + ports + `step()`/`run()` |
| `rebase.py` | `rebase_run`: move a run onto revision N+1 keeping accepted, unchanged work (see *Rebase*) |
| `simulators.py`, `simulation.py` | deterministic doubles of M2–M5 and a scripted "world" |
| `cli.py`, `__main__.py` | command line |

## Contracts (event and assignment version `1.2.0`; full-plan routing contract `1.0.0`)

| Port | Direction | Methods |
|---|---|---|
| `PlanRoutingPort` | M1 ↔ M2 | `plan(PlanRoutingRequest) -> [PlannedRoute]` — all approved-plan tasks, including dependency-blocked tasks; one route result per task, no reservation |
| `AssignmentPort` | M1 ↔ M2 | `propose(AssignmentRequest) -> [Assignment]` — request includes the approved plan SHA-256, READY tasks, dependencies, acceptance criteria, verification and opaque classification metadata; M1 validates every proposal |
| `ExecutionPort` | M1 → M3 | `start(StartOrder)`, `cancel(CancelOrder)`, `query(attempt_id)`; every order has an idempotency key |
| `EventPort` | M4 → M1 | `SchedulerCore.ingest(Event)` and `.submit_verdict(Verdict)` |
| `RecoveryPort` | M1 ↔ M5 | `propose(FailureContext) -> RecoveryProposal` (`retry` \| `block` \| `wait`); advice only |
| `VerificationPort` | validator → M1 | `request(VerifyOrder)` out; the verdict returns through `submit_verdict` |
| `StateRepository` | M1 ↔ store | `transaction()` (atomic read-modify-write incl. audit rows), `audit_log(since)` |

Rules: no sibling can mark a task completed or write state; ports are called **outside** transactions; assignment
advice is validated and invalid proposals are audited before M1 skips them. The initial route port must return a
complete, valid map; otherwise startup is refused before dispatch. A port that raises during later assignment is
audited and leaves the task ready. `Event`: `event_id, plan_id, revision, task_id, attempt_id, source, kind,
occurred_at, payload, token, contract_version`; kinds `execution_started | execution_finished | execution_failed |
execution_cancelled | heartbeat | incident_observed`. Events are not exactly-once: duplicates, late and reordered ones
are expected. `incident_observed` is an M4 audit reference with a strict v1.2.0 allowlist and idempotency key; it may
append an audit row but cannot change task, attempt or lease state, including for a matching terminal attempt.
Contract 1.1.0 appended optional, defaulted fields to `TaskView` and `AssignmentRequest`, preserving old positional
calls. The scheduler emits 1.2.0 events by default; it continues to accept lifecycle events explicitly tagged 1.0.0,
whose shape is unchanged.

The additive `PlanRoutingPort` contract is versioned independently as `1.0.0`. At run creation M1 sends the complete
DAG to M2 and persists one non-reserving route recommendation per task in its run state. An incomplete or malformed
route map blocks run startup before executor reconciliation or dispatch. M2's READY assignment request still runs
when a task becomes dispatchable, so the current route is re-evaluated against current local eligibility and quota
facts. `RUN.projection.json` joins the frozen task classification with the current recommendation for operator review;
the approved `PLAN.json` remains immutable.

Absent ports: no assignment port → plan-order FIFO with the label `local`; no execution port → orders wait in the
outbox (`pending_orders()` for pull-style adapters); no recovery port → "retry while the attempt budget lasts, then
block". `Config` (all explicit, none inferred from the plan; an estimate is never a timeout): `max_parallel_tasks=1`,
`max_attempts=1`, `lease_seconds=300`, `reconcile_seconds=60`, `repository_isolation="shared"`,
`unknown_surface="serialize"`, `max_recovery_wait=3600`, `max_recovery_waits=3`, `max_deliveries=5`,
`require_independent_verifier=True`, `exclusive_scopes=()` (plan `scope` values whose tasks claim their whole repository
exclusively: the one classification field the core reads, and only when the operator names values here). A recovery `wait` always holds at least one second and, like any wait, is not
progress. `run()` also returns when the only live attempts left are `uncertain` (an operator must resolve them).
The outbox is bounded: past 1000 items, settled orders of closed attempts are pruned (newest 500 kept).

## States

Task: `pending → ready → active → completed`; `active → recovering → ready | blocked`; `blocked` and `recovering` may move to `ready` by an
authorised `reopen`; `completed → pending` only by `rework`; `cancelled`. *Attempt*: `reserved → dispatched → running → verifying → accepted`, or `failed |
rejected | cancelled | uncertain`. Run: `running | paused | completed | blocked | cancelled` (derived).
`completed` needs an **independent verdict, correlated to the current attempt, with evidence**; an executor's "finished"
only reaches `verifying`. Tasks downstream of a blocked/cancelled task are reported as `unreachable` (derived, never
stored), so reopening frees them. `blocked` never stops independent branches, and "nothing left to run" is never success.

## Rework (an audit rejected accepted work)

`core.reject_and_rework(verdict, task_ids, by, reason)` applies a **rejecting** verdict and, in the same transaction,
sends `task_ids`, everything downstream of them and the rejected task itself back to `pending` (fresh attempt budget,
`reworks += 1`); tasks whose prerequisites are all still completed become `ready` at once. Nothing is completed by it:
redone work needs a new independent verdict. When it cannot start the outcome depends on why: a **live attempt** in scope defers the whole verdict (status
`deferred`, nothing applied, the caller offers it again); a task already sent back `Config.max_reworks` times (default
2) applies the verdict and **blocks** the rejected task at once (`rework_limit`, audit `rework_refused`) because another
attempt cannot fix it; a cancelling run just applies the verdict. Repeating the same verdict reworks once.
`core.rework(task_ids, by, reason)` is the owner's version (no limit; refused while a live attempt is in scope) and
`core.rework_problem(...)` says in advance why a rework would not start (`busy:`, `limit:` or `cancelled:`).

## Persistence decision

One authority per run: the `StateRepository`. `SqliteRepository` (WAL, `BEGIN IMMEDIATE`, one connection per
transaction) keeps the run as a JSON document plus an append-only `audit` table changed in the same transaction;
concurrent threads and processes queue on the database lock. The in-memory repository has the same contract. Chosen over
event sourcing for simplicity at plan scale (hundreds of tasks); the audit log is the history. Historical files of the
methodology are never read or written by this module; a `RUN.json`-style projection is the adapter's job.

Run-state schema 2 adds the durable per-task route recommendation map and the completed-map marker. The loader upgrades
schema-1 state in memory and writes schema 2 on the next state change; older M1 versions reject schema 2 rather than
silently dropping route decisions.

## Dispatch and restart

Reserve + dispatch intent are one transaction; `deliveries` is incremented **before** the port call; the call is made with
the idempotency key; the answer is recorded. After a crash a pending order with `deliveries > 0` is first **queried**: the
executor says running/finished/failed (learned), `not_found` (never received: sent once more), or nothing (the attempt
becomes `uncertain`, the reservation stays, no second writer). A lapsed lease or a stale heartbeat only triggers a query,
never a verdict of death. Attempts carry a fencing `token`; events with another token or for a superseded attempt are `stale`.

## Command line

`python -m bt_scheduler_core <action>` (folder containing the package on `PYTHONPATH`); exit 0 ok, 2 refused/invalid.

- `validate PLAN.json --sha256 H [--plan-id ID] [--revision N] [--json]` loads against the approved hash.
- `simulate PLAN.json --sha256 H [--db FILE] [--parallel N] [--max-attempts N] [--fail T[:N]] [--reject T[:N]] [--json]`
  runs the whole plan against in-process doubles (no provider, no network).
- `status PLAN.json --sha256 H --db FILE [--json]` read-only snapshot of a persisted run (refuses another plan).
- `audit --db FILE [--since SEQ] [--json]` the audit trail.

## Python API

```python
import bt_scheduler_core as sc
plan = sc.load_plan(text, approved_sha256=approved_hash)            # raises SchedulerError; creates nothing
core = sc.SchedulerCore(plan, sc.SqliteRepository("run.db"), config=sc.Config(max_parallel_tasks=3),
                        ports=sc.Ports(assignment=m2, routing=m2, execution=m3, verification=validator, recovery=m5))
core.start()                                                        # create the run or verify it is this plan
core.run()                                                          # event-driven; or call core.step() yourself
core.ingest(event); core.submit_verdict(verdict); core.snapshot(); core.audit_log()
core.pause(by) / resume / cancel / reopen(task_id, by) / resolve_attempt(attempt_id, outcome, by)
```

## Rebase (a new approved revision without losing accepted work)

`rebase_run(repository, old_plan, new_plan)` moves the persisted run from revision N to N+1 in one transaction.
An accepted task whose *fingerprint* (id, prerequisites, repository, acceptance criteria, verification; never the
classification) is unchanged, and whose prerequisites were all kept, stays accepted with its attempts and route.
Every other existing task returns to `pending` with a fresh attempt budget (its old attempts stay in the history);
new tasks start `pending`; removed tasks leave the run. A run with a live attempt is refused (`NOT_ALLOWED`), and so are
another plan id, a revision that is not later, and a cancelled run; a run bound to another plan is `PLAN_MISMATCH`.
Audit: `run_rebased {from_rev, to_rev, kept, reset, added, removed}` plus a `task_transition` (`decision: rebase`) per
reset task. After it, `SchedulerCore(new_plan, repository).start()` binds the run to revision N+1.

## Errors (stable codes, `SchedulerError.code`)

`PLAN_UNREADABLE`, `PLAN_NOT_APPROVED`, `PLAN_INVALID`, `PLAN_SCHEMA_UNSUPPORTED`, `PLAN_MISMATCH`, `STATE_UNREADABLE`,
`STATE_MISSING`, `STATE_UNAVAILABLE`, `ILLEGAL_TRANSITION`, `CONFIG_INVALID`, `UNKNOWN_TASK`, `UNKNOWN_ATTEMPT`,
`NOT_ALLOWED`, `CONTRACT_VIOLATION`, `ROUTING_UNAVAILABLE`, `ROUTING_INVALID`.

## Acceptance evidence (plan SC-AC01..20 → tests; `tests/test_readme.py` checks every name exists)

| AC | Evidence |
|---|---|
| SC-AC01 no AI | `test_no_ai_vocabulary_in_package_code`, `test_importing_and_running_pulls_in_no_network_process_or_provider_module` |
| SC-AC02 parent & interfaces | `test_only_standard_library_and_the_package_itself_are_imported`, `test_ports_are_structural_protocols_any_object_can_implement` |
| SC-AC03 approved plan | `test_a_contract_example_plan_loads_bound_to_id_revision_and_hash`, `test_loading_a_file_never_modifies_it`, `test_valid_json_is_not_an_approved_plan` |
| SC-AC04 invalid plan | `test_unreadable_inputs`, `test_cycles_are_reported_with_the_path`, `test_a_failed_load_leaves_no_state_anywhere`, `test_a_persisted_run_of_another_revision_or_hash_is_refused_and_left_untouched` |
| SC-AC05 dependencies | `test_dependent_waits_until_the_prerequisite_is_completed_and_verified` |
| SC-AC06 parallelism | `test_independent_tasks_run_together_up_to_the_configured_capacity`, `test_six_plus_tasks_three_independent_branches_run_in_parallel_and_complete` |
| SC-AC07 no double run | `test_one_winner_per_task_in_memory`, `test_one_winner_per_task_with_sqlite_connections`, `test_separate_processes_cannot_both_win_the_same_task` |
| SC-AC08 shared resources | `test_exclusive_resource_serialises_tasks_and_releases_on_completion`, `test_incompatible_resources_are_never_both_held_under_a_race` |
| SC-AC09 valid states | `test_invariants_hold_under_random_interleavings`, `test_illegal_transitions_are_refused_and_the_transaction_rolls_back` |
| SC-AC10 verification mandatory | `test_started_then_finished_moves_the_attempt_but_never_completes_the_task`, `test_the_executors_own_label_cannot_accept_its_work` |
| SC-AC11 duplicate events | `test_the_same_event_twice_equals_once`, `test_the_same_verdict_twice_equals_once` |
| SC-AC12 late events | `test_a_late_event_of_an_old_attempt_cannot_touch_the_current_one`, `test_a_wrong_fencing_token_is_stale` |
| SC-AC13 idempotent dispatch | `test_crash_after_the_executor_took_the_order_never_starts_a_second_writer`, `test_crash_between_reservation_and_delivery`, `test_losing_any_one_commit_never_breaks_the_outcome` |
| SC-AC14 local failure | `test_a_failed_branch_does_not_stop_independent_branches`, `test_one_local_failure_blocks_only_its_own_descendants` |
| SC-AC15 safe restart | `test_memory_store`, `test_sqlite_store_reopened_by_a_fresh_connection`, `test_an_old_heartbeat_or_lapsed_lease_never_declares_an_attempt_dead` |
| SC-AC16 M2/M5 failure | `test_a_crashing_recovery_module_does_not_stop_the_core`, `test_unavailable_or_garbage_answers_leave_the_state_intact` |
| SC-AC17 correct result | `test_no_ready_tasks_is_not_success`, `test_paused_is_not_completed`, `test_cancelled_run_is_not_completed_and_keeps_finished_work` |
| SC-AC18 compatibility | methodology suite `tests/test_scheduler_integration.py` (historical fixtures read-only, hash-checked) |
| SC-AC19 observability | `test_every_audit_entry_is_identifiable`, `test_every_task_transition_in_the_audit_trail_is_legal_and_chained` |
| SC-AC20 no providers | `test_a_whole_simulation_runs_with_the_network_and_processes_forbidden`, `test_the_whole_session` |

Run the module's suite from anywhere: `python -I -m unittest discover -s <path>/bt_scheduler_core/tests`; the isolation test
runs it again from a lone copy of the package.
