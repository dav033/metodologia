---
contract: taller-esenciales
version: 1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
owner: David
created: 2026-10-26
compatibility: breaking
---

# taller-esenciales@v1 — Taller essentials

## 1. Identity and traceability

Planning draft for REQ-021 / M1 / SP-3. Author: delegated Designer. Approval authority: David with the plan; this draft is not an implementation input. The planning flow will copy the approved bytes to `design/contracts/taller-esenciales@v1.md`. This revises the existing v1 planning draft in place; no approved version exists. The adjacent HTML is a static planning mockup, not a production preview or an enabled `design/preview` project.

Source snapshot (2026-10-26): `PLAN.json` revision 1, SHA-256 `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8`; `SPEC.md` SHA-256 `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4`; `PLAN.md` SHA-256 `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3`. The plan is still being discussed. SP-3 binds `ui.contract=taller-esenciales`, `ui.version=1`, design-copy task **T3.1** and independent visual review **T3.7**. UI consumers: **T3.2** tables/scene AI/shopping (V1,V2,V5,V6), **T3.3** Backing (V3), **T3.4** export (V7,D1). **T3.5** builds the browser/Blender harness; **T3.6** runs integration; **T3.8** audits spec/standards. Owner answers to round 9 q1–q4 (2026-10-26T18:53) settle behavior; the contract and SP-3 remain unapproved, and planning focus stays SP-2. V4 is retired; existing view IDs are preserved. SP-3 consumes `session-guard@1` from SP-1 and produces `taller-scene@1` through T3.4.

| Source | Covered behavior | View / flow / criteria |
|---|---|---|
| R9 / US-5 | Add/edit rectangular size and chairs; shopping list follows actual placement; manual and scene AI paths | V1, V2, V5, V6 / F1, F2 / UI-AC-01–06, 18, 28, 31–32 |
| R10 / US-6 | GLB with matching transforms, metre scale and colours, then Blender verification | V7, D1 / F4 / UI-AC-10–14, 21 |
| R11 / US-7 | One Backing group in Taller Fondos y muebles; move seven cards without duplicates, preserve original-name/AI/photo discovery and identities; Shopify `/catalogo` unchanged | V3 / F3 / UI-AC-07–09, 19, 29–30, 33 |

Draft revision / impact record (2026-10-26, owner feedback 18:53; kept here because this brief authorizes no changelog file): draft; revise the same unapproved v1. Compatibility is **breaking relative to the previous draft**: remove provisional V4/Shopify navigation, duplicate-card alternatives, the generic creation entry and pre-creation-form alternative; confirm per-type default creation plus existing inspector, quantities/dimensions without rental prices, the seven-card move and portable Blender LTS verification. Affected consumers: **T3.2** (V1/V2/V5/V6, F1/F2/F5), **T3.3** (V3/F3; remove V4), **T3.4** (V7/D1/F4 copy and feedback retained), **T3.5/T3.6** (confirmed automated real import plus separate owner opening), **T3.7/T3.8** (revised review scope). No accepted implementation exists to establish shipped conformity. Six active views retain their existing layout, tokens and applicable states. No other subplan contract changes; SP-1/2 own access, SP-8 owns translation and SP-4 owns server saves. Required action: owner plan/contract approval, then T3.1 exact copy, T3.2–T3.4 implementation, T3.5/T3.6 verification and T3.7/T3.8 independent review. An approved version is immutable; subsequent changes require v2 and impact analysis.

