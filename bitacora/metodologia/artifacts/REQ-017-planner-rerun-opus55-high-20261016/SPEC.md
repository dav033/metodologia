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
- Activity-specific, selectable official-structure options in the existing individual-piece flow; unknown activities keep the existing menu.
- Activity-aware restriction and server-side enforcement for free complete-composition proposals.
- Auditable record of event-based adjustments.

## Out of scope
- Happia package recommender at `/happie`.
- Changes to event-aware library search or carousel.
- New event vocabulary, catalogue ideas, materials, pricing, 3D generation, or database changes.
- An additional proactive chat turn after the activity is identified.
- Persisting a new widget field when the activity can be derived from the current brief and customer messages.

## Requirements
- R1. For a recognized activity, the individual-piece choices shall place the approved recommended structures first and keep the free-choice option last.
- R2. For a recognized activity, a free complete-composition proposal shall use only the approved structures for that activity.
- R3. An explicit customer-named structure or an edit to an existing plan shall retain current precedence over recommendations.
- R4. Structures unsupported by the 3D flow shall not appear in the curated recommendations for recognized activities, while explicit customer requests keep current handling.
- R5. An unrecognized activity shall retain current recommendation and proposal behavior, including the existing structure choices.
- R6. Any server-side adjustment made to enforce the event policy shall be recorded in the existing audit trail.

## Edge cases & errors
- Unknown or ambiguous activity label.
- Too few recommended structures to compose multiple distinct pieces.
- Provider returns a structure outside the event's allowed set despite a narrowed tool schema.
- Customer explicitly asks for a structure outside the event's recommendations.
- A saved conversation is reopened by an older deployment.

## Constraints
- Reuse the canonical `eventoDeTexto` event vocabulary; do not add a fourth vocabulary.
- The client-safe event module must not bundle `decoraciones.json`.
- Official catalogue, materials, prices, and existing named customer requests remain authoritative.
- No paid model calls.

## Priorities & phases
- MVP: curated event-to-structure policy; server enforcement and audit; exact event-specific structures selectable in the individual-piece flow.
- Deferred: unify event vocabularies and expand thin library coverage.

## Timeline & dependencies
- On 2026-10-16 the owner requested that development continue. The implementation uses the five Opus recommendations as revisable assumptions; no item-by-item product approval is recorded.
- M1 begins with the proposed mapping. M2 server and M3 client depend on M1 and can then proceed independently.

## Assumptions
- The proposed mapping and behavior from Opus 5.5 high in delegation `D-20261016-090752-bc5d` are implementation assumptions, not permanent owner-approved policy; revise them if the owner corrects the scope.
- Independent part means one official structure selected through the existing individual-piece path.
- The free-choice event constraint applies only on the “Propónme algo” path.
- Use the full curated event-to-structure table in PLAN.md; library coverage is informational only.
- Show exact event structures as selectable cards and keep «La que tú quieras» last; do not add a proactive chat turn or a persisted widget field.
- Exclude structures without 3D support from recommendations, while preserving explicit customer requests and existing behavior for unknown events.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear — implementation assumptions are explicit and revisable |
| Out of scope | Clear |
| Flows & behavior | Clear — implementation assumptions define the surface and part definition |
| Edge cases | Clear — unknown events, unsupported structures and explicit requests have defined behavior |
| Acceptance criteria | Clear — detailed in plan; product mapping remains reviewable |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear — implementation is in progress under revisable assumptions |

## Clarifications
- 2026-10-16 — Owner requested continuing development. Use the plan's recommended choices as revisable assumptions; this instruction is not recorded as five explicit product answers.
- Q1 assumption: use the full curated event-to-structure table in PLAN.md; catalogue coverage is evidence only.
- Q2 assumption: apply recommendations only within the existing “Propónme algo” flow.
- Q3 assumption: an independent part is one official structure in the existing individual-piece path.
- Q4 assumption: exclude structures without 3D support from recognized-event mappings; preserve explicit requests and all current unknown-event behavior.
- Q5 assumption: show exact recommended official structure IDs as selectable cards, keep «La que tú quieras», add no proactive turn and persist no new widget field.
