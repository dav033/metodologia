---
name: Parte de acceso
contract: cuentas-admin
version: 1
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
revision: r14.dir-a
subplan: SP-2
requirements: [R1, R3, R16, R17]
owner: David
author: Designer
date: 2026-10-27
source_revision: r13.dir-a + canonical amend-1
feedback: "2026-10-27T14:17 direction=a: company is Sempertex; other legal information remains placeholder"
---

# Parte de acceso — direction A

## 1. Identidad y trazabilidad

**Borrador; no aprobado para implementación.** Revisión 14 de la dirección A “Parte de acceso”, basada en una copia de r13 A. Esta es la iteración solicitada de una sola dirección, no una finalización canónica ni una nueva dirección. El propietario la aprueba junto con el plan; Designer no concede aprobación. Los archivos canónicos, las revisiones anteriores, los contratos paralelos, el plan y los repositorios del proyecto permanecen inmutables en esta delegación.

Alcance: `cuentas-admin@v1.r14.behavior.md` actual, SP-2, R1/R3/R16/R17. SPEC.md y PLAN.md/PLAN.json solo aportan contexto. Los comentarios del propietario del 2026-10-27T14:17 direction=a resuelven la pregunta sobre el nombre legal: el aviso menciona **Sempertex** en ES y EN; el correo del contacto de derechos y la URL de la política conservan sus marcadores existentes entre corchetes. No se cambia ningún otro texto del aviso. Tanto la activación como la reaceptación obligatoria comparten el mismo componente del aviso. No se inventa ningún sufijo legal, dirección de contacto, URL ni aprobación legal.

Se conserva la enmienda canónica posterior 1: cuatro planes respaldados por el catálogo, seis roles del sistema de solo lectura, un permiso general de Taller (doce concesiones en total), explorador exclusivo de Master Designer, Enthusiast traducido, datos de prueba neutrales enmendados, orden correcto del selector de roles y renovación de sesión con contraseña propia. Primero se copia el TSX de r13 y luego se le aplican esos deltas existentes de la enmienda; el HTML canónico y el HTML de la enmienda 1 son idénticos byte por byte al inspeccionarlos. El CSS seleccionado, la estructura, la navegación, la tipografía, la densidad y el registro cinético permanecen idénticos byte por byte a r13. Solo cambian los dos marcadores del nombre legal del aviso y la etiqueta de revisión del inspector con respecto a la fuente de la enmienda canónica.

Instantáneas de solo lectura de las fuentes:

| Entrada | SHA-256 |
|---|---|
| `cuentas-admin@v1.r13.dir-a.tsx` | `7ad4f5526859611950de1595e7d71ee1fcf37c86a7d899e0cf0082eb030fd238` |
| `cuentas-admin@v1.r13.dir-a.html` | `6fbc92b149739f55e4e467be53ec85385bd150a2524b35ea8ec8feb5e4895931` |
| `cuentas-admin@v1.r13.dir-a.md` | `f23f547ea82e861a064fcad7eb10b7c417dd5797c36a6df22524a36234df39f2` |
| `cuentas-admin@v1.r13.dir-a.json` | `9feebf978acfa8c0a06286047d0e8acb01bff77de9ffb58bd1926e865e2a0bf5` |
| `cuentas-admin@v1.r14.behavior.md` | `76936ca02335918683373873e8e28c321f95ccf020761795865ffbbf3b7f5302` |
| `cuentas-admin@v1.md` | `465f35b2da29f91f4b024ef82d1b6fa71c9a60824462b97ee5ca55dfc370b1b5` |
| `cuentas-admin@v1.html` | `e78373c1b2143abb364cb1d046ef027f191cbe1f4621500568a0169903232953` |

Solo SP-2 declara `ui.contract=cuentas-admin`, versión 1: T2.1 de copia de diseño y T2.7 de revisión visual. Los consumidores de UI son T2.3 (acceso, activación, restablecimiento, aviso), T2.4 (menú compartido de cuenta/Mi cuenta) y T2.5 (cuentas/invitaciones/roles). SP-1 proporciona account-service@1, session-guard@1, permission-map@1 y plan-catalogue@1. El catálogo es responsable de los nombres, el orden, los precios, la disponibilidad y los permisos de los planes. SP-14 es responsable de la información pública de los planes y sus enlaces; aquí no se agrega ninguna vista nueva de planes públicos ni un flujo de pago.

