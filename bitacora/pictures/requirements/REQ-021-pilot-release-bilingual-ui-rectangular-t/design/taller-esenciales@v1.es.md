---
contract: taller-esenciales
version: 1
status: draft
subplan: SP-3
requirements: [R9, R10, R11]
owner: David
created: 2026-10-26
compatibility: undetermined
---

# taller-esenciales@v1 — Elementos esenciales de Taller

## 1. Identity and traceability

Planning draft for REQ-021 / M1 / SP-3. Author: delegated Designer. Approval authority: David with the plan; this draft is not an implementation input. The planning flow will copy the approved bytes to `design/contracts/taller-esenciales@v1.md`. This revises the existing v1 planning draft in place; no approved version exists. The adjacent HTML is a static planning mockup, not a production preview or an enabled `design/preview` project.

Source snapshot (2026-10-26): `PLAN.json` revision 1, SHA-256 `1b47820ae156e298b94ea01c322bcd26b780c2310c6d9357caad4a0796d3dd38`; `SPEC.md` SHA-256 `fafa1d7e372305f80cf2ecae420c661145c6cf569a9e6d7967f7f3a3c469aa73`; `PLAN.md` SHA-256 `77260acb94eb20a81d159a7beec889012ed58bdbae3ef512d1b4fa44dcfac112`. The plan is still being discussed. SP-3 binds `ui.contract=taller-esenciales`, `ui.version=1`, design-copy task **T3.1** and independent visual review **T3.7**. UI consumers: **T3.2** tables/scene AI/shopping (V1,V2,V5,V6), **T3.3** Backing (V3, conditional V4), **T3.4** export (V7,D1). **T3.5** builds the browser/Blender harness; **T3.6** runs integration; **T3.8** audits spec/standards. Round 9 q1–q4 are open; task descriptions are proposed, not owner decisions. SP-3 consumes `session-guard@1` from SP-1 and produces `taller-scene@1` through T3.4.

| Source | Covered behavior | View / flow / criteria |
|---|---|---|
| R9 / US-5 | Add/edit rectangular size and chairs; shopping list follows actual placement; manual and scene AI paths | V1, V2, V5, V6 / F1, F2 / UI-AC-01–06, 18, 28 |
| R10 / US-6 | GLB with matching transforms, metre scale and colours, then Blender verification | V7, D1 / F4 / UI-AC-10–14, 21 |
| R11 / US-7 | One Backing category in Taller and catalogue; preserve old discovery paths and identities | V3, conditional V4 / F3 / UI-AC-07–09, 19, 29–30 |

Draft revision / impact record (2026-10-26, owner feedback 17:26; kept here because this brief authorizes no changelog file): draft; same SP-3 contract and seven views; compatibility **undetermined** against shipped UI because no accepted implementation snapshot exists. Revision changes: explicitly separate the proposed table cards/pricing/Backing grouping and Blender acquisition from confirmed requirements; preserve semantic groups and repository assignments; make V4 conditional. Per-type table cards remain proposed q1=a. No unrelated visual tokens, layout rules or existing states change. Affected views V1–V7, D1–D2. Existing editor/export patterns are retained. No other subplan contract is changed. SP-1/2 provide permission/session outcomes; language work owns translated strings; project persistence owns server saves. Compared with the previous unapproved draft, these clarify pending choices; a choice that changes creation, pricing or category location requires adapting the named consumers before approval. Required action: owner approval including round 9 decisions, then T3.1 exact copy, T3.2–T3.4 implementation, T3.6 integration and T3.7 independent rendered review. An approved version is immutable; subsequent changes require v2 and impact analysis.

Read-only product evidence (pictures is the implementation repository; t12 is the compatibility reference, not an additional implementation target):
- `t12` HEAD `fb872bce`: `src/app/globals.css`, `src/components/tres-d/ui-taller.ts`, `Taller3D.tsx`, `HojaMovil.tsx`, `EditorConjuntoMesa.tsx`, `FondosYMuebles.tsx`, `ListaEscenografia.tsx`; `src/lib/globos3d/mobiliario-conjunto-tipos.ts`, `fondos-escenografia.ts`, `mobiliario-tipos.ts`; `src/lib/catalogo/asignacion-fondos.ts`; `src/app/catalogo/page.tsx`, `src/components/catalogo/Facetas.tsx`.
- `pictures` / `asesor` HEAD `fa101a47`: same table editor and shared UI classes; `ExportarEscenaTaller.tsx`, `exportar-escena-glb.ts`, `exportadores-escena-globos.ts`, `archivo-escena.ts`. The GLB UI/exporter exists here, not in the inspected t12 source. Shared Taller colour tokens match; globals differ elsewhere. Do not assume worktrees contain identical features.
- Table default dimensions and limits below are source values, not new business rules. Mock examples, counts and capacities are explicitly fictitious; runtime counts come from the engine. No mock price is a catalogue fact.

