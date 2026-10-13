---
id: REQ-004
status: in-progress
created: 2026-10-11
track: deep
---
# REQ-004 — Transversal Maros UX and motion refinement

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Maros has an established dark, dense Material design system and strong workflow controls, but motion is limited to local feedback. Navigation, detail expansion, image preview, and common interaction patterns do not yet form one coherent, modern experience. The owner asks for a transversal review and aggressive implementation of high-value design and usability improvements, specifically crossfades, shared-element enlargement, and blur.

**Success looks like:** all current frontend routes are reviewed; shared design and interaction issues are fixed at their common component where possible; client navigation crossfades and selected record/media transitions use shared-element motion; motion remains interruptible or falls back cleanly, respects reduced-motion preferences, and keeps all existing CRM behavior; the frontend lints, typechecks, builds, and its changed core interactions are exercised in a browser.

## Users / actors / stakeholders
- Internal Maros staff and external users who use authenticated CRM workflows or public shared notes.
- David, product owner and approver of the implementation plan.

## Scope (in)
### US-1 (P1, Must) — Make shared CRM navigation and page surfaces coherent
As a CRM user, I want consistent page hierarchy, responsive spacing, clear state feedback, and useful transitions across CRM areas so that I can move between work without losing context.
**Acceptance:**
- Given every current `maros-next` route and the shared authenticated shell, when the design audit is complete, then the inventory identifies common issues, feature-specific issues, and deliberate domain-specific exceptions.
- Given the existing MARO Rev E/F design system, when common shell or shared UI is refined, then its charcoal/elevation/mint identity, data contrast, compact density, and business semantics remain intact unless the owner approves a new direction.
- Given a client-side route navigation, when the destination is ready, then content transitions with a short crossfade that does not trap input or interfere with URL, focus, scroll, or loading behavior.

### US-2 (P1, Must) — Add shared-element enlargement and focused blur
As a CRM user, I want task and image previews to expand from where I selected them, with a softened backdrop, so that I keep spatial context while focusing on detail.
**Acceptance:**
- Given a task opened from its board/list card, when its detail sheet opens or closes, then the matching task surface animates between source and detail while status, DnD, keyboard, and dialog focus behavior remain unchanged.
- Given an image selected from an attachment thumbnail, when its preview opens or closes, then the image enlarges from and returns to that thumbnail with a restrained blurred backdrop; non-image/PDF previews retain their current viewer behavior.
- If the selected source is absent (direct link, stale list, permission-filtered route), then the detail still opens with a normal entrance and no shared-element error.

### US-3 (P1, Must) — Improve shared interaction quality without changing CRM rules
As a CRM user, I want common controls, loading/empty/error states, and focus behavior to be clear and consistent so that routine work needs less guessing.
**Acceptance:**
- Given a shared control or repeated workflow issue is found across features, when it is corrected, then the fix is made at its shared owner and respects each feature's validation, permission, retry, and data semantics.
- Given the audit identifies a defect in a permission, business rule, financial value, backend contract, or persisted workflow, then it is not changed under a visual polish assumption; its behavior and consumers are recorded and scoped explicitly before alteration.

## Out of scope
- Replacing the approved MARO Rev E/F identity with Catppuccin or another palette; adding a light theme; translating product copy wholesale.
- Enabling an experimental Next.js View Transition flag in production without explicit approval and cross-browser evidence.
- Altering backend APIs, authorization, financial calculations, persisted business rules, or adding new CRM entities without a separate accepted requirement.
- Marketing-site work, infrastructure/deployment changes, commits, merges, pushes, or production deploys.

## Requirements
- R1. When the route audit is complete, the inventory shall cover every current frontend page and the authenticated shared shell, grouped into understandable product flows.
- R2. When a route change is committed client-side, the app shall show a short crossfade only after the new content is available; first paint, server redirect, login, and public-note flows shall not be delayed or made inaccessible.
- R3. When a user expands a task or attachment image into a detail surface, matching shared elements shall interpolate position and size, and the backdrop shall gain a subtle blur; keyboard, touch, focus, close, and fallback behavior shall remain available.
- R4. When `prefers-reduced-motion` is active, layout transforms, crossfades, and animated blurs shall be removed or reduced to immediate state changes.
- R5. While transitions run, old snapshots shall not intercept input; navigation may be repeated or interrupted without waiting for animation completion.
- R6. When common UI is improved, changes shall use the existing MARO tokens and maintain WCAG AA text contrast for interactive/data text.
- R7. When a feature-specific defect touches a business rule or external contract, the owner, consumers, and rollback shall be documented before changing it.
- R8. When navigating from `/projects` to `/project/[id]`, the selected project shall be reconstructed from the existing client query cache without calling `/projects/:id/details` or refetching the project list; a cold direct link may load the versioned list contract as fallback. Fields required only by the detail view shall be added through a versioned read endpoint so the existing list contract remains stable.

## Edge cases & errors
- Direct load, refresh, back/forward navigation, redirects, slow streaming/server components, and rapid repeated route changes.
- Reduced motion, keyboard-only navigation, touch, small mobile viewport, zoom, and long localized/English labels.
- Task detail opened without its board card; selected image removed while preview is open; file has no image MIME type or fails to load.
- Dialog and popover focus trapping, scroll-lock restoration, nested overlays, and route change while an overlay is open.
- Permission-filtered items and public-note routes must not expose or animate private content into a snapshot.

