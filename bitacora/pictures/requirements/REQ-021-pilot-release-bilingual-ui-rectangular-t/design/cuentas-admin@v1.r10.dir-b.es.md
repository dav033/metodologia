---
name: Umbral de aire
status: draft
kind: independent-direction-exploration
contract_ref: cuentas-admin@v1
revision: r10.dir-b
subplan: SP-2
requirements: [R1, R3, R16]
owner: David
approval: pending-owner-selection
chosen_thumbnail: cuentas-admin@v1.r10.dir-b.html.candidate-1.html
---

# Umbral de aire — dirección B

## 1. Identidad y trazabilidad

Esta es la **exploración** cinética/espacial, no el contrato canónico, una versión aprobada ni un insumo de implementación. No se modifica ningún contrato compartido, plan, historial, repositorio ni otra dirección. El propietario elige una dirección antes de que un finalizador independiente redacte el contrato canónico.

Fuentes consultadas: SPEC.md (`65b1e5ecc06f20d9`), PLAN.md (`cc7e53f2abf3c23c`), PLAN.json (`7a2c833a7e711508`) y el archivo compartido `cuentas-admin@v1.r10.behavior.md` (`c665ab01443531a7`); los hashes son prefijos SHA-256. SP-2 cubre R1/R3/R16 y T2.1–T2.8. Impacto visual propuesto: acceso en T2.3, cuenta en T2.4 y administración en T2.5; las pruebas de T2.6, la revisión visual de T2.7 y la auditoría de T2.8 siguen siendo independientes. T2.1 deberá copiar más adelante el artefacto canónico aprobado por el propietario, nunca esta exploración. La compatibilidad con una implementación futura está por determinar hasta que se seleccione y finalice una dirección; la nueva composición requiere implementación y revisión visual. Aquí no se redirige ningún consumidor.

## 2. Concepto, gesto memorable y dos miniaturas

**Concepto:** entrar al espacio de trabajo de una decoradora a través de un umbral inflable. La escena se compone de elementos físicos del producto: látex inflado, un globo metalizado amarillo, una cuerda de sujeción y una superficie de instalación. La tipografía grande e inclinada hacia adelante expresa la presión y el impulso de esos materiales. La información de trabajo permanece en un plano opaco.

**Gesto memorable:** el arco cobalto gira hasta encajar en su base, el globo metalizado aparece en diagonal y tensa su cuerda, y el plano de trabajo se asienta a su lado con una pequeña corrección de perspectiva. La forma sigue presente y legible. Tras llegar, el globo metalizado se balancea suavemente sujeto por su cuerda, en vez de hacer flotar la forma misma.

Las dos composiciones HTML pequeñas originales se escribieron **antes** del TSX/build completo:

- **Elegida: candidata 1**, `cuentas-admin@v1.r10.dir-b.html.candidate-1.html`: umbral asimétrico y plano de trabajo legible. El formulario, su título y la ayuda comparten un eje izquierdo; el pie de página comparte los ejes exteriores de la escena. Sigue siendo comprensible cuando la escultura se convierte en un detalle pequeño en el teléfono.
- Candidata 2, `cuentas-admin@v1.r10.dir-b.html.candidate-2.html`: una amplia escena de equipo bajo un recorrido de tres paradas. Se descartó porque el recorrido y el segundo título grande compiten con la lista; la combinación horizontal de escultura y lista deja menos espacio para los metadatos de cuenta en el teléfono.

**Por qué no es una opción predeterminada:** no usa morado, crema pálido, terracota, métricas de panel genéricas ni una cuadrícula ornamental de tarjetas. Los volúmenes físicos azules y amarillos, la tipografía condensada e itálica de exhibición, la esquina asimétrica del umbral y la coreografía espacial de asentamiento forman un conjunto coherente. Los campos operativos siguen usando controles reales y familiares. Los reflejos materiales aparecen en los objetos; el texto nunca se coloca sobre un degradado.

## 3. Registro visual y jerarquía

Consultar las notas de exploraciones hermanas: proyectos r8 A (archivo de trabajo), B (elevación frontal y cinta de miniaturas), C (muestras de materiales archivadas); Taller r6 B (escena de medición y columna de herramientas), C (mesa de corte y bandeja inferior), y r7 C (molde de silueta). Esta dirección no repite su archivo, cinta, carpetas de muestras, columna vertical de herramientas, bandeja inferior, reglas de medición ni catálogo que se acerca.

