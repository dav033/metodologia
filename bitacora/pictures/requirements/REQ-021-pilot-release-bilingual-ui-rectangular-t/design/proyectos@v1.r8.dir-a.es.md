---
name: Archivo de montajes
status: draft
kind: direction-exploration
contract_ref: proyectos@v1
revision: r8.dir-a
subplan: SP-4
requirements: [R6, R7]
owner: David
date: 2026-10-27
chosen_thumbnail: proyectos@v1.r8.dir-a.html.candidate-1.html
---

# Archivo de montajes — dirección A

## 1. Identidad y trazabilidad

Una **exploración** independiente, pendiente de selección por parte del propietario. Este no es el contrato canónico, una revisión aprobada, una implementación ni una instrucción para consumir un borrador. Solo se escriben los seis artefactos de dirección específicos de esta revisión y el RESULT de delegación. SPEC, PLAN, los contratos compartidos, el historial y los repositorios permanecen intactos.

Fuentes: `SPEC.md` (prefijo SHA-256 `65b1e5ecc06f20d9`), `PLAN.md` (`cc7e53f2abf3c23c`), `PLAN.json` (`7a2c833a7e711508`) y `proyectos@v1.r8.behavior.md` (`378c0aa4a41164c6`). La fuente compartida identifica SP-4, R6/R7, el contrato futuro `proyectos@v1`, la tarea de diseño T4.1 y la auditoría visual T4.8. El plan sigue en discusión; la ronda 9 define el comportamiento, no la aprobación del diseño.

## 2. Propósito, concepto y recurso memorable

**Concepto:** un archivo de trabajo de montajes con globos. Un proyecto es un montaje con nombre, propietario, escena completa y revisión guardada. La pantalla responde: «¿Qué montaje puedo continuar y dónde están mis cambios?». La propiedad y el estado del guardado son información de trabajo, no estadísticas decorativas.

**Recurso memorable:** el registro seleccionado **se despliega en el mismo lugar** para mostrar una vista de escena y detalles. El título y la revisión permanecen en el encabezado del registro; debajo se abre un pliegue en perspectiva poco profundo. Durante un conflicto, las hojas local y del servidor se alinean una junto a la otra con un desfase de 80 ms. Es una breve secuencia de alineación, sin rebote elástico ni desaparición del texto.

Usuarios: los propietarios continúan sus propias escenas; los empleados y administradores con `proyectos.ver_todos` inspeccionan la colección autorizada; el personal sin `taller.usar` tiene una vista de solo lectura y no puede crear una copia. La importación solicita el consentimiento de la cuenta actual. Abrir el proyecto de otra persona nunca cambia su propietario.

## 3. Composición, propuestas y registro visual

Se crearon dos miniaturas visuales nuevas **antes** del TSX:

- **Elegida: [propuesta 1](proyectos@v1.r8.dir-a.html.candidate-1.html)** — registros compactos de ancho completo con despliegue integrado de escena y detalles. Los nombres, propietarios y revisiones se mantienen comparables. El registro abierto incluye una acción principal para continuar.
- [Propuesta 2](proyectos@v1.r8.dir-a.html.candidate-2.html) — una placa grande para el proyecto reciente y una pila más pequeña con imágenes. Da más espacio a las ilustraciones, pero reduce la consistencia al recorrer la vista y muestra menos información sobre propiedad y revisión.

Las miniaturas son composiciones originales de pequeño tamaño, no pantallas de producción ni una alternativa basada en fragmentos HTML. La maqueta completa usa el constructor real de la biblioteca sin conexión.

**Por qué no es un diseño genérico predeterminado:** no hay estadísticas de panel, ilustración de fondo ni cuadrícula de tarjetas de vista previa uniformes. Los registros de montaje se despliegan dentro de su colección. La jerarquía se compone del nombre grande del proyecto, una marca de tiempo compacta, un diagrama de la escena completa y el comprobante del guardado. La lista, no un elemento principal decorativo, ocupa la página.