## 2. Propósito y usuarios

Las cuentas externas con `taller.usar` (inicialmente, Plan 3), el personal y los administradores crean escenas para eventos; necesitan encontrar una mesa rectangular, editar los asientos y reutilizar Backing. El acceso al catálogo depende de `catalogo.ver` y es independiente del acceso a Taller. Un usuario que solo tiene acceso al catálogo puede inspeccionar el contenido permitido, pero no agregarlo a Taller. Éxito: el usuario puede encontrar un elemento decorativo, insertarlo una sola vez, ver las cantidades reales de mesas/sillas e iniciar una descarga GLB sin perder el trabajo de la escena. La correspondencia con Blender es un resultado de exportación que se verifica por separado; nunca se infiere a partir de un mensaje de éxito.

V1 permite encontrar la mesa; V2, ajustarla; V3, encontrar Backing para escenas; V4, encontrar Backing en el catálogo; V5, comprobar los materiales reales; V6, solicitar la misma mesa mediante la IA de escena existente; V7, enviar la escena a Blender. No se incluyen administración de cuentas, edición de espacios nuevos, Illustrator, edición de módulos ni rediseño del guardado de proyectos.

## 3. Information architecture and hierarchy

Keep the existing workshop shell: title/actions → panel rail → Add panel → scene viewport → selected-piece/IA inspector. One local primary action per panel. The scene and selected object remain visible while dimensions change.

- Add → **Fondos y muebles / Mobiliario** → one card per existing parametric type (Redonda, Cuadrada, Rectangular, Ovalada, Cóctel, Media luna, Serpentina, Banquete en U), as proposed in round 9 q1=a. Rectangular is explicitly visible and uses the existing model/editor. Retain the generic **Mesa con sillas a medida** entry during transition with its existing round-table behavior; no type is removed. “Imperial” is an existing fixed catalogue piece, not a new parametric type: do not add it to `TIPOS_MESA`. If David chooses q1=b, revise this draft to specify the pre-creation form before approval.
- Add → **Fondos y muebles / Backing** is a presentation group, not a new data repository. The mock exposes it directly as a category shortcut. Round 9 q3 decides whether the seven cards leave their previous visual groups (q3=a, recommended) or remain there too as aliases (q3=b), or another list/location is chosen (q3=c). Neither choice is approved. The mock’s “Grupos actuales · referencia” explains their current locations; it does not claim alias retention has been approved. Keep `GrupoCatalogo = "fondo" | "asiento" | "mesa" | "decorado"` and every `ASIGNACION_FONDOS` entry unchanged. Derive Backing display membership from the explicit seven-ID set; do not write `grupo: "backing"`, move repositories or migrate saved scenes for presentation. Keep the catalogue name “Marco hexagonal metálico” for `aro_hexagonal`; “aro hexagonal” remains a discovery alias. Search “Backing” returns the seven distinct canonical entries; original names, AI/photo discovery and repository filters remain compatible. Counters follow the filtered canonical results, not duplicated aliases.
- Inspector: selected name → dimensions in metres → chair count/engine capacity → chair type/distribution → existing material/colour controls → grouped move/rotate/duplicate helper.
- Shopping list: actual quantities, then material description; distinguish Mobiliario / Escenografía from store products. Preserve “no es producto de la tienda”; do not invent purchasability, prices or stock.
- Export remains a header action (compact named action on narrow screens). Put **Descargar modelo GLB · Blender** alongside existing PNG, then one sentence explaining metres and Blender import. No wizard or invented progress percentage.

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

## 5. Navigation and interaction model

Keep `/3d` and `/catalogo`; do not create standalone production routes for V1–V7. V1/V2/V3/V6/V7 are workshop panel states. V5 is the existing shopping dialog D2. V4 is a provisional catalogue category alternative: round 9 q3 currently proposes only the Taller collection, while the SP-3 outcome still says “catalogue and Taller”; Q3 must settle that mismatch. The mockup's “Vista / Estado / Diálogo / Tema” controls and pending-decision notes are planning-only and do not ship. V4 is retained to compare the previous draft with the outstanding Q3 choice; it is excluded from the proposed T3.3 implementation unless expressly selected. All seven views still have selectable states for review.

