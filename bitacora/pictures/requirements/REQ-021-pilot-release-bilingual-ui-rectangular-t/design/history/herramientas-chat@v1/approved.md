---
contract: herramientas-chat
version: 1
status: draft
subplan: SP-7
requirements: [R13, R16]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: a
name: Operación en paralelo
source_revision: r2
source_behavior: herramientas-chat@v1.r2.behavior.md
plan_revision: 17
---

# herramientas-chat@v1 — Operación en paralelo

## 1. Identity and traceability

Canonical planning **draft; not approved for implementation**. The owner chose direction a, “Operación en paralelo” (revision r2, left tool sidebar), through the web comparison. That choice authorizes this finalization; it does not approve the contract, the subplan or the plan. This is version 1; no approved predecessor exists. The design outputs of this task are only `design/herramientas-chat@v1.md` and `design/herramientas-chat@v1.html`. No exploration, history, SPEC, PLAN, production file, contract changelog or preview was changed.

Scope: REQ-021 / M2 / SP-7 “Assisted chat as three tools and the decorations explorer”, from SPEC (status ready; rounds 10 and 15), PLAN.json revision 17, `herramientas-chat@v1.r2.behavior.md` and the chosen r2 direction's Markdown, JSON, TSX and HTML. This contract specifies the UI of the tool home, the balloon counter, the cost calculator, the decorations gallery and the tool sidebar. It does not specify the tool catalogue, server gating, counter API, spend tagging or Python quote, which belong to T7.2–T7.4.

| Requirement | Contract coverage | Consuming tasks |
|---|---|---|
| R13 — assisted chat split into cost calculator, balloon counter and normal chat; chat connects to the 3D workshop | V0–V3, V5, F1–F4, F6, counter/calculator states, UI-AC-01–23, 30–31 | T7.5, T7.6, T7.7; review T7.10 |
| R16 — each plan grants exactly its tools, cumulatively; staff hold every tool | V0/V1 per-role tool lists, V7 denied page, F1, UI-AC-02–05, 26 | T7.5 (UI only; server enforcement is T7.2/T7.4) |
| Gallery product criteria (`decoraciones.explorar`) | V4, V6, D1, F5, gallery states, UI-AC-24–29 | T7.8; review T7.10 |

PLAN consumers: SP-7 `ui.contract=herramientas-chat`, `ui.version=1`, `design_task=T7.1`, `visual_review_task=T7.10`; UI implementation tasks T7.5 (home, classic chat retirement), T7.6 (counter), T7.7 (calculator), T7.8 (gallery). T7.1 copies only the owner-approved artifact. T7.9 (browser e2e) and T7.11 (audit) verify behaviour, not this visual contract.

**Changes relative to the chosen r2 exploration.** Composition, navigation, copy, states and motion are preserved. The canonical HTML was rebuilt with the current offline builder from a copy of the r2 TSX with two verified layout defects corrected (both visible in the r2 artifact itself; see §11):

1. *Quote split never stacked below 1100px viewport.* A later `@media (max-width:1099px){.quote-grid{grid-template-columns:minmax(0,1fr) 300px}}` rule overrode the container query that stacks the quote at main-column width ≤760px. At 390px the materials column was 48px wide and its labels, buttons and “Gastos y ganancia” wrapped letter by letter underneath the totals. The override was removed; the contract's container rule (§9) now governs.
2. *Price per pack clipped on phones.* Below 640px the material row was `minmax(0,1fr) 88px`, so “15000”/“20000” did not fit the COP / paquete input (45–49px of text in 38px). The phone row is now two equal columns (Paquetes | COP / paquete).

No other source change. The patched source and its diff are kept as delegation evidence (`.state/delegations/D-20261029-121224-c92f/herramientas-chat@v1.final.{tsx,diff}`), not as design files. The artifact's title bar and footer still read “Operación en paralelo · r2 A” / “Exploración operativa, borrador r2”; these are provenance chrome, not product copy.

**Impact:** new contract; no approved implementation exists, so no consumer migration. T7.5–T7.8 implement against it; T7.10 reviews against §11. The left tool sidebar exists only on the tool home and SP-7 tool pages; sibling contracts `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` keep their horizontal route row (open question Q1).

Read-only product evidence used by the exploration: t12 `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/components/guiado/VistaGuiada.tsx`, `src/components/cotizacion/{CotizacionProfesional,CampoGanancia,PreciosMateriales}.tsx`, `src/components/tres-d/{IdeasDelAsistente,Biblioteca}.tsx`. This finalization did not reopen product decisions.

## 2. Purpose and users

Users: signed-in accounts of type Usuario on one of four plans (Entusiasta, Designer, Designer Plus, Master Designer) and staff (Empleado interno, Administrador). Staff hold every tool.