**Registro visual:** se leyeron SP-2 `cuentas-admin@v1.r7.dir-a/b/c.md` y SP-3 `taller-esenciales@v1.r6.dir-a/b/c.md`. Cuentas A usa un margen lateral editorial y un registro; B, un pase de acceso que se despliega y una barra inferior; C, pases perforados y espacios para permisos. Taller A usa dos bandas de montaje; B, una columna de herramientas, un escenario y un folio; C, una mesa de corte y una bandeja inferior de herramientas. Esta exploración comparte la marca de anillo y punto de Pictures, los términos del producto, la asignación de tokens y la navegación neutra. No usa su margen lateral, pase de acceso, barra inferior, columna de herramientas ni bandeja de montaje. Aquí el pliegue abre el registro de un proyecto dentro de una colección, en vez de un pase de identidad de dos hojas. Su movimiento preciso de alineación, sin elasticidad, difiere de la coreografía de resorte y bisagra del pase de acceso.

## 4. Ocho ejes, asignación al sistema y componentes reales

| Eje | Expresión actual | Evidencia renderizada |
|---|---|---|
| Concepto | Archivo activo de montajes con nombre; cada registro incluye al propietario y la versión guardada. | `.record`, `.record-sub`, `.folio-info` |
| Diseño | Registros apilados de ancho completo; el registro abierto se despliega en escena y detalles con una proporción aproximada de 44:56. La edición de escenas y la importación usan sus propias superficies de trabajo contextuales. | `.archive`, `.record-fold`, `.editor-layout`, `.import-layout` |
| Navegación | Subrayado neutro integrado al flujo para cambiar de colección, búsqueda en toda la colección, filtro de propietario exclusivo para el personal y registros desplegables operables con teclado. El retorno al proyecto aparece junto a su título. | `.scope-nav`, `.search-field`, `.record-toggle`, `.backline` |
| Tipografía | Alternativa sin conexión Arial/Helvetica; título de página de 32 px, nombres de registros de 21 px en escritorio y 23 px en teléfono, título del despliegue o conflicto de 24 px, texto y controles de 14–15 px, marca de tiempo monoespaciada tabular de 12 px. | `.intro-copy h1`, `.record-title`, `.record-date` |
| Densidad y forma | Los registros comienzan en 91 px en escritorio y 110 px en teléfono. Filas con líneas divisorias, márgenes interiores de 24 px al desplegarse y controles de 44 px; solo los diagramas y las decisiones necesitan marcos redondeados. | `.record-toggle`, `.record-fold`, `.stage`, `.btn` |
| Componentes | Button, Input, Skeleton, Dialog y AlertDialog reales; control desplegable de registro personalizado, SVG de instalación, vista de versiones y comprobante de importación. | `[data-slot=button]`, `[data-slot=input]`, `.compare-versions`, `.import-receipt` |
| Color | Asignación de colores claro/oscuro de Pictures; malva para la acción principal y los globos, verde para guardado, ámbar para elementos sin enviar o en conflicto, rojo para errores; navegación neutra entre colecciones. | `.status`, `.notice`, `.scope-link`, `.balloon` |
| Movimiento | Alineación horizontal de 9 px, desfase de filas de 45 ms, pliegue en perspectiva de -4°, alineación de hojas de 80 ms; función de aceleración `cubic-bezier(.16,1,.3,1)`. Pliegue expresivo de 420/588 ms, natural de 220/308 ms y sutil de 140/196 ms; interacción de presión o desplazamiento sobre controles de 160 ms. | `.record`, `.record-fold`, `.archive-tools`, `.record-arrow`, `.version-sheet` |

El JSON complementario proporciona los ocho ejes y 14 selectores para los cuatro ejes medibles. Cada selector de movimiento tiene una animación o transición real. `useMotionProfile()` establece los tiempos y el estado de movimiento reducido; las animaciones CSS finitas proporcionan la gramática de esta dirección. No hay animaciones decorativas infinitas. Si la pestaña queda oculta, las animaciones se pausan; el movimiento reducido, Quieto y `?still=1` eliminan los desplazamientos y las rotaciones sin alterar las acciones ni la disposición final.

