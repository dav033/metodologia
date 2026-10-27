---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r12.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
source_revision: r11.dir-a
feedback: "2026-10-27T08:36 direction=a: remove sidebar/material card, sober account title, Spanish copy, product system"
---

# Parte de acceso — direction A

## 1. Identidad y trazabilidad

Iteración unidireccional **r12 de r11 A**, estado **draft**, a la espera de que el propietario la seleccione junto con el plan. Esta nota de dirección de doce secciones no es el contrato canónico ni una entrada de implementación aprobada. El nombre de la dirección sigue siendo “Parte de acceso”. No se crean nuevas direcciones, miniaturas, contratos compartidos, planes ni cambios en el repositorio.

Fuente de comportamiento: `cuentas-admin@v1.r12.behavior.md` SHA-256 `3fb1bbc78c83aae3`. Instantáneas de contexto: `SPEC.md` SHA-256 `65b1e5ecc06f20d9`; `PLAN.md` SHA-256 `cc7e53f2abf3c23c`; `PLAN.json` SHA-256 `7a2c833a7e711508`. SP-2 cubre las cuentas solo por invitación R1, la gestión de roles R3 y el acceso asignado R16. Los contratos existentes de SP-1 siguen siendo account-service@1, session-guard@1 y permission-map@1. Las tareas de diseño son T2.1, T2.3–T2.5 y la revisión visual T2.7; no se agrega ninguna ruta de ingeniería al alcance del diseño.

## 2. Propósito, concepto y elemento memorable

El administrador responde «¿Quién tiene acceso, qué rol tiene y qué hay que cambiar?». Cada fila delimitada mantiene juntos el nombre, el correo electrónico, la empresa opcional, el rol asignado, el estado, el último acceso y la acción contextual. Los formularios de acceso gestionan el inicio de sesión, la activación, el restablecimiento y la aceptación obligatoria del aviso; Mi cuenta identifica a la persona y permite cambiar su contraseña.

La inscripción cinética existente sigue siendo la interacción memorable: el panel de trabajo se asienta en vertical, las filas se inscriben en horizontal y la respuesta visual dibuja un breve trazo de inscripción. La barra lateral del plan y la tarjeta “De la idea al montaje” eliminadas no tienen reemplazo. Esta es una superficie de administración, con títulos de tareas habituales y sin eslogan ni total decorativo. Todas las filas y operaciones se identifican como datos simulados; las descripciones neutrales de cuentas y los datos de prueba `@prueba.local` reemplazan a personas, empresas y fechas ficticias. Los totales de filas siguen derivándose de la lista visible de datos de prueba.

## 3. Composición preservada y registro visual

Se partió de una copia de `cuentas-admin@v1.r11.dir-a.tsx`. Se aplicaron los cuatro comentarios del propietario de 2026-10-27T08:36: se eliminó por completo la barra lateral “Cada persona. Sus herramientas.” y su lista de planes/herramientas; se eliminó la tarjeta de material; se amplió el registro de cuentas al ancho disponible; se reemplazaron los eslóganes visibles y “05 Pilot accounts” por títulos de página habituales; se estableció ES como idioma inicial de inspección, con EN solo cuando se selecciona; se reemplazaron las identidades y fechas de ejemplo inventadas por datos neutrales. Se mantienen la navegación existente Cuentas / Roles y permisos / Mi cuenta, los diálogos contextuales, las formas redondeadas, las etiquetas de estado, los permisos y los flujos de acceso.

Se inspeccionaron los archivos Markdown y HTML inmutables de los elementos relacionados `taller-esenciales@v1` y `proyectos@v1`. Su Markdown establece la paleta semántica existente de Pictures, la tipografía Geist/system-sans, la navegación neutral y el vocabulario de cuentas/encabezado. Su HTML empaquetado actual aún contiene paletas, tipografía y textos principales exploratorios anteriores que discrepan de esos contratos escritos. Esta revisión sigue las fuentes de tokens y tipografías de producción, así como los contratos escritos de los elementos relacionados, en lugar de importar esas divergencias. No se modifica ningún archivo relacionado. La dirección conserva explícitamente la navegación horizontal existente y la composición de registro de trabajo, tal como se solicitó.

