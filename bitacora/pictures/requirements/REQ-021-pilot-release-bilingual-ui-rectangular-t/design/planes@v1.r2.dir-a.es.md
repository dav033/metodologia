# Pliegues de consulta · información abierta

## 1. Identidad y trazabilidad

- Artefacto: `planes@v1.r2.dir-a`, exploración de planificación independiente, **estado: borrador**, no es un contrato aprobado.
- Contrato previsto: `planes@v1`; SP-14, R17–R20. Propietario: David. Fecha de diseño: 2026-10-27.
- Autoridad de comportamiento: `planes@v1.r2.behavior.md`, SPEC “Comportamiento — planes de acceso y sección de planes” y “Comportamiento — vista adicional de SP-14 (ronda 13 respondida)”, PLAN.json SP-14.
- Composición nueva, no es un parche ni una copia de un borrador anterior de planes. Esta exploración conserva la idea de pliegues de consulta elegida por el propietario, pero elimina por completo los controles para plegar.
- El alcance reemplaza la solicitud de salida canónica: solo se escriben los dos HTML candidatos específicos de esta revisión, el TSX/HTML compilado/MD/JSON de esta dirección y el RESULT delegado. No se modifican el contrato canónico, el historial, el código de producción, el registro compartido, SPEC ni PLAN.

## 2. Propósito y usuarios

Responder «¿Qué herramientas incluye cada plan y cuál es su precio mensual?» para una persona visitante o con sesión iniciada. Una segunda vista responde «¿Qué plan estoy comparando?» sin adquirirlo, solicitarlo, registrarse ni cambiar la asignación de cuenta. La comparación completa sigue siendo legible sin seleccionar nada.

La vista previa también muestra el enlace a planes en el inicio de sesión y el enlace a planes en el menú de cuenta existentes. La autenticación y la edición de cuentas siguen siendo comportamientos de SP-2; las pantallas de entrada son instantáneas contextuales de muestra, no un diseño que reemplace el de SP-2.

## 3. Enfoque, jerarquía y miniatura elegida

**Elegida: `planes@v1.r2.dir-a.html.candidate-1.html`.** Su hoja continua con líneas divisorias conserva el orden de comparación y evita acomodar cuatro columnas largas en una tableta. La candidata 2 explora bloques de planes en una cuadrícula de dos por dos; la separación entre bloques hace menos directa la lectura acumulativa. Ambas miniaturas se dibujaron antes del TSX completo.

Conservar el encabezado de Pictures/Sempertex, la marca de anillo y punto, el control de idioma, el papel con esquinas redondeadas, la navegación horizontal neutra por secciones y el desplegable nativo de cuenta de `cuentas-admin@v1`. `proyectos@v1` y `taller-esenciales@v1`, consultados, refuerzan el mismo vocabulario de tipografías y tokens de producción; no se agregan a esta sección pública sus barras laterales específicas de la biblioteca o el editor.

Cambiar solo el contenido específico de planes: cuatro pliegues abiertos y ordenados, cada uno compuesto por nombre del plan → precio mensual → lista completa de herramientas incluidas. En escritorio, un índice breve en la página queda junto al papel único. En tableta, el índice se mueve sobre el papel. Todas las herramientas siguen el flujo normal del documento. Sin acordeón, control para ocultar/mostrar, recomendación de plan, distintivo promocional, beneficio inventado ni titular de marketing.

Orden de los planes: Entusiasta / Entusiasta, Designer, Designer Plus, Master Designer. Cada bloque repite su lista acumulativa completa para evitar referencias del tipo «todo lo anterior» que dependan de la memoria. El chat con límite más alto de Designer reemplaza la línea del chat con límite más bajo. Plus y Master muestran por separado las tres herramientas no disponibles, cada una con la etiqueta exacta de no disponibilidad.

## 4. Sistema de diseño y evidencia de ocho ejes

