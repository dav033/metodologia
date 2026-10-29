---
contract: herramientas-chat
version: 1
status: draft
subplan: SP-7
direction: c
name: Mesa editable
source_behavior: herramientas-chat@v1.r1.behavior.md
owner: David
---

# Mesa editable — exploración de la dirección C

## 1. Identidad y trazabilidad

Exploración preliminar para herramientas-chat@v1; no es el contrato canónico ni está aprobada para implementación. R13/R16; consumidores de interfaz de SP-7: T7.1, T7.5–T7.8 y T7.10. El responsable elige una dirección antes de que una persona encargada de finalizar redacte el contrato compartido de doce secciones. Esta delegación cambia solo sus seis artefactos de diseño específicos de la revisión y el resultado de delegación requerido.

Fuente del alcance: `herramientas-chat@v1.r1.behavior.md`. SPEC/PLAN son contextuales; el Planner activo puede modificarlos. Fuentes inspeccionadas en modo de solo lectura: ambos repositorios proporcionados, t12 globals.css/layout.tsx, CabeceraApp/MenuApp, VistaGuiada, CotizacionProfesional/CampoGanancia, IdeasDelAsistente/Biblioteca; archivos Markdown y HTML compilado de cuentas-admin@v1, planes@v1 y proyectos@v1, subplanes hermanos. Rigen su encabezado compartido, navegación horizontal, superficies de trabajo redondeadas, fuentes, formas de controles y asignación de tokens. La fuente de dirección C r12 seleccionada de proyectos proporcionó solo la asignación CSS compartida y las importaciones locales de fuentes. Se conservaron las modificaciones no relacionadas existentes en los repositorios/HQ.

Compatibilidad: **indeterminada hasta que el responsable elija**. Esta es una composición propuesta para SP-7, no una modificación del comportamiento aprobado de los subplanes hermanos. No se redirige ningún otro subplan; bajo esta delegación acotada no se escriben PLAN, contrato canónico, registro de cambios, fuente de producción, pruebas del repositorio ni memoria del proyecto.

## 2. Propósito y usuarios

La persona con sesión iniciada abre una herramienta permitida, cuenta globos sin ver precios, puede llevar los materiales a la cotización profesional existente u abrir una decoración lista en Taller. Master Designer y el personal pueden usar el explorador; una ruta directa no autorizada al calculador/galería/taller muestra Sin acceso. Los nombres de planes nunca aparecen como invitación para actualizar. Cada cantidad, precio, tolerancia, etiqueta de decoración y diagrama simulado se identifica explícitamente como dato de muestra, no como resultado del motor/catálogo.

## 3. Enfoque, jerarquía y miniatura elegida

**Elegida: candidata 1**, `herramientas-chat@v1.r1.dir-c.html.candidate-1.html`. Ambas candidatas se dibujaron antes del TSX completo. La candidata 1 ubica la decoración visible y el detalle de edición junto al resultado de compra; la candidata 2 presenta una franja de formulario de ancho completo antes de la vista previa/resultado. La primera mantiene junta la relación entre control y efecto, con menos movimiento de la mirada entre secciones distantes. Ambas son composiciones pequeñas dentro de la estructura existente, no propuestas de marca alternativas.

El cambio está en el área de trabajo: las medidas se despliegan debajo del esquema; los precios se editan en la fila de material correspondiente; los gastos se despliegan en la misma cotización; la vista previa de una decoración se abre dentro de su propia franja. No se propone rediseñar el editor, las reglas de cotización profesional ni la conversación guiada. Inicio conserva tarjetas de herramientas permitidas que abren páginas separadas; la primera tarjeta, que ocupa ambas columnas, conserva el rol heredado de entrada al chat normal, sin un encabezado promocional.

### Ocho ejes

