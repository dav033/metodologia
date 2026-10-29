---
name: Registro operativo
contract: gasto-ia
version: 1
revision: r1
direction: a
status: draft
subplan: SP-6
requirements: [R4, R5]
source_behavior: gasto-ia@v1.r1.behavior.md
author: Designer
date: 2026-10-29
---

# Registro operativo — direction a

Esta es una **exploración** completada, no el contrato canónico de doce secciones ni una aprobación. El propietario aún está analizando el plan. Solo se escribieron los archivos específicos de esta revisión de la dirección; no se modificaron ningún contrato compartido, repositorio de producción, plan, directorio de vista previa ni otra dirección. Un finalizador posterior deberá redactar el borrador canónico después de que el propietario elija.

## Enfoque y miniatura elegida

La pregunta principal es: **¿a qué usuario, sesión o elemento de trabajo corresponde este gasto estimado, y qué se sabe realmente?** El área modificada es el espacio de administración del personal. Un registro operativo de ancho completo presenta filtros, totales de la consulta y filas agrupadas en una sola hoja de trabajo. Al abrir una sesión o un elemento de trabajo, se mantienen la cabecera, la navegación, los filtros y el vocabulario de costos. No se introduce un visor de prompts, configuración de proveedores, acción de facturación, límite de gasto, exportación, filtro de fechas ni una nueva estructura de aplicación.

**Miniatura elegida: `gasto-ia@v1.r1.dir-a.html.candidate-1.html`.** La candidata 1 permite comparar ambas sesiones, ofrece espacio para las cinco dimensiones de agrupación y mantiene visible el total de costos estimados mientras se revisan los registros. La candidata 2 (`…candidate-2.html`) explora un selector de sesiones de 260px junto a un panel de inspección de detalles; destina espacio de trabajo a una segunda región de navegación y dificulta comparar sesiones entre sí. Ambas miniaturas se conservan como composiciones visuales con la estructura heredada, las dos opciones de tema y la fuente Geist local real incrustada. Son bocetos, no maquetas completas auditadas para todos los estados.

El TSX de origen monta componentes instalados reales mediante `mountMockup/useMockup` de `@kit/mockup`; el generador sin conexión integra su CSS/JS y las fuentes locales. Los selectores externos nativos conservan `view`, `state`, `theme`, `motion`, las etiquetas Vista, Estado, Tema y Movimiento, y la etiqueta visible Mockup. No hay diálogos, así que no corresponde un selector de escenas. El selector de idioma ES/EN del producto está separado de los controles de inspección.

## Producto existente y sistema fijo

Evidencia de solo lectura: `src/app/globals.css` de ambos repositorios; `src/app/layout.tsx`, `src/components/admin/AdminTabs.tsx`, `src/app/admin/page.tsx`, `src/components/ui/shell/CabeceraApp.tsx` de t12, y los wrappers existentes para modelos y valores predeterminados. Administración ya tiene un título, navegación contextual y contenido operativo con pestañas. No existe un panel de gasto en IA vinculado a la cuenta que pueda usarse como referencia. Esta dirección añade contenido dentro del vocabulario de administración y de la estructura compartida más reciente de sus proyectos hermanos; no afirma que ya exista una nueva ruta de producción.

