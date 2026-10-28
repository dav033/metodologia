---
contract: proyectos@v1
status: draft
subplan: SP-4
exploration: r12.dir-b
name: Inspector lateral
created: 2026-10-28
---
# Inspector lateral — exploración B

## 1. Identidad y trazabilidad

**proyectos@v1 · draft · exploración r12/B, sin aprobación.** Esta nota acompaña a `proyectos@v1.r12.dir-b.tsx`, su HTML construido, las dos miniaturas y el JSON de ocho ejes. No sustituye el contrato canónico ni permite implementar una variante no elegida.

Alcance: SP-4, R6/R7, brief `proyectos@v1.r12.behavior.md`; contexto SPEC «Behavior — SP-3 and SP-4 (round 9 answered)» y SP-4 del PLAN vigente. Vistas afectadas: `/proyectos`, `/3d`, `/proyectos/[id]`. Consumidores futuros: T4.1, T4.4, T4.5 y T4.8; no se modifican plan, repositorios, contratos compartidos ni archivos de otra dirección.

Fuentes leídas: `globals.css`, `layout.tsx`, `Taller3D.tsx`, `Biblioteca.tsx`, `CabeceraApp.tsx` y `MenuApp.tsx` de los repositorios indicados; contratos y HTML hermanos `cuentas-admin@v1` y `planes@v1`; david-ui-kit/SKILL.md, directions.md, manifest.json, runtime y mockup-craft.md. La herramienta real estaba disponible: no se usó el fallback HTML ni se instalaron paquetes.

## 2. Propósito y usuarios

La persona encuentra un proyecto propio y lo continúa. El personal autorizado filtra por propietario y abre un original ajeno en solo lectura. Quien puede usar el Taller guarda una copia propia. La persona que llega con una escena heredada del navegador decide expresamente si importarla a su cuenta.

La pregunta principal de la lista es «¿qué proyecto voy a abrir?». La del inspector del Taller es «¿mis cambios están guardados y cómo continúo si no lo están?». Una selección, una posición y una acción explícita evitan confundir inspección con apertura.

## 3. Arquitectura y enfoque espacial

Se conserva el masthead Pictures/Sempertex, marca de anillo y punto, cuenta desplegable, idioma y regla horizontal de navegación de los contratos hermanos. El área cambiada es una hoja continua: filtros arriba, registros seleccionables a la izquierda e inspector a la derecha. La selección no abre el Taller; **Abrir proyecto** lo hace desde el inspector. No se añade un panel de vistas previas ni otro servicio de miniaturas.

En el Taller se mantiene la relación herramientas/lienzo/cabecera de escena. El nombre continúa editable en línea. El estado y las decisiones de recuperación se reúnen junto al lienzo; la escena permanece visible durante un conflicto. Se reproducen los nombres de las herramientas existentes como contexto; el SVG es una ilustración explícita de ejemplo, no el motor 3D ni un nuevo diseño de sus herramientas.

Miniatura elegida: **candidate-1**, lista lateral con inspector contiguo. Candidate-2 explora una franja de selección horizontal con detalle debajo. Se elige la primera porque ofrece espacio estable para nombres y propietarios, mantiene la paginación junto a los resultados y deja una única zona de decisiones. Las dos miniaturas se escribieron antes de construir la dirección completa y se conservan.

## 4. Sistema visual y ocho ejes

Se respetan Geist Sans/Geist Mono locales, sin nueva familia, paleta, material o identidad. La instrucción actual de conservar el sistema del producto y los hermanos gobierna sobre el feedback histórico que solicitaba paletas y familias distintas. La diferencia se concentra en estructura, selección y movimiento.

