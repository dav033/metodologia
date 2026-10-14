# Improve architecture: find and rank deepening candidates

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/improve-codebase-architecture/SKILL.md and
HTML-REPORT.md. Adapted here: the churn-first scan, the candidate card with a strength badge, the ADR-conflict
callout and the grill-through loop. Original here: output goes to the bitácora (artifacts, DECISIONS.md, PENDING.md)
and never to a temp dir or the repo, and no CDN is required. Not imported: the Tailwind/Mermaid CDN scaffold, the
forbidden-word list and auto-opening a browser. License: `third-party-notices.md`.

## Load when

Only on an explicit request: "improve the architecture", "mejora la arquitectura", "busca módulos superficiales",
"candidatos de refactor", `/improve-architecture`, or when the owner picks this as the follow-up of an architecture
audit. Never start it on your own from an unrelated task: unrequested refactors are Proposals
(`engineering.md` §1). Read [`design-vocabulary.md`](design-vocabulary.md) first.

## 1. Scope the scan

- If the owner named a direction (module, subsystem, pain point), take it and skip the inference.
- Otherwise find the hot spots: `git log --oneline` over a good stretch of history, plus `bitacora.py trace --file`
  for files that keep appearing in requirements. Areas that changed recently pay back deepening first; if changes
  are scattered with no hot spot, widen the net.
- Read `GLOSSARY.md`, `DECISIONS.md` and `ARCHITECTURE.md` for that area before looking at code.

## 2. Explore for friction

Send the `explorer` for wide sweeps (`subagents.md`). Look for:

- A concept that needs bouncing between many small modules.
- Shallow modules: interface nearly as complex as the implementation.
- Pure functions extracted only for testability while the real bugs hide in how they are called.
- Tightly coupled modules that leak across their seams.
- Parts that are untested or hard to test through their current interface.

Apply the deletion test to every suspect: would deleting it concentrate complexity or just move it? Keep only
candidates where it concentrates. Every claim cites `path:line`; an unverified suspicion is labelled as such.

## 3. Present candidates, no interfaces yet

One card per candidate, ordered by strength:

| Field | Content |
|---|---|
| Files | the modules involved |
| Problem | the friction, in domain words from GLOSSARY.md |
| Solution | what would change, in plain language: say what concentrates where, never name a new interface, port, type or signature |
| Benefits | locality and leverage gained, and how tests improve |
| Dependency category | in-process, local-substitutable, remote-owned, true external |
| Strength | `Strong`, `Worth exploring` or `Speculative`, with the evidence behind it |
| Decision conflict | only when it contradicts a DECISIONS.md entry **and** the friction is real enough to reopen it |

Close with the one you would do first and why. Show the cards in the conversation (Spanish, concise). When a
before/after picture helps, also write one self-contained HTML in `<project>/artifacts/` per `documentation.md`
§Artifacts, and give its URL; a diagram renderer, if the platform provides one, may draw it, but the cards are the
required output. Do not propose interface shapes yet (not even "a small X interface" or "a port for Y"); end by asking which candidates
the owner wants to explore and recommend one.

## 4. Grill the chosen candidate

Use the existing Grill Me interview (`requirements.md` §4): constraints, dependencies, shape of the deepened module,
what sits behind the seam, which tests survive. Optionally design it twice (`design-vocabulary.md`). As decisions
land:

- A new domain concept or a sharpened term goes to GLOSSARY.md now (`domain-glossary.md`).
- A candidate rejected for a load-bearing reason goes to DECISIONS.md so later reviews do not resurface it: hard to
  reverse, surprising without context, and a real trade-off. Ephemeral reasons ("not now") are not recorded.
- Work the owner accepts becomes a requirement or a PENDING.md item with urgency and complexity.

## Limits

This flow produces proposals, decisions and glossary entries, not code. Editing project repos needs an approved
plan like any other change. Structural and behavioral changes stay in separate steps (`engineering.md` §2).
