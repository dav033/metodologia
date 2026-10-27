---
name: En la pieza
contract_target: taller-esenciales@v1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
revision: r10.dir-c
owner: David
approval: exploration only; no canonical contract changed
---

# En la pieza — dirección C

Esta es una exploración independiente, no un contrato aprobado. El comportamiento compartido de r10 sigue siendo la autoridad. No se editó ningún repositorio de producción, plan, artefacto complementario, contrato compartido ni archivo de historial.

## Enfoque y miniatura seleccionada

Se selecciona la opción 1: la mesa permanece sobre su bandeja de edición horizontal; sus controles de dimensiones visibles llevan el foco del teclado a los campos numéricos asociados. La opción 2 mantiene un inspector vertical flotante a la derecha de la misma escena, pero ocupa el espacio horizontal que necesitan las mesas largas. La opción 1 relaciona directamente los controles modificados con la pieza y reordena los mismos campos debajo de ella en un teléfono. Ambas composiciones HTML pequeñas se escribieron antes que el TSX completo.

Reproducir la cabecera establecida de Pictures/Sempertex con anillo y punto, el acceso a idioma/cuenta, la cabecera de escena de Taller, el regreso a Mis proyectos, la barra lateral de paneles, Fondos y muebles y la escena central. El inspector horizontal de la pieza seleccionada modifica solo la superficie de inspector permitida por SP-3. Conserva el vocabulario existente de tipo, dimensiones, altura, mantel y sillas, y muestra progresivamente los ajustes secundarios. La estructura es compartida; la exploración se centra en la ubicación y la interacción de estos controles modificados.

Fuentes de solo lectura: t12 `src/app/3d/page.tsx`, `Taller3D.tsx`, `FondosYMuebles.tsx`, `EditorConjuntoMesa.tsx`, `ListaEscenografia.tsx`, `CabeceraApp.tsx`, datos de mesas/sillas/catálogo y `globals.css`; asesor `globals.css`, estructura compartida y `ExportarEscenaTaller.tsx` (el componente de exportación con nombre no existe en t12). Se inspeccionaron los pares Markdown/HTML canónicos de ambos proyectos complementarios; sus correspondencias escritas de tokens de producción tienen precedencia sobre los estilos exploratorios anteriores que permanecen en el paquete de proyectos. Se leyeron “Behavior — SP-3 and SP-4 (round 9 answered)” de SPEC y la referencia de interfaz de usuario en el PLAN de SP-3. Esto no añade ninguna página, marca, paleta ni familia tipográfica nueva.

## Ocho ejes

| Eje | Decisión específica de la dirección |
|---|---|
| concepto | En la pieza: seleccionar la mesa, ajustar sus dimensiones y editar el conjunto seleccionado sin salir de la escena de Taller. |
| diseño | Cabecera y barra de herramientas existentes de Taller sobre la barra lateral de paneles de 60px, el catálogo de objetos de 292px y la escena flexible; el inspector modificado es una bandeja horizontal directamente debajo del objeto seleccionado, en lugar de una segunda barra lateral. |
| navegación | Barra lateral de paneles y grupos de Fondos y muebles existentes; los botones de dimensiones enfocan los campos correspondientes, Pieza muestra el inspector y los elementos details nativos muestran los ajustes existentes de tipo/mantel/sillas. La lista de compras y la exportación conservan la escena circundante. |
| tipografía | Geist de producción integrada; título de hasta 24px, título del inspector de 20px, jerarquía de objetos de 16px, texto de trabajo de 14px y valores de dimensiones tabulares. Sin fuente de exhibición ni familia nueva. |
| densidad | Tarjetas de objetos en dos columnas y edición directa en cuatro columnas en escritorio; campos en dos columnas y control de incremento de sillas a todo el ancho en teléfono. Una franja plana del objeto seleccionado conecta el lienzo y el inspector; relleno del área de trabajo de 24px/20px. |
| componentes | Button, Input y Skeleton de shadcn/Base UI instalados, organizados como tarjetas de objetos, controles de dimensiones numéricas y un control de incremento de sillas. Los elementos select/details nativos conservan la interacción por teclado; un SVG esquemático personalizado da contexto a la escena. |
| color | Tokens fijos de Pictures y tokens específicos de Taller en ambos temas. La acción principal y la selección usan el acento existente; las advertencias y los errores usan aviso/error existentes. Los bordes de controles usan el alias texto-tenue de los proyectos complementarios; no se añade una paleta nueva. |
| movimiento | Gramática táctil de pulsación y asentamiento: colocación de tarjetas con resorte según el perfil, asientos de mesa comprimidos, colocación escalonada de sillas, bandeja del inspector que aparece desde abajo, corrección lateral de advertencias, asentamiento de recibo, barrido de preparación de exportación y sello de confirmación. Rebote CSS (.34,1.4,.64,1), expresivo 480/180ms; natural 300/140ms, sutil 160/100ms. El modo reducido/sin animación elimina el desplazamiento y las animaciones repetidas. |

