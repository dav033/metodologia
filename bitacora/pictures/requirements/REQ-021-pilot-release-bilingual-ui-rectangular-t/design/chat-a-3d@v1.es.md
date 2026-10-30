---
contract: chat-a-3d
version: 1
status: draft
subplan: SP-12
requirements: [R13]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: b
name: Escena junto al chat
source_revision: r1
source_behavior: chat-a-3d@v1.r1.behavior.md
current_behavior: chat-a-3d@v1.r1.chosen.behavior.md
source: chat-a-3d@v1.r1.dir-b.tsx
plan_revision: 17
---

# chat-a-3d@v1 — Escena junto al chat

## 1. Identidad y trazabilidad

Planificación canónica **borrador; no aprobado para implementación**. El propietario eligió la dirección b, “Escena junto al chat” (revisión r1), en la comparación web (`drafts.json` SHA-256 seleccionado `bf3148b1…` = `chat-a-3d@v1.r1.dir-b.html`). Esa elección autoriza solo esta finalización; no aprueba este contrato, SP-12 ni el plan. Versión 1; no existe una versión predecesora aprobada, por lo que no se requiere migración de consumidores. Esta tarea escribe únicamente `design/chat-a-3d@v1.md` y `design/chat-a-3d@v1.html`. No se modificó la exploración, el historial, SPEC, PLAN, ningún archivo de producción, el registro de cambios del contrato ni la vista previa.

Alcance: REQ-021 / M4 / SP-12 “El chat normal recomienda decoraciones 3D listas para usar”, de SPEC (ronda 16; fila de verificación de SP-12), revisión 17 de PLAN.json, el resumen de la dirección `chat-a-3d@v1.r1.behavior.md`, el resumen actual `chat-a-3d@v1.r1.chosen.behavior.md` y los archivos Markdown, JSON, TSX y HTML de la dirección b elegida en r1. Este contrato especifica el área de recomendaciones del chat guiado existente en `/asistente`, la llegada al Taller como una escena nueva sin guardar y el rechazo de un enlace directo sin permiso. No especifica el recomendador, la herramienta del modelo, la sanitización del flujo, los metadatos de la galería, los permisos del servidor ni el guardado, que corresponden a T12.2, SP-7, SP-1 y SP-4.

| Requisito / criterio | Cobertura del contrato | Tareas consumidoras |
|---|---|---|
| R13 — el chat normal se conecta con el Taller 3D | V1, V3, F1–F3, UI-AC-02–09, 17 | T12.3; revisión T12.5 |
| Tarjetas con vista previa, nombre en el idioma de la sesión y cantidad de globos, para cada plan | Tarjetas V1/V2, F1, F4, UI-AC-06, 15, 16 | T12.3; T12.5 |
| «Abrir en el Taller» solo con `decoraciones.explorar`; abre `/3d?decoracion=<id>` como proyecto nuevo; los demás no ven el botón ni menciones al plan | V1 frente a V2, V3, V4, F2, F5, UI-AC-07, 09, 17, 18 | T12.3; T12.5 |
| Verificación de SPEC SP-12: si no hay coincidencias, se muestra una explicación y nunca se inventan recomendaciones | Estado `empty`, F1, UI-AC-11 | T12.3 |

Consumidores de PLAN: SP-12 `ui.contract=chat-a-3d`, `ui.version=1`, `design_task=T12.1`, `visual_review_task=T12.5`. T12.1 copia solo el artefacto aprobado por el propietario. T12.3 implementa `TarjetaRecomendacion3D.tsx` y `textos/recomendaciones-3d.ts` conforme a este contrato. T12.4 (pruebas e2e en navegador) y T12.6 (auditoría) verifican el comportamiento, no este contrato visual.

**Cambio del plan incorporado (resumen actual frente al resumen de la dirección).** El único cambio es el objetivo de T12.3: ahora crea `scripts/test/test-integracion-recomendaciones-3d.ts` (modos SP-12 y CG-12, proveedores de prueba deterministas, base de datos local de REQ-021, sin llamadas de pago a la IA) y prueba Entusiasta, Master Designer y personal, tarjetas en inglés, apertura como proyecto nuevo sin guardar, guardado, ausencia de coincidencias y falta de permisos mediante puntos de entrada reales. El propio arnés es trabajo de ingeniería; su consecuencia para la interfaz es que cada caso nombrado debe tener una pantalla definida y observable. La tabla siguiente vincula cada caso con este contrato; los cambios 3–5 de abajo fueron necesarios para que los casos de guardado, ausencia de coincidencias y falta de permisos fueran observables.

| Caso de prueba de T12.3 | Dónde se especifica |
|---|---|
| Entusiasta (también Designer, Designer Plus) | V2, tabla de cuentas §5, UI-AC-07, 08 |
| Master Designer y personal (Empleado interno, Administrador) | V1, tabla de cuentas §5, UI-AC-02, 09 |
| Tarjetas en inglés | F4, reglas de redacción §7, UI-AC-15 |
| Apertura como proyecto nuevo sin guardar | F2, V3, UI-AC-09 |
| Guardado | Paso 5 de F2, V3 «Guardar proyecto» → proyectos@v1 D1, UI-AC-10 |
| Sin coincidencias | Estado `empty`, UI-AC-11 |
| Falta de permisos | V2 (sin botón ni ruta), V4 rechazo del enlace directo, UI-AC-07, 08, 18 |

