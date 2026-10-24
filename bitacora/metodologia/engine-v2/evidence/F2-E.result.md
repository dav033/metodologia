STATUS: DONE
SUMMARY: Runtime enforcement rejects schema 1.3.0 Designer snapshots that change paths outside `design/`, including both sides of an escaping rename. Preview writes require the project setting; refused snapshots remain preserved and are rejected before verification. Legacy plans and other task kinds retain existing behavior.
CHANGES: `skill/scripts/bt_scheduler_executor_adapter.py` — added exact snapshot diff checks and stable refusal codes.
CHANGES: `skill/scripts/bt_scheduler_executor_wiring.py` — applied checks to terminal success events before verification.
CHANGES: `skill/scripts/bt_config.py`, `skill/scripts/tests/test_config.py` — added `design.preview` and `design.preview_projects` settings and validation.
CHANGES: `skill/scripts/tests/test_designer_write_scope.py` — covered scope, rename, preview, legacy, non-design, and pre-verification refusal behavior.
CHANGES: `skill/references/modules.md` — documented the runtime gate.
VERIFICATION: Focused executor, config, and audit gate tests → exit 0 (2.8s); 81 tests.
VERIFICATION: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/bt_scheduler_quality/tests` → exit 0 (19.6s); 156 tests.
VERIFICATION: `python -m unittest discover -s tests` → exit 1 (941.8s); 2,410 tests, 15 failures, 6 skipped. All 15 failures match the baseline categories in `RULES.md`; no additional failure.
VERIFICATION: `git diff --check` → exit 0.
COMMITS: `c93512da` Enforce Designer runtime write scope
PROVENANCE: None.
CONCERNS: The full suite remains red on the 15 documented baseline failures.