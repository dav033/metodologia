---
name: Molde — piezas a presión
status: draft
kind: direction-exploration
contract_ref: taller-esenciales@v1
subplan: SP-3
requirements: [R9, R10, R11]
revision: r9.dir-c
chosen_thumbnail: taller-esenciales@v1.r9.dir-c.html.candidate-1.html
---

# Molde — dirección C

Esta es una exploración independiente sin aprobar, no el contrato canónico. Conserva la fuente de comportamiento compartida y deja sin cambios todos los contratos, planes, historial y repositorios de producción compartidos. El propietario elige la dirección antes de que un finalizador independiente redacte el contrato de doce secciones.

## Concepto, gesto memorable y por qué no es la opción predeterminada

Los decoradores de eventos trabajan con piezas moldeadas, látex suave, tela doblada, lámina metálica y herramientas. Molde convierte la superficie de trabajo en una bandeja de empaque moldeada: cada objeto tiene su cavidad, una mesa se coloca junto con sus sillas y los cuatro destinos de trabajo se ubican en un cinturón inferior de herramientas. El gesto memorable es la mesa y sus sillas comprimiéndose hasta quedar en su sitio mientras la etiqueta de especificaciones se despliega a su lado. Los botones se presionan con resistencia material; un arrastre horizontal opcional de la mesa se asienta gracias al resorte instalado, con alternativas explícitas de izquierda/derecha.

La composición es un plano de montaje visto desde arriba y un cinturón de herramientas moldeado, no un panel genérico con navegación a la izquierda. Las formas tipográficas grandes en serif cursiva dan una voz escultórica; el frambuesa y la ciruela provienen del material de los globos, en lugar de la paleta morada predeterminada del SaaS. El color decorativo se limita a los materiales de la escena/paquete; el color también identifica el éxito, las advertencias y los errores. Cada advertencia incluye palabras.

## Miniaturas dibujadas primero

1. **Elegida:** `taller-esenciales@v1.r9.dir-c.html.candidate-1.html` — escena amplia, etiqueta de especificaciones y cinturón de herramientas inferior. Da espacio a la escena y deja un lugar predecible para la edición numérica.
2. `taller-esenciales@v1.r9.dir-c.html.candidate-2.html` — órbita de discos circulares de herramientas alrededor de una escena circular. Se conserva como composición exploratoria; la navegación ocupaba el espacio necesario para las dimensiones y las etiquetas más largas en español.

Ambas son miniaturas visuales autocontenidas, con selectores de tema y redistribución para teléfonos. Son bocetos, no representaciones de componentes shadcn instalados. La dirección completa usa la cadena de herramientas instalada real, sin alternativa de respaldo.

## Ocho ejes