**Cambios con respecto a la exploración elegida de r1.** Se conservan la composición, el patrón de navegación, los tokens, la tipografía y el movimiento. El HTML canónico se reconstruyó con el generador sin conexión actual a partir de una copia del TSX de r1 con estos cambios (el código fuente modificado y el diff se conservan como evidencia de delegación: `.state/delegations/D-20261029-163215-a3ef/chat-a-3d@v1.final.{tsx,diff}`):

1. *Vistas con nombre de cuenta (cambio).* El inspector de Vista nombra las cuentas: “Chat · Master y personal”, “Chat · Entusiasta–Designer Plus”, “Taller · escena sin guardar”, “Enlace sin permiso”. Solo elementos de la interfaz del inspector.
2. *Se muestra la ruta al Taller 3D a cuentas sin acceso al explorador (defecto verificado).* r1 mostraba el enlace de ruta «Taller 3D» en la vista de solo recomendaciones. `herramientas-chat@v1`, aprobado, muestra únicamente las herramientas permitidas (Taller 3D es para Master Designer y el personal). El enlace ahora está ausente en V2 y V4.
3. *Opción de guardado al llegar (cambio: guardado).* V3 agrega la acción principal existente de proyectos@v1 «Guardar proyecto» junto a «Volver al chat». Representa proyectos@v1 D1 (primer guardado con nombre); la maqueta solo informa de esa transferencia.
4. *Rechazo del enlace directo (cambio: falta de permisos).* La nueva vista de contexto V4 reutiliza el texto de V7 de `herramientas-chat@v1` para `/3d?decoracion=<id>` abierto sin `decoraciones.explorar`.
5. *Ausencia de coincidencias sin explicación (cambio: sin coincidencias; verificación de SPEC SP-12).* El cuerpo `empty` de r1 repetía la etiqueta de su propio botón (“Cuéntame qué quieres cambiar…”). Ahora el cuerpo explica: “Ninguna decoración de la galería encaja con lo que describiste. Cambia el tamaño, los colores o la ocasión.”
6. *El cuerpo del error repetía la acción (defecto verificado).* El cuerpo de `error` en r1 decía “Intentar de nuevo”, igual que el botón. Ahora dice “La conversación se conserva.”
7. *Se perdía la evidencia del enlace profundo al llegar (defecto verificado).* La nota de r1 dice que la llegada muestra la ruta codificada; el cambio de vista volvía a montar la pantalla y la descartaba. La línea de ruta ahora se conserva durante la transición.
8. El pie de página indica la procedencia: “Contrato borrador · Sin aprobación”. La barra de título conserva “Mockup · Chat · Taller 3D · B”; ambos son elementos de procedencia, no texto del producto.

Ningún otro cambio en el código fuente. Evidencia del producto de solo lectura usada en la exploración: t12 `src/app/asistente/page.tsx`, `src/components/guiado/{VistaGuiada,CarruselDecoraciones,Compositor,ConfirmarEmpezarDeNuevo}.tsx`, `src/components/ui/shell/{CabeceraApp,MenuApp}.tsx`, `src/app/globals.css`, `src/app/layout.tsx`; asesor `src/components/asesor/ChatView.tsx` (no es el objetivo).

## 2. Propósito y usuarios

Usuarios: cuentas de Usuario con sesión iniciada en Entusiasta, Designer, Designer Plus o Master Designer, y personal (Empleado interno, Administrador). Solo Master Designer y el personal tienen `decoraciones.explorar`.

| Vista | Objetivo del usuario | Éxito observable |
|---|---|---|
| V1 Chat con apertura (`/asistente`, Master Designer/personal) | Describir el evento en dos o tres mensajes y comenzar con una decoración lista para usar | Dos o tres tarjetas con vista previa, nombre y cantidad de motores; una ampliada; «Abrir en el Taller» en la tarjeta ampliada y en todas las tarjetas. |
| V2 Chat, solo recomendaciones (`/asistente`, Entusiasta/Designer/Designer Plus) | Hacer la misma descripción y ver qué opciones encajan | Tarjetas y selección idénticas, sin acción para abrir, sin ruta al Taller y sin menciones al plan en el área de recomendaciones. |
| V3 Llegada al Taller (`/3d?decoracion=<id>`, contexto) | Continuar en el taller desde la decoración elegida | “Escena nueva / Sin guardar todavía” con el nombre y la cantidad de esa decoración; «Guardar proyecto» lleva al primer guardado de proyectos@v1. |
| V4 Enlace directo sin permiso (contexto) | Entender que el enlace no se puede abrir | Rechazo sin datos de la decoración y sin mencionar un plan; «Volver a herramientas». |

## 3. Arquitectura de la información y jerarquía

Contenedor global, sin cambios respecto a las vistas hermanas: encabezado Pictures/Sempertex (marca de anillo y punto, “Pictures”, “Sempertex” en Geist Mono), selector de Idioma, menú desplegable «Mi cuenta» → fila H1 (“Asistente de decoración” + «Empezar de nuevo») → separador horizontal de rutas (Chat, Taller 3D solo con el permiso de exploración, Proyectos) → contenido → pie de página. Consulta Q1 sobre la barra lateral de herramientas de SP-7.

Contenido de V1/V2 a ≥1100px: **columna de conversación** (izquierda, 280–340px, fija al desplazarse) | **área de recomendaciones** (derecha, flexible).

