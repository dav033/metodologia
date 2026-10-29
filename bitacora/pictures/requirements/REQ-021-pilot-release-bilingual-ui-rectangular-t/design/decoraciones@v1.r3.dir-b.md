---
name: Espacio de composición
status: draft
artifact: exploration
subplan: SP-5
requirement: R8
contract_candidate: decoraciones@v1
direction: b
source_revision: r3
plan_revision: 15
date: 2026-10-29
owner: David
---

# Espacio de composición — direction b

## 1. Identity and traceability

Planning exploration, **draft and unapproved**. This direction is a candidate for `decoraciones@v1`, not the canonical contract. The owner chooses a direction in the comparison; a later finalizer writes the canonical contract. Nothing here approves the plan or authorizes implementation.

Scope: SP-5, R8, shared `decoraciones@v1.r3.behavior.md`, SPEC § “Behavior — SP-5 (round 11 answered)” and PLAN.json revision 15. Consumers after independent approval: T5.1 copies the contract, T5.3 implements the personal library, T5.5 reviews its rendered result. This exploration creates only its two candidate HTMLs, TSX, built HTML, this note and axis JSON, plus the explicitly requested delegation result. No repository, canonical artifact, SPEC, PLAN, changelog or preview is changed.

Read-only evidence: both repositories' `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/Biblioteca.tsx` and `Taller3D.tsx`. `Biblioteca.tsx` is identical in t12 and asesor. Their theme token blocks match; globals.css differences concern an icon-button extraction and prompt-bar styling, not the palette used here. Existing surface: Taller `/3d`, selected-piece/current-scene save controls, name/occasion form, thumbnail library, occasion/color/balloon filters, item preview, “Añadir a mi escena” and removal of browser-local items. Existing storage is `taller3d:biblioteca-propia:v1`. Server/account separation is the required change.