Registro integrado de versiones e impacto, 2026-10-27: **r13 → r14 implica un cambio incompatible en el contenido y el comportamiento de permisos porque incorpora la enmienda canónica del plan ya registrada; la composición sigue siendo compatible. La enmienda canónica → r14 es una aclaración compatible del texto del aviso.** T2.3 debe mostrar Sempertex en ambas vistas que incluyen el aviso y preservar el consentimiento y la recuperación; T2.4/T2.5 mantienen las expectativas enmendadas de sesión y roles. T2.7 vuelve a renderizar los estados afectados en ambos idiomas y temas, en teléfono/tableta/escritorio. T2.1 espera la aprobación independiente de la instantánea seleccionada exacta. No se redirige a ningún otro consumidor; las escrituras independientes del registro de cambios y del plan quedan fuera del alcance.

## 2. Propósito y usuarios

El administrador responde a “¿Quién tiene acceso, cuál es su rol y qué necesita cambiar?”. El registro completo con líneas separadoras mantiene juntos la identidad, el rol, el estado y la acción de gestión de cada persona. Las personas invitadas establecen una contraseña personal, aceptan el aviso y llegan a una herramienta permitida. Las personas con sesión iniciada se identifican, cambian su propia contraseña y cierran sesión.

La administración de cuentas requiere `cuentas.administrar`; la administración de roles requiere de forma independiente `roles.administrar`. Los nombres de rol o `internas.usar` nunca sustituyen estos permisos. El éxito significa un cambio confirmado por el servidor y un siguiente paso explícito. Los usuarios sin permiso ven un rechazo acotado sin datos restringidos.

El HTML etiqueta los datos como simulados y las operaciones como simuladas. Los datos de prueba de cuentas neutrales `@prueba.local` corresponden al vocabulario de pruebas del SPEC, no a identidades reales. Mi cuenta y el menú de cuenta identifican ambos a Cuenta administradora / admin@prueba.local; la activación identifica a Cuenta Master Designer / master@prueba.local. Los enlaces reservados de pictures.example nunca emiten acceso real. Los conteos derivan de las mismas filas de datos de prueba; los valores de último acceso y las fechas de aviso de ejemplo son ilustrativos.

## 3. Arquitectura de información y jerarquía

Conservar r13: cabecera compacta Pictures/Sempertex con anillo y punto, con controles de idioma/cuenta → encabezado de tarea de 24 px → navegación horizontal neutra Cuentas / Roles y permisos / Mi cuenta en las superficies permitidas con sesión iniciada → un único papel de trabajo → pie de página alineado. No hay contador de edición, riel de planes, eslogan, muestra de material ni tarjeta promocional secundaria.

Cuentas ocupa el ancho disponible del registro: Cuentas del piloto / Datos de ejemplo e Invitar persona → filtros de búsqueda/rol/estado → registros con líneas separadoras → conteo de resultados derivado y leyenda en hora de Bogotá. En escritorio, los filtros comparten columnas flexibles 2:1:1. Cada fila mantiene juntos nombre/correo/empresa, rol asignado, estado, último acceso y Gestionar.

Roles conserva la composición lista de roles/editor: encabezado/Crear rol → seis roles de sistema de solo lectura y ejemplos personalizados → título y explicación del rol seleccionado → nombre del rol personalizado cuando es editable → cuatro fieldsets de herramientas → guardar/eliminar y retroalimentación. La lista en escritorio mide 240 px de ancho; el editor ocupa el espacio restante. Las subcapacidades de Taller son texto explicativo bajo el único permiso de Taller.

Inicio de sesión, activación, restablecimiento, Mi cuenta y aviso obligatorio usan un espacio de trabajo centrado de hasta 676 px, con un eje de formulario de 620 px, con encabezado/retroalimentación coincidentes y pie de página apilado. La activación coloca la identidad del invitado antes de las contraseñas, el aviso completo antes del consentimiento sin marcar, y el consentimiento antes del envío. El aviso obligatorio retiene las demás rutas del producto hasta su aceptación. Los diálogos contextuales mantienen la invitación, la gestión de la cuenta seleccionada, el comprobante de un solo uso y la confirmación permanente junto al flujo de trabajo que los origina.

