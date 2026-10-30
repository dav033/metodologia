---
contract: herramientas-chat
version: 1
status: draft
subplan: SP-7
requirements: [R13, R16]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: a
name: Operación en paralelo
source_revision: r2
source_behavior: herramientas-chat@v1.r2.behavior.md
plan_revision: 17
---

# herramientas-chat@v1 — Operación en paralelo

## 1. Identidad y trazabilidad

Borrador de planificación canónico; no está aprobado para implementación. El propietario eligió la dirección a, «Operación en paralelo» (revisión r2, barra lateral izquierda de herramientas), mediante la comparación en la web. Esa elección autoriza esta finalización; no aprueba el contrato, el subplan ni el plan. Esta es la versión 1; no existe una versión predecesora aprobada. Los únicos entregables de diseño de esta tarea son `design/herramientas-chat@v1.md` y `design/herramientas-chat@v1.html`. No se modificaron la exploración, el historial, SPEC, PLAN, archivos de producción, el registro de cambios del contrato ni la vista previa.

Alcance: REQ-021 / M2 / SP-7 «Chat asistido como tres herramientas y explorador de decoraciones», según SPEC (estado listo; rondas 10 y 15), revisión 17 de PLAN.json, `herramientas-chat@v1.r2.behavior.md` y los archivos Markdown, JSON, TSX y HTML de la dirección r2 elegida. Este contrato especifica la interfaz de la página principal de herramientas, el contador de globos, la calculadora de costos, la galería de decoraciones y la barra lateral de herramientas. No especifica el catálogo de herramientas, el control de acceso del servidor, la API del contador, el etiquetado de gastos ni la cotización de Python, que corresponden a T7.2–T7.4.

| Requisito | Cobertura del contrato | Tareas consumidoras |
|---|---|---|
| R13 — chat asistido dividido en calculadora de costos, contador de globos y chat normal; el chat se conecta al taller 3D | V0–V3, V5, F1–F4, F6, estados del contador/calculadora, UI-AC-01–23, 30–31 | T7.5, T7.6, T7.7; revisión T7.10 |
| R16 — cada plan otorga exactamente sus herramientas, de forma acumulativa; el personal tiene todas las herramientas | listas de herramientas por rol V0/V1, página de acceso denegado V7, F1, UI-AC-02–05, 26 | T7.5 (solo interfaz; la aplicación de permisos en el servidor corresponde a T7.2/T7.4) |
| Criterios del producto de la galería (`decoraciones.explorar`) | V4, V6, D1, F5, estados de la galería, UI-AC-24–29 | T7.8; revisión T7.10 |

Consumidores de PLAN: SP-7 `ui.contract=herramientas-chat`, `ui.version=1`, `design_task=T7.1`, `visual_review_task=T7.10`; tareas de implementación de interfaz T7.5 (página principal, retiro del chat clásico), T7.6 (contador), T7.7 (calculadora), T7.8 (galería). T7.1 copia únicamente el artefacto aprobado por el propietario. T7.9 (prueba e2e del navegador) y T7.11 (auditoría) verifican el comportamiento, no este contrato visual.

**Cambios respecto a la exploración r2 elegida.** Se conservan la composición, la navegación, los textos, los estados y el movimiento. El HTML canónico se reconstruyó con el generador sin conexión actual, a partir de una copia del TSX de r2 con dos defectos de diseño verificados corregidos (ambos eran visibles en el artefacto r2; ver §11):

1. *La división de cotización nunca se apilaba por debajo de 1100px de ancho de ventana.* Una regla posterior `@media (max-width:1099px){.quote-grid{grid-template-columns:minmax(0,1fr) 300px}}` anulaba la consulta de contenedor que apila la cotización cuando el ancho de la columna principal es ≤760px. A 390px, la columna de materiales tenía 48px de ancho y sus etiquetas, botones y «Gastos y ganancia» se ajustaban letra por letra debajo de los totales. Se eliminó la regla que anulaba la consulta; ahora rige la regla de contenedor del contrato (§9).
2. *El precio por paquete se recortaba en teléfonos.* Por debajo de 640px, la fila de materiales usaba `minmax(0,1fr) 88px`, por lo que «15000»/«20000» no cabían en el campo de COP / paquete (45–49px de texto en 38px). Ahora, en teléfonos, la fila tiene dos columnas iguales (Paquetes | COP / paquete).

No hubo otros cambios de código fuente. El código fuente corregido y su diff se conservan como evidencia de delegación (`.state/delegations/D-20261029-121224-c92f/herramientas-chat@v1.final.{tsx,diff}`), no como archivos de diseño. La barra de título y el pie del artefacto todavía dicen «Operación en paralelo · r2 A» / «Exploración operativa, borrador r2»; estos son elementos gráficos de procedencia, no textos del producto.

**Impacto:** contrato nuevo; no existe una implementación aprobada, así que no se requiere migrar consumidores. T7.5–T7.8 implementan conforme a este contrato; T7.10 lo revisa según §11. La barra lateral izquierda de herramientas solo aparece en la página principal de herramientas y en las páginas de herramientas de SP-7; los contratos hermanos `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` conservan la fila horizontal de rutas (pregunta abierta Q1).

Evidencia del producto de solo lectura usada en la exploración: t12 `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/components/guiado/VistaGuiada.tsx`, `src/components/cotizacion/{CotizacionProfesional,CampoGanancia,PreciosMateriales}.tsx`, `src/components/tres-d/{IdeasDelAsistente,Biblioteca}.tsx`. Esta finalización no reabrió decisiones del producto.

## 2. Propósito y usuarios

Usuarios: cuentas autenticadas de tipo Usuario en uno de cuatro planes (Entusiasta, Designer, Designer Plus, Master Designer) y personal (Empleado interno, Administrador). El personal tiene todas las herramientas.

