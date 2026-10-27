---
name: Mesa de montaje
status: draft
subplan: SP-3
contract_candidate: taller-esenciales@v1
revision: r6
direction: b
requirements: [R9, R10, R11]
created: 2026-10-26
---

# Mesa de montaje — direction B

Independent kinetic/spatial exploration, not the canonical contract. No direction or contract is approved here. Source of product behavior: `taller-esenciales@v1.r6.behavior.md`, checked against SPEC.md, PLAN.md and PLAN.json SP-3 / T3.1–T3.8. The owner chooses a direction before a finalizer writes the twelve-section canonical contract. This delegation only owns its two thumbnails, TSX, built HTML, this note and the eight-axis JSON, plus the required delegation result.

## Concept and memorable move

The Taller is a place to assemble an event: a rectangular tabletop, Tiffany chairs, round panels, metal hoops, pedestals and a balloon rig. Its working surface becomes a measured assembly stage. The selected table settles onto an axonometric floor, Backing lifts into position a beat later and the inspector squares against a registration corner. Dashed dimension leaders resolve around the arrangement. Motion expresses putting physical things into place; it does not move a field while someone enters a value.

The memorable move is **the selected object settling inside its measurement brackets while its inspector aligns against a physical square**. The scene remains readable from the start. There is no drag-only interaction, orbit gesture or hidden hotspot. Standard text-labelled buttons provide all the exploration's actions.

Why this is not the default: the central surface is an actual event arrangement rather than a dashboard, the navigation is a slim vertical sequence of tool stations rather than generic page tabs, and its working folio is open along ruled sections instead of stacked cards. Only peer objects use a small illustrated shelf. Typography places the editable physical measurements above supporting metadata. The composition derives its identity from the product's materials and verbs.

## Two thumbnails, made first

1. `taller-esenciales@v1.r6.dir-b.html.candidate-1.html` — **chosen: Mesa de montaje.** Separate tool spine, generous scene and right inspector. Selection follows visual inspection of both thumbnails at 1150 px. The stage and the form have stable, independent reading areas and a common top edge.
2. `taller-esenciales@v1.r6.dir-b.html.candidate-2.html` — Escenario por capas. Scene labels become tilted physical tags on the floor. Rejected because floating panels compete with the objects and make longer inspector content less stable. It also approaches the physical-pass language already explored in SP-2.

These are intentionally small, standalone visual compositions. They use inline HTML/CSS/SVG and system light/dark preference. The full chosen mockup uses the real library builder, explicit native selectors and complete behavior/state fixtures.

## Look ledger and shared identity

Read sibling `cuentas-admin@v1.r7.dir-a.md`, `dir-b.md` and `dir-c.md`. Shared Pictures identity is retained through the Taller palette, restrained system sans, ordinary controls, invitation-only account context and physical balloon-decoration objects. SP-2 B already uses a hinged access pass and a persistent bottom dock; neither composition nor navigation is repeated. SP-2 C uses roster/credential compositions; this direction centres scene geometry and orthogonal measurement. The stage here is the actual work surface, not an access-screen illustration.

Project evidence, read-only in both `t12` and `pictures`/`asesor`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `FondosYMuebles.tsx`, `EditorConjuntoMesa.tsx` and `src/lib/globos3d/mobiliario-conjunto-tipos.ts`. The tables' eight names, defaults, dimension bounds, chair types and arrangements come from that source. Pictures owns the existing export UI; this exploration does not move source ownership.

## Eight axes

| Axis | Concrete direction |
|---|---|
| Concept | A measured assembly stage for the table, actual placed chairs and Backing arrangement. Physical objects and registration brackets replace generic dashboard decoration. |
| Layout / composition | At 1280 px: 112 px tool spine, flexible scene, 350 px folio, 24 px gaps. The scene's heading, illustration and scale footer occupy one frame. The inspector and stage share the top alignment; the page footer aligns to the stage's left edge and folio's right edge. |
| Navigation | Six text-and-icon vertical tool stations: Mesas, Medidas, Backing, Lista de compra, IA de escena, Exportar. The active button has a neutral edge and offset bracket. Named header triggers open an actual Dialog and Popover. Mobile uses a 3-column tool grid, not a bottom dock. |
| Typography / scale | Shared system sans; project title 24 px, folio heading 26 px, section title 16 px, copy 13–14 px. Dimensions are monospaced 24 px and the placed-chair total is 32 px. Scene dimensions are 14 px SVG text; list counts use tabular figures and right alignment. |
| Density / shape | Open scene, compact ruled folio and a two-column peer-object shelf. Inspector padding 26 px, desktop structural gaps 24 px, phone gutters 20 px and panel padding 24 px. Controls are at least 44 px tall; numeric controls are 56 px. No nested card stacks. |
| Signature components | Custom SVG event stage and measurement leaders; bracketed tool station; squared folio; real shadcn/Base UI fields and buttons; Animate UI shopping Dialog/export Popover. Thumbnails are source-derived silhouettes, not remote stock images. |
| Colour logic | Pictures Taller surface tokens: light panel #faf9fc, card #ffffff, scene #ebe7f1; dark panel #16131d, card #1d1926, scene #1a1722. Primary pair #6d3fe0/#ffffff in light and existing accessible #b9a4ff/#120b24 in dark. Strong control edges use Taller medio; decorative dividers use Taller borde. Lavender materials are scene data, not navigation paint. |
| Motion | Expressive spatial spring stiffness 220/damping 16/mass .9: table drops into place, Backing rises with the profile's .09 s stagger, folio squares from a small rotation and horizontal offset. Rulers resolve over 520 ms with cubic-bezier(.34,1.4,.64,1); objects lift 4 px/tilt 2° on hover, tool stations shift 3 px. Controls use 200 ms feedback. Natural/subtle profiles reduce travel/timing. Reduced motion and `?still=1` show final geometry and retain the same actions. |

