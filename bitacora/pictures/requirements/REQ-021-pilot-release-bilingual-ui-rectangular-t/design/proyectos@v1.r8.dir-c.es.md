---
name: Archivo de muestrarios
status: draft
kind: direction-exploration
contract_ref: proyectos@v1
subplan: SP-4
requirements: [R6, R7]
revision: r8.dir-c
owner: David
chosen_thumbnail: proyectos@v1.r8.dir-c.html.candidate-1.html
---

# Archivo de muestrarios — dirección C

Exploración táctil/lúdica independiente, **no aprobada**. Esta nota no es el contrato canónico de doce secciones ni es un insumo de implementación. El propietario elige la dirección antes de que un finalizador independiente escriba el contrato compartido. El brief de exploración acotado reemplaza al par de salidas canónico: solo se escriben los seis archivos de esta dirección y el RESULT de delegación requerido. No se modifica ningún código fuente de producción, SPEC, PLAN, contrato compartido, historial, otra dirección, memoria del proyecto ni estado de aprobación.

## Concepto, movimiento memorable y elección

Un decorador vuelve a un arreglo completo como se vuelve a una muestra en un archivo de estudio. Los proyectos se convierten en **muestras de material archivadas**: una pestaña de fecha sobresaliente, una pequeña ilustración de escena, el nombre del montaje, su propietario y una acción directa para abrirlo. La pantalla principal responde “¿Qué montaje estoy continuando?” sin un dashboard, estadísticas decorativas ni carrusel. Al guardar, la misma muestra se abre como un folio con una nota de encuadernación; las opciones de conflicto se despliegan encima, donde no pueden confundirse con un guardado exitoso.

El movimiento memorable es **una carpeta que se desliza hasta su lugar mientras su pestaña de fecha se eleva, seguida de un sello de guardado comprimido**. Las carpetas se asientan con un pequeño rebasamiento en lugar de desaparecer en secuencias de fade-up. En el folio abierto, el arco de globos se puede mover directamente; dos botones con texto ofrecen el mismo cambio voluntario. El resorte instalado asienta esa manipulación. El movimiento reducido muestra de inmediato la misma geometría, estado y acciones.

Se escribieron dos composiciones en miniatura antes del TSX:

- **Candidata 1, seleccionada:** [Archivo de muestrarios](proyectos@v1.r8.dir-c.html.candidate-1.html). Filas de carpeta de ancho completo mantienen juntos el nombre completo, la propiedad y la acción de apertura. Cada proyecto está disponible directamente sin avanzar un mazo.
- [Candidata 2, conservada](proyectos@v1.r8.dir-c.html.candidate-2.html): Caja de muestras. Una muestra reciente grande y muestras más pequeñas debajo crean una jerarquía más fuerte de proyecto destacado, pero hacen que la colección sea menos uniforme de recorrer. No se desarrolló más.

Las miniaturas son pequeños bocetos visuales en línea con ambos temas y CSS responsivo, no componentes de biblioteca sustitutos. El HTML completo usa el toolchain real instalado. Ninguna miniatura está aprobada.

### Por qué esto no es lo predeterminado

La silueta de carpeta tiene un propósito: su pestaña expone el tiempo, su muestra enseña el mundo material del producto y su cuerpo agrupa el proyecto con su cuenta. No hay una cuadrícula de dashboard genérica, ni tarjetas de métricas, ni tendencias ornamentales. La colección se lee en vertical; abrir un proyecto revela un folio encuadernado en lugar de un clon de editor guiado por un inspector. Una navegación de texto neutra rodea la única acción primaria malva. Lo lúdico vive en la silueta física y en la respuesta al tacto, mientras que los controles de entrada siguen siendo familiares.

### Registro de estilo

Se leyeron las notas hermanas `cuentas-admin@v1.r7.dir-a/b/c.md` y `taller-esenciales@v1.r6.dir-a/b/c.md`. Cuentas explora un registro editorial, un pase de acceso de dos hojas/dock inferior y pases de permisos perforados. Taller explora una hoja de trabajo, un escenario medido axonométrico y un banco de corte con herramientas a lo largo de su junta. Esta dirección no usa ninguna de esas composiciones, ni ranuras de permisos, ni dock inferior, ni regla, ni cuadrícula de corte. Su sello distintivo es el **archivo vertical de muestras, las pestañas de fecha sobresalientes y el folio de guardado encuadernado**. La marca compartida de anillo/punto, los tokens de Pictures, el lenguaje directo en español, los controles familiares y el tema de globos/Backing conectan intencionalmente los subplanes. Una ilustración de escena tipo escenario es dato de producto compartido, no un esqueleto de navegación o de layout repetido.

