---
name: Registro de biblioteca
status: draft
subplan: SP-5
contract_target: decoraciones@v1
revision: r2
direction: a
scope: planning-exploration
source_behavior: decoraciones@v1.r2.behavior.md
chosen_thumbnail: decoraciones@v1.r2.dir-a.html.candidate-1.html
---

# Registro de biblioteca — operational direction A

This exploration is complete as a candidate for comparison, **unapproved and not the canonical contract**. The owner chooses the direction and later approves the plan. No production implementation, shared contract, other direction, SPEC, PLAN or project memory was edited.

## Approach and existing-surface delta

The working question is “Which of my saved scenes or pieces should I add to this project?” Keep that answer beside the existing Taller viewer: a compact, ruled library occupies the left working panel; the selected item's geometry, provenance and copy-placement action occupy the right workspace. Saving a whole scene or the selected piece replaces the right detail with the existing name/occasion form vocabulary. It is a change inside the Taller, not a destination page or catalogue redesign.

The shell reuses the finalised sibling contracts: Pictures ring-and-dot mark, Sempertex, language/account disclosure, 24px heading and neutral horizontal Taller 3D / Proyectos routes. The scene toolbar, tool rail, undo/redo, Foto realista and Lista de compra remain recognisable context. Their unrelated mock handlers announce their existing destination rather than pretending to implement it. This direction reorganises only personal-library retrieval, saving and the saved-item detail. The global/admin catalogue stays separate.

Production sources inspected read-only: both repositories' `src/app/globals.css`; t12 `src/components/tres-d/Biblioteca.tsx` (local persistence, FiltrosCompactos, FichaDialogo, AccionesPieza), `PanelAnadir.tsx`, `Taller3D.tsx`, and `src/components/ui/shell/CabeceraApp.tsx`. Sibling inputs read: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html`, and `proyectos@v1.md/.html`; the selected proyectos r12 source supplies the exact shared shell/token mapping. SPEC Behavior — SP-5 (round 11 answered) and current PLAN.json SP-5 confirm the owner/staff boundary. The r2 behavior brief and latest owner feedback govern the scope.

## Two thumbnails and choice

Both thumbnail HTMLs were drawn before the complete TSX entry. They are intentionally small compositions, not alternate complete contracts.

- **Candidate 1 — chosen:** adjacent library rows and scene workspace. Search, scene/piece identity and placement stay beside one another on desktop. It scales to the Taller's existing phone panel switching.
- **Candidate 2 — retained:** the viewer above a horizontal lower library dock. This gives more canvas width but lengthens the path between the search controls, selected row and placement detail. It also consumes the vertical space needed for the save form on phones.

Files: `decoraciones@v1.r2.dir-a.html.candidate-1.html` and `decoraciones@v1.r2.dir-a.html.candidate-2.html`. Both are static, use embedded existing Geist and the product tokens, and are clearly labelled Mockup. The complete artifact uses the real offline builder; these sketches are not a toolchain fallback.

## Eight-axis direction

| Axis | Observable implementation |
|---|---|
| concept | An operational personal-decoration register inside the existing Taller: identify a scene or piece, inspect it and place a copy without leaving the work surface. |
| layout | Preserved Pictures/Sempertex masthead and horizontal Taller/Proyectos routes; 52px tool rail, 390px library and flexible scene/detail workspace. At phone width, Biblioteca/Escena exposes one workspace panel at a time. |
| navigation | Existing product routes remain horizontal and neutral. Mi biblioteca is the owner entry; Otra cuenta and its owner selector appear only in the staff fixture. Search, type and occasion narrow the register; Filtros reveals colour and balloon controls. |
| typography | Existing Geist Sans: 24px page title, 20px library and selected-item headings, 14px item names, 13px controls and 12px provenance. Existing Geist Mono is limited to Sempertex. |
| density | Ruled compact records with 66px thumbnail columns and 16px vertical insets; no repeated large cards. Colour and balloon filters are disclosed on demand, with browser-local records in a separately labelled group. |
| components | Installed shadcn/Base UI Button, Input and Skeleton; Animate UI-backed Dialog for name/occasion and AlertDialog for deletion. Existing native filter selects and details/account disclosure; custom static scene SVG is labelled Mockup. |
| colour | Exact Pictures globals.css and finalised sibling token mappings: fondo/superficie/texto/acento plus existing Taller, success and error roles. No new palette or font; texto-tenue supplies accessible input edges. |
| motion | Precise lateral registration: rows move 12px over 220ms with 40ms offsets and cubic-bezier(.77,0,.175,1); feedback enters laterally and confirmation marks settle over 360ms. Natural 170/24ms, subtle 120/12ms, 150ms hover/press. Reduced motion and still show final content immediately; hidden tabs pause CSS animation. |

Selectors in `decoraciones@v1.r2.dir-a.json` target actual rendered elements. `.decoration-row` runs `row-cut`, not just a claim of motion; `.btn` has measurable hover/press transitions. Native `#view`, `#state`, `#scene`, `#theme` and `#motion` remain outside the product as the kit's planning controls.

