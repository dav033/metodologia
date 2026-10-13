---
id: REQ-008
status: done
created: 2026-10-11
track: standard
---
# REQ-008 — Minimal clean UI and smooth motion

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The current visual treatment feels overdecorated and distracts from creating and reviewing a proposal. David wants a modern, clean interface with restrained styling and smooth, subtle animation.

**Success looks like:** Admin, sign-in, entry, and shared proposal screens use one coherent, quiet visual system; the comparison remains the visual focus; interactions still work on mobile and with reduced motion enabled.

## Users / actors / stakeholders
- David, managing prospects and proposals in the admin studio.
- Prospects, reviewing a shared proposal and comparing the current site with the prototype.

## Scope (in)
### US-1 (P1, Must) — Simplify the proposal studio
As David, I want the admin, sign-in, and entry surfaces to use a cleaner visual hierarchy so I can focus on proposal work.
**Acceptance:**
- Given any admin, sign-in, or entry page, when it is rendered, then layout, typography, controls, borders, and surfaces use a consistent minimal visual system.
- Given the current admin flows, when I navigate and edit proposals, then their existing behavior and information remain available.

### US-2 (P1, Must) — Simplify the shared proposal
As a prospect, I want the proposal to foreground the design comparison and useful information without decorative effects competing for attention.
**Acceptance:**
- Given a shared proposal, when I view it on desktop or mobile, then the comparison, findings, and proposal details remain clear and usable.
- Given a multi-page proposal, when I select a page or drag the comparison divider, then the existing interactions continue to work.

### US-3 (P1, Must) — Use calm, accessible motion
As a user, I want transitions to feel smooth without slowing down interaction or ignoring motion preferences.
**Acceptance:**
- Given a supported reveal or control transition, when it runs, then it uses short, subtle movement and opacity changes without layout shifts.
- Given `prefers-reduced-motion: reduce`, when the interface loads or changes state, then nonessential motion is removed or minimized.

### US-4 (P1, Must) — Compare without dragging
As a prospect, I want another way to set the comparison position so I can use a click, tap, or keyboard control instead of dragging the divider.
**Acceptance:**
- Given the comparison, when I change the position range control, then the divider and visible proposal area update to the same percentage.
- Given the divider is moved with pointer or keyboard, when its position changes, then the range control reflects the current position.

## Out of scope
- Changes to proposal data, authentication, sharing, capture, prototype rendering, routes, or the existing divider interaction.
- New animation or UI libraries, new colors outside the existing Catppuccin Mocha palette, or a light theme.
- Deploying or publishing the redesign.

## Requirements
- R1. When any admin, sign-in, entry, or shared-proposal screen renders, the system shall use consistent spacing, typography, control, surface, and border tokens with restrained decoration.
- R2. When an element is elevated, the system shall communicate hierarchy primarily through spacing, contrast, and borders; gradients, glow, blur, and large shadows shall not be the default treatment.
- R3. When users use existing proposal, authentication, navigation, and comparison controls, the system shall preserve their current behavior.
- R4. When supported UI transitions run, the system shall use short, subtle transitions that do not delay input or cause content layout shifts.
- R5. When reduced motion is requested, the system shall suppress nonessential transitions and reveals.
- R6. When the interface is used at narrow viewport widths, the system shall remain readable and keep existing controls reachable.
- R7. When the comparison is changed, the system shall provide an equivalent range control that supports pointer click/touch and keyboard input without requiring a drag gesture.

## Edge cases & errors
- Long business names, findings, and deliverable text must wrap without clipping.
- Comparison controls and embedded prototype remain usable at mobile widths.
- The comparison range and divider remain synchronized across pointer and keyboard changes.
- Reduced-motion styling must also cover hover and reveal transitions.

## Constraints
- Preserve Catppuccin Mocha with mauve/lavender accents as required by global workspace instructions.
- Reuse the existing Astro/CSS/Motion setup; no new dependencies.
- Preserve unrelated work already present in the working tree.
- Do not run tests unless David asks for verification; do not deploy without explicit instruction.

## Priorities & phases
- MVP: shared tokens and restrained styling across admin and public proposal, plus subtle accessible transitions.
- Later: none identified.

## Timeline & dependencies
- No external dependencies. Implementation follows approval of the plan.

## Assumptions
- “La UI” means the admin experience, sign-in and entry pages, and the prospect-facing shared proposal, not just one surface.
- Retain the dark palette and mauve/lavender accents; “less fancy” refers to reducing effects and excessive decoration, not changing brand colors.
- Keep meaningful feedback/status colors and focus indicators for usability.

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
| Timeline | Clear |

## Clarifications
- Q: Which UI surfaces should be included? → A: Admin, sign-in, entry, and shared proposal together, based on the broad request to simplify “la UI”.
