# Brief de interfaz — SP-14 · Plans section: the four access plans, public and informative

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Anyone, signed in or not, opens the plans section from the sign-in screen or the account menu and compares Entusiasta, Designer, Designer Plus and Master Designer with their monthly price (COP in Spanish, USD in English) and included tools read from the plan catalogue, with the tools not built yet marked «aún no disponible»; a separate view lets visitors select/highlight one plan for comparison only; nothing in it buys, requests, signs up or changes an account’s assigned plan.

## Requisitos que cubre

- R17: The system shall hold the four access plans in one plan catalogue — name, monthly price in COP and USD (Entusiasta free; Designer COP 20,000 / USD 7; Designer Plus COP 45,000 / USD 14; Master Designer COP 70,000 / USD 25), included tools in cumulative order and whether each tool is available yet — and every screen and permission that names a plan shall read it from that catalogue.
- R18: When anyone, signed in or not, opens the plans section, the system shall show the four plans in order with name, monthly price and included tools, marking extended chat, structure detection and advanced balloon detection «aún no disponible», without any purchase, request or access change.
- R19: The sign-in screen and the account menu shall each link to the plans section.
- R20: While the interface is in Spanish the plans section shall show prices in COP, and while it is in English in USD.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-14 extra view (round 13 answered)»

## Criterios de producto

- The /planes page shows Entusiasta, Designer, Designer Plus and Master Designer in that order, each with its name, monthly price and included tools taken from the plan catalogue, and a value changed in the catalogue appears on the page without editing the page.
- With a Spanish browser language the page shows every price in COP per month and with an English one in USD per month, never both, Entusiasta shows as free in each language and is named Enthusiast in English.
- Extended chat, structure detection and advanced balloon detection appear under Designer Plus and Master Designer marked «aún no disponible» in Spanish and «not available yet» in English, the Entusiasta chat reads «con límites» / «with limits» and the Designer chat «con límites más altos» / «with higher limits», and the page has no purchase, request or sign-up control and shows no limit value.
- The sign-in screen and the account menu each show one link to the plans section that opens /planes, signed out from the sign-in screen and signed in from the menu.

## Flujos de usuario

1. Signed-out visitor compares the plans
   1. Opens the sign-in screen
   2. Follows its plans link
   3. Reads the four plans in order with name, monthly price and included tools
   4. Goes back to the sign-in screen
2. Signed-in person looks at the plans
   1. Opens the account menu on any signed-in page
   2. Follows its plans entry
   3. Reads the four plans
   4. Returns to the page they came from
3. English visitor
   1. Opens /planes with an English browser
   2. Sees the same four plans and tools in English with prices in USD per month

## Pantallas y estados

- /planes in Spanish: Entusiasta, Designer, Designer Plus and Master Designer in that order, prices in COP per month, Entusiasta free
- /planes in English: Enthusiast, Designer, Designer Plus and Master Designer with prices in USD per month
- Cumulative plans: each plan includes everything of the plan before it; the contract decides whether a plan lists all its tools or what it adds
- Chat lines without numbers: Entusiasta «Chat con límites» / «Chat with limits»; Designer «Chat con límites más altos» / «Chat with higher limits»
- Tools not built yet (extended chat, structure detection, advanced balloon detection) shown under Designer Plus and Master Designer as «aún no disponible» / «not available yet»
- Signed-out page (no account menu) and signed-in page (account menu present)
- Phone 390 px and desktop 1280 px without horizontal scrolling; keyboard focus order
- Plans link on the sign-in screen and plans entry in the account menu

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/login`, `/planes (new)`
- paths: `src/app/login/page.tsx`, `src/app/login/LoginForm.tsx`, `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, `src/components/ui/shell/MenuApp.tsx`
- components: `LoginForm`, `CabeceraApp`, `MenuApp`, `MenuCuenta (planned by SP-2 T2.4, not on main yet)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: The sign-in screen and the account menu are redesigned by SP-2 (cuentas-admin@v1, owner-chosen direction «Parte de acceso»); planes@v1 only adds one plans link in each and follows that direction and the tokens of src/app/globals.css. The page data comes only from the plan catalogue (src/lib/planes/catalogo.ts, SP-1 T1.2).

## No debe cambiar

- The sign-in screen and account menu layout, copy and behavior defined by cuentas-admin@v1, except one plans link in each
- No purchase, subscription, request, contact or sign-up action anywhere in the section
- No limit values, counters or limit messages
- Custom roles, staff roles and permission keys are never shown in the section

## Reglas de copy

- Plan names, prices and tool names come only from the plan catalogue; no marketing claims, testimonials, discounts or invented benefits
- Plan names: Entusiasta (English: Enthusiast), Designer, Designer Plus, Master Designer
- Spanish shows prices in COP per month and English in USD per month, never both currencies
- Entusiasta is free («Gratis» / «Free»)
- Tools not built yet say «aún no disponible» (Spanish) and «not available yet» (English)
- Chat limits are named without numbers: Entusiasta «con límites» / «with limits», Designer «con límites más altos» / «with higher limits» (owner, 2026-10-27)
- The Taller 3D line of Master Designer stands for the whole 3D balloon editor, the ready-made decorations explorer included; no separate explorer line (owner-confirmed 2026-10-27)
- If the section says how a plan is obtained, it says only that an administrator assigns it
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T14.1 — Copy the owner-approved planes@v1 contract into the repository
  - Objetivo: The repository holds the exact owner-approved visual contract of the plans section and its two entry points before any of them is built.
- T14.2 — Public plans page: the four plans from the plan catalogue, prices by language
  - Objetivo: A public /planes page renders the four access plans only from the plan catalogue, in the visitor's language with its currency, with all tool lists visible, no hide-tools control, and an extra informational view to select/highlight a plan for comparison without changing account assignment.
- T14.3 — Plans links on the sign-in screen and in the account menu
  - Objetivo: The sign-in screen and the account menu each lead to the plans section without changing anything else the cuentas-admin@v1 screens do.
- T14.5 — SP-14 visual review against the planes@v1 contract
  - Objetivo: A fresh reviewer compares the rendered plans section and its two entry points with the approved contract at phone, tablet and desktop widths and in both languages, including the extra selection view and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T14.4, T14.6.
