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

Draft revision / impact record (2026-10-26, owner feedback 18:53; kept here because this brief authorizes no changelog file): draft; revise the same unapproved v1. Compatibility is **breaking relative to the previous draft**: remove provisional V4/Shopify navigation, duplicate-card alternatives, the generic creation entry and pre-creation-form alternative; confirm per-type default creation plus existing inspector, quantities/dimensions without rental prices, the seven-card move and portable Blender LTS verification. Affected consumers: **T3.2** (V1/V2/V5/V6, F1/F2/F5), **T3.3** (V3/F3; remove V4), **T3.4** (V7/D1/F4 copy and feedback retained), **T3.5/T3.6** (confirmed automated real import plus separate owner opening), **T3.7/T3.8** (revised review scope). No accepted implementation exists to establish shipped conformity. Delegation D-20261026-191119-918c rechecked the same source snapshot; its mockup corrections are compatible with this owner-answer draft: the capacity warning now follows the entered request, validation can recover to the last valid value, and offline recovery is reachable. Production flows, tokens, views and task ownership are unchanged; T3.2 and T3.7 gain the explicit regression criteria UI-AC-34–35 below. Six active views retain their tokens and applicable states; the visual composition is superseded by the owner-requested revision below. No other subplan contract changes; SP-1/2 own access, SP-8 owns translation and SP-4 owns server saves. Required action: owner plan/contract approval, then T3.1 exact copy, T3.2–T3.4 implementation, T3.5/T3.6 verification and T3.7/T3.8 independent review. An approved version is immutable; subsequent changes require v2 and impact analysis.

**Visual revision — owner feedback 2026-10-26T19:36, delegation D-20261026-193603-299b.** Rebuild the visual layer across all six views and both dialogs, following `agents/designer/references/mockup-craft.md`: neutral token-based navigation/surfaces, one foreground primary action, equal peer-object cards, compact ruled inspector sections, plain conversation entries, file handoff without tinted containers, right-aligned tabular quantities, and consistent inline SVG icons. Keep every flow, state, breakpoint, canonical identity and the original UI-AC-01–35. This is **breaking visual compatibility relative to the previous draft** because hierarchy and component composition change; functional behavior and data contracts remain compatible. T3.2 consumes the V1/V2/V5/V6 composition, T3.3 the V3 cards and T3.4 the V7/D1 export presentation; T3.1 copies the resulting exact artifact and T3.7 must re-render all affected views/dialogs. T3.5/T3.6/T3.8 retain their functional scope and use the revised visual criteria where applicable. SP-1/2/4/8 contracts are unchanged. There is no approved implementation to migrate. This record replaces a separate changelog only because the delegated boundary authorizes exactly two design artifacts plus RESULT.json. The contract remains `draft` and requires owner approval with the plan.

**Kit revision — owner feedback 2026-10-26T21:01, delegation D-20261026-213506-5754.** Recompose all six views and D1/D2 from the kit template/snippets, preserving F1–F5, canonical data, all eleven state names and the original criteria. Compatibility is **breaking visual** relative to the previous unapproved draft, **compatible functional/data**. Affected: T3.1 exact-copy artifact, T3.2 V1/V2/V5/V6, T3.3 V3, T3.4 V7/D1; T3.7 must re-render all surfaces. T3.5/T3.6/T3.8 keep their scope. Dark action colours are mapped to an existing accessible project pair; cards, controls, footer alignment and padding now follow the kit. Narrow layouts keep one active panel with document scrolling, rather than compressing the form into a fixed-height remainder. No other subplan, API, source token file or approved version is changed. Approval remains with David and the plan.

