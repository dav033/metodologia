# Control de conjunto — exploración A

Status: **draft · exploration only**. SP-3, R9/R10/R11; revisión r10, 2026-10-27. Candidato para `taller-esenciales@v1`, sin aprobación ni contrato canónico escrito. La selección y la finalización corresponden al propietario.

Fuente de comportamiento: `taller-esenciales@v1.r10.behavior.md`; contexto: SPEC «Behavior — SP-3 and SP-4 (round 9 answered)» y SP-3 del PLAN. Esta exploración conserva los requisitos, sin diseñar tareas de ingeniería ni modificar repositorios.

## Enfoque sobre la superficie existente

La pregunta de trabajo es: **¿qué mesa y cuántas sillas hay realmente en la escena?** La respuesta permanece junto al inspector: medidas grandes, cantidad solicitada separada de cantidad colocada y aviso de capacidad con deshacer. El catálogo ocupa una columna compacta con dos tarjetas por fila; el visor conserva el centro y la lista se abre desde el botón existente en la cabecera.

Se mantiene `/3d`, cabecera Taller 3D, identidad Pictures/Sempertex, escena, deshacer/rehacer, Foto realista, Exportar, Lista de compra y riel Añadir/Piezas/Plantillas/Sala. Las acciones ajenas al brief son referencias de contexto, con resultado explícitamente fuera de la exploración. No se crea una pantalla comercial, un catálogo Shopify ni una navegación general distinta. La reorganización se limita a catálogo de muebles, edición de mesa, cantidades y exportación GLB.

La cabecera y el riel se basan en ambos checkouts de `src/components/tres-d/Taller3D.tsx`. Se leyeron también FondosYMuebles, EditorConjuntoMesa, Inspector, ListaCompra/ListaEscenografia, ExportarEscenaTaller, los catálogos y tipos de conjuntos. Los dos `globals.css` y los layouts confirman la misma familia Geist y los tokens Pictures. Se leyeron los contratos y se renderizaron los HTML canónicos hermanos; la discrepancia entre ellos se registra al final.

## Dos miniaturas, una elección

- **Elegida: candidato 1**, `taller-esenciales@v1.r10.dir-a.html.candidate-1.html`. Catálogo a la izquierda, escena central e inspector simultáneo. Permite comprobar el efecto de una edición sin desplazar el catálogo bajo la escena.
- **Candidato 2**, `taller-esenciales@v1.r10.dir-a.html.candidate-2.html`. Catálogo bajo el visor e inspector al lado. El bloque inferior compite con la lectura de cantidades y alarga el trayecto entre añadir y editar; por eso se descartó para la dirección operacional.

Ambas miniaturas son composiciones HTML locales, dibujadas primero. El mockup completo se compuso de nuevo en el TSX asignado; no copia ni parchea una dirección anterior. Las miniaturas son bocetos de composición, no pruebas completas de estados o accesibilidad.

## Ocho ejes

| Eje | Decisión visible |
|---|---|
| Concepto | Control de conjunto: añadir, editar y comprobar lo colocado dentro del Taller existente. |
| Composición | A ≥1101 px: riel 60 px, catálogo 310 px, visor flexible, inspector 300 px. Catálogo con desplazamiento propio; inspector de altura natural para conservar accesibles los avisos y acciones. |
| Navegación | Índice compacto de los cinco grupos junto a búsqueda; selección neutral y subrayado animado. Riel existente y lista en diálogo. Exportar abre un grupo contextual en el inspector desde su control de cabecera. |
| Tipografía | Geist real incrustada. Título 18 px, tarjetas 13 px, cuerpo 14 px, medidas 28 px y cantidades 24 px tabulares. No familia nueva ni tipografía de campaña. |
| Densidad y forma | Dos tarjetas por fila; dibujos de las piezas, nombres completos y medidas. Campos agrupados por Mesa/Sillas, sin paneles ornamentales. |
| Componentes | Button, Input, Field, Card, Alert y Dialog reales instalados; tablas semánticas para cantidades. Dibujos SVG específicos de la exploración, sin activos remotos. |
| Color | Tokens Pictures de ambos temas; navegación neutral, acento para acción/selección/foco y estados semánticos. Borde funcional derivado de `--texto-tenue`, como cuentas-admin. |
| Movimiento | Cortes precisos con `cubic-bezier(.23,1,.32,1)`, asentamiento corto de cifras, reglas y selección; expresivo por defecto, sin cambiar la identidad del producto. |

