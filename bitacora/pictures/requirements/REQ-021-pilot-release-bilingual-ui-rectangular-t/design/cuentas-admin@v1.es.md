---
contract: cuentas-admin
version: 1
status: draft
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
author: Designer
date: 2026-10-26
---

# cuentas-admin@v1 — Inicio de sesión, invitación y administración

## 1. Identidad y trazabilidad

Este es el primer borrador de planificación, **no está aprobado para implementación**. La aprobación corresponde al responsable junto con el plan; el flujo de planificación copia esta instantánea sin cambios a `design/contracts/` después de la aprobación. No existe un contrato anterior. Esta tarea escribe deliberadamente solo este contrato y su maqueta HTML adyacente, además del resultado de delegación requerido; no crea un registro de cambios ni una vista previa del repositorio.

Instantánea de origen: REQ-021 `SPEC.md`, incluidas las rondas de aclaraciones 4–6 y el aviso bilingüe sobre el tratamiento de datos; estado de `PLAN.md`: borrador; esquema 1.3.0 de `PLAN.json`, revisión 1. SHA-256 en la inspección:

- SPEC: `10731db2ac74bc60ed91cb666974c0ee0d739bd0a52d2cc0078c444edb36fa92`.
- PLAN.md: `39c9327614da8587af25662a459d10d8c68cbc8713f92a60e2d014e3b6e1d4ac`.
- PLAN.json: `d39a1fb950015ad8d101d56acc82e77457d4d35ca8aaa672c170c97c3206eb30`.

Búsqueda exacta de consumidores: solo SP-2 nombra `ui.contract: cuentas-admin`, `version: 1`. `design_task`, `visual_review_task` y los ID de tareas de implementación de SP-2 **aún no están asignados**; no hay tareas de SP-2 en esta revisión. El Planner debe agregar esos consumidores, las comprobaciones de integración y una revisión visual antes de la ejecución. No invente ID de tareas. Dependencias previas: SP-1 T1.2 `permission-map@1`, T1.3 `account-service@1`, T1.4 `session-guard@1`. T1.4 ya se encarga de la respuesta simple `/sin-acceso`; los estilos y las acciones de V9 requieren coordinación con esa tarea, sin duplicar la autorización del servidor.

| Requisito | Vistas / flujos | Criterios de aceptación |
|---|---|---|
| R1 cuentas invitadas, sin registro abierto | V1–V6; F1–F4 | UI-AC-01–09, 13, 18 |
| R3 elegir permisos y administrar roles | V7–V8; F6 | UI-AC-14–17, 23 |
| R16 asignar exactamente un rol/plan de acceso | V5–V6, V8; F3, F5 | UI-AC-10–12, 15 |

Compatibilidad: **sin determinar** (contrato inicial; no hay una versión anterior ni una implementación con la que compararlo). Impacto directo: todas las vistas de SP-2 y las futuras tareas de interfaz. El mapa de permisos de SP-1 debe incluir explícitamente las rutas propuestas a continuación, especialmente la ruta pública de restablecimiento y las pantallas de cuentas/roles con protección independiente. SP-8/SP-10 reutilizarán la disposición y los textos para el soporte de idiomas; este borrador no cambia sus referencias de contrato ni afirma que su trabajo esté completo. No se afirma ningún impacto en pantallas no relacionadas de Taller o gastos.

## 2. Propósito y usuarios

- Persona invitada: identificar la invitación, crear una contraseña, leer y aceptar el aviso sobre datos y, luego, iniciar sesión. Éxito observable: una cuenta activa, la versión y la fecha del consentimiento registradas por el servicio y un destino permitido después del inicio de sesión.
- Persona que regresa: iniciar sesión con correo electrónico y contraseña, recibir instrucciones de recuperación, restablecer la contraseña mediante un enlace proporcionado por un administrador y cerrar sesión. Sin registro abierto, envío de correo de autoservicio, pagos, mejoras de plan ni precios de planes.
- Administrador de cuentas (`cuentas.administrar`): buscar una cuenta, invitarla, copiar su enlace de activación/restablecimiento, revisar su acceso, cambiar su único rol, desactivarla/reactivarla o eliminarla explícitamente cuando la política de eliminación lo permita.
- Administrador de roles (`roles.administrar`): consultar cinco roles del sistema, crear/editar un rol personalizado con permisos identificados por nombre y eliminar solo un rol personalizado que no esté asignado. Un rol personalizado puede conceder cada permiso de administración de manera independiente; no dependa del nombre del rol ni de `internas.usar` para conceder acceso a estas pantallas.
- Una persona que no tenga un permiso recibe una explicación y un destino seguro para volver, sin ver datos restringidos de cuentas.

## 3. Arquitectura de información y jerarquía

Marco público: logotipo de Pictures → título de la página → contexto identificativo → campos → una acción principal → instrucciones de recuperación/invitación. Los formularios de contraseña deben ser compactos; el aviso sobre datos se muestra completo en línea y nunca se oculta detrás de una casilla de aceptación.

Marco de administración: encabezado de Pictures con cuenta actual, tema y opción para cerrar sesión → título «Administración» → navegación «Cuentas» / «Roles» filtrada por permisos → título de la página y acción principal → búsqueda/filtros → lista → página de detalles. La administración existente de catálogos/internos es un destino independiente, no una nueva pestaña miscelánea de este flujo.

Detalles de la cuenta: identidad y estado → rol con resumen exacto de permisos → fechas de la cuenta y aceptación del aviso → enlace de recuperación → sección de acciones peligrosas separada. Las invitaciones destacan al destinatario y el acceso **antes** de crear el enlace. El enlace resultante es el contenido principal, acompañado por la fecha de vencimiento e instrucciones para compartirlo manualmente.

