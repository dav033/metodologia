---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
designer: Codex
date: 2026-10-26
---

# proyectos@v1 — Proyectos guardados

## 1. Identity and traceability

Planning draft for REQ-021 / M2 / SP-4, covering R6, R7 and US-3. **Not approved for implementation.** The owner approves this draft with the plan; the Designer grants no approval. This is the first version, with no predecessor. The companion `proyectos@v1.html` is a self-contained planning mockup, not `design/preview/` or a product implementation. No network, fonts, images, backend or real customer data are used.

Source snapshot read on 2026-10-26:

| Input | Revision / SHA-256 |
|---|---|
| SPEC.md, status ready | `fafa1d7e372305f80cf2ecae420c661145c6cf569a9e6d7967f7f3a3c469aa73` |
| PLAN.md, status draft | `77260acb94eb20a81d159a7beec889012ed58bdbae3ef512d1b4fa44dcfac112` |
| PLAN.json, schema 1.3.0, revision 1 | `1b47820ae156e298b94ea01c322bcd26b780c2310c6d9357caad4a0796d3dd38` |

Exact consumer: SP-4 `ui.contract=proyectos`, `ui.version=1`, `design_task=T4.1`, `visual_review_task=T4.8`. UI consumers: **T4.4** (V1–V4, D1–D3, saving and local drafts) and **T4.5** (V5 import). T4.2/T4.3 own versioned project-document@1, validation, authorization, durable mutation/import receipts and paginated APIs; T4.31 is the required storage checkpoint before UI work. T4.6/T4.7 exercise real cross-browser integration, T4.8 independently reviews visual fidelity and T4.9 audits spec/standards. These tasks remain draft; round 9 choices are pending. SP-1 owns authentication and permission semantics; SP-2 owns the shared account menu. SP-6/SP-12 consume project identity, not this UI contract automatically. SP-8/SP-10 own language rollout. SP-5's library remains separate. SP-13 consumes the accepted saved-work release flow.

Version record, embedded because this delegation permits only the two named design files: 2026-10-26 — initial draft and static mockup. Compatibility: **undetermined** against production (new server persistence and unresolved Q1–Q4); no approved consumer exists to migrate. Impact: SP-4 V1–V5, D1–D3 and shared Taller save-status placement. Required action: resolve round 9 / section 12, approve with the plan, then independently review rendered implementation. Reconciled with the live T4.1–T4.9/T4.31 breakdown before handoff; initial source inspection preceded that breakdown. T4.4/T4.5 must implement the resolved policy and T4.8 must review both full-staff and read-only custom-role variants. Do not silently promote the draft or choose unresolved product policies during implementation.

## 2. Propósito y usuarios

| Vista | Usuario / objetivo | Éxito observable |
|---|---|---|
| V1 Mis proyectos | Una cuenta con sesión iniciada y acceso a sus propios proyectos encuentra trabajo guardado | Abre el proyecto seleccionado del servidor y continúa la misma escena en otro navegador |
| V2 Todos los proyectos | Un empleado/administrador, o un rol personalizado con el permiso correspondiente, encuentra el proyecto de otra cuenta | El propietario aparece claramente en cada fila/tarjeta y el proyecto seleccionado se abre sin cambiar de propietario |
| V3 Proyecto propio en Taller | Un propietario autorizado guarda y continúa el trabajo | La confirmación del servidor identifica el proyecto guardado y la hora; un fallo nunca se muestra como si se hubiera guardado |
| V4 Proyecto de otro propietario, de solo lectura | El personal autorizado inspecciona el trabajo guardado | El propietario y el modo de visualización permanecen visibles; la política de edición está pendiente de Q2 |
| V5 Revisión de importación del navegador | Una persona con sesión iniciada decide si una escena local le pertenece | Una importación explícita crea un proyecto del servidor propiedad de la cuenta; los datos originales del navegador sobreviven a todos los resultados |

V4b es la misma vista de proyecto de solo lectura para un rol personalizado con `proyectos.ver_todos` pero sin `taller.usar`: no incluye navegación a Taller, acciones sobre proyectos propios ni acción de copia.

R6 corresponde a V1–V4 (incluida V4b), F1–F4 y UI-AC-01–15. R7 corresponde a V1/V5, F5 y UI-AC-16–19. La concurrencia corresponde a D2/F3; los cambios de permisos, a S8/F4. Los nombres, nombres de cuenta y fechas de la maqueta son datos ficticios.

## 3. Arquitectura de la información y jerarquía

Biblioteca de proyectos: estructura compartida de Pictures → navegación de secciones → título y una acción principal (“Nuevo proyecto”) → aviso opcional de importación del navegador → búsqueda por nombre (y filtro por propietario en V2) → cantidad y orden de resultados → proyectos. Cada proyecto muestra una ilustración no esencial de la escena, el nombre, la hora del último guardado en el servidor, el propietario en V2 y “Abrir proyecto”. Los guardados más recientes aparecen primero; se propone este orden de presentación. No se muestran métricas comerciales ni precios sin fundamento. Si falta una miniatura, se usa un marcador neutral de escena; nunca se impide abrir el proyecto. No se presupone el uso de IA para generar miniaturas.

Taller: volver a la biblioteca → nombre y propietario/modo del proyecto → estado veraz del guardado → “Guardar proyecto” / “Guardar ahora” → espacio de trabajo existente. Los objetos, las dimensiones y la ubicación de la escena constituyen el trabajo; no se agrega un panel de control del proyecto. “Guardar decoración” pertenece a SP-5 y debe seguir claramente etiquetado; no puede usarse como acción para guardar el proyecto. Los metadatos del proyecto se mantienen fuera del lienzo 3D y están disponibles para tecnologías de asistencia.

