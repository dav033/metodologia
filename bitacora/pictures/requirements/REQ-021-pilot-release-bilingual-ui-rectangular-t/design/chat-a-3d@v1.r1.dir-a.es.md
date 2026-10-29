---
contract: chat-a-3d
version: 1
status: draft
subplan: SP-12
requirements: [R13]
direction: a
revision: r1
name: Mesa de recomendaciones
owner: David
date: 2026-10-29
---

# Mesa de recomendaciones — exploración A

## 1. Identidad y trazabilidad

Exploración de `chat-a-3d@v1`, **borrador; sin aprobación**. Esta nota acompaña únicamente a `chat-a-3d@v1.r1.dir-a.*`; no sustituye ni modifica el contrato canónico. El propietario elige la dirección y después aprueba el contrato con el plan. No existe una revisión anterior de esta dirección.

Alcance: brief compartido `chat-a-3d@v1.r1.behavior.md`, SP-12/R13. SPEC.md y PLAN.md/PLAN.json actuales se consultaron como contexto, sin convertir tareas técnicas en alcance visual. Consumidor identificado: SP-12, `ui.contract=chat-a-3d`, versión 1, copia T12.1, implementación de tarjetas T12.3 y revisión visual T12.5. Compatibilidad **sin determinar** hasta la selección y aprobación; no hay un contrato anterior que migrar. La galería y la separación de herramientas pertenecen a SP-7; la identidad y el guardado del proyecto, a SP-4. La exploración no cambia esos contratos ni su estructura.

Fuentes consultadas en ambos repositorios, solo lectura: `src/app/globals.css`, `src/components/ui/shell/CabeceraApp.tsx`/`MenuApp.tsx`, el chat `src/components/guiado/VistaGuiada.tsx`, `src/lib/globos3d/escenas-presets.ts`, `biblioteca.ts` y `escena.ts`. La ruta confirmada del chat normal es `/asistente`. Se leyeron los contratos y el HTML relacionados `cuentas-admin@v1`, `planes@v1`, `proyectos@v1`: rigen la cabecera Pictures/Sempertex, el anillo/punto, Geist, la navegación horizontal, el pie y las formas. Su estado de borrador no se presenta como aprobación.

## 2. Propósito y usuarios

La persona describe la celebración, un tamaño aproximado y los colores en dos o tres mensajes, y compara dos o tres decoraciones existentes con su vista, nombre localizado y cantidad de globos. Todas las cuentas con acceso al chat reciben las mismas tarjetas. Solo `decoraciones.explorar` agrega «Abrir en el Taller»; sin ese permiso no hay botón, bloqueo, explicación de planes ni invitación a cambiar de plan.

La dirección responde una pregunta operativa: «¿Qué decoración existente encaja y cuántos globos lleva?». Mantiene la conversación mientras los resultados se consultan a un lado. No introduce recomendaciones comerciales, precios, clasificaciones inventadas ni una página nueva.

## 3. Arquitectura, enfoque y elección de miniatura

**Elegida: candidate-1**, mesa dividida. La miniatura candidate-2 conserva todo en el hilo con dos tarjetas verticales en paralelo; se conserva como evidencia, no como segunda pantalla. La primera aprovecha mejor el ancho disponible para comparar cantidades y opciones de apertura, mantiene el contexto junto a los resultados y permite agregar la tercera recomendación como otra fila. La segunda exigiría desplazarse por el hilo para volver a la necesidad y comprimiría más los nombres.

Orden compartido: cabecera heredada → título y acción existente para reiniciar → navegación horizontal → anclas locales → área de trabajo → pie. Escritorio: conversación y compositor en una columna, recomendaciones en otra. Móvil: conversación, resultados, compositor. No se copia una página de inicio ni se sustituye la navegación global por una barra lateral. El compositor permanece en el flujo y las anclas permiten llegar a cada grupo sin crear subrutas.

## 4. Sistema visual y ocho ejes

