---
name: Parte de acceso
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r13.dir-a
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
date: 2026-10-27
source_revision: r12.dir-a
feedback: "2026-10-27T09:08 direction=a: correct left-heavy alignment and use available space better"
---

# Parte de acceso — direction A

## 1. Identidad y trazabilidad

Iteración en una sola dirección **r13 de r12 A**, estado **borrador**, pendiente de que el propietario la seleccione junto con el plan. Esta nota de dirección de doce secciones no es el contrato canónico ni un insumo de implementación aprobado. El nombre de la dirección se mantiene como “Parte de acceso”. No se crean nuevas direcciones, miniaturas, contratos compartidos, planes ni cambios en repositorios.

Fuente del comportamiento: `cuentas-admin@v1.r13.behavior.md` SHA-256 `3fb1bbc78c83aae3`. Instantáneas de contexto: `SPEC.md` SHA-256 `65b1e5ecc06f20d9`; `PLAN.md` SHA-256 `cc7e53f2abf3c23c`; `PLAN.json` SHA-256 `7a2c833a7e711508`. SP-2 cubre cuentas solo con invitación R1, administración de roles R3 y acceso asignado R16. Los contratos existentes de SP-1 siguen siendo account-service@1, session-guard@1 y permission-map@1. Las tareas de diseño son T2.1, T2.3–T2.5 y la revisión visual T2.7; no se agrega ninguna ruta de ingeniería al alcance del diseño.

## 2. Propósito, concepto y elemento memorable

El administrador responde «¿Quién tiene acceso, qué rol tiene y qué hay que cambiar?». Cada fila delimitada mantiene juntos el nombre, el correo electrónico, la empresa opcional, el rol asignado, el estado, el último acceso y la acción contextual. Los formularios de acceso gestionan el inicio de sesión, la activación, el restablecimiento y la aceptación obligatoria del aviso; Mi cuenta identifica a la persona y permite cambiar su contraseña.

La inscripción cinética existente sigue siendo la interacción memorable: el panel de trabajo se asienta en vertical, las filas se inscriben en horizontal y la respuesta visual dibuja un breve trazo de inscripción. La barra lateral del plan y la tarjeta “De la idea al montaje” eliminadas no tienen reemplazo. Esta es una superficie de administración, con títulos de tareas habituales y sin eslogan ni total decorativo. Todas las filas y operaciones se identifican como datos simulados; las descripciones neutrales de cuentas y los datos de prueba `@prueba.local` reemplazan a personas, empresas y fechas ficticias. Los totales de filas siguen derivándose de la lista visible de datos de prueba.

## 3. Composición conservada y registro visual

Se comenzó con una copia de `cuentas-admin@v1.r12.dir-a.tsx`. Se aplicaron los comentarios del propietario del 2026-10-27T09:08, dirección=A: se centraron las cinco vistas orientadas a formularios en un panel de 676px ajustado al contenido, en lugar de anclar un formulario de 620px a la izquierda de una hoja de ancho completo. Los títulos de página, las superficies de los formularios, las respuestas y el pie apilado comparten ese eje; los formularios de escritorio conservan su ancho legible de 620px y márgenes exteriores iguales. Las cuentas conservan el registro de trabajo completo, con los filtros de búsqueda/rol/estado ahora en columnas flexibles de proporción 2:1:1 que comparten el espacio. El selector de rol se amplía de 200px a 240px en escritorio para equilibrar sus etiquetas con la hoja de permisos. Por debajo de los puntos de quiebre existentes, se mantiene la disposición apilada establecida. La estructura, navegación, contenido, fixtures, tokens, tipografía, formas, flujos y registro cinético permanecen como en r12.

Se inspeccionaron los archivos Markdown y HTML inmutables de los subproyectos `taller-esenciales@v1` y `proyectos@v1`. Sus archivos Markdown establecen la paleta semántica existente de Pictures, la tipografía Geist/system-sans, la navegación neutral y el vocabulario de cuenta/encabezado. El HTML empaquetado actual todavía contiene paletas, tipografías y texto principal exploratorios anteriores que no coinciden con esos contratos escritos. Esta revisión sigue las fuentes de tokens/fuentes de producción y los contratos escritos de los subproyectos, en vez de incorporar esas discrepancias. No se modifica ningún archivo de los subproyectos. La dirección conserva explícitamente la navegación horizontal y la composición del registro de trabajo solicitadas.

