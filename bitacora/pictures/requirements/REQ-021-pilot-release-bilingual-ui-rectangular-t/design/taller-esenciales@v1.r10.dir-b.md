---
name: Mesa en plano
contract: taller-esenciales@v1
revision: r10.dir-b
status: draft
kind: independent-exploration
subplan: SP-3
requirements: [R9, R10, R11]
source_plan_revision: 1
source_plan_schema: 1.3.0
owner: David
date: 2026-10-27
chosen_thumbnail: taller-esenciales@v1.r10.dir-b.html.candidate-1.html
---

# Mesa en plano — direction B

## 1. Identity and scope

Draft exploration for `taller-esenciales@v1`, **not the canonical contract and not approved for implementation**. The owner chooses a direction before finalization. Only this direction's six revision-specific artifacts and the required delegation result are written. No production repository, shared contract, SPEC, PLAN or historical revision is changed.

Behavioral authority: `taller-esenciales@v1.r10.behavior.md`, then SPEC “Behavior — SP-3 and SP-4 (round 9 answered)” and PLAN SP-3. Consumers identified by the supplied brief/plan: T3.1 design copy, T3.2 table creation/editing, T3.3 Backing, T3.4 export and T3.7 rendered review. Existing Blender geometry, AI tool parity, saved-scene compatibility and Shopify behavior remain engineering acceptance obligations; the static illustration cannot verify them.

## 2. Name, approach and fit

**Mesa en plano** puts the selected table's inspector directly below the existing Taller canvas. The table, its dimensions and its placed-chair count share one vertical axis. The original left rail and left catalogue remain recognizable. There is no new page, route, brand, palette or font.

The changed work area comprises the catalogue's group navigation/type cards, the canvas illustration, the inspector dock and export feedback. The spatial move is the downward inspector reveal after creation. Width goes to side-by-side Mesa and Sillas fieldsets instead of a narrow right inspector. The shopping list can occupy that same dock for rapid quantity checking; the header's existing shopping-list dialog remains available.

This suits an editor whose main job is placing an object and changing its parameters while seeing the result. On phone, the existing canvas-plus-sheet model becomes one switchable Añadir / Pieza / Lista de compra sheet, avoiding a long catalogue between creation and editing.

## 3. Two thumbnails and selection

Both compositions were built fresh from the brief and inspected as rendered 1280px screenshots before the full TSX was composed.

| Candidate | Composition | Decision |
|---|---|---|
| [Candidate 1](taller-esenciales@v1.r10.dir-b.html.candidate-1.html) | Left catalogue; canvas over a wide two-column inspector. | **Chosen.** Keeps creation and the selected object's controls adjacent without making the catalogue a horizontal strip. |
| [Candidate 2](taller-esenciales@v1.r10.dir-b.html.candidate-2.html) | Canvas beside a right inspector; full-width horizontal catalogue below. | Retained as exploration evidence. Its eight simultaneous cards use more width and push creation below the editing area. |

The full mockup corrects a weakness discovered in the first render of candidate 1: catalogue height must not stretch the canvas and push the inspector out of the first viewport. Desktop catalogue scrolling is independent; the canvas has a bounded height and the inspector grows naturally when warnings appear. The page can scroll for expanded feedback rather than clipping it inside a fixed-height inspector.

## 4. Fixed product system and source evidence

Read-only production surfaces: both repositories' `src/app/globals.css`; asesor `/3d` and `Taller3D`, `FondosYMuebles`, `EditorConjuntoMesa`, `Inspector`, `ListaCompra`, `ListaEscenografia`, `ExportarEscenaTaller`, furniture defaults/perimeter/catalogue and `ASIGNACION_FONDOS`. The Taller header retains its ring mark, Taller 3D label, scene context, undo/redo, Foto realista, Exportar and Lista de compra; Paneles retains Añadir, Piezas, Plantillas, Sala, assistant return and help. Non-SP-3 actions only identify their exploration boundary.

Sibling `cuentas-admin@v1.md/.html` and `proyectos@v1.md/.html` were read. Their bundled historical-looking HTMLs disagree on palette/fonts. The current cuentas-admin written contract explicitly resolves this in favor of production tokens and Geist. This direction follows that resolution, its compact account/language vocabulary and neutral active navigation, while retaining the route-specific Taller shell. It does not import proyectos' obsolete Work/Measure palette or its library-page rail.