Identidad compartida: el nombre Pictures, la silueta de marca similar a un anillo, las palabras directas en español para los productos, el acceso solo por invitación y el mundo real de la decoración con globos. El morado existente se reemplaza deliberadamente solo en esta exploración, en respuesta a la solicitud del propietario de usar mundos cromáticos distintos. No se propone ningún cambio de tokens de producción como si ya se hubiera realizado.

Cada plano de trabajo responde una pregunta: ¿puedo entrar?, ¿puedo aceptar?, ¿quién tiene acceso?, ¿qué puede hacer esta cuenta? o ¿qué permite este rol? A continuación aparece una única acción principal que responde esa pregunta. La tipografía de exhibición grande queda fuera del plano operativo. La lista de cuentas usa registros separados por líneas, no mosaicos de KPI. Los permisos de rol se agrupan por herramienta.

## 4. Ocho ejes, sistema visual y procedencia

| Eje | Presencia en esta dirección |
|---|---|
| Concepto | Umbral de entrada inflable, globo metalizado y cuerda alrededor de la superficie de acceso de la decoradora. |
| Diseño / composición | Dos planos: `.stage` usa .78fr para la historia/escultura y 1.6fr para el plano de trabajo opaco, con una separación de 32px. El plano tiene una esquina de entrada de 72px; las demás esquinas conservan 18px. En ≤760px, la historia se compacta sobre el plano de trabajo. |
| Navegación | Una cinta superior dentro del flujo, no una barra lateral ni un anclaje inferior: Cuentas, Roles, Mi cuenta. La estación activa es un disco opaco. Las filas de cuentas abren detalles; los controles con etiquetas directas abren diálogos. El acceso público no incluye navegación para registrarse ni crear invitaciones. |
| Tipografía / escala | DejaVu Sans Condensed Bold Oblique incorporada para títulos de exhibición de 48–78px; Liberation Sans Regular/Bold incorporada para el texto de trabajo. Títulos de trabajo de 24–26px, cuerpo de 15px, texto secundario de 12–14px; los metadatos de rol llegan a 11px. |
| Densidad / forma | Escena abierta; relleno del plano de 34px en escritorio, 28px en tamaño intermedio y 22px en teléfono, con márgenes exteriores de 20px. Campos de 48px; botones de ≥44px; casillas de verificación de 24px dentro de etiquetas de ≥44px. Las filas de cuenta se reorganizan en líneas para nombre, empresa, rol, estado y último acceso. |
| Componentes | Button, Input, Skeleton y DropdownMenu reales de shadcn/Base UI; Checkbox, Dialog y AlertDialog de Animate UI. Arco/globo metalizado/cuerda, plano de entrada y disco de estación con CSS personalizado; exhibición con resorte de Motion. Selectores nativos de planificación e idioma. |
| Lógica del color | Claro: fondo azul #d9e7fb, plano #f3f7ff, texto azul marino #10294f, acción cobalto #1545cc y globo metalizado amarillo #ffcf49. Oscuro: escena #081d42, plano #102b56, texto blanco #f3f7ff y acciones amarillas. La navegación es neutra; los errores y éxitos semánticos se expresan con texto y color. |
| Movimiento | Rotación/estiramiento del arco, llegada diagonal del globo metalizado, desenrollado de la cuerda, asentamiento en perspectiva del plano, alineación de la tipografía mediante resorte, asentamiento lateral de filas, compresión de la respuesta visual, estabilización del anillo vacío, elevación al pasar el cursor y compresión al presionar. Tras la entrada, el globo metalizado se balancea sujeto por su cuerda durante 6s. Escena expresiva: 800ms; natural: 480ms; sutil: 240ms. Retraso entre filas: 55ms; controles: 180ms. |

Evidencia del repositorio en modo de solo lectura: `src/app/globals.css` tanto de t12 como de asesor, incluidos los alias semánticos compartidos y los roles de Taller. El mapeo conserva los nombres de rol del proyecto: `--fondo` → fondo, `--superficie` → tarjeta/ventana emergente, `--texto` → primer plano, `--texto-suave` → primer plano atenuado, `--acento`/`--sobre-acento` → par principal, `--borde` → borde/entrada y `--error` → destructivo. Los valores anteriores conforman una paleta explícita de exploración, no los valores actuales de producción. Los bordes interactivos son #54709a en tema claro y #a3b8e0 en tema oscuro. El foco usa el color principal con un contorno de 3px y un desplazamiento de 4px. El espaciado es semántico en los niveles de plano, grupo y campo, en lugar de aplicar ajustes arbitrarios a cada campo.

