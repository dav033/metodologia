---
id: REQ-017
status: in-progress
created: 2026-10-16
track: standard
---
# REQ-017 — Activity-aware guided-chat decoration recommendations

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The guided chat should help a customer choose suitable decorations or individual structures for the activity they are planning. The current library carousel already considers event and theme, but the individual-piece menu is static and the model can select any official structure without grounding the choice in the event.

**Success looks like:** For a recognized activity, guided-chat recommendations prioritize an owner-approved ordered set of official, supported structures; an unknown activity keeps current behavior; explicit customer choices remain authoritative.

## Users / actors / stakeholders
- Customer using the Pictures guided chat.
- David as product owner of the recommendation policy and event-to-structure mapping.

## Scope (in)
- Activity-aware ordering for the existing individual-piece menu.
- Activity-aware restriction and server-side enforcement for free complete-composition proposals.
- Auditable record of event-based adjustments.

## Out of scope
- Happia package recommender at `/happie`.
- Changes to event-aware library search or carousel.
- New event vocabulary, catalogue ideas, materials, pricing, 3D generation, or database changes.
- An additional proactive chat turn after the activity is identified.

## Requirements
- R1. For a recognized activity, the individual-piece choices shall place the approved recommended structures first and keep the free-choice option last.
- R2. For a recognized activity, a free complete-composition proposal shall use only the approved structures for that activity.
- R3. An explicit customer-named structure or an edit to an existing plan shall retain current precedence over recommendations.
- R4. Structures unsupported by the 3D flow shall not be recommended, while explicit customer requests for them keep current handling.
- R5. An unrecognized activity shall retain current recommendation and proposal behavior.
- R6. Any server-side adjustment made to enforce the event policy shall be recorded in the existing audit trail.

## Edge cases & errors
- Unknown or ambiguous activity label.
- Too few recommended structures to compose multiple distinct pieces.
- Provider returns a structure outside the event's allowed set despite a narrowed tool schema.
- Customer explicitly asks for a structure outside the event's recommendations.
- A stored client widget predates the optional event field.

## Constraints
- Reuse the canonical `eventoDeTexto` event vocabulary; do not add a fourth vocabulary.
- The client-safe event module must not bundle `decoraciones.json`.
- Official catalogue, materials, prices, and existing named customer requests remain authoritative.
- No paid model calls.

## Priorities & phases
- MVP: curated event-to-structure policy; server enforcement and audit; event-ordered existing piece menu.
- Deferred: unify event vocabularies and expand thin library coverage.

## Timeline & dependencies
- Temporary planning exercise. David explicitly requested implementation through Claude Work; the five Opus recommendations are provisional defaults. Keep the implementation isolated and reviewable so David can revise them before integration.
- M1 begins with the Opus-proposed mapping as a provisional implementation default. M2 server and M3 client depend on M1 and can then proceed independently.

## Assumptions
- Draft product choices and event mapping are proposed by Opus 5.5 high in delegation `D-20261016-090752-bc5d`; use them provisionally under David's direct implementation request, and keep them open for his review before integration.
- Independent part means one official structure selected through the existing individual-piece path.
- The free-choice event constraint applies only on the “Propónme algo” path.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Partial — Opus recommendations are provisional defaults |
| Out of scope | Clear |
| Flows & behavior | Partial — provisional surface and part definition from Opus |
| Edge cases | Partial — proposed fallback rules are reviewable |
| Acceptance criteria | Clear — detailed in plan; product mapping remains reviewable |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear — no date; implementation awaits approval |

## Clarifications
<!-- Answers are recorded after the owner review. -->
