---
name: Operación en paralelo
status: draft
artifact: exploration
contract_target: herramientas-chat@v1
subplan: SP-7
requirements: [R13, R16]
revision: r1
direction: a
owner: David
---

# Operación en paralelo — dirección A

Solo exploración de planificación. Este no es el contrato canónico, una aprobación ni una instrucción de implementación. El responsable todavía debe elegir una dirección y aprobar el plan. Solo se crearon los archivos asignados para esta revisión; no se modificaron el repositorio, el contrato canónico, el plan compartido ni la memoria del proyecto.

## Enfoque y superficie existente

La conversación guiada existente pasa a ser una de las herramientas, mientras que la nueva página principal de herramientas reemplaza el chat clásico en `/`. El encabezado con anillos y puntos de Pictures/Sempertex, los controles de idioma/cuenta, la navegación horizontal neutra, los radios de los paneles y las fuentes Geist locales, sin cambios, provienen de los módulos hermanos de cuentas, planes y proyectos seleccionados/finalizados. El contenido modificado se convierte en una hoja de trabajo compacta: entrada del contador a la izquierda y resultado del motor a la derecha; la calculadora ubica la edición de líneas en la columna izquierda, más ancha, y los totales en la columna derecha, más estrecha; la galería combina un registro de miniaturas con una vista previa adyacente. Es un cambio dentro de la aplicación existente, no una identidad nueva ni una página de inicio.

Evidencia del producto de solo lectura: t12 `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/components/guiado/VistaGuiada.tsx`, `src/components/cotizacion/{CotizacionProfesional,CampoGanancia,PreciosMateriales}.tsx`, `src/components/tres-d/{IdeasDelAsistente,Biblioteca}.tsx` y la cotización profesional existente en Python. El resumen compartido de UI define el alcance; SPEC y PLAN son contexto. Se inspeccionó el estado de ambos repositorios: asesor contiene modificaciones existentes no relacionadas, que se dejaron intactas. El Markdown y el HTML compilado de `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`, seleccionados/finalizados, sirvieron de referencia para el marco compartido; la fuente seleccionada de proyectos aportó su asignación exacta de tokens e importaciones de fuentes.

## Dos composiciones de miniaturas y elección

- Candidato 1: `.html.candidate-1.html`, documento de entrada y resultado en paralelo. Elegido. A 1280px se ven simultáneamente el formulario, las filas de cantidades y las primeras líneas de la lista de compras; la acción queda junto al resultado que transfiere.
- Candidato 2: `.html.candidate-2.html`, bandas horizontales de entrada con un resultado de ancho completo debajo. Se conserva como evidencia. Ofrece más espacio horizontal para las entradas, pero desplaza la lista de compras por debajo de la primera ventana gráfica de escritorio.

Se escribieron y renderizaron ambos archivos HTML candidatos antes de construir la entrada completa. Son miniaturas de composición; tanto ambas miniaturas como la maqueta completa incorporan los archivos WOFF2 reales Geist Sans/Mono del proyecto. El renderizado inicial de las miniaturas usó una fuente del sistema como sustituto; se corrigió y se usaron los recursos locales del proyecto antes de la entrega. Ninguna miniatura incorpora una paleta. El resultado completo compilado usa las bibliotecas reales instaladas, sin alternativas, instalaciones ni descargas de recursos.

## Ocho ejes

| Eje | Expresión renderizada |
|---|---|
| concepto | Operativo: mantener visibles las entradas y la salida del motor al mismo tiempo dentro de la hoja de trabajo existente de Pictures. |
| diseño | Un panel dividido: distribución de entrada/resultado de 0.85:1.35; la cotización invierte la disposición, con un editor de líneas ancho y una columna estrecha de totales; la galería es un registro de miniaturas con vista previa adyacente. |
| navegación | Enlaces de rutas horizontales y neutros heredados; botones de método para alternar entre formulario/frase/foto en el mismo lugar; las filas de la galería seleccionan una vista previa integrada en lugar de abrir otra página. |
| tipografía | Geist Sans heredada, H1 de 24px, secciones de 18px, controles y filas de 13–15px; conteo y totales de cotización tabulares de 28px. Geist Mono conserva el tratamiento heredado de Sempertex. |
| densidad | Filas compactas con separadores y campos agrupados en 2 columnas, márgenes internos de panel de 24px; sin métricas decorativas de panel de control. En el teléfono, los mismos grupos de trabajo se apilan con márgenes de 20px. |
| componentes | Button, Input, Textarea y Skeleton reales de shadcn/Base UI, y AlertDialog de Animate UI, recombinados en un panel; selectores nativos y el panel desplegable de cuenta heredado. |
| color | Exactamente los tokens claros/oscuros de Pictures y el alias heredado y accesible del borde de controles. El acento se usa solo para acciones principales y foco; selección de rutas y paneles neutros. |
| movimiento | Transiciones precisas: el panel entra 5px en vertical, las filas entran 8px en horizontal con un escalonamiento de 35ms, los resultados llegan desde el borde opuesto y la vista previa aparece con una escala de .985. 280ms cubic-bezier(.23,1,.32,1); acciones repetidas, 150ms; reducción natural/sutil de escala; el movimiento reducido elimina los desplazamientos y las transiciones. |