Editor de roles: nombre → casillas de permisos agrupadas → resumen de acceso exacto y actualizado en tiempo real → guardar/cancelar → sección de eliminación para roles personalizados. Nunca muestre una clave de permiso sin explicación como única etiqueta. Los recuentos son secundarios; no incluya tarjetas decorativas de análisis ni métricas de adopción inventadas.

## 4. Sistema de diseño y lenguaje visual

Evidencia de solo lectura: `t12` HEAD `fb872bce` y `pictures`/asesor HEAD `fa101a47`, ambos `src/app/globals.css`; `src/app/layout.tsx`; `src/app/login/{page.tsx,LoginForm.tsx}`; `src/components/ui/shell/{CabeceraApp.tsx,MenuApp.tsx}`; entrada de administración existente. Estos árboles de trabajo son referencias, no la base de ejecución. La paleta semántica es compartida; asesor también extrae el CSS de los botones con iconos. Reutilice la paleta del producto en lugar de reemplazar la aplicación con colores del tema del escritorio.

| Tokens existentes | Claro | Oscuro | Uso |
|---|---|---|---|
| `--fondo`, `--superficie` | #faf9fc, #ffffff | #0b0c10, #16181f | lienzo / paneles |
| `--superficie-suave`, `--superficie-2` | #faf8fd, #efe9f8 | #1c1e26, #242733 | secciones / rellenos secundarios |
| `--borde`, `--borde-suave` | #e3daef, #efe9f8 | #383c48, #2a2d38 | bordes decorativos / separadores |
| `--texto`, `--texto-suave`, `--texto-tenue` | #1c1425, #6b6178, #766c85 | #f4f5f7, #9aa1ad, #8a91a0 | encabezados, texto principal, metadatos |
| `--acento`, `--acento-hover`, `--acento-suave` | #6d3fe0, #5530b8, #ece3fb | #9479ff, #a58dff, #241f3d | principal, al pasar el cursor, seleccionado |
| `--sobre-acento` | #ffffff | #120b24 | texto principal (el tema oscuro no debe usar blanco) |
| `--exito`, `--exito-suave` | #1f7a55, #dcf5e9 | #78d6a8, #173b31 | completado / activo |
| `--error`, `--error-suave` | #b23a45, #ffeaec | #ff979f, #43252a | error / peligro |
| `--aviso`, `--aviso-suave` | #8f5f12, #fff3d8 | #f7c46b, #3f311c | desactualizado, pendiente de revisión legal |

Reutilice `.ui-button-primary`, `.ui-button-secondary`, `.ui-button-ghost`, `.ui-card`, `.ui-input`, `.ui-alert`, `.ui-chip`, los patrones existentes de casillas, selectores y menús, y el comportamiento de retorno del foco. Radio de tarjeta: 1.25rem; radio de controles: 0.7–0.8rem; `--radius` permanece en 0.8rem. El espaciado usa incrementos de 4/8/12/16/24/32/48px. Ancho máximo del marco: 1200px; formulario de autenticación: 440px; aviso/activación: 640px; formulario de administración: 760px. Estas son reglas de disposición, no nuevos tokens globales.

Tipografía: Geist sans existente mediante `--font-sans`/`--font-geist-sans`; fuente monoespaciada solo para enlaces/ID. La maqueta independiente usa alternativas locales `system-ui` y `ui-monospace`, porque no se permiten recursos de fuentes ni de red. Texto principal: 14–16px/1.5; etiquetas: 14px/600; título de página: 28–32px/1.2; título de sección: 18px/1.35; texto complementario: mínimo 13px. No introduzca una nueva fuente de marca.

Nuevo token semántico propuesto `--control-borde`: `--texto-tenue` en ambos temas, para los bordes de campos y casillas cuando el contraste de 3:1 no se alcance con el `--borde` decorativo existente, de bajo contraste. Mantenga `--borde` en los paneles. El foco usa el contorno existente de 2px con `--acento` y un desplazamiento de 2px. Use chips de estado con texto; los iconos son opcionales y los decorativos se ocultan a las tecnologías de asistencia (AT). Use la marca existente de anillo y punto. Las transiciones al pasar el cursor o enfocar deben durar ≤160ms; no use animaciones decorativas en bucle; el movimiento reducido elimina las transiciones.

## 5. Navegación y modelo de interacción

Contrato de rutas propuesto (el Planner debe conciliarlas y agregarlas al mapa de SP-1 antes de la implementación):

| Vista | Ruta propuesta | Acceso / salida |
|---|---|---|
| V1 inicio de sesión | `/login?from=<relative-path>` | pública; al completarse, vuelve a la ruta relativa segura del mismo origen indicada en `from`; de lo contrario, va al inicio de la sesión `/` |
| V2 activar | `/activar?token=…` | pública; consume la invitación solo al enviarla explícitamente; al completarse → V1 |
| V3 restablecer contraseña | `/restablecer?token=…` | pública; consume el enlace de restablecimiento solo al enviar el formulario; al completarse → V1 |
| V4 cuentas | `/administracion/cuentas` | `cuentas.administrar`; sale a una página de inicio permitida |
| V5 invitar / enlace creado | `/administracion/cuentas/invitar` | `cuentas.administrar`; volver → V4 |
| V6 detalles de la cuenta | `/administracion/cuentas/<id>` | `cuentas.administrar`; volver → V4 |
| V7 roles | `/administracion/roles` | `roles.administrar`; volver → una página de inicio permitida |
| V8 crear / editar / consultar rol | `/administracion/roles/nuevo`, `/administracion/roles/<id>` | `roles.administrar`; volver → V7 |
| V9 acceso denegado | respuesta `/sin-acceso` | respuesta de denegación existente de SP-1; «Volver al inicio», «Cerrar sesión» |

