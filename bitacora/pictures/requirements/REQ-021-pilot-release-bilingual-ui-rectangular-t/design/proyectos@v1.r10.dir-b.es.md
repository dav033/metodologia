---
name: Bambalinas
status: draft
kind: independent-direction-exploration
contract_ref: proyectos@v1
revision: r10.dir-b
subplan: SP-4
requirements: [R6, R7]
owner: David
approval: pending-owner-selection
chosen_thumbnail: proyectos@v1.r10.dir-b.html.candidate-2.html
---

# Bambalinas — dirección B

## 1. Identidad y trazabilidad

Exploración cinética/espacial independiente, a la espera de la selección del propietario. Este no es el contrato canónico, una aprobación ni una entrada para la implementación. Fuentes: `SPEC.md` `65b1e5ecc06f20d9`; `PLAN.md` `cc7e53f2abf3c23c`; `PLAN.json` `7a2c833a7e711508`; `design/proyectos@v1.r10.behavior.md` `378c0aa4a41164c6`. Las fuentes pueden seguir cambiando durante la planificación colaborativa; los hashes identifican la instantánea consultada aquí.

SP-4 cubre los proyectos de servidor pertenecientes a la cuenta de R6 y la importación explícita y sin pérdida de escenas del navegador de R7. T4.1 finalmente copia el contrato canónico aprobado; T4.4 consume la lista de proyectos/la interfaz de guardado y solo lectura, y T4.5 consume la importación. T4.6/T4.7 verifican la integración real del servicio/navegador; T4.8 revisa la implementación renderizada y T4.9 la audita de forma independiente. El punto de control de almacenamiento/API T4.31 sigue fuera de este diseño. No se modificó ningún artefacto canónico, plan, repositorio ni historial.

## 2. Concepto y movimiento memorable

**Bambalinas** convierte la estructura de montaje del decorador de eventos en una interfaz de trabajo guardado. Una escena cuelga de dos cables debajo de una viga compartida. Los proyectos con nombre forman una hilera escalonada de contrapesos. Al seleccionar un nombre, la escena desciende hasta su lugar; abrirla sigue siendo una operación independiente y claramente identificada. Esto responde a «¿Qué instalación quiero continuar?» sin requerir gestos espaciales.

**Movimiento memorable:** la polea gira, la escena desciende con una leve corrección de perspectiva y sus contrapesos con nombre se elevan hasta alinearse. El conjunto de látex se mueve contra la estructura de montaje rígida mientras una estrella de foil gira atada a su cordel. El texto real permanece opaco durante todo el movimiento. Los controles de trabajo siguen siendo rápidos y familiares.

## 3. Dos miniaturas nuevas y registro visual

Ambas miniaturas visuales se dibujaron antes del TSX completo. Cada una contiene su propio CSS integrado, una fuente local de presentación incrustada, un selector de tema y reorganización para teléfonos. Son estudios visuales pequeños, no alternativas HTML a los componentes reales.

- Candidata 1, `proyectos@v1.r10.dir-b.html.candidate-1.html`: una plataforma giratoria redonda e inclinada junto a un directorio de proyectos plano. Su marcada silueta circular sugiere rotación, pero deja el directorio sin relación con el objeto y se superpone con ideas anteriores de elevación frontal/cintas.
- **Elegida: candidata 2**, `proyectos@v1.r10.dir-b.html.candidate-2.html`: una viga completa con una escena suspendida y contrapesos escalonados con nombre. La escena y el directorio comparten una relación estructural concreta. Se amplía de forma natural para incluir el comprobante de guardado del taller y se apila en una secuencia legible para teléfonos.

Consulta las notas del registro visual de sus proyectos hermanos: cuentas-admin r10 A registro de producción, B umbral inflable y C bandas de látex; taller-esenciales r9 A/B/C, incluido su ensamblaje espacial y su silueta moldeada. Esta dirección evita su hoja de producción, la composición de acceso/formulario, el riel de identidad a la izquierda, la navegación orbital de tabla y el cinturón de herramientas moldeado. La silueta del nombre/punto-anillo de Pictures, el lenguaje directo del producto, los materiales de globos Sempertex, los nombres semánticos de tokens y las acciones seguras explícitas aportan continuidad. No se copió ni modificó HTML o TSX de proyectos anteriores.

## 4. Por qué esta propuesta no es una opción predeterminada y cuáles son sus ocho ejes