Revisión de importación: procedencia (“Solo en este navegador”) → cuenta de destino con sesión iniciada → nombre de la escena local y resultado de validación → casilla explícita de confirmación de propiedad → acción de importación → resultado y recuperación. Nunca se debe sugerir que una escena de un navegador compartido necesariamente pertenece a la cuenta actual.

No se agregan funciones de eliminación, uso compartido, carpetas, colaboración, exploración del historial del proyecto, publicación global ni acciones masivas. Se conserva la edición existente del nombre dentro de la escena; no se agrega un flujo independiente para cambiarlo.

## 4. Sistema de diseño y lenguaje visual

Evidencia de solo lectura: `t12` HEAD `fb872bce` y `pictures`/asesor HEAD `fa101a47`, `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/{Taller3D.tsx,ui-taller.ts,DialogoTaller.tsx,guardado-escena.ts,archivo-escena.ts}` y el componente compartido `src/components/ui/shell/CabeceraApp.tsx`. Ambos repositorios usan la misma paleta semántica. El diseño existente del producto tiene prioridad sobre las preferencias para escritorio. El borrador de cuentas `cuentas-admin@v1` es una referencia de coherencia, no una dependencia aprobada.

| Token existente | Claro | Oscuro | Función |
|---|---|---|---|
| `--fondo`, `--superficie` | #faf9fc / #ffffff | #0b0c10 / #16181f | lienzo, paneles |
| `--superficie-suave`, `--superficie-2` | #faf8fd / #efe9f8 | #1c1e26 / #242733 | áreas insertadas, relleno secundario |
| `--texto`, `--texto-suave`, `--texto-tenue` | #1c1425 / #6b6178 / #766c85 | #f4f5f7 / #9aa1ad / #8a91a0 | jerarquía del texto |
| `--borde`, `--borde-suave` | #e3daef / #efe9f8 | #383c48 / #2a2d38 | bordes de paneles, separadores |
| `--acento`, `--acento-hover`, `--acento-suave` | #6d3fe0 / #5530b8 / #ece3fb | #9479ff / #a58dff / #241f3d | acciones, estado al pasar el cursor, selección |
| `--sobre-acento` | #ffffff | #120b24 | texto sobre el color principal; no se debe usar blanco en botones oscuros de la biblioteca |
| `--exito`, `--exito-suave` | #1f7a55 / #dcf5e9 | #78d6a8 / #173b31 | guardado/importación confirmados |
| `--error`, `--error-suave` | #b23a45 / #ffeaec | #ff979f / #43252a | error |
| `--aviso`, `--aviso-suave` | #8f5f12 / #fff3d8 | #f7c46b / #3f311c | sin guardar, sin conexión, conflicto |
| `--overlay` | rgb(28 20 37 / .4) | rgb(0 0 0 / .6) | fondo de diálogo modal |

Dentro del `.taller-3d` real, mantén los equivalentes de `--taller-*` con alcance local y `BTN`/`BTN_PRI`/`BTN_ICO`, incluido su botón principal oscuro existente con texto blanco. La estructura independiente usa los tokens genéricos anteriores, sin combinar un acento oscuro genérico con texto blanco en los botones. Conserva el comportamiento existente de foco/modal de `DialogoTaller`. Reutiliza `.ui-button-primary`, `.ui-button-secondary`, `.ui-card`, `.ui-input`, las alertas de estado y las etiquetas. La maqueta usa controles semánticos nativos con estilos acordes a esos patrones.

La propuesta de alias semántico para el borde de controles `--control-borde: var(--texto-tenue)` coincide con el borrador de cuentas: úsalo en campos de entrada y listas de selección donde los bordes decorativos de bajo contraste no permitan identificar un control. No agregues otros tokens de color. Radio de controles: .8rem; radio de paneles: 1.25rem; espaciado: 4/8/12/16/24/32/48px. Ancho máximo de la biblioteca: 1200px; ancho máximo del contenido de importación legible: 760px; ancho máximo de los diálogos: 560px. Estas son decisiones de diseño, no nuevos tokens globales.

La tipografía de producción sigue siendo Geist sans (`--font-sans`, `--font-geist-sans`), con mono solo para identificadores técnicos cuando sea necesario. La maqueta sin conexión usa system-ui/ui-monospace como alternativas. Títulos de página: 28–32px/1.2; encabezados de sección: 18–20px/1.3; texto principal: 14–16px/1.5; metadatos: ≥13px. Los iconos complementan las etiquetas visibles y se ocultan a las tecnologías de asistencia. Foco: contorno de acento existente de 2px con desplazamiento de 2px. Transiciones de ≤160ms; sin efecto de brillo continuo en esqueletos ni movimiento decorativo; el movimiento reducido elimina las transiciones.

## 5. Navegación y modelo de interacción

Las rutas siguientes son **propuestas de enrutamiento** para Planner; las claves de permisos y los contratos de API corresponden a las tareas SP-1/SP-4.