No incluya enlaces de administración en la navegación de personas no autorizadas. Las solicitudes directas siguen dependiendo de las protecciones del servidor. No agrupe todas las rutas de cuentas bajo la regla existente `/admin/*` (`internas.usar`) sin excepciones explícitas de permisos. Un administrador solo de roles debe poder acceder a V7/V8 incluso sin permisos de cuenta. Los endpoints de autenticación siguen a cargo de SP-1; los endpoints adicionales de las pantallas son trabajo del Planner, no API inventadas aquí.

Al navegar, mueva el foco al H1 nuevo (`tabindex=-1`); tras anunciar el resumen de validación del formulario, enfoque el primer campo no válido. La búsqueda no debe quitar el foco. Comportamiento del teclado nativo en los selectores; controles etiquetados. La confirmación usa un cuadro de diálogo modal, mantiene el foco dentro, inicia con Cancelar, se cierra con Escape excepto mientras haya una solicitud confirmada pendiente y devuelve el foco al control que lo activó. No use modales para formularios habituales. El botón «Atrás» del navegador conserva los filtros no confidenciales; nunca guarde contraseñas, tokens ni formularios completos en el almacenamiento. La maqueta tiene una barra propia, etiquetada, para seleccionar la vista/el estado fuera del marco del producto y no contiene destinos externos.

## 6. Flujos

**F1 iniciar sesión.** 1) Ingresa el correo y la contraseña con compatibilidad con gestores de contraseñas. 2) Envía una sola vez; la etiqueta cambia a “Ingresando…”. 3) Si la operación tiene éxito, resuelve el destino seguro; si el área solicitada ya no está permitida, muestra V9 en lugar de una oferta de mejora. 4) La contraseña incorrecta, el correo desconocido, la cuenta desactivada y el bloqueo muestran exactamente “No pudimos iniciar sesión. Revisa el correo y la contraseña o consulta con tu administrador.” No reveles si existe la cuenta ni el contador de intentos. 5) Aviso de recuperación: “Pide a tu administrador un enlace para restablecer tu contraseña.” El vencimiento de la sesión usa V1 con “Tu sesión terminó. Inicia sesión para continuar.” La sesión de 30 días no tiene un control “recordarme”.

**F2 activar.** 1) Valida el enlace sin consumirlo; muestra el destinatario de solo lectura y el rol asignado, obtenidos del servidor. 2) Define la contraseña (8–200 caracteres), confírmala y muestra el control para mostrar u ocultar; se permite pegar. 3) Lee el aviso completo proporcionado y muestra una casilla de aceptación explícita, desmarcada: “He leído el aviso y autorizo el tratamiento descrito.” 4) “Activar cuenta” valida y envía la contraseña y la versión del aviso. 5) Solo la confirmación de éxito del servicio muestra “Tu cuenta está activa” e “Ir a iniciar sesión”. Propuesta: no iniciar sesión de forma implícita (Q5). Los enlaces vencidos, usados o no válidos no permiten definir una contraseña; la indicación dice que se consulte con el administrador que envió la invitación. Un enlace vencido puede volver al inicio de sesión; uno usado ofrece específicamente iniciar sesión. Nunca consumas el enlace al cargar la página.

**F3 invitar.** 1) V4 “Invitar persona”. 2) Nombre y correo obligatorios, empresa opcional, selector obligatorio de un solo rol, inicialmente sin selección. 3) Muestra una vista previa de los permisos exactos antes de crear; cinco opciones del sistema más roles personalizados, sin un control de plan adicional independiente. 4) “Crear invitación” → servicio → mismo resultado V5 con destinatario, vencimiento del servidor y enlace seleccionable. 5) “Copiar enlace” realiza una copia iniciada por el usuario; si no está disponible, permite seleccionar y copiar manualmente. Anuncia “Enlace copiado” solo después de que la copia tenga éxito. Explica: “Compártelo directamente con esta persona. No se envió ningún correo.” No afirmes falsamente que se envió un correo. 6) Vuelve a V4; el enlace no se vuelve a mostrar a partir de un hash. La recuperación de invitaciones perdidas o vencidas sigue pendiente en Q2; no es una acción de regeneración disponible.

**F4 restablecer.** 1) En V6, cuenta activa: “Crear enlace de restablecimiento”. 2) Confirma el destinatario y explica: “Válido por 24 horas. Al cambiar la contraseña se cerrarán sus sesiones.” 3) Genera el enlace → resultado copiable en V6 con vencimiento y uso compartido manual. 4) El destinatario ingresa y confirma la contraseña nueva en V3; no vuelve a aceptar el aviso legal. 5) El éxito del servidor revoca las sesiones y muestra “Contraseña actualizada. Inicia sesión con tu nueva contraseña.” La edición de la contraseña actual y el restablecimiento de correo de autoservicio están fuera del alcance. El manejo de enlaces vencidos, usados o no válidos coincide con F2. Reemplazar un enlace de restablecimiento existente que no se haya usado está pendiente en Q2.

