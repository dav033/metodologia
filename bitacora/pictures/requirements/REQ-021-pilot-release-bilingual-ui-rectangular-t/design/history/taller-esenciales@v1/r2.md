---
contract: taller-esenciales
version: 1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
owner: David
created: 2026-10-26
compatibility: undetermined
---

# taller-esenciales@v1 — Taller essentials

## 1. Identity and traceability

Planning draft for REQ-021 / M1 / SP-3. Author: delegated Designer. Approval authority: David with the plan; this draft is not an implementation input. The planning flow will copy the approved bytes to `design/contracts/taller-esenciales@v1.md`. This revises the existing v1 planning draft in place; no approved version exists. The adjacent HTML is a static planning mockup, not a production preview or an enabled `design/preview` project.

Source snapshot (2026-10-26): `PLAN.json` revision 1, SHA-256 `1b47820ae156e298b94ea01c322bcd26b780c2310c6d9357caad4a0796d3dd38`; `SPEC.md` SHA-256 `fafa1d7e372305f80cf2ecae420c661145c6cf569a9e6d7967f7f3a3c469aa73`; `PLAN.md` SHA-256 `77260acb94eb20a81d159a7beec889012ed58bdbae3ef512d1b4fa44dcfac112`. The plan is still being discussed. SP-3 binds `ui.contract=taller-esenciales`, `ui.version=1`, design-copy task **T3.1** and independent visual review **T3.7**. UI consumers: **T3.2** tables/scene AI/shopping (V1,V2,V5,V6), **T3.3** Backing (V3, conditional V4), **T3.4** export (V7,D1). **T3.5** builds the browser/Blender harness; **T3.6** runs integration; **T3.8** audits spec/standards. Round 9 q1–q4 are open; task descriptions are proposed, not owner decisions. SP-3 consumes `session-guard@1` from SP-1 and produces `taller-scene@1` through T3.4.

| Source | Covered behavior | View / flow / criteria |
|---|---|---|
| R9 / US-5 | Add/edit rectangular size and chairs; shopping list follows actual placement; manual and scene AI paths | V1, V2, V5, V6 / F1, F2 / UI-AC-01–06, 18, 28 |
| R10 / US-6 | GLB with matching transforms, metre scale and colours, then Blender verification | V7, D1 / F4 / UI-AC-10–14, 21 |
| R11 / US-7 | One Backing category in Taller and catalogue; preserve old discovery paths and identities | V3, conditional V4 / F3 / UI-AC-07–09, 19, 29–30 |

Draft revision / impact record (2026-10-26, owner feedback 17:26; kept here because this brief authorizes no changelog file): draft; same SP-3 contract and seven views; compatibility **undetermined** against shipped UI because no accepted implementation snapshot exists. Revision changes: explicitly separate the proposed table cards/pricing/Backing grouping and Blender acquisition from confirmed requirements; preserve semantic groups and repository assignments; make V4 conditional. Per-type table cards remain proposed q1=a. No unrelated visual tokens, layout rules or existing states change. Affected views V1–V7, D1–D2. Existing editor/export patterns are retained. No other subplan contract is changed. SP-1/2 provide permission/session outcomes; language work owns translated strings; project persistence owns server saves. Compared with the previous unapproved draft, these clarify pending choices; a choice that changes creation, pricing or category location requires adapting the named consumers before approval. Required action: owner approval including round 9 decisions, then T3.1 exact copy, T3.2–T3.4 implementation, T3.6 integration and T3.7 independent rendered review. An approved version is immutable; subsequent changes require v2 and impact analysis.