| Eje | Expresión visualizada |
|---|---|
| concepto | Mesa editable: operar sobre medidas, precios de materiales y vistas previas de decoraciones donde se ve su efecto, manteniendo la estructura existente del producto Pictures. |
| distribución | El contador en escritorio es una superficie de trabajo con proporción 1.45:1 y una superficie esquemática/de medición junto al resultado de compras; el calculador muestra filas editables de ancho completo seguidas de una franja de totales integrada; la galería usa franjas horizontales expandibles para elementos, no una cuadrícula de tarjetas. Inicio usa dos columnas y la primera herramienta ocupa ambas. |
| navegación | Rutas horizontales neutrales heredadas, tres botones de método de conteo en línea, un control explícito para desplegar medidas, otro para desplegar gastos y una sola vista previa de decoración expandida a la vez; cada tarjeta de Inicio sigue abriendo su propia página de herramienta nueva o existente. |
| tipografía | Geist Sans / Geist Mono integradas existentes. El encabezado de página heredado mide 24px; los encabezados de elementos, 20px; el texto del cuerpo, 15px; el texto complementario, 12–14px; y el conteo, 28px con cifras tabulares. No se cambian la fuente ni la identidad. |
| densidad | Márgenes interiores de trabajo de 28px y separaciones de 20–28px; una cotización profesional continua con filas de entrada separadas por líneas; las franjas de la galería muestran una vista previa completa a la vez. En teléfono se usan márgenes interiores de 20px, campos apilados y flujo de elementos de ancho completo. |
| componentes | Button, Input, Skeleton de shadcn/Base UI instalados y Dialog de Animate UI, recompuestos como controles de medición en línea, filas editables de materiales y franjas expandibles de decoración; selectores/details nativos conservan el vocabulario visual de los subplanes hermanos. |
| color | Tokens exactos de fondo/superficie/texto/acento de Pictures y de superficie de Taller; alias texto-tenue existente del subplan hermano para los bordes de controles. El color primario señala una acción principal; la navegación permanece neutral. Ambos temas existentes se asignan a los roles del kit. |
| movimiento | Presionar y asentar con respuesta táctil: registro de papel/objeto comprimido durante 520ms, con desfases de 35ms; respuesta al presionar durante 170ms; botones presionados con desplazamiento de 2px y escala 0.965; el asentamiento del diagrama y la bisagra de la vista previa usan cubic-bezier(.34,1.4,.64,1). Los perfiles natural/sutil usan 320/140 y 160/100ms. La animación de resorte de Motion usa el perfil instalado. El movimiento reducido/quieto elimina el desplazamiento y conserva todos los controles; los efectos repetidos ocultos/fuera de pantalla se pausan. |

## 4. Sistema de diseño y componentes fijos

Los tokens de producción y la asignación de roles accesibles de los proyectos hermanos se conservan exactamente:

| Token del proyecto | Rol del kit | Claro / oscuro |
|---|---|---|
| --fondo | background | #faf9fc / #0b0c10 |
| --superficie | card, popover | #ffffff / #16181f |
| --texto | foreground | #1c1425 / #f4f5f7 |
| --texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| --superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| --acento | primary, ring | #6d3fe0 / #9479ff |
| --sobre-acento | primary-foreground | #ffffff / #120b24 |
| --acento-hover | primary-hover | #5530b8 / #a58dff |
| --borde / --borde-suave | borde decorativo / separador | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| --texto-tenue | borde de entrada/control | #766c85 / #8a91a0 |
| --exito, --aviso, --error | éxito, advertencia, destructivo | Valores existentes del tema en globals.css |
| --taller-visor | superficie esquemática / existente de la escena Taller | #ebe7f1 / #1a1722 |

Panel de 32px, inserción de 24px, campo de 18px y píldora de 999px coinciden con los contratos de los proyectos hermanos. Las fuentes para cuerpo y monoespaciadas son los recursos WOFF2 locales reales de t12 Geist, integrados por el generador offline. No se añade identidad de paleta ni tipográfica. Los diagramas usan los tokens existentes de superficie de la interfaz en lugar de inventar muestras de color para globos; los nombres de color del resultado son etiquetas autoritativas. Los esquemas se identifican explícitamente como dibujos esquemáticos, no como miniaturas reales de decoración ni como un renderizador 3D.