| Vista / diálogo | Destino / entrada propuestos | Salida |
|---|---|---|
| V1 | `/proyectos`, navegación “Mis proyectos”, Taller “Mis proyectos” | Abrir → V3; Nuevo → V3 sin guardar; revisar escena local → V5 |
| V2 | `/proyectos?ambito=todos`, “Todos los proyectos” filtrado por permisos | Abrir propio → V3, el de otra persona → V4; “Mis proyectos” → V1 |
| V3 | `/3d?proyecto=<id>` o `/3d` para una escena nueva sin guardar | La biblioteca, las acciones de nuevo/abrir y la navegación pasan por la protección de cambios sin guardar F4 |
| V4 / V4b | `/proyectos/<id>` | Página autorizada de solo lectura; copiar solo cuando también se conceda `taller.usar`; nunca omitir el permiso de `/3d` |
| V5 | `/proyectos?importar=navegador`, aviso tras el primer inicio de sesión y enlace persistente a la escena local | “Ahora no” → V1; “Abrir proyecto” si la operación tiene éxito → V3 |
| D1 Guardar primer proyecto / copia | “Guardar proyecto” para una escena nueva o “Guardar una copia” | Enviar → V3 tras el éxito; Cancelar/Escape vuelve al espacio de trabajo sin cambios |
| D2 Conflicto al guardar | El guardado recibe una revisión más reciente del servidor | “Guardar una copia” → D1; “Abrir versión guardada” → D3 si hay cambios sin guardar; “Seguir aquí” conserva el trabajo local sin guardar |
| D3 Salir con cambios sin guardar | Abrir otro proyecto, crear uno nuevo o salir de la biblioteca con una escena modificada | “Guardar y continuar”, “Conservar borrador y salir”, “Seguir aquí” |

El menú de cuenta y el control de tema compartidos siguen SP-2 y el shell existente. No crear aquí pantallas separadas de inicio de sesión, cuenta, catálogo o decoración. La maqueta marca estos destinos como externos a SP-4 cuando se activan; la navegación real del producto usa sus rutas existentes. Si no hay acceso a los proyectos propios, se oculta la navegación de proyectos; las solicitudes directas siguen devolviendo una respuesta de permiso denegado. Los datos de la lista y los filtros por propietario provienen únicamente de resultados autorizados, nunca del filtrado en el cliente de los registros de todas las personas.

La tecla Enter envía los formularios de búsqueda/guardado. La búsqueda filtra los nombres de proyectos; el filtro de propietario de V2 es independiente y ofrece “Todas las cuentas”; ambos se conservan al abrir un proyecto y al volver. T4.3 pagina hasta 50 filas de metadatos por página. Mostrar “Cargar más proyectos” mientras exista un cursor, un recuento de elementos cargados en lugar de un total inventado y una opción visible para reintentar la página siguiente si falla. Conservar los resultados cargados y los filtros de búsqueda y propietario; nunca obtener documentos completos de escenas para filtrar la lista ni afirmar que una página cargada representa toda la biblioteca. La búsqueda, los filtros y la semántica del cursor deben estar vinculados de manera coherente en T4.3/T4.4.

## 6. Flujos

**F1 — Primer guardado y continuación (R6; cadencia provisional Q1 / ronda 9 q5).** 1) Una escena nueva muestra “Sin guardar en tu cuenta”. 2) “Guardar proyecto” abre D1 con el nombre actual de la escena. 3) Exigir un nombre sin espacios al inicio ni al final, de 1–120 caracteres (el mismo límite que el campo de nombre existente de Taller); los nombres visibles duplicados no identifican un proyecto ni reemplazan uno. 4) “Guardar en mi cuenta” desactiva los envíos repetidos mientras la solicitud está pendiente. 5) Solo tras la confirmación del servidor se muestra “Guardado en tu cuenta · 26 oct, 14:32” y una identidad de proyecto persistente. Si falla, se conservan la escena y el nombre, y se ofrece reintentar; si el resultado es desconocido, se reconcilia antes de reintentar, sin crear duplicados a ciegas. 6) Propuesta tras el primer guardado: serializar los guardados automáticos en la cuenta 500ms después de la última edición y ofrecer “Guardar ahora”; mostrar “Cambios sin guardar” hasta que se confirme la generación de edición correspondiente. Mantener una solicitud en curso y poner en cola la escena más reciente. Una respuesta anterior nunca debe borrar cambios más recientes pendientes de guardar. Toda respuesta se vincula a la cuenta, el proyecto y la identidad de la solicitud. Esta cadencia está pendiente de confirmación del responsable. La maqueta estática congela estos estados para su inspección; su selector de estado simula los estados pendiente y exitoso en vez de ejecutar un temporizador de carga en segundo plano.

**F2 — Volver a abrir (R6).** 1) Entrar en V1 o en V2 con autorización. 2) Buscar/filtrar; abrir un proyecto específico por su nombre. 3) Si la escena actual tiene cambios sin guardar, resolver F4 primero. 4) Mostrar la carga del proyecto y luego reemplazar el espacio de trabajo solo cuando la carga y validación de los datos hayan tenido éxito. 5) Restaurar el nombre, el contenido de la escena, las ubicaciones, las dimensiones y los colores sin convertir ni descartar silenciosamente los datos no compatibles. Si falla, el espacio de trabajo anterior permanece intacto y se explica si es posible reintentar; no recurrir a un resultado exitoso con una “escena vacía”. La inclusión de conversaciones está pendiente de Q3.

