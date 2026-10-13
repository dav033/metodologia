---
req: REQ-004
status: in-progress
created: 2026-10-11
---
# Plan — REQ-004 — Transversal Maros UX and motion refinement

## Approach
Keep the approved Rev E/F tokens and use the already-installed Motion library for short, interruptible opacity and layout transitions. Avoid the experimental Next.js View Transition flag and avoid a blanket redesign: first audit every route, then fix shared owners and the highest-impact responsive defects found in the running app. Move the shared file viewer under attachments, because both attachments and leads consume it.

## Global constraints
- Preserve the approved charcoal/elevation/mint identity, contrast, compact density, finance colors, permissions, domain rules, persisted behavior, and backend contracts.
- Keep existing uncommitted REQ-003 work intact; no commit, deploy, push, or merge.
- Exclude login, public-note routes, redirects, and first paint from route animation; reduced-motion users get immediate state changes.
- Image shared-element animation applies only to image previews. PDFs and documents keep their existing viewer paths. Task detail must work without a source card.
- Use no new dependency or experimental Next.js flag. Do not add or run test suites; perform lint, typecheck, production build, and focused browser checks.

## Tasks
- [ ] T1 — Reconcile the existing 59/59 route inventory (`REQ-003/INTERACTION-INVENTORY.md`) against current `src/app/**/page.tsx`, then add visual/interaction evidence for overview/calendar, projects, leads/contacts/customers, tasks/workspaces, notes/public notes, finance, reports, settings, and auth/public/legal routes; record deliberate exceptions and rank issues · files: all `src/app/**/page.tsx`, `src/app/AppShell.tsx`, shared UI and feature page owners · verify: route assertion plus screenshots/manual walkthrough at desktop and narrow viewport · covers: R1, US-1, US-3
- [x] T2 — Add a shared authenticated-route crossfade after destination content is ready; keep interaction immediate and exclude first load, redirects, login, public notes, and reduced motion · files: `src/app/AppShell.tsx`, motion/presentation utility if needed · after: T1 · verify: browser navigate, back/forward, rapid repeated navigation, reduced-motion emulation; inspect URL, focus and scroll · covers: R2, R4, R5
- [x] T3 — Move the reusable preview surface from `features/leads` to `features/attachments`; animate image thumbnail ↔ viewer with a stable per-file layout id and softened/blurred backdrop; preserve PDF/DOCX viewer behavior and close/focus semantics · files: `src/features/leads/presentation/pages/sections/FilePreviewModal.tsx`, attachment sections and their imports, `src/components/ui/dialog.tsx` · after: T1 · verify: open/close images by pointer and keyboard; open a PDF/document; repeat with reduced motion and a missing image source · covers: R3, R4, R6
- [ ] T4 — Add the task card ↔ detail surface shared-element expansion, with a normal entrance when no board/list source is mounted · files: `src/features/tasks/presentation/molecules/TaskCard.tsx`, `src/features/tasks/presentation/organisms/TaskDetailSheet.tsx`, board/list owners · after: T1 · verify: open/close by pointer and keyboard; check DnD, nested actions, child-task navigation, direct detail route, focus return, and reduced motion · covers: R3, R4, R5
- [ ] T5 — Correct the route-audit-confirmed mobile overflow at its shared owner (page headings/toolbars/tabs and data tables), starting with Reports, Notes, Tasks, Leads, Projects and Calendar; apply the same fix to other affected routes, retaining local horizontal table scrolling and all finance values · files: `src/components/shared/PageHeaderCard.tsx`, report/table shell and affected feature owners recorded by T1 · after: T1 · verify: browser at 456px and desktop width; ensure no page-level horizontal overflow and controls/data remain reachable · covers: R1, R6, US-1, US-3
- [ ] T6 — Refine common overlay timing/backdrop blur and loading, empty, and error affordances only where the audit proves an inconsistency; retain Radix focus trapping, nested overlay priority, scroll restoration, and all existing states · files: shared Dialog/Sheet/AlertDialog and audited shared state components · after: T1 · verify: nested dialogs/popovers, Escape/close, keyboard focus, responsive layout, and reduced motion in browser · covers: R3-R6, US-3
- [ ] T7 — Reconcile the route inventory against the repository, finish the full browser walkthrough, run frontend lint/typecheck/build, review the diff for unrelated changes, and update Bitácora with verified outcomes and remaining issues · files: affected frontend files; `~/bitacora/maros/` · after: T2,T3,T4,T5,T6 · verify: `npm run lint`, `npm run typecheck`, `npm run build`; manual browser walkthrough · covers: R1-R7
- [x] T8 — Render `/project/[id]` from the selected project already cached by `/projects`, without a route-level details request or stale-list refetch; include detail-only lead/contact fields in an explicit versioned list contract and reuse cached financial summary. Cold direct links may load the versioned list as fallback · files: project route/cache adapter, project frontend mapper, versioned projects list endpoint/mapper · after: existing project-name layout IDs · verify: trace warm navigation and confirm zero `/projects/:id/details` and zero list refetch; verify cold direct link and contract compatibility · covers: R8

## Verification
Walk all frontend page routes and shared flows, including desktop and 456px layouts; verify client navigation crossfade, image and task shared-element transitions, direct-route fallbacks, PDF/document previews, dialog blur, reduced motion, DnD, keyboard/focus, and no page-level horizontal overflow. Reconcile all routes with the source inventory, then run `npm run lint`, `npm run typecheck`, and `npm run build`. No test suites are added or executed.

## Rulings
- T2: Use installed Motion instead of React/Next View Transitions — the Next flag is experimental and user-visible snapshots need explicit reduced-motion and interaction handling — cost if wrong: medium.
- T5: Keep wide financial tables horizontally scrollable inside their table surface on narrow screens; do not compress or truncate decision-critical amounts — cost if wrong: low.
- Browser review uses the existing Firefox window's new tab at 456px; initial 404 captures came from malformed fast URL entry during dev compilation and were discarded after logs confirmed valid route responses — cost if wrong: low.
- Existing REQ-003 uncommitted changes are user work and remain in place — cost if wrong: high.

## Progress log
- 2026-10-11: Verified local frontend/API responses; audited App Router inventory, inspected the live dashboard and tasks, notes, leads, projects, document scans, calendar, and client-scorecard pages in Firefox; confirmed narrow-layout clipping and compiled valid route responses from server logs. No source files changed for REQ-004.
- 2026-10-11: Continued implementation after David's direct request to implement the reviewed UX work and run the local server. Added the authenticated route crossfade, task/image shared-element transitions, blurred overlays, reduced-motion fallbacks, shared attachment preview ownership, page-header wrapping, and local scrolling for the client scorecard. The existing local app returns HTTP 200 at `http://localhost:3000`; the API docs return HTTP 200 at `http://localhost:4000/api/docs`.
- 2026-10-11: `npm run lint` passed with 0 errors and 177 warnings; `npm run typecheck`, `npm run build`, and `git diff --check` passed. The build compiled all app routes and generated 41 static pages. A screenshot and visible text were captured from the isolated agent Firefox profile at 1440px; the screenshot was in a loading state, so visual acceptance for transitions, overlays, and the 456px layout remains open. The installed Firefox MCP still targets port 9222, while the isolated agent Firefox listens on 9223; no interaction was sent to the personal Firefox. No tests, commit, push, merge, or deploy were performed.

- 2026-10-11: Investigated David's report that task detail had no animation and felt poor to use. Root cause: task card/detail shared `layoutId` ran inside the authenticated route's `AnimatePresence mode="sync"` without a coordinating `LayoutGroup`; the dialog also dropped its task/source state immediately on close. Added an app `LayoutGroup`, verified source-card presence before using the shared ID, added a normal detail entrance fallback, kept the URL/task mounted through the Radix exit interval, and added restrained card hover/press feedback. Prevented clicks/Enter from nested task controls from activating the parent card.
- 2026-10-11: Browser QA in an isolated headless Chromium profile on the local app loaded 41 existing task cards without changing CRM data. Measured card hover transform, task-detail expansion from the card's position/scale to the dialog surface, Radix open/close animation, and URL return to `/tasks`. At 456px, `documentElement.scrollWidth` matched the viewport width (456px).
- 2026-10-11: The same browser surfaced an actual sidebar hydration mismatch from the `AppSidebar` Suspense boundary: server markup contained the sidebar while the client used the null fallback. Removed that unnecessary boundary; after reload the route showed no hydration exception or issues badge and the task cards still loaded. `npm run lint` passed with 0 errors/177 warnings; `npm run typecheck`, `npm run build` (41 generated static pages), and `git diff --check` passed. No tests were run. The full route-by-route visual walkthrough in T7 remains open.

- 2026-10-11: Correction to the hydration diagnosis: removing the AppSidebar Suspense boundary fixed the null-fallback mismatch, but the earlier clean-profile check missed a second mismatch caused by synchronous localStorage initialization. AppSidebar now starts from server-safe defaults, reads only boolean group values after hydration, and avoids writing defaults before that read completes. Reproduced stored `{Leads:false,Projects:false}` in isolated Chromium against `localhost:3000/tasks`: no Next overlay or page errors, 41 task cards loaded. Hover transform measured at scale 1.01 / y -2px; task detail opened with an in-progress opacity/position/scale transition and closed after Escape. Full ESLint passed (0 errors, 177 warnings), typecheck passed, and `git diff --check` passed. A production build was not rerun because the active dev server shares `.next`; a previous build passed before this small sidebar change. The correct agent Firefox profile is on 9223, but the loaded connectors cannot attach: one points at 9222 and direct BiDi reports an occupied session. No personal Firefox was accessed. T7's complete route walkthrough remains open.

- 2026-10-11: Cross-route runtime sweep uncovered a real contact-detail defect: API contact `251` returns `notes` as a plain string, while related project `notes` fields can contain structured QuickBooks/import metadata objects. `ContactHttpRepository.getDetails` had returned unvalidated `any`; `ContactNotesSection` then called `.map` on the string. Added a Zod boundary schema and explicit mapper: single legacy contact strings become one display note; structured non-text project metadata is omitted from the notes presentation with a warning that reports field/key names but no values. `ContactDetails` now has a typed repository return. Direct API-to-mapper check passes (1 contact note, 4 leads), and the authenticated SSR/browser route renders its notes card at 456px with no page exception or horizontal overflow.
- 2026-10-11: Initial route audit reconciled 59 inventory entries. It reached the project/report area before being stopped because Next dev reached ~12 GB RSS and the host fell to ~3.4 GB available. A 10-route 456px check then passed with no page-level overflow or page errors; leads, contacts and tasks retain local scroll containers. The desktop run is partial: some dynamic route IDs were examples rather than verified valid records; the public note token was intentionally invalid; compile timeouts and an HMR missing-chunk error prevent closing T1/T7. Keep those items open.
- 2026-10-11: Full lint passed (0 errors, 176 warnings) and typecheck passed after the contact adapter change; `git diff --check` passed. The local web and API services are active. Crossfade/image-preview interaction verification and a production build remain open; do not mark REQ-004 complete yet.

## Progress update · route hydration mismatch
- Reproduced two React hydration warnings on `/tasks`; both were Radix IDs under the authenticated shell and task create dialog. A controlled browser isolation showed the mismatch was associated with the route animation tree. Removed the global `LayoutGroup` from `RouteTransition` while retaining `AnimatePresence` and the fade.
- After Next finished recompiling, a fresh Chromium context loaded `/tasks` with HTTP 200, zero hydration warnings, and matching server/client Radix IDs. A separate client navigation sample measured both outgoing/incoming layers at opacities 0.17/0.83, 0.04/0.96, then 0/1, confirming the crossfade remains.
- Targeted ESLint reported 0 errors and one existing `no-explicit-any` warning in `contact/infra/http/mappers.ts`; `npm run typecheck` and `git diff --check` passed. No production build was run because the active development server shares `.next`; no test suites were run.
- T2/T4 and T7 remain open pending the remaining back/forward, reduced-motion, task shared-element, focus, and full route walkthrough checks.

## Progress update · task board loading investigation
- Rechecked the running worktree and local services: web `/tasks` and API docs return HTTP 200. The local task board endpoint itself returns HTTP 200 with 41 tasks across statuses when called directly.
- The rendered `/tasks` UI still showed the board skeleton after 3 seconds, and the browser emitted no task-board endpoint request. `useInstantTasksBoard` reports a pending/fetching query during SSR, but the client-side query invocation and retry path remain unresolved; do not count task animation verification as complete until the board renders and interactions work.
- A fresh full reload after the route transition recompilation matched server/client Radix IDs and emitted zero hydration warnings. Route crossfade remains measurable with incoming/outgoing layers overlapping. The active dev server has high memory use and slow route recompiles; do not restart it without owner approval.

