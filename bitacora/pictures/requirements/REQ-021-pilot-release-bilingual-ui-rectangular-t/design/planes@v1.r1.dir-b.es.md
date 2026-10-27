---
contract: planes
version: 1
status: draft
kind: exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
direction: b
revision: 1
name: Índice y paneles
owner: David
author: Designer
date: 2026-10-27
---

# Índice y paneles — dirección espacial B

Exploración **completa en borrador**, no es un contrato aprobado ni una instrucción de implementación. El propietario no ha seleccionado esta dirección. Solo se producen los seis archivos de diseño asignados y específicos de la revisión. No se escribe ningún `planes@v1.md` / `planes@v1.html` canónico, repositorio, plan, contrato compartido ni otro registro del proyecto.

## Enfoque y superficie existente

La pregunta es «¿Qué incluye cada plan de acceso y cuál es su precio mensual?». Un documento continuo la responde sin controles de compra, solicitud, contacto, registro ni cambio de plan.

Se conservan el encabezado existente de anillos y puntos de Pictures/Sempertex, el control de idioma, el desplegable de cuenta, el encabezado de tarea de 24px, el papel de trabajo redondeado, el eje del formulario y el pie de página del elemento hermano **Parte de acceso** seleccionado. El área modificada es una sola hoja con un **índice de precios y un documento de herramientas**, que reutiliza la composición de lista de roles/editor del elemento hermano en lugar de una cuadrícula de tarjetas promocionales. La página pública no tiene menú de cuenta. La vista de cuenta activa usa como ejemplo una cuenta Entusiasta; no añade contenido de personal, roles personalizados ni claves de permisos a la sección.

Los cuatro precios de referencia permanecen en el orden del catálogo, en el lado izquierdo del contenido de escritorio. El lado derecho contiene las cuatro listas completas de herramientas, separadas por líneas; ningún beneficio queda oculto tras la selección de un plan. El índice de precios permanece disponible al desplazarse. En un teléfono, el mismo índice se convierte en cuatro filas compactas sobre el documento completo de herramientas. Esta es una nueva ruta `/planes` dentro de la estructura existente del producto, no una nueva identidad ni una página de inicio.

Ambas superficies de entrada siguen siendo reconocibles: el formulario de inicio de sesión conserva su explicación de acceso solo por invitación, los campos de correo electrónico y contraseña, la acción de acceso y las indicaciones para restablecimiento por parte del administrador; el menú de cuenta conserva la identidad, Mi cuenta y cerrar sesión. Cada uno incorpora exactamente un enlace **Planes / Planes**. La vista de cuenta es un ejemplo neutro de origen simulado, no funcionalidad adicional de cuenta de SP-14.

## Dos miniaturas y la elección

- **Elegida: `planes@v1.r1.dir-b.html.candidate-1.html`.** Un índice lateral de precios junto a cada lista completa de herramientas. Muestra de inmediato los nombres y precios de los cuatro planes y permite leer juntos los conjuntos acumulativos de herramientas.
- `planes@v1.r1.dir-b.html.candidate-2.html`. Una franja superior con los cuatro precios sobre un inspector enfocado. Es una composición espacial viable, pero oculta las demás listas de herramientas detrás de la selección. Es menos adecuada para esta tarea explícita de comparación y no se desarrolló.

Las dos composiciones independientes se crearon antes del TSX completo y del HTML generado. La miniatura 1 es la fuente de diseño de la dirección completa; el artefacto completo, no las miniaturas, contiene el comportamiento y el movimiento auditados.

## Ocho ejes