- Conversación: encabezado “Chat” → hilo (saludo del asistente y “¿Qué vas a celebrar?”, respuesta del usuario, “¿Qué tamaño y qué colores?”, respuesta del usuario, línea de respuesta “Ideas de decoración” o título del estado) → área de entrada (etiqueta, chip de sugerencia opcional, campo de texto, enviar/detener).
- Área de recomendaciones: encabezado “Ideas de decoración” + línea de cantidad (“3 decoraciones”) → **escenario** (el objeto más grande: vista previa ampliada, luego nombre de 20px + “<n> globos”, y después «Abrir en el Taller» para quienes tienen permiso de exploración) → **índice de vistas previas** de tarjetas compactas (vista previa, nombre completo, cantidad, “Vista actual”/“Ver escena”, acción «Abrir en el Taller» en la tarjeta para quienes tienen permiso de exploración).
- Información principal: vista previa, nombre y cantidad de la decoración seleccionada. Secundaria: las demás tarjetas. Complementaria: línea de cantidad y avisos de estado.

Revelación progresiva: el escenario y el índice aparecen solo cuando se completa la descripción; antes se muestra un marcador de posición neutro. Al seleccionar una tarjeta, se reemplaza la escena ampliada en el mismo lugar; nunca se navega a otra vista ni se cambia el orden de las recomendaciones. Justificación: la conversación breve y la decoración examinada permanecen una junto a la otra (concepto de dirección).

## 4. Sistema de diseño y lenguaje visual

Sistema fijo del proyecto; sin paleta, fuente ni marca nuevas. Tokens (claro / oscuro), de t12 `globals.css` e idénticos a los contratos de las vistas hermanas: `--fondo` #faf9fc/#0b0c10; `--superficie` #ffffff/#16181f; `--superficie-suave` #faf8fd/#1c1e26; `--superficie-2` #efe9f8/#242733; `--borde` #e3daef/#383c48; `--borde-suave` #efe9f8/#2a2d38; `--texto` #1c1425/#f4f5f7; `--texto-suave` #6b6178/#9aa1ad; `--texto-tenue` #766c85/#8a91a0; `--acento` #6d3fe0/#9479ff; `--acento-hover` #5530b8/#a58dff; `--sobre-acento` #ffffff/#120b24; `--error` #b23a45/#ff979f; `--error-suave` #ffeaec/#43252a; `--taller-visor` #ebe7f1/#1a1722; `--taller-panel` #faf9fc/#16131d. Los roles de shadcn se asignan una vez por tema: background → fondo; card/popover/sidebar → superficie; foreground → texto; primary/primary-foreground → acento/sobre-acento; secondary/muted/accent → superficie-2; muted-foreground → texto-suave; input → texto-tenue (borde del control ≥3:1); border → borde; ring → acento; destructive → error.

Tipografía: Geist Sans (WOFF2 local) para el cuerpo, 15px/1.5; H1 24px/600; nombre de la decoración seleccionada 20px/600; encabezados de panel 18px/600; texto del hilo y metadatos del escenario 14px; nombre de tarjeta 14px/600 (15px en teléfono); metadatos 12–13px. Las cantidades usan cifras tabulares. Geist Mono solo para la marca heredada “Sempertex”. Radios: paneles 32px, tarjetas/recuadros 24px, campos 18px, píldoras/botones 999px. Relleno: 24px en escritorio, 20px en teléfono. Iconos lucide de 18px (15px dentro de las tarjetas), decorativos.

Uso del color: el acento se usa solo en «Abrir en el Taller» de la escena ampliada, enviar, «Guardar proyecto» y el foco. «Abrir en el Taller» de las tarjetas es un botón delineado. Tarjeta seleccionada: borde `--texto-tenue` sobre `--superficie-suave`; elemento de ruta actual: `--texto` con subrayado de 3px en `--texto` (neutro). Los iconos de error usan `--error`; el fallo siempre se expresa con palabras.

Foco: contorno de 3px en `--acento`, con separación de 4px en cada elemento interactivo; el H1 recibe el foco mediante programación (tabindex −1) después de cambiar de vista.

Componentes (`origen:id variante estado`, ruta de importación):

| Componente | Uso | Importación |
|---|---|---|
| `shadcn:button default ready/hover/focus/pressed/disabled/busy` | «Abrir en el Taller» de la escena ampliada (estado ocupado “Abriendo…”), enviar, «Guardar proyecto», confirmar diálogo | `@/components/ui/button` |
| `shadcn:button outline ready/hover/focus/pressed/disabled` | «Abrir en el Taller» de las tarjetas, «Empezar de nuevo», «Intentar de nuevo», «Volver a las recomendaciones», «Volver al chat», «Volver a herramientas», detener, chip de sugerencia, Cancelar | `@/components/ui/button` |
| `shadcn:input text empty/filled/focus` | Área de entrada, con etiqueta | `@/components/ui/input` |
| `shadcn:skeleton scene loading` | Geometría reservada para la vista previa, el nombre y la cantidad | `@/components/ui/skeleton` |
| `shadcn:dialog restart open/closed` (implementación instalada de Animate UI/Base UI) | Confirmación de reinicio D1 | `@/components/ui/dialog` |
| `custom:scene-stage selected ready/preview-error/count-error/opening` | Vista previa ampliada + nombre/cantidad + acción principal | `article` semántico + tokens |
| `custom:recommendation-card index unselected/selected/focus/disabled-open` | Tarjeta con botón nativo `custom:card-preview` (`aria-pressed`) y acción opcional para abrir | `article`/`button` semánticos |
| `custom:scene-preview svg illustrative` | Solo vistas previas simuladas; en producción se usa la imagen de vista previa de la galería | SVG integrado |
| `custom:status-box alert` | Aviso de error de cantidad, rechazo V4 | HTML semántico |
| `custom:empty-stage placeholder/status/alert` | Inicial, conversación, vacío, error, sin conexión, no disponible | HTML semántico |
| `native:details account open/closed`, `native:select language es/en` | Contenedor heredado | Nativo |
| `kit:planning-controls view/state/scene/theme/motion` | Inspector de maqueta, fuera del producto | `@kit/mockup` |

