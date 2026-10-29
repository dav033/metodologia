---
contract: gasto-ia
version: 1
revision: r1
artifact: direction-exploration
status: draft
subplan: SP-6
requirements: [R4, R5]
owner: David
author: Designer
date: 2026-10-29
direction: Desglose en el lugar (c)
source_behavior: gasto-ia@v1.r1.behavior.md
chosen_thumbnail: gasto-ia@v1.r1.dir-c.html.candidate-1.html
---

# Desglose en el lugar — dirección C

## 1. Identidad y trazabilidad

Exploración de planificación, **borrador; sin aprobar**. Esta es una dirección candidata para `gasto-ia@v1`, no el contrato canónico ni una aprobación de implementación. El brief de comportamiento compartido es la fuente de autoridad. Insumos: ese brief, SPEC “Behavior — SP-6 (round 12 pending)”, PLAN SP-6 y los artefactos Markdown y HTML canónicos paralelos `cuentas-admin@v1`, `planes@v1`, `proyectos@v1`. Las otras direcciones, los contratos compartidos, los archivos de planificación y los repositorios de producción no se modifican.

Alcance: selección del contrato/textos de T6.1, panel de control para el personal de T6.4, revisión de renderizado de T6.6; T6.5 aporta la verificación posterior de atribución/autorización en producción. El artefacto visual no implementa ni verifica un libro mayor o una API. La compatibilidad está **indeterminada hasta la selección por parte del propietario y la finalización**; no se reemplaza ninguna versión aprobada ni se redirige a ningún consumidor del plan.

## 2. Propósito y usuarios

Un Empleado interno o Administrador con `gasto.ver` revisa dónde se produjeron los gastos de IA pagados y luego los filtra por cuenta y tipo de llamada. Los mismos datos filtrados se pueden agrupar por sesión, elemento de trabajo o cuenta. La identidad del elemento de trabajo se compone del proyecto y el detalle de conversación cuando existe un proyecto; de lo contrario, corresponde a la conversación. Los subtotales de herramientas se muestran en los grupos expandidos; cada llamada muestra su proveedor/modelo y fecha.

Las cuentas de Usuario ordinario, las visitas sin sesión iniciada y las personas sin el permiso no reciben el libro mayor, los filtros, las identidades de otros usuarios ni los totales. Los fixtures estáticos de denegación solo ilustran la presentación; el servidor debe aplicar la autorización real tanto a la página como a su API.

## 3. Enfoque y jerarquía de la información

El cambio se integra en la superficie administrativa existente; **no es un producto independiente ni una nueva página de inicio**. La referencia actual es `t12/src/app/admin/page.tsx` → `src/components/admin/AdminTabs.tsx`; `asesor` aporta la misma configuración de tokens/tipografía del producto y un contenedor relacionado. La administración existente ya tiene un encabezado, un enlace de regreso al chat y navegación horizontal. Los contratos paralelos elegidos definen su cabecera actualizada de Pictures/Sempertex con anillo y punto, controles de idioma/cuenta, título de 24px, separador de ruta neutral y papel de trabajo con esquinas redondeadas. Se reutilizan esos elementos y solo se añaden el destino Gasto de IA y el contenido de gastos.

Orden de lectura: contexto de maqueta/datos/fecha → filtros de cuenta/tipo y filtro opcional de herramienta → un total de costos conocidos con información sobre integridad y cobertura de tokens → controles de agrupación → divulgaciones de grupo a ancho completo → cargar más/estado → aviso que solo muestra metadatos. La franja de totales usa dos columnas, no mosaicos KPI separados. Cada grupo de sesión/trabajo/cuenta contiene su subtotal, filas de llamadas y desglose por tipo/herramienta.

**Miniatura elegida: candidata 1.** Ambas composiciones pequeñas se diseñaron y renderizaron antes de la página de entrada completa. La candidata 1 mantiene todas las opciones de manipulación dentro del papel de trabajo y conserva espacio para los metadatos. La candidata 2 usa un panel permanente de subtotales por usuario, que compite con la navegación horizontal existente y reduce el ancho de los registros. Ambas usan los tokens del producto, Geist de producción incorporado y la marca existente; la instantánea de datos parciales de seis llamadas es intencionalmente más amplia que las cuatro llamadas correctas de la maqueta completa habitual.

## 4. Dirección de ocho ejes y sistema de diseño

