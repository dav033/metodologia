---
contract: decoraciones
version: 1
status: draft
subplan: SP-5
requirements: [R8]
owner: David
author: Designer (Claude)
date: 2026-10-29
direction: c
name: Manipulación directa
source_revision: r1
source_behavior: decoraciones@v1.r1.behavior.md
---

# Manipulación directa — decoraciones@v1 · r1 · C

**Solo exploración; borrador, no aprobado ni contrato de implementación.** Esta nota acompaña a
`decoraciones@v1.r1.dir-c.tsx`, el archivo generado `decoraciones@v1.r1.dir-c.html`, dos miniaturas candidatas y el JSON de ejes.
No escribe los archivos canónicos `decoraciones@v1.md`/`.html`, SPEC, PLAN ni ningún repositorio. El propietario elige entre
las direcciones; después, quien finalice la dirección escribe el contrato de doce secciones.

## Alcance y superficie existente

Alcance: el informe de interfaz `decoraciones@v1.r1.behavior.md` (R8 y SPEC «Behavior — SP-5 (round 11 answered)»). Superficie existente, ubicada en modo de solo lectura en `pictures-wt/asesor`:

- `src/components/tres-d/Biblioteca.tsx` — `AccionesPieza` en el inspector: «Ver sola / Ver con sus decoraciones»,
  «Guardar en mi biblioteca», el enlace «Guardar toda la escena en mi biblioteca», formulario en línea Nombre + Ocasión + Guardar
  y línea de estado «Guardado en tu biblioteca: «X» (tipo).». La persistencia actual es `taller3d:biblioteca-propia:v1`
  en `localStorage`. `FichaDialogo`/`Ficha`: «Abrir en Escena», «Añadir a mi escena», «Quitar de mi biblioteca»,
  «De dónde viene», productos, «Volver a la biblioteca».
- `PanelAnadir.tsx` — panel «Añadir a la escena» con búsqueda y los segmentos Estructuras · Decoraciones · Utilería ·
  Ideas; los elementos propios se mezclan en esas pestañas con la etiqueta de origen «Tu biblioteca» (`GrillaCompacta.tsx`).
- `MenuContextual.tsx` «Guardar en mi biblioteca» y `MenuMas.tsx` «Guardar la escena en mi biblioteca…» (mismo formulario).
- Tokens: `src/app/globals.css` (`--fondo`… y `--taller-*`), Geist/Geist Mono; contenedor, masthead, navegación de rutas,
  encabezado del taller y mapa de tokens reutilizados exactamente de los proyectos hermanos `proyectos@v1` (dirección C elegida) y
  `cuentas-admin@v1`/`planes@v1`. Sin paleta, fuente ni marca nuevos.

## Enfoque — cómo esta dirección cambia la superficie

Los controles modificados se manipulan donde ya están:

1. **Guardar en el mismo lugar.** «Guardar en mi biblioteca» en el inspector despliega el formulario existente dentro del inspector (sin
   diálogo). El formulario agrega una línea de destino: «Se guarda en tu cuenta: la verás en «Mi biblioteca» desde cualquier
   navegador.» Guardar → «Guardando…» (deshabilitado) → confirmación «Guardado en tu biblioteca: «Arco» (estructura con
   decoraciones).» con «Ver en Mi biblioteca», que mueve el foco a la fila nueva. Las confirmaciones de error/sin conexión/sesión conservan
   el nombre y la ocasión y ofrecen «Reintentar» o «Iniciar sesión».
2. **«Mi biblioteca» como quinto segmento** de «Añadir a la escena», con el conteo de la cuenta. Los elementos guardados personalmente forman un grupo separado
   del catálogo del Taller (SPEC: separado del catálogo global). Las filas son compactas; al tocar una fila se expande en el mismo lugar (solo una a la vez)
   para mostrar un marcador de posición de vista 3D, globos/piezas y acciones: «Añadir a mi escena» (principal),
   «Abrir en Escena», «Ver ficha». Las herramientas exclusivas del propietario aparecen debajo de un separador: «Cambiar nombre» convierte el nombre en un campo en
   línea (Enter confirma, Escape cancela, vacío → «Escribe un nombre para la decoración.»), y «Quitar de mi
   biblioteca» abre un AlertDialog real.
3. **Arrastrar para colocar.** Las filas propias y locales se pueden arrastrar al visor (zona de destino con borde discontinuo de color de acento); «Añadir a mi
   escena» es la alternativa equivalente para teclado/táctil. Al colocar, el visor confirma «Añadida a tu escena: «X».»
4. **Las entradas locales del navegador siguen siendo locales.** Un grupo plegado con borde discontinuo «En este navegador · 2» explica «Guardadas antes en
   este navegador. Siguen aquí y no se pasan a tu cuenta durante el piloto.» No existe ningún control de importación.
