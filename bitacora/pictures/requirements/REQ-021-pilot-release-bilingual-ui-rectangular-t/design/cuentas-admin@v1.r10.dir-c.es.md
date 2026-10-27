---
name: Nudos — acceso en tensión
status: draft
kind: direction-exploration
contract_ref: cuentas-admin@v1
subplan: SP-2
requirements: [R1, R3, R16]
revision: r10.dir-c
chosen_thumbnail: cuentas-admin@v1.r10.dir-c.html.candidate-1.html
---

# Nudos — dirección C

Exploración táctil/juguetona no aprobada. Esta es una nota de dirección, no el contrato canónico de doce secciones. No se modifica ningún plan, contrato compartido, código fuente de producción, historial ni estado de aprobación. El propietario elige una dirección; una persona encargada de la finalización redacta el contrato canónico por separado.

## Concepto y elemento distintivo

Una persona que decora con globos une material blando mediante un nudo firme. Aquí, la cuenta es una **banda de látex tensada** y el rol es la conexión que determina a qué herramientas da acceso. La lista de cuentas es una secuencia continua de bandas legibles con anclajes amarillos en las válvulas, en lugar de un panel de tarjetas idénticas. El formulario de inicio de sesión usa la misma silueta estirada. La tipografía local grande y redondeada da carácter inflable a la pantalla de trabajo sin convertir las etiquetas del formulario en texto de exhibición.

El elemento distintivo es una banda que se estira hasta su lugar, una pequeña válvula que gira y una clavija de navegación seleccionada que encaja en ángulo. Al presionarlas, el material se comprime; los errores liberan presión hacia los lados; el éxito se asienta como un sello. Se puede arrastrar un lazo decorativo de látex con el resorte instalado o moverlo mediante dos botones etiquetados equivalentes. Moverlo no cambia ninguna cuenta ni permiso. Todas las operaciones de cuenta siguen siendo acciones de texto explícitas; ningún gesto controla una operación sensible para la seguridad.

## Dos bocetos, primero

1. **Elegida:** `cuentas-admin@v1.r10.dir-c.html.candidate-1.html`, estructura de tensión con una identidad y una muestra de material a la izquierda, una banda de inicio de sesión alineada a la derecha y bandas lineales para las cuentas. El campo de trabajo rectangular admite direcciones de correo electrónico y validación, mientras que el borde exterior moldeado aporta la identidad del material.
2. `cuentas-admin@v1.r10.dir-c.html.candidate-2.html`, una constelación de cápsulas infladas con personas alrededor de una acción central para invitar. Tiene una silueta más juguetona, pero dificulta comparar el correo, el rol, el último acceso y las acciones seguras de cuenta. Se conserva como boceto visual, sin desarrollarlo.

Ambos bocetos tienen CSS integrado, un selector de tema y adaptación para teléfonos. Son bocetos visuales, no afirmaciones de que sean implementaciones con shadcn. La maqueta completa usa las bibliotecas instaladas reales y el constructor sin conexión.

## Por qué no es la opción predeterminada

El lenguaje visual propio del material no es una paleta SaaS morada ni un carrusel de tarjetas redondeadas. El amarillo funciona como anclaje físico, el petróleo indica elementos accionables y un fondo azul pálido conecta la escena de trabajo con la muestra de látex. La redondez inflada del encabezado, las esquinas asimétricas de las bandas y las pequeñas válvulas de unión forman un conjunto coherente. Las bandas de cuenta de ancho completo facilitan el escaneo práctico, en lugar de convertir una burbuja decorativa en el objetivo de navegación. No hay estadísticas inventadas ni gráficos decorativos.

## Registro visual e identidad compartida

Lee las notas hermanas `proyectos@v1.r8.dir-a/b/c.md`: colección editorial, escenario/cinta y archivo de materiales. Sus notas también documentan las exploraciones del banco de corte de Taller y del recorrido de permisos de cuentas. Esta dirección no repite las pestañas de carpeta del archivo, la cinta de miniaturas del escenario, la regla del banco de corte ni el pase perforado de permisos. Usa una banda tensada, un nudo de látex y clavijas de navegación encajadas. Se mantienen la denominación Pictures/Sempertex, la marca de círculos enlazados, el vocabulario del dominio, los controles de formulario legibles y las protecciones explícitas de cuentas. Los nuevos valores de color y tipografía de abajo son propuestas exploratorias basadas en los comentarios más recientes del propietario, no cambios a los tokens del proyecto.

