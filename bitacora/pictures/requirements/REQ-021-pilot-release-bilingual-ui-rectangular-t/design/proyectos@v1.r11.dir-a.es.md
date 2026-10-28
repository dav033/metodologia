---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
direction: a
name: Registro de proyectos
source_revision: r11
source_behavior: proyectos@v1.r11.behavior.md
approval: pending-owner-selection-and-plan-approval
---

# Registro de proyectos — exploración A, r11

## 1. Identidad y trazabilidad

Esta es una exploración específica de esta revisión para **proyectos@v1**, no es el contrato canónico ni una entrada de implementación aprobada. Cambia únicamente las superficies de proyectos guardados del producto existente. Elegir esta dirección no aprueba el plan. Esta delegación no escribe ningún contrato compartido, PLAN, fuente del repositorio, registro de cambios ni archivo de memoria del proyecto.

Autoridad de comportamiento: `proyectos@v1.r11.behavior.md` (SHA-256 `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65`), R6/R7 y SPEC «Behavior — SP-3 and SP-4 (round 9 answered)». Los propietarios siguen editando SPEC y PLAN; sus secciones de ingeniería no relacionadas no forman parte del alcance de diseño. Instantánea de fuentes al momento de la inspección: SPEC `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d`; PLAN.json `c7600864b9a1b48b9381622f346ca3e32e7e7cff61180ca20af10e7e6db2793f`.

Fuentes del producto de solo lectura inspeccionadas en t12 y asesor: `src/app/globals.css`, `layout.tsx`, `3d/page.tsx`, `Taller3D.tsx`, `guardado-escena.ts`, `guardado-conversacion.ts`, `imagenes-guardadas.ts`, `Biblioteca.tsx`, `CabeceraApp.tsx` y `/api/decoraciones`. Esta última es la biblioteca de decoraciones, no el almacenamiento de proyectos. La aplicación existente permite guardar en el navegador, incluye un nombre de escena en línea y una etiqueta de estado de guardado; las listas vinculadas a cuentas, el manejo de conflictos y la importación heredada son adiciones dentro del alcance. Mantener por separado el almacenamiento de conversaciones e imágenes de IA que solo existe en el navegador.

Autoridad del shell compartido: borradores finales de los proyectos hermanos `cuentas-admin@v1.md/.html` y `planes@v1.md/.html`. Se mantienen su marca compacta de anillo y punto de Pictures/Sempertex, tipografía Geist, navegación horizontal neutra, superficies con esquinas redondeadas, acciones tipo píldora y control de cuenta desplegable. El brief más reciente reemplaza explícitamente los comentarios anteriores que solicitaban paletas y fuentes separadas; esas direcciones históricas no se reutilizan. No se introduce una marca, fuente ni paleta nuevas.

Consumidores afectados si el propietario elige y aprueba esta dirección más adelante: copia de diseño de SP-4 T4.1, implementación de interfaz T4.4/T4.5 y revisión visual T4.8. La compatibilidad con el diseño exploratorio anterior, aún no aprobado, es **un cambio visual incompatible**: la composición de barra lateral/archivo se convierte en el shell compartido del producto y en un registro continuo. Se conservan la semántica de R6/R7 y el comportamiento de la ronda 9. Ningún otro subplan se redirige ni aprueba implícitamente.

## 2. Propósito y usuarios

El propietario responde «¿Qué escena guardada quiero continuar?». El personal también puede encontrar el proyecto de un propietario autorizado e inspeccionarlo sin modificar el original. En Taller, el nombre y el estado real del guardado se leen juntos. Al iniciar sesión por primera vez, un aviso pregunta si la escena heredada de este navegador pertenece a la cuenta actual; el consentimiento es explícito.

