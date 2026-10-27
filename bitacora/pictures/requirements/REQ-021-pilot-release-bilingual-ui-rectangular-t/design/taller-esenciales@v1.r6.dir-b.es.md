---
name: Mesa de montaje
status: draft
subplan: SP-3
contract_candidate: taller-esenciales@v1
revision: r6
direction: b
requirements: [R9, R10, R11]
created: 2026-10-26
---

# Mesa de montaje — dirección B

Exploración cinética/espacial independiente, no es el contrato canónico. Aquí no se aprueba ninguna dirección ni contrato. Fuente del comportamiento del producto: `taller-esenciales@v1.r6.behavior.md`, contrastado con SPEC.md, PLAN.md y PLAN.json SP-3 / T3.1–T3.8. El propietario elige una dirección antes de que un finalizador redacte el contrato canónico de doce secciones. Esta delegación solo tiene a su cargo sus dos miniaturas, TSX, HTML compilado, esta nota y el JSON de ocho ejes, además del resultado de delegación requerido.

## Concepto y gesto memorable

El Taller es un lugar para montar un evento: una mesa rectangular, sillas Tiffany, paneles redondos, aros metálicos, pedestales y una estructura de globos. Su superficie de trabajo se convierte en una plataforma de montaje con medidas. La mesa seleccionada se asienta sobre un piso axonométrico; un instante después, Backing se eleva hasta su posición y el inspector se alinea con una esquina de referencia. Las líneas discontinuas de cota se despliegan alrededor de la composición. El movimiento expresa la colocación de objetos físicos; no desplaza un campo mientras alguien introduce un valor.

El gesto memorable es **el objeto seleccionado que se asienta entre sus cotas mientras su inspector se alinea con una escuadra física**. La escena se entiende desde el inicio. No hay interacciones que dependan solo de arrastrar, gestos de órbita ni puntos interactivos ocultos. Los botones estándar con etiquetas de texto proporcionan todas las acciones de exploración.

Por qué no es la opción predeterminada: la superficie central muestra un montaje real de evento en lugar de un tablero; la navegación es una secuencia vertical y delgada de estaciones de trabajo en vez de pestañas genéricas de página; y el área de trabajo está abierta como una carpeta con secciones pautadas en vez de tarjetas apiladas. Solo los objetos relacionados usan un estante ilustrado pequeño. La tipografía sitúa las medidas físicas editables por encima de los metadatos complementarios. La composición obtiene su identidad de los materiales y verbos del producto.

## Dos miniaturas, creadas primero

1. `taller-esenciales@v1.r6.dir-b.html.candidate-1.html` — **elegida: Mesa de montaje.** Columna de herramientas independiente, escena amplia e inspector a la derecha. La elección se hizo tras inspeccionar visualmente ambas miniaturas a 1150 px. El escenario y el formulario tienen áreas de lectura estables e independientes, y comparten el borde superior.
2. `taller-esenciales@v1.r6.dir-b.html.candidate-2.html` — Escenario por capas. Las etiquetas de la escena se convierten en rótulos físicos inclinados sobre el piso. Se descartó porque los paneles flotantes compiten con los objetos y hacen menos estable el contenido extenso del inspector. También se acerca al lenguaje de pase físico ya explorado en SP-2.

Son composiciones visuales intencionalmente pequeñas e independientes. Usan HTML/CSS/SVG en línea y la preferencia de sistema para el tema claro/oscuro. La maqueta completa elegida usa el constructor real de la biblioteca, selectores nativos explícitos y fixtures completos de comportamiento/estado.

## Registro visual e identidad compartida

Lee los documentos hermanos `cuentas-admin@v1.r7.dir-a.md`, `dir-b.md` y `dir-c.md`. La identidad compartida de Pictures se conserva mediante la paleta del Taller, una tipografía sans de sistema discreta, controles habituales, un contexto de cuentas solo por invitación y objetos físicos de decoración con globos. SP-2 B ya usa un pase de acceso con bisagra y un dock inferior persistente; aquí no se repiten ni la composición ni la navegación. SP-2 C usa composiciones de listas y credenciales; esta dirección centra la geometría de la escena y las medidas ortogonales. Aquí el escenario es la superficie de trabajo real, no una ilustración para una pantalla de acceso.

