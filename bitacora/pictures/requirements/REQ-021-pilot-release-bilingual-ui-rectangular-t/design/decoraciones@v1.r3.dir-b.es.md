---
name: Espacio de composición
status: draft
artifact: exploration
subplan: SP-5
requirement: R8
contract_candidate: decoraciones@v1
direction: b
source_revision: r3
plan_revision: 15
date: 2026-10-29
owner: David
---

# Espacio de composición — direction b

## 1. Identidad y trazabilidad

Exploración de planificación, **borrador sin aprobar**. Esta dirección es una candidata para `decoraciones@v1`, no el contrato canónico. El propietario elige una dirección en la comparación; posteriormente, un finalizador redacta el contrato canónico. Nada de lo aquí presentado aprueba el plan ni autoriza la implementación.

Alcance: SP-5, R8, `decoraciones@v1.r3.behavior.md` compartido, SPEC § “Behavior — SP-5 (round 11 answered)” y revisión 15 de PLAN.json. Consumidores después de la aprobación independiente: T5.1 copia el contrato, T5.3 implementa la biblioteca personal y T5.5 revisa el resultado renderizado. Esta exploración crea únicamente sus dos HTML candidatos, TSX, HTML compilado, esta nota y el JSON de ejes, además del resultado de la delegación solicitada explícitamente. No se modifica ningún repositorio, artefacto canónico, SPEC, PLAN, registro de cambios ni vista previa.

Evidencia de solo lectura: `src/app/globals.css`, `src/app/layout.tsx`, `src/components/tres-d/Biblioteca.tsx` y `Taller3D.tsx` de ambos repositorios. `Biblioteca.tsx` es idéntico en t12 y asesor. Sus bloques de tokens del tema coinciden; las diferencias de globals.css corresponden a la extracción de un botón con icono y al estilo de la barra de prompts, no a la paleta utilizada aquí. Superficie existente: Taller `/3d`, controles para guardar la pieza seleccionada o la escena actual, formulario de nombre/ocasión, biblioteca de miniaturas, filtros por ocasión/color/globos, vista previa del elemento, “Añadir a mi escena” y eliminación de elementos locales del navegador. El almacenamiento existente es `taller3d:biblioteca-propia:v1`. La separación por servidor/cuenta es el cambio requerido.

Se leyeron las entradas de subplanes relacionados: `cuentas-admin@v1.md/.html`, `planes@v1.md/.html` y `proyectos@v1.md/.html`. Se conserva el vocabulario de su shell compartido finalizado: cabecera de Pictures/Sempertex con anillo y punto, selector de idioma, menú desplegable de cuenta, H1 de 24px, regla horizontal neutra entre rutas, Geist integrado y controles redondeados. El origen r12 elegido de Proyectos aporta el shell y la correspondencia de tokens de producción; la nueva disposición de la biblioteca se compone desde cero.

Clasificación del impacto: **candidata a cambio incompatible de UI** para T5.3, sujeta a la elección del propietario; la disposición espacial de la biblioteca/ficha, la navegación por foco y el comportamiento adaptable requieren implementación y revisión de T5.5. No se modifica ningún predecesor aprobado. La compatibilidad en producción no está verificada; esto no implementa almacenamiento ni autorización.

## 2. Propósito y usuarios

La pregunta de trabajo es “¿Qué decoración guardada quiero añadir a mi proyecto actual?”. Una cuenta autenticada con acceso a Taller, incluida Master Designer y el personal, guarda la escena completa o su pieza seleccionada con nombre y ocasión. Para considerar que la operación fue exitosa, el almacenamiento de la cuenta debe confirmarse en el servidor, debe ser posible recuperar los elementos desde otro navegador y colocarlos en un proyecto propio.