Todos los datos de ejemplo son neutros y están claramente marcados como Mockup: Mesa rectangular, Arco, Backing, Columna y Guirnalda con «· ejemplo»; Cuenta de ejemplo y Otra cuenta de ejemplo; `cuenta@prueba.local`. No hay identidades de clientes inventadas, fechas de eventos, eslóganes promocionales ni historial. Los recuentos se derivan de la lista en memoria. Los proyectos guardados durante la interacción con el mockup se agregan a esa misma lista. Al actualizar el HTML se restablecen todas las operaciones; no se accede al localStorage de la aplicación, IndexedDB, cuentas ni servicios remotos.

## 3. Enfoque, composición y miniatura elegida

Primero se dibujaron dos composiciones pequeñas en HTML. **Se elige la opción 1:** un único registro con filas delimitadas, búsqueda y propietario en una barra compartida y una acción Abrir inmediata en cada fila. **La opción 2** exploró una división entre lista y detalle; dedica un ancho considerable a una vista previa y agrega un paso de selección antes de abrir, por lo que se ajusta menos a esta postura operativa. Ambas miniaturas permanecen como evidencia inmutable en las rutas asignadas de r11.

La composición elegida cambia el producto solo donde los proyectos guardados necesitan una nueva superficie. Conserva el encabezado principal de los proyectos hermanos, el título de página de 24px, la regla de rutas neutras Proyectos/Taller y el pie alineado. En escritorio, el nombre, el propietario, el estado y Abrir comparten una misma línea base; en teléfonos, las filas apilan el nombre sobre el propietario y el estado, con Abrir al lado. No se agregan cuadrículas de tarjetas, líneas de tiempo del historial de proyectos, franjas promocionales ni acciones para eliminar o transferir.

Taller conserva la estructura existente del editor: nombre de escena editable en línea y estado en la barra de herramientas superior, panel lateral de herramientas, lienzo de escena, inspector de escena/IA y el contexto existente de fotos/lista de compras. Se agregan el control de guardado, la navegación de cuenta/proyecto y los avisos persistentes de conflicto/sin conexión. La ilustración y los datos de ejemplo simplificados de herramientas existentes son contextuales; no rediseñan ni reemplazan los renderizadores y editores de producción.

La importación es un aviso durante el primer inicio de sesión, encima de la lista de proyectos; no es una nueva página /import ni una ruta permanente del producto. Antes de dar el consentimiento, se muestra la cuenta que recibirá la escena. El selector de acceso del Mockup es una herramienta de inspección, nunca un ajuste del producto que otorgue permisos al personal.

### Tabla de ocho ejes

| Eje | Expresión renderizada |
|---|---|
| concepto | Registro operativo de proyectos: nombres, propietarios, estado real de guardado y apertura alineados en una sola superficie de trabajo. |
| diseño | Shell de Pictures/Sempertex y regla horizontal de rutas sobre una única lista delimitada a todo el ancho; Taller conserva su barra de herramientas, panel de herramientas, lienzo e inspector; la importación es un aviso en línea durante el primer inicio de sesión, encima de la lista. |
| navegación | Control de cuenta desplegable compartido y rutas Proyectos/Taller; las filas se abren directamente sin un panel de detalles; el filtro de propietario y la búsqueda por nombre comparten una barra; diálogos contextuales para nombre, carga y salida. |
| tipografía | Geist Sans local existente: título de página de 24px, título de sección de 20px, nombres de proyectos de 17px, acciones de 14px y datos complementarios de 12–13px; Geist Mono se limita a los roles existentes de metadatos y recuentos. |
| densidad | Una superficie continua con relleno de 28px, filas delimitadas de 24px, relleno de 20px en teléfonos y acciones de 44px. En escritorio, el propietario, el estado y la apertura se agrupan en la línea base del nombre; en teléfonos, la identidad queda encima del propietario y el estado, junto a Abrir. |
| componentes | Button, Input y Skeleton de shadcn/Base UI instalados, Dialog y AlertDialog de Animate UI, selectores nativos de rol/propietario/idioma y detalles de cuenta; sin cuadrícula ornamental de tarjetas. |
| color | Tokens exactos claros/oscuros de Pictures en globals.css, alias de roles SP-2/SP-14 heredados y formas redondeadas. El color de énfasis se aplica a la acción principal; los colores semánticos de éxito, advertencia y error se usan para el estado real. Los límites de entradas y controles de contorno usan texto-tenue. |
| movimiento | Registro preciso: 360ms cubic-bezier(.77,0,.175,1) para la superficie 8px, fila 10px con desplazamientos de 28ms, retroalimentación -6px, estado -5px; 150ms para elevación/presión del botón, flecha y foco. El indicador de guardado gira y el skeleton se comprime; los estados de movimiento reducido o detenido se establecen al instante, y las animaciones se pausan cuando la pestaña está oculta. |

