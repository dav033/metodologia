# GLOSSARY.md conventions

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/domain-modeling/GLOSSARY-FORMAT.md and
ADR-FORMAT.md. Adapted here: canonical term, definition and Avoid aliases; opinionated, tight, project-specific.
Original here: the file is a bitácora central file, consequential choices link to DECISIONS.md, and contexts are
sections instead of a `GLOSSARY-MAP.md`. License: `third-party-notices.md`. Behavior while working:
[`domain-glossary.md`](domain-glossary.md).

## Where and when

- One file per project: `<project>/GLOSSARY.md` in the bitácora, from `templates/GLOSSARY.md`. Edited in place;
  the entry is the current truth, history of *why* stays in DECISIONS.md.
- Created lazily when the first term is resolved. Updated in the turn the term settles, not at wrap-up.
- Read it whenever specs, plans, test names or replies need the project's words.
- A repo's own `GLOSSARY.md`, if present, is respected and not edited without an approved plan.

## Entry format

```md
**Order**:
One or two sentences saying what it is.
_Avoid_: Purchase, transaction
_Decision_: D-012
```

- **Canonical term**: bold, singular, the one word the project uses.
- **Definition**: what it **is**, not what it does or how it is built. Use other glossary terms inside it.
- **Avoid**: the aliases you replaced, so a reader or agent who meets one knows the canonical word. Say where an
  alias is legitimate (for example a UI label) instead of leaving it ambiguous.
- **Decision** (optional): `D-NNN` when the entry records a consequential choice (it is hard to reverse, surprising
  without context, and a real trade-off). Routine naming has no link.

## Rules

- **Be opinionated.** Pick one word per concept; list the rest under Avoid.
- **Keep it tight.** Two sentences at most. No implementation detail, no specs, no scratch notes.
- **Project-specific only.** General programming terms do not belong.
- **Group** under headings when clusters or contexts emerge (for example one heading per repo of the workspace);
  a flat list is fine otherwise.
- **Flag resolved ambiguities** in a short "Resolved ambiguities" list: the loose usage and what it was replaced by.
- **Revise in place.** A stale definition is a defect; edit it, and note a superseding choice in DECISIONS.md.
- **No secrets, no personal data.**

## Registration

`GLOSSARY.md` is a central file next to SUMMARY.md and DECISIONS.md. Link it from SUMMARY.md when it exists. Create it
with `bitacora.py --project <p> glossary` (idempotent; never overwrites). The project INDEX.md and the web project
page list it as soon as it exists.
