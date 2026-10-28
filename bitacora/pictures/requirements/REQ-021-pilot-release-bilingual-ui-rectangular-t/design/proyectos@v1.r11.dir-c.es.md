---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer
date: 2026-10-28
direction: c
name: Edición en contexto
source_revision: r11
source_behavior: proyectos@v1.r11.behavior.md
---

# Edición en contexto — proyectos@v1 · r11 · C

## 1. Identidad y trazabilidad

**Solo exploración; borrador, no aprobado ni contrato de implementación.** Esta nota específica de la dirección acompaña el TSX, el HTML autocontenido, dos composiciones candidatas y el JSON de ejes. No reemplaza ni modifica el `proyectos@v1.md` / `.html` canónico, ninguno de los contratos relacionados, SPEC ni PLAN. El propietario selecciona una dirección; un finalizador independiente escribe el par canónico después de la selección.

Alcance del comportamiento: `proyectos@v1.r11.behavior.md`, R6/R7 y SPEC «Comportamiento — SP-3 y SP-4 (respuestas de la ronda 9)». Consumidores, si se selecciona y aprueba esta dirección de forma independiente: SP-4 T4.1 copia el artefacto aprobado; T4.4 implementa las vistas de lista/guardado/conflicto/solo lectura/escena nueva; T4.5 implementa la importación; T4.8 revisa la fidelidad del renderizado. Ningún otro subplan adquiere una dependencia de UI por el solo hecho de consumir la identidad del proyecto. Compatibilidad con la maqueta anterior no aprobada: **composición visual incompatible**, porque la divulgación de la lista, la jerarquía y la edición en contexto requieren implementación y revisión; las reglas de persistencia/propiedad del producto no cambian. La compatibilidad con una implementación de producción aprobada está por determinar; no se afirma que exista.

Fuentes inspeccionadas en modo de solo lectura en t12 y asesor: `src/app/globals.css`, `layout.tsx`, `/3d/page.tsx`, `Taller3D.tsx`, la lógica local para guardar escenas y la navegación del shell. El guardado local existente usa una escena del navegador y un debounce de 500ms; no es persistencia vinculada a una cuenta. El Markdown/HTML canónico relacionado de cuentas-admin y planes y sus TSX seleccionados establecen el encabezado compartido de cuenta, el control de idioma, la divulgación de cuenta, la navegación horizontal neutra, Geist y el vocabulario de bordes generosamente redondeados. Las solicitudes anteriores de paletas/tipografías independientes ceden ante el alcance explícito de esta delegación, que fija el sistema visual del producto.

Solo se escriben archivos específicos de esta revisión. No se editan los repositorios de producción. No se instalan paquetes, no se consultan recursos de red, no se inicia ningún servidor ni se realizan commits, cambios al plan o aprobaciones.

## 2. Propósito y usuarios

La lista responde «¿Qué escena guardada quiero continuar?». El encabezado de edición responde «¿Cómo se llama este proyecto y estos cambios se guardaron en mi cuenta?». La escena permanece en contexto mientras la persona edita su nombre, revisa los límites del guardado o resuelve un error.

Los propietarios guardan, buscan, vuelven a abrir y continúan sus proyectos. Los empleados/administradores autorizados buscan entre los propietarios a los que tienen permiso de acceder y leen los originales de otras personas. Copiar requiere permiso para usar Taller y crea un proyecto propio; nunca edita ni transfiere el original. El acceso de solo lectura sin permiso para usar Taller tiene su propia presentación accesible y no incluye controles para copiar/editar. Una persona que inicia sesión en un navegador compartido da su consentimiento explícito antes de importar contenido heredado.

## 3. Arquitectura de la información y enfoque

Se conservan el encabezado de Pictures/Sempertex, los controles de idioma y cuenta, y la regla horizontal neutra de las vistas relacionadas. Proyectos introduce dos destinos de ruta, Taller 3D y Proyectos, porque el requisito de proyectos guardados los exige; esto no constituye un nuevo modelo de navegación global. El Taller conserva la barra de herramientas de escena, la barra lateral de paneles, el vocabulario del inspector de escena/IA, deshacer/rehacer y los controles contextuales existentes de foto y lista de compras.