## 4. Sistema de diseño y componentes definidos

Usa los tokens claros/oscuros existentes de Pictures; no importes la paleta predeterminada del kit. `--fondo` corresponde al fondo; `--superficie` a tarjeta/ventana emergente; `--texto` al primer plano; `--texto-suave` al primer plano atenuado; `--superficie-2` a secundario/atenuado/hover neutro; `--acento` y `--sobre-acento` a roles primarios; `--exito`, `--aviso`, `--error` a estados semánticos reales. `--borde` y `--borde-suave` siguen siendo líneas decorativas; `--texto-tenue` proporciona el borde accesible de entrada y botón de contorno, según SP-2/SP-14. No se proponen nuevos valores de color.

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

Los recursos WOFF2 locales de producción de Geist Sans y Geist Mono se incluyen desde la compilación existente de t12, igual que en las aplicaciones hermanas. No se solicitan ni instalan fuentes. H1 24px, H2 20px, nombres de proyecto 17px, acciones 14px, etiquetas/ayuda 12–13px; solo los recuentos usan mono tabular. Los radios de panel/área interna/campo/píldora de 32/24/18/999px se heredan del vocabulario de la aplicación hermana seleccionada. Las superficies usan 28px de relleno en escritorio y 20px en teléfono; los diálogos, 28/24px; los controles tienen una altura mínima de 44px.

| Contrato del componente | Fuente real / uso |
|---|---|
| shadcn:button predeterminado listo/hover/foco/presionado/deshabilitado/cargando | `@/components/ui/button`; guardar/nuevo/importar, estado deshabilitado explícito según el estado |
| shadcn:button contorno listo/hover/foco/presionado/deshabilitado | Igual; Abrir, reintentar, cancelar y elementos de prueba de herramientas contextuales |
| shadcn:input texto vacío/con contenido/en foco/no válido/deshabilitado | `@/components/ui/input`; etiquetas asociadas para búsqueda y nombre del proyecto |
| shadcn:skeleton carga del registro/escena | `@/components/ui/skeleton`; los marcadores de posición conservan la geometría del contenido |
| shadcn:dialog nombre/copia/pendiente abierto/cerrado | `@/components/ui/dialog`; primitiva real de Animate UI/Base UI, sin imitación en HTML |
| shadcn:alert-dialog cargar del servidor/descartar cambios sin guardar abierto/cerrado | `@/components/ui/alert-dialog`; confirmación explícita y foco inicial en Cancelar |
| native:select idioma/propietario/inspección predeterminado/en foco/deshabilitado | Selectores nativos con etiqueta; no se afirma que sea shadcn Select |
| native:details cuenta/biblioteca cerrado/abierto/en foco | Vocabulario de cuenta existente y elemento de prueba de biblioteca contextual; no es un menú ARIA |
| custom:project-register resultados con líneas/cargando/vacío/error | Lista semántica de artículos de proyectos con datos alineados y nombres de acción por proyecto |
| custom:save-status en línea guardando/guardado/pendiente/sin conexión/error/conflicto | Amplía la posición existente del nombre/estado de la escena; texto más icono, nunca solo color |
| custom:import-prompt pendiente/éxito/rechazado/no válido con alcance de cuenta | Consentimiento explícito de la cuenta actual y elemento de prueba original descargable |
| custom:scene-illustration SVG contextual/vacía | Escena estática en línea; no es un motor 3D funcional ni implica que se pueda exportar |
| kit:mockup inspector | Montaje `@kit/mockup` con mountMockup/useMockup y `@kit/motion` con useMotionProfile |