| Existing source role | Kit / local role | Light / dark |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | card, popover | `#ffffff` / `#16181f` |
| `--texto` | foregrounds | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | muted foreground | `#6b6178` / `#9aa1ad` |
| `--texto-tenue` | input/control edge | `#766c85` / `#8a91a0` |
| `--acento`, `--sobre-acento` | primary, primary foreground | `#6d3fe0`, white / `#9479ff`, `#120b24` |
| `--borde` | decorative rules | `#e3daef` / `#383c48` |
| `--superficie-2` | neutral selected navigation | `#efe9f8` / `#242733` |
| `--taller-visor` | scene ground | `#ebe7f1` / `#1a1722` |
| `--taller-panel` | catalogue | `#faf9fc` / `#16131d` |
| `--taller-tarjeta` | inspector | white / `#1d1926` |
| `--taller-encima` | miniature surface | `#f3eefb` / `#231e2e` |
| Existing aviso/error/exito pairs | warning/error/success messages | Exact product values in the TSX; measured in both themes. |

The accessible primary and input mappings follow the finalized sibling's written mapping. Decorative rules keep their original lighter borders. Shapes retain Taller 10px controls, 12px cards and the sibling's rounded account disclosure. Controls are at least 44px high; panel padding is 24px desktop and 20px phone/tablet.

Actual production Geist Sans and Geist Mono Latin WOFF2 files from the local t12 Next build are embedded as data URIs. Geist is used for interface copy, Geist Mono for quantities/dimensions. The kit's default palette/fonts are fully remapped. Scene material colors are existing furniture values, not a second UI palette.

Actual installed components: `shadcn:button default|outline default|hover|focus|pressed|disabled`, `shadcn:input number|search default|focus`, `shadcn:skeleton loading`, and `shadcn:dialog shopping open|closed` with its installed Animate UI/Base UI enhancement, imported from `@/components/ui/{button,input,skeleton,dialog}`. Group/type/disposition/language selects, color inputs and disclosures are explicitly native controls. SVG scene, catalogue thumbnails and divided dock are custom compositions. `mountMockup/useMockup` and `useMotionProfile` come from the supplied real runtime. No HTML fallback, package installation or asset fetching was used.

## 5. Eight axes

| Axis | Direction B evidence |
|---|---|
| Concept | A spatial editing bench inside the existing Taller: chosen object above, parameters directly below. |
| Layout | 60px rail + 312px catalogue + canvas-over-inspector work area; catalogue becomes 340px at 1440px. `.work-body`, `.stage`, `.inspector-dock`. |
| Navigation | Original Paneles rail; native Grupo selector; Mesa y sillas / Lista de compra dock buttons; phone Añadir / Pieza / Lista de compra sheet. `.tool-rail`, `.group-select`, `.dock-nav`, `.mobile-sheet-tabs`. |
| Typography | Existing Geist; 24px catalogue title, 20px dock title, 14px field controls, mono quantities. `.catalog-panel h1`, `.dock-heading h2`, `.dimension`. |
| Density / shape | Two illustrated cards per row; three numeric measures together; two fieldsets side by side on desktop; divided flat surfaces with existing rounded controls. `.catalog-grid`, `.measure-fields`, `.inspector-grid`. |
| Components | Real buttons/inputs/loading skeleton/dialog, native group/type selectors, production table/default/perimeter data, custom schematic scene. No decorative dashboard tiles. |
| Colour | Exact production and finalized sibling token roles. Neutral navigation; existing accent for primary shopping/download controls and focus; status colors reserved for actual feedback. |
| Motion | Spatial settling from different origins: catalogue left, canvas right, inspector up, table down, chairs sequentially. Tactile hover/press and anchored export feedback. See §9. |

Machine-readable claims and rendered selector evidence are in `taller-esenciales@v1.r10.dir-b.json`.

## 6. Flows and data discipline

**Create and edit.** Open Fondos y muebles → Grupo Mesas → activate a type card → create its production default table and select it → move focus to the inspector heading → change measures/chairs → update the schematic, actual placed count and shopping-list lines from the same table data. Rectangular defaults are **240 × 90 × 75 cm**. Existing fixed pieces, including the Imperial pieces, remain available under their original catalogue names. Parametric cards show default dimensions to distinguish them from fixed entries. No paid AI request is made.

