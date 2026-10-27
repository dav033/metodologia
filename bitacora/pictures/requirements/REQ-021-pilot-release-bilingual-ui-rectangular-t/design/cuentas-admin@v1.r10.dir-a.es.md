---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r10.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
chosen_thumbnail: cuentas-admin@v1.r10.dir-a.html.candidate-1.html
---

# Parte de acceso — direction A

## 1. Identidad y trazabilidad

**Exploración independiente; a la espera de la selección del propietario.** Esta nota no es el contrato canónico de doce secciones ni un insumo de implementación aprobado. El contrato final `cuentas-admin@v1` aún requiere selección y finalización junto con el plan. No se editó ningún contrato compartido, plan, historial ni repositorio.

Fuentes leídas: `SPEC.md` (`65b1e5ecc06f20d9`), `PLAN.md` (`cc7e53f2abf3c23c`), `PLAN.json` (`7a2c833a7e711508`) y el archivo compartido `cuentas-admin@v1.r10.behavior.md` (`c665ab01443531a7`). Estos hashes identifican la instantánea de origen, no una aprobación. SP-2 cubre R1 cuentas invitadas, R3 administración de roles y R16 planes de acceso. Sus contratos consumidos de SP-1 son `account-service@1`, `session-guard@1` y `permission-map@1`.

## 2. Propósito, concepto y elemento memorable

**Concepto: una hoja de producción para eventos.** El administrador responde: «¿Quién integra el equipo, qué herramientas puede usar y qué debo cambiar?». Cada fila reglada reúne el nombre, correo electrónico, empresa, rol asignado, estado, último acceso y acción de administración de la persona. La franja de anotaciones explica los tres planes acumulativos mientras el trabajo permanece en el registro. Los nombres, empresas, direcciones de correo electrónico, fechas y cantidades son datos de ejemplo ilustrativos; los dominios `.example` son ejemplos reservados.

**Elemento memorable: registro cinético.** La página se acomoda en su posición de trabajo mediante varias direcciones deliberadas: el papel desciende, los registros se desplazan horizontalmente, la franja de anotaciones entra desde arriba y, por último, una costura metalizada queda estampada en su lugar. Los cambios de estado trazan un breve movimiento de registro. El contenido legible permanece visible durante estas transformaciones. La idea se inspira en alinear una hoja de producción y revisar una instalación de globos terminada; no imita una credencial física de acceso ni una carpeta de proyecto.

## 3. Candidatos nuevos y registro visual

Las dos miniaturas visuales originales se crearon antes del TSX. Incluyen CSS adaptable, tipografía de visualización integrada para uso sin conexión y variantes claras/oscuras del sistema; son estudios de composición, no alternativas de fragmentos para la maqueta completa.

- **Elegido: [candidato 1](cuentas-admin@v1.r10.dir-a.html.candidate-1.html)** — un encabezado amplio, filas de cuentas completas y comparables, y una franja estrecha de anotaciones sobre los planes. Hace visible el trabajo recurrente del administrador y se extiende de forma natural al editor de roles.
- [Candidato 2](cuentas-admin@v1.r10.dir-a.html.candidate-2.html) — una columna de despacho a la izquierda y una hoja sobredimensionada para la persona seleccionada. Da demasiada importancia a una sola persona y repite una composición de navegación lateral ya representada en el registro visual.

El registro incluye SP-4 `proyectos@v1.r8.dir-a/b/c.md` y SP-3 `taller-esenciales@v1.r7.dir-c.md`. El pliegue de escenas en línea del archivo, el marco espacial, las carpetas de muestras y las ranuras de silicona del taller siguen siendo elementos distintos de este amplio registro de cuentas y hoja de permisos. El símbolo de anillo y punto de Pictures, el lenguaje de productos de Sempertex, los planes acumulativos, los nombres semánticos de roles y los controles de trabajo claros mantienen la continuidad. Los nuevos colores exploratorios son propuestas, sujetas a la selección del propietario.

## 4. Ocho ejes, lenguaje visual y componentes reales

