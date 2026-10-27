---
id: proyectos
version: 1
status: draft
artifact: independent-exploration
revision: r10
direction: c
name: Estuche
date: 2026-10-27
---

# Estuche — dirección C

## 1. Identidad y trazabilidad

Exploración de planificación para SP-4, Proyectos guardados, que cubre R6 y R7. Esta dirección no está aprobada para el futuro `proyectos@v1`; no es el contrato canónico ni una autorización de implementación. El propietario y Planner aún están conversando sobre el plan. Solo se escriben los seis artefactos asignados y específicos de la revisión, además del resultado de delegación requerido.

Fuentes consultadas: SPEC.md, PLAN.md, PLAN.json actuales y `proyectos@v1.r10.behavior.md` (digest de SP-4 `749be52ec4afc053`). Prefijos SHA-256 de las fuentes inspeccionadas: SPEC `65b1e5ecc06f20d9`; PLAN.md `cc7e53f2abf3c23c`; PLAN.json `7a2c833a7e711508`; comportamiento compartido `378c0aa4a41164c6`. Se consultaron los archivos AGENTS.md, globals.css y el guardador existente de escenas del navegador en ambos repositorios del espacio de trabajo, t12 y asesor. No se editó ninguno de los repositorios.

## 2. Propósito, concepto y elemento memorable

La pregunta es: **¿qué montaje guardado quiero retomar?** Quienes tienen acceso a Taller guardan y continúan sus propias escenas completas. El personal con `proyectos.ver_todos` consulta proyectos autorizados; para hacer una copia también necesita `taller.usar`. Nadie edita el original de otra persona.

Estuche presenta la colección como un estuche acolchado de viaje para decoradores. Los proyectos van en bolsillos suaves, con esquinas redondeadas y costuras. El material azul piscina sostiene un título inflado con letras azul tinta; el cian brillante es el herraje de la cremallera, con un cian más profundo para las acciones del tema claro que necesitan ser accesibles. El látex rosa y el foil plateado aparecen dentro del montaje esquemático y conectan el estuche con el mundo de trabajo de Sempertex.

La combinación final de tipografía redondeada comparte una identidad de materiales suaves con las cuentas C, pero cambia deliberadamente la paleta, la composición, la navegación y el movimiento guiado por la cremallera.

**Elemento memorable:** la cremallera se extiende a lo ancho de la página, el tirador encaja en su lugar y tres bolsillos de proyectos aparecen con una respuesta de compresión/expansión del material a intervalos de 70ms. Se puede arrastrar el tirador con un resorte o moverlo con Left/Right/Home. Es una muestra decorativa de material; nunca guarda, selecciona ni elimina un proyecto. Cada acción esencial tiene un botón de texto explícito.

## 3. Dos miniaturas, registro visual y jerarquía

Ambos HTML de miniatura se escribieron y renderizaron antes de la entrada TSX completa:

- **Candidato 1, elegido:** `proyectos@v1.r10.dir-c.html.candidate-1.html`, un estuche de viaje abierto con tres bolsillos de proyecto escalonados. Muestra varios proyectos con nombre y sus acciones para retomarlos de una vez.
- **Candidato 2, descartado:** `proyectos@v1.r10.dir-c.html.candidate-2.html`, un índice estrecho de proyectos frente a una gran vista previa. Dedica demasiado espacio a un solo montaje y repite una composición conocida de índice/plano de trabajo del registro.

Se leyeron las notas de cuentas r10 A/B/C y Taller r9 A/B/C. Esta exploración evita el registro de permisos de cuentas, la entrada inflable, el riel de identidad izquierdo y las bandas de cuentas de Nudos, el cinturón inferior de herramientas y las cavidades moldeadas para objetos de Taller, así como sus composiciones de dibujo técnico o escena suspendida. Se mantienen compartidos los nombres Pictures/Sempertex, la marca de círculos enlazados, el vocabulario de proyectos, los roles semánticos de tokens, el uso ES/EN y las protecciones explícitas de propiedad. La nueva paleta y la combinación tipográfica son propuestas locales de esta exploración. Los bocetos iniciales de las miniaturas usaron herrajes naranjas provisionales y una serif del sistema; una revisión final del registro de fuentes subyacentes y paletas encontró que los diseños A/B vecinos también usan familias serif/naranjas, así que la dirección completa se define deliberadamente con Mplus redondeada, azul piscina, cian y rosa. Las miniaturas siguen siendo la evidencia original de composición.