**F5 administrar cuenta.** 1) Busca por nombre o correo; filtra por estado y rol. 2) Abre V6; la identidad es de solo lectura (la edición del perfil no está dentro del alcance). 3) Cambia el rol único: muestra los permisos exactos nuevos y “Guardar rol”; pide confirmación si se agregan permisos administrativos o si esto elimina el acceso propio; explica que se aplica en la siguiente solicitud. 4) La confirmación de “Desactivar cuenta” indica que las sesiones finalizarán en la siguiente solicitud y que los datos se conservan; si tiene éxito, el estado pasa a Desactivada y la reactivación reemplaza la desactivación. 5) “Reactivar cuenta” usa la confirmación del servicio y devuelve la cuenta al estado activo; no implica crear una invitación. 6) La eliminación usa un diálogo de peligro separado con el correo del destinatario y una confirmación que requiere escribir el correo. Se prohíbe desactivar, eliminar o degradar al último Administrador activo; muestra el motivo junto a los controles deshabilitados; si el servidor rechaza por datos obsoletos, actualiza el estado autoritativo. Se ilustra la eliminación de una cuenta sin trabajo guardado asociado; el alcance destructivo para proyectos, decoraciones o gastos guardados sigue **sin resolverse en Q3**. Si una cuenta tiene trabajo asociado o desconocido, bloquea la eliminación final y muestra que la política está pendiente de resolución; no inventes una eliminación en cascada ni una promesa de conservación.

**F6 administrar roles.** 1) V7 separa cinco filas “Del sistema · Solo lectura” de los roles personalizados. 2) V8 “Crear rol” requiere un nombre y selecciones explícitas de permisos; ninguno está preseleccionado. La propuesta de exigir al menos un permiso está pendiente en Q4. 3) Las casillas son capacidades independientes, no un árbol de herencia obligatorio: seleccionar una capacidad nunca agrega otra silenciosamente. `taller.usar` es intencionalmente general y su texto de ayuda enumera IA de escena, exportación, proyectos y decoraciones propios, planes y hoja de armado. 4) El resumen enumera con precisión los nombres seleccionados y la cantidad; “Guardar rol” muestra el éxito del servicio. 5) Al editar un rol personalizado, la cantidad de cuentas asignadas permanece visible y se confirma que los cambios para las cuentas afectadas se aplican en la siguiente solicitud. 6) El rol del sistema muestra la misma matriz en modo de solo lectura, sin guardar ni eliminar. 7) Elimina un rol personalizado solo cuando la cantidad de asignaciones sea cero; en caso contrario, muestra “Este rol está asignado a N cuentas. Asígnales otro rol antes de eliminarlo.” No se implica que exista una herramienta de reasignación masiva.

## 7. Especificaciones de vistas

| Vista | Estructura, datos y texto visible | Acciones principales / secundarias | Adaptación responsiva |
|---|---|---|---|
| V1 | Pictures; “Iniciar sesión”; “Usa el correo con el que te invitaron”; etiquetas visibles Correo/Contraseña; texto de ayuda “El acceso es por invitación.” | “Entrar”; mostrar/ocultar; aviso de recuperación | Columna de 440 px, acción principal de ancho completo; desplazamiento de página con teclado/zoom |
| V2 | “Activa tu cuenta”; destinatario/rol; contraseña nueva + confirmación; “Aviso de tratamiento de datos · versión 1”; aviso completo y aceptación; advertencia de entrada legal en la maqueta | “Activar cuenta”; mostrar/ocultar; éxito → V1 | Columna de 640 px; aviso de ancho completo; sin área de desplazamiento legal anidada |
| V3 | “Restablecer contraseña”; destinatario identificado del enlace; ayuda de 8–200 y dos campos de contraseña; vencimiento del enlace | “Guardar contraseña”; V1 después del éxito | Columna de 440 px |
| V4 | “Cuentas”; llamada a la acción para invitar; búsqueda, filtros de estado y rol; la lista muestra nombre/correo, rol, estado y último acceso; texto con el total y los resultados filtrados | “Invitar persona”; “Ver cuenta” en cada fila | ≥640 px: tabla semántica; <640 px: tarjetas equivalentes con etiquetas, sin ocultar identidad/acceso/estado |
| V5 | Volver; “Invitar persona”; nombre/correo/empresa/rol; vista previa de acceso exacto; destinatario del resultado, vencimiento, enlace completo | “Crear invitación”; Cancelar; en el resultado, “Copiar enlace” y “Volver a cuentas” | ≥1024 px: formulario + panel lateral de acceso de 300 px; en tamaños menores, apila la vista previa antes del envío |
| V6 | Volver; nombre/correo/empresa/estado; fechas de invitación/activación/último acceso; versión/fecha del aviso o “Aún no ha aceptado”; selector de un solo rol y vista previa; sección de restablecimiento; sección de peligro | “Guardar rol”; restablecer; desactivar/reactivar; eliminar | ≥1024 px: columna de identidad + área principal; en tamaños menores, apila; los controles destructivos nunca aparecen solo como iconos |
| V7 | “Roles y permisos”; “Crear rol”; filas de roles del sistema con cantidad de permisos; filas de roles personalizados con cantidad de asignaciones | “Ver rol” o “Editar rol” | Una lista legible en todos los tamaños; las cantidades se ajustan a varias líneas en lugar de recortarse |
| V8 | Volver; “Crear rol” / nombre del rol; campo de nombre personalizado; matriz de permisos agrupados, casillas independientes con explicaciones; resumen; cantidad de asignaciones | “Guardar rol”; Cancelar; eliminar rol personalizado sin asignaciones | ≥1024 px: matriz + resumen de 300 px; en tamaños menores, una columna y área de activación completa para la etiqueta de cada casilla |
| V9 | “No tienes acceso a esta sección”; “Tu rol actual no incluye este permiso. Consulta con tu administrador si necesitas acceso.” Sin detalles del recurso restringido | “Volver al inicio”; “Cerrar sesión” | Columna de 440 px, botones que se ajustan a varias líneas |

Etiquetas de permisos del catálogo SP-1 (una sola fuente en la implementación):

