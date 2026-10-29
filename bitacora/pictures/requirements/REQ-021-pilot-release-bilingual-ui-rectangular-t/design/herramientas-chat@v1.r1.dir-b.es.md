---
name: Lienzo e inspector
contract_candidate: herramientas-chat@v1
revision: r1.dir-b
status: draft
subplan: SP-7
requirements: [R13, R16]
owner: David
approval: pending
---

# Dirección B — Lienzo e inspector

Solo exploración. Esta es una opción de diseño específica de esta revisión, no el contrato canónico de doce secciones ni una propuesta aprobada para implementación. Solo una finalización posterior seleccionada por el responsable puede crear el par canónico. No se cambió código de producción, contrato compartido, plan, archivo del repositorio ni otra dirección.

## Enfoque y superficie existente

Conservar el encabezado de Pictures/Sempertex, la marca de anillos y puntos, la navegación horizontal entre rutas, los controles de idioma/cuenta y el vocabulario de paneles de papel establecidos por `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`. Cambiar el área de trabajo para convertirla en un espacio de trabajo espacial: entrada a la izquierda, escena o materiales en el centro y resultados a la derecha. La escena sigue siendo el vínculo visual entre una entrada y el conteo de globos. Esto cambia las superficies existentes de chat guiado/Taller; no crea una nueva identidad visual ni una página de inicio.

El contador usa paneles de entrada / escena / lista de compras. La cotización profesional usa un índice de secciones / materiales y gastos editables / inspector de totales. El explorador de decoraciones usa filtros / ideas existentes agrupadas / vista previa seleccionada, bajo la navegación local de Taller. Inicio contiene solo tarjetas de herramientas autorizadas. El chat guiado conserva una conversación y un cuadro de redacción junto a la vista previa de una idea existente; es evidencia contextual, no una especificación que reemplace la interacción del chat.

El área modificada toma prestada la disposición familiar de lienzo e inspector de Taller y conserva el encabezado de las superficies hermanas. El chat normal y la biblioteca/editor existente de Taller siguen a cargo de sus superficies actuales. La vista de taller aquí es un destino ilustrativo, no un rediseño del editor.

## Evidencia inspeccionada en modo de solo lectura

- Fuente de comportamiento: `herramientas-chat@v1.r1.behavior.md`, todos los resultados, reglas de contenido, flujos y estados de pantalla especificados. SPEC R13/R16 y ronda 15; PLAN SP-7, vinculación de interfaz y tareas T7.1/T7.5–T7.8/T7.10.
- Markdown y HTML canónicos de las superficies hermanas: `cuentas-admin@v1`, `planes@v1`, `proyectos@v1`; el TSX seleccionado del proyecto `proyectos@v1.r12.dir-c.tsx` proporciona las importaciones locales exactas de fuentes, la asignación semántica de tokens, el contenedor compartido y el vocabulario de foco.
- t12: `src/app/globals.css`, `layout.tsx`, `CabeceraApp.tsx`, `MenuApp.tsx`, `VistaGuiada.tsx`, `CotizacionProfesional.tsx`, `CampoGanancia.tsx`, `ResumenPrecio.tsx`, `IdeasDelAsistente.tsx`, `Biblioteca.tsx` y nombres de decoraciones existentes de `src/lib/biblioteca-sempertex/decoraciones.json`.
- asesor: `src/app/globals.css` existente confirma la misma paleta de origen. No se editaron archivos del repositorio. Se observaron modificaciones preexistentes de t12 y se dejaron intactas.
- Manifiesto/entorno de ejecución/referencia del kit instalado, `directions.md`, `mockup-craft.md`, habilidades de autoría de contratos de interfaz y de versionado/impacto. Estado real del kit sin conexión: `installed=True built=True entries ok=96/96`.

## Ocho ejes