| Vista | Objetivo del usuario | Éxito observable |
|---|---|---|
| V0 Barra lateral de herramientas | Moverme entre mis herramientas sin volver a la página principal | Solo aparecen mis herramientas; la actual está marcada; al elegir otra, cambia en el mismo lugar y enfoca su título. |
| V1 Página principal `/` | Ver qué puedo usar y abrirlo | Una tarjeta por cada herramienta otorgada, cada una con Abrir; sin tarjetas bloqueadas, deshabilitadas ni de venta adicional. |
| V2 Contador `/contador` | Saber cuántos globos necesita una decoración, según tamaño y color, y qué comprar | Cantidad total, tabla por tamaño/color y lista de compras, nunca un precio; los resultados fotográficos están etiquetados como estimaciones. |
| V3 Calculadora `/calculadora` | Calcular el precio profesional de una decoración | Los precios/cantidades de paquetes, mano de obra, transporte/equipo, costos indirectos y ganancia editables generan subtotales por material, desglose de costos y precio para el cliente. |
| V4 Galería `/3d/decoraciones` | Encontrar una decoración lista y empezar un proyecto nuevo a partir de ella | Catálogo filtrado con vista previa integrada; «Abrir como proyecto nuevo» abre `/3d?decoracion=<id>` como una escena nueva sin guardar. |
| V5 Chat `/asistente` (existente) | Mantener la conversación guiada | Flujo sin cambios; sin contenido de precios cuando falta costos.usar; enlaces al contador, a la calculadora (con costos) y al Taller (con Taller). |
| V6 Taller `/3d` (existente, contexto) | Acceder a la galería desde el editor | Una entrada «Decoraciones»; el editor no cambia. |
| V7 Sin acceso | Entender que no puedo abrir esta herramienta | Denegación sin datos ni mención de ningún plan; opción para volver a las herramientas. |

## 3. Arquitectura de la información y jerarquía

Estructura global, sin cambios respecto de las páginas hermanas, de arriba abajo: encabezado de Pictures/Sempertex (marca de anillo y punto, “Pictures”, “Sempertex” en Geist Mono), selector de idioma y menú desplegable «Mi cuenta» (Cuenta de ejemplo, Cambiar tema, Mi cuenta, Planes, Cerrar sesión) → área de contenido → pie de página.

Área de contenido en páginas de herramientas: **barra lateral izquierda de herramientas (V0)** | **columna principal**. Orden de la columna principal: H1 + acción de página opcional (galería: «Volver al Taller») → línea de estado (cuando corresponda) → una “hoja” (superficie de trabajo redondeada) que contiene la vista.

- Orden de la barra lateral: etiqueta de grupo «Herramientas de tu cuenta»; «Herramientas» (inicio, separado por una línea); luego las herramientas habilitadas, en el orden del catálogo: Chat, Contador de globos, Calculadora de costos, Catálogo, Taller 3D; «Decoraciones» anidada bajo Taller 3D. Las herramientas no disponibles no se muestran.
- Hoja del contador: encabezado (“Contar globos” + selector de método Formulario | Frase | Foto) → división: entradas (izquierda, 0.85) | resultado (derecha, 1.35). Orden del resultado: “Resultado” + total tabular destacado de 28px (“120 globos”) → aviso de estimación por foto (solo para Foto) → tabla de tamaño/color/cantidad → “Lista de compra” → «Calcular costo» (solo con permisos de costos).
- Hoja de la calculadora: encabezado (“Precio al cliente” + indicación “COP · Datos de ejemplo, no precios de catálogo”) → división invertida: editor de materiales + “Gastos y ganancia” + «Calcular precio al cliente» (izquierda, amplia) | “Totales” (derecha, estrecha). Orden de los totales: Materiales, Mano de obra, Transporte y equipos, Costos indirectos, Costo total, Ganancia y, por último, “Precio al cliente” destacado en 28px.
- Hoja de la galería: encabezado (“Decoraciones” + “Ideas del asistente e Ideas Sempertex”) → fila de filtros (Buscar, Ocasión, Tamaño) → división: registro de miniaturas | vista previa adyacente (nombre, tamaño, esquema, “Se abrirá como una escena nueva sin guardar.”, «Abrir como proyecto nuevo», ruta de enlace profundo).

Fundamento: las entradas y el resultado del motor permanecen visibles al mismo tiempo (concepto de dirección “operativa”); los únicos números grandes son el conteo y el precio al cliente; no hay métricas de tablero. Divulgación progresiva: el campo de foto solo aparece con el método Foto, los totales solo después de un cálculo válido y la vista previa solo para la fila seleccionada.

## 4. Sistema de diseño y lenguaje visual

Sistema fijo del proyecto; no se agregan paletas, tipografías ni marcas. Tokens (claro / oscuro): `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--borde` #e3daef/#383c48; `--borde-suave` #efe9f8/#2a2d38; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--acento-hover` #5530b8/#a58dff; `--sobre-acento` #ffffff/#120b24; `--exito`, `--aviso`, `--error` (y sus variantes `-suave`) y roles `--taller-*` según `globals.css` de t12. Los roles de shadcn se asignan una vez por tema: background/card/popover → fondo/superficie; foreground → texto; primary/primary-foreground → acento/sobre-acento; input → texto-tenue (borde de control accesible ≥3:1, heredado de las páginas hermanas); sidebar/sidebar-foreground/sidebar-accent/sidebar-border → superficie/texto/superficie-2/borde. La barra lateral renderizada se apoya sobre `--fondo` y tiene una línea divisoria derecha `--borde-suave`.

Tipografía: Geist Sans (WOFF2 local) para el cuerpo, 15px/1.5; etiquetas, 13px seminegrita; filas de tabla, 14px; encabezados de sección, 17–18px; H1, 24px; números del conteo y del precio al cliente, 28px tabulares. Geist Mono solo para la marca “Sempertex” heredada. Radios: hoja, 32px; campos, 18px; pastillas/botones, 999px; grupos internos, 24px. Relleno de panel: 24px en escritorio y 20px en teléfono. Iconos: lucide, 18px, decorativos (`aria-hidden`).

Uso del color: el acento se reserva para acciones principales y el foco. Elemento actual de la barra lateral = nivel neutro `--superficie-2` + peso 600 + `--texto`; elementos inactivos, `--texto-suave`; sin barra de color. Los errores usan avisos en tono `--error`; los precios nunca se muestran con colores de error o atención.

