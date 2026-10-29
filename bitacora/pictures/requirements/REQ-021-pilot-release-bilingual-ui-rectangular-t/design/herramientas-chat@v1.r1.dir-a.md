---
name: Operación en paralelo
status: draft
artifact: exploration
contract_target: herramientas-chat@v1
subplan: SP-7
requirements: [R13, R16]
revision: r1
direction: a
owner: David
---

# Operación en paralelo — direction A

Planning exploration only. This is not the canonical contract, an approval or an implementation instruction. The owner still chooses a direction and approves the plan. Only the assigned revision-specific files were authored; no repository, canonical contract, shared plan or project memory was modified.

## Approach and existing surface

The existing guided conversation becomes one of the tools, while the new tool home replaces the classic chat at `/`. The unchanged Pictures/Sempertex ring-and-dot masthead, language/account controls, neutral horizontal navigation, paper radii and local Geist fonts come from the selected/finalized accounts, plans and projects siblings. The changed content becomes a compact working paper: counter input on the left, engine-count output on the right; the calculator puts line editing in the wider left column and totals in the narrower right; the gallery combines a thumbnail register with an adjacent preview. This is a change inside the existing app, not a new identity or landing page.

Read-only product evidence: t12 `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/components/guiado/VistaGuiada.tsx`, `src/components/cotizacion/{CotizacionProfesional,CampoGanancia,PreciosMateriales}.tsx`, `src/components/tres-d/{IdeasDelAsistente,Biblioteca}.tsx` and the existing Python professional quote. The shared UI brief is the scope; SPEC and PLAN are context. Both repository statuses were inspected: asesor contains unrelated existing edits, left untouched. The chosen/finalized `cuentas-admin@v1`, `planes@v1` and `proyectos@v1` Markdown and built HTML informed the shared shell; the selected projects source supplied its exact token mapping and font imports.

## Two thumbnail compositions and choice

- Candidate 1: `.html.candidate-1.html`, side-by-side input/result paper. Chosen. At 1280px both the form, the count rows and the first shopping-list lines are simultaneously visible; the action is adjacent to the result it transfers.
- Candidate 2: `.html.candidate-2.html`, horizontal input bands with a full-width result below. Retained as evidence. It gives inputs more lateral space but pushes the shopping list below the first desktop viewport.

Both candidate HTMLs were written and rendered before constructing the full entry. They are composition thumbnails; both thumbnails and the full mockup embed the project's real Geist Sans/Mono WOFF2 files. The initial thumbnail render used a system-font stand-in, corrected to the local project assets before handoff. Neither thumbnail introduces a palette. The full built output uses installed real libraries, with no fallback, install or asset fetch.

## Eight axes

| Axis | Rendered expression |
|---|---|
| concept | Operational: keep inputs and engine output visible together inside the existing Pictures working paper. |
| layout | One divided paper: 0.85:1.35 input/result split; quote reverses to a wide line editor and narrow totals column; gallery is a thumbnail register with adjacent preview. |
| navigation | Inherited neutral horizontal route links; method buttons switch form/phrase/photo in place; gallery rows select an inline preview instead of opening another page. |
| typography | Inherited Geist Sans, 24px H1, 18px sections, 13–15px controls and rows; 28px tabular count and quote totals. Geist Mono remains the inherited Sempertex treatment. |
| density | Compact ruled rows and grouped 2-column fields, 24px panel gutters; no ornamental dashboard metrics. Phone stacks the same working groups with 20px gutters. |
| components | Real shadcn/Base UI Button, Input, Textarea, Skeleton and Animate UI AlertDialog, recomposed into one paper; native selects and the inherited account disclosure. |
| colour | Exactly Pictures light/dark tokens and inherited accessible control-edge alias. Accent only for primary actions and focus; neutral route selection and panels. |
| motion | Precise cuts: paper enters 5px vertically, rows enter 8px horizontally with 35ms stagger, results arrive from the opposite edge, preview seats at .985 scale. 280ms cubic-bezier(.23,1,.32,1), repeated actions 150ms; natural/subtle scale down; reduced motion removes travel and transitions. |

## Fixed system and component provenance

Light/dark source values, respectively: `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--sobre-acento` #ffffff/#120b24. All other success/warning/error and Taller roles are copied from the same sibling/project source. `background/card/popover` map to the Pictures surfaces; `foreground` maps to texto; `primary/primary-foreground` to acento/sobre-acento. `input` maps to texto-tenue, retaining the sibling's accessible control edge. Decorative rules retain borde/borde-suave. No new colours or font families.