Referencias de producto de solo lectura: `src/app/globals.css`, `src/app/layout.tsx`, `src/app/login/{page,LoginForm}.tsx`, `src/components/admin/AdminTabs.tsx` y `src/components/ui/shell/CabeceraApp.tsx` de ambos árboles de trabajo. El inicio de sesión existente es un formulario de contraseña; los controles de correo electrónico/invitación/roles son las adiciones dentro del alcance. La administración existente usa un título sobrio y pestañas dentro del flujo; se reutiliza la marca de anillo y punto del encabezado, con el menú de cuenta requerido. No se propone ninguna marca, tipografía de exhibición ni paleta de exploración. La producción y otros cambios locales permanecen intactos.

## 4. Ocho ejes, lenguaje visual y componentes reales

| Eje | Expresión actual |
|---|---|
| Concepto | Un registro operativo de acceso: cuentas invitadas, rol asignado, estado de acceso y la siguiente acción de gestión. Sin paneles de marketing ni promoción de planes. |
| Diseño | Encabezado compacto de Pictures/Sempertex, título de página sobrio de 24px y regla horizontal de rutas conservada. Las cuentas ocupan el ancho del registro con filtros de búsqueda/rol/estado equilibrados en proporción 2:1:1; los roles usan un selector de 240px junto a la hoja de permisos. Acceso, activación, restablecimiento, aviso y Mi cuenta usan un panel centrado de 676px y un eje compartido de 620px para formularios y comentarios, que elimina la mitad derecha vacía. |
| Navegación | Navegación horizontal y neutra de Cuentas / Roles y permisos / Mi cuenta conservada, diálogos contextuales de cuenta y detalles de cuenta con nombre. El acceso solo por invitación no tiene una ruta de registro. Los selectores de planificación permanecen fuera del contenedor del producto. |
| Tipografía | Geist Sans y Geist Mono de producción, integradas desde la compilación local existente. Título de página de 24px, títulos de sección de 20px, texto principal de 14–16px y metadatos de 11–13px; sin familia tipográfica de exhibición ni sección principal. ES es el idioma inicial; EN aparece en el selector de idioma. |
| Densidad | Se conservan el relleno de 24px en las filas de cuentas, los márgenes internos del papel de 28px en escritorio / 20px en teléfono, los paneles de 32px, las superficies interiores de 24px, las entradas de 18px, las casillas de 8px y los controles y chips de estado tipo píldora. Los paneles de formularios ajustados al contenido tienen márgenes exteriores iguales; las vistas de gestión amplias mantienen el espacio de trabajo disponible y filtros flexibles. |
| Componentes | Button, Input, Checkbox, Skeleton, Dialog y AlertDialog instalados de shadcn/Base UI, compuestos como filas de cuentas y grupos de campos de permisos. Marca de anillo y punto de producción; paneles redondeados, estados semánticos tipo píldora y navegación neutra. El texto para cerrar diálogos sigue ES/EN. |
| Color | Paleta exacta de globals.css de Pictures asignada como en proyectos@v1: claro #faf9fc / #ffffff con acciones #6d3fe0; oscuro #0b0c10 / #16181f con acciones #9479ff y primer plano #120b24. Tokens existentes de éxito/advertencia/error; los bordes de entrada usan como alias texto-tenue. Sin paleta exploratoria. |
| Movimiento | Registro cinético conservado: cubic-bezier(.76,0,.24,1), registro de papel/fila/regla/estado de 480ms, desfases de fila de 55ms y controles de 180ms, ritmos naturales de 300/140ms y sutiles de 160/100ms. Se mantienen el barrido de Skeleton y el desplazamiento de la flecha al pasar el cursor o presionar; se elimina el movimiento retirado del riel/foil. Reducido/estático desactiva el movimiento y las pestañas ocultas pausan la animación. |

