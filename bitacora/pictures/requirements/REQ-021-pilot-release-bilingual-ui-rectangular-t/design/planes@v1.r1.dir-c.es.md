---
contract: planes
version: 1
revision: r1.dir-c
status: draft
artifact: independent-direction-exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
name: Pliegues de consulta
chosen_thumbnail: planes@v1.r1.dir-c.html.candidate-2.html
---

# Pliegues de consulta — dirección C

## 1. Identidad y trazabilidad

Esta es una exploración independiente completada, **en borrador y sin aprobación**. No crea ni reemplaza `planes@v1.md`, `planes@v1.html` ni un contrato canónico de implementación. La selección del responsable y la finalización posterior son procesos separados. Alcance: `planes@v1.r1.behavior.md`, R17–R20, SP-14; contexto: SPEC, PLAN y SP-14 actuales en PLAN.json. Las tareas de contenido T14.1, planes públicos T14.2, enlaces de entrada T14.3 y revisión visual independiente T14.5 son los consumidores de UI afectados. No se modifican tareas de ingeniería ni archivos de producción.

Evidencia del producto en modo de solo lectura: t12 `src/app/globals.css`, `layout.tsx`, `login/page.tsx`, `login/LoginForm.tsx`, `CabeceraApp.tsx` y `MenuApp.tsx`; asesor es la segunda fuente del producto. Se inspeccionaron los archivos Markdown y HTML seleccionados/finalizados `cuentas-admin@v1`, `taller-esenciales@v1` y `proyectos@v1` como entradas compartidas de superficie. El encabezado principal de Parte de acceso de SP-2 r13, el eje central del formulario, el texto y las formas tienen prioridad sobre el inicio de sesión de producción anterior, que solo admite contraseña, y los estilos exploratorios de las interfaces complementarias. La entrada reutiliza la base CSS exacta de SP-2 r13, las importaciones de recursos de fuente de producción y la estructura de la aplicación/encabezado; solo agrega bandas de planes y enlaces de entrada acotados. No propone un diseño alternativo de cuenta.

## 2. Propósito y usuarios

Una persona, con o sin sesión iniciada, responde: ¿qué herramientas incluye cada plan y cuál es su precio mensual en el idioma de esta interfaz? El éxito consiste en leer los cuatro planes en el orden del catálogo, incluidas todas las anotaciones de funciones no disponibles, y luego volver a la superficie de origen. No hay acciones de compra, solicitud, registro, contacto, suscripción ni cambio de acceso.

La interacción directa se aplica a la **presentación**: contraer una lista en el lugar, volver a abrirla o enfocar un plan desde la navegación local. Los precios, las herramientas y la asignación de planes no se pueden editar aquí. Esto conserva el comportamiento exclusivamente informativo del informe.

## 3. Composición, jerarquía y selección de miniatura

**Candidata 1:** un selector de cuatro planes a la izquierda y un lector de herramientas del plan activo. Conserva una comparación compacta de precios, pero oculta las herramientas de los demás planes y exige selecciones repetidas para compararlas de forma acumulativa.

**Candidata elegida 2:** cuatro bandas continuas delimitadas por líneas. La identidad y el precio mensual quedan a la izquierda y las listas acumulativas completas de herramientas, a la derecha. Todas las listas empiezan expandidas. Contraer una lista de forma independiente reduce la repetición sin ocultar un plan ni su precio. Un índice de planes que se ajusta a varias líneas expande, desplaza la vista hasta el destino contraído y lo enfoca. Mantiene la comparación en la misma posición de lectura, sin cuadrícula de tarjetas con aspecto de pago, nivel promocionado, sustitución por pestañas ni estructura de página de inicio separada.

Ambas composiciones de miniatura se dibujaron antes de crear la entrada y se inspeccionaron visualmente a 1280px. Son estudios de composición intencionalmente pequeños, no contratos interactivos completos; el TSX/HTML completo incluye ambos temas, selectores, estados y comportamiento adaptable.