Foco: contorno `--acento` de 3px, con desplazamiento de 4px, en todos los elementos interactivos; H1 recibe el foco programático (tabindex −1) después de cambiar de vista.

Componentes (`origen:id variante estado`, ruta de importación):

| Componente | Uso | Importación |
|---|---|---|
| `shadcn:sidebar static(collapsible=none) default/hover/focus/current` — SidebarProvider, Sidebar, SidebarContent, SidebarGroup, SidebarMenu, SidebarMenuItem, SidebarMenuButton (se renderiza como `<a>`), SidebarMenuSub/SubItem/SubButton | Barra lateral de herramientas V0 | `@/components/ui/sidebar` |
| `shadcn:button default enabled/hover/focus/pressed/disabled/loading` | Principal: Contar globos, Calcular precio al cliente, Abrir como proyecto nuevo, Enviar | `@/components/ui/button` |
| `shadcn:button outline enabled/hover/focus/pressed` | Abrir, Calcular costo, Añadir material, Restaurar precios de catálogo, Vista previa, Volver…, Intentar de nuevo, acciones secundarias del diálogo, alternador de la barra lateral en teléfono | `@/components/ui/button` |
| `shadcn:input default editing/invalid/disabled` | Medidas, producto, paquetes, COP / paquete, costos, ganancia, búsqueda de galería | `@/components/ui/input` |
| `shadcn:textarea default editing` | Entrada de Frase, mensaje de chat | `@/components/ui/textarea` |
| `shadcn:skeleton default loading` | Carga del conteo, cálculo y galería | `@/components/ui/skeleton` |
| `shadcn:alert-dialog default open/closed` (implementación instalada de Animate UI/Base UI) | Confirmación de trabajo sin guardar D1 | `@/components/ui/alert-dialog` |
| `custom:method-switch` (grupo de botones, `aria-pressed`) | Formulario/Frase/Foto | HTML semántico + tokens |
| `custom:count-table` (`table` semántica, números alineados a la derecha) | Resultado del contador | HTML semántico |
| `custom:ruled-material-editor` | Filas de la calculadora | HTML semántico + entradas de shadcn |
| `custom:thumbnail-register`, `custom:scene-schematic` (SVG, ejemplo) | Galería | HTML semántico/SVG |
| `custom:notice` (`role=status` / `role=alert`) | Preguntas, errores, procedencia, notas de alcance | HTML semántico |
| `custom:tool-card` | Tarjetas de inicio | `article` semántico |
| `select` nativo | Estructura, Tamaños, Ocasión, Tamaño, Idioma | nativo |
| `custom:account-disclosure` heredado | Mi cuenta | patrón de página hermana |

Movimiento (dirección a, “cortes precisos”; solo transformaciones, contenido siempre legible): `.paper` entra 5px en vertical; los elementos de la barra lateral `.tool-nav-item` y las filas `.count-line` entran 8px en horizontal, con un intervalo escalonado de 35ms; el indicador de herramienta actual (`.tool-marker`, diseño compartido de Motion con `layoutId`) se desliza entre elementos de la barra lateral; `.result-panel` entra desde el borde opuesto (8px); `.preview-stage` aparece con escala .985; los cambios de método se desplazan 3px; el chevrón del alternador para teléfono gira 180°; las flechas de los botones se desplazan 3px al pasar el cursor; los botones escalan a 1.025 al pasar el cursor y a .965 al presionarlos. Perfiles: expresivo, 280ms (controles repetidos, 150ms); natural, 200/140ms; sutil, 130/110ms; curva de aceleración cubic-bezier(.23,1,.32,1). Sin bucles infinitos. Movimiento reducido (sistema operativo, «Quieto», `?still=1`): elimina desplazamientos, escalas y transiciones; el indicador se mueve con duración cero.

## 5. Navegación y modelo de interacción

- **Entrada:** después de iniciar sesión, se llega a `/` (V1). La página de chat clásica que antes estaba en `/` se retira; `/api/chat` sigue ofreciendo el chat guiado.
- **Navegación persistente:** barra lateral V0 en V1–V4, V6–V7 y V5. Los elementos son enlaces (`/`, `/asistente`, `/contador`, `/calculadora`, ruta existente del catálogo, `/3d`, `/3d/decoraciones`). Al elegir un elemento, se navega dentro de la aplicación, se establece `aria-current="page"`, se desliza el indicador y el foco pasa al H1 de la página. Decoraciones es el elemento actual en V4; Taller 3D, en V6.
- **Listas según el rol (las herramientas no disponibles nunca se deshabilitan ni se nombran):**

| Cuenta | Elementos de la barra lateral después de «Herramientas» | Tarjetas de inicio |
|---|---|---|
| Entusiasta | Chat, Contador de globos | “Chat con límites”, Contador de globos |
| Designer | Chat, Contador de globos | “Chat con límites más altos”, Contador de globos |
| Designer Plus | + Calculadora de costos | + Calculadora de costos |
| Master Designer, Empleado interno, Administrador | + Catálogo, Taller 3D › Decoraciones | + Catálogo, Taller 3D |

- **Teléfono (ventana gráfica <840px):** la barra lateral se contrae a un alternador de contorno de ancho completo «Herramientas · <tool>» (se omite el texto secundario en el inicio) con `aria-expanded`/`aria-controls="tool-list"`. Abre la misma lista en el flujo, sobre el encabezado (sin cajón ni superposición). Al elegir una herramienta, la lista se cierra y el foco pasa al H1; Escape dentro de la lista la cierra y devuelve el foco al alternador.
- **Enlaces entre herramientas:** resultado del contador «Calcular costo» → V3 con datos importados (solo con permisos de costos). Acciones de respuesta del chat: «Lista de compra» → resultado V2; «Abrir en Taller 3D» (solo con Taller); «Calcular costo» (solo con permisos de costos). V3 vacío «Ir al contador» → V2. V6 «Decoraciones» → V4. V4 «Volver al Taller» → V6. Abrir V4 → escena nueva sin guardar en V6 (mediante D1 si hay trabajo sin guardar). V7 «Volver a herramientas» → V1.
- **Catálogo:** destino existente fuera de SP-7; este contrato solo lo enumera (Q4).
- **Controles dentro de la página:** el selector de método cambia las entradas en el mismo lugar y restablece el resultado al estado inactivo; «Vista previa» de la galería selecciona una fila y actualiza la vista previa adyacente sin navegar (la fila seleccionada muestra una marca de verificación).

