# Brief de interfaz — SP-14 · Plans section: the four access plans, public and informative

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Anyone, signed in or not, reads four conventional informational subscription cards for Entusiasta, Designer, Designer Plus and Master Designer in catalogue order, with monthly price (COP in Spanish, USD in English), complete included-tool lists and unavailable-tool markers. There is no comparison/selection mode, highlighted/current/recommended plan, purchase, request, registration or account mutation.

## Requisitos que cubre

- R17: The system shall hold the four access plans in one plan catalogue — name, monthly price in COP and USD (Entusiasta free; Designer COP 20,000 / USD 7; Designer Plus COP 45,000 / USD 14; Master Designer COP 70,000 / USD 25), included tools in cumulative order and whether each tool is available yet — and every screen and permission that names a plan shall read it from that catalogue.
- R18: When anyone, signed in or not, opens the plans section, the system shall show the four plans in order with name, monthly price and included tools, marking extended chat, structure detection and advanced balloon detection «aún no disponible», without any purchase, request or access change.
- R19: The sign-in screen and the account menu shall each link to the plans section.
- R20: While the interface is in Spanish the plans section shall show prices in COP, and while it is in English in USD.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-14 subscription cards (P-211 supersedes round13 extra view)»

## Criterios de producto

- The /planes route presents four conventional informational subscription cards in catalogue order, each with plan name, monthly price and full included-tool list; no comparison/selection controls, highlighted/current/recommended plan or card action is rendered, and no hide-tools control is offered.
- Legacy /planes?vista=seleccionar and obsolete plan-selection query parameters show the same four informational cards without restoring a comparison mode, selection state, pressed plan, highlighted default plan or selection-specific controls.
- The four cards and full cumulative tool lists remain legible in Spanish and English at360,390,768 and1280px without horizontal page scrolling, clipping or collapsed tools, and every remaining language, back and account-menu link works by keyboard.
- The owner confirms the final planes@v2 design and SP14 before implementation. Preserve all unaffected catalogue/public-information/account invariants; full lists stay visible and reading cards never mutates account access.

## Flujos de usuario

1. Signed-out visitor reads the plan cards
   1. Open sign-in and follow its existing plans link.
   2. Read four conventional subscription cards in catalogue order with name, monthly price and full included tools.
   3. Return through the existing back navigation without selecting or requesting a plan.
2. Signed-in person looks at the plans
   1. Opens the account menu on any signed-in page
   2. Follows its plans entry
   3. Reads the four plans
   4. Returns to the page they came from
3. English visitor
   1. Opens /planes with an English browser
   2. Sees the same four plans and tools in English with prices in USD per month
4. Legacy plan-selection URL
   1. Open /planes?vista=seleccionar or an obsolete selected-plan query.
   2. Read the same informational cards; no comparison, selection or highlighting mode appears and no account changes.

## Pantallas y estados

