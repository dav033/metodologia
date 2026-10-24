STATUS: DONE  
SUMMARY: Implemented PLAN.json schema 1.3.0 validation while preserving the 1.2.0 `init` default and legacy canonical behavior.  
Added subplan graph exposure reporting, P-177 fixtures, compatibility coverage, and negative tests for planner-owned schema error codes.  
Committed as `733793ac4` and `a40acaa8d`; worktree is clean.  
CHANGES: `skill/scripts/bt_planner/` — schema 1.3.0 validation, canonicalization, graph reporting, schema document, example, and README.  
`skill/scripts/bt_planner/tests/` — P-177 fixture and schema validation tests.  
`skill/scripts/tests/test_plan_schema_13_compat.py` — frozen-plan compatibility checks against `pre-engine-v2`.  
VERIFICATION: `python -m unittest discover -s bt_planner/tests` → exit 0; 343 tests.  
`python -m unittest tests.test_plan_schema_13_compat tests.test_plan_boundary` → exit 0; 7 tests.  
`python -m unittest discover -s tests` → exit 1; 2,406 tests, 15 failures, 6 skipped, 978.704 s. All 15 failures match the baseline categories in `RULES.md`; no additional failure.  
`git diff --check` → exit 0.  
COMMITS: `733793ac4 feat(bt-planner): support schema 1.3 subplans`  
`a40acaa8d test(bt-planner): cover remaining schema 1.3 diagnostics`  
PROVENANCE:  
CONCERNS: The `PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE` adapter capability refusal remains out of scope for F1-A; the adapter was not changed.