| Eje | Expresión actual |
|---|---|
| Concepto | Pliegues de consulta abiertos; información de trabajo densa con todas las herramientas visibles y selección limitada a la comparación. |
| Diseño | Un papel dividido, bloques horizontales de nombre/precio y herramientas, índice de 192px en escritorio, índice de dos columnas sobre el contenido en tableta y bloques apilados en teléfono. |
| Navegación | Encabezado existente de Pictures/Sempertex; regla neutral para las rutas de comparación/selección; anclas de planes; enlaces a cuenta/inicio de sesión y retorno explícito. |
| Tipografía | Geist Sans / Geist Mono existentes, integradas desde la compilación de producción t12. Título de página y precios de 24px; nombres de planes de 20px; herramientas de 14px; disponibilidad de 12px. Cifras de precio tabulares. |
| Densidad | Separación de 12px entre herramientas, separación de 24px entre filas, relleno de 28px en el papel, márgenes internos de 20px en teléfono. Sin tarjetas anidadas. |
| Componentes | Button, Input y Skeleton de shadcn/Base UI instalados; disclosure/select/radio nativos; lista de planes personalizada con líneas divisorias. Sin acordeón. |
| Color | Tokens de Pictures para modo claro/oscuro de producción; navegación neutra, encabezado/línea de selección de acento y acción principal de retorno a la comparación. Sin paleta de exploración. |
| Movimiento | Registro rápido de filas: traslación de 12px, intervalo escalonado de 45ms y escala de línea scaleX(.45→1), 300ms con cubic-bezier(.23,1,.32,1) expresiva; controles de 180ms y paridad para movimiento reducido/sin animación. |

Fuentes inspeccionadas en modo de solo lectura en t12 y asesor: `src/app/globals.css`, `src/app/layout.tsx`, componentes de inicio de sesión y estructura, archivos MD/HTML canónicos relacionados. Se inspeccionaron el estado y las diferencias del repositorio; t12 tiene cambios locales preexistentes y asesor estaba limpio. No se editó ningún repositorio. El `src/lib/planes/catalogo.ts` previsto para SP-1 no existe en ninguno de los árboles inspeccionados; la vista previa usa un único `plan-catalogue@1` estático, claramente identificado, que coincide con el brief y SPEC. En producción se debe leer el catálogo de SP-1 en lugar de copiar esta muestra.

| Token del producto | Función en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--superficie-suave` | superficie suave | #faf8fd / #1c1e26 |
| `--superficie-2` | secundario, atenuado, acento neutro | #efe9f8 / #242733 |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde de entrada, como en contratos relacionados | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | principal, primer plano principal | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento` | anillo | #6d3fe0 / #9479ff |
| `--borde`, `--borde-suave` | bordes decorativos, líneas divisorias | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| `--error`, `--error-suave` | destructivo, destructivo suave | #b23a45 / #ffeaec; #ff979f / #43252a |

El vocabulario de formas sigue al elemento relacionado seleccionado: papel de 32px, disclosure flotante de 24px, campos de 18px y acciones tipo píldora. Los archivos de tipografía están integrados como URI de datos desde archivos WOFF2 locales existentes de Geist Latin; no se descargan fuentes. El contorno de foco usa `--ring`, 2px con desplazamiento de 4px. Las líneas decorativas no funcionan como límites de controles de formulario.

Componentes reales: `shadcn:button default|outline default|hover|focus|pressed` de `@/components/ui/button`; `shadcn:input email|password default|focus` de `@/components/ui/input`; `shadcn:skeleton loading` de `@/components/ui/skeleton`. El selector de idioma, el disclosure de cuenta, el fieldset y las etiquetas de radio nativos se identifican con precisión como nativos. `.consultation`, `.plan-row`, `.tools`, `.plan-index` son personalizados y proporcionan el diseño. `mountMockup/useMockup` provienen de `@kit/mockup`, `useMotionProfile` de `@kit/motion` y la animación de filas de `motion/react`. Sin fragmentos de respaldo ni instalación de paquetes.