Fuentes de los componentes: `shadcn:button` (`@/components/ui/button`, default/outline/ghost/destructive y deshabilitado); `shadcn:input`, `shadcn:skeleton`, `shadcn:dropdown-menu`; `shadcn:checkbox`, `shadcn:dialog`, `shadcn:alert-dialog` con Animate UI. Un adaptador local de Button agrega `data-variant` porque el componente instalado consume su propiedad variant sin representar ese atributo; el botón real sigue a cargo de la semántica y la interacción con teclado. La ilustración de materiales es CSS, no una alternativa basada en generación de imágenes ni en un kit HTML. El constructor sin conexión real incorpora las fuentes a partir de archivos locales existentes. No se usan instalaciones, descargas, CDN, imágenes remotas ni fuentes remotas.

## 5. Navegación e interacción

Los selectores nativos del entorno de ejecución siguen siendo `view`, `state`, `scene`, `theme`, además de `motion`, con la etiqueta Mockup. Son controles de planificación externos al producto. El selector de idioma del producto permite previsualizar ES/EN; el idioma inicial sigue la configuración del navegador. La navegación dentro del mock conserva a la persona seleccionada y los cambios de cuenta; los campos de contraseña no persisten cuando se vuelve a montar una pantalla.

Las páginas con sesión iniciada muestran Ana Restrepo / Administradora, Mi cuenta y Cerrar sesión mediante un menú desplegable real. La aceptación del aviso actualizado bloquea la navegación del producto e inhabilita Mi cuenta hasta que se acepte; cerrar sesión sigue disponible. La navegación enfoca el título principal de la página. Los diálogos son primitivas reales de Base UI/Animate UI con fondo modal, operación por teclado y cierre con Escape. Las acciones destructivas usan AlertDialog, con una acción Cancelar explícita.

La estación activa se representa con una forma estática de selección. El entorno de ejecución vuelve a montar el producto al cambiar de vista o estado, por lo que **no se afirma que el disco sea un elemento compartido en movimiento**; la coreografía de vista/estado se muestra mediante el plano, la tipografía, los materiales y las filas que vuelven a asentarse.

## 6. Flujos de comportamiento preservados

1. **Iniciar sesión:** correo electrónico/contraseña → página solicitada si está permitida → de lo contrario, primera área permitida o Mi cuenta. La contraseña incorrecta, el correo desconocido, la cuenta desactivada y el bloqueo reciben el mismo rechazo, incluido el período de espera de quince minutos. No hay registro público ni servicio de envío de restablecimiento por correo.
2. **Activar:** nombre/correo invitado → contraseña dos veces, de 8–200 caracteres → aviso visible en el idioma del navegador y consentimiento sin marcar → activar → se inicia la sesión y se abre la primera herramienta permitida. El destino de muestra del Plan 2 es Chat asistido. El mock estático informa el destino, pero no implementa esa herramienta.
3. **Restablecer:** enlace generado por un administrador → contraseña nueva dos veces → confirmación → iniciar sesión. Los enlaces inválidos, usados y vencidos muestran el mismo mensaje para renovar. El restablecimiento no afirma que la sesión se inicie automáticamente.
4. **Aceptar aviso actualizado:** aviso bloqueante → aceptación explícita → confirmación registrada de versión/fecha → continuar. El mock ofrece el destino Cuentas del administrador de muestra.
5. **Mi cuenta:** identidad, rol y fecha del aviso → contraseña actual/nueva/confirmada → confirmación que explica que todas las sesiones anteriores finalizan y este navegador recibe una nueva.
6. **Invitar/administrar:** buscar/filtrar la lista → nombre/correo/empresa opcional/un rol → rechazar correo duplicado → mostrar un enlace copiable una sola vez. Los enlaces de invitación duran 7 días y los de restablecimiento, 24 horas; regenerar invalida los enlaces anteriores sin usar del mismo tipo. Si falla la copia, se permite seleccionar/copiar manualmente.
7. **Acciones de cuenta:** cambiar rol → efecto en la siguiente solicitud; desactivar/reactivar con explicación; eliminar solo con correo exacto y si no hay trabajo asociado. Camila demuestra CUENTA_CON_TRABAJO; Ana demuestra la restricción del último administrador; Julián demuestra la eliminación permitida. El gasto en IA se conserva sin datos personales como Cuenta eliminada. El mock no afirma que haya validación en el backend.
8. **Roles:** consultar cinco roles del sistema de solo lectura; crear/editar nombre personalizado y permisos mediante casillas; rechazar cero permisos con ROL_SIN_PERMISOS; impedir la eliminación mientras estén asignados a cuentas. El rol personalizado existente tiene dos cuentas; uno recién creado no tiene ninguna y puede eliminarse durante la demostración.