**Cambio específico de esta dirección:** los proyectos son bandas expandibles de ancho completo, no una tabla permanente, una cuadrícula de tarjetas ni una barra lateral de maestro/detalle. Al abrir «Ver escena», la escena aparece dentro de la banda de ese proyecto. El nombre, el propietario y la acción de apertura permanecen en su línea original. Se abre como máximo una vista previa. «Qué se guarda» muestra la explicación de almacenamiento local frente a la cuenta en el punto donde se necesita. En el Taller, el nombre editable pasa a ser el campo etiquetado; Enter o el botón de verificación confirma y Escape cancela. Los controles nuevos responden con una sensación de presión y asentamiento, sin introducir una nueva identidad visual.

Primero se dibujaron dos miniaturas HTML:

- **Candidata 1, elegida:** banda de proyecto de ancho completo con vista previa en el mismo lugar y divulgación contigua sobre los límites del guardado. Mantiene la identidad del proyecto y la alineación de las acciones, mientras la divulgación progresiva cambia la densidad.
- Candidata 2: paneles de dos columnas que priorizan la escena. Es una composición válida dentro del sistema, pero repite vistas previas grandes y pierde la relación directa de la primera candidata entre la fila cerrada y su estado abierto.

El mockup completo desarrolla la candidata 1. Ambas miniaturas siguen siendo composiciones ilustrativas; ninguna es el artefacto interactivo completo. El HTML principal se construye con componentes instalados reales, no con la alternativa HTML de sustitución.

## 4. Sistema de diseño fijo y ocho ejes

Los tokens del proyecto se asignan a los roles semánticos reales del kit; no se introduce una paleta ni una familia tipográfica nuevas.

| Fuente del proyecto | Responsabilidad del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--superficie-suave` | grupo local sutil | #faf8fd / #1c1e26 |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto de apoyo | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde accesible de control, alias heredado de la vista relacionada | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primario / texto sobre el primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | rol de hover del primario | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | contorno decorativo / divisor | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--exito`, `--exito-suave` | roles de éxito | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | roles de advertencia | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | roles de error | #b23a45, #ffeaec / #ff979f, #43252a |
| `--taller-visor`, `--taller-panel`, `--taller-encima` | contexto existente de la escena del taller | #ebe7f1, #faf9fc, #f3eefb / #1a1722, #16131d, #231e2e |

Geist Sans y Geist Mono se integran desde los recursos WOFF2 locales existentes de Next. Mono se limita al tratamiento heredado de metadatos y marca denominativa. Los radios de panel/campo/píldora de 32/18/999px y el margen interior de 24px coinciden con las vistas relacionadas. El relleno de la banda es de 28px en escritorio y 20px en teléfono; el relleno del diálogo es de 28px en escritorio y 24px en teléfono. El color identifica la acción principal y los estados reales de guardado/error. No cambia el color de la navegación de rutas.

| Eje | Dirección observable |
|---|---|
| concepto | Edición en contexto: abrir una escena dentro de su propia fila, renombrar en la cabecera y desplegar únicamente la explicación o recuperación necesaria. |
| layout | Una pila de bandas horizontales a todo el ancho. La banda abierta contiene escena y explicación en proporción 1.8:1; no existe un panel maestro-detalle lateral ni una cuadrícula permanente de tarjetas. |
| navigation | Cabecera y navegación horizontal compartidas; Ver escena/Ocultar escena expande el proyecto en su propio lugar, Abrir lleva al Taller o a solo lectura. Qué se guarda despliega la explicación junto al estado. |
| typography | Geist Sans del producto: título 24px, proyecto 20px, sección 16–18px, cuerpo 14–15px, metadatos 12–13px. Geist Mono solo en la identificación Sempertex heredada. |
| density | Proyectos cerrados de una fila y una única escena abierta. La información secundaria se revela a demanda; 28px de margen interior en escritorio y 20px en teléfono. |
| components | Button/Input/Skeleton/Dialog reales de shadcn y Base UI/Animate UI. Composición propia de bandas expandibles y renombrado in situ; botones con presión táctil, selector de propietario nativo y disclosure de cuenta heredado. |
| colour | Exactamente Pictures: fondo/superficie/texto/acento y tokens Taller para el visor; roles accesibles de borde de control heredados de cuentas-admin y planes. No hay nueva paleta ni familia tipográfica. |
| motion | Asentamiento táctil: las bandas se comprimen .985 y se asientan con una secuencia de 55ms; la escena pasa de .965→1.008→1; el estado rota de -14°→5°→0; los avisos se asientan verticalmente; presión .965 con spring 220/16; hover en iconos y nombre editable. Expresivo 520/170ms, natural 320/140ms, sutil 160/100ms; reducción sin desplazamiento. |