| Grupo | Clave → etiqueta visible ES / texto de ayuda |
|---|---|
| Herramientas | `chat.usar` → Chat asistido; `contador.usar` → Contador de globos; `catalogo.ver` → Catálogo; `costos.usar` → Calculadora de costos; `decoraciones.explorar` → Explorador de decoraciones |
| Taller y proyectos | `taller.usar` → Taller 3D / Incluye IA de escena, planes y hoja de armado, exportación, proyectos y decoraciones propios; `proyectos.ver_todos` → Proyectos de todas las cuentas |
| Equipo interno | `gasto.ver` → Gasto de IA; `internas.usar` → Herramientas internas |
| Administración | `cuentas.administrar` → Administrar cuentas; `roles.administrar` → Administrar roles; `textos.corregir` → Corregir textos en inglés |

Resumen de roles del sistema: Usuario · Plan 1 = los tres primeros; Usuario · Plan 2 agrega costos/explorador; Usuario · Plan 3 agrega Taller; Empleado interno agrega todos los proyectos, gastos y herramientas internas; Administrador agrega los tres permisos de administración. Tienen 3/5/6/9/12 permisos, respectivamente, exactamente los del catálogo del servicio. No hay un sexto rol genérico de Usuario. El texto del producto está en español en SP-2; la interfaz bilingüe está en SP-10. La maqueta ofrece por separado el aviso legal ES/EN **ya proporcionado** como control para inspeccionar su contenido, no como preferencia de idioma de la cuenta ni como afirmación de que toda la interfaz esté traducida.

Contenido legal: reproduce el texto ES/EN de SPEC “Aviso de tratamiento de datos (borrador v1, SP-2)” **verbatim**, conservando los campos entre corchetes para el nombre legal, el correo para ejercer derechos y la URL de la política. Muestra “Texto pendiente de aprobación y datos legales” junto a la maqueta del aviso. Nunca conviertas un marcador de posición en un enlace falso a una política ni inventes asesoría legal. `notice_pending` deshabilita la activación hasta que el propietario o el equipo legal confirmen el contenido y se completen los campos; el escenario normal de aviso válido se simula explícitamente solo para la revisión de diseño. Los implementadores deben usar el contenido y la versión aprobados, y la URL real, antes de permitir la activación externa real. Este es el control existente de SPEC, no un flujo de aprobación nuevo.

## 8. Estados

Los nombres de estado siguientes son valores exactos del selector de la maqueta. Cada combinación aplicable se puede alcanzar con los selectores visibles “Vista” y “Estado”; las variaciones de diálogo tienen un selector “Diálogo” independiente. Los cambios de selector son controles de diseño, no funciones del producto. Los datos de la maqueta usan personas ficticias y `example.com`/`.invalid`; no se almacena ni envía nada.

| Estado | Vistas aplicables | Apariencia, acción disponible, transición / recuperación |
|---|---|---|
| `ready` | V1–V9 | Vista normal; V9 ya es una respuesta de denegación. Los formularios vacíos cuentan como listos, no como un estado de datos vacío. |
| `loading` | V1–V8 | Esqueleto estático con etiqueta / “Cargando…”; no se muestran datos momentáneamente ni se habilitan acciones de modificación. La carga de V1 representa la comprobación de sesión/destino, no datos remotos del formulario. |
| `error` | V1–V8 | Alerta; autenticación usa un rechazo genérico; los demás muestran “No pudimos cargar/guardar…” con reintento seguro y conservan las entradas no secretas. Un error de modificación nunca muestra éxito. |
| `offline` | V1–V8 | “Sin conexión. Vuelve a conectarte y reintenta.” Los borradores del formulario permanecen en memoria; las modificaciones están deshabilitadas; no se encolan guardados ni se repiten automáticamente. |
| `pending` | V1–V3, V5–V6, V8 | Envío en curso; cambiar campos o repetir el envío está deshabilitado; etiqueta específica para la acción. La tecla Enter no puede duplicar la solicitud. El resultado proviene únicamente de una respuesta confirmada del servicio. |
| `validation` | V1–V3, V5–V6, V8 | Resumen y errores en línea con etiquetas; se enfoca el primer campo no válido; sintaxis de correo, nombre/rol obligatorios, contraseña de 8–200 caracteres, confirmación coincidente y consentimiento obligatorio. Para el mínimo de permisos del rol, consulta Q4. |
| `success` | V1–V3, V5–V6, V8 | Acción completada explícitamente; V5 conserva el resultado para copiar hasta la navegación; V6/V8 muestran datos autoritativos actualizados. La acción de autenticación exitosa lleva al traspaso definido para el alcance; la maqueta no pretende mostrar el producto de inicio. |
| `empty` | V4, V7 | V4 sin cuentas: “Aún no hay cuentas” + Invitar. Este ejemplo representa una lista vacía permitida, no la eliminación del administrador actual. V7 sin roles personalizados: permanecen los cinco roles del sistema + Crear. |
| `no_results` | V4 | La búsqueda o los filtros no coinciden con ningún resultado: “No hay cuentas con estos filtros” + “Limpiar filtros”; distinto de no tener cuentas. |
| `stale` | V4, V6–V8 | Marca de tiempo y “No pudimos actualizar. Estos datos pueden haber cambiado.” Datos en caché de solo lectura, modificaciones deshabilitadas; “Actualizar” obtiene el estado más reciente. Las respuestas parciales usan la misma advertencia e identifican los campos no disponibles como “No disponible”; nunca muestran un cero falso. |
| `denied` | V4–V8 | Reemplaza la vista con V9; descarta los datos restringidos y no deja un formulario debajo. 401 vuelve a V1 con el aviso de sesión finalizada. |
| `expired`, `used`, `invalid` | V2–V3 | Reemplaza el formulario de contraseña, muestra un motivo legible y “Ir a iniciar sesión”, y pide al administrador un enlace válido; no muestra el valor del token ni información de la cuenta obtenida de un enlace no válido. |
| `notice_pending` | V2 | Marcadores de posición/advertencia legal visibles; casilla y activación deshabilitadas con el motivo junto a los controles. |
| `conflict` | V5–V6, V8 | Correo de invitación duplicado: identifica la cuenta existente solo ante un administrador autorizado y ofrece ir a la lista; cambio simultáneo de rol/estado: actualiza el registro autoritativo antes de volver a enviar. Conserva por separado la entrada propuesta; nunca la sobrescribe silenciosamente. |
| `last_admin` | V6 | Último Administrador activo; cambio de rol, desactivación y eliminación deshabilitados con la misma explicación; el restablecimiento sigue disponible. El rechazo del servidor sigue siendo autoritativo. |
| `fixed` | V8 | Nombre/permisos del rol del sistema de solo lectura, “Rol del sistema · Solo lectura”; sin guardar ni eliminar. |
| `role_in_use` | V8 | Rol personalizado editable; eliminación deshabilitada con la cantidad de cuentas asignadas y el siguiente paso requerido. |
| `disabled` | V1–V3, V5–V6, V8 | Acción principal deshabilitada con un motivo visible (entrada incompleta, rol sin cambios o requisito legal/de política pendiente). No se muestran iconos deshabilitados sin explicación. |

