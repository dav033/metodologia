---
contract: taller-esenciales
version: 1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
owner: David
created: 2026-10-26
compatibility: breaking
---

# taller-esenciales@v1 — Elementos esenciales de Taller

## 1. Identity and traceability

Planning draft for REQ-021 / M1 / SP-3. Author: delegated Designer. Approval authority: David with the plan; this draft is not an implementation input. The planning flow will copy the approved bytes to `design/contracts/taller-esenciales@v1.md`. This revises the existing v1 planning draft in place; no approved version exists. The adjacent HTML is a static planning mockup, not a production preview or an enabled `design/preview` project.

Source snapshot (2026-10-26): `PLAN.json` revision 1, SHA-256 `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8`; `SPEC.md` SHA-256 `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4`; `PLAN.md` SHA-256 `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3`. The plan is still being discussed. SP-3 binds `ui.contract=taller-esenciales`, `ui.version=1`, design-copy task **T3.1** and independent visual review **T3.7**. UI consumers: **T3.2** tables/scene AI/shopping (V1,V2,V5,V6), **T3.3** Backing (V3), **T3.4** export (V7,D1). **T3.5** builds the browser/Blender harness; **T3.6** runs integration; **T3.8** audits spec/standards. Owner answers to round 9 q1–q4 (2026-10-26T18:53) settle behavior; the contract and SP-3 remain unapproved, and planning focus stays SP-2. V4 is retired; existing view IDs are preserved. SP-3 consumes `session-guard@1` from SP-1 and produces `taller-scene@1` through T3.4.

| Source | Covered behavior | View / flow / criteria |
|---|---|---|
| R9 / US-5 | Add/edit rectangular size and chairs; shopping list follows actual placement; manual and scene AI paths | V1, V2, V5, V6 / F1, F2 / UI-AC-01–06, 18, 28, 31–32 |
| R10 / US-6 | GLB with matching transforms, metre scale and colours, then Blender verification | V7, D1 / F4 / UI-AC-10–14, 21 |
| R11 / US-7 | One Backing group in Taller Fondos y muebles; move seven cards without duplicates, preserve original-name/AI/photo discovery and identities; Shopify `/catalogo` unchanged | V3 / F3 / UI-AC-07–09, 19, 29–30, 33 |

Draft revision / impact record (2026-10-26, owner feedback 18:53; kept here because this brief authorizes no changelog file): draft; revise the same unapproved v1. Compatibility is **breaking relative to the previous draft**: remove provisional V4/Shopify navigation, duplicate-card alternatives, the generic creation entry and pre-creation-form alternative; confirm per-type default creation plus existing inspector, quantities/dimensions without rental prices, the seven-card move and portable Blender LTS verification. Affected consumers: **T3.2** (V1/V2/V5/V6, F1/F2/F5), **T3.3** (V3/F3; remove V4), **T3.4** (V7/D1/F4 copy and feedback retained), **T3.5/T3.6** (confirmed automated real import plus separate owner opening), **T3.7/T3.8** (revised review scope). No accepted implementation exists to establish shipped conformity. Six active views retain their existing layout, tokens and applicable states. No other subplan contract changes; SP-1/2 own access, SP-8 owns translation and SP-4 owns server saves. Required action: owner plan/contract approval, then T3.1 exact copy, T3.2–T3.4 implementation, T3.5/T3.6 verification and T3.7/T3.8 independent review. An approved version is immutable; subsequent changes require v2 and impact analysis.