| View | User goal | Observable success |
|---|---|---|
| V0 Tool sidebar | Move between my tools without returning home | Only my tools are listed; the current one is marked; choosing another switches in place and focuses its title. |
| V1 Home `/` | See what I can use and open it | One card per granted tool, each with Abrir; no locked, disabled or upsell cards. |
| V2 Counter `/contador` | Know how many balloons a decoration needs, by size and colour, and what to buy | Count total, per size/colour table and shopping list, never a price; photo results labelled as estimate. |
| V3 Calculator `/calculadora` | Price a decoration professionally | Editable pack prices/quantities, labour, transport/equipment, indirect costs and profit produce per-material subtotals, cost breakdown and customer price. |
| V4 Gallery `/3d/decoraciones` | Find a ready-made decoration and start a new project from it | Filtered register with an inline preview; «Abrir como proyecto nuevo» opens `/3d?decoracion=<id>` as a new unsaved scene. |
| V5 Chat `/asistente` (existing) | Keep the guided conversation | Unchanged flow; no price content without costos.usar; links to counter, calculator (with costs) and Taller (with Taller). |
| V6 Taller `/3d` (existing, context) | Reach the gallery from the editor | A «Decoraciones» entry; editor itself unchanged. |
| V7 No access | Understand I cannot open this tool | Refusal without data and without naming any plan; return to tools. |

## 3. Information architecture and hierarchy

Global shell, unchanged from siblings, top to bottom: Pictures/Sempertex masthead (ring-and-dot mark, “Pictures”, Geist Mono “Sempertex”), Idioma select and «Mi cuenta» disclosure (Cuenta de ejemplo, Cambiar tema, Mi cuenta, Planes, Cerrar sesión) → content area → footer.

Content area on tool pages: **left tool sidebar (V0)** | **main column**. Main column order: H1 + optional page action (gallery: «Volver al Taller») → status feedback line (when any) → one “paper” (rounded working surface) holding the view.

- Sidebar order: group label «Herramientas de tu cuenta»; «Herramientas» (home, separated by a rule); then granted tools in catalogue order: Chat, Contador de globos, Calculadora de costos, Catálogo, Taller 3D; «Decoraciones» nested under Taller 3D. Absent tools are not rendered.
- Counter paper: header (“Contar globos” + method switch Formulario | Frase | Foto) → split: inputs (left, 0.85) | result (right, 1.35). Result order: “Resultado” + dominant 28px tabular total (“120 globos”) → photo estimate notice (photo only) → size/colour/count table → “Lista de compra” → «Calcular costo» (costs only).
- Calculator paper: header (“Precio al cliente” + hint “COP · Datos de ejemplo, no precios de catálogo”) → split reversed: material editor + “Gastos y ganancia” + «Calcular precio al cliente» (wide left) | “Totales” (narrow right). Totals order: Materiales, Mano de obra, Transporte y equipos, Costos indirectos, Costo total, Ganancia, then the dominant “Precio al cliente” 28px.
- Gallery paper: header (“Decoraciones” + “Ideas del asistente e Ideas Sempertex”) → filter row (Buscar, Ocasión, Tamaño) → split: thumbnail register | adjacent preview (name, size, schematic, “Se abrirá como una escena nueva sin guardar.”, «Abrir como proyecto nuevo», the deep-link path).

Rationale: inputs and engine output stay visible together (direction concept “operational”); the count and the customer price are the only large numerals; no dashboard metrics. Progressive disclosure: photo field only in Foto method, totals only after a valid calculation, preview only for the selected row.

## 4. Design system and visual language

Fixed project system; no new palette, font or brand. Tokens (light / dark): `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--borde` #e3daef/#383c48; `--borde-suave` #efe9f8/#2a2d38; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--acento-hover` #5530b8/#a58dff; `--sobre-acento` #ffffff/#120b24; `--exito`, `--aviso`, `--error` (+ `-suave`) and `--taller-*` roles as in t12 `globals.css`. shadcn roles map once per theme: background/card/popover → fondo/superficie; foreground → texto; primary/primary-foreground → acento/sobre-acento; input → texto-tenue (accessible control edge ≥3:1, inherited from siblings); sidebar/sidebar-foreground/sidebar-accent/sidebar-border → superficie/texto/superficie-2/borde. The rendered sidebar sits on `--fondo` with a `--borde-suave` right rule.

Typography: Geist Sans (local WOFF2) body 15px/1.5; labels 13px semibold; table rows 14px; section headings 17–18px; H1 24px; count and customer-price numerals 28px tabular. Geist Mono only for the inherited “Sempertex” mark. Radii: paper 32px, fields 18px, pills/buttons 999px, inset groups 24px. Panel padding 24px desktop, 20px phone. Icons: lucide 18px, decorative (`aria-hidden`).

Colour use: accent only for primary actions and focus. Sidebar current item = neutral `--superficie-2` step + weight 600 + `--texto`; inactive items `--texto-suave`; no coloured bar. Errors use `--error` tone notices; no price ever shown in error/attention colour.