Movimiento (dirección b, “acoplamiento espacial opuesto”; solo transformaciones, el contenido siempre es legible): `.conversation` entra desde x −18px, `.scene-stage` desde x +26px, con curva cubic-bezier(.16,1,.3,1); `.recommendation-card` se acomoda desde y +16px, gira .6deg y rebasa hasta −2px, con desfase escalonado de 65ms; una escena recién seleccionada (`.scene-object`) entra desde x +24px, escala .975; `.status-box` entra desde x +8px; la vista previa de la tarjeta se eleva 3px al pasar el cursor; los botones escalan a 1.025 al pasar el cursor / .965 al presionarlos, los iconos se desplazan 2px. Perfiles: expresivo, entrada de 580ms / controles de 180ms / desfase escalonado de 65ms; natural, 360/140/35; sutil, 180/100/12. Sin animaciones infinitas. La opción de movimiento reducido del sistema operativo, «Quieto» y `?still=1` eliminan todos los desplazamientos y transiciones; las pestañas ocultas pausan las animaciones.

## 5. Navegación y modelo de interacción

- **Entrada:** `/asistente`, a través de la fila de rutas del contenedor (o la barra lateral de herramientas de SP-7, si Q1 lo determina). El flujo de chat y el área de entrada son los existentes.
- **Control de acceso por cuenta (solo UI; la protección del servidor no cambia):**

| Cuenta | Tarjetas | «Abrir en el Taller» | Ruta Taller 3D | `/3d?decoracion=<id>` |
|---|---|---|---|---|
| Entusiasta, Designer, Designer Plus | Sí, idénticas | No aparece (no está deshabilitada ni se reemplaza) | No aparece | Rechazada → V4 |
| Master Designer, Empleado interno, Administrador | Sí | En la tarjeta ampliada y en todas las tarjetas | Presente | Abre V3 |

- **Selección:** el botón de vista previa de cada tarjeta la selecciona; el foco permanece en ese botón; `aria-pressed` y el texto “Vista actual” la identifican; cambian la escena ampliada, el nombre y la cantidad; una región activa cortés anuncia “<name> · <n> globos”.
- **Abrir:** cualquier acción autorizada para abrir navega a `/3d?decoracion=<id>` con el id de esa tarjeta, abre V3 como una escena nueva sin guardar y enfoca su H1. Un proyecto que ya estaba abierto conserva su identidad (proyectos@v1). Mientras se abre, la acción de la escena ampliada muestra “Abriendo…” y todas las acciones para abrir están deshabilitadas.
- **Llegada (V3):** «Volver al chat» regresa a las recomendaciones; «Guardar proyecto» abre proyectos@v1 D1.
- **Rechazo (V4):** «Volver a herramientas» → `/` (herramientas-chat@v1 V1). La ruta Chat permanece.
- **Reinicio:** «Empezar de nuevo» (deshabilitado en `initial`) abre D1; Cancelar/Escape conservan la conversación y devuelven el foco al elemento que abrió el diálogo; al confirmar, se vuelve a `initial`.
- **Menú de cuenta y ruta Proyectos:** contexto del contenedor heredado, sin rediseño.

## 6. Flujos

**F1 — Describir el evento y obtener recomendaciones (todos los planes).** Saludo y “¿Qué vas a celebrar?” (`initial`; sugerencia «Cumpleaños») → respuesta del usuario → “¿Qué tamaño y qué colores?” (`conversation`) → respuesta del usuario → `loading` (“Buscando decoraciones…”, esqueleto, el botón enviar cambia a Detener; el área de entrada sigue habilitada) → `ready` (tres resultados) o `two-results` (dos; sin espacio vacío para un tercero). Aparecen tarjetas después de un máximo de tres mensajes del cliente. Sin coincidencias → `empty` con la explicación y «Cuéntame qué quieres cambiar…», que enfoca el área de entrada; nunca se muestra una tarjeta poco pertinente o inventada. Fallo → `error`/`offline` con opción para reintentar; se conserva la conversación.

**F2 — Abrir y guardar (Master Designer, personal).** Desde `ready`, seleccionar otra tarjeta si se desea → «Abrir en el Taller» (en la escena ampliada o en una tarjeta) → `opening` → V3: H1 “Taller 3D”, “Escena nueva”, “Sin guardar todavía”, vista previa, nombre y cantidad de la decoración → «Guardar proyecto» → proyectos@v1 D1 (nombre, Guardando…, “Guardado en tu cuenta” solo después de la confirmación del servidor; si falla, se conserva la escena). Si el id es desconocido o se retiró → `unavailable`, sin reemplazo.

