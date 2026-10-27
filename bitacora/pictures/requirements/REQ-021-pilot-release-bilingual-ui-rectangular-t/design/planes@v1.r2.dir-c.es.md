---
name: Pliegues de consulta
contract_candidate: planes@v1
revision: r2
direction: c
status: draft
artifact_kind: exploration
ready: true
stale: false
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
source_behavior: planes@v1.r2.behavior.md
source_behavior_sha256: 3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239
chosen_thumbnail: planes@v1.r2.dir-c.html.candidate-1.html
---

# Pliegues de consulta — dirección C, r2

## 1. Identidad y trazabilidad

**Exploración preliminar, completa para comparar con la persona responsable; no es un contrato aprobado ni un insumo de implementación.** Esta nueva composición aborda la dirección C ya seleccionada por la persona responsable y los comentarios de las 14:19, `/tmp/REQ-021-planes-feedback-1.md`, y la aclaración de las 14:44. No reutiliza ni modifica un borrador anterior de planes. Los archivos canónicos, el historial, los planes, los contratos de los pares y los repositorios del proyecto permanecen intactos.

El alcance es `planes@v1.r2.behavior.md`, R17–R20 y SPEC «Comportamiento — vista adicional de SP-14 (respondida en la ronda 13)». La vista adicional solo selecciona/resalta para comparar; no realiza compras, solicitudes, registros, asignaciones de cuenta, cambios de permisos ni establece valores de límite. Todas las herramientas permanecen visibles. La ronda 13 está respondida y no se vuelve a abrir aquí.

Evidencia de producto de solo lectura: ambos `globals.css` de t12 y asesor; `layout.tsx` de t12, página de inicio de sesión/LoginForm, CabeceraApp y MenuApp. Se inspeccionó el Markdown y HTML canónicos de cuentas-admin, taller-esenciales y proyectos. La **Parte de acceso** actual de cuentas-admin aporta la cabecera, los controles nativos de idioma/cuenta, la navegación horizontal neutra, las hojas de trabajo redondeadas y el eje de acceso. La paleta de producción y las fuentes Geist prevalecen cuando las exploraciones HTML anteriores de los pares difieren de sus asignaciones de tokens escritas. En los árboles de trabajo inspeccionados todavía no existe un archivo de catálogo de planes de producción; la fixture se deriva únicamente del brief compartido. Producción debe leer el catálogo de SP-1, no copiar esta fixture como una segunda fuente de verdad.

Solo SP-14 consume `ui.contract=planes`, versión 1: T14.1 copia el contrato aprobado posteriormente; T14.2 implementa la comparación/selección; T14.3 agrega los enlaces de entrada; T14.5 revisa. T14.4 consume la verificación de integración. En relación con el comportamiento solicitado anteriormente, la vista de selección y la redistribución para tabletas requieren adaptar la implementación (cambio visual/interactivo incompatible); los tokens y los destinos de los enlaces de entrada son compatibles. La propiedad de los datos de SP-1 y el comportamiento de cuenta de SP-2 no cambian. Esta nota no redirige a los consumidores ni aprueba un contrato.

## 2. Propósito y usuarios

Las visitas públicas y las personas con sesión iniciada comparan cuatro planes acumulativos, sus precios y la disponibilidad de herramientas. Una consulta satisfactoria significa que cada plan se puede leer sin autenticación y sin listas contraídas. Una vista aparte permite elegir un resaltado para la comparación y volver a los cuatro planes. «Un administrador asigna el plan» explica la asignación de cuenta sin ofrecerla.

Los datos de cuenta neutrales son explícitamente de maqueta: Cuenta Entusiasta / cuenta Entusiasta, `entusiasta@prueba.local`, Empresa de ejemplo. Los formularios de acceso a la cuenta solo reproducen el contexto del elemento del mismo nivel; al enviarlos se muestra un aviso de límite de la maqueta y no se transmite ningún dato. Esto no verifica el servicio de cuenta.

## 3. Enfoque, jerarquía y miniatura elegida

