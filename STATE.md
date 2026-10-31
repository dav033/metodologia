# bounded-repair: state at emergency shutdown (2026-10-31)

Branch `bounded-repair` (from main 4a32ce2e7). Decision number reserved: **D-241** (not yet written into DECISIONS.md).

## Done (commit ef788b8c7)
- `skill/scripts/bt_planner/repairs.py`: a pure classifier, `classify(frozen, draft)`, exported from `bt_planner`.
- `bt_planning_flow.py`: `confirmed_as`, `policy_confirm` (record `by: policy`, `policy: {rule, requested_by, repair,
  evidence, previous}`), and `by`/`policy` added to the per-subplan state.
- `bt_stages.py`: `repair_reconfirm` and `_repair_evidence`; `freeze`/`run` take `repair_evidence=`, `by=`. New codes
  are STAGE_REPAIR_UNBOUNDED and STAGE_REPAIR_EVIDENCE. Calling it again after the stage is frozen does nothing, so
  the Planner can freeze and the Solucionador can then join.
- `bt_cli_stage.py`: `stage run|freeze REQ [SP] --repair-evidence f1,f2 --by planner|solver`.
- `bt_subplan_status.py`: the Plan tab shows «Sigue confirmado por tu regla D-241…».
- Docs: `agents/solver.md`, `agents/planner.md`, `references/requirements.md`.
- `tests/test_bounded_repair.py`: 13 tests, all green. Together with test_stages, test_planning_flow,
  test_stage_queue and test_subplan_control: 74 tests OK.
- The classifier was checked read-only against live pictures r28→r29: it returns bounded, adds T10.441, detector
  T10.45, touches SP-10. `confirmed_as` also matches the live digests.
- Generated agent copies were rendered into a scratch HOME and contain D-241. They were not installed live.

## Left
1. Run the full regression. The selection covers 287/311 suites and is NOT trusted. Make sure no integration holds
   `~/bitacora/.state/integrate.lock`, then run the following with SIGTTIN/SIGTTOU/SIGTSTP at their defaults:
   `python3 skill/scripts/bt_regress.py <wt> <scratch> <results>`. It never ran: it was waiting on the lock, which
   post-own-venv integrations held.
2. Paste the D-241 entry into `~/bitacora/metodologia/DECISIONS.md`. The text is in the agent's report.
3. Integration and installing the agent prompts are the coordinator's job.

## Resume
`cd <this worktree>`, then run `skill/scripts/../../.venv/bin/python -m unittest tests.test_bounded_repair` from
`skill/scripts`, then step 1.
