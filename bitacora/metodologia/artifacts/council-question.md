# Council question

**¿Está bien diseñada la skill "metodologia"? ¿Qué le sobra, qué le falta, qué riesgos tiene y qué harías distinto?**

## Who uses it
A solo developer (works at Sempertex + personal projects), Windows 11, several computers, works mostly from the home
folder across many projects. Uses Claude Code (Opus) and Codex. Explicit preferences: maximum agent autonomy
("no quiero limitaciones", "no preguntar cada 5 minutos"), questions only up front, ONE approval gate (the plan),
everything documented, hates giant files, Spanish conversation, code in the repo's language.

## What was built (in one long session, ~1 day) — repo C:\Users\davidt\metodologia (private GitHub monorepo)
- **Always-on skill** (`skill/SKILL.md` ~110 lines, injected every session via CLAUDE.md @import; Codex via hook) +
  references loaded on demand (~1,050 lines total: requirements, execution, engineering + 4 stack guides,
  documentation, tools, subagents, codegraph).
- **Requirements flow**: explore first, prioritized rounds (≤5 questions, recommended answer each), coverage
  checklist, SPEC (EARS, user stories), PLAN, single human gate (plan approval), then autonomous execution.
- **HQ planning room** (~/bitacora): plan there, then `launch` opens a NEW Windows Terminal window with
  `claude --dangerously-skip-permissions` + `/loop` (or `codex --yolo` + `/goal`) and a HANDOFF.md.
- **Bitácora** per project (markdown): day logs per session, week/month rollups, DECISIONS (ADR-lite), PENDING,
  SUMMARY, ARCHITECTURE, TOOLS (servers/hosting access, no secrets), INDEX; local git + auto push/pull to GitHub.
- **Hooks**: SessionStart (context injection, pull), Stop (blocks stopping until the bitácora is updated if files
  changed), SessionEnd (cleanup + commit), PostToolUse (500-line file alert).
- **Local web UI** (Python stdlib server on 127.0.0.1, token-protected forms): dashboard, documents, question
  rounds as forms, plan approval button that launches the executor, Review tab (REPORT.md, per-repo diff,
  one-click merge of all repos), interactive trace graph (Cytoscape).
- **Trace graph** derived from IDs (REQ/US/R/T/D/P + commits citing them), lint for drift, context bundles.
- **Workspaces**: a project = several repos with roles, portable across machines (git remote + hint path).
- **5 subagent roles** (explorer/researcher/implementer/reviewer/runner) installed for Claude + Codex.
- **gitleaks** secret scanning (bitácora commits + pre-commit in project repos); optional CodeGraph MCP.
- **Evals**: 10 real `claude -p` cases in throwaway repos, 10/10 passing (~USD 1.5/run).
- Size: 20 Python scripts (~2,800 lines), web assets, templates; `install.py` sets up any machine.

## Evidence so far
- Already used live by the user's other sessions without supervision: 5 projects in the bitácora (one created
  REQ-004 with 13 requirements not yet covered by tasks — the graph flagged it).
- NEVER tested end to end: HQ → web rounds → approve button → executor window with /loop → REPORT → merge.
  Unverified: /loop as initial prompt, launching Windows Terminal from the background server, Codex /goal.
- Bugs found during the build: several self-inflicted breakages of the live hooks (escaping errors), hooks failing
  under PowerShell for ~20 min, a test commit accidentally made in a real repo (reverted, never pushed),
  console windows flashing. All fixed.

## Deliberate decisions
- No guard hook against destructive commands (user rejected limits); executor runs with permissions bypassed;
  safety = prose rules ("stop and ask for push/deploy/destroying data/credentials") + secret scanning.
- One private monorepo with skill + all project docs (incl. employer projects) on the personal GitHub account.
- Replaced the user's previous tool "hefesto" entirely.
- Documented for later: executor status/notifications/resume, concurrent edits to central files, pruning.

## What's at stake
This is meant to be the user's daily way of working for every project (personal and employer), with agents
running autonomously with full permissions on his machine and servers. A bad design costs time every day, can
lose work or leak data, and an over-engineered one may simply stop being used.

Files you may skim if useful (keep it brief): C:\Users\davidt\metodologia\README.md,
C:\Users\davidt\metodologia\skill\SKILL.md, C:\Users\davidt\metodologia\skill\references\execution.md