Ambos repositorios se inspeccionaron en modo de solo lectura: `src/app/globals.css`, `src/components/tres-d/guardado-escena.ts` y el componente consumidor del guardado `Taller3D.tsx`. El debounce existente de 500 ms es un valor técnico predeterminado; la nueva interfaz no afirma que el escritor actual del navegador guarde en el servidor. El lector anterior puede descartar datos de escena incompatibles, por lo que SP-4 debe leer los datos heredados sin procesar antes de pasarlos por ese analizador, tal como exige la fuente de comportamiento.

| Token de Pictures | Función en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | tarjeta/ventana emergente | `#ffffff` / `#16181f` |
| `--texto` | colores de primer plano | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | color de primer plano atenuado | `#6b6178` / propuesta local `#adb3c0` |
| `--superficie-2` | secundario/atenuado | `#efe9f8` / `#242733` |
| `--acento`, `--sobre-acento` | principal/primer plano principal/anillo | `#6d3fe0`, blanco / `#9479ff`, `#120b24` |
| `--acento-suave` | principal suave | `#ece3fb` / `#241f3d` |
| `--borde` | borde decorativo | `#e3daef` / `#383c48` |
| `--texto-tenue` / `--texto-suave` | borde local más marcado para entradas | `#766c85` / `#9aa1ad` |
| `--taller-visor` | fondo del diagrama | `#ebe7f1` / `#1a1722` |
| `--exito`, `--aviso`, `--error` | texto de estado y fondos suaves | Valores existentes de Pictures según el tema |

El borde más marcado de los campos de entrada, la línea decorativa más oscura y los metadatos más claros en tema oscuro son adaptaciones de accesibilidad explícitas y locales a la maqueta. No modifican el sistema de diseño de producción. La página, el encabezado y el pie de página comparten el mismo eje exterior; el contenido desplegado tiene un margen interior propio y uniforme. El diseño no usa casillas de verificación, por lo que no introduce dependencias del contraste de casillas nativas.

Procedencia de los componentes: `shadcn:button default/outline/ghost` de `@/components/ui/button`; `shadcn:input` de `@/components/ui/input`; `shadcn:skeleton` de `@/components/ui/skeleton`; `shadcn:dialog` de `@/components/ui/dialog` y `shadcn:alert-dialog` de `@/components/ui/alert-dialog` (Animate UI instalado sobre Base UI). `@kit/mockup` proporciona `mountMockup/useMockup`; `@kit/motion` proporciona `useMotionProfile`; `motion/react` está incluido en el paquete. El control desplegable del registro es un botón semántico personalizado, no un Accordion de upstream. Los gestos de Bencho y los efectos promocionales de React Bits no son necesarios para esta pantalla operativa.

## 5. Navegación y modelo de interacción

Los selectores nativos de planificación mantienen **Mockup**, Vista, Estado, Diálogo, Tema y Movimiento. El puente de la página del plan puede controlarlos mediante sus IDs estables `view`, `state`, `scene`, `theme`, `motion`. Son controles de demostración fuera del producto, no un modelo de autorización.

La navegación del producto es contextual: cambio de colección, búsqueda y filtro, despliegue de registro, Continuar/Abrir en modo de solo lectura, retorno al proyecto e inicio de revisión de importación. La colección de usuario normal oculta el selector de ámbito para el personal y el filtro de propietario. Las cinco opciones nativas de Vista muestran los escenarios autorizados para compararlos; no añaden un elemento de navegación para el personal al producto de un usuario normal.

Cada control para desplegar un registro expone `aria-expanded` y `aria-controls`. Las acciones de los diálogos con nombre usan componentes modales reales, restringen la navegación con Tab y Shift+Tab, y admiten Escape con retorno del foco. La confirmación de carga del servidor usa AlertDialog; no se puede cerrar con un clic casual fuera del diálogo. No se requiere arrastrar, usar acciones disponibles solo al pasar el puntero ni navegar con iconos sin texto.

## 6. Flujos y límites de comportamiento