Read-only product evidence (pictures is the implementation repository; t12 is the compatibility reference, not an additional implementation target):
- `t12` HEAD `fb872bce`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `Taller3D.tsx`, `HojaMovil.tsx`, `EditorConjuntoMesa.tsx`, `FondosYMuebles.tsx`, `ListaEscenografia.tsx`; `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `fondos-escenografia.ts`, `mobiliario-tipos.ts`; `src/lib/catalogo/asignacion-fondos.ts`; `src/app/catalogo/page.tsx`, `src/components/catalogo/Facetas.tsx`.
- `pictures` / `asesor` HEAD `fa101a47`: same table editor and shared UI classes; `ExportarEscenaTaller.tsx`, `exportar-escena-glb.ts`, `exportadores-escena-globos.ts`, `archivo-escena.ts`. The GLB UI/exporter exists here, not in the inspected t12 source. Shared Taller colour tokens match; globals differ elsewhere. Do not assume worktrees contain identical features.
- Table default dimensions and limits below are source values, not new business rules. Mock examples, counts and capacities are explicitly fictitious; runtime counts come from the engine. No mock price is a catalogue fact.

## 2. Propósito y usuarios

Las cuentas externas con `taller.usar` (Plan 3 inicial), el personal y los administradores crean escenas de eventos; necesitan poder encontrar una mesa rectangular, editar los asientos y reutilizar Backing. Estas vistas requieren acceso a Taller; Shopify `/catalogo` y su permiso independiente `catalogo.ver` quedan fuera de este subplan. El resultado esperado es que el usuario pueda encontrar un elemento, insertarlo una sola vez, ver las cantidades reales de mesas/sillas e iniciar la descarga de un GLB sin perder el trabajo en la escena. La paridad con Blender es un resultado de exportación verificado por separado; nunca se deduce de un aviso de operación exitosa.

V1 permite encontrar la mesa; V2 la ajusta; V3 permite encontrar Backing de la escena; V5 comprueba los materiales reales; V6 solicita la misma mesa mediante la IA de escena existente; V7 envía la escena a Blender. No se incluye administración de cuentas, nueva edición de salas, Illustrator, edición de módulos ni rediseño del guardado de proyectos.

## 3. Arquitectura de información y jerarquía

Conservar la estructura actual del taller: título/acciones → barra de paneles → panel Añadir → vista de escena → inspector de pieza seleccionada/IA. Una acción principal local por panel. La escena y el objeto seleccionado siguen visibles mientras se cambian las dimensiones.

- Añadir → **Fondos y muebles / Mobiliario** → una tarjeta por cada tipo paramétrico existente (Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, Banquete en U), confirmado en la ronda 9 q1=a. Rectangular queda explícitamente visible y usa el modelo/editor existente. Cada tarjeta de tipo inserta su tamaño predeterminado de `PARTIDA_MESA`, selecciona el grupo y abre el inspector existente; no hay formulario previo a la creación. Las tarjetas por tipo reemplazan la entrada genérica de creación **Mesa con sillas a medida**; siguen disponibles los ocho tipos paramétricos. “Imperial” es una pieza fija existente del catálogo, no un nuevo tipo paramétrico: no añadirla a `TIPOS_MESA`.
- Añadir → **Fondos y muebles / Backing** es un grupo de presentación, no un nuevo repositorio de datos. La maqueta lo muestra directamente como acceso directo a la categoría. La ronda 9 q3=a confirma que las siete tarjetas pasan de sus grupos visuales anteriores a este único grupo Backing, una sola vez cada una. Las demás piezas permanecen en sus grupos visuales actuales. No crear alias de tarjetas duplicados ni una colección/filtro Backing en Shopify `/catalogo`. Conservar `GrupoCatalogo = "fondo" | "asiento" | "mesa" | "decorado"` y todas las entradas de `ASIGNACION_FONDOS` sin cambios. Derivar los elementos visibles de Backing del conjunto explícito de siete ID; no escribir `grupo: "backing"`, mover repositorios ni migrar escenas guardadas con fines de presentación. Conservar el nombre de catálogo “Marco hexagonal metálico” para `aro_hexagonal`; “aro hexagonal” sigue siendo un alias de búsqueda. La búsqueda “Backing” muestra las siete entradas canónicas distintas; se mantienen la compatibilidad con la búsqueda por nombres originales, IA/foto y filtros de repositorio. Los contadores siguen los resultados canónicos filtrados, no los alias duplicados.
- Inspector: nombre seleccionado → dimensiones en metros → cantidad de sillas/capacidad del motor → tipo/distribución de sillas → controles existentes de material/color → ayuda agrupada para mover/rotar/duplicar.
- Lista de compras: cantidades y dimensiones reales, luego descripción del material; distinguir Mobiliario / Escenografía de los productos de la tienda. Conservar “no es producto de la tienda”; no mostrar precios de alquiler ni inventar disponibilidad de compra o existencias (ronda 9 q2=a).
- La exportación sigue siendo una acción del encabezado (acción con nombre compacto en pantallas estrechas). Colocar **Descargar modelo GLB · Blender** junto a la opción existente de PNG, y luego una oración que explique los metros y la importación en Blender. No añadir asistente ni porcentaje de progreso inventado.

## 4. Sistema de diseño y lenguaje visual

Reutilizar los tokens y las clases de `globals.css` `BTN`, `BTN_PRI`, `BTN_ICO`, `RIEL`, `RIEL_ON`, `CHIP`, `TARJETA`, `DATO`, `ROTULO`, `FLOTANTE` de `ui-taller.ts`. No agregar una paleta de marca. Los controles nativos usan los mismos tokens de superficie/texto. Los tokens del proyecto tienen prioridad sobre las preferencias globales de tipografía/paleta de escritorio: este producto usa Geist Sans/Geist Mono, no JetBrains Mono. La maqueta sin conexión usa alternativas `system-ui` y `ui-monospace` porque no se permiten fuentes externas.

| Token semántico | Claro | Oscuro | Uso |
|---|---|---|---|
| `--taller-barra` | #ffffff | #121018 | Encabezado / barra |
| `--taller-panel` | #faf9fc | #16131d | Inspector / panel Agregar |
| `--taller-visor` | #ebe7f1 | #1a1722 | Fondo de escena |
| `--taller-tarjeta` | #ffffff | #1d1926 | Tarjetas / superficies de entrada |
| `--taller-boton` | #ffffff | #1b1724 | Controles secundarios |
| `--taller-encima` | #f3eefb | #231e2e | Al pasar el cursor / miniaturas |
| `--taller-elegido` | #ece3fb | #2a2140 | Filas / chips seleccionados |
| `--taller-borde` | #ddd3ea | #2d2838 | Separadores suaves existentes |
| `--taller-texto` | #1c1425 | #f2eff7 | Texto principal |
| `--taller-texto-2` | #3a3146 | #ddd8e6 | Texto de apoyo |
| `--taller-medio` | #5a5168 | #a59db5 | Etiquetas secundarias legibles |
| `--taller-primario` | #6d3fe0 | #7a55ec | Botón principal con `--taller-sobre-primario` #ffffff |
| `--taller-resalte` | #6d3fe0 | #8f6ef5 | Enfoque / selección |
| `--taller-acento` | #5530b8 | #b9a4ff | Texto de énfasis |
| `--taller-peligro` | #a8323d | #f08a94 | Errores con texto/icono |
| `--taller-valido` | #1a6a4a | #5fd3a0 | Éxito con texto/icono |

Los bordes suaves existentes no bastan como único límite interactivo: usar `--taller-medio` para los contornos de entrada y las etiquetas seleccionadas, con una indicación de texto/selección. No se necesita un token semántico nuevo. La geometría decorativa de la maqueta usa los colores de elementos decorativos del código fuente; son materiales de escena, no tokens de interfaz.

El espaciado sigue la escala existente de Tailwind, en incrementos de 4 px: 8 px entre controles, 12 px entre tarjetas, 16 px de relleno de sección, 24 px entre grupos. Encabezado de 56 px, barra de escritorio de 60 px, panel Agregar de hasta 340 px, inspector de hasta 320 px. Radio de 10 px para botones/entradas, 12 px para tarjetas y 20 px para la hoja móvil. Texto del cuerpo de 13–14 px, etiquetas de 12 px, encabezados de 16–20 px; las cantidades usan cifras tabulares. Los controles existentes de escritorio tienen al menos 36 px de alto; las acciones táctiles, 44 px. Enfoque: contorno de 2 px `--taller-resalte` con desplazamiento de 3 px, nunca recortado. Sin movimiento decorativo; cualquier transición de hoja dura ≤180 ms y tiene una alternativa instantánea para movimiento reducido.

## 5. Navegación y modelo de interacción

Conservar `/3d`; no crear rutas de producción independientes para V1–V7. V1/V2/V3/V6/V7 son estados de panel del taller; V5 es el diálogo de compras existente D2. V4 se eliminó del contrato y la maqueta tras la ronda 9 q3=a: Shopify `/catalogo` no cambia. Los controles “Vista / Estado / Diálogo / Tema” de la maqueta y las notas sobre el contexto de las decisiones son solo de planificación y no se publican. Las seis vistas activas tienen estados seleccionables para revisión.

La selección usa botones reales; “Editar mesa” ofrece una alternativa de teclado a hacer clic/arrastrar en la escena. Al añadir una mesa, se la selecciona y, en pantallas estrechas, el foco pasa al encabezado del inspector; en escritorio se anuncia la selección sin quitar el foco al usuario mientras explora. Los valores válidos se aplican al cambiar el valor o perder el foco; la entrada transitoria no válida permanece visible y no modifica la escena. Conservar la agrupación de deshacer/rehacer y la identidad del objeto. Esc cierra el cuadro emergente/diálogo de exportación y devuelve el foco al control que lo abrió. La lista de compras usa un diálogo modal con etiqueta y contención de foco; la exportación usa un grupo no modal con etiqueta, como hoy, no un menú ARIA simulado. Se cierra con Escape o al hacer clic fuera; Tab sigue el orden normal de los botones.

Ninguna acción depende exclusivamente de arrastrar. Los botones para añadir Backing respetan los resultados autoritativos de permisos de Taller. La navegación no inicia una escena vacía ni reemplaza una escena actual como efecto secundario. La navegación entre paneles conserva el trabajo actual; la persistencia queda fuera de SP-3. La maqueta simula solo mutaciones locales y no realiza descargas ni solicitudes de red.

## 6. Flows

**F1 — Add and edit manually (R9).** 1. Open Add / Mobiliario. 2. Activate “Mesa rectangular”. Insert one editable group with current source defaults: 2.40 × 0.90 × 0.75 m; chair defaults remain the engine's current defaults (8 requested in the existing entry), not a second UI rule. 3. Select the new table and open dimensions. 4. Change length/width/height and chair quantity/type/distribution. 5. Engine recomputes geometry/capacity and actual placed chairs. 6. Announce “Mesa actualizada: …; … sillas colocadas”. 7. Open shopping list and see the same actual quantities. Undo restores the previous group and counts.

**F2 — Capacity / validation recovery (R9).** Accept rectangular ranges from `LIMITES_MESA`: length 1–6 m, width 0.40–1.50 m, height 0.40–1.10 m. Existing sliders use 0.05 m steps; numeric input must not silently round a typed invalid value. Integer chairs 0–40 requested, actual capacity from `repartirSillas`; do not use 40 as the physical capacity. Show “Pedidas 12 · Colocadas 8” when the engine fits fewer, with the existing capacity explanation. Shopping/export use placed chairs only. On invalid text, show field error and keep last valid geometry; allow correction or “Restablecer valores”. If resizing reduces capacity, show the result visibly, never report the requested count as placed. Scene AI uses the same validation and counts. Old fixed groups offer the existing “Hacerla editable”; room-generated tables retain their current “ajustar el salón” instruction, not an independent conflicting editor.

**F3 — Find Backing (R11).** Open Add → Fondos y muebles → Backing. Browse/search names and descriptions. The confirmed canonical set contains `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. All seven appear in the mock, with original names and identity. Add a permitted piece by button or existing drag path; select it and announce its name. Return to old search: it remains findable by the same identity. The seven cards leave Fondos y tapetes / Decorado de pie visually; they are not duplicated there. Old-name search, repository filtering, AI/photo discovery and saved-scene identities remain compatible. Cancel/exit returns to the existing scene without adding a second piece. Existing dimensions/material options stay in the selected-piece inspector. Shopify `/catalogo` gets no Backing UI or catalogue behavior change.