| Eje | Opción observable |
|---|---|
| Concepto | Una decoración entre sus entradas y su resultado: una superficie de trabajo espacial dentro de Pictures. |
| Diseño | Entrada de 260px / escena flexible / resultado de 270px. La galería conserva los tres paneles; la calculadora los adapta a índice de 230px / formulario de materiales / totales de 290px. El inicio combina una columna contextual de 260px con tarjetas de herramientas. |
| Navegación | Rutas horizontales neutras existentes; Inicio abre cada herramienta autorizada. Los botones de método permanecen en el panel de entrada del contador, los anclajes de secciones de costo saltan dentro del formulario de materiales y los enlaces locales de Taller permiten entrar y salir de Decoraciones. |
| Tipografía | Geist Sans existente, título de página de 24px, títulos de herramientas de 18–20px, texto principal de 14–15px, metadatos de 12–13px, resultado de 30px con cifras tabulares. Geist Mono existente solo para Sempertex. |
| Densidad | Todas las áreas de trabajo de escritorio permanecen visibles una junto a otra. En tablet, el resultado pasa abajo; en teléfono, se apilan la entrada, la escena y el resultado. Relleno de 24px en escritorio y 20px en teléfono; sin cuadrículas de tarjetas decorativas anidadas. |
| Componentes | Button/Input/Skeleton reales de shadcn/Base UI y AlertDialog de Animate UI. Recompone las etiquetas tipo píldora existentes, el menú nativo de cuenta, los paneles divididos y la escena SVG contextual. |
| Color | Tokens exactos de Pictures y superficie de escena de Taller de origen, en ambos temas. El acento identifica las acciones principales y el dibujo de globos claramente ilustrativo; la navegación permanece neutra. |
| Movimiento | Entradas laterales opuestas para la entrada y el inspector; centro elevado 18px con escala de .985→1. Perfil expresivo de 620ms cubic-bezier(.16,1,.3,1), con escalonamiento de tarjetas de 65ms; respuesta rápida de controles de 180ms. Natural: 340/140/30ms; sutil: 180/100/12ms. El modo reducido/inmóvil elimina el desplazamiento y mantiene legible cada estado. |

## Dos miniaturas y selección

1. **Elegida:** `herramientas-chat@v1.r1.dir-b.html.candidate-1.html` — tres paneles simultáneos: formulario, escena y lista de compras. Mantiene visibles a la vez las medidas y los resultados; proporciona la estructura común más sólida para el contador, la cotización y la galería.
2. `herramientas-chat@v1.r1.dir-b.html.candidate-2.html` — escena ampliada con un panel de entrada inferior y un inspector a la derecha. Da más espacio al lienzo, pero dispersa los campos del contador a lo largo del borde inferior y requiere un cambio mayor cuando la cotización necesita muchas filas editables.

Ambas se dibujaron antes de completar la entrada y luego se inspeccionaron como composiciones renderizadas. Ambas conservan Geist incrustada localmente y los tokens de origen de los temas claro/oscuro; los controles de miniatura son solo evidencia de la composición. La maqueta completa desarrolla la candidata 1.

## Tokens y componentes reales

No se agregan paleta, familia tipográfica, marca ni dependencia nuevas. La entrada incluye los recursos WOFF2 locales de Next. El HTML compilado incorpora todos los recursos y el código JS; no requiere fuentes/imágenes remotas, instalación de paquetes ni solicitudes en tiempo de ejecución.

| Tokens del proyecto | Funciones del kit | Claro / oscuro |
|---|---|---|
| fondo | background | #faf9fc / #0b0c10 |
| superficie | card, popover | #ffffff / #16181f |
| superficie-suave | agrupación sutil local | #faf8fd / #1c1e26 |
| superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| texto | foregrounds | #1c1425 / #f4f5f7 |
| texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| texto-tenue | borde accesible de entrada, tratamiento heredado de superficies hermanas | #766c85 / #8a91a0 |
| acento / sobre-acento | primary, ring / primary-foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| borde / borde-suave | contornos decorativos / separadores | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| error / error-suave | texto de error / superficie | #b23a45 / #ffeaec; #ff979f / #43252a |
| taller-visor | lienzo ilustrativo | #ebe7f1 / #1a1722 |

