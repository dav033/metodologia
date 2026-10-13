---
id: REQ-016
status: ready
created: 2026-10-13
track: standard
---
# REQ-016 — Guided 3D edit leftovers: exact undo and colour resolver (P-042, P-058)

## Problem & goal
Two small defects left in the guided 3D editing flow (REQ-007 phase 5): undo applies an inverse edit and drifts (enlarge-then-shrink != identity; name-based colour returns can change the code), and the colour resolver asks needlessly or rewrites order state after edits.

**Success looks like:** undo restores the exact stored previous spec; the colour resolver no longer asks in the cases listed below; all covered by regression tests.

## Scope (in)
### US-1 (P1, Must) — Exact undo (P-042)
**Acceptance:** Given any sequence of size/colour edits, when the customer undoes, then the spec equals the stored previous spec byte-for-byte (same piece sizes, same colour codes), never an inverse edit.
### US-2 (P2, Must) — Colour resolver leftovers (P-058)
**Acceptance:**
- A1: a palette-word order whose destination is already in the selection does not ask after a successful edit (needs a stored last order); «puede ser» cases counted in the no_aplicadas audit.
- A2: sumarIdeaAEspec keeps `origen` (anti-alternation stays on).
- A3: «rosa → rosado» on a plan already rosado does not ask (add `!entran.includes(codigo)`).
- A4: consumo.ts declares the correct `origen.tipo` (not 'ui').

## Out of scope
New edit types, UI redesign, push/merge/deploy, paid calls, other pending items (P-057 leftovers beyond what A1 needs).

## Requirements
- R1. When the customer undoes a guided 3D edit, the system shall restore the stored previous spec.
- R2. When a colour order's destination is already selected after a successful edit, the system shall not ask for clarification.
- R3. When sumarIdeaAEspec runs, the system shall preserve `origen`.
- R4. When «rosa → rosado» targets a plan already rosado, the system shall not ask.

## Edge cases & errors
Undo after several edits; undo when no previous spec is stored (refuse honestly, no fabricated success); chained colour orders.

## Constraints
AGENTS.md rules; no `any`; contracts/persisted session schemas stay rollback-compatible (D-035); no push; `npm run gate` green.

## Priorities & phases
M1 undo (US-1), M2 resolver (US-2).

## Assumptions
Defects are still present at HEAD 1f304b4e (executor must reproduce each with a failing test first; if one is already fixed, close it with evidence instead of changing code).

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Scope / out of scope | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
