# decoraciones@v1 · r1 · Dirección A — Biblioteca de trabajo

Borrador de exploración para REQ-021 / SP-5 “Decoraciones guardadas” (R8). No es un contrato ni está aprobado. El propietario compara las direcciones; solo quien finalice la dirección elegida escribe `decoraciones@v1.md`.

Archivos: `decoraciones@v1.r1.dir-a.tsx` (entrada), `decoraciones@v1.r1.dir-a.html` (maqueta generada),
`decoraciones@v1.r1.dir-a.json` (ejes + evidencia del selector), miniaturas `…dir-a.html.candidate-1.html` y
`…candidate-2.html`.

## Superficie existente modificada

Ubicada en modo de solo lectura en t12 (`/home/david/dev/pictures-wt/t12`): `src/components/tres-d/Biblioteca.tsx`
(biblioteca localStorage `taller3d:biblioteca-propia:v1`, formulario de guardado `AccionesPieza` con Nombre + Ocasión,
«Guardar en mi biblioteca», «Guardar toda la escena en mi biblioteca», `FichaDialogo` con «Abrir en Escena»,
«Añadir a mi escena», «Quitar de mi biblioteca»), `PanelAnadir.tsx` (panel «Añadir a la escena»: búsqueda
«Buscar: columna, flor, dorado…», pestañas Estructuras/Decoraciones/Utilería/Ideas, filtro «Ocasión: todas») y
`ui-taller.ts` / `globals.css` (tokens `--taller-*`, botones Taller de 36–44px, `taller-rotulo`). El contenedor de la aplicación
(masthead, Idioma, Mi cuenta, regla de rutas Taller 3D / Proyectos, encabezado de guardado del Taller) se reutiliza de los proyectos hermanos
`proyectos@v1` (dirección c elegida) y `cuentas-admin@v1` / `planes@v1`, con los mismos tokens y fuentes Geist.

Lo que cambia esta dirección, y solo esto:

1. **Una quinta pestaña «Mi biblioteca»** en el panel existente «Añadir a la escena» muestra la biblioteca personal de la cuenta
   como una lista compacta agrupada por los tipos de elementos existentes (Escenas, Estructuras, Decoraciones, Utilería), con una línea de resumen
   «N en tu cuenta · Al día con tu cuenta». Los elementos propios siguen apareciendo en las otras pestañas con la marca «Tu biblioteca»
   (etiqueta `Fuente` existente), así que no se pierde nada del flujo actual.
2. **La ficha pasa a la columna del inspector** (vista maestra-detalle) en lugar de cubrir la escena: miniatura, nombre,
   tipo/ocasión, globos, una línea de propiedad y las acciones existentes. «Ver ficha completa» sigue abriendo el `FichaDialogo` completo existente
   (productos, fuente), que se muestra como aviso de maqueta.
3. **Guardar en la cuenta**: el formulario existente del inspector (Nombre, Ocasión, Guardar) ahora indica el destino: «Se guarda
   en tu cuenta…». Mientras se guarda, la fila aparece en la lista con un indicador giratorio y «Guardando…», nunca con una marca de verificación; solo la
   confirmación agrega la marca y el mensaje «Guardado en tu biblioteca: «…» (tipo). Está en tu cuenta.»
4. **Controles solo para el propietario**: cambiar el nombre (lápiz → campo en línea, Escape/Cancelar devuelve el foco) y «Quitar de mi
   biblioteca» (AlertDialog). El personal con «Biblioteca de: Cuenta de ejemplo» ve un candado por fila, «Solo lectura» y
   no tiene opciones para cambiar el nombre ni eliminar.
5. **Las entradas locales del navegador siguen siendo locales**: un grupo plegado «Solo en este navegador · N» debajo de la lista de la cuenta explica
   que no se importan durante el piloto y no son visibles en otros navegadores; su ficha conserva las acciones de ubicación existentes
   y «Quitar de este navegador», sin opción de importación.
6. **Cambio de cuenta / cierre de sesión**: la lista se reemplaza por esqueletos («Cargando la biblioteca de la cuenta elegida…»);
   las filas de la cuenta anterior no permanecen en pantalla.

## Interacción y movimiento

