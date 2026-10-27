---
id: proyectos
version: 1
status: draft
artifact: independent-exploration
revision: r10
direction: c
name: Estuche
date: 2026-10-27
---

# Estuche — direction C

## 1. Identity and traceability

Planning exploration for SP-4, Saved projects, covering R6 and R7. This is an unapproved direction for the future `proyectos@v1`, not the canonical contract or an implementation authorization. The owner and Planner are still discussing the plan. Only the six assigned revision-specific artifacts and the required delegation result are written.

Sources read: current SPEC.md, PLAN.md, PLAN.json and `proyectos@v1.r10.behavior.md` (SP-4 digest `749be52ec4afc053`). Inspected source SHA-256 prefixes: SPEC `65b1e5ecc06f20d9`; PLAN.md `cc7e53f2abf3c23c`; PLAN.json `7a2c833a7e711508`; shared behaviour `378c0aa4a41164c6`. Both workspace repositories, t12 and asesor, were read for their AGENTS.md, globals.css and the existing browser scene saver. Neither repository was edited.

## 2. Purpose, concept and memorable move

The question is: **which saved montage do I want to pick up again?** Users with Taller access save and continue their own complete scenes. Staff with `proyectos.ver_todos` consult authorized projects; a copy additionally requires `taller.usar`. Nobody edits another person's original.

Estuche treats the collection as a decorator's padded travel case. Projects sit in stitched, soft-cornered pockets. Pool-blue material supports an ink-blue inflated-letter title; bright cyan is the zipper hardware, with a deeper accessible cyan for light-theme actions. Pink latex and silver foil appear inside the schematic montage, connecting the case to Sempertex's working world.

The final rounded display pairing shares a soft-material identity with accounts C while deliberately changing its palette, composition, navigation and zipper-led motion.

**Memorable move:** the zipper registers across the page, its pull seats into place, and three project pockets arrive with a compressed/expanded material response at 70ms intervals. The pull can be dragged with a spring or moved using Left/Right/Home. It is a decorative material sample and never saves, selects or deletes a project. Every essential action has an explicit text button.

## 3. Two thumbnails, look ledger and hierarchy

Both thumbnail HTMLs were written and rendered before the complete TSX entry:

- **Candidate 1, chosen:** `proyectos@v1.r10.dir-c.html.candidate-1.html`, an open travel case with three stepped project pockets. It exposes several named projects and their continuation actions at once.
- **Candidate 2, rejected:** `proyectos@v1.r10.dir-c.html.candidate-2.html`, a narrow project index facing one large preview. It gives too much space to a single montage and repeats a familiar index/working-plane composition from the ledger.

Read the sibling accounts r10 A/B/C and Taller r9 A/B/C notes. This exploration avoids the accounts permission register, inflatable entrance, Nudos' left identity rail and account bands, Taller's lower toolbelt and molded object cavities, and its technical drawing or suspended scene compositions. Pictures/Sempertex naming, linked-circle mark, project vocabulary, semantic token roles, ES/EN operation and explicit ownership protections remain shared. The new palette and type pairing are proposals local to this exploration. The initial thumbnail sketches used provisional orange hardware and a system serif; a final underlying-font and palette ledger check found sibling A/B also using serif/orange families, so the full direction deliberately resolves to rounded Mplus, pool blue, cyan and pink. The thumbnails remain the original composition evidence.

The collection hierarchy is title/action, material zipper, search and authorized scope, loaded count, named project pockets, next-page recovery, browser-scene retrieval and footnote. The editor hierarchy is project name, relevant recovery/import notices, saving status, broad schematic and an unboxed ownership/persistence note. There are no invented KPI tiles, status charts or generic dashboard summaries.

## 4. Eight axes and visual system