## Sistema fijo y procedencia de los componentes

Valores de origen claros/oscuros, respectivamente: `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--sobre-acento` #ffffff/#120b24. Todos los demás roles de éxito/advertencia/error y Taller se copian de la misma fuente del módulo hermano/proyecto. `background/card/popover` se asignan a las superficies de Pictures; `foreground` se asigna a texto; `primary/primary-foreground`, a acento/sobre-acento. `input` se asigna a texto-tenue y conserva el borde accesible de controles del módulo hermano. Los separadores decorativos conservan borde/borde-suave. Sin colores ni familias tipográficas nuevos.

| Componente / estado | Importación real / fuente |
|---|---|
| shadcn:button predeterminado y outline; predeterminado/hover/foco/presionado/deshabilitado/cargando | `@/components/ui/button` |
| shadcn:input predeterminado; edición/inválido/deshabilitado | `@/components/ui/input` |
| shadcn:textarea predeterminado; entrada de frase/chat | `@/components/ui/textarea` |
| shadcn:skeleton cargando | `@/components/ui/skeleton` |
| shadcn:alert-dialog confirmación de trabajo sin guardar; cerrado/abierto, contención/devolución del foco | `@/components/ui/alert-dialog` implementación instalada de Animate UI/Base UI |
| custom:count-table, ruled-material-editor, thumbnail-register, notice | HTML semántico, con estilos aplicados solo mediante roles del proyecto; no se presentan como componentes instalados |
| custom:account-disclosure y selectores nativos | Patrón heredado del módulo hermano; Escape/clic fuera para cerrar; el selector de roles del mockup está etiquetado como parte de la simulación |
| kit:mockup selectors / motion profile | `@kit/mockup`, `@kit/motion`; `view`, `state`, `scene`, `theme` nativos, más motion |

Los radios de paneles/campos/píldoras se mantienen en 32/18/999px; los grupos internos, en 24px. Geist Sans: cuerpo de 15px, etiquetas de 13px, tablas de 14px, encabezados de sección de 17–18px, H1 de 24px. El conteo tabular de 28px es el dato dominante, no un encabezado promocional.

## Pantallas y flujos de interacción