| Eje | Diseño observable |
|---|---|
| concepto | Molde: un decorador presiona, coloca y empaca piezas para eventos en una bandeja moldeada de herramientas. El látex y la lámina metálica inspiran las cavidades redondeadas, la silueta de la mesa y la respuesta reactiva al presionar. |
| distribución | Una escena amplia vista desde arriba ocupa la parte superior izquierda; a su derecha se coloca una etiqueta de especificaciones, y debajo aparece una bandeja de cavidades de ocho formas. Backing se convierte en una bandeja amplia de muestras, la lista de compras en un comprobante de empaque que prioriza cantidades y la exportación en un paquete de dos partes. A 700px estos planos se apilan; el cinturón de cuatro herramientas permanece cerca de la parte inferior. |
| navegación | Un cinturón moldeado fijo de cuatro estaciones en la parte inferior permite elegir Mesas, Backing, Lista y Exportar. Las tarjetas de mesas las añaden con las dimensiones predeterminadas y abren inmediatamente el inspector; las acciones en línea Return y Undo mantienen el contexto de trabajo. Un diálogo de ayuda aparte explica la importación en Blender; los selectores nativos de planificación permanecen fuera del producto. |
| tipografía | FreeSerif Bold Italic local incrustada, de 54–88px, da al título de trabajo una silueta escultórica y comprimida; Liberation Sans local incrustada, de 13–26px, se usa para las etiquetas y los datos. Los números de cantidad prioritaria del comprobante de empaque usan la serif expresiva en tamaños de 38–45px. Esta combinación difiere de las direcciones hermanas con sans condensada y redondeada. |
| densidad | Amplio espacio para la escena y márgenes interiores de 26px en el inspector; cuatro cavidades con márgenes interiores de 20px en escritorio y dos con márgenes interiores de 16px en teléfono. Los controles de trabajo tienen áreas táctiles de al menos 44px; la selección, la capacidad y la acción siguiente se indican con texto explícito. Sin panel de KPI ni métricas ornamentales. |
| componentes | Button, Input y Skeleton reales de shadcn/Base UI instalados; primitivas de diálogo de Animate UI Base UI, arrastre Motion y resortes de perfil. Siluetas personalizadas en SVG de mesas/globos/objetos, cinturón de herramientas moldeado y composición de empaques. Se incluyen en modo de solo lectura la normalización pura de mesas, los contornos, la colocación de sillas y la asignación explícita del repositorio existentes. |
| color | Acciones frambuesa propuestas #a20c48 sobre material de empaque rosa #f4dfe7, tinta ciruela oscura #381526 y lámina metálica #c79750 limitada al material decorativo. Fondo ciruela oscura #28131f y superficies #3a2030 usan acciones rosa pálido #ffc0d7 y texto #fff1f7. Los roles semánticos existentes de Pictures se asignan a los roles del kit; los valores morados de producción no se modifican silenciosamente. |
| movimiento | Gramática de presionar y colocar con cubic-bezier(.18,1.38,.48,1), coreografía expresiva de 720ms para planos/etiquetas y controles de 180ms; asentamiento en perspectiva de bandeja, compresión tipográfica cursiva, torsión de etiquetas, recortes escalonados de cavidades/sillas, interacción del cinturón de herramientas, despliegue del paquete, respiración ambiental del látex, liberación de presión en errores, sello de éxito y arrastre directo interrumpible. Natural: 460/160ms; sutil: 260/120ms; reducido/estático mantiene la misma funcionalidad de forma inmediata. Los efectos ambientales se pausan fuera de pantalla y en pestañas ocultas. |

## Registro visual e identidad compartida

Se leyeron las notas y el JSON de las direcciones hermanas para `cuentas-admin@v1.r10.dir-a/b/c` y `proyectos@v1.r8.dir-a/b/c`: registro de producción, entrada inflable, bandas de tensión, archivo desplegable, cinta de escenario y carpetas de muestras. Molde conserva Pictures, la marca de círculos enlazados, el vocabulario de eventos, las etiquetas en metros, la recuperación explícita y los controles utilizables. No repite su estructura de identidad a la izquierda, bandas de permisos, pestañas de carpetas, cinta de proyectos ni transportador superior de estaciones. La barra de herramientas de planificación es intencionalmente idéntica porque el comparador controla sus selectores nativos.

## Fuentes y uso real de bibliotecas

Se leyeron SPEC.md, PLAN.md, SP-3/tasks de PLAN.json y la fuente de comportamiento compartida r9. SHA-256 de la fuente de comportamiento compartida: `4113589a9342573e5a6a3e16661117ce6e982908a43a9736aad8b12c1540846f`.

La inspección de solo lectura del repositorio abarcó `globals.css` de t12 y asesor, el editor de mesas existente, la creación de muebles, los tipos/defaults/límites paramétricos, la colocación de sillas, el catálogo de Backing y la asignación explícita de repositorios. Ambos repositorios usan `--fondo`, `--superficie`, `--texto`, `--texto-suave`, `--acento`, `--sobre-acento`, `--borde` y roles de Taller. Esta exploración asigna sus responsabilidades a `--background`, `--card`, `--foreground`, `--muted-foreground`, `--primary`, `--primary-foreground`, `--input` y `--ring`. Los valores frambuesa/ciruela propuestos son propuestas de diseño locales que responden a comentarios del propietario, no afirmaciones sobre los valores actuales en producción. El objetivo para texto es 4.5:1; para bordes de controles/foco, 3:1. No se usa ninguna casilla de verificación nativa.

