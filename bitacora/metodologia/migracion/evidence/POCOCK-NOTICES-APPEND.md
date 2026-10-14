# Block to append to `skill/references/third-party-notices.md`

Append the section below after the existing "Matt Pocock's Grill Me / grilling" section and before
"Apache License 2.0". Also change the intro sentence of that file ("excerpts and modified prompts in
`communication-and-context.md`") so it names the files listed here. The MIT text is already present in the existing
Pocock section for the same commit, so this block references it instead of repeating it.

---

## Matt Pocock's engineering and productivity skills (policy adaptations)

Adapted and modified from `mattpocock/skills`, revision `49dd158d1076134a641b33efb035946536778336`, the same
revision and license as the Grill Me / grilling section above. License: MIT, "Copyright (c) 2026 Matt Pocock"; the
complete permission notice is reproduced in that section and applies to every file below.

Only prompt material was reviewed and re-expressed; no upstream script, template, runtime or dependency is
distributed. Each adapted file begins with `Source: mattpocock/skills@49dd158 (MIT), <path>` and states which rules
are adapted and which are original or deliberately not imported.

| metodologia file | Upstream source (at the revision above) |
|---|---|
| `references/design-vocabulary.md` | `skills/engineering/codebase-design/SKILL.md`, `DEEPENING.md`, `DESIGN-IT-TWICE.md` |
| `references/improve-architecture.md` | `skills/engineering/improve-codebase-architecture/SKILL.md`, `HTML-REPORT.md` |
| `references/domain-glossary.md` | `skills/engineering/domain-modeling/SKILL.md`, `GLOSSARY-FORMAT.md`, `ADR-FORMAT.md` |
| `references/glossary-conventions.md`, `templates/GLOSSARY.md` | `skills/engineering/domain-modeling/GLOSSARY-FORMAT.md`, `ADR-FORMAT.md` |
| `references/test-seams.md` | `skills/engineering/tdd/SKILL.md`, `tests.md`, `mocking.md`; seam step of `skills/engineering/to-spec/SKILL.md` |
| `references/diagnosing-bugs.md` | `skills/engineering/diagnosing-bugs/SKILL.md` |
| `references/retro-feedback.md` | `skills/engineering/retro/SKILL.md` |
| `references/writing-for-agents.md` | `skills/productivity/writing-for-agents/SKILL.md`, `SKILL-MECHANICS.md` |
| `references/wait-what.md` | `skills/productivity/wait-what/SKILL.md` |

Reviewed and not adopted (no text used): all other upstream skills, including `pr`, whose visual-summary menu is
credited upstream to Dex Horthy's `show-me` (`skills/engineering/pr/CREDITS.md`); if `pr` is ever adopted, that
credit must be carried here as well.

The pinned upstream copy used for review is `/home/david/.local/share/metodologia-migration/upstream/skills`;
the review record is `bitacora/metodologia/migracion/evidence/POCOCK-REVIEW.md`.
