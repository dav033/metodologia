---
contract: decoraciones
version: 1
status: draft
subplan: SP-5
requirements: [R8]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: b
name: Espacio de composición
source_revision: r3
source_behavior: decoraciones@v1.r3.behavior.md
source: decoraciones@v1.r3.dir-b.tsx
plan_revision: 17
---

# decoraciones@v1 — Espacio de composición

## 1. Identidad y trazabilidad

Borrador de planificación canónico; **no aprobado para implementación**. El propietario eligió la dirección b, «Espacio de composición», en la comparación web. Esa elección autoriza únicamente esta finalización; no aprueba este contrato, SP-5 ni el plan. Versión 1; no existe una versión anterior aprobada, así que no se modifica nada aprobado. Esta tarea solo escribe `design/decoraciones@v1.md` y `design/decoraciones@v1.html` (además del RESULT de delegación). No se modifica ningún archivo de exploración, historial, SPEC, PLAN, registro de cambios, vista previa ni producción.

Alcance: REQ-021 / M2 / SP-5 «Decoraciones guardadas», R8, de SPEC (§ «Comportamiento — SP-5 (respondido en la ronda 11)», decisiones de la ronda 11, q1/q2), revisión 17 de PLAN.json, `decoraciones@v1.r3.behavior.md` y los archivos Markdown, TSX y HTML de la dirección b elegida en r3. Los comentarios del propietario `cddd13f71c873c18` (sin importación; grupo local «En este navegador»; personal de solo lectura; solo cuentas Taller; elementos guardados únicamente tras la confirmación del servidor; estados enumerados; sin estados de importación) ya se aplicaron en r3 y se conservan aquí.

| Requisito / criterio | Cobertura del contrato | Tareas consumidoras |
|---|---|---|
| R8 — guardar una composición la agrega a la biblioteca personal | V1–V3, F1–F3, estados de guardado, UI-AC-03–06, 14 | T5.3; revisión visual T5.5 |
| Buscar, filtrar y colocar en el proyecto abierto; los controles existentes de nombre/ocasión/miniatura/filtro siguen funcionando | V1, F4, UI-AC-01, 10, 17 | T5.3; T5.5 |
| El personal puede abrir en modo de solo lectura los elementos de otra cuenta; colocarlos agrega una copia a su propio proyecto | V4, F5, UI-AC-09, 10 | T5.3; T5.5 |
| Las entradas heredadas de `taller3d:biblioteca-propia:v1` permanecen locales y nunca se importan; al cambiar de cuenta o cerrar sesión no se muestran los elementos anteriores | V1 «En este navegador», F7, UI-AC-07, 11, 12 | T5.3; T5.5 |
| Estados de guardado, lista, solo lectura, vacío, carga, reintento y error, en teléfono y escritorio | §8, §9, §11 | T5.5 |

Consumidores de PLAN: SP-5 `ui = {contract: decoraciones, version: 1, design_task: T5.1, visual_review_task: T5.5}`. T5.1 copia el contrato aprobado por el propietario, byte por byte, a `design/contracts/decoraciones@v1.md` solo después de la aprobación independiente. T5.3 implementa la interfaz (`Biblioteca.tsx`, `biblioteca/BibliotecaPersonal.tsx`, `biblioteca/textos-biblioteca.ts`). T5.2 (almacenamiento/API), T5.4 (E2E del navegador) y T5.6 (auditoría) son responsables de la persistencia, autorización, regla de eliminación y pruebas de aislamiento; este contrato especifica solo la interfaz y no constituye evidencia para esas tareas.

Evidencia del producto en modo de solo lectura: t12 (HEAD `fb872bce`) y asesor `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/Biblioteca.tsx`, `Taller3D.tsx`. `Biblioteca.tsx` ya incluye «Guardar toda la escena en mi biblioteca», la opción para la pieza seleccionada «Guardar en mi biblioteca», «Esta pieza no se puede guardar sola.», el formulario de nombre/ocasión, miniaturas, filtros por ocasión/color/globos, vista previa, «Añadir a mi escena» y eliminación local, todo en `taller3d:biblioteca-propia:v1`. Los borradores hermanos `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` aportan el vocabulario compartido de la estructura.

Impacto: **cambio incompatible de interfaz** para T5.3 respecto de la biblioteca actual, solo local (nueva fuente de cuenta, disposición en tres áreas, modo de solo lectura para el personal, conjunto de estados). No se ve afectado ningún contrato aprobado.

## 2. Propósito y usuarios

Pregunta de trabajo: «¿Qué decoración guardada agrego a mi proyecto actual y está mi guardado protegido en mi cuenta?»

- **Propietario con acceso a Taller** (Diseñador maestro, Empleado interno, Administrador en su propia biblioteca): guarda la escena completa o la pieza seleccionada con un nombre y una ocasión, ve «Guardado en mi cuenta» solo después de la confirmación del servidor, la encuentra después de recargar y en otro navegador, la busca/filtra y la coloca en el proyecto abierto. Solo el propietario cambia el nombre, edita o elimina sus elementos.
- **Personal que consulta otra cuenta** (Empleado interno, Administrador): inspecciona los elementos de esa cuenta en modo de solo lectura; el propietario y «Solo lectura» están visibles; «Añadir a mi escena» agrega una copia al proyecto del miembro del personal; no aparecen las opciones de cambiar el nombre, editar ni eliminar.
- **Las cuentas sin acceso a Taller** nunca llegan a esta vista; el acceso se concede desde las vistas de cuenta/rol de `cuentas-admin@v1`.