Sibling inputs read: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html` and `proyectos@v1.md/.html`. Their finalized shared shell vocabulary is retained: Pictures/Sempertex ring-and-dot masthead, language selector, account disclosure, 24px H1, neutral horizontal route rule, embedded Geist and rounded controls. Proyectos' chosen r12 source supplies the shell and production token mapping; the changed library arrangement is composed anew.

Impact classification: **breaking UI candidate** for T5.3, subject to owner selection; the spatial library/ficha arrangement, focus navigation and responsive behavior need implementation and T5.5 review. No approved predecessor is changed. Production compatibility is unverified; this is not a storage or authorization implementation.

## 2. Purpose and users

The working question is “Which saved decoration do I want to add to my current project?” A signed-in account with Taller, including Master Designer and staff, saves the whole scene or its selected piece with name and occasion. Success requires server-confirmed account storage, later retrieval from another browser and placement into an owned project.

Staff can inspect another account's library read-only. The owner and read-only label remain visible, and placement creates a copy in the staff member's own project. Rename, edit and delete controls are absent for the foreign original. Accounts without Taller do not enter this library; granting access remains with the established account/role surface.

## 3. Approach, composition and thumbnail choice

**Chosen thumbnail:** `decoraciones@v1.r3.dir-b.html.candidate-1.html` — lateral library, central preview, right inspector. The list, search and occasion filter remain visible while the selected decoration has a large preview and its actions occupy one stable edge. It fits the existing Taller's canvas-and-inspector working model while changing only the personal-library area.

Candidate 2, `decoraciones@v1.r3.dir-b.html.candidate-2.html`, places the library in a bottom tray below preview and ficha. Its thumbnail makes the preview wider but compresses collection navigation and omits the search/filter area from the tray. Candidate 1 better accommodates this brief's required library controls without creating another page. Both small visual compositions were written and rendered before the complete TSX was built.

| Axis | Observable direction |
|---|---|
| concept | Espacio de composición: keep the existing Taller shell and arrange the personal library, isolated preview and item inspector as three connected working areas. |
| layout | At 1100px+ a 280px library, flexible central preview and 264px inspector share one continuous workshop panel; at 640–1099px the inspector sits below the preview; at 320–639px all three areas stack. |
| navigation | Preserve the Pictures/Sempertex masthead and neutral Taller 3D/Proyectos route rule. Inside the workshop, Biblioteca/Vista previa/Ficha moves focus to each area; account/browser source buttons change the list without changing route. |
| typography | Use the existing embedded Geist Sans and Geist Mono. H1 stays 24px; inspector heading 20px, library heading 18px, item name 14px, labels 12–14px and supporting metadata 12–13px. |
| density | A compact thumbnail list and a single expanded item share the screen; filters beyond occasion use native disclosure. Desktop insets are 20–24px inside the inherited shell, with 20px phone gutters and 44px controls. |
| components | Recompose real installed shadcn Button, Input and Skeleton with Animate UI/Base UI Dialog and AlertDialog; use semantic native source buttons, selects and details, an inline SVG mock scene and a Motion shared area marker. |
| colour | Use only Pictures globals.css tokens and the finalized sibling aliases: fondo/superficie/texto/acento plus Taller preview roles; texto-tenue supplies accessible control edges, and exito/error/aviso identify actual feedback. Both themes retain the same palette and fonts. |
| motion | Spatial choreography: library travels 20px from the left, inspector 24px from the right, records stagger 65ms, preview seats horizontally and its object enters with 25px travel/−12deg Y rotation. Expressive travel 640ms, natural 360ms, subtle 160ms, easing cubic-bezier(.23,1,.32,1); shared area marker uses the kit profile spring. Reduced motion and still mode remove all travel. |

The workshop toolbar retains the current project's identity and existing Deshacer/Rehacer, Foto realista and Lista de compra vocabulary. The preview explicitly does not modify that open project. “Añadir a mi escena” changes the mock scene only after activation and reports an owned copy. The global decoration catalogue stays separate.

## 4. Fixed design system and actual components

No palette, font or identity is introduced. Local Next WOFF2 assets embed Geist Sans and Geist Mono; no font is fetched. Rounded shell/control roles remain those of the sibling drafts (panel 32px, inset 24px, field 18px, pill 999px); the existing Taller frame uses its sibling 24px radius.

| Product token | Kit role / use |
|---|---|
| `--fondo`, `--texto` | background, foreground |
| `--superficie`, `--superficie-2` | card/popover and secondary/muted surfaces |
| `--texto-suave`, `--texto-tenue` | supporting text; accessible control-edge alias |
| `--acento`, `--sobre-acento`, `--acento-hover` | primary, primary-foreground, hover |
| `--borde`, `--borde-suave` | decorative boundaries and dividers |
| `--exito`, `--exito-suave` | confirmed save and placed-copy feedback |
| `--error`, `--error-suave`, `--aviso`, `--aviso-suave` | failure and unsupported-piece feedback |
| `--taller-visor`, `--taller-panel`, `--taller-barra` | preview, its context and workshop chrome |

The entry contains explicit light/dark values copied from production/sibling sources, once per theme. Examples: fondo `#faf9fc/#0b0c10`, texto `#1c1425/#f4f5f7`, acento `#6d3fe0/#9479ff`, sobre-acento `#ffffff/#120b24`. Active global navigation uses text and its rule; primary-action colour identifies the placement/save action. The SVG illustration uses the same tokens and is visibly example data, not a proposed stored-thumbnail format.

| Actual source:id / variant / states | Import or implementation |
|---|---|
| shadcn:button / default, outline, destructive / normal, hover, focus, disabled, busy | `@/components/ui/button` |
| shadcn:input / text / filled, empty, invalid, disabled, focus | `@/components/ui/input` |
| shadcn:skeleton / item thumbnail and lines / loading | `@/components/ui/skeleton` |
| shadcn:dialog / rename and metadata edit / open, validation, pending, closed | `@/components/ui/dialog` using installed Animate UI/Base UI |
| shadcn:alert-dialog / removal / confirmation, pending, cancel | `@/components/ui/alert-dialog` using installed Animate UI/Base UI |
| kit:mockup / native inspection / view, state, scene, theme, motion | `mountMockup/useMockup` from `@kit/mockup` |
| kit:motion / profile / expressive, natural, subtle, reduced | `useMotionProfile` from `@kit/motion`, `motion.i` from `motion/react` |
| custom:source-nav, zone-nav, library-record, preview, inspector | Semantic HTML and project-token CSS, not claimed as an installed library component |
| custom:account-disclosure | Native details/summary retained from sibling shell |

The installed component workspace reports installed/built and 96/96 entries available. No fallback, package install, asset download or runtime network request was used.

## 5. Navigation and interaction model

