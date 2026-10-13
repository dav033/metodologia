---
id: REQ-009
status: done
created: 2026-10-11
track: standard
---
# REQ-009 — Material 3 redesign for complete proposal workflows

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The previous UI pass mostly changed surface decoration. The real proposal workflow still feels inconsistent and difficult, especially the long create/edit forms, dynamic page rows, capture uploads, and save/publish/share actions. David explicitly asked for a complete redesign based on current Material guidance and UX, not another landing-page-only polish.

**Success looks like:** The entire application has one coherent Material 3-inspired interface adapted to Catppuccin Mocha. Users can create, edit, compare, publish, and share proposals with clear structure, labels, progress, useful validation, and visible action feedback across desktop and mobile.

## Users / actors / stakeholders
- David, the sole administrator preparing and managing proposals.
- Prospects using shared proposal pages and the comparison control.

## Scope (in)
### US-1 (P1, Must) — Use a consistent adaptive application shell
As David, I want every admin page to share understandable navigation and page structure so that I can focus on proposal tasks.
**Acceptance:**
- Given dashboard, create/edit, GitHub integration, or account entry, when viewed at desktop/tablet/mobile widths, then navigation, breadcrumbs/page titles, active location, and primary actions remain consistent and reachable.
- Given public entry, login, and shared proposals, when rendered, then they share the same typography, spacing, surface, focus, and motion rules without admin-only navigation.

### US-2 (P1, Must) — Make forms understandable and recoverable
As David, I want proposal and GitHub forms to guide input and explain errors beside their fields so I can complete work without guessing.
**Acceptance:**
- Given create/edit fields, when I enter data, then each control has a visible label, concise instruction where needed, and stable, useful focus state.
- Given invalid or failed saves/uploads/imports, when the action returns, then entered data remains, errors identify the affected task/field and how to fix it, and focus moves to the error summary or field.
- Given save/publish/import requests are running, when I activate the action, then duplicate submission is prevented and progress/success/failure is visible.

### US-3 (P1, Must) — Support the actual proposal workflow clearly
As David, I want proposal data, comparison pages, captures, preview, and sharing to be organized in task order so each step is easy to understand.
**Acceptance:**
- Given proposal creation/editing, when I work through the page, then required business/site/capture fields appear before optional prototype/link actions and dynamic page management is clearly grouped.
- Given additional pages, when adding/removing a page or capture, then page identity, required work, removal, and upload state are clear and keyboard accessible.
- Given draft or published status, when reviewing actions, then save, publish, duplicate, archive, and create/revoke share link have clear hierarchy and status-aware feedback.

### US-4 (P1, Must) — Keep the prospect experience focused and usable
As a prospect, I want to compare the current site and proposed prototype easily, including on a phone and without dragging.
**Acceptance:**
- Given a public proposal, when I switch a page or move the divider, then the selected current capture and matching prototype remain paired and controls explain their values.
- Given a narrow viewport or reduced-motion preference, when I view or interact with the page, then content remains readable and motion is reduced.

## Out of scope
- Data-model, authentication provider, GitHub permissions, proposal lifecycle, sharing policy, or capture behavior changes.
- New UI framework/component dependency or a light theme. Keep Catppuccin Mocha and mauve/lavender accents.
- Sending email, deploying, committing, or pushing.

## Requirements
- R1. All public/admin routes in scope shall use a coherent, adaptive Material 3-inspired visual system with the existing Catppuccin palette.
- R2. Each visible form field shall have a stable label association; instructions and required/optional status shall be explicit where needed.
- R3. If client/server validation fails, the page shall preserve user input and provide concise errors that point to the associated field or task.
- R4. While network mutations run, the corresponding action shall expose progress and prevent duplicate requests; on completion it shall expose success or recovery guidance.
- R5. Proposal forms shall present required information before optional or later-stage work, with clear groups for pages, preview, publishing, and sharing.
- R6. Dynamic page/capture controls shall remain understandable and keyboard usable after add/remove operations.
- R7. Navigation, forms, statuses, dialogs, and public comparison shall work without horizontal overflow at compact and wide viewport sizes.
- R8. Nonessential motion shall respect `prefers-reduced-motion`.
- R9. Existing authorization, proposal lifecycle, expiry, revocation, and storage behavior shall remain unchanged.
- R10. Share creation shall accept an optional operation UUID, use it to identify the created link, and return a stable conflict if the same operation is repeated. The admin client shall persist the operation until it confirms that the one-time URL was copied or explicitly saved; recovery shall identify only that operation's link.

## Edge cases & errors
- Empty proposal list and a new proposal with no ID yet.
- Many pages (up to the existing limit), long business/page names, and missing screenshots.
- Save succeeds but image upload fails; display persisted draft state and actionable retry.
- Invalid user input, conflict/duplicate slug, timeout/network failure, and failed publish/import/archive/share.
- Screen reader/keyboard use, 320 px viewport, zoomed text, and reduced motion.

## Constraints
- Keep Astro SSR and current source-owned UI components; no new dependencies.
- Preserve global Catppuccin Mocha visual preference.
- Preserve all unrelated working-tree changes.
- User authorized the redesign and adversarial UX audit in chat on 2026-10-11. Do not deploy/commit/push.
- Focused browser and automated verification are authorized by the request to audit usability; do not alter checks to achieve a pass.

## Priorities & phases
- P1: application shell, create/edit forms, validation and action states, integration flow.
- P1: dashboard, login, public entry and comparison surfaces.
- Audit with fresh antagonistic visual and form-flow reviewers; remediate major/high findings before close.

## Timeline & dependencies
- Start after David's explicit instruction on 2026-10-11. Material/W3C/GOV.UK reference notes are captured alongside this spec.

## Assumptions
- "Todo" covers existing public entry/login, admin dashboard, proposal creation/editing, GitHub integration, share controls, and public proposal pages; `/admin/settings` intentionally redirects and remains so.
- "Material" means Material 3 patterns for adaptive layout, clear hierarchy, field states and feedback, not importing Google's component library or copying its visual theme.
- Catppuccin Mocha remains mandatory from global workspace instructions.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- Q: Which surfaces count as "all UI"? → A: All current public and admin routes, especially forms and usability, per David's 2026-10-11 instruction.
- Q: Theme/framework constraints? → A: Retain Catppuccin Mocha and the current Astro stack; adapt Material 3 patterns without adding a component dependency.

## Authorization
- David directed implementation and multiple proactive antagonistic audits on 2026-10-11; this is the execution approval.

## Completion
- Implemented across dashboard, create/edit, integrations, sign-in/public pages, and comparison surfaces.
- Responsive browser verification covered 320, 390, 620, 681, 850, 1024, and 1440 px; focused share recovery covers network loss, HTTP 500, failed status read, reload, delivery confirmation, and two tabs.
- Two fresh antagonistic auditors re-reviewed the final share recovery and UI flows and returned SOUND.
- `npm run build` and the focused Playwright E2E suite passed on 2026-10-12. The full build includes Astro diagnostics, ESLint, Prettier, Vitest, and Astro/Vercel production build.
- Visual inspection used local Playwright screenshots and browser automation. Native CUA browser control was unavailable in this session.
- No commit, push, or deployment was performed.