**F3 — Guardado concurrente (caso límite de R6).** 1) Otra sesión modifica el proyecto después de que esta sesión lo leyó. 2) El guardado rechaza una revisión obsoleta; D2 indica “Hay una versión más reciente” y muestra la fecha del último guardado en el servidor y su autor solo si los datos autorizados los devuelven. 3) Conservar el trabajo local y la escena más reciente del servidor. 4) Detener la cola de guardado automático ante un 409 hasta que se resuelva explícitamente el conflicto. Recuperación propuesta: guardar el trabajo local como un proyecto nuevo o abrir explícitamente la versión más reciente mediante D3. No ofrecer acciones de sobrescritura/guardado forzado ni fusión automática de campos. Se requiere una comprobación de comparación y guardado en el servidor; el modal por sí solo no puede garantizar la seguridad frente a conflictos de concurrencia.

**F4 — Salida / cambio de permisos.** 1) Una escena local con cambios sin guardar activa D3 antes de reemplazarla o navegar dentro de la aplicación. 2) “Guardar y continuar” reanuda la acción prevista solo después de confirmar el guardado; un conflicto o error cancela la salida y conserva el trabajo local. 3) “Conservar borrador y salir” conserva la escena no enviada como un borrador de recuperación local asociado a la cuenta/proyecto, no cambia ninguna revisión del servidor y luego continúa; nunca elimina el origen de la importación heredada. Al volver con la misma cuenta, ofrecer “Recuperar borrador” antes de reemplazar los datos guardados y conciliar su revisión de base. Otras cuentas no deben poder enumerarlo ni abrirlo. 4) Al cerrar la pestaña completa, usar el aviso nativo del navegador sobre cambios sin guardar cuando esté disponible, sin prometer un texto personalizado fiable ni persistencia garantizada. 5) Una sesión revocada lleva al inicio de sesión de SP-2 con una ruta de retorno segura; si se revoca el permiso sobre un recurso, mostrar S8 sin metadatos de propietario/título y no reintentar escrituras ni copiar datos de la cuenta a otra cuenta con sesión iniciada. Borrar el estado visible de la escena y las cachés de consultas al cerrar sesión o perder la autenticación, ignorar las operaciones completadas que correspondan a la identidad anterior y ofrecer recuperar lo retenido solo a la misma cuenta. Estos son límites de T4.4; Q1 confirma la cadencia de guardado, no autoriza divulgar borradores.

**F5 — Importación desde el navegador (R7).** 1) Detectar `taller3d:escena:v1` sin procesar después del primer inicio de sesión, sin modificarlo; la evidencia del repositorio indica que hay una escena actual, no una biblioteca inventada de varios proyectos en el navegador. 2) Ofrecer la opción solo en la primera visita autenticada a Taller con datos locales (T4.5), no dentro del controlador de inicio de sesión. Una cuenta sin acceso a Taller conserva el origen hasta que se le conceda acceso. Ofrecer “Hay una escena en este navegador” / “Revisar importación”; no asignarla automáticamente. 3) V5 muestra la cuenta de destino con sesión iniciada, el nombre de la escena local si puede leerse de forma segura y una casilla sin marcar “Esta escena es mía y quiero guardarla en esta cuenta”. 4) “Importar a mi cuenta” se habilita solo tras la confirmación y con datos válidos y compatibles; la importación es explícita. 5) Conservar el origen heredado sin procesar antes de que cualquier guardado automático normal de Taller pueda reemplazarlo; la detección de solo lectura no debe llamar al cargador normal que normaliza o descarta contenido malformado. 6) La confirmación del servidor crea un proyecto nuevo y un comprobante de importación por cuenta/origen; al revisar de nuevo, se muestra el resultado existente en vez de duplicarlo. 7) “Ahora no” pospone la acción sin ocultar la opción persistente de revisión; no eliminar el origen después de importar con éxito. 8) Si el origen no es compatible o está dañado, permanece local y se indica el motivo con la opción “Descargar copia original” (JSON sin procesar, sin afirmar que se puede abrir). No sustituirlo por un proyecto vacío.

## 7. Especificaciones de las vistas

**V1 — Mis proyectos.** H1 “Mis proyectos”; texto introductorio “Retoma tu trabajo desde cualquier navegador.”; acción principal “Nuevo proyecto” cuando se concede `taller.usar`. Si se muestra un aviso de importación, va antes de la búsqueda. Campo etiquetado “Buscar proyecto”, recuento “3 proyectos”, texto de orden “Guardados más recientes primero”. Tarjetas: “Quince años · Valentina”, “Boda · Jardín Botánico”, “Lanzamiento · Coral”; marca de tiempo “Guardado el 26 oct 2026, 14:32”; botón visible “Abrir proyecto” con un nombre accesible que incluya el título. Si hay un cursor, mostrar “Cargar más proyectos”; S13 contempla el error al cargar la página siguiente y conserva los resultados ya cargados. Las ilustraciones son opcionales y decorativas. Estado vacío: “Aún no tienes proyectos guardados” / “Crea un proyecto en el Taller 3D y guárdalo en tu cuenta.” / “Nuevo proyecto”. Si la búsqueda no arroja resultados, mostrar “No encontramos ese proyecto” / “Limpiar búsqueda”. F1/F2/F5; S1–S5/S8/S10.

**V2 — Todos los proyectos.** H1 “Todos los proyectos”; texto de apoyo “Consulta los proyectos guardados de cada cuenta.”; misma estructura que V1, más el filtro de propietario y el propietario visible en cada tarjeta (“Lucía Torres · Eventos Lila”, “Mateo Ruiz · Montajes Norte”). La cuenta de prueba de esta vista corresponde a una persona empleada, no a un usuario común con un selector de roles expuesto. Solo V2 y V4 muestran la identidad del personal en la maqueta. Sin acciones para crear proyectos en nombre de otras personas ni transferir la propiedad. F2/F4; S1–S5/S8/S10.