Componentes: `shadcn:button default|outline normal|hover|focus|pressed|disabled` de `@/components/ui/button`; `shadcn:input number|text normal|focus|edited` de `@/components/ui/input`; `shadcn:skeleton loading` de `@/components/ui/skeleton`; `shadcn:dialog unsaved open|closed` de `@/components/ui/dialog` (implementación instalada de Animate UI/Base UI). Select, textarea, entrada de archivo y details/summary nativos se describen con precisión; el boceto, el papel de trabajo, la tabla de compras, las filas de cotización en línea y las bandas de decoración son composiciones personalizadas. Se usan `mountMockup/useMockup` y `useMotionProfile` del entorno de ejecución instalado. No se instalaron paquetes, ni se usaron CDN, recursos descargados o alternativas HTML.

## 5. Navegación e interacción

Conservar Pictures/Sempertex, los controles de idioma/cuenta y la navegación horizontal neutra. Las rutas de producto son `/`, `/asistente`, `/contador`, `/calculadora`, `/3d/decoraciones` y `/3d?decoracion=<id>`; el prototipo las simula localmente, sin solicitudes de red. El catálogo, los proyectos, la cuenta, los planes, la implementación de tema/idioma y los controles del taller existentes siguen siendo contexto y no páginas nuevas de esta propuesta. Los controles de contexto identifican su destino en vez de simular operaciones del producto. La selección de la cuenta de prueba es un control externo de inspección de Mockup; nunca es un cambio de rol de producción.

El inicio omite las herramientas que no tienen permiso en lugar de mostrar tarjetas bloqueadas. El contador tiene botones de Formulario/Frase/Foto y el desplegable Editar medidas. Al abrir la herramienta de costos, se transfiere el resultado simulado del material y se muestra Materiales del contador. Las filas de cotización muestran la cantidad del paquete y el precio editable; los gastos son un desplegable nativo; Tu ganancia conserva el sentido de la fórmula existente. Los totales se ocultan mientras se espera el cálculo posterior a la edición. La cuadrícula de gastos usa cuatro columnas en escritorio, dos en tableta y una en teléfono. Los demás modos admitidos del componente profesional existente, la procedencia de compra y las exclusiones deben conservarse durante la implementación; aquí solo se muestra el ejemplo del paquete.

El explorador mantiene los filtros de búsqueda, ocasión y tamaño sobre bandas de objetos expandibles. Vista previa/Ocultar vista previa cambia una banda en el mismo lugar. Al abrir sin trabajo sin guardar, se inicia una escena nueva sin guardar. Si hay trabajo sin guardar, Cancelar lo conserva; Guardar y continuar requiere confirmación del guardado por el servidor antes de abrir; Descartar escena y continuar es explícito. El mock solo simula el éxito y señala la dependencia del servidor. No se sobrescribe ningún proyecto actual. Los vínculos desconocidos muestran Decoración no encontrada y mantienen intacta la escena abierta. En producción, los enlaces profundos usan identificadores reales del catálogo, nunca estos identificadores de ejemplo.

## 6. Flujos

1. Iniciar sesión → tarjetas permitidas en la página de inicio → página de herramienta independiente. El selector externo de cuentas de prueba muestra Entusiasta/Designer, Designer Plus, Master Designer y personal. En producción, los permisos deben hacerse cumplir en el servidor.
2. Formulario → desplegar las medidas → seleccionar estructura/tamaños/colores → Contar globos → cantidades por tamaño/color y lista de paquetes, sin precios. Si falta una medida en la frase, se solicita. La selección de una foto se mantiene local; el resultado de ejemplo indica explícitamente que es una estimación y muestra un margen de tolerancia de ejemplo. Al editar una medida, se retira el conteo anterior hasta volver a ejecutar el cálculo.
3. Contador → Calcular costo (solo con costos.usar) → filas de materiales importadas → editar precio/cantidad o desplegar gastos → calcular → totales de materiales/gastos/cliente. Al iniciar vacío, se ofrecen acciones para agregar materiales o ir al contador. Si falla la cotización, se conserva el trabajo ingresado y se ofrece volver a intentar. Todos los cálculos del prototipo son ilustrativos; Python sigue siendo responsable de los totales reales y el catálogo sigue siendo la fuente de los precios.
4. Taller → Decoraciones → filtros → vista previa en el mismo lugar → enlace para abrir como nueva → opción de proteger el trabajo existente sin guardar → nueva escena sin guardar. Se pueden restablecer los filtros sin resultados; los errores permiten volver a intentar; los identificadores desconocidos no pueden modificar la escena actual.
5. Saludo/chips/compositor de chat existentes → vista previa de la idea → transferencia permitida a Taller. No aparecen precios sin restricciones, recomendaciones de planes ni contadores de límites. La conversación guiada completa de producción no cambia; esto solo proporciona contexto representativo.

