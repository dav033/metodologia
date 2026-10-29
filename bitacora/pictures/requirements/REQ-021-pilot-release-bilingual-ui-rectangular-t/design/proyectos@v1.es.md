---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer (Codex)
date: 2026-10-29
direction: c
name: Edición en contexto
source_revision: r12
source_behavior: proyectos@v1.r12.behavior.md
plan_revision: 15
---

# proyectos@v1 — Edición en contexto

## 1. Identidad y trazabilidad

Borrador canónico de planificación; **no aprobado para implementación**. El propietario eligió la dirección c, «Edición en contexto», mediante la comparación web. La elección de dirección autoriza esta finalización; no aprueba el contrato, el subplan ni el plan. Esta es la versión 1 y no modifica ningún predecesor aprobado. Los únicos entregables de diseño de esta tarea son `design/proyectos@v1.md` y `design/proyectos@v1.html`; el RESULT requerido de la delegación es evidencia administrativa. No se modifica ninguna exploración, historial, SPEC, PLAN, archivo de producción, registro de cambios del contrato ni vista previa.

Alcance: REQ-021 / M2 / SP-4 «Proyectos guardados», R6/R7 y US-3, según la SPEC vigente (estado listo), la revisión 15 de PLAN.json, `proyectos@v1.r12.behavior.md` y los archivos Markdown, TSX y HTML de la dirección r12 elegida. La sección «Behavior — SP-3 and SP-4 (round 9 answered)» de SPEC establece el guardado inicial explícito seguido del guardado automático, la persistencia de escenas/nombres, el acceso de solo lectura a originales ajenos, la importación sin pérdida, la búsqueda en toda la colección y las transiciones de proyectos nuevos sin guardar. Este contrato especifica su interfaz, no una nueva API de persistencia o autorización.

| Requisito | Cobertura del contrato | Tareas consumidoras |
|---|---|---|
| R6 — guardar en la cuenta, volver a abrir sin cambios; el personal/administrador abre proyectos autorizados | V1–V4, F1–F6, estados de guardado/lista/conflicto/recuperación y UI-AC-01–19, 24–29 | T4.4; revisión visual T4.8 |
| R7 — importación explícita de escenas del navegador sin pérdida | V5, D6, F7, estados de importación y UI-AC-20–23 | T4.5; revisión visual T4.8 |

Consumidores exactos del PLAN: SP-4 `ui.contract=proyectos`, `ui.version=1`, `design_task=T4.1`, `visual_review_task=T4.8`; tareas de implementación de interfaz T4.4 (lista, guardado, escena nueva, conflicto, solo lectura) y T4.5 (importación). T4.1 copia el artefacto aprobado por el propietario solo después de la aprobación independiente. T4.2/T4.3 son responsables del almacenamiento y la autorización, respectivamente, y las verifican; T4.6/T4.7 verifican el comportamiento real entre navegadores; T4.9 audita la especificación y los estándares. Que SP-6/SP-12 consuman la identidad del proyecto no los convierte en consumidores de este contrato visual.

**Impacto:** la composición supone un cambio incompatible respecto del borrador canónico sustituido y no aprobado: las bandas apiladas y expandibles, los detalles contextuales y la edición del nombre en línea requieren adaptar T4.4 y revisar T4.8 en pantalla. La presentación de la importación afecta a T4.5/T4.8. Respecto de la composición, navegación y movimiento de la dirección c seleccionada en r12, se mantienen; la versión actual incorpora actualizaciones de ejecución del kit. No se necesitó ningún cambio de comportamiento en el código fuente. La compatibilidad con cualquier implementación de producción aprobada está por determinar; no se afirma que exista. En esta delegación, no redirigir las referencias del plan, publicar en `design/contracts/`, aprobar ni implementar este borrador.

Evidencia del producto en modo de solo lectura: t12 `src/app/globals.css`, `layout.tsx`, `/3d/page.tsx`, `Taller3D.tsx` y `guardado-escena.ts`, además del resumen de interfaz proporcionado y los contratos hermanos `cuentas-admin@v1` / `planes@v1`. El Taller existente ya tiene un nombre de escena en línea, estado de guardado local, herramientas y una espera de 500 ms antes de guardar en el navegador. El almacenamiento, la lista, la identidad, la importación y los conflictos de proyectos son nuevos. El texto existente sobre el guardado del navegador no demuestra que haya persistencia en la cuenta. El TSX seleccionado se reconstruye sin cambios con el generador local instalado; no se copia desde su HTML generado anteriormente.

## 2. Propósito y usuarios

V1 responde «¿Qué escena guardada quiero continuar?». V3 responde «¿Cómo se llama este proyecto y estos cambios están guardados en mi cuenta?». Editar el nombre, comprobar el límite del guardado y resolver un fallo mantienen la escena visible en su contexto. El resultado esperado es volver a abrir la escena guardada completa con la misma cuenta en otro navegador, distinguiendo claramente el trabajo local pendiente de los datos confirmados en la cuenta.

Los propietarios enumeran, buscan, guardan y continúan sus propios proyectos. Los empleados/administradores con `proyectos.ver_todos` pueden filtrar por propietarios autorizados y abrir originales ajenos en modo de solo lectura; `taller.usar` también permite crear una copia propia. Un rol personalizado con permiso de lectura global, pero sin permiso del Taller, sigue teniendo acceso de solo lectura y no puede copiar. Quien use un navegador compartido decide explícitamente si la escena heredada debe guardarse en la cuenta que tiene la sesión iniciada. Abrir o previsualizar un proyecto ajeno nunca cambia su propietario.

Entre navegadores solo se transfieren el nombre del proyecto y la escena completa, incluidas la sala, el entorno, el salón, los materiales y las relaciones entre nodos de la escena. La conversación con IA y las imágenes generadas permanecen en su navegador. Las herramientas, la estructura, la navegación y la identidad existentes del Taller quedan fuera del rediseño. No se agrega una interfaz para eliminar, transferir, combinar, compartir públicamente ni consultar el historial de versiones.

## 3. Arquitectura de la información y jerarquía

Mantener el encabezado de Pictures/Sempertex, los controles de idioma/cuenta, la fila de título/acciones y la regla horizontal neutra de navegación establecida por los contratos hermanos. Los destinos de navegación son Taller 3D y Proyectos; este alcance no reemplaza la navegación global de la aplicación. En V3, conservar como contexto existente la barra de herramientas del Taller, la barra lateral de paneles, el inspector de escena/IA, deshacer/rehacer y el vocabulario de fotografía realista y lista de compras.