- /planes ES: four cards Entusiasta,Designer,Designer Plus,Master Designer in that order; monthly COP,Entusiasta Gratis.
- /planes EN: Enthusiast,Designer,Designer Plus,Master Designer; monthly USD,Enthusiast Free; never both currencies together.
- Each card contains its complete cumulative catalogue tool list, visible without accordion/hide control, plus unavailable markers and the existing chat-limit wording without numbers.
- Signed-out and signed-in pages show identical public plan information; preserve host shell/account controls for its actual role without marking a current plan.
- 360/390px phone,768px tablet and1280px desktop; readable cards,normal vertical scrolling,no horizontal overflow,visible keyboard focus and ES/EN/light/dark/reduced-motion parity.
- Loading/catalogue unavailable/error recovery follows the existing architecture without invented plans/prices or success from partial/invalid data; no comparison controls appear in any state.
- Legacy selection query URLs resolve to the same non-selectable cards. No comparison tabs/side index/selection summary,default highlighted plan,per-plan pressed state,select/buy/request/register CTA or recommended/current-plan badge.

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/planes`, `/planes?vista=seleccionar (legacy query only; no separate mode after amendment)`, `existing plans link in /login and shared signed-in account menu`
- paths: `src/app/planes/page.tsx`, `src/components/planes/ComparadorPlanes.tsx`, `src/components/planes/comparador-planes.module.css`, `src/components/planes/textos-planes.ts`, `src/lib/planes/catalogo.ts`, `src/components/cuentas/MenuCuenta.tsx`, `src/app/globals.css`
- components: `ComparadorPlanes (legacy filename/export may remain; behavior becomes informational cards)`, `MenuCuenta (preserve active SP2 contract,including chosen cuentas-admin@v2 when composed)`
- screenshots: `/home/david/.local/share/bitacora-solver/pictures/20261031-153033-1a41/planes.png`, `/home/david/.local/share/bitacora-solver/pictures/20261031-153033-1a41/seleccionar.png`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Owner P211 explicitly replaces comparison/selection with conventional subscription cards. Read exact published commit0715a331b72111afe085e35d773b284764924fe4 through git show in /home/david/dev/.pictures-wt/login-redirect; never read/write /home/david/dev/pictures. Reproduction evidence/owner-rejected/SP-14-v2.md. Approved planes@v1 is immutable history,not the new design; new planes@v2 is a breaking scoped presentation/interaction revision. Keep actual Pictures shell/tokens/fonts and approved sibling account-menu composition. SP2 chosen-C correction is independent; do not redesign its account/password surface or create a new login/menu layout.

## No debe cambiar

- Four catalogue plans/order,canonical names,monthly COP/ES versus USD/EN prices,full cumulative tools,unavailable markers and existing chat-limit copy without numeric limits.
- Public informational /planes route and existing sign-in/account-menu entry links for every signed-in role; no authentication/permission/role/catalogue/business contract change.
- No buying,paying,requesting,contacting,signing up,changing plans or marking the current account plan. Cards are informational articles,not selection controls; do not add disabled or decorative purchase CTA.
- Preserve exact current host shell/account-menu behavior and SP2 contract,including dismissal/focus/name/plan identity. No new theme,language placement,font,palette,brand,marketing badge or invented benefit.
- Remove only owner-superseded comparison/selection features. Do not remove unrelated language,accessibility,responsive,public-route,entry-link or authorization regression coverage.

## Reglas de copy

- Plan names, prices and tool names come only from the plan catalogue; no marketing claims, testimonials, discounts or invented benefits
- Plan names: Entusiasta (English: Enthusiast), Designer, Designer Plus, Master Designer
- Spanish shows prices in COP per month and English in USD per month, never both currencies
- Entusiasta is free («Gratis» / «Free»)
- Tools not built yet say «aún no disponible» (Spanish) and «not available yet» (English)
- Chat limits are named without numbers: Entusiasta «con límites» / «with limits», Designer «con límites más altos» / «with higher limits» (owner, 2026-10-27)
- The Taller 3D line of Master Designer stands for the whole 3D balloon editor, the ready-made decorations explorer included; no separate explorer line (owner-confirmed 2026-10-27)
- If the section says how a plan is obtained, it says only that an administrator assigns it
- Use the heading Planes / Plans and ordinary subscription-card hierarchy: plan name,price/currency per month,full included tools. Remove Comparar planes,Seleccionar para comparar,Ir a un plan,Plan resaltado,selection-summary and return-to-comparison copy.
- No recommended/popular/best-value/current-plan badges,discounts,testimonials or invented marketing claims. All four cards are peers and no card is selected/highlighted by default.
- If explanatory access copy is useful,retain only the existing factual administrator-assignment statement; do not introduce a purchase/request action.
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T14.11 — Copy the independently owner-approved planes@v2 subscription-card contract
  - Objetivo: Copy only the exact independently owner-approved planes@v2 card contract to design/contracts/planes@v2.md after CG1. Unchanged T14.1 preserves the old approved v1 artifact; never overwrite it. The new contract removes comparison/selection and changes only the public plan presentation,not catalogue data,permissions or account/menu behavior. Exact owner visual and SP14 approval are prerequisites,not authority granted by the Planner or Designer.
- T14.2 — Replace comparison and selection with public subscription cards
- T14.3 — Plans links on the sign-in screen and in the account menu
  - Objetivo: The sign-in screen and shared account menu each retain exactly one plans entry,without changing the active owner-approved SP2 account contract or its sign-in,dismissal,identity and password behavior; preserve cuentas-admin@v2 when composed rather than resurrect older v1 layout.
- T14.5 — SP-14 visual review against the planes@v2 subscription-card contract
  - Objetivo: A fresh reviewer checks the owner-approved planes@v2 card presentation and unchanged entry-link composition at phone,tablet and desktop widths in ES/EN,with no comparison/selection controls,default highlighting,card actions or collapsed tools,recording every deviation with the responsible task. Preserve existing visual ledger and audit policy.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T14.1, T14.4, T14.6.