Read-only product evidence (pictures is the implementation repository; t12 is the compatibility reference, not an additional implementation target):
- `t12` HEAD `fb872bce`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `Taller3D.tsx`, `HojaMovil.tsx`, `EditorConjuntoMesa.tsx`, `FondosYMuebles.tsx`, `ListaEscenografia.tsx`; `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `fondos-escenografia.ts`, `mobiliario-tipos.ts`; `src/lib/catalogo/asignacion-fondos.ts`; `src/app/catalogo/page.tsx`, `src/components/catalogo/Facetas.tsx`.
- `pictures` / `asesor` HEAD `fa101a47`: same table editor and shared UI classes; `ExportarEscenaTaller.tsx`, `exportar-escena-glb.ts`, `exportadores-escena-globos.ts`, `archivo-escena.ts`. The GLB UI/exporter exists here, not in the inspected t12 source. Shared Taller colour tokens match; globals differ elsewhere. Do not assume worktrees contain identical features.
- Table default dimensions and limits below are source values, not new business rules. Mock examples, counts and capacities are explicitly fictitious; runtime counts come from the engine. No mock price is a catalogue fact.

## 2. Purpose and users

External accounts with `taller.usar` (initial Plan 3), employees and administrators build event scenes; they need a discoverable rectangular table, editable seating and reusable Backing. These views require Taller access; Shopify `/catalogo` and its independent `catalogo.ver` access remain outside this subplan. Success: the user can locate a prop, insert it once, see the actual table/chair counts, and start a GLB download without losing scene work. Blender parity is a separately verified export outcome, never inferred from a success toast.

V1 finds the table; V2 adjusts it; V3 finds scene Backing; V5 checks actual materials; V6 requests the same table through existing scene AI; V7 hands the scene to Blender. No account administration, new room editing, Illustrator, module editing or save-project redesign is included.

## 3. Information architecture and hierarchy

Keep the existing workshop shell: title/actions → panel rail → Add panel → scene viewport → selected-piece/IA inspector. One local primary action per panel. The scene and selected object remain visible while dimensions change.

- Add → **Fondos y muebles / Mobiliario** → one card per existing parametric type (Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, Banquete en U), confirmed in round 9 q1=a. Rectangular is explicitly visible and uses the existing model/editor. Each type card inserts its default size from `PARTIDA_MESA`, selects the group and opens the existing inspector; no pre-creation form. The per-type cards replace the generic **Mesa con sillas a medida** creation entry; all eight parametric types remain available. “Imperial” is an existing fixed catalogue piece, not a new parametric type: do not add it to `TIPOS_MESA`.
- Add → **Fondos y muebles / Backing** is a presentation group, not a new data repository. The mock exposes it directly as a category shortcut. Round 9 q3=a confirms that the seven cards move from their previous visual groups into this single Backing group, once each. Other pieces remain in their current visual groups. No duplicated card aliases and no Backing collection/filter in Shopify `/catalogo`. Keep `GrupoCatalogo = "fondo" | "asiento" | "mesa" | "decorado"` and every `ASIGNACION_FONDOS` entry unchanged. Derive Backing display membership from the explicit seven-ID set; do not write `grupo: "backing"`, move repositories or migrate saved scenes for presentation. Keep the catalogue name “Marco hexagonal metálico” for `aro_hexagonal`; “aro hexagonal” remains a discovery alias. Search “Backing” returns the seven distinct canonical entries; original names, AI/photo discovery and repository filters remain compatible. Counters follow the filtered canonical results, not duplicated aliases.
- Inspector: selected name → dimensions in metres → chair count/engine capacity → chair type/distribution → existing material/colour controls → grouped move/rotate/duplicate helper.
- Shopping list: actual quantities and dimensions, then material description; distinguish Mobiliario / Escenografía from store products. Preserve “no es producto de la tienda”; show no rental prices; do not invent purchasability or stock (round 9 q2=a).
- Export remains a header action (compact named action on narrow screens). Put **Descargar modelo GLB · Blender** alongside existing PNG, then one sentence explaining metres and Blender import. No wizard or invented progress percentage.

## 4. Design system and visual language

Reuse `globals.css` tokens and classes `BTN`, `BTN_PRI`, `BTN_ICO`, `RIEL`, `RIEL_ON`, `CHIP`, `TARJETA`, `DATO`, `ROTULO`, `FLOTANTE` from `ui-taller.ts`. No new brand palette. Native controls use the same surface/text tokens. Project tokens take precedence over global desktop font/palette preferences: this product uses Geist Sans/Geist Mono, not JetBrains Mono. Offline mockup uses `system-ui` and `ui-monospace` fallbacks because no external fonts are allowed.

| Semantic token | Light | Dark | Use |
|---|---|---|---|
| `--taller-barra` | #ffffff | #121018 | Header / rail |
| `--taller-panel` | #faf9fc | #16131d | Inspector / Add panel |
| `--taller-visor` | #ebe7f1 | #1a1722 | Scene background |
| `--taller-tarjeta` | #ffffff | #1d1926 | Cards / input surfaces |
| `--taller-boton` | #ffffff | #1b1724 | Secondary controls |
| `--taller-encima` | #f3eefb | #231e2e | Hover / thumbnails |
| `--taller-elegido` | #ece3fb | #2a2140 | Selected chips / rows |
| `--taller-borde` | #ddd3ea | #2d2838 | Existing soft separators |
| `--taller-texto` | #1c1425 | #f2eff7 | Main copy |
| `--taller-texto-2` | #3a3146 | #ddd8e6 | Supporting copy |
| `--taller-medio` | #5a5168 | #a59db5 | Readable secondary labels |
| `--taller-primario` | #6d3fe0 | #7a55ec | Primary button with `--taller-sobre-primario` #ffffff |
| `--taller-resalte` | #6d3fe0 | #8f6ef5 | Focus / selection |
| `--taller-acento` | #5530b8 | #b9a4ff | Accent text |
| `--taller-peligro` | #a8323d | #f08a94 | Errors with text/icon |
| `--taller-valido` | #1a6a4a | #5fd3a0 | Success with text/icon |

Existing soft borders are not sufficient as the only interactive boundary: use `--taller-medio` for input outlines and selected labels, with a text/check indication. No new semantic token is needed. Decorative mock geometry uses source prop colours; these are scene materials, not UI tokens.

Spacing follows existing Tailwind 4 px scale: 8 px control gaps, 12 px card gaps, 16 px section padding, 24 px between groups. Header 56 px, desktop rail 60 px, Add panel up to 340 px, inspector up to 320 px. Radius 10 px buttons/inputs, 12 px cards, 20 px mobile sheet. Body 13–14 px, labels 12 px, headings 16–20 px; amounts use tabular figures. Existing desktop controls at least 36 px high; touch actions 44 px. Focus: 2 px `--taller-resalte` outline with 3 px offset, never clipped. No decorative motion; any sheet transition ≤180 ms with reduced-motion instant equivalent.

## 5. Navigation and interaction model

Keep `/3d`; do not create standalone production routes for V1–V7. V1/V2/V3/V6/V7 are workshop panel states; V5 is the existing shopping dialog D2. V4 has been removed from the contract and mockup following round 9 q3=a: Shopify `/catalogo` is unchanged. The mockup’s “Vista / Estado / Diálogo / Tema” controls and decision-context notes are planning-only and do not ship. All six active views have selectable states for review.

Selection uses real buttons; “Editar mesa” provides a keyboard alternative to clicking/dragging the scene. Adding a table selects it and focuses the inspector heading on narrow screens; desktop announces selection without stealing focus while the user browses. Editing applies valid values after change/blur; transient invalid input stays visible and does not mutate the scene. Preserve undo/redo grouping and object identity. Esc closes export popover/dialog and returns to its invoker. Shopping uses a labelled modal with focus trap; export uses a labelled nonmodal group as today, not a fake ARIA menu. Close by Escape or outside click; Tab follows normal button order.

No drag-only actions. Backing add buttons respect authoritative Taller permission outcomes. Do not start a new empty scene or replace a current scene as a side effect of navigation. Panel navigation preserves current work; persistence ownership stays outside SP-3. The mockup simulates only local mutations and makes no download/network request.

## 6. Flows

**F1 — Add and edit manually (R9).** 1. Open Add / Mobiliario. 2. Activate “Mesa rectangular”. Insert one editable group with current source defaults: 2.40 × 0.90 × 0.75 m; chair defaults remain the engine's current defaults (8 requested in the existing entry), not a second UI rule. 3. Select the new table and open dimensions. 4. Change length/width/height and chair quantity/type/distribution. 5. Engine recomputes geometry/capacity and actual placed chairs. 6. Announce “Mesa actualizada: …; … sillas colocadas”. 7. Open shopping list and see the same actual quantities. Undo restores the previous group and counts.

**F2 — Capacity / validation recovery (R9).** Accept rectangular ranges from `LIMITES_MESA`: length 1–6 m, width 0.40–1.50 m, height 0.40–1.10 m. Existing sliders use 0.05 m steps; numeric input must not silently round a typed invalid value. Integer chairs 0–40 requested, actual capacity from `repartirSillas`; do not use 40 as the physical capacity. Show “Pedidas 12 · Colocadas 8” when the engine fits fewer, with the existing capacity explanation. Shopping/export use placed chairs only. On invalid text, show field error and keep last valid geometry; allow correction or “Restablecer valores”. If resizing reduces capacity, show the result visibly, never report the requested count as placed. Scene AI uses the same validation and counts. Old fixed groups offer the existing “Hacerla editable”; room-generated tables retain their current “ajustar el salón” instruction, not an independent conflicting editor.

**F3 — Find Backing (R11).** Open Add → Fondos y muebles → Backing. Browse/search names and descriptions. The confirmed canonical set contains `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. All seven appear in the mock, with original names and identity. Add a permitted piece by button or existing drag path; select it and announce its name. Return to old search: it remains findable by the same identity. The seven cards leave Fondos y tapetes / Decorado de pie visually; they are not duplicated there. Old-name search, repository filtering, AI/photo discovery and saved-scene identities remain compatible. Cancel/exit returns to the existing scene without adding a second piece. Existing dimensions/material options stay in the selected-piece inspector. Shopify `/catalogo` gets no Backing UI or catalogue behavior change.

