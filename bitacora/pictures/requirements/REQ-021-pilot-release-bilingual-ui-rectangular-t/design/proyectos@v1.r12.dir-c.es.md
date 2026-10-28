---
contract: proyectos
version: 1
status: draft
subplan: SP-4
requirements: [R6, R7]
owner: David
author: Designer
date: 2026-10-28
direction: c
name: Edición en contexto
source_revision: r12
source_behavior: proyectos@v1.r12.behavior.md
---

# Edición en contexto — proyectos@v1 · r12 · C

## 1. Identidad y trazabilidad

**Solo exploración; borrador, no aprobado ni contrato de implementación.** Esta nota específica de la dirección acompaña el TSX, el HTML autocontenido, las dos composiciones candidatas y el JSON de ejes. No reemplaza ni modifica los archivos canónicos proyectos@v1.md / .html, ninguno de los contratos de elementos hermanos, SPEC ni PLAN. El propietario selecciona una dirección; un finalizador independiente escribe el par canónico después de la selección.

Alcance conductual: `proyectos@v1.r12.behavior.md`, R6/R7 y SPEC «Behavior — SP-3 and SP-4 (round 9 answered)». Consumidores, si se selecciona esta dirección y se aprueba de forma independiente: SP-4 T4.1 copia el artefacto aprobado, T4.4 implementa las vistas de lista/guardado/conflicto/solo lectura/escena nueva, T4.5 implementa la importación, T4.8 revisa la fidelidad del renderizado. Ningún otro subplan adquiere una dependencia de interfaz de usuario solo por consumir la identidad del proyecto. Compatibilidad con r11 C: **refinamiento compatible**; se conservan el contenedor, la jerarquía, la gramática de movimiento y los requisitos conductuales, con reinicio corregido de la paginación local y recuperación del foco del teclado. Compatibilidad con la maqueta canónica anterior no aprobada: **cambio incompatible de composición visual**, porque el despliegue de la lista, la jerarquía y la edición en línea requieren implementación y revisión; las reglas de persistencia/propiedad del producto no cambian. La compatibilidad con una implementación de producción aprobada es indeterminada; no se afirma que exista.

Fuentes inspeccionadas en modo de solo lectura en t12 y asesor: `src/app/globals.css`, `layout.tsx`, `/3d/page.tsx`, `Taller3D.tsx`, la lógica local de guardado de escenas y la navegación del contenedor. El guardado local actual usa una escena del navegador y un debounce de 500ms; no persiste en la cuenta. Los archivos canónicos Markdown/HTML de cuentas-admin y planes de elementos hermanos, junto con su TSX seleccionado, establecen el encabezado compartido de cuenta, el control de idioma, el desplegable de cuenta, la navegación horizontal neutra, Geist y el vocabulario de radios amplios. Las solicitudes anteriores de paletas/tipografías independientes ceden ante el alcance explícito de sistema de producto fijo de esta delegación.

R12 conserva la dirección de r11 porque el brief conductual de r12 es idéntico byte por byte al de r11. Primero se reconstruyen las dos miniaturas con componentes reales instalados; se conserva la composición elegida de despliegue en línea más sólido. Esta revisión corrige el reinicio de paginación del fixture de maqueta al cambiar la búsqueda/el propietario y la devolución del foco después de confirmar/cancelar un nombre en línea, sin modificar el alcance conductual aceptado. Solo se escriben los archivos asignados y específicos de la revisión, y el RESULT requerido de la delegación. No se editan repositorios de producción. No se realizan instalaciones de paquetes, descargas de red, inicio de servidores, commits, ediciones del plan ni aprobaciones.

## 2. Propósito y usuarios

La lista responde «¿Qué escena guardada quiero continuar?». El encabezado de edición responde «¿Cómo se llama este proyecto y estos cambios se guardaron en mi cuenta?». La escena permanece en contexto mientras la persona edita su nombre, revisa los límites del guardado o resuelve un error.

Los propietarios guardan, buscan, vuelven a abrir y continúan sus proyectos. Los empleados/administradores autorizados buscan entre los propietarios a los que tienen permiso de acceder y leen los originales de otras personas. Copiar requiere permiso para usar Taller y crea un proyecto propio; nunca edita ni transfiere el original. El acceso de solo lectura sin permiso para usar Taller tiene su propia presentación accesible y no incluye controles para copiar/editar. Una persona que inicia sesión en un navegador compartido da su consentimiento explícito antes de importar contenido heredado.

## 3. Arquitectura de la información y enfoque