### Tabla de ocho ejes

| Eje | Enfoque representado |
|---|---|
| concepto | Pliegues de consulta: plegar y volver a desplegar directamente las listas de herramientas en las franjas originales de sus planes; los datos del catálogo siguen siendo informativos e inmutables. |
| diseño | Una hoja con cuatro franjas delimitadas a todo lo ancho. En escritorio, las franjas ubican la identidad y el precio en una columna izquierda del 28 %, y todas las herramientas acumuladas en una región derecha de dos columnas; en teléfonos, apilan la identidad sobre una única lista de herramientas. |
| navegación | Cuatro enlaces internos que se ajustan a varias líneas expanden la franja de destino, la desplazan a la vista y enfocan su encabezado. Cada plan tiene un control de expansión independiente. Se conservan los enlaces de acceso e ingreso a la cuenta y el enlace contextual para volver. |
| tipografía | Geist Sans y Geist Mono, ya incrustadas. H1 fijo de 24px, nombres de planes de 20px, precios tabulares de 22px (20px en teléfonos), herramientas de 14px y anotaciones de disponibilidad de 12px; no se incorpora otra familia tipográfica. |
| densidad | Franjas compactas delimitadas de 24px dentro de una hoja con radio de 32px, e inserción interior de 28px en escritorio y 20px en teléfonos. Todas las herramientas son visibles inicialmente; al plegar se oculta la lista, pero se conservan el nombre y el precio mensual. |
| componentes | Cabecera de Pictures y control de cuenta nativo ya existentes, Button e Input reales de shadcn/Base UI, Skeleton real, artículo semántico y lista de herramientas. Los controles Button de expansión reemplazan cualquier acción para adquirir un plan. |
| color | Paleta exacta de globals.css de Pictures, asignada a los roles del kit con el alias hermano para el borde de entrada --texto-tenue. Navegación y marcas de verificación neutrales; el acento se limita a la marca, los enlaces, el foco y la acción del formulario de acceso ya existente. |
| movimiento | Franjas táctiles que se comprimen y se asientan: registro con translateY/scaleY de 480ms, escalonado en intervalos de 65ms, respuesta de presión de 180ms, chevrones de expansión giratorios y aparición de la lista de herramientas con asentamiento elástico. Motion según el perfil, paridad del estado final en modos silencioso/reducido y pausa de CSS con pestaña oculta. |

## 4. Sistema de diseño fijo y vocabulario de componentes

Reutilizar la cabecera de Pictures/Sempertex con anillos y puntos, el control de idioma, el control de cuenta, la hoja de acceso centrada y con bordes redondeados, el pie de página y el contenido neutral delimitado. No se incorpora una paleta, identidad, tipografía, descarga de recursos ni dependencia nueva. Todos los archivos tipográficos son recursos locales de Next existentes, incrustados como URI de datos por el builder real.

| Token del producto | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--texto` | primer plano | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, hover neutral | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, primer plano primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--borde`, `--borde-suave` | borde de hoja, separador de fila | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | borde de entrada/control, alias hermano accesible heredado | #766c85 / #8a91a0 |

Conservar Geist Sans / Geist Mono y las formas hermanas: panel de 32px, inserción interior de 24px, campo de 18px y píldora de 999px. Cuerpo de 15px; los tamaños de texto por rol figuran en la tabla de ejes. Ningún relleno de acento señala un plan recomendado. La disponibilidad se expresa con texto legible, no con color ni una acción deshabilitada. Las líneas decorativas no son controles.