The static artifact imports existing `TIPOS_MESA`, `NOMBRE_MESA`, `PARTIDA_MESA`, `LIMITES_MESA`, `SILLAS`, `contornoDeMesa` and `repartirSillas` read-only. It does not duplicate a guessed capacity formula. The initial rectangular/Tiffany fixture requests eight and places eight; its capacity is ten. Capacity-exceeded state requests sixteen and places ten. At 300 × 90 cm, Tiffany capacity is twelve. Counts, drawn chair marks and list quantities derive from the same `puestos` result. Changing type uses the existing type's default measures; derived round/square/half-moon depth remains derived. Undo/redo restore complete mock scene snapshots; Ctrl+Z also works outside fields.

**Backing.** Select Backing → see exactly the seven required cards → add one and retain its original ID/name. Search matches original names and IDs across Fondos y muebles. Former groups are populated from the real catalogue with only those seven IDs removed. `ASIGNACION_FONDOS` is reused for shopping-list ownership; the visual move never changes a repository. The parametric media-luna card has a preview-only namespaced creation action so it cannot be mistaken for the existing `media_luna` Backing prop. Stored product identifiers are not redefined.

**Quantities.** Open the dock list or the header dialog. Furniture appears under Mobiliario, with quantities and dimensions and “no es producto de la tienda”. Scenery appears in its existing repository section. There are no rental prices, currency symbols or shopping charges. Table measures and chair measures remain separate.

**Export.** Open the existing header Exportar control → Descargar modelo GLB → preparing status and disabled repeated submission → completion or visible retryable failure. PNG remains in the existing menu. Pending/result feedback is directly after the canvas, before the inspector on all widths. Escape/Cerrar closes the non-modal export group and returns focus to Exportar. The shopping-list dialog uses actual modal containment and Escape dismissal.

Export is explicitly **simulated** in this static artifact: an action completes locally after 1100ms and does not download a fabricated GLB. The Estado selector freezes exporting/done/failed examples for inspection. No geometry, Blender validation, network, AI, server save or account operation is claimed. Scene/export values are clearly Datos de ejemplo.

## 7. Views and inspectable states

