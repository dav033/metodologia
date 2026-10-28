# Brief de interfaz — SP-3 · Elementos esenciales del Taller: estructuras Backing y tipos de mesa investigados y modelados, tarjetas por tipo y exportación a Blender de todos los tipos

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

El propietario aprueba, a partir de una propuesta fundamentada en fuentes, qué nuevas estructuras Backing y tipos de mesa incluirá el piloto; el Taller los modela como mesas paramétricas y muebles paramétricos mediante registros exhaustivos de tipos, y los integra con la búsqueda, la IA de escena, la lectura de fotos, las frases en inglés y la lista de compras; Fondos y muebles ofrece una tarjeta por tipo de mesa (los ocho tipos existentes, incluido el rectangular, más los nuevos) que lo agrega con su tamaño predeterminado y abre el editor de mesa existente, y un grupo Backing con los siete elementos existentes trasladados desde sus grupos anteriores, más los nuevos; el GLB de cada tipo de elemento que enumera el código, por separado y en una escena completa, se abre en Blender LTS portable con la misma distribución, dimensiones en metros y colores base, o el tipo que falla se enumera como defecto.

## Requisitos que cubre

- R9: El Taller ofrecerá una tarjeta de creación por cada tipo de mesa paramétrica —los ocho tipos existentes, incluido el rectangular, más los tipos nuevos que el propietario apruebe a partir de la investigación de SP-3, modelados en el generador de mesas paramétricas— que agregue la mesa con su tamaño predeterminado y abra el editor de mesa existente (tamaño, sillas, distribución); la lista de compras mostrará cantidades y dimensiones sin precios de alquiler (modificado el 2026-10-27, corrección del propietario).
- R10: Cuando un usuario exporte a GLB, el sistema generará un archivo que Blender pueda abrir con la distribución, las dimensiones y los colores de la escena.
- R11: Fondos y muebles del Taller tendrá un grupo Backing con panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, trasladados desde sus grupos visuales anteriores, más las nuevas estructuras Backing que el propietario apruebe a partir de la investigación de SP-3, modeladas como elementos del Taller con compatibilidad con la búsqueda, la IA de escena, la lectura de fotos, las frases en inglés y la lista de compras; se mantendrá la compatibilidad con los ID existentes, las escenas guardadas, la búsqueda por nombre original y el descubrimiento mediante IA/fotos; Shopify /catalogo no cambia (propietario, ronda 9 q3; modificado el 2026-10-27).

Secciones de SPEC.md que nombran este subplan (léelas): «Comportamiento — SP-3 y SP-4 (respuestas de la ronda 9)»

## Criterios de producto

- Fondos y muebles muestra una tarjeta de creación por cada tipo de mesa paramétrica: los ocho tipos existentes y cada tipo nuevo aprobado. Cada tipo se encuentra al buscar su nombre o sus sinónimos (incluido rectangular); tocar una tarjeta agrega ese tipo con su tamaño predeterminado (rectangular: 240 × 90 × 75 cm), con tantas sillas predeterminadas como quepan, hasta ocho, lo selecciona y abre el editor de mesas existente.
- El editor de mesas existente muestra las etiquetas de dimensiones y los límites correctos para cada tipo de mesa, y conserva la advertencia de capacidad y la función de deshacer. Las mesas Imperial fijas y las demás piezas fijas siguen disponibles.
- Los conteos de tarjetas del repositorio y del selector Mobiliario incluyen exactamente las tarjetas de tipos de mesa en lugar de la antigua tarjeta única «Mesa con sillas a medida».
- Fondos y muebles tiene un grupo Backing que muestra una vez cada uno de estos elementos: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico y cada Backing nuevo aprobado. Los siete ya no aparecen en «Fondos y tapetes» ni en «Decorado de pie», y cada tarjeta agrega su elemento al tocarla o arrastrarla.
- Buscar «Backing» encuentra todas las tarjetas Backing y los nombres originales siguen encontrando cada elemento; los ids, la asignación a repositorios, las escenas guardadas, la IA de escenas y la búsqueda por foto resuelven los mismos ids, y Shopify /catalogo no cambia.
- La suite del repositorio del catálogo pasa y cada elemento Backing sigue asignado a su repositorio anterior.
- Las vistas de teléfono, tableta y escritorio de las tarjetas de tipos de mesa, el editor de mesas con un tipo nuevo, el grupo Backing y el menú de exportación sin cambios coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos accionables se asignan a las tareas responsables.

