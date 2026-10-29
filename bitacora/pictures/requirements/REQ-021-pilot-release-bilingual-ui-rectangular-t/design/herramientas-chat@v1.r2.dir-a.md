---
name: Operación en paralelo
status: draft
artifact: exploration
contract_target: herramientas-chat@v1
subplan: SP-7
requirements: [R13, R16]
revision: r2
previous_revision: r1
owner_feedback: "2026-10-29T11:41 direction=a — tools as a left sidebar to switch between them"
direction: a
owner: David
---

# Operación en paralelo — direction A

Revision r2 of direction A. Planning exploration only. This is not the canonical contract, an approval or an implementation instruction. The owner still chooses a direction and approves the plan. Only the assigned revision-specific files were authored; no repository, canonical contract, shared plan or project memory was modified.

## Revision r2 — what changed and why

Owner feedback (2026-10-29T11:41, direction=a): «Me gusta esta dirección pero prefiero que sea como una barra en la izquierda que tenga las herramientas y que se pueda ir cambiando entre ellas, como una sidebar». Applied as follows; everything else in r1 (concept, paper composition, method tabs, states, copy, fixtures, motion grammar, dialog) is kept.

- **Tool sidebar replaces the horizontal route row.** A persistent left sidebar (real shadcn `Sidebar`, static `collapsible="none"`) lists only the tools the signed-in account's role grants: «Herramientas» (the home `/`), then Chat, Contador de globos, Calculadora de costos, Catálogo and Taller 3D, with «Decoraciones» nested under Taller 3D (`/3d/decoraciones`). Choosing an item switches the tool in place, marks it with `aria-current="page"` and moves focus to the page H1. Locked tools are absent, never disabled or named (copy rule). Entusiasta/Designer see Herramientas, Chat and Contador only.
- **Shared shell kept.** The Pictures/Sempertex masthead, language and account disclosure stay full-width above the sidebar; the footer stays full-width below. The sidebar lives inside the content area, so the global shell of the sibling contracts is not replaced; it only replaces this subplan's tool route row (see Q: sidebar scope).
- **Current item** is a neutral `--superficie-2` step with weight 600 and `--texto` colour (inactive items `--texto-suave`), no coloured bar; the step slides between items as a shared-layout marker (motion axis).
- **Phone (<840px):** the sidebar collapses to a full-width «Herramientas · <current tool>» toggle (`aria-expanded`, `aria-controls`); it opens the same vertical list above the page heading; choosing a tool or Escape closes it and returns focus.
- **Home cards kept.** `/` still shows one card per granted tool (product criterion: «the home page shows only the tools… each opening its own page»); the sidebar is the persistent switcher on every tool page.
- **Container-driven splits.** Because the sidebar takes width, the input/result, quote and gallery splits now stack by the main column's width (container queries) instead of viewport width.

## Approach and existing surface

The existing guided conversation becomes one of the tools, while the new tool home replaces the classic chat at `/`. The unchanged Pictures/Sempertex ring-and-dot masthead, language/account controls, paper radii and local Geist fonts come from the selected/finalized accounts, plans and projects siblings. In r2 the siblings' neutral horizontal route row is replaced, for these tool pages only, by a left tool sidebar requested by the owner. The changed content becomes a compact working paper: counter input on the left, engine-count output on the right; the calculator puts line editing in the wider left column and totals in the narrower right; the gallery combines a thumbnail register with an adjacent preview. This is a change inside the existing app, not a new identity or landing page.

Read-only product evidence: t12 `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/components/guiado/VistaGuiada.tsx`, `src/components/cotizacion/{CotizacionProfesional,CampoGanancia,PreciosMateriales}.tsx`, `src/components/tres-d/{IdeasDelAsistente,Biblioteca}.tsx` and the existing Python professional quote. The shared UI brief is the scope; SPEC and PLAN are context. Both repository statuses were inspected: asesor contains unrelated existing edits, left untouched. The chosen/finalized `cuentas-admin@v1`, `planes@v1` and `proyectos@v1` Markdown and built HTML informed the shared shell; the selected projects source supplied its exact token mapping and font imports.

## Two thumbnail compositions and choice (r1, retained)

