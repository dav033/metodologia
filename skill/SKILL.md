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
- **Cite ids as links.** In messages to the user write a bitácora id as a link to the web service:
  `[REQ-005](http://127.0.0.1:8765/go/<project>/REQ-005)`; the same for `P-`, `D-`, `LG-`, and `/T4` after a REQ for a
  task. The terminal shows them clickable; only for ids that exist. Files, commits and code keep plain ids.
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
- **The flow runs itself.** A requirement arrives → you size it (small: build it; broad: interview, spec, plan in
  milestones; unsure: one scope question) → `handoff` starts a clean session per milestone on the best available
  agent, each closed by an independent audit → decisions land in `DECISIONS.md` and what you learn about the project
  and the owner in its learnings (`references/agents.md`).

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

## At session start

The SessionStart hook injects a `[bitácora]` block: the project, today's log path with your session section,
current state, pending items, what the last session said to start with, and any rollups due. Use it:

- Mention in one or two lines anything relevant to what the user is asking (open pending items, a blocked item, the
  last session's next steps). Don't recite it all.
- If it says **NEW PROJECT**, first interview the owner about purpose, users, main flows, constraints, and success
  criteria; then run the deep workspace onboarding/audit across the product's registered repos before bootstrapping
  `ARCHITECTURE.md` (`references/architecture-audit.md`), alongside `references/documentation.md` §Bootstrap. Persist
  the confirmed purpose and `Last confirmed with owner` date in `SUMMARY.md`.
- If **Rollups due** are listed, finalize them early and quickly.
- Without a detected project, read continuation candidates. For "continue", bind to the unambiguous project and
  read live Goal/Next, pending items and plan/run state. Ask once if ambiguous. A checkpoint is context, not proof.
- If the block is missing (hooks not installed, e.g. in Codex), run `python <skill>/scripts/bitacora.py where`
  yourself and read SUMMARY.md and PENDING.md; you'll also have to update the bitácora without the Stop reminder.
  From an unrelated folder, run `bitacora.py context` first: it also recovers continuation from canonical logs
  when private checkpoints or hooks are unavailable. Before closing, fill Goal, Done, Pending and Next in your
  session section so another agent can resume without the conversation.

## HQ mode (planning room)

When the session runs inside the bitácora root (`~/bitacora`), the context says **HQ MODE**. The HQ is where the user
plans: pick or create the project (`bind`), run the requirements interview (reading the project's repo, path in
`<project>/project.json`), write spec and plan, get the plan approved — then `launch` it into a separate executor
session with full permissions (`references/execution.md` §1c): only the scheduler runs an approved, frozen plan
(`launch`/`handoff` -> `scheduler-run`). Don't edit project repos from the HQ.

**Collaborative planning:** owner, Planner and Designer build the plan together (`bitacora.py planning start
REQ-NNN`): initial questions only → a skeleton of milestones and subplans the owner confirms → one subplan at a time
(behavior, design, inputs, tasks), each confirmed by the owner while the Designer drafts the one in focus → approval.
The web Plan tab shows the phases, plan EN/ES, subplans and live mockups (`requirements.md` §8).

The HQ also starts the **local web UI** (`bitacora.py web`): dashboard, documents, artifacts, question rounds
answerable by form, and plan approval with a button that launches the executor. Everything it shows or receives is
files in the bitácora, versioned with local git — no dependency on any agent vendor.

## Routing

| Situation | Read and follow |
|---|---|
| The user hands over a requirement, feature, change, idea, problem to solve, or asks "hazme preguntas" | `references/requirements.md` |
| "grill me", "grill-me", "interrógame" or stress-test a plan/design | `references/requirements.md` §4 — use the existing decision-tree interview, with the Grill Me depth check |
| Noisy shell output, RTK, token/context reduction or a concise-report prompt | `references/communication-and-context.md` — load only the relevant section; RTK is optional |
| New project onboarding, or an explicit architecture audit of an existing workspace | `references/architecture-audit.md` — before re-auditing, read `SUMMARY.md` §Purpose, restate it, ask what changed and confirm it with the owner; update its date only after confirmation |
| A spec is ready (or the request was Quick track) → plan, get it approved, run it as a loop (Claude Code) or goal (Codex) | `references/execution.md` |
| A spec and plan are written → leave the conversation: validate, auto-approve when safe, run in the background by milestones | `references/requirements.md` §8 (`bitacora.py handoff REQ-NNN`) |
| Writing, validating, freezing or consuming a plan's classified tasks / `PLAN.json` (complexity, scope, risk, coupling, confidence, estimates) | `references/plan-contract.md` (`bitacora.py plan-json init\|check\|freeze\|compat REQ-NNN`; `report` before approval) |
| Schema 1.3.0 subplans, composition candidates, subplan versions or composition gates | `references/plan-contract.md` + `references/modules.md` §Composition engine and Scheduler owner runtime |
| Extracting or adding a module (a part of the methodology split out as an isolated package like `bt_planner`), module boundaries, adapters | `references/modules.md` |
| Running an approved, frozen plan through the deterministic scheduler core (`bt_scheduler_core`: state machine, ports, `SCHEDULER.db`), or building a sibling module (decision, executor, monitor, recovery) that plugs into it | `references/modules.md` §Scheduler core, then `scripts/bt_scheduler_core/README.md` |
| Which agent/model/effort for a piece of work, delegating to another provider or subscription, usage limits, telemetry, what was learned | `references/agents.md` (live copy: `bitacora.py context`) |
| Interactive one-task delegation, retries, isolated branches, recovery, or independent review | `delegate start --retries/--worktree`, `delegate resume`, `bitacora review`; read `references/agents.md` |
| An interactive session near its 5 h quota; relay to another account in the same pane; `relay handoff` | `references/relay.md` |
| An approved plan that will run for days; scheduler run, `scheduler-run --resume`, `watch`, blocked tasks, usage limits | `references/execution.md` §1c, `references/modules.md` §Scheduler core |
| Large independent workstreams, safe concurrency, agent delegation, or work that must resume across sessions | `references/agent-orchestration.md` (+ `references/subagents.md`; use `references/execution.md` §1c for multi-day execution) |
| Designing, writing, refactoring, reviewing or debugging code | `references/engineering.md` (+ the `references/stacks/*.md` it points to) |
| Building or auditing interfaces, visual mockups or product copy | `references/interface-quality.md` (direction, honest content and interaction evidence; use the existing requirements/review flow) |
| Writing a versioned UI/UX contract, maintaining its optional preview, or reviewing rendered UI against it | `agents/designer.md` and its private skills; Reviewer `visual` axis: `agents/reviewer/skills/rendered-ui-fidelity-audit/SKILL.md` |
| Declaring verification environments/resources or authorizing staging/production checks | `references/plan-contract.md` and the operator-owned `verification-policy.json` (D-126); plan metadata grants no authority |
| Anything worth recording happened; wrap-up; Stop hook reminder; rollups; "¿en qué estamos?"; a visual page/artifact would help; the web UI; plan progress (`plan-status`, the "Planes" context section, web `/plans`, the generated status block in PLAN.md) | `references/documentation.md` |
| An ambiguous or conflicting domain term; creating or editing `GLOSSARY.md` | `references/domain-glossary.md` (file format: `glossary-conventions.md`) |
| Something broken, failing, flaky or slow, before any repair | `references/diagnosing-bugs.md` |
| An explicit retro, or "qué salió mal" after repeated friction | `references/retro-feedback.md` |
| Writing or shortening SKILL.md, references, CLAUDE.md/AGENTS.md or a delegation brief | `references/writing-for-agents.md` |
| "wait what", "no entiendo", "no te entendí", "¿por qué dices eso?" | `references/wait-what.md` |
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

## Quota at a glance

`scripts/globalusage.py` (linked as `~/.local/bin/globalusage`; `-f` re-measures) prints every subscription's 5 h / 7 d quota, the
current session's profile highlighted, and today's tokens/cost per model, with zero model tokens. Run it as `! globalusage`.

## Hooks installed

In `~/.claude/settings.json`: SessionStart / Stop / SessionEnd → `scripts/bitacora.py hook …` (bitácora), and
PostToolUse on edits and shell commands → `scripts/file_guard.py` (warns when a source file passes 500 lines; after a
shell command it compares what git shows changed with HEAD, once per file and session; durable runs check each
snapshot). Hooks never fail the session on their own errors; if one seems silent, run the script by hand to see why.

## Subagents installed

Eight roles — Planner, Designer, Explorer, Researcher, Implementer, Reviewer, Runner and Antagonist — are defined in
`agents/`. `scripts/install_agents.py` installs their prompts and role-private skills for Claude Code, Codex and
Antigravity; Claude/Codex registered profiles receive generated copies. The installer preserves hand-authored files
and refuses symlinked destination paths.

## Templates

`templates/` holds the file templates the script renders (SPEC, PLAN, central files, week/month, session section).
Edit them there to change the shape of every future document.