The product masthead and Taller 3D/Proyectos routes remain recognizable and neutral. Proyectos/account/plans destinations remain owned by sibling subplans; contextual controls display a clearly marked mockup scope notice rather than fabricating new product screens. Sign out in the mockup immediately clears its account fixture and demonstrates the isolation placeholder; this is not proof of authentication.

Within the changed area, Biblioteca/Vista previa/Ficha move focus to labelled areas. They scroll only when needed, with a shared moving selection marker. In save views the final area is labelled Guardar and the name field receives focus; phone scroll brings that form into view. Selecting a library item changes its preview and ficha without replacing the open project.

Source controls distinguish “En mi cuenta” from “En este navegador”. Staff viewing another account sees “En esta cuenta” and an explicit owner selector. That selector is a provisional demonstration of authorized scope, not a client authorization rule. Source changes clear search/filter selection. Search, occasion/type/color/balloon filters operate on a small labelled example subset, with a no-results recovery. In this subset all records contain latex; only scenes contain white balloons. Other catalogue options are intentionally absent from this small fixture.

Buttons and links that would replace the save target are held during a pending save. Dialogs contain focus; Escape/cancel and successful completion restore the surviving trigger, with inspector fallback after removal. Foreign-account forced planning dialogs show a read-only explanation without a mutation form/action. Loading and account switching suppress item dialogs as well as list/detail/preview data.

## 6. Flows

1. **Save the scene:** choose “Guardar toda la escena en mi biblioteca” → inspect whole-scene preview → name and occasion → Guardar → pending, duplicate submission disabled → show saved only after simulated confirmation → “Ver en mi biblioteca”. Implementation must use a real server confirmation, and support reload/other-browser retrieval.
2. **Save a selected piece:** choose existing “Guardar en mi biblioteca” in selected-piece context → piece-only preview and same form → confirmed account save. Unsupported pieces show the existing “Esta pieza no se puede guardar sola.” message and disabled save. The sample footer action illustrates that existing selected-piece entry.
3. **Recover save failure:** error remains with name and occasion visible → “Reintentar guardar” → same target/input while pending → confirmation. Failed saves do not enter the account list or receive a saved label.
4. **Find/place:** select source → search/filter → choose thumbnail row → inspect name/type/occasion/owner → “Añadir a mi escena” → owned copy feedback. The original decoration remains in its library. Static placement is illustrative; it is not the 3D engine.
5. **Staff inspect/place:** authorized staff scope → Cuenta de ejemplo → owner/read-only treatment → absent rename/edit/delete → add a copy to their own project. No original mutation or ownership change is offered.
6. **Owner metadata/removal:** Renombrar or Editar → named fields → wait for confirmation → update list/ficha; Q2 still governs content-edit scope. Removal uses AlertDialog; cancel keeps the item, confirmed server removal updates the account list. Existing browser-local removal updates only its group immediately and never imports it.
7. **Account isolation:** account switch/sign out → clear previous server list, detail, thumbnail and preview before loading the next account → neutral skeleton → next account's empty list. The example continuation button is a mock inspection aid, not a production account-switch flow. Legacy browser storage is not migrated or mutated by this transition.

## 7. Views and content boundaries

| Native view | Changed area and main action |
|---|---|
| `library` | Own account/browser collection, search/filter, central selected-item preview and right ficha. Main action: Añadir a mi escena. Owner-only server metadata and removal actions. |
| `save-scene` | Same shell/library/preview arrangement; right inspector becomes the whole-scene name/occasion form. Main action: Guardar. |
| `save-piece` | Same arrangement with selected-piece preview and form, including unsupported-piece recovery. |
| `staff` | Same arrangement with owner scope and visible read-only treatment. Main action adds an owned copy; foreign-original mutation controls are absent. Selecting Mi cuenta demonstrates the staff member's own library. |

Native scene inspector: none, rename, edit, remove. The last uses real AlertDialog. Planning inspector labels stay Vista/Estado/Diálogo/Tema/Movimiento and retain “Mockup”. All names are “de ejemplo”, occasions come from the existing UI, and no customer identity, date, claim or marketing heading is invented. ES/EN product copy is switched through the inherited language control.

The account-deletion guard is an existing account-management consequence (“saved decorations prevent delete; deactivate instead”), not a new admin screen in this Taller exploration. Its service and account UI acceptance belong to the plan's owners; no delete-account control is added here.

## 8. State catalogue

