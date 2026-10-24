# Engine v2 F1-B — human plan synchronization, status grouping and consumer capability refusal

Read /home/david/dev/.engine-v2-wt/RULES.md. Start only from a reviewed/merged F1-A2 base supplied by the lead.
You are not alone: preserve all other work and edit only owned files, in your isolated worktree. No bitacora writes or push.

Read CONTRACT.md §2 F1/§6 and SCHEMA-1.3.0.md §§0,8 in /home/david/dev/metodologia/bitacora/metodologia/engine-v2/;
master §§7.8–7.9; inspect existing plan parsing/status tests and consumers before changing interfaces.

Own: skill/references/plan-contract.md; skill/scripts/bt_planner/markdown.py and matching markdown tests;
skill/scripts/bt_planstatus.py, bt_planblock.py and their tests; skill/scripts/bt_plan_adapter.py (publication capability refusal only)
and its integration/compatibility tests. If another file is required, stop with exact path and reason. Do not change schema validators/defaults,
M1/M2/M6, scheduler runtime or real plans. F4-7 later owns the final capability/default switch.

Acceptance:
1. PLAN.md task fields `subplan: SP-n` and `ui: yes|no` parse and compare with PLAN.json fields `subplan_id` and `ui`.
   Detect omitted/mismatched membership/UI metadata where JSON declares it; do not require headings to represent subplans.
   Legacy PLAN.md/JSON parsing and comparison output stay identical. Round-trip and fail-first mismatch tests.
2. plan-status and generated plan status blocks group tasks by subplan inside their existing milestones for plans with subplans;
   composition/final tasks without subplan remain visible, each task exactly once. Legacy output byte-identical via existing fixtures.
3. Adapter refuses publication/approval/freeze of unsupported schema capabilities with stable PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE,
   before owner approval or any freeze writes. Use existing downstream capability aggregation through adapters, never import M1/M2/M6
   directly into bt_planner. compat reports consumer_supported. Unknown/malformed capabilities fail closed; legacy still works.
   Prove failure makes no partial approved revision. Do not enable 1.3 default; all consumers must pass later F4 acceptance first.
4. plan-contract.md documents actual 1.3 fields, validation codes, external-verification classification, Designer gate, optional preview,
   compatibility and atomic revisions. Remove obsolete assertions that functional subplans have no schema support; describe engine readiness honestly.
5. TDD behavior/regression tests, existing related suites, full suite per RULES.md. Persist complete test output under the external worktree root.

Commit with required coauthor; return RULES.md structured final with exact totals and baseline/non-baseline failures.
