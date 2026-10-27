---
name: Bambalinas
status: draft
kind: independent-direction-exploration
contract_ref: proyectos@v1
revision: r10.dir-b
subplan: SP-4
requirements: [R6, R7]
owner: David
approval: pending-owner-selection
chosen_thumbnail: proyectos@v1.r10.dir-b.html.candidate-2.html
---

# Bambalinas — direction B

## 1. Identity and traceability

Independent kinetic/spatial exploration, awaiting owner selection. This is not the canonical contract, an approval, or an implementation input. Sources: `SPEC.md` `65b1e5ecc06f20d9`; `PLAN.md` `cc7e53f2abf3c23c`; `PLAN.json` `7a2c833a7e711508`; `design/proyectos@v1.r10.behavior.md` `378c0aa4a41164c6`. Sources may continue changing during collaborative planning; the hashes identify the snapshot read here.

SP-4 covers R6 account-owned server projects and R7 explicit lossless browser-scene import. T4.1 eventually copies the approved canonical contract; T4.4 consumes the project list/save/read-only UI and T4.5 consumes import. T4.6/T4.7 verify the real service/browser integration; T4.8 reviews the rendered implementation and T4.9 independently audits it. Storage/API checkpoint T4.31 remains outside this design. No canonical artifact, plan, repository or history was modified.

## 2. Concept and memorable move

**Bambalinas** turns the event decorator’s mounting rig into a saved-work interface. A scene hangs from two cables below a shared beam. The named projects form a stepped run of counterweights. Selecting a name lowers its scene into place; opening it remains a separate, clearly named operation. This answers “Which installation do I want to continue?” without requiring spatial gestures.

**Memorable move:** the pulley turns, the scene descends with a slight perspective correction, and its named counterweights rise into registration. The latex cluster breathes against the rigid mounting structure while a foil star turns on its tether. Actual text remains opaque throughout motion. Working controls stay quick and familiar.

## 3. Two fresh thumbnails and the look ledger

Both visual thumbnails were drawn before the full TSX. Each contains its own inline CSS, embedded local display font, a theme selector and phone reflow. They are small visual studies, not HTML fallbacks for real components.

- Candidate 1, `proyectos@v1.r10.dir-b.html.candidate-1.html`: an angled round turning platform beside a flat project directory. Its strong circular silhouette suggests rotation, but it leaves the directory unrelated to the object and overlaps older front-elevation/ribbon ideas.
- **Chosen: candidate 2**, `proyectos@v1.r10.dir-b.html.candidate-2.html`: a full beam with suspended scene and staggered named counterweights. The scene and directory share a concrete structural relationship. It expands naturally into the workshop’s save slip and stacks into a readable phone sequence.

Read sibling look-ledger notes: cuentas-admin r10 A production register, B inflatable threshold and C latex bands; taller-esenciales r9 A/B/C including its spatial assembly and molded silhouette. This direction avoids their call sheet, gate/form composition, left identity rail, orbital table navigation and molded toolbelt. The Pictures name/ring-dot silhouette, direct product language, Sempertex balloon materials, semantic token names and explicit safe actions provide continuity. No previous project HTML or TSX was copied or patched.

## 4. Why this is not a default, and the eight axes

The hierarchy is built from a mounting beam and its counterweights, rather than independent dashboard cards. Upright condensed serif display, vermilion hardware, silver-sage foil, unilateral rounded ends and reciprocal vertical motion belong to the same physical idea. It introduces neither KPI filler nor invented product capabilities. The scene is explicitly an illustration; the static mockup does not claim to render a saved 3D document.