Selection uses real buttons; “Editar mesa” provides a keyboard alternative to clicking/dragging the scene. Adding a table selects it and focuses the inspector heading on narrow screens; desktop announces selection without stealing focus while the user browses. Editing applies valid values after change/blur; transient invalid input stays visible and does not mutate the scene. Preserve undo/redo grouping and object identity. Esc closes export popover/dialog and returns to its invoker. Shopping uses a labelled modal with focus trap; export uses a labelled nonmodal group as today, not a fake ARIA menu. Close by Escape or outside click; Tab follows normal button order.

No drag-only actions. Backing add buttons and catalogue-to-Taller handoff respect permission server outcomes. Do not start a new empty scene or replace a current scene as a side effect of navigation. A catalogue handoff preserves current work; persistence ownership stays outside SP-3. The mockup simulates only local mutations and makes no download/network request.

## 6. Flows

**F1 — Add and edit manually (R9).** 1. Open Add / Mobiliario. 2. Activate “Mesa rectangular”. Insert one editable group with current source defaults: 2.40 × 0.90 × 0.75 m; chair defaults remain the engine's current defaults (8 requested in the existing entry), not a second UI rule. 3. Select the new table and open dimensions. 4. Change length/width/height and chair quantity/type/distribution. 5. Engine recomputes geometry/capacity and actual placed chairs. 6. Announce “Mesa actualizada: …; … sillas colocadas”. 7. Open shopping list and see the same actual quantities. Undo restores the previous group and counts.

**F2 — Capacity / validation recovery (R9).** Accept rectangular ranges from `LIMITES_MESA`: length 1–6 m, width 0.40–1.50 m, height 0.40–1.10 m. Existing sliders use 0.05 m steps; numeric input must not silently round a typed invalid value. Integer chairs 0–40 requested, actual capacity from `repartirSillas`; do not use 40 as the physical capacity. Show “Pedidas 12 · Colocadas 8” when the engine fits fewer, with the existing capacity explanation. Shopping/export use placed chairs only. On invalid text, show field error and keep last valid geometry; allow correction or “Restablecer valores”. If resizing reduces capacity, show the result visibly, never report the requested count as placed. Scene AI uses the same validation and counts. Old fixed groups offer the existing “Hacerla editable”; room-generated tables retain their current “ajustar el salón” instruction, not an independent conflicting editor.

**F3 — Find Backing (R11).** Open Backing in Add or catalogue. Browse/search names and descriptions. The proposed canonical set contains `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal`, `arco_metalico`. All seven appear in the mock, with original names and identity. Add a permitted piece by button or existing drag path; select it and announce its name. Return to old search: it remains findable by the same identity. Whether the old visual groups retain the cards is pending round 9 q3; old-name search and canonical identities remain in either option. Cancel/exit returns to the existing scene without adding a second piece. Existing dimensions/material options stay in the selected-piece inspector. Backing membership and category surface require Q3 approval; preserve identity compatibility regardless of grouping.

Canonical membership / invariants for F3 (all remain `ASIGNACION_FONDOS → escenografia`; qualification is unchanged):

| Canonical ID | Existing name | Existing semantic `GrupoCatalogo` | Current visual group |
|---|---|---|---|
| `panel_redondo` | Panel redondo | `fondo` (implicit default) | Fondos y tapetes |
| `media_luna` | Media luna | `fondo` (implicit default) | Fondos y tapetes |
| `arcos_chiara` | Arcos chiara | `fondo` (implicit default) | Fondos y tapetes |
| `pedestales` | Pedestales | `decorado` | Decorado de pie |
| `aro_metalico` | Aro metálico | `decorado` | Decorado de pie |
| `aro_hexagonal` | Marco hexagonal metálico | `decorado` | Decorado de pie |
| `arco_metalico` | Arco metálico | `decorado` | Decorado de pie |

**F4 — Export for Blender (R10).** Open Export → GLB. Read “Escena completa · escala en metros”. Export only committed scene geometry, including the existing room, excluding grid, selection outlines, transform handles and editor lights. Do not export pending AI preview as if committed; do not silently omit unsupported pieces. Freeze a coherent snapshot for export, then prepare. Disable duplicate starts while preparing. On success announce **“Descarga GLB iniciada.”**, never “Guardado en tu equipo” or “Verificado en Blender”. On error show safe actionable copy and “Reintentar”, retain scene and allow editing. Keep PNG available as an existing sibling but no PNG redesign is required here. Completion help: “En Blender: Archivo → Importar → glTF 2.0 (.glb/.gltf)”. Product scale/layout/colour parity needs T3.5/T3.6 automated export/import verification and documented owner import; this mockup cannot prove either. The proposed check compares world positions/dimensions within 1 mm and base-colour channels within 1/255 in the same colour space, with material/lighting limitations recorded. Portable Blender acquisition versus owner-only import is pending round 9 q4; this design neither installs software nor grants permission.