Conservar el encabezado de Pictures/Sempertex, los controles de idioma/cuenta y la línea horizontal neutra de navegación de las vistas hermanas. Proyectos incorpora dos destinos de navegación, Taller 3D y Proyectos, porque el encargo de proyectos guardados los requiere; no se trata de un nuevo modelo global de navegación. El Taller conserva la barra de herramientas de escena, la barra lateral de paneles, el vocabulario del inspector de escena/IA, deshacer/rehacer y los controles contextuales existentes de fotografía y lista de compras.

**Cambio específico de esta propuesta:** los proyectos son franjas desplegables de ancho completo, no una tabla permanente, una cuadrícula de tarjetas ni una barra lateral maestra/detalle. Al abrir “Ver escena”, la escena aparece dentro de la franja de ese proyecto. El nombre, el propietario y la acción de abrir permanecen en su línea original. Se muestra como máximo una vista previa a la vez. “Qué se guarda” muestra la explicación sobre el almacenamiento local y en la cuenta en el lugar donde se necesita. En el Taller, el nombre editable se convierte en el campo etiquetado; Enter/la marca de verificación confirma y Escape cancela. Los controles nuevos usan una respuesta visual al presionarlos y al soltarlos, en lugar de introducir una nueva identidad visual.

Primero se dibujaron dos miniaturas HTML:

- **Candidata 1, elegida:** franja de proyecto de ancho completo con vista previa en línea y explicación adyacente sobre los límites del guardado. Conserva la identidad del proyecto y la alineación de las acciones, mientras la divulgación progresiva modifica la densidad.
- Candidata 2: paneles de dos columnas que priorizan la escena. Es una composición válida dentro del sistema, pero repite las vistas previas grandes y pierde la relación directa de la primera candidata entre la fila cerrada y su estado abierto.

La maqueta completa desarrolla la candidata 1. Ambas miniaturas siguen siendo composiciones ilustrativas; ninguna es el artefacto interactivo completo. Las dos miniaturas HTML y el HTML completo se construyen sin conexión con componentes reales instalados. El HTML principal conserva los selectores de inspección nativos Vista/Estado/Diálogo/Tema/Movimiento. No hay una alternativa HTML provisional.

## 4. Sistema de diseño fijo y ocho ejes

Los tokens del proyecto se asignan a los roles semánticos reales del kit; no se introduce una paleta ni una familia tipográfica nuevas.

