---
contract: decoraciones
version: 1
status: draft
subplan: SP-5
requirements: [R8]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: b
name: Espacio de composición
source_revision: r3
source_behavior: decoraciones@v1.r3.behavior.md
source: decoraciones@v1.r3.dir-b.tsx
plan_revision: 17
---

# decoraciones@v1 — Espacio de composición

## 1. Identity and traceability

Canonical planning **draft; not approved for implementation**. The owner chose direction b, “Espacio de composición”, in the web comparison. That choice authorizes this finalization only; it does not approve this contract, SP-5 or the plan. Version 1; no approved predecessor exists, so nothing approved is changed. This task writes only `design/decoraciones@v1.md` and `design/decoraciones@v1.html` (plus the delegation RESULT). No exploration, history, SPEC, PLAN, changelog, preview or production file is changed.

Scope: REQ-021 / M2 / SP-5 “Saved decorations”, R8, from SPEC (§ “Behavior — SP-5 (round 11 answered)”, decisions round 11 q1/q2), PLAN.json revision 17, `decoraciones@v1.r3.behavior.md` and the chosen r3 direction-b Markdown, TSX and HTML. Owner feedback `cddd13f71c873c18` (no import; local group «En este navegador»; staff read-only; Taller accounts only; saved only after server confirmation; listed states; no import states) was already applied in r3 and is preserved here.

| Requirement / criterion | Contract coverage | Consuming tasks |
|---|---|---|
| R8 — saving a composition adds it to the personal library | V1–V3, F1–F3, save states, UI-AC-03–06, 14 | T5.3; visual review T5.5 |
| Search, filter and place into the open project; existing name/occasion/thumbnail/filter controls keep working | V1, F4, UI-AC-01, 10, 17 | T5.3; T5.5 |
| Staff open another account's item read-only; placing adds a copy to their own project | V4, F5, UI-AC-09, 10 | T5.3; T5.5 |
| Legacy `taller3d:biblioteca-propia:v1` entries stay local, never imported; account switch/sign-out never shows previous items | V1 «En este navegador», F7, UI-AC-07, 11, 12 | T5.3; T5.5 |
| Save, list, read-only, empty, loading, retry and error states at phone and desktop | §8, §9, §11 | T5.5 |

PLAN consumers: SP-5 `ui = {contract: decoraciones, version: 1, design_task: T5.1, visual_review_task: T5.5}`. T5.1 copies the owner-approved contract byte for byte to `design/contracts/decoraciones@v1.md` only after independent approval. T5.3 implements the UI (`Biblioteca.tsx`, `biblioteca/BibliotecaPersonal.tsx`, `biblioteca/textos-biblioteca.ts`). T5.2 (storage/API), T5.4 (browser E2E) and T5.6 (audit) own persistence, authorization, deletion rule and isolation proofs; this contract specifies UI only and is not evidence for them.

Read-only product evidence: t12 (HEAD `fb872bce`) and asesor `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/Biblioteca.tsx`, `Taller3D.tsx`. `Biblioteca.tsx` already has «Guardar toda la escena en mi biblioteca», the selected-piece «Guardar en mi biblioteca», «Esta pieza no se puede guardar sola.», name/occasion form, thumbnails, occasion/color/balloon filters, preview, «Añadir a mi escena» and local removal, all on `taller3d:biblioteca-propia:v1`. Sibling drafts `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` supply the shared shell vocabulary.

Impact: **breaking UI** for T5.3 relative to the current local-only library (new account source, three-area arrangement, read-only staff mode, state set). No approved contract is affected.

## 2. Purpose and users

Working question: “Which saved decoration do I add to my current project, and is my save safely in my account?”

- **Owner with Taller access** (Master Designer, Empleado interno, Administrador on their own library): saves the whole scene or the selected piece with a name and occasion, sees «Guardado en mi cuenta» only after server confirmation, finds it after reload and in another browser, searches/filters it and places it into the open project. Only the owner renames, edits or removes their items.
- **Staff viewing another account** (Empleado interno, Administrador): inspects that account's items read-only; owner and «Solo lectura» are visible; «Añadir a mi escena» adds a copy to the staff member's own project; rename/edit/remove are absent.
- **Accounts without Taller access** never reach this surface; access is granted on the account/role surfaces of `cuentas-admin@v1`.

