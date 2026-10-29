---
contract: gasto-ia
version: 1
status: draft
subplan: SP-6
requirements: [R4, R5]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: c
name: Desglose en el lugar
source_revision: r1
source_behavior: gasto-ia@v1.r1.behavior.md
source: gasto-ia@v1.r1.dir-c.tsx
plan_revision: 17
---

# gasto-ia@v1 — Desglose en el lugar

## 1. Identidad y trazabilidad

Borrador de planificación canónico; **no aprobado para implementación**. El propietario eligió la dirección c, «Desglose en el lugar», en la comparación web. Esa elección autoriza únicamente esta versión final; no aprueba este contrato, SP-6 ni el plan. Versión 1; no existe una versión anterior aprobada, por lo que no se reemplaza nada aprobado. Esta tarea solo escribe `design/gasto-ia@v1.md` y `design/gasto-ia@v1.html` (además del RESULT de delegación). No se modifica ningún archivo de exploración, historial, SPEC, PLAN, registro de cambios, vista previa ni producción.

Alcance: REQ-021 / M2 / SP-6 «Gasto de IA por usuario y sesión», R4 y R5, según SPEC § «Comportamiento — SP-6 (ronda 12 pendiente)» y las decisiones del propietario de la ronda 12 q1/q2, PLAN.json revisión 17 (esquema 1.3.0), `gasto-ia@v1.r1.behavior.md` y los archivos Markdown, JSON, TSX y HTML de la dirección c r1 elegida. No se registraron comentarios del propietario sobre las direcciones. Aplica una decisión posterior del propietario: **ronda 16 q4 (respondida el 2026-10-29) / PLAN SP-10 — las pantallas exclusivas para el personal, incluido el gasto de IA, permanecen en español**. La exploración (escrita antes de esa respuesta) tradujo al inglés toda la página de gastos; esta versión final corrige únicamente ese comportamiento (§11 enumera el cambio exacto).

| Requisito / criterio | Cobertura del contrato | Tareas consumidoras |
|---|---|---|
| R4 — una llamada de IA pagada y completada almacena los tokens y el coste estimado asociados al usuario y la sesión | Semántica de datos §7, metadatos de llamada V1, reglas parcial/desconocido §8, UI-AC-05–07 | T6.4 (renderizado); T6.5 verifica la atribución y la idempotencia |
| R5 — empleado/administrador ve los totales por sesión, tipo y usuario | Filtros y agrupación V1, F1–F2, UI-AC-02–04, 08 | T6.4; revisión visual T6.6 |
| Filtrar por usuario y tipo; totales por sesión y elemento de trabajo; sin instrucciones, contenido generado, secretos ni datos personales innecesarios | V1, F2, §7, UI-AC-04, 13 | T6.4; T6.6 |
| Las cuentas de Usuario, las personas con sesión cerrada o quienes no tienen `gasto.ver` no pueden acceder a la página ni a la API; validación del lado del servidor | V2/V3, F6, UI-AC-10 | T6.4; T6.5 |
| El error del proveedor con uso facturable conocido se conserva como parcial/error; los campos faltantes permanecen desconocidos | Estado `partial`, F3, UI-AC-06–07 | T6.4; T6.5 |

Consumidores de PLAN: SP-6 `ui = {contract: gasto-ia, version: 1, design_task: T6.1, visual_review_task: T6.6}`. T6.1 copia el contrato aprobado por el propietario, byte por byte, únicamente a `design/contracts/gasto-ia@v1.md` después de la aprobación independiente. T6.4 construye la página protegida por `gasto.ver` y la API con filtros del lado del servidor. T6.5 se encarga de la evidencia de atribución y autorización desde la entrada real; T6.6 revisa el panel renderizado según este contrato. T6.2/T6.3 (registro de uso y captura) y T6.7 (auditoría) no son UI y esta maqueta no los evidencia. SP-10 T10.4 debe incluir esta pantalla entre las pantallas del personal que solo están en español.

Evidencia de producto de solo lectura: t12 (HEAD `fb872bce`) y asesor `src/app/globals.css`, `src/app/layout.tsx`, `src/app/admin/page.tsx` → `src/components/admin/AdminTabs.tsx` (H1 «Panel de administración», «← Volver al chat», pestañas horizontales), `CabeceraApp`. Los contratos relacionados `cuentas-admin@v1`, `planes@v1`, `proyectos@v1` (aprobados) establecen el encabezado compartido, el menú de cuenta, el título de 24px, la regla de navegación neutra y el documento de trabajo con esquinas redondeadas; `decoraciones@v1` (borrador) usa el mismo vocabulario.

Impacto: **interfaz aditiva** — un nuevo destino de administración «Gasto de IA» dentro de la superficie de administración existente; no cambia el comportamiento de ninguna vista existente. No afecta ningún contrato aprobado.