El personal puede inspeccionar en modo de solo lectura la biblioteca de otra cuenta. La etiqueta de propietario y solo lectura permanece visible, y al colocar el elemento se crea una copia en un proyecto propio del miembro del personal. No hay controles para renombrar, editar ni eliminar el original de otra cuenta. Las cuentas sin Taller no acceden a esta biblioteca; el acceso se concede desde la superficie establecida de cuentas/roles.

## 3. Enfoque, composición y elección de miniatura

**Miniatura elegida:** `decoraciones@v1.r3.dir-b.html.candidate-1.html` — biblioteca lateral, vista previa central e inspector a la derecha. La lista, la búsqueda y el filtro por ocasión permanecen visibles mientras la decoración seleccionada tiene una vista previa amplia y sus acciones ocupan un borde fijo. Se ajusta al modelo de trabajo existente de Taller, con lienzo e inspector, y cambia solo el área de la biblioteca personal.

La candidata 2, `decoraciones@v1.r3.dir-b.html.candidate-2.html`, coloca la biblioteca en una bandeja inferior, debajo de la vista previa y la ficha. Su miniatura amplía la vista previa, pero comprime la navegación de la colección y omite del área de la bandeja la búsqueda y los filtros. La candidata 1 satisface mejor los controles de biblioteca requeridos en este encargo sin crear otra página. Ambas composiciones visuales pequeñas se escribieron y renderizaron antes de crear el TSX completo.

| Eje | Dirección observable |
|---|---|
| concepto | Espacio de composición: conservar el shell existente de Taller y organizar la biblioteca personal, la vista previa aislada y el inspector del elemento en tres áreas de trabajo conectadas. |
| layout | A partir de 1100px, una biblioteca de 280px, una vista previa central flexible y un inspector de 264px comparten un panel continuo de taller; entre 640–1099px, el inspector queda debajo de la vista previa; entre 320–639px, las tres áreas se apilan. |
| navegación | Conservar la cabecera de Pictures/Sempertex y la regla neutra entre las rutas Taller 3D/Proyectos. Dentro del taller, Biblioteca/Vista previa/Ficha mueve el foco a cada área; los botones de origen de cuenta/navegador cambian la lista sin cambiar de ruta. |
| tipografía | Usar Geist Sans y Geist Mono integrados, que ya existen. H1 permanece en 24px; encabezado del inspector en 20px, encabezado de biblioteca en 18px, nombre del elemento en 14px, etiquetas en 12–14px y metadatos de apoyo en 12–13px. |
| densidad | Una lista compacta de miniaturas y un elemento expandido ocupan la pantalla; los filtros distintos de ocasión usan un desplegable nativo. Los márgenes internos en escritorio son de 20–24px dentro del shell heredado, con márgenes laterales de 20px en teléfonos y controles de 44px. |
| componentes | Recomponer los componentes reales instalados de shadcn Button, Input y Skeleton con Animate UI/Base UI Dialog y AlertDialog; usar botones de origen semánticos nativos, selectores y details, una escena de ejemplo SVG en línea y un indicador de área compartida de Motion. |
| color | Usar solo los tokens de Pictures globals.css y los alias finalizados de subplanes relacionados: fondo/superficie/texto/acento, más los roles de vista previa de Taller; texto-tenue proporciona bordes accesibles para controles, y exito/error/aviso identifican comentarios reales. Ambos temas conservan la misma paleta y tipografías. |
| movimiento | Coreografía espacial: la biblioteca entra desde la izquierda desplazándose 20px, el inspector desde la derecha con 24px, los registros aparecen en secuencia con intervalos de 65ms, la vista previa se posiciona horizontalmente y su objeto entra desplazándose 25px/girando −12deg en Y. Desplazamiento expresivo de 640ms, natural de 360ms, sutil de 160ms, con curva cubic-bezier(.23,1,.32,1); el indicador de área compartida usa el perfil de resorte del kit. El movimiento reducido y el modo estático eliminan todo desplazamiento. |