| Eje | Expresión presente en la maqueta |
|---|---|
| concept | Un proyecto seleccionado conserva su lugar en la lista y dispone de un inspector contiguo; en el Taller, ese espacio aloja guardado y recuperación sin sustituir la escena. |
| layout | Shell Pictures/Sempertex y navegación horizontal heredados. Hoja continua con filtros arriba, lista de selección de 1.65 fr e inspector de 1 fr. Taller con herramientas, lienzo e inspector; debajo de 1100px el inspector baja y en teléfono el estado crítico precede al lienzo. |
| navigation | Seleccionar una fila muestra sus datos; Abrir proyecto es una acción explícita en el inspector. Búsqueda y propietario preceden a la paginación. Proyectos/Taller permanecen en la misma regla horizontal; los diálogos guardan el contexto y devuelven el foco. |
| typography | Geist Sans y Geist Mono locales existentes. H1 24px, inspector 20px, nombres de fila 16px (15px teléfono), cuerpo 15px y metadatos 12–13px. La selección gana jerarquía en el inspector sin una nueva tipografía. |
| density | Tres filas de muestra por primera página, separadores suaves y 24px de padding vertical; 28px en filtros/inspector, 20px de padding de hoja en teléfono. Información secundaria reunida en un solo inspector, sin tarjetas por proyecto ni miniaturas. |
| components | Button, Input y Skeleton reales de shadcn; Dialog de Animate UI/Base UI; native select/details; botones de selección con aria-pressed y marcador Motion compartido. Paneles de radio 32px, campos 18px y acciones pill del shell hermano. |
| colour | Mismos tokens de globals.css y contratos hermanos en claro/oscuro: fondo/superficie/texto, acento únicamente en acción principal/foco, texto-tenue para bordes de controles y exito/aviso/error para estados reales. Sin nueva paleta. |
| motion | Registro espacial opuesto: hoja +12px vertical, filas −18px horizontal con 65ms de secuencia, inspector +26px, marcador scaleY y spring compartido, estado scale .6→1, punto de guardado desplazado tres ciclos, controles −2px/press .98 e icono +3px. Expresivo 560/180ms con cubic-bezier(.77,0,.175,1) y (.23,1,.32,1), natural 340/140 y sutil 180/100; reduced/still elimina movimiento. |

| Token Pictures | Rol kit | Claro / oscuro |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | selección/inspector neutros | #faf8fd / #1c1e26 |
| `--superficie-2` | secondary, muted, skeleton, disabled | #efe9f8 / #242733 |
| `--texto` | foreground | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted-foreground | #6b6178 / #9aa1ad |
| `--texto-tenue` | input/borde de control accesible heredado | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primary, ring / primary-foreground | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--borde`, `--borde-suave` | border, separadores decorativos | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--exito`, `--exito-suave` | estado confirmado | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | conflicto/sin guardar | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | error de guardado | #b23a45, #ffeaec / #ff979f, #43252a |
| `--taller-visor` | fondo del lienzo existente | #ebe7f1 / #1a1722 |

Se heredan los radios de los hermanos: hoja 32px, selección 24px, campo 18px, acciones pill. Padding de filtros e inspector: 28px escritorio, 20px hoja en teléfono y 24px diálogo. Sin sombras en filas o paneles; sombra solo en el desplegable flotante de cuenta. El violeta identifica la acción principal y el foco; la selección y la navegación son neutras. «Solo lectura» no usa color de éxito.

Componentes reales, denominación **source:id variant state**:

| Componente | Importación y uso |
|---|---|
| `shadcn:button default/outline/ghost normal/hover/focus/pressed/disabled` | `@/components/ui/button`; abrir, guardar, reintentar, cancelar y herramientas existentes de contexto |
| `shadcn:input text normal/focus/invalid` | `@/components/ui/input`; buscar, nombrar, renombrar |
| `shadcn:skeleton row loading` | `@/components/ui/skeleton`; filas aún no cargadas |
| `animate-ui:dialog popup open/closed/validation` | Export `Dialog` de `@/components/ui/dialog`, instalado sobre Animate UI/Base UI; foco contenido y fondo modal inerte |
| `native:select owner/language normal/focus` | Propietario autorizado e idioma español del fixture; los selectores externos del inspector son nativos |
| `native:details account open/closed` | Cuenta heredada, Escape y restauración de foco |
| `custom:project-record selection normal/selected` | Botón con `aria-pressed`, reglas, nombre y metadatos; marcador compartido `motion.span` |
| `custom:project-inspector contextual normal/read-only` | Nombre, propietario, estado y acción explícita de apertura |
| `custom:save-inspector contextual saved/saving/offline/error/conflict` | Explicación y recuperación junto al lienzo |

