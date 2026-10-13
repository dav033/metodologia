---
id: REQ-004
status: done
created: 2026-10-11
track: standard
---
# REQ-004 — Proposal Studio visual system and motion

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Proposal Studio already has its primary flows, but its public proposal and admin overview need a more cohesive, polished visual language and purposeful motion. David asked to use components from 21st.dev, add a separate component library, and add animation.

**Success looks like:** the public comparison/proposal and admin overview share a consistent, responsive visual system; both use the selected UI component library where it improves the interface; the public proposal uses a selected 21st.dev component; motion is present but respects reduced-motion preferences and does not obstruct the prototype comparison or controls.

## Users / actors / stakeholders
- David, who prepares and manages proposals in the private admin.
- Prospects, who read and interact with a public proposal and its live prototype.

## Scope (in)
### US-1 (P1, Must) — Improve the public proposal experience
As a prospect, I want a polished proposal page with restrained motion so that the comparison and proposed solution feel clear and credible.
**Acceptance:** The public share URL and proposal preview, comparison, findings, and summary use a consistent design system; key content enters with short, non-blocking transitions; the live prototype and divider remain fully interactive; reduced-motion preference disables nonessential motion.

### US-2 (P1, Must) — Add a component from 21st.dev
As David, I want to use a polished community component from 21st.dev in the product.
**Acceptance:** One MIT-licensed 21st.dev Spotlight component is adapted into a React island for proposal finding cards on public share URLs; it is useful on pointer devices, remains understandable on touch devices, and does not rely on pointer-tracking when reduced motion is requested. Its source and license are attributed.

### US-3 (P1, Must) — Add a separate component library
As David, I want a reusable component library alongside 21st.dev so future screens can use consistent accessible primitives.
**Acceptance:** Starwind UI is installed as the Astro-native component library and visibly used for suitable buttons, badges, or cards on the public proposal and admin overview, themed to the existing mauve/lavender dark palette; unused components are not bulk-loaded.

### US-4 (P1, Must) — Polish the admin overview
As David, I want the private overview to feel consistent with the proposals I share.
**Acceptance:** The admin overview uses the same tokens, card treatment, typography, spacing, responsive behavior, and motion rules as the public proposal.

## Out of scope
- Replacing the Astro application with React or hydrating every page.
- Redesigning editor, integrations, settings, auth, or database behavior.
- Replacing the working draggable comparison, changing prototype sandboxing, or adding analytics.
- Decorative looping motion, autoplay video, WebGL, or heavy background effects.
- Installing every component from either library.

## Requirements
- R1. When a visitor opens a public share URL, the application shall render a consistent responsive visual system around the existing comparison, findings, deliverables, estimate, and contact action.
- R2. When a visitor views findings on a supported pointer device, the application shall show a restrained Spotlight hover treatment based on the MIT-licensed 21st.dev component; on touch devices it shall keep a static visual affordance.
- R3. When a visitor requests reduced motion, the page shall omit nonessential entry, hover-tracking, and transform animations while preserving all content and controls.
- R4. When a visitor uses the comparison divider or live prototype, the new visual components shall not capture pointer input outside their own controls or alter the iframe's interaction.
- R5. When an administrator opens the overview, Starwind UI cards and buttons shall use the product's design tokens and preserve accessible names, focus states, links, and status text.
- R6. When proposal content is long or the viewport is narrow, the pages shall not clip text, cause horizontal overflow, or hide primary actions.
- R7. The project shall include only the Starwind UI components it uses and hydrate React only for the 21st.dev Spotlight island.

## Edge cases & errors
- If JavaScript is delayed or disabled, core proposal content, comparison fallback link, admin text, and navigation remain in server-rendered markup; enhancement-only motion may not run.
- When reduced motion is enabled, no required content starts hidden or waits for animation to become readable.
- When pointer hover is unavailable, finding cards remain legible without Spotlight.
- If animation initialization fails, content remains visible and usable.
- Long findings, absent optional proposal sections, keyboard focus, 320 px viewport, and the prototype iframe's pointer interactions remain supported.

## Constraints
- Keep Astro/Vercel SSR and existing database/auth/API contracts.
- Use current dark palette (Catppuccin Mocha with mauve `#cba6f7` and lavender `#b4befe`) and Spanish user interface.
- Use React only for the selected React island; leave Astro routes and existing admin scripts Astro/vanilla TS.
- Use the `motion` package for lightweight HTML entry animation and the selected React component; keep dependencies pinned through package-lock.
- Starwind Astro components are kept as editable project source; avoid installing its full component set.
- Public proposal content and prototypes remain untrusted data; no extra HTML injection or sandbox permissions.

## Priorities & phases
- MVP: public proposal visual pass, Spotlight finding cards, Starwind cards/CTA, admin overview visual pass, accessible motion, responsive checks.
- Later: apply the system to editor, integrations, settings, and login only if the first pass proves useful.

## Timeline & dependencies
- No deadline specified. Depends on the existing Astro workspace and its current user-facing proposal/admin routes.

## Assumptions
- The user's blanket authorization to proceed autonomously accepts the recommended choices from Round 1: use a limited React island for selected 21st.dev components with a native Astro-compatible library, and prioritize public proposals plus the admin overview.
- Starwind UI is the separate component library because it supplies editable Astro-native components and accessible primitives. Its Tailwind v4 styling toolchain is added without migrating existing CSS; only selected components are included.
- Use Motion's `inView` for short section entry transitions and disable those effects for `prefers-reduced-motion: reduce`.
- Use the MIT-licensed Spotlight component by Julien Thibeaut from the 21st.dev Motion Primitives catalog, adapted to this product and attributed in source/docs.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Deferred (none provided) |

## Clarifications
### Round 1 — 2026-10-11
- Q: How should 21st.dev and the separate component library be combined? → A: Use a native Astro component library for the shared base and a few selected 21st.dev components as React islands.
- Q: Which views should be included? → A: Public proposals first and the admin overview with the same visual system.
- The user authorized autonomous continuation. After comparing the official installation paths, Starwind UI was selected over Web Awesome to keep the library Astro-native and source-owned; this changes the specific initial recommendation but preserves the approved direction.
