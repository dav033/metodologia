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
source_revision: r13.dir-a + amend-1
amendment: 1
baseline: cuentas-admin@v1.md (immutable)
---

# cuentas-admin@v1 — Parte de acceso

## 1. Identidad y trazabilidad

**Borrador; no aprobado para implementación.** Enmienda acotada 1 de la Parte de acceso (a) seleccionada por el propietario, r13. El contrato canónico `cuentas-admin@v1.md` y `.html` permanecen inmutables; este snapshot completo enmendado conserva el id/versión de contrato `cuentas-admin@v1` y requiere aprobación independiente del plan. T2.1 solo puede copiar al repositorio el snapshot exacto aprobado posteriormente. Esta enmienda no otorga ninguna aprobación.

Fuentes: SPEC.md y PLAN.json actuales, revisión 1 (la planificación continúa); resumen de comportamiento de la enmienda; contrato/maqueta canónicos inmutables; punto de partida TSX r13.dir-a requerido. La enmienda reemplaza los tres planes anteriores por cuatro planes respaldados por catálogo y seis roles de sistema de solo lectura, conservando la composición, la navegación, el movimiento, los tokens y cada decisión no modificada. Snapshots SHA-256 de las fuentes:

| Fuente | SHA-256 |
|---|---|
| `SPEC.md` | `777042bd633762995149f659869d70a43eb3132597c7627d286c9e3ad4094290` |
| `PLAN.json` | `a4261dcfb3ac4c6cef8cb92e5533abbb40cf6b7133873443536ba6360ba4ea49` |
| `design/cuentas-admin@v1.amend-1.behavior.md` | `76936ca02335918683373873e8e28c321f95ccf020761795865ffbbf3b7f5302` |
| `design/cuentas-admin@v1.r13.behavior.md` | `3fb1bbc78c83aae3a915983b47a7bee63aaf08c2e2a2c1bd3f976ecaa797f7f4` |
| `design/cuentas-admin@v1.md` | `52e5e8eaf0f2d7cc0da19841cbddabc2f20e50007df957c6296d95fb7bf569ba` |
| `design/cuentas-admin@v1.html` | `41de6620ad2ca6f4cdf18177cde91e72868bb70036768259912950a28045204b` |
| `design/cuentas-admin@v1.r13.dir-a.tsx` | `7ad4f5526859611950de1595e7d71ee1fcf37c86a7d899e0cf0082eb030fd238` |

Solo **SP-2** vincula `ui.contract=cuentas-admin`, versión 1, la copia de diseño **T2.1** y la revisión visual **T2.7**. Consumidores de UI: **T2.3** inicio de sesión/activación/restablecimiento/aviso obligatorio; **T2.4** menú de cuenta compartido y Mi cuenta; **T2.5** cuentas/invitaciones/roles. **T2.2** suministra las API; **T2.6** integra los flujos reales de navegador; **T2.8** audita. SP-1 suministra account-service@1, session-guard@1, permission-map@1 y plan-catalogue@1. Su catálogo es el único propietario de los nombres de los planes, el orden, los precios, la disponibilidad de herramientas y la pertenencia a permisos; SP-2 lo lee sin lógica de planes independiente. SP-14 es propietario de la sección pública de planes y de sus enlaces de entrada de inicio de sesión/menú de cuenta; agregarlos queda fuera de este resumen de enmienda. Los demás subplanes no se convierten en consumidores solo por dependencia.

| Requisito | Vistas / flujos | Aceptación |
|---|---|---|
| R1 cuentas invitadas | V1–V4, V6–V7 / F1–F5, F7–F8 | UI-AC-06–14, 19–24, 29–30 |
| R3 roles y permisos | V4–V5 / F5–F6 | UI-AC-15–19, 25, 31, 35 |
| R16 planes asignados acumulativos | V4–V5 / F2–F3, F5–F6 | UI-AC-15–16, 25, 41–42 |
| R17 catálogo de planes compartido | V4–V6 / F3, F5–F6 | UI-AC-15, 25, 41–43 |