Radios: paneles de 32px, recuadros de 24px, campos de 18px y etiquetas tipo píldora de 999px, heredados de las superficies hermanas elegidas. Otras funciones de éxito/advertencia/barra lateral/gráfico usan los mismos tokens asignados de las superficies hermanas; no constituyen un nuevo sistema de color.

- `shadcn:button default|outline ready|hover|focus|pressed|disabled` — `@/components/ui/button`; acciones reales respaldadas por Base UI y con el tratamiento de píldora del producto.
- `shadcn:input default empty|filled|invalid|focus` — `@/components/ui/input`; medidas, costos, búsqueda e ilustración de guardado con nombre.
- `shadcn:skeleton default loading` — `@/components/ui/skeleton`; marcadores de posición estáticos y texto de carga visible, sin movimiento indefinido.
- `shadcn:alert-dialog unsaved open|closed|invalid` — `@/components/ui/alert-dialog`; modal instalado de Animate UI/Base UI con fondo inerte, contención del foco y cancelación explícita. La agrupación personalizada de acciones conserva el vocabulario de botones del proyecto.
- Botones nativos personalizados de método, anclajes de sección, selector de datos de prueba de permisos, entrada de archivo y menú de cuenta con details/summary. No se presentan como componentes adicionales del kit.
- Vista previa de decoración neutra en SVG personalizada: una escena ilustrativa, nunca el motor/la fotografía reales ni una fuente de conteos.
- `@kit/mockup` proporciona la etiqueta visible Mockup y los inspectores nativos `view`, `state`, `scene`, `theme`, `motion`. `@kit/motion` proporciona el perfil/el estado reducido y el resorte numérico `motion.strong`.

## Vistas, flujos y cobertura de estados

| Vista | Estados / recuperación | Flujo principal |
|---|---|---|
| Inicio | Solo herramientas disponibles; no hay estado vacío porque todos los roles con sesión iniciada tienen herramientas. Los demás estados globales del inspector no aplican aquí. | El accesorio de cuenta selecciona Entusiasta/Designer (2), Designer Plus (3), Master Designer o personal (5). No aparece ninguna tarjeta bloqueada ni nombre o precio de un plan de actualización. La selección de herramientas conserva la cuenta del accesorio. |
| Chat | Conversación inicial y normal, pregunta por medidas faltantes, carga, error/reintento, sin costos. Los demás estados globales dejan el accesorio en estado normal. | Conversación/compositor guiados existentes; acceso directo al contador; conexión autorizada con Taller. Accesorio contextual sin precios para todas las cuentas. |
| Contador | Inicial, medida faltante, contando, resultado, archivo demasiado grande, formato no compatible con imágenes, error/reintento del motor, sin costos. | Formulario / frase / foto → cantidad por tamaño/color + lista de compras, sin precios. Solo `costos.usar` obtiene Calcular costo → estado importado del calculador. |
| Calculador | Vacío, importado desde el contador, edición, cálculo, totales, error/reintento de cotización, denegación de permiso. | Materiales manuales o importados → precio unitario/cantidad editables + costos de mano de obra/equipo/transporte/indirectos + Tu ganancia existente → inspector de totales. La edición oculta los totales anteriores hasta volver a calcular. |
| Galería | Carga, resultados, ningún filtro coincide, error/reintento de carga, id de decoración desconocido, escena actual sin guardar, denegación de permiso. | Búsqueda + filtro de ocasión + tamaño → elegir una idea existente → vista previa → destino de anclaje real `/3d?decoracion=<id>` con apertura simulada en la maqueta. |
| Contexto de Taller | Escena actual con trabajo sin guardar o escena recién abierta sin guardar. | Al abrir una decoración se inicia un proyecto nuevo sin guardar. El editor/biblioteca existente son contextuales; no se rediseñan ni se implementan por completo. |
| Modal de trabajo sin guardar | Abierto, nombre de proyecto vacío no válido, cancelar, guardar/continuar simulado, descartar/continuar explícito. | En el estado sin guardar de Galería, al abrir se pregunta antes de cambiar la escena. Cancelar conserva la escena actual. Para guardar se requiere un nombre; descartar es una acción aparte. |

