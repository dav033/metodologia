STATUS: PARTIAL
SUMMARY: Added schema 1.3 PLAN.md `subplan`/`ui` parsing and JSON comparison while preserving legacy parser output.
Plan status tables and generated blocks group tasks within milestones and retain unassigned tasks.
The adapter now fails closed on unsupported or malformed consumer capability reports before approval or freeze; `compat` reports `consumer_supported`.
Updated the plan contract reference and committed as `1e10a2e2`.
The full suite has one additional failure caused by an outdated fixture outside my ownership.

CHANGES:
skill/references/plan-contract.md — documented schema 1.3 fields, validation, capability readiness, UI/preview, external verification, and atomic revisions.
skill/scripts/bt_planner/markdown.py — parsed and validated `subplan: SP-n` and `ui: yes|no` without adding fields to legacy parse results.
skill/scripts/bt_planner/sync.py — compared schema 1.3 membership and UI annotations with PLAN.json.
skill/scripts/bt_planner/tests/test_markdown.py — added annotation parsing and invalid-value tests.
skill/scripts/bt_planner/tests/test_md_sync.py — added round-trip, omission, and mismatch tests.
skill/scripts/bt_planstatus.py — carried subplan IDs and titles into task status data.
skill/scripts/bt_planblock.py — grouped subplan tasks in terminal and generated status output, with unassigned tasks visible once.
skill/scripts/tests/test_planstatus.py — tested subplan metadata and task visibility.
skill/scripts/tests/test_planblock.py — tested grouped rendering and unassigned tasks.
skill/scripts/bt_plan_adapter.py — added fail-closed capability checks, stable `PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE`, and `consumer_supported`.
skill/scripts/tests/test_plan_contract_compat.py — tested unsupported and malformed reports, refusal before approval/freeze, and no partial revision.
skill/scripts/tests/test_second_auditor_policy.py — updated the capability fixture to the aggregated report shape.

VERIFICATION: `python -m unittest bt_planner.tests.test_markdown bt_planner.tests.test_md_sync` → exit 0 (39 tests, 0.24 s)
VERIFICATION: Focused plan compatibility, integration, status, block, policy, and schema compatibility suites → exit 0 (70 tests, 8.29 s)
VERIFICATION: `python -m unittest discover -s bt_planner/tests` → exit 1 (360 tests, 2 skipped, 2 failures, 22.83 s)
VERIFICATION: `python -m unittest discover -s tests` → exit 1 (2411 tests, 6 skipped, 16 failures, 953.89 s); complete output: `/home/david/dev/.engine-v2-wt/F1-B-full-suite.log`
VERIFICATION: Baseline failures: 15 across migration routing parity (2), legacy contracts (5), package install (4), discovery isolation (1), collection identity (1), delegate modes (1), and glossary methodology (1), matching RULES.md.
VERIFICATION: Additional non-baseline failure: `test_subplans_are_part_of_frozen_hash_and_bind_reports_drift` in `skill/scripts/bt_planner/tests/test_schema_13.py`; also causes the isolated module suite and its root boundary test to fail.
VERIFICATION: `git diff --check` → exit 0

COMMITS: 1e10a2e2afa05bef1f1c693ce647217a90b9f4f9 feat(planner): sync human subplan fields and gate capabilities

PROVENANCE: None

CONCERNS: `skill/scripts/bt_planner/tests/test_schema_13.py` declares `subplan_id` in JSON without the required PLAN.md annotation; the new consistency check rejects it before the test’s expected drift check. This file is outside my assigned ownership, so I left it unchanged. The validator accepts 1.3.0, while init/default capability switching remains for F4-7. No bitácora files were written and nothing was pushed.