## Ocho ejes

| Eje | Propuesta observable | Evidencia |
|---|---|---|
| concepto | Nudos: las bandas de látex conectan a las personas con las herramientas que pueden usar; la válvula suave es la firma compartida del universo del producto. | `.latex-loop`, `.person-band` |
| diseño | Estructura asimétrica de tensión: panel de identidad fijo con ancho del 38% y columna de trabajo continua del 62%. Las filas de cuentas se extienden entre dos anclajes redondeados; en el teléfono se apilan la identidad, la navegación y las filas. | `.workbench`, `.rubber-band`, `.person-band` |
| navegación | Botones de carrete con forma de clavija a la izquierda para Personas, Roles y Mi cuenta; la clavija seleccionada se inclina. El menú de cuenta permanece en el encabezado; el formulario y las acciones destructivas usan confirmaciones modales. | `.spool-nav`, `.user-menu` |
| tipografía | Rounded Mplus 1c ExtraBold integrada, de 43–72px con espaciado compacto para titulares; Adwaita Sans integrada para controles y datos de 13–17px. Las formas redondeadas de las letras evocan el látex inflado sin recurrir a una tipografía geométrica sans de estilo SaaS. | `.big-title`, `.person-name` |
| densidad | Relleno generoso de 38px para el formulario, 22px para las bandas de personas y separación de 17px entre filas. Las bandas largas y bajas muestran los seis datos de cada cuenta; no hay indicadores clave de rendimiento ni panel de tarjetas iguales. | `.rubber-band`, `.account-stack` |
| componentes | Button, Input y Skeleton reales de shadcn; casilla de Animate UI y primitivas de modal/alert-dialog de Base UI. Lazo SVG de látex personalizado, superficies de acciones comprimidas, filas de cuenta con forma de banda y selector de permisos agrupado. | `[data-slot=button]`, `[data-slot=checkbox]`, `.dialog-box` |
| color | Propuesta: azul claro de piscina #dfeded y petróleo profundo #075e60, con amarillo látex #f7ce45 solo para anclajes del material. Tema oscuro: #10282b/#193b3e con controles menta #8ce0d5. Texto #123b3f o #f0f9f7; sin morado, crema/terracota ni el color de énfasis predeterminado compartido. | `:root`, `html[data-theme=dark]`, `.initial` |
| movimiento | Gramática de tensión elástica, cubic-bezier(.22,1.35,.55,1), composición expresiva de 680ms y controles de 190ms: entrada de banda estirada, torsión del nudo, compresión del texto, encaje de la clavija, acople del conector, liberación de presión ante errores, presión de sellado al lograrlo, balanceo del estado vacío, elevación al pasar el cursor/compresión al presionar y arrastre con resorte según el perfil. Natural: 440/160ms; sutil: 240/120ms. El movimiento reducido y still=1 se estabilizan de inmediato. | `.rubber-band`, `.latex-loop`, `.big-title`, `.press` |

## Sistema de diseño existente y bibliotecas reales

La inspección de solo lectura abarcó los `AGENTS.md` y `src/app/globals.css` de ambos repositorios del espacio de trabajo, sus alias semánticos de shadcn y la fuente conductual actual SPEC/PLAN/SP-2. El plan fuente define doce permisos y cinco roles fijos; los roles del sistema son Plan 1, Plan 2, Plan 3, Empleado interno y Administrador. Las tres categorías de actores de la SPEC inicial no son tres roles del sistema editables.

| Token existente del proyecto | Rol del kit | Valores exploratorios claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#dfeded` / `#10282b` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#193b3e` |
| `--texto` | `--foreground` y fondos de superficie | `#123b3f` / `#f0f9f7` |
| `--texto-suave` | `--muted-foreground` | `#36595d` / `#bad3d1` |
| `--superficie-2` | `--secondary`, `--muted`, `--accent` | `#d2e7e6` / `#21474a` |
| `--acento` | `--primary`, `--ring` | `#075e60` / `#8ce0d5` |
| `--sobre-acento` | `--primary-foreground` | `#ffffff` / `#10282b` |
| `--borde` | `--border` | `#729496` en ambos temas |
| rol de borde marcado para controles | `--input` | `#46787a` / `#92b3b3` |
| `--error`, `--exito`, `--aviso` | roles de error, éxito y advertencia | pares de texto/relleno específicos del tema definidos en TSX |
| `--ease-rebote` | curva de tensión propuesta `--snap` | `cubic-bezier(.22,1.35,.55,1)` |
| nuevo rol de material local | `--latex` con `--ink` | `#f7ce45` con `#123b3f` en ambos temas |

