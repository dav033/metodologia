# REQ-010 report — Isolated planner module (`bt_planner`)

Date: 2026-10-14 · Decision: D-020 · Follows REQ-009 (D-019). Nothing committed or pushed.
Owner's request: the planner as an isolated module, verifiable end to end, working independently, no dependency mixing,
no coupling; clarified mid-work: it stays part of the methodology, divided into modules (so not a separate project).

## What changed

| Area | Result |
|---|---|
| New module | `skill/scripts/bt_planner/`: `contract.py`, `revisions.py`, `markdown.py` (own PLAN.md parser), `sync.py`, `_lock.py` (own lock), `cli.py` + `__main__.py`, `resources.py`, `data/plan.schema.json`, `data/plan.example.json`, `README.md`, `tests/` |
| Boundary | imports only the standard library and itself; no other `bt_*`, `RUN.json`, bitácora path, env, subprocess/network, dynamic import or `parents[N]` (AST + text tests, each with mutation tests of the detector) |
| Seam | one adapter `skill/scripts/bt_plan_adapter.py` (+ `bt_cli_plan.py` argument plumbing). Hooks: `bt_handoff.assess`, `bt_launch.launch`, `bt_runstate.init_state` each call the adapter |
| Removed | `bt_plan_contract.py`, `bt_plan_revisions.py`, `bt_plan_sync.py`, `skill/schemas/` |
| Packaging | `pyproject`: package `bt_planner` + `data/*.json`/README as package data; adapter in `py-modules`; module tests not shipped; wheel test checks content and runs `python -m bt_planner example` from the installed wheel |
| Docs | `bt_planner/README.md` (contract, rubric, API, CLI, error codes), `references/plan-contract.md` (how the methodology uses it), new `references/modules.md` (convention to split other parts), routing rows in `SKILL.md` |

Contract and behaviour are those of REQ-009 (AC-01..AC-15 unchanged). Extras of the extraction: `python -m bt_planner`
with `validate <file>`, `schema`, `example`, `--plan-id`, `--approved-states`; `run_reference()` replaces `attach_ref`
(the module returns fields, the methodology merges them); `list_revisions` replaces `revisions` (name clash with the submodule).

## Acceptance (R1-R7)

| R | Evidence |
|---|---|
| R1 content inside the package | file list above; `test_boundaries.test_sources_exist` |
| R2 boundary | `bt_planner/tests/test_boundaries.py` (AST + text checks and tests of the detector); manual mutations (environ alias, getenv, eval, parents[3], bt_core, subprocess, requests) each fail the suite |
| R3 own CLI | `test_e2e_cli.py` (subprocess, `python -I`, unrelated cwd): init, check, freeze, drift, bump, compat, validate example |
| R4 verifiable alone | `test_isolation.py`: package copied alone to a temp dir passes its suite there; the main suite runs the module suite as an isolated subprocess |
| R5 one adapter | `test_plan_integration.Boundary`: repo-wide AST/string scan, only the adapter (and two allow-listed tests) names `bt_planner`; old modules gone; wheel test |
| R6 same behaviour | module and methodology tests migrated; hooks, run state, AC-11 (existing RUN.json bytes untouched), real-plan compat (REQ-013/015/016 hashed before/after); parser parity with `bt_runstate.parse_plan` on synthetic input and on every real PLAN.md in the repo (incl. complexity normalisation) |
| R7 convention | `references/modules.md`, asserted by `test_plan_integration.Wiring` |

## Verification (final tree)

- Module suite, isolated interpreter: `cd skill/scripts && python3 -I -m unittest discover -s bt_planner/tests` -> **111 OK** (includes the lone-copy run, 5 concurrent processes freezing the same plan, stale/busy lock).
- Methodology suite: `cd skill/scripts && python3 -m unittest discover -s tests` -> **752 OK**.
- Packaging/migration (wheel built and installed in a venv): package-install, collection identity, legacy contracts, entrypoint parity, namespace alias, legacy collection -> **802 OK**.
- Every new file < 500 lines (largest `test_sync.py` 474). This requirement's own `PLAN.json` (7 tasks) checks clean and is frozen as revision 1.

## Review

Independent spec+isolation review: APPROVE, no isolation breach, with 3 medium and 4 low hardening items, all addressed
except the foreground-launch gap (P-019): boundary test now AST-based (aliased `environ`/`getenv`, `eval`/`exec`/
`__import__`/`import_module`/`compile()`, `parents[N]`) with tests of the detector; the "no methodology reachable" command
test uses a lone copy; the importer scan walks the whole repo and flags string references; parity also compares
`complexity`; the brittle `ran > 100` count relaxed; lock tests added (multi-process, stale, busy, release on error,
unwritable) and a non-re-entrancy note.

## Deliberate trade-offs / limits

- The module keeps its own small PLAN.md parser and lock (duplicated knowledge) to stay independent; the parity test is the guard.
- The foreground launch path (`bt_orchestration_transition`, in-flight REQ-008 work) still does not freeze (P-019, unchanged).
- The lock is not re-entrant and its stale-break has the usual two-waiter race; critical sections are one manifest write.
- Only the planner is split. Other parts remain flat `bt_*` files; `modules.md` is the recipe (proposal P-022).
- `test_pip_install` (builds a wheel through pip) was not run; the wheel is built and installed by `test_package_install`.
- Nothing was run against a live provider. Unrelated in-flight work (REQ-007/008) in the tree is untouched.
