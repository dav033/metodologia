# Task F1-A — PLAN.json schema 1.3.0 in `bt_planner` (critical path)

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Implement PLAN.json schema **1.3.0** exactly as designed in
`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/SCHEMA-1.3.0.md` (read it entirely; §0 principles and
§10 review log are binding). Context, only if needed: owner rulings
`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §2 and master spec (Spanish)
`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` §7 (lines 179–357).

## You own (edit only these)
- `skill/scripts/bt_planner/**` (code, `data/plan.schema.json`, `data/plan.example.json` may stay 1.2.0; add a
  1.3.0 example `data/plan.example.1.3.0.json`), `skill/scripts/bt_planner/README.md`, and new tests under
  `skill/scripts/bt_planner/tests/`.
- One new compatibility test file `skill/scripts/tests/test_plan_schema_13_compat.py`.

Read-only for you: `skill/scripts/bt_plan_adapter.py`, `skill/scripts/bt_scheduler_core/plan.py`,
`skill/references/plan-contract.md`, the live plans `bitacora/*/requirements/*/PLAN.json` and their
`plan-revisions/` (read them, never write them).

## Requirements
1. Versions: `LATEST_SCHEMA_VERSION = "1.3.0"` accepted by `validate`; `SCHEMA_VERSION` (the `init` default) stays
   `"1.2.0"` (it moves in a later phase). Add `SCHEMA_13 = (1, 3, 0)` gating.
2. New module(s), e.g. `subplans.py` (+ `subplan_graph.py` if needed), for every §1–§6 rule. Keep `contract.py`
   under 500 lines (it is at 481): move code out rather than in. Every new error line starts with its stable code,
   `CODE: where: message`.
3. Task keys: a separate `TASK_KEYS_13` (adds `subplan_id`, `ui` after `kind`) used **only** for 1.3.0.
   `TASK_KEYS`, `REQUIRED_TASK_KEYS`, `LEGACY_TASK_KEYS`, `SCHEMA_1_1_*`, `compat` output and every `canonicalize`
   branch below 1.3.0 must produce identical output to today. `design` is a valid `kind` only in 1.3.0.
   Verification keys `environment`, `requires`, `authorization_needed` only in 1.3.0.
4. `SCHEMA_FIELD_UNSUPPORTED` for the 1.3.0 names in a <1.3.0 document: error when `strict_publication=True`
   (publication: `check`, approve, freeze), warning otherwise (`load()` of a frozen document never starts failing).
5. P-177 regression fixture under `bt_planner/tests/scenarios/` (or a fixtures folder): a 24-task plan in two
   shapes. Legacy 1.2.0 shape: one audit at the end; F1–F5 exposure = number of tasks downstream of the introducing
   task before the first barrier, computed from the graph (≥ 20 for at least one defect). 1.3.0 shape: subplans
   with checkpoints/audits; validates with no error; every defect's exposure ≤ 6. The defect map
   (`defect → introducing task → expected first barrier`) is machine-readable and the test computes exposure with a
   helper you add to `bt_planner` (also used by `report`'s `exposure`). The 1.3.0 legacy-shaped plan (one final
   audit, 24 chained tasks) must FAIL with `LATE_CHECKPOINT`.
6. Negative tests (one per error code in SCHEMA §9), each failing before your code where feasible. Include: the
   antagonist counterexamples (publication gate cycle is now valid with two gates; mutual contract consumption with
   `defined_by` exemption is valid; a P-177 chain built via an undeclared cross-subplan `after` is rejected by
   `SUBPLAN_EDGE`; `.tsx` path without `ui` key is rejected; `ui: false` accepts it).
7. Compatibility test `skill/scripts/tests/test_plan_schema_13_compat.py`:
   - For every `bitacora/*/requirements/*/PLAN.json` and every `plan-revisions/PLAN.r*.json` next to it: the current
     `bt_planner` produces the same `validate()` errors/warnings and the same `canonicalize`/`dumps` bytes and sha256
     as the `bt_planner` of git tag `pre-engine-v2` (extract it with `git archive pre-engine-v2 skill/scripts/bt_planner`
     into a temp dir, import it under another package name; `skipTest` if the tag is unavailable). Recorded frozen
     revisions' manifest sha256 still verifies.
   - No live plan or revision uses any 1.3.0-only name.
8. `report` (1.3.0 only) adds `subplans` as SCHEMA §8; 1.0–1.2 report shapes unchanged.
9. Freeze/revisions: a 1.3.0 plan freezes as one artifact; a change in `subplans` alone changes sha256 and is
   detected as drift by `bind_approved` (test it).
10. README: a "Schema 1.3.0" section (contract, rules, codes, compatibility). Keep it factual and short.
11. JSON schema document `data/plan.schema.json` gains the 1.3.0 optional properties; the existing test that keeps it
    in step with the constants must pass (adapt the test only if the 1.3.0 keys need a separate branch).

## Out of scope (do not do)
PLAN.md `subplan:` / `ui:` task-line fields and sync, `plan-status`, the adapter capability refusal,
`plan-contract.md`, planner prompts/skills, any scheduler module. (Other tasks own them.)

## Verify
- `cd skill/scripts && python -m unittest discover -s bt_planner/tests` → 0
- `cd skill/scripts && python -m unittest tests.test_plan_schema_13_compat` (run as the suite does if imports need it)
- full suite per RULES.md.