5. **Personal con acceso de solo lectura.** Para empleados/administradores, un selector nativo «Biblioteca de» permite elegir otra cuenta. Sus filas
   muestran «Solo lectura» y solo «Ver ficha»; la ficha muestra un aviso de solo lectura, sin acciones para cambiar el nombre, quitar ni colocar. Una
   mutación rechazada (API directa) muestra el estado «No se cambió nada · Solo la cuenta dueña puede cambiar o quitar esta
   decoración.»
6. **Cambio de cuenta.** Al cerrar sesión/cambiar de cuenta se vacía la lista y aparecen esqueletos con «Cambiaste de cuenta · Las
   decoraciones de la cuenta anterior ya no se muestran.» antes de mostrar los elementos de la siguiente cuenta.

## Detalle de interacción y movimiento

Presión y asentamiento táctiles, finitos y legibles (el contenido nunca queda oculto a mitad de una animación; solo transformaciones):

- las filas se asientan al cargar (translateY 8px, scale .985 → 1.004 → 1, desfase de 45ms); una fila recién guardada baja desde −14px y se asienta; la miniatura de la fila abierta se encaja .9 → 1.04 → 1; el detalle y el formulario para guardar se despliegan con scaleY .92 → 1.012 → 1 desde el borde superior; el campo para cambiar el nombre se encaja con scaleX .95 → 1.012 → 1 desde el borde del texto;
- el icono del recibo gira −16° → 6° → 0; el contador de «Mi biblioteca» da un pequeño salto 1.3 → .92 → 1 después de guardar; la etiqueta de ubicación baja y se asienta en el visor; los botones y las filas se presionan hasta .96–.975 (la fila y el campo para cambiar el nombre usan `motion.button` con el resorte del perfil);
- perfiles: expresivo 480/160/45ms, natural 300/130/25ms, sutil 150/90/10ms, curva cubic-bezier(.3,1.45,.6,1); Quieto, `?still=1` y la opción de movimiento reducido del sistema eliminan toda animación y transición, y mantienen visibles todas las palabras y controles; las pestañas ocultas pausan la animación CSS.

## Por qué encaja con el producto existente

Conserva el formulario para guardar, sus textos, la ubicación del inspector, el panel «Añadir a la escena» y la ficha que los usuarios ya conocen, y cambia solo lo que necesita R8: el destino (la cuenta, no el navegador), un lugar para encontrar la biblioteca de la cuenta, los controles exclusivos del propietario y el acceso de solo lectura. Usa la misma gramática en contexto que el propietario eligió para `proyectos@v1` («Edición en contexto»), así que el Taller se siente como un solo producto. El arrastre al visor ya existe para las tarjetas «Nuevas» (`PanelAnadir.tsx` `TarjetaNueva`).

## Ocho ejes

| Eje | Esta dirección |
|---|---|
| concepto | Manipulación directa: guardar en el inspector y abrir/cambiar el nombre/quitar/arrastrar cada decoración desde su propia fila. |
| distribución | Estructura del taller de proyectos@v1: barra lateral 60 · panel Añadir 300–340 · visor · inspector 280; en tablet, inspector debajo a ancho completo; en teléfono, apilado y ordenado según la tarea. |
| navegación | Navegación heredada de la cabecera y las rutas; segmentos del panel con «Mi biblioteca» + contador; filas con apertura única (aria-expanded); «Ver en Mi biblioteca» mueve el foco; selector «Biblioteca de» para el personal. |
| tipografía | Geist: título 24, panel 15, nombre de fila 14/600, metadatos 12; Geist Mono 12 para los contadores. |
| densidad | Filas de 64px, una expandida; grupo local contraído; formulario breve en el inspector. |
| componentes | shadcn Button/Input/Skeleton/Dialog/AlertDialog (Base UI), motion.button, select/details nativos, filas arrastrables con alternativa mediante botón. |
| color | Solo tokens de Pictures/Taller; acento en la acción principal, la fila abierta y el destino para soltar; estados de éxito/error en los recibos. |
| movimiento | Presión y asentamiento: asentamiento de fila, caída de fila, encaje de miniatura, despliegue de detalle/formulario, encaje de campo, encaje de estado, salto del contador, asentamiento al colocar; paridad con movimiento reducido. |

## Vistas, estados y diálogos de la maqueta

- Vista: «Taller 3D · Guardar pieza» (`taller`), «Taller 3D · Mi biblioteca» (`biblioteca`), «Personal · Biblioteca de otra cuenta» (`personal`).
- Estado: normal, cargando, vacío, error de carga, guardando, guardado, error al guardar, sin conexión, cambio de nombre (nombre vacío), colocado, heredado (grupo del navegador abierto), no permitido, cambiando de cuenta, sesión vencida.
- Diálogo: ficha (propia / local / ajena de solo lectura), quitar (AlertDialog «¿Quitar «X» de tu biblioteca?» — «Se quita de tu cuenta en todos los navegadores. Lo que ya añadiste a tus escenas se queda en ellas.», «Conservar» / «Quitar de mi biblioteca»).
- Puntos de quiebre: ≥1100 cuatro columnas; 640–1099 inspector debajo; <640 apilado; márgenes internos de 20/24/40px como en proyectos@v1.
- Datos de ejemplo: nombres neutros «… de ejemplo», «Cuenta de ejemplo», cantidades ilustrativas de globos/piezas; nombres de ocasiones de la taxonomía existente (General, Cumpleaños, Cumpleaños infantil, Baby shower, Boda). Las vistas 3D son marcadores de posición SVG integrados.

