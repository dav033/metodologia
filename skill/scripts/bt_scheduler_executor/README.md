# bt_scheduler_executor — the agent executor (M3) of the Scheduler

Part of the methodology, isolated by construction (`references/modules.md`). Given an **authorised order** from the
scheduler core (M1) and the **route** M2 selected for it, it launches one agent CLI in its own git worktree, supervises
the process, keeps every artefact, preserves the work **whatever way the agent ends** (clean, failed, out of quota,
connection lost, timed out, killed, cancelled, lost) and reports technical events. It survives its own restart.

It **runs and preserves; it never decides.** It does not choose provider/model/account (M2), reserve capacity or change
task/attempt state (M1), interpret what an agent says (M4), choose a retry (M5) or accept work (the independent verifier).
A clean exit is the event `execution_finished` = "the agent stopped". There is no code path that completes a task.

## Boundaries (enforced by `tests/test_boundaries.py`, `tests/test_isolation.py`)

- Imports only the standard library and itself; no other `bt_*` module. It names no provider, model, bitácora path or
  scheduler type; the only absolute paths in its source are `/proc` reads. POSIX only (process groups, `/proc` identity).
- Everything it needs from the world arrives through five **ports** (`typing.Protocol`); everything it answers uses its own
  small frozen dataclasses. The methodology reaches it through one adapter, `skill/scripts/bt_scheduler_executor_adapter.py`,
  which translates to and from the scheduler core's classes (`tests/test_scheduler_executor_integration.py` enforces that
  only the adapter imports the module).
- One live supervisor per executor root (`executor.lock`, `ROOT_BUSY`), one root per scheduler run (a foreign plan/revision
  is refused, `FOREIGN_RUN`).

## Layout

| File | Role |
|---|---|
| `model.py`, `errors.py`, `config.py` | value types and state vocabularies; the single error type with stable codes; explicit limits (`Config`) |
| `core_port.py`, `gates.py` | dependency-injected methodology port bridge and the exact frozen-plan/base-tree start gates |
| `ports.py` | `RouteResolver`, `BriefSource`, `AgentDriver`, `WorkspaceManager`, `EventSink` |
| `ledger.py` | SQLite (WAL) record: attempts with unique ids/keys, checked state machine, write-ahead event outbox |
| `executor.py` | `AgentExecutor`: `start`/`cancel`/`query`, the supervisor loop, prepare + spawn, watching, events |
| `spawn.py` | prepare + spawn: brief, worktree, prompt, launch through the driver, the detached shim, abort of a failed spawn |
| `settle.py`, `recovery.py` | closing an attempt (outcome → handoff → terminal event); putting unfinished attempts back under supervision after a restart |
| `shim.py`, `procinfo.py` | the detached per-attempt supervisor; process identity and signalling |
| `workspace.py`, `handoff.py`, `gitutil.py` | attempt, reconstructable subplan and candidate integration workspaces; the recoverable snapshot of the work; one safe way to run git |
| `classify.py`, `prompt.py`, `artifacts.py` | outcome → cause class; the agent prompt; the artefact directory |
| `simulators.py`, `cli.py` | provider-free doubles of the ports; `python -m bt_scheduler_executor` |

## Ports

| Port | Method | Notes |
|---|---|---|
| `RouteResolver` | `resolve(StartRequest) -> Route` | M2's opaque reference → provider/model/profile/effort. Unknown/stale → `ROUTE_UNRESOLVABLE`, never a default |
| `BriefSource` | `brief(StartRequest) -> Brief` | the frozen plan's task as the agent's brief |
| `AgentDriver` | `prepare(route, prompt, workspace, timeout) -> Launch`; `classify(route, raw, returncode, …) -> Classification` | provider knowledge: argv/stdin/account environment, and the provider's own reading of the output |
| `WorkspaceManager` | `allocate(request) -> Workspace`, `check(request)` | idempotent per attempt id; `GitWorkspaces` is the default |
| `EventSink` | `deliver(TechnicalEvent)` | at-least-once; raising = "not delivered, keep it" |