Importaciones reales: `shadcn:button default/outline/disabled` (`@/components/ui/button`); `shadcn:input default/invalid/disabled` (`@/components/ui/input`); `shadcn:skeleton loading` (`@/components/ui/skeleton`); `@animate-ui/react/primitives/base-ui/dialog` instalado para la contención del teclado, el fondo inerte y el retorno/cierre del foco; `motion/react` para la respuesta al arrastre; `@kit/motion` para el resorte del perfil y el estado reducido; `mountMockup` / `useMockup` de `@kit/mockup`. Los componentes personalizados son la bandeja/cinturón de herramientas moldeados, el esquema SVG, el comprobante de cantidades y el paquete de exportación. Sin instalación de paquetes, recursos de red ni alternativa mediante fragmentos de código.

FreeSerif Bold Italic y Liberation Sans Regular locales se incrustan como URI de datos en memoria. El resultado de compilación es autocontenido. El mismo CSS de entrada también se incrusta en un `<style data-direction="c">` estático tras la compilación offline para que el verificador de contraste estático mida la asignación de roles propuesta, no solo los valores predeterminados del kit compilado.

## Comportamiento y vistas disponibles

| Vista | Resultado conservado |
|---|---|
| Mesas | Una tarjeta de creación por cada tipo paramétrico existente: redonda, cuadrada, rectangular, ovalada, coctelera, media luna, serpentina y en U. Una tarjeta añade la mesa de inmediato con las dimensiones PARTIDA_MESA y abre su inspector. La rectangular comienza en 2.40 × 0.90 × 0.75m. Sin formulario previo a la creación. Las piezas imperiales fijas permanecen en su catálogo establecido. |
| Inspector | Mesa rectangular seleccionada de forma predeterminada; metros en los controles y conversión del modelo a centímetros, restricciones de largo/profundidad/altura, de 0 a 40 sillas solicitadas, cantidad/capacidad real colocada, siete tipos de silla existentes y cinco disposiciones. Una configuración de cuarenta sillas muestra la advertencia. Mesa/sillas se mueven y giran juntas; Undo restaura el modelo local anterior. El SVG usa contornos reales de mesas y coordenadas de sillas, no totales de sillas inventados. |
| Backing | Exactamente siete IDs originales: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal, arco_metalico. La búsqueda acepta nombres comunes, IDs y Backing. El filtro del repositorio usa el mapa ASIGNACION_FONDOS real (los siete pertenecen actualmente a escenografia). Cada elemento aparece una vez y puede añadirse. No se inventan productos de Shopify ni alias de catálogo. |
| Lista de compras | Cantidades y dimensiones de mesas y sillas realmente colocadas, seguidas por las cantidades añadidas de Backing y las dimensiones de origen (se identifica el arco más grande/pedestal azul al describir un conjunto). Sin precios de alquiler. La cantidad refleja el truncamiento por capacidad. |
| Exportar | Propósito de exportar la escena completa como GLB, metros, colores base, posiciones y exclusión de la luz/controles solo del editor; estados explícitos de inactividad, preparación, deshabilitado por escena vacía, error con posibilidad de reintento y éxito. La ayuda incluye los pasos para importar glTF en Blender. La simulación no genera ni valida un GLB. |

Proyecto de ejemplo: Cumpleaños de Lucía. Configuración inicial: una mesa rectangular, ocho sillas, ningún Backing colocado; los tres globos en la parte superior del esquema son un estudio decorativo de materiales, no objetos de escena contados. Todos los valores son datos locales de prueba. La normalización de mesas, los contornos, la colocación real de sillas y la asignación de repositorio provienen del repositorio inspeccionado como importaciones de solo lectura. La paridad de herramientas de IA, la compatibilidad de IDs guardados/búsqueda/fotos, la exportación GLB en coordenadas del mundo, la importación real en Blender y Undo en producción siguen siendo responsabilidades de implementación/integración (T3.2–T3.6); este mockup no afirma haberlos verificado.

## Estados, navegación y recuperación