La jerarquía se construye a partir de una viga de montaje y sus contrapesos, en lugar de tarjetas independientes de un panel. La tipografía serif condensada y vertical para titulares, los herrajes bermellón, el laminado plata y salvia, los extremos redondeados en un solo lado y el movimiento vertical recíproco pertenecen a una misma idea física. No agrega contenido de relleno para KPI ni capacidades de producto inventadas. La escena es explícitamente una ilustración; la maqueta estática no afirma representar un documento 3D guardado.

| Eje | Expresión actual |
|---|---|
| Concepto | Bambalinas: un sistema de tramoya para decoradores. Una instalación completa de globos cuelga de un pórtico; los nombres de los proyectos son contrapesos que colocan una escena en posición de trabajo. |
| Diseño | Un título de trabajo amplio y la búsqueda en la colección preceden a un pórtico de ancho completo. Una escena suspendida del 57% y un directorio escalonado de contrapesos del 43% comparten una viga; en el teléfono, la escena, los detalles, los nombres de los proyectos y la recuperación de importaciones se apilan. Taller reemplaza el directorio por una ficha estrecha de escena y guardado. |
| Navegación | Los contrapesos con nombres de proyectos son botones reales en una región de navegación, con selección mediante aria-pressed y una acción Abrir explícita y separada. El personal autorizado usa selectores de colección y propietario. El enlace superior para volver y una franja de importación contextual permiten salir, sin barra lateral, vista orbital, carrusel ni cinta de miniaturas. |
| Tipografía | DejaVu Serif Condensed Bold incrustada y vertical como Marquee, para titulares de 48–88px y encabezados de escena de 27–34px; Liberation Sans regular/negrita incrustada para el texto de trabajo y Liberation Mono para los conteos de carga, las etiquetas de revisión y los pies de escenario. El título se extiende verticalmente hasta la zona de registro. |
| Densidad | Margen exterior de escritorio de 40px, separación entre escenarios de 40px, relleno de contrapesos de 22px, acciones de al menos 44px y campos de 46px; márgenes de 20px en el teléfono y una sola columna por debajo de 768px. Las placas rectilíneas del escenario contrastan con un extremo redondeado del contrapeso. |
| Componentes | Button, Input y Skeleton reales de shadcn/Base UI, y Checkbox, Dialog y AlertDialog de Animate UI; los resortes del perfil de Motion colocan una escena personalizada de látex y laminado en SVG. El pórtico, los cables, los botones escalonados de contrapesos y el hilo de guardado personalizados son una composición propia del producto, no fragmentos presentados como componentes instalados de la biblioteca. |
| Color | Propuesta asignada a los roles semánticos de Pictures: gris frío de escenario #e8eceb, blanco verdoso opaco #f8faf8, tinta #232c28, acción bermellón #b62913 y laminado plata y salvia. Escenario oscuro #14211b/#20342a, texto #f0f7f0 y acción con reflejo de laminado color durazno #ffb3a0. Los degradados de material solo aparecen dentro de la ilustración del globo; no hay texto sobre degradados. |
| Movimiento | Gramática de resortes de un sistema de tramoya: giro de la polea de la viga, descenso en perspectiva de la escena suspendida, ascenso escalonado de los contrapesos, tensión vertical del titular, respiración del látex sujeto por una cuerda, torsión del laminado, efecto rápido de palanca al pasar el cursor y compresión al presionar, asentamiento de avisos, tensión del hilo de guardado y sello de éxito. Escenario expresivo de 760ms, desfase de 65ms y controles de 180ms; natural de 460/40/160; sutil de 240/20/120. Los desplazamientos finitos mantienen el texto totalmente opaco. Movimiento reducido, still=1 y Quieto eliminan los desplazamientos y los bucles ambientales; el contenido oculto o fuera de pantalla se pausa. |

## 5. Tokens, componentes reales y límites de origen

Lee `src/app/globals.css` de ambos repositorios y el límite existente `guardado-escena.ts`. Los roles existentes de Pictures `--fondo`, `--superficie`, `--superficie-2`, `--texto`, `--texto-suave`, `--acento`, `--acento-hover`, `--sobre-acento` y `--borde` se asignan a los roles de fondo/tarjeta/atenuado/primer plano/principal/entrada del kit. El propietario solicitó explícitamente mundos cromáticos nuevos, así que los valores anteriores son una **propuesta**, no un reemplazo de los tokens de marca aprobado para producción. El texto de error, éxito y advertencia conserva su semántica y nombre en ambos temas. Los bordes de los controles de los selectores nativos y las casillas sin marcar se midieron.

