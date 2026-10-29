# Independent review of req030-iter2-merge6 at 3cdace8f4 (2026-10-28 21:25, session metodologia-6d)

Scope (requested by session metodologia-b1, which ended before it could be delivered): `git diff 986515000 3cdace8f4 --
skill/scripts/bt_durable/execution skill/scripts/bt_durable/adapters/{integration,composition}.py skill/scripts/bt_supervisor`,
plus the pure control functions replay re-executes (`control/classify.py`, `control/frontier.py`). Questions: replay
safety for the live REQ-021 histories, CAS/atomicity of the multi-line integration, any agent launch while paused.
Read-only: DBOS queried with DBOSClient (list_workflows, list_workflow_steps, get_event); REQ-021's frozen plan run
offline through the 3cdace8f4 pure functions. Scripts: scratchpad `live_history.py`, `req021_offline.py`, `req021_audits.py`.

## Findings

1. HIGH — a step failure in the `bt.run` body kills the run. `steps._port` re-raises every port error as StepFailure;
   `bt.run` calls `steps.sync_lines` (workflows.py:116), `steps.compose` (:125) and `steps.audit_gate` (:159) directly,
   without handling. Once the step's retries are exhausted DBOS raises into the body and the run workflow ends in ERROR,
   which DBOS never recovers (task workflows send `task_done` to a dead workflow). Triggers: LineMoved three times
   (integration.py:170, sync contends with bt.integrate on the same subplan lines), a merge-tree hard error (:118),
   compose's `line_base` LINE_BASE_UNKNOWN (composition.py:65, not caught there unlike `sync`), StopIteration (:61),
   composition-engine exceptions, an audit judge git error or REPOSITORY_UNKNOWN. Task workflows are immune: `_enqueue`
   turns errors into `internal_error`.
2. MEDIUM — the multi-line integration is not atomic on a CAS failure (integration.py:141-143): the run line moves
   first, then each subplan line with its own `update-ref`. A later CAS failure leaves the run line moved; the retry
   converges, but if the retries are exhausted the attempt ends `internal_error` while its snapshot is on the run line
   and not on its subplan lines. The docstring's "a conflict in any line leaves every line as it was" holds only for
   merge conflicts.
3. MEDIUM (resume procedure) — `T3.2:d1` / `T2.6:d1` were recorded by the previous engine; a replay does not re-run a
   recorded `DBOS.set_event`, so their `decision` events keep the old options (no `reverify`, no `verify_attempt`).
   `bt-durable attest --request T3.2:d1` refuses (cli.py:226) and the panel does not offer reverify. `bt-durable answer
   … T3.2:d1 reverify` works (no options check; PATCH_OWNER_REVERIFY sits at a new point; covered by
   test_durable_upgrade from 366cbf372); the existing receipt bound to att-0059 binds through the legacy manifest's
   `attempt_id` (adapters/m6.py:97).
4. LOW — a task waiting on a pause records 4 operations per `run_poll_seconds` (workflows.py:377-380); `bt.run`
   records 3 per poll (212 operations at review time). Long pauses lengthen replays.
5. INFO — the subplan lines of a migrated run hold a superset of their scope: seeding merges each legacy snapshot with
   its whole history (integration.py:10 says "exactly").

## Verified

- The live `bt.run` history starts with `bt.plan_text` (op 1): `workflow_plan()` replays it. REQ-021's two `bt.agent`
  workflows are ERROR (never recovered), so the new agent body is never replayed.
- `T2.6:k1` / `T3.2:k1` (18 operations, `recv` live at op 18) replay on the new code: the new classifier does turn
  T3.2's reconcile verdict into MANUAL_EVIDENCE_REQUIRED (owner first), but PATCH_RECONCILE_ASKS_OWNER meets the
  recorded `setEvent` and returns False; PATCH_TASK_PAUSE meets the recorded `bt.now`; `policy.py` is unchanged.
- `bt.run`: PATCH_RUN_SUBPLANS returns False through every recorded iteration and turns on at the first live one.
  Offline on REQ-021's plan: `_line_items` does not raise (role pictures: SP-1, SP-2, SP-14, SP-3); the frontier is
  `ready=(T3.11,)` with and without gates; nothing to compose yet; T2.6 home SP-2, T3.2 home SP-3.
- REQ-021's audits (T2.7, T2.8, T3.15, T14.5, T14.6) all declare their `*.findings.json`; live policy:
  ledger_required, read_only, remediate, 2 rounds.
- Nothing launches an agent while paused: `bt.run` starts tasks only when not paused; task workflows created while
  paused (retry_task, audit repair rounds) wait at the pause check. Only M6 verification runs (reconcile, reverify).
- Supervisor: `supervisor_id` = sha256 of the store root, stable across engine restarts (adoption keeps working);
  processes without the field still count.
