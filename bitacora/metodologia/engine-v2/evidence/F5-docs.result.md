STATUS: PARTIAL
SUMMARY: Updated the plan contract, module map, role installation guidance, routing table and README for Engine v2.  
Documented schema 1.3.0 defaults, composition and M1 state, trusted verification authority, Designer and visual review, `bt_knowledge`, and the D-10 benchmark.  
Audited `third-party-notices.md`; its F2/F3 sources already include repository, path, commit SHA and license, so it needed no edits.  
No code changed. The worktree is clean after commit `f2eb8bff6`.
CHANGES: `skill/references/plan-contract.md` — default and legacy schemas; M6 evidence and operator-owned verification authority.  
CHANGES: `skill/references/modules.md` — composition engine, M1 schema 9, knowledge stores and D-10 benchmark.  
CHANGES: `skill/references/agents.md`, `skill/references/subagents.md` — eight roles, private skill locations, installation behavior and subplan review coverage.  
CHANGES: `skill/SKILL.md` — concise routing for composition, Designer/visual review and verification policy.  
CHANGES: `README.md` — Engine v2 capabilities, role count and installer behavior.
VERIFICATION: `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_agent_skills_static` → exit 0 (9 tests; 0.071 s).
VERIFICATION: Document-consistency modules selected by `grep -l 'README\|modules.md\|SKILL.md' skill/scripts/tests/test_*.py` → exit 1 (372 tests; 41 failures, 1 skipped; 179.158 s). Repeated failure: fixtures stop at `PLAN_CHECKS_UNMAPPED` because verification purposes do not exactly match criteria.
VERIFICATION: `python -m unittest discover -s tests -p 'test_legacy_collection.py'` → exit 1 (2,353 tests; 3 failures, 6 skipped; 903.068 s). All 3 failures were in `test_recovery_benchmark`, involving the S11 disk/workspace scenario and intervention-count expectations.
VERIFICATION: `git diff --staged --check` and post-commit `git diff HEAD^ --check` → exit 0. Commit hook gitleaks scan → exit 0, no leaks found.
COMMITS: `f2eb8bff6 docs(engine-v2): document schema 1.3 and composition runtime`
PROVENANCE: No new upstream sources. The existing F2/F3 entries in `third-party-notices.md` were checked for repository, path, pinned SHA and license.
CONCERNS: Test failures remain unmodified because this task is documentation-only. The legacy failures are recorded as observed; a baseline comparison was not performed.