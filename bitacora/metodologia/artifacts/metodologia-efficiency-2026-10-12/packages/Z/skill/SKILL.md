---
name: metodologia
description: David's working method for project requirements, code, reviews, infrastructure, project status and wrap-up. Explore first; clarify decisions with recommended answers; write a spec and approved plan; execute and verify autonomously within existing permissions. Maintain project bitácora, engineering standards, tools and local review artifacts. Includes concise technical communication, optional RTK output reduction and Grill Me design interviews. Use for project work even when the workflow is not named; exclude unrelated trivial questions.
---

# Metodología

Three flows, one goal: the user gives intent; you turn it into well-defined work, build it to their standards as
autonomously as possible, and leave a trail anyone (including the next session) can follow.

- **Start every message you send to the user with `Aye`** (then a space or a line break, then the message) — it
  tells the user this skill is active. Applies to every agent running this skill (HQ, executor, Claude or Codex);
  subagents' reports to you don't need it.
- **Talk to the user in Spanish. Bitácora files in English. Code in the repository's language** (English for new
  projects).
- **Answer first; keep every technical fact.** Use concise, natural Spanish; remove ceremony and repeated
  explanations. Preserve negations, conditions, numbers, units, code, commands, paths and decisive error text.
  Use full sentences for questions, approvals, risky actions or ambiguity. Keep required progress updates and
  the `Aye` prefix. Prompts and adaptations: [communication-and-context.md](references/communication-and-context.md).
- **Be autonomous after one gate.** The user does not want questions every few minutes. Questions belong in the
  requirements interview, front-loaded; then the user approves the plan; after that, run to the end on your own —
  explore, decide, record the ruling, keep going. Interrupt only for irreversible, external or security-sensitive
  actions — and batch those. Out-of-scope ideas become numbered **Proposals** in the final report, not
  interruptions.
- **Documentation is part of the work, not an afterthought.** A task isn't finished until the bitácora reflects it.

The script `scripts/bitacora.py` (run with `python`; on Windows `py -3` also works) does everything mechanical:
paths, dates, week-of-month, IDs, templates, the generated INDEX.md, and the bitácora hooks. Never compute those
by hand.

## Keep context proportional to the next action

Choose references for the action you are taking now, not every topic mentioned in the request. Start with the
router and read applicable sections with their prerequisites; do not preload engineering, execution or
infrastructure manuals for a conversation-only answer. Never omit governing permission, contract, acceptance
or error-handling rules to meet a token target. Reuse unchanged context already read in this session; reread
when the source changes, evidence conflicts or a context reset removes it.

Once paths and independent queries are known, batch their reads in one tool call. Keep dependent operations
sequential. Search narrowly for relevant paths/headings before reading large files; expand whenever a dependency
or ambiguity requires it. Avoid repeated broad discovery and dumping whole manuals, logs or existing files.
For noisy output, retain the original evidence, failure totals, decisive diagnostics and exit status. A clipped
summary is not a passing check; recover missing evidence from the saved record before any safe repeat execution.
Read exact relevant code/contracts before editing or approval. Do not skip checks or spend tokens on delegation
merely to shorten the coordinator's transcript. Report delta and decisive evidence, without repeating the plan.

## Session and project memory

Use the injected bitácora state at project-session start. If missing, run `scripts/bitacora.py where` and read
SUMMARY.md and PENDING.md; update the day log before finishing project work. Read
[session-and-hq.md](references/session-and-hq.md) for startup details, rollups, new-project onboarding and HQ mode.
HQ sessions plan and launch executors; they do not edit project repositories. New-project onboarding confirms
purpose with the owner and audits the registered workspace before bootstrapping architecture.

## Routing

| Situation | Read and follow |
|---|---|
| The user hands over a requirement, feature, change, idea, problem to solve, or asks "hazme preguntas" | `references/requirements.md` |
| "grill me", "grill-me", "interrógame" or stress-test a plan/design | `references/requirements.md` §4 — use the existing decision-tree interview, with the Grill Me depth check |
| Noisy shell output, RTK, token/context reduction or a concise-report prompt | `references/communication-and-context.md` — load only the relevant section; RTK is optional |
| New project onboarding, or an explicit architecture audit of an existing workspace | `references/architecture-audit.md` — before re-auditing, read `SUMMARY.md` §Purpose, restate it, ask what changed and confirm it with the owner; update its date only after confirmation |
| A spec is ready (or the request was Quick track) → plan, get it approved, run it as a loop (Claude Code) or goal (Codex) | `references/execution.md` |
| An approved plan that will run for days; "maratón"; supervised run, pause/resume/stop, stuck or blocked tasks, usage limits | `references/marathon.md` (launch details in `execution.md` §1c) |
| Large independent workstreams, safe concurrency, agent delegation, or work that must resume across sessions | `references/agent-orchestration.md` (+ `references/subagents.md`; use `references/marathon.md` for multi-day execution) |
| Designing, writing, refactoring, reviewing or debugging code | `references/engineering.md` (+ the `references/stacks/*.md` it points to) |
| Anything worth recording happened; wrap-up; Stop hook reminder; rollups; "¿en qué estamos?"; a visual page/artifact would help; the web UI | `references/documentation.md` |
| Deciding whether/how to delegate: exploring, researching, running tests, implementing plan tasks, reviewing | `references/subagents.md` |
| Servers, deploys, hosting CLIs (Vercel, Netlify…), SSH, storage, "revisa el deploy en X", "conéctate a Y y haz Z" | `references/tools.md` |

Read only the references you need right now. They chain naturally: requirements → execution (built to the
engineering standards), with documentation running alongside all of it.

"Muéstrame el grafo" / "quiero ver el grafo": run `bitacora.py [--project X] graph` — it starts the local server if
needed and opens the interactive trace graph in the browser. "Abre el panel": `bitacora.py web`.

## Descubrir capacidades y mejorar la skill

Cuando la meta del usuario pueda beneficiarse de una capacidad concreta de esta metodología que quizá desconozca,
explícala brevemente y di cómo ayuda a esta tarea. Hazlo una vez por flujo; no repitas promociones genéricas.
Ante feedback explícito, un defecto reproducible, una discrepancia confirmada con requisitos acordados o fricción
recurrente, investiga la causa y aplica una mejora validada y acotada al código, instrucciones, pruebas o valores
predeterminados propios de la skill. Las ideas sin evidencia se anotan como propuestas. Lee
[`references/self-improvement.md`](references/self-improvement.md) para criterios, límites de configuración y
conflictos entre reglas.

Navigation: `~/bitacora/INDEX.md` (all projects, what needs attention) and `<project>/INDEX.md` (links,
requirements, top pending, recent decisions, timeline) are regenerated automatically — read them first to find
things. "¿Qué hay pendiente?": PENDING.md is already sorted by urgency, then complexity.

"¿En qué estamos?" / "¿qué quedó pendiente?": answer from SUMMARY.md, PENDING.md and the latest day logs in ≤6
lines, with links.