## Ocho ejes

| Eje | Expresión observable | Evidencia renderizada |
|---|---|---|
| Concepto | Muestras de material archivadas para los montajes guardados; la propiedad permanece junto a la escena y el nombre. | `.project-file`, `.file-tab`, `.file-info` |
| Layout / composición | Una pila vertical de carpetas horizontales: muestra de 200 px, nombre flexible, acción al final. El folio abierto tiene una escena amplia y una nota de encuadernación de 300 px. En teléfono, la acción de la carpeta pasa debajo de la muestra/nombre y la nota de encuadernación se apila. | `.file-stack`, `.project-file`, `.file-action`, `.folio-body` |
| Navegación | Herramientas de espacio de trabajo discretas arriba, “Abrir proyecto” directo en cada carpeta, búsqueda por nombre de proyecto, filtro de propietario solo para personal interno, acción explícita de volver. Cada fixture también tiene los selectores de planificación nativos requeridos. | `.global-nav`, `.archive-tools`, `.project-file .press` |
| Tipografía | Cuerpo en Arial/Helvetica sin conexión; título 32/28 px, nombre de carpeta 20/17 px, cuerpo 14–15 px; fechas y conteos monoespaciados de 12 px. Los nombres largos de proyecto se ajustan en varias líneas. | `.page-heading h1`, `.file-info h2`, `.file-tab` |
| Densidad / forma | Relleno de 24 px en carpetas/paneles, 20 px en teléfonos; 40 px entre carpetas para exponer las pestañas; acciones de mínimo 44 px y campos de 46 px; esquinas de folio de 18/14 px y encuadernaciones punteadas. | `.project-file`, `.folio-band`, `.binding-note`, `.input`, `.press` |
| Componentes | Botones, inputs y skeletons reales de shadcn/Base UI; Dialog y AlertDialog reales de Animate UI. Carpeta personalizada, muestra de escena SVG, sello de guardado, pliegue de conflicto y nota de encuadernación. No se necesita checkbox: el consentimiento de importación es la acción explícita con nombre. | `[data-slot=button]`, `[data-slot=input]`, `.mini-scene`, `.conflict-fold` |
| Color | Fondos, superficies y texto existentes de Pictures; acción malva y materiales lavanda. Navegación neutra. Advertencia/error/éxito tienen explicaciones escritas además del color. Los bordes de control fuertes están separados de los divisores sutiles. | `.sample`, `.press[data-variant=default]`, `.notice`, `.global-nav` |
| Movimiento | Inserción expresiva de carpetas, pestañas que se elevan, folio con bisagra y sello comprimido; respuesta a la pulsación; arrastre voluntario con resorte y paridad con botones. Entrada expresiva de 520 ms, escalonado de 45 ms entre carpetas, 200 ms de retroalimentación en controles repetidos; natural 320/140 ms y sutil 200/90 ms. | `.project-file`, `.file-tab`, `.press`, `.stamp-ink`, `.scene-piece` |

El JSON hermano contiene exactamente los ocho ejes y la evidencia de selectores. Cada selector se verificó contra elementos renderizados. Chromium reportó animaciones activas `folio-open`, `folder-seat` y `tab-seat` con duración de 520 ms. `useMotionProfile()` provee el resorte del arrastre (rigidez expresiva 220, amortiguación 16, masa .9); el CSS usa los tokens de duración/easing del perfil. El rebasamiento de entrada usa cubic-bezier(.34,1.4,.64,1), nunca vuelve el texto transparente y no anima dimensiones de layout. Las pestañas ocultas pausan las líneas de tiempo CSS; la escena no tiene bucle autónomo ni fuera de pantalla. El movimiento reducido del SO, Quieto y `?still=1` asientan la escena sin cambiar las acciones disponibles. El arrastre voluntario sigue siendo voluntario; ninguna acción requiere arrastrar.

## Sistema existente y bibliotecas reales

La inspección de solo lectura cubrió los `AGENTS.md` de ambos repositorios, `src/app/globals.css`, `src/app/layout.tsx`, el guardado local de escenas y sus consumidores de `Taller3D.tsx`. Ambos usan alias semánticos de Pictures; ambos layouts cargan Geist a través de Next. Este artefacto usa deliberadamente fuentes sans/monoespaciadas locales de respaldo instaladas y no descarga archivos de fuentes. Producción debería conservar su Geist ya cargado, con los mismos tamaños por rol; las métricas exactas de la fuente requieren la revisión visual de la implementación.