Read-only product evidence (pictures is the implementation repository; t12 is the compatibility reference, not an additional implementation target):
- `t12` HEAD `fb872bce`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `Taller3D.tsx`, `HojaMovil.tsx`, `EditorConjuntoMesa.tsx`, `FondosYMuebles.tsx`, `ListaEscenografia.tsx`; `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `fondos-escenografia.ts`, `mobiliario-tipos.ts`; `src/lib/catalogo/asignacion-fondos.ts`; `src/app/catalogo/page.tsx`, `src/components/catalogo/Facetas.tsx`.
- `pictures` / `asesor` HEAD `fa101a47`: same table editor and shared UI classes; `ExportarEscenaTaller.tsx`, `exportar-escena-glb.ts`, `exportadores-escena-globos.ts`, `archivo-escena.ts`. The GLB UI/exporter exists here, not in the inspected t12 source. Shared Taller colour tokens match; globals differ elsewhere. Do not assume worktrees contain identical features.
- Table default dimensions and limits below are source values, not new business rules. Mock examples, counts and capacities are explicitly fictitious; runtime counts come from the engine. No mock price is a catalogue fact.

## 2. Purpose and users

External accounts with `taller.usar` (initial Plan 3), employees and administrators build event scenes; they need a discoverable rectangular table, editable seating and reusable Backing. These views require Taller access; Shopify `/catalogo` and its independent `catalogo.ver` access remain outside this subplan. Success: the user can locate a prop, insert it once, see the actual table/chair counts, and start a GLB download without losing scene work. Blender parity is a separately verified export outcome, never inferred from a success toast.

V1 finds the table; V2 adjusts it; V3 finds scene Backing; V5 checks actual materials; V6 requests the same table through existing scene AI; V7 hands the scene to Blender. No account administration, new room editing, Illustrator, module editing or save-project redesign is included.

Each screen has one question and one main job; these are design intent, not additional production banners. The mockup displays them above the product shell for review.

| View | One question | Main job / observable success |
|---|---|---|
| V1 Tables | ¿Qué mesa necesita esta escena? | Add the intended type at its default size and reach the existing inspector. |
| V2 Table editor | ¿Qué medidas y cuántas sillas caben? | Edit dimensions and see the requested versus actually placed chairs. |
| V3 Backing | ¿Qué piezas completan el Backing? | Find and add a canonical panel, hoop or pedestal once. |
| V5 Shopping | ¿Qué piezas tengo que preparar? | Read actual quantities and dimensions with no rental-price claim. |
| V6 Scene AI | ¿Cómo añado esta mesa con la IA? | Describe, review and apply the same editable table. |
| V7 Export | ¿Cómo llevo esta escena a Blender? | Initiate a GLB download in metres and read its Blender import destination. |

Product inventory: Pictures / Taller 3D; project “Cumpleaños · lavanda”; rectangular table, Tiffany chairs, round panel, pedestal set and the seven canonical Backing pieces. These concrete scene objects replace generic dashboard panels or invented account metrics. The scene is the single visually expressive area; surrounding controls are restrained working surfaces.

## 3. Information architecture and hierarchy

Keep the existing workshop shell: title/actions → panel rail → Add panel → scene viewport → selected-piece/IA inspector. One local primary action per panel. The scene and selected object remain visible while dimensions change.

- Add → **Fondos y muebles / Mobiliario** → one card per existing parametric type (Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, Banquete en U), confirmed in round 9 q1=a. Rectangular is explicitly visible and uses the existing model/editor. Each type card inserts its default size from `PARTIDA_MESA`, selects the group and opens the existing inspector; no pre-creation form. The per-type cards replace the generic **Mesa con sillas a medida** creation entry; all eight parametric types remain available. “Imperial” is an existing fixed catalogue piece, not a new parametric type: do not add it to `TIPOS_MESA`.
- Add → **Fondos y muebles / Backing** is a presentation group, not a new data repository. The mock exposes it directly as a category shortcut. Round 9 q3=a confirms that the seven cards move from their previous visual groups into this single Backing group, once each. Other pieces remain in their current visual groups. No duplicated card aliases and no Backing collection/filter in Shopify `/catalogo`. Keep `GrupoCatalogo = "fondo" | "asiento" | "mesa" | "decorado"` and every `ASIGNACION_FONDOS` entry unchanged. Derive Backing display membership from the explicit seven-ID set; do not write `grupo: "backing"`, move repositories or migrate saved scenes for presentation. Keep the catalogue name “Marco hexagonal metálico” for `aro_hexagonal`; “aro hexagonal” remains a discovery alias. Search “Backing” returns the seven distinct canonical entries; original names, AI/photo discovery and repository filters remain compatible. Counters follow the filtered canonical results, not duplicated aliases.
- Inspector: selected name → dimensions in metres → chair count/engine capacity → chair type/distribution → existing material/colour controls → grouped move/rotate/duplicate helper.
- Shopping list: actual quantities and dimensions, then material description; distinguish Mobiliario / Escenografía from store products. Preserve “no es producto de la tienda”; show no rental prices; do not invent purchasability or stock (round 9 q2=a).
- Export remains a header action (wrapping named action on narrow screens). Put **Descargar modelo GLB · Blender** alongside existing PNG, then one sentence explaining metres and Blender import. No wizard or invented progress percentage.

## 4. Design system and visual language

**Governing visual revision — owner feedback 2026-10-26T21:01.** Compose every changed view from the david-ui stand-in kit. The HTML starts from `kit/templates/mockup.html`, keeps its labelled native selectors and Mockup label, and embeds the current kit with `kit/inline.py`. Component classes, structure, padding, focus and variants come from vetted snippets, not a parallel stylesheet. Source palette and source data remain Pictures'. This supersedes the former draft's bespoke visual classes, not its functional flows.

### Project role mapping

Values come from `src/app/globals.css` in both inspected worktrees. Offline typography uses the kit's system sans fallback for production Geist Sans; no font download. Source `--taller-primario` is still #6d3fe0 light / #7a55ec dark, but the dark role `--primary` deliberately uses the existing `--taller-acento` and `--taller-sobre-acento` pair: it can serve both a readable text link and an accessible filled control in the kit. This is a proposed semantic-role mapping for SP-3, not an edit to production globals or a new palette.

| Kit roles | Existing Pictures source | Light | Dark |
|---|---|---|---|
| `--background` | `--taller-panel` | #faf9fc | #16131d |
| `--foreground`, card/popover/secondary/accent foreground | `--taller-texto` | #1c1425 | #f2eff7 |
| `--card`, `--popover` | `--taller-tarjeta` | #ffffff | #1d1926 |
| `--primary` | `--taller-primario` light / `--taller-acento` dark | #6d3fe0 | #b9a4ff |
| `--primary-foreground` | `--taller-sobre-primario` light / `--taller-sobre-acento` dark | #ffffff | #120b24 |
| `--primary-hover` | `--taller-acento` light / `--taller-texto-2` dark | #5530b8 | #ddd8e6 |
| `--secondary`, `--muted`, `--accent` | `--taller-encima` | #f3eefb | #231e2e |
| `--muted-foreground`, `--input` | `--taller-medio` | #5a5168 | #a59db5 |
| `--border` | `--taller-borde`, decorative separators only | #ddd3ea | #2d2838 |
| `--ring`, `--sidebar-ring` | `--taller-resalte` | #6d3fe0 | #8f6ef5 |
| `--sidebar` | `--taller-barra` | #ffffff | #121018 |
| `--sidebar-accent` | `--taller-panel` light / `--taller-tarjeta` dark | #faf9fc | #1d1926 |
| `--destructive` | `--taller-peligro` | #a8323d | #f08a94 |
| `--success` | `--taller-valido` | #1a6a4a | #5fd3a0 |
| `--warning` | `--taller-medio` (neutral capacity/status notice) | #5a5168 | #a59db5 |
| `--info` | `--taller-acento` | #5530b8 | #b9a4ff |
| `--scene-background` (proposal alias) | `--taller-visor` | #ebe7f1 | #1a1722 |

Status soft roles use existing neutral panel/card surfaces; destructive foreground uses the same contrasting source pair as primary foreground; sidebar foreground/primary/border roles mirror the matching roles above. Retain the kit's unused chart and overlay defaults. No raw UI colours outside this one mapping block. SVG prop/material colours are scene data, not chrome.

### Components and snippet provenance

| Composition | Contract name / variant / states | Vetted snippet |
|---|---|---|
| App rail | Sidebar · state=collapsed · current/hover/focus | `kit/components/sidebar.html#collapsed` |
| Type and Backing cards | Card · size=sm · parts=content/header/title/description/footer | `kit/components/card.html#actions`, small variant from `#stats` |
| Actions | Button · variant=default/outline/ghost · state=default/hover/focus-visible/disabled/loading | `kit/components/button.html#variants`, `#sizes`, `#states` |
| Numeric fields | Field · orientation=vertical · state=default/error; Input · type=text/number · state=default/error | `kit/components/field.html#vertical`, `kit/components/input.html#types` |
| Chair/material choices | Select · native · state=default/focus-visible/disabled | `kit/components/select.html#native` |
| Prompt | Textarea · state=default/error/disabled | `kit/components/textarea.html#states` |
| Persistent feedback, including inline empty states | Alert · variant=default/success/destructive · action | `kit/components/alert.html#variants` |
| Loading | Skeleton · rows · state=loading | `kit/components/skeleton.html#card` (neutral placeholder parts) |
| Count/status label | Badge · variant=secondary | `kit/components/badge.html#variants` |
| Legacy details | Accordion · type=multiple · state=closed/open | `kit/components/accordion.html#default` |
| Shopping D2 | Dialog · size=lg · header/title/description/footer/close; Table · numeric alignment=end | `kit/components/dialog.html#open`, table anatomy from `kit/components/data-table.html#ready` |
| Export D1 | Popover · align=end (nonmodal role=group to preserve existing export semantics) | `kit/components/popover.html#open` |
| Transient local acknowledgement | Toast · type=info · state=visible | `kit/components/toast.html#stack` |