Diálogos que se pueden seleccionar en la maqueta: `change_role`, `deactivate`, `reactivate`, `delete_account`, `reset_link` en V6; `edit_role`, `delete_role` en V8. Cada uno tiene las fases `confirm`, `pending`, `error`. La eliminación final, el restablecimiento y los cambios de rol nunca se ejecutan al abrir el diálogo. Los secretos de contraseñas y tokens nunca se repiten en las alertas. Si falla el portapapeles, se muestra un error local con el enlace seleccionable; no se vuelve a crear la invitación.

No aplicable: V9 no tiene lista, modificación, carga, estado vacío, éxito ni estado sin conexión; es una explicación de denegación del servidor. El plan actual no requiere desplazamiento infinito ni paginación: si la API de implementación está paginada, se deben especificar el volumen de datos y la paginación; nunca se deben truncar cuentas silenciosamente. No hay operaciones destructivas optimistas ni cola de operaciones sin conexión en segundo plano. No hay envío/carga de correo ni error de entrega porque no existe un servicio de envío. No hay límites de gasto ni estado de facturación.

## 9. Comportamiento adaptable

Los puntos de quiebre son reglas de diseño explícitas propuestas para este subplan, basadas en `body { min-width: 320px }` y las convenciones `sm`/`lg` de Tailwind; no implican compatibilidad inferida únicamente con ciertos dispositivos:

- **Compacto 320–639px:** margen interno de página de 16px; una columna; los controles de la maqueta se ajustan a varias líneas; la lista de cuentas se convierte en tarjetas con campos etiquetados; los filtros de búsqueda/estado/rol se apilan. La marca y las acciones del encabezado se ajustan a varias líneas. Los enlaces Cuentas/Roles permanecen visibles y se ajustan (no se requiere navegación oculta tipo menú hamburguesa). Todos los grupos de formularios/acciones pueden ajustarse; las acciones principales ocupan todo el ancho. Ancho del diálogo `calc(100% - 32px)`, altura máxima `calc(100dvh - 32px)` y desplazamiento interno; Cancelar precede a la confirmación destructiva. La página sigue siendo desplazable con el teclado virtual y con el tamaño del texto al 200%.
- **Medio 640–1023px:** margen interno de 24px; tabla semántica de cuentas con ajuste de línea para correo/rol (la identidad no se comunica únicamente mediante texto truncado); los controles se ajustan en filas; los formularios y las vistas previas de acceso se apilan; ancho máximo de los diálogos de 520px.
- **Amplio ≥1024px:** margen interno de 32px, ancho máximo de 1200px; el formulario y el resumen de invitación/cuenta/rol pueden usar columnas 1fr/300px; la tabla de cuentas mantiene el ancho completo; la autenticación permanece estrecha en lugar de expandirse. El resumen no queda fijo si puede cubrir acciones en ventanas gráficas de poca altura.

Las URL/correos electrónicos completos usan `overflow-wrap:anywhere`; no hay desplazamiento horizontal a nivel de página en ninguno de los anchos declarados, incluido 320px. Se deben probar los límites 639/640 y 1023/1024. Con un zoom de escritorio del 400% (equivalente a una ventana gráfica CSS de 320px), se aplica el diseño compacto. Ningún elemento depende únicamente del cursor sobre el elemento; en móviles están disponibles las mismas operaciones. No hay una navegación que ocupe toda la pantalla.

## 10. Objetivos de accesibilidad

Objetivo **WCAG 2.2 AA**, pendiente de verificación del producto renderizado; un borrador/maqueta no constituye una afirmación de conformidad.

