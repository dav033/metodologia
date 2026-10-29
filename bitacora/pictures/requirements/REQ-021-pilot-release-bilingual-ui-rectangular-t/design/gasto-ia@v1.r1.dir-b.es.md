---
exploration: gasto-ia@v1.r1.dir-b
name: Sesiones e inspector
status: draft
subplan: SP-6
requirements: [R4, R5]
stance: spatial
chosen_thumbnail: gasto-ia@v1.r1.dir-b.html.candidate-1.html
owner: David
date: 2026-10-29
---

# Sesiones e inspector — exploración espacial B

## 1. Identidad y trazabilidad

Solo exploración de planificación, **borrador y sin aprobar**. Esta dirección es una candidata para el futuro contrato `gasto-ia@v1`, no es el contrato canónico ni una aprobación de implementación. No se modificaron el contrato canónico, el HTML compartido, el PLAN, el repositorio de producción ni ningún otro archivo de bitácora. Comentarios del responsable: ninguno proporcionado.

Alcance: `gasto-ia@v1.r1.behavior.md`, R4/R5 y SPEC “Comportamiento — SP-6 (ronda 12 pendiente)”. El PLAN actual identifica SP-6, el contrato `gasto-ia`, versión 1, la copia del diseño T6.1 y la revisión visual T6.6; T6.4 construye el panel y T6.5 verifica los puntos de entrada reales. Estos son los consumidores afectados si se elige esta dirección. La compatibilidad está **sin determinar** hasta la selección independiente y la aprobación del plan; no hay un borrador anterior de gasto-ia que reemplazar.

Evidencia del producto de solo lectura: las superficies t12 y asesor, y globals.css; `src/components/admin/AdminTabs.tsx`, `src/components/ui/shell/CabeceraApp.tsx` y `src/app/layout.tsx` de t12; vocabulario de proveedores y modelos de producción; Markdown/HTML canónicos de los contratos hermanos `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`, además de la fuente seleccionada de cuentas r14 para precisar la composición del shell, los tokens y la tipografía. La administración existente contiene pestañas operativas, pero no una pantalla de gasto en IA vinculada a cuentas. El área de gasto propuesta se agrega a ese contexto de administración y usa el shell compartido actualizado de los proyectos hermanos. La ruta sigue pendiente de decisión del responsable.

## 2. Propósito y usuarios

Un Empleado interno o Administrador con `gasto.ver` revisa el gasto estimado conocido y los tokens informados por sesión, elemento de trabajo, usuario, tipo y herramienta. Los filtros de usuario y tipo de llamada restringen todos los totales y grupos mostrados. El éxito consiste en encontrar un grupo y rastrear sus importes hasta las llamadas individuales con costo, sin abrir el contenido de las conversaciones.

El Usuario común, quien no haya iniciado sesión y cualquier persona que llame sin `gasto.ver` no reciben datos de gasto. El caso de prueba de acceso denegado contiene un rechazo y no muestra totales, filtros, grupos ni llamadas. Este artefacto estático solo demuestra la presentación; no implementa autenticación ni autorización del servidor. En producción, se debe hacer cumplir el permiso antes de devolver los datos del registro y ocultar de forma independiente los destinos de navegación inaccesibles.

## 3. Enfoque y jerarquía

Conservar el encabezado con anillos y puntos de Pictures/Sempertex, los controles de idioma y cuenta, el título de tarea de 24px, la navegación horizontal neutral de administración, el panel de trabajo redondeado y el pie establecidos por los proyectos hermanos. Agregar el destino Gasto IA en ese contexto; no rediseñar otras pantallas de administración.

Dentro del área modificada, colocar el total filtrado y los filtros encima de un espacio de trabajo de dos paneles. El panel izquierdo es un registro de grupos; el panel derecho, más ancho, es un inspector con el total del grupo seleccionado, subtotales por tipo y filas de llamadas atribuidas. Esto reemplaza un informe plano por una relación espacial entre un grupo y sus llamadas. No hay gráficos, paneles promocionales, editores de presupuesto, límites, facturas ni flujos de facturación inventados.