1. **Primer guardado con nombre:** Nuevo proyecto abre un borrador; Guardar proyecto solicita un nombre no vacío e identifica a Ana Torres como la cuenta de destino. Al confirmar, se añade un registro de demostración de su propiedad. Las ediciones posteriores muestran los estados pendiente → guardando → guardado con el debounce heredado de 500 ms y una demora ilustrativa de solicitud. Guardar ahora sigue disponible para proyectos existentes propios.
2. **Buscar y volver a abrir:** La búsqueda abarca toda la colección autorizada antes de paginar; al cambiar la consulta o el propietario, se restablece la página. Los datos de prueba simulados incluyen 57 registros de dos propietarios; «Terraza azul» es el registro 57 y puede encontrarse sin cargar las páginas anteriores. El ámbito del personal muestra el filtro de propietario. Si falla la carga de una página posterior, se conservan los registros anteriores y se ofrece reintentar. En producción se deben usar búsquedas literales en todo el servidor, cursores vinculados a filtros y rechazo de respuestas obsoletas; no se debe copiar este filtro en memoria como búsqueda exclusiva del cliente.
3. **Conflicto:** Un 409 detiene el guardado; el trabajo local sin enviar se conserva. Las dos hojas identifican los cambios locales y la versión 13 del servidor. Guardar como copia crea una nueva escena propia; cargar la versión del servidor solicita confirmación y conserva la escena local anterior como borrador asociado a la cuenta y al proyecto. La demostración permite guardar como copia el borrador desplazado que se conservó después de cargar la versión 13. No ofrece una acción para sobrescribir ni un visor del historial de versiones.
4. **Sin conexión o error:** Las ediciones sin enviar permanecen visibles y marcadas como no enviadas, con opciones para reintentar o reconectar. Nunca se representan como un guardado correcto en el servidor. En producción, los acuses de recibo deben coincidir con la cuenta, el proyecto, la revisión y la generación de edición actuales; una respuesta obsoleta no puede cambiar el estado del borrador más reciente.
5. **Original de otra persona:** El personal autorizado consulta la escena sin controles para modificarla. La copia requiere `taller.usar`, pertenece a la cuenta actual y deja intacto el original. Abrir el proyecto no transfiere la propiedad. El estado Deshabilitado muestra explícitamente el rol de solo lectura sin acceso a Taller.
6. **Importación heredada:** La revisión identifica el origen y la cuenta de destino. Con el consentimiento, se importa una vez; «Ahora no» conserva los datos locales sin procesar y ofrece revisarlos más tarde. Repetir el consentimiento o volver a revisar no duplica el registro simulado. Si los datos heredados no son válidos, se explica por qué no se pueden importar y se ofrece descargar la muestra sin modificar. Para garantizar que los reintentos sean seguros en producción se necesita la cuenta, el hash de la fuente sin procesar y una transacción; la maqueta no demuestra persistencia.
7. **Salir del proyecto:** Si hay cambios sin enviar, la acción de retorno al proyecto abre una decisión para conservarlos, con opciones para seguir trabajando o crear una copia propia. En producción se deben conservar los borradores y comprobantes por cuenta y proyecto, y limpiar la vista de la cuenta anterior al cambiar de cuenta. SP-4 no añade un selector de cuentas ni un flujo de eliminación.

La carga útil persistida sigue siendo **nombre más escena completa**: sala, entorno, salón, materiales, adjuntos y relaciones entre nodos. La conversación con IA y las imágenes generadas permanecen en el navegador. El rechazo a eliminar una cuenta que tiene proyectos, la validación del servidor, las actualizaciones condicionales atómicas, las comprobaciones de mutaciones entre orígenes y el aislamiento de propiedad siguen siendo obligaciones de T4.2/T4.3/T4.31/T4.6/T4.9; esta ilustración no las demuestra. No se añade ninguna función para eliminar proyectos, transferir la propiedad ni consultar el historial de versiones.

## 7. Inventario de vistas y consumidores