| Token existente del proyecto | Rol en el kit / uso | Claro / oscuro en esta exploración |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--texto` | roles de foreground | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | `--muted-foreground` | `#6b6178` / metadatos más claros propuestos `#adb3c0` |
| `--superficie-2` | `--muted`, `--secondary` | `#efe9f8` / `#242733` |
| `--acento`, oscuro `--taller-acento` | `--primary`, `--ring` | `#6d3fe0` / `#b9a4ff` |
| `--sobre-acento` | `--primary-foreground` | `#ffffff` / `#120b24` |
| `--borde` | divisor sutil `--border` | `#e3daef` / `#383c48` |
| `--texto-suave`, `--taller-medio` | borde de control fuerte `--input` | `#6b6178` / `#a59db5` |
| `--taller-visor` | adaptación del fondo de la escena | `#ebe7f1` / neutro propuesto `#24212d` |
| `--ease-rebote` | gramática expresiva de asentamiento | cubic-bezier(.34,1.4,.64,1) |

Los metadatos oscuros más claros y la adaptación del fondo de la escena son propuestas visuales locales, no ediciones de tokens compartidos. No se propone ningún dato de escena persistido adicional ni una nueva API de proyectos.

Fuentes reales: `shadcn:button default/outline/ghost`, import `@/components/ui/button`; `shadcn:input default/invalid`, import `@/components/ui/input`; `shadcn:skeleton loading`, import `@/components/ui/skeleton`; `shadcn:dialog default` con la primitiva instalada de Animate UI, import `@/components/ui/dialog`; `shadcn:alert-dialog confirmation` con la primitiva instalada de Animate UI, import `@/components/ui/alert-dialog`. El movimiento proviene de `motion/react` y `@kit/motion`; el shell de planificación de `@kit/mockup`. Se inspeccionaron las exportaciones reales de los componentes. **No se usó ningún kit HTML de respaldo, instalación ni recurso de red.**

## Comportamiento, vistas y límites de la simulación

Fuentes: el `SPEC.md` y `PLAN.md` actuales, `PLAN.json` revisión 1 y el `proyectos@v1.r8.behavior.md` compartido. La fuente actual asigna R6/R7 a SP-4 y confirma las decisiones de la ronda 9 sobre guardado, propiedad, escena completa e importación. La fuente de comportamiento se conserva; esta exploración no crea nuevas aprobaciones.

| Valor nativo de Vista | Fixture y trabajo |
|---|---|
| `propios` | Lista de proyectos propios de Ana; búsqueda por nombre, búsqueda vacía, carga incremental, reintento y regreso a la importación heredada. Los proyectos propios abren el folio de guardado. |
| `todos` | Ana como empleada interna autorizada; todos los fixtures de proyectos autorizados, selector de propietario y nombres. Los proyectos ajenos abren la consulta de solo lectura. El selector representa el punto de entrada del personal; no es un permiso otorgado por este artefacto. |
| `taller` | Primer guardado con nombre, estado pendiente/guardando/guardado, Guardar ahora, reintento sin conexión/por error, confirmación obsoleta, conflicto de concurrencia y recuperación. El diagrama ilustra la UI circundante de proyectos guardados, no un nuevo motor 3D. |
| `consulta` | El original de Camila se muestra en solo lectura; sin herramientas de mover/editar. Guardar una copia propia requiere acceso a Taller. `sin-taller` quita el destino Taller y deshabilita la acción de copia con una explicación escrita. |
| `importar` | Consentimiento explícito para Ana, aviso de dispositivo compartido, primera importación con nombre, Ahora no, finalización segura ante reintentos y recuperación de datos incompatibles. Sin carga automática. |

La colección usa seis registros simulados pequeños y realistas, nunca un total de producción falso. La búsqueda y el filtrado operan sobre todo ese fixture antes de recortarlo. Los cambios de filtro reinician el recorte. “Cargar más” agrega filas; el reintento de una página parcial conserva las filas visibles. **Esto no verifica la búsqueda en todo el servidor más allá de 50 registros, el enlace del cursor ni las respuestas de red fuera de orden**; T4.3/T4.4/T4.6 son responsables de esos requisitos reales. No se llama a ningún endpoint remoto.