## Views, flows and state coverage

| Native Vista | Product task and structure |
|---|---|
| Biblioteca | Search the account list, select a scene/piece, inspect its thumbnail/provenance, add a copy into the open project. The owner can edit name/occasion or confirm deletion. |
| Guardar escena | Current scene preview → name and occasion → Guardar → Guardando… → confirmed success, or preserved form and Reintentar. |
| Guardar pieza | Same in-place form for the selected piece, with “La pieza sola.” explanation and piece preview. |
| Otra cuenta · Solo lectura | Staff-only owner context and read-only marker precede the list. Edit, rename and delete controls are absent. “Añadir copia a mi escena” targets the staff member's own scene. |

| Native Estado | Visible result / recovery |
|---|---|
| Normal | Account-owned rows and the distinct local group; selected detail and placement action. |
| Cargando | Two skeleton records, loading copy and no saved-item edit/place controls. |
| Cuenta vacía | Empty server list with a save-scene entry; the existing browser-local group remains distinct. No invented server record becomes editable. |
| Error de carga | Persistent error, explanation and Reintentar; no fictitious selected saved item. |
| Guardando | Save control disabled; name/occasion preserved and locked during the request simulation. No saved confirmation or newly added row before completion. |
| Guardado confirmado | Server-confirmed success illustration, explicitly marked as a simulation in the form. Real click flow adds the mock row only after its simulated response. |
| Error al guardar · Reintentar | Form stays visible with its name/occasion, contextual failure and retry action. The normal submit and retry use the same pending/confirmed sequence. |
| Cambio de cuenta | Previous server rows, detail, local group and item actions are removed immediately. Neutral loading placeholders do not reuse the previous account's items. |
| Sesión cerrada | Session explanation; account rows/detail are absent. The native state selector supplies the test-only return to an authenticated fixture. |
| Sin acceso al Taller | Access explanation for accounts without Taller; no library items or restricted item controls. |
| Sin coincidencias | Clear-filter action; no fabricated match or selected saved-item controls. |
| Copia añadida | Persistent local confirmation of copy placement in the current scene. No original item is mutated. |

The first two states remain stable when selected in the inspector. Interactive Guardar/Reintentar completes after a clearly simulated response (1100ms); metadata edit and deletion demonstrate a 900ms confirmation. Those delays are fixture mechanics, not API performance requirements. Blank-name validation is local and focuses no unrelated flow. Search, occasion, type, colour and balloon controls work on deliberately tiny fixtures. Counts derive from the displayed fixture records. The search/filter result does not become a new authoritative catalogue.

Native Diálogo exposes Editar nombre y ocasión and Eliminar decoración for an owned server item. Real Base UI-backed modal/alert-modal components manage inert background and keyboard containment. Cancel returns focus to the originating control; after deletion focus moves to the remaining row. Selecting a row on a phone reveals the scene panel and transfers focus to its selected-item heading. Dialogs are suppressed for staff, local-only items and invalid sessions. Mutation controls are absent in staff mode rather than presented as disabled permissions.

**Browser-local rule:** `taller3d:biblioteca-propia:v1` is an existing product source, not read or written by this fixture. “En este navegador” is a separate illustrative group with a local provenance label. There is no import action, progress, error or conversion flow. No account response is represented as a local legacy entry. Legacy items have no new edit/delete controls in this exploration.

**Account rule:** saved items belong to accounts with Taller (Master Designer and authorized staff). Account deletion refusal/deactivation belongs to the existing account administration surface; this design does not add another deletion-account interface. Backend authorization, second-browser persistence, sign-out cleanup, caching and request cancellation must be implemented and independently tested by their assigned tasks; a static mockup cannot prove them.

## Fixed design system and responsive behavior

The entry embeds the local Next Geist and Geist Mono WOFF2 assets. Exact sibling semantic mapping is preserved: `--fondo → --background`, `--superficie → --card/--popover`, `--texto → foregrounds`, `--texto-suave → --muted-foreground`, `--acento/--sobre-acento → --primary/--primary-foreground`, `--texto-tenue → --input`, with existing success/error/warning and Taller roles. Light background/surface/accent: `#faf9fc / #ffffff / #6d3fe0`; dark: `#0b0c10 / #16181f / #9479ff`. These are existing globals.css values, not a direction palette. Existing sibling radii remain 32px panels, 24px insets, 18px fields and pill controls; the work surface retains the Taller's 24px outer framing.

Real installed sources: `shadcn:button` outline/default/destructive states from `@/components/ui/button`; `shadcn:input` from `@/components/ui/input`; `shadcn:skeleton` from `@/components/ui/skeleton`; `shadcn:dialog` from `@/components/ui/dialog`; `shadcn:alert-dialog` from `@/components/ui/alert-dialog`. Dialog primitives are the installed Animate UI/Base UI implementations. The register rows and neutral scene SVG are custom composition; the SVG is illustrative geometry, not a production 3D thumbnail or renderer. No package installation or asset fetch occurred.