| Component / state | Real import / source |
|---|---|
| shadcn:button default and outline; default/hover/focus/pressed/disabled/loading | `@/components/ui/button` |
| shadcn:input default; editing/invalid/disabled | `@/components/ui/input` |
| shadcn:textarea default; phrase/chat input | `@/components/ui/textarea` |
| shadcn:skeleton loading | `@/components/ui/skeleton` |
| shadcn:alert-dialog unsaved-work confirmation; closed/open, focus trap/return | `@/components/ui/alert-dialog` installed Animate UI/Base UI implementation |
| custom:count-table, ruled-material-editor, thumbnail-register, notice | Semantic HTML, styled only with project roles; not claimed to be installed components |
| custom:account-disclosure and native selects | Inherited sibling pattern; Escape/outside close; mockup role selector is labelled simulation chrome |
| kit:mockup selectors / motion profile | `@kit/mockup`, `@kit/motion`; native `view`, `state`, `scene`, `theme`, plus motion |

Panel/field/pill radii stay 32/18/999px; inset groups 24px. Geist Sans body 15px, labels 13px, tables 14px, section headings 17–18px, H1 24px. The 28px tabular count is the dominant datum, not a promotional heading.

## Screens and interaction flows

1. **Home `/`**: signed-in account sees only permitted tools. Each is a horizontal peer card with existing name, a concise tool descriptor and Abrir. No locked cards, upsell or named-plan gate. Fixture account selection is explicitly labelled Mockup and is not a product role switch. Entusiasta/Designer show Chat and Contador, Designer Plus adds Calculadora; Master/staff additionally show Catálogo and Taller in this draft, pending Q1 below. No home empty state: every account has tools. Catalogue entry displays an honest scope notice, since that existing destination is not redesigned by SP-7.
2. **Counter `/contador` (proposed route)**: choose Formulario/Frase/Foto in place. Form groups structure, width/height in metres, sizes and colours. Phrase asks for missing measurements. Photo uses the existing JPG/PNG/WebP under-6-MB wording. Count action moves to loading, then a clearly simulated result: 120 balloons, two rows of 60 by size/colour and a price-free shopping list. All numeric values are illustrative engine-response fixtures, not estimates computed by this UI. Photo results additionally identify an estimate and reserve the tolerance field for engine-provided data; no numerical tolerance is invented. Calcular costo appears only with costs permission and transfers the result to Calculadora. No amount, currency, total or quote is rendered in the counter at any permission level.
3. **Calculator `/calculadora`**: starts empty for manual entry; imported state identifies counter materials. Sample quote uses two 50-unit packs per colour, visibly labelled, which explains why purchase units exceed the count. Edit package prices, quantities, labour, transport/equipment, indirect costs and profit; add/remove material rows; restore mock catalogue prices. Real catalogue lookup remains the product source, and the fixture explicitly says its prices are examples. Product calculation remains Python-owned. The simulation preserves existing CampoGanancia semantics: profit percentage is added to total cost; it is not redefined as gross margin. Changes hide valid totals until recalculation; errors preserve inputs. Calculated results include per-material subtotals, cost breakdown, profit and customer price. No free-form entry becomes an authoritative catalogue product in production; the fixture editor stands for the existing material-entry mechanism.
4. **Gallery `/3d/decoraciones`**: Taller entry opens a searchable register of both Ideas del asistente and Ideas Sempertex, with occasion/size filters. Preview selects a row in place; no modal preview or new library/editor model. The adjacent drawing is a CSS/SVG scene schematic labelled example, not an actual reference photo or final 3D result. Opening simulates `/3d?decoracion=<id>` as a new unsaved scene, preserving the selected decoration across views. No-results clears filters. Unknown id leaves the open scene unchanged. Permission denial exposes no decoration data.
5. **Unsaved work**: reuses proyectos@v1's pending-work guard. The installed AlertDialog offers Cancelar, Guardar y continuar and Descartar escena y continuar. The draft simulates success only; production may continue after save confirmation, must retain state on failed/pending/conflicted saving and must never replace the existing account project's identity. First-name/save/retry behavior stays in SP-4. A failed save is not illustrated as a successful save.
6. **Existing chat `/asistente` and Taller `/3d`**: context views demonstrate entry/exit links only. Guided conversation flow and existing editor/library are not redesigned. Chat has no price content; costs/Taller actions are permission-gated. Taller opens an unsaved scene and its Decoraciones entry. Existing out-of-scope controls show explicit Mockup destination notices rather than fake live effects. No network, provider call or persistence is used.

## States and fixture controls

Native inspectors expose all declared states. Global state names have view-local meanings; irrelevant combinations fall back to that view's baseline rather than inventing impossible product states. `denied` is testable on every view, and real fixture-account denial also applies to calculator/Taller/gallery. The initial home is not given fabricated loading/error/empty states.