Cada estado enumerado tiene una opción nativa en el inspector; el inspector de escena abre el modal de forma independiente. Los valores de estado compartidos son contextuales: no implican que todas las pantallas tengan todos los estados. El brief no introduce un Inicio vacío, un catálogo de galería sin filtros ni estados específicos de desconexión. En producción se deben mostrar todos los elementos originales del catálogo; el accesorio de galería contiene intencionalmente solo tres registros de muestra claramente identificados.

Las entradas del contador, la validación del tipo de archivo, el cambio de método, las cantidades, la edición de precios, los filtros, la selección de vista previa, los botones de reintento, los anclajes de sección y los selectores de escenario son ejemplos locales interactivos. Los cambios en el formulario ocultan el conteo anterior del accesorio. Los conteos no recalculan la geometría real del motor. El artefacto completo identifica cada conteo/precio/operación como simulado. La tolerancia fotográfica ±10% es un valor de muestra etiquetado, nunca una tolerancia de producción propuesta.

## Objetivos de accesibilidad y diseño adaptable

- **360–639px (verificación en 390px):** márgenes laterales de 20px, encabezado/rutas con ajuste de línea; todos los paneles de trabajo se apilan en orden de lectura. La lista de Galería va después de los filtros y antes de la vista previa. Las filas de cotización muestran la identidad del producto sobre los dos campos numéricos. El ancho del modal es el del viewport menos 40px, con un margen interior de 24px; las acciones se ajustan en varias líneas y el contenido se desplaza verticalmente.
- **640–1099px (verificación en 768px):** márgenes laterales de 24px, entrada de 230px junto al área de trabajo flexible; el resultado/vista previa pasa abajo y usa dos columnas. Chat apila la conversación y el contexto. Las herramientas de Inicio pasan a una columna junto al contexto. Ningún panel fijo cubre contenido.
- **1100px+ (verificación en 1280px):** márgenes laterales de 40px, ancho máximo de la aplicación de 1520px; espacio de trabajo simultáneo de tres paneles. Formularios/resultados tienen márgenes interiores de 24px.

Objetivos: WCAG 2.2 AA, controles semánticos con etiquetas, contornos de foco visibles de 3px, altura de control ≥44px, contraste de texto ≥4.5:1 y de límites de controles ≥3:1, sin desplazamiento horizontal de página. Número/unidad/color se mantienen como texto; el significado de las cantidades no depende solo del color. Los mensajes de error y carga usan semántica de alert/status. Los filtros/botones de método nativos funcionan con teclado. AlertDialog debe contener el foco y restaurarlo al cancelar; al cerrar el detalle de cuenta con Escape, el foco vuelve al resumen. Se requiere verificación independiente con lectores de pantalla reales, zoom de 200–400% y aplicación de permisos y WebGL en producción. El control visible ES/EN se hereda del contexto de la interfaz; la traducción completa corresponde a SP-10, y su respuesta simulada lo indica explícitamente.

El movimiento es finito y prioriza las transformaciones; el contenido permanece legible en todo momento. Las animaciones CSS se pausan cuando la pestaña está oculta. La opción de movimiento reducido del sistema operativo, Quieto y `?still=1` eliminan el desplazamiento CSS, y el perfil Motion instalado salta al contenido final; no se usa una animación de carga indefinida. Los selectores de evidencia JSON identifican elementos que realmente se mueven, no la raíz del documento.