| Eje | Dirección observable |
|---|---|
| concept | Un documento continuo de planes con un índice espacial de precios: comparar los cuatro precios mensuales mientras se leen todas las listas acumulativas de herramientas. |
| layout | Una hoja redondeada compartida, un índice fijo de planes de 264px a la izquierda y secciones de herramientas separadas por líneas a la derecha; una columna por debajo de 761px, con las cuatro filas de precios antes del documento de herramientas. |
| navigation | Cuatro anclas reales en la página, en el orden del catálogo; la ubicación activa sigue el desplazamiento, las anclas enfocan el encabezado correspondiente y los enlaces de retorno restauran el foco de origen. Los controles existentes de inicio de sesión y cuenta incorporan cada uno un enlace a Planes. |
| typography | Solo las familias Geist Sans y Geist Mono ya integradas; título de página de 24px, nombres de sección de 20px, precios de 24px en escritorio / 20px en teléfono, herramientas de 14px, disponibilidad y etiquetas acumulativas de 12px. |
| density | Un índice despejado con filas de 100px en escritorio / 72px en teléfono, junto a herramientas compactas en dos columnas a partir de 1101px; herramientas en una columna en anchos menores. Sin carrusel de funciones ni beneficios contraídos. |
| components | Button, Input y Skeleton de shadcn instalados; se conservan los detalles de cuenta nativos y el selector de idioma; el índice de anclas personalizado y las secciones separadas por líneas recomponen el vocabulario de lista de roles/editor del elemento hermano. |
| colour | Se conservan los tokens claros/oscuros de Pictures. El relleno secundario neutro indica la posición de lectura; el color de acento de origen aparece en los enlaces y el foco. La disponibilidad sigue indicándose con texto tenue explícito y un icono de contorno diferenciado. |
| motion | Resortes espaciales expresivos desplazan el marcador del índice entre las anclas; el documento se asienta desde -8px y las secciones desde 26px con intervalos de 63ms; las líneas se extienden desde un ancho del 80% durante 500ms. Las flechas al pasar el cursor se desplazan 4px durante 180ms; el movimiento reducido y el modo estático conservan todos los destinos y la disposición final, sin desplazamiento animado. |

El JSON contiene evidencia de selectores activos para disposición, navegación, tipografía y movimiento. Se encontró cada selector en la vista pública renderizada por defecto. La evidencia de movimiento se midió con el movimiento activado; no se infirió a partir de nombres de clase.

## Tokens existentes, tipografía y componentes reales

`src/app/globals.css` de producción es la fuente de color. Se leyeron los contratos y los archivos HTML incluidos de los elementos hermanos accounts/proyectos/taller; la dirección de accounts seleccionada rige los elementos compartidos de la interfaz que no pertenecen al taller. El generador sin conexión integra los archivos binarios de fuentes de producción disponibles en la compilación Next de t12, con las mismas familias **Geist Sans / Geist Mono**. No se obtiene ningún recurso. No se propone una paleta, familia tipográfica ni identidad nuevas.

| Fuente del proyecto | Función en la maqueta / kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | `#faf9fc` / `#0b0c10` |
| `--superficie` | tarjeta, ventana emergente | `#ffffff` / `#16181f` |
| `--texto` | primer plano y primeros planos de superficies | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | primer plano atenuado | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | secundario, atenuado, marcador neutro del índice | `#efe9f8` / `#242733` |
| `--superficie-suave` | índice al pasar el cursor | `#faf8fd` / `#1c1e26` |
| `--acento` / `--sobre-acento` | primario / primer plano primario | `#6d3fe0` / blanco; `#9479ff` / `#120b24` |
| `--borde`, `--borde-suave` | límites decorativos / líneas | `#e3daef`, `#efe9f8` / `#383c48`, `#2a2d38` |
| `--texto-tenue` | borde de control significativo (alias accesible del elemento hermano) | `#766c85` / `#8a91a0` |
| `--error`, `--error-suave` | aviso de error de cuenta | `#b23a45`, `#ffeaec` / `#ff979f`, `#43252a` |
| `--sombra` | solo desplegable flotante de cuenta | sombra de origen existente en cada tema |

Los demás roles semánticos conservan la asignación de accounts a los valores existentes de éxito/advertencia/error/acento. El color de origen se asigna una sola vez por tema; los bordes decorativos no son el único borde identificador de los controles de entrada. Se conserva el vocabulario compartido de formas seleccionadas: panel de 32px, inserto de 24px, campo de 18px y píldora de 999px. El relleno de la estructura es de 40px en escritorio, 28px en ancho intermedio y 20px en teléfono; el relleno del papel es de 28px / 20px. El título de página es de 24px, los nombres de sección de 20px, el texto de herramientas de 14px y el texto complementario de 12–13px. Las unidades monetarias en teléfono son de 11px. Los números usan cifras tabulares.

