STATUS: DONE
SUMMARY: Installer writes now refuse symlink leaves and symlinked ancestors, and verify resolved destinations stay inside the configured agent directory. POSIX writes use `O_NOFOLLOW`; configured top-level aliases and Planner’s correctly targeted methodology link remain supported. Regression tests cover external and dangling links, role files, ancestor links, alias handling, Planner links, and a leaf link introduced before open.
CHANGES: [install_agents.py](/home/david/dev/.engine-v2-wt/F2-S/skill/scripts/install_agents.py) — validate destinations and write without following leaf symlinks.
CHANGES: [test_install_symlink_safety.py](/home/david/dev/.engine-v2-wt/F2-S/skill/scripts/tests/test_install_symlink_safety.py) — add temporary-directory symlink regressions.
VERIFICATION: `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_install test_agent_skills_static test_install_symlink_safety` → exit 0; 23 tests passed (0.293s).
VERIFICATION: `python -m unittest discover -s tests` → exit 1; 2,432 tests, 15 failures, 6 skipped (880.299s). All 15 failures match the baseline categories in RULES.md; no non-baseline failures.
VERIFICATION: `git diff --check` → exit 0.
COMMITS: `d72b469e` Prevent installer writes through symlinks
PROVENANCE: N/A
CONCERNS: None.