| Eje | Expresión presente en la dirección |
|---|---|
| concept | Mesa operativa: la necesidad y dos o tres decoraciones listas se consultan simultáneamente dentro del chat existente. |
| layout | Rejilla de trabajo con conversación y compositor a la izquierda, panel de recomendaciones a la derecha; cada decoración ocupa una fila con vista, nombre, cantidad y opción para abrir. En móvil, título de la tarjeta a todo el ancho y vista, cantidad y acción debajo. |
| navigation | Estructura horizontal heredada y dos anclas locales Conversación / Decoraciones 3D; apertura contextual como proyecto nuevo y retorno al chat, sin otro nivel de navegación global. |
| typography | Geist Sans del producto; H1 24px, H2 20px, nombre 16px/15px móvil; cantidad tabular 26px/24px. Geist Mono 11–12px reservado para metadatos. |
| density | Densidad operativa con dos columnas de proporción .82:1.35, separación de 24px y filas de pares. Margen interior de 24px en escritorio y 20px en móvil; formas heredadas de 32/24/18px y botones píldora de 44px como mínimo. |
| components | Button, Textarea, Skeleton y AlertDialog reales del workspace instalado. Tarjetas propias compuestas como filas; detalles de cuenta, selectores nativos y marca anillo/punto heredados. |
| colour | Tokens de Pictures en globals.css, idénticos a los contratos relacionados; acento para apertura y foco, superficies neutras para conversación y filas. Los bordes de controles usan texto-tenue, como en los contratos relacionados; sin paleta nueva. |
| motion | Secuencia breve por capas: tablero 8px vertical, encabezados 4px vertical, tarjetas 18px horizontal y desfase de 65ms; 380ms expressive, 280ms natural, 160ms subtle, curva de aceleración productiva cubic-bezier(.23,1,.32,1). Controles 140ms/90ms. La carga respira a 1.3s; se suspende fuera de la vista y en pestañas ocultas. Reduced/Quieto/still elimina el movimiento sin eliminar información. |

Los tokens exactos de Pictures se asignan una vez por tema a los roles del kit:

| Fuente Pictures → roles | Claro / oscuro |
|---|---|
| `--fondo` → background | `#faf9fc` / `#0b0c10` |
| `--superficie` → card, popover | `#ffffff` / `#16181f` |
| `--superficie-suave` → vista esquemática | `#faf8fd` / `#1c1e26` |
| `--superficie-2` → secondary, muted, accent | `#efe9f8` / `#242733` |
| `--texto` → foregrounds | `#1c1425` / `#f4f5f7` |
| `--texto-suave` → muted-foreground | `#6b6178` / `#9aa1ad` |
| `--texto-tenue` → input | `#766c85` / `#8a91a0` |
| `--acento` → primary, ring | `#6d3fe0` / `#9479ff` |
| `--sobre-acento` → primary-foreground | `#ffffff` / `#120b24` |
| `--acento-hover` → primary-hover | `#5530b8` / `#a58dff` |
| `--borde` / `--borde-suave` → bordes / reglas | `#e3daef` / `#383c48`; `#efe9f8` / `#2a2d38` |
| `--exito`, `--error`, `--aviso` → success, destructive, warning | Valores exactos existentes por tema; sin colores nuevos |

Geist y Geist Mono se incrustan desde archivos WOFF2 locales de la compilación existente de t12; no se solicitan fuentes ni imágenes externas. Los radios de 32/24/18px y la forma de píldora pertenecen al vocabulario de los contratos relacionados seleccionados. No hay recurso alternativo al HTML del kit ni cambios de identidad.

Componentes reales: `shadcn:button default|outline default|hover|focus|pressed|disabled`, `@/components/ui/button`; `shadcn:textarea default|focus`, `@/components/ui/textarea`; `shadcn:skeleton loading`, `@/components/ui/skeleton`; `shadcn:alert-dialog reset open|closed`, `@/components/ui/alert-dialog` (Base UI/Animate UI instalado). Composiciones propias: `.recommendation-card`, `.working-board`, vista SVG esquemática. `native:select` para inspectores/idioma y `native:details` para la cuenta; no se atribuyen a shadcn. La entrada importa `mountMockup/useMockup` y `useMotionProfile`; el entorno de ejecución aporta los selectores nativos `view`, `state`, `scene`, `theme`, `motion` y sus etiquetas en español fuera del producto.

## 5. Navegación e interacción

Entrada `/asistente`, dentro de la estructura existente. «Conversación» y «Decoraciones 3D» son anclas locales con nombre y foco visible; no son pestañas que oculten contenido. Las rutas de herramientas/cuenta externas al subplan se representan como contexto y no ejecutan navegación en el archivo estático. La muestra sin permiso omite también la herramienta de costos por la cuenta base ilustrativa; esto no redefine el catálogo de permisos de SP-1/SP-7.

