---
req: REQ-009
status: approved
created: 2026-10-14
---
# Plan — Planner PLAN.json classification contract

## Approach
Follow `/home/david/dev/metodologia/PLAN-SUPERIA-FASE-1-PLANES.md` §8. Pure-stdlib contract module + CLI
`plan-json init|check|freeze|compat`, new reference docs, tests per §10. Approved by the owner's `/goal` (2026-10-14).

## Global constraints
No commit/push; do not modify any RUN.json; stdlib only; new modules under 500 lines.

## Tasks

### M1 — Diagnosis and contract design
- [x] T1 — Map producers/consumers of SPEC/PLAN/HANDOFF/RUN · verify: `test -s /home/david/bitacora/metodologia/artifacts/plan-contract-map.md`
- [ ] T2 — JSON Schema 1.0.0 and validator core · after: T1 · files: skill/schemas/plan.schema.json, skill/scripts/bt_plan_contract.py
- [ ] T3 — Classification rubric with boundary examples · after: T1 · files: skill/references/plan-contract.md

### M2 — Structured output and sync
- [ ] T4 — PLAN.json generation (init) in the planner flow · after: T2, T3
- [ ] T5 — PLAN.md <-> PLAN.json consistency check · after: T4
- [ ] T6 — Immutable approved revisions and run reference · after: T4

### M3 — Validation and backwards compatibility
- [ ] T7 — Full validator with negative tests · after: T2, T4
- [ ] T8 — Compatibility report on REQ-013/015/016 · after: T5, T7
- [ ] T9 — End-to-end planner cycle test · after: T6, T8

### M4 — Documentation and adoption
- [ ] T10 — Document contract, rubric and review process · after: T9
- [ ] T11 — Scheduler read-only loader and example input · after: T9

## Verification
`PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests` plus AC-01..AC-15 trace in the final report.

## Rulings

## Progress log
