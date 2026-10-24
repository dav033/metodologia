STATUS: DONE
SUMMARY: Updated the Designer flow across requirements, execution guidance, templates, references, and agent prompts. Documented owner approval for each contract version and Runner’s screenshot evidence handoff to Reviewer `visual`. No Python files were changed; the worktree is clean.
CHANGES:
- `skill/references/requirements.md` — UI detection, recommended visual direction, approval gate, and handoff pause.
- `skill/references/interface-quality.md` — resolved the gate contradiction; defined guidance for Designer and Reviewer.
- `skill/references/execution.md` — UI task sequence, waiting state, missing-contract reason, and visual evidence flow.
- `skill/references/agent-orchestration.md` — Designer scope, approval dependency, and evidence responsibilities.
- `skill/references/agents.md` — Designer routing and model choices.
- `skill/references/subagents.md` — design-task brief example and implementer contract requirement.
- `skill/references/documentation.md` — contract storage, version history, approval, and preview.
- `skill/references/engineering.md` — UI contract conformance and visual-review completion checks.
- `skill/references/architecture-audit.md` — added UI contracts to the audit inventory.
- `skill/references/tools.md` — optional preview documentation guidance.
- `skill/templates/SPEC.md` — UI / design contract section and coverage item.
- `skill/templates/PLAN.md` — design, UI implementation, and visual-review task examples.
- `skill/agents/runner.md` — routed screenshot evidence capture to a private skill.
- `skill/agents/runner/skills/visual-evidence-capture/SKILL.md` — breakpoint × state capture instructions; Runner reports evidence and does not judge.
- `skill/agents/explorer.md` — UI contract and preview discovery guidance.
- `skill/agents/antagonist.md` — contract-drift review guidance.
- `skill/agents/researcher.md` — research guidance that preserves approved design direction.
- `skill/agents/reviewer.md` — consumes Runner screenshot evidence and reports coverage gaps.
- `skill/SKILL.md` — concise note distinguishing plan approval from contract approval.
VERIFICATION:
- `PYTHONPATH=skill/scripts/tests:skill/scripts python -m unittest test_agent_skills_static` → exit 0 (9 tests).
- `git diff --check` → exit 0.
- `python -m unittest discover -s tests` → exit 1 (1335.7s; 2,534 tests, 18 failures, 6 skipped). Fifteen failures match the baseline in RULES.md; three `test_recovery_benchmark` failures occurred with 3.9 GiB free on `/home` (below the documented 5 GiB requirement).
COMMITS: f57b92fde docs(designer): document UI contract approval and visual evidence
PROVENANCE: none
CONCERNS: Full suite remains non-green due to documented baseline failures and the low-disk benchmark condition. No additional failures were reported.