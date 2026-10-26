---
id: REQ-021
status: ready
created: 2026-10-26
track: deep
---
# REQ-021 — Pilot release: bilingual UI, rectangular tables, backing, 3D space, admin roles, AI spend, save projects and decorations, Blender/Illustrator export, editable quartets and modules

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Owner (2026-10-26): three weeks to ship Pictures to a **pilot production** release (target 2026-11-16). Raw list, in his
words, «a grandes rasgos»: English; rectangular tables; backing; add a space in 3D; the ability to create
administrators who can create roles; review the tokens; save projects; save decorations; export to Blender and Adobe
Illustrator; be able to modify quartets and modules.

**Success looks like:** on pilot day, real external users sign in with their own account, build and save 3D projects and decorations, and employees and administrators see per-user AI spend and manage roles; the items in «Never cut» are live, and the rest ships or is cut in the agreed order.

## Users / actors / stakeholders
- **Usuario** (real, external): uses the 3D balloon workshop; no spend dashboard.
- **Empleado interno**: same plus the token/spend dashboard.
- **Administrador**: everything above plus user and role management.
- Owner: David.

## Scope (in)
### US-1 (P1, Must) — Accounts, roles and permissions
As an administrator I invite real external users and internal employees, and create roles by choosing permissions, so that each person sees only what their role allows.
**Acceptance:**
- Given an administrator, when they invite an email, then that person can set a password and sign in; there is no open registration.
- Given three initial roles (usuario, empleado interno, administrador), when the administrator creates a role and picks permissions, then users with that role get exactly those permissions and no more.
- Given a user without a permission, when they open that page or call that API, then access is denied server-side, not only hidden in the UI.
- Given the old shared `APP_PASSWORD` login, when the pilot is live, then it no longer grants access to the pilot.
### US-2 (P1, Must) — AI spend per user
As an employee or administrator I see how many tokens and how much money AI has used, per user and per session, split by kind (text, image generation), mainly in the Taller 3D.
**Acceptance:**
- Given any paid AI call made by a signed-in user, when it completes, then its tokens and estimated cost are stored with that user and session.
- Given an employee or administrator, when they open the spend view, then they see totals per session and per kind and can filter by user; a plain usuario cannot open it.
- No caps or blocking in this plan (owner).
### US-3 (P1, Must) — Save projects
As a user I save, reopen and continue my 3D projects from any browser.
**Acceptance:**
- Given a signed-in user, when they save, then the project is stored on the server under their account and reopens identically.
- Given employees and administrators, when they list projects, then they can open any user's project; a usuario sees only their own.
- Given scenes already saved in the browser (`taller3d:escena:v1`), when the user first signs in, then they are offered an import and nothing is lost.
### US-4 (P1, Must) — Save decorations
As a user I save a composition I built in the scene to my personal library and reuse it in other projects.
**Acceptance:**
- Given a selection or composition in the scene, when I save it with a name, then it appears in my library and can be placed in any of my projects.
- Publishing to the global library is out of this plan.
### US-5 (P1, Must) — Rectangular tables
As a user I create and edit rectangular tables in the Taller 3D, with chairs, by hand and through the AI.
**Acceptance:**
- Given the Taller UI, when I add a rectangular table, then I choose its size and number of chairs, and the shopping list reflects it. (The engine already supports it; the UI path is to be verified.)
### US-6 (P1, Must) — Export to Blender
As a user I export my scene to a file Blender opens with the pieces placed correctly.
**Acceptance:**
- Given a scene, when I export GLB, then Blender imports it with the same layout, sizes and colours; verified by a documented manual check and an automated test of the export.
### US-7 (P1, Must) — Backing category
As a user I find party props (metal hoops, pedestals, round panel, half moon, chiara arches and similar) under one catalogue category called Backing.
**Acceptance:**
- Given the catalogue, when I open Backing, then all existing items of those kinds are listed there and can be added to the scene; no item is lost from where it is found today.
### US-8 (P2, Should) — English / Spanish for everything
As a user I switch between English and Spanish, detected automatically from the browser the first time, and everything changes: interface, AI replies, product names and descriptions.
**Acceptance:**
- Given a first visit with an English browser, when the app loads, then it is in English; the switch changes it back and the choice is remembered per account.
- Given product names and descriptions, when the language is English, then the English text generated once from the Spanish source is shown; an administrator can correct it.
- Given the AI chats, when the language is English, then they reply in English.
- No Spanish string remains on the screens listed as done in the plan; the plan states which screens it covers (cut order: Taller 3D and navigation first).
### US-9 (P2, Should) — Editable modules and quartets
As a user I modify quartets and other modules in the Taller 3D beyond colours (today only colours are editable).
**Acceptance:**
- Given a module in the scene, when I edit it, then the change applies to that module and the counts and shopping list update. The exact edits (shape, spacing, balloon positions) are for the Planner to settle with the owner.
### US-10 (P2, Should) — Assisted chat split and chat↔3D integration
As a user I use three separate tools instead of one chat: a cost calculator, a balloon counter, and the «normal» chat; the chat and the 3D workshop connect.
**Acceptance:**
- Given the three tools, when I open each, then it does one job with its own prompts and spend measured separately.
- Given the normal chat, when I describe what I need in two or three messages, then it defines the need and recommends already-made 3D decorations I can open in the workshop.
- The chat never invents counts or prices (it uses the engine and the real catalogue).