Registro incrustado de versión/impacto (un changelog separado queda fuera del alcance asignado): **2026-10-27, enmienda 1, borrador. Compatibilidad: expectativas de contenido/permisos incompatibles respecto del borrador canónico; composición visualmente compatible.** Los selectores y el filtro de rol de invitación/cuenta de V4, la lista de roles de sistema/selección de permisos de V5 y la identidad de cuenta de V6/compartida deben consumir seis roles de sistema, no cinco. T2.5 adapta las asignaciones de plan y los permisos de solo lectura; T2.4 adapta la visualización de roles respaldada por catálogo; T2.3 muestra la nueva identidad/destino de invitado cuando corresponda. T2.1 debe copiar el snapshot aprobado de forma independiente; T2.7 debe revisar las etiquetas, el orden y los permisos enmendados en ambos temas/idiomas y en los rangos responsivos. plan-catalogue@1 y permission-map@1 de SP-1 producen los datos; ningún otro subplan de UI se convierte en consumidor solo por dependencia. El SPEC/PLAN actual resuelve el explorador como exclusivo de Master Designer y el nombre en inglés como Enthusiast. No se agrega aquí ninguna página de planes nueva, flujo de pago, UI de límites nueva ni comparación de precios.

El TSX requerido comienza como una copia de r13.dir-a inmutable. Sus dos correcciones exclusivamente canónicas se conservan en el código fuente antes de reconstruir: el cambio de contraseña propia renueva la sesión de este navegador, y Taller tiene un solo permiso con capacidades de apoyo (12 permisos disponibles). El CSS permanece idéntico byte a byte al del TSX seleccionado; el shell, la navegación, la jerarquía y el movimiento conservan la composición elegida. La enmienda se reconstruye con el constructor sin conexión actual; el HTML generado no se parchea manualmente.

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

Fuentes de producción inspeccionadas en modo de solo lectura: t12 y `src/app/globals.css` de asesor, configuración de diseño/fuentes, formulario de inicio de sesión, AdminTabs y CabeceraApp; contratos hermanos proyectos@v1 y taller-esenciales@v1. Rigen los tokens y las fuentes del producto, así como las correspondencias documentadas en los contratos hermanos. Algunos archivos HTML agrupados de contratos hermanos conservan estilos exploratorios anteriores; no se adopta esa discrepancia. Se mantienen la navegación horizontal r13 seleccionada por el propietario, los formularios redondeados y espaciosos y el registro cinético. No se introduce una paleta ni una familia tipográfica nuevas.

La correspondencia de roles del proyecto proviene de `globals.css` de ambos repositorios y de los roles compartidos correspondientes en proyectos@v1. Todos los valores siguientes ya existen en el producto; no se introduce ningún color nuevo.

