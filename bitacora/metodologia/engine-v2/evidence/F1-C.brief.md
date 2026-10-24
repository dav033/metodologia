# Task F1-C — Planner prompt and planner skills for functional subplans

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Make the Planner role plan functional subplans with the new PLAN.json schema 1.3.0, the active Designer gate and
early audits — documentation/prompt work only.

Sources (read):
- Schema design: `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/SCHEMA-1.3.0.md` (the contract; other
  code implements it in parallel — write the prompts against this document, by field name and error code).
- Owner rulings: `.../engine-v2/CONTRACT.md` §2 (F1), §3 (Designer: gate is ACTIVE, preview optional per project,
  contract mandatory with UI work), §6.
- Master spec (Spanish): `.../engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` §7 (lines 179–357), §19.1 (lines
  1296–1330), §20.7 Planner addendum (lines 1947–1952).
- Current files: `skill/agents/planner.md`, `skill/agents/planner/skills/*/SKILL.md`,
  `skill/references/plan-contract.md` (read-only for you).

## You own
- `skill/agents/planner.md`
- `skill/agents/planner/skills/functional-subplan-decomposition/SKILL.md` (exists, extracted verbatim from master
  §19.1 — update it)
- `skill/agents/planner/skills/wbs-dag-decomposition/SKILL.md`, `adversarial-plan-review/SKILL.md`,
  `plan-mermaid-view/SKILL.md`
- `skill/agents/planner/skills/socratic-elicitation/SKILL.md` only if a one-line pointer is needed.

## Requirements
1. `functional-subplan-decomposition`: keep the master's procedure, but:
   - replace the "Contract compatibility" section: schema **1.3.0** has native optional `subplans`,
     `composition_gates`, task `subplan_id`/`ui`, kind `design`, verification `environment`/`requires`/
     `authorization_needed`; never write those into a 1.2.0 document; legacy plans stay valid; until the engine
     consumes 1.3.0 the adapter refuses approval (`PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE`) — say so, do not work around it;
   - the Designer gate is **active**: a subplan with UI work declares `ui {contract, version, design_task,
     visual_review_task}`; `design` task before every `ui: true` task; visual review (Reviewer axis `visual`) before
     the subplan audit; preview is a project setting, never a plan field;
   - name the validator rules it must satisfy (SUBPLAN_EDGE, LATE_CHECKPOINT ≤ 6 tasks between barriers,
     implementation deps after the producer audit, publication deps after a gate that excludes the consumer,
     composition gates for every cross-subplan consumption, UI_WORK_UNDECLARED, FILE_EXISTENCE_CHECK,
     EXTERNAL_ONLY_IMPLEMENT, secrets by name only) and how to fix each;
   - output: the subplan table plus the PLAN.json 1.3.0 fields; keep "planned tests are planned, not passing".
2. `planner.md`: add the mandatory subplan stage after the general plan and before tasks (master §7.2 sequence,
   §7.8 point 1), load rule for the fifth skill, the Designer interface (§7.5: the Planner plans the gate, never
   designs), rework/gate rules (§7.6), external verification classification (§7.7). Keep every existing rule,
   tool list and report contract; frontmatter unchanged except the description if it must mention subplans.
3. `wbs-dag-decomposition`: tasks inside a subplan get `subplan_id`; internal DAG per subplan; cross-subplan edges
   only to `defined_by`/audit/gate tasks with a declared `consumes`; legacy (no subplans) path preserved.
4. `adversarial-plan-review`: challenge fake independence, late audits (P-177: the first barrier for each likely
   defect), file-existence evidence, blanket rework of consumers, UI without Designer contract.
5. `plan-mermaid-view`: optional subplan view (subplans as clusters, contract/implementation/publication edges
   styled differently, gates); not mandatory.
6. Each SKILL.md keeps valid frontmatter (`name` = folder name, `description`). No PLAN.json examples that the
   1.3.0 design would reject.
7. A static test is NOT yours (another task writes tests over all skills); but make sure every path you reference
   exists in the repo or is explicitly marked as a project-repo convention (e.g. `design/contracts/...`).

## Verify
- `cd skill/scripts && python -m unittest tests.test_planner_runtime tests.test_planner_profile` (run them as the
  suite does if imports need it) and the full suite per RULES.md.
