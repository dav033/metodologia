---
id: REQ-022
status: dropped
created: 2026-10-27
track: standard
---
# REQ-022 — Plans catalogue: subscription tiers section (Free, 20k, Designer, Designer Max)

> **Dropped 2026-10-27 (owner):** the plans work moves into REQ-021 as new subplan(s). See `HANDOFF-to-REQ-021.md`.

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Owner (2026-10-27), while reviewing the REQ-021 SP-2 design (accounts/administration): the side panel «Cada persona.
Sus herramientas.» (Plan 1/2/3 as a list of tools) adds nothing for users or administrators. Instead of that panel, Pictures
needs its own **section to look at the plans**. Owner's definition of the four tiers, in his words:

1. **Free**: «el asistente de decoración básico por chat, contador de globos y ya, con límites».
2. **Second tier**: «20k pesos al mes / 7 dólares». *Contents not stated yet (see open questions).*
3. **Designer plan**: «chat extendido, calculadora de costos, detección de estructuras y detección de globos avanzado»;
   «45k pesos y 14 dólares».
4. **Designer Max**: «todo lo anterior + el acceso al software de globos» (the Taller 3D).

REQ-021 SP-2 will NOT carry any of this logic (owner). This requirement is the subsequent logic, planned by a separate
Planner instance.

**Success looks like:** _to be confirmed with the owner (draft)._

## Users / actors / stakeholders
- Prospective and current users who want to see what each plan includes and costs (assumption).
- Administrators who assign plans (REQ-021 SP-2 assigns access plans as roles).
- Owner: David.

## Scope (in)
<!-- User stories, ranked. Each one independently valuable and testable.
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
- Anything inside REQ-021 SP-2's screens: that subplan keeps accounts, roles and permissions only; its plan side panel is removed (owner).
- Payment processing, billing and subscription management are NOT stated by the owner: treat as unknown until confirmed (see open questions).

## Requirements
<!-- EARS style, numbered so tests/plan can cite them:
- R1. When <trigger>, the system shall <response>.
- R2. If <unwanted condition>, then the system shall <response>.
- R3. While <state>, the system shall <response>.
For business processes, "the system" can be a role or the process ("the approver shall…"). -->

## UI / design contract (optional)
<!-- Include when the requirement contains user-facing UI. Record users, supported flows/views, existing design
system or visual direction and any meaningful accessibility constraints. The plan defines UI subplans; Designer
authors a versioned contract and the owner approves each version before UI implementation. -->
- UI scope / users:
- Visual direction / existing system:
- Accessibility or interaction constraints:

## Edge cases & errors
-

## Constraints
- Prices as given: tier 2 COP 20,000 / USD 7 per month; Designer COP 45,000 / USD 14 per month. Free has «límites» (values not given).
- Must not contradict or edit REQ-021 (SPEC, PLAN.json, rounds, `.planning/`). REQ-021 R16 and round 6 currently define
  THREE access plans as roles (Usuario · Plan 1/2/3: chat+counter / + costs+explorer / + Taller 3D). The owner's four tiers
  differ (Free, 20k, Designer, Designer Max); how they map onto those roles is an **open decision**.
- UI follows the existing Pictures design system (see the SP-2 chosen direction «Parte de acceso» style: rounded surfaces).

## UI / design contract
_If scope includes a UI subplan: identify its users and primary task, visual direction, existing design system or
brand constraints, supported states/breakpoints, and accessibility requirements. Planner assigns a versioned
contract to Designer; the owner approves each version before UI implementation. Omit or mark not applicable when
there is no UI subplan._

## Priorities & phases
_MoSCoW + what is MVP vs later._

## Timeline & dependencies
-

## Open questions (for the owner; the Planner must ask, not guess)
1. What does the 20k / USD 7 tier include and what are the Free limits (messages, balloon counts, per day/month)?
2. Is this section informative only (compare plans, contact/request upgrade) or does it include purchase/subscription?
   If purchase: payment provider, currencies (COP and USD shown together or by locale), trial, cancellation.
3. Mapping to REQ-021 roles: do the four tiers replace «Plan 1/2/3», extend them, or live apart from roles/permissions?
   (Detection of structures and advanced balloon detection are tools that do not exist as permissions yet.)
4. Who sees the section (public, signed-in users, administrators) and where it lives in the app navigation.
5. Are «chat extendido», «detección de estructuras» and «detección de globos avanzado» existing capabilities or future work?
6. Pilot date: is this inside the 2026-11-16 pilot or after it?
7. What is the Designer Max monthly price (COP and USD)? The owner gave prices for the second tier and Designer only.
8. Does each plan include everything in the plans below it (Designer = second tier + its own tools; Designer Max =
   Designer + Taller 3D)? The owner said «todo lo anterior» only for Designer Max.
9. How are prices shown: COP in Spanish and USD in English (REQ-021 language switch), or both always?

Blocking (Planner, 2026-10-27; detail in PLAN.md «Open question → subplan blocking»): Q1 → SP-1 data (T1.2), SP-2,
SP-3 · Q2 → only a conditional plan-action subplan (SP-1 is informative by owner instruction) · Q3 → SP-2, SP-4 ·
Q4 → SP-1 placement (T1.4, T1.5), SP-4 · Q5 → SP-1 tool list (T1.2), SP-2 · Q6 → ordering against REQ-021 ·
Q7, Q8 → SP-1 data (T1.2) · Q9 → SP-1 page (T1.3).

## Assumptions
_Best guesses taken instead of asking, with why. Revisit if they turn out wrong._
- The section is a new UI (own design contract) shown in Spanish by default. Revisit when Q2 is answered.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Partial |
| Users / actors | Partial |
| Scope | Partial (draft subplans SP-1..SP-4 in PLAN.md; requirements R1–R7 proposed there, not yet in this SPEC) |
| Out of scope | Partial |
| Flows & behavior | Partial (SP-1 informative section drafted; SP-2..SP-4 wait for Q1, Q3, Q4, Q5) |
| Edge cases | Missing |
| Acceptance criteria | Partial (SP-1 tasks only) |
| Constraints | Partial |
| UI / design direction | Partial (SP-1 `planes@v1` ui_brief: existing Pictures tokens, no invented copy) |
| Priorities & phases | Partial (owner: plans section first, informative; entitlements after) |
| Timeline | Missing (Q6) |

## Clarifications
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
- 2026-10-27 (owner, relayed by the coordinator): the plans section to look at and compare the four plans is a subplan
  inside REQ-022 with its own UI design contract; informative section first; entitlement and role-mapping logic are
  separate subplans after it.
- Round 1 posted 2026-10-27 (questions 1–9 above); answers pending.