| Componente | Fuente instalada y rol |
|---|---|
| `shadcn:button outline expanded/collapsed` | `@/components/ui/button`; Button real de Base UI, control independiente para expandir la lista de herramientas, `aria-expanded` y `aria-controls` |
| `shadcn:button outline ready` | La misma importación; reintento del catálogo y acciones de cuenta ya existentes |
| `shadcn:button default ready/disabled` | La misma importación; solo el contexto sin cambios del formulario de acceso |
| `shadcn:input default/disabled` | `@/components/ui/input`; contexto conservado del formulario centrado de inicio de sesión/cuenta |
| `shadcn:skeleton loading` | `@/components/ui/skeleton`; cuatro franjas neutrales, sin inventar precios |
| `native:details account closed/open` | Control de cuenta SP-2 ya existente, con exactamente un enlace Plans agregado |
| `native:select language/theme/view/state/motion` | Selector de idioma del producto ya existente y controles de inspección en tiempo de ejecución |
| `custom:plan-band` | Artículo semántico, encabezado, precio, Button de expansión real y lista de herramientas; composición específica de SP-14 |
| `motion:tool-list` | `motion/react` con `useMotionProfile` de `@kit/motion`; respuesta de presión/asentamiento, sin acciones que solo puedan realizarse arrastrando |

## 5. Navegación e interacciones

Los controles nativos de inspección en tiempo de ejecución conservan los identificadores `view`, `state`, `theme`, `motion`, las etiquetas en español y la etiqueta Mockup. No se define ningún diálogo, por lo que no corresponde un selector de escena. El cambio entre ES/EN del producto actualiza conjuntamente los nombres, el texto de las herramientas y la moneda mensual; el idioma inicial es inglés si el navegador está en inglés y español en los demás casos. Al cambiar la vista/el estado en esta exploración se conserva el idioma del producto que se haya seleccionado explícitamente.

Ruta pública `/planes`: sin menú de cuenta; el enlace para volver lleva a `/login`. Ruta de `/planes` con sesión iniciada: conserva el control de cuenta; el enlace para volver restaura el origen. Mi cuenta es la superficie ilustrativa de origen con sesión iniciada en esta exploración acotada. En producción se debe conservar la ruta de entrada segura del mismo origen, en lugar de forzar siempre Mi cuenta. La entrada directa con sesión iniciada y sin origen puede llevar a Mi cuenta.

Los enlaces internos expanden su destino, enfocan su H2 y desplazan la página dejando espacio para la barra fija de inspección. Con movimiento reducido, el desplazamiento es inmediato. Plegar/desplegar mantiene el foco del teclado en el mismo Button; el contenido plegado queda oculto y no simplemente recortado mientras sigue siendo legible con el teclado. Se pueden mantener abiertas varias franjas. El estado del plan es solo de presentación y no indica que un plan esté asignado, activo o seleccionado para el acceso.

## 6. Flujos

1. **Entrada pública:** inicio de sesión → su único enlace Plans → planes públicos → cuatro franjas expandidas → plegar/volver a desplegar opcionalmente → Volver a iniciar sesión. El formulario de inicio de sesión y las indicaciones para restablecer la contraseña conservan la estructura y el texto elegidos en SP-2; no se agrega un control de registro.
2. **Entrada con sesión iniciada:** Mi cuenta → control de cuenta nativo → su único enlace Plans → planes con sesión iniciada → volver → Mi cuenta. La identidad neutral de prueba del menú es Cuenta Entusiasta / entusiasta@prueba.local y coincide con los datos de prueba de la cuenta. En la sección de planes no aparecen roles del personal ni claves de permisos.
3. **Idioma:** navegador en inglés → Enthusiast / Free, 7 / 14 / 25 USD al mes; español → Entusiasta / Gratis, 20.000 / 45.000 / 70.000 COP al mes. Solo se muestra la moneda activa.
4. **Expansión:** activar Ocultar herramientas → la misma franja conserva la identidad/el precio y muestra Mostrar herramientas → activar de nuevo o usar su enlace de índice local → las herramientas acumuladas vuelven a aparecer en su lugar. Enter/Espacio y la activación con puntero producen el mismo resultado.
5. **Falla del catálogo:** seleccionar error, vacío, parcial o sin conexión → no mostrar precios de planes ni comparaciones de herramientas sin confirmar → reintentar → catálogo completo de cuatro planes. Esta es una transición local de prueba, no una demostración de un servicio de producción.