**F3 — Solo recomendaciones (Entusiasta, Designer, Designer Plus).** Igual que F1. Las tarjetas, la selección y las cantidades son idénticas; no hay acción para abrir, ruta al Taller ni invitación a cambiar de plan, y no se menciona ningún plan en el área de recomendaciones.

**F4 — Sesión en inglés.** Con el inglés seleccionado, los nombres de las tarjetas provienen de los textos en inglés de la galería (SP-9 `textos-ingles`); una decoración sin texto en inglés muestra su nombre en español. Las cantidades son idénticas en ambos idiomas; el chat nunca traduce ni inventa nombres.

**F5 — Enlace directo sin permiso.** Una cuenta sin `decoraciones.explorar` solicita `/3d?decoracion=<id>` → V4: “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». Sin nombre, vista previa ni cantidad de la decoración; sin mencionar planes.

**F6 — Recuperación de datos parciales.** Falla la vista previa → `preview-error` (se conservan el nombre y la cantidad; opción para reintentar). Falla la cantidad → `count-error` (“Conteo no disponible”, nunca cero; abrir está deshabilitado; opción para reintentar) — consulta Q2.

**D1 — Reiniciar.** Título «Empezar de nuevo», descripción “Se borrará esta conversación.”, acciones Cancelar / Empezar de nuevo (existente `ConfirmarEmpezarDeNuevo`).

## 7. Especificaciones de vistas

| Vista | Estructura y contenido | Acciones | Adaptabilidad |
|---|---|---|---|
| V1 Chat con apertura | Orden de §3. Escenario: vista previa (aprox. 16:7, `--superficie-suave`), nombre h3 de 20px, “<n> globos” con el número en negrita, acción principal «Abrir en el Taller» (nombre accesible “Abrir en el Taller: <name>”). Índice: tres tarjetas (vista previa de 86px de alto, nombre h3, “<n> globos”, “Ver escena ↗”/“Vista actual ✓”, botón delineado «Abrir en el Taller»). | Seleccionar, abrir, enviar/detener, sugerencia, reiniciar | §9 |
| V2 Solo recomendaciones | V1 sin acciones para abrir ni ruta Taller 3D. Las tarjetas mantienen el mismo ritmo de alturas; nada reemplaza el botón. | Seleccionar, enviar/detener, reiniciar | §9 |
| V3 Llegada al Taller (contexto) | H1 “Taller 3D”; ruta Taller 3D actual; panel del estudio: encabezado “Escena nueva” / “Sin guardar todavía” + «Volver al chat», «Guardar proyecto»; cuerpo: riel, lienzo `--taller-visor` con la decoración, inspector “Escena” / nombre / “<n> globos”. El editor se rige por los contratos de proyectos@v1/taller y no se rediseña aquí. | Volver al chat, Guardar proyecto | Inspector oculto por debajo de 1100px; riel oculto por debajo de 640px; las acciones pasan a varias líneas |
| V4 Rechazo de enlace directo (contexto) | H1 “Taller 3D”; ruta sin Taller 3D; cuadro de alerta (máximo 720px): h2 “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.”, «Volver a herramientas». | Volver a herramientas | Igual en todos los anchos |

Reglas de texto: las cadenas en español están en `src/components/guiado/textos/recomendaciones-3d.ts`, con sus equivalentes en inglés (SP-10). Los nombres y las cantidades de las decoraciones provienen exclusivamente de la galería (`galeria-index`) y del motor (`productosDe(item).totalGlobos`); las tres decoraciones de prueba (Arco orgánico con dos columnas y guirnalda 530; Pared de globos al fondo y dos columnas 346; Techo con tiras y flores colgando 188) son una instantánea de solo lectura usada como datos ilustrativos y no deben incluirse en la versión final. Sus nombres en inglés en el artefacto son traducciones provisionales para la composición; en producción se usan los textos de SP-9. Las vistas previas SVG son ilustrativas; en producción se muestra la imagen de vista previa de la galería. Las respuestas del usuario (“Cumpleaños”, “3 × 2,4 m · rosa y blanco”) son datos de ejemplo. Las cadenas con prefijo “Mockup ·”, “Datos de ejemplo” y las etiquetas del inspector son elementos de la interfaz de simulación. Las unidades se mantienen en cm/m.

## 8. Estados

El `state` del inspector se aplica a V1/V2; V3 y V4 lo ignoran. `scene=restart` del diálogo llega a D1 desde V1/V2.