Esta tabla asigna las responsabilidades semánticas existentes; propone nuevos valores visuales solo para esta exploración. No afirma que estos colores ya estén presentes en Pictures. Si se eligen, quien finalice deberá hacer explícita la propuesta de tema en el contrato canónico. Rounded Mplus 1c ExtraBold y Adwaita Sans son fuentes locales instaladas, limitadas al subconjunto latino e incrustadas en memoria como URI de datos, sin nuevos archivos de fuentes, instalación de paquetes ni solicitudes de red. La tipografía de producción existente permanece sin cambios.

Componentes reales: `shadcn:button default/outline/disabled` de `@/components/ui/button`; `shadcn:input default/invalid/disabled` de `@/components/ui/input`; `shadcn:skeleton loading` de `@/components/ui/skeleton`; `animate-ui:checkbox checked/unchecked/disabled` mediante `@/components/ui/checkbox`; `@animate-ui/react/primitives/base-ui/dialog` y `alert-dialog`, instalados, para el foco/modalidad y la confirmación de acciones destructivas. Las primitivas directas proporcionan transiciones de entrada **y salida** que respetan el perfil. `motion/react` y `@kit/motion` proporcionan el resorte voluntario de arrastre. Estructura de planificación: `mountMockup` / `useMockup` de `@kit/mockup`. Se conservan deliberadamente los selectores nativos. Los componentes personalizados son el nudo SVG, los contenedores de bandas, el selector de permisos agrupado y la navegación del carrete. No se usó una biblioteca HTML alternativa para la maqueta completa.

## Comportamiento conservado y límites de la simulación

Fuentes: resumen de `cuentas-admin@v1.r10.behavior.md` `abde9480c2f8d545`, SPEC actual, PLAN y PLAN.json. Esta composición nueva conserva el requisito de comportamiento; no copia ningún borrador visual anterior.

| Vista nativa | Objetivo de la persona usuaria y estados clave |
|---|---|
| `login` | Inicio de sesión con correo electrónico y contraseña. Los errores de credenciales, correo desconocido, cuenta deshabilitada y cuenta bloqueada comparten un mensaje que incluye la espera de quince minutos. No se inventan el registro abierto ni el envío autónomo de correos. La fixture de éxito local muestra destinos de Plan 2 y el menú de cuenta de la persona; la navegación real a la página solicitada y a la primera área permitida corresponde a la implementación. |
| `activar` | Nombre, correo electrónico y Plan 2 de la invitación; contraseñas coincidentes de 8–200 caracteres; aviso versionado y aceptación sin marcar. La activación permanece deshabilitada hasta aceptar. El estado de enlace usado/vencido solicita un enlace nuevo al administrador. |
| `restablecer` | Enlace de un solo uso emitido por un administrador, dos contraseñas nuevas coincidentes, validez de 24 horas y una explicación clara de la revocación de sesiones. Los enlaces no válidos muestran la misma explicación. |
| `aviso` | Aviso versionado en ES/EN con marcadores de posición para revisión legal, claramente delimitados entre corchetes. El menú de cuenta está deshabilitado hasta aceptar; antes de la aceptación no aparece ningún otro destino. Se puede cerrar la sesión. La aceptación muestra el reconocimiento de versión/fecha y una acción para continuar. |
| `cuenta` | Nombre, correo electrónico, rol, versión/fecha del aviso aceptado y cambio de contraseña que requiere la contraseña actual. El éxito explica la revocación de otras sesiones y la renovación de la sesión del navegador. |
| `cuentas` | Cinco personas ficticias con nombre, correo electrónico, empresa, rol, estado y último acceso; búsqueda local real y filtros por rol/estado. La invitación solicita nombre/correo electrónico/empresa opcional/rol, rechaza duplicados y muestra un enlace ficticio de un solo uso con control para copiar. Las acciones de cuenta muestran cambio de rol, desactivación/reactivación, restablecimiento, renovación de invitación y eliminación con protecciones. |
| `roles` | Cinco roles inmutables del sistema y un rol personalizado de ejemplo. Permisos de solo lectura o nombre/casillas editables. El selector de grupos de herramientas muestra los doce permisos en cuatro grupos sin un modal móvil extenso. Las selecciones se conservan al cambiar de grupo. Se rechaza guardar sin permisos mediante `ROL_SIN_PERMISOS`; se bloquea la eliminación del rol de ejemplo asignado. |
| `sinacceso` | Denegación de permisos por escrito, orientación para el administrador, Mi cuenta y cierre de sesión. Esto no afirma que se apliquen permisos reales de API. |