La asignación de roles del proyecto se basa en globals.css de ambos repositorios y los roles compartidos correspondientes en proyectos@v1. Todos los valores siguientes ya existen en el producto; no se introduce ningún color nuevo.

| Origen en Pictures | Rol en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | principal, primer plano principal | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | principal al pasar el cursor, anillo | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | borde decorativo, regla | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | entrada (alias accesible existente de un control relacionado) | #766c85 / #8a91a0 |
| `--superficie-suave` | superficie suave de rol seleccionado | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | éxito, éxito suave | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | advertencia, advertencia suave | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45, #ffeaec / #ff979f, #43252a |
| Primer plano destructivo existente | primer plano destructivo | #ffffff / #3a0f13 |
| `--fondo` | información suave, principal suave | #faf9fc / #0b0c10 |

La tipografía es Geist Sans / Geist Mono real de producción, integrada sin conexión desde los recursos WOFF2 latinos locales de la compilación t12 existente de Next. No se descargan fuentes ni recursos. H1 es de 24px/1.25 en todos los anchos, el título de sección es de 20px/1.3 en escritorio, el texto principal es de 14–16px y los metadatos de 11–13px; la fuente monoespaciada se limita a identificadores/metadatos. Se conservan el tamaño de las secciones en teléfono y las formas generosas de r11. Los roles de forma de R11 siguen siendo `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. Estas son las decisiones de forma del borrador que el propietario conservó, no nuevas decisiones de paleta o tipografía de producción. El relleno de papel y diálogos se mantiene en 28px en escritorio, 20px en el papel del teléfono / 24px en los diálogos del teléfono; las filas se mantienen en 24px en escritorio / 20px en teléfono.

Componentes instalados: `shadcn:button` predeterminado/contorno/destructivo, `shadcn:input` texto/correo electrónico/contraseña, `shadcn:checkbox` marcada/sin marcar/deshabilitada, `shadcn:skeleton`, `shadcn:dialog` y `shadcn:alert-dialog`; las importaciones son `@/components/ui/{button,input,checkbox,skeleton,dialog,alert-dialog}`. Las primitivas instaladas de Base UI/Animate UI proporcionan contención del foco y confirmación de acciones destructivas. El DialogClose real se recompone con un nombre accesible traducido para que ES no exponga el “Cerrar” en inglés de la biblioteca. Las filas de cuenta con aspecto de tabla, la hoja de roles, los grupos de campos y el encabezado son composiciones personalizadas existentes; los selectores nativos de idioma/rol/estado siguen siendo nativos. `@kit/mockup` proporciona mountMockup/useMockup y `@kit/motion` proporciona useMotionProfile. Sin fragmentos, instalación ni generador alternativo.

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

En **1101px y más**, un registro de ancho completo tiene cuatro columnas alineadas; no hay barra lateral ni celda de edición. La hoja de roles tiene un selector de 240px y un editor de permisos agrupados. Los filtros de búsqueda, rol y estado se distribuyen en columnas flexibles 2:1:1 que ocupan el ancho disponible del escritorio, con anchos mínimos de 240/180/160px. El relleno exterior es de 40px y el relleno del papel es de 28px. El encabezado incluye Pictures/Sempertex, selector de idioma y los detalles de la cuenta con sesión iniciada; el título de página normal de 24px precede las mismas rutas horizontales de cuentas.

En **761–1100px**, el relleno exterior es de 28px, el registro sigue ocupando todo el ancho, los filtros usan dos columnas y la búsqueda ocupa todo el ancho; las acciones de cuenta pasan debajo del registro y los grupos de permisos se organizan en una sola columna.

En **360–760px**, el relleno exterior/del papel es de 20px y las esquinas del panel se mantienen en 32px. La identidad ocupa todo el registro; el rol y el estado comparten la línea siguiente y la acción de gestión va después. Los filtros, las opciones de rol, los permisos, la identidad y los campos del formulario se apilan. Las rutas se ajustan dentro del flujo. Los diálogos mantienen márgenes de 16px respecto al área visible, relleno de 24px y desplazamiento vertical. Los comentarios del registro conservan el tratamiento de alineación para teléfono de r12: ancho completo del papel con un margen interno de 20px. Los comentarios del formulario ocupan el papel del teléfono con un margen interno de 20px, alinean el texto con las etiquetas de los campos y usan el ancho disponible. El encabezado se ajusta y el rol de la cuenta queda disponible dentro de sus detalles. El título de página se mantiene en 24px; no hay sección principal ni tarjeta de material en ningún ancho.

El ancho mínimo compatible es 360px. No hay desplazamiento horizontal de página; ES/EN se redistribuyen. Inicio de sesión, activación, restablecimiento, Mi cuenta y aviso usan un panel centrado con ancho máximo de 676px (formulario de 620px más dos márgenes internos de papel de 28px). El encabezado sigue el mismo eje exterior de 676px. En anchos menores, el panel ocupa el espacio disponible y el formulario se contrae sin desbordarse. Los comentarios del formulario en escritorio tienen el mismo ancho máximo centrado de 620px, incluidos los estados de error/éxito; en teléfonos, su banda ocupa el papel y el texto mantiene el margen interno de 20px de los campos; los estados de enlace vencido y rechazo de permisos heredan la misma geometría del panel. Cuentas y roles conservan espacios de trabajo de ancho completo. Los avisos legales permanecen completamente visibles mediante desplazamiento vertical. Los controles de la maqueta quedan fuera de la geometría del producto.

## 10. Objetivos de accesibilidad y movimiento

Los objetivos son WCAG 2.2 AA para las interacciones aplicables: texto 4.5:1, bordes de controles significativos y foco 3:1, anillo de foco visible de tres píxeles con un desplazamiento de cuatro píxeles, acciones de 44 px, campos y casillas con nombres programáticos, grupos etiquetados y errores/resultados anunciados. El estado de las casillas con función de sistema sigue siendo visualmente legible aunque estén deshabilitadas. Los efectos destructivos se explican antes de confirmar; la confirmación con el correo electrónico exacto se aplica a la eliminación de cuentas.

Los ID de permisos se normalizan en identificadores sin espacios para que el `aria-labelledby` generado por Base UI resuelva la etiqueta de cada casilla. La búsqueda y los formularios conservan el foco mientras se escribe. Dialog/AlertDialog usan las primitivas reales instaladas para contener el foco, volver inerte el fondo y restaurar el foco al cerrarse. La conformidad con lectores de pantalla es un objetivo, no algo que las mediciones del navegador por sí solas acrediten.

Vocabulario de movimiento: registro preciso de panel de 480 ms, desplazamientos de filas de 55 ms y recorrido de controles de 180 ms; natural, 300/140 ms; sutil, 160/100 ms. El papel, las filas, las reglas, la respuesta de estado, el barrido del esqueleto y el movimiento de flecha al pasar el cursor o presionar siguen siendo comportamientos distintos. La animación del riel/foil se elimina junto con su contenido retirado. Los cargadores repetitivos restantes y todas las animaciones se pausan cuando la pestaña está oculta. No quedan animaciones decorativas fuera de pantalla. `useMotionProfile()` proporciona el perfil/estado reducido. El movimiento reducido, Quieto y `?still=1` eliminan el desplazamiento y los efectos repetitivos, y conservan el mismo contenido y las mismas acciones. La animación de navegación/filtros desplaza el contenido legible en vez de recortarlo. No se usan desvanecimientos de opacidad de texto ni destellos.

## 11. Criterios de aceptación observables y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1101+ | cuentas normal | Nombre/correo electrónico/empresa, rol, estado, último acceso y Gestionar comparten cada registro delimitado; los recuentos provienen de las mismas filas. |
| A-02 | 360–760 | cuentas normal | La identidad ocupa todo el registro; el rol/estado y Gestionar se reorganizan debajo sin desplazamiento horizontal de página. |
| A-03 | 360+ | error de inicio de sesión | Un mensaje genérico incluye la espera de quince minutos y no revela diferencias de existencia/estado de la cuenta. |
| A-04 | 360+ | activación normal | Ambos campos de contraseña y el aviso completo preceden al consentimiento; Activar está deshabilitado hasta marcar el consentimiento. |
| A-05 | 360+ | enlace vencido | No aparece la entrada de contraseña y pedir un enlace nuevo al administrador es la recuperación visible. |
| A-06 | 360+ | invitación | Nombre/correo electrónico/empresa opcional/un rol preceden a la generación; se rechaza el correo electrónico duplicado. |
| A-07 | 360+ | recepción del enlace | La acción de copiar, el uso único/la duración y la invalidación de enlaces anteriores son visibles; cerrar elimina el comprobante. |
| A-08 | 360+ | trabajo guardado / último administrador | El rechazo explica la invariante y el envío destructivo permanece deshabilitado. |
| A-09 | 360+ | eliminación de cuenta | Para una cuenta sin trabajo asociado, se debe ingresar su correo electrónico exacto antes de que se habilite Eliminar permanentemente. |
| A-10 | 360+ | editor de roles | Los cinco roles del sistema son de solo lectura, las etiquetas de permisos agrupados son accesibles y los roles personalizados requieren al menos un permiso. |
| A-11 | 360+ | actualización del aviso | No aparecen otras rutas del producto; se puede acceder al consentimiento o al cierre de sesión; los marcadores de posición se indican explícitamente. |
| A-12 | 360+ | Mi cuenta | La identidad coincide con el menú de cuenta; la contraseña actual precede a las nuevas contraseñas y al texto sobre el cierre de sesión. |
| A-13 | 360+ | oscuro / claro | Los bordes de entrada, las casillas personalizadas, las acciones con contorno y el foco son visibles en sus superficies reales. |
| A-14 | 360+ | reducido / expresivo | El registro expresivo se puede medir; reducido/estático no ejecuta animaciones y conserva todas las acciones. |
| A-15 | 360+ | diálogo abierto / descartado | El foco permanece dentro del diálogo real; al presionar Escape en la invitación, el foco vuelve a la acción que la inició tras descartarla. |
| A-16 | 360+ | normal, cualquier tema | El radio de esquina calculado del papel principal y del diálogo es de 32px; el aviso y los comentarios interiores tienen radios de 24px. |
| A-17 | 360+ | normal, cualquier tema | Los botones, selectores nativos, detalles de cuenta y chips de estado tienen radios tipo píldora; las entradas de texto tienen radios de 18px y bordes visibles. |
| A-18 | 1101+ | cuentas normal | El papel tiene un relleno interior de 28px y las filas de cuentas tienen un relleno vertical de 24px; cada fila permanece alineada con las columnas compartidas del registro. |
| A-19 | 360+ | roles normal | El rol seleccionado tiene una superficie suave redondeada de 18px, las opciones de rol están separadas por 8px y las casillas de permisos conservan estados diferenciados de marcada/sin marcar con esquinas de 8px. |

| A-20 | 360+ | cuentas normal | H1 es “Cuentas” de 24px; no se muestra ningún eslogan, contador de edición, barra lateral de planes ni tarjeta de material. |
| A-21 | 1101+ | cuentas normal | El espacio de trabajo tiene una columna; el registro ocupa el espacio que antes ocupaba el riel de anotaciones. |
| A-22 | 360+ | ES / EN | El idioma inicial es ES; las etiquetas de la interfaz en inglés aparecen solo al seleccionar EN; DialogClose se denomina “Cerrar” en ES. |
| A-23 | 360+ | ambos temas | La fuente calculada del cuerpo es Geist y los colores corresponden a los valores de globals.css de Pictures, con bordes de control texto-tenue. |
| A-24 | 360+ | cuentas / cuenta / activación | Solo se muestran datos de prueba neutros con etiquetas; las identidades del menú de cuenta y de Mi cuenta coinciden. |

| A-25 | 761+ | inicio de sesión / activación / restablecimiento / Mi cuenta / aviso, ambos temas | El espacio de trabajo tiene un ancho máximo de 676px e iguales márgenes izquierdo y derecho respecto al área visible; sus campos tienen un ancho máximo de 620px y están centrados en ese mismo eje; el pie está apilado sobre el eje del panel. |
| A-26 | 761+ | error / éxito del formulario / enlace vencido | Los comentarios y la recuperación permanecen dentro del panel de formulario centrado; no queda una hoja en blanco de ancho completo a la derecha. |
| A-27 | 1101+ | cuentas normal | Los filtros de búsqueda/rol/estado ocupan la fila en columnas flexibles de proporción 2:1:1, en lugar de una búsqueda muy ancha y dos controles fijos y estrechos. |
| A-28 | 1101+ | roles normal | El selector de roles tiene 240px de ancho y el editor de permisos ocupa el ancho restante con los grupos de permisos existentes en dos columnas. |
| A-29 | 360–760 | todas las vistas de formulario | El panel centrado se contrae al ancho disponible con 20px de relleno para teléfono, sin desplazamiento horizontal ni acciones ocultas. |

Verificación final de r13 (SHA-256 del HTML final `6fbc92b149739f55e4e467be53ec85385bd150a2524b35ea8ec8feb5e4895931`):

- Cadena de herramientas sin conexión actual: instalada/compilada, **96/96 entradas disponibles**. `bitacora.py components mockup build` con rutas absolutas volvió a compilar el TSX r13 asignado en su HTML independiente asignado: **678KB, 2150 archivos fuente**, código de salida 0. Componentes reales instalados de shadcn/Base UI y fuentes de producción integradas localmente; sin instalación de paquetes, descarga de recursos ni fragmentos alternativos.
- `contrast.py` con rutas absolutas: **158 pares verificados en claro y oscuro, todos aprobados**, código de salida 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/audit_mockup.py <r13.html> --max-combos 476`: **476 renderizaciones / 476 combinaciones planificadas**, **12,598 mediciones de texto / 1,396 paradas de foco**, código de salida 0, con `/usr/bin/chromium` seleccionado por el kit actual. Cada combinación de vista/estado/tema y cada diálogo en su estado normal, a 390/1280px; sin muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Comprobaciones complementarias con Playwright en caché: **494 aserciones APROBADAS**, incluidas **112 pruebas responsivas ES/EN** (siete vistas × dos temas × dos idiomas × 360/768/1024/1440px). Se midieron el centrado del formulario y del panel, el límite de 676px del panel, la tipografía Geist real y la ausencia de desbordamiento horizontal. Los **18 selectores de evidencia JSON** coinciden con las vistas renderizadas previstas. La aceptación del aviso habilita la activación; un enlace vencido oculta la entrada de contraseña; el diálogo de invitación se abre y Escape lo cierra. El modo Expresivo muestra **ocho animaciones en curso**, Quieto muestra **cero** y el ajuste de movimiento reducido del sistema operativo muestra **cero**. No se produjeron excepciones de página ni solicitudes HTTP(S). Una comparación del código fuente confirma que **toda la lógica de interacción permanece byte por byte idéntica a r12** después de excluir CSS, atributos de diseño y la etiqueta de revisión. La nota tiene doce secciones y el JSON conserva su estructura exacta de tres claves y ocho ejes.

