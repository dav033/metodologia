STATUS: PARTIAL

SUMMARY: Schema 1.3.0 subplans, composition gates and task metadata are implemented in M1.
Audited facts persist in run-state schema 4; publication facts are tied to the plan revision.
Committed as `7c1289f66d52d27c9b48b09b5407f9b4d70c10d3` with the required coauthor. Worktree is clean.
The full suite has one new failure: the flow bus has no rule for `subplan_version_published`; its implementation is outside this task’s ownership.

CHANGES:
`skill/scripts/bt_scheduler_core/plan.py` — parse schema 1.3.0 fields; include new task metadata in fingerprints.
`skill/scripts/bt_scheduler_core/subplans.py` — immutable subplan and gate models, derived status, fact operations.
`skill/scripts/bt_scheduler_core/model.py` — schema 4 persistence and in-memory upgrades.
`skill/scripts/bt_scheduler_core/scheduler.py` — audited fact APIs and M2 metadata.
`skill/scripts/bt_scheduler_core/transitions.py` — hold composition gates pending until member versions are published.
`skill/scripts/bt_scheduler_core/views.py` — subplan status and composition-waiting attention.
`skill/scripts/bt_scheduler_core/contracts.py` — add optional metadata to `StartOrder`.
`skill/scripts/bt_scheduler_core/reservation.py` — carry schema 1.3.0 metadata in start payloads.
`skill/scripts/bt_scheduler_core/dispatch.py` — pass task metadata to M3.
`skill/scripts/bt_scheduler_core/rebase.py` — include schema 1.3.0 fields in fingerprints.
`skill/scripts/bt_scheduler_core/__init__.py` — export schema capability and status API.
`skill/scripts/bt_scheduler_adapter.py` — expose fact-operation wrappers.
`skill/scripts/bt_scheduler_core/README.md` — document contracts, state, audit kinds and errors.
`skill/references/modules.md` — update the M1 description.
`skill/scripts/bt_scheduler_core/tests/test_subplans.py` — cover parsing, facts, gating and metadata.
`skill/scripts/bt_scheduler_core/tests/test_persistence.py` — cover schema migration and fact persistence.
`skill/scripts/bt_scheduler_core/tests/test_routing.py` — update expected state schema.
`skill/scripts/tests/test_scheduler_subplan_adapter.py` — cover adapter forwarding.

VERIFICATION:
`python -m unittest discover -s bt_scheduler_core/tests` → exit 0; 305 tests (63 s).
Focused subplan, persistence and adapter-forwarding tests → exit 0; 7, 24 and 1 tests.
Adapter-importing test sweep → most passed; isolated failures: `test_plan_amendments.py` (14, `PLAN_CHECKS_UNMAPPED`), `test_recovery_hardening.py` (1, `open` vs `unrepairable`), `test_remote_recovery.py` (1, `PLAN_CHECKS_UNMAPPED`), `test_scheduler_decision_sources.py` (1, `PLAN_CHECKS_UNMAPPED`).
`python -m unittest discover -s tests` → exit 1 (897 s); 2,415 tests, 16 failures, 6 skipped. Fifteen are the baselines listed in `RULES.md`; the additional failure is `test_every_m1_audit_kind_has_a_rule`, because `bt_flow_bus.M1_RULES` lacks `subplan_version_published`.
`git diff --cached --check` → exit 0. `git status` → clean.

COMMITS:
`7c1289f66d52d27c9b48b09b5407f9b4d70c10d3 feat(scheduler-core): support plan schema 1.3.0 subplans`

PROVENANCE: None.

CONCERNS: Adding the required audit kind exposes a consumer mapping gap in `skill/scripts/bt_flow_bus.py`. I left it untouched because it is outside the authorized files; the lead must decide who updates that consumer. Full test output is saved at `/home/david/dev/.engine-v2-wt/F4-3-resumed-tests.log`.