- Un H1; puntos de referencia de encabezado/navegación/contenido principal, enlace para saltar al contenido, títulos de tabla y encabezados con ámbito; las tarjetas compactas conservan las etiquetas y permiten las mismas operaciones. Usar enlaces para navegación real y botones para acciones. Los controles de escena de la maqueta son listas de selección etiquetadas fuera del producto.
- Etiquetas de formulario visibles, indicadores de campos obligatorios en texto, autocompletado correcto (`username`/correo electrónico, `current-password`, `new-password`, nombre/organización); sin acertijos de composición de contraseñas, bloqueo de pegado ni retos con temporizador. Los botones para mostrar/ocultar indican el estado actual y el campo asociado.
- Controles nativos o patrones accesibles existentes de Radix. Agrupar las casillas de permisos en conjuntos de campos con leyendas; el texto de ayuda describe las implicaciones generales de los permisos. Tab/Shift+Tab permiten acceder a todas las acciones; Espacio marca o desmarca una casilla; Enter envía una sola vez. Indicador de foco de 2px, con desplazamiento de 2px, que nunca quede recortado.
- Resumen de errores/alerta dinámica, además de `aria-invalid` y `aria-describedby` en el campo; el rechazo genérico de autenticación no revela si existe la cuenta. Anunciar de forma cortés la carga/finalización/confirmación de copia; no anunciar tablas completas que se vuelven a renderizar por cada pulsación. Usar `aria-busy` durante las operaciones pendientes o la carga.
- Diálogo con título/descripción etiquetados, fondo inerte, trampa de foco, foco inicial en Cancelar, cierre con Escape y retorno del foco al control que lo abrió; botón visible para cerrar/cancelar. Mientras haya una operación pendiente, explicar por qué el cierre está temporalmente deshabilitado. La acción destructiva requiere confirmación mediante correo electrónico; el correo de destino nunca aparece rellenado de antemano.
- Contraste de texto ≥4.5:1 (texto grande ≥3:1); controles significativos/foco ≥3:1. Usar `--control-borde` en los límites de los controles y los pares semánticos existentes; los bordes decorativos de paneles no son límites interactivos. Los controles deshabilitados también tienen un motivo adyacente legible. No comunicar el estado únicamente mediante el tono de color.
- Objetivo para este subplan: controles táctiles de 44×44px (mínimo WCAG de 24×24px, incluidas las excepciones de espaciado); áreas de activación de etiquetas ≥44px. Redimensionamiento del texto al 200%, adaptación a un ancho CSS de 320px y sin restricción forzada del zoom de la ventana gráfica. El movimiento reducido deshabilita las transiciones/animaciones no esenciales.
- Aún se requiere verificación del producto renderizado: secuencia de teclado y foco, comportamiento nativo del diálogo, anuncios del lector de pantalla, combinaciones de color medidas en ambos temas, zoom alto y enlace a la política legal una vez disponible. El aviso en inglés usa `lang=en`; la interfaz permanece en `lang=es` hasta la traducción de SP-10.

## 11. Criterios de aceptación visual

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 320–639px | V1 ready | Las etiquetas Correo y Contraseña, y Entrar, caben sin desplazamiento horizontal. |
| UI-AC-02 | ≥320px | V1 error | El correo desconocido, la contraseña incorrecta y las cuentas inactivas y bloqueadas muestran el mismo rechazo genérico. |
| UI-AC-03 | ≥320px | V1 pending | Entrar cambia a Ingresando… y se deshabilita el envío repetido. |
| UI-AC-04 | ≥320px | V1 ready | Las instrucciones de acceso solo por invitación están visibles y no hay ninguna acción para registrarse. |
| UI-AC-05 | ≥320px | V2 ready | El destinatario, el rol asignado y el aviso completo sobre datos aparecen antes de la acción de activación. |
| UI-AC-06 | ≥320px | V2 validation | La falta de aceptación del aviso se indica junto a la casilla sin marcar. |
| UI-AC-07 | ≥320px | V2 notice_pending | Los marcadores legales muestran una advertencia de contenido pendiente y la activación está deshabilitada. |
| UI-AC-08 | ≥320px | V2/V3 expired/used/invalid | El formulario de contraseña se reemplaza por instrucciones de recuperación y una acción para iniciar sesión. |
| UI-AC-09 | ≥320px | V3 success | La página confirma el cambio de contraseña y ofrece iniciar sesión, en lugar de mostrar otro formulario de contraseña. |
| UI-AC-10 | ≥1024px | V5 ready | Una sola opción de rol y su vista previa exacta de permisos están visibles simultáneamente en dos columnas. |
| UI-AC-11 | 320–1023px | V5 ready | La misma vista previa de acceso se apila antes del envío sin eliminar permisos. |
| UI-AC-12 | ≥320px | V5 ready | Las vistas previas de Plan 1/2/3 muestran 3/5/6 permisos con nombre, respectivamente, y no incluyen precio ni controles de pago. |
| UI-AC-13 | ≥320px | V5 success | El destinatario, el vencimiento a siete días determinado por el servidor, el enlace seleccionable y las instrucciones para compartirlo manualmente aparecen juntos. |
| UI-AC-14 | ≥320px | V7 empty | Los cinco roles del sistema, de solo lectura, siguen visibles cuando no hay roles personalizados. |
| UI-AC-15 | ≥320px | V8 ready | Marcar un permiso actualiza el resumen exacto sin seleccionar otros permisos. |
| UI-AC-16 | ≥320px | V8 fixed | Un rol del sistema tiene una etiqueta de solo lectura y no ofrece controles para guardar/eliminar. |
| UI-AC-17 | ≥320px | V8 role_in_use | Eliminar está deshabilitado junto al conteo de cuentas asignadas y las instrucciones para reasignarlas. |
| UI-AC-18 | ≥320px | V6 ready/reset_link | El diálogo de restablecimiento indica una validez de 24 horas y que la sesión se cerrará solo después del cambio de contraseña. |
| UI-AC-19 | ≥320px | V6 last_admin | Cambiar el rol, desactivar y eliminar están deshabilitados junto a la explicación de que es el último administrador. |
| UI-AC-20 | 320–639px | V4 ready | Cada tarjeta de cuenta conserva el nombre, correo electrónico, rol, estado y Ver cuenta. |
| UI-AC-21 | 640–1023px / ≥1024px | V4 ready | Los encabezados de la tabla identifican a la persona, el rol, el estado, el último acceso y la acción; los correos largos se ajustan a varias líneas. |
| UI-AC-22 | ≥320px | V4 no_results | Limpiar filtros restaura la lista sin filtrar sin crear una cuenta. |
| UI-AC-23 | ≥320px | V8 ready/edit_role | La confirmación para guardar el rol personalizado indica que las cuentas asignadas cambiarán en la próxima solicitud. |
| UI-AC-24 | ≥320px | V4/V6–V8 stale | Una advertencia de datos desactualizados incluye la hora de la última actualización y las modificaciones están deshabilitadas. |
| UI-AC-25 | ≥320px | V1–V8 offline | No se ofrece ninguna modificación como en cola o exitosa; el reintento requiere una acción deliberada. |
| UI-AC-26 | ≥320px | V6 ready/delete_account | La confirmación de eliminación requiere escribir el correo mostrado y conserva una acción Cancelar visible. |
| UI-AC-27 | ≥320px | V6 disabled | La eliminación de cuentas con trabajo guardado asociado o desconocido explica que la política está pendiente y no se puede confirmar. |
| UI-AC-28 | ≥320px | V4–V8 denied | Solo permanecen la explicación de acceso denegado y las opciones seguras para salir; no se muestran datos restringidos. |
| UI-AC-29 | 320 / 639 / 640 / 1023 / 1024 / 1440px | todos los estados accesibles | El documento no presenta desbordamiento horizontal. |
| UI-AC-30 | ≥320px | todos los estados interactivos | El foco del teclado permanece visible en cada control accionable en ambos temas. |
| UI-AC-31 | ≥320px | diálogos confirm/error | Escape cierra el diálogo y devuelve el foco al control que lo abrió. |
| UI-AC-32 | ≥320px | diálogos pending | La confirmación del diálogo está deshabilitada y no es posible duplicar la acción. |
| UI-AC-33 | ≥320px | ready/error/success | Los mensajes de estado usan etiquetas de texto y los pares medidos de primer plano/fondo cumplen AA. |
| UI-AC-34 | ≥320px | todos los estados de la maqueta | La etiqueta Mockup/draft y los selectores de vista/estado permanecen visibles y se pueden usar. |

