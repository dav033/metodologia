# Brief de interfaz — SP-5 · Saved decorations

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A signed-in Master Designer saves a named scene composition or selected piece to a server-side personal decoration library and places it into projects; employee and administrator roles can open another account’s items read-only, while only the owner can update or delete them. Existing browser-local library entries remain local and are not imported in the pre-production pilot.

## Requisitos que cubre

- R8: When a user saves a composition as a decoration, the system shall add it to their personal library.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-5 (round 11 answered)»

## Criterios de producto

- A signed-in user can save the current scene or selected piece with a name and occasion, and the saved item appears in that account’s personal library after reload and from another browser.
- A user can place a saved item into a project; employee and administrator roles can open another account’s saved decorations read-only, but only the owning account can update or delete them, including through direct API requests.
- Existing entries in `taller3d:biblioteca-propia:v1` are not imported in the pre-production pilot and remain in their original browser-local library.

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

- T5.1 — Copy the approved personal-decoration library UI contract
  - Objetivo: The exact approved decoraciones@v1 contract is pinned in the repository before changing the Taller library UI.
- T5.3 — Connect Taller save, place and idempotent browser-library import flows
  - Objetivo: Replace `Biblioteca.tsx`’s browser-only persistence as the source of truth with the account API while preserving the existing save-current-scene, save-selected-piece, place, rename and delete interactions. Do not import `taller3d:biblioteca-propia:v1` items in this pre-production pilot; preserve current browser-local records untouched. Show a read-only state when staff open another account’s saved item, while owner-only controls remain available to the owner. On sign-out or account switch, clear remote-derived in-memory entries before showing the next account.
- T5.4 — Verify cross-browser persistence, placement and ownership isolation
  - Objetivo: A real-entrypoint integration scenario proves personal decorations persist across browsers, can be placed into projects, remain isolated between users and import legacy browser entries without loss.
- T5.5 — Review the rendered personal-library UI against its contract
  - Objetivo: The rendered personal-library save, import, empty, loading, retry, success and error states match the approved UI contract at phone and desktop widths, with accessible names, keyboard flow and truthful save status.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T5.2, T5.6.