Focus: 3px `--acento` outline, 4px offset, on every interactive element; H1 receives programmatic focus (tabindex −1) after view changes.

Components (`source:id variant state`, import path):

| Component | Use | Import |
|---|---|---|
| `shadcn:sidebar static(collapsible=none) default/hover/focus/current` — SidebarProvider, Sidebar, SidebarContent, SidebarGroup, SidebarMenu, SidebarMenuItem, SidebarMenuButton (rendered as `<a>`), SidebarMenuSub/SubItem/SubButton | V0 tool sidebar | `@/components/ui/sidebar` |
| `shadcn:button default enabled/hover/focus/pressed/disabled/loading` | Primary: Contar globos, Calcular precio al cliente, Abrir como proyecto nuevo, Enviar | `@/components/ui/button` |
| `shadcn:button outline enabled/hover/focus/pressed` | Abrir, Calcular costo, Añadir material, Restaurar precios de catálogo, Vista previa, Volver…, Intentar de nuevo, dialog secondary actions, phone sidebar toggle | `@/components/ui/button` |
| `shadcn:input default editing/invalid/disabled` | Measures, product, packs, COP / paquete, costs, profit, gallery search | `@/components/ui/input` |
| `shadcn:textarea default editing` | Frase input, chat message | `@/components/ui/textarea` |
| `shadcn:skeleton default loading` | Counting, calculating, gallery loading | `@/components/ui/skeleton` |
| `shadcn:alert-dialog default open/closed` (installed Animate UI/Base UI implementation) | D1 unsaved-work confirmation | `@/components/ui/alert-dialog` |
| `custom:method-switch` (button group, `aria-pressed`) | Formulario/Frase/Foto | semantic HTML + tokens |
| `custom:count-table` (semantic `table`, right-aligned numbers) | Counter result | semantic HTML |
| `custom:ruled-material-editor` | Calculator rows | semantic HTML + shadcn inputs |
| `custom:thumbnail-register`, `custom:scene-schematic` (SVG, example) | Gallery | semantic HTML/SVG |
| `custom:notice` (`role=status` / `role=alert`) | Questions, errors, provenance, scope notes | semantic HTML |
| `custom:tool-card` | Home cards | semantic `article` |
| Native `select` | Estructura, Tamaños, Ocasión, Tamaño, Idioma | native |
| Inherited `custom:account-disclosure` | Mi cuenta | sibling pattern |

Motion (direction a, “precise cuts”; transform-only, content always readable): `.paper` enters 5px vertically; `.tool-nav-item` sidebar items and `.count-line` rows enter 8px horizontally with 35ms stagger; the current-tool marker (`.tool-marker`, Motion shared layout `layoutId`) slides between sidebar items; `.result-panel` enters from the opposite edge (8px); `.preview-stage` seats from scale .985; method changes cut by 3px; phone toggle chevron rotates 180°; button arrows travel 3px on hover; buttons scale 1.025 hover / .965 press. Profiles: expressive 280ms (repeated controls 150ms), natural 200/140ms, subtle 130/110ms; easing cubic-bezier(.23,1,.32,1). No infinite loop. Reduced motion (OS, «Quieto», `?still=1`) removes travel, scale and transitions, marker moves with zero duration.

## 5. Navigation and interaction model

- **Entry:** sign-in lands on `/` (V1). The classic chat page formerly at `/` is retired; `/api/chat` keeps serving the guided chat.
- **Persistent navigation:** V0 sidebar on V1–V4, V6–V7, and V5. Items are links (`/`, `/asistente`, `/contador`, `/calculadora`, existing catalogue route, `/3d`, `/3d/decoraciones`). Choosing an item navigates in place, sets `aria-current="page"`, slides the marker and moves focus to the page H1. Decoraciones is current on V4; Taller 3D on V6.
- **Per-role lists (tools absent, never disabled or named):**

| Account | Sidebar items after «Herramientas» | Home cards |
|---|---|---|
| Entusiasta | Chat, Contador de globos | “Chat con límites”, Contador de globos |
| Designer | Chat, Contador de globos | “Chat con límites más altos”, Contador de globos |
| Designer Plus | + Calculadora de costos | + Calculadora de costos |
| Master Designer, Empleado interno, Administrador | + Catálogo, Taller 3D › Decoraciones | + Catálogo, Taller 3D |

