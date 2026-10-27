# Brief de interfaz — SP-3 · Taller essentials: researched and modelled Backing and table types, type cards and every-type Blender export

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

The owner approves, from a sourced proposal, which new Backing structures and table types the pilot gets; the Taller models them as parametric tables and parametric furniture through exhaustive type registries and integrates them with search, scene AI, photo reading, English phrases and the shopping list; Fondos y muebles offers one card per table type (the eight existing types, rectangular included, plus the new ones) that adds it at its default size and opens the existing table editor, and one Backing group with the seven existing props moved from their former groups plus the new ones; the GLB of every element type the code enumerates, alone and in one full scene, opens in portable Blender LTS with the same layout, sizes in metres and base colours, or the failing type is listed as a defect.

## Requisitos que cubre

- R9: The Taller shall offer one creation card per parametric table type — the eight existing types, rectangular included, plus the new types the owner approves from the SP-3 research, modelled in the parametric table generator — that adds the table at its default size and opens the existing table editor (size, chairs, arrangement); the shopping list shall show quantities and dimensions without rental prices (amended 2026-10-27, owner correction).
- R10: When a user exports to GLB, the system shall produce a file that Blender opens with the scene's layout, sizes and colours.
- R11: Taller Fondos y muebles shall have one Backing group containing panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal and arco_metalico moved from their former visual groups, plus the new Backing structures the owner approves from the SP-3 research, modelled as Taller props with search, scene AI, photo reading, English phrase and shopping-list support; existing IDs, saved scenes, original-name search and AI/photo discovery shall remain compatible; Shopify /catalogo is unchanged (owner, round 9 q3; amended 2026-10-27).

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-3 and SP-4 (round 9 answered)»

## Criterios de producto

- Fondos y muebles shows one creation card per parametric table type, the eight existing types and every approved new type, each found by searching its name or synonyms (rectangular included); touching a card adds that type at its default size (rectangular 240 × 90 × 75 cm) with as many default chairs as fit up to eight, selects it and opens the existing table editor.
- The existing table editor shows the right dimension labels and limits for every table type and keeps its capacity warning and undo, and the fixed Imperial and other fixed table pieces remain available.
- The repository card counts and the Mobiliario selector count include exactly the table type cards in place of the former single «Mesa con sillas a medida» card.
- Fondos y muebles has one Backing group listing panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico and every approved new Backing once each, the seven no longer appear in «Fondos y tapetes» or «Decorado de pie», and each card adds its prop by click or drag.
- Searching «Backing» finds every Backing card and the original names still find each prop; ids, repository ownership, saved scenes, scene AI and photo discovery resolve the same ids, and Shopify /catalogo is unchanged.
- The catalogue repository suite passes with every Backing prop still assigned to its former repository.
- Phone, tablet and desktop renderings of the table type cards, the table editor with a new type, the Backing group and the unchanged export menu match the approved taller-esenciales@v1 contract, with actionable findings mapped to their owning tasks.

## Flujos de usuario

