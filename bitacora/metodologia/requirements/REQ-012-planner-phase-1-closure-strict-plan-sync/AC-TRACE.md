# REQ-012 — Acceptance traceability

Each criterion of PLAN-PLANNER-001 §9 (AC-01…AC-15) and of the owner's `/goal` of 2026-10-14 (G1–G5), with the
automated test or inspection that verifies it. Test paths are relative to `skill/scripts`; `M:` = module suite
(`bt_planner/tests`), `X:` = methodology suite (`tests`). `bitacora.py`-level behaviour was also exercised by the six
real planning trials (`planning-trials/RESULTS.json`, 182 checks).

| ID | Criterion | Verified by |
|---|---|---|
| G1 | Duplicate ids and contradictions in title / repo / dependencies / verification rejected | M: `test_md_sync.py` (Grammar: duplicate ids with lines, dropped values; Contradictions: id twice in PLAN.md and PLAN.json, title, repository, after, verification, risk, milestone title) · M: `test_scenarios.py::test_every_corruption_is_refused_with_the_cause` (6 scenarios × 9 corruptions) |
| G2 | Every launch path validates and freezes exactly the approved revision | X: `test_plan_integration.py::LaunchPaths` (standard, force, dry-run, foreground + helper, new run, resumed run refused on drift, approval, no-bypass guard) · M: `test_evidence.py::LaunchGate` · trials `lifecycle` (approve → freeze → gate → drift → re-approve) |
| G3 | Classifications justified with evidence (complexity, scope, duration, risk, coupling, confidence) | M: `test_evidence.py::Evidence`, `::Coherence`, `::PublicationAndEvidenceScope` · trials: `file:` evidence checked against real checkouts |
| G4 | Real planning trials with representative requirements; quality, coherence, dependencies, classification | `planning-trials/` (6 real trials) · fixtures in M: `tests/scenarios/` run by `test_scenarios.py` |
| G5 | Failures fixed, full suites, docs / plan state / criteria updated | REPORT.md §Verification · `PLAN-SUPERIA-FASE-1-PLANES.md` closing section · README, `plan-contract.md`, D-021 |
| AC-01 | Methodology preserved (SPEC/PLAN/handoff still produced, legacy plans work) | X: `LaunchPaths::test_legacy_plans_start_runs_exactly_as_before`, `::test_approving_a_legacy_plan_is_unchanged`, `Launch::test_legacy_plans_launch_as_before`, `ParserParity` (planner and supervisor parse identically, all real plans) |
| AC-02 | PLAN.json exists, parses, passes the versioned schema | M: `test_flow.py::test_full_cycle_is_reproducible_and_starts_nothing`, `test_contract.py::PublishedSchema` |
| AC-03 | Complete classification, no null / silent defaults | M: `test_contract.py::test_every_classification_field_is_mandatory` · `test_evidence.py::test_each_dimension_is_required` |
| AC-04 | Independent taxonomies (low complexity, high risk) | M: `test_contract.py::test_low_complexity_with_high_risk_is_allowed` · `test_evidence.py::test_low_complexity_high_risk_stays_legal` · `test_scenarios.py::test_dimensions_stay_independent_in_real_plans` · trial TRAIN-1 T2 |
| AC-05 | Dependencies verified, cycles blocked | M: `test_contract.py::test_duplicate_task_ids` and graph tests · `test_evidence.py::test_cycles_do_not_hang_or_crash_the_lints` |
| AC-06 | Shared surfaces explicit, no parallelism guarantee | M: `test_contract.py::test_shared_resources_warning_does_not_block` · `test_evidence.py::test_coupling_must_name_what_it_couples_to`, `Coherence::test_unordered_tasks_sharing_a_path_with_coupling_low_are_an_error` |
| AC-07 | Observable criteria and executable / explicit verification, no unexecuted success claimed | M: `test_contract.py::test_verification_rules` · `test_evidence.py::test_text_that_carries_no_information` · trials: commands checked to exist, planned paths exist or are created |
| AC-08 | `full_system` decomposed or documented exception | M: `test_contract.py::test_full_system_without_exception_rejected` · `test_scenarios.py::test_a_system_level_task_alone_is_refused_but_its_decomposition_publishes` · trial TRAIN-6 |
| AC-09 | Honest uncertain estimates (`confidence: low` + justification) | M: `test_evidence.py::test_high_confidence_cannot_rest_on_assumptions` · `test_scenarios.py::test_uncertainty_is_kept_not_hidden` · trials TRAIN-3 T1, METH-5 T1/T2 |
| AC-10 | Immutability and revisions | M: `test_sync.py::test_changing_a_frozen_revision_is_an_error_until_the_revision_is_bumped` · `test_evidence.py::LaunchGate::test_edit_after_approval_is_drift_not_a_new_revision` |
| AC-11 | RUN.json never rewritten by planning | X: `RunState::test_an_existing_run_json_is_never_modified_by_planner_operations` · `RealHistoricalPlans::test_a_finished_run_json_keeps_its_bytes_and_has_no_plan_ref` · trials sentinel RUN.json |
| AC-12 | Planner ends; plan readable in a later session | M: `test_flow.py::test_a_fresh_process_can_read_the_plan_without_the_planner` · trials: frozen revision read by the scheduler core reader (read-only) |
| AC-13 | Retrospective compatibility (REQ-013/015/016) | M: `test_sync.py::test_compat_is_read_only_and_reports_gaps_without_inventing_values` · X: `RealHistoricalPlans` |
| AC-14 | Negative tests name task/field | M: `test_md_sync.py`, `test_evidence.py`, `test_scenarios.py` (every needle is `<task>.<field>`) |
| AC-15 | No model / account / worker assignment | M: `test_contract.py::test_forbidden_keys_at_every_level` · `test_evidence.py::test_forbidden_scheduling_keys_inside_evidence_are_rejected` |

Constraint checks: Scheduler untouched (`git status` shows `bt_scheduler_core/`, `bt_scheduler_adapter.py` and
`PLAN-SCHEDULER-CORE-M1.md` only as another session's untracked work; none edited here); no historical RUN.json
modified; no push, no publish, no deploy.
