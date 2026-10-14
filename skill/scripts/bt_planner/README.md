# bt_planner — the planner module

Part of the methodology, isolated by construction. It **describes and classifies work**: a human `PLAN.md` next to a
validated, versioned `PLAN.json` that a deterministic scheduler can read without interpreting prose. It inspects nothing
about who will run the work: it never picks a model, account or worker count, never supervises, and never writes
execution state. Only two things are written: `PLAN.json` (`init`) and `plan-revisions/` (`freeze`).

## Boundaries (enforced by `tests/test_boundaries.py`)

- Imports only the Python standard library and itself. No other `bt_*` module, no third-party package.
- Names no methodology path or file (`bitacora`, `RUN.json`, `~`): it works on **a directory you pass in**.
- Everything it needs travels inside the package: parser, lock, schema (`data/plan.schema.json`), example
  (`data/plan.example.json`), CLI, tests.
- The rest of the methodology reaches it through one adapter, `skill/scripts/bt_plan_adapter.py`. The dependency points
  one way only: adapter → `bt_planner`.

## Layout

| File | Role |
|---|---|
| `contract.py` | enums, validator, canonical JSON, `load`, `PlanContractError`, `Report` |
| `revisions.py` | immutable approved revisions (`plan-revisions/`), manifest + sha256, `run_reference` |
| `markdown.py` | the `PLAN.md` task-line / milestone grammar (own parser) |
| `sync.py` | skeleton from PLAN.md, PLAN.md ↔ PLAN.json consistency, `check`, freeze, compat report |
| `_lock.py` | exclusive lock for one plan directory |
| `cli.py`, `__main__.py` | command line |
| `data/` | bundled JSON Schema and example plan |
| `tests/` | the module's own suite (run from anywhere) |

## Command line

All actions: `python -m bt_planner <action> [directory|file] [--plan-id ID] [--force] [--json] [--approved-states a,b]`
(run with the folder that contains `bt_planner` on `PYTHONPATH`, or from it). Exit code 0 = ok, 2 = invalid or refused.

- `python -m bt_planner init <dir>` derives the skeleton from `<dir>/PLAN.md`; classification stays absent and is
  reported as gaps (never defaulted).
- `python -m bt_planner check <dir>` is the publication gate: schema, unique ids, existing references, no cycles, no
  dependency on a later milestone, no orphan milestone, PLAN.md ↔ PLAN.json agreement on ids / milestone membership /
  `after`, and frozen-revision integrity.
- `python -m bt_planner freeze <dir>` freezes the checked PLAN.json as the next revision. `PLAN.md` front matter
  `status:` must be one of `approved, launched, done, merged` (override with `--approved-states`).
- `python -m bt_planner show <dir>` lists frozen revisions.
- `python -m bt_planner compat <dir>` is read-only: what an existing plan already provides and what needs explicit
  enrichment (legacy `complexity:`/`risk:` values are reported verbatim as legacy labels, never converted).
- `python -m bt_planner validate <file>` validates one PLAN.json on its own, e.g. a scheduler's input.
- `python -m bt_planner schema` / `python -m bt_planner example` print the bundled schema / example.

`plan_id` defaults to the `REQ-042` style prefix of the directory name (`REQ-042-some-slug`), otherwise the directory name.

## Python API

```python
import bt_planner as planner
plan = planner.load(path_to_plan_json)                 # validated, read-only; raises PlanContractError
report = planner.check(directory)                      # Report(errors, warnings, ok)
entry = planner.approve_freeze(directory)              # {revision, sha256, frozen_at}
frozen = planner.load_revision(directory, 1)           # what an executor ran, hash-verified
fields = planner.run_reference(directory)              # {"plan_ref": {...}} | {"plan_ref_error": code} | {}
```

Files that exist before the module is used: `PLAN.md` (the narrative; grammar below), `SPEC.md` (target of `spec_ref`).

## PLAN.md grammar understood

```
### M1 — Milestone title
- [ ] T1 — Task title · repo: backend · after: T0, T0a · verify: `pytest -q` · files: src/a.py · resources: db
```

Task ids `T1`, `T2.1`, `T3a`; milestone headings `###`/`####` with `M<number>`; fields separated by ` · `; `verify` only
when backticked; unsafe `files` (absolute or `..`) are dropped; HTML comments ignored.

## The contract (schema 1.0.0)

