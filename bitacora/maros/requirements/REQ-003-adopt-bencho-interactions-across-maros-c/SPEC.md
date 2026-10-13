---
id: REQ-003
status: done
created: 2026-10-11
track: deep
---
# REQ-003 — Adopt Bencho interactions across Maros CRM

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Maros has interactive workflows across task management, notes, calendar, CRM forms, file handling, and reporting. The owner wants Bencho's interactive React blocks applied throughout the product where they improve these workflows, and wants worthwhile new capabilities surfaced by the library implemented end to end.

**Success looks like:** every user-facing frontend route has a row in `INTERACTION-INVENTORY.md`, with its interactive workflows and a reasoned Bencho disposition; selected blocks work with the existing data, authorization, accessibility, and error behavior; the new cross-section command palette works on authenticated routes.

## Users / actors / stakeholders
- Maros internal staff and external users who interact with CRM/public-link workflows.
- Maros owner as approver of scope and plan.

## Scope (in)
### US-1 (P1, Must) — Improve existing interactive surfaces
As a Maros user, I want useful Bencho interactions adapted to my existing CRM workflows so that common actions feel direct, clear, and responsive without losing existing behavior.
**Acceptance:**
- Given every user-facing interactive route in `maros-next`, when it is audited, then the implementation records its workflows and whether a Bencho block improves them.
- Given the audit is complete, when `INTERACTION-INVENTORY.md` is reviewed, then it has an entry for every `src/app/**/page.tsx` route and each shared interactive shell, with audience, workflow/control, current implementation, considered Bencho block(s), disposition and rationale, relevant guardrails, and verification evidence.
- Given a selected block is integrated, when I use the related workflow, then existing data, permissions, validation, keyboard/touch behavior, loading/error states, and navigation remain correct.
- Given a block does not improve a surface or duplicates an existing accessible control, when the audit is complete, then that surface's existing interaction is retained with its reason recorded.

### US-2 (P2, Conditional) — Add justified capabilities discovered through Bencho
As a Maros user, I want any newly discovered interactive capability to support a real CRM workflow so that the product gains useful behavior without speculative features. This story is conditional: it does not require inventing a new capability if the audit finds none beyond the global palette in US-3.
**Acceptance:**
- Given the route audit identifies a Bencho capability missing from Maros, when it is assessed, then only capabilities with a clear CRM actor, workflow, and outcome are added to the approved implementation scope; if none qualify, record that result and close this conditional story without adding a feature.
- Given an accepted capability needs server behavior or persistence, when it ships, then authorization, validation, durable state, and UI states are implemented end to end.

### US-3 (P1, Must) — Search and navigate from one command palette
As an authenticated Maros user, I want one command palette for navigation and finding tasks and notes so that I can reach work from any CRM area without switching to a feature-specific screen first.
**Acceptance:**
- Given I am on any authenticated CRM route, when I press Ctrl+K or ⌘K or activate the visible search control, then one accessible command palette opens.
- Given I search, when matching tasks or notes are returned, then the palette labels each result type and opens the selected record using existing routes and permission checks.
- Given I lack permission to a destination, when navigation choices are shown, then that destination is omitted; the server remains the authorization authority.
- Given I am on a public route or `/login`, when the page loads, then the authenticated command palette is not mounted.
- Given the query has no matches, is loading, or fails, when results are shown, then the palette communicates the correct empty/loading/error state and remains usable for navigation.

