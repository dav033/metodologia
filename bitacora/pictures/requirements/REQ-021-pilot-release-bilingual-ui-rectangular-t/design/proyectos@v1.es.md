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

## 1. Identidad y trazabilidad

Borrador de planificación para REQ-021 / M2 / SP-4, que abarca R6, R7 y US-3. **No está aprobado para implementación.** El propietario aprueba este borrador junto con el plan; el diseñador no concede aprobación. Esta es la primera versión, sin predecesor aprobado; esta revisión conserva el borrador de planificación existente y las respuestas aceptadas de la ronda 9. Esta revisión atiende los comentarios del propietario del 2026-10-26 21:01: reconstruir cada vista a partir de la plantilla y los fragmentos de componentes de david-ui, conservando los flujos, vistas, estados y criterios acordados. Los colores del proyecto se asignan a los roles del kit; el CSS/JS de los componentes se inserta sin cambios. La alineación, el relleno, los bordes de controles en tema oscuro y la casilla de verificación de propiedad son objetivos explícitos de revisión. Se mantienen las correcciones anteriores sobre guardado pendiente y foco de diálogo. SP-2 sigue siendo el foco de planificación: este trabajo no confirma SP-4 ni cambia la aprobación del plan. El archivo complementario `proyectos@v1.html` es un mockup de planificación autocontenido, no `design/preview/` ni una implementación del producto. No se usan solicitudes de red, fuentes o imágenes externas, backend ni datos reales de clientes.

Instantánea de origen leída el 2026-10-26:

| Insumo | Revisión / SHA-256 |
|---|---|
| SPEC.md, estado listo | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md, estado borrador | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json, esquema 1.3.0, revisión 1 | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |

Consumidor exacto: SP-4 `ui.contract=proyectos`, `ui.version=1`, `design_task=T4.1`, `visual_review_task=T4.8`. Consumidores de UI: **T4.4** (V1–V4, D1–D3, guardado y borradores locales) y **T4.5** (importación V5). T4.2/T4.3 son responsables de project-document@1 versionado, validación, autorización, comprobantes durables de mutación/importación y API paginadas; T4.31 es el punto de control de almacenamiento obligatorio antes del trabajo de UI. T4.6/T4.7 prueban la integración real en distintos navegadores, T4.8 revisa de forma independiente la fidelidad visual y T4.9 audita la especificación/los estándares. Estas tareas siguen como borrador; el comportamiento de la ronda 9 está definido, mientras la aprobación del diseño/subplan sigue pendiente. SP-1 es responsable de la semántica de autenticación y permisos; SP-2, del menú de cuenta compartido. SP-6/SP-12 consumen la identidad del proyecto, no este contrato de UI automáticamente. SP-8/SP-10 son responsables del despliegue de idiomas. La biblioteca de SP-5 sigue separada. SP-13 consume el flujo aceptado de publicación del trabajo guardado.

Registro de versiones, incluido aquí porque esta delegación solo permite los dos archivos de diseño nombrados: **2026-10-26, comentarios del propietario 21:01 — reconstrucción con el kit.** Compatibilidad: **cambio visual compatible** con este borrador no aprobado: mismos permisos del producto, navegación, flujos F1–F6, seis variantes de vista, 26 estados y D1–D3. La estructura, las tarjetas, los campos, los selectores, los botones, las alertas, las insignias, la casilla de verificación, los diálogos y las notificaciones ahora usan la anatomía del kit. Las propuestas de diseño específico del proyecto/ilustración/modal nativo conservan los puntos de quiebre declarados. El destino de importación y la nota al pie sobre consentimiento y retención/descarga comparten un borde izquierdo en la misma columna legible. La acción principal aparece una vez por vista activa; la biblioteca vacía ya no la repite en su encabezado. Impacto: T4.4, T4.5 y T4.8; T4.1 debe copiar la instantánea aprobada por el propietario. Los contratos de almacenamiento/consulta de T4.2/T4.3 no cambian. La aprobación sigue correspondiendo al propietario; esto no constituye una dependencia de implementación aprobada. A continuación se conserva el registro de revisiones anteriores. **2026-10-26, comentarios del propietario 19:36 — reconstrucción completa de la capa visual**. Compatibilidad: **cambio visual compatible** con este borrador no aprobado: V1–V5/V4b y D1–D3 conservan su contenido, destinos, permisos, modelo de interacción, vocabulario de estados y estructura de puntos de quiebre. La estructura/navegación neutra, los avisos planos con separadores y los grupos de importación/conflicto, la tipografía compacta con mayúsculas y minúsculas convencionales, el SVG integrado coherente y las cifras tabulares de guardado alineadas a la derecha reemplazan la interfaz anterior teñida, los textos decorativos en mayúsculas, las tarjetas anidadas y el glifo decorativo del estado vacío. La paleta semántica existente no cambia. Consumidores afectados: SP-4 T4.4 (V1–V4b/D1–D3), T4.5 (V5) y revisión renderizada independiente T4.8; T4.1 copia este borrador exacto tras la aprobación del propietario. No se implica ningún cambio de API/almacenamiento ni nueva dependencia para T4.2/T4.3; T4.6/T4.7 siguen siendo responsables de la evidencia del entorno de ejecución real. No se afirma que una implementación esté aprobada ni sea compatible sin revisión de T4.8. Acción requerida: aprobación del propietario junto con el plan, seguida de la revisión renderizada de la implementación. Se conserva el registro de revisión anterior: revisión de inspección actual — sin cambios en el comportamiento ni el diseño del producto; el mockup ahora aplica la protección existente ante salida con cambios sucios/pendientes/desconocidos a “Nuevo proyecto” y conserva el objetivo de foco de origen en la transición D2 → D1/D3, con una alternativa contextual si ese objetivo ya no existe. D3 ahora muestra junto a la acción deshabilitada para guardar y continuar el motivo existente de pendiente/desconocido/sin conexión. Compatibilidad: **corrección compatible con este mismo contrato de borrador**; consumidor de UI afectado T4.4, F4 y D1–D3. T4.8 debe verificar ambos comportamientos en la implementación de producción. Se reparó la continuidad de las tablas Markdown para todos los estados y criterios visuales. A continuación se conserva sin cambios el registro de revisión anterior del borrador: 2026-10-26 — conservar el borrador inicial y el mockup estático; revisar tras los comentarios del propietario/Planner de las 18:53. Compatibilidad: **cambio de comportamiento incompatible con el mockup de planificación anterior** para la búsqueda/paginación de V1/V2, ahora modeladas con más de 50 fixtures, límites de consulta normalizados, restablecimiento de filtros, rechazo de respuestas tardías y recuperación de la página siguiente. Resolver el contenido/copy provisional de guardado conserva el diseño previsto de V3–V5/D1–D3. Compatibilidad con producción: **indeterminada**; la persistencia en servidor es nueva y no existe ningún consumidor aprobado que deba migrar. Consumidores exactos afectados: SP-4 T4.4 (consultas V1/V2, estados de guardado/copia V3/V4 y D1), T4.5 (explicación de importación de escenas completas V5), T4.6/T4.7 (evidencia de integración) y T4.8 (revisión renderizada); T4.2/T4.3 proporcionan los contratos asentados de documento/consulta. Los tokens compartidos, puntos de quiebre y diseños no afectados permanecen sin cambios. Acción requerida: aprobación del propietario de este borrador junto con el plan, copia idéntica byte por byte por T4.1, luego implementación y revisión independiente de T4.8 para las variantes de todo el personal y de rol personalizado de solo lectura. Esta delegación no autoriza cambios separados a CHANGELOG o PLAN; este registro contiene la evaluación de impacto requerida para el borrador. No promuevas este borrador a aprobado.

## 2. Propósito y usuarios

| Vista | Usuario / objetivo | Éxito observable |
|---|---|---|
| V1 Mis proyectos | Una cuenta con sesión iniciada y acceso a sus propios proyectos encuentra trabajos guardados | Abre el proyecto del servidor elegido y continúa la misma escena en otro navegador |
| V2 Todos los proyectos | Un empleado/administrador, o un rol personalizado con el permiso correspondiente, encuentra el proyecto de otra cuenta | El propietario aparece claramente en cada fila/tarjeta y el proyecto seleccionado se abre sin cambiar de propietario |
| V3 Proyecto propio en Taller | El propietario autorizado guarda y continúa el trabajo | La confirmación del servidor identifica el proyecto guardado y la hora; los errores nunca se muestran como guardados |
| V4 Proyecto de otro propietario, solo lectura | El personal autorizado inspecciona trabajos guardados | El propietario y el modo de visualización permanecen visibles; el original ajeno es de solo lectura y una copia personal requiere `taller.usar` |
| V5 Revisión de importación del navegador | Una persona con sesión iniciada decide si una escena local le pertenece | La importación explícita crea un proyecto del servidor propiedad de la cuenta; los datos originales del navegador se conservan en todos los casos |

