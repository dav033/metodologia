# Modules: how the methodology is divided

The methodology is one product split into modules. A module is a package `skill/scripts/bt_<name>/` that can be
understood, run and verified **without the rest**. Modules so far: `bt_planner` (plans) and `bt_scheduler_core` (runs an approved plan). Use this page when you extract,
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

## Scheduler core (`bt_scheduler_core`, REQ-011)

The second module, built under the same five rules. It is the deterministic heart of the Scheduler (system parent of
M1 core, M2 decision, M3 executor, M4 monitor, M5 recovery): it loads a hash-approved `PLAN.json`, resolves the DAG, runs the
task/attempt state machine on a transactional store (SQLite WAL), reserves capacity/resources atomically, dispatches through
ports, ingests events idempotently and reconciles after a restart. **No AI inside**: sibling modules implement the ports
(`AssignmentPort`, `ExecutionPort`, `RecoveryPort`, `VerificationPort`, `StateRepository`; contract in its README) and may
be simulated with `bt_scheduler_core.simulators`.

- Adapter: `skill/scripts/bt_scheduler_adapter.py` (only file that imports it). It hands the core the latest frozen plan
  revision (through `bt_plan_adapter`, hash from the planner's manifest — approval is the caller-supplied sha256, no hash,
  no run), opens the run database at `<bitácora root>/.state/scheduler/<project>-<REQ>.db` (local, untracked; outside that
  layout `<requirement>/SCHEDULER.db`), and can write a `RUN.json`-shaped read model marked `authority: "scheduler"` as
  `<requirement>/RUN.projection.json`.
- **One authority per requirement**: a requirement is run by the legacy supervisor (`RUN.json`) or by the core (its run
  database), never both; the database alone decides. The projection is never called `RUN.json`, so no legacy control can
  write into it and no legacy state file can be overwritten by it. The adapter refuses to open a core over a legacy
  `RUN.json`; `bt_runentry.supervise` refuses a scheduler-owned requirement. Historical runs are not migrated.
- Opt-in: nothing in the existing commands changes; the core is used by calling the adapter or `python -m bt_scheduler_core`.
- Tests: module suite `bt_scheduler_core/tests/` (boundaries, lone-copy isolation, CLI end to end, fuzzed invariants,
  crash-at-every-commit restarts) and `tests/test_scheduler_integration.py` (boundary from outside, frozen-plan hand-over,
  authority rules, historical `RUN.json` byte-identical).