## 7. Vistas y contenido

| Selector de vista | Superficie | Cambio visible |
|---|---|---|
| `public` | `/planes`, sin sesión iniciada | Cabecera existente sin menú de cuenta; H1 nominal, enlace contextual para volver, índice de planes con ajuste de líneas, una hoja de planes delimitada, explicación de asignación y pie de página existente |
| `signed` | `/planes`, con sesión iniciada | La misma comparación, más el control de cuenta existente con un enlace Plans |
| `login` | contexto de entrada `/login` | Diseño y texto de acceso SP-2 centrados ya existentes, con un enlace Plans agregado después de las indicaciones para restablecer la contraseña |
| `account` | contexto de entrada `/cuenta` | Formulario de cuenta centrado ya existente y control de cuenta nativo con un enlace Plans agregado; no rediseña la cuenta |

Cada plan enumera todas sus herramientas acumuladas, en lugar de resumir beneficios heredados. Un único catálogo de prueba contiene los nombres, los precios en moneda y las filas de herramientas. Entusiasta muestra Chat con límites; Designer y los planes superiores muestran Chat con límites más altos. Designer Plus y Master Designer muestran Chat ampliado, Detección de estructuras y Detección avanzada de globos, cada una con la anotación exacta de disponibilidad. Calculadora de costos se mantiene disponible según el brief de UI. Master tiene una única entrada de Taller 3D que comprende todo el editor, incluido el explorador de decoraciones prediseñadas; no hay una segunda línea para el explorador. A continuación se pregunta explícitamente si se debe incluir el catálogo del producto, dado que está en el accesorio de prueba hermano, pero no se enumera en R16.

Las marcas de verificación de disponibilidad son decorativas y el texto repetido transmite todo el significado. No se muestran umbrales numéricos de chat, titulares promocionales, pruebas ficticias, afirmaciones de mejor plan ni llamadas a la acción para adquirir planes. Los formularios de cuenta/inicio de sesión son contexto visual, no implementaciones completas de autenticación, restablecimiento o cambio de contraseña. Sus envíos simulados nunca envían credenciales ni escriben en el almacenamiento.

## 8. Estados

| Selector de estado | Comportamiento de planes | Aplicabilidad al contexto de entrada |
|---|---|---|
| `ready` | Cuatro franjas expandidas con todos los datos | Contexto habitual de inicio de sesión/cuenta |
| `folded` | Se conservan los encabezados y precios de las cuatro franjas, con las listas ocultas de forma independiente | Estado de catálogo solo de presentación; el contexto de entrada no cambia |
| `loading` | Cuatro franjas de carga esqueleto, estado Cargando planes, sin estimaciones de precios | Campos/acción de inicio de sesión deshabilitados con la etiqueta En proceso; se conserva el contexto de cuenta |
| `empty` | Mensaje de catálogo no disponible + reintento; no representa un resultado legítimo de cero planes | No aplica a la identidad/formulario; se conserva el contexto de entrada |
| `error` | Alerta + reintento, sin inventar datos del catálogo | Rechazo ilustrativo de credenciales/cuenta SP-2; los formularios están fuera del alcance de implementación de SP-14 |
| `offline` | Explicación explícita de falta de conexión + reintento | Específico del catálogo; se conserva el contexto de entrada |
| `partial` | Cierre por defecto ante un catálogo incompleto; explicación + reintento | Específico del catálogo; se conserva el contexto de entrada |
| `menu-open` | Control con sesión iniciada visiblemente abierto; la página pública sigue sin mostrarlo | Menú de cuenta abierto en Mi cuenta; no aplica al inicio de sesión sin sesión iniciada |