La barra de herramientas del taller conserva la identidad del proyecto actual y el vocabulario existente de Deshacer/Rehacer, Foto realista y Lista de compra. La vista previa indica explícitamente que no modifica el proyecto abierto. “Añadir a mi escena” cambia la escena de ejemplo solo al activarse y confirma que se creó una copia propia. El catálogo global de decoraciones permanece separado.

## 4. Sistema de diseño fijo y componentes reales

No se incorpora ninguna paleta, tipografía ni identidad nueva. Los recursos locales WOFF2 de Next integran Geist Sans y Geist Mono; no se descargan fuentes. Los roles de bordes redondeados del shell/controles siguen los de los borradores relacionados (panel 32px, margen interno 24px, campo 18px, píldora 999px); el marco existente de Taller usa el radio de 24px del subplan relacionado.

| Token del producto | Rol/uso del kit |
|---|---|
| `--fondo`, `--texto` | fondo, primer plano |
| `--superficie`, `--superficie-2` | superficies de tarjeta/desplegable y secundaria/atenuada |
| `--texto-suave`, `--texto-tenue` | texto de apoyo; alias para bordes accesibles de controles |
| `--acento`, `--sobre-acento`, `--acento-hover` | principal, primer plano del color principal, hover |
| `--borde`, `--borde-suave` | límites decorativos y divisores |
| `--exito`, `--exito-suave` | confirmación de guardado y comentario de copia colocada |
| `--error`, `--error-suave`, `--aviso`, `--aviso-suave` | error y comentario de pieza no compatible |
| `--taller-visor`, `--taller-panel`, `--taller-barra` | vista previa, su contexto y la interfaz del taller |

La página incluye valores explícitos para los temas claro/oscuro, copiados de fuentes de producción/subplanes relacionados, una vez por tema. Ejemplos: fondo `#faf9fc/#0b0c10`, texto `#1c1425/#f4f5f7`, acento `#6d3fe0/#9479ff`, sobre-acento `#ffffff/#120b24`. La navegación global activa usa texto y su regla; el color de acción principal identifica la acción de guardar/colocar. La ilustración SVG usa los mismos tokens y se identifica claramente como dato de ejemplo, no como formato propuesto para las miniaturas almacenadas.

| Fuente real:id / variante / estados | Importación o implementación |
|---|---|
| shadcn:button / default, outline, destructive / normal, hover, foco, deshabilitado, en curso | `@/components/ui/button` |
| shadcn:input / text / con contenido, vacío, no válido, deshabilitado, foco | `@/components/ui/input` |
| shadcn:skeleton / miniatura y líneas del elemento / carga | `@/components/ui/skeleton` |
| shadcn:dialog / edición del nombre y metadatos / abierto, validación, pendiente, cerrado | `@/components/ui/dialog` con Animate UI/Base UI instalado |
| shadcn:alert-dialog / eliminación / confirmación, pendiente, cancelar | `@/components/ui/alert-dialog` con Animate UI/Base UI instalado |
| kit:mockup / inspección nativa / vista, estado, escena, tema, movimiento | `mountMockup/useMockup` de `@kit/mockup` |
| kit:motion / perfil / expresivo, natural, sutil, reducido | `useMotionProfile` de `@kit/motion`, `motion.i` de `motion/react` |
| custom:source-nav, zone-nav, library-record, preview, inspector | HTML semántico y CSS con tokens del proyecto; no se presenta como componente de una biblioteca instalada |
| custom:account-disclosure | details/summary nativos conservados del shell relacionado |

El espacio de trabajo de componentes instalado indica que está instalado/compilado y que hay 96/96 entradas disponibles. No se usaron alternativas, instalaciones de paquetes, descargas de recursos ni solicitudes de red en tiempo de ejecución.

## 5. Modelo de navegación e interacción

La cabecera del producto y las rutas Taller 3D/Proyectos siguen siendo reconocibles y neutras. Los destinos Proyectos/cuenta/planes pertenecen a los subplanes relacionados; los controles contextuales muestran un aviso de alcance de maqueta claramente identificado en lugar de inventar nuevas pantallas del producto. Cerrar sesión en la maqueta borra inmediatamente los datos de ejemplo de la cuenta y muestra el estado vacío de aislamiento; esto no demuestra que haya autenticación.

