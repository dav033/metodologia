---
name: Mesa en plano
contract: taller-esenciales@v1
revision: r10.dir-b
status: draft
kind: independent-exploration
subplan: SP-3
requirements: [R9, R10, R11]
source_plan_revision: 1
source_plan_schema: 1.3.0
owner: David
date: 2026-10-27
chosen_thumbnail: taller-esenciales@v1.r10.dir-b.html.candidate-1.html
---

# Mesa en plano — dirección B

## 1. Identidad y alcance

Exploración preliminar para `taller-esenciales@v1`, **no es el contrato canónico ni está aprobada para su implementación**. El propietario elige una dirección antes de la finalización. Sólo se escriben los seis artefactos específicos de esta revisión y el resultado de delegación requerido. No se modifica ningún repositorio de producción, contrato compartido, SPEC, PLAN ni revisión histórica.

Autoridad de comportamiento: `taller-esenciales@v1.r10.behavior.md`, luego SPEC “Comportamiento — SP-3 y SP-4 (respuestas de la ronda 9)” y PLAN SP-3. Consumidores identificados por el brief/plan suministrado: T3.1 textos de diseño, T3.2 creación/edición de mesas, T3.3 Backing, T3.4 exportación y T3.7 revisión renderizada. La geometría existente de Blender, la paridad de herramientas de IA, la compatibilidad de escenas guardadas y el comportamiento de Shopify siguen siendo obligaciones de aceptación de ingeniería; la ilustración estática no puede verificarlos.

## 2. Nombre, enfoque y adecuación

**Mesa en plano** coloca el inspector de la mesa seleccionada directamente debajo del lienzo existente del Taller. La mesa, sus dimensiones y la cantidad de sillas colocadas comparten un mismo eje vertical. El riel izquierdo original y el catálogo de la izquierda siguen siendo reconocibles. No se agrega ninguna página, ruta, marca, paleta ni tipografía.

El área de trabajo modificada comprende la navegación de grupos/tarjetas de tipos del catálogo, la ilustración del lienzo, el panel acoplado del inspector y los comentarios de exportación. El cambio espacial consiste en mostrar el inspector debajo al crear una mesa. El ancho se distribuye entre los conjuntos de campos de Mesa y Sillas lado a lado, en lugar de un inspector lateral estrecho. La lista de compra puede ocupar ese mismo panel para revisar rápidamente las cantidades; el diálogo de lista de compra existente en la cabecera sigue disponible.

Esta propuesta es adecuada para un editor cuya tarea principal consiste en colocar un objeto y cambiar sus parámetros mientras observa el resultado. En el teléfono, el modelo existente de lienzo y panel se convierte en un panel único con pestañas intercambiables Añadir / Pieza / Lista de compra, para evitar que un catálogo largo se interponga entre la creación y la edición.

## 3. Dos miniaturas y selección

Ambas composiciones se crearon desde cero a partir del brief y se inspeccionaron como capturas renderizadas de 1280px antes de componer el TSX completo.

| Candidato | Composición | Decisión |
|---|---|---|
| [Candidato 1](taller-esenciales@v1.r10.dir-b.html.candidate-1.html) | Catálogo a la izquierda; lienzo sobre un inspector ancho de dos columnas. | **Elegido.** Mantiene la creación y los controles del objeto seleccionado cerca, sin convertir el catálogo en una franja horizontal. |
| [Candidato 2](taller-esenciales@v1.r10.dir-b.html.candidate-2.html) | Lienzo junto a un inspector a la derecha; catálogo horizontal de ancho completo debajo. | Se conserva como evidencia de exploración. Sus ocho tarjetas simultáneas ocupan más ancho y desplazan la creación debajo del área de edición. |

La maqueta completa corrige una debilidad detectada en el primer renderizado del candidato 1: la altura del catálogo no debe estirar el lienzo ni desplazar el inspector fuera de la primera vista. El desplazamiento del catálogo en escritorio es independiente; el lienzo tiene una altura acotada y el inspector crece de forma natural cuando aparecen advertencias. La página permite desplazarse para ver comentarios ampliados, en lugar de recortarlos dentro de un inspector de altura fija.

