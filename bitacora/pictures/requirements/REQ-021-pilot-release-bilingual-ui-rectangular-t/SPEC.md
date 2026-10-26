---
id: REQ-021
status: clarifying
created: 2026-10-26
track: standard
---
# REQ-021 — Pilot release: bilingual UI, rectangular tables, backing, 3D space, admin roles, AI spend, save projects and decorations, Blender/Illustrator export, editable quartets and modules

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Owner (2026-10-26): three weeks to ship Pictures to a **pilot production** release (target 2026-11-16). Raw list, in his
words, «a grandes rasgos»: English; rectangular tables; backing; add a space in 3D; the ability to create
administrators who can create roles; review the tokens; save projects; save decorations; export to Blender and Adobe
Illustrator; be able to modify quartets and modules.

**Success looks like:** _to settle in the interview (what must work on pilot day, for whom)._

## Users / actors / stakeholders
- **Usuario** (real, external): uses the 3D balloon workshop; no spend dashboard.
- **Empleado interno**: same plus the token/spend dashboard.
- **Administrador**: everything above plus user and role management.
- Owner: David.

## Scope (in)
<!-- User stories, ranked. Each one independently valuable and testable.
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
- Later (owner agreed 2026-10-26): 3D space from a venue photo; vector export for Illustrator.

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
_Tech, integrations, data, security/privacy, compliance, budget, people._

## UI / design contract
_If scope includes a UI subplan: identify its users and primary task, visual direction, existing design system or
brand constraints, supported states/breakpoints, and accessibility requirements. Planner assigns a versioned
contract to Designer; the owner approves each version before UI implementation. Omit or mark not applicable when
there is no UI subplan._

## Priorities & phases
- **Added to scope in round 2:** the assisted chat (advisor / guided chat) is IN: it will be broken apart, split and improved (details pending). AI spend caps are OUT for now: measure and show spend only.
- **Must:** accounts with three initial roles (usuario, empleado interno, administrador) and an admin editor to create roles and choose permissions (owner, round 2); AI spend per user with cap and dashboard for employee/admin (mainly Taller 3D); save projects; save decorations; rectangular tables; export to Blender.
- **Should:** switchable English/Spanish for the whole app (interface, AI replies, products), auto-detected; editable modules and quartets; Backing category.
- **Later:** 3D space from photo; vector export for Illustrator.
- Tension to resolve: the owner wants the language switch to cover EVERYTHING (not just main flows) although it is ranked Should.

## Timeline & dependencies
- Owner deadline: pilot production in three weeks from 2026-10-26 (about 2026-11-16). Not an emergency fix: planned work.
- Overlaps with cancelled REQ-004 (users and spend), REQ-005 (decorations from scratch), REQ-006 (venue photo to 3D) and done REQ-011 (module studio), REQ-012 (tables and chairs).

## Assumptions
_Best guesses taken instead of asking, with why. Revisit if they turn out wrong._

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Missing |
| Users / actors | Missing |
| Scope | Missing |
| Out of scope | Missing |
| Flows & behavior | Missing |
| Edge cases | Missing |
| Acceptance criteria | Missing |
| Constraints | Missing |
| UI / design direction | Missing |
| Priorities & phases | Missing |
| Timeline | Missing |

## Clarifications
- Round 1 (2026-10-26): pilot users = real external users + internal employees + administrators; priorities accepted as proposed; «tokens» = AI spend per user, visible to employee and admin (session total, image-generation spend); Backing = one catalogue category grouping party props (metal hoops, pedestals, round panel, half moon, chiara arches); language: EN/ES switch, auto-detected, covering AI replies, products and interface.
- Round 2 (2026-10-26): assisted chat is in scope (to be broken apart, split and improved); external accounts are invited by an administrator, no open registration; admin can create roles and choose permissions from the pilot; no spend caps now (measure and show only); English product names/descriptions are AI-generated once from the Spanish source, stored in the database and editable by an administrator.