**V3 — Espacio de trabajo del proyecto.** El enlace a la biblioteca, el título del proyecto, la insignia textual del guardado en la cuenta y la acción de guardado permanecen visibles fuera del lienzo. Mostrar la hora del guardado, no solo “hace poco”; las fechas usan la configuración regional activa y una zona horaria local etiquetada si se muestra una comparación exacta. La región principal es el lienzo existente de Taller, el árbol de escena y el inspector; la maqueta los representa intencionalmente con ilustraciones y contexto etiquetados, no como un motor 3D funcional. “Simular edición” es un control exclusivo de la maqueta. Un proyecto nuevo comienza como “Proyecto sin título” y nunca aparece en V1 antes de que el servidor confirme el guardado. La acción de guardado se desactiva, con un motivo cercano, si no hay cambios, mientras carga o mientras hay una solicitud pendiente. F1–F4; S1/S2/S4–S12.

**V4 — Vista de solo lectura de un proyecto ajeno (propuesta Q2).** Página de escena de solo lectura separada en `/proyectos/<id>`, con “Proyecto de Mateo Ruiz” y “Solo lectura” siempre visibles. El borrador no incluye controles para editar la escena ni acciones para actualizar el original. “Guardar una copia en mi cuenta” abre D1 e indica explícitamente que la propiedad de destino pasa a la cuenta actual; el comportamiento de la copia personal requiere la aprobación de Q2. V4b omite el botón de copia y la navegación a Taller/proyectos propios cuando no se concede `taller.usar`, pero conserva el menú de cuenta, el propietario y “Todos los proyectos”. F2/F4; S1/S2/S4/S5/S8/S10. Nunca insinuar que abrir un proyecto concede permiso de escritura.

**V5 — Revisar importación.** H1 “Trae tu escena a tu cuenta”; subtítulo “La encontramos en este navegador. Revisa que sea tuya antes de importarla.” Mostrar destino “Lucía Torres · lucia@example.test”, origen “Este navegador”, nombre de la escena y estado. Casilla de verificación de F5; acción principal “Importar a mi cuenta”; acción secundaria “Ahora no”; acción de recuperación “Descargar copia original”. Si tiene éxito, mostrar “Escena importada a tu cuenta”, el nombre confirmado del proyecto y “Abrir proyecto”; mantener el mensaje de que el origen se conserva. Si el origen ya se importó, mostrar “Esta escena ya está en tu cuenta” y abrir el proyecto confirmado anteriormente. F5; S1–S8/S10/S11.

**D1 — Guardar proyecto / Guardar una copia.** Modal nativo con encabezado, “Nombre del proyecto”, límite de 120 caracteres, cuenta de destino, “Cancelar” y “Guardar en mi cuenta”. La copia comienza con “[original name] · copia”. Mensaje en línea si el nombre está vacío: “Escribe un nombre para el proyecto.”; conservar la entrada del usuario si ocurre un error. Mientras esté pendiente, mostrar “Guardando…” e impedir envíos repetidos. Cerrar el modal o pulsar Escape mientras hay una solicitud pendiente no debe dar a entender que se canceló una operación ya enviada; el resultado en segundo plano debe conciliarse de todos modos. No anidar un formulario dentro de otro.

**D2 — Hay una versión más reciente.** Explicar: “Otra sesión guardó cambios después de que abriste este proyecto. Tu trabajo sigue aquí.” Mostrar dos filas etiquetadas: “Tu trabajo · sin guardar” y “En tu cuenta · 26 oct 2026, 14:36”. Acciones “Guardar una copia”, “Abrir versión guardada”, “Seguir aquí”. Sin botones ambiguos como “Aceptar”, opciones destructivas predeterminadas, recargas automáticas ni sobrescrituras forzadas. El foco inicial va al encabezado.

**D3 — Tienes cambios sin guardar.** Explicar que un borrador local retenido solo es visible para esta cuenta en este navegador; botones “Guardar y continuar” (principal), “Conservar borrador y salir” (secundario), “Seguir aquí” (secundario, foco inicial). Si el guardado falla, sigue pendiente o tiene conflictos, no se puede completar la salida prevista. Cerrar o pulsar Escape equivale a “Seguir aquí”.

## 8. Estados

El mockup muestra selectores nativos `view`, `state`, `scene`, `theme` con las etiquetas visibles “Vista”, “Estado”, “Diálogo” y “Tema”. Las vistas son V1–V5 más la variante de permisos V4b (`foreign-limited`). Los valores de escena son `none`, `save`, `conflict`, `leave`. Los valores de tema son `light`, `dark`. Los valores de estado que se indican a continuación conforman el vocabulario exacto de integración. Al seleccionar un estado con un contexto específico, el mockup muestra ese contexto; esta es una navegación de planificación, no una transición de estado del producto.