Criterio de éxito: un guardado confirmado aparece en «En mi cuenta», persiste al recargar o usar otro navegador y se puede colocar; nadie ve los elementos de otra cuenta después de cambiar de cuenta o cerrar sesión; las entradas heredadas del navegador permanecen intactas en «En este navegador».

## 3. Arquitectura de información y jerarquía

Orden dentro de la página existente de Taller, de arriba abajo:

1. Estructura heredada: encabezado de Pictures/Sempertex (marca de anillo y punto, selector de «Idioma» ES/EN, menú desplegable «Mi cuenta»), H1 «Taller 3D» con la acción principal de la página «Guardar toda la escena en mi biblioteca» (solo en contexto de propietario), regla de navegación «Taller 3D» (actual) / «Proyectos».
2. Un **panel de trabajo** continuo (radio de 24px):
   - Barra de Taller: identidad del proyecto actual («Proyecto de ejemplo» · «Mi cuenta») y herramientas existentes Deshacer, Rehacer, Foto realista, Lista de compra (sin cambios; fuera del alcance).
   - Navegador de áreas «Zonas de la biblioteca»: Biblioteca / Vista previa / Ficha (Ficha pasa a llamarse «Guardar» en las vistas de guardado).
   - Tres áreas de trabajo: **Biblioteca** (izquierda) → **Vista previa** (centro) → **Inspector** (derecha).
   - Barra inferior: «Biblioteca personal · El catálogo global permanece separado.» más la opción para la pieza seleccionada «Guardar en mi biblioteca» (propietario) o «Solo lectura · <owner>» (personal que consulta una cuenta ajena).
3. Pie de página (estructura).

Jerarquía: principal = vista previa del elemento seleccionado y su única acción principal («Añadir a mi escena» o «Guardar»); secundaria = lista de la biblioteca con fuente/búsqueda/ocasión; complementaria = metadatos, filtros adicionales (Tipo, Color, Globos) dentro del desplegable nativo «Filtros», acciones de propietario/cambiar nombre/editar/eliminar. La divulgación progresiva mantiene expandido un solo elemento a la vez; la lista permanece visible para que la navegación nunca sustituya el proyecto abierto.

Orden del contenido del área Biblioteca: encabezado («Mi biblioteca»; «Biblioteca» al consultar otra cuenta) → selector de propietario (solo para el personal) → selector de fuente («En mi cuenta» | «En este navegador»; «En esta cuenta» únicamente para una cuenta ajena) → indicación de fuente local → búsqueda → selector de ocasión → desplegable «Filtros» → lista de elementos / estado vacío / error / esqueleto de carga.

## 4. Sistema de diseño y lenguaje visual

No se agregan paleta, tipografía, identidad ni token semántico. Los tokens son los nombres de producción de `globals.css`; cada tema los define una vez y los asigna a los roles de shadcn.

| Token del producto | Rol / uso | Claro / oscuro |
|---|---|---|
| `--fondo`, `--texto` | fondo, primer plano | `#faf9fc`/`#0b0c10`, `#1c1425`/`#f4f5f7` |
| `--superficie`, `--superficie-suave`, `--superficie-2` | tarjeta/ventana emergente, fila al pasar el cursor, fila seleccionada y atenuada | `#ffffff`/`#16181f`, `#faf8fd`/`#1c1e26`, `#efe9f8`/`#242733` |
| `--texto-suave`, `--texto-tenue` | texto complementario; bordes de controles y borde de campos (≥3:1) | `#6b6178`/`#9aa1ad`, `#766c85`/`#8a91a0` |
| `--acento`, `--acento-hover`, `--sobre-acento` | acción principal, anillo de foco, globos ilustrativos | `#6d3fe0`/`#9479ff`, `#5530b8`/`#a58dff`, `#ffffff`/`#120b24` |
| `--borde`, `--borde-suave` | divisores de área, separadores de filas, separadores de estructura | `#e3daef`/`#383c48`, `#efe9f8`/`#2a2d38` |
| `--exito`, `--exito-suave` | guardado confirmado, copia colocada | `#1f7a55`/`#78d6a8`, `#dcf5e9`/`#173b31` |
| `--error`, `--error-suave` | error de lista/guardado/acción, acción destructiva | `#b23a45`/`#ff979f`, `#ffeaec`/`#43252a` |
| `--aviso`, `--aviso-suave` | pieza no compatible | `#8f5f12`/`#f7c46b`, `#fff3d8`/`#3f311c` |
| `--taller-visor`, `--taller-panel`, `--taller-barra` | lienzo de vista previa y miniaturas, panel de trabajo/etiqueta de vista previa, barras de Taller | `#ebe7f1`/`#1a1722`, `#faf9fc`/`#16131d`, `#ffffff`/`#121018` |
| `--overlay` | fondo de diálogo | `rgb(28 20 37/.4)` / `rgb(0 0 0/.6)` |