- **Phone (<840px viewport):** the sidebar collapses to a full-width outline toggle «Herramientas · <tool>» (secondary text omitted on home) with `aria-expanded`/`aria-controls="tool-list"`. It opens the same list in flow above the heading (no drawer/overlay). Choosing a tool closes it and focuses H1; Escape inside the list closes it and returns focus to the toggle.
- **Cross-tool links:** counter result «Calcular costo» → V3 imported (costs only). Chat answer actions: «Lista de compra» → V2 result; «Abrir en Taller 3D» (Taller only); «Calcular costo» (costs only). V3 empty «Ir al contador» → V2. V6 «Decoraciones» → V4. V4 «Volver al Taller» → V6. V4 open → V6 new unsaved scene (via D1 if unsaved work). V7 «Volver a herramientas» → V1.
- **Catálogo:** an existing destination outside SP-7; this contract only lists it (Q4).
- **In-page controls:** method switch changes inputs in place and resets the result to idle; gallery «Vista previa» selects a row and updates the adjacent preview without navigation (selected row shows a check).

## 6. Flows

**F1 — Sign in and open a tool (R16).** Sign in → V1 shows only the role's tools (table §5) → Abrir or the sidebar opens the tool page, H1 focused. Direct URL to an ungranted tool → V7.

**F2 — Count by form (R13).** V2 Formulario: Estructura (Arco/Guirnalda/Columna), Ancho (m), Alto (m), Tamaños, Colores → «Contar globos». Missing/non-positive measure → `question` notice «¿Cuánto mide la decoración?» with «Añadir medidas». Valid → `loading` (button «Contando…», disabled; skeleton; “Contando globos…”) → `result`: total, per size/colour rows, shopping list. No amount, currency, total price or quote at any permission level. Engine failure → `error` with «Intentar de nuevo»; inputs kept.

**F3 — Count by phrase or photo (R13).** Frase: textarea «Describe la decoración» (hint “Incluye las medidas.”); a phrase without a measure → `question`; «Añadir medidas» returns to Frase with the text kept. Foto: file input «Elegir la foto», “JPG, PNG o WebP de menos de 6 MB.”, “El conteo de una foto es una estimación.”; no file → status “Elige una foto para seguir.”; non-image → `photo-type` (“El archivo no es una imagen. Usa JPG, PNG o WebP.”); ≥6 MB → `photo-large` (“La foto supera el tamaño permitido. Usa una foto de menos de 6 MB.”); both offer «Elegir otra foto». Success → `photo-estimate`: result plus “Estimación por foto” with the engine-provided tolerance (Q5).

**F4 — Price a decoration (R13, costs).** From F2 «Calcular costo» → V3 `imported` (notice “Materiales del contador” summarising counted materials) or open V3 directly → `empty` (“Añade materiales o usa el resultado del contador.”, «Añadir material», «Ir al contador»; calculate disabled until a material exists). Edit Producto · paquete, Paquetes, COP / paquete; add/remove rows (remove has accessible name “Quitar material N”); «Restaurar precios de catálogo»; Mano de obra, Transporte y equipos, Costos indirectos (COP), Tu ganancia (%) with “Tu ganancia se suma a lo que te cuesta todo (materiales y tus gastos).” Any edit → `editing`: previous totals hidden, “Los valores cambiaron. Vuelve a calcular para ver una cotización vigente.” «Calcular precio al cliente» validates fields (native validity), then `loading` → `totals`. Quote failure → `error` (“No pude calcular la cotización”, “Los datos escritos se conservan. Inténtalo de nuevo.”, «Revisar datos»). Python owns totals; profit is added to total cost (CampoGanancia semantics), not a gross margin.

**F5 — Open a ready-made decoration (gallery).** V6 «Decoraciones» or sidebar → V4. Search, Ocasión, Tamaño filter the register live; no match → “Sin resultados”, “Prueba otra búsqueda o cambia los filtros.”, «Limpiar filtros». «Vista previa» selects a row. «Abrir como proyecto nuevo» → `/3d?decoracion=<id>` opens a new unsaved scene; the previously open project keeps its identity and is not overwritten. With unsaved Taller work → D1 first. Unknown id → “Decoración no encontrada”, “La escena abierta no cambió.”, «Volver a decoraciones». Load failure → “No pude cargar las decoraciones”, “El trabajo del Taller se conserva.”, «Intentar de nuevo».

**F6 — Guided chat (R13).** V5 keeps the existing conversation. Answers contain counts and the shopping-list link but no price, total or quote without costos.usar, and never say which plan has costs. With Taller, «Abrir en Taller 3D» connects chat to the workshop.

**F7 — Denied.** Ungranted route or gallery deep link without `decoraciones.explorar` → V7: “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». No data, no plan name, no upgrade prompt. The sidebar still lists only the account's tools.

**D1 — Unsaved work guard (reuses proyectos@v1).** Title “Tienes cambios sin guardar”; description “Guarda el proyecto actual antes de abrir una decoración como proyecto nuevo. La escena abierta se conserva hasta que decidas.”; actions Cancelar, Guardar y continuar, Descartar escena y continuar. Cancel/Escape closes and returns focus to the invoking «Abrir como proyecto nuevo» (H1 fallback). Save continues only after confirmed save (save/retry/first-name rules are proyectos@v1 / SP-4); failed or pending save keeps the scene and does not navigate. Discard opens the new unsaved scene.