| Componente / estado real | Importación o composición personalizada fiel |
|---|---|
| `shadcn:button default / outline default, hover, focus, disabled, pending` | `@/components/ui/button`; composición existente de acción en forma de píldora |
| `shadcn:input email / password default, focus, disabled, validation` | `@/components/ui/input`; vocabulario sin cambios del ejemplo de cuenta/inicio de sesión |
| `shadcn:skeleton plan-index / tools loading` | `@/components/ui/skeleton` |
| `native:select language ES / EN` | Etiqueta visible asociada; control existente del encabezado |
| `native:details account closed / open` | Desplegable no modal existente; sin menú ARIA inventado |
| `custom:plan-index anchor normal / current / hover / focus` | `.plan-index`, `.index-item`, anclas reales con `aria-current="location"` |
| `custom:plan-document cumulative normal` | Cuatro secciones semánticas, encabezados y listas; `.plan-document`, `.plan-section` |
| `motion:spatial-marker / section / rule` | `motion/react`, marcador compartido y transiciones escaladas según el perfil |

En tiempo de ejecución se importan `mountMockup` / `useMockup` de `@kit/mockup` y `useMotionProfile` de `@kit/motion`. Se usaron componentes reales instalados; no hay fragmentos alternativos, instalación de paquetes ni solicitudes a recursos externos.

## Navegación, información y datos

### Vistas

| Valor nativo de `view` | Superficie / comportamiento de entrada |
|---|---|
| `planes-publico` | `/planes`, con sesión cerrada; cuatro planes; sin menú de cuenta; retorno a `/login` |
| `planes-cuenta` | El mismo `/planes`, con sesión iniciada; los mismos datos de planes; con menú de cuenta; el ejemplo de origen es `/cuenta` |
| `login` | Composición de inicio de sesión seleccionada con exactamente un enlace añadido a `/planes` |
| `cuenta` | Composición seleccionada de cuenta propia, ejemplo representativo; el menú de cuenta tiene exactamente una entrada a `/planes` |

El control de idioma sigue inicialmente el idioma del navegador: español → COP, inglés → USD; luego, al cambiar entre ES/EN, se actualizan juntos todos los nombres, precios y herramientas de los planes. El nombre en inglés de Entusiasta es **Enthusiast**. Gratis se mantiene como **Gratis / Gratis**, sin importe. En el documento de planes no aparecen monedas simultáneas, límites numéricos de chat, contadores, controles de asignación de planes, roles de personal o personalizados ni claves de permisos.

Todos los nombres, precios, herramientas y estados de disponibilidad mostrados provienen de un único ejemplo explícito de datos. Los precios son los exactos del requisito: 20,000 / 45,000 / 70,000 COP y 7 / 14 / 25 USD al mes. La ruta de catálogo de producción `src/lib/planes/catalogo.ts` aún no existe en los árboles de trabajo inspeccionados; producción debe reemplazar este ejemplo con `plan-catalogue@1`, sin otro catálogo propiedad de la página. Esta exploración no verifica la propagación del catálogo ni la autorización.

Cada sección enumera el conjunto completo de herramientas que ofrece el plan. La redacción sobre límites más altos de Designer reemplaza el texto básico de chat, en lugar de afirmar que hay dos chats utilizables distintos. Designer Plus y Master Designer repiten cada uno las líneas no disponibles **Chat ampliado / Chat ampliado**, **Detección de estructuras / Detección de estructuras** y **Detección avanzada de globos / Detección avanzada de globos**, cada una con **aún no disponible / aún no disponible**. La calculadora está disponible con Plus y Master. Master solo añade la línea **Taller 3D / Taller 3D** para todo el editor, incluido el explorador de decoraciones; no hay un beneficio separado para el explorador. La línea base **Catálogo / Catálogo** sigue las concesiones de acceso base de SPEC y se identifica abajo como una pregunta para el propietario.

Al hacer clic en un ancla del índice, la página se desplaza hasta el encabezado correspondiente y le da foco. Todas las secciones permanecen renderizadas. El desplazamiento actualiza la ubicación activa independientemente del acceso a la cuenta. Un ancla de plan sirve para navegar, nunca para seleccionar un derecho de acceso. La tecla Tab permite llegar a cada enlace; Enter lo activa. El retorno restaura el foco en el enlace Planes del inicio de sesión o en el desplegable de cuenta. En producción, se conserva la página de origen real y segura del mismo dominio al entrar desde el menú de cuenta; `/cuenta` es el ejemplo de origen de esta maqueta. La alternativa directa para la entrada con sesión iniciada sigue siendo una pregunta explícita.

### Estados

El selector nativo visible `state` permite elegir `normal`, `cargando`, `vacio` y `error`. Los controles nativos `view`, `theme` y `motion` conservan las etiquetas del tiempo de ejecución **Vista, Estado, Tema, Movimiento** y **Mockup**. No hay diálogo y, por lo tanto, no hay selector `scene`.

