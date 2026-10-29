---
name: Edición en el lugar
contract_target: decoraciones@v1
status: draft
artifact: exploration
direction: c
revision: r2
subplan: SP-5
requirements: [R8]
owner: David
date: 2026-10-29
behavior_source: decoraciones@v1.r2.behavior.md
chosen_thumbnail: decoraciones@v1.r2.dir-c.html.candidate-1.html
---

# Dirección C — Edición en el lugar

## 1. Identidad y alcance

Exploración de planificación únicamente; no aprobada. Esta nota no es el contrato canónico `decoraciones@v1` ni autoriza la implementación. El propietario elige la dirección antes de que un finalizador escriba ese contrato. No se modificaron contratos canónicos, planes, fuentes de producción, registros compartidos ni directorios de vista previa.

Autoridad de comportamiento: `decoraciones@v1.r2.behavior.md`, SPEC «Behavior — SP-5 (round 11 answered)» y los criterios de resultado/producto de SP-5 en PLAN.json. Prevalece la retroalimentación del propietario del 2026-10-29: sin importación de la biblioteca del navegador, estado de guardado confirmado por el servidor, originales de solo lectura para el personal, colocación como copia en una escena propia, permiso de Taller y aislamiento inmediato al cambiar de cuenta. T5.1 es el siguiente paso de control para copiar el contrato; T5.3 implementa la interfaz de usuario; T5.5 es responsable de la revisión visual independiente. Esta exploración no modifica esas tareas ni afirma que hayan sido aceptadas.

## 2. Propósito y enfoque

La pregunta de trabajo es: «¿Qué parte de esta escena debería guardar y qué decoración guardada debería agregar aquí?». Se mantiene visible el Taller existente mientras se responde. Al seleccionar la pieza de la escena, el formulario para guardarla se despliega en el inspector existente. Los elementos guardados aparecen en una sección de miniaturas debajo de ese mismo espacio de trabajo. Al abrir una tarjeta, se muestran ahí mismo su vista previa, las opciones de colocación y la edición opcional de metadatos, sin una nueva ruta ni una página de detalles a pantalla completa.

Los usuarios son Master Designers y personal con sesión iniciada y acceso al Taller. La biblioteca propiedad de la cuenta está separada del catálogo global/administrativo. El personal inspecciona el original de otra cuenta con una insignia de solo lectura y sin controles para cambiar el nombre, editar o eliminar; «Añadir a mi escena» crea una copia en su propia escena abierta. El inspector sigue correspondiendo a su escena actual, nunca al original de la biblioteca ajena. Las restricciones para eliminar cuentas permanecen en la superficie existente de cuentas SP-2; esta exploración no agrega una página de administración de cuentas.

## 3. Superficie existente, composición y elección de miniatura

Referencias de producción de solo lectura: `src/app/globals.css` de ambos repositorios; `src/app/layout.tsx` de t12; `src/components/tres-d/Biblioteca.tsx` (`AccionesPieza`, `Ficha`, `FiltrosCompactos`, biblioteca local); sus consumidores en el Taller. Los controles existentes proporcionan «Guardar en mi biblioteca», «Guardar toda la escena en mi biblioteca», «Nombre», «Ocasión», «Añadir a mi escena» y el vocabulario de filtros de ocasión/color/globo.