### US-4 (P1, Must) — Add useful, accessible motion and animated components
As a Maros user, I want meaningful feedback when CRM state changes so that actions, loading, and navigation feel responsive without slowing down routine work.
**Acceptance:**
- Given an interaction is selected for motion in the route inventory, when its state changes, then animation clarifies feedback or spatial continuity and does not delay task completion.
- Given Motion Primitives is requested as an additional component source, when implementation completes, then at least one source component is adapted into a concrete CRM workflow identified by the route inventory; the inventory names the source component and records why it improves that workflow.
- Given the OS/browser requests reduced motion, when any adopted animation runs, then non-essential movement is removed or reduced while state, affordance, and feedback remain clear.
- Given a Bencho or Motion Primitives source block is considered, when copied into Maros, then its dependencies, license, keyboard/touch behavior, server/client boundary, and design-token fit are reviewed and documented before adoption.
- Given an existing shadcn/Radix component already serves the workflow, when an animated block is considered, then it may decorate that control but shall not replace its semantics, validation, authorization, or accessible behavior.

## Out of scope
- Adding Bencho as a runtime/npm dependency: Bencho distributes individual React source blocks for copying, not an installable component package.
- Replacing the existing shadcn/Radix design system with another foundational component system, including a migration to Base UI.
- Adopting every gallery block regardless of CRM fit.
- Adding motion solely for decoration, continuous background effects, or animation that obscures status or content.
- Replacing working business logic, API contracts, or existing accessible components solely to make the UI visually uniform.
- Backend-only refactoring unrelated to an accepted interactive capability.
- Publishing, pushing, merging, or deploying.

## Requirements
- R1. When any user-facing interactive frontend route is reviewed, the implementation shall record its interactive workflows and the disposition of each relevant Bencho block.
- R2. When a Bencho source block is adopted, the implementation shall adapt its dependencies, styling, data contract, and motion behavior to Maros; copied substantial source shall retain the MIT copyright/license notice.
- R3. While a user performs an adopted interaction, the system shall preserve authorization, business validation, data correctness, keyboard access, touch operation, reduced-motion preference, and explicit loading/error/success states.
- R4. When a new CRM capability is implemented, the system shall provide the complete required frontend and backend path, with runtime validation and authorization at API boundaries.
- R5. When a gallery block has no justified CRM workflow or would weaken usability/accessibility, the system shall not introduce it.
- R6. When the interaction audit is complete, the requirement folder shall contain `INTERACTION-INVENTORY.md` with a row for every frontend page route and shared interactive shell plus all required disposition fields.
- R7. When an authenticated user invokes the global command palette, the system shall combine permission-filtered navigation choices with existing task and note search capabilities without changing their data or authorization contracts.
- R8. When motion is added, it shall communicate interaction or state, respect `prefers-reduced-motion`, preserve keyboard/touch alternatives, and keep information understandable without animation.

## Edge cases & errors
- Bencho source may assume dependencies or CSS not present in Maros, or duplicate Radix, shadcn, `@dnd-kit`, React Hook Form, or another existing interaction.
- Drag-only, hover-only, sound-only, and motion-dependent interactions must keep keyboard, touch, and reduced-motion alternatives.
- Existing workflows may fail partially (upload, save, sync, search, calendar); visual enhancements must retain retry and error recovery.
- Task and note areas currently own separate Ctrl/⌘K palettes; consolidation must remove duplicate listeners and preserve each feature's query behavior.
- Public-link and authenticated routes have different user identities and permissions; preserve their existing authorization and access boundaries.
- No new feature may invent CRM data or bypass existing API authorization.

## Constraints
- Workspace includes `maros-next` (Next.js 16 / React 19 / Tailwind 4, shadcn/Radix, `@dnd-kit`) and `maros-nest` (NestJS API). Current working branches are `feat/req-001-fix-document-scans-and-estimate-email` in both; worktrees were clean at exploration.
- The backend has no visual UI; Bencho adoption belongs in the frontend unless a justified feature requires API work.
- Bencho's individual blocks and copied source are MIT according to its official license; preserve the notice with substantial copied code and do not copy site branding/photos.
- Maros already uses shadcn/Radix, Next.js 16, React 19, and Tailwind 4. Use Motion Primitives as a supplementary source of copyable animated components, not as a second base component system. Its source project declares MIT and beta status; inspect each selected block rather than assuming library-wide accessibility or SSR guarantees.
- Prefer CSS transitions for simple effects. Add the `motion` runtime only when an accepted component needs its state/gesture/layout capabilities; retain reduced-motion alternatives and verify the client boundary in Next.js.
- No production writes, external communications, push, merge, or deploy are in scope.