El JSON compañero contiene selectores medibles para composición, navegación, tipografía y movimiento. Ningún eje se demuestra únicamente con `body`.

## Sistema visual y componentes reales

Los tokens de repositorio siguen siendo la fuente: `--fondo`, `--superficie`, `--superficie-2`, `--texto`, `--texto-suave`, `--texto-tenue`, `--borde`, `--acento`, `--acento-hover`, `--sobre-acento`, `--exito`, `--aviso`, `--error` y los `--taller-*` correspondientes. Se mapearon a `background/foreground`, `card/popover`, `secondary/muted/accent`, `primary/primary-foreground`, `border/input/ring` y estados shadcn. `--input` usa el token existente `--texto-tenue` para identificar los controles. En oscuro los botones genéricos usan `--sobre-acento` oscuro; el pequeño identificador original del Taller conserva `--taller-sobre-primario`.

Espaciado: 24 px en paneles de escritorio, 20 px en teléfono; grupos con 12/16/20/24 px. Radios de controles y paneles dentro del vocabulario existente; no nueva paleta, familia, textura de marca o identidad. Se usa la tipografía Geist instalada, incrustada como data URI; no sustitución por fuentes externas.

| Fuente / componente / variante | Import real | Aplicación |
|---|---|---|
| shadcn:button · default/outline/ghost · enabled/disabled/focus | `@/components/ui/button` | Cabecera, riel, grupos, añadir, deshacer, exportar y recuperación |
| shadcn:input · search/number · normal/invalid | `@/components/ui/input` | Búsqueda, dimensiones y cantidad solicitada |
| shadcn:field · vertical | `@/components/ui/field` | Etiqueta y control asociados |
| shadcn:card · peer object | `@/components/ui/card` | Tarjetas de creación, sin sombras |
| shadcn:alert · default con rol semántico | `@/components/ui/alert` | Capacidad, error recuperable y resultado de exportación |
| Animate UI / Dialog · modal controlado | `@/components/ui/dialog` | Lista de compra, Escape y restauración de foco |
| Motion · grupo SVG | `motion/react` | Cambio de dimensiones de la escena ilustrativa |
| Runtime y perfil | `@kit/mockup`, `@kit/motion` | mountMockup/useMockup/useMotionProfile y selectores nativos |

Personalizado: disposición de columnas, índice de grupos, dibujos de mobiliario y escena, reglas de medida, contador y tabla de lista. Estos elementos no se presentan como un componente de biblioteca que no existe. El selector de tipo de mesa es nativo y está etiquetado. No hay casillas nativas sin estilo ni interacción exclusivamente por arrastre. No se empleó fallback HTML para el mockup completo.

## Comportamiento y estados inspeccionables

**Mesas.** Ocho tarjetas paramétricas con los nombres y tamaños iniciales del catálogo: redonda, cuadrada, rectangular, ovalada, cóctel, media luna, serpentina y Banquete en U. Rectangular añade 240 × 90 × 75 cm y queda elegida. Permanecen Mesa imperial, Mesa imperial con mantel y Mesa imperial con 10 sillas como piezas fijas. El inspector usa límites y etiquetas por tipo; la rectangular muestra largo, ancho de la mesa y alto de la tapa. Editar medidas o cantidad solicitada actualiza datos de ejemplo compartidos por escena, cantidades y lista. Un valor fuera de rango conserva la última geometría válida y muestra el error asociado al campo.