**F5 — Scene AI (US-5).** Open existing IA tab. Example “Añade una mesa rectangular de 2,40 × 0,90 m con 8 sillas Tiffany”. While waiting retain committed scene, mark pending and offer no duplicate submission. Use existing proposal/acceptance behavior; show actual dimensions and placed/requested counts, not a new chat architecture. Applying a valid result updates the same table model and shopping list. On recoverable failure retain prompt and prior scene. Mockup represents a fixture response only; no AI is called.

## 7. View specifications

| ID / mock `view` | Structure / copy / actions | Responsive / states / flow |
|---|---|---|
| V1 `tables` | Add title; Mobiliario selected; search; “Mesa rectangular / A medida · con sillas”; cards for other existing types plus generic-table route; primary “Añadir mesa rectangular”; scene; compact selected-piece summary | Desktop three panes, narrow active sheet; S1–S5,S7,S9–S10; F1 |
| V2 `table-editor` | “Mesa rectangular 01”; length, width, tabletop height numeric fields + source ranges; chair requested/placed/capacity, type, distribution; existing cloth/colour controls; actual-count note; “Ver lista de compra” | One inspector column; fields never side-scroll; S1,S2,S3,S4,S5,S6,S7,S8,S9,S10; F1/F2 |
| V3 `backing` | Add → Backing; “Aros, pedestales y paneles”; search; two-column illustrated cards with canonical names, dimensions when known, “Añadir…” accessible names; preserve old paths | Cards wrap; no stock/price invented; S1–S5,S7,S9,S10; F3 |
| V4 `catalogue` — conditional Q3 alternative | Catalogue shell; category filter Backing; heading/result count; all seven proposed props and provenance; “Abrir en Taller” only with permission; “Pieza de escenografía · sin precio de tienda” for non-store props | Facets at left ≥1024, disclosure above below 1024; S1–S5,S7,S9,S10; F3; Q3 provisional |
| V5 `shopping` / D2 | Dialog title “Lista de compra”; Mobiliario and Escenografía; e.g. 1 × rectangular table (2.40 × 0.90 m), 8 × Tiffany chair, 1 × round panel, 1 × pedestal set; “No son productos de la tienda”; no invented currency total; close to prior scene | Max 640 px modal, nearly full viewport narrow; S1–S5,S7,S9,S10; F1/F2 |
| V6 `ai` | Existing scene IA inspector; one mock conversation; text prompt; “Enviar”; pending response; result “1 mesa rectangular · 8 sillas colocadas”; existing proposal/apply interaction and manual-edit link | Input below conversation, expands above mobile keyboard; S1–S5,S6,S7,S8,S9,S10,S11; F5 |
| V7 `export` / D1 | Workshop with export group open; PNG sibling, primary “Descargar modelo GLB · Blender”; scene name, metre scale, import instruction; prepare/error/started feedback next to trigger | Popover max 320 px, fits viewport; accessible in compact narrow header; S1–S5,S7,S8,S9,S10,S11; F4 |

Visible product copy is Spanish for this draft. Semantic strings are translation-ready; bilingual rollout belongs to the language subplan (R12), not an implicit SP-3 implementation. Backing and GLB retain those names in both locales. No new language switch is introduced. Test translated labels with 40% expansion; only project name may truncate with an accessible full name. The dark/light mock selector represents both existing product themes.

## 8. Estados

`#state` es un selector nativo visible; solo se ofrecen los estados aplicables a la vista actual. `#view` usa los siete ids anteriores; `#scene` ofrece `none`, `export`, `shopping`; `#theme` ofrece `dark`, `light`. Todos tienen etiquetas visibles. El puente puede asignar un valor y generar un evento `change`. Las opciones de estado se actualizan cuando cambia la vista. El estado del diálogo proviene de la vista/estado seleccionados; los datos de ejemplo exportados nunca se descargan. El estado exclusivo del mockup indica explícitamente que cualquier cambio resultante es simulado.

