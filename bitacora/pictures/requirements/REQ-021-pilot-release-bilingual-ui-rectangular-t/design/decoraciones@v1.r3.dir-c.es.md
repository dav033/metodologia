---
name: Edición en la pieza
contract_target: decoraciones@v1
status: draft
exploration: r3.dir-c
subplan: SP-5
requirements: [R8]
owner: David
date: 2026-10-29
source_behavior: decoraciones@v1.r3.behavior.md
chosen_thumbnail: decoraciones@v1.r3.dir-c.html.candidate-1.html
---

# Edición en la pieza — dirección C

Exploración independiente; **borrador, sin aprobación**. No sustituye ni escribe el contrato canónico `decoraciones@v1`. El propietario elegirá la dirección y una finalización posterior escribirá el contrato compartido. Ninguna decisión aquí autoriza la implementación de un borrador.

## 1. Identidad y trazabilidad

Fuentes: brief `decoraciones@v1.r3.behavior.md`, SPEC «Comportamiento — SP-5 (ronda 11 respondida)», SP-5 del PLAN vigente y comentarios del propietario 2026-10-29T06:58. Consumidores previstos: T5.1 copia posterior del contrato aprobado, T5.3 biblioteca personal del Taller y T5.5 revisión visual. Esta exploración no modifica PLAN, SPEC, otros diseños ni repositorios.

Leído en ambos repositorios: `src/app/globals.css`, `src/components/tres-d/Biblioteca.tsx`, `src/components/tres-d/Taller3D.tsx` y la navegación de `src/components/ui/shell/CabeceraApp.tsx`. La superficie real ya permite guardar piezas/escenas por nombre y ocasión (`AccionesPieza`), muestra miniaturas, fichas y filtros de ocasión/color/globo, y guarda datos localmente en el navegador. Se conserva esa ubicación en el Taller; no se crea una página de biblioteca ni una página de destino.

Se leyeron los contratos y el HTML finalizados de `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`. Sus encabezados de Pictures/Sempertex, idioma/cuenta, regla horizontal de rutas, Geist, radios y alias accesibles son la referencia compartida. La composición propia de SP-5 se limita a la biblioteca y la captura de decoraciones dentro del Taller. No se traslada la importación de proyectos de SP-4: **SP-5 no importa nada**.

## 2. Propósito y usuarios

Master Designer y personal interno con Taller guardan una pieza o la escena completa y la reutilizan mediante una copia en su proyecto abierto. La respuesta confirmada del servidor distingue un guardado real de un intento pendiente o fallido. Empleado interno y Administrador consultan otra cuenta con `proyectos.ver_todos`; el original permanece de solo lectura y Colocar copia únicamente añade a su propia escena.

Los datos son explícitamente de ejemplo: Guirnalda, Mi escena, Proyecto de ejemplo y Cuenta de ejemplo. No se inventan clientes, fechas, eslóganes ni materiales comerciales. Fashion Violeta y formatos R-5/R-12 proceden del catálogo de código. Los SVG son miniaturas esquemáticas de composición, no renders ni fotografías reales. Las ocasiones de ejemplo General/Cumpleaños/Boda proceden de la taxonomía del Taller.

## 3. Enfoque y elección de miniatura

**Candidata 1 elegida:** biblioteca vertical al lado del visor, con un formulario que se abre en el elemento que cambia. Conserva el mapa espacial de los paneles actuales y deja el objeto junto a su nombre/ocasión. El mockup completo conserva además el inspector original para guardar la pieza o la escena; en móvil ese mismo formulario pasa bajo el visor, antes de la lista.

**Candidata 2:** bandeja horizontal bajo el visor y captura en el inspector. Ambas miniaturas se escribieron y renderizaron antes del TSX completo. La segunda separa el guardado de su resultado y concentra menos controles de búsqueda cerca de los elementos; se conserva como evidencia, no como otra pantalla de producto.