**Capacidad y deshacer.** Se muestran cantidad solicitada, colocadas y capacidad. El exceso no figura como sillas colocadas. El aviso usa el texto existente «Se pidieron …, pero … solo caben …» y ofrece Deshacer; también existe el control de cabecera y Ctrl/Cmd+Z fuera de los campos. La exploración demuestra recuperación del conjunto anterior, sin fijar una nueva política de agrupación del historial de producción.

**Backing.** Un grupo con exactamente panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico. Etiquetas: Panel redondo, Media luna, Arcos chiara, Pedestales, Aro metálico, Marco hexagonal metálico y Arco metálico. Las antiguas secciones Fondos y tapetes y Decorado de pie conservan ejemplos de sus otras piezas, sin repetir esos siete objetos. Se puede añadir cada pieza y buscar por nombre o ID original. Las tarjetas paramétricas usan una clave de presentación separada para no confundir Mesa media luna con el prop media_luna. Esto no propone cambiar ningún ID guardado o repositorio. La búsqueda sin resultados ofrece Limpiar búsqueda.

**Lista.** Diálogo sobre el Taller, con tabla de piezas, cantidades colocadas y dimensiones, sin columna ni valor de alquiler. Se conserva «no es producto de la tienda». Mesa y sillas proceden del mismo conjunto de datos de ejemplo; las sillas muestran las dimensiones del catálogo, 45 × 45 × 90 cm. El diálogo se cierra con su control o Escape y devuelve foco al activador.

**Exportación.** Idle, Preparando GLB…, preparado y fallo con Reintentar exportación. Preparar bloquea el segundo envío; el error conserva escena y medidas. El formato sigue siendo GLB. Se indican metros, colores base y la posible diferencia de iluminación en Blender. «Simular resultado» es una herramienta del mockup para completar el estado pendiente; no es una acción propuesta para producción. No se genera ni se descarga un GLB real ni se invoca red o IA en esta exploración.

Los selectores nativos **Vista, Estado, Diálogo, Tema y Movimiento** conservan sus ids `view/state/scene/theme/motion` y el rótulo **Mockup**. Vistas: Mesas/inspector, Backing, Fondos y tapetes, Decorado de pie y Exportar GLB. El índice interno incluye Sillas y asientos, como la superficie original. Diálogo: Lista de compra. Estados: normal, carga del catálogo, escena vacía, sin resultados, error de catálogo, capacidad excedida, medida no válida, exportando, preparado y fallo. La escena vacía permite crear; carga/error de catálogo conservan el contexto de la escena y ofrecen ver catálogo/reintentar. Exportar queda deshabilitado sin piezas o mientras prepara.

No se inventan pantallas de permiso, offline de exportación ni persistencia parcial: la autorización del Taller pertenece a SP-2, exportar es local y el brief no añade una sincronización. La recuperación de un fallo real de exportación y la compatibilidad de AI/fotos/escenas guardadas corresponden al producto implementado.

## Interacción y movimiento

| Disparador | Comportamiento expresivo | Duración |
|---|---|---|
| Carga del shell | Cabecera se asienta desde −6 px, contenido opaco | 480 ms |
| Cambiar grupo/buscar | Tarjetas entran desde −8 px, escalonadas cada 25 ms | 300 ms por tarjeta |
| Selección de grupo | Línea neutral se extiende desde su origen | 300 ms |
| Entrada/cambio de inspector | Desplazamiento horizontal de 12 px | 300 ms |
| Editar medidas | El conjunto SVG interpola sus proporciones | 220 ms |
| Mostrar regla | Regla de dimensiones se despliega de .65 a 1 | 480 ms |
| Cambiar cantidades | Asentamiento vertical −3 → 1 → 0 px | 300 ms |
| Hover / presión | Tarjeta sube 2 px; botón baja 1 px y comprime levemente | 160 ms |
| Aviso / confirmación | Mensaje se asienta desde 6 px; texto legible | 300 ms |
| Preparar GLB / cargar catálogo | Indicador de avance / desplazamiento de placeholder | 1200 / 1400 ms, sólo en pendiente |

