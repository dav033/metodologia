---
name: plan-mermaid-view
description: Produces an optional Mermaid dependency diagram from a valid PLAN.json when a human would benefit from seeing the plan topology.
---

# Mermaid plan view

Use this only when the plan has enough milestones or dependency edges that a picture improves review.

- Treat validated `PLAN.json` as the only source of truth. Render milestone groups and task nodes; draw an arrow from each predecessor named in `after` to its dependent task.
- For schema 1.3.0 plans with subplans, optionally render subplans as clusters inside their milestone, composition gates as explicit gate nodes, and subplan-to-subplan contract, implementation and publication relationships from `consumes` with distinct edge styles. Render task-level arrows only for `after` edges actually present; never infer task edges from `consumes`. A plan with no subplans keeps the ordinary milestone/task view.
- Task `covers`, `subplan_id`, `ui`, `kind`, declared `interfaces`, verification `category` and composition-gate criteria may be shown as labels when useful; do not turn labels into extra dependencies.
- Use a Mermaid `flowchart` for the graph. Do not make a Gantt chart: the plan contract contains estimates, not approved start dates or calendar scheduling. Do not invent dates, parallel execution guarantees, architecture structure, or additional tasks.
- Do not annotate provider/service, account, model, effort, worker count or quota assignments; the Planner does not choose them.
- Save the diagram as a separate, explicitly derived `.mmd` artifact only when requested or useful for review. Never add diagram fields to `PLAN.json` or make the diagram a second source of truth.
- Check that each displayed task ID and edge maps to the plan, and label the diagram as a projection. If diagram syntax was not rendered or parsed, say so.
