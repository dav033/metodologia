---
id: REQ-012
status: done
created: 2026-10-14
---
# Plan — REQ-012 Planner phase 1 closure

Executed inline by the owner's `/goal` (no handoff): single session, iterative build → test → detect → fix.
Repository: `skill` (`~/dev/metodologia`). Scheduler and `RUN.json` untouched.

### M1 — Strict PLAN.md ↔ PLAN.json sync
- [x] T1 — Report what the PLAN.md parser drops and reject duplicate ids/headings · repo: skill · files: skill/scripts/bt_planner/markdown.py · verify: `python3 -m unittest bt_planner.tests.test_md_sync`
- [x] T2 — Compare title, repo, after, verify, risk and milestone titles; always evaluate both layers · repo: skill · after: T1 · files: skill/scripts/bt_planner/sync.py · verify: `python3 -m unittest bt_planner.tests.test_md_sync`

### M2 — One launch gate
- [x] T3 — Planner `bind_approved` and PLAN_DRIFT/PLAN_MISSING; approval freezes · repo: skill · after: T2 · files: skill/scripts/bt_planner/sync.py, skill/scripts/bt_rounds.py · verify: `python3 -m unittest bt_planner.tests.test_evidence`
- [x] T4 — Route standard, web, handoff, foreground (+helper) and new runs through the gate · repo: skill · after: T3 · files: skill/scripts/bt_plan_adapter.py, skill/scripts/bt_launch.py, skill/scripts/bt_orchestration_transition.py, skill/scripts/bt_run.py · verify: `python3 -m unittest tests.test_plan_integration`

### M3 — Justified classifications
- [x] T5 — Schema 1.1.0, evidence rules and plan-level coherence (evidence.py, quality.py) · repo: skill · after: T2 · files: skill/scripts/bt_planner/evidence.py, skill/scripts/bt_planner/quality.py, skill/scripts/bt_planner/contract.py, skill/scripts/bt_planner/data/plan.schema.json · verify: `python3 -m unittest bt_planner.tests.test_evidence`

### M4 — Real planning trials
- [x] T6 — Six trials on real repositories (plans, judge, corruption battery, lifecycle) and fixtures for the module suite · repo: skill · after: T4, T5 · files: skill/scripts/bt_planner/tests/test_scenarios.py · verify: `python3 -m unittest bt_planner.tests.test_scenarios`

### M5 — Close
- [x] T7 — Full suites, docs, plan state and acceptance traceability · repo: skill · after: T6 · files: skill/references/plan-contract.md, PLAN-SUPERIA-FASE-1-PLANES.md · verify: `python3 -m unittest discover -s tests`

## Progress log
- 2026-10-14 T1–T7 done in one session; defects found by the trials and fixed: terse justifications rejected legit trivial
  tasks (floor lowered 5 → 4 words and plans improved), a stated `verify:` in my own PLAN.md differed from PLAN.json
  (caught by the new check), consistency was skipped while schema errors existed (now both layers always run), a
  checked-in historical title drift in REQ-009 surfaced (P-024), quadratic/recursive graph lints made iterative.