- **1024px and above:** 40px outer gutters, existing toolbar and a 52px rail + up-to-390px library + flexible scene/detail layout.
- **640–1023px:** 24px gutters, 44px rail and 300px library; save fields stack and secondary scene toolbar actions hide to preserve the workspace.
- **Below 640px:** 20px gutters, wrapped existing masthead and horizontal product navigation. Biblioteca/Escena controls switch the single visible workshop panel; row selection opens the scene/detail. Save views start on Escena. Fields and dialog actions stack; no page-level horizontal scrolling. Validation includes 390px phone and additional 768px/tablet and English reflow.

Controls use at least 44px targets, explicit labels, 3px visible focus, semantic error/status announcements, native selects and reduced-motion parity. These are design targets with the measured evidence below, not a blanket WCAG certification. Reduced/still suppresses travel and animations without hiding content; hidden tabs suspend CSS animation. No perpetual display animation is introduced.

## Reviewable visual expectations

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1280px | Normal | Shared Pictures/Sempertex masthead and horizontal product navigation precede the existing Taller toolbar. |
| A-02 | 390 / 1280px | Normal | Server rows and En este navegador have separate headings and provenance; no import control exists. |
| A-03 | 390 / 1280px | Guardando | No Guardado confirmation or new server-list row appears before the response simulation completes. |
| A-04 | 390 / 1280px | Error al guardar | Name/occasion remain available for retry and the failure is announced. |
| A-05 | 390 / 1280px | Staff | Edit/rename/delete controls are absent and the primary action explicitly adds a copy to the staff member's own scene. |
| A-06 | 390 / 1280px | Cambio de cuenta | No previous account's decoration row or saved-item detail remains visible. |
| A-07 | 390px | Normal / selection | Biblioteca/Escena panel switching reflows without horizontal scrolling; row activation focuses the selected detail heading. |
| A-08 | 390 / 1280px | Reduced / still | Final readable state appears without travel, with the same controls and statuses as expressive mode. |

These are exploration expectations for comparison, not an approved implementation contract.

## Evidence and honest limits

- Real offline builder, absolute entry/output paths: successful self-contained HTML, about 638KB, 2135 bundled source files; inline JS/CSS and embedded fonts, no network asset references.
- Token contrast: `contrast: 158 pairs checked in light and dark, all pass` (exit 0).
- Rendered audit on the final output: `audit: decoraciones@v1.r2.dir-a.html — 224 renders (224 combinations planned), 7604 text measurements, 1648 focus stops` (exit 0).

  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Behavior smoke: staff read-only, copy placement, immediate account-item clearing, server-confirmation gating, retry form retention, modal/cancel focus, 24 width/theme/view cases (390/768/1280), English reflow, no HTTP(S) requests or page errors; all passed. Added phone row-selection focus test passed.
- Screenshots inspected directly in both themes at 1280 and 390: light owner library, dark staff view, light phone save-piece and dark phone library. First pass led to reducing filter height; colour/balloon filtering stays accessible under Filtros. Later changes only add the focus transfer on row selection; final audit covers the final build.
- Additional selector/filter smoke: every JSON evidence selector resolves; expanded Color/Globo filters are visible and operable, with no overflow at 360/390/768/1024px. Both candidate thumbnails contain embedded fonts and no unresolved asset expressions. An initial exact-label test and diagnostic timed out because the wrapped select label includes option text; the corrected scoped DOM locator passed without changing the mockup. This was a test-locator failure, not evidence of a hidden dropdown.
- No repository lint/test/build was run: production repositories are read-only and unchanged. No account API, server persistence, second browser, permission service, actual 3D engine or deployment is tested by this static artifact.

## Open questions / CONCERNS

Q: Does editing an owned decoration cover only its name and occasion in the pilot, or must it also explicitly replace the stored composition? The illustrated editor covers metadata; composition replacement awaits the owner/Planner decision.
Q: From which existing account/admin surface should staff enter another account's decoration library? The exploratory staff fixture uses a scoped owner selector in the Taller; the production entry point remains unconfirmed.
Q: Should saving an existing name create a separate item, require another name or explicitly replace an item? The mockup demonstrates a new record after confirmation and never silently overwrites by name.

All three decisions belong to David and the Planner. They do not block comparing this direction. No canonical contract or implementation approval is granted. Production cache isolation, denied API mutations and account-deletion refusal require their assigned engineering and independent acceptance tasks.

## Consumer impact

Only SP-5 consumes decoraciones@v1: T5.1 copies the subsequently approved contract, T5.3 implements the personal-library UI and T5.5 performs independent visual review. This r2 exploration changes none of those references. Compatibility is **undetermined until direction/plan approval**; relative to the current browser-only library the server/local separation, read-only mode and responsive working-panel hierarchy require T5.3 adaptation. Shared sibling shell/tokens are retained; no other subplan is assigned new implementation work. Finalisation must resolve the questions and write the canonical twelve-section contract in its separately authorised task.
