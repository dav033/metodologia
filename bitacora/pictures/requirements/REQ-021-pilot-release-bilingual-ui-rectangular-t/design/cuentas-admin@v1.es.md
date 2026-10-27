---
contract: cuentas-admin
version: 1
status: draft
subplan: SP-2
requirements: [R1, R3, R16, R17]
owner: David
author: Designer
date: 2026-10-27
direction: Parte de acceso (a)
source_revision: r14.dir-a
source_behavior: cuentas-admin@v1.r14.behavior.md
---

# cuentas-admin@v1 — Parte de acceso

## 1. Identidad y trazabilidad

**Borrador; no aprobado para implementación.** Finalización de la dirección **Parte de acceso (a), r14** seleccionada en la web por el propietario. Elegir una dirección no aprueba este contrato. Este contrato conductual y visual completo de doce secciones reemplaza el borrador canónico anterior no aprobado, conserva la composición, la navegación y el movimiento seleccionados, y sigue sujeto a la aprobación independiente del propietario y del plan. T2.1 solo puede copiar la instantánea exacta que se apruebe posteriormente en `design/contracts/cuentas-admin@v1.md`; Designer no concede aprobación.

Entradas: SPEC.md y PLAN.json actuales (esquema 1.3.0, revisión 1), `cuentas-admin@v1.r14.behavior.md` y los archivos Markdown, HTML autocontenido y TSX de la dirección r14 seleccionada. La retroalimentación sobre la dirección A del 2026-10-27T14:17 registrada en r14 indica **Sempertex** como nombre de la empresa en ambos idiomas del aviso; se mantienen los marcadores de posición del contacto para ejercer derechos y de la política. Esta aclaración posterior del propietario rige la sustitución del nombre legal en el aviso, mientras que se conserva el resto del contenido v1 de SPEC. No se inventan sufijos legales, direcciones, URL ni aprobaciones legales.

Instantáneas SHA-256 de las fuentes para esta finalización:

| Entrada | SHA-256 |
|---|---|
| `SPEC.md` | `85733361b25e8b6c9ff055cde3ddee45e77d36c0326698e01cde675b44aae204` |
| `PLAN.json` | `7b33d8cb90b956bcac2fdec6603dd6ad68c69f9c156381f32567f63175a546b1` |
| `design/cuentas-admin@v1.r14.behavior.md` | `76936ca02335918683373873e8e28c321f95ccf020761795865ffbbf3b7f5302` |
| `design/cuentas-admin@v1.r14.dir-a.md` | `b97d0a3defc2fea5ee3db1f3270cda3849c54c62a38435cf4d4696aba5026542` |
| `design/cuentas-admin@v1.r14.dir-a.tsx` | `ef11a0cc3d89ce9589a6a3db7fdd60a2508fd43ed11f32cb425615054f5c713b` |
| `design/cuentas-admin@v1.r14.dir-a.html` | `312dfaadd4b07c6fc38a803d35a14b79e25925079266f724b2285e77d3a370fd` |

Solo **SP-2** vincula `ui.contract=cuentas-admin`, versión 1, copia del diseño **T2.1** y revisión visual **T2.7**. Los consumidores de la implementación de UI son **T2.3** (inicio de sesión, activación, restablecimiento y aviso), **T2.4** (menú de cuenta compartido/Mi cuenta) y **T2.5** (cuentas, invitaciones y roles). **T2.2** proporciona las API de cuentas, **T2.6** verifica los flujos integrados en el navegador y **T2.8** realiza una auditoría independiente. SP-1 proporciona account-service@1, session-guard@1, permission-map@1 y plan-catalogue@1. Su catálogo es responsable de las etiquetas, el orden, los precios, la disponibilidad y los permisos de los planes; SP-2 lo consulta sin convertirse en otro responsable de la lógica de planes. SP-14 es responsable de la sección pública de planes y sus dos enlaces de entrada en inicio de sesión/menú de cuenta; esas adiciones se integran con estas vistas mediante planes@v1 y quedan fuera del alcance de la finalización r14. Ninguna otra subplan de UI se convierte en consumidor únicamente por tener una dependencia.

| Requisito | Vistas / flujos | Criterios de aceptación |
|---|---|---|
| R1 cuentas invitadas | V1–V4, V6–V7 / F1–F5, F7–F8 | UI-AC-06–14, 19–24, 29–30, 44 |
| R3 roles y permisos | V4–V5 / F5–F6 | UI-AC-15–19, 25, 31, 35 |
| R16 planes asignados acumulativos | V4–V5 / F2–F3, F5–F6 | UI-AC-15–16, 25, 41–42 |
| R17 catálogo compartido de planes | V4–V6 / F3, F5–F6 | UI-AC-15, 25, 41–43 |

Registro integrado de versión e impacto, **2026-10-27: finalización del borrador, compatible con la dirección r14 seleccionada**. No se rediseñan las interacciones, la jerarquía, la navegación, los estados, la estructura adaptable, la paleta, la tipografía ni el movimiento. Se conservan los cuatro planes ya modificados, los seis roles de sistema de solo lectura, las doce concesiones, el explorador exclusivo de Master Designer y la renovación de sesión tras cambiar la contraseña propia. En comparación con la modificación canónica anterior, incluir Sempertex en ambos avisos es una aclaración de copia compatible que afecta a las expectativas de T2.3 para la activación y la nueva aceptación, y a la revisión de T2.7; T2.4/T2.5 conservan sus expectativas modificadas. T2.1 espera la aprobación independiente de esta instantánea exacta. Un registro de cambios independiente, una actualización del historial, un cambio en PLAN y una copia del contrato en el repositorio quedan fuera de las escrituras permitidas por esta delegación; este registro integrado proporciona trazabilidad sin redirigir a los consumidores.

`cuentas-admin@v1.html` se reconstruye directamente desde el TSX seleccionado e inmutable con el generador sin conexión CURRENT. No se explora ni edita el código fuente, y no se usa un TSX nuevo, una modificación del HTML generado, una instalación de paquetes ni una alternativa de respaldo. La etiqueta de dirección r14 del inspector identifica la fuente seleccionada y no concede aprobación. Los requisitos conductuales de producción que siguen son obligatorios; los controladores locales ilustrativos y la evidencia visual estática no sustituyen el comportamiento de account-service.

## 2. Propósito y usuarios

El administrador responde a “¿Quién tiene acceso, cuál es su rol y qué necesita cambiar?”. El registro completo con líneas separadoras mantiene juntos la identidad, el rol, el estado y la acción de gestión de cada persona. Las personas invitadas establecen una contraseña personal, aceptan el aviso y llegan a una herramienta permitida. Las personas con sesión iniciada se identifican, cambian su propia contraseña y cierran sesión.

La administración de cuentas requiere `cuentas.administrar`; la administración de roles requiere de forma independiente `roles.administrar`. Los nombres de rol o `internas.usar` nunca sustituyen estos permisos. El éxito significa un cambio confirmado por el servidor y un siguiente paso explícito. Los usuarios sin permiso ven un rechazo acotado sin datos restringidos.

El HTML etiqueta los datos como simulados y las operaciones como simuladas. Los datos de prueba de cuentas neutrales `@prueba.local` corresponden al vocabulario de pruebas del SPEC, no a identidades reales. Mi cuenta y el menú de cuenta identifican ambos a Cuenta administradora / admin@prueba.local; la activación identifica a Cuenta Master Designer / master@prueba.local. Los enlaces reservados de pictures.example nunca emiten acceso real. Los conteos derivan de las mismas filas de datos de prueba; los valores de último acceso y las fechas de aviso de ejemplo son ilustrativos.

## 3. Arquitectura y jerarquía de la información

Conservar la composición r14 seleccionada: encabezado compacto de anillo y punto de Pictures/Sempertex con controles de idioma y cuenta → encabezado de tarea de 24px → navegación horizontal neutral Cuentas / Roles y permisos / Mi cuenta en las superficies con sesión iniciada y permisos → un único espacio de trabajo → pie alineado. No hay contador de edición, barra lateral de planes, eslogan, muestra de materiales ni tarjeta promocional secundaria.

