# M6 context cost (measured, not targeted)

Measured 2026-10-14 with `wc -c` / `wc -l` on `/home/david/dev/metodologia/skill`. Bytes, not tokens; no tokenizer
was run, so no token figure is claimed. No reduction target is assumed: these are costs of what M6 adds, and
what stays unchanged.

## Always-on today

| File | Bytes | Lines | Loaded |
|---|---|---|---|
| `skill/SKILL.md` | 11,696 | 141 | every session (router plus rules) |
| `skill/references/engineering.md` (reference, for context) | 16,592 | 254 | when code is designed, written, reviewed or debugged |
| `skill/references/third-party-notices.md` (for context) | 15,685 | 306 | attribution only, never agent instructions |

M6 changed none of these three files in this task; the new files below are additions.

## New files (all load only on their trigger)

| File | Bytes | Lines | Trigger (first section "Load when") |
|---|---|---|---|
| `references/design-vocabulary.md` | 4,759 | 67 | module interface, seam or abstraction design/review; architecture flow |
| `references/improve-architecture.md` | 4,173 | 70 | explicit request for architecture/deepening candidates |
| `references/domain-glossary.md` | 3,503 | 51 | ambiguous or conflicting domain term; writing GLOSSARY.md |
| `references/glossary-conventions.md` | 2,549 | 47 | writing or editing the GLOSSARY.md file itself |
| `references/test-seams.md` | 4,258 | 68 | planning/writing tests for business logic or a bug fix |
| `references/diagnosing-bugs.md` | 5,038 | 78 | broken, failing, flaky or slow, before any repair |
| `references/retro-feedback.md` | 4,092 | 54 | explicit retro after repeated friction |
| `references/writing-for-agents.md` | 4,643 | 70 | writing or shortening agent-facing documents |
| `references/wait-what.md` | 2,772 | 42 | "wait what"/"no entiendo" style signal |
| `templates/GLOSSARY.md` | 898 | 24 | rendered once, when a glossary is created |
| **Total added** | **36,685** | 571 | none is read in a session that does not hit its trigger |

Largest single file a task could load on top of its normal context: `diagnosing-bugs.md`, 5,038 bytes. A typical
design task would load `design-vocabulary.md` (4,759) and possibly `test-seams.md` (4,258), about 9 KB.

## What the router costs if every trigger gets its own row

Draft rows (not applied; `SKILL.md` was not edited in this task):

```
| Designing or reviewing a module interface, a seam or an abstraction ("deep"/"shallow" module) | `references/design-vocabulary.md` |
| An explicit request for architecture or deepening candidates | `references/improve-architecture.md` |
| A domain term is ambiguous or conflicts; writing or editing GLOSSARY.md | `references/domain-glossary.md` (format: `glossary-conventions.md`) |
| Planning or writing tests for business logic or a bug fix; reviewing test coupling | `references/test-seams.md` |
| Something broken, failing, flaky or slow, before any repair | `references/diagnosing-bugs.md` |
| An explicit retro, or "qué salió mal" after repeated friction | `references/retro-feedback.md` |
| Writing or shortening SKILL.md, references, CLAUDE.md/AGENTS.md or delegation briefs | `references/writing-for-agents.md` |
| "wait what", "no entiendo", "no te entendí", "¿por qué dices eso?" | `references/wait-what.md` |
```

| Option | Rows in SKILL.md | Always-on bytes added | Other |
|---|---|---|---|
| A: eight rows | 8 | 927 (11,696 -> about 12,623) | none |
| B: five rows in SKILL.md; the three code-only references pointed from `engineering.md` §5, §7 and §3 | 5 | 579 (11,696 -> about 12,275) | about 271 bytes added to `engineering.md`, loaded only for code work |

Option B keeps the always-on router smaller at the price of three pointers inside `engineering.md`; both satisfy
"the always-on router stays small". The choice is the coordinator's and should be recorded with the measured
before/after in the day log after the edit, using `wc -c` again rather than these estimates.

## Behavior evidence in this task

- Six deterministic-format eval cases were added (`evals/cases/m6-*.json`): five check that a trigger reaches its
  reference and that the governance rules are kept; one checks that a small direct change loads none of the new
  references. They parse as JSON; they were **not** run against a live agent in this task (needs `claude -p`
  and budget), so no pass rate is reported. Real-agent results must be recorded separately.
- The router rows are not in `SKILL.md`, so a live eval of the routing cannot pass until the coordinator applies
  option A or B.