| Fuente de Pictures | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, primer plano del primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover`, `--acento` | hover del primario, anillo | #5530b8, #6d3fe0 / #a58dff, #9479ff |
| `--borde`, `--borde-suave` | borde decorativo, línea | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | entrada (alias de control accesible existente del contrato hermano) | #766c85 / #8a91a0 |
| `--superficie-suave` | superficie suave del rol seleccionado | #faf8fd / #1c1e26 |
| `--exito`, `--exito-suave` | éxito, éxito suave | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | advertencia, advertencia suave | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45, #ffeaec / #ff979f, #43252a |
| Primer plano destructivo existente | primer plano destructivo | #ffffff / #3a0f13 |
| `--fondo` | informativo suave, primario suave | #faf9fc / #0b0c10 |

La tipografía corresponde a Geist Sans / Geist Mono, las fuentes reales de producción, incrustadas para uso sin conexión a partir de los recursos locales Latin WOFF2 de la compilación existente de t12 en Next. No se obtiene ninguna fuente ni recurso. H1 mide 24px/1.25 en todos los anchos; el título de sección, 20px/1.3 en escritorio; el texto de cuerpo, 14–16px; y los metadatos, 11–13px. La fuente monoespaciada se limita a identificadores/metadatos. Se conservan de r11 el tamaño de las secciones en teléfonos y las formas generosas. Los roles de forma de r11 se mantienen como `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-check:8px`, `--radius-pill:999px`. Estas son las opciones de forma conservadas del borrador del propietario, no nuevas opciones de paleta o tipografía de producción. El relleno del papel y los diálogos sigue siendo de 28px en escritorio y de 20px para el papel / 24px para los diálogos en teléfonos; las filas siguen siendo de 24px en escritorio / 20px en teléfonos.

Los componentes se nombran como **fuente:id variante estado**; todas las rutas corresponden a componentes realmente instalados, no a fragmentos de HTML:

| Nombre | Importación / composición |
|---|---|
| `shadcn:button default default\|hover\|focus\|pressed\|disabled\|loading` | `@/components/ui/button`, composición Action seleccionada; envío/invitación/copia principales |
| `shadcn:button outline default\|hover\|focus\|pressed\|disabled` | La misma importación; gestión, recuperación, cancelación/navegación |
| `shadcn:button destructive default\|hover\|focus\|disabled\|loading` | La misma importación; confirmación explícita de eliminación permanente |
| `shadcn:input text\|email\|password default\|focus\|invalid\|disabled` | `@/components/ui/input`; Field personalizado es una etiqueta asociada, un control y una indicación, no el componente Field estándar de shadcn |
| `shadcn:checkbox permission\|consent unchecked\|checked\|focus\|disabled` | `@/components/ui/checkbox`, mejora instalada de Animate UI/Base UI |
| `shadcn:skeleton record\|form loading` | `@/components/ui/skeleton` |
| `shadcn:dialog invitation\|management\|link open\|closed` | `@/components/ui/dialog`, mejora instalada de Animate UI/Base UI |
| `shadcn:alert-dialog account-delete\|role-delete open\|blocked\|pending\|closed` | `@/components/ui/alert-dialog`, mejora instalada de Animate UI/Base UI |
| `native:select role\|status\|language default\|focus\|disabled` | Select nativo de HTML con etiqueta; no se afirma que sea el Select de shadcn |
| `native:details account closed\|open` | Disclosure de cuenta con nombre, Mi cuenta y cierre de sesión; no modal |
| `custom:access-register ruled normal\|loading\|empty\|error` | `.register-head`, `.person-row`, `.identity`, `.footline` |
| `custom:permission-sheet grouped system-readonly\|custom-editable\|validation` | `.role-layout`, `.role-list`, `.role-editor`, fieldset/legend |
| `custom:app-header compact normal` | `.masthead`, `.heading`, `.route-nav`; marca de anillo y punto de Pictures |
| `custom:message ruled error\|success` | `.message` con semántica de alerta/estado |

`mountMockup` / `useMockup` se importan desde `@kit/mockup`; `useMotionProfile`, desde `@kit/motion`. El espacio de trabajo real sin conexión agrupa React, controles, fuentes y movimiento. No se usaron CDN, instalación de paquetes, solicitudes externas de imágenes/fuentes ni una alternativa de HTML simple.


**Movimiento: registro cinético, sin cambios desde r13.** `useMotionProfile()` proporciona el perfil y el estado de movimiento reducido. Cubic-bezier(.76,0,.24,1); papel/filas/líneas/estado expresivos: 480ms con desfases de 55ms entre filas; controles: 180ms; natural: 300/140ms; sutil: 160/100ms. El papel se desplaza 12px en vertical, las filas 14px en horizontal y las líneas/estados 6px. Los botones se elevan −2px al pasar el cursor y se presionan 1px con escala(.98); las flechas se desplazan 3px. El barrido del skeleton se repite cada 1.4s. No se vuelve a introducir el movimiento retirado de la barra lateral o el papel metálico. El texto legible permanece visible. Las pestañas ocultas pausan la animación; no queda ninguna animación decorativa fuera de pantalla. El movimiento reducido del sistema operativo, Quieto y `?still=1` suprimen el movimiento y los efectos repetitivos, conservan la disposición final y mantienen todas las acciones.

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

## 7. Especificaciones de las vistas

| Vista | Estructura / texto y datos | Acciones y flujo relacionado |
|---|---|---|
| V1 | “Iniciar sesión” / “Sign in”; Iniciar sesión, correo electrónico/contraseña, explicación de acceso solo por invitación, guía de restablecimiento por el administrador | Entrar; error genérico/reintento; F1 |
| V2 | “Activar cuenta” / “Activate account”; nombre/correo electrónico de la persona invitada, contraseña nueva/repetida, aviso completo, consentimiento sin marcar, explicación de siete días | Activar cuenta deshabilitado hasta otorgar el consentimiento; reemplazo por enlace inválido/Volver al acceso; F2 |
| V3 | “Restablecer contraseña” / “Reset password”; restablecer la contraseña dos veces; explicación de uso único y 24 horas | Guardar contraseña y luego iniciar sesión; reemplazo por enlace inválido; F4 |
| V4 | “Cuentas” / “Accounts”; Cuentas del piloto / Datos de ejemplo, filtros y cinco registros de cuenta completos ilustrativos, conteo de resultados/zona horaria | Invitar persona, Gestionar, borrar filtros, reintentar; F3/F5 |
| V5 | “Roles y permisos” / “Roles and permissions”; seis roles del sistema/lista de roles personalizados, nombre seleccionado, grupos de permisos y paquete explicativo de Taller | Crear rol, Guardar rol, Eliminar rol si es personalizado; estado de solo lectura del sistema; F6 |
| V6 | “Mi cuenta” / “My account”; identidad/empresa/rol actuales de la sesión iniciada, contraseña actual/nueva/repetida, versión/fecha | Cambiar contraseña; retroalimentación de renovación de sesión con sesión iniciada; divulgación de cuenta compartida; F7 |
| V7 | “Aviso de tratamiento de datos personales” / “Personal data notice”; Aviso actualizado, explicación del bloqueo, texto completo versionado, consentimiento sin marcar | Aceptar y continuar, Cerrar sesión; sin otras rutas del producto; F8 |

Escenas contextuales (`scene`): `invitar` = formulario de nombre/correo electrónico/empresa/un solo rol; `gestionar` = identidad seleccionada, rol, regenerar/restablecer, desactivar/reactivar y eliminar con motivos en línea; `enlace` = destinatario, enlace seleccionable, advertencia de vigencia/uso único/reemplazo, Copiar y Listo; `eliminar` = rechazo de la cuenta o confirmación con el correo electrónico exacto; `eliminar-rol` = rechazo del rol o confirmación de eliminación permanente. Una `scene` vacía es Ninguno. No se requiere ninguna otra vista exploratoria.

El catálogo de permisos es de **12 permisos**, suministrados una sola vez por SP-1. Las seis capacidades de Taller son texto de apoyo para un único `taller.usar` de alcance amplio; nunca deben convertirse en casillas independientes ni en claves de permiso inventadas. Conservar cuatro fieldsets agrupados y la geometría de editor elegida.

| Grupo de herramientas | Clave → etiqueta ES / EN |
|---|---|
| Planificación | `chat.usar` → Chat asistido / Assisted chat; `contador.usar` → Contador de globos / Balloon counter; `catalogo.ver` → Catálogo / Catalogue; `costos.usar` → Calculadora de costos / Cost calculator; `decoraciones.explorar` → Explorador de decoraciones / Decoration explorer |
| Taller 3D | `taller.usar` → Taller 3D / 3D workshop. Incluye IA de escena, planes de ensamblaje/hoja de construcción, exportación, proyectos y decoraciones propios; sin subcapacidades seleccionables de forma independiente. |
| Herramientas internas | `proyectos.ver_todos` → Proyectos de todos / Everyone’s projects; `gasto.ver` → Consumo de IA / AI spend; `internas.usar` → Herramientas internas / Internal tools |
| Administración | `cuentas.administrar` → Gestionar usuarios / Manage users; `roles.administrar` → Gestionar roles / Manage roles; `textos.corregir` → Corregir textos en inglés / Correct English copy |

Roles del sistema, en el orden exacto del selector/lista:

| Rol del sistema ES / EN | Permisos otorgados seleccionados (solo lectura) | Cantidad |
|---|---|---|
| Usuario · Entusiasta / User · Enthusiast | chat, contador, catálogo | 3 |
| Usuario · Designer / User · Designer | Igual que Entusiasta; sin permiso adicional ni límite numérico de chat | 3 |
| Usuario · Designer Plus / User · Designer Plus | Permisos de Entusiasta + costos | 4 |
| Usuario · Master Designer / User · Master Designer | Permisos de Designer Plus + Taller + explorador de decoraciones prediseñadas | 6 |
| Empleado interno / Internal employee | Todos los permisos de Master Designer + proyectos de todos, consumo y herramientas internas | 9 |
| Administrador / Administrator | Todos los permisos, incluida la administración de cuentas/roles/textos | 12 |

No existe un séptimo Usuario genérico. Los roles personalizados van después de los seis roles del sistema y conservan casillas independientes sin herencia silenciosa. `proyectos.ver_todos` permite leer originales ajenos; con `taller.usar` se puede guardar una copia propia, nunca editar el original (SPEC ronda 9). Las rutas/servicios usan claves, nunca etiquetas traducidas. La disponibilidad es distinta de la asignación: no se deben inventar permisos adicionales seleccionables para chat extendido, detección de estructuras o detección avanzada de globos. T1.2 actualmente marca esas tres como no disponibles y mantiene el permiso de costos con Designer Plus; ninguna herramienta pasa a estar disponible al cambiar la etiqueta de su rol.

**Datos compartidos del catálogo (R17, datos de referencia, no una nueva pantalla de precios de SP-2):**

| Orden | Nombre ES / EN | COP mensual | USD mensual |
|---|---|---|---|
| 1 | Entusiasta / Enthusiast | Gratis | Gratis |
| 2 | Designer / Designer | 20,000 | 7 |
| 3 | Designer Plus / Designer Plus | 45,000 | 14 |
| 4 | Master Designer / Master Designer | 70,000 | 25 |

El TSX del mock contiene un único fixture de catálogo de planes claramente marcado (nombres, precios en ambas monedas, herramientas acumulativas con disponibilidad y permisos seleccionados). Las opciones de rol y las marcas de verificación de los planes leen ese fixture; no mantienen arreglos de niveles que compitan entre sí. Producción lee el catálogo real de SP-1; este fixture de diseño no es un nuevo propietario en producción. Ni la invitación ni la gestión de cuentas agregan precios, acciones de compra o un selector de plan independiente. Entusiasta/Designer tienen permisos idénticos por ahora; el propietario aplazó los límites numéricos de chat, por lo que no se inventan valores ni un control de límite. La comparación completa, el texto de funciones no disponibles y los enlaces de entrada son alcance de SP-14.

El aviso completo se reproduce textualmente desde la SPEC. El texto entre corchetes permanece visiblemente pendiente de revisión legal, no un hipervínculo de política inventado. Es contenido de mock hasta que David/Sempertex suministren los campos legales antes de las invitaciones reales.

**ES — Aviso de tratamiento de datos personales (versión 1)**

[RAZÓN SOCIAL DE SEMPERTEX] tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a [CORREO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.

**EN — Personal data notice (version 1)**

[SEMPERTEX LEGAL NAME] will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to [RIGHTS CONTACT EMAIL]. The data-processing policy is at [POLICY URL]. By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012.

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

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 1101px+ | cuentas normal | El título de tarea de 24px se ubica sobre un único papel de cuentas reglado de ancho completo; no hay celda de edición, riel ni tarjeta de material. |
| UI-AC-02 | 1101px+ | cuentas normal | Cada registro agrupa visiblemente nombre, correo, empresa, rol, estado, último acceso y Manage. |
| UI-AC-03 | 360–760px | cuentas normal | La identidad ocupa todo el ancho de su registro; rol/estado y Manage se reacomodan debajo sin desbordamiento de página. |
| UI-AC-04 | 761–1100px | cuentas normal | La búsqueda abarca ambas columnas de filtros y Manage sigue a los demás campos de la fila. |
| UI-AC-05 | 360px+ | cuentas filtradas/vacías | El conteo de resultados coincide con los registros mostrados; limpiar filtros restaura el registro sin filtrar. |
| UI-AC-06 | 360px+ | carga | Los skeletons reemplazan el contenido no resuelto y un envío pendiente no puede repetirse. |
| UI-AC-07 | 360px+ | error de cuentas/roles | Las filas no confirmadas están ausentes y Reintentar es visible. |
| UI-AC-08 | 360px+ | error de inicio de sesión | El mismo rechazo y la misma sugerencia de espera de quince minutos aparecen para las cuatro causas de rechazo de credenciales. |
| UI-AC-09 | 360px+ | activación normal | Dos controles de contraseña y el aviso completo preceden al consentimiento sin marcar y al botón Activate deshabilitado. |
| UI-AC-10 | 360px+ | activación marcada | Marcar el consentimiento habilita una activación válida y el éxito explica que hay una sesión activa iniciada. |
| UI-AC-11 | 360px+ | invitación/restablecimiento inválido | La captura de contraseña se reemplaza por la recuperación mediante un enlace emitido por el administrador, sin divulgar la causa específica. |
| UI-AC-12 | 360px+ | invitación | Nombre/correo/empresa opcional/un rol preceden a la generación; un correo duplicado produce un rechazo. |
| UI-AC-13 | 360px+ | comprobante de un solo uso | Se ven el destinatario, el enlace seleccionable con ajuste de línea, Copy, el uso único/vigencia y la advertencia de reemplazo. |
| UI-AC-14 | 360px+ | comprobante descartado | El comprobante cerrado no puede recuperar su enlace anterior; la recuperación es regenerarlo. |
| UI-AC-15 | 360px+ | rol de sistema | Exactamente seis roles de sistema son de solo lectura y tienen 3/3/4/6/9/12 permisos seleccionados en el orden del catálogo/personal. |
| UI-AC-16 | 360px+ | rol personalizado | Cuatro grupos de herramientas contienen doce permisos disponibles; Taller es una sola casilla con texto de ayuda sobre las capacidades incluidas. |
| UI-AC-17 | 360px+ | validación de rol | Guardar un rol personalizado con nombre y sin ningún permiso anuncia ROL_SIN_PERMISOS y conserva la edición. |
| UI-AC-18 | 360px+ | rol en uso | La eliminación permanente está deshabilitada y la explicación de reasignar primero es visible. |
| UI-AC-19 | 360px+ | trabajo guardado/último administrador | El rechazo explica su invariante y la confirmación de eliminación permanente está deshabilitada. |
| UI-AC-20 | 360px+ | eliminación de cuenta sin trabajo | La eliminación permanente permanece deshabilitada hasta que el correo escrito coincida exactamente con la cuenta seleccionada. |
| UI-AC-21 | 360px+ | cuenta propia | La identidad coincide con la divulgación de la cuenta y la contraseña actual precede al par de contraseñas nuevas. |
| UI-AC-22 | 360px+ | éxito de contraseña propia | El mensaje indica que la sesión de este navegador fue renovada y que las sesiones anteriores terminaron; no aparece ningún requisito de segundo inicio de sesión. |
| UI-AC-23 | 360px+ | éxito de restablecimiento | El mensaje pide a la persona iniciar sesión con la nueva contraseña. |
| UI-AC-24 | 360px+ | compuerta de aviso | Están presentes el aviso completo con versión, el consentimiento sin marcar y cerrar sesión, mientras que el resto de la navegación del producto está ausente. |
| UI-AC-25 | 360px+ | rol de cuenta modificado | El rol único seleccionado se actualiza con un texto que explica la aplicación en la siguiente solicitud; las etiquetas de plan permanecen acumulativas. |
| UI-AC-26 | 360px+ | claro/oscuro | Los bordes de campos, los estados de casillas, las acciones con contorno y el foco son visibles sobre sus superficies reales. |
| UI-AC-27 | 360px+ | expresivo | El papel se registra verticalmente, los registros horizontalmente y la retroalimentación de regla/estado mediante trazos cortos, con la curva/temporización r13 y texto legible. |
| UI-AC-28 | 360px+ | reducido/estático | No queda movimiento en ejecución ni diálogo desplazado; los mismos controles y contenido son utilizables. |
| UI-AC-29 | 360px+ | invitación abierta/descartada | El tabulador permanece dentro del diálogo; al descartarlo se restaura el foco en la acción que lo inició. |
| UI-AC-30 | 360px+ | ES/EN | Los encabezados, etiquetas, avisos y acciones del diálogo se reacomodan sin desplazamiento horizontal de la página. |
| UI-AC-31 | 360–760px | roles normal | El selector de rol se apila antes del editor de permisos con su divisor horizontal. |
| UI-AC-32 | 761px+ | inicio de sesión/activación/restablecimiento/Mi cuenta/aviso | El espacio de trabajo del formulario mide como máximo 676px, centrado con márgenes exteriores iguales; los campos permanecen dentro de un eje de 620px. |
| UI-AC-33 | 761px+ | error/éxito de formulario/enlace inválido | El encabezado, la retroalimentación, la recuperación y el pie apilado siguen el eje centrado del formulario. |
| UI-AC-34 | 1101px+ | cuentas normal | Los filtros de búsqueda/rol/estado ocupan columnas flexibles 2:1:1 a lo ancho del registro. |
| UI-AC-35 | 1101px+ | roles normal | El selector de rol mide 240px; el ancho restante del editor contiene dos columnas de permisos. |
| UI-AC-36 | 360px+ | ambos temas | Los radios del papel/diálogo son de 32px, del aviso/retroalimentación 24px, de los campos 18px y de la casilla 8px, con acciones en forma de píldora. |
| UI-AC-37 | 1101px+ | cuentas normal | El relleno del papel es de 28px y el relleno vertical del registro es de 24px. |
| UI-AC-38 | 360px+ | ambos temas | El cuerpo usa Geist incrustada; los colores semánticos coinciden con el mapeo de producción y los bordes de entrada usan texto-tenue. |
| UI-AC-39 | 360px+ | ES/EN, diálogo | El idioma inicial de inspección es ES; EN traduce las etiquetas; el nombre accesible de cierre del diálogo en ES es Cerrar. |
| UI-AC-40 | 360–760px | vistas de formulario | El panel se contrae con relleno de papel de 20px y todas las acciones esenciales siguen siendo alcanzables sin desplazamiento horizontal. |
| UI-AC-41 | 360px+ | selector de rol de invitación/cuenta, ES/EN | Los cuatro nombres de plan del catálogo aparecen en el orden de los planes, luego Empleado interno, Administrador y los roles personalizados; EN usa Enthusiast. |
| UI-AC-42 | 360px+ | rol de sistema seleccionado | Entusiasta y Designer muestran los mismos permisos; costs tiene su primera marca en Designer Plus, Taller y explorer en su primera marca en Master Designer; los roles de personal incluyen todos los permisos de los planes. |
| UI-AC-43 | 360px+ | cuentas/roles, ES/EN | No se muestra ninguna etiqueta Plan 1/2/3, ningún límite numérico de chat inventado, ninguna acción de pago ni ningún campo adicional de plan aditivo. |


La verificación se aplica únicamente a **cuentas-admin@v1.amend-1.html**, reconstruido a partir de **cuentas-admin@v1.amend-1.tsx** con la cadena de herramientas fuera de línea actual. Compilación: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/cuentas-admin@v1.amend-1.tsx --out <design>/cuentas-admin@v1.amend-1.html` → **679 KB, 2150 archivos fuente, código de salida 0**, sin conexión. No se instalaron paquetes, no se descargaron recursos, no hubo alternativa de respaldo ni parches al HTML generado. Los hashes canónicos de entrada se conservan en la sección 1.

