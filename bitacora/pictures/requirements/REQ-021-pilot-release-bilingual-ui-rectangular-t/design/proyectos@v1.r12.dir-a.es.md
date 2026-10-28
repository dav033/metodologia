---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
direction: a
name: Registro operativo
source_revision: r12
source_behavior: proyectos@v1.r12.behavior.md
approval: pending-owner-selection-and-plan-approval
---

# Registro operativo — exploración A, r12

## 1. Identidad y trazabilidad

Esta es una exploración específica de la revisión **proyectos@v1**, no el contrato canónico ni un insumo de implementación aprobado. Cambia únicamente las superficies de proyectos guardados del producto existente. Elegir esta dirección no aprueba el plan. Esta delegación no escribe ningún contrato compartido, PLAN, fuente del repositorio, registro de cambios ni archivo de memoria del proyecto.

Autoridad de comportamiento: `proyectos@v1.r12.behavior.md` (SHA-256 `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65`), R6/R7 y SPEC “Comportamiento — SP-3 y SP-4 (ronda 9 respondida)”. Los responsables de SPEC y PLAN siguen editándolos activamente; sus secciones de ingeniería no relacionadas no forman parte del alcance de diseño. Instantánea de las fuentes al momento de la inspección: SPEC `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d`; PLAN.json `b19d26e25d207f059fe4d83c2234f0d868305d43f0608749283b2ef8cf169cc3`.

Fuentes de producto de solo lectura inspeccionadas en t12 y asesor: `src/app/globals.css`, `layout.tsx`, `3d/page.tsx`, `Taller3D.tsx`, `guardado-escena.ts`, `guardado-conversacion.ts`, `imagenes-guardadas.ts`, `Biblioteca.tsx`, `CabeceraApp.tsx` y `/api/decoraciones`. Esta última es la biblioteca de decoraciones, no el almacenamiento de proyectos. La aplicación existente permite guardar en el navegador, incluye un nombre de escena en línea y una etiqueta de estado de guardado; las listas vinculadas a cuentas, el manejo de conflictos y la importación heredada son las adiciones dentro del alcance. Se mantienen por separado el almacenamiento de conversaciones de IA y de imágenes, ambos solo en el navegador.

Autoridad del marco compartido: borradores finales de los proyectos hermanos `cuentas-admin@v1.md/.html` y `planes@v1.md/.html`. Se conservan su marca compacta de anillo y punto de Pictures/Sempertex, tipografía Geist, navegación horizontal neutra, superficies con esquinas redondeadas, acciones en forma de píldora y divulgación de cuenta. El informe más reciente reemplaza explícitamente los comentarios anteriores que pedían paletas y tipografías separadas; esas directrices históricas no se reutilizan. No se introduce ninguna marca, tipografía ni paleta nueva.

Consumidores afectados si el responsable elige y aprueba esta dirección más adelante: texto de diseño de SP-4 T4.1, implementación de UI T4.4/T4.5 y revisión visual T4.8. La compatibilidad con el diseño exploratorio anterior no aprobado se clasifica como **ajuste visual compatible respecto a r11**: se mantienen el registro existente, el marco compartido, la navegación, los estados y los flujos; el relleno de filas en escritorio se reduce de 24px a 16px, los nombres de proyectos pasan de 17px a 16px y los cortes rápidos de ruta y búsqueda se incorporan a la gramática de movimiento conservada. Las exploraciones anteriores de barra lateral y archivo siguen siendo históricas. Esta clasificación no aprueba una implementación ni redirige a ningún consumidor. Se conservan la semántica de R6/R7 y el comportamiento de la ronda 9. Ningún otro subplan se redirige ni se aprueba de forma implícita.

## 2. Propósito y usuarios

El propietario responde «¿Qué escena guardada quiero continuar?». El personal también puede encontrar el proyecto de un propietario autorizado e inspeccionarlo sin modificar el original. En Taller, el nombre y el estado real del guardado se leen juntos. Al iniciar sesión por primera vez, un aviso pregunta si la escena heredada de este navegador pertenece a la cuenta actual; el consentimiento es explícito.

Todos los datos de ejemplo son neutros y están claramente marcados como Mockup: Mesa rectangular, Arco, Backing, Columna y Guirnalda con «· ejemplo»; Cuenta de ejemplo y Otra cuenta de ejemplo; `cuenta@prueba.local`. No hay identidades de clientes inventadas, fechas de eventos, eslóganes promocionales ni historial. Los recuentos se derivan de la lista en memoria. Los proyectos guardados durante la interacción con el mockup se agregan a esa misma lista. Al actualizar el HTML se restablecen todas las operaciones; no se accede al localStorage de la aplicación, IndexedDB, cuentas ni servicios remotos.

## 3. Enfoque, composición y miniatura elegida

