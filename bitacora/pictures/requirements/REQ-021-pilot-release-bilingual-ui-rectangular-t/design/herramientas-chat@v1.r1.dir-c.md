---
contract: herramientas-chat
version: 1
status: draft
subplan: SP-7
direction: c
name: Mesa editable
source_behavior: herramientas-chat@v1.r1.behavior.md
owner: David
---

# Mesa editable — direction C exploration

## 1. Identity and traceability

Draft exploration for herramientas-chat@v1, not the canonical contract and not approved for implementation. R13/R16; SP-7 UI consumers T7.1, T7.5–T7.8 and T7.10. The owner chooses a direction before a finalizer authors the shared twelve-section contract. This delegation changes only its six revision-specific design artifacts and its required delegation result.

Scope source: `herramientas-chat@v1.r1.behavior.md`. SPEC/PLAN are contextual; the live Planner may change them. Source inspected read-only: both supplied repositories, t12 globals.css/layout.tsx, CabeceraApp/MenuApp, VistaGuiada, CotizacionProfesional/CampoGanancia, IdeasDelAsistente/Biblioteca; sibling cuentas-admin@v1, planes@v1 and proyectos@v1 Markdown and built HTML. Their shared masthead, horizontal navigation, rounded working papers, fonts, control shapes and token mapping govern. The selected proyectos r12 direction-C source provided the shared CSS mapping and local font imports only. Existing unrelated repository/HQ modifications were preserved.

Compatibility: **undetermined until owner selection**. This is a proposed SP-7 composition, not an amendment to approved sibling behavior. No other subplan is redirected; no PLAN, canonical contract, changelog, production source, repository tests or project memory is written under this narrow delegation.

## 2. Purpose and users

The signed-in person opens an allowed tool, counts balloons without seeing prices, optionally carries materials into the existing professional quote, or opens a ready-made decoration in Taller. Master Designer and staff hold the explorer; a direct denied calculator/gallery/workshop route shows Sin acceso. Plan names never appear as an upgrade invitation. Every mock quantity, price, tolerance, decoration label and diagram is explicitly sample data, not an engine/catalogue result.

## 3. Approach, hierarchy and chosen thumbnail

**Chosen: candidate 1**, `herramientas-chat@v1.r1.dir-c.html.candidate-1.html`. Both candidates were drawn before the full TSX. Candidate 1 puts the visible decoration and editing disclosure beside the purchase result; candidate 2 gives the form a full-width strip before the preview/result. The first keeps the control/effect relationship together with less eye movement between distant sections. Both are small compositions in the existing shell, not alternative branding.

The change is in the working area: measurements unfold under the sketch; prices edit in their material row; expenses unfold in the same quote; a decoration preview opens inside its own band. No editor, professional-quote rule or guided conversation redesign is proposed. Home remains permitted tool cards opening separate pages; the special first spanning card gives chat its inherited normal-chat entry role without a marketing hero.

### Eight axes

| Axis | Rendered expression |
|---|---|
| concept | Mesa editable: act on measurements, material prices and decoration previews where their effect is seen, keeping the existing Pictures product shell. |
| layout | Desktop counter is a 1.45:1 working paper with a schematic/measurement surface beside the shopping result; calculator is full-width editable rows followed by an inline totals band; gallery uses expandable horizontal object bands, not a card grid. Home uses two columns with the first tool spanning both. |
| navigation | Inherited neutral horizontal routes, three in-place counting-method buttons, an explicit measures disclosure, inline expense disclosure and single-expanded decoration preview; each home card still opens its own existing/new tool page. |
| typography | Existing embedded Geist Sans / Geist Mono. The inherited page heading is 24px, object headings 20px, body 15px, supporting copy 12–14px and count 28px with tabular figures; no font or identity change. |
| density | 28px working insets and 20–28px gaps; a continuous professional quote with ruled input rows; gallery bands disclose one full preview at a time. Phone uses 20px insets, stacked fields and full-width object flow. |
| components | Installed shadcn/Base UI Button, Input, Skeleton and Animate UI Dialog, recomposed as in-place measurement controls, editable material rows and expandable decoration bands; native selectors/details preserve the sibling vocabulary. |
| colour | Exact Pictures fondo/superficie/texto/acento and Taller surface tokens; existing sibling texto-tenue alias for control edges. Primary colour marks one main action, navigation remains neutral. Both existing themes are mapped to kit roles. |
| motion | Tactile press/settle: 520ms compressed-paper/object registration with 35ms offsets, 170ms press feedback, 2px/0.965 pressed buttons; diagram settle and preview hinge use cubic-bezier(.34,1.4,.64,1). Natural/subtle use 320/140 and 160/100ms. Motion spring uses the installed profile. Reduced/still removes travel and retains every control; hidden/offscreen repeating effects pause. |