El producto existente incorpora **hojas de consulta abiertas**, no una página de inicio de marketing. Cada hoja de escritorio coloca el nombre del plan y el precio mensual a la izquierda del primer pliegue, y todas sus herramientas a la derecha. «Pliegues» describe el gesto con el que se asienta la hoja; nunca significa una sección de herramientas contraída. La vista de selección adicional recompone el mismo contenido en hojas pares de dos por dos con un control de comparación pulsable. No se puede editar ningún dato factual del catálogo.

Se crearon dos miniaturas HTML **antes** del TSX completo y se renderizaron a 1280 px. **Se eligió la opción 1:** las hojas horizontales muestran las cabeceras de los cuatro planes en un recorrido vertical compacto y alinean las identidades con el área de herramientas. La opción 2 usa hojas de dos por dos incluso en escritorio; se conserva como evidencia visual, pero prescinde de ese eje de comparación. La versión completa usa la opción 1 para comparar y la disposición de hojas pares para la vista de selección explícitamente separada.

| Eje | Expresión renderizada |
|---|---|
| Concepto | Pulsar/seleccionar un resaltado de comparación directamente en las hojas abiertas de los planes; los datos del catálogo permanecen en modo de solo lectura. |
| Disposición | A ≥1100 px, cuatro hojas de ancho completo con columnas de identidad de 248 px y listas en dos columnas. La comparación en tabletas y la selección en escritorio/tabletas usan hojas de dos por dos; en teléfonos se usa una sola columna. |
| Navegación | Cabecera/divulgación de cuenta existentes; enlaces neutros de Comparar / Seleccionar; cuatro anclas para saltar a los planes en la comparación; retorno explícito a la comparación completa y a la superficie de entrada original. |
| Tipografía | Geist Sans y Geist Mono existentes, desde los archivos WOFF2 locales de producción. H1 de 24 px, encabezados de planes de 20 px, precios de 22 px/tabulares, herramientas de 14 px, contexto/disponibilidad de 12–14 px. |
| Densidad | Hojas abiertas cuyo tamaño se ajusta al contenido, con márgenes internos de 28 px en escritorio, 24 px en tabletas y 20 px en teléfonos; separaciones de 16 px; paneles de 32 px y formas tipo píldora existentes. Las listas en tabletas tienen una columna de texto completa por plan. |
| Componentes | Button, Input y Skeleton de shadcn/Base UI instalados; selectores/divulgación de cuenta nativos; enlaces/artículos/listas semánticos; marcas de verificación/flechas de Lucide. Sin alternativa de kit. |
| Color | Tokens exactos de Pictures en modo claro/oscuro; elementos neutros, acento en acciones/selección y aviso en etiquetas de indisponibilidad. Sin reemplazar paleta, fuente ni identidad. |
| Movimiento | Apertura/asentamiento de 440 ms, desfases entre hojas de 45 ms, ease-out existente, resorte de pulsación interrumpible y sello de etiqueta seleccionada; controles de 180 ms. Los perfiles Natural/Sutil reducen los tiempos; Reducido/quieto conserva todo el contenido sin desplazamiento. |

## 4. Sistema de diseño fijo y detalle de interacción

| Tokens de Pictures | Funciones del kit | Claro / oscuro |
|---|---|---|
| `--fondo`, `--superficie` | fondo, tarjeta/superposición | #faf9fc / #0b0c10; #ffffff / #16181f |
| `--texto`, `--texto-suave` | primeros planos, primer plano atenuado | #1c1425 / #f4f5f7; #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--borde`, `--borde-suave` | borde, separadores decorativos | #e3daef / #383c48; #efe9f8 / #2a2d38 |
| `--texto-tenue` | borde de entrada/control, como en los elementos del mismo nivel | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primario/anillo, primer plano primario | #6d3fe0 / #9479ff; #ffffff / #120b24 |
| `--error`, `--aviso` | destructivo, advertencia de disponibilidad | #b23a45 / #ff979f; #8f5f12 / #f7c46b |