Componentes: `shadcn:button` predeterminado/con contorno/deshabilitado (`@/components/ui/button`), `shadcn:input` predeterminado/no válido/deshabilitado (`@/components/ui/input`), `shadcn:skeleton` de carga (`@/components/ui/skeleton`), `shadcn:checkbox` mejorado con Animate UI, sin marcar/marcado/deshabilitado (`@/components/ui/checkbox`), `shadcn:dialog` para nombre/importación (`@/components/ui/dialog`) y `shadcn:alert-dialog` para confirmar salida/carga (`@/components/ui/alert-dialog`). Se inspeccionaron las exportaciones antes de usarlas. La escena, la viga y los contrapesos personalizados usan SVG/CSS y Motion; no se presentan como componentes de la biblioteca. `mountMockup`/`useMockup` y `useMotionProfile` provienen del entorno de ejecución instalado. No se descargaron paquetes ni recursos; no hicieron falta fragmentos alternativos de HTML para obtener el resultado completo.

Las fuentes se incrustaron desde las versiones locales de DejaVu Serif Condensed Bold, Liberation Sans regular/negrita y Liberation Mono regular. No hay fuentes, imágenes ni solicitudes HTTP de ejecución externas. Para que el verificador estático de tokens inspeccione exactamente los colores de la propuesta renderizada, el HTML generado también refleja la hoja de estilos de la entrada en `style[data-direction-source=bambalinas]`; se genera desde el mismo literal `css`, no desde una hoja de estilos diseñada por separado.

## 6. Navegación, vistas y jerarquía adaptable

Los selectores nativos de planificación conservan `view`, `state`, `scene`, `theme` y `motion`, con las etiquetas Vista, Estado, Diálogo, Tema y Movimiento. Se conserva la etiqueta visible **Mockup**. La selección de español/inglés del producto muestra etiquetas más largas; parte del texto explicativo permanece en español porque SP-4 planifica centralizar las cadenas en español antes de los subplanes posteriores de localización. Esta exploración no demuestra que la localización al inglés esté completa.

Vistas:
1. `mine`: colección de la cuenta actual, búsqueda global por nombre, ilustración de la escena seleccionada, Abrir explícito en Taller, conteo de elementos cargados, acción para la página siguiente y acceso reversible a la importación.
2. `staff`: colección de todas las cuentas autorizadas, selectores de colección y propietario, identidad del propietario del proyecto, proyecto seleccionado y original ajeno en modo de solo lectura. Mine sigue limitada a la cuenta ilustrativa activa.
3. `workshop`: nombre del proyecto, propietario y revisión, hilo de guardado visible, primer guardado con nombre o Guardar ahora, Guardar copia, alcance de escena completa y una edición de demostración identificada. Los originales ajenos ocultan las acciones de edición y solo permiten crear una copia a una cuenta con acceso a Taller.
4. `reading`: ruta independiente de solo lectura para un rol con `proyectos.ver_todos` pero sin `taller.usar`. No se muestran acciones para copiar ni herramientas de edición. Se explica la limitación del rol.

Puntos de quiebre: **360–767px** una columna, margen exterior de 20px, escena seleccionada seguida de sus detalles y luego el directorio de proyectos; los pasos ocupan todo el ancho. **768–1099px** dos columnas con margen exterior y separación de 24px; la acción de la escena pasa debajo de sus detalles. **1100px+** margen exterior de 40px, separación entre escenarios de 40px y división 57/43. Taller tiene una ficha de guardado de 290px, reducida a 250px en tablet y apilada debajo de la escena en el teléfono. Los diálogos ocupan como máximo el área visible menos 40px, tienen relleno amplio de 26–30px, acciones que se ajustan al espacio y desbordamiento vertical. El pie comparte el borde izquierdo de la página. Los nombres se ajustan a varias líneas; no se requiere desplazamiento horizontal de la página.

## 7. Requisitos de comportamiento preservados

