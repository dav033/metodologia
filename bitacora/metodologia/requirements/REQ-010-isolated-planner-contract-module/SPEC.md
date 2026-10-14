---
id: REQ-010
status: ready
created: 2026-10-14
track: standard
---
# REQ-010 — Isolated planner-contract module

## Problem & goal
REQ-009 delivered the PLAN.json contract spread over `bt_plan_*.py` files that import `bt_runstate`, `bt_lock`, `bt_core`.
The owner wants the planner to be **a module of the methodology, with the methodology divided into modules**: isolated,
verifiable end to end, working on its own, with no dependency mixing and no coupling.
**Success looks like:** the planner is the package `skill/scripts/bt_planner/` (README, public API, bundled schema,
own tests, own CLI). It imports only the Python standard library and itself (AST-enforced); its own suite passes from a
fresh interpreter (`python -I`) run from an unrelated directory; the rest of the methodology reaches it only through one
thin adapter (`bt_plan_adapter.py`), never the other way round. The same convention is written down for the next modules.

## Requirements
- R1. `bt_planner/` shall hold the contract, validator, canonical JSON, revision store, PLAN.md parser, sync/consistency,
  compat report, CLI and bundled schema/example.
- R2. The module shall import nothing but the standard library and itself, and shall not name any other `bt_*` module,
  `RUN.json` or bitácora path (AST/text-enforced test).
- R3. The module shall run with `python -m bt_planner <action> <directory>` with no other part of the methodology present.
- R4. Its tests live inside the module and shall pass in a subprocess with `python -I` from an unrelated cwd, including an
  end-to-end CLI run; the main suite runs that as one test.
- R5. The methodology shall consume it only via `skill/scripts/bt_plan_adapter.py` (+ argument plumbing in `bt_cli_plan.py`);
  the old `bt_plan_contract/revisions/sync` modules are removed; packaging includes the module.
- R6. Behaviour stays that of REQ-009 (AC-01..AC-15); all previous tests migrate; the methodology suite stays green.
- R7. A short module convention (`references/modules.md`) states the rules so other parts can be split the same way.

## Out of scope
Changing the contract itself, new features, Scheduler, splitting other parts of the methodology (only the convention is written), committing/pushing.

## Constraints
Stdlib only; files < 500 lines; no change to existing RUN.json; unrelated in-flight work in the tree is untouched.

## Assumptions
- The module keeps a small own PLAN.md task-line parser (documented grammar) instead of importing `bt_runstate`; a parity
  test in the methodology suite compares both parsers on real plans so they cannot drift silently.
- The module owns its lock (O_EXCL file inside the plan directory) instead of `bt_lock`.
- The module takes an explicit directory; `plan_id` defaults to the `REQ-NNN`-style prefix of the directory name.