Canonical membership / invariants for F3 (all remain `ASIGNACION_FONDOS → escenografia`; qualification is unchanged):

| Canonical ID | Existing name | Existing semantic `GrupoCatalogo` | Previous visual group (cards move to Backing) |
|---|---|---|---|
| `panel_redondo` | Panel redondo | `fondo` (implicit default) | Fondos y tapetes |
| `media_luna` | Media luna | `fondo` (implicit default) | Fondos y tapetes |
| `arcos_chiara` | Arcos chiara | `fondo` (implicit default) | Fondos y tapetes |
| `pedestales` | Pedestales | `decorado` | Decorado de pie |
| `aro_metalico` | Aro metálico | `decorado` | Decorado de pie |
| `aro_hexagonal` | Marco hexagonal metálico | `decorado` | Decorado de pie |
| `arco_metalico` | Arco metálico | `decorado` | Decorado de pie |

**F4 — Export for Blender (R10).** Open Export → GLB. Read “Escena completa · escala en metros”. Export only committed scene geometry, including the existing room, excluding grid, selection outlines, transform handles and editor lights. Do not export pending AI preview as if committed; do not silently omit unsupported pieces. Freeze a coherent snapshot for export, then prepare. Disable duplicate starts while preparing. On success announce **“Descarga GLB iniciada.”**, never “Guardado en tu equipo” or “Verificado en Blender”. On error show safe actionable copy and “Reintentar”, retain scene and allow editing. Keep PNG available as an existing sibling but no PNG redesign is required here. Completion help: “En Blender: Archivo → Importar → glTF 2.0 (.glb/.gltf)”. Product scale/layout/colour parity needs T3.5/T3.6 automated export/import verification and documented owner import; this mockup cannot prove either. The plan check compares world positions/dimensions within 1 mm and base-colour channels within 1/255 in the same colour space, with material/lighting limitations recorded. Round 9 q4=a authorizes the future verification task to provision checksum-verified official portable Blender LTS under `~/.local/opt/blender` without pacman or other system-package changes, record version/executable and run automated real GLB import. The owner also opens the file manually and documents the result; the automated and manual evidence are both required. A missing executable/import failure is blocked or failed evidence, never a pass. This planning/design task does not install Blender or run product verification.