## 7. View specifications

| View | Structure and content | Actions | Responsive |
|---|---|---|---|
| V0 Sidebar | `nav` “Herramientas de tu cuenta”; items with lucide icon + label (House, MessageCircle, ListChecks, Calculator, LayoutGrid, Box; Images for Decoraciones); home separated by a rule; Decoraciones indented under Taller 3D with a vertical guide. Current: superficie-2 pill, weight 600. | Navigate; phone toggle | 248px column ≥840px, sticky; toggle <840px |
| V1 Home | H1 “Herramientas”; paper with intro row “Herramientas de tu cuenta”; ruled list of `tool-card`s: icon, name (h2), descriptor (Asistente guiado / Formulario, frase o foto / Precio al cliente / Explorar catálogo / Decoraciones y proyectos), «Abrir →». | Abrir each | Cards stack; Abrir below text on phone |
| V2 Counter | §3 order. Form fields in two-column groups (Ancho/Alto). Table headers Tamaño · Color · Cantidad. Shopping list “<Color> · <size>” / “N unidades”. Idle result text: “Cuenta por formulario, frase o foto para ver los globos por tamaño y color y la lista de compra.” | Method switch, Contar globos, Añadir medidas, Elegir otra foto, Intentar de nuevo, Calcular costo (costs) | Split stacks at main ≤640px; result after inputs |
| V3 Calculator | §3 order. Material row: Producto · paquete de 50 (full width) / Paquetes / COP / paquete / remove; Subtotal line per row. Cost fields grid. Totals list with ruled rows and dominant customer price. Fixture hint states values are examples. | Añadir material, remove row, Restaurar precios de catálogo, Ir al contador, Calcular precio al cliente, Revisar datos | Quote stacks at main ≤760px (totals after editor); phone rows: product full width, then Paquetes | COP / paquete halves |
| V4 Gallery | Filter row (Buscar input with placeholder “Buscar decoraciones”, Ocasión, Tamaño); register rows: thumbnail schematic, name (selected underlined), origin (Ideas del asistente / Ideas Sempertex), size · “Datos de ejemplo”, «Vista previa» (check when selected); preview: name, size · “Escena de ejemplo”, schematic, open note, primary action, path text. | Filters, Limpiar filtros, Vista previa, Abrir como proyecto nuevo, Volver al Taller, Volver a decoraciones, Intentar de nuevo | Split stacks at main ≤640px; register precedes preview; open action wraps |
| V5 Chat (existing) | “Asistente guiado”; user/assistant bubbles; answer “Tu plan está listo: 120 globos.” + “12″ · Blanco y dorado” and gated actions; composer (Mensaje, Enviar). Context only. | Lista de compra, Abrir en Taller 3D (Taller), Calcular costo (costs) | Unchanged existing behaviour |
| V6 Taller (context) | Existing project header (“Sin guardar”), «Decoraciones», «Guardar proyecto», existing panel rail (Escena, Piezas, Sala, Biblioteca). Not redesigned. | Decoraciones | Existing |
| V7 No access | Paper with error notice (§6 F7). H1 keeps the requested tool's name. | Volver a herramientas | Same at all widths |

Copy rules: Spanish interface; every new string goes in a `textos-*.ts` module per screen (SP-10 translates). Tool names from plan-catalogue@1. Counts and prices are the engine's/catalogue's numbers; all numbers in the artifact (120, 60/60, 15.000/20.000 COP, 30.000/10.000/5.000 COP, 20 %, sizes, decoration names) are illustrative fixtures and must not ship. Strings prefixed “Mockup ·”, the account fixture selector (“Mockup · Cuenta”) and “Datos de ejemplo” captions are simulation chrome, not product copy. Units stay cm/m; prices COP in both languages.

## 8. States

Inspector `state` values are global; each view maps them locally and falls back to its baseline for irrelevant values. `denied` is reachable on every view and also follows from the fixture account.

| State | Views | What appears / can be done / recovery |
|---|---|---|
| `ready` (idle) | V2 | Inputs + idle result explanation. V3 maps to `empty` (or `imported` after transfer). V4 results. |
| `empty` | V2, V3 | V2 as idle. V3 manual-entry message, Añadir material / Ir al contador, calculate disabled. V6 after open: new unsaved scene. |
| `question` | V2 | Result area notice “¿Cuánto mide la decoración?” / “Falta una medida para contar los globos.” + Añadir medidas. |
| `loading` | V2, V3, V4 | Skeleton shaped like the result, polite status text, `aria-busy`; primary action disabled with progressive label (Contando…/Calculando…). |
| `result` | V2 | Total, rows, list; Calcular costo only with costs. |
| `photo-estimate` | V2 | Result + “Estimación por foto” + tolerance text from the engine. |
| `photo-large` / `photo-type` | V2 | Alert “No pude leer tu foto” with the specific reason + Elegir otra foto. |
| `error` | V2, V3, V4 | Alert with retry; inputs and the open scene are preserved; no cached success is fabricated. |
| `imported` | V3 | “Materiales del contador” provenance notice; rows prefilled; totals require calculation. |
| `editing` | V3 | Stale-totals explanation; previous totals hidden; recalculation required. |
| `totals` | V3 | Per-row subtotals, cost breakdown, Ganancia, Precio al cliente. |
| `no-results` | V4 | “Sin resultados” + Limpiar filtros. |
| `unknown` | V4 | Not-found alert, scene unchanged, Volver a decoraciones. |
| `unsaved` | V4 | Status “El Taller tiene cambios sin guardar.” under the open action; open triggers D1. |
| `denied` | all | V7. |
| Dialog `scene=unsaved` | V4 | D1 open. |

