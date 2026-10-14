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
4. Fill the classification in `PLAN.json` (rubric: `bt_planner/README.md`). **Argue every dimension**: schema 1.1.0 needs
   `classification_evidence` per task (justification of at least 4 words + typed references `file:`, `command:`,
   `precedent:`, `spec:`, `task:`, `assumption:`). Cite files you actually opened; `confidence: high` cannot stand on
   assumptions; an unknown stays `confidence: low` with a research task before the work that depends on it.
5. `bitacora.py plan-json check REQ-NNN` (exit 2 on any error) is the publication gate: schema, evidence (`file:`
   references are verified against the project's registered repositories; unverifiable ones are an error at approval and
   launch), PLAN.md ↔ PLAN.json agreement and
   unordered tasks that collide. Fix and rerun; do not present an invalid plan for approval. `plan-json report REQ-NNN`
   prints critical path, widest level, distributions and gaps: read it before asking for approval.
6. Approval freezes: `plan approve` (terminal), the web button and `handoff` validate PLAN.json and freeze exactly that
   revision (an invalid plan cannot be approved). **A launch never freezes**: a plan approved by editing `status:` by
   hand is refused with `PLAN_NOT_FROZEN` until `plan-json freeze REQ-NNN` records the approval (only an explicit
   `launch --force` is taken as the owner's approval). Later scope changes mean `revision: N+1` and a new approval.
7. Close the planning session; a later session reads `PLAN.json` / `plan-revisions/` only. Nothing here launches agents.

`plan-json show REQ-NNN` lists revisions; `plan-json compat REQ-NNN` is read-only and reports what a legacy plan lacks
(and any ambiguity in its PLAN.md). Schema 1.0.0 plans already frozen keep working; new revisions are published as 1.1.0.

### What `check` compares between PLAN.md and PLAN.json

Ids defined once on both sides, milestone membership and titles, task titles, `repo:` against `repository`, `after:`
(as a set), a stated `verify:` against a command verification, a legacy `risk: low|medium|high`. A value PLAN.md does not
state is not a contradiction; one it states differently is an error. Fields the parser would silently drop (a repeated
field, an `after` entry that is not a task id, an unbackticked `verify`) are reported with their line.

## Where the methodology touches the module

Only `bt_plan_adapter.py` imports `bt_planner` (enforced by `tests/test_plan_integration.py`):

- `bt_cli_plan.py` → `adapter.run_cli` : the `plan-json` command (requirement folder → plan directory, approved words,
  repository roots of the project so `file:` evidence is verified).
- `bt_handoff.assess` → `adapter.handoff_problems` : an invalid `PLAN.json` is a problem, so `handoff` refuses it.
- `bt_rounds.plan_decide` (approve) → `adapter.publishable_problem` before, `adapter.freeze_approved` after: an invalid
  PLAN.json cannot be approved and the approved bytes are frozen as that revision.
- **The launch gate** `adapter.launch_problem` / `freeze_on_launch` (planner `bind_approved`): valid, consistent with
  PLAN.md and exactly the latest frozen revision. Every path that starts work goes through it:
  `bt_launch.launch` (standard, web approve-and-launch, handoff; a dry run verifies without writing; `--force`
  still validates), `bt_orchestration_transition.launch` and its successor helper (foreground), and
  `bt_run._open` for any NEW run. A resumed run is never rewritten, but it refuses to go on when PLAN.json is no longer
  the latest approved revision (`resume_problem`). The gate fails closed: an unexpected error is `PLAN_CHECK_FAILED`.
- `bt_runstate.init_state` → `adapter.run_state_fields` : `plan_ref` for new runs only; existing `RUN.json` are never touched.

Outcomes: `PLAN_NOT_APPROVED`, `PLAN_INVALID`, `PLAN_MISSING` (PLAN.json removed after a freeze), `PLAN_NOT_FROZEN` and `PLAN_DRIFT` (an
edit or an unapproved new revision: approve it with `plan approve` or `plan-json freeze`; a launch never freezes an
unreviewed edit). A plan approved by hand and never frozen has no approval record and is refused (`PLAN_NOT_FROZEN`). A test
(`LaunchPaths`) fails if a new module creates run state around the gate.

## Verify

`cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` (the module alone, isolated copy included) and the
methodology suite `python3 -m unittest discover -s tests` from `skill/scripts`.