Checkbox/Radio/Switch controls are not needed in these six flows. Do not add a checkbox as a substitute for chair quantity or a new export setting. Any such control introduced by an approved later change must use the kit's `.checkbox`, `.radio` or `.switch`; browser-native white squares are unacceptable in the dark theme.

**Layout proposals outside the kit:** workshop split panes (`workshop-grid`, `workshop-pane`, `scene-pane`), scene illustration frame, equal object-card grid, compact dimension grid, native-dialog host and responsive export anchoring. They use role tokens and 4 px spacing multiples and compose kit components without changing their visual classes. The kit has no 3D editor or canvas: the static SVG scene is explicitly a proposal/schematic, not a new rendering engine. A custom script is necessary for shared table data, validation/history, applicable state options, and modal state/focus behavior that visibility attributes alone cannot express.

Use `.app` + `.sidebar` + `.app-main` + `.app-header`; stacks/rows provide all internal gaps. The tools row wraps inside one padded content frame. No centred form with a footer on another axis: inspector labels/help/actions share the same left edge; Card header/content/footer use the same component inset; Dialog header/body/footer belong to one box. Inline empty states use left-aligned Alert anatomy to keep the workshop axis.

Typography: body/labels 14 px, metadata 12 px, headings 16/20/24 px from kit roles; numeric inputs and quantities right-aligned with tabular figures. Source icons are consistent inline SVG, not emoji. Default cards use kit 24 px padding (20 px on phones); these peer cards deliberately select **size=sm**, the kit's 16 px inset, not bespoke cramped padding. Default controls are 36 px, phone controls 40 px; default controls never use an 8 px card inset. Panel inset 24 px desktop / 16 px narrow. Standard gaps 8/12/16/24 px. Kit radii and visible 2 px focus ring are retained. Phone controls meet 24 px minimum and prefer 40–44 px touch area; layout allows wrapping instead of shrinking labels.