1. Add a table by its type
   1. Opens the Añadir panel of the Taller 3D and Fondos y muebles (Utilería tab under «Todos», or the Mobiliario repository)
   2. Sees one card per table type in the «Mesas» group: Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, En U and one card per new type the owner approves (unknown until SP-3's research is approved; mockups show them as marked placeholders «Mesa nueva A», «Mesa nueva B»)
   3. Optionally searches «rectangular» and finds its card
   4. Touches the card: the table appears at its default size with its default chairs, is selected and the existing table editor opens in the inspector
   5. Edits size, chairs and arrangement exactly as today
2. Find and add a Backing
   1. Opens Fondos y muebles (or the Escenografía repository)
   2. Opens the new Backing group with the seven existing props and the new approved Backings (mockups show the new ones as marked placeholders «Backing nuevo A», «Backing nuevo B»)
   3. Finds one by browsing, by searching «Backing» or by its original name
   4. Adds it by touching or dragging the card, as with any other card

## Pantallas y estados

- «Mesas» group with one card per parametric table type in place of today's single «Mesa con sillas a medida» card; each card uses the existing card style with a thumbnail of that type at its default size
- Panel result counter and Mobiliario repository selector count including the table type cards
- Search «rectangular» showing the Rectangular card; the existing no-results state
- The existing status line after adding a table, naming the added type
- The existing table editor with a new table type selected: its dimension labels and slider limits for that shape
- Backing group in Fondos y muebles and in the Escenografía repository view: the seven existing cards and the new Backing cards, each once
- «Fondos y tapetes» and «Decorado de pie» without the seven moved cards
- Phone, tablet and desktop widths of the Añadir panel
- Without new pieces approved: «Mesas» holds the fixed tables and the eight type cards, and Backing holds the seven existing props

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/3d`
- paths: `src/components/tres-d/PanelAnadir.tsx`, `src/components/tres-d/FondosYMuebles.tsx`, `src/components/tres-d/DibujoFondo.tsx`, `src/components/tres-d/EditorConjuntoMesa.tsx`, `src/components/tres-d/Inspector.tsx`, `src/components/tres-d/ListaEscenografia.tsx`, `src/components/tres-d/ExportarEscenaTaller.tsx`, `src/lib/catalogo/anadir-repositorios.ts`, `src/lib/catalogo/asignacion-fondos.ts`, `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `src/lib/globos3d/fondos-escenografia.ts`, `src/lib/globos3d/mobiliario-catalogo.ts`
- components: `PanelAnadir`, `FondosYMuebles`, `DibujoFondo`, `EditorConjuntoMesa`, `Inspector`, `ListaEscenografia`, `ExportarEscenaTaller`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: SP-3 moved to M2 (owner 2026-10-27, answer B). The new table types and Backings are not known until the owner approves the research list during execution (T3.2, T3.4), so the design shows them only as marked placeholders. Dimension labels of every type come from one registry (ETIQUETA_MEDIDAS_MESA, T3.3). Read on origin/main a9f3d6e5 (the registered pictures checkout has the same Taller files). The functionality already exists; SP-3 changes only the entry points and adds pieces. Today: the Añadir panel (PanelAnadir) has a repository selector Todos / Sempertex / Mobiliario / Escenografía; under «Todos» FondosYMuebles sits in the Utilería tab with the heading «Fondos y muebles · no son globos: no cotizan» and four groups of three-column cards (thumbnail + name): «Fondos y tapetes», «Sillas y asientos», «Mesas», «Decorado de pie». «Mesas» lists the fixed catalogue tables (Imperial, redonda, cóctel, postres…) and ends with ONE card «Mesa con sillas a medida» (round 1.5 m with eight Tiffany chairs); its search words omit «rectangular»; touching it adds a round table, selects it and shows a status line. The inspector then shows EditorConjuntoMesa: «Mesa» (Tipo de mesa select with the eight types, sliders Diámetro / Lado / Largo / Ancho total, Ancho de la mesa, Alto de la tapa, Mantel, tapa/mantel and patas colours, + camino de mesa) and «Sillas» (Cantidad − / + with «caben N», the warning «Se pidieron X, pero en esta mesa con esta disposición solo caben Y», Tipo de silla, Disposición, colours, + cojín). panel_redondo, media_luna and arcos_chiara are in «Fondos y tapetes»; pedestales, aro_metalico, aro_hexagonal (shown as «Marco hexagonal metálico») and arco_metalico in «Decorado de pie». The shopping list already shows furniture as «N × Mesa rectangular 240×90 (mobiliario)» under «Mobiliario · no es producto de la tienda», without price, with the real placed chair count. Export: the header «Exportar» menu with «Descargar PNG · 3000 px» and «Descargar modelo GLB», states «Preparando GLB…», «Descarga GLB iniciada.» and «No se pudo exportar GLB: …»; SP-3 does not change it. No screenshots are stored in the repository.

## No debe cambiar

- The Taller shell, header, side rail, viewer, inspector layout and the table editor's controls (only the dimension labels and limits of new types are added)
- The card style (thumbnail and name) and the other cards of every group
- The export menu, its actions and its states; the shopping list layout
- Existing furniture and prop ids, their repositories, saved scenes and original-name, AI and photo discovery
- Shopify /catalogo and its categories (Backing exists only in the Taller)

## Reglas de copy

- Spanish interface; every new string in src/components/tres-d/textos-taller-esenciales.ts for later translation
- Table card names are the existing type names (Mesa redonda, Mesa rectangular…); new pieces take the Spanish names the owner approves in T3.2; until then mockups use visibly marked placeholders («Mesa nueva A», «Backing nuevo A») and never invented names, dimensions or pictures
- The group is called «Backing»; no invented descriptions
- Furniture lines show quantity and dimensions, never a rental price
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T3.1 — Copy the approved Taller essentials design contract
- T3.9 — One creation card per table type in Fondos y muebles
  - Objetivo: Following design/contracts/taller-esenciales@v1.md, replace the single «Mesa con sillas a medida» card of the «Mesas» group in src/components/tres-d/FondosYMuebles.tsx with one card per TIPOS_MESA type (the eight existing types and the approved new ones, in TIPOS_MESA order, after the fixed catalogue tables, which stay), each named NOMBRE_MESA[tipo], with a thumbnail of that type at its PARTIDA_MESA size and search text NOMBRE_MESA plus SINONIMOS_MESA, so «rectangular» finds the Rectangular card; TEXTO_CONJUNTO goes away. Touching a card calls agregarConjuntoPorDefecto(escena, maxNodos, tipo) (src/lib/globos3d/mobiliario-conjunto-escena.ts; today it always builds a redonda with 8 chairs), which adds that type at its PARTIDA_MESA size with sillasDePartida(tipo) chairs, selects it, opens the existing table editor and shows the existing status line naming the type with SINGULAR_MESA. In src/components/tres-d/EditorConjuntoMesa.tsx the dimension labels come from ETIQUETA_MEDIDAS_MESA instead of the etiquetaAncho if-chain; controls, capacity warning and undo stay. contarFondosYMuebles and fijasDe (src/lib/catalogo/anadir-repositorios.ts) count the type cards instead of the single card. Every new string goes in src/components/tres-d/textos-taller-esenciales.ts. New scripts/test/test-taller-mesas-piloto.ts covers the cards, the search, the typed default add, the editor labels and limits for every type, capacity warning and undo; in scripts/test/test-anadir-repositorios.tsx and scripts/test/test-anadir-repositorios-ui.ts write the Mobiliario and Todos counts as expressions of TIPOS_MESA.length and re-pin the DORADO_DE_SIEMPRE hashes whose filter shows the «Mesas» group, stating in the task report that the HTML diff only replaces the table card.
- T3.10 — Backing group in Fondos y muebles with the seven existing and the new Backing props
  - Objetivo: Following design/contracts/taller-esenciales@v1.md, show in src/components/tres-d/FondosYMuebles.tsx a «Backing» group, in Fondos y muebles under «Todos» and in the Escenografía repository view, listing every IDS_BACKING prop once (the seven existing ones and the approved new ones) through grupoVisibleDe (src/lib/globos3d/backing.ts), for presentation only: the seven no longer appear in «Fondos y tapetes» or «Decorado de pie», while the entries' semantic grupo, clase, ids, ASIGNACION_FONDOS repository, saved scenes, scene AI and photo reading stay unchanged and Shopify /catalogo is untouched. Searching «Backing» matches every Backing card (the word joins their search text in the panel only) and the original names still match. Cards add by click, drag and keyboard as today. New strings in src/components/tres-d/textos-taller-esenciales.ts. New scripts/test/test-backing-piloto.ts covers group membership, absence from the former groups, search and adding; update the group-dependent counts and re-pin the affected DORADO_DE_SIEMPRE hashes in scripts/test/test-anadir-repositorios.tsx and scripts/test/test-anadir-repositorios-ui.ts, stating in the task report that the HTML diff only moves the seven cards and adds the new ones.
- T3.14 — Review rendered Taller essentials against the design

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T3.2, T3.3, T3.4, T3.5, T3.6, T3.7, T3.8, T3.11, T3.12, T3.13, T3.15.