El éxito corresponde a la comparación completa habitual; no hay notificación de éxito por cambios. Los controles deshabilitados/en carga del formulario pertenecen al contexto de entrada conservado. Una anotación de disponibilidad de un plan no es un control de selección deshabilitado. La denegación de permisos no aplica porque la comparación es pública e idéntica para todos los roles. La validación es una condición previa del catálogo: los campos faltantes nunca se convierten en precios vacíos o gratuitos. Los datos obsoletos y sin conexión no se presentan silenciosamente como actuales; las vistas previas parcial/sin conexión muestran un fallo recuperable. No existen cambios optimistas de plan, estados de compra pendiente ni diálogos.

## 9. Comportamiento adaptable

Conservar los puntos de quiebre elegidos en SP-2: **360–760px**, **761–1100px**, **1101px+**. La exploración también prueba la reorganización a 320px.

- A partir de 1101px, el ancho máximo de la aplicación es 1520px, con márgenes exteriores de 40px; la hoja de planes tiene una inserción interior de 28px; las franjas cuentan con columnas de identidad del 28 % y herramientas flexibles; las herramientas ocupan dos columnas en orden por fila.
- Entre 761 y 1100px, los márgenes de la aplicación son de 28px; la identidad ocupa al menos 190px junto a una columna de herramientas; los enlaces locales se ajustan a varias líneas sobre la hoja. No se introduce una tabla horizontal ni un carrusel.
- Entre 360 y 760px, los márgenes de la aplicación y la inserción interior de la hoja son de 20px; las herramientas de la cabecera se ajustan a varias líneas; el enlace para volver va después del H1; los enlaces de planes se ajustan a varias líneas; la identidad precede a una única lista de herramientas. El nombre ocupa el ancho de la franja; el precio y el control para desplegar comparten la siguiente fila cuando es posible. A 320px, el control para desplegar pasa a otra fila. El texto de las herramientas y las anotaciones de no disponibilidad se ajustan en puntos seguros.
- Todos los precios usan cifras tabulares. La moneda/mes se ajusta a otra línea sin recortarse. El menú de cuenta cabe en el ancho de la ventana. Se espera desplazamiento vertical; ninguna superposición fija inferior oculta el último plan o el pie de página.

## 10. Accesibilidad y movimiento

Objetivos: WCAG 2.2 AA para la revisión del producto renderizado, contraste de texto legible ≥4.5:1, bordes/foco de controles significativos ≥3:1 y controles nuevos de al menos 44px de alto. Los enlaces, selectores, botones y elementos details nativos conservan la operación estándar con teclado; un H1 y H2 secuenciales estructuran la comparación; cada artículo queda etiquetado por su H2. Los nombres accesibles de los controles de expansión incluyen el nombre del plan. La carga usa un estado y una región ocupada; los fallos usan una alerta; la disponibilidad de herramientas se expresa con texto visible. Los cambios de ruta enfocan el H1; los saltos internos enfocan el H2; los controles de expansión conservan el foco en el elemento que los activa. No se incorpora ninguna operación que dependa solo del hover, del arrastre o del color.

Gramática del movimiento: compresión que se asienta, sin crear una identidad nueva para la aplicación. `.plan-band` se registra con un asentamiento finito de translate/scale de 480ms, escalonado en intervalos de 65ms; los controles responden con transiciones de presión de 180ms y rotación del chevrón; la lista real de herramientas de Motion aparece con un resorte corto. Están conectados los perfiles sutil/natural/expresivo. Los modos silencioso, de movimiento reducido del sistema operativo y `?still=1` eliminan el desplazamiento y la animación, muestran el contenido final de inmediato y conservan exactamente las mismas interacciones. El registro CSS se pausa en pestañas ocultas; no hay efectos continuos ni intensos. Las auditorías renderizadas usan el estado asentado/reducido; a continuación se registra una inspección aparte de interacciones/animaciones.