## 4. Sistema de producto establecido y evidencia de fuentes

Superficies de producción de solo lectura: `src/app/globals.css` de ambos repositorios; `/3d` del asesor y `Taller3D`, `FondosYMuebles`, `EditorConjuntoMesa`, `Inspector`, `ListaCompra`, `ListaEscenografia`, `ExportarEscenaTaller`, valores predeterminados/perímetro/catálogo de muebles y `ASIGNACION_FONDOS`. El encabezado de Taller conserva su marca circular, la etiqueta Taller 3D, el contexto de escena, deshacer/rehacer, Foto realista, Exportar y Lista de compra; Paneles conserva Añadir, Piezas, Plantillas, Sala, el retorno al asistente y la ayuda. Las acciones ajenas a SP-3 solo identifican el límite de exploración.

Se leyeron los archivos hermanos `cuentas-admin@v1.md/.html` y `proyectos@v1.md/.html`. Sus archivos HTML históricos incluidos no coinciden en la paleta ni las fuentes. El contrato escrito actual de cuentas-admin resuelve explícitamente esta discrepancia a favor de los tokens de producción y Geist. Esta dirección sigue esa resolución, su vocabulario compacto de cuenta/idioma y la navegación activa neutra, mientras conserva la estructura de Taller específica de la ruta. No importa la paleta obsoleta Work/Measure de proyectos ni su barra lateral de página de biblioteca.

| Función de la fuente existente | Función del kit / local | Claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | card, popover | `#ffffff` / `#16181f` |
| `--texto` | primeros planos | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | primer plano atenuado | `#6b6178` / `#9aa1ad` |
| `--texto-tenue` | borde de entrada/control | `#766c85` / `#8a91a0` |
| `--acento`, `--sobre-acento` | primario, primer plano primario | `#6d3fe0`, blanco / `#9479ff`, `#120b24` |
| `--borde` | separadores decorativos | `#e3daef` / `#383c48` |
| `--superficie-2` | navegación seleccionada neutra | `#efe9f8` / `#242733` |
| `--taller-visor` | suelo de escena | `#ebe7f1` / `#1a1722` |
| `--taller-panel` | catálogo | `#faf9fc` / `#16131d` |
| `--taller-tarjeta` | inspector | blanco / `#1d1926` |
| `--taller-encima` | superficie de miniatura | `#f3eefb` / `#231e2e` |
| Pares existentes de aviso/error/éxito | mensajes de advertencia/error/éxito | Valores exactos del producto en el TSX; medidos en ambos temas. |

Las correspondencias accesibles para los elementos primarios y de entrada siguen el mapeo escrito finalizado del proyecto hermano. Los separadores decorativos conservan sus bordes originales más claros. Las formas mantienen los controles Taller de 10px, las tarjetas de 12px y el desplegable de cuenta redondeado del proyecto hermano. Los controles tienen al menos 44px de alto; el relleno de los paneles es de 24px en escritorio y 20px en teléfono/tableta.

Los archivos WOFF2 de producción reales de Geist Sans y Geist Mono Latin, del build local de Next de t12, están incrustados como URI de datos. Geist se usa para el texto de la interfaz y Geist Mono para cantidades/dimensiones. La paleta y las fuentes predeterminadas del kit están reasignadas por completo. Los colores de materiales de la escena son valores existentes de los muebles, no una segunda paleta de interfaz.

Componentes instalados reales: `shadcn:button default|outline default|hover|focus|pressed|disabled`, `shadcn:input number|search default|focus`, `shadcn:skeleton loading` y `shadcn:dialog shopping open|closed` con su mejora instalada de Animate UI/Base UI, importados desde `@/components/ui/{button,input,skeleton,dialog}`. Los selectores de grupo/tipo/disposición/idioma, los controles de color y los desplegables son controles nativos explícitos. La escena SVG, las miniaturas del catálogo y el panel dividido son composiciones personalizadas. `mountMockup/useMockup` y `useMotionProfile` provienen del entorno de ejecución real proporcionado. No se usaron alternativas HTML, instalaciones de paquetes ni descargas de recursos.

