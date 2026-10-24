# Task DZ-docs — Designer in every doc, template and agent prompt

Read first, binding: `/home/david/dev/.designer-wt/RULES.md`, then `CONTEXT.md` and `INVENTORY.md` in that directory.
Worktree branch `dz/DZ-docs` from origin/main. Docs/prompts/templates only — no Python.
You own: `skill/references/{requirements,interface-quality,execution,agent-orchestration,agents,subagents,documentation,
engineering,architecture-audit,tools}.md`, `skill/templates/SPEC.md`, `skill/templates/PLAN.md` (and any other
template that renders a spec/plan), `skill/agents/{runner,explorer,antagonist,researcher,planner,reviewer}.md` (only
the Designer-related lines), `skill/agents/runner/**` if a private skill is the right home for visual capture,
`skill/SKILL.md` (only the HQ / plan-approval wording and, if needed, one routing row). Two other tasks run in parallel:
DZ-code (kinds/telemetry/prompts in Python) and DZ-approval (approval CLI/web/gate, modules.md, plan-contract.md,
the `design` CLI docs). Do NOT edit `skill/references/modules.md`, `plan-contract.md` or any `.py`.

Write truthfully for the behaviour CONTEXT.md describes (D-127), cross-referencing where the approval is done
(`bitacora.py design approve|changes REQ-NNN <contract>@vN` or the web requirement page), every item in INVENTORY.md
Docs and Prompts. Specifically:
- requirements.md: UI detection + visual direction in the interview (front-loaded, with a recommended answer), the
  spec's "UI / design contract" section, the plan's design task + owner contract approval + visual review, and §8
  handoff/launch notes (a UI plan will pause for the owner's contract approval during the run).
- interface-quality.md: remove the contradiction; it is the guidance Designer authors with and Reviewer `visual` judges.
- Runner: it captures screenshots per breakpoint × state through the project's existing browser/preview tooling
  (agent Firefox via BiDi per the user's setup, or Playwright if the project has it), returns evidence ids/paths, never
  judges; Reviewer `visual` consumes them. Keep each prompt concise and consistent with its existing style.
- agents.md table row for designer (Claude Opus high; Codex gpt-6.1-sol high), subagents.md design-task brief example.
Keep SKILL.md concise. Run `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_agent_skills_static`
and any doc-consistency tests that touch the files you edit; the full root suite once at the end.