## 4. Sistema de diseño y lenguaje visual

### Nota de dirección de ocho ejes

| Eje | Expresión actual |
|---|---|
| Concepto | Un registro operativo de acceso: cuentas invitadas, rol asignado, estado de acceso y siguiente acción de gestión. Sin paneles de marketing ni promoción de planes. |
| Diseño | Encabezado compacto de Pictures/Sempertex, título de página sobrio de 24px y regla horizontal de navegación conservada. Las cuentas ocupan todo el ancho del registro con filtros equilibrados de búsqueda/rol/estado en proporción 2:1:1; los roles usan un selector de 240px junto a la hoja de permisos. Acceso, activación, restablecimiento, aviso y Mi cuenta usan un panel centrado de 676px y un eje compartido de formulario/retroalimentación de 620px, lo que elimina la mitad derecha vacía. |
| Navegación | Se conserva la navegación horizontal neutral Cuentas / Roles y permisos / Mi cuenta, los diálogos contextuales de cuenta y el desplegable con nombre de cuenta. El acceso solo por invitación no tiene una ruta de registro. Los selectores de planificación permanecen fuera de la estructura del producto. |
| Tipografía | Geist Sans y Geist Mono de producción, integradas desde la compilación local existente. Título de página de 24px, títulos de sección de 20px, cuerpo de 14–16px y metadatos de 11–13px; sin tipografía de exhibición ni sección principal destacada. ES es el idioma inicial; EN aparece mediante el selector de idioma. |
| Densidad | Se conservan el relleno de 24px en las filas de cuenta, márgenes de papel de 28px en escritorio / 20px en teléfono, paneles de 32px, superficies interiores de 24px, campos de 18px, casillas de 8px y controles/chips de estado tipo píldora. Los paneles de formulario ajustados al contenido tienen márgenes exteriores iguales; las vistas de gestión anchas conservan el espacio de trabajo disponible y filtros flexibles. |
| Componentes | Button, Input, Checkbox, Skeleton, Dialog y AlertDialog de shadcn/Base UI instalados, compuestos como filas de cuenta y grupos de campos de permisos. Marca de anillo y punto de producción; paneles redondeados, estados semánticos tipo píldora y navegación neutral. El texto para cerrar el diálogo sigue ES/EN. Los seis roles del sistema de catálogo/personal siguen siendo de solo lectura; cuatro planes acumulativos usan etiquetas del catálogo. Ambos idiomas del aviso mencionan Sempertex y conservan los marcadores de contacto de derechos y de política. |
| Color | Paleta exacta de Pictures globals.css, asignada como en proyectos@v1: modo claro #faf9fc / #ffffff con acciones #6d3fe0; modo oscuro #0b0c10 / #16181f con acciones #9479ff y primer plano #120b24. Tokens existentes de éxito/advertencia/error; los bordes de entrada usan el alias texto-tenue. Sin paleta exploratoria. |
| Movimiento | Se conserva el registro cinético: cubic-bezier(.76,0,.24,1), registro de papel/filas/regla/estado de 480ms, desfases de fila de 55ms y controles de 180ms; natural de 300/140ms y sutil de 160/100ms. Se mantienen el barrido del esqueleto y el desplazamiento de la flecha al pasar el cursor o presionar; se elimina el movimiento retirado de riel/laminado. El movimiento reducido/quieto lo desactiva y las pestañas ocultas pausan la animación. |

Fuentes de producción inspeccionadas en modo de solo lectura: t12 y asesor `src/app/globals.css`, configuración de layout/fuentes, formulario de inicio de sesión, AdminTabs y CabeceraApp; contratos hermanos planes@v1, proyectos@v1 y taller-esenciales@v1. Se aplican los tokens/fuentes del producto y las asignaciones escritas de los proyectos hermanos. Algunos HTML agrupados de proyectos hermanos conservan estilos exploratorios anteriores; esa discrepancia no se importa. Se conservan la navegación horizontal, los formularios amplios y redondeados y el registro cinético seleccionados por el propietario en r13. No se introduce ninguna paleta ni familia tipográfica nueva.

