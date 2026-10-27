# Brief de interfaz — SP-3 · Taller essentials: rectangular tables, Backing and Blender export

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A user adds a rectangular table from its type card, edits size and chairs and sees actual quantities and dimensions without rental prices in the shopping list; Taller Fondos y muebles has one Backing group containing the seven existing props moved from their former visual groups, with saved IDs and AI/photo discovery preserved; the exported GLB opens in portable Blender LTS with the same layout, sizes in metres and base colours.

## Requisitos que cubre

- R9: When a user adds a rectangular table, the system shall let them set size and chairs and update the shopping list.
- R10: When a user exports to GLB, the system shall produce a file that Blender opens with the scene's layout, sizes and colours.
- R11: Taller Fondos y muebles shall have one Backing group containing panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico moved from their former visual groups; existing IDs, saved scenes, original-name search and AI/photo discovery shall remain compatible; Shopify /catalogo is unchanged (owner, round 9 q3).

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-3 and SP-4 (round 9 answered)»

## Criterios de producto

- Adding a rectangular table exposes length, depth and chair count, selects it in the inspector and updates the real shopping list with placed chairs, including capacity warnings and undo.
- The existing agregar_mesas, cambiar_mesas and cambiar_sillas tools produce the same table dimensions and actual chair counts as manual editing without a paid AI call.
- Each existing parametric table type has a creation card that adds its default-sized table and opens the inspector; rectangular tables use 240 × 90 × 75 cm by default and the shopping list contains quantities and dimensions without rental prices.
- Backing lists panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each addable; existing IDs, saved scenes, repository ownership, search and AI/photo discovery remain compatible.
- The seven Backing cards appear once in the new Taller group and no longer in their previous visual groups; Shopify /catalogo is unchanged and the original names and AI/photo discovery still resolve the same IDs.
- The exported GLB preserves actual scene world transforms, dimensions in metres, visible instances and base colours without mutating the editor or calling the network; export failure is visible and retryable.
- Phone, tablet and desktop renderings of table creation/editing, Backing and export states match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks.

## Flujos de usuario

1. Add and edit a rectangular table
   1. Opens Fondos y muebles in the Taller 3D
   2. Touches the card of a table type (Rectangular among the existing parametric types)
   3. The table appears in the scene at its default size (rectangular 240 × 90 × 75 cm) and the inspector opens
   4. Changes length, depth and number of chairs in the inspector
   5. Sees the placed chairs and the shopping list update; a capacity warning explains chairs that do not fit
   6. Undoes the change
2. Find and add a Backing prop
   1. Opens Fondos y muebles
   2. Opens the Backing group
   3. Finds one of the seven props (also by its original name in search)
   4. Adds it to the scene
3. Export the scene to GLB
   1. Opens the export control of the Taller
   2. Exports GLB and gets the file
   3. If the export fails, sees the failure and retries

## Pantallas y estados

- Table type cards in Fondos y muebles (one per existing parametric table type; fixed Imperial pieces stay available)
- Inspector of a selected table: length, depth, chairs
- Capacity warning when the chosen chairs do not fit the table
- Shopping list with furniture as quantities and dimensions, without rental prices («no es producto de la tienda» section)
- Backing group in Fondos y muebles with panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico, each once
- The former groups «Fondos y tapetes» and «Decorado de pie» without those seven cards
- Search with no results in Fondos y muebles
- Export states: idle, exporting, done, failed with retry
- Phone, tablet and desktop widths of the Taller

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/3d`
- paths: `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `src/components/tres-d/FondosYMuebles.tsx`, `src/components/tres-d/EditorConjuntoMesa.tsx`, `src/components/tres-d/Inspector.tsx`, `src/components/tres-d/ListaCompra.tsx`, `src/components/tres-d/ListaEscenografia.tsx`, `src/components/tres-d/ExportarEscenaTaller.tsx`, `src/components/tres-d/exportar-escena-glb.ts`, `src/lib/globos3d/mobiliario-conjunto-escena.ts`, `src/lib/globos3d/mobiliario-catalogo.ts`, `src/lib/catalogo/asignacion-fondos.ts`, `src/lib/catalogo/lista-por-repositorio.ts`
- components: `Taller3D`, `FondosYMuebles`, `EditorConjuntoMesa`, `Inspector`, `ListaCompra`, `ListaEscenografia`, `ExportarEscenaTaller`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Paths read on origin/main a9f3d6e5 (~/dev/.pictures-wt/login-redirect). FondosYMuebles groups cards today as «Fondos y tapetes», «Sillas y asientos», «Mesas» and «Decorado de pie» and filters by ASIGNACION_FONDOS; it creates only a default round parametric table; EditorConjuntoMesa already supports rectangular limits and chairs. ListaEscenografia shows furniture under «no es producto de la tienda». No screenshots are stored in the repository.

## No debe cambiar

- Shopify /catalogo and its categories (Backing exists only in the Taller)
- Existing furniture and prop IDs, their repositories (ASIGNACION_FONDOS), saved scenes and original-name, AI and photo discovery
- The Taller shell, navigation and design tokens outside the cards, inspector, shopping list and export control
- The GLB format (no new export format)

## Reglas de copy

- Spanish interface; every new string in src/components/tres-d/textos-taller-esenciales.ts for later translation
- No invented copy: prop and table names are the existing catalogue names; the group is called «Backing»
- Furniture lines show quantity and dimensions, never a rental price
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T3.1 — Copy the approved Taller essentials design contract
- T3.2 — Add rectangular tables through the existing table editor
- T3.3 — Group existing party props under Backing without changing their identities
- T3.4 — Verify and repair the GLB geometry and material export
- T3.7 — Review rendered Taller essentials against the design

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T3.5, T3.6, T3.8.