`mountMockup/useMockup` proceden de `@kit/mockup`; `useMotionProfile` de `@kit/motion`; el marcador usa `motion/react`. Fuentes WOFF2 existentes de t12 embebidas por el builder. No se cargan imágenes, fuentes, scripts o estilos desde red.

## 5. Navegación, interacción y movimiento

Proyectos/Taller son enlaces de ruta sobre la misma regla horizontal. El selector de vista expone Mis proyectos, Proyectos del personal autorizado, Taller propio y Taller ajeno. La selección de una fila conserva el foco en su botón; en teléfono desplaza el inspector a la vista sin animación bajo reducción. Abrir enfoca el título del destino. Buscar mantiene el foco en el campo. Cambiar búsqueda o propietario vuelve a página 1 y el inspector sigue una selección que existe entre los resultados.

Los diálogos conservan el contexto, permiten cancelar y restauran el foco al control de origen si sigue montado. El botón de copia ajena y las herramientas de edición quedan deshabilitados sin `taller.usar`. La cabecera mantiene el renombrado en línea: Enter confirma, Escape cancela. Guardar ahora permanece visible y se deshabilita durante envío o conflicto.

La gramática de movimiento es **registro espacial opuesto**, no una sucesión de fundidos: hoja desde +12px vertical, filas desde −18px horizontal, inspector desde +26px. Son desplazamientos de elementos presentes, sin texto que atraviese estados de baja opacidad. Hay ocho comportamientos observables: apertura de hoja; secuencia de filas; entrada del inspector; expansión del marcador; traslado compartido del marcador; asentamiento del punto de estado; recorrido del punto mientras guarda; hover/press e icono de acciones. El punto de envío usa tres ciclos finitos, no decoración ambiental permanente.

Expresivo: 560ms espacial, 180ms controles, 65ms de secuencia; natural 340/140/35ms; sutil 180/100/15ms. Curvas del producto `.77,0,.175,1` y `.23,1,.32,1`; marcador con spring del perfil (expresivo 220/16/0.9). Quieto, `?still=1` y `prefers-reduced-motion` eliminan desplazamiento, animaciones y transiciones conservando información y acciones. La pestaña oculta pausa CSS; no hay efectos ambientales infinitos fuera de pantalla.

## 6. Flujos

1. **Primer guardado:** Escena nueva → Sin guardar → Guardar proyecto/Guardar ahora → nombre obligatorio y cuenta visible → confirmar → Guardado en tu cuenta. Cancelar no descarta la escena. El proyecto de ejemplo aparece en la colección de memoria y puede reabrirse.
2. **Continuar:** abrir proyecto → nombre/escena → editar → Guardando… → confirmación de esos cambios. Guardar ahora permite enviar de inmediato. Una respuesta anterior no puede confirmar otra escena o una revisión posterior. El fixture protege el cambio de escena con una identidad de operación; la garantía real pertenece a la implementación.
3. **Escena nueva:** desde un proyecto confirmado se desvincula la nueva escena; desde envío pendiente se espera su confirmación. Una escena nunca guardada muestra confirmación con Cancelar, Guardar proyecto y Descartar y continuar. Tras guardar y continuar, la nueva escena vuelve a Sin guardar y conserva «Escena nueva». Plantillas y Abrir en Escena de la biblioteca deben reutilizar esta misma transición; sus selectores existentes no se rediseñan aquí.
4. **Reabrir/buscar:** búsqueda sobre toda la colección autorizada antes de paginar → seleccionar resultado → inspeccionar propietario/estado → Abrir proyecto. Un fallo de siguiente página conserva los resultados actuales y ofrece Reintentar; el filtro nuevo invalida la página anterior.
5. **Conflicto:** detener autosave → conservar borrador → Guardar una copia propia o Cargar versión del servidor. Esta última acción confirma que cambia la escena visible y conserva el borrador. Cancelar mantiene conflicto y borrador. Guardar una copia pide nombre; nunca modifica el original ajeno o la versión en conflicto.
6. **Sin conexión/error:** estado explícito sin guardar, borrador conservado y Reintentar guardado. La maqueta permite simular recuperación; no es una prueba de conectividad real.
7. **Original ajeno:** propietario y Solo lectura visibles, edición deshabilitada → copia propia solo con permiso del Taller. Sin ese permiso se explica por qué la copia está deshabilitada. Abrir nunca transfiere propiedad.
8. **Importación:** consentimiento para la cuenta visible → nombre del proyecto → importar una vez → confirmación de conservación del original. No importar cierra sin tocar almacenamiento. Incompatibilidad explica el fallo y permite descargar el original de ejemplo. Reintentar no duplica el fixture. No se importan conversación ni imágenes.