La jerarquía de la colección es: título/acción, cremallera de material, búsqueda y alcance autorizado, cantidad cargada, bolsillos de proyectos con nombre, recuperación de la página siguiente, recuperación de escenas del navegador y nota al pie. La jerarquía del editor es: nombre del proyecto, avisos pertinentes de recuperación/importación, estado del guardado, esquema amplio y nota sin recuadro sobre propiedad y persistencia. No hay mosaicos KPI, gráficos de estado ni resúmenes de dashboard genéricos inventados.

## 4. Ocho ejes y sistema visual

| Eje | Diseño observable | Evidencia |
|---|---|---|
| Concepto | El estuche de viaje de un decorador protege cada montaje con nombre en un bolsillo cosido. | `.pocket`, `.zip-track`, `.zip-pull` |
| Diseño | Tres bolsillos escalonados en escritorio, con el primero ligeramente más ancho; el editor divide la escena amplia y una nota estrecha sin recuadro. | `.pocket-wall`, `.project-plane` |
| Navegación | Continuación directa por proyecto, regreso a proyectos y recuperación de escenas del navegador; el personal ve los controles integrados en el flujo Mine/Everyone y un filtro por propietario. Sin barra lateral persistente ni dock inferior fijo. | `.pocket .actions`, `.more`, `.scope-nav` |
| Tipografía | Mplus 1c ExtraBold Rounded incrustada, con título de 44–78px y nombres de proyecto de 25px, combinada con FreeSans incrustada para texto de trabajo de 14–16px. | `.display`, `.pocket h2` |
| Densidad/forma | Márgenes de escritorio de 44px, relleno de bolsillos de 27px, lóbulos superiores de 60px y esquinas inferiores de 27px; una costura discontinua interior define el material. El teléfono tiene márgenes de 20px y un bolsillo por fila. | `.estuche`, `.pocket:before` |
| Componentes | Controles reales de shadcn, cuadros de diálogo de Animate UI, bolsillo cosido personalizado, esquemas SVG integrados y control deslizante de cremallera con Motion. | `[data-slot=button]`, `[data-slot=input]`, `.dialog-box`, `.scene-art` |
| Color | Azul piscina y azul tinta, herrajes cian brillante, acciones cian profundo, látex rosa y foil azul plateado. El tema oscuro usa superficies azul agua sólidas y acciones cian brillante. | `.estuche`, `.zip-pull`, `.scene-art` |
| Movimiento | Compresión, encaje elástico y aparición escalonada de bolsillos; desplazamiento de cremallera, inflado de globos, oscilación del foil, respuesta de estampado, liberación de presión y respuestas táctiles al presionar. | `.pocket`, `.display`, `.zip-track`, `.zip-pull`, `.balloon-group`, `.foil-shine` |

**Por qué esta dirección no es la predeterminada:** la colección tiene un ritmo deliberadamente escalonado de materiales y bordes físicos cosidos, en vez de tarjetas de dashboard uniformes. Las letras redondeadas infladas y la base azul piscina del estuche de herramientas corresponden con la cremallera, el foil y el látex. No hereda el morado de Pictures, el crema/terracota, un degradado morado ni el verde ácido sobre negro. El cian es un herraje físico y un color deliberado para las acciones, no un acento aplicado a cada superficie.

| Token existente de Pictures | Función en el kit | Propuesta clara / oscura |
|---|---|---|
| `--fondo` | fondo | `#c9e7f3` / `#102d40` |
| `--superficie` | tarjeta, menú emergente | `#f3fbff` / `#183e55` |
| `--texto` | primeros planos | `#103247` / `#f3fbff` |
| `--texto-suave` | primer plano atenuado | `#33586b` / `#b4d6e9` |
| `--acento`, `--sobre-acento` | par primario | `#07577a`, blanco / `#82d9ff`, `#05283d` |
| `--borde` | borde | `#51869f` / `#77abc5` |
| Borde de control más marcado propuesto | entrada | `#36687f` / `#8abbd2` |
| Foco | anillo | `#07577a` / `#82d9ff` |
| Responsabilidades semánticas existentes | éxito / advertencia / destructivo | `#175840` / `#704209` / `#a51c36`; oscuro `#9cddbd` / `#f5d194` / `#ffafc0` |