Primero se dibujaron dos composiciones pequeñas en HTML. **Se elige la candidata 1:** un único registro continuo con líneas, búsqueda y propietario en una barra compartida y una acción Abrir inmediata en cada fila. La **candidata 2** exploró una división entre lista y detalle; dedica mucho espacio a una vista previa y agrega un paso de selección antes de abrir, por lo que resulta menos adecuada para este enfoque operativo. Ambas miniaturas permanecen como evidencia inmutable en las rutas asignadas a r12.

La composición elegida cambia el producto solo donde los proyectos guardados necesitan una nueva superficie. Mantiene el encabezado principal de los proyectos hermanos, el encabezado de página de 24px, la regla neutra de rutas Proyectos/Taller y el pie alineado. En escritorio, nombre, propietario, estado y Abrir comparten una línea base; en teléfonos, las filas apilan el nombre sobre el propietario y el estado, con Abrir al lado. No se agregan cuadrículas de tarjetas, cronologías del historial de proyectos, franjas promocionales ni acciones para eliminar o transferir.

Taller conserva la estructura existente del editor: nombre de escena editable en línea y estado en la barra de herramientas superior, carril de paneles, lienzo de escena, inspector de escena/IA y el contexto existente de fotos/lista de compras. Se agregan el control de guardado, la navegación de cuenta/proyecto y los avisos persistentes de conflicto/sin conexión. La ilustración y los elementos simplificados existentes de las herramientas aportan contexto; no rediseñan ni reemplazan el renderizador/editor de producción.

La importación aparece como una solicitud en el primer inicio de sesión, encima de la lista de proyectos; no es una nueva página /import ni una ruta permanente del producto. La cuenta que recibirá la escena es visible antes de otorgar el consentimiento. El selector de acceso del Mockup es solo un recurso de inspección, nunca una configuración del producto que otorgue permisos al personal.

### Tabla de ocho ejes

| Eje | Expresión representada |
|---|---|
| concepto | Registro operativo de proyectos: comparar nombres de escenas guardadas, propietarios y estados reales de guardado; abrir una fila directamente. |
| diseño | El encabezado fijo de Pictures/Sempertex y la regla horizontal neutra de rutas preceden a un único registro continuo de ancho completo. Nombre, propietario, estado y Abrir comparten una fila en escritorio. Sin barra lateral de vista previa; Taller conserva la barra de herramientas/carril/lienzo/inspector. |
| navegación | Apertura directa desde cada fila, búsqueda por nombre y selector de propietario autorizado en una barra de herramientas; divulgación nativa de cuenta y rutas Proyectos/Taller; confirmaciones contextuales para nombrar, copiar y salir/cargar. |
| tipografía | Solo la Geist Sans existente: H1 de 24px, título de sección de 20px, nombres de proyectos compactos seminegrita de 16px, acciones de 14px y metadatos de 12–13px. Geist Mono existente para los recuentos numéricos de escenas. |
| densidad | Una superficie única con esquinas redondeadas y márgenes internos de 28px, filas verticales de 16px en escritorio y espacios de 24px entre columnas. Las filas en teléfonos tienen márgenes internos/relleno vertical de 20px y agrupan propietario/Abrir en dos columnas; los controles miden al menos 44px de alto. |
| componentes | Button, Input y Skeleton reales de shadcn/Base UI instalados, y Dialog/AlertDialog de Animate UI; selectores/details nativos y una lista semántica personalizada con líneas. Radios y acciones en forma de píldora existentes de los proyectos hermanos, y marca de anillo y punto. |
| color | Paleta de Pictures en globals.css sin cambios en ambos temas: fondo/superficie/texto/acento; colores semánticos de éxito/aviso/error solo para estados reales. Los alias existentes de texto-tenue ofrecen bordes accesibles para controles; no se agrega ninguna paleta. |
| movimiento | Registro preciso de cortes rápidos: 360ms cubic-bezier(.77,0,.175,1), desfase escalonado de filas de 28ms; entrada de ruta a −8px, búsqueda a −4px, superficie a +8px, filas a +10px, estado a −5px, retroalimentación a −6px. Controles de 150ms, además de respuestas de presión/enfoque/flecha y guardado/esqueleto. Natural y sutil reducen el movimiento; la opción del sistema reducido/quieto lo elimina. |

## 4. Sistema de diseño y componentes fijos

Usa los tokens existentes de Pictures claro/oscuro; no importes la paleta predeterminada del kit. `--fondo` corresponde a fondo; `--superficie` a tarjeta/popover; `--texto` a primer plano; `--texto-suave` a primer plano atenuado; `--superficie-2` a secundario/atenuado/hover neutro; `--acento` y `--sobre-acento` a roles primarios; `--exito`, `--aviso`, `--error` a estados semánticos reales. `--borde` y `--borde-suave` se mantienen como líneas decorativas; `--texto-tenue` proporciona el borde accesible de entradas y botones de contorno, según SP-2/SP-14. No se proponen valores de color nuevos.

