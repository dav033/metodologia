# Escena junto al chat — SP-12, direction B, revision r2

Estado: **exploración de borrador; sin aprobación**. Candidata para `chat-a-3d@v1`, revisión r2 (motivo: cambió el plan). Responsable: David. Alcance: SP-12 / R13, exactamente `chat-a-3d@v1.r2.behavior.md`. Esta dirección escribe solo sus archivos específicos de la revisión; no crea ni modifica el contrato canónico, SPEC, PLAN, diseños hermanos ni código de producción. La elección de la persona responsable y la aprobación del plan están pendientes.

## Cambios respecto a r1

El brief de r2 agrega el alcance de prueba de T12.3 (Entusiasta, Master Designer y staff, tarjetas en inglés, apertura de un proyecto nuevo sin guardar, guardado, sin coincidencias y permiso denegado), y la lista de diseños hermanos ahora incluye `herramientas-chat@v1`, finalizado, cuya barra lateral de herramientas envuelve `/asistente` (su V5). Por lo tanto, r2 conserva el enfoque espacial de r1, pero:

- reemplaza la fila de rutas horizontal de r1 con el **shell de herramientas-chat@v1**: cabecera + barra lateral de herramientas de 248px con listas de herramientas por rol (Chat actual) y el conmutador móvil «Herramientas · Chat»;
- agrega vistas por rol (Master Designer, staff, Entusiasta), la **llegada al Taller con guardado** (proyectos@v1 D1 «Guardar proyecto», error de nombre vacío, Guardando…, «Guardado en tu cuenta»), la **protección contra trabajo sin guardar** reutilizada de herramientas-chat D1 y el **rechazo del enlace directo** reutilizado de herramientas-chat V7;
- usa el texto real del producto para reiniciar («¿Empezar de nuevo?» / «Se borra esta conversación y vuelves al inicio.», t12 `ConfirmarEmpezarDeNuevo.tsx`) en un AlertDialog;
- reemplaza la afirmación de un diseño compartido por una transferencia de escena FLIP funcional (el entorno de ejecución del kit vuelve a montar el producto por vista/estado, por lo que `layoutId` de Motion no puede animar entre vistas).

## Enfoque y superficie existente

Modifica el chat guiado normal existente en `/asistente` (t12 `src/app/asistente/page.tsx`, `src/components/guiado/VistaGuiada.tsx`; saludo `SALUDO`, «Ideas de decoración» de `CarruselDecoraciones.tsx`, compositor `Compositor.tsx`) dentro del shell de herramientas-chat@v1. Solo se reorganiza el área modificada: la conversación permanece acoplada a la izquierda de la columna principal y el área de recomendaciones se convierte en un escenario (una decoración de galería ampliada) con un índice de las dos o tres recomendaciones. Cada tarjeta muestra una vista previa, el nombre en el idioma de la sesión y el conteo de globos del motor; «Abrir en el Taller» aparece solo para cuentas con `decoraciones.explorar` y abre `/3d?decoracion=<id>` como un proyecto nuevo sin guardar. No se agrega ninguna página, navegador de catálogo, filtro, precio, comparación de planes ni oferta adicional.

Se conservan: la cabecera de Pictures/Sempertex, el selector Idioma, el desplegable de cuenta (con su opción Planes heredada), la barra lateral de herramientas y su movimiento, las fuentes Geist, los tokens, las superficies redondeadas y los controles tipo píldora. El Taller es solo contexto (riel de herramientas, lienzo y panel existentes); su editor y las reglas de guardado corresponden a proyectos@v1.

## Miniaturas

Ambas se escribieron antes del TSX completo y se renderizaron a 1280px:

- **Elegida: candidata 1** — `chat-a-3d@v1.r2.dir-b.html.candidate-1.html`: barra lateral | conversación de 300px | escenario ampliado con un índice de 3 tarjetas debajo. Las recomendaciones se perciben como tarjetas equivalentes (criterio del producto), y la conversación, la escena ampliada y las tres tarjetas caben en la primera ventana gráfica de 1280px.
- Candidata 2 — `chat-a-3d@v1.r2.dir-b.html.candidate-2.html`: conversación amplia | «inspector de escena» de 360px con vista previa ampliada y filas compactas. Las filas se perciben como una lista, no como tarjetas, y la acción para abrir solo está disponible en el elemento seleccionado; se ajusta menos al criterio de tarjetas.

## Por qué encaja con Pictures

Es la misma aplicación que herramientas-chat@v1: cabecera, barra lateral, encabezado H1 más «Datos de ejemplo», superficies y respuesta de botones idénticos. El escenario reutiliza el lenguaje visual de las vistas previas de la galería de herramientas-chat V4 (suelo de taller-visor, esquema ilustrativo, apertura como proyecto nuevo), y la llegada al Taller refleja V6/proyectos@v1 («Escena nueva», «Sin guardar todavía», «Guardar proyecto»). Solo son nuevos la jerarquía del área de recomendaciones y sus transiciones.

## Ocho ejes

| Eje | Expresión renderizada |
|---|---|
| Concepto | Conversación acoplada junto a un escenario espacial; al abrir, la vista previa elegida se amplía hasta ocupar el lienzo del Taller. |
| Diseño | Barra lateral de 248px + área principal. Área principal >820px: conversación fija de 300px \| escenario + índice de tarjetas de 3 columnas (2 con dos resultados). 600–820px: conversación de 260px \| escenario + filas de tarjetas en una columna. <600px: elementos apilados. Consulta de contenedor en la columna principal. |
| Navegación | Enlaces heredados de la barra lateral (`aria-current`), conmutador móvil. Botones de vista previa en la página con `aria-pressed`, texto «Vista actual» y un marcador de resorte que se desliza entre tarjetas; el foco permanece en la tarjeta activa. «Abrir en el Taller» en el escenario y en cada tarjeta autorizada; «Volver al chat» desde el Taller. |
| Tipografía | Geist Sans 24/20/17/14–15/12–13px; conteos tabulares; Geist Mono solo en el logotipo tipográfico. |
| Densidad | Una escena ampliada, tarjetas compactas con nombres que ocupan todas las líneas necesarias; en anchos reducidos, las tarjetas se convierten en filas en lugar de comprimirse. |
| Componentes | Sidebar, Button, Input, Skeleton, Dialog y AlertDialog reales; `select`/`details` nativos; botones personalizados de vista previa de tarjetas y vistas previas SVG etiquetadas. |
| Color | Solo tokens del proyecto; acento en la acción principal de apertura/guardado, el foco y los globos ilustrativos; error para los fallos; exito para el estado guardado. |
| Movimiento | Acoplamiento en direcciones opuestas (−18px / +28px), secuencia de colocación de tarjetas (+18px, .6deg, intervalo de 70ms), recolocación de escena al seleccionar (+24px, .975), marcador de selección con resorte, transferencia de escena FLIP al Taller (680/420/200ms). Con movimiento reducido/Quieto/sin movimiento: sin desplazamiento. |

Evidencia de selectores: `chat-a-3d@v1.r2.dir-b.json`; todos los selectores coincidieron con un elemento renderizado en la prueba que se describe a continuación.

## Detalles de interacción y movimiento