## 6. Flujos

**F1 — Iniciar sesión y abrir una herramienta (R16).** Iniciar sesión → V1 muestra solo las herramientas del rol (tabla §5) → Abrir o la barra lateral abre la página de la herramienta y enfoca el H1. URL directa a una herramienta no habilitada → V7.

**F2 — Contar mediante formulario (R13).** V2 Formulario: Estructura (Arco/Guirnalda/Columna), Ancho (m), Alto (m), Tamaños, Colores → «Contar globos». Medida faltante/no positiva → aviso `question` «¿Cuánto mide la decoración?» con «Añadir medidas». Datos válidos → `loading` (botón «Contando…», deshabilitado; esqueleto; “Contando globos…”) → `result`: total, filas por tamaño/color, lista de compra. Sin cantidad de dinero, moneda, precio total ni cotización, sin importar el nivel de permisos. Fallo del motor → `error` con «Intentar de nuevo»; se conservan las entradas.

**F3 — Contar mediante frase o foto (R13).** Frase: área de texto «Describe la decoración» (indicación “Incluye las medidas.”); una frase sin medidas → `question`; «Añadir medidas» vuelve a Frase y conserva el texto. Foto: entrada de archivo «Elegir la foto», “JPG, PNG o WebP de menos de 6 MB.”, “El conteo de una foto es una estimación.”; si no hay archivo → estado “Elige una foto para seguir.”; archivo que no es imagen → `photo-type` (“El archivo no es una imagen. Usa JPG, PNG o WebP.”); ≥6 MB → `photo-large` (“La foto supera el tamaño permitido. Usa una foto de menos de 6 MB.”); ambos casos ofrecen «Elegir otra foto». Éxito → `photo-estimate`: resultado más “Estimación por foto” con el margen de tolerancia proporcionado por el motor (Q5).

**F4 — Calcular el precio de una decoración (R13, costos).** Desde F2, «Calcular costo» → V3 `imported` (aviso “Materiales del contador” que resume los materiales contados); o abrir V3 directamente → `empty` (“Añade materiales o usa el resultado del contador.”, «Añadir material», «Ir al contador»; cálculo deshabilitado hasta que haya un material). Editar Producto · paquete, Paquetes, COP / paquete; agregar/eliminar filas (el nombre accesible de eliminar es “Quitar material N”); «Restaurar precios de catálogo»; Mano de obra, Transporte y equipos, Costos indirectos (COP), Tu ganancia (%) con “Tu ganancia se suma a lo que te cuesta todo (materiales y tus gastos).” Cualquier edición → `editing`: se ocultan los totales anteriores, “Los valores cambiaron. Vuelve a calcular para ver una cotización vigente.” «Calcular precio al cliente» valida los campos (validación nativa) y luego pasa a `loading` → `totals`. Error en la cotización → `error` (“No pude calcular la cotización”, “Los datos escritos se conservan. Inténtalo de nuevo.”, «Revisar datos»). Python es responsable de los totales; la ganancia se suma al costo total (semántica de CampoGanancia), no es un margen bruto.

**F5 — Abrir una decoración prediseñada (galería).** V6 «Decoraciones» o la barra lateral → V4. Buscar, Ocasión y Tamaño filtran el registro en tiempo real; si no hay coincidencias → “Sin resultados”, “Prueba otra búsqueda o cambia los filtros.”, «Limpiar filtros». «Vista previa» selecciona una fila. «Abrir como proyecto nuevo» → `/3d?decoracion=<id>` abre una escena nueva sin guardar; el proyecto abierto anteriormente conserva su identidad y no se sobrescribe. Si hay trabajo sin guardar en Taller → primero D1. ID desconocido → “Decoración no encontrada”, “La escena abierta no cambió.”, «Volver a decoraciones». Error de carga → “No pude cargar las decoraciones”, “El trabajo del Taller se conserva.”, «Intentar de nuevo».

**F6 — Chat guiado (R13).** V5 conserva la conversación existente. Las respuestas incluyen conteos y el enlace a la lista de compra, pero no incluyen precio, total ni cotización sin costos.usar, y nunca indican qué plan incluye costos. Si la cuenta tiene Taller, «Abrir en Taller 3D» conecta el chat con el taller.

**F7 — Acceso denegado.** Ruta sin permisos o enlace profundo a la galería sin `decoraciones.explorar` → V7: “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». Sin datos, nombre del plan ni invitación a mejorar el plan. La barra lateral sigue mostrando solo las herramientas de la cuenta.

**D1 — Protección ante trabajo sin guardar (reutiliza proyectos@v1).** Título “Tienes cambios sin guardar”; descripción “Guarda el proyecto actual antes de abrir una decoración como proyecto nuevo. La escena abierta se conserva hasta que decidas.”; acciones Cancelar, Guardar y continuar, Descartar escena y continuar. Cancelar/Escape cierra y devuelve el foco a «Abrir como proyecto nuevo», que lo invocó (con el H1 como alternativa). Guardar continúa solo después de confirmar el guardado (las reglas de guardado, reintento y primer nombre corresponden a proyectos@v1 / SP-4); si el guardado falla o está pendiente, se conserva la escena y no se navega. Descartar abre la escena nueva sin guardar.

## 7. Especificaciones de vistas