El primer guardado pide un nombre y muestra validación en línea. Los cambios simulados posteriores se aplican con debounce de 500 ms y luego muestran guardando y finalización; 500 ms es el valor predeterminado del Planner, no una decisión de tiempos del propietario. Los cambios pendientes no se presentan como confirmados. Un conflicto deshabilita Guardar ahora y detiene la ruta de guardado ordinaria conservando la ilustración local. “Guardar como copia” abre el Dialog de guardado con nombre. “Cargar versión guardada” usa AlertDialog y luego expone “Recuperar borrador local” para el fixture de la misma cuenta. Salir con cambios pendientes ofrece guardar y salir, conservar el borrador y salir, o cancelar; guardar no está disponible sin conexión ni durante un conflicto. La persistencia de escena/cuenta, los recibos idempotentes y la semántica real de la cola siguen siendo responsabilidad de la implementación.

Los avisos de error/sin conexión de importación usan franjas planas con reglas dentro del folio; en teléfonos los íconos de aviso van sobre el texto de ancho completo. La ilustración de importación es explícitamente una muestra; no analiza ni accede al almacenamiento del usuario. Los datos incompatibles exponen una descarga de **JSON de ejemplo** etiquetada en lugar de fingir exportar una escena heredada real. La descarga en producción debe contener los bytes originales sin modificar. El original debe permanecer sin cambios tras un rechazo, una falla de validación o un éxito. Los nombres y las escenas completas son portables; las conversaciones de IA y las imágenes generadas permanecen locales al navegador. No se agrega eliminación, transferencia, UI de historial de versiones, sobrescritura oculta ni reasignación automática de cuenta.

Los fixtures del runtime se remontan intencionalmente al cambiar de vista/estado. El tema y el movimiento preservan la UI montada. Las variables locales de la página demuestran la selección/copia y la recuperación; no son almacenamiento aislado por cuenta ni una sesión autenticada. “Volver a entrar · simulación” reinicia un fixture y no es un flujo de inicio de sesión real.

### Cobertura de estados y diálogos

Los selectores nativos conservan **Mockup**, `view`/Vista, `state`/Estado, `scene`/Diálogo, `theme`/Tema y `motion`/Movimiento. Los dieciséis valores de estado declarados son alcanzables. Las vistas contextualizan los estados; las combinaciones irrelevantes conservan el fixture normal en lugar de inventar un nuevo flujo de trabajo.

| Estado values | Fixture aplicable y recuperación visible |
|---|---|
| `normal` | Todas las vistas, fixture con datos y acciones habituales habilitadas. |
| `cargando` | Listas y folio de guardado: Skeletons reales y estables; `guardando` es el fixture de importación en curso. |
| `vacio` | Listas: crear el primer proyecto. Taller: escena sin guardar, el primer guardado abre el Dialog de nombre. |
| `error` | Reintento en la lista; el Taller conserva el trabajo pendiente y ofrece reintentar el guardado; el reintento de importación explica que una respuesta incierta no debe duplicar un proyecto. |
| `guardando`, `guardado`, `pendiente` | Estado de guardado y acción duplicada deshabilitada; procesamiento/finalización de la importación según corresponda. Pendiente y guardando no implican confirmación del servidor. |
| `sin-conexion` | La lista advierte que los datos están desactualizados; el Taller conserva el trabajo local de la misma cuenta, deshabilita Guardar ahora y ofrece reconectar; importación deshabilitada con el original preservado. |
| `conflicto` | Taller: pliegue de conflicto persistente con dos opciones, escena local conservada y guardado normal detenido. |
| `validacion` | Aviso de error del Taller más la escena nativa Nombre: nombre vacío, asociación del campo y error en línea recuperable. |
| `sin-permiso`, `sesion-caducada` | Todas las vistas ocultan el contenido del proyecto y explican cómo volver a la propia lista o iniciar sesión de nuevo con la misma cuenta; los diálogos permanecen cerrados. |
| `parcial` | La lista conserva las filas y reintenta la página siguiente. El Taller describe una confirmación anterior con ediciones más recientes pendientes. |
| `incompatible`, `importado` | Falla exclusiva de importación con ejemplo de descarga en bruto, o éxito confirmado con el original conservado y la acción Abrir proyecto. |
| `sin-taller` | La consulta no tiene herramientas de edición ni copia habilitada; la importación se deniega; la acción de nuevo proyecto está deshabilitada. |

Opciones de Diálogo: Ninguno, Nombre / guardar copia (`nombre`), Salir con cambios (`salir`), Cargar versión guardada (`servidor`). Usan primitivas modales reales con títulos/descripciones accesibles, fondo inerte y contención del foco. Escape cierra el Dialog de guardado ordinario y devuelve el foco a quien lo invocó; también está disponible un Cancelar explícito. AlertDialog se usa para el posible reemplazo de una escena abierta y para abandonar trabajo pendiente. Sus fixtures no son verificaciones de autorización de la cuenta.