Referencias del producto en modo de solo lectura: `src/app/globals.css`, `src/app/layout.tsx`, `src/app/login/{page,LoginForm}.tsx`, `src/components/admin/AdminTabs.tsx` y `src/components/ui/shell/CabeceraApp.tsx` de ambos árboles de trabajo. El inicio de sesión existente es un formulario de contraseña; los controles de correo electrónico/invitación/rol son las adiciones incluidas en el alcance. La administración existente usa un título sobrio y pestañas integradas en el flujo; se reutiliza la marca de anillo y punto del encabezado, junto con el menú de cuenta requerido. No se propone una marca, tipografía de exhibición ni paleta exploratoria. La producción y los demás cambios locales quedan intactos.

## 4. Ocho ejes, lenguaje visual y componentes reales

| Eje | Expresión actual |
|---|---|
| Concepto | Un registro operativo de acceso: cuentas invitadas, rol asignado, estado de acceso y siguiente acción de administración. Sin paneles promocionales ni promoción de planes. |
| Diseño | Encabezado compacto de Pictures/Sempertex, título de página sobrio de 24px, regla horizontal de rutas preservada y un registro de cuentas delimitado a todo el ancho. Roles conserva el selector y la hoja de permisos agrupados. Sin barra lateral de anotaciones, tarjeta de material ni contador decorativo de cuentas. |
| Navegación | Se conserva la navegación horizontal neutral Cuentas / Roles y permisos / Mi cuenta, los diálogos contextuales de cuenta y el menú de cuenta con nombre. El acceso solo por invitación no tiene ruta de registro. Los selectores de planificación quedan fuera del contenedor del producto. |
| Tipografía | Geist Sans y Geist Mono de producción, incorporadas desde la compilación local existente. Título de página de 24px, títulos de sección de 20px, texto de 14–16px y metadatos de 11–13px; sin tipografía de exhibición ni contenido principal. ES es el idioma inicial; EN aparece mediante el selector de idioma. |
| Densidad | Se conserva el relleno de 24px de las filas de cuenta, márgenes internos del área de trabajo de 28px en escritorio / 20px en teléfono, paneles de 32px, superficies internas de 24px, campos de 18px, casillas de verificación de 8px y controles/etiquetas de estado en forma de píldora. El registro de cuentas usa el ancho liberado al eliminar la barra lateral. |
| Componentes | Button, Input, Checkbox, Skeleton, Dialog y AlertDialog de shadcn/Base UI instalados, compuestos como filas de cuenta y conjuntos de campos de permisos. Marca de anillo y punto de producción; paneles redondeados, estados semánticos en forma de píldora y navegación neutral. El texto de cierre del diálogo sigue el idioma ES/EN. |
| Color | Paleta exacta de Pictures `globals.css`, asignada como en proyectos@v1: claro #faf9fc / #ffffff con acciones #6d3fe0; oscuro #0b0c10 / #16181f con acciones #9479ff y primer plano #120b24. Tokens existentes para éxito/advertencia/error; los bordes de entrada son alias de texto-tenue. Sin paleta exploratoria. |
| Movimiento | Se conserva la inscripción cinética: cubic-bezier(.76,0,.24,1), inscripción de papel/filas/regla/estado de 480ms, desfases de fila de 55ms y controles de 180ms, movimiento natural de 300/140ms y sutil de 160/100ms. Se mantienen el barrido de Skeleton y el desplazamiento de flecha al pasar el cursor/presionar; se elimina el movimiento retirado de la barra lateral/laminado. El modo de movimiento reducido/estático desactiva el movimiento y las pestañas ocultas pausan la animación. |

La asignación de roles del proyecto proviene de `globals.css` de ambos repositorios y de los roles compartidos correspondientes en proyectos@v1. Todos los valores siguientes ya existen en el producto; no se introduce ningún color nuevo.