**Primero se escribieron y renderizaron dos miniaturas.** La candidata 1 ubica un registro compacto y un inspector ancho de llamadas dentro de un mismo panel. La candidata 2 ubica un registro ancho de proyectos junto a un inspector angosto independiente. Se eligió la candidata 1 porque el inspector puede mostrar proveedor/modelo, sesión, elemento de trabajo y metadatos faltantes sin comprimirlos en una columna angosta. Ambos HTML de miniaturas siguen disponibles; los datos compuestos son ilustrativos y no agregan contratos de comportamiento.

## 4. Dirección de ocho ejes y sistema de diseño fijo

| Eje | Expresión en este artefacto |
|---|---|
| Concepto | Seleccionar un grupo de gasto e inspeccionar las llamadas con costo que generan el importe conocido. Los totales de proyectos conservan la atribución a conversaciones; las llamadas independientes se agrupan por conversación. |
| Diseño | Un panel de trabajo; filtros en la parte superior; registro de 330px e inspector fluido a partir de 1100px, registro de 270px entre 768 y 1099px. Por debajo de 768px, una secuencia de grupo a detalle en un solo panel reutiliza el mismo contenido. |
| Navegación | Controles locales de “Agrupar por” para Sesión, Trabajo, Usuario, Tipo y Herramienta; las filas de grupo seleccionadas actualizan el inspector contiguo. En teléfono, la selección abre el inspector y el control para volver devuelve el foco a la fila seleccionada. |
| Tipografía | Geist Sans existente; H1 de página de 24px, encabezados de sección/grupo seleccionado de 20px, importe seleccionado de 28px (26px en teléfono), títulos/cuerpo de llamadas de 15px y metadatos de 12–13px. Geist Mono solo para identificadores de origen y metadatos de modelos. USD usa cifras tabulares. |
| Densidad | Relleno del panel de 28px en escritorio y 20px en teléfono, relleno de filas del registro de 18px, separación de llamadas de 20px y filas con separadores. Dos llamadas iniciales mantienen acotado el inspector; una acción explícita para ver más llamadas muestra el resto de las llamadas de prueba. Sin cuadrícula repetida de tarjetas KPI. |
| Componentes | Button y Skeleton reales de shadcn/Base UI ya instalados, selectores nativos con etiquetas, controles nativos de divulgación de atribución y composiciones personalizadas de registro/inspector. Mismos paneles de 32px, vocabulario de inserciones de 24px, campos de 18px y controles tipo píldora de los proyectos hermanos. |
| Color | globals.css de producción exacto y asignaciones de los proyectos hermanos en ambos temas. Interfaz neutral; los tokens primary/ring se usan para identidad y foco; los tokens de advertencia, solo para estados reales de uso parcial/error. Los valores desconocidos conservan texto neutral. Sin paletas ni familias tipográficas nuevas. |
| Movimiento | Posicionamiento espacial: el inspector se desplaza desde +22px, pasa por −2px y llega a su posición; las filas entran desde −10px; las llamadas se asientan con desplazamiento vertical de 8px; el panel se abre desde scaleX(.99). 460ms expresivo / 300ms natural / 160ms sutil, intervalos de 45ms entre filas, controles de 180/140/100ms; cubic-bezier(.23,1,.32,1). Al pasar el cursor, los grupos se desplazan 3px y los botones se elevan 2px. |

La asignación de tokens de origen se copia del shell de cuentas conservado, no de los valores predeterminados de la paleta del kit:

| Origen Pictures | Rol / uso en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--superficie-suave` | fila de registro seleccionada, divulgación | #faf8fd / #1c1e26 |
| `--acento`, `--sobre-acento` | principal, primer plano principal | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | interacción al pasar el cursor sobre el color principal | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | borde decorativo, separador | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | límite accesible de entrada, alias heredado del proyecto hermano | #766c85 / #8a91a0 |
| `--aviso`, `--aviso-suave` | advertencia, advertencia suave | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45, #ffeaec / #ff979f, #43252a |

Los archivos WOFF2 de Geist Sans/Mono están incrustados desde la compilación existente de t12 con Next. No se descargaron recursos ni paquetes. Componentes: `shadcn:button outline default|hover|pressed|focus|disabled` de `@/components/ui/button`; `shadcn:skeleton record loading` de `@/components/ui/skeleton`. `native:select user|kind|language`, `native:details account|attribution`, `custom:spend-register` y `custom:call-inspector` son composiciones explícitamente personalizadas, no afirmaciones de que sean componentes de biblioteca. `mountMockup/useMockup` y `useMotionProfile` son importaciones reales del runtime del kit.

## 5. Navegación e interacción

Los controles para agrupar el producto conservan los filtros de usuario/tipo; seleccionar una fila conserva la agrupación y los filtros actuales. Un grupo con varias cuentas muestra la cantidad de usuarios en lugar de atribuir todo el grupo a la primera cuenta. Los selectores nativos de vista/estado/tema/movimiento son controles visibles de inspección fuera del producto y conservan la etiqueta Mockup. Cambiar vistas/estados de inspección restablece los datos de prueba; las interacciones del producto conservan su propio estado.

Los destinos de administración Cuentas / Roles y permisos / Mi cuenta y el texto de divulgación de cuenta se conservan como contexto del shell y se representan mediante etiquetas que no navegan: esta exploración no simula esos flujos de los proyectos hermanos ni realiza solicitudes a sus rutas. ES/EN cambia localmente las etiquetas del producto y el formato de los metadatos. No se necesitan diálogos, por lo que no se declara ningún selector `scene`.

Una fila de grupo es un botón real con `aria-pressed` y `aria-controls`. En teléfono, al activarla se enfoca el encabezado del inspector; al volver, el foco regresa a la misma fila. La divulgación de atribución usa un control nativo accesible con teclado. Al expandir para ver más llamadas se agregan los demás registros simulados sin cambiar el grupo seleccionado ni realizar una solicitud. La paginación de producción debe conservar la semántica del cursor del servidor; este caso de prueba no afirma implementarla.

## 6. Flujos

1. **Revisar una sesión:** acceder a la vista de gasto con permiso → elegir usuario y tipo si hace falta → elegir Sesión → seleccionar una sesión del servidor → inspeccionar el total conocido, los subtotales de texto/imagen y sus llamadas → expandir la atribución si hace falta.
2. **Revisar un proyecto:** cambiar a Trabajo conservando los filtros → seleccionar Proyecto pro_01 → inspeccionar las llamadas con con_01 y con_03 → mostrar las llamadas restantes. con_02 independiente es un elemento de trabajo distinto, no un proyecto.
3. **Comparar otros totales:** elegir Usuario, Tipo o Herramienta → seleccionar un grupo → inspeccionar sus llamadas. Los totales y las cantidades se derivan del mismo conjunto de datos filtrado.
4. **Recuperarse:** cargar error → mantener disponibles los selectores de usuario/tipo → Reintentar → reemplazar el error por los resultados conservando los filtros. Sin resultados → cambiar los filtros o Ver todos. Durante la carga se deshabilitan las acciones duplicadas de filtro.
5. **Inspeccionar uso parcial:** seleccionar Datos parciales en la barra del inspector → el uso con error conocido sigue incluido → se informa explícitamente de una llamada con costo desconocido → expandir su atribución; nunca reemplazar un costo, token o modelo faltante por cero ni por un valor supuesto.
6. **Inspección en teléfono:** seleccionar una fila del registro → reemplazar el registro por el inspector → enfocar su encabezado → volver → restaurar el foco en la fila seleccionada. El movimiento reducido conserva esta secuencia sin desplazamientos.

## 7. Especificaciones de vistas y datos simulados

Cinco vistas comparten los mismos filtros, el resumen de total conocido y el inspector: Sesión, Trabajo, Usuario, Tipo, Herramienta. Cada grupo seleccionado muestra el USD estimado conocido, los importes de texto/imagen, la cantidad de llamadas y sus filas de llamadas. Cada fila muestra tipo, herramienta, proveedor/modelo cuando se informa, contexto de proyecto o conversación independiente, id de conversación, etiqueta de cuenta, id de sesión del servidor, fecha, tokens de entrada/salida, costo estimado y estado explícito de finalizada/parcial/error. La divulgación de atribución agrega el correo electrónico y el id del registro. No se incluye ningún prompt, respuesta, recurso generado, clave de API ni dato ajeno del perfil personal.

Las cuatro llamadas del caso de prueba normal pertenecen a dos cuentas simuladas existentes de los proyectos hermanos (`master@prueba.local`, `admin@prueba.local`), tres sesiones del servidor, un proyecto con dos conversaciones y una conversación independiente. El total normal conocido es **0.0560 USD**, el total del proyecto **0.0480 USD** y el de ses_01 **0.0420 USD**. Los tokens informados normales suman **6,100**; los tokens no informados de la llamada de imagen aparecen como “No informado”. Los datos están etiquetados explícitamente como simulados; el vocabulario de proveedor/modelo proviene del repositorio. La fecha mostrada es la fecha 2026-10-29 indicada para esta delegación, no una cronología de eventos inventada; no se agregan nombres ni horarios ficticios de personas/eventos.

El caso de prueba parcial agrega 0.0010 USD y 100 tokens de entrada conocidos provenientes de un error del proveedor, además de un error de imagen con modelo/tokens/costo desconocidos. El total conocido filtrado pasa a **0.0570 USD**, los tokens conocidos a **6,200**, con un costo explícitamente desconocido. Los valores enteros del caso de prueba representan diezmilésimas de USD para que las sumas sean deterministas; no establecen el almacenamiento ni los precios de producción. La propuesta visual de cuatro decimales está pendiente de Q3.

## 8. Estados

| Valor de estado nativo | Comportamiento visible / recuperación |
|---|---|
| `normal` | Resultados correctos, totales derivados e inspector del grupo seleccionado; borrar filtros está deshabilitado cuando los filtros ya incluyen todos los registros. |
| `cargando` | Esqueletos del registro/inspector, estado de carga y controles de usuario/tipo/borrar deshabilitados; no se presenta como actual ninguna moneda obsoleta. |
| `vacio` | “No hay llamadas registradas para estos filtros.” y Ver todos; sin registros inventados ni llamadas con uso cero. Se llega al mismo estado con una combinación real de filtros del caso de prueba que no devuelve llamadas. |
| `error` | Error de carga acotado; los filtros existentes siguen disponibles y Reintentar recupera los datos localmente conservándolos. Los errores de conexión/fetch de producción usan la misma presentación recuperable. |
| `parcial` | Un texto de advertencia explica que se conservan los importes conocidos y que los valores faltantes no son cero; el estado parcial/error por llamada y los metadatos desconocidos siguen visibles. |
| `sin-permiso` | Rechazo acotado; no se muestran totales del registro, filtros, grupos ni llamadas. La aplicación de permisos del servidor queda fuera del mockup estático. |

No se introduce ninguna modificación editable del registro, validación de formulario, confirmación de guardado correcto, confirmación destructiva ni flujo de pago; esos estados no aplican. La revisión correcta es el estado normal. Contraer/expandir la atribución y alternar entre lista/detalle en teléfono son subestados locales accesibles. Una llamada fallida del proveedor es el estado de un registro y se distingue de un error al cargar el panel.

## 9. Comportamiento adaptable

Rango de diseño admitido: **desde 360px**; puntos de control de auditoría automatizada en 390px y 1280px; además, se realizó una comprobación de interacción en 360px con tema oscuro e interfaz en inglés. A partir de 1100px, márgenes laterales del shell de 40px, registro de 330px, inspector fluido y franja de filtros de tres columnas. Entre 768 y 1099px, márgenes de 24px, registro de 270px, dos campos de filtro con la acción de borrar debajo y metadatos de divulgación apilados. Por debajo de 768px, márgenes del shell/panel de 20px, etiquetas de encabezado/ruta ajustables en varias líneas, filtros apilados y un solo registro o inspector activo. El detalle del grupo seleccionado sigue disponible por completo después de seleccionarlo y volver; no se elimina en teléfono por considerarlo incompatible. Los nombres largos de cuentas, modelos e ids se ajustan en varias líneas. El precio de la llamada puede pasar debajo de su título. La página tiene desplazamiento vertical y no tiene desplazamiento horizontal.

## 10. Accesibilidad y paridad de movimiento

WCAG 2.2 AA es el objetivo de diseño; esta auditoría de maqueta aporta evidencia de propiedades medidas, no una afirmación general de cumplimiento. Están presentes las etiquetas asociadas, los selectores y paneles de divulgación nativos, los encabezados semánticos, los totales y estados dinámicos, la alerta si falla la carga, el contorno de foco visible de 3px y una altura mínima de 44px para los controles. Los grupos seleccionados se distinguen mediante un cambio de texto y contorno, además del estado presionado, no solo mediante el color. Las cifras monetarias indican USD y si son estimaciones o coberturas. El permiso y el estado de llamada no se infieren del color.

El movimiento expresivo sigue siendo legible sin ocultar texto. `useMotionProfile` proporciona el perfil y el estado de movimiento reducido; CSS usa esos tiempos. La preferencia de movimiento reducido del sistema operativo, Quieto y `?still=1` suprimen el desplazamiento, la animación cíclica del esqueleto y las transiciones, y conservan todos los controles y el estado final. Las pestañas ocultas pausan las animaciones de CSS. Solo se ejecutan transiciones espaciales finitas y un esqueleto de carga; no se introduce ningún renderizador pesado fuera de pantalla, canvas ni animación decorativa cíclica.

## 11. Criterios de aceptación observables y evidencia

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 1280px | normal | El encabezado de Pictures/Sempertex, el contexto de idioma/cuenta, la navegación neutral y una hoja redondeada coinciden con la estructura compartida de la interfaz hermana. |
| B-AC-02 | 1280px | normal | El registro está a la izquierda del inspector, que es más ancho, y ambos tienen encima una franja de filtros compartida. |
| B-AC-03 | 360–767px | normal | Al elegir un grupo, se muestra su inspector y la acción para volver, sin desplazamiento horizontal de la página. |
| B-AC-04 | 390px | normal | Al volver desde el inspector, el foco regresa a la fila seleccionada del registro. |
| B-AC-05 | todos los compatibles | normal | Los filtros de usuario/tipo actualizan el total general y cada grupo a partir de los mismos registros. |
| B-AC-06 | todos los compatibles | normal | La navegación entre grupos y el reintento tras un error de carga conservan los filtros de producto seleccionados. |
| B-AC-07 | todos los compatibles | parcial | El total conocido es 0.0570 USD; una llamada con costo desconocido se identifica por separado. |
| B-AC-08 | todos los compatibles | parcial | Los tokens, el modelo y el costo desconocidos indican No informado; el uso conocido de errores del proveedor sigue incluido. |
| B-AC-09 | todos los compatibles | normal / parcial | La agrupación por proyecto conserva los ID de conversación en las filas de llamadas y mantiene separadas las conversaciones independientes. |
| B-AC-10 | 390 / 1280px | cargando / vacío / error | Se puede acceder a los esqueletos, la explicación del estado vacío y la acción de reintento desde Estado. |
| B-AC-11 | todos los compatibles | denegado | No se muestra ningún importe del registro, filtro, grupo ni llamada. |
| B-AC-12 | todos los compatibles | todos | Ambos temas y ES/EN conservan las etiquetas, el texto legible y la indicación de foco. |
| B-AC-13 | todos los compatibles | normal | En modo expresivo, el inspector tiene una entrada espacial en curso; con movimiento reducido o activado mediante «still», muestra su estado final sin una animación de desplazamiento en curso. |
| B-AC-14 | 390px | normal, atribución abierta | La atribución expandida cabe dentro de la hoja y no presenta problemas de contraste, relleno ni desbordamiento. |

Constructor final sin conexión: **APROBADO**, HTML autocontenido de 393 KB, 1,956 archivos de origen incluidos. Para la maqueta completa no se usó una alternativa en HTML simple ni se instalaron paquetes.

`contrast.py`: **se comprobaron 158 pares en los temas claro y oscuro; todos aprobados**.

`audit_mockup.py` final: **120 renderizados (120 combinaciones planificadas), 4,062 mediciones de texto, 384 paradas de foco**; código de salida 0.

**RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**

También se aprobaron las comprobaciones adicionales de Playwright: derivación de totales y filtros; atribución de proyectos y conversaciones; conservación de selecciones al cambiar la agrupación o reintentar; etiquetas de grupos con cuentas mixtas; divulgación de llamadas parciales; ocultamiento de datos en estado denegado; expansión de paneles de divulgación nativos; encabezado en teléfono y restitución del foco; reorganización a 360px con tema oscuro e inglés; animación activa del inspector y paridad de movimiento reducido; cero errores de JavaScript y cero solicitudes HTTP. La prueba de atribución abierta a 390px midió 67 elementos de texto y no encontró problemas de contraste, elementos no textuales, alineación, relleno, desbordamiento ni colores sin medir. Se inspeccionaron capturas renderizadas a 1280px con ambos temas y a 390px en vista de lista y detalle; ambas composiciones de miniaturas se inspeccionaron visualmente antes de la compilación completa. Las capturas se inspeccionaron en memoria; no se escribieron archivos de capturas ni registros sin asignar.

## 12. Preguntas abiertas e inquietudes

P: ¿Gasto IA debería ser un destino del mismo nivel que la administración de cuentas, con su propia página permitida, o una pestaña adicional dentro de las AdminTabs operativas actuales? La maqueta propone la navegación compartida entre secciones; aquí no se aprueba ninguna ruta.
P: ¿La consulta inicial debería incluir todo el historial conservado o un período de informes acotado? La fecha de los datos de prueba solo delimita los datos ilustrativos y no establece una ventana de fechas predeterminada en producción ni un nuevo requisito de filtro por fecha.
P: ¿Es aceptable mostrar USD con cuatro decimales? ¿Cómo deberían presentarse los costos conocidos no nulos pero menores para evitar que el redondeo parezca indicar un costo cero? La precisión de la maqueta es ilustrativa; no constituye una decisión sobre la precisión del registro ni las tarifas.

Responsable de la decisión: David con Planner. Estas preguntas no bloquean esta exploración acotada de planificación. Confirmado: los totales por proyecto conservan el detalle de conversaciones; las llamadas independientes se agrupan por conversación; el uso facturable conocido con errores del proveedor sigue incluido, y los valores faltantes se consideran desconocidos. Designer no ha aprobado ningún plan ni orientación.

Inquietudes: esta maqueta estática no valida la autorización del servidor, la integridad de la facturación del proveedor, la idempotencia de los reintentos, la paginación real con cursores, las identidades de las cuentas ni las marcas de tiempo reales. Esos aspectos corresponden a la ingeniería de SP-6 y a la aceptación independiente. La finalización canónica y la implementación del flujo de trabajo hermano quedan fuera de esta exploración. No se modificó código del repositorio ni contratos compartidos.