## 4. Fixed design system and components

Production tokens and the siblings' accessible role mapping are retained exactly:

| Project token | Kit role | Light / dark |
|---|---|---|
| --fondo | background | #faf9fc / #0b0c10 |
| --superficie | card, popover | #ffffff / #16181f |
| --texto | foreground | #1c1425 / #f4f5f7 |
| --texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| --superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| --acento | primary, ring | #6d3fe0 / #9479ff |
| --sobre-acento | primary-foreground | #ffffff / #120b24 |
| --acento-hover | primary-hover | #5530b8 / #a58dff |
| --borde / --borde-suave | decorative edge / rule | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| --texto-tenue | input/control edge | #766c85 / #8a91a0 |
| --exito, --aviso, --error | success, warning, destructive | Existing globals.css theme values |
| --taller-visor | schematic / existing Taller scene surface | #ebe7f1 / #1a1722 |

Panel 32px, inset 24px, field 18px and pill 999px match sibling contracts. Body and mono fonts are the actual local t12 Geist WOFF2 assets, inlined by the offline builder. No palette/font identity is added. Diagrams use existing UI surface tokens rather than inventing balloon colour swatches; colour names in the result are authoritative labels. Schematics are explicitly not real decoration thumbnails or a 3D renderer.

Components: `shadcn:button default|outline normal|hover|focus|pressed|disabled` from `@/components/ui/button`; `shadcn:input number|text normal|focus|edited` from `@/components/ui/input`; `shadcn:skeleton loading` from `@/components/ui/skeleton`; `shadcn:dialog unsaved open|closed` from `@/components/ui/dialog` (installed Animate UI/Base UI implementation). Native select, textarea, file input and details/summary are named honestly; the sketch, working paper, purchase table, inline quote rows and decoration bands are custom compositions. `mountMockup/useMockup` and `useMotionProfile` are used from the installed runtime. No package installation, CDN, fetched asset or HTML fallback.

## 5. Navigation and interaction

Preserve Pictures/Sempertex, language/account controls and neutral horizontal navigation. Product routes are `/`, `/asistente`, `/contador`, `/calculadora`, `/3d/decoraciones`, and `/3d?decoracion=<id>`; the prototype simulates them locally without network requests. Existing catalogue, projects, account, plans, theme/language rollout and workshop controls remain context, not new pages in this direction. Context-only controls identify their destination instead of fabricating product operation. Account-fixture selection is external Mockup inspection chrome, never a production role switch.

Home omits tools without permission, rather than showing locked cards. Counter has Formulario/Frase/Foto buttons and Editar medidas disclosure. Opening the costs tool carries the mock material result and shows Materiales del contador. Quote rows expose package quantity and editable price; expenses are a native disclosure; Tu ganancia preserves the existing formula's meaning. Totals are hidden pending calculation after editing. The expense grid uses four columns on desktop, two on tablet and one on phone. The existing professional component's other supported modes, purchase provenance and exclusions must survive implementation; only the package example is shown here.

The explorer keeps search, occasion and size filters above expandable object bands. Vista previa/Ocultar vista previa changes one band in place. Opening without dirty work enters a new unsaved scene. With unsaved work, Cancelar keeps it; Guardar y continuar requires server-confirmed save before opening; Descartar escena y continuar is explicit. The mock simulates success only and labels the server dependency. No current project is overwritten. Unknown links show Decoración no encontrada and leave the open scene intact. Deep links use real catalogue identifiers in production, never these sample ids.