Canonical membership / invariants for F3 (all remain `ASIGNACION_FONDOS → escenografia`; qualification is unchanged):

| Canonical ID | Existing name | Existing semantic `GrupoCatalogo` | Previous visual group (cards move to Backing) |
|---|---|---|---|
| `panel_redondo` | Panel redondo | `fondo` (implicit default) | Fondos y tapetes |
| `media_luna` | Media luna | `fondo` (implicit default) | Fondos y tapetes |
| `arcos_chiara` | Arcos chiara | `fondo` (implicit default) | Fondos y tapetes |
| `pedestales` | Pedestales | `decorado` | Decorado de pie |
| `aro_metalico` | Aro metálico | `decorado` | Decorado de pie |
| `aro_hexagonal` | Marco hexagonal metálico | `decorado` | Decorado de pie |
| `arco_metalico` | Arco metálico | `decorado` | Decorado de pie |

**F4 — Export for Blender (R10).** Open Export → GLB. Read “Escena completa · escala en metros”. Export only committed scene geometry, including the existing room, excluding grid, selection outlines, transform handles and editor lights. Do not export pending AI preview as if committed; do not silently omit unsupported pieces. Freeze a coherent snapshot for export, then prepare. Disable duplicate starts while preparing. On success announce **“Descarga GLB iniciada.”**, never “Guardado en tu equipo” or “Verificado en Blender”. On error show safe actionable copy and “Reintentar”, retain scene and allow editing. Keep PNG available as an existing sibling but no PNG redesign is required here. Completion help: “En Blender: Archivo → Importar → glTF 2.0 (.glb/.gltf)”. Product scale/layout/colour parity needs T3.5/T3.6 automated export/import verification and documented owner import; this mockup cannot prove either. The plan check compares world positions/dimensions within 1 mm and base-colour channels within 1/255 in the same colour space, with material/lighting limitations recorded. Round 9 q4=a authorizes the future verification task to provision checksum-verified official portable Blender LTS under `~/.local/opt/blender` without pacman or other system-package changes, record version/executable and run automated real GLB import. The owner also opens the file manually and documents the result; the automated and manual evidence are both required. A missing executable/import failure is blocked or failed evidence, never a pass. This planning/design task does not install Blender or run product verification.