- El primer guardado solicita un nombre explícitamente; los cambios posteriores ponen en cola el guardado automático y muestran Guardar ahora. Los estados modificado, guardando y guardado confirmado son distintos. Solo se puede confirmar la generación de edición enviada; las ediciones posteriores permanecen sin guardar. En producción, las solicitudes deben serializarse y vincularse con la identidad de cuenta/proyecto.
- Los nombres y la escena **completa** deben estar disponibles en distintos navegadores, incluidas la sala, el entorno, los materiales y las relaciones entre nodos. La conversación con IA y las imágenes generadas permanecen en el navegador local; la interfaz hace visible ese alcance. Al abrir otro proyecto, se restablece la identidad del historial de deshacer/conversación en vez de asociar el historial de otro proyecto.
- La búsqueda de listas y el filtrado autorizado por propietario abarcan toda la colección del servidor **antes de la paginación**. La implementación de producción debe agrupar las solicitudes por clave con antirrebote, restablecer el cursor y los resultados al cambiar los filtros, ignorar respuestas obsoletas y conservar las filas cargadas después de errores al solicitar la página siguiente. El prototipo solo filtra su pequeña colección ilustrativa en memoria y no afirma verificar la paginación del servidor ni la autorización. Los conteos muestran los elementos cargados, sin inventar totales.
- Un conflicto detiene el guardado automático, conserva el trabajo local no enviado y ofrece **crear una copia propia** o **cargar la versión guardada**. La carga requiere un AlertDialog aparte que explica el reemplazo y la conservación del borrador de recuperación, y ofrece descargar una ilustración del borrador. No se incorpora ninguna combinación ni sobrescritura silenciosa.
- Los originales ajenos nunca otorgan derechos de edición. La lectura no transfiere la propiedad. Solo una cuenta de personal con acceso a Taller puede crear una copia en su propia cuenta. No se agrega ninguna interfaz para eliminar, transferir ni consultar el historial de versiones.
- Los errores de conexión, red, autenticación o permisos conservan el trabajo de recuperación de la misma cuenta y ofrecen una opción para recuperarlo sin afirmar que se guardó. Al salir con trabajo pendiente, se ofrecen Guardar y salir, Conservar el borrador local y salir o Permanecer. Las rutas de guardado no disponibles aparecen deshabilitadas. Al cambiar de cuenta o perder la sesión, se ocultan la escena y los resultados anteriores; nunca se enumeran borradores de otra cuenta.
- La importación se ofrece en la primera visita autenticada a Taller cuando hay datos heredados sin procesar, y puede volver a abrirse desde los proyectos después de «Ahora no». Indica la cuenta de destino, advierte sobre el origen en un dispositivo compartido y requiere marcar una casilla de consentimiento explícito. No hay ninguna carga antes del consentimiento. Los bytes originales sin procesar permanecen intactos después de aceptar, rechazar o fallar. Los datos no compatibles muestran una explicación y permiten descargar el original sin procesar. Los reintentos o envíos duplicados usan la cuenta y el hash de origen sin procesar para recuperar un solo proyecto; no se establece ninguna asociación automática para una cuenta nueva. Las cuentas sin acceso a Taller conservan los datos hasta que se les otorgue el permiso.

Todos los datos de prueba y las descargas JSON se identifican como contenido de demostración. La persistencia, la conservación de bytes sin procesar, las comprobaciones de revisión, la protección del mismo origen, el aislamiento de borradores, las condiciones de carrera en la base de datos, la autenticación y la idempotencia de reintentos requieren la implementación y las pruebas reales de T4.2–T4.7. La maqueta no accede a localStorage ni a datos del usuario.

## 8. Estados y diálogos accesibles

Los 23 estados están disponibles en el selector nativo Estado: normal, loading, empty, no-results, error, unnamed, dirty, saving, saved, offline, save-error, conflict, foreign, denied, expired, account-switch, page-loading, page-error, partial, validation, import-invalid, import-success y disabled.

El estado de carga usa un esqueleto de escena y tres esqueletos para los nombres. El estado vacío invita a crear el primer proyecto; si no hay coincidencias, ofrece borrar la búsqueda. El error inicial reemplaza la colección con una opción para reintentar, mientras que el error al solicitar la página siguiente conserva las filas cargadas. Los estados pendiente/guardando/guardado tienen nombres; los errores de conexión o guardado ofrecen reintentar; los conflictos deshabilitan el guardado normal. La expiración o el cambio de cuenta eliminan el contexto de identidad visible; el acceso denegado no muestra metadatos del proyecto. Los datos no compatibles en una importación muestran la descarga de demostración del original sin procesar; tras el éxito, se conserva el original y se ofrece el proyecto importado. La validación se muestra en el diálogo de nombre; el estado deshabilitado se demuestra en los controles de guardado y edición de Taller.

