# Pliego — archivo de montaje

Estado: **exploración de borrador**, no es el contrato canónico proyectos@v1 ni está aprobado para implementación. Revisión: r10 / dirección A. Fuentes: PLAN.json revisión 1 y resumen compartido de SP-4 749be52ec4afc053. Subplan SP-4, R6/R7. Fecha: 2026-10-27. El propietario decide la dirección; el alcance del Designer se limita a esta exploración.

## Concepto y recurso memorable

La metáfora de trabajo es un registro de montaje plegado. Un proyecto es el montaje completo del decorador, con su propietario y estado de guardado asociados. El recurso memorable es un **registro que se despliega en el lugar**: al seleccionar el nombre de un proyecto, se abre una lámina de escena y una ficha precisa del contenido dentro de esa fila. Abrir el proyecto real sigue siendo una acción con nombre propio. Las costuras de papel metalizado, el látex naranja y la pequeña marca de globo conservan la identidad de Pictures/Sempertex sin añadir un panel decorativo.

Esta es la postura operativa/editorial: nombres densos, metadatos del propietario, marcas de tiempo y revisiones; un sustantivo serif de escala asimétrica; secuencias laterales y de plegado precisas. El riesgo se concentra en la tipografía editorial, la lógica de material frío/naranja de señalización y el movimiento de plegado/registro. Los controles siguen siendo familiares y legibles. No es una opción predeterminada segura de SaaS: no hay tratamiento casi blanco y morado, cuadrícula uniforme de tarjetas, métricas ornamentales, ilustración genérica destacada ni una pila repetitiva de elementos que aparecen con desvanecimiento desde abajo.

## Dos miniaturas y luego selección

- Candidato 1: `proyectos@v1.r10.dir-a.html.candidate-1.html`. Una colección reglada e indexada por fecha, con un pliegue integrado para la escena/especificación. **Elegido** porque el contexto de la escena permanece asociado a su propietario y fila, y el pliegue tiene un propósito directo de recuperación de información.
- Candidato 2: `proyectos@v1.r10.dir-a.html.candidate-2.html`. Un índice de archivador en dos columnas junto a una escena destacada permanente. Rechazado porque la vista previa destacada permanente compite con la colección completa y repite la composición estática de inspector ya explorada en otros subplanes.

Ambos candidatos se crearon antes del TSX completo; son composiciones pequeñas, no listas de direcciones compuestas solo por texto. Sus objetos generales son estudios visuales, no prototipos de interacción.

## Registro visual e identidad compartida

Lee la fuente de comportamiento compartida r10, la ronda 9 de SPEC, PLAN/PLAN.json SP-4 y las notas actuales de cuentas-admin r10 A/B/C y taller-esenciales r9 A/B/C. Las direcciones de cuentas ya usan una hoja de ruta operativa cobalto, una puerta inflable azul/amarilla y nudos elásticos color petróleo. Taller explora dibujos medidos en rojo de registro, paletas escénicas orbitales y bandejas moldeadas color frambuesa. Pliego usa una jerarquía serif/mono distinta, un índice izquierdo estrecho, un pliegue de registro en el lugar y una importación tipo comprobante de origen, en vez de la regla superior de rutas, la navegación orbital, el cinturón de herramientas inferior o el riel de identidad del 38 % de aquellas propuestas. Un dibujo de escena y la marca de globo son objetos compartidos intencionalmente del producto; la composición y la navegación son nuevas.

## Tabla de diseño de ocho ejes