| Axis | Present expression |
|---|---|
| Concept | Bambalinas: a decorator’s fly system. A complete balloon installation hangs from a gantry; project names are counterweights that bring one scene into working position. |
| Layout | A broad working title and collection search precede a full-width gantry. A 57% suspended scene and 43% stepped counterweight directory share one beam; phone stacks scene, detail, project names and import recovery. Workshop replaces the directory with a narrow scene/save slip. |
| Navigation | Named project counterweights are actual buttons in a navigation landmark, with aria-pressed selection and a separate explicit Open action. Authorized staff use collection/owner selectors. The top return link and a scoped import strip provide exits without a sidebar, orbit, carousel or thumbnail ribbon. |
| Typography | Embedded DejaVu Serif Condensed Bold upright as Marquee, 48–88px display and 27–34px scene headings; embedded Liberation Sans regular/bold for working text, Liberation Mono for loading counts, revision tags and stage captions. The title stretches vertically into registration. |
| Density | 40px outer desktop margin, 40px stage gap, 22px counterweight padding, 44px minimum actions, 46px fields; 20px phone margins and a single column below 768px. Rectilinear scene plates contrast with one rounded counterweight end. |
| Components | Real installed shadcn/Base UI Button, Input, Skeleton and Animate UI Checkbox, Dialog, AlertDialog; Motion profile springs seat a custom SVG latex/foil scene. Custom gantry, cables, stepped counterweight buttons and save thread are product-world composition, not snippets presented as installed library components. |
| Colour | Proposal mapped onto Pictures semantic roles: cool stage grey #e8eceb, opaque white-green #f8faf8, ink #232c28, vermilion action #b62913 and silver-sage foil. Dark stage #14211b/#20342a, text #f0f7f0, peach foil-reflection action #ffb3a0. Material gradients exist only inside the balloon illustration; no text is on a gradient. |
| Motion | Fly-system spring grammar: beam pulley turn, suspended perspective descent, staggered upward counterweights, vertical display tension, tethered latex breathing, foil torsion, short hover lever/press compression, notice seating, save-thread tension and success stamp. Expressive 760ms stage/65ms stagger/180ms controls; natural 460/40/160; subtle 240/20/120. Finite travels retain full-opacity text. Reduced motion, still=1 and Quieto remove travel/ambient loops, and hidden/offscreen content pauses. |

## 5. Tokens, real components and source boundary

Read both repositories’ `src/app/globals.css` and the existing `guardado-escena.ts` boundary. Existing Pictures roles `--fondo`, `--superficie`, `--superficie-2`, `--texto`, `--texto-suave`, `--acento`, `--acento-hover`, `--sobre-acento` and `--borde` map to the kit’s background/card/muted/foreground/primary/input roles. The owner explicitly requested fresh colour worlds, so the values above are a **proposal**, not a brand-token replacement approved for production. Error/success/warning text remains semantic and named in both themes. Native selectors and unchecked checkboxes have measured control edges.

Components: `shadcn:button` default/outline/disabled (`@/components/ui/button`), `shadcn:input` default/invalid/disabled (`@/components/ui/input`), `shadcn:skeleton` loading (`@/components/ui/skeleton`), Animate UI-enhanced `shadcn:checkbox` unchecked/checked/disabled (`@/components/ui/checkbox`), `shadcn:dialog` name/import (`@/components/ui/dialog`) and `shadcn:alert-dialog` leave/load confirmation (`@/components/ui/alert-dialog`). Exports were inspected before use. Custom scene/beam/counterweights use SVG/CSS and Motion; they are not claimed to be library components. `mountMockup`/`useMockup` and `useMotionProfile` come from the real installed runtime. No packages or assets were fetched; no fallback HTML snippets were needed for the full output.

Fonts are embedded from local DejaVu Serif Condensed Bold, Liberation Sans regular/bold and Liberation Mono regular. There are no external fonts, images or runtime HTTP requests. To make the static token checker inspect exactly the rendered direction colours, the built HTML also mirrors the entry’s stylesheet in `style[data-direction-source=bambalinas]`; it is generated from the same `css` literal, not separately designed CSS.

## 6. Navigation, views and responsive hierarchy

The native planning selectors retain `view`, `state`, `scene`, `theme` and `motion`, labelled Vista, Estado, Diálogo, Tema and Movimiento. The visible **Mockup** label is retained. Product Spanish/English selection demonstrates longer labels; some explanatory copy remains Spanish because SP-4 plans centralized Spanish strings before the later localization subplans. This exploration is not evidence of complete English localization.

Views:
1. `mine`: current account collection, global-by-name search, selected scene illustration, explicit Open in Taller, loaded count, next-page action and reversible import entry.
2. `staff`: authorized all-account collection, collection and owner selectors, project owner identity, selected project and read-only foreign original. Mine remains scoped to the active illustrative account.
3. `workshop`: project name/owner/revision, visible save thread, first named save or Save now, Save copy, complete-scene scope and a labelled demonstration edit. Foreign originals hide editing actions and allow owned copy only for a Taller-capable account.
4. `reading`: a separate read-only route for a role with `proyectos.ver_todos` but no `taller.usar`. No copy action or edit tools are exposed. The role limitation is explained.

Breakpoints: **360–767px** single column, 20px outer inset, selected scene then its details then project directory; steps flatten to full width. **768–1099px** two columns with 24px outer inset and gap; scene action moves below its details. **1100px+** 40px outer inset, 40px stage gap and a 57/43 split. Workshop has a 290px save slip, narrowed to 250px on tablet and stacked below the scene on phone. Dialogs use at most viewport minus 40px, generous 26–30px padding, wrapping actions and vertical overflow. Footer shares the page’s left edge. Names wrap; no horizontal page scrolling is required.

