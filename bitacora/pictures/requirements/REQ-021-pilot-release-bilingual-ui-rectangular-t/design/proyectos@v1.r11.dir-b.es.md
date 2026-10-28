---
contract: proyectos
version: 1
status: draft
artifact: direction-exploration
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer
date: 2026-10-28
direction: b
name: Mesa de escenas
revision: r11
source_behavior: proyectos@v1.r11.behavior.md
source: proyectos@v1.r11.dir-b.tsx
mockup: proyectos@v1.r11.dir-b.html
chosen_thumbnail: proyectos@v1.r11.dir-b.html.candidate-1.html
---

# Mesa de escenas — dirección B / r11

## 1. Identidad y trazabilidad

**Borrador de exploración, sin aprobar y no es el contrato canónico proyectos@v1.** Solo se escriben los artefactos asignados a r11/B. El Owner elige una dirección; un finalizador aparte genera el contrato canónico. No se modifica ningún repositorio, plan, contrato hermano, historial compartido ni archivo de memoria del proyecto.

Alcance: `proyectos@v1.r11.behavior.md`, leído primero; “Behavior — SP-3 and SP-4 (round 9 answered)” de SPEC y SP-4 de PLAN.json. R6 corresponde a la lista/acción de abrir/guardar/solo lectura/conflicto de proyectos; R7 corresponde a la importación/rechazo/recuperación explícitos de elementos heredados. Consumidores propuestos afectados: texto de diseño de T4.1, lista de proyectos y guardado de Taller de T4.4, importación de T4.5, revisión visual de T4.8. Las tareas solo de ingeniería quedan fuera de esta exploración.