| Token de origen | Claro | Oscuro |
|---|---|---|
| fondo / superficie | #faf9fc / #ffffff | #0b0c10 / #16181f |
| superficie-2 | #efe9f8 | #242733 |
| texto / texto-suave | #1c1425 / #6b6178 | #f4f5f7 / #9aa1ad |
| texto-tenue | #766c85 | #8a91a0 |
| acento / sobre-acento | #6d3fe0 / #ffffff | #9479ff / #120b24 |
| acento-hover | #5530b8 | #a58dff |
| borde / borde-suave | #e3daef / #efe9f8 | #383c48 / #2a2d38 |
| exito / aviso / error | #1f7a55 / #8f5f12 / #b23a45 | #78d6a8 / #f7c46b / #ff979f |

Los archivos WOFF2 locales de producción de Geist Sans y Geist Mono vienen incluidos en la compilación existente de t12 y coinciden con los de los proyectos hermanos. No se solicitan ni instalan fuentes. H1 de 24px, H2 de 20px, nombres de proyectos de 16px, acciones de 14px y etiquetas/texto de apoyo de 12–13px; los recuentos usan únicamente números tabulares en tipografía mono. Los radios de panel/margen interno/campo/píldora de 32/24/18/999px se heredan del vocabulario del proyecto hermano elegido. Las superficies usan 28px de relleno en escritorio y 20px en teléfonos; las filas usan 16px/20px de relleno vertical en escritorio/teléfonos; los diálogos, 28/24px; los controles tienen una altura mínima de 44px.

| Contrato del componente | Fuente/uso real |
|---|---|
| shadcn:button listo/hover/enfoque/presionado/deshabilitado/cargando predeterminado | `@/components/ui/button`; guardar/nuevo/importar, estado deshabilitado explícito según el estado |
| shadcn:button de contorno listo/hover/enfoque/presionado/deshabilitado | El mismo; Abrir, reintentar, cancelar y elementos contextuales de herramientas |
| shadcn:input de texto vacío/completo/enfoque/no válido/deshabilitado | `@/components/ui/input`; etiquetas asociadas para búsqueda y nombre del proyecto |
| shadcn:skeleton al cargar registro/escena | `@/components/ui/skeleton`; los marcadores de posición mantienen la geometría del contenido |
| shadcn:dialog para nombre/copia/pendiente abierto/cerrado | `@/components/ui/dialog`; primitivo real de Animate UI/Base UI, sin imitación en HTML |
| shadcn:alert-dialog para cargar del servidor/descartar cambios sin guardar abierto/cerrado | `@/components/ui/alert-dialog`; confirmación explícita y foco inicial en Cancelar |
| native:select para idioma/propietario/inspección predeterminado/enfoque/deshabilitado | Selectores nativos con etiquetas; no se afirma que sea un Select de shadcn |
| native:details para cuenta/biblioteca cerrado/abierto/enfoque | Vocabulario existente de cuenta y recurso contextual de biblioteca; no es un menú ARIA |
| custom:project-register para resultados/carga/vacío/error con líneas | Lista semántica de artículos de proyectos con datos alineados y nombres de acción para cada proyecto |
| custom:save-status en línea guardando/guardado/pendiente/sin conexión/error/conflicto | Amplía la posición existente del nombre/estado de escena; texto más icono, nunca solo color |
| custom:import-prompt para cuenta pendiente/éxito/rechazo/no válido | Consentimiento explícito para la cuenta actual y recurso descargable original |
| custom:scene-illustration SVG contextual/vacío | Escena estática integrada; no es un motor 3D funcional ni ofrece exportación |
| kit:mockup inspector | `@kit/mockup` mountMockup/useMockup y `@kit/motion` useMotionProfile |

## 5. Navegación, foco y movimiento

Las rutas del producto son /proyectos y /3d, o la apertura de identidad en Taller planificada como /proyectos/[id]; el mockup permanece en un único documento independiente. La divulgación de cuenta incluye el vocabulario compartido de Mi cuenta/Proyectos/Planes/cerrar sesión, con los destinos fuera del alcance identificados explícitamente como simulados. La importación se muestra mediante el selector nativo Vista solo para inspección. Los enlaces de ruta Proyectos y Taller se mantienen neutros. El filtrado de propietarios para el personal aparece como “Mockup · Acceso → Empleado / administrador”; los propietarios ordinarios no tienen controles para otras cuentas.

La búsqueda conserva el foco del teclado mientras se escribe. Busca en toda la colección simulada autorizada, incluida Columna, que aparece después de la primera página cargada. Los cambios de búsqueda/propietario reinician la paginación. En producción, los filtros deben aplicarse antes de paginar y se deben ignorar las respuestas obsoletas; el mockup local, sincrónico, muestra el resultado en la interfaz, pero no prueba una API ni la concurrencia.

