# Planner module: classified plans and `PLAN.json`

Read this when you write, validate, freeze or consume a plan that will run through the supervisor/scheduler. The logic
lives in the **module `skill/scripts/bt_planner/`** (see its `README.md` for the contract, the classification rubric with
boundary examples, the PLAN.md grammar, revisions and the stable error codes). This page only says how the methodology
uses it. Design source: `PLAN-SUPERIA-FASE-1-PLANES.md` (REQ-009); isolation: REQ-010; convention: `modules.md`.

The planner **describes and classifies** work. It never chooses the model, account or worker count, never supervises,
never writes `RUN.json`: it inspects, writes, validates, hands over and ends.

## Files

| File | Owner | Role |
|---|---|---|
| `SPEC.md`, `PLAN.md` | planner | what/why and the human narrative (task-line grammar unchanged) |
| `PLAN.json` | planner | the classified, validated contract the scheduler reads |
| `plan-revisions/PLAN.r<N>.json` + `MANIFEST.json` | planner at approval | immutable approved revisions with sha256 |
| `HANDOFF.md` | launch | context for a fresh executor session |
| `RUN.json` | supervisor/scheduler | execution state; a NEW run copies only `plan_ref {plan_id, revision, sha256}` (or `plan_ref_error`) |

Checkboxes in `PLAN.md` are presentation; once `RUN.json` exists it alone is authority on state. Old plans without
`PLAN.json` keep working in the old flow: the contract is opt-in per requirement.

## Planner flow

1. Inspect the real project; never copy paths, commands or tests from another plan without checking they exist.
2. Write `SPEC.md` and `PLAN.md` as usual (milestones `### M1 — …`, task lines with `after:` and backticked `verify:`).
3. `bitacora.py plan-json init REQ-NNN` derives the skeleton; every classification field stays **absent** and is reported.
4. Fill the classification in `PLAN.json` (rubric: `bt_planner/README.md`).
5. `bitacora.py plan-json check REQ-NNN` (exit 2 on any error) is the publication gate. Fix and rerun; do not present an
   invalid plan for approval.
6. After approval run `plan-json freeze REQ-NNN` (or let `launch` do it). Later scope changes mean `revision: N+1`.
7. Close the planning session; a later session reads `PLAN.json` / `plan-revisions/` only. Nothing here launches agents.

`plan-json show REQ-NNN` lists revisions; `plan-json compat REQ-NNN` is read-only and reports what a legacy plan lacks.

## Where the methodology touches the module

Only `bt_plan_adapter.py` imports `bt_planner` (enforced by `tests/test_plan_integration.py`):

- `bt_cli_plan.py` → `adapter.run_cli` : the `plan-json` command (requirement folder → plan directory, approved words).
- `bt_handoff.assess` → `adapter.handoff_problems` : an invalid `PLAN.json` is a problem, so `handoff` refuses it.
- `bt_launch.launch` → `adapter.freeze_on_launch` : freezes the approved revision (not on `--dry-run`); an invalid one stops the launch.
- `bt_runstate.init_state` → `adapter.run_state_fields` : `plan_ref` for new runs only; existing `RUN.json` are never touched.

The foreground launch path (`bt_orchestration_transition`) does not freeze yet (PENDING P-019).

## Verify

`cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` (the module alone, isolated copy included) and the
methodology suite `python3 -m unittest discover -s tests` from `skill/scripts`.