## Miniaturas

- **Candidata 1 — elegida** (`decoraciones@v1.r1.dir-c.html.candidate-1.html`): guardado en el inspector y filas expandibles dentro de un segmento «Mi biblioteca» del panel existente. Permanece en la superficie actual y mantiene todas las acciones accesibles con el teclado.
- Candidata 2 (`…candidate-2.html`): una bandeja de biblioteca acoplada debajo del visor con un espacio para soltar y guardar. Es más espacial, pero añade una región que el producto no tiene y hace que guardar dependa de arrastrar; se rechazó.

## Auditoría (resultados reales de esta salida)

- Compilación: `components mockup build` terminó con código 0 — 660 KB, 2,135 archivos de origen, sin conexión; shadcn/Base UI/Animate UI reales.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (también para ambas miniaturas).
- `audit_mockup.py` (valores predeterminados 1280/390): primera ejecución `RESULT: FAIL — contrast 1, padding 1` (descripción del formulario para guardar 4.24:1 en tema oscuro; relleno de fila esqueleto). Corregido (token de texto `--texto-suave`, relleno 12/14). Resultado final: 192/192 renderizados, `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- `audit_mockup.py --widths 1280,390,768`: 288/288 renderizados, mismo PASS; advertencia «1 recorrido de foco se detuvo en 60 paradas; no se comprobaron los controles posteriores».
- Prueba de interacción (Playwright integrado, no se conservaron archivos aparte de las capturas en /tmp): guardar → «Guardando…» → recibo y fila nueva (contador 3→4); al cambiar el nombre vacío aparece el error, Escape devuelve el foco a «Cambiar nombre»; se confirma el cambio de nombre; AlertDialog quita la fila; al arrastrar una fila al visor aparece «Añadida a tu escena»; la vista de otra cuenta para el personal tiene 0 controles para cambiar nombre/0 para quitar y muestra la etiqueta de solo lectura; 6 animaciones en ejecución al cargar (expresivo), 0 con `?still=1`; 0 solicitudes externas; sin errores de página.
- Capturas inspeccionadas: Taller claro a 1280, biblioteca oscura a 1280, personal oscuro a 768, guardado claro a 390, ficha a 1280, AlertDialog oscuro a 390. En una primera revisión, los botones del inspector estaban comprimidos y la indicación del visor se superponía a la nota de la escena; se corrigió antes de la auditoría final.

## Preguntas abiertas para el propietario

- Q: ¿Lo guardado en tu cuenta aparece solo en «Mi biblioteca» (como en esta maqueta) o también mezclado en Estructuras/Decoraciones/Ideas como hoy con la etiqueta «Tu biblioteca»?
- Q: ¿El personal (empleado/administrador) puede añadir a su propia escena una decoración de otra cuenta sin modificarla, o solo verla? La maqueta solo permite «Ver ficha».
- Q: Las entradas «En este navegador» (antiguas): ¿se siguen pudiendo quitar y renombrar como hoy, o quedan solo para añadir/abrir? La maqueta permite añadir, abrir y ver ficha, sin quitar.
- Q: T5.3 pide conservar «renombrar», pero la biblioteca actual no tiene renombrar; ¿se añade «Cambiar nombre» (como aquí) para el dueño?
- Q: T5.4/T5.5 hablan de «importar entradas del navegador» y de estados de importación, pero el SPEC (ronda 11 q1) dice que no se importan en el piloto; la maqueta sigue el SPEC (sin importación). ¿Se corrigen esas tareas?
- Q: ¿Se pide confirmación al quitar (AlertDialog, como aquí) aunque la biblioteca actual quita sin confirmar?
- Q: ¿Se permite repetir el nombre en tu biblioteca (como hoy, con id distinto) o debe avisar?

## Inquietudes

- Contradicción entre las tareas del brief (T5.4 «importar entradas antiguas del navegador sin pérdida», T5.5 estados de «importación») y SPEC ronda 11 q1 (sin importación). Esta dirección sigue SPEC; no se muestra ninguna interfaz de importación.
- Se muestra «Abrir en Escena», pero su validación corresponde a `proyectos@v1` (proyecto nuevo sin guardar); la maqueta solo muestra un aviso de maqueta al respecto.
- El texto de AlertDialog «Lo que ya añadiste a tus escenas se queda en ellas» supone que al colocar se copia el contenido en la escena, como hace hoy «Añadir a mi escena»; confirmar cuando T5.2 defina la API.
- La maqueta demuestra solo la distribución renderizada, el contraste y la interacción; la persistencia entre navegadores, la aplicación de la propiedad y la limpieza al cambiar de cuenta corresponden a T5.2–T5.4.