1. **Inicio `/`**: la cuenta con sesión iniciada ve solo las herramientas permitidas. Cada una es una tarjeta horizontal equivalente, con el nombre existente, una descripción breve de la herramienta y Abrir. No hay tarjetas bloqueadas, ofertas de mejora ni restricciones por nombre de plan. La selección de cuenta de prueba está etiquetada explícitamente como Mockup y no cambia el rol del producto. Entusiasta/Designer muestran Chat y Contador; Designer Plus agrega Calculadora; Master/personal interno también muestran Catálogo y Taller en este borrador, a la espera de Q1. No hay un estado vacío en el inicio: todas las cuentas tienen herramientas. La entrada a Catálogo muestra un aviso de alcance claro, ya que SP-7 no rediseña ese destino existente.
2. **Contador `/contador` (ruta propuesta)**: elegir Formulario/Frase/Foto en el mismo lugar. El formulario agrupa estructura, ancho/alto en metros, tamaños y colores. Frase solicita las medidas que falten. Foto usa el texto existente para JPG/PNG/WebP de menos de 6 MB. La acción de conteo pasa al estado de carga y luego a un resultado claramente simulado: 120 globos, dos filas de 60 por tamaño/color y una lista de compras sin precios. Todos los valores numéricos son datos de respuesta ilustrativos del motor, no estimaciones calculadas por esta UI. Los resultados de foto también identifican una estimación y reservan el campo de tolerancia para los datos que entregue el motor; no se inventa un valor numérico de tolerancia. Calcular costo aparece solo con permiso de costos y transfiere el resultado a Calculadora. El contador no muestra importes, moneda, totales ni cotizaciones, con ningún nivel de permisos.
3. **Calculadora `/calculadora`**: empieza vacía para la entrada manual; el estado importado identifica los materiales del contador. La cotización de muestra usa dos paquetes de 50 unidades por color, con una etiqueta visible que lo indica y explica por qué las unidades de compra superan el conteo. Editar precios de paquetes, cantidades, mano de obra, transporte/equipamiento, costos indirectos y ganancia; agregar o quitar filas de materiales; restaurar los precios del catálogo de prueba. La consulta al catálogo real sigue siendo la fuente del producto, y el fixture indica explícitamente que sus precios son ejemplos. El cálculo del producto sigue siendo responsabilidad de Python. La simulación conserva la semántica existente de CampoGanancia: el porcentaje de ganancia se suma al costo total; no se redefine como margen bruto. Los cambios ocultan los totales válidos hasta que se vuelva a calcular; los errores conservan las entradas. Los resultados calculados incluyen subtotales por material, desglose de costos, ganancia y precio para el cliente. En producción, una entrada libre no se convierte en un producto de catálogo autoritativo; el editor del fixture representa el mecanismo existente para ingresar materiales.
4. **Galería `/3d/decoraciones`**: la entrada a Taller abre un registro con búsqueda de Ideas del asistente e Ideas Sempertex, y filtros por ocasión/tamaño. La vista previa selecciona una fila en el mismo lugar; no hay vista previa modal ni un nuevo modelo de biblioteca/editor. El dibujo adyacente es un esquema de escena en CSS/SVG etiquetado como ejemplo, no una foto de referencia real ni un resultado 3D final. Al abrir, se simula `/3d?decoracion=<id>` como una escena nueva sin guardar, conservando la decoración seleccionada entre vistas. Sin resultados, se borran los filtros. Un id desconocido deja intacta la escena abierta. Si se deniega el permiso, no se exponen datos de decoraciones.
5. **Trabajo sin guardar**: reutiliza la protección contra trabajo pendiente de proyectos@v1. El AlertDialog instalado ofrece Cancelar, Guardar y continuar y Descartar escena y continuar. El borrador simula solo los casos exitosos; en producción se puede continuar después de confirmar el guardado, se debe conservar el estado si el guardado falla, está pendiente o entra en conflicto, y nunca se debe reemplazar la identidad del proyecto de cuenta existente. El comportamiento de primer nombre/guardado/reintento se mantiene en SP-4. No se ilustra un guardado fallido como si hubiera tenido éxito.
6. **Chat existente `/asistente` y Taller `/3d`**: las vistas de contexto muestran solo enlaces de entrada/salida. No se rediseñan el flujo de conversación guiada ni el editor/biblioteca existentes. Chat no muestra información de precios; las acciones de costos/Taller dependen de permisos. Taller abre una escena sin guardar y su entrada Decoraciones. Los controles existentes fuera del alcance muestran avisos explícitos de destinos de Mockup en lugar de simular efectos reales. No se usa red, se llama a proveedores ni se guarda información.

## Estados y controles del fixture

Los inspectores nativos exponen todos los estados declarados. Los nombres de estados globales tienen significados propios en cada vista; las combinaciones irrelevantes vuelven al estado inicial de esa vista en lugar de inventar estados imposibles del producto. `denied` se puede probar en todas las vistas; las cuentas de fixture con permisos denegados también se aplican a las rutas de calculadora/Taller/galería. Al inicio no se inventan estados de carga/error/vacío.