## Vistas, estados e interacciones

Los controles nativos `view`, `state`, `scene`, `theme` y `motion` permanecen visibles sobre el producto, junto con la etiqueta Mockup del runtime. Escenas contiene solo «Ninguno»: esta propuesta usa divulgación en línea, no un diálogo modal.

- **Mesa seleccionada:** escena esquemática → objetivos seleccionables de cm/sillas → franja de pieza seleccionada → inspector con largo, profundidad, altura y sillas solicitadas. Los botones de dimensiones abren el inspector y enfocan el campo correspondiente. Cerrar lo contrae; Pieza lo restaura. Los campos numéricos y los botones +/- ofrecen alternativas de teclado; no se requiere arrastrar.
- **Tarjetas de mesas:** una tarjeta de creación por cada uno de los ocho tipos paramétricos existentes. Una tarjeta selecciona las dimensiones predeterminadas de origen de su tipo y abre el mismo inspector. Rectangular comienza en 240 × 90 × 75 cm; el accesorio heredado de ocho sillas es ilustrativo. La Mesa imperial fija existente sigue estando disponible por separado.
- **Backing:** exactamente una tarjeta por ID original: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico. Los nombres visibles son los del catálogo, incluido Marco hexagonal metálico. La búsqueda acepta tanto el ID original como el nombre. Al agregar un elemento decorativo, se actualizan la escena esquemática y la lista de compra. Las adiciones repetidas son instancias colocadas por separado, no tarjetas duplicadas del catálogo.
- **Grupos anteriores:** Fondos y tapetes y Decorado de pie siguen disponibles, con objetos representativos restantes y sin ninguna de las siete tarjetas movidas. El prototipo no reproduce el catálogo completo. Backing es exclusivo de Taller; no se modifican las categorías ni la propiedad/los IDs de Shopify.
- **Lista de compra:** conserva el contexto de la escena y muestra las cantidades y dimensiones reales del accesorio, con «Mobiliario · no es producto de la tienda». Mesa rectangular y Silla Tiffany usan un modelo de edición compartido; no aparecen precios, columnas de alquiler ni totales inventados. Los 45 × 45 × 90 cm de Tiffany provienen de la fuente existente de sillas. Las adiciones de Backing aparecen con sus nombres originales.
- **Exportar GLB:** acción inactiva, preparación deshabilitada, estado de finalización, error visible y Reintentar. La generación del archivo es explícitamente simulada: no se realiza ninguna solicitud de red, generación de GLB, llamada a IA ni importación a Blender. La funcionalidad PNG existente queda fuera de la superficie GLB modificada y no se redefine.

Estados nativos declarados: Normal; Cargando (esqueletos del catálogo/escena, edición deshabilitada); Vacío (ningún objeto de escena seleccionado; se puede crear); Búsqueda sin resultados (recuperación mediante limpiar la búsqueda); Error (reintento del catálogo, además de recuperación de GLB si se selecciona la exportación); Capacidad excedida (24 solicitadas frente a las colocadas/la capacidad, con advertencia explicativa); Deshecho (accesorio predeterminado restaurado); Exportando; Exportación lista; Exportación fallida. Los estados de exportación pertenecen a la vista de exportación. Todos se pueden seleccionar directamente. Las ediciones de mesas y elementos decorativos del accesorio persisten al navegar entre vistas, incluida la lista de compra y la exportación simulada. Cambiar el estado de inspección reemplaza intencionalmente el accesorio; es un control de planificación, no una acción del producto. SP-3 no introduce estados de permisos, guardado en red ni carga de IA.

