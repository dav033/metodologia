---
name: Pliegues de consulta
contract_candidate: planes@v1
revision: r3
direction: c
status: draft
artifact_kind: exploration
ready: true
stale: false
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
source_behavior: planes@v1.r3.behavior.md
source_behavior_sha256: 3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239
chosen_thumbnail: planes@v1.r3.dir-c.html.candidate-1.html
---

# Pliegues de consulta — dirección C, r3

## 1. Identidad y trazabilidad

**Exploración preliminar, completa para que el propietario la compare; no es un contrato aprobado ni un insumo de implementación.** Esta revisión de la composición existente aborda la dirección C ya elegida por el propietario y los comentarios de las 14:19, `/tmp/REQ-021-planes-feedback-1.md`, y la aclaración de las 14:44. Revisa r2 sin cambiar la dirección elegida, la estructura, la navegación ni el movimiento; la única corrección de contenido restituye Catálogo en las cuatro listas acumulativas, como ya exigen la SPEC vigente y el borrador canónico. Los archivos canónicos, el historial, los planes, los contratos relacionados y los repositorios del proyecto permanecen intactos.

El alcance incluye `planes@v1.r3.behavior.md`, R17–R20 y la sección «Behavior — SP-14 extra view (round 13 answered)» de SPEC. La vista adicional solo permite seleccionar y resaltar planes para compararlos; no permite comprar, solicitar, registrarse, asignar cuentas, cambiar permisos ni establecer valores de límites. Todas las herramientas permanecen visibles. La ronda 13 ya fue respondida y no se vuelve a abrir aquí.

Evidencia del producto consultada en modo de solo lectura: `globals.css` de t12 y asesor; `layout.tsx` de t12, la página de inicio de sesión/LoginForm, CabeceraApp y MenuApp. Se inspeccionaron los archivos Markdown y HTML canónicos relacionados de cuentas-admin, taller-esenciales y proyectos. La **Parte de acceso** actual de cuentas-admin proporciona el encabezado, los controles nativos de idioma y cuenta, la navegación horizontal neutra, las hojas de trabajo redondeadas y el eje de acceso. La paleta de producción y las fuentes Geist prevalecen cuando difieren de los mapeos de tokens escritos en exploraciones HTML anteriores de proyectos relacionados. Todavía no existe un archivo de catálogo de planes de producción en los árboles de trabajo inspeccionados; el fixture se basa únicamente en el brief compartido. En producción se debe consultar el catálogo de SP-1, no copiar este fixture como una segunda fuente de datos.

Solo SP-14 consume `ui.contract=planes`, versión 1: T14.1 copia el contrato aprobado posteriormente, T14.2 implementa la comparación y selección, T14.3 agrega enlaces de entrada y T14.5 revisa. T14.4 consume la verificación de integración. En comparación con el comportamiento solicitado anteriormente, la vista de selección y el reajuste para tabletas requieren una adaptación de implementación (cambio incompatible de aspecto e interacción); los tokens y destinos de los enlaces de entrada son compatibles. La propiedad de los datos de SP-1 y el comportamiento de cuenta de SP-2 no cambian. Esta nota no redirige a los consumidores ni aprueba un contrato.

## 2. Propósito y usuarios

Las visitas públicas y las personas con sesión iniciada comparan cuatro planes acumulativos, sus precios y la disponibilidad de herramientas. Una consulta satisfactoria significa que cada plan se puede leer sin autenticación y sin listas contraídas. Una vista aparte permite elegir un resaltado para la comparación y volver a los cuatro planes. «Un administrador asigna el plan» explica la asignación de cuenta sin ofrecerla.

Los datos de cuenta neutrales son explícitamente de maqueta: Cuenta Entusiasta / cuenta Entusiasta, `entusiasta@prueba.local`, Empresa de ejemplo. Los formularios de acceso a la cuenta solo reproducen el contexto del elemento del mismo nivel; al enviarlos se muestra un aviso de límite de la maqueta y no se transmite ningún dato. Esto no verifica el servicio de cuenta.

## 3. Enfoque, jerarquía y miniatura elegida