| Eje | Decisión observable |
|---|---|
| concepto | Registro de montaje plegado de un decorador: volver a abrir el montaje completo con globos, no una miniatura separada de su propiedad y estado de guardado. Las costuras de papel metalizado y un registro de producción reglado conectan la información de trabajo con los materiales de Sempertex. |
| diseño | Un índice estrecho de 154px junto a un registro amplio y continuo. Un sustantivo serif grande ancla la parte superior izquierda; la fila seleccionada se despliega en el lugar como una lámina de escena y una ficha de contenido en dos columnas. Taller usa una escena amplia y un inventario estrecho; la importación del navegador es un comprobante de origen junto al consentimiento. A 760px, el índice se convierte en tres estaciones en el flujo y los metadatos del registro se reordenan debajo del nombre. |
| navegación | Índice vertical dentro del flujo a la izquierda: Archivo / En el Taller / Del navegador; cambia a una franja de tres estaciones en el teléfono. Los nombres de proyectos despliegan el contexto; botones independientes Abrir/Consultar llevan al editor del propietario o a la vista ajena de solo lectura. Sin cinturón fijo inferior, paletas orbitales, carrusel ni inspector destacado permanente. |
| tipografía | DejaVu Serif Condensed Regular local integrada como Archive, en 57–84px para el sustantivo editorial y 25–36px para los encabezados de contenido. Adwaita Sans integrada como Work, en 13–19px, muestra los nombres reales de proyectos y controles; Liberation Mono integrada como Measure, en 11–14px, registra fechas y revisiones. La tipografía grafito permanece completamente opaca durante el movimiento. |
| densidad | Filas compactas de metadatos regladas de 108px, primer registro ampliado intencionalmente, esquinas cuadradas de 2px en los controles y sin cuadrícula de tarjetas de proyectos. Margen interior principal de escritorio de 38px y de teléfono de 20px; el comprobante de origen tiene márgenes de 26/22px y el modal de 28/24px. Las acciones cumplen un mínimo de 44px y muestran juntos los nombres reales, propietarios, marcas de tiempo y revisiones. |
| componentes | Button, Input y Skeleton reales instalados de shadcn/Base UI; Dialog y AlertDialog de Animate UI Base UI instalados, con cancelación explícita y gestión del foco. Lámina de escena SVG integrada personalizada, registros de proyecto reglados, comprobante de origen plegado, costura de papel metalizado y casilla de consentimiento nativa con apariencia marcada/sin marcar diseñada para ambos temas. Sin kit alternativo HTML. |
| color | Propuesta de asignación de roles semánticos de Pictures: tonos fríos #e8eceb y #f8faf9, grafito #202c2b, naranja de señalización #a43800 para la acción principal. Tonos oscuros verde perenne #192522/#24332e, tinta clara #f2f6f4 y acciones naranja melocotón #ffb386. El papel metalizado plateado y el látex naranja pertenecen al montaje ilustrativo. Los tokens morados de producción son de solo lectura y no se modifican. |
| movimiento | Gramática mecánica de pliegue/registro: cubic-bezier(.86,0,.14,1), registro expresivo de 640ms, desfases de fila de 45ms y controles de 180ms; composición tipográfica del título, secuenciación lateral de registros, despliegue en perspectiva, elevación de la lámina, registro de tabla, ajuste del látex, deriva escalonada de siete segundos del papel metalizado, extensión de regla, sello de confirmación, alineación del comprobante de origen, asentamiento del contorno vacío, rotación del guardado y registro durante el desplazamiento. Natural: 420/150ms; sutil: 220/120ms. Movimiento reducido/estático elimina desplazamientos, bucles y transiciones; la suspensión fuera de pantalla/oculta se aplica al papel metalizado ambiental. |

## Sistema de origen e inventario de componentes reales

Ambos repositorios de solo lectura exponen tokens semánticos de Pictures en `src/app/globals.css`, con `--fondo`, `--superficie`, `--texto`, `--texto-suave`, `--borde`, `--acento`, `--sobre-acento` y los alias existentes de shadcn. La exploración asigna esos **mismos roles** a una paleta propuesta, una vez por tema; no se edita ningún token de producción ni repositorio. El morado existente no se considera una restricción aprobada para la exploración, de acuerdo con las indicaciones explícitas del propietario. La implementación futura requiere que el propietario seleccione esta propuesta.