## 5. Navegación, interacción y detalle del movimiento

- La pantalla de inicio de sesión agrega exactamente un enlace `Planes` / `Planes` a `/planes`. Los textos y controles existentes del formulario siguen siendo la referencia de SP-2.
- El disclosure de cuenta conserva Mi cuenta / Mi cuenta y Cerrar sesión / Cerrar sesión y agrega una entrada Planes / Planes. En la sección de planes no aparecen roles de personal ni claves de permisos.
- La comparación y la selección son vistas hermanas locales de `/planes`; no se agrega otro destino de nivel superior en la aplicación. La vista previa usa opciones nativas de Vista para mostrar por separado las variantes con y sin sesión iniciada.
- El índice se desplaza hasta un encabezado de plan visible y le da el foco sin un segundo desplazamiento. Las pestañas/botones llevan el foco al encabezado de la nueva página. El retorno público va al inicio de sesión; el retorno con sesión iniciada usa la página de producto de origen. Esta vista previa aislada usa Mi cuenta como muestra de página de origen con sesión iniciada.
- En la selección, radios nativos forman un fieldset. Marcar un plan actualiza solo la selección de comparación en memoria. El acento del nombre/línea y el texto «Seleccionado para comparar» / «Seleccionado para comparar» lo identifican independientemente del color. Un estado cortés anuncia el nombre del plan seleccionado. Las cuatro listas completas de herramientas permanecen visibles.
- «Volver a la comparación» / «Volver a la comparación» funciona con una opción elegida o sin ella. Una opción elegida se conserva al volver y el foco pasa al encabezado del plan elegido. Sin elección, el foco vuelve al encabezado de la página. No presenta la opción como el plan actual de una cuenta ni afirma que se haya asignado correctamente.
- La entrada de filas se registra horizontalmente con 12px; intervalo escalonado de 45ms, sin desvanecer el texto. Una línea horizontal se dibuja desde scaleX(.45) hasta 1. Expresivo: 300ms; natural: 220ms; sutil: 140ms; la aceleración usa la curva `--ease-out` existente. Al pasar el cursor, el índice se desplaza 3px; al presionar un botón, 1px; los controles duran 180/140/100ms. Las animaciones finitas terminan pronto; no hay animación decorativa persistente. Las pestañas ocultas pausan los efectos CSS. MotionProfile y el movimiento reducido del sistema operativo, Quieto y `?still=1` muestran el contenido final de inmediato, con todas las acciones intactas.

## 6. Flujos

1. **Público:** inicio de sesión → Planes → leer los cuatro bloques completos → elegir opcionalmente para comparar → volver a la comparación completa resaltada → volver al inicio de sesión.
2. **Con sesión iniciada:** menú de cuenta → Planes → comparar o resaltar → volver a la página de producto original. La cuenta de ejemplo sigue en Entusiasta, independientemente del resaltado.
3. **Idioma:** ES/EN inicial según el idioma del navegador; un control de idioma de la vista previa muestra ambas variantes. ES muestra solo COP; EN muestra solo USD. Los cambios de idioma conservan la selección de comparación. El selector permite inspeccionar el futuro control compartido de SP-8 y no agrega una elección de moneda aparte.
4. **Falla/recuperación:** carga → listo, vacío o error. Las vistas vacía y de error ofrecen Reintentar / Reintentar y conservan la salida/navegación. Al reintentar, la muestra de planificación vuelve al estado listo. No se presenta un catálogo incompleto como una comparación completa satisfactoria.

## 7. Vistas y datos exactos