| View | State IDs and visible behavior |
|---|---|
| Counter | `ready`/`empty`: instructions; `question`: missing measurement and Add measurements; `loading`: counting text + skeleton, count action disabled; `result`: 120 and rows/list; `photo-estimate`: estimate/tolerance field; `photo-large`/`photo-type`: file-specific recovery; `error`: engine failure and retry |
| Calculator | `empty`: manual material entry or return to counter; `imported`: provenance notice; `editing`: stale explanation, no valid total; `loading`: calculating skeleton and disabled calculate; `totals`: rows/subtotals/totals; `error`: quote failure and retained inputs |
| Gallery | `loading`: skeleton; `ready`: results; `no-results`: clear filters; `unknown`: not found and scene unchanged; `unsaved`: pending-work explanation and opening guard; `error`: retry without changing scene |
| Access | `denied`: no data, no plan named, return to tools. Also reached through account permission fixture on restricted routes. |
| Dialog | `scene=unsaved`: pending-work AlertDialog from visible open action or inspector; Escape/Cancel close; focus returns to the invoking element, with page-title fallback after navigation. |

Offline is not a separate product requirement: engine/quote/gallery error presentations cover unavailable responses without fabricating cached success. A browser-only fixture cannot verify server authorization, AI-spend tagging, exact engine quantities, catalogue prices, save durability or real file analysis. These are outside this design exploration.

## Responsive behavior and accessibility

- 1100px and above: 40px outer gutters, inherited header/navigation, split counter and quote; adjacent gallery preview.
- 840–1099px: 24px gutters, same counter/gallery split; quote total column 300px; long navigation wraps without a carousel.
- 640–839px: 24px gutters, all input/result and gallery/preview panels stack; gallery rows use two columns before preview.
- Below 640px: 20px gutters, header controls wrap, page heading/action wrap, neutral navigation wraps, one-column gallery; material rows become named fields instead of an overflowing table; quote expenses stack; dialog actions fill available width. Counter dimensions retain two readable columns. No fixed desktop sidebar is added.

Target WCAG 2.2 AA, subject to implementation verification. Native fields have explicit labels; selects stay keyboard-native. Buttons are at least 44px high; focus is a 3px accent outline with 4px offset. Counts use a semantic table with right-aligned numbers. Errors use role=alert, waiting/feedback role=status, loading aria-busy. Account disclosure has Escape/outside dismissal. AlertDialog provides modal inertness/focus containment; cancellation returns focus. View changes focus H1. Spanish and English text variants retain state; units remain cm/m and quotes COP. Language persistence and complete translated copy are owned by SP-8/SP-10.

## Interaction and motion detail

Direction-specific motion is quick and precise, without fading away working information: `.paper` seats down by 5px, `.count-line` reveals horizontally by 8px in 35ms stagger, `.result-panel` enters from the opposite edge, `.preview-stage` seats from .985 scale, method changes cut by 3px, and button arrows travel 3px on hover. All use transform-based motion; the paper's content is immediately readable. Expressive profile is 280ms / repeated controls 150ms, easing cubic-bezier(.23,1,.32,1); natural 200/140ms and subtle 130/110ms. `useMotionProfile()` supplies active profile/reduced state. Hidden tabs pause CSS animations, no infinite decorative loop exists. Reduced OS preference, Quieto and `?still=1` remove animations/transitions/travel while retaining controls, data and status text. The installed AlertDialog retains its reduced-motion-aware primitive behavior.

## Observable visual acceptance for this exploration

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1280, 1024, 390px | All | Pictures/Sempertex mark, Geist, exact source theme tokens and neutral route navigation are retained. |
| A-02 | 1280px | Counter result | Input, 120 total, two count rows and shopping list appear in one divided paper with no price. |
| A-03 | 390px | Counter result | Result follows inputs in DOM/visual order, no horizontal page scrolling. |
| A-04 | All | Entusiasta | No calculator/Taller link or Calcular costo action appears; direct restricted view shows no data and no upgrade-plan name. |
| A-05 | All | Question/photo errors | Explanation and the corresponding measurement/photo recovery control appear in the result area. |
| A-06 | All | Calculator editing | Previous total is not presented as current; recalculation is explicitly requested. |
| A-07 | All | Calculator totals | Editable package prices, per-row subtotals and quote breakdown share the same illustrative values. |
| A-08 | 1280px | Gallery results | Register and preview are adjacent; row selection changes preview without navigation. |
| A-09 | 390px | Gallery results | Register precedes preview, search/filters reflow and the long open action wraps. |
| A-10 | All | Unknown decoration | Not-found notice says scene unchanged; no scene substitution occurs. |
| A-11 | All | Unsaved dialog | Cancel, save-and-continue and discard-and-continue appear in a focus-contained confirmation; cancellation restores focus. |
| A-12 | All | Reduced motion | Every endpoint remains visible with no active finite travel/scale animations after settling. |