| Rol del proyecto | Rol del kit | Claro | Oscuro |
|---|---|---|---|
| fondo | fondo | #e8eceb | #192522 |
| superficie | tarjeta / ventana emergente | #f8faf9 | #24332e |
| superficie-2 | atenuado / secundario / acento | #dce2df | #31443c |
| texto | primer plano | #202c2b | #f2f6f4 |
| texto-suave | primer plano atenuado | #485c56 | #c1d2c9 |
| borde | entrada / borde | #71827b | #91a89b |
| acento | principal / anillo | #a43800 | #ffb386 |
| sobre-acento | primer plano principal | #ffffff | #302016 |

Componentes reales instalados: `shadcn:button` (principal/secundario/simple, normal/deshabilitado), `shadcn:input` (predeterminado/validación/deshabilitado), `shadcn:skeleton` (carga) y Dialog/AlertDialog de Base UI instalados de Animate UI mediante `@/components/ui/dialog` y `@/components/ui/alert-dialog`. Las importaciones y el montaje usan `@kit/mockup` y `@kit/motion`. Piezas personalizadas: filas de registro, lámina de escena plegable, montaje SVG, comprobante de origen, reglas de movimiento y casilla de consentimiento nativa. Sin alternativa de fragmentos HTML ni descarga de paquetes o recursos. DejaVu Serif Condensed, Adwaita Sans y Liberation Mono locales se integran como URI de datos. Lucide proporciona iconos de trazo uniforme. El archivo independiente incluye el CSS exacto diseñado en el encabezado y también como estilo de ejecución, para que las verificaciones de tokens y del navegador inspeccionen la misma paleta.

## Vistas, navegación y comportamientos conservados

| Vista / selector nativo | Estructura y resultado principal |
|---|---|
| Archivo de proyectos / lista | Búsqueda por nombre; colección propia/todas y filtro de propietario autorizado; registros con nombre, propietario, fecha/hora, revisión y acción para abrir/consultar; pliegue integrado; cargar más; entrada para recuperar importaciones del navegador. El conjunto de prueba predeterminado es la colección propia de la empleada Marina. Las filas ajenas aparecen en Todos los proyectos y llevan a Consulta. |
| Taller / taller | Proyecto personal con nombre, primer guardado con nombre explícito, cambio de nombre, estado visible guardado/guardando/pendiente/sin conexión/conflicto y Guardar ahora; escena amplia con el contenido completo del documento; salida protegida ante trabajo pendiente. Los controles de escena son interacciones ilustrativas acotadas, no un reemplazo del diseño de SP-3. |
| Consulta ajena / consulta | Se nombra al propietario antes de la escena; explicación explícita de Solo lectura; sin controles de edición. Guardar una copia propia requiere taller.usar. El estado sin-taller oculta esa acción y explica el acceso exclusivo de consulta, en concordancia con /proyectos/[id]. |
| Importar del navegador / importar | Comprobante de origen, cuenta de destino actual, advertencia sobre dispositivo compartido, nombre editable y consentimiento explícito sin marcar. Importar solo tras la confirmación; Ahora no vuelve a la colección y deja una entrada recuperable. Los datos no admitidos reciben una explicación y una descarga de los datos sin procesar en vez de un proyecto vacío. |

Los selectores de planificación conservan los ids nativos `view`, `state`, `scene`, `theme`, las etiquetas en español Vista/Estado/Diálogo/Tema y la etiqueta visible Mockup; Movimiento comienza en modo expresivo salvo que se solicite movimiento reducido. Se pueden inspeccionar por separado cuatro escenas de diálogo: asignar nombre/copiar, conflicto de versiones, confirmar la carga de la versión guardada y salir con cambios pendientes. Los selectores nativos de la plantilla permanecen fuera del producto.