Success: a confirmed save appears in «En mi cuenta», survives reload/other browser, and can be placed; no one sees another account's items after a switch or sign-out; legacy browser entries remain in «En este navegador» untouched.

## 3. Information architecture and hierarchy

Order inside the existing Taller page, top to bottom:

1. Inherited shell: Pictures/Sempertex masthead (ring-and-dot brandmark, «Idioma» ES/EN select, «Mi cuenta» disclosure), H1 «Taller 3D» with the primary page action «Guardar toda la escena en mi biblioteca» (owner context only), route rule «Taller 3D» (current) / «Proyectos».
2. One continuous **workshop panel** (24px radius):
   - Workshop bar: current project identity («Proyecto de ejemplo» · «Mi cuenta») and existing tools Deshacer, Rehacer, Foto realista, Lista de compra (unchanged; out of scope).
   - Area navigator «Zonas de la biblioteca»: Biblioteca / Vista previa / Ficha (Ficha becomes «Guardar» in save views).
   - Three working areas: **Library** (left) → **Preview** (centre) → **Inspector** (right).
   - Bottom bar: «Biblioteca personal · El catálogo global permanece separado.» plus the selected-piece entry «Guardar en mi biblioteca» (owner) or «Solo lectura · <owner>» (staff on foreign account).
3. Page footer (shell).

Hierarchy: primary = the selected item's preview and its single primary action («Añadir a mi escena» or «Guardar»); secondary = library list with source/search/occasion; supporting = metadata, extra filters (Tipo, Color, Globos) behind the native «Filtros» disclosure, owner/rename/edit/remove actions. Progressive disclosure keeps one item expanded at a time; the list stays visible so browsing never replaces the open project.

Library area content order: heading («Mi biblioteca»; «Biblioteca» when viewing another account) → owner selector (staff only) → source switch («En mi cuenta» | «En este navegador»; «En esta cuenta» only for a foreign account) → local-source hint → search → occasion select → «Filtros» disclosure → record list / empty / error / skeleton.

## 4. Design system and visual language

No new palette, font, identity or semantic token. Tokens are the production `globals.css` names; each theme defines them once and maps them onto shadcn roles.

| Product token | Role / use | Light / dark |
|---|---|---|
| `--fondo`, `--texto` | background, foreground | `#faf9fc`/`#0b0c10`, `#1c1425`/`#f4f5f7` |
| `--superficie`, `--superficie-suave`, `--superficie-2` | card/popover, hover row, selected row & muted | `#ffffff`/`#16181f`, `#faf8fd`/`#1c1e26`, `#efe9f8`/`#242733` |
| `--texto-suave`, `--texto-tenue` | supporting text; control edges and input border (≥3:1) | `#6b6178`/`#9aa1ad`, `#766c85`/`#8a91a0` |
| `--acento`, `--acento-hover`, `--sobre-acento` | primary action, focus ring, illustrative balloons | `#6d3fe0`/`#9479ff`, `#5530b8`/`#a58dff`, `#ffffff`/`#120b24` |
| `--borde`, `--borde-suave` | area dividers, row rules, shell rules | `#e3daef`/`#383c48`, `#efe9f8`/`#2a2d38` |
| `--exito`, `--exito-suave` | confirmed save, copy placed | `#1f7a55`/`#78d6a8`, `#dcf5e9`/`#173b31` |
| `--error`, `--error-suave` | list/save/action failure, destructive | `#b23a45`/`#ff979f`, `#ffeaec`/`#43252a` |
| `--aviso`, `--aviso-suave` | unsupported piece | `#8f5f12`/`#f7c46b`, `#fff3d8`/`#3f311c` |
| `--taller-visor`, `--taller-panel`, `--taller-barra` | preview canvas & thumbnails, workshop panel/preview label, workshop bars | `#ebe7f1`/`#1a1722`, `#faf9fc`/`#16131d`, `#ffffff`/`#121018` |
| `--overlay` | dialog backdrop | `rgb(28 20 37/.4)` / `rgb(0 0 0/.6)` |