| ID / selector | Resultado visible y recuperación disponible | Transición / aplicabilidad |
|---|---|---|
| S1 `ready` | Contenido estable; una acción principal clara; conteos reales | Estado inicial de todas las vistas |
| S2 `loading` | Estructura estable, mensaje etiquetado de carga/esqueleto; desactivar las acciones de añadir/exportar que dependen del contenido; la escena confirmada permanece | Todas; se resuelve en ready/empty/error; sin porcentajes inventados |
| S3 `empty` | Contexto: ninguna coincidencia de búsqueda → “No encontramos piezas” + “Limpiar búsqueda”; sin selección → “Selecciona una mesa” + volver a Añadir; lista de compra/escena vacía → “Añade una pieza para continuar” | Todas; exportar está desactivado si la escena está vacía; IA vacía significa que no hay mensajes y que se puede usar el campo de texto |
| S4 `error` | “No pudimos cargar las piezas”, “No pudimos actualizar la lista” o “No se pudo exportar el GLB”, con opción contextual para reintentar; conservar la escena/entrada válida anterior | Todas; Reintentar → pendiente/carga → ready; sin trazas de pila ni falsos éxitos |
| S5 `success` | Pieza añadida con nombre / mesa actualizada / lista al día / descarga iniciada; región de estado, sin forzar la navegación | Todas; vuelve a ready sin borrar el contenido; el éxito de exportación solo indica que se inició la descarga |
| S6 `validation` | Error debajo del campo numérico/de texto afectado, asociado mediante `aria-describedby`; conservar el valor; no modificar la última escena válida | Solo V2 y V6; corregir → ready; no aplica al catálogo/lista/exportación de solo lectura |
| S7 `disabled` | Acción no disponible con el motivo al lado (límite de escena/nodos o permisos para transferir al catálogo); ninguna acción ficticia activada que no se pueda completar | Todas; al eliminarse la condición → ready; no usar una ayuda emergente como único indicador de desactivación |
| S8 `partial` | En V2 se ajustan menos sillas; solicitadas y colocadas se indican explícitamente. En V6 hay un resultado propuesto aún sin aplicar. En V7 hay piezas sin resolver → se bloquea la exportación y se muestra “Revisa las piezas antes de exportar” | V2,V6,V7; al resolver el problema → ready; nunca generar silenciosamente un GLB parcial |
| S9 `permission-denied` | “Tu cuenta no tiene acceso a esta herramienta” y “Volver”; ocultar los datos de escena/privados; SP-1/2 determina el destino de autenticación | Todas; que se deniegue añadir desde el catálogo no borra la vista del catálogo si `catalogo.ver` sigue permitido; sin flujo de pago/actualización propia |
| S10 `offline` | “Sin conexión”; desactivar la actualización del catálogo remoto/IA; conservar la escena en memoria; “Reintentar” vuelve a comprobar la conexión | Todas; siguen disponibles las ediciones locales, la lista de compra derivada de una escena completa y la exportación de elementos ya cargados; si los recursos no están disponibles, bloquear la exportación e indicar el motivo, sin asumir que hubo un guardado en el servidor |
| S11 `pending` | “La IA está preparando una propuesta…” / “Preparando GLB…”; bloquear el envío/exportación duplicados y mantener la escena en solo lectura solo cuando sea necesario para conservar una instantánea coherente | Solo V6 y V7; al completarse → success/error; no mostrar un botón de cancelación ficticio si la operación no admite cancelación |

No se introducen resultados parciales del Backing remoto: si falla la carga del catálogo, se informa del error y los datos completos conocidos anteriormente se conservan y se muestran como desactualizados. `offline` cubre la actualización no disponible y los datos desactualizados que se conservan. No hay un estado independiente de éxito silencioso con datos desactualizados. No hace falta un estado de confirmación destructiva; estos flujos no eliminan datos. La exportación no requiere permisos aparte del permiso existente de Taller. La vista previa activa no se puede exportar hasta que se resuelva. La autorización y los derechos de acceso en tiempo de ejecución son la fuente de verdad, no los selectores del mockup.

## 9. Comportamiento adaptable

Rango admitido: desde 320 px; anchos principales para revisión: 360, 768, 1024 y 1440 px, además del reflujo a 320 px. Reutiliza el punto de corte existente de Taller de 1024 px y la regla para orientación horizontal con poca altura; 1440 px es un ancho para recopilar evidencia, no un nuevo límite de funcionalidad.