Inapplicable: home empty/loading/error (every role has at least one tool and the list is server-rendered from the role — confirmed in the brief); offline as a separate state (engine/quote/gallery errors cover unavailable responses); disabled tools (locked tools are absent by rule).

## 9. Responsive behavior

Supported range 360px and up; checked at 1280, 1024, 768 and 390px. Splits follow the **main column width** (CSS container `main`, inline-size), not the viewport.

- **≥1100px viewport:** 40px outer gutters; full-width masthead; 248px sidebar + 32px gap, sticky below the header; counter and gallery split; quote split while main >760px (at 1280px main is 920px).
- **840–1099px:** 24px gutters; sidebar 248px + 24px gap. Main ≈704–780px: quote stacks when main ≤760px (totals below the editor); counter and gallery stay split above 640px main.
- **<840px:** sidebar becomes the «Herramientas · <tool>» toggle above the heading; list opens in flow; main is full width. Splits stack when main ≤640px.
- **<640px:** 20px gutters and panel padding; header controls wrap; heading and page action wrap; gallery one column with register before preview; material rows become named fields (product full width, Paquetes | COP / paquete in two equal columns, remove button below); cost fields stack; dialog actions fill the width; Ancho/Alto stay two columns.
- No horizontal page scrolling at any supported width; long labels wrap by word, never per letter; every input shows its full fixture value.

## 10. Accessibility targets

Target WCAG 2.2 AA, subject to rendered verification of the implementation.

- Landmarks: masthead `header`, sidebar `nav` (“Herramientas de tu cuenta”), `main` column, `footer`. Sidebar items are links with `aria-current="page"` on the current one.
- Phone toggle: button with `aria-expanded`, `aria-controls`; Escape closes and returns focus.
- View change focuses the H1 (tabindex −1). Method switch uses `aria-pressed`. Gallery selection exposes the selected state in text (check icon is decorative) and does not move focus.
- Every field has a visible programmatic label; units in labels (m, COP, %). Native selects stay keyboard-native. Invalid numbers use native validity / `aria-invalid` with the value kept.
- Live regions: waiting and feedback `role=status`; errors and photo failures `role=alert`; loading `aria-busy`.
- Count table is a semantic table with header cells and right-aligned numbers.
- D1: modal, inert background, focus contained, Escape/Cancelar close, focus returns to the invoker (H1 fallback).
- Contrast: text ≥4.5:1, control edges and focus ≥3:1 in both themes. Targets ≥44px high. Focus 3px accent outline, 4px offset.
- Reflow to 320 CSS px without loss (rendered check at 360/390); 200% zoom without clipping.
- Reduced motion: no travel/scale; state and data identical.

## 11. Visual acceptance criteria and verification

