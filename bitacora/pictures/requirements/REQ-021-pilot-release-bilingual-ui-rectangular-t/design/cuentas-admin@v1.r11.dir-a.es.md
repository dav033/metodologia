---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r11.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
source_revision: r10.dir-a
feedback: "2026-10-27T08:01 direction=a: generous radii, softer surfaces and more air"
---

# Parte de acceso — direction A

## 1. Identidad y trazabilidad

**Iteración unidireccional r11 de r10 A; borrador pendiente de selección por parte del propietario.** Esta nota no es el contrato canónico de doce secciones ni un insumo de implementación aprobado. El contrato `cuentas-admin@v1` definitivo todavía requiere selección y finalización junto con el plan. No se editó ningún contrato compartido, plan, historial ni repositorio.

Fuentes leídas: `SPEC.md` (`65b1e5ecc06f20d9`), `PLAN.md` (`cc7e53f2abf3c23c`), `PLAN.json` (`7a2c833a7e711508`) y el archivo compartido `cuentas-admin@v1.r11.behavior.md` (`c665ab01443531a7`). Estos hashes identifican la instantánea de las fuentes, no su aprobación. SP-2 cubre R1 cuentas invitadas, R3 administración de roles y R16 planes de acceso. Sus contratos consumidos de SP-1 son `account-service@1`, `session-guard@1` y `permission-map@1`.

## 2. Propósito, concepto y elemento memorable

**Concepto: una hoja de producción para eventos.** El administrador responde: «¿Quién integra el equipo, qué herramientas puede usar y qué debo cambiar?». Cada fila reglada reúne el nombre, correo electrónico, empresa, rol asignado, estado, último acceso y acción de administración de la persona. La franja de anotaciones explica los tres planes acumulativos mientras el trabajo permanece en el registro. Los nombres, empresas, direcciones de correo electrónico, fechas y cantidades son datos de ejemplo ilustrativos; los dominios `.example` son ejemplos reservados.

**Elemento memorable: registro cinético.** La página se acomoda en su posición de trabajo mediante varias direcciones deliberadas: el papel desciende, los registros se desplazan horizontalmente, la franja de anotaciones entra desde arriba y, por último, una costura metalizada queda estampada en su lugar. Los cambios de estado trazan un breve movimiento de registro. El contenido legible permanece visible durante estas transformaciones. La idea se inspira en alinear una hoja de producción y revisar una instalación de globos terminada; no imita una credencial física de acceso ni una carpeta de proyecto.

## 3. Composición preservada y registro visual

Esta revisión parte de una copia exacta del TSX de r10 y solo modifica CSS. Los comentarios del propietario (2026-10-27T08:01, direction=a) solicitan tarjetas, botones, campos, chips y paneles mucho más redondeados, superficies más suaves, más espacio y una jerarquía más ligera, conservando la composición, navegación y movimiento de A. No se crearon una dirección nueva ni miniaturas. Las dos miniaturas históricas de abajo pertenecen a r10 y permanecen inmutables. Ambas miniaturas visuales originales se generaron antes del TSX de r10. Incluyen CSS adaptable, tipografía de visualización integrada sin conexión y variantes claras y oscuras del sistema; son estudios de composición, no alternativas basadas en fragmentos para la maqueta completa.

- **Elegida: [candidata 1](cuentas-admin@v1.r10.dir-a.html.candidate-1.html)** — un encabezado amplio, filas completas y comparables de cuentas y una franja estrecha de anotaciones del plan. Hace visible el trabajo reiterado del administrador y se integra con naturalidad en el editor de roles.
- [Candidata 2](cuentas-admin@v1.r10.dir-a.html.candidate-2.html) — una columna vertebral de navegación a la izquierda y una ficha sobredimensionada de la persona seleccionada. Da demasiada importancia a una sola persona y repite una composición con navegación lateral ya representada en el registro visual.

El registro incluye SP-4 `proyectos@v1.r8.dir-a/b/c.md` y SP-3 `taller-esenciales@v1.r7.dir-c.md`. El despliegue de escenas en línea del archivo, el marco espacial, las carpetas de muestras y las ranuras de silicona del taller se distinguen del amplio registro de cuentas y la hoja de permisos. La marca de anillo y punto de Pictures, el lenguaje de productos de Sempertex, los planes acumulativos, los nombres semánticos de roles y los controles operativos claros aportan continuidad. Los nuevos colores de exploración son propuestas sujetas a la selección del propietario.

## 4. Ocho ejes, lenguaje visual y componentes reales