En el área modificada, Biblioteca/Vista previa/Ficha mueven el foco a áreas etiquetadas. Solo desplazan la página cuando es necesario, con un indicador de selección compartido que se mueve. En las vistas de guardado, la última área se etiqueta como Guardar y el campo de nombre recibe el foco; en teléfonos, el desplazamiento muestra el formulario. Seleccionar un elemento de la biblioteca cambia su vista previa y ficha sin reemplazar el proyecto abierto.

Los controles de origen distinguen entre “En mi cuenta” y “En este navegador”. El personal que inspecciona otra cuenta ve “En esta cuenta” y un selector explícito de propietario. Ese selector es una demostración provisional del alcance autorizado, no una regla de autorización del cliente. Cambiar el origen borra la selección de búsqueda/filtros. La búsqueda y los filtros de ocasión/tipo/color/globos funcionan sobre un pequeño subconjunto de ejemplo etiquetado, con una opción de recuperación cuando no hay resultados. Todos los registros de este subconjunto contienen látex; solo las escenas contienen globos blancos. Las demás opciones del catálogo se omiten deliberadamente de estos pocos datos de ejemplo.

Los botones y enlaces que reemplazarían el destino de guardado quedan bloqueados mientras hay un guardado pendiente. Los diálogos mantienen el foco; Escape/cancelar y la finalización correcta devuelven el foco al activador que siga disponible, con el inspector como alternativa tras una eliminación. Los diálogos de planificación activados para otra cuenta muestran una explicación de solo lectura sin formulario ni acción de modificación. La carga y el cambio de cuenta ocultan los diálogos de elementos, además de los datos de lista/detalle/vista previa.

## 6. Flujos

1. **Guardar la escena:** elegir “Guardar toda la escena en mi biblioteca” → inspeccionar la vista previa de la escena completa → ingresar nombre y ocasión → Guardar → mostrar estado pendiente y deshabilitar envíos duplicados → confirmar el guardado solo después de una confirmación simulada → “Ver en mi biblioteca”. La implementación debe usar una confirmación real del servidor y admitir recarga/recuperación desde otro navegador.
2. **Guardar una pieza seleccionada:** elegir “Guardar en mi biblioteca” existente en el contexto de una pieza seleccionada → vista previa solo de la pieza y el mismo formulario → confirmar el guardado en la cuenta. Las piezas no compatibles muestran el mensaje existente “Esta pieza no se puede guardar sola.” y el guardado deshabilitado. La acción de ejemplo al pie ilustra la entrada existente para piezas seleccionadas.
3. **Recuperarse de un error al guardar:** el error permanece visible con el nombre y la ocasión → “Reintentar guardar” → mismo destino/entrada mientras está pendiente → confirmación. Los guardados fallidos no se agregan a la lista de la cuenta ni reciben una etiqueta de guardado.
4. **Buscar/colocar:** seleccionar el origen → buscar/filtrar → elegir una fila de miniatura → inspeccionar nombre/tipo/ocasión/propietario → “Añadir a mi escena” → comentario de copia propia. La decoración original permanece en su biblioteca. La colocación estática es ilustrativa; no corresponde al motor 3D.
5. **Inspeccionar/colocar como personal:** ámbito autorizado del personal → Cuenta de ejemplo → tratamiento de propietario/solo lectura → opciones para renombrar/editar/eliminar ausentes → añadir una copia al proyecto propio. No se ofrece modificar el original ni cambiar su propietario.
6. **Editar metadatos/eliminar como propietario:** Renombrar o Editar → campos con nombre → esperar la confirmación → actualizar la lista/ficha; Q2 sigue rigiendo el alcance de edición del contenido. Para eliminar, se usa AlertDialog; cancelar conserva el elemento y confirmar su eliminación en el servidor actualiza la lista de la cuenta. La eliminación existente de elementos locales del navegador actualiza solo su grupo de inmediato y nunca los importa.
7. **Aislamiento de cuentas:** cambiar de cuenta/cerrar sesión → borrar la lista del servidor, el detalle, la miniatura y la vista previa anteriores antes de cargar la siguiente cuenta → mostrar un esqueleto neutro → mostrar la lista vacía de la siguiente cuenta. El botón de continuación de ejemplo es una ayuda de inspección de la maqueta, no un flujo de cambio de cuenta en producción. Esta transición no migra ni modifica el almacenamiento heredado del navegador.