## Reflujo, accesibilidad y objetivos de revisión

- **360–767 px:** relleno de 20 px en el shell y los paneles; acciones del encabezado apiladas; muestra de 96 px junto al nombre de carpeta con salto de línea; la acción de apertura pasa debajo y ocupa el ancho disponible. Las opciones de folio, importación y conflicto pasan a una sola columna. Las acciones modales se apilan; el ancho del modal está limitado por márgenes laterales de 20 px y su contenido se desplaza verticalmente cuando es necesario.
- **768–1023 px:** relleno de 24 px en el shell; muestra de carpeta de 150 px; la acción de apertura queda bajo el texto de la carpeta; la nota del folio mide 260 px. Sin control oculto de filtro por propietario ni acción que dependa solo de gestos.
- **1024 px en adelante:** ancho máximo del shell de 1160 px incluyendo 32 px de relleno lateral; muestra de carpeta de 200 px, título flexible, acción al final; nota de vinculación del folio de 300 px. El encabezado, el contenido y el pie comparten el mismo eje exterior.
- **Objetivos:** WCAG 2.2 AA: texto 4.5:1, texto grande 3:1 y bordes visibles de controles/foco 3:1; acciones de 44 px; entradas/selectores con etiqueta, información de guardado/reintento en vivo, propiedad explícita y copia de solo lectura, alternativas de teclado al arrastre, selectores nativos y paridad con movimiento reducido. Se ejercitó el comportamiento real del teclado en los modales. La evidencia automatizada no certifica la conformidad total con WCAG ni la semántica con lectores de pantalla o en producción.

| Criterio de dirección | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-01 | 1024+ | lista normal | Una pestaña de fecha se proyecta sobre cada carpeta horizontal; el nombre, el propietario y la acción de apertura pertenecen a la misma carpeta. |
| C-02 | 360–767 | lista normal | La acción de apertura queda debajo de la muestra/nombre, sin desplazamiento horizontal de la página. |
| C-03 | 360+ | carga | La lista muestra filas skeleton estables en lugar de un spinner aislado. |
| C-04 | 360+ | vacío/error | La explicación, la recuperación y el contenido de soporte se mantienen en el eje izquierdo de la página. |
| C-05 | 360+ | conflicto | La explicación del conflicto y las dos alternativas etiquetadas aparecen antes del folio abierto; Guardar ahora está deshabilitado. |
| C-06 | 360+ | ajeno/sin-taller | Se ven el propietario del original y la explicación de solo lectura; no hay herramientas de movimiento y la copia está deshabilitada sin Taller. |
| C-07 | 360+ | importación incompatible | Se ven la explicación de preservación del original y la acción de descarga del ejemplo; no se muestra ninguna acción Importar habilitada. |
| C-08 | 360+ | diálogo de validación | El campo de nombre expone su error en línea, el foco del teclado permanece en el modal y Cancelar es alcanzable. |
| C-09 | 360+ | expresivo/reducido | Las carpetas y pestañas se animan en modo expresivo; el modo reducido/estático muestra el contenido final y conserva todas las acciones. |
| C-10 | 360+ | ambos temas | Los bordes de entradas, acciones con contorno y foco siguen siendo visibles sobre sus superficies reales. |

## Verificación y límites honestos

Estado de las herramientas: instaladas y compiladas, **96/96 entradas disponibles**. Compilado con el comando `components mockup build` con ruta absoluta, desde el TSX de esta dirección hacia el HTML de esta dirección: **568 KB, 2135 archivos fuente empaquetados, sin conexión**, código de salida 0. Sin instalación de paquetes ni recursos descargados.

`contrast.py proyectos@v1.r8.dir-c.html`: **158 pares verificados en claro y oscuro, todos aprueban**, código de salida 0.