## 2. Propósito y usuarios

Pregunta que responde: «¿A dónde fue el gasto de IA pagado, quién lo generó y en qué sesión o elemento de trabajo?»

- **Empleado interno y Administrador con `gasto.ver`**: abre Administración → «Gasto de IA», consulta un total de coste conocido con su nivel de integridad, filtra por cuenta («Usuario») y tipo de llamada («Tipo de llamada»), opcionalmente por herramienta («Herramienta»), agrupa por sesión, proyecto/conversación o usuario, abre un grupo para ver sus subtotales por tipo y herramienta y despliega una llamada para consultar sus metadatos del registro de uso. El registro es de solo lectura.
- **Cuentas de Usuario, visitantes con sesión cerrada y cualquier persona sin `gasto.ver`**: no reciben el registro de uso, los filtros, las identidades de otras personas ni los totales; solo un rechazo o una explicación de inicio de sesión con un destino de recuperación existente. El servidor aplica esta regla a la página y la API; la maqueta solo muestra la presentación.

Éxito: un miembro autorizado del personal ve totales que cuadran, distingue los costes conocidos de los desconocidos, puede localizar la cuenta/sesión/elemento de trabajo/proveedor/modelo/fecha de una llamada y nunca ve instrucciones, respuestas ni contenido generado.

## 3. Arquitectura de la información y jerarquía

El cambio se integra en la superficie administrativa existente; no es una página independiente ni una página de inicio. Orden, de arriba abajo:

1. Contenedor heredado: encabezado con el anillo y el punto de Pictures/Sempertex, selector «Idioma» ES/EN, menú de cuenta («Mi cuenta», «Planes», «Cerrar sesión»).
2. Encabezado de página: H1 «Gasto de IA» con «Volver al chat» (estilo ghost, icono de flecha a la izquierda) a la derecha.
3. Regla de navegación de administración: «Cuentas» / «Roles y permisos» / «Gasto de IA» (actual). Los enlaces solo se muestran cuando quien consulta tiene el permiso correspondiente (Q1).
4. Un único **documento de trabajo** continuo (radio de 32px):
   - Línea de contexto: «Datos de ejemplo · Solo lectura» (solo en la maqueta) y «Fecha de las llamadas · UTC · <fecha>».
   - Área de filtros (en línea): selector «Usuario» → «Tipo de llamada» Todos/Texto/Imagen → desplegable «Herramienta» → «Limpiar filtros» (a la derecha).
   - Franja de totales (1.2 : 1): a la izquierda, «Coste estimado conocido · USD», importe, «N / M llamadas con coste informado»; a la derecha, «N llamadas · N cuentas · N sesiones», «Tokens totales conocidos: X · n/m llamadas», «Total de todos los resultados filtrados; importes estimados, no es una factura.»
   - Control de agrupación «Agrupar gasto»: «Por sesión» / «Por proyecto o conversación» / «Por usuario».
   - Lista de gastos: franjas de grupo a todo lo ancho; solo una desplegada a la vez, con subtotales por tipo → lista de llamadas (desplegables nativos) → subtotales por herramienta.
   - Paginación: «n / m grupos · Los totales incluyen todos los resultados.» + «Cargar más».
   - Nota de privacidad: «Solo metadatos de uso. Sin instrucciones, respuestas ni contenido generado.»
5. Pie de página (contenedor).

Jerarquía: principal = total filtrado de coste conocido y su nivel de integridad; secundaria = franjas de grupo con su subtotal; complementaria = metadatos de llamadas, subtotales por tipo/herramienta y filtro de herramienta. Divulgación progresiva: filtro de herramienta detrás de un desplegable, metadatos detrás del desplegable de cada llamada, un grupo abierto. No hay tarjetas KPI ni panel lateral de detalles.

## 4. Sistema de diseño y lenguaje visual

No se agrega una paleta, fuente, identidad ni token semántico. Los tokens usan los nombres de `globals.css` de producción; cada tema los define una vez y los asigna a los roles de shadcn (`--background`←`--fondo`, `--card`/`--popover`←`--superficie`, `--primary`←`--acento`, `--muted`/`--secondary`/`--accent`←`--superficie-2`, `--muted-foreground`←`--texto-suave`, `--border`←`--borde`, `--input`←`--texto-tenue`, `--ring`←`--acento`, `--destructive`←`--error`).