Los **12** controles corresponden exactamente al catálogo de permisos de PLAN T1.2, agrupados en 3/2/1/3/3. Plan 1 tiene 3 permisos, Plan 2 tiene 5, Plan 3 tiene 6, empleado tiene 9 y administrador tiene 12. Taller 3D es un solo permiso que incluye IA de escenas, planes, hoja de montaje, exportación y trabajo propio guardado. No se inventan permisos independientes para sus funciones.

## 7. Inventario de vistas

| Vista del entorno de ejecución | Contenido de trabajo / acción principal |
|---|---|
| login | Correo electrónico, contraseña y explicación del restablecimiento por administrador; Entrar. |
| activate | Identidad invitada, contraseña/confirmación, aviso completo, consentimiento; Activar cuenta. |
| reset | Contraseña/confirmación y recuperación para enlace inválido; Restablecer contraseña y luego iniciar sesión. |
| notice | Aviso completo bloqueante y consentimiento; Aceptar y continuar. |
| mine | Nombre, correo electrónico, rol, versión/fecha del aviso aceptado; contraseña actual/nueva/confirmada. |
| accounts | Búsqueda por nombre/correo electrónico, filtros de rol/estado; metadatos completos de cuenta, acción de detalles e Invitar persona. |
| invite | Nombre, correo electrónico, empresa opcional, resumen de rol/acceso; crear el enlace una sola vez y copiarlo. |
| detail | Identidad/empresa/estado/último acceso, rol editable, regenerar enlace, desactivar/reactivar, eliminación protegida. |
| roles | Cinco roles del sistema y ejemplo personalizado; permisos agrupados, nombre del rol y validación; crear/guardar/eliminar. |

Los datos de prueba del mock usan direcciones `.example` reservadas, fechas de acceso ficticias y un token visiblemente inválido. El acceso real, la revocación de tokens, la expiración de sesiones, la verificación de contraseñas, el almacenamiento de datos personales, la autorización por rol, la protección CSRF y la eliminación en la base de datos siguen siendo responsabilidades de producción de SP-1/SP-2. No se infiere conformidad legal ni aceptación del backend.

## 8. Estados y diálogos

Opciones visibles de Estado: normal, cargando (esqueleto estable), vacío, error, éxito, validación, enlace inválido, permiso denegado y sin conexión/pendiente. Opciones de escena: ninguna, aviso, enlace nuevo, desactivar/reactivar, eliminar cuenta, rol con cuentas. Cada estado puede alcanzarse con los selectores nativos; los controles dentro del producto también permiten abrir los diálogos correspondientes.

El estado vacío se aplica a los resultados de la lista y a los roles personalizados; los roles del sistema siguen visibles. Los formularios de autenticación no tienen un estado de colección vacía, así que seleccionarlo deja visible el formulario normal. El estado de enlace inválido se aplica a la activación/el restablecimiento; en otras vistas no inventa una condición de token. La validación corresponde específicamente a la contraseña/consentimiento, el correo duplicado o la ausencia de permisos para un rol. Sin conexión conserva la entrada visible y los datos obsoletos, explica que no se envió ni guardó nada e inhabilita el envío; el reintento es explícito. Denegado reemplaza el contenido protegido con instrucciones de recuperación. Los controles deshabilitados incluyen consentimiento sin aceptar, roles del sistema inmutables, envío sin conexión, último administrador protegido, trabajo asociado y correo de eliminación que no coincide.

Los estados de carga, éxito normal y datos de prueba nunca pretenden demostrar el comportamiento de la API. Los enlaces regenerados son deliberadamente tokens de demostración inválidos. El permiso del portapapeles puede fallar; el fallo se muestra en vez de inventar un éxito.

## 9. Comportamiento adaptable

- **>1100px:** márgenes exteriores de 40px, separación de 32px entre paneles, relleno de 34px en el plano, columnas completas para el listado.
- **761–1100px:** márgenes exteriores y relleno del plano de 28px, separación de 24px; la historia y los metadatos de la empresa se reorganizan dentro de cada registro.
- **≤760px:** márgenes exteriores de 20px, titular y material compactos, un plano de ancho completo con relleno de 22px, filtros y pares de campos apilados, metadatos del listado debajo de la identidad, grupos de permisos en una sola columna. La cinta transportadora permanece en el flujo y nunca se superpone al listado.
- Ancho exploratorio mínimo compatible: **360px**. El desplazamiento vertical natural permite recorrer textos de consentimiento y permisos extensos. Sin desplazamiento horizontal de página ni contenido accesible solo mediante gestos. El texto, los formularios, la ayuda y el pie usan ejes de contenedor compartidos explícitos.

