---
name: Registro de biblioteca
status: draft
subplan: SP-5
contract_target: decoraciones@v1
revision: r2
direction: a
scope: planning-exploration
source_behavior: decoraciones@v1.r2.behavior.md
chosen_thumbnail: decoraciones@v1.r2.dir-a.html.candidate-1.html
---

# Registro de biblioteca — dirección operativa A

Esta exploración está completa como candidata para comparación, **sin aprobar y no es el contrato canónico**. El propietario elige la dirección y después aprueba el plan. No se editó ninguna implementación de producción, contrato compartido, otra dirección, SPEC, PLAN ni memoria del proyecto.

## Enfoque y diferencia respecto de las superficies existentes

La pregunta de trabajo es «¿Cuál de mis escenas o piezas guardadas debería agregar a este proyecto?». La respuesta permanece junto al visor existente del Taller: una biblioteca compacta con filas ocupa el panel de trabajo izquierdo; la geometría, procedencia y acción para colocar una copia del elemento seleccionado ocupan el espacio de trabajo derecho. Al guardar una escena completa o la pieza seleccionada, el detalle derecho se reemplaza por el vocabulario existente del formulario de nombre y ocasión. Es un cambio dentro del Taller, no una página de destino ni un rediseño del catálogo.

La estructura reutiliza los contratos de los productos relacionados ya finalizados: marca de anillo y punto de Pictures, Sempertex, opciones de idioma y cuenta, encabezado de 24px y rutas neutrales horizontales de Taller 3D / Proyectos. La barra de herramientas de escena, la barra lateral de herramientas, deshacer/rehacer, Foto realista y Lista de compra siguen siendo un contexto reconocible. Sus controladores simulados no relacionados anuncian su destino existente en vez de aparentar que los implementan. Esta dirección reorganiza solo la búsqueda en la biblioteca personal, el guardado y el detalle del elemento guardado. El catálogo global/administrativo permanece separado.