## Constraints
- Frontend: Next.js 16.1.3 App Router, React 19.2.1, Tailwind 4, shadcn/Radix, and existing `motion` 14.1.0 dependency. Backend is NestJS/PostgreSQL; no API changes are assumed.
- The approved design direction is documented in `maros-next/docs/TRABAJO-2026-09-27.md` and the shared token contract in `src/styles/globals.css`.
- Next.js documents its integrated `experimental.viewTransition` option as not recommended for production; prefer the installed Motion layout/AnimatePresence APIs unless a verified stable path is found.
- Firefox in the existing Hyprland desktop is available for visual acceptance at a narrow 456px viewport; desktop-width review must still be performed during implementation. Source/build output alone is not sufficient for motion acceptance.
- Do not add or run test suites unless David explicitly requests them; run lint, typecheck, build, and direct runtime checks that are not tests.

## Priorities & phases
- P1: audit route/shared patterns; establish transition primitives; ship the route crossfade and high-value shared-element expansion/blur for tasks and attachment images; correct architecture ownership of shared preview UI.
- P1: apply systemic visual/interaction improvements to high-traffic Home, projects, leads, tasks, notes, reports, and finance flows where evidence justifies changes; preserve domain-specific dense tables and financial signals.
- P2: extend the proven patterns to remaining routes and public-note surfaces; keep exceptional layouts documented.

## Timeline & dependencies
- No deadline stated. Requires approval of the concrete implementation plan before code changes. Backend work is not a dependency under the current assumption.

## Assumptions
- The owner's explicit request authorizes a broad frontend UX review and high-value interaction/design changes once the plan is approved.
- Preserve the project-approved MARO Rev E/F design direction, compact CRM density, and English product content; the global Catppuccin preference applies to the desktop environment, not this separately branded CRM.
- Use installed Motion for route and local shared-element transitions; avoid experimental framework flags in production.
- Keep behavior changes limited to interaction clarity, accessibility, feedback, responsiveness, and concrete frontend defects that do not alter backend/domain contracts.
- Exception added 2026-10-11 at the owner's request: project list-to-detail handoff requires additional read fields, so add `/projects/v2/all` while retaining `/projects/all`; do not change project writes, permissions, financial calculations, or persisted behavior. Consumers are the Maros project-list query and project-detail route; rollback is restoring the frontend list path to `/projects/all` while the server endpoint remains additive.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear — owner wants a modern, coherent UX with crossfade/shared enlargement/blur |
| Users / actors | Clear — internal staff and external users; exact role groups are not needed for visual scope |
| Scope | Clear — all routes and shared owners inventoried; frontend experience only, with CRM domain/API behavior preserved |
| Out of scope | Partial — preserve approved identity and domain/API contracts; confirm below |
| Flows & behavior | Clear — route transitions, task detail, attachment image preview, reduced motion and responsive defects scoped in REQ-004 PLAN.md |
| Edge cases | Clear — direct links, reduced motion, responsive input, permissions, failures included |
| Acceptance criteria | Clear — criteria and manual verification are defined in REQ-004 PLAN.md |
| Constraints | Clear — current stack/design system and experimental Next transition caveat verified |
| Priorities & phases | Clear — ordered tasks and verification are defined in REQ-004 PLAN.md; awaiting owner plan approval |
| Timeline | Clear — no deadline stated; explicit plan gate before edits |

## Clarifications
### Round 1 — 2026-10-11
- Q → preserve the current MARO visual system and CRM semantics while making the experience modern? → A: yes; this follows the already-approved Rev E/F design decision and is captured in scope and constraints.
- Q → may the transversal scope include changes to finance/business behavior or backend contracts? → A: no; retain all domain, permission, persisted workflow, and API behavior.
- Visual evidence gathered from the running app: the existing Firefox window is 456px wide. Notes, Leads, Tasks and Calendar headings/filters can overflow or clip; the client scorecard compresses numeric columns until headings wrap vertically. Routes under `/projects` and `/leads` redirect to their canonical `construction` routes; server logs confirmed successful responses after the first malformed rapid URL attempt, so no missing-route defect is attributed.
- Source-level follow-up: those page headings share `src/components/shared/PageHeaderCard.tsx`; its description is not configured to wrap or constrain long text. The scorecard uses a six-column `ClientScorecardTable` without a locally scrolling wrapper, so the narrow viewport compresses money/status columns. The existing REQ-003 interaction inventory already covers all 59 route wrappers and will be reused as the route denominator rather than duplicated.
- Main-page route inventory: overview, calendar; projects (construction/roofing, completed, lost, QuickBooks import), project detail/report; leads (construction/roofing, lost), lead detail, contacts/customers/companies/review; tasks (board/list/mine/calendar/archive, detail, workspaces); notes (index/favorites/shared/trash/detail and public share/unlock/expired); finance (invoice scans, scan, transaction, receivables); reports (clients, QuickBooks backlog/estimated/invoiced/outstanding/paid/revenue, restoration visit/final, stale leads); settings (notifications/public links/QuickBooks/roles/users); login/about/privacy/meeting.
- Round 2 — 2026-10-11: David clarified that list data must be handed into `/project/[id]` automatically instead of fetching the detail endpoint. Implementation scope is cache-first client navigation plus an additive `/projects/v2/all` DTO; direct cold links retain a list-fetch fallback.