Read-only product evidence (pictures is the implementation repository; t12 is the compatibility reference, not an additional implementation target):
- `t12` HEAD `fb872bce`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `Taller3D.tsx`, `HojaMovil.tsx`, `EditorConjuntoMesa.tsx`, `FondosYMuebles.tsx`, `ListaEscenografia.tsx`; `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `fondos-escenografia.ts`, `mobiliario-tipos.ts`; `src/lib/catalogo/asignacion-fondos.ts`; `src/app/catalogo/page.tsx`, `src/components/catalogo/Facetas.tsx`.
- `pictures` / `asesor` HEAD `fa101a47`: same table editor and shared UI classes; `ExportarEscenaTaller.tsx`, `exportar-escena-glb.ts`, `exportadores-escena-globos.ts`, `archivo-escena.ts`. The GLB UI/exporter exists here, not in the inspected t12 source. Shared Taller colour tokens match; globals differ elsewhere. Do not assume worktrees contain identical features.
- Table default dimensions and limits below are source values, not new business rules. Mock examples, counts and capacities are explicitly fictitious; runtime counts come from the engine. No mock price is a catalogue fact.

## 2. Purpose and users

External accounts with `taller.usar` (initial Plan 3), employees and administrators build event scenes; they need a discoverable rectangular table, editable seating and reusable Backing. Catalogue access follows `catalogo.ver`, independent of Taller access. A catalogue-only user may inspect permitted catalogue content but cannot add it to Taller. Success: the user can locate a prop, insert it once, see the actual table/chair counts, and start a GLB download without losing scene work. Blender parity is a separately verified export outcome, never inferred from a success toast.

V1 finds the table; V2 adjusts it; V3 finds scene Backing; V4 illustrates catalogue Backing only if Q3 selects that surface; V5 checks actual materials; V6 requests the same table through existing scene AI; V7 hands the scene to Blender. No account administration, new room editing, Illustrator, module editing or save-project redesign is included.

## 3. Information architecture and hierarchy

Keep the existing workshop shell: title/actions → panel rail → Add panel → scene viewport → selected-piece/IA inspector. One local primary action per panel. The scene and selected object remain visible while dimensions change.

- Add → **Fondos y muebles / Mobiliario** → one card per existing parametric type (Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, Banquete en U), as proposed in round 9 q1=a. Rectangular is explicitly visible and uses the existing model/editor. Retain the generic **Mesa con sillas a medida** entry during transition with its existing round-table behavior; no type is removed. “Imperial” is an existing fixed catalogue piece, not a new parametric type: do not add it to `TIPOS_MESA`. If David chooses q1=b, revise this draft to specify the pre-creation form before approval.
- Add → **Fondos y muebles / Backing** is a presentation group, not a new data repository. The mock exposes it directly as a category shortcut. Round 9 q3 decides whether the seven cards leave their previous visual groups (q3=a, recommended) or remain there too as aliases (q3=b), or another list/location is chosen (q3=c). Neither choice is approved. The mock’s “Grupos actuales · referencia” explains their current locations; it does not claim alias retention has been approved. Keep `GrupoCatalogo = "fondo" | "asiento" | "mesa" | "decorado"` and every `ASIGNACION_FONDOS` entry unchanged. Derive Backing display membership from the explicit seven-ID set; do not write `grupo: "backing"`, move repositories or migrate saved scenes for presentation. Keep the catalogue name “Marco hexagonal metálico” for `aro_hexagonal`; “aro hexagonal” remains a discovery alias. Search “Backing” returns the seven distinct canonical entries; original names, AI/photo discovery and repository filters remain compatible. Counters follow the filtered canonical results, not duplicated aliases.
- Inspector: selected name → dimensions in metres → chair count/engine capacity → chair type/distribution → existing material/colour controls → grouped move/rotate/duplicate helper.
- Shopping list: actual quantities, then material description; distinguish Mobiliario / Escenografía from store products. Preserve “no es producto de la tienda”; do not invent purchasability, prices or stock.
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

Keep `/3d` and `/catalogo`; do not create standalone production routes for V1–V7. V1/V2/V3/V6/V7 are workshop panel states. V5 is the existing shopping dialog D2. V4 is a provisional catalogue category alternative: round 9 q3 currently proposes only the Taller collection, while the SP-3 outcome still says “catalogue and Taller”; Q3 must settle that mismatch. The mockup's “Vista / Estado / Diálogo / Tema” controls and pending-decision notes are planning-only and do not ship. V4 is retained to compare the previous draft with the outstanding Q3 choice; it is excluded from the proposed T3.3 implementation unless expressly selected. All seven views still have selectable states for review.

Selection uses real buttons; “Editar mesa” provides a keyboard alternative to clicking/dragging the scene. Adding a table selects it and focuses the inspector heading on narrow screens; desktop announces selection without stealing focus while the user browses. Editing applies valid values after change/blur; transient invalid input stays visible and does not mutate the scene. Preserve undo/redo grouping and object identity. Esc closes export popover/dialog and returns to its invoker. Shopping uses a labelled modal with focus trap; export uses a labelled nonmodal group as today, not a fake ARIA menu. Close by Escape or outside click; Tab follows normal button order.

No drag-only actions. Backing add buttons and catalogue-to-Taller handoff respect permission server outcomes. Do not start a new empty scene or replace a current scene as a side effect of navigation. A catalogue handoff preserves current work; persistence ownership stays outside SP-3. The mockup simulates only local mutations and makes no download/network request.

## 6. Flows

**F1 — Add and edit manually (R9).** 1. Open Add / Mobiliario. 2. Activate “Mesa rectangular”. Insert one editable group with current source defaults: 2.40 × 0.90 × 0.75 m; chair defaults remain the engine's current defaults (8 requested in the existing entry), not a second UI rule. 3. Select the new table and open dimensions. 4. Change length/width/height and chair quantity/type/distribution. 5. Engine recomputes geometry/capacity and actual placed chairs. 6. Announce “Mesa actualizada: …; … sillas colocadas”. 7. Open shopping list and see the same actual quantities. Undo restores the previous group and counts.

**F2 — Capacity / validation recovery (R9).** Accept rectangular ranges from `LIMITES_MESA`: length 1–6 m, width 0.40–1.50 m, height 0.40–1.10 m. Existing sliders use 0.05 m steps; numeric input must not silently round a typed invalid value. Integer chairs 0–40 requested, actual capacity from `repartirSillas`; do not use 40 as the physical capacity. Show “Pedidas 12 · Colocadas 8” when the engine fits fewer, with the existing capacity explanation. Shopping/export use placed chairs only. On invalid text, show field error and keep last valid geometry; allow correction or “Restablecer valores”. If resizing reduces capacity, show the result visibly, never report the requested count as placed. Scene AI uses the same validation and counts. Old fixed groups offer the existing “Hacerla editable”; room-generated tables retain their current “ajustar el salón” instruction, not an independent conflicting editor.

**F3 — Find Backing (R11).** Open Backing in Add; use the separate catalogue route only if Q3 selects V4. Browse/search names and descriptions. The proposed canonical set contains `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. All seven appear in the mock, with original names and identity. Add a permitted piece by button or existing drag path; select it and announce its name. Return to old search: it remains findable by the same identity. Whether the old visual groups retain the cards is pending round 9 q3; old-name search and canonical identities remain in either option. Cancel/exit returns to the existing scene without adding a second piece. Existing dimensions/material options stay in the selected-piece inspector. Backing membership and category surface require Q3 approval; preserve identity compatibility regardless of grouping.