## 5. Navegación, foco y movimiento

Las rutas del producto son /proyectos y /3d, o la identidad prevista /proyectos/[id] que abre Taller; el mockup permanece en un único documento autocontenido. El desplegable de cuenta incluye el vocabulario compartido Mi cuenta/Proyectos/Planes/cerrar sesión, y los destinos fuera de alcance se etiquetan explícitamente como simulados. La importación se ofrece mediante el selector nativo Vista solo para inspección. Los enlaces de rutas Proyectos y Taller mantienen un tono neutro. El filtrado por propietario para personal se muestra como “Mockup · Acceso → Empleado / administrador”; los propietarios comunes no tienen controles para otras cuentas.

La búsqueda conserva el foco del teclado mientras se escribe. Busca en toda la colección autorizada del mockup, incluida Columna, que va más allá de la primera página cargada. Los cambios de búsqueda/propietario restablecen la paginación. En producción, esos filtros deben aplicarse antes de paginar e ignorar respuestas obsoletas; el mockup local síncrono demuestra la interfaz resultante, pero no prueba la API ni la concurrencia.

Los activadores de diálogo conservan su objetivo de foco; Cancelar/Escape cierran los diálogos normales y restauran el foco. AlertDialog requiere una elección explícita y empieza con el foco en Cancelar. Base UI proporciona contención del foco modal y vuelve inerte el fondo. Los cambios de ruta enfocan H1. El desplegable de cuenta admite el cierre con Escape y al hacer clic fuera, con foco visible. El encabezado del producto y el pie de página comparten el mismo contenedor horizontal.

**Gramática de movimiento: registro preciso.** El perfil Expresivo usa como valores predeterminados 360ms cubic-bezier(.77,0,.175,1), con desfases de fila de 28ms. Natural usa 240/120/18ms y Sutil 140/90/8ms para registro/acciones rápidas/desfase escalonado; los controles rápidos expresivos usan 150ms cubic-bezier(.23,1,.32,1). Comportamientos reales: (1) registro vertical de la superficie de 8px, (2) desfase horizontal escalonado de filas de 10px, (3) registro de -6px al cambiar de estado para la respuesta visual, (4) registro de -5px para el estado, (5) hover del botón de -2px, (6) presión de +1px/scale(.98), (7) movimiento de la flecha al abrir, (8) ajuste del contorno de foco de 5→3px, (9) rotación al guardar y (10) compresión horizontal del esqueleto. Las transiciones modales usan el perfil de movimiento/estado reducido. El texto del cuerpo permanece completamente visible durante la entrada; no hay desvanecimiento intermedio que dificulte la lectura.

El movimiento reducido del sistema operativo, Quieto y ?still=1 eliminan el movimiento/los efectos repetidos y mantienen el contenido/las acciones finales. Las pestañas ocultas pausan las animaciones CSS. Los efectos continuos se limitan al estado de carga/guardado, no al contenido decorativo fuera de pantalla. No hay desplazamiento/paralaje ni decoración ambiental que deban suspenderse.

## 6. Flujos de usuario