Estos valores reasignan explícitamente las responsabilidades existentes del proyecto; no describen la paleta actual de producción. Los controles opcionales de función de muestra e idioma son herramientas del mockup dentro de la página, no una propuesta de mecanismo de cambio de cuenta para el producto.

Inventario real de componentes: `shadcn:button default/outline/ghost/disabled` de `@/components/ui/button`; `shadcn:input default/invalid/disabled` de `@/components/ui/input`; `shadcn:skeleton loading` de `@/components/ui/skeleton`. El adaptador de Button conserva el componente real y agrega `data-variant` para cambiar su estilo. Los nombres modales usan `@animate-ui/react/primitives/base-ui/dialog`; las decisiones potencialmente disruptivas de salir/cargar usan su equivalente `alert-dialog`. Sus Root, Portal, Backdrop, Popup, Title y Description reales proveen semántica modal, hacen inerte el fondo y contienen el foco. `motion/react`, `@kit/motion` y `@kit/mockup` proveen el resorte, los perfiles, mountMockup y useMockup. Los recursos personalizados son SVG/CSS integrados; no se necesitó una alternativa basada en snippets.

Mplus 1c ExtraBold Rounded se obtuvo como subconjunto del TTF local instalado en memoria y se incrustó como URI de datos. Las familias tipográficas subyacentes reales se contrastaron con las vecinas A/B; C no reutiliza DejaVu Serif Condensed para títulos. FreeSans existente se obtuvo como subconjunto en memoria y se incrustó como URI de datos OpenType porque este generador no carga archivos `.otf`; no se creó ni descargó ningún archivo de fuentes o paquete. No se pudo generar WOFF2 en memoria sin Brotli; la codificación OpenType de la fuente instalada funciona sin conexión. Después de la generación también se inserta el CSS exacto escrito en un bloque de estilo del encabezado para que el comprobador estático de contraste lea los mismos tokens propuestos que el entorno de ejecución.

## 5. Modelo de navegación e interacción

El producto usa acciones etiquetadas directas, sin exigir la cremallera ni gestos. Cada bolsillo abre su propio proyecto. Las escenas propias editables corresponden a `/3d?proyecto=<uuid>`; la consulta del personal corresponde a la vista autorizada de solo lectura `/proyectos/[id]`. Quien no tiene acceso a Taller no puede entrar en su editor ni crear una copia. Regresar a proyectos corresponde a `/proyectos`.

La barra nativa de planificación conserva **Mockup**, Vista `view`, Estado `state`, Diálogo `scene`, Tema `theme` y Movimiento `motion`. ES/EN es `language`; las funciones de muestra son `actor`. Ambos son selectores nativos con nombres accesibles. El perfil de movimiento inicial es expresivo. El personal puede seleccionar Everyone y luego filtrar por propietario; los usuarios comunes solo tienen su propia colección. Los filtros reinician la paginación. La colección ilustrativa filtra toda su fixture antes de dividirla en páginas; no demuestra una consulta de producción al servidor.

Escape/cancelar en un modal lo cierra y devuelve el foco al control que lo originó. Los errores de nombre conservan el texto ingresado. Si hay trabajo pendiente, la navegación ofrece Guardar antes de salir, Conservar borrador y salir, o Permanecer aquí. Al elegir Guardar, se completa el guardado en la escena actual; luego el usuario puede salir. No hay una acción predeterminada para descartar ni sobrescribir.

## 6. Flujos de comportamiento conservados

