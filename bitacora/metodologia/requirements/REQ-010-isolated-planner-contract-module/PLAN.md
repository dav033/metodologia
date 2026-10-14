---
req: REQ-010
status: done
created: 2026-10-14
---
# Plan — REQ-010 — Isolated planner-contract module

## Approach
Extract REQ-009's code into the package `skill/scripts/bt_planner/` (stdlib-only, AST-enforced boundary, own tests and
CLI), then make the methodology depend on it through one adapter. Alternative considered and rejected after the owner's
clarification: a separate project with its own pyproject (the planner is part of the methodology, divided into modules). Approved by the owner's request (2026-10-14).

## Global constraints
_Copied from the spec: things every task must respect._

## Tasks

### M1 — Standalone module
- [x] T1 — Create the `bt_planner` package and move contract/revisions with an own lock
- [x] T2 — Own PLAN.md parser, sync, compat, CLI (`python -m bt_planner`), bundled schema and example · after: T1

### M2 — Isolation proof
- [x] T3 — Migrate core tests into the module and add import-boundary, bundled-fixtures and end-to-end CLI tests · after: T2
- [x] T4 — Prove it works from a fresh `python -I` interpreter in an unrelated cwd, with nothing else of the methodology on the path · after: T3

### M3 — Re-integrate the methodology
- [x] T5 — Thin adapter `bt_plan_adapter.py`; rewire bt_cli_plan, bt_launch, bt_handoff, bt_runstate; remove old modules; packaging · after: T4
- [x] T6 — Integration tests (hooks, run state, real-plan parser parity and compat) · after: T5

### M4 — Verify and document
- [x] T7 — Full suites, independent review, docs (module README, `references/modules.md`, plan-contract reference), bitácora and report · after: T6

## Verification
_End-to-end check that proves the spec's acceptance criteria (tests, running the app, a dry run of the process)._

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