- **320–767 px:** encabezado compacto con ajuste de línea y acceso a Exportar y a la lista; 40% para la escena / el resto para la hoja activa cuando quepan ambas, vista previa de escena de al menos 180 px y panel con desplazamiento independiente; botones de pestaña de ≥44 px. Muestra un solo panel activo de Añadir/Inspector/IA; conserva la pieza seleccionada y la búsqueda al cambiar de panel. La lista de compra/exportación debe caber en `100vw - 24px`. Sin desplazamiento horizontal de la página ni gestos de arrastre obligatorios. Con ampliación alta, permite el desplazamiento vertical del documento para que la hoja no oculte campos detrás de un lienzo fijo. El título del proyecto puede acortarse; las etiquetas de acción se ajustan al ancho.
- **768–1023 px:** mismo modelo de hoja activa única; se conserva más altura de escena en el área visible; las tarjetas del catálogo pueden usar tres columnas; no comprimir el diseño de tres paneles de escritorio.
- **≥1024 px:** encabezado de 56 px, barra lateral de 60 px, panel Añadir de 300–340 px, escena flexible e inspector de 300–320 px. Con 1024 px, cierra Añadir cuando se edite para mantener la escena utilizable; en anchos mayores pueden estar abiertos ambos paneles. Desplazamiento independiente de los paneles; el área visible nunca provoca desbordamiento de la página.
- **Orientación horizontal con ancho <1024 px y alto ≤540 px:** panel activo junto a la vista previa (aproximadamente 45%/55%), no debajo; el encabezado se ajusta al ancho y no cubre el contenido; los controles tienen desplazamiento vertical. La lista de compra a pantalla completa se ajusta a la altura visible y permite el desplazamiento del contenido. A 320 px/con ampliación, prioriza la legibilidad del contenido y el desplazamiento del documento en lugar de forzar una composición lado a lado.
- El catálogo usa la barra lateral de filtros existente con ≥1024 px; por debajo de esa medida, un control de divulgación nativo encima de los resultados. El ancho mínimo de las tarjetas depende del contenido; usa dos columnas solo si caben las etiquetas; en caso contrario, una. Conserva el orden lógico de lectura del DOM y permite el crecimiento natural de las etiquetas en español/inglés.

La barra de herramientas del mockup está fuera de la estructura del producto; su altura no forma parte de las dimensiones del producto. No se requieren recursos de imagen remotos, Google Fonts ni APIs en tiempo de ejecución.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA para la interfaz modificada. Una descripción de diseño no demuestra conformidad. En producción se deben verificar el contraste renderizado, el teclado, el lector de pantalla y el reflujo.

- Un h1 por superficie; los encabezados identifican los paneles; cada campo/select tiene una etiqueta de texto visible. Las dimensiones numéricas incluyen «m», descripciones de error/rango y el modo de entrada apropiado; las sillas son enteras. Acompañar las muestras de color con etiquetas descriptivas; nunca usar solo el color para seleccionar o indicar errores.
- Los botones y los selectores nativos admiten el teclado y muestran el foco. Las pestañas seleccionadas usan semántica explícita de selección/pulsación, no solo un fondo. Los botones nativos ofrecen alternativas para agregar/seleccionar en cada operación de arrastre. Proporcionar un resumen de escena con nombre fuera del lienzo, que incluya las dimensiones de la mesa seleccionada y la cantidad real de sillas.
- La región de estado `role=status` / polite anuncia una actualización consolidada, no cada cambio del control deslizante. Los errores usan `role=alert`, con `aria-invalid` y descripciones en el campo. No revelar datos privados cuando se deniegan los permisos.
- D2 usa un diálogo nativo o un modal etiquetado equivalente, mantiene el foco dentro al pulsar Tab, admite Escape y devuelve el foco al control que lo abrió. D1 usa un grupo etiquetado no modal, el orden normal de Tab y restaura el foco al pulsar Escape. El lienzo no debe atrapar el teclado. El mockup usa un comportamiento de foco equivalente, incluido el cierre de diálogos al cambiar de vista del mockup.
- Texto normal ≥4.5:1; texto grande ≥3:1; límites de controles significativos, selección y foco ≥3:1. Los bordes suaves de los tokens son solo decorativos; los controles reciben un contorno de mayor contraste según se especifica. Los controles deshabilitados conservan una explicación legible junto a ellos.
- Se prefieren objetivos táctiles de 44 px; el mínimo WCAG para el tamaño de objetivo es 24 CSS px o un espaciado conforme para controles compactos de escritorio. El texto al 200%/zoom al 400% se redistribuye sin acciones recortadas a 320 CSS px. Ninguna información esencial depende solo del desplazamiento del puntero, el movimiento, la perspectiva o el lienzo.
- Respetar `prefers-reduced-motion`; no animar los esqueletos del mockup. Nombres de botones estables; el estado pendiente también establece la semántica de ocupado. La usabilidad real de Blender y una interfaz completa de autoría 3D no visual están fuera del alcance de este artefacto de diseño; la edición de texto, el resumen de escena y los controles modificados sí están incluidos.

## 11. Visual acceptance criteria

