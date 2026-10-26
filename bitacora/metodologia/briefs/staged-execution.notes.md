# Working notes — staged execution (D-134)

Brief: `staged-execution.md` (same folder). Session 349f442d (claude-work, Opus 5.5).
OWNER RULE (mid-session): do NOT use the methodology flow for this work (no REQ/plan/planning/round/delegate/launch/
scheduler-run on metodologia). Change skill code directly; bitácora only for D-134, these notes, PENDING, day log.
Note: ~/bitacora is a symlink into ~/dev/metodologia/bitacora. Never touch ~/bitacora/pictures (read-only peek done).

## Status
- [x] 1 Read
- [x] 2 Design D-134 (written at end of DECISIONS.md)
- [ ] 3 Implement
- [ ] 4 Tests
- [ ] 5 Antagonist review
- [ ] 6 Report + day log + PENDING

## Findings (file:line refs, skill/scripts/)
- Freeze: `bt_planner/revisions.py::freeze` validates strict_publication, writes PLAN.r<N>.json + MANIFEST entry
  {revision, sha256, frozen_at, source, plan_md_sha256?}. Manifest entries carry extra keys freely.
- Publication gate: `bt_planner/sync.py::check` (validate + consistency PLAN.md<->JSON + revision store) and
  `approve_freeze` (needs PLAN.md status approved). `bind_approved` = launch gate: PLAN_DRIFT if working PLAN.json !=
  latest frozen; PLAN_PROSE_DRIFT via narrative_digest.
- Traceability (`traceability.check`) errors when SPEC requirement ids missing from plan.requirements, or a declared
  requirement has no task. Schema13 (`schema_13.check`) SUBPLAN_EMPTY etc for every declared subplan.
- Adapter `bt_plan_adapter.py` is the only bt_planner importer: launch_problem/resume_problem/publishable_problem/
  freeze_approved/freeze_revision (scheduler-made revisions write the frozen plan back as working PLAN.json!).
- `scheduler-run` (bt_scheduler_run.run) does NOT run launch_problem; it loads latest frozen revision
  (`bt_scheduler_adapter.approved_plan`), requires runtime binding == latest frozen (PLAN_MISMATCH otherwise),
  calls `bt_requirements_gate.require_ready` (fingerprints PLAN.md+SPEC.md: staged editing would trip it).
- `bt_launch.launch` requires PLAN.md status approved, freeze_on_launch (bind_approved), sets status launched.
- Core run status derives from tasks (views.run_status): adding tasks via rebase reopens a COMPLETED run.
  `rebase_run` refuses live attempts / cancel_requested; content cascade keeps unchanged accepted tasks.
- `bt_scheduler_cli_run --rebase` = rebase_to_latest + rebind_runtime + resume.
- Watchdog `bt_scheduler_watch._apply_frozen` applies only healing-source revisions after PLAN_MISMATCH; reads
  PLAN.json revision (draft!) — must not rely on it for staged plans.
- Remediation/healing/recovery revisions: built from latest frozen, `freeze_revision` overwrites PLAN.json.
- D-131 `bt_verification.state/gate` iterates the WORKING PLAN.json subplans: unbuilt draft subplans are "waiting"
  → merge gate already blocks closing while remainder not built. Fail-closed via ledger `gated`.
- Planning flow `bt_planning_flow`: subplan confirmed iff flow.json digest == _digest(current); confirm requires tasks,
  criteria, `## Pruebas` row, inputs resolved, design ready. approval_problems also checks plan-wide inputs.
- Designs: `bt_design_drafts.pin_for_plan` pins ALL ready drafts at plan approval (needs refs filter for a stage).
- Web: `bt_page_planning_flow._run_button` posts `session-start` mode=auto (D-132); server `session_post`.
- REQ-021 draft (read-only peek): schema 1.3.0, 13 subplans, only SP-1 has tasks (T1.1–T1.8, audit T1.8), no gates,
  no REQUIREMENTS.json, PLAN.md status draft, flow.json SP-1 confirmed.

