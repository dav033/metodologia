STATUS: DONE

SUMMARY:
Fixed aggregate reason codes so rejected and unresolved verification results cannot report `PASS`.
Legacy result replay now returns `UNCLASSIFIED` without changing stored content or hashes; normalized legacy reads validate.
Published contract and runtime both reject incomplete composition identity.
Moved check cache/history persistence and migration into a 106-line module; `QualityStore` retains its public API and transaction boundary.
Full suite output is saved at `/home/david/dev/.engine-v2-wt/F4-6/F4-6-fix-tests.log`.

CHANGES:
skill/scripts/bt_scheduler_quality/evidence.py — classify final verdicts and validate normalized legacy records.
skill/scripts/bt_scheduler_quality/store.py — migrate replay results and delegate history persistence.
skill/scripts/bt_scheduler_quality/check_history.py — own check cache/history schema, migration, and persistence.
skill/scripts/bt_scheduler_quality/api-contract.json — require composition identity fields together.
skill/scripts/bt_scheduler_quality/tests/ — cover public review outcomes, legacy replay and validation, composition identity, and module boundary.

VERIFICATION:
`python -m unittest discover -s bt_scheduler_quality/tests` → exit 0; 168 passed (15.357 s).
Audit-gate, audit-evidence, CLI ledger, ledger deferral, quality ledger, and real M6 integration tests → exit 0; 49 passed total.
`python -m unittest discover -s tests` → exit 0; 2228 tests, 6 skipped (573 s); 0 baseline and 0 non-baseline failures.
`git diff --check` → exit 0.

COMMITS:
ac83315d6ef84fcf1e0df0c688f47f0fb6f25089 engine-v2: fix M6 evidence migration and history boundary

PROVENANCE: none

CONCERNS: Cross-ledger production owner wiring remains assigned to F4-9; external verification metadata remains assigned to F4-7. The requested test log remains untracked in the worktree.