| Vista | Estructura y contenido | Acciones | Adaptable |
|---|---|---|---|
| V0 Barra lateral | `nav` “Herramientas de tu cuenta”; elementos con icono lucide + etiqueta (House, MessageCircle, ListChecks, Calculator, LayoutGrid, Box; Images para Decoraciones); inicio separado por una línea; Decoraciones con sangría bajo Taller 3D y una guía vertical. Actual: píldora superficie-2, peso 600. | Navegar; alternador para teléfono | Columna de 248px ≥840px, fija al desplazarse; alternador <840px |
| V1 Inicio | H1 “Herramientas”; panel con fila introductoria “Herramientas de tu cuenta”; lista con líneas divisorias de `tool-card`s: icono, nombre (h2), descripción (Asistente guiado / Formulario, frase o foto / Precio al cliente / Explorar catálogo / Decoraciones y proyectos), «Abrir →». | Abrir cada una | Las tarjetas se apilan; Abrir debajo del texto en teléfono |
| V2 Contador | Orden de §3. Campos del formulario en grupos de dos columnas (Ancho/Alto). Encabezados de tabla Tamaño · Color · Cantidad. Lista de compra “<Color> · <size>” / “N unidades”. Texto del resultado en reposo: “Cuenta por formulario, frase o foto para ver los globos por tamaño y color y la lista de compra.” | Cambiar método, Contar globos, Añadir medidas, Elegir otra foto, Intentar de nuevo, Calcular costo (costos) | Las secciones divididas se apilan cuando la columna principal mide ≤640px; resultado después de las entradas |
| V3 Calculadora | Orden de §3. Fila de material: Producto · paquete de 50 (ancho completo) / Paquetes / COP / paquete / eliminar; línea de subtotal por fila. Cuadrícula de campos de costos. Lista de totales con filas divisorias y precio al cliente destacado. La indicación de datos de prueba aclara que los valores son ejemplos. | Añadir material, eliminar fila, Restaurar precios de catálogo, Ir al contador, Calcular precio al cliente, Revisar datos | La cotización se apila cuando la columna principal mide ≤760px (totales debajo del editor); en teléfono, filas: producto a ancho completo, luego Paquetes | COP / paquete en mitades |
| V4 Galería | Fila de filtros (campo Buscar con marcador de posición “Buscar decoraciones”, Ocasión, Tamaño); filas del registro: miniatura esquemática, nombre (el seleccionado aparece subrayado), origen (Ideas del asistente / Ideas Sempertex), tamaño · “Datos de ejemplo”, «Vista previa» (marca cuando está seleccionado); vista previa: nombre, tamaño · “Escena de ejemplo”, esquema, nota de apertura, acción principal, texto de ruta. | Filtros, Limpiar filtros, Vista previa, Abrir como proyecto nuevo, Volver al Taller, Volver a decoraciones, Intentar de nuevo | Las secciones divididas se apilan cuando la columna principal mide ≤640px; el registro aparece antes que la vista previa; la acción de apertura se ajusta a varias líneas |
| V5 Chat (existente) | “Asistente guiado”; burbujas de usuario/asistente; respuesta “Tu plan está listo: 120 globos.” + “12″ · Blanco y dorado” y acciones sujetas a permisos; compositor (Mensaje, Enviar). Solo contexto. | Lista de compra, Abrir en Taller 3D (Taller), Calcular costo (costos) | Comportamiento existente sin cambios |
| V6 Taller (contexto) | Encabezado de proyecto existente (“Sin guardar”), «Decoraciones», «Guardar proyecto», barra lateral de paneles existente (Escena, Piezas, Sala, Biblioteca). No rediseñado. | Decoraciones | Existente |
| V7 Sin acceso | Panel con aviso de error (§6 F7). H1 conserva el nombre de la herramienta solicitada. | Volver a herramientas | Igual en todos los anchos |

Reglas de texto: interfaz en español; cada cadena nueva va en un módulo `textos-*.ts` por pantalla (SP-10 traduce). Los nombres de herramientas provienen de plan-catalogue@1. Las cantidades y los precios son los del motor/catálogo; todos los números del artefacto (120, 60/60, 15.000/20.000 COP, 30.000/10.000/5.000 COP, 20 %, tamaños, nombres de decoraciones) son datos de prueba ilustrativos y no deben publicarse. Las cadenas con prefijo “Mockup ·”, el selector de cuenta de prueba (“Mockup · Cuenta”) y los textos “Datos de ejemplo” son elementos de la simulación, no textos del producto. Las unidades se mantienen en cm/m; los precios, en COP en ambos idiomas.

## 8. Estados

Los valores de `state` del inspector son globales; cada vista los adapta localmente y, para los valores no pertinentes, vuelve a su estado base. `denied` se puede alcanzar desde todas las vistas y también se activa con la cuenta de prueba.

| Estado | Vistas | Qué aparece / qué se puede hacer / recuperación |
|---|---|---|
| `ready` (en reposo) | V2 | Entradas + explicación del resultado en reposo. V3 se adapta a `empty` (o `imported` después de transferir). Resultados de V4. |
| `empty` | V2, V3 | V2 como en reposo. V3 muestra un mensaje de ingreso manual, Añadir material / Ir al contador, y el cálculo está deshabilitado. V6 después de abrir: escena nueva sin guardar. |
| `question` | V2 | Aviso en el área de resultados “¿Cuánto mide la decoración?” / “Falta una medida para contar los globos.” + Añadir medidas. |
| `loading` | V2, V3, V4 | Esqueleto con la forma del resultado, texto de estado no intrusivo, `aria-busy`; acción principal deshabilitada con etiqueta progresiva (Contando…/Calculando…). |
| `result` | V2 | Total, filas, lista; Calcular costo solo si hay costos. |
| `photo-estimate` | V2 | Resultado + “Estimación por foto” + texto sobre el margen de tolerancia proporcionado por el motor. |
| `photo-large` / `photo-type` | V2 | Alerta “No pude leer tu foto” con el motivo específico + Elegir otra foto. |
| `error` | V2, V3, V4 | Alerta con opción para volver a intentar; se conservan las entradas y la escena abierta; no se inventa un resultado exitoso en caché. |
| `imported` | V3 | Aviso de procedencia “Materiales del contador”; filas rellenadas previamente; los totales requieren un cálculo. |
| `editing` | V3 | Explicación de que los totales están desactualizados; se ocultan los totales anteriores; es necesario recalcular. |
| `totals` | V3 | Subtotales por fila, desglose de costos, Ganancia, Precio al cliente. |
| `no-results` | V4 | “Sin resultados” + Limpiar filtros. |
| `unknown` | V4 | Alerta de elemento no encontrado, escena sin cambios, Volver a decoraciones. |
| `unsaved` | V4 | Estado “El Taller tiene cambios sin guardar.” debajo de la acción de apertura; abrir activa D1. |
| `denied` | todas | V7. |
| Diálogo `scene=unsaved` | V4 | D1 abierto. |