Tipografía: Geist Sans (cuerpo 15px/1.5), Geist Mono solo para la etiqueta del encabezado «Sempertex». H1 24px/600; H2 del inspector 20px/600; H2 de la biblioteca 18px/600; H3 del estado vacío 16px/600; nombre del elemento 14px/600; etiquetas 12–14px/600; metadatos, indicaciones y texto de estado 12–13px.

Forma y espaciado: radio del panel de trabajo 24px; diálogos 32px (24px en teléfono); campos 18px; botones y selectores nativos en forma de píldora, 999px; filas de elementos 18px; miniaturas 12px. Relleno de áreas 24px × 20px; márgenes laterales de la estructura 40px (≥1100px), 24px (640–1099px), 20px (<640px). Todos los controles miden ≥44px de alto (campos de 46px).

Iconografía: lucide-react 18px, `aria-hidden`, siempre junto a texto visible (solo Deshacer/Rehacer usan iconos sin texto, con nombres accesibles).

Foco: contorno de `--acento` de 3px con desplazamiento de 4px en cada elemento interactivo. La selección usa `aria-pressed`/`aria-current` además de la superficie y el peso del texto; nunca depende solo del color.

Componentes (`origen:id variante estado`, ruta de importación):

| Componente | Variantes / estados | Importación |
|---|---|---|
| shadcn:button | predeterminado (principal: Guardar, Añadir a mi escena), outline (secundario/herramientas), destructivo (Quitar) / normal, hover, foco, presionado, deshabilitado, ocupado | `@/components/ui/button` |
| shadcn:input | texto (búsqueda, Nombre) / vacío, con contenido, foco, no válido, deshabilitado | `@/components/ui/input` |
| shadcn:skeleton | miniatura 58×64, línea de texto / cargando | `@/components/ui/skeleton` |
| shadcn:dialog (Animate UI / Base UI) | cambiar nombre, editar / abierto, validación, pendiente, cerrado; explicación de solo lectura para cuentas ajenas | `@/components/ui/dialog` |
| shadcn:alert-dialog (Animate UI / Base UI) | eliminar / confirmar, pendiente, cancelar | `@/components/ui/alert-dialog` |
| kit:motion | expresivo, natural, sutil, movimiento reducido | `useMotionProfile` de `@kit/motion`; marcador de diseño `motion.i` de `motion/react` |
| custom:zone-nav | Biblioteca / Vista previa / Ficha·Guardar / actual | `nav` semántico + botones, tokens del proyecto |
| custom:source-nav | cuenta, navegador, cuenta ajena / presionado, deshabilitado | `nav` semántico + botones `aria-pressed` |
| custom:library-record | escena, pieza / predeterminado, hover, seleccionado, deshabilitado mientras se guarda | `button` con miniatura, nombre, «Tipo · Ocasión» |
| custom:preview | escena, pieza, colocada, vacía / cargando, error, cambiando | `section` con barra de etiqueta y pie |
| custom:inspector | detalles, formulario de guardado, solo lectura, cargando | `aside` |
| custom:status-note | neutro (pendiente), éxito, advertencia, error (+ Reintentar) | `role=status` / `role=alert` |
| custom:account-disclosure | cerrado, abierto | `details/summary` nativo de la estructura hermana |
| select / details nativos | Idioma, Propietario, Ocasión, Tipo, Color, Globos, Filtros | nativos, con estilo de los tokens del proyecto |

El arte de vista previa de la maqueta es un SVG ilustrativo, no un formato de miniatura; en producción se utiliza el renderizado existente de miniaturas/vistas previas de Taller.

Movimiento (firma de dirección: «acoplamiento espacial»), curva de aceleración `cubic-bezier(.23,1,.32,1)`:

| Elemento | Movimiento | expresivo / natural / sutil |
|---|---|---|
| Área Biblioteca | entra desde x −20px | 640 / 360 / 160 ms |
| Área Inspector | entra desde x +24px | igual |
| Lienzo de vista previa | se posiciona desde scaleX .97 | igual |
| Objeto de vista previa | x +25px, rotateY −12° → 0 con ligero sobrepaso | igual |
| Filas de elementos | x −12px, escalonadas | intervalo de 65 / 35 / 15 ms |
| Notas de estado | x +12px | duración del desplazamiento |
| Marcador de zona | deslizamiento con diseño compartido | resorte del perfil del kit |
| Botones | escala al pasar el cursor 1.025, al presionar .965 + 1px | 180 / 150 / 100 ms |

Solo se animan transformaciones/opacidad; el texto permanece legible en todo momento. La preferencia de movimiento reducido, el perfil «Quieto» y `?still=1` eliminan todas las transformaciones/transiciones (incluido el indicador giratorio de espera) y muestran el contenido final. Las animaciones se pausan cuando la pestaña está oculta o el panel fuera de la pantalla. No hay ciclos decorativos infinitos.

## 5. Navegación y modelo de interacción