SHA-256 final del código fuente: `3e0b23dc622f24233bff202f996687d258b77ae2e1924d4caff6dc64dfcae017`. SHA-256 final del HTML: `e78373c1b2143abb364cb1d046ef027f191cbe1f4621500568a0169903232953`.

`python3 <kit>/kit/contrast.py <design>/cuentas-admin@v1.amend-1.html` → **contrast: 158 pairs checked in light and dark, all pass**, código de salida 0.

`UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/cuentas-admin@v1.amend-1.html --max-combos 476`, `/usr/bin/chromium` del sistema → **476 renderizados (476 combinaciones planificadas), 12.454 mediciones de texto, 1.463 paradas de foco**, código de salida 0. Ambos temas, todas las combinaciones de vista/estado y las escenas de diálogo a 1280/390px se midieron sin omisiones por muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Playwright fuera de línea complementario sobre la instantánea final: **446 aserciones aprobadas**. Cada rol de sistema tiene exactamente **3/3/4/6/9/12** permisos marcados de doce, en ambos temas e idiomas; costs first corresponde a Designer Plus, explorer first a Master Designer. La invitación, la gestión de cuentas y el filtro comparten el orden del catálogo, la edición personalizada sigue disponible tras el desplazamiento de índices de roles de sistema, y la protección del último administrador y la renovación canónica de la sesión propia permanecen intactas. La gestión de cuenta inicial selecciona el mismo rol Designer Plus que su destinatario realmente tiene; la invitación conserva ese valor predeterminado correspondiente. **140 casos responsivos** (siete vistas × dos temas × dos idiomas × 360/390/768/1024/1280px) aprobaron las comprobaciones de desbordamiento de página y de Geist. No se observaron excepciones de página ni solicitudes HTTP(S).