Referencias de proyectos hermanos: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html`, `proyectos@v1.md/.html` y la fuente seleccionada de proyectos `proyectos@v1.r12.dir-c.tsx`. Se conservan la marca de anillo y punto de Pictures, el logotipo de Sempertex, los controles de cuenta/idioma, el título de tarea de 24px, la navegación horizontal neutral Taller 3D / Proyectos y el vocabulario de herramientas/lienzo/inspector del taller. Los destinos del menú de cuenta y de proyectos fuera de SP-5 muestran un aviso de alcance de la maqueta en vez de simular la implementación de esos subplanes.

Se dibujaron dos composiciones HTML reales antes del TSX completo:

- **Candidata 1, elegida:** barra, lienzo e inspector existentes sobre una sección de miniaturas adjunta. Los campos para guardar una pieza permanecen junto a la escena actual. Sus miniaturas abren un detalle debajo de la sección. Conserva el inspector de escena existente y mantiene la biblioteca como complemento contextual.
- **Candidata 2:** columna de biblioteca a la izquierda de la escena y formulario para guardar debajo del lienzo. Ocupa el espacio que normalmente usa el diseño de escena existente y separa los controles para guardar piezas del inspector de escena. Se ajusta menos a este encargo.

El artefacto completo desarrolla la candidata 1; ambos archivos de miniaturas siguen disponibles. Los HTML de miniaturas son intencionalmente bocetos pequeños de composición; la cobertura completa de estados interactivos, ambos temas, la composición de la biblioteca real y la evidencia de auditoría corresponden al HTML compilado, no a los bocetos.

## 4. Sistema visual fijo y ocho ejes

Tokens exactos de producción, tema claro / oscuro: `--fondo` #faf9fc / #0b0c10; `--superficie` #ffffff / #16181f; `--superficie-suave` #faf8fd / #1c1e26; `--superficie-2` #efe9f8 / #242733; `--borde` #e3daef / #383c48; `--texto` #1c1425 / #f4f5f7; `--texto-suave` #6b6178 / #9aa1ad; `--texto-tenue` #766c85 / #8a91a0; `--acento` #6d3fe0 / #9479ff; `--sobre-acento` #ffffff / #120b24. Los colores de éxito/error/advertencia y de la escena del taller también provienen de `globals.css`. No se propone una paleta ni una familia tipográfica nuevas.

Correspondencia del kit: fondo→fondo, card/popover→superficie, foreground→texto, muted/secondary→superficie-2, muted-foreground→texto-suave, primary/ring→acento, primary-foreground→sobre-acento, input→texto-tenue, destructive→error, success→exito, warning→aviso. Los separadores no esenciales usan borde; los bordes significativos de controles usan texto-tenue. Los recursos WOFF2 locales existentes de Geist Sans / Geist Mono se incrustan para funcionar sin conexión. Se mantienen las formas de los elementos de los proyectos hermanos: panel 32px, recuadro 24px, campo 18px y píldora 999px.

| Eje | Dirección C, observable en el artefacto |
|---|---|
| Concepto | Guardar la pieza/escena actual y reutilizar elementos guardados dentro del Taller de trabajo existente. |
| Diseño | La barra, la escena y el inspector permanecen sobre una sección de biblioteca de tres columnas. Una tarjeta seleccionada despliega una vista previa y un área de metadatos/colocación debajo de la sección. |
| Navegación | Al seleccionar el lienzo se abre el formulario del inspector; los botones de las tarjetas expanden/contraen sus detalles; las entradas locales y los filtros de color/globo usan secciones nativas desplegables. Se mantienen las rutas horizontales del producto. |
| Tipografía | Geist existente: título 24px, biblioteca 20px, detalle 18px, nombre del elemento 15px, controles 14px y texto complementario 12–13px. Geist Mono se limita a Sempertex. |
| Densidad | Cada tarjeta compacta comparte miniatura, identidad y acceso a la ficha. Los formularios para guardar y editar metadatos solo aparecen cuando se solicitan. No se agregan paneles, tarjetas KPI ni material promocional. |
| Componentes | Button, Input y Skeleton instalados de shadcn/Base UI; AlertDialog de Animate UI para eliminar. Los selectores y elementos details nativos conservan la semántica de filtros y secciones desplegables. |
| Color | El acento existente identifica el guardado/la colocación y los elementos seleccionados. La navegación permanece neutral; el éxito confirmado y los errores usan los colores semánticos de producción junto con texto. |
| Movimiento | Compresión táctil y retorno a la posición inicial, secuencia finita de miniaturas de 480ms con intervalos de 50ms, despliegue articulado del formulario/detalle y sello de éxito. Las acciones repetidas usan respuesta de 180ms. La compatibilidad con movimiento reducido es explícita. |

Importaciones reales: `@/components/ui/button` (`shadcn:button default/outline`, normal/hover/focus/pressed/disabled), `@/components/ui/input` (`shadcn:input`, editable/invalid/disabled), `@/components/ui/skeleton` (carga), `@/components/ui/alert-dialog` (`shadcn:alert-dialog` con transiciones instaladas de Animate UI). Composición personalizada: `.studio-body`, `.inline-save`, `.library-grid`, `.piece-detail`; las ilustraciones SVG de escenas/miniaturas son ejemplos visuales, no un renderizador WebGL ni una función de generación de miniaturas.

## 5. Detalles de interacción y movimiento

Al hacer clic en la pieza con nombre de la escena o en «Guardar en mi biblioteca», se muestra el formulario junto a la escena y el foco pasa al campo del nombre. «Guardar toda la escena en mi biblioteca…» usa la misma ubicación con el alcance de escena completa. Los campos permanecen montados mientras se escribe. Si al quitar los espacios el nombre queda vacío, se muestra un error asociado; un envío válido desactiva los envíos duplicados y muestra «Guardando…». Solo la confirmación simulada cambia ese texto a «Guardado en tu biblioteca.» y agrega el elemento con nombre.

Cada miniatura es un botón de teclado con `aria-expanded`/`aria-controls`. Como máximo, un detalle puede estar expandido. La edición del nombre y la ocasión ocurre junto a la vista previa de ese elemento; Cancelar conserva los metadatos originales. La colocación inserta una copia ilustrativa y anuncia que el original no cambia. Para eliminar, se requiere el AlertDialog real; las copias de proyecto se conservan y, al cancelar, el foco vuelve al control que abrió el diálogo o, después de eliminar, al encabezado de la biblioteca.

El gesto táctil comprime una tarjeta a .975 o un control a .965 antes de devolverlo a su posición. Los fotogramas clave CSS de las tarjetas las mueven 8px hacia abajo → 2px hacia arriba → reposo, con `cubic-bezier(.34,1.4,.64,1)` y una secuencia finita de 480ms. Los formularios para guardar/detalles se despliegan desde arriba 6px, sin desaparecer detrás de la opacidad. El sello de éxito pasa de .96 → 1.02 → 1. Los perfiles de movimiento natural/sutil reducen las duraciones y los intervalos. El perfil de movimiento instalado proporciona los resortes al presionar/colocar. Las pestañas ocultas pausan los efectos CSS. El movimiento reducido del sistema operativo, Quieto y `?still=1` eliminan las transiciones/desplazamientos y conservan todas las palabras de estado y acciones; no se agrega animación continua a la escena.

## 6. Flujos

1. **Guardar:** seleccionar una pieza o la escena completa → revisar el alcance y el destino → ingresar el nombre y la ocasión → enviar → pendiente → confirmación y nuevo mosaico. Si falla, se conserva la información ingresada y se ofrece “Reintentar guardado”. En producción, el elemento confirmado es el elemento del servidor propiedad de la cuenta; el HTML usa un fixture explícito en memoria.
2. **Buscar y colocar:** buscar por nombre y filtrar por ocasión/tipo; mostrar los filtros de color y globos cuando sea necesario → elegir un mosaico → revisar la vista previa → “Añadir a mi escena” → confirmación de que se colocó una copia en el proyecto propio. Las acciones para borrar la búsqueda o los filtros restauran la lista permitida.
3. **Actualizar o quitar como propietario:** expandir un mosaico propio → cambiar el nombre o la ocasión en el lugar → confirmar; o solicitar que se quite → confirmar/cancelar. Los controles ocupados impiden una segunda modificación. El comportamiento de reemplazo de contenido es una pregunta abierta más abajo, no un control inventado.
4. **Consulta del personal:** Vista selecciona el fixture del personal → elegir un propietario autorizado → expandir un elemento ajeno → consultar el original en modo de solo lectura → colocar una copia en el proyecto actual del miembro del personal. No aparece ningún control para editar o quitar elementos ajenos. El selector de propietario del prototipo es ilustrativo y nunca concede autorización.
5. **Entradas locales del navegador:** abrir explícitamente “En este navegador” → ver el fixture exclusivo del navegador y colocarlo si se desea. No existe ninguna acción de importación, estado de progreso ni estado de error. El mockup nunca escribe ni migra `taller3d:biblioteca-propia:v1`.
6. **Cambio de cuenta/cierre de sesión:** el control de cuenta del Mockup cambia de cuenta → se quitan los mosaicos anteriores, el detalle abierto, el formulario de guardado y el contexto de la escena → superficie de carga → biblioteca propia de la cuenta actual. Al cerrar sesión, se ocultan el taller y la biblioteca. No se muestra la lista del servidor de la cuenta anterior mientras se carga la cuenta siguiente.

## 7. Vistas y controles visibles

La Vista nativa expone `library` (Mi biblioteca), `save-piece` (Guardar pieza), `save-scene` (Guardar escena), `staff` (Personal · Solo lectura). Todas son vistas del mismo contenedor de Taller; no se introduce una página de inicio decorativa ni una nueva ruta global. El Diálogo nativo expone ninguna opción o `delete`. El Tema nativo expone claro/oscuro; Idioma ofrece ES/EN para comprobar la expansión. Las etiquetas del Mockup permanecen fuera del producto.

La jerarquía de la biblioteca es identidad/alcance → búsqueda por nombre y selectores de ocasión/tipo → filtros existentes de color/globos, que se muestran cuando corresponde → miniaturas al mismo nivel → detalle del elemento seleccionado → grupo independiente exclusivo del navegador. Un mensaje de carga/error/vacío reemplaza la lista del servidor sin inventar resultados. El personal ve el contexto del propietario autorizado y el alcance de solo lectura; el propietario ve “En mi cuenta”. En el fixture ajeno, el inspector de la escena actual permite guardar la propia escena del miembro del personal; no edita el original de la biblioteca.

## 8. Cobertura de estados

Todos los estados declarados se pueden alcanzar mediante Estado nativo. Las combinaciones de vista/estado que corresponden a otra superficie conservan el contexto sin inventar una regla de permisos.

| Estado | Comportamiento visible y recuperación |
|---|---|
| `normal` | Elementos permitidos de la cuenta simulada; seleccionar, buscar, filtrar y colocar. Los formularios solo aparecen en las vistas específicas de guardado. |
| `loading` | Lista esqueleto y “Cargando biblioteca…”; sin filas ni recuentos de elementos guardados. |
| `empty` | La lista de elementos de la cuenta en el servidor está vacía; el propietario puede guardar desde la escena actual. Las entradas exclusivas del navegador permanecen separadas. Una lista vacía para personal ofrece orientación para seleccionar un propietario. |
| `error` | Error al cargar la lista y acción Reintentar; no se inventa una lista exitosa. |
| `saving` | Se desactiva el guardado duplicado; formulario ocupado y mensaje Guardando; no se afirma que el guardado se completó. |
| `saved` | Fixture explícito de guardado confirmado; texto de éxito con marca de verificación. El guardado interactivo normal solo llega a este estado después del temporizador de confirmación. |
| `save-failed` | Se conserva la información ingresada; se muestra el error y la opción de reintentar; al reintentar, pasa al estado pendiente y luego se confirma. |
| `no-results` | No hay coincidencias y se ofrece borrar la búsqueda para recuperar resultados; es distinto de una biblioteca de cuenta vacía. |
| `editing` | Ficha del propietario expandida y formulario en línea para nombre/ocasión. El personal nunca obtiene ese formulario. |
| `validation` | Mensaje de nombre no válido asociado al campo, que se corrige mediante la entrada; un envío fallido nunca se convierte en un elemento guardado. |
| `account-switch` | Se quitan los datos de la cuenta anterior; solo se muestra la superficie de carga de la cuenta actual. Al continuar en el Mockup, aparece una segunda cuenta vacía. |
| `permission-denied` | No se muestran datos del taller, la escena ni la biblioteca personal; explicación sobre el acceso al Taller. |
| `session-expired` | Explicación de que la sesión terminó; no se muestran metadatos de la escena ni de la biblioteca. |
| `delete-failed` | El original permanece; el error y la opción para reintentar la eliminación vuelven a abrir la confirmación. |

Los controles incluyen estados al pasar el cursor, presionado, con foco visible, deshabilitado y ocupado. Las acciones de importar, el progreso de importación y los errores de importación están deliberadamente ausentes. La falta de conexión se asigna al error correspondiente de lista/guardado y muestra una opción explícita para reintentar; el artefacto no promete que las operaciones sin conexión tengan éxito. El catálogo global, la eliminación de cuentas, la paginación del servidor, el guardado automático, las compras y los estados del proveedor quedan fuera del alcance de UI de esta propuesta.

## 9. Comportamiento adaptable

Rango de diseño admitido: desde 360px; puntos de control de auditoría visual: 390/768/1280px, con ambos temas. A partir de 1100px, se conserva la barra de 60px, la escena flexible y el inspector de 310px; la biblioteca tiene tres columnas, y la búsqueda comparte una fila con los selectores nativos. Entre 640 y 1099px, se conservan la barra y el lienzo, el inspector pasa debajo de la escena, su formulario se distribuye en dos columnas, la biblioteca usa dos columnas y la búsqueda pasa arriba de los demás filtros. Entre 360 y 639px, se oculta la barra, se apilan escena → inspector → biblioteca, los campos, mosaicos y detalles usan una columna, las acciones de encabezado y título pueden pasar a otra línea, y las acciones del diálogo destructivo se apilan. La escena permanece dentro de su marco delimitado.

Los márgenes exteriores son de 40px en escritorio, 24px en tableta y 20px en teléfono. El relleno de la biblioteca es de 28px en escritorio y 20px en teléfono. Las etiquetas largas y la expansión en inglés se ajustan a varias líneas; la página no tiene desplazamiento horizontal. Los estados más extensos de guardado/error/detalle se desplazan verticalmente sin ocultar acciones. AlertDialog limita su altura al alto de la ventana menos 48px y su ancho al ancho de la ventana menos 40px, con un máximo de 540px. En un Taller alto en funcionamiento, la biblioteca aparece después del lienzo; se accede a ella mediante el desplazamiento vertical normal, no a través de una segunda ruta.

## 10. Objetivos de accesibilidad

Objetivo: cumplir los criterios aplicables de WCAG 2.2 AA; estas comprobaciones no certifican la conformidad de producción. Los encabezados, la navegación/ruta actual, las etiquetas, los campos no válidos asociados, el estado cortés de guardado/colocación y las alertas de error con acciones son semánticos. Los mosaicos y controles de divulgación admiten el uso con teclado. El foco se indica con un contorno de acento del producto de 3px y un desplazamiento de 4px. Los botones y campos tienen como objetivo una altura mínima de 44px. El texto tiene como objetivo una relación de contraste ≥4.5:1; los bordes/focos significativos, ≥3:1; el color se acompaña de palabras. Los mosaicos seleccionados exponen su estado expandido y un detalle asociado.

Usar el comportamiento modal instalado para el fondo inerte, la contención del foco, Escape y el retorno del foco. Las modificaciones ocupadas no se pueden descartar como si se hubieran completado. Los campos de guardado reciben el foco al abrirse y lo conservan mientras se escribe. Al cancelar la eliminación, el foco vuelve al control que la inició; si se completa, el foco pasa al encabezado de biblioteca que permanece. El comportamiento con movimiento reducido conserva la finalización de la tarea y el estado visible. Las pruebas con lectores de pantalla, el zoom y el comportamiento real de WebGL/API/permisos en producción siguen siendo responsabilidades de aceptación de la implementación.

## 11. Aceptación visual y verificación real

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | 360px+ | Todos | Pictures/Sempertex, Geist, los controles de idioma/cuenta y la navegación neutral Taller/Proyectos conservan el vocabulario de las vistas hermanas. |
| C-AC-02 | 1100px+ | Normal | La escena y el inspector permanecen sobre una estantería de miniaturas de tres columnas. |
| C-AC-03 | 640–1099px | Normal | El inspector aparece después de la escena y la estantería tiene dos columnas. |
| C-AC-04 | 360–639px | Normal / error | Los campos, mosaicos y detalles se apilan sin desbordamiento horizontal de la página. |
| C-AC-05 | Todos | Guardar pieza / escena | El alcance indicado, el destino de la cuenta, el nombre y la ocasión aparecen en el inspector. |
| C-AC-06 | Todos | Guardando | Guardando está visible y el guardado duplicado está deshabilitado; no aparece texto de guardado confirmado. |
| C-AC-07 | Todos | Error al guardar | Los metadatos ingresados permanecen junto a Reintentar guardado. |
| C-AC-08 | Todos | Ficha de personal expandida | Solo lectura está visible; no aparecen los controles para renombrar/editar/quitar el original. |
| C-AC-09 | Todos | Colocación | Aparece una copia en la escena simulada y el mensaje indica que el original no cambia. |
| C-AC-10 | Todos | Cambio de cuenta / cierre de sesión | No aparecen los mosaicos anteriores del servidor, la ficha seleccionada ni el formulario de guardado. |
| C-AC-11 | Todos | Grupo local abierto | Las entradas exclusivas del navegador tienen su propia explicación y no hay acción de importación. |
| C-AC-12 | Todos | Carga / vacío / error | El esqueleto, la orientación para listas vacías o la explicación de reintento reemplazan la lista del servidor, según corresponda. |
| C-AC-13 | Todos | Filtros abiertos | Los selectores existentes de color y globos siguen etiquetados, se pueden usar con teclado y se pueden borrar. |
| C-AC-14 | Todos | Diálogo de eliminación | Cancelar conserva el elemento y devuelve el foco; confirmar la eliminación quita únicamente ese elemento. |
| C-AC-15 | Todos | Movimiento reducido / Quieto / estático | El contenido final y las palabras de estado permanecen mientras desaparecen el desplazamiento y los efectos continuos. |

Evidencia del HTML final de esta propuesta:

| Comprobación | Resultado real |
|---|---|
| Kit real instalado | `installed=True built=True entries ok=96/96`. |
| Compilación sin conexión | Código de salida 0; 639 KB, 2,132 archivos fuente empaquetados. React, los controles instalados reales y ambas fuentes locales están insertados. No se instalan paquetes ni se obtienen recursos. |
| Contraste de tokens | Código de salida 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría visual final | Código de salida 0: 360 renderizados / 360 combinaciones planificadas; 16,092 mediciones de texto y 2,322 paradas de foco a 1280/390/768px con ambos temas, sin muestreo. |
| Divulgaciones ampliadas de filtros/locales | `EXPANDED DISCLOSURES: PASS 4 renders`, 390/1280px en tema claro/oscuro, usando las sondas de renderizado reales de la auditoría. |
| Interacciones específicas | `INTERACTIONS: PASS 15 groups; 0 page errors; 0 external HTTP(S) requests`. Incluye foco/validación de entrada, guardado pendiente→confirmado, reintento, actualización de metadatos, filtros/búsqueda, separación local, modo de solo lectura/colocación de personal, cambio de propietario, cancelación/eliminación con retorno del foco/confirmación, cambio de cuenta/cierre de sesión y reflujo en inglés a 360/390/768/1280px con ambos temas. |
| Prueba de movimiento | A los 120ms: 3 animaciones expresivas activas, 0 con movimiento reducido del sistema operativo y 0 con `?still=1`. |
| Evidencia por eje | `compare_directions.py` en este artefacto: `RESULT: PASS`, `evidence_ok=true`, sin selectores faltantes. Esta comprobación de selectores de una sola propuesta no afirma que exista distinción por pares. |
| Inspección visual | Se inspeccionaron ambas composiciones candidatas, predeterminadas a 1280/390px en tema claro/oscuro, la ficha de personal expandida a 1280px en tema oscuro y el error de guardado a 390px en tema claro, mediante capturas en memoria. No se agregaron archivos de captura. |

`RESULT: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento`

La auditoría inicial devolvió `RESULT: FAIL — alignment 18`: el recuadro anidado del mensaje de lista vacía/error en teléfono creó un eje de alineación incoherente. El mensaje de lista se aplanó para alinearlo con el eje existente de la estantería; luego, la compilación y la auditoría completa finales pasaron. Una compilación inicial de la composición TSX detectó un error de sintaxis en una llamada auxiliar JSX; se corrigió antes del renderizado. Ninguna de las comprobaciones se omitió, se redujo mediante muestreo ni se reclasificó como aprobada.

Reproducción:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
python3 /home/david/bitacora/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/bitacora/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html --widths 1280,390,768
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/bitacora/skill/agents/designer/skills/david-ui-kit/kit/compare_directions.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/decoraciones@v1.r2.dir-c.html
```