| Estado | Comportamiento de la sección de planes / recuperación |
|---|---|
| normal | Los cuatro precios ordenados y todas las listas de herramientas; lectura correcta, sin estado de éxito de mutación |
| cargando | Marcadores de carga del índice/herramientas con las formas correspondientes y estado de carga localizado; `aria-busy`; sin precios supuestos |
| vacio | Mensaje explícito «No hay planes disponibles.» / «No hay planes disponibles.» y opción Reintentar; nunca es una comparación válida con cero planes |
| error | Rechazo localizado al cargar el catálogo y opción Reintentar; no se presentan niveles desactualizados o incompletos como autoritativos |

Reintentar vuelve únicamente al ejemplo normal de datos; no hace ninguna solicitud. Las respuestas de catálogo vacías, parciales, no válidas o sin conexión deben fallar de forma cerrada durante la implementación, sin fingir que hay menos planes en el catálogo. Un catálogo incompleto se muestra como error. «Éxito» significa una lectura completa y correcta, así que no es útil una pantalla de confirmación aparte. Los estados de compra, solicitud, asignación, permiso denegado, cuota, límite numérico y contacto no corresponden. La ruta pública no requiere permisos. Los formularios de inicio de sesión y cuenta propia son ejemplos simulados del elemento hermano; SP-2 sigue siendo responsable de su comportamiento.

## Interacción adaptable y movimiento

- **1101–1519px:** índice de precios fijo de 264px, separación de 40px con el divisor y documento flexible con herramientas en dos columnas. Los cuatro nombres y precios del índice permanecen juntos. A partir de 1520px, el índice pasa a 288px y la separación a 48px, dentro del límite existente de 1520px para el contenedor.
- **761–1100px:** índice fijo de 232px, separación de 28px y herramientas en una columna. Los controles del encabezado se ajustan usando el mismo comportamiento de los elementos hermanos.
- **Hasta 760px:** relleno exterior y del papel de 20px, índice no fijo con cuatro filas de al menos 72px y precios alineados a la derecha, seguido del documento de herramientas en una columna. Sin franja horizontal, controles que solo funcionan al deslizar, plan oculto ni inspector lateral. La identidad de la cuenta oculta el sufijo de rol en línea, como en la vista hermana, y lo conserva dentro del desplegable.
- Los anchos medidos son **390, 768 y 1280px**. Estas comprobaciones de la maqueta no acreditan el zoom completo del navegador, la lectura con lector de pantalla ni la representación en producción.

El detalle distintivo de esta propuesta es un **marcador de lectura neutro compartido** que se desplaza entre las entradas del índice a medida que la persona lee el documento. El movimiento no implica que se haya elegido o asignado un plan. El papel completo se estabiliza desde -8px; cuatro secciones se estabilizan horizontalmente desde 26px en el perfil expresivo, con intervalos escalonados de 63ms. La rigidez del resorte es 220, la amortiguación 16 y la masa .9, según `useMotionProfile`; los perfiles natural/sutil usan sus resortes configurados y distancias menores. Las líneas de sección se extienden del 80% al ancho completo en 500/300/160ms. Los controles repetidos usan la temporización de origen de 180/140/100ms y la aceleración espacial `cubic-bezier(.22,1,.36,1)`; las flechas se desplazan 4px al pasar el cursor. El contenido sigue siendo legible durante el movimiento.

La preferencia de movimiento reducido, Quieto y `?still=1` eliminan el desplazamiento, los efectos repetidos de esqueleto y el desplazamiento animado, pero conservan todos los destinos, indicadores de ubicación actual, herramientas, reintentos y resultados del foco. Las animaciones CSS se pausan cuando la pestaña está oculta; los efectos repetidos de elementos secundarios se pausan cuando están fuera de pantalla. No se agrega animación de fondo, paralaje, carrusel automático ni animación decorativa continua. En la vista normal medida, las transformaciones de Motion terminan en su posición final y el modo estático tiene cero animaciones en curso.

## Accesibilidad y criterios visuales provisionales de aceptación

