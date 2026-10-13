# Table handoff inspection — 2026-10-12

Status: implementation in progress. Full route verification remains open.

## Latest static checks

Current frozen source passed `npm run lint` (164 warnings / 0 errors), `npm run typecheck`, `git diff --check` and an isolated `npm run build`. The copied source was compared before and after the build for the final source-context and task-focus corrections. Logs: `/tmp/maros-frozen-static-tmxppf70/`. Build warnings remain for the middleware convention, Tailwind config module declaration and `jose` compression APIs in Edge. No repository tests run.

## Current acceptance evidence

- Integrated CRM routes at 1440 px and 456 px: Contacts, Companies and Construction Leads each completed A → history back → B → history back → A. All 18 return traces had zero frames missing the source title after the list URL appeared, one table maximum, 20–21 frames with the body copy and zero copies/markers after settlement. Complete detail revisits generated zero fixture API requests; all list returns generated zero API requests. First contact visits loaded `/contacts/:id/details` for missing relations, and first details loaded their uncached child panels. Companies reused both their base and cached contact catalogue without company/detail reads. Leads generated no `/leads/:id` reads. Fixture leads with `found:false` did not show a fabricated QuickBooks zero estimate.
- Logs: `maros-crm-desktop-evidence.log`, `maros-crm-mobile-evidence.log`. These prove the listed CRM routes only. The frame probe captures return projection and settlement; it does not prove each individual secondary-link entry or all fields in all features.

- Shared entry/return timing: 420 ms / 320 ms, with the approved distinct easing curves.
- Direct isolated Chromium inspection of the real `SharedEntityName` component: two entities entered and returned; each animated with one visible body copy, then zero copies/hidden-source markers after settlement.
- Scroll clipping: the source was inside a 40 px `overflow:auto` section. The temporary body text layer followed Motion's projected coordinates outside that section; no ancestor scroll clipping applies to this layer.
- Duplicate entities: selected the second of two instances of the same company. Entry started at its second row (y≈403), return ended at that row. A later generic source correctly replaced the prior selected alias (y≈553).
- Changing `prefers-reduced-motion` during projection removed the temporary copy and source marker.
- Evidence: `maros-shared-overlay-evidence.log`. Source harness and CDP driver are retained alongside this document; they are direct runtime inspection artifacts, not repository test suites. The driver currently bundles the `/tmp` harness location; copy the retained TSX there before reproducing.

## Coherence corrections in this continuation

- Workspace archive/files/folder changes invalidate the workspace list as well as its detail.
- Contact changes invalidate embedded contact/company fields in company, lead, project and customer views. Covered Contacts CRUD, Customers contact controls, standalone contact detail, contact mutations and embedded lead contact edits/associations.
- Company changes also invalidate contacts, leads and projects; Customers company controls use the expanded invalidation set.
- Lead creation/status/type/association/conversion changes invalidate contact views containing leads and aggregate counts.
- Project edits/revert/delete invalidate embedded lead/contact views; warm project detail keeps an enabled observer so invalidations can refresh it.
- Removed server list-loader waits from contacts, companies, customers, typed leads and notes index; existing client hooks own cold reads and cached return rendering.
- Preserved the distinction between missing QuickBooks estimate and zero when mapping a lead row to detail.

## Coverage to inspect in the complete app

Primary sources implemented: Projects desktop/mobile, Contacts, Companies, Customers, Leads active/review/lost/converted, Document Scans, Tasks list/board/mine/calendar, Workspaces, Notes home/favorites/shared/folders/entity lists.

Secondary sources implemented: analytics/receivables project links and numbers, contact lead/project links, project client links, workspace task links, note mentions/backlinks.

Calendar occurrences have distinct task/day layout IDs; source selection and focus restoration use the clicked occurrence. Repeated project clients have distinct project/viewport source IDs; a route-lifetime context preserves selections by entity for both directions, including nested navigation to a different entity.

Do not consider this inventory proof of rendered behavior. Still required: integrated desktop/mobile cycles and request traces for the remaining features (projects after migration, customers, documents, tasks/workspaces, notes, secondary links), cold links and relation failure/retry. Current static checks pass. Prior temporary full-app fixtures/processes disappeared on environment reset and their unfinished inspection is not evidence.