## 6. Flows

1. Sign in → allowed home cards → separate tool page. The external fixture switch demonstrates Entusiasta/Designer, Designer Plus, Master Designer and staff. Permissions must be server-enforced in production.
2. Form → unfold measurements → select structure/sizes/colours → Contar globos → size/colour counts and package list without money. Phrase missing a measure asks for it. Photo selection remains local; sample result explicitly says estimate and sample tolerance. Editing a measure withdraws the old count pending a fresh run.
3. Counter → Calcular costo (only costos.usar) → imported material rows → edit price/quantity or disclose expenses → calculate → material/gasto/customer totals. Empty starts with an add-material or counter action. Failed quote preserves entered work and offers retry. All arithmetic in the mock is illustrative; Python continues owning real totals and catalogue data continues owning prices.
4. Taller → Decoraciones → filters → in-place preview → open-as-new link → optional existing unsaved guard → new unsaved scene. No-result filters can reset; errors can retry; unknown ids cannot mutate the current scene.
5. Existing chat greeting/chips/composer → idea preview → allowed Taller handoff. No unrestricted price, plan recommendation or limit counter appears. The complete production guided conversation is unchanged; this is representative context only.

## 7. Views and responsive composition

| Preview value | Working surface | Composition |
|---|---|---|
| home | / | 2-column permitted tool cards, first chat spans both; one column on phone. |
| counter | /contador | Method strip → schematic and editing controls beside purchase result → single count action. |
| calculator | /calculadora | Full-width ruled material rows → in-place expense disclosure → gain field → inline totals/action band. |
| chat | /asistente | Existing centred greeting/conversation/chips/composer vocabulary; no-price sample and allowed Taller link. |
| gallery | /3d/decoraciones | Search/occasion/size → horizontal decoration bands → single in-place preview and open action. |
| workshop | /3d?decoracion=<id> | Existing toolbar/rail/scene/inspector vocabulary as destination context; new scene is Sin guardar. |

## 8. Reachable states and limits

The native Vista/Estado/Diálogo/Tema/Movimiento selectors remain visible. States are a union; a state that does not apply to a view keeps that view's normal composition rather than inventing a product state.

| Estado value | Applicable view / response |
|---|---|
| normal | Home populated; counter idle; calculator sample materials; gallery results; chat initial; workshop current sample scene. Home-empty is impossible. |
| loading | Counter Contando globos; calculator Calculando cotización; gallery loading; chat preparing. Skeletons, disabled repeat submit. Home/workshop use normal context. |
| empty | Calculator Sin materiales with add/counter actions; gallery Sin resultados with clear filters. Counter remains idle; home has allowed cards. |
| error | Counter engine failure, quote failure, gallery load failure, chat failure; scoped retry and preserved input. |
| missing | Counter asks for measurement and offers Completar medidas with field focus. |
| photo-large / photo-invalid | Counter names the upload failure and offers Elegir otra imagen. The file-size limit is unresolved. |
| result | Counter counts; calculator explicit totals; chat sample idea. |
| photo-result | Counter selected photo method, estimate and sample ±12-balloon tolerance; not a real tolerance policy. |
| imported | Calculator shows materials imported from counter; values remain editable. |
| editing | Calculator expense fields expanded; totals pending recalculation. |
| unknown | Explorer/workshop say Decoración no encontrada; existing scene not replaced. |
| unsaved | Explorer opens the contextual unsaved guard; Cancelar preserves the current scene. |
| denied | Sin acceso with safe Inicio recovery; no restricted prices or list data. |

Diálogo=unsaved opens the same guard from any inspection view; it is not an additional production dialog. Offline/pending persistence/conflict behavior belongs to the existing project contract and is not redesigned. No quotas, billing dashboard or new pricing rule is introduced.

## 9. Responsive behavior