- **Entrada:** ruta `/3d` (Taller 3D). La biblioteca forma parte de Taller; no es una página nueva. «Guardar toda la escena en mi biblioteca» (encabezado) abre V2; la opción de la barra inferior «Guardar en mi biblioteca», en el contexto de una pieza seleccionada, abre V3. El personal llega a V4 al elegir un propietario (ver Q1).
- **Salida:** «Proyectos» y el menú desplegable de cuenta («Mi cuenta», «Planes», «Cerrar sesión») llevan a vistas hermanas (`proyectos@v1`, `cuentas-admin@v1`, `planes@v1`). «Cancelar» y «Ver en mi biblioteca» regresan a V1 desde una vista de guardado.
- **Navegador de áreas:** Biblioteca / Vista previa / Ficha (o Guardar) mueve el foco al área etiquetada y desplaza la página solo si es necesario (de forma suave, salvo que se prefiera reducir el movimiento). El marcador móvil muestra el área actual.
- **Seleccionar un elemento** actualiza la vista previa y el inspector; no modifica el proyecto abierto. En una vista de guardado, seleccionar un elemento regresa a V1 con ese elemento.
- **Selector de fuente** («En mi cuenta» / «En este navegador») reemplaza la lista sin cambiar de ruta y borra la búsqueda y todos los filtros.
- **Entrada de guardado** coloca el foco en el campo «Nombre»; en teléfonos, primero lo desplaza a la vista.
- **Durante el guardado:** los botones de fuente, las filas de elementos, «Cancelar», los enlaces de navegación y las opciones de guardado de la página se deshabilitan o muestran «Guardando en mi cuenta…» en vez de navegar, para que el destino del guardado no pueda cambiar durante la solicitud.
- **Diálogos** (cambiar nombre, editar, eliminar) mantienen el foco dentro, se cierran con Escape/«Cancelar» (salvo que haya una operación pendiente) y devuelven el foco al elemento que los abrió; tras eliminar, el foco pasa al área del inspector. Los diálogos no aparecen durante la carga ni al cambiar de cuenta.
- **Colocación:** «Añadir a mi escena» agrega el elemento (su estructura y sus decoraciones en conjunto) a la escena actual y mueve el foco a la vista previa; el original permanece en su biblioteca.
- **Cerrar sesión / cambiar de cuenta:** la lista, los detalles, las miniaturas y la vista previa del servidor de la cuenta anterior se eliminan de inmediato, antes de cargar los datos de la cuenta siguiente.

## 6. Flujos

**F1 Guardar toda la escena.** «Guardar toda la escena en mi biblioteca» → V2: vista previa «La escena entera», inspector «Guardar en mi biblioteca» con Nombre y Ocasión, indicación «Disponible desde otros navegadores de tu cuenta.» → «Guardar» → si el nombre recortado está vacío: validación (F1a) → de lo contrario, pendiente: campos y botones deshabilitados, «Guardando…» / «Guardando en mi cuenta…» → al confirmar el servidor: «Guardado en mi cuenta» + «Ver en mi biblioteca» → V1 muestra el nuevo registro en «En mi cuenta». Si falla → F3.

**F1a Validación.** Nombre vacío o con espacios en blanco → el campo recibe `aria-invalid`, se muestra «Escribe un nombre.» debajo y el foco queda en el campo; editarlo borra el error.

**F2 Guardar la pieza seleccionada.** Con una pieza seleccionada, «Guardar en mi biblioteca» → V3: vista previa «La pieza sola», el mismo formulario → igual que F1. Si la pieza no se puede guardar sola: advertencia «Esta pieza no se puede guardar sola.», formulario deshabilitado, «Cancelar» disponible.

**F3 Error al guardar y reintento.** Error «No se pudo guardar. Conservamos el nombre y la ocasión.»; Nombre/Ocasión siguen completados y editables; el botón principal dice «Reintentar guardar» → pendiente → confirmación. Un guardado fallido nunca aparece en la lista de la cuenta ni muestra una etiqueta de guardado.

**F4 Buscar y colocar.** Origen → búsqueda («Buscar en mi biblioteca») y/o Ocasión y «Filtros» (Tipo, Color, Globos; «Limpiar filtros» cuando haya alguno seleccionado) → elegir registro → vista previa + ficha (nombre, Tipo, Ocasión, Propietario, indicación de procedencia) → «Añadir a mi escena» → «Copia añadida a tu escena.» y pie de la vista previa «Copia añadida a tu propio proyecto.». Sin coincidencias → «Sin resultados» / «Cambia la búsqueda o los filtros.» + «Limpiar filtros».

**F5 El personal inspecciona y coloca.** El personal selecciona un propietario → encabezado «Biblioteca», solo el origen «En esta cuenta», «Solo lectura» en la etiqueta de la vista previa, el inspector y la barra inferior; Propietario muestra al propietario; explicación «Solo el propietario puede actualizar o quitar esta decoración. Añadir crea una copia en tu propio proyecto.» → «Añadir a mi escena» agrega una copia al proyecto propio del miembro del personal. Las acciones Renombrar, Editar y Quitar no aparecen (no están deshabilitadas). Al elegir «Mi cuenta» en Propietario, se muestra la biblioteca propia del miembro del personal con las acciones habituales del propietario.

