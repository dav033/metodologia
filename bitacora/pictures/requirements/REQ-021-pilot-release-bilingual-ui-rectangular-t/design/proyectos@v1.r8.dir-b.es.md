---
name: Bastidor
status: draft
kind: independent-direction-exploration
contract: proyectos@v1
revision: r8.dir-b
subplan: SP-4
requirements: [R6, R7]
source_plan_revision: 1
approval: pending-owner-direction-choice
---

# Bastidor

Un marco de elevación frontal para las instalaciones que un decorador quiere retomar. La escena ocupa la superficie amplia; su nombre, propietario, último guardado y dimensiones de la sala responden a qué proyecto es. Una cinta de miniaturas elige la siguiente instalación. Esta es una exploración de borrador independiente, no el contrato aprobado ni el Taller de producción.

## Dos candidatas de miniaturas, compuestas primero

1. **Elegida: candidata 1** — `proyectos@v1.r8.dir-b.html.candidate-1.html`. Elevación amplia, leyenda del proyecto al lado y una cinta de miniaturas dentro del flujo. El proyecto principal es reconocible mientras su acción nombrada sigue siendo explícita. En teléfono estos elementos se apilan sin requerir un gesto.
2. **Candidata 2** — `proyectos@v1.r8.dir-b.html.candidate-2.html`. Índice lateral con un escenario independiente inclinado. Se descartó porque su navegación vertical persistente repite la columna de herramientas de Taller y dedica más espacio del teléfono a la navegación antes de mostrar la instalación.

Ambas son pequeñas composiciones HTML originales. Ninguna copia un borrador previo de proyectos. La entrada final se construyó después de estas miniaturas.

## Movimiento memorable y por qué esto no es una galería por defecto

La instalación elegida entra en el marco con un resorte mientras el Backing, el grupo de globos y la mesa se asientan de forma independiente. Al seleccionar otra miniatura se vuelve a montar el escenario de ese proyecto; las flechas etiquetadas ofrecen la misma selección sin arrastrar. Los materiales físicos toman color mientras el resto de la interfaz permanece neutro. A diferencia de una cuadrícula genérica de tarjetas de proyecto, una instalación tiene una amplia elevación física y una leyenda de trabajo discreta; la cinta es un selector, no una cuadrícula de paneles iguales.

La identidad compartida son los tokens existentes de Pictures y su vocabulario de producto. El registro de estilo se leyó a través de las direcciones a/b/c de Cuentas r7 y a/b/c de Taller esenciales r6. Esta dirección conserva sus materiales físicos pero evita su pase de acceso, perforación, registro editorial, dock inferior, columna vertical de herramientas y banco horizontal del inspector. Un encabezado superior es una orientación compartida deliberada, mientras que la selección de proyectos es específica de este subplan.

## Ocho ejes

| Eje | Presente en el mockup |
|---|---|
| concepto | Bastidor: una instalación guardada vuelve a su marco físico, con grupos de globos, Backing y una mesa rectangular. Los proyectos son escenas por retomar, no estadísticas de un panel. |
| disposición | Un escenario amplio de elevación frontal y una leyenda de proyecto más angosta forman una composición 1.6:1; debajo se ubica una cinta de cuatro miniaturas. Por debajo de 768px el escenario, la leyenda y la cinta de dos columnas se apilan. El editor tiene un resumen de 280px; la importación usa un despliegue de consentimiento 1.3:1. |
| navegación | Elige proyectos directamente en la cinta de miniaturas o con botones etiquetados de anterior/siguiente; el título seleccionado y la acción Continuar permanecen junto al escenario. El encabezado regresa a Proyectos. No hay barra lateral, dock flotante, dependencia de arrastre ni riel de estaciones de herramientas. Los selectores nativos de vista previa e idioma permanecen visibles. |
| tipografía | Sans de sistema compartida: título de colección de 30px, título de proyecto seleccionado de 34px en peso ligero, título del editor de 24px, título de diálogo de 22px y texto de trabajo de 14–15px. Los metadatos son de 12–13px. Los títulos de proyecto se ajustan libremente en teléfono; sin tipografía de exhibición ni numerales KPI decorativos. |
| densidad | Un proyecto seleccionado recibe un escenario de 325px y 40px de separación respecto a su leyenda. La estructura de escritorio usa 24px de relleno exterior, el teléfono 20px. Los diálogos tienen relleno de 28/24px y los controles miden al menos 44px de alto. Cuatro objetos de miniatura forman una cinta compacta en lugar de tarjetas de información iguales. |
| componentes | Button, Input y Skeleton de shadcn/Base UI instalados; raíces y títulos de Dialog/AlertDialog de shadcn con Portal/Backdrop/Popup reales de Animate UI compuestos localmente para cumplir transiciones de entrada/salida según el perfil. SVG personalizados de instalación, escenario, cinta de miniaturas, resumen de escena y filtros nativos. Sin HTML sustituto de respaldo. |
| color | Roles existentes de Pictures: claro #faf9fc/#ffffff/#1c1425 y primario #6d3fe0; oscuro #0b0c10/#16181f/#f4f5f7 y primario #9479ff con texto #120b24. Los controles usan como bordes los tokens de texto legible del proyecto #766c85/#8a91a0. Lavanda/rosa en la escena representan materiales; verde/ámbar/rojo comunican por escrito el estado de guardado/recuperación. |
| movimiento | Un resorte espacial lleva el escenario seleccionado 39.6px hacia un lado con rotación de perspectiva de -5deg y escala .98 en modo expresivo; su estructura se registra a 30px/3deg en 832ms, el grupo de globos cae 24px/7deg en 936ms y la mesa se asienta 18px en 650ms. La cinta entra con desfases de 45ms y se eleva 5px al pasar el cursor. Los controles usan 200ms; los diálogos usan la curva del perfil (420/220/140ms). El movimiento reducido y still=1 eliminan el desplazamiento y usan transiciones de fondo/ventana modal de duración cero; el CSS se pausa en pestañas ocultas. |