Fuentes existentes del producto inspeccionadas en modo de solo lectura en t12 y asesor: `src/app/globals.css`, `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `guardado-escena.ts`, `ia/PestanasLaterales.tsx`, `src/components/ui/shell/CabeceraApp.tsx` y `MenuApp.tsx`. El fragmento de fuente prescrito establece el almacenamiento separado de conversaciones/imágenes. Los documentos canónicos actuales `cuentas-admin@v1.md/.html` y `planes@v1.md/.html`, junto con los TSX de sus fuentes seleccionadas, establecen el shell hermano, la tipografía, las funciones de las formas y los bordes de controles accesibles. Los HTML se leyeron como artefactos compilados, no como nuevo comportamiento de producción.

El informe más reciente fija la paleta, las fuentes, el shell y el vocabulario de componentes. Por lo tanto, prevalece sobre los comentarios históricos que pedían paletas/tipografías independientes. Esta dirección centra su variación en la disposición, la densidad, la navegación local y el movimiento espacial del área modificada. Usa bibliotecas instaladas reales en lugar de la alternativa antigua de HTML simulado.

Compatibilidad: borrador alternativo con una composición de lista distinta, **incompatible con una implementación de lista dispuesta de otra manera**; no reemplaza ninguna versión aprobada. La acción requerida sigue siendo la selección del Owner y la aprobación posterior del plan exacto, seguida de la implementación y una revisión independiente. Esta nota no autoriza ninguna de ellas.

## 2. Propósito y usuarios

El Owner encuentra y vuelve a abrir una escena con nombre, luego continúa en Taller con un estado veraz del guardado en la cuenta. El personal autorizado busca en todas las cuentas y abre originales externos en modo de solo lectura. Una persona que inicia sesión con una escena heredada en el navegador decide si pertenece a la cuenta actual. El éxito consiste en una escena completa reabierta o en un guardado/importación confirmado, preservando el trabajo sin enviar y la fuente original si se produce un fallo.

Solo el nombre y la escena completa se transfieren entre navegadores. La conversación y las imágenes generadas permanecen en el navegador. No se añade ninguna interfaz de eliminación, transferencia ni historial de versiones.

## 3. Enfoque, composición y jerarquía

El shell actual de la cuenta/aplicación rodea **una sola hoja de trabajo**: índice compacto de proyectos a la izquierda, lienzo de la escena seleccionada en el centro e identidad/propietario/acción del proyecto a la derecha. La selección permite inspeccionar; **Abrir proyecto** entra explícitamente en Taller. La vista previa local se deriva de la escena guardada completa, no de una captura almacenada, una función de sincronización de contenido multimedia ni un lienzo editable independiente.

Así, la escena es el contenido principal, a diferencia de una galería de tarjetas con miniaturas o un registro editorial de ancho completo. La búsqueda y la selección de propietario permanecen junto a los registros que filtran. El propietario y el significado de solo lectura aparecen junto a la acción que abre el proyecto. No se añaden contadores decorativos, fechas ni texto de marketing; el pequeño recuento de registros se deriva del mismo fixture neutro.

Se dibujaron dos miniaturas antes del TSX completo:

- **Candidato 1, seleccionado:** índice / escena / inspector. Contexto espacial continuo y una acción explícita para abrir; admite tanto proyectos propios como externos sin introducir una galería.
- Candidato 2: escena con una franja horizontal inferior y detalles laterales. Compite con el panel inferior existente de Taller en teléfonos y ofrece menos espacio para los filtros de búsqueda/propietario. Se conserva como miniatura de comparación, no como otra dirección implementada.

El SVG central es una escena simulada ilustrativa, no un renderizador 3D funcional. Producción debe derivar la vista previa de la escena autorizada seleccionada sin prometer almacenamiento de imágenes en la nube.

## 4. Sistema de diseño fijo y ocho ejes

| Eje | Evidencia renderizada y enfoque |
|---|---|
| Concepto | Un banco de trabajo de escenas para volver a abrir trabajos guardados: un índice de proyectos persistente, una vista de escena derivada y un inspector del proyecto seleccionado dentro del entorno establecido de Pictures. |
| Diseño | Una hoja continua con columnas de 276px / flexible / 238px; en tablet, el índice permanece junto a un área apilada de escena y detalle; en teléfono, se apilan el índice, la escena y el detalle. |
| Navegación | Rutas horizontales compartidas de Taller 3D / Proyectos guardados; selección local de proyecto con estado presionado, seguida de Abrir proyecto explícito; anclas en teléfono conectan la lista de proyectos y la vista previa de la escena. |
| Tipografía | Geist Sans y Geist Mono locales existentes; título de página de 24px, inspector de 20px, encabezado del índice de 16px, texto de 14–15px y metadatos de 12–13px. Sin familias nuevas. |
| Densidad | Registros de proyectos compactos y separados, junto a una escena dominante y un inspector de lectura despejado. Se reutilizan las formas existentes de hoja de 32px, campo de 18px y control tipo píldora; márgenes interiores de 24px en escritorio y 20px en teléfono. |
| Componentes | Button e Input de shadcn/Base UI instalados, Skeleton y Dialog de Animate UI; selects y disclosure de cuenta nativos, filas de proyecto semánticas y un SVG de escena ilustrativo local. |
| Color | Tokens exactos de fondo/superficie/texto/acento de Pictures y de estados semánticos; superficie de taller-visor para la escena. Los bordes de los controles usan el alias texto-tenue del proyecto hermano. Sin paleta nueva. |
| Movimiento | Bisagra espacial indexHinge de 620ms con cubic-bezier(.22,.85,.3,1.08), inspectorDock lateral, sceneDolly de 775ms, desfase rowDepth de 65ms, statusRegister, marcador con resorte compartido y hover/press de 180ms. Tiempos naturales/sutiles de escala; Quieto/inmóvil/reducir eliminan el movimiento. |

Entorno compartido: marca de anillo y punto de Pictures, separador con el logotipo de Sempertex, selector de idioma, disclosure de cuenta con nombre, regla de ruta horizontal, título de 24px y pie alineado. Sigue el vocabulario elegido/finalizado del proyecto hermano; no importa sus formularios de cuenta ni su diseño de comparación de planes.

| Token de origen de producción | Función / uso en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--superficie-2` | atenuado, secundario, fila seleccionada | #efe9f8 / #242733 |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto de apoyo | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde de entrada/control, alias heredado del proyecto hermano | #766c85 / #8a91a0 |
| `--acento` / `--sobre-acento` | principal/anillo y texto principal | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento-hover` | hover principal | #5530b8 / #a58dff |
| `--borde` / `--borde-suave` | marcos/reglas decorativos | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| `--taller-visor` | lienzo de escena | #ebe7f1 / #1a1722 |
| `--taller-barra` / `--taller-panel` | elementos de interfaz existentes de Taller | #ffffff / #faf9fc; #121018 / #16131d |
| `--exito` / `--exito-suave` | éxito confirmado | #1f7a55 / #dcf5e9; #78d6a8 / #173b31 |
| `--aviso` / `--aviso-suave` | pendiente/sin conexión | #8f5f12 / #fff3d8; #f7c46b / #3f311c |
| `--error` / `--error-suave` | conflicto/error | #b23a45 / #ffeaec; #ff979f / #43252a |

Geist y Geist Mono están incrustadas desde los recursos WOFF2 locales existentes de Next; sin fuentes de red ni instalaciones. El cuerpo usa 15px/1.5; las filas de proyecto, 14px; las etiquetas de apoyo, 12–13px; y los encabezados, 16/20/24px. Mono se limita a metadatos de conteo/logotipo. Paneles/campos/píldoras reutilizan las funciones de 32/24/18/999px de los proyectos hermanos. Los márgenes interiores de grupos enmarcados son de 24px en escritorio y 20px en teléfono; los diálogos usan 28px en escritorio y 24px en teléfono. Los bordes decorativos no sustituyen los bordes visibles de los controles.

Procedencia real de los componentes, según `real/manifest.json`:

| Origen:id / variantes / estados | Importación real o composición personalizada |
|---|---|
| `shadcn:button default/outline/ghost ready/hover/focus/pressed/disabled` | `@/components/ui/button`, Base UI; Action reenvía data-variant explícito para el mapeo del proyecto |
| `shadcn:input text empty/filled/invalid/focus` | `@/components/ui/input` |
| `shadcn:skeleton project/scene loading` | `@/components/ui/skeleton` |
| `shadcn:dialog save/copy/rename/new/leave/load open/closed` | `@/components/ui/dialog`, mejora instalada de Animate UI/Base UI |
| `custom:project-index selection/filter/pagination` | aside semántico, select nativo de propietario con etiqueta, botones de fila con estado presionado |
| `custom:scene-preview illustrative normal/empty` | SVG y figure locales, sin atribuirlo a un componente 3D de terceros |
| `custom:account-disclosure closed/open` | details/summary nativo conservado del entorno del proyecto hermano; Escape devuelve el foco |
| `custom:local-navigation route/fragment` | anclas semánticas; las anclas del teléfono enfocan el destino sin perder la selección |
| `custom:selection-marker selected` | `motion.span` de `motion/react`; perfil de `@kit/motion` |
| `custom:planning-controls view/state/scene/theme/motion` | `mountMockup/useMockup` de `@kit/mockup` |

## 5. Detalle de navegación y movimiento

Entrada: navegación de productos de la cuenta → `/proyectos`; proyecto seleccionado → `/proyectos/[id]` / contexto de Taller. El artefacto de planificación usa selectores de vista locales en lugar de navegación de red. La vista de importación representa la primera visita autenticada a Taller, no una ruta pública nueva. Los enlaces de cuenta llevan a los mockups locales del proyecto hermano; el cierre de sesión se simula explícitamente.

La selección en el índice de escritorio actualiza la escena derivada y el inspector del propietario sin entrar en modo de edición. En teléfono, las anclas “Lista de proyectos” y “Vista previa” conectan las secciones apiladas; su activación con teclado enfoca el destino indicado. El inspector mantiene la única acción principal **Abrir proyecto**. Taller conserva el encabezado con nombre/estado de escena, los controles de deshacer/rehacer/foto/compra, la barra de herramientas de 60px, la escena y el contexto del panel Pieza/IA. Los controles existentes del editor son representaciones contextuales; su comportamiento de producción no se rediseña.

Comportamientos animados diferenciados:

1. `.project-index`: bisagra finita en perspectiva, x=-16px / rotateY(9deg), ligero sobreimpulso y se estabiliza a los 620ms.
2. `.project-row`: registro rowDepth, x=-8px con desfase de 65ms; la opacidad del texto siempre permanece completa.
3. `.scene-art`: desplazamiento tipo cámara de 775ms desde scale(.94)/y=12px con un pequeño sobreimpulso de estabilización.
4. `.project-inspector` y `.import-panel`: entrada lateral derecha de 620ms desde x=32px, luego x=-3px y finalmente reposo.
5. `.selection-pin`: resorte de diseño compartido entre registros seleccionados, rigidez expresiva de 220 / amortiguación de 16 / masa de .9.
6. `.status` / `.status-line`: registro scaleX(.8) al cambiar de estado; el texto de estado permanece legible.
7. Al pasar el cursor por `.project-row`, se desplaza 4px; los botones se elevan -2px, se comprimen a .975 al presionarlos y desplazan su ícono en línea 2px. El anillo de foco aparece de inmediato y mide 3px.
8. El grupo de skeletons de carga usa un barrido de 3px en lugar de destellos de opacidad; al abrirse, el modal usa el comportamiento instalado de Animate UI.

La función de aceleración CSS espacial es `cubic-bezier(.22,.85,.3,1.08)`, separada intencionalmente de la gramática de registro de acceso o de hoja de comparación de los proyectos hermanos. Natural usa 360/140/35ms y sutil usa 180/100/15ms para estabilización/acción rápida/desfase. El valor predeterminado es expresivo. El movimiento reducido, `?still=1` y Quieto eliminan los desplazamientos/transiciones, incluidos los pseudoelementos; el contenido, el foco y la respuesta se mantienen. Las animaciones CSS se pausan en pestañas ocultas. No hay efectos ambientales continuos pesados; las demás entradas son finitas.

## 6. Flujos y reglas de conservación

1. **Primer guardado:** trabajar en una escena sin guardar → Guardar proyecto → diálogo con nombre y etiqueta → validar que el nombre no esté en blanco → confirmar → estado guardado confirmado por la cuenta. Solo entonces pueden guardarse automáticamente las ediciones posteriores. Se conserva el límite de 120 caracteres del campo de nombre existente. Cancelar un diálogo de nombre deja sin cambios el nombre visible.
2. **Guardados posteriores:** cambiar la escena → Guardando… → Guardado en tu cuenta solo para la revisión más reciente confirmada. Guardar ahora sigue disponible. Las respuestas obsoletas nunca pueden confirmar trabajo pendiente más reciente.
3. **Escena nueva/plantilla/biblioteca:** primero guardar las ediciones pendientes del proyecto abierto con nombre; si no se puede completar, conservar la escena actual y explicar cómo recuperarla. Para una escena nunca guardada, preguntar si se desea guardar, continuar sin guardar o cancelar. Después, las tres entradas crean una **Escena nueva / Sin guardar** sin vínculo; no se escribe en el servidor hasta el primer guardado con nombre.
4. **Lista/volver a abrir:** aplicar la búsqueda autorizada del servidor y los filtros de propietario antes de paginar. Los cambios de filtro reinician la paginación. Ante un error al ir a la página siguiente, conservar los resultados actuales y permitir volver a intentar esa página. Ignorar respuestas de consultas obsoletas. Abrir la escena completa con el nombre guardado.
5. **Conflicto:** detener el guardado automático, conservar el borrador local y mostrar el conflicto junto a la escena visible. Ofrecer Cargar versión del servidor con confirmación explícita o Guardar copia en la cuenta actual. Al cargar la versión del servidor, conservar una opción visible Guardar borrador como copia para recuperar el borrador local preservado. Ninguna opción sobrescribe silenciosamente el original ajeno o en conflicto.
6. **Sin conexión/error:** permitir continuar el trabajo local, mostrar el estado no guardado, conservar los cambios pendientes y ofrecer reintentar. Bloquear el reemplazo por una escena nueva mientras no se pueda guardar el trabajo pendiente del proyecto actual con nombre. Las ediciones locales simuladas conservan la etiqueta sin conexión/conflicto en vez de generar un éxito falso.
7. **Lectura de proyecto ajeno:** mostrar el propietario y Solo lectura; no mostrar controles editables para el nombre original ni para la escena. Solo taller.usar permite Guardar copia. Las vistas de lista con permiso denegado no revelan contenido de proyectos. Las comprobaciones de permisos siguen a cargo del servidor.
8. **Importación heredada:** mostrar primero la identidad de la cuenta actual y luego las acciones explícitas de importar/rechazar. El éxito crea un proyecto propio, incluso después de reintentar; el rechazo/error/entrada no válida dejan intactos los datos locales sin procesar. Los datos no válidos explican el error de formato, ofrecen Descargar original y permiten continuar sin importar. Solo se importan el nombre/la escena; la conversación y las imágenes permanecen locales.

## 7. Especificaciones de las vistas

| `view` nativa | Estructura y acción principal |
|---|---|
| `list` | Entorno compartido → encabezado de proyectos/regla de ruta → nota etiquetada sobre datos de prueba → índice de proyectos / escena seleccionada / inspector del propietario → Abrir proyecto |
| `staff` | La misma hoja; el filtro Cuenta propietaria aparece sobre las filas y abarca a los propietarios autorizados. La selección de un proyecto ajeno indica Solo lectura antes de abrirlo. |
| `taller` | Contexto existente de Taller con nombre de escena y estado de guardado en línea; Guardar proyecto/Guardar ahora explícitos; la recuperación por conflicto/sin conexión aparece sobre la escena sin reemplazarla. |
| `foreign` | Escena de Taller legible; aviso del propietario y Solo lectura; controles del nombre original/edición deshabilitados; Guardar copia requiere permiso de Taller. |
| `import` | Mensaje de primera visita en el contexto de Taller: vista previa de la escena del navegador / decisión de importar a la cuenta actual, explicación de conservación y recuperación ante éxito/rechazo/error. |

Los datos de prueba neutrales usan únicamente “Escena de ejemplo” con sufijos ordinales, Cuenta Master Designer / Cuenta de ejemplo y `master@prueba.local` / `admin@prueba.local`, vocabulario de pruebas heredado. No se inventan fechas, afirmaciones sobre clientes, identidades reales ni capturas de pantalla. Los globos de la ilustración son contenido de la escena, no una identidad visual nueva.

## 8. Estados y selectores declarados

El selector de estado nativo permite acceder a todos los estados siguientes. Las combinaciones irrelevantes conservan el estado base de esa vista; el siguiente mapeo define los escenarios significativos. Se puede acceder a los diálogos de forma independiente mediante la vista nativa `scene` y mediante acciones reales.

| `state` | Vista aplicable / recuperación esperada |
|---|---|
| `normal` | Todas las vistas; fixture lista ordinaria |
| `loading` | Filas skeleton y vista previa de list/staff; carga de origen de importación; sin datos guardados falsos |
| `empty` | list/staff: explicación e Ir al Taller 3D |
| `no-match` | list/staff: sin coincidencias autorizadas; Limpiar filtros |
| `next-page` | list/staff: segunda página del fixture cargada |
| `page-error` | list/staff: se conservan las filas anteriores; Reintentar página |
| `saving` | Encabezado de Taller Guardando…; importación Importando… con el envío deshabilitado |
| `saved` | Encabezado de Taller Guardado en tu cuenta |
| `unsaved` | Taller Escena nueva / Sin guardar; el primer guardado solicita un nombre |
| `offline` | Cambios de Taller pendientes con opción para reintentar; la importación conserva el origen si falla |
| `error` | Reintento de lista / reintento de guardado de Taller / reintento de importación, según la vista activa |
| `conflict` | Taller detiene el guardado automático; recuperación con la versión del servidor o una copia propia |
| `invalid` | Error de formato de importación con descarga del original; validación del diálogo de guardado con nombre |
| `imported` | Confirmación de importación y Abrir proyecto |
| `forbidden` | Rechazo de list/staff sin metadatos restringidos; opción de copia externa deshabilitada sin permiso de Taller |

Diálogos nativos: ninguno, primer guardado, copia propia, iniciar otra escena, cargar la versión del servidor, salir de una escena sin guardar y cambiar el nombre. La validación del formulario de primer guardado se activa al enviar un nombre vacío. Los diálogos cerrados no están presentes ni activos; el foco vuelve al control que los abrió. Los controles permanentes de eliminación/transferencia/historial no aplican y no aparecen.

## 9. Comportamiento adaptable

- **1100px o más:** hoja de tres columnas (276px / flexible / 238px), márgenes exteriores de 40px. Taller conserva la barra / escena / panel lateral. La lista de registros y la acción de apertura comparten una misma ventana gráfica a 1280px.
- **640–1099px:** márgenes de 24px, índice de 240px junto a la escena; el inspector pasa debajo de la escena, en la misma segunda columna. Los datos de propietario/nombre usan dos columnas. El panel lateral de Taller pasa debajo de su escena y conserva el orden del DOM. La importación mantiene dos columnas con ajuste flexible del texto.
- **320–639px:** márgenes e interiores exteriores de 20px. Índice → vista previa → inspector forman una hoja apilada. Las anclas del teléfono conectan la lista y la vista previa; los controles se ajustan y la acción principal ocupa todo el ancho disponible. La importación apila la vista previa y luego la decisión; los diálogos usan un área de desplazamiento limitada por la ventana gráfica. El encabezado ajusta la marca y los controles de cuenta/idioma en filas alineadas. No hay desplazamiento horizontal de página.

El español es el idioma inicial. El control de idioma conservado muestra etiquetas traducidas y cadenas más largas en inglés; la implementación centraliza todo el texto nuevo en `src/components/proyectos/textos-proyectos.ts`. No se declara persistencia nueva de configuración regional.

## 10. Objetivos de accesibilidad y límites de la evidencia

Objetivo WCAG 2.2 AA, sujeto a una revisión de implementación independiente. Se requieren encabezados y regiones semánticos, etiquetas asociadas a campos de entrada y selección, descripciones alternativas para SVG, controles de icono con nombre, controles de 44px, foco visible de 3px, navegación por teclado entre rutas y fragmentos, selección de proyecto con estado presionado, confinamiento del foco en diálogos modales, cierre con Escape y retorno del foco, estado de guardado anunciado de forma cortés y validación y recuperación explícitas. El texto debe tener un contraste ≥4.5:1 y los bordes de controles significativos y el foco, ≥3:1 en ambos temas, incluso durante la animación; el texto de entrada no usa desvanecimiento de opacidad.

El fixture estático nunca lee ni escribe el localStorage, IndexedDB, las cookies, las sesiones ni los proyectos del servidor reales. No puede demostrar autorización del servidor, control atómico de revisiones, deduplicación por hash de origen, integridad entre navegadores, retención duradera de borradores locales, condiciones de carrera al eliminar, rechazo de respuestas de red obsoletas ni conformidad con tecnologías de asistencia. Eso sigue pendiente de verificación en producción. El primer guardado es una acción inmediata del fixture; el inspector de estado muestra explícitamente el guardado, el modo sin conexión y el conflicto, así como las ediciones simuladas posteriores. Producción también debe deshabilitar los envíos del primer guardado pendientes y mostrar el estado real de espera y resultado del servidor.

Los controles preexistentes de foto, compras e historial de Taller, y el contexto de Pieza/IA, son elementos visuales de referencia etiquetados como ajenos a la interacción modificada; esta exploración no implementa herramientas de edición. No hay instalación de paquetes, solicitudes de red, sustitución por un kit HTML de respaldo ni un directorio de vista previa independiente.

## 11. Criterios de aceptación visual observables

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 1280px | lista normal | El encabezado compartido y la regla de ruta preceden una única ficha de proyecto continua con tres columnas. |
| B-AC-02 | 1280px | lista normal | La escena ocupa la columna central flexible; la acción explícita Abrir proyecto está en el inspector derecho. |
| B-AC-03 | 768/1024px | lista normal | El índice permanece a la izquierda; el inspector aparece debajo de la escena, sin desplazamiento horizontal de página. |
| B-AC-04 | 320/390px | lista normal | El índice, la vista previa y el inspector se apilan; los anclajes del teléfono llevan a la lista o a la vista previa y establecen el foco del teclado. |
| B-AC-05 | Todos los compatibles | filtrado de lista/personal | La búsqueda o el filtro reinicia la paginación y la vista previa corresponde a un proyecto autorizado que coincide. |
| B-AC-06 | Todos los compatibles | carga de lista | Los esqueletos con etiquetas reemplazan las filas y el contenido de la escena seleccionada. |
| B-AC-07 | Todos los compatibles | lista vacía/sin coincidencias/error | Cada estado ofrece la recuperación adecuada: crear, borrar el filtro o reintentar. |
| B-AC-08 | Todos los compatibles | error de página | Los registros existentes permanecen visibles encima de Reintentar página. |
| B-AC-09 | Todos los compatibles | Taller sin guardar | El encabezado muestra Escena nueva / Sin guardar y Guardar proyecto abre el diálogo de nombre. |
| B-AC-10 | Todos los compatibles | primer guardado no válido | Un envío vacío muestra un error de nombre asociado sin cerrar el diálogo. |
| B-AC-11 | Todos los compatibles | cancelar cambio de nombre | El nombre anterior de la escena permanece visible y el foco vuelve al control de nombre. |
| B-AC-12 | Todos los compatibles | guardando/guardado | El encabezado distingue Guardando… de Guardado en tu cuenta. |
| B-AC-13 | Todos los compatibles | sin conexión | Los cambios locales siguen visiblemente pendientes; reintentar y crear una escena nueva conservan la escena actual. |
| B-AC-14 | Todos los compatibles | conflicto | La escena local permanece visible debajo de la recuperación; ningún éxito de guardado automático reemplaza el conflicto. |
| B-AC-15 | Todos los compatibles | recuperación de versión del servidor | Cargar la versión del servidor deja visible la acción Guardar borrador local como copia. |
| B-AC-16 | Todos los compatibles | ajeno | El aviso de propietario y solo lectura está visible; las ediciones de escena y nombre están deshabilitadas y la copia depende de los permisos. |
| B-AC-17 | Todos los compatibles | importación normal | La cuenta de destino actual está visible antes de los controles Importar/No importar. |
| B-AC-18 | Todos los compatibles | rechazo/error de importación | Aparece una copia de preservación y el rechazo permite continuar a Taller. |
| B-AC-19 | Todos los compatibles | importación no válida | Se muestran la explicación del origen no válido, Descargar original y Continuar sin importar. |
| B-AC-20 | Todos los compatibles | importación completada | El éxito reemplaza el envío de importación y ofrece Abrir proyecto. |
| B-AC-21 | Todos los compatibles | diálogo modal abierto | Tab permanece dentro del diálogo; Escape cancela y restaura el foco. |
| B-AC-22 | 390/1280px | claro/oscuro | Los tokens de origen, Geist integrado y los bordes accesibles de los controles coinciden con el vocabulario de la interfaz hermana. |
| B-AC-23 | 1280px | inicial expresivo | La bisagra del índice, la alineación de filas, el movimiento de cámara de la escena, el acoplamiento del inspector y la alineación del estado se animan de forma visible. |
| B-AC-24 | Todos los compatibles | Quieto/estático/reducción de movimiento | No quedan animaciones de entrada o desplazamiento activas; los datos, el proyecto seleccionado y las opciones de recuperación siguen visibles. |
| B-AC-25 | Todos los compatibles | nuevo/plantilla/biblioteca | La escena nunca guardada solicita confirmación antes de reemplazarse; la siguiente escena comienza sin vínculo y sin guardar. |

### Verificación real

- Generador de componentes reales sin conexión: PASS; el código fuente final agrupa 2,126 archivos de origen en un HTML de aproximadamente 646KB con recursos integrados. Sin solicitudes, instalaciones ni contenido de respaldo.
- `contrast.py`: **158 pares comprobados en temas claro y oscuro; todos pasan**, código de salida 0.
- Primera auditoría completa: 630 renderizados en 1280/390/768; PASS. Auditoría posterior en cuatro anchos: 840 renderizados, 28,136 mediciones de texto y 1,517 paradas de foco; PASS. Después, el fixture final habilitó ediciones simuladas locales sin conexión y en conflicto, sin confirmar un guardado; más abajo se registra una auditoría final reciente.
- Playwright complementario en caché: **18 grupos PASS**, con cobertura de paginación, coincidencias después de la primera página del fixture, filtrado por propietario, modo ajeno de solo lectura/sin permiso de copia, primer guardado/validación, cancelación de cambio de nombre/foco, guardado automático, copia de conflicto conservada, reemplazo/reintento sin conexión, las tres formas de crear una escena nueva, rechazo/continuación, importación correcta, descarga de datos no válidos y confinamiento del foco en el diálogo modal. Las muestras adaptables cubren ES/EN en 320/390/640/768/1024/1280 en ambos temas, sin desbordamiento de página. No se observaron errores de página ni solicitudes HTTP. Una primera comprobación inmediata de Tab observó el delimitador de foco intermedio de Base UI; una prueba diagnóstica y una nueva ejecución, con una espera de 40ms para el microproceso del administrador de foco, confirmaron el confinamiento de 12 paradas. No se debilitó ninguna comprobación de producción.
- Capturas de pantalla inspeccionadas en memoria, sin escribir archivos adicionales: lista en 1280 claro y 390 oscuro; conflicto de Taller en 1280 oscuro; importación no válida en 390 claro. Se mantienen los ejes comunes, los márgenes generosos y los controles legibles. En la sesión se registra una inspección final adicional de la lista en teléfono claro y escritorio oscuro.
- Evidencia de selectores: `compare_directions.py` con solo B pasó (`ok=true`, `evidence_ok=true`, sin evidencia faltante); esto demuestra las afirmaciones de B, no la distinción por pares. La comparación de tres direcciones no pudo ejecutarse al principio porque los metadatos JSON de las direcciones hermanas aún no estaban disponibles. El estado de la comparación final se registra abajo.

Auditoría final del artefacto reconstruido, `--widths 1280,390,768,1024 --max-combos 240`: **840 renderizados (840 combinaciones previstas), 28,152 mediciones de texto, 1,530 paradas de foco**, código de salida 0; sin advertencia de muestreo.

**RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**

Comprobación complementaria después del cambio final de edición local: **5 comprobaciones adicionales PASS** — la edición sin conexión permanece sin guardar, la edición en conflicto permanece sin guardar, el modo expresivo tiene efectos activos, `?still=1` no tiene efectos en curso y la preferencia de movimiento reducido del sistema operativo no tiene efectos en curso. Estas comprobaciones complementan los 18 grupos de interacción anteriores; no demuestran el comportamiento del servidor.

SHA-256 del HTML final: `fdb6dbc9425219ea4658ed0c352d85851ba235a75d111855352514bfca564b77`.
Comparación final de tres direcciones `compare_directions.py A.html B.html C.html --json`: **PASS**, código de salida 0, `ok=true`, `evidence_ok=true`, sin evidencia de selectores faltante. Todos los pares pasan: similitud de diseño A/B **0.131**, B/C **0.156**, A/C **0.114**. B difiere de ambas alternativas en movimiento real; B/C también difieren en densidad. La navegación de ruta compartida se mantiene intencionalmente consistente con el armazón del producto. Los archivos hermanos solo se leyeron; no se modificaron.

## 12. Preguntas abiertas, supuestos e inquietudes

**Preguntas abiertas del propietario: ninguna nueva.** La política de primer guardado/guardado automático, el contenido completo de la escena, los derechos de copia del personal, la semántica de escena nueva y el filtrado de toda la colección ya están definidos en el resumen/SPEC proporcionado. La elección de dirección y la aprobación independiente del plan siguen pendientes y esta exploración no las concede.

Supuestos para esta propuesta: una escena seleccionada se puede mostrar en modo de solo lectura a partir de su documento autorizado; no se necesita ninguna imagen adicional en la nube. La disposición de vista previa y la navegación por fragmentos del teléfono son propuestas específicas de esta dirección, pendientes de la elección del propietario. Los nombres de ejemplo, la identidad y la ilustración son solo del fixture; las dimensiones, referencias y colores reales de la escena completa siguen siendo la fuente de verdad persistida. El envío local inmediato y los datos descargados del fixture no demuestran el comportamiento real del servidor ni la fidelidad de una importación real desde el navegador.

**INQUIETUDES:** El borrador sigue sin aprobarse; el backend, el editor real y la tecnología de asistencia no están verificados. La evidencia de auditoría/comparación final anterior debe interpretarse teniendo en cuenta esos límites. El contrato/HTML canónico, SPEC, PLAN, los repositorios de producción y las otras direcciones no se modificaron.
