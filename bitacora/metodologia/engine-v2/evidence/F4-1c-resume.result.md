STATUS: DONE

SUMMARY: Completed the accepted F4-1c repairs in `ev2/F4-1`. Worktree is clean.  
Workspace pruning now requires ownership proof and a dead owner; failed Git removal retains data and reports the error.  
Ref transactions use no-deref behavior; migrations and publication/rejection transitions are transactional.  
Verdict proofs bind candidate identity, manifest, commit/tree, verifier, and evidence. Conflict diagnostics and empty-path evidence checks fail closed.  
The `run_base` test and docs preserve current-first behavior.

CHANGES:

- Composition engine, store, public contracts, API docs, and migration tests.
- Git adapter and real-Git integration tests.

VERIFICATION:

- `python -m unittest discover -s bt_composition/tests` → 0 (32 tests, passed).
- `python -m unittest tests.test_composition_integration` → 0 (11 tests, passed).
- `python -m unittest discover -s tests` → 1 (864.679s; 2,415 tests, 15 baseline failures, 6 skipped; no additional failures). Full log: [F4-1c-tests.log](/home/david/dev/.engine-v2-wt/F4-1c-tests.log).
- `git diff --check` → 0.

COMMIT: `22b05492cc1193013f063d8e0455f94b375c0192` — `fix(composition): close accepted repair blockers`

CONCERNS: The full suite exits 1 because of the 15 pre-existing failures listed in `RULES.md`.