| Token del producto | Función / uso | Claro / oscuro |
|---|---|---|
| `--fondo`, `--texto` | fondo, primer plano | `#faf9fc`/`#0b0c10`, `#1c1425`/`#f4f5f7` |
| `--superficie`, `--superficie-suave`, `--superficie-2` | documento/menú, inserto de lista de llamadas, controles seleccionados y skeleton | `#ffffff`/`#16181f`, `#faf8fd`/`#1c1e26`, `#efe9f8`/`#242733` |
| `--texto-suave`, `--texto-tenue` | texto complementario y valores desconocidos; bordes de controles (≥3:1) | `#6b6178`/`#9aa1ad`, `#766c85`/`#8a91a0` |
| `--acento`, `--acento-hover`, `--sobre-acento` | botón principal, marca, indicador de foco | `#6d3fe0`/`#9479ff`, `#5530b8`/`#a58dff`, `#ffffff`/`#120b24` |
| `--borde`, `--borde-suave` | reglas del documento, las franjas y la franja de totales; reglas del contenedor | `#e3daef`/`#383c48`, `#efe9f8`/`#2a2d38` |
| `--exito` | estado «Completada» | `#1f7a55`/`#78d6a8` |
| `--aviso`, `--aviso-suave` | texto de estado parcial, aviso de parcialidad | `#8f5f12`/`#f7c46b`, `#fff3d8`/`#3f311c` |
| `--error`, `--error-suave` | texto de estado de error | `#b23a45`/`#ff979f`, `#ffeaec`/`#43252a` |
| `--overlay` | sombra del menú de cuenta | `rgb(28 20 37/.4)` / `rgb(0 0 0/.6)` |

Tipografía: Geist Sans para el cuerpo, 15px/1.5; Geist Mono para los importes (coste por grupo y llamada, 14–16px), con cifras tabulares. H1 24px/600 (−0.4px); título de grupo 20px/600 (18px en teléfono); H2 vacío/error 20px; total 32px/600 (−0.7px), cifras tabulares; etiquetas 13px/600; metadatos 12–14px; `dt` 12px atenuado. Sin rótulos introductorios en mayúsculas.

Forma y espaciado: radio del documento 32px, lista de llamadas 24px, avisos 24px, botones/selectores/resúmenes desplegables en forma de píldora 999px, filas skeleton 24px. Margen interno del documento: 28px en escritorio / 20px en teléfono; relleno de franja 24px; márgenes exteriores 40px (≥1101px), 28px (761–1100px), 20px (≤760px). Todos los controles tienen una altura mínima de 44px.

Iconografía: lucide-react 18px, `aria-hidden`, siempre junto al texto (ChevronDown, ChevronRight, UserRound, ArrowLeft, RotateCcw, Info, CircleAlert).

Foco: contorno de 3px `--acento` con desplazamiento de 4px en cada elemento interactivo. Los botones de tipo/agrupación seleccionados usan `aria-pressed`, una superficie `--superficie-2` y un contorno `--texto`; no dependen solo del color.

Componentes (`origen:id variante estado`, ruta de importación):

| Componente | Variantes / estados | Importación |
|---|---|---|
| shadcn:button | default (principal: «Reintentar», «Cargar más», «Abrir Mi cuenta», «Iniciar sesión», «Limpiar filtros» en estado vacío), outline (control de tipo, elementos del menú de cuenta), ghost («Volver al chat», agrupación, «Limpiar filtros» en el área de filtros) / normal, hover, focus, pressed (`aria-pressed`), disabled | `@/components/ui/button` |
| shadcn:skeleton | fila de 88px / cargando | `@/components/ui/skeleton` |
| kit:motion | expresivo, natural, sutil, reducido; resorte del perfil al presionar una franja | `useMotionProfile` de `@kit/motion`; `motion.button` de `motion/react` |
| native:select user-filter / tool-filter / language | predeterminado, foco, deshabilitado (cargando) | `select` nativo con `label` |
| native:details more-filters / call / account-disclosure | cerrado, abierto | `details/summary` nativo |
| custom:filter-workbench | inactivo, con filtros, cargando (deshabilitado) | `div` etiquetado «Filtros» |
| custom:total-strip | conocido, cobertura-parcial | `div` `aria-live=polite` `aria-atomic` |
| custom:group-tabs | sesiones, trabajo, usuarios / presionado | `nav` «Agrupar gasto» + botones |
| custom:usage-band | contraído, desplegado, coste-desconocido | `section` + `h2 > button[aria-expanded]` |
| custom:call-row | éxito, parcial, error / cerrado, abierto | `details` con metadatos en `dl` |
| custom:notice | parcial (aviso), alcance (neutro) | `role=status` |
| custom:empty-block | vacío, error-de-carga (`role=alert`), denegado, sesión-cerrada | `div` con H2, texto y acción principal |
| custom:brandmark | anillo y punto | SVG en línea del contenedor relacionado |

AdminTabs de producción usa `@/components/ui/tabs`; la regla de navegación de aquí sigue la regla de enlace neutro de los contratos relacionados (`aria-current=page`), ya aprobada en `cuentas-admin@v1`.

Movimiento (firma de la dirección — «compresión táctil y asentamiento»), curva `cubic-bezier(.34,1.4,.64,1)`:

| Elemento | Movimiento | expresivo / natural / sutil |
|---|---|---|
| Franjas de grupo | scaleY .975 + 5px → leve sobreimpulso → reposo, escalonado | 520 / 320 / 160 ms; intervalos 55 / 30 / 12 ms |
| Importe total | scaleX .965 → 1.012 → 1 en cada cambio de filtro | duración de asentamiento |
| Cuerpo del grupo desplegado | translateY −5px, scaleY .985 → reposo | duración de asentamiento |
| Metadatos de llamada, campo de herramienta | scaleX .975 → reposo | duración de asentamiento |
| Avisos | scaleY .97 → reposo | duración de asentamiento |
| Botones | al pasar el cursor −1px; al presionar scale .965 + 1px | 170 / 140 / 100 ms |
| Activación de franja | al presionar scale .993 con resorte del perfil | resorte |

Solo se anima la transformación; no se reduce la opacidad y el texto permanece legible en todo momento. El ajuste de movimiento reducido del sistema operativo, «Quieto» y `?still=1` eliminan todas las animaciones/transiciones/transformaciones y muestran el contenido final. Las animaciones CSS se pausan mientras la pestaña está oculta. No hay bucles infinitos.

## 5. Navegación y modelo de interacción

- **Entrada:** Administración → «Gasto de IA» (regla de navegación). No se especifica la ruta exacta del producto (Q1); `#gasto` en la maqueta es un ancla del artefacto, no un contrato de ruta.
- **Salida:** «Volver al chat» (existente), «Cuentas» / «Roles y permisos» (`cuentas-admin@v1`, relacionado), menú de cuenta → «Mi cuenta», «Planes», «Cerrar sesión» (contratos relacionados). En la maqueta, estos muestran un aviso de alcance «<destino> · Destino existente fuera de este contrato.»
- **Idioma:** el selector «Idioma» del encabezado y el pie de página siguen el mecanismo de idioma compartido (SP-8). El título, la regla de navegación, el documento de trabajo, los avisos y todos los textos sobre gastos permanecen **en español en ambos idiomas** (SP-10, ronda 16 q4); esas regiones llevan `lang="es"` mientras `html[lang]` sigue el idioma de la solicitud. El formato numérico de la región de gastos usa la agrupación del español (es-CO) en ambos idiomas.
- **Filtros** se aplican inmediatamente al cambiar. Cambiar «Usuario», «Tipo de llamada» o «Herramienta» contrae el grupo abierto y reinicia la paginación a la primera página; el foco permanece en el control modificado. «Limpiar filtros» restablece los tres filtros y la paginación, y vuelve a abrir el primer grupo; está deshabilitado cuando no hay filtros activos (excepto en el estado vacío) y durante la carga.
- **Agrupación:** los botones cambian la disposición en el mismo lugar (no cambian de ruta); el botón activo conserva `aria-pressed=true` y, al terminar el cambio, el foco vuelve a él. Los filtros se mantienen al cambiar la agrupación.
- **Grupos:** activar una franja la abre y cierra cualquier otra; activar la franja abierta la cierra. Al cargar por primera vez y después de limpiar los filtros, el primer grupo queda abierto.
- **Llamadas:** cada llamada es un desplegable nativo; al abrirlo, muestra los metadatos en el mismo lugar; el foco permanece en su resumen.
- **«Cargar más»** añade los siguientes grupos; el total sigue describiendo todos los resultados filtrados.
- No hay diálogos, por lo que no hay una trampa de foco ni un selector `scene`.

## 6. Flujos

**F1 Revisar el gasto.** Acceso autorizado → esqueleto de carga → total + cobertura → elegir agrupación → abrir un grupo → consultar subtotales por tipo («Texto: $…», «Imagen: $…») y por herramienta («Chat: $…», «Taller 3D: $…») → expandir una llamada → metadatos.

**F2 Filtrar la revisión.** Elegir «Usuario» o «Tipo de llamada», o ambos; opcionalmente abrir «Herramienta: Todas» y elegir una herramienta → el total, la cobertura, los conteos y los grupos se actualizan juntos, y el importe se reposiciona → «Limpiar filtros» restaura el alcance completo. Sin coincidencias → estado vacío (F5).

**F3 Investigar el uso incompleto del proveedor.** Una llamada parcial o con error aparece con su estado («Error · uso parcial» o «Error · coste desconocido») y el aviso «Hay errores del proveedor con uso facturable conocido y metadatos incompletos. / El coste conocido se incluye. Lo no informado queda desconocido; no equivale a cero.» Se incluyen el coste y los tokens conocidos; los campos faltantes muestran «No informado»; un grupo cuyas llamadas no tienen coste muestra «Desconocido», nunca `$0.0000`.