## Build, audits and visual inspection

Toolchain installed: 96/96 entries available. Build uses absolute CLI path and the assigned TSX entry, producing the assigned self-contained HTML with local embedded fonts and no runtime requests. Token contrast: 158 pairs checked in light and dark, all pass.

Rendered screenshots inspected: both candidate compositions at 1280px; full counter/result/light at 1280px and gallery/results/dark at 390px. That inspection exposed the phone title wrap and outline-button token mismatch; both were corrected in source. Final source additionally inspected at gallery/light/1280px, calculator/totals/dark/1280px, counter/result/dark/390px, home/light/390px and the unsaved-work dialog/dark/390px. Together these cover both themes at desktop and phone widths. The first full audit found four chat-axis alignment findings; the next found four isolated subtotal-line findings. The source now uses a full-width contextual chat paper and the existing paired label/value subtotal pattern; the six-case targeted subtotal regression passes without changing numeric alignment.

Focused browser checks on the built artifact:

- Entusiasta home has exactly two tools; counter results contain no COP or cost CTA; direct calculator entry is denied.
- Missing-measure phrase produces the question; adding measurements completes the simulated count; Calcular costo imports it.
- Changing the sample package price to 10,000 COP produces 126,000 COP after recalculation; two material subtotals appear; editing again removes a stale total.
- Gallery search/no-results/clear filters, inline preview and selected Guirnalda opening as a new unsaved Taller scene pass.
- AlertDialog has save/discard/cancel actions; Escape dismissal and return to the opening control pass. The initial test used a premature 120ms unmount assertion; waiting for the actual modal-hidden state fixed the test, with no product-source change.
- All six views reflow in English at 1280/1024/390px in both themes (36 cases), without horizontal page overflow or browser page errors.
- All 13 unique selector-evidence entries match their relevant rendered views. The row-cut keyframes actually animate at 0.28s; Quieto leaves no running animations and retains the result state. Only one local file-document request occurs, with no network requests.
- Photo MIME/size rejection, recovery and a labelled price-free simulated estimate pass. The initial heading assertion collided with the inspector option; using the heading role fixed the test, with no source change. Actual image decoding/recognition is not simulated.

Final builder: PASS, self-contained real-library HTML, 653 KB, 2,133 bundled source modules, offline. No packages or assets fetched.

Final contrast command: `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py herramientas-chat@v1.r1.dir-a.html` — exit 0, 158 light/dark token pairs pass.

Final rendered audit command: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py herramientas-chat@v1.r1.dir-a.html --widths 1280,1024,390 --max-combos 240` — exit 0. Actual coverage: 612 renders / 612 planned combinations, 18,816 text measurements, 2,279 keyboard focus stops; no sampling warning.

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

This is the real final audit result, after fixing the earlier findings; it does not certify production authorization, engine accuracy, persistence or full WCAG conformance. No repository lint/type/test/build was run because no production repository was edited; the assigned mockup builder, token checker, rendered audit and focused browser checks were executed.

## Impact, concerns and open questions

Affected SP-7 UI consumers: T7.1 design-copy, T7.5 home, T7.6 counter, T7.7 calculator, T7.8 gallery and T7.10 visual review. Compatibility is undetermined until the owner selects and approves a direction; this draft creates no version migration. Shared accounts/plans/projects contracts remain unchanged. No claim of approval, server enforcement or complete product accessibility conformance.

Open decisions for David/Planner (no implementation may infer answers from fixture values):

Q: Should Catálogo also appear on the Entusiasta/Designer/Designer Plus home? The sibling plan contract includes base catalogue access, while the SP-7 acceptance example expects only Chat and Contador for Entusiasta. This exploration follows that two-tool example and exposes Catálogo with the five-tool Master/staff fixture only.
Q: What tolerance wording/value does the existing photo-count engine return? The preview reserves the label and shows no invented percentage; the “pending engine value” phrase is mockup-only and must not ship.
Q: Should size filters use exact measurements or agreed size ranges? The shown 3 m / up-to-2 m options are explicitly illustrative fixture values, not a new product taxonomy.

Assumptions: `/contador` is the draft counter route because the brief does not fix its path; the planner may confirm it without changing the composition. No home empty state is applicable. The exact live product catalogue supplies decoration names, filter values, package sizes and prices. All generated content is neutral, clearly mock and limited to these flows.