`Launch.env_remove`/`env_set` build the child environment (removals first, then sets); the values may be secrets and are
never persisted. Own types: `StartRequest` (idempotency key, plan/revision and optional approved SHA-256, task, attempt,
fencing token, route reference, repository role, base ref, optional timeout), `Route`, `Receipt` (`accepted | duplicate | rejected` + code),
`AttemptStatus`, `TechnicalEvent`, `Brief` (including optional frozen-plan `review_axis`), `Workspace` (kind `attempt`, `subplan` or `integration`), `Launch`, `Classification`.
`PLAN_SCHEMA_CAPABILITIES` — plan schemas M3 consumes (1.0.0–1.3.0; 1.3.0 adds subplan integration lines, the Designer
base-tree gate and the `composition_base` seam).

The methodology adapter derives subplan line membership from the frozen plan. In schema 1.3.0 plans with subplans,
accepted member-task deltas and accepted ancestors are folded under `refs/m3/line/<run>/<repository-role>/<SP-id>`;
redo replaces the prior delta and conflicts stay visible. Non-subplan tasks use the candidate/current commit injected by
the owner adapter and fail closed with `COMPOSITION_BASE_MISSING` when it is absent. UI implementer starts require the
exact declared design contract blob in the selected base commit tree (`DESIGN_CONTRACT_MISSING` otherwise). A visual audit
brief carries `review_axis: visual` from the frozen subplan metadata. `GitWorkspaces.reconstruct_subplan()` reconstructs a
scope commit; `allocate_integration()` checks out a candidate, and `release()` safely cleans either candidate workspace
repeatedly. Attempt workspaces retain their existing per-attempt lifecycle and receipt binding.

The Scheduler adapter always supplies the frozen plan hash. Older direct callers may omit it; a row written before the
field existed is accepted only as an idempotent replay and does not authorize M5 recovery evidence.

## Attempt life cycle

```
start ─ validate (route, repository, base ref, order shape) ─ REJECTED (stable record; replay answers the same)
      └ QUEUED ─ PREPARING (brief, worktree, prompt, shim spawn) ─ RUNNING   [execution_started]
                                     │                               │
                                     └───────────────┬───────────────┘
                                                     SETTLING (outcome persisted, handoff captured)
                                                     └ FINISHED | FAILED | CANCELLED   [exactly one terminal event, same transaction]
```

Every arrow is one atomic ledger transition (compare-and-set along legal edges only). A crash between any two is recovered.
`query` mapping for M1: queued/preparing/running/settling → `running`; terminal states as themselves; unknown id → `not_found`.

## The shim

An agent is never a direct child of the executor. `shim.py` is double-forked (re-parented to init), lives in its own session,
runs the agent in its own process group, enforces the timeout, keeps the output (head up to a cap in `output.log` + the
last window in `output.tail`, with a dropped-byte count), and writes `exit.json` atomically as its last act
(`reason: exited | timeout | cancelled | spawn_error`, `returncode`, bytes). `shim.json` records the shim's and the agent's
start-time identities. While the agent runs, the shim samples Linux `/proc` every 0.1 seconds and atomically records up to
4,096 observed descendant PID/start identities in `descendants.json`. After the agent exits the shim kills whatever is left
in its group: nothing outlives it to keep writing.
Executor restart = re-attach, finalise from `exit.json`, or (shim gone without record) stop the orphan by identity and report `lost`.
A pid is signalled only if its recorded start-time identity still matches.