## 11. Criterios visuales observables y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | 1101px+ | listo, cualquiera de los temas | Cuatro bandas con separadores aparecen en el orden del catálogo dentro de un mismo papel; la identidad/precio está junto a la región de herramientas. |
| C-AC-02 | 360–760px | listo ES/EN | Todas las bandas se apilan encima de una lista de herramientas en una columna, sin desplazamiento horizontal de página. |
| C-AC-03 | 761–1100px | listo | Las herramientas forman una columna junto a la identidad del plan; los enlaces a planes locales se ajustan. |
| C-AC-04 | 320–1280px | listo ES | Aparecen Gratis y 20.000 / 45.000 / 70.000 COP al mes, sin USD. |
| C-AC-05 | 320–1280px | listo EN | Aparecen Enthusiast / Free y 7 / 14 / 25 USD al mes, sin COP. |
| C-AC-06 | 320–1280px | listo | Aparecen exactamente tres anotaciones de funciones no disponibles en cada uno de Designer Plus y Master Designer. |
| C-AC-07 | 320–1280px | listo | El texto del chat distingue entre límites y límites mayores, y no contiene umbrales numéricos. |
| C-AC-08 | 320–1280px | listo | Solo Master Designer tiene la fila Taller 3D; no hay una fila independiente para el explorador. |
| C-AC-09 | 320–1280px | plegado | El nombre y el precio de cada plan permanecen visibles; al activar su botón se restauran las herramientas de la misma banda. |
| C-AC-10 | 320–1280px | plegado → listo | Un enlace a un plan local expande su destino, enfoca su H2 y lo mantiene despejado de la barra de inspección. |
| C-AC-11 | 320–1280px | inicio de sesión | Exactamente un enlace Plans abre la comparación pública, sin menú de cuenta. |
| C-AC-12 | 320–1280px | menú abierto | Exactamente una entrada Plans abre la comparación con sesión iniciada; el botón contextual para volver regresa a Mi cuenta en este fixture. |
| C-AC-13 | 320–1280px | carga | Cuatro bandas neutras de esqueleto y un estado de carga sustituyen los precios de la comparación. |
| C-AC-14 | 320–1280px | vacío/error/parcial/sin conexión | Un motivo y una acción para reintentar sustituyen la comparación; el reintento restaura las cuatro bandas. |
| C-AC-15 | 320–1280px | ambos temas | El anillo de foco y los bordes del control desplegable siguen siendo claramente distinguibles. |
| C-AC-16 | 320–1280px | quieto/reducido | No queda ningún desplazamiento de entrada; todo el contenido y los controles de planes producen los mismos resultados. |

Verificación final de los artefactos de planificación (2026-10-27):