## Progress update · shared project identity
- Inspected `/projects` → `/project/[id]`: the client list is in TanStack Query, while the server detail route independently loads a richer project DTO. App Router does not pass the selected row automatically. Added a project-name `layoutId` across desktop/mobile list presentation and the detail heading, preserving reduced-motion behavior and the full detail fetch.
- Targeted ESLint passed with 0 errors and 3 existing `no-explicit-any` warnings in `ProjectDetailsPage.tsx`; typecheck and `git diff --check` passed. Browser verification remains open; T1/T7 remain incomplete.
- The project-detail loading skeleton now reads the selected list row from TanStack's existing client cache and renders the matching responsive `layoutId` before the richer detail response arrives. The detail request remains for overview, attachments, payments and QuickBooks data. Targeted ESLint, typecheck and `git diff --check` pass; browser animation verification remains open.

## Progress update · task board first render
- `/tasks` now attempts to server-load its unfiltered board and seed the matching normalized TanStack query. Filtered searches and non-board views do not receive that data. Next compiled the route and returned HTTP 200, but an isolated Chromium session redirected to Dashboard without an authenticated session; its 43 HTML markers did not prove rendered task cards. Authenticated behavior remains unverified.
- Full lint passed (0 errors/173 warnings), typecheck and `git diff --check` passed. Browser hydration/motion checks remain open; T4/T7 remain incomplete.
- Projects' desktop row and mobile card now use distinct `layoutId`s paired with responsive detail targets, so the CSS-hidden copy cannot compete for the active shared element. Targeted ESLint and typecheck pass; browser animation verification remains open.

## Progress update · project detail mobile header
- Changed the project-detail header from a rigid single row to a stacked mobile layout; long project identities can wrap and action buttons wrap across rows. Updated the loading skeleton to keep the same responsive geometry. Targeted ESLint, typecheck and `git diff --check` pass. Browser viewport evidence remains open; T5/T7 remain incomplete.

## Progress update · detail tab visibility
- `DetailTabsBar` now scrolls its active tab into view within its horizontal viewport when URL state, pointer or keyboard changes the selection, including initial deep links. This applies to lead and project details, preserves nowrap behavior, and respects reduced motion. ESLint targeted, typecheck and `git diff --check` pass; visual mobile verification remains open (T5/T7).

## Progress update · shared toolbar width
- `PageToolbarCard`, used across tasks/leads/projects/contacts/companies, now constrains its root and flex rows to the available width (`w-full`, `min-w-0`, `max-w-full`) so minimum-width controls wrap inside the toolbar instead of expanding the page. Targeted ESLint, typecheck and `git diff --check` pass; viewport proof remains open (T5/T7).

## Progress update · Kanban horizontal navigation
- Added Spanish overflow guidance and previous/next controls above status columns. Arrow navigation advances one column, stays outside the DnD surface, disables at each edge, uses instance-safe `useId` controls, and switches to instant scrolling for reduced motion. Targeted ESLint, typecheck and `git diff --check` pass. Runtime check needs a session with `tasks:read`; T4/T5/T7 remain open.
- Task Workspace folder branches can now collapse/expand with an animated height and chevron; initial state remains fully expanded. Collapsed descendants are hidden from focus and pointer input, reduced-motion users get immediate changes, and the existing folder selection/reorder controls remain separate. Targeted ESLint, typecheck and `git diff --check` pass; browser review remains open.

- 2026-10-11: Reconciled current page wrapper paths against the existing 59-route inventory: 59/59, no missing or stale entries. Improved `TaskCard` semantics so its wrapper is an article, the title is the keyboard activation target, nested action buttons remain independent, and pointer/Shift-click behavior is retained. Targeted ESLint, typecheck and `git diff --check` pass. Browser keyboard/motion checks remain open; a new production build was deferred because the active dev server uses about 9.8 GiB and shares `.next`. T1/T4/T7 remain incomplete.

- 2026-10-11: Fixed task shared-element source detection timing in `TaskDetailSheet`: changed the task-card DOM lookup from a passive effect to a layout effect so the matching `layoutId` is assigned before paint when the dialog opens. Direct detail routes still use the normal entrance because they have no source card. Targeted ESLint, typecheck and `git diff --check` pass; `/tasks` and `/projects/construction` return HTTP 200. Authenticated browser verification of the shared transition remains open; T4/T7 are still incomplete.