Las cuentas ocupan todo el ancho disponible del registro: Cuentas del piloto / Datos de ejemplo e Invitar persona → filtros de búsqueda/rol/estado → registros con separadores → recuento derivado de resultados y texto de zona horaria de Bogotá. En escritorio, los filtros comparten columnas flexibles con proporciones 2:1:1. Cada fila mantiene juntos el nombre/correo electrónico/empresa, el rol asignado, el estado, el último acceso y Gestionar.

Los roles conservan la composición de lista/editor: encabezado/Crear rol → seis roles de sistema de solo lectura y ejemplos personalizados → título y explicación del rol seleccionado → nombre del rol personalizado cuando se puede editar → cuatro grupos de campos de herramientas → guardar/eliminar y comentarios. La lista de escritorio tiene un ancho de 240px; el editor ocupa el espacio restante. Las subcapacidades más detalladas se explican mediante texto bajo la única concesión Taller.

El inicio de sesión, la activación, el restablecimiento, Mi cuenta y el aviso obligatorio usan un espacio de trabajo centrado con un ancho máximo de 676px y un eje de formulario de 620px, encabezado/comentarios concordantes y pie apilado. La activación muestra la identidad invitada antes de las contraseñas, el aviso completo antes del consentimiento sin marcar y el consentimiento antes del envío. El aviso obligatorio bloquea otras rutas del producto hasta que se acepte. Los cuadros de diálogo contextuales mantienen la invitación, la gestión de la cuenta seleccionada, el comprobante de un solo uso y la confirmación permanente junto al flujo de trabajo que los originó.

## 4. Sistema de diseño y lenguaje visual

### Nota de dirección en ocho ejes

| Eje | Expresión actual |
|---|---|
| Concepto | Un registro operativo de acceso: cuentas invitadas, rol asignado, estado de acceso y la siguiente acción de gestión. Sin paneles de marketing ni promoción de planes. |
| Diseño | Encabezado compacto de Pictures/Sempertex, título de página sobrio de 24px y regla horizontal de navegación conservada. Las cuentas ocupan todo el ancho del registro, con filtros equilibrados de búsqueda/rol/estado en proporciones 2:1:1; los roles usan un selector de 240px junto a la hoja de permisos. El acceso, la activación, el restablecimiento, el aviso y Mi cuenta usan un panel centrado de 676px y un eje compartido de formulario/comentarios de 620px, lo que elimina la mitad derecha vacía. |
| Navegación | Se conserva la navegación horizontal neutral Cuentas / Roles y permisos / Mi cuenta, los cuadros de diálogo contextuales de cuenta y la información de cuenta identificada por nombre. El acceso exclusivo por invitación no tiene una ruta de registro. Los selectores de planificación permanecen fuera del shell del producto. |
| Tipografía | Geist Sans y Geist Mono de producción, integradas desde la compilación local existente. Título de página de 24px, títulos de sección de 20px, texto principal de 14–16px y metadatos de 11–13px; sin tipografía de exhibición ni encabezado principal promocional. ES es el idioma inicial; EN está disponible mediante el selector de idioma. |
| Densidad | Se conservan el relleno de 24px en las filas de cuentas, los márgenes interiores del espacio de trabajo de 28px en escritorio / 20px en teléfono, los paneles de 32px, las superficies interiores de 24px, los campos de entrada de 18px, las casillas de verificación de 8px y los controles y chips de estado en forma de píldora. Los paneles de formularios ajustados al contenido tienen márgenes exteriores iguales; las vistas de gestión anchas conservan el espacio de trabajo disponible y los filtros flexibles. |
| Componentes | Button, Input, Checkbox, Skeleton, Dialog y AlertDialog de shadcn/Base UI instalados, compuestos como filas de cuentas y grupos de campos de permisos. Marca de anillo y punto de producción; paneles redondeados, estados semánticos en forma de píldora y navegación neutral. El texto de cierre de los cuadros de diálogo sigue el idioma ES/EN. Los seis roles de sistema del catálogo/personal siguen siendo de solo lectura; los cuatro planes acumulativos usan las etiquetas del catálogo. Ambos idiomas del aviso mencionan Sempertex y conservan los marcadores de posición del contacto para ejercer derechos y de la política. |
| Color | Paleta exacta de Pictures globals.css asignada como en proyectos@v1: modo claro #faf9fc / #ffffff con acciones #6d3fe0; modo oscuro #0b0c10 / #16181f con acciones #9479ff y texto principal #120b24. Tokens existentes de éxito/advertencia/error; los bordes de entrada toman el alias texto-tenue. Sin paleta exploratoria. |
| Movimiento | Se conserva el registro cinético: cubic-bezier(.76,0,.24,1), registro de espacios de trabajo/filas/reglas/estados de 480ms, desfases entre filas de 55ms y controles de 180ms; 300/140ms naturales y sutiles de 160/100ms. Se mantienen el barrido del esqueleto y el desplazamiento de la flecha al pasar el cursor o presionar; se elimina el movimiento retirado de la barra lateral y el papel metálico. Las opciones de movimiento reducido o estático desactivan el movimiento y las pestañas ocultas pausan la animación. |

Fuentes de producción inspeccionadas en modo de solo lectura: t12 y asesor `src/app/globals.css`, configuración de layout/fuentes, formulario de inicio de sesión, AdminTabs y CabeceraApp; contratos relacionados de planes@v1, proyectos@v1 y taller-esenciales@v1. Rigen los tokens/fuentes del producto y las asignaciones documentadas de productos relacionados. Algunos HTML integrados de productos relacionados conservan estilos exploratorios anteriores; no se importan esos estilos incompatibles. Se conserva la navegación horizontal, los formularios amplios y redondeados y el registro cinético seleccionados por el propietario. No se introduce ninguna paleta ni familia tipográfica nueva.

La asignación de roles del proyecto proviene de globals.css de ambos repositorios y de los roles compartidos correspondientes en proyectos@v1. Cada valor indicado a continuación ya existe en el producto; no se introduce ningún color nuevo.

| Fuente de Pictures | Rol en Kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | texto principal | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto secundario atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, texto sobre el primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | primario al pasar el cursor, anillo | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | borde decorativo, separador | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | campo de entrada (alias existente para controles accesibles en productos relacionados) | #766c85 / #8a91a0 |
| `--superficie-suave` | superficie suave del rol seleccionado | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | éxito, fondo suave de éxito | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | advertencia, fondo suave de advertencia | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, fondo suave de error | #b23a45, #ffeaec / #ff979f, #43252a |
| Color de texto destructivo existente | texto sobre el color destructivo | #ffffff / #3a0f13 |
| `--fondo` | fondo suave informativo, fondo suave primario | #faf9fc / #0b0c10 |