El selector de estado global expone los estados normal, carga estructural, vacío, error, éxito, validación, sin conexión, permiso denegado y enlace usado/vencido. El estado vacío aplica a la búsqueda de cuentas y a los roles personalizados; usado/vencido, a los formularios de tokens; y permiso denegado, a las vistas con sesión iniciada. Los estados no relacionados conservan la fixture normal. No hay una fixture de datos remotos desactualizados: todos los registros son datos locales de demostración. El estado sin conexión muestra una advertencia escrita y una opción para reintentar; los puntos de entrada para mutaciones están deshabilitados. La carga reemplaza el contenido con Skeleton estructural y un estado activo escrito. También se puede acceder a cada diálogo de forma independiente mediante el selector nativo Diálogo: invitación, enlace de un solo uso, administración de cuenta, desactivar/reactivar, eliminación de cuenta, editor de roles, eliminación de rol asignado y menú de cuenta.

Fixtures de personas: Camila (trabajo guardado), Julián (invitado, sin trabajo), Lucía (personal, trabajo guardado), Tomás (inactivo, sin trabajo), Ana (última administradora activa). La eliminación solicita el correo electrónico exacto y explica que la eliminación de datos personales es irreversible, mientras que el gasto anonimizado de IA se conserva. Las protecciones de trabajo guardado y última persona administradora son visibles antes de que pueda ejecutarse una acción. La última persona administradora tampoco puede perder su rol ni ser desactivada. Una nueva invitación o enlace de restablecimiento indica que los enlaces anteriores sin usar del mismo tipo quedan invalidados. Las invitaciones duran siete días; los enlaces de restablecimiento, veinticuatro horas.

La maqueta no llama a ninguna API de cuentas ni crea enlaces reales o sesiones autenticadas. El inicio de sesión exitoso es una demostración acotada de destinos de Plan 2, no una navegación funcional a las herramientas de producción. Las ediciones de cuentas y la creación de invitaciones operan sobre el estado local de la fixture hasta que cambia la vista/el estado; el editor de roles demuestra selección, validación y comentarios de éxito, pero no es un almacén persistente de roles. Los cambios nativos de vista/estado vuelven a montar deliberadamente las fixtures. La selección directa de escena puede mostrar un diálogo en cualquier vista para su revisión; no otorga permisos reales. Si los permisos del navegador impiden copiar, la alternativa del portapapeles solicita seleccionar el texto manualmente. El texto del enlace se identifica claramente como ficticio y se muestra como texto, no como enlace de navegación externa.

## Objetivos de capacidad adaptable, accesibilidad y movimiento

- 360–767px: una columna, margen exterior de 20px, margen interior del formulario de 22px, margen interior del modal de 22px, menú de cuenta a ancho completo, sin nudo decorativo, bandas de cuenta con ajuste de línea y una acción etiquetada debajo de los datos. La navegación de controles permanece en línea y se ajusta; no se oculta en un menú de iconos sin etiqueta.
- 768–1023px: franja de identidad de 270px y contenido flexible, margen exterior de 24px, búsqueda encima de dos filtros; acciones de las personas debajo del bloque del nombre cuando sea necesario.
- 1024–1599px: estructura de dos columnas de 0.72/1.28, margen de 40px y separación de 54px; margen interior del formulario de 38px y pie de apoyo alineado. A partir de 1600px, la estructura se mantiene limitada a 1280px y su separación aumenta a 85px.
- Controles nativos, etiquetas de texto, mensajes activos de éxito/error, objetivos principales de 46–48px, contornos de foco visibles de 3px y foco/modalidad de modal establecidos. Las operaciones destructivas usan la primitiva AlertDialog real. Se comprueban el texto y los bordes de controles en ambos temas. WCAG 2.2 AA es un objetivo, no una certificación derivada de una auditoría automatizada.
- El movimiento expresivo es el comportamiento predeterminado. El contenido nunca se desvanece hasta que el texto sea ilegible y las transformaciones no cambian el diseño circundante. Ocho fotogramas clave finitos creados manualmente, la respuesta al pasar el cursor/presionar/enfocar controles repetidos y un resorte de Motion distinguen la gramática de tensión. Las líneas de tiempo CSS se pausan en pestañas ocultas; no hay bucles autónomos decorativos infinitos. La carga usa un Skeleton pulsante en una región acotada. El movimiento reducido del sistema operativo, Quieto y `?still=1` eliminan el desplazamiento y los bucles, y estabilizan la entrada/salida del modal sin perder controles ni campos seleccionados. No hay una secuencia decorativa de seis pasos de aparición gradual hacia arriba.