## 12. Preguntas abiertas y supuestos

**Preguntas para el propietario (sin resolver; no son decisiones de implementación):**

- Q1 — David / área legal de Sempertex: ¿Cuáles son el nombre legal de la entidad, la URL real de la política de privacidad y el correo electrónico de contacto para ejercer derechos? ¿Se puede aprobar el aviso ES/EN versión 1 después de la revisión legal? Mantener los marcadores y bloquear la activación real mientras esté pendiente.
- Q2 — David, con SP-1 Planner: ¿Debería un administrador volver a generar una invitación vencida/perdida? ¿Generar una nueva invitación/enlace de restablecimiento debería invalidar todos los enlaces anteriores sin usar? Recomendación: una operación explícita de reemplazo invalida los enlaces anteriores del mismo tipo; esto no está contemplado actualmente en el contrato del servicio de invitaciones. En este borrador no se habilita ningún control para volver a generar enlaces.
- Q3 — David, con SP-4/SP-5/SP-6 Planner: ¿Qué ocurre con los proyectos guardados, las decoraciones personales y los registros de gasto de IA atribuibles cuando se elimina una cuenta, y qué texto exacto sobre la pérdida irreversible se debe mostrar? Hasta que se decida, bloquear la eliminación si hay trabajo asociado o no se puede verificar; permitir el caso sin trabajo asociado ya contemplado por SP-1, sin afirmar que se ejecuta una eliminación en cascada.
- Q4 — David: ¿Puede un rol personalizado no tener permisos? Recomendación: exigir al menos uno para evitar invitar a una persona a una cuenta inutilizable; la maqueta marca esto como una validación propuesta, que deberá ajustarse a la decisión futura del servicio.
- Q5 — David: Después de la activación, ¿la persona debería iniciar sesión explícitamente, como se muestra, o recibir una sesión de inmediato? Recomendación: inicio de sesión explícito, acorde con las operaciones separadas `activar` e `ingresar` de SP-1.

**Confirmado:** cuentas con un solo rol; cinco roles del sistema; roles del sistema fijos y roles personalizados editables conforme a la decisión actual de Planner; invitación copiada manualmente (7 días), restablecimiento generado por el administrador (24 horas), contraseña de 8 a 200 caracteres, sesión del servidor de 30 días; error genérico de inicio de sesión, incluidos los bloqueos; sin registro público; `/asesor` y `/happie` permanecen separados; el servidor aplica las modificaciones de cuentas/roles; el primer administrador se crea fuera de estas pantallas mediante el comando ejecutado por el propietario. No volver a plantear estos puntos como preguntas.

**Propuestas pendientes de aprobación del plan:** rutas y puntos de quiebre de las secciones 5/9, inicio de sesión explícito tras la activación, mínimo de un permiso personalizado, confirmación de eliminación mediante correo escrito y las decisiones de presentación/interacción de este borrador. Los datos de ejemplo seleccionados son ilustrativos; no son una lista de clientes identificada. Las fechas y los vencimientos del producto provienen del servidor y se muestran según la configuración regional del usuario, con la zona horaria disponible; la maqueta fija el 26 de oct. de 2026 a las 15:40 America/Bogota para que el resultado sea reproducible.

**Entrega a Planner:** agregar las tareas consumidoras exactas de SP-2 y los IDs de revisión visual; conciliar los permisos propuestos para las rutas/el restablecimiento público con SP-1, asignar la aprobación de publicación del aviso legal y la responsabilidad sobre la política de eliminación, y decidir si se necesita paginación en la API de la lista. Los escenarios normales/de éxito de la maqueta simulan entradas aprobadas válidas; no autorizan la activación real mientras Q1 siga abierta. Esta tarea completa los artefactos de planificación solicitados, no la aprobación del plan, la implementación del producto ni la validación legal en producción.
