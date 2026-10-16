---
status: approved
---
# Plan — METH-4

### M1 — Terminal
- [ ] T1 — Expose the report action through the adapter and the plan-json command · repo: metodologia · files: skill/scripts/bt_plan_adapter.py, skill/scripts/bt_cli_plan.py · verify: `python3 -m unittest tests.test_plan_integration` · resources: plan-adapter-api

### M2 — Web review
- [ ] T2 — Render the summary block on the plan review page · repo: metodologia · after: T1 · files: skill/scripts/bt_page_req.py, skill/scripts/tests/test_plan_integration.py · verify: `python3 -m unittest tests.test_plan_integration` · resources: plan-adapter-api
- [ ] T3 — Document the new views in the plan contract reference · repo: metodologia · after: T2 · files: skill/references/plan-contract.md
