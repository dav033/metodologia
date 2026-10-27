---
name: En la pieza
contract_target: taller-esenciales@v1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
revision: r10.dir-c
owner: David
approval: exploration only; no canonical contract changed
---

# En la pieza — direction C

This is an independent exploration, not an approved contract. The shared r10 behavior remains authoritative. No production repository, plan, sibling artifact, shared contract or history file was edited.

## Approach and selected thumbnail

Candidate 1 is selected: the table stays above its horizontal editing tray; its visible dimension targets take keyboard focus to the associated numeric fields. Candidate 2 keeps a floating vertical inspector to the right of the same scene, but consumes the horizontal space needed for long tables. Candidate 1 gives the changed controls a direct relationship to the piece and reflows the same fields underneath it on a phone. Both small HTML compositions were written before the complete TSX.

Reproduce the established Pictures/Sempertex ring-and-dot masthead, language/account entry, Taller scene header, Mis proyectos return, panel rail, Fondos y muebles and central scene. The horizontal selected-piece inspector changes only SP-3's allowed inspector surface. It keeps the existing type, dimensions, height, mantel and chair vocabulary, progressively disclosing secondary settings. The shell is shared; the exploration is in the placement and interaction of these changed controls.

Read-only sources: t12 `src/app/3d/page.tsx`, `Taller3D.tsx`, `FondosYMuebles.tsx`, `EditorConjuntoMesa.tsx`, `ListaEscenografia.tsx`, `CabeceraApp.tsx`, table/chair/catalogue data and `globals.css`; asesor `globals.css`, shared shell and `ExportarEscenaTaller.tsx` (the named export component is absent in t12). Both sibling canonical Markdown/HTML pairs were inspected; their written production-token mappings take precedence over older exploratory styling remaining in the proyectos bundle. SPEC's “Behavior — SP-3 and SP-4 (round 9 answered)” and SP-3's PLAN UI reference were read. This adds no new page, brand, palette or font family.

## Eight axes

| Axis | Direction-specific decision |
|---|---|
| concept | En la pieza: select the table, touch its dimensions and edit the selected set without leaving the Taller scene. |
| layout | Existing masthead and Taller toolbar above the 60px panel rail, 292px object catalogue and flexible scene; the changed inspector is a horizontal tray directly below the selected object, rather than a second sidebar. |
| navigation | Existing panel rail and Fondos y muebles groups; dimension buttons focus matching fields, Pieza discloses the inspector, and native details disclose the existing type/mantel/chair settings. Shopping list and export retain the surrounding scene. |
| typography | Embedded production Geist; 24px maximum title, 20px inspector title, 16px object hierarchy, 14px working text and tabular dimension values. No display font or new family. |
| density | Two-column object cards and four-column direct editing at desktop; two-column fields plus full-width chair stepper at phone. Flat selected-object strip joins canvas and inspector; 24px/20px work-area padding. |
| components | Installed shadcn/Base UI Button, Input and Skeleton, arranged as object cards, numeric dimension targets and a chair stepper. Native select/details preserve keyboard interaction; custom schematic SVG provides scene context. |
| colour | Fixed Pictures and scoped Taller tokens in both themes. Primary action/selection use existing acento; warning and failure use existing aviso/error. Control edges use the siblings’ texto-tenue alias; no new palette. |
| motion | Tactile press/settle grammar: profile-aware spring card placement, compressed table seating, staggered chair seating, rising inspector tray, lateral warning correction, receipt settling, export preparation sweep and confirmation stamp. CSS rebote (.34,1.4,.64,1), expressive 480/180ms; natural 300/140ms, subtle 160/100ms. Reduced/still removes travel and repeated animation. |

## Views, states and interactions

The native `view`, `state`, `scene`, `theme` and `motion` controls remain visible above the product, with the runtime's Mockup label. Scenes contains only “Ninguno”: this direction uses in-place disclosure, not a modal dialog.

- **Mesa seleccionada:** schematic scene → clickable cm/chair targets → selected-piece strip → inspector with length, depth, height and requested chairs. Dimension buttons open the inspector and focus the matching field. Close collapses it; Pieza restores it. Numeric inputs and +/- buttons provide keyboard alternatives; there is no mandatory drag gesture.
- **Tarjetas de mesas:** one creation card for each of the eight existing parametric types. A card selects its type's source default dimensions and opens the same inspector. Rectangular starts at 240 × 90 × 75 cm; the inherited eight-chair fixture is illustrative. The existing fixed Mesa imperial remains separately available.
- **Backing:** exactly one card per original ID: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico. Visible names are the catalogue's names, including Marco hexagonal metálico. Search accepts both the original ID and name. Adding a prop updates the schematic scene and shopping list. Repeated additions are separate placed instances, not duplicate catalogue cards.
- **Grupos anteriores:** Fondos y tapetes and Decorado de pie remain available, with representative remaining objects and none of the seven moved cards. The prototype is not a full catalogue reproduction. Backing is Taller-only; no Shopify categories or ownership/IDs are changed.
- **Lista de compra:** retains scene context and shows actual fixture quantities and dimensions, with “Mobiliario · no es producto de la tienda”. Mesa rectangular and Silla Tiffany use one shared edit model; no price, rental column or fabricated total appears. Tiffany's 45 × 45 × 90 cm comes from the existing chair source. Backing additions appear under their original names.
- **Exportar GLB:** idle action, disabled preparation, completion status, visible error and Reintentar. File generation is explicitly simulated: no network request, GLB, AI call or Blender import is performed. Existing PNG functionality is outside the changed GLB surface and is not redefined.