Cada pantalla plantea una pregunta y tiene una tarea principal; estas decisiones determinan su bloque de mayor tamaño y su acción principal:

| Pantalla | Una pregunta | Tarea principal / respuesta visual |
|---|---|---|
| V1 | “¿Qué proyecto de decoración quiero continuar?” | Encontrar y abrir una escena guardada en la cuadrícula de proyectos; “Nuevo proyecto” es la única acción con color. |
| V2 | “¿El proyecto de quién estoy buscando?” | Buscar/filtrar proyectos autorizados con el propietario visible en cada tarjeta de nivel equivalente. |
| V3 | “¿Se guardaron los cambios de mi escena en mi cuenta?” | Continuar la escena con un estado de guardado veraz y persistente junto a la acción para guardar. |
| V4 / V4b | “¿De quién es esta escena y qué puedo hacer con ella?” | Inspeccionar el original en solo lectura; solo las cuentas habilitadas pueden crear una copia personal. |
| V5 | “¿Esta escena del navegador es mía y qué cuenta la recibirá?” | Revisar el origen y el destino y luego aceptar explícitamente la importación. |
| D1 | “¿Cómo se llamará este proyecto en mi cuenta?” | Asignarle un nombre y guardarlo, con la cuenta de destino visible. |
| D2 | “¿Cómo conservo mi trabajo si se guardó otra versión?” | Comparar dos filas de versiones claramente etiquetadas y elegir una resolución segura. |
| D3 | “¿Cómo puedo salir sin perder estos cambios?” | Guardar, conservar un borrador local asociado a la cuenta o quedarse; las opciones deshabilitadas explican el motivo. |

V4b es la misma vista de proyecto en solo lectura para un rol personalizado con `proyectos.ver_todos` pero sin `taller.usar`: sin navegación de Taller, acciones sobre proyectos propios ni acción para copiar.

R6 corresponde a V1–V4 (incluida V4b), F1–F4 y UI-AC-01–15. R7 corresponde a V1/V5, F5 y UI-AC-16–19. La concurrencia corresponde a D2/F3; los cambios de permisos, a S8/F4. Los nombres, nombres de cuenta y fechas de la maqueta son fixtures ficticios.

## 3. Arquitectura de información y jerarquía

Biblioteca de proyectos: estructura compartida de Pictures → navegación de secciones → título y una acción principal (“Nuevo proyecto”) → aviso opcional de importación del navegador → búsqueda por nombre (y filtro por propietario en V2) → cantidad/orden de resultados → proyectos. Cada proyecto muestra una ilustración no esencial de la escena, el nombre, la hora del último guardado en el servidor, el propietario en V2 y “Abrir proyecto”. Primero el guardado más reciente (`updatedAt DESC`, luego `id DESC`); no se muestran métricas comerciales ni precios sin respaldo. Si falta una miniatura, se usa un marcador neutral de escena; esto nunca impide abrir el proyecto. No se implica el uso de IA para generar miniaturas.

Taller: volver a la biblioteca → nombre y propietario/modo del proyecto → estado de guardado veraz → “Guardar proyecto” / “Guardar ahora” → espacio de trabajo existente. Los objetos, las dimensiones y la ubicación de la escena son el trabajo; no se agrega un panel de proyectos. “Guardar decoración” corresponde a SP-5 y debe conservar una etiqueta claramente distinta; no puede servir como acción para guardar el proyecto. Los metadatos del proyecto se mantienen fuera del lienzo 3D y están disponibles para tecnologías de asistencia.

Revisión de importación: procedencia (“Solo en este navegador”) → cuenta de destino con sesión iniciada → nombre de la escena local y resultado de validación → casilla explícita de propiedad → acción de importación → resultado y recuperación. Nunca se debe sugerir que una escena en un navegador compartido necesariamente pertenece a la cuenta actual.

No se incorporan eliminación, uso compartido, carpetas, colaboración, explorador del historial de proyectos, publicación global ni acciones en lote. Se mantiene la edición de nombres existente dentro de la escena; no se agrega un flujo de cambio de nombre independiente.

## 4. Design system and visual language

Read-only evidence: `t12` HEAD `fb872bce` and `pictures`/asesor HEAD `fa101a47`, `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/{Taller3D.tsx,ui-taller.ts,DialogoTaller.tsx,guardado-escena.ts,archivo-escena.ts}` and shared `src/components/ui/shell/CabeceraApp.tsx`. Both repositories use the same semantic palette. Existing product design takes precedence over desktop preferences. The accounts draft `cuentas-admin@v1` is a consistency reference, not an approved dependency.

| Existing token | Light | Dark | Role |
|---|---|---|---|
| `--fondo`, `--superficie` | #faf9fc / #ffffff | #0b0c10 / #16181f | canvas, panels |
| `--superficie-suave`, `--superficie-2` | #faf8fd / #efe9f8 | #1c1e26 / #242733 | inset areas, secondary fill |
| `--texto`, `--texto-suave`, `--texto-tenue` | #1c1425 / #6b6178 / #766c85 | #f4f5f7 / #9aa1ad / #8a91a0 | text hierarchy |
| `--borde`, `--borde-suave` | #e3daef / #efe9f8 | #383c48 / #2a2d38 | panel borders, dividers |
| `--acento`, `--acento-hover`, `--acento-suave` | #6d3fe0 / #5530b8 / #ece3fb | #9479ff / #a58dff / #241f3d | actions, hover, selection |
| `--sobre-acento` | #ffffff | #120b24 | text on primary; do not use white in dark library buttons |
| `--exito`, `--exito-suave` | #1f7a55 / #dcf5e9 | #78d6a8 / #173b31 | acknowledged save/import |
| `--error`, `--error-suave` | #b23a45 / #ffeaec | #ff979f / #43252a | error |
| `--aviso`, `--aviso-suave` | #8f5f12 / #fff3d8 | #f7c46b / #3f311c | unsaved, offline, conflict |
| `--overlay` | rgb(28 20 37 / .4) | rgb(0 0 0 / .6) | modal backdrop |

The production source remains read-only. Production typography remains Geist sans (`--font-sans`, `--font-geist-sans`); the offline mockup uses the kit's system sans fallback, with mono only for identifiers. Existing `.taller-3d` scoped `--taller-*` tokens and `DialogoTaller` semantics remain production references; this static contract does not rewrite the 3D editor or shared components.

The planning HTML starts from `kit/templates/mockup.html`, keeps `.mockup-bar`, its labelled native view/state/scene/theme selects and “Mockup” label, and inlines the current `tokens.css`, `components.css` and `kit.js` using the kit's `inline.py`. A single project style block follows the kit. It maps the following semantic roles; components retain their kit anatomy, padding and state rules.

| Kit role | Existing Pictures source / mapping | Reason |
|---|---|---|
| `--background`, `--foreground` | `--fondo`, `--texto` | Canvas and primary text |
| `--card`, `--popover`, corresponding foregrounds | `--superficie`, `--texto` | Working surfaces and floating layers |
| `--primary`, `--primary-hover`, `--primary-foreground`, `--ring` | `--acento`, `--acento-hover`, `--sobre-acento`, `--acento` | One primary action; dark primary uses dark text, never white |
| `--secondary`, `--muted`, `--accent` | `--superficie-2` | Neutral secondary fill and selection; accent here is a kit interaction role, not Pictures' brand-accent token |
| `--secondary-foreground`, `--accent-foreground` | `--texto` | Neutral readable actions and navigation |
| `--muted-foreground` | `--texto-suave` | Supporting text, including dark mode |
| `--border` | `--borde` | Decorative separation, not a control-identification edge |
| `--input` | proposed control-border alias to `--texto-tenue`: light #766c85; dark #8a91a0 | ≥3:1 meaningful control edge; the source decorative border alone cannot identify a control |
| `--success`, `--warning`, `--destructive` | `--exito`, `--aviso`, `--error` | State text with an explicit status word |
| `--info` | `--acento` | Informational status |
| `--primary-soft`, `--success-soft`, `--warning-soft`, `--destructive-soft`, `--info-soft` | `--fondo` | Neutral notices/groups preserved from previous owner feedback |
| `--destructive-foreground` | light #ffffff; dark #3a0f13, as in source | Text on error actions; destructive hover retains the same measured fill |
| `--sidebar`, `--sidebar-foreground`, `--sidebar-accent`, `--sidebar-accent-foreground`, `--sidebar-border`, `--sidebar-ring` | `--fondo`, `--texto`, `--superficie-2`, `--texto`, `--borde`, `--acento` | Quiet navigation; active item has a neutral fill |
| `--radius`, `--spacing` | .8rem; kit .25rem spacing unit | Existing Pictures radius; 4px rhythm |
| `--control-h`, `--control-h-sm`, `--control-h-lg` | proposed 2.75rem for project actions | Preserve the existing contract's 44px targets at every width |