- 2026-10-11: Continued the shared-owner review. `PageHeaderCard` headings now wrap and balance on narrow screens rather than truncating. Targeted ESLint, typecheck, and diff check pass. Runtime viewport evidence remains needed for the changed header; visual walkthrough and build remain open due the human browser lease and high-memory active dev server.
- 2026-10-11: Correction to the earlier “identidad compartida de proyectos desde caché” note: that change only rendered the cached project name in the skeleton while `/project/[id]` still called `loadProjectDetailsData` for the full page. David clarified that the project row should be handed into the detail route without that request. T8 now covers a cache-first route and a versioned list DTO for fields that the prior list omitted; warm navigation disables list and financial refetches. Typecheck and targeted lint pass in both repos; visual/network browser verification remains open under the human browser lease.
- 2026-10-11: David reported that task-detail entry still felt rough. Replaced the fixed short translate/scale entry with a mass/damping spring, restrained blur cleanup, and staggered section reveals; shared-source expansion remains active and reduced-motion users skip the entry. Frontend typecheck, targeted ESLint, and diff check pass. Visual calibration remains unverified while the browser lease is human-owned.
- 2026-10-11: After David said the task-detail entrance still felt unnatural, removed competing panel transforms and blur. The shared card expansion now uses a softer layout spring; content sections reveal with a short, restrained stagger. Added an explicit reduced-motion variant for those child reveals. Targeted ESLint, frontend typecheck, and `git diff --check` pass; visual calibration remains pending.
- 2026-10-11: Reconciled `src/app/**/page.tsx` against REQ-003 inventory: 59 current wrappers, all 59 listed, no stale routes or duplicates (the inventory's 60th row is the shared shell). The browser lease is still human-owned. As a shared-owner improvement, Dialog, AlertDialog and Sheet overlays now transition backdrop blur in/out with a 200 ms ease and drop the transition under reduced motion. Targeted ESLint, typecheck and diff check pass; visual/browser sweep remains open.
- 2026-10-11: Implemented the P-002 retryable project-list error state in both the lead-type Projects view and the Completed/Lost shared view. Query errors now remain distinct from a legitimate empty result; stale rows stay visible during a background error. Added a shared `ProjectListLoadError` with generic recovery copy and pending feedback. Typecheck, targeted ESLint and diff check pass; authenticated failure/retry browser verification remains open.

## Progress update · task detail entrance tuning
- Tuned the task card/detail shared expansion to a consistent, softer spring and made the section reveal more legible with a restrained 7 px staggered lift. Direct entrances now use a short spring settle from a subtle offset; reduced motion remains immediate.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. The isolated browser rendered the task board skeleton during the attempted visual capture, so this turn does not claim visual confirmation. T4/T7 remain incomplete.
- The shared image preview uses the same spring profile as task-card expansion, so its thumbnail-to-viewer magnification settles naturally while the existing blurred Radix backdrop remains. A fresh authenticated isolated tab confirmed `/tasks?task=29` opens the detail; the earlier contrary result came from a stale diagnostic tab. T4 remains open for the shared animation, return focus, DnD, nested actions, and reduced-motion checks.

## Progress update · task opening latency and loading state
- Changed task query-only URL updates to the App Router-integrated History API so opening/closing a task does not request a fresh server-rendered board. In an isolated browser, pushing `/tasks?view=mine&task=29` updated `useSearchParams` and opened the dialog; no new `_rsc` request was observed. Directly invoking the title React handler changed the URL once; Escape then returned to `/tasks` and closed the dialog. A CDP mouse click reaches the DOM but has not invoked the React handler in this diagnostic session; a title-only parent fallback was added. Verify real pointer activation, child-task replace, and close behavior before closing T4.
- The detail panel now reads validated summary fields from task query cache (title, status, priority, due date) while fetching the full detail, shows an inline retry state on failure, and caps the full detail request at 12 seconds. In an isolated 1440px browser, the dialog showed `T-29`, `Test`, `Backlog`, `Normal`, and “Loading the rest of this task…” within 50 ms of mount. Targeted ESLint, frontend typecheck, and `git diff --check` pass. The forced-timeout/retry UI check did not reach the detail mount in its capture window; T4/T7 remain open.

## Progress update · image preview loading polish
- Added a short reduced-motion-aware crossfade between the attachment preview loader and the shared image as it decodes; the existing thumbnail-to-viewer spring and blurred dialog backdrop remain. The spinner now stops under reduced motion.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. I did not have a loaded S3-backed image preview in the isolated browser for visual confirmation. T3/T7 remain open for image/PDF keyboard and browser walkthrough checks.

## Progress update · organic task-detail entrance
- Separated the task-detail shared layout element into a background shell so its card-to-dialog expansion no longer scales the detail text and controls. The real content now fades and settles independently with a short, reduced-motion-aware reveal; task-shell and card use the same spring profile.
- Targeted ESLint and frontend typecheck pass. The browser tab continued serving the previous DOM after reload, while the local Next worker used about 10.3 GiB and `/tasks` timed out after 20 seconds; API docs returned 200. No server restart was performed. Visual verification of this revision remains open; T4/T7 remain incomplete.
- After closing 20 duplicate tabs in the agent-owned headless browser, the page recovered and the updated shared shell rendered. At 1440 px the card shell moved toward the dialog while the content wrapper stayed at its final size (`transform: none`); the task opened with summary/loading content. Measured `scrollWidth` equaled available width at both 1440 px and 456 px. A later 80 ms content-reveal delay was added to better synchronize content with the shell; its updated timing was not visually sampled because `/tasks` and CDP became intermittently unresponsive again. T4/T7 remain open.

## Progress update · warm/cold project-detail handoff
- Captured a real warm navigation from `/projects/construction` to `/project/144`: the page showed the project identity and detail data without requesting `/projects/v2/all` or `/projects/144/details`; the only detail request was the separate QuickBooks cost-breakdown report. A new authenticated tab opened `/project/144` cold and requested `/projects/v2/all`, `/projects/financials`, and that cost report, with no `/details` call.
- Fixed the cold-path financial-query gate: `isWarmNavigation` now records whether the list was cached at mount, so the cold path can enable financials once the versioned list arrives while warm navigation keeps using cached list/financial rows without refetching.
- A 456 px screenshot showed project-cost category names compressed to initials and the forecast placeholder clipped. Reflowed mobile rows into label/paid and forecast lines, shortened the placeholder to “Sin dato,” and rechecked the screenshot: full category labels, readable placeholders, and document width 456 px. Targeted ESLint, frontend typecheck and `git diff --check` pass. T5/T8/T7 remain open for the full walkthrough and remaining acceptance checks.

## Progress update · organic task-detail entrance follow-up
- Softened the shared card-to-dialog spring to `stiffness: 185`, `damping: 24`, `mass: 1` on both source card and destination shell. The content now settles from a small 12 px / 1.5% offset, then reveals sections with a short stagger and spring lift; reduced-motion remains immediate.
- Targeted ESLint and frontend typecheck passed; `git diff --check` passed. The local frontend request to `/tasks` timed out after 12 seconds, so this exact timing revision could not be visually calibrated in the browser. No server restart, tests, or build were run. T4/T7 remain open.

## Progress update · task shared-surface opacity
- A real browser opening showed the task detail content over the blurred page but the shared background shell at computed opacity `0`. Motion was crossfading between the complete task card and an empty dialog shell, leaving the dialog surface transparent during its expansion.
- Set `layoutCrossfade={false}` on that shared shell so its opaque surface expands over the source card. In a second authenticated browser opening, the shell reached opacity `1`, `transform: none`, and the expected `1085 × 828` final size. This verifies the final surface state; timing under ordinary device load and pointer/keyboard close behavior still need the full T4 walkthrough.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. `/tasks` returned 200 after 4.1 seconds; the existing Next process remains unusually CPU/memory intensive. No restart, tests, or build were run. T4/T7 remain incomplete.

## Progress update · task entrance naturalness
- David said the task detail now partly works but its entrance still feels unnatural. Removed the content panel's scale-in so text and controls no longer zoom while the shared card surface expands; shortened the initial content offset, softened the settling spring, and reduced the section stagger. Reduced-motion remains immediate.
- A real authenticated opening showed the content was visible while the shared surface was still at card size. The entry class's 60 ms delay had no backwards fill, so the opacity stayed at 1 during the delay. Added backwards fill and aligned the content reveal 120 ms after the surface begins expanding. Captured early and settled screenshots: the shared surface expands first, then the content fades in without a scale transform. The shell went from 270 × 140 px to about 1086 × 814 px and nearly settled within 500 ms.
- Reloading the authenticated tab with `prefers-reduced-motion: reduce` verified no shared shell, no content animation, and no content transform. Restored the browser to `no-preference` afterward. Targeted ESLint, frontend typecheck, and `git diff --check` passed. No tests or build were run. T4/T7 remain open for the wider task interaction and route walkthrough.

## Progress update · note table menu narrow-screen overflow
- At a 456 px viewport, activated the note table menu with a non-mutating text selection. The BubbleMenu was wider than the available content and could extend beyond the viewport because `top-start` shift only corrected the vertical axis. Enabled horizontal collision shifting and Floating UI size clamping; the menu wraps whole row/column/table groups within the available width.
- Browser verification at 456 px showed the menu at x=8..448 with all 10 labeled controls inside the viewport and document width still 456 px. At 1440 px it retained its one-row 446.8 px layout. Targeted ESLint, typecheck, and `git diff --check` passed; no note content was changed. T5/T7 remain open for the rest of Notes and the route walkthrough.

## Progress update · organic project-detail entrance
- David said the project-detail entrance animation felt stiff. Replaced the repeated `280/30` shared-layout spring with one feature-level spring profile (`stiffness: 170`, `damping: 24`, `mass: 1`) across the desktop/mobile source names, loading skeleton, and detail targets. The content below the shared project heading now reveals over 360 ms with a slight 8 px rise and soft blur, without scaling the shared name; reduced-motion renders immediately.
- Follow-up after David's feedback: removed the broad blur and replaced the 360 ms ease animation with a subtle 12 px rise on a damped spring (`150/26/0.8`, 60 ms delay). The shared project name stays visually dominant. Reduced-motion still bypasses the entrance. No browser calibration or test commands were run for this follow-up; T7 remains open.

## Progress update · user and role settings responsive layout
- Expanded both settings pages to use the available width and responsive padding. Set the Users table to a 980 px minimum data width so its seven columns stay legible and use the existing contained horizontal scroller on narrow screens.
- Roles now show a skeleton during load, an explicit retry path on failure, a useful empty state, and role cards that stack details and actions on narrow screens. Targeted ESLint, frontend typecheck, and `git diff --check` pass.
- The permission editor now renders loading/error/empty states for its catalog, offers retry, preserves cached choices on refresh errors, blocks save when no options exist, and uses a single-column checkbox grid on small screens. Role-management actions and form labels are translated to Spanish; icon buttons have accessible names. Targeted ESLint, typecheck, and diff check pass.
- Static review only. The isolated browser refused control while the human is using it; the responsive result and the project entrance still need browser calibration. No tests were run.
- The Users table and page now use Spanish headings, status labels and `es-CO` date formatting; role/access/invitation controls expose names that include the affected person. Reconciled the 59 App Router page files against the 59 route entries in the interaction inventory; no missing or stale routes. The full visual walkthrough remains open.
- Localized the role editor and destructive confirmation flow, added accessible names to icon-only role actions, and kept permission labels readable in the small-screen dialog. Targeted ESLint, typecheck, and diff check pass; no test suites were run.
- The invitation dialog now renders role loading/error/empty feedback, offers retry, enforces the external-user zero-permission role constraint in its visible choices, and disables submission while no eligible role exists. Targeted ESLint, frontend typecheck, and `git diff --check` pass; no tests were run.

## Progress update · lead and contact shared-name navigation
- Added `SharedEntityName`, which uses the shared entity spring and omits `layoutId` under reduced motion. Contact names link from a lead detail card to its Contact heading; lead names link from Contact lead cards to the matching Lead heading.
- Added a second Contact-name source from Company details, preserving its card-wide mouse navigation and nested `mailto:` link while making the name itself a keyboard-accessible link. Converted Contact page lead/project cards to semantic links with focus rings. Targeted ESLint reports 0 errors and 6 existing `no-explicit-any` warnings; typecheck and diff check pass. The isolated browser still reports `human_has_control`, so visual interpolation and keyboard navigation remain unverified; no tests were run.
- Extended matching names to unique rows in Companies, Contacts, Leads and Leads-in-Review tables. Converted leads that navigate to a project and the reusable contact chip are deliberately excluded: the former has a different destination identity, and the latter can repeat the same contact `layoutId` in multiple rows. Targeted ESLint now reports 0 errors and 8 existing `no-explicit-any` warnings; frontend typecheck and `git diff --check` pass. Browser acceptance remains open.
- Targeted ESLint passed with 0 errors and 3 existing `no-explicit-any` warnings in `ProjectDetailsPage.tsx`; `npm run typecheck` and `git diff --check` passed. Browser visual calibration was not possible: `/projects/construction` did not respond within 25 seconds, while the already-running Next process remained at about 13.8 GiB RSS / 165% CPU. I did not restart it. T7 remains open.

## Progress update · project and finance mobile walkthrough
- In the authenticated isolated browser, `/projects/construction` loaded 66 projects; its 456 px card view stayed within the viewport. A cold `/project/144` rendered the cached-list detail data from `/api/projects/v2/all`, `/api/projects/financials`, and `/api/projects/144/cost-breakdown`, with no `/api/projects/144/details` request. At 456 px, the project detail document and main viewport both remained 456 px; tabs use an internal horizontal viewport.
- `/finance/receivables` rendered its 61-project aging view at 456 px with no page-level overflow; the cards keep “no invoice recorded” warnings visible. `/settings/users` remained on “Loading users…” during observation and emitted no `/api/users` browser request, so its data state is inconclusive rather than a verified page defect. The dev-server child process changed from PID 14142 (~14.6 GiB RSS) to PID 820022 under the same long-lived launcher; no restart was issued. Shared project-name interpolation was not confirmed by this click harness; keep it open under T2/T7. The global route walkthrough remains incomplete.

## Progress update · project shared-element and crossfade verification
- A real authenticated click from `/project/144` back to `/projects/construction` produced `Page.navigatedWithinDocument`; the browser document and React state were preserved. The route layers crossfaded from opacity 1/0 through 0.43/0.57 at 90 ms and 0.03/0.97 at 119 ms, with the outgoing layer inert and `aria-hidden`; it was removed by about 313 ms.
- The matching `Plumbing Managment` name also moved and resized between the list row and detail heading. A cold-forward trace captured both layout-ID copies crossfading while the destination settled from the source row's 140 × 18 px geometry to the 157 × 24 px heading; the spring stopped moving within about 800 ms. No route error occurred. A reduced-motion route trace remains inconclusive: the browser matched the emulated preference after reload, but the following route click did not yield a stable transition sample. T2/T7 remain open for back/forward, rapid interruption, and the rest of the route walkthrough.

## Progress update · browser evidence for route and file transitions
- On an authenticated image attachment, the source thumbnail stayed visible while the full-resolution target loaded; the image then rendered at 341 × 699 with natural size 876 × 1795. Keyboard Enter opened the image viewer, Escape closed it, and focus returned to its preview button. A PDF attachment still rendered through `<embed type="application/pdf">` with no image element.
- Under emulated reduced motion, the image stayed untransformed (`transform: none`) and the backdrop retained its 8 px blur with `transition-property: none`, so the blur applies immediately without an animated transition.
- Authenticated navigation from lead detail to projects showed incoming opacity progressing from about 0.96 to 1 while the outgoing route was `aria-hidden`, inert, and `pointer-events: none`; browser Back returned to the lead route. The reduced-motion route check crossed a pending destination window before a stable layer sample, so it remains unverified. T2/T3 still need the remaining route, keyboard/focus, and viewport walkthroughs; T4/T7 remain open.

## Progress update · mobile entity-detail header
- A 456 px screenshot of lead detail exposed a shared `EntityDetailHeader` layout defect: long titles collapsed to one word per line beside schedule/conversion actions, and the actions were clipped. Changed the shared header to stack title and wrapping actions on narrow screens, with a 24 px mobile title; the desktop row remains intact.
- After reload, the lead title occupied a readable two-line block (`328 px` wide), all actions wrapped below it, and document/main widths both stayed at 456 px. The `/contacts` list also fit the viewport; its 409 px table viewport scrolls its 965 px data surface locally, with no page-level overflow. Targeted ESLint, frontend typecheck, and `git diff --check` passed. T5 remains open for the rest of the route families and viewport checks.
- A follow-up request for `/notes` timed out after 15 seconds while the existing Next process was consuming about 13.7 GiB RSS and 162% CPU; no Notes visual result was captured and no restart was performed. Keep the Notes route in T1/T5 pending.

## Progress update · coordinated task entrance follow-up
- Removed the nested CSS fade/slide that duplicated Motion's panel and section animations. The panel now fades once after the shared surface begins expanding, then reveals its content sections in a short stagger; section motion uses a small spring lift. Matched the source card and destination shell to the same softer `160/27/1.1` spring. The existing reduced-motion path remains immediate.
- Targeted ESLint, `npm run typecheck`, and `git diff --check` passed. This timing revision was not visually sampled in the browser, so perceived naturalness still needs direct confirmation; no tests, build, or server restart were run. T4/T7 remain open.

## Progress update · task motion surface extraction
- Moved the task dialog's shared surface and entrance orchestration into `TaskDetailDialogSurface.tsx`, keeping its shared-layout shell, close affordance, and reduced-motion behavior together and separate from task editing logic.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed after extraction. Browser timing remains unverified; no tests, build, or server restart were run. T4/T7 remain open.

## Progress update · project-name handoff source audit
- Rechecked the current source of `/projects` and `/project/[id]`: the desktop `Project Name` column and mobile card both render `project.lead.name`; their desktop/mobile `layoutId`s match the two responsive detail-heading targets. Warm navigation builds detail data from the cached project list, and cold navigation uses the typed list fallback. No source change was needed.
- Visual confirmation remains open. Linux computer-use reports the human holds the desktop lease; the isolated Firefox BiDi endpoint is not listening (`127.0.0.1:9223` connection refused). The existing frontend dev server remains listening on port 3000 (PID 820022); it was not restarted. T8/T7 remain open.

## Progress update · route scroll continuity
- The authenticated app's persistent `<main>` is the scroll container, so route changes can carry the previous page's `scrollTop` into the incoming page. Added route-keyed scroll memory: a new path starts at the top, and returning to a previously visited path restores its last position before the crossfade paints.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Browser forward/back scroll behavior remains unverified while the human holds the desktop lease; no tests, build, or server restart were run. T2/T7 remain open.

## Progress update · shared-element measurements inside the app scroller
- Registered the authenticated app's scrollable `<main>` with Motion via `layoutScroll`, so project-name, entity-name, task-card, and image layout IDs include the container's scroll offset in their measured shared-transition geometry.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. The official Motion documentation specifies `layoutScroll` for layout animations in scrollable containers. A scrolled-list visual trace remains pending because the desktop lease is human-held; no tests, build, or server restart were run. T2/T7 remain open.

## Progress update · contact-to-project shared name
- Added desktop/mobile project-name layout IDs to the project cards on Contact details. They match the existing responsive project-detail heading IDs, use the shared spring, and are omitted under reduced motion. The API model defines Project↔Lead as one-to-one, so the contact's list of leads cannot introduce duplicate project-name layout IDs for the same project.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Browser interpolation remains unverified while the human holds the desktop lease; no tests, build, or server restart were run. T2/T7 remain open.

## Progress update · task list and My Tasks title handoffs
- Added a reduced-motion-aware shared title from Task List and My Tasks rows into task detail. The detail uses the cached summary title during loading and the editable title after the task read completes; the source detector prioritizes the board's whole-card transition and avoids treating nested-task navigation as a new list opening.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. The browser lease remains human-held and Firefox BiDi is unavailable, so interpolation and close behavior need visual verification. No tests, build, or server restart were run. T4/T7 remain open.

## Progress update · organic task-detail entrance follow-up
- Removed the competing Radix dialog opening animation so Motion owns the panel reveal. The card-to-dialog shared spring now has a slight natural settle, while content sections fade from a subtle blur with restrained spring lifts and a short stagger. Reduced-motion remains immediate.
- Targeted ESLint (3 files), `npm run typecheck`, and `git diff --check` passed. Direct visual calibration remains open because the existing dev server is under heavy load and the agent browser is unavailable; no tests, build, or server restart were run. T4/T7 remain open.

## Progress update · route-transition source audit and frontend lint
- Re-reviewed `RouteTransition` and `AppShell`: the outgoing route layer becomes inert and pointer-disabled, and scroll positions are saved/restored by pathname. No additional source defect was confirmed without browser evidence.
- Full `npm run lint` passed with 0 errors and 164 warnings; `npm run typecheck` and `git diff --check` passed. The dev server is still running against Next's default `.next` directory, so a production build is deferred to avoid colliding with the live app. Browser route/back-forward/scroll checks remain open; T2/T7 remain incomplete.

## Progress update · isolated production build
- Built an isolated copy of the current frontend worktree at `/tmp/maros-next-build-5pcweo`, excluding `.next`, `node_modules`, and environment files while reusing installed dependencies. `npm run build` passed and generated all 41 static pages without touching the active development server's `.next` output.
- Warnings: deprecated Next `middleware` convention; `jose` CompressionStream/DecompressionStream APIs in the Edge Runtime import path; Node module-type warning for `tailwind.config.ts`. Browser walkthrough remains open; T2/T7 remain incomplete.
- Reconciled the current App Router page files against the REQ-003 inventory: 59 source page routes, all represented; the one extra inventory entry is the shared authenticated shell.

## Progress update · reduced-motion priority in shared overlays
- Compiled CSS confirmed that the state-qualified Radix animation classes had higher specificity than the former reduced-motion utilities. Updated Dialog, Sheet, and AlertDialog to use important reduced-motion animation/transition overrides, preserving an immediate blur state without animation.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. An isolated production build passed and generated all 41 static pages; its CSS output contains the expected `animation:none!important` and `transition-property:none!important` declarations under the reduced-motion media query. Direct browser focus/overlay walkthrough remains open; T6/T7 remain incomplete.

## Progress update · reduced-motion loading indicators
- Applied the reduced-motion preference to the shared `animate-spin` and `animate-ping` utilities in `globals.css`, covering repeated loading indicators across calendar, tasks, finance, attachments, users, and reports. The static refresh dot remains visible while its animated halo is hidden.
- An isolated production build passed all 41 static pages; generated CSS confirms the spin and ping overrides under the reduced-motion media query. `git diff --check` passed. Browser confirmation remains open; T6/T7 remain incomplete.

## Progress update · reduced-motion Radix menus and popovers
- Added important reduced-motion animation/transition overrides to ContextMenu, DropdownMenu (including submenus), Popover, Select, and Tooltip content. This prevents the state-qualified Radix fade/zoom/slide classes from overriding the user's reduced-motion preference.
- Targeted ESLint (5 shared UI files), `npm run typecheck`, and `git diff --check` passed. An isolated production build passed all 41 static pages; compiled CSS includes the important media-query overrides. Direct keyboard, nested-overlay, and visual checks remain open; T6/T7 remain incomplete.

## Progress update · reduced-motion feature entrances
- Added important reduced-motion overrides to the translation feedback toast and dashboard filter updating/error entrances, the only remaining feature-level `animate-in` usages found outside shared primitives.
- Targeted ESLint (2 feature files), `npm run typecheck`, and `git diff --check` passed. An isolated production build passed all 41 static pages. Visual review remains open; T6/T7 remain incomplete.

## Progress update · task-detail entrance naturalness
- Removed the task dialog content's scale and blur transitions to avoid stacking them with the card-to-dialog expansion. Kept the shared shell's spring matched to the source card; direct openings use a subtle 8 px spring settle, while shared openings reveal content after the shell starts expanding and stagger sections by 45 ms. Reduced-motion still bypasses movement and opacity changes.
- Targeted ESLint (2 files), `npm run typecheck`, and `git diff --check` passed. Visual calibration is still pending: the desktop lease is held by the human and Firefox BiDi on port 9223 refuses connections. No tests, build, or server restart were run; T4/T7 remain open.

## Progress update · task title-only shared handoff
- Separated title-only sharing from the full card surface transition. Task rows now use the normal immediate panel entrance while the title animates; only a real card-to-dialog surface expansion delays the content reveal. This removes the empty pause when opening from Task List or My Tasks.
- After this correction, targeted ESLint (2 files), `npm run typecheck`, and `git diff --check` passed. The latest source was copied into an isolated build tree; `npm run build` passed and generated all 41 static pages. Full `npm run lint` also passed with 0 errors and 164 existing warnings before the final small handoff correction. Browser calibration remains pending because the human holds the desktop lease and Firefox BiDi is unavailable; T4/T7 remain open.

## Progress update · task shared-element return
- For task details opened from a card or title, the close path now removes Radix's competing content zoom/fade and lets Motion return the matching element to its source immediately. Direct task routes without a mounted source keep the standard dialog exit; reduced-motion still bypasses shared transforms.
- Targeted ESLint (2 files), `npm run typecheck`, and `git diff --check` passed. An isolated production build containing the latest task-detail files passed and generated all 41 pages. The source and destination geometry still need a browser close/open trace; the desktop lease is human-held and Firefox BiDi is unavailable. T4/T7 remain open.

## Progress update · image preview shared-motion ownership
- When an image preview has a mounted thumbnail source, the Radix content no longer adds its own zoom/fade on open and close; Motion owns the image's thumbnail-to-viewer geometry while the shared Dialog overlay still applies the blurred backdrop. PDF, DOCX, unsupported files, reduced-motion users, and previews without a live source keep the normal viewer transition.
- Targeted ESLint, `npm run typecheck`, and `git diff --check` passed. An isolated production build containing the latest preview code passed and generated all 41 static pages. Browser timing, keyboard close, and visual return-to-thumbnail remain unverified because the human holds the desktop lease and Firefox BiDi is unavailable; T3/T7 remain open.

## Progress update · recoverable and sanitized DOCX preview
- DOCX previews now reset stale content when the selected URL changes, abort network work on close/reselection, and show a recoverable error with an open-document action after failure or a 15-second deadline. Added status/alert semantics for loading and errors.
- The installed Mammoth 1.12.0 README explicitly warns it does not sanitize source documents. Sanitized its HTML output with an element/attribute allowlist, safe HTTP(S)/mailto links, and bounded raster data images before `dangerouslySetInnerHTML`; empty safe output now receives the recovery state.
- Full `npm run lint` passed with 0 errors and 164 warnings, with no warnings in the changed preview/task files. Targeted ESLint, `npm run typecheck`, `git diff --check`, and an isolated production build generating all 41 pages passed. Runtime document/keyboard review remains open because the human holds the desktop lease and Firefox BiDi is unavailable; T3/T6/T7 remain open.

## Progress update · attachment source readiness and route exclusions
- Attachment thumbnails now expose a shared-layout source only after the image has decoded. The preview modal checks for that ready source before suppressing the normal panel entrance or assigning the destination layout ID; opening while a thumbnail is still loading or after it fails gets the ordinary viewer entrance.
- Re-audited `AppShell`/`RouteTransition`: `/login`, `/about`, `/privacy-policy`, and `/p/*` bypass the authenticated shell; the transition key is pathname-only, so task query updates do not crossfade the full route. No change was needed there.
- Targeted ESLint (3 files), `npm run typecheck`, `git diff --check`, and an isolated production build with the latest attachment files passed; all 41 static pages were generated. Browser visual calibration remains pending because the human holds the desktop lease and Firefox BiDi is unavailable; T1/T3/T7 remain open.


## REQ-004 · organic project-detail entrance follow-up
- David reported the project-detail entrance still felt stiff. Softened the project-name shared-layout spring (`135/22/1`) and changed the detail tabs/content reveal to a restrained 9 px rise with a subtle 0.99→1 scale and damped spring; reduced-motion still bypasses the entrance.
- Targeted ESLint passed with 0 errors and 3 existing `no-explicit-any` warnings in `ProjectDetailsPage.tsx`; `npm run typecheck` and `git diff --check` passed. No tests/build or server restart were run. Visual calibration remains open because browser access is unavailable; T2/T7 remain open.


## REQ-004 · calendar view transitions
- Reused the reduced-motion-aware shared animated selector for Calendar's Month/Agenda and Upcoming/Past controls, then added a short fade/settle crossfade between the month grid and agenda while preserving existing query, filter, and selection state.
- Targeted ESLint (CalendarPage and AnimatedBackground), `npm run typecheck`, and `git diff --check` passed. The running frontend returned HTTP 200 for `/calendar` in 2.66 s; its existing process remains active at high memory/CPU use, so it was not restarted. Browser visual calibration and production build remain open; T2/T7 remain incomplete.


## REQ-004 · converted-lead to project name handoff
- The converted-leads table routes by `lead.project.id`, and the API models `Lead.project`/`Project.lead` as a one-to-one relation. Added responsive project-name layout IDs to the read-only row, matching the desktop/mobile project-detail targets; ordinary lead rows keep their existing lead IDs. This updates the earlier deliberate exclusion now that the target identity mapping is verified.
- Targeted ESLint passed with 0 errors and 1 existing `no-explicit-any` warning in `useLeadsTableColumns.tsx`; frontend typecheck and `git diff --check` passed. No tests/build or server restart were run. Visual transition confirmation remains open; T2/T7 remain incomplete.


## REQ-004 · project detail entry points and SPA continuity
- Extended the project-name handoff to the receivables table and Project Health alerts where the source name is the lead-backed project name; Project Health skips its project-number fallback because it does not match the detail title. Converted Leads uses its verified one-to-one project relation.
- Replaced `window.location.href` with Next `router.push` in the post-conversion estimate dialog so “View project” keeps the authenticated shell and route crossfade. Existing permissions, mutations, and project URLs are unchanged.
- Targeted ESLint passed with 0 errors and 1 existing `no-explicit-any` warning in `useLeadsTableColumns.tsx`; frontend typecheck and `git diff --check` passed. Browser controls are unavailable (`cua.getState()` returned no apps/browsers), so visual interpolation is still unverified. No tests, build, or server restart were run; T2/T7 remain open.


## REQ-004 · project cache-first detail edge cases
- Confirmed `/project/[id]` does not call the legacy `/projects/:id/details` endpoint: the route builds its view from the cached `/projects/v2/all` read model, whose backend DTO includes project overview/notes/attachments and linked lead/contact/company/estimate fields. Cold routes fall back to that list contract.
- Warm detection now requires the requested project ID to exist in cache; otherwise the list is force-refetched on mount and the skeleton stays up while the target is unresolved. Project financials reuse the matching cached row; an authorized user fetches the shared financials endpoint only when that project's row is absent/invalidated, with focus polling disabled on the detail view. The finance query key is now owned by `projectsKeys.financials()`.
- Targeted ESLint (5 files), frontend typecheck, and `git diff --check` passed. Runtime network trace could not run: Linux browser lease is human-held, Firefox BiDi on 9223 refuses connections, and the existing Next server is using about 12.7 GiB RSS at high CPU, so I did not compile another route or restart it. No tests/build were run; T8 still needs runtime confirmation and T7 remains open.


## REQ-004 · project financial-cache permission guard
- The project detail cache adapter now receives the cached financial summary only when the current user has `finance:read`; a finance row left in the query cache cannot surface through this route after a permission change.
- Re-ran targeted ESLint (5 files), frontend typecheck, and `git diff --check`; all passed. Runtime permission/network trace remains pending because the human holds the browser lease and the dev server is under high load.


## REQ-004 · isolated browser verification attempt
- Tried opening the local project route in a new `maros-qa` Firefox session using the approved agent-profile clone. The Linux computer-use plugin rejected the session with `human_has_control`; the agent did not take over the active desktop. Firefox BiDi on 9223 remains unavailable.
- Source checks still pass; do not report the project warm-navigation network trace or the latest motion calibration as visually verified.


## REQ-004 · finance-status cache permission boundary
- `mergeProjectFinancials` stores `invoiceStatus` on the cached project row, so gating only the separate `financial` object left a finance-derived badge visible to a `projects:read` user without `finance:read`. Made the list-to-detail adapter require the permission and omit both invoice status and financial amounts when it is absent.
- Targeted ESLint (2 files), frontend typecheck, and `git diff --check` passed. Runtime visual/permission confirmation is still unavailable under the human-held browser lease; no tests/build or server restart were run.


## REQ-004 · project entrance motion refinement
- Responding to David's feedback, removed the content-wide scale-in that made project detail feel rigid. The tabs/content now rise 12 px with a damped spring (`190/24/0.7`) and 40 ms delay; the project-name shared-layout spring is `210/24/0.72`. The detail tabs also use a shared animated active pill and keep reduced-motion support.
- Targeted ESLint passed with 0 errors and 3 pre-existing `no-explicit-any` warnings; `npm run typecheck` and `git diff --check` passed. Browser calibration remains pending because the desktop lease is human-held. No tests, build, or server restart were run; T2/T7 remain open.


## REQ-004 · detail-panel transitions
- Added a short fade and 4 px settle to active Radix tab panels in the shared `TabsContent`, so project/lead details, task tabs and tabbed dialogs no longer switch with a hard cut. `prefers-reduced-motion` disables the entry animation.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. The existing local frontend returned HTTP 200 for `/tasks` (4.28 s). The browser lease is still human-held, so the transition was not visually calibrated; no tests, build, or server restart were run. T2/T6/T7 remain open.


## REQ-004 · shared motion consistency
- Unified project, lead, contact and company shared-name handoffs on the same `210/24/0.72` damped spring; the project transition now reuses the common motion token. This removes a subtle timing mismatch between adjacent CRM routes.
- The shared `TabsContent` entry animation is in place with a short fade/4 px settle and reduced-motion override. Targeted ESLint, frontend typecheck, and `git diff --check` passed. Firefox visual verification is unavailable (`human` lease; BiDi port 9223 refuses connections). No tests, build, or server restart were run.
- Tried `npm run ui:audit`; it fails because `scripts/ui-audit.mjs` is missing. The existing docs already record this as a repository tooling issue; no unrelated script/package change was made.


## REQ-004 · shared overlay blur owner
- Extracted the identical Radix modal backdrop recipe (dim, 200 ms fade/blur, immediate reduced-motion path) into `modalOverlayStyles.ts`; Dialog, AlertDialog and Sheet now use the same class token, preventing their blurred backdrops from drifting.
- Targeted ESLint, frontend typecheck and `git diff --check` passed. The running Next process (PID 820022) remained on port 3000 at about 12.7 GiB RSS / 94% CPU. Its first `/tasks` request timed out at 10 s; a retry returned HTTP 200 in 2.08 s. I did not restart it. Firefox visual acceptance remains unavailable under the human desktop lease; no tests/build were run. T6/T7 remain open.


## REQ-004 · sidebar route-state handoff
- Added a reduced-motion-aware shared active background that moves between sidebar links as client routes change, and set `aria-current="page"` on the active link. Fixed the overlapping route match so `/tasks/workspaces…` selects “Task workspaces” without also marking “Tasks” active.
- Targeted ESLint, frontend typecheck and `git diff --check` passed. `/tasks` returned HTTP 200 in 4.67 s. The existing Next process (PID 820022) was still using about 13.1 GiB RSS / 95% CPU; I left it running. Browser interpolation remains unverified under the human desktop lease; no tests/build were run. T2/T7 remain open.


## REQ-004 · sidebar active-state emphasis
- Added a narrow MARO mint accent to the moving sidebar selection surface, keeping the existing active background and text treatment. `prefers-reduced-motion` still renders it as a static selected state.
- Re-ran targeted ESLint, frontend typecheck and `git diff --check`; all passed. `/tasks/workspaces` returned HTTP 200 in 13.12 s on the existing high-load dev server. Firefox remains human-held, so layout interpolation is not visually verified; no tests/build or server restart were performed. T2/T7 remain open.


## REQ-004 · sidebar state for detail routes
- Extended sidebar route matching with boundary-safe alternative prefixes so the shared active indicator persists from the main lists into `/project/[id]` and its report, `/contact/[id]`, and `/lead/[id]`. Prefix matches now require a segment boundary; exclusions keep sibling sections distinct.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Browser visual confirmation remains unavailable under the human-held desktop lease; no tests/build or server restart were run. T2/T7 remain open.


## REQ-004 · attachment-preview accessibility
- The shared image viewer now announces image loading as a polite status and preview failures as alerts; embedded PDFs expose a title containing the filename. Shared-image geometry, focus return, PDF rendering and reduced-motion behavior are unchanged.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Visual browser verification remains unavailable (human desktop lease; Firefox BiDi on 9223 is offline). No tests/build or server restart were run. T3/T7 remain open.


## REQ-004 · dynamic viewport fit for file previews
- Changed the shared preview dialog, image limits, PDF height, and DOCX viewport cap from `vh` to `dvh`, so mobile browser chrome no longer consumes space counted as visible preview area.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Browser viewport verification remains pending because the human holds the desktop lease; no tests/build or server restart were run. T3/T5/T7 remain open.


## REQ-004 · current route and lint audit
- Reconciled `src/app/**/page.tsx` against the approved interaction inventory again: 59 actual routes, 59 inventory routes, no missing or stale entries. This confirms route coverage only; it does not close the required visual walkthrough.
- `npm run lint` passed with 0 errors and 164 warnings; `git diff --check` passed. The current Next dev process is still live on port 3000 and using 13.3 GiB RSS / about 97% CPU, with 7.7 GiB system memory available and swap heavily used; I did not run a build against its shared `.next` tree or restart the server. The browser lease remains human-held and BiDi on 9223 is offline. T1/T2/T3/T4/T5/T6/T7/T8 remain open for their runtime/visual acceptance items.


## Progress update · organic route entrance
- Responding to David's feedback, changed the shared route fade into a restrained spring settle (8 px rise, 0.6% scale correction, soft blur cleanup) with a short opacity fade; outgoing routes yield with a small reverse offset. Reduced-motion users skip the entrance.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. No browser calibration, tests/build, or server restart; T2/T7 remain open.


## Progress update · reduced-motion tab indicator
- Auditing the shared motion surfaces found a reduced-motion exception: detail-tab layout duration was zeroed, but opacity could use Motion's default transition. Made the regular opacity fade explicit and the reduced-motion transition duration zero across properties.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Browser reduced-motion walkthrough remains pending; T2/T7 remain open.


## Progress update · attachment reorder reduced motion
- Fixed a cross-feature inconsistency in the shared attachment workflows: entity and lead sortable rows now skip dnd-kit's animated transition for reduced-motion users, while preserving transform-based dragging.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Browser DnD/reduced-motion verification remains pending; T3/T7 remain open.


## Progress update · sortable reduced-motion sweep
- Extended the reduced-motion correction from attachments to the note tree and entity-linked task board. A source audit of all frontend `useSortable` owners now shows each omits the DnD transition under reduced motion while preserving transforms for actual dragging.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Direct pointer/keyboard DnD verification remains pending with the browser walkthrough; T3/T4/T7 remain open.


## Progress update · project-list failure feedback
- Prevented the main project list from flashing its empty state while retrying an empty SSR fallback, and hid the table's empty state after a no-data query error. Completed/lost lists now also show the retry error without claiming there are no matching projects; stale data stays visible on refresh errors.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Browser fault/retry flow remains unverified; T5/T7 remain open.


## Progress update · runtime verification status
- Current checks show the existing Next server still on port 3000 (PID 820022, ~13.8 GiB RSS / ~99% CPU). Linux desktop lease is human-held and Firefox BiDi on 9223 is unavailable, so this turn made no browser navigation, screenshots, build, or server restart.


## Progress update · avoid stacked page entrances
- Removed duplicate page-mount movement from common page headers, toolbars, CRUD content, and full-page Tasks/Customers surfaces. The route crossfade now provides the single route-level entrance; Analytics' data-ready widget stagger and the dynamic Bulk Actions entrance remain local.
- Targeted ESLint (6 files), typecheck, and `git diff --check` pass. Browser calibration remains pending: desktop lease is human-owned, Firefox BiDi is offline, and the existing server is left untouched. T2/T5/T7 remain open.


## Progress update · analytics report shared elements
- Extended shared-name handoffs from report tables into Contact and Lead details: Client Scorecard now shares the contact name; Stale Leads shares each lead name. Both use the existing reduced-motion-aware shared component.
- Targeted ESLint, frontend typecheck, and diff check pass. Browser interpolation remains unverified; T2/T7 remain open.


## Progress update · linked company/contact shared elements
- Added reduced-motion-aware company and contact name handoffs from Contact, Lead, and Project detail cards into the matching entity detail headings. Confirmed the Project contact card is rendered once, so IDs remain unique on that route.
- Targeted ESLint: 0 errors, 9 existing warnings; frontend typecheck and diff check pass. Browser calibration remains pending; T2/T7 remain open.


## Progress update · project report name handoff
- Added the cached project name to the QuickBooks report header and connected it to the project's existing desktop/mobile shared-name IDs. This reads `projectsKeys.list()` directly and adds no query/fetch; cold direct report links keep their number fallback.
- Targeted ESLint, frontend typecheck, and diff check pass. Browser layout/network verification remains pending; T2/T7/T8 remain open.


## Progress update · task surface transition and local URL state
- Added an accessible shared presence layer and a reduced-motion-aware crossfade for the four task surfaces, which share `/tasks` and do not trigger the route-level animation.
- Query-only task view/filter updates now use the App Router-integrated History API; the dynamic server loader previously reran on each `router.replace` even though filtered/view URLs skip its initial-board data path.
- Targeted ESLint, typecheck, and diff check pass. Browser focus/rapid-switch/network verification remains open; T2/T4/T7 remain open.


## Progress update · task transition interaction safety
- Preserved keyboard focus across task view changes and restricted task-detail portals to the currently present view, covering the shared-query case during a crossfade.
- Targeted ESLint (9 files), typecheck, and diff check pass. Browser focus/portal/rapid-interruption walkthrough remains pending under the human-owned desktop lease; T4/T7 remain open.


## Progress update · task calendar mobile overflow
- Corrected the calendar scroll boundary: the 980 px grid now lives inside a full-width, shrinkable horizontal scroller. This keeps the page viewport bounded while preserving access to all seven day columns.
- Targeted ESLint, typecheck, and diff check pass. The 456 px runtime overflow check remains pending with the browser walkthrough; T5/T7 remain open.


## Progress update · organic route entrance and outgoing overlays
- Reworked the route entrance to use a more visible 12 px spring settle with a restrained scale correction, softer 2 px blur, and a longer ease-out opacity; exits now move less so the incoming page carries the motion. Applied the same softer spring cadence to Task Board/List/Mine/Calendar changes.
- The presence context now reaches Radix portals. Dialog, alert dialog, sheet, dropdown/context menu, popover, select, and tooltip content unmounts while its source route/view exits, preventing stale overlays and focus traps above the crossfade.
- Targeted ESLint (11 files), frontend typecheck, and `git diff --check` pass. Visual calibration remains pending because the desktop lease is human-owned and Firefox BiDi is unavailable; no tests/build/server restart were run. T2/T4/T7 remain open.


## Progress update · isolated browser route-transition measurement
- Confirmed the Firefox BiDi endpoint is still unavailable and the desktop lease remains human-owned. Found the already-running isolated headless Chromium session on port 9225 and used it without touching the personal browser or CRM data.
- A client-side transition from `/settings/users` to `/projects/completed` rendered the incoming route from opacity 0 / y=12 px / scale 0.988 / blur 2 px toward its final state. The outgoing route became `aria-hidden`, `inert`, and ended at opacity 0; the incoming route settled at opacity 1 with no transform or blur. At `/projects/completed`, document/body/main widths were all 456 px at the narrow viewport and 1440 px at desktop width.
- This provides runtime evidence for one route and two viewport widths, not a human judgment of perceived naturalness or the full route/interaction walkthrough. No screenshots, tests, build, or server restart were run. T2/T5/T7 remain open.
- With `prefers-reduced-motion: reduce` emulated, a client route change rendered both outgoing and incoming layers at opacity 1, with no transform or blur; the outgoing layer remained inert. The media emulation was cleared after the check.


## Progress update · restore shared-layout coordinator
- A current-source audit found that `AppShell` had no `LayoutGroup`, despite the plan recording one as the fix for task card/detail shared elements. The app contains route-spanning layout IDs for task cards/titles, project/entity names, attachment images, tabs, and sidebar selection. Added one stable `LayoutGroup id="maros-app"` around the authenticated shell so source and destination elements, including portaled task detail, share the same coordinator.
- Targeted ESLint (6 motion owners), frontend typecheck, and `git diff --check` pass. The headless Chromium CDP session on 9225 has ended and Firefox BiDi on 9223 remains unavailable, so task/image interpolation cannot be sampled in this turn. T2/T3/T4/T7 remain open.


## Progress update · direct task-link transition fallback
- The task shared-source hook treated its initial non-null `?task=id` as a newly opened detail and could match a card during first paint. It now initializes its previous-ID reference from the current URL state, so only a later in-session null → task-ID transition can claim a mounted card/title as the shared source. Cold links retain the regular detail entrance.
- Targeted ESLint (hook and detail owner), frontend typecheck, and `git diff --check` pass. Browser direct-link and in-session open/close checks remain pending because the isolated Chromium is no longer running and the human holds the desktop lease. T4/T7 remain open.


## Progress update · remove duplicate dashboard section entrance
- Rechecked the analytics exception against its actual trigger: `DashboardWidgets.Section` animated every mount with a 120 ms stagger, so its movement stacked with the new route entrance and was not data-driven. Removed that wrapper animation; `AsyncWidget`'s existing content reveal still runs when data arrives, and the selection-driven Bulk Actions entrance remains.
- Targeted ESLint (dashboard widgets and data/widget owners), frontend typecheck, and `git diff --check` pass. Runtime animation timing remains unverified without an agent browser; T2/T7 remain open.


## Progress update · task expansion and focus-return verification
- Reused the isolated headless Chromium profile and made a real pointer click on a task title. The detail dialog opened with focus inside; its shared surface expanded from roughly 343 px to 733 px by 350 ms and settled by 700 ms. Escape closed it, kept the task-list scroll at 569 px, and returned focus to the originating task button after the source-target focus fix.
- Before the fix, the same keyboard close after a programmatic opening left focus on `body`; after the fix, the real pointer flow restored the task button. Targeted ESLint (5 task owners), frontend typecheck, and `git diff --check` pass. Full visual judgment and direct-link/reduced-motion variants remain open; T4/T7 remain incomplete.


## Progress update · direct-link and reduced-motion runtime checks
- A cold browser navigation to `/tasks?task=29` rendered 43 task cards and opened the detail with no shared background shell, confirming the normal entrance fallback. Escape removed the query and closed the dialog; a follow-up focus sample found the matching task title button focused after the dialog exit.
- Started Chromium with `prefers-reduced-motion: reduce` emulated before document load. The direct task detail again had no shared shell and the overlay had `transition-property: none`. On a client navigation from `/projects/completed` to `/settings/users`, the destination remained at opacity 1, transform none, blur 0; only one route layer existed after 120 ms. Cleared emulation on the blank QA tab afterward. T2/T4 reduced-motion/source fallback now have focused runtime evidence; full route and visual walkthrough remains open (T7).


## Progress update · avoid nested Analytics data entrance
- The dashboard's `AsyncWidget` and KPI cards both ran opacity/lift entrances on the same data-ready render. Added a narrow `animateOnLoad` option and disabled only the outer entrance for the KPI overview, leaving its six-card stagger and the widget's refetch dimming intact.
- Targeted ESLint (3 Analytics owners), frontend typecheck, and `git diff --check` pass. The project detail at 456 px had document/body/main widths of 456 px, but the `/notes` load stalled under the existing high-load dev process and its renderer stopped answering; viewport emulation was cleared by CDP. No server restart/build/tests. T5/T7 remain open.


## Progress update · organic page entrance follow-up
- David reported that the route entrance still felt unnatural. Removed the full-page scale and blur, which made all page content zoom and soften together; unified route and task-view entry on a small 8 px spring settle with a short opacity fade and slight outgoing fade.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. This revision has not been visually calibrated in the browser; no tests, build, or server restart were run. T2/T7 remain open.


## Progress update · shared overlay depth
- The shared Dialog, AlertDialog, and Sheet overlay was using a 4 px blur under a 65% opaque background, muting the page behind it. Increased the blur to the standard 8 px backdrop and softened the scrim to 55%, with a 250 ms opacity/filter transition; reduced-motion still disables the transition.
- Targeted ESLint (overlay owners), frontend typecheck, and `git diff --check` pass. Visual browser calibration remains pending; no tests, build, or server restart were run. T6/T7 remain open.


## Progress update · project name shared-element amplification
- Source review found the project name entered its detail header at nearly the same size as the table label. Increased the matching desktop/mobile destination to 20 px and aligned the cached skeleton target, making the existing shared layout transition read as an enlargement. The name editor is now visible on touch-sized layouts and has an accessible label; desktop keeps the hover/focus reveal.
- Targeted ESLint reports 0 errors and 3 pre-existing `no-explicit-any` warnings in `ProjectDetailsPage.tsx`; frontend typecheck and `git diff --check` pass. Browser calibration remains pending because the desktop lease is human-held and Firefox BiDi is unavailable. No tests, build, or server restart; T3/T7/T8 remain open.


## Progress update · touch-visible task and note actions
- A source audit found opacity-hidden task completion, task actions, task drag, note-tree drag, and note removal controls; these depended on mouse hover for discovery. They now stay visible on touch and compact layouts, while large pointer layouts retain hover/focus reveal. All controls retain keyboard focus visibility and reduced-motion-aware opacity transitions.
- Targeted ESLint (5 owners), frontend typecheck, and `git diff --check` pass. Source search found no remaining fully opacity-hidden task/note action controls; the remaining desktop-only note-tree context action is already visible on small screens. Browser touch walkthrough remains pending under the human desktop lease; no tests, build, or server restart. T4/T5/T7 remain open.


## Progress update · global reduced-motion fallback
- Added a global `prefers-reduced-motion` fallback that reduces CSS animation/transition timing and disables smooth scrolling, covering shared controls whose local classes omitted motion-reduce variants. Existing loading-sheen/spinner overrides remain in place.
- `git diff --check` passes. No tests, build, or browser emulation were run; the Linux desktop lease is human-held and Firefox BiDi is unavailable. T2/T6/T7 remain open.


## Progress update · rapid route crossfade cleanup
- The common page transition used its entry spring for the outgoing layer's final 2 px displacement, so exit presence could outlast the 240 ms fade during rapid navigation. Removed the outgoing displacement; the departing route now fades while only the incoming route settles, reducing stale inert layers without weakening the crossfade.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Rapid-navigation browser verification remains pending: desktop lease is human-held, Firefox BiDi is offline, and the running dev server is using roughly 18 GB RSS. No tests, build, or restart; T2/T7 remain open.


## Progress update · command-palette editor shortcut safety
- The global `Ctrl/⌘ K` listener previously intercepted the shortcut even while a text field or rich-text note editor was active, overriding native editing commands. It now ignores editable controls, already-handled events, and IME composition so the palette shortcut only runs in non-editing contexts.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Keyboard behavior still needs a browser walkthrough; desktop lease is human-held and Firefox BiDi is offline. No tests, build, or server restart; T1/T7 remain open.


## Progress update · command-palette mobile search layout
- The shared dialog close control sat over the global search input's right edge, and the default dialog width reached the mobile viewport edges. Added input-side clearance for the close control and a 16 px viewport gutter with a viewport-relative max height.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. Browser mobile visual confirmation remains pending under the human-held desktop lease; no tests, build, or server restart. T5/T7 remain open.


## Progress update · command-palette input naming and local server
- Added an explicit accessible name to the command-palette input. Source audit found no parent-level permission field on sidebar groups, so recursive route collection does not bypass a group permission; the leaf permissions remain filtered.
- Restarted the previously stopped local frontend under David's earlier explicit request to run it. Port 3000 is listening; `/login` returns the local debug-session redirect to `/dashboard`. First root compilation took about 20 seconds and the dev worker climbed to ~5.6 GB RSS, so I did not trigger more page compiles. The desktop lease remains human-held and no browser session is available for visual checks.
- Targeted ESLint, frontend typecheck, and `git diff --check` pass. No tests, build, or deploy. T1/T7 remain open.


## Progress update · palette visual and reduced-motion QA
- Used a separate headless Chromium profile (no personal Firefox/desktop control) against the running local app. Dashboard screenshots at 1440×1000 and 456×900 show the responsive cards and filter panel within the viewport. At 456 px, the command dialog measured x=16 / width=424 / right=440, document width=456, and computed 12 px corners; the screenshot shows its close control clear of the search text and the blurred backdrop.
- Emulated `prefers-reduced-motion: reduce` in that page: dialog and overlay transition durations were 0.01 ms, dialog animation duration 0 s, and root scroll behavior `auto`; cleared media emulation and stopped the isolated browser. `/dashboard` returned 200. No tests/build; the route-wide walkthrough remains open because this covers one route and the palette only (T2/T5/T6/T7).
- The earlier note that no automation browser was available referred to attached browser services; an isolated system Chromium was available and supplied this focused evidence. The dev server remains active on port 3000.


## Progress update · cache-first project handoff and shared title
- Verified warm `/projects/construction` → `/project/144` navigation from a visible project card in isolated Chromium. No `/api/projects/*` request fired during the handoff; the destination rendered the project name and its shared 20 px heading moved from the card into the detail header. A cold direct `/project/144` load also rendered the project heading with no alert. The frontend calls the explicitly versioned `/projects/v2/all` read model; the previous `/projects/all` route remains in place, and the controller's `projects:read` permission applies to both.
- T8 complete. Full route inventory and cross-feature browser walkthrough remain incomplete (T1/T7).


## Progress update · stable notification IDs and route sweep
- Clean browser traces isolated the hydration mismatch to the two responsive `NotificationBell` instances. Replaced their implicit Radix `aria-controls` values with stable per-instance content IDs; the experimental AppSidebar Suspense boundary was removed because delayed mobile hydration could mismatch the responsive sidebar tree. Fresh reloads of Receivables and Client scorecard show zero console errors and zero alert nodes. Targeted ESLint, frontend typecheck, and `git diff --check` pass.
- Walked all 45 static route wrappers at desktop width and 9 representative product areas at 456 px. Static pages returned 200 documents and rendered headings; main scroll widths fit their containers. Task list/mine, Projects, Leads and local login redirects landed on their expected canonical paths. The 456 px pages showed no document/main overflow. Dashboard's initial 57 skeletons coincided with compiling the route set; a cold reload after compilation loaded all widgets, with endpoint timings 317–1,031 ms and all statuses 200. Dynamic record routes, public-note tokens, overlays, and interaction-level route review remain pending; T1/T7 are incomplete.


## Progress update · task card expansion and attachment image shared transition
- Verified the task board at 456 px with 43 cards. The card-to-detail shared surface expanded from the selected card; the original spring overshot to 1.034 scale around 300 ms. Matched the source and destination springs at stiffness 150/damping 28; the repeat settled near 0.997 scale without that overshoot. Escape closes the detail and returns focus, reduced-motion skips transforms, and a cold `/tasks/T-29` load renders the detail without a mounted card or loading/error state. DnD, nested actions, and child-task navigation remain unverified, so T4 stays open.
- Runtime review found that the attachment image viewer had matching `layoutId` values but no actual shared layout animation: the destination only received its ID after loading. The destination now mounts as a shared wrapper after a hidden preloader finishes, while thumbnail and modal wrappers use the same per-file layout ID. On a real lead image, the modal image geometry changed during the transition; the backdrop computed to `blur(8px)`, Escape returned focus to the thumbnail, and reduced-motion opened without a transform. A project's generic attachment section opened its PDF through the existing embed path. The dev dataset has no project/company image attachment, so only the lead image path supplies image-transition runtime evidence; T3 remains open for DOCX, failure, and additional close/keyboard variants.
- `npx eslint` on the five changed owners, `npm run typecheck`, and `git diff --check` pass. No tests or build were run. The web unit was inactive after the earlier Next dev process crashed at a recorded 19.1 GB peak; `dev-maros start` restored the local environment (Postgres healthy, API active, web active), and `/tasks` returned HTTP 200. T1/T2/T3/T4/T5/T6/T7 remain open; T8 remains complete.

## Progress update · mobile sidebar hydration and route motion verification
- Reproduced a Radix menu ID hydration mismatch only at a 500 px viewport. Replaced the mobile breakpoint hook's effect-driven state with `useSyncExternalStore` and a stable server snapshot. Clean local browser reloads at 500 px and 1440 px have no Next.js issue or hydration error; the desktop user menu opens and dismisses by Escape.
- Sampled Dashboard → Projects route motion: the new layer starts at opacity 0 / y=7 px, is ~0.98 opacity / y=2.7 px by ~160 ms, and settles by ~750 ms; the outgoing layer is inert during the overlap. `/projects/construction` → `/project/144` animated the matching project name from 140×18 px to 201×25 px and fired no `/api/projects` request. Both paths fit their viewport; `/project/144` returned 200.
- Targeted ESLint on the breakpoint and motion owners, frontend typecheck, `git diff --check`, and direct local route/browser checks passed. No tests/build/server restart. Dynamic/public-note flows, nested overlays, touch focus, task DnD and child navigation, and the remaining route-wide walkthrough keep T1/T2/T4/T6/T7 in progress.

## Progress update · task board action menu and drag cancellation
- At 1440 px, the local task board rendered 129 cards without page-level overflow. The task action menu opened with six items; Escape dismissed it and restored focus without changing the route or issuing a task request.
- Pointer drag activated the card placeholder; Escape/release restored the same 129-card order with zero `/api/tasks` requests. Space activated the keyboard drag sensor and Escape was sent to cancel. No task state was changed. A drop that persists a move, nested action branches, and child-task navigation still need review (no visible subtask counters were present on this board).
- T4/T7 remain open. No tests, build, or server restart.

## Progress update · mobile task detail, public expiry, and Users route
- At 456 px, opening a task card rendered one detail dialog with document/main widths at 456 px. After detail data arrived, the Details/Subtasks tabs responded; this selected task had no children, so Subtasks showed the correct empty state and disabled blank Add. Escape removed the task query and restored focus to the originating card.
- A synthetic invalid placeholder path rendered the public expired-link message at 456 px with `no-referrer`, no authenticated shell/palette/route layer, and no page overflow. No real share token was used.
- The 456 px Users route resolved its prior inconclusive loading state: staff rows rendered in the page's local horizontal table viewport while document width stayed 456 px. A role selector opened four options; Escape closed it and returned focus. No write request was issued.
- T1/T4/T6/T7 remain open for the live public reader/unlock flow, a task with real subtasks, nested overlay cases, and remaining route walkthrough. No tests, build, or server restart.

## Progress update · organic route-entry motion refinement
- Increased authenticated route entry from 7 px to 10 px and switched its vertical settle to a lightly underdamped spring (`185/22/1`) with a shorter ease-out opacity fade. The project/entity-name shared spring now uses matching physics. The global zoom and blur remain absent.
- The local `/tasks` route returned HTTP 200. An isolated 456 px client-navigation sample showed the incoming route begin at opacity 0 / y=10 px, crossfade while the outgoing layer was inert, and finish within the sampled 320 ms window. Fine-grained frame sampling timed out; exact timing and subjective visual calibration remain approximate.
- Focused ESLint, `npm run typecheck`, and `git diff --check` passed. No tests, build, or server restart. T2/T7 remain open.

## Progress update · route-transition keyboard focus recovery
- Reproduced focus remaining on a button inside the outgoing route after it became `aria-hidden` and inert, then falling to `body` when the exit layer unmounted. Added `tabIndex={-1}` to the persistent main landmark and moved focus there on pathname changes after restoring the destination scroll position (`preventScroll`).
- Isolated Chromium at 456 px confirmed focus stayed on `main` throughout the crossfade and after the outgoing layer unmounted. Pressing Tab then reached the destination route's first control. No CRM state changed.
- Focused ESLint, `npm run typecheck`, and `git diff --check` passed. T2/T7 remain open for back/forward, rapid navigation, reduced motion, and broader route coverage.

## Progress update · reduced-motion preference consistency and verification
- Replaced the installed Motion hook in 14 app animation owners with the existing `usePrefersReducedMotion` subscription. Motion 14.1's hook initializes a static `useState` value and has a TODO for reacting to later preference changes; the app-owned subscription follows `prefers-reduced-motion` with `useSyncExternalStore` across route, shared-name, task, project, sidebar, and attachment transitions.
- With reduced motion enabled before reload, isolated Chromium navigated `/tasks` → `/projects` at 456 px with opacity 1 and no transform. Scroll restoration and browser Back restored Projects to 260 px; keyboard focus remained on the persistent main landmark. CDP emulation changed `matchMedia().matches` without dispatching `MediaQueryList`'s `change` event, so a mid-session preference toggle remains inconclusive.
- Full `npm run lint` passed with 0 errors and 164 warnings; `npm run typecheck` passed. `npm run build` passed in an isolated worktree copy and generated all 41 static pages. Existing warnings: deprecated middleware convention, `jose` Edge Runtime compression streams, and `tailwind.config.ts` module type. No tests/server restart. T2/T7 remain open for rapid navigation and the remaining route/interaction walkthrough.

## Progress update · nested task menu and dialog keyboard behavior
- The 456 px board rendered 43 cards; the authenticated task list API reported 56 tasks and no parent/child tasks. No CRM records were created to force a child-navigation test.
- Reproduced the Priority submenu's Escape closing both levels. TaskActionsMenu now closes only the submenu on first Escape, returns focus to Priority, closes the parent on the next Escape, and resets submenu state when the root closes. Reopen/close runtime verification passed with zero non-GET task requests. This matches the [WAI-ARIA menu pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/) for Escape in a submenu.
- Verified the nested archive AlertDialog: Escape closes the alert, leaves the task detail and `?task=` open, and returns focus to “More task actions”; a second Escape closes detail. No writes fired.
- Rapid direct history changes ended with one active Calendar layer after ~2.3 s; at 1.3 s the exiting layers were still present and the incoming layer had not settled. Real sidebar clicks through Contacts and Calendar settled at Calendar with one active layer and no alert. Keep T2 open for additional rapid-navigation/content-readiness evidence.
- Full lint passed (0 errors, 164 warnings), typecheck passed, and an isolated production build generated all 41 pages. Build warnings include the deprecated middleware convention and `tailwind.config.ts` module type. `git diff --check` passed. T4/T6/T7 remain open for child-task navigation, DOCX/failure, remaining overlay, and route coverage.

## Progress update · organic route-entry motion follow-up
- Adjusted route entry from a straight 10 px lift to a damped spring with 8 px travel, minimal scale (0.992→1), and brief subtle blur (4 px→0); exit gets a small upward drift and 2 px blur while fading. Reduced-motion behavior remains handled by the shared presence layer.
- `/tasks` returned HTTP 200; targeted ESLint, typecheck, and `git diff --check` passed. No tests or restart. CUA listed no browser, so graphical motion calibration remains open under T2/T7.

## Progress update · keep route exits interruptible
- Review found the route exit had regained displacement and blur, which can extend outgoing presence during rapid navigation. Kept the organic motion on entry and returned exit to an opacity-only fade so the outgoing layer does not run the entry spring.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. The existing Next process uses about 10 GiB and a project-route request timed out; no extra compilation or restart was triggered. T2/T7 still need rapid-navigation timing and broader visual walkthrough evidence.

## Progress update · task shared-surface and backdrop runtime check
- In isolated authenticated Chromium at 500 px, a real pointer click on the task title opened the shared detail surface, which expanded from its source card to the mobile full-screen panel. The overlay computed to `blur(8px)` and the expected 55% scrim.
- Escape closed the task detail and cleaned `?task=`; after the exit interval focus returned to the same title button. No task mutation was performed. T2/T7 remain open for rapid route navigation and the complete route walkthrough.

## Progress update · DOCX preview recovery
- Added in-dialog retry for failed DOCX conversion. Network failures now show stable recovery copy instead of exposing a raw browser error; users can retry conversion or open the source document. The existing 15-second timeout and safe-HTML sanitizer remain.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. No tests or server restart. Runtime DOCX success/failure check remains open under T3/T7 because the active Next process is using about 10 GiB and route compilation was deferred.

## Progress update · image preview recovery
- Added an in-place image-preview retry next to “Open image”; retry restores the loading state so the image can render and use the existing shared thumbnail-to-viewer layout animation again.
- Targeted ESLint, frontend typecheck, and `git diff --check` passed. Authenticated contact-tab CDP evaluation timed out twice while Next used about 10.5 GiB / 80% CPU; no restart. Image failure and DOCX runtime cases remain open under T3/T7.

## Progress update · mobile route navigation and T2 completion
- Reproduced the mobile sidebar remaining open over the destination route after selecting a link. Sidebar navigation now closes the mobile sheet on Next client navigation, and pathname changes close it for browser Back/Forward. `RouteTransition` then leaves focus on the persistent main landmark.
- In isolated Chromium at 500 px, `/tasks` → `/dashboard` closed the sidebar, removed its dialog overlay, crossfaded the outgoing route as inert with the incoming route, and settled to one layer. The destination had no page-level overflow; focus was on `main`. A rapid Back then Forward sample also settled to one active layer within 500 ms with focus maintained on `main`.
- Reduced-motion before reload, first-load suppression, login/public/legal route exclusions, scroll continuity, and regular client-navigation crossfades already have focused evidence in prior entries. Targeted ESLint, frontend typecheck, and `git diff --check` pass; no tests, build, or server restart. T2 is complete; T1/T3/T4/T5/T6/T7 remain open.
- Directly loaded the legacy `/tasks/list` alias in Chromium; it redirected to `/tasks?view=list`. After document readiness, the authenticated shell had exactly one route layer at opacity 1 and no intermediate transition layer. This closes T2's redirect and first-load check.

## Progress update · organic route-entry motion follow-up (2026-10-12)
- Refined the shared route entrance to use 12 px of lift, a 0.99 scale start, and a lightly underdamped spring (`125/19/1`) for a softer settle. Opacity and the subtle 2 px blur now ease out over 340/400 ms. Exit remains opacity-only, and the shared presence layer still applies the reduced-motion preference.
- Focused ESLint, frontend typecheck, and `git diff --check` passed. I attempted to sample a client transition in the isolated Chromium tab, but the current lead page did not expose the expected `/tasks` navigation anchor, so this timing change has not been visually calibrated in-browser. No tests, build, or server restart; T2/T7 remain open for further visual review.

## Progress update · T3 attachment preview verification complete (2026-10-12)
- The shared viewer is owned by `features/attachments`; the former leads path re-exports it. Existing browser evidence covers the per-file image shared-element geometry, blurred dialog backdrop, and reduced-motion opening without transforms. A DOCX loaded successfully, then a controlled network failure showed its retry/open-original recovery and retry loaded the preview.
- In the current isolated Chromium tab at 500 px, intercepting one PNG request produced the image error with retry; disabling interception and retrying loaded the image. Escape closed the modal and returned focus to the same thumbnail. Space opened the image preview and Escape restored focus. A PDF opened from its focused preview button and Escape closed it with focus returned. Document width stayed 500 px.
- T3 is complete. No tests, build, or server restart; T1/T4/T5/T6/T7 remain open.

## Progress update · route entrance calibration and task direct route (2026-10-12)
- On a real mobile client navigation at 500 px, sampled the new route layer at opacity 0.39, scale 0.990, y=11.5 px, and blur 1.3 px; the exiting page was already inert and fading. By ~300 ms the incoming layer reached opacity 1, transform none, blur 0, and the old layer had unmounted. The persistent scroll main retained focus and the document stayed 500 px wide. This visually calibrates the organic entrance parameters that were unverified in the preceding note.
- Direct-loaded `/tasks/T-29` with no card mounted as a shared source. The task rendered in page mode without a dialog or load error, and the 500 px document/main had no horizontal overflow. T4 remains open for task-card keyboard/close, DnD, nested actions, reduced motion, and child-task navigation coverage.

## Progress update · responsive layout sample and sidebar hydration correction (2026-10-12)
- At 456 px, `/projects/construction` fit the document and route main at 456/441 px respectively while retaining one local horizontal table scroller. `/reports/clients` rendered 50 rows with document width 456 px and main width 441 px. Dashboard also fit 456 px. The project and client-scorecard screenshots were visually inspected; T5 remains open for Notes, Tasks, Leads, Calendar, and desktop coverage.
- The client scorecard showed a real Next.js hydration issue in the sidebar account `DropdownMenuTrigger`: its Radix-generated ID differed between server and narrow client when the sidebar switches into its mobile Sheet tree. Gave the single account menu explicit stable trigger/content IDs and controlled its open state so `aria-controls` and `aria-labelledby` remain paired. Reload at 456 px now reports no issue badge or hydration error. Space opens the menu, the ID relationships match, Escape closes the menu and returns focus, and a second Escape closes the mobile sidebar.
- Focused ESLint on `AppSidebar.tsx`, frontend typecheck, and `git diff --check` pass. No tests, build, or server restart; T5/T6 remain open for the rest of their route and overlay matrices.

## Progress update · lead project-type loading states and route entrance follow-up (2026-10-12)
- Propagated first-fetch, error, cached-option and retry states for project types across lead create/edit/review, contact lead creation, and lead detail inline editing. Empty selectors now disclose loading or unavailable state; failed refreshes retain cached options and expose retry. Focused ESLint passed with 0 errors/20 existing warnings, frontend typecheck and `git diff --check` passed, and an isolated production build of the current tree generated 41 static pages and listed 59 routes.
- After David's request for a more organic route entrance, removed the global route scale and blur, leaving an 8 px spring lift with a soft opacity ease-out. The previous browser timing sample described the superseded animation; this profile still needs visual review. The Linux computer-use lease is held by the human and Firefox BiDi 9223 currently refuses connections, so no browser control was attempted. No tests or server restart. T1/T4/T5/T6/T7 remain open.
- Comprobé el estado local antes de iniciar: `forja-maros-web` había terminado por OOM. Usé el `dev-maros start` ya autorizado; el servicio quedó activo y `/notes` respondió HTTP 200 en 1.74 s tras la compilación inicial. No lo reinicié después. La lease Linux sigue humana y BiDi de agentes no conecta, por lo que esta comprobación no sustituye al walkthrough visual.

## Progress update · isolated responsive walkthrough and shared motion evidence (2026-10-12)
- At 456 px, visually inspected Projects, Notes, Tasks, Leads, Calendar, Receivables, Client scorecard, and Users. All eight report document/body/main width 456 px; wide tables keep a local scroller and the task board scrolls its own columns. At 1440 px, visually inspected Dashboard, Projects, Leads, Tasks, Notes, Calendar, Receivables, Client scorecard, and Users; all nine report document/body width 1440 px and main width 1184 px, with no page overflow. Project names are visible in the list cards.
- On hydrated client navigation Projects → `/project/144`, the outgoing route became inert and faded while the incoming route entered at opacity 0/y=8 px, reached opacity ~0.96 by 155 ms, and settled toward y=0 over ~500 ms. The same project name appears at source/destination; only `/api/projects/144/cost-breakdown` was requested after navigation, with no list or financial-summary refetch.
- Opened task T-29 from a board card at 456 px: the shared surface expanded from 270×140 px toward 448×869 px in ~500 ms. Escape cleaned `?task=29`, closed the dialog, and restored focus to the original task-title button. Saved views resolved normally and `/api/task-saved-views` returned 200.
- No tests or server restart. T1/T4/T5/T6/T7 stay open for remaining route families, DnD/nested actions/child navigation, full overlay matrix, and final route walkthrough. The active dev server answers HTTP 200; it uses ~10.3 GB RAM at the latest check.

## Progress update · nested task-dialog focus restoration (2026-10-12)
- Reproduced a focus loss in the task cancellation flow: Escape closed the nested cancellation dialog but left focus on `body` while the parent task detail stayed open. Added an explicit ref to the “Cancel task…” trigger and restore focus there on ordinary nested-dialog close. Successful cancellation still returns focus to the task status control. Verified the nested textarea, two stacked dialogs/8 px backdrops, Escape closing only the inner dialog, and focus returning to the trigger; no cancellation mutation was submitted.
- Focused ESLint, frontend typecheck, and `git diff --check` pass. No tests, production build, or server restart. T6 remains open for the broader overlay/focus matrix; T1/T4/T5/T7 remain open.


## Progress update · route entrance spring refinement (2026-10-12)
- Refined the shared route entrance after David reported the previous motion still felt mechanical: the incoming page now rises 12 px from a 0.992 scale with a lightly underdamped `190/17/0.8` spring, while opacity eases over 380 ms. Kept the outgoing layer opacity-only so rapid navigation remains interruptible; the shared presence layer still honors reduced motion.
- Focused ESLint, frontend typecheck, and `git diff --check` pass. The local web service is active and `/` returned HTTP 200. No tests, build, server restart, or browser calibration of this exact spring profile was run. T1/T4/T5/T6/T7 remain open.


## Progress update · task status selector and route spring calibration (2026-10-12)
- In isolated Chromium at 456 px, opened T-29's nested status selector and pressed Escape. The listbox closed while the task detail stayed open, and focus returned to the status combobox; no task update was submitted. T6 remains open for the broader nested-overlay matrix.
- The previous route spring sample reached opacity 0.97 by about 100 ms and was visually settled around 320 ms, which supported the report that entry felt rushed. Softened the shared route spring from `190/17/0.8` to `145/19/1` and extended opacity easing from 380 to 420 ms. Focused ESLint, typecheck, and `git diff --check` pass. A post-change client-navigation sample did not start reliably in the isolated Chromium session, so the new profile still needs visual calibration. The local server remains active and `/tasks` returns HTTP 200. No tests, build, or server restart. T1/T4/T5/T6/T7 remain open.


## Progress update · task action submenu Escape behavior (2026-10-12)
- In isolated Chromium at 1440 px, opened T-29's task action menu and opened the Priority submenu with ArrowRight. The first Escape closed only that submenu and restored focus to the Priority item; the second closed the root menu and restored focus to the original Task actions trigger. No priority action was selected. This closes the nested action-menu portion of the T4/T6 check; the remaining DnD, task keyboard-entry, and broader overlay cases stay open.
- The updated global route spring still lacks a reliable post-change visual timing sample: repeated navigation attempts in this authenticated headless session remained on `/tasks`. No code was changed in this verification pass.


## Progress update · nested task action menu browser check (2026-10-12)
- Confirmed the isolated Chromium harness must dispatch a pointer sequence for Radix dropdown triggers; `.click()` alone does not open them. At 1440 px, the T-29 action trigger has a visible 24 × 24 px target. The menu opens and Escape restores focus to its trigger. ArrowRight opens Priority; Escape closes only the submenu and restores focus to Priority; a second Escape closes the root and restores focus to Task actions. No task mutations occurred.
- T4/T6 still need the rest of their interaction matrices (DnD with non-persistent/mocked effects, task keyboard entry, child navigation, and additional overlays). The route entrance profile `145/19/1` still needs a reliable after-change client-navigation sample; earlier retries did not navigate.


## REQ-004 · calmer project-name and route entrance
- Reworked the authenticated route entrance after David's feedback: removed the scale transform, shortened the vertical lift to 8 px, and used a restrained spring (`120/22/1`) with a 300 ms fade. Route exits now fade over 160 ms so rapid navigation can hand off sooner. Project-name shared elements now use their own softer spring (`140/24/1.1`) instead of inheriting the generic shared-name timing.
- Focused ESLint on both motion owners, `npm run typecheck`, and `git diff --check` passed. The local project route returned HTTP 200 in 13.05 s after HMR. The exact revised interpolation was not captured reliably in the isolated browser, so visual acceptance remains open; no tests or build were run. T2/T7 remain open.

## REQ-004 · Projects cache-first when returning from detail
- David reported that the project name and number took too long to reappear. The route awaited server-side `loadProjectsData()` before mounting `ProjectsPage`; its loading fallback did not have the project list in its QueryClient and showed a skeleton during that wait. Removed the route-level wait so the client page can reuse its existing query, while cold entry still fetches through the client.
- Headless Chromium completed Projects → `/project/144` → back and showed the row with `Plumbing Managment` and `100-0826` before the 700 ms capture. `/projects/construction` and `/project/144` returned HTTP 200. Typecheck, focused ESLint, and `git diff --check` passed. No tests or build.

## REQ-004 · correction: project identity return animation
- The prior 700 ms browser capture was too late to isolate the delay and led me to over-attribute it to server loading. A frame-by-frame return trace showed the cached name and number already present at ~17 ms but still projected away from their table cells by the 500 ms shared-layout transition; they settled near ~80 ms only after shortening it.
- Changed the project shared transition to a 220 ms ease-out. In headless Chromium the fields were within about 2 px of their cells by ~80 ms and had no transform by ~216 ms. Typecheck, focused ESLint (0 errors; 3 pre-existing `any` warnings), and `git diff --check` passed. No tests or build.

### Follow-up: suppress reverse project pairing
- David confirmed the visual delay persisted. The duration change only made the reverse shared-element move faster; it did not remove the pairing. Added route-aware suppression for project shared layout IDs when transitioning from `/project/:id` back to `/projects/*`, for both the exiting detail and incoming list.
- Replayed the round trip in headless Chromium. At the first return sample (~30 ms), `Plumbing Managment` and `100-0826` were present and neither had a transform; the matched list nodes stayed at their table positions. TypeScript typecheck passed; focused ESLint had 0 errors and 3 pre-existing `any` warnings; `git diff --check` passed. No tests or build.

### Follow-up: preserve the next project entry
- The prior fix removed shared IDs during the return, which also removed the source needed by the next project entry. Kept those IDs mounted and made only the return layout transition instant. The route transition clears that mode after exit, and memoized table columns now respond to its change.
- Replayed A → back → B → back → A in Chromium at 1440 px and 456 px. The name and number projected from the table on all three entries and settled; each return showed both at opacity 1 with no transform from the first sampled frame. Cycle 2 used browser history back. Typecheck and focused ESLint passed (0 errors; 3 existing `any` warnings); full build passed from an isolated workspace. Full ESLint passed with 164 warnings and 0 errors; `git diff --check` passed.

### Correction: project outlet flicker
- The previous opacity-only trace missed an ancestor hiding the incoming table. The expanded trace checks inherited visibility, opacity across ancestors, missing frames and duplicate outlets. Before this fix, name/number were hidden through ~176–208 ms and 52 rows were mounted during exit.
- Replaced project outlets without an exit overlap and scoped shared layout IDs to each visit to Projects. The return creates a new scope; subsequent list/detail entries share it. Updated all project-name consumers to retain their matching IDs. The report test harness now includes its required QueryClient provider.
- A → back → B → back → A passed at 1440 px and 456 px, including history back: no hidden return frames, one table (26 rows), and all six entries animated name and number. Full ESLint (0 errors/164 warnings), typecheck, isolated build, four focused tests and `git diff --check` passed.


## REQ-004 · shared project-number handoff
- Extended the existing project-name shared element to include the project number. The desktop table and mobile project card now expose responsive `layoutId`s for the same `leadNumber`; the detail heading and its cached-data skeleton provide matching desktop/mobile targets. The visible number remains unchanged in the source (`100-0826`) and reads `Project #100-0826` in the destination. Reduced-motion users still omit the layout IDs.
- Headless Chromium navigated from `/projects/construction` by clicking project 144 at both 1440 px and 456 px: the desktop row and mobile card showed `100-0826`, and the destination heading showed `Project #100-0826` with the matching responsive target. The mobile destination document stayed 456 px wide. The local route returned HTTP 200 in 1.28 s. Focused ESLint passed with 0 errors and 3 existing `any` warnings in `ProjectDetailsPage.tsx`; frontend typecheck and `git diff --check` passed. No tests or build were run.


## REQ-004 · project-number shared-element rendering fix
- David reported that the project number still did not animate. A headless trace showed Motion generating a scale/translation matrix for the destination, but the number nodes were ordinary inline spans; CSS transforms do not move non-replaced inline boxes. Changed the source and destination number spans to `inline-block` while retaining the separate desktop/mobile layout IDs.
- Replayed `/projects/construction` → `/project/144` in headless Chromium. At the transition midpoint the visible number had `display:inline-block` and a projected transform (`scale` about 0.89, vertical translation about 94 px); after settling it reached identity transform at the project heading. Captured `/tmp/maros-project-number-mid.png` and `/tmp/maros-project-number-settled.png`. Project detail returned HTTP 200. Focused ESLint had 0 errors (3 existing `any` warnings), frontend typecheck and `git diff --check` passed. The mobile source/target content was confirmed, but its interpolation was not captured in this run. No tests or build were run.

## REQ-004 · Projects name/number visibility after returning (2026-10-12)
- Reproduced Projects → `/project/144` → volver. Motion left two copies of the shared origin mounted during the route handoff and crossfaded the active name/number to opacity 0. Set `layoutCrossfade={false}` for the project name/number pairs, including cached detail targets and QBO project name; preserved the generic `SharedEntityName` default. Made source name spans `inline-block` so transforms apply.
- Headless Chromium confirmed name and number visible with opacity 1 after return, and a non-identity projection matrix at the detail-entry midpoint. Focused ESLint and `npm run typecheck` pass; 3 existing `any` warnings remain in `ProjectDetailsPage.tsx`. `git diff --check` passes. No tests or build.

## REQ-004 · reducir saltos al entrar a Projects detail (2026-10-12)
- La ruta completa y los shared elements se movían simultáneamente; además el fallback omitía las pestañas y el panel de coste, por lo que la ficha empujaba contenido al cargar. Cambié las rutas Projects/detail a fundido sin traslación, usé un tween ease-in-out de 500 ms para nombre/número y alineé la geometría de skeleton con encabezado, pestañas, coste y tarjetas.
- Chromium headless mostró el número en trayectoria a mitad y en posición destino al terminar; inspeccioné fallback y ficha cargada, y repetí vuelta a Projects con nombre/número visibles. Typecheck y `git diff --check` pasan; ESLint enfocado 0 errores/3 advertencias preexistentes. No tests ni build.

### Follow-up: bidirectional project shared elements

- Owner accepted the flicker correction and requested an animated return to the source row plus a more noticeable movement.
- Preserve immediate project outlet replacement (no retained duplicate table), keep the shared-layout scope stable in both directions, and change the shared tween from 220 ms to 420 ms with an ease-in-out curve.
- Verify repeated A → back → B → browser back → A navigation at desktop/mobile sizes, checking both fields, inherited visibility, settlement, and single-table rendering.

- Outcome: repeated desktop/mobile checks passed with effective visibility preserved, projection and settlement in both directions, and no duplicate table. Typecheck, isolated build, and diff check passed; lint reported 0 errors / 164 existing warnings.

### Follow-up: separate project return timing

- Owner approved entry motion but disliked the return. Added a destination-table transition shared by name/number on desktop/mobile: 320 ms tween, easing [0.16, 1, 0.3, 1], to start immediately and decelerate into the row. Detail/skeleton keep the approved 420 ms entry transition.
- Inspected Motion projection code to confirm destination transition ownership. Typecheck, focused ESLint, and git diff --check passed. No browser regression tests or production build run for this timing-only follow-up; perceived motion still needs owner feedback.

### Extension: all navigable tables and reusable detail handoff

Owner requested the accepted project behavior across remaining tables, with shared animation and cache reuse abstractions. Owner confirmed that missing detail-only information may load; direct links without cache load normally.

Acceptance: bidirectional shared text transitions, source data visible immediately, no mount refetch of complete cached records, missing content/relations loaded honestly, mutations still invalidate, direct links/errors/reduced motion preserved.

1. Share directional transition tokens and the complete-detail query policy. Preserve feature-owned adapters and avoid retaining mutable App Router outlets.
2. Add cache-aware client detail routes for contacts, companies, leads, reusing customer and typed lead lists too. Preserve missing relationships as pending, never fabricate empty data.
3. Extend documents, workspace, notes, and tasks to reuse complete cached details and use list summaries while missing contents load. Add matching shared titles/numbers to sources and destinations, including secondary reports.
4. Inspect every inventory entry and record applicable/non-navigating tables. Check types/lint/build and actual navigation/request evidence; run tests only when explicitly authorized. Keep work local and uncommitted.


### Extension progress — 2026-10-12

Shared query/source-label policy and feature adapters implemented. Repeated desktop/mobile navigation, eight cold links, and recoverable error/retry inspected with local read-only fixtures; see HANDOFF-INSPECTION.md and retained traces. Converted and Stale Leads history state repaired. Final types/lint/build passed; no tests run. Spec and standards findings fixed and approved on re-review. Acceptance coverage remains open for the explicitly listed variants/expiry/duplicate-source scenarios; do not close the entire requirement from this evidence.


### Task dragging performance follow-up —2026-10-12

Fixed repeated heavy card rendering during sortable/drop-highlight updates. Two before/after fixture measurements show77–79% less JavaScript and11–12 versus2 slow frames (>50ms). Pointer and keyboard/cancel inspection passed. Types/lint/build/diff checks passed; no repository tests executed. Both review axes approved. Evidence and limitations retained in HANDOFF-INSPECTION.md.


### Task card opening follow-up —2026-10-12

Stabilized modal geometry, isolated board renders from task URL updates, unified surface timing, and staged expensive editor/control mounting after the opening interval. Desktop warm first frame871→273ms in100-card fixture; pending→loaded height jump removed. Mobile, reduced motion, direct-link/history/filter retention, task switching and quick-close inspected. Types/lint/build/diff passed; no tests run. Review timer finding fixed and runtime-checked. See HANDOFF-INSPECTION.md for evidence and limits.