- **360–639px:** 20px outer/working insets; masthead and controls wrap; navigation remains horizontal/wrapped; cards and counter stack; measures/expense/filter fields are one column; quote material rows become two-column labelled inputs with full-width identity and subtotal; gallery preview follows its band header, with diagram before detail/open action; Taller rail/inspector hide as in proyectos. No page overflow.
- **640–1099px:** 24px outer insets; counter becomes one working column with result data in two columns; quote rows use three columns with subtotal on the next aligned line; gallery preview is 1.3:1; Taller inspector hides, rail stays.
- **1100px+:** inherited max-width 1520px / 40px gutters; counter 1.45:1; quote four aligned columns; gallery preview 1.6:1 and toolbar 2:1:1. Content scrolls vertically; no concealed mandatory control.

Modal width is min(580px, viewport−40px), height at most viewport−48px, with scrolling. All primary interactive targets are at least 44px high. Long copy wraps. Full English translation is SP-10; the language selector here preserves shell vocabulary and explains its scope, rather than claiming translated views.

## 10. Accessibility and motion detail

Target WCAG 2.2 AA; not a full conformance attestation. Associated labels, table caption/headers, named drawings, native disclosure semantics, aria-expanded/aria-controls on editing/preview actions, error alerts and polite result announcements. 3px acento focus ring with 4px offset; text ≥4.5:1 and control edges ≥3:1. The chat retains its original centred working heading without an added duplicate page title/footer. Navigation focuses H1; missing-measure action focuses its field. Dialog uses real Base UI focus containment/Escape behavior, Cancelar autofocus and an explicit finalFocus target. Return focus must land on the surviving invoking control after dismissal; direct inspector-driven dialogs have no production trigger.

Motion grammar is physical settling within a working surface: paper compresses vertically 7px/.992; card bands seat horizontally .985→1.004→1; diagram .96/−1deg→1.01/.2deg→1; preview hinges scaleY(.97→1.008→1); results seat 4px/.98. All effects are transform-first. Repeated buttons compress .965 and 2px on press, then settle; hover rises 1px. Profile timings and reduced/still parity match the axis table. No entrance hides text by opacity, no infinite decorative scene effect, no flashing. Skeleton pressure pauses offscreen; hidden tabs pause all app CSS animations. Static/reduced mode leaves all final content/actions present.

## 11. Visual acceptance and evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | All | All | Pictures/Sempertex masthead, Geist typography, account/language controls and inherited neutral route rule remain. |
| C-AC-02 | ≥1100px | counter/result | One paper places schematic/measures to the left and counts/shopping list to the right at 1.45:1. |
| C-AC-03 | All | counter/idle | Editar medidas expands labelled length/height fields in place and exposes expanded state. |
| C-AC-04 | All | counter/result | Rows total 120 sample balloons (48+48+24), with size/colour counts and package list, with no price. |
| C-AC-05 | All | counter/photo-result | The visible result is explicitly an estimate with sample tolerance, never an exact photo claim. |
| C-AC-06 | All | counter/missing | Completing measures moves focus to the missing field; the result does not fabricate counts. |
| C-AC-07 | All | counter/photo-large, photo-invalid, error | Each problem names the failure and exposes a recovery action. |
| C-AC-08 | All | calculator/imported | The materials-from-counter notice and editable material rows appear together. |
| C-AC-09 | All | calculator/editing | Price and package fields are in their material row; expense disclosure is open; current totals are withdrawn pending recalculation. |
| C-AC-10 | All | calculator/result | Material/gasto/customer sample totals align in the bottom band; edited prices update the next simulated quote. |
| C-AC-11 | All | gallery/normal | Each band names origin, occasion and size; the selected preview opens inside that band. |
| C-AC-12 | All | gallery/empty, error, unknown | Reset/retry/return actions remain reachable; unknown id says current scene is unchanged. |
| C-AC-13 | All | gallery/unsaved | Cancelar, explicit discard and server-save-before-open paths are visible in the real modal. |
| C-AC-14 | All | home / fixture roles | Unavailable tools are omitted; calculator/Taller direct inspection is denied when the role lacks access. |
| C-AC-15 | 360–639px | result, normal | Counter/quote/gallery stack with 20px insets, labelled inputs and no horizontal page scroll. |
| C-AC-16 | 640–1099px | normal | Counter stacks while gallery retains preview/detail columns; Taller inspector hides. |
| C-AC-17 | All | reduced/still | No travel/repeating animation remains; every action and final result remains visible. |
| C-AC-18 | All | chat | Existing guided copy/chips/composer remain; no forbidden monetary content or locked-plan pitch appears. |