El perfil Natural acorta a 130/210/340 ms y Sutil a 90/140/220 ms; Motion lee `useMotionProfile`. Con `prefers-reduced-motion`, `?still=1` o Quieto se eliminan recorridos, bucles y transiciones, conservando datos, errores y acciones. La pestaña oculta pausa las animaciones CSS. No hay efecto ambiental pesado ni scroll decorativo permanente. Sólo la selección explícita en teléfono desplaza hacia el inspector; reducido usa desplazamiento inmediato. El movimiento propio de esta dirección usa transformaciones, sin desvanecer texto ni introducir colores intermedios de bajo contraste.

## Reflow y accesibilidad

- **≥1101 px:** cuatro columnas; catálogo con altura acotada y scroll propio; visor con altura del espacio de trabajo; inspector natural para que sus avisos y exportación no queden recortados.
- **768–1100 px:** riel, catálogo de 280 px y visor; inspector debajo en dos columnas.
- **320–767 px:** cabecera se envuelve; visor, riel horizontal, catálogo de dos tarjetas por fila e inspector se apilan. Paddings de 20 px y acciones de grupos de 44 px. Añadir lleva al inspector; existe «Ir al inspector» al foco.
- **Horizontal 640–1023 px con altura ≤540 px:** riel al lado, catálogo y visor en paralelo, inspector debajo. No se fuerza una hoja alta sobre el visor.

Objetivo WCAG 2.2 AA: controles reales, etiquetas asociadas, estados con palabras, tabla con encabezados, mensajes `status`/`alert`, foco visible de 2 px y borde funcional contrastado. El SVG es ilustrativo y aria-hidden: medidas, cantidades y selección están en texto/controles. Orden DOM coherente, teclado nativo, modal con fondo inerte, Escape y foco restaurado. Los botones nuevos de teléfono tienen al menos 44 px; el índice denso de escritorio tiene al menos 36 px. No se afirma conformidad completa WCAG ni acceso al motor 3D a partir de esta maqueta.

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| A-AC-01 | ≥1101 px | Normal | Riel, catálogo, escena e inspector son visibles en columnas. |
| A-AC-02 | 320–767 px | Normal | Catálogo e inspector refluyen sin scroll horizontal de página. |
| A-AC-03 | 320–1440 px | Añadir rectangular | Inspector muestra 240 × 90 × 75 cm tras tocar su tarjeta. |
| A-AC-04 | 320–1440 px | Edición | Medidas de mesa en lista coinciden con el inspector. |
| A-AC-05 | 320–1440 px | Capacidad excedida | Solicitadas y colocadas se distinguen y se ofrece Deshacer. |
| A-AC-06 | 320–1440 px | Backing | Hay siete tarjetas con los nombres originales, cada una una vez. |
| A-AC-07 | 320–1440 px | Grupos anteriores | Ninguno de esos siete IDs se repite en los grupos antiguos. |
| A-AC-08 | 320–1440 px | Sin resultados | Se muestran Sin resultados y Limpiar búsqueda. |
| A-AC-09 | 320–1440 px | Lista de compra | Tabla muestra dimensiones y cantidades colocadas sin precios de alquiler. |
| A-AC-10 | 320–1440 px | Exportando | Preparando GLB… está visible y no admite otro envío. |
| A-AC-11 | 320–1440 px | Fallo exportación | Reintentar exportación es visible y escena/medidas permanecen. |
| A-AC-12 | Ambos temas | Foco / diálogo | Escape cierra lista y devuelve foco al botón que la abrió. |
| A-AC-13 | 844 × 390 px | Normal | Catálogo y visor se disponen al lado, sin overflow de página. |
| A-AC-14 | Ambos temas | Quieto / reducido | Las mismas acciones y resultados quedan accesibles sin movimiento. |

## Evidencia y límites honestos