No aplicables: inicio vacío/en carga/con error (cada rol tiene al menos una herramienta y la lista se renderiza desde el servidor según el rol — confirmado en el brief); modo sin conexión como estado separado (los errores del motor/cotización/galería cubren respuestas no disponibles); herramientas deshabilitadas (por regla, las herramientas bloqueadas no aparecen).

## 9. Comportamiento adaptable

Rango compatible: 360px en adelante; comprobado en 1280, 1024, 768 y 390px. Los diseños divididos dependen del **ancho de la columna principal** (contenedor CSS `main`, inline-size), no del viewport.

- **Viewport ≥1100px:** márgenes exteriores de 40px; encabezado de ancho completo; barra lateral de 248px + espacio de 32px, fija al desplazarse debajo del encabezado; el contador y la galería se dividen; la cotización se divide cuando la columna principal mide >760px (a 1280px, la columna principal mide 920px).
- **840–1099px:** márgenes de 24px; barra lateral de 248px + espacio de 24px. Columna principal ≈704–780px: la cotización se apila cuando la columna principal mide ≤760px (totales debajo del editor); el contador y la galería permanecen divididos cuando la columna principal supera los 640px.
- **<840px:** la barra lateral se convierte en el alternador «Herramientas · <tool>» sobre el encabezado; la lista se despliega en el flujo; la columna principal ocupa todo el ancho. Las secciones divididas se apilan cuando la columna principal mide ≤640px.
- **<640px:** márgenes y relleno de panel de 20px; los controles del encabezado se ajustan a varias líneas; el encabezado y la acción de página se ajustan a varias líneas; la galería usa una columna, con el registro antes de la vista previa; las filas de material se convierten en campos con nombre (producto a ancho completo, Paquetes | COP / paquete en dos columnas iguales, botón para eliminar debajo); los campos de costos se apilan; las acciones del diálogo ocupan todo el ancho; Ancho/Alto permanecen en dos columnas.
- Sin desplazamiento horizontal de la página en ningún ancho compatible; las etiquetas largas se ajustan por palabra, nunca letra por letra; cada entrada muestra su valor de prueba completo.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA, sujeto a verificación de la implementación renderizada.

- Hitos: `header` para el encabezado, `nav` de la barra lateral (“Herramientas de tu cuenta”), columna `main`, `footer`. Los elementos de la barra lateral son enlaces con `aria-current="page"` en el actual.
- Alternador para teléfono: botón con `aria-expanded`, `aria-controls`; Escape cierra y devuelve el foco.
- Al cambiar de vista, el foco pasa al H1 (tabindex −1). El cambio de método usa `aria-pressed`. La selección en la galería expone el estado seleccionado en texto (el icono de marca es decorativo) y no mueve el foco.
- Cada campo tiene una etiqueta visible y programática; las etiquetas incluyen unidades (m, COP, %). Los selectores nativos conservan el comportamiento de teclado nativo. Los números no válidos usan la validación nativa / `aria-invalid` y conservan el valor.
- Regiones dinámicas: espera y comentarios con `role=status`; errores y fallos de foto con `role=alert`; carga con `aria-busy`.
- La tabla de conteo es una tabla semántica con celdas de encabezado y números alineados a la derecha.
- D1: modal, fondo inerte, foco contenido, Escape/Cancelar cierran, el foco vuelve al control que lo abrió (con H1 como alternativa).
- Contraste: texto ≥4.5:1; bordes de controles y foco ≥3:1 en ambos temas. Objetivo de altura ≥44px. Contorno de foco de 3px en color de acento, con desplazamiento de 4px.
- Adaptación a 320px CSS sin pérdida (comprobación renderizada en 360/390); zoom al 200% sin recortes.
- Movimiento reducido: sin desplazamiento ni cambio de escala; estado y datos idénticos.

## 11. Criterios de aceptación visual y verificación