| Estado | Qué aparece / qué se puede hacer / recuperación |
|---|---|
| `ready` | Tres tarjetas; la primera ampliada; selección en su lugar. |
| `two-results` | Dos tarjetas, misma jerarquía, sin tercer marcador de posición. |
| `initial` | Saludo, “¿Qué vas a celebrar?”, chip «Cumpleaños»; el área de recomendaciones muestra el marcador de posición “Decoraciones Sempertex”; reinicio deshabilitado. |
| `conversation` | Primera respuesta y la pregunta sobre tamaño/color; el marcador de posición invita a responder; sin tarjeta. |
| `loading` | Esqueleto de vista previa/nombre/conteo, “Buscando decoraciones…”, `aria-busy`; el compositor permite escribir; Detener reemplaza Enviar. |
| `empty` (sin coincidencias) | “No hay coincidencias” + “Ninguna decoración de la galería encaja con lo que describiste. Cambia el tamaño, los colores o la ocasión.” + «Cuéntame qué quieres cambiar…» (enfoca el compositor). Sin tarjetas. |
| `error` | Alerta “No pudimos cargar las decoraciones” + “La conversación se conserva.” + «Intentar de nuevo». |
| `offline` | Alerta “Sin conexión” + “Revisa tu conexión e intenta de nuevo.” + «Intentar de nuevo»; se conservan los mensajes anteriores. |
| `preview-error` | La vista previa ampliada se reemplaza por “Vista previa no disponible” + «Intentar de nuevo»; el nombre, el conteo y la acción para abrir se mantienen. |
| `count-error` | Alerta “No pudimos cargar el conteo de globos.” + reintento; todos los conteos muestran “Conteo no disponible”, nunca 0; las acciones para abrir están deshabilitadas (Q2). |
| `opening` | La acción ampliada muestra “Abriendo…”, todas las acciones para abrir están deshabilitadas. |
| `unavailable` | Alerta “Decoración no disponible” + “Vuelve a las recomendaciones.” + «Volver a las recomendaciones»; sin nombre de reemplazo. |
| permission-denied | V2 (sin acción) para el chat; V4 para un enlace directo. No es un estado de error dentro del chat. |
| success (open) | V3, escena nueva sin guardar. El éxito o fallo al guardar corresponde a proyectos@v1. |

No aplican: errores de validación (un compositor vacío solo deshabilita Enviar); datos obsoletos (cada respuesta es un resultado nuevo de la herramienta); acción para abrir deshabilitada por falta de permiso (la regla establece que la acción no está presente).

## 9. Comportamiento adaptable

Rango admitido: desde 360px; comprobado en 1280, 768 y 390px.

- **≥1100px:** márgenes de 40px; conversación de 280–340px, fija junto al área de recomendaciones; índice en tres columnas debajo del escenario.
- **840–1099px:** márgenes de 24px; conversación de 280px junto al área; el índice pasa a una columna de filas horizontales (vista previa de 80px | nombre/conteo/etiqueta | acción para abrir de ≤140px); la información del escenario apila el nombre sobre la acción.
- **640–839px:** conversación sobre el área (no fija; respuestas del hilo en dos columnas); índice en tres columnas; información del escenario en una fila.
- **360–639px:** márgenes de 20px; los controles del encabezado pasan a varias líneas; H1 y reinicio apilados; separación de ruta de 20px; todo se apila; las tarjetas son horizontales (vista previa de 85px | texto), la acción para abrir la tarjeta se alinea debajo del texto; la acción ampliada se alinea a la izquierda, debajo del conteo.
- V3: inspector oculto por debajo de 1100px, riel oculto por debajo de 640px; las acciones del encabezado pasan a varias líneas. V4 no cambia.
- La página no tiene desplazamiento horizontal; los nombres se ajustan por palabra y nunca se truncan; los conteos nunca se separan de “globos”.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA, sujeto a la verificación de la implementación renderizada.

- Puntos de referencia: `header`, `nav` de ruta (“Navegación del producto”), `section` de conversación y `section` de recomendaciones con encabezados, `nav` del índice de vistas previas (“Elegir vista previa”), `footer`. Las tarjetas son `article`.
- Los botones de vista previa son botones nativos con el nombre accesible “Ver escena: <name>”, `aria-pressed` y `aria-controls` que apunta al título del escenario; el actual también muestra el texto “Vista actual”. El foco permanece en el elemento que invocó la selección.
- Los nombres accesibles de las acciones para abrir incluyen la decoración (“Abrir en el Taller: <name>”).
- Regiones dinámicas: nombre/conteo seleccionado, con anuncios corteses; carga con `role=status` + `aria-busy`; estado vacío con `role=status`; error/sin conexión/no disponible/error de conteo/V4 con `role=alert`.
- El cambio de vista enfoca H1 (tabindex −1). D1: modal, foco contenido; Escape/Cancelar cierra y devuelve el foco a «Empezar de nuevo».
- Contraste: texto ≥4.5:1, bordes de controles y foco ≥3:1 en ambos temas. Objetivos táctiles ≥44px. Contorno de foco de 3px con color de énfasis y desplazamiento de 4px.
- Vistas previas: las imágenes tienen texto alternativo que nombra la decoración; los íconos decorativos usan `aria-hidden`.
- Reajuste a 360px (y 320 CSS px) sin pérdida; zoom al 200% sin recortes; el movimiento reducido mantiene el contenido idéntico.

## 11. Criterios de aceptación visual y verificación