Typography: Geist Sans (body 15px/1.5), Geist Mono only for the «Sempertex» masthead label. H1 24px/600; inspector H2 20px/600; library H2 18px/600; empty-state H3 16px/600; record name 14px/600; labels 12–14px/600; metadata, hints and status text 12–13px.

Shape and spacing: workshop panel radius 24px; dialogs 32px (24px phone); fields 18px; buttons and native selects pill 999px; record rows 18px; thumbnails 12px. Area padding 24px × 20px; shell gutters 40px (≥1100px), 24px (640–1099px), 20px (<640px). All controls ≥44px tall (fields 46px).

Iconography: lucide-react 18px, `aria-hidden`, always beside visible text (icon-only only for Deshacer/Rehacer, which have accessible names).

Focus: 3px `--acento` outline with 4px offset on every interactive element. Selection uses `aria-pressed`/`aria-current` plus surface and text weight, never colour alone.

Components (`source:id variant state`, import path):

| Component | Variants / states | Import |
|---|---|---|
| shadcn:button | default (primary: Guardar, Añadir a mi escena), outline (secondary/tools), destructive (Quitar) / normal, hover, focus, pressed, disabled, busy | `@/components/ui/button` |
| shadcn:input | text (search, Nombre) / empty, filled, focus, invalid, disabled | `@/components/ui/input` |
| shadcn:skeleton | thumbnail 58×64, text line / loading | `@/components/ui/skeleton` |
| shadcn:dialog (Animate UI / Base UI) | rename, edit / open, validation, pending, closed; foreign read-only explanation | `@/components/ui/dialog` |
| shadcn:alert-dialog (Animate UI / Base UI) | remove / confirm, pending, cancel | `@/components/ui/alert-dialog` |
| kit:motion | expressive, natural, subtle, reduced | `useMotionProfile` from `@kit/motion`; `motion.i` layout marker from `motion/react` |
| custom:zone-nav | Biblioteca / Vista previa / Ficha·Guardar / current | semantic `nav` + buttons, project tokens |
| custom:source-nav | account, browser, foreign-account / pressed, disabled | semantic `nav` + `aria-pressed` buttons |
| custom:library-record | scene, piece / default, hover, selected, disabled-while-saving | `button` with thumbnail, name, «Tipo · Ocasión» |
| custom:preview | scene, piece, placed, blank / loading, error, switching | `section` with label bar and footer |
| custom:inspector | details, save-form, read-only, loading | `aside` |
| custom:status-note | neutral (pending), success, warning, error (+ Reintentar) | `role=status` / `role=alert` |
| custom:account-disclosure | closed, open | native `details/summary` from sibling shell |
| native select / details | Idioma, Propietario, Ocasión, Tipo, Color, Globos, Filtros | native, project-token styled |

The preview art in the mockup is an illustrative SVG, not a thumbnail format; production uses the existing Taller thumbnail/preview rendering.

Motion (direction signature — “spatial docking”), easing `cubic-bezier(.23,1,.32,1)`:

| Element | Movement | expressive / natural / subtle |
|---|---|---|
| Library area | enters from x −20px | 640 / 360 / 160 ms |
| Inspector area | enters from x +24px | same |
| Preview canvas | seats from scaleX .97 | same |
| Preview object | x +25px, rotateY −12° → 0 with slight overshoot | same |
| Record rows | x −12px, stagger | step 65 / 35 / 15 ms |
| Status notes | x +12px | travel duration |
| Zone marker | shared-layout slide | kit profile spring |
| Buttons | hover scale 1.025, press .965 + 1px | 180 / 150 / 100 ms |

Only transform/opacity animate; text is legible throughout. Reduced-motion preference, the «Quieto» profile and `?still=1` remove all transforms/transitions (including the pending spinner) and show the final content. Animations pause when the tab is hidden or the panel is offscreen. No infinite decorative loop.

## 5. Navigation and interaction model