## 7. Vistas y límites del contenido

| Vista nativa | Área modificada y acción principal |
|---|---|
| `library` | Colección de la cuenta/navegador propio, búsqueda/filtro, vista previa central del elemento seleccionado y ficha a la derecha. Acción principal: Añadir a mi escena. Metadatos del servidor y acciones para quitar elementos solo para el propietario. |
| `save-scene` | La misma disposición de estructura/biblioteca/vista previa; el inspector derecho pasa a ser el formulario de nombre/ocasión de toda la escena. Acción principal: Guardar. |
| `save-piece` | La misma disposición, con vista previa de la pieza seleccionada y formulario, incluida la recuperación ante piezas no compatibles. |
| `staff` | La misma disposición, con alcance del propietario y tratamiento de solo lectura visible. La acción principal añade una copia propia; no aparecen controles para modificar el original ajeno. Al seleccionar Mi cuenta se muestra la biblioteca propia del miembro del personal. |

Inspector nativo de escena: ninguno, renombrar, editar, quitar. La última acción usa un AlertDialog real. Las etiquetas del inspector de planificación siguen siendo Vista/Estado/Diálogo/Tema/Movimiento y conservan “Mockup”. Todos los nombres son “de ejemplo”, las ocasiones provienen de la interfaz existente y no se inventan identidades de clientes, fechas, afirmaciones ni encabezados de marketing. El texto del producto ES/EN cambia mediante el control de idioma heredado.

La protección contra la eliminación de la cuenta es una consecuencia existente de la gestión de cuentas (“las decoraciones guardadas impiden eliminarla; desactívala en su lugar”), no una pantalla nueva de administración en esta exploración del Taller. La aceptación de su servicio e interfaz de cuenta corresponde a los responsables del plan; aquí no se añade ningún control para eliminar la cuenta.

## 8. Catálogo de estados

| Estado nativo | Vista aplicable / comportamiento observable |
|---|---|
| `normal` | Todas las vistas: registros de ejemplo confirmados o formulario listo de nombre/ocasión. |
| `loading` | Esqueletos de la lista de la cuenta, vista previa neutra e inspector; ningún registro ni acción de elemento obsoletos de la cuenta. |
| `empty` | Colección vacía del servidor con acceso para guardar una escena para el propietario; la fuente local conserva su fixture independiente. |
| `list-error` | Error al cargar la cuenta y opción Reintentar; mientras falle la lectura no se muestra ningún registro/vista previa autoritativos. El grupo del navegador sigue siendo independiente. |
| `saving` | Vistas de guardado: nombre/ocasión conservados, envío deshabilitado, “Guardando en mi cuenta…”, sin un nuevo resultado guardado. |
| `saved` | Vistas de guardado: “Guardado en mi cuenta” y Ver en mi biblioteca. Solo los registros confirmados aparecen como guardados en las vistas de lista. |
| `save-failed` | Vistas de guardado: valores editables conservados, error, Reintentar guardar. |
| `account-switch` | Todas las vistas: se quitan los datos previos del servidor, la lista, los detalles, las imágenes y el propietario antes de mostrar el esqueleto de la siguiente cuenta; no se muestran diálogos de elementos. |
| `placed` | Biblioteca/personal: confirmación de copia propia y vista previa ilustrativa del proyecto actual. El elemento original de la biblioteca permanece. |
| `validation` | Vistas de guardado: campo de nombre vacío, error asociado y recuperación visible. La regla provisional es un nombre no vacío después de quitar espacios al inicio y al final. |
| `action-error` | Ficha: acción no completada, elemento conservado y opción para reintentar. Si falla, no se confirma el éxito ni la eliminación. |
| `unsupported` | Guardado de pieza seleccionada: explicación existente de pieza no compatible; guardado deshabilitado. No se aplica al guardado de toda la escena. |