The shim also drains stdout and stderr separately with one selector while continuing to build the existing combined
`output.log`/`output.tail` artifacts. A private `stream.fifo` carries versioned binary frames: the 24-byte header and up to
3,840 payload bytes stay below Linux `PIPE_BUF` (4,096 bytes). Writes use `O_NONBLOCK`; during startup the shim retries
an unavailable FIFO reader for at most 0.5 seconds so the Scheduler owner can attach after M3 creates the endpoint.
After that bounded grace, no reader or a full FIFO drops the whole frame and records bounded per-stream sequence/offset
ranges in `stream.json`. After the range cap, the final entry
is inferred as coalesced by the M4 adapter when its sequence span exceeds its exact dropped-frame count; it carries true
first/last sequence and offset bounds plus exact lost byte/frame totals,
even when healthy frames fall inside its bounding span. When delivery resumes, a compact gap frame precedes the next payload.
The shim's summary writer runs separately from pipe draining, so filesystem latency in
the status snapshot cannot hold the provider's stdout/stderr pipes open. `describe()` exposes this additive M3 summary;
`bt_scheduler_executor_adapter.M3StreamAdapter` validates and drains the private FIFO into the monitor's bounded in-memory
queue (10,000 frames / 16 MiB). The M1 lifecycle event sink does not receive stream payloads.

## Cause classes (facts, never decisions)

`clean`, `quota_exhausted` (with `reset_epoch` only when the provider gave one), `connection_lost` (patterns on the output of a
FAILING exit only), `agent_error`, `timeout`, `killed` (signal from outside), `incomplete_output` (exit 0 without the provider's
end-of-turn evidence: never `finished`), `start_failed`, `lost`, `artifact_error`, `cancelled`.

## Events (`EVENT_KINDS`)

`execution_started`, `execution_finished`, `execution_failed`, `execution_cancelled`, `heartbeat` — the names the core ingests.
Ids are deterministic (`<attempt>:started|finished|failed|cancelled`; heartbeats `<attempt>:hb:<epoch ms>`, hints only), so redelivery is idempotent.
Started/terminal events are written to the ledger outbox **in the same transaction** as the state change and delivered in order;
heartbeats are hints (not stored, never retried). The terminal payload carries the cause class, return code/signal, reset epoch,
provider/model/profile/effort as run, usage/cost as the provider reported them, output sizes, the handoff summary, artefact
paths and the agent's own report labelled a **claim**.

## Handoff (US-4)

At every end the executor captures, into `<attempt dir>/handoff/` and private refs, without touching the attempt's branch, its
real index or the base: base sha, branch, head sha, the commits above the base, **uncommitted + untracked files** as a snapshot
commit (`refs/m3/handoff/<dirname>`; HEAD pinned at `refs/m3/head/<dirname>`; ignored files excluded), a binary-safe
`changes.patch` (`base..snapshot`, capped), `log-tail.txt`, `manifest.json` and `continue.md`. The cases "commits only",
"dirty only", "both" and "nothing" are all distinguished (`empty: true`). `continue.md` is a plain-text brief for a *different*
agent or a human: **no agent reasoning or conversation is transferred between providers**, and its author's report is only a claim.

An explicit `Config(handoff_mode="patch")` provides an opt-in patch-only handoff for running agents against edited workspaces.
It builds `changes.patch` against the pinned base from the real working tree with a temporary index, records its byte length and
SHA-256, and leaves HEAD, the real index, branches and refs unchanged. The prompt tells the agent not to commit. Empty work is
captured as a valid empty patch. If the patch exceeds `patch_max_bytes`, the attempt's handoff fails with `PATCH_TOO_LARGE`; a
failure manifest is written and no captured status is reported. Patch-only handoffs have `snapshot_sha: null` and `refs: {}`.
Their manifests use schema 2; schema 1 remains the snapshot contract.
They can be applied manually with `git apply --binary` on the pinned base. Automatic predecessor integration requires snapshot
refs and therefore cannot consume patch-only handoffs. The default remains `handoff_mode="snapshot"` with existing behavior.

## Artefacts