## 5. Ocho ejes

| Eje | Evidencia de la dirección B |
|---|---|
| Concepto | Un banco de edición espacial dentro del Taller existente: objeto elegido arriba, parámetros justo debajo. |
| Diseño | Barra de 60px + catálogo de 312px + área de trabajo con lienzo sobre inspector; el catálogo pasa a 340px a 1440px. `.work-body`, `.stage`, `.inspector-dock`. |
| Navegación | Barra original de Paneles; selector nativo Grupo; botones Mesa y sillas / Lista de compra en el panel inferior; panel de teléfono Añadir / Pieza / Lista de compra. `.tool-rail`, `.group-select`, `.dock-nav`, `.mobile-sheet-tabs`. |
| Tipografía | Geist existente; título del catálogo de 24px, título del panel inferior de 20px, controles de campo de 14px, cantidades monoespaciadas. `.catalog-panel h1`, `.dock-heading h2`, `.dimension`. |
| Densidad / forma | Dos tarjetas ilustradas por fila; tres medidas numéricas juntas; dos grupos de campos lado a lado en escritorio; superficies planas divididas con controles redondeados existentes. `.catalog-grid`, `.measure-fields`, `.inspector-grid`. |
| Componentes | Botones/entradas/esqueleto de carga/diálogo reales, selectores nativos de grupo/tipo, datos de tabla/valores predeterminados/perímetro de producción, escena esquemática personalizada. Sin mosaicos decorativos de panel de control. |
| Color | Funciones exactas de los tokens de producción y del proyecto hermano finalizado. Navegación neutra; acento existente para controles principales de compra/descarga y foco; colores de estado reservados para comentarios reales. |
| Movimiento | Asentamiento espacial desde distintos orígenes: catálogo desde la izquierda, lienzo desde la derecha, inspector desde arriba, tabla desde abajo, sillas en secuencia. Interacción táctil al pasar y presionar, y comentarios de exportación anclados. Véase §9. |

Las afirmaciones legibles por máquina y la evidencia de selectores renderizados están en `taller-esenciales@v1.r10.dir-b.json`.

## 6. Flujos y disciplina de datos

**Crear y editar.** Abrir Fondos y muebles → Grupo Mesas → activar una tarjeta de tipo → crear la mesa predeterminada de producción y seleccionarla → mover el foco al encabezado del inspector → cambiar medidas/sillas → actualizar el esquema, la cantidad real colocada y las líneas de la lista de compra a partir de los mismos datos de la mesa. Los valores predeterminados rectangulares son **240 × 90 × 75 cm**. Las piezas fijas existentes, incluidas las piezas Imperial, siguen disponibles con sus nombres originales en el catálogo. Las tarjetas paramétricas muestran las dimensiones predeterminadas para distinguirlas de las entradas fijas. No se realiza ninguna solicitud de IA de pago.

El artefacto estático importa en modo de solo lectura `TIPOS_MESA`, `NOMBRE_MESA`, `PARTIDA_MESA`, `LIMITES_MESA`, `SILLAS`, `contornoDeMesa` y `repartirSillas` existentes. No duplica una fórmula de capacidad supuesta. La configuración rectangular/Tiffany inicial solicita ocho y coloca ocho; su capacidad es diez. El estado de capacidad excedida solicita dieciséis y coloca diez. A 300 × 90 cm, la capacidad de Tiffany es doce. Las cantidades, las marcas dibujadas de sillas y las cantidades de la lista se derivan del mismo resultado `puestos`. Al cambiar el tipo, se usan las medidas predeterminadas del tipo existente; la profundidad derivada de los tipos redondo/cuadrado/semicírculo sigue siendo derivada. Deshacer/rehacer restaura instantáneas completas de la escena de prueba; Ctrl+Z también funciona fuera de los campos.

