# Escena junto al chat — SP-12, dirección B

Estado: **exploración preliminar; sin aprobar**. Candidata para `chat-a-3d@v1`, revisión r1. Responsable: David. Alcance: SP-12 / R13, exactamente `chat-a-3d@v1.r1.behavior.md`. Esta dirección no crea ni modifica el contrato canónico, SPEC, PLAN ni código de producción. La selección del responsable y la aprobación del plan siguen pendientes.

## Enfoque y superficie existente

Modificar el chat guiado normal existente en `/asistente`, ubicado en t12 `src/app/asistente/page.tsx` y `src/components/guiado/VistaGuiada.tsx`. Las ideas de decoración actuales están en `CarruselDecoraciones.tsx`, su compositor en `Compositor.tsx` y su estructura visual en `src/components/ui/shell/CabeceraApp.tsx` / `MenuApp.tsx`. Se inspeccionó en modo de solo lectura la superficie guiada correspondiente del repositorio asesor y su componente separado `src/components/asesor/ChatView.tsx`; este diseño apunta a `/asistente`, no a `/asesor`.

El área modificada pasa a ser una columna de conversación junto a una recomendación ampliada y un índice de vista previa local. La conversación registra la necesidad; la escena ampliada permite que la persona inspeccione la misma decoración de la galería antes de abrirla. Es una disposición del chat existente y sus tarjetas de recomendaciones dentro del producto, sin una nueva página de inicio, explorador de catálogo, inspector de edición, función de búsqueda/filtro ni flujo de precios.

Conservar el encabezado elegido de Pictures/Sempertex con anillo y punto, la divulgación de cuenta, el control de idioma, la regla horizontal neutral de ruta, la tipografía Geist, las superficies redondeadas y los controles tipo píldora. La ruta local de Chat es el destino actual `/asistente`; Taller 3D y Proyectos conservan sus destinos equivalentes. La navegación de cuenta y otras herramientas son controles contextuales simulados, con indicación explícita de Mockup. La llegada al taller es una fixture de contexto acotada que muestra Escena nueva / Sin guardar todavía; el editor real y el comportamiento de guardado pertenecen a `proyectos@v1`.

## Comparación de miniaturas

Los dos HTML de miniatura se escribieron antes del TSX completo:

- **Elegida: candidata 1**, `chat-a-3d@v1.r1.dir-b.html.candidate-1.html`: conversación a la izquierda, escena ampliada a la derecha e índice compacto de vistas previas debajo. A 1280px, la conversación y la primera recomendación permanecen visibles al mismo tiempo.
- Candidata 2, `chat-a-3d@v1.r1.dir-b.html.candidate-2.html`: escena ampliada junto a un índice vertical de vistas previas, con la conversación debajo de ambos. En su miniatura renderizada a 1280px, la conversación queda debajo del primer viewport. Es menos adecuada para la tarea conversacional breve.

Las miniaturas son bocetos de composición con ilustraciones repetidas. La dirección completa diferencia las tres formas de las ilustraciones, usa controles instalados reales, admite ambos temas e incluye todos los estados declarados.

## Por qué encaja con Pictures

El encabezado compartido, la navegación neutral entre rutas y las superficies redondeadas coinciden con `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`. La vista previa de escena de este último y el vocabulario de cuenta y navegador siguen siendo reconocibles. Solo cambia la jerarquía del área de recomendaciones: una vista previa seleccionada más grande y un selector compacto en la página, en lugar de un carrusel aislado. Los nombres siguen siendo legibles y se ajustan a varias líneas; los conteos permanecen junto a la decoración que describen. La conversación nunca se convierte en un formulario ni en un asistente de varios pasos.

## Ocho ejes