1. **Primer guardado:** entrar en Taller → Escena nueva / Sin guardar → Guardar proyecto → campo de nombre con etiqueta → el nombre vacío anuncia un error de validación → guardado explícito → confirmación Guardado en tu cuenta. Las ediciones posteriores pasan a pendiente → Guardando… → guardado confirmado. Guardar ahora es un acceso directo explícito. Si la escena cambia durante una simulación en curso, se invalida ese temporizador anterior; solo se guarda la escena pendiente más reciente. En producción se usan revisiones confirmadas por el servidor; nunca se muestra una etiqueta de éxito basada en una respuesta obsoleta.
2. **Escena nueva:** Escena nueva, Plantillas o “Abrir en Escena” en la Biblioteca contextual usan el mismo límite de creación de proyecto. La edición pendiente de un proyecto con nombre se guarda antes de que aparezca la escena nueva. Sin conexión/error/conflicto impide completar la acción y conserva el borrador. Una escena que nunca se guardó requiere Guardar, Cancelar o Descartar explícito; cancelar la deja en su lugar. El nombre resultante es exactamente Escena nueva, con Sin guardar y sin identidad guardada; nada llega al servidor hasta que se guarde por primera vez con un nombre. Las revisiones de proyectos existentes permanecen intactas.
3. **Volver a abrir:** visitar Proyectos con la misma cuenta → buscar/explorar/cargar más → Abrir en la fila correspondiente → escena completa y su nombre. Los cambios en los filtros vuelven a la primera página. Los errores de la página siguiente conservan las filas actuales y ofrecen Reintentar siguiente página. La persistencia real entre navegadores es un criterio de aceptación de implementación; este HTML no la garantiza.
4. **Conflicto:** mostrar un panel persistente “Hay otra versión guardada” y “Conflicto · autoguardado detenido” junto al nombre de la escena → guardar como un nuevo proyecto propio mediante el diálogo de nombre, o confirmar la carga de la versión del servidor. La carga reemplaza la escena visible y conserva un borrador local recuperable para esta cuenta. No hay una acción para sobrescribir/reintentar con la revisión actual ni una interfaz de historial de versiones.
5. **Sin conexión/error:** “Sin guardar” permanece visible; la opción de reintentar es contextual. La escena permanece local. Al restablecerse la conexión pasa a pendiente; solo la confirmación posterior produce Guardado en tu cuenta. Un borrador local no enviado no debe aparecer cuando inicia sesión otra cuenta.
6. **Solo lectura de otra cuenta:** el personal busca entre todos los propietarios autorizados → abre la fila de otra cuenta → aviso visible de propietario/solo lectura → controles de edición ausentes/deshabilitados. Guardar copia solo está disponible con taller.usar y guarda en la cuenta de quien consulta. Sin taller.usar, la acción aparece deshabilitada con una explicación visible. Abrir nunca transfiere la propiedad ni actualiza el original.
7. **Importación heredada:** el primer inicio de sesión detecta una escena sin procesar en el navegador → el aviso identifica esta cuenta y las exclusiones de datos solo disponibles en el navegador → Importar a mi cuenta crea un proyecto propio tras la confirmación; los reintentos hacen referencia a la misma fuente/constancia. Ahora no no crea nada. El elemento de prueba no válido explica que la escena no contiene una escena válida y ofrece Descargar original. La fuente sin procesar nunca se modifica ni se borra, sea cual sea el resultado. La descarga del mockup se identifica claramente como un JSON de ejemplo no válido, nunca como datos del navegador de la persona usuaria.

## 7. Vistas y selectores de estado local

| Valor de Vista | Superficie / contenido |
|---|---|
| lista | Estructura compartida de la aplicación; encabezado de proyectos; búsqueda en la lista; filtro de propietario solo para personal; filas con líneas; paginación y recuperación |
| taller | Estructura existente del taller; nombre/estado de escena en línea; Guardar ahora/primer guardado; respuestas a falta de conexión/conflicto; contexto de escena |
| consulta | Misma escena del taller; aviso de propietario externo/solo lectura; sin edición; solo acción permitida para crear una copia propia |
| importar | Misma estructura compartida de lista con un aviso de importación explícito encima, cuenta receptora, consentimiento y explicación de conservación |

