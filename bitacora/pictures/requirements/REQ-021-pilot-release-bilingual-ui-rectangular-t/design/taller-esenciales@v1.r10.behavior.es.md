# Brief de interfaz — SP-3 · Elementos esenciales de Taller: mesas rectangulares, Backing y exportación a Blender

Fuente compartida de comportamiento para el Designer. Lo que no figura aquí queda fuera del alcance de diseño.

## Resultado esperado

Un usuario agrega una mesa rectangular desde su tarjeta de tipo, edita las dimensiones y las sillas, y ve las cantidades y dimensiones reales sin precios de alquiler en la lista de compras; Taller Fondos y muebles tiene un grupo Backing que contiene los siete elementos existentes, trasladados desde sus grupos visuales anteriores, y conserva los IDs guardados y el descubrimiento mediante IA/fotos; el archivo GLB exportado se abre en la versión portátil LTS de Blender con la misma disposición, dimensiones en metros y colores base.

## Requisitos que cubre

- R9: Cuando un usuario agrega una mesa rectangular, el sistema debe permitirle configurar sus dimensiones y sillas, y actualizar la lista de compras.
- R10: Cuando un usuario exporta a GLB, el sistema debe generar un archivo que Blender pueda abrir con la disposición, las dimensiones y los colores de la escena.
- R11: Taller Fondos y muebles debe tener un grupo Backing que contenga panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, trasladados desde sus grupos visuales anteriores; los IDs existentes, las escenas guardadas, la búsqueda por nombre original y el descubrimiento mediante IA/fotos deben seguir siendo compatibles; Shopify /catalogo no cambia (propietario, ronda 9, pregunta 3).

Secciones de SPEC.md que mencionan este subplan (léelas): «Comportamiento — SP-3 y SP-4 (respuestas de la ronda 9)»

## Criterios de producto

- Al agregar una mesa rectangular, se pueden especificar el largo, el ancho y la cantidad de sillas; la mesa queda seleccionada en el inspector y se actualiza la lista de compras real con las sillas colocadas, incluidos los avisos de capacidad y la opción de deshacer.
- Las herramientas existentes agregar_mesas, cambiar_mesas y cambiar_sillas producen las mismas dimensiones de mesa y cantidades reales de sillas que la edición manual, sin una llamada de pago a la IA.
- Cada tipo de mesa paramétrica existente tiene una tarjeta de creación que agrega una mesa con sus dimensiones predeterminadas y abre el inspector; las mesas rectangulares usan 240 × 90 × 75 cm de forma predeterminada y la lista de compras incluye cantidades y dimensiones, sin precios de alquiler.
- Backing incluye panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, todos disponibles para agregar; los IDs existentes, las escenas guardadas, la propiedad del repositorio, la búsqueda y el descubrimiento mediante IA/fotos siguen siendo compatibles.
- Las siete tarjetas de Backing aparecen una sola vez en el nuevo grupo de Taller y ya no aparecen en sus grupos visuales anteriores; Shopify /catalogo no cambia y los nombres originales y el descubrimiento mediante IA/fotos siguen resolviendo los mismos IDs.
- El GLB exportado conserva las transformaciones reales de la escena en coordenadas globales, las dimensiones en metros, las instancias visibles y los colores base, sin modificar el editor ni hacer llamadas de red; los errores de exportación son visibles y permiten reintentar.
- Las vistas para teléfono, tableta y escritorio de los estados de creación y edición de mesas, Backing y exportación coinciden con el contrato aprobado taller-esenciales@v1, y los hallazgos que requieren acciones se asignan a sus tareas correspondientes.

## Flujos de usuario

1. Añadir y editar una mesa rectangular
   1. Abre Fondos y muebles en el Taller 3D
   2. Toca la tarjeta de un tipo de mesa (Rectangular entre los tipos paramétricos existentes)
   3. La mesa aparece en la escena con su tamaño predeterminado (rectangular de 240 × 90 × 75 cm) y se abre el inspector
   4. Cambia el largo, la profundidad y la cantidad de sillas en el inspector
   5. Ve cómo se actualizan las sillas colocadas y la lista de compra; una advertencia de capacidad explica qué sillas no caben
   6. Deshace el cambio