1. **Primer guardado:** Proyecto nuevo → Taller sin nombre → Guardar proyecto → diálogo de nombre → nombre no vacío → guardado explícito → revisión 1 y confirmación de guardado. Las ediciones posteriores muestran pendiente → guardando → guardado; Guardar ahora sigue disponible cuando hay conexión y no hay conflictos.
2. **Continuar:** buscar por nombre del proyecto en toda la colección autorizada → cargar más si hace falta → Continuar proyecto. El alcance persistido en el servidor incluye el nombre completo y la escena completa. La conversación con IA y las imágenes generadas permanecen locales; la identidad de la conversación de la escena no debe asociarse silenciosamente a otro proyecto.
3. **Conflicto:** una respuesta de escritura obsoleta pausa el guardado automático y conserva el trabajo local. La comparación muestra la revisión base local y la revisión guardada más reciente. Guardar mi trabajo como copia abre la asignación de nombre y crea un proyecto propio. Cargar la versión guardada requiere un AlertDialog que explique el reemplazo de la escena visible y la conservación de un borrador local. Después de un conflicto no se realiza ningún reintento ni sobrescritura automática.
4. **Lectura/copia del personal:** filtro autorizado Todos/propietario → Ver proyecto → original de solo lectura → Crear una copia en mi cuenta solo con acceso a Taller. El original permanece sin cambios. Un rol personalizado de solo lectura muestra la explicación y una acción de copia deshabilitada.
5. **Importación heredada:** la muestra autenticada de Taller ofrece un montaje anterior del navegador para revisarlo antes de cualquier carga. Revisar → vista de importación específica que indica la cuenta de destino de Ana y advierte sobre los dispositivos compartidos → Importar a mi cuenta explícitamente. Ahora no es reversible desde la colección. Si se interrumpe la respuesta, el reintento debe devolver ese mismo proyecto. Si los datos no son compatibles, se ofrece la descarga del original en vez de reemplazarlo por una escena vacía.
6. **Recuperación:** en el producto implementado, los borradores sin conexión o pendientes siguen vinculados a la cuenta y al proyecto. La maqueta muestra un aviso de recuperación de borrador local después de Conservar borrador y salir. Si se pierde la autenticación, se cierra la vista privada; el borrador solo puede restaurarse al volver a la misma cuenta. Al cambiar de cuenta se deben borrar las cachés de escena y consulta, e ignorar las respuestas de la cuenta anterior.

Los requisitos de la fuente de comportamiento compartida para el espacio de nombres de producción del último flujo, la arbitraje de revisiones, el rechazo de respuestas obsoletas, el debounce serializado de 500 ms, el comprobante de bytes sin procesar heredados y la idempotencia de importación siguen siendo precisos. Esta exploración visual no los reemplaza por una implementación simulada en el cliente.

## 7. Especificaciones de vistas

| Vista nativa | Estructura y propósito observable |
|---|---|
| `lista` | Búsqueda, alcance propio/autorizado, cantidad cargada, grupos escalonados con nombre y hora/revisión de guardado, continuación explícita, conservación de las filas ante errores de la página siguiente, reintento/carga adicional y recuperación de la escena del navegador. Ocho casos de prueba realistas incluyen un nombre propio más allá de las primeras tres filas y dos propietarios externos. |
| `taller` | Oferta de escena del navegador para la primera visita, proyecto con nombre, franja de guardado visible con Guardar ahora, esquema ilustrativo, simulación de edición y nota sobre propiedad/persistencia. La recuperación por estado pendiente/sin conexión/conflicto está junto al espacio de trabajo. Las herramientas del Taller real quedan fuera de este alcance de diseño; este esquema no las elimina. |
| `ajeno` | Nombre del proyecto, aviso explícito de solo lectura, esquema y nota sobre propietario/revisión. Crear una copia propia depende del acceso a Taller. Los errores indican un fallo de lectura, no de escritura; la consulta sin conexión advierte que los datos podrían estar desactualizados. |
| `importar` | Vista previa de la fuente del navegador, explicación sobre dispositivos compartidos, cuenta de destino, nombre, importación explícita, opción reversible Ahora no, descarga de la muestra original y aviso de conservación. La validación deja intacto el original. Tras importar correctamente, se puede abrir el proyecto importado. |

Los diálogos son `nombre` (primer guardado o copia propia), `salir` (trabajo pendiente) y `servidor` (reemplazar la escena visible por la versión guardada). Cada escena puede abrirse de forma independiente desde el selector nativo y desde la acción relacionada del producto. Los nombres, las fechas, las revisiones, las miniaturas esquemáticas y todas las operaciones son ilustrativos. La descarga contiene un JSON de muestra etiquetado, nunca el localStorage real del usuario.

## 8. Estados y movimiento