| Eje | Expresión actual |
|---|---|
| Concepto | Una hoja de producción para eventos: las personas se registran con sus herramientas exactas, estado de acceso y siguiente acción. El símbolo de anillo y punto de Pictures y la costura metalizada conectan la página operativa con las instalaciones de Sempertex. |
| Diseño | Encabezado amplio y asimétrico (título grande y condensado a la izquierda, total de cuentas actualizado a la derecha), regla horizontal de navegación, registro reglado de ancho completo con una franja estrecha de anotaciones sobre los planes; la lista de roles y la hoja de permisos reemplazan el registro sin una cuadrícula de tarjetas de panel. En teléfonos, el registro aparece antes de las anotaciones sobre los planes. |
| Navegación | Botones neutrales de rutas en línea Cuentas / Roles y permisos / Mi cuenta, diálogos contextuales Manage para cada persona y un menú de cuenta con nombre; el acceso exclusivo por invitación no tiene una ruta de registro abierto. Los selectores de vista previa nativos quedan fuera del producto. |
| Tipografía | DejaVu Sans Condensed Bold integrada como Dispatch, visualización de 38–68 px, títulos de sección y diálogos de 23–28 px; Adwaita Sans integrada como Work a 14–16 px, Adwaita Mono integrada como Measure a 11–13 px para marcas de tiempo de acceso y detalles de la edición. El texto en inglés y español se adapta al espacio. |
| Densidad | Filas compactas y regladas de cuentas con nombre/correo electrónico/empresa/rol/estado/último acceso/acciones, campos planos de papel, controles cuadrados con esquinas de 2 px y relleno generoso en los contenedores: 24 px en escritorio y 20 px en teléfono; sin mosaicos de indicadores clave. |
| Componentes | Button, Input, Checkbox y Skeleton reales de shadcn/Base UI instalados; Dialog y AlertDialog de Animate UI con contención del foco. Filas personalizadas del registro, encabezado de producción, conjuntos de campos de permisos y costura metalizada. Selectores nativos de rol/estado/idioma, sin alternativas de fragmentos. |
| Color | Propuesta de exploración local basada en los roles semánticos de Pictures: acero frío #e4ebf2, tinta #112c48, cobalto #12489e; azul marino oscuro #0b1c2e con acción #a6caff. El cobre metalizado se limita a una muestra de material de Sempertex; el estado de la cuenta usa los significados de verde/ámbar/rojo. La navegación neutral usa texto y una regla, no el color de acento. |
| Movimiento | Registro cinético preciso, cubic-bezier(.76,0,.24,1), hojas expresivas de 480 ms con desplazamientos de filas de 55 ms y controles de 180 ms; registro del papel, registro de filas, registro de reglas, contramovimiento de la franja, estampado metalizado de 900 ms, registro metalizado ambiental de 6 s, estampado de estado, barrido de esqueleto y desplazamiento de flecha al pasar el cursor o presionar. Los perfiles sutil/natural reducen los tiempos. El contenido permanece visible durante el movimiento. Reducir/sin movimiento elimina toda animación; suspensión cuando está oculto o fuera de pantalla. |

Por qué esta estructura funciona: las cuentas son información de producción. Un título grande y el total actualizado de cuentas establecen el alcance, mientras un único registro reglado reúne los datos de trabajo de cada persona. La tipografía expresiva se reserva para los títulos; las etiquetas pequeñas y los controles usan Adwaita Sans. La muestra metalizada tiene una costura inflable cosida, un color cobrizo discreto y su propio movimiento de registro. Conecta con los materiales del decorador sin competir con los datos de las cuentas.

Se inspeccionaron `AGENTS.md`, `src/app/globals.css` y los patrones de `src/components/admin/AdminTabs.tsx` de `t12` y `asesor` solo en modo de lectura. El producto actual asigna nombres de tokens en español a los roles de shadcn existentes. La exploración conserva esas responsabilidades semánticas y propone los siguientes valores locales; no modifica los tokens de producción:

| Rol de Pictures | Rol del kit | Mapeo exploratorio claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#e4ebf2` / `#0b1c2e` |
| `--superficie` | card / popover | `#f9fbff` / `#142b42` |
| `--texto` | primeros planos | `#112c48` / `#e6effa` |
| `--texto-suave` | primer plano atenuado | `#405771` / `#b6c9df` |
| `--superficie-2` | secondary / muted | `#dce5ef` / `#203b54` |
| `--acento`, `--sobre-acento` | primary / primer plano de primary | `#12489e`, blanco / `#a6caff`, `#0b1c2e` |
| `--borde` | border | `#8292a4` / `#829cb5` |
| Borde de control accesible | input | `#64788f` / `#96aec7` |
| `--exito`, `--aviso`, `--error` | success / warning / destructive | `#205d43`, `#755000`, `#a62434` / `#a1dfbe`, `#f2d591`, `#ffafb8` |
| Lámina metalizada propuesta, solo para materiales | `--foil`, `--foil-ground` | `#8c2b15`, `#f3c2ac` / `#ffb899`, `#51382c` |