| Eje | Expresión observable de esta dirección |
|---|---|
| Concepto | Cambiar los filtros donde se muestran sus valores actuales; abrir un grupo y una llamada justo donde se enumeran sus gastos. Los valores del libro mayor son de solo lectura. |
| Diseño | Cabecera/título/separador de ruta existentes; un papel con radio de 32px; área de filtros en línea, franja de totales de 1.2:1 y luego bandas continuas a ancho completo. Sin panel lateral de inspección. |
| Navegación | Separador de ruta de Administración y tres botones locales de agrupación; un grupo expandido; divulgación nativa anidada para las llamadas; filtro opcional de herramienta. |
| Tipografía | Geist/Geist Mono incorporadas existentes; H1 de 24px, nombres de grupo de 20px en escritorio/18px en teléfono, importe de 32px y detalles de 12–15px. Los números usan cifras tabulares. |
| Densidad | Márgenes interiores del papel de 28px en escritorio y 20px en teléfono; relleno de grupo de 24px; objetivos interactivos de 44px; los registros en teléfono se redistribuyen en lugar de convertirse en una tabla desplazable. |
| Componentes | Button y Skeleton reales instalados de shadcn/Base UI, selects/details nativos e iconos Lucide; controles de píldora, marca de anillo y punto y divulgación de cuenta existentes. |
| Color | Tokens exactos del tema Pictures; superficie neutral para el grupo activo; marca/foco morados; verde, aviso y error existentes para los estados registrados; datos desconocidos atenuados. |
| Movimiento | Secuencia finita de compresión/asentamiento con pulsación de grupo impulsada por resorte, asentamiento independiente de totales/divulgación, bandas escalonadas y alternativas inmediatas equivalentes con movimiento reducido. |

Fuentes de tokens inspeccionadas en modo de solo lectura: `src/app/globals.css` de ambos repositorios, `AdminTabs`, `CabeceraApp`, definiciones de diseño/tipografía y contratos paralelos. No se añaden paletas, familias tipográficas, paquetes ni recursos descargados de forma remota.

| Token del producto | Función en el kit / uso | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | `#faf9fc` / `#0b0c10` |
| `--superficie` | tarjeta/ventana emergente | `#ffffff` / `#16181f` |
| `--texto` | primer plano | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | primer plano atenuado | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | controles secundarios, atenuados y seleccionados | `#efe9f8` / `#242733` |
| `--superficie-suave` | fondo interior de llamada | `#faf8fd` / `#1c1e26` |
| `--acento`, `--sobre-acento` | primario, primer plano primario | `#6d3fe0`, blanco / `#9479ff`, `#120b24` |
| `--texto-tenue` | borde de entrada; alias accesible paralelo | `#766c85` / `#8a91a0` |
| `--borde`, `--borde-suave` | panel y separadores decorativos | `#e3daef`, `#efe9f8` / `#383c48`, `#2a2d38` |
| `--exito` | estado completado | `#1f7a55` / `#78d6a8` |
| `--aviso`, `--aviso-suave` | estado parcial/error facturable | `#8f5f12`, `#fff3d8` / `#f7c46b`, `#3f311c` |
| `--error`, `--error-suave` | estado/superficie de error | `#b23a45`, `#ffeaec` / `#ff979f`, `#43252a` |

Componentes instalados: `shadcn:button outline/ghost/default disabled/pressed/focus` de `@/components/ui/button`; `shadcn:skeleton loading` de `@/components/ui/skeleton`. Las bandas de grupo, los totales y las listas de metadatos específicas del producto son composiciones personalizadas, no componentes de biblioteca mal etiquetados. Las divulgaciones nativas de herramienta/cuenta/llamada son elementos HTML `details`, no un Accordion de shadcn. El movimiento usa `motion/react` y `@kit/motion`. El constructor real importa e incorpora los archivos tipográficos locales de producción.

## 5. Navegación e interacción directa

La estructura existente sigue siendo reconocible: encabezado de Pictures/Sempertex, control de idioma, menú de cuenta, título, Volver al chat y regla neutral de administración. Este prototipo de administración muestra Cuentas / Roles y permisos / Gasto de IA; en producción se deben omitir los enlaces hermanos cuando no se tengan sus permisos independientes. Mi cuenta, Planes y cerrar sesión siguen siendo destinos administrados por otras secciones. El prototipo muestra de forma transparente un aviso de alcance para esos enlaces, en vez de afirmar que esas páginas están implementadas.