Use the kit typography hierarchy: H1 24px/1.25; H2 20px/1.3; card title 16px; body 14px/1.5; metadata 12px. Sentence case, no tracked uppercase headings. Save figures use tabular numerals. Gaps come from `.stack-sm` (8px), `.row` (12px), `.stack`/`.grid` (16px), `.stack-lg` (24px), `.stack-xl` (32px). Card content/header/footer padding is 24px, 20px at phone widths; default control height is token-mapped to 44px. Kit borders, rather than shadows, frame nonfloating cards; floating dialogs/menus/toasts keep kit shadows. No bespoke margins or component skins. Inline SVG icons supplement labels and are hidden from AT.

Component inventory (catalog names and exact snippet examples):

| Name · variant / state | Snippet | Use |
|---|---|---|
| Sidebar · state=expanded · parts=header/group/menu-button | `kit/components/sidebar.html#expanded` | Desktop shell; neutral current item |
| Button · variant=default/outline/ghost · state=normal/disabled/loading/focus-visible | `kit/components/button.html#variants`, `#states` | One primary per active view/dialog, secondary actions outlined, supporting actions ghost |
| Card · parts=header/title/description/content/footer · size=default | `kit/components/card.html#actions` | Peer project cards; scene preview within padded content |
| Field · orientation=vertical · state=default/error; Input · type=text/search | `kit/components/field.html#vertical`, `kit/components/input.html#types` | Search and project name; associated error and description |
| Select · native · state=default | `kit/components/select.html#native` | Owner filter and planning toolbar |
| Checkbox · state=unchecked/checked/disabled | `kit/components/checkbox.html#list`, `#states` | Explicit ownership consent; `.choice` label and `.checkbox` input, never an unstyled native square |
| Badge · variant=secondary/success/warning/destructive | `kit/components/badge.html#variants` | Read-only/save state, with words |
| Alert · variant=default/success/warning/destructive · action | `kit/components/alert.html#variants` | Import offer, save/recovery/error feedback; neutral mapped fills |
| Empty · variant=default · parts=title/description/content | `kit/components/empty.html#no-results` | Empty/no-match/denied states, no decorative media tile |
| Skeleton · shape=line | `kit/components/skeleton.html#card` | Loading content; no false empty result |
| Dialog · size=default · parts=header/title/description/footer/close | `kit/components/dialog.html#open` | D1–D3 within a native modal host for focus/inertness |
| DropdownMenu · item variant=default; Avatar · tone=muted | `kit/components/dropdown-menu.html#trigger`, `kit/components/avatar.html#media` | Shared account entry, fictional account identity |
| Toast · type=info · parts=title/description | `kit/components/toast.html#stack` | Explicitly labelled mockup action results |

**Proposals outside the kit:** `project-shell/rail/tabs` adapts app layout to the established 200px desktop rail and visible wrapping navigation below 1024px; `project-grid` preserves three/two/one project columns; `project-filters/source/workspace` lays out project-specific content at the existing breakpoints; `project-modal` is a transparent native-dialog host around the unchanged Dialog snippet; `scene-preview` is a noninteractive SVG illustration with role-token fills, clearly labelled “Escena ilustrativa”. These proposals add layout/illustration semantics, not replacements for kit controls. Reflow adapters may allow long status text and action labels to wrap where fixed kit sizing would clip them; such adaptations must retain role colors, padding, focus and 44px targets. Illustrations convey no saved-state truth and are not a 3D round-trip claim. Actual object colors remain scene data, not these illustrative role colors.

The scene-led recognition from the earlier draft remains the distinctive emphasis; there are no KPIs or decorative dashboard widgets. Import destination, source, consent, actions and retention/download footnote share the same readable column and left axis. Default notices, account avatar and navigation use neutral tokens. Focus uses the kit's 2px `--ring` outline with 2px offset. Keep the template's subtle/natural/expressive motion selector and reduced-motion support; project transitions answer interactions only. The kit loading skeleton uses its standard pulse; reduced motion removes it. No decorative scene animation.

## 5. Modelo de navegación e interacción

Las rutas de biblioteca y de enlaces profundos editables siguen T4.4; los demás destinos de consulta/diálogo describen el enrutamiento de interfaz dentro de esa superficie. Las claves de permisos y los contratos de API corresponden a las tareas de SP-1/SP-4.

| Vista / diálogo | Destino / punto de entrada propuesto | Salida |
|---|---|---|
| V1 | `/proyectos`, navegación “Mis proyectos”, Taller “Mis proyectos” | Abrir → V3; Nuevo → V3 sin guardar; revisar escena local → V5 |
| V2 | `/proyectos?ambito=todos`, “Todos los proyectos” filtrado por permisos | Abrir uno propio → V3, uno de otro propietario → V4; “Mis proyectos” → V1 |
| V3 | `/3d?proyecto=<id>` o `/3d` para una escena nueva sin guardar | Biblioteca, acción de crear/abrir y navegación pasan por la protección F4 ante cambios sin guardar |
| V4 / V4b | `/proyectos/<id>` | Página autorizada de solo lectura; permitir copiar solo si también está concedido `taller.usar`; nunca omitir el permiso de `/3d` |
| V5 | `/proyectos?importar=navegador`, aviso después del primer inicio de sesión y enlace persistente a la escena local | “Ahora no” → V1; “Abrir proyecto” tras completar correctamente → V3 |
| D1 Guardar primer proyecto / copiar | “Guardar proyecto” para una escena nueva o “Guardar una copia” | Enviar → éxito en V3; Cancelar/Escape vuelve al espacio de trabajo sin cambios |
| D2 Conflicto al guardar | El guardado recibe una revisión más reciente del servidor | “Guardar una copia” → D1; “Abrir versión guardada” → D3 si hay cambios sin guardar; “Seguir aquí” conserva el trabajo local sin guardar |
| D3 Salida con cambios sin guardar | Abrir otro proyecto, crear uno nuevo o salir de la biblioteca con una escena modificada | “Guardar y continuar”, “Conservar borrador y salir”, “Seguir aquí” |

El menú de cuenta compartido y el control de tema siguen SP-2 y el shell existente. No crees aquí pantallas separadas de inicio de sesión, cuenta, catálogo ni decoración. El mockup marca estos destinos como externos a SP-4 cuando se activan; la navegación real del producto utiliza sus rutas existentes. Si no hay acceso a los proyectos propios, se oculta la navegación de proyectos; las solicitudes directas siguen devolviendo una respuesta de permiso denegado. Los datos de la lista y los filtros por propietario provienen únicamente de resultados autorizados, nunca del filtrado en el cliente de los registros de todas las personas.

Enter envía los formularios de guardado; la búsqueda se aplica después de una breve demora y Enter la aplica de inmediato. La búsqueda filtra los nombres de proyecto de **toda la colección autorizada en el servidor**, antes de la paginación. El filtro de propietario de V2 es independiente y comienza en “Todas las cuentas”; conserva ambos filtros al abrir un proyecto o volver desde él. T4.3 acepta `q` (subcadena literal del nombre, recortada, de hasta 120 caracteres; `%` y `_` son caracteres literales), `scope=mine|all` (predeterminado `mine`) y `ownerId` (UUID, solo con `all` autorizado). Nunca envíes `ownerId` desde V1. `all` requiere `proyectos.ver_todos`. Las opciones de propietario provienen únicamente de los metadatos autorizados de propietarios de proyectos en toda la colección permitida, incluidos los propietarios cuyos resultados estén fuera de la página actual; nunca enumeres cuentas no relacionadas ni derives las opciones solo de la página cargada. No interpretes la interfaz como un directorio global de cuentas.