El inspector conserva los identificadores nativos de vista/estado/escena/tema/movimiento y las etiquetas en español Vista/Estado/Diálogo/Tema/Movimiento. Se puede seleccionar cada estado declarado; los estados que no correspondan a la vista actual dejan intacta su estructura habitual, en lugar de inventar un comportamiento de producto ajeno. El elemento de prueba de acceso y el control ES/EN no modifican los permisos del backend ni las preferencias guardadas. El contenido inicial está en español; ES/EN es una referencia ilustrativa de redacción/reflujo, y durante la implementación las cadenas finales se agruparán en `textos-proyectos.ts`.

## 8. Cobertura de estados

| Valor de estado | Se aplica a / interfaz observable y recuperación |
|---|---|
| normal | Lista normal, Taller guardado en la cuenta, solo lectura de propietario externo, importación pendiente del primer inicio de sesión |
| cargando | Esqueletos de la lista o la escena; acciones de importación pendientes/deshabilitadas; no se afirma que esté guardada mientras se carga la escena |
| vacio | Explicación de la lista de proyectos y acceso a Taller; no una escena vacía de usuario inventada |
| sin-resultados | Explicación de que no hay coincidencias con una acción para borrar la búsqueda |
| pagina-siguiente | Filas autorizadas adicionales en la siguiente página cargada |
| error-pagina | Se conservan las filas existentes, con error en línea y control para reintentar la página siguiente |
| error | Fallo acotado de lista/apertura/importación y reintento explícito; los datos locales permanecen |
| nuevo | Nombre de Taller Escena nueva, elemento de prueba sin piezas, Sin guardar; el primer guardado solicita un nombre |
| guardando | Guardando… junto al nombre; guardado duplicado deshabilitado; la edición puede crear un cambio pendiente más reciente; etiqueta de importación pendiente |
| guardado | Guardado en tu cuenta solo después de la confirmación simulada del guardado actual |
| pendiente | Cambios pendientes → simulación de autoguardado; Guardar ahora disponible |
| sin-conexion | Estado explícito sin guardar/sin conexión, borrador conservado, acción para reconectar/reintentar |
| error-guardar | Error persistente al guardar, sin falso estado de guardado; borrador conservado y reintento disponible |
| conflicto | Se detiene el autoguardado; se conserva el borrador local actual; opciones para crear una copia propia o cargar la versión del servidor con confirmación |
| datos-invalidos | Se explica la estructura de importación no válida; no se crea ningún proyecto; acción para descargar el original |
| importado | Constancia de importación exactamente una vez y acción Abrir proyecto; se conserva el original |
| rechazado | No se crea ningún proyecto, el original permanece, opción para continuar a los proyectos |
| validacion + guardar/copia | Error asociado de nombre obligatorio; el campo y los botones siguen siendo accesibles |
| sin-taller + consulta | Original de propietario externo en solo lectura, copia deshabilitada, permiso de Taller faltante explicado |
| sin-permiso | Rechazo sin contenido de escena ni nombre de proyecto protegido; volver a los proyectos propios |

Escenas: guardar (primer nombre), copia (copia propia), cargar (carga confirmada del servidor), descartar (reemplazo de una escena nunca guardada), continuar (salida bloqueada/pendiente). Si falla el guardado, se conservan el campo ingresado y la escena actual hasta la recuperación; los cambios de estado de la fuente son controles de inspección, no transiciones de producción. Aquí no existe la opción de eliminar, transferir, consultar el historial de versiones ni editar la administración de cuentas.

## 9. Responsive rules

At >1100px use the full four-column register, 40px shell gutters and Taller rail/canvas/280px inspector. At 761–1100px use 28px shell gutters, three register columns (status remains available on the opened scene), flexible name/owner data and a 240px workshop inspector. Search and owner retain a 2:1 split when space permits.