Los activadores de diálogos conservan su destino de foco; Cancelar/Escape cierra los diálogos normales y restaura el foco. AlertDialog requiere una opción explícita y comienza con el foco en Cancelar. Base UI proporciona contención del foco modal y vuelve inerte el fondo. Los cambios de ruta enfocan H1. La divulgación de cuenta admite el cierre con Escape y al hacer clic fuera, con foco visible. El encabezado del producto y el pie comparten el mismo contenedor horizontal.

**Gramática de movimiento: registro preciso.** La configuración expresiva usa 360ms cubic-bezier(.77,0,.175,1) y desfases de filas de 28ms. Natural usa 240/120/18ms y sutil usa 140/90/8ms para registro/rápido/escalonado; los controles rápidos expresivos usan 150ms cubic-bezier(.23,1,.32,1). Comportamientos reales: la regla de ruta entra a −8px y el grupo de búsqueda a −4px; (1) registro vertical de la superficie de 8px, (2) desfase horizontal escalonado de filas de 10px, (3) registro de retroalimentación de -6px en los cambios de estado, (4) registro de estado de -5px, (5) hover del botón de -2px, (6) presión de +1px/scale(.98), (7) movimiento de la flecha al abrir, (8) asentamiento del contorno de enfoque de 5→3px, (9) rotación al guardar y (10) compresión horizontal del esqueleto. Las transiciones modales usan el perfil de movimiento/estado reducido. El texto del cuerpo permanece completamente visible durante la entrada; no hay fundidos intermedios que dificulten la lectura.

El movimiento reducido del sistema, Quieto y ?still=1 eliminan los desplazamientos/efectos repetidos y mantienen el contenido/las acciones finales. Las pestañas ocultas pausan las animaciones CSS. Los efectos continuos solo aparecen en el estado de carga/guardado, no en contenido decorativo fuera de pantalla. No hay desplazamiento/paralaje ni decoración ambiental que deba suspenderse.

## 6. Flujos de usuario

1. **Primer guardado:** entrar a Taller → Escena nueva / Sin guardar → Guardar proyecto → campo de nombre con etiqueta → el nombre vacío anuncia la validación → guardar explícitamente → confirmación Guardado en tu cuenta. Las ediciones simuladas posteriores pasan de pendiente → Guardando… → guardado confirmado. Los estados del inspector nativo permanecen estables para la revisión, salvo que una edición o un guardado simulado real haya iniciado la operación simulada. Guardar ahora es un atajo explícito. Si la escena cambia durante una simulación en curso, se invalida ese temporizador anterior; solo se guarda la escena pendiente más reciente. En producción se usan revisiones confirmadas por el servidor; nunca se muestra una etiqueta de éxito basada en una respuesta obsoleta.
2. **Escena nueva:** Escena nueva, Plantillas o la acción contextual “Abrir en Escena” de Biblioteca usan el mismo límite de proyecto nuevo. La edición pendiente de un proyecto con nombre se guarda antes de mostrar la escena nueva. Los errores, el modo sin conexión o los conflictos impiden completar la acción y conservan el borrador. Una escena que nunca se guardó requiere Guardar, Cancelar o Descartar explícitamente; cancelar la deja en su sitio y elimina cualquier destino aplazado, de modo que una reconexión o un guardado posterior no provoquen una navegación inesperada. El nombre resultante es exactamente Escena nueva, con Sin guardar y sin identidad guardada; nada llega al servidor hasta el primer guardado con nombre. Las revisiones de proyectos existentes permanecen intactas.
3. **Volver a abrir:** visitar Proyectos con la misma cuenta → buscar, explorar o cargar más → Abrir en cada fila → escena completa y su nombre. Los cambios en los filtros vuelven a la primera página. Los errores al cargar la página siguiente conservan las filas actuales y ofrecen Reintentar siguiente página. La persistencia real entre navegadores es un criterio de aceptación de la implementación, no una garantía de este HTML.
4. **Conflicto:** mostrar un panel persistente “Hay otra versión guardada” y “Conflicto · autoguardado detenido” junto al nombre de la escena → guardar como proyecto propio nuevo mediante el diálogo de nombre, o confirmar la carga de la versión del servidor. La carga reemplaza la escena visible y conserva un borrador local recuperable para esta cuenta. No hay ninguna acción para sobrescribir o reintentar con la revisión actual ni interfaz de historial de versiones.
5. **Sin conexión o error:** “Sin guardar” permanece visible; la opción para reintentar aparece según el contexto. La escena permanece local. Al restablecerse la conexión, pasa a pendiente; solo una confirmación posterior produce Guardado en tu cuenta. Un borrador local no enviado no debe aparecer cuando inicia sesión otra cuenta.
6. **Solo lectura de otra cuenta:** el personal busca entre todos los propietarios autorizados → abre la fila de otra cuenta → aviso visible de propietario y solo lectura → los controles para editar los elementos de prueba no aparecen o están deshabilitados. Guardar copia está disponible solo con taller.usar y escribe en la cuenta del usuario actual. Sin taller.usar, la acción está deshabilitada con una explicación visible. Abrir nunca transfiere la propiedad ni actualiza el original.
7. **Importación heredada:** el primer inicio de sesión detecta una escena sin procesar del navegador → el aviso menciona esta cuenta y las exclusiones de datos que solo están en el navegador → Importar a mi cuenta crea un proyecto propio tras la confirmación; los reintentos remiten a la misma fuente y recibo. Ahora no no crea ninguno. Si el elemento de prueba no es válido, se explica que escena no contiene una escena válida y se ofrece Descargar original. La fuente sin procesar nunca se modifica ni se borra, sea cual sea el resultado. La descarga simulada es claramente un ejemplo de JSON no válido, nunca los datos del navegador del usuario.