“Todos” significa desde 360px, comprobado al menos en 390/768/1280px, en claro y oscuro, en español salvo que se indique otra cosa.

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | Todos | Todos | El encabezado de Pictures/Sempertex, Idioma, Mi cuenta, las fuentes Geist y los tokens coinciden con los contratos relacionados. |
| UI-AC-02 | ≥1100px | V1 listo | La conversación está a la izquierda de la escena ampliada y el índice de tres tarjetas está debajo de esa escena. |
| UI-AC-03 | 840–1099px | V1 listo | El índice es una sola columna de filas horizontales dentro de la columna del escenario; los nombres y las etiquetas para abrir se ajustan dentro de su tarjeta. |
| UI-AC-04 | 640–839px | V1 listo | La conversación está sobre el escenario; el índice tiene tres columnas. |
| UI-AC-05 | 360–639px | V1/V2 listo | La conversación, el escenario y el índice se apilan sin desplazamiento horizontal de la página; las tarjetas muestran la vista previa a la izquierda y el texto a la derecha. |
| UI-AC-06 | Todos | listo / dos resultados | Cada tarjeta muestra una vista previa, el nombre completo de la decoración y “<n> globos”; dos resultados muestran exactamente dos tarjetas y ningún marcador de posición. |
| UI-AC-07 | Todos | V2 cualquiera | En el área de recomendaciones no aparece «Abrir en el Taller», un sustituto deshabilitado, texto de actualización ni el nombre de un plan. |
| UI-AC-08 | Todos | V2, V4 | La fila de rutas muestra Chat y Proyectos, y no muestra Taller 3D. |
| UI-AC-09 | Todos | V1 listo → abrir una tarjeta que no sea la primera | V3 muestra “Escena nueva”, “Sin guardar todavía” y el nombre y conteo de esa tarjeta; la ruta solicitada es `/3d?decoracion=<that id>`. |
| UI-AC-10 | Todos | V3 | «Guardar proyecto» (principal) y «Volver al chat» están en el encabezado del estudio; al activar «Guardar proyecto» se abre el diálogo de primer guardado de proyectos@v1. |
| UI-AC-11 | Todos | vacío | Aparecen “No hay coincidencias”, la oración explicativa y «Cuéntame qué quieres cambiar…»; no se muestra ninguna tarjeta, vista previa ni conteo. |
| UI-AC-12 | Todos | cargando | Aparecen esqueletos y “Buscando decoraciones…”; no hay nombre ni conteo; Enviar muestra Detener. |
| UI-AC-13 | Todos | error / sin conexión / no disponible | El título de la alerta, la explicación y su acción de recuperación aparecen en el área de recomendaciones; los mensajes anteriores permanecen en el hilo. |
| UI-AC-14 | Todos | error de conteo | Todos los conteos muestran “Conteo no disponible” (nunca 0) y todas las acciones para abrir están deshabilitadas. |
| UI-AC-15 | Todos | listo, inglés | Los nombres son los textos de la galería en inglés (en español si faltan); las etiquetas muestran “Abrir en el Taller” / “globos”; los conteos son idénticos a los del español; los nombres largos se ajustan sin desbordarse. |
| UI-AC-16 | Todos | selección | Al elegir otra vista previa, cambia la escena ampliada, el nombre y el conteo; la tarjeta queda marcada como “Vista actual” con `aria-pressed=true` y el foco permanece en ese botón. |
| UI-AC-17 | Todos | V1 abriendo | La acción ampliada muestra “Abriendo…” y todas las acciones para abrir están deshabilitadas. |
| UI-AC-18 | Todos | V4 | Aparecen “No tienes acceso a esta herramienta”, “Tu cuenta no tiene permiso para abrirla.” y «Volver a herramientas», sin nombre de decoración, imagen, conteo ni nombre de plan. |
| UI-AC-19 | Todos | error de vista previa | “Vista previa no disponible” y reintentar reemplazan la vista previa ampliada, mientras el nombre y el conteo siguen visibles. |
| UI-AC-20 | Todos | D1 | Cancelar/Escape conservan la conversación y devuelven el foco a «Empezar de nuevo»; al confirmar, se vuelve a `initial`. |
| UI-AC-21 | Todos | Movimiento reducido / Quieto / estático | Todo el contenido y los controles están presentes sin animaciones en curso después de la carga. |

**Evidencia del HTML canónico construido durante esta finalización** (`design/chat-a-3d@v1.html`, SHA-256 `e11e8f52b7fde89d1a3d00af5ba1b9ed4f86639af854b1ef9b3e6d2083287a17`):

| Comprobación | Observación real |
|---|---|
| Kit instalado | `components status`: `installed=True built=True entries ok=96/96`. |
| Compilación sin conexión | Código de salida 0: `built … (633 KB, 2126 source files, offline)`; controles reales de shadcn/Base UI/Animate UI, CSS/JS integrados y Geist WOFF2 local de t12. Sin alternativa, instalación ni descarga. |
| `contrast.py` | Código de salida 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría renderizada | Primera ejecución: `RESULT: FAIL — overflow 1` (el selector Vista de la maqueta era 36px más ancho que 390px por las etiquetas largas del inspector). Se acortaron las etiquetas; ejecución final, código de salida 0: `312 renders (312 combinations planned), 8058 text measurements, 711 focus stops` en 1280/390/768, ambos temas. |
| Prueba de interacción | 30/30 PASS: cuatro acciones para abrir en V1 y ruta de Taller; conteos 530/346/188; la selección conserva el foco y actualiza el escenario; al abrir la segunda tarjeta se muestran Escena nueva/Sin guardar todavía/su nombre/346/`escena%3Apared_fondo_columnas`; «Guardar proyecto» está presente y abre D1; V2 no muestra acción para abrir, ruta de Taller ni palabras de planes en el área de recomendaciones; mismos conteos; texto de alerta de V4, sin datos de decoración; explicación del estado vacío y sin tarjetas; explicación de error y el reintento restaura tres tarjetas; dos resultados, dos tarjetas; error de conteo deshabilita la acción para abrir y no muestra “0 globos”; nombres y conteos en inglés; el diálogo de reinicio se abre y Escape lo cierra; sin desbordamiento a 390 en las cuatro vistas; `?still=1`, 0 animaciones en curso, movimiento reducido del sistema operativo 0, expresivo 6; cero errores de página; cero solicitudes externas. |
| Inspección visual | Capturas inspeccionadas: V3 claro 1280, V4 oscuro 1280, V2 inglés oscuro 390, página completa. |