`<root>/ledger.db`, `<root>/executor.lock`, `<root>/executor.log`, `<root>/ws/` (worktrees, intent manifests, `journal.jsonl`),
`<root>/attempts/<dirname>/` (0700; files 0600): `order.json`, `route.json`, `brief.json` (the full brief), `prompt.txt` (0600), `output.log`, `output.tail`,
`shim.json`, `descendants.json`, `exit.json`, `report.json` (if the agent wrote one), `handoff/`. History is never deleted; worktree cleanup is an
explicit operator action (`GitWorkspaces.release`).

## Configuration (`Config`, all explicit)

`handoff_mode="snapshot"` (or opt-in `"patch"`), `prompt_rtk=True` (optional RTK inspection guidance; verification stays RAW), `max_running=2` (a safety ceiling; M1 owns global capacity), `max_queued=64`, `timeout_seconds=1800`, `max_timeout_seconds=86400`,
`grace_seconds=10`, `spare_interactive=True`, `heartbeat_seconds=30`, `poll_seconds=0.5`, `output_head_bytes=8 MiB`, `output_tail_bytes=256 KiB`,
`classify_head_bytes=64 KiB`, `patch_max_bytes=16 MiB`, `log_tail_bytes=64 KiB`, `max_event_backlog=10000`, `deliver_batch=100`,
`spawn_wait_seconds=10`, `settle_retry_seconds=5`, `handoff_tries=3`, `handoff_retry_seconds=0.5`. An order's own timeout wins over the default, both capped by the maximum.

## Python API

```python
import bt_scheduler_executor as m3
x = m3.AgentExecutor(root, resolver=..., briefs=..., driver=..., workspaces=m3.GitWorkspaces(root / "ws", repos),
                     sink=..., config=m3.Config())
x.start(m3.StartRequest(...))          # -> Receipt   (idempotent; accepted | duplicate | rejected + code)
x.cancel(attempt_id, token, key, reason)  # -> Receipt   (fenced by token; idempotent)
x.query(attempt_id)                    # -> AttemptStatus (reflects process reality)
x.wait_idle(); x.describe(attempt_id); x.flush_events(); x.close()   # close() stops supervising, NOT the agents
```

## Command line

`python -m bt_scheduler_executor status|show|events --root DIR [--json]` (read-only) and `selftest [--keep DIR] [--json]`
(two attempts through the real executor with a scripted driver; exit 0 ok, 2 refused/failed).

## Errors (stable codes, `ExecutorError.code`)

`ORDER_INVALID`, `FOREIGN_RUN`, `ROUTE_UNRESOLVABLE`, `ROUTE_INVALID`, `POLICY_DENIED`, `REPOSITORY_UNKNOWN`, `BASE_UNRESOLVED`,
`QUEUE_FULL`, `KEY_CONFLICT`, `TOKEN_MISMATCH`, `UNKNOWN_ATTEMPT`, `WORKSPACE_ERROR`, `ARTIFACT_ERROR`, `START_FAILED`,
`LEDGER_ERROR`, `CONFIG_INVALID`, `PLATFORM_UNSUPPORTED`, `ROOT_BUSY`, `PORT_ERROR`.

The methodology adapter also returns typed start blockers in its core acknowledgment detail: `COMPOSITION_BASE_MISSING`,
`COMPOSITION_BASE_UNAVAILABLE`, and `DESIGN_CONTRACT_MISSING`. The latter is tagged `blocked-environment`; M1's current
`Ack` has no result-classification field, so an owner/runtime contract update is needed before M1 can preserve that class.

(`tests/test_resilience.py` also generates one test per crash point — accept, allocate, before/after RUNNING, before/after SETTLING,
during/after the handoff, before/after the terminal transaction, between delivery and the delivered mark — each killing the executor with
`os._exit` and checking one process, one terminal event, an intact handoff.)

## Acceptance evidence (SPEC US/R → tests; `tests/test_readme.py` checks every cited test exists)