**F5 — Scene AI (US-5).** Open existing IA tab. Example “Añade una mesa rectangular de 2,40 × 0,90 m con 8 sillas Tiffany”. While waiting retain committed scene, mark pending and offer no duplicate submission. Use existing proposal/acceptance behavior; show actual dimensions and placed/requested counts, not a new chat architecture. Applying a valid result updates the same table model and shopping list. On recoverable failure retain prompt and prior scene. Mockup represents a fixture response only; no AI is called.

## 7. View specifications

| ID / mock `view` | Structure / copy / actions | Responsive / states / flow |
|---|---|---|
| V1 `tables` | Add title; Mobiliario selected; search; “Mesa rectangular / A medida · con sillas”; cards for the other seven existing types; primary “Añadir mesa rectangular”; scene; compact selected-piece summary | Desktop three panes, narrow active sheet; S1–S5,S7,S9–S10; F1 |
| V2 `table-editor` | “Mesa rectangular 01”; length, width, tabletop height numeric fields + source ranges; chair requested/placed/capacity, type, distribution; existing cloth/colour controls; actual-count note; “Ver lista de compra” | One inspector column; fields never side-scroll; S1,S2,S3,S4,S5,S6,S7,S8,S9,S10; F1/F2 |
| V3 `backing` | Add → Backing; “Aros, pedestales y paneles”; search; two-column illustrated cards with canonical names, dimensions when known, “Añadir…” accessible names; preserve original-name/AI/photo discovery; no duplicate cards in previous groups | Cards wrap; no stock/price invented; S1–S5,S7,S9,S10; F3 |
| V5 `shopping` / D2 | Dialog title “Lista de compra”; Mobiliario and Escenografía; e.g. 1 × rectangular table (2.40 × 0.90 × 0.75 m), 8 × Tiffany chair, 1 × round panel, 1 × pedestal set; “No son productos de la tienda”; no invented currency total; close to prior scene | Max 640 px modal, nearly full viewport narrow; S1–S5,S7,S9,S10; F1/F2 |
| V6 `ai` | Existing scene IA inspector; one mock conversation; text prompt; “Enviar”; pending response; result “1 mesa rectangular · 8 sillas colocadas”; existing proposal/apply interaction and manual-edit link | Input below conversation, expands above mobile keyboard; S1–S5,S6,S7,S8,S9,S10,S11; F5 |
| V7 `export` / D1 | Workshop with export group open; PNG sibling, primary “Descargar modelo GLB · Blender”; scene name, metre scale, import instruction; prepare/error/started feedback next to trigger | Popover max 320 px, fits viewport; accessible in compact narrow header; S1–S5,S7,S8,S9,S10,S11; F4 |

Visible product copy is Spanish for this draft. Semantic strings are translation-ready; bilingual rollout belongs to the language subplan (R12), not an implicit SP-3 implementation. Backing and GLB retain those names in both locales. No new language switch is introduced. Test translated labels with 40% expansion; only project name may truncate with an accessible full name. The dark/light mock selector represents both existing product themes.

## 8. States

`#state` is a visible native select; only states applicable to the current view are offered. `#view` uses the six active ids above; `#scene` offers `none`, `export`, `shopping`; `#theme` offers `dark`, `light`. All have visible labels. The bridge can set value and dispatch `change`. State options update when the view changes. Dialog state comes from the chosen view/state; exported example data is never downloaded. Mock-only status explicitly says any resulting change is simulated.

| ID / selector | Visible result and enabled recovery | Transition / applicability |
|---|---|---|
| S1 `ready` | Stable content; one clear primary action; actual counts | Initial state for every view |
| S2 `loading` | Stable shell, labelled skeleton/loading message; disable content-dependent add/export; committed scene remains | All; resolve to ready/empty/error; no fabricated percentages |
| S3 `empty` | Context: no search match → “No encontramos piezas” + “Limpiar búsqueda”; no selection → “Selecciona una mesa” + return to Add; empty shopping/scene → “Añade una pieza para continuar” | All; export disabled when scene empty; AI empty is no messages, prompt usable |
| S4 `error` | “No pudimos cargar las piezas”, “No pudimos actualizar la lista” or “No se pudo exportar el GLB”, contextual retry; keep prior valid scene/input | All; Retry → pending/loading → ready; no stack traces or false success |
| S5 `success` | Named piece added / table updated / list current / download initiated; status region, not forced navigation | All; returns to ready without erasing content; export success refers to initiated download only |
| S6 `validation` | Error below affected numeric/prompt field, linked by `aria-describedby`; value retained; last valid scene untouched | V2, V6 only; correction → ready; not applicable to Backing/export/list |
| S7 `disabled` | Non-available action plus adjacent reason (scene/node limit or export not ready); no unreachable enabled fake action | All; condition cleared → ready; no disabled-only tooltip |
| S8 `partial` | V2 fewer chairs fitted, requested and placed explicit; V6 proposed result not yet applied; V7 unresolved pieces → export blocked, “Revisa las piezas antes de exportar” | V2,V6,V7; resolving issue → ready; no silently partial GLB |
| S9 `permission-denied` | “Tu cuenta no tiene acceso a esta herramienta” and “Volver”; hide scene/private data; SP-1/2 owns auth destination | All; no self-upgrade/payment flow |
| S10 `offline` | “Sin conexión”; remote library refresh/AI disabled; existing in-memory scene retained; “Reintentar” checks again | All; local edits, shopping derived from a complete scene and already-loaded export remain available; if assets unavailable block export with reason, never assume server save |
| S11 `pending` | “La IA está preparando una propuesta…” / “Preparando GLB…”; block duplicate submit/export, keep scene read-only only as needed for coherent snapshot | V6,V7 only; completion → success/error; no fake cancel button unless operation supports cancellation |

