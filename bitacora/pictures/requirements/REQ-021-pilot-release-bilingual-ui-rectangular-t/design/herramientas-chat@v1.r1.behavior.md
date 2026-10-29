# Brief de interfaz — SP-7 · Assisted chat as three tools and the decorations explorer

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

The assisted chat becomes three tools on a home page that shows only the tools of the account's plan: the guided chat as the normal chat (no prices without the costs permission), a balloon counter by form, phrase or photo without prices, and the existing professional cost calculator with editable prices, labour, transport and margin; each tool's AI spend is measured separately and counts and prices come only from the engine and the real catalogue; a ready-made decorations gallery inside the Taller 3D (Master Designer and staff) opens a decoration as a new project by link.

## Requisitos que cubre

- R13: The assisted chat shall be split into a cost calculator, a balloon counter and a normal chat, and the normal chat shall connect to the 3D workshop.
- R16: When an administrator assigns one of the four access plans to a Usuario account, the system shall grant on the server exactly that plan's tools, cumulatively: Entusiasta the assisted chat and the balloon counter; Designer the same tools (its higher chat limits wait for the limit values); Designer Plus adds the cost calculator; Master Designer adds the Taller 3D; Empleado interno and Administrador shall hold every plan tool (amended 2026-10-27, round 10).

## Criterios de producto

- The home page / shows only the tools the signed-in account's role grants, each opening its own page; the classic chat page is gone while /api/chat keeps serving the guided chat's plan agent.
- The balloon counter page counts by form, by phrase or by photo and shows counts per size and colour and the shopping list without any price, and offers «Calcular costo» only to accounts with costos.usar.
- The cost calculator page takes the counter's result or materials typed by hand, lets the person edit balloon prices and add labour, transport, indirect costs and margin, and shows per-product prices from the real catalogue and the professional quote totals.
- The decorations gallery at /3d/decoraciones lists every Ideas del asistente and Ideas Sempertex item with search, occasion and size filters and a preview, and «Abrir como proyecto nuevo» opens /3d?decoracion=<id> as a new unsaved scene.
- The gallery and its deep link are reachable only with decoraciones.explorar; other accounts get the no-access page, and an unknown decoration id shows a not-found message without changing the open scene.
- The rendered home, counter, calculator and gallery screens match the approved herramientas-chat@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-7 visual ledger.

## Flujos de usuario

1. Sign in → home shows only the role's tools → open a tool
2. Counter: form (structure, measures, sizes, colours) or phrase or photo → counts per size and colour + shopping list without prices → «Calcular costo» only with the costs permission
3. Calculator: from the counter result or typed materials → edit balloon prices, labour, transport, indirect, margin → per-product prices and totals
4. Gallery (Taller, Master Designer and staff): search, occasion and size filters, preview → «Abrir como proyecto nuevo» opens /3d?decoracion=<id>

## Pantallas y estados

- Home: one to five tool cards depending on role; empty is impossible (every role has at least one tool)
- Counter: idle, missing-measure question, counting, result, photo too large or not an image, engine error
- Calculator: empty, imported from counter, editing, calculating, totals, quote error
- Gallery: loading, results, no results for a filter, unknown decoration link, opening with unsaved work in the Taller

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- components: `VistaGuiada (/asistente, stays the normal chat)`, `CotizacionProfesional (materials, labour, equipment and transport, indirect costs, margin)`, `IdeasDelAsistente and Biblioteca in the Taller`, `CabeceraApp / MenuApp shell`, `MenuCuenta (SP-2)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Read on origin/main a9f3d6e5. The classic chat page at / (src/app/page.tsx) is retired; / becomes the tool home. The professional quote already exists inside the guided chat and the Taller; the calculator page reuses it.

## No debe cambiar

- The guided chat conversation flow except removing prices for accounts without costs
- The Taller editor and its existing library panel
- The professional quote calculation (Python owns totals)

## Reglas de copy

- Spanish interface; every new string in a textos-*.ts module per screen for SP-10's translation
- Never show a price, total or quote to an account without the costs permission, and never name which plan has a locked tool
- Counts and prices are the engine's numbers; a photo count is labelled as an estimate with its tolerance
- Tool names come from plan-catalogue@1 (Chat con límites / con límites más altos, Contador de globos, Calculadora de costos)
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T7.1 — Copy the owner-approved herramientas-chat@v1 contract into the repository
  - Objetivo: The repository holds the exact owner-approved visual contract for the tool home, the counter, the calculator and the decorations gallery before any of them is built.
- T7.5 — Tool home page at / and retirement of the classic chat page
  - Objetivo: Signing in lands on a home page that shows only the tools the role grants, and the old classic chat page no longer exists.
- T7.6 — Balloon counter page: form, phrase and photo with a price-free result
  - Objetivo: A person counts the balloons of a decoration by form, phrase or photo and sees counts per size and colour and the shopping list, never a price.
- T7.7 — Cost calculator page from the existing professional quote, fed by the counter or by hand
  - Objetivo: A person with the costs permission prices a decoration with editable balloon prices, labour, transport, indirect costs and margin on its own page.
- T7.8 — Ready-made decorations gallery in the Taller with an open-as-new-project link
  - Objetivo: A Master Designer or staff member browses the ready-made 3D decorations, filters them and opens one as a new unsaved scene through a link the chat can reuse.
- T7.10 — SP-7 visual review against the herramientas-chat@v1 contract
  - Objetivo: A fresh reviewer compares the rendered home, counter, calculator and gallery with the approved contract at three widths and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T7.2, T7.3, T7.4, T7.9, T7.11.