### Actual verification

| Check | Actual result |
|---|---|
| Offline builder | Exit 0; 648 KB, 2,126 bundled source files; real React/shadcn/Base UI/Animate UI and inlined production Geist assets. |
| Token contrast | `contrast: 158 pairs checked in light and dark, all pass` (exit 0). |
| Final rendered audit | Exit 0; **540 / 540** combinations at **1280, 390 and 768px**, both themes; **18,296** text measurements and **2,250** focus stops. No sampling warning. |
| Axis selector evidence | `compare_directions.py` on this direction only: `ok=true`, `evidence_ok=true`, no missing evidence. This verifies selector/motion claims; it does not claim distinction from sibling directions, which is the coordinator's comparison. |
| Local interaction checks | PASS: inspector permission persistence; forbidden calculator refused; counter has no COP or costs action without permission; counter import; simulated quote 84,000→87,600 COP after editing a price; one material added from empty; open-as-new deep-link href and destination; cancel/unknown/filter recovery; explicit photo estimate. No page errors or HTTP(S) requests. |
| Responsive interaction sample | PASS: six views at 360/768/1280px without horizontal document overflow. |
| Final focused checks | PASS: chat normal/result/loading/error probes in both themes; Escape dismisses the modal and restores the exact open action; `?still=1` and `?rm=1` leave no running animation. |
| Visual inspection | In-memory screenshots inspected: both candidate thumbnails; desktop light home/counter/chat; dark desktop gallery/quote; light phone estimated-count result; dark phone expense editing and unsaved dialog. No screenshot artifacts written. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Earlier checks are not hidden: an initial in-progress audit was cancelled when the artifact changed and was not accepted. The first complete measured run failed with 28 alignment findings in the uneven three-column expense section; it was recomposed into four/two/one columns. The next complete run failed with seven chat alignment findings involving the external inspection strip and added full-width heading/footer around a centred conversation; the inspection strip now has header semantics and the existing chat's single centred working heading/no-footer composition is restored. A separate keyboard check exposed lost focus after dismissal; explicit Base UI finalFocus now restores the actual invoking action. The final full audit above ran against the resulting unchanged HTML, with no check suppression or tool modification.

Final HTML SHA-256: `90021efc3f8bd7285f8ff74769df56c891ee43901e2ef8ae14de606ceb411849`.


No production lint/types/build or provider/engine check is claimed: this task owns planning artifacts only. No assertion of real catalogue completeness, actual image estimation, 3D rendering, authentication, save durability or full professional-quote equivalence follows from a static mockup.

## 12. Open questions and assumptions

Q: Home catalogue visibility: SPEC round 15's SP-7 walkthrough says Entusiasta sees only Chat and Contador, while the current plan catalogue/permission description includes Catálogo. Should the home show its permitted Catálogo entry (the provisional mock choice), or deliberately omit it?
Q: What size/type limits and engine-supplied tolerance representation govern photo counting? ±12 in the mock is explicitly a fixture, not an approved threshold or policy.
Q: Which occasion/size metadata and size-filter units/ranges exist for every item of Ideas del asistente and Ideas Sempertex? The mock uses sample exact 2m/3m values, not an invented production taxonomy.
Q: Which structures and mandatory measurements are exposed by the existing form-counting engine? Arco/Guirnalda/Columna and the shown length/height fields are a provisional composition, not a new geometry contract.

Confirmed: normal chat stays VistaGuiada; old classic / becomes home; no costs permission means no prices; counts/totals/catalogue remain engine-owned; explorer is Taller permission scope; opening creates a new unsaved scene and cannot overwrite the current project. Questions belong to owner/Planner and the supplying engine/catalogue contracts; exploration continues without approving them.