## 7. Vistas y composición adaptable

| Valor de vista previa | Superficie de trabajo | Composición |
|---|---|---|
| home | / | Tarjetas de herramientas permitidas en 2 columnas; el primer chat ocupa ambas; una columna en teléfono. |
| counter | /contador | Franja de métodos → esquema y controles de edición junto al resultado de compras → una sola acción para contar. |
| calculator | /calculadora | Filas de materiales regladas a todo lo ancho → desplegable de gastos en el mismo lugar → campo de ganancia → franja integrada de totales/acción. |
| chat | /asistente | Vocabulario existente para saludo/conversación/chips/compositor centrados; ejemplo sin precios y enlace permitido a Taller. |
| gallery | /3d/decoraciones | Búsqueda/ocasión/tamaño → franjas horizontales de decoraciones → una sola vista previa en el mismo lugar y acción para abrir. |
| workshop | /3d?decoracion=<id> | Vocabulario existente de barra de herramientas/riel/escena/inspector como contexto del destino; la escena nueva aparece como Sin guardar. |

## 8. Estados y límites accesibles

Los selectores nativos Vista/Estado/Diálogo/Tema/Movimiento permanecen visibles. Los estados forman una unión; un estado que no se aplica a una vista conserva la composición normal de esa vista, en vez de inventar un estado del producto.

| Valor de Estado | Vista aplicable / respuesta |
|---|---|
| normal | Página de inicio con contenido; contador en reposo; materiales de ejemplo en la calculadora; resultados en la galería; chat inicial; escena de ejemplo actual en el taller. La página de inicio vacía es imposible. |
| loading | Contador con mensaje Contando globos; calculadora con mensaje Calculando cotización; carga de la galería; preparación del chat. Esqueletos y envío repetido desactivado. La página de inicio y el taller muestran el contexto normal. |
| empty | Calculadora Sin materiales con acciones para agregar o ir al contador; galería Sin resultados con opción para borrar filtros. El contador sigue en reposo; la página de inicio tiene tarjetas permitidas. |
| error | Fallo del motor del contador, de la cotización, de carga de la galería o del chat; opción para volver a intentar en esa vista y datos ingresados conservados. |
| missing | El contador solicita la medida y ofrece Completar medidas con el foco en el campo. |
| photo-large / photo-invalid | El contador indica el error de carga y ofrece Elegir otra imagen. El límite de tamaño del archivo no está definido. |
| result | Conteos del contador; totales explícitos de la calculadora; idea de ejemplo del chat. |
| photo-result | Método de foto seleccionado en el contador, estimación y tolerancia de ejemplo de ±12 globos; no es una política de tolerancia real. |
| imported | La calculadora muestra los materiales importados del contador; los valores siguen siendo editables. |
| editing | Campos de gastos desplegados en la calculadora; totales pendientes de nuevo cálculo. |
| unknown | El explorador/taller indican Decoración no encontrada; no se reemplaza la escena existente. |
| unsaved | El explorador abre la advertencia contextual de cambios sin guardar; Cancelar conserva la escena actual. |
| denied | Sin acceso con opción segura para volver a Inicio; no se muestran precios ni datos de listas restringidos. |