## Out of scope
- 3D space (adding or defining spaces in 3D): owner, round 3: not in this plan.
- Later (owner agreed 2026-10-26): 3D space from a venue photo; vector export for Illustrator.

## Requirements
- R1. When an administrator invites an email, the system shall let that person create a password and sign in; open registration shall not exist.
- R2. The system shall enforce roles and permissions on the server for every page and API of the pilot.
- R3. When an administrator creates a role, the system shall let them choose its permissions from a defined list; the three initial roles shall exist.
- R4. When a paid AI call completes, the system shall store tokens and estimated cost against the user and session.
- R5. While signed in as employee or administrator, the system shall show spend totals per session, kind and user.
- R6. When a user saves a project, the system shall store it server-side under their account; employees and administrators shall be able to open any project.
- R7. When a user first signs in with browser-saved scenes, the system shall offer to import them without data loss.
- R8. When a user saves a composition as a decoration, the system shall add it to their personal library.
- R9. When a user adds a rectangular table, the system shall let them set size and chairs and update the shopping list.
- R10. When a user exports to GLB, the system shall produce a file that Blender opens with the scene's layout, sizes and colours.
- R11. The catalogue shall have a Backing category that lists the existing party props of those kinds.
- R12. When the language is changed or detected, the system shall show the interface, AI replies and product text in that language.
- R13. The assisted chat shall be split into a cost calculator, a balloon counter and a normal chat, and the normal chat shall connect to the 3D workshop.
- R14. If any of R1–R13 is not finished by the deadline, then the cut order in Priorities shall apply; the never-cut items shall ship.

## UI / design contract (optional)
<!-- Include when the requirement contains user-facing UI. Record users, supported flows/views, existing design
system or visual direction and any meaningful accessibility constraints. The plan defines UI subplans; Designer
authors a versioned contract and the owner approves each version before UI implementation. -->
- UI scope / users: Taller 3D and admin screens for real external users, employees and administrators.
- Visual direction / existing system: the existing app design; the Designer proposes admin and spend views consistent with it.
- Accessibility or interaction constraints: to be settled by the Designer per subplan.

## Edge cases & errors
- A user is removed or loses a permission while signed in: access ends on the next request.
- Browser-saved scenes from an older schema fail to import: the user keeps the original and sees why.
- Two sessions save the same project: the later save does not silently overwrite the earlier one.
- AI generation fails midway: spend recorded only for what was billed.
- Product without an English text yet: show the Spanish text rather than an empty field.