## Comportamiento conservado de la fuente r8 compartida

Fuentes: `proyectos@v1.r8.behavior.md`, SPEC US-3/R6/R7 y ronda 9, PLAN SP-4 y tareas T4.1–T4.9/T4.31. La exploración no cambia esos requisitos.

- Proyectos propios: `/proyectos`, búsqueda por nombre en toda la colección autorizada, seguida de paginación. El fixture tiene 63 proyectos, 62 de Ana, y una coincidencia de Aurora más allá de los primeros 50 registros propios. El fixture completo se filtra antes de mostrar las primeras cuatro miniaturas; esto demuestra la semántica, no una implementación de servidor.
- Lista del equipo: el filtro por propietario aparece solo en la vista explícita del equipo. El ejemplo con sesión iniciada sigue siendo Ana Morales en todo momento. El original de Elena Ríos se abre en modo de solo lectura. `taller.usar` controla la disponibilidad de copias propias; el selector de permisos del mock está etiquetado explícitamente como un ejemplo.
- Primer guardado con nombre, autoguardado posterior y Guardar ahora: un proyecto nuevo abre un diálogo de nombre explícito; los nombres en blanco fallan la validación. La edición simulada espera 500ms antes de guardar y luego confirma el nombre enviado. Una guarda de contexto de ticket/proyecto evita que una finalización simulada obsoleta actualice una vista distinta. Las revisiones condicionales reales y el orden de solicitudes del servidor siguen siendo obligaciones de la implementación.
- Un guardado concurrente pausa el autoguardado y conserva la escena local; la persona usuaria puede guardar una copia propia o confirmar la carga de la versión del servidor. La confirmación indica que el borrador permanece local. No se introduce ninguna interfaz de sobrescritura, eliminación, transferencia de propiedad ni historial de versiones.
- Los estados sin conexión/de error nunca dicen guardado. La navegación con trabajo pendiente/sin conexión/en conflicto ofrece Guardar y salir, Conservar borrador y salir, o Cancelar. Guardar está deshabilitado mientras haya desconexión, conflicto o un guardado en curso.
- La importación nombra la cuenta actual, advierte sobre dispositivos compartidos, requiere una acción explícita y ofrece un No ahora reversible. Los datos heredados desconocidos pueden descargarse; la carga inválida/sin conexión está deshabilitada. La descarga ilustrativa está marcada como datos de mock. Una confirmación de éxito lleva a Taller. La preservación del original y la deduplicación segura ante reintentos se expresan en el texto; aquí no se ejecuta ningún localStorage, carga, base de datos ni migración real.
- Solo el nombre y la escena completa viajan entre navegadores. La conversación y las imágenes de IA generadas permanecen locales; ese límite es visible en las vistas de proyecto, editor e importación.
- La ruta de lista propuesta `/proyectos`, el enlace directo del propietario `/3d?proyecto=<uuid>` y la ruta ajena de solo lectura `/proyectos/[id]` siguen siendo destinos del PLAN. Esta exploración estática cambia entre vistas sin fingir navegar ni autenticarse contra producción.