**F6 Metadatos y eliminación por el propietario.** «Renombrar» → diálogo con Nombre → «Guardar» → pendiente «Guardando en mi cuenta…» → al confirmar, se actualizan la lista y la ficha, estado «Guardado en mi cuenta», foco de vuelta al control que abrió el diálogo. «Editar» → el mismo diálogo con Nombre y Ocasión (alcance: Q2). «Quitar de mi biblioteca» → AlertDialog que nombra el artículo → «Cancelar» lo conserva; «Quitar» → «Quitando…» → al confirmar, el registro desaparece de la lista, estado «Quitado de mi biblioteca», foco en el inspector. Los artículos guardados solo en el navegador ofrecen únicamente «Quitar de mi biblioteca»; tras confirmar en el mismo AlertDialog, desaparecen de inmediato de la lista de ese navegador, sin llamada al servidor ni importación. Error en la acción → «No se pudo completar la acción. La decoración sigue en tu biblioteca.» + «Reintentar».

**F7 Aislamiento de cuentas.** Cerrar sesión o cambiar de cuenta → etiqueta del proyecto «Cambiando cuenta…», lista/vista previa/inspector reemplazados por esqueletos y «La biblioteca anterior ya no se muestra.» → se carga la lista de la siguiente cuenta (vacía o con sus propios registros). El almacenamiento heredado del navegador no se migra ni se modifica. No existe ninguna acción, progreso ni error de importación.

## 7. Especificaciones de vistas

Todas las vistas comparten la estructura del taller y el contenedor de §3; solo cambian el contenido del inspector, la etiqueta de la vista previa y las acciones disponibles. El selector «Idioma» heredado cambia entre español e inglés; el prototipo muestra las cadenas en inglés.

**V1 `library` — Mi biblioteca (propietario).** Biblioteca: «Mi biblioteca», origen «En mi cuenta» (predeterminado) | «En este navegador»; en el origen del navegador, la indicación «Solo en este navegador. No se importan a tu cuenta.» Los registros muestran miniatura, nombre, «Escena|Decoración · Ocasión», chevrón. Etiqueta de la vista previa «Vista previa»; pie «Vista previa · No modifica el proyecto abierto.» (el prototipo antepone «de ejemplo»). Inspector «Ficha»: H2 con el nombre del artículo; `dl` Tipo / Ocasión / Propietario («Mi cuenta» o «En este navegador»); indicación de procedencia «Guardado en mi cuenta» (icono de nube) o «Solo en este navegador.» (icono de monitor); acciones en una columna: «Añadir a mi escena» (principal), luego, para artículos de la cuenta, «Renombrar» y «Editar», después «Quitar de mi biblioteca»; nota «“Añadir a mi escena” la suma a la que tienes, con su armado: la estructura y sus decoraciones juntas.» Flujos F4, F6, F7.

**V2 `save-scene` — Guardar escena.** Igual que V1; el tercer elemento del navegador de áreas dice «Guardar»; etiqueta de la vista previa «La escena entera»; inspector «Guardar en mi biblioteca» / «La escena entera.», campos Nombre (completado de antemano con el nombre de la escena actual) y Ocasión, espacio para mensajes, acciones «Guardar» (principal) + «Cancelar». Tras la confirmación, el formulario se reemplaza por la nota de éxito y «Ver en mi biblioteca». Flujos F1, F1a, F3.

**V3 `save-piece` — Guardar pieza.** Igual que V2, con «La pieza sola» y la advertencia de que no se admite esa pieza. Flujos F2, F3.

**V4 `staff` — Personal · Solo lectura.** Encabezado de biblioteca «Biblioteca», selector «Propietario» encima del selector de origen, único origen «En esta cuenta», sin «En este navegador» para cuentas ajenas. La etiqueta de la vista previa muestra «Solo lectura» con icono de candado. Inspector: etiqueta «Solo lectura», nombre del artículo, metadatos con Propietario = propietario, texto de explicación, solo «Añadir a mi escena». Barra inferior: «Solo lectura · <owner>», sin opción para guardar; opción para guardar oculta en el encabezado. Flujo F5.

**Diálogos.** D1 Renombrar (Nombre). D2 Editar (Nombre, Ocasión). D3 Quitar de mi biblioteca (AlertDialog: título, nombre del artículo, «Cancelar», «Quitar» destructivo). Si se solicita un diálogo de modificación para un artículo ajeno, solo muestra «Solo lectura» + «Solo el propietario puede actualizar/quitar esta decoración.» + «Volver»; nunca muestra un formulario de modificación.

Datos que se muestran: nombre, tipo (Escena / Decoración), ocasión (taxonomía existente), propietario, procedencia, miniatura. Los datos de ejemplo del prototipo llevan la etiqueta «de ejemplo»; no incluyen identidad de clientes, fechas ni textos de marketing.

## 8. Estados