**F5 — Scene AI (US-5).** Open existing IA tab. Example “Añade una mesa rectangular de 2,40 × 0,90 m con 8 sillas Tiffany”. While waiting retain committed scene, mark pending and offer no duplicate submission. Use existing proposal/acceptance behavior; show actual dimensions and placed/requested counts, not a new chat architecture. Applying a valid result updates the same table model and shopping list. On recoverable failure retain prompt and prior scene. Mockup represents a fixture response only; no AI is called.

## 7. View specifications

| ID / mock `view` | Structure / copy / actions | Responsive / states / flow |
|---|---|---|
| V1 `tables` | Add title; Mobiliario selected; search; “Mesa rectangular / A medida · con sillas”; cards for the other seven existing types; primary “Añadir mesa rectangular”; scene; compact selected-piece summary | Desktop three panes, narrow active sheet; S1–S5,S7,S9–S10; F1 |
| V2 `table-editor` | “Mesa rectangular 01”; length, width, tabletop height numeric fields + source ranges; chair requested/placed/capacity, type, distribution; existing cloth/colour controls; actual-count note; “Ver lista de compra” | One inspector column; fields never side-scroll; S1,S2,S3,S4,S5,S6,S7,S8,S9,S10; F1/F2 |
| V3 `backing` | Add → Backing; “Aros, pedestales y paneles”; search; two-column illustrated cards with canonical names, dimensions when known, “Añadir…” accessible names; preserve original-name/AI/photo discovery; no duplicate cards in previous groups | Cards wrap; no stock/price invented; S1–S5,S7,S9,S10; F3 |
| V5 `shopping` / D2 | Dialog title “Lista de compra”; Mobiliario and Escenografía; e.g. 1 × rectangular table (2.40 × 0.90 × 0.75 m), 8 × Tiffany chair, 1 × round panel, 1 × pedestal set; “No son productos de la tienda”; no invented currency total; close to prior scene | Max 640 px modal, nearly full viewport narrow; S1–S5,S7,S9,S10; F1/F2 |
| V6 `ai` | Existing scene IA inspector; one mock conversation; text prompt; “Enviar”; pending response; result “1 mesa rectangular · 8 sillas colocadas”; existing proposal/apply interaction and manual-edit link | Input below conversation, expands above mobile keyboard; S1–S5,S6,S7,S8,S9,S10,S11; F5 |
| V7 `export` / D1 | Workshop with export group open; PNG sibling, primary “Descargar modelo GLB · Blender”; scene name, metre scale, import instruction; prepare/error/started feedback next to trigger | Popover max 320 px, fits viewport; accessible in compact narrow header; S1–S5,S7,S8,S9,S10,S11; F4 |

Visible product copy is Spanish for this draft. Semantic strings are translation-ready; bilingual rollout belongs to the language subplan (R12), not an implicit SP-3 implementation. Backing and GLB retain those names in both locales. No new language switch is introduced. Test translated labels with 40% expansion; only project name may truncate with an accessible full name. The dark/light mock selector represents both existing product themes.

## 8. States

`#state` is a visible native select; only states applicable to the current view are offered. `#view` uses the six active ids above; `#scene` offers `none`, `export`, `shopping`; `#theme` offers `dark`, `light`. All have visible labels. The bridge can set value and dispatch `change`. State options update when the view changes. Dialog state comes from the chosen view/state; exported example data is never downloaded. Mock-only status explicitly says any resulting change is simulated.