## Decisions (draft, to formalize in D-134)
- Stage = a frozen revision that is the PROJECTION of the draft onto a cumulative subplan set S (tasks of S, non-subplan
  tasks whose subplan ancestors are all in S, milestones used, requirements covered, gates within S) + top-level
  `stage` object. Validated by the unchanged full validator (with SPEC ids restricted to the stage's requirements).
- Drift for staged plans = projection(draft, S_frozen) != frozen (ignoring revision field) → STAGE_DRIFT at
  launch/join/freeze points; remainder edits never block. Running stage keeps executing its frozen revision.

## Done

## Left

## OWNER DECISION 2 (mid-session): backward compat NOT required
Drop opt-in/exact-bytes/legacy constraints. Staged execution is THE way plans run. Simplify legacy-only paths I touch.
Design change (D-134 to be rewritten accordingly):
- Every approval is a stage freeze; whole-plan approval = stage holding every subplan (require_complete).
  A revision without `stage` reads as the complete stage of its own plan (no special path).
- One drift gate for all plans: projection(draft, S_frozen) == frozen (PLAN_DRIFT), PLAN.md lines of approved tasks
  (PLAN_PROSE_DRIFT, replaces whole-narrative digest), SPEC items of approved requirements (PLAN_REQUIREMENTS_DRIFT).
- Draft `revision` field no longer compared with frozen revisions; freeze assigns latest+1.
- Run binds to its own revision on resume; any newer frozen revision joins at a quiet point (pause dispatch, wait
  no live attempts, rebase, resume) unless it would redo more accepted tasks than gates.rework_confirm_over.
- Scheduler-made revisions splice into the draft (never overwrite PLAN.json).
- Requirements gate: PLAN.md/SPEC.md fingerprints waived for scheduler-run (approved scope protected by bind pins).

## Progress log
- Planner: `bt_planner/stages.py` (project/bind/freeze/splice/summary), `sync.check_stage/freeze_stage`, approve_freeze
  = complete stage, bind_approved = stages.bind; check() no longer compares draft revision; `revisions.freeze(extra=)`;
  contract validates `stage`; schema doc + README updated; tests updated (test_sync/test_evidence/test_scenarios/
  test_e2e_cli) + new `bt_planner/tests/test_stages.py` (12). Planner suite: 373 OK.
- Adapter: launch_problem(forced) via bind; resume_problem = plan_ref names an approved revision; stage_problem/
  freeze_stage/stage_summary/stage_subplans/draft_subplans; freeze_revision splices into draft.
- Scheduler adapter: run_identity/run_plan/join_target/join_cost; open_scheduler + executor wiring use run_plan.
- scheduler_run: _join_ready (pause, marker `<db>.join.json`), join(), dispatch loop, notify stage note,
  require_ready(waive=PLANNING_FILES). Watchdog `_apply_frozen` removed (superseded by joins).
- requirements gate: waive param.
NEXT: bt_stages.py (eligibility + run), pin_for_plan(refs), bt_launch join, review merge gate, CLI `stage`, web
button/action, sessions auto refused, projection stage info, docs, pyproject, tests (unit + E2E), full suite.

## Checkpoint before quota relay (2026-10-26 ~16:30)
Done since last log: bt_stages.py, bt_cli_stage.py (`bitacora.py stage run|freeze|status REQ SP-n[,SP-m]`), web action
`stage-run` (bt_server.stage_post, loopback) + Plan-tab button (bt_page_planning_flow._run_button → stage-run, only for
confirmed subplans; «En ejecución · etapa rN» chip once held), sessions auto mode retired (SESSION_AUTO_SUPERSEDED,
prompt_auto deleted, Sesión tab only hands-on), pin_for_plan(refs), bt_launch joins an existing run on final approval,
bt_review.stage_gap (STAGE_INCOMPLETE, fail closed), projection `stage` + run page KPI + Ahora card label,
adapter: second_auditor_lines applied to the stage projection, resume_problem verifies frozen bytes,
freeze_revision without draft writes plan. pyproject: bt_stages, bt_cli_stage.
Tests: new tests/test_stages.py (15, OK), tests/test_stage_execution_e2e.py (OK, ~8 s), bt_planner/tests/test_stages.py.
Updated old tests to new semantics: test_plan_launch_paths, test_plan_contract_compat, test_plan_integration,
test_plan_adapter_evidence, test_scheduler_integration (hijack test just edited, rerun it), test_planning_flow,
test_subplan_sessions, planner tests.
STILL FAILING / TODO (from full suite run 1, before fixes): test_scheduler_watch (2 tests of removed _apply_frozen:
delete them), test_scheduler_launch_boundaries (existing scheduler authority now joins: update), test_planblock
(prose drift test: change to task-line edit). test_plan_schema_13_compat = baseline (scans real bitácora drafts).
Then: rerun full suite (each module alone if run_case_support complains), docs (plan-contract.md, modules.md,
requirements.md §8, execution.md §1c, agents/planner.md), rewrite D-134 for compat dropped, antagonist review,
day log `### Delegation`, PENDING items, final report.
