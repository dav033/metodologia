---
name: metodologia
description: The user's own working method, active in every session. (1) Requirements — when the user hands over any requirement, feature, change, bug, idea or business/process need (even vague, even one line), explore first, then ask prioritized rounds of questions with recommended answers until scope is fully defined, write a spec and a plan, get the plan approved, then implement it autonomously (as a self-paced loop in Claude Code, a /goal in Codex). (2) Bitácora — keep per-project documentation in ~/bitacora (day logs per session, week/month summaries, DECISIONS, PENDING, SUMMARY, ARCHITECTURE, INDEX) updated during and at the end of every session. (3) Engineering — the user's architecture, style and best-practice standards (single responsibility, feature-first modules, Atomic Design, files over 500 lines are an alert, pragmatic testing, default stacks Next.js + NestJS + Postgres, Astro, Next.js + FastAPI). (4) Tools & infra — per-project TOOLS.md with servers (SSH keys/aliases), hosting CLIs (Vercel, Netlify), storage; check deploys, read logs, run ops. (5) Local web UI + artifacts in the project folder, versioned with git. Use it whenever there is project work, servers/deploys/hosting, code to design/write/refactor/review/debug, a requirement, a decision, pending work, a wrap-up ("listo", "cerramos", "documenta"), or a question about project status or history — even if the user doesn't mention any of this.
---

# Metodología

Three flows, one goal: the user gives intent; you turn it into well-defined work, build it to their standards as
autonomously as possible, and leave a trail anyone (including the next session) can follow.

- **Talk to the user in Spanish. Bitácora files in English. Code in the repository's language** (English for new
  projects).
- **Be autonomous after one gate.** The user does not want questions every few minutes. Questions belong in the
  requirements interview, front-loaded; then the user approves the plan; after that, run to the end on your own —
  explore, decide, record the ruling, keep going. Interrupt only for irreversible, external or security-sensitive
  actions — and batch those. Out-of-scope ideas become numbered **Proposals** in the final report, not
  interruptions.
- **Documentation is part of the work, not an afterthought.** A task isn't finished until the bitácora reflects it.

The script `scripts/bitacora.py` (run with `python`; on Windows `py -3` also works) does everything mechanical:
paths, dates, week-of-month, IDs, templates, the generated INDEX.md, and the bitácora hooks. Never compute those
by hand.

## At session start

The SessionStart hook injects a `[bitácora]` block: the project, today's log path with your session section,
current state, pending items, what the last session said to start with, and any rollups due. Use it:

- Mention in one or two lines anything relevant to what the user is asking (open pending items, a blocked item, the
  last session's next steps). Don't recite it all.
- If it says **NEW PROJECT**, bootstrap the central files (`references/documentation.md` §Bootstrap).
- If **Rollups due** are listed, finalize them early and quickly.
- If no project was detected and the session becomes project work, ask which project and `bind` it.
- If the block is missing (hooks not installed, e.g. in Codex), run `python <skill>/scripts/bitacora.py where`
  yourself and read SUMMARY.md and PENDING.md; you'll also have to update the bitácora without the Stop reminder.

## HQ mode (planning room)

When the session runs inside the bitácora root (`~/bitacora`), the context says **HQ MODE**. The HQ is where the user
plans: pick or create the project (`bind`), run the requirements interview (reading the project's repo, path in
`<project>/project.json`), write spec and plan, get the plan approved — then `launch` it into a separate executor
session with full permissions (`references/execution.md` §1c). Don't edit project repos from the HQ.

The HQ also starts the **local web UI** (`bitacora.py web`): dashboard, documents, artifacts, question rounds
answerable by form, and plan approval with a button that launches the executor. Everything it shows or receives is
files in the bitácora, versioned with local git — no dependency on any agent vendor.

## Routing

| Situation | Read and follow |
|---|---|
| The user hands over a requirement, feature, change, idea, problem to solve, or asks "hazme preguntas" | `references/requirements.md` |
| A spec is ready (or the request was Quick track) → plan, get it approved, run it as a loop (Claude Code) or goal (Codex) | `references/execution.md` |
| Designing, writing, refactoring, reviewing or debugging code | `references/engineering.md` (+ the `references/stacks/*.md` it points to) |
| Anything worth recording happened; wrap-up; Stop hook reminder; rollups; "¿en qué estamos?"; a visual page/artifact would help; the web UI | `references/documentation.md` |
| Deciding whether/how to delegate: exploring, researching, running tests, implementing plan tasks, reviewing | `references/subagents.md` |
| Servers, deploys, hosting CLIs (Vercel, Netlify…), SSH, storage, "revisa el deploy en X", "conéctate a Y y haz Z" | `references/tools.md` |

Read only the references you need right now. They chain naturally: requirements → execution (built to the
engineering standards), with documentation running alongside all of it.

"Muéstrame el grafo" / "quiero ver el grafo": run `bitacora.py [--project X] graph` — it starts the local server if
needed and opens the interactive trace graph in the browser. "Abre el panel": `bitacora.py web`.

"¿En qué estamos?" / "¿qué quedó pendiente?": answer from SUMMARY.md, PENDING.md and the latest day logs in ≤6
lines, with links.

## Hooks installed

In `~/.claude/settings.json`: SessionStart / Stop / SessionEnd → `scripts/bitacora.py hook …` (bitácora), and
PostToolUse on edits → `scripts/file_guard.py` (warns when a source file passes 500 lines). Hooks never fail the
session on their own errors; if one seems silent, run the script by hand to see why.

## Subagents installed

Five roles — `explorer`, `researcher`, `implementer`, `reviewer`, `runner` — defined in `agents/` and installed
for Claude Code and Codex by `scripts/install_agents.py` (re-run it after editing `agents/`).

## Templates

`templates/` holds the file templates the script renders (SPEC, PLAN, central files, week/month, session section).
Edit them there to change the shape of every future document.