No se ha especificado la URL exacta del producto para el gasto; `#gasto` local es un ancla del artefacto, **no un contrato de ruta**. La agrupación es navegación local dentro de la página, no tres rutas nuevas del producto. Los selectores nativos de planificación, fuera del producto, exponen `view`, `state`, `theme`, `motion`, con las etiquetas Vista/Estado/Tema/Movimiento. No se introduce ningún modal/cuadro de diálogo, así que `scene` no aplica.

La selección de cuenta y los botones Texto/Imagen/Todos cambian los filtros de inmediato. El menú opcional Herramienta muestra su selector nativo etiquetado. Al cambiar los filtros, se cierra el grupo expandido y se reinicia la paginación visible. Al borrar los filtros, se restauran todas las llamadas coincidentes y se abre el grupo inicial. La acción para borrar se muestra deshabilitada cuando no hay filtros aplicados y durante la carga.

Solo se abre un grupo a la vez. Al expandir las llamadas dentro del grupo se muestran la atribución, el proveedor/modelo, los campos de tokens, la fecha y el estado explícito de finalización/parcial/error; nunca se muestran los prompts ni el contenido generado. Los paneles expandidos conservan el foco del elemento que los activó. Los botones de agrupación mantienen su estado semántico de activado. El entorno estático vuelve a montar las vistas cuando cambia el inspector externo de vista/estado. Las opciones locales de inspección conservan los filtros y el idioma tras esos montajes; los botones de agrupación del producto devuelven el foco al nuevo control de agrupación activado sin interrumpir la escritura en los filtros. Este estado solo existe en la memoria del prototipo, sin escribir en el almacenamiento.

## 6. Flujos

1. **Revisar el gasto:** acceso autorizado → total conocido y cobertura → elegir agrupación por sesión/trabajo/cuenta → abrir un grupo → inspeccionar subtotales por tipo/herramienta → expandir una llamada para ver los metadatos del registro.
2. **Acotar la revisión:** elegir cuenta y tipo; mostrar el selector de herramienta si se desea → el total derivado, la cobertura y todos los grupos se actualizan juntos → borrar los filtros para recuperar el alcance completo. No existe una operación para editar/guardar registros financieros.
3. **Investigar el uso incompleto de un proveedor:** seleccionar el estado parcial/error en la inspección → se incluye el costo conocido facturable → los campos desconocidos conservan las etiquetas explícitas desconocido/no informado → cargar más para ver una sesión cuyo costo es totalmente desconocido. Nunca se inventa un cero para un valor desconocido.
4. **Recuperarse de un error de consulta:** no se muestra ningún total sin confirmar → los filtros siguen disponibles → Reintentar restaura el prototipo de datos exitoso. En producción se debe volver a ejecutar la consulta autorizada del servidor con esos filtros.
5. **Revisar grupos adicionales:** Cargar más agrega dos grupos de prototipo sin duplicar los totales. El total siempre representa todos los resultados filtrados, no solo la página visible. En producción se necesitan agregados filtrados completos calculados por el servidor y paginación de detalles segura mediante cursor.
6. **Acceso denegado/sesión cerrada:** mostrar la explicación de rechazo o inicio de sesión correspondiente sin el registro → ofrecer recuperación mediante Mi cuenta o el inicio de sesión en los destinos existentes. Nunca se deben obtener los datos prohibidos para luego simplemente ocultarlos.

## 7. Vistas y semántica de los datos

| Vista del inspector | Identidad del grupo principal | Detalle conservado |
|---|---|---|
| `sessions` | Sufijo visible de la sesión, cuenta, elemento de trabajo y costo | Las llamadas individuales incluyen proyecto/conversación, proveedor/modelo, tokens de entrada/salida/totales y fecha. |
| `work` | Proyecto, si existe; de lo contrario, conversación | Cada llamada conserva la atribución de conversación, cuenta y sesión, incluidas varias sesiones del mismo proyecto. |
| `users` | Identidad de la cuenta y su costo | La atribución de sesiones, proyecto/conversación y tipo/herramienta se conserva dentro del grupo de la cuenta. |

Todas son disposiciones del mismo panel que solo muestra metadatos. En producción, la agrupación debe usar ID estables del servidor, no sufijos visibles ni nombres de proyecto. No es necesario exponer los ID completos para revisar el gasto.