| ID / selector | Visible result and enabled recovery | Transition / applicability |
|---|---|---|
| S1 `ready` | Stable content; one clear primary action; actual counts | Initial state for every view |
| S2 `loading` | Stable shell, labelled skeleton/loading message; disable content-dependent add/export; committed scene remains | All; resolve to ready/empty/error; no fabricated percentages |
| S3 `empty` | Context: no search match → “No encontramos piezas” + “Limpiar búsqueda”; no selection → “Selecciona una mesa” + return to Add; empty shopping/scene → “Añade una pieza para continuar” | All; export disabled when scene empty; AI empty is no messages, prompt usable |
| S4 `error` | “No pudimos cargar las piezas”, “No pudimos actualizar la lista” or “No se pudo exportar el GLB”, contextual retry; keep prior valid scene/input | All; Retry → pending/loading → ready; no stack traces or false success |
| S5 `success` | Named piece added / table updated / list current / download initiated; status region, not forced navigation | All; returns to ready without erasing content; export success refers to initiated download only |
| S6 `validation` | Error below affected numeric/prompt field, linked by `aria-describedby`; value retained; last valid scene untouched | V2, V6 only; correction → ready; not applicable to Backing/export/list |
| S7 `disabled` | Non-available action plus adjacent reason (scene/node limit or export not ready); no unreachable enabled fake action | All; condition cleared → ready; no disabled-only tooltip |
| S8 `partial` | V2 fewer chairs fitted, requested and placed explicit; V6 proposed result not yet applied; V7 unresolved pieces → export blocked, “Revisa las piezas antes de exportar” | V2,V6,V7; resolving issue → ready; no silently partial GLB |
| S9 `permission-denied` | “Tu cuenta no tiene acceso a esta herramienta” and “Volver”; hide scene/private data; SP-1/2 owns auth destination | All; no self-upgrade/payment flow |
| S10 `offline` | “Sin conexión”; remote library refresh/AI disabled; existing in-memory scene retained; “Reintentar” checks again | All; local edits, shopping derived from a complete scene and already-loaded export remain available; if assets unavailable block export with reason, never assume server save |
| S11 `pending` | “La IA está preparando una propuesta…” / “Preparando GLB…”; block duplicate submit/export, keep scene read-only only as needed for coherent snapshot | V6,V7 only; completion → success/error; no fake cancel button unless operation supports cancellation |

Partial remote Backing results are not introduced: failed catalogue loading reports an error and keeps previously known complete data visibly stale. `offline` covers unavailable refresh and stale retained data. No separate silent stale-success state. No destructive-confirmation state is needed; these flows do not delete data. Export has no separate permission beyond the existing Taller permission. Active preview state is not eligible for export until resolved. Runtime authorization and entitlements are authoritative, not the mock selectors.

## 9. Responsive behavior

Supported range: 320 px and up; primary review widths 360, 768, 1024, 1440 px plus 320 px reflow. Reuse existing 1024 px workshop cut and low-height landscape rule; 1440 px is an evidence width, not a new feature boundary.

- **320–767 px:** compact wrapping header with Export and list access; 40% scene / remaining active sheet when both fit, minimum scene preview 180 px, independently scrollable panel; tab buttons ≥44 px. Show one active Add/Inspector/IA content pane, preserve selected piece and search across switches. Shopping/export fit `100vw - 24px`. No page-level horizontal scroll, no mandatory drag gestures. At large zoom allow vertical document scrolling so the sheet cannot hide inputs behind a fixed canvas. Project title may shorten; action labels wrap.
- **768–1023 px:** same single-active-sheet model, viewport retains more scene height; Backing cards may use three columns; no squeezed triple-pane desktop layout.
- **≥1024 px:** 56 px header, 60 px rail, 300–340 px Add, flexible scene, 300–320 px inspector. At 1024 px close inactive Add when editing to keep the scene usable; both panels can be open at wider widths. Independent panel scroll; viewport never establishes page overflow.
- **Landscape with width <1024 px and height ≤540 px:** active panel beside preview (about 45%/55%), not below it; header wraps rather than covering content; controls scroll vertically. Fullscreen shopping fits viewport height with body scrolling. At 320 px/zoom, prioritize readable content and document scrolling over forced side-by-side composition.
- Backing uses the same workshop Add panel and sheet as table creation; no separate storefront/facet layout. Cards use content-driven minimum widths; two columns only when labels fit, otherwise one. Preserve logical DOM reading order and natural Spanish/English label growth.

Mockup toolbar is outside the product shell; its height is not part of product geometry. No remote image assets, Google Fonts or runtime APIs are required.

## 10. Accessibility targets

Target WCAG 2.2 AA for changed UI. A design description does not establish conformance. Production needs rendered contrast, keyboard, screen-reader and reflow verification.