| Requirement | Evidence |
|---|---|
| US-1 run once | `test_start.test_the_same_order_twice_is_one_attempt`; `test_start.test_the_same_order_delivered_concurrently_starts_one_process_in_the_end`; `test_reconcile.test_an_accepted_but_never_started_order_is_started_exactly_once_by_the_new_executor`; `test_hardening.test_a_preparing_attempt_whose_shim_died_but_whose_agent_lives_is_never_relaunched`; `test_reconcile.test_an_attempt_whose_shim_started_but_was_never_recorded_as_running_is_adopted_not_duplicated` |
| US-2 route, profile, model | `test_scheduler_executor_adapter.test_a_model_that_does_not_belong_to_the_provider_is_invalid`; `test_scheduler_executor_adapter.test_claude_gets_its_model_effort_and_profile_account`; `test_scheduler_executor_adapter.test_the_child_environment_drops_parent_session_state_and_foreign_credentials`; `test_scheduler_executor_integration.test_each_agent_got_exactly_the_model_effort_profile_and_worktree_it_was_assigned`; `test_scheduler_executor_integration.test_a_work_only_profile_cannot_run_a_personal_project`; `test_start.test_an_unresolvable_route_is_rejected_before_any_side_effect_and_never_defaulted` |
| US-3 isolated worktrees | `test_concurrency.test_eight_parallel_attempts_on_one_repository_stay_apart`; `test_concurrency.test_attempts_on_different_repositories_run_together_and_do_not_mix`; `test_workspace.test_parallel_allocations_on_one_repository_all_succeed_and_are_distinct`; `test_executor.test_the_concurrency_ceiling_is_never_exceeded_and_the_rest_wait_in_the_queue` |
| US-4 preserve the work | `test_handoff.test_commits_only`; `test_handoff.test_dirty_tree_only_modified_tracked_plus_untracked`; `test_handoff.test_commits_and_uncommitted_work_together`; `test_handoff.test_an_attempt_that_changed_nothing_is_reported_empty_not_missing`; `test_handoff.test_the_branch_the_index_the_base_and_the_worktree_are_untouched`; `test_handoff.test_patch_mode_reapplies_dirty_binary_and_deletion_without_mutating_git_state`; `test_handoff.test_patch_mode_preserves_committed_files_that_are_now_ignored`; `test_handoff.test_patch_mode_cap_overflow_fails_with_failure_manifest_and_no_stale_patch`; `test_handoff.test_patch_mode_overflow_keeps_prior_patch_without_advertising_it_as_current`; `test_classification.test_quota_exhaustion_still_preserves_the_half_done_work`; `test_hardening.test_a_clean_exit_with_work_that_cannot_be_preserved_is_a_failure_not_a_success` |
| US-5 facts, not verdicts | `test_executor.test_finished_means_the_agent_stopped_never_that_the_task_is_done`; `test_events.test_the_failed_event_carries_cause_handoff_and_artifact_paths`; `test_scheduler_executor_integration.test_an_agent_that_says_it_finished_is_not_a_completed_task_until_the_verifier_says_so`; `test_classification.test_a_clean_exit_without_end_of_turn_evidence_is_never_finished` |
| US-6 cancel | `test_cancel.test_a_queued_attempt_is_cancelled_and_never_spawned`; `test_cancel.test_a_running_attempt_is_stopped_its_work_preserved_and_one_cancelled_event_emitted`; `test_cancel.test_a_wrong_token_is_rejected_and_the_attempt_carries_on`; `test_cancel.test_cancel_racing_the_natural_exit_always_ends_with_exactly_one_terminal_event`; `test_scheduler_executor_integration.test_cancelling_the_run_stops_the_running_agents_and_preserves_their_work` |
| US-7 reconcile | `test_reconcile.test_a_live_agent_is_reattached_after_a_restart_and_finishes_once`; `test_reconcile.test_an_agent_that_finished_while_no_executor_was_alive_is_finalised_from_its_exit_record`; `test_reconcile.test_a_vanished_agent_with_no_record_is_lost_and_its_work_is_preserved`; `test_reconcile.test_a_recycled_pid_is_never_signalled`; `test_scheduler_executor_integration.test_an_executor_restart_in_the_middle_of_a_run_loses_nothing_and_starts_nothing_twice` |
| US-8 real CLIs | `test_scheduler_executor_real.test_claude_code`; `test_scheduler_executor_real.test_codex`; `test_scheduler_executor_real.test_gemini_through_antigravity` |
| R1 isolated module | `test_boundaries.test_only_the_standard_library_and_the_package_itself_are_imported`; `test_isolation.test_suite_passes_from_a_lone_copy`; `test_scheduler_executor_integration.test_only_the_adapter_imports_the_executor_module` |
| R2 write-ahead idempotent start | `test_ledger.test_processes_racing_to_insert_one_key_produce_one_row`; `test_start.test_the_same_key_with_a_different_order_is_rejected`; `test_start.test_a_replay_is_answered_even_if_the_route_would_no_longer_resolve` |
| R3 validate before side effects | `test_start.test_invalid_route_policy_denial_unknown_repository_and_bad_base_are_all_refused_up_front`; `test_scheduler_executor_adapter.test_the_work_only_gate_refuses_before_any_worktree_exists`; `test_hardening.test_the_base_is_pinned_when_the_order_is_accepted` |
| R4 worktree per attempt | `test_workspace.test_allocation_is_idempotent_per_attempt`; `test_workspace.test_two_attempts_never_share_a_directory_branch_or_index`; `test_hardening.test_attempt_ids_with_dots_slashes_and_hostile_characters_get_valid_branch_names` |
| R5 detached shim | `test_shim.test_a_clean_run_writes_both_records_and_the_output`; `test_shim.test_the_shim_persists_an_agent_terminal_descendant_after_the_agent_exits`; `test_audit_round2.test_the_real_executor_sweeps_an_agent_terminal_child_after_the_agent_exits`; `test_shim.test_a_timeout_stops_the_agent_and_its_grandchildren`; `test_shim.test_output_beyond_the_head_cap_is_dropped_with_a_count_and_the_tail_is_kept`; `test_hardening.test_stragglers_that_escaped_the_process_group_are_stopped_before_the_handoff` |
| R6 bounded limits | `test_start.test_the_queue_is_bounded_and_the_refusal_is_a_stable_record`; `test_concurrency.test_a_burst_of_thirty_orders_respects_the_ceiling_and_every_one_finishes_once`; `test_hardening.test_the_log_never_grows_without_bound`; `test_hardening.test_non_finite_timeouts_and_limits_are_refused` |
| R7 handoff then one terminal event | `test_executor.test_every_attempt_ends_in_exactly_one_terminal_event`; `test_events.test_the_terminal_event_is_persisted_in_the_same_transaction_as_the_terminal_state`; `test_executor.test_a_failing_sink_never_blocks_the_attempt_and_events_are_redelivered_in_order`; `test_hardening.test_one_poisoned_attempt_does_not_block_the_events_of_the_others` |
| R8 classification | `test_classification.test_quota_exhaustion_carries_the_reset_epoch_the_provider_gave`; `test_classification.test_connection_words_in_the_output_of_a_successful_run_are_not_a_failure`; `test_scheduler_executor_adapter.test_classification_uses_the_real_normalisers`; `test_hardening.test_connection_words_with_a_zero_exit_are_never_a_connection_failure` |
| R9 safe cancel | `test_cancel.test_a_cancel_that_arrives_while_the_attempt_is_still_preparing_stops_it_before_any_process`; `test_cancel.test_cancelling_twice_is_one_cancellation_and_one_terminal_event`; `test_cancel.test_cancel_after_the_attempt_ended_changes_nothing` |
| R10 reconcile on construction | `test_reconcile.test_query_reflects_process_reality_not_just_the_ledger`; `test_reconcile.test_an_attempt_stuck_in_settling_is_settled_once_with_the_stored_outcome`; `test_reconcile.test_an_attempt_stuck_in_preparing_with_no_process_is_prepared_again_once` |
| R11 environment and secrets | `test_executor.test_the_child_gets_the_profile_environment_and_loses_the_other_profiles_secrets`; `test_executor.test_no_secret_reaches_the_ledger_the_artifacts_or_the_events`; `test_scheduler_executor_integration.test_no_secret_value_appears_in_the_executors_state_or_in_the_cores_audit`; `test_hardening.test_artifacts_are_private` |
| R12 prompt and claims | `test_executor.test_the_prompt_is_task_text_and_rules_and_is_private`; `test_prompt.test_patch_mode_executor_prompt_forbids_commits`; `test_events.test_the_agents_report_is_labelled_a_claim_in_the_event`; `test_hardening.test_the_agents_report_cannot_hang_or_exhaust_the_executor` |
| R13 artefacts | `test_executor.test_artifacts_live_under_attempts_and_nothing_is_written_to_the_main_checkout`; `test_hardening.test_a_cancelled_attempt_has_a_manifest_and_a_brief_even_with_no_workspace`; `test_hardening.test_a_queue_full_refusal_leaves_no_empty_directory` |
| R14 real CLIs opt-in | `test_scheduler_executor_real.test_every_real_case_resolves_without_launching_anything` |
| R15 no regressions, opt-in | `test_scheduler_executor_integration.test_a_legacy_requirement_is_not_taken_over_and_its_run_json_is_untouched`; `test_scheduler_executor_integration.test_historical_runs_of_this_repository_are_byte_identical_after_a_whole_executor_session` |
| R16 documentation | `test_readme.test_every_public_name_is_documented`; `test_readme.test_every_error_code_is_listed`; `test_readme.test_the_acceptance_table_cites_tests_that_exist` |
| F4-5 workspace kinds | `test_workspace.test_subplan_workspace_reconstructs_from_a_frozen_line_commit`; `test_workspace.test_integration_workspace_uses_candidate_and_cleanup_is_idempotent` |