Partial remote Backing results are not introduced: failed catalogue loading reports an error and keeps previously known complete data visibly stale. `offline` covers unavailable refresh and stale retained data. No separate silent stale-success state. No destructive-confirmation state is needed; these flows do not delete data. Export has no separate permission beyond the existing Taller permission. Active preview state is not eligible for export until resolved. Runtime authorization and entitlements are authoritative, not the mock selectors.

## 9. Comportamiento adaptable

Rango admitido: desde 320 px; anchos principales de revisión: 360, 768, 1024 y 1440 px, además del ajuste a 320 px. Reutilice el punto de cambio existente del Taller en 1024 px y la regla para orientación horizontal y poca altura; 1440 px es un ancho para pruebas, no un nuevo límite de funcionalidad.

- **320–767 px:** encabezado compacto con ajuste de línea y acceso a Exportar y a la lista; 40 % para la escena / el espacio restante para el panel activo cuando ambos quepan, vista previa de escena de 180 px como mínimo y panel con desplazamiento independiente; botones de pestaña de ≥44 px. Muestre un solo panel de contenido activo de Añadir/Inspector/IA y conserve la pieza seleccionada y la búsqueda al cambiar de panel. La lista de compra/exportación debe caber en `100vw - 24px`. Sin desplazamiento horizontal de la página ni gestos de arrastre obligatorios. Con niveles de zoom altos, permita el desplazamiento vertical del documento para que el panel no oculte campos detrás de un lienzo fijo. Se puede acortar el título del proyecto; las etiquetas de acciones se ajustan en varias líneas.
- **768–1023 px:** el mismo modelo de un solo panel activo, con más altura de escena visible; Backing puede usar tres columnas; no comprimir el diseño de tres paneles de escritorio.
- **≥1024 px:** encabezado de 56 px, barra lateral de 60 px, panel Añadir de 300–340 px, escena flexible, inspector de 300–320 px. A 1024 px, cierre Añadir cuando se edite para mantener utilizable la escena; a anchos mayores se pueden abrir ambos paneles. Desplazamiento independiente de paneles; la vista nunca provoca desbordamiento de la página.
- **Orientación horizontal con ancho <1024 px y altura ≤540 px:** panel activo al lado de la vista previa (aprox. 45 %/55 %), no debajo; el encabezado se ajusta en varias líneas sin cubrir contenido; los controles se desplazan verticalmente. La lista de compra a pantalla completa cabe en la altura de la ventana y permite desplazar el cuerpo. A 320 px/zoom, se prioriza el contenido legible y el desplazamiento del documento antes que forzar una composición en paralelo.
- Backing usa el mismo panel Añadir y la misma hoja del Taller que la creación de mesas; no tiene un diseño separado de tienda/facetas. Las tarjetas usan anchos mínimos según su contenido; solo se muestran en dos columnas si caben las etiquetas; de lo contrario, en una. Conserve el orden lógico de lectura del DOM y el crecimiento natural de las etiquetas en español/inglés.

La barra de herramientas del mockup queda fuera del contenedor del producto; su altura no forma parte de las dimensiones del producto. No se requieren recursos de imagen remotos, Google Fonts ni API en tiempo de ejecución.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA para la interfaz modificada. Una descripción de diseño no demuestra conformidad. En producción se deben verificar el contraste renderizado, el teclado, el lector de pantalla y el reflujo.

- Un h1 por superficie; los encabezados identifican los paneles; cada campo/select tiene una etiqueta de texto visible. Las dimensiones numéricas incluyen «m», descripciones de error/rango y el modo de entrada apropiado; las sillas son enteras. Acompañar las muestras de color con etiquetas descriptivas; nunca usar solo el color para seleccionar o indicar errores.
- Los botones y los selectores nativos admiten el teclado y muestran el foco. Las pestañas seleccionadas usan semántica explícita de selección/pulsación, no solo un fondo. Los botones nativos ofrecen alternativas para agregar/seleccionar en cada operación de arrastre. Proporcionar un resumen de escena con nombre fuera del lienzo, que incluya las dimensiones de la mesa seleccionada y la cantidad real de sillas.
- La región de estado `role=status` / polite anuncia una actualización consolidada, no cada cambio del control deslizante. Los errores usan `role=alert`, con `aria-invalid` y descripciones en el campo. No revelar datos privados cuando se deniegan los permisos.
- D2 usa un diálogo nativo o un modal etiquetado equivalente, mantiene el foco dentro al pulsar Tab, admite Escape y devuelve el foco al control que lo abrió. D1 usa un grupo etiquetado no modal, el orden normal de Tab y restaura el foco al pulsar Escape. El lienzo no debe atrapar el teclado. El mockup usa un comportamiento de foco equivalente, incluido el cierre de diálogos al cambiar de vista del mockup.
- Texto normal ≥4.5:1; texto grande ≥3:1; límites de controles significativos, selección y foco ≥3:1. Los bordes suaves de los tokens son solo decorativos; los controles reciben un contorno de mayor contraste según se especifica. Los controles deshabilitados conservan una explicación legible junto a ellos.
- Se prefieren objetivos táctiles de 44 px; el mínimo WCAG para el tamaño de objetivo es 24 CSS px o un espaciado conforme para controles compactos de escritorio. El texto al 200%/zoom al 400% se redistribuye sin acciones recortadas a 320 CSS px. Ninguna información esencial depende solo del desplazamiento del puntero, el movimiento, la perspectiva o el lienzo.
- Respetar `prefers-reduced-motion`; no animar los esqueletos del mockup. Nombres de botones estables; el estado pendiente también establece la semántica de ocupado. La usabilidad real de Blender y una interfaz completa de autoría 3D no visual están fuera del alcance de este artefacto de diseño; la edición de texto, el resumen de escena y los controles modificados sí están incluidos.