Aproximación de manipulación directa: Editar transforma la fila en campos de nombre/ocasión; Cancelar devuelve la fila sin cambiarla; Guardar cambios confirma en el mismo sitio. La selección visible en el visor ancla la captura. Colocar produce una copia que se asienta dentro de la propia escena. No se exige arrastrar ni usar gestos para completar ningún flujo.

### Ocho ejes

| Eje | Evidencia presente |
|---|---|
| concepto | Edición en la pieza: guardar la selección desde el inspector existente y cambiar nombre/ocasión dentro de su propia fila, sin salir del Taller. |
| disposición | Masthead y rutas compartidos; riel de 60 px, biblioteca de 320 px, visor flexible e inspector de 264 px. La edición expande solo la fila elegida. En teléfono, visor → captura abierta → biblioteca. |
| navegación | Taller 3D y Proyectos conservan su regla horizontal. Buscar y filtrar actúan en la biblioteca; En este navegador se revela con details. La edición se confirma/cancela en su fila; el borrado abre AlertDialog. |
| tipografía | Geist Sans/Geist Mono locales del producto. H1 24 px, biblioteca 18 px, nombre 15 px, formularios 13–14 px y metadatos 12 px; nombres y acciones envuelven dentro del mismo panel. |
| densidad | Biblioteca compacta de filas con miniatura de 64×70 px, 16 px entre registros y filtros nativos 2×2. El nombre/ocasión se ocultan hasta Editar; el panel de captura solo se despliega al guardar. |
| componentes | Button e Input reales shadcn/Base UI, Skeleton y AlertDialog con Animate UI. Filas, formulario en contexto, visor SVG y details nativo recompuestos con los radios y controles de los contratos hermanos. |
| color | Tokens exactos de Pictures en ambos temas: fondo/superficie/texto/acento y familia taller-*. Acento en Colocar/Guardar y selección; éxito solo tras respuesta simulada confirmada; error junto al intento fallido. Borde de control alias texto-tenue, como los hermanos. |
| movimiento | Asiento táctil: filas comprimen a .965 y asientan a 1.006 en 520 ms, desfase 65 ms; campos abren desde el punto de edición; confirmar asienta con giro ±2 grados; copia viaja 35 px al visor. Controles 170 ms con presión .965. Natural 320/140 ms; sutil 160/100 ms. Quieto, still, reduced-motion sin desplazamiento ni animación; pestaña oculta pausa CSS. |

## 4. Sistema visual y componentes

La fuente de tokens existe: **no se usa la paleta por defecto del kit**. Se copian las asignaciones de `proyectos@v1` y se conservan los valores de producción en ambos temas. Fuentes WOFF2 Geist Sans y Geist Mono del build local de t12 embebidas por el builder, sin red.

| Fuente Pictures | Roles del kit | Claro / oscuro |
|---|---|---|
| fondo | background | #faf9fc / #0b0c10 |
| superficie | card, popover | #ffffff / #16181f |
| texto | foregrounds | #1c1425 / #f4f5f7 |
| texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| acento / sobre-acento | primary / primary-foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| texto-tenue | input/control edge (alias accesible de los hermanos) | #766c85 / #8a91a0 |
| borde / borde-suave | decorative border/rule | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| éxito / éxito-suave | success / success-soft | #1f7a55 / #dcf5e9; #78d6a8 / #173b31 |
| error / error-suave | destructive / destructive-soft | #b23a45 / #ffeaec; #ff979f / #43252a |
| taller-panel, taller-visor, taller-barra, taller-tarjeta, taller-elegido, taller-acento | superficies del Taller | Valores exactos de globals.css; no nuevo tema |