Las capturas finales se inspeccionaron en memoria con Chromium del sistema de la auditoría: inicio de sesión en 1280/tema claro, cuentas en 1280/tema oscuro, error de inicio de sesión en 390/tema claro y roles en 390/tema oscuro. El pie de página final sigue el eje del panel del formulario, los anchos de los filtros están equilibrados y el texto de error en móvil se alinea con las etiquetas de los campos. Capturas anteriores en memoria también cubrieron la activación en tema oscuro y los roles en escritorio. No se escribieron archivos de captura.

Historial de auditoría: la primera revisión completa de r13 devolvió **FAIL — alineación 30**. El pie de página de ancho completo no seguía el nuevo panel del formulario centrado y las bandas de error más estrechas en móvil creaban un eje interior en competencia. Ahora el pie de página se apila sobre el eje del panel; en móvil, los mensajes ocupan todo el área de fondo blanco y el texto conserva la sangría de los campos. El artefacto final reconstruido supera la auditoría completa anterior sin cambiar ninguna comprobación ni umbral. Una prueba exploratoria con el navegador en caché también informó de un problema con la heurística de alineación de la etiqueta de consentimiento, reproducido sin cambios en r12; la auditoría actual con el kit y el navegador del sistema no informa de ese problema. La primera prueba complementaria de interacción apuntó a la casilla nativa oculta de Base UI y agotó el tiempo de espera; se corrigió al usar el rol de casilla accesible visible, y la prueba complementaria final completa se supera. Las pruebas fallidas o incompletas no se cuentan como comprobaciones superadas.