El servidor devuelve solo metadatos, hasta 50 filas, ordenadas por `updatedAt DESC` y luego `id DESC`. Un cursor opaco validado está vinculado a `scope/q/ownerId` normalizados; una discordancia entre el cursor y los filtros devuelve 400. Ante cualquier cambio de nombre/propietario/ámbito/cuenta: invalida de inmediato las identidades de solicitudes anteriores (antes de la demora), restablece las filas y el cursor, y luego solicita la primera página de la nueva consulta normalizada. Conserva los filtros ingresados y muestra S23 en la región de resultados; las filas de la consulta anterior nunca deben presentarse como resultados actuales. Las respuestas solo pueden actualizar la interfaz si corresponden a la cuenta, los filtros normalizados y la generación de solicitud actuales. Una respuesta obsoleta no genera ningún cambio visible en el estado/título/filas ni muestra notificaciones. Al borrar los filtros, se inicia una nueva solicitud de la primera página. Si el cursor no coincide, muestra “La lista cambió. Vuelve a cargarla.” / “Recargar lista”, vuelve a empezar en la primera página y nunca repite el cursor rechazado.

Muestra un conteo de elementos **cargados** (“50 proyectos cargados”), no un total inventado, y “Cargar más proyectos” solo mientras exista un cursor siguiente. Mientras se carga la página siguiente, conserva las filas de la consulta actual, anuncia “Cargando más proyectos…” y deshabilita la paginación repetida. Si falla la carga de la página siguiente, conserva las filas, los filtros y el cursor reintentable con “Reintentar carga”; al reintentar, agrega resultados sin duplicados. Cuando cambia la consulta, se descartan esas filas y ese cursor anteriores. Nunca cargues documentos completos de escenas para filtrar ni afirmes que una página cargada representa toda la biblioteca. F6/S13/S23–S26 y UI-AC-41–51 rigen estas transiciones.

## 6. Flujos

**F1 — Primer guardado y continuación (R6; ronda 9 del propietario, q5).** 1) La escena nueva muestra “Sin guardar en tu cuenta”. 2) “Guardar proyecto” abre D1 con el nombre de escena existente. 3) Se requiere un nombre sin espacios al inicio ni al final, de 1–120 caracteres (el mismo límite que el campo de nombre existente de Taller); los nombres visibles duplicados no identifican un proyecto ni lo reemplazan. 4) “Guardar en mi cuenta” deshabilita los envíos repetidos mientras hay uno pendiente. 5) Solo el éxito confirmado del servidor muestra “Guardado en tu cuenta · 26 oct, 14:32” y una identidad de proyecto persistente. Si falla, se conservan la escena y el nombre y se ofrece reintentar; si el resultado es desconocido, se concilia antes de reintentar, sin duplicar a ciegas. 6) Después del primer guardado con nombre: serializar los guardados automáticos en la cuenta 500 ms después de la última edición y mantener disponible “Guardar ahora”; mostrar “Cambios sin guardar” hasta que se confirme la generación de edición correspondiente. Mantener una solicitud en curso y poner en cola detrás de ella la escena más reciente. Una respuesta anterior nunca borra cambios pendientes más recientes: mientras una generación enviada está pendiente, las ediciones posteriores muestran “Guardando cambios anteriores · hay cambios nuevos sin guardar”, siguen permitiendo la edición y esperan detrás de esa solicitud. Cada respuesta está vinculada a la cuenta, el proyecto y la identidad de la solicitud. Después de cambiar de proyecto, una finalización anterior no debe modificar el título actual, el lienzo, el estado de cambios sin guardar, la revisión, la identidad de la conversación ni el historial de deshacer. No se muestra una notificación de éxito del producto para un proyecto que ya no está activo; la conciliación de la solicitud anterior permanece dentro de ese proyecto. F4 rige la salida incluso si solo quedan ediciones pendientes. El propietario confirmó el primer guardado explícito con nombre, seguido del guardado automático y un estado visible; 500 ms es el valor técnico predeterminado del Planner, no un plazo especificado por el propietario. La maqueta estática fija estos estados para su inspección; su selector de estado simula el estado pendiente o el éxito en vez de ejecutar un temporizador de carga en segundo plano.

**F2 — Volver a abrir (R6).** 1) Entrar en V1 o en V2 con autorización. 2) Buscar o filtrar; abrir un proyecto específico con nombre. 3) Si la escena actual tiene cambios sin guardar, resolver F4 primero. 4) Mostrar la carga del proyecto y luego reemplazar el espacio de trabajo solo cuando la validación y la carga de datos hayan finalizado correctamente. 5) Restaurar el nombre y la escena completa, incluidos la habitación, el entorno, el salón, los materiales, las relaciones entre nodos de escena, las ubicaciones, las dimensiones, los colores y todos los campos y referencias válidos, sin convertir ni eliminar silenciosamente datos no compatibles. Si falla, el espacio de trabajo anterior permanece intacto y se explica si es posible reintentar; no se recurre a una escena vacía como alternativa de éxito. Restablecer la pila de deshacer y la identidad de conversación de la escena en el límite del proyecto que se abrió correctamente; nunca mostrar el hilo de IA del proyecto anterior en el nuevo. La conversación de IA y las imágenes generadas, que se almacenan por separado, permanecen locales y no se garantiza que estén disponibles en otro navegador. Conservar los datos locales existentes; las referencias a nodos de escena forman parte de la escena, incluso cuando hacen referencia a contenido multimedia. No se puede descartar ningún campo o referencia válido para mantener el límite separado de los datos de IA.

**F3 — Guardado simultáneo (caso límite de R6).** 1) Otra sesión modifica el proyecto después de que esta sesión lo leyó. 2) El guardado rechaza una revisión obsoleta; D2 indica “Hay una versión más reciente” y muestra la fecha del último guardado del servidor y el autor solo cuando esos datos se devuelven con autorización. 3) Conservar el trabajo local y la escena más reciente del servidor. 4) Detener la cola de guardado automático ante un 409 hasta que haya una resolución explícita. Recuperación: guardar el trabajo local como un proyecto nuevo o abrir explícitamente la versión más reciente mediante D3. No hay acciones para sobrescribir o forzar el guardado ni combinación automática de campos. Se requiere una comprobación de comparación y guardado en el servidor; el modal por sí solo no puede garantizar la seguridad frente a cambios simultáneos.

**F4 — Salida o cambio de permisos.** 1) Una escena local con cambios sin guardar o un guardado en curso sin confirmar activa D3 antes de reemplazar contenido o navegar dentro de la aplicación. 2) Guardar y continuar reanuda la acción prevista solo después de que el éxito se confirme; un conflicto o fallo cancela la salida y conserva el trabajo local. 3) “Conservar borrador y salir” retiene la escena no enviada como borrador local de recuperación, vinculado a la cuenta y al proyecto (las escenas nuevas sin guardar usan una identidad temporal separada), no cambia ninguna revisión del servidor y luego continúa; nunca elimina la fuente de importación heredada. Al volver con la misma cuenta, ofrecer “Recuperar borrador” antes de reemplazar los datos guardados y conciliar su revisión base. Otras cuentas no pueden enumerarlo ni abrirlo. Si el almacenamiento del navegador está lleno o bloqueado, mostrar “No pudimos conservar el borrador en este navegador”; permanecer en el proyecto actual y retener la escena en memoria. La salida conservando el borrador solo se completa cuando este se ha guardado localmente y nunca presenta el estado del servidor como guardado. 4) Al cerrar toda la pestaña, usar el aviso nativo del navegador sobre cambios sin guardar cuando esté disponible, sin prometer texto personalizado fiable ni persistencia garantizada. 5) Una sesión revocada lleva al inicio de sesión de SP-2 con una ruta de retorno segura; si se elimina el permiso para el recurso, se muestra S8 sin metadatos del propietario ni del título y no se deben reintentar escrituras ni copiar datos de la cuenta a otra cuenta con sesión iniciada. Borrar el estado visible de la escena y las cachés de consultas al cerrar sesión o perder la autenticación, ignorar las finalizaciones de identidades anteriores y ofrecer la recuperación retenida solo a la misma cuenta. Estos son límites de T4.4; la frecuencia de guardado automático aprobada no concede permiso para divulgar borradores.