Curva de aceleración `cubic-bezier(.16,1,.3,1)` para los movimientos espaciales; la barra lateral y los botones conservan los cortes precisos del hermano con `cubic-bezier(.23,1,.32,1)` (filas −8px, botones ±1px, 150ms). Perfiles: asentamiento expresivo de 600ms / intervalo de 70ms, natural de 360/35ms, sutil de 180/12ms. Al seleccionar una tarjeta, el foco permanece en ella, se actualiza el escenario (fotograma clave de recolocación) y se anuncia el nombre · conteo de forma discreta; el marcador de selección se mueve con resorte (rigidez 260 / amortiguación 26 en expresivo; 380/34 en natural; 520/34 en sutil; duración 0 con movimiento reducido). Al abrir, se guarda el rectángulo de la miniatura pulsada (o de la vista previa del escenario) y, al montar el Taller, se anima el lienzo desde ese rectángulo hasta el suyo (traslación + escala, solo transformación), de modo que la decoración se desplaza visiblemente del chat al taller. Con `prefers-reduced-motion`, «Quieto» o `?still=1`, se omiten la transferencia y todos los fotogramas clave, y el contenido aparece de inmediato en su estado final; las pestañas ocultas pausan la animación CSS. No hay animaciones infinitas.

Flujos mostrados: intercambio de dos o tres mensajes (Cumpleaños → «¿Qué tamaño y qué colores?» → respuesta de ejemplo) → «Ideas de decoración» con 2–3 tarjetas → selección → apertura (Master Designer/staff) → Taller «Escena nueva» / «Sin guardar todavía» → D1 «Guardar proyecto» (si el nombre está vacío, permanece abierto con «Escribe un nombre para el proyecto.»; Guardando…) → «Guardado en tu cuenta». Si hay trabajo sin guardar en el Taller, al abrir primero aparece «Tienes cambios sin guardar» (Cancelar / Descartar escena y continuar / Guardar y continuar; Escape devuelve el foco a la tarjeta que inició la acción). Entusiasta ve las mismas tarjetas sin la acción para abrir y sin texto de planes en el área de recomendaciones; su barra lateral muestra solo Herramientas, Chat, Contador de globos. Un enlace directo a `/3d?decoracion=…` sin permiso muestra «No tienes acceso a esta herramienta» / «Tu cuenta no tiene permiso para abrirla.» / «Volver a herramientas», sin datos de decoración.

## Vistas, estados y diálogos (selectores nativos)

Vista: Chat · Master Designer; Chat · Personal interno; Chat · Entusiasta; Taller · proyecto nuevo desde el chat; Enlace directo sin permiso. Estado: listo (3), dos resultados, inicial, conversación, cargando (esqueleto, «Buscando decoraciones…», detener), vacío (sin coincidencias: «No hay coincidencias» + explicación, sin tarjetas), error, sin conexión, error de vista previa (se conservan el nombre/conteo), error de conteo («Conteo no disponible», nunca cero, apertura deshabilitada), apertura («Abriendo…»), no disponible, sin guardar (el Taller tiene cambios sin guardar; al abrir se muestra la protección), guardado (Taller). Diálogo: reinicio, protección contra cambios sin guardar, primer guardado. Tema claro/oscuro; movimiento expresivo/natural/sutil/Quieto; Idioma del producto ES/EN.

## Datos e idioma

Los nombres y conteos provienen de t12 `BIBLIOTECA_FABRICA` y `productosDe(item).totalGlobos` (solo lectura, como en r1): «Arco orgánico con dos columnas y guirnalda» 530, «Pared de globos al fondo y dos columnas» 346, «Techo con tiras y flores colgando» 188. Una sola fixture alimenta el escenario, las tarjetas, el anuncio y el panel del Taller. Las vistas previas SVG son ilustraciones esquemáticas etiquetadas, no renderizados de la galería. Los nombres en inglés son sustitutos provisionales para SP-9 `textos-ingles`; en producción se usan datos localizados de la galería, nunca nombres generados por el chat.

## Sistema de diseño fijo

Tokens copiados exactamente de t12 `src/app/globals.css` (claro/oscuro), asignados una vez a los roles de shadcn como en herramientas-chat@v1 (background/card → fondo/superficie, primary → acento/sobre-acento, input → texto-tenue, sidebar-* → superficie/superficie-2/borde). Geist Sans/Mono incorporadas desde t12 `.next/static/media`. Radios de 32/24/18/999px. Sin nueva paleta, fuente ni marca.