## Flujos de usuario

1. Agregar una mesa por tipo
   1. Abre el panel Añadir de Taller 3D y Fondos y muebles (pestaña Utilería dentro de «Todos», o el repositorio Mobiliario)
   2. Ve una tarjeta por tipo de mesa en el grupo «Mesas»: Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, En U y una tarjeta por cada tipo nuevo que apruebe el propietario (se desconocen hasta que se apruebe la investigación de SP-3; las maquetas los muestran como marcadores de posición identificados: «Mesa nueva A», «Mesa nueva B»)
   3. Opcionalmente, busca «rectangular» y encuentra su tarjeta
   4. Toca la tarjeta: la mesa aparece con su tamaño predeterminado y sus sillas predeterminadas, queda seleccionada y el editor de mesas existente se abre en el inspector
   5. Edita el tamaño, las sillas y la disposición como hoy
2. Encontrar y agregar un Backing
   1. Abre Fondos y muebles (o el repositorio Escenografía)
   2. Abre el nuevo grupo Backing con los siete elementos existentes y los nuevos Backings aprobados (las maquetas muestran los nuevos como marcadores de posición identificados: «Backing nuevo A», «Backing nuevo B»)
   3. Encuentra uno explorando, buscando «Backing» o usando su nombre original
   4. Lo agrega tocando o arrastrando la tarjeta, igual que cualquier otra tarjeta

## Pantallas y estados

- Grupo «Mesas» con una tarjeta por cada tipo de mesa paramétrica, en lugar de la tarjeta única «Mesa con sillas a medida» de hoy; cada tarjeta usa el estilo existente, con una miniatura de ese tipo en su tamaño predeterminado
- El contador de resultados del panel y el conteo del selector del repositorio Mobiliario incluyen las tarjetas de tipos de mesa
- La búsqueda «rectangular» muestra la tarjeta Rectangular; el estado existente sin resultados
- La línea de estado existente después de agregar una mesa, con el nombre del tipo agregado
- El editor de mesas existente con un tipo nuevo seleccionado: sus etiquetas de dimensiones y los límites de los controles deslizantes para esa forma
- Grupo Backing en Fondos y muebles y en la vista del repositorio Escenografía: las siete tarjetas existentes y las nuevas tarjetas Backing, una vez cada una
- «Fondos y tapetes» y «Decorado de pie» sin las siete tarjetas trasladadas
- Anchos de teléfono, tableta y escritorio del panel Añadir
- Si no se aprueban piezas nuevas: «Mesas» contiene las mesas fijas y las ocho tarjetas de tipos, y Backing contiene los siete elementos existentes

## Superficie existente a modificar