**F5 — Importación desde el navegador (R7).** 1) Detectar `taller3d:escena:v1` sin procesar después del primer inicio de sesión, sin modificarlo; la evidencia del repositorio muestra una escena actual, no una biblioteca de proyectos del navegador inventada. 2) Ofrecer la opción solo en la primera visita autenticada a Taller si hay datos locales (T4.5), no dentro del controlador de inicio de sesión. Una cuenta sin acceso a Taller conserva la fuente hasta que se le conceda acceso. Ofrecer “Hay una escena en este navegador” / “Revisar importación”; no asignarla automáticamente. 3) V5 muestra la cuenta de destino con sesión iniciada, el nombre de la escena local cuando se pueda leer de forma segura y una casilla sin marcar: “Esta escena es mía y quiero guardarla en esta cuenta”. 4) “Importar a mi cuenta” se habilita solo después de la confirmación y si los datos son válidos y compatibles; la importación es explícita. 5) Conservar la fuente heredada sin procesar antes de que cualquier guardado automático normal de Taller pueda reemplazarla; la detección de solo lectura no debe llamar al cargador normal, que normaliza o descarta contenido mal formado. 6) La confirmación del servidor crea un proyecto nuevo y un recibo de importación por cuenta y fuente; si se revisa de nuevo, se muestra el resultado existente en vez de duplicarlo. 7) “Ahora no” pospone la acción sin ocultar la entrada persistente para revisarla; la fuente nunca se elimina después del éxito. 8) La fuente incompatible o dañada permanece local, con un motivo veraz y la opción “Descargar copia original” (JSON sin procesar; no se afirma que pueda abrirse). No se sustituye por un proyecto vacío. El texto explica: “Se guardan el nombre y la escena completa. La conversación y las imágenes de IA siguen en este navegador.” Esto excluye únicamente los datos de IA almacenados por separado, no los campos ni las referencias válidos de la escena.

**F6 — Buscar y paginar (R6; resolución del Planner para Q4).** 1) Abrir V1 o V2 con autorización y las primeras ≤50 filas de metadatos. 2) Escribir un nombre literal y, opcionalmente, seleccionar un propietario autorizado en V2; restablecer la paginación y mostrar S23 mientras se consulta toda la colección autorizada. 3) Mostrar las coincidencias devueltas aunque estén después de la fila 50 de la lista sin filtrar; cuando no hay resultados, S14 representa una consulta exitosa sin coincidencias, no una cuenta vacía. 4) Cargar más solo con el cursor vinculado al filtro actual (S25). 5) Si falla una página, conservar las filas y permitir reintentar (S13); un cambio de filtro invalida el cursor fallido. 6) Una consulta obsoleta y lenta no debe reemplazar las filas ni los filtros actuales; S24 es una prueba de inspección para este rechazo, que de otro modo sería silencioso. La maqueta simula el servidor sobre una colección en memoria con más de 50 proyectos de prueba propios, páginas de 50 filas y aplicación de consultas vinculada a una generación; no realiza solicitudes de red ni constituye evidencia de la API.

## 7. View specifications

**V1 — Mis proyectos.** H1 “Mis proyectos”; lead “Retoma tu trabajo desde cualquier navegador.”; primary “Nuevo proyecto” when `taller.usar` is granted. Optional import notice precedes search. Labelled input “Buscar proyecto”, count “50 proyectos cargados” for a full first page, sort text “Guardados más recientes primero”. Cards: “Quince años · Valentina”, “Boda · Jardín Botánico”, “Lanzamiento · Coral”; timestamp “Guardado el 26 oct 2026, 14:32”; visible button “Abrir proyecto” with accessible name including title. A cursor shows “Cargar más proyectos”; S13 covers next-page failure with previously loaded results retained. Illustrations are optional/decorative. Empty uses “Aún no tienes proyectos guardados” / “Crea un proyecto en el Taller 3D y guárdalo en tu cuenta.” / “Nuevo proyecto”. Zero search results differ: “No encontramos ese proyecto” / “Limpiar filtros”. F1/F2/F5; S1–S5/S8/S10/S13/S14/S23–S26.

Components: Sidebar · expanded; Card · default (`card.html#actions`); Input · search / Field · vertical; Button · default/outline; Alert · default; Empty · default; Skeleton · line.


**V2 — Todos los proyectos.** H1 “Todos los proyectos”; support “Consulta los proyectos guardados de cada cuenta.”; same structure as V1 plus owner filter and visible owner per card (“Lucía Torres · Eventos Lila”, “Mateo Ruiz · Montajes Norte”). Fixture account in this view is an employee, not an ordinary user with an exposed role toggle. Only V2 and V4 present staff identity in the mockup. No create-on-behalf action or ownership transfer. F2/F4; S1–S5/S8/S10/S13/S14/S23–S26.

Components: the V1 list plus Select · native (`select.html#native`) and Card description for explicit owner metadata.


**V3 — Project workspace.** Library link, project title, textual account-save status and save action stay visible outside the canvas. Show saved time, not relative-only “hace poco”; dates use active locale and labelled local timezone if an exact comparison is shown. Main region is existing Taller canvas, scene tree and inspector; mockup intentionally represents them as labelled illustration/context, not a functional 3D engine. “Simular edición” is a mockup-only control. New project starts with “Proyecto sin título”, never appears in V1 before server success. Save action is disabled with a nearby reason when unchanged, loading or pending. F1–F4; S1/S2/S4–S12.

Components: Button · default/outline/ghost; Badge · success/warning; Alert · default/success/warning/destructive; proposal `project-workspace` / `scene-preview`.


**V4 — Read-only foreign project view (owner round 9 q7).** Separate `/proyectos/<id>` read-only scene page with persistent “Proyecto de Mateo Ruiz” and “Solo lectura”. No editable scene controls or update-original action. “Guardar una copia en mi cuenta” opens D1 and explicitly changes destination ownership to the current account; copy requires `taller.usar` and creates a new project owned by the signed-in account; it never updates or transfers the original. Copy stays disabled while loading, after a read error or offline, with the corresponding loading/error/connectivity reason visible. V4b omits the copy button and Taller/own-project navigation when `taller.usar` is absent, while retaining account menu, owner and “Todos los proyectos”. F2/F4; S1/S2/S4/S6/S8/S10/S17. Loading and failure describe reading, never saving; no account-save success banner appears on a foreign original. Never imply that opening grants write permission.

Components: Badge · secondary; Button · default/disabled (copy where permitted); Alert · default; proposal read-only `project-workspace` / `scene-preview`. V4b has no copy control.


**V5 — Revisar importación.** H1 “Trae tu escena a tu cuenta”; subtitle “La encontramos en este navegador. Revisa que sea tuya antes de importarla.” Show destination “Lucía Torres · lucia@example.test”, source “Este navegador”, scene name and status. Checkbox from F5; primary “Importar a mi cuenta”; secondary “Ahora no”; recovery “Descargar copia original”. Success shows “Escena importada a tu cuenta”, confirmed project name and “Abrir proyecto”; source-retention message remains. Already imported source shows “Esta escena ya está en tu cuenta” and opens the previously confirmed project. F5; S1–S8/S10/S11/S16/S21. “Esta escena ya está en tu cuenta” is distinct from a newly acknowledged import; its receipt belongs to the currently signed-in account. Another account gets a fresh unchecked consent, never the prior project association.

Components: Checkbox · unchecked/checked/disabled (`checkbox.html#list`); Button · default/outline/ghost; Badge · secondary; Alert · success/destructive; proposal `project-source`.


**D1 — Guardar proyecto / Guardar una copia.** Native modal with heading, “Nombre del proyecto”, 120-character limit, destination account, “Cancelar” and “Guardar en mi cuenta”. Copy starts with “[original name] · copia”. Inline blank-name message “Escribe un nombre para el proyecto.”; keep user input on failure. Pending says “Guardando…” and prevents repeated submits. Close/Escape during a pending request does not claim cancellation of an operation already sent; background result must still reconcile. No form nested inside another form.

Components: Dialog · default (`dialog.html#open`); Field · vertical / Input · text, default/error; Button · default/outline, normal/pending/disabled; native-modal host proposal.


**D2 — Hay una versión más reciente.** Explain “Otra sesión guardó cambios después de que abriste este proyecto. Tu trabajo sigue aquí.” Show two labelled rows: “Tu trabajo · sin guardar” and “En tu cuenta · 26 oct 2026, 14:36”. Actions “Guardar una copia”, “Abrir versión guardada”, “Seguir aquí”. No ambiguous “Aceptar”, destructive default, automatic reload or forced overwrite. First focus is heading.

Components: Dialog · default; Separator and Row for two version groups; Button · default/outline; no nested Card.