## 12. Preguntas abiertas, límites e impacto

P: ¿Al actualizar una decoración guardada propia, se debe reemplazar su composición por la pieza/escena actual o solo cambiar su nombre y ocasión? Responsable: David/Planner. Esta exploración muestra los controles de metadatos confirmados y no inventa un comportamiento de reemplazo de contenido.

Confirmado: las decoraciones locales del navegador no se importan; solo el propietario actualiza o elimina los originales; el personal crea una copia al colocarla; la biblioteca personal requiere Taller; el estado de guardado espera una confirmación; los cambios de cuenta eliminan los elementos anteriores del servidor. Las dos opciones del selector de propietario del personal son datos neutros de prueba, no un rol o permiso nuevo ni una afirmación sobre la API de lista de cuentas.

Límites de los datos de prueba: los temporizadores en memoria ilustran las confirmaciones del servidor; la persistencia entre recargas o navegadores, las consultas autorizadas al servidor, la identidad de la cuenta, el aislamiento real del almacenamiento, la idempotencia de los reintentos y la fidelidad del contenido no están implementados ni demostrados por este HTML. Los datos de prueba de colores y globos están etiquetados explícitamente como ejemplos, no como afirmaciones sobre el catálogo. La clave real del navegador heredado permanece intacta. No se usaron servidores de aplicaciones, proveedores de pago ni credenciales. No se ejecutó el conjunto de pruebas/lint/typecheck/build de producción porque ambos repositorios son de solo lectura y el código de producción no se modificó.

Impacto: superficies de guardado/listado/detalle/personal/locales/cambio de cuenta de SP-5 Taller, futuros T5.1/T5.3/T5.5. La compatibilidad está **sin determinar hasta que se seleccione y apruebe**; la exploración cambia la jerarquía, la divulgación de información y la disposición adaptable con respecto a la biblioteca local actual, por lo que la implementación requerirá adaptación. Se reutilizan el shell, los tokens, las fuentes y la navegación de proyectos hermanos; no se redirige ninguna referencia de consumidores. El contrato canónico, la aprobación independiente, la implementación de producción, las garantías de API y la comparación entre direcciones siguen a cargo de sus responsables asignados.

INQUIETUDES: la pregunta sobre el responsable indicada arriba; borrador de exploración, no aprobado. No hay alternativa de cadena de herramientas ni fuente de tokens faltante. La auditoría final del artefacto pasó; sus evidencias se aplican únicamente a este artefacto estático de planificación.