Los cinco diálogos se seleccionan por separado mediante Diálogo: `save`, `copy`, `import`, `replace`, `leave`; la opción vacía cierra todos. El comportamiento modal de Base UI proporciona contención del foco y un fondo inerte. Escape cierra los diálogos normales; siempre hay una opción explícita para cancelar. El foco vuelve al elemento que abrió el diálogo. Las acciones de reemplazo y salida usan AlertDialog. Las operaciones en curso deshabilitan temporalmente las acciones duplicadas y muestran un estado de guardado con nombre.

## 9. Objetivos de movimiento y accesibilidad

El objetivo es WCAG 2.2 AA; los resultados automatizados son evidencia acotada, no un certificado de conformidad. El contraste del texto apunta a 4.5:1; los bordes de controles y el foco, a 3:1. Las acciones tienen una altura mínima de 44px; las etiquetas están asociadas, la selección usa `aria-pressed`, los errores usan alertas y la confirmación de guardado usa un estado dinámico. Las teclas de flecha permiten operar los selectores nativos; cada operación espacial es un botón. No se requiere ninguna interacción que dependa exclusivamente de arrastrar. El movimiento mantiene el texto opaco sobre planos opacos; los degradados solo se usan como materiales decorativos de globos.

Se implementan al menos doce comportamientos CSS independientes: descenso de la escena suspendida, asentamiento de contrapesos, tensión del título, rotación de la polea, respiración del látex, torsión del laminado, asentamiento de avisos, sello de guardado, ajuste del hilo de guardado, hilo de guardado activo, balanceo en estado vacío y respiración del esqueleto. El giro rápido de la palanca/flecha al pasar el cursor y la compresión al presionar agregan retroalimentación rápida. El movimiento usa el resorte real del perfil del entorno de ejecución cuando se reemplaza la escena, y tiempos CSS específicos del perfil para la coreografía. `prefers-reduced-motion`, `?still=1` y Quieto eliminan la animación y la transición, conservando todas las vistas y acciones; al ocultar la pestaña o poner la página fuera de pantalla, los efectos se pausan.

## 10. Criterios de aceptación observables

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 1100px+ | normal | La escena seleccionada y el directorio escalonado de proyectos con nombre cuelgan debajo de una sola viga de ancho completo. |
| B-AC-02 | 360–767px | normal | La escena, los detalles, el directorio y la recuperación de importación forman una columna dentro de márgenes de página de 20px. |
| B-AC-03 | all | normal | Se puede llegar al campo de búsqueda, a cada nombre de proyecto y a la acción explícita Abrir con el teclado, con un indicador de foco visible de 3px. |
| B-AC-04 | all | unnamed | Editar la escena de demostración no evita el primer guardado explícito con nombre. |
| B-AC-05 | all | saving/saved | El estado guardando se distingue visiblemente del guardado confirmado; la acción de guardado se deshabilita temporalmente. |
| B-AC-06 | all | conflict | Guardar ahora está deshabilitado; se muestran las opciones para crear una copia propia y cargar la versión guardada; la carga abre una confirmación. |
| B-AC-07 | all | page-error | Los proyectos cargados permanecen visibles con una acción para reintentar la solicitud de la página siguiente. |
| B-AC-08 | all | reading | El lector sin acceso a Taller no dispone de ninguna acción de guardado, copia ni edición. |
| B-AC-09 | all | import | El destino con nombre y la advertencia sobre dispositivos compartidos preceden a una casilla de consentimiento sin marcar; Importar empieza deshabilitado. |
| B-AC-10 | all | import-invalid | Aparecen una explicación de recuperación y una acción para descargar el original, sin reemplazar la escena de origen. |
| B-AC-11 | all | expired/denied | El contenido de la escena o colección anterior no queda expuesto. |
| B-AC-12 | 1280/390px, ambos temas | reduced/Quieto | Todo el contenido sigue siendo utilizable y no hay animaciones en curso. |
| B-AC-13 | all | normal | La interfaz de planificación conserva Mockup y todos los ejes nativos; no se realizan solicitudes de recursos HTTP(S). |

## 11. Verificación y límites declarados con honestidad