Componentes del manifiesto instalados: `shadcn:button` predeterminado/contorno/destructivo, `shadcn:input` texto/correo electrónico/contraseña, `shadcn:checkbox` marcado/sin marcar/deshabilitado, `shadcn:skeleton` carga, `shadcn:dialog` invitación/administración/enlace y `shadcn:alert-dialog` eliminación permanente. Sus importaciones son `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Dialog, AlertDialog y Checkbox usan la implementación instalada de Animate UI/Base UI. `mountMockup`/`useMockup` provienen de `@kit/mockup`; `useMotionProfile` proviene de `@kit/motion`. El registro personalizado de cuentas, la franja de planes, el encabezado, los conjuntos de campos de permisos y la costura son composiciones personalizadas con nombre; no se presentan como componentes estándar de biblioteca. No se usaron fragmentos alternativos, instalaciones de paquetes ni recursos descargados.

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

A **1101 px o más**, el registro principal tiene cuatro columnas alineadas y una franja de anotaciones de 280 px; un título amplio y una celda de edición de 300 px comparten el encabezado. La hoja de roles tiene un selector de roles de 200 px y un editor de permisos agrupados. El relleno exterior principal es de 40 px y el de la hoja es de 24 px.

A **761–1100 px**, el relleno exterior pasa a 28 px, la franja a 220 px, los filtros usan dos columnas con la búsqueda a todo el ancho, las acciones de cuenta pasan debajo de cada fila y los grupos de permisos se muestran en una sola columna.

A **760 px o menos**, la hoja y la franja de anotaciones se apilan; los rellenos exterior y de la hoja son de 20 px. Las identidades de las cuentas ocupan todo el ancho de su fila, el rol y el estado comparten una fila secundaria y cada acción de administración aparece a continuación. Los filtros, la selección de roles, los permisos, los metadatos de identidad y los campos de formulario se apilan. La navegación se ajusta en el flujo. Los diálogos conservan un relleno interior de 24 px y márgenes de 16 px respecto a la ventana, y permiten desplazamiento vertical cuando superan su altura. Los selectores nativos siguen siendo nativos en ambos temas.

Ancho mínimo compatible: 360 px, sin desplazamiento horizontal de la página. Las etiquetas en español e inglés se reajustan. Todas las secciones del producto y el pie comparten el eje exterior; los formularios y avisos comparten el eje interior de su hoja.

## 10. Accesibilidad y objetivos de movimiento

Los objetivos son WCAG 2.2 AA para las interacciones aplicables: contraste de texto de 4.5:1, bordes de controles relevantes y foco de 3:1, anillo de foco visible de tres píxeles con un desplazamiento de cuatro píxeles, acciones de 44 px, campos y casillas con nombres programáticos, grupos etiquetados y errores/resultados anunciados. El estado de las casillas de roles del sistema sigue siendo visualmente legible aunque estén deshabilitadas. Los efectos destructivos se explican antes de la confirmación; para eliminar una cuenta se debe confirmar con el correo electrónico exacto.

Los ID de permisos se normalizan en identificadores sin espacios para que `aria-labelledby` generado por Base UI vincule cada casilla con su etiqueta. La búsqueda y los formularios conservan el foco mientras se escribe. Dialog/AlertDialog usan las primitivas reales instaladas para contener el foco, volver inerte el fondo y restaurar el foco al cerrar. La conformidad con lectores de pantalla es un objetivo; las mediciones del navegador por sí solas no la certifican.

Vocabulario de movimiento: registro preciso de la hoja en 480 ms, desplazamientos de filas de 55 ms y movimiento de controles de 180 ms; natural de 300/140 ms, sutil de 160/100 ms. El papel, las filas, las reglas, la franja, la entrada del efecto metálico, el efecto metálico ambiental, la respuesta de estado, el barrido del esqueleto y el movimiento de flechas al pasar el cursor/presionar son comportamientos distintos. La secuencia del efecto metálico ambiental dura seis segundos, solo transforma elementos, se pausa fuera de pantalla, al pasar el cursor y cuando la pestaña está oculta. `useMotionProfile()` proporciona el perfil y el estado de movimiento reducido. El movimiento reducido, Quieto y `?still=1` eliminan los desplazamientos y efectos repetitivos, y conservan el mismo contenido y las mismas acciones. Las animaciones de navegación/filtros desplazan el contenido legible en vez de recortarlo. No se usan fundidos de texto por opacidad ni destellos.

## 11. Criterios de aceptación observables y verificación

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1101+ | cuentas normal | Nombre/correo electrónico/empresa, rol, estado, último acceso y Administrar comparten un registro delimitado por reglas; los recuentos provienen de las mismas filas. |
| A-02 | 360–760 | cuentas normal | La identidad ocupa todo el registro; el rol/estado y Administrar se reajustan debajo sin desplazamiento horizontal de la página. |
| A-03 | 360+ | error de inicio de sesión | Un mensaje genérico incluye la espera de quince minutos y no revela diferencias por existencia/estado de la cuenta. |
| A-04 | 360+ | activación normal | Ambos campos de contraseña y el aviso completo aparecen antes del consentimiento; Activar está deshabilitado hasta que se marque el consentimiento. |
| A-05 | 360+ | enlace vencido | No aparece la entrada de contraseña y la opción visible de recuperación indica que se solicite un enlace nuevo al administrador. |
| A-06 | 360+ | invitación | Nombre/correo electrónico/empresa opcional/un rol aparecen antes de generar el enlace; se rechaza el correo duplicado. |
| A-07 | 360+ | recepción del enlace | Se muestran la acción de copiar, el uso único/la vigencia y la invalidación de enlaces anteriores; al cerrar, se elimina el comprobante. |
| A-08 | 360+ | trabajo guardado / último administrador | El rechazo explica la regla y el envío destructivo permanece deshabilitado. |
| A-09 | 360+ | eliminación de cuenta | Se debe introducir el correo electrónico exacto de una cuenta sin trabajo antes de habilitar Eliminar permanentemente. |
| A-10 | 360+ | editor de roles | Los cinco roles del sistema son de solo lectura, las etiquetas de permisos agrupados son accesibles y los roles personalizados requieren al menos un permiso. |
| A-11 | 360+ | actualización del aviso | No aparecen otras rutas del producto; se puede acceder al consentimiento o al cierre de sesión; los marcadores de posición siguen siendo explícitos. |
| A-12 | 360+ | Mi cuenta | La identidad coincide con la del menú de cuenta; la contraseña actual precede a las nuevas contraseñas y al texto sobre el cierre de sesión. |
| A-13 | 360+ | oscuro / claro | Los bordes de entrada, las casillas personalizadas, las acciones delineadas y el foco son visibles sobre sus superficies reales. |
| A-14 | 360+ | reducido / expresivo | El registro expresivo se puede medir; el modo reducido/quieto no tiene animaciones en curso y conserva todas las acciones. |
| A-15 | 360+ | diálogo abierto / cerrado | El foco permanece dentro del diálogo real; al cerrar la invitación con Escape, se restaura el foco en la acción que la inició. |

Se usa el entorno local sin restricciones dentro del límite de archivos asignado; esta nota no afirma nada sobre el aislamiento del sistema operativo. La cadena de herramientas informó **instaladas/compiladas, 96/96 entradas disponibles**. El comando del generador sin conexión se ejecutó mediante ruta absoluta solo en este TSX y este HTML: **4474 KB, 2150 archivos fuente incluidos**, código de salida 0. Las fuentes están incrustadas desde archivos TTF locales ya instalados; no hay fuentes ni imágenes externas, ni solicitudes en tiempo de ejecución.

`contrast.py` sobre este resultado: **158 pares en tema claro y oscuro, todos aprobados**, código de salida 0.

Se conserva el historial de auditoría con fidelidad: la primera auditoría por muestreo detectó un problema de contraste en el texto del efecto metálico y un eje visualmente confuso en el editor de roles. La siguiente revisión completa detectó 79 problemas de alineación móvil, en su mayoría consecuencias repetidas de una columna de mensajes con icono/texto. Se corrigieron con texto más oscuro para el efecto metálico, una hoja de permisos más ancha, mensajes apilados a todo el ancho en teléfonos y texto de estado alineado a la izquierda. Una auditoría posterior se interrumpió antes de terminar para corregir los ID de permisos que contenían espacios; no se cuenta como aprobada. Una aserción complementaria temprana comprobó una entrada oculta de Base UI en vez de su casilla de rol visible, y una aserción de cierre se ejecutó antes de que el diálogo terminara de desmontarse; ambas comprobaciones se corrigieron sin desactivar verificaciones del producto. El estilo de movimiento reducido también reveló y permitió corregir una regla que anulaba el centrado del diálogo antes de las comprobaciones aprobadas.

Una revisión visual específica de 476 casos no encontró problemas de contraste, contenido no textual, alineación, relleno ni desbordamiento. La auditoría final completa de la interfaz renderizada aprobó **476/476 combinaciones, 19,738 mediciones de texto, 1,435 paradas de foco**, código de salida 0, tras el último ajuste del texto de éxito específico de cada vista.

`RESULT: PASS — sin problemas de contraste, contenido no textual, foco, alineación, relleno ni desbordamiento`

SHA-256 del HTML auditado final: `a1411ee67ba12b53ca686732d8f4129b2d54ec828a50c10b3556fc48ff0b4cff`.

La prueba rápida del navegador aprobó búsqueda/sin resultados/borrar, invitación y comprobante de un solo uso, rechazo de eliminación por trabajo asociado, control del consentimiento, validación/guardado de activación y rol personalizado, con **cero errores del navegador y cero solicitudes HTTP(S)**. Otras comprobaciones aprobaron la eliminación de cuenta con correo confirmado, recuperación de enlace vencido, restauración del foco con Escape y **48 casos adaptables en español e inglés** a 360/768/1024 px en ambos temas, sin desbordamiento de página. El modo expresivo tenía **12 animaciones en curso** al medir la entrada; `?still=1` tenía **cero**. Se inspeccionaron en memoria capturas de pantalla de cuentas en tema claro a 1280 px, roles en tema oscuro a 1280 px, cuentas en tema claro a 390 px y activación en tema oscuro a 390 px. No se guardaron capturas de pantalla adicionales.

`compare_directions.py` frente a r10 A/B/C devolvió **código de salida 0, ok=true, evidence_ok=true, sin selectores faltantes**. Similitud de diseño A/B: **0.006**; A/C: **0.006**; ninguno de esos pares compartió tipografía, navegación ni movimiento medidos. B/C fue 0.053, con navegación compartida únicamente. Los selectores de movimiento JSON coincidieron con elementos que tenían animaciones/transiciones reales. Prefijos de las instantáneas de comparación final: A `a1411ee67ba12b53`, B `a93dc792617df618`, C `179b1593ee5d3c1b`. Estas son las instantáneas observadas por esta comparación; las exploraciones paralelas siguen bajo responsabilidad independiente.

Esta exploración de diseño estático no certifica lint/tipos/compilación/pruebas de producción, autorización de API, caducidad/invalidez seguras de tokens, persistencia, concurrencia, enrutamiento automático, aprobación legal, sesiones con lectores de pantalla ni compatibilidad entre navegadores.

## 12. Preguntas abiertas, supuestos e impacto

P: ¿Qué entidad legal, correo electrónico de contacto sobre derechos y URL de política deben reemplazar los campos entre corchetes antes de que usuarios externos reales puedan activar sus cuentas? Responsables de la decisión: David y el equipo legal de Sempertex. Se conserva la redacción aprobada del borrador del aviso; esta pregunta se refiere únicamente a los marcadores de posición aún sin resolver.

Se conserva el comportamiento confirmado sin volver a abrirlo: un rol por cuenta; los cinco roles del sistema, incluidos tres planes acumulativos; contraseñas de ocho caracteres; indicación de bloqueo durante quince minutos; invitación de siete días y restablecimiento de 24 horas; enlaces de un solo uso generados por el administrador; sin correo automático; nueva aceptación cuando cambie el aviso; protección ante trabajo guardado/último administrador; los roles personalizados requieren un permiso.

Los consumidores futuros afectados son SP-2 T2.1 (copiar el contrato aprobado posteriormente), T2.3 (inicio de sesión/activación/restablecimiento/aviso), T2.4 (menú de cuenta/cambio de contraseña), T2.5 (cuentas/invitación/acciones/roles), T2.6 (integración), T2.7 (revisión visual) y T2.8 (auditoría). **La compatibilidad no se determinará hasta seleccionar una dirección y finalizar el contrato canónico.** Si se selecciona esta composición, será necesario implementar su jerarquía, reajuste, material/movimiento y expectativas de foco, y conservar el comportamiento compartido. Esta exploración no redirige consumidores ni concede aprobación. Solo se escriben los seis archivos de diseño específicos de la revisión de esta dirección y el RESULT requerido de delegación.