## 11. Criterios de aceptación visual

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | ≥1024 px | listo | V1 tiene una entrada visible «Mesa rectangular» dentro de Mobiliario. |
| UI-AC-02 | 320–1023 px | listo | Al activar Añadir, se muestran controles de mesa en una hoja activa legible, sin desplazamiento horizontal de la página. |
| UI-AC-03 | Todos | listo | V2 muestra campos separados para largo, ancho y altura de la superficie, con unidades en metros. |
| UI-AC-04 | Todos | validación | Un largo fuera del rango muestra un error vinculado al campo, mientras la escena conserva su última geometría válida. |
| UI-AC-05 | Todos | parcial | V2 muestra las cantidades de sillas solicitadas y colocadas cuando difieren. |
| UI-AC-06 | Todos | éxito | Después de una edición, V5 muestra la misma cantidad de sillas colocadas que V2. |
| UI-AC-07 | Todos | listo | V3 muestra un grupo de visualización de Backing con nombre dentro de Fondos y muebles. |
| UI-AC-08 | Todos | listo | V3 enumera una vez cada uno de los siete elementos canónicos de Backing dentro del grupo. |
| UI-AC-09 | 320–1023 px | vacío | V3 muestra «Limpiar búsqueda» sin desbordamiento horizontal. |
| UI-AC-10 | Todos | listo | D1 etiqueta la acción GLB con Blender y muestra la escala en metros. |
| UI-AC-11 | Todos | pendiente | V7 muestra «Preparando GLB…» e impide iniciar otra exportación. |
| UI-AC-12 | Todos | error | V7 ofrece reintentar y mantiene visible la escena confirmada. |
| UI-AC-13 | Todos | éxito | V7 indica «Descarga GLB iniciada.» sin afirmar que se guardó localmente ni que se verificó en Blender. |
| UI-AC-14 | Todos | vacío | V7 deshabilita GLB y explica que la escena necesita una pieza. |
| UI-AC-15 | 360,768,1024,1440 px | listo | Ambos temas usan los tokens compartidos de superficie y acento de Taller indicados. |
| UI-AC-16 | Todos | permiso denegado | El contenido del taller denegado no contiene detalles de la escena ni del proyecto. |
| UI-AC-17 | Todos | listo | Al cerrar D2 con Escape, el foco vuelve al activador de la lista. |
| UI-AC-18 | Todos | listo | V6 ofrece una opción de edición manual después de aplicar la propuesta de mesa. |
| UI-AC-19 | Todos | listo | Las piezas de Backing que no provienen de la tienda no tienen precios ni afirmaciones de existencias inventados. |
| UI-AC-20 | <1024 px, altura ≤540 px | listo | El panel activo está junto a la vista previa y sus controles permiten desplazamiento vertical. |
| UI-AC-21 | Todos | parcial | La exportación se bloquea con un motivo explícito relacionado con una pieza sin resolver. |
| UI-AC-22 | Todos | cargando | El contenido del catálogo se carga manteniendo la estructura y bloqueando las acciones para añadir. |
| UI-AC-23 | Todos | sin conexión | El aviso distingue el estado sin conexión de la disponibilidad de la escena local conservada. |
| UI-AC-24 | Todos | listo | El foco del teclado es visible en todos los controles modificados. |
| UI-AC-25 | Todos | listo | El HTML expone listas desplegables nativas etiquetadas con los ids view, state, scene y theme. |
| UI-AC-26 | 320 px / equivalente a zoom del 400 % | listo | El contenido del diálogo y las acciones principales se redistribuyen sin desplazamiento horizontal de la página. |
| UI-AC-27 | Todos | deshabilitado | Cada acción principal deshabilitada tiene una explicación visible adyacente. |
| UI-AC-28 | Todos | listo | Después de editar una mesa, deshacer restaura las dimensiones anteriores y la cantidad de sillas colocadas en el inspector y la lista de compras. |
| UI-AC-29 | Todos | listo | Al buscar «Backing» en V3, se muestran las siete tarjetas canónicas y una cantidad de resultados filtrados coincidente. |
| UI-AC-30 | Todos | listo | La maqueta tiene seis vistas activas y no incluye una vista de Backing de Shopify ni transferencia al catálogo. |
| UI-AC-31 | Todos | listo | Al activar una tarjeta de tipo de mesa, se inserta su grupo con el tamaño predeterminado y se abre el inspector existente sin un formulario intermedio. |
| UI-AC-32 | Todos | listo | V5 muestra las cantidades y dimensiones del mobiliario sin precios de alquiler. |
| UI-AC-33 | Todos | listo | Las siete tarjetas de Backing no aparecen en Fondos y tapetes ni en Decorado de pie. |

La ronda 9 q1–q4 define estos comportamientos; el contrato aún requiere la aprobación del propietario. Las siete tarjetas pasan a Backing y salen de sus grupos visuales anteriores, que conservan sus demás piezas. Se mantiene la búsqueda por nombre original; no se crean alias de tarjetas duplicados. La identidad, `GrupoCatalogo`, `ASIGNACION_FONDOS`, la compatibilidad con IA/fotos y la ausencia de las siete tarjetas en los grupos anteriores requieren verificaciones de origen/funcionales en T3.3/T3.8; la agrupación representada no permite demostrarlas.

La paridad del motor, la distribución, la escala y el color, así como la búsqueda por nombre original y el descubrimiento mediante IA/fotos, requieren pruebas funcionales y la importación documentada en Blender; la revisión de capturas de pantalla por sí sola no puede aceptar R9–R11. El HTML representa geometría esquemática y simula interacciones; no genera un GLB, una cotización, una cantidad real del catálogo ni una respuesta de IA en vivo.

## 12. Preguntas abiertas y supuestos