La tipografía es la Geist Sans / Geist Mono real de producción, integrada sin conexión desde los recursos WOFF2 locales en latín de la compilación t12 Next existente. No se descargan fuentes ni recursos. H1 es de 24px/1.25 en todos los anchos; el título de sección es de 20px/1.3 en escritorio; el texto principal es de 14–16px y los metadatos, de 11–13px; la tipografía monoespaciada se limita a identificadores/metadatos. Se conservan los tamaños de sección para teléfono y las formas amplias de r11. Se mantienen los roles de forma de r11: `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. Estas son las opciones de forma del borrador que el propietario decidió conservar, no nuevas decisiones de paleta ni tipografía de producción. El relleno de los espacios de trabajo y cuadros de diálogo se mantiene en 28px en escritorio y 20px en espacios de trabajo para teléfono / 24px en cuadros de diálogo para teléfono; las filas se mantienen en 24px en escritorio / 20px en teléfono.

Los componentes se nombran como **fuente:id variante estado**; todas las rutas hacen referencia a componentes realmente instalados, no a fragmentos de HTML:

| Nombre | Importación / composición |
|---|---|
| `shadcn:button default default\|hover\|focus\|pressed\|disabled\|loading` | `@/components/ui/button`, composición Action seleccionada; enviar, invitar y copiar como acciones principales |
| `shadcn:button outline default\|hover\|focus\|pressed\|disabled` | La misma importación; administración, recuperación, cancelación y navegación |
| `shadcn:button destructive default\|hover\|focus\|disabled\|loading` | La misma importación; confirmación explícita de eliminación permanente |
| `shadcn:input text\|email\|password default\|focus\|invalid\|disabled` | `@/components/ui/input`; Field personalizado asocia etiqueta, control y texto de ayuda; no es el Field estándar de shadcn |
| `shadcn:checkbox permission\|consent unchecked\|checked\|focus\|disabled` | `@/components/ui/checkbox`, mejora instalada de Animate UI/Base UI |
| `shadcn:skeleton record\|form loading` | `@/components/ui/skeleton` |
| `shadcn:dialog invitation\|management\|link open\|closed` | `@/components/ui/dialog`, mejora instalada de Animate UI/Base UI |
| `shadcn:alert-dialog account-delete\|role-delete open\|blocked\|pending\|closed` | `@/components/ui/alert-dialog`, mejora instalada de Animate UI/Base UI |
| `native:select role\|status\|language default\|focus\|disabled` | Select nativo de HTML con etiqueta; no se afirma que sea shadcn Select |
| `native:details account closed\|open` | Panel desplegable de cuenta con nombre, con Mi cuenta y cierre de sesión; no modal |
| `custom:access-register ruled normal\|loading\|empty\|error` | `.register-head`, `.person-row`, `.identity`, `.footline` |
| `custom:permission-sheet grouped system-readonly\|custom-editable\|validation` | `.role-layout`, `.role-list`, `.role-editor`, fieldset/legend |
| `custom:app-header compact normal` | `.masthead`, `.heading`, `.route-nav`; marca de anillo y punto de Pictures |
| `custom:message ruled error\|success` | `.message` con semántica de alerta/estado |

`mountMockup` / `useMockup` se importan desde `@kit/mockup`; `useMotionProfile` desde `@kit/motion`. El espacio de trabajo local sin conexión incluye React, controles, fuentes y movimiento. No se usó CDN, instalación de paquetes, solicitud externa de imágenes o fuentes ni alternativa basada en HTML simple.


**Movimiento: registro cinético, sin cambios respecto a la fuente r14 seleccionada.** `useMotionProfile()` proporciona el perfil y el estado de movimiento reducido. Cubic-bezier(.76,0,.24,1); papel, filas, reglas y estados expresivos: 480ms con desfases de 55ms entre filas; controles: 180ms; natural: 300/140ms; sutil: 160/100ms. El papel se desplaza verticalmente 12px, las filas horizontalmente 14px y las reglas/estados 6px. Los botones se elevan −2px al pasar el cursor y se presionan 1px con scale(.98); las flechas se desplazan 3px. El barrido del esqueleto se repite cada 1.4s. No se reintroduce el movimiento retirado del riel o del foil. El texto legible permanece visible. Las pestañas ocultas pausan la animación; no queda animación decorativa fuera de pantalla. El movimiento reducido del sistema operativo, Quieto y `?still=1` suprimen el movimiento y los efectos repetitivos, conservan la disposición final y mantienen todas las acciones.

## 5. Navegación y modelo de interacción

| Vista | Ruta del producto / permiso | Valor de vista previa |
|---|---|---|
| V1 iniciar sesión | `/login?from=<relative-path>`; pública | `view=login` |
| V2 activar | `/activar/<token>`; invitación pública válida | `view=activar` |
| V3 restablecer | `/restablecer/<token>`; restablecimiento público válido | `view=restablecer` |
| V4 cuentas | `/admin/cuentas`; `cuentas.administrar` | `view=cuentas` |
| V5 roles/editor | `/admin/roles`; `roles.administrar` | `view=roles` |
| V6 cuenta propia | `/cuenta`; sesión activa | `view=cuenta` |
| V7 aviso obligatorio | `/aviso-datos?from=<relative-path>`; sesión activa | `view=aviso` |

La invitación, la administración y el enlace son diálogos contextuales de V4, y la edición de roles se realiza en línea en V5. No conserves como requisitos las rutas de subvista mediante parámetros de consulta inventadas en el borrador anterior. SP-1 es responsable de `/sin-acceso`; la fixture `sin-permiso` muestra su rechazo visual acotado y la opción de recuperación Mi cuenta. No autoriza una nueva ruta ni revela un recurso denegado.

Al iniciar sesión correctamente, usa un destino relativo seguro del mismo origen al que se tenga permiso; de lo contrario, usa primero Taller 3D, luego Chat, después Catálogo y, si no se permite ninguno, `/cuenta` (T2.3). La activación crea una sesión y usa la misma alternativa según las herramientas permitidas, sin exigir otro inicio de sesión. Después de aceptar el aviso, vuelve a validar el destino guardado y los permisos vigentes. No simules como página autenticada funcional ninguna herramienta fuera de SP-2. La siguiente solicitud aplica en el servidor la desactivación y los cambios de permisos y roles.

Las páginas con sesión iniciada muestran el nombre y el rol de la cuenta, además de Mi cuenta y Cerrar sesión; el resumen compacto mantiene el nombre y el despliegue revela el rol. Muestra los enlaces Cuentas y Roles solo cuando se tengan los permisos correspondientes, que son independientes. La vista estática proporciona la fixture del administrador; no es un servicio de permisos. En V7 conserva la identidad y la opción de cerrar sesión, pero oculta los otros destinos del producto hasta que se acepte el aviso. Los controles de vista previa son elementos externos de inspección, nunca una forma de eludir las restricciones del producto.

La navegación enfoca el encabezado de la página nueva; un envío no válido anuncia el error y enfoca el primer campo no válido. La búsqueda y los filtros conservan el foco mientras se escribe. Al abrirse un diálogo, el foco pasa a su interior, queda contenido dentro, el fondo se vuelve inerte y, al cerrarlo, se restaura en la acción que lo abrió. La invitación, la administración y el enlace admiten Escape; los diálogos destructivos requieren Cancelar o Confirmar explícitamente y empiezan con Cancelar seleccionado. Si hay una mutación de datos pendiente, desactiva los envíos repetidos; evita cerrar una solicitud ya confirmada como si se hubiera cancelado. El despliegue nativo de la cuenta usa semántica de disclosure, no un patrón parcial de menú ARIA; las acciones de teclado mantienen el foco visible.

La barra de la maqueta conserva los controles nativos `view`, `state`, `scene`, `theme`, `motion` y las etiquetas Vista, Estado, Diálogo, Tema y Movimiento. Se puede acceder a todos los estados y escenas de vista previa declarados. El selector de idioma del producto es ES/EN; comienza en ES en este artefacto de inspección seleccionado, y EN se puede seleccionar explícitamente. En el producto, el aviso de invitación sigue inicialmente el idioma del navegador; después, la preferencia de idioma guardada sigue SP-8/SP-10. La selección en la vista previa no guarda la configuración de la cuenta ni cambia los permisos del servidor. El despliegue de traducciones sigue PLAN: las cadenas en español de SP-2 permanecen agrupadas para SP-8/SP-10; el aviso es bilingüe desde el inicio. Esta referencia visual bilingüe no afirma que esas tareas posteriores estén implementadas.

## 6. Flujos

**F1 — Iniciar sesión.** Ingresar correo/contraseña invitados → enviar una sola vez → carga → destino seguro confirmado por el servidor. La contraseña incorrecta, el correo desconocido, la cuenta desactivada y el correo bloqueado usan el mismo rechazo: “Revisa el correo y la contraseña. Después de varios intentos fallidos debes esperar quince minutos.” Inglés: “Check your email and password. After several failed attempts you must wait fifteen minutes.” No exponer existencia/estado/contadores de intentos. SP-1 bloquea un correo tras cinco fallos en quince minutos durante quince minutos; la UI siempre muestra la pista neutral. El texto de solo invitación y la recuperación emitida por el administrador son visibles; no hay registro abierto ni restablecimiento automático por correo. Las sesiones duran 30 días bajo SP-1 y terminan al cerrar sesión/desactivar/cambiar contraseña, como se especifica más adelante.

**F2 — Activar.** Validar la invitación sin consumirla al cargar → mostrar nombre/correo del invitado → nueva contraseña y confirmación → aviso vigente completo en el idioma del navegador/seleccionado → consentimiento sin marcar → Activar deshabilitado hasta marcarlo → envío válido explícito. La contraseña tiene de 8 a 200 caracteres, la confirmación es igual; permitir gestor de contraseñas/pegado. Solo la activación confirmada almacena la versión/fecha del aviso, consume el token de un solo uso de siete días, crea una sesión y abre la primera herramienta permitida o Mi cuenta. Los enlaces vencidos, usados o reemplazados usan una única recuperación genérica `LINK_INVALIDO`, ocultan el ingreso de contraseña y piden al administrador un enlace nuevo; no revelar qué condición ocurrió ni datos del destinatario a partir de un enlace inválido. El destino Taller 3D del dato de prueba es un ejemplo para su rol Master Designer, no un destino impuesto a todos los roles.

**F3 — Invitar.** Cuentas → Invitar persona → nombre/correo obligatorios, empresa opcional, exactamente un rol/plan en orden de catálogo (Entusiasta, Designer, Designer Plus, Master Designer), luego Empleado interno, Administrador y roles personalizados → Generar invitación → pendiente → comprobante del enlace de un solo uso confirmado por el servidor. Un correo registrado devuelve `CORREO_REGISTRADO` y “Este correo ya está registrado. Gestiona su cuenta existente.” sin crear otra invitación. El comprobante nombra al destinatario, el uso único/vigencia y el envío manual; nada afirma entrega por correo. Copiar informa éxito solo después de que el portapapeles lo logre; si falla, indica seleccionar/copiar manualmente el enlace con salto de línea. Al cerrar/salir se elimina el comprobante. Generar una nueva invitación desde el diálogo de gestión de una cuenta invitada para recuperar un comprobante perdido/vencido; explicar antes de generar y en el comprobante que todas las invitaciones anteriores sin usar de esa cuenta quedan inválidas. Los tipos restablecimiento e invitación no se revocan entre sí.

**F4 — Restablecimiento por el administrador.** Gestionar una cuenta existente → Generar restablecimiento → explicar que los restablecimientos anteriores sin usar quedan inválidos, el nuevo enlace es de un solo uso durante 24 horas → generar/copiar/cerrar una vez. El destinatario abre V3 → nueva contraseña dos veces, de 8 a 200 caracteres y coincidentes → el restablecimiento confirmado revoca las sesiones → iniciar sesión con la nueva contraseña. No se agrega un nuevo consentimiento de aviso al restablecimiento; la recuperación por enlace inválido coincide con F2. Generar un restablecimiento no afirma por sí mismo que una contraseña haya cambiado.

**F5 — Administración de cuentas.** Buscar por nombre/correo y filtrar por rol/estado → Gestionar la fila seleccionada → leer la identidad y elegir un rol de esa misma lista ordenada de catálogo/personal/personalizados → Guardar rol; los efectos se aplican en la siguiente solicitud. Desactivar termina las sesiones y conserva el trabajo guardado; Reactivar restablece el acceso sujeto al mismo rol y aviso. El último Administrador activo no puede ser desactivado/eliminado/degradado (`ULTIMO_ADMIN`); la Cuenta administradora del dato de prueba es el último administrador, no una regla de que todos los administradores sean inmutables. Los proyectos/decoraciones guardados o cualquier fila de trabajo guardado registrada bloquean la eliminación (`CUENTA_CON_TRABAJO`) y no cambian nada; explicar la desactivación como alternativa. El gasto por sí solo no es trabajo guardado. Solo una cuenta sin trabajo puede continuar al AlertDialog de eliminación permanente; exigir el correo exacto coincidente, explicar la irreversibilidad y la retención del gasto anónimo como “Cuenta eliminada”. La elegibilidad desconocida u obsoleta nunca habilita la eliminación; volver a verificar al confirmar. Manejar un rechazo concurrente en el mismo lugar con datos autoritativos actualizados y sin afirmar éxito. La edición de perfil, las operaciones masivas y la transferencia de cuentas quedan fuera del alcance.

**F6 — Roles y planes.** Seleccionar uno de los seis roles de sistema para inspeccionar sus permisos de solo lectura → o Crear rol → nombre y casillas independientes inicialmente sin marcar agrupadas por herramienta → exigir al menos un permiso (`ROL_SIN_PERMISOS`) → Guardar el rol personalizado confirmado. Al editar se cargan los permisos realmente seleccionados de ese rol; nunca hereda el estado transitorio de casillas de otro rol. Los roles de sistema no pueden editarse/eliminarse (`ROL_SISTEMA`). Los roles personalizados asignados rechazan la eliminación (`ROL_EN_USO`) y explican que primero se debe asignar otro rol; los roles personalizados sin asignar usan la confirmación de eliminación permanente. El conteo de asignados mostrado debe provenir de asignaciones reales de cuentas, no de la posición en la lista. No existe un campo de plan aditivo separado: los cuatro planes de acceso son roles de Usuario, un rol por cuenta; los roles de personal/personalizados los siguen. Los roles personalizados siguen siendo independientes de los planes. Leer nombres, orden y permisos de los planes directamente de plan-catalogue@1 en lugar de copiar la lógica de niveles en SP-2.

**F7 — Contraseña propia.** Menú desplegable de cuenta → Mi cuenta → leer la propia identidad/empresa/rol y la versión/fecha del aviso → ingresar la contraseña actual, la nueva y la confirmación → validar → confirmar el éxito del servicio. Una contraseña actual incorrecta es accionable sin terminar la sesión válida. El servicio termina todas las sesiones anteriores y T2.2 abre una nueva para el navegador solicitante; limpiar los campos secretos y anunciar “Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.” La persona permanece con sesión iniciada aquí; los demás navegadores deben iniciar sesión de nuevo. Esto es distinto del restablecimiento F4. No se introduce la edición propia de correo/perfil/rol.

**F8 — Actualización del aviso.** En la siguiente solicitud después de un cambio de versión del aviso, reemplazar el contenido solicitado con V7 → mostrar la versión completa y el consentimiento sin marcar → aceptar y guardar exactamente esa versión y fecha → ir al destino permitido o cerrar sesión para volver a V1. No se puede omitir ni posponer, y no hay enlaces al producto subyacente antes de aceptar. Si la versión mostrada cambia mientras el aviso está abierto, descarta el consentimiento para el texto anterior y solicita uno nuevo. Si hay un error o el servicio no está disponible, conserva la entrada para esa versión, permite reintentar explícitamente y no simula que se registró el éxito. El texto v1 del aviso en la vista previa es un ejemplo ilustrativo de aceptación renovada, no un texto legal v2 inventado.

## 7. Especificaciones de vistas

| Vista | Estructura / texto y datos | Acciones y flujo relacionado |
|---|---|---|
| V1 | “Iniciar sesión” / “Iniciar sesión”; Iniciar sesión, correo/contraseña, explicación de acceso solo por invitación, indicaciones para restablecer la contraseña por parte del administrador | Entrar; error genérico/reintentar; F1 |
| V2 | “Activar cuenta” / “Activar cuenta”; nombre/correo de la persona invitada, contraseña nueva/repetida, aviso completo, consentimiento sin marcar, explicación de siete días | Activar cuenta deshabilitado hasta aceptar el consentimiento; reemplazo de enlace no válido/Volver al acceso; F2 |
| V3 | “Restablecer contraseña” / “Restablecer contraseña”; introducir la contraseña nueva dos veces; explicación de uso único durante 24 horas | Guardar contraseña y luego iniciar sesión; reemplazo de enlace no válido; F4 |
| V4 | “Cuentas” / “Cuentas”; Cuentas del piloto / Datos de ejemplo, filtros y cinco registros ilustrativos completos de cuentas, cantidad de resultados/zona horaria | Invitar persona, Gestionar, borrar filtros, reintentar; F3/F5 |
| V5 | “Roles y permisos” / “Roles y permisos”; lista de seis roles del sistema y roles personalizados, nombre seleccionado, grupos de permisos y explicación del paquete Taller | Crear rol, Guardar rol, Eliminar rol si es personalizado; estado del sistema de solo lectura; F6 |
| V6 | “Mi cuenta” / “Mi cuenta”; identidad/empresa/rol de la sesión actual, contraseña actual/nueva/repetida, versión/fecha | Cambiar contraseña; mensaje de renovación de la sesión iniciada; aviso sobre cuenta compartida; F7 |
| V7 | “Aviso de tratamiento de datos personales” / “Aviso de tratamiento de datos personales”; Aviso actualizado, explicación de bloqueo, texto completo con versión, consentimiento sin marcar | Aceptar y continuar, Cerrar sesión; sin otras rutas del producto; F8 |

Escenas contextuales (`scene`): `invitar` = formulario de nombre/correo/empresa/un rol; `gestionar` = identidad seleccionada, rol, regenerar/restablecer, desactivar/reactivar y eliminar con motivos en línea; `enlace` = destinatario, enlace seleccionable, aviso sobre vigencia/uso único/reemplazo, Copiar y Listo; `eliminar` = rechazo de cuenta o confirmación con correo exacto; `eliminar-rol` = rechazo de rol o confirmación de eliminación permanente. Una `scene` vacía es Ninguna. No se requiere ninguna otra vista exploratoria.

El catálogo de permisos tiene **12 permisos**, proporcionados una sola vez por SP-1. Las seis capacidades de Taller son texto complementario de un único `taller.usar`; nunca deben convertirse en casillas independientes ni en claves de permisos inventadas. Conservar los cuatro grupos de campos y la geometría elegida para el editor.

| Grupo de herramientas | Clave → etiqueta en ES / EN |
|---|---|
| Planificación | `chat.usar` → Chat asistido / Chat asistido; `contador.usar` → Contador de globos / Contador de globos; `catalogo.ver` → Catálogo / Catálogo; `costos.usar` → Calculadora de costos / Calculadora de costos; `decoraciones.explorar` → Explorador de decoraciones / Explorador de decoraciones |
| Taller 3D | `taller.usar` → Taller 3D / Taller 3D. Incluye IA de escena, planes de montaje/hoja de construcción, exportación, proyectos propios y decoraciones; no hay capacidades secundarias seleccionables de forma independiente. |
| Herramientas internas | `proyectos.ver_todos` → Proyectos de todos / Proyectos de todos; `gasto.ver` → Consumo de IA / Consumo de IA; `internas.usar` → Herramientas internas / Herramientas internas |
| Administración | `cuentas.administrar` → Gestionar usuarios / Gestionar usuarios; `roles.administrar` → Gestionar roles / Gestionar roles; `textos.corregir` → Corregir textos en inglés / Corregir textos en inglés |

Roles del sistema, en el orden exacto del selector/lista:

| Rol del sistema ES / EN | Permisos otorgados (solo lectura) | Cantidad |
|---|---|---|
| Usuario · Entusiasta / Usuario · Entusiasta | chat, contador, catálogo | 3 |
| Usuario · Designer / Usuario · Designer | Igual que Entusiasta; sin permisos adicionales ni límite numérico de chat | 3 |
| Usuario · Designer Plus / Usuario · Designer Plus | Permisos de Entusiasta + costos | 4 |
| Usuario · Master Designer / Usuario · Master Designer | Permisos de Designer Plus + Taller + explorador de decoraciones listas para usar | 6 |
| Empleado interno / Empleado interno | Todos los permisos de Master Designer + proyectos de todos, consumo y herramientas internas | 9 |
| Administrador / Administrador | Todos los permisos, incluida la administración de cuentas/roles/textos | 12 |

No existe un séptimo Usuario genérico. Los roles personalizados aparecen después de los seis roles del sistema y mantienen casillas independientes, sin herencia silenciosa. `proyectos.ver_todos` permite leer originales de otras personas; con `taller.usar` se puede guardar una copia propia, nunca editar el original (SPEC ronda 9). Las rutas/servicios usan claves, nunca etiquetas traducidas. Disponibilidad y asignación son conceptos distintos: no inventar permisos adicionales seleccionables para chat extendido, detección de estructura o detección avanzada de globos. T1.2 marca actualmente esos tres elementos como no disponibles y conserva el permiso de costos con Designer Plus; cambiar la etiqueta del rol no habilita ninguna herramienta.

**Datos compartidos del catálogo (R17, datos de referencia, no una nueva pantalla de precios de SP-2):**

| Orden | Nombre ES / EN | COP mensual | USD mensual |
|---|---|---|---|
| 1 | Entusiasta / Entusiasta | Gratis | Gratis |
| 2 | Designer / Designer | 20,000 | 7 |
| 3 | Designer Plus / Designer Plus | 45,000 | 14 |
| 4 | Master Designer / Master Designer | 70,000 | 25 |

El TSX simulado contiene un único registro de catálogo de planes, claramente identificado (nombres, precios en ambas monedas, herramientas acumulativas con disponibilidad y permisos seleccionados). Las opciones de rol y las marcas de planes leen ese registro; no mantienen listas paralelas de niveles. Producción lee el catálogo real de SP-1; este registro de diseño no es una nueva fuente de datos de producción. Ni las invitaciones ni la gestión de cuentas agregan precios, acciones de compra o un selector de planes independiente. Entusiasta/Designer tienen permisos idénticos actualmente; el responsable aplazó los límites numéricos de chat, por lo que no se inventan valores ni controles de límite. La comparación completa, el texto de funciones no disponibles y los enlaces de acceso corresponden a SP-14.

El aviso completo conserva el cuerpo de SPEC v1 con la sustitución de Sempertex, autorizada por el responsable, en lugar del marcador de posición del nombre legal en ambos idiomas. El correo de contacto para ejercer derechos y la URL de la política permanecen como marcadores entre corchetes, tal como se solicitó explícitamente; se mantiene visible la anotación existente de revisión legal. No se inventan hipervínculos a políticas, direcciones de contacto ni declaraciones de que la revisión legal haya concluido.

**ES — Aviso de tratamiento de datos personales (versión 1)**

Sempertex tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a [CORREO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.

**EN — Aviso de tratamiento de datos personales (versión 1)**

Sempertex tratará tus datos personales —nombre, correo, empresa (si la proporcionas), el rol y plan que se te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el uso de inteligencia artificial. Los proyectos y decoraciones que guardes estarán asociados a tu cuenta. Puedes acceder a tus datos, actualizarlos, rectificarlos o solicitar su eliminación, y revocar esta autorización, escribiendo a [CORREO DE CONTACTO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta confirmas que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley colombiana 1581 de 2012.

## 8. Estados

La vista previa global permite intencionalmente combinaciones de vista/estado no relacionadas. El comportamiento aplicable del producto se define a continuación; no se debe implementar una combinación absurda solo porque el inspector pueda seleccionarla.

| Id / etiqueta de vista previa | Resultado aplicable, acción y recuperación |
|---|---|
| `normal` / Normal | Formulario/registro editable; roles del sistema válidos de solo lectura; sin solicitud pendiente. |
| `cargando` / Cargando | Esqueletos de cuentas/roles/formulario y acción en procesamiento; sin envío duplicado ni mutación pendiente editable. Nunca se debe sugerir cero registros durante la carga. |
| `vacio` / Vacío | Explicación de cuentas sin coincidencias/vacío inicial. El vacío filtrado ofrece borrar filtros; el vacío inicial real dirige a Invitar. Los seis roles del sistema no pueden ser un catálogo vacío. |
| `error` / Error | Las lecturas de cuentas/roles ocultan las filas no confirmadas y ofrecen Reintentar. Los formularios conservan la entrada segura, describen el fallo y permiten reintentar. El inicio de sesión usa el mismo rechazo genérico de quince minutos para cualquier causa del servicio. |
| `exito` / Éxito | Resultado confirmado específico de cada vista: destino con sesión iniciada; activada/sesión; restablecimiento/inicio de sesión; contraseña propia/nueva sesión; versión/fecha del aviso; rol/cuenta guardados. Ningún éxito antes del reconocimiento autoritativo. |
| `validacion` / Validación | Error anunciado y control inválido, identidad requerida/contraseña actual, contraseña nueva de 8–200 caracteres y coincidente, selección de nombre/rol y al menos un permiso personalizado. Conservar la entrada, enfocar la corrección. |
| `sin-permiso` / Sin permiso | Rechazo acotado sin formulario ni filas restringidos; solicitar permiso, abrir Mi cuenta o cerrar sesión. El servicio sigue aplicando 403. |
| `enlace-vencido` / Enlace vencido o usado | Formulario de V2/V3 reemplazado por una única recuperación de enlace inválido; sin envío de contraseña ni divulgación de causa/identidad. |
| `duplicado` / Correo duplicado | Invitación rechazada; correo marcado, gestionar la cuenta existente; sin nuevo enlace/cuenta. |
| `con-trabajo` / Cuenta con trabajo | Eliminación rechazada sin cambios con `CUENTA_CON_TRABAJO`; explicar la desactivación; confirmar deshabilitado. |
| `ultimo-admin` / Último administrador | No se puede eliminar/desactivar/degradar al último administrador activo; explicar la protección y deshabilitar/rechazar la mutación. |
| `rol-en-uso` / Rol en uso | Eliminación de rol personalizado asignado rechazada; reasignar primero las cuentas; el estado de solo lectura de los roles del sistema sigue siendo independiente. |

Los estados de control incluyen predeterminado, hover, foco, presionado, deshabilitado, cargando, inválido y consentimiento/permisos marcados/sin marcar. El comprobante de un solo uso tiene éxito de copia y alternativa de copia manual. La divulgación de la cuenta tiene estados abierto/cerrado. La eliminación con correo exacto permanece deshabilitada hasta que coincida exactamente; “pendiente” también deshabilita la confirmación.

Las lecturas sin conexión, incompletas u obsoletas comparten la presentación de error recuperable: ningún guardado sin confirmar, ningún conteo engañoso presentado como autoritativo ni mutación sin restricciones basada en una elegibilidad obsoleta. Conservar localmente la entrada segura, explicar el reintento, volver a consultar el rol/elegibilidad/aviso autoritativo según corresponda; un aviso modificado restablece el consentimiento. No son necesarias nuevas rutas distintas de sin conexión/conflicto. Un conjunto de datos de roles del sistema vacío y el registro público de autoservicio no aplican, porque los roles del sistema están precargados y el acceso es por invitación. La IA de pago, los gráficos de consumo, el guardado de proyectos, la finalización legal, la resolución de condiciones de carrera en la base de datos y los mecanismos reales de token/sesión no se simulan como prueba de este artefacto.

## 9. Comportamiento adaptable

Ancho mínimo admitido por el contrato: **360px**. Se espera desplazamiento vertical para contenido extenso de avisos, editores y diálogos. No debe haber desplazamiento horizontal de la página ni controles esenciales recortados en ninguno de los temas o idiomas. El CSS seleccionado usa transiciones en 760px y 1100px.

| Rango | Diseño |
|---|---|
| **1101px+** | `.app` con ancho máximo de 1520px y 40px de relleno lateral; margen interior del papel de 28px. Un espacio de trabajo de cuentas/registro de ancho completo; filtros en proporción 2:1:1; cuatro columnas de registros alineadas, con 24px de relleno vertical por fila. Lista de roles de 240px junto al editor, permisos en dos columnas. Espacio de trabajo, encabezado y pie del formulario limitados a 676px y centrados; contenido del formulario con ancho máximo de 620px. |
| **761–1100px** | Relleno exterior de 28px; papel de 28px; el campo de búsqueda ocupa ambas columnas de filtros. La acción de cuenta aparece después de los campos del registro; lista de roles de 200px junto al editor; permisos en una columna. El panel del formulario permanece centrado, con límite de 676px. |
| **360–760px** | Relleno exterior y del papel de 20px; los controles del encabezado se ajustan a varias líneas, el nombre permanece visible y la divulgación muestra el rol. H1 permanece en 24px. Los filtros y grupos de campos/identidad se apilan; la identidad de la cuenta ocupa la fila completa y los campos de rol/estado se reorganizan debajo, seguidos de Gestionar. Las filas tienen 20px de relleno vertical. El selector de roles se apila antes del editor y un divisor horizontal reemplaza al divisor izquierdo. Las acciones se apilan a ancho completo. El panel del formulario se ajusta al espacio disponible. La confirmación ocupa el ancho del papel y su texto se alinea con el margen interior del campo. |

Los diálogos conservan un ancho máximo de `min(560px, 100vw − 32px)`, relleno de 28px en escritorio/24px en teléfono, altura máxima de `100svh − 48px` y desplazamiento vertical. El radio del papel y los diálogos es de 32px; el de avisos/confirmaciones, 24px; el de campos/rol seleccionado, 18px; el de casillas, 8px; y el de botones/selectores/etiquetas de estado/divulgación de cuenta, 999px. El aviso en teléfono tiene 16px de relleno. El pie de administración principal usa el eje del espacio de trabajo; el pie del formulario se apila en su eje de 676px. Revisar 390/768/1280px y el mínimo de 360px; las cadenas en inglés deben ajustarse sin un diseño nuevo.

## 10. Objetivos de accesibilidad

El objetivo es WCAG 2.2 AA para el contenido y las interacciones aplicables; esta descripción y la auditoría automatizada no certifican conformidad. El contraste objetivo del texto es ≥4.5:1; el del texto grande, ≥3:1 según la excepción aplicable; el de los bordes de controles significativos y el foco, ≥3:1. Conserva el anillo de foco de 3px con un desplazamiento de 4px. Las acciones principales de trabajo miden al menos 44px de alto; las etiquetas de las casillas amplían el área de interacción, aunque el cuadro visual sea pequeño. Prueba el zoom y el reajuste del diseño al 200 % y con un ancho equivalente a 320px CSS; el límite visual contractual es 360px y la verificación con zoom del navegador sigue siendo evidencia pendiente explícita.

Usa encabezados jerárquicos, puntos de referencia para contenido principal/navegación, etiquetas/campos/ayudas/errores asociados, autocompletado de tipo correo/contraseña, grupos con nombre accesible mediante fieldset/legend y botones/selectores nativos reales. Usa el estado para los resultados correctos y alertas para los errores; no dependas de iconos ni del color. Los identificadores de permisos se normalizan sin espacios para que se resuelvan las etiquetas accesibles de Base UI. En producción, asocia los resúmenes/errores de campo con sus controles y expón el estado de solicitud en curso. Se permite pegar y autocompletar contraseñas; no se fuerzan interacciones cronometradas.

Mantén el foco al escribir en búsquedas/formularios, el foco al cambiar de ruta, la contención del foco en diálogos, el fondo inerte y la devolución del foco al cerrar. Las confirmaciones destructivas comienzan con Cancelar como opción segura y requieren confirmar la cuenta mediante el correo exacto. No sugieras que se pueden modificar controles del sistema inaccesibles y de solo lectura. El consentimiento es explícito y aparece desmarcado inicialmente para cada activación/versión nueva del aviso. El movimiento reducido o desactivado suprime toda animación y conserva el contenido final, el foco, la alineación del diálogo y la respuesta inmediata; no debe haber parpadeos, texto oculto ni estados ilegibles durante una animación.

El inspector sin conexión y las comprobaciones automatizadas miden el funcionamiento renderizado. Las sesiones manuales con lectores de pantalla, todos los niveles de zoom, el comportamiento completo del teclado en avisos expandidos, las pruebas entre navegadores, los errores reales del servidor y el enrutamiento de producción requieren verificación posterior durante la implementación. Consérvalos como objetivos, sin afirmar que los controladores ilustrativos locales los implementan.

## 11. Criterios de aceptación visual y verificación

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 1101px+ | cuentas normales | El título de tarea de 24px aparece sobre un único panel de cuentas reglado que ocupa todo el ancho; no hay celda de edición, carril ni tarjeta de material. |
| UI-AC-02 | 1101px+ | cuentas normales | Cada registro agrupa visiblemente el nombre, correo electrónico, empresa, rol, estado, último acceso y la opción Gestionar. |
| UI-AC-03 | 360–760px | cuentas normales | La identidad ocupa el ancho del registro; el rol, el estado y la opción Gestionar se reorganizan debajo sin desbordar la página. |
| UI-AC-04 | 761–1100px | cuentas normales | La búsqueda ocupa ambas columnas de filtros y la opción Gestionar sigue a los demás campos de la fila. |
| UI-AC-05 | 360px+ | cuentas filtradas/vacías | El recuento de resultados coincide con los registros mostrados; al borrar los filtros se restaura el registro sin filtrar. |
| UI-AC-06 | 360px+ | cargando | Los esqueletos reemplazan el contenido aún no resuelto y el envío pendiente no se puede repetir. |
| UI-AC-07 | 360px+ | error de cuentas/roles | Las filas sin confirmar no aparecen y la opción Reintentar está visible. |
| UI-AC-08 | 360px+ | error de inicio de sesión | Las mismas denegación e indicación de espera de quince minutos aparecen para las cuatro causas de rechazo de credenciales. |
| UI-AC-09 | 360px+ | activación normal | Los dos controles de contraseña y el aviso completo aparecen antes del consentimiento sin marcar y de la opción Activar deshabilitada. |
| UI-AC-10 | 360px+ | consentimiento marcado | Al marcar el consentimiento se habilita una activación válida y el mensaje de éxito explica que la sesión está activa y se inició. |
| UI-AC-11 | 360px+ | invitación/restablecimiento inválidos | La entrada de contraseña se reemplaza por la recuperación mediante un enlace emitido por el administrador, sin revelar información específica de la causa. |
| UI-AC-12 | 360px+ | invitación | El nombre, el correo electrónico, la empresa opcional y un rol preceden a la generación; un correo electrónico duplicado produce una denegación. |
| UI-AC-13 | 360px+ | comprobante de un solo uso | Se muestran el destinatario, el enlace seleccionable con ajuste de línea, la opción Copiar, el uso único, la vigencia y la advertencia de reemplazo. |
| UI-AC-14 | 360px+ | comprobante cerrado | El comprobante cerrado no permite recuperar su enlace anterior; la recuperación consiste en generarlo de nuevo. |
| UI-AC-15 | 360px+ | roles del sistema | Exactamente seis roles del sistema son de solo lectura y tienen 3/3/4/6/9/12 permisos seleccionados, en el orden del catálogo y del personal. |
| UI-AC-16 | 360px+ | rol personalizado | Cuatro grupos de herramientas contienen doce permisos disponibles; Taller es una casilla con texto auxiliar que indica que agrupa capacidades. |
| UI-AC-17 | 360px+ | validación de rol | Al guardar un rol personalizado con nombre y sin permisos, se anuncia ROL_SIN_PERMISOS y se conserva la edición. |
| UI-AC-18 | 360px+ | rol en uso | La eliminación permanente está deshabilitada y se muestra la explicación de que primero hay que reasignar. |
| UI-AC-19 | 360px+ | trabajo guardado/último administrador | La denegación explica el invariante y la confirmación de eliminación permanente está deshabilitada. |
| UI-AC-20 | 360px+ | eliminación de cuenta sin trabajo | La eliminación permanente está deshabilitada hasta que el correo electrónico escrito coincida exactamente con el de la cuenta seleccionada. |
| UI-AC-21 | 360px+ | cuenta propia | La identidad coincide con la información de la cuenta y la contraseña actual precede al par de contraseñas nuevas. |
| UI-AC-22 | 360px+ | contraseña propia cambiada correctamente | El mensaje indica que se renovó la sesión de este navegador y que terminaron las sesiones anteriores; no se indica que haya que iniciar sesión otra vez. |
| UI-AC-23 | 360px+ | restablecimiento exitoso | El mensaje pide a la persona que inicie sesión con la nueva contraseña. |
| UI-AC-24 | 360px+ | barrera del aviso | Están presentes el aviso completo con versión, el consentimiento sin marcar y la opción para cerrar sesión; no aparece el resto de la navegación del producto. |
| UI-AC-25 | 360px+ | rol de cuenta cambiado | El rol único seleccionado se actualiza con un texto que explica que se aplicará en la siguiente solicitud; las etiquetas de los planes siguen siendo acumulativas. |
| UI-AC-26 | 360px+ | tema claro/oscuro | Los bordes de los campos, los estados de las casillas, las acciones de contorno y el foco son visibles sobre sus superficies reales. |
| UI-AC-27 | 360px+ | animación expresiva | Los paneles se animan verticalmente, los registros horizontalmente y las líneas y mensajes de estado con trazos breves, usando la aceleración y los tiempos seleccionados en r14, con texto legible. |
| UI-AC-28 | 360px+ | movimiento reducido/sin movimiento | No queda ninguna animación en ejecución ni diálogo desplazado; los mismos controles y contenidos siguen siendo utilizables. |
| UI-AC-29 | 360px+ | invitación abierta/cerrada | El foco del tabulador se mantiene dentro del diálogo; al cerrarlo, se restaura el foco en la acción que lo inició. |
| UI-AC-30 | 360px+ | ES/EN | Los encabezados, las etiquetas, los avisos y las acciones del diálogo se reorganizan sin desplazamiento horizontal de la página. |
| UI-AC-31 | 360–760px | roles normales | El selector de roles se apila antes del editor de permisos, con su divisor horizontal. |
| UI-AC-32 | 761px+ | inicio de sesión/activación/restablecimiento/Mi cuenta/aviso | El espacio del formulario no supera los 676px; está centrado con márgenes exteriores iguales y los campos se mantienen dentro de un eje de 620px. |
| UI-AC-33 | 761px+ | error/éxito/enlace inválido del formulario | El encabezado, los mensajes, la recuperación y el pie apilado siguen el eje del formulario centrado. |
| UI-AC-34 | 1101px+ | cuentas normales | Los filtros de búsqueda, rol y estado ocupan columnas flexibles en proporción 2:1:1 a lo ancho del registro. |
| UI-AC-35 | 1101px+ | roles normales | El selector de roles mide 240px; el ancho restante del editor contiene dos columnas de permisos. |
| UI-AC-36 | 360px+ | ambos temas | Los radios de los paneles y diálogos son de 32px, los del aviso y los mensajes de 24px, los de los campos de 18px y los de las casillas de 8px; las acciones tienen forma de píldora. |
| UI-AC-37 | 1101px+ | cuentas normales | El relleno del panel es de 28px y el relleno vertical de los registros es de 24px. |
| UI-AC-38 | 360px+ | ambos temas | El cuerpo usa Geist incrustada; los colores semánticos coinciden con el mapeo de producción y los bordes de entrada usan texto-tenue. |
| UI-AC-39 | 360px+ | ES/EN, diálogo | El idioma de inspección inicial es ES; EN traduce las etiquetas; el nombre accesible del botón para cerrar el diálogo en ES es Cerrar. |
| UI-AC-40 | 360–760px | vistas de formulario | El panel se contrae con 20px de relleno y todas las acciones esenciales siguen siendo accesibles sin desplazamiento horizontal. |
| UI-AC-41 | 360px+ | selector de rol para invitación/cuenta, ES/EN | Aparecen los cuatro nombres de planes del catálogo en el orden de los planes, seguidos de Empleado interno, Administrador y los roles personalizados; EN usa Enthusiast. |
| UI-AC-42 | 360px+ | rol del sistema seleccionado | Entusiasta y Designer muestran los mismos permisos; los costos aparecen por primera vez en Designer Plus, y Taller y el explorador aparecen por primera vez en Master Designer; los roles del personal incluyen todos los permisos de los planes. |
| UI-AC-43 | 360px+ | cuentas/roles, ES/EN | No se muestra ninguna etiqueta Plan 1/2/3, límite numérico inventado para el chat, acción de pago ni campo adicional de plan acumulativo. |
| UI-AC-44 | 360px+ | activación / aviso obligatorio, ES/EN | El aviso comienza con Sempertex, sin un marcador de posición para el nombre legal; el correo electrónico de contacto y la URL de la política conservan sus marcadores de posición entre corchetes específicos del idioma. |

### Verificación de finalización — artefacto canónico actual

SHA-256 del HTML: `a882555eccb6b8c2e53c73afa08a0f6adf1e96c1e3986c4a79a22812841455d9`. Los artefactos TSX y de exploración seleccionados siguen sin cambios. El HTML reconstruido coincide con el HTML r14 seleccionado después de normalizar únicamente el `<title>` del documento de salida; la composición, el texto, el runtime, los estilos y las animaciones integrados son idénticos en todos los demás aspectos. No se necesitó ningún parche adicional de artefactos por defectos de comportamiento verificados.

- `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components status` → instalado/compilado, **96/96 entradas OK**.
- `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/cuentas-admin@v1.r14.dir-a.tsx --out <design>/cuentas-admin@v1.html` → **679 KB, 2150 archivos fuente, sin conexión**, código de salida 0. Se usó el generador instalado ACTUAL; no hubo fallback, descargas ni cambios en la exploración.
- `python3 <kit>/kit/contrast.py <design>/cuentas-admin@v1.html` → **contraste: 158 pares comprobados en modos claro y oscuro; todos pasan**, código de salida 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/cuentas-admin@v1.html --max-combos 476` → **476 renderizados (476 combinaciones planificadas), 12,454 mediciones de texto, 1,436 paradas de foco**, código de salida 0. Cubre todas las vistas, estados y temas, así como cada escena de diálogo declarada en 1280/390px sin muestreo, además de sus pruebas de movimiento y movimiento reducido. No se informaron advertencias.

**RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, espaciado interno ni desbordamiento**

Aquí `<design>` es el directorio `design` de este requisito y `<kit>` es `/home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit`.

Ejecución complementaria de Playwright/Chromium en caché: **216 aserciones PASS**, código de salida 0. Las siete vistas normales se comprobaron en **360/390/768/1280px × claro/oscuro × ES/EN** (112 casos de reflujo); los formularios de escritorio/tableta se comprobaron para el límite centrado de 676px; se comprobó la activación/aceptación renovada para Sempertex, los marcadores de posición localizados restantes y el envío deshabilitado sin consentimiento. Se observaron **cero excepciones de página y cero solicitudes HTTP(S)**. Esto verifica la solicitud inicial de consentimiento, no el flujo completo del servicio de activación. El primer contenido de captura PNG superó el límite de salida de la terminal; el resultado correcto del comando y las estadísticas resumidas quedaron visibles, pero las imágenes truncadas no se contabilizaron como inspección visual. Luego se repitieron las cuatro capturas como JPEG comprimidos en memoria y se inspeccionaron; no se volvió a ejecutar la suite de aserciones.

Se inspeccionaron visualmente capturas de página completa, sin escribir artefactos adicionales: **activación en 1280/claro ES, cuentas en 1280/oscuro ES, activación en 390/claro ES y aviso obligatorio en 390/oscuro EN**. El registro conserva sus filas alineadas; el formulario permanece centrado en escritorio; en móvil, el aviso, la identidad, el consentimiento y las acciones se apilan y siguen siendo legibles sin que se recorten controles esenciales. La comparación del código fuente conserva el registro cinético seleccionado en lugar de sustituirlo por una nueva gramática de movimiento.