**F4 Recuperarse de un error de carga.** «No se pudo cargar el gasto» / «No se muestran totales sin confirmar. Conservamos los filtros para que puedas reintentar.» + «Reintentar» → vuelve a ejecutar la consulta autorizada al servidor con los mismos filtros → normal.

**F5 Vacío.** «No hay llamadas para estos filtros» / «Cambia o limpia los filtros para revisar otras llamadas. Si no hay llamadas registradas, aparecerán cuando haya uso de IA.» + «Limpiar filtros». No se muestra ningún total.

**F6 Acceso denegado / sesión cerrada.** Usuario sin `gasto.ver`: «Sin acceso» / «Tu cuenta no tiene permiso para ver el gasto de IA.» + «Abrir Mi cuenta». Sesión cerrada: no se revela información de la cuenta; «Inicia sesión para continuar» / «El gasto de IA requiere una sesión y permiso de acceso.» + «Iniciar sesión»; el foco pasa al H1. La regla de ruta, los filtros y el registro no se muestran; el servidor nunca envía datos prohibidos para ocultarlos en el cliente.

## 7. Especificaciones de vistas

Todas las vistas comparten §3; el selector de inspección `view` cambia la agrupación (en producción: los botones de agrupación).

**V1a `sessions` — Por sesión.** Banda: título «Sesión …<sufijo>», subtítulo = cuenta, metadatos «N llamadas» + elemento de trabajo (nombre del proyecto o «Conversación …<sufijo>»), coste + «USD estimados», chevrón.

**V1b `work` — Por proyecto o conversación.** Las llamadas de un proyecto se agrupan en el proyecto (todas sus conversaciones y sesiones); las llamadas sin proyecto se agrupan en «Conversación …<sufijo>». Metadatos «N llamadas» + «N sesiones». Cada llamada conserva la conversación, la cuenta y la sesión (ronda 12 q1).

**V1c `users` — Por usuario.** Título = cuenta, subtítulo «Gasto de esta cuenta», metadatos «N llamadas» + «N sesiones».

**Fila de llamada (todas las vistas).** Resumen: «<Tipo> · <Herramienta>», subtítulo «<Proyecto> / Conversación …<sufijo> · Sesión …<sufijo>», etiqueta de estado («Completada», «Error · uso parcial», «Error · coste desconocido»), tokens («2.800 tokens» o «No informado»), coste (o «Desconocido»). Metadatos `dl`: Usuario, Sesión, Proyecto / conversación, Proveedor / modelo, Tokens de entrada, Tokens de salida, Tokens totales informados, Fecha · UTC, Estado («Completada», «Error del proveedor · uso parcial facturable», «Error del proveedor · coste desconocido»). Los tokens de entrada, de salida y totales son campos independientes; ninguno se calcula a partir de los demás.

**V2 acceso denegado, V3 sesión cerrada.** El encabezado y «Volver al chat» se mantienen; la regla de ruta y el contenido de la hoja se sustituyen por el bloque vacío de F6.

Semántica de los datos: coste estimado en USD con 4 decimales (Q3); una suma incluye solo valores conocidos y siempre muestra su cobertura («n / m llamadas con coste informado», «n/m llamadas» para los tokens). La agrupación usa identificadores estables del servidor; la interfaz muestra sufijos breves, no los identificadores completos, y no muestra correos electrónicos ni otros datos personales aparte del nombre visible de la cuenta. Fechas etiquetadas como UTC (Q2).

Datos de ejemplo (ilustrativos, sintéticos): normal = cuatro llamadas completadas, dos cuentas («Cuenta de ejemplo», «Cuenta de ejemplo · 2»), sesiones …a41/…b72: `0.0042 + 0.0600 + 0.0030 + 0.0360 = $0.1032`; Texto `$0.0072`, Imagen `$0.0960`; …a41 `$0.0642`, …b72 `$0.0390`; 4.800 tokens en 2/4 llamadas. El estado parcial añade una llamada parcial (`$0.0010`, 300 tokens) y una llamada con error en la sesión …c13 (1.200 tokens, coste desconocido): total `$0.1042`, 5 / 6 con coste conocido, 6.300 tokens en 4/6 llamadas. Proveedores/modelos (Google / gemini-3.6-flash, fal.ai / FLUX.2) pertenecen al vocabulario existente del repositorio; los costes no son afirmaciones sobre precios. Todas las fechas son 2026-10-29.

## 8. Estados