La fuente de verdad funcional no cambia: /proyectos lista metadatos autorizados por el servidor, la edición propia abre /3d?proyecto=<uuid> y la consulta ajena abre /proyectos/[id]. El primer guardado solicita un nombre explícitamente; las ediciones posteriores se guardan automáticamente con el debounce serializado de 500ms del Planner. Guardar ahora siempre se identifica claramente. Las respuestas confirman solo la generación enviada; las finalizaciones obsoletas no pueden marcar como guardado un trabajo posterior. La búsqueda y los filtros de propietario autorizado se aplican a **toda la colección del servidor antes de la paginación**, restablecen los cursores cuando cambian y rechazan respuestas obsoletas; un error al cargar la página siguiente conserva las filas visibles y permite reintentar. La demo estática filtra localmente sus datos de prueba finitos y agrega una fila de ejemplo para la página siguiente. No afirma demostrar la consulta al servidor, la autorización ni la implementación de cursores.

Ante un 409, el guardado se detiene y los cambios locales se conservan. El diálogo de conflicto ofrece guardar una copia propia o cargar la versión del servidor; la carga requiere confirmación mediante AlertDialog y conserva un borrador de recuperación. La salida con cambios pendientes ofrece guardar/continuar, conservar un borrador local con espacio de nombres/salir o cancelar. Sin conexión/conflicto impiden guardar/continuar. En producción, el cambio de proyecto o cuenta debe borrar la identidad de escena/conversación y las cachés; otra cuenta nunca debe ver borradores anteriores. La memoria de datos de prueba del mockup es efímera y no incluye autenticación ni persistencia real.

Solo el nombre y la escena completa de project-document@1 viajan entre navegadores: sala, entorno, salón, materiales, relaciones entre nodos y referencias. La conversación con IA y las imágenes generadas permanecen en el navegador. No se añade ninguna interfaz para eliminar, transferir propiedad ni consultar el historial de versiones. La revisión mostrada en la lista es un metadato, no un navegador del historial.

La importación heredada sigue siendo explícita para la cuenta actual, durante la primera visita autenticada permitida a Taller. La validación del servidor y la deduplicación por cuenta más hash del origen original evitan duplicados tras perder una respuesta, reintentos, recargas o dos pestañas. La clave heredada permanece sin cambios; los comprobantes independientes se generan tras la confirmación del servidor. La descarga de ejemplo se identifica claramente como un **original del conjunto de prueba**, no como un archivo del navegador de una persona real. Esta exploración no lee, carga ni elimina datos de origen.

## Acceso a estados

Todos los estados se pueden seleccionar en el control nativo Estado; su pertinencia depende del contexto. Un estado que no corresponda a una vista deja esa vista en su forma normal en vez de inventar un comportamiento nuevo del producto.

| Estado nativo | Representación aplicable y recuperación |
|---|---|
| normal | Lista activa, editor propio, consulta ajena o consentimiento de importación sin marcar. |
| cargando | Esqueleto de lista, escena o importación; envío y acciones duplicadas deshabilitados. |
| vacio | Sin proyectos/sin coincidencias de búsqueda; escena vacía; sin fuente local. Cada caso ofrece un siguiente paso con nombre. |
| error | Fallo al cargar la primera página, abrir un proyecto o importar; se conservan originales/borradores; reintentar o descargar. La escena para asignar nombre también muestra una explicación del fallo al guardar. |
| guardado | Conjunto de prueba con guardado confirmado; comprobante en la lista; comprobante de importación y apertura del proyecto importado. |
| guardando | Estado de guardado propio y envío repetido deshabilitado; envío de importación deshabilitado. |
| pendiente | Estado de guardado propio y acción Guardar ahora; protección de navegación. |
| sin-conexion | Aviso de borrador local propio, reintento de guardado sin etiqueta falsa de guardado; fallo de importación con la fuente conservada. |
| conflicto | Estado de autoguardado propio detenido; resolución, copia y carga confirmada del servidor. |
| sin-permiso | Sin escena ni metadatos del proyecto; volver a la colección propia. |
| sesion | Sin contenido de escena; explicación para recuperar el acceso mediante inicio de sesión en la misma cuenta. |
| incompatible | Explicación de conservación del original y descarga del conjunto de prueba; importación deshabilitada. |
| validacion | Error del diálogo para asignar nombre y validación del nombre/consentimiento sin marcar de la importación. |
| error-pagina | La colección existente permanece visible; reintentar la página siguiente. |
| sin-taller | La consulta funciona; no aparecen las acciones de edición ni de guardar una copia propia. |