Datos sintéticos normales: cuatro llamadas exitosas entre dos cuentas y dos sesiones. Los costos en USD son `0.0042 + 0.0600 + 0.0030 + 0.0360 = 0.1032`. El total de texto es `0.0072`; el de imágenes es `0.0960`. La sesión …a41 suma `0.0642` y la …b72, `0.0390`. Dos llamadas informan los tokens totales, que suman 4,800; las otras dos no. La cobertura siempre se muestra para evitar que la suma se confunda con un total completo de tokens.

Los datos parciales/de error agregan una llamada con error del proveedor y costo conocido de `0.0010` y 300 tokens totales conocidos, además de otra sesión con error del proveedor, 1,200 tokens totales conocidos y costo desconocido. El costo conocido pasa a `0.1042` en **5/6 llamadas con costo conocido**; los tokens totales suman 6,300 en **4/6 llamadas con tokens conocidos**. La sesión cuyo costo es totalmente desconocido muestra «Desconocido», no `$0.0000`. Los campos disponibles de tokens de entrada/salida/totales se informan de forma independiente; los campos no disponibles permanecen como «No informado». No se presupone que la suma de entrada + salida esté completa.

Todas las fechas del prototipo usan la fecha de sesión proporcionada **2026-10-29**, etiquetada como UTC, sin inventar fechas históricas, nombres de clientes ni correos electrónicos. Google/gemini-3.6-flash y fal.ai/FLUX.2 son vocabulario existente de proveedores/modelos encontrado en los repositorios. Los costos de ejemplo son importes ilustrativos del registro, no afirmaciones sobre precios de proveedores. No se necesitó investigar en la red, llamar a proveedores ni instalar paquetes.

## 8. Estados

| Estado del inspector | Presentación / recuperación |
|---|---|
| `normal` | Llamadas exitosas, un grupo abierto inicialmente, totales y cobertura; los metadatos desconocidos de tokens siguen visibles como desconocidos. |
| `loading` | Tres Skeletons reales con forma de fila, estado Cargando gasto, `aria-busy`; sin totales obsoletos y con las modificaciones de filtros deshabilitadas. |
| `empty` | Explicación de que no hay llamadas y opción para borrar/cambiar filtros; sin un total cero engañoso. Abarca tanto la ausencia de llamadas coincidentes como la falta de uso registrado. |
| `error` | Sin cifras sin confirmar, explicación explícita del error de carga, filtros conservados y opción Reintentar. |
| `partial` | Aviso explícito de uso parcial/error del proveedor, uso facturable conocido incluido y valores desconocidos preservados; la tercera sesión está disponible con Cargar más. |
| `denied` | Prototipo de cuenta normal, sin registro ni filtros, con opciones Sin acceso y recuperación mediante Mi cuenta. |
| `signed-out` | Sin menú de cuenta ni registro; explicación del inicio de sesión y destino existente para iniciarla. |

Los controles reales ejercitan los estados de puntero, foco, activado, deshabilitado y panel expandido/contraído. Los errores de validación de filtros no aplican a los selectores enumerados. El éxito al guardar, la edición, eliminación, configuración de presupuesto, exportaciones y diálogos de aprobación quedan fuera del alcance. No se inventa una caché sin conexión independiente ni una promesa de actualización: una lectura inicial no disponible usa el estado de error de carga y oculta los totales. La consulta en curso de la página dos y su reintento siguen siendo comportamientos de producción que requieren una decisión; la adición local del artefacto es instantánea y no demuestra la confiabilidad de la red.

## 9. Comportamiento adaptable

Conservar los cambios de diseño de 760px/1100px de las secciones hermanas y un **mínimo de 360px**.

| Rango | Comportamiento |
|---|---|
| 1101px+ | Ancho máximo de la aplicación de 1520px, relleno exterior de 40px, margen interior del panel de 28px; filtros en línea; franja de totales en dos columnas; cuadrícula de identidad/metadatos/costo/flecha para los grupos; metadatos expandidos en tres columnas. |
| 761–1100px | Relleno exterior de 28px; los metadatos del grupo aparecen debajo de la identidad; costo y control de expansión permanecen alineados a la derecha; los metadatos expandidos pasan a dos columnas. |
| 360–760px | Relleno exterior/interior del panel de 20px; el encabezado se ajusta de forma natural; los filtros y la franja de totales se apilan, los botones de tipo permanecen en una fila de tres controles; los botones de agrupación pasan a un grupo vertical etiquetado; el importe aparece después de su identidad; los metadatos de llamadas pasan a una columna. El menú desplegable de cuenta se alinea con su borde izquierdo dentro de la ventana. No hay desplazamiento horizontal de la página. |