Diálogo=unsaved abre la misma advertencia desde cualquier vista de inspección; no es un diálogo de producción adicional. El comportamiento de persistencia sin conexión, guardado pendiente y conflictos corresponde al contrato de proyecto existente y no se rediseña. No se agregan cuotas, panel de facturación ni reglas de precios nuevas.

## 9. Comportamiento adaptable

- **360–639px:** márgenes exteriores y de trabajo de 20px; encabezado y controles se ajustan a varias líneas; la navegación se mantiene horizontal y puede ajustarse a varias líneas; las tarjetas y el contador se apilan; los campos de medidas/gastos/filtros quedan en una columna; las filas de materiales de cotización se convierten en campos etiquetados de dos columnas con identidad y subtotal a todo lo ancho; la vista previa de la galería va debajo del encabezado de su franja, con el diagrama antes del detalle/acción para abrir; el riel/inspector de Taller se ocultan como en proyectos. Sin desbordamiento de página.
- **640–1099px:** márgenes exteriores de 24px; el contador pasa a una columna de trabajo y los datos del resultado se muestran en dos columnas; las filas de cotización usan tres columnas y el subtotal aparece en la siguiente línea alineada; la vista previa de la galería tiene relación de aspecto 1.3:1; el inspector de Taller se oculta y el riel permanece.
- **1100px+:** ancho máximo heredado de 1520px / márgenes laterales de 40px; contador con relación 1.45:1; cuatro columnas alineadas en la cotización; vista previa de galería con relación 1.6:1 y barra de herramientas con relación 2:1:1. El contenido se desplaza verticalmente; no se ocultan controles obligatorios.

El ancho del modal es min(580px, viewport−40px), su altura máxima es viewport−48px y permite desplazamiento. Todos los objetivos interactivos principales tienen al menos 44px de alto. Los textos largos se ajustan a varias líneas. La traducción completa al inglés está en SP-10; el selector de idioma conserva aquí el vocabulario de la interfaz general y explica su alcance, en vez de afirmar que las vistas están traducidas.

## 10. Detalles de accesibilidad y movimiento

Objetivo: WCAG 2.2 AA; no constituye una certificación completa de conformidad. Etiquetas asociadas, título/encabezados de tabla, dibujos con nombre, semántica nativa de desplegables, aria-expanded/aria-controls en acciones de edición/vista previa, alertas de error y anuncios de resultados corteses. Anillo de enfoque acento de 3px con desplazamiento de 4px; texto ≥4.5:1 y bordes de controles ≥3:1. El chat conserva su encabezado de trabajo original centrado, sin añadir un título de página/pie duplicados. La navegación enfoca H1; la acción de medidas faltantes enfoca su campo. El diálogo usa el comportamiento real de contención de enfoque/Escape de Base UI, enfoque automático en Cancelar y un destino finalFocus explícito. Al cerrarse, el enfoque debe volver al control invocador que siga presente; los diálogos abiertos directamente desde el inspector no tienen un activador de producción.

La gramática de movimiento representa un asentamiento físico dentro de una superficie de trabajo: el papel se comprime verticalmente 7px/.992; las bandas de tarjetas se asientan horizontalmente en .985→1.004→1; el diagrama pasa por .96/−1deg→1.01/.2deg→1; las bisagras de vista previa usan scaleY(.97→1.008→1); los resultados se asientan 4px/.98. Todos los efectos priorizan transform. Los botones repetidos se comprimen .965 y 2px al presionarlos y luego se asientan; al pasar el puntero suben 1px. Los tiempos del perfil y la paridad de movimiento reducido/fijo coinciden con la tabla de ejes. Ninguna entrada oculta texto con opacidad; no hay efectos decorativos de escena infinitos ni destellos. La presión de los esqueletos se pausa fuera de pantalla; las pestañas ocultas pausan todas las animaciones CSS de la aplicación. El modo estático/reducido mantiene visible todo el contenido y las acciones finales.