Pruebas de movimiento sobre la instantánea final, ambos temas: la entrada expresiva tiene **8 animaciones en ejecución**; `?still=1` **0**; Quieto (`?motion=still`) **0**; reducción de movimiento del SO **0**. Una vez inicializado el runtime, el diálogo de invitación es visiblemente opaco y tiene **0 animaciones en ejecución** en los modos de reducción del SO y Quieto. No se introdujo ninguna animación ni estilo nuevo.

Capturas de pantalla inspeccionadas en memoria sobre la instantánea final: **cuentas 1280/claro, roles 1280/oscuro, invitación 390/claro, roles 390/oscuro**. El papel redondeado, la estructura/navegación seleccionada, los seis roles de sistema y el selector móvil de invitación conservan la composición elegida. No se escribieron archivos de captura. Las comprobaciones estáticas aprobaron: doce secciones, estado de borrador, 43 ids de aceptación únicos, todos los hashes de entrada sin cambios, CSS idéntico byte a byte respecto de r13 y aviso ES/EN textual.

Historial/límite de la prueba: una apertura programática inmediata del diálogo antes de los fotogramas iniciales de estabilización de movimiento reducido del runtime produjo una ventana emergente transparente (tiempo de animación 0). Una prueba de disponibilidad que espera 300ms antes de abrir, en línea con el enfoque de inicialización de la auditoría, mostró opacidad 1 y ninguna animación en ejecución en ambos modos reducidos; las capturas finales usan esa condición de disponibilidad. Esta condición de carrera en el arranque del toolkit se registra en lugar de afirmarse como una aprobación incondicional en arranque en frío. No se editó ningún archivo del toolkit ni de producción. La primera auditoría completa también aprobó; tras alinear la selección inicial de gestión con el rol enmendado de su destinatario, se volvieron a ejecutar la reconstrucción final, la comprobación de contraste, la auditoría completa de 476 renderizados y las comprobaciones focalizadas anteriores. La evidencia canónica previa no se reutiliza como evidencia de la enmienda.