“Todos” significa desde 360px en adelante, comprobado al menos en 390/768/1280px, en tema claro y oscuro. Los inspectores llegan a todos los estados; las afirmaciones funcionales (control del servidor, cifras del motor, etiquetas de gasto, guardado) requieren evidencia de T7.4/T7.9, no de este conjunto de datos de prueba.

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | Todos | Todos | El encabezado de Pictures/Sempertex, los controles Idioma y Mi cuenta y las fuentes Geist coinciden con los contratos de las vistas hermanas; no hay una fila de rutas horizontal en páginas SP-7. |
| UI-AC-02 | ≥840px | Entusiasta, cualquier vista | La barra lateral muestra exactamente Herramientas, Chat y Contador de globos. |
| UI-AC-03 | ≥840px | Designer Plus | La barra lateral añade Calculadora de costos y no muestra Catálogo, Taller 3D ni Decoraciones. |
| UI-AC-04 | ≥840px | Master/staff | La barra lateral muestra Herramientas, Chat, Contador de globos, Calculadora de costos, Catálogo, Taller 3D y Decoraciones anidado bajo Taller 3D. |
| UI-AC-05 | Todos | V1 según el rol | Inicio muestra una tarjeta por herramienta concedida con Abrir, sin tarjetas bloqueadas, deshabilitadas, de venta adicional o con el nombre de un plan. |
| UI-AC-06 | ≥840px | Cualquier vista de herramienta | El elemento actual de la barra lateral tiene un fondo neutro superficie-2, peso 600 y `aria-current=page`; sin barra de color. |
| UI-AC-07 | Todos | Al cambiar de herramienta | Al elegir un elemento de la barra lateral, la vista cambia en el lugar y el foco pasa a su H1; el indicador se desliza (movimiento expresivo) o salta (movimiento reducido). |
| UI-AC-08 | <840px | Cualquier vista de herramienta | La barra lateral es un alternador de ancho completo «Herramientas · <tool>»; al abrirlo, muestra la misma lista sobre el H1; elegir un elemento o pulsar Escape lo cierra. |
| UI-AC-09 | 1280px | Resultado de V2 | Las entradas, el total de 120, dos filas de conteo y la lista de compra aparecen lado a lado en un panel, sin precio ni moneda. |
| UI-AC-10 | 390px | Resultado de V2 | El resultado aparece después de las entradas, a ancho completo, sin desplazamiento horizontal de la página. |
| UI-AC-11 | Todos | Cualquier V2, cualquier rol | En el contador no aparece ninguna cantidad, COP, total ni cotización. |
| UI-AC-12 | Todos | Resultado de V2, Entusiasta/Designer | «Calcular costo» no aparece. |
| UI-AC-13 | Todos | Pregunta de V2 | La pregunta sobre las medidas y «Añadir medidas» aparecen en el área de resultados. |
| UI-AC-14 | Todos | V2 photo-large / photo-type | “No pude leer tu foto” con el motivo específico y «Elegir otra foto» aparecen en el área de resultados. |
| UI-AC-15 | Todos | V2 photo-estimate | “Estimación por foto” y una línea sobre el margen de tolerancia aparecen sobre la tabla de conteo. |
| UI-AC-16 | Todos | Carga de V2/V3 | Aparecen un esqueleto y texto de estado; la acción principal muestra Contando…/Calculando… y está deshabilitada. |
| UI-AC-17 | Todos | V3 imported | El aviso “Materiales del contador” aparece sobre las filas de material rellenadas previamente. |
| UI-AC-18 | Todos | V3 editing | No se muestra ningún total; la explicación de datos desactualizados solicita recalcular. |
| UI-AC-19 | Todos | Totales de V3 | Los subtotales por fila, el desglose de costos, Ganancia y Precio al cliente de 28px coinciden con los valores editables de prueba. |
| UI-AC-20 | 1280px | Totales de V3 | El editor de materiales (ancho, a la izquierda) y los totales (estrechos, a la derecha) aparecen lado a lado. |
| UI-AC-21 | 768–1099px y 390px | Totales de V3 | Los totales se apilan debajo del editor a todo el ancho de la columna principal; ninguna etiqueta, botón ni encabezado se ajusta letra por letra. |
| UI-AC-22 | 360–639px | V3 con filas, cualquier estado | El producto ocupa todo el ancho; Paquetes y COP / paquete comparten una fila en mitades iguales y muestran todos sus valores. |
| UI-AC-23 | Todos | Error de V3 | Aparece la alerta de error de cotización, se conservan los valores de las entradas y aparece «Revisar datos». |
| UI-AC-24 | 1280px | V4 listo | El registro y la vista previa aparecen uno al lado del otro; «Vista previa» en otra fila actualiza la vista previa sin navegar. |
| UI-AC-25 | 390px | V4 listo | El registro aparece antes que la vista previa; los filtros se reorganizan; «Abrir como proyecto nuevo» se ajusta dentro del panel. |
| UI-AC-26 | Todos | V4 sin resultados | Aparecen “Sin resultados” y «Limpiar filtros». |
| UI-AC-27 | Todos | V4 desconocido | “Decoración no encontrada” indica que la escena abierta no cambió; no se sustituye la escena. |
| UI-AC-28 | Todos | V4 sin guardar + abrir | D1 muestra Cancelar, Guardar y continuar, Descartar escena y continuar; Escape/Cancelar devuelve el foco a la acción de apertura. |
| UI-AC-29 | Todos | V4/V6/V3 sin permiso | V7 muestra el rechazo y «Volver a herramientas», sin datos de decoración/cotización ni nombre de plan. |
| UI-AC-30 | Todos | V5 Entusiasta | La respuesta del chat muestra conteos y «Lista de compra», pero no muestra precio, «Calcular costo» ni «Abrir en Taller 3D». |
| UI-AC-31 | Todos | Movimiento reducido / Quieto / inmóvil | Todo el contenido y los controles están visibles, sin animaciones en ejecución una vez que la vista se estabiliza. |

**Evidencia del HTML canónico generado en esta finalización** (`design/herramientas-chat@v1.html`, SHA-256 `0b482164529ac991b2ebcc448dbd2c97fb3f13394163c4b0819b4c62b3c76725`):

| Verificación | Observación real |
|---|---|
| Kit instalado | `components status`: `installed=True built=True entries ok=96/96`. |
| Compilación sin conexión | Código de salida 0: `built … (756 KB, 2194 source files, offline)`; controles reales de React/shadcn/Base UI/Animate UI, CSS/JS insertados y Geist WOFF2 local. Sin alternativas, instalaciones ni descargas. |
| `contrast.py` | Código de salida 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría renderizada | Código de salida 0: `612 renders (612 combinations planned), 18176 text measurements, 1472 focus stops` en 1280/390/768, con ambos temas. |
| Prueba de diseño (r2 frente a final) | Columnas de `.quote-grid`, r2 → final: 1024px `402px 300px` → `702px`; 768px `418px 300px` → `718px`; 390px `48px 300px` → `348px`; 1280px sin cambios `593px 325px`. Las divisiones del contador y la galería son idénticas. Valores de entrada recortados por debajo de 640px: en r2, `price-0` 45>38px y `price-1` 49>38px → en final, ninguno entre 1280–360px. |
| Prueba de interacción | 25/25 APROBADAS: cambiar la barra lateral enfoca H1 + `aria-current`; ancho vacío → pregunta; Añadir medidas → Frase; estado de carga ocupado/deshabilitado; resultado 120; Calcular costo → importado; errores de foto no válida/no basada en imagen/≥6 MB; editar oculta los totales; recalcular muestra los totales nuevos; un error de cotización conserva los campos; seleccionar una fila actualiza la vista previa; D1 se abre con tres acciones, Escape devuelve el foco; acceso denegado a la galería no muestra datos; el control del teléfono se contrae/se abre/Escape devuelve el foco/seleccionar cierra; sin desbordamiento horizontal en 390; `?still=1`, 0 animaciones en curso; movimiento reducido del sistema operativo, 0; expresivo, 12 en curso a 120ms; cero errores de página/consola; cero solicitudes externas. |
| Prueba de restricciones de acceso | Las cinco cuentas de prueba × todas las vistas: las listas de la barra lateral coinciden con §5; el contador no muestra términos de precios para ningún rol; Calcular costo solo para Designer Plus/Master/personal; V3 denegado para Entusiasta/Designer; V4/V6 denegados por debajo de Master. |
| Inspección visual | Capturas inspeccionadas: resultado del contador en tema claro a 1280, galería en tema oscuro a 1280, inicio en tema claro a 390, totales de la calculadora a 390 (antes y después de la corrección). |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Nota: la propia auditoría de la exploración r2 también informó APROBADO aunque la calculadora se contraía por debajo de 1100px; la auditoría no detecta el ajuste de texto letra por letra dentro de una columna de cuadrícula demasiado estrecha. UI-AC-21/22 hacen que esto sea observable para T7.10.