Componentes reales, con evidencia de importación:

| Nombre del componente | Fuente y uso |
|---|---|
| `shadcn:button default default/hover/focus/pressed/disabled/loading` | `@/components/ui/button`; guardado de cuenta, importación y copia propia |
| `shadcn:button outline default/hover/focus/pressed/disabled` | Mismo import; vista previa, navegación, reintento y cancelación |
| `shadcn:input text empty/filled/focus/invalid/disabled` | `@/components/ui/input`; búsqueda, nombre en línea y guardado con nombre |
| `shadcn:skeleton record loading` | `@/components/ui/skeleton`; bandas esqueleto de la lista |
| `shadcn:dialog project open/closed/validating/busy` | `@/components/ui/dialog`; diálogo real instalado de Animate UI/Base UI con confinamiento del foco |
| `custom:project-band collapsed/expanded` | Artículo semántico y botón con aria-expanded/aria-controls; sin atribución inventada a una biblioteca |
| `custom:account-disclosure closed/open/focus` | details/summary nativos compartidos, con cierre mediante Escape o clic fuera |
| `custom:owner-filter native all/mine/other` | Select nativo etiquetado; solo para el personal |
| `custom:scene-preview illustrative` | SVG en línea que representa una escena neutra de ejemplo; no es un renderizador WebGL ni un contrato de miniatura almacenada |
| `custom:motion profile/reduced` | Perfil `@kit/motion`; `motion.button` de `motion/react`, spring de useMotionProfile |
| `custom:planning-controls` | `mountMockup/useMockup` de `@kit/mockup`; selectores nativos de vista/estado/escena/tema/movimiento |

## 5. Navegación, interacción y movimiento

La lista abre los proyectos propios en el Taller y los proyectos ajenos en modo de solo lectura. Los destinos reales son `/proyectos`, `/3d?proyecto=<id>` y `/proyectos/[id]`, según lo especificado en el plan. El HTML simula la navegación localmente, sin solicitudes de red. Los cambios de vista enfocan H1; las divulgaciones mantienen el foco en el control que las activa. Los botones de vista previa exponen el estado expandido y un id de destino. El primer guardado y la copia requieren un nombre no vacío después de recortarlo. Escape o cancelar en un diálogo devuelven el foco exactamente al control activador que siga disponible; si la vista de origen fue reemplazada, se usa como alternativa el campo de nombre, el botón o H1. Los detalles cerrados ocultan explícitamente su contenido, preservando la visibilidad y medición de la divulgación.

La gramática del movimiento es táctil, finita y legible en todas las vistas. El modo expresivo usa asentamiento de 520ms / controles de 170ms / desfases de banda de 55ms con cubic-bezier(.34,1.4,.64,1). El modo natural usa 320/140/30ms y el sutil, 160/100/12ms. El artefacto presenta estos comportamientos diferenciados:

1. La coreografía de carga/cambio de vista de las bandas las comprime a .985, las eleva brevemente y las asienta; cada banda siguiente tiene un desfase de 55ms.
2. La escena expandida se acomoda desde .965, pasa por 1.008 y llega a 1 sin ocultar su texto.
3. Los avisos se asientan con una breve compresión vertical, independiente de la escena.
4. Los iconos de estado de guardado rotan de -14° a 5° y luego a cero, y se asientan en escala.
5. Los campos de edición en línea se acomodan desde scaleX(.96), pasan por 1.01 y llegan a 1, anclados al borde del texto.
6. El hover del botón eleva su icono; al presionarlo se comprime a .965. El control de nombre usa el spring de Motion instalado, con stiffness 220/damping 16 en modo expresivo.
7. El guardado/importación pendiente muestra un icono giratorio solo mientras está pendiente; la respuesta del teclado sigue siendo un contorno estático de alto contraste.