## Known limits (demonstrated or declared, not hidden)

- POSIX only. Process identity needs `/proc` (Linux) or `ps` (fallback); not tested on macOS or Windows.
- Descendant recording is a best-effort Linux `/proc` sample every 0.1 seconds, capped at 16,384 process entries per scan
  and 4,096 unique PID identities per attempt. The record marks itself `truncated` if either cap is reached. A process that
  daemonises and is re-parented between samples may be missed.
- Quota detection is only as good as the provider's own output and `bt_driver`'s normaliser; a limit message without a reset
  time yields `reset_epoch: null`. Connection-loss detection is a pattern list on failing exits, not a network probe.
- Codex has no end-of-turn marker: its "clean" means exit 0 with output (M1 still requires an independent verdict).
- The handoff snapshot uses `git add -A` semantics (respects `.gitignore`): a huge untracked, un-ignored tree is captured whole.
- `close()` leaves agents running by design; a stuck agent is stopped only by `cancel`, its own timeout, or an executor on the same root.
- A shim killed with SIGKILL while its agent runs is detected on the next watch; until then the agent is an orphan. A shim killed in the
  few microseconds between spawning the agent and writing `shim.json` leaves an agent nobody has a record of (not recoverable by identity).
- Stragglers: after an attempt ends the executor kills every process whose working directory is inside the worktree (this catches
  `setsid` escapes), but a descendant that `chdir`s away and escapes the process group is out of reach (no subreaper: the module may not use `ctypes`).