Ejecución final del kit sobre el HTML entregado: `audit: proyectos@v1.r10.dir-b.html — 448 renders (448 combinations planned), 11304 text measurements, 1406 focus stops`.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

`contrast: 158 pairs checked in light and dark, all pass`.

Las comprobaciones específicas en navegador pasaron en la compilación final: selección y apertura de proyectos con nombre coincidente; primer guardado explícito y validación del nombre; creación desde el estado vacío; nombre accesible del consentimiento de importación, control de acceso según esté sin marcar o marcado, Escape y retorno del foco; detención del guardado ante conflictos y confirmación del reemplazo; filtro por propietario y distinción entre solo lectura y copia de proyectos ajenos; restricciones de lectura para quienes no tienen acceso a Taller; sin desbordamiento en 360/390/768/1024/1280 en ambos temas; movimiento reducido del sistema operativo, Quieto y `still=1`; pausa fuera de pantalla; sin errores de página ni solicitudes HTTP(S). Se observaron seis comportamientos expresivos simultáneos en CSS (`title-tension`, `pulley-turn`, `fly-in`, `latex-breathe`, `foil-turn`, `counterweight`). Los selectores definen y alcanzan otros efectos de estado. El cuadro de diálogo de importación también pasó las pruebas renderizadas de contraste, contenido no textual, alineación, relleno y desbordamiento a 390px en ambos temas.

Las comprobaciones específicas detectaron inicialmente una aserción de salida del cuadro de diálogo prematura (la biblioteca conserva brevemente el DOM de salida) y un resorte residual real de Motion al cambiar a Quieto. Ahora la prueba espera a que el cuadro de diálogo se elimine realmente; la escena reducida vuelve a montarse en su pose final sin reiniciar la selección del elemento principal, lo que detiene de inmediato el resorte residual. El control de consentimiento visible tiene un nombre explícito. También se comprobó que la acción del estado vacío cree un proyecto sin nombre.

La primera auditoría completa renderizó 448 combinaciones y encontró un problema de relleno en la etiqueta explicativa de solo lectura (10px de margen lateral en lugar de los 12px requeridos). Se cambió a 12px. Se inspeccionaron visualmente capturas a 1280 y 390 en ambos temas, además del conflicto de escritorio y el cuadro de diálogo de importación en teléfono con tema oscuro; las capturas se transmitieron en memoria y no se escribieron archivos de evidencia sin asignar. Las comprobaciones específicas anteriores cubrieron el reajuste de tablet y 360px, así como las interacciones. Este mockup de diseño no verifica el comportamiento completo del servidor, la seguridad, la importación sin pérdida, la persistencia entre navegadores ni la localización completa al inglés.

`compare_directions.py` se ejecutó sin conexión contra r10 A/B/C, con código de salida 0, `ok: true`, `evidence_ok: true` y sin evidencia faltante. Similitud de diseño de B frente a A: 0.007; de B frente a C: 0.050. La tipografía, la navegación y el movimiento son distintos en ambas comparaciones. Estas mediciones complementan el juicio visual y no eligen una dirección por el propietario.

## 12. Preguntas abiertas, supuestos e impacto

P: Propietario — ¿La colección debería mostrar, al seleccionar un proyecto, una vista previa de escena autorizada y renderizada en el cliente, o reservar la vista previa 3D real para abrir un proyecto? Esta exploración usa una ilustración con etiqueta explícita y supone que no se agrega una API para almacenar miniaturas.
P: Propietario — Si se elige esta dirección, ¿pueden la paleta bermellón/acero y la tipografía serif vertical reemplazar la paleta morada de trabajo actual, o debería la versión final conservar parte de los tokens de marca existentes?

Se preserva el comportamiento confirmado en la ronda 9 y en la fuente de comportamiento compartida; no se vuelve a discutir. La nueva composición, jerarquía y navegación requerirían adaptaciones en T4.4/T4.5 y una revisión renderizada en T4.8; la compatibilidad con cualquier implementación futura queda **sin determinar** hasta que el propietario elija una opción y se finalice el contrato canónico. No se redirige ningún consumidor existente. La elección del propietario y el contrato canónico final siguen pendientes de aprobación; no son trabajo incompleto de esta exploración.

SHA-256 del HTML entregado: `1c627ccb63ff24eb73f9ee6c85a559c9c0c01f57632aae7eeafb017b08587234`.