Fuentes de proyectos hermanos consultadas: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html`, `proyectos@v1.md/.html`, además del TSX del proyecto elegido para verificar la correspondencia exacta de temas y fuentes. La estructura conserva el símbolo de anillo y punto de Pictures, el logotipo de Sempertex, el control de idioma etiquetado, el menú de cuenta con nombre, el encabezado de 24px, la navegación horizontal neutra entre rutas, la hoja redondeada y el pie alineado. Los destinos de administración de cuentas aparecen solo en los datos de ejemplo del administrador; los datos de ejemplo del empleado conservan Gasto IA / Mi cuenta. La implementación real debe determinar la visibilidad según los permisos efectivos, no codificar un nombre de rol.

| Fuente de Pictures | Rol/uso en Kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--superficie-suave` | aviso complementario | #faf8fd / #1c1e26 |
| `--superficie-2` | insignia atenuada, secundaria y neutra | #efe9f8 / #242733 |
| `--texto` | colores de primer plano y regla de agrupación seleccionada | #1c1425 / #f4f5f7 |
| `--texto-suave` | color de primer plano atenuado | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde de entrada/control, alias accesible heredado del proyecto hermano | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primario, anillo / primer plano primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | estado hover del primario | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | contorno decorativo / reglas de registros | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--aviso`, `--aviso-suave` | uso parcial | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | error facturable del proveedor / error de consulta | #b23a45, #ffeaec / #ff979f, #43252a |
| `--exito`, `--exito-suave` | roles de éxito existentes con correspondencia | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |

Geist Sans y Geist Mono están incrustadas desde los archivos WOFF2 locales de `.next/static/media/` existentes de t12, cuyos nombres especifica el TSX; no se usa ninguna descarga ni fuente nueva. Los radios de 32px del panel, 24px del recuadro complementario, 18px del campo y 999px de la píldora conservan los roles de los proyectos hermanos. El relleno de la hoja es de 28px en escritorio y 20px en teléfono; los números se alinean a la derecha con cifras tabulares. Los valores de los tokens del proyecto prevalecen sobre los valores predeterminados de Kit. No se necesitó una alternativa HTML de Kit, instalar paquetes ni usar recursos de red.

Vocabulario de componentes reales: `shadcn:button outline ready|hover|focus|disabled` de `@/components/ui/button`; `shadcn:skeleton record loading` de `@/components/ui/skeleton`; selectores nativos con etiqueta para usuario/tipo/idioma e inspección; registros de tabla semántica; `details/summary` nativos para los detalles de cuenta/trabajo/conversación; `motion.span` de `motion/react` para el marcador de agrupación; `useMotionProfile` de `@kit/motion`; iconos de Lucide. El registro, la franja de totales, los avisos y la composición adaptable de etiquetas y valores son composiciones personalizadas, no componentes de biblioteca inventados.

## Tabla de ocho ejes y detalles de interacción

| Eje | Expresión renderizada |
|---|---|
| Concepto | Un registro de trabajo del gasto estimado en IA, con los metadatos conocidos y desconocidos separados explícitamente. |
| Diseño | Una hoja de ancho completo: fila de filtros de usuario/tipo → franja de totales → cinco controles de agrupación → registros con líneas divisorias. Los detalles reemplazan solo el contenido de trabajo. No hay cuadrícula de tarjetas KPI ni panel lateral de inspección persistente. |
| Navegación | Regla de rutas de administración existente, además de Por sesión / Por usuario / Por trabajo / Por tipo / Por herramienta. Haz clic en una sesión o elemento de trabajo para ver su detalle; Volver al resumen restaura el resumen con sus filtros. El primer detalle está desplegado inicialmente. |
| Tipografía | Geist existente; H1 24px, H2 18–20px, totales 28–32px, registros 14px, metadatos 12–13px. Fuente mono solo para identificadores técnicos; no se crea una nueva identidad tipográfica. |
| Densidad | Fila de filtros con proporción 2:1:auto en escritorio, datos compactos con líneas divisorias dentro de la hoja compartida, metadatos junto a la identidad y divulgación progresiva del detalle por llamada. En móviles, los registros se reorganizan en pares con etiquetas; los filtros se apilan. |
| Componentes | Button/Skeleton reales de shadcn/Base UI, selectores y detalles nativos, tabla semántica, etiquetas contextuales de errores facturables y una línea de subrayado móvil para la agrupación. |
| Color | Temas exactos del proyecto; el acento se usa solo para el símbolo heredado, los enlaces y el foco; navegación activa neutra; tokens de advertencia/error solo para sus estados de datos semánticos. No hay una paleta nueva. |
| Movimiento | Registro rápido con la curva ease-out de producción `cubic-bezier(.23,1,.32,1)`: hoja + totales durante 320ms; las filas aparecen desde 10px a la derecha con intervalos de 28ms; marcador de agrupación durante 180ms; hover/press durante 160ms. Natural: 220/130ms con intervalos de 18ms; sutil: 140/100ms con intervalos de 8ms. Reducido/estático elimina el movimiento y conserva todo el contenido. |

La interacción distintiva es reagrupar una consulta sin cambios: el total permanece fijo mientras un único subrayado se desplaza a la agrupación elegida y las filas aparecen rápidamente. Sesión → proyecto → conversación muestra la atribución sin exponer la entrada ni la salida de IA. Hover eleva los botones de acción 2px; press los asienta 1px hacia abajo; las flechas de detalle se desplazan 3px. Los detalles aparecen desde 6px arriba. Todo movimiento es finito; las pestañas ocultas pausan las animaciones CSS. Los perfiles controlan explícitamente las duraciones y el estado reducido del marcador de Motion. No hay bucles ambientales, parpadeos ni comentarios que dependan solo de la animación.

## Vistas, flujos y semántica de datos

| Vista nativa | Propósito y estructura |
|---|---|
| `summary` — Resumen | Filtrar por la identidad de la cuenta autenticada y el tipo de llamada. Consultar los USD estimados, los tokens conocidos y la cantidad de llamadas; luego cambiar entre totales por sesión/usuario/trabajo/tipo/herramienta sin modificar la consulta. Las filas de sesión muestran el usuario; las de trabajo muestran el proyecto o el identificador de conversación independiente. |
| `session` — Detalle de sesión | Conservar la sesión seleccionada y los filtros. Mostrar usuario, totales de sesión y detalles desplegables del trabajo. Cada detalle de trabajo contiene herramienta, tipo de texto/imagen, proveedor/modelo, tokens de entrada/salida, USD estimados, identificadores de llamada/sesión/conversación y contexto de fecha. Ver conversaciones abre ese elemento de trabajo específico. |
| `work` — Detalle de trabajo | Conservar el contexto del proyecto o de la conversación independiente y los filtros. Los detalles de proyectos separan las conversaciones; el trabajo independiente sigue siendo la conversación, sin inventar un proyecto. Cada detalle muestra solo metadatos de uso. |

Flujo: un empleado/administrador con permiso entra a Gasto IA → elige Usuario y Tipo de llamada → consulta los totales → elige una agrupación → abre un registro de sesión/trabajo → abre el detalle de la conversación → vuelve al resumen. En los datos de ejemplo, los cambios de filtro se aplican de inmediato y conservan el foco de texto/control. Los filtros elegidos, el idioma y el registro seleccionado sobreviven a los cambios de vista en memoria. No se escribe en el almacenamiento del navegador ni se realizan llamadas remotas. La agrupación inicial es Por sesión; el primer detalle de trabajo/conversación está desplegado y se puede cerrar o volver a abrir con el teclado. La implementación completa debe filtrar y agregar en toda la consulta del servidor, no solo en la página cargada. Los totales de la consulta son distintos de la cantidad de grupos visibles. Los datos de ejemplo de error de cursor conservan el primer grupo cargado, muestran un error al cargar la página siguiente y la opción Reintentar; después del reintento, restauran todos los grupos de ejemplo. Los datos de ejemplo normales no tienen cursor siguiente ni una acción activa de Cargar más.

Los datos de ejemplo son neutros y están marcados explícitamente como Datos de ejemplo / Mock data. Cinco llamadas normales suman **USD 0.0492**, **4,200 tokens conocidos**, **5 llamadas**: ses-001, USD 0.0430 / 2,800 tokens conocidos; ses-002, USD 0.0062 / 1,400 tokens conocidos. El modelo predeterminado para texto usa el `gemini-3.6-flash` inspeccionado; los valores de modelo no reportados se muestran como No informado. La fecha de la tarea proporcionada, 2026-10-29, es la fecha de los datos de ejemplo y está etiquetada como UTC; esto no afirma que exista un intervalo de fechas activo ni actividad real de clientes. No aparecen nombres de clientes, correos electrónicos, cuerpos de prompts, contenido generado, secretos, saldo ni información de facturas.

En `partial`, un error facturable conocido añade USD 0.0030 y 200 tokens de entrada conocidos, con la salida desconocida; el costo y los tokens de una llamada parcial de imagen son desconocidos. El total pasa a ser **USD 0.0522 estimados conocidos**, **4,400 tokens conocidos**, **7 llamadas**, con una explicación de que el total está incompleto. El uso conocido de errores se sigue incluyendo. Los valores desconocidos se muestran como No informado, nunca como cero; un grupo sin tokens conocidos muestra No informado. Las sumas usan los valores de los datos de ejemplo antes de aplicar el formato de visualización. Cuatro decimales y UTC son **propuestas de presentación pendientes de las preguntas siguientes**. Nada de esto implementa precios de proveedores ni la integridad del registro.

| Estado nativo | Comportamiento renderizado / recuperación |
|---|---|
| `normal` | Datos de ejemplo del administrador, resumen completo o detalle seleccionado; menú de cuenta del administrador y navegación de administración permitida. |
| `employee` | Mismo acceso y datos de gasto, con identidad del empleado; en estos datos de ejemplo no aparecen enlaces ajenos a la administración de cuentas/roles. |
| `loading` | Estado de carga con filas de esqueleto estáticas; filtros y acción de limpiar deshabilitados; no se inventan totales. |
| `empty` | No se ha registrado uso; se explica que las llamadas aparecerán después de registrar su uso; sin totales numéricos ni acciones irrelevantes. |
| `no-results` | No hay registros coincidentes; se explica cómo cambiar el usuario/tipo; Limpiar filtros vuelve a los datos de ejemplo normales. |
| `error` | Falló la consulta; se conservan los filtros y se ofrece Reintentar. Se ocultan los totales y los valores obsoletos del registro. |
| `partial` | Se incluyen errores facturables conocidos del proveedor, se etiquetan los campos desconocidos y se indica explícitamente que el agregado está incompleto y que algunas llamadas son parciales o tienen errores. |
| `offline` | Sin conexión, controles de consulta conservados y opción para reintentar; no se afirma que los valores almacenados en caché estén actualizados. |
| `denied` | Identidad de cuenta habitual y Sin acceso; sin navegación de rutas del personal, filtros, totales, grupos ni metadatos de llamadas; recuperación mediante Mi cuenta. |
| `expired` | Sin menú de cuenta ni metadatos del registro; explicación de que la sesión terminó y opción para iniciar sesión. |
| `next-page-error` | El resumen conserva su primer grupo cargado, los totales completos de la consulta y el estado de que hay más datos pendientes, con opción para reintentar. En las vistas de detalle, este estado de inspección usa su diseño normal porque la paginación con cursor corresponde al resumen. |

Los controles deshabilitados son visibles en los estados de carga y de filtros borrados predeterminados. La validación de formularios, la confirmación de acciones destructivas y los estados de guardado y edición no corresponden a esta vista de revisión de solo lectura. No hay campos modificables de cuenta, importe ni modelo. Los estados de autorización/sesión son solo datos visuales de ejemplo; el trabajo de permisos del servidor y de API de SP-6 sigue siendo necesario por separado.

## Objetivos de diseño adaptable y accesibilidad

Ancho mínimo admitido: 360px. A **1100px o más**, el espacio de trabajo tiene un ancho máximo de 1520px y márgenes exteriores de 40px; los filtros usan columnas 2:1:auto, el resumen usa una franja de totales de 1.5:1:1 y los registros se muestran en una tabla horizontal. Entre **640 y 1099px**, los márgenes exteriores pasan a 24px y los filtros se distribuyen en dos columnas, con el filtro de tipo debajo. Entre **360 y 639px**, los márgenes exteriores y del papel son de 20px, la cabecera y las herramientas de ruta se ajustan a varias líneas, los filtros se apilan, el USD estimado ocupa ambas columnas de métricas, los tokens y las llamadas conocidos comparten la siguiente fila, los controles de agrupación se ajustan a varias líneas y los registros se convierten en pares de valores etiquetados. Los ID de modelo largos se ajustan a varias líneas. Los avisos móviles se alinean directamente con el eje de contenido del papel, sin añadir un segundo margen interior. Se espera desplazamiento vertical; la página no tiene desplazamiento horizontal.

Objetivo WCAG 2.2 AA: controles etiquetados, encabezados/tablas/divulgaciones semánticos, foco de acento visible de 3px con desplazamiento de 4px, objetivos de interacción de 44px, contraste de texto ≥4.5:1 y contraste de controles esenciales/foco ≥3:1, agrupación operable con teclado mediante `aria-pressed`, texto/iconos de estado junto al color y estado de carga y totales anunciado de forma cortés. Los errores de consulta usan alertas. La navegación entre páginas enfoca H1; los filtros y la agrupación no desplazan el foco que inició la acción. La divulgación de cuenta admite Escape y devuelve el foco al resumen. La reducción de movimiento del sistema operativo, Quieto y `?still=1` conservan todos los datos/acciones y eliminan las animaciones finitas. El comportamiento completo con lectores de pantalla y la aplicación de permisos en producción requieren una aceptación independiente; una maqueta estática no los demuestra.

## Verificación, impacto y aspectos por resolver

Los artefactos incluidos en este alcance son las dos miniaturas candidatas, el TSX de entrada, el HTML generado, esta nota y el JSON de evidencias por eje. La compatibilidad del nuevo borrador está **indeterminada** hasta que se elija/apruebe de forma independiente una dirección y un contrato canónico. Solo SP-6 consume `ui.contract=gasto-ia`, versión 1: T6.1 lo fija, T6.4 implementa la superficie para el personal, T6.5 verifica la atribución/autorización del punto de entrada y T6.6 realiza la revisión visual. Esta exploración no cambia ningún contrato paralelo ni consumidor de producción.

Evidencia final real: kit instalado `installed=True built=True entries ok=96/96`; generación sin conexión, código de salida 0, 528 KB y 1,956 archivos fuente; contraste de tokens, código de salida 0, `contrast: 158 pairs checked in light and dark, all pass`. La auditoría inicial de 180 renderizados informó 42 problemas de alineación por el doble margen interior del aviso móvil. El aviso ahora comparte el eje de contenido del papel móvil; la siguiente auditoría de 180 renderizados pasó. La auditoría final completa, tras añadir el estado de inspección del empleado, terminó con código 0: **198 renderizados / 198 combinaciones previstas**, **6,370 mediciones de texto**, **470 paradas de foco**, a 1280/390/768px en ambos temas, sin muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

El script de interacción enfocado pasó 12 grupos: filtrado por cuenta/tipo, los cinco tipos de agrupación, selección exacta de sesión/trabajo, etiquetado de tokens desconocidos, totales incompletos, denegación, expiración, reintento de consulta, recuperación ante error de cursor, textos EN, redistribución a 360/390/768/1280 y Escape en la cuenta; cero errores de página o solicitudes HTTP(S) externas. Las pruebas adicionales finales, posteriores a la incorporación del empleado, pasaron: la navegación del empleado contiene solo Gasto IA / Mi cuenta, la divulgación del rol del empleado y Escape funcionan, todos los selectores de evidencia JSON existen en la vista declarada, seis animaciones expresivas están activas en el momento de observación y ninguna está activa con el movimiento reducido del sistema operativo o `?still=1`. Se inspeccionaron en memoria capturas de pantalla de ambas composiciones candidatas, el resumen claro a 1280, la sesión oscura a 1280, el resumen parcial oscuro a 390 y el detalle de trabajo claro a 390. No se escribieron archivos de captura. Estas mediciones describen únicamente este fixture. No se afirma que se haya probado/construido en producción.

Comandos finales reproducibles (todas las rutas son absolutas):

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/gasto-ia@v1.r1.dir-a.html --widths 1280,390,768 --max-combos 100
```