| Estado | Se aplica a | Qué aparece | Qué se puede hacer / recuperación |
|---|---|---|---|
| `normal` | todas | Registros confirmados; formulario listo en las vistas para guardar | Todos los flujos |
| `loading` | todas | «Cargando biblioteca…», 3 filas de esqueleto, vista previa vacía, esqueleto en el inspector; `aria-busy` | Nada específico de un artículo; sin registros desactualizados ni diálogos; búsqueda y filtros deshabilitados |
| `empty` | V1, V4 propia | «Tu biblioteca está vacía» / «Guarda la escena o una pieza desde el Taller.» + «Guardar toda la escena»; el origen del navegador conserva sus propios registros | Guardar; cambiar a «En este navegador». **Regla:** una colección de cuenta sin artículos muestra este estado vacío (no «Sin resultados»), independientemente de cómo se haya llegado a él |
| sin resultados | V1, V4 | «Sin resultados» / «Cambia la búsqueda o los filtros.» + «Limpiar filtros» | Borrar la búsqueda y los filtros; solo cuando la colección tiene artículos, pero ninguno coincide |
| `list-error` | origen de cuenta | Nota de error «No se pudo cargar tu biblioteca.» + «Reintentar»; vista previa «Reintenta cargar la biblioteca.»; sin registros ni acciones de la lectura fallida | Reintentar; el origen del navegador es independiente |
| `saving` | V2, V3 (y diálogos) | Campos conservados y deshabilitados, indicador de carga, «Guardando…», «Guardando en mi cuenta…»; deshabilitada la navegación que cambiaría el destino | Esperar; sin etiqueta de guardado |
| `saved` | V2, V3 | Nota de éxito «Guardado en mi cuenta» + «Ver en mi biblioteca» | Volver a V1, donde aparece el nuevo registro |
| `save-failed` | V2, V3 | Nota de error con Nombre/Ocasión conservados; botón principal «Reintentar guardar» | Reintentar con el mismo destino; editar los valores |
| `validation` | V2, V3, D1, D2 | Nombre vacío, `aria-invalid`, «Escribe un nombre.» | Escribir un nombre |
| `unsupported` | solo V3 | Advertencia «Esta pieza no se puede guardar sola.»; formulario y «Guardar» deshabilitados | «Cancelar». No aplica al guardado de toda la escena |
| `placed` | V1, V4 | Etiqueta de vista previa «Mi escena», objeto agregado, pie «Copia añadida a tu propio proyecto.», inspector «Copia añadida a tu escena.» | Seguir navegando; el original permanece en la lista |
| `action-error` | inspector de V1 | «No se pudo completar la acción. La decoración sigue en tu biblioteca.» + «Reintentar» | Reintentar; el artículo se conserva; no se indica éxito |
| `account-switch` | todas | «Cambiando cuenta…», esqueletos, «La biblioteca anterior ya no se muestra.»; no se muestran nombres, miniaturas, propietario ni vista previa de la cuenta anterior; sin diálogos | Esperar los resultados de la siguiente cuenta |
| mutación pendiente | D1–D3 | «Guardando en mi cuenta…» / «Quitando de mi biblioteca…», botones deshabilitados, Escape ignorado | Esperar; ante un error → `action-error` |
| permission-denied | artículos ajenos | Controles de modificación ausentes; el diálogo forzado muestra la explicación de solo lectura | «Volver». Las cuentas sin Taller nunca llegan a esta vista |

No aplican: importación, progreso de importación y error de importación (ronda 11, pregunta 1 del propietario: no hay importación). Las lecturas sin conexión o desactualizadas usan `list-error`/`save-failed`; no hay un estado separado sin conexión. No se muestran datos parciales: si falla la lectura de la cuenta, no se muestran registros.

Transiciones: las notas de estado aparecen con la animación de estado; el estado de guardado aparece solo tras la confirmación; el cambio de cuenta borra los datos antes de cargar; con movimiento reducido, los estados finales aparecen de inmediato.

## 9. Comportamiento adaptable

Compatible desde 320px. Los mismos puntos de quiebre se aplican a ambos temas e idiomas.

| Rango | Diseño |
|---|---|
| ≥1100px | Ancho máximo del contenedor: 1520px, márgenes de 40px. Cuadrícula del espacio de trabajo `280px | minmax(0,1fr) | 264px`, altura mínima de 520px; borde derecho de la biblioteca y borde izquierdo del inspector. Altura mínima del lienzo de vista previa: 360px; ilustración de hasta 600px de ancho. Acciones del inspector en una columna, ancho completo. |
| 640–1099px | Márgenes de 24px. Cuadrícula `260px | minmax(0,1fr)`; la biblioteca ocupa dos filas a la izquierda, la vista previa queda arriba a la derecha y el inspector debajo de la vista previa (borde superior). Acciones del inspector y formulario para guardar en dos columnas (mensajes y acciones ocupan todo el ancho). La cabecera se ajusta a varias líneas. Altura mínima del lienzo: 310px. |
| <640px | Márgenes de 20px. La cabecera se ajusta a varias líneas; herramientas del encabezado a todo el ancho; H1 y opción para guardar se apilan. Las áreas se apilan según el orden del DOM: biblioteca → vista previa → inspector, separadas por bordes. El navegador de áreas ocupa una fila (iconos ocultos, padding de 12px). Registros `64px | 1fr | 16px`. Altura mínima del lienzo: 270px. El botón de la barra inferior y las acciones de los diálogos ocupan todo el ancho; diálogos con padding/radio de 24px. La opción para guardar desplaza el campo Nombre a la vista y le da el foco. |

Sin desplazamiento horizontal de la página; el texto se ajusta (`overflow-wrap:anywhere`); ningún contenedor de texto con altura fija recorta el contenido. Los diálogos miden `min(580px, 100vw−40px)` (AlertDialog de 540px), con altura máxima `100svh−48px` y desplazamiento interno.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA; se verificará en la implementación renderizada.