## 7. Preserved behavioral requirements

- First save explicitly requests a name; later changes queue autosave and expose Save now. Dirty, saving and confirmed saved are different. Only the submitted edit generation may be acknowledged; later edits remain dirty. Production must serialize and bind requests to account/project identity.
- Names and the **complete** scene travel across browsers, including room, environment, materials and node relationships. AI conversation/generated images remain browser-local; the interface makes that scope visible. Opening a different project resets undo/conversation identity rather than attaching another project’s history.
- List search and authorized owner filtering cover the entire server collection **before pagination**. The production implementation must debounce/key requests, reset cursor/results on filter changes, ignore obsolete responses and preserve loaded rows after next-page errors. The prototype filters its small illustrative in-memory collection only and makes no claim to verify server pagination or authorization. Loaded counts are shown without invented totals.
- A conflict stops autosave, preserves unsent local work and offers **owned copy** or **load saved version**. Loading requires a separate AlertDialog, explains replacement and retained recovery draft, and exposes an illustrative draft download. No merge or silent overwrite is introduced.
- Foreign originals never gain editing rights. Reading does not transfer ownership. Only a Taller-capable staff account may create a copy under its own account. No deletion, transfer or version-history UI is added.
- Offline/network/auth/permission failures keep same-account recovery work and offer recovery without claiming a save. Leaving with pending work offers Save and leave, Keep local draft and leave, or Stay. Unavailable save paths are disabled. Account change/session loss hides prior scene/results and never enumerates another account’s drafts.
- Import is offered on the first authenticated Taller visit with raw legacy data and can be reopened from projects after “Not now”. It names the destination account, warns about shared-device origin and requires explicit checkbox consent. No upload before consent. Original raw bytes remain unchanged after acceptance, refusal or failure. Unsupported data shows explanation and a raw-original download. Retry/double-submit uses account plus raw-source hash to recover one project; no automatic association is made for a new account. Accounts without Taller access keep the data until permission is granted.

All mock data and JSON downloads are labelled demonstration content. Persistence, raw-byte retention, revision checks, same-origin protection, draft isolation, database races, authentication and retry idempotency require the real T4.2–T4.7 implementation/tests. The mockup does not access localStorage or user data.

## 8. Reachable states and dialogs

All 23 states are exposed by the native Estado selector: normal, loading, empty, no-results, error, unnamed, dirty, saving, saved, offline, save-error, conflict, foreign, denied, expired, account-switch, page-loading, page-error, partial, validation, import-invalid, import-success and disabled.

Loading uses a scene skeleton and three name skeletons. Empty invites the first project; zero matches offers clearing search. Initial error replaces the collection with retry, while next-page error retains loaded rows. Pending/saving/saved are named; offline/save errors expose retry; conflict disables ordinary saving. Expired/account-switch clears visible identity context; denied reveals no project metadata. Import-incompatible exposes the raw-original demonstration download; success keeps the original and offers the imported project. Validation is visible in the name dialog; disabled is demonstrated in the workshop’s save/edit controls.

Five dialogs are separately selectable through Diálogo: `save`, `copy`, `import`, `replace`, `leave`; the empty option closes all. Base UI modal behavior supplies focus containment and inert background. Escape closes ordinary dialogs; explicit cancel remains available. Focus returns to the opener. Replacement and leave use AlertDialog. Busy operations temporarily disable duplicate actions, with a named saving status.

## 9. Motion and accessibility targets

WCAG 2.2 AA is the target; automated results are bounded evidence, not a conformance certificate. Text contrast targets 4.5:1, control edges/focus 3:1. Actions have 44px minimum height; labels are associated, selection uses `aria-pressed`, errors use alerts and save feedback uses live status. Arrow keys can operate native selectors; every spatial operation is a button. No drag-only interaction is required. Motion retains opaque text on opaque planes; gradients are decorative balloon materials only.

At least twelve separate CSS behaviors are authored: suspended scene descent, counterweight seating, title tension, pulley rotation, latex breathing, foil torsion, notice seating, save stamp, save-thread tightening, active save thread, empty sway and skeleton breath. Hover lever/arrow rotation and press compression add quick feedback. Motion uses the runtime profile’s actual spring for scene replacement, and profile-specific CSS timings for choreography. `prefers-reduced-motion`, `?still=1` and Quieto remove animation/transition while preserving every view/action; tab-hidden/offscreen page pauses effects.