El `--ease-out: cubic-bezier(.23,1,.32,1)` de origen controla el despliegue y asentamiento de las hojas. El gesto expresivo desplaza 12 px y rota de −3° a +0.4° hasta asentarse en 440 ms; el desfase es de 45 ms. La selección usa el resorte de Motion instalado mediante `useMotionProfile`; al pulsar, el puntero comprime a .965 y desplaza 2 px, y luego se asienta al soltar. Una etiqueta seleccionada aparece estampada en su lugar mientras el borde seleccionado permanece visible. La opacidad predeterminada del contenido nunca baja de .8 durante la entrada de las hojas. La duración de los estados de pasar el cursor/pulsar de los controles es 180 ms; Natural, 140 ms; Sutil, 100 ms. El tiempo de las hojas es de 280 ms/25 ms de desfase en Natural y de 160 ms/12 ms en Sutil. El gesto se puede interrumpir; nada espera a que termine la animación para poder usarse. El movimiento reducido o `?still=1` elimina las animaciones/transiciones y conserva las etiquetas de selección, los bordes, el foco y todo el texto de herramientas. Las pestañas ocultas pausan la animación CSS; no hay animaciones decorativas perpetuas ni bucles de renderizado.

Componentes de origen: `shadcn:button outline/default default|hover|focus|pressed|selected|disabled` de `@/components/ui/button`; `shadcn:input email/password default|focus` de `@/components/ui/input`; `shadcn:skeleton sheet loading` de `@/components/ui/skeleton`. Composición personalizada: `.plan-sheet` = artículo semántico + encabezado/precio + lista semántica completa, no un acordeón simulado. Los selectores nativos incluyen Vista/Estado/Tema/Movimiento, fuera del producto, e Idioma, dentro de él. No hay un eje de diálogos porque no se declara ninguno. La etiqueta **Mockup** del entorno de ejecución permanece visible.

## 5. Navegación y modelo de interacción

- `/login`: conservar el panel de acceso centrado de SP-2, los campos, la acción de inicio de sesión y el texto de recuperación; agregar exactamente un enlace «Planes» a `/planes` debajo del formulario existente. El formulario es ilustrativo; la autenticación sigue siendo responsabilidad de SP-2.
- Divulgación de cuenta compartida: conservar la identidad, Mi cuenta y Cerrar sesión; agregar exactamente un enlace a `/planes`. La vista de entrada del menú se muestra sobre el contexto existente de Mi cuenta, no en un nuevo centro de navegación. Escape y un clic fuera cierran el menú; Escape devuelve el foco a su resumen.
- `/planes`: la vista sin sesión iniciada no tiene menú de cuenta; la vista con sesión iniciada lo conserva. La navegación neutra dentro de la página ofrece «Comparar planes» y «Seleccionar para comparar». Esta última se representa como `/planes?vista=seleccionar`; es una vista local, no una nueva ruta de adquisición.
- Cuatro anclas hash desplazan el contenido y enfocan la hoja nombrada en la comparación completa; ninguna ancla filtra ni oculta otros planes. La vista de selección conserva las cuatro hojas y sus listas. Cada botón de selección tiene `aria-pressed`; solo se resalta una hoja a la vez. «Volver a la comparación completa» regresa sin cambiar el orden ni ocultar los demás planes. La selección es temporal y solo en memoria; nunca guarda un campo de cuenta, persiste una preferencia ni envía una solicitud.
- En la maqueta, Volver regresa a la superficie de entrada de origen (inicio de sesión o Mi cuenta). En producción, se conserva la ubicación de retorno del mismo origen, validada y recibida de quien invoca la vista; si se abre directamente sin sesión iniciada, el destino alternativo es el inicio de sesión; si se abre directamente con sesión iniciada, es Mi cuenta. El botón Atrás del navegador sigue disponible.

## 6. Flujos