- Candidate 1: `.html.candidate-1.html`, side-by-side input/result paper. Chosen. At 1280px both the form, the count rows and the first shopping-list lines are simultaneously visible; the action is adjacent to the result it transfers.
- Candidate 2: `.html.candidate-2.html`, horizontal input bands with a full-width result below. Retained as evidence. It gives inputs more lateral space but pushes the shopping list below the first desktop viewport.

r2 is an iteration of the chosen composition, not a new exploration: no new thumbnails were produced; the r1 candidates remain the composition evidence. Both candidate HTMLs were written and rendered before constructing the full entry. They are composition thumbnails; both thumbnails and the full mockup embed the project's real Geist Sans/Mono WOFF2 files. The initial thumbnail render used a system-font stand-in, corrected to the local project assets before handoff. Neither thumbnail introduces a palette. The full built output uses installed real libraries, with no fallback, install or asset fetch.

## Eight axes

| Axis | Rendered expression |
|---|---|
| concept | Operational: keep inputs and engine output visible together inside the existing Pictures working paper. |
| layout | Persistent left tool sidebar (248px) beside one divided working paper: 0.85:1.35 input/result split; quote reverses to a wide line editor and narrow totals column; gallery is a thumbnail register with adjacent preview. Splits stack by container width, not viewport. |
| navigation | Left sidebar (real shadcn Sidebar, static) lists only the account's tools — Herramientas home, then each tool, with Decoraciones nested under Taller 3D — and switches between them in place with aria-current; on phones it collapses behind a «Herramientas · <tool>» toggle. Method buttons switch form/phrase/photo in place; gallery rows select an inline preview. |
| typography | Inherited Geist Sans, 24px H1, 18px sections, 13–15px controls and rows; 28px tabular count and quote totals. Geist Mono remains the inherited Sempertex treatment. |
| density | Compact ruled rows and grouped 2-column fields, 24px panel gutters; no ornamental dashboard metrics. Phone stacks the same working groups with 20px gutters. |
| components | Real shadcn Sidebar (SidebarProvider, Sidebar collapsible=none, SidebarMenu/Button/Sub), Button, Input, Textarea, Skeleton and Animate UI AlertDialog, recomposed into sidebar + one paper; native selects and the inherited account disclosure. |
| colour | Exactly Pictures light/dark tokens and inherited accessible control-edge alias. Accent only for primary actions and focus; sidebar current item is a neutral superficie-2 step with weight, no coloured bar. |
| motion | Precise cuts: paper enters 5px vertically, sidebar items and rows enter 8px horizontally with 35ms stagger, the neutral current-tool marker slides between sidebar items (shared layout), results arrive from the opposite edge, preview seats at .985 scale. 280ms cubic-bezier(.23,1,.32,1), repeated actions 150ms; natural/subtle scale down; reduced motion removes travel and transitions. |

## Fixed system and component provenance

Light/dark source values, respectively: `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--sobre-acento` #ffffff/#120b24. All other success/warning/error and Taller roles are copied from the same sibling/project source. `background/card/popover` map to the Pictures surfaces; `foreground` maps to texto; `primary/primary-foreground` to acento/sobre-acento. `input` maps to texto-tenue, retaining the sibling's accessible control edge. `sidebar/sidebar-foreground/sidebar-accent/sidebar-border` map to superficie/texto/superficie-2/borde; the rendered sidebar sits on `--fondo` with a `--borde-suave` rule. Decorative rules retain borde/borde-suave. No new colours or font families.

| Component / state | Real import / source |
|---|---|
| shadcn:sidebar static (`collapsible=none`) — SidebarProvider, Sidebar, SidebarContent, SidebarGroup, SidebarMenu, SidebarMenuItem, SidebarMenuButton (rendered as `<a>`), SidebarMenuSub/SubItem/SubButton; default/hover/focus/current | `@/components/ui/sidebar` |
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