**D3 — Tienes cambios sin guardar.** Explain that a retained local draft is visible only to this account on this browser; buttons “Guardar y continuar” (primary), “Conservar borrador y salir” (secondary), “Seguir aquí” (secondary, initial focus). A failed/pending/conflicted save cannot complete the intended departure. When “Guardar y continuar” is disabled, D3 itself explains the pending acknowledgment, unknown result or offline condition; do not rely on a status hidden behind the modal. Closing/Escape equals “Seguir aquí”.

Components: Dialog · default; Button · default/outline, disabled where required; Alert · destructive for failed local backup.


## 8. States

The mockup exposes native selects `view`, `state`, `scene`, `theme` with visible labels “Vista”, “Estado”, “Diálogo”, “Tema”. Views are V1–V5 plus permission variant V4b (`foreign-limited`). Scene values are `none`, `save`, `copy` (D1 copy variant), `conflict`, `leave`. Inapplicable inspection combinations normalize to the applicable view; they must never turn a read-only original into an editable project. Theme values are `light`, `dark`. The template additionally keeps `motion` (subtle/natural/expressive). Kit `data-show-view/state/scene` bindings govern the generated view frame, loading regions and dialog contents. Local JavaScript supplies fixture queries, account/query-generation isolation, dependent-selector normalization and native modal transitions that simple visibility switches cannot express. State values below are exact integration vocabulary. Selecting a state with a specific context takes the mockup to that context; this is planning navigation, not a product state transition.

| ID / switch value | Applies | Visible result and recovery |
|---|---|---|
| S1 `ready` | all | Loaded library/workspace; reviewable local source. Product actions enabled according to permission/dirty state |
| S2 `loading` | all | Skeleton plus “Cargando proyectos…” / “Abriendo proyecto…” / “Revisando escena…”; `aria-busy`; do not render an empty success or activate writes |
| S3 `empty` | V1/V2/V5 | True library empty state, or “No hay escenas para importar en este navegador”; useful return/create action. Selector moves editor to V1 |
| S4 `error` | all / D1 | “No pudimos cargar los proyectos” or “No pudimos guardar el proyecto”; inline reason, “Reintentar”; preserve existing scene and form. Failed reopen does not replace scene |
| S5 `success` | V1/V2/V3/V5 | Confirmed save/import message with title and time; no fake confirmation before response. Opening itself is a loaded state, not a save success |
| S6 `disabled` | V3/V4/V5 | Unchanged own scene (“No hay cambios para guardar”), foreign read-only, or missing ownership confirmation; reason is visible, not just opacity |
| S7 `validation` | D1 or V5 | Name error in D1, or unsupported/corrupt local source with preserved original; field error announced and associated. Mockup selects V3/D1 by default |
| S8 `permission-denied` | all | “No tienes acceso a estos proyectos” without title/owner/thumbnail; “Volver al inicio” and account navigation; controls cannot bypass guard |
| S9 `stale` | V3 / D2 | Conflicting server revision; both scenes retained; see F3. Selector opens V3/D2 |
| S10 `offline` | all | “Sin conexión. No podemos confirmar el guardado en tu cuenta.” Local editing remains enabled; account writes stay disabled until an explicit retry/reconciliation. Local work stays; list only shows explicitly identified already-loaded data, not a fabricated cache. “Reintentar conexión”; no automatic account queue |
| S11 `pending` | V3/V5/D1 | “Guardando en tu cuenta…” / “Importando…”; repeated mutation disabled. Timeout with unknown result says “No pudimos confirmar el resultado”; reconcile before resubmission. Mockup selects V3 |
| S12 `dirty` | V3 / D3 | “Cambios sin guardar”; save enabled; leave requires D3. Local backup success must not change this label |
| S13 `partial` | V1/V2 | The next page failed; previously loaded projects remain, with loaded count, reason and “Reintentar carga”. Cursor retry does not repeat existing rows. Selector opens V1 unless already in V2 |
| S14 `no-results` | V1/V2 | Name/owner filters have zero matches; show active filter and “Limpiar filtros”; never offer import as if no projects exist |
| S15 `recovery` | V3 | “Hay un borrador de esta cuenta en este navegador” with “Recuperar borrador”; recovery marks dirty and checks the stored base revision before writing. Selector opens V3 |
| S16 `unknown` | V3/V5/D1 | “No pudimos confirmar el resultado”; preserve local work, disable a new mutation and offer “Comprobar guardado” to reconcile the existing mutation/import receipt before retry. Selector opens V3 unless already in V5 |
| S17 `unavailable` | V3/V4/V4b | “Proyecto no disponible”; inaccessible and missing items share this 404 presentation, without title, owner or thumbnail; return to authorized list |
| S18 `too-large` | V3/D1 | “El proyecto supera el límite de 2 MiB”; unsent scene/name retained, never retry unchanged automatically; return to editing before another save |
| S19 `draft-error` | V3/D3 | “No pudimos conservar el borrador en este navegador”; keep current work visible and remain here; “Reintentar respaldo” retries only local persistence and completes the stored departure only if it succeeds |
| S20 `late-response` | V3 | Inspection fixture: after switching from Valentina to Boda, an obsolete Valentina completion leaves Boda’s title/scene and “Cambios sin guardar” unchanged. Explanation is mockup-only; product stays quiet |
| S21 `already-imported` | V5 | “Esta escena ya está en tu cuenta”; open the existing receipt-bound project, no second import; original remains; consent and receipt never cross accounts |
| S22 `pending-newer` | V3 | “Guardando cambios anteriores · hay cambios nuevos sin guardar”; save stays disabled while serialized request is in flight, scene editing remains available; older acknowledgment cannot label all edits saved |
| S23 `query-loading` | V1/V2 | Filters remain usable; results region shows “Buscando proyectos…” with `aria-busy`, prior-query rows removed, no empty-result claim; latest query replaces this pending state |
| S24 `query-late-response` | V1/V2 | Inspection fixture: current query “Horizonte” still shows “Ceremonia · Horizonte”, originally beyond unfiltered row 50, after a simulated old “Boda” response; only the mockup explains the ignored response, product remains quiet |
| S25 `page-loading` | V1/V2 | Current rows/count remain, “Cargando más proyectos…” announced and load-more disabled; success appends, failure transitions to S13 |
| S26 `cursor-invalid` | V1/V2 | “La lista cambió. Vuelve a cargarla.” retains visible current-query rows; “Recargar lista” restarts at page one with the same filters, never retries the rejected cursor |

Offline durable upload queue, live multi-user presence, background AI generation status and project deletion states are inapplicable: no such feature is assigned to SP-4. Thumbnails are optional; failure displays a placeholder, never a fatal project error. A malformed scene is an error, never silently dropped into an empty project. Session expiry reuses SP-2, not a new login dialog. A partial state is not used to fabricate a partly loaded scene.

## 9. Responsive behavior

Supported width starts at the product's existing 320px minimum. Content breakpoints align with existing Tailwind `sm` (640), `md` (768), `lg` (1024) and Taller's narrow/landscape behavior. Test 320, 390, 768, 1024 and 1440px, plus 844×390 landscape.

| Range | Library / import | Taller / dialogs |
|---|---|---|
| 320–639px | Compact header, horizontally wrapping section navigation; H1/action stack; labelled filters one column; cards one column, full names wrap; 16px gutters | Save status on its own wrapping row, explicit labelled save action; canvas then contextual scene summary; dialog spans viewport width with a naturally sized, internally scrolling kit Dialog body; all actions remain in normal flow |
| 640–767px | Navigation above content; 24px gutters; two-card grid if available width fits; filters wrap | Dialog centered ≤560px, max-height 92dvh; editor context remains below canvas |
| 768–1023px | Two-card grid, filter search/owner on one line; import readable max-width 760px | Canvas and scene summary fit side by side; header wraps rather than clipping |
| ≥1024px | 200px section nav rail, main max-width 1200px, three-card grid; filters full row | Existing Taller rail and canvas/inspector layout retained; centered dialogs |

At ≤1023px landscape and height ≤540px, prioritize canvas space and put context beside it if content fits; do not force a tall mobile bottom panel. At zoom/reflow 320 CSS px, stack again. No page-wide horizontal scrolling. Long names wrap at safe opportunities; ellipsis is permitted only where full name is otherwise available to touch/keyboard, never only a hover tooltip. Dialog actions wrap; no fixed footer covers content; body has overscroll containment. EN expansion up to roughly 35% is a layout stress case, not a translation guarantee. ES copy is specified here; SP-8/SP-10 wire account language and complete translations. No RTL support is declared by this pilot.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA; la conformidad queda pendiente de la revisión del producto renderizado. Usar regiones de encabezado/navegación/contenido principal, un H1, una lista semántica de proyectos, campos de entrada/selectores con etiquetas, botones/enlaces reales y un enlace para saltar al contenido. Los nombres accesibles de apertura incluyen el nombre del proyecto. La ilustración de la escena usa `aria-hidden`; todos los datos del proyecto/guardado están disponibles en texto. La identidad de la cuenta nunca se comunica solo mediante un avatar/color.