At ≤760px use 20px page/paper gutters; row status text aligns with the name/owner edge without an offset icon; the common masthead's account/language controls wrap as in the sibling contracts; title/tools and filters stack. Project identity spans the row; owner/status sit at the left and Open at the right. No horizontal table scroller or clipped action is introduced. Taller collapses its contextual side rail and places its inspector below the full-width illustration; name, status and save control wrap without ellipsis. Phone dialog actions stack in reverse visual order, with primary action first visually and all choices accessible. Dialog width is viewport minus 40px and height is bounded below the inspection bar with internal vertical scrolling.

Targets: 390px phone, 768px tablet, 1280px desktop; 320px reflow is a guardrail. Portrait/short windows must scroll to all controls; there is no forced fixed-height working card. The inspection bar is outside the product and does not represent production height requirements.

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

### Actual verification

- Installed real workspace available: installed=True, built=True, 96/96 entries. No fallback, installation or fetched asset.
- Offline builder succeeded for the assigned TSX and HTML, including local Geist fonts and installed React/Animate UI controls.
- contrast.py: **158 pairs checked in light and dark, all pass** (bundled role sheet); actual runtime styles checked by audit below.
- Initial full audit: 400/400 planned combinations, 13,790 text measurements, 1,367 focus stops; PASS. Later refinements add stronger outline boundaries and interactive fixture fidelity; final-build evidence follows.
- Playwright behavior checks: named save; newly saved list entry; retained search typing focus; matching beyond the initial loaded page; pending→saving→saved; obsolete-save timer cancellation after a newer edit; conflict pause; kept/restorable local draft; foreign original copy permission; import success and invalid-data download action. All passed with **zero page errors and zero network requests**. This is mock interaction evidence, not server/storage proof.
- Final screenshots inspected in-memory: 1280 light list, 390 light Taller, 1280 dark Taller and 390 dark import. The broader audit supplies all declared combinations; screenshots are not separate permitted deliverables.
- Additional responsive/English probe: the first 320px run found the status icon offset misaligned with name/owner text. Phone row icons were removed while retaining the full text status. The repeated 24-render check at 320/768/1024px in both themes passed with zero contrast, non-text, padding, overflow or alignment findings. The repaired 320px dark English list was visually inspected.
- Direction evidence: compare_directions.py on A alone found every layout/navigation/type/motion selector, with no missing evidence. The three-direction comparison then passed all pairs: A/B layout similarity 0.131; A/C 0.114; B/C 0.156. Navigation remains shared, while measured composition and motion differ. This is a comparison of the rendered peer snapshots, not approval of those artifacts.
- **Final audit: 400 renders / 400 planned combinations, 14,022 text measurements, 1,360 focus stops; exit 0.**

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

The final post-rebuild three-direction comparison also returned exit 0, `ok=true`, `evidence_ok=true`, zero missing selectors and the same passing pair metrics. No production tests, build, backend authorization, storage or cross-browser persistence checks were executed; this delegation owns only the offline design artifacts.

## 12. Open questions, assumptions and concerns

Q: After “Ahora no”, should the legacy-import prompt be offered again on a later sign-in, and where can it be reopened? Owner/Planner decision; this exploration adds no permanent import route or unsolicited navigation entry.
Q: If the legacy scene lacks a usable name, should import request one or use the existing “Escena nueva” name? Owner/Planner decision; the valid import fixture already has an illustrative name and does not decide that fallback.

The existing scene-name input's 120-character maximum is reused as a draft assumption, pending alignment with the project-name input contract. New strings use Spanish-first grouped copy with illustrative English counterparts; implementation must place final new strings in textos-proyectos.ts. No new product permission is granted by an inspection selector.

All save/import/offline/server behaviors are in-memory simulations. No raw user scene is read, erased, uploaded or changed. The plan still requires owner selection and independent approval; this direction cannot authorize T4.1 or production implementation. The peer-direction comparison was run read-only after both peer JSON/HTML outputs became available; no peer artifact was edited. All three pairs passed, which establishes exploration distinctness, not owner approval or production acceptance.