- One h1 per surface; headings label panels; visible text labels every field/select. Numeric dimensions include “m”, error/range descriptions and appropriate input mode; chairs integer. Pair colour swatches with named labels, never colour-only selection/error.
- Buttons and native selects support keyboard and visible focus. Selected tabs use explicit selected/pressed semantics, not only background. Native buttons provide add/select paths for every drag operation. Provide a named scene summary outside canvas, including selected table dimensions and actual chairs.
- Status region `role=status` / polite announces one settled update, not every slider frame. Errors `role=alert`, with field `aria-invalid` and descriptions. Do not leak private data in permission-denied state.
- D2 uses native dialog or equivalent labelled modal, traps Tab, supports Escape, returns focus to invoking control. D1 uses a nonmodal labelled group, normal Tab order and focus restoration on Escape. No keyboard trap in canvas. The mock uses equivalent focus behavior, including closing dialogs when switching mock views.
- Normal text ≥4.5:1; large text ≥3:1; meaningful control boundaries, selection and focus ≥3:1. Soft token borders are decoration only; controls get a higher-contrast outline as specified. Disabled controls retain an adjacent readable reason.
- Touch targets 44 px preferred; WCAG target-size minimum 24 CSS px or compliant spacing for compact desktop controls. 200% text/400% zoom reflows without clipped actions at 320 CSS px. No essential information depends on hover, motion, perspective or canvas alone.
- Respect `prefers-reduced-motion`; do not animate mock skeletons. Stable button names; pending state also sets busy semantics. Actual Blender usability and a complete nonvisual 3D-authoring interface are outside this design artifact; text editing, scene summary and changed controls remain in scope.

## 11. Visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | ≥1024 px | ready | V1 has a visible “Mesa rectangular” entry inside Mobiliario. |
| UI-AC-02 | 320–1023 px | ready | Activating Add shows table controls in a readable active sheet without horizontal page scrolling. |
| UI-AC-03 | All | ready | V2 displays separate length, width and tabletop height fields with metre units. |
| UI-AC-04 | All | validation | An out-of-range length shows a linked field error while the scene retains its last valid geometry. |
| UI-AC-05 | All | partial | V2 shows both requested and placed chair counts when they differ. |
| UI-AC-06 | All | success | V5 displays the same placed chair count as V2 after an edit. |
| UI-AC-07 | All | ready | V3 exposes one named Backing display group inside Fondos y muebles. |
| UI-AC-08 | All | ready | V3 lists each of the seven canonical Backing members once within the group. |
| UI-AC-09 | 320–1023 px | empty | V3 shows “Limpiar búsqueda” without horizontal overflow. |
| UI-AC-10 | All | ready | D1 labels the GLB action with Blender and displays metre scale. |
| UI-AC-11 | All | pending | V7 shows “Preparando GLB…” and cannot start another export. |
| UI-AC-12 | All | error | V7 offers retry while leaving the committed scene visible. |
| UI-AC-13 | All | success | V7 says “Descarga GLB iniciada.” without claiming local save or Blender verification. |
| UI-AC-14 | All | empty | V7 disables GLB and explains that the scene needs a piece. |
| UI-AC-15 | 360,768,1024,1440 px | ready | Both themes use the stated shared Taller surface and accent tokens. |
| UI-AC-16 | All | permission-denied | Denied workshop content contains no scene or project details. |
| UI-AC-17 | All | ready | Closing D2 with Escape restores focus to the list trigger. |
| UI-AC-18 | All | ready | V6 exposes a manual-edit path after the table proposal is applied. |
| UI-AC-19 | All | ready | Non-store Backing pieces have no invented price or stock claim. |
| UI-AC-20 | <1024 px, height ≤540 px | ready | Active panel is beside the preview and its controls can scroll vertically. |
| UI-AC-21 | All | partial | Export is blocked with an explicit unresolved-piece reason. |
| UI-AC-22 | All | loading | Loading catalogue content retains the shell and blocks add actions. |
| UI-AC-23 | All | offline | The banner distinguishes offline status from retained local scene availability. |
| UI-AC-24 | All | ready | Keyboard focus is visible on every changed control. |
| UI-AC-25 | All | ready | The HTML exposes labelled native selects with ids view, state, scene and theme. |
| UI-AC-26 | 320 px / 400% zoom equivalent | ready | Dialog content and primary actions reflow without page-level horizontal scrolling. |
| UI-AC-27 | All | disabled | Every disabled primary action has an adjacent visible explanation. |
| UI-AC-28 | All | ready | Undo after a table edit restores the preceding dimensions and placed chair count in the inspector and shopping list. |
| UI-AC-29 | All | ready | Searching “Backing” in V3 displays the seven canonical cards and a matching filtered result count. |
| UI-AC-30 | All | ready | The mockup has six active views and no Shopify Backing view or catalogue handoff. |
| UI-AC-31 | All | ready | Activating a table-type card inserts its default-sized group and opens the existing inspector without an intermediate form. |
| UI-AC-32 | All | ready | V5 shows furniture quantities and dimensions without rental prices. |
| UI-AC-33 | All | ready | The seven Backing cards do not appear in Fondos y tapetes or Decorado de pie. |