| Axis | Observable design | Evidence |
|---|---|---|
| Concept | A decorator's travel case protects each named montage in a stitched pocket. | `.pocket`, `.zip-track`, `.zip-pull` |
| Layout | Three stepped pockets at desktop, the first slightly wider; editor splits into a broad scene and narrow unboxed note. | `.pocket-wall`, `.project-plane` |
| Navigation | Direct per-project continuation, Back to projects and browser-scene retrieval; staff reveal in-flow Mine/Everyone controls and an owner filter. No persistent sidebar or fixed bottom dock. | `.pocket .actions`, `.more`, `.scope-nav` |
| Typography | Embedded Rounded Mplus 1c ExtraBold, 44–78px title and 25px project names, paired with embedded FreeSans for 14–16px working copy. | `.display`, `.pocket h2` |
| Density/shape | 44px desktop gutters, 27px pocket padding, 60px upper lobes and 27px base corners; an inset dashed seam defines the material. Phone has 20px gutters and one pocket per row. | `.estuche`, `.pocket:before` |
| Components | Real shadcn controls, Animate UI dialogs, custom stitched pocket, inline SVG schematics and a Motion zipper slider. | `[data-slot=button]`, `[data-slot=input]`, `.dialog-box`, `.scene-art` |
| Colour | Pool blue and ink blue, bright cyan hardware, deep cyan actions, pink latex and silver-blue foil. Dark uses solid water-blue surfaces and bright cyan actions. | `.estuche`, `.zip-pull`, `.scene-art` |
| Motion | Compression, elastic seating and staggered pockets; zipper travel, balloon inflation, foil rocking, stamped feedback, pressure release and tactile press responses. | `.pocket`, `.display`, `.zip-track`, `.zip-pull`, `.balloon-group`, `.foil-shine` |

**Why this is not the default:** the collection has a deliberately stepped material rhythm and stitched physical edges, rather than equal dashboard cards. The inflated rounded lettering and pool-blue tool-case ground belong with the zipper, foil and latex. It does not inherit Pictures purple, cream/terracotta, a purple gradient or acid green on black. Cyan is physical hardware and a deliberate action role, not an accent applied to every surface.

| Existing Pictures token | Kit role | Light / dark proposal |
|---|---|---|
| `--fondo` | background | `#c9e7f3` / `#102d40` |
| `--superficie` | card, popover | `#f3fbff` / `#183e55` |
| `--texto` | foregrounds | `#103247` / `#f3fbff` |
| `--texto-suave` | muted foreground | `#33586b` / `#b4d6e9` |
| `--acento`, `--sobre-acento` | primary pair | `#07577a`, white / `#82d9ff`, `#05283d` |
| `--borde` | border | `#51869f` / `#77abc5` |
| Proposed stronger control edge | input | `#36687f` / `#8abbd2` |
| Focus | ring | `#07577a` / `#82d9ff` |
| Existing semantic responsibilities | success / warning / destructive | `#175840` / `#704209` / `#a51c36`; dark `#9cddbd` / `#f5d194` / `#ffafc0` |

These values explicitly remap the project's existing responsibilities; they are not claims about the current production palette. The optional sample-role and language controls are mockup tooling inside the page, not a proposed product account-switch mechanism.

Actual component inventory: `shadcn:button default/outline/ghost/disabled` from `@/components/ui/button`; `shadcn:input default/invalid/disabled` from `@/components/ui/input`; `shadcn:skeleton loading` from `@/components/ui/skeleton`. The Button adapter preserves the real component and adds `data-variant` for restyling. Modal naming uses `@animate-ui/react/primitives/base-ui/dialog`; potentially disruptive leave/load decisions use its `alert-dialog` counterpart. Their real Root, Portal, Backdrop, Popup, Title and Description supply modal semantics, inert background and focus containment. `motion/react`, `@kit/motion` and `@kit/mockup` supply the spring, profiles, mountMockup and useMockup. Custom assets are inline SVG/CSS; no snippet fallback was needed.

Rounded Mplus 1c ExtraBold is subset from its installed local TTF in memory and embedded as a data URI. The actual underlying font families were checked against sibling A/B; C does not reuse their DejaVu Serif Condensed display. Existing FreeSans was subset in memory and embedded as an OpenType data URI because this builder has no `.otf` file loader; no font file or package was created or fetched. An attempted in-memory WOFF2 encoding was unavailable without Brotli; the installed font's OpenType encoding works offline. The exact authored CSS is also inserted in a head style block after building so the static contrast checker reads the same proposed tokens as the runtime.

## 5. Navigation and interaction model

The product uses direct labelled actions rather than requiring the zipper or gestures. Each pocket opens its own project. Own editable scenes correspond to `/3d?proyecto=<uuid>`; staff consultation corresponds to the authorized read-only `/proyectos/[id]` view. A role without Taller cannot enter its editor or create a copy. Back to projects corresponds to `/proyectos`.