The sibling JSON names rendered selectors for composition, navigation, typography and motion. They were tested with the kit's actual EVIDENCE probe; every selector passed. `.dimension-line` has a finite CSS keyframe; `.object-card .mini-stage` and `.tool-spine button` have actual hover transitions. Motion is not claimed solely from a library import. Active expressive animation timelines were observed in Chromium.

## Behavior retained and illustrative boundaries

- **Mesas / `tables`:** eight parametric type cards, rectangular first with 2.40 × 0.90 × 0.75 m source default. One click creates the selected fixture and opens its inspector; no pre-creation form. All eight source defaults and valid inspector bounds were checked. Fixed Imperial pieces remain part of existing Mobiliario, outside the changed shelf.
- **Medidas / `table-editor`:** source dimension ranges and unit labels, requested chairs, placed count, seven chair types, five dispositions, tablecloth and named material colour. Last valid geometry survives invalid input. Deshacer restores the previous fixture. Numeric editing keeps focus. The capacity fixture illustrates 8 placed at 2.40 × 0.90 m and 12 at 3.00 × 1.00 m; production must use the existing perimeter engine, not this example formula. Changing a partial request from 12 to 4 resolves the warning and counts 4 in the list.
- **Backing / `backing`:** exactly seven original IDs, each addable: `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. Preserve the name “Marco hexagonal metálico” and discovery alias “aro hexagonal”. The alias matches only its appropriate card; original-name search remains available. No separate Shopify route, duplicate card or repository/semantic-ID migration is proposed.
- **Lista / `shopping`:** ruled actual quantities and dimensions, no rental price or invented total. Both the full view and real modal consume the same selected table, placed chairs and grouped Backing fixtures. Modal title and description are programmatic; Escape closes and returns focus to the invoking control.
- **IA / `ai`:** prompt, local illustrative proposal, explicit apply/discard and manual editing path. No paid or other AI call. The production `agregar_mesas`, `cambiar_mesas` and `cambiar_sillas` must use the same existing scene operations as manual editing; this mock does not prove their parity.
- **Exportar / `export`:** GLB/Blender handoff, scale in metres, import steps and lighting/material limitations. Header Popover retains existing PNG as a sibling and opens the full GLB handoff. Pending blocks duplicate export; partial/unresolved pieces block export; error keeps the scene and offers retry; empty explains why a piece is required. Completion says “Descarga GLB iniciada”, explicitly simulated. This artifact never emits a fake GLB or claims Blender verification.

Scope of the fixture: one selected table illustrates defaults and edits; replacing the selected table during type-card exploration does not prescribe replacing an existing scene table in production. Multiple tables, actual 3D manipulation, arbitrary prop geometry/materials, saved IDs, AI/photo recognition, GLB generation and real Blender import remain implementation responsibilities. The SVG is an illustration of the selected rectangular workflow, not a second 3D engine. No server save is inferred from local edits. Spanish copy is used here as in the shared draft; SP-8 owns ES/EN rollout. Native labels and layout use wrapping and flexible tracks rather than fixed text widths.

## States, dialogs, reflow and access

Visible planning chrome retains **Mockup**, native `view`/Vista, `state`/Estado, `scene`/Diálogo, `theme`/Tema and `motion`/Movimiento. All eleven state IDs remain selectable. Scene options are Ninguno, Lista de compra and Exportar. The planning selectors deliberately remount a view/state example; theme and motion preserve component state. Cross-view fixture values remain local to the page session, never a persistence claim.

| State | Visible manifestation and recovery |
|---|---|
| `ready` | Stable scene, named tools, relevant working content. |
| `loading` | Content skeletons in the folio with a loading label; scene and shell retained; content-dependent actions absent. |
| `empty` | No-match library with Limpiar búsqueda, no selected table with Ver mesas, empty list/scene or disabled GLB with explanation. AI keeps an editable prompt without prior conversation. |
| `error` | Contextual error, prior scene retained and Reintentar. No stack trace or fabricated export file. |
| `success` | Named completed example; export specifically reports initiated download and simulation. |
| `validation` | Relevant to numeric editing and AI. Linked field error/invalid state and recovery. Other views retain their ordinary content rather than inventing validation behavior. |
| `disabled` | Adjacent readable reason; content-changing buttons disabled. The informational list remains readable. |
| `partial` | Relevant to table capacity, unapplied AI proposal and unresolved export. Shows requested/placed values or explicit blocked-export explanation. Other views do not invent partial-catalogue semantics. |
| `permission-denied` | No private scene, project title, shopping content or file action; return affordance with SP-1/SP-2-owned destination. |
| `offline` | Retained local scene, local fields/list and loaded GLB available. Remote library add/refresh and AI disabled; Reintentar does not claim server save. |
| `pending` | Relevant to AI/export, with named pending copy and duplicate-submit prevention. Other views do not create a new asynchronous operation. |

Responsive composition:

- **320–359 px:** 20 px outer gutters, two-column tool grid, one-column fields and shelves. No horizontal page scrolling.
- **360–767 px:** tool grid in three columns, scene then active folio in document flow, two-column measurements/shelf where they fit. Full-size form controls, 24 px folio padding. Dialog width viewport minus 40 px and bounded vertical scrolling; Popover also fits this inset.
- **768–1100 px:** 82 px tool track, flexible scene, 310 px folio, 16 px structural gaps and 24 px outer gutters. Scene labels stack when space is tight. No reduced font below 11 px.
- **1101–1439 px:** 112 px tool track, flexible scene, 350 px folio, 24 px gaps and 32 px outer gutters.
- **≥1440 px:** 128 px tools, flexible scene, 380 px folio, 28 px gaps and 30 px folio padding; workspace capped at 1600 px.

The layout has intentional vertical document scrolling for long shelves/inspectors; it does not hide the footer under a fixed sheet. Whole-page reflow was checked at 320, 360, 390, 768, 1024, 1280 and 1440 px in both themes across all six views. Theme-specific native inputs/selects have explicit edge tokens; this subplan has no checkbox and does not introduce the unreadable checkbox treatment from the old feedback.

Accessibility targets are WCAG 2.2 AA for the changed surface: semantic navigation/buttons/headings, visible field labels, units/ranges and linked errors, 3 px visible focus, normal text ≥4.5:1 and control boundaries ≥3:1. Numeric/list editing provides a non-canvas path and the scene has an accessible summary. Status and errors are announced. Real modal behavior supplies focus containment, Escape and return; export Popover remains nonmodal. Reduced-motion/still mode retains all content/actions with final transforms; there are no infinite decorative effects. Dynamic preference changes also force the final visible geometry. This is a rendered mockup check, not full WCAG certification or an accessible authoring-engine implementation.

## Visual review targets for this direction

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| B-01 | 1101–1439 px | ready | Tools, scene and folio occupy three unequal tracks with aligned top edges. |
| B-02 | ≥768 px | ready | Footer left edge matches the scene; right edge matches the folio. |
| B-03 | 320–767 px | ready | Scene and folio stack without horizontal page scrolling. |
| B-04 | All | ready | Rectangular creation opens the inspector with 2.40 × 0.90 × 0.75 m. |
| B-05 | All | partial | Requested and placed chair counts appear together. |
| B-06 | All | partial | Reducing request to four updates the list to four placed chairs. |
| B-07 | All | validation | Invalid numeric input retains the last valid scene measurement. |
| B-08 | All | ready | Backing shelf has seven distinct original entries once each. |
| B-09 | All | ready | Searching “aro hexagonal” isolates Marco hexagonal metálico. |
| B-10 | All | shopping | Closing the shopping modal with Escape restores focus. |
| B-11 | All | pending | GLB action cannot be invoked again during preparation. |
| B-12 | All | success | GLB feedback states initiation and makes the simulation explicit. |
| B-13 | All, both themes | ready | Input/select edges and keyboard focus remain visible against their surface. |
| B-14 | All | reduced motion | Table, Backing and folio show final transforms and retain equivalent controls. |
| B-15 | All | permission-denied | No project or scene data is shown. |

## Components, build and honest verification

Real installed component provenance:

| Source / id | Variant or use | Import |
|---|---|---|
| shadcn/Base UI `button` | default, outline, ghost; disabled/feedback/navigation | `@/components/ui/button` |
| shadcn/Base UI `input` | search and numeric dimensions; invalid/disabled | `@/components/ui/input` |
| shadcn `textarea` | prompt | `@/components/ui/textarea` |
| shadcn `alert`, `skeleton` | state feedback and stable loading | `@/components/ui/alert`, `@/components/ui/skeleton` |
| shadcn/Animate UI `dialog` | shopping list, actual modal | `@/components/ui/dialog` |
| shadcn/Animate UI `popover` | export group | `@/components/ui/popover` |
| custom compositions | measured SVG stage, silhouettes, squared folio, native product selects and HTML table | direction TSX; no uninstalled library claimed |
| runtime / motion | native planning selectors, profile-aware springs | `@kit/mockup`, `@kit/motion`, `motion/react` |

Role mapping reuses `--taller-panel`, `--taller-tarjeta`, `--taller-visor`, `--taller-texto`, `--taller-medio`, `--taller-borde`, `--taller-primario`, `--taller-acento`, `--taller-sobre-acento`, `--taller-peligro` and `--taller-valido`. The dark action mapping deliberately uses the existing readable acento/sobre-acento pair. `--scene-line` is a proposed decorative grid alias, not a functional control boundary. Source theme/token files are untouched. Existing shared identity takes priority over the kit's default mauve values.

Built offline with the absolute `bitacora.py components mockup build` command named in the brief. Builder: approximately 635 KB, 2187 source modules, inline JS/CSS/fonts, real library marker. The toolchain was available; no HTML fallback, package installation or fetched asset was used. The two small thumbnails are deliberate exploration sketches, not stand-in claims about real components.

Verification record:

- Token contrast: `contrast: 158 pairs checked in light and dark, all pass`.
- Initial sampled audit found two dark recovery-button text contrasts at 4.12:1. Fixed the real outline-button surface and foreground together. Full subsequent runs passed; the final immutable-output run is recorded below.
- Interaction checks passed creation/inspector handoff, numeric focus retention, 3 × 1 m / 12 chairs, shared modal list, Escape/focus return, undo, invalid-value scene retention, seven Backing cards, original/hexagonal alias search/add and export Popover dismissal. A broad alias assignment was caught and corrected. A count assertion that expected the modal DOM to be immediately removed was corrected to await hidden state because the real primitive retains exit DOM.
- All eight type cards handed off valid source-default dimensions; capacity recovery 12 requested → 4 placed updates the shared list. Zero JavaScript page errors and zero HTTP/HTTPS requests in the interaction/reflow run.
- 84 normal view/theme/width reflow combinations passed at seven widths. All JSON evidence selectors passed the kit's real probe. Expressive animation timelines were observed; final visible transforms under a dynamically changed reduced-motion preference are `none`.
- In-memory screenshots inspected: both thumbnail compositions; 1280 light inspector; 1280 dark Backing and tables; 390 dark inspector and shopping modal; 390 light export. No screenshot files were written outside this task.
- Final immutable-output full audit: **312/312 renders**, 12,637 text measurements and 1,537 focus stops at 1280/390 px, both themes, every declared view/state plus both dialog scenes. Exit 0.

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Final audited HTML SHA-256: `49c8ada09dd1eacbee30d523108d628e68458816cc0e20c83d9fdeaefdc01734`.

No A/B/C similarity verdict is claimed; sibling exploration comparison belongs to the owner/planning comparison. No actual GLB, Blender executable, AI provider, production build, persistence, server permission or saved-scene compatibility was tested. Portable Blender setup is already settled by round 9; implementation T3.5/T3.6 must provide real import evidence and the owner opening, never substitute this screenshot audit.

## Impact, decisions and concerns

**Compatibility:** breaking visual relative to the prior unapproved composition, functionally/data compatible with the shared SP-3 behavior. If chosen, T3.2 adapts table/editor/list/AI composition, T3.3 the Backing shelf and T3.4 the export surface. T3.1 copies the eventual owner-approved canonical bytes; T3.7 must re-render this structure. T3.5/T3.6/T3.8 retain engine/export verification scope. No other subplan, source repository, plan, contract version or approval state is changed. This note is not an implementation approval.

**Open behavioral questions:** none discovered in this snapshot. The round-9 decisions about per-type default creation, no rental prices, single seven-piece Backing group and portable Blender verification remain settled. Direction selection and the plan/contract approval remain with the owner; neither is requested or granted by this exploration.

**Concerns:** single-selected-table/illustrated capacity are mock boundaries; only the real engine determines placement and export. Spanish-only copy here inherits the shared draft; SP-8 owns complete bilingual production copy. Complete screen-reader/zoom review, cross-subplan integration and Blender import remain future evidence. The final rendered audit passed; owner selection and approval remain pending.