Los ejes de estado son controles de inspección: los estados exclusivos de guardado no inventan fallos de formulario artificiales en una vista que solo muestra una lista. Las mutaciones simuladas usan demoras finitas. Cambiar la inspección o volver a montar puede restablecer los datos de ejemplo; actualizar la página restablece los fixtures del artefacto. No se afirma que haya una API real, persistencia entre navegadores, aplicación de autenticación ni almacenamiento de sesión. La aplicación de permisos sigue siendo responsabilidad del servidor. Las lecturas sin conexión u obsoletas usan los tratamientos recuperables de error de lista/guardado; no se introduce una nueva ruta sin conexión ni de importación. No hay estado de importación, progreso de importación ni error de importación.

## 9. Comportamiento adaptable

| Ancho | Composición |
|---|---|
| 1100px+ | Tres columnas: lista de 280px, vista previa flexible e inspector de 264px. Ancho máximo compartido de la estructura de 1520px y márgenes exteriores de 40px. Un solo taller con bordes continuos; sin cuadrícula de tarjetas anidadas. |
| 640–1099px | Márgenes exteriores de 24px. La lista permanece a la izquierda con 260px, la vista previa queda a la derecha y el inspector debajo de esta; los controles de metadatos/formulario pueden usar dos columnas. Las herramientas del encabezado pasan a otra línea si hace falta. |
| 320–639px | Márgenes exteriores de 20px. El encabezado se adapta como en las vistas hermanas; lista → vista previa → inspector en orden de lectura. La navegación de áreas cabe en una sola fila; los controles de fuente siguen visibles. El acceso para guardar desplaza la vista y enfoca el formulario. Los controles y el texto se ajustan sin desplazamiento horizontal de la página. |

La vista previa cambia de tamaño como ilustración en vez de reducir el texto. Ningún panel de texto de altura fija recorta contenido. La búsqueda y los selectores caben en su columna; los diálogos limitan su ancho/alto al área visible y permiten desplazarse internamente. Ambos temas e idiomas comparten los mismos puntos de quiebre.

## 10. Accesibilidad y detalles de interacción/movimiento

Objetivos: WCAG 2.2 AA, contraste de texto de 4.5:1, bordes de controles/enfoque significativos de 3:1, controles de mínimo 44px, etiquetas/errores asociados, navegación semántica y botones para seleccionar elementos de la lista. La selección usa aria-pressed/current además del color. La carga usa busy/status; los errores usan alert; las confirmaciones usan status. Dialog/AlertDialog usan las primitivas de contención del enfoque realmente instaladas. El SVG pequeño de la escena es ilustrativo y está oculto a tecnologías de asistencia; el texto visible cercano identifica la vista previa. Las pruebas de tareas con lectores de pantalla en producción, el zoom del 200–400% y la validación entre navegadores siguen siendo objetivos de aceptación, no afirmaciones respaldadas por este artefacto estático.

El detalle distintivo de esta dirección es el acoplamiento espacial: la colección entra desde su propio lado, el inspector desde el lado opuesto y solo el objeto de la escena gira brevemente en perspectiva. El texto permanece visible en todo momento. Las entradas de elementos se escalonan y el marcador del área local se desliza con el resorte del perfil de la biblioteca. Al presionar o pasar el puntero por los botones se usan los controles táctiles heredados. Este movimiento permanece dentro del Taller existente; no es una nueva animación de marca.