## 10. Accesibilidad y objetivos de movimiento

WCAG 2.2 AA es el objetivo, no una afirmación de conformidad. El texto debe alcanzar ≥4.5:1, el texto grande ≥3:1 y los bordes interactivos ≥3:1 en ambos temas. Las superficies de trabajo opacas mantienen el contraste del texto durante toda la animación. Los campos tienen etiquetas visibles; la retroalimentación usa semántica de alerta/estado; los campos no válidos indican la retroalimentación correspondiente. El aviso está disponible en línea, no oculto tras un enlace legal pequeño. Los controles deshabilitados tienen explicaciones cercanas.

El movimiento es expresivo de forma predeterminada. La duración medida de las transiciones es de .8s en modo expresivo, .48s en modo natural y .24s en modo sutil. Se reserva la geometría del contenido final; el movimiento basado en transformaciones no desplaza el diseño. El balanceo del foil se pausa al pasar el cursor sobre la escultura, cuando el escenario sale de la ventana gráfica y en una pestaña oculta. `prefers-reduced-motion`, Quieto y `?still=1` eliminan el desplazamiento, el balanceo y las transiciones, y muestran de inmediato el mismo contenido y las mismas acciones. El titular, el acceso, el foil, la cuerda, el plano, las filas, la retroalimentación y los gestos de control tienen activadores distintos; no hay destellos ni cambios animados de opacidad del texto.

## 11. Aceptación observable y evidencia real

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 1280px | normal | La historia y el plano de trabajo están en columnas separadas; el encabezado y el pie comparten los ejes exteriores del escenario. |
| B-AC-02 | 360–390px | normal | Los filtros, campos y grupos de permisos se apilan sin desplazamiento horizontal; los metadatos del registro permanecen visibles. |
| B-AC-03 | all | activación | Activar cuenta está deshabilitado antes del consentimiento; las contraseñas coincidentes de ocho caracteres y el consentimiento habilitan el flujo de demostración. |
| B-AC-04 | all | inicio de sesión/error | Un único rechazo genérico incluye la espera de quince minutos; no identifica el motivo del fallo. |
| B-AC-05 | all | aviso | La navegación Cuentas/Roles no aparece antes de la aceptación; la opción para cerrar sesión sigue disponible. |
| B-AC-06 | all | detalles de cuenta | Las explicaciones sobre el trabajo propio y el último administrador están visibles junto a las acciones destructivas deshabilitadas. |
| B-AC-07 | all | diálogo de eliminación | Un correo electrónico incorrecto no puede habilitar la eliminación permanente; el correo electrónico exacto de la cuenta elegible sí puede hacerlo. |
| B-AC-08 | all | roles | Hay doce controles de permisos; Plan 3 tiene seis permisos de solo lectura; se rechaza un conjunto personalizado de permisos vacío. |
| B-AC-09 | all | diálogo de nuevo enlace | Una invitación renovada usa activar y 7 días; un restablecimiento usa restablecer y 24 horas; la explicación de revocación precede a la generación. |
| B-AC-10 | ambos temas | carga/error/sin conexión | Los indicadores de carga estables, el reintento explícito y las explicaciones sobre datos no enviados o desactualizados se distinguen visualmente. |
| B-AC-11 | all | movimiento reducido | No queda ninguna animación activa; todo el contenido y los controles habituales siguen disponibles. |
| B-AC-12 | 1280/390px | diálogos | Se abre un modal/alertdialog real con título/descripción y controles accesibles para cancelar/cerrar. |

Los resultados finales de las herramientas se registran a continuación. Los hallazgos iniciales se conservaron en la sesión: activador de cuenta comprimido, contraste de Reintentar de 4.42:1 y relleno de 5px en la acción Ver. Las causas se corrigieron en la composición real: dimensiones explícitas del activador, un punto de extensión de estilo para la variante renderizada y una columna más ancha para las acciones de fila. La acción secundaria para volver de la pantalla de restablecimiento también recibió un contorno visible, de modo que su etiqueta centrada sea un control explícito y no una línea de texto centrada aislada. No se modificaron umbrales ni reglas de comprobación.