| Native state | Applicable view / observable behavior |
|---|---|
| `normal` | All views: confirmed example records or ready name/occasion form. |
| `loading` | Account list skeletons, neutral preview and inspector; no stale account record or item action. |
| `empty` | Empty server collection with save-scene entry for an owner; local source still contains its independent fixture. |
| `list-error` | Account-load error and Reintentar; no authoritative record/preview while the read failed. Browser group remains independent. |
| `saving` | Save views: retained name/occasion, disabled submission, “Guardando en mi cuenta…”, no new saved result. |
| `saved` | Save views: “Guardado en mi cuenta” and Ver en mi biblioteca. Only confirmed records appear as saved in list views. |
| `save-failed` | Save views: preserved editable values, error, Reintentar guardar. |
| `account-switch` | All views: previous server list/details/art/owner data removed before next-account skeleton; no item dialogs. |
| `placed` | Library/staff: owned-copy feedback and illustrative current-project preview. Original library item remains. |
| `validation` | Save views: empty name input, associated error and visible recovery. A trimmed non-empty name is the provisional rule. |
| `action-error` | Ficha: action not completed, item retained and retry. No success/deletion is claimed on failure. |
| `unsupported` | Selected-piece save: existing unsupported-piece explanation; save disabled. Not applicable to whole-scene save. |

State axes are inspection controls: save-only states do not invent artificial form failures on a list-only view. Live mutations use finite simulated delays. Inspection changes/remounts can reset example inputs; refresh resets the artifact's fixtures. No real API, cross-browser persistence, auth enforcement or session storage is claimed. Permission enforcement remains server-owned. Offline/stale reads use the recoverable list/save error treatments; no new offline or import route is introduced. There is no import, import-progress or import-error state.

## 9. Responsive behavior

| Width | Composition |
|---|---|
| 1100px+ | Three columns: 280px list, flexible preview, 264px inspector. Shared shell max-width 1520px and 40px outer gutters. One continuous bordered workshop; no nested card grid. |
| 640–1099px | 24px outer gutters. List stays 260px on the left, preview on the right and inspector below preview; metadata/form controls may use two columns. Header tools wrap. |
| 320–639px | 20px outer gutters. Header wraps as in siblings; list → preview → inspector in reading order. Area navigation fits one row; source controls remain visible. Save entry scrolls/focuses the form. Controls and text wrap without horizontal page scroll. |

The preview resizes as an illustration rather than shrinking text. No fixed-height text panel clips copy. Search and selects fit their column; dialogs use viewport-bounded width/height and scroll internally. Both themes and both languages share the same breakpoints.

## 10. Accessibility and interaction/motion detail

Targets: WCAG 2.2 AA, 4.5:1 text, 3:1 meaningful control edges/focus, minimum 44px controls, associated labels/errors, semantic navigation and list-selection buttons. Selection uses aria-pressed/current as well as colour. Loading uses busy/status; errors use alert; confirmations use status. Dialog/AlertDialog use the actual installed focus-containment primitives. The small scene SVG is illustrative and aria-hidden; nearby visible text identifies the preview. Production screen-reader task testing, 200–400% zoom and cross-browser validation remain acceptance targets, not claims from this static artifact.

The direction's memorable detail is spatial docking: the collection enters from its own side, the inspector from the opposite side and only the scene object makes a short perspective turn. Text stays visible throughout. Item entrances stagger, and the local area marker slides using the kit's profile spring. Button press/hover uses the inherited tactile controls. This motion stays inside the existing Taller; it is not a new brand animation.

CSS timing/easing and evidence selectors are in the companion JSON. Expressive travel 640ms/65ms stagger; natural 360/35ms; subtle 160/15ms; repeated controls 180/150/100ms. `useMotionProfile` supplies the actual spring/reduced state. Hidden-tab/offscreen work pauses. Reduced-motion preference, Quieto and `?still=1` remove transforms/transitions and show the same final content immediately. No infinite decorative loop exists; pending spinners also stop under reduction.