| Eje | Expresión actual |
|---|---|
| Concepto | Una hoja de llamado para la producción de un evento: las personas se registran junto con sus herramientas específicas, estado de acceso y próxima acción. La marca de anillo y punto de Pictures y la unión de lámina conectan la página operativa con las instalaciones de Sempertex. |
| Diseño | Encabezado amplio y asimétrico (título grande y condensado a la izquierda, cantidad actual de cuentas a la derecha), regla horizontal de navegación, registro con líneas divisorias a todo lo ancho y una franja estrecha de anotaciones del plan; la lista de roles y la hoja de permisos reemplazan el registro sin usar una cuadrícula de tarjetas de panel. En teléfonos, el registro queda sobre las anotaciones del plan. |
| Navegación | Botones neutros de ruta horizontal dentro del flujo para Cuentas / Roles y permisos / Mi cuenta, diálogos contextuales de administración para cada persona y un menú desplegable de cuenta con nombre; el acceso exclusivo por invitación no tiene una ruta de registro abierto. Los selectores nativos de vista previa permanecen fuera del producto. |
| Tipografía | DejaVu Sans Condensed Bold integrada como Dispatch, título de 38–68px y títulos de sección y diálogo de 23–28px; Adwaita Sans integrada como Work, de 14–16px, y Adwaita Mono integrada como Measure, de 11–13px para marcas de tiempo de acceso y detalles de edición. El texto en inglés y español se adapta al espacio. |
| Densidad | Filas de cuenta con líneas divisorias y más espacio, con 24px de relleno vertical; relleno de papel de 28px en escritorio y 20px en teléfono; esquinas de panel de 32px, superficies internas de 24px, esquinas de campos y controles de rol de 18px, esquinas de casillas de 8px y acciones, selectores y chips de estado en forma de píldora; sin mosaicos de indicadores clave. |
| Componentes | Button, Input, Checkbox y Skeleton reales de shadcn/Base UI ya instalados; Dialog y AlertDialog de Animate UI con contención del foco. Filas de registro, encabezado de producción, grupos de campos de permisos y unión de lámina personalizados; paneles redondeados de papel y planes, selección de rol con relleno suave y chips semánticos de estado en forma de píldora. Selectores nativos de rol, estado e idioma; no se usan fragmentos alternativos. |
| Color | Asignación de exploración local propuesta para los roles semánticos de Pictures: acero frío #e4ebf2, tinta #112c48 y cobalto #12489e; azul marino oscuro #0b1c2e con acción #a6caff. El cobre de la lámina se limita a una muestra de material de Sempertex; el verde, ámbar y rojo indican el estado por nombre. Las reglas neutras más suaves y una superficie de plan de bajo contraste aligeran la jerarquía sin cambiar la paleta ni los bordes accesibles de los controles. La navegación neutra usa texto y una regla, no el color de acento. |
| Movimiento | Registro cinético preciso, cubic-bezier(.76,0,.24,1), paneles expresivos de 480ms con desplazamientos de filas de 55ms y controles de 180ms; registro distintivo del papel y las filas, registro de reglas, contramovimiento del contador de la franja, sello de lámina de 900ms, registro ambiental de lámina de 6s, estampado de estado, recorrido del esqueleto y desplazamiento de flecha al pasar el cursor o presionar. Los perfiles sutil/natural acortan los tiempos. El contenido permanece visible durante el movimiento. Los modos reducido/inmóvil eliminan toda animación; suspensión cuando está oculto o fuera de pantalla. |

Por qué esta estructura funciona: las cuentas son información de producción. Un título grande y el total actual de cuentas establecen el alcance, mientras que un único registro con líneas divisorias muestra los datos operativos de cada persona. La tipografía expresiva se reserva para los títulos; las etiquetas pequeñas y los controles usan Adwaita Sans. La muestra de lámina tiene una unión inflable cosida, un color cobre discreto y su propio movimiento de registro. La conecta con los materiales del decorador sin competir con los datos de las cuentas.

La revisión r11 volvió a comprobar los mismos archivos en modo de solo lectura, tanto en `t12` como en `asesor`. Se inspeccionaron en modo de solo lectura los archivos `AGENTS.md`, `src/app/globals.css` y los patrones de `src/components/admin/AdminTabs.tsx` de ambos repositorios. El producto actual asigna nombres de tokens en español a roles de shadcn ya existentes. La exploración conserva esas responsabilidades semánticas y propone los siguientes valores locales; no cambia los tokens de producción:

| Rol de Pictures | Rol del kit | Asignación de exploración clara / oscura |
|---|---|---|
| `--fondo` | `--background` | `#e4ebf2` / `#0b1c2e` |
| `--superficie` | card / popover | `#f9fbff` / `#142b42` |
| `--texto` | primeros planos | `#112c48` / `#e6effa` |
| `--texto-suave` | primer plano atenuado | `#405771` / `#b6c9df` |
| `--superficie-2` | secondary / muted | `#dce5ef` / `#203b54` |
| `--acento`, `--sobre-acento` | primary / primer plano de primary | `#12489e`, blanco / `#a6caff`, `#0b1c2e` |
| `--borde` | border | `#8292a4` / `#829cb5` |
| Borde accesible del control | input | `#64788f` / `#96aec7` |
| `--exito`, `--aviso`, `--error` | success / warning / destructive | `#205d43`, `#755000`, `#a62434` / `#a1dfbe`, `#f2d591`, `#ffafb8` |
| Lámina propuesta, solo para materiales | `--foil`, `--foil-ground` | `#8c2b15`, `#f3c2ac` / `#ffb899`, `#51382c` |
| Separadores decorativos propuestos | `--rule` | `#c4d0dd` / `#405a73`; solo reglas decorativas, nunca límites necesarios de controles |
| Superficie de panel suave propuesta | `--surface-soft` | `#edf3fa` / `#193149`; panel de anotaciones y fondo del rol seleccionado |

Los tokens de forma de r11 son propuestas locales del borrador compartidas entre clases de componentes: `--radius` / `--radius-field:18px`, `--radius-panel:32px`, `--radius-inset:24px`, `--radius-check:8px` y `--radius-pill:999px`. Reemplazan las esquinas de 2px de r10 y amplían la convención de producción `--radius:0.8rem`; no modifican los tokens de producción. El papel, la franja y los diálogos usan radios de panel; la muestra de material, el aviso legal, los comentarios y el menú desplegable de cuenta usan radios internos; los campos, los elementos de rol y los recibos de enlaces usan radios de campo; los botones, selectores nativos, el menú desplegable de cuenta y los chips de estado usan forma de píldora. Las rutas horizontales de solo texto mantienen el modelo de subrayado existente. Las filas de cuenta conservan columnas compartidas y líneas más ligeras, con 24px de relleno vertical; las opciones de rol ganan una separación de 8px y una superficie suave al seleccionarse. Los bordes de entrada y foco significativos conservan los colores accesibles originales.