| Fuente de Pictures | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, primer plano primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | hover primario, anillo | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | borde decorativo, regla | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | entrada (alias de control accesible existente del elemento relacionado) | #766c85 / #8a91a0 |
| `--superficie-suave` | superficie suave de rol seleccionado | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | éxito, éxito suave | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | advertencia, advertencia suave | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45, #ffeaec / #ff979f, #43252a |
| Primer plano destructivo existente | primer plano destructivo | #ffffff / #3a0f13 |
| `--fondo` | informativo suave, primario suave | #faf9fc / #0b0c10 |

La tipografía es la Geist Sans / Geist Mono real de producción, incorporada sin conexión desde los recursos WOFF2 latinos locales de la compilación Next t12 existente. No se descarga ninguna fuente ni recurso. H1 es de 24px/1.25 en todos los anchos, los títulos de sección son de 20px/1.3 en escritorio, el texto es de 14–16px y los metadatos de 11–13px; la tipografía monoespaciada se limita a identificadores/metadatos. Se conservan de r11 el tamaño de las secciones en teléfono y las formas amplias. Los roles de forma de R11 siguen siendo `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. Son las opciones de forma conservadas por el propietario en el borrador, no nuevas opciones de paleta ni tipografía de producción. El relleno de papel y diálogo se mantiene en 28px en escritorio y 20px para el papel / 24px para diálogos en teléfono; las filas se mantienen en 24px en escritorio / 20px en teléfono.

Componentes instalados: `shadcn:button` default/outline/destructive, `shadcn:input` text/email/password, `shadcn:checkbox` checked/unchecked/disabled, `shadcn:skeleton`, `shadcn:dialog` y `shadcn:alert-dialog`; las importaciones son `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Las primitivas instaladas de Base UI/Animate UI proporcionan contención del foco y confirmación de acciones destructivas. El componente real DialogClose se recompone con un nombre accesible traducido para que ES no exponga el texto en inglés “Close” de la biblioteca. Las filas de cuenta similares a una tabla, la hoja de roles, los conjuntos de campos y el encabezado son composiciones personalizadas existentes; los selectores nativos de idioma/rol/estado siguen siendo nativos. `@kit/mockup` proporciona mountMockup/useMockup y `@kit/motion` proporciona useMotionProfile. Sin fragmentos, instalación ni constructor alternativo.

## 5. Navegación e interacción

Las siete vistas nativas de la vista previa son Cuentas, Roles y permisos, Iniciar sesión, Activar invitación, Restablecer contraseña, Mi cuenta y Nuevo aviso obligatorio. La barra **Mockup** visible de la plantilla conserva `view`, `state`, `scene`, `theme` y el selector de movimiento expresivo por defecto. El producto tiene su propio selector nativo de idioma ES/EN, configurado en ES para este artefacto de planificación; EN es una opción explícita del selector.

Las vistas con sesión iniciada tienen rutas de cuenta neutrales integradas en el flujo y un menú de cuenta que muestra el nombre del administrador de datos de prueba neutrales y su rol, con Mi cuenta y Cerrar sesión. El resumen en teléfono muestra el nombre; al abrirlo se muestran el rol y las mismas acciones. La identidad de Mi cuenta coincide con admin@prueba.local en el menú de cuenta; la activación identifica a plan3@prueba.local. En el producto, el aviso de invitación sigue inicialmente el idioma del navegador y muestra el idioma seleccionado; esta vista previa se abre deliberadamente en ES para que la inspeccione el propietario y permite seleccionar EN. La vista de aviso obligatorio oculta el resto de la navegación del producto y ofrece aceptar o cerrar sesión. Los controles de vista previa permanecen fuera de esa barrera del producto.

La gestión es contextual a la cuenta seleccionada. Los diálogos conservan el foco del teclado y lo devuelven al cerrarse. Los diálogos de invitación, gestión y enlace de un solo uso permiten cerrar con Escape; las eliminaciones de cuentas/roles usan AlertDialog y una acción explícita Cancelar. La vista previa simula resultados localmente y no implementa enrutamiento autenticado, emisión de tokens ni comprobaciones de permisos.

## 6. Flujos conservados