Orden de V1/V2: título y Escena nueva; navegación; búsqueda de proyectos con etiqueta y filtro de propietario solo para el personal autorizado; entrada de revisión/recuperación de importación cuando corresponda; bandas de proyectos autorizadas; estado de paginación/reintento/cargar más. No inferir el filtro de propietario a partir de un rol seleccionado por el cliente: la autorización del servidor determina el alcance disponible.

Los proyectos son bandas expandibles de ancho completo. El nombre, los metadatos de propietario/guardado/solo lectura y Ver escena/Abrir permanecen en el encabezado de la banda. Ver escena muestra la escena y la explicación sobre cuenta frente a navegador dentro de esa misma banda; al previsualizar otra, se cierra la anterior. Solo puede haber una abierta a la vez. Conservar inicialmente expandido el primer proyecto autorizado de la composición seleccionada; si no hay resultados, ninguno queda expandido. Cambiar la búsqueda o el propietario cierra la vista previa y reinicia la paginación. La vista previa es una ayuda de presentación local y no marca el proyecto como abierto para edición.

En las bandas expandidas de escritorio, la escena y la explicación usan una distribución de 1.8:1; en el teléfono, se apilan. «Qué se guarda» muestra los límites detallados de persistencia en el lugar donde se necesitan. En V3, el nombre de la escena se convierte en el campo de entrada en la misma ubicación del encabezado. El estado actual del guardado aparece junto a la identidad, con controles para el primer guardado/Guardar ahora; los errores contextuales aparecen inmediatamente encima de la escena. En V4, el aviso de propietario/solo lectura precede a la escena y a la acción opcional para crear una copia propia. El consentimiento de importación es un diálogo al que se accede desde el aviso o la entrada de la lista de V5.

La composición seleccionada es la de bandas en contexto de r12 c. Las alternativas son entradas históricas, no pantallas ni entregables adicionales. El HTML canónico conserva los inspectores nativos Vista/Estado/Diálogo/Tema/Movimiento fuera de la estructura del producto. Sus etiquetas, marcador de revisión y avisos de datos de mockup identifican un artefacto de planificación, no requisitos de la interfaz de producción.

## 4. Sistema de diseño y lenguaje visual


Los tokens del proyecto se asignan a los roles semánticos reales del kit; no se agrega una paleta ni una familia tipográfica.