Per task, all required (no `null`, no silent defaults): `id`, `milestone_id`, `title`, `objective`, `repository`,
`after` (`[]` if none), `acceptance_criteria` (observable, non-empty), `verification` (`{type: command|manual, value,
purpose}`; `manual` also needs `expected`; optional `created_by: T<n>` for a test the plan itself creates),
`complexity`, `scope`, `estimated_minutes`, `risk`, `coupling`, `confidence`, `estimate_rationale`, `expected_paths`
(guidance, may be `[]`), `shared_resources` (`[]` if none known). Per milestone: `id`, `title`, `acceptance_criteria`.
Top level: `schema_version`, `plan_id`, `revision` (1..1000000), `spec_ref` (relative path inside the directory),
`milestones`, `tasks`. Extra fields are allowed, except scheduling/execution keys (`model`, `agent`, `account`,
`workers`, `status`, `attempts`, `sessions`, `cost`…) which are rejected at any nesting level. Ids use ASCII digits;
NaN/Infinity are rejected; `estimated_minutes` is 1..100000 (a warning above 480: consider splitting).

### Rubric (the dimensions are independent)

- **complexity** = reasoning needed, not time, file count or model quality. `low` known localized solution · `medium`
  some investigation/decisions · `high` cross-component reasoning or relevant uncertainty · `extreme` exceptional
  uncertainty or far-reaching architectural decisions.
- **scope** = size of the change: `isolated_fix` · `small_change` · `large_change` (extensive/transversal) ·
  `full_feature` (verifiable end to end) · `full_system` (**decompose it**; only with `scope_exception: {reason}`).
- **estimated_minutes** = integer for one reasonable run including local verification; an estimate, not a limit. If no
  number can be defended, do not publish: split the task or add a research task first.
- **risk** = impact of a mistake: `low` local, reversible, caught by simple tests · `medium` possible functional
  regression or shared contract · `high` security, data, permissions, compatibility, production, payments or hard to revert.
- **coupling** = interaction with other tasks: `low` independent · `medium` shared contracts/resources need coordination ·
  `high` tight interaction or high conflict potential. A signal for a scheduler, never permission to parallelise.
- **confidence** (of the estimate): `high` code investigated, precedent or direct evidence · `medium` partial evidence ·
  `low` preliminary or depends on relevant unknowns. `low` is allowed; say why in `estimate_rationale`.

| Case | complexity | scope | risk | coupling | Note |
|---|---|---|---|---|---|
| Two-line fix of an authorization check | low | isolated_fix | high | medium | easy but sensitive; shares the session contract |
| Mechanical rename across 80 files with codemod | low | large_change | medium | high | big, not hard; many tasks touch the same paths |
| Change a public API response shape used by two clients | high | large_change | high | high | cross contracts; name the contract in `shared_resources` |
| New report page with its own endpoint and tests | medium | full_feature | medium | low | end-to-end, self-contained |
| Replace the persistence layer | extreme | full_system | high | high | **decompose** (adapter, migration, cutover…) or file an exception |
| Add a CSS token to one component | low | small_change | low | low | trivial everywhere |
| Investigate why a job is flaky, outcome unknown | medium | small_change | low | low | `confidence: low`; likely precedes a fix task |

Honesty rules: planned tests that do not exist yet are work items (`created_by`), never evidence; manual checks state the
expected result; do not attribute success that was not executed; distinguish "classification not available" from "estimated".

## Revisions

`freeze` writes `plan-revisions/PLAN.r<N>.json` (canonical text, read-only, created exclusively) and appends to
`plan-revisions/MANIFEST.json` under a lock. A frozen revision never changes: editing PLAN.json afterwards makes `check`
fail until `revision` is bumped to N+1. An orphan revision file left by an interrupted freeze is adopted when identical
and refused otherwise. `run_reference` gives an executor the three fields it should remember (`plan_id`, `revision`,
`sha256`) instead of copying the plan.

## Error codes

`PlanContractError.code` is stable; `issues` are actionable lines naming the task and field.
Reading: `PLAN_NOT_FOUND`, `PLAN_UNREADABLE`, `PLAN_NOT_JSON` (also NaN/Infinity and absurd nesting), `PLAN_TOO_LARGE`,
`PLAN_NOT_SERIALISABLE`, `PLAN_INVALID` (e.g. `T3.risk: 'critical' is not one of low, medium, high`).
Revisions: `REVISION_UNKNOWN`, `REVISION_TAMPERED`, `REVISION_FROZEN`, `REVISION_ORDER`, `REVISION_STORE_DAMAGED`,
`REVISION_STORE_UNREADABLE`, `REVISION_STORE_UNSAFE` (symlinked directory), `REVISION_STORE_UNWRITABLE`,
`REVISION_STORE_BUSY`. CLI-side refusals: `PLAN_EXISTS`, `PLAN_MD_EMPTY`, `PLAN_NOT_APPROVED`.

## Verify it

```
cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -v          # the module's own suite
python3 -I -m unittest discover -s bt_planner/tests                             # same, isolated interpreter
```

`tests/test_isolation.py` copies the package alone to a temporary directory and runs this suite and an end-to-end CLI
session there with `python -I`, so nothing from the methodology can be silently relied on.