| Estado | Qué aparece | Qué se puede hacer / recuperación |
|---|---|---|
| `normal` | Total, cobertura, grupos (primero abierto), paginación, nota de privacidad | F1, F2 |
| `loading` | «Cargando gasto…», tres filas de esqueleto, `aria-busy=true`; sin totales; filtros y «Limpiar filtros» deshabilitados | Esperar |
| `empty` | Explicación de F5 y «Limpiar filtros»; sin total monetario. Incluye tanto las llamadas sin coincidencias como la falta de uso registrado | Limpiar/cambiar filtros |
| `error` | Alerta de F4, filtros conservados y habilitados, sin cifras | «Reintentar» |
| `partial` | Aviso (F3), uso conocido incluido, valores desconocidos etiquetados; se puede acceder a una tercera sesión con coste desconocido mediante «Cargar más» | Inspeccionar llamadas; cargar más |
| `denied` | V2 | «Abrir Mi cuenta» |
| `signed-out` | V3 | «Iniciar sesión» |
| estados de controles | hover, foco, presionado, deshabilitado, paneles de detalles abiertos/cerrados en los controles reales | — |

No aplicables: validación (solo selectores enumerados), guardar/éxito, editar/eliminar, presupuestos/límites (SPEC: los límites quedan fuera), exportación, diálogos. Sin conexión/datos desactualizados: una lectura no disponible usa `error`; no se muestran cifras en caché. No se ha decidido qué ocurre si falla una página posterior («Cargar más») (Q4); la adición del prototipo es local e inmediata.

Transiciones: un cambio de filtro reposiciona el total y restablece los grupos; los cambios de estado sustituyen el contenido sin dejar cifras desactualizadas; con movimiento reducido se muestran los estados finales de inmediato.

## 9. Comportamiento adaptable

Compatible desde 360px; puntos de transición en 760px y 1100px (contenedor compartido).

| Rango | Diseño |
|---|---|
| ≥1101px | Ancho máximo de la aplicación: 1520px; márgenes laterales de 40px; margen interior de la hoja de 28px. Filtros en una sola fila con «Limpiar filtros» alineado a la derecha; franja del total en dos columnas 1.2fr/1fr; cuadrícula de bandas `identity | meta (≥160px) | cost 150px | chevron`; cuadrícula de llamadas `title | tokens | cost 125px | chevron`; metadatos de llamada en tres columnas. |
| 761–1100px | Márgenes laterales de 28px. Los metadatos de la banda pasan debajo de la identidad; coste y chevrón se mantienen a la derecha en la primera fila; metadatos de llamada en dos columnas. |
| 360–760px | Márgenes laterales de 20px y margen interior de la hoja. La cabecera principal se apila; las herramientas de cabecera ocupan todo el ancho; se oculta la etiqueta del rol de cuenta; el menú de cuenta se alinea con su borde izquierdo. Los filtros se apilan en una columna, con selectores a ancho completo; el control de tipo ocupa una fila de tres columnas; «Limpiar filtros» queda a la izquierda. La franja del total ocupa una columna. Los botones de agrupación forman una lista vertical. Banda: identidad, metadatos y luego coste debajo (alineado a la izquierda), chevrón arriba a la derecha; título del grupo de 18px. Llamada: título, tokens y coste apilados, chevrón arriba a la derecha; metadatos en una columna. La paginación se apila. |

No hay desplazamiento horizontal de página en ningún rango, tema o idioma; las etiquetas largas de modelos/identidad se ajustan (`overflow-wrap:anywhere`). No se descarta contenido en teléfonos.

## 10. Objetivos de accesibilidad

Objetivo WCAG 2.2 AA, por verificar en la implementación renderizada.

- Regiones/estructura: `header`; `nav` «Administración» con `aria-current=page`; `section` «Revisión de gasto» con `aria-busy` durante la carga; `nav` «Agrupar gasto»; cada banda es una `section` etiquetada por su `h2 > button`; metadatos como `dl`.
- Teclado: todos los controles en el orden del DOM; las bandas se alternan con Enter/Space (`aria-expanded`, `aria-controls`); detalles y selectores nativos; el foco se conserva en el filtro modificado y vuelve al botón de agrupación presionado; H1 (`tabindex=-1`) recibe el foco al cerrar la sesión.
- Anuncios: franja del total con `aria-live=polite aria-atomic`; carga, vacío y parcial con `role=status`; error de carga con `role=alert`.
- Idioma: `lang="es"` en las regiones del personal cuando el contenedor está en inglés, para que la tecnología de asistencia pronuncie correctamente el texto en español.
- Contraste: texto ≥4.5:1; bordes de controles, foco y selección ≥3:1 en ambos temas. El estado siempre se expresa con palabras, nunca solo con color; los valores desconocidos se expresan con palabras («Desconocido», «No informado»).
- Tamaño objetivo ≥44×44px; reorganización a 360px (320px y zoom de 200–400% siguen siendo verificaciones de producción).
- Movimiento reducido según §4.