**No ejecutado:** lint/tipos/pruebas/compilación de producción, autenticación real o verificaciones de permisos del servidor, operaciones durables de roles/sesiones/tokens, concurrencia de base de datos, certificación WCAG completa o revisión legal. Esas corresponden a tareas posteriores de implementación/integración/revisión. Esta tarea de diseño no agrega código de producción y no certifica esas comprobaciones.


## 12. Preguntas abiertas y supuestos

**P: ¿Qué entidad legal, correo de contacto de derechos y URL de política reemplazan los campos entre corchetes antes de la activación externa real?** Responsable: David con el área legal de Sempertex. El cuerpo del aviso v1 fue aprobado en la ronda 7 de SPEC; los marcadores de posición y la revisión siguen explícitamente pendientes. No bloquean este borrador visual, y no se fabrica ninguna URL de política válida ni aprobación legal.

**Resuelto a partir del plan actual:** English Entusiasta = Enthusiast (responsable 2026-10-27); explorer pertenece únicamente a Master Designer y al personal; SP-1 es dueño del catálogo compartido; los valores numéricos del límite de chat se difieren explícitamente y no son un bloqueo de diseño. La pregunta heredada de r13 sobre la finalización del cambio de contraseña propia se responde con T2.2: se cierran las sesiones anteriores y se emite una nueva sesión para este navegador solicitante. Mi cuenta permanece con la sesión iniciada; el restablecimiento por parte de un administrador regresa por separado al inicio de sesión. T1.2 define 12 permisos otorgables y conteos acumulativos del sistema 3/3/4/6/9/12; las subcapacidades de Taller son texto de ayuda, no permisos otorgables por separado. Estas son correcciones de discrepancias verificadas, no nuevas decisiones del responsable.