Ningún estado seleccionado implica que el HTML estático aplique controles de seguridad o persistencia. La lista de producción de una cuenta normal debe omitir el alcance de personal y los filtros de propietario; el conjunto de prueba de colección proporcionado corresponde explícitamente a un empleado con esos permisos. No se introducen permisos nuevos.

## Objetivos de diseño adaptable y accesibilidad

Por encima de 1100px: índice de 154px, margen interior principal de 38px, fila de cinco partes y pliegue de dos columnas. De 761–1100px: índice de 130px, margen interior de 28px, la revisión es metadato complementario y puede omitirse de la fila compacta; el nombre del filtro ocupa la primera línea. En ≤760px: navegación de tres estaciones integrada al flujo, márgenes exteriores de 20px, título de presentación de 57px, metadatos y acción Abrir debajo del nombre; pliegue de escena/especificación, editor e importación apilados. Sin desplazamiento horizontal de página ni dependencia de gestos. Los diálogos usan límites relativos al viewport y desbordamiento interno; la cancelación sigue siendo accesible. Las pantallas también deben admitir nombres largos de proyectos localizados; la traducción completa al inglés corresponde a los subplanes de idioma posteriores y no se afirma como completa aquí.

Objetivos: contraste de texto WCAG 2.2 AA ≥4.5:1, contraste de controles/foco ≥3:1, foco visible de 3px con desplazamiento de 4px, etiquetas semánticas y estado actual de navegación, funcionamiento nativo de búsqueda/selección/casilla de verificación, nombres aria-expanded, confirmaciones de guardado corteses y recuperación ante errores de alerta. Los botones tienen al menos 44px de alto. Base UI se encarga de la inactividad modal y la contención del foco; las comprobaciones manuales deben verificar el cierre y la devolución del foco. La confirmación usa AlertDialog. La representación de la casilla de verificación está definida en ambos temas, incluida la marca de selección, para evitar bordes invisibles que dependan del navegador. La escena es un SVG ilustrativo con etiqueta; todas las cantidades también aparecen como texto.

El movimiento permanece completamente opaco: las transformaciones no hacen que el texto se desvanezca durante fotogramas intermedios ilegibles. Se implementan seis o más comportamientos distintos, no solo se describen: registro del título, secuencia lateral de filas, pliegue en perspectiva, elevación de la placa de escena, registro de la tabla, asentamiento del látex, deriva del foil, extensión de la costura discontinua, estampado de estado, enderezamiento del comprobante de origen, asentamiento del contorno vacío, rotación de guardado y línea de posición de desplazamiento. Los tokens de perfil CSS controlan secuencias de 640/420/220ms e interacciones de 180/150/120ms. El movimiento ambiental del foil se pausa cuando el documento está oculto y su dibujo queda fuera de pantalla. El movimiento reducido del sistema operativo, Quieto y ?still=1 eliminan las animaciones/transiciones, pero mantienen intactos el contenido final, el foco y las acciones.