La primera auditoría renderizada encontró variantes incorrectas del botón primario y problemas de alineación en torno a los estados vacíos centrados y a una línea final del alcance de la cuenta. Atributos de variante reales, contenido de estado vacío coherente alineado a la izquierda y una línea de alcance alineada corrigieron las causas. Posteriormente, una prueba renderizada enfocada de 12 ejemplos no encontró hallazgos de contraste, elementos no textuales, alineación, relleno ni desbordamiento. La siguiente auditoría completa conservó ocho hallazgos de alineación en alertas de teléfono: su ícono dejaba el texto en una franja central estrecha. Ahora los avisos en teléfono apilan el ícono sobre el texto de ancho completo. La inspección de capturas de pantalla también expuso un fixture de error de lista que reportaba filas ocultas como visibles; ahora el conteo indica correctamente cero y no aparece ninguna acción de página siguiente. Una auditoría intermedia se interrumpió intencionalmente antes de completarse para incluir esa corrección; no es un resultado aprobado. La prueba final enfocada de errores en teléfono aprobó las cinco categorías visuales medidas y las aserciones de conteo/reintento. Otros seis hallazgos de alineación identificaron relleno duplicado en los avisos de importación anidados dentro del folio. Esos avisos ahora son franjas planas con regla, alineadas con el formulario de importación, en lugar de otra tarjeta con marco. Un barrido suplementario completo de **320 ejemplos de vista/estado/tema/ancho encontró cero hallazgos de contraste, elementos no textuales, alineación, relleno ni desbordamiento** antes de la auditoría final completa de teclado.

Auditoría final de la salida exacta: **380 renders / 380 combinaciones planificadas**, **8,788 mediciones de texto**, **618 paradas de foco**, código de salida 0. Se renderizaron ambos temas y todas las combinaciones de vista/estado, además de cada diálogo, a 1280/390 px.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

SHA-256 del HTML auditado: `027271537e5df104e1268c5aab386875fa9885eef22125986ea1203f084e9a6b`.

Prueba de humo adicional con Playwright: **APROBADA** para búsqueda, búsqueda vacía, paginación, filtrado por propietario, solo lectura de elementos ajenos, fixture de permisos sin Taller, Escape en el Dialog y retorno del foco, confirmación de conflicto y recuperación del borrador local, validación del nombre en el primer guardado, autoguardado simulado, importación explícita y recuperación ante datos incompatibles. No se observaron errores del navegador ni solicitudes HTTP(S). Tras las correcciones visuales, una prueba responsiva verificó **30 combinaciones a 360/768/1024 px**, ambos temas, en lista, lista parcial de personal, conflicto, consulta sin Taller e importación incompatible: sin desbordamiento horizontal de la página. Todos los selectores de ejes coincidieron con elementos renderizados; se observaron keyframes expresivos y `?still=1` reportó cero animaciones en ejecución.

Las capturas de pantalla renderizadas se inspeccionaron en memoria a 1280/claro, 390/oscuro, conflicto 1280/oscuro e importación incompatible 390/claro, y luego el error final en teléfono y el Dialog de validación del nombre. No son archivos de salida adicionales. Este artefacto de diseño no certifica pruebas en producción, persistencia en servidor, permisos reales, restauración entre navegadores, pruebas con lectores de pantalla, fidelidad de Blender/3D, concurrencia de API, importación de fuente sin procesar ni búsqueda en servidor de más de 50 filas.

## Impacto, preguntas y próxima decisión del responsable

Los consumidores de SP-4 siguen siendo `proyectos@v1`: T4.1 copia el contrato aprobado posterior; T4.4 consume la UI de lista/guardado/consulta/conflicto; T4.5 consume la importación; T4.8 revisa el renderizado; T4.6/T4.7 verifican la integración real en el navegador y T4.9 audita el aislamiento/la concurrencia. El comportamiento sigue vinculado a R6/R7. **Clasificación de compatibilidad: indeterminada hasta que se seleccione y finalice una dirección.** Si se selecciona, la composición de carpetas, el folio y todas las expectativas de reflujo/foco/movimiento indicadas deben incorporarse al contrato canónico y a su revisión visual. Ningún consumidor es redirigido por estos archivos.

P: ¿Debe la lista mostrar una vista previa derivada de la escena cuando haya una fuente autorizada disponible, o una muestra de material neutral hasta entonces? Esta exploración no autoriza ningún campo de miniatura persistido, carga adicional de escenas ni una costosa obtención de escena por fila; las ilustraciones de muestra actuales son datos simulados. Responsable de la decisión: David con el Planner para el límite de datos.

No se reabren las decisiones confirmadas: primer guardado con nombre, autoguardado posterior, portabilidad completa de la escena, originales ajenos de solo lectura, permiso de Taller para copias propias, detención/preservación ante conflicto, borradores por cuenta e importación explícita sin pérdida e idempotente. La selección de la dirección y la finalización canónica siguen pendientes de revisión por el responsable. Esta tarea no concede ninguna aprobación.