La maqueta es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una página de inicio: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- rutas: `/3d`
- rutas de archivo: `src/components/tres-d/PanelAnadir.tsx`, `src/components/tres-d/FondosYMuebles.tsx`, `src/components/tres-d/DibujoFondo.tsx`, `src/components/tres-d/EditorConjuntoMesa.tsx`, `src/components/tres-d/Inspector.tsx`, `src/components/tres-d/ListaEscenografia.tsx`, `src/components/tres-d/ExportarEscenaTaller.tsx`, `src/lib/catalogo/anadir-repositorios.ts`, `src/lib/catalogo/asignacion-fondos.ts`, `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `src/lib/globos3d/fondos-escenografia.ts`, `src/lib/globos3d/mobiliario-catalogo.ts`
- componentes: `PanelAnadir`, `FondosYMuebles`, `DibujoFondo`, `EditorConjuntoMesa`, `Inspector`, `ListaEscenografia`, `ExportarEscenaTaller`
- repositorio t12: `/home/david/dev/pictures-wt/t12`
- repositorio pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: SP-3 se trasladó a M2 (propietario 2026-10-27, respuesta B). Los nuevos tipos de mesa y Backings se desconocen hasta que el propietario apruebe la lista de investigación durante la ejecución (T3.2, T3.4), así que el diseño los muestra solo como marcadores de posición identificados. Las etiquetas de dimensiones de cada tipo provienen de un único registro (ETIQUETA_MEDIDAS_MESA, T3.3). Leer en origin/main a9f3d6e5 (el checkout registrado de pictures tiene los mismos archivos de Taller). La funcionalidad ya existe; SP-3 solo cambia los puntos de entrada y agrega piezas. Hoy: el panel Añadir (PanelAnadir) tiene un selector de repositorio Todos / Sempertex / Mobiliario / Escenografía; en «Todos», FondosYMuebles está en la pestaña Utilería con el encabezado «Fondos y muebles · no son globos: no cotizan» y cuatro grupos de tarjetas de tres columnas (miniatura + nombre): «Fondos y tapetes», «Sillas y asientos», «Mesas», «Decorado de pie». «Mesas» muestra las mesas fijas del catálogo (Imperial, redonda, cóctel, postres…) y termina con UNA tarjeta «Mesa con sillas a medida» (redonda de 1.5 m con ocho sillas Tiffany); sus términos de búsqueda omiten «rectangular»; al tocarla, agrega una mesa redonda, la selecciona y muestra una línea de estado. Luego, el inspector muestra EditorConjuntoMesa: «Mesa» (selector Tipo de mesa, con los ocho tipos, controles deslizantes Diámetro / Lado / Largo / Ancho total, Ancho de la mesa, Alto de la tapa, colores de Mantel, tapa/mantel y patas, + camino de mesa) y «Sillas» (Cantidad − / + con «caben N», la advertencia «Se pidieron X, pero en esta mesa con esta disposición solo caben Y», Tipo de silla, Disposición, colores, + cojín). panel_redondo, media_luna y arcos_chiara están en «Fondos y tapetes»; pedestales, aro_metalico, aro_hexagonal (mostrado como «Marco hexagonal metálico») y arco_metalico están en «Decorado de pie». La lista de compras ya muestra los muebles como «N × Mesa rectangular 240×90 (mobiliario)» bajo «Mobiliario · no es producto de la tienda», sin precio y con el conteo real de sillas colocadas. Exportación: el menú «Exportar» de la cabecera con «Descargar PNG · 3000 px» y «Descargar modelo GLB», estados «Preparando GLB…», «Descarga GLB iniciada.» y «No se pudo exportar GLB: …»; SP-3 no lo cambia. No hay capturas de pantalla guardadas en el repositorio.

## No debe cambiar

- El shell de Taller, la cabecera, la barra lateral, el visor, la disposición del inspector y los controles del editor de mesas (solo se agregan las etiquetas de dimensiones y los límites de los tipos nuevos)
- El estilo de las tarjetas (miniatura y nombre) y las demás tarjetas de cada grupo
- El menú de exportación, sus acciones y sus estados; la disposición de la lista de compras
- Los ids de muebles y elementos existentes, sus repositorios, las escenas guardadas y la búsqueda por nombre original, IA y foto
- Shopify /catalogo y sus categorías (Backing existe solo en Taller)

## Reglas de copy

- Interfaz en español; todas las cadenas nuevas van en src/components/tres-d/textos-taller-esenciales.ts para su traducción posterior
- Los nombres de las tarjetas de mesas son los nombres de tipos existentes (Mesa redonda, Mesa rectangular…); las piezas nuevas llevan los nombres en español que apruebe el propietario en T3.2; hasta entonces, las maquetas usan marcadores de posición visiblemente identificados («Mesa nueva A», «Backing nuevo A») y nunca nombres, dimensiones o imágenes inventados
- El grupo se llama «Backing»; no se inventan descripciones
- Las líneas de muebles muestran la cantidad y las dimensiones, nunca un precio de alquiler
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T3.1 — Copiar el contrato de diseño aprobado de Taller essentials
- T3.9 — Una tarjeta de creación por tipo de mesa en Fondos y muebles
  - Objetivo: Siguiendo design/contracts/taller-esenciales@v1.md, reemplazar la única tarjeta «Mesa con sillas a medida» del grupo «Mesas» en src/components/tres-d/FondosYMuebles.tsx por una tarjeta por cada tipo de TIPOS_MESA (los ocho tipos existentes y los nuevos aprobados, en el orden de TIPOS_MESA, después de las mesas fijas del catálogo, que se mantienen), cada una con el nombre NOMBRE_MESA[tipo], una miniatura de ese tipo en su tamaño PARTIDA_MESA y el texto de búsqueda NOMBRE_MESA más SINONIMOS_MESA, para que «rectangular» encuentre la tarjeta Rectangular; TEXTO_CONJUNTO desaparece. Al tocar una tarjeta, se llama a agregarConjuntoPorDefecto(escena, maxNodos, tipo) (src/lib/globos3d/mobiliario-conjunto-escena.ts; hoy siempre crea una mesa redonda con 8 sillas), que agrega ese tipo en su tamaño PARTIDA_MESA con sillasDePartida(tipo) sillas, lo selecciona, abre el editor de mesas existente y muestra la línea de estado existente con el nombre del tipo y SINGULAR_MESA. En src/components/tres-d/EditorConjuntoMesa.tsx las etiquetas de dimensiones provienen de ETIQUETA_MEDIDAS_MESA en lugar de la cadena condicional etiquetaAncho; los controles, la advertencia de capacidad y la función de deshacer se mantienen. contarFondosYMuebles y fijasDe (src/lib/catalogo/anadir-repositorios.ts) cuentan las tarjetas de tipos en lugar de la tarjeta única. Todas las cadenas nuevas van en src/components/tres-d/textos-taller-esenciales.ts. El nuevo scripts/test/test-taller-mesas-piloto.ts cubre las tarjetas, la búsqueda, la adición con valores predeterminados según el tipo, las etiquetas y los límites del editor para cada tipo, la advertencia de capacidad y la función de deshacer; en scripts/test/test-anadir-repositorios.tsx y scripts/test/test-anadir-repositorios-ui.ts, expresar los conteos de Mobiliario y Todos en función de TIPOS_MESA.length y volver a fijar los hashes DORADO_DE_SIEMPRE cuyo filtro muestra el grupo «Mesas», indicando en el informe de la tarea que el diff de HTML solo reemplaza la tarjeta de mesas.
- T3.10 — Grupo Backing en Fondos y muebles con los siete elementos Backing existentes y los nuevos
  - Objetivo: Siguiendo design/contracts/taller-esenciales@v1.md, mostrar en src/components/tres-d/FondosYMuebles.tsx un grupo «Backing», en Fondos y muebles bajo «Todos» y en la vista del repositorio Escenografía, que muestre cada elemento de IDS_BACKING una sola vez (los siete existentes y los nuevos aprobados) mediante grupoVisibleDe (src/lib/globos3d/backing.ts), solo para su presentación: los siete ya no aparecen en «Fondos y tapetes» ni en «Decorado de pie», mientras que el grupo semántico, la clase, los ids, el repositorio ASIGNACION_FONDOS, las escenas guardadas, la IA de escenas y la lectura de fotos de las entradas se mantienen sin cambios, y Shopify /catalogo no se modifica. Buscar «Backing» coincide con cada tarjeta Backing (la palabra se agrega al texto de búsqueda solo en el panel) y los nombres originales siguen coincidiendo. Las tarjetas se agregan al hacer clic, arrastrarlas o usar el teclado, como hoy. Las cadenas nuevas van en src/components/tres-d/textos-taller-esenciales.ts. El nuevo scripts/test/test-backing-piloto.ts cubre la pertenencia al grupo, la ausencia en los grupos anteriores, la búsqueda y la adición; actualizar los conteos que dependen de los grupos y volver a fijar los hashes DORADO_DE_SIEMPRE afectados en scripts/test/test-anadir-repositorios.tsx y scripts/test/test-anadir-repositorios-ui.ts, indicando en el informe de la tarea que el diff de HTML solo traslada las siete tarjetas y agrega las nuevas.
- T3.14 — Revisar la vista renderizada de Taller essentials frente al diseño

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, sin diseño ni revisión), verificación, expected_paths, shared_resources, classification y estimates, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T3.2, T3.3, T3.4, T3.5, T3.6, T3.7, T3.8, T3.11, T3.12, T3.13, T3.15.