- Regiones: `header`, `nav` del producto «Navegación del producto», `section` «Biblioteca del Taller», `nav` «Zonas de la biblioteca», `nav` «Origen de las decoraciones», sección de biblioteca con etiqueta, sección de vista previa y `aside` del inspector («Ficha» / «Guardar en mi biblioteca»). El elemento de zona «Guardar» y el «Guardar» del formulario comparten un nombre, pero están dentro de regiones con etiquetas distintas.
- Teclado: todos los controles son accesibles en el orden del DOM; las áreas pueden recibir foco mediante programación (`tabindex=-1`) y son destinos del navegador; Escape cierra el panel de cuenta y los diálogos (y devuelve el foco).
- Semántica de estado: selección de registro y origen mediante `aria-pressed`; área actual mediante `aria-current`; carga con `aria-busy` + `role=status`; acciones pendientes y éxito con `role=status`; errores con `role=alert`; nombre no válido con `aria-invalid` + `aria-describedby` asociado al error.
- Contraste: texto ≥4.5:1; bordes de controles, anillo de foco e indicadores de selección ≥3:1 en ambos temas (bordes `--texto-tenue`, foco `--acento`).
- Tamaño objetivo ≥44×44px; adaptación a 320px sin desplazamiento horizontal; el zoom del 200–400% queda como verificación de producción.
- Las ilustraciones usan `aria-hidden`; las etiquetas visibles identifican la vista previa.
- Movimiento reducido según §4.

## 11. Criterios de aceptación visual y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | ≥1100px | normal | La biblioteca, la vista previa y el inspector aparecen en tres columnas contiguas dentro de un panel de trabajo con borde, debajo del encabezado y la regla de ruta «Taller 3D»/«Proyectos», que permanecen sin cambios. |
| UI-AC-02 | 640–1099px | normal | La biblioteca queda a la izquierda; la vista previa, arriba a la derecha; y el inspector, debajo de la vista previa. |
| UI-AC-03 | <640px | normal | La biblioteca, la vista previa y el inspector se apilan en ese orden; el navegador de áreas cabe en una fila y no hay desplazamiento horizontal de página a 320px. |
| UI-AC-04 | all | save-scene / save-piece | Los campos etiquetados «Nombre» y «Ocasión» están visibles y la etiqueta de la vista previa dice «La escena entera» o «La pieza sola». |
| UI-AC-05 | all | saving | Se muestra «Guardando en mi cuenta…», el botón principal está deshabilitado y no aparece el texto «Guardado en mi cuenta». |
| UI-AC-06 | all | saved | Se muestran «Guardado en mi cuenta» y «Ver en mi biblioteca»; después de «Ver en mi biblioteca», el nuevo registro aparece en «En mi cuenta». |
| UI-AC-07 | all | save-failed | Se muestran juntos la nota de error, los valores conservados de nombre y ocasión, y «Reintentar guardar». |
| UI-AC-08 | all | empty | Para la fuente de la cuenta, se muestra «Tu biblioteca está vacía» con «Guardar toda la escena»; «En este navegador» sigue mostrando sus propios registros. |
| UI-AC-09 | all | staff (foreign) | Se muestran «Solo lectura» y el propietario; «Renombrar», «Editar» y «Quitar de mi biblioteca» no están presentes en el DOM; «Añadir a mi escena» sí está presente. |
| UI-AC-10 | all | placed | Aparece «Copia añadida a tu escena.» y el registro original sigue en la lista y seleccionado. |
| UI-AC-11 | all | account-switch | El nombre, la miniatura, el propietario y la vista previa de ningún registro de la cuenta anterior están en el DOM; se muestran esqueletos y «La biblioteca anterior ya no se muestra.». |
| UI-AC-12 | all | browser source | «En este navegador» muestra «Solo en este navegador. No se importan a tu cuenta.» y no existe ningún control ni estado de importación. |
| UI-AC-13 | all | loading | Tres filas de esqueleto reemplazan los registros; el inspector no tiene acciones para los elementos. |
| UI-AC-14 | all | validation | Si «Nombre» está vacío, se muestra «Escribe un nombre.», vinculado mediante `aria-describedby`, y el foco queda en el campo. |
| UI-AC-15 | all | list-error | «No se pudo cargar tu biblioteca.» con «Reintentar» reemplaza la lista; no se muestra ningún registro. |
| UI-AC-16 | all | unsupported | Se muestra «Esta pieza no se puede guardar sola.» y «Guardar» está deshabilitado. |
| UI-AC-17 | all | no results | Con una búsqueda sin coincidencias, aparecen «Sin resultados» y «Limpiar filtros»; al activarlo, se restablece la lista. |
| UI-AC-18 | all | remove dialog | «Cancelar» cierra el AlertDialog, el elemento permanece seleccionado y el foco vuelve a «Quitar de mi biblioteca». |
| UI-AC-19 | all | rename confirmed | Tras la confirmación, el nuevo nombre aparece en el registro y en el encabezado de la ficha, y el foco vuelve a «Renombrar». |
| UI-AC-20 | all | action-error | Se muestra la nota de error con «Reintentar» y el elemento permanece en la lista. |
| UI-AC-21 | all | light/dark, ES/EN | Solo se usan los tokens de §4 y Geist; todo el texto cabe en su columna sin recortarse. |
| UI-AC-22 | all | reduced motion / still | El contenido final se muestra de inmediato, sin animaciones en curso; no gira ningún indicador de carga. |
| UI-AC-23 | ≥1100px | normal, first render | La biblioteca entra desde la izquierda, el inspector desde la derecha y el objeto de la vista previa gira al entrar; la animación termina en ~640ms + retraso escalonado (expresivo). |
| UI-AC-24 | all | any | Todos los controles interactivos miden ≥44px de alto y muestran el contorno de foco de acento de 3px al recibir el foco del teclado. |