Round 9 q1–q4 settle these behaviors; the contract itself still requires owner approval. The seven cards move into Backing and leave their former visual groups, which retain their other pieces. Original-name search remains; no duplicate card aliases are created. Identity, `GrupoCatalogo`, `ASIGNACION_FONDOS`, AI/photo compatibility and absence of the seven cards from former groups require source/functional checks in T3.3/T3.8; a rendered grouping cannot prove them.

Engine/layout/scale/colour parity and original-name/AI/photo discovery need functional tests plus the documented Blender import; screenshot review cannot accept R9–R11 alone. HTML renders schematic geometry and simulates interactions; it does not produce a GLB, quote, actual catalogue count or live AI response.

## 12. Open questions and assumptions

### Open questions

None. No genuinely new unresolved owner question was discovered against this SP-3 snapshot. Plan approval and approval of this contract remain pending; behavior answers do not approve the draft or move planning focus from SP-2.

### Resolved owner decisions — round 9, 2026-10-26T18:53

- **Q1 resolved — q1=a:** one card per existing parametric table type; add its source default size, select it and edit in the existing inspector. No pre-creation form.
- **Q2 resolved — q2=a:** shopping lists show actual quantities and dimensions, without rental prices.
- **Q3 resolved — q3=a:** the seven canonical Backing cards move from their old visual groups to one group in Taller Fondos y muebles, without duplicated card aliases. Shopify `/catalogo` remains unchanged; canonical IDs, semantic `GrupoCatalogo`, `ASIGNACION_FONDOS`, original-name search and AI/photo discovery remain stable. SPEC R11 and SP-3 now agree; V4 is removed.
- **Q4 resolved — q4=a:** official checksum-verified portable Blender LTS under `~/.local/opt/blender`, no pacman; automated real import plus the owner’s documented manual opening. Setup and evidence belong to the future implementation/verification tasks, not this static design revision.

### Confirmed boundaries and explicit assumptions

- Confirmed: never-cut R9/R10/R11; GLB, not a new Blender format; scene layout/sizes/colours and metre scale; Backing grouping with preserved canonical identities; existing app styling; no new 3D-room work. Source table limits and existing editable-group behavior are reused.
- Owner-confirmed behavior: one creation card per type including rectangular and no rental prices. Design details awaiting plan/contract approval: native numeric companions for dimensions, visible requested-versus-placed capacity feedback and captioned GLB import help. These do not claim that the current UI already behaves this way.
- The retired V4 is not a destination, mock selector or implementation requirement. View IDs V1–V3/V5–V7 remain stable for unaffected traceability. SP-3 must implement the settled behavior after approval; no obsolete catalogue or pricing alternative remains.
- SP-3 task bindings are T3.1–T3.8 as listed in section 1; all remain draft until plan approval. No tasks from other subplans are silently reassigned.
- Local export requires all relevant assets already loaded; offline does not guarantee that. Permissions come from SP-1/2, stored-project conflict behavior from persistence, language strings from language work. No simulated UI success implies those integrations passed.
- Mock fixtures use a celebration scene named “Cumpleaños · lavanda”, source table default 2.40 × 0.90 × 0.75 m and 8 illustrative placed Tiffany chairs. The mock capacity is labelled example and is not an alternative perimeter algorithm. No network, paid provider, actual download, production write, repository change or extra bitácora output is authorized here.

### Previous draft verification record (2026-10-26; retained evidence, not a rerun of this revision)

Historical report from the prior draft. Its undo claim is superseded: current interaction testing exposed duplicate change registration during input replacement, now corrected in this mockup. The current revision evidence below governs handoff.

Local Chromium via the existing Playwright dependency: 63 view/state combinations × 6 viewports × 2 themes = 756 layout checks; no document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. Ten core exercised interaction checks passed: add/select table, valid dimension update, invalid dimension retains last geometry, capacity warning, shopping uses placed chairs, Escape focus restoration, export pending blocks duplicate, honest simulated completion, AI empty-prompt validation and apply proposal. No JavaScript page errors. Representative desktop dark, mobile editor and tablet light catalogue were visually inspected. Sampled token contrast: primary white text 4.84:1 dark / 6.11:1 light; secondary labels 6.63:1 / 7.47:1; focus against panel 4.99:1 / 5.82:1. Additional final checks passed: undo/redo restored 2.40 m / 3.00 m, the seven canonical Backing cards were present, add-piece feedback and hexagonal search worked, export Escape restored focus, the shopping dialog trapped/returned focus, and the actual inline mockup bridge drove view/state/theme. No HTTP requests were made. These are scoped mockup checks, not a full accessibility audit or product/Blender acceptance. Other table-type cards represent existing-editor handoffs with explicit simulation feedback; full non-rectangular editing and real 3D geometry are not implemented by this static artifact.