## 11. Observable acceptance and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-AC-01 | 1100px+ | normal | Library, central preview and right ficha occupy three distinct columns inside the inherited Taller shell. |
| B-AC-02 | 320–639px | normal | The three areas stack in DOM order with no horizontal page scroll and a single-row area navigator. |
| B-AC-03 | 320px+ | save-scene/save-piece | Name and occasion are labelled; current save target is explicitly scene or piece. |
| B-AC-04 | 320px+ | saving | Pending copy is visible; the new record does not receive a saved result before confirmation. |
| B-AC-05 | 320px+ | saved | Confirmed account-save text and library-return action appear. |
| B-AC-06 | 320px+ | save-failed | Error, retained name/occasion and retry action appear together. |
| B-AC-07 | 320px+ | empty | Empty account list has an owner save entry; browser-local records remain in a separate source. |
| B-AC-08 | 320px+ | loading | Skeleton records replace account names/thumbnails; preview and inspector expose no stale record actions. |
| B-AC-09 | 320px+ | staff | Foreign owner and read-only label are visible; rename/edit/remove buttons are absent. |
| B-AC-10 | 320px+ | placed | Placement reports a copy in the current user's own project; the original remains listed. |
| B-AC-11 | 320px+ | account-switch | Previous server names, thumbnails, detail and preview are absent before next-account results. |
| B-AC-12 | 320px+ | browser group | “En este navegador” identifies local data and has no import action/state. |
| B-AC-13 | 320px+ | removal | AlertDialog cancellation leaves the selected item and returns focus after close. |
| B-AC-14 | 320px+ | validation | Empty name input exposes an associated visible error and can receive keyboard focus. |
| B-AC-15 | 320px+ | light/dark, ES/EN | Project tokens and Geist remain unchanged; controls/copy remain inside their columns. |
| B-AC-16 | 320px+ | reduced/still | Content and outcomes are unchanged with zero running entrance animations. |

Offline builder: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/decoraciones@v1.r3.dir-b.tsx --out <design>/decoraciones@v1.r3.dir-b.html` → 651 KB, 2135 source files, exit 0, offline. The real builder is available; no HTML fallback.

Contrast: `python3 <kit>/kit/contrast.py <design>/decoraciones@v1.r3.dir-b.html` → **158 pairs checked in light and dark, all pass**, exit 0.

Final rendered audit: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/decoraciones@v1.r3.dir-b.html` → **240 renders (240 combinations planned), 9,804 text measurements, 1,564 focus stops**, exit 0. All declared view/state/theme combinations plus every dialog scene on each view's base state were rendered at 1280/390px, without sampling. Motion/reduced-motion probes also ran.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

Playwright interaction evidence: confirmed scene/piece saves, no early saved label, retained retry inputs, staff mutation-control absence and owned copy, local group without import, account-switch data clearing, confirmed rename/focus return, removal cancellation/local-only removal, English/dark reflow at 320/390/760/1280px, phone form focus, actual running choreography and zero running animations under `?still=1`. No browser error or HTTP request was observed. A final check also confirmed every axis-evidence selector exists in the rendered DOM and that save-target navigation/item selection is disabled until confirmation. A focus assertion was initially made before asynchronous close/focus restoration completed; waiting for the actual completed focus state passed, with no source change for that timing correction.

Both candidate thumbnails and full mockup screenshots were inspected in memory. Desktop light library, desktop dark staff, phone dark library and phone light piece-save preserve the product shell, the three areas and readable controls. The phone navigator was refined to stay on one row, and save entry now focuses the form instead of leaving it below the list. No screenshot file or separate preview was written.

Automated measurements supplement design review: they do not prove service persistence, authorization, real scene geometry, thumbnail production or account-deletion enforcement. Pairwise comparison with the other two exploration directions remains with the owner/Planner comparison workflow.

## 12. Open questions and assumptions

Q: Owner/Planner — From which existing entry should Empleado interno and Administrador open another account's decoration library, and should the provisional owner selector remain inside the Taller library?
Q: Owner/Planner — Does “Editar” update only the decoration's name/occasion, or must the owner also replace its saved composition? This candidate demonstrates metadata only; content-edit behavior must be settled before finalization.

Confirmed: no browser-local import; local source remains independent; new saves belong to the signed-in account; saved status follows server confirmation; foreign staff access is read-only; placement produces an owned copy; only the owner mutates/deletes; Taller access is required. Assumptions awaiting finalization: keep existing owner/local removal, use a non-empty trimmed save name, preserve existing occasion taxonomy, and show only neutral example data in the mockup.

CONCERNS: owner selection and plan/contract approval remain outstanding. The two questions above are intentionally recorded rather than blocking exploration. Static fixtures are not persistence/auth evidence. Metadata editing, staff entry and production account isolation require their final contract and service implementation. No engineering-only task or extra production path is designed here.