## 7. Vistas y selectores de estado local

| Valor de Vista | Superficie / contenido |
|---|---|
| lista | Estructura compartida de la aplicación; encabezado de proyectos; búsqueda en la lista; filtro de propietario solo para personal; filas con líneas; paginación y recuperación |
| taller | Estructura existente del taller; nombre/estado de escena en línea; Guardar ahora/primer guardado; respuestas a falta de conexión/conflicto; contexto de escena |
| consulta | Misma escena del taller; aviso de propietario externo/solo lectura; sin edición; solo acción permitida para crear una copia propia |
| importar | Misma estructura compartida de lista con un aviso de importación explícito encima, cuenta receptora, consentimiento y explicación de conservación |

El inspector conserva los identificadores nativos de vista/estado/escena/tema/movimiento y las etiquetas en español Vista/Estado/Diálogo/Tema/Movimiento. Se puede seleccionar cada estado declarado; los estados que no correspondan a la vista actual dejan intacta su estructura habitual, en lugar de inventar un comportamiento de producto ajeno. El elemento de prueba de acceso y el control ES/EN no modifican los permisos del backend ni las preferencias guardadas. El contenido inicial está en español; ES/EN es una referencia ilustrativa de redacción/reflujo, y durante la implementación las cadenas finales se agruparán en `textos-proyectos.ts`.

## 8. Cobertura de estados

| Valor del estado | Se aplica a / interfaz observable y recuperación |
|---|---|
| normal | Lista normal, Taller guardado en la cuenta, solo lectura de otra cuenta, importación pendiente del primer inicio de sesión |
| cargando | Esqueletos de la lista o de la escena; acciones de importación pendientes/deshabilitadas; no se afirma que la escena esté guardada mientras se carga |
| vacio | Explicación de la lista de proyectos y acceso a Taller; no se presenta una escena vacía de usuario ficticia |
| sin-resultados | Explicación de que no hay coincidencias con una acción para borrar la búsqueda |
| pagina-siguiente | Filas autorizadas adicionales de la siguiente página cargada |
| error-pagina | Se conservan las filas existentes; error en línea y control para reintentar la página siguiente |
| error | Error acotado al listado/apertura/importación y opción explícita de reintento; los datos locales permanecen |
| nuevo | Nombre Escena nueva en Taller, datos de prueba sin piezas, Sin guardar; el primer guardado solicita un nombre |
| guardando | Guardando… junto al nombre; se deshabilita el guardado duplicado; la edición puede crear un cambio pendiente más reciente; etiqueta de importación pendiente |
| guardado | Guardado en tu cuenta solo después de la confirmación del guardado simulado actual |
| pendiente | Cambios pendientes; Guardar ahora está disponible. La inspección nativa permanece pendiente; una edición simulada real inicia la simulación de autoguardado. |
| sin-conexion | Estado explícito de falta de guardado/sin conexión, borrador conservado, acción para reconectar/reintentar |
| error-guardar | Error de guardado persistente, sin falso estado de guardado, borrador conservado y opción de reintento |
| conflicto | Se detiene el autoguardado; se conserva el borrador local actual; opciones para crear una copia propia o cargar la versión del servidor con confirmación |
| datos-invalidos | Se explica que el formato de importación no es válido; no se crea ningún proyecto; acción para descargar el original |
| importado | Constancia de una sola importación y acción para abrir el proyecto; se conserva el original |
| rechazado | No se crea ningún proyecto, el original permanece, opción para continuar a los proyectos |
| validacion + guardar/copia | Error asociado de nombre obligatorio; el campo y los botones siguen accesibles |
| sin-taller + consulta | El original de otra cuenta es de solo lectura, la copia está deshabilitada, se explica que falta el permiso de Taller |
| sin-permiso | Rechazo sin contenido de la escena ni nombre del proyecto protegido; volver a los proyectos propios |

