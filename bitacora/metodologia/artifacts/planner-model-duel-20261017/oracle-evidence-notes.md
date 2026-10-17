# Source-grounded rubric interpretation (recorded while first calls are running)

The 13 expectation items were copied from existing draft corpus candidates, not from an independently validated final oracle. Interpret behaviors against the actual pinned code and SPEC; the candidate's source-path suggestions are not a golden implementation. Preserve this limitation in the report.

## CP1

The endpoint at apps/api/src/app.ts:30 returns repository.list(); project-repository.ts:33–35 SELECTs full rows and returns snapshots. The web client types list items but its listProjects() currently expects only {projects} and one unpaginated call. Updating the endpoint alone can silently truncate the visible list. Ordering is updated_at DESC without a tie-break; a cursor on mutable updated_at is not automatically snapshot-consistent. External trainingApp-mcp is not present: no measured compatibility or completion claim is possible. A safe draft may explicitly gate publication on a compatibility/notification decision without inventing acknowledgement.

## CP2

database.ts creates projects/assets with JSON validity, FK and unique external_key constraints; revision conflict and conditional no-op update behavior are in ProjectRepository.mutate. Switching to async PostgreSQL affects callers as well as persistence. backup.ts copies SQLite and asset files separately and writes hashes; a PostgreSQL backup plan must account for assets and recovery after writes on the new store. Readiness and Docker/EC2 cannot keep assuming a mounted SQLite file. The phrase 'without losing ... availability' cannot be silently changed into an approved maintenance outage. If a draft proposes a write pause, it must expose the conflict/decision gate and its unresolved consequence; do not score a zero-downtime claim as fulfilled merely because a migration has stages.

## CP3

The snapshot already lists report in bt_cli_plan.add_parser and routes it through bt_plan_adapter.run_cli to planner_cli.run. Recognizing that R1 is already implemented and adding regression proof is better than duplicating it. A structured adapter helper may still be needed for web consumption. The actual owner plan-approval UI is bt_page_req.plan_panel; bt_page_review.review_panel is the later implementation/merge review tab. The old oracle path hint must not force a wrong tab. When PLAN.json is absent, adding any new placeholder/notice changes the required existing rendering. Verify observable page output, not only a helper result. Computations stay in the Planner/report owner; CLI/web should consume an adapter projection.

## General

Host validate/check/report failures are first-response reliability results, not automatically missing substantive coverage. Reject invented passed commands, nonexistent baseline consumers/tests asserted as existing, unsupported migration safety and unrecorded owner decisions. A covers label or generic 'test thoroughly' does not prove the behavioral expectation is addressed. Unknown product decisions can be represented as gated draft work; false execution readiness must remain visible.