Comandos reproducibles:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components status
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/.state/delegations/D-20261029-121224-c92f/herramientas-chat@v1.final.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.html --widths 1280,390,768 --max-combos 240
```

## 12. Preguntas abiertas y supuestos

Preguntas abiertas (responsable de la decisión: David con el Planner; los implementadores no deben inferir respuestas a partir de valores de prueba):

- **Q1** — ¿La barra lateral izquierda de herramientas también debe convertirse en la navegación global para Proyectos, Mi cuenta, Cuentas y Planes? Las secciones hermanas mantienen una fila horizontal de rutas; este contrato usa la barra lateral solo en las páginas de SP-7, por lo que quedan dos patrones de navegación.
- **Q2** — Si la barra lateral siempre está visible, ¿`/` debe conservar una tarjeta por herramienta (este contrato; coincide con el criterio del producto) o convertirse en un acceso breve a la barra lateral?
- **Q3** — Dentro del Taller (`/3d`), ¿la barra lateral de herramientas debe permanecer junto al editor (este contrato) u ocultarse para dar todo el ancho al lienzo?
- **Q4** — ¿Catálogo debe aparecer para Entusiasta/Designer/Designer Plus? planes@v1 incluye acceso al catálogo base, pero el ejemplo de aceptación de SP-7 espera solo Chat y Contador para Entusiasta; este contrato sigue el ejemplo.
- **Q5** — ¿Qué texto/valor de tolerancia devuelve el motor de conteo de fotos? El texto del artefacto “Tolerancia: pendiente del motor” es solo para el mockup y no debe publicarse.
- **Q6** — Filtro por tamaño: ¿medidas exactas o rangos acordados? “3 m / Hasta 2 m” son valores de prueba, no una taxonomía.
- **Q7** — ¿Qué nombre del chat ve el personal en la tarjeta de inicio? plan-catalogue@1 solo define los niveles del plan; el artefacto muestra “Chat con límites más altos” para Master y el personal.

Decisiones confirmadas (de SPEC/brief, no se vuelven a abrir): `/` es la página de inicio de herramientas y la página clásica de chat se retiró; tres herramientas; contador por formulario, frase o foto, sin precios; la calculadora es la cotización profesional existente, alimentada por el contador o manualmente; sin precios ni nombres de planes sin costos.usar; galería en `/3d/decoraciones`, restringida por `decoraciones.explorar` (Master Designer y personal); abrir como proyecto nuevo mediante `/3d?decoracion=<id>`; comentarios del propietario sobre r2: herramientas en una barra lateral izquierda para cambiar entre ellas.

Supuestos: las rutas son `/contador` y `/calculadora` (el brief no define la ruta del contador; la verificación de SP-7 en SPEC usa `/calculadora`). Después de descartar D1 o abrir directamente, V6 en el artefacto muestra “Proyecto de ejemplo · Sin guardar” genérico; la escena nueva real incluye la decoración (contrato taller-scene). La entrada de texto libre para materiales representa el mecanismo existente para ingresarlos; ninguna entrada libre se convierte en un producto del catálogo. Solo se simula la disposición en inglés; la traducción y la persistencia del idioma corresponden a SP-8/SP-10.

Límites de los datos de prueba: no incluyen red, motor, catálogo, cotización de Python, persistencia ni análisis real de archivos; los tiempos y números son simulados. La autorización del servidor, las etiquetas de gasto y la precisión del motor se verifican en T7.2–T7.4, T7.9 y T7.11.

**Aprobación:** este es un borrador. David/el aprobador independiente debe aprobar este borrador exacto mediante el flujo de planificación antes de que T7.1 lo copie. El Designer no otorga aprobaciones.

### Identidad de entrada/artefacto

| Entrada / artefacto | SHA-256 |
|---|---|
| `SPEC.md` | `1231537116a3514a13601d6cf8ef844235948844c0c28d79368d530d62aa897c` |
| `PLAN.json` (revisión 17) | `c4242beea078367051fcf3b33179024ae677d93ed9ac1504d4f4293582fd4952` |
| `design/herramientas-chat@v1.r2.behavior.md` | `193825c90fa318b1b7a2c1b0b8f61f80ed8efd465c843db2d4fc435f8021f493` |
| `design/herramientas-chat@v1.r2.dir-a.md` | `5e8334932d48e103912c675177a90111c4ad306c81ea857e2943425c5dd84606` |
| `design/herramientas-chat@v1.r2.dir-a.tsx` | `06d938bd05bf4b0b4ded3e6019ee57eb5d894117c0facd49de86c7fd08817069` |
| `design/herramientas-chat@v1.r2.dir-a.html` | `9e3753ff7649f24aa1fc68b23ba4f9ae5d7ff76a7660bd754b3106c3fa650460` |
| Código fuente corregido (evidencia de delegación) `herramientas-chat@v1.final.tsx` | `a0c8f3d3d9f10f35324e2b51b48dfef1aeec4996671dc18c798e4205a24665b3` |
| `design/herramientas-chat@v1.html` | `0b482164529ac991b2ebcc448dbd2c97fb3f13394163c4b0819b4c62b3c76725` |
