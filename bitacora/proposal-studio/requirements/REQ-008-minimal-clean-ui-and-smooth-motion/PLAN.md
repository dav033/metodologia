---
id: REQ-008
status: done
created: 2026-10-11
---
# REQ-008 — Implementation plan

## Outcome
A quieter, modern interface across the admin studio and public proposal, with the comparison still taking center stage and motion reduced to subtle, accessible feedback.

## Plan
1. **Set the visual direction**
   - Keep the existing dark Catppuccin palette and mauve/lavender accents.
   - Simplify shared styling in `src/styles/global.css`: remove decorative ambient gradients/glows/orbits, reduce layered backgrounds and large shadows, tighten typography hierarchy, and use restrained borders and consistent radii.
   - Simplify admin styling in `src/styles/admin.css`: flatten the sidebar/top-level surfaces and cards, reduce over-rounded controls, shadows, backdrop blur, and decorative gradients; preserve clear active, focus, and status states.
2. **Reduce visual noise in components**
   - Replace the pointer-following Spotlight treatment on proposal findings with static, clean cards and ordinary hover/focus feedback.
   - Keep the existing draggable comparison behavior and add a synchronized native range control as a click/touch/keyboard alternative.
   - Prioritize the proposal list ahead of secondary dashboard metrics; retain all metrics and make the update date available on mobile.
3. **Tune motion and responsiveness**
   - Keep the existing Motion implementation; shorten and soften reveal/hover transitions without delaying interaction.
   - Ensure `prefers-reduced-motion` suppresses all nonessential movement, including component hover/reveal effects.
   - Review responsive styling for entry, sign-in, admin, and shared proposal so navigation, comparison, and controls remain usable on narrow screens.
4. **Document and inspect the result**
   - Review the diff for accidental changes to behavior and for overlap with pre-existing work.
   - Do not run automated tests unless David explicitly asks; do not deploy or commit.

## Files likely to change
- `src/styles/global.css`
- `src/styles/admin.css`
- `src/components/react/SpotlightCards.tsx`
- `src/components/react/ProposalComparisonSlider.tsx`
- `src/components/react/ProposalPageSwitcher.tsx`
- `src/pages/admin/index.astro`
- `src/pages/index.astro`
- `src/scripts/reveal-client.ts` (only if the existing timing cannot be tuned in CSS)
- Potentially `src/pages/s/[token].astro` or admin page markup, only if CSS alone cannot provide the agreed hierarchy.

## Acceptance checks
- Entry, sign-in, admin, and shared proposal look like one restrained design system and retain legible hierarchy.
- Shared proposal still presents the multi-page comparison prominently; page selection and divider dragging are preserved, and range control changes synchronize with the divider.
- Existing functional forms, links, navigation, and proposal details remain present.
- Narrow screens retain reachable controls and readable content.
- Reduced-motion preference removes nonessential movement.
- Dashboard proposals remain the primary content; metrics and last-updated information remain available at mobile/tablet sizes.
- No new dependency, auth/data/workflow change, commit, or deploy.

## Risks and mitigations
- **Risk:** Simplifying styles unintentionally reduces visibility of state and actions.
  **Mitigation:** Preserve contrast, focus rings, active navigation, and explicit button hierarchy.
- **Risk:** Shared CSS changes disturb the in-progress comparison/capture work.
  **Mitigation:** Keep edits scoped to visual rules and review the existing diff before editing.

## Approval
Approved by David on 2026-10-11; implementation complete on 2026-10-11.
- 2026-10-11 23:08 plan APPROVED (terminal)