| Eje | Expresión renderizada |
|---|---|
| Concepto | La conversación breve y la escena de galería seleccionada permanecen juntas en pantallas anchas. |
| Diseño | A partir de 1100px, columna de chat de 280–340px + área de escena flexible; tarjeta seleccionada ampliada sobre un índice de vistas previas de tres tarjetas. |
| Navegación | Regla de rutas compartida; botones locales nativos de vista previa con `aria-pressed`, etiqueta de vista previa actual y foco conservado al seleccionar; las acciones autorizadas para abrir permanecen en cada tarjeta. |
| Tipografía | Geist Sans del producto: H1 de 24px, decoración seleccionada de 20px, encabezados de panel de 18px, texto principal de 14–15px y metadatos de 12–13px. Solo se hereda la marca denominativa Geist Mono; conteos de globos tabulares. |
| Densidad | Conversación compacta y tarjetas indexadas; una vista previa ampliada. El índice para tabletas cambia de disposición para evitar tarjetas comprimidas; las tarjetas para teléfonos usan una composición horizontal de vista previa y texto. |
| Componentes | Button/Input/Skeleton/Dialog reales del kit instalado; detalles de cuenta nativos y selector de idioma; botones de vista previa semánticos personalizados y SVG ilustrativos etiquetados. |
| Color | Tokens exactos del proyecto existente y asignación semántica de roles del componente hermano elegido; acento para la acción de apertura y el foco, navegación y dibujos neutrales, texto de error más palabras explícitas para indicar fallos. |
| Movimiento | Acoplamiento en direcciones opuestas, una secuencia finita de asentamiento de tarjetas y transferencia de escena; tiempos según el perfil, sin animación ambiental continua y con equivalencia para movimiento reducido o quieto. |

La evidencia de selectores JSON está en `chat-a-3d@v1.r1.dir-b.json`. Cada selector coincide con elementos renderizados. Los selectores de movimiento controlan fotogramas clave CSS reales; no apuntan simplemente a un contenedor estático.

## Detalles de interacción y movimiento

La conversación se acopla desde x=-18px y la plataforma de escena desde x=+26px, con cubic-bezier(.16,1,.3,1). Las tarjetas compactas se asientan desde y=16px y rotate(.6deg), sobrepasan la posición hasta y=-2px y luego se estabilizan, con 65ms de diferencia entre cada tarjeta. Al seleccionar una vista previa, se conserva el foco de teclado del botón activador, se actualiza su etiqueta de estado y de vista actual, y la escena de reemplazo se asienta desde x=24px / scale(.975). El nombre y el conteo ampliados se anuncian de forma cortés. La selección nunca cambia los datos de la galería ni crea un proyecto.

El perfil Expresivo usa tiempos de entrada, control y escalonamiento de 580ms / 180ms / 65ms; Natural, 360/140/35ms; Sutil, 180/100/12ms. Los controles tipo píldora existentes conservan la respuesta rápida a la pulsación y la respuesta del ícono del componente hermano. `useMotionProfile()` proporciona el perfil seleccionado y la marca de movimiento reducido. El movimiento reducido del sistema operativo, Quieto y `?still=1` eliminan todos los desplazamientos y transiciones sin ocultar el contenido ni las acciones; las pestañas ocultas pausan la animación CSS. Las entradas son finitas y mantienen el texto legible en todo momento. El diálogo real instalado de Animate UI/Base UI contiene el foco para la confirmación de reinicio existente.

Abrir la tarjeta seleccionada o cualquier tarjeta indexada usa la identidad de esa tarjeta y representa `/3d?decoracion=<id>` como un **proyecto nuevo sin guardar**. El fixture local muestra la ruta codificada como evidencia de Mockup y conserva la decoración elegida al cambiar de vista. No realiza solicitudes de red ni guarda un proyecto. Quienes no tengan `decoraciones.explorar` reciben las mismas tarjetas y selección de vistas previas, sin **acción de apertura, reemplazo deshabilitado, aviso para mejorar el plan ni mención del plan en el área de recomendaciones**. Planes en el menú de cuenta permanece como contexto heredado de la estructura compartida.

La acción existente Empezar de nuevo conserva un diálogo de confirmación, Cancelar y la devolución del foco. El envío de un campo de texto vacío está deshabilitado; la conversación ilustrativa avanza de la ocasión al tamaño y los colores, y luego a las recomendaciones. El texto arbitrario no se interpreta: la interfaz marca explícitamente las respuestas de ejemplo y el fixture nunca llama a un asistente ni a un modelo.

## Sistema de diseño fijo y componentes reales

Fuentes: `src/app/globals.css` de ambos repositorios, configuración de fuentes en `src/app/layout.tsx`, estructura compartida actual, controles guiados y los tres contratos y archivos HTML de componentes hermanos proporcionados. El TSX completo incorpora directamente el CSS compartido de encabezado y navegación del componente hermano `proyectos@v1.r12.dir-c.tsx` y su asignación de tokens; no importa las operaciones del listado de proyectos ni del taller.

