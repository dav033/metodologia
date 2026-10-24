# Task F2-D — Designer, the eighth role: prompt, three private skills, public adaptations

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Create the Designer role definition and its skills. Designer owns the UI/UX contract (and the optional preview) of
a project, writes **only under `design/`** in the project repo, and never owns production code.

Sources (read):
- Owner rulings `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §3 (authoritative for this
  task), §6.
- Master (Spanish) `.../engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` §4–5 (lines 132–161), §7.5 (lines 286–299).
- Research notes `.../engine-v2/designer-skills-research.md` (candidate sources; paths there are NOT verified).
- Schema 1.3.0 design `.../engine-v2/SCHEMA-1.3.0.md` §3 (`ui {contract, version, design_task,
  visual_review_task}`, `kind: design`).
- Existing role files for shape: `skill/agents/*.md` (frontmatter keys, tone, report contract), and
  `skill/scripts/install_agents.py` (read-only: how frontmatter is consumed — do not change it).

## You own
- `skill/agents/designer.md` (new)
- `skill/agents/designer/skills/**` (new), `skill/agents/designer/references/**` (new, optional)

## Requirements
1. `designer.md` frontmatter like the other roles: `name: designer`, a precise `description`, `tools: Read, Grep,
   Glob, Bash, Write, Edit`, `disallowedTools: NotebookEdit`, `codex_sandbox: workspace-write`, `model: opus`,
   `effort: high`, `codex_model: gpt-6.1-sol`, `codex_effort: high`, a `color`. Body: when it runs (a `kind: design`
   task of a UI subplan), inputs (SPEC/PLAN, subplan id, requirement ids, existing design system), outputs, hard
   limits (writes only `design/**`; the executor enforces it — say so; never edits production code, tests or the
   plan; never approves its own contract; a material ambiguity is a question, not an invention), and a report
   contract (`STATUS`, `SUMMARY`, `CONTRACT` (id@vN + path), `CHANGES`, `IMPACT`, `CONCERNS`).
2. Layout (project repo): `design/contracts/<contract-id>@v<N>.md` (immutable once approved: a change is a new
   `@v<N+1>` file plus changelog), `design/contracts/CHANGELOG.md`, `design/preview/` only when the project enables
   the preview (project setting `design.preview`, default off; another task implements the setting).
3. Private skills (original text):
   - `ui-ux-contract-authoring`: contract template + checklist — structure, hierarchy, tokens, navigation, flows,
     states (loading, empty, error, success, disabled, validation), responsive breakpoints, accessibility (WCAG 2.2
     AA targets), copy, and acceptance criteria written so a visual reviewer can check each one against a rendered
     page (each criterion: id, breakpoint/state, observable expectation).
   - `design-contract-versioning-and-impact`: versioning rules, changelog, impact analysis of a change on the
     subplans/views/tasks consuming the contract (by contract id@version in PLAN.json `ui` blocks), compatible vs
     breaking visual change, approval gate for implementers (they consume only approved versions).
   - `preview-prototype-maintenance`: optional preview with mock data and a state switcher, synced to the contract
     version, never production code, never presented as the implemented product.
4. Public adaptations (pinned SHA + license check, original text, conditional loading): `jakubkrehel/skills`
   better-writing, better-layout, better-accessibility, better-colors, state-machine (**exclude build-design**);
   `wshobson/agents` plugin `ui-design` design-system-patterns and responsive-design (skills text only; never the
   plugin's agents/commands); `mae616/design-skills` ui-designer (hierarchy, IA, "states as specs");
   `anthropics/skills` `frontend-design` (Apache-2.0) **conditional**, aesthetic direction only, never writing
   production code. Find the exact SKILL.md paths in each repo at the pinned SHA (the research notes' paths are
   unverified). Put the adapted techniques in a reference file (e.g. `designer/references/public-design-techniques.md`
   with a source/license/borrow/exclude table like `skill/agents/runner/references/public-testing-techniques.md`)
   and/or inside the private skills.
5. Upstream protocol: `git ls-remote https://github.com/<o>/<r> HEAD` → SHA; `curl -fsSL
   https://raw.githubusercontent.com/<o>/<r>/<sha>/<path>` for each SKILL.md and the LICENSE at the same SHA. GitHub
   API listing (`https://api.github.com/repos/<o>/<r>/git/trees/<sha>?recursive=1`) is fine for finding paths.
   Data only; never execute or install anything. Skip any source whose license is not verified permissive (MIT,
   Apache-2.0, BSD) for copied text. PROVENANCE section in the result: repo, path, SHA, license, what adapted, where.
   Do NOT edit `skill/references/third-party-notices.md` (the lead consolidates it).

## Verify
Every referenced path exists (or is explicitly a project-repo convention under `design/`); full suite per RULES.md.