Tables containing inline actions/forms only (users, roles, payments, import results and report-only rows without a detail destination) do not have a route shared-element handoff.

## Environment

- Frontend localhost:3000 restarted after socket inspection proved it absent.
- API localhost:4000 absent. Backend configuration points to remote Supabase; it was not started.
- Do not claim live-data navigation verification from empty lists or permission redirects.
- No repository tests run, commit, push or deployment in this continuation.


## Follow-up: shared return motion and task schedule coherence — 2026-10-12

- Kept the shared-name entrance profile unchanged. Return projection now uses a 400 ms tween with a softer ease; the outgoing route fades over 240 ms with a 4 px upward drift. The project-specific route fade also now lasts 240 ms.
- Task schedule queries now have a stable prefix. A remote `task.changed` event invalidates schedule caches after refreshing the task or confirming its deletion, so returning to a warm calendar cannot preserve stale task dates.
- `npm run typecheck` passed. Focused ESLint for the changed motion, query-key, and SSE files passed. No tests were run. Visual browser calibration of the revised return remains open.
- Full route verification remains incomplete as listed above; these focused changes do not close the broader table handoff requirement.


## Follow-up: converted lead project-number handoff — 2026-10-12

- The source audit found a missing shared identity in Converted Leads: the row already shared its project name, but the displayed lead/project number still used the lead identity while the destination project header uses a project identity. The number now maps to the destination project's desktop/mobile layout IDs and uses the same return transition as the Projects table. Ordinary lead rows keep their lead-number identity.
- Focused ESLint passed with one existing `no-explicit-any` warning in the table column callback; `npm run typecheck` and `git diff --check` passed. No tests were run. Integrated browser evidence for this route and the remaining handoff families is still required.


## Follow-up: secondary table handoffs — 2026-10-12

- Added the contact-name shared element to the navigable contact chip used by Leads and Leads-in-Review tables. A chip configured with a custom modal callback stays outside the route handoff.
- Added responsive project-number handoffs in Project Health Alerts and Receivables. Top Clients now resolves the canonical project number from its already cached project list before animating the project number; rows without that project data keep their plain invoice value and do not create a mismatched pair.
- Together with the previous Converted Leads number correction, these close static source gaps found during the secondary-navigation audit. Five-file focused ESLint passed with one existing `no-explicit-any` warning in the Leads table, frontend typecheck passed, and `git diff --check` passed. No tests were run. Integrated visual and request-trace coverage is still open; localhost:3000 and fixture/API ports were absent during this audit.


## Follow-up: restore Converted source and repeated project navigation — 2026-10-12

- Converted Leads kept its selected view only in component state, so history back restored Pipeline and removed the project-name/number source pair. Reused the existing URL-tab hook with `?view=converted`; the default Pipeline view keeps a clean URL and switching views uses native history replacement without a server navigation.
- With separate active/converted fixtures, A → back → B → back → A passed at 1440 px and 456 px. Every return kept Converted selected, projected both the project name and number, kept one table, and left zero overlay copies after settlement. All six list returns and both complete A revisits generated zero fixture API reads. First visits loaded missing project catalog/financials and cost reports deliberately.
- Projects at 1440 px also completed A/back/B/back/A with name and number projection (25–26 sampled frames), one table, zero copies after settlement, zero return reads, and zero complete A-revisit reads.
- Current source typecheck, focused ESLint for the URL-state correction, and diff check passed. No repository tests run. Full remaining-route audit stays open.
- Read-only fixture returns HTTP 405 for writes and has no connection to the real backend/database. QA frontend is on localhost:3101. Secondary-route inspection confirms both name and number returning from Project Health and Receivables; Top Clients shares the canonical number. See retained mobile trace. The older desktop secondary trace used a short observation window that assigned late detail-panel reads to the return; do not use it for zero-return-read claims.


## Follow-up: cross-feature runtime coverage and source labels — 2026-10-12