Gramática: cortes rápidos y precisos, solo desaceleración (`cubic-bezier(.2,0,0,1)`), sin sobreimpulso; deliberadamente distinta de los
resortes táctiles del proyecto hermano porque esta es una herramienta de uso frecuente basada en listas.

| Movimiento | Expresivo | Natural | Sutil |
|---|---|---|---|
| Las filas entran con `translateX(-8px)→0`, escalonadas | 150ms, +16ms/fila | 120ms, +10ms | 90ms, +5ms |
| El cuerpo de la ficha cambia al seleccionar otra fila `translateY(6px)→0` | 150ms | 120ms | 90ms |
| El texto de sincronización / los avisos avanzan con `translateY(-4px)→0` | 150ms | 120ms | 90ms |
| Fila recién confirmada: barra inferior `scaleX(0→1)` en taller-valido | 260ms | 200ms | 140ms |
| El indicador de pestaña (Motion `layoutId`) se desliza entre pestañas | 150ms | 120ms | 90ms |
| Indicador giratorio solo mientras hay un guardado/cambio de nombre/eliminación pendiente | 900ms/vuelta | igual | igual |

Al presionar: los botones se desplazan 1px hacia abajo; al pasar el cursor cambia el nivel de superficie del Taller. El movimiento reducido del sistema operativo, «Quieto» y
`?still=1` eliminan todas las animaciones y transiciones, pero conservan todas las palabras y controles; las pestañas ocultas pausan las animaciones CSS.
El contenido nunca se oculta durante una animación (sin entradas con opacidad).

Teclado: las filas tienen un botón con el nombre (`aria-pressed`) y un botón independiente «Añadir a mi escena: <name>»; Cerrar la
ficha devuelve el foco a su fila; el AlertDialog mantiene el foco dentro y Escape devuelve el foco a «Quitar de mi biblioteca»;
la búsqueda conserva el foco mientras se escribe (verificado con una prueba).

## Por qué encaja con el producto

La biblioteca personal ya está en el panel «Añadir» y en el inspector del Taller; esta dirección la mantiene ahí,
agrega la ubicación que R8 necesita para encontrar elementos de la cuenta y mantiene visible la escena mientras se colocan, que es la tarea principal
(«poner mi elemento guardado en este proyecto»). La densidad, las etiquetas de grupo `taller-rotulo` existentes y los botones Taller de 40px
coinciden con el vocabulario de trabajo del editor; el contenedor es idéntico, hasta el nivel de bytes, al de los proyectos hermanos.

## Ocho ejes

| Eje | Lo observable en la maqueta |
|---|---|
| concepto | La biblioteca como lista de trabajo dentro del Taller: quinta pestaña «Mi biblioteca» + ficha en el inspector; el guardado confirma solo lo que aceptó la cuenta. |
| diseño | Columnas de escritorio de 60 / 330 / lienzo / 300px; en tableta: la ficha pasa a ser una franja de ancho completo (miniatura de 200px + detalle) debajo del panel y el lienzo; en teléfono: fila de navegación, lienzo, panel y ficha apilados. |
| navegación | Masthead compartido y regla Taller 3D/Proyectos; pestañas segmentadas con indicador deslizante compartido; fila → ficha en el mismo lugar, Cerrar vuelve a la fila; selector nativo «Biblioteca de» para el personal. |
| tipografía | Geist: H1 24px, panel 15px, nombre de ficha 18px, nombre de fila 14px/600, metadatos 12–13px, etiquetas de grupo en mayúsculas de 11px (el `taller-rotulo` existente), conteos en Geist Mono. |
| densidad | Filas de 52px (56px en teléfono) con miniatura de 44×36, tipo·ocasión, icono de estado y botón para añadir de 40/44px; conteos agrupados; grupo local plegado. |
| componentes | Input, Skeleton, Button y AlertDialog reales (shadcn/Base UI/Animate UI), Motion `layoutId`; filas personalizadas, ficha, sección local desplegable, formulario de guardado con estilos de botones Taller. |
| color | Solo tokens de Pictures/Taller: color primario en Añadir a mi escena/Guardar; taller-valido = guardado en la cuenta; taller-medio = local / solo lectura; error al quitar y en los fallos. |
| movimiento | Cortes rápidos con desaceleración: entrada escalonada de filas, cambio de ficha, avance de sincronización, barrido de confirmación, indicador de pestaña deslizante; escala según el perfil; paridad con movimiento reducido/quieto. |