Abrir una tarjeta usa **el id devuelto por la galería**, destino `/3d?decoracion=<id>` como proyecto nuevo sin guardar. `data-destination`/`data-route` documentan ese destino en la simulación, sin navegar ni generar tráfico de red. El mockup conserva la selección entre estados, muestra los estados pendiente/error y un contexto del Taller heredado con la escena elegida y «Sin guardar». El Taller se ilustra como límite del flujo; no se rediseña. Guardar, proteger el trabajo previo y persistir siguen regidos por proyectos@v1. No se guarda automáticamente ni se sobrescribe un proyecto existente desde una recomendación.

El compositor permite enviar mediante el botón o Enter; Mayús+Enter agrega una línea y la composición IME no envía. Si no hay contenido o la solicitud está en curso, Enviar está desactivado; el borrador permanece editable. Reiniciar usa el AlertDialog existente; Cancelar recibe el foco inicial y lo devuelve a la acción. Confirmar limpia solo la sesión simulada y enfoca el compositor. La cuenta conserva el control de expansión y Escape; el cambio de idioma usa la misma variable que el inspector de idioma.

## 6. Flujos

1. Inicio → pregunta «¿Qué vas a celebrar?» → primera respuesta → pedir tamaño y colores → segunda respuesta → carga → dos o tres tarjetas. La necesidad puede estar completa en dos mensajes; el motor no debe exigir tres por diseño.
2. Comparar vista, nombre y conteo por tarjeta → abrir solo con `decoraciones.explorar` → pendiente → `/3d?decoracion=<id>` → proyecto nuevo sin guardar. Error de apertura mantiene tarjetas/contexto y ofrece Reintentar; no declara creación exitosa.
3. Sin permiso de apertura → mismas recomendaciones y datos; tarjeta sin acción ni hueco reservado al botón. No se nombra un plan.
4. Sin coincidencia suficientemente buena → ninguna tarjeta inventada → mensaje de ausencia y foco al compositor para revisar tamaño/colores. Error técnico → Reintentar conserva la conversación.
5. Reiniciar → confirmación → cancelar conserva el hilo; confirmar vuelve al inicio. Su confirmación reproduce una acción existente, no una funcionalidad nueva de SP-12.

## 7. Vistas, contenido y datos

**V1, chat ES/EN:** `view=chat-es` y `chat-en` son variantes de inspección de la misma ruta, no dos páginas. Las tarjetas siguen el orden del motor. Nombre 16px, conteo tabular 26px y acción aparecen junto a la vista en escritorio. Móvil da todo el ancho al nombre antes del grupo vista/conteo/acción. Se muestran dos pares completos por defecto; `tres` agrega el tercero.

**Frontera Taller:** `state=abierto` conserva marca, cabecera, navegación y vocabulario Escena/Añadir/Biblioteca/Deshacer/Rehacer del producto y estado Proyecto nuevo/Sin guardar. El botón «Volver al chat» es navegación local simulada. No hay nuevo flujo de guardado, diálogo de nombre ni controles de edición ficticios.

Fixtures neutrales, rotulados Mockup/Datos de ejemplo, tomados de `ESCENAS_PREDEFINIDAS`:

| Id de escena fuente | Nombre ES existente | `productosDe(itemDeEscena(...)).totalGlobos` |
|---|---|---:|
| arco_organico_columnas_guirnalda | Arco orgánico con dos columnas y guirnalda | 530 |
| pared_fondo_columnas | Pared de globos al fondo y dos columnas | 346 |
| techo_racimos | Techo con tiras y flores colgando | 188 |

Los conteos se ejecutaron en el motor, no se estimaron en el dibujo. La id final y el nombre localizado de producción los devuelve la galería de SP-7. Los nombres EN del mockup son traducciones ilustrativas de estos nombres, no nuevas decoraciones ni un catálogo aprobado. Las vistas SVG son **esquemas rotulados**, no capturas del Taller ni imágenes reales de galería: los datos/activos de la galería futura no están disponibles en este brief. Producción debe usar su imagen canónica, sin recolorearla al cambiar el tema. El SVG simplifica geometría y no representa el número real de globos. No se añaden nombres de personas, fechas, lemas o copy promocional.

## 8. Estados e interacción/movimiento