| ID | Breakpoint | State | Observable expectation |
|---|---|---|---|
| UI-AC-01 | ≥1024 px | ready | V1 has a visible “Mesa rectangular” entry inside Mobiliario. |
| UI-AC-02 | 320–1023 px | ready | Activating Add shows table controls in a readable active sheet without horizontal page scrolling. |
| UI-AC-03 | All | ready | V2 displays separate length, width and tabletop height fields with metre units. |
| UI-AC-04 | All | validation | An out-of-range length shows a linked field error while the scene retains its last valid geometry. |
| UI-AC-05 | All | partial | V2 shows both requested and placed chair counts when they differ. |
| UI-AC-06 | All | success | V5 displays the same placed chair count as V2 after an edit. |
| UI-AC-07 | All | ready | V3 exposes one named Backing display group inside Fondos y muebles (Q3 location pending). |
| UI-AC-08 | All | ready | V3 lists each of the seven proposed canonical Backing members once within the group (pending Q3 membership approval). |
| UI-AC-09 | 320–1023 px | empty | V3 (and conditional V4 if selected) shows “Limpiar búsqueda” without horizontal overflow. |
| UI-AC-10 | All | ready | D1 labels the GLB action with Blender and displays metre scale. |
| UI-AC-11 | All | pending | V7 shows “Preparando GLB…” and cannot start another export. |
| UI-AC-12 | All | error | V7 offers retry while leaving the committed scene visible. |
| UI-AC-13 | All | success | V7 says “Descarga GLB iniciada.” without claiming local save or Blender verification. |
| UI-AC-14 | All | empty | V7 disables GLB and explains that the scene needs a piece. |
| UI-AC-15 | 360,768,1024,1440 px | ready | Both themes use the stated shared Taller surface and accent tokens. |
| UI-AC-16 | All | permission-denied | Denied workshop content contains no scene or project details. |
| UI-AC-17 | All | ready | Closing D2 with Escape restores focus to the list trigger. |
| UI-AC-18 | All | ready | V6 exposes a manual-edit path after the table proposal is applied. |
| UI-AC-19 | All | ready | Non-store Backing pieces have no invented price or stock claim. |
| UI-AC-20 | <1024 px, height ≤540 px | ready | Active panel is beside the preview and its controls can scroll vertically. |
| UI-AC-21 | All | partial | Export is blocked with an explicit unresolved-piece reason. |
| UI-AC-22 | All | loading | Loading catalogue content retains the shell and blocks add actions. |
| UI-AC-23 | All | offline | The banner distinguishes offline status from retained local scene availability. |
| UI-AC-24 | All | ready | Keyboard focus is visible on every changed control. |
| UI-AC-25 | All | ready | The HTML exposes labelled native selects with ids view, state, scene and theme. |
| UI-AC-26 | 320 px / 400% zoom equivalent | ready | Dialog content and primary actions reflow without page-level horizontal scrolling. |
| UI-AC-27 | All | disabled | Every disabled primary action has an adjacent visible explanation. |
| UI-AC-28 | All | ready | Undo after a table edit restores the preceding dimensions and placed chair count in the inspector and shopping list. |
| UI-AC-29 | All | ready | Searching “Backing” in V3 displays the seven canonical cards and a matching filtered result count. |
| UI-AC-30 | All | ready | The HTML labels V4 as a pending Q3 alternative to the current Taller-only proposal. |

Criteria dependent on Q1–Q3 describe the illustrated proposal, not accepted decisions. If q3=a is selected, original visual groups remain for their other pieces and the seven move visually into Backing; if q3=b is selected, the same canonical cards also remain in their old groups. Original-name search remains in both. Do not interpret UI-AC-07 as a requirement to pick q3=b. V4-only criteria apply only if its surface is approved. Identity, `GrupoCatalogo` and `ASIGNACION_FONDOS` invariants require source/functional checks in T3.3/T3.8; a rendered grouping cannot prove them.

Engine/layout/scale/colour parity and old-category discovery need functional tests plus the documented Blender import; screenshot review cannot accept R9–R11 alone. HTML renders schematic geometry and simulates interactions; it does not produce a GLB, quote, actual catalogue count or live AI response.

## 12. Preguntas abiertas y supuestos

### Owner decisions requested

These mirror the still-open `rounds/round-09.json` rather than creating a second decision round. David owns the answers, with Planner reconciling SPEC/PLAN. The following are **not confirmed**:

- **Q1 — Table creation (round 9 q1).** One visible card per existing table type, immediately inserted and adjusted in the inspector (recommended and mocked), or the generic card followed by a pre-creation form? No new form is specified unless David selects that alternative.
- **Q2 — Furniture pricing (round 9 q2).** Keep quantities/dimensions under “Mobiliario · no es producto de la tienda” without prices (recommended and mocked), or introduce rental prices from an owner-supplied table? Never invent a price while this is pending.
- **Q3 — Backing membership and location (round 9 q3).** Confirm the seven canonical IDs and whether to move them from their old visual groups or show them in both. Also reconcile the SP-3 “catalogue and Taller” outcome with q3=a, which proposes only a Taller group while `/catalogo` is currently Shopify-only. Recommendation: the seven scene props as one named Backing group in Fondos y muebles with preserved search/AI/photo identities; decide explicitly whether V4 belongs in Shopify `/catalogo` or only the scene catalogue. V4 is a clearly marked alternative, not an approved new product collection. T3.3 currently has no `/catalogo` implementation files: choosing that surface requires Planner to revise task paths and acceptance before plan approval. Moving cards from their current visual groups also needs reconciliation with US-7's “no item is lost from where it is found today”.
- **Q4 — Blender verification (round 9 q4).** Portable Blender acquisition for automated real import plus one owner manual import (Planner recommendation), or file-level checks plus owner-only import? No installation is performed or authorized by this contract. Record missing real-import evidence as blocked/manual, never as passing.