El producto existente incorpora **hojas de consulta abiertas**, no una página de marketing. En cada hoja de escritorio, el nombre del plan y el precio mensual aparecen en el lado izquierdo, y todas sus herramientas en el derecho. «Pliegues» describe el gesto con que se asienta la hoja; nunca significa una sección de herramientas contraída. La vista de selección adicional reorganiza el mismo contenido en hojas pares dispuestas en una cuadrícula de dos por dos, con un control de comparación que se puede pulsar. Ningún dato factual del catálogo se puede editar.

Se crearon dos archivos HTML de miniaturas específicos de esta revisión **antes** del TSX completo y se inspeccionaron como capturas en memoria a 1280px. **Se eligió la opción 1:** las hojas horizontales muestran los encabezados de los cuatro planes en un recorrido vertical compacto y alinean sus nombres con el área de herramientas. La opción 2 también usa hojas en una cuadrícula de dos por dos en escritorio; se conserva como evidencia visual, pero prescinde de ese eje de comparación. La versión completa usa la opción 1 para comparar y la disposición de hojas pares para la vista de selección, que es claramente independiente.

| Eje | Expresión renderizada |
|---|---|
| Concepto | Pulsar o seleccionar un resaltado comparativo directamente en las hojas de planes abiertas; los datos del catálogo permanecen en modo de solo lectura. |
| Diseño | En ≥1100px, cuatro hojas de ancho completo con columnas de identidad de 248px y listas en dos columnas. La comparación en tabletas y la selección en escritorio y tabletas usan hojas en una cuadrícula de dos por dos; en teléfonos se usa una sola columna. |
| Navegación | Encabezado y menú desplegable de cuenta existentes; enlaces neutros Comparar / Seleccionar; cuatro anclas a planes en la comparación; regreso explícito a la comparación completa y a la superficie de entrada original. |
| Tipografía | Geist Sans y Geist Mono existentes, a partir de los archivos WOFF2 locales de producción. H1 de 24px, encabezados de planes de 20px, precios de 22px con cifras tabulares, herramientas de 14px, contexto y disponibilidad de 12–14px. |
| Densidad | Hojas abiertas que se ajustan al contenido, con márgenes internos de 28px en escritorio, 24px en tabletas y 20px en teléfonos, separaciones de 16px, y paneles de 32px y formas de píldora existentes. Las listas en tabletas muestran una columna de texto completa por plan. |
| Componentes | Button, Input y Skeleton de shadcn/Base UI instalados; selectores nativos y menú desplegable de cuenta; enlaces, artículos y listas semánticos; marcas de verificación y flechas de Lucide. Sin alternativa de otro kit de herramientas. |
| Color | Tokens exactos de Pictures en modo claro y oscuro; elementos de interfaz neutros, color de acento en acciones y selección, y color de aviso en etiquetas de funciones no disponibles. Sin reemplazar la paleta, la fuente ni la identidad visual. |
| Movimiento | Apertura y asentamiento de 440ms, desplazamientos entre hojas de 45ms, curva ease-out existente, efecto de resorte interrumpible al pulsar y sello de etiqueta seleccionada; controles de 180ms. Los modos natural y sutil reducen la duración; los modos reducido y estático conservan todo el contenido sin desplazamientos. |

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

1. Sin sesión iniciada: elegir la vista de acceso → activar su enlace Planes → leer las cuatro hojas → entrar en Seleccionar para comparar → pulsar un plan → volver a la comparación completa con esa hoja resaltada → volver al acceso.
2. Con sesión iniciada: elegir la vista de entrada del menú de cuenta → seguir Planes → comparar y seleccionar como antes → Volver lleva a Mi cuenta. El fixture de cuenta mantiene Cuenta Entusiasta incluso cuando se resalta Master Designer.
3. Inglés: si el idioma inicial del navegador empieza por `en`, se selecciona inglés; con cualquier otro idioma inicial, se usa español. Idioma cambia el mismo fixture de catálogo entre ES/COP y EN/USD y conserva el resaltado de la comparación. Gratis se muestra como Free y Entusiasta como Enthusiast. La resolución del idioma en producción se integra con SP-2; no existe un selector de moneda alternativo.
4. Carga, catálogo vacío, error o falta de conexión: usar el selector Estado visible. La carga muestra hojas esqueleto y un aviso de carga. Los estados vacío, error, sin conexión e incompleto muestran una explicación específica y la opción Reintentar; en la simulación, Reintentar restaura los datos normales del fixture. No se presenta un catálogo parcial inventado como una comparación válida.