## Vistas, estados y diálogo de la maqueta

Vista: «Taller · Mi biblioteca», «Taller · Guardar en mi biblioteca», «Taller · Biblioteca de otra cuenta (personal)».
Estado: Al día, Cargando, Vacía, Error al cargar, Sin conexión, Solo en este navegador, Guardando, Guardado en tu
cuenta, Error al guardar, Rechazado por la cuenta, Cambiando el nombre, Error al cambiar el nombre, Quitando, Error al
quitar, Cambio de cuenta, No disponible, Sesión terminada. Diálogo: «Quitar de mi biblioteca». Pares con significado:
estados de guardado con la vista de guardado; estados de cambio de nombre/eliminación con la vista de biblioteca; Cambio de cuenta con cualquier vista.

## Miniatura elegida

**Candidato 1** (pestaña en el panel «Añadir» + ficha en el inspector). El candidato 2 (bandeja de tabla ordenable debajo del
lienzo) reduce el lienzo, pierde columnas en el teléfono y aleja la biblioteca de donde está actualmente.

## Preguntas abiertas (para el propietario)

- P: ¿Pueden los empleados/administradores colocar en su propia escena un elemento guardado de otra cuenta (Añadir a mi escena / Abrir en Escena) mientras sigue siendo de solo lectura? La maqueta lo permite.
- P: ¿Las entradas locales del navegador «Solo en este navegador» deben seguir visibles en el Taller (maqueta: grupo plegado con opciones para colocar y quitar de este navegador) u ocultarse?
- P: Cambiar el nombre aparece en T5.3, pero no existe en el `Biblioteca.tsx` actual; confirmar si cambiar el nombre por el propietario debe incluirse en el piloto (maqueta: en línea en la ficha, límite de 120 caracteres tomado de proyectos@v1).
- P: ¿Desde dónde abre el personal la biblioteca de otra cuenta: desde el selector «Biblioteca de» en el Taller (maqueta) o desde la pantalla de cuentas/proyectos ajenos?
- P: PLAN T5.4/T5.5 todavía menciona importar entradas heredadas y un estado de «importación», en contradicción con SPEC, ronda 11, y T5.3 (sin importación); la maqueta sigue SPEC (sin interfaz de importación).
- P: Al quitar un elemento de la biblioteca, ¿se debe indicar algo sobre los proyectos donde ya se había colocado? La maqueta indica que no cambian (al colocarse se copia el contenido, como hoy).

## Auditoría (resultados reales, compilación final)

- Compilación: `bitacora.py components mockup build … --out decoraciones@v1.r1.dir-a.html` → 660 KB, 2132 archivos de origen, sin conexión.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (código de salida 0).
- `audit_mockup.py --widths 1280,390,768`: 324 renderizados / 324 previstos, 15678 mediciones de texto, 2847 paradas de foco.
  `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- En ejecuciones anteriores se encontraron y corrigieron: relleno vertical de botón de 7px (<8px) en la vista de guardado; pestaña «Decoraciones» que se partía
  a mitad de palabra a 390px; acción destructiva de AlertDialog que se mostraba con el color de acento.
- Prueba (Playwright en línea, capturas de pantalla solo en /tmp): la búsqueda conserva el foco al escribir; al seleccionar una fila se muestra su ficha; se abre el AlertDialog de eliminación y Escape devuelve el foco a «Quitar de mi biblioteca»; al colocar se muestra «Añadida a tu escena»; al guardar aparece una fila pendiente con indicador giratorio y luego la confirmación; la vista del personal no ofrece opciones para cambiar el nombre ni eliminar; 7 animaciones en curso a ~60ms en modo expresivo, 0 con `?still=1`; cero solicitudes externas. Se inspeccionaron capturas de pantalla: biblioteca clara a 1280, guardado oscuro a 1280, elemento local claro a 768, biblioteca oscura a 390, diálogo de eliminación claro a 390.
- No se comprobó: persistencia real, comportamiento entre navegadores, aplicación de permisos de propiedad, borrado al cambiar de cuenta; corresponden a T5.2–T5.4 y las auditorías.
