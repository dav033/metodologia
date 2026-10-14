# Retro: improve the agent's environment from observed friction

Source: mattpocock/skills@49dd158 (MIT), skills/engineering/retro/SKILL.md. Adapted here: the candidate
categories (steering files and no-ops merged), severity ordering, "mechanical violations get a deterministic
check, judgement calls get a standard", and the implementation-versus-review context pressure. Original here: a
Process category, output through `bitacora.py learn add`, no automatic policy rewrite and no file created in the
repo. Not imported: scanning session logs across the machine and the assumed `CODING_STANDARDS.md`.
License: `third-party-notices.md`.

## Load when

The owner asks for a retro ("retro", "retrospectiva", "qué salió mal", "cómo mejoramos el entorno"), a milestone
or long session ends after repeated friction, or a bug fix revealed that nothing could have caught it. It is a
backward look at the **environment** (navigation, checks, standards, steering files, tools), not at the code.

## Procedure

1. **Read primary sources for the session named** (default: the current one): its day-log section, PLAN.md
   progress and Rulings, RUN artifacts, review findings, and `learn list`. Stay inside the project and sessions
   the owner pointed at; do not search the machine for unrelated transcripts.
2. **Collect observed friction**, each with evidence (path, command, task id, what cost time). No evidence, no item.
3. **Classify** each item into one category below and rank by severity: cost incurred, repetition, and whether
   it risked wrong output.
4. **Present** the ranked list in Spanish with the proposed change per item. Record, do not apply.
5. **Record** each accepted item with `bitacora.py learn add "<statement>" --scope skill|project --evidence
   "<what happened>" --source <REQ/Tn>`. Use `project` for facts about this codebase or workflow and `skill` for
   friction in the methodology itself. A permanent choice goes to DECISIONS.md instead (`agents.md` §Learning).
   Candidates become rules only after the owner confirms or three independent sightings (`self-improvement.md`).
6. Changes to the skill follow `self-improvement.md`: smallest validated change in the canonical source, never
   from one session's hunch. Out-of-scope fixes are Proposals.

## Categories

| Category | Look for | Typical remedy |
|---|---|---|
| Navigation | the agent took long to find the right file; hidden dependencies | a pointer in ARCHITECTURE.md or the repo's CLAUDE.md |
| Automated checks | an error a linter, type, test or arch check could have caught; no guardrail at all | wire the check the repo already has, or add one (`engineering.md` §9) |
| Coding standards | the reviewer missed a violation | mechanical (fixed pattern, banned API, import shape): a deterministic check; judgement call: a written standard |
| Steering size | a large always-loaded file with no-ops or rules better placed elsewhere | move to a check, a reference or a pointer (`writing-for-agents.md`) |
| Tool economy | an expensive or noisy call a cheaper one would replace | `communication-and-context.md` or a tool alias in TOOLS.md |
| Information access | a decisive fact was not reachable (logs, read-only access) | give read-only access or tee the log; record it in TOOLS.md (no secrets) |
| Process | a gate, hand-off or review step that failed or was skipped | a learning with evidence, or a Proposal |

Where the finding is the absence of a correct seam to lock a bug down, route it to
[`improve-architecture.md`](improve-architecture.md).

## Principles

- **Implementation has the most context pressure, review the least.** Put enforcement of standards in review and
  checks, not in a longer prompt for the implementer.
- **Default to a check over a sentence** for anything mechanical; a sentence is for what no check can enforce.
- **Rank by observed friction, not by taste.** An idea without a sighting is a Proposal.
- Do not delete a rule because it looks like a no-op: governance, permission and approval rules stay unless an
  eval or a confirmed learning shows the change is safe.