| Fuente del proyecto | Responsabilidad del kit | Claro / oscuro |
|---|---|---|
| fondo | fondo | #faf9fc / #0b0c10 |
| superficie | tarjeta, ventana emergente, barra lateral | #ffffff / #16181f |
| superficie-suave | superficie local seleccionada | #faf8fd / #1c1e26 |
| superficie-2 | secundario, atenuado, acento | #efe9f8 / #242733 |
| texto | primeros planos | #1c1425 / #f4f5f7 |
| texto-suave | texto complementario, primer plano atenuado | #6b6178 / #9aa1ad |
| texto-tenue | límite accesible del control | #766c85 / #8a91a0 |
| acento / sobre-acento | color principal y primer plano principal | #6d3fe0 / #ffffff; oscuro #9479ff / #120b24 |
| acento-hover | al pasar el cursor | #5530b8 / #a58dff |
| borde / borde-suave | contornos y separadores decorativos | #e3daef / #efe9f8; oscuro #383c48 / #2a2d38 |
| error / error-suave | texto de error y superficie de origen | #b23a45 / #ffeaec; oscuro #ff979f / #43252a |
| taller-visor / taller-panel | contexto heredado de llegada al taller | #ebe7f1 / #faf9fc; oscuro #1a1722 / #16131d |

Geist Sans y Geist Mono se incluyen desde los recursos WOFF2 existentes de t12 en `.next/static/media`; no se descargan paquetes ni recursos. Los radios compartidos de paneles, inserciones, campos y píldoras siguen siendo 32/24/18/999px. Los roles semánticos para éxito, advertencia, gráficos y primer plano destructivo se heredan del componente hermano elegido para validar el contraste del kit completo, sin agregar datos ni colores visibles que no estén relacionados.

| Componente, estado de variante source:id | Importación real / función |
|---|---|
| shadcn:button default listo/hover/foco/presionado/deshabilitado/ocupado | `@/components/ui/button`; abrir y enviar autorizados en tamaño ampliado |
| shadcn:button outline listo/hover/foco/presionado/deshabilitado | igual; abrir, recuperar, reiniciar y cancelar desde elementos indexados |
| shadcn:input text vacío/con contenido/foco | `@/components/ui/input`; campo de texto etiquetado |
| shadcn:skeleton carga de escena | `@/components/ui/skeleton`; geometría reservada para imagen/nombre/conteo, sin valores inventados |
| shadcn:dialog reinicio abierto/cerrado | `@/components/ui/dialog`; mejora con Animate UI/Base UI instalado |
| custom:preview-index nativo sin seleccionar/seleccionado/foco | `.card-preview`, nombre/conteo completos, `aria-pressed`, etiqueta de vista previa actual |
| custom:scene-preview SVG ilustrativo/no disponible | `.scene-art`; sin WebGL, miniatura generada ni afirmación de fidelidad exacta a la escena |
| native:details cuenta abierta/cerrada | disclosure de cuenta heredado, cierre con Escape o al hacer clic fuera |
| native:select idioma es/en | etiquetado como `#language`; expansión de idioma solo en el fixture, sin guardar preferencias |
| kit:planning-controls vista/estado/escena/tema/movimiento | `mountMockup/useMockup` de `@kit/mockup`; selectores nativos fuera del producto |

## Procedencia de los datos e idioma

La evaluación local de solo lectura con `tsx --conditions=react-server` de t12 instalado importó `BIBLIOTECA_FABRICA` y `productosDe`. Cada número corresponde a `productosDe(item).totalGlobos`, no a una estimación escrita a mano ni al conteo de los círculos SVG decorativos:

| Identidad real del catálogo | Nombre real de origen | Total del motor |
|---|---|---|
| escena:arco_organico_columnas_guirnalda | Arco orgánico con dos columnas y guirnalda | 530 |
| escena:pared_fondo_columnas | Pared de globos al fondo y dos columnas | 346 |
| escena:techo_racimos | Techo con tiras y flores colgando | 188 |

Los dos mensajes de clientes del fixture son ejemplos neutrales, no una prueba de clasificación de recomendaciones. Todas las imágenes de vista previa están etiquetadas como SVG ilustrativos de muestra; no reproducen 530 globos ni afirman ser la representación real de la galería. En producción se debe usar la vista previa correspondiente de la galería y el conteo del motor. Los nombres y conteos comparten una única variable del fixture en las tarjetas, la vista previa ampliada y el contexto del taller. Las traducciones al inglés de esta exploración son traducciones provisionales de esas etiquetas reales de origen, a la espera de la decisión de localización de la galería que se indica a continuación; la implementación debe consumir los datos localizados de la galería en lugar de pedirle al chat que invente o traduzca nombres.