La preferencia reducida del sistema operativo, Quieto y `?still=1` eliminan el desplazamiento, las transiciones animadas y el giro, manteniendo todos los estados, controles y textos de estado. En el producto, las animaciones CSS de pestañas ocultas quedan en pausa; no hay efectos ambientales decorativos persistentes. El movimiento de entrada usa transformaciones sin cambios de layout, reducción de opacidad ni cambios de color a mitad de la animación.

## 6. Flujos e invariantes de comportamiento

1. **Primer guardado:** escena nueva → «Sin guardar todavía» → Guardar proyecto → diálogo de nombre → validación o Guardando… → solo una revisión actual confirmada indica Guardado en tu cuenta. Las ediciones posteriores se guardan automáticamente; Guardar ahora sigue disponible fuera de los estados pendiente/conflicto. Las respuestas de producción reconocen únicamente la generación e identidad que enviaron.
2. **Proyecto nuevo:** Escena nueva, plantilla y Abrir en Escena comparten la misma transición. Un proyecto guardado primero completa el guardado pendiente; una escena sin guardar pide confirmación antes de descartarse. Un fallo/conflicto conserva la escena y bloquea el reemplazo. La escena nueva se llama Escena nueva, no tiene identidad guardada y no se carga hasta su primer guardado con nombre. No se agrega una nueva interfaz de eliminación ni de historial.
3. **Reapertura:** buscar en toda la colección autorizada, usar el filtro de propietario solo cuando esté permitido, conservar las filas visibles si falla la página siguiente y reabrir la escena completa. Los cambios de filtro restablecen la paginación; las respuestas tardías no deben reemplazar la consulta actual. Estos son requisitos de producción, no afirmaciones sobre la búsqueda sincrónica del fixture del mock.
4. **Conflicto:** una escritura obsoleta detiene el guardado automático, conserva la escena local y muestra Cargar versión del servidor / Guardar una copia. Al cargar la versión del servidor se confirma qué escena se mostrará y se mantiene disponible el borrador local de recuperación. Al guardar una copia propia se solicita su nombre y nunca se actualiza el documento ajeno/original.
5. **Sin conexión/fallo:** mostrar Sin guardar con el motivo y la opción de reintentar; un reintento muestra Guardando… hasta recibir confirmación. Si falla una copia de seguridad local, se pide a la persona que mantenga la vista abierta y vuelva a intentarla. Si se pierde la autenticación, no se muestra metadata del proyecto y se indica recuperar el acceso mediante la misma cuenta.
6. **Original ajeno:** aviso de solo lectura con escena y propietario; sin nombre editable, herramientas de escena ni acción para guardar sobre el original. Con permiso de Taller, Guardar una copia abre un diálogo explícito para crear una copia propia; sin ese permiso, la acción de copia no aparece.
7. **Importación heredada:** la primera entrada autenticada al Taller ofrece revisar los datos de la cuenta actual, advierte sobre dispositivos compartidos y explica el límite de solo escena. La importación es explícita, segura ante reintentos y crea exactamente un proyecto propio aunque se pierda la respuesta y se reintente. Ahora no conserva el original y la lista ofrece una forma de volver a importar. Los datos inválidos/desconocidos incluyen una explicación y la descarga del original sin procesar. El éxito, la negativa o el fallo nunca modifican ni borran el origen del navegador. Otra cuenta recibe una nueva solicitud de consentimiento, nunca un comprobante ni borrador anterior.

Solo el nombre y la escena completa se transfieren entre navegadores. La conversación con IA y las imágenes generadas permanecen locales. No se incorpora una interfaz de combinación, eliminación, transferencia, uso compartido público ni historial de versiones. Estos invariantes siguen siendo obligatorios cuando quien finalice/implemente adopte una dirección.