## Comprobaciones de diseño observables si se elige esta dirección

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1280px | normal/lista | Un índice angosto a la izquierda precede al registro continuo; el primer proyecto se despliega dentro de su propia fila. |
| A-02 | 390px | normal/lista | La navegación, los filtros, el propietario y la acción Abrir permanecen dentro del viewport; el dibujo precede a su inventario de texto. |
| A-03 | 390/1280px | error-pagina/lista | Las filas visibles permanecen y Reintentar siguiente página está disponible. |
| A-04 | 390/1280px | conflicto/taller | Autoguardado detenido está visible y Guardar ahora está deshabilitado; la resolución muestra las dos opciones. |
| A-05 | 390/1280px | sin-conexion/taller | El estado identifica el trabajo como borrador local, sin afirmar que se guardó en la cuenta. |
| A-06 | 390/1280px | normal/consulta | El propietario y Solo lectura aparecen antes de la escena; no se muestra ningún control de edición. |
| A-07 | 390/1280px | sin-taller/consulta | Guardar copia está ausente y se explica que el acceso es solo de consulta. |
| A-08 | 390/1280px | normal/importar | El destino Marina Solano y la advertencia sobre dispositivos compartidos aparecen antes del consentimiento sin marcar; la importación está deshabilitada hasta proporcionar el nombre y el consentimiento. |
| A-09 | 390/1280px | incompatible/importar | La descarga original está disponible y la importación está deshabilitada; ninguna escena vacía sustituye los datos no válidos. |
| A-10 | 390/1280px | cargar dialog | Una confirmación independiente indica el reemplazo de la escena y la preservación del borrador local; Cancelar sigue siendo accesible. |
| A-11 | 390/1280px | dark/all | Los límites de campos/casillas nativos, el texto del cuerpo y el foco del teclado se distinguen visiblemente. |
| A-12 | 390/1280px | reduced/all | Todas las vistas muestran el contenido final de inmediato; no queda ninguna animación de entrada finita en curso ni ningún ciclo ambiental. |

## Evidencia de verificación

- Generador sin conexión con bibliotecas reales: código de salida 0, 2,596 KB antes de reflejar el CSS escrito en el proyecto, 2,135 archivos de origen empaquetados; sin instalación ni descarga de recursos. El HTML independiente final exacto tiene 4,741,676 bytes. Entrada: `proyectos@v1.r10.dir-a.tsx`; salida: `proyectos@v1.r10.dir-a.html`.
- `python3 .../kit/contrast.py proyectos@v1.r10.dir-a.html`: **contraste: se comprobaron 158 pares en modo claro y oscuro; todos pasan**, código de salida 0. La paleta definida está presente en el CSS del encabezado, así que estas mediciones usan los valores de roles de esta dirección.
- `UV_OFFLINE=1 uv run --offline --with playwright python .../kit/audit_mockup.py proyectos@v1.r10.dir-a.html --max-combos 304`: **304 representaciones / 304 previstas**, 11,100 mediciones de texto, 598 paradas de foco de teclado; 1280px y 390px, ambos temas, las cuatro vistas, los quince estados y las cuatro escenas de diálogo; código de salida 0. No se omitió ninguna combinación por muestreo.
- **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- `compare_directions.py` sobre los HTML A/B/C actuales de r10 con `--json`: código de salida 0, `ok: true`, `evidence_ok: true`, sin selectores faltantes. Similitud de diseño A/B .007; A/C .003; B/C .050. Todos los pares difieren en tipografía, navegación y movimiento medidos. El resultado verifica una distinción medible, no la preferencia ni la aprobación del propietario.
- **RESULTADO DE INTERACCIÓN: APROBADO — 12 comprobaciones**: borrador sin nombre, validación del nombre, primer guardado explícito, salida pendiente/cancelación, detención del conflicto/confirmación/borrador recuperable, separación de permisos de consulta/copia de terceros, comprobante de consentimiento/importación, fuente no compatible/descarga, filtrado/consulta del personal, reintento de la página siguiente que conserva las filas, edición/reintento sin conexión sin una etiqueta falsa de guardado y reorganización de todas las vistas en 360/390/768/1024/1280px con ambos temas. No se observaron errores de página ni solicitudes HTTP(S). Son interacciones de fixtures, no pruebas de persistencia/API.
- **EVIDENCIA DE MOVIMIENTO: 8 animaciones CSS distintas en curso** observadas simultáneamente: foil-register, type-register, record-register, unfold, plate-register, balloon-register, table-register y rule-register.
- **RESULTADO DE MOVIMIENTO/DIÁLOGO: APROBADO**: ?still=1 y ?rm=1 no tienen animaciones en curso después de 150ms; las 16 combinaciones de diálogo/tema/ancho permanecen dentro de los viewports de 390/1280px y contienen el foco del teclado una vez que se estabilizan las barreras de foco de Base UI. Si se deniega la consulta, se ocultan los metadatos del propietario externo. Una primera prueba del ciclo de foco consultó la barrera de forma sincrónica; esperar la devolución de foco programada confirmó la trampa de foco instalada, sin necesidad de una solución provisional en el código del producto.
- **RESULTADO DEL NOMBRE DE IMPORTACIÓN: APROBADO**: un nombre de importación personalizado se conserva en el comprobante y al abrir el proyecto importado.
- **COMPROBACIÓN DE TIPOS DE LA ENTRADA: APROBADA**: diagnósticos estrictos/noEmit en memoria para esta entrada, alias de dependencias instaladas y skipLibCheck. Esto no es una comprobación de tipos del espacio de trabajo de producción.
- La inspección visual usó capturas renderizadas en memoria, sin escribir archivos adicionales: archivo de escritorio en tema claro, archivo de teléfono en tema claro, importación en teléfono en tema oscuro y segmento de casilla marcada/acción/pie de página. El pie de página sigue el margen interior del formulario; la marca, el relleno y el borde de la casilla se distinguen en el modo oscuro. Las miniaturas originales se conservan como evidencia visual permitida.
- SHA-256 del HTML final: `0d1dce11f823c34eb9da3ebf29120d9b4a0b44f55026cf25a7becbc07cb80fa8`.