“All” means 360px and up, checked at least at 390/768/1280px, light and dark. Inspectors reach every state; functional claims (server gating, engine numbers, spend tags, save) require T7.4/T7.9 evidence, not this fixture.

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | All | All | The Pictures/Sempertex masthead, Idioma and Mi cuenta controls and Geist fonts match sibling contracts; no horizontal route row on SP-7 pages. |
| UI-AC-02 | ≥840px | Entusiasta, any view | The sidebar lists exactly Herramientas, Chat and Contador de globos. |
| UI-AC-03 | ≥840px | Designer Plus | The sidebar adds Calculadora de costos and no Catálogo, Taller 3D or Decoraciones. |
| UI-AC-04 | ≥840px | Master/staff | The sidebar lists Herramientas, Chat, Contador de globos, Calculadora de costos, Catálogo, Taller 3D and Decoraciones nested under Taller 3D. |
| UI-AC-05 | All | V1 per role | Home shows one card per granted tool with Abrir and no locked, disabled, upsell or plan-named card. |
| UI-AC-06 | ≥840px | Any tool view | The current sidebar item has a neutral superficie-2 background, weight 600 and `aria-current=page`; no coloured bar. |
| UI-AC-07 | All | Switching tools | Choosing a sidebar item changes the view in place and focuses its H1; the marker slides (expressive) or jumps (reduced). |
| UI-AC-08 | <840px | Any tool view | The sidebar is a full-width «Herramientas · <tool>» toggle; opening shows the same list above the H1; choosing an item or Escape closes it. |
| UI-AC-09 | 1280px | V2 result | Inputs, the 120 total, two count rows and the shopping list appear side by side in one paper with no price or currency. |
| UI-AC-10 | 390px | V2 result | The result follows the inputs, full width, with no horizontal page scroll. |
| UI-AC-11 | All | V2 any, any role | No amount, COP, total or quote appears anywhere in the counter. |
| UI-AC-12 | All | V2 result, Entusiasta/Designer | «Calcular costo» is absent. |
| UI-AC-13 | All | V2 question | The measurement question and «Añadir medidas» appear in the result area. |
| UI-AC-14 | All | V2 photo-large / photo-type | “No pude leer tu foto” with the specific reason and «Elegir otra foto» appears in the result area. |
| UI-AC-15 | All | V2 photo-estimate | “Estimación por foto” and a tolerance line appear above the count table. |
| UI-AC-16 | All | V2/V3 loading | A skeleton and status text appear and the primary action shows Contando…/Calculando… disabled. |
| UI-AC-17 | All | V3 imported | “Materiales del contador” notice appears above prefilled material rows. |
| UI-AC-18 | All | V3 editing | No total is shown; the stale explanation asks to recalculate. |
| UI-AC-19 | All | V3 totals | Per-row subtotals, the cost breakdown, Ganancia and the 28px Precio al cliente agree with the editable fixture values. |
| UI-AC-20 | 1280px | V3 totals | Material editor (wide, left) and totals (narrow, right) are side by side. |
| UI-AC-21 | 768–1099px and 390px | V3 totals | Totals stack below the editor at full main width; no label, button or heading wraps per letter. |
| UI-AC-22 | 360–639px | V3 any with rows | Product is full width; Paquetes and COP / paquete share a row in equal halves and show their full values. |
| UI-AC-23 | All | V3 error | The quote error alert appears with inputs still filled and «Revisar datos». |
| UI-AC-24 | 1280px | V4 ready | Register and preview are adjacent; «Vista previa» on another row updates the preview without navigation. |
| UI-AC-25 | 390px | V4 ready | Register precedes preview; filters reflow; «Abrir como proyecto nuevo» wraps inside the paper. |
| UI-AC-26 | All | V4 no-results | “Sin resultados” and «Limpiar filtros» appear. |
| UI-AC-27 | All | V4 unknown | “Decoración no encontrada” says the open scene did not change; no scene substitution occurs. |
| UI-AC-28 | All | V4 unsaved + open | D1 shows Cancelar, Guardar y continuar, Descartar escena y continuar; Escape/Cancelar returns focus to the open action. |
| UI-AC-29 | All | V4/V6/V3 without permission | V7 shows the refusal and «Volver a herramientas», no decoration/quote data and no plan name. |
| UI-AC-30 | All | V5 Entusiasta | The chat answer shows counts and «Lista de compra» but no price, «Calcular costo» or «Abrir en Taller 3D». |
| UI-AC-31 | All | Reduced motion / Quieto / still | All content and controls are visible with no running animation after settling. |

**Evidence for the canonical HTML built in this finalization** (`design/herramientas-chat@v1.html`, SHA-256 `0b482164529ac991b2ebcc448dbd2c97fb3f13394163c4b0819b4c62b3c76725`):

| Check | Actual observation |
|---|---|
| Installed kit | `components status`: `installed=True built=True entries ok=96/96`. |
| Offline build | Exit 0: `built … (756 KB, 2194 source files, offline)`; real React/shadcn/Base UI/Animate UI controls, inlined CSS/JS and local Geist WOFF2. No fallback, install or fetch. |
| `contrast.py` | Exit 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Rendered audit | Exit 0: `612 renders (612 combinations planned), 18176 text measurements, 1472 focus stops` at 1280/390/768, both themes. |
| Layout probe (r2 vs final) | `.quote-grid` columns, r2 → final: 1024px `402px 300px` → `702px`; 768px `418px 300px` → `718px`; 390px `48px 300px` → `348px`; 1280px unchanged `593px 325px`. Counter/gallery splits identical. Clipped input values below 640px: r2 `price-0` 45>38px, `price-1` 49>38px → final none at 1280–360px. |
| Interaction probe | 25/25 PASS: sidebar switch focuses H1 + `aria-current`; empty width → question; Añadir medidas → Frase; loading busy/disabled; result 120; Calcular costo → imported; non-image/≥6 MB photo errors; edit hides totals; recalculation shows new totals; quote error keeps inputs; row selection updates preview; D1 opens with three actions, Escape returns focus; gallery denied shows no data; phone toggle collapsed/opens/Escape returns focus/choose closes; no horizontal overflow at 390; `?still=1` 0 running animations; OS reduced motion 0; expressive 12 running at 120ms; zero page/console errors; zero external requests. |
| Gating probe | All five fixture accounts × all views: sidebar lists match §5; counter has no price words for any role; Calcular costo only for Designer Plus/Master/staff; V3 denied for Entusiasta/Designer; V4/V6 denied below Master. |
| Visual inspection | Screenshots inspected: counter result light 1280, gallery dark 1280, home light 390, calculator totals 390 (before and after the fix). |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Note: the r2 exploration's own audit also reported PASS while its calculator collapsed at <1100px; the audit does not detect per-letter wrapping inside a too-narrow grid track. UI-AC-21/22 make that observable for T7.10.