## 7. Especificaciones de vistas y diálogos

| Vista del inspector | Superficie y jerarquía | Acción principal / detalle progresivo |
|---|---|---|
| `projects` | Búsqueda de proyectos propios, acceso para recuperar importaciones y pila de bandas de proyectos | Escena nueva; Abrir por fila; Ver/Ocultar escena; Qué se guarda |
| `staff` | La misma superficie compartida más un filtro de propietario etiquetado | Abrir una escena propia o ajena autorizada; distinción clara de propietario/solo lectura |
| `workshop` | Contexto existente del Taller, nombre de escena, estado de guardado en la cuenta y panel contextual de fallos | Nombre en el lugar, primer guardado explícito/Guardar ahora, explicación del guardado local y recuperación ante fallos |
| `readonly` | Aviso de propietario ajeno/solo lectura y contexto completo de la escena | Copia propia solo con permiso de Taller; volver a la lista permitida |

La vista previa de la escena es un SVG ilustrativo neutro, etiquetado «Vista de escena · Mockup». No se propone un nuevo campo de miniatura en el servidor, un trabajo de generación de capturas ni contenido persistente adicional del proyecto.

| Diálogo del inspector (`scene`) | Contenido y resultados |
|---|---|
| empty | Sin diálogo |
| `first-save` | Campo para guardar con nombre, validación, explicación del límite de solo escena, guardar/cancelar |
| `copy` | Nombre de la copia propia, explicación de que se conserva el original, guardar/cancelar |
| `new-scene` | Guardar antes de reemplazar; descartar sin guardar o cancelar de forma explícita; el fallo del guardado muestra el motivo |
| `leave` | Conservar el trabajo pendiente antes de navegar a la lista de proyectos; el guardado continúa hacia el destino solicitado originalmente |
| `server-version` | Explicación explícita de la carga del servidor y conservación del borrador local; cancelar |
| `import` | Destino en la cuenta actual, importación o rechazo explícitos, advertencia sobre dispositivos compartidos; recuperación de datos inválidos/error y descarga del original |

## 8. Reachable states

The native Estado switch exposes every state below. States apply to the named surface; unrelated combinations retain the normal surface rather than inventing new business behavior. The Diálogo switch independently reaches every dialog on any view. The native controls are outside the product shell and retain the Mockup label.

| State id | Relevant view | Visible outcome / recovery |
|---|---|---|
| `normal` | All | Authorized results or confirmed account-save text |
| `loading` | List | Skeleton bands and polite loading status |
| `empty` | List | No saved projects; existing Escena nueva action and brief next step |
| `no-results` | List | Explicit no-match feedback and clear search action |
| `next-page` | List | More fixture rows, end-of-list disabled control |
| `next-page-error` | List | Already loaded rows remain; failed next-page reason and retry |
| `unsaved` | Taller | Escena nueva / Sin guardar todavía; first named save required |
| `saving` | Taller | Guardando… with pending control state; no claim of confirmed persistence |
| `offline` | List/Taller | Query failure or unsaved scene; explicit retry, scene remains |
| `error` | List/Taller | Load/save failure, recoverable explanation and retry |
| `conflict` | Taller | Autosave stopped; local scene retained; server-load/copy panel |
| `no-taller` | Read-only | Foreign scene readable, no editing or copy action |
| `import-offer` | List/Taller | Legacy scene review entry with current-account explanation |
| `import-invalid` | List/Taller/import dialog | Incompatible data explanation, raw mock download, no import submit |
| `importing` | Import context/dialog | Importing status/disabled duplicate submit |
| `imported` | List/Taller | One-project acknowledgement and original-retention message |
| `import-error` | List/Taller/import dialog | Retry-safe failed confirmation plus original download |
| `recovery` | Taller | Account-local recovery draft available |
| `local-error` | Taller | Backup failure; stay in view and retry backup |
| `permission-denied` | All | Access refusal without project names/owners/scene metadata |
| `unavailable` | All | Non-disclosing unavailable-project surface |
| `session-expired` | All | Same-account sign-in/recovery guidance and no scene data |