One primary action maximum on the visible surface. V1 gives rectangular creation the primary action; V2 uses list access; V3's peer add actions remain outline; V6 uses Send or Apply, never both primary; V7 uses open-export or GLB, never both primary. An open D1/D2 removes background primary emphasis. Navigation is neutral with explicit current/pressed semantics. Flat fixed surfaces; shadows only on floating Popover/Dialog/Toast. Preserve the template's Sutil/Natural/Expresivo motion selector; reduced-motion disables meaningful displacement, and loading skeletons remain static. Component motion is functional and comes from the kit.

## 5. Navigation and interaction model

Keep `/3d`; do not create standalone production routes for V1–V7. V1/V2/V3/V6/V7 are workshop panel states; V5 is the existing shopping dialog D2. V4 has been removed from the contract and mockup following round 9 q3=a: Shopify `/catalogo` is unchanged. The mockup’s “Vista / Estado / Diálogo / Tema” controls and decision-context notes are planning-only and do not ship. All six active views have selectable states for review.

Selection uses real buttons; “Editar mesa” provides a keyboard alternative to clicking/dragging the scene. Adding a table selects it and focuses the inspector heading on narrow screens; desktop announces selection without stealing focus while the user browses. Editing applies valid values after change/blur; transient invalid input stays visible and does not mutate the scene. Preserve undo/redo grouping and object identity. Esc closes export popover/dialog and returns to its invoker. Shopping uses a labelled modal with focus trap; export uses a labelled nonmodal group as today, not a fake ARIA menu. Close by Escape or outside click; Tab follows normal button order.

No drag-only actions. Backing add buttons respect authoritative Taller permission outcomes. Do not start a new empty scene or replace a current scene as a side effect of navigation. Panel navigation preserves current work; persistence ownership stays outside SP-3. The mockup simulates only local mutations and makes no download/network request.

## 6. Flows

**F1 — Add and edit manually (R9).** 1. Open Add / Mobiliario. 2. Activate “Mesa rectangular”. Insert one editable group with current source defaults: 2.40 × 0.90 × 0.75 m; chair defaults remain the engine's current defaults (8 requested in the existing entry), not a second UI rule. 3. Select the new table and open dimensions. 4. Change length/width/height and chair quantity/type/distribution. 5. Engine recomputes geometry/capacity and actual placed chairs. 6. Announce “Mesa actualizada: …; … sillas colocadas”. 7. Open shopping list and see the same actual quantities. Undo restores the previous group and counts.