| Fuente del proyecto | Responsabilidad del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--superficie-suave` | grupo local sutil | #faf8fd / #1c1e26 |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--texto` | texto principal | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto complementario | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde accesible de control, alias heredado de los contratos hermanos | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | principal / texto sobre el color principal | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | rol principal al pasar el cursor | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | contorno decorativo / separador | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--exito`, `--exito-suave` | roles de éxito | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | roles de advertencia | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | roles de error | #b23a45, #ffeaec / #ff979f, #43252a |
| `--taller-visor`, `--taller-panel`, `--taller-encima` | contexto existente de la escena del Taller | #ebe7f1, #faf9fc, #f3eefb / #1a1722, #16131d, #231e2e |

Geist Sans y Geist Mono se incorporan desde los recursos WOFF2 locales existentes de Next. Mono se limita al tratamiento heredado de metadatos/marca. Los radios de panel/campo/etiqueta de 32/18/999px y el margen interior de 24px coinciden con los contratos hermanos. El relleno de las bandas es de 28px en escritorio y 20px en teléfono; el del diálogo es de 28px en escritorio y 24px en teléfono. El color identifica la acción principal y los estados reales de guardado/error. No cambia el color de la navegación.

| Eje | Dirección observable |
|---|---|
| concepto | Edición en contexto: abrir una escena dentro de su propia fila, renombrar en la cabecera y desplegar únicamente la explicación o recuperación necesaria. |
| distribución | Una pila de bandas horizontales a todo el ancho. La banda abierta contiene escena y explicación en proporción 1.8:1; no hay panel lateral maestro-detalle ni cuadrícula permanente de tarjetas. |
| navegación | Cabecera y navegación horizontal compartidas; Ver escena/Ocultar escena expande el proyecto en su propio lugar; Abrir lleva al Taller o al modo de solo lectura. Qué se guarda despliega la explicación junto al estado. |
| tipografía | Geist Sans del producto: título de 24px, proyecto de 20px, sección de 16–18px, cuerpo de 14–15px y metadatos de 12–13px. Geist Mono solo para la identificación Sempertex heredada. |
| densidad | Proyectos cerrados en una fila y una única escena abierta. La información secundaria se muestra a demanda; margen interior de 28px en escritorio y 20px en teléfono. |
| componentes | Button/Input/Skeleton/Dialog reales de shadcn y Base UI/Animate UI. Composición propia de bandas expandibles y renombrado en contexto; botones con presión táctil, selector de propietario nativo y disclosure de cuenta heredado. |
| color | Exactamente Pictures: fondo/superficie/texto/acento y tokens Taller para el visor; roles accesibles de borde de control heredados de cuentas-admin y planes. No se agrega una paleta ni una familia tipográfica. |
| movimiento | Asentamiento táctil: las bandas se comprimen a .985 y se asientan con una secuencia de 55ms; la escena pasa de .965→1.008→1; el estado rota de -14°→5°→0; los avisos se asientan verticalmente; presión .965 con spring 220/16; efectos hover en iconos y nombre editable. Expresivo 520/170ms, natural 320/140ms, sutil 160/100ms; la reducción elimina el desplazamiento. |

Componentes reales, con evidencia de importación:

| Nombre del componente | Fuente y uso |
|---|---|
| `shadcn:button default default/hover/focus/pressed/disabled/loading` | `@/components/ui/button`; guardado en la cuenta, importación y copia propia |
| `shadcn:button outline default/hover/focus/pressed/disabled` | La misma importación; vista previa, navegación, reintento y cancelación |
| `shadcn:input text empty/filled/focus/invalid/disabled` | `@/components/ui/input`; búsqueda, nombre en línea y guardado con nombre |
| `shadcn:skeleton record loading` | `@/components/ui/skeleton`; bandas esqueleto de la lista |
| `shadcn:dialog project open/closed/validating/busy` | `@/components/ui/dialog`; diálogo real instalado de Animate UI/Base UI con contención del foco |
| `custom:project-band band collapsed/expanded` | Artículo semántico y botón con aria-expanded/aria-controls; sin atribución inventada a una biblioteca |
| `custom:account-disclosure native closed/open/focus` | details/summary nativos compartidos, con cierre mediante Escape/fuera del componente |
| `custom:owner-filter native all/mine/other` | select nativo con etiqueta; solo para el personal |
| `custom:scene-preview SVG illustrative` | SVG en línea que representa una escena neutral de mockup; no es un renderizador WebGL ni un contrato de miniatura almacenada |
| `kit:motion expressive/natural/subtle active/reduced` | Perfil `@kit/motion`; `motion.button` de `motion/react`, spring de useMotionProfile |
| `kit:planning-controls native selected/focus` | `mountMockup/useMockup` de `@kit/mockup`; selectores nativos de vista/estado/escena/tema/movimiento |


## 5. Navegación y modelo de interacción


La lista abre los proyectos propios en Taller y los proyectos de terceros en modo de solo lectura. Los destinos del producto siguen siendo `/proyectos` para la lista, `/proyectos/[id]` para abrir un proyecto guardado y `/3d` para Taller, según los nombres del brief de UI. El HTML simula la navegación localmente, sin solicitudes de red. Los cambios de vista llevan el foco al H1; los elementos desplegables mantienen el foco en el control que los activa. Los botones de vista previa exponen el estado expandido y un id de destino. El primer guardado y la copia requieren un nombre no vacío después de quitar los espacios al inicio y al final. Escape/cancelar en un diálogo devuelve el foco al control activador exacto que siga disponible; si la vista de origen se reemplazó, se usa como alternativa el nombre, un botón o el H1. Los detalles cerrados ocultan explícitamente su contenido, manteniendo la visibilidad y medición de los elementos desplegables.

La gramática de movimiento es táctil, finita y clara en toda la experiencia. Expresiva usa 520 ms de asentamiento / 170 ms para controles / 55 ms de desfase entre bandas, con cubic-bezier(.34,1.4,.64,1). Natural usa 320/140/30 ms y sutil, 160/100/12 ms. Comportamientos distintivos presentes en el artefacto:

1. La coreografía de carga/vista de las bandas las comprime a .985, las eleva brevemente y las asienta; cada banda posterior tiene un desfase de 55 ms.
2. La escena expandida se asienta desde .965, pasando por 1.008, hasta 1, sin ocultar su texto.
3. Los avisos se asientan con una compresión vertical breve, independiente de la escena.
4. Los iconos del estado de guardado giran de -14° a 5° y luego a cero, y se asientan con una transformación de escala.
5. Los campos de edición en línea se asientan desde scaleX(.96), pasando por 1.01, hasta 1, anclados al borde del texto.
6. Al pasar el cursor por un botón, su icono se eleva; al presionarlo, se comprime a .965. El control de nombre usa el resorte de Motion instalado, con rigidez 220/amortiguación 16 para el modo expresivo.
7. Durante un guardado/importación pendiente, solo gira el icono; la respuesta al teclado sigue siendo un contorno estático de alto contraste.

La preferencia reducida del sistema operativo, Quieto y `?still=1` eliminan el desplazamiento, las transiciones animadas y los giros, conservando todos los estados, controles y palabras de estado. En el producto, las animaciones CSS de pestañas ocultas se pausan; no hay efectos ambientales decorativos persistentes. El movimiento de entrada usa transformaciones sin cambiar el diseño, reducir la opacidad ni cambiar los colores a mitad de la animación.



Reglas adicionales de navegación: al abrir una fila propia, se restauran su nombre y la escena completa; las filas de terceros llevan a V4. El HTML simula estos destinos; en producción, `/proyectos/[id]` debe usar datos autorizados. Volver a la lista, crear una escena, seleccionar una plantilla y abrir una escena de la biblioteca deben pasar por la misma protección ante trabajo pendiente. No se deben reemplazar la escena ni la identidad del proyecto si el guardado falla, entra en conflicto o no se completa. Una escena guardada sin cambios puede continuar directamente. Los destinos del menú de cuenta pertenecen a SP-2/planes; las herramientas contextuales que se conservan en el mockup muestran un aviso de alcance.

El nombre en línea acepta hasta el límite existente de 120 caracteres. Enter/check confirma un nombre no vacío tras quitar los espacios al inicio y al final; Escape/Cancelar restaura el nombre anterior y devuelve el foco. Si el nombre en línea está vacío, se permanece en el modo de edición sin confirmar; los nombres vacíos al guardar por primera vez o al copiar muestran el error explícito de campo en D1/D2. Cambiar el nombre de una escena que nunca se ha guardado no crea un proyecto de cuenta ni habilita el guardado automático. Cambiar el nombre de un proyecto propio ya guardado crea un cambio pendiente y sigue las mismas reglas de guardado/rechazo que las ediciones de escena. Los originales de terceros no tienen control para cambiar el nombre.

## 6. Flujos

**F1 — Primer guardado con nombre y guardado automático (R6).** Crea o abre una escena nueva sin guardar en V3. Muestra “Escena nueva” y “Sin guardar todavía”; no se carga nada a la cuenta. Guardar proyecto abre D1. Cancelar deja intacta la escena; si el nombre queda vacío después de quitar los espacios, D1 permanece abierto con “Escribe un nombre para el proyecto.” Al enviar, se muestra Guardando… y se deshabilita el envío duplicado. Solo la confirmación de la cuenta actual, la identidad del proyecto y la generación de edición enviada puede mostrar “Guardado en tu cuenta”. Las ediciones posteriores se guardan automáticamente; Guardar ahora solicita el mismo guardado protegido. El debounce heredado de 500 ms es un valor técnico predeterminado, no una promesa adicional al usuario. Una confirmación tardía de una generación anterior nunca marca como guardadas las ediciones más recientes.

**F2 — Iniciar un proyecto nuevo (R6).** Escena nueva, una plantilla y Abrir en Escena usan la misma protección. Si un proyecto propio tiene ediciones pendientes, deben guardarse correctamente antes de reemplazarlo; mientras se guarda, el destino queda pendiente. Un fallo, estar sin conexión o un conflicto conserva la escena y bloquea el reemplazo. Una escena que nunca se ha guardado abre D3 con Guardar y continuar, Descartar escena y continuar, y Cancelar (texto visible en el artefacto: “Descartar escena y continuar”). Guardar abre D1 y continúa solo tras la confirmación; descartar explícitamente inicia la escena solicitada sin modificar un original guardado. El resultado es “Escena nueva”, sin identidad de proyecto guardado ni carga hasta el primer guardado con nombre. Salir a Proyectos usa D4 y, después de guardar, continúa al destino solicitado originalmente, en vez de crear una escena nueva.

**F3 — Buscar y volver a abrir (R6).** En otro navegador autenticado, entra a V1 o a V2 autorizada. Busca nombres en toda la colección del servidor a la que se tiene acceso, incluso más allá de la primera página cargada. El filtrado por propietario se aplica antes de la paginación. Cambiar la consulta o el alcance restablece los cursores e ignora las respuestas obsoletas. Cargar más conserva las filas existentes; si falla, muestra el motivo y Reintentar debajo de ellas. La cuenta vacía y una búsqueda sin coincidencias son casos distintos. Abrir restaura el nombre guardado y la escena completa. Los originales de terceros siguen F6. Si un recurso no existe o no está autorizado, se muestra un aviso que no revela información, sin nombres, propietarios ni contenido de escena en caché.

**F4 — Guardados en conflicto (R6).** Una revisión obsoleta produce un conflicto, detiene el guardado automático, conserva la escena local no enviada y muestra Cargar versión del servidor y Guardar una copia. El guardado normal permanece deshabilitado. D5 explica que cargar reemplaza la escena mostrada y conserva el borrador local de recuperación; cancelar deja visible el trabajo local. No se realiza ninguna combinación automática ni sobrescritura silenciosa. D2 para crear una copia propia crea un proyecto separado en la cuenta actual y no escribe sobre el original. Si falla la copia, el trabajo local sigue disponible; solo una copia confirmada se convierte en el proyecto guardado activo.

**F5 — Sin conexión, rechazo y recuperación (R6).** Muestra “Sin guardar · Sin conexión” o “Sin guardar · Error”, conserva la escena y el nombre, y explica cómo reintentar. Reintentar vuelve a Guardando… hasta que se confirme; no se debe dar a entender que una copia de seguridad local del navegador equivale a guardar en la cuenta. Un rechazo del servidor, incluidos los datos no válidos o demasiado grandes y las modificaciones prohibidas, conserva el trabajo pendiente y ofrece instrucciones de recuperación. Si falla la copia de seguridad del navegador, se pide explícitamente al usuario que mantenga la vista abierta y vuelva a intentar la copia. La recuperación limitada a la cuenta ofrece Recuperar borrador; al cargar un borrador recuperado, queda sin guardar/con cambios pendientes. Si la sesión vence, se indica iniciar sesión con la misma cuenta; cambiar de cuenta o de proyecto nunca expone borradores ni comprobantes de otra cuenta. No se ofrece recuperación local entre cuentas.

**F6 — El personal abre un original de terceros (R6).** V2 filtra los propietarios permitidos; Abrir lleva a V4, que muestra el propietario y Solo lectura. No hay herramientas de edición, nombre editable ni acción para guardar el original. Con `taller.usar`, Guardar una copia abre D2, explica el destino y la cuenta actual, indica que el original se conserva, solicita un nombre y crea un proyecto propio tras la confirmación. Sin ese permiso, la acción para copiar no aparece. Volver regresa a la lista autorizada; abrir no transfiere la propiedad.

**F7 — Importar una escena del navegador (R7).** En el primer acceso autenticado con datos sin procesar `taller3d:escena:v1`, V5 ofrece revisar la escena para la cuenta actual. D6 identifica el destino y advierte que los datos de un dispositivo compartido podrían pertenecer a otra persona. Importar a mi cuenta es un consentimiento explícito; Ahora no/Escape cierra el aviso sin cargar ni modificar el origen, y una entrada en la lista permite volver más tarde. Una importación pendiente deshabilita los envíos duplicados. La aceptación crea exactamente un proyecto propio por cuenta/origen sin procesar, incluso si se pierde la respuesta y se reintenta; producción usa la deduplicación existente especificada por cuenta más origen. La confirmación dice “Escena importada”, “Se ha creado un proyecto en tu cuenta” e indica que el original se conserva. Un error permite reintentar de forma segura y descargar el original. Si el JSON no es válido, el esquema no está admitido o los datos son incompatibles, se explica por qué no se importó nada y se ofrece Descargar original sin enviar una importación. El éxito, el rechazo y el fallo conservan el origen sin procesar sin cambios. Otra cuenta recibe su propio consentimiento, no el comprobante de una cuenta anterior. La conversación y las imágenes de IA quedan excluidas explícitamente.

## 7. Especificaciones de vistas

| Vista | Ruta / propósito | Estructura, texto y acciones | Adaptación / flujo |
|---|---|---|---|
| V1 `projects` | `/proyectos`, escenas propias guardadas | Título Proyectos, Escena nueva; Buscar por nombre; entrada para importar desde el navegador; bandas de proyecto de ancho completo que muestran el nombre, Mi cuenta y el estado confirmado de la cuenta; Ver/Ocultar escena, Abrir; Cargar más o estado de reintento/fin. Banda expandida: escena, Escena completa, explicación sobre la persistencia de la escena y el nombre, elemento desplegable Qué se guarda. | La identidad de la banda se mantiene en todos los anchos; el detalle se organiza en columna en el teléfono; F2/F3/F7. |
| V2 `staff` | `/proyectos`, alcance autorizado de todas las cuentas | Vocabulario de V1 más un selector de Propietario con etiqueta: Todas las cuentas, Mi cuenta y propietarios autorizados. Las bandas de terceros muestran el propietario y Solo lectura; la búsqueda abarca esta colección autorizada. El artefacto usa datos de ejemplo neutros de Cuenta de ejemplo en lugar de identidades reales. | Los filtros se ajustan en varias líneas antes de las bandas; F3/F6. |
| V3 `workshop` | `/3d` y destino de edición de un proyecto propio guardado | Contexto existente de Taller; control del nombre de la escena en línea, estado de guardado visible, Qué se guarda, Guardar proyecto o Guardar ahora. Los avisos de error/recuperación/importación aparecen antes del lienzo. Las herramientas existentes siguen siendo contextuales; no se rediseñan. Las entradas del pie de página para crear, usar plantillas y abrir la biblioteca comparten la protección. | El encabezado, el estado y las acciones se ajustan en varias líneas; la escena conserva el ancho disponible; F1/F2/F4/F5/F7. |
| V4 `readonly` | `/proyectos/[id]` de un tercero autorizado | Título del proyecto, propietario y aviso Solo lectura; escena completa; Guardar una copia opcional; explicación sobre los límites del guardado y Volver a proyectos. Sin controles de edición ni para guardar el original. | El aviso y las acciones se ajustan en varias líneas; la escena se adapta al marco; F6. |
| V5 presentación de importación | Aviso contextual en V1/V3; D6, no es una ruta nueva | Escena guardada en este navegador, explicación sobre la cuenta actual y aviso de dispositivo compartido; Revisar importación. Las variantes de inválido/error/éxito conservan el contexto y la opción de recuperación descargando el original. V5 se representa mediante una vista y un estado, no como una quinta opción de Vista. | El aviso y las acciones del diálogo se apilan en el teléfono; F7. |

| Diálogo (`scene`) | Contenido y resultados |
|---|---|
| D1 `first-save` | Guardar proyecto; Nombre del proyecto con etiqueta y el límite existente de 120 caracteres; explicación limitada a la escena y el nombre; Guardar proyecto/Cancelar; error asociado al nombre vacío; Guardando… y envío duplicado deshabilitado. |
| D2 `copy` | Guardar una copia; destino en la cuenta actual y original sin cambios; nombre editable propuesto para la copia; copiar/Cancelar; mismas reglas de validación y espera que D1. |
| D3 `new-scene` | Antes de abrir una escena nueva; explicación sobre el guardado pendiente en la cuenta; Guardar y continuar; opción explícita de descartar solo para una escena nunca guardada; Cancelar. Si el guardado falla, hay un conflicto o sigue pendiente, se impide el reemplazo. |
| D4 `leave` | Título Guardar proyecto en el artefacto seleccionado, explicación sobre el cambio pendiente; Guardar y continuar, opción explícita de descartar solo si nunca se guardó, Cancelar. Si el guardado se completa, continúa al destino solicitado de la lista. |
| D5 `server-version` | Cargar versión del servidor; explica que se conserva el borrador local y se reemplaza la escena mostrada; cargar/Cancelar explícitos; no se combinan las versiones. |
| D6 `import` | Importar escena del navegador; destino en la cuenta actual, aviso de dispositivo compartido, alcance limitado a la escena y conservación del origen sin procesar; Importar a mi cuenta/Ahora no; explicación de error/invalidez y Descargar original; envío pendiente deshabilitado. |

El inspector de escena vacío significa que no hay ningún diálogo. El fondo modal no es interactivo; el foco permanece dentro y luego vuelve al activador que siga disponible (o, después de navegar, al nombre de la escena/encabezado como alternativa). Los controles de guardado/importación en espera impiden acciones duplicadas y reemplazos accidentales mientras se procesa un envío.

El texto de producción en español es la base de SP-4. Las nuevas cadenas pertenecen al archivo planificado `src/components/proyectos/textos-proyectos.ts`; SP-8 es responsable del despliegue de idiomas y la preferencia de cuenta. El control de idioma del mockup ofrece ES/EN para comprobar la expansión del texto; no implementa de nuevo la persistencia del idioma. Los nombres de proyectos son datos y permanecen sin traducir. Los ejemplos están marcados como simulados: nombres neutros de escenas/proyectos/cuentas y un SVG en línea ilustrativo. No es un renderizador WebGL, un campo de miniatura del servidor, una función para generar miniaturas ni evidencia de fidelidad de una escena persistida.

## 8. Estados

Estado nativo expone cada id a continuación; Vista selecciona V1/V2/V3/V4 y Diálogo llega de forma independiente a D1–D6. Los pares de estado/vista solo son válidos según lo indicado; seleccionar un par no relacionado mantiene la superficie normal en lugar de inventar otra regla de negocio. Los diálogos con nombre se pueden inspeccionar de forma independiente, incluida la validación al enviarlos. Los estados y errores se muestran con palabras visibles y roles semánticos de estado/alerta, nunca solo con color.

| Id. de estado | Vista aplicable | Presentación visible, acción disponible y transición |
|---|---|---|
| `normal` | V1–V4 | Bandas de proyectos autorizadas o texto de confirmación del guardado de la cuenta; vista previa/abrir/nombrar/copiar según los permisos. En producción, ningún cambio pendiente se representa como texto guardado. |
| `loading` | V1/V2 | Bandas esqueleto y mensaje cortés Cargando proyectos…; sin resultados ni recuentos inventados. |
| `empty` | V1/V2 | Todavía no tienes proyectos; explica cómo crear y nombrar una escena; Escena nueva sigue siendo la siguiente acción. |
| `no-results` | V1/V2 | No hay coincidencias; prueba otro nombre/propietario; Limpiar búsqueda restablece el alcance permitido de la lista. |
| `next-page` | V1/V2 | Se agregan filas adicionales; el estado final No hay más proyectos desactiva la carga de más resultados. |
| `next-page-error` | V1/V2 | Se conservan las filas existentes; No se cargó la siguiente página y Reintentar aparecen debajo de ellas. |
| `unsaved` | V3 | Escena nueva / Sin guardar todavía; el primer guardado abre D1. Cambiar el nombre por sí solo no crea una identidad guardada. |
| `saving` | V3/D1/D2 | Guardando… y controles de envío ocupados. El guardado o una transición protegida espera; la confirmación debe coincidir con la generación actual del proyecto/cuenta/edición. |
| `offline` | V1/V2/V3 | Lista: Sin conexión y Reintentar. Taller: Sin guardar · Sin conexión, escena conservada y acción para reintentar al conectarse. Sin indicar que se guardó en la cuenta. |
| `error` | V1/V2/V3 | Explicación de que no se pudo cargar/guardar; reintento visible; escena pendiente conservada. En producción, los rechazos de cambios usan este vocabulario de recuperación sin exponer detalles de implementación o seguridad. |
| `conflict` | V3 | Conflicto de guardado; guardado automático detenido y borrador local conservado; acciones para cargar/copiar desde el servidor; Guardar ahora desactivado. |
| `no-taller` | V4 | El original de otra persona sigue siendo legible para quien tenga permiso de lectura total; no aparecen acciones para editar ni copiar. |
| `import-offer` | V1/V3/V5 | Aviso de escena heredada, explicación sobre la cuenta actual/dispositivo compartido y Revisar importación. Sin importación automática. |
| `import-invalid` | V1/V3/D6 | Explicación de datos/versión incompatibles, Ver explicación y Descargar original; D6 no tiene botón para enviar la importación. La fuente no cambia. |
| `importing` | D6 con contexto de V1/V3 | Importando…; las acciones para duplicar la importación y cerrar están desactivadas durante la operación pendiente. Este inspector es una ilustración estática de un estado pendiente, no un trabajo de backend. |
| `imported` | V1/V3/V5 | Escena importada, confirmación de que se creó un proyecto propio y mensaje de conservación del original; Ver proyectos. |
| `import-error` | V1/V3/D6 | Explicación de que no se pudo confirmar; reintento seguro de la importación y descarga del original. Un reintento no crea un proyecto adicional. |
| `recovery` | V3 | Aviso de borrador local asociado a la cuenta, Recuperar borrador; el trabajo recuperado queda pendiente, no guardado en la cuenta. |
| `local-error` | V3 | No pudimos conservar el borrador en este navegador; mantén la vista abierta y Reintentar respaldo. Sin confirmaciones falsas de respaldo o guardado en la cuenta. |
| `permission-denied` | Todas | Rechazo de acceso; sin nombres de proyectos/propietarios ni contenido de escenas; recuperación hacia los proyectos autorizados. |
| `unavailable` | Todas | Proyecto no disponible; recuperación sin revelar información ni metadatos de otra persona. |
| `session-expired` | Todas | Tu sesión ha terminado; instrucciones para iniciar sesión con la misma cuenta, sin exponer datos de escenas/proyectos. |

Los controles también contemplan los estados predeterminado, hover, presionado, foco, desactivado y ocupado. Los nombres no válidos en D1/D2 muestran campos etiquetados con `aria-invalid` y los errores asociados; cancelar conserva el trabajo anterior. Cancelar un cambio de nombre en línea conserva el nombre anterior. El trabajo pendiente/local no enviado es la presentación aplicable para datos obsoletos; el conflicto es la recuperación ante una versión obsoleta del servidor. No hay un estado optimista separado de “guardado”. Los datos de la lista sin conexión no se etiquetan como recién cargados; si producción conserva filas anteriores al actualizar, su estado obsoleto/de carga debe quedar explícito.

No aplicable: cambios de compra/plan, confirmaciones de eliminación/transferencia/historial/fusión, selección masiva, uso compartido público y publicación en la biblioteca global de decoraciones. Quedan fuera de R6/R7. Los diálogos no necesitan una casilla de consentimiento adicional: Importar a mi cuenta y Ahora no son acciones explícitas de aceptación/rechazo. Los estados internos de WebGL, generación de IA, deshacer/rehacer y lista de compras pertenecen a sus superficies existentes; sus controles de maqueta dan contexto y muestran un aviso explicativo de Mockup.

## 9. Comportamiento adaptable

El rango de diseño admitido empieza en 360px; los puntos de control principales de renderizado son 390px para teléfono, 768px para tableta y 1280px para escritorio en ambos temas. La disposición sigue los límites exactos del TSX seleccionado:

- **360–639px:** margen exterior de 20px; encabezado, cuenta e idioma se ajustan en varias líneas; el título y la acción se apilan. La búsqueda y el filtro ocupan todo el ancho. El título/metadatos de la banda preceden a las acciones de vista previa/abrir ajustadas en varias líneas; la escena y luego la explicación se apilan dentro de la misma banda. Relleno del encabezado de la banda: 24px 20px; detalle: 0 20px 24px. Los controles de identidad/nombre/estado/guardado de Taller se ajustan en varias líneas; la barra lateral y el inspector se ocultan, se conserva el contexto de herramientas existente para teléfono. El lienzo permanece dentro del marco de la escena. El ancho del diálogo es el del viewport menos 40px, con relleno de 24px; las acciones se apilan. El desplazamiento vertical permite acceder a todas las acciones.
- **640–1099px:** margen exterior de 24px; el encabezado se ajusta en varias líneas; la barra de búsqueda/filtros pasa a una columna con las acciones alineadas al inicio. La banda expandida tiene una proporción de 1.3:1 y una columna de explicación de 240px como mínimo; el inspector de Taller se oculta, la barra lateral y el lienzo permanecen. No conviertas la lista de proyectos en tarjetas ni en una barra lateral.
- **1100px y más:** margen exterior de 40px dentro de un contenedor máximo de 1520px; la identidad/acciones del encabezado de la banda comparten una fila; el detalle tiene una proporción de 1.8:1, una columna de explicación de 260px como mínimo y un margen/relleno de detalle de 28px. La barra lateral, el lienzo y el inspector de 260px de Taller permanecen visibles. El ancho máximo del diálogo es de 580px, con relleno de 28px.

Los botones tienen una altura mínima de 44px. Los nombres largos y los controles en español/inglés se ajustan en varias líneas, sin desplazamiento horizontal de la página ni truncamiento del motivo del guardado. La altura máxima de los diálogos es la del viewport menos 48px, con desplazamiento vertical interno. El contenido de la página puede desplazarse verticalmente; un viewport corto no justifica ocultar una acción principal. Al ampliar o reorganizar el contenido se aplica la composición estrecha correspondiente. Las interacciones con el lienzo del Taller real no cambian con este contrato.

## 10. Objetivos de accesibilidad

Objetivo: cumplir las WCAG 2.2 AA aplicables; este borrador y las comprobaciones de la maqueta no certifican conformidad. Conserva el orden semántico de los encabezados, el estado de navegación/ruta actual, los artículos de proyectos y los controles etiquetados de búsqueda/propietario/idioma. Cada control tiene un nombre accesible; los iconos/formas SVG decorativos quedan ocultos y las ilustraciones de escenas tienen etiquetas descriptivas en su contenedor. Los botones de vista previa exponen `aria-expanded`/`aria-controls`; los elementos desplegables mantienen la navegación con Enter/Espacio y ocultan el contenido cerrado.

Los campos de nombre tienen etiquetas programáticas. La validación de D1/D2 usa `aria-invalid` y un error asociado, conserva el valor ingresado y mantiene abierta la tarea. El estado de guardado/carga/importación se comunica de forma cortés y dinámica; los errores que requieren acción usan alertas y una acción visible de reintento/recuperación. No anuncies repetidamente texto de guardado automático que no haya cambiado. Los cambios de página/vista trasladan el foco a H1; al alternar elementos desplegables se conserva el foco en el control que los activa. Al confirmar/cancelar el nombre en línea, el foco vuelve al control del nombre. Los diálogos tienen un título/descripción programáticos, fondo inerte, contención del foco del teclado, salida con Escape/cancelar y retorno del foco al control que los abrió; si la navegación elimina ese control, un nombre/botón/H1 de la escena que siga presente sirve como alternativa. Mientras el envío esté pendiente, cerrar no debe provocar que se reemplace la escena ni que se descarte.

El foco tiene un contorno de acento de 3px, con un desplazamiento de 4px; el foco y los bordes de los controles deben alcanzar una relación de contraste ≥3:1 con la superficie adyacente. El texto de cuerpo/apoyo debe alcanzar ≥4.5:1 en ambos temas (mínimo ≥3:1 para texto grande); usa texto-tenue para los bordes de controles significativos y borde decorativo solo para líneas no esenciales. El estado se comunica con texto/icono y color. Los objetivos interactivos de este artefacto tienen una altura mínima de 44px, superior al mínimo aplicable de 24px con separación. La reorganización, el texto ampliado, el acceso en viewports cortos y las etiquetas bilingües deben seguir siendo utilizables.

El movimiento reducido del sistema operativo, Quieto y `?still=1` eliminan los desplazamientos, giros y transiciones, y conservan todas las palabras/acciones; no hay parpadeo ni mensajes que dependan solo de la animación. Los efectos CSS de pestañas ocultas se pausan; no hay animación ambiental intensa. El perfil Motion instalado controla el resorte al presionar el nombre y el movimiento del diálogo del kit. Las comprobaciones de contraste/foco/disposición renderizadas y las pruebas de interacción son evidencia solo para este HTML; el comportamiento con lectores de pantalla, el zoom de 200–400%, el acceso por teclado al WebGL de producción y todas las garantías reales de API/persistencia/seguridad aún requieren sus revisiones de implementación independientes.

## 11. Criterios de aceptación visual y verificación

«Todos» significa el rango compatible de 360px en adelante, verificado al menos en 390/768/1280px cuando corresponda, en los temas claro y oscuro. Quienes inspeccionen deben llegar al estado/vista/cuadro de diálogo indicado; las afirmaciones sobre persistencia funcional requieren evidencia de la integración real de SP-4, no del fixture.

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | Todos | Todos | Se conservan el encabezado de Pictures/Sempertex y el vocabulario compartido de Geist, cuenta y navegación. |
| UI-AC-02 | 1100px+ | V1/V2 normal, expanded | La escena expandida se ubica dentro de su banda de proyecto de ancho completo, con la explicación al lado. |
| UI-AC-03 | 360–639px | V1/V2 normal, expanded | La escena y la explicación se apilan dentro de la misma banda sin desbordamiento horizontal de la página. |
| UI-AC-04 | Todos | V1/V2 normal | La vista previa de la primera banda autorizada aparece expandida inicialmente. |
| UI-AC-05 | Todos | V1/V2 expanded/collapsed | Ver/Ocultar escena actualiza el estado expandido de la banda seleccionada y permite como máximo una vista previa. |
| UI-AC-06 | Todos | V1/V2 loading | La carga muestra bandas esqueleto y el estado Cargando proyectos. |
| UI-AC-07 | Todos | V1/V2 empty | Todavía no tienes proyectos explica cómo crear una escena con nombre y ofrece Escena nueva. |
| UI-AC-08 | Todos | V1/V2 no-results | No hay coincidencias incluye una acción para recuperar los resultados borrando la búsqueda. |
| UI-AC-09 | Todos | V1/V2 next-page-error | Las filas ya cargadas siguen visibles sobre el error de la página siguiente y Reintentar. |
| UI-AC-10 | Todos | V2 normal | El filtro de propietario lleva la etiqueta Propietario y las entradas de otras personas muestran propietario y Solo lectura. |
| UI-AC-11 | Todos | V3 inline rename | El control de nombre se convierte en un campo de entrada en la misma posición del encabezado y devuelve el foco al confirmar o pulsar Escape. |
| UI-AC-12 | Todos | D1/D2 invalid | Si se envía un nombre vacío, el cuadro de diálogo permanece abierto y muestra el error asociado al nombre. |
| UI-AC-13 | Todos | V3 saving | Guardando… permanece visible mientras el guardado está pendiente. |
| UI-AC-14 | Todos | V3 unsaved after F2 | La escena nueva muestra Escena nueva y Sin guardar todavía. |
| UI-AC-15 | Todos | D3/D4 unsaved | Cancelar conserva la escena actual; descartar explícitamente se distingue visualmente de guardar. |
| UI-AC-16 | Todos | V3 conflict | Las acciones para cargar desde el servidor y crear una copia propia aparecen juntas, mientras el guardado normal está deshabilitado. |
| UI-AC-17 | Todos | V3 offline/error | El motivo por el que no se guardó aparece junto al contexto de la escena y ofrece una acción explícita para reintentar. |
| UI-AC-18 | Todos | V4 normal | El original de otra persona no ofrece un nombre editable, herramientas de edición ni la acción para guardar el original. |
| UI-AC-19 | Todos | V4 no-taller | Guardar una copia no está disponible. |
| UI-AC-20 | Todos | D6 import-offer | El destino de la cuenta actual y la advertencia sobre el dispositivo compartido aparecen antes de ofrecer las opciones explícitas de importar o rechazar. |
| UI-AC-21 | Todos | D6 import-invalid | La explicación y la descarga del original están disponibles, sin opción para enviar la importación. |
| UI-AC-22 | Todos | V5 importing | Se muestra el mensaje Importando y el envío duplicado está deshabilitado. |
| UI-AC-23 | Todos | V5 imported | La confirmación de un proyecto indica explícitamente que el original del navegador se conserva. |
| UI-AC-24 | 390/768px | D1–D6 | El contenido del modal permanece dentro del marco de la ventana y se puede acceder a las acciones desplazándose verticalmente. |
| UI-AC-25 | Todos | Keyboard dialogs | Escape/cancelar devuelve el foco al control invocador que siga disponible o al destino de navegación alternativo declarado. |
| UI-AC-26 | Todos | Reduced/Quieto/still | Las palabras de estado y las acciones siguen visibles, sin desplazamientos ni giros. |
| UI-AC-27 | Todos | Expressive normal | Las bandas y vistas previas usan la secuencia elegida, finita, de presión y reposo, sin ocultar contenido. |
| UI-AC-28 | Todos | Permission/session/unavailable | La vista de rechazo no expone metadatos ni escenas de proyectos. |
| UI-AC-29 | 640–1099px | V1/V2/V3 normal | La barra de herramientas se ajusta a varias líneas y el inspector de Taller se oculta, mientras la escena permanece dentro del ancho del contenido. |

La evidencia siguiente corresponde al **HTML canónico reconstruido en esta finalización**, no a la auditoría histórica de la exploración. El TSX seleccionado permaneció idéntico byte por byte; no se necesitó editar el código fuente de comportamiento, agregar alternativas, instalar paquetes, acceder a la red ni modificar producción.

| Verificación | Observación real |
|---|---|
| Kit instalado | `installed=True built=True entries ok=96/96`. |
| Compilación sin conexión actual | Código de salida 0; 648 KB, 2,126 archivos fuente; controles reales de React/shadcn/Animate UI/Base UI con CSS, JS y fuentes locales integrados. |
| `contrast.py` | Código de salida 0: `contrast: 158 pairs checked in light and dark, all pass`. |
| Auditoría renderizada sin conexión | Código de salida 0: 672 renderizados / 672 combinaciones planificadas; 17,388 mediciones de texto y 1,959 paradas de foco a 1280, 390 y 768px en ambos temas. Sin muestreo. |
| Recorrido de interacciones específicas | Código de salida 0: `INTERACTIONS: PASS 17 groups`; cero errores de página y cero solicitudes HTTP(S) externas. Abarca inspectores nativos, búsqueda con teclado, vista previa única, filtro de propietario/reinicio de paginación, reintento de página, confirmación/cancelación con Escape/restauración del foco en el cambio de nombre en línea, validación del primer guardado/estado pendiente/confirmación, conflicto con copia/foco del modal, reintento sin conexión, permisos de solo lectura/copia para originales ajenos, restricción de plantillas, importación no válida/descarga/Escape, rechazo/aceptación explícitos, bloqueo ante guardado pendiente, navegación a la lista después de guardar y textos en inglés. |
| Pruebas de movimiento | A los 120ms: 3 animaciones expresivas activas; 0 con movimiento reducido del sistema operativo; 0 con `?still=1`. |
| Inspección visual | Se inspeccionaron capturas en memoria: bandas de proyectos en tema oscuro a 1280px, Taller en tema claro a 1280px, conflicto en tema oscuro a 390px y diálogo de importación no válida en tema claro a 390px. No se escribieron archivos de captura. |

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Comandos necesarios para reproducir (las rutas absolutas son intencionales):

```text
python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components status
python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.r12.dir-c.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html
python3 /home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/proyectos@v1.html --widths 1280,390,768 --max-combos 240
```

Las pruebas de sondeo opcionales se ejecutaron como scripts de Playwright en línea, sin guardar artefactos de prueba. En pruebas anteriores hubo un error tipográfico en una expresión de diagnóstico, un selector ambiguo de control de plantilla y una aserción inmediata antes de que terminara de cerrarse el diálogo; se corrigieron las expresiones, el selector y la espera, sin modificar el HTML/TSX. El comando final, que consolidó los 17 grupos, terminó correctamente. Estas verificaciones respaldan el comportamiento renderizado de este artefacto de planificación; no lo aprueban ni demuestran que el almacenamiento o la seguridad de producción cumplan los requisitos.

## 12. Preguntas abiertas y supuestos

**Preguntas abiertas sobre el producto:** ninguna impide finalizar según el brief proporcionado y la dirección elegida por el propietario. La nota de r12 preguntaba si la primera vista previa debía aparecer expandida; esta finalización conserva exactamente esa composición visible seleccionada, según las instrucciones. Es un supuesto de presentación que se mantiene, no una afirmación de que el propietario haya respondido esa pregunta por separado. Cualquier cambio posterior debe ser una enmienda explícita al borrador, no una decisión del implementador.

**Decisiones confirmadas:** primero se guarda explícitamente con nombre y luego se activa el guardado automático; identidad de proyecto nuevo que nunca se guardó; el mismo bloqueo para Escena nueva/plantillas/Abrir en Escena; estado de revisión actual confirmado por el servidor; los conflictos conservan el trabajo local; el original ajeno es de solo lectura y la copia depende de Taller; solo se sincronizan el nombre y la escena completa; importación sin pérdida para la cuenta actual, con reintento seguro y explícito. Estas decisiones provienen de SPEC/brief y no se reabren.

**Límites del fixture / responsables del seguimiento:** los tiempos de guardado/importación, el filtrado, la ilustración de escenas y las transiciones usan datos simulados en memoria. El archivo descargado `escena-original.mock.json` demuestra un control de recuperación; no permite recuperar realmente datos heredados. Este artefacto no implementa ni demuestra backend, almacenamiento, validación atómica de revisiones, idempotencia, consulta del conjunto completo desde el servidor, fidelidad de escenas entre navegadores, aplicación real de permisos ni aislamiento de borradores al cambiar de cuenta. T4.2–T4.7 y las revisiones independientes son responsables de esas verificaciones. El HTML actual conserva la procedencia del título/pie de página de r12 y los marcadores contextuales de herramientas existentes; ninguno es texto de producción. La simulación de diseño ES/EN no implica que todo el producto esté traducido ni que la selección de idioma se guarde. No se genera un directorio de vista previa.

**CONSIDERACIONES:** `RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`. No hay bloqueos de alternativas ni de la cadena de herramientas. El artefacto sigue siendo un borrador sin aprobar; aquí no se verifican el comportamiento de producción ni la aceptación independiente. La primera vista previa inicialmente expandida se mantiene de la composición seleccionada, como se explicó arriba.

**Aprobación:** David o el aprobador independiente deben aprobar este borrador exacto mediante el flujo de planificación antes de que T4.1 lo copie para su consumo. La persona de diseño no otorga la aprobación. La finalización canónica está completa; la implementación y la aceptación independiente siguen a cargo de las tareas asignadas.

### Identidad de entradas y artefactos

| Entrada / artefacto | SHA-256 |
|---|---|
| `SPEC.md` | `7f99f01dd99318864a66f99d85902e4b3de4b07ab0694b873125aee8a8331660` |
| `PLAN.json` | `63c04b811e851a3b056671e9c26e999228c6bb91c84bddf3497c91be8d109462` |
| `design/proyectos@v1.r12.behavior.md` | `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65` |
| `design/proyectos@v1.r12.dir-c.md` | `880305b825c2859e469a88965c336f2c60aff7f1018f01e901bdb2a9e0321186` |
| `design/proyectos@v1.r12.dir-c.tsx` | `4de35ec0f1c7fbe4964d4d3b9c706dd96b721137ab503ddc32a3e6464c729b4f` |
| `design/proyectos@v1.r12.dir-c.html` | `403ac3672d0c14edf9f280ba26368b971bc09ce8227acd9ea9649db9236b465f` |
| `design/proyectos@v1.html` | `906852d5a0d4d04bd724e05302eab6ade35e65eae40ee2ebf4b230ed36b1a0b6` |