- Added presentation-only source labels to the shared-source context. Contacts, leads and projects keep known names/numbers in their pending header while genuinely missing details load; labels never mark a record complete. Stale Leads retains its chosen days through history using the existing URL-state hook. Analytics queries now honor explicit invalidation on mount while retaining warm unchanged data.
- Completed 54 fixture round trips across workspaces, notes home/favorites/shared, invoice scans, and task list/board/mine/calendar at desktop/mobile widths. Complete note/task revisits did not reload domain records. Invoice/workspace revisits retained necessary authentication/SSE traffic but did not reload their complete domain records. Task dialogs opened/closed correctly; this evidence does not establish their exact visual trajectory.
- Customers and secondary workspace-task/contact-project/project-client links also navigated successfully. Eight cold detail links (contact/company/lead/project/task/note/workspace/invoice) loaded the missing data. Retained traces distinguish expected relation/catalog reads from record reuse.
- Delayed-source desktop inspection kept project name/number, contact name, and lead name/number visible while detail reads were pending. Returns issued no fixture API reads and left no overlay copies; Stale Leads returned to its selected 30-day threshold. Contact relation 503 recovered through Retry; project-list 503 displayed an error rather than an empty-success table and recovered through Try again.
- Review found keyboard activation bypassing source capture and terminal contact errors retaining an editable cached preview. Fixed both: capture Enter/Space on the focused navigation trigger, excluding children; discard contact detail/preview on normalized 401/403/404. Both spec and standards reviewers approved these focused corrections after re-review.
- Final source: typecheck exit 0; full lint exit 0 with 164 existing warnings and zero errors; isolated production build exit 0; diff check passed. No repository tests, commits, pushes, production writes or deployments. QA uses a local GET-only fixture, not the real API/database.
- Remaining limits: populated review/lost variants, note folder/mention/backlink navigation, expiring invoice file URLs, and exact duplicate-client source selection have not all received integrated browser coverage. The broader REQ-004 remains open. Missing contact/lead mutation invalidations of analytics were confirmed to predate this continuation; the new mount policy respects existing invalidation but does not resolve that separate coherence gap.


### Final targeted inspection

- Mobile (456 px) delayed project/contact/lead entry retained known source labels after the transition settled, then fetched the missing data. All three returns had zero fixture reads and zero settled copies/active overlay markers; the selected 30-day stale report remained selected.
- Mobile contact relation 503 and project-list 503 both recovered through their retry controls. The project failure never appeared as a successful empty table.
- A keyboard Enter navigation from the contact table with an intercepted HTTP 404 displayed the entity error and removed the editable contact information. The terminal-error path is confirmed at runtime, in addition to both static review approvals.
- Converted row activation with Space also reached the matching project with its name and number visible. Both final browser inspection drivers exited 0.


## Contact badge visibility regression — 2026-10-12

- Owner reported contact badges in Leads containing an icon but no visible name. Reproduced with two converted leads sharing one contact: the first shared text had computed visibility:hidden on initial rendering and after returning from the contact. It was a Motion layout identity collision, not missing contact data or a lingering overlay marker.
- ContactInfoDisplay now requires a sourceInstance supplied by both consumers: lead-id and review-lead-id. Each badge gets a distinct projection identity while the existing context connects the selected origin with the contact detail header. No global visibility override or animation removal.
- Desktop fixture inspection after the fix found both names visible on initial rendering and after contact navigation/back. Typecheck passed; full lint passed with zero errors and 164 existing warnings; diff check passed. Spec and standards reviewers approved the three-file correction. No repository tests executed; no commits/deployments.
- Normal web3000 and API4000 remain running. QA inspection is isolated on3101 with the GET-only fixture4101; no real CRM write was used to reproduce this defect. Shared names in a repeated list must carry a stable row-specific sourceInstance, not only the entity ID.
- Narrow viewport (456 px): initial badges and both successive contact/back round trips kept every name visibility:visible, opacity:1 and no active overlay marker. Inspection exited0. Stopped the temporary QA frontend after inspection; normal web/API remain active.
- Isolated production build of the corrected current source exited0 (known middleware/Tailwind/jose warnings).


## Task drag performance regression — 2026-10-12