Registro de correcciones transparente: la primera auditoría por muestreo falló por un margen interior de navegación demasiado estrecho y una etiqueta de vista previa larga que causaba desbordamiento en el teléfono; se corrigieron ambos. La primera auditoría completa detectó casos de alineación del contenido de estado en el fixture de sesión finalizada; ampliar el aviso hasta ocupar toda la columna de trabajo resolvió el problema. Una prueba de navegación con clics también encontró que el remontaje del runtime del fixture perdía una fila añadida de la página siguiente; se corrigió la continuidad del fixture y ahora pasa su prueba de reintento. Todas las comprobaciones finales informadas arriba pasaron; los fallos anteriores no se presentan como aprobados.

No se ejecutó ni modificó código de producción, repositorios, base de datos, API, autenticación, importación real ni arnés de integración. La seguridad, el almacenamiento entre navegadores, la fidelidad del documento completo y la idempotencia siguen siendo requisitos de T4.2–T4.7 y del ciclo de aceptación independiente T4.8/T4.9.

## Decisiones pendientes y alcance

P: ¿El propietario elige el registro de existencias frías/naranja de Pliego, la tipografía serif de presentación y el pliegue en sitio para finalizar, o elige otra exploración? Esta es la única decisión de dirección pendiente; se conservan los comportamientos R6/R7 y las decisiones de la ronda 9, que no se vuelven a abrir.

Todas las personas, nombres de empresas/eventos, cantidades y fechas son ilustrativos. La preservación de la escena completa y de los datos sin procesar son requisitos de implementación; un SVG estático o la memoria de un fixture no los demuestran. La vista previa local no llama a las API de persistencia/autenticación, no valida esquemas de escena, no implementa el autoguardado real ni demuestra concurrencia entre navegadores. Aquí no se aprueba ningún contrato.

Impacto si se elige: T4.1 copia únicamente el artefacto canónico aprobado posteriormente por el propietario; T4.4 consume los diseños de lista/guardado/consulta/conflicto/salida pendiente; T4.5 consume los diseños de importación/datos no válidos/comprobante; T4.8 revisa la fidelidad renderizada. T4.2/T4.3 siguen siendo responsables de los datos y la API; T4.6/T4.7 verifican la persistencia real y la autorización. La compatibilidad queda **sin determinar hasta que el propietario elija y se finalice la versión canónica**. Esta dirección no puede reemplazar por sí sola una entrada de consumidor aprobada. No se modificó ningún contrato compartido, PLAN, repositorio ni otra dirección.