## Vistas, flujos y estados

Vista nativa muestra el chat con permiso de apertura, el chat con solo recomendaciones y el contexto de llegada al taller. Estado nativo muestra todos los estados siguientes. Diálogo nativo permite acceder por separado a la confirmación de reinicio. Tema ofrece claro/oscuro, Movimiento ofrece todos los perfiles/Quieto e Idioma del producto ofrece ES/EN. El taller es solo contexto: su apariencia sigue siendo la entrega exitosa para cada selección de Estado; los estados del chat no inventan fallos del taller.

| Estado | Presentación y recuperación |
|---|---|
| ready | Tres tarjetas de decoración existentes; la primera escena se muestra ampliada al inicio y seleccionar otra la mantiene en su lugar. |
| two-results | Dos tarjetas, misma jerarquía, sin tercer espacio vacío ni tercer resultado inventado. |
| initial | Saludo/pregunta sobre la ocasión existentes, marcador de posición neutral para recomendaciones y respuesta de ejemplo Cumpleaños. Reiniciar está deshabilitado porque no hay una conversación que borrar. |
| conversation | Primera respuesta del usuario, pregunta breve sobre tamaño y color, campo de texto enfocado mediante la acción de respuesta complementaria; sin recomendación inventada. |
| loading | Esqueleto con espacio reservado para escena/nombre/conteo y Buscando decoraciones; el campo de texto sigue habilitado y Enviar cambia a Detener. |
| empty | No hay coincidencias, sin tarjetas; la acción enfoca el campo de texto para precisar lo que se busca. |
| error | No pudimos cargar las decoraciones; Intentar de nuevo explícito restablece los resultados de ejemplo. |
| offline | Sin conexión, texto sobre conexión/reintento; se conserva la conversación de ejemplo y no se afirma que haya resultados nuevos. |
| preview-error | La vista previa seleccionada no está disponible, con opción de reintentar; el nombre/conteo reales siguen visibles. Los dibujos indexados del mock siguen siendo contexto ilustrativo. |
| count-error | Conteo no disponible; no se sustituye por cero ni por una estimación; opción explícita de reintentar. La apertura autorizada está deshabilitada hasta obtener el conteo, sujeto a la pregunta Q1 del propietario. |
| opening | Abriendo… en la acción ampliada y controles duplicados de apertura deshabilitados. El estado se puede inspeccionar explícitamente; la acción habitual muestra directamente la llegada exitosa. |
| unavailable | Decoración no disponible; volver a las recomendaciones, sin inventar un nombre de reemplazo. |
| restart dialog | Se borrará esta conversación, Cancelar y Empezar de nuevo. Cancelar o pulsar Escape conserva la conversación y devuelve el foco; confirmar vuelve al estado inicial. |

La ausencia de permisos se representa mediante la vista de cuenta de solo lectura, no mediante un error ni una oferta de mejora. No se agregan consentimientos, pagos, registros, operaciones del editor, precios ni comparaciones de planes. Los rechazos de autenticación, la gestión de cuotas, los estados internos del contador/calculadora y los conflictos al guardar pertenecen a sus subplanes existentes y no se inventan aquí. La validación del campo de texto vacío se representa con el envío deshabilitado, no con un diálogo de error inventado.

## Objetivos de diseño adaptable y accesibilidad

Rango compatible desde 360px; puntos de control renderizados en 390, 768 y 1280px con ambos temas. A partir de 1100px, usar márgenes exteriores de 40px, conversación fija y tres tarjetas compactas debajo de la etapa. Entre 840 y 1099px, usar márgenes de 24px, una conversación de 280px y filas verticales de recomendaciones junto a la etapa. Entre 640 y 839px, usar márgenes de 24px, conversación y etapa apiladas y tres columnas para el índice de vistas previas. Entre 360 y 639px, usar márgenes de 20px, encabezado y navegación con ajuste de línea, conversación y etapa apiladas y tarjetas compactas en una sola columna, con imagen y texto en horizontal. El nombre, el conteo y la acción seleccionados se apilan; todas las etiquetas largas se ajustan a varias líneas. La página no tiene desplazamiento horizontal. El desplazamiento vertical mantiene accesibles la conversación completa, las alternativas y la acción.