- Generador real sin conexión: **PASS**, HTML final de 559 KB, 2.031 archivos de origen empaquetados; sin fallback, instalación, descarga de recursos ni dependencia de red en ejecución.
- `contrast.py`: **158 pares comprobados en temas claro y oscuro; todos pasan**.
- `audit_mockup.py` final: **128 representaciones / 128 combinaciones planificadas**, 3.300 mediciones de texto, 402 paradas de foco, ambos temas a 1280/390px. Sin advertencias por muestreo.
- **RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**
- Ejecución complementaria de interacción y reflujo: **917 aserciones PASS**, incluidas **896 combinaciones de reflujo** en 320/360/390/760/768/1100/1280px, ambos temas, ambos idiomas, las cuatro vistas y los ocho estados de inspección; sin excepciones de página ni solicitudes HTTP externas. Las aserciones cubrieron los precios ES/EN, el orden del catálogo, seis anotaciones de elementos no disponibles, la fila Taller exclusiva de Master, los enlaces de entrada pública y con sesión iniciada, la navegación de retorno, el plegado mediante teclado, la expansión del índice y el foco, y la recuperación. Esta ejecución precedió a la corrección final de un solo ajuste del rótulo móvil.
- La corrección localizada final se verificó con la auditoría renderizada indicada arriba y **56 casos renderizados enfocados / 224 comprobaciones de contención del chevrón desplegable**, todos PASS, en los mismos siete anchos, ambos temas, ambos idiomas y la comparación expandida/plegada. Sin problemas de contraste, bordes, alineación, relleno, desbordamiento ni hallazgos sin medir. La inspección visual había detectado que el chevrón del teléfono en español quedaba fuera de su píldora; permitir que el rótulo se ajuste de línea lo mantiene dentro, como confirman la captura final y las comprobaciones de contención.
- Inspección de evidencia y movimiento: cuatro animaciones `band-settle` en curso al cargar; dos animaciones activas de revelación de listas de herramientas al volver a abrir; todos los selectores JSON coincidieron con su vista declarada (el desplegable de cuenta solo aparece con sesión iniciada); el modo quieto deja la transformación de la banda en `none`. Se inspeccionaron capturas en memoria de miniaturas, comparación de escritorio, comparación de teléfono en tema oscuro, inicio de sesión público y contexto del menú de cuenta con sesión iniciada. No se escribieron archivos de captura adicionales.

Estas comprobaciones corresponden únicamente a la maqueta de planificación. No acreditan lint, tipos, pruebas ni compilación del producto, servicio de catálogo real, autorización de cuentas, restauración real del origen ni conformidad completa con WCAG. Siguen pendientes la selección de la dirección por parte de la persona propietaria, la finalización canónica y las tareas posteriores de implementación y revisión.

## 12. Preguntas abiertas, supuestos e impacto

**P: ¿Debe Catálogo / Catalogue aparecer como herramienta pública incluida en todos los planes?** El catálogo de muestra seleccionado actualmente para SP-2 lo incluye explícitamente entre las herramientas del plan base; R16 enumera el chat y el contador. Esta exploración conserva esa fila existente en vez de inventar otro beneficio. David/Planner debe confirmar el contenido del catálogo público antes de finalizar; quitarlo eliminaría una fila de cada banda sin cambiar esta composición.

Confirmado: cuatro planes y su orden, precios mensuales exactos en COP/USD, Enthusiast gratis, tres herramientas no disponibles con nombre en Plus/Master, límites cualitativos del chat y la entrada combinada de Taller en Master. El brief de UI prevalece explícitamente sobre el paréntesis ambiguo de Prioridades de la SPEC anterior respecto a cuáles tres adiciones no están disponibles; la calculadora de costos está disponible y el chat extendido no.

Decisiones de presentación de esta exploración: todas las bandas expandidas inicialmente; contraído independiente; un índice de planes que se ajusta en varias líneas; listas acumulativas completas; ningún nivel destacado ni insignia de plan asignado. El texto de recuperación es contenido funcional de la maqueta, no una afirmación de que se requiera una API de catálogo en línea. El catálogo de producción puede leerse de forma estática; en ese caso, las vistas previas de carga y sin conexión documentan la superficie de fallos, en lugar de prescribir una solicitud cliente innecesaria.

Clasificación del impacto: **indeterminada hasta que el propietario seleccione una dirección; no existe un contrato previo para estos planes**. Un futuro contrato canónico afecta solo a SP-14 T14.1/T14.2/T14.3/T14.5 y a las dos ubicaciones de enlaces de entrada de SP-2. SP-1 sigue siendo el único responsable del catálogo. Se conservan el contenedor compartido, la navegación, las fuentes, los tokens y las vistas no relacionadas de los subplanes hermanos; la aprobación y el trabajo de ingeniería quedan fuera de esta delegación. No se escribe un registro de cambios independiente ni un archivo de memoria compartida, porque el brief de exploración permite únicamente resultados específicos de revisión y su informe de delegación.