## 7. Vistas y contenido del catálogo

| Opción nativa de Vista | Contexto del producto | Contenido |
|---|---|---|
| `compare` | /planes, sin sesión iniciada | Cuatro hojas abiertas completas, anclas de comparación, regreso al inicio de sesión, sin menú de cuenta. |
| `compare-signed` | /planes, con sesión iniciada | Las mismas hojas más el menú desplegable de cuenta existente y el contexto de regreso. |
| `select` | Vista adicional, sin sesión iniciada | Las cuatro listas completas, un resaltado seleccionable por hoja y regreso a la comparación completa. |
| `select-signed` | Vista adicional, con sesión iniciada | La misma selección informativa; la identidad de la cuenta no cambia. |
| `login` | Contexto de entrada de acceso de SP-2 | Eje de acceso existente más exactamente un enlace a Planes. |
| `menu` | Contexto de entrada de Mi cuenta de SP-2 | Patrón existente del menú de cuenta más exactamente una opción Planes; el formulario subyacente es un contexto ilustrativo de un proyecto relacionado y está marcado dentro del alcance. |

Orden y precios: Entusiasta/Enthusiast Gratis/Free; Designer 20.000 COP / mes o 7 USD / mes; Designer Plus 45.000 COP / mes o 14 USD / mes; Master Designer 70.000 COP / mes o 25 USD / mes. Se muestra exactamente un idioma y una moneda a la vez. Gratis no tiene un precio cero que pueda inducir a error.

Las herramientas se repiten en su totalidad para comunicar su inclusión acumulativa: Entusiasta muestra Chat con límites, Contador de globos y Catálogo; Designer muestra Chat con límites más altos, el mismo contador y Catálogo. Designer Plus agrega Calculadora de costos, Chat extendido, Detección de estructuras y Detección avanzada de globos. Las tres últimas herramientas de esta lista (chat extendido, detección de estructuras y detección avanzada de globos) llevan el texto explícito «aún no disponible» / «not available yet». Master Designer repite esa lista y agrega Taller 3D, que incluye el explorador de decoraciones prediseñadas sin una línea separada para el explorador. Hay 21 filas de herramientas y seis etiquetas de no disponible entre las cuatro hojas. La disponibilidad sigue el brief compartido actual; el historial incoherente de versiones anteriores de SPEC no se usa como una segunda fuente de autoridad. La sección de planes no muestra límites numéricos de chat, roles de personal, roles personalizados, claves de permisos, afirmaciones de marketing ni controles para modificar cuentas.

## 8. Estados

| Estado | Efecto renderizado / recuperación |
|---|---|
| Normal | Fixture completo de cuatro planes; en un documento nuevo no se resalta ninguno inicialmente. Un resaltado elegido antes en memoria se conserva durante la navegación. |
| Plan resaltado | Permite ver un resaltado ilustrativo de Designer Plus sin interacción; una selección real tiene prioridad. Es una respuesta visual de comparación, no la confirmación de un plan asignado. |
| Cargando | Cuatro hojas esqueleto, `aria-busy` y aviso de carga. Sin precios estimados ni controles de selección interactivos. |
| Catálogo vacío | «No hay planes disponibles» / «No plans available», indicaciones breves para reintentar y opción Reintentar. No se inventa un nivel gratuito. |
| Error | Alerta «No se pudieron cargar los planes» / «Could not load plans», indicaciones para reintentar y opción Reintentar. |
| Datos incompletos | Tratamiento de error con «No se muestran datos sin confirmar. Reintenta.» / «Unconfirmed data is not shown. Try again.» No se representa un catálogo parcial como completo; Reintentar restaura el fixture simulado normal. |
| Sin conexión | «Sin conexión» / «Offline», indicaciones para reconectarse o recargar y opción Reintentar. No se anuncian precios desactualizados como vigentes. |