## Vistas y estados alcanzables

Los selectores nativos `view`, `state`, `scene`, `theme` y `motion` provienen del runtime real `mountMockup`; las etiquetas siguen siendo Vista, Estado, Diálogo, Tema y Movimiento. `#language` cambia el texto del producto entre ES/EN. La etiqueta Mockup permanece visible.

| Vista | Estados principales y recuperación |
|---|---|
| Mis proyectos | Normal, skeleton de carga, colección vacía/sin coincidencias de búsqueda, error de carga con reintento, advertencia sin conexión/desactualizado, reintento fallido de la página siguiente conservando las filas cargadas, éxito de guardado y acceso denegado |
| Todos · equipo interno | Los mismos estados de la colección, filtro de propietario autorizado, apertura ajena de solo lectura |
| Taller · guardado | Pendiente, guardando, guardado, sin conexión, error de guardado, resolución de conflicto, permiso interrumpido y validación de guardado con nombre |
| Proyecto ajeno · lectura | Escena de solo lectura, fixtures de permiso/carga/error y copia deshabilitada sin permiso de Taller |
| Importar del navegador | Consentimiento explícito, navegador vacío, carga, importando, datos incompatibles, explicación de respuesta interrumpida/reintento, sin conexión, éxito y rechazo reversible |

Opciones de estado global: `normal`, `loading`, `empty`, `error`, `pending`, `saving`, `offline`, `conflict`, `denied`, `invalid`, `page-error`, `success`. Los estados se aplican donde la vista tiene esa operación; las combinaciones irrelevantes conservan la vista en lugar de inventar un conflicto en un registro de solo lectura. Opciones de diálogo: primer guardado, guardar copia, cargar versión del servidor y salir con cambios. Un contrato canónico confirmado por el propietario debería conservar una matriz de aplicabilidad en lugar de tratar cada combinación cartesiana como un flujo de producto.

## Reflujo, accesibilidad y retroalimentación atendidos

- Escritorio ≥1024px: despliegue de proyecto seleccionado 1.6:1; cinta de cuatro columnas; resumen del editor de 280px. Tableta 768–1023px: despliegue 1.2:1, espacios reducidos y resumen del editor de 230px. Teléfono 360–767px: escenario antes que la leyenda, dos miniaturas por fila, editor/importación de una sola columna, acciones de encabezado con ajuste de línea y acciones de diálogo de ancho completo. El texto largo en español e inglés puede ajustarse en varias líneas.
- El relleno exterior es de 24px en anchos mayores y de 20px en teléfono. La leyenda de la escena tiene su propio borde interior de 24/20px. El pie de página permanece dentro del mismo espacio de trabajo con el mismo eje x exterior; no hay una nota al pie centrada y desprendida.
- Los diálogos tienen relleno de 28px en escritorio/24px en teléfono, un ancho restringido al viewport, desplazamiento cuando es necesario, manejo real de foco modal, un título/descripción nombrados y Cancelar explícito. Escape los descarta; el foco regresa al control que los invocó. La carga usa un Skeleton estructural, no un spinner centrado.
- Los bordes de texto y de controles nativos usan roles del proyecto con contraste verificado; el foco es un contorno de acento de 3px con desplazamiento de 4px. No se introduce ningún checkbox nativo. Las decisiones destructivas/de cargar la versión actual usan el primitivo AlertDialog instalado. Los estados tienen significados escritos y roles live/error.
- Los dibujos de vista previa son SVG en línea. No se descargan fuentes, imágenes, scripts ni hojas de estilo; no se instaló ningún paquete. El constructor de componentes reales instalado estuvo disponible, por lo que no se usaron fragmentos de respaldo ni sustitución con `inline.py`.

## Verificación y límites