## 11. Criterios de aceptación visual y evidencia

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | Todos | Todos | Se conservan el encabezado de Pictures/Sempertex, la tipografía Geist, los controles de cuenta/idioma y la regla de rutas neutra heredada. |
| C-AC-02 | ≥1100px | counter/result | Una hoja coloca el esquema/medidas a la izquierda y los conteos/lista de compras a la derecha, con relación 1.45:1. |
| C-AC-03 | Todos | counter/idle | Editar medidas expande en el mismo lugar los campos etiquetados de largo/alto y muestra el estado expandido. |
| C-AC-04 | Todos | counter/result | Las filas suman 120 globos de ejemplo (48+48+24), con conteos por tamaño/color y lista de paquetes, sin precios. |
| C-AC-05 | Todos | counter/photo-result | El resultado visible se indica explícitamente como estimación con tolerancia de ejemplo, nunca como una afirmación exacta basada en la foto. |
| C-AC-06 | Todos | counter/missing | Completar medidas enfoca el campo faltante; el resultado no inventa conteos. |
| C-AC-07 | Todos | counter/photo-large, photo-invalid, error | Cada problema indica el fallo y muestra una acción para resolverlo. |
| C-AC-08 | Todos | calculator/imported | Aparecen juntos el aviso de materiales del contador y las filas de materiales editables. |
| C-AC-09 | Todos | calculator/editing | Los campos de precio y paquete están en la fila del material; el desplegable de gastos está abierto; los totales actuales se ocultan hasta recalcular. |
| C-AC-10 | Todos | calculator/result | Los totales de ejemplo de materiales/gastos/cliente se alinean en la franja inferior; los precios editados actualizan la siguiente cotización simulada. |
| C-AC-11 | Todos | gallery/normal | Cada franja indica origen, ocasión y tamaño; la vista previa seleccionada se abre dentro de esa franja. |
| C-AC-12 | Todos | gallery/empty, error, unknown | Las acciones para restablecer/reintentar/volver siguen accesibles; el identificador desconocido indica que la escena actual no cambió. |
| C-AC-13 | Todos | gallery/unsaved | Cancelar, descartar explícitamente y guardar en el servidor antes de abrir son opciones visibles en el modal real. |
| C-AC-14 | Todos | home / fixture roles | Se omiten las herramientas no disponibles; se deniega la inspección directa de calculadora/Taller cuando el rol no tiene acceso. |
| C-AC-15 | 360–639px | result, normal | El contador/cotización/galería se apilan con márgenes de 20px, campos etiquetados y sin desplazamiento horizontal de página. |
| C-AC-16 | 640–1099px | normal | El contador se apila y la galería conserva columnas de vista previa/detalle; el inspector de Taller se oculta. |
| C-AC-17 | Todos | reduced/still | No queda movimiento repetido ni desplazamiento animado; todas las acciones y el resultado final siguen visibles. |
| C-AC-18 | Todos | chat | Se conserva el texto/chips/compositor guiados existentes; no aparecen contenido monetario prohibido ni mensajes para vender planes bloqueados. |

### Verificación real

| Verificación | Resultado real |
|---|---|
| Generador offline | Código de salida 0; 648 KB, 2,126 archivos fuente incluidos; React/shadcn/Base UI/Animate UI reales y recursos de producción Geist integrados. |
| Contraste de tokens | `contrast: 158 pairs checked in light and dark, all pass` (código de salida 0). |
| Auditoría final renderizada | Código de salida 0; **540 / 540** combinaciones en **1280, 390 y 768px**, ambos temas; **18,296** mediciones de texto y **2,250** paradas de enfoque. Sin aviso de muestreo. |
| Evidencia de selectores de ejes | `compare_directions.py` solo para esta propuesta: `ok=true`, `evidence_ok=true`, sin evidencia faltante. Verifica las afirmaciones sobre selectores/movimiento; no afirma que se distinga de las propuestas hermanas, cuya comparación corresponde al coordinador. |
| Verificaciones locales de interacción | CORRECTO: persistencia de permisos del inspector; calculadora no autorizada rechazada; el contador no presenta acción de COP ni costos sin permiso; importación al contador; cotización simulada de 84,000→87,600 COP tras editar un precio; se agregó un material desde una lista vacía; href y destino de enlace profundo al abrir como nuevo; cancelación/recuperación ante elemento desconocido/filtro; estimación explícita de foto. Sin errores de página ni solicitudes HTTP(S). |
| Muestra de interacción adaptable | CORRECTO: seis vistas a 360/768/1280px sin desbordamiento horizontal del documento. |
| Verificaciones enfocadas finales | CORRECTO: pruebas del chat en estado normal/resultado/carga/error en ambos temas; Escape cierra el modal y devuelve el enfoque a la acción exacta que lo abrió; `?still=1` y `?rm=1` no dejan animaciones en ejecución. |
| Inspección visual | Capturas en memoria inspeccionadas: ambas miniaturas candidatas; inicio/contador/chat en escritorio claro; galería/cotización en escritorio oscuro; resultado de recuento estimado en teléfono claro; edición de gastos y diálogo sin guardar en teléfono oscuro. No se escribieron artefactos de capturas. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