## 11. Criterios de aceptación visual y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 360px+ | todos | La cabecera principal con marca de anillo y punto, selector «Idioma», H1 «Gasto de IA», «Volver al chat» y pie de página son visibles en ambos temas. |
| UI-AC-02 | ≥1101px | normal | Los filtros aparecen en una fila horizontal sobre una franja del total de dos columnas y bandas de grupo a ancho completo; no hay panel lateral de inspección ni cuadrícula de tarjetas KPI. |
| UI-AC-03 | 360–760px | normal | Los filtros se apilan en una columna con una fila de tres botones de tipo, los botones de agrupación se apilan verticalmente, el importe de cada banda aparece debajo de su identidad y la página no tiene desplazamiento horizontal. |
| UI-AC-04 | 360px+ | normal | Al elegir «Texto» se muestra `$0.0072`; luego, al elegir la cuenta «Cuenta de ejemplo», se muestra `$0.0042`; el foco se conserva en el control modificado. |
| UI-AC-05 | 360px+ | normal | Al expandir una llamada se muestran Usuario, Sesión, Proyecto / conversación, Proveedor / modelo, Tokens de entrada, Tokens de salida, Tokens totales informados, Fecha · UTC y Estado. |
| UI-AC-06 | 360px+ | partial | El total muestra `$0.1042`, «5 / 6 llamadas con coste informado» y «Tokens totales conocidos: 6.300 · 4/6 llamadas», con el aviso encima. |
| UI-AC-07 | 360px+ | partial | «Cargar más» añade la sesión …c13, cuyo coste aparece como «Desconocido» (no `$0.0000`); el total se mantiene en `$0.1042`. |
| UI-AC-08 | 360px+ | loading / error | La carga muestra tres filas de esqueleto y «Cargando gasto…»; el error muestra «No se pudo cargar el gasto» con «Reintentar»; ninguno muestra un total. |
| UI-AC-09 | 360px+ | empty | Se muestran «No hay llamadas para estos filtros» y «Limpiar filtros»; no se renderiza ningún total monetario. |
| UI-AC-10 | 360px+ | denied / signed-out | No aparecen la regla de ruta, los filtros, el total ni los grupos; se ofrece «Abrir Mi cuenta» (acceso denegado) o «Iniciar sesión» (sesión cerrada). |
| UI-AC-11 | 360px+ | cualquier agrupación | Cambiar entre «Por sesión» / «Por proyecto o conversación» / «Por usuario» conserva los filtros y el total; el botón activo permanece presionado y enfocado. |
| UI-AC-12 | 360px+ | contenedor EN | Con «Idioma» EN, la cabecera principal, el menú de cuenta y el pie de página están en inglés, mientras que el H1, la regla de ruta y cada texto de la hoja de trabajo permanecen en español y llevan `lang="es"`. |
| UI-AC-13 | 360px+ | todos | No aparece ningún prompt, respuesta ni contenido generado; la nota de privacidad «Solo metadatos de uso…» aparece debajo de los grupos. |
| UI-AC-14 | 390 / 1280px | expandido | Los metadatos expandidos, el menú de cuenta y el selector de herramientas permanecen dentro del área visible en ambos temas e idiomas del contenedor. |
| UI-AC-15 | 360px+ | reducido / quieto | Todos los campos, controles y estados están presentes sin animaciones en curso. |
| UI-AC-16 | ≥1101px | primer renderizado | Las bandas aparecen con un escalonamiento visible y el total se reposiciona tras cada cambio de filtro en ~520ms (expresivo). |
| UI-AC-17 | 360px+ | cualquiera | Cada control interactivo tiene una altura ≥44px y muestra el contorno de acento de 3px al recibir el foco del teclado. |

Verificación del HTML canónico generado en esta finalización:

- Origen: `gasto-ia@v1.r1.dir-c.tsx`, la opción elegida, copiada a un directorio de trabajo temporal fuera de la bitácora (`/tmp/gasto-ia-final.ktCO/gasto-ia@v1.tsx`, temporal, no forma parte del registro) con una corrección de comportamiento: (1) un traductor `shell()` para la etiqueta de idioma de la cabecera, el panel de cuenta y el pie de página, mientras que el texto de las regiones del personal usa solo español; (2) `lang="es"` en el encabezado, la regla de ruta, el aviso de alcance y la hoja; (3) agrupación de números en español siempre en la región del personal; (4) la clave para reposicionar el total ya no incluye el idioma; (5) el texto del aviso de alcance cambia de «fuera de esta exploración» a «fuera de este contrato». El diseño, CSS, tokens, componentes, datos de ejemplo y movimiento no cambiaron. Los archivos de exploración no se modificaron.
- Generación: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /tmp/gasto-ia-final.ktCO/gasto-ia@v1.tsx --out design/gasto-ia@v1.html` → 526 KB, 1,956 archivos de origen, sin conexión, código de salida 0. Espacio de trabajo: instalado y generado, 96/96 elementos.
- Contraste: `python3 <kit>/kit/contrast.py design/gasto-ia@v1.html` → 158 pares en modo claro y oscuro, todos aprobados, código de salida 0.
- Auditoría: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py design/gasto-ia@v1.html` → 84 renderizados (84 previstos), 2,648 mediciones de texto, 432 paradas de foco, código de salida 0. **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, espaciado ni desbordamiento.**
- Prueba de comportamiento (Playwright en línea, `?still=1`): 34/34 verificaciones: totales `$0.1032`/`$0.0072`/`$0.0042`, foco conservado, filtros limpiados; contenedor EN con encabezado/recorrido/hoja en español, `html[lang=en]`, hoja `lang=es`, pie de página y menú de cuenta en inglés; parcial `$0.1042`, 5 / 6, 6.300, 4/6; «Cargar más» añade un grupo con coste desconocido sin cambiar el total; las tres agrupaciones; campos de metadatos de llamadas; estados de acceso denegado/sesión cerrada sin registro; carga, error + reintento, vacío; sin desbordamiento horizontal a 1280/390 en ambos temas; sin errores de página; sin solicitudes de red. Se inspeccionaron capturas a 1280 en modo claro y a 390 en modo oscuro: la composición coincide con la dirección elegida.

