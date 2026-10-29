# Brief de interfaz — SP-6 · AI spend per user and session

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Every successful paid AI model call made by Next or services/ai-api is recorded once with the authenticated account, server session, work item (project, with conversation detail, when a project context exists; otherwise conversation), tool, call kind (text or image), provider/model, token usage and estimated USD cost. Empleado interno and Administrador can review totals by user, session, work item, kind and tool; ordinary Usuario accounts cannot access the data.

## Requisitos que cubre

- R4: When a paid AI call completes, the system shall store tokens and estimated cost against the user and session.
- R5: While signed in as employee or administrator, the system shall show spend totals per session, kind and user.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-6 (round 12 pending)»

## Criterios de producto

- An employee or administrator can filter usage by user and kind and see totals by session and work item without seeing prompts, generated content, API secrets or other unnecessary personal data.
- A Usuario account, signed-out visitor or caller without gasto.ver cannot access the dashboard or its API; authorization is checked on the server.
- A provider error with known billable usage retains those tokens/cost with an explicit partial/error status; fields not returned by the provider remain unknown and are never fabricated.

## Flujos de usuario

- El Planner no los escribió: derívalos de los requisitos y de la superficie existente, sin inventar flujos.

## Pantallas y estados

- El Planner no los escribió: lista en el contrato las pantallas y estados que exigen los requisitos.

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

El Planner no nombró las pantallas actuales. No las adivines: localízalas en solo lectura en estos repositorios y basa el mockup en ellas; si no las encuentras, dilo en CONCERNS.
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`

## No debe cambiar

- El resto de la superficie existente: shell, navegación, cabecera, tokens, fuentes y componentes.

## Reglas de copy

- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T6.1 — Pin the approved AI-spend UI contract
  - Objetivo: Copy the exact approved gasto-ia@v1 visual contract into design/contracts before building the staff dashboard.
- T6.4 — Build the staff spend dashboard and server-filtered API
  - Objetivo: Add a gasto.ver-protected page and API that filter by user and call kind and group totals by session and work item, with tool/provider/model and date context. Return only ledger fields needed for review; never expose prompt/response bodies. Use cursor-safe server queries.
- T6.5 — Run real-entrypoint usage attribution and authorization checks
  - Objetivo: Exercise one text and one image call through Next and ai-api with seeded users; verify user/session/work-item attribution, totals, retry idempotency, partial metadata behavior and denied access for Usuario. Store evidence against the isolated REQ-021 database.
- T6.6 — Review the rendered spend dashboard against gasto-ia@v1
  - Objetivo: Audit responsive layout, loading/empty/error states, filter labels, keyboard access and that no prompt/body data is rendered.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T6.2, T6.3, T6.7.