Los selectores nativos visibles son Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` y Movimiento `motion`; el movimiento predeterminado es expresivo. Un selector de idioma del producto demuestra el ajuste del texto en español e inglés. La barra de herramientas inferior dirige a Mesas / Backing / Lista / Exportar; se accede al inspector al agregar una mesa, mediante la acción Edit table o el selector de planificación.

Selector de estado: normal; carga/preparación estructural; vacío/sin resultados; error recuperable; éxito; capacidad insuficiente; tamaño no válido; límite de piezas de la escena; sin conexión. La carga sustituye el contenido por Skeletons estructurales y anuncia el progreso. El inspector, la lista y la exportación vacíos muestran una siguiente acción, y la exportación permanece deshabilitada. La escena vacía del catálogo de mesas mantiene disponibles las tarjetas de creación. Si Backing no muestra resultados, se borran la búsqueda y los filtros de repositorio. Los errores conservan los datos locales y permiten volver a intentarlo. La advertencia de capacidad muestra por separado la cantidad solicitada, la capacidad y la cantidad colocada; un tamaño no válido conserva el último valor válido. El límite de piezas rechaza las adiciones sin crear objetos parciales. Sin conexión, se permite seguir editando y exportar localmente, mientras se deshabilita la exploración remota del catálogo. Los fixtures globales no relacionados conservan el contenido local normal en lugar de inventar permisos o estados remotos. La denegación de autenticación o permisos corresponde a SP-2, y la persistencia y los conflictos del servidor, a SP-4; no se incorporan aquí.

Cada diálogo de ayuda se puede abrir de forma independiente desde Diálogo y desde los controles Help/Open in Blender del producto. Se cierra con Escape o Got it, aísla el fondo y usa transiciones que respetan la configuración del perfil. Ninguna acción esencial depende de arrastrar. Los botones explícitos para mover están en el panel desplegable de posición; Tab y Enter permiten usar todos los destinos y controles de creación.

## Expectativas de diseño adaptable y accesibilidad

Escritorio por encima de 1000px: márgenes exteriores de 40px, proporción 1.65:1 entre la escena y el plano del inspector, y cavidades para objetos en cuatro columnas. Entre 701 y 1000px: márgenes de 26px, proporción 1.2:1, cavidades en tres columnas y controles de dimensiones del inspector apilados. En 700px o menos: márgenes exteriores de 20px, primero la escena y luego el inspector, cavidades en dos columnas y barra de herramientas inferior compacta con iconos y texto. En 370px o menos: cavidades en una columna y campos de dimensiones. Sin desplazamiento horizontal de página; las etiquetas se ajustan en varias líneas. El espacio inferior de la página deja lugar para la barra de herramientas fija; el diálogo de ayuda se limita al área visible y se desplaza internamente.

Objetivos: contraste de texto y controles WCAG 2.2 AA, áreas interactivas de 44px, contorno de foco visible de 3px, encabezados y etiquetas semánticos, anuncios de cambios no intrusivos, advertencias enfáticas y recuperación ante errores. El SVG decorativo se oculta cuando corresponde; el esquema incluye una descripción de la escena. Con prefers-reduced-motion, still=1 y el perfil Quieto, se eliminan los desplazamientos, el movimiento de resorte al asentarse, la respiración infinita y las transiciones, mientras se conservan la información final y las acciones. La suspensión de pestañas ocultas y de IntersectionObserver pausa el trabajo ambiental. El movimiento de entrada usa transformaciones sin volver transparente el texto, para que los fotogramas intermedios sigan siendo legibles.

## Ejemplos de aceptación visual para la finalización

| ID | Punto de quiebre | Estado | Comportamiento observable esperado |
|---|---|---|---|
| C-01 | 1280px | normal / Mesas | La escena amplia y la etiqueta de especificaciones comparten una fila superior; debajo caben cuatro cavidades con formas de mesa. |
| C-02 | 390px | normal / Inspector | La escena, la etiqueta y la barra de herramientas inferior caben en el área visible, con márgenes del producto de 20px y sin desplazamiento horizontal. |
| C-03 | todos | normal | La creación rectangular lleva directamente al inspector con dimensiones 2.40 × 0.90 × 0.75m. |
| C-04 | todos | capacidad | La cantidad solicitada (cuarenta), la capacidad real y la cantidad colocada se muestran por separado; la lista de compras usa la cantidad colocada. |
| C-05 | todos | normal / Backing | Los siete ID originales aparecen una sola vez; al filtrar por Mobiliario, no hay resultados de Backing en la asignación inspeccionada. |
| C-06 | todos | carga / Exportar | Los marcadores de posición estructurales y el texto de preparación reemplazan el área de acciones de edición y exportación. |
| C-07 | todos | error / Exportar | El error indica que la escena está intacta y ofrece volver a intentarlo. |
| C-08 | ambos temas | teclado | Los controles muestran un contorno contrastante de 3px; la ayuda mantiene el foco dentro del diálogo y se cierra con Escape. |
| C-09 | todos | reducido / still | Los títulos, las bandejas, las etiquetas y la escena llegan a la misma posición final sin animación continua. |

## Evidencia de auditoría transparente

- Constructor sin conexión para biblioteca real: aprobado, HTML empaquetado de 1,989 KB antes de incrustar la hoja de estilos estática de roles duplicada; sin fallback. El HTML final autocontenido incluye fuentes incrustadas y el CSS estático de roles idéntico.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- Primera auditoría completa corregida: 200 renderizados de 200 combinaciones planificadas, 6,616 mediciones de texto y 786 paradas de foco en 1280/390 para ambos temas.
- `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Una comprobación posterior de interacción con movimiento reducido detectó transformaciones al pasar el cursor pese a las transiciones inmediatas. Se eliminaron esas transformaciones con reduced/still y se repitió la auditoría completa final; sus mediciones finales se registran abajo.
- Prueba interactiva en navegador: aprobada para ocho tarjetas de tipos, creación rectangular/inspector predeterminado, fixture real de silla con cuarenta solicitadas y diez colocadas, y cantidades de la lista; siete tarjetas de Backing, búsqueda por ID y filtro de repositorio, agregar/mover/rotar/deshacer, modal/Escape, cambio a inglés y éxito simulado de exportación. Sin errores en la consola ni solicitudes externas.
- Capturas de pantalla renderizadas inspeccionadas en 1280, tema claro, Mesas; 1280, tema oscuro, Exportar; 390, tema claro, Backing; y 390, tema oscuro, Inspector. Las vistas de teléfono se apilan y mantienen bordes legibles; la barra fija deja espacio al final de la página.
- Auditoría final tras corregir el comportamiento al pasar el cursor con movimiento reducido: 200/200 renderizados, 6,616 mediciones de texto y 786 paradas de foco. `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Comprobación adaptable adicional: veinte combinaciones de vista normal en inglés a 320/768px para ambos temas aprobaron sin desbordamiento horizontal ni errores en la consola.
- Se ejecutó `compare_directions.py A.html B.html C.html --json` tras crear los tres archivos sidecar. Todas las comprobaciones de geometría y distinción entre pares aprobaron: similitud de diseño A/B 0.006, A/C 0.019 y B/C 0.024; la tipografía, la navegación y el movimiento difieren en cada par. Se midieron correctamente todas las afirmaciones sobre selectores C, incluidos los seis selectores animados.
- **El comparador global terminó con código 1 / FAIL:** `evidence_ok: false`, únicamente por falta de evidencia de `.chapter` en `taller-esenciales@v1.r9.dir-a.html`. Es un problema de selector de A; no se editó ningún archivo A/B. El intento anterior, antes de que B escribiera su sidecar, devolvió `COMPARE NOT RUN` por la falta del JSON de B; la comparación completada arriba reemplaza ese intento. No informes que la comparación global fue aprobada.

## Impacto, preguntas y aprobación

Los consumidores siguen siendo la versión 1 del contrato de UI de SP-3, la tarea de diseño T3.1, la implementación T3.2/T3.3/T3.4, la revisión visual T3.7 y la auditoría T3.8. No se redirige a ningún consumidor. La compatibilidad está **indeterminada hasta la selección/finalización**; esta composición cambia la jerarquía, la navegación, las formas, los tokens, la tipografía y el movimiento, y requerirá implementación y revisión explícitas si se selecciona. No autoriza un rediseño de producción fuera de SP-3.

P: Si se selecciona Molde, ¿la paleta de frambuesa y ciruela y la tipografía serif de exhibición deben mantenerse exclusivas de Taller o convertirse en una propuesta de identidad compartida para una futura finalización del administrador/proyecto? Responsable de la decisión: David; aquí no se realizan cambios entre subplanes.

No se reabren las decisiones confirmadas por el responsable: creación predeterminada por tipo, cantidades reales de sillas, sin precios de alquiler, un grupo de Backing que conserva los ID y la capacidad de descubrimiento, y el GLB existente verificado en Blender real. La selección de dirección y la finalización del contrato canónico siguen pendientes.