Los tiempos/curvas de CSS y los selectores de evidencia están en el JSON complementario. Desplazamiento expresivo: 640ms/escalonamiento de 65ms; natural: 360/35ms; sutil: 160/15ms; controles repetidos: 180/150/100ms. `useMotionProfile` proporciona el estado real del resorte/reducción. El trabajo en pestañas ocultas o fuera de pantalla se pausa. La preferencia de movimiento reducido, Quieto y `?still=1` eliminan las transformaciones/transiciones y muestran inmediatamente el mismo contenido final. No hay bucles decorativos infinitos; los indicadores giratorios pendientes también se detienen con la reducción activada.

## 11. Aceptación observable y verificación

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| B-AC-01 | 1100px+ | normal | La biblioteca, la vista previa central y la ficha derecha ocupan tres columnas distintas dentro de la estructura heredada del Taller. |
| B-AC-02 | 320–639px | normal | Las tres áreas se apilan en el orden del DOM, sin desplazamiento horizontal de la página y con el navegador de áreas en una sola fila. |
| B-AC-03 | 320px+ | save-scene/save-piece | El nombre y la ocasión están etiquetados; el destino del guardado actual se identifica explícitamente como escena o pieza. |
| B-AC-04 | 320px+ | saving | El texto de espera está visible; el nuevo registro no recibe un resultado de guardado antes de la confirmación. |
| B-AC-05 | 320px+ | saved | Aparecen el texto que confirma el guardado en la cuenta y la acción para volver a la biblioteca. |
| B-AC-06 | 320px+ | save-failed | El error, el nombre/ocasión conservados y la acción para reintentar aparecen juntos. |
| B-AC-07 | 320px+ | empty | La lista vacía de la cuenta tiene un acceso para que el propietario guarde; los registros locales del navegador permanecen en una fuente separada. |
| B-AC-08 | 320px+ | loading | Los esqueletos reemplazan los nombres/miniaturas de la cuenta; la vista previa y el inspector no exponen acciones de registros obsoletos. |
| B-AC-09 | 320px+ | staff | El propietario ajeno y la etiqueta de solo lectura están visibles; no aparecen botones para renombrar/editar/quitar. |
| B-AC-10 | 320px+ | placed | La colocación informa que se creó una copia en el proyecto propio del usuario actual; el original sigue en la lista. |
| B-AC-11 | 320px+ | account-switch | Los nombres, miniaturas, detalles y la vista previa anteriores del servidor no aparecen antes de los resultados de la siguiente cuenta. |
| B-AC-12 | 320px+ | browser group | “En este navegador” identifica los datos locales y no tiene acción/estado de importación. |
| B-AC-13 | 320px+ | removal | La cancelación de AlertDialog conserva el elemento seleccionado y devuelve el enfoque al cerrarse. |
| B-AC-14 | 320px+ | validation | El campo de nombre vacío muestra un error visible asociado y puede recibir el enfoque del teclado. |
| B-AC-15 | 320px+ | light/dark, ES/EN | Los tokens del proyecto y Geist permanecen sin cambios; los controles/textos siguen dentro de sus columnas. |
| B-AC-16 | 320px+ | reduced/still | El contenido y los resultados no cambian y no hay animaciones de entrada en curso. |

Generador sin conexión: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/decoraciones@v1.r3.dir-b.tsx --out <design>/decoraciones@v1.r3.dir-b.html` → 651 KB, 2135 archivos fuente, código de salida 0, sin conexión. El generador real está disponible; no hay una alternativa en HTML.

Contraste: `python3 <kit>/kit/contrast.py <design>/decoraciones@v1.r3.dir-b.html` → **158 pares comprobados en tema claro y oscuro, todos aprobados**, código de salida 0.

Auditoría final renderizada: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/decoraciones@v1.r3.dir-b.html` → **240 renderizados (240 combinaciones planificadas), 9,804 mediciones de texto, 1,564 paradas de enfoque**, código de salida 0. Todas las combinaciones declaradas de vista/estado/tema y cada escena de diálogo en el estado base de cada vista se renderizaron a 1280/390px, sin muestreo. También se ejecutaron pruebas de movimiento/movimiento reducido.

**RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, enfoque, alineación, relleno ni desbordamiento**

Evidencia de interacción con Playwright: guardado confirmado de escena/pieza, ausencia de etiqueta de guardado prematura, campos de reintento conservados, ausencia de controles de mutación para personal y copia propia, grupo local sin importación, borrado de datos al cambiar de cuenta, renombrado confirmado/restauración del enfoque, cancelación de eliminación/eliminación solo local, redistribución en inglés/tema oscuro a 320/390/760/1280px, enfoque del formulario en teléfono, coreografía en ejecución real y cero animaciones en curso con `?still=1`. No se observaron errores del navegador ni solicitudes HTTP. Una comprobación final también confirmó que todos los selectores de evidencia de ejes existen en el DOM renderizado y que la navegación al destino del guardado/selección de elementos permanece deshabilitada hasta la confirmación. Una aserción de enfoque se hizo inicialmente antes de que terminara la operación asíncrona de cierre/restauración del enfoque; al esperar el estado de enfoque realmente completado, pasó sin cambios en el código fuente para corregir esa temporización.

Se inspeccionaron en memoria ambas miniaturas candidatas y las capturas completas del mockup. La biblioteca de escritorio en tema claro, la vista de personal de escritorio en tema oscuro, la biblioteca de teléfono en tema oscuro y el guardado de pieza de teléfono en tema claro conservan la estructura del producto, las tres áreas y los controles legibles. El navegador del teléfono se ajustó para permanecer en una fila y el acceso para guardar ahora enfoca el formulario en vez de dejarlo debajo de la lista. No se escribió ningún archivo de captura ni vista previa separada.

Las mediciones automatizadas complementan la revisión de diseño: no demuestran persistencia del servicio, autorización, geometría real de la escena, generación de miniaturas ni aplicación de la eliminación de cuentas. La comparación por pares con las otras dos direcciones de exploración queda pendiente en el flujo de comparación del propietario/Planificador.

## 12. Preguntas abiertas y supuestos

P: Propietario/Planificador — ¿Desde qué acceso existente deben Empleado interno y Administrador abrir la biblioteca de decoraciones de otra cuenta, y debe permanecer el selector provisional de propietario dentro de la biblioteca del Taller?
P: Propietario/Planificador — ¿“Editar” actualiza solo el nombre/ocasión de la decoración o también debe permitir reemplazar su composición guardada? Esta propuesta muestra solo metadatos; el comportamiento de edición de contenido debe definirse antes de la finalización.

Confirmado: no hay importación de datos locales del navegador; la fuente local sigue siendo independiente; los nuevos guardados pertenecen a la cuenta con sesión iniciada; el estado de guardado depende de la confirmación del servidor; el acceso de personal a contenido ajeno es de solo lectura; la colocación crea una copia propia; solo el propietario puede modificar/eliminar; se requiere acceso al Taller. Supuestos pendientes de finalizar: mantener la eliminación existente para el propietario/datos locales, usar un nombre de guardado no vacío tras quitar los espacios iniciales y finales, conservar la taxonomía de ocasiones existente y mostrar únicamente datos de ejemplo neutros en el mockup.

INQUIETUDES: la selección del propietario y la aprobación del plan/contrato siguen pendientes. Las dos preguntas anteriores se registran intencionalmente y no bloquean la exploración. Los fixtures estáticos no demuestran persistencia/autenticación. La edición de metadatos, el acceso de personal y el aislamiento de cuentas en producción requieren su contrato definitivo y la implementación del servicio. Aquí no se diseña ninguna tarea exclusivamente de ingeniería ni una ruta adicional de producción.