1. Sin sesión iniciada: elegir la vista de acceso → activar su enlace Planes → leer las cuatro hojas → entrar en Seleccionar para comparar → pulsar cualquier plan → volver a la comparación completa con esa hoja resaltada → regresar a la vista de acceso.
2. Con sesión iniciada: elegir la vista de entrada del menú de cuenta → seguir el enlace Planes → comparar/seleccionar como antes → Volver regresa a Mi cuenta. La fixture de cuenta permanece como Cuenta Entusiasta durante todo el flujo, incluso al resaltar Master Designer.
3. Inglés: si el idioma inicial del navegador comienza por `en`, se selecciona inglés; otros idiomas iniciales usan español. Idioma cambia la misma fixture del catálogo entre ES/COP y EN/USD, y conserva el resaltado de comparación. Free se convierte en Gratis y Enthusiast en Entusiasta. La resolución del idioma en producción se integra con SP-2; no existe un selector alternativo de moneda.
4. Carga/vacío/error/sin conexión del catálogo: usar el selector visible de Estado. La carga muestra hojas esqueleto y un aviso de carga. Los estados de vacío/error/sin conexión muestran una explicación específica y Reintentar; en la maqueta, Reintentar restaura los datos normales de la fixture. No se presenta un catálogo parcial inventado como si fuera una comparación satisfactoria.

## 7. Vistas y contenido del catálogo

| Opción nativa de Vista | Contexto del producto | Contenido |
|---|---|---|
| `compare` | /planes, sin sesión | Cuatro fichas completas abiertas, anclas de comparación, retorno al inicio de sesión y sin menú de cuenta. |
| `compare-signed` | /planes, con sesión | Las mismas fichas, más la divulgación de cuenta existente y el contexto de retorno. |
| `select` | Vista adicional, sin sesión | Las cuatro listas completas, un resaltado seleccionable por ficha y retorno a la comparación completa. |
| `select-signed` | Vista adicional, con sesión | La misma selección informativa; la identidad de la cuenta no cambia. |
| `login` | Contexto de entrada de acceso de SP-2 | Eje de acceso existente, más exactamente un enlace a Planes. |
| `menu` | Contexto de entrada de Mi cuenta de SP-2 | Patrón existente del menú de cuenta, más exactamente una opción Planes; el formulario subyacente es un contexto ilustrativo hermano marcado en cuanto al alcance. |

Orden y precios: Entusiasta/Enthusiast Gratis/Free; Designer 20.000 COP / mes o 7 USD / mes; Designer Plus 45.000 COP / mes o 14 USD / mes; Master Designer 70.000 COP / mes o 25 USD / mes. Se muestra exactamente un idioma y una moneda a la vez. Gratis no tiene un precio cero que pueda inducir a error.

Las herramientas se repiten por completo para comunicar la inclusión acumulativa: Entusiasta incluye Chat con límites y Contador de globos; Designer incluye Chat con límites más altos y el mismo contador. Designer Plus agrega Calculadora de costos, Chat extendido, Detección de estructuras y Detección avanzada de globos. Las últimas tres herramientas enumeradas aquí (chat extendido, detección de estructuras y detección avanzada de globos) muestran el texto explícito «aún no disponible» / «aún no disponible». Master Designer repite esa lista y agrega Taller 3D, que incluye el explorador de decoraciones listas para usar sin una línea separada para el explorador. Hay 17 filas de herramientas y seis etiquetas de no disponibilidad entre las cuatro fichas. La disponibilidad sigue el resumen compartido actual; el historial inconsistente de SPEC anteriores no se usa como segunda autoridad. En la sección de planes no aparecen límites numéricos de chat, funciones del personal, funciones personalizadas, claves de permisos, afirmaciones de marketing ni controles para modificar la cuenta.

## 8. Estados

| Estado | Efecto renderizado / recuperación |
|---|---|
| Normal | Fixture completo de cuatro planes; no hay un resaltado inicial en un documento nuevo. Un resaltado elegido previamente en memoria se conserva durante la navegación. |
| Plan resaltado | Permite acceder a un resaltado ilustrativo de Designer Plus sin interacción; una selección real tiene prioridad. Es una respuesta visual de comparación, no la confirmación de un plan asignado. |
| Cargando | Cuatro fichas esqueleto, `aria-busy` y estado de carga. Sin precios supuestos ni controles de selección accionables. |
| Catálogo vacío | «No hay planes disponibles» / «No hay planes disponibles», indicaciones breves para volver a intentarlo y Reintentar. Sin inventar un nivel gratuito. |
| Error | Alerta: «No se pudieron cargar los planes» / «No se pudieron cargar los planes», indicaciones para volver a intentarlo y Reintentar. |
| Sin conexión | «Sin conexión» / «Sin conexión», indicaciones para reconectarse o recargar y Reintentar. No se anuncian precios desactualizados como vigentes. |