1. **Iniciar sesión:** correo electrónico invitado y contraseña → página solicitada permitida, primera herramienta permitida o Mi cuenta si el rol no tiene herramientas. El caso de error usa un mensaje genérico para contraseña incorrecta, correo electrónico desconocido, cuenta desactivada y correo electrónico bloqueado; siempre explica la espera de quince minutos después de varios intentos fallidos. Para recuperar la contraseña, se solicita al administrador un enlace de un solo uso válido por 24 horas; no se incorpora el envío automático de correos electrónicos ni el registro público.
2. **Activar:** nombre/correo electrónico invitado → contraseña nueva y confirmación, mínimo de ocho caracteres → aviso completo en el idioma del navegador, versión 1 → aceptación explícita sin marcar de antemano → activación y destino directo a la primera herramienta permitida con sesión iniciada. Si el enlace se usó, venció o se reemplazó, se solicita un enlace nuevo emitido por el administrador. La invitación tiene una vigencia de siete días.
3. **Actualizar aviso:** la versión nueva bloquea todas las demás páginas del producto hasta que se acepte. El texto de finalización indica la obligación de almacenar la versión y la fecha. El texto de aviso proporcionado se conserva exactamente en ES/EN, incluidos los marcadores legales entre corchetes.
4. **Mi cuenta:** consultar identidad personal y rol → contraseña actual más contraseña nueva dos veces → cambiar la contraseña y volver a iniciar sesión. Se muestran datos de ejemplo de la versión y fecha de aceptación. Cambiar la contraseña finaliza las sesiones.
5. **Invitar/administrar:** buscar y filtrar → indicar nombre, correo electrónico, empresa opcional y un rol → generar → copiar un enlace que se muestra una sola vez → cerrar. Se rechaza un correo electrónico registrado. Para una cuenta existente, cambiar el rol, desactivar/reactivar, generar un enlace nuevo de invitación o restablecimiento, o solicitar su eliminación. Los enlaces nuevos invalidan los enlaces anteriores sin usar del mismo tipo; esa consecuencia se informa antes de generarlos y en el comprobante. Si se rechaza el acceso al portapapeles, se explica cómo seleccionar y copiar manualmente.
6. **Eliminar:** si hay trabajo guardado, se rechaza la eliminación sin modificar la cuenta (`CUENTA_CON_TRABAJO`); no se puede eliminar ni desactivar al último administrador, ni quitarle el rol de administrador. Para eliminar de forma permanente una cuenta sin trabajo guardado, se requiere escribir su correo electrónico exacto. El gasto de IA se conserva sin datos personales como «Cuenta eliminada». La maqueta ilustra la opción; no garantiza la integridad de la base de datos.
7. **Roles:** seleccionar uno de cinco roles de sistema de solo lectura para revisar permisos agrupados por herramienta, o crear/editar un nombre personalizado y una selección de casillas. Se rechaza un rol personalizado sin permisos con `ROL_SIN_PERMISOS`. No se pueden eliminar los roles personalizados asignados; un rol personalizado sin asignaciones se puede eliminar después de confirmarlo. Cada cuenta tiene un rol, incluidos los planes de acceso.

## 7. Especificaciones de vistas

| Vista | Jerarquía principal y controles | Información complementaria |
|---|---|---|
| Cuentas | Título de página sobrio, acción de invitación, búsqueda por nombre/correo electrónico, filtros de rol/estado, filas de cuenta completas, cantidad visible de resultados. | Empresa, último acceso según la hora de Bogotá; datos de prueba neutrales; acciones contextuales de cuenta. |
| Roles | Cinco roles de sistema de solo lectura más ejemplos personalizados; rol seleccionado, nombre, casillas de verificación agrupadas por herramienta y acciones para guardar/eliminar roles personalizados. | Explicación de solo lectura, validación de permisos mínimos, rechazo de roles asignados. |
| Inicio de sesión | Correo electrónico, contraseña, Entrar. | Acceso solo por invitación; restablecimiento de contraseña emitido por el administrador; error genérico; texto de confirmación de destino. |
| Activación | Identidad invitada, nueva contraseña dos veces, aviso completo, consentimiento sin marcar, botón Activar deshabilitado hasta aceptar. | Regla de ocho caracteres; invitación válida por siete días; recuperación de invitación vencida/usada/reemplazada. |
| Restablecimiento | Nueva contraseña dos veces, guardar y volver al inicio de sesión. | Enlace de un solo uso válido por 24 horas, emitido por el administrador; recuperación de enlace no válido. |
| Mi cuenta | Identidad/empresa/rol del administrador de datos de prueba, contraseña actual, nueva contraseña dos veces, acción para cambiarla. | Las sesiones terminan al cambiar la contraseña; versión/fecha de aviso de ejemplo. |
| Actualización del aviso | Aviso v1 completo en el idioma seleccionado/del navegador, consentimiento sin marcar, aceptar/continuar, cerrar sesión. | Almacenamiento de versión/fecha; texto entre corchetes pendiente de revisión legal; otras rutas del producto ausentes. |