El prototipo ilustra un conjunto con una mesa seleccionada. Su capacidad es un accesorio simplificado intencionalmente, no una implementación de `repartirSillas`; producción debe conservar la capacidad basada en la geometría existente, los tipos de sillas, las distribuciones, el catálogo completo, los límites de validación y el historial de escenas. Las tarjetas de otros tipos de mesa muestran los valores predeterminados de origen y permiten seleccionarlos; aquí se especifica la edición detallada de mesas rectangulares. El catálogo y el SVG son ilustrativos; la creación de mesas no demuestra un motor 3D completo con varias mesas. Los IDs guardados, la detección mediante IA/fotos, la independencia de las llamadas de pago y la fidelidad de Blender requieren las tareas de ingeniería; una maqueta HTML no puede verificarlos.

## Correspondencia con el sistema de diseño y componentes

Los colores corresponden exactamente a las asignaciones de producción del proyecto hermano: fondo/primer plano = fondo/texto; tarjeta/popover = superficie/texto; primario = acento/sobre-acento; hover = acento-hover; secundario/atenuado/acento = superficie-2; texto de apoyo = texto-suave; líneas decorativas = borde; borde significativo de entrada/control = texto-tenue; anillo = acento; éxito, advertencia y error = exito, aviso y error, más sus rellenos suaves existentes. Las superficies de la escena conservan taller-barra/panel/visor/tarjeta/elegido. El pie de escena oscuro usa el valor taller-medio existente para que el texto de apoyo sea legible. El color primario oscuro original, limitado a la barra de herramientas del producto, no se usa como texto sobre un botón primario compartido del proyecto hermano: los botones compartidos usan sobre-acento.

Geist se integra como URI de datos a partir del recurso de compilación WOFF2 Latin estático de Next existente en t12 (`caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2`). No se descargaron fuentes, paquetes ni recursos. Se reutilizan las acciones tipo píldora compartidas existentes, los controles redondeados de 14px, las tarjetas de objetos con bordes redondeados amplios, la navegación neutra, el foco visible de tres píxeles y los controles de 44px como mínimo. El relleno del área de trabajo es de 24px en escritorio / 20px en teléfono, sobre un eje izquierdo compartido; no hay una columna de pie de página flotante.

| Origen:id · variantes/estados | Importación instalada o composición personalizada |
|---|---|
| shadcn:button · outline/default/ghost · normal/hover/press/focus/disabled | `@/components/ui/button`, Base UI; el contenedor Action asigna los tokens del producto |
| shadcn:input · search/number · normal/focus/disabled | `@/components/ui/input`, Base UI; etiquetas asociadas, unidades explícitas |
| shadcn:skeleton · catalogue/scene · loading | `@/components/ui/skeleton` |
| native:select · language/table/mantel/chair/layout | Controles nativos con etiquetas y bordes asignados a tokens |
| native:details · account/secondary inspector · closed/open | Divulgación mediante Summary con teclado; el contenido cerrado se retira del diseño |
| custom:scene-target · selected/empty | SVG en línea, formas esquemáticas con tokens de origen; no es un renderizador 3D |
| custom:receipt/feedback · normal/warning/error/success | Encabezados semánticos, filas de cantidades y regiones de estado/alerta |
| motion/react + @kit/motion | Motion instalado; useMotionProfile proporciona el estado de resorte/reducción |
| @kit/mockup | mountMockup/useMockup; se conservan los selectores nativos de planificación |

No se usó una alternativa HTML. Las dos composiciones en miniatura son bocetos, no sustitutos de la maqueta completa con componentes reales.

## Detalle de movimiento y adaptación