Usar semántica de diálogo modal nativa (o el equivalente accesible existente), con título/descripción etiquetados, foco restringido al diálogo, tecla Escape y retorno del foco al elemento que lo abrió. Para D2 → D1/D3, conservar el elemento de la página original que abrió el diálogo durante la transición; si ese elemento ya no existe después del renderizado, enfocar el control de resolución del conflicto o el encabezado de la vista actual, nunca el cuerpo del documento ni un control oculto del diálogo. Foco inicial: nombre de D1; encabezado de D2; “Seguir aquí” de D3. Al validar, enfocar el primer campo no válido; al completarse la carga de permisos/datos, mover el foco al encabezado de la página solo después de una navegación real. No robar el foco repetidamente al actualizar el estado de guardado. El fondo permanece inerte mientras el diálogo modal está abierto. El estado de guardado usa una región dinámica cortés; los errores que requieren acción usan una alerta una sola vez. Las etiquetas de estados sin conexión/obsoleto/deshabilitado/éxito incluyen palabras además de color.

Todos los nuevos objetivos en los que se puede hacer clic miden ≥44×44 px CSS; los controles angostos existentes de Taller quedan fuera del rediseño de esta maqueta, pero los controles de guardado/biblioteca agregados cumplen ese objetivo. Activación estándar por teclado, orden lógico del DOM y del tabulador, sin acciones de proyecto que dependan solo de arrastrar ni menús que dependan solo de pasar el cursor. Contraste del texto ≥4.5:1 (texto grande ≥3:1); controles/indicadores de foco con significado ≥3:1. Los bordes decorativos de paneles no son indicadores de controles. Mantener el zoom de texto al 200 % y el reajuste al 400 %; ningún foco oculto bajo encabezados fijos. Respetar la preferencia de movimiento reducido. El contraste debe medirse para las combinaciones reales de primer plano/fondo en ambos temas; el nombre de un token no es evidencia. El acceso por teclado al motor 3D pertenece al alcance existente, pero todas las acciones de proyecto agregadas deben poder usarse sin operar su lienzo.

## 11. Criterios de aceptación visual

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | ≥1024px | ready / V1 | The library displays three columns of project cards beside the section rail. |
| UI-AC-02 | 320–639px | ready / V1 | Cards, search and the new-project action fit one column without horizontal page scrolling. |
| UI-AC-03 | 640–1023px | ready / V1 | The project grid has two columns and navigation sits above content. |
| UI-AC-04 | 320–1440px | ready / V2 | Every project card shows its owner as visible text. |
| UI-AC-05 | 320–1440px | no-results | A clear-filters action is shown with the zero-results explanation. |
| UI-AC-06 | 320–1440px | empty / V1 | “Aún no tienes proyectos guardados” appears with “Nuevo proyecto”. |
| UI-AC-07 | 320–1440px | loading | Skeletons and a loading label appear instead of an empty-library success. |
| UI-AC-08 | 320–1440px | dirty / V3 | “Cambios sin guardar” is visible adjacent to the enabled save action outside the canvas. |
| UI-AC-09 | 320–1440px | success / V3 | Account-save confirmation includes the saved time in visible text. |
| UI-AC-10 | 320–1440px | validation / D1 | Submitting a blank name keeps the modal open and associates its error with the name input. |
| UI-AC-11 | 320–1440px | pending / D1 | The submit button reads “Guardando…” and cannot issue a second save. |
| UI-AC-12 | 320–1440px | stale / D2 | Both local-unsaved and server-saved versions are labelled without a force-overwrite action. |
| UI-AC-13 | 320–639px | dirty / D3 | All three departure choices remain reachable through vertical scrolling. |
| UI-AC-14 | 320–1440px | disabled / V4 | Owner and “Solo lectura” are visible and no update-original action is offered. |
| UI-AC-15 | 320–1440px | permission-denied | Restricted project names, owners and thumbnails are absent from the denied view. |
| UI-AC-16 | 320–1440px | ready / V5 | Import shows the signed-in destination account above the unchecked ownership confirmation. |
| UI-AC-17 | 320–1440px | disabled / V5 | Import is disabled until the ownership checkbox is checked. |
| UI-AC-18 | 320–1440px | validation / V5 | An incompatible source shows its reason and the original-copy download action. |
| UI-AC-19 | 320–1440px | success / V5 | Confirmed import shows an open-project action and says the browser original is retained. |
| UI-AC-20 | 320–1440px | partial / V1 | Previously loaded cards remain visible beside a next-page retry control. |
| UI-AC-21 | 320–1440px | offline | The account-save status explicitly says that saving cannot be confirmed. |
| UI-AC-22 | 320–1440px | error | A labelled retry control appears without replacing existing scene contents with an empty scene. |
| UI-AC-23 | 320–1440px | ready / D1–D3 | Escape closes the dialog and restores focus to the activating control. |
| UI-AC-24 | 320–1440px | ready / both themes | Focus on each project/save control is visible against its actual background. |
| UI-AC-25 | 844×390px | dirty / V3 | Save controls and status remain reachable while the workspace reflows for the low-height viewport. |
| UI-AC-26 | 320–1440px | ready / dark | Generic primary buttons use `--sobre-acento` rather than white. |
| UI-AC-27 | 320px at reflow | ready / V1 | Long project names wrap without requiring a hover tooltip to read them. |
| UI-AC-28 | 320–1440px | ready / V4b | The read-only custom-role view has no copy or Taller action. |
| UI-AC-29 | 320–1440px | recovery / V3 | The recovery banner identifies this account and exposes an explicit recover action. |
| UI-AC-30 | 320–1440px | unknown | An outcome-reconciliation action appears while new mutations are disabled. |
| UI-AC-31 | 320–1440px | late-response / V3 | The Boda project title remains visible with “Cambios sin guardar” after the mocked previous-project completion. |
| UI-AC-32 | 320–1440px | pending-newer / V3 | The save badge explicitly distinguishes submitted changes from newer unsaved edits. |
| UI-AC-33 | 320–1440px | offline / V3 | The mockup’s edit control remains enabled while account saving is unavailable. |
| UI-AC-34 | 320–1440px | already-imported / V5 | The existing-import message offers opening a project without another import submission. |
| UI-AC-35 | 320–1440px | ready / V5 | Changing the fixture account clears ownership consent and never reveals another account’s import result. |
| UI-AC-36 | 320–1440px | error / V4b | The failure describes loading the project and offers no save or copy action. |
| UI-AC-37 | 320–1440px | unavailable | The unavailable-project screen contains no project title, owner or scene illustration. |
| UI-AC-38 | 320–1440px | draft-error | A failed local backup leaves the current project visible and offers retrying the local backup. |
| UI-AC-39 | 320–1440px | too-large | The size-limit message states 2 MiB and does not claim successful saving. |
| UI-AC-40 | 320–1440px | stale / D1 copy | The copy dialog names the current destination account and never offers overwriting the original. |
| UI-AC-41 | 320–1440px | ready / V1 | Searching “Horizonte” finds “Ceremonia · Horizonte” before loading page two of the unfiltered fixture collection. |
| UI-AC-42 | 320–1440px | ready / V1 | The initial 50-row fixture page shows “50 proyectos cargados”. |
| UI-AC-43 | 320–1440px | ready / V1 | “Cargar más proyectos” appends the next page without duplicate cards. |
| UI-AC-44 | 320–1440px | query-loading / V1/V2 | The results region displays “Buscando proyectos…” while the labelled filters remain operable. |
| UI-AC-45 | 320–1440px | query-late-response / V1/V2 | “Horizonte” and its matching card remain after the mock obsolete “Boda” response. |
| UI-AC-46 | 320–1440px | partial / V1/V2 | Changing a filter removes the failed old page's retry control and starts a first-page query. |
| UI-AC-47 | 320–1440px | ready / V2 | The owner selector includes the authorized fixture owners Lucía, Mateo and Ana. |
| UI-AC-48 | 320–1440px | page-loading / V1/V2 | “Cargando más proyectos…” appears below retained cards with a disabled pagination button. |
| UI-AC-49 | 320–1440px | ready / V1 | After loading page two, changing the name filter resets pagination to at most 50 matching rows. |
| UI-AC-50 | 320–1440px | ready / V5 | Import explains that the complete scene is saved and separately stored AI conversation/images remain in this browser. |
| UI-AC-51 | 320–1440px | cursor-invalid / V1/V2 | “Recargar lista” restarts the first page while preserving the visible name/owner filters. |
| UI-AC-52 | 320–1440px | pending / unknown / V3 | Choosing “Nuevo proyecto” opens D3 and retains the current title until departure is resolved. |
| UI-AC-53 | 320–1440px | stale / D2 → D1 or D3 | Cancelling the second dialog restores focus to the original page trigger or the current conflict-resolution control. |
| UI-AC-54 | 320–1440px | pending / pending-newer / unknown / offline / D3 | A visible explanation inside D3 states why “Guardar y continuar” is disabled. |
| UI-AC-55 | 320–1440px | ready / V1–V5 / both themes | Active section navigation has neutral surface/text tokens, without an accent fill or colored rail. |
| UI-AC-56 | 320–1440px | ready / V1–V5 / both themes | Default notices, account avatar and destination groups have no accent-colored background. |
| UI-AC-57 | 320–1440px | ready / V1/V2 | Every card save date is right-aligned and uses tabular figures. |
| UI-AC-58 | 320–1440px | ready / V1–V5 | Page headings and supporting section labels use sentence case without tracked uppercase eyebrows. |
| UI-AC-59 | 320–1440px | ready / D2 | Local-work and account-version details are separated by rules instead of nested cards. |
| UI-AC-60 | 1440×1000px | ready / V1/V2 | The first project row includes visible titles, save dates, owner where applicable and opening actions within the viewport. |
| UI-AC-61 | 320–1440px | empty / V1/V2 | The empty-state instruction and next action appear without a decorative icon tile. |
| UI-AC-62 | 320–1440px | ready / V1–V5 | Nonfloating peer cards and scene panels have borders without shadows. |
| UI-AC-63 | 320–1440px | ready / V1/V2 | The loaded count is right-aligned at the end of the result summary and uses tabular figures. |
| UI-AC-64 | 320–1440px | success / V3 | The visible save time matches the selected project’s save timestamp in the library. |
| UI-AC-65 | 320–1440px | ready / V5 / both themes | Destination, consent and retention/download group share the import column's left content edge. |
| UI-AC-66 | 320–1440px | ready / V5 / dark | Ownership consent uses the kit Checkbox with an identifiable ≥3:1 unchecked edge and a visible checked state. |
| UI-AC-67 | 320–1440px | ready / both themes | Input and Select edges use the measured `--input` role and remain distinguishable from adjacent surfaces. |
| UI-AC-68 | 320–1440px | ready / V1/V2 | Project card titles, content and footer use the kit's 24px content padding, reduced to 20px on phones. |
| UI-AC-69 | 320–1440px | all | Visible labelled Vista, Estado, Diálogo and Tema selectors and the Mockup label remain available for inspection. |