| Fuente del proyecto | Responsabilidad del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, menú emergente | #ffffff / #16181f |
| `--superficie-suave` | grupo local sutil | #faf8fd / #1c1e26 |
| `--superficie-2` | secundario, atenuado, acento | #efe9f8 / #242733 |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto de apoyo | #6b6178 / #9aa1ad |
| `--texto-tenue` | borde accesible de control, alias heredado de la vista relacionada | #766c85 / #8a91a0 |
| `--acento`, `--sobre-acento` | primario / texto sobre el primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | rol de hover del primario | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | contorno decorativo / divisor | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--exito`, `--exito-suave` | roles de éxito | #1f7a55, #dcf5e9 / #78d6a8, #173b31 |
| `--aviso`, `--aviso-suave` | roles de advertencia | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | roles de error | #b23a45, #ffeaec / #ff979f, #43252a |
| `--taller-visor`, `--taller-panel`, `--taller-encima` | contexto existente de la escena del taller | #ebe7f1, #faf9fc, #f3eefb / #1a1722, #16131d, #231e2e |

Geist Sans y Geist Mono se integran desde los recursos WOFF2 locales existentes de Next. Mono se limita al tratamiento heredado de metadatos y marca denominativa. Los radios de panel/campo/píldora de 32/18/999px y el margen interior de 24px coinciden con las vistas relacionadas. El relleno de la banda es de 28px en escritorio y 20px en teléfono; el relleno del diálogo es de 28px en escritorio y 24px en teléfono. El color identifica la acción principal y los estados reales de guardado/error. No cambia el color de la navegación de rutas.

| Eje | Dirección observable |
|---|---|
| concepto | Edición en contexto: abrir una escena dentro de su propia fila, renombrar en la cabecera y desplegar únicamente la explicación o recuperación necesaria. |
| layout | Una pila de bandas horizontales a todo el ancho. La banda abierta contiene escena y explicación en proporción 1.8:1; no existe un panel maestro-detalle lateral ni una cuadrícula permanente de tarjetas. |
| navigation | Cabecera y navegación horizontal compartidas; Ver escena/Ocultar escena expande el proyecto en su propio lugar, Abrir lleva al Taller o a solo lectura. Qué se guarda despliega la explicación junto al estado. |
| typography | Geist Sans del producto: título 24px, proyecto 20px, sección 16–18px, cuerpo 14–15px, metadatos 12–13px. Geist Mono solo en la identificación Sempertex heredada. |
| density | Proyectos cerrados de una fila y una única escena abierta. La información secundaria se revela a demanda; 28px de margen interior en escritorio y 20px en teléfono. |
| components | Button/Input/Skeleton/Dialog reales de shadcn y Base UI/Animate UI. Composición propia de bandas expandibles y renombrado in situ; botones con presión táctil, selector de propietario nativo y disclosure de cuenta heredado. |
| colour | Exactamente Pictures: fondo/superficie/texto/acento y tokens Taller para el visor; roles accesibles de borde de control heredados de cuentas-admin y planes. No hay nueva paleta ni familia tipográfica. |
| motion | Asentamiento táctil: las bandas se comprimen .985 y se asientan con una secuencia de 55ms; la escena pasa de .965→1.008→1; el estado rota de -14°→5°→0; los avisos se asientan verticalmente; presión .965 con spring 220/16; hover en iconos y nombre editable. Expresivo 520/170ms, natural 320/140ms, sutil 160/100ms; reducción sin desplazamiento. |

Componentes reales, con evidencia de importación:

| Nombre del componente | Fuente y uso |
|---|---|
| `shadcn:button default default/hover/focus/pressed/disabled/loading` | `@/components/ui/button`; guardado de cuenta, importación y copia propia |
| `shadcn:button outline default/hover/focus/pressed/disabled` | Mismo import; vista previa, navegación, reintento y cancelación |
| `shadcn:input text empty/filled/focus/invalid/disabled` | `@/components/ui/input`; búsqueda, nombre en línea y guardado con nombre |
| `shadcn:skeleton record loading` | `@/components/ui/skeleton`; bandas esqueleto de la lista |
| `shadcn:dialog project open/closed/validating/busy` | `@/components/ui/dialog`; diálogo real instalado de Animate UI/Base UI con confinamiento del foco |
| `custom:project-band collapsed/expanded` | Artículo semántico y botón con aria-expanded/aria-controls; sin atribución inventada a una biblioteca |
| `custom:account-disclosure closed/open/focus` | details/summary nativos compartidos, con cierre mediante Escape o clic fuera |
| `custom:owner-filter native all/mine/other` | Select nativo etiquetado; solo para el personal |
| `custom:scene-preview illustrative` | SVG en línea que representa una escena neutra de ejemplo; no es un renderizador WebGL ni un contrato de miniatura almacenada |
| `custom:motion profile/reduced` | Perfil `@kit/motion`; `motion.button` de `motion/react`, spring de useMotionProfile |
| `custom:planning-controls` | `mountMockup/useMockup` de `@kit/mockup`; selectores nativos de vista/estado/escena/tema/movimiento |

## 5. Navegación, interacción y movimiento

La lista abre los proyectos propios en Taller y los proyectos de otras personas en la vista de solo lectura. Los destinos del producto siguen siendo `/proyectos` para la lista, `/proyectos/[id]` para abrir un proyecto guardado y `/3d` para Taller, tal como se nombran en el brief de interfaz de usuario. El HTML simula la navegación localmente, sin solicitudes de red. Los cambios de vista enfocan H1; los elementos desplegables mantienen el foco en el control que los activa. Los botones de vista previa exponen el estado expandido y un id de destino. El primer guardado y la copia requieren un nombre recortado que no esté vacío. Escape/cancelación en el diálogo devuelven el foco al control exacto que lo invocó y que aún exista; hay un respaldo de nombre/botón/H1 si se reemplazó la vista de origen. Los detalles cerrados ocultan explícitamente sus cuerpos, preservando la visibilidad y medición del elemento desplegable.

La gramática del movimiento es táctil, acotada y legible en todo momento. El perfil expresivo usa 520ms para asentarse / 170ms para controles / desfases de 55ms entre bandas con cubic-bezier(.34,1.4,.64,1). El perfil natural usa 320/140/30ms y el sutil 160/100/12ms. El artefacto presenta estos comportamientos diferenciados:

1. La secuencia de carga/cambio de vista de las bandas se comprime a .985, se eleva brevemente y se asienta; cada banda posterior tiene un desfase de 55ms.
2. La escena expandida se asienta desde .965, pasa por 1.008 y llega a 1 sin ocultar su texto.
3. Los avisos se asientan con una breve compresión vertical, independiente de la escena.
4. Los íconos de estado de guardado rotan de -14° a 5° y luego a cero, con una estabilización de escala.
5. Los campos de edición en línea se asientan desde scaleX(.96), pasan por 1.01 y llegan a 1, anclados al borde del texto.
6. Al pasar el puntero sobre el botón, su ícono se eleva; al presionarlo, se comprime a .965. El control del nombre usa el resorte de Motion instalado, stiffness 220/damping 16 en el perfil expresivo.
7. El guardado/la importación pendientes muestran un ícono giratorio solo mientras están pendientes; la respuesta del teclado conserva un contorno estático de alto contraste.

La preferencia de reducción de movimiento del sistema operativo, Quieto y `?still=1` eliminan el desplazamiento, las transiciones animadas y los giros, sin quitar ningún estado, control ni palabra de estado. En el producto, las animaciones CSS se pausan cuando la pestaña está oculta; no hay ningún efecto ambiental decorativo persistente. El movimiento de entrada usa transformaciones sin cambios de diseño, reducción de opacidad ni cambios de color durante la animación.

## 6. Flujos e invariantes de comportamiento

1. **Primer guardado:** escena nueva → «Sin guardar todavía» → Guardar proyecto → diálogo de nombre → validación o Guardando… → solo una revisión actual confirmada indica Guardado en tu cuenta. Las ediciones posteriores se guardan automáticamente; Guardar ahora sigue disponible fuera de los estados pendiente/conflicto. Las respuestas de producción reconocen únicamente la generación e identidad que enviaron.
2. **Proyecto nuevo:** Escena nueva, plantilla y Abrir en Escena comparten la misma transición. Un proyecto guardado primero completa el guardado pendiente; una escena sin guardar pide confirmación antes de descartarse. Un fallo/conflicto conserva la escena y bloquea el reemplazo. La escena nueva se llama Escena nueva, no tiene identidad guardada y no se carga hasta su primer guardado con nombre. No se agrega una nueva interfaz de eliminación ni de historial.
3. **Reapertura:** buscar en toda la colección autorizada, usar el filtro de propietario solo cuando esté permitido, conservar las filas visibles si falla la página siguiente y reabrir la escena completa. Los cambios de filtro restablecen la paginación; las respuestas tardías no deben reemplazar la consulta actual. Estos son requisitos de producción, no afirmaciones sobre la búsqueda sincrónica del fixture del mock.
4. **Conflicto:** una escritura obsoleta detiene el guardado automático, conserva la escena local y muestra Cargar versión del servidor / Guardar una copia. Al cargar la versión del servidor se confirma qué escena se mostrará y se mantiene disponible el borrador local de recuperación. Al guardar una copia propia se solicita su nombre y nunca se actualiza el documento ajeno/original.
5. **Sin conexión/fallo:** mostrar Sin guardar con el motivo y la opción de reintentar; un reintento muestra Guardando… hasta recibir confirmación. Si falla una copia de seguridad local, se pide a la persona que mantenga la vista abierta y vuelva a intentarla. Si se pierde la autenticación, no se muestra metadata del proyecto y se indica recuperar el acceso mediante la misma cuenta.
6. **Original ajeno:** aviso de solo lectura con escena y propietario; sin nombre editable, herramientas de escena ni acción para guardar sobre el original. Con permiso de Taller, Guardar una copia abre un diálogo explícito para crear una copia propia; sin ese permiso, la acción de copia no aparece.
7. **Importación heredada:** la primera entrada autenticada al Taller ofrece revisar los datos de la cuenta actual, advierte sobre dispositivos compartidos y explica el límite de solo escena. La importación es explícita, segura ante reintentos y crea exactamente un proyecto propio aunque se pierda la respuesta y se reintente. Ahora no conserva el original y la lista ofrece una forma de volver a importar. Los datos inválidos/desconocidos incluyen una explicación y la descarga del original sin procesar. El éxito, la negativa o el fallo nunca modifican ni borran el origen del navegador. Otra cuenta recibe una nueva solicitud de consentimiento, nunca un comprobante ni borrador anterior.

Solo el nombre y la escena completa se transfieren entre navegadores. La conversación con IA y las imágenes generadas permanecen locales. No se incorpora una interfaz de combinación, eliminación, transferencia, uso compartido público ni historial de versiones. Estos invariantes siguen siendo obligatorios cuando quien finalice/implemente adopte una dirección.

## 7. Especificaciones de vistas y diálogos

| Vista del inspector | Superficie y jerarquía | Acción principal / detalle progresivo |
|---|---|---|
| `projects` | Búsqueda de proyectos propios, acceso para recuperar importaciones y pila de bandas de proyectos | Escena nueva; Abrir por fila; Ver/Ocultar escena; Qué se guarda |
| `staff` | La misma superficie compartida más un filtro de propietario etiquetado | Abrir una escena propia o ajena autorizada; distinción clara de propietario/solo lectura |
| `workshop` | Contexto existente del Taller, nombre de escena, estado de guardado en la cuenta y panel contextual de fallos | Nombre en el lugar, primer guardado explícito/Guardar ahora, explicación del guardado local y recuperación ante fallos |
| `readonly` | Aviso de propietario ajeno/solo lectura y contexto completo de la escena | Copia propia solo con permiso de Taller; volver a la lista permitida |

La vista previa de la escena es un SVG ilustrativo neutro, etiquetado «Vista de escena · Mockup». No se propone un nuevo campo de miniatura en el servidor, un trabajo de generación de capturas ni contenido persistente adicional del proyecto.

| Diálogo del inspector (`scene`) | Contenido y resultados |
|---|---|
| empty | Sin diálogo |
| `first-save` | Campo para guardar con nombre, validación, explicación del límite de solo escena, guardar/cancelar |
| `copy` | Nombre de la copia propia, explicación de que se conserva el original, guardar/cancelar |
| `new-scene` | Guardar antes de reemplazar; descartar sin guardar o cancelar de forma explícita; el fallo del guardado muestra el motivo |
| `leave` | Conservar el trabajo pendiente antes de navegar a la lista de proyectos; el guardado continúa hacia el destino solicitado originalmente |
| `server-version` | Explicación explícita de la carga del servidor y conservación del borrador local; cancelar |
| `import` | Destino en la cuenta actual, importación o rechazo explícitos, advertencia sobre dispositivos compartidos; recuperación de datos inválidos/error y descarga del original |

## 8. Estados alcanzables

El selector nativo Estado permite acceder a todos los estados siguientes. Los estados se aplican a la superficie indicada; las combinaciones no relacionadas conservan la superficie normal en lugar de introducir comportamientos de negocio nuevos. El selector Diálogo permite acceder por separado a todos los diálogos desde cualquier vista. Los controles nativos están fuera del contenedor del producto y conservan la etiqueta Mockup.

| Id. del estado | Vista pertinente | Resultado visible / recuperación |
|---|---|---|
| `normal` | Todas | Resultados autorizados o texto de confirmación al guardar la cuenta |
| `loading` | Lista | Bandas de esqueleto y estado de carga anunciado de forma cortés |
| `empty` | Lista | Sin proyectos guardados; acción existente Escena nueva y breve paso siguiente |
| `no-results` | Lista | Aviso explícito de que no hay coincidencias y acción para borrar la búsqueda |
| `next-page` | Lista | Más filas de muestra y control deshabilitado al final de la lista |
| `next-page-error` | Lista | Las filas ya cargadas permanecen visibles; motivo del error al cargar la página siguiente y opción para reintentar |
| `unsaved` | Taller | Escena nueva / Sin guardar todavía; se requiere el primer guardado con nombre |
| `saving` | Taller | Guardando… con control en estado pendiente; no se afirma que los datos se hayan guardado |
| `offline` | Lista/Taller | Error de consulta o escena sin guardar; opción explícita para reintentar y la escena permanece |
| `error` | Lista/Taller | Error al cargar o guardar, explicación recuperable y opción para reintentar |
| `conflict` | Taller | Guardado automático detenido; escena local conservada; panel para cargar la versión del servidor o copiar |
| `no-taller` | Solo lectura | Escena ajena disponible para lectura, sin acciones para editar ni copiar |
| `import-offer` | Lista/Taller | Acceso para revisar una escena heredada con explicación sobre la cuenta actual |
| `import-invalid` | Lista/Taller/diálogo de importación | Explicación de datos incompatibles, descarga de muestra sin modificar y sin opción para confirmar la importación |
| `importing` | Contexto/diálogo de importación | Estado de importación y confirmación duplicada deshabilitada |
| `imported` | Lista/Taller | Confirmación de un proyecto y mensaje de que se conserva el original |
| `import-error` | Lista/Taller/diálogo de importación | Confirmación fallida que se puede reintentar de forma segura, además de la descarga del original |
| `recovery` | Taller | Borrador de recuperación disponible en la cuenta |
| `local-error` | Taller | Error de copia de respaldo; permanece en la vista y permite reintentarla |
| `permission-denied` | Todas | Acceso rechazado sin revelar nombres de proyectos, propietarios ni metadatos de escenas |
| `unavailable` | Todas | Vista de proyecto no disponible que no revela información |
| `session-expired` | Todas | Indicaciones para iniciar sesión o recuperar el acceso con la misma cuenta, sin datos de la escena |

Los controles también muestran los estados normal, hover, foco y pulsado, así como el comportamiento de validación y deshabilitado/ocupado. La importación no requiere una casilla: las acciones distintas y explícitas Importar a mi cuenta y Ahora no permiten aceptar o rechazar sin una casilla de consentimiento redundante.

## 9. Comportamiento adaptable

- **360–639px:** margen exterior de 20px; los controles de encabezado, idioma y cuenta se ajustan a varias líneas; el título y la acción se apilan; la búsqueda y los filtros ocupan todo el ancho; la vista previa aparece debajo de los controles de fila y la explicación debajo de la escena; los controles de nombre, estado y guardado de Taller se ajustan a varias líneas, y el riel de paneles existente y el inspector se contraen para mostrar el contexto de herramientas del teléfono; los diálogos ocupan el ancho de la ventana menos 40px y tienen relleno de 24px. Las acciones tienen una altura mínima de 44px. El desplazamiento vertical es intencional; no se permite el desplazamiento horizontal de la página.
- **640–1099px:** margen exterior de 24px; los filtros se ajustan encima de la lista; la banda expandida conserva la escena y su explicación cuando hay espacio; el inspector de Taller se contrae y conserva la escena principal y el riel. Los controles nativos de cuenta y encabezado se ajustan a varias líneas sin cambiar la semántica de navegación.
- **1100px en adelante:** margen exterior de 40px, contenedor compartido con ancho máximo de 1520px; bandas de proyectos a todo el ancho; proporción de 1.8:1 entre escena y explicación; contexto existente de escena, riel e inspector visible.

Las comprobaciones visuales incluyen 390, 768 y 1280px. Las comprobaciones renderizadas adicionales en 360 y 1024px verifican el reflujo de la lista en ambos temas. El selector de idioma compartido de la maqueta admite la expansión al inglés; los nombres de proyectos de muestra son datos, no identidades traducidas.

## 10. Objetivos de accesibilidad y límites de verificación

El objetivo es cumplir los criterios WCAG 2.2 AA aplicables, sin afirmar certificación. Se incluyen encabezados, artículos y navegación semánticos, nombres programáticos y anuncios de estado y error; Enter/Espacio activan botones y controles de expansión. Los campos para guardar con nombre tienen etiquetas asociadas, además de aria-invalid y una descripción del error. Los diálogos usan el fondo inerte y la contención del foco del componente modal instalado. Escape devuelve el foco al control que abrió el diálogo. El foco usa un contorno de acento del producto de 3px, separado por 4px. Los bordes de los controles usan el alias accesible texto-tenue del elemento hermano en lugar del token decorativo de divisor. El contraste del texto es de 4.5:1 y el de los bordes de controles y el foco, de 3:1 en ambos temas. El movimiento reducido conserva la información y las acciones.

Esta es una muestra de planificación: la sincronización de guardado/importación, las coincidencias y el filtrado por propietario, y las transiciones son simulaciones en memoria. El JSON descargado se identifica explícitamente como `escena-original.mock.json`; muestra la interfaz de recuperación, no la recuperación de datos del usuario. Aquí no se implementa ni verifica almacenamiento/API, comprobación atómica de revisiones, idempotencia, fidelidad de escenas entre navegadores, búsqueda en el servidor de colecciones completas, autenticación ni aislamiento real al cambiar de cuenta. Los controles existentes de foto, compras y herramientas muestran un aviso de alcance Mockup; se conservan como contexto, no se rediseñan ni implementan. El comportamiento real corresponde a las tareas de implementación e integración del plan.

## 11. Criterios de aceptación observables y evidencia verificable

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | 360–1280px | Todos | La cabecera de Pictures/Sempertex, la tipografía Geist y el vocabulario compartido de cuenta/navegación siguen siendo reconocibles; no aparece una paleta nueva. |
| C-AC-02 | 1100px+ | Lista normal | Una escena expandida está dentro de la franja de ancho completo de su proyecto, con la identidad/acciones arriba y la explicación del guardado a su lado. |
| C-AC-03 | 360–639px | Lista normal | La escena y la explicación se apilan dentro de la misma franja, sin desbordamiento horizontal. |
| C-AC-04 | Todos | Lista expandida/contraída | Ver/Ocultar escena cambia solo la franja seleccionada y expone aria-expanded; otra franja puede reemplazar la vista previa abierta. |
| C-AC-05 | Todos | Cargando/vacío/sin resultados | Cada estado de lista identificado muestra una respuesta visible distinta y un siguiente paso ejecutable; la carga usa franjas esqueléticas. |
| C-AC-06 | Todos | Error en página siguiente | Las filas cargadas previamente permanecen visibles mientras el error de la página siguiente y la acción Reintentar aparecen debajo. |
| C-AC-07 | Todos | Lista del personal | Solo la vista del personal expone el filtro de propietario; las entradas ajenas muestran el propietario y el texto Solo lectura. |
| C-AC-08 | Todos | Renombrado en línea en Taller | El control del nombre de la escena se convierte en una entrada etiquetada en la posición actual de su encabezado; confirmar/Escape mantiene el contexto. |
| C-AC-09 | Todos | Primer guardado no válido | Los nombres vacíos muestran el error asociado al campo y mantienen abierto el diálogo. |
| C-AC-10 | Todos | Guardando/guardado | Guardando… permanece visible hasta la confirmación; no se muestra el texto de guardado si el trabajo está pendiente. |
| C-AC-11 | Todos | Escena nueva | Los tres puntos de entrada para crear producen Escena nueva con Sin guardar todavía después de proteger las ediciones anteriores. |
| C-AC-12 | Todos | Conflicto | El panel de error muestra las acciones para cargar desde el servidor y conservar una copia propia; se detiene el guardado normal. |
| C-AC-13 | Todos | Sin conexión | Sin guardar y el motivo de la desconexión permanecen junto al contexto del proyecto, con una opción explícita para reintentar. |
| C-AC-14 | Todos | Original ajeno | No hay un nombre editable ni herramientas de escena; la opción de copiar no aparece sin permiso de Taller. |
| C-AC-15 | Todos | Oferta de importación | El destino de la cuenta actual y la advertencia sobre dispositivos compartidos preceden a las acciones diferenciadas para importar o rechazar. |
| C-AC-16 | Todos | Importación no válida | La explicación y la descarga del original siguen disponibles, mientras que el botón para enviar la importación no aparece. |
| C-AC-17 | 390px | Diálogos | El contenido modal cabe dentro del marco de la ventana gráfica, con márgenes legibles y acciones accesibles en ambos temas. |
| C-AC-18 | Todos | Teclado/movimiento reducido | El foco es visible, Escape en el modal devuelve el foco al punto de invocación y los modos reducido/fijo conservan todas las acciones sin desplazamiento. |

La evidencia de compilación y auditoría de ESTA captura r12 se registra a continuación. Las mediciones de rondas anteriores no se reutilizan como evidencia de este archivo. No se requirió instalar paquetes ni obtener recursos de red. La comprobación `components status` informó installed=True, built=True, 96/96 entries ready. Ambas miniaturas candidatas se compilaron con el mismo vocabulario de componentes reales antes de restaurar la entrada completa.

Comprobaciones del archivo final completadas hasta ahora:

- `contrast.py`: **158 pares comprobados en temas claro y oscuro; todos aprobados**.
- Recorrido de interacciones con Playwright: **13 comprobaciones aprobadas**, que abarcan inspectores nativos, una vista previa en línea, reinicio de filtros/paginación, propiedad de solo lectura/permiso para copiar, validación/confirmación del primer guardado, foco del nombre en línea, reintento sin conexión, copia del conflicto, protección de plantillas, guardado antes de reemplazar/navegar, descarga de importación no válida/Escape/foco, rechazo/consentimiento y texto en inglés. **Cero errores de página; cero solicitudes HTTP(S) externas.** Una primera prueba esperaba una coincidencia, aunque los fixtures neutrales contienen correctamente dos registros Escena coincidentes; se corrigió la expectativa de la prueba. El recorrido también reveló un problema real de prioridad del foco alternativo después de renombrar; el TSX final lo corrige y el recorrido completo se aprueba con el HTML recompilado.
- Sondeos adicionales de listas renderizadas en **360 y 1024px, ambos temas**: no se detectaron problemas de contraste, elementos no textuales, alineación, márgenes, desbordamiento ni hallazgos sin medir.
- Movimiento a 120ms: **3 animaciones expresivas activas**, **0 con reducción del sistema operativo**, **0 con `?still=1`**. Todas las acciones y estados siguen disponibles.
- El módulo oficial de medición `compare_directions.py` verificó la evidencia de selectores de esta dirección: **ok=true, evidence_ok=true, missing_evidence=[]**. La preparación de la comparación A/B/C por pares se comprobó después de la auditoría final: no existía `proyectos@v1.r12.dir-b.json`, por lo que la comparación por pares **NO SE EJECUTÓ**. El coordinador puede ejecutarla cuando existan todas las notas hermanas; aquí no se afirma que se haya aprobado una comparación por pares.
- Capturas inspeccionadas en memoria: ambas candidatas con componentes reales; lista de escritorio en tema oscuro; Taller de escritorio en tema claro; conflicto de teléfono en tema oscuro; diálogo de importación no válida de teléfono en tema claro; diálogo de primer guardado de teléfono en tema oscuro y vista de solo lectura ajena de escritorio en tema oscuro. No se guardaron archivos de captura.

Auditoría exhaustiva final de la interfaz renderizada, sobre el HTML r12 recompilado después de corregir las interacciones: **672 renderizados / 672 combinaciones previstas**, **17,388 mediciones de texto**, **1,965 paradas de foco**, en **1280, 390 y 768px** con ambos temas. Código de salida **0**; no se omitió ninguna combinación mediante muestreo. Se detuvieron dos ejecuciones de auditoría anteriores, ya reemplazadas, mientras se verificaban las correcciones de paginación/foco; solo se atribuye el resultado de esta ejecución final completada al archivo final.

`RESULTADO: APROBADO — sin problemas de contraste, contenido no textual, foco, alineación, márgenes ni desbordamiento`

Comandos:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/proyectos@v1.r12.dir-c.tsx --out <design>/proyectos@v1.r12.dir-c.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <design>/proyectos@v1.r12.dir-c.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <design>/proyectos@v1.r12.dir-c.html --widths 1280,390,768
```