| ID / valor del selector | Se aplica a | Resultado visible y recuperación |
|---|---|---|
| S1 `ready` | todas | Biblioteca/espacio de trabajo cargado; fuente local revisable. Las acciones del producto están habilitadas según los permisos y el estado de cambios pendientes |
| S2 `loading` | todas | Esqueleto estático y “Cargando proyectos…” / “Abriendo proyecto…” / “Revisando escena…”; `aria-busy`; no mostrar un estado vacío como si fuera exitoso ni activar escrituras |
| S3 `empty` | V1/V2/V5 | Estado realmente vacío de la biblioteca o “No hay escenas para importar en este navegador”; acción útil para volver o crear. El selector lleva el editor a V1 |
| S4 `error` | todas / D1 | “No pudimos cargar los proyectos” o “No pudimos guardar el proyecto”; motivo en línea, “Reintentar”; conservar la escena y el formulario existentes. Si falla la reapertura, no se reemplaza la escena |
| S5 `success` | V1/V2/V3/V4/V5 | Mensaje de confirmación del guardado o la importación con título y hora; no mostrar una confirmación ficticia antes de recibir la respuesta. La apertura es un estado cargado, no un guardado exitoso |
| S6 `disabled` | V3/V4/V5 | Escena propia sin cambios (“No hay cambios para guardar”), acceso de solo lectura a una escena ajena o falta de confirmación de propiedad; el motivo es visible, no se indica solo con opacidad |
| S7 `validation` | D1 o V5 | Error de nombre en D1, o fuente local no compatible/corrupta con el original conservado; el error del campo se anuncia y se asocia con él. De forma predeterminada, el mockup selecciona V3/D1 |
| S8 `permission-denied` | todas | “No tienes acceso a estos proyectos” sin mostrar título, propietario ni miniatura; “Volver al inicio” y navegación de cuenta; los controles no pueden eludir la protección |
| S9 `stale` | V3 / D2 | Revisión del servidor en conflicto; se conservan ambas escenas; consulta F3. El selector abre V3/D2 |
| S10 `offline` | todas | “Sin conexión. No podemos confirmar el guardado en tu cuenta.” El trabajo local se conserva; la lista solo muestra datos ya cargados que se identifiquen explícitamente, no una caché ficticia. “Reintentar conexión”; no se crea una cola automática de cuenta |
| S11 `pending` | V3/V5/D1 | “Guardando en tu cuenta…” / “Importando…”; se deshabilitan las mutaciones repetidas. Si se agota el tiempo sin conocerse el resultado, se muestra “No pudimos confirmar el resultado”; conciliar antes de volver a enviar. El mockup selecciona V3 |
| S12 `dirty` | V3 / D3 | “Cambios sin guardar”; guardar está habilitado; para salir se requiere D3. Guardar correctamente una copia de seguridad local no debe cambiar esta etiqueta |
| S13 `partial` | V1/V2 | Falló la página siguiente; los proyectos cargados anteriormente permanecen visibles, junto con el total cargado, el motivo y “Reintentar carga”. Al reintentar el cursor no se repiten las filas existentes. El selector abre V1, salvo que ya esté en V2 |
| S14 `no-results` | V1/V2 | Los filtros de nombre/propietario no arrojan coincidencias; mostrar el filtro activo y “Limpiar filtros”; nunca ofrecer la importación como si no existieran proyectos |
| S15 `recovery` | V3 | “Hay un borrador de esta cuenta en este navegador” con “Recuperar borrador”; la recuperación marca cambios pendientes y comprueba la revisión base almacenada antes de escribir. El selector abre V3 |
| S16 `unknown` | V3/V5 | “No pudimos confirmar el resultado”; conservar el trabajo local, deshabilitar nuevas mutaciones y ofrecer “Comprobar guardado” para conciliar el comprobante de la mutación/importación existente antes de reintentar. El selector abre V3, salvo que ya esté en V5 |

La cola persistente de carga sin conexión, la presencia en tiempo real de varios usuarios, el estado de generación de IA en segundo plano y los estados de eliminación de proyectos no aplican: ninguna de estas funciones está asignada a SP-4. Las miniaturas son opcionales; si fallan, se muestra un marcador de posición, nunca un error fatal del proyecto. Una escena malformada es un error; nunca se descarta silenciosamente para dejar un proyecto vacío. El vencimiento de sesión reutiliza SP-2, no abre un nuevo diálogo de inicio de sesión. No se usa un estado parcial para simular una escena cargada parcialmente.

## 9. Comportamiento adaptable

El ancho mínimo admitido es el mínimo existente del producto: 320px. Los puntos de quiebre del contenido se alinean con los valores existentes de Tailwind `sm` (640), `md` (768), `lg` (1024) y con el comportamiento de Taller en pantallas estrechas y apaisadas. Probar en 320, 390, 768, 1024 y 1440px, además de 844×390 en orientación apaisada.

| Rango | Biblioteca / importación | Taller / diálogos |
|---|---|---|
| 320–639px | Encabezado compacto, navegación de secciones con ajuste horizontal; H1 y acción apilados; filtros con etiqueta en una columna; tarjetas en una columna, nombres completos con ajuste de línea; márgenes internos de 16px | Estado del guardado en su propia fila con ajuste de línea, acción de guardado explícita y con etiqueta; primero el lienzo y luego el resumen contextual de la escena; el diálogo ocupa el ancho y el alto del viewport, con cuerpo desplazable internamente y área de acciones segura |
| 640–767px | Navegación sobre el contenido; márgenes internos de 24px; cuadrícula de dos tarjetas si cabe en el ancho disponible; filtros con ajuste de línea | Diálogo centrado de ≤560px, altura máxima de 92dvh; el contexto del editor permanece debajo del lienzo |
| 768–1023px | Cuadrícula de dos tarjetas; búsqueda y filtro de propietario en una línea; importación con ancho máximo legible de 760px | El lienzo y el resumen de la escena caben uno al lado del otro; el encabezado se ajusta en vez de recortarse |
| ≥1024px | Navegación de secciones en una barra lateral de 200px, área principal con ancho máximo de 1200px, cuadrícula de tres tarjetas; filtros en una fila completa | Se conserva la barra lateral y la distribución de lienzo/inspector existentes de Taller; diálogos centrados |