0. **Tool sidebar (all signed-in tool views)**: labelled navigation «Herramientas de tu cuenta» with Herramientas (home) and each granted tool; Decoraciones nested under Taller 3D for decoraciones.explorar holders. Current item has `aria-current=page`; Catálogo shows a scope notice (existing destination outside SP-7). The denied page keeps the sidebar with only the account's tools.
1. **Home `/`**: signed-in account sees only permitted tools. Each is a horizontal peer card with existing name, a concise tool descriptor and Abrir. No locked cards, upsell or named-plan gate. Fixture account selection is explicitly labelled Mockup and is not a product role switch. Entusiasta/Designer show Chat and Contador, Designer Plus adds Calculadora; Master/staff additionally show Catálogo and Taller in this draft, pending the Catálogo question below. No home empty state: every account has tools. Catalogue entry displays an honest scope notice, since that existing destination is not redesigned by SP-7.
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

- 1100px and above: 40px outer gutters, full-width masthead, 248px left tool sidebar + 32px gap, main column with heading, split counter and quote, adjacent gallery preview. Sidebar is sticky below the mockup bar.
- 840–1099px: 24px gutters, sidebar keeps 248px with a 24px gap. Main-column container ≤760px stacks the quote totals below the material editor; counter and gallery stay split above 640px of main width.
- Below 840px: the sidebar becomes a full-width «Herramientas · <tool>» toggle above the heading; the list opens in place (no overlay or drawer). Main column is full width; splits stack when the main column is ≤640px.
- Below 640px: 20px gutters, header controls wrap, page heading/action wrap, one-column gallery; material rows become named fields instead of an overflowing table; quote expenses stack; dialog actions fill available width. Counter dimensions retain two readable columns.

Target WCAG 2.2 AA, subject to implementation verification. Native fields have explicit labels; selects stay keyboard-native. Buttons are at least 44px high; focus is a 3px accent outline with 4px offset. Counts use a semantic table with right-aligned numbers. Errors use role=alert, waiting/feedback role=status, loading aria-busy. Account disclosure has Escape/outside dismissal. The sidebar is a `nav` landmark; items are links with `aria-current=page`; the phone toggle exposes `aria-expanded`/`aria-controls` and Escape closes it, returning focus to the toggle. AlertDialog provides modal inertness/focus containment; cancellation returns focus. View changes focus H1. Spanish and English text variants retain state; units remain cm/m and quotes COP. Language persistence and complete translated copy are owned by SP-8/SP-10.

## Interaction and motion detail

Direction-specific motion is quick and precise, without fading away working information: `.paper` seats down by 5px, `.tool-nav-item` sidebar items enter 8px horizontally with the row stagger, the `.tool-marker` current-tool step slides to the newly chosen item (Motion shared layout, same 280/200/130ms ease; zero duration when reduced), the phone toggle chevron turns 180°, `.count-line` reveals horizontally by 8px in 35ms stagger, `.result-panel` enters from the opposite edge, `.preview-stage` seats from .985 scale, method changes cut by 3px, and button arrows travel 3px on hover. All use transform-based motion; the paper's content is immediately readable. Expressive profile is 280ms / repeated controls 150ms, easing cubic-bezier(.23,1,.32,1); natural 200/140ms and subtle 130/110ms. `useMotionProfile()` supplies active profile/reduced state. Hidden tabs pause CSS animations, no infinite decorative loop exists. Reduced OS preference, Quieto and `?still=1` remove animations/transitions/travel while retaining controls, data and status text. The installed AlertDialog retains its reduced-motion-aware primitive behavior.

## Observable visual acceptance for this exploration

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| A-01 | 1280, 1024, 390px | All | Pictures/Sempertex mark, Geist, exact source theme tokens and full-width masthead are retained; tool navigation is the left sidebar (no horizontal route row). |
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
| A-13 | 1280, 1024px | All tool views | Left sidebar lists only the role's tools; the current item is a neutral grey step with weight and `aria-current=page`; Decoraciones is nested under Taller 3D and current on the gallery. |
| A-14 | 390px | All tool views | Sidebar collapses to the «Herramientas · <tool>» toggle; opening shows the same list above the heading; choosing a tool or Escape closes it. |
| A-15 | All | Switching tools | Choosing a sidebar item changes the tool in place, slides the marker and focuses the page H1. |
| A-12 | All | Reduced motion | Every endpoint remains visible with no active finite travel/scale animations after settling. |

## Build, audits and visual inspection (r2)