- Trust boundary: the agent runs as the same user and without a sandbox (the providers are launched in their permission-bypass modes, as the
  methodology launcher does); it can read or forge files in the attempt directory (`exit.json`, `descendants.json`) and edit the repository's git configuration. Files
  are 0600 and directories 0700 (root 0700, `ledger.db` 0600, `executor.log` 0600) against other users only. `exit.json`, `shim.json`
  and `descendants.json` are shape-checked on read: a forged or malformed `exit.json` is treated as a vanished supervisor (cause `lost`),
  and invalid descendant evidence identifies no terminal process as agent-owned. A well-formed same-uid forgery remains inside the declared trust boundary.
- If the handoff cannot be captured (after `handoff_tries`), the attempt ends **failed** with cause `artifact_error` even if the agent exited cleanly
  ("never a silent success"); the worktree still holds the files and the failure is stated in the event.
- The sink is called from the supervisor thread: a slow `EventSink` delays watching and scheduling (use a fast, non-blocking sink; the adapter's calls the core's `ingest`). A failing
  event holds back only its own attempt's later events.
- `bind_run`: the first accepted order binds an executor root to its plan/revision; use one root per scheduler run.
- Events enter the core through the adapter's sink because M4 does not exist yet; the sink is a port so M4 can sit in between.
- `route:<id>` resolves through M2's persisted selected route. The adapter checks its plan/revision/task binding, rejects a
  decision superseded for that task, and rejects missing or expired quota evidence at resolution and immediately before
  provider launch, including routes that waited in the queue. Operator-written `direct:<provider>/<model>[@profile][#effort]` references are refused when
  an M2 lookup is configured unless `allow_direct=True`; M3 never chooses a default model.