- Constructor real sin conexión: PASS; HTML final de 585,511 bytes, 2,135 archivos fuente empaquetados. React, estilos y SVG están en línea; sin instalación de paquetes ni descarga de recursos.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (exit 0).
- `audit_mockup.py` final: 320 renders / 320 combinaciones planificadas a 1280px y 390px, 7,252 mediciones de texto y 873 paradas de foco por teclado (exit 0). No se descartó ninguna combinación por muestreo.
- `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`
- Recorrido de clics enfocado en el navegador: `INTERACTION RESULT: PASS`; búsqueda más allá del registro 50, filtrado del equipo/solo lectura/acceso a copias, validación de guardado con nombre, autoguardado simulado, diálogo de conflicto, navegación protegida sin conexión, rechazo/descarga reversible de importación, controles en inglés y reflujo a 360/390/768/1024/1280px pasaron. Sin errores de página ni solicitudes HTTP(S).
- Seguimiento de movimiento: se observaron en ejecución la entrada y el resorte del proyecto seleccionado; `still=1` y `rm=1` no tienen animaciones en ejecución tras 130ms. La recuperación de error de lectura ajena oculta el contenido de la escena. Cada selector de evidencia JSON coincide con un elemento renderizado en su vista declarada; todos los selectores de movimiento están presentes en la colección.
- SHA-256 del HTML final: `bc66cbdd228286273d35a870c2fd7c16da745761aab96b0aa51702d3a2b40250`.

La revisión renderizada cubre la colección a 1280/390 en ambos temas, el conflicto en teléfono y el diálogo de guardado con nombre en escritorio oscuro. Las comprobaciones de interacción adicionales cubren el fixture de búsqueda completo, el filtro de propietario del equipo, el permiso de copia de solo lectura, el primer guardado explícito, la validación, el autoguardado simulado de 500ms, la confirmación de conflicto, el descarte con Escape y retorno del foco con movimiento reducido, la navegación sin conexión, el rechazo/descarga de importación, los controles en inglés y el reflujo a 360/390/768/1024/1280px. No se observaron errores de página del navegador ni solicitudes HTTP(S) en ese recorrido de clics.

Un recorrido de clics encontró inicialmente una salida de fondo de 400ms bajo movimiento reducido en la composición estándar del componente. La exploración ahora compone directamente el Portal/Backdrop/Popup de Animate UI instalado con transiciones del perfil y duraciones cero cuando se reduce el movimiento. La prueba de interacción enfocada repetida pasó, incluida la ausencia de animaciones en ejecución 120ms después de Escape. Esta es una composición local; las bibliotecas instaladas no se modificaron.

El mockup demuestra presentación e interacciones locales acotadas. El aislamiento real de cuentas, la validación de escenas, las escrituras de revisión condicionales, la recuperación duradera de borradores, la preservación de bytes sin procesar, la idempotencia de la importación, el aislamiento al cambiar de cuenta y el orden de solicitudes de paginación requieren pruebas T4.2–T4.7 en la implementación. Esta tarea de diseño no ejecutó pruebas de producto, compilación de producción, despliegue ni comprobaciones de base de datos.

## Preguntas abiertas y supuestos

Q: ¿La selección de proyectos debería mostrar una vista previa derivada de la escena guardada, o una ilustración neutral hasta abrir el proyecto? Los dibujos aquí son ilustrativos; el PLAN actual no establece la generación/almacenamiento de recursos de vista previa. El Owner/Planner debería resolverlo antes de la finalización sin cambiar la preservación de la escena ni los permisos.

Confirmado: ya están establecidos el primer guardado explícito con nombre y luego autoguardado, solo nombre más escena completa, originales ajenos de solo lectura y copias propias con permiso de Taller, importación reversible basada en consentimiento, búsqueda en toda la colección, y sin eliminación/transferencia/historial. No se reabren como preguntas.

Supuesto de la exploración: las personas de ejemplo, los títulos de proyecto, las marcas de tiempo, los tamaños de sala y los dibujos son ficticios. Las vistas previas de selección pueden ser un esquema neutral si las vistas previas reales de escenas ampliaran el alcance de la implementación.

## Impacto y aprobación

Esto escribe únicamente los archivos de exploración de r8.dir-b y su informe de resultado delegado. No modifica `proyectos@v1.md`, `proyectos@v1.html`, el historial, SPEC, PLAN, el código de producción ni ninguna otra dirección.

Si se elige y se finaliza, T4.1 copia el artefacto canónico aprobado; T4.4 consume las vistas de colección/guardado/solo lectura/conflicto; T4.5 consume los estados de importación; T4.6/T4.7 verifican los flujos reales; T4.8 revisa la fidelidad renderizada; T4.9 audita de forma independiente el aislamiento y la preservación. La compatibilidad es **indeterminada hasta que el propietario elija y se finalice el canónico**. Ninguna implementación está autorizada a consumir este borrador.
