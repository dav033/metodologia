# Domain glossary: keep the project's language sharp while you work

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/domain-modeling/SKILL.md, GLOSSARY-FORMAT.md and
ADR-FORMAT.md. Adapted here: challenge against the glossary, sharpen fuzzy terms, scenario stress-tests,
cross-check with code, update inline, and offer a decision record only on the three criteria. Original here: the
glossary lives in the project's bitácora, decisions go to DECISIONS.md (not `docs/adr/`), and no file is created in
a repo. Not imported: `GLOSSARY-MAP.md`, per-repo `docs/adr/` and the setup skill that writes `docs/agents/`.
License: `third-party-notices.md`. File format: [`glossary-conventions.md`](glossary-conventions.md).

## Load when

- During requirements rounds, a Grill Me interview or an architecture review, a domain word is ambiguous,
  overloaded ("account" meaning two things) or contradicts what the code or the glossary says.
- You are asked to write, edit or review `GLOSSARY.md`, or to name a new domain concept.
- A user message mixes two terms for one concept, or one term for two.

Merely reading `GLOSSARY.md` to use its words is a habit, not a reason to load this file. Do not use it for
generic programming vocabulary.

## What to do while the conversation runs

1. **Challenge against the glossary.** When a term conflicts with its entry, say so at once: "GLOSSARY defines
   'cancellation' as X, you seem to mean Y; which one?" Put it in the current round as a question with a
   recommended answer.
2. **Sharpen fuzzy language.** Propose one canonical term for a vague or overloaded word, and name the aliases it
   replaces.
3. **Stress-test with a concrete scenario.** When relationships between concepts are being decided, invent a
   scenario that probes an edge (partial cancellation, a refund after a plan change) and make the boundary explicit.
4. **Cross-check with the code.** When the owner states how something works, check it. If code disagrees, surface
   the contradiction instead of choosing silently: "the code cancels whole Orders, you said partial is allowed".
5. **Write it down when it settles.** Update `<project>/GLOSSARY.md` in the same turn, not at wrap-up. Create the
   file from `templates/GLOSSARY.md` the first time a term is resolved; never create it for its own sake.
6. **Use the term afterwards**: in specs, plans, test names, hypotheses, commit messages and replies.

## What stays out of the glossary

Implementation detail, scratch notes and specs. It defines what a term **is**, in one or two sentences, for terms
specific to this project. A general programming concept (timeout, retry, DTO) does not belong even if used heavily.

## Decisions

A choice goes to DECISIONS.md (`documentation.md`) only when it is hard to reverse, surprising without context and
the result of a real trade-off between alternatives; otherwise leave it out and keep the log readable. A glossary
entry that records a consequential choice links its `D-NNN`. If your proposal contradicts an existing decision,
say so explicitly ("contradicts D-007, worth reopening because...") instead of silently overriding it.

## Boundaries

The glossary belongs to the project, not to a repo: it is a bitácora file, so the "no new files in repos" rule
holds. If a repo already ships its own `GLOSSARY.md`, read it and respect it; propose changes to it rather than
editing it without a plan. A workspace with several repos has one glossary, grouped by context under headings.
