# Modules: how the methodology is divided

The methodology is one product split into modules. A module is a package `skill/scripts/bt_<name>/` that can be
understood, run and verified **without the rest**. First module: `bt_planner` (plans). Use this page when you extract,
add or review a module.

## Rules (each one is enforced by a test, not by good intentions)

1. **Imports: standard library + itself.** No other `bt_*` module, no third-party package, no relative import that
   climbs out of the package. → `bt_<name>/tests/test_boundaries.py` (AST).
2. **No knowledge of the rest.** It never names another module, a bitácora path, `RUN.json`, a home directory or the
   environment, and does no network/subprocess work. It works on inputs you pass in (a directory, a file, arguments).
   Methodology vocabulary it needs (e.g. which `status:` words mean approved) is a parameter with a documented default.
3. **Self-contained.** Parser, lock, schema/data (`data/`), CLI (`python -m bt_<name>`), README and tests travel inside
   the package. Writes are confined to a short documented list and checked by a test.
4. **One public surface.** `__init__.py` exports the API (`__all__`); everything else is private. The README lists the
   API, the commands and the stable error codes, and a test keeps the README and the code in step.
5. **Verifiable end to end, alone.** Own suite in `bt_<name>/tests/` including (a) `test_boundaries.py`, (b) an end-to-end
   CLI session in `python -I` from an unrelated cwd, (c) `test_isolation.py`: the package copied ALONE to a temp directory
   passes its own suite there.

## Integration (one direction only)

- Exactly one adapter, `skill/scripts/bt_<name>_adapter.py`, imports the module; argument plumbing sits in
  `bt_cli_<name>.py`. The rest of the methodology calls the adapter. Dependency: methodology → adapter → module, never back.
- `tests/test_<name>_integration.py` in the methodology suite asserts: only the adapter imports the module; the module
  imports nothing of the methodology; the module suite passes as an isolated subprocess; each hook works; existing state
  files are untouched.
- If the module deliberately duplicates a small piece of knowledge to stay independent (the planner's PLAN.md parser), a
  parity test compares both on every real plan in the repository so they cannot drift silently.
- Packaging: list the package in `pyproject.toml` `packages` and its `data/*.json`/README in `package-data`; the adapter
  and CLI plumbing go in `py-modules`; the module's tests are not shipped.

## Checklist to split another part

Identify its inputs/outputs → write the README (purpose, boundaries, API, errors) first → move code, replacing every
import of another `bt_*` by a parameter or a data argument → add the five tests above → add the adapter and rewire the
callers → delete the old modules → run both suites → record the decision in `DECISIONS.md`.