| Vista / id | Contenido y resultado principal | Trazabilidad |
|---|---|---|
| Mis proyectos / `mine` | Colección personal, búsqueda por nombre, montaje desplegable, propietario y revisión guardados, proyecto nuevo, continuación de página y acceso a la importación local. | R6/R7 · T4.4/T4.5 |
| Consulta del equipo / `all` | Colección autorizada, filtro por propietario actual, acceso de solo lectura a proyectos ajenos y búsqueda en toda la colección. | R6 · T4.3/T4.4 |
| Proyecto propio / `editor` | Guardado con nombre, comprobante de guardado visible, diagrama ilustrativo de la escena completa, comparación de conflictos y recuperación del borrador conservado. | R6 · T4.4 |
| Proyecto ajeno / `foreign` | Propietario identificado, escena de solo lectura y copia propia condicionada al permiso de Taller. | R6 · T4.4 |
| Importar del navegador / `import` | Garantía de conservar la fuente sin procesar, cuenta de destino, nombre y consentimiento explícitos, rechazo, reintento y explicación o descarga ante datos incompatibles. | R7 · T4.5 |

Las cuatro escenas de diálogo son `first-save`, `copy`, `load-server`, `leave`. Las dos últimas son decisiones de recuperación, no una ampliación del alcance del producto. El esquema solo muestra una mesa representativa, ocho sillas, un panel y globos; es un SVG local, no un motor 3D, un servicio para generar miniaturas ni una serialización de proyectos validada.

## 8. Inventario de estados

Los trece estados se pueden alcanzar desde Estado. Los estados contextuales afectan solo a los controles pertinentes; elegir una fixture no implica que todos los estados puedan ocurrir en todas las vistas de producción.

| Estado / id | Comportamiento visible y recuperación |
|---|---|
| Normal / `ready` | Colección y continuación; edición propia; importación voluntaria. |
| Cargando / `loading` | Esqueletos estables para filas/escenas; controles que dependen de solicitudes deshabilitados; las fixtures con nombre existentes conservan su última revisión conocida. |
| Vacío / `empty` | Explicación de la colección con una próxima acción y acceso a la importación local. En el editor/importación, esta fixture no inventa un contenido externo vacío. |
| Error / `error` | Texto del error, trabajo conservado y reintento; no se inventa contenido de la colección. |
| Éxito / `success` | Confirmación de guardado/importación; la importación explica que la fuente sin procesar se conserva. |
| Guardando / `saving` | Estado pendiente o texto de la acción de importación; controles de solicitud repetida deshabilitados. |
| Cambios sin guardar / `dirty` | Estado explícito de envío pendiente en un proyecto propio. No es un nuevo estado de guardado para un original externo. |
| Sin conexión / `offline` | El trabajo local permanece visible; las operaciones remotas están deshabilitadas; la acción para reconectarse explica cómo recuperarse. |
| Conflicto / `conflict` | Guardado propio detenido, hojas con dos versiones, opciones para copiar/cargar y ninguna sobrescritura silenciosa. Los originales externos no ofrecen una acción para editar el original en caso de conflicto. |
| Datos no válidos / `invalid` | Explicación del campo/contenido; descarga del contenido sin procesar para importar; sin migraciones con pérdida de datos ni éxitos inventados. |
| Sin permiso / `denied` | Escena y metadatos externos ocultos; volver a los proyectos propios. |
| Sin Taller / `disabled` | En la vista externa, el original se puede inspeccionar, la edición/copia está deshabilitada y se explica el permiso faltante. |
| Falló la página siguiente / `next-error` | Se conserva la lista existente y se puede reintentar la continuación; los cambios de consulta/filtro reinician la página mostrada. |

La lista de muestra es síncrona, por lo que el rechazo de respuestas de consultas obsoletas, las carreras entre dos navegadores y el aislamiento de cuentas son requisitos especificados para la implementación, no afirmaciones simuladas sobre el backend. La selección de fixtures ilustrativas sigue siendo independiente de las interacciones del producto; usa Normal para inspeccionar las transiciones locales naturales.

## 9. Reglas de diseño adaptable