- Owner reported card dragging felt like 10 FPS. Profiled the actual TaskBoard in an isolated development frontend with a GET-only fixture of 100 cards, 1440px viewport, headless Chromium, identical 120 pointer moves and cancellation; no real CRM task was moved.
- Cause: sortable context updates repeatedly rebuilt TaskCard content (Motion + menus/pickers). Column drop-highlight updates also rebuilt row action callbacks, defeating card memoization. The final correction uses standard React memo on TaskCard, stable dragHandle props, and a memoized TaskCardList shared by status/assignee columns. EntityTaskBoard keeps its open callback stable too. No custom comparator, ignored handler or changed persistence/drop logic.
- Two baseline runs: ScriptDuration 7875/7965ms; layout109/111ms; 12/11 frames over50ms; overall pointer sequence8088/7825ms. Two corrected runs: ScriptDuration1689/1822ms (77–79% reduction); layout3.1/3.5ms; 2/2 frames over50ms; sequence4094/4000ms. Framep95 baseline66.7/33.4ms vs corrected16.8/33.3ms. Dev/headless measurements establish the local improvement; they do not assert the owner's browser runs at a fixed FPS. Keep this memoization while card controls remain expensive under sortable updates; reevaluate against the same fixture if the card/context design changes.
- Direct browser inspection confirmed pointer drag activation, moving overlay, Escape cancellation, keyboard Space activation/ArrowDown navigation/Escape cancellation, and all100 source cards retained. Writes are blocked by the fixture. Actual status persistence/drop mutations were not exercised against the remote database.
- Final typecheck exit0, full lint exit0 (zero errors,164 existing warnings), isolated production build exit0, diff check passed. Spec and standards reviewers approved the scoped memoization and checked callback dependencies/selection updates. No repository tests run, commits or deployment.
- Changes are live in normal localhost3000 development source; API4000 remains running with the owner's authorized remote connection. Stopped the temporary QA frontend3101 and performance fixture4102 after inspection; the older read-only base fixture4101 remains separate.


## Task card opening follow-up — 2026-10-12

- Owner confirmed both animation jumps/deformation and delayed detail appearance. Inspected TaskBoard, URL state, shared-source capture, modal surface, pending/full details and editor mount path before editing.
- Isolated before profile:100cards,1440px,GET-only fixture with700ms cold detail delay. First dialog frame cold1232ms/warm871ms; cold dialog height476→900px and y262→50px. These are dev/headless observations, not a claimed production FPS/latency budget.
- Board view state now excludes only `task` from its memo identity. Stable URL callbacks read the current query on activation. A thin URL adapter passes stable view state into the memoized board, preserving filter/data subscriptions while avoiding rebuilding its card controls when the detail parameter changes.
- Dialog height stays90dvh desktop/full viewport mobile while missing details arrive. Card and detail surface share a320ms tween; removed the stagger/double shared-content fade. Known summary paints before editors/pickers mount after the surface interval; pending data still fetches, complete cached details still do not refetch. Cached staging says Opening task rather than claiming a network load. Full-page/reduced-motion modes bypass staged waiting.
- Desktop final staged inspection: first frame cold775ms/warm273ms; height900→900px, y50→50px. Mobile456px: first frame cold795ms/warm216ms; height1000→1000px/y0 throughout. Both mobile and reduced-motion warm opens issued zero API reads; cold opens fetched the deliberately missing detail/dependencies/note references. Reduced-motion omits the shared surface and staged wait (raw generic aria-hidden surface selector also matches SVGs; do not interpret its bounds as a projection surface).
- Direct-link close retained q=Drag; internal quick close mounted no editors during exit; switch2000→2001 showed the correct title; history back preserved the filter and removed the modal. All drivers exited0. No task mutation executed; fixtures reject writes.
- Both review axes inspected the changes. Spec review found the preparation timer could outlive the start of normal closing; fixed by cancelling its ref synchronously in handleClose and guarding the effect with isClosing. The quick-close runtime inspection confirms editors do not mount on exit. No remaining concrete review finding.
- Final typecheck/lint/isolated production build exited0; lint164 existing warnings/zero errors; diff check passed. No repository tests, commit, push or deployment. Browser calibration against the owner's actual task dataset remains the practical limit of fixture evidence.
- Normal source changes are live on web3000; owner-authorized remote-backed API4000 remains running. Stopped temporary QA3101/performance fixture4102 after inspection; no environment files changed.
