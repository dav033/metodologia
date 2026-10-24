# Task F2-C — Implementer role: Ponytail/Caveman adaptations and three approved private skills

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding).

## Goal
The Implementer writes the smallest complete change against approved contracts, reports compactly without losing
data, and loads its three private skills by task.

Sources (read):
- Owner rulings `/home/david/dev/metodologia/bitacora/metodologia/engine-v2/CONTRACT.md` §2 (the 3 Implementer
  drafts are APPROVED by the owner), §6 (exclusions stand).
- Master (Spanish) `.../engine-v2/METODOLOGIA_AGENTES_SUBPLANES.md` §12 (lines 619–722), §18.3, §19.5–19.9 (lines
  1373–1450), §20.7 Implementer addendum (lines 1961–1973).
- Existing adaptation precedent: `skill/references/third-party-notices.md` §Caveman (an older Caveman revision is
  already adapted for `communication-and-context.md`) — read-only.
- Schema 1.3.0 design `.../engine-v2/SCHEMA-1.3.0.md` (subplan_id, ui tasks, Designer contract) for brief fields.

## You own
- `skill/agents/implementer.md`
- `skill/agents/implementer/skills/**` (three extracted drafts exist)
- `skill/agents/implementer/references/**` (new, optional)

## Requirements
1. The three private skills become **approved**: drop "draft (not approved)" wording and the "use only if approved"
   trigger; keep their content and boundaries; align field names with the engine (subplan id/revision, Designer
   contract `design/contracts/<id>@v<N>.md`, base snapshot; result taxonomy reasons `BLOCKED_EXTERNAL`, `FAIL_CODE`
   etc. only as notes until the engine migrates). `safe-worktree-contribution`: M3 owns worktrees; never create,
   delete, merge or push.
2. `implementer.md`: master §20.7 addendum — Ponytail "minimal complete implementation" and Caveman "compact
   reporting" (adapted, never caricature tone; machine fields and persisted artifacts are not compressed) — and
   conditional loading of the three private skills (replace the "remain DISABLED" sentence: they are approved).
   Keep the exclusions explicit: no `systematic-debugging`, `verification-before-completion`,
   `receiving-code-review`. Keep frontmatter, tools and the report contract (`STATUS`, `SUMMARY`, `CHANGES`,
   `VERIFICATION`, `COMMITS`, `RULINGS`, `CONCERNS`).
3. Upstream protocol: Ponytail `DietrichGebert/ponytail` `skills/ponytail/SKILL.md`; Caveman
   `JuliusBrussee/caveman` `skills/caveman/SKILL.md` (repo has mixed licenses — read LICENSE/LICENSING/NOTICE at the
   pinned SHA and adapt only the textual skill). For each: `git ls-remote https://github.com/<o>/<r> HEAD` → SHA;
   `curl -fsSL https://raw.githubusercontent.com/<o>/<r>/<sha>/<path>` for the skill and license files. Data only;
   never execute anything; write original text. List repo/path/SHA/license/what-adapted-where in PROVENANCE. Do NOT
   edit `skill/references/third-party-notices.md` (the lead consolidates it).
4. Candidates `lean-build`, `surgical-patch`, `safe-refactor`, `incremental-implementation`, TDD stay candidates:
   do not add them.

## Verify
Every referenced path exists; full suite per RULES.md.