Fuentes de producción inspeccionadas en modo de solo lectura: `src/app/globals.css` de ambos repositorios; `src/components/tres-d/Biblioteca.tsx` de t12 (persistencia local, FiltrosCompactos, FichaDialogo, AccionesPieza), `PanelAnadir.tsx`, `Taller3D.tsx` y `src/components/ui/shell/CabeceraApp.tsx`. Se leyeron como referencia los insumos de productos relacionados: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html` y `proyectos@v1.md/.html`; la fuente r12 seleccionada de proyectos proporciona el mapeo exacto del contenedor y los tokens compartidos. El comportamiento de SPEC — SP-5 (respondido en la ronda 11) y el PLAN.json actual de SP-5 confirman el límite entre propietario y personal. El resumen de comportamiento r2 y los comentarios más recientes del propietario rigen el alcance.

## Dos miniaturas y elección

Ambos HTML de miniaturas se dibujaron antes de la entrada TSX completa. Son composiciones deliberadamente pequeñas, no contratos completos alternativos.

- **Candidata 1 — elegida:** filas de biblioteca adyacentes al espacio de trabajo de la escena. En escritorio, la búsqueda, la identidad de la escena/pieza y la acción para colocarla permanecen juntas. Se adapta al cambio existente entre paneles del Taller en teléfonos.
- **Candidata 2 — conservada:** el visor encima de una biblioteca horizontal en la parte inferior. Esto ofrece más ancho al lienzo, pero alarga el recorrido entre los controles de búsqueda, la fila seleccionada y el detalle de colocación. También ocupa el espacio vertical que necesita el formulario de guardado en teléfonos.

Archivos: `decoraciones@v1.r2.dir-a.html.candidate-1.html` y `decoraciones@v1.r2.dir-a.html.candidate-2.html`. Ambos son estáticos, usan Geist existente incrustado y los tokens del producto, y están claramente etiquetados como Maqueta. El artefacto completo usa el generador sin conexión real; estos bocetos no son una alternativa de la cadena de herramientas.

## Dirección en ocho ejes

| Eje | Implementación observable |
|---|---|
| concepto | Registro operativo de decoraciones personales dentro del Taller existente: identificar una escena o pieza, inspeccionarla y colocar una copia sin salir del espacio de trabajo. |
| distribución | Se conservan el encabezado de Pictures/Sempertex y las rutas horizontales de Taller/Proyectos; barra de herramientas de 52px, biblioteca de 390px y espacio flexible para la escena/el detalle. En el ancho de teléfono, Biblioteca/Escena muestra un panel de trabajo a la vez. |
| navegación | Las rutas existentes del producto siguen siendo horizontales y neutrales. Mi biblioteca es la entrada del propietario; Otra cuenta y el selector de propietario aparecen solo en el ejemplo de personal. La búsqueda, el tipo y la ocasión filtran el registro; Filtros muestra los controles de color y globos. |
| tipografía | Geist Sans existente: título de página de 24px, encabezados de biblioteca y elemento seleccionado de 20px, nombres de elementos de 14px, controles de 13px y procedencia de 12px. Geist Mono existente se limita a Sempertex. |
| densidad | Registros compactos con filas, columnas de miniatura de 66px e insetos verticales de 16px; sin tarjetas grandes repetidas. Los filtros de color y globos se muestran a pedido, con los registros locales del navegador en un grupo con etiqueta independiente. |
| componentes | Button, Input y Skeleton instalados de shadcn/Base UI; Dialog con tecnología de Animate UI para nombre/ocasión y AlertDialog para eliminación. Selectores nativos existentes para filtros y detalles/opciones de cuenta; el SVG estático personalizado de escena lleva la etiqueta Maqueta. |
| color | Mapeos exactos de globals.css de Pictures y tokens de productos relacionados ya finalizados: roles de fondo/superficie/texto/acento, además de los roles existentes de Taller, éxito y error. Sin paleta ni tipografía nuevas; texto-tenue proporciona bordes accesibles para los campos. |
| movimiento | Registro lateral preciso: las filas se mueven 12px durante 220ms con desfases de 40ms y cubic-bezier(.77,0,.175,1); la respuesta aparece lateralmente y las marcas de confirmación se asientan durante 360ms. Natural 170/24ms, sutil 120/12ms, 150ms al pasar el cursor/presionar. El movimiento reducido y el modo estático muestran inmediatamente el contenido final; las pestañas ocultas pausan la animación CSS. |

Los selectores en `decoraciones@v1.r2.dir-a.json` apuntan a elementos renderizados reales. `.decoration-row` ejecuta `row-cut`; no se limita a afirmar que hay movimiento; `.btn` tiene transiciones medibles al pasar el cursor y presionar. Los controles nativos `#view`, `#state`, `#scene`, `#theme` y `#motion` permanecen fuera del producto, como controles de planificación del kit.

## Cobertura de vistas, flujos y estados

| Vista nativa | Tarea y estructura del producto |
|---|---|
| Biblioteca | Buscar en la lista de la cuenta, seleccionar una escena/pieza, inspeccionar su miniatura/procedencia y agregar una copia al proyecto abierto. El propietario puede editar el nombre/la ocasión o confirmar la eliminación. |
| Guardar escena | Vista previa de la escena actual → nombre y ocasión → Guardar → Guardando… → éxito confirmado, o formulario preservado y Reintentar. |
| Guardar pieza | El mismo formulario en el lugar para la pieza seleccionada, con la explicación «La pieza sola.» y vista previa de la pieza. |
| Otra cuenta · Solo lectura | El contexto del propietario, solo para el personal, y el indicador de solo lectura preceden a la lista. Los controles de edición, cambio de nombre y eliminación están ausentes. «Añadir copia a mi escena» apunta a la escena propia del miembro del personal. |