Objetivos: WCAG 2.2 AA para el contenido aplicable, texto con contraste ≥4.5:1 (texto grande ≥3:1) y bordes de controles/foco significativos con contraste ≥3:1. Los anclajes y controles de formulario son nativos, las listas son semánticas, los encabezados están asociados con las secciones, los íconos son decorativos y las herramientas no disponibles tienen etiquetas de texto. El foco usa el contorno compartido de 3px con el acento de origen y un desplazamiento de 4px. Las acciones principales y los destinos de entrada tienen al menos 44px de alto. La información de carga/error usa semántica de estado/alerta. Estos son objetivos respaldados por las mediciones siguientes, no una afirmación de conformidad completa con WCAG.

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| SP14-B-01 | 390, 768, 1280px | normal, ES | Cuatro nombres de planes en orden y Gratis / 20.000 / 45.000 / 70.000; solo unidades mensuales en COP |
| SP14-B-02 | 390, 768, 1280px | normal, EN | Enthusiast / Designer / Designer Plus / Master Designer; Free / 7 / 14 / 25; solo unidades mensuales en USD |
| SP14-B-03 | 1280px | normal | El índice fijo ocupa el panel izquierdo y todas las secciones de herramientas permanecen visibles en el documento derecho |
| SP14-B-04 | 390px | normal | Cuatro filas compactas de precios preceden todas las listas de herramientas en una columna, sin desplazamiento horizontal de página |
| SP14-B-05 | todos los anchos medidos | normal | En Plus y Master aparecen tres etiquetas de herramientas no disponibles, con el texto localizado requerido sobre su disponibilidad |
| SP14-B-06 | todos los anchos medidos | normal | Las descripciones del chat de Entusiasta y Designer no contienen valores numéricos de límites |
| SP14-B-07 | todos los anchos medidos | normal | Master tiene una línea de Taller 3D y no tiene una línea independiente para el explorador de decoraciones |
| SP14-B-08 | todos los anchos medidos | inicio de sesión / menú | Exactamente un enlace Plans en cada superficie de entrada abre la vista de planes pública o de sesión iniciada que corresponda |
| SP14-B-09 | todos los anchos medidos | normal | La activación del índice enfoca el encabezado de sección correspondiente; Return restaura el foco en la entrada de origen |
| SP14-B-10 | 390, 1280px | carga / vacío / error | Cada selección nativa de estado muestra una presentación localizada y medida, con la recuperación especificada |
| SP14-B-11 | 390, 1280px | claro / oscuro | Las mediciones de primer plano, controles y foco cumplen los umbrales de auditoría sin cambios de tipografía o paleta específicos del tema |
| SP14-B-12 | 1280px | expresivo / reducido | El desplazamiento de las secciones y el marcador es perceptible con el movimiento activado; el modo estático no tiene animaciones en curso y conserva todo el contenido |

## Verificación y limitaciones explícitas

La instantánea final generada se construyó con el espacio de trabajo instalado real: **550 KB, 2031 archivos de origen, sin conexión**. Los comandos usaron las rutas absolutas asignadas. Ambas herramientas requeridas se ejecutaron sobre **`planes@v1.r1.dir-b.html`**, no sobre la salida canónica.

- Generador sin conexión: código de salida 0.
- `contrast.py`: código de salida 0 — **158 pares comprobados en temas claro y oscuro; todos pasan**.
- `audit_mockup.py`: código de salida 0 — **64 representaciones / 64 combinaciones planificadas**, **1.536 mediciones de texto**, **178 paradas de foco**. Incluye todas las combinaciones nativas de vista/estado/tema a 390 y 1280px, además de las comprobaciones de movimiento y movimiento reducido.

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

- Comprobaciones complementarias en navegador: **24 representaciones de planes normales localizados**, **12 menús de cuenta abiertos**, **24 flujos de entrada/retorno** en **390/768/1280px**, ambos idiomas y ambos temas. Se verificaron la inicialización del idioma del navegador, los nombres/precios exactos, una sola moneda, las seis etiquetas de elementos no disponibles, la separación entre las vistas pública y del menú de cuenta, ambos enlaces de entrada a `/planes`, el foco en el encabezado de destino, la restauración del foco al volver, la ausencia de excepciones de ejecución y la ausencia de solicitudes externas. Las comprobaciones de diseño y contraste de la auditoría de origen no encontraron problemas en estos estados localizados normales y de menú.
- Comprobación de movimiento/selectores: todos los selectores JSON se resuelven en la vista renderizada predeterminada; la transformación medida de una sección cambia de `matrix(1, 0, 0, 1, 26, 0)` a `none`; la traslación de la flecha al pasar el cursor es de 3.59px durante su recorrido de 4px; `?still=1` tiene cero animaciones en curso; cero errores de ejecución.
- Inspección visual: capturas de pantalla en memoria a 1280 y 390px en temas claro/oscuro, con ejemplos en español e inglés, y la entrada de inicio de sesión a 390px. No se crearon archivos de captura fuera de la lista de salidas asignada.