2. Buscar y añadir un elemento de utilería de Backing
   1. Abre Fondos y muebles
   2. Abre el grupo Backing
   3. Encuentra uno de los siete elementos de utilería (también por su nombre original en la búsqueda)
   4. Lo añade a la escena
3. Exportar la escena a GLB
   1. Abre el control de exportación del Taller
   2. Exporta a GLB y obtiene el archivo
   3. Si la exportación falla, ve el error y vuelve a intentarlo

## Pantallas y estados

- Tarjetas de tipos de mesa en Fondos y muebles (una por cada tipo de mesa paramétrica existente; las piezas Imperial fijas siguen disponibles)
- Inspector de una mesa seleccionada: largo, profundidad y sillas
- Advertencia de capacidad cuando las sillas elegidas no caben en la mesa
- Lista de compra con muebles como cantidades y dimensiones, sin precios de alquiler (sección «no es producto de la tienda»)
- Grupo Backing en Fondos y muebles con panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico, una unidad de cada uno
- Los grupos anteriores «Fondos y tapetes» y «Decorado de pie» sin esas siete tarjetas
- Búsqueda sin resultados en Fondos y muebles
- Estados de exportación: inactivo, exportando, completado, fallido con opción para reintentar
- Anchos de teléfono, tableta y escritorio del Taller

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/3d`
- paths: `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `src/components/tres-d/FondosYMuebles.tsx`, `src/components/tres-d/EditorConjuntoMesa.tsx`, `src/components/tres-d/Inspector.tsx`, `src/components/tres-d/ListaCompra.tsx`, `src/components/tres-d/ListaEscenografia.tsx`, `src/components/tres-d/ExportarEscenaTaller.tsx`, `src/components/tres-d/exportar-escena-glb.ts`, `src/lib/globos3d/mobiliario-conjunto-escena.ts`, `src/lib/globos3d/mobiliario-catalogo.ts`, `src/lib/catalogo/asignacion-fondos.ts`, `src/lib/catalogo/lista-por-repositorio.ts`
- components: `Taller3D`, `FondosYMuebles`, `EditorConjuntoMesa`, `Inspector`, `ListaCompra`, `ListaEscenografia`, `ExportarEscenaTaller`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Paths leídos en origin/main a9f3d6e5 (~/dev/.pictures-wt/login-redirect). FondosYMuebles agrupa actualmente las tarjetas en «Fondos y tapetes», «Sillas y asientos», «Mesas» y «Decorado de pie», y filtra por ASIGNACION_FONDOS; solo crea una mesa paramétrica redonda predeterminada; EditorConjuntoMesa ya admite límites rectangulares y sillas. ListaEscenografia muestra los muebles bajo «no es producto de la tienda». No hay capturas de pantalla guardadas en el repositorio.

## No debe cambiar

- Shopify /catalogo y sus categorías (Backing existe solo en el Taller)
- Los IDs de muebles y elementos de utilería existentes, sus repositorios (ASIGNACION_FONDOS), las escenas guardadas y el descubrimiento por nombre original, IA y fotos
- El shell del Taller, la navegación y los tokens de diseño fuera de las tarjetas, el inspector, la lista de compra y el control de exportación
- El formato GLB (sin formatos de exportación nuevos)

## Reglas de copy

- Interfaz en español; cada cadena nueva en src/components/tres-d/textos-taller-esenciales.ts para traducirla más adelante
- No inventar copy: los nombres de los elementos de utilería y de las mesas son los nombres existentes en el catálogo; el grupo se llama «Backing»
- Las líneas de muebles muestran la cantidad y las dimensiones, nunca el precio de alquiler
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T3.1 — Copiar el contrato de diseño aprobado para los elementos esenciales del Taller
- T3.2 — Añadir mesas rectangulares mediante el editor de mesas existente
- T3.3 — Agrupar los elementos existentes de utilería para fiestas bajo Backing sin cambiar su identidad
- T3.4 — Verificar y corregir la geometría y la exportación de materiales GLB
- T3.7 — Revisar la versión renderizada de los elementos esenciales del Taller frente al diseño

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, no relacionadas con diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T3.5, T3.6, T3.8.