**Confirmado:** Parte de acceso r13 seleccionada por el responsable; paleta de producción y Geist; jerarquía de formulario centrada y movimiento conservado; un rol por cuenta; seis roles del sistema/cuatro planes de catálogo acumulativos; al menos un permiso para roles personalizados; mínimo de ocho caracteres, invitaciones de siete días, restablecimientos de 24 horas; enlaces de un solo uso generados por el administrador sin correo automático; los enlaces nuevos sin usar revocan los enlaces previos del mismo tipo; sesión inmediata al activar; sugerencia genérica de inicio de sesión de quince minutos; reaceptación obligatoria del aviso; protecciones del trabajo guardado y del último administrador activo.

**Límites:** el éxito de los fixtures demuestra la retroalimentación, no la autenticación, el enrutamiento del servidor, los roles duraderos, la entrega al portapapeles, la expiración de tokens ni el cumplimiento legal. El inspector global expone combinaciones de estado/vista no relacionadas para su revisión, no transiciones de producto válidas. La persistencia y los conteos de roles, así como la elegibilidad del trabajo guardado, deben provenir de SP-1/T2.2, no de la posición en la lista del fixture. La implementación posterior debe verificar el foco de ruta, las mutaciones pendientes, la recuperación ante datos obsoletos/sin conexión, los lectores de pantalla y el comportamiento completo con teclado. La regla del producto de aviso según el idioma del navegador se mantiene; este artefacto de planificación comienza deliberadamente en ES para la inspección del responsable. No se habilita ni se crea ninguna vista previa de producción opcional.