| `state` | Presentación y recuperación |
|---|---|
| normal | Dos recomendaciones completas y respuesta/compositor; apertura por permiso. |
| tres | Tres recomendaciones completas, mismo orden y composición. |
| inicio | Saludo existente y celebración; ningún resultado adelantado. |
| definiendo | Primer mensaje y petición de tamaño/colores; sin decoración inventada. |
| cargando | Dos esqueletos de tarjeta, estado anunciado; ninguna cifra ni nombre ficticios en la carga. |
| vacio | Sin coincidencias; explicación y Escribir respuesta lleva al compositor. |
| error | Error de carga con Reintentar; se conserva hilo/borrador. También representa indisponibilidad de red sin reclamar éxito. |
| parcial | Dos tarjetas válidas conservadas y aviso de que no se cargaron todas; reintento ilustrativo. Política pendiente de Q2. |
| sin-boton | Dos tarjetas sin botón ni explicación de plan. No es pantalla de acceso denegado al chat. |
| abriendo | Aviso de apertura, tarjetas legibles, botones desactivados para evitar repetición. |
| apertura-error | Aviso de error de apertura y reintento, sin afirmar que ya existe un proyecto nuevo. |
| abierto | Contexto del Taller para la decoración elegida, proyecto nuevo sin guardar. |

`scene=reset` permite inspeccionar el AlertDialog en ambos idiomas/temas; `scene=''` lo cierra. Hover, focus, press y disabled se obtienen con controles reales, no con selectores de estado de negocio. Autenticación/sesión caducada pertenecen al guard compartido, no a una nueva vista de SP-12. Stale-data se evita mostrando solo datos válidos del mismo resultado: no mezclar el conteo de otra revisión. Una ficha sin nombre/conteo verificado no recibe valores de modelo ni cero provisional.

Movimiento distintivo: el tablero registra verticalmente, después cada recomendación entra lateralmente con 65ms de separación. El nombre y el número permanecen legibles durante la entrada; no se animan cifras ni se simulan cálculos. Las anclas son rápidas y el control responde en 140ms. No hay flotación decorativa continua. Solo la carga repite su respiración: IntersectionObserver la pausa fuera de vista y visibilitychange pausa la pestaña oculta. Reduced-motion, Quieto y `?still=1` conservan contenido, foco y acciones con todas las animaciones/transiciones anuladas.

## 9. Reflow y breakpoints

- **1100px o más:** 40px de margen, shell máximo 1520px; mesa `.82fr / 1.35fr`, 24px entre columnas, vista de tarjeta de 170px.
- **760–1099px:** margen 24px, dos columnas `.85fr / 1.1fr`; vista 130px. Controles/cabecera se ajustan con wrap; inspector del Taller se oculta.
- **360–759px:** margen 20px; conversación → resultados → compositor. Título de tarjeta ocupa ancho completo y vista 110px queda junto a conteo/acción. Navegación y cabecera envuelven; sin carrusel ni scroll horizontal.
- **320–359px:** tarjeta apilada con vista, conteo y apertura en una columna. Mantiene contenido y controles completos; se comprobó EN a 320px además del audit 390px.

El documento usa scroll vertical normal, sin fijar alturas del hilo ni el compositor. Ambos temas conservan las mismas posiciones y jerarquía. Zoom/reflow sigue las reglas de ancho disponible.

## 10. Accesibilidad

Objetivo WCAG 2.2 AA para el delta; las mediciones del mockup no certifican conformidad de la aplicación. Cada tarjeta tiene article y heading asociado; la vista tiene nombre accesible, y el conteo conserva su unidad. El botón se llama «Abrir en el Taller: <nombre>» para diferenciar tarjetas. La ausencia del botón elimina también la parada de teclado.

Textarea tiene label; Enter/Mayús+Enter y botón son alternativas. Esqueletos se ocultan al árbol accesible, pendiente usa status/aria-busy y fallos alert. El AlertDialog tiene título/descripción, fondo inerte, contención de foco y devolución al control de reinicio. Se usa foco sólido de 3px con offset, targets mínimos 44px, bordes de control texto-tenue y contraste medido. No se atribuyen a producción las pruebas de un archivo estático. Lectores de pantalla y guardado/navegación reales requieren revisión de implementación.