Reproducible commands:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components status
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/.state/delegations/D-20261029-121224-c92f/herramientas-chat@v1.final.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html --widths 1280,390,768 --max-combos 240
```

## 12. Open questions and assumptions

Open questions (decision owner: David with the Planner; implementers must not infer answers from fixture values):

- **Q1** — Should the left tool sidebar also become the global navigation for Proyectos, Mi cuenta, Cuentas and Planes? Siblings keep a horizontal route row; this contract uses the sidebar only on SP-7 pages, leaving two navigation patterns.
- **Q2** — With the sidebar always present, should `/` keep one card per tool (this contract; matches the product criterion) or become a short pointer to the sidebar?
- **Q3** — Inside the Taller (`/3d`), should the tool sidebar stay beside the editor (this contract) or hide to give the canvas full width?
- **Q4** — Should Catálogo appear for Entusiasta/Designer/Designer Plus? planes@v1 includes base catalogue access, but SP-7's acceptance example expects only Chat and Contador for Entusiasta; this contract follows the example.
- **Q5** — What tolerance wording/value does the photo-count engine return? The artifact's “Tolerancia: pendiente del motor” is mockup-only and must not ship.
- **Q6** — Size filter: exact measurements or agreed ranges? “3 m / Hasta 2 m” are fixture values, not a taxonomy.
- **Q7** — Which chat name do staff see on the home card? plan-catalogue@1 names plan tiers only; the artifact shows “Chat con límites más altos” for Master and staff.

Confirmed decisions (from SPEC/brief, not reopened): `/` is the tool home and the classic chat page is retired; three tools; counter by form, phrase or photo without prices; calculator is the existing professional quote fed by the counter or by hand; no prices or plan names without costos.usar; gallery at `/3d/decoraciones` gated by `decoraciones.explorar` (Master Designer and staff); open-as-new-project via `/3d?decoracion=<id>`; owner's r2 feedback: tools as a left sidebar to switch between them.

Assumptions: `/contador` and `/calculadora` are the routes (the brief does not fix the counter path; SPEC's SP-7 check uses `/calculadora`). After D1 discard or a direct open, V6 in the artifact shows a generic “Proyecto de ejemplo · Sin guardar”; the real new scene carries the decoration (taller-scene contract). Material free-text entry stands for the existing material-entry mechanism; no free-form entry becomes a catalogue product. English layout is simulated only; translation and language persistence belong to SP-8/SP-10.

Fixture limits: no network, engine, catalogue, Python quote, persistence or real file analysis; timings and numbers are mock. Server authorization, spend tags and engine accuracy are verified by T7.2–T7.4, T7.9 and T7.11.

**Approval:** this is a draft. David/the independent approver must approve this exact draft through the planning workflow before T7.1 copies it. The Designer grants no approval.

### Input/artifact identity

| Input / artifact | SHA-256 |
|---|---|
| `SPEC.md` | `1231537116a3514a13601d6cf8ef844235948844c0c28d79368d530d62aa897c` |
| `PLAN.json` (revision 17) | `c4242beea078367051fcf3b33179024ae677d93ed9ac1504d4f4293582fd4952` |
| `design/herramientas-chat@v1.r2.behavior.md` | `193825c90fa318b1b7a2c1b0b8f61f80ed8efd465c843db2d4fc435f8021f493` |
| `design/herramientas-chat@v1.r2.dir-a.md` | `5e8334932d48e103912c675177a90111c4ad306c81ea857e2943425c5dd84606` |
| `design/herramientas-chat@v1.r2.dir-a.tsx` | `06d938bd05bf4b0b4ded3e6019ee57eb5d894117c0facd49de86c7fd08817069` |
| `design/herramientas-chat@v1.r2.dir-a.html` | `9e3753ff7649f24aa1fc68b23ba4f9ae5d7ff76a7660bd754b3106c3fa650460` |
| Patched source (delegation evidence) `herramientas-chat@v1.final.tsx` | `a0c8f3d3d9f10f35324e2b51b48dfef1aeec4996671dc18c798e4205a24665b3` |
| `design/herramientas-chat@v1.html` | `0b482164529ac991b2ebcc448dbd2c97fb3f13394163c4b0819b4c62b3c76725` |