`<design>` representa el directorio de diseño asignado a este requisito. La compilación completa integra **2,126 archivos fuente**, aproximadamente **648KB**, con CSS/JS/fuentes integrados y sin recursos externos. Estos resultados constituyen evidencia de un mockup de planificación, no de conformidad con la persistencia/seguridad en producción ni de aprobación del plan.

## 12. Pregunta abierta y supuestos

P: David, ¿debe abrirse la vista previa del primer proyecto al entrar en Proyectos, como en esta exploración, o deben comenzar todas las escenas contraídas?

Supuesto provisional a la espera de elegir una dirección: la primera muestra autorizada se abre para comparar; solo se expande una vista previa a la vez. Esto afecta la presentación inicial, no la propiedad, el consentimiento para el primer guardado/importación ni la semántica de persistencia. Las decisiones de alcance sobre cuenta, guardado, conflictos, importación y escena nueva ya están resueltas y no se vuelven a plantear aquí.

El propietario no ha elegido ni aprobado esta dirección. Los artefactos canónicos y el plan permanecen intactos. El comportamiento en producción, la revisión visual independiente y cualquier formalización canónica posterior corresponden a las tareas asignadas del plan.

### Identidad de entrada y artefactos

| Archivo | SHA-256 |
|---|---|
| `SPEC.md` | `032cbfb717c61ff8edc32160716a92fb925e8d41e1e31c8f62176f8da9decd7d` |
| `PLAN.json` | `b19d26e25d207f059fe4d83c2234f0d868305d43f0608749283b2ef8cf169cc3` |
| `design/proyectos@v1.r12.behavior.md` | `1d89ee0c436645cf1af3f8ac62d888d9ad089801f688870a48344d862c1c2b65` |
| `design/proyectos@v1.r12.dir-c.tsx` | `4de35ec0f1c7fbe4964d4d3b9c706dd96b721137ab503ddc32a3e6464c729b4f` |
| `design/proyectos@v1.r12.dir-c.html` | `403ac3672d0c14edf9f280ba26368b971bc09ce8227acd9ea9649db9236b465f` |
| `design/proyectos@v1.r12.dir-c.html.candidate-1.html` | `07f0102a26ff2da8da5e501f7dbe6f58be6e48bb150914440d17bd61312b3df2` |
| `design/proyectos@v1.r12.dir-c.html.candidate-2.html` | `fdda95d231b61eb7dcf0f051e90e3298f59f11d1538c87269c05a2964d454cf1` |
| `design/proyectos@v1.r12.dir-c.json` | `a2e798b6b31410847924b3fa5f8c26a00e8bf56eaed0807bdd061ea03a076984` |