## 7. Especificaciones de vistas

| Vista | Jerarquía, contenido y acción |
|---|---|
| V1 Mis proyectos | Shell → Proyectos/Escena nueva → búsqueda → registros/paginación → inspector Nombre/Propietario/Estado/Abrir proyecto. Sin filtro de otros propietarios. |
| V2 Proyectos del personal | Misma superficie, filtro Propietario con todos/propios/otra cuenta autorizada. Los resultados ajenos indican su propietario; la apertura dirige a solo lectura. |
| V3 Taller propio | Cabecera de escena existente con nombre editable y estado, Guardar ahora/Escena nueva; herramientas y lienzo conservados; inspector de guardado y recuperación. Las herramientas ajenas al cambio son controles ilustrativos explícitos. |
| V4 Taller ajeno | Cabecera, banda Solo lectura/propietario y Guardar una copia; controles de edición deshabilitados; lienzo consultable. En teléfono se evita repetir el mismo mensaje en otro inspector. |
| D1 Primer guardado/copia | Nombre asociado a su etiqueta, cuenta destino, explicación y Cancelar/Guardar. Campo vacío produce error asociado. |
| D2 Escena nueva | Advertencia de escena nunca guardada y tres salidas explícitas. |
| D3 Cargar servidor | Explicación de sustitución de la escena visible/conservación del borrador, Cancelar/Cargar versión del servidor. |
| D4 Importar | Cuenta destino, consentimiento explícito por acción, nombre editable y No importar/Importar a mi cuenta. Importando impide repetir envío; importado explica resultado. |
| D5 Importación incompatible | Explicación y Descargar original/Cerrar. Sin limpieza automática del navegador. |

Solo se utilizan nombres numerados «Proyecto de ejemplo», cuentas `@prueba.local` e ilustración declarada de ejemplo. No hay fechas, empresas, slogans, precios, historias de versión ni operaciones de borrado/transferencia.

## 8. Estados y recuperación

El inspector nativo conserva `view`, `state`, `scene`, `theme`, `motion` y la etiqueta **Mockup**. La lista de Estado declara todos los estados de esta dirección; Vista y Diálogo acotan dónde son aplicables. Un estado que no corresponde a la vista conserva su superficie base, sin inventar un error adicional.

| Estado | Vista/diálogo aplicable | Presentación y salida |
|---|---|---|
| normal | V1–V4 | Resultados o proyecto confirmado; solo lectura en V4 |
| loading | V1/V2 | Tres filas Skeleton y anuncio Cargando proyectos… |
| empty | V1/V2 | Aún no tienes proyectos guardados + Escena nueva |
| no-match | V1/V2 | No hay coincidencias + Limpiar búsqueda |
| next-page | V1/V2 | Segunda página de datos de ejemplo y selección consistente |
| next-loading | V1/V2 | Filas conservadas; Cargando… deshabilitado |
| next-error | V1/V2 | Filas conservadas; error y Reintentar en paginación |
| new | V3 | Escena nueva, Sin guardar, ningún proyecto vinculado; primer guardado pide nombre |
| saving | V3/D1 | Guardando…; Guardar ahora/confirmación deshabilitados |
| saved | V3 | Guardado en tu cuenta después de confirmación |
| offline | V1/V2/V3/D1/D4 | Sin conexión, no se afirma guardado, salida de reintento; borrador conservado |
| error | V1/V2/V3/D1/D4 | Explicación y recuperación; nombre/escena originales conservados |
| conflict | V3 | Autosave detenido; borrador local y dos decisiones explícitas |
| no-permission | V4 | Solo lectura y copia deshabilitada con motivo visible |
| invalid | D4/D5 | Incompatibilidad, explicación y descarga original |
| importing | D4 | Importando… deshabilitado, sin doble envío |
| imported | D4 | Proyecto importado una sola vez; original conservado |
| validation | D1/D4, mediante acción | Nombre vacío muestra error asociado sin cerrar diálogo |