La primera prueba complementaria detectó pérdida de foco después de navegar mediante el anclaje de plan, porque un componente React declarado localmente volvía a montar su DOM. Se corrigió con funciones auxiliares de renderizado estables; las comprobaciones finales de foco pasan. Una edición intermedia para elevar un campo dejó una referencia en el ámbito externo; la prueba complementaria detectó el fallo de ejecución, se corrigió y se volvieron a ejecutar todas las comprobaciones finales. La auditoría compartida imprimió PASS durante ese fallo de ejecución intermedio porque un `#app` vacío seguía presente; ese resultado se rechazó y no se usó como aceptación. La auditoría final de 64 representaciones indicada arriba se volvió a ejecutar sobre las vistas corregidas y pobladas, respaldada por aserciones de ejecución y contenido. Reforzar la comprobación del kit de herramientas para detectar una raíz vacía o errores de ejecución queda como seguimiento fuera del alcance.

No se afirma que se hayan ejecutado el lint, la compilación, las pruebas de backend, la propagación de ediciones al catálogo, la base de datos, la autenticación real de cuentas, el despliegue, una sesión completa con lector de pantalla, una matriz completa de zoom ni la aprobación de la persona propietaria. No se modificaron repositorios de origen ni se hizo commit, push o despliegue. El par canónico sigue ausente y sin cambios.

## Preguntas abiertas y supuestos

**Q1 — Propietario:** ¿Debe **Catálogo / Catalogue** aparecer como una herramienta incluida y visible al público en los cuatro planes? La SPEC actual lo mantiene entre las prestaciones base, mientras que el resumen funcional no nombra explícitamente esa línea. Esta maqueta lo incluye de forma visible y deja abierta la decisión; no agrega una capacidad nueva.

**Q2 — Propietario / Planner:** Si se visita directamente `/planes` con la sesión iniciada y sin una página de origen, ¿debe Return abrir **Mi cuenta**? La maqueta usa Mi cuenta como fixture de origen. La entrada normal desde un menú de cuenta debe regresar a la página segura de origen real, según lo requerido en el resumen.

Confirmado: exactamente cuatro niveles acumulativos; Enthusiast gratis; moneda según el idioma; sin compra, solicitud, registro ni modificación de planes; sin límites numéricos de chat; las tres herramientas no disponibles marcadas en los dos niveles superiores; todo el editor/explorador dentro de la línea Taller 3D de Master. Los valores numéricos de límites de chat se posponen deliberadamente y no son una pregunta para esta exploración. La estructura del contenedor, los formularios de entrada y el menú de cuenta pertenecen a SP-2.

Supuestos: el texto de carga/vacío/error del catálogo es provisional y funcional, no una afirmación de marketing nueva; la cuenta y los formularios ilustrativos solo permiten inspeccionar los dos puntos de entrada a los planes. SP-1 debe proporcionar los registros localizados y autorizados del catálogo antes de la implementación. La persona propietaria o quien finalice el trabajo posteriormente debe resolver Q1/Q2 y redactar el contrato canónico de doce secciones; este artefacto no se aprueba a sí mismo.

## Instantáneas de origen

La fuente funcional compartida define el alcance; SPEC/PLAN aportan únicamente contexto complementario. Huellas capturadas al cerrar esta exploración:

| Fuente de solo lectura | SHA-256 |
|---|---|
| `design/planes@v1.r1.behavior.md` | `15d876a533b5c4f184f022dc07071ef93bb2ca8c90e83a01a8b84961d2fbc07f` |
| `design/cuentas-admin@v1.md` | `465f35b2da29f91f4b024ef82d1b6fa71c9a60824462b97ee5ca55dfc370b1b5` |
| `design/taller-esenciales@v1.md` | `50d823239d182ee1362687317d6d27823ae532282ab69c95993095023df16631` |
| `design/proyectos@v1.md` | `5dbe092fdc220552e38b68169f397af89942dab87313a397fc91c21224ef4c98` |
| `SPEC.md` | `c5ccaae83dad325ac83a7c0b02b4606ca13c0e1ade469ab47041a971ee18a9a0` |
| `PLAN.json` | `ff69d95a94c09b1799d946bda70c85d2a693a9f6772c73e0cb84f43b037c0fa6` |