Evidencia del proyecto, consultada en modo de solo lectura tanto en `t12` como en `pictures`/`asesor`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `FondosYMuebles.tsx`, `EditorConjuntoMesa.tsx` y `src/lib/globos3d/mobiliario-conjunto-tipos.ts`. Los ocho nombres de mesas, valores predeterminados, límites de dimensiones, tipos de sillas y disposiciones provienen de esa fuente. Pictures es propietario de la interfaz de exportación existente; esta exploración no cambia la propiedad del código fuente.

## Ocho ejes

| Eje | Dirección concreta |
|---|---|
| Concepto | Una plataforma de montaje con medidas para la mesa, las sillas realmente colocadas y la composición de Backing. Los objetos físicos y las escuadras de referencia reemplazan la decoración genérica de un tablero. |
| Diseño / composición | A 1280 px: columna de herramientas de 112 px, escena flexible, carpeta de 350 px y separaciones de 24 px. El encabezado, la ilustración y el pie de escala de la escena ocupan un mismo marco. El inspector y el escenario comparten la alineación superior; el pie de página se alinea con el borde izquierdo del escenario y el borde derecho de la carpeta. |
| Navegación | Seis estaciones verticales de herramientas con texto e icono: Mesas, Medidas, Backing, Lista de compra, IA de escena, Exportar. El botón activo tiene un borde neutro y una escuadra desplazada. Los controles con nombre en el encabezado abren un Dialog y un Popover reales. En móvil se usa una cuadrícula de herramientas de 3 columnas, no un dock inferior. |
| Tipografía / escala | Sans de sistema compartida; título del proyecto de 24 px, encabezado de carpeta de 26 px, título de sección de 16 px, texto de 13–14 px. Las dimensiones usan una tipografía monoespaciada de 24 px y el total de sillas colocadas es de 32 px. Las dimensiones de la escena son texto SVG de 14 px; los conteos de la lista usan cifras tabulares y alineación a la derecha. |
| Densidad / forma | Escena abierta, carpeta compacta con divisiones y estante de objetos relacionados de dos columnas. Relleno del inspector de 26 px, separaciones estructurales de escritorio de 24 px, márgenes laterales en móvil de 20 px y relleno del panel de 24 px. Los controles tienen al menos 44 px de alto; los controles numéricos, 56 px. Sin pilas de tarjetas anidadas. |
| Componentes distintivos | Escenario de evento SVG personalizado y líneas de cota; estación de herramientas con escuadra; carpeta cuadrada; campos y botones reales de shadcn/Base UI; Dialog de compras y Popover de exportación de Animate UI. Las miniaturas son siluetas derivadas de la fuente, no imágenes de archivo remotas. |
| Lógica del color | Tokens de superficie del Taller de Pictures: panel claro #faf9fc, tarjeta #ffffff, escena #ebe7f1; panel oscuro #16131d, tarjeta #1d1926, escena #1a1722. Par primario #6d3fe0/#ffffff en tema claro y #b9a4ff/#120b24, accesible y existente, en tema oscuro. Los bordes marcados de los controles usan Taller medio; los divisores decorativos usan Taller borde. Los materiales lavanda son datos de la escena, no decoración de la navegación. |
| Movimiento | Resorte espacial expresivo con rigidez 220/amortiguación 16/masa .9: la mesa cae en su lugar, Backing se eleva con el escalonamiento de perfil de .09 s, la carpeta se alinea desde una pequeña rotación y un desplazamiento horizontal. Las reglas aparecen durante 520 ms con cubic-bezier(.34,1.4,.64,1); los objetos se elevan 4 px y se inclinan 2° al pasar el puntero, las estaciones de herramientas se desplazan 3 px. Los controles usan una respuesta de 200 ms. Los perfiles natural/sutil reducen recorrido y duración. El movimiento reducido y `?still=1` muestran la geometría final y conservan las mismas acciones. |

El JSON hermano nombra selectores renderizados para composición, navegación, tipografía y movimiento. Se probaron con la sonda EVIDENCE real del kit; todos los selectores pasaron. `.dimension-line` tiene una regla CSS de fotogramas clave con duración finita; `.object-card .mini-stage` y `.tool-spine button` tienen transiciones reales al pasar el puntero. El movimiento no se atribuye únicamente a la importación de una biblioteca. Se observaron en Chromium las secuencias de animación expresiva activas.

## Comportamiento conservado y límites ilustrativos