| Estado nativo | Resultado visible / recuperación |
|---|---|
| Normal | Filas pertenecientes a la cuenta y el grupo local diferenciado; detalle seleccionado y acción para colocar. |
| Cargando | Dos registros esqueleto, texto de carga y ausencia de controles para editar/colocar elementos guardados. |
| Cuenta vacía | Lista del servidor vacía con una opción para guardar una escena; el grupo existente del navegador permanece diferenciado. No se inventa ningún registro del servidor editable. |
| Error de carga | Error persistente, explicación y Reintentar; ningún elemento guardado ficticio seleccionado. |
| Guardando | Control de guardado deshabilitado; nombre/ocasión preservados y bloqueados durante la simulación de la solicitud. No aparece una confirmación de guardado ni una fila nueva antes de completarse. |
| Guardado confirmado | Ilustración de éxito confirmada por el servidor, marcada explícitamente como simulación en el formulario. El flujo de clic real agrega la fila simulada solo después de su respuesta simulada. |
| Error al guardar · Reintentar | El formulario sigue visible con su nombre/ocasión, un error contextual y la acción para reintentar. El envío normal y el reintento usan la misma secuencia pendiente/confirmada. |
| Cambio de cuenta | Las filas anteriores del servidor, el detalle, el grupo local y las acciones del elemento se eliminan de inmediato. Los marcadores de carga neutrales no reutilizan elementos de la cuenta anterior. |
| Sesión cerrada | Explicación sobre la sesión; no aparecen filas/detalles de la cuenta. El selector de estado nativo permite volver a un ejemplo autenticado, solo para pruebas. |
| Sin acceso al Taller | Explicación sobre el acceso para cuentas sin Taller; no se muestran elementos de la biblioteca ni controles restringidos de elementos. |
| Sin coincidencias | Acción para borrar los filtros; no se muestran coincidencias inventadas ni controles de elementos guardados seleccionados. |
| Copia añadida | Confirmación local persistente de que se colocó una copia en la escena actual. El elemento original no se modifica. |

Los dos primeros estados permanecen estables al seleccionarlos en el inspector. Guardar/Reintentar interactivo se completa tras una respuesta claramente simulada (1100ms); la edición de metadatos y la eliminación muestran una confirmación después de 900ms. Esos retrasos son mecanismos del ejemplo, no requisitos de rendimiento de la API. La validación de nombres vacíos es local y no enfoca un flujo ajeno. Los controles de búsqueda, ocasión, tipo, color y globos funcionan con ejemplos deliberadamente pequeños. Los conteos se derivan de los registros del ejemplo mostrados. El resultado de la búsqueda/los filtros no se convierte en un catálogo nuevo y autoritativo.

El Diálogo nativo ofrece Editar nombre y ocasión y Eliminar decoración para un elemento propio del servidor. Los componentes modales/alerta modal basados en Base UI gestionan el fondo inerte y la contención del teclado. Cancelar devuelve el foco al control de origen; después de eliminar, el foco pasa a la fila restante. Seleccionar una fila en un teléfono muestra el panel de escena y pasa el foco al encabezado del elemento seleccionado. Los diálogos se suprimen para el personal, los elementos solo locales y las sesiones no válidas. Los controles de modificación están ausentes en el modo de personal, en vez de presentarse como permisos deshabilitados.

**Regla de almacenamiento local en el navegador:** `taller3d:biblioteca-propia:v1` es una fuente existente del producto; este ejemplo no la lee ni escribe. «En este navegador» es un grupo ilustrativo independiente con una etiqueta de procedencia local. No hay ninguna acción, progreso, error ni flujo de conversión para importar. Ninguna respuesta de la cuenta se representa como una entrada local heredada. Los elementos heredados no tienen controles nuevos para editar/eliminar en esta exploración.

**Regla de cuenta:** los elementos guardados pertenecen a cuentas con Taller (Master Designer y personal autorizado). El rechazo de eliminación/desactivación de cuentas corresponde a la superficie existente de administración de cuentas; este diseño no agrega otra interfaz para eliminar cuentas. La autorización del backend, la persistencia en un segundo navegador, la limpieza al cerrar sesión, el almacenamiento en caché y la cancelación de solicitudes deben implementarse y probarse de forma independiente en las tareas asignadas; una maqueta estática no puede demostrarlos.

## Sistema de diseño fijo y comportamiento adaptable

La entrada incrusta los recursos WOFF2 locales de Next Geist y Geist Mono. Se conserva el mapeo semántico exacto de los productos relacionados: `--fondo → --background`, `--superficie → --card/--popover`, `--texto → foregrounds`, `--texto-suave → --muted-foreground`, `--acento/--sobre-acento → --primary/--primary-foreground`, `--texto-tenue → --input`, con los roles existentes de éxito/error/advertencia y de Taller. Fondo/superficie/acento claro: `#faf9fc / #ffffff / #6d3fe0`; oscuro: `#0b0c10 / #16181f / #9479ff`. Estos son valores existentes de globals.css, no una paleta de la dirección. Se conservan los radios de borde de los productos relacionados: paneles de 32px, insetos de 24px, campos de 18px y controles tipo píldora; la superficie de trabajo mantiene el marco exterior de 24px del Taller.