Escenas: guardar (primer nombre), copia (copia propia), cargar (carga confirmada del servidor), descartar (reemplazo de una escena que nunca se guardó), continuar (salida bloqueada/pendiente). Los guardados fallidos conservan el campo ingresado/la escena actual hasta la recuperación; los cambios de estado de la fuente son controles de inspección, no transiciones de producción. Aquí no existe la opción de eliminar, transferir ni ver el historial de versiones, ni la edición de la gestión de cuentas.

## 9. Reglas adaptables

A >1100px, usar el registro completo de cuatro columnas, márgenes laterales de 40px y el panel lateral de Taller, lienzo e inspector de 280px. Entre 761 y 1100px, usar márgenes laterales de 28px, tres columnas en el registro (el estado sigue disponible en la escena abierta), datos flexibles de nombre/propietario e inspector del taller de 240px. La búsqueda y el propietario mantienen una proporción de 2:1 cuando el espacio lo permite.

A ≤760px, usar márgenes de página/papel de 20px; el texto de estado de la fila se alinea con el borde del nombre/propietario, sin icono desplazado; los controles de cuenta/idioma del encabezado común se ajustan como en los contratos de las vistas hermanas; el título/herramientas y los filtros se apilan. La identidad del proyecto ocupa toda la fila; el propietario/estado quedan a la izquierda y Abrir a la derecha. No se introduce una tabla con desplazamiento horizontal ni una acción recortada. Taller contrae su panel lateral contextual y coloca el inspector debajo de la ilustración de ancho completo; el nombre, el estado y el control de guardado se ajustan sin puntos suspensivos. Las acciones del diálogo en el teléfono se apilan en orden visual inverso; la acción principal de guardar/cargar aparece encima de las acciones secundarias y todas las opciones siguen siendo accesibles. En producción, el orden del teclado y de lectura debe coincidir con la jerarquía de acciones aprobada; los datos de prueba conservan el orden DOM heredado. El ancho del diálogo es el ancho de la ventana gráfica menos 40px y su altura se limita por debajo de la barra de inspección, con desplazamiento vertical interno.

Objetivos: teléfono de 390px, tableta de 768px, escritorio de 1280px; el ajuste a 320px es una salvaguarda. Las ventanas verticales o de poca altura deben permitir desplazarse hasta todos los controles; no se fuerza una tarjeta de trabajo de altura fija. La barra de inspección está fuera del producto y no representa requisitos de altura de producción.

## 10. Objetivos y límites de accesibilidad

Objetivo WCAG 2.2 AA: texto ≥4.5:1, límites/enfoque de controles significativos ≥3:1; acciones principales ≥44px; etiquetas de estado con texto e icono; enlaces, campos, elementos desplegables y diálogos accesibles mediante teclado; etiquetas completas en español/inglés; foco programático en H1/campo no válido; estado de guardado aria-live polite y errores alert; contención/restauración del foco modal y opciones destructivas explícitas. Este alcance no requiere casillas de verificación nativas, por lo que no se reintroduce el problema histórico de las casillas oscuras.

La auditoría sin conexión de la interfaz renderizada comprueba los estilos calculados reales, no las descripciones de la paleta. Abarca ambos temas, todas las combinaciones del inspector y las paradas del teclado. contrast.py estático lee la hoja de roles en línea del generador; la auditoría renderizada también evalúa las anulaciones de tokens del proyecto en tiempo de ejecución. Superar estas comprobaciones no demuestra la accesibilidad completa de la aplicación, la autorización autenticada, la interoperabilidad con tecnologías de asistencia ni la persistencia entre navegadores. Eso sigue siendo trabajo de implementación/revisión.