- **Mesas / `tables`:** ocho tarjetas de tipos paramétricos, primero el tipo rectangular con el valor predeterminado de origen de 2.40 × 0.90 × 0.75 m. Un clic crea el elemento seleccionado y abre su inspector; no hay formulario previo a la creación. Se comprobaron los ocho valores predeterminados de origen y los límites válidos del inspector. Las piezas imperiales fijas siguen en Mobiliario, fuera del estante modificado.
- **Medidas / `table-editor`:** rangos de dimensiones y etiquetas de unidades de origen, sillas solicitadas, cantidad colocada, siete tipos de silla, cinco disposiciones, mantel y color de material con nombre. La última geometría válida se conserva si la entrada no es válida. Deshacer restaura el elemento anterior. La edición numérica conserva el foco. El ejemplo de capacidad muestra 8 sillas colocadas en 2.40 × 0.90 m y 12 en 3.00 × 1.00 m; producción debe usar el motor de perímetro existente, no esta fórmula de ejemplo. Al cambiar una solicitud parcial de 12 a 4, se resuelve la advertencia y se cuentan 4 en la lista.
- **Backing / `backing`:** exactamente siete IDs originales, todos se pueden agregar: `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. Se conserva el nombre “Marco hexagonal metálico” y el alias de búsqueda “aro hexagonal”. El alias solo coincide con la tarjeta correspondiente; se mantiene la búsqueda por nombre original. No se propone una ruta independiente de Shopify, una tarjeta duplicada ni una migración del repositorio/ID semántico.
- **Lista / `shopping`:** cantidades y dimensiones reales con divisiones, sin precio de alquiler ni total inventado. Tanto la vista completa como el modal real consumen la misma mesa seleccionada, las sillas colocadas y los elementos de Backing agrupados. El título y la descripción del modal son accesibles por programación; Escape cierra el modal y devuelve el foco al control que lo abrió.
- **IA / `ai`:** indicación, propuesta ilustrativa local, acciones explícitas para aplicar/descartar y ruta de edición manual. No se realiza ninguna llamada de IA, de pago ni de otro tipo. En producción, `agregar_mesas`, `cambiar_mesas` y `cambiar_sillas` deben usar las mismas operaciones de escena existentes que la edición manual; esta maqueta no demuestra que sean equivalentes.
- **Exportar / `export`:** transferencia a GLB/Blender, escala en metros, pasos de importación y limitaciones de iluminación/materiales. El Popover del encabezado conserva el PNG existente como opción hermana y abre la transferencia completa de GLB. Los bloqueos pendientes impiden duplicar la exportación; las piezas parciales o sin resolver bloquean la exportación; los errores conservan la escena y ofrecen reintentar; el estado vacío explica por qué se requiere una pieza. Al completar, se muestra “Descarga GLB iniciada”, que se indica explícitamente como simulada. Este artefacto no genera un GLB falso ni afirma que se haya verificado Blender.

Alcance del fixture: una mesa seleccionada ilustra los valores predeterminados y las ediciones; reemplazar la mesa seleccionada al explorar las tarjetas de tipos no prescribe reemplazar una mesa existente de la escena en producción. Varias mesas, manipulación 3D real, geometría/materiales arbitrarios de elementos, IDs guardados, reconocimiento por IA/fotografías, generación de GLB e importación real a Blender siguen siendo responsabilidades de implementación. El SVG ilustra el flujo de mesa rectangular seleccionado, no constituye un segundo motor 3D. Las ediciones locales no implican un guardado en el servidor. Aquí se usa texto en español, como en el borrador compartido; SP-8 es responsable del despliegue ES/EN. Las etiquetas nativas y el diseño usan ajuste de texto y pistas flexibles en vez de anchos de texto fijos.

## Estados, diálogos, reflujo y acceso

La interfaz de planificación visible conserva **Mockup**, `view`/Vista nativo, `state`/Estado, `scene`/Diálogo, `theme`/Tema y `motion`/Movimiento. Los once ID de estado siguen disponibles para selección. Las opciones de escena son Ninguno, Lista de compra y Exportar. Los selectores de planificación desmontan y vuelven a montar deliberadamente un ejemplo de vista/estado; el tema y el movimiento conservan el estado del componente. Los valores de prueba entre vistas permanecen locales a la sesión de la página y nunca implican persistencia.

| Estado | Manifestación visible y recuperación |
|---|---|
| `ready` | Escena estable, herramientas con nombre y contenido de trabajo pertinente. |
| `loading` | Esqueletos de contenido en el folio con una etiqueta de carga; se conservan la escena y la estructura; no se muestran las acciones que dependen del contenido. |
| `empty` | Biblioteca sin coincidencias con Limpiar búsqueda, tabla sin elementos seleccionados con Ver mesas, lista/escena vacía o GLB deshabilitado con una explicación. La IA conserva un mensaje editable sin conversación previa. |
| `error` | Error contextual, se conserva la escena anterior y se ofrece Reintentar. Sin trazas de pila ni archivos de exportación inventados. |
| `success` | Ejemplo completado con nombre; la exportación informa específicamente que se inició la descarga y que es una simulación. |
| `validation` | Pertinente a la edición numérica y a la IA. Error de campo vinculado/estado no válido y recuperación. Las demás vistas conservan su contenido habitual en lugar de inventar un comportamiento de validación. |
| `disabled` | Motivo legible junto al elemento; botones que cambian contenido deshabilitados. La lista informativa sigue siendo legible. |
| `partial` | Pertinente a la capacidad de la mesa, una propuesta de IA sin aplicar y una exportación sin resolver. Muestra los valores solicitados/ubicados o una explicación explícita del bloqueo de la exportación. Las demás vistas no inventan semánticas de catálogo parcial. |
| `permission-denied` | No se muestran escenas privadas, títulos de proyectos, contenido de compras ni acciones de archivos; se ofrece una opción para volver al destino a cargo de SP-1/SP-2. |
| `offline` | Escena local conservada, campos/lista locales y GLB cargado disponibles. Se deshabilitan la incorporación/actualización de la biblioteca remota y la IA; Reintentar no afirma que se haya guardado en el servidor. |
| `pending` | Pertinente a la IA/exportación, con texto de espera identificado y prevención de envíos duplicados. Las demás vistas no crean una operación asíncrona nueva. |

Composición adaptable:

- **320–359 px:** márgenes exteriores de 20 px, cuadrícula de herramientas de dos columnas, campos y estantes de una columna. Sin desplazamiento horizontal de la página.
- **360–767 px:** cuadrícula de herramientas de tres columnas, escena seguida del folio activo en el flujo del documento, mediciones/estante de dos columnas cuando quepan. Controles de formulario de tamaño completo, relleno del folio de 24 px. Ancho del diálogo igual al ancho de la ventana menos 40 px y desplazamiento vertical limitado; el Popover también cabe en este margen.
- **768–1100 px:** carril de herramientas de 82 px, escena flexible, folio de 310 px, separaciones estructurales de 16 px y márgenes exteriores de 24 px. Las etiquetas de escena se apilan cuando el espacio es limitado. Sin reducir la fuente por debajo de 11 px.
- **1101–1439 px:** carril de herramientas de 112 px, escena flexible, folio de 350 px, separaciones de 24 px y márgenes exteriores de 32 px.
- **≥1440 px:** herramientas de 128 px, escena flexible, folio de 380 px, separaciones de 28 px y relleno del folio de 30 px; el espacio de trabajo tiene un ancho máximo de 1600 px.

La composición permite intencionalmente el desplazamiento vertical del documento para estantes/inspectores extensos; no oculta el pie de página bajo una hoja fija. Se comprobó el reflujo de toda la página en 320, 360, 390, 768, 1024, 1280 y 1440 px con ambos temas en las seis vistas. Los campos/selectores nativos específicos del tema tienen tokens de borde explícitos; este subplan no tiene casillas de verificación ni incorpora el tratamiento ilegible de las casillas mencionado en los comentarios anteriores.

Los objetivos de accesibilidad son WCAG 2.2 AA para la superficie modificada: navegación/botones/encabezados semánticos, etiquetas de campo visibles, unidades/rangos y errores vinculados, foco visible de 3 px, contraste del texto normal ≥4.5:1 y de los límites de controles ≥3:1. La edición numérica/de listas ofrece una alternativa al lienzo y la escena tiene un resumen accesible. Se anuncian los estados y errores. El comportamiento modal real proporciona contención del foco, Escape y retorno; el Popover de exportación sigue siendo no modal. El modo de movimiento reducido/estático conserva todo el contenido y las acciones con las transformaciones finales; no hay efectos decorativos infinitos. Los cambios dinámicos de preferencias también fuerzan la geometría visible final. Esta es una comprobación de una maqueta renderizada, no una certificación WCAG completa ni una implementación accesible del motor de autoría.

## Objetivos de revisión visual para esta dirección

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-01 | 1101–1439 px | listo | Las herramientas, la escena y el folio ocupan tres columnas de distinto ancho con los bordes superiores alineados. |
| B-02 | ≥768 px | listo | El borde izquierdo del pie de página coincide con el de la escena; el derecho coincide con el del folio. |
| B-03 | 320–767 px | listo | La escena y el folio se apilan sin desplazamiento horizontal de la página. |
| B-04 | Todos | listo | Al crear un rectángulo, se abre el inspector con las medidas 2.40 × 0.90 × 0.75 m. |
| B-05 | Todos | parcial | Se muestran juntos los recuentos de sillas solicitadas y colocadas. |
| B-06 | Todos | parcial | Al reducir la solicitud a cuatro, la lista se actualiza para mostrar cuatro sillas colocadas. |
| B-07 | Todos | validación | Una entrada numérica no válida conserva la última medida válida de la escena. |
| B-08 | Todos | listo | El estante de revestimientos contiene una sola vez cada una de las siete entradas originales distintas. |
| B-09 | Todos | listo | La búsqueda de “aro hexagonal” muestra únicamente Marco hexagonal metálico. |
| B-10 | Todos | compras | Al cerrar el modal de compras con Escape, se restaura el foco. |
| B-11 | Todos | pendiente | No se puede volver a ejecutar la acción GLB durante la preparación. |
| B-12 | Todos | éxito | El mensaje de GLB indica que el proceso se inició y deja explícito que es una simulación. |
| B-13 | Todos, ambos temas | listo | Los bordes de los campos de entrada y los selectores, así como el foco del teclado, siguen siendo visibles sobre su superficie. |
| B-14 | Todos | movimiento reducido | Mesa, Revestimiento y folio muestran sus transformaciones finales y conservan controles equivalentes. |
| B-15 | Todos | permiso denegado | No se muestran datos del proyecto ni de la escena. |

## Componentes, compilación y verificación honesta

Procedencia de los componentes instalados:

| Origen / id | Variante o uso | Importación |
|---|---|---|
| shadcn/Base UI `button` | predeterminado, contorno, sin fondo; deshabilitado/retroalimentación/navegación | `@/components/ui/button` |
| shadcn/Base UI `input` | búsqueda y dimensiones numéricas; no válido/deshabilitado | `@/components/ui/input` |
| shadcn `textarea` | indicación | `@/components/ui/textarea` |
| shadcn `alert`, `skeleton` | retroalimentación de estado y carga estable | `@/components/ui/alert`, `@/components/ui/skeleton` |
| shadcn/Animate UI `dialog` | lista de compras, modal real | `@/components/ui/dialog` |
| shadcn/Animate UI `popover` | grupo de exportación | `@/components/ui/popover` |
| composiciones personalizadas | área SVG medida, siluetas, carpeta cuadrada, selectores de productos nativos y tabla HTML | TSX de la dirección; no se afirma el uso de bibliotecas no instaladas |
| tiempo de ejecución / movimiento | selectores de planificación nativos, resortes adaptados al perfil | `@kit/mockup`, `@kit/motion`, `motion/react` |

El mapeo de roles reutiliza `--taller-panel`, `--taller-tarjeta`, `--taller-visor`, `--taller-texto`, `--taller-medio`, `--taller-borde`, `--taller-primario`, `--taller-acento`, `--taller-sobre-acento`, `--taller-peligro` y `--taller-valido`. El mapeo de acciones oscuras usa deliberadamente el par existente acento/sobre-acento, que es legible. `--scene-line` es un alias decorativo propuesto para la cuadrícula, no un límite de control funcional. Los archivos de tema y tokens de origen no se modificaron. La identidad compartida existente tiene prioridad sobre los valores malva predeterminados del kit.

Compilado sin conexión con el comando absoluto `bitacora.py components mockup build` indicado en el brief. Generador: aproximadamente 635 KB, 2187 módulos de origen, JS/CSS/fuentes integrados, marcador de biblioteca real. La cadena de herramientas estaba disponible; no se usó alternativa HTML, instalación de paquetes ni recurso descargado. Las dos miniaturas pequeñas son bocetos exploratorios deliberados, no afirmaciones sustitutas sobre componentes reales.

Registro de verificación:

- Contraste de tokens: `contrast: 158 pairs checked in light and dark, all pass`.
- La auditoría inicial de muestras detectó dos contrastes de texto en botones de recuperación oscuros de 4.12:1. Se corrigieron conjuntamente la superficie y el primer plano del botón de contorno real. Las ejecuciones completas posteriores pasaron; la ejecución final sobre la salida inmutable se registra a continuación.
- Las comprobaciones de interacción pasaron la transferencia de creación/inspector, la retención del foco numérico, 3 × 1 m / 12 sillas, la lista compartida del modal, Escape/devolución del foco, deshacer, retención de la escena ante un valor no válido, siete tarjetas de revestimiento, la búsqueda/adición de alias original/hexagonal y el cierre del Popover de exportación. Se detectó y corrigió una asignación amplia de alias. Se corrigió una aserción de conteo que esperaba que el DOM del modal se eliminara de inmediato para que esperara al estado oculto, ya que el primitivo real conserva el DOM durante la salida.
- Las ocho tarjetas de tipo transfirieron dimensiones válidas predeterminadas por el origen; la recuperación de capacidad de 12 solicitadas → 4 colocadas actualiza la lista compartida. Cero errores de JavaScript en la página y cero solicitudes HTTP/HTTPS durante la ejecución de interacción/reflujo.
- Pasaron 84 combinaciones normales de vista/tema/ancho en siete anchos. Todos los selectores de evidencia JSON pasaron la sonda real del kit. Se observaron cronologías de animación expresivas; las transformaciones visibles finales con una preferencia de movimiento reducido modificada dinámicamente son `none`.
- Se inspeccionaron capturas de pantalla en memoria: ambas composiciones de miniaturas; inspector claro a 1280; revestimiento y tablas oscuros a 1280; inspector y modal de compras oscuros a 390; exportación clara a 390. No se guardaron archivos de capturas fuera de esta tarea.
- Auditoría completa final sobre la salida inmutable: **312/312 renderizados**, 12,637 mediciones de texto y 1,537 paradas de foco a 1280/390 px, ambos temas, todas las vistas/estados declarados y ambas escenas de diálogo. Código de salida 0.

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

SHA-256 del HTML auditado final: `49c8ada09dd1eacbee30d523108d628e68458816cc0e20c83d9fdeaefdc01734`.

No se afirma ningún veredicto de similitud A/B/C; la comparación de exploración entre alternativas corresponde al responsable/la comparación de planificación. No se probaron ningún GLB real, ejecutable de Blender, proveedor de IA, compilación de producción, persistencia, permisos del servidor ni compatibilidad de escenas guardadas. La configuración portátil de Blender ya se resolvió en la ronda 9; la implementación T3.5/T3.6 debe aportar evidencia de importación real y que el responsable la abra, sin sustituirla por esta auditoría de capturas.

## Impacto, decisiones y preocupaciones

**Compatibilidad:** cambio visual respecto de la composición anterior no aprobada, compatible funcionalmente y en cuanto a datos con el comportamiento compartido de SP-3. Si se elige, T3.2 adapta la composición de la tabla/editor/lista/IA, T3.3 la estantería Backing y T3.4 la superficie de exportación. T3.1 copia los bytes canónicos que apruebe el responsable; T3.7 debe volver a renderizar esta estructura. T3.5/T3.6/T3.8 conservan el alcance de verificación del motor y la exportación. No se modifica ningún otro subplan, repositorio de origen, plan, versión del contrato ni estado de aprobación. Esta nota no constituye una aprobación de implementación.

**Preguntas de comportamiento abiertas:** no se descubrieron en esta instantánea. Las decisiones de la ronda 9 sobre la creación predeterminada por tipo, la ausencia de precios de alquiler, un único grupo Backing de siete piezas y la verificación portátil de Blender siguen vigentes. La selección de la dirección y la aprobación del plan/contrato corresponden al responsable; esta exploración no las solicita ni las concede.

**Preocupaciones:** la selección de una sola tabla y la capacidad ilustrada son límites de la maqueta; solo el motor real determina la colocación y la exportación. El texto únicamente en español de aquí hereda el borrador compartido; SP-8 es responsable del texto de producción bilingüe completo. La revisión completa con lector de pantalla y zoom, la integración entre subplanes y la importación en Blender quedan como evidencia futura. La auditoría final renderizada se aprobó; la selección y aprobación del responsable siguen pendientes.