Objetivo: cumplir los criterios aplicables de WCAG 2.2 AA, sin afirmar que el producto está certificado: encabezados, artículos y navegación semánticos; botones nativos para las vistas previas, operables con teclado; nombres accesibles que incluyan la decoración; estado textual de la vista previa actual; selección con `aria-pressed`; controles de 44px; anillo de foco de acento de 3px con desplazamiento de 4px; contraste ≥4.5:1 para el texto del cuerpo y ≥3:1 para los límites significativos de controles y foco. Las actualizaciones de estado son corteses; los errores que requieren una acción usan una alerta y una opción para volver a intentar. Los iconos decorativos están ocultos; los SVG tienen etiquetas descriptivas. El diálogo mantiene el foco dentro y lo devuelve al cerrarse. El modo reducido/estático conserva la misma información y los mismos resultados, sin desplazamientos animados. El comportamiento real del asistente, los permisos, la experiencia con lectores de pantalla y las garantías del servidor requieren revisión de implementación.

| ID | Punto de quiebre | Estado | Resultado observable |
|---|---|---|---|
| B-AC-01 | Todos | Todos | El shell compartido de Pictures/Sempertex, las fuentes, los tokens y la navegación horizontal neutra siguen visibles. |
| B-AC-02 | 1100px+ | listo | La conversación queda a la izquierda de la escena ampliada y el índice de vistas previas con tres tarjetas queda debajo de esa escena. |
| B-AC-03 | 840–1099px | listo | El índice usa filas horizontales compactas; los nombres y las etiquetas para abrir caben dentro de la columna de la escena. |
| B-AC-04 | 640–839px | listo | La conversación queda encima de la etapa; el índice de vistas previas tiene tres columnas. |
| B-AC-05 | 360–639px | listo | La conversación, la etapa y el índice se apilan sin desbordamiento horizontal de la página. |
| B-AC-06 | Todos | listo/dos resultados | Cada tarjeta muestra su vista previa, el nombre completo de origen y el conteo correspondiente del motor; dos resultados no dejan un tercer marcador de posición. |
| B-AC-07 | Todos | solo lectura | En el área de recomendaciones no aparece ninguna acción para abrir ni para promover un plan. |
| B-AC-08 | Todos | selección | Seleccionar una vista previa cambia la escena ampliada, el nombre, el conteo y el indicador de selección, mientras el foco permanece en su botón. |
| B-AC-09 | Todos | apertura | Abrir cualquier tarjeta autorizada lleva su identidad a un contexto de Escena nueva / Sin guardar todavía. |
| B-AC-10 | Todos | carga | Aparecen esqueletos de imagen, nombre y conteo, y el mensaje Buscando decoraciones, sin inventar nombres ni conteos. |
| B-AC-11 | Todos | vacío/error/sin conexión/no disponible | El estado incluye una explicación visible y la opción documentada de recuperación mediante reintento, ajuste o recomendación. |
| B-AC-12 | Todos | error de conteo | El conteo faltante se etiqueta como no disponible y nunca se reemplaza por cero; se deshabilita la apertura duplicada hasta que se recupere. |
| B-AC-13 | Todos | error de vista previa | El nombre y el conteo siguen disponibles junto a un error explícito de vista previa y la opción para volver a intentar. |
| B-AC-14 | Todos | diálogo de reinicio | Cancelar/Escape conserva la conversación y devuelve el foco; confirmar la borra. |
| B-AC-15 | Todos | inglés | Los nombres existentes se traducen para la fixture y los controles expandidos se ajustan dentro de la misma jerarquía; los conteos no cambian. |
| B-AC-16 | Todos | reducido/estático | Todo el contenido y los controles siguen disponibles, sin movimiento de entrada ni continuo. |

## Verificación

Todas las evidencias siguientes corresponden al HTML final específico de esta revisión. El builder real estaba disponible; no se usaron alternativas, instalaciones de paquetes, solicitudes de red ni modificaciones en producción.