- **Entry:** route `/3d` (Taller 3D). The library is part of the Taller, not a new page. «Guardar toda la escena en mi biblioteca» (header) opens V2; the bottom-bar «Guardar en mi biblioteca» in selected-piece context opens V3. Staff reach V4 by choosing an owner (see Q1).
- **Exit:** «Proyectos» and the account disclosure («Mi cuenta», «Planes», «Cerrar sesión») go to sibling surfaces (`proyectos@v1`, `cuentas-admin@v1`, `planes@v1`). «Cancelar» and «Ver en mi biblioteca» return from a save view to V1.
- **Area navigator:** Biblioteca / Vista previa / Ficha (or Guardar) moves focus to the labelled area and scrolls only if needed (smooth unless reduced). The moving marker shows the current area.
- **Selecting a record** updates preview and inspector; the open project is not changed. In a save view, selecting a record returns to V1 with that record.
- **Source switch** («En mi cuenta» / «En este navegador») replaces the list without route change and clears search and all filters.
- **Save entry** focuses the «Nombre» field; on phones it is scrolled into view first.
- **While saving:** source buttons, record rows, «Cancelar», route links and the page-level save entries are disabled or report «Guardando en mi cuenta…» instead of navigating, so the save target cannot change mid-request.
- **Dialogs** (rename, edit, remove) contain focus, close with Escape/«Cancelar» (not while pending) and return focus to their trigger; after a removal focus goes to the inspector area. Dialogs are suppressed during loading and account switch.
- **Placement:** «Añadir a mi escena» adds the item (structure and its decorations together) to the current scene and moves focus to the preview; the original stays in its library.
- **Sign out / account switch:** previous account's server list, details, thumbnails and preview are removed immediately, before the next account's data loads.

## 6. Flows

**F1 Save the whole scene.** «Guardar toda la escena en mi biblioteca» → V2: preview «La escena entera», inspector «Guardar en mi biblioteca» with Nombre and Ocasión, hint «Disponible desde otros navegadores de tu cuenta.» → «Guardar» → if the trimmed name is empty: validation (F1a) → else pending: inputs and buttons disabled, «Guardando…» / «Guardando en mi cuenta…» → on server confirmation: «Guardado en mi cuenta» + «Ver en mi biblioteca» → V1 lists the new record under «En mi cuenta». On failure → F3.

**F1a Validation.** Empty/whitespace name → input `aria-invalid`, «Escribe un nombre.» below it, focus on the field; editing clears the error.

**F2 Save the selected piece.** With a piece selected, «Guardar en mi biblioteca» → V3: preview «La pieza sola», same form → as F1. If the piece cannot be saved alone: warning «Esta pieza no se puede guardar sola.», form disabled, «Cancelar» available.

**F3 Save failure and retry.** Error «No se pudo guardar. Conservamos el nombre y la ocasión.»; Nombre/Ocasión stay filled and editable; primary reads «Reintentar guardar» → pending → confirmation. A failed save never appears in the account list nor shows a saved label.

**F4 Find and place.** Source → search («Buscar en mi biblioteca») and/or Ocasión and «Filtros» (Tipo, Color, Globos; «Limpiar filtros» when any is set) → choose record → preview + ficha (name, Tipo, Ocasión, Propietario, provenance hint) → «Añadir a mi escena» → «Copia añadida a tu escena.» and preview footer «Copia añadida a tu propio proyecto.». No match → «Sin resultados» / «Cambia la búsqueda o los filtros.» + «Limpiar filtros».

**F5 Staff inspect and place.** Staff selects an owner → heading «Biblioteca», source «En esta cuenta» only, «Solo lectura» on preview label, inspector and bottom bar; Propietario shows the owner; explanation «Solo el propietario puede actualizar o quitar esta decoración. Añadir crea una copia en tu propio proyecto.» → «Añadir a mi escena» adds a copy to the staff member's own project. Rename, edit and remove are absent (not disabled). Choosing «Mi cuenta» in Propietario shows the staff member's own library with normal owner actions.