- The module never integrates prerequisite work: `after` only orders tasks in time and a task starts from `base_ref` (default `HEAD` of its
  repository). The methodology's `wire(..., integrate_predecessors=True)` (`bt_scheduler_integrator`, on by default; `integrate_predecessors=False` turns it off) supplies a `base_ref` that
  merges the accepted same-repository predecessors' handoff snapshots (`git merge-tree`, objects only, kept under `refs/m3/integration/`);
  a conflict or a missing snapshot rejects the order with `INTEGRATION_CONFLICT` / `PREDECESSOR_HANDOFF_MISSING` instead of guessing.
  With the option off a dependent task does not see its predecessors' work.
- Verifier independence compares opaque executor labels (`provider/model@profile`); two labels for the same underlying account are not detected.
- `Route.account_ref` and `Route.single_use` are part of the route record: the adapter re-checks `account_ref` against M2 at resolve time and again
  at launch (TOCTOU), and refuses `direct:` references when an M2 lookup is configured unless `allow_direct=True`.
- Branches and handoff refs live in the shared repository, so they are scoped by the executor root (`m3/<attempt>-<root hash>`,
  `refs/m3/handoff/<attempt>-<root hash>`): a second run of the same plan, with its own root, never collides with or overwrites the first run's.
- The cwd sweep (`spare_interactive=True`, the default) preserves an operator's terminal and stops an agent-owned terminal process
  only when it is still a live descendant or its PID/start identity matches `descendants.json`. It rechecks the identity and cwd
  after opening a Linux pidfd, then signals through that descriptor so PID reuse cannot redirect the signal. If pidfds are unavailable,
  terminal processes are preserved. A recycled PID never matches.
  Sampling is best effort: a daemon re-parented between samples, or one that changes its cwd away from the worktree, may remain
  out of reach. `spare_interactive=False` sweeps every process in the exclusive worktree.
- The cwd sweep runs only when the worktree path is exclusive to the attempt; a workspace manager that returns a path another live attempt uses
  is refused at start (`WORKSPACE_ERROR`) instead of risking a neighbour's agent.
- A PREPARING attempt that no job drives (a start job died, a transient settle failure) is reconciled again after `settle_retry_seconds`
  instead of holding a slot forever; adoption of a live shim/agent is by recorded identity, and an unrecorded shim is found only by its exact
  command line `<python> <shim> <attempt dir>`.