Componentes reales: `shadcn:button default|outline default|focus|pressed|disabled|pending` desde `@/components/ui/button`; `shadcn:input text default|invalid|disabled` desde `@/components/ui/input`; `shadcn:skeleton library loading` desde `@/components/ui/skeleton`; `shadcn:alert-dialog delete open|pending|error` desde `@/components/ui/alert-dialog`, con primitivas Animate UI instaladas. Los selectores son **native:select**, no se presentan como un Select de shadcn. Fila, formulario inline, panel de captura y visor SVG son composiciones propias; details/summary de cuenta y legado son nativos.

Radios compartidos: panel 32 px, inset 24 px, campos 18 px, botones pill. Se mantienen los controles táctiles de al menos 44 px. `mountMockup`/`useMockup` de `@kit/mockup` generan Vista/Estado/Diálogo/Tema/Movimiento fuera del producto; `useMotionProfile` de `@kit/motion` determina tiempos y reducción. Sin fallback HTML para el mockup completo, sin instalación ni descarga.

## 5. Navegación e interacción

La entrada sigue siendo Taller 3D `/3d`, con riel y paneles ya existentes; Proyectos permanece en la regla horizontal del hermano. El mockup no navega hacia otros contratos: sus entradas identifican el destino mediante feedback local. Los controles de otras herramientas mantienen etiquetas y ubicación; no simulan funciones 3D completas.

En el inspector existente, Guardar en mi biblioteca abre captura de la pieza; Guardar toda la escena en mi biblioteca abre la composición completa. Nombre y ocasión permanecen juntos hasta confirmar/cancelar. La biblioteca ordena grupo del servidor primero y luego el details **En este navegador**; abrirlo no importa ni crea elementos de cuenta. El grupo del navegador no tiene acción de importación, progreso ni error de importación.

Editar revela nombre/ocasión en la fila. El foco pasa al nombre; tras guardar o cancelar vuelve al botón Editar. Borrar abre AlertDialog con Cancelar como primer foco; Escape/cancelar restaura el control iniciador. Colocar es siempre un botón disponible por teclado. Las acciones de modificación están ausentes en filas ajenas, también cuando la barra de inspección fuerza el estado Editar.

El selector de propietario visible al personal interno representa una propuesta de descubrimiento, pendiente de Q1; no cambia el rol de la cuenta actual. El visor siempre representa el proyecto propio de quien coloca una copia. No se abre el proyecto de otra cuenta para editarlo.

## 6. Flujos

1. **Guardar pieza/escena:** seleccionar entrada existente → ver alcance («La pieza sola» / «La escena entera (3 piezas)») → nombre y ocasión → Guardar → Guardando… con envío repetido bloqueado → respuesta confirmada → Guardado en tu cuenta y nuevo registro. Un error conserva los campos y permite Reintentar. Nombre vacío anuncia «Escribe un nombre» y enfoca el campo.
2. **Buscar y colocar:** buscar nombre y combinar ocasión, tipo, color y globo → resultados/ninguna coincidencia → Colocar → una copia en el proyecto propio; feedback en la misma superficie. Quitar filtros recupera los resultados. Los selectores del mockup muestran un subconjunto neutral; producción conserva la taxonomía y opciones derivadas existentes.
3. **Editar elemento propio:** Editar → campos inline → Guardar cambios → confirmación del servidor antes de cambiar la fila. Error conserva el formulario. Cancelar restaura la presentación anterior. En esta exploración, editar significa nombre y ocasión; Q2 mantiene explícito el alcance de actualización de composición.
4. **Eliminar elemento propio:** Quitar de mi biblioteca → confirmación nombrando el elemento y aclarando que copias colocadas no cambian → Eliminar → pendiente → eliminación confirmada. Fallo mantiene el diálogo y permite reintentar; Cancelar conserva el elemento.
5. **Personal interno:** abrir biblioteca autorizada de Cuenta de ejemplo → indicador Solo lectura junto al propietario y al elemento → ninguna acción de cambio/borrado → Colocar copia → copia en la propia escena; original intacto.
6. **Cuenta/sesión cambia:** retirar inmediatamente lista, edición, captura y resultados de la cuenta previa → cargar cuenta actual sin filas anteriores → lista confirmada o vacía/error. El estado inspeccionable permanece pendiente a propósito: no mezcla la identidad previa y la nueva. El grupo local permanece separado y explícitamente ligado al navegador.