**F6 Owner metadata and removal.** «Renombrar» → Dialog with Nombre → «Guardar» → pending «Guardando en mi cuenta…» → on confirmation list and ficha update, status «Guardado en mi cuenta», focus back to trigger. «Editar» → same Dialog with Nombre and Ocasión (scope: Q2). «Quitar de mi biblioteca» → AlertDialog naming the item → «Cancelar» keeps it; «Quitar» → «Quitando…» → on confirmation the record leaves the list, status «Quitado de mi biblioteca», focus to inspector. Browser-local items offer only «Quitar de mi biblioteca»; after the same AlertDialog confirmation they leave that browser's list immediately, with no server call and no import. Action failure → «No se pudo completar la acción. La decoración sigue en tu biblioteca.» + «Reintentar».

**F7 Account isolation.** Sign out or switch account → project label «Cambiando cuenta…», list/preview/inspector replaced by skeletons and «La biblioteca anterior ya no se muestra.» → next account's list loads (empty or its own records). Legacy browser storage is neither migrated nor modified. No import action, progress or error exists anywhere.

## 7. View specifications

All views share §3's shell and workshop structure; only the inspector content, preview label and available actions change. ES/EN copy is switched by the inherited «Idioma» select; English strings are in the mockup.

**V1 `library` — Mi biblioteca (owner).** Library: «Mi biblioteca», source «En mi cuenta» (default) | «En este navegador»; in browser source the hint «Solo en este navegador. No se importan a tu cuenta.» Records show thumbnail, name, «Escena|Decoración · Ocasión», chevron. Preview label «Vista previa»; footer «Vista previa · No modifica el proyecto abierto.» (mockup prefixes «de ejemplo»). Inspector «Ficha»: H2 item name; `dl` Tipo / Ocasión / Propietario («Mi cuenta» or «En este navegador»); provenance hint «Guardado en mi cuenta» (cloud icon) or «Solo en este navegador.» (monitor icon); actions in one column: «Añadir a mi escena» (primary), then for account items «Renombrar», «Editar», then «Quitar de mi biblioteca»; note «“Añadir a mi escena” la suma a la que tienes, con su armado: la estructura y sus decoraciones juntas.» Flows F4, F6, F7.

**V2 `save-scene` — Guardar escena.** As V1, area navigator's third item reads «Guardar»; preview label «La escena entera»; inspector «Guardar en mi biblioteca» / «La escena entera.», fields Nombre (prefilled with current scene name) and Ocasión, feedback slot, actions «Guardar» (primary) + «Cancelar». After confirmation the form is replaced by the success note and «Ver en mi biblioteca». Flows F1, F1a, F3.

**V3 `save-piece` — Guardar pieza.** As V2 with «La pieza sola» and the unsupported-piece warning. Flows F2, F3.

**V4 `staff` — Personal · Solo lectura.** Library heading «Biblioteca», «Propietario» select above the source switch, single source «En esta cuenta», no «En este navegador» for foreign accounts. Preview label shows «Solo lectura» with lock icon. Inspector: «Solo lectura» label, item name, metadata with Propietario = owner, explanation text, «Añadir a mi escena» only. Bottom bar: «Solo lectura · <owner>», no save entry; header save entry hidden. Flow F5.

**Dialogs.** D1 Renombrar (Nombre). D2 Editar (Nombre, Ocasión). D3 Quitar de mi biblioteca (AlertDialog: title, item name, «Cancelar», destructive «Quitar»). If a mutation dialog is requested on a foreign item, it shows only «Solo lectura» + «Solo el propietario puede actualizar/quitar esta decoración.» + «Volver», never a mutation form.

Data shown: name, type (Escena / Decoración), occasion (existing taxonomy), owner, provenance, thumbnail. Example data in the mockup is labelled «de ejemplo»; no customer identity, date or marketing copy.

## 8. States