Controls additionally expose normal/hover/focus/press, validation and disabled/busy behavior. No checkbox is needed for import: the distinct explicit Importar a mi cuenta and Ahora no actions give consent/refusal without a redundant consent checkbox.

## 9. Responsive behavior

- **360–639px:** 20px outer gutter; masthead/language/account controls wrap; heading/action stack; search/filter become full-width; preview moves below the row controls and explanation below the scene; Taller scene-name/status/save controls wrap, existing panel rail/inspector collapse to the phone tool context; dialogs use viewport-minus-40px width and 24px padding. Actions remain at least 44px high. Vertical scrolling is intentional; no horizontal page scroll is allowed.
- **640–1099px:** 24px outer gutter; filters wrap above the list; expanded band keeps a scene plus explanation when space permits; Taller inspector collapses, preserving the main scene and rail. Native account/header controls wrap without changing navigation semantics.
- **1100px and above:** 40px outer gutter, 1520px maximum shared shell; full-width project bands; 1.8:1 scene/explanation; existing scene/rail/inspector context visible.

Visual checks include 390, 768 and 1280px. Additional rendered probes at 360 and 1024px verify list reflow in both themes. English expansion is supported in the mockup's shared language selector; fixture project names remain data, not translated identities.

## 10. Accessibility targets and verification boundaries

Target applicable WCAG 2.2 AA, not a certification. Semantic headings/articles/navigation, programmatic names and state/error announcements are present; keyboard Enter/Space invoke buttons and disclosures. Named-save inputs have associated labels and aria-invalid/described error. Dialogs use the installed modal's inert background/focus containment. Escape returns to the invoking control. Focus uses a 3px product accent outline offset 4px. Control boundaries use the sibling's accessible texto-tenue alias rather than the decorative divider token. Text targets 4.5:1 and control edges/focus 3:1 in both themes. Reduced motion preserves information and actions.

This is a planning fixture: save/import timing, matching/owner-filtering and transitions are in-memory simulation. The downloaded JSON is explicitly `escena-original.mock.json`; it demonstrates recovery UI, not user-data recovery. No storage/API, atomic revision check, idempotency, cross-browser scene fidelity, full-collection server search, authentication or real account-switch isolation is implemented or verified here. Existing photo/shopping/tool controls show a Mockup scope notice; they are retained context, not redesigned or implemented. Real behavior belongs to the plan's implementation/integration tasks.

## 11. Observable acceptance and honest evidence

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| C-AC-01 | 360–1280px | All | The Pictures/Sempertex masthead, Geist type and shared account/navigation vocabulary remain recognizable; no new palette appears. |
| C-AC-02 | 1100px+ | List normal | An expanded scene is inside its project's full-width band, with identity/actions above and save explanation beside it. |
| C-AC-03 | 360–639px | List normal | Scene and explanation stack within the same band without horizontal overflow. |
| C-AC-04 | All | List expanded/collapsed | Ver/Ocultar escena changes only the selected band and exposes aria-expanded; another band can replace the open preview. |
| C-AC-05 | All | Loading/empty/no-results | Each named list state has distinct visible feedback and an actionable next step; loading uses skeleton bands. |
| C-AC-06 | All | Next-page failure | Previously loaded rows stay visible while the next-page failure and Reintentar action appear below them. |
| C-AC-07 | All | Staff list | Only the staff view exposes the owner filter; foreign entries carry owner and Solo lectura copy. |
| C-AC-08 | All | Taller inline rename | The scene-name control becomes a labelled input in its current header position; confirm/Escape keep the context. |
| C-AC-09 | All | First save invalid | Empty names show the associated field error and keep the dialog open. |
| C-AC-10 | All | Saving/saved | Guardando… remains visible until acknowledgement; saved text is not shown for pending work. |
| C-AC-11 | All | New scene | All three creation entry points yield Escena nueva with Sin guardar todavía after protecting prior edits. |
| C-AC-12 | All | Conflict | The failure panel shows both server-load and owned-copy actions; normal save is stopped. |
| C-AC-13 | All | Offline | Sin guardar and the offline reason remain beside the project context, with an explicit retry. |
| C-AC-14 | All | Foreign original | No editable name or scene tool is present; copy is absent without Taller permission. |
| C-AC-15 | All | Import offer | The current-account destination and shared-device warning precede distinct import/refusal actions. |
| C-AC-16 | All | Invalid import | Explanation and original download remain available, while import submit is absent. |
| C-AC-17 | 390px | Dialogs | Modal content fits within its viewport frame, with readable padding and reachable actions in both themes. |
| C-AC-18 | All | Keyboard/reduced | Focus is visible, modal Escape restores invocation focus and reduced/still modes retain every action without travel. |

