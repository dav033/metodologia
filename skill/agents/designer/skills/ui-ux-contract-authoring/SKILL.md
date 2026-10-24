---
name: ui-ux-contract-authoring
description: Author or revise a versioned UI/UX contract for a UI subplan, with implementable view specifications and observable visual acceptance criteria.
---

# UI/UX contract authoring — Designer private skill

Use this skill for every `kind: design` task. The contract is mandatory for UI work, whether or not the project enables a preview. Write the contract under `design/contracts/`; the executor enforces Designer's `design/**` write boundary.

## Author the contract

Start from the approved SPEC and PLAN. Identify the subplan, requirement ids, success outcomes, views, flows, existing design system, platforms and supported breakpoints. Reuse established decisions. Record unknowns that materially affect user behavior or design as questions; do not fill them with guesses.

Create `design/contracts/<contract-id>@v<N>.md` with these sections:

1. **Identity and traceability** — contract id and version, status (`draft` or `approved`), subplan id, requirement ids, source SPEC/PLAN revision, owner and date.
2. **Purpose and users** — each view's user goal, context and observable success.
3. **Information architecture and hierarchy** — content groups and order; primary, secondary and supporting information; progressive disclosure and rationale for major emphasis.
4. **Design system and visual language** — existing semantic tokens, component patterns, typography roles, spacing, surfaces, borders, icon use, motion and focus treatment. Cite existing token names. Propose new semantic tokens only when necessary, with values or definitions and intended use. Do not add arbitrary per-component values where a system exists.
5. **Navigation and interaction model** — entry and exit points, destinations, persistent navigation, focus behavior and control outcomes.
6. **Flows** — numbered or linked steps for each important user goal, including decisions, validation, recovery and completion.
7. **View specifications** — for each view, give structure, hierarchy, component roles, visible copy, actions, data shown, responsive behavior and references to relevant flows and states. Copy must communicate the action or next step and follow the product's existing voice and terminology.
8. **States** — cover every applicable state: loading, empty, error, success, disabled, validation, permission-denied, partial/stale data and offline or pending where relevant. State what appears, what can be done, how recovery works and how transitions occur. Mark genuinely inapplicable states with a reason.
9. **Responsive behavior** — name supported breakpoints or content-driven breakpoint rules; define layout changes, navigation changes, overflow behavior and component adaptations at each. Do not assume device categories without project evidence.
10. **Accessibility targets** — target WCAG 2.2 AA for applicable content and interactions. Specify semantic roles, keyboard operation, visible focus, accessible names, status/error announcements, contrast requirements, reflow/zoom, target size and reduced-motion behavior where relevant. State exclusions or items requiring rendered verification; do not claim conformance from a design description alone.
11. **Visual acceptance criteria** — write criteria a Reviewer can check against rendered pages. Every criterion has an id, breakpoint, state, and one observable expectation. Keep each expectation independently checkable.
12. **Open questions and assumptions** — list unresolved questions separately from confirmed decisions; identify the decision owner. Do not hide assumptions inside the specification.

Use this acceptance-criteria format:

```markdown
| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | 360–767 px | empty | The empty-state explanation and “Create project” action are visible without horizontal scrolling. |
```

The breakpoint and state must match the project's vocabulary and supported range. An observable expectation describes what appears, where it appears, or what happens after an action; avoid subjective checks such as “looks polished.”

## Review before handoff

- Every requirement assigned to the UI subplan maps to at least one view, flow or criterion.
- Every view needed by the flows is specified; navigation destinations are accounted for.
- All applicable states are defined, and excluded states have reasons.
- Responsive behavior covers all supported ranges and does not rely on unstated device assumptions.
- Tokens and components match the existing system or are proposed explicitly.
- Accessibility targets are concrete and labeled as targets awaiting rendered verification where necessary.
- Every acceptance criterion has a unique id, breakpoint, state and observable expectation.
- Implementers can identify what to render and how to evaluate it without making material design decisions.
- The version path, changelog and approval state follow `design-contract-versioning-and-impact`.

If required information is missing, leave a draft and report the precise question. Do not mark the contract approved or ready for implementation.