Se puede elegir español e inglés en ambos temas; el prototipo no cambia ninguna preferencia de idioma persistida. Las etiquetas largas de modelos/identidad se ajustan a varias líneas. Se espera desplazamiento vertical para ver los detalles. No hay interacciones que dependan solo de arrastrar ni pérdida de metadatos exclusiva para móviles.

## 10. Accesibilidad y movimiento

WCAG 2.2 AA es el objetivo de implementación, no una certificación. Los selectores nativos etiquetados, paneles nativos, encabezados y listas de definición semánticos, botones de agrupación/tipo con estado de activación, anuncios de estado de actividad/estado/alerta y controles de 44px como mínimo facilitan la navegación con teclado. El foco usa un contorno de acento de 3px con un desplazamiento de 4px. Los controles seleccionados conservan un contorno, no dependen solo del color. Los estados parcial/error también se expresan con texto explícito. No hay trampa de foco porque no se introduce ningún diálogo.

Gramática de movimiento: el registro de bandas se comprime y se estabiliza con intervalos de 55ms; el total se asienta horizontalmente cuando cambian los filtros; el grupo expandido se asienta verticalmente; los campos expandidos de llamadas/filtros se comprimen horizontalmente; los avisos se estabilizan de forma independiente. Los perfiles expresivo, natural y sutil duran 520/170/55ms, 320/140/30ms y 160/100/12ms (estabilización/control/desfase), respectivamente. La curva de aceleración del producto es `cubic-bezier(.34,1.4,.64,1)`. Al presionar un grupo se usa el resorte real del perfil; los controles se comprimen al presionarlos y mantienen la legibilidad sin bajar la opacidad. Las animaciones son finitas y solo transforman elementos; las pestañas ocultas pausan el movimiento CSS. No se agrega ningún bucle ambiental.

El movimiento reducido del sistema operativo, Quieto y `?still=1` desactivan el desplazamiento, el escalado, los fotogramas clave y las transiciones, y conservan los mismos campos, controles y estados. El estado de movimiento reducido del entorno se pasa a Motion; nada depende del movimiento para comunicar el estado.

## 11. Criterios de aceptación observables y evidencia real

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| C-01 | 360px+ | todos | La marca Pictures/Sempertex, el control de idioma, el título de tarea de 24px y el pie de página existente siguen siendo reconocibles en ambos temas. |
| C-02 | 1101px+ | normal | Los filtros en línea preceden a una franja de totales de dos columnas y a grupos de ancho completo; no hay un inspector lateral permanente ni una cuadrícula de tarjetas KPI. |
| C-03 | 360–760px | normal | Todos los filtros y controles de agrupación caben en la página; el importe de un registro aparece después de su identidad, sin desplazamiento horizontal. |
| C-04 | 360px+ | normal | Al seleccionar Texto se muestra `$0.0072`; al intersectar con la cuenta A se muestra `$0.0042`; el foco permanece en el control modificado. |
| C-05 | 360px+ | normal | Al expandir una llamada se muestran la cuenta/sesión/elemento de trabajo/proveedor/modelo/fecha y los campos de tokens disponibles por separado. |
| C-06 | 360px+ | partial | El total muestra `$0.1042`, una cobertura de costos de 5/6 y 6,300 tokens totales conocidos en 4/6 llamadas. |
| C-07 | 360px+ | partial | Cargar más muestra la tercera sesión; su costo es desconocido y el total de todos los resultados no cambia. |
| C-08 | 360px+ | loading / error | Los Skeletons o la recuperación tras un error de carga sustituyen las cifras; no se muestra ningún total sin confirmar. |
| C-09 | 360px+ | denied / signed-out | No aparecen el registro ni los filtros; se ofrece la recuperación existente correspondiente de cuenta/inicio de sesión. |
| C-10 | 360px+ | empty | Se muestra la explicación de que no hay llamadas y la opción para borrar los filtros; no se inventa un cero monetario. |
| C-11 | 390 / 1280px | expanded | Los metadatos, el menú de cuenta y el selector de herramienta siguen siendo legibles y conservan espacio respecto a los bordes de la pantalla en ES/EN y ambos temas. |
| C-12 | 360px+ | reduced / still | Todo el contenido y la retroalimentación siguen disponibles, sin movimiento finito en curso. |

### Verificación declarada