## 12. Open questions and assumptions

**Open questions for the owner: none.** Q1–Q3 are resolved by the accepted round 9 q5–q7 answers; Q4 is resolved by the Planner's technical ruling and T4.3/T4.4/T4.6. The design and subplan remain unapproved; SP-2 remains the planning focus. No repeated owner confirmation is requested for these settled behaviors.

| Resolved decision | Authority | Effective contract |
|---|---|---|
| Q1 — Save mode | Owner, round 9 q5 | First explicit named save; subsequent autosave with visible state and “Guardar ahora”. 500ms debounce remains the Planner technical default. Account/project draft isolation and truthful pending/offline/conflict handling remain. |
| Q2 — Foreign originals | Owner, round 9 q7 | Staff/admin with read-all access inspect originals read-only. “Guardar una copia en mi cuenta” requires `taller.usar` and creates a caller-owned project. No original update or ownership transfer. |
| Q3 — Saved content | Owner, round 9 q6 | Name plus complete scene including room/environment/salon/materials/scene-node relationships. Separately stored AI conversation/generated images remain local. No local erasure or dropped valid scene field/reference. |
| Q4 — Search/filter scope | Planner ruling, T4.3/T4.4/T4.6 | Global authorized server filtering before 50-row cursor pagination, literal trimmed `q` ≤120, `mine|all`, authorized UUID `ownerId`, filter-bound cursor mismatch 400, metadata-only owner choices, reset/late-response/page-retry handling in F6. |

Confirmed: users see their own projects; authorized staff can open everyone's; browser scenes are offered for explicit import; original data must not be lost; later saves must not silently overwrite earlier concurrent saves. Saving requires server acknowledgment. Plan 3 includes own Taller projects; custom roles are evaluated by actual permissions, not display names.

Presentation assumptions retained from the prior draft: one detected current browser scene from the evidenced key; no delete/share/history UI; optional nonessential scene illustrations; ES copy with translation rollout in SP-8/SP-10; search debounce is a UI implementation timing, not a new owner decision. The self-contained mockup uses system fonts, fictional metadata and illustrative scenes; save/import states remain manually inspectable and do not write real storage. Search/pagination alone simulate asynchronous responses locally. Source receipt/deduplication and raw-source preservation remain implementation requirements for lossless import. T4.2/T4.3 specify project-document@1, trimmed names of 1–120 characters, 2 MiB limit, complete scene validation, atomic revision compare-and-save and account-scoped durable mutation/import receipts.

Authoritative errors: missing/inaccessible item 404 (generic “Proyecto no disponible” without metadata), collection-scope denial 403, unauthenticated 401 (SP-2), conflict 409, too-large 413 (retain scene and explain 2 MiB limit), cursor/filter mismatch 400 (restart the list as specified in section 5). CSS illustrations and simulated queries cannot prove identical 3D round trips, database pagination, concurrency, access control, storage retention, import idempotency or accessibility compliance. Those need task-level integration tests and independent rendered review. No preview setting is required for these explicitly requested planning files.

Planning artifact verification for the 21:01 kit revision (2026-10-26):

- `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/inline.py <HTML>`: current kit inlined; no network reference, external font or image. The native labelled view/state/scene/theme selects and the Mockup label remain present.
- `python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <HTML>`: **158 pairs checked in light and dark, all pass**.
- `uv run --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <HTML> --max-combos 720`: **720 renders / 720 planned combinations**, widths 1280 and 390px, both themes; **37,406 text measurements and 1,029 focus stops**. **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems.** The final full matrix was not sampled and emitted no warnings. Earlier audit failures were corrected: long pending-newer status now wraps beside a compact badge, consent has its own semantic group, and generic denied/unavailable pages use the standard app content width rather than the import form width. Native dialog content identifies its modal semantics for rendered measurement; native modal behavior provides inertness and focus containment.
- Supplementary Playwright reflow inspection recorded **1,560 cases** across 320/640/768/1024/1440px and both themes: zero horizontal overflow or page exceptions. This inspection preceded the final axis/binding refinements; the subsequent complete kit audit above covers the final HTML at 1280/390px.
- **46 interaction assertions passed**: global name search beyond row 50; 50→56 owned-fixture pagination without duplicates; query-reset/late-response behavior; authorized owner filter; read-only foreign view/copy destination and restricted-role controls; blank-name validation and named saving; departure guard and focus return across conflict→copy; pending/offline disabled saving with local editing; explicit import consent, original-retention copy and per-account receipt isolation; denied/unavailable metadata suppression. Zero page exceptions or external requests were observed.
- Supplementary rendering measured **30 cases** for dialogs and checked consent at 320×900, 390×900 and 844×390 in both themes; no contrast, control-edge, alignment, padding or overflow findings. A complete keyboard cycle across both libraries in six list states and both themes checked **24 cases / 1,404 focus stops**, with no failed indicators. This includes controls below the first 50 project cards.
- In-memory screenshots were visually inspected for the desktop library at 1440×1000 (first row's opening actions within the viewport), dark phone import and dark phone first-save dialog. No extra screenshot or preview files were written. Import destination, consent group and retention/download group use the same content axis; sticky-header focus clearance is a project layout proposal.

These checks attest only the planning mockup. Earlier draft evidence is superseded. Product lint/types/build, real persistence/authorization, lossless 3D round trips, database concurrency/import idempotency and full WCAG conformance were not run or established; T4.6–T4.9 and owner plan/design approval remain pending. No production repository, SPEC, PLAN or other bitácora content was edited by this task.