En orientación apaisada, con ancho ≤1023px y alto ≤540px, priorizar el espacio del lienzo y ubicar el contexto junto a él si cabe el contenido; no forzar un panel inferior alto para móviles. Con zoom/reflujo a 320 CSS px, volver a apilar. No debe haber desplazamiento horizontal de toda la página. Los nombres largos se ajustan en puntos seguros; se permite usar puntos suspensivos solo si el nombre completo está disponible de otra forma al tacto o con teclado, nunca únicamente mediante un tooltip al pasar el cursor. Las acciones de los diálogos se ajustan; ningún pie fijo debe cubrir el contenido; el cuerpo usa contención del desplazamiento excesivo. La expansión del inglés de hasta aproximadamente un 35% es un caso de estrés de diseño, no una garantía de traducción. Aquí se especifica el texto en español; SP-8/SP-10 integran el idioma de la cuenta y completan las traducciones. Este piloto no declara compatibilidad con RTL.

## 10. Objetivos de accesibilidad

El objetivo es WCAG 2.2 AA; la conformidad queda pendiente de la revisión del producto renderizado. Usar puntos de referencia `header`/`nav`/`main`, un H1, una lista semántica de proyectos, campos de entrada y selectores con etiquetas, botones y enlaces reales, y un enlace para saltar al contenido. Los nombres accesibles para abrir un proyecto incluyen el nombre del proyecto. La ilustración de la escena lleva `aria-hidden`; todos los datos del proyecto y del guardado están disponibles como texto. La identidad de la cuenta nunca se comunica únicamente mediante un avatar o un color.

Usar semántica nativa de diálogo modal (o la alternativa accesible existente), título y descripción asociados, foco contenido dentro del diálogo, tecla Escape y devolución del foco al activador. Foco inicial: nombre en D1; encabezado en D2; “Seguir aquí” en D3. Al validar, mover el foco al primer campo no válido; al finalizar la carga de datos o una comprobación de permisos, mover el foco al encabezado de la página solo después de una navegación real. No robar el foco repetidamente cuando se actualice el estado del guardado. El fondo queda inerte mientras el diálogo modal está abierto. El estado del guardado usa una región viva cortés; los errores que requieren acción usan una alerta una sola vez. Las etiquetas de estados sin conexión, obsoleto, deshabilitado y exitoso incluyen palabras además de color.

Todos los objetivos interactivos nuevos miden al menos 44×44 CSS px; los controles estrechos existentes de Taller quedan fuera de este rediseño del mockup, pero los controles nuevos para guardar y acceder a la biblioteca cumplen ese objetivo. Activación estándar por teclado, orden lógico en el DOM y al tabular, ninguna acción de proyecto que dependa solo de arrastrar y ningún menú que dependa solo del cursor. Contraste del texto ≥4.5:1 (texto grande ≥3:1); controles e indicadores de foco significativos ≥3:1. Los bordes decorativos de paneles no son indicadores de control. Admitir zoom de texto al 200% y reflujo al 400%; ningún elemento enfocado debe quedar oculto bajo encabezados fijos. Respetar la preferencia de movimiento reducido. El contraste debe medirse en pares reales de primer plano y fondo para ambos temas; el nombre de un token no es evidencia. El acceso al motor 3D mediante teclado forma parte del alcance existente, pero toda acción de proyecto nueva debe poder usarse sin interactuar con el lienzo.

## 11. Criterios de aceptación visual