Build: real offline builder, 647KB self-contained HTML, 2126 source files bundled. No fallback or downloaded assets. `contrast.py`: **158 pairs checked in light and dark, all pass**. The first rendered audit found two band-padding findings caused by measurable closed-disclosure content; explicit hidden bodies fixed them. A complete subsequent audit measured 672 renders, 17,388 text measurements and 1,965 focus stops with a PASS. A focused interaction test found the invoking import button was being recreated; lifting the feedback component out of the render and retaining disclosure identity fixed the return target. The final source is re-audited after these fixes; final RESULT and counts are recorded below when complete.

The complete scripted mockup walkthrough passed 12 checks with zero page errors: first-save validation/acknowledgement, inline rename, offline retry, conflict copy, new/template guard, save-and-continue destination, focused search, authorized-owner/read-only/copy visibility, invalid import/download/Escape/focus, import refusal and English view. Initial walkthrough attempts had two locator/assertion mistakes (two Plantillas controls and two legitimate Escena matches), corrected without changing the UI's behavior. Additional 360/390/768/1024/1280px list probes found no contrast, control-edge, padding, alignment or overflow issues in either theme. Screenshots were inspected in memory for both candidates, desktop list/Taller, phone list/conflict/first-save/import and tablet list; no additional screenshot files were written.

`compare_directions.py` measured A/B/C: overall `ok=true`, selector evidence passes, no missing evidence. A–C layout similarity **0.114**, B–C **0.156**; both pairs have different motion; B–C also has different density. Shared route navigation intentionally remains the same. These measurements are visual distinction evidence, not proof of production behavior or owner approval.

Final snapshot audit (after the component-identity and pending-navigation corrections): **672 renders / 672 planned, 17,388 text measurements, 1,963 focus stops**, at 1280/390/768px in both themes, exit 0. No combinations were sampled away.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Two additional final-file checks passed: Escena nueva and navigation to Proyectos each wait for an in-flight mock save acknowledgement. There were zero external HTTP(S) requests. At 150ms, expressive startup had three active animations; OS reduced motion and `?still=1` each had zero. Final contrast and A/B/C comparison were rerun on the built final file and passed. The final source/HTML hashes below match this tested snapshot.

## 12. Open question and assumptions

Q: David, ¿debe abrirse la vista previa del primer proyecto al entrar en Proyectos, como en esta exploración, o deben comenzar todas las escenas contraídas?

Provisional assumption pending direction selection: the first authorized fixture opens for comparison; only one preview is expanded at a time. This affects initial presentation, not ownership, first-save/import consent or persistence semantics. The scope's account/save/conflict/import/new-scene decisions are already settled and are not reopened here.

The owner has not selected or approved this direction. The canonical artifacts and plan remain untouched. Production behavior, independent visual review and any later canonical finalization remain with their assigned plan tasks.

### Input/artifact identity

| File | SHA-256 |
|---|---|
| `SPEC.md` | `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d` |
| `PLAN.json` | `4807c95679b4a0802ec51f16e30a7726d7baf989c5eb308c04dc9f2b6b84edd7` |
| `design/proyectos@v1.r11.behavior.md` | `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65` |
| `design/proyectos@v1.r11.dir-c.tsx` | `f081bd227ac4e420001cc7f3772a2d88a87e9a8f9c19a68f47e61022241a63f9` |
| `design/proyectos@v1.r11.dir-c.html` | `67054c904ffab4e227045695ee9737f2440ec3462d1499d17d8dc2a6d8b8c9a3` |