El selector de seis estados se aplica a las vistas del catálogo. Las capturas de entrada de cuenta o inicio de sesión conservan sus formularios normales, porque sus estados de carga, error, validación y permisos pertenecen a SP-2 y no se redefinen aquí. No aplicable a SP-14: acceso denegado por permisos (página pública), éxito de modificación de cuenta, compra pendiente, validación de registro y confirmación destructiva. Las herramientas no disponibles se presentan como texto informativo, no como botones de adquisición deshabilitados. No se inventa un estado parcial o desactualizado del catálogo; un catálogo no confirmado o parcial debe usar el tratamiento de error mientras se esperan datos autorizados.

## 9. Comportamiento adaptable

| Ancho | Comparación completa | Vista adicional de selección |
|---|---|---|
| 390–639px | Una sola columna; cada lista también ocupa una sola columna; márgenes exteriores e interiores de las fichas de 20px; las anclas de planes se ajustan en pares; los controles de encabezado pasan a una segunda línea; el pie se apila. | Una sola columna; selección debajo del nombre y el precio; acción de retorno de ancho completo; todas las etiquetas de herramientas se ajustan. |
| 640–1099px | **Regla explícita para tabletas:** fichas en cuadrícula de 2×2, en orden de catálogo por filas; márgenes exteriores e interiores de las fichas de 24px; nombre y precio sobre una lista de una columna a ancho completo. Sin cuatro columnas de escritorio comprimidas, carrusel ni tabla horizontal. | La misma cuadrícula de 2×2; selección debajo de la identidad; las listas de herramientas no se contraen. El encabezado se ajusta cuando es necesario. |
| ≥1100px | Cuatro fichas horizontales de ancho completo; identidad de 248px, área restante con una lista de herramientas en dos columnas, márgenes interiores de ficha de 28px y exteriores de 40px, ancho máximo de la aplicación de 1520px. | Fichas pares en cuadrícula de 2×2, con listas de herramientas en una columna y controles de comparación junto a la identidad cuando el espacio lo permite. |

Los formularios de entrada conservan el eje del formulario hermano de 676px exteriores y 620px interiores, márgenes de 28px en escritorio y 20px en teléfono, y encabezado y pie apilado alineados con ese eje. No hay alturas fijas de ficha ni texto de herramientas recortado. El orden de lectura sigue el orden del DOM en todos los puntos de quiebre. Se probó el reflujo a 390, 639, 640, 768, 820, 1024, 1099, 1100 y 1280px.

## 10. Objetivos de accesibilidad y límites de la evidencia

Objetivo WCAG 2.2 AA: encabezados, artículos, listas y navegación semánticos; enlaces, selectores y divulgación nativos; contorno de foco explícito de 3px en acento con desplazamiento de 4px; controles de ≥44px; estado seleccionado indicado mediante texto, marca o `aria-pressed`, no solo mediante color. El estado de no disponibilidad es texto literal asociado a la etiqueta de la herramienta. Tab/Enter/Space operan los controles; al cambiar de vista, el foco pasa a H1; los enlaces hash enfocan la ficha correspondiente; la selección mantiene el foco en su control; Escape retorna a la divulgación de cuenta. La selección de estado usa una región dinámica cortés; el error del catálogo usa una alerta. La respuesta con movimiento reducido es inmediata y completa.