| ID | Punto de quiebre | Estado | Resultado observable |
|---|---|---|---|
| UI-AC-01 | ≥1024px | ready / V1 | La biblioteca muestra tres columnas de tarjetas de proyecto junto a la barra lateral de secciones. |
| UI-AC-02 | 320–639px | ready / V1 | Las tarjetas, la búsqueda y la acción para crear un proyecto caben en una columna sin desplazamiento horizontal de la página. |
| UI-AC-03 | 640–1023px | ready / V1 | La cuadrícula de proyectos tiene dos columnas y la navegación está sobre el contenido. |
| UI-AC-04 | 320–1440px | ready / V2 | Cada tarjeta de proyecto muestra al propietario como texto visible. |
| UI-AC-05 | 320–1440px | no-results | Se muestra una acción para borrar los filtros junto con la explicación de que no hay resultados. |
| UI-AC-06 | 320–1440px | empty / V1 | Aparece “Aún no tienes proyectos guardados” junto con “Nuevo proyecto”. |
| UI-AC-07 | 320–1440px | loading | Se muestran esqueletos y una etiqueta de carga en lugar de indicar que la biblioteca está vacía. |
| UI-AC-08 | 320–1440px | dirty / V3 | “Cambios sin guardar” aparece junto a la acción de guardar habilitada, fuera del lienzo. |
| UI-AC-09 | 320–1440px | success / V3 | La confirmación del guardado en la cuenta incluye la hora del guardado en texto visible. |
| UI-AC-10 | 320–1440px | validation / D1 | Al enviar un nombre en blanco, el modal permanece abierto y el error se asocia con el campo del nombre. |
| UI-AC-11 | 320–1440px | pending / D1 | El botón de envío muestra “Guardando…” y no permite iniciar un segundo guardado. |
| UI-AC-12 | 320–1440px | stale / D2 | Ambas versiones, la local sin guardar y la guardada en el servidor, están etiquetadas y no hay una acción para sobrescribir a la fuerza. |
| UI-AC-13 | 320–639px | dirty / D3 | Las tres opciones para salir siguen siendo accesibles mediante desplazamiento vertical. |
| UI-AC-14 | 320–1440px | disabled / V4 | El propietario y “Solo lectura” son visibles y no se ofrece una acción para actualizar el original, sujeto a Q2. |
| UI-AC-15 | 320–1440px | permission-denied | En la vista de acceso denegado no aparecen nombres, propietarios ni miniaturas de proyectos restringidos. |
| UI-AC-16 | 320–1440px | ready / V5 | La importación muestra la cuenta de destino con sesión iniciada sobre la confirmación de propiedad, que aparece sin marcar. |
| UI-AC-17 | 320–1440px | disabled / V5 | La importación permanece deshabilitada hasta marcar la casilla de confirmación de propiedad. |
| UI-AC-18 | 320–1440px | validation / V5 | Una fuente incompatible muestra el motivo y la acción para descargar la copia original. |
| UI-AC-19 | 320–1440px | success / V5 | La importación confirmada muestra una acción para abrir el proyecto e indica que se conserva el original del navegador. |
| UI-AC-20 | 320–1440px | partial / V1 | Las tarjetas cargadas anteriormente permanecen visibles junto a un control para reintentar la carga de la página siguiente. |
| UI-AC-21 | 320–1440px | offline | El estado del guardado en la cuenta indica explícitamente que no se puede confirmar el guardado. |
| UI-AC-22 | 320–1440px | error | Aparece un control etiquetado para reintentar sin reemplazar el contenido de la escena existente por una escena vacía. |
| UI-AC-23 | 320–1440px | ready / D1–D3 | Escape cierra el diálogo y devuelve el foco al control que lo activó. |
| UI-AC-24 | 320–1440px | ready / ambos temas | El foco en cada control de proyecto/guardado es visible sobre su fondo real. |
| UI-AC-25 | 844×390px | dirty / V3 | Los controles y el estado del guardado siguen siendo accesibles mientras el espacio de trabajo se adapta al viewport de poca altura. |
| UI-AC-26 | 320–1440px | ready / dark | Los botones primarios genéricos usan `--sobre-acento` en lugar del blanco. |
| UI-AC-27 | 320px con reflujo | ready / V1 | Los nombres largos de proyectos se ajustan y pueden leerse sin un tooltip al pasar el cursor. |
| UI-AC-28 | 320–1440px | ready / V4b | La vista de solo lectura con rol personalizado no tiene acciones de copia ni de Taller. |
| UI-AC-29 | 320–1440px | recovery / V3 | El aviso de recuperación identifica esta cuenta y ofrece una acción explícita para recuperar el borrador. |
| UI-AC-30 | 320–1440px | unknown | Aparece una acción para conciliar el resultado mientras las nuevas mutaciones están deshabilitadas. |

## 12. Open questions and assumptions

Decision owner for all questions: David with the Planner. The following proposals are visible in the mockup for review; they are not settled behavior. Resolve them before implementation consumes this contract.

- **Q1 — Save cadence and recovery:** Confirm round 9 q5: first account save explicit with a name, then serialized 500ms debounced autosave plus “Guardar ahora”, as now proposed by the Planner, or manual saves throughout? Local recovery remains isolated by account/project and is never disclosed after an account switch. No durable offline upload queue is proposed.
- **Q2 — Foreign-project writes:** Can staff change another owner's original project, or only inspect it and create a copy under their own account? The draft proposes read-only original plus an explicitly owned personal copy; ownership is never reassigned by opening.
- **Q3 — Reopened/imported content:** Does “project” include the Taller AI conversation, or only the scene, its name and scene configuration? Existing scene storage keeps the conversation separately. Round 9 q6 and T4.2 propose name plus complete Escena, including room, materials and attachments, excluding conversation/media. The draft models that complete document; it does not promise conversation restoration or import.
- **Q4 — Search and owner-filter scope:** Confirm name search and owner filtering over the entire authorized server library, rather than only the loaded page? This draft proposes server-wide results. T4.3 currently specifies cursor pagination without search/filter query parameters; the Planner must align its API contract and T4.4 tests with this decision before implementation.

Confirmed: users see their own projects; authorized staff can open everyone's; browser scenes are offered for explicit import; original data must not be lost; later saves must not silently overwrite earlier concurrent saves. Saving requires server acknowledgment. Plan 3 includes own Taller projects; custom roles are evaluated by actual permissions, not display names.

Presentation assumptions/proposals: `/proyectos` routes, name search and most-recent-save order; 1–120 character trimmed names consistent with existing editor; one detected current browser scene from the evidenced key; no delete/share/history UI; source receipt/deduplication and raw-source preservation are required implementation mechanisms to fulfill lossless import. T4.2/T4.3 specify project-document@1, 2 MiB limit, complete scene validation, atomic revision compare-and-save and account-scoped durable mutation/import receipts. T4.4 must bind paginated search/filter presentation to the API consistently; no inference from static fixtures. Authoritative errors: missing/inaccessible item 404 (generic “Proyecto no disponible” with no metadata), collection-scope denial 403, unauthenticated 401 (SP-2), conflict 409, too-large 413 (retain scene and explain 2 MiB limit). The scene mockup is CSS illustration and cannot prove identical 3D round trips, concurrency, access control, storage retention, import idempotency or accessibility compliance. Those need task-level integration tests and independent rendered review. No preview setting is required for these explicitly requested planning files.