## 7. Vistas

| Vista del inspector | Superficie del producto | Contenido y acciones |
|---|---|---|
| library | Taller / Mi biblioteca | Búsqueda, filtros, lista de cuenta, colocar, editar metadata/borrar propios, disclosure local, visor y captura progresiva |
| save-piece | Mismo Taller, inspector de la pieza | Formulario abierto para la pieza seleccionada, nombre/ocasión, guardar/cancelar y confirmación/error |
| save-scene | Mismo Taller, inspector de escena | Formulario abierto para escena completa; distingue alcance, sin sustituir el proyecto abierto |
| staff | Misma biblioteca, propietario autorizado ajeno | Selector de propietario propuesto, Solo lectura, miniatura, nombre, ocasión, Colocar copia; ausencia de editar/borrar |

No son páginas nuevas ni rutas nuevas. El único diálogo declarado es eliminar una decoración propia. La eliminación/desactivación de cuentas pertenece a Cuentas/SP-2; SP-5 no rediseña su pantalla ni el catálogo global/admin.

## 8. Estados inspeccionables

| Valor nativo Estado | Qué se ve / recuperación |
|---|---|
| normal | Biblioteca y visor, captura cerrada hasta pedir guardar |
| editing | Nombre/ocasión dentro de la primera fila propia; confirmar/cancelar |
| loading | Esqueletos y Cargando decoraciones; ninguna fila del servidor |
| empty | Lista del servidor vacía y guardar escena; grupo del navegador separado |
| list-error | No se pudo cargar tu biblioteca, Reintentar; ninguna fila de cuenta antigua |
| saving | Formulario bloqueado, Guardando…; ningún Saved ni inserción anticipada |
| saved | Guardado en tu cuenta después de respuesta confirmada; Cerrar |
| save-error | Nombre/ocasión retenidos, fallo explícito y Reintentar |
| invalid | Error asociado al nombre vacío, recuperación en el mismo campo |
| readonly | Otra cuenta de personal interno; sin renombrar/editar/eliminar |
| account-switch | Lista anterior retirada, Cargando la cuenta actual; sin captura ni acciones de guardado |
| no-results | No hay coincidencias, Quitar filtros |
| placed | Copia visible en la escena propia y feedback de colocación |
| update-error | Campos inline retenidos; corregir/reintentar/cancelar |
| denied | Rechazo localizado Sin acceso al Taller; sin biblioteca ni datos restringidos |
| delete-error | AlertDialog conserva el elemento; mensaje de error, reintentar/cancelar |

`scene=delete` muestra la confirmación propia desde cualquier vista compatible; se suprime en solo lectura, cambio de cuenta y sin acceso. Un error de red se representa mediante list-error/save-error/update-error/delete-error; no se inventa una cola de sincronización. No hay importación ni estados de importación. La simulación es finita y deliberada: no prueba persistencia, permisos o APIs reales.

## 9. Diseño adaptable

Rango 360 px en adelante, como Proyectos. Puntos de comprobación 390/768/1280 px, ambos temas.

- **360–639 px:** gutters 20 px, masthead y acciones envuelven, riel e inspector lateral ocultos como contexto móvil del hermano. Orden visor → acciones de guardar → captura abierta → biblioteca. La edición inline permanece dentro de su fila, miniatura 80×80 px. Los cuatro filtros se distribuyen 2×2. Página con scroll vertical; ningún scroll horizontal ni controles recortados.
- **640–1099 px:** gutters 24 px; riel 60 px, biblioteca 300 px, visor flexible; inspector sustituido por la captura bajo visor/biblioteca cuando se abre. No hay columna derecha vacía.
- **≥1100 px:** shell max 1520 px, gutters 40 px; riel 60 px, biblioteca 320 px, visor flexible, inspector 264 px. Visor crece con la edición inline sin saltar a una nueva página.