## Verificación

- Generador real sin conexión: PASS, 2,148 archivos fuente incluidos en el paquete. El generador produjo un paquete de 861KB; el HTML independiente final tiene 1,167,893 bytes después de incluir también el CSS exacto creado manualmente en un bloque de estilo del encabezado, para que el comprobador estático de tokens lea los mismos valores que el tiempo de ejecución. No se descargó ninguna hoja de estilos, fuente, recurso ni paquete.
- `contrast.py`: `contrast: 158 pairs checked in light and dark, all pass` (salida 0).
- `audit_mockup.py --max-combos 300` final: **544 renders / 544 combinaciones planificadas**, 11,476 mediciones de texto y 1,544 puntos de foco del teclado a 1280px y 390px en ambos temas (salida 0). No se omitió ninguna combinación mediante muestreo.
- **RESULTADO: PASS — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- `compare_directions.py A.html B.html C.html --json` final: salida 0, `ok: true`, `evidence_ok: true`, sin selectores faltantes. Similitud de diseño de A/C: .006; de B/C: .053. Ambas difieren en tipografía y movimiento. B/C comparten la medición de navegación de la primera pantalla, pero sus composiciones, tipografía y movimiento difieren; todos los pares pasan. Esta es una comprobación mecánica de distinción, no una aprobación de la persona propietaria ni una prueba de preferencia visual.
- `RESULTADO DE INTERACCIÓN: PASS — 27 comprobaciones`: aceptación del aviso y discrepancia de contraseñas, destinos de Plan 2 sin Taller, bloqueo de navegación por aviso actualizado, búsqueda/recuperación de estado vacío, rechazo de invitación duplicada, presentación de enlace de un solo uso, inserción de invitación local y cambios de plan, rechazo por trabajo guardado, protección de la última persona administradora, eliminación con correo electrónico exacto, permisos del sistema de solo lectura, rechazo de roles sin permisos, conservación de selección de grupos de herramientas, Escape/retorno del foco, orientación genérica de inicio de sesión con espera de quince minutos y reflujo en 360/390/768/1024/1280px. No se observaron errores de página en tiempo de ejecución ni solicitudes HTTP(S).
- `RESULTADO DE MOVIMIENTO Y MODAL: PASS`: se observaron en ejecución las líneas de tiempo reales de 680ms `letter-pressure`, `knot-in` y `band-tension`. La vista previa de Plan 2 con sesión iniciada muestra el menú de cuenta de la persona, y cerrar sesión regresa a la fixture de inicio de sesión. Tanto `?still=1` como `?rm=1` dejan de tener animaciones en ejecución después de 150ms, incluida la entrada/salida del modal. Los límites del editor de roles permanecen dentro de las vistas de 390/1280px en ambos temas con el movimiento reducido del sistema operativo.
- `VERIFICACIÓN DE TIPOS DE ENTRADA: PASS`: comprobación TypeScript estricta/noEmit en memoria de los diagnósticos de este TSX, con alias explícitos para las bibliotecas/runtime instalados y skipLibCheck. No es una verificación de tipos del repositorio de producción. La primera invocación del comprobador requirió asignar explícitamente las exportaciones de declaraciones instaladas de Animate UI; fue un problema de configuración del resolver, no un error de código fuente suprimido.
- Revisión visual renderizada: inicio de sesión/cuentas en escritorio claro, cuentas en teléfono oscuro, editor de roles en escritorio oscuro y activación por invitación completa en teléfono claro. El pie de inicio de sesión comparte el margen interior del formulario; los bordes de controles oscuros y los rellenos de casillas siguen siendo visibles. La herramienta de comparación aceptó de forma independiente todos los selectores de evidencia JSON.
- SHA-256 final del HTML: `179b1593ee5d3c1b62d6c68e883f07dde4766ceb67b0bf2d4593981e041e55fb`.