Selector de escenas: formulario de invitación, hoja de gestión, enlace de un solo uso, eliminación de cuenta y eliminación de rol. Todas las escenas se pueden abrir directamente para inspección y también desde su flujo aplicable del producto.

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

En **1101px o más**, un registro de ancho completo tiene cuatro columnas alineadas; no hay barra lateral ni celda de edición. La hoja de roles conserva un selector de 200px y un editor de permisos agrupados. El relleno exterior es de 40px y el relleno del papel es de 28px. El encabezado contiene Pictures/Sempertex, el selector de idioma y el menú de cuenta de la sesión iniciada; el título de página habitual de 24px precede las mismas rutas horizontales de cuentas.

En **761–1100px**, el relleno exterior es de 28px, el registro sigue ocupando todo el ancho, los filtros se organizan en dos columnas con la búsqueda a todo el ancho, las acciones de cuenta pasan debajo del registro y los grupos de permisos pasan a una sola columna.

En **360–760px**, el relleno exterior y del papel es de 20px y las esquinas de los paneles se mantienen en 32px. La identidad ocupa todo el registro; el rol y el estado comparten la siguiente línea y después aparece la acción de gestión. Los filtros, las opciones de rol, los permisos, la identidad y los campos del formulario se apilan. Las rutas se ajustan dentro del flujo. Los diálogos mantienen márgenes de 16px respecto a la ventana, relleno de 24px y desplazamiento vertical. Las franjas de respuesta conservan el tratamiento de alineación para teléfono de r11: todo el ancho del papel con un margen interno de 20px. El encabezado se ajusta y el rol de la cuenta está disponible en su menú. El título de página se mantiene en 24px; no hay contenido principal ni tarjeta de material en ningún ancho.

El ancho mínimo compatible es de 360px. No hay desplazamiento horizontal de página; ES/EN se reorganiza según el ancho. Los formularios conservan su ancho legible interno de 620px mientras el panel circundante usa el ancho disponible; los avisos legales permanecen completamente visibles mediante desplazamiento vertical. Así se conserva la composición del formulario sin dejar una barra lateral vacía. Los controles de Mockup quedan fuera de la geometría del producto.

## 10. Objetivos de accesibilidad y movimiento

Los objetivos son WCAG 2.2 AA para las interacciones aplicables: texto 4.5:1, bordes de controles significativos y foco 3:1, anillo de foco visible de tres píxeles con un desplazamiento de cuatro píxeles, acciones de 44 px, campos y casillas con nombres programáticos, grupos etiquetados y errores/resultados anunciados. El estado de las casillas con función de sistema sigue siendo visualmente legible aunque estén deshabilitadas. Los efectos destructivos se explican antes de confirmar; la confirmación con el correo electrónico exacto se aplica a la eliminación de cuentas.

Los ID de permisos se normalizan en identificadores sin espacios para que el `aria-labelledby` generado por Base UI resuelva la etiqueta de cada casilla. La búsqueda y los formularios conservan el foco mientras se escribe. Dialog/AlertDialog usan las primitivas reales instaladas para contener el foco, volver inerte el fondo y restaurar el foco al cerrarse. La conformidad con lectores de pantalla es un objetivo, no algo que las mediciones del navegador por sí solas acrediten.