La asignación de roles del proyecto se basa en globals.css de ambos repositorios y en los roles compartidos correspondientes de proyectos@v1. Todos los valores que aparecen a continuación ya existen en el producto; no se introduce ningún color nuevo.

| Fuente de Pictures | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, primer plano primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | primario al pasar el cursor, anillo | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | borde decorativo, regla | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | entrada (alias de control accesible existente en proyecto hermano) | #766c85 / #8a91a0 |
| `--superficie-suave` | superficie suave para rol seleccionado | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | éxito, éxito suave | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | advertencia, advertencia suave | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45, #ffeaec / #ff979f, #43252a |
| Primer plano destructivo existente | primer plano destructivo | #ffffff / #3a0f13 |
| `--fondo` | información suave, primario suave | #faf9fc / #0b0c10 |

La tipografía es la Geist Sans / Geist Mono real de producción, integrada sin conexión desde los recursos WOFF2 Latin locales de la compilación Next existente de t12. No se obtiene ninguna fuente ni recurso. H1 mide 24px/1.25 en todos los anchos; los títulos de sección, 20px/1.3 en escritorio; el cuerpo, 14–16px, y los metadatos, 11–13px; la tipografía mono se limita a identificadores/metadatos. Se conservan de r11 el tamaño de sección en teléfono y las formas amplias. Se mantienen los roles de forma de r11: `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. Estas son las elecciones de forma del borrador que conserva el propietario, no nuevas elecciones de paleta o tipografía de producción. El relleno de papel y diálogo se mantiene en 28px en escritorio, 20px para el papel en teléfono / 24px para los diálogos en teléfono; las filas se mantienen en 24px en escritorio / 20px en teléfono.

Los componentes se nombran **fuente:id variante estado**; todas las rutas corresponden a componentes realmente instalados, no a fragmentos HTML:

| Nombre | Importación / composición |
|---|---|
| `shadcn:button default default\|hover\|focus\|pressed\|disabled\|loading` | `@/components/ui/button`, composición Action seleccionada; envío/invitación/copia principales |
| `shadcn:button outline default\|hover\|focus\|pressed\|disabled` | La misma importación; gestión, recuperación, cancelación/navegación |
| `shadcn:button destructive default\|hover\|focus\|disabled\|loading` | La misma importación; confirmación explícita de eliminación permanente |
| `shadcn:input text\|email\|password default\|focus\|invalid\|disabled` | `@/components/ui/input`; Field personalizado asocia etiqueta, control y ayuda, no es el Field estándar de shadcn |
| `shadcn:checkbox permission\|consent unchecked\|checked\|focus\|disabled` | `@/components/ui/checkbox`, mejora instalada de Animate UI/Base UI |
| `shadcn:skeleton record\|form loading` | `@/components/ui/skeleton` |
| `shadcn:dialog invitation\|management\|link open\|closed` | `@/components/ui/dialog`, mejora instalada de Animate UI/Base UI |
| `shadcn:alert-dialog account-delete\|role-delete open\|blocked\|pending\|closed` | `@/components/ui/alert-dialog`, mejora instalada de Animate UI/Base UI |
| `native:select role\|status\|language default\|focus\|disabled` | Select nativo de HTML con etiqueta; no se afirma que sea Select de shadcn |
| `native:details account closed\|open` | Desplegable con nombre de cuenta, Mi cuenta/cerrar sesión; no modal |
| `custom:access-register ruled normal\|loading\|empty\|error` | `.register-head`, `.person-row`, `.identity`, `.footline` |
| `custom:permission-sheet grouped system-readonly\|custom-editable\|validation` | `.role-layout`, `.role-list`, `.role-editor`, fieldset/legend |
| `custom:app-header compact normal` | `.masthead`, `.heading`, `.route-nav`; marca de anillo y punto de Pictures |
| `custom:message ruled error\|success` | `.message` con semántica de alerta/estado |

`mountMockup` / `useMockup` se importan de `@kit/mockup`; `useMotionProfile`, de `@kit/motion`. El espacio de trabajo real sin conexión agrupa React, controles, fuentes y movimiento. No se usaron CDN, instalación de paquetes, solicitudes externas de imágenes/fuentes ni alternativa de HTML simple.


**Movimiento: registro cinético, sin cambios desde r13.** `useMotionProfile()` proporciona el perfil/estado reducido. Cubic-bezier(.76,0,.24,1); papel/filas/regla/estado expresivos de 480ms con desfases de fila de 55ms, controles de 180ms; natural de 300/140ms; sutil de 160/100ms. El papel se desplaza verticalmente 12px, las filas horizontalmente 14px y las reglas/estados 6px. Los botones se elevan −2px al pasar el cursor, se presionan 1px con scale(.98) y las flechas se desplazan 3px. El barrido del esqueleto se repite cada 1.4s. No se reincorpora el movimiento retirado de riel/laminado. El texto legible permanece presente. Las pestañas ocultas pausan la animación; no queda ninguna animación decorativa fuera de pantalla. El movimiento reducido del SO, Quieto y `?still=1` suprimen el movimiento y los efectos repetidos, conservan la disposición final y mantienen todas las acciones.

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

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 1101px+ | cuentas normal | El título de tarea de 24px aparece sobre un registro de cuentas reglado que ocupa todo el ancho; no hay celda de edición, riel ni tarjeta de material. |
| UI-AC-02 | 1101px+ | cuentas normal | Cada registro agrupa visiblemente nombre, correo electrónico, empresa, rol, estado, último acceso y Administrar. |
| UI-AC-03 | 360–760px | cuentas normal | La identidad ocupa todo el ancho de su registro; el rol/estado y Administrar se reorganizan debajo sin desbordar la página. |
| UI-AC-04 | 761–1100px | cuentas normal | La búsqueda ocupa ambas columnas de filtros y Administrar sigue a los demás campos de la fila. |
| UI-AC-05 | 360px+ | cuentas filtradas/vacías | El recuento de resultados coincide con los registros mostrados; borrar los filtros restaura el registro sin filtrar. |
| UI-AC-06 | 360px+ | cargando | Los esqueletos reemplazan el contenido sin resolver y no se puede repetir un envío pendiente. |
| UI-AC-07 | 360px+ | error de cuentas/roles | Las filas sin confirmar no aparecen y Reintentar está visible. |
| UI-AC-08 | 360px+ | error de inicio de sesión | La misma negativa y la indicación de espera de quince minutos aparecen para las cuatro causas de rechazo de credenciales. |
| UI-AC-09 | 360px+ | activación normal | Dos controles de contraseña y el aviso completo preceden al consentimiento desmarcado y a Activar deshabilitado. |
| UI-AC-10 | 360px+ | activación marcada | Marcar el consentimiento habilita una activación válida y el mensaje de éxito explica que la sesión iniciada está activa. |
| UI-AC-11 | 360px+ | invitación/restablecimiento no válidos | La entrada de contraseña se reemplaza por la recuperación mediante un enlace emitido por el administrador, sin revelar la causa específica. |
| UI-AC-12 | 360px+ | invitación | Nombre/correo electrónico/empresa opcional/un rol preceden a la generación; el correo electrónico duplicado produce una negativa. |
| UI-AC-13 | 360px+ | comprobante de un solo uso | El destinatario, el enlace seleccionable con ajuste de línea, Copiar, el uso único/la vigencia y la advertencia de reemplazo están visibles. |
| UI-AC-14 | 360px+ | comprobante cerrado | El comprobante cerrado no puede recuperar su enlace anterior; la recuperación consiste en generarlo de nuevo. |
| UI-AC-15 | 360px+ | rol del sistema | Exactamente seis roles del sistema son de solo lectura y tienen 3/3/4/6/9/12 permisos seleccionados en el orden del catálogo/personal. |
| UI-AC-16 | 360px+ | rol personalizado | Cuatro grupos de herramientas contienen doce permisos disponibles; Taller es una casilla con texto de ayuda sobre las capacidades agrupadas. |
| UI-AC-17 | 360px+ | validación de rol | Guardar un rol personalizado con nombre y sin permisos anuncia ROL_SIN_PERMISOS y conserva la edición. |
| UI-AC-18 | 360px+ | rol en uso | La eliminación permanente está deshabilitada y se ve la explicación de que primero se debe reasignar. |
| UI-AC-19 | 360px+ | trabajo guardado/último administrador | La negativa explica su invariante y la confirmación de eliminación permanente está deshabilitada. |
| UI-AC-20 | 360px+ | eliminación de cuenta sin trabajo | La eliminación permanente está deshabilitada hasta que el correo electrónico escrito coincida exactamente con el de la cuenta seleccionada. |
| UI-AC-21 | 360px+ | cuenta propia | La identidad coincide con la información de la cuenta y la contraseña actual precede al par de contraseñas nuevas. |
| UI-AC-22 | 360px+ | éxito al cambiar contraseña propia | El mensaje indica que se renovó la sesión de este navegador y que las sesiones anteriores finalizaron; no aparece el requisito de iniciar sesión por segunda vez. |
| UI-AC-23 | 360px+ | éxito al restablecer | El mensaje pide a la persona que inicie sesión con la nueva contraseña. |
| UI-AC-24 | 360px+ | aviso obligatorio | El aviso completo y versionado, el consentimiento desmarcado y cerrar sesión están presentes mientras la navegación del resto del producto está ausente. |
| UI-AC-25 | 360px+ | rol de cuenta cambiado | El rol único seleccionado se actualiza con un texto que explica la aplicación en la siguiente solicitud; las etiquetas de plan siguen siendo acumulativas. |
| UI-AC-26 | 360px+ | claro/oscuro | Los bordes de los campos, los estados de las casillas, las acciones de contorno y el foco son visibles sobre sus superficies reales. |
| UI-AC-27 | 360px+ | expresivo | Los registros en papel se despliegan verticalmente, los registros horizontalmente y las reglas/el estado mediante trazos cortos, con el suavizado/tiempos de r13 y texto legible. |
| UI-AC-28 | 360px+ | movimiento reducido/inmóvil | No queda movimiento en curso ni diálogo desplazado; se pueden usar los mismos controles y contenidos. |
| UI-AC-29 | 360px+ | invitación abierta/cerrada | El foco del teclado permanece dentro del diálogo; al cerrarlo, el foco vuelve a la acción que lo inició. |
| UI-AC-30 | 360px+ | ES/EN | Los encabezados, las etiquetas, los avisos y las acciones del diálogo se reorganizan sin desplazamiento horizontal de la página. |
| UI-AC-31 | 360–760px | roles normal | El selector de roles se apila antes del editor de permisos, con su divisor horizontal. |
| UI-AC-32 | 761px+ | inicio de sesión/activación/restablecimiento/Mi cuenta/aviso | El espacio de trabajo del formulario mide como máximo 676px y queda centrado con márgenes exteriores iguales; los campos se mantienen dentro de un eje de 620px. |
| UI-AC-33 | 761px+ | error/éxito del formulario/enlace no válido | El encabezado, los mensajes, la recuperación y el pie apilado siguen el eje del formulario centrado. |
| UI-AC-34 | 1101px+ | cuentas normal | Los filtros de búsqueda/rol/estado ocupan columnas flexibles en proporción 2:1:1 a lo ancho del registro. |
| UI-AC-35 | 1101px+ | roles normal | El selector de roles mide 240px; el ancho restante del editor contiene dos columnas de permisos. |
| UI-AC-36 | 360px+ | ambos temas | Los radios de las esquinas del papel/diálogo son de 32px, los del aviso/mensaje de 24px, los de los campos de 18px y los de las casillas de 8px, con acciones en forma de píldora. |
| UI-AC-37 | 1101px+ | cuentas normal | El relleno del papel es de 28px y el relleno vertical de los registros es de 24px. |
| UI-AC-38 | 360px+ | ambos temas | El cuerpo usa Geist integrado; los colores semánticos coinciden con la asignación de producción y los bordes de entrada usan texto-tenue. |
| UI-AC-39 | 360px+ | ES/EN, diálogo | El idioma inicial de inspección es ES; EN traduce las etiquetas; el nombre accesible del cierre del diálogo en ES es Cerrar. |
| UI-AC-40 | 360–760px | vistas de formulario | El panel se contrae con 20px de relleno de papel y todas las acciones esenciales siguen disponibles sin desplazamiento horizontal. |
| UI-AC-41 | 360px+ | selector de rol de invitación/cuenta, ES/EN | Aparecen los cuatro nombres de planes del catálogo en orden de plan, seguidos por Empleado interno, Administrador y los roles personalizados; EN usa Enthusiast. |
| UI-AC-42 | 360px+ | rol del sistema seleccionado | Entusiasta y Designer muestran las mismas autorizaciones; los costos se verifican por primera vez en Designer Plus, Taller y explorador se verifican por primera vez en Master Designer; los roles de personal incluyen todas las autorizaciones de los planes. |
| UI-AC-43 | 360px+ | cuentas/roles, ES/EN | No se muestran etiquetas Plan 1/2/3, límites numéricos inventados para el chat, acciones de pago ni campos de plan aditivos adicionales. |
| UI-AC-44 | 360px+ | activación / aviso obligatorio, ES/EN | El aviso comienza con Sempertex, sin marcador de posición de razón social; el correo electrónico de contacto y la URL de la política conservan sus marcadores de posición entre corchetes específicos del idioma.

Verificación final de r14, SHA-256 del HTML `312dfaadd4b07c6fc38a803d35a14b79e25925079266f724b2285e77d3a370fd`:

- Generador sin conexión actual: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/cuentas-admin@v1.r14.dir-a.tsx --out <design>/cuentas-admin@v1.r14.dir-a.html` → **679 KB, 2150 archivos fuente, sin conexión**, código de salida 0. Componentes reales instalados y fuentes locales de producción integradas; sin instalación, recursos de red, fragmentos alternativos ni modificaciones al HTML generado.
- `python3 <kit>/kit/contrast.py <design>/cuentas-admin@v1.r14.dir-a.html` → **contraste: 158 pares comprobados en temas claro y oscuro; todos aprobados**, código de salida 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/cuentas-admin@v1.r14.dir-a.html --max-combos 476` → **476 renderizados (476 combinaciones previstas), 12,454 mediciones de texto, 1,407 paradas de foco**, código de salida 0, con Chromium del sistema seleccionado por el kit actual. Se comprobaron todas las combinaciones de vista/estado/tema y cada escena de diálogo a 1280/390px; sin muestreo.

`RESULT: PASS — no se detectaron problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento`

Comprobaciones complementarias con Playwright en caché: **438 aserciones APROBADAS**, incluidas **112 pruebas responsivas** (siete vistas × dos temas × ES/EN × 360/768/1024/1440px). Las dos vistas con aviso mencionan Sempertex y conservan los dos marcadores de posición restantes en cada idioma/tema en todos los anchos medidos. Se aprobaron el centrado del formulario/límite de 676px, Geist de producción, ausencia de desbordamiento horizontal, los **18 selectores de evidencia JSON**, los recuentos de permisos de seis roles del sistema de solo lectura (3/3/4/6/9/12), el orden de roles de invitación, la habilitación por consentimiento, la recuperación de enlaces no válidos y el mensaje de renovación de sesión al cambiar la contraseña propia. La carga expresiva mostró **nueve animaciones en curso**; el movimiento reducido del sistema operativo, Quieto y `?still=1` mostraron **cero**. El diálogo de invitación inicializado con movimiento reducido permaneció visible con opacidad 1. No ocurrieron excepciones de página ni solicitudes HTTP(S).

Se inspeccionaron visualmente capturas de página completa **en memoria**, sin escribir archivos adicionales: activación en 1280/claro (ES), cuentas en 1280/oscuro (ES), activación en 390/claro (ES) y aviso obligatorio en 390/oscuro (EN). Los grupos de aviso/consentimiento/acción siguen siendo legibles y se reorganizan; el panel de formulario centrado y el registro funcional conservan la composición de la dirección A. Las comparaciones de fuente verifican que el CSS de r13 es idéntico byte por byte y que la enmienda canónica se conservó exactamente, excepto las dos sustituciones de razón social y el título de revisión del inspector. El contrato contiene los mismos textos del aviso ES/EN que TSX, doce secciones numeradas y la nota de ocho ejes; JSON conserva su estructura exacta de tres claves y ocho ejes. Los hashes de entrada de la sección 1 siguen coincidiendo después del trabajo.

Historial de pruebas: el primer script complementario seleccionó EN antes de cambiar la vista del inspector, cuyo entorno de ejecución actual vuelve a montar la vista/el estado local; su aserción de empresa falló después de que el idioma volviera a ES. La prueba corregida selecciona el idioma después de cada cambio de vista/estado y aprueba todos los casos anteriores. No fue necesario modificar el artefacto ni los umbrales de auditoría. Este es el estado de idioma del inspector; el comportamiento del idioma del navegador de producción sigue según lo especificado. La evidencia de auditoría de revisiones anteriores no se contabiliza como evidencia de r14.

Límites de verificación: estas comprobaciones miden un artefacto de diseño estático, no la autenticación de producción, el enrutamiento, los permisos del servidor, la persistencia, el manejo seguro de tokens, la entrega al portapapeles, la preparación legal ni la conformidad completa con WCAG. Aún se requieren una revisión independiente de implementación/visual y su aprobación.


## 12. Preguntas abiertas y supuestos

**Preguntas abiertas para el propietario: ninguna para esta revisión.** La respuesta del 2026-10-27T14:17 resuelve la pregunta legal anterior: usar **Sempertex** y mantener `[CORREO PARA DERECHOS]` / `[CORREO DE CONTACTO PARA DERECHOS]` y `[URL DE LA POLÍTICA]` / `[URL DE LA POLÍTICA]` como marcadores de posición. Estos campos se aplazan deliberadamente; no son decisiones de diseño pendientes. Conserva la anotación existente de revisión legal; este borrador no afirma que la revisión legal esté completa ni inventa un enlace funcional a la política. El resto del cuerpo del aviso permanece sin cambios.

**Resuelto anteriormente:** inglés Entusiasta = Entusiasta; explorador pertenece solo a Master Designer/personal; SP-1 es responsable del catálogo compartido; los valores numéricos del límite de chat siguen aplazados. Cambiar la propia contraseña cierra las sesiones anteriores y renueva la sesión de este navegador según T2.2, mientras que el restablecimiento por parte del administrador devuelve al inicio de sesión. Las doce concesiones de permisos producen recuentos acumulados del sistema de 3/3/4/6/9/12; las subcapacidades de Taller son texto complementario, no concesiones independientes.

**Confirmado:** nombre/composición/navegación/movimiento de la dirección A; paleta de producción y Geist; jerarquía del formulario centrada; un rol por cuenta; cuatro planes de catálogo y seis roles del sistema; al menos un permiso para roles personalizados; mínimo de ocho caracteres, invitaciones de siete días, restablecimientos de 24 horas; enlaces de administración de un solo uso sin correo automático; los enlaces nuevos sin usar del mismo tipo reemplazan a los anteriores; sesión de activación inmediata; aviso genérico de inicio de sesión de quince minutos; aceptación obligatoria del aviso nuevamente; protecciones para el trabajo guardado y el último administrador activo. En producción, el aviso sigue el idioma del navegador; este artefacto de planificación comienza deliberadamente en ES para facilitar la inspección y ofrece EN.

**Límites y PREOCUPACIONES:** la aprobación sigue pendiente. El propietario aplazó los marcadores de posición del contacto para derechos y de la política. Algunos HTML empaquetados de subplanes conservan paletas y tipografías anteriores que entran en conflicto con sus contratos escritos y con la fuente de producción; r14 mantiene el mapeo de producción compartido con planes@v1 y los contratos escritos de los subplanes. Los controladores locales ilustrativos no demuestran autenticación, enrutamiento, seguridad de sesión, persistencia de roles, entrega al portapapeles, caducidad de tokens, elegibilidad del trabajo guardado, recuentos de cuentas ni cumplimiento legal. Esos valores y operaciones deben provenir del servicio, no de la posición en los datos de prueba. La verificación de los estados de espera y error, el foco, el lector de pantalla y el zoom en producción sigue siendo responsabilidad de la implementación y la revisión independiente. Consulta la sección 11 para ver la evidencia renderizada real y los límites de medición restantes.

Solo se escriben los cuatro archivos de dirección r14 asignados y el RESULTADO obligatorio de delegación. No se crea ni edita ninguna vista previa opcional del repositorio, contrato compartido, plan, registro de cambios, código del repositorio, pruebas, registros ni archivo de memoria. Esta nota incorpora el registro del impacto del borrador porque las escrituras en un registro de cambios aparte quedan fuera del alcance.