Verificación del HTML canónico generado en esta finalización (el TSX seleccionado es idéntico byte por byte; no hay parches de código fuente, fallback ni HTML):

- Compilación: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build design/decoraciones@v1.r3.dir-b.tsx --out design/decoraciones@v1.html` → 651 KB, 2,135 archivos fuente, sin conexión, código de salida 0. Espacio de trabajo: instalado, compilado, 96/96 entradas.
- Contraste: `python3 <kit>/kit/contrast.py design/decoraciones@v1.html` → 158 pares en modo claro y oscuro; todos aprobados, código de salida 0.
- Auditoría: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py design/decoraciones@v1.html` → 240 renderizados (240 planificados), 9,804 mediciones de texto, 1,567 paradas de foco, código de salida 0. **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento.**
- Prueba de comportamiento (Playwright integrado, `?still=1`, 1280px): la vista del personal sobre cuenta ajena tiene 0 acciones de Renombrar/Editar/Quitar y muestra 2 «Solo lectura»; al colocar desde la vista del personal aparece la nota de copia; al guardar la escena, el estado pendiente muestra 0 etiquetas de guardado anticipadas y luego «Guardado en mi cuenta» y el estado `saved`; `account-switch` tiene 0 registros y 0 nombres anteriores; la fuente del navegador muestra solo la indicación de que no se importa; no hay errores de página ni solicitudes de red.
- Defecto conocido, solo de la maqueta (no corregido; véase §12): después de «Cerrar sesión» → «Continuar · cuenta de ejemplo», al cambiar el estado de inspección a `normal` se muestra «Sin resultados» en lugar del estado vacío, porque cerrar sesión vacía el fixture compartido. La regla de §8 (`empty`) rige la implementación; al recargar se restablece la maqueta.

| Artefacto | SHA-256 |
|---|---|
| `design/decoraciones@v1.r3.dir-b.tsx` | `5756ac1a85b7cf44d833d8a0d4dce118b349a281ee25251564b0cb24096fd74f` |
| `design/decoraciones@v1.r3.dir-b.html` (exploración) | `5275c3628551b64348b7fee6b7bff475310cc82629c985fd1b32d77c0c098078` |
| `design/decoraciones@v1.html` (reconstrucción canónica) | `7cd8693d0d4d0eef1dc2d5e07c75893a5dda1267c9991473a980f0b1eac03ae6` |

Los selectores de inspección de la maqueta son `view` (biblioteca, save-scene, save-piece, staff), `state` (12 estados anteriores), `scene` (none, rename, edit, delete) y `theme`. Los fixtures estáticos no demuestran persistencia, recuperación entre navegadores, autorización, generación de miniaturas ni la regla de eliminación de cuentas; eso corresponde a T5.2, T5.4 y T5.6.

## 12. Preguntas abiertas y supuestos

Preguntas abiertas:

- Q1 (propietario/Planner): ¿Desde qué opción existente abren Empleado interno y Administrador la biblioteca de otra cuenta: desde el selector «Propietario» dentro de la biblioteca del Taller (como se muestra), o desde la sección de administración de cuentas? El selector aquí es provisional y no constituye una regla de autorización.
- Q2 (propietario/Planner): ¿«Editar» cambia solo el nombre y la ocasión (como se muestra), o el propietario también debe poder reemplazar la composición guardada? Hasta recibir una respuesta, T5.3 implementa la edición solo de metadatos y no permite reemplazar el contenido.
Decisiones confirmadas: no se importa `taller3d:biblioteca-propia:v1` (ronda 11 q1); las entradas locales permanecen intactas en «En este navegador»; las nuevas guardadas pertenecen a la cuenta con sesión iniciada; solo se muestra «Guardado» después de la confirmación del servidor; el acceso del personal a otras cuentas es de solo lectura y al colocar se crea una copia propia (ronda 11 q2); solo el propietario actualiza o elimina; la biblioteca requiere acceso al Taller; el catálogo global permanece separado; las cuentas con decoraciones guardadas no se pueden eliminar, solo desactivar (consecuencia para la administración de cuentas; aquí no se agrega ningún control).

Supuestos: la eliminación local del navegador usa el mismo AlertDialog y se completa de inmediato, sin llamada al servidor; un nombre no vacío después de quitar espacios en los extremos es la única validación al guardar; se reutiliza la taxonomía de ocasiones existente (la maqueta muestra General y Cumpleaños como subconjunto); las opciones de filtro de color/globo son las existentes (el subconjunto de la maqueta es ilustrativo); «Continuar · cuenta de ejemplo» y los avisos de alcance de la maqueta son ayudas de inspección, no flujos del producto.