## 10. Observable acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1100px+ | normal | Selected scene and stepped named-project directory hang below one full-width beam. |
| B-AC-02 | 360–767px | normal | Scene, details, directory and import recovery form one column within 20px page margins. |
| B-AC-03 | all | normal | Search, each project name and explicit Open are keyboard reachable, with a 3px visible focus indicator. |
| B-AC-04 | all | unnamed | Editing the demonstration scene does not bypass the first explicit named save. |
| B-AC-05 | all | saving/saved | Saving is visibly distinct from confirmed saved; the saving action is temporarily disabled. |
| B-AC-06 | all | conflict | Save now is disabled; owned copy and load saved version are visible; loading opens a confirmation. |
| B-AC-07 | all | page-error | Loaded projects remain visible with a retry-next-page action. |
| B-AC-08 | all | reading | No save/copy/edit action is exposed to the no-Taller reader. |
| B-AC-09 | all | import | Named destination and shared-device warning precede an unchecked consent checkbox; Import starts disabled. |
| B-AC-10 | all | import-invalid | A recovery explanation and original-download action appear without replacing the source scene. |
| B-AC-11 | all | expired/denied | Previous scene/collection content is not exposed. |
| B-AC-12 | 1280/390px, both themes | reduced/Quieto | All content stays usable with no running animation. |
| B-AC-13 | all | normal | Planning chrome retains Mockup and all native axes; no HTTP(S) asset request is made. |

## 11. Verification and honest limits

Final kit run on the delivered HTML: `audit: proyectos@v1.r10.dir-b.html — 448 renders (448 combinations planned), 11304 text measurements, 1406 focus stops`.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

`contrast: 158 pairs checked in light and dark, all pass`.

Focused browser checks passed on the final build: project selection/opening with matching name; explicit first save and name validation; empty-state creation; import consent accessible name, unchecked/checked gating, Escape and focus return; conflict save stop and replacement confirmation; owner filter and foreign read-only/copy distinction; no-Taller reader restrictions; no overflow at 360/390/768/1024/1280 in both themes; OS reduced-motion, Quieto and `still=1`; offscreen pause; no page errors or HTTP(S) requests. Six simultaneous expressive CSS behaviors were observed (`title-tension`, `pulley-turn`, `fly-in`, `latex-breathe`, `foil-turn`, `counterweight`). Additional state effects are defined and reached by the selectors. The checked import dialog also passed the rendered contrast/non-text/alignment/padding/overflow probes at 390px in both themes.

The focused checks initially caught an overly early dialog-exit assertion (the library retains exit DOM briefly) and a real residual Motion spring when changing to Quieto. The test now waits for actual dialog removal; the reduced scene is remounted in its final pose without resetting parent selection, ending the residual spring immediately. The visible consent control is explicitly named. The empty-state action was also checked to create an unnamed project.

The first full audit rendered 448 combinations and found one padding issue in the explanatory read-only tag (10px lateral inset versus 12px required). That tag was changed to 12px. Screenshots were visually inspected at 1280 and 390 in both themes, plus desktop conflict and phone import dialog in dark theme; screenshots were streamed in memory and no unassigned evidence files were written. Tablet/360px reflow and interaction coverage passed in the focused checks above. Full server behavior, security, lossless import, browser-to-browser persistence and complete English localization remain unverified by this design mockup.

`compare_directions.py` ran offline against r10 A/B/C with exit 0, `ok: true`, `evidence_ok: true`, no missing evidence. B versus A layout similarity: 0.007; B versus C: 0.050. Typography, navigation and motion are distinct in both comparisons. These measurements supplement visual judgment and do not select a direction for the owner.

## 12. Open questions, assumptions and impact

Q: Owner — Should the collection show an authorized client-rendered scene preview on selection, or reserve the actual 3D preview for opening a project? This exploration uses an explicitly labelled illustration and assumes no new stored-thumbnail API.
Q: Owner — May this direction’s vermilion/steel palette and upright serif display replace the current purple working palette if selected, or should finalization keep part of the existing brand tokens?

Confirmed behavior from round 9 and the shared behavioral source is preserved, not reopened. New composition, hierarchy and navigation would require adaptation in T4.4/T4.5 and rendered review by T4.8; compatibility with any eventual implementation is **undetermined** until owner selection and canonical finalization. No existing consumer is retargeted. The owner’s choice and final canonical contract remain outstanding approval steps, not incomplete work in this exploration.

Delivered HTML SHA-256: `1c627ccb63ff24eb73f9ee6c85a559c9c0c01f57632aae7eeafb017b08587234`.