Fuentes reales instaladas: variantes outline/default/destructive de `shadcn:button` desde `@/components/ui/button`; `shadcn:input` desde `@/components/ui/input`; `shadcn:skeleton` desde `@/components/ui/skeleton`; `shadcn:dialog` desde `@/components/ui/dialog`; `shadcn:alert-dialog` desde `@/components/ui/alert-dialog`. Las primitivas de Dialog son implementaciones instaladas de Animate UI/Base UI. Las filas del registro y el SVG neutral de escena son composiciones personalizadas; el SVG es geometría ilustrativa, no una miniatura 3D ni un renderizador de producción. No se instalaron paquetes ni se obtuvieron recursos.

- **1024px o más:** márgenes exteriores de 40px, barra de herramientas existente y distribución con barra lateral de 52px + biblioteca de hasta 390px + escena/detalle flexible.
- **640–1023px:** márgenes de 24px, barra lateral de 44px y biblioteca de 300px; los campos de guardado se apilan y las acciones secundarias de la barra de herramientas de escena se ocultan para preservar el espacio de trabajo.
- **Menos de 640px:** márgenes de 20px, encabezado existente con ajuste de línea y navegación horizontal del producto. Los controles Biblioteca/Escena alternan entre los paneles visibles del espacio de trabajo; al seleccionar una fila se abre la escena/el detalle. Las vistas de guardado empiezan en Escena. Los campos y las acciones de los diálogos se apilan; no hay desplazamiento horizontal a nivel de página. La validación incluye teléfonos de 390px, además de redistribución a 768px/tableta y en inglés.

Los controles tienen áreas de interacción de al menos 44px, etiquetas explícitas, foco visible de 3px, anuncios semánticos de errores/estados, selectores nativos y compatibilidad con movimiento reducido. Son objetivos de diseño con la evidencia medida que se detalla a continuación, no una certificación general de WCAG. El movimiento reducido/estático suprime los desplazamientos y las animaciones sin ocultar contenido; las pestañas ocultas suspenden la animación CSS. No se agregan animaciones perpetuas en pantalla.

## Expectativas visuales verificables

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1280px | Normal | El encabezado compartido de Pictures/Sempertex y la navegación horizontal del producto preceden a la barra de herramientas existente del Taller. |
| A-02 | 390 / 1280px | Normal | Las filas del servidor y En este navegador tienen encabezados y procedencias separados; no hay control de importación. |
| A-03 | 390 / 1280px | Guardando | No aparece la confirmación de Guardado ni una fila nueva de la lista del servidor antes de que termine la simulación de respuesta. |
| A-04 | 390 / 1280px | Error al guardar | El nombre/la ocasión siguen disponibles para reintentar y se anuncia el error. |
| A-05 | 390 / 1280px | Personal | Los controles para editar/cambiar el nombre/eliminar están ausentes y la acción principal indica explícitamente que se agrega una copia a la escena propia del miembro del personal. |
| A-06 | 390 / 1280px | Cambio de cuenta | No permanece visible ninguna fila de decoración ni detalle de elementos guardados de la cuenta anterior. |
| A-07 | 390px | Normal / selección | El cambio entre los paneles Biblioteca/Escena se redistribuye sin desplazamiento horizontal; al activar una fila, el foco pasa al encabezado del detalle seleccionado. |
| A-08 | 390 / 1280px | Movimiento reducido / estático | El estado final legible aparece sin desplazamientos y mantiene los mismos controles y estados que el modo expresivo. |

Estas son expectativas de la exploración para comparar, no un contrato de implementación aprobado.

## Evidencia y límites honestos