| State | Applies to | What appears | What can be done / recovery |
|---|---|---|---|
| `normal` | all | Confirmed records; ready form in save views | All flows |
| `loading` | all | «Cargando biblioteca…», 3 skeleton rows, blank preview, inspector skeleton; `aria-busy` | Nothing item-specific; no stale record, no dialogs; search/filters disabled |
| `empty` | V1, V4 own | «Tu biblioteca está vacía» / «Guarda la escena o una pieza desde el Taller.» + «Guardar toda la escena»; browser source keeps its own records | Save; switch to «En este navegador». **Rule:** an account collection with zero items shows this empty state (not «Sin resultados»), regardless of how it was reached |
| no results | V1, V4 | «Sin resultados» / «Cambia la búsqueda o los filtros.» + «Limpiar filtros» | Clear search and filters; only when the collection has items but none match |
| `list-error` | account source | Error note «No se pudo cargar tu biblioteca.» + «Reintentar»; preview «Reintenta cargar la biblioteca.»; no records or actions from the failed read | Reintentar; browser source independent |
| `saving` | V2, V3 (and dialogs) | Retained inputs disabled, spinner, «Guardando…», «Guardando en mi cuenta…»; navigation that would change the target disabled | Wait; no saved label |
| `saved` | V2, V3 | Success note «Guardado en mi cuenta» + «Ver en mi biblioteca» | Return to V1 where the new record is listed |
| `save-failed` | V2, V3 | Error note with retained Nombre/Ocasión; primary «Reintentar guardar» | Retry same target; edit values |
| `validation` | V2, V3, D1, D2 | Empty Nombre, `aria-invalid`, «Escribe un nombre.» | Type a name |
| `unsupported` | V3 only | Warning «Esta pieza no se puede guardar sola.»; form and «Guardar» disabled | «Cancelar». N/A to whole-scene save |
| `placed` | V1, V4 | Preview label «Mi escena», added object, footer «Copia añadida a tu propio proyecto.», inspector «Copia añadida a tu escena.» | Continue browsing; original stays listed |
| `action-error` | V1 inspector | «No se pudo completar la acción. La decoración sigue en tu biblioteca.» + «Reintentar» | Retry; item retained; no success claimed |
| `account-switch` | all | «Cambiando cuenta…», skeletons, «La biblioteca anterior ya no se muestra.»; no names, thumbnails, owner or preview of the previous account; no dialogs | Wait for next account's results |
| pending mutation | D1–D3 | «Guardando en mi cuenta…» / «Quitando de mi biblioteca…», buttons disabled, Escape ignored | Wait; on failure → `action-error` |
| permission-denied | foreign items | Mutation controls absent; forced dialog shows read-only explanation | «Volver». Accounts without Taller never reach the surface |

Inapplicable: import, import-progress and import-error (owner round 11 q1: no import). Offline/stale reads use `list-error`/`save-failed`; no separate offline state. Partial data is not shown: a failed account read shows no records.

Transitions: state notes dock in with the status motion; saved status appears only on confirmation; account switch clears before loading; reduced motion shows final states immediately.

## 9. Responsive behavior

Supported from 320px. Same breakpoints for both themes and languages.

| Range | Layout |
|---|---|
| ≥1100px | Shell max-width 1520px, 40px gutters. Workspace grid `280px | minmax(0,1fr) | 264px`, min-height 520px; library right border, inspector left border. Preview canvas min-height 360px, art ≤600px wide. Inspector actions single column, full width. |
| 640–1099px | 24px gutters. Grid `260px | minmax(0,1fr)`; library spans two rows on the left, preview top-right, inspector below preview (top border). Inspector actions and save form two columns (feedback and actions full width). Masthead wraps. Canvas min-height 310px. |
| <640px | 20px gutters. Masthead wraps; header tools full width; H1 and save entry stack. Areas stack in DOM order library → preview → inspector, separated by borders. Area navigator on one row (icons hidden, 12px padding). Records `64px | 1fr | 16px`. Canvas min-height 270px. Bottom-bar button and dialog actions full width; dialogs 24px padding/radius. Save entry scrolls the Nombre field into view and focuses it. |

No horizontal page scroll; text wraps (`overflow-wrap:anywhere`); no fixed-height text container clips copy. Dialogs are `min(580px, 100vw−40px)` (AlertDialog 540px), max-height `100svh−48px`, internal scroll.

## 10. Accessibility targets

Targets WCAG 2.2 AA; to be verified on the rendered implementation.