La primera auditoría encontró cuatro casos de relleno en leyendas sobre el marco y un editor de roles extenso en teléfono. Reemplazar las leyendas que cruzaban el borde por grupos de permisos con nombre y margen interior, y mostrar un grupo de herramientas a la vez, resolvió esos hallazgos. Una prueba posterior de interacción encontró que la transformación Motion en línea del modal instalado reemplazaba el centrado CSS: el diálogo podía extenderse por debajo de la vista aunque la auditoría automatizada pasara. El posicionamiento ahora usa la propiedad `translate` independiente de CSS, y pasan las comprobaciones explícitas de límites de vista y clic. El texto del modal reemplaza el efecto de opacidad/desenfoque predeterminado para permanecer completamente opaco; la entrada y la salida siguen usando la transición del perfil.

Una comprobación inicial de cierre de sesión esperaba el botón en español de la vista anterior después de cambiar de vista; el tiempo de ejecución vuelve a montar la fixture deliberadamente y reaplica el idioma del navegador. La comprobación corregida afirma el destino de inicio de sesión y selecciona español explícitamente antes de revisar la etiqueta. Esto no demuestra la persistencia del idioma por cuenta.

Esta tarea de diseño no ejecutó pruebas de producción, despliegues, base de datos, autenticación real, invalidación de tokens ni aplicación de seguridad. Esas tareas siguen siendo responsabilidad de implementación/aceptación; no se reportan como aprobadas.

## Preguntas abiertas y supuestos

P: ¿Quién proporciona el nombre final del responsable del tratamiento, la base legal, la política de retención y los datos de contacto para el aviso bilingüe? El propietario o el equipo legal deben reemplazar los marcadores entre corchetes antes de publicar el piloto; el borrador los mantiene visibles.
P: ¿El propietario elige esta dirección de látex en tonos petróleo y amarillo, junto con la combinación tipográfica redondeada, para el contrato canónico de cuenta, o conserva otra exploración? Este artefacto no aprueba cambios de paleta ni de tipografía.

Confirmado, no se reabre: solo cuentas invitadas; enlaces copiados y compartidos por el administrador; cinco roles de sistema inmutables; permisos exactos según el plan de herramientas; aplicación de permisos del lado del servidor; contraseña de mínimo ocho caracteres; indicación genérica de espera de quince minutos; revocación en la siguiente solicitud; protección del último administrador; eliminación solo si la cuenta no tiene trabajo guardado; gasto de IA anonimizado y conservado.

Supuestos: todas las personas, empresas, fechas, direcciones de correo y enlaces son datos ficticios de prueba. El texto del aviso es una muestra visiblemente provisional, sujeta a revisión legal. El idioma se determina inicialmente según el navegador, y el control local ES/EN demuestra el cambio; el idioma persistido de la cuenta y las traducciones de producción corresponden a SP-6. Las etiquetas de roles del sistema y las fechas de los datos de prueba pueden conservar su presentación original en español en esta maqueta exploratoria; no constituye una afirmación de aceptación bilingüe completa de SP-6.

## Impacto y estado de aprobación

Solo borrador. Si se elige, los consumidores afectados de SP-2 son: T2.1 copia el contrato final aprobado por el propietario; T2.3 implementa el inicio de sesión, las invitaciones y el restablecimiento, y el aviso; T2.4 implementa la cuenta, el menú y la contraseña; T2.5 implementa la administración y la edición de roles; T2.6 prueba el flujo en dos navegadores; T2.7 compara la fidelidad visual renderizada; T2.8 audita el comportamiento y la seguridad. R1 corresponde a las pantallas de token y cuenta, R3 a la edición y protección de roles, y R16 a las descripciones exactas de los planes y los cambios de rol. T2.2 sigue siendo la implementación de la API y no se implementa aquí. La compatibilidad está **indeterminada hasta seleccionar una dirección y finalizar la versión canónica**. Ninguna tarea de implementación puede usar esta exploración como contrato aprobado.