| Estado | Tratamiento visible y recuperación |
|---|---|
| Normal | Grupos de proyecto con nombre, revisión almacenada y acciones explícitas. |
| Cargando | Skeletons estructurales o marcador de posición de la escena inicial; acciones de guardado/importación deshabilitadas. |
| Vacío/sin resultados | Grupo de ancho completo alineado con el encabezado/pie; crear el primer proyecto o borrar la búsqueda. La importación vacía vuelve a los proyectos. |
| Error recuperable | Error específico de la acción y Reintentar. Los fallos de solo lectura no implican escrituras. El reintento de importación explica la pérdida de la confirmación y la conservación del original. |
| Pendiente | Estado visible de cambios pendientes; no muestra la etiqueta de guardado. |
| Guardando/importando | Estado en curso con nombre y acciones repetidas de guardado/importación deshabilitadas. |
| Guardado/importado | Confirmación textual, revisión e información de conservación. |
| Sin conexión | Se indica explícitamente que el trabajo local no está en la cuenta; continuar trabajando/reintentar. La vista previa de solo lectura indica que los datos podrían estar desactualizados y deshabilita la copia. |
| Conflicto | Solo en Taller: cola pausada, comparación local/servidor, opción de copia o confirmación explícita de carga. |
| Validación | Diálogo de nombre no válido o importación no compatible; explicación textual, entrada/original conservados y descarga de la muestra sin procesar. |
| Acceso denegado | El contenido del proyecto privado se reemplaza por una explicación de acceso. |
| Sesión finalizada | Se cierra la vista privada, no se muestra metadato del proyecto y se explica la recuperación en la misma cuenta. |
| Error de página siguiente | La colección ya cargada se conserva; Reintentar página siguiente reemplaza a Cargar más. |

Los casos de prueba de guardado/conflicto no tienen efecto de escritura en vistas ajenas de solo lectura. La validación específica de importación no tiene significado en el editor dimensional. Los casos de prueba no relacionados conservan la vista base pertinente en lugar de inventar operaciones adicionales. Las acciones deshabilitadas indican el motivo cerca de ellas y conservan texto y bordes legibles.

La gramática del movimiento es un asentamiento elástico de material: `cubic-bezier(.16,1.3,.38,1)`. Las entradas expresivas de grupos, títulos y línea de cremallera duran 650 ms; las naturales, 430 ms; las sutiles, 250 ms. La respuesta repetida de botones dura 190/160/120 ms. El recorrido de la cremallera dura 850 ms, el asentamiento del globo 900 ms y el balanceo ambiental del papel metálico 5.8 s. Los comportamientos distintivos incluyen compresión del bolsillo, compresión del título, encaje de la cremallera, rotación/recorrido del tirador, inflado del globo, balanceo del papel metálico, asentamiento del alcance seleccionado, presión del sello de guardado, liberación de presión ante errores, asentamiento del anillo vacío, respiración del esqueleto, encaje al desplazarse y deformación al pasar el cursor/presionar. El perfil instalado de movimiento proporciona el resorte interrumpible de la cremallera y la temporización del diálogo.

El movimiento principal cambia transformaciones, nunca el color ni la opacidad del texto. El contenido de las ventanas emergentes permanece opaco. Las pestañas ocultas pausan las animaciones; IntersectionObserver pausa los bolsillos/escenas fuera de pantalla. `prefers-reduced-motion`, `?still=1` y Quieto eliminan las animaciones, el recorrido de las transiciones, los bucles ambientales y las transformaciones al pasar el cursor/presionar, conservando la información/acciones finales. Los cambios de cremallera con teclado se asientan de inmediato con movimiento reducido; ninguna operación esencial depende del movimiento.

## 9. Comportamiento adaptable

- **1101px y más:** márgenes exteriores de 44px; tres columnas de bolsillos `1.13fr 1fr 1fr`, escalonadas a 0/42/84px. El editor usa `1.7fr .8fr`; la importación, `1.1fr 1fr`.
- **761–1100px:** márgenes exteriores de 28px; dos columnas de bolsillos y desplazamiento de 42px en los bolsillos pares; los filtros se ajustan a dos columnas. El editor conserva la división `1.4fr 1fr`.
- **760px y menos:** márgenes exteriores de 20px; secuencia de bolsillos en una columna sin escalonamiento; título/acciones apilados; luego escena y nota de propiedad; vista previa y luego formulario de importación; los botones/acciones de diálogo se ajustan o ocupan todo el ancho. Las herramientas de la cabecera se ajustan; los selectores nativos mantienen límites de ancho. Ninguna navegación fija del producto tapa el contenido.