El lint, los tipos, las pruebas y la compilación de producción, el enrutamiento autenticado, los permisos del backend, el vencimiento seguro de tokens, la persistencia y el cumplimiento legal o de WCAG completo quedan fuera de esta verificación estática del diseño. La evidencia de R12 permanece en su nota inmutable; la selección del propietario y la aprobación canónica siguen pendientes.

## 12. Preguntas abiertas, supuestos e impacto

P: ¿Qué entidad legal, correo electrónico de contacto para derechos y URL de políticas reemplazarán los campos entre corchetes antes de la activación externa real? Responsable: David con el equipo legal de Sempertex; los campos legales aplazados se mantienen sin cambios en ambos textos aprobados del aviso.
P: Después de cambiar una contraseña en Mi cuenta, ¿este navegador debería conservar una sesión recién emitida o volver al inicio de sesión? Responsable: Planner/David; la maqueta heredada solicita iniciar sesión de nuevo, mientras que la nota anterior identificó una discrepancia de aceptación en T2.2. Esta revisión del contenido conserva el flujo heredado hasta que se concilie antes de la aprobación canónica.

Se conserva el comportamiento confirmado: un rol por cuenta, cinco roles del sistema, incluidos los tres planes de acceso, contraseñas de ocho caracteres, indicación genérica de bloqueo de quince minutos, invitaciones de siete días y restablecimientos de 24 horas, enlaces de un solo uso generados por administradores sin envío automático de correo electrónico, aceptación obligatoria del aviso, protecciones para el trabajo guardado y el último administrador, y al menos un permiso para los roles personalizados. Quitar el panel promocional de planes no elimina los controles necesarios para asignar roles o planes ni la inspección de solo lectura de los permisos del sistema. Los datos y operaciones de muestra son ilustrativos; no se modifica ninguna cuenta ni sesión real. La selección inicial de ES para la planificación es un valor predeterminado de inspección, no reemplaza el requisito del producto de mostrar el aviso en el idioma del navegador.

