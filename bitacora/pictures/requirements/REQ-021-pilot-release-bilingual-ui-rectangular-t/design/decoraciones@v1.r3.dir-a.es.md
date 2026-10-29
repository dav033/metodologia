---
name: Registro junto a la escena
contract_target: decoraciones@v1
status: draft
artifact: exploration
subplan: SP-5
requirements: [R8]
revision: r3.dir-a
owner: David
---

# Registro junto a la escena — dirección A

## 1. Identidad y trazabilidad

Exploración **draft**, pendiente de elección y aprobación independiente. No es el contrato canónico `decoraciones@v1` y no autoriza implementación. Alcance: `decoraciones@v1.r3.behavior.md`, SPEC «Behavior — SP-5 (round 11 answered)» y SP-5 del PLAN vigente. Atiende el feedback del 2026-10-29: ninguna importación de biblioteca local, consulta de staff de solo lectura, copia al colocar, confirmación de servidor y aislamiento al cambiar de cuenta.

Fuentes leídas en ambos repositorios, en solo lectura: `src/app/globals.css`, `src/components/tres-d/Biblioteca.tsx`, `Taller3D.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, y taxonomía/tipos de biblioteca. Se leyeron los contratos hermanos `cuentas-admin@v1`, `planes@v1` y `proyectos@v1`, y se renderizaron sus HTML. El shell, fuentes embebidas, mapeo semántico, rutas y controles de cuenta parten del hermano Proyectos elegido r12-C. No se editó ningún repositorio, contrato compartido ni plan.

## 2. Propósito y personas

Master Designer y staff con Taller guardan la escena actual o una pieza elegida en su biblioteca de cuenta y vuelven a colocarla en su proyecto. Empleado interno y Administrador consultan otra cuenta autorizada sin modificar su original. La confirmación de éxito requiere respuesta del servidor: «Guardando…» no equivale a «Guardado en tu biblioteca».

Los registros «Escena de ejemplo», «Pieza de ejemplo», «Cuenta de ejemplo» y «Pieza de ejemplo · local» son fixtures explícitos. Los dibujos SVG son vistas ilustrativas, no miniaturas obtenidas del servidor ni un motor 3D. Las operaciones son simulaciones en memoria; el mockup no demuestra persistencia, autorización, recarga ni disponibilidad entre navegadores.

## 3. Enfoque, jerarquía y miniatura elegida

**Elegida: candidate-1**, el registro lateral. Conserva el contexto de trabajo del Taller: barra de proyecto, riel Añadir/Piezas/Plantillas/Sala, biblioteca junto al visor y guardado desde Escena e IA. Sustituye únicamente la composición del listado personal por filas compactas: miniatura → nombre/tipo/ocasión → ficha. Una navegación interna lleva a la cuenta o a «En este navegador». La ficha concentra colocar y, solo en propiedad, gestionar.

La miniatura candidate-2 ensayó la bandeja bajo el visor. En la composición renderizada, los filtros y el grupo local quedan más abajo y el origen se separa visualmente de los registros. Candidate-1 mantiene el origen, búsqueda y resultados sobre el mismo eje y utiliza mejor la franja lateral que ya existe en el Taller. Ambas son composiciones visuales pequeñas; los controles completos y temas pertenecen al HTML final.

El shell compartido se conserva: Pictures/anillo y punto, Sempertex, idioma/cuenta, H1 24 px, rutas neutrales Taller 3D / Proyectos y pie. El toolbar mantiene Deshacer/Rehacer, Foto realista y Lista de compra como contexto. Sus destinos externos a SP-5 muestran un aviso de alcance, sin simular una función terminada. El catálogo global «Del taller» queda separado y contextual; esta dirección no lo rediseña.

### Ocho ejes

| Eje | Expresión presente |
|---|---|
| concept | Registro operativo de guardados junto a la escena abierta, con procedencia de cuenta y de navegador separadas. |
| layout | Riel heredado de 52 px, registro lateral de 340–390 px y visor con guardado contextual; en teléfono visor y panel se apilan. |
| navigation | Rutas Taller 3D / Proyectos del shell hermano; riel Añadir/Piezas/Plantillas/Sala; anclas Mi biblioteca / En este navegador y fichas contextuales. |
| typography | Geist Sans existente: H1 24 px, panel 20 px, escena 16 px, registros 14 px y metadatos 12 px. Geist Mono solo en Sempertex. |
| density | Filas con miniatura 64 px (56 px en teléfono), nombre y ocasión en dos líneas, acceso de ficha de 44 px; filtros de ocasión/tipo pareados en escritorio y color/globo desplegables. |
| components | Button/Input/Skeleton reales de shadcn/Base UI; Dialog/AlertDialog con Animate UI; selects, radio, details y anclas nativos recompuestos dentro de los tokens Pictures. |
| colour | Tokens exactos de Pictures y Taller; acento solo en acción primaria/selección, éxito tras confirmación y error en rechazo. Navegación neutral, sin paleta nueva. |
| motion | Registro preciso: filas entran desde x=-12 px con 35 ms de secuencia; visor y formulario se asientan 8/12 px; confirmación escala y rota. 360 ms cubic-bezier(.77,0,.175,1), controles 150 ms; perfiles y reducción sin movimiento. |

## 4. Sistema visual y componentes

Se usan **los tokens existentes**, sin paleta ni familias nuevas. Se conserva el alias de borde accesible de los hermanos, `--input:var(--texto-tenue)`, en lugar de emplear el borde decorativo de bajo contraste. Mapeo de roles:

| Fuente Pictures | Roles reales del kit | Claro / oscuro |
|---|---|---|
| fondo | background | #faf9fc / #0b0c10 |
| superficie | card, popover | #ffffff / #16181f |
| superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| superficie-suave | plano suave del dibujo | #faf8fd / #1c1e26 |
| texto | foregrounds | #1c1425 / #f4f5f7 |
| texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| texto-tenue | input, contorno de control | #766c85 / #8a91a0 |
| acento / sobre-acento | primary / primary-foreground | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| acento-hover | primary-hover | #5530b8 / #a58dff |
| borde / borde-suave | border / reglas | #e3daef / #efe9f8; #383c48 / #2a2d38 |
| exito / exito-suave | success / success-soft | #1f7a55 / #dcf5e9; #78d6a8 / #173b31 |
| error / error-suave | destructive / destructive-soft | #b23a45 / #ffeaec; #ff979f / #43252a |
| aviso / aviso-suave | warning / warning-soft | #8f5f12 / #fff3d8; #f7c46b / #3f311c |
| taller-panel / taller-visor | panel/visor heredados | #faf9fc / #ebe7f1; #16131d / #1a1722 |

Geist y Geist Mono se importan de los WOFF2 latinos locales de t12 y el builder los embebe. La familia mono se limita al identificador Sempertex. Se conservan radios panel 32 px, inset 24 px, campos 18 px y botones pill; las miniaturas y controles del toolbar mantienen formas de Taller. Márgenes exteriores 40 px a ≥1100, 24 px intermedios, 20 px a ≤767. Los valores Taller proceden de globals.css de producción, no de los colores por defecto del kit.

| Componente: fuente:id variante estado | Import real / composición |
|---|---|
| shadcn:button default/outline ready/hover/focus/pressed/disabled/pending | `@/components/ui/button`; Base UI real. Action añade el atributo data-variant para el mapeo Pictures. |
| shadcn:input text ready/invalid/disabled | `@/components/ui/input`; nombre y búsqueda, labels asociados. |
| shadcn:skeleton row loading | `@/components/ui/skeleton`; miniatura y dos renglones, sin pulso. |
| shadcn:dialog ficha/rename/edit open/closed | `@/components/ui/dialog`; Animate UI/Base UI, título y descripción reales. |
| shadcn:alert-dialog delete open/error | `@/components/ui/alert-dialog`; confirmación destructiva, Cancelar primero. |
| native:select theme/view/state/scene/language/occasion/type/owner | Selects etiquetados; los inspectores están fuera del producto. |
| native:radio source scene/piece | Grupo Guardar con legend, controles de 20 px dentro de labels de 44 px. |
| native:details account/filters/catalogue closed/open | Disclosure, sin atribución falsa a menú ARIA. |
| custom:library-register grouped normal/loading/empty/error/read-only | Artículos con nombre, miniatura, ocasión y acción de ficha de 44 px. |
| custom:scene-preview illustrative normal/copied | SVG inline de escena neutral y copia añadida visible. |

`mountMockup/useMockup` de `@kit/mockup` y `useMotionProfile` de `@kit/motion` son reales. No se usó fallback HTML para el mockup completo; las dos miniaturas son bocetos HTML propios solicitados para comparar composiciones.

## 5. Navegación, interacción y movimiento

No se crea una ruta de producto: biblioteca y guardado son estados del Taller `/3d`. Proyectos conserva la ruta del shell hermano; en el mockup es contextual. Las vistas externas `biblioteca`, `guardar` y `consulta` son inspectores, no destinos nuevos. Las anclas de procedencia y el botón Añadir del riel llevan al contenido de biblioteca; Añadir enfoca su título y despeja el inspector sticky.

La consulta autorizada de staff añade un selector Cuenta. Cambiarlo vacía las filas anteriores inmediatamente y presenta carga antes de la nueva lista de ejemplo. El estado inspector «Cambio de cuenta» sustituye todo el área de datos: no mantiene miniaturas, nombres, ficha abierta ni formulario de la cuenta previa. Cerrar sesión usa el mismo vaciado. La cuenta del header no recibe una nueva opción de cambio inventada: el cambio de identidad se inspecciona desde Estado.

Las fichas son diálogos con foco contenido, fondo inerte, Escape y cierre explícito. El foco vuelve a quien abrió la ficha, o al H1 si ese control ya no existe. Eliminar usa AlertDialog con Cancelar inicial, conserva el registro si falla y ofrece Reintentar. La ficha de otra cuenta no contiene Renombrar, Editar ni Eliminar, tampoco versiones deshabilitadas. «Añadir a mi escena» anuncia y dibuja una copia en el proyecto propio.

**Detalle de movimiento:** las filas se registran lateralmente desde −12 px con 35 ms entre ellas; el visor se asienta desde 8 px y el formulario desde 12 px. Los avisos entran 10 px y el check confirma con escala .7→1 y rotación −18°→0. Expresivo 360 ms, curva `.77,0,.175,1`; acciones repetidas 150 ms, hover −1 px y presión +1 px/escala .98. Natural 240/130/22 ms; sutil 140/100/10 ms. Los tiempos son settle/control/secuencia. El spinner solo existe durante guardado pendiente. No se oculta el texto ni se anima la geometría del layout. Dialog/AlertDialog conservan su primitiva Animate UI instalada.

Quieto, `?still=1` y preferencia reducida eliminan desplazamientos, rotación, transición y repetición sin perder información, controles ni confirmación. Las animaciones CSS se pausan cuando la pestaña está oculta. Los selectores de evidencia de motion coinciden con animaciones/transiciones efectivas del DOM.

## 6. Flujos observables

1. **Guardar escena o pieza:** desde Escena e IA, elegir el alcance → formulario contextual con Nombre y Ocasión → validar → Guardando… con envío repetido deshabilitado → confirmación → registro de cuenta. Un rechazo conserva escena y campos; Reintentar reutiliza los mismos datos. El nombre/ocasión no se borran por el fallo. Solo la confirmación permite «Guardado»; el mockup simula la respuesta con una demora, no llama una API.
2. **Encontrar y colocar:** buscar por nombre, filtrar ocasión/tipo y desplegar color/globo → Ver ficha → Añadir a mi escena → copia ilustrativa visible y anuncio. Nombre, miniatura y ocasión continúan presentes. Las opciones del mockup son un subconjunto explícito; producción conserva todos los valores de la taxonomía y filtros existentes.
3. **Gestionar propios:** ficha propia → Renombrar o Editar nombre/ocasión → confirmar cambio; Eliminar → confirmación explícita → quitar solo tras éxito. Los mensajes de esos handlers dicen confirmación simulada. El proyecto abierto y sus copias se conservan.
4. **Staff:** seleccionar cuenta autorizada → carga sin filas anteriores → lista y ficha Solo lectura → Añadir crea una copia propia. Nunca se modifica ni se convierte en editable el original de la cuenta consultada. Staff mantiene su biblioteca propia al seleccionar Mi cuenta.
5. **Biblioteca local:** ancla En este navegador → ficha identificada local → colocar una copia. No hay acción, diálogo, progreso ni error de importación. El mockup no lee ni escribe localStorage; producción debe conservar intacta la clave `taller3d:biblioteca-propia:v1`.
6. **Cuenta/sesión:** al cambiar o cerrar sesión se vacían datos de cuenta y diálogos antes de cualquier nueva carga. Sin taller.usar se muestra la negativa sin datos restringidos. No se añade gestión de cuentas: el bloqueo de eliminación de cuentas con trabajo corresponde a la superficie SP-2 y al contrato de cuentas.

## 7. Vistas

| Vista del inspector | Estructura y acciones |
|---|---|
| biblioteca | Shell heredado → toolbar → riel → filtros y grupos de origen junto al visor → guardado desde inspector Escena e IA. |
| guardar | Mismo shell/listado/visor, formulario Nombre/Ocasión y alcance escena/pieza debajo del visor; Guardar y volver. |
| consulta | Mismo Taller propio, lista de otra cuenta con selector y aviso de solo lectura; ficha sin mutaciones, colocar copia propia. |
| ficha, renombrar, editar, eliminar | Diálogos contextuales alcanzables desde controles de producto y selector Diálogo; solo los permitidos se renderizan. No son páginas nuevas. |

## 8. Estados y recuperación

Todos están disponibles en el selector nativo Estado; el selector Diálogo cubre las cuatro escenas. Los estados de guardado llevan al formulario en vistas propias; no abren un formulario de modificación sobre otra cuenta.

| Valor | Qué se ve / qué se permite |
|---|---|
| normal | Lista de cuenta y grupo local distintos; buscar, ficha y guardado contextual. |
| loading | Skeleton de filas y Cargando biblioteca…; el grupo local conserva procedencia separada. |
| empty | Lista del servidor vacía y acción guardar propia; el grupo local no se trata como resultado de cuenta. Staff no recibe un CTA para guardar en la cuenta ajena. |
| error | Error al cargar la lista y Reintentar → carga; ningún estado de guardado se infiere de ese fallo. |
| saving | Guardando… y envío/campos/retorno deshabilitados, sin check ni mensaje Guardado. |
| saved | Guardado en tu biblioteca y check, reservado a confirmación. |
| save-error | Fallo, escena y campos conservados, Sin guardar y Reintentar. |
| read-only | Cuenta ajena, aviso claro y ficha sin rename/edit/delete; solo colocar copia. |
| account-switch | Datos anteriores y diálogos ausentes; carga de nueva cuenta, con botón externo explícitamente «Simular respuesta de la nueva cuenta». |
| signed-out | Sin registros ni diálogos; sesión cerrada y salida hacia cuenta/acceso delegada al shell. |
| no-permission | Sin acceso al Taller, sin biblioteca ni acciones de datos. |
| no-results | Cero coincidencias y quitar filtros; no confunde búsqueda vacía con cuenta sin elementos. |
| validation | Nombre con aria-invalid y error asociado; no se guarda un nombre vacío en esta propuesta. |
| delete-error | AlertDialog con registro intacto y reintento, solo para propietario. |

No se declara estado de importación: no existe en el piloto. Offline se representa mediante fallo de carga/guardado y recuperación, sin prometer cola offline, sincronización local ni éxito optimista. No se propone merge de composición, sistema de versiones ni política de conflictos que el brief no define.

## 9. Reflujo

A ≥1100 px, shell de hasta 1520 px, márgenes 40 px, riel 52 px, registro hasta 390 px y visor flexible. A 768–1099 px, márgenes 24 px, registro 310–360 px y campos del guardado apilados. A ≤767 px, márgenes 20 px, toolbar envuelve y muestra iconos con nombres accesibles, riel se vuelve horizontal, escena y formulario preceden al panel de biblioteca; Añadir lleva a la biblioteca y enfoca su título. No se agrega navegación global.

En teléfono las filas mantienen miniatura 56 px + texto flexible + acción 44 px; Ocasión y Tipo pasan a una columna. El visor ocupa 230 px; no se fija el cuerpo a una altura que bloquee el scroll. Los diálogos usan el ancho disponible menos 40 px y scroll interno si hace falta. El inspector Mockup permanece visible fuera del producto. La prueba de reflujo adicional cubre 360, 390, 768, 1024 y 1280 px; la auditoría oficial cubre 390/1280.

## 10. Accesibilidad y evidencia

Objetivo WCAG 2.2 AA para contenido aplicable; la descripción no acredita conformidad de producción. Labels asociados, fuente de guardado en fieldset/legend, botones de icono nombrados, focus-visible de 3 px con acento y offset 4 px, objetivos de 44 px. Los mensajes usan status/alert, validación aria-invalid/aria-describedby. Base UI proporciona semántica y contención modal; las acciones de cierre restauran foco. Navegación neutral; la información de guardado/error/solo lectura se expresa con palabras además del color.

Se ejecutó el builder real offline por ruta absoluta, sin paquetes ni assets descargados. `contrast.py`: **158 pares, ambos temas, todos pasan**. Se inspeccionaron capturas en memoria del shell hermano, ambos candidatos y vistas de lista/guardado/ficha a 1280/390 en claro y oscuro; no se añadieron capturas al directorio de diseño.

Auditoría final real: **216 renders de 216 combinaciones**, 8672 medidas de texto y 1922 paradas de foco; 1280/390 px en ambos temas, todos los estados y escenas del plan de auditoría, sin muestreo.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Prueba adicional Playwright: PASS — filtros, ficha de staff sin mutaciones y copia visible, estado pendiente antes de confirmar, reintento, vaciado de filas/diálogos al cambiar o cerrar sesión, selector EN, Escape, reflujo a 360/390/768/1024/1280 px, animaciones reales y Quieto sin animaciones. Se observaron cero peticiones externas y cero errores de navegador. Todos los selectores del JSON de evidencia encontraron elementos renderizados. La primera auditoría encontró un fallo de padding en cambio de cuenta; se corrigió y la última ejecución usa el HTML reconstruido final.

Límites: controles contextuales fuera de SP-5 son referencias de shell; los handlers no implementan el backend. La prueba de navegador comprueba el prototipo y sus simulaciones, no seguridad de cuentas, persistencia entre navegadores ni copia real de una composición 3D. La taxonomía del fixture es reducida, las miniaturas son SVG mock y los valores de ejemplo no representan registros reales.

## 11. Criterios visuales de aceptación de esta exploración

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1280 px | normal | Pictures/Sempertex, idioma/cuenta y rutas neutrales coinciden con la familia de contratos hermanos. |
| A-02 | ≥768 px | normal | Riel, registro y visor comparten una fila; cada registro reúne miniatura, nombre, tipo/ocasión y ficha. |
| A-03 | 390 px | normal | El layout no produce scroll horizontal y la acción de ficha mantiene 44 px. |
| A-04 | 390/1280 px | loading | El grupo de cuenta muestra skeleton y texto de carga, nunca registros de la cuenta previa. |
| A-05 | 390/1280 px | empty | Lista de cuenta vacía y En este navegador permanecen separados. |
| A-06 | 390/1280 px | saving | El texto dice Guardando, sin check ni Guardado. |
| A-07 | 390/1280 px | saved | El check y Guardado en tu biblioteca aparecen juntos. |
| A-08 | 390/1280 px | save-error | El formulario conserva nombre/ocasión y ofrece Reintentar. |
| A-09 | 390/1280 px | read-only | La ficha ajena contiene Solo lectura y Añadir a mi escena; no tiene Renombrar, Editar ni Eliminar. |
| A-10 | 390/1280 px | account-switch/signed-out | No hay filas ni diálogos de la cuenta anterior en el DOM de producto. |
| A-11 | 390/1280 px | normal | En este navegador carece de acción de importación. |
| A-12 | 390/1280 px | ficha | Añadir cierra la ficha, anuncia copia y añade la pieza ilustrativa en el visor propio. |
| A-13 | 390/1280 px | validation | El error de nombre está asociado al campo y el formulario no confirma un valor vacío. |
| A-14 | 390/1280 px | delete-error | Se conserva la confirmación con Cancelar y Reintentar sin quitar el registro. |
| A-15 | 390/1280 px | normal + reducido | Todos los controles/estados siguen disponibles y no se ejecutan animaciones. |
| A-16 | 390/1280 px | todos / ambos temas | No hay petición externa de fuente, imagen o script; cada estado usa los tokens del producto. |

Impacto: solo SP-5, T5.1 copia futura, T5.3 biblioteca Taller y T5.5 revisión visual. Es una propuesta inicial de composición y comportamiento, **compatibilidad por determinar** hasta elección/finalización; no se redirige ningún consumidor ni se escribe CHANGELOG compartido. El resto de las superficies conserva sus contratos.

## 12. Preguntas y supuestos

Decisor: owner, con Planner. Se registran sin bloquear esta exploración.

Q: ¿«Editar» modifica solo nombre/ocasión, como muestra esta propuesta, o también permite reemplazar la composición guardada desde la escena actual?
Q: ¿Los elementos heredados de «En este navegador» conservan su eliminación local anterior? Esta exploración permite consultarlos y colocar copias sin controles de mutación para mantenerlos intactos.
Q: ¿Se confirma un nombre obligatorio de hasta 120 caracteres, como en el proyecto hermano, o se conserva el nombre por defecto «Mi escena» al dejar el campo vacío como hacía la biblioteca local?

Supuestos visibles: la cuenta ajena se consulta mediante un selector staff autorizado; no introduce un directorio público de cuentas. Idioma ES/EN es una demostración del shell y copy de acciones; nombres/ocasiones de fixture son datos y no se traducen automáticamente. El guardado fallido no se considera sincronizado. Los controles locales no se transfieren a una cuenta nueva. La cuenta con decoraciones no se puede eliminar; la UI de administración de cuentas queda bajo SP-2 y no se rediseña aquí.