**PREOCUPACIONES:** La aprobación independiente del plan/contrato sigue pendiente. Los marcadores de posición legales siguen pendientes de la respuesta del responsable/legal de Sempertex indicada arriba. El estilo del HTML empaquetado hermano no coincide con sus contratos de tokens de producción escritos; esta enmienda conserva el mapeo canónico elegido. Las dos correcciones de comportamiento exclusivas de la versión canónica ahora se incluyen en el propio TSX de la enmienda, evitando que se pierdan al reconstruir. No se inventa ninguna decisión sin resolver sobre el nombre del plan/explorer; las últimas aclaraciones de SPEC/T1.2 resuelven ambas. El kit puede dejar una ventana emergente transparente si el inspector la abre antes de sus fotogramas iniciales de estabilización con movimiento reducido; los diálogos en modo reducido ya inicializados pasan (sección 11). Consulte la sección 11 para ver la evidencia de auditoría actual real y sus límites.

T2.1 debe esperar la aprobación independiente de esta instantánea exacta enmendada; Designer no la aprueba. Los tres archivos de enmienda solicitados y el RESULT obligatorio de la delegación son todo el alcance de escritura; no se escribe ningún registro de cambios aparte, historial, SPEC, PLAN, código del repositorio, pruebas ni archivo de memoria.