| Vista | IDs de estado y comportamiento visible |
|---|---|
| Counter | `ready`/`empty`: instrucciones; `question`: medida faltante y Add measurements; `loading`: texto de conteo + skeleton, acción de conteo deshabilitada; `result`: 120 y filas/lista; `photo-estimate`: campo de estimación/tolerancia; `photo-large`/`photo-type`: recuperación específica del archivo; `error`: error del motor y reintento |
| Calculator | `empty`: entrada manual de materiales o volver al contador; `imported`: aviso de procedencia; `editing`: explicación de resultados desactualizados, sin totales válidos; `loading`: skeleton de cálculo y acción de cálculo deshabilitada; `totals`: filas/subtotales/totales; `error`: error de cotización y entradas conservadas |
| Gallery | `loading`: skeleton; `ready`: resultados; `no-results`: borrar filtros; `unknown`: no se encontró y la escena sigue intacta; `unsaved`: explicación del trabajo pendiente y protección al abrir; `error`: reintento sin cambiar la escena |
| Access | `denied`: sin datos ni nombres de planes; volver a las herramientas. También se alcanza mediante el fixture de permisos de cuenta en rutas restringidas. |
| Dialog | `scene=unsaved`: AlertDialog de trabajo pendiente desde una acción visible de apertura o el inspector; Escape/Cancel cierra; el foco vuelve al elemento que lo invocó, con el título de la página como alternativa después de navegar. |

El modo sin conexión no es un requisito independiente del producto: las vistas de error del motor/cotización/galería cubren respuestas no disponibles sin inventar un éxito en caché. Un fixture que solo se ejecuta en el navegador no puede verificar la autorización del servidor, el etiquetado del gasto de IA, las cantidades exactas del motor, los precios del catálogo, la durabilidad del guardado ni el análisis real de archivos. Estos aspectos están fuera de esta exploración de diseño.

## Comportamiento responsivo y accesibilidad

- 1100px y más: márgenes exteriores de 40px, encabezado/navegación heredados, contador y cotización divididos; vista previa de galería adyacente.
- 840–1099px: márgenes de 24px, misma división entre contador y galería; columna del total de la cotización de 300px; la navegación larga se ajusta en varias líneas sin carrusel.
- 640–839px: márgenes de 24px, todos los paneles de entrada/resultado y galería/vista previa se apilan; las filas de la galería usan dos columnas antes de la vista previa.
- Menos de 640px: márgenes de 20px, los controles del encabezado se ajustan en varias líneas, el título/acción de la página se ajustan, la navegación neutra se ajusta en varias líneas, galería de una columna; las filas de materiales se convierten en campos con nombre en lugar de una tabla que desborda; los gastos de la cotización se apilan; las acciones del diálogo ocupan todo el ancho disponible. Las dimensiones del contador mantienen dos columnas legibles. No se agrega una barra lateral fija de escritorio.

Objetivo WCAG 2.2 AA, sujeto a verificación de implementación. Los campos nativos tienen etiquetas explícitas; los selectores siguen siendo nativos y accesibles con teclado. Los botones tienen al menos 44px de alto; el foco usa un contorno de acento de 3px con un desplazamiento de 4px. Los conteos usan una tabla semántica con números alineados a la derecha. Los errores usan role=alert; la espera y los comentarios, role=status; la carga, aria-busy. El menú de cuenta se cierra con Escape o al hacer clic fuera. AlertDialog proporciona inercia modal y contención del foco; al cancelar, el foco vuelve a su origen. Los cambios de vista enfocan H1. Las variantes de texto en español e inglés conservan el estado; las unidades siguen siendo cm/m y las cotizaciones, COP. SP-8/SP-10 se encargan de la persistencia del idioma y de la traducción completa del contenido.

## Detalles de interacción y movimiento

El movimiento específico de cada dirección es rápido y preciso, sin desvanecer información útil: `.paper` baja 5px, `.count-line` aparece horizontalmente con un desplazamiento de 8px y un escalonamiento de 35ms, `.result-panel` entra desde el borde opuesto, `.preview-stage` aparece con una escala de .985, los cambios de método se desplazan 3px y las flechas de los botones avanzan 3px al pasar el cursor. Todo el movimiento usa transform; el contenido del papel se puede leer de inmediato. El perfil expresivo es de 280ms / controles repetidos de 150ms, con cubic-bezier(.23,1,.32,1); el natural, de 200/140ms; y el sutil, de 130/110ms. `useMotionProfile()` proporciona el perfil activo y el estado reducido. Las pestañas ocultas pausan las animaciones CSS; no hay ciclos decorativos infinitos. La preferencia reducida del sistema operativo, Quieto y `?still=1` eliminan las animaciones/transiciones/desplazamientos y conservan los controles, datos y textos de estado. AlertDialog conserva el comportamiento de su primitiva, que tiene en cuenta el movimiento reducido.