Canonical membership / invariants for F3 (all remain `ASIGNACION_FONDOS → escenografia`; qualification is unchanged):

| Canonical ID | Existing name | Existing semantic `GrupoCatalogo` | Current visual group |
|---|---|---|---|
| `panel_redondo` | Panel redondo | `fondo` (implicit default) | Fondos y tapetes |
| `media_luna` | Media luna | `fondo` (implicit default) | Fondos y tapetes |
| `arcos_chiara` | Arcos chiara | `fondo` (implicit default) | Fondos y tapetes |
| `pedestales` | Pedestales | `decorado` | Decorado de pie |
| `aro_metalico` | Aro metálico | `decorado` | Decorado de pie |
| `aro_hexagonal` | Marco hexagonal metálico | `decorado` | Decorado de pie |
| `arco_metalico` | Arco metálico | `decorado` | Decorado de pie |

**F4 — Export for Blender (R10).** Open Export → GLB. Read “Escena completa · escala en metros”. Export only committed scene geometry, including the existing room, excluding grid, selection outlines, transform handles and editor lights. Do not export pending AI preview as if committed; do not silently omit unsupported pieces. Freeze a coherent snapshot for export, then prepare. Disable duplicate starts while preparing. On success announce **“Descarga GLB iniciada.”**, never “Guardado en tu equipo” or “Verificado en Blender”. On error show safe actionable copy and “Reintentar”, retain scene and allow editing. Keep PNG available as an existing sibling but no PNG redesign is required here. Completion help: “En Blender: Archivo → Importar → glTF 2.0 (.glb/.gltf)”. Product scale/layout/colour parity needs T3.5/T3.6 automated export/import verification and documented owner import; this mockup cannot prove either. The proposed check compares world positions/dimensions within 1 mm and base-colour channels within 1/255 in the same colour space, with material/lighting limitations recorded. Portable Blender acquisition versus owner-only import is pending round 9 q4; this design neither installs software nor grants permission.