All native planning selectors remain visible with the Mockup label: Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` and Movimiento `motion`. Changing planning axes selects a fresh fixture; product interactions within a fixture share live data.

| Selector | Values and behavior |
|---|---|
| Vista | `mesas`, `backing`, `fondos`, `decorado`, `lista`, `exportar`. Seats also remain accessible through Grupo. |
| Estado | `normal`; `cargando` shows catalogue/inspector skeletons and disables export/list; `vacio` shows the no-result query and Limpiar búsqueda; `error` shows retryable catalogue failure; `capacidad` shows requested/placed warning and working Undo; `exportando`, `listo`, `fallo` show the corresponding export feedback. |
| Diálogo | Ninguno or `lista`; real shopping-list modal with quantities/dimensions and Cerrar. |
| Tema | Claro / Oscuro, using the fixed source token mappings. |
| Movimiento | Expresivo by default; Natural, Sutil and Quieto. OS reduced motion and `?still=1` also settle the layout. |

Search with no matches retains the existing scene and gives an actionable recovery. Catalogue failure does not erase the table. Export failure preserves the editor and offers Reintentar. Validation/capacity warnings distinguish requested chairs from actually placed chairs. These are local tool operations; new account permission-denied, offline/server-conflict or stale-account states are outside SP-3's brief and are not invented here.

## 8. Responsive rules

- **≥1024px:** retain the original rail and catalogue at the left; bounded 300px scene above the broad inspector. Mesa and Sillas are adjacent fieldsets. The catalogue scrolls separately. Additional warning/export content increases page height rather than clipping controls. At 1440px the catalogue grows to 340px.
- **640–1023px:** 60px rail, 264px catalogue and the remaining work area. Inspector fieldsets stack, numeric measures stay together, header actions wrap. No horizontal page scrolling.
- **<640px:** 20px side padding. Header wraps; existing panel icons become a horizontal row. Canvas precedes the export result and the switchable sheet. Creation opens Pieza and focuses its heading; catalogue is hidden while editing. The sheet's Lista de compra action opens the inline quantity view; the header button still opens its dialog. Measures use two columns with height on the next row, then chairs stack. No overlay obscures the numeric fields.

Spanish names and long original catalogue names wrap; no ellipsis hides the action or measured dimensions. Tablet 768px and phone/desktop 390/1280px were rendered. 320px is checked separately as a reflow boundary, not asserted from the 390px audit alone.

## 9. Interaction and motion detail

Spatial grammar uses the production spring-like `cubic-bezier(.34,1.4,.64,1)` and ease-out `cubic-bezier(.23,1,.32,1)`. Readable text stays opaque throughout. Panel/card entrances are 620ms expressive, 400ms natural, 220ms subtle; repeated controls are 180/150/120ms respectively.

| Behavior | Trigger / actual rendered evidence |
|---|---|
| Catalogue registration | 24px travel from left, `catalog-enter` on `.catalog-panel`. |
| Canvas registration | 16px travel from right, `stage-enter` on `.stage`. |
| Card placement | 12px travel and 1° settling rotation, 35ms per-card stagger, `card-arrive` on `.creation-card`. |
| Inspector unfolding | 28px upward settling, `dock-unfold` on `.inspector-dock`. |
| Table placement | 800ms, −16px and scale .97 → 1, `table-land` on `.table-projection`. |
| Chair placement | 650ms, 25ms offsets, 9px/scale settling, `chair-settle` on `.chair`; marks are actual calculated placed seats. |
| Hover / press / focus | Cards lift 4px and rotate −.6°; controls lift 2px and press 1px/scale .98; keyboard focus uses a 3px source accent outline. |
| Feedback | 480ms 10px/0.5° folding gesture, `feedback-fold` on capacity/export/status messages. |
| Export opening / progress | 360ms anchored 8px/scale opening; progress translates for a 1.5s cycle. Offscreen progress and all animations in hidden tabs pause. |

There is no decorative infinite ambient animation. `useMotionProfile` controls profile/reduced state. Quieto, OS reduced motion and `?still=1` remove animation/transitions and preserve final geometry, feedback and keyboard actions. The SVG's necessary layout transforms remain intact when reduced. A state change can be inspected without motion, and it never relies on color or movement alone.

## 10. Accessibility and visual acceptance criteria

Target: WCAG 2.2 AA for the added interface. Native labeled selects and number/search/color fields, real button semantics, 44px control heights, visible source-accent focus, semantic fieldsets/legends, polite count/status announcements and alert semantics for failures. Export is a named non-modal group, not an incomplete ARIA menu. Shopping-list modal uses the installed dialog primitive. Escape dismisses it; its opener regains focus. Custom SVG is explicitly a schematic image with a descriptive accessible name; all added actions are possible without manipulating its drawing.

| ID | Width / state | Observable criterion |
|---|---|---|
| B-01 | All / normal | Existing Taller header actions and Paneles vocabulary remain recognizable; no new identity is introduced. |
| B-02 | All / Mesas | Eight parametric type cards use original type names and production default dimensions; existing fixed/Imperial cards remain. |
| B-03 | All / create | A rectangular card creates 240 × 90 × 75 cm, selects it and reveals/focuses the inspector. |
| B-04 | ≥1024 / normal | Canvas and two-fieldset inspector share the same horizontal boundaries and 24px inset; the catalogue does not stretch the canvas. |
| B-05 | All / capacity | Requested sixteen at rectangular default results in ten actual Tiffany seats; warning, drawing and list agree. |
| B-06 | All / undo | Deshacer restores previous measures and actual quantities, including after a capacity warning. |
| B-07 | All / Backing | Exactly the seven required props appear once; none remains in the former two visual groups; original-ID search works. |
| B-08 | All / list | Quantities and per-item dimensions appear without prices; Mobiliario/Escenografía ownership follows the existing map. |
| B-09 | All / export | GLB pending, done and failure are inspectable; retry is actionable; repeated pending export is disabled; scene data is unchanged. |
| B-10 | <640 / editing | Canvas remains above the sheet; creating a table switches from Añadir to Pieza, rather than requiring scrolling through the catalogue. |
| B-11 | All / loading, empty, error | Loading uses skeletons; no-result recovery clears the query; load-error retry is visible and does not clear the scene. |
| B-12 | Both themes / all states | Text contrast ≥4.5:1, control edges ≥3:1, visible focus, aligned padding and no horizontal page overflow in the measured matrix. |
| B-13 | Reduced / all | Same final positions and actions; no animation remains active after settling; no essential meaning depends on motion. |

## 11. Verification and impact

The real toolchain built this direction offline with React, shadcn/Base UI and Animate UI, inlining CSS, JS, source geometry functions and two local fonts into one HTML. No CDN, external image/font or package installation is used.

Verification commands used the supplied absolute paths: `components mockup build` on this direction's TSX/output, `kit/contrast.py`, `UV_OFFLINE=1 uv run --offline --with playwright python kit/audit_mockup.py ... --max-combos 120`, and `kit/compare_directions.py`. The matrix contains 108 cases per width, so cap 120 does not sample it: 216 total planned renders at 1280/390, both themes, all six views/eight states and shopping-list scenes.

Final source/output build: **PASS**, 1015 KB self-contained HTML built offline from 2224 source files. Final HTML SHA-256: `a41c0577b6405ca6050a1bad3144980c1d6e89ff3e98924b73d357e9c795bc8d`.

`contrast: 158 pairs checked in light and dark, all pass`

`audit: taller-esenciales@v1.r10.dir-b.html — 216 renders (216 combinations planned), 11638 text measurements, 2375 focus stops`

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

This is the final complete matrix, not a sampled or pre-adjustment result. Earlier layout findings were repaired before this final run. No audit warning remains.

Twenty-six focused browser assertions passed: production rectangular defaults/capacity, creation and selection, resizing, capacity warning, derived quantity list, no rental prices, undo, seven Backing cards, distinct Media luna prop identity, original-ID search, former-group omissions, empty-state recovery, real dialog/Escape, export retry/completion and unchanged scene, responsive sheet selection and no page overflow at 390/768/1280. No browser exception or external HTTP(S) request occurred. The final export-placement/repository grouping adjustment also received a focused smoke check. **Nineteen additional checks passed**: all eight type defaults, dialog focus return, expanded native color controls and rendered contrast/padding/reflow at 320/390/768/1280px in both themes, OS reduced-motion override and `?still=1`. Closed advanced fields are explicitly absent from layout/focus until their disclosure is opened.

Rendered screenshots were inspected in memory: both thumbnails at 1280, full desktop light workspace, desktop dark capacity/Backing, light tablet Backing, phone dark piece sheet and phone light export failure. Screenshot files were not written outside the assigned artifacts.

**Final A/B/C rendered comparison: PASS**, `ok=true`, `evidence_ok=true`, no missing selector evidence. B versus A layout similarity is **0.072**; B versus C is **0.050**. Navigation, density and motion differ in both comparisons; all three pairs pass. Typography differences are reported by the tool but do not count toward distinctness. These measurements are a structural check, not an approval or a replacement for visual inspection. A single-direction evidence run also passed every declared selector claim.

Compatibility if selected: **breaking visual** for T3.2/T3.3/T3.4 due to inspector relocation, group selector and responsive sheet navigation; behavior/data identities stay governed by the shared brief. T3.7 must review the chosen final contract at the stated breakpoints. No SP-2/SP-4 contract, implementation or approval is changed by this exploration. This artifact cannot establish GLB metre transforms, base-color precision, Blender import or AI/manual parity; those remain their existing engineering checks.

## 12. Concerns and owner questions

The provided sibling HTMLs and written contracts are not visually consistent with each other. This exploration resolves token/font conflicts through the production sources and the current cuentas-admin written decision, while preserving the existing Taller-specific shell. The finalizer should use the same precedence.

Q: ¿Se conservan ocho sillas iniciales para todos los tipos de mesa paramétrica, limitadas por la capacidad real, o debe existir una cantidad inicial propia de cada tipo? Esta exploración conserva las ocho del conjunto actual.
Q: ¿Basta mostrar las medidas en las tarjetas paramétricas para distinguirlas de las piezas fijas que comparten nombre, o se debe añadir un rótulo de sección con copy aprobado? Esta exploración conserva los nombres originales y todas las piezas existentes.

The palette/font requests in older feedback are superseded by this round's explicit fixed-product-system instruction. Variation is therefore structural, navigational and kinetic. Approval of this draft, choice among A/B/C and canonical finalization belong to the owner and finalizer.
