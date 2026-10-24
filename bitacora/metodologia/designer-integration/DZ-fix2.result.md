STATUS: DONE
SUMMARY: Approval resolution now reads the contract from the newest executor run’s matching subplan line; it uses `HEAD` only before a run exists.
The web snapshot, CLI `show`, and approval flow use the same revision rule.
Added coverage for line-only contracts, requirement isolation, `HEAD` fallback, and design-task output approved before the UI task starts.
Committed as `43b19369e`.
CHANGES: `bt_design_approval.py`, `bt_design_web.py`, `bt_cli_design.py`, `bt_page_req.py` — resolve and use the run’s subplan line.
`test_design_approval.py`, `test_scheduler_owner_e2e_subplans.py` — add resolver and scheduler-chain coverage.
`modules.md`, `plan-contract.md`, executor README — document the revision rule.
VERIFICATION: Focused approval and web suites → exit 0 (1.2s combined; 9 and 7 tests).
`python -m unittest discover -s tests -p test_scheduler_owner_e2e_subplans.py` → exit 0 (415.2s; 10 tests).
`python -m unittest discover -s bt_scheduler_executor/tests` → exit 0 (279.1s; 303 tests).
`python -m unittest discover -s bt_scheduler_core/tests` → exit 0 (42.4s; 333 tests).
`python -m unittest discover -s tests` → exit 1 (1092.6s; 2,595 tests, 18 failures, 6 skipped): 15 listed baseline migration failures and 3 known low-disk recovery benchmark failures; no additional failure category.
`git diff --check` → exit 0.
COMMITS: `43b19369e fix(design): approve contract from active subplan line`
PROVENANCE: N/A
CONCERNS: The full-suite failures match the baseline and low-disk exceptions documented in `RULES.md`; they were not changed.