- **≥1024 px:** contenedor compartido de hasta 1360 px, márgenes exteriores de 40 px (48 a ≥1500); columnas horizontales para título/propietario/hora/detalles del registro; distribución de escena/detalles de aproximadamente 44:56; editor de proyectos con escena y columna contextual de 280 px; importación en dos columnas.
- **768–1023 px:** márgenes de 24 px; el alcance de la colección pasa a su propia fila; búsqueda y filtro/acción permanecen alineados; contexto del editor de 250 px; metadatos del registro más estrechos.
- **360–767 px:** márgenes exteriores de 20 px; búsqueda/filtro/acción apilados; cada registro tiene una línea para nombre/propiedad y otra para la marca de tiempo; la vista plegada, el editor y la importación pasan a una columna. Las hojas de versiones se apilan. Los controles miden ≥44 px y el texto extenso se ajusta a varias líneas. La página se desplaza verticalmente; ningún dock fijo del producto oculta el contenido.
- **320–359 px:** se conservan los márgenes exteriores de 20 px; los datos se reducen a dos columnas y se elimina el anillo decorativo de marca para mantener legible la etiqueta de cuenta. La página no se desplaza horizontalmente.
- **Altura horizontal ≤540 px, ancho <1024 px:** la escena del editor y el contexto de 240 px se muestran uno al lado del otro; la altura del modal se limita por debajo de la barra de planificación y el contenido se desplaza internamente.

Los diálogos usan márgenes exteriores de 20 px y un ancho ≤560 px, con desplazamiento interno y espacio libre respecto a la barra de planificación. Las acciones del modal se apilan en teléfonos. El encabezado, la página y el pie comparten el mismo eje exterior, en lugar de centrar líneas sin relación.

## 10. Objetivos de accesibilidad y evidencia observada

Objetivo WCAG 2.2 AA: texto legible con contraste ≥4.5:1; bordes interactivos/foco ≥3:1; foco visible de 3 px con separación de 3 px; disclosures semánticos, títulos/descripciones de modales, mensajes de estado/alerta y campos/selectores etiquetados. Las etiquetas del cuerpo/metadatos miden al menos 12 px; las dimensiones del diagrama, 11 px. Los controles deshabilitados permanecen opacos y legibles. No se requiere una casilla de verificación nativa. El movimiento reducido elimina el pliegue/desplazamiento, pero conserva todos los datos y decisiones.

La auditoría automatizada mide el foco, el relleno, la alineación, el contraste y el desbordamiento; no constituye una certificación WCAG completa. Una prueba de teclado enfocada verificó que 12 pulsaciones consecutivas de Tab permanecen dentro del diálogo, que Escape lo cierra y que el foco vuelve al activador real. La lectura del lector de pantalla, el zoom del 200–400 %, las tecnologías de asistencia táctil y las cadenas traducidas de producción quedan pendientes para una aceptación renderizada; aquí no hay evidencia de que se hayan completado.