## 11. Criterios visuales y auditoría

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | Todos | Todos | Cabecera Pictures/Sempertex, fuentes y tokens son los del shell hermano; inspectores Mockup están fuera del producto. |
| A-02 | ≥1100px | normal/tres | Conversación/compositor quedan a la izquierda; recomendaciones en filas a la derecha. |
| A-03 | Todos | normal/tres | Cada tarjeta presenta vista rotulada de ejemplo, nombre existente, conteo del mismo fixture y unidad globos/balloons. |
| A-04 | Todos | sin-boton | Se ven las mismas dos decoraciones y conteos; no hay botón de apertura, explicación de plan ni CTA de compra. |
| A-05 | Todos | normal | Cada apertura lleva su propia id en data-destination y conserva la selección al mostrar el Taller sin guardar. |
| A-06 | Todos | cargando | Se ven esqueletos, nunca conteos o nombres inventados como sustitutos de carga. |
| A-07 | Todos | vacio/error/parcial | Ausencia/error no fabrica coincidencias; recuperación visible y el hilo se conserva. |
| A-08 | 360–759px | normal/tres | Nombre a todo el ancho; debajo vista a la izquierda y conteo/acción a la derecha, sin recorte. |
| A-09 | 320–359px | normal EN | Tarjeta apilada sin scroll horizontal; controles y nombres completos. |
| A-10 | Todos | abriendo/apertura-error | Pendiente impide apertura duplicada; error mantiene contexto y Reintentar. |
| A-11 | Todos | scene=reset | Cancelar recibe foco y al cerrar vuelve al reinicio; confirmar vuelve al inicio. |
| A-12 | Todos | normal EN/ES | Las tarjetas usan la lengua activa; no mezclan nombres traducidos por el modelo en producción. |
| A-13 | 1280/390px, claro/oscuro | Todos | Contraste texto 4.5:1, controles/foco 3:1; contenido sin overflow horizontal. |
| A-14 | Todos | reduced/Quieto/still | Movimiento suprimido y todas las tarjetas, contenidos y acciones siguen presentes. |

**Auditoría:** se usa el builder real offline por ruta absoluta, sin instalar paquetes ni obtener activos. Primera pasada: 96 renders, FAIL por dos avisos geométricos de alineación móvil. Se ajustó la jerarquía móvil poniendo el título a todo lo ancho, y se añadió la confirmación de reinicio heredada. La pasada posterior revisó 104 renders, 3596 mediciones de texto y 497 pasos de foco sin hallazgos. La prueba funcional local pasó apertura de la segunda tarjeta, tarjetas sin botón, flujo de dos mensajes con Enter, cancelación/foco del reinicio, EN y reflow adicional de 320px; sin errores JS. El primer intento de esa prueba consultó el foco antes de asentarse: se sustituyó por una espera observable `to_be_focused`; no se ocultó un defecto ni se cambió un criterio.

`contrast: 158 pairs checked in light and dark, all pass`

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

La pasada final, después de los atributos de evidencia del destino y la pausa offscreen, volvió a pasar: **104 renders de 104 combinaciones previstas, 3596 mediciones de texto y 500 pasos de foco**. Se inspeccionaron capturas finales en memoria a 1280 y 390px en ambos temas (ES claro/EN oscuro en escritorio; EN claro/ES oscuro en móvil), sin archivos de screenshot. También pasó la comprobación de selectores JSON existentes, animación `card-register` real, supresión en Quieto y cero solicitudes HTTP(S). El artefacto no prueba ranking real, traducciones de galería, permisos del servidor ni persistencia.

## 12. Preguntas y supuestos abiertos

**Confirmado por brief:** dos o tres recomendaciones; vistas para todas las cuentas; nombre en idioma de sesión; conteo de galería/motor; abrir por `decoraciones.explorar`; destino como proyecto nuevo; sin mención de plan cuando falta permiso. No se reabren esas decisiones.

**Supuestos de esta exploración:** los presets existentes son fixtures visuales neutrales, no una promesa de la galería final. Las imágenes reales serán proporcionadas por SP-7; el esquema rotulado no las sustituye en producción. Los errores usan recuperación mínima local. Las decisiones pendientes son del dueño/Planner y no se delegan implícitamente a implementación.

Q: ¿Qué debe mostrarse si la galería no tiene un nombre en el idioma de sesión: ocultar esa recomendación o conservar el nombre original con un aviso? El mockup usa traducciones ilustrativas, sin establecer la política de fallback.
Q: ¿Si solo queda una coincidencia válida, o una tercera falla al cargar, se conserva lo válido con aviso o se exige siempre un resultado completo de dos o tres? El estado parcial ilustra dos válidas y reintento; no autoriza recomendaciones débiles ni conteos no verificados.
Q: ¿Qué recuperación se desea cuando falla únicamente la imagen de galería pero nombre y conteo siguen siendo válidos? Esta exploración no fija un placeholder de producción; sus SVG son explícitamente ejemplos.

CONCERNS: imágenes y nombres EN de la galería final no disponibles como entrada; se distinguen esquemas/traducciones ilustrativas de las fuentes canónicas. Selección de dirección y aprobación pendientes. Shell/contexto ajeno al delta es una representación estática, no una nueva implementación de navegación o del Taller.
