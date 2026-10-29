# Brief de interfaz — SP-5 · Saved decorations

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A signed-in Master Designer (and staff) saves a named scene composition or selected piece to a server-side personal decoration library and places it into projects from any browser; Empleado interno and Administrador open another account's items read-only and only the owner updates or deletes them; an account with saved decorations cannot be deleted, only deactivated; existing browser-local library entries stay local and are not imported in the pilot.

## Requisitos que cubre

- R8: When a user saves a composition as a decoration, the system shall add it to their personal library.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-5 (round 11 answered)»

## Criterios de producto

- From the Taller a person saves the current scene or the selected piece with a name and occasion, sees saved only after the server confirms, and finds the item after a reload and in another browser of the same account.
- A saved item can be searched and placed into the open project, and the existing name, occasion, thumbnail and filter controls keep working.
- When staff open another account's item it is clearly read-only: rename, edit and delete controls are absent and placing it adds a copy to the staff member's own project.
- Entries already in the browser key taller3d:biblioteca-propia:v1 stay in that browser's local list untouched, nothing imports them, and switching or signing out never shows the previous account's server items.
- The rendered personal-library save, list, read-only, empty, loading, retry and error states match the approved decoraciones@v1 contract at phone and desktop widths, and every finding is recorded with the task to redo in the SP-5 visual ledger.

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
  - Objetivo: The repository holds the exact owner-approved decoraciones@v1 contract before the Taller library changes.
- T5.3 — Taller personal library on the account API: save, place, staff read-only and account switch
  - Objetivo: The Taller's personal library saves to and reads from the account API, keeps legacy browser entries local and never shows one account's items to another.
- T5.5 — SP-5 visual review against the decoraciones@v1 contract
  - Objetivo: A fresh reviewer compares the rendered personal library with the approved contract and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T5.2, T5.4, T5.6.