Las etiquetas en español e inglés se redistribuyen. En las muestras verificadas de 320/390/768/1280px no hay desplazamiento horizontal del documento. Los diálogos se limitan a la ventana gráfica y permiten desplazamiento interno. Las superficies vacías/de acceso comparten el eje y el ancho de la página, en lugar de introducir un formulario centrado sin relación.

## 10. Accesibilidad y límites de la evidencia

Objetivos: contraste de texto WCAG 2.2 AA de al menos 4.5:1; bordes de controles y foco de al menos 3:1; campos nativos etiquetados; encabezados, botones y regiones de estado/alerta semánticos; contención del foco del modal y retorno del foco; contorno de foco de 3px con desplazamiento de 4px. Los botones y campos funcionales tienen al menos 44px de alto. El objetivo decorativo de la cremallera mide 44×28px, por encima del mínimo de 24px del nivel AA, y permite operar con flechas/Home. No realiza ninguna acción esencial.

Las muestras iniciales de copia/lectura/importación no afirman que exista autorización de producción. No se realiza ningún inicio de sesión real, acceso a base de datos o escena remota, renderizado 3D, solicitud a IA ni escritura de almacenamiento. El dibujo de la escena completa es ilustrativo, no una miniatura persistida ni una prueba de geometría. Al actualizar se restablece el modelo simulado. La validación de fuentes/servicios de producción, la durabilidad de borradores, el aislamiento entre cuentas, las versiones atómicas, la gestión de carreras, la búsqueda en el servidor, la restauración entre navegadores y la idempotencia de importación requieren la implementación planificada y las comprobaciones del entorno de pruebas.

## 11. Criterios observables y verificación real

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| C-01 | 1280px | normal / colección | Tres bolsillos unidos tienen distintos desplazamientos verticales; cada uno muestra nombre, revisión guardada y acción de continuación. |
| C-02 | 390px | normal / colección | Los bolsillos se apilan sobre el eje de página de 20px sin desplazamiento horizontal. |
| C-03 | all | primer guardado | Un proyecto sin nombre solicita un nombre antes de mostrar una revisión guardada. |
| C-04 | all | pendiente/guardando | La franja indica el trabajo pendiente/en curso y no afirma que haya llegado a la cuenta. |
| C-05 | all | conflicto | Se muestran las revisiones local y del servidor con opciones de copiar/cargar; Guardar ahora está deshabilitado. |
| C-06 | all | ajeno/solo lectura | El original es de solo lectura; un rol sin acceso a Taller no puede crear una copia. |
| C-07 | all | importación | La cuenta de destino y la explicación sobre dispositivos compartidos aparecen antes de la acción explícita de importación. |
| C-08 | all | validación de importación | El error explica que el original se conserva y ofrece descargar la muestra original. |
| C-09 | all | error de página siguiente | Los proyectos ya cargados siguen visibles junto a Reintentar página siguiente. |
| C-10 | ambos temas | teclado/diálogo | El foco es visible; Escape cierra el diálogo y devuelve el foco a quien lo abrió. |
| C-11 | 320/768/1280px | inglés normal | Cada una de las cuatro vistas se redistribuye sin desplazamiento horizontal del documento. |
| C-12 | all | movimiento reducido/sin movimiento | Aparecen el mismo contenido y las mismas acciones finales, sin desplazamiento ambiental ni deformación al pasar el cursor. |

Registro de verificación:

- Cadena de herramientas sin conexión real: instalada/compilada, 96/96 entradas disponibles. Compilación final: paquete de 807KB, 2,133 archivos de origen; HTML independiente tras insertar el CSS escrito: 843,923 bytes (SHA-256 `a14962b528e8e173db71643f9e1e9c7cdd80eb61135fa6831405cc3f387a64cc`); sin alternativas de respaldo, instalación de paquetes ni recursos descargados. Todas las fuentes, hojas de estilo, secuencias de comandos e ilustraciones están insertadas.
- `contrast.py`: **contraste: se comprobaron 158 pares en los temas claro y oscuro; todos pasan**.
- La auditoría completa inicial encontró 12 hallazgos agrupados de alineación causados por un bolsillo vacío/de acceso estrecho y centrado. Ahora la superficie ocupa el mismo eje de página que el encabezado y el pie. Las siguientes auditorías completas pasaron. Un hallazgo posterior de alineación en teléfono, relacionado con la acción “Ahora no” sin marco de la oferta de importación, se corrigió dando superficies delineadas explícitas a ambas acciones de la oferta.
- Auditoría completa final del HTML final: **256/256 renderizados, 5,980 mediciones de texto y 774 paradas de foco** a 1280/390px en ambos temas.
- **RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- La prueba de interacción pasó nueve grupos: búsqueda más allá de la primera página/continuidad de entrada, primer guardado/revisión 1, pendiente→guardando→guardado, copia por conflicto, identidad ajena y restricciones de rol entre cambios de estado, Escape del modal/retorno del foco, importación explícita, cremallera con teclado y 24 combinaciones de vistas/temas/ventanas en inglés. Después del cambio final de fuente, también pasaron 32 combinaciones de vistas/temas/ventanas en inglés a 320/390/768/1280px. Sin errores de JavaScript ni solicitudes externas.
- También pasaron las comprobaciones específicas adicionales de la oferta de importación de primera visita, la opción reversible Ahora no, la recuperación posterior, el contenido opaco del modal, 13 animaciones expresivas predeterminadas activas, equivalencia en modo sin movimiento/reducción de movimiento del sistema y límites de teclado/posición más a la derecha de la cremallera a 320/390/768/1280px. Un arrastre largo del puntero a 320px permaneció dentro de la página durante y después del gesto.
- Se inspeccionaron capturas de pantalla en memoria de colección clara a 1280, colección oscura a 390, conflicto oscuro a 1280, importación no válida clara a 390 y lectura ajena oscura a 390. No se escribieron archivos de capturas fuera de la lista de resultados de la tarea.
- La comparación sin conexión de tres direcciones pasó con toda la evidencia medida y sin selectores faltantes. Similitud de diseño A/B: 0.007; A/C: 0.003; B/C: 0.050. La tipografía, la navegación y el movimiento difieren en todos los pares. La ejecución final tuvo `ok: true`, `evidence_ok: true`, sin evidencia faltante y código de salida 0; todos los selectores C pasaron. Prefijos SHA-256 de los HTML comparados: A `0d1dce11f823c34e`, B `1c627ccb63ff24eb`, C `a14962b528e8e173`. La diferencia numérica no aprueba el gusto: las variantes A/B siguen usando familias relacionadas de serifas y acciones cálidas; sus responsables deberían revisar esa coincidencia por separado. No se editó ningún archivo de las variantes.

## 12. Preguntas abiertas, impacto y aprobación

P: Si se selecciona Estuche, ¿David aprueba esta paleta azul piscina/cian/rosa y la combinación con tipografía de pantalla redondeada para Proyectos guardados, o debería la finalización adaptar la composición seleccionada a otra paleta compartida de Pictures?

P: ¿El diseño seleccionado debería usar vistas previas de proyectos derivadas de la escena dentro de los bolsillos, o un marcador de posición claramente esquemático hasta que haya miniaturas reales? R6/R7 requieren el nombre guardado y la escena completa, no un nuevo servicio de generación de miniaturas; esta exploración usa dibujos etiquetados y no agrega ese servicio.

Las decisiones confirmadas no se reabren: primer guardado explícito con nombre y luego guardado automático; la escena completa y el nombre se trasladan entre navegadores; la conversación y las imágenes de IA permanecen locales; el personal lee originales ajenos y crea copias propias solo con acceso a Taller; no hay sobrescritura concurrente silenciosa; la importación heredada requiere consentimiento y conserva el original.

Los posibles consumidores son SP-4, texto de diseño T4.1; tareas de interfaz T4.4/T4.5; banco de pruebas T4.6/T4.7; revisión visual T4.8 y auditoría T4.9. R6 corresponde a colección/editor/solo lectura/conflicto; R7 corresponde a oferta de primera visita/importación/validación/preservación. Esta exploración cambia la jerarquía, los componentes materiales, el énfasis de navegación, los tokens, la tipografía y el movimiento. La compatibilidad está **sin determinar hasta la selección del propietario y la finalización**. No se redirige a ningún consumidor del plan, no se modifica ningún contrato compartido/historial/registro de cambios y ningún subplan posterior está autorizado a consumir este borrador.