| Selector de vista | Vista del producto | Contenido y comportamiento |
|---|---|---|
| `plans` | Comparación pública | Sin menú de cuenta; ficha ordenada de cuatro planes, herramientas completas, índice y regreso al inicio de sesión. |
| `choose` | Selección pública | Mismo marco y datos; botones de opción en un grupo de campos, explicación explícita de que la comparación es solo informativa, estado de selección y regreso a la comparación. |
| `plans-in` | Comparación con sesión iniciada | Mismo catálogo; se muestra la divulgación de la cuenta identificada y se permite volver al origen. |
| `choose-in` | Selección con sesión iniciada | Mismo flujo de selección con botones de opción, solo para comparar, y divulgación de la cuenta; la asignación de la cuenta no cambia. |
| `login` | Acceso existente para iniciar sesión | Ficha de acceso centrada de SP-2 con correo electrónico y contraseña, texto que indica que solo se puede acceder por invitación y que el administrador restablece la contraseña, más un enlace a /planes. El envío del formulario solo informa que las operaciones son simuladas. |
| `account` | Contexto del menú de cuenta | Marco y divulgación existentes, además de metadatos neutrales de una cuenta de ejemplo para mostrar la entrada a /planes. La edición completa de la cuenta de SP-2 queda fuera de esta exploración. |

| Plan | Precio mensual ES | Precio mensual EN | Herramientas visibles completas |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Gratis | Chat con límites / Chat with limits; Contador de globos / Balloon counter; Catálogo / Catalogue. |
| Designer | 20.000 COP / mes | 7 USD / mes | Chat con límites más altos / Chat with higher limits; contador; catálogo. |
| Designer Plus | 45.000 COP / mes | 14 USD / mes | Chat con límites más altos; contador; catálogo; Calculadora de costos / Cost calculator; Chat extendido / Extended chat; Detección de estructuras / Structure detection; Detección avanzada de globos / Advanced balloon detection. |
| Master Designer | 70.000 COP / mes | 25 USD / mes | Todas las herramientas de Plus, más Taller 3D / 3D workshop. No hay una línea independiente del explorador de decoraciones prediseñadas. |

Cada una de las últimas tres herramientas de Plus y Master muestra “aún no disponible” / “aún no disponible”, junto con un ícono de reloj en lugar de una marca de disponibilidad. No se indican límites numéricos de chat. Los valores reales de los datos de prueba se mantienen una sola vez en el catálogo TSX; todas las vistas de vista previa los consumen. “Un administrador asigna el plan.” / “Un administrador asigna el plan.” es la única explicación sobre cómo obtenerlo.

## 8. Estados

El selector nativo Estado expone todos los estados declarados del catálogo en las cuatro vistas de planes. No rediseña las dos capturas de los puntos de entrada de SP-2.

| Estado | Comportamiento representado / recuperación |
|---|---|
| ready | Cuatro bloques de planes con todas las listas de herramientas y la moneda correspondiente; ninguna o una opción de comparación resaltada. |
| loading | “Cargando planes…” / “Cargando planes…” y cuatro grupos de elementos esqueleto con semántica de estado y carga; no se muestran precios inventados ni un resultado vacío presentado como exitoso. |
| empty | “Planes no disponibles” / “Planes no disponibles”, instrucción para volver a intentarlo y Reintentar / Reintentar. El estado vacío significa que el catálogo no está disponible, nunca que los planes de pago cuestan cero. |
| error | “No se pudieron cargar los planes” / “No se pudieron cargar los planes”, semántica de alerta y Reintentar / Reintentar. La salida sigue disponible. |
| selected / unselected | Botones de opción reales y el estado de selección en vivo adyacente, al que se llega al interactuar en el estado ready. Al restablecer el documento se borra la selección temporal; no se garantiza persistencia ni modificación de la cuenta. |
| hover / pressed / focus | Estados reales de controles; el índice y los botones ofrecen respuesta espacial rápida, y las entradas nativas muestran el foco de forma visible. |

El éxito corresponde al estado ready o al resaltado de comparación reconocido, no a una asignación exitosa. La validación, la denegación de permisos y la mutación pendiente no aplican: los datos públicos son de solo lectura y la selección local opcional no requiere permisos ni envío. Si no hay conexión y el catálogo no está confirmado, se usa error/retry. Los datos parciales u obsoletos no deben hacerse pasar por el catálogo completo de cuatro planes; la implementación puede reutilizar error hasta que haya un catálogo actual completo. No hay ningún estado que cambie los privilegios.