AlertDialog ancho máximo 500 px / viewport menos 40 px, altura máxima viewport menos 48 px y scroll interno. Nombres y botones envuelven; navegación y estados no dependen del hover.

## 10. Accesibilidad y movimiento

Objetivo WCAG 2.2 AA; el mockup aporta verificaciones renderizadas acotadas, no certifica la app. Todos los inputs/selects tienen label; icon buttons tienen nombre accesible, miniatura decorativa y visor con descripción textual. Búsqueda mantiene foco y texto mientras filtra; los errores usan alert y la confirmación/colocación status. El foco visible usa el acento del producto con 3 px y offset 4 px. El diálogo modal se monta con la biblioteca real y protege su fondo; Cancelar precede Eliminar.

Movimiento de asiento táctil, sin animación de marketing: filas `tile-seat` 520 ms, desfase 65 ms; campos `field-seat` desde origen izquierdo/derecho; confirmación `confirm-seat`; copia `copy-seat` 35 px; botones 170 ms y presión scale(.965). `useMotionProfile` mantiene natural 320/140 ms y sutil 160/100 ms. Transform/opacity primero; el texto permanece legible. Quieto, `?still=1` y preferencia de SO eliminan toda animación/transición sin esconder contenido ni acciones. La pestaña oculta pausa CSS; no existe un bucle decorativo fuera del viewport. Spinner de Guardando solo funciona cuando ese estado se está mostrando.

## 11. Criterios visuales y evidencia

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| C-01 | 390/768/1280 | todos | Pictures/Sempertex, Geist y navegación horizontal Taller/Proyectos siguen el shell hermano. |
| C-02 | ≥1100 | normal | Biblioteca de 320 px entre el riel y el visor; inspector de captura a la derecha. |
| C-03 | 360–639 | guardar | El formulario de captura aparece entre visor y lista. |
| C-04 | todos | edición | Solo el registro elegido contiene los campos nombre/ocasión y Guardar cambios/Cancelar. |
| C-05 | todos | guardando | Guardando… permanece visible sin sello de guardado ni nuevo elemento prematuro. |
| C-06 | todos | guardado | Guardado en tu cuenta aparece tras la confirmación, con icono y texto de éxito. |
| C-07 | todos | error de guardado | Se conservan los valores y Reintentar permite recuperar el guardado. |
| C-08 | todos | cargando | Esqueletos sustituyen la lista del servidor; ningún elemento previo permanece. |
| C-09 | todos | vacío | La lista del servidor explica que está vacía; En este navegador permanece en otro grupo. |
| C-10 | todos | solo lectura | Propietario ajeno y Solo lectura son visibles; editar y eliminar están ausentes. |
| C-11 | todos | colocado / personal | El feedback identifica una copia en la escena propia sin modificar el original ajeno. |
| C-12 | todos | cambio de cuenta | La biblioteca contiene cero filas de servidor y no muestra controles de captura. |
| C-13 | todos | normal / local abierto | En este navegador revela elementos locales sin botón de importación. |
| C-14 | todos | sin resultados | Quitar filtros limpia filtros y búsqueda, y recupera los resultados. |
| C-15 | todos | eliminar/error | AlertDialog nombra el elemento, empieza en Cancelar y conserva los datos ante error. |
| C-16 | 390/1280 | oscuro / claro | Los valores de color y fuentes proceden de globals.css y del build local. |
| C-17 | todos | movimiento reducido/quieto | No quedan animaciones activas; datos y acciones siguen visibles. |
| C-18 | 360–1280 | todos | No hay scroll horizontal ni botones cortados; los campos mantienen su foco al escribir. |

### Verificación real