Obsolescencia de respuestas de consulta y validación servidor se especifican en el comportamiento, pero esta maqueta no ejecuta consultas de red. No se presenta esa garantía como un resultado de la auditoría visual. Tampoco se simulan tokens, hashes, revisiones persistidas o sesiones reales.

## 9. Reflujo

- **≥1100px:** lista/inspector 1.65:1; Taller herramientas 180px, lienzo flexible, inspector 310px. Padding exterior 40px.
- **768–1099px:** lista/inspector 1.4:1, inspector mínimo 260px; herramientas 150px y lienzo, estado de guardado debajo a todo el ancho. Padding exterior 28px. No desplazamiento horizontal.
- **<768px:** una columna, 20px exteriores; filtros apilados, lista antes del inspector. En Taller el estado de guardado precede a herramientas/lienzo; solo lectura se expresa en su banda sin mensaje duplicado. Acciones Foto realista/Exportar/Lista de compra apiladas, sin cortar palabras para caber en tres columnas. Diálogos de ancho disponible, contenido desplazable y acciones apiladas.

Los cambios se producen por CSS, sin alterar la identidad del proyecto. Se verifican 390/768/1024/1280px; 320px se añade en un probe de reflujo. La maqueta está en español según el brief; no implementa el trabajo de localización SP-8. El control de idioma se conserva en ES como contexto del shell.

## 10. Accesibilidad

Objetivo WCAG 2.2 AA para controles y contenido del cambio, sujeto a revisión del producto implementado. Texto ≥4.5:1, bordes de campos ≥3:1, foco de 3px visible y controles de al menos 44px. Jerarquía H1/H2 y etiquetas asociadas; filas son botones con selección anunciada mediante `aria-pressed`, sin inventar un árbol ni un grid ARIA.

`role=status` anuncia guardado y carga; errores de nombre utilizan `role=alert`, `aria-invalid` y `aria-describedby`. Los diálogos tienen título/descripción, foco contenido y fondo inerte mediante la biblioteca real; Escape/cancelación retornan al origen cuando existe. El SVG tiene nombre accesible y se identifica como escena de ejemplo. Los iconos redundantes están ocultos a lectores. Selección y estado incluyen texto, no solo color.

El runtime y CSS dan paridad a reducción de movimiento, Quieto y still, incluidos pseudo-elementos. Se verifica navegación Tab y recuperación de foco en cancelar conflicto. La auditoría automatizada no acredita por sí sola conformidad WCAG completa, lectura real con tecnologías de asistencia ni comportamiento servidor.