The native planning bar retains **Mockup**, Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` and Movimiento `motion`. ES/EN is `language`; sample roles are `actor`. Both are native selects with accessible names. The initial motion profile is expressive. Staff may select Everyone and then filter by owner; plain users have only their own collection. Filters reset pagination. The illustrative collection filters its complete fixture before slicing pages; it does not demonstrate a production server query.

Modal Escape/cancel closes and returns focus to the originating control. Naming errors retain entered text. Navigation with pending work offers Save before leaving, Keep draft and leave, or Stay here. Choosing Save completes the save on the current scene; the user can then leave. There is no discard-by-default or overwrite action.

## 6. Behavioural flows retained

1. **First save:** New project → unnamed Taller → Save project → name dialog → nonempty name → explicit save → revision 1 and saved confirmation. Later edits show pending → saving → saved; Save now remains available when online and conflict-free.
2. **Continue:** search by project name across the authorized collection → load more if needed → Continue project. The full name and complete scene are the server-persisted scope. AI conversation and generated images stay local; the scene's conversation identity must not be silently attached to another project.
3. **Conflict:** a stale-write response pauses autosave and retains local work. The comparison shows the local base revision and newer saved revision. Save my work as a copy opens naming and creates an owned project. Load saved version requires an AlertDialog explaining replacement of the visible scene and preservation of a local draft. No automatic retry/overwrite follows a conflict.
4. **Staff read/copy:** authorized Everyone/owner filter → View project → read-only original → Create a copy in my account only with Taller access. The original remains unchanged. A view-only custom role sees the explanation and a disabled copy action.
5. **Legacy import:** the authenticated Taller sample offers an earlier browser montage for review before any upload. Review → dedicated import view names Ana's destination account and warns about shared devices → explicit Import to my account. Not now is reversible from the collection. Success preserves the original and identifies one project; interrupted-response retry must return that same project. Unsupported data offers the original download instead of replacing it with an empty scene.
6. **Recovery:** offline/pending drafts remain account/project scoped in the implemented product. The mockup demonstrates a local-draft recovery notice after Keep draft and leave. Authentication loss closes the private view; only returning to the same account may restore its draft. Account switching must clear scene/query caches and ignore prior-account responses.

The last flow's production namespace, revision arbitration, stale-response rejection, serialized 500ms debounce, legacy raw-byte receipt and import idempotency remain precisely the shared behavioural source's requirements. This visual exploration does not replace them with a simulated client implementation.

## 7. View specifications

| Native view | Structure and observable purpose |
|---|---|
| `lista` | Search, owned/authorized scope, loaded count, stepped named pockets with saved time/revision, explicit continuation, retained rows on next-page failure, retry/load-more and browser-scene retrieval. Eight realistic fixtures include an owned name beyond the first three rows and two foreign owners. |
| `taller` | First-visit browser-scene offer, named project, visible saving strip with Save now, illustrative schematic, edit simulation and ownership/persistence note. Pending/offline/conflict recovery is adjacent to the workspace. The real Taller's tools are outside this design slice and are not removed by this schematic. |
| `ajeno` | Project name, explicit read-only notice, schematic and owner/revision note. Create owned copy is conditional on Taller access. Errors name a read failure rather than a failed write; offline consultation warns it may be stale. |
| `importar` | Browser-source preview, shared-device explanation, destination account, name, explicit import, reversible Not now, original sample download and preservation notice. Validation leaves the original intact. Success can open the imported project. |

Dialogs are `nombre` (first save or owned copy), `salir` (pending work) and `servidor` (replace visible scene with the saved version). Every scene is independently reachable from the native selector as well as its related product action. Names, dates, revisions, schematic thumbnails and all operations are illustrative. The download contains a labelled sample JSON, never the user's real localStorage.

## 8. States and motion

| State | Visible treatment and recovery |
|---|---|
| Normal | Named project pockets, stored revision and explicit actions. |
| Loading | Structural Skeletons or opening-scene placeholder; save/import actions disabled. |
| Empty/no results | Full-width pocket aligned with heading/footer; create first project or clear search. Empty import returns to projects. |
| Retryable error | Action-specific error and Retry. Read-only failures do not imply writes. Import retry explains lost acknowledgement and preserved original. |
| Pending | Visible changes-pending status; no saved label. |
| Saving/importing | Named in-progress status and disabled repeated save/import. |
| Saved/imported | Text confirmation, revision and preservation information. |
| Offline | Local work is explicitly not in the account; keep working/retry. Read-only preview names staleness and disables copy. |
| Conflict | Taller only: paused queue, local/server comparison, copy or explicit load confirmation. |
| Validation | Invalid naming dialog or unsupported import; text explanation, preserved input/original, raw sample download. |
| Permission denied | Private project body replaced by an access explanation. |
| Session ended | Private view closed, no project metadata, same-account recovery explanation. |
| Next-page error | Loaded collection remains; Retry next page replaces Load more. |

Saving/conflict fixtures have no write meaning in foreign read-only views. Import-specific validation has no dimensional-editor meaning. Unrelated fixtures retain the relevant base view rather than inventing extra operations. Disabled actions state their reason nearby and retain legible text/edges.

The motion grammar is elastic material seating: `cubic-bezier(.16,1.3,.38,1)`. Expressive pocket/title/zip-line arrivals are 650ms; natural 430ms; subtle 250ms. Repeated button feedback is 190/160/120ms. The zipper travel is 850ms, balloon seating 900ms, foil ambient rock 5.8s. Distinct behaviours include pocket compression, title compression, zipper registration, pull rotation/travel, balloon inflation, foil rocking, selected-scope seating, saving-seal press, error pressure release, empty-ring settling, skeleton breathing, scroll registration and hover/press deformation. Motion's installed profile supplies the zipper's interruptible spring and dialog timing.

Main motion changes transforms, never text colour or text opacity. Popup content stays opaque. Hidden tabs pause animations; IntersectionObserver pauses offscreen pockets/scenes. `prefers-reduced-motion`, `?still=1` and Quieto remove animations, transition travel, ambient loops and hover/press transforms while retaining final information/actions. Keyboard zipper changes settle immediately under reduced motion; no essential operation depends on moving it.

## 9. Responsive behaviour

- **1101px and wider:** 44px outer gutters; three pocket columns `1.13fr 1fr 1fr`, staggered at 0/42/84px. Editor is `1.7fr .8fr`; import is `1.1fr 1fr`.
- **761–1100px:** 28px outer gutters; two pocket columns and 42px offset on even pockets; filters wrap to two columns. Editor remains split at `1.4fr 1fr`.
- **760px and below:** 20px outer gutters; single pocket sequence with no stagger, title/actions stack, scene then ownership note, preview then import form, buttons/dialog actions wrap or fill width. The masthead tools wrap; native selects remain bounded. No fixed product navigation obscures content.

Spanish and English labels reflow. There is no document horizontal scroll in the verified 320/390/768/1280px samples. Dialogs are viewport-bounded and scroll internally. Empty/access surfaces share the page's axis and width instead of introducing an unrelated centered form.

## 10. Accessibility and evidence limits

Targets: WCAG 2.2 AA text contrast at least 4.5:1; control edges and focus at least 3:1; labelled native fields; semantic headings, buttons, status/alert regions; modal focus containment and return focus; 3px focus outline with 4px offset. Working buttons and fields are at least 44px high. The decorative zipper target is 44×28px, meeting the AA 24px target floor, with arrow/Home keyboard operation. It carries no essential action.

The initial copy/read/import samples make no production authorization claim. No real login, database, remote scene, 3D renderer, AI request or storage write is performed. The complete-scene drawing is illustrative rather than a persisted thumbnail or a geometry proof. Refresh resets the mock model. Production source/service validation, draft durability, account isolation, atomic versions, race handling, server search, multi-browser restoration and import idempotency need the planned implementation and harness checks.

## 11. Observable criteria and actual verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-01 | 1280px | normal / collection | Three stitched pockets have distinct vertical offsets; each shows name, saved revision and continuation action. |
| C-02 | 390px | normal / collection | Pockets stack on the 20px page axis with no horizontal scroll. |
| C-03 | all | first save | An unnamed project asks for a name before showing a saved revision. |
| C-04 | all | pending/saving | The strip names pending/saving work and does not claim it has reached the account. |
| C-05 | all | conflict | Both local and server revisions appear with copy/load choices; Save now is disabled. |
| C-06 | all | foreign/view-only | Original is read-only; a role lacking Taller cannot create a copy. |
| C-07 | all | import | Destination account and shared-device explanation precede the explicit import action. |
| C-08 | all | import validation | Error explains original preservation and exposes sample original download. |
| C-09 | all | next-page failure | Already-loaded projects remain visible beside Retry next page. |
| C-10 | both themes | keyboard/dialog | Focus is visible; Escape closes the dialog and returns focus to its opener. |
| C-11 | 320/768/1280px | English normal | Each of the four views reflows without document horizontal scrolling. |
| C-12 | all | reduced/still | The same final content/actions appear with no ambient travel or hover deformation. |

Verification log:

- Real offline toolchain: installed/built, 96/96 entries available. Final builder: 807KB bundle, 2,133 source files; standalone HTML after authored-CSS embedding: 843,923 bytes (SHA-256 `a14962b528e8e173db71643f9e1e9c7cdd80eb61135fa6831405cc3f387a64cc`); no fallback, package install or fetched asset. All fonts, styles, scripts and drawings are inline.
- `contrast.py`: **contrast: 158 pairs checked in light and dark, all pass**.
- Initial full audit found 12 grouped alignment findings caused by a narrow centered empty/access pocket. The surface now spans the same page axis as the heading and footer. The next complete audits passed. A later phone alignment finding on the import offer’s unframed “Not now” action was fixed by giving both offer actions explicit outlined surfaces.
- Final complete audit on the final HTML: **256/256 renders, 5,980 text measurements and 774 focus stops** at 1280/390px, both themes.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- Interaction smoke passed nine groups: search beyond the first page/input continuity, first save/revision 1, pending→saving→saved, conflict copy, foreign identity and role restrictions across state changes, modal Escape/return focus, explicit import, keyboard zipper and 24 English viewport/theme/view combinations. After the final font change, 32 English viewport/theme/view combinations at 320/390/768/1280px also passed. No JavaScript errors or external requests.
- Additional focused checks passed for the first-visit import offer, reversible Not now, later retrieval, opaque modal content, 13 active default expressive animations, still/OS-reduced parity and zipper keyboard/rightmost bounds at 320/390/768/1280px. A long pointer drag at 320px stayed inside the page during and after the gesture.
- In-memory screenshots were inspected at 1280 light collection, 390 dark collection, 1280 dark conflict, 390 light invalid import and 390 dark foreign read. No screenshot files were written outside the task's output list.
- Offline three-direction comparison passed with all evidence measured and no missing selectors. A/B layout similarity 0.007; A/C 0.003; B/C 0.050. Typography, navigation and motion differ in all pairs. The final run had `ok: true`, `evidence_ok: true`, no missing evidence and exit 0; every C selector passed. Compared HTML SHA-256 prefixes: A `0d1dce11f823c34e`, B `1c627ccb63ff24eb`, C `a14962b528e8e173`. Numeric distinction does not approve taste: sibling A/B still use related serif and warm-action families; their owners should review that overlap independently. No sibling file was edited.

## 12. Open questions, impact and approval

Q: If Estuche is selected, does David approve this pool-blue/cyan/pink palette and rounded-display pairing for Saved projects, or should finalization map the selected composition back to another shared Pictures palette?

Q: Should the selected design use scene-derived project previews in the pockets, or a clearly schematic placeholder until real thumbnails are available? R6/R7 require saved name and complete scene, not a new thumbnail-generation service; this exploration uses labelled drawings and does not add such a service.

Confirmed decisions are not reopened: explicit first named save then autosave; full scene and name travel across browsers; AI conversation/images remain local; staff read foreign originals and create owned copies only with Taller access; no silent concurrent overwrite; legacy import requires consent and preserves the original.

Potential consumers are SP-4 design copy T4.1, UI tasks T4.4/T4.5, harness T4.6/T4.7, visual review T4.8 and audit T4.9. R6 maps to collection/editor/read-only/conflict; R7 maps to first-visit offer/import/validation/preservation. This exploration changes hierarchy, material components, navigation emphasis, tokens, typography and motion. Compatibility is **undetermined until owner selection and finalization**. No plan consumer is redirected, no shared contract/history/changelog is changed, and no downstream subplan is authorized to consume this draft.