- Constructor offline real, rutas absolutas de entrada y salida: HTML autónomo exitoso, aproximadamente 638 KB, 2135 archivos fuente incluidos; JS/CSS en línea y fuentes incrustadas, sin referencias a recursos de red.
- Contraste de tokens: `contrast: 158 pairs checked in light and dark, all pass` (código de salida 0).
- Auditoría renderizada en el resultado final: `audit: decoraciones@v1.r2.dir-a.html — 224 renders (224 combinations planned), 7604 text measurements, 1648 focus stops` (código de salida 0).

  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Prueba rápida de comportamiento: personal en modo de solo lectura, colocación de copias, eliminación inmediata de elementos de la cuenta, bloqueo hasta la confirmación del servidor, conservación del formulario al reintentar, foco en modal/cancelación, 24 casos de ancho/tema/vista (390/768/1280), redistribución del contenido en inglés, sin solicitudes HTTP(S) ni errores de página; todo aprobado. También se aprobó la prueba de foco al seleccionar una fila en el teléfono.
- Se inspeccionaron capturas directamente en ambos temas a 1280 y 390: biblioteca del propietario en tema claro, vista de personal en tema oscuro, guardar pieza en teléfono con tema claro y biblioteca en teléfono con tema oscuro. La primera revisión llevó a reducir la altura de los filtros; los filtros de color/globo siguen accesibles en Filtros. Los cambios posteriores solo agregan la transferencia de foco al seleccionar una fila; la auditoría final cubre la compilación final.
- Prueba rápida adicional de selectores/filtros: se resuelven todos los selectores de evidencia JSON; los filtros expandidos de Color/Globo son visibles y operables, sin desbordamiento a 360/390/768/1024px. Ambas miniaturas candidatas contienen fuentes incrustadas y no tienen expresiones de recursos sin resolver. Una prueba inicial de etiqueta exacta y su diagnóstico agotaron el tiempo de espera porque la etiqueta del selector envuelto incluye el texto de la opción; el localizador DOM acotado corregido pasó sin modificar la maqueta. Fue un fallo del localizador de prueba, no evidencia de un menú desplegable oculto.
- No se ejecutaron pruebas de lint/test/build del repositorio: los repositorios de producción son de solo lectura y no se modificaron. Este artefacto estático no prueba ninguna API de cuenta, persistencia del servidor, segundo navegador, servicio de permisos, motor 3D real ni implementación.

## Preguntas pendientes / INQUIETUDES

P: ¿Editar una decoración propia en el piloto solo abarca su nombre y ocasión, o también debe reemplazar explícitamente la composición almacenada? El editor ilustrado cubre los metadatos; el reemplazo de la composición queda pendiente de la decisión del propietario/Planner.
P: ¿Desde qué superficie existente de cuenta/administración debe acceder el personal a la biblioteca de decoraciones de otra cuenta? El ejemplo exploratorio para el personal usa un selector de propietario con alcance en el Taller; el punto de entrada de producción aún no está confirmado.
P: ¿Guardar un nombre existente debe crear un elemento separado, exigir otro nombre o reemplazar explícitamente un elemento? La maqueta muestra un nuevo registro tras la confirmación y nunca sobrescribe un elemento por nombre de forma silenciosa.

Las tres decisiones corresponden a David y al Planner. No impiden comparar esta propuesta. No se aprueba ningún contrato canónico ni implementación. El aislamiento de caché en producción, las mutaciones de API denegadas y el rechazo al eliminar una cuenta requieren las tareas de ingeniería y aceptación independiente asignadas.

## Impacto en consumidores

Solo SP-5 consume decoraciones@v1: T5.1 copia el contrato aprobado posteriormente, T5.3 implementa la interfaz de la biblioteca personal y T5.5 realiza la revisión visual independiente. Esta exploración r2 no modifica ninguna de esas referencias. La compatibilidad está **indeterminada hasta la aprobación de la dirección/plan**; respecto de la biblioteca actual, que solo funciona en el navegador, la separación entre servidor y almacenamiento local, el modo de solo lectura y la jerarquía adaptable del panel de trabajo requieren adaptación en T5.3. Se conservan la estructura y los tokens compartidos con el módulo hermano; no se asigna nuevo trabajo de implementación a ningún otro subplan. La finalización debe resolver las preguntas y redactar el contrato canónico de doce secciones en su tarea autorizada por separado.