El selector de siete estados se aplica a las vistas del catálogo. Las capturas de entrada de cuenta e inicio de sesión conservan sus formularios normales porque sus estados de carga, error y validación, así como los permisos, pertenecen a SP-2 y aquí no se redefinen. No aplican a SP-14: acceso denegado por permisos (página pública), confirmación de cambio de cuenta, compra pendiente, validación de registro y confirmación de acciones destructivas. Las herramientas no disponibles son texto informativo, no botones desactivados para adquirirlas. El estado de datos incompletos, que se puede inspeccionar explícitamente, usa el tratamiento de error; nunca se presentan precios desactualizados como vigentes. No hay modo de datos en caché.

## 9. Comportamiento adaptable

| Ancho | Comparación completa | Vista de selección adicional |
|---|---|---|
| 320–639px | Una columna, listas en una columna, márgenes externos e internos de las hojas de 20px; las anclas de planes se ajustan en pares; los controles del encabezado ocupan una segunda línea; el pie de página se apila. | Una columna; selección debajo del nombre y el precio; acción de regreso de ancho completo; todas las etiquetas de herramientas se ajustan. |
| 640–1099px | **Regla explícita para tabletas:** hojas en cuadrícula de 2×2 y orden de catálogo por filas; márgenes externos e internos de las hojas de 24px; nombre y precio encima de una lista de ancho completo en una columna. Sin cuatro columnas de escritorio comprimidas, carrusel ni tabla horizontal. | La misma cuadrícula de 2×2; selección debajo de la identidad; las listas de herramientas nunca se contraen. El encabezado se ajusta cuando hace falta. |
| ≥1100px | Cuatro hojas horizontales de ancho completo; identidad de 248px, área restante con lista de herramientas en dos columnas, márgenes internos de las hojas de 28px y externos de 40px, ancho máximo de la aplicación de 1520px. | Hojas pares en una cuadrícula de dos por dos, con listas de herramientas en una columna y controles de comparación junto a la identidad cuando hay espacio suficiente. |

Los formularios de entrada conservan el eje de formularios de 676px externos y 620px internos del proyecto relacionado, márgenes internos de 28px en escritorio y 20px en teléfonos, y el encabezado y el pie apilado alineados con ese eje. Las hojas no tienen una altura fija ni recortan el texto de las herramientas. El contorno de selección no cambia el relleno ni la geometría de las hojas. Los cambios de selección conservan el foco del botón en lugar de volver a montar las hojas. El orden de lectura sigue el orden del DOM en todos los puntos de quiebre. El reajuste se probó a 320, 390, 639, 640, 768, 820, 1024, 1099, 1100 y 1280px.

## 10. Objetivos de accesibilidad y límites de la evidencia

Objetivo WCAG 2.2 AA: encabezados, artículos, listas y navegación semánticos; enlaces, selectores y divulgación nativos; contorno de foco explícito de 3px en acento con desplazamiento de 4px; controles de ≥44px; estado seleccionado indicado mediante texto, marca o `aria-pressed`, no solo mediante color. El estado de no disponibilidad es texto literal asociado a la etiqueta de la herramienta. Tab/Enter/Space operan los controles; al cambiar de vista, el foco pasa a H1; los enlaces hash enfocan la ficha correspondiente; la selección mantiene el foco en su control; Escape retorna a la divulgación de cuenta. La selección de estado usa una región dinámica cortés; el error del catálogo usa una alerta. La respuesta con movimiento reducido es inmediata y completa.

Objetivo de contraste: ≥4.5:1 para el texto del cuerpo y ≥3:1 para los límites y el foco de controles significativos. Ambos temas asignan el primer plano oscuro a #120b24, preservando la regla de contraste de producción. Las auditorías automatizadas complementan las comprobaciones de capturas renderizadas e interacción; no demuestran conformidad completa con tecnologías de asistencia, integración con el catálogo de producción ni autorización real de cuenta. La calidad de los anuncios para lectores de pantalla y el zoom del navegador del 200–400% no se probaron manualmente en esta delegación.