## 11. Criterios de aceptación visual y evidencia

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-AC-01 | 1280px | lista/normal | El símbolo de anillo y punto de Pictures, Sempertex, el idioma, la cuenta y la regla neutra de ruta coinciden con el shell hermano. |
| A-AC-02 | 1280px | lista/normal | Nombre, propietario, estado y Abrir comparten cada fila delimitada; no aparece una cuadrícula de tarjetas de proyectos ni un panel de detalles. |
| A-AC-03 | 390px | lista/normal | El nombre del proyecto, el propietario, el estado y Abrir se reorganizan dentro de márgenes de 20px sin desplazamiento horizontal. |
| A-AC-04 | 390/1280px | lista/cargando | Aparecen esqueletos con forma de contenido junto con Cargando proyectos; no hay un indicador de carga aislado en el centro. |
| A-AC-05 | 390/1280px | lista/vacio | Están presentes la explicación del estado vacío y la entrada a Taller. |
| A-AC-06 | 390/1280px | lista/sin-resultados | La acción para borrar la búsqueda restablece los resultados autorizados disponibles. |
| A-AC-07 | 768/1280px | lista/staff fixture | El filtro por propietario aparece para el personal; el modo de propietario común muestra solo los proyectos propios. |
| A-AC-08 | 390/1280px | lista/error-pagina | Las filas existentes permanecen visibles junto con una acción para reintentar la página siguiente. |
| A-AC-09 | 390/1280px | taller/nuevo | El nombre es Escena nueva, el estado es Sin guardar y Guardar abre el diálogo del nombre. |
| A-AC-10 | 390/1280px | guardar/validacion | Al enviar un nombre vacío se muestra un error asociado; no se indica un estado guardado. |
| A-AC-11 | 390/1280px | taller/guardando | El estado permanece junto al nombre de la escena, se deshabilita el guardado duplicado y se puede seguir editando. |
| A-AC-12 | 390/1280px | taller/sin-conexion | El estado sin guardar/sin conexión y la opción de reintentar siguen visibles mientras se mantiene el contexto de la escena. |
| A-AC-13 | 390/1280px | taller/conflicto | El estado de guardado automático detenido y ambas opciones, conservar copia/cargar del servidor, están visibles; Guardar ahora está deshabilitado. |
| A-AC-14 | 390/1280px | cargar | La confirmación identifica las versiones local y del servidor, y Cancelar recibe el foco inicial. |
| A-AC-15 | 390/1280px | consulta/sin-taller | El aviso de solo lectura identifica el contexto externo y Guardar copia está deshabilitado con una explicación. |
| A-AC-16 | 390/1280px | importar/normal | La cuenta receptora aparece antes del consentimiento; se explican el almacenamiento local en el navegador de la conversación/imágenes y la conservación de los datos originales. |
| A-AC-17 | 390/1280px | importar/datos-invalidos | Se muestra una explicación específica de la escena no válida y se puede descargar el original; no aparece un comprobante de éxito. |
| A-AC-18 | 390/1280px | descartar | Para reemplazar una escena nunca guardada se requiere Guardar, Cancelar o Descartar explícitamente. |
| A-AC-19 | todos los anchos declarados | reducida/estática | La animación se detiene en la disposición final legible; las acciones y el texto de estado siguen disponibles. |
| A-AC-20 | 390/1280px | ambos temas | Los campos, las acciones delineadas y los selectores nativos tienen límites y foco de teclado visibles. |
| A-AC-21 | 390/1280px | sin-permiso | No se revela el nombre de ninguna escena/protegido; está disponible volver a los proyectos propios. |

### Verificación actual — solo r12

- Se dibujaron dos HTML de miniatura antes de completar la entrada. Ambos se renderizaron e inspeccionaron a 1080px; se seleccionó el candidato 1. La vista previa dividida del candidato 2 consume ancho útil sin aportar información necesaria para abrir la escena.
- Generador sin conexión actual: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/proyectos@v1.r12.dir-a.tsx --out <design>/proyectos@v1.r12.dir-a.html` — APROBADO, 656 KB, 2,135 archivos de código fuente empaquetados. Bibliotecas reales instaladas y fuentes Geist locales de producción; sin recursos alternativos, instalación ni recursos descargados.
- `contrast.py <design>/proyectos@v1.r12.dir-a.html` — **158 pares comprobados en modo claro y oscuro; todos aprobados**, código de salida 0. La auditoría del renderizado también comprueba las asignaciones de tokens en tiempo de ejecución.
- Auditoría inicial de r12: **600 renderizados / 600 combinaciones planificadas a 1280/390/768px, 20,944 mediciones de texto y 1,376 paradas de foco**, código de salida 0. `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`. Luego se reconstruyó un ajuste de cancelación limitado al controlador; la auditoría del artefacto final que aparece abajo reemplaza esta ejecución inicial.
- Se aprobaron las comprobaciones específicas de Playwright en caché: la búsqueda encuentra Columna más allá de la página inicial y conserva el foco en la entrada; validación de nombre vacío y primer guardado con nombre; secuencia de pendiente/guardado/guardado confirmado; cancelación del temporizador de guardado simulado obsoleto después de ediciones nuevas; el conflicto pausa el guardado e inicia la confirmación de carga del servidor al cancelar; borrador local conservado y restaurable; copia de solo lectura de un proyecto ajeno y copia propia sujeta a permisos; comprobante de importación y control de descarga para fuentes inválidas. No se observaron errores de página ni solicitudes HTTP externas.
- Prueba de adaptación: **80 combinaciones sin desbordamiento**, 320/390/768/1024/1280px × ambos temas × cuatro vistas × ciclo ES/EN. El control de idioma está en el contenedor compartido de lista e importación; Taller hereda la última configuración regional elegida. Esta es evidencia de reajuste del fixture, no una verificación de localización de producción.
- Comprobaciones complementarias de cancelación: un intento sin conexión de crear un proyecto seguido de Cancelar y reconectar conserva el original; un proyecto con nombre pendiente se guarda antes de crear Escena nueva; el reemplazo de una plantilla/biblioteca que nunca se guardó sigue requiriendo una decisión explícita. Un localizador inicial del script era ambiguo porque Plantillas aparece tanto en la barra lateral como en el inspector; un localizador limitado al inspector completó la comprobación. No se infirió un defecto del producto a partir de ese error del localizador.
- Capturas inspeccionadas en memoria: ambas miniaturas a 1080px, lista clara a 1280px / lista oscura a 390px, conflicto de Taller oscuro a 1280px / importación inválida clara a 390px. El contenedor compartido, los grupos de filas alineados, los márgenes interiores de 20px en teléfono, el texto de estado semántico y las acciones de recuperación sin recortes siguen visibles. No se escribieron capturas ni archivos adicionales de vista previa.
- Comprobación de evidencia actual en una sola dirección: `compare_directions.py A.html --json` devolvió **ok=true, evidence_ok=true, cero selectores ausentes**. Los selectores de diseño, navegación y tipografía coinciden con los elementos renderizados; los cuatro selectores de evidencia de movimiento se animan en el perfil expresivo. Esto no es un resultado de diferenciación de tres direcciones.

### Verificación del artefacto final

- Reconstrucción final sin conexión: APROBADA, 656 KB, 2,135 archivos de código fuente. Comprobación final de contraste: **158 pares comprobados en modo claro y oscuro; todos aprobados**, código de salida 0.
- Comando de auditoría final: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <design>/proyectos@v1.r12.dir-a.html --max-combos 200 --widths 1280,390,768` — **600 renderizados (600 combinaciones planificadas), 20,944 mediciones de texto, 1,367 paradas de foco**, código de salida 0. Sin advertencia de muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