r2 source started from a copy of the r1 TSX. Built with the current offline builder: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build herramientas-chat@v1.r2.dir-a.tsx --out herramientas-chat@v1.r2.dir-a.html` — `built … (756 KB, 2194 source files, offline)`. Real libraries only; no fallback, install or asset fetch; fonts remain the embedded local Geist WOFF2.

Rendered screenshots inspected: counter/result/light/1280, calculator/totals/dark/1280, gallery/light/1024, counter/result/dark/1024, calculator/totals/light/1024, home/light/390, gallery/dark/390 and the phone sidebar opened. That inspection found the phone toggle reading «Herramientas · Herramientas» on home and centre-wrapping; it was changed to a left-aligned toggle with the current tool as secondary text (omitted on home) and rebuilt. No horizontal page overflow at any checked width.

Focused browser checks on the built artifact: clicking Contador in the sidebar switches the view, focuses H1 and the marker is mid-translation 100ms later (`matrix(1,0,0,1,0.47,-6.84)`); clicking Decoraciones marks it `aria-current=page`; switching the fixture to Entusiasta leaves exactly Herramientas, Chat and Contador de globos in the sidebar; phone toggle opens (`aria-expanded=true`) and Escape closes it. All JSON evidence selectors match rendered elements (`.tool-shell`, `.work-grid`, `.quote-grid`, `.gallery-work`, `.tool-sidebar`, 7 `.tool-link`, `.tabs`, `.decoration-row .btn`, `.heading h1`, `.count-total`, `.summary-total`); `.paper`, `.tool-nav-item`, `.count-line`, `.preview-stage` declare running CSS animations, `.tool-marker` moves by script, `.btn` transitions. With `?still=1` no element declares an animation and 0 animations run after settling. No page errors or console errors.

Contrast: `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py herramientas-chat@v1.r2.dir-a.html` — exit 0, «158 pairs checked in light and dark, all pass».

Rendered audit: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py herramientas-chat@v1.r2.dir-a.html --widths 1280,1024,390 --max-combos 240` — exit 0; 612 renders / 612 planned combinations, 19,360 text measurements, 1,472 focus stops (fewer than r1 because the phone sidebar list is collapsed by default).

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

This does not certify production authorization, engine accuracy, persistence or full WCAG conformance. No repository was edited, so no repository lint/type/test/build was run.

## Impact, concerns and open questions

Affected SP-7 UI consumers: T7.1 design-copy, T7.5 home, T7.6 counter, T7.7 calculator, T7.8 gallery and T7.10 visual review. Compatibility is undetermined until the owner selects and approves a direction; this draft creates no version migration. Shared accounts/plans/projects contracts remain unchanged. No claim of approval, server enforcement or complete product accessibility conformance.

Open decisions for David/Planner (no implementation may infer answers from fixture values):

Q: Should the left tool sidebar also become the global navigation for Proyectos, Mi cuenta, Cuentas and Planes? Sibling contracts (cuentas-admin@v1, planes@v1, proyectos@v1) keep a horizontal route row; this r2 uses the sidebar only on the tool home and the SP-7 tool pages, which leaves two navigation patterns in the product.
Q: With the sidebar always present, should the home `/` keep one card per tool (current draft, matches the product criterion) or become a short landing that only points to the sidebar?
Q: Inside Taller 3D (`/3d`), should the tool sidebar stay visible beside the editor, or hide to give the canvas full width? This draft keeps it; the Taller editor itself is unchanged.

Q: Should Catálogo also appear on the Entusiasta/Designer/Designer Plus home? The sibling plan contract includes base catalogue access, while the SP-7 acceptance example expects only Chat and Contador for Entusiasta. This exploration follows that two-tool example and exposes Catálogo with the five-tool Master/staff fixture only.
Q: What tolerance wording/value does the existing photo-count engine return? The preview reserves the label and shows no invented percentage; the “pending engine value” phrase is mockup-only and must not ship.
Q: Should size filters use exact measurements or agreed size ranges? The shown 3 m / up-to-2 m options are explicitly illustrative fixture values, not a new product taxonomy.

Assumptions: `/contador` is the draft counter route because the brief does not fix its path; the planner may confirm it without changing the composition. No home empty state is applicable. The exact live product catalogue supplies decoration names, filter values, package sizes and prices. All generated content is neutral, clearly mock and limited to these flows.