## 9. Comportamiento adaptable

| Ancho | Diseño concreto |
|---|---|
| 320–639px | Márgenes interiores de 20px para la aplicación y la ficha, encabezado que se ajusta en varias líneas, herramientas de idioma y cuenta en su propia línea, título y regreso apilados. Índice de cuatro planes en dos columnas compactas; bloques de planes en una sola columna, con todas las herramientas debajo del nombre y precio. Solo desplazamiento vertical. |
| 640–1023px | Márgenes de 24px para la aplicación; índice sobre la ficha en dos columnas. Cada plan abierto ocupa una columna de identidad y precio de 200px junto a una columna completa de herramientas; no se comprimen cuatro tarjetas. Relleno de la ficha de 28px. A 768 y 834px, todo el texto y las listas caben en el flujo normal. |
| 1024–1100px | Índice lateral de 192px y espacio de 28px; identidad del plan de 190px, una columna de herramientas. |
| 1101–1439px | Se conserva el índice lateral; identidad del plan de 208px y dos columnas de herramientas. |
| ≥1440px | La misma aplicación con ancho máximo de 1520px; identidad del plan de 240px. No cambian la tipografía ni la marca. |

Los nombres largos de planes y las herramientas traducidas se ajustan en varias líneas. No hay alturas fijas para los planes, carrusel ni comparación con desplazamiento horizontal. El estado de selección y el pie de acciones se ajustan sin superponerse a las herramientas. En teléfonos, la comparación es intencionalmente larga porque todas las herramientas siguen visibles. A 320 píxeles CSS, los bloques apilados conservan la legibilidad; las tabletas tienen una composición especificada propia en lugar de heredar las columnas de escritorio. Una ventana de poca altura se desplaza con normalidad; ningún pie fijo cubre las herramientas. La barra de inspección es un elemento independiente de la interfaz de la maqueta.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA; las comprobaciones automatizadas de la vista previa no certifican la conformidad. Regiones semánticas lógicas, un H1, H2 visibles para los planes, listas semánticas de herramientas, selectores etiquetados y botones de opción dentro de fieldset/legend. Las flechas del teclado y la barra espaciadora usan el comportamiento nativo de los botones de opción. Las etiquetas de selección ofrecen un área objetivo de ≥44px de alto. Botones, enlaces de salida, elemento de divulgación y enlaces del índice ofrecen áreas objetivo de ≥44px. El enlace para saltar al contenido lleva al encabezado de la página. La disponibilidad y la selección tienen texto explícito y no se indican solo con color.

Contraste del texto ≥4.5:1; el texto grande y los bordes o indicadores de foco significativos de los controles de formulario, ≥3:1. Las cifras de precios usan numerales tabulares. Las etiquetas de entrada siguen asociadas a sus campos. La nueva navegación mueve el foco al nuevo encabezado, y el regreso a la comparación enfoca el encabezado visible del plan seleccionado. La divulgación de la cuenta conserva la semántica nativa del elemento de divulgación; no afirma implementar un patrón ARIA de menú incompleto. El error es una alerta y la selección actualiza un estado informativo cortés. El modo de movimiento reducido/estático conserva todo el contenido y las acciones de teclado. No hay fuentes ni imágenes externas, interacciones exclusivas con puntero, listas de herramientas ocultas, acciones de compra ni información que solo aparezca al pasar el cursor.