- Builder real offline: salida `decoraciones@v1.r3.dir-c.html`, 648 KB / 2132 archivos fuente, exit 0. Dos miniaturas compuestas y renderizadas antes de escribir el entry completo. Ninguna petición de fuentes/assets remotos.
- `contrast.py`: **158 pares comprobados en claro y oscuro, todos aprobados**, exit 0.
- Auditoría Playwright del HTML final: **408 renderizados (408 combinaciones planificadas), 15950 mediciones de texto, 2314 paradas de foco**, a 1280/390/768 px, ambos temas; exit 0, sin muestreo.

  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

  Comando: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <design>/decoraciones@v1.r3.dir-c.html --widths 1280,390,768 --max-combos 240`.
- Playwright suplementario: **APROBADO, 13 grupos de comprobaciones**, incluidos 56 escenarios de reflujo (360/390/640/768/1024/1100/1280 px × ambos temas × cuatro vistas). Verificados: continuidad al escribir; inserción/confirmación solo tras respuesta simulada; reintento conservando valores; edición de cada fila y foco exacto; borrado confirmado; Escape/cancelar y devolución del foco tras terminar la animación de salida; controles ajenos ausentes; colocación de copia propia; cambio de cuenta con cero filas antiguas; legado sin importación; filtros combinados; captura móvil antes de lista; animaciones reales, Quieto, `?still=1` y preferencia reducida del SO. **0 peticiones HTTP externas y 0 errores de ejecución**. Una comprobación inicial esperó menos que la animación de salida del diálogo; la repetición final comprobó el estado asentado y pasó.
- `compare_directions.py <design>/decoraciones@v1.r3.dir-c.html --json`: **ok=true, evidence_ok=true, missing_evidence=[]**, exit 0. Comprobación de selectores de esta única dirección; no demuestra diversidad frente a las otras direcciones.
- Capturas finales inspeccionadas en memoria a **1280/390 px en ambos temas**: edición inline ES claro, guardado confirmado EN oscuro, reintento móvil ES claro y biblioteca ajena EN oscuro. Sin archivos de captura adicionales; miniaturas también renderizadas antes de escoger.
- Validación de entrega: seis archivos específicos de la revisión presentes, ocho ejes con el esquema pedido, doce secciones en la nota y ningún asset externo referenciado por el HTML. Sin cambios a archivos canónicos.

Limitaciones honestas: los temporizadores representan respuestas simuladas, no conectan al servidor. Recarga, otro navegador, validación de composición, permisos reales y aislamiento real deben probarse en T5.3/T5.4/T5.5. Los accesos a otras pantallas solo señalan el contrato hermano correspondiente.

## 12. Decisiones abiertas y supuestos

**Confirmado:** sin importación; servidor primero; legado En este navegador intacto; Master Designer y personal interno con Taller; personal interno lee ajenos sin cambiar/borrar; Colocar añade copia propia; Guardado solo tras confirmación; cuenta con decoraciones se desactiva, no se elimina. No se reabre ninguna de estas decisiones.

**Preguntas para el propietario:**

- Q1: ¿El personal interno accede a decoraciones ajenas mediante el selector de propietario dentro de Mi biblioteca? La exploración muestra esta entrada, porque el brief confirma la lectura pero no su punto de descubrimiento.
- Q2: ¿Actualizar una decoración incluye sustituir su composición/miniatura o solo nombre y ocasión? Esta exploración permite editar metadata propia en la fila; no inventa un editor del original guardado.

**Impacto:** SP-5, T5.1/T5.3/T5.5; vistas del Taller, guardado, edición inline, biblioteca, solo lectura y cambio de cuenta. Compatibilidad **sin determinar** respecto de cualquier implementación aprobada: se trata de una nueva exploración pendiente de elección, no de una revisión aprobada. Sin impacto escrito sobre los contratos hermanos ni nuevas obligaciones para sus tareas. El finalizador debe resolver Q1/Q2 e incorporar la dirección elegida; esta exploración no concede aprobación.