Objetivo de contraste: ≥4.5:1 para el texto del cuerpo y ≥3:1 para los límites y el foco de controles significativos. Ambos temas asignan el primer plano oscuro a #120b24, preservando la regla de contraste de producción. Las auditorías automatizadas complementan las comprobaciones de capturas renderizadas e interacción; no demuestran conformidad completa con tecnologías de asistencia, integración con el catálogo de producción ni autorización real de cuenta. La calidad de los anuncios para lectores de pantalla y el zoom del navegador del 200–400% no se probaron manualmente en esta delegación.

## 11. Criterios de aceptación visual y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | ≥1100px | normal | Aparecen cuatro fichas horizontales en orden de catálogo; cada una tiene el nombre y el precio en una columna izquierda de 248px y todas las herramientas a la derecha. |
| C-AC-02 | 640–1099px | normal | La comparación es una cuadrícula de 2×2 ordenada por filas, con listas de herramientas en una sola columna y sin desplazamiento horizontal de la página. |
| C-AC-03 | 390–639px | normal | Las cuatro fichas se apilan en orden; todas las herramientas y etiquetas de disponibilidad se ajustan dentro de los márgenes interiores de 20px. |
| C-AC-04 | Todos los admitidos | normal / seleccionado | No hay controles para mostrar u ocultar herramientas ni listas de herramientas contraídas. |
| C-AC-05 | Todos los admitidos | normal ES | Los precios son Gratis, 20.000, 45.000 y 70.000, y los precios de pago indican COP / mes; no aparece USD. |
| C-AC-06 | Todos los admitidos | normal EN | Enthusiast es Free; los precios de pago son 7, 14 y 25 USD / mes; no aparece COP. |
| C-AC-07 | Todos los admitidos | normal | Cada plan superior incluye visiblemente todas las herramientas de los niveles inferiores; cada una de las tres herramientas futuras tiene una etiqueta de no disponibilidad en ambos planes superiores. |
| C-AC-08 | Todos los admitidos | seleccionando / seleccionado | Al presionar cualquier plan se resalta exactamente una ficha y se anuncia su nombre para la comparación sin cambiar la identidad de la cuenta. |
| C-AC-09 | Todos los admitidos | seleccionado | Al volver a la comparación completa se conservan el resaltado de borde y texto elegidos y las cuatro listas completas. |
| C-AC-10 | Todos los admitidos | cargando | Aparecen cuatro fichas esqueleto y el estado de carga, sin valores de catálogo supuestos. |
| C-AC-11 | Todos los admitidos | vacío / error / sin conexión | Se muestran la explicación específica y Reintentar; Reintentar restaura el fixture normal simulado. |
| C-AC-12 | Todos los admitidos | puntos de entrada | El inicio de sesión y la divulgación de cuenta contienen exactamente un enlace cada uno con destino /planes. |
| C-AC-13 | 390 / 768 / 1024 / 1280px | normal | La vista sin sesión no tiene divulgación de cuenta; la vista con sesión tiene la misma divulgación compartida y no expone funciones del personal, funciones personalizadas ni claves de permisos en /planes. |
| C-AC-14 | Todos los admitidos | cualquier estado del catálogo | No se muestran acciones de compra, solicitud, contacto, registro, límite numérico ni asignación de plan a la cuenta. |
| C-AC-15 | Todos los admitidos | teclado | Tab muestra el foco visible, la activación nativa funciona y Escape cierra la divulgación de cuenta y restablece el foco. |
| C-AC-16 | Todos los admitidos | expresivo / reducido / estático | La estabilización y la respuesta al presionar la ficha se animan en modo expresivo; los modos reducido o estático mantienen el contenido estabilizado y la respuesta de selección sin movimiento. |
| C-AC-17 | Escritorio/tableta | entrada de acceso | El encabezado de acceso, el panel y el pie apilado comparten el eje hermano de 676px; el enlace agregado a Planes aparece después del formulario sin cambios. |

### Verificación real sin conexión