## 11. Criterios de aceptación visual y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | ≥1100px | normal | Aparecen cuatro hojas horizontales en el orden del catálogo; cada una tiene el nombre y el precio en una columna izquierda de 248px y todas las herramientas a la derecha. |
| C-AC-02 | 640–1099px | normal | La comparación aparece en una cuadrícula de 2×2 ordenada por filas, con listas de herramientas en una columna y sin desplazamiento horizontal de la página. |
| C-AC-03 | 320–639px | normal | Las cuatro hojas se apilan en orden; todas las herramientas y etiquetas de disponibilidad se ajustan dentro de los márgenes internos de 20px. |
| C-AC-04 | Todos los compatibles | normal / seleccionado | No existe ningún control para mostrar u ocultar herramientas ni listas de herramientas contraídas. |
| C-AC-05 | Todos los compatibles | normal ES | Los precios son Gratis, 20.000, 45.000 y 70.000; los precios de pago indican COP / mes; no aparece USD. |
| C-AC-06 | Todos los compatibles | normal EN | Enthusiast aparece como Free; los precios de pago son 7, 14 y 25 USD / month; no aparece COP. |
| C-AC-07 | Todos los compatibles | normal | Cada plan de nivel superior incluye visiblemente todas las herramientas de los niveles inferiores; cada una de las tres herramientas futuras tiene una etiqueta de no disponible en ambos planes superiores. |
| C-AC-08 | Todos los compatibles | seleccionando / seleccionado | Al pulsar cualquier plan, se resalta exactamente una hoja y se anuncia su nombre para la comparación sin cambiar la identidad de la cuenta. |
| C-AC-09 | Todos los compatibles | seleccionado | Al volver a la comparación completa se conservan el borde y el texto resaltados del plan elegido y las cuatro listas completas. |
| C-AC-10 | Todos los compatibles | cargando | Aparecen cuatro hojas esqueleto y el aviso de carga, sin valores de catálogo estimados. |
| C-AC-11 | Todos los compatibles | vacío / error / sin conexión / parcial | Se muestran una explicación específica y la opción Reintentar; Reintentar restaura el fixture simulado normal. |
| C-AC-12 | Todos los compatibles | puntos de entrada | El inicio de sesión y el menú desplegable de cuenta contienen cada uno exactamente un enlace con destino /planes. |
| C-AC-13 | 390 / 768 / 1024 / 1280px | normal | Sin sesión iniciada no aparece el menú de cuenta; con sesión iniciada aparece el mismo menú compartido y no se exponen en /planes roles de personal o personalizados ni claves de permisos. |
| C-AC-14 | Todos los compatibles | cualquier estado del catálogo | No se muestra ninguna acción para comprar, solicitar, contactar, registrarse, establecer límites numéricos o asignar un plan a una cuenta. |
| C-AC-15 | Todos los compatibles | teclado | Tab muestra un indicador de foco visible, la activación nativa funciona y Escape cierra el menú desplegable de cuenta y devuelve el foco. |
| C-AC-16 | Todos los compatibles | expresivo / reducido / estático | El asentamiento de las hojas y la respuesta al pulsarlas se animan en el modo expresivo; los modos reducido y estático conservan el contenido asentado y la respuesta visual de selección sin movimiento. |
| C-AC-17 | Escritorio/tableta | entrada de acceso | El encabezado de acceso, el panel y el pie apilado comparten el eje de 676px del proyecto relacionado; el enlace Planes agregado aparece después del formulario, que permanece sin cambios. |

### Verificación sin conexión actual

La entrada se compiló con el comando absoluto `bitacora.py components mockup build` contra `planes@v1.r3.dir-c.tsx`; el `planes@v1.r3.dir-c.html` resultante contiene React/Base UI/Motion, CSS y datos WOFF2 locales de Geist integrados (547 KB; 2,031 archivos fuente empaquetados). No se instaló ningún paquete ni se usó una implementación HTML alternativa, un recurso externo o una solicitud de red. Los HTML de las miniaturas son deliberadamente bocetos visuales pequeños, no implementaciones completas alternativas.