**Respaldo.** Seleccionar Respaldo → ver exactamente las siete tarjetas requeridas → añadir una y conservar su ID/nombre original. La búsqueda coincide con nombres e IDs originales en Fondos y muebles. Los grupos anteriores se rellenan desde el catálogo real, excluyendo solo esos siete IDs. Se reutiliza `ASIGNACION_FONDOS` para asignar elementos a la lista de compra; el traslado visual no cambia ningún repositorio. La acción de creación de la tarjeta paramétrica media luna está limitada a la vista previa y tiene un espacio de nombres para que no pueda confundirse con el elemento de Respaldo existente `media_luna`. Los identificadores de producto almacenados no se redefinen.

**Cantidades.** Abrir la lista del panel inferior o el diálogo del encabezado. Los muebles aparecen en Mobiliario, con cantidades y dimensiones y la indicación “no es producto de la tienda”. La escenografía aparece en la sección de su repositorio existente. No hay precios de alquiler, símbolos de moneda ni cargos de compra. Las medidas de las mesas y las de las sillas siguen separadas.

**Exportar.** Abrir el control Exportar existente en el encabezado → Descargar modelo GLB → estado de preparación y envío repetido desactivado → finalización o error visible que permite reintentar. PNG permanece en el menú existente. Los comentarios de espera/resultado aparecen justo después del lienzo y antes del inspector en todos los anchos. Escape/Cerrar cierra el grupo de exportación no modal y devuelve el foco a Exportar. El diálogo de la lista de compra usa contención modal real y se cierra con Escape.

La exportación está **simulada** explícitamente en este artefacto estático: una acción se completa localmente tras 1100ms y no descarga un GLB ficticio. El selector Estado congela ejemplos de exportación en curso/finalizada/fallida para inspeccionarlos. No se afirma que haya geometría, validación de Blender, red, IA, guardado en servidor ni operaciones de cuenta. Los valores de escena/exportación se identifican claramente como Datos de ejemplo.

## 7. Vistas y estados inspeccionables