- Landmarks: `header`, product `nav` «Navegación del producto», `section` «Biblioteca del Taller», `nav` «Zonas de la biblioteca», `nav` «Origen de las decoraciones», labelled library section, preview section and inspector `aside` («Ficha» / «Guardar en mi biblioteca»). The zone item «Guardar» and the form's «Guardar» share a name but sit in different labelled landmarks.
- Keyboard: every control reachable in DOM order; areas are programmatically focusable (`tabindex=-1`) targets of the navigator; Escape closes the account disclosure and dialogs (returning focus).
- State semantics: record and source selection via `aria-pressed`; current area via `aria-current`; loading `aria-busy` + `role=status`; pending/success `role=status`; errors `role=alert`; invalid name `aria-invalid` + `aria-describedby` to the error.
- Contrast: text ≥4.5:1; control edges, focus ring and selection indicators ≥3:1 in both themes (`--texto-tenue` edges, `--acento` focus).
- Target size ≥44×44px; reflow at 320px without horizontal scroll; 200–400% zoom remains a production check.
- Illustrations are `aria-hidden`; visible labels name the preview.
- Reduced motion as in §4.

## 11. Visual acceptance criteria and verification

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | ≥1100px | normal | Library, preview and inspector are three side-by-side columns inside one bordered workshop panel under the unchanged masthead and «Taller 3D»/«Proyectos» route rule. |
| UI-AC-02 | 640–1099px | normal | Library is on the left; preview is top-right; inspector sits below the preview. |
| UI-AC-03 | <640px | normal | Library, preview and inspector stack in that order, the area navigator fits on one row and there is no horizontal page scroll at 320px. |
| UI-AC-04 | all | save-scene / save-piece | Labelled «Nombre» and «Ocasión» fields are visible and the preview label reads «La escena entera» or «La pieza sola». |
| UI-AC-05 | all | saving | «Guardando en mi cuenta…» is visible, the primary button is disabled and no «Guardado en mi cuenta» text appears. |
| UI-AC-06 | all | saved | «Guardado en mi cuenta» and «Ver en mi biblioteca» are visible; after «Ver en mi biblioteca» the new record is in «En mi cuenta». |
| UI-AC-07 | all | save-failed | The error note, the retained name and occasion values and «Reintentar guardar» are visible together. |
| UI-AC-08 | all | empty | «Tu biblioteca está vacía» with «Guardar toda la escena» is shown for the account source; «En este navegador» still lists its own records. |
| UI-AC-09 | all | staff (foreign) | «Solo lectura» and the owner are visible; «Renombrar», «Editar» and «Quitar de mi biblioteca» are absent from the DOM; «Añadir a mi escena» is present. |
| UI-AC-10 | all | placed | «Copia añadida a tu escena.» appears and the original record is still listed and selected. |
| UI-AC-11 | all | account-switch | No previous account's record name, thumbnail, owner or preview is in the DOM; skeletons and «La biblioteca anterior ya no se muestra.» are visible. |
| UI-AC-12 | all | browser source | «En este navegador» shows «Solo en este navegador. No se importan a tu cuenta.» and no import control or state exists. |
| UI-AC-13 | all | loading | Three skeleton rows replace records; the inspector has no item actions. |
| UI-AC-14 | all | validation | Empty «Nombre» shows «Escribe un nombre.» linked by `aria-describedby`, and focus is on the field. |
| UI-AC-15 | all | list-error | «No se pudo cargar tu biblioteca.» with «Reintentar» replaces the list; no record is shown. |
| UI-AC-16 | all | unsupported | «Esta pieza no se puede guardar sola.» is shown and «Guardar» is disabled. |
| UI-AC-17 | all | no results | With a non-matching search, «Sin resultados» and «Limpiar filtros» appear; activating it restores the list. |
| UI-AC-18 | all | remove dialog | «Cancelar» closes the AlertDialog, the item stays selected and focus returns to «Quitar de mi biblioteca». |
| UI-AC-19 | all | rename confirmed | After confirmation the new name appears in the record and the ficha heading, and focus returns to «Renombrar». |
| UI-AC-20 | all | action-error | The error note with «Reintentar» is shown and the item remains listed. |
| UI-AC-21 | all | light/dark, ES/EN | Only §4 tokens and Geist are used; all copy stays inside its column without clipping. |
| UI-AC-22 | all | reduced motion / still | Final content renders immediately with zero running animations; no spinner rotates. |
| UI-AC-23 | ≥1100px | normal, first render | Library enters from the left, inspector from the right and the preview object turns in, completing within ~640ms + stagger (expressive). |
| UI-AC-24 | all | any | Every interactive control is ≥44px tall and shows the 3px accent focus outline on keyboard focus. |