## 11. Criterios de aceptación visual y evidencia de auditoría

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| A-01 | 320–1520px | ready | Los cuatro nombres de planes aparecen en el orden requerido. |
| A-02 | 320–1520px | ready, ES | Los precios de pago muestran COP / mes y no USD; Entusiasta indica Gratis. |
| A-03 | 320–1520px | ready, EN | Los precios de pago muestran USD / mes y no COP; Enthusiast indica Gratis. |
| A-04 | 320–1520px | ready | Cada plan tiene una lista completa y visible de herramientas y no hay un control para mostrar u ocultar herramientas. |
| A-05 | 320–1520px | ready | Plus y Master muestran tres etiquetas de no disponibilidad cada uno, incluida la detección avanzada de globos. |
| A-06 | 320–1520px | ready | Entusiasta usa el texto de chat con límites y Designer el de límites más altos, sin indicar un límite numérico. |
| A-07 | 768 / 834px | ready | El índice de planes está sobre la ficha, en dos columnas. |
| A-08 | 768 / 834px | ready | Las filas de planes abiertos tienen una columna de identidad de 200px junto a una columna de herramientas, sin desplazamiento horizontal en toda la página. |
| A-09 | 390px | ready | El título, el precio y todas las herramientas del plan se apilan verticalmente dentro de márgenes interiores de 20px en la ficha. |
| A-10 | 1280px | ready | El índice lateral acompaña una ficha, y las herramientas forman dos columnas dentro de cada bloque horizontal de plan. |
| A-11 | 320–1520px | ready, selection | Hay un botón de opción etiquetado por cada plan, junto con todas sus herramientas. |
| A-12 | 320–1520px | selected | El nombre del plan y el texto explícito que indica que está seleccionado para la comparación identifican la opción elegida. |
| A-13 | 320–1520px | selected → comparison | El regreso conserva el resaltado elegido y enfoca el encabezado visible del plan. |
| A-14 | 320–1520px | ready, signed in | Al seleccionar otro plan, la asignación del plan Entusiasta a la cuenta de ejemplo no cambia. |
| A-15 | 320–1520px | entry | El inicio de sesión tiene un enlace a /planes y el menú de cuenta tiene una entrada a /planes. |
| A-16 | 320–1520px | public | No aparece la divulgación de la cuenta. |
| A-17 | 320–1520px | loading | Los elementos esqueleto y el estado de carga sustituyen los precios del catálogo. |
| A-18 | 320–1520px | empty / error | Aparece un control para volver a intentar junto con un mensaje veraz de no disponibilidad o error. |
| A-19 | 320–1520px | keyboard | Al activar el índice de planes, el foco pasa al encabezado visible correspondiente. |
| A-20 | 320–1520px | reduced / still | Todo el contenido de los planes permanece visible y no hay efectos de movimiento en ejecución. |
| A-21 | 320–1520px | ready | No hay controles de compra, solicitud, registro, asignación de cuenta ni permisos. |
| A-22 | 320–1520px | both themes | Los colores de primer plano y fondo del producto, y los tokens de controles, coinciden con las asignaciones de productos hermanos o de producción. |
| A-23 | 320–1520px | all | La etiqueta de la maqueta y los selectores nativos etiquetados Vista, Estado, Tema y Movimiento permanecen visibles. No se declara ningún diálogo. |

La verificación corresponde al artefacto de planificación, no a la implementación de producción:

- Compilador real sin conexión: PASS, HTML autocontenido de 531KB y 2,031 archivos de origen incluidos. Sin instalación ni solicitudes de recursos externos.
- `contrast.py`: **contraste: se comprobaron 158 pares en los temas claro y oscuro; todos pasan**.
- Auditoría completa de la representación en el HTML final: 96/96 combinaciones en seis vistas, cuatro estados, dos temas y 1280/390px; 2,488 mediciones de texto y 404 paradas de foco.
- **RESULTADO: PASS — no se detectaron problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- Una auditoría anterior detectó una discrepancia en la alineación centrada del pie de la vista de entrada; ahora el texto del pie comparte el borde izquierdo de la columna de entrada. La auditoría final reemplaza ese resultado fallido.
- Comprobación complementaria con Playwright: 112 combinaciones de ES/EN, claro/oscuro, comparación/selección pública y con sesión iniciada, y anchos de 320/390/640/768/834/1024/1280; están presentes los cuatro bloques de planes, 21 filas de herramientas, seis etiquetas de no disponibilidad y una sola moneda correcta; sin desbordamiento horizontal, excepciones de página ni solicitudes HTTP(S). Esta matriz precedió a la mejora semántica final del encabezado; la auditoría final incluye esa mejora.
- Comprobaciones enfocadas del marcado final: PASS para el foco en encabezados visibles desde la selección y el índice, el regreso al plan resaltado y el reajuste a 390/768/834/1024/1280. Se observaron las cinco animaciones de entrada reales (una regla y cuatro filas), de 300ms cada una; cero animaciones en ejecución con movimiento reducido.
- Las comprobaciones de interacción también ejercitaron los enlaces de entrada al inicio de sesión y al menú de cuenta, y verificaron que la cuenta de vista previa sigue en Entusiasta después de seleccionar Designer Plus. No se contacta ningún sistema de cuentas real.
- Capturas de pantalla inspeccionadas en memoria: comparación a 1280px en tema claro y oscuro, selección oscura a 834px, comparación clara a 390px y selección oscura a 390px. No se guardaron archivos de captura fuera de la lista de artefactos permitidos.
- Se comprobaron todos los selectores de evidencia JSON frente a la vista renderizada predeterminada; todos coinciden. Se eliminó el selector del menú de cuenta de la evidencia de la vista predeterminada porque la vista pública no muestra correctamente ninguna divulgación de cuenta.
- Limitaciones: el cierre del menú de cuenta con teclado, más allá del comportamiento nativo de details, la edición/autenticación completa de SP-2, la actualización del catálogo de producción, los permisos reales y la restauración del origen de navegación real requieren revisión de implementación. No se ejecutaron pruebas de lint, tipos, compilación de producción ni integración con cuentas reales; esta delegación es solo de diseño.

## 12. Preguntas abiertas, supuestos e impacto

**Preguntas abiertas para la persona responsable: ninguna.** La pregunta q1 de la ronda 13 ya tiene una decisión sobre la semántica de selección. La aprobación sigue pendiente; no se da por aprobada ninguna decisión sobre el contrato o el plan. Las notas de dirección están listas para compararse y finalizarse, pero no autorizan la implementación.

Confirmado: público e informativo, cuatro planes, todas las herramientas visibles, precios y monedas exactos según el idioma, sin límites numéricos de chat, herramientas no disponibles marcadas, el Taller de Master incluye el editor 3D completo y solo un administrador asigna un plan a una cuenta. El idioma del navegador es la fuente inicial antes de SP-8. La selección temporal en la página es independiente de la identidad de la sesión.

Supuestos de presentación: la selección para comparar solo se conserva en memoria; el origen con sesión iniciada es Mi cuenta en esta vista previa aislada; la recuperación de errores restablece los datos de prueba; las etiquetas de la interfaz en inglés traducen los términos existentes en los requisitos. Las capturas de inicio de sesión y cuenta establecen los enlaces añadidos, mientras que SP-2 es responsable de su comportamiento completo y esta vista previa no puede reemplazarlo.

El impacto se limita a SP-14: T14.1 copia del contrato finalmente aprobado; T14.2 planes, selección y comportamiento adaptable; T14.3 enlaces de entrada y T14.5 revisión de la interfaz renderizada; T14.4 es la tarea de verificación de integración del Planner, fuera de la ejecución de diseño. La reestructuración adaptable y la vista de selección añadida requieren adaptación de la implementación y **cambian las expectativas visuales** respecto de una comparación anterior que permitía ocultar herramientas. Esta exploración no cambia el contrato de asignación de cuentas. El catálogo y los permisos de SP-1 no cambian. El contrato canónico, el diseño y los destinos existentes de SP-2 no cambian; esta dirección muestra únicamente sus enlaces a planes ya requeridos. No se añade ninguna entrada de navegación adicional a SP-2. Los archivos canónicos y sus historiales permanecen intactos.