- `contrast.py`: **contraste: 158 pares comprobados en temas claro y oscuro; todos aprobados**.
- Auditoría final requerida: **336/336 renderizados**, 8,576 mediciones de texto y 528 paradas de foco en 1280/390/768/1024px, ambos temas; sin advertencias. **RESULTADO: APROBADO — sin problemas de contraste, contenido no textual, foco, alineación, relleno ni desbordamiento**.
- Auditoría en inglés: **336/336 renderizados**, 8,576 mediciones de texto y 528 paradas de foco con la configuración regional del navegador `en-US`, en los mismos cuatro anchos y ambos temas. Se invocó el mismo módulo de auditoría sin modificar, con `Browser.new_page` configurado en memoria para esa configuración regional; sus sondeos y umbrales no cambiaron. **RESULTADO: APROBADO — sin problemas de contraste, contenido no textual, foco, alineación, relleno ni desbordamiento**.
- Playwright complementario: **160 casos adaptables aprobados** (10 anchos × 2 temas × 2 idiomas × 4 vistas del catálogo); cada vista tiene cuatro planes, 21 filas de herramientas y seis etiquetas de disponibilidad; sin desbordamiento horizontal; en tableta se calculan exactamente dos columnas.
- Diez grupos de interacción aprobados: las cuatro selecciones conservan el foco del botón y exactamente un estado presionado; los datos de prueba de la cuenta Entusiasta nunca cambian; al volver se conservan el resaltado de comparación de Master Designer y las cuatro listas; Escape en la cuenta devuelve el foco; ambos enlaces de entrada existentes llevan a `/planes`; Reintentar restaura todos los datos de prueba ante estados vacío, de error, sin conexión o incompleto. No se observaron excepciones de página ni solicitudes HTTP(S).
- Los selectores de eje se resuelven en las vistas declaradas. `.plan-sheet` usa realmente la animación `unfold` en el modo expresivo y ninguna animación en el modo estático. Se pueden inspeccionar los selectores nativos, ambos temas y los siete estados. La auditoría del kit también comprueba el movimiento reducido y el desplazamiento del diseño durante la carga.
- Capturas de pantalla en memoria inspeccionadas: ambas composiciones candidatas a 1280px; la comparación compilada a 1280px en ES claro y EN oscuro, la comparación a 768px en ES claro y la selección a 390px en EN oscuro. No se crearon archivos de captura adicionales.

Estas comprobaciones corresponden al artefacto de planificación, no al lint, los tipos o la compilación de producción, la conexión real al catálogo, el enrutamiento de retorno del navegador, los permisos de cuenta, los lectores de pantalla ni la conformidad completa con WCAG o el zoom. Los repositorios de producción se consultaron en modo de solo lectura. No se modificó ningún contrato canónico, HTML canónico, SPEC, PLAN, diseño hermano ni otro archivo de bitácora. Solo se escribe el RESULT.json de delegación exigido explícitamente, fuera de estos seis archivos de exploración.

## 12. Preguntas abiertas, supuestos e impacto

**Preguntas abiertas para el propietario: ninguna.** La ronda 13 resuelve explícitamente que la selección solo se usa para comparar. La aprobación de la dirección y del plan sigue correspondiendo a David; este borrador no otorga ninguna aprobación. El finalizador solo puede consumir esta exploración específica de la revisión después del flujo de selección/aprobación del propietario.

Confirmado: dirección C; comportamiento público e informativo; cuatro listas completas; ES/COP y EN/USD; vista adicional solo para comparar; sin control de divulgación por plan; diseño legible específico para tabletas; contratos SP-1/SP-2 sin cambios. La selección en memoria y `?vista=seleccionar` son mecanismos de navegación propuestos dentro de esta dirección, no un comportamiento nuevo de cuenta. Al actualizar la página, se restablece el resaltado. El idioma inicial usa el idioma del navegador; el selector nativo permite ver ambos idiomas.

Los formularios estáticos de cuenta e inicio de sesión solo ilustran la ubicación de los enlaces de entrada. SP-2 sigue modificado para su actualización separada solicitada por el propietario; esta exploración no lo resuelve ni lo aprueba. La validación de contraseñas, la autenticación real, los destinos del menú de cuenta y las operaciones del servicio de cuenta siguen siendo responsabilidad del contrato SP-2 exacto. La integración con el catálogo de producción, la invariancia de permisos y el comportamiento en el entorno desplegado requieren T14.4; esta prueba sin conexión no puede demostrarlos. No se ejecutaron pruebas, compilación ni lint de producción porque el alcance no incluye código de producción. La aceptación completa con lectores de pantalla y zoom queda pendiente de la revisión de implementación.