**F5 — Scene AI (US-5).** Open existing IA tab. Example “Añade una mesa rectangular de 2,40 × 0,90 m con 8 sillas Tiffany”. While waiting retain committed scene, mark pending and offer no duplicate submission. Use existing proposal/acceptance behavior; show actual dimensions and placed/requested counts, not a new chat architecture. Applying a valid result updates the same table model and shopping list. On recoverable failure retain prompt and prior scene. Mockup represents a fixture response only; no AI is called.

## 7. View specifications

| ID / mock `view` | Structure / copy / actions | Responsive / states / flow |
|---|---|---|
| V1 `tables` | Add title; Mobiliario selected; search; “Mesa rectangular / A medida · con sillas”; cards for other existing types plus generic-table route; primary “Añadir mesa rectangular”; scene; compact selected-piece summary | Desktop three panes, narrow active sheet; S1–S5,S7,S9–S10; F1 |
| V2 `table-editor` | “Mesa rectangular 01”; length, width, tabletop height numeric fields + source ranges; chair requested/placed/capacity, type, distribution; existing cloth/colour controls; actual-count note; “Ver lista de compra” | One inspector column; fields never side-scroll; S1,S2,S3,S4,S5,S6,S7,S8,S9,S10; F1/F2 |
| V3 `backing` | Add → Backing; “Aros, pedestales y paneles”; search; two-column illustrated cards with canonical names, dimensions when known, “Añadir…” accessible names; preserve original-name discovery (visual aliases pending Q3) | Cards wrap; no stock/price invented; S1–S5,S7,S9,S10; F3 |
| V4 `catalogue` — conditional Q3 alternative | Catalogue shell; category filter Backing; heading/result count; all seven proposed props and provenance; “Abrir en Taller” only with permission; “Pieza de escenografía · sin precio de tienda” for non-store props | Facets at left ≥1024, disclosure above below 1024; S1–S5,S7,S9,S10; F3; Q3 provisional |
| V5 `shopping` / D2 | Dialog title “Lista de compra”; Mobiliario and Escenografía; e.g. 1 × rectangular table (2.40 × 0.90 m), 8 × Tiffany chair, 1 × round panel, 1 × pedestal set; “No son productos de la tienda”; no invented currency total; close to prior scene | Max 640 px modal, nearly full viewport narrow; S1–S5,S7,S9,S10; F1/F2 |
| V6 `ai` | Existing scene IA inspector; one mock conversation; text prompt; “Enviar”; pending response; result “1 mesa rectangular · 8 sillas colocadas”; existing proposal/apply interaction and manual-edit link | Input below conversation, expands above mobile keyboard; S1–S5,S6,S7,S8,S9,S10,S11; F5 |
| V7 `export` / D1 | Workshop with export group open; PNG sibling, primary “Descargar modelo GLB · Blender”; scene name, metre scale, import instruction; prepare/error/started feedback next to trigger | Popover max 320 px, fits viewport; accessible in compact narrow header; S1–S5,S7,S8,S9,S10,S11; F4 |

Visible product copy is Spanish for this draft. Semantic strings are translation-ready; bilingual rollout belongs to the language subplan (R12), not an implicit SP-3 implementation. Backing and GLB retain those names in both locales. No new language switch is introduced. Test translated labels with 40% expansion; only project name may truncate with an accessible full name. The dark/light mock selector represents both existing product themes.

## 8. States

`#state` is a visible native select; only states applicable to the current view are offered. `#view` uses the seven ids above; `#scene` offers `none`, `export`, `shopping`; `#theme` offers `dark`, `light`. All have visible labels. The bridge can set value and dispatch `change`. State options update when the view changes. Dialog state comes from the chosen view/state; exported example data is never downloaded. Mock-only status explicitly says any resulting change is simulated.