### Previous revision verification (2026-10-26; before owner answers)

- Historical run: re-read then-current SPEC draft behavior, open round 9 q1–q4, PLAN SP-3/T3.1–T3.8 and both supplied repositories read-only. Source SHA-256 values above remained unchanged through handoff. No repository, SPEC, PLAN, changelog or project preview was edited.
- Static checks passed: all twelve numbered sections, unique visual criteria, required labelled native selectors, inline JavaScript syntax and no external resource references. The adjacent artifact remains self-contained with CSP blocking network access.
- Final Chromium/Playwright matrix passed: 63 view/state combinations × 6 viewports × 2 themes = 756 layout checks, with no horizontal document/dialog overflow, clipped horizontal controls, JavaScript errors or HTTP requests. Width/height fixtures: 320×800, 360×800, 768×1024, 1024×850, 1440×980, 844×390.
- 27 interaction assertions passed for table insertion/selection, valid and invalid dimensions, last-valid scene retention, undo/redo, requested/placed capacity, shopping counts, Escape/focus restoration, all seven canonical Backing identities and their original semantic/repository metadata, Backing/name/hexagonal-alias search, matching counters, add feedback, conditional V4 label, export pending/simulated completion, AI validation/apply and the actual inline plan bridge. Fixture metadata checks do not prove production repository compatibility.
- 24 final dialog checks across the same widths/themes passed for export and shopping; shopping explicitly cycles Tab and Shift+Tab within the modal, and both dismiss with Escape. This revision fixed duplicate input-change history entries and added an explicit modal Tab cycle after the verification exposed them.
- Visually inspected in-memory Chromium captures: desktop dark Backing at 1440×980 and full mobile light table/capacity state at 360×900. No screenshot or extra preview file was written. Existing tokens and breakpoints remain unchanged.
- These checks cover the static mockup only. Real scene geometry, paid-provider parity, downloadable GLB validity, Blender import and production accessibility conformance remain for T3.2–T3.8 after owner approval. No Blender was installed or invoked.

### Current revision verification — owner-answer reconciliation (2026-10-26)

- Read the updated SPEC, PLAN.md and PLAN.json SP-3/T3.1–T3.8 plus the supplied repositories read-only; the source hashes recorded in section 1 match at handoff. Shared table-default, assignment and Taller-class files match between t12 and pictures. Only the two named design artifacts and the required delegation RESULT.json were written; no repository, SPEC, PLAN, changelog or project-preview edits, commits, launches or Blender installation.
- Static checks passed: twelve numbered sections, 33 unique acceptance criteria, `status: draft`, four visibly labelled native selectors, inline JavaScript parsed by Node `vm.Script`, no external resource references and no obsolete catalogue route or pending Q1–Q4 mock branch. CSP continues to prohibit network requests.
- Headless Chromium using the repository’s existing Playwright dependency: **55 applicable view/state combinations × 6 viewports × 2 themes = 660 layout checks**, plus **144 export/shopping dialog layout checks**. No document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. All six active view ids and state selectors were driven through native `change` events, matching the bridge integration interface.
- **34 interaction assertion groups passed**: all eight type cards use their source defaults and open the inspector without an intermediate form; valid/invalid dimensions, last-valid geometry, undo/redo, requested/placed capacity, actual shopping counts/dimensions without prices, seven unique canonical Backing cards with unchanged semantic/repository fixture metadata, original-name and hexagonal-alias discovery, matching Backing results, add feedback, pending export duplicate prevention, honest simulated completion, Escape/focus return and AI validation/application. An initial test incorrectly required every original-name query to return exactly one result; “Arco metálico” also matches “Marco hexagonal metálico” under the preserved substring search. Corrected the check to require the original canonical card once, without changing the established search behavior; the focused interaction run passed. Fixture metadata/discovery does not prove production AI/photo or saved-scene compatibility.
- **24 keyboard checks passed** across the same viewport/theme pairs: shopping Tab/Shift+Tab cycles within the modal and Escape returns focus; export Escape returns focus. Final interaction run observed zero JavaScript page errors and zero HTTP requests.
- Visually inspected in-memory Chromium captures: 1440×980 dark Backing and 360×900 full-page light table/capacity state. No screenshot or extra preview file was written. Tokens, responsive boundaries, rectangular illustration and unaffected flows remain intact; other type cards now demonstrate their source-default inspector handoff with schematic type artwork.
- Earlier verification records include the removed V4 and are historical only. This revision validates a static planning artifact: production engine geometry, deterministic AI-tool parity, saved-scene/AI/photo compatibility, actual GLB validity, automated Blender import, owner manual opening and full accessibility conformance remain for the planned implementation/verification cycle after owner approval.