**Impacto: iteración incompatible del diseño responsivo r12 → r13** limitada a SP-2; el significado del producto, la navegación, el contenido y el movimiento siguen siendo compatibles. En el futuro, T2.1 podrá copiar únicamente el artefacto seleccionado/finalizado más adelante por el propietario. T2.3 debe adaptar el espacio de trabajo centrado de inicio de sesión, activación, restablecimiento y aviso obligatorio; T2.4 debe adaptar Mi cuenta al mismo eje del formulario; T2.5 debe adaptar las proporciones de los filtros en escritorio y el selector de roles de 240px. T2.7 debe volver a renderizar estas vistas en teléfono, tableta y escritorio con la revisión seleccionada por el propietario. No se redirige ningún otro subplan ni contrato aprobado. Esta nota incluye el registro del impacto del borrador porque la escritura de un registro de cambios o plan por separado queda fuera de esta delegación.

INQUIETUDES: los archivos HTML agrupados de los subplanes hermanos no coinciden con sus contratos escritos de tokens de producción; prevalecen los valores globales y el diseño actuales del producto, además de las correspondencias escritas de los subplanes hermanos. La pregunta sobre completar el cambio de contraseña y los campos legales aplazados siguen abiertos. No se modifica la interfaz de producción, el esquema ni el plan. No se crea una vista previa de diseño opcional del repositorio. El generador real y el navegador en caché están disponibles; no se necesitan alternativas ni recursos externos.

Solo se escriben los cuatro archivos r13 de esta dirección y el RESULTADO obligatorio de la delegación. Las fuentes r12, el comportamiento compartido, los archivos canónicos, los subplanes hermanos, los repositorios y los demás archivos de bitácora permanecen sin cambios.