### Preguntas abiertas

Ninguna. No se descubrió ninguna pregunta nueva y genuinamente sin resolver para el propietario al revisar esta instantánea de SP-3. La aprobación del plan y la aprobación de este contrato siguen pendientes; las respuestas sobre el comportamiento no aprueban el borrador ni cambian el foco de planificación de SP-2.

### Decisiones del propietario resueltas — ronda 9, 2026-10-26T18:53

- **Q1 resuelta — q1=a:** una tarjeta por cada tipo de mesa paramétrica existente; al añadirla, usar su tamaño predeterminado de origen, seleccionarla y editarla en el inspector existente. Sin formulario previo a la creación.
- **Q2 resuelta — q2=a:** las listas de compras muestran las cantidades y dimensiones reales, sin precios de alquiler.
- **Q3 resuelta — q3=a:** las siete tarjetas canónicas de Backing pasan de sus grupos visuales anteriores a un grupo en Taller Fondos y muebles, sin duplicar alias de tarjetas. Shopify `/catalogo` permanece sin cambios; los IDs canónicos, `GrupoCatalogo` semántico, `ASIGNACION_FONDOS`, la búsqueda por nombre original y el descubrimiento mediante IA/fotos permanecen estables. SPEC R11 y SP-3 ahora coinciden; se elimina V4.
- **Q4 resuelta — q4=a:** Blender LTS portable oficial con checksum verificado en `~/.local/opt/blender`, sin pacman; importación real automatizada más apertura manual documentada por el propietario. La configuración y las evidencias corresponden a las futuras tareas de implementación/verificación, no a esta revisión de diseño estático.

### Límites confirmados y supuestos explícitos

- Confirmado: R9/R10/R11 nunca se recortan; GLB, sin crear un formato nuevo de Blender; distribución, tamaños y colores de la escena, y escala en metros; agrupación de Backing con identidades canónicas conservadas; estilo existente de la aplicación; sin nuevos trabajos de salas 3D. Se reutilizan los límites de las mesas de origen y el comportamiento existente de los grupos editables.
- Comportamiento confirmado por el propietario: una tarjeta de creación por tipo, incluida la rectangular, y sin precios de alquiler. Detalles de diseño pendientes de aprobación del plan/contrato: campos numéricos nativos complementarios para las dimensiones, comentarios visibles sobre la capacidad solicitada y la colocada, y ayuda para la importación de GLB con leyenda. Esto no afirma que la interfaz actual ya funcione así.
- V4, que se retiró, no es un destino, selector de maqueta ni requisito de implementación. Los IDs de vista V1–V3/V5–V7 permanecen estables para la trazabilidad no afectada. SP-3 debe implementar el comportamiento acordado después de la aprobación; no quedan alternativas obsoletas de catálogo ni de precios.
- Las tareas de SP-3 son T3.1–T3.8, como se indica en la sección 1; todas siguen siendo borradores hasta que se apruebe el plan. No se reasignan tácitamente tareas de otros subplanes.
- La exportación local requiere que todos los recursos pertinentes ya estén cargados; trabajar sin conexión no lo garantiza. Los permisos provienen de SP-1/2; el comportamiento ante conflictos de proyectos almacenados proviene de persistencia; las cadenas de idioma provienen del trabajo de idiomas. Ningún éxito simulado de la interfaz implica que esas integraciones hayan pasado las verificaciones.
- Los datos de prueba de la maqueta usan una escena de celebración llamada «Cumpleaños · lavanda», el tamaño predeterminado de la mesa de origen de 2.40 × 0.90 × 0.75 m y 8 sillas Tiffany colocadas a modo ilustrativo. La capacidad de la maqueta se etiqueta como ejemplo y no es un algoritmo de perímetro alternativo. Aquí no se autoriza ninguna red, proveedor de pago, descarga real, escritura en producción, cambio al repositorio ni salida adicional de bitácora.

### Registro de verificación del borrador anterior (2026-10-26; evidencia conservada, no es una repetición de esta revisión)

Informe histórico del borrador anterior. Su afirmación sobre deshacer quedó superada: las pruebas de interacción actuales detectaron un registro duplicado de cambios al reemplazar la entrada, ya corregido en esta maqueta. La evidencia de la revisión actual que aparece abajo rige la entrega.

Chromium local mediante la dependencia existente de Playwright: 63 combinaciones de vistas/estados × 6 tamaños de ventana × 2 temas = 756 verificaciones de diseño; sin desbordamiento horizontal del documento o los diálogos ni controles recortados horizontalmente. Tamaños de ventana: 320×800, 360×800, 768×1024, 1024×850, 1440×980 y 844×390 en orientación horizontal. Se aprobaron diez verificaciones de interacción principales: agregar/seleccionar una mesa, actualizar dimensiones válidas, conservar la última geometría ante dimensiones no válidas, advertencia de capacidad, usar las sillas colocadas en las compras, restaurar el foco con Escape, bloquear exportaciones duplicadas mientras la exportación está pendiente, completar la simulación de forma transparente, validar una solicitud vacía de IA y aplicar una propuesta. No hubo errores de JavaScript en la página. Se inspeccionaron visualmente una vista representativa de escritorio en tema oscuro, el editor móvil y el catálogo de tablet en tema claro. Contraste de muestras de tokens: texto blanco primario 4.84:1 en tema oscuro / 6.11:1 en tema claro; etiquetas secundarias 6.63:1 / 7.47:1; foco frente al panel 4.99:1 / 5.82:1. También se aprobaron verificaciones finales adicionales: deshacer/rehacer restauró 2.40 m / 3.00 m, estaban presentes las siete tarjetas canónicas de Backing, funcionaron la confirmación de agregado de pieza y la búsqueda hexagonal, Escape en la exportación restauró el foco, el diálogo de compras retuvo y devolvió el foco, y el puente integrado en la maqueta controló la vista/estado/tema. No se realizaron solicitudes HTTP. Son verificaciones acotadas de la maqueta, no una auditoría completa de accesibilidad ni una aprobación del producto o de Blender. Las tarjetas de otros tipos de mesas representan transferencias al editor existente con comentarios de simulación explícitos; esta pieza estática no implementa la edición completa de formas no rectangulares ni geometría 3D real.