## 11. Criterios visuales y evidencia

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 390/768/1024/1280 | todos | Marca, Pictures/Sempertex, cuenta y regla horizontal mantienen el sistema de los hermanos. |
| B-AC-02 | ≥768 | resultados | La lista y el inspector están contiguos en una sola hoja; no hay cuadrícula de tarjetas. |
| B-AC-03 | <768 | resultados | Lista e inspector se apilan y las acciones no desbordan. |
| B-AC-04 | todos | selección | Cambiar de fila actualiza nombre y propietario del inspector; seleccionar no abre el Taller. |
| B-AC-05 | todos | búsqueda | Escribir conserva el foco; encontrar 05 funciona sin cargar antes la segunda página. |
| B-AC-06 | todos | filtro | Cambiar propietario/búsqueda vuelve a página 1 y mantiene una selección existente entre resultados. |
| B-AC-07 | todos | next-error | Se conservan los registros y aparece Reintentar en la zona de paginación. |
| B-AC-08 | todos | primer guardado | El nombre vacío muestra error sin cerrar; el confirmado aparece en lista y puede reabrirse. |
| B-AC-09 | todos | new | Escena nueva muestra Sin guardar y el primer guardado pide nombre. |
| B-AC-10 | todos | saving → new | La respuesta simulada anterior no convierte la escena nueva en Guardado. |
| B-AC-11 | todos | conflict | Guardar ahora está deshabilitado; el inspector ofrece copia/cargar servidor y conserva el lienzo. |
| B-AC-12 | <768 | conflict/offline/error | La explicación de recuperación precede al lienzo. |
| B-AC-13 | todos | foreign | Propietario y Solo lectura son visibles; editar está deshabilitado. |
| B-AC-14 | todos | no-permission | Guardar una copia está deshabilitado y el motivo es legible. |
| B-AC-15 | todos | incompatible | Descargar original está disponible y no se modifica localStorage. |
| B-AC-16 | todos | imported/retry | Dos aceptaciones del fixture dejan un único proyecto importado. |
| B-AC-17 | todos | diálogo cancelado | El foco retorna al control de origen y el conflicto permanece. |
| B-AC-18 | todos | expressive | Hoja, filas, inspector, marcador y controles tienen movimientos observables distintos. |
| B-AC-19 | todos | reduced/still | No queda animación activa; la selección y las acciones siguen presentes. |
| B-AC-20 | 390 | Taller | Las tres acciones inferiores se apilan y sus etiquetas permanecen completas. |
| B-AC-21 | ambos temas | todos | Texto, bordes de control y foco pasan medición; footer y contenido comparten eje exterior. |
| B-AC-22 | todos | inspección | Vista, Estado, Diálogo, Tema, Movimiento y Mockup están visibles fuera del producto. |

### Evidencia ejecutada

PENDIENTE_RESULTADO_FINAL

Los recorridos Playwright complementarios comprobaron búsqueda manteniendo foco, resultados fuera de la primera página, selección tras reintento, primer guardado/validación/listado/reapertura, copia ajena, denegación sin permiso, renombrado en línea y guardado simulado, espera antes de Escena nueva y protección frente a una respuesta de guardado obsoleta, conflicto/cancelación/foco, descarga de original de ejemplo e importación repetida sin duplicado. Un primer probe se interrumpió por un selector de prueba ambiguo durante la salida del diálogo; el probe corregido espera su cierre y pasa. No fue un fallo de la maqueta.

Se inspeccionaron capturas en memoria a 1280/390px en ambos temas. Se corrigió el apilado de acciones inferiores del Taller en teléfono a partir de esa inspección. No se escribieron capturas ni archivos de log fuera de los entregables permitidos.

## 12. Preguntas y límites

**Q: ¿La importación debe conservar el nombre legado en un campo editable prellenado o pedir un nombre antes de confirmar?** Recomendación: prellenar el nombre legado sin modificar la fuente; la exploración expone un campo de nombre antes de importar. Responsable: owner/Planner. No cambia las decisiones ya cerradas sobre consentimiento, conservación o copia única.

Supuestos del fixture: seis proyectos neutros iniciales, paginación reducida, cuenta de ejemplo y memoria volátil. El ejemplo de escena usa globo/mesa como contexto del Taller existente; no propone nuevas piezas ni cambia sus herramientas. El idioma permanece ES, como pide el brief; la localización y los destinos Mi cuenta/Planes/Cerrar sesión pertenecen a sus subplanes y aquí se identifican al activarlos. Las herramientas de edición, plantillas y biblioteca se conservan como contexto; el mockup no ejecuta sus motores.

Límites verificados: los probes prueban comportamiento de una maqueta local. Persistencia entre navegadores, autorización real, conservación byte a byte del original, recuperación después de recargar y deduplicación transaccional requieren implementación/verificación de SP-4. Ningún resultado visual se presenta como prueba de esas garantías.

Impacto: alternativa de composición e interacción compatible con el resultado funcional del brief; **breaking visual** respecto de la composición anterior, si se elige, por lista/inspector, apertura explícita y reflujo. Afecta T4.4/T4.5 y criterios de T4.8, con copia posterior T4.1. Los shells/tokens/contratos hermanos y los requisitos no cambian. Esta dirección sigue draft; no se concede aprobación ni se modifica el canónico.