La mesa seleccionada se comprime y se asienta (rebote de 480ms), las sillas se acomodan individualmente con intervalos de 25ms, las tarjetas del catálogo aparecen con el resorte del perfil, el panel del inspector sube 18px hasta su lugar, las advertencias se corrigen lateralmente 8px, el recibo se asienta 10px, la preparación de la exportación se desplaza y su confirmación se fija en su lugar. Los botones se elevan 2px al pasar el cursor y se comprimen a .96 al presionarlos, con transiciones de 180ms. Los perfiles Natural/sutil reducen estas duraciones; el texto no desaparece mediante desvanecimiento ni pasa por un estado de bajo contraste. Todos los selectores de evidencia de movimiento en JSON apuntan a elementos que realmente se animan o transicionan.

La reducción de movimiento del sistema operativo, `?still=1` y el perfil nativo Quieto eliminan los desplazamientos, las animaciones repetitivas de trabajo y el recorrido al pasar el cursor o presionar, con respuesta final inmediata y todos los controles intactos. Las pestañas ocultas pausan la animación CSS. No hay decoración ambiental infinita ni efectos fuera de pantalla que deban suspenderse. El movimiento de la escena es una respuesta esquemática, no una promesa de que la exportación modificará el editor.

Puntos de quiebre: por encima de 1100px, la barra de 60px y el catálogo de 292px acompañan la escena, con cuatro columnas de campos directos; entre 761 y 1100px se usa un catálogo de 252px y dos columnas de campos directos; entre 360 y 760px se usa el mismo encabezado, una sola fila de panel Añadir/Pieza/Backing, luego la escena/el inspector y, debajo, el catálogo. La barra de escritorio se oculta en teléfonos para evitar controles de panel duplicados. Los controles de sillas ocupan ambas columnas en teléfonos. Las cantidades y dimensiones de compra se apilan en tabletas y teléfonos. Ningún panel lateral cubre la mesa seleccionada. El desplazamiento estándar del documento permite acceder a todos los controles. El selector de idioma pertenece al contexto del shell; el contenido de esta exploración SP-3 permanece en español, como lo solicita el brief de comportamiento; la traducción al inglés corresponde a la tarea posterior de textos.

## Criterios observables de aceptación visual

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-01 | 1101px+ | normal | El encabezado existente y la barra de herramientas de Taller preceden a la barra, el catálogo y la escena central; no aparece ninguna página nueva de la aplicación ni ninguna marca nueva. |
| C-02 | 761px+ | seleccionada | Los campos del inspector forman un único panel horizontal inmediatamente debajo de la franja del objeto seleccionado; al hacer clic en una dimensión, se enfoca el campo correspondiente. |
| C-03 | 360px+ | creación | Existen ocho tarjetas de tipos paramétricos, el tipo rectangular crea una mesa de 240 × 90 × 75 cm y la Imperial fija sigue disponible. |
| C-04 | 360px+ | editada | Los valores 300 × 100 cm / 12 sillas solicitadas aparecen de forma coherente en las etiquetas de la escena y las cantidades de compra después de abrir la lista. |
| C-05 | 360px+ | capacidad | Las cantidades solicitadas y colocadas se distinguen explícitamente; una advertencia explica cuáles sillas no cupieron. |
| C-06 | 360px+ | deshacer | Deshacer restaura la edición anterior y los valores compartidos de la escena/lista. |
| C-07 | 360px+ | Backing | Aparecen una sola vez las siete tarjetas con sus IDs originales y nombres originales; ninguna aparece en los grupos anteriores. |
| C-08 | 360px+ | sin resultados | La búsqueda muestra Sin resultados y Limpiar búsqueda restaura las tarjetas. |
| C-09 | 360px+ | lista | Las cantidades y dimensiones del mobiliario aparecen sin precios de alquiler. |
| C-10 | 360px+ | GLB pendiente/fallida/exitosa | La preparación deshabilita la acción; si falla, se muestra reintentar; si se completa, se identifica explícitamente como una simulación de maqueta. |
| C-11 | 360–760px | normal | La navegación de panel móvil único precede a la escena; los campos se reorganizan sin desbordamiento de página. |
| C-12 | 360px+ | ambos temas | Los bordes de los controles, el foco del teclado y el texto siguen siendo medibles respecto de las superficies asignadas reales. |
| C-13 | 360px+ | reducido/sin movimiento | Los controles y el contenido permanecen visibles sin desplazamientos ni animación repetida de preparación. |