## 11. Criterios observables y verificación

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| SP4-A-01 | ≥1024 px | ready | Un registro abierto conserva su nombre/propietario/revisión en el encabezado y muestra debajo una distribución de escena y detalles. |
| SP4-A-02 | 320–767 px | ready | Los registros usan dos filas de texto y la vista plegada se apila sin desplazamiento horizontal de página. |
| SP4-A-03 | todos los anchos admitidos | loading | Los esqueletos ocupan el área final del contenido y la acción de guardar que depende de una solicitud está deshabilitada. |
| SP4-A-04 | todos los anchos admitidos | empty | Una acción visible inicia un montaje nuevo y una segunda acción permite revisar la escena del navegador. |
| SP4-A-05 | todos los anchos admitidos | conflict | Se distinguen el trabajo local pendiente de envío y la versión 13 del servidor; copiar y cargar desde el servidor son acciones identificadas; Guardar ahora está deshabilitado. |
| SP4-A-06 | todos los anchos admitidos | offline | La escena propia sigue visible con el estado de envío pendiente y el guardado en el servidor deshabilitado. |
| SP4-A-07 | todos los anchos admitidos | disabled, foreign | La propietaria sigue siendo Luisa; los controles de edición/copia están deshabilitados y se indica la limitación de permisos de Taller. |
| SP4-A-08 | todos los anchos admitidos | invalid, import | La explicación de incompatibilidad y la descarga del original están visibles; la importación no está disponible. |
| SP4-A-09 | todos los anchos admitidos | denied | No se renderiza ninguna escena ni metadato del original externo. |
| SP4-A-10 | todos los anchos admitidos | next-error | Los registros cargados previamente se conservan y se puede volver a intentar la continuación. |
| SP4-A-11 | todos los anchos admitidos | copy/load modal | Las decisiones del diálogo caben dentro de los márgenes de la ventana y se pueden operar con el teclado. |
| SP4-A-12 | todos los anchos admitidos | reduced motion | No continúa ningún desplazamiento/giro de entrada, y los registros, controles y decisiones siguen disponibles. |
| SP4-A-13 | ≥1024 px y teléfono | ready, ambos temas | El encabezado/la página/el pie comparten un eje exterior; los controles tienen bordes visibles y muestran el foco. |
| SP4-A-14 | todos los anchos admitidos | recovery | Al cargar la versión del servidor, se conserva el desplazamiento local y se ofrece guardar ese borrador como copia propia. |

Compilación real sin conexión: **588,871 bytes**, aproximadamente 575 KB, 2,135 archivos fuente incluidos en el paquete. Sin instalación de paquetes, descarga de recursos, fuentes externas, CDN ni alternativa HTML. Solo se compiló la ruta de salida asignada.

Comandos ejecutados:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <proyectos@v1.r8.dir-a.tsx> --out <proyectos@v1.r8.dir-a.html>
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <proyectos@v1.r8.dir-a.html>
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <proyectos@v1.r8.dir-a.html>
```

La CLI de contraste informó `contrast: 158 pairs checked in light and dark, all pass`. Como TSX inyecta las personalizaciones del proyecto en tiempo de ejecución, una ejecución adicional de `contrast.check` combinó el CSS del tema instalado con el CSS exacto de la entrada: **158 pares efectivos del rol Pictures, PASS**. En la primera ejecución se encontró un par heredado `primary-soft` oscuro, sin uso, con una relación de 3.67:1; asignarlo explícitamente a `--acento-suave` de Pictures corrigió esa inconsistencia del token. La auditoría renderizada mide los colores calculados reales.

Auditoría renderizada final, código de salida 0, sobre la compilación final:

```text
audit: proyectos@v1.r8.dir-a.html — 340 renders (340 combinations planned), 11348 text measurements, 896 focus stops
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Se midieron las 340 combinaciones planificadas, sin muestreo: cinco vistas, trece fixtures de estado, cuatro diálogos, ambos temas y 1280/390 px. Las comprobaciones de auditoría también pasaron la estabilización de movimiento reducido y la estabilidad del diseño durante la carga expresiva. SHA-256 del HTML final: `8731d9a316dd7a4fd24177a95ebc2d3145a7ccc684d98309d0a146d0485025ff`.

Evidencia adicional: diez grupos de interacción aprobados (búsqueda en toda la colección, incluido el registro 57; filtro por propietario/reinicio de página; secuencia de edición/guardado; conservación sin conexión; copia propia tras conflicto; control de permisos de solo lectura para externos; rechazo/consentimiento/deduplicación de importación; descarga de contenido sin procesar incompatible; denegación sin escena; primer guardado con nombre y validación de nombre vacío). El cambio final de recuperación también se aprobó: el desplazamiento local sobrevive a la carga de la revisión 13 y se puede guardar como copia propia. El texto del comprobante sin conexión describe explícitamente que el guardado está en pausa.