| ID / selector | Visible result and enabled recovery | Transition / applicability |
|---|---|---|
| S1 `ready` | Stable content; one clear primary action; actual counts | Initial state for every view |
| S2 `loading` | Stable shell, labelled skeleton/loading message; disable content-dependent add/export; committed scene remains | All; resolve to ready/empty/error; no fabricated percentages |
| S3 `empty` | Context: no search match → “No encontramos piezas” + “Limpiar búsqueda”; no selection → “Selecciona una mesa” + return to Add; empty shopping/scene → “Añade una pieza para continuar” | All; export disabled when scene empty; AI empty is no messages, prompt usable |
| S4 `error` | “No pudimos cargar las piezas”, “No pudimos actualizar la lista” or “No se pudo exportar el GLB”, contextual retry; keep prior valid scene/input | All; Retry → pending/loading → ready; no stack traces or false success |
| S5 `success` | Named piece added / table updated / list current / download initiated; status region, not forced navigation | All; returns to ready without erasing content; export success refers to initiated download only |
| S6 `validation` | Error below affected numeric/prompt field, linked by `aria-describedby`; value retained; last valid scene untouched | V2, V6 only; correction → ready; not applicable to read-only catalogue/export/list |
| S7 `disabled` | Non-available action plus adjacent reason (scene/node limit or permissions on catalogue handoff); no unreachable enabled fake action | All; condition cleared → ready; no disabled-only tooltip |
| S8 `partial` | V2 fewer chairs fitted, requested and placed explicit; V6 proposed result not yet applied; V7 unresolved pieces → export blocked, “Revisa las piezas antes de exportar” | V2,V6,V7; resolving issue → ready; no silently partial GLB |
| S9 `permission-denied` | “Tu cuenta no tiene acceso a esta herramienta” and “Volver”; hide scene/private data; SP-1/2 owns auth destination | All; catalogue add denial does not erase catalogue view if `catalogo.ver` still allowed; no self-upgrade/payment flow |
| S10 `offline` | “Sin conexión”; remote catalogue refresh/AI disabled; existing in-memory scene retained; “Reintentar” checks again | All; local edits, shopping derived from a complete scene and already-loaded export remain available; if assets unavailable block export with reason, never assume server save |
| S11 `pending` | “La IA está preparando una propuesta…” / “Preparando GLB…”; block duplicate submit/export, keep scene read-only only as needed for coherent snapshot | V6,V7 only; completion → success/error; no fake cancel button unless operation supports cancellation |

Partial remote Backing results are not introduced: failed catalogue loading reports an error and keeps previously known complete data visibly stale. `offline` covers unavailable refresh and stale retained data. No separate silent stale-success state. No destructive-confirmation state is needed; these flows do not delete data. Export has no separate permission beyond the existing Taller permission. Active preview state is not eligible for export until resolved. Runtime authorization and entitlements are authoritative, not the mock selectors.

## 9. Responsive behavior

Supported range: 320 px and up; primary review widths 360, 768, 1024, 1440 px plus 320 px reflow. Reuse existing 1024 px workshop cut and low-height landscape rule; 1440 px is an evidence width, not a new feature boundary.

- **320–767 px:** compact wrapping header with Export and list access; 40% scene / remaining active sheet when both fit, minimum scene preview 180 px, independently scrollable panel; tab buttons ≥44 px. Show one active Add/Inspector/IA content pane, preserve selected piece and search across switches. Shopping/export fit `100vw - 24px`. No page-level horizontal scroll, no mandatory drag gestures. At large zoom allow vertical document scrolling so the sheet cannot hide inputs behind a fixed canvas. Project title may shorten; action labels wrap.
- **768–1023 px:** same single-active-sheet model, viewport retains more scene height; catalogue cards may use three columns; no squeezed triple-pane desktop layout.
- **≥1024 px:** 56 px header, 60 px rail, 300–340 px Add, flexible scene, 300–320 px inspector. At 1024 px close inactive Add when editing to keep the scene usable; both panels can be open at wider widths. Independent panel scroll; viewport never establishes page overflow.
- **Landscape with width <1024 px and height ≤540 px:** active panel beside preview (about 45%/55%), not below it; header wraps rather than covering content; controls scroll vertically. Fullscreen shopping fits viewport height with body scrolling. At 320 px/zoom, prioritize readable content and document scrolling over forced side-by-side composition.
- Catalogue uses the existing ≥1024 px facet sidebar; below that a native disclosure above results. Result cards min width is content-driven; two columns only when labels fit, otherwise one. Preserve logical DOM reading order and natural Spanish/English label growth.

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
| UI-AC-07 | All | ready | V3 exposes one named Backing display group inside Fondos y muebles (Q3 location pending). |
| UI-AC-08 | All | ready | V3 lists each of the seven proposed canonical Backing members once within the group (pending Q3 membership approval). |
| UI-AC-09 | 320–1023 px | empty | V3 (and conditional V4 if selected) shows “Limpiar búsqueda” without horizontal overflow. |
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
| UI-AC-30 | All | ready | The HTML labels V4 as a pending Q3 alternative to the current Taller-only proposal. |

