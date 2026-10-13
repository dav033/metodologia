# Session startup, HQ and installed helpers

Read for actual project-session startup or HQ operation. General language, permission and routing rules remain
in SKILL.md. Conversation-only evaluations with explicit no-tools/no-files scope do not create project sessions.

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
- If no project was detected and the session becomes project work, ask which project and `bind` it.
- If the block is missing (hooks not installed, e.g. in Codex), run `python <skill>/scripts/bitacora.py where`
  yourself and read SUMMARY.md and PENDING.md; you'll also have to update the bitácora without the Stop reminder.

## HQ mode (planning room)

When the session runs inside the bitácora root (`~/bitacora`), the context says **HQ MODE**. The HQ is where the user
plans: pick or create the project (`bind`), run the requirements interview (reading the project's repo, path in
`<project>/project.json`), write spec and plan, get the plan approved — then `launch` it into a separate executor
session with full permissions (`references/execution.md` §1c) — **marathon mode** (a supervisor running one fresh
session per task, for multi-day plans) is the default. Don't edit project repos from the HQ.

The HQ also starts the **local web UI** (`bitacora.py web`): dashboard, documents, artifacts, question rounds
answerable by form, and plan approval with a button that launches the executor. Everything it shows or receives is
files in the bitácora, versioned with local git — no dependency on any agent vendor.

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