**F2 — Capacity / validation recovery (R9).** Accept rectangular ranges from `LIMITES_MESA`: length 1–6 m, width 0.40–1.50 m, height 0.40–1.10 m. Existing sliders use 0.05 m steps; numeric input must not silently round a typed invalid value. Correcting an invalid field back to its previous valid value clears the error without creating a redundant undo entry. Integer chairs 0–40 requested, actual capacity from `repartirSillas`; do not use 40 as the physical capacity. Show “Pedidas 12 · Colocadas 8” when the engine fits fewer, with the existing capacity explanation. Shopping/export use placed chairs only. On invalid text, show field error and keep last valid geometry; allow correction or “Restablecer valores”. If resizing reduces capacity, show the result visibly, never report the requested count as placed. Scene AI uses the same validation and counts. Old fixed groups offer the existing “Hacerla editable”; room-generated tables retain their current “ajustar el salón” instruction, not an independent conflicting editor.

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
| V1 `tables` | Card · size=sm (`card.html#actions/#stats`); Button · default/outline (`button.html#variants`); Field/Input · search (`field.html#vertical`). Add title; Mobiliario selected; search; “Mesa rectangular”, source default dimensions; cards for the other seven existing types; rectangular-card action “Añadir” (accessible name “Añadir Mesa rectangular”); equal-width type cards; scene; compact selected-piece summary | Desktop three panes, narrow active sheet; S1–S5,S7,S9–S10; F1 |
| V2 `table-editor` | Field/Input · default/error (`field.html#vertical`, `input.html#types`); Select · native (`select.html#native`); Alert · capacity (`alert.html#variants`); Accordion · closed/open (`accordion.html#default`). “Mesa rectangular 01”; length, width, tabletop height numeric fields + source ranges; chair requested/placed/capacity, type, distribution; existing cloth/colour controls; actual-count note; “Ver lista de compra” | One inspector column; fields never side-scroll; S1,S2,S3,S4,S5,S6,S7,S8,S9,S10; F1/F2 |
| V3 `backing` | Card · size=sm (`card.html#actions/#stats`); Button · outline; Badge · secondary; Field/Input · search. Add → Backing; “Aros, pedestales y paneles”; search; two-column peer cards with transparent illustrated thumbnails and canonical names, dimensions when known, “Añadir…” accessible names; preserve original-name/AI/photo discovery; no duplicate cards in previous groups | Cards wrap; no stock/price invented; S1–S5,S7,S9,S10; F3 |
| V5 `shopping` / D2 | Dialog · size=lg (`dialog.html#open`); Table · numeric alignment=end (`data-table.html#ready`); Button · default. Dialog title “Lista de compra”; ruled Mobiliario and Escenografía sections; right-aligned tabular “Cantidad” column; e.g. 1 × rectangular table (2.40 × 0.90 × 0.75 m), 8 × Tiffany chair, 1 × round panel, 1 × pedestal set; “No son productos de la tienda”; no invented currency total; close to prior scene | Kit Dialog size=lg, max 672 px, viewport inset 16 px narrow; S1–S5,S7,S9,S10; F1/F2 |
| V6 `ai` | Textarea · default/error/disabled (`textarea.html#states`); Alert · default/success/destructive; Button · default/outline. Existing scene IA inspector; one mock conversation; text prompt; “Enviar”; pending response; result “1 mesa rectangular · 8 sillas colocadas”; existing proposal/apply interaction and manual-edit link | Input below conversation, expands above mobile keyboard; S1–S5,S6,S7,S8,S9,S10,S11; F5 |
| V7 `export` / D1 | Popover · align=end (`popover.html#open`); Button · default/outline/loading; Alert · default/destructive/success. Workshop with export group open; PNG sibling, primary “Descargar modelo GLB · Blender”; scene name, metre scale, import instruction; prepare/error/started feedback next to trigger | Popover max 340 px, fits viewport; accessible in compact narrow header; S1–S5,S7,S8,S9,S10,S11; F4 |

Visible product copy is Spanish for this draft. Semantic strings are translation-ready; bilingual rollout belongs to the language subplan (R12), not an implicit SP-3 implementation. Backing and GLB retain those names in both locales. No new language switch is introduced. Test translated labels with 40% expansion; only project name may truncate with an accessible full name. The dark/light mock selector represents both existing product themes.

## 8. States

`#state` is a visible native select; only states applicable to the current view are offered. `#view` uses the six active ids above; `#scene` offers `none`, `export`, `shopping`; `#theme` offers `dark`, `light`. All have visible labels. The bridge can set value and dispatch `change`. State options update when the view changes. Dialog state comes from the chosen view/state; exported example data is never downloaded. Mock-only status explicitly says any resulting change is simulated. The template’s fifth `#motion` select exposes subtle/natural/expressive motion profiles; it is planning-only.

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

- **320–767 px:** wrapping tools row with named Export and shopping actions; one active Add/Inspector/IA pane below the scene preview. Preview SVG is 180–220 px high; its controls and summary retain their own padding. Use vertical document scrolling so the toolbar, full fields and keyboard cannot hide each other. Preserve selected piece/search when navigating panels; the mock’s planning view selector resets illustrative search, as before. Shopping/export fit `100vw - 32px`. Numeric fields become a single column below 480 px; object cards use one column when two kit-padded cards do not fit. No page-level horizontal scroll, mandatory drag or clipped primary action.
- **768–1023 px:** same single-active-pane model; content-driven peer cards may expand to three columns; no squeezed triple-pane desktop layout. The sidebar rail is replaced by the labelled mobile navigation row.
- **1024–1279 px:** collapsed 56 px Sidebar within a 64 px layout track, one active 320–340 px side panel and flexible scene. Hide Add when editing/using AI/export, hide Inspector when browsing Tables/Backing. Header 56 px plus a wrapping padded actions row.
- **≥1280 px:** Add 340 px + flexible scene + Inspector 340 px with the existing rail. Each side panel scrolls independently with at least 680 px content viewport; the scene can remain sticky. At 1440×980 the default rectangular inspector shows dimensions, chairs, Materials heading and first control without scrolling.
- **Landscape 640–1023 px and height ≤540 px:** active panel beside preview (45% preview / 55% panel), vertically scrollable controls. Below 640 px or at large zoom, prioritize readable vertical flow over forced columns. Shopping body scrolls within viewport height; export becomes a bounded fixed floating panel below 480 px.
- Backing shares Add and its responsive behavior; no storefront/facet route. Maintain logical DOM order (Add → scene → Inspector on desktop; scene → active pane when narrow). Spanish/English label expansion is a production review target; this draft remains Spanish.

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
| UI-AC-20 | 640–1023 px, height ≤540 px | ready | Active panel is beside the preview and its controls can scroll vertically. |
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
| UI-AC-34 | All | partial | After requesting 20 chairs with the eight-chair mock fixture, the warning and input both say 20 requested and the placed count remains 8. |
| UI-AC-35 | All | validation → ready | Correcting an invalid dimension or chair quantity back to its previous valid value removes the field error. |
| UI-AC-36 | All | ready | Active rail, category tabs and mobile navigation have neutral text/surface selection, without a purple strip or tinted banner. |
| UI-AC-37 | All | ready / partial | At most one foreground action uses the primary fill, including when export or shopping is open. |
| UI-AC-38 | All | ready | V1 uses eight peer cards of equal column width; rectangular has no tinted enclosing hero. |
| UI-AC-39 | All | ready | V5 quantities share a right-aligned column and use tabular figures. |
| UI-AC-40 | All | ready | V2 numeric input values and type-card dimensions are right aligned with tabular figures. |
| UI-AC-41 | All | ready | Fixed panels and notices have flat token surfaces with no shadow, gradient, blur or glow. |
| UI-AC-42 | All | ready | Navigation, export and add icons are inline SVG; supporting UI text is at least 11 CSS px. |
| UI-AC-43 | 1440×980 px | ready | V2 shows the dimensions and chairs groups plus the Materials heading and its first control in the initial desktop inspector viewport. |