## Constraints
- Next.js on Vercel, Python ai-api on a VPS, Neon Postgres; migrations in `scripts/migrations/`. Work branches from `origin/main` in a new worktree, never in the dirty checkout `~/dev/pictures`.
- Security: server-side enforcement of roles; passwords hashed; invited accounts only; personal data of real external users.
- Deadline about 2026-11-16 (pilot production); a plan sized for three weeks.

## UI / design contract
_If scope includes a UI subplan: identify its users and primary task, visual direction, existing design system or
brand constraints, supported states/breakpoints, and accessibility requirements. Planner assigns a versioned
contract to Designer; the owner approves each version before UI implementation. Omit or mark not applicable when
there is no UI subplan._

## Priorities & phases
- **Cut order if time is short (owner agreed, round 3):** 1) language: Taller 3D and navigation first, the rest after the pilot; 2) editable quartets/modules beyond colours; 3) chat improvements beyond the split and reliability. **Never cut:** accounts, roles and permissions, saved projects and decorations, spend per user, rectangular tables, Blender export, Backing. One plan covers everything; the plan is written by a dedicated Opus 5.5 high Planner session, not by the HQ session.
- **Assisted chat (round 3):** split into three tools — cost calculator, balloon counter and the «normal» chat — plus a basic chat↔3D integration: in 2–3 messages the chat defines what is needed and recommends already-made 3D decorations.
- **Added to scope in round 2:** the assisted chat (advisor / guided chat) is IN: it will be broken apart, split and improved (details pending). AI spend caps are OUT for now: measure and show spend only.
- **Must:** accounts with three initial roles (usuario, empleado interno, administrador) and an admin editor to create roles and choose permissions (owner, round 2); AI spend per user with cap and dashboard for employee/admin (mainly Taller 3D); save projects; save decorations; rectangular tables; export to Blender.
- **Should:** switchable English/Spanish for the whole app (interface, AI replies, products), auto-detected; editable modules and quartets; Backing category.
- **Later:** 3D space from photo; vector export for Illustrator.
- Tension to resolve: the owner wants the language switch to cover EVERYTHING (not just main flows) although it is ranked Should.

## Timeline & dependencies
- Owner deadline: pilot production in three weeks from 2026-10-26 (about 2026-11-16). Not an emergency fix: planned work.
- Overlaps with cancelled REQ-004 (users and spend), REQ-005 (decorations from scratch), REQ-006 (venue photo to 3D) and done REQ-011 (module studio), REQ-012 (tables and chairs).

## Assumptions
- Login is email plus password with invitation by email (owner chose «invited», not the mechanism). Revisit if an identity provider is preferred.
- «Blender export» is the existing GLB, verified and fixed, not a new format.
- «Modify quartets and modules» means editing more than colours; the exact edits are not specified yet.
- Existing shared quotes and the advisor accounts table are kept; only the data they need is migrated.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Partial |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| UI / design direction | Deferred |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- Round 1 (2026-10-26): pilot users = real external users + internal employees + administrators; priorities accepted as proposed; «tokens» = AI spend per user, visible to employee and admin (session total, image-generation spend); Backing = one catalogue category grouping party props (metal hoops, pedestals, round panel, half moon, chiara arches); language: EN/ES switch, auto-detected, covering AI replies, products and interface.
- Round 2 (2026-10-26): assisted chat is in scope (to be broken apart, split and improved); external accounts are invited by an administrator, no open registration; admin can create roles and choose permissions from the pilot; no spend caps now (measure and show only); English product names/descriptions are AI-generated once from the Spanish source, stored in the database and editable by an administrator.


### Round 3 (2026-10-26)
- Q: Assisted chat → A: three tools (cost calculator, balloon counter, «normal» chat) + basic chat↔3D integration (2–3 messages to define the need, recommends existing 3D decorations).
- Q: 3D space → A: not added to this plan.
- Q: Who sees saved projects → A: each user sees their own; employees and administrators see all; browser-saved scenes are imported on login.
- Q: Saved decoration → A: a composition built in the scene, saved to the user's personal library for other projects (publishing to the global library is later).
- Q: What moves if time is short → A: cut order above.
