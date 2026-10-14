# PLAN.json compatibility report: REQ-013, REQ-015, REQ-016 (pictures)

Generated 2026-10-14 by `bt_plan_sync.compat` (read-only). Each requirement folder was hashed before and after:
no file changed (including REQ-016's `RUN.json` and `HANDOFF.md`). Nothing was written, no value was imputed.

| Requirement | PLAN.md status | Tasks | `### M` milestones | Tasks without milestone | RUN.json | HANDOFF.md | Gaps in a derived skeleton |
|---|---|---|---|---|---|---|---|
| REQ-013 | in-progress | 32 | none | 32 | no | no | 449 |
| REQ-015 | done | 13 | none | 13 | no | no | 168 |
| REQ-016 | done | 3 | M1, M2 | 0 | yes | yes | 34 |

## What each plan already provides (derivable without guessing)

- **REQ-013**: `after` 32/32, `id` 32/32, `title` 32/32
- **REQ-015**: `after` 13/13, `expected_paths` 3/13, `id` 13/13, `title` 13/13, `verification` 12/13
- **REQ-016**: `after` 3/3, `expected_paths` 1/3, `id` 3/3, `milestone_id` 3/3, `repository` 3/3, `title` 3/3, `verification` 3/3

## What needs explicit enrichment

Every task of the three plans lacks `objective`, `complexity`, `scope`, `estimated_minutes`, `risk`, `coupling`, `confidence`,
`estimate_rationale`, `acceptance_criteria` and `shared_resources`; milestones lack `acceptance_criteria`. These are
reported as **classification not available**, not estimated.

Structural findings:

- **REQ-013 and REQ-015 have no `### M<n>` headings** (REQ-013 groups tasks under `## Phase N`; its `status:` is the free text
  `in-progress (phases 1-5 built, 6-7 pending)`). The contract requires a milestone per task, so a `PLAN.json` for them needs
  milestones declared by a human (e.g. phases as milestones) and matching `### M<n>` headings or an explicit migration decision.
  The parser reads the first word of the status, so approval logic still works.
- **Repository role** is derivable only when a task line carries `repo:`; no task line of REQ-013 or REQ-015 has one, so `repository` must be supplied.
- **Verification** is derivable only from backticked `verify:` values; REQ-013 has none (0/32) and REQ-015 has 12/13; the rest need a command or a manual
  check with `expected`.
- **Legacy labels**: no task of these three plans declares `complexity:` or `risk:` on its line, so there is nothing to carry over
  (where other plans use `complexity: S/M/L`, `compat` lists it as `legacy_complexity` and never maps it to low/medium/high).
- **REQ-016** is the closest to the contract (milestones M1/M2, repo, verify, `after`). Its `RUN.json` keeps `complexity`/`risk` null;
  it has no `plan_ref` and none is added retroactively (only new runs record one).

## Decision

Migration is opt-in per requirement: `plan-json init` derives a skeleton; the owner or planner supplies the classification
explicitly. Historical plans keep working in the old flow without `PLAN.json` (`handoff`/`launch` only act when the file exists).

Reproduce: `python3 -c` over `bt_plan_sync.compat(<requirement dir>)` for each folder, as in `skill/scripts/tests/test_plan_compat_real.py`.
