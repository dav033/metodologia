---
req: REQ-001
status: done
created: 2026-10-12
---
# Plan — Nontechnical agent workbench

## Approach
Create an instruction-first coordinator named agentes-de-trabajo, with plain Spanish interaction and focused references for agent discovery, memory/improvement and GitHub persistence and proactive connection setup. Task agents are reusable skills plus scoped memory in the same repository. Use templates instead of building a runtime. Storage and autonomy: D-001.

## Global constraints
Respect existing files and owner approval boundaries. Work capabilities must be discovered, not assumed. No commits, remote creation, push, installation or global configuration edits without explicit authorization. Use fictional invoice data.

## Planned package
Provisional root: /home/david/dev/agentes-de-trabajo.
- skills/agentes-de-trabajo/: SKILL.md, UI metadata, focused references and agent templates.
- agents/INDEX.md: registry of active agents; generated agents get their own definition, procedure, context, decisions, pending work and history.
- examples/invoice-drafts/: clearly marked synthetic example, outside the active registry.
- README.md: GitHub packaging, short Work setup and use instructions, with actual capability limitations.
- evaluations/: representative requests, expected behavior and actual results.
No application framework, new dependencies or speculative scripts.

## Tasks
- [x] T1 — Write coordinator, discovery flow and agent templates with readiness/pause states · files: skills/agentes-de-trabajo/, agents/INDEX.md · verify: creation and selection scenarios · covers: R1, R2, R3, R7, US-1, US-2
- [x] T2 — Add scoped memory, approval, history and restoration guidance · after: T1 · files: skill references and templates · verify: correction, exception, conflict and permission scenarios · covers: R4, R5, R8, R9, US-3
- [x] T3 — Document one-repository persistence and Work setup; add synthetic invoice example · after: T2 · files: README.md, examples/, persistence and connections references, connections/INDEX.md · verify: read-only, uncertain-write and competing-edit scenarios · covers: R6, R8, R10, US-4
- [x] T4 — Validate structure/references, independently exercise behavior, fix evidenced defects and record limitations · after: T3 · files: evaluations/, REPORT.md, bitacora · verify: quick_validate.py, isolated scenarios and trace check · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, US-1, US-2, US-3, US-4

## Verification
Run python /home/david/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/david/dev/agentes-de-trabajo/skills/agentes-de-trabajo. Check relative references and unfinished scaffolds. Independently exercise creation, fresh-session correction recall, one-off exception, permission expansion, missing write access, uncertain save, concurrent changes, malicious document instructions, pause and scoped restoration in isolated files with no external writes. Review spec and standards independently. Run bitacora trace. Real installation and GitHub writes remain explicitly unexecuted until available in the target account.

## Rulings
- Provisional name and instruction-only format make v1 focused and easy to revise.
- One repository per owner/team: repository readers can read every agent's tracked memory.
- Review through the plan file/chat; do not start a local web server without the explicit confirmation required by the owner's global instructions.

## Progress log
- 2026-10-12: Owner chose Work, one repo and bounded learning. Specification and plan prepared; awaiting approval of this concrete plan. No skill implementation or remote publication yet.
- 2026-10-12 11:55 review comments (chat): Owner approved and added proactive MCP/connection setup and remembered capability state.
- 2026-10-12 11:55 plan APPROVED (chat)

- 2026-10-12: Owner approved plan and R10 connection management extension. Proceed locally; no live account setup or remote publication requested.

- 2026-10-12: T1–T3 authored locally; coordinator, references, three blueprints, registries, README and synthetic invoice example complete. Format validators passed using isolated uv/PyYAML; structural check passed (30 local links, YAML/UI metadata, arithmetic). Spec review APPROVE; behavior and standards reviews running before T4 completion.

- 2026-10-12: T1–T4 complete locally. Format validators passed twice; final checks passed for 39 links, metadata/JSON/whitespace and evaluator artifacts. Independent spec/standards reviews approved. Follow-up partial-readback and foreign-grant scenarios resolved the evidenced ambiguities. Deployment/live connections/GitHub publication remain explicitly deferred. No commit or remote mutation.

- 2026-10-12: Owner separately authorized a public repo and initial upload after implementation/review. T5 published dav033/agentes-de-trabajo on feat/agent-workbench; GitHub public setting, branch/commit SHA and main SKILL.md blob SHA match local evidence. This one-time package publication does not authorize future workspace memory writes.