## Ejemplos de aceptación observables

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| B-01 | Todos | Todos | El encabezado de Pictures/Sempertex y el vocabulario heredado de Geist/tokens permanecen visibles. |
| B-02 | 1100px+ | Resultado del contador | La entrada, la escena y la lista de compras forman tres paneles contiguos. |
| B-03 | 640–1099px | Resultado del contador | El panel de resultados aparece debajo de la entrada y la escena. |
| B-04 | 360–639px | Todos | El contenido se apila sin desplazamiento horizontal de la página. |
| B-05 | Todos | Sin costos | El contador y el chat no muestran importes; el contador no tiene la acción Calcular costo. |
| B-06 | Todos | Edición del calculador | Los totales anteriores quedan ocultos y aparece una instrucción para volver a calcular. |
| B-07 | Todos | Contador importado | El calculador muestra el origen de los materiales del contador. |
| B-08 | Todos | Resultados de Galería | Ideas del asistente e Ideas Sempertex siguen siendo identificables. |
| B-09 | Todos | Galería filtrada | La búsqueda, la ocasión y el tamaño reducen los registros de muestra; la vista previa corresponde a un registro coincidente. |
| B-10 | Todos | Id desconocido | El mensaje de no encontrado indica que la escena abierta no cambió. |
| B-11 | Todos | Apertura con trabajo sin guardar | El modal distingue entre guardar, descartar y cancelar; al guardar con nombre vacío se muestra una validación. |
| B-12 | Todos | Proyecto nuevo abierto | El contexto de Taller muestra Escena nueva y Sin guardar todavía. |
| B-13 | Todos | Movimiento reducido/quieto | Todas las acciones y el texto de estado están disponibles sin desplazamiento ni efecto de rebote en los números. |
| B-14 | Todos | Accesorio de autorización de Inicio | Las herramientas sin permiso no aparecen; no se muestran bloqueadas ni promocionadas. |

## Preguntas abiertas y supuestos

P: ¿Se conserva «Tu ganancia» como porcentaje añadido al costo, tal como hace hoy CotizacionProfesional, aunque el brief lo llame «margen», o se quiere cambiar esa regla?
P: ¿Qué límite de tamaño y formatos de foto debe mostrar el contador, y qué datos de tolerancia devuelve el motor para cada estimación?
P: ¿Decoraciones debe tener también una tarjeta directa en Inicio, además de vivir dentro del Taller, como en esta propuesta de cinco herramientas?

Responsable de la decisión: David/Planner. Las preguntas quedan registradas sin detener la exploración. Supuestos mostrados explícitamente: se conserva la regla de ganancia aditiva existente; los controles de cuenta/permiso son solo simulados; la ilustración/el conteo/la tolerancia fotográfica/los precios son datos de muestra. Este artefacto estático no afirma que exista una fuente real de precios, respuesta de IA, autorización del servidor, cálculo del motor, asiento contable, guardado de proyectos ni idempotencia.

## Impacto y límite de aprobación

Candidato a SP-7 para T7.1, implementación de interfaz T7.5–T7.8 y revisión visual T7.10. Es compatible con la estructura compartida heredada; la nueva página de herramientas, el contador, el calculador y la galería añaden una interacción/distribución que no existía en la única superficie de entrada actual y requieren las implementaciones previstas. Se reutiliza la estructura compartida de SP-2/SP-4/SP-14; no se modificó ningún consumidor de contratos hermanos. SP-10 es responsable de extraer/traducir las cadenas nuevas. SP-1 es responsable de los permisos reales y el catálogo de origen. La aprobación sigue pendiente; esta exploración no puede copiarse como contrato aprobado.

## Verificación honesta

La entrada TSX completa usa el constructor local instalado real, sin alternativa en HTML ni instalación de paquetes. Se corrigió visualmente el modal final para teléfono para apilar sus acciones; no correspondía ejecutar pruebas de build/lint/API de producción en esta exploración de diseño de solo lectura.