Vocabulario de movimiento: registro preciso de panel de 480 ms, desplazamientos de filas de 55 ms y recorrido de controles de 180 ms; natural, 300/140 ms; sutil, 160/100 ms. El papel, las filas, las reglas, la respuesta de estado, el barrido del esqueleto y el movimiento de flecha al pasar el cursor o presionar siguen siendo comportamientos distintos. La animación del riel/foil se elimina junto con su contenido retirado. Los cargadores repetitivos restantes y todas las animaciones se pausan cuando la pestaña está oculta. No quedan animaciones decorativas fuera de pantalla. `useMotionProfile()` proporciona el perfil/estado reducido. El movimiento reducido, Quieto y `?still=1` eliminan el desplazamiento y los efectos repetitivos, y conservan el mismo contenido y las mismas acciones. La animación de navegación/filtros desplaza el contenido legible en vez de recortarlo. No se usan desvanecimientos de opacidad de texto ni destellos.

## 11. Criterios de aceptación observables y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1101+ | cuentas normal | Nombre/correo electrónico/empresa, rol, estado, último acceso y Administrar comparten cada registro delimitado por reglas; los conteos provienen de las mismas filas. |
| A-02 | 360–760 | cuentas normal | La identidad ocupa todo el registro; el rol/estado y Administrar se reorganizan debajo sin desplazamiento horizontal de la página. |
| A-03 | 360+ | error de inicio de sesión | Un único mensaje genérico incluye la espera de quince minutos y no revela diferencias según la existencia/el estado de la cuenta. |
| A-04 | 360+ | activación normal | Ambos campos de contraseña y el aviso completo aparecen antes del consentimiento; Activar permanece deshabilitado hasta marcar la casilla de consentimiento. |
| A-05 | 360+ | enlace vencido | No se muestran campos de contraseña y la opción visible de recuperación es pedir un enlace nuevo al administrador. |
| A-06 | 360+ | invitación | El nombre/correo electrónico/empresa opcional/un rol preceden la generación; se rechaza el correo electrónico duplicado. |
| A-07 | 360+ | confirmación del enlace | Se muestran la acción de copiar, el uso único/la vigencia y la invalidación de enlaces anteriores; al cerrar, se elimina la confirmación. |
| A-08 | 360+ | trabajo guardado/último administrador | El rechazo explica la invariante y el envío destructivo permanece deshabilitado. |
| A-09 | 360+ | eliminar cuenta | Se requiere el correo electrónico exacto de una cuenta sin trabajo para habilitar Eliminar permanentemente. |
| A-10 | 360+ | editor de roles | Los cinco roles del sistema son de solo lectura, las etiquetas de permisos agrupadas son accesibles y los roles personalizados requieren al menos un permiso. |
| A-11 | 360+ | actualización del aviso | No aparecen otras rutas del producto; se puede acceder al consentimiento o al cierre de sesión; los marcadores de posición permanecen explícitos. |
| A-12 | 360+ | Mi cuenta | La identidad coincide con la del menú de cuenta; la contraseña actual precede a las nuevas contraseñas y al texto que informa sobre el cierre de sesión. |
| A-13 | 360+ | oscuro/claro | Los bordes de los campos, las casillas personalizadas, las acciones con contorno y el foco son visibles sobre sus superficies reales. |
| A-14 | 360+ | movimiento reducido/expresivo | El registro expresivo se puede medir; en estado reducido/sin movimiento no hay animaciones en curso y se conservan todas las acciones. |
| A-15 | 360+ | diálogo abierto/cerrado | El foco permanece dentro del diálogo real; al cerrar la invitación con Escape, se restaura el foco en la acción que la abrió. |
| A-16 | 360+ | normal, cualquiera de los temas | El radio calculado de las esquinas del papel principal y del diálogo es de 32px; el aviso interno y la respuesta tienen radios de 24px. |
| A-17 | 360+ | normal, cualquiera de los temas | Los botones, los selectores nativos, el desplegable de cuenta y las etiquetas de estado tienen radios de píldora; los campos de texto tienen radios de 18px y bordes visibles. |
| A-18 | 1101+ | cuentas normal | El papel tiene 28px de relleno interno y las filas de cuenta tienen 24px de relleno vertical; todas las filas se alinean con las columnas compartidas del registro. |
| A-19 | 360+ | roles normal | El rol seleccionado tiene una superficie suave redondeada de 18px, las opciones de rol están separadas por 8px y las casillas de permisos conservan estados marcados/no marcados diferenciados y esquinas de 8px. |