## Priorities & phases
- P1: Create `INTERACTION-INVENTORY.md` covering all user-facing routes, shared shell, and applicable Bencho block dispositions.
- P1: Consolidate task and notes search palettes into one permission-aware command palette available across authenticated routes.
- P1: Integrate high-value existing CRM interactions in dependency-ordered feature slices.
- P1: Add purposeful, reduced-motion-aware transitions and selected animated components where the route inventory demonstrates a workflow benefit.
- P2 conditional: Implement another capability discovered in the audit only when it has a clear CRM actor, workflow, and outcome; if the palette in US-3 is the only justified capability, record that no additional feature is needed.
- P2: Complete the audit disposition for remaining interaction surfaces without gratuitous replacement.

## Timeline & dependencies
- Implementation follows an approved plan; broad scope will span multiple phases.

## Assumptions
- "End to end" means every user-facing interactive route is audited, with selective Bencho adoption wherever it materially helps a real Maros task; it does not mean copying all gallery blocks into Maros.
- Backend changes are allowed only when a justified new capability requires persistence or business logic.
- New capabilities should be directly supported by an identifiable Maros workflow, not novelty alone.
- The command palette will be mounted in the authenticated app shell and reuse current task and note search adapters; no new backend search contract is assumed.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear — product-wide interactive UX adoption and useful capabilities |
| Users / actors | Clear — internal staff and external users across public and authenticated routes |
| Scope | Clear — all user-facing interactive frontend routes; API only for justified new capabilities |
| Out of scope | Clear — no wholesale copy, unrelated refactor, or production action |
| Flows & behavior | Clear — full route inventory and one cross-section palette are defined |
| Edge cases | Clear — accessibility, compatibility, and existing recovery states identified |
| Acceptance criteria | Clear — US-1/US-4 criteria and route audit artifact defined |
| Constraints | Clear — workspace architecture, Bencho, Motion Primitives, and reduced-motion boundaries verified |
| Priorities & phases | Clear — US-2 is conditional and no extra capability is required without a concrete workflow |
| Timeline | Deferred — no deadline supplied |

## Clarifications
### Round 1 — 2026-10-11
- Q: Should the full frontend boundary include interactive public/external routes (public project/estimate links, contact or invite flows) as well as authenticated CRM routes? → Include every user-facing interactive route, based on the owner's original product-wide instruction; do not mount the authenticated palette on public pages.
- Discovery: the authenticated shell currently has separate task and note Ctrl/⌘K palettes. → Add one shared, permission-aware palette that reuses both existing search paths.
- Pre-mortem: wholesale adoption could disrupt CRM muscle memory, accessibility, or existing data/permission behavior. → Inventory every route first; adopt blocks only where the workflow improves, preserve keyboard/touch/reduced-motion paths, and verify each feature slice before continuing.

### Round 2 — 2026-10-11
- Q: Should Maros adopt a separate component source and broader motion polish alongside Bencho? → Yes. Keep existing shadcn/Radix controls; use Motion Primitives selectively as a supplementary source, preserve reduced-motion behavior, and avoid decorative motion.
- Discovery: Maros already has React 19, Next.js 16, Tailwind 4, shadcn/Radix, and reduced-motion CSS/hooks; Magic UI's official docs emphasize landing pages and marketing, while Motion Primitives documents app-oriented copyable animated components and declares MIT/beta.
- Approval: the owner directly instructed implementation and authorized autonomous execution on 2026-10-11; the updated requirement and plan are approved.
- US-2 conditional outcome: the route audit did not justify another capability beyond the global palette; no speculative feature was added.