- Comparación final de solo lectura con el r12 C disponible: `compare_directions.py A.html C.html --json` — **ok=true, evidence_ok=true, missing_evidence=[]**, código de salida 0; similitud de diseño **0.101**, same_navigation=true, same_motion=false. Ambos comparten la navegación del producto requerida, mientras que su composición y movimiento difieren. Esta comprobación de dos direcciones no establece la comparación A/B/C.
- Existe el HTML de B, pero su JSON de ejes no estaba disponible al momento de la entrega. Por lo tanto, la comparación de tres direcciones **no se ejecutó** y queda como seguimiento del coordinador. No se modifica ninguna dirección de pares ni archivo canónico.
- SHA-256 del HTML final: `e5d2ea4673fcda6f3e505b70852b6790224f68f97c621c2864cb989d7dab4544`.

Esto demuestra la calidad del fixture sin conexión, no la persistencia del servidor activo, la autorización, la deduplicación de importaciones ni la conformidad de accesibilidad en producción. No se ejecutaron pruebas ni compilaciones del repositorio de producción ni se invocó ningún servicio de red.

## 12. Preguntas abiertas, supuestos e inquietudes

P: Después de «Ahora no», ¿se debería volver a ofrecer la solicitud de importación heredada en un inicio de sesión posterior y dónde se podría volver a abrir? Decisión del propietario/Planner; esta exploración no agrega una ruta de importación permanente ni una entrada de navegación no solicitada.
P: Si la escena heredada no tiene un nombre válido, ¿la importación debería pedir uno o usar el nombre existente «Escena nueva»? Decisión del propietario/Planner; el fixture de importación válido ya tiene un nombre ilustrativo y no define esa alternativa.

Se reutiliza como supuesto para el borrador el límite actual de 120 caracteres del campo de nombre de escena, pendiente de alineación con el contrato del campo de nombre de proyecto. Las cadenas nuevas usan textos agrupados con prioridad al español y equivalentes ilustrativos en inglés; la implementación debe incluir las cadenas nuevas finales en textos-proyectos.ts. Ningún selector de inspección concede permisos nuevos sobre el producto.

Todos los comportamientos de guardado/importación/sin conexión/servidor son simulaciones en memoria. No se lee, elimina, carga ni modifica ninguna escena de usuario sin procesar. El plan aún requiere la selección del propietario y aprobación independiente; esta dirección no puede autorizar T4.1 ni la implementación en producción. Esta delegación abarca solo la dirección A. La diferenciación por pares entre A/C se mide en los artefactos actuales; la diferenciación completa entre A/B/C de r12 sigue pendiente de una comparación del coordinador hasta que B proporcione su JSON de ejes. No se hereda ningún resultado de comparación de r11 ni se edita ninguna otra dirección. La comprobación de evidencia propia se registra con los resultados de verificación actuales.


Alcance de la revisión: no se modifican los archivos canónicos proyectos@v1.md/.html. Esta dirección sigue como **borrador; pendiente de selección del propietario y aprobación del plan**. El contenedor compartido sigue los contratos finalizados de elementos hermanos y los tokens de producción; la solicitud histórica de paletas y familias tipográficas separadas queda reemplazada por la restricción de sistema fijo de este brief. El generador real de componentes reemplaza los comentarios anteriores que solo abarcaban fragmentos. No se realiza ninguna instalación de paquetes, edición de código fuente, creación de directorio de vista previa ni aprobación.