| A-20 | 360+ | cuentas normal | El H1 es “Cuentas” de 24px; no se muestra ningún eslogan, contador de edición, barra lateral de planes ni tarjeta de materiales. |
| A-21 | 1101+ | cuentas normal | El espacio de trabajo tiene una columna; el registro ocupa el espacio que antes ocupaba el riel de anotaciones. |
| A-22 | 360+ | ES / EN | El idioma inicial es ES; las etiquetas de la interfaz en inglés aparecen solo cuando se selecciona EN; DialogClose se etiqueta como “Cerrar” en ES. |
| A-23 | 360+ | ambos temas | La fuente calculada del cuerpo es Geist y los colores corresponden a los valores de globals.css de Pictures, con bordes de controles en texto-tenue. |
| A-24 | 360+ | cuentas/cuenta/activación | Solo se muestran fixtures neutrales con etiquetas; las identidades del menú de cuenta y Mi cuenta coinciden. |

Verificación final r12 (solo esta instantánea; la evidencia de r11 permanece inmutable):

- Estado actual de la cadena de herramientas: instalada/compilada, **96/96 entradas disponibles**. `bitacora.py components mockup build` con ruta absoluta volvió a compilar el TSX asignado en el HTML asignado: **677KB / 2150 archivos fuente empaquetados**, código de salida 0. Bibliotecas reales instaladas, CSS/JS en línea y fuentes de producción locales incrustadas; no se instalaron paquetes, descargaron recursos ni usaron fragmentos alternativos.
- `contrast.py` con ruta absoluta: **se comprobaron 158 pares en temas claro y oscuro; todos pasaron**, código de salida 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/audit_mockup.py <r12.html> --max-combos 476`: **476 renderizados / 476 combinaciones planificadas**, **12,598 mediciones de texto / 1,392 paradas de foco**, código de salida 0. Las siete vistas, los doce estados y los cinco diálogos; móvil de 390px/escritorio de 1280px, ambos temas y matriz completa sin muestreo.

`RESULT: PASS — no hay problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento`

SHA-256 del HTML auditado: `c68a3a7ccd2ddd41818ab01199c582d4afa030eb7da0168d7bb6cfddb980b227`.

Comprobaciones complementarias con Playwright en caché: **288 aserciones PASS**, incluidas **84 comprobaciones responsivas ES/EN** (siete vistas × dos temas × dos idiomas × 360/768/1024px). El H1 sigue siendo de 24px; la barra lateral/edición/materiales retirados no aparecen; el espacio de trabajo usa una columna de ancho completo; cada selector de evidencia JSON coincide con la vista prevista. Se probaron la búsqueda/sin resultados/limpieza, la generación de invitaciones/confirmación de un solo uso, DialogClose traducido, Escape y restauración del foco en la acción que inició la operación, el requisito de consentimiento/activación y la supresión de la contraseña en enlaces no válidos. Se comprobaron la fuente de producción y el fondo oscuro. El registro expresivo mostró **ocho animaciones en curso**, mientras que el estado sin movimiento mostró **cero**; se conservan la pausa con pestaña oculta y el CSS de movimiento reducido. Cero excepciones de página o solicitudes HTTP(S) en esta comprobación complementaria.

Se inspeccionaron visualmente capturas en memoria de las vistas de cuentas a 1280/claro, roles a 1280/oscuro, cuentas a 390/claro y activación a 390/oscuro. No se guardaron archivos de captura. La corrección final para acortar la etiqueta se limita a la etiqueta de último acceso del fixture de prueba; después, su vista exacta en móvil se comprobó con la auditoría final completa y la captura a 390/claro.

Historial de auditoría: el primer barrido completo de r12 devolvió **FAIL — alineación 6** porque la etiqueta más larga de acceso de ejemplo neutral creó una línea engañosa aislada en el borde derecho de los registros en la vista móvil. Al acortar esa etiqueta de fixture a “Ejemplo”, se restableció el eje de fila establecido; una comprobación puntual del renderizado y la matriz final completa anterior pasan. No se cambió ningún umbral ni comprobación. Una limpieza intermedia que solo afectó el código fuente eliminó por accidente el CSS responsivo; se restauraron el CSS equilibrado y los bloques originales de respuesta y fotogramas clave antes del primer barrido completo. Una aserción complementaria de movimiento esperaba inicialmente una animación en una URL explícita `?still=1`; el diagnóstico confirmó que el modo sin movimiento suprime correctamente el desplazamiento y la comprobación complementaria final prueba los estados expresivo/sin movimiento por separado, sin esa consulta. Ninguna de las comprobaciones incompletas o fallidas cuenta como aprobada.

El lint/tipado/compilación/pruebas del producto, la corrección del backend/sesiones/permisos, el vencimiento seguro de tokens, la persistencia en base de datos, la concurrencia y el cumplimiento total de WCAG o legal no quedan establecidos por este artefacto estático. La selección del propietario y la aprobación canónica final siguen pendientes.

## 12. Preguntas abiertas, supuestos e impacto

P: ¿Qué entidad legal, correo electrónico de contacto sobre derechos y URL de política reemplazarán los campos entre corchetes antes de la activación externa real? Responsable: David con el área legal de Sempertex; los campos legales aplazados permanecen sin cambios en ambos textos aprobados del aviso.
P: Después de cambiar una contraseña en Mi cuenta, ¿debe este navegador conservar una sesión recién emitida o volver al inicio de sesión? Responsable: Planner/David; el mockup heredado solicita iniciar sesión de nuevo, mientras que la nota anterior identificó una discrepancia de aceptación T2.2. Esta revisión de contenido conserva el flujo heredado, pendiente de conciliación antes de la aprobación canónica.

Se conserva el comportamiento confirmado: un rol por cuenta, cinco roles del sistema, incluidos los tres planes de acceso, contraseñas de ocho caracteres, indicación genérica de bloqueo de quince minutos, invitaciones de siete días y restablecimientos de 24 horas, enlaces de un solo uso generados por administradores sin envío automático de correos, aceptación obligatoria del aviso nuevamente, protecciones para trabajo guardado/último administrador y al menos un permiso para roles personalizados. Quitar el panel promocional de planes no elimina los controles necesarios para asignar roles/planes ni la inspección de permisos del sistema de solo lectura. Los datos y las operaciones del mockup son ilustrativos; no se modifica ninguna cuenta ni sesión real. La selección inicial de ES para la planificación es un valor predeterminado de inspección, no sustituye el requisito del producto de mostrar el aviso según el idioma del navegador.

**Impacto: iteración visual incompatible de r11 → r12** en la jerarquía/ancho de las cuentas y en la restauración del color/tipografía del producto; no se incorpora ningún flujo de producto ni política de permisos. SP-2 T2.1 futuro copiará solo el artefacto seleccionado/finalizado posteriormente por el propietario. T2.3 (formularios de acceso), T2.4 (menú de cuenta/Mi cuenta) y T2.5 (cuentas/invitaciones/roles) deben mostrar los tokens de producto seleccionados, el texto traducido y las formas conservadas; T2.5 debe usar el registro de ancho completo. T2.7 debe comparar la revisión elegida en móvil, tableta y escritorio. Estos borradores no redirigen a ningún consumidor ni conceden aprobación. La integración y la auditoría independiente siguen a cargo de los responsables de sus planes, no de esta delegación de diseño.

OBSERVACIONES: los HTML empaquetados de los subproyectos no coinciden con sus contratos escritos de tokens de producción; prevalecen los valores globales/la estructura actuales del producto y las correspondencias escritas de los subproyectos. La pregunta sobre la finalización de contraseña y los campos legales aplazados siguen abiertos. No se edita ningún comportamiento de la interfaz de producción, esquema ni plan. No se crea una vista previa de diseño opcional del repositorio. El compilador real y el navegador en caché están disponibles; no se requieren recursos externos ni alternativas.

Solo se escriben los cuatro archivos r12 de esta dirección y el RESULT obligatorio de la delegación. Las fuentes r11, el comportamiento compartido, los archivos canónicos, los subproyectos, los repositorios y los demás archivos de bitácora permanecen sin cambios.