Criteria dependent on Q1–Q3 describe the illustrated proposal, not accepted decisions. If q3=a is selected, original visual groups remain for their other pieces and the seven move visually into Backing; if q3=b is selected, the same canonical cards also remain in their old groups. Original-name search remains in both. Do not interpret UI-AC-07 as a requirement to pick q3=b. V4-only criteria apply only if its surface is approved. Identity, `GrupoCatalogo` and `ASIGNACION_FONDOS` invariants require source/functional checks in T3.3/T3.8; a rendered grouping cannot prove them.

Engine/layout/scale/colour parity and old-category discovery need functional tests plus the documented Blender import; screenshot review cannot accept R9–R11 alone. HTML renders schematic geometry and simulates interactions; it does not produce a GLB, quote, actual catalogue count or live AI response.

## 12. Open questions and assumptions

### Owner decisions requested

These mirror the still-open `rounds/round-09.json` rather than creating a second decision round. David owns the answers, with Planner reconciling SPEC/PLAN. The following are **not confirmed**:

- **Q1 — Table creation (round 9 q1).** One visible card per existing table type, immediately inserted and adjusted in the inspector (recommended and mocked), or the generic card followed by a pre-creation form? No new form is specified unless David selects that alternative.
- **Q2 — Furniture pricing (round 9 q2).** Keep quantities/dimensions under “Mobiliario · no es producto de la tienda” without prices (recommended and mocked), or introduce rental prices from an owner-supplied table? Never invent a price while this is pending.
- **Q3 — Backing membership and location (round 9 q3).** Confirm the seven canonical IDs and whether to move them from their old visual groups or show them in both. Also reconcile the SP-3 “catalogue and Taller” outcome with q3=a, which proposes only a Taller group while `/catalogo` is currently Shopify-only. Recommendation: the seven scene props as one named Backing group in Fondos y muebles with preserved search/AI/photo identities; decide explicitly whether V4 belongs in Shopify `/catalogo` or only the scene catalogue. V4 is a clearly marked alternative, not an approved new product collection. T3.3 currently has no `/catalogo` implementation files: choosing that surface requires Planner to revise task paths and acceptance before plan approval. Moving cards from their current visual groups also needs reconciliation with US-7's “no item is lost from where it is found today”.
- **Q4 — Blender verification (round 9 q4).** Portable Blender acquisition for automated real import plus one owner manual import (Planner recommendation), or file-level checks plus owner-only import? No installation is performed or authorized by this contract. Record missing real-import evidence as blocked/manual, never as passing.

No new independent owner decision was discovered. Q3 already contains a material scope mismatch (Taller scene catalogue versus Shopify `/catalogo`), and Q4=b would require aligning the unconditional automated Blender acceptance in T3.5/T3.6 with owner-only import evidence. Planner owns those reconciliations; this draft does not resolve them by choosing an option.

### Confirmed boundaries and explicit assumptions