- Estado real del espacio de trabajo instalado: instalado/compilado; **96/96** entradas disponibles. Se usó el generador sin conexión requerido, con ruta absoluta, para la ruta TSX/salida de esta dirección. Sin alternativa, instalación, recursos externos ni escritura canónica.
- `contrast.py`: **158 pares comprobados en claro y oscuro; todos aprobados**.
- Auditoría requerida de Playwright: **84 representaciones / 84 combinaciones planificadas**, **2,648 mediciones de texto**, **432 paradas de foco**. Salida final recompilada: `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`.
- Ejecución suplementaria de interacciones: **43 comprobaciones aprobadas** (filtros y retención del foco, visibilidad de herramientas, metadatos, totales, semántica parcial/desconocida, cargar más, las tres agrupaciones, supresión al denegar/sin sesión, reintento de carga, 24 comprobaciones de desbordamiento por idioma ES/EN/tema/ancho, sin errores de ejecución ni solicitudes de red).
- Se inspeccionaron en memoria capturas renderizadas a 1280/390 en ambos temas; también se renderizaron las miniaturas antes de la composición completa. No se escribieron capturas fuera de los archivos asignados.
- Las comprobaciones adicionales ampliadas de metadatos/cuenta/herramientas detectaron inicialmente que el menú desplegable de cuenta para teléfono estaba demasiado cerca del borde de la pantalla. Se ajustó la alineación a la izquierda por debajo de 760px y se tradujo la etiqueta del rol al inglés; la repetición aprobó las **8 combinaciones ampliadas de metadatos/cuenta/herramientas** en ES/EN, ambos temas y 390/1280px. El fallo inicial no se cuenta como aprobado.
- También se aprobaron las comprobaciones de regresión de la salida final recompilada: la agrupación conserva los mismos filtros/idioma y devuelve el foco al botón activo; el reintento conserva los filtros. Las 24 combinaciones adaptables y las 8 comprobaciones ampliadas volvieron a aprobarse tras este cambio.
- El muestreo de animación en vivo observó los fotogramas clave reales `total-seat`, `band-settle`, `disclosure-seat` con una duración de 520ms. Los selectores de evidencia JSON identifican los controles y el movimiento renderizados, no el cuerpo.
- No se ejecutaron lint, comprobación de tipos, pruebas ni compilación de producción: los repositorios eran de solo lectura y no se modificó código de producción. La compilación estática y la auditoría del navegador no demuestran autorización del servidor, integridad del registro, idempotencia ni comportamiento real del cursor; esas responsabilidades siguen en T6.5/T6.6.

## 12. Preguntas abiertas, supuestos y preocupaciones

**Confirmado:** acceso solo a metadatos con `gasto.ver`; filtrado por cuenta/tipo; agrupación por sesión/usuario/trabajo; detalle de proyecto más conversación o conversación independiente; se conserva el uso facturable conocido de errores; los campos desconocidos del proveedor nunca se inventan. El libro de registros es de solo lectura en este alcance.

**Decisiones visuales provisionales:** un grupo expandido inicialmente, tres modos de agrupación, filtrado opcional por herramienta, cuatro decimales en USD, fecha etiquetada explícitamente como UTC, integridad total junto a la integridad de tokens y agregado completo filtrado sobre los grupos paginados. Esto no autoriza un nuevo contrato de API ni una configuración del producto.

P: ¿Cuál es la ruta final del gasto y la entrada de administración con permisos para Empleado interno, conservando el marco de navegación del módulo hermano y ocultando los enlaces Cuentas/Roles cuando falten sus permisos?
P: ¿El personal debe revisar las fechas en UTC, como se indica explícitamente en esta exploración, o en America/Bogota, como en el registro de cuentas del módulo hermano?
P: ¿Cuatro decimales son suficientes para la estimación de USD mostrada, o los importes inferiores a $0.0001 deberían usar una precisión mayor para conservar los valores distintos de cero?
P: ¿Qué texto y opciones de recuperación deben mostrarse cuando falla la carga de una página posterior del cursor, y deben seguir disponibles los grupos ya confirmados? La anexión en el mock local no simula ese estado asíncrono.

Responsable de la decisión: David junto con el Planner. Estas preguntas no bloquean la exploración y deben resolverse o quedar explícitamente pendientes para la finalización antes de la implementación. Aquí no se aprueban cambios de permisos, cuentas, planes ni navegación fuera de SP-6. El artefacto sigue **siendo un borrador a la espera de elegir una dirección**, y los archivos canónicos `gasto-ia@v1.md`/`.html` no se modifican.