### Verificación de la revisión anterior (2026-10-26; antes de las respuestas del propietario)

- Ejecución histórica: se volvieron a leer el comportamiento del borrador de SPEC vigente entonces, las preguntas abiertas q1–q4 de la ronda 9, PLAN SP-3/T3.1–T3.8 y ambos repositorios suministrados, todos en modo de solo lectura. Los valores SHA-256 de origen indicados arriba permanecieron sin cambios hasta la entrega. No se editó ningún repositorio, SPEC, PLAN, registro de cambios ni vista previa del proyecto.
- Se aprobaron las verificaciones estáticas: las doce secciones numeradas, los criterios visuales únicos, los selectores nativos requeridos y etiquetados, la sintaxis de JavaScript en línea y la ausencia de referencias a recursos externos. El artefacto adyacente sigue siendo autónomo, con CSP que bloquea el acceso a la red.
- Se aprobó la matriz final de Chromium/Playwright: 63 combinaciones de vista/estado × 6 tamaños de ventana × 2 temas = 756 verificaciones de diseño, sin desbordamiento horizontal del documento ni del diálogo, controles horizontales recortados, errores de JavaScript ni solicitudes HTTP. Tamaños de ventana/escenarios: 320×800, 360×800, 768×1024, 1024×850, 1440×980, 844×390.
- Se aprobaron 27 aserciones de interacción para la inserción y selección de mesas, dimensiones válidas e inválidas, conservación de la última escena válida, deshacer/rehacer, capacidad solicitada/colocada, cantidades de compras, Escape/restauración del foco, las siete identidades canónicas de Backing y sus metadatos semánticos/de repositorio originales, búsqueda de Backing/nombres/alias hexagonal, contadores coincidentes, confirmación al añadir, etiqueta condicional de V4, exportación pendiente/finalización simulada, validación/aplicación de IA y el puente real al plan en línea. Las verificaciones de metadatos de los datos de prueba no demuestran la compatibilidad con el repositorio de producción.
- Se aprobaron 24 verificaciones finales de diálogos para exportación y compras en los mismos tamaños/temas. En compras se recorre el foco dentro del modal con Tab y Shift+Tab, y ambos diálogos se cierran con Escape. Esta revisión corrigió las entradas duplicadas en el historial por cambios de entrada y agregó un ciclo explícito de Tab en el modal después de que la verificación las detectara.
- Se inspeccionaron visualmente capturas de Chromium en memoria: Backing oscuro de escritorio a 1440×980 y el estado completo de mesa/capacidad móvil en tema claro a 360×900. No se guardó ninguna captura ni archivo adicional de vista previa. Los tokens y puntos de interrupción existentes permanecen sin cambios.
- Estas verificaciones cubren solo la maqueta estática. La geometría real de la escena, la paridad con proveedores de pago, la validez del GLB descargable, la importación en Blender y la conformidad de accesibilidad en producción quedan pendientes para T3.2–T3.8, tras la aprobación del propietario. No se instaló ni se ejecutó Blender.

### Current revision verification — owner-answer reconciliation (2026-10-26)

- Read the updated SPEC, PLAN.md and PLAN.json SP-3/T3.1–T3.8 plus the supplied repositories read-only; the source hashes recorded in section 1 match at handoff. Shared table-default, assignment and Taller-class files match between t12 and pictures. Only the two named design artifacts and the required delegation RESULT.json were written; no repository, SPEC, PLAN, changelog or project-preview edits, commits, launches or Blender installation.
- Static checks passed: twelve numbered sections, 33 unique acceptance criteria, `status: draft`, four visibly labelled native selectors, inline JavaScript parsed by Node `vm.Script`, no external resource references and no obsolete catalogue route or pending Q1–Q4 mock branch. CSP continues to prohibit network requests.
- Headless Chromium using the repository’s existing Playwright dependency: **55 applicable view/state combinations × 6 viewports × 2 themes = 660 layout checks**, plus **144 export/shopping dialog layout checks**. No document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. All six active view ids and state selectors were driven through native `change` events, matching the bridge integration interface.
- **34 interaction assertion groups passed**: all eight type cards use their source defaults and open the inspector without an intermediate form; valid/invalid dimensions, last-valid geometry, undo/redo, requested/placed capacity, actual shopping counts/dimensions without prices, seven unique canonical Backing cards with unchanged semantic/repository fixture metadata, original-name and hexagonal-alias discovery, matching Backing results, add feedback, pending export duplicate prevention, honest simulated completion, Escape/focus return and AI validation/application. An initial test incorrectly required every original-name query to return exactly one result; “Arco metálico” also matches “Marco hexagonal metálico” under the preserved substring search. Corrected the check to require the original canonical card once, without changing the established search behavior; the focused interaction run passed. Fixture metadata/discovery does not prove production AI/photo or saved-scene compatibility.
- **24 keyboard checks passed** across the same viewport/theme pairs: shopping Tab/Shift+Tab cycles within the modal and Escape returns focus; export Escape returns focus. Final interaction run observed zero JavaScript page errors and zero HTTP requests.
- Visually inspected in-memory Chromium captures: 1440×980 dark Backing and 360×900 full-page light table/capacity state. No screenshot or extra preview file was written. Tokens, responsive boundaries, rectangular illustration and unaffected flows remain intact; other type cards now demonstrate their source-default inspector handoff with schematic type artwork.
- Earlier verification records include the removed V4 and are historical only. This revision validates a static planning artifact: production engine geometry, deterministic AI-tool parity, saved-scene/AI/photo compatibility, actual GLB validity, automated Blender import, owner manual opening and full accessibility conformance remain for the planned implementation/verification cycle after owner approval.