Una prueba de diseño adaptable aprobó **50 diseños** (5 vistas × 5 anchos 320/390/768/1024/1280 × 2 temas) y **40 ajustes de modal** (4 escenas × 5 anchos × 2 temas). En estas pruebas ni en la prueba de humo de interacción se observaron errores de página ni solicitudes HTTP/HTTPS. La medición se volvió a ejecutar después de que el selector inicial coincidiera por error tanto con un diálogo cerrado que salía como con el AlertDialog activo; ahora comprueba el popup activo `data-open`. Una aserción inicial aparte de la prueba de humo esperaba “sin acceso al Taller”, mientras que el texto real dice “Tu rol no tiene acceso al Taller”; al corregir esa expectativa, la prueba de humo de interacción completa pasó. Ninguno de los fallos de los scripts de prueba se ocultó presentándolo como aprobado ni se sorteó mediante cambios al comportamiento del producto.

Se inspeccionaron en memoria cuatro capturas renderizadas: colección de escritorio/tema claro, colección de teléfono/tema oscuro, conflicto de escritorio/tema oscuro e importación de teléfono/tema claro. Al principio, el icono de búsqueda se superponía al texto indicativo; la entrada final usa un margen izquierdo de 44 px. La acción duplicada de nuevo proyecto en la cabecera se sustituyó por navegación contextual de la colección. No se agregaron archivos de capturas/logs. La prueba de evidencia de dirección validó **14 selectores**, sin evidencia faltante. No se realizó una comparación por pares con direcciones alternativas como parte de esta tarea. La carga expresiva mostró **10 animaciones finitas activas**; `?still=1` terminó con **cero animaciones activas** y el mismo contenido.

No se ejecutaron el lint/tipos/compilación de producción, las comprobaciones de base de datos/autorización, la persistencia entre navegadores, los conflictos atómicos, la importación idempotente del contenido sin procesar ni la protección contra respuestas obsoletas: no se modificó código de producción y el mockup no tiene conexión a servicios. Estas siguen siendo comprobaciones independientes del plan; no son motivo para afirmar que este artefacto está implementado.

## 12. Preguntas abiertas, supuestos e impacto

**P: ¿David quiere seleccionar “Archivo de montajes”, con registros que se despliegan dentro de la colección, como dirección de SP-4?** Responsable de la decisión: David, mediante la comparación visual. Esta es la única decisión abierta del propietario identificada durante esta exploración. Ninguna pregunta vuelve a abrir el modo de guardado de la ronda 9, el contenido entre navegadores ni las restricciones de escritura del personal.

Los supuestos son solo ilustrativos: Ana Torres/Luisa Rojas, 57 registros de muestra, marcas de tiempo, revisiones 12/13, dimensiones de la habitación, ocho sillas, muestra de descarga JSON sin procesar y demora de solicitud. No se leyeron datos reales de usuarios ni secretos. El SVG es esquemático; la muestra de descarga sin procesar contiene datos simulados, no el almacenamiento del navegador de David. El diseño no añade un formato de importación ni un límite de validación.

**Impacto:** una composición visual potencialmente **incompatible** si se selecciona, con requisitos de comportamiento compatibles. SP-4 es el único consumidor de `proyectos@v1` en esta instantánea: T4.1 copiará solo el contrato canónico que finalmente se apruebe; T4.4 implementa la lista, los nombres, los comprobantes de estado, la lectura/copia y los conflictos/recuperación; T4.5 implementa la importación; T4.8 vuelve a renderizar la composición seleccionada. T4.2/T4.3/T4.31 son responsables de los requisitos previos de almacenamiento/API; T4.6/T4.7, de la evidencia real de integración con el navegador; y T4.9, de la auditoría independiente de aislamiento/concurrencia. Más adelante, CG-3 verifica la composición con cuentas y Taller. Esta exploración no modifica ninguna de esas referencias ni aprobaciones.

El texto de la interfaz en español sigue el producto; SP-8 es responsable del texto de producción completo en ambos idiomas. La navegación del encabezado al producto general y el motor real de Taller pertenecen a sus superficies existentes. No se escribió ninguna vista previa del repositorio, registro de cambios compartido, contrato canónico, HTML canónico, plan ni aprobación. La decisión/finalización del propietario sigue pendiente.