Componentes del manifiesto instalados: `shadcn:button` default/outline/destructive, `shadcn:input` text/email/password, `shadcn:checkbox` checked/unchecked/disabled, `shadcn:skeleton` loading, `shadcn:dialog` invitation/management/link y `shadcn:alert-dialog` permanent deletion. Sus importaciones son `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Dialog, AlertDialog y Checkbox usan la implementación de Animate UI/Base UI instalada. `mountMockup`/`useMockup` provienen de `@kit/mockup`; `useMotionProfile` proviene de `@kit/motion`. El registro de cuentas, la franja de planes, el encabezado, los grupos de campos de permisos y la unión son composiciones personalizadas con nombre, no componentes de biblioteca estándar. No se usaron fragmentos alternativos, instalaciones de paquetes ni recursos descargados.

## 5. Navegación e interacción

Las siete vistas de vista previa nativas son Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Mi cuenta y Nuevo aviso obligatorio. La barra visible **Mockup** de la plantilla conserva los selectores `view`, `state`, `scene`, `theme` y el selector de movimiento expresivo predeterminado. El producto tiene su propio selector nativo de idioma ES/EN, inicializado según el idioma del navegador.

Las vistas con sesión iniciada tienen rutas de cuenta neutrales en línea y un menú de cuenta que muestra David y su rol de administrador, con Mi cuenta y cerrar sesión. El resumen para teléfono muestra el nombre; al abrirlo, revela el rol y las mismas acciones. La identidad de Mi cuenta es la misma cuenta de David, mientras que los datos de ejemplo de invitación identifican a Valentina. La vista de aviso obligatorio oculta las demás rutas del producto y ofrece aceptar o cerrar sesión. Los controles de vista previa quedan fuera de esta barrera del producto.

La administración depende de la cuenta seleccionada. Los diálogos mantienen el foco del teclado y lo devuelven al cerrarse. Los diálogos de invitación, administración y enlace de un solo uso permiten usar Escape; la eliminación de cuentas o roles usa AlertDialog y un botón explícito para cancelar. La maqueta simula los resultados localmente y no implementa rutas autenticadas, emisión de tokens ni comprobaciones de permisos.

## 6. Flujos conservados

1. **Iniciar sesión:** correo electrónico invitado y contraseña → página solicitada permitida, primera herramienta permitida o Mi cuenta si el rol no tiene herramientas. El caso de error usa un mensaje genérico para contraseña incorrecta, correo electrónico desconocido, cuenta desactivada y correo electrónico bloqueado; siempre explica la espera de quince minutos después de varios intentos fallidos. Para recuperar la contraseña, se solicita al administrador un enlace de un solo uso válido por 24 horas; no se incorpora el envío automático de correos electrónicos ni el registro público.
2. **Activar:** nombre/correo electrónico invitado → contraseña nueva y confirmación, mínimo de ocho caracteres → aviso completo en el idioma del navegador, versión 1 → aceptación explícita sin marcar de antemano → activación y destino directo a la primera herramienta permitida con sesión iniciada. Si el enlace se usó, venció o se reemplazó, se solicita un enlace nuevo emitido por el administrador. La invitación tiene una vigencia de siete días.
3. **Actualizar aviso:** la versión nueva bloquea todas las demás páginas del producto hasta que se acepte. El texto de finalización indica la obligación de almacenar la versión y la fecha. El texto de aviso proporcionado se conserva exactamente en ES/EN, incluidos los marcadores legales entre corchetes.
4. **Mi cuenta:** consultar identidad personal y rol → contraseña actual más contraseña nueva dos veces → cambiar la contraseña y volver a iniciar sesión. Se muestran datos de ejemplo de la versión y fecha de aceptación. Cambiar la contraseña finaliza las sesiones.
5. **Invitar/administrar:** buscar y filtrar → indicar nombre, correo electrónico, empresa opcional y un rol → generar → copiar un enlace que se muestra una sola vez → cerrar. Se rechaza un correo electrónico registrado. Para una cuenta existente, cambiar el rol, desactivar/reactivar, generar un enlace nuevo de invitación o restablecimiento, o solicitar su eliminación. Los enlaces nuevos invalidan los enlaces anteriores sin usar del mismo tipo; esa consecuencia se informa antes de generarlos y en el comprobante. Si se rechaza el acceso al portapapeles, se explica cómo seleccionar y copiar manualmente.
6. **Eliminar:** si hay trabajo guardado, se rechaza la eliminación sin modificar la cuenta (`CUENTA_CON_TRABAJO`); no se puede eliminar ni desactivar al último administrador, ni quitarle el rol de administrador. Para eliminar de forma permanente una cuenta sin trabajo guardado, se requiere escribir su correo electrónico exacto. El gasto de IA se conserva sin datos personales como «Cuenta eliminada». La maqueta ilustra la opción; no garantiza la integridad de la base de datos.
7. **Roles:** seleccionar uno de cinco roles de sistema de solo lectura para revisar permisos agrupados por herramienta, o crear/editar un nombre personalizado y una selección de casillas. Se rechaza un rol personalizado sin permisos con `ROL_SIN_PERMISOS`. No se pueden eliminar los roles personalizados asignados; un rol personalizado sin asignaciones se puede eliminar después de confirmarlo. Cada cuenta tiene un rol, incluidos los planes de acceso.

## 7. Especificaciones de las vistas

| Vista | Jerarquía principal y controles | Información complementaria |
|---|---|---|
| Cuentas | Título del alcance/total actualizado, acción de invitación, búsqueda por nombre/correo electrónico, filtros de rol/estado, filas completas de cuentas, cantidad visible de resultados. | Empresa, último acceso en hora de Bogotá, franja de planes acumulativos; acciones contextuales de cuenta. |
| Roles | Cinco roles de sistema de solo lectura y ejemplos personalizados; rol seleccionado, nombre, casillas agrupadas por herramienta y guardar/eliminar rol personalizado. | Explicación de solo lectura, validación de permisos mínimos, rechazo de roles asignados. |
| Iniciar sesión | Correo electrónico, contraseña, Enter. | Acceso solo por invitación; restablecimiento de contraseña emitido por el administrador; error genérico; texto de finalización del destino. |
| Activar | Identidad de la persona invitada, contraseña nueva dos veces, aviso completo, consentimiento sin marcar, botón Activar deshabilitado hasta aceptar. | Regla de ocho caracteres; invitación válida por siete días; recuperación de invitación vencida/usada/reemplazada. |
| Restablecer | Contraseña nueva dos veces, guardar y volver a iniciar sesión. | Enlace de un solo uso válido por 24 horas, emitido por el administrador; recuperación ante un enlace no válido. |
| Mi cuenta | Identidad/empresa/rol de administrador de David, contraseña actual, contraseña nueva dos veces, acción para cambiarla. | Las sesiones finalizan al cambiar la contraseña; versión/fecha de ejemplo del aviso. |
| Actualizar aviso | Aviso completo, versión 1, en el idioma seleccionado/del navegador; consentimiento sin marcar, aceptar/continuar, cerrar sesión. | Almacenamiento de versión/fecha; texto entre corchetes pendiente de revisión legal; sin otras rutas del producto. |

Selector de escenas: formulario de invitación, hoja de administración, enlace de un solo uso, eliminación de cuenta y eliminación de rol. Cada escena se puede abrir directamente para inspeccionarla y también mediante el flujo del producto correspondiente.

## 8. Estados y alcance

| Estado de vista previa | Alcance aplicable / resultado observable |
|---|---|
| Normal | Estado de trabajo editable; los roles del sistema de solo lectura siguen siendo de solo lectura. |
| Cargando | Esqueletos de cuentas/roles; esqueleto del formulario y envío/campos deshabilitados; sin acciones duplicadas. |
| Vacío | Lista de cuentas: no hay cuentas coincidentes; permite borrar filtros o muestra orientación para invitar. Los roles del sistema nunca forman un conjunto de datos vacío. |
| Error | Las lecturas de cuentas/roles ocultan las filas sin confirmar y permiten reintentar. El inicio de sesión muestra el mensaje uniforme con una espera de quince minutos. Los demás formularios explican el fallo y conservan los datos escritos. |
| Éxito | Resultado específico de la vista: destino de inicio de sesión/activación, recuperación del inicio de sesión con contraseña, aviso aceptado o cambio de administración guardado. |
| Validación | Anuncio de error con una acción clara; controles de contraseña/nombre no válidos y selección obligatoria/permitida; la validación de rol personalizado sin permisos también funciona al enviar el formulario. |
| Sin permiso | Rechazo limitado al ámbito, sin datos/acciones de administración; permite recuperarse desde Mi cuenta. Esta prueba visual no concede permisos del servidor. |
| Enlace vencido o usado | El formulario de activación/restablecimiento se reemplaza por texto de recuperación; no se envía ninguna contraseña. |
| Correo duplicado | El rechazo explica cómo administrar la cuenta existente; no se envía una invitación nueva. |
| Cuenta con trabajo | El rechazo de eliminación identifica el trabajo guardado, ofrece la alternativa de desactivación y muestra un código de error estable. |
| Último administrador | Se rechaza la eliminación/desactivación/reasignación. |
| Rol en uso | Se rechaza la eliminación del rol asignado; los roles del sistema siguen siendo de solo lectura. |

La vista previa global permite deliberadamente combinaciones de vistas/estados no relacionadas; su alcance de producto se define arriba. Los estados al pasar el cursor, presionar, enfocar con el teclado, deshabilitar, marcar/desmarcar el consentimiento, usar un enlace de un solo uso y recurrir al portapapeles se pueden activar mediante controles reales. Las variantes sin conexión y de lectura parcial se representan con el estado de error recuperable: el diseño no afirma que algo se haya «guardado» sin confirmar ni promete recuentos actualizados. La gestión real de red, sesiones y condiciones de carrera corresponde a las tareas de implementación.

## 9. Comportamiento adaptable

A partir de **1101 px**, el registro principal tiene cuatro columnas alineadas y un panel de anotaciones de 280 px; un título amplio y una celda de edición de 300 px comparten el encabezado fijo. La hoja de roles tiene un selector de roles de 200 px y un editor de permisos agrupado. El margen exterior principal es de 40 px y el margen interno del papel es de 28 px. El panel de 280px tiene un margen interno de 24px y una superficie con esquinas suavemente redondeadas.

Entre **761–1100 px**, el margen exterior pasa a 28 px, el panel a 220 px (margen interno de 24px), los filtros usan dos columnas con la búsqueda a todo lo ancho, las acciones de cuenta pasan debajo de cada fila y los grupos de permisos pasan a una sola columna.

A **760 px o menos**, el papel y el panel de anotaciones se apilan y conservan sus radios de 32px; tanto el margen exterior como el del papel son de 20 px. Las identidades de cuenta ocupan todo el ancho de su fila, el rol y el estado en forma de píldora comparten una fila secundaria, y cada acción de administración de píldoras aparece debajo. Las filas para teléfono conservan el relleno vertical existente de 20px y las separaciones de 12px. Los filtros, la selección de roles, los permisos, los metadatos de identidad y los campos del formulario se apilan. La navegación se ajusta dentro del flujo. Los diálogos conservan un margen interno de 24 px, márgenes de 16 px respecto a la ventana y desplazamiento vertical cuando superan la altura de la ventana. Las bandas de comentarios se extienden por todo el ancho del papel en teléfono y conservan un espaciado interior de 20px, de modo que su texto queda en el mismo eje interior que el formulario, en lugar de crear una segunda columna estrecha. Los selectores nativos siguen siendo nativos en ambos temas.

Ancho mínimo compatible: 360 px, sin desplazamiento horizontal de la página. Las etiquetas en español e inglés se redistribuyen. Todas las secciones del producto y el pie de página comparten el eje exterior; los formularios y avisos comparten el eje interior de su papel.

## 10. Accesibilidad y objetivos de movimiento

Los objetivos son WCAG 2.2 AA para las interacciones aplicables: contraste de texto de 4.5:1, bordes de controles relevantes y foco de 3:1, anillo de foco visible de tres píxeles con un desplazamiento de cuatro píxeles, acciones de 44 px, campos y casillas con nombres programáticos, grupos etiquetados y errores/resultados anunciados. El estado de las casillas de roles del sistema sigue siendo visualmente legible aunque estén deshabilitadas. Los efectos destructivos se explican antes de la confirmación; para eliminar una cuenta se debe confirmar con el correo electrónico exacto.

Los ID de permisos se normalizan en identificadores sin espacios para que `aria-labelledby` generado por Base UI vincule cada casilla con su etiqueta. La búsqueda y los formularios conservan el foco mientras se escribe. Dialog/AlertDialog usan las primitivas reales instaladas para contener el foco, volver inerte el fondo y restaurar el foco al cerrar. La conformidad con lectores de pantalla es un objetivo; las mediciones del navegador por sí solas no la certifican.

Vocabulario de movimiento: registro preciso de la hoja en 480 ms, desplazamientos de filas de 55 ms y movimiento de controles de 180 ms; natural de 300/140 ms, sutil de 160/100 ms. El papel, las filas, las reglas, la franja, la entrada del efecto metálico, el efecto metálico ambiental, la respuesta de estado, el barrido del esqueleto y el movimiento de flechas al pasar el cursor/presionar son comportamientos distintos. La secuencia del efecto metálico ambiental dura seis segundos, solo transforma elementos, se pausa fuera de pantalla, al pasar el cursor y cuando la pestaña está oculta. `useMotionProfile()` proporciona el perfil y el estado de movimiento reducido. El movimiento reducido, Quieto y `?still=1` eliminan los desplazamientos y efectos repetitivos, y conservan el mismo contenido y las mismas acciones. Las animaciones de navegación/filtros desplazan el contenido legible en vez de recortarlo. No se usan fundidos de texto por opacidad ni destellos.

## 11. Criterios de aceptación observables y verificación

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1101+ | cuentas normal | Nombre/correo electrónico/empresa, rol, estado, último acceso y Administrar comparten cada registro con líneas divisorias; los conteos provienen de las mismas filas. |
| A-02 | 360–760 | cuentas normal | La identidad ocupa todo el registro; el rol/estado y Administrar se redistribuyen debajo sin desplazamiento horizontal de la página. |
| A-03 | 360+ | error de inicio de sesión | Un único mensaje genérico incluye la espera de quince minutos y no revela diferencias según la existencia o el estado de la cuenta. |
| A-04 | 360+ | activación normal | Ambos campos de contraseña y el aviso completo aparecen antes del consentimiento; Activar está deshabilitado hasta que se marque el consentimiento. |
| A-05 | 360+ | enlace vencido | No se muestran campos de contraseña y la opción de pedir un enlace nuevo al administrador es la recuperación visible. |
| A-06 | 360+ | invitación | El nombre/correo electrónico/empresa opcional/un rol preceden la generación; se rechazan los correos electrónicos duplicados. |
| A-07 | 360+ | recepción del enlace | La acción de copiar, el uso único/la vigencia y la invalidación de enlaces anteriores son visibles; al cerrar se elimina el comprobante. |
| A-08 | 360+ | trabajo guardado / último administrador | El rechazo explica el invariante y el envío destructivo permanece deshabilitado. |
| A-09 | 360+ | eliminación de cuenta | Para una cuenta sin trabajo asociado, se requiere su correo electrónico exacto antes de habilitar Eliminar permanentemente. |
| A-10 | 360+ | editor de roles | Los cinco roles del sistema son de solo lectura, las etiquetas de permisos agrupados son accesibles y los roles personalizados requieren al menos un permiso. |
| A-11 | 360+ | actualización de aviso | No aparecen otras rutas del producto; se puede acceder al consentimiento o al cierre de sesión; los marcadores de posición siguen siendo explícitos. |
| A-12 | 360+ | Mi cuenta | La identidad coincide con el menú de cuenta; la contraseña actual precede a las nuevas contraseñas y al texto sobre el cierre de sesión. |
| A-13 | 360+ | oscuro / claro | Los bordes de los campos, las casillas personalizadas, las acciones delineadas y el foco son visibles sobre sus superficies reales. |
| A-14 | 360+ | reducido / expresivo | El registro expresivo se puede medir; el modo reducido/estático no tiene animaciones en ejecución y conserva todas las acciones. |
| A-15 | 360+ | diálogo abierto / descartado | El foco de tabulación permanece dentro del diálogo real; al presionar Escape en una invitación, el foco vuelve a la acción que la inició después de cerrarla. |
| A-16 | 360+ | normal, cualquiera de los temas | El papel principal, el panel de anotaciones y el diálogo tienen radios de esquina computados de 32px; el aviso interior, los comentarios y la muestra de material tienen radios de 24px. |
| A-17 | 360+ | normal, cualquiera de los temas | Los botones, los selectores nativos, el desplegable de cuenta y los indicadores de estado tienen radios de píldora; los campos de texto tienen radios de 18px y bordes visibles. |
| A-18 | 1101+ | cuentas normal | El papel tiene un margen interno de 28px y las filas de cuenta tienen un relleno vertical de 24px; cada fila permanece alineada con las columnas compartidas del registro. |
| A-19 | 360+ | roles normal | El rol seleccionado tiene una superficie suave y redondeada de 18px, las opciones de rol están separadas por 8px y las casillas de permisos conservan estados marcados/no marcados distintos, con esquinas de 8px. |

Evidencia de R11 (solo esta instantánea; la verificación de r10 permanece en su nota inmutable): la cadena de herramientas instalada actual informa **instaladas/compiladas, 96/96 entradas disponibles**. Se ejecutó el compilador sin conexión actual mediante una ruta absoluta sobre `cuentas-admin@v1.r11.dir-a.tsx` para producir `cuentas-admin@v1.r11.dir-a.html`: **4475 KB, 2150 archivos de código fuente incluidos en el paquete**, código de salida 0. Se conservan shadcn/Base UI y Animate UI reales e instalados; no se usaron fragmentos alternativos, instalaciones ni recursos descargados. Las fuentes locales integradas siguen disponibles sin conexión.

`contrast.py`: **158 pares comprobados en temas claro y oscuro; todos pasan**, código de salida 0.

La auditoría final completa de renderizado sin conexión pasó **476/476 combinaciones, 19,738 mediciones de texto, 1,395 paradas de foco**, código de salida 0, a 1280px y 390px, en ambos temas, las siete vistas, doce estados y las cinco escenas de diálogo. Comprueba el renderizado estable con movimiento reducido y la estabilidad del diseño expresivo.

`RESULT: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento`

SHA-256 del HTML auditado: `03cc12f665c9e7740dffc150f20b0648bae496cbc3071e059d78899b8a9155dc`.

Historial de auditoría: el primer barrido de r11 falló con 98 hallazgos de alineación distintos, principalmente porque los comentarios en teléfono introducían un eje de texto más estrecho. Las bandas de comentarios a todo lo ancho en teléfono restauran el eje compartido del papel. Después, una comprobación específica reveló que el formato en línea del indicador de estado inactivo producía una línea centrada engañosa; los indicadores con formato de bloque y ancho ajustado al contenido conservan la alineación a la izquierda. Un barrido completo intermedio se interrumpió (código de salida 130) antes de la corrección del indicador y no cuenta como aprobado. Luego, seis comprobaciones específicas de vistas/estados móviles pasaron sin hallazgos de contraste, elementos no textuales, alineación, relleno ni desbordamiento antes del barrido completo final descrito arriba. No se cambió ninguna comprobación ni umbral.

La cobertura complementaria del navegador pasó **84 casos ES/EN** (siete vistas × dos temas × dos idiomas × 360/768/1024px) sin desbordamiento horizontal de página. Cada selector de evidencia JSON coincidió con la vista renderizada prevista. Se comprobaron los radios calculados: papel/panel/diálogo 32px, campos 18px, botones/selectores/estados 999px y recuadro de material 24px. Pasaron la búsqueda/sin resultados/limpiar, el bloqueo por consentimiento y la activación, el cierre real del diálogo con Escape y la restauración del foco a la acción que lo inició. Las primeras comprobaciones complementarias necesitaron el idioma correcto después de volver a montar una vista y esperar a que el diálogo realmente se desmontara y se restaurara el foco, en lugar de una pausa fija de 350ms; las aserciones finales basadas en eventos pasaron. No hubo solicitudes HTTP(S) ni errores del navegador durante la comprobación específica de interacciones.

La evidencia de movimiento está activa: papel `register`, filas `row-register`, navegación `rule-register`, panel `rail-enter`, lámina `foil-register`/`foil-drift`; los botones conservan sus transiciones de transformación/fondo/borde de 180ms. La entrada expresiva tuvo **12 animaciones en ejecución**; `?still=1` tuvo **cero**. Se inspeccionaron capturas en memoria en cuentas a 1280/tema claro, roles a 1280/tema oscuro, cuentas a 390/tema oscuro y activación a 390/tema claro. No se escribieron capturas. El TSX fuera de su plantilla CSS permanece idéntico byte por byte a r10, incluidas las rutas, controles, datos, lógica de estado y opciones de montaje; los fotogramas clave, curvas de aceleración y duraciones no cambiaron.

No se certifican lint/tipos/compilación/pruebas de producción, autorización de API, vencimiento/invalidez segura de tokens, persistencia, concurrencia, enrutamiento automático, aprobación legal, sesiones de lector de pantalla ni compatibilidad entre navegadores mediante esta exploración de diseño estático.

## 12. Preguntas abiertas, supuestos e impacto

P: ¿Qué entidad legal, correo electrónico de contacto para asuntos de derechos y URL de la política deben reemplazar los campos entre corchetes antes de que usuarios externos reales activen su cuenta? Responsable de la decisión: David con el equipo legal de Sempertex. Se conserva la redacción aprobada del aviso de borrador; esta pregunta se refiere solo a sus marcadores de posición aún sin resolver.

Se conserva el comportamiento confirmado en lugar de reabrirlo: un rol por cuenta; los cinco roles del sistema, incluidos tres planes acumulativos; contraseñas de ocho caracteres; indicación de bloqueo de quince minutos; invitación de siete días y restablecimiento de 24 horas; enlaces de un solo uso generados por el administrador; sin correo electrónico automático; nueva aceptación cuando cambie el aviso; protección del trabajo guardado/del último administrador; los roles personalizados requieren un permiso.

Los futuros consumidores afectados son SP-2 T2.1 (copiar el contrato aprobado posteriormente), T2.3 (inicio de sesión/activación/restablecimiento/aviso), T2.4 (menú de cuenta/cambio de contraseña), T2.5 (cuentas/invitación/acciones/roles), T2.6 (integración), T2.7 (revisión visual) y T2.8 (auditoría). **Este cambio de r10 → r11 es una iteración visual compatible:** las rutas, el contenido, los datos, el comportamiento, la estructura adaptable, el foco y el movimiento permanecen sin cambios; cambian los radios, las reglas decorativas, los rellenos internos y el espaciado. T2.3–T2.5 deben aplicar los tokens propuestos de formas/espaciado y T2.7 debe volver a renderizar la revisión seleccionada. La compatibilidad canónica y la aprobación de implementación siguen sin determinarse hasta que se elija y finalice una dirección. La acción existente para completar el cambio de contraseña en Mi cuenta pide a la persona que vuelva a iniciar sesión, mientras que la aceptación actual de T2.2 requiere automáticamente una sesión nueva del navegador; esta discrepancia de comportamiento preexistente queda fuera de esta iteración limitada a las formas y el Planificador/finalizador debe resolverla antes de la aprobación canónica. Esta exploración no redirige consumidores ni otorga aprobación. Solo se escriben los cuatro archivos específicos de la revisión r11 de esta dirección y el RESULT requerido de la delegación. Las fuentes de r10, el comportamiento compartido de r11, el par canónico, las otras direcciones, los planes y los repositorios permanecen sin cambios.