`RESULT: PASS — no hay problemas de contraste, elementos no textuales, foco, alineación, espaciado ni desbordamiento`

Comandos reproducibles:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components status
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/.state/delegations/D-20261029-163215-a3ef/chat-a-3d@v1.final.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.html --widths 1280,390,768
```

Estas comprobaciones validan únicamente el artefacto de planificación. El orden de recomendaciones, la sanitización del texto transmitido por streaming, la fidelidad de las imágenes de la galería, la cobertura en inglés de SP-9, el rechazo de permisos del servidor y el guardado se verifican en T12.2, T12.4 y T12.6, no con este dispositivo de prueba.

## 12. Preguntas abiertas y supuestos

Preguntas abiertas (responsable de la decisión: David con el Planner; quienes implementen no deben inferir respuestas a partir de los valores del dispositivo de prueba):

- **Q1** — Navegación del armazón en `/asistente`: `herramientas-chat@v1`, aprobado, coloca la barra lateral izquierda de herramientas de SP-7 en V5 Chat `/asistente`, mientras que la dirección elegida mantiene la fila horizontal de rutas relacionada. Este contrato rige solo el área de recomendaciones; el armazón de la página sigue el contrato de armazón aprobado que corresponda. Confirmar si SP-12 hereda la barra lateral de SP-7 (el espacio de trabajo de dos columnas queda entonces en la columna principal) o si se mantiene la fila de rutas.
- **Q2** — Si falla el conteo del motor para una recomendación, ¿se debe omitir la tarjeta hasta que se recupere o mostrar “Conteo no disponible” y deshabilitar la acción para abrir (como establece este contrato)?
- **Q3** — ¿Qué vista previa debe mostrar una tarjeta cuando la galería no tiene una imagen de la decoración: omitir la tarjeta o mostrar “Vista previa no disponible” de forma neutral, como en `preview-error`?

Decisiones confirmadas (SPEC/PLAN, no se reabren): dos o tres decoraciones existentes de la galería, o ninguna; nombres y conteos solo de la galería y el motor; todos los planes ven las tarjetas; solo `decoraciones.explorar` (Master Designer, staff) abre `/3d?decoracion=<id>` como proyecto nuevo sin guardar y sin sobrescribir el trabajo existente; las demás personas no ven el botón ni una mención al plan; si no hay coincidencias, se muestra una explicación; los nombres en inglés siguen SP-9 y, si falta el inglés, se usa el español como alternativa (comprobación SPEC SP-9); guardar corresponde a proyectos@v1/SP-4; los permisos del servidor rechazan el acceso no autorizado a Taller.

Supuestos: inicialmente se amplía la primera recomendación devuelta; la selección es solo de presentación y no cambia el orden; V3 y V4 son dispositivos de contexto (editor y página principal de herramientas, regidos por otros contratos); los reintentos, las respuestas de ejemplo y los tiempos son transiciones en memoria del dispositivo de prueba, sin red ni modelo.

**Aprobación:** este es un borrador. David o la persona aprobadora independiente deben aprobar este borrador exacto mediante el flujo de planificación antes de que T12.1 lo copie. El Designer no otorga aprobaciones.

### Identidad de entradas y artefactos

| Entrada / artefacto | SHA-256 |
|---|---|
| `SPEC.md` | `095f5311948eb1f9bd2d3039da276f3011eb4fff13a95686748aadf315e720f9` |
| `PLAN.json` (revisión 17) | `59880c53f91e69a17befc303572f9d41024d466895b40a3f7cd8155af0387810` |
| `design/chat-a-3d@v1.r1.behavior.md` | `0b1fdc83c6c2b72f0e0e0997e5c654485cede943ad8089cc39bb475de3bc6082` |
| `design/chat-a-3d@v1.r1.chosen.behavior.md` | `bce9d700b43677d53b4002483168e2025cf27d411b960fa2df40827916ee1a52` |
| `design/chat-a-3d@v1.r1.dir-b.md` | `7a29adcdfd51ac515ba8da0e93a9fd795431a18e3ecf86d57b8222042f9ee07c` |
| `design/chat-a-3d@v1.r1.dir-b.json` | `041c55dc046381f4cfe48f0d31e53d5cd255176ffdb6627ff053ca679b05d650` |
| `design/chat-a-3d@v1.r1.dir-b.tsx` | `b0b84228a97cafb563884836d7136141fc82ec5649ea83ffbe99fa057fc27338` |
| `design/chat-a-3d@v1.r1.dir-b.html` (selección de quien es responsable) | `bf3148b1ed4657fc50160d1c7e7bb70054e77ba1690064aff37ca595aedea0d4` |
| Fuente parcheada (evidencia de delegación) `chat-a-3d@v1.final.tsx` | `ba263532f4cbc11a1dfd953436a0395b3e38caaa100298fe92295735f3293a7a` |
| `design/chat-a-3d@v1.html` | `e11e8f52b7fde89d1a3d00af5ba1b9ed4f86639af854b1ef9b3e6d2083287a17` |