| UI-AC-44 | All | ready | Every view uses the inlined kit and the named component anatomy from sections 4/7; `Mockup` remains visible. |
| UI-AC-45 | All | ready / validation | Inspector field labels, controls, help and action starts share their container’s left edge. |
| UI-AC-46 | All | ready | Card header/content/footer have matching kit size=sm insets of 16 px. |
| UI-AC-47 | All | ready / error | Text meets 4.5:1 and interactive boundaries/focus meet 3:1 in both themes. |
| UI-AC-48 | 320–767 px | ready / empty / error | Export controls and the shopping footer fit inside the viewport’s 16 px side insets. |
| UI-AC-49 | All | ready | Motion profiles are reachable through the labelled planning selector, and reduced motion removes displacement. |

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

### Previous revision verification — owner-answer reconciliation (2026-10-26)

- Read the updated SPEC, PLAN.md and PLAN.json SP-3/T3.1–T3.8 plus the supplied repositories read-only; the source hashes recorded in section 1 match at handoff. Shared table-default, assignment and Taller-class files match between t12 and pictures. Only the two named design artifacts and the required delegation RESULT.json were written; no repository, SPEC, PLAN, changelog or project-preview edits, commits, launches or Blender installation.
- Static checks passed: twelve numbered sections, 33 unique acceptance criteria, `status: draft`, four visibly labelled native selectors, inline JavaScript parsed by Node `vm.Script`, no external resource references and no obsolete catalogue route or pending Q1–Q4 mock branch. CSP continues to prohibit network requests.
- Headless Chromium using the repository’s existing Playwright dependency: **55 applicable view/state combinations × 6 viewports × 2 themes = 660 layout checks**, plus **144 export/shopping dialog layout checks**. No document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. All six active view ids and state selectors were driven through native `change` events, matching the bridge integration interface.
- **34 interaction assertion groups passed**: all eight type cards use their source defaults and open the inspector without an intermediate form; valid/invalid dimensions, last-valid geometry, undo/redo, requested/placed capacity, actual shopping counts/dimensions without prices, seven unique canonical Backing cards with unchanged semantic/repository fixture metadata, original-name and hexagonal-alias discovery, matching Backing results, add feedback, pending export duplicate prevention, honest simulated completion, Escape/focus return and AI validation/application. An initial test incorrectly required every original-name query to return exactly one result; “Arco metálico” also matches “Marco hexagonal metálico” under the preserved substring search. Corrected the check to require the original canonical card once, without changing the established search behavior; the focused interaction run passed. Fixture metadata/discovery does not prove production AI/photo or saved-scene compatibility.
- **24 keyboard checks passed** across the same viewport/theme pairs: shopping Tab/Shift+Tab cycles within the modal and Escape returns focus; export Escape returns focus. Final interaction run observed zero JavaScript page errors and zero HTTP requests.
- Visually inspected in-memory Chromium captures: 1440×980 dark Backing and 360×900 full-page light table/capacity state. No screenshot or extra preview file was written. Tokens, responsive boundaries, rectangular illustration and unaffected flows remain intact; other type cards now demonstrate their source-default inspector handoff with schematic type artwork.
- Earlier verification records include the removed V4 and are historical only. This revision validates a static planning artifact: production engine geometry, deterministic AI-tool parity, saved-scene/AI/photo compatibility, actual GLB validity, automated Blender import, owner manual opening and full accessibility conformance remain for the planned implementation/verification cycle after owner approval.


### Previous delegation verification — D-20261026-191119-918c (2026-10-26)