Estas son comprobaciones recientes del HTML canónico, no resultados de exploración copiados. Las comprobaciones estáticas y las capturas no demuestran la autenticación de producción, la aplicación de permisos en el servidor, el estado persistente, la preparación legal ni la conformidad completa con WCAG. No se ejecutaron lint, tipos, pruebas ni compilación de producción, ni se comprobaron servicios en vivo: esta delegación solo modifica artefactos de planificación. T2.6/T2.7/T2.8 aún deben aportar evidencia independiente de implementación y la aprobación sigue pendiente.


## 12. Preguntas abiertas y supuestos

**Preguntas abiertas para el propietario: ninguna surgida de esta finalización.** El propietario seleccionó la dirección A de r14 y ya resolvió la pregunta sobre el nombre de la empresa: usar **Sempertex**, conservar `[CORREO PARA DERECHOS]` / `[RIGHTS CONTACT EMAIL]` y `[URL DE LA POLÍTICA]` / `[POLICY URL]`. Estos campos aplazados deliberadamente y su anotación de revisión legal se mantienen; no se afirma que haya un enlace funcional a la política, una dirección de contacto ni preparación legal.

**Decisiones confirmadas:** composición de registro/formulario seleccionada, navegación horizontal, eje centrado del formulario y registro cinético; paleta de producción/Geist; un rol por cuenta; cuatro planes de catálogo y seis roles de sistema de solo lectura; doce permisos disponibles con cantidades de sistema 3/3/4/6/9/12; las capacidades de Taller siguen como texto bajo un único permiso; el explorador solo está disponible para Master Designer/personal; Entusiasta en inglés = Enthusiast. Los roles personalizados requieren al menos un permiso. Las invitaciones duran siete días y los restablecimientos 24 horas; ambos son de un solo uso; los enlaces nuevos sin usar del mismo tipo invalidan los anteriores. La activación inicia sesión inmediatamente. El inicio de sesión usa el aviso genérico de quince minutos. Las nuevas versiones del aviso requieren un consentimiento nuevo. El trabajo guardado y el último administrador activo impiden la eliminación. El cambio de la contraseña propia renueva la sesión de este navegador y cierra las demás sesiones; el restablecimiento por parte de un administrador devuelve al inicio de sesión. Los límites numéricos del chat se aplazan y no se muestran ni aplican aquí.