No se ocultan las verificaciones anteriores: se canceló una auditoría inicial en curso cuando cambió el artefacto y no se aceptó. La primera ejecución completa con mediciones falló con 28 hallazgos de alineación en la sección irregular de gastos de tres columnas; se recompuso en cuatro/dos/una columnas. La siguiente ejecución completa falló con siete hallazgos de alineación del chat relacionados con la franja de inspección externa y un encabezado/pie de página añadidos a todo el ancho alrededor de una conversación centrada; ahora la franja de inspección tiene semántica de encabezado y se restableció la composición del chat existente con un único encabezado de trabajo centrado y sin pie. Una verificación independiente de teclado detectó pérdida de enfoque al cerrar; ahora finalFocus de Base UI devuelve el enfoque a la acción que abrió el diálogo. La auditoría completa final anterior se ejecutó sobre el HTML resultante sin cambios, sin suprimir verificaciones ni modificar herramientas.

SHA-256 del HTML final: `90021efc3f8bd7285f8ff74769df56c891ee43901e2ef8ae14de606ceb411849`.


No se afirma que se haya ejecutado lint, verificación de tipos, compilación de producción ni verificación del proveedor/motor: esta tarea abarca únicamente artefactos de planificación. Un mock estático no implica que el catálogo esté completo, que la estimación con imágenes funcione realmente, que haya renderizado 3D, autenticación, persistencia de guardado ni equivalencia total con la cotización profesional.

## 12. Preguntas abiertas y supuestos

P: Visibilidad del catálogo en Inicio: el recorrido de SP-7 de la ronda 15 de SPEC indica que Entusiasta solo ve Chat y Contador, mientras que la descripción actual del catálogo y los permisos del plan incluye Catálogo. ¿Inicio debería mostrar la entrada permitida a Catálogo (la opción provisional de la maqueta) o excluirla deliberadamente?
P: ¿Qué límites de tamaño/tipo y representación de tolerancia proporcionada por el motor rigen el conteo de fotos? ±12 en la maqueta es explícitamente un dato de prueba, no un umbral ni una política aprobados.
P: ¿Qué metadatos de ocasión/tamaño y unidades/rangos de filtro por tamaño existen para cada elemento de Ideas del asistente e Ideas Sempertex? La maqueta usa valores exactos de ejemplo de 2m/3m; no define una taxonomía de producción.
P: ¿Qué estructuras y mediciones obligatorias expone el motor existente de conteo de formas? Arco/Guirnalda/Columna y los campos de longitud/altura mostrados son una composición provisional, no un nuevo contrato de geometría.

Confirmado: el chat normal permanece en VistaGuiada; el antiguo / clásico pasa a ser Inicio; si no hay permiso de costos, no se muestran precios; los conteos/totales/catálogos siguen bajo la responsabilidad del motor; explorer está dentro del alcance del permiso Taller; abrir crea una escena nueva sin guardar y no puede sobrescribir el proyecto actual. Las preguntas corresponden al propietario/Planner y a los contratos del motor/catálogo que proporciona los datos; la exploración continúa sin aprobarlas.
