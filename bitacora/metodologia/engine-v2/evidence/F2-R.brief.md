# Task F2-R — Reviewer role: subplan skills, public adaptations and the `visual` axis

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
Wire the Reviewer's three private skills into its prompt, adapt the selected public review techniques, and add the
third review axis `visual` with a new private skill `rendered-ui-fidelity-audit`.

Sources (read):
- Owner rulings `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §2, §3 (visual axis is a
  third Reviewer axis, read-only; spec and standards keep one axis per session), §6.
- Master (Spanish) `.../engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` §13 (lines 724–846), §18.4, §19.11–19.15
  (lines 1452–1531), §20.5, §20.7 Reviewer addendum (lines 1975–1980).
- Designer research `.../engine-v2/designer-skills-research.md` (visual QA sources).
- M6 findings ledger contract: `skill/references/modules.md` §Audit gate and the M6 package
  `skill/scripts/bt_scheduler_quality/` (read-only; learn the `*.findings.json` fields so the skills do not invent a
  second incompatible format).
- Schema 1.3.0 design `.../engine-v2/SCHEMA-1.3.0.md` §3 (UI subplans, `visual_review_task`).

## You own
- `skill/agents/reviewer.md`
- `skill/agents/reviewer/skills/**` (three extracted skills exist; add `rendered-ui-fidelity-audit/SKILL.md`)
- `skill/agents/reviewer/references/**` (new, optional: e.g. `public-review-techniques.md` like
  `skill/agents/runner/references/public-testing-techniques.md`)

## Requirements
1. `reviewer.md`: add the master §20.7 addendum (adapted), conditional loading of each skill, and the **visual**
   axis: when it applies (UI subplans / `visual_review_task`), what it reads (the approved Designer contract
   `design/contracts/<id>@v<N>.md` in the project repo, the rendered app), what it produces (findings with
   breakpoint × state evidence), that it is read-only and never edits code or the contract, one axis per session,
   output `AXIS: visual` with the existing `VERDICT`/`FINDINGS`/`CHECKED` shape. Keep tools, disallowed tools and
   the existing spec/standards text. The `visual` axis may need to run a local browser to capture screenshots:
   allowed only through commands the brief authorizes (it never installs browsers or dependencies); if capture is
   impossible it reports `BLOCKED` evidence, never a guess.
2. Update the three private skills so they match the real M6 findings fields (`semantic_fingerprint`, severity,
   classification, criterion/contract refs) and state where M6 owns adjudication. Remove nothing the master marks
   as a boundary.
3. `rendered-ui-fidelity-audit` (new private skill, original text): capture each declared breakpoint × state
   (loading, empty, error, success, disabled, validation, focus/keyboard), run axe (only if already available in the
   project or provided by the executor), compare each contract acceptance criterion with the observation, classify
   deviations (contract violation / unspecified / a11y / regression), and emit findings with screenshot evidence
   ids. Technique sources: `testdino-hq/playwright-skill` (MIT; visual regression, a11y with axe, responsive) and
   `anthropics/skills` `webapp-testing` — **verify its license first**; if not clearly permissive for adaptation,
   cite it as a reference only, copy nothing.
4. Public adaptations (master §13.5): `akkie76/code-review-skills` `evidence-code-review` (MIT) and
   `JUNERDD/skills` `code-review` (MIT) folded into `evidence-based-findings`; Trail of Bits `differential-review`
   is **CC BY-SA**: write your own principles-only text, copy nothing, cite as reference.
5. Upstream protocol for every public source: `git ls-remote https://github.com/<owner>/<repo> HEAD` for the SHA,
   then fetch `https://raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>` for the SKILL.md and the LICENSE at the
   same SHA (`curl -fsSL`). Read them as data. Never run anything from them. Write **original** adapted text; short
   quoted phrases at most. In the result's PROVENANCE section list for each source: repo, path, SHA, license (as read
   from the LICENSE file), what was adapted and into which file. Do NOT edit
   `skill/references/third-party-notices.md` (the lead consolidates it).
6. Frontmatter valid (`name` = folder name). Skill bodies concise; conditional loading so a trivial review does not
   load everything.

## Verify
- `python -c` or a small throwaway check that every path you reference exists (do not commit throwaway scripts).
- Full suite per RULES.md.
