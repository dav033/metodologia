# Working notes — staged execution (D-134)

Brief: `staged-execution.md` (same folder). Session 349f442d (claude-work, Opus 5.5).
OWNER RULE (mid-session): do NOT use the methodology flow for this work (no REQ/plan/planning/round/delegate/launch/
scheduler-run on metodologia). Change skill code directly; bitácora only for D-134, these notes, PENDING, day log.
Note: ~/bitacora is a symlink into ~/dev/metodologia/bitacora. Never touch ~/bitacora/pictures (read-only peek done).

## Status
- [x] 1 Read
- [x] 2 Design D-134 (written at end of DECISIONS.md)
- [x] 3 Implement
- [x] 4 Tests (baseline failures documented)
- [x] 5 Antagonist review (two independent passes; nine findings corrected)
- [x] 6 Report + day log + PENDING

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

## Relay continuation — Codex
- Verified git status on main; preserved shared local changes. No commits, service restarts, real runs or Pictures writes.
- Fresh scheduler integration: 29 tests OK. Reproduced obsolete watchdog expectations (2 failures) and launch authority
  expectations (2 failures). Replaced removed watchdog healing-rebase assertions with refusal/no-outside-rebase coverage;
  launch dry-run now checks join preview and AUTHORITY_CONFLICT for historical authority.
- PLAN block prose test originally appended free prose (no longer protected); changing text after a parsed `verify`
  field was also ignored by the parser. Corrected fixture to edit the approved task TITLE, the actual protected scope.
- Combined named modules abort with run_case_support root-order protection; isolated modules / discovery are used.
- Full methodology, Planner, M1 core and M3 executor suites running; logs /tmp/staged-*-tests.log.
- Updated contract/runtime/planning documentation and corrected D-134 to the owner's no-compatibility decision.
- Independent read-only antagonist review started; fixes and final verification pending.

### Independent antagonist review — six verified findings, all corrected
- A1: concurrent edits could enter after eligibility. Approval now carries one captured PLAN.json object through
  validation/freeze, with a document guard (PLAN.md/SPEC/flow/design content) immediately before publication;
  mutation regression returns STAGE_APPROVAL_CHANGED without a revision.
- A2: full approval restricted SPEC ids like a partial stage. Complete stages now validate ALL SPEC requirements;
  R5-without-coverage regression reproduced red and passes after correction.
- A3: merge checked historical complete/subplan ids only. It now checks current binding; adding T99 or removing the
  draft cannot bypass final closure. Drift regression reproduced red and passes after correction.
- A4/A5: joining a newer target lost pause ownership; crash after M1 rebase left stale runtime binding. Durable marker
  now preserves ownership and reconciles even when DB already reached target. Both regressions reproduced red,
  then passed. Marker is written before pausing or rebasing so interruption cannot orphan the pause.
- A6: identical JSON skipped repinning SPEC. Approval idempotence now includes pins and remaining-scope metadata;
  reapproval produces a new revision and binds correctly. Regression reproduced red, then green.
- Split responsibilities: bt_plan_consumers.py owns capability/auditor policy; bt_scheduler_stage_join.py owns
  durable quiet-point join. Facades stay below 500 lines; pyproject includes both modules. Planner importer boundary
  remains unchanged. No outstanding antagonist finding.
- Fresh checks: Planner 375 OK; core 333 OK; executor 324 OK; staged owner E2E 1 OK (8.9s); stage rules 18 OK;
  watchdog 23, launch boundaries 5, PLAN block 17, collaborative flow 16, subplan sessions 9 OK.
- New-module scoped Ruff, Python compilation and git diff --check pass. Installed-wheel suite builds/installs but
  has 2 proven pre-existing assertion failures (21 tests): recorded as P-206. No configured type checker was found.
- General-suite runs still in progress; final counts will be appended here and in today's Delegation section.

### Final independent pass and latest evidence
- Second bounded antagonist pass found three additional proven cases: closed Markdown Requirements headings bypassed
  pins; complete reapproval skipped a newly added SPEC requirement; crash after journal write but before pause did not
  restore dispatch pause. All three reproduced red and corrected. Shared traceability parser now owns SPEC grammar;
  complete approvals pin every current SPEC item and always revalidate, even when idempotent; journal reconciliation
  restores the pause when the marker already exists. No independent finding left unresolved.
- Coordinator regressions also prevent auto-join after approved-scope drift and closing against an older/uncompleted
  run revision. Final closure checks current draft binding, latest approved run identity and completed task states.
- Latest Planner suite: 377 tests OK (33.525s). Latest stage rules: 21 OK. Latest actual Scheduler owner E2E: 1 OK
  (8.481s), with fake agents and isolated repositories. Shared SPEC parser remains covered by the complete Planner suite.
- First general sweep: 2548 tests / 802.833s, 6 failures, 6 existing skips: 4 baseline schema-compat subtests reading
  real drafts (P-195), plus two obsolete PLAN-block/session assertions corrected afterwards and green in isolation.
- General second sweep was started before the final audit corrections; latest targeted suites above cover those
  corrections. Its aggregate count will be recorded separately; do not mistake an older imported test snapshot for
  current source.

### Final aggregate result
- Second general sweep: `cd skill/scripts/tests && PYTHONPATH=..:. python3 -m unittest discover -s . -p 'test_*.py'`:
  2551 tests in804.735s, FAILED (5 failures,6 existing skips). Four failures are existing non-hermetic
  `test_plan_schema_13_compat` subtests (P-195); the fifth used the pre-edit imported hands-on-session assertion.
  Current `test_subplan_sessions` has9 passing tests; `test_planblock` has17 passing tests. Final audit fixes are
  covered by current Planner377 / stage21 / E2E1 green reruns. This is not an all-green aggregate claim.
- General logs: /tmp/staged-full-tests.log, /tmp/staged-full-final.log. Latest module logs:
  /tmp/staged-planner-latest.log, /tmp/staged-stages-final.log, /tmp/staged-e2e-complete.log,
  /tmp/staged-sessions-latest.log. All evidence in this note is summarized from actual command output.
- Git status rechecked; shared Pictures edits belong to the other session and were preserved. No commits/pushes,
  deployments, real Scheduler launches or service restarts. No owner decision remains open. Live UI/real-agent
  validation remains unexecuted under the brief's constraints. Package baseline repair is P-206; schema fixture debt
  is P-195. The implementation is ready for owner review in the working tree.