- Compilación: constructor final real sin conexión, bibliotecas instaladas; **2637KB**, 2292 archivos de origen. Prefijo SHA-256 final del HTML: `a93dc792617df618`; TSX: `33f8fef4bd85dad7`.
- Contraste: HTML final, **158 pares entre tema claro y oscuro; todos aprobados**.
- Pruebas de renderizado específicas: **160 renderizados**, ES/EN, tema claro/oscuro, anchos de 360/390/768/1280, estados normal/error en cinco vistas representativas; **0 hallazgos de contraste, elementos no textuales, alineación, relleno o desbordamiento**.
- Comprobaciones de interacción: consentimiento/contraseña de activación; rechazo genérico al iniciar sesión; acceso condicionado por aviso/continuación; identidad de la cuenta seleccionada; ruta de invitación renovada/vencimiento de 7 días/Escape; eliminación con correo electrónico exacto; protección del trabajo/desactivación; protección del último administrador; 12 permisos/seis permisos de Plan 3; rechazo de cero permisos y eliminación de rol nuevo; correo electrónico duplicado; invitación/enlace y actualización de la lista. Todas aprobadas. Al principio, el localizador de prueba encontró el campo de entrada oculto de Base UI; la comprobación corregida usa el rol de casilla de verificación visible y se aprobó sin clics forzados.
- Observación de solicitudes en tiempo de ejecución: **cero solicitudes HTTP(S)**, **cero errores del navegador** durante esas interacciones.
- Movimiento reducido y `?still=1`: cero animaciones activas, con los mismos cinco controles de inicio de sesión que en el modo expresivo. Las duraciones naturales/sutiles medidas fueron de .48s/.24s. La estación activa es estática, como se documenta arriba.
- Capturas de pantalla inspeccionadas en memoria: inicio de sesión claro a 1280 y editor personalizado/roles oscuro; cuentas oscuro y activación claro a 390. Las capturas no son archivos adicionales fuera del alcance de salida asignado.
- Auditoría final: **504 de 504 combinaciones planificadas renderizadas**, 10,622 mediciones de texto, 1,366 paradas de foco en 1280/390px, tema claro/oscuro, cada vista/estado y diálogo. Comando: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r10.dir-b.html --max-combos 300`.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

- Comprobaciones finales del movimiento ambiental: se midieron `foil-arrive, foil-sway`; tanto el estado de desplazamiento sobre el elemento como el estado simulado de pestaña oculta indicaron `paused`. El movimiento reducido y `?still=1` indicaron cero animaciones activas.
- Comparación de direcciones: la comparación A/B/C actual de r10 devolvió inicialmente `ok: true`, `evidence_ok: true`, sin selectores faltantes. La similitud de diseño A/B fue .006; la de B/C, .053; la tipografía y el movimiento difieren en ambos pares. La prueba no encuentra navegación en la primera pantalla de B ni de C, por lo que `same_navigation: true` para B/C se registra fielmente; las afirmaciones sobre su navegación tras iniciar sesión se comprobaron por separado. La comparación del HTML reconstruido final también devolvió **`ok: true`, `evidence_ok: true`, `missing_evidence: []`**, con las mismas similitudes de diseño de .006 para A/B y .053 para B/C. El comando real `compare_directions.py A.html B.html C.html --json` se ejecutó sin conexión con los archivos hermanos actuales de r10 y se aprobó. Una importación intermedia de conveniencia en Python usó un nombre de función inexistente y no se ejecutó; la comparación directa mediante la CLI indicada arriba es la verificación que sí se completó.

## 12. Pregunta abierta y límites

P: ¿Qué identidad final del controlador de datos, contacto de privacidad, URL de la política y texto del aviso ES/EN aprobará el área legal de Sempertex para reemplazar el contenido ilustrativo entre corchetes antes de enviar invitaciones reales?

El texto de privacidad es un borrador ilustrativo visible, no una aprobación legal ni una afirmación de que los marcadores de posición estén listos para la publicación. La aceptación de origen y la seguridad deben verificarse en el producto implementado. No se afirma haber ejecutado lint, verificación de tipos, compilación de producción, pruebas del backend ni aceptación en producción del repositorio para una tarea exclusivamente de diseño. Las fuentes provienen de archivos locales existentes y se incluyen en el paquete para revisión; la selección de fuentes del producto final y la revisión de licencias corresponden a la finalización. La selección de dirección por parte del propietario y la aprobación del plan siguen pendientes.