- Re-read SPEC, PLAN and SP-3/T3.1–T3.8 in PLAN.json; their SHA-256 values still match section 1. The exact UI consumer remains SP-3, `taller-esenciales@v1`, design-copy task T3.1, implementation tasks T3.2/T3.3/T3.4 and independent visual task T3.7. No additional owner questions or scope changes were found. Status remains **draft**, pending plan approval.
- Preserved the six existing views, confirmed round 9 decisions, source tokens, responsive layouts and export scope. Fixed two reproduced mock fidelity defects: hard-coded requested-chair feedback and errors persisting after restoring a previous valid value. Added the missing visible offline retry action. No production engine behavior is implemented by these corrections.
- Node `vm.Script` parsed the inline JavaScript. Static structure checks verified twelve numbered sections, draft status, unique acceptance-criteria ids, six view ids, four labelled native selects and no external resource links. The final contract has **35** visual acceptance criteria.
- Headless Chromium using the existing repository Playwright installation passed **660 view/state/viewport/theme layout checks** and **144 dialog layout checks**. Sizes: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and 844×390 landscape; both themes. No horizontal document/dialog overflow, horizontally clipped controls, JavaScript page errors or HTTP requests occurred. Native select value/change events exercise the plan bridge interface; the external bridge itself was not rerun in this delegation.
- **34 interaction assertions passed**, including default creation and inspector handoff for all eight table types, numeric edits, last-valid geometry, undo/redo, 20 requested versus 8 placed, list counts, same-value dimension/chair validation recovery, seven unique Backing identities, hexagonal alias discovery, add feedback, offline retry, export failure/retry visibility, duplicate-export blocking, honest simulated completion and AI validation/apply. An initial test used an ambiguous retry locator because both desktop panels exposed retry; scoped it to the active catalogue panel and the full interaction run passed. No product behavior was weakened to satisfy that test.
- **24 keyboard checks passed** across the same viewport/theme pairs: shopping modal Tab/Shift+Tab containment and Escape focus return; export Escape focus return.
- Visually inspected in-memory renders of all six desktop views at 1440×980 and full-height 320 px light renders of table/capacity (20 requested) and export error/retry, in addition to the earlier dark narrow view. The corrections preserve the existing composition and readable wrapping. No screenshot or other artifact file was written. These are scoped mock checks, not a full accessibility conformance claim.
- Only the two authorized design artifacts and the required delegation RESULT.json are written. Repositories remain read-only; no SPEC/PLAN, changelog, project preview, other bitácora file, commit, installation or deployment is part of this task. Application lint/types/build, real engine/AI-tool parity, actual GLB export, Blender import and owner opening remain unexecuted here and belong to T3.2–T3.8 after approval.


### Previous delegation verification — D-20261026-193603-299b (2026-10-26)

- Read the governing Designer authoring/versioning skills and `mockup-craft.md`, then SPEC.md, PLAN.md, PLAN.json SP-3/T3.1–T3.8, both previous design artifacts, the project memory and relevant shared Taller tokens/components in both supplied repositories read-only. The three planning source SHA-256 values still match section 1. Only the two named design artifacts and the required delegation RESULT.json are authored by this task; no repository code, SPEC/PLAN, separate changelog, project preview, memory file, screenshot file, installation, commit or deployment was performed by this Designer.
- Rebuilt the complete visual stylesheet and the affected view markup; retained six views, eleven state names with their view-specific applicability (55 combinations), four labelled native selectors, source token values, breakpoint boundaries, canonical Backing identities and every existing functional flow. All original UI-AC-01–35 remain; eight visual criteria add up to **43 unique criteria** across **12 numbered sections**. Status remains **draft**, awaiting owner approval with the plan. No new unresolved owner question was found.
- Final checks: inline JavaScript parsed with Node `vm.Script`; static assertions verified section/criteria uniqueness, draft status, labelled selectors and no external resource references. Chromium launched headlessly from the existing repository Playwright dependency and opened the HTML directly through `file:`; no server or package installation was needed. `git diff --check` for the two artifacts passed.
- Final layout/state matrix: **660 checks** (55 view/state combinations × six viewport sizes × two themes) plus **144 export/shopping dialog checks** passed. Sizes: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. No horizontal document/dialog overflow, horizontally clipped controls, duplicate foreground primary actions, literal template fragments, JavaScript page errors or HTTP requests were observed. The matrix also asserts that each non-denied shopping state actually opens its dialog. Native selector change events exercise the plan bridge interface; the external bridge asset itself was not rerun.
- Final focused suite: **95 assertions passed**, including static structure, all eight source-default table creation paths, valid/invalid dimensions, last-valid geometry, undo/redo, same-value recovery, 20 requested versus 8 placed chairs, actual shopping counts and dimensions without prices, seven unique Backing cards and discovery aliases, add feedback, offline/empty recovery, AI validation/proposal/apply/manual handoff, busy/duplicate prevention, honest export completion and failure/partial handling. This includes **24 keyboard scenarios** across the six viewport/theme pairs: shopping Tab/Shift+Tab containment with Escape focus return, and export Escape focus return. A separate AI-proposal-plus-export check confirms one foreground primary action.
- Verification exposed and corrected mock-only fidelity defects: a literal validation-range placeholder, stale overlay focus returning to a planning selector after view navigation, and shopping states remaining closed after permission-denied. An intermediate test also counted the inspector tab alongside the manual-edit action; its locator was narrowed to the named action without weakening product behavior. One temporary template-quoting syntax error introduced during primary-action styling was corrected before the final passing run. Busy semantics and AI success counts now follow the visible shared state. These are static artifact corrections, not claims about production behavior.
- Visually inspected in-memory Chromium renders: all six desktop views at 1440×980; all six narrow views at 320 px, including full table/capacity, Backing, shopping, AI proposal and export-error content; and every applicable state's panel in 1440 px dark / 320 px light state sheets. The first look led to compacting the inspector so the Materials control is visible in its initial desktop viewport (cloth control y=909–947 at 1440×980), and a second look confirmed the narrow title no longer wraps. Screenshots/contact sheets existed only in memory; none were written to disk.
- Sampled source-token contrast ratios, dark/light: primary label **4.84/6.11**, secondary text on panel **7.07/7.12**, focus on panel **4.99/5.82**, input boundary **6.63/7.47**, error text **7.66/6.28**, success text **9.88/6.25**. These samples meet the corresponding 4.5:1 text and 3:1 boundary/focus targets; they do not establish full WCAG conformance.
- Product lint/types/tests/build, live AI/tool parity, production scene geometry and compatibility, actual downloadable GLB, portable Blender import and the owner's manual opening were **not run** in this design-only task. They remain the approved-plan implementation/verification responsibilities of T3.2–T3.8. This mockup makes no network call, real download, purchase or production write.