Verification of the canonical HTML built in this finalization (the selected TSX is byte-identical; no source, fallback or HTML patch):

- Build: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build design/decoraciones@v1.r3.dir-b.tsx --out design/decoraciones@v1.html` → 651 KB, 2,135 source files, offline, exit 0. Workspace: installed, built, 96/96 entries.
- Contrast: `python3 <kit>/kit/contrast.py design/decoraciones@v1.html` → 158 pairs in light and dark, all pass, exit 0.
- Audit: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py design/decoraciones@v1.html` → 240 renders (240 planned), 9,804 text measurements, 1,567 focus stops, exit 0. **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems.**
- Behaviour probe (inline Playwright, `?still=1`, 1280px): staff foreign view has 0 Renombrar/Editar/Quitar and 2 «Solo lectura»; staff placement shows the copy note; scene save shows pending with 0 early saved labels, then «Guardado en mi cuenta» and state `saved`; `account-switch` has 0 records and 0 previous names; browser source shows only the no-import hint; no page errors, no network requests.
- Known mockup-only defect (not fixed; see §12): after «Cerrar sesión» → «Continuar · cuenta de ejemplo», switching the inspection state to `normal` shows «Sin resultados» instead of the empty state because the sign-out empties the shared fixture. The rule in §8 (`empty`) governs implementation; reload resets the mockup.

| Artifact | SHA-256 |
|---|---|
| `design/decoraciones@v1.r3.dir-b.tsx` | `5756ac1a85b7cf44d833d8a0d4dce118b349a281ee25251564b0cb24096fd74f` |
| `design/decoraciones@v1.r3.dir-b.html` (exploration) | `5275c3628551b64348b7fee6b7bff475310cc82629c985fd1b32d77c0c098078` |
| `design/decoraciones@v1.html` (canonical rebuild) | `7cd8693d0d4d0eef1dc2d5e07c75893a5dda1267c9991473a980f0b1eac03ae6` |

The mockup's inspection selectors are `view` (library, save-scene, save-piece, staff), `state` (12 states above), `scene` (none, rename, edit, delete) and `theme`. Static fixtures do not prove persistence, cross-browser retrieval, authorization, thumbnail generation or the account-deletion rule; those belong to T5.2, T5.4 and T5.6.

## 12. Open questions and assumptions

Open questions:

- Q1 (owner/Planner): From which existing entry do Empleado interno and Administrador open another account's library — the «Propietario» selector inside the Taller library (as drawn), or from the account administration surface? The selector here is provisional and is not an authorization rule.
- Q2 (owner/Planner): Does «Editar» change only name and occasion (as drawn), or must the owner also be able to replace the saved composition? Until answered, T5.3 implements metadata-only edit and no content replacement.
Confirmed decisions: no import of `taller3d:biblioteca-propia:v1` (round 11 q1); local entries stay in «En este navegador» untouched; new saves belong to the signed-in account; «Guardado» only after server confirmation; staff access to other accounts is read-only and placing creates an owned copy (round 11 q2); only the owner updates or deletes; the library requires Taller access; the global catalogue stays separate; account with saved decorations cannot be deleted, only deactivated (account-management consequence, no control added here).

Assumptions: browser-local removal goes through the same AlertDialog and completes immediately without a server call; a trimmed non-empty name is the only save validation; the existing occasion taxonomy is reused (mockup shows General and Cumpleaños as a subset); color/balloon filter options are the existing ones (mockup subset is illustrative); the mockup's «Continuar · cuenta de ejemplo» and mock scope notices are inspection aids, not product flows.