No new independent owner decision was discovered. Q3 already contains a material scope mismatch (Taller scene catalogue versus Shopify `/catalogo`), and Q4=b would require aligning the unconditional automated Blender acceptance in T3.5/T3.6 with owner-only import evidence. Planner owns those reconciliations; this draft does not resolve them by choosing an option.

### Límites confirmados y supuestos explícitos

- Confirmado: R9/R10/R11 nunca se recortan; GLB, no un nuevo formato de Blender; distribución/tamaños/colores de la escena y escala en metros; agrupación Backing que conserva las identidades canónicas; estilos existentes de la aplicación; no se agrega trabajo nuevo para salas 3D. Se reutilizan los límites de las mesas de origen y el comportamiento existente de grupos editables.
- Propuesta de UX en borrador que requiere aprobación del plan: una tarjeta de creación por tipo, incluida la rectangular; controles numéricos nativos complementarios para las dimensiones; información visible sobre la capacidad solicitada y la colocada; ayuda de importación de GLB con leyendas. Son decisiones de diseño, no afirmaciones sobre el comportamiento actual de la interfaz.
- V4, la pertenencia a grupos y la compatibilidad con grupos visuales son dependencias provisionales de Q3; la presentación de precios del mobiliario depende de Q2 y el flujo de creación de Q1. Los implementadores no deben resolver estas ambigüedades por su cuenta. La planificación puede continuar; la aprobación del responsable resuelve estos puntos antes de la implementación.
- Las tareas de SP-3 son T3.1–T3.8, según se enumeran en la sección 1; todas siguen en borrador hasta que se apruebe el plan. No se reasignan silenciosamente tareas de otros subplanes.
- La exportación local requiere que todos los recursos pertinentes ya estén cargados; el modo sin conexión no lo garantiza. Los permisos provienen de SP-1/2, el comportamiento ante conflictos de proyectos almacenados proviene de persistencia y las cadenas de idioma provienen del trabajo de idiomas. Ningún éxito simulado de la interfaz implica que esas integraciones hayan sido aprobadas.
- Los datos de ejemplo del mockup usan una escena de celebración llamada «Cumpleaños · lavanda», una mesa de origen predeterminada de 2.40 × 0.90 × 0.75 m y 8 sillas Tiffany ilustrativas colocadas. La capacidad del mockup está etiquetada como ejemplo y no es un algoritmo de perímetro alternativo. Aquí no se autoriza ninguna red, proveedor de pago, descarga real, escritura en producción, cambio del repositorio ni salida adicional de bitácora.

### Previous draft verification record (2026-10-26; retained evidence, not a rerun of this revision)

Local Chromium via the existing Playwright dependency: 63 view/state combinations × 6 viewports × 2 themes = 756 layout checks; no document/dialog horizontal overflow or horizontally clipped controls. Viewports: 320×800, 360×800, 768×1024, 1024×850, 1440×980 and landscape 844×390. Ten core exercised interaction checks passed: add/select table, valid dimension update, invalid dimension retains last geometry, capacity warning, shopping uses placed chairs, Escape focus restoration, export pending blocks duplicate, honest simulated completion, AI empty-prompt validation and apply proposal. No JavaScript page errors. Representative desktop dark, mobile editor and tablet light catalogue were visually inspected. Sampled token contrast: primary white text 4.84:1 dark / 6.11:1 light; secondary labels 6.63:1 / 7.47:1; focus against panel 4.99:1 / 5.82:1. Additional final checks passed: undo/redo restored 2.40 m / 3.00 m, the seven canonical Backing cards were present, add-piece feedback and hexagonal search worked, export Escape restored focus, the shopping dialog trapped/returned focus, and the actual inline mockup bridge drove view/state/theme. No HTTP requests were made. These are scoped mockup checks, not a full accessibility audit or product/Blender acceptance. Other table-type cards represent existing-editor handoffs with explicit simulation feedback; full non-rectangular editing and real 3D geometry are not implemented by this static artifact.