### Current delegation verification — D-20261026-213506-5754 (2026-10-26)

- Read the kit, mockup-craft, contract-authoring/versioning and interface-quality guidance; rechecked SPEC/PLAN/SP-3/T3.1–T3.8, previous artifacts, project memory and the two worktrees read-only. All three planning source hashes still match section 1. No unresolved owner question was found; round 9 decisions remain settled. The contract remains **draft** pending owner approval with the plan.
- Started from `kit/templates/mockup.html`; composed all six views and D1/D2 using the snippet references in sections 4/7. Embedded the kit with its absolute-path `inline.py`. Retained the four native planning selectors and added the template's motion selector. Preserved canonical data, all eleven state names (55 applicable view/state pairs), creation/edit/history/capacity behavior and honest simulated AI/export feedback. No network, external font/image, real download or provider call is used.
- Ran `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py` on the final HTML: **158 pairs checked in light and dark, all pass**. Source primary/accent role mapping is explicit in section 4; no production palette was edited.
- Ran `uv run --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py` on the final HTML, using its default Chromium and widths 1280/390 px: **240/240 renders, 9,444 text measurements, 1,184 focus stops**. Final result: **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**. The audit crosses its initially available states and dialog scenes; the separate matrix below covers all eleven state names with their per-view applicability. No sampled/unknown measurement warning was emitted.
- Earlier measured failures were corrected through kit composition: card size=sm provides sufficient inset; Export uses the snippet's align=end anchor; closed Accordion content is explicitly hidden; inline empty feedback follows the inspector's left axis; planning annotations are contained in the template header. Removed nonessential illustration lettering that the SVG contrast probe could not associate with its painted backing surface. One intermediate audit process ended with exit 143 and no result; it was not counted as a pass. Later completed output above is the handoff evidence.
- Focused Chromium suite: **679 layout/interaction assertion groups passed**, including eight default type-card paths, valid edits, invalid-value retention and recovery, undo, 20 requested/8 placed, shopping actual quantities, Backing canonical membership/hexagonal alias/add feedback, AI empty-prompt validation/application, duplicate-export prevention, honest simulated completion and retry. It exposed a native blur/change reentrancy error when a focused input was replaced; the mock now guards rendering and ignores that intermediate change event. The corrected suite observed no JavaScript errors or HTTP requests.
- Final-file matrix rerun: **660 layout combinations** (55 applicable pairs × 6 widths × 2 themes), zero page overflow, JavaScript errors or HTTP requests. Sizes: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and 844×390. **24 dialog keyboard scenarios** passed across these viewport/theme pairs: shopping Tab/Shift+Tab containment, Escape dismissal and trigger focus restoration; export Escape/focus return. All **3 motion profiles** are reachable through the template selector.
- Static assertions pass: **12 numbered sections, 49 unique visual criteria, draft status**, inlined kit, required labelled native selectors and no external resource references. Node `vm.Script` parsed both inline JavaScript blocks. Visually inspected in-memory screenshots of the dark desktop editor and Backing, light narrow export error and dark narrow shopping. The default Materials heading and first control fit at 1440×980. No screenshot file or additional design preview was written.
- Only the two authorized design artifacts and the required delegation RESULT.json were written. Production lint/types/tests/build, engine/tool parity, actual GLB export, portable Blender import, owner manual opening and complete WCAG conformance were **not run** here; they remain T3.2–T3.8 responsibilities after approval. No SPEC/PLAN, repository, separate changelog, other bitácora/memory file, installation, commit or deployment was changed by this task.