- Constructor real: APROBADO, HTML autocontenido de 547 KB y 2,031 archivos fuente empaquetados sin conexión desde el espacio de trabajo instalado. La entrada importa `mountMockup`, `useMockup` y `useMotionProfile`; sin alternativa ni instalación de paquetes.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass`.
- Ejecución de `audit_mockup.py`, requerida, contra este resultado específico de la revisión, anchos `1280,390,768,1024`: **288/288 renderizados, 7,456 mediciones de texto, 456 paradas de foco**; sin muestreo. El idioma predeterminado del navegador es inglés. Código de salida 0.
- Segunda ejecución de la misma auditoría con Playwright `Browser.new_page(locale="es-CO")`, los mismos cuatro anchos: **288/288 renderizados, 7,456 mediciones de texto, 456 paradas de foco**. Código de salida 0. Este contenedor solo cambia el idioma del navegador; no modifica la auditoría ni omite comprobaciones.
- Líneas de resultado de ambas auditorías reales: `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Prueba adicional sin conexión con Playwright: **240 aserciones APROBADAS** para ES/COP y EN/USD, selección de cada plan con y sin sesión, 17 filas de herramientas visibles, seis etiquetas de no disponibilidad, enlaces de entrada, retorno a la comparación completa con el resaltado, identidad de cuenta sin cambios, Escape y foco de cuenta, nueve anchos de ventana y comportamiento expresivo/estático. No se observaron solicitudes HTTP ni errores de página. Se ejecutó antes de la corrección final de apilamiento del pie y la fila de contexto, exclusiva del acceso; la auditoría final cubre esos cambios renderizados. No verifica autorización de producción.
- Evidencia del selector: APROBADA mediante la sonda EVIDENCE real de la herramienta de comparación en todas las vistas declaradas. Los 16 selectores coinciden con elementos visibles; los selectores de movimiento se animan o realizan una transición. La tipografía calculada del producto es Geist.
- Capturas inspeccionadas: ambas composiciones candidatas a 1280px; comparación y selección completas a 768px; selección a 390px en tema oscuro; comparación completa a 1280px en tema oscuro; acceso a 1280px en tema claro y entrada de cuenta a 1280px en tema oscuro. Muestran listas abiertas y legibles, geometría de las fichas y el armazón compartido del producto. Las capturas y los registros temporales están en `/tmp/planes-c-*`; son evidencia, no artefactos adicionales del proyecto.

Las auditorías iniciales señalaron seis problemas de alineación del eje de acceso y, luego, dos problemas residuales del pie. El encabezado y el pie se alinearon con el eje del formulario hermano y el pie se apiló; las dos auditorías finales por idioma indicadas arriba no detectan problemas. No se suprimieron comprobaciones ni se modificó producción o se parcheó el HTML generado.

## 12. Preguntas abiertas, supuestos e impacto

**Preguntas abiertas para el responsable: ninguna.** La ronda 13 resuelve explícitamente que la selección solo se usa para comparar. La decisión de dirección y aprobación del plan corresponden a David; este borrador no concede aprobación. El finalizador puede utilizar esta exploración específica de la revisión solo después del flujo de selección y aprobación del responsable.

Confirmado: dirección C; comportamiento público e informativo; cuatro listas completas; ES/COP y EN/USD; vista adicional solo de comparación; sin control de divulgación por plan; diseño legible específico para tabletas; contratos SP-1/SP-2 sin cambios. La selección en memoria y `?vista=seleccionar` son mecanismos de navegación propuestos dentro de esta dirección, no un comportamiento nuevo de cuenta. Al actualizar la página, el resaltado se restablece. El idioma inicial usa el idioma del navegador; el selector nativo permite mostrar ambos idiomas.

Los formularios estáticos de cuenta y de inicio de sesión ilustran solo la ubicación del enlace de entrada. La validación de contraseña, la autenticación real, los destinos del menú de cuenta y las operaciones del servicio de cuenta siguen siendo responsabilidad exacta del contrato SP-2. La integración con el catálogo de producción, la invariancia de permisos y el comportamiento en producción requieren T14.4; este fixture sin conexión no puede demostrarlos. No se ejecutaron pruebas, compilación ni lint de producción porque el alcance no incluye código de producción. La aceptación completa con lectores de pantalla y zoom queda pendiente de la revisión de implementación.