Todos los selectores nativos de planificación permanecen visibles con la etiqueta Mockup: Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` y Movimiento `motion`. Cambiar los ejes de planificación selecciona una configuración de prueba nueva; las interacciones con el producto dentro de una configuración comparten datos en vivo.

| Selector | Valores y comportamiento |
|---|---|
| Vista | `mesas`, `backing`, `fondos`, `decorado`, `lista`, `exportar`. Los asientos también siguen siendo accesibles desde Grupo. |
| Estado | `normal`; `cargando` muestra esqueletos del catálogo/inspector y desactiva exportar/lista; `vacio` muestra la consulta sin resultados y Limpiar búsqueda; `error` muestra un error recuperable del catálogo; `capacidad` muestra la advertencia de cantidad solicitada/colocada y permite usar Deshacer; `exportando`, `listo`, `fallo` muestran los comentarios correspondientes de exportación. |
| Diálogo | Ninguno o `lista`; diálogo modal real de lista de compra con cantidades/dimensiones y Cerrar. |
| Tema | Claro / Oscuro, con los mapeos fijos de tokens de la fuente. |
| Movimiento | Expresivo de forma predeterminada; Natural, Sutil y Quieto. El movimiento reducido del sistema operativo y `?still=1` también dejan estable el diseño. |

Una búsqueda sin coincidencias conserva la escena existente y ofrece una acción de recuperación. Un error del catálogo no borra la mesa. Un error de exportación conserva el editor y ofrece Reintentar. Las advertencias de validación/capacidad distinguen las sillas solicitadas de las realmente colocadas. Estas son operaciones locales de herramientas; los estados nuevos de permiso de cuenta denegado, conflicto sin conexión/con el servidor o cuenta desactualizada están fuera del brief de SP-3 y no se inventan aquí.

## 8. Reglas de diseño adaptable

- **≥1024px:** conservar la barra original y el catálogo a la izquierda; escena acotada de 300px sobre el inspector amplio. Mesa y Sillas son grupos de campos adyacentes. El catálogo se desplaza por separado. El contenido adicional de advertencias/exportación aumenta la altura de la página en lugar de recortar controles. A 1440px, el catálogo crece hasta 340px.
- **640–1023px:** barra de 60px, catálogo de 264px y el área de trabajo restante. Los grupos de campos del inspector se apilan, las medidas numéricas permanecen juntas y las acciones del encabezado se ajustan a varias líneas. Sin desplazamiento horizontal de la página.
- **<640px:** relleno lateral de 20px. El encabezado se ajusta; los iconos de panel existentes pasan a una fila horizontal. El lienzo precede al resultado de exportación y al panel intercambiable. La creación abre Pieza y enfoca su encabezado; el catálogo se oculta durante la edición. La acción Lista de compra del panel abre la vista de cantidades integrada; el botón del encabezado sigue abriendo su diálogo. Las medidas usan dos columnas y la altura pasa a la fila siguiente; luego las sillas se apilan. Ninguna superposición oculta los campos numéricos.

Los nombres en español y los nombres originales largos del catálogo se ajustan a varias líneas; los puntos suspensivos no ocultan acciones ni dimensiones medidas. Se renderizaron tableta de 768px y teléfono/escritorio de 390/1280px. El límite de reajuste de 320px se comprueba por separado, no se infiere solo de la auditoría de 390px.

## 9. Detalles de interacción y movimiento

La gramática espacial usa la curva de resorte similar a la de producción `cubic-bezier(.34,1.4,.64,1)` y la curva de salida suave `cubic-bezier(.23,1,.32,1)`. El texto legible permanece opaco durante toda la animación. Las entradas de paneles/tarjetas duran 620ms en modo expresivo, 400ms en natural y 220ms en sutil; los controles repetidos duran 180/150/120ms, respectivamente.

| Comportamiento | Activador / evidencia renderizada real |
|---|---|
| Aparición del catálogo | Desplazamiento de 24px desde la izquierda, `catalog-enter` en `.catalog-panel`. |
| Aparición del lienzo | Desplazamiento de 16px desde la derecha, `stage-enter` en `.stage`. |
| Colocación de tarjeta | Desplazamiento de 12px y giro de asentamiento de 1°, intervalo de 35ms entre tarjetas, `card-arrive` en `.creation-card`. |
| Despliegue del inspector | Asentamiento ascendente de 28px, `dock-unfold` en `.inspector-dock`. |
| Colocación de la mesa | 800ms, −16px y escala de .97 → 1, `table-land` en `.table-projection`. |
| Colocación de sillas | 650ms, intervalos de 25ms, asentamiento de 9px/escala, `chair-settle` en `.chair`; las marcas corresponden a los asientos colocados calculados realmente. |
| Pasar el cursor / presionar / enfocar | Las tarjetas se elevan 4px y giran −.6°; los controles se elevan 2px y se presionan 1px/escala .98; el foco del teclado usa un contorno de acento de origen de 3px. |
| Comentarios | Gesto de plegado de 480ms, 10px/0.5°, `feedback-fold` en mensajes de capacidad/exportación/estado. |
| Apertura/exportación en curso | Apertura anclada de 360ms, 8px/escala; el progreso se desplaza durante un ciclo de 1.5s. El progreso fuera de pantalla y todas las animaciones de pestañas ocultas se pausan. |

No hay animación ambiental decorativa infinita. `useMotionProfile` controla el perfil/estado reducido. Quieto, el movimiento reducido del sistema operativo y `?still=1` eliminan animaciones/transiciones y conservan la geometría final, los comentarios y las acciones de teclado. Las transformaciones necesarias para la disposición del SVG permanecen intactas cuando el movimiento está reducido. Los cambios de estado se pueden inspeccionar sin movimiento y nunca dependen solo del color o el movimiento.

## 10. Criterios de accesibilidad y aceptación visual

Objetivo: WCAG 2.2 AA para la interfaz añadida. Selectores nativos etiquetados y campos numéricos, de búsqueda y de color; semántica real de botones; controles de 44px de alto; foco visible con el acento de la fuente; grupos de campos y leyendas semánticos; anuncios corteses de recuentos y estados; y semántica de alerta para errores. La exportación es un grupo con nombre y no modal, no un menú ARIA incompleto. El modal de la lista de compras usa la primitiva de diálogo instalada. Escape lo cierra y el foco vuelve al elemento que lo abrió. El SVG personalizado se presenta explícitamente como imagen esquemática con un nombre accesible descriptivo; todas las acciones añadidas se pueden realizar sin manipular su dibujo.

| ID | Ancho / estado | Criterio observable |
|---|---|---|
| B-01 | Todos / normal | Las acciones existentes de la cabecera de Taller y el vocabulario de Paneles siguen siendo reconocibles; no se introduce una nueva identidad. |
| B-02 | Todos / Mesas | Ocho tarjetas de tipos paramétricos usan los nombres originales y las dimensiones predeterminadas de producción; se conservan las tarjetas fijas y en unidades imperiales existentes. |
| B-03 | Todos / creación | Una tarjeta rectangular crea 240 × 90 × 75 cm, la selecciona y muestra/enfoca el inspector. |
| B-04 | ≥1024 / normal | El lienzo y el inspector de dos grupos de campos comparten los mismos límites horizontales y una inserción de 24px; el catálogo no ensancha el lienzo. |
| B-05 | Todos / capacidad | Solicitar dieciséis con los valores predeterminados rectangulares da como resultado diez asientos Tiffany reales; la advertencia, el dibujo y la lista coinciden. |
| B-06 | Todos / deshacer | Deshacer restaura las medidas y cantidades reales anteriores, incluso después de una advertencia de capacidad. |
| B-07 | Todos / Backing | Aparecen exactamente una vez las siete propiedades requeridas; ninguna permanece en los dos grupos visuales anteriores; funciona la búsqueda por ID original. |
| B-08 | Todos / lista | Se muestran las cantidades y las dimensiones de cada artículo, sin precios; la pertenencia a Mobiliario/Escenografía sigue el mapa existente. |
| B-09 | Todos / exportación | Se pueden inspeccionar los estados pendiente, completado y error de GLB; se puede volver a intentar; se deshabilita la exportación pendiente repetida; los datos de la escena no cambian. |
| B-10 | <640 / edición | El lienzo permanece sobre la hoja; al crear una mesa, la selección cambia de Añadir a Pieza, sin tener que desplazarse por el catálogo. |
| B-11 | Todos / carga, vacío, error | La carga usa esqueletos; la recuperación sin resultados borra la consulta; se muestra la opción de reintentar tras un error de carga y la escena se conserva. |
| B-12 | Ambos temas / todos los estados | Contraste de texto ≥4.5:1, bordes de controles ≥3:1, foco visible, relleno alineado y sin desbordamiento horizontal de página en la matriz medida. |
| B-13 | Reducido / todos | Las mismas posiciones finales y acciones; no queda ninguna animación activa al terminar; ningún significado esencial depende del movimiento. |

## 11. Verificación e impacto

La cadena de herramientas real generó esta dirección sin conexión, con React, shadcn/Base UI y Animate UI, e integró CSS, JS, funciones de geometría de origen y dos fuentes locales en un único HTML. No se usan CDN, imágenes o fuentes externas ni se instalan paquetes.

Los comandos de verificación usaron las rutas absolutas proporcionadas: `components mockup build` sobre el TSX/la salida de esta dirección, `kit/contrast.py`, `UV_OFFLINE=1 uv run --offline --with playwright python kit/audit_mockup.py ... --max-combos 120` y `kit/compare_directions.py`. La matriz contiene 108 casos por ancho, por lo que el límite de 120 no la muestrea: son 216 renderizados planificados en total a 1280/390, con ambos temas, las seis vistas, los ocho estados y las escenas de la lista de compras.

Generación final del código fuente y la salida: **PASS**, HTML autocontenido de 1015 KB generado sin conexión a partir de 2224 archivos de origen. SHA-256 del HTML final: `a41c0577b6405ca6050a1bad3144980c1d6e89ff3e98924b73d357e9c795bc8d`.

`contrast: 158 pairs checked in light and dark, all pass`

`audit: taller-esenciales@v1.r10.dir-b.html — 216 renders (216 combinations planned), 11638 text measurements, 2375 focus stops`

RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento

Esta es la matriz completa final, no un resultado muestreado ni anterior a los ajustes. Los problemas de diseño detectados antes se corrigieron antes de esta ejecución final. No quedan advertencias de auditoría.

Se aprobaron veintiséis aserciones de navegador enfocadas: valores predeterminados/capacidad de producción para rectángulos, creación y selección, redimensionamiento, advertencia de capacidad, lista de cantidades derivadas, ausencia de precios de alquiler, deshacer, siete tarjetas Backing, identidad distinta de la propiedad Media luna, búsqueda por ID original, omisiones de los grupos anteriores, recuperación del estado vacío, diálogo real/Escape, reintento/finalización de exportación con la escena intacta, selección de la hoja adaptable y ausencia de desbordamiento de página a 390/768/1280. No se produjo ninguna excepción del navegador ni solicitud HTTP(S) externa. El ajuste final de ubicación de la exportación y agrupación del repositorio también recibió una prueba rápida enfocada. **Se aprobaron diecinueve verificaciones adicionales**: valores predeterminados de los ocho tipos, devolución del foco del diálogo, controles de color nativos ampliados y contraste/relleno/reflujo renderizados a 320/390/768/1280px en ambos temas, ajuste de movimiento reducido del sistema operativo y `?still=1`. Los campos avanzados cerrados quedan explícitamente fuera del diseño y del foco hasta que se abra su sección desplegable.

Se inspeccionaron capturas renderizadas en memoria: ambas miniaturas a 1280, el espacio de trabajo completo de escritorio en tema claro, capacidad/Backing en escritorio oscuro, Backing en tableta clara, hoja de pieza en teléfono oscuro y error de exportación en teléfono claro. Los archivos de captura no se guardaron fuera de los artefactos asignados.

**La comparación renderizada final A/B/C: PASS**, `ok=true`, `evidence_ok=true`, sin evidencia de selectores faltante. La similitud de diseño entre B y A es **0.072**; entre B y C es **0.050**. La navegación, la densidad y el movimiento difieren en ambas comparaciones; los tres pares pasan. La herramienta informa las diferencias tipográficas, pero estas no cuentan para la distinción. Estas mediciones son una comprobación estructural, no una aprobación ni un reemplazo de la inspección visual. Una ejecución de evidencia de una sola dirección también aprobó todas las afirmaciones declaradas sobre selectores.

Compatibilidad si se selecciona: **cambio visual incompatible** para T3.2/T3.3/T3.4 debido a la reubicación del inspector, el selector de grupo y la navegación adaptable mediante hoja; las identidades de comportamiento y datos siguen regidas por el brief compartido. T3.7 debe revisar el contrato final elegido en los puntos de corte indicados. Esta exploración no modifica ningún contrato, implementación ni aprobación de SP-2/SP-4. Este artefacto no puede comprobar transformaciones de metros de GLB, precisión de color base, importación en Blender ni paridad de IA/manual; esas verificaciones siguen siendo las comprobaciones de ingeniería existentes.

## 12. Inquietudes y preguntas para la persona responsable

Los HTML complementarios proporcionados y los contratos escritos no son visualmente coherentes entre sí. Esta exploración resuelve los conflictos de tokens y fuentes según las fuentes de producción y la decisión escrita actual de cuentas-admin, y conserva la estructura específica de Taller existente. La persona encargada de finalizar debe aplicar la misma precedencia.

Q: ¿Se conservan ocho sillas iniciales para todos los tipos de mesa paramétrica, limitadas por la capacidad real, o debe existir una cantidad inicial propia de cada tipo? Esta exploración conserva las ocho del conjunto actual.
Q: ¿Basta mostrar las medidas en las tarjetas paramétricas para distinguirlas de las piezas fijas que comparten nombre, o se debe añadir un rótulo de sección con copy aprobado? Esta exploración conserva los nombres originales y todas las piezas existentes.

Las solicitudes de paleta y fuente de comentarios anteriores quedan reemplazadas por la instrucción explícita de esta ronda de mantener fijo el sistema de producto. Por tanto, la variación es estructural, de navegación y de movimiento. La aprobación de este borrador, la elección entre A/B/C y la finalización canónica corresponden a la persona responsable y a quien finalice.