## Verificación (HTML final)

| Comprobación | Resultado real |
|---|---|
| Compilación sin conexión | `components mockup build` finalizó con código 0; 748 KB, 2.194 archivos fuente, sin conexión. |
| Contraste | `contrast: 158 pairs checked in light and dark, all pass` (código 0). |
| Auditoría renderizada | Código 0: 340 renderizados / 340 planificados, 9.348 mediciones de texto, 716 paradas de foco. |
| Prueba de interacción | 43/43 PASS: la selección actualiza el escenario y conserva el foco; la apertura lleva la identidad (/3d?decoracion=escena%3Apared_fondo_columnas) a «Escena nueva / Sin guardar todavía»; error de nombre vacío; guardar → «Guardado en tu cuenta»; Entusiasta: 3 tarjetas, sin «Abrir», sin «plan», barra lateral de 3 elementos; rechazo por falta de permiso sin tarjetas; se muestra la protección, Escape devuelve el foco, descartar abre la decoración correcta; cancelar/confirmar el reinicio; dos resultados; error de conteo deshabilitado sin mostrar cero; sin coincidencias ni tarjetas; nombres en inglés con conteos sin cambios; todos los selectores JSON presentes; cero errores de página y cero solicitudes HTTP(S); el conmutador móvil se abre/Escape; sin desbordamiento horizontal a 390px. |
| Movimiento | 12 animaciones en ejecución a los 120ms en modo expresivo; 0 con `?still=1`; 0 con movimiento reducido del sistema operativo; la transferencia FLIP se anima al abrir (1 animación en `.studio-canvas`) y no se ejecuta con `?still=1`. |
| Inspección visual | Capturas inspeccionadas: Master claro 1280/1024/768/390, Entusiasta oscuro 1280, Taller oscuro 1280, error de conteo oscuro 390. La primera compilación no mostró globos de acento (`nth-child` dentro de `<g>`), tenía un encabezado de conversación estrecho y un contorno de foco en el encabezado después de enfocar por código; los tres problemas se corrigieron antes de la auditoría final. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

La primera ejecución de la prueba falló porque el entorno vuelve a montar el producto por vista/estado, lo que descartó la respuesta de llegada e imposibilitó la transferencia con `layoutId` de Motion; ahora la respuesta y el origen de la transferencia se conservan en la memoria del módulo, y la transferencia usa FLIP. Dos fallos posteriores de la prueba se debieron a que sus propios selectores coincidían con las etiquetas de opciones del Diálogo. Las capturas y pruebas permanecieron en `/tmp`. Estas comprobaciones validan únicamente este artefacto de planificación, no el orden de resultados, la fidelidad de la galería, los permisos, el enrutamiento ni el guardado.

## Preguntas

- Q1 — Si falla el conteo del motor para una recomendación, ¿se omite la tarjeta hasta que se recupere o se muestra como «Conteo no disponible» con la apertura deshabilitada (este borrador)?
- Q2 — ¿Quién proporciona los nombres de la galería en inglés (SP-9) y qué se muestra cuando falta un nombre localizado?
- Q3 — ¿Qué recomendación se amplía primero: la que ocupa el primer puesto según el recomendador (este borrador) o ninguna hasta que la persona elija?
- Q4 — ¿Deben incluir «Abrir en el Taller» tanto el escenario como cada tarjeta (este borrador) o solo el escenario ampliado?
- Q5 — Para staff, ¿la apertura desde el chat funciona exactamente igual que para Master Designer (este borrador), sin contexto adicional de propietario/cuenta?

Supuestos: la selección es solo visual y no cambia el orden de resultados; la apertura nunca sobrescribe el proyecto abierto; el comportamiento de guardado, el guardado automático y los conflictos corresponden a proyectos@v1; la protección y el rechazo corresponden a herramientas-chat@v1.