Declared native states: Normal; Cargando (catalogue/scene skeletons, disabled editing); Vacío (no selected scene object; creation remains possible); Búsqueda sin resultados (clear-search recovery); Error (catalogue retry, plus GLB recovery when export is selected); Capacidad excedida (24 requested versus placed/capacity with explanatory warning); Deshecho (restored default fixture); Exportando; Exportación lista; Exportación fallida. Export states belong to the export view. All are directly selectable. Table and prop fixture edits persist across view navigation, including the shopping list and simulated export. Changing the inspection state intentionally replaces the fixture; this is a planning control, not a product action. No permission, network-save or AI-loading state is introduced by SP-3.

The prototype illustrates one selected table set. Its capacity is an intentionally simplified fixture, not an implementation of `repartirSillas`; production must keep the existing geometry-based capacity, chair types, layouts, full catalogue, validation limits and scene history. Other table-type cards demonstrate source defaults and selection; detailed editing is specified here for rectangular tables. The catalogue and SVG are illustrative; table creation does not demonstrate a full multi-table 3D engine. Saved IDs, AI/photo discovery, paid-call independence and Blender fidelity require the engineering tasks; an HTML mockup cannot verify them.

## Design-system mapping and components

Colours map exactly to the sibling production mappings: background/foreground = fondo/texto; card/popover = superficie/texto; primary = acento/sobre-acento; hover = acento-hover; secondary/muted/accent = superficie-2; supporting text = texto-suave; decorative rules = borde; meaningful input/control edge = texto-tenue; ring = acento; success, warning and error = exito, aviso and error plus their existing soft fills. Scene surfaces preserve taller-barra/panel/visor/tarjeta/elegido. Dark scene caption uses the existing taller-medio value for readable supporting text. The product's scoped original dark toolbar primary is not used as text on a shared sibling primary button: shared buttons use sobre-acento.

Geist is embedded as a data URI from the existing t12 Next static Latin WOFF2 build asset (`caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2`). No font, package or asset was fetched. Existing shared pill actions, 14px rounded controls, generous rounded object cards, neutral navigation, visible three-pixel focus and 44px minimum controls are reused. Work-area padding is 24px desktop / 20px phone, on a shared left axis; no free-floating footer column.

| Source:id · variants/states | Installed import or custom composition |
|---|---|
| shadcn:button · outline/default/ghost · normal/hover/press/focus/disabled | `@/components/ui/button`, Base UI; Action wrapper maps product tokens |
| shadcn:input · search/number · normal/focus/disabled | `@/components/ui/input`, Base UI; associated labels, explicit units |
| shadcn:skeleton · catalogue/scene · loading | `@/components/ui/skeleton` |
| native:select · language/table/mantel/chair/layout | Labelled native controls, token-mapped edges |
| native:details · account/secondary inspector · closed/open | Summary keyboard disclosure; closed content removed from layout |
| custom:scene-target · selected/empty | Inline SVG, schematic source-token shapes; not a 3D renderer |
| custom:receipt/feedback · normal/warning/error/success | Semantic headings, quantity rows and status/alert regions |
| motion/react + @kit/motion | Installed Motion; useMotionProfile supplies spring/reduced state |
| @kit/mockup | mountMockup/useMockup; native planning selectors retained |

No HTML fallback was used. The two thumbnail compositions are sketches, not substitutes for the real-component full mockup.

## Motion and responsive detail

The selected table compresses and settles (480ms rebote), chairs seat individually at 25ms offsets, catalogue cards register with the profile spring, the inspector tray rises 18px into place, warnings correct laterally by 8px, the receipt settles 10px, export preparation sweeps and its confirmation stamps into place. Buttons lift 2px on hover and compress to .96 on press, with 180ms transitions. Natural/subtle shorten these durations; text does not fade away or pass through a low-contrast frame. All motion evidence selectors in JSON point to elements that actually animate or transition.

OS reduced motion, `?still=1` and the native Quieto profile remove displacement, repeated work animation and hover/press travel, with immediate final feedback and all controls intact. Hidden tabs pause CSS animation. There is no infinite ambient decoration or offscreen effect to suspend. Scene motion is schematic feedback, not a promise that export changes the editor.