ASPECTOS POR RESOLVER: esta dirección y las opciones propuestas de ruta/intervalo temporal/precisión siguen sin aprobarse. La autorización real del servidor, la agregación entre páginas, el cálculo exacto de costos, la idempotencia, la conciliación de reintentos, la contabilidad del proveedor y el aislamiento real de sesiones están fuera de esta exploración y no se han verificado. La navegación a páginas paralelas externas nombra sus destinos reales; esas páginas no están implementadas en este archivo estático. No se produjo ningún bloqueo por fallback ni por la cadena de herramientas. Esta exploración no redacta intencionalmente el contrato canónico completo de doce secciones.

## Preguntas abiertas para el propietario

P: ¿Gasto IA debería usar `/admin/gasto-ia` e incorporarse a la navegación de administración existente para el personal? Esta exploración propone ese destino; el brief no fija la ruta.

P: ¿Qué intervalo de fechas debería cubrir la consulta inicial de gastos? La maqueta usa únicamente la fecha de la tarea proporcionada, claramente identificada como contexto del fixture; no se infiere ningún intervalo de producción.

P: ¿Las fechas de llamadas mostradas deberían usar UTC o la zona horaria de Bogotá utilizada en el registro paralelo de cuentas? En esta exploración se especifica UTC; el almacenamiento en producción sigue siendo UTC.

P: ¿Es suficiente mostrar el USD estimado con cuatro decimales o deben mostrarse los importes conocidos más pequeños con mayor precisión? La versión final debe fijar el formato sin convertir los valores desconocidos en cero.

Todas las preguntas corresponden a David/Planner. No impiden comparar esta dirección del borrador. Aquí no se solicita ni se concede aprobación.