Builder offline ejecutado por ruta absoluta: `bitacora.py components mockup build taller-esenciales@v1.r10.dir-a.tsx --out taller-esenciales@v1.r10.dir-a.html`. **620 KB, 2133 módulos fuente**, componentes instalados reales, sin instalación ni descarga de paquetes/activos. Sólo el HTML de salida solicitado se construyó; no se escribió preview ni contenido compartido.

`contrast.py`: **158 pares en ambos temas; todos pasan**.

Auditoría final sobre el HTML final: **220 renders / 220 combinaciones previstas**, 14 430 mediciones de texto y 3010 paradas de foco, a 1280/390 px y en ambos temas, sin muestreo.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

Las revisiones intermedias detectaron padding en un inspector con scroll/altura limitada; se corrigió mediante altura natural del inspector. También se contuvo el dibujo dentro del SVG y se alinearon las etiquetas de medidas. La evidencia final sustituye esos resultados intermedios.

Comprobación adicional de interacción: **PASS, 120 aserciones**, incluidas creación y edición, lista coherente, capacidad, deshacer, validación, búsqueda de los siete IDs, eliminación de duplicados en grupos antiguos, selección de Backing, cierre/foco del modal y exportación simulada/reintento. **70 casos de reflow** a 320/390/640/768/844×390/1024/1440 px, ambos temas y cinco vistas, sin overflow horizontal. Cero excepciones de página y cero solicitudes externas.

`compare_directions.py A B C --json`: **PASS, evidence_ok=true, sin evidencia faltante**. En la medición final realizada: similitud de geometría A/B .062, A/C .046, B/C .045; navegación, densidad y movimiento distintos en cada pareja. La tipografía se informa pero no puntúa la separación de direcciones. Esto no sustituye una decisión del propietario ni certifica los contratos de B/C.

Se inspeccionaron capturas en memoria, sin escribir archivos adicionales: escritorio claro/oscuro, teléfono con Backing y con lista en oscuro, y exportación fallida en teléfono claro. La comprobación automática completa cubre ambos temas a 1280/390 px. Las miniaturas no se sometieron a la matriz completa.

**Límites:** el visor es un dibujo SVG neutro, no el motor 3D. La capacidad es una simulación local para visualizar solicitadas/colocadas; no reemplaza `repartirSillas` ni prueba la paridad de agregar_mesas/cambiar_mesas/cambiar_sillas. Las piezas distintas de la mesa principal usan ilustraciones esquemáticas. Los ejemplos de los grupos antiguos no son un inventario exhaustivo. No se verifica un archivo GLB, importación en Blender, transformaciones, tolerancias, materiales, IDs persistidos ni descubrimiento AI/fotos. Estos aspectos requieren sus tareas de producto; el mockup no hace una afirmación técnica de éxito sobre ellos. No se ejecutaron tests/build de producción ni se editó código de los repositorios.

## Preguntas y supuestos para el propietario

Q: ¿Qué referencia compartida debe regir al finalizar si el HTML canónico de proyectos sigue usando otra paleta/familias que su Markdown y cuentas-admin? Esta exploración aplica los tokens del repositorio y Geist, conforme al brief vigente; la discrepancia debe resolverse entre los artefactos compartidos antes de la finalización.

Confirmado por el brief: rectangular 240 × 90 × 75 cm, una tarjeta por tipo paramétrico, Imperial fijo disponible, siete piezas movidas a Backing sólo en Taller, cantidades/dimensiones sin alquiler y exportación GLB local recuperable. No se reabre ninguna de esas decisiones.

La aprobación del plan y la elección visual siguen pendientes. Este resultado es una exploración completa, no un contrato aprobado ni una autorización de implementación. Impacto potencial: SP-3, T3.1/T3.2/T3.3/T3.4/T3.7; catálogo/inspector/lista/exportación. Clasificación: propuesta con cambios de composición y navegación contextual que requiere adaptación/revisión si se elige; no altera un contrato aprobado, otra dirección ni SP-2/SP-4.