| Artefacto | SHA-256 |
|---|---|
| `design/gasto-ia@v1.r1.dir-c.tsx` (origen elegido) | `b8bc764b05127c34cd7f43d1d0965532e0f9bec34887b94a4cf9202b98f0182e` |
| `design/gasto-ia@v1.r1.dir-c.html` (exploración) | `a7f43154cc781c45b7cb16e2108c83cc399e51ece7bb2d9aa19ee9ec98eae037` |
| TSX temporal con la corrección | `7658718e25f75c3ee479eed943e7e0618311044d51232d7882a802210f8adca1` |
| `design/gasto-ia@v1.html` (reconstrucción canónica) | `b685b198f2992c232399d2159fe7f25f60fd6788696dbab4659198f81e9e781c` |

Selectores de inspección: `view` (sessions, work, users — «Vista»), `state` (normal, loading, empty, error, partial, denied, signed-out — «Estado»), `theme` («Tema»), `motion` («Movimiento»); no hay `scene`. Los datos estáticos de ejemplo no demuestran la autorización del servidor, la corrección del registro, la idempotencia ni la paginación con cursor; eso corresponde a T6.4/T6.5.

## 12. Preguntas abiertas y supuestos

Preguntas abiertas (responsable de la decisión: David con el Planner):

- Q1: ¿Cuál es la ruta de gasto y cómo se ve la entrada de administración para un Empleado interno que no tiene permisos de usuarios/roles (ocultar «Cuentas» / «Roles y permisos» como se muestra, u ofrecer otra entrada)? Hasta que se responda, los enlaces solo se muestran para los permisos concedidos.
- Q2: ¿El personal debe leer las fechas en UTC (como se muestra) o en America/Bogota, como en el registro de cuentas relacionado?
- Q3: ¿Son suficientes cuatro decimales para USD o los importes inferiores a $0.0001 deberían usar más precisión para que un costo distinto de cero nunca aparezca como `$0.0000`? Relacionado: la región en español separa los millares con «.» («4.800»), mientras que los importes en USD usan «.» como separador decimal («$0.1032»); confirma si USD debe conservar la notación «$0.1032» o seguir es-CO («US$ 0,1032»). Hasta que se responda, T6.4 se muestra como está.
- Q4: ¿Qué texto y opciones de recuperación aparecen cuando falla una página posterior («Cargar más»), y los grupos ya cargados permanecen visibles? Propuesta para decidir: conservar los grupos cargados y mostrar un error en línea debajo de ellos con «Reintentar».

Decisiones confirmadas: el acceso requiere `gasto.ver` en la página y la API (del lado del servidor); solo metadatos, sin prompts/respuestas/contenido generado; filtros por usuario y tipo, totales por sesión, elemento de trabajo y usuario; total del proyecto con detalles de la conversación, llamadas independientes por conversación (ronda 12 q1); el uso facturable conocido en errores del proveedor se conserva como parcial/error, los campos ausentes son desconocidos, nunca cero (ronda 12 q2); sin límites de gasto (ronda 2); pantallas para el personal, incluido el gasto en IA, en español (ronda 16 q4, SP-10); el registro es de solo lectura.

Supuestos (decisiones visuales provisionales, no son una API ni configuración nuevas): un grupo expandido a la vez, inicialmente el primero; tres modos de agrupación; filtro opcional de herramientas detrás de un control desplegable; el total abarca todos los resultados filtrados sobre los grupos paginados (requiere un agregado del lado del servidor); el nombre para mostrar de la cuenta es el único dato personal que se muestra; «Datos de ejemplo», los avisos de alcance y los selectores de inspección de la maqueta son ayudas de inspección, no texto del producto.