- Confirmed: never-cut R9/R10/R11; GLB, not a new Blender format; scene layout/sizes/colours and metre scale; Backing grouping with preserved canonical identities; existing app styling; no new 3D-room work. Source table limits and existing editable-group behavior are reused.
- Draft UX proposal requiring plan approval: one creation card per type including rectangular, native numeric companions for dimensions, visible requested-versus-placed capacity feedback, captioned GLB import help. These are design choices, not claims that the current UI already behaves this way.
- V4, group membership and visual-group compatibility are provisional Q3 dependencies; furniture price presentation depends on Q2 and creation flow on Q1. Implementers must not resolve these ambiguities themselves. Planning can continue; owner approval settles them before implementation.
- SP-3 task bindings are T3.1–T3.8 as listed in section 1; all remain draft until plan approval. No tasks from other subplans are silently reassigned.
- Local export requires all relevant assets already loaded; offline does not guarantee that. Permissions come from SP-1/2, stored-project conflict behavior from persistence, language strings from language work. No simulated UI success implies those integrations passed.
- Mock fixtures use a celebration scene named “Cumpleaños · lavanda”, source table default 2.40 × 0.90 × 0.75 m and 8 illustrative placed Tiffany chairs. The mock capacity is labelled example and is not an alternative perimeter algorithm. No network, paid provider, actual download, production write, repository change or extra bitácora output is authorized here.

### Previous draft verification record (2026-10-26; retained evidence, not a rerun of this revision)

Historical report from the prior draft. Its undo claim is superseded: current interaction testing exposed duplicate change registration during input replacement, now corrected in this mockup. The current revision evidence below governs handoff.

Local Chromium via the existing Playwright dependency: 63 view/state combinations × 6 viewports × 2 themes = 756 layout checks; no document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. Ten core exercised interaction checks passed: add/select table, valid dimension update, invalid dimension retains last geometry, capacity warning, shopping uses placed chairs, Escape focus restoration, export pending blocks duplicate, honest simulated completion, AI empty-prompt validation and apply proposal. No JavaScript page errors. Representative desktop dark, mobile editor and tablet light catalogue were visually inspected. Sampled token contrast: primary white text 4.84:1 dark / 6.11:1 light; secondary labels 6.63:1 / 7.47:1; focus against panel 4.99:1 / 5.82:1. Additional final checks passed: undo/redo restored 2.40 m / 3.00 m, the seven canonical Backing cards were present, add-piece feedback and hexagonal search worked, export Escape restored focus, the shopping dialog trapped/returned focus, and the actual inline mockup bridge drove view/state/theme. No HTTP requests were made. These are scoped mockup checks, not a full accessibility audit or product/Blender acceptance. Other table-type cards represent existing-editor handoffs with explicit simulation feedback; full non-rectangular editing and real 3D geometry are not implemented by this static artifact.


### Current revision verification (2026-10-26)

- Re-read SPEC Draft behavior, round 9 q1–q4, PLAN SP-3/T3.1–T3.8 and both supplied repositories read-only. Source SHA-256 values above remained unchanged through handoff. No repository, SPEC, PLAN, changelog or project preview was edited.
- Static checks passed: all twelve numbered sections, unique visual criteria, required labelled native selectors, inline JavaScript syntax and no external resource references. The adjacent artifact remains self-contained with CSP blocking network access.
- Final Chromium/Playwright matrix passed: 63 view/state combinations × 6 viewports × 2 themes = 756 layout checks, with no horizontal document/dialog overflow, clipped horizontal controls, JavaScript errors or HTTP requests. Width/height fixtures: 320×800, 360×800, 768×1024, 1024×850, 1440×980, 844×390.
- 27 interaction assertions passed for table insertion/selection, valid and invalid dimensions, last-valid scene retention, undo/redo, requested/placed capacity, shopping counts, Escape/focus restoration, all seven canonical Backing identities and their original semantic/repository metadata, Backing/name/hexagonal-alias search, matching counters, add feedback, conditional V4 label, export pending/simulated completion, AI validation/apply and the actual inline plan bridge. Fixture metadata checks do not prove production repository compatibility.
- 24 final dialog checks across the same widths/themes passed for export and shopping; shopping explicitly cycles Tab and Shift+Tab within the modal, and both dismiss with Escape. This revision fixed duplicate input-change history entries and added an explicit modal Tab cycle after the verification exposed them.
- Visually inspected in-memory Chromium captures: desktop dark Backing at 1440×980 and full mobile light table/capacity state at 360×900. No screenshot or extra preview file was written. Existing tokens and breakpoints remain unchanged.
- These checks cover the static mockup only. Real scene geometry, paid-provider parity, downloadable GLB validity, Blender import and production accessibility conformance remain for T3.2–T3.8 after owner approval. No Blender was installed or invoked.