| Verificación | Evidencia real |
|---|---|
| Compilación local | Código de salida 0; 642 KB, 2,132 archivos fuente, todos los recursos integrados. |
| Contraste de tokens | Código de salida 0; `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría final renderizada | Código de salida 0; 648 renders / 648 combinaciones planificadas a 1280/390/768px en ambos temas, 19,176 mediciones de texto, 2,146 paradas de foco. Sin muestreo de combinaciones. Un recorrido de foco alcanzó el límite de 60 paradas; no se midieron los controles posteriores de ese recorrido. |
| Sondeos de flujos específicos | `INTERACTIONS: PASS 8 groups; page errors=0; external HTTP(S) requests=0`. Cubre el recuento de herramientas autorizadas/la conservación de la cuenta, el rechazo de la calculadora, la transferencia del contador, la conservación de precios editados y el total de datos de prueba de COP 82,800, la conservación del método de frase/foto, la tolerancia explícita de fotos, la búsqueda/filtro/vista previa de coincidencias/enlace de la galería agrupada, la validación del nombre sin guardar/cancelación/restauración del foco/guardado/nuevo estado sin guardar, el enlace desconocido, el rechazo de permisos y el cierre del diálogo de cuenta con Escape. |
| Modal final para teléfono | `FINAL MODAL: PASS full-width actions, 12 settled keyboard containment checks and cancel focus return`. Los tres cuadros de acción miden 300px × 44.25px en una ventana gráfica de 390px. La primera prueba inmediata de foco detectó el centinela transitorio de foco de Base UI; una vez completada su tarea de redirección del foco, Tab recorre input → save → discard → cancel → input. No fue necesario ningún mecanismo de contención personalizado ni modificar la biblioteca. |
| Movimiento | A 120ms, expressive tiene 6 animaciones en curso; el movimiento reducido del sistema operativo tiene 0; `?still=1` tiene 0. |
| Evidencia de ejes | `JSON EVIDENCE: PASS 16 selectors match rendered elements across declared views`. Los selectores de movimiento corresponden a paneles/tarjetas animados reales; el JSON se puede analizar. |
| Puntos de reflujo | `REFLOW: PASS 360/390/768/1280px counter spot checks`; la auditoría renderizada también recorre todas las combinaciones declaradas en sus tres anchos. |
| Inspección visual | Ambas miniaturas candidatas; contador/calculadora en escritorio claro, inicio/galería en escritorio oscuro, contador en teléfono claro, calculadora/modal en teléfono oscuro, galería en tableta clara. Se inspeccionaron capturas en memoria, sin archivos de artefactos adicionales. El modal final inspeccionado para teléfono tiene tres acciones de ancho completo y muestra el contexto del nombre/error. |
| Espacios en blanco | `git diff --check` en el ámbito de trabajo/preparación pasó. |

Las comprobaciones anteriores detectaron un fallo de contraste del marcador de posición del chat en tema claro (3.43:1), un cálculo local completado que restablecía los precios editados y etiquetas de acciones apretadas en el diálogo para teléfono. Se corrigieron respectivamente con tokens de origen, conservación del estado local y acciones apiladas para teléfono; las verificaciones específicas anteriores confirman las correcciones. Un primer localizador de automatización con mouse quedó esperando estabilidad; el recorrido completo de flujos realizado usa activación real por teclado y no afirma que se haya completado un recorrido íntegro con mouse.

Para reproducir la compilación y las auditorías requeridas:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/herramientas-chat@v1.r1.dir-b.html --widths 1280,390,768 --max-combos 240
```

SHA-256 del HTML final: `7ca3a5308ef53c50320fab56d784effc7fd2fd5fb3e4e505f70099667af06332`.

INQUIETUDES: las preguntas sobre responsables indicadas arriba siguen abiertas; la aprobación y la autorización de producción/verificación de cálculos/almacenamiento/traducción quedan fuera de esta exploración. No se escribió ningún contrato canónico, HTML compartido, directorio de vista previa ni código fuente de producción.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

`warning: 1 focus walks stopped at 60 stops; later controls were not checked`

Este es el resultado de la auditoría final del HTML. El límite restringe la cobertura automatizada del foco en ese único recorrido; no significa que se haya comprobado cada posible parada de teclado. Las comprobaciones independientes del modal tras estabilizarse confirman el ciclo específico de foco entre cuatro controles y el comportamiento de retorno descritos arriba. La aceptación completa de accesibilidad/producción sigue pendiente.
