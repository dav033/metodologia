---
name: plan-mermaid-view
description: Produces an optional Mermaid dependency diagram from a valid PLAN.json when a human would benefit from seeing the plan topology.
---

# Mermaid plan view

Use this only when the plan has enough milestones or dependency edges that a picture improves review.

- Treat validated `PLAN.json` as the only source of truth. Render milestone groups and task nodes; draw an arrow from each predecessor named in `after` to its dependent task.
- Use a Mermaid `flowchart` for the graph. Do not make a Gantt chart: the plan contract contains estimates, not approved start dates or calendar scheduling. Do not invent dates, parallel execution guarantees, architecture structure, or additional tasks.
- Save the diagram as a separate, explicitly derived `.mmd` artifact only when requested or useful for review. Never add diagram fields to `PLAN.json` or make the diagram a second source of truth.
- Check that each displayed task ID and edge maps to the plan, and label the diagram as a projection. If diagram syntax was not rendered or parsed, say so.