| Comprobación | Resultado real |
|---|---|
| Estado de la biblioteca instalada | `installed=True built=True entries ok=96/96`. |
| Compilación sin conexión | Código de salida 0; 631 KB, 2,126 archivos fuente, React, controles reales instalados y fuentes locales integrados. |
| Contraste de tokens | Código de salida 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría de renderizado requerida | Código de salida 0: **234 renderizados / 234 combinaciones previstas**, 6,942 mediciones de texto, 584 paradas de foco, en 1280/390/768px con ambos temas, incluido el diálogo de reinicio. Sin muestreo. |
| Complemento de renderizado en inglés | 216 combinaciones de vista/estado/tema/ancho base; cero hallazgos de contraste, contenido no textual, alineación, relleno, desbordamiento o elementos sin medir; sin errores de página ni solicitudes HTTP(S). Este complemento excluye las escenas de diálogo; la auditoría requerida en español cubre el diálogo. |
| Interacciones específicas | Código de salida 0: `INTERACTIONS: PASS 9 groups; zero page errors and zero external HTTP(S) requests`. Incluye límites de selección por cantidad de resultados, vista previa y foco por teclado, identidad correcta del taller seleccionado, ausencia de textos para abrir o promocionar planes en modo de solo lectura, reintentos de conteo/vista previa, Escape/cancelación/foco/confirmación del reinicio, conversación de ejemplo, detención de la carga y conteos en inglés. |
| Selectores de evidencia | Todos los selectores de diseño, navegación, tipografía y movimiento del JSON coincidieron con elementos renderizados reales. |
| Movimiento | A los 120ms, 6 animaciones expresivas en ejecución; 0 con el movimiento reducido del sistema operativo; 0 con `?still=1`. |
| Inspección visual | Se inspeccionaron ambas miniaturas candidatas a 1280px. Se inspeccionaron capturas del HTML final a 1280/390px en tema claro/español y oscuro/inglés; las tarjetas de recomendaciones del teléfono se redistribuyen, y los nombres y las acciones se ajustan por completo. Las capturas se conservaron en memoria; no se escribieron archivos adicionales. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Las primeras pasadas de auditoría detectaron falsos positivos de alineación de columna centrada causados por contenedores con metadatos que se ajustaban al contenido (35 hallazgos y luego 21 en el aviso de error de conteo para teléfono). Hacer que la identidad seleccionada y el texto de error ocuparan el espacio flexible disponible corrigió esas agrupaciones ambiguas; la auditoría final sin modificaciones informa cero hallazgos. Una sonda inicial de interacciones esperaba 530 después de seleccionar deliberadamente la decoración de 346 globos; se corrigió la expectativa y la sonda consolidada final pasa. No se presenta ninguna comprobación fallida como aprobada.

Comandos para reproducir:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/chat-a-3d@v1.r1.dir-b.html --widths 1280,390,768
```

Las sondas complementarias de inglés, interacciones, selectores, movimiento y capturas se ejecutaron en línea con Playwright/Chromium en caché y no escribieron artefactos adicionales. Estas comprobaciones validan únicamente este artefacto de planificación; la precisión de las recomendaciones, la cobertura del catálogo localizado, la fidelidad de las imágenes reales de la galería, la aplicación de permisos, el enrutamiento del servidor y el guardado quedan fuera de la evidencia.

## Preguntas y supuestos

Q1 — Propietario: si falla el conteo del motor para una recomendación, ¿debe omitirse la tarjeta hasta que se recupere o permanecer con el mensaje “Conteo no disponible” y la apertura deshabilitada, como se muestra en esta exploración? El borrador elige la segunda opción únicamente como estado de recuperación inspeccionable; no se inventa ningún conteo.

Q2 — Propietario / responsable de localización de la galería: ¿quién proporciona los nombres en inglés de la galería y qué debe mostrarse cuando falta un nombre localizado? Los nombres en inglés del HTML son traducciones provisionales para inspeccionar el diseño, no entradas confirmadas del catálogo ni nombres generados por el chat.

Supuestos que se mantienen para la comparación: ampliar inicialmente la primera recomendación devuelta; la selección local es solo de presentación y no cambia el orden; abrir crea una escena nueva sin guardar y delega el comportamiento del editor/guardado a SP-4; los resultados de los reintentos y las respuestas de ejemplo son transiciones de una fixture en memoria. Son decisiones de diseño revisables, no evidencia del comportamiento en producción ni de la aprobación del propietario. Esta exploración no escribe directorio de vistas previas, contrato canónico, registro de cambios ni archivo de plan.

Impacto: texto futuro del contrato de T12.1, interfaz de recomendaciones de T12.3 y revisión visual de T12.5 de SP-12. La decisión de composición/interacción queda indeterminada hasta que haya una selección y aprobación del propietario. Se reutilizan la identidad/conteo de la galería, las entradas de idioma y la semántica del mapa de permisos; no se modifica ningún contrato de subplan. La autenticación en producción, el orden de las recomendaciones, la fidelidad de la galería, la alternativa de localización, el enrutamiento y la creación de proyectos guardados no se verifican aquí.