## Criterios de aceptación visual observables para esta exploración

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1280, 1024, 390px | Todos | Se conservan la marca Pictures/Sempertex, Geist, los tokens exactos del tema de origen y la navegación neutra entre rutas. |
| A-02 | 1280px | Resultado del contador | La entrada, el total de 120, las dos filas del conteo y la lista de compras aparecen en un solo panel de papel dividido, sin precio. |
| A-03 | 390px | Resultado del contador | El resultado sigue a las entradas en el orden del DOM y visual; la página no tiene desplazamiento horizontal. |
| A-04 | Todos | Entusiasta | No aparece ningún enlace a Calculadora/Taller ni la acción Calcular costo; la vista restringida directa no muestra datos ni el nombre de un plan superior. |
| A-05 | Todos | Errores de pregunta/foto | La explicación y el control correspondiente para recuperar la medición/foto aparecen en el área de resultados. |
| A-06 | Todos | Edición de la calculadora | El total anterior no se presenta como actual; se solicita explícitamente volver a calcular. |
| A-07 | Todos | Totales de la calculadora | Los precios de paquetes editables, los subtotales por fila y el desglose de la cotización comparten los mismos valores ilustrativos. |
| A-08 | 1280px | Resultados de la galería | El registro y la vista previa aparecen uno junto al otro; seleccionar una fila cambia la vista previa sin navegar. |
| A-09 | 390px | Resultados de la galería | El registro aparece antes de la vista previa; la búsqueda y los filtros se reorganizan y la acción larga para abrir se ajusta en varias líneas. |
| A-10 | Todos | Decoración desconocida | El aviso de elemento no encontrado indica que la escena no cambió; no se sustituye la escena. |
| A-11 | Todos | Diálogo de cambios sin guardar | Cancelar, guardar y continuar, y descartar y continuar aparecen en una confirmación que contiene el foco; al cancelar, el foco vuelve a su origen. |
| A-12 | Todos | Movimiento reducido | Todos los puntos finales siguen visibles y, una vez que termina el movimiento, no hay animaciones activas finitas de desplazamiento/escala. |

## Compilación, auditorías e inspección visual

Cadena de herramientas instalada: 96/96 entradas disponibles. La compilación usa la ruta absoluta de CLI y la entrada TSX asignada, y genera el HTML autocontenido asignado con fuentes locales incrustadas y sin solicitudes en tiempo de ejecución. Contraste de tokens: 158 pares comprobados en claro y oscuro; todos aprobados.

Capturas renderizadas inspeccionadas: ambas composiciones candidatas a 1280px; vista completa de contador/resultado/tema claro a 1280px y galería/resultados/tema oscuro a 390px. La inspección reveló el ajuste de línea del título para teléfono y una discrepancia en el token del botón de contorno; ambos se corrigieron en el código fuente. El código fuente final también se inspeccionó en galería/claro/1280px, calculadora/totales/oscuro/1280px, contador/resultado/oscuro/390px, inicio/claro/390px y diálogo de cambios sin guardar/oscuro/390px. En conjunto, cubren ambos temas en anchos de escritorio y teléfono. La primera auditoría completa detectó cuatro problemas de alineación en el eje del chat; la siguiente detectó cuatro problemas aislados en las líneas de subtotal. El código fuente ahora usa un documento de chat contextual de ancho completo y el patrón existente de etiqueta/valor en paralelo para subtotales; la regresión dirigida de seis casos para subtotales se aprueba sin cambiar la alineación numérica.

Comprobaciones enfocadas en el navegador sobre el artefacto compilado:

- La página de inicio de Entusiasta tiene exactamente dos herramientas; los resultados del contador no contienen COP ni una llamada a la acción de costo; se deniega el acceso directo a la calculadora.
- La frase sobre la medida faltante genera la pregunta; añadir medidas completa el conteo simulado; Calcular costo lo importa.
- Cambiar el precio del paquete de ejemplo a 10,000 COP produce 126,000 COP tras recalcular; aparecen dos subtotales de materiales; editar de nuevo elimina un total obsoleto.
- La búsqueda/filtros de la galería, los resultados vacíos, la limpieza, la vista previa en línea y la apertura de la Guirnalda seleccionada como una nueva escena de Taller sin guardar se aprueban.
- AlertDialog ofrece acciones para guardar/descartar/cancelar; se aprueban el cierre con Escape y el retorno al control inicial. La prueba inicial comprobó el desmontaje del diálogo demasiado pronto, a los 120ms; esperar a que el estado indicara que el modal estaba oculto solucionó la prueba, sin modificar el código fuente del producto.
- Las seis vistas se reorganizan en inglés a 1280/1024/390px en ambos temas (36 casos), sin desbordamiento horizontal de la página ni errores de página del navegador.
- Las 13 entradas únicas de selectores de evidencia coinciden con sus vistas renderizadas correspondientes. Los fotogramas clave de corte de fila se animan realmente a 0.28s; Quieto no deja animaciones en curso y conserva el estado del resultado. Solo se produce una solicitud local de documento de archivo, sin solicitudes de red.
- Se aprueban el rechazo del tipo MIME/tamaño de la foto, la recuperación y una estimación simulada etiquetada sin precios. La comprobación inicial del encabezado coincidió con la opción del inspector; usar el rol de encabezado corrigió la prueba, sin cambios en el código fuente. No se simulan la decodificación ni el reconocimiento de imágenes reales.

Generador final: aprobado; HTML autocontenido con bibliotecas reales, 653 KB, 2,133 módulos fuente empaquetados, sin conexión. No se descargaron paquetes ni recursos.

Comando final de contraste: `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py herramientas-chat@v1.r1.dir-a.html` — código de salida 0; aprobados los 158 pares de tokens claros/oscuros.

Comando final de auditoría renderizada: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py herramientas-chat@v1.r1.dir-a.html --widths 1280,1024,390 --max-combos 240` — código de salida 0. Cobertura real: 612 representaciones / 612 combinaciones planificadas, 18,816 mediciones de texto, 2,279 paradas de foco del teclado; sin advertencia de muestreo.

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

Este es el resultado de auditoría final real, obtenido tras corregir los hallazgos anteriores; no certifica autorización de producción, precisión del motor, persistencia ni conformidad total con WCAG. No se ejecutaron lint, comprobaciones de tipos, pruebas ni compilación del repositorio porque no se editó ningún repositorio de producción; sí se ejecutaron el generador de maquetas asignado, el comprobador de tokens, la auditoría renderizada y las comprobaciones enfocadas en el navegador.

## Impacto, inquietudes y preguntas pendientes

Consumidores de interfaz afectados de SP-7: T7.1 diseño y contenido, T7.5 inicio, T7.6 contador, T7.7 calculadora, T7.8 galería y T7.10 revisión visual. La compatibilidad no se determina hasta que el responsable seleccione y apruebe una dirección; este borrador no crea una migración de versión. Los contratos compartidos de cuentas/planes/proyectos no cambian. No se afirma aprobación, aplicación de restricciones en el servidor ni conformidad completa con los requisitos de accesibilidad del producto.

Decisiones pendientes para David/Planner (la implementación no debe inferir respuestas a partir de los valores de los datos de prueba):

Q: ¿Catálogo también debería aparecer en el inicio de Entusiasta/Designer/Designer Plus? El contrato del plan hermano incluye acceso básico al catálogo, mientras que el ejemplo de aceptación de SP-7 espera solo Chat y Contador para Entusiasta. Esta exploración sigue ese ejemplo de dos herramientas y muestra Catálogo solo con los datos de prueba de cinco herramientas de Master/personal.
Q: ¿Qué texto/valor de tolerancia devuelve el motor existente de conteo por foto? La vista previa reserva el rótulo y no muestra un porcentaje inventado; la frase “valor pendiente del motor” es solo para la maqueta y no debe publicarse.
Q: ¿Los filtros de tamaño deberían usar medidas exactas o rangos de tamaño acordados? Las opciones mostradas de 3 m / hasta 2 m son explícitamente valores ilustrativos de los datos de prueba, no una nueva taxonomía de productos.

Suposiciones: `/contador` es la ruta provisional del contador porque el encargo no define su ruta; Planner puede confirmarla sin cambiar la composición. No corresponde un estado vacío de inicio. El catálogo de productos activo exacto proporciona los nombres de las decoraciones, los valores de los filtros, los tamaños de los paquetes y los precios. Todo el contenido generado es neutro, claramente de prueba y limitado a estos flujos.