Breakpoints: above 1100px the 60px rail and 292px catalogue accompany the scene, with four direct-field columns; 761–1100px uses a 252px catalogue and two direct-field columns; 360–760px uses the same header, a single Añadir/Pieza/Backing panel row, then scene/inspector, followed by the catalogue. The desktop rail is hidden on phones to avoid duplicate panel controls. Chair controls span both phone columns. Shopping quantities and dimensions stack on tablet/phone. No side sheet covers the selected table. Standard document scrolling keeps every control reachable. The language selector is shell context; this SP-3 exploration's content remains Spanish, as requested by the behavior brief; EN translation belongs to the later copy task.

## Observable visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-01 | 1101px+ | normal | Existing masthead and Taller toolbar precede the rail, catalogue and central scene; no new application page or brand appears. |
| C-02 | 761px+ | selected | Inspector fields form one horizontal tray immediately below the selected-object strip; clicking a dimension focuses the corresponding field. |
| C-03 | 360px+ | creation | Eight parametric type cards exist, rectangular creates 240 × 90 × 75 cm, and fixed Imperial remains available. |
| C-04 | 360px+ | edited | 300 × 100 cm / 12 requested chairs appears consistently in scene labels and shopping quantities after opening the list. |
| C-05 | 360px+ | capacity | Requested and placed quantities differ explicitly; warning explains the chairs that did not fit. |
| C-06 | 360px+ | undo | Deshacer restores the preceding edit and the shared scene/list values. |
| C-07 | 360px+ | Backing | Seven original-ID cards appear once, with original names; none appears in previous groups. |
| C-08 | 360px+ | no-results | Search shows Sin resultados and Limpiar búsqueda restores cards. |
| C-09 | 360px+ | list | Furniture quantity and dimensions appear without rental prices. |
| C-10 | 360px+ | GLB pending/failure/success | Preparation disables the action; failure exposes retry; success explicitly identifies mockup simulation. |
| C-11 | 360–760px | normal | Single mobile panel navigation precedes the scene; fields reflow without page overflow. |
| C-12 | 360px+ | both themes | Control edges, keyboard focus and text remain measurable against their actual mapped surfaces. |
| C-13 | 360px+ | reduced/still | Controls/content remain present without running travel or repeated preparation animation. |

## Evidence and concerns

Builder: real installed offline workspace, 96/96 component entries available; output bundles 2031 source files, approximately 530 KB. Contrast checker: `contrast: 158 pairs checked in light and dark, all pass`. First full audit identified seven padding findings caused by closed native-details descendants retaining layout boxes; explicitly removing closed content from layout fixed them. The final revision also compacts the canvas and mobile navigation and keeps table edits across view changes.

Final audit on the final HTML: **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**. Measured 240/240 planned view/state/theme/width combinations, 12,524 text measurements and 4,182 keyboard focus stops. `compare_directions.py A.html B.html C.html --json` exited 0: ok=true, evidence_ok=true, no missing selectors; A/C layout similarity 0.042, B/C 0.048, with distinct navigation, density and motion. All three pair comparisons passed. The initial comparison identified two state-only selectors that its view-only traversal could not reach; JSON evidence now points to genuine animations/transitions in its measured views. No visual or behavioral change was made to obtain that selector check. Screenshot inspection: 1280px light/dark and 390px light/dark, plus 820px rendered probes; screenshots remained in memory and no unassigned files were written. Focused browser smoke passed table creation, 300 × 100 cm / 12-chair edit, list persistence, undo, seven Backing cards/add, simulated export success and failure/retry, with zero page errors. Rendered probes at 1280/820/390 in both themes found no contrast, nontext, alignment, padding or overflow findings.

These checks do not establish WCAG conformance, real GLB geometry/colour preservation, paid-call independence, AI discovery or production keyboard/screen-reader behaviour. Production components, export/Blender checks and translation remain with their assigned implementation tasks. Shared shell navigation outside SP-3 only announces its existing destination in the mockup; it does not implement other subplans.

## Impact and open decisions

Target remains taller-esenciales@v1, **draft**. SP-3 binds version 1, design-copy T3.1 and visual review T3.7; affected UI consumers are T3.2 (table inspector/cards/list), T3.3 (Backing) and T3.4 (export surface). This exploration is a proposed breaking visual arrangement of the existing inspector and phone hierarchy; behavioral requirements and format/identity compatibility are unchanged. Only an owner-selected finalizer may write the canonical contract; no separate changelog is permitted by this delegation.

Q: Owner — Do you confirm the inspector beneath the selected scene, with click-to-focus dimension targets, rather than retaining the current lateral inspector?
Q: Owner — Should the changed numeric dimension fields display centimetres as shown here, or retain the existing inspector's metre presentation? Stored dimensions and GLB metres are unchanged.

Assumptions: the source's eight-chair creation example is retained solely as a mock fixture; full parametric defaults stay source-owned. Existing shell account/language/project behavior belongs to the sibling contracts. No approval is inferred from a passing audit.

Final HTML SHA-256: `e32ffa0f15c775ed670cdddaafe0a12e2dbeedd924eef89c05755805f03c6e65`.