## Evidencia y observaciones

Constructor: espacio de trabajo real instalado y sin conexión, con 96/96 entradas de componentes disponibles; los paquetes de salida contienen 2031 archivos de origen y ocupan aproximadamente 530 KB. Verificador de contraste: `contrast: 158 pairs checked in light and dark, all pass`. La primera auditoría completa identificó siete problemas de relleno causados porque los elementos descendientes de `details` nativos cerrados conservaban sus cajas de diseño; retirarlos explícitamente del diseño corrigió esos problemas. La revisión final también compacta el lienzo y la navegación móvil y conserva las ediciones de las mesas al cambiar de vista.

Auditoría final sobre el HTML final: **RESULTADO: APROBADO — no hay problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**. Se midieron 240/240 combinaciones planificadas de vista/estado/tema/ancho, 12,524 mediciones de texto y 4,182 paradas de foco del teclado. `compare_directions.py A.html B.html C.html --json` terminó con código 0: ok=true, evidence_ok=true, ningún selector faltante; la similitud de diseño entre A/C fue 0.042 y entre B/C, 0.048, con diferencias en navegación, densidad y movimiento. Las tres comparaciones por pares aprobaron. La comparación inicial identificó dos selectores exclusivos de estado a los que su recorrido limitado a vistas no podía acceder; la evidencia JSON ahora apunta a animaciones/transiciones reales en las vistas medidas. No se hizo ningún cambio visual o de comportamiento para obtener la aprobación de esa verificación de selectores. Inspección de capturas: 1280px claro/oscuro y 390px claro/oscuro, además de pruebas renderizadas en 820px; las capturas permanecieron en memoria y no se escribieron archivos sin asignación. La prueba rápida del navegador aprobó la creación de una mesa, la edición a 300 × 100 cm / 12 sillas, la persistencia de la lista, deshacer, la adición de siete tarjetas de Backing y el éxito y fallo/reintento de la exportación simulada, sin errores de página. Las pruebas renderizadas en 1280/820/390 con ambos temas no encontraron problemas de contraste, contenido no textual, alineación, relleno ni desbordamiento.

Estas comprobaciones no acreditan conformidad con WCAG, preservación real de la geometría/el color de GLB, independencia de las llamadas de pago, detección mediante IA ni comportamiento de teclado/lector de pantalla en producción. Los componentes de producción, las comprobaciones de exportación/Blender y la traducción corresponden a las tareas de implementación asignadas. La navegación compartida del shell fuera de SP-3 solo anuncia su destino existente en la maqueta; no implementa otros subplanes.

## Impacto y decisiones pendientes

El objetivo sigue siendo taller-esenciales@v1, **borrador**. SP-3 se vincula con la versión 1, la tarea de textos de diseño T3.1 y la revisión visual T3.7; los consumidores de interfaz afectados son T3.2 (inspector/tarjetas/lista de mesas), T3.3 (Backing) y T3.4 (superficie de exportación). Esta exploración propone una disposición visual incompatible con la actual del inspector y la jerarquía del teléfono; los requisitos de comportamiento y la compatibilidad de formato/identidad no cambian. Solo una persona finalizadora seleccionada por el propietario puede escribir el contrato canónico; esta delegación no permite un registro de cambios separado.

P: Propietario — ¿Confirma que el inspector vaya debajo de la escena seleccionada, con objetivos de dimensión que reciben el foco al hacer clic, en lugar de conservar el inspector lateral actual?
P: Propietario — ¿Los campos numéricos de dimensión modificados deben mostrar centímetros como aquí o conservar la presentación en metros del inspector actual? Las dimensiones almacenadas y los metros de GLB no cambian.

Supuestos: el ejemplo de creación del origen con ocho sillas se conserva únicamente como accesorio simulado; los valores predeterminados paramétricos completos siguen bajo el control del origen. El comportamiento existente de cuenta/idioma/proyecto del shell corresponde a los contratos del proyecto hermano. No se infiere aprobación a partir de una auditoría aprobada.

SHA-256 del HTML final: `e32ffa0f15c775ed670cdddaafe0a12e2dbeedd924eef89c05755805f03c6e65`.
