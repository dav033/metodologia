# REQ-009 report — Planner PLAN.json classification contract

> **Layout superseded by REQ-010 (D-020):** the code listed below as `bt_plan_contract/revisions/sync` now lives in the isolated
> module `skill/scripts/bt_planner/` (README there), reached only through `bt_plan_adapter.py`; schema/example moved to
> `bt_planner/data/`; the module's tests are in `bt_planner/tests/`. The contract and behaviour are unchanged.

Date: 2026-10-14 · Source plan: `/home/david/dev/metodologia/PLAN-SUPERIA-FASE-1-PLANES.md` · Decision: D-019.
Nothing was committed or pushed. `RUN.json` of existing requirements was not modified (hash-checked).

## What was built (all in `/home/david/dev/metodologia/skill`)

| Piece | Where |
|---|---|
| Contract constants, validator, canonical JSON, read-only `load` | `scripts/bt_plan_contract.py` |
| Immutable revisions, manifest, `plan_ref` for new runs | `scripts/bt_plan_revisions.py` |
| Skeleton from PLAN.md, consistency, freeze, compat | `scripts/bt_plan_sync.py` |
| CLI `bitacora.py plan-json init\|check\|freeze\|show\|compat REQ-NNN` | `scripts/bt_cli_plan.py` (+3 lines in `bitacora.py`) |
| Published schema and example input | `schemas/plan.schema.json`, `schemas/plan.example.json` |
| Rubric, process, scheduler interface | `references/plan-contract.md` (+ routing row in `SKILL.md`, notes in `requirements.md` §8 and `templates/PLAN.md`) |
| Opt-in hooks | `bt_handoff.assess` (invalid PLAN.json = problem), `bt_launch.launch` (freeze when approved), `bt_runstate.init_state` (`plan_ref`) |
| Tests | `scripts/tests/test_plan_contract.py`, `test_plan_sync.py`, `test_plan_flow.py`, `test_plan_compat_real.py`, `plan_contract_support.py` |
| Evidence | `artifacts/plan-contract-map.md` (T1), `artifacts/plan-contract-compat.md` (T8) |

This requirement's own `PLAN.json` (11 tasks classified) passes `plan-json check` and is frozen as revision 1.
Its classifications are retrospective for finished work and say so in each `estimate_rationale`.

## Acceptance trace

| AC | Evidence |
|---|---|
| 01 methodology preserved | hooks are opt-in; `test_plan_flow` legacy tests; full suite 826 OK |
| 02 structured contract | `test_plan_contract::ValidPlans`, `PublishedSchema` (schema ↔ code parity), `schemas/plan.example.json` |
| 03 complete classification | `Negative.test_every_classification_field_is_mandatory`, enum/minutes tests |
| 04 independent dimensions | `ValidPlans.test_low_complexity_with_high_risk_is_allowed`, `…large_but_easy…` |
| 05 verified dependencies | duplicate/unknown/self/cycle/later-milestone tests; `test_plan_flow` handoff gate |
| 06 shared resources | `test_shared_resources_warning_does_not_block` (warning, never a parallelism guarantee) |
| 07 verifiable | `test_verification_rules`, manual needs `expected`, `created_by` for planned tests |
| 08 oversized tasks | `full_system` needs `scope_exception`; tests both directions |
| 09 honest estimates | number required (1..100000), `confidence=low` allowed with rationale |
| 10 immutability | `Revisions.test_changing_a_frozen_revision…`, tamper, gaps, orphan adoption, concurrency |
| 11 run isolation | `RunIsolation.test_planner_operations_never_touch_an_existing_run_json` |
| 12 planner ends | `PlannerCycle.test_a_fresh_process_can_read_the_plan_without_the_planner`, no `Popen`/`run` in the cycle |
| 13 retro compatibility | `test_plan_compat_real` (REQ-013/015/016 hashed before/after), report in `artifacts/plan-contract-compat.md` |
| 14 negative tests | `Negative`, `Robustness` (fuzz: `validate` never raises, wrong input never passes) |
| 15 no model selection | `FORBIDDEN_TASK_KEYS` rejected at every nesting level; `test_forbidden_keys_at_every_level` |

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s skill/scripts/tests`: 828 tests OK (93 s), 100 of them the new `test_plan_*` suites.
- `tests/migration` packaging, collection, legacy-contract and entrypoint tests: 48 OK after the last edits (a wider
  migration run, 853 OK, was done earlier on the pre-fix tree; `test_pip_install` was not run: an earlier combined run
  was killed by the OS (exit 137) and it builds a wheel).
- All new files are under 500 lines (largest: `bt_plan_contract.py` 348).

## Reviews (independent, fresh context)

Spec axis and standards axis both returned CHANGES_NEEDED; all findings were fixed with regression tests:
unhashable values crashing `validate`/`check`; forbidden keys only at task top level; Unicode digits in ids;
unconstrained `spec_ref`; NaN/huge numbers; unvalidated manifest entries; non-crash-safe, unlocked freeze; silent
swallowing in `attach_ref` (now records `plan_ref_error`); double read between check and freeze; positional zip in
`compat`. The fuzz test also found one defect nobody cited (`str()` of a huge integer raised inside an error message).
The re-verification review returned APPROVE with two low residuals (read-only or symlinked `plan-revisions`), also fixed
(`REVISION_STORE_UNWRITABLE`, `REVISION_STORE_UNSAFE`). A decision revised during the review: an orphan file for the *next* revision is a warning in `check` and is adopted or
rejected by `freeze`, because treating it as an error blocked the recovery.

## Rulings on §15 (also D-019)

1 schema in `skill/schemas`, Python only · 2 PLAN.json owns classification, skeleton from PLAN.md · 3 freeze at launch/approval,
manifest + sha256 · 4 legacy plans work unchanged; `compat` is read-only · 5 undeterminable duration blocks publication.

## Not done / limits (honest)

- The foreground launch path is not wired to freeze (P-019).
- The published JSON Schema is not executed by any validator (no dependency); the Python validator is the gate and a
  parity test keeps both aligned.
- Scheduler, calibration of estimates, web UI display: out of scope (P-020, P-021).
- Nothing was run against a live provider; no executor was launched.
- Pre-existing unrelated uncommitted work in the tree (REQ-008, REQ-007 migration) was left untouched; its hunks in
  `bt_launch.py`, `bt_handoff.py` and `bt_runstate.py` are not part of this requirement.

## Proposals

P-019 foreground freeze · P-020 scheduler and estimate calibration · P-021 UI display / optional enrichment of historical plans.