**Supuestos del artefacto:** todas las identidades, marcas de tiempo, tokens, cantidades de asignaciones de roles y operaciones son claramente simulados. El fixture estático de administrador no autoriza el acceso; los datos del servicio y los criterios de elegibilidad deben sustituir las posiciones del fixture. En producción, inicialmente se usa el idioma del navegador (los idiomas distintos de ES/EN recurren a ES); luego, la preferencia de la cuenta sigue los subplanes de idioma; el inspector de planificación seleccionado inicia en ES y permite elegir EN. La inspección del estado/vista puede restablecer las entradas locales de la maqueta y no es persistencia. El componente compartido de avisos de la fuente mantiene idéntico el texto de activación y de aceptación renovada. Las reglas de siete días para invitaciones y 24 horas para restablecimientos son requisitos, aunque la maqueta solo las ilustre en el texto contextual.

**INQUIETUDES:** la aprobación sigue pendiente. El contacto para derechos y la política aplazados, así como la revisión legal de Sempertex, siguen registrados en SPEC/comentarios del propietario. La autenticación, la autorización, las rutas reales, la duración de tokens/sesiones, la validación de límite superior/contraseña actual, los permisos/contadores duraderos e independientes de roles personalizados, la recuperación ante estados pendientes/errores, las protecciones autoritativas para último administrador/trabajo guardado, la entrega mediante portapapeles y el almacenamiento versionado del consentimiento requieren implementación y verificación independiente; esta maqueta estática no los demuestra. El foco y los anuncios para lectores de pantalla de diálogos/rutas/campos no válidos, el zoom/reflujo, la compatibilidad entre navegadores y los fallos de servidores reales siguen siendo objetivos de implementación. Los enlaces a los planes de inicio de sesión/menú de cuenta de SP-14 deben integrarse con este contrato; no se agregan silenciosamente a la exploración seleccionada e inmutable. Algunos archivos HTML de tareas relacionadas usan fuentes/paletas exploratorias más antiguas; se conserva la asignación de tokens de producción seleccionada. Auditoría real de finalización: **RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, espaciado interno ni desbordamiento** (476/476 renderizados, código de salida 0); el contraste también pasa en los 158 pares. La sección 11 registra los comandos y límites de verificación; los resultados de exploración anteriores no se reutilizan como evidencia reciente.

Solo se escriben los dos artefactos de diseño canónicos asignados y el RESULT obligatorio de la delegación. No se modifica la exploración, el historial, la traducción, SPEC, PLAN, el registro de cambios, ningún archivo de producción, la vista previa opcional del repositorio, el registro del proyecto ni ningún archivo de memoria.
