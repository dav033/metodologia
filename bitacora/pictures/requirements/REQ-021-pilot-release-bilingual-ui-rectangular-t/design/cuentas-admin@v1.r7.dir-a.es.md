---
name: Registro de acceso
status: draft
kind: independent-direction-exploration
subplan: SP-2
candidate-contract: cuentas-admin@v1
revision: r7
stance: operational-editorial
owner: David
date: 2026-10-26
---

# Registro de acceso — dirección A

Esta es una **exploración no aprobada**, no el contrato canónico de UI/UX ni un insumo para la implementación. No se modificó ningún contrato compartido, plan, repositorio, artefacto histórico ni estado de aprobación. Conserva el comportamiento compartido de SP-2 (digest `abde9480c2f8d545`), cubre R1/R3/R16 y explora la semilla operativa/editorial. La aprobación y la selección de dirección siguen a cargo del responsable.

## Concepto y recurso memorable

Pictures asigna a cada persona invitada que decora un conjunto específico de herramientas de trabajo. Esta dirección trata el acceso como un registro que se mantiene cuidadosamente: las personas, el rol, el estado y el último acceso permanecen visibles en conjunto; el margen editorial responde «Quién puede entrar». El **trazo de registro** se desplaza hasta su posición de reposo antes de que se fije el título de trabajo y las filas del registro se asienten en una secuencia mesurada. Es un único y sutil énfasis teatral en torno a la administración cotidiana.

El margen no es una barra lateral de aplicación que ocupe toda la altura. Forma parte de la composición tipográfica de la página, se reorganiza sobre el contenido en teléfonos y proporciona una línea base común para el formulario de cuenta, el texto de consentimiento y el pie de página. El encabezado más grande del margen y el encabezado más pequeño de la tarea cumplen deliberadamente funciones distintas: orientación y acción.

## Dos miniaturas y selección

- **Elegida: candidata 1**, `cuentas-admin@v1.r7.dir-a.html.candidate-1.html`: margen editorial, navegación breve de tres entradas y un registro de cuentas con líneas contiguo.
- Candidata 2, `cuentas-admin@v1.r7.dir-a.html.candidate-2.html`: registro de ancho completo debajo de un título grande y una franja de resumen. Se conserva como alternativa, pero los totales predominan en una tarea cuyo propósito es identificar y cambiar el acceso de una persona.

Ambas son composiciones visuales pequeñas en HTML, con recursos integrados, selector de tema claro/oscuro y adaptación para teléfonos. Se crearon antes de la maqueta completa en TSX. El diseño completo refina la candidata 1 en lugar de copiar un borrador anterior.

## Por qué esta no es la opción predeterminada

No hay una cuadrícula de tarjetas de panel, una barra de iconos, una fila ornamental de indicadores clave, una barra lateral coloreada de altura completa ni una tarjeta de autenticación centrada. El título ocupa un margen asimétrico; las herramientas y las personas identificadas ocupan la columna de trabajo. La autenticación usa exactamente la misma alineación editorial, de modo que el pie complementario comparte la coordenada x del formulario. Las acciones destructivas requieren una capa de confirmación aparte. El color se mantiene fuera de la navegación neutra.

La búsqueda de notas sobre el registro visual no encontró **notas de direcciones afines** para este requisito al momento de la exploración. Se consultaron los borradores existentes `taller-esenciales@v1.md` de SP-3 y `proyectos@v1.md` de SP-4 únicamente para mantener la identidad compartida: paleta de Pictures, alternativa sans serif del sistema, textos directos en español y administración compartida del menú de cuenta. Esta dirección no usa la composición de inspector/ventana gráfica del taller ni una cuadrícula de tarjetas/navegación de proyectos. No se afirma que otras direcciones desarrolladas en paralelo ya hayan pasado por una comparación.

## Ocho ejes

| Eje | Expresión implementada |
|---|---|
| Concepto | Un registro operativo de las personas que imaginan, calculan y construyen decoraciones: quién puede entrar y qué herramientas puede usar. |
| Diseño | Un margen editorial asimétrico de 232px y una columna de trabajo fluida, separados por 48px; los formularios de cuenta y sus pies comparten el borde izquierdo de la columna de trabajo. Por debajo de 768px, el margen pasa a ser un encabezado compacto sobre el contenido. |
| Navegación | Tres entradas de texto en el margen editorial (Cuentas, Roles y permisos, Mi cuenta), con una línea base neutra para el elemento activo; un menú de cuenta identificado en el encabezado principal. En teléfonos, la navegación pasa a ser una sola fila horizontal dentro del flujo, no un cajón. |
| Tipografía | Arial/sans serif del sistema, encabezado compacto de dos líneas de 34px en el margen frente a un título de tarea de 24px; registros de 13px y metadatos de 12px. La tipografía monoespaciada se reserva para las horas de acceso, las versiones de los avisos y los enlaces. |
| Densidad | Seis cuentas distribuidas en seis columnas de tabla en escritorio; registros planos con líneas en lugar de tarjetas. En teléfonos, los registros conservan la empresa, el rol, el estado y el último acceso en una jerarquía con etiquetas. Los formularios usan separaciones de 22px entre grupos e campos de 44px de alto. |
| Componentes | Botones e campos reales de shadcn/Base UI, casillas de verificación con Animate UI, diálogos, diálogos de alerta y menú desplegable de cuenta; un registro HTML semántico personalizado y una columna tipográfica. Las casillas de permisos agrupadas funcionan como comprobante de acceso a herramientas. |
| Color | El fondo lavanda neutro claro y el fondo casi negro oscuro existentes de Pictures, asignados a los roles del kit. El morado identifica la acción principal y la línea de registro; el verde/ámbar comunica el estado de la cuenta. Los tokens legibles de texto del proyecto también proporcionan los bordes de los controles. |
| Movimiento | Registro preciso en lugar de rebote elástico: barrido de línea desde la izquierda, recorte de panel de 12px, fijación del título de 5px y asentamiento de filas de 7px, con retrasos sucesivos de 35ms y cubic-bezier(.76,0,.24,1). Entrada escalada según el perfil: ~340ms expresiva / 178ms natural / 113ms sutil; el desplazamiento repetido al pasar el cursor o presionar permanece en 150–160ms. La preferencia de movimiento reducido y still=1 muestran de inmediato el mismo contenido final. |

La evidencia de selectores está en `cuentas-admin@v1.r7.dir-a.json`; las cuatro categorías de evidencia identifican elementos del producto renderizados. Los selectores de movimiento tienen fotogramas clave CSS reales o transiciones al pasar el cursor o presionar, no son solo nombres. No hay animaciones decorativas en bucle. Las entradas finitas se pausan en una pestaña oculta; el movimiento reducido y `?still=1` eliminan el desplazamiento y las transiciones, pero conservan el contenido y la respuesta a las acciones.

## Correspondencia con el sistema de diseño y componentes reales

Fuentes consultadas en modo de solo lectura: `src/app/globals.css` y los componentes de inicio de sesión en ambos worktrees registrados (`t12` y `asesor`); el manifiesto/entorno de ejecución real instalado y las exportaciones de componentes; SPEC, PLAN y el comportamiento compartido. Geist de producción recurre a la pila sin conexión Arial/Helvetica/sans-serif del sistema; no se descargaron fuentes ni recursos.

| Fuente de Pictures | Rol del kit | Claro / oscuro |
|---|---|---|
| `--fondo` | `--background`, `--sidebar` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--texto` | roles de primer plano | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | `--muted-foreground` | `#6b6178` / `#9aa1ad` |
| `--superficie-2` | `--secondary`, `--muted`, `--accent` | `#efe9f8` / `#242733` |
| `--borde` | `--border` decorativo | `#e3daef` / `#383c48` |
| `--texto-tenue` claro / `--texto-suave` oscuro | `--input` interactivo | `#766c85` / `#9aa1ad` |
| `--acento`, `--sobre-acento` | `--primary`, `--primary-foreground`, `--ring` | `#6d3fe0`, blanco / `#9479ff`, `#120b24` |
| `--acento-hover` | `--primary-hover` | `#5530b8` / `#a58dff` |
| `--error`, `--exito`, `--aviso` | destructivo, éxito, advertencia | valores del tema de origen |

La asignación de bordes legibles es deliberada: los bordes decorativos de origen no delimitan suficientemente los campos de entrada. No se editó ningún token de producción. El valor propuesto local para el estado de interacción destructivo al pasar el cursor es ligeramente más oscuro en el tema claro. Los tokens de gráficos no usados conservan los valores predeterminados del kit; no se dibujan gráficos.

| Procedencia del componente | Variante y propósito |
|---|---|
| `shadcn:button` — `@/components/ui/button` | acción principal, secundaria con borde, acción de texto y acción destructiva sólida; al pasar el cursor, foco y deshabilitado |
| `shadcn:input` — `@/components/ui/input` | campos identificados de correo electrónico/contraseña/texto, validación, deshabilitado |
| `shadcn:checkbox` — `@/components/ui/checkbox` | Animate UI/Base UI; consentimiento explícito del aviso y permisos de herramientas agrupados; marcado, sin marcar, solo lectura |
| `shadcn:dialog` — `@/components/ui/dialog` | Animate UI/Base UI para invitaciones, edición de cuentas y enlaces de un solo uso |
| `shadcn:alert-dialog` — `@/components/ui/alert-dialog` | confirmaciones separadas para eliminación/desactivación |
| `shadcn:dropdown-menu` — `@/components/ui/dropdown-menu` | menú de cuenta identificado, Mi cuenta y Cerrar sesión |
| `shadcn:skeleton` — `@/components/ui/skeleton` | cuatro barras de carga estables, sin reemplazo de página giratorio |
| Composición HTML nativa/personalizada | tabla semántica de cuentas, grupos de permisos con fieldset/legend, columna editorial, líneas de estado, avisos y selectores de producto |
| `@kit/mockup`, `@kit/motion`, `motion/react` | selectores de planificación nativos; estado del perfil/movimiento reducido; producto montado |

El constructor real estaba disponible y se usó correctamente. No se usaron un kit HTML de respaldo, instalación de paquetes, fuentes externas, imágenes remotas ni solicitudes de red en tiempo de ejecución para la maqueta completa. El HTML generado integra las bibliotecas instaladas; conserva la etiqueta visible “Mockup” y los selectores nativos `view`, `state`, `scene`, `theme`, `motion`. El selector de idioma adicional del producto controla explícitamente el aviso, cuyo texto completo aprobado en ES/EN se reproduce literalmente desde SPEC. La traducción de toda la interfaz queda para el trabajo posterior del plan.

## Comportamiento conservado y vistas disponibles

| Vista / escena | Comportamiento observable conservado | Fuente / consumidor |
|---|---|---|
| Iniciar sesión | Correo electrónico/contraseña; un mensaje de error indistinguible con espera de quince minutos; solicitudes de invitación/restablecimiento al administrador; sin registro abierto | R1 / T2.3 |
| Activar invitación | Nombre/correo electrónico de la persona invitada, dos contraseñas de mínimo ocho caracteres, aviso completo y versionado en el idioma del navegador, casilla de verificación explícita como requisito para la activación; al iniciar sesión, la página de destino es la primera herramienta permitida | R1 / T2.3 |
| Restablecer contraseña | Dos contraseñas nuevas que deben coincidir; los enlaces usados/vencidos usan el mismo flujo de recuperación que las invitaciones; después del restablecimiento, se vuelve al inicio de sesión | R1 / T2.3 |
| Aceptar aviso | La versión actualizada bloquea otras páginas; exige un nuevo consentimiento explícito; ofrece la alternativa de cerrar sesión | R1 / T2.3 |
| Mi cuenta / menú | Nombre, correo electrónico, rol, empresa y versión/fecha de aceptación; se requiere la contraseña actual para cambiarla; se cierran las demás sesiones y se renueva la de este navegador; cierre de sesión en el menú identificado | R1 / T2.4 |
| Cuentas | Seis personas de ejemplo, nombre/correo electrónico/empresa/rol/estado/último acceso; búsqueda y dos filtros; acción Gestionar accesible e individualizada para cada persona | R1, R16 / T2.5 |
| Invitar persona / enlace | Nombre/correo electrónico/empresa opcional/un rol; rechazo de correo electrónico duplicado; enlace de un solo uso para copiar, sin correo electrónico automático; vigencia de siete días | R1, R16 / T2.5 |
| Gestionar cuenta | Cambio de rol/plan; desactivar/reactivar; generar enlace de restablecimiento; nuevo enlace de invitación para una cuenta invitada; no permite cambiar la contraseña existente de la persona | R1, R16 / T2.5 |
| Nuevo enlace de invitación/restablecimiento | La confirmación explica que se invalidan todos los enlaces anteriores no usados del mismo tipo; el enlace se muestra una vez; el de restablecimiento vence en veinticuatro horas | R1 / T2.5 |
| Eliminar cuenta | Confirmación con el correo electrónico exacto para una cuenta sin trabajo; rechazo si hay trabajo guardado o si es la última cuenta administradora; gasto de IA conservado de forma anonimizada | R1 / T2.5 |
| Roles / Editor de rol | Cinco roles del sistema de solo lectura (3/5/6/9/12 permisos); rol personalizado con permisos agrupados por herramienta; rechazo sin permisos `ROL_SIN_PERMISOS`; no se puede eliminar un rol que tenga cuentas asignadas | R3, R16 / T2.5 |

Las claves de permisos son las doce indicadas en PLAN T1.2: `chat.usar`, `contador.usar`, `catalogo.ver`, `costos.usar`, `decoraciones.explorar`, `taller.usar`, `proyectos.ver_todos`, `gasto.ver`, `internas.usar`, `cuentas.administrar`, `roles.administrar`, `textos.corregir`. Los tres planes externos son roles del sistema, no un segundo campo de permisos independiente. El plan 2 explica explícitamente que no incluye Taller 3D. No se agregó ningún permiso, mecanismo de registro, servicio de correo electrónico ni cuenta real.

La vista previa es un **simulador estático de datos de ejemplo**: no ejecuta redirecciones del servidor, revocación de sesiones, validación de API 403/del mismo origen, invalidación real de tokens, anonimización ni entrega mediante portapapeles. Al copiar un enlace, se indica explícitamente que es una simulación. Los destinos de herramientas externas quedan fuera de SP-2; no se simula ninguna página de herramienta. Estas obligaciones de comportamiento siguen en la fuente compartida para el contrato final y la implementación. No se deben tratar las interacciones con datos de ejemplo como evidencia de pruebas del backend.

## Estados y reglas de adaptación

Los doce estados están disponibles en el selector nativo Estado: Normal, Cargando, Vacío, Error, Éxito, Validación, Sin permiso, Sin conexión, Enlace usado o vencido, Cuenta con trabajo, Último administrador, Rol con cuentas. Cada escena de diálogo se puede seleccionar por separado. La carga muestra contenido de esqueleto; el éxito y los errores muestran avisos anunciados; el modo sin conexión deshabilita las modificaciones y ofrece reintentar; la validación identifica los campos o el grupo de permisos. Los resultados vacíos de cuentas conservan los filtros; los roles vacíos conservan los cinco roles del sistema y explican que no hay roles personalizados. Los formularios de contraseña usan campos vacíos para el caso de ejemplo.

El vencimiento del enlace se aplica a la activación/restablecimiento. Los ejemplos de trabajo guardado y último administrador corresponden a la administración de cuentas; el rol en uso corresponde a la administración de roles. Estos estados especializados no inventan errores equivalentes en pantallas ajenas; la barra de herramientas permite inspeccionar cada eje por separado. El menú de cuenta corresponde a las pantallas con sesión iniciada. Los estados sin conexión, de carga y sin consentimiento incluyen ejemplos explícitos de controles deshabilitados. Esta exploración estática no pretende definir un modelo de producción completo para datos desactualizados ni para reintentos o revocaciones.

- **1024px en adelante:** margen editorial de 232px, separación de 48px, relleno exterior de 40px y registro de seis columnas. A 1440px, la separación entre columnas pasa a 64px dentro de un contenedor de ancho máximo de 1320px.
- **768–1023px:** margen de 190px, separación de 28px y relleno exterior de 24px. La búsqueda ocupa la primera fila de filtros; la empresa deja de aparecer entre las columnas visibles del registro de escritorio en este ancho intermedio.
- **360–767px:** relleno de página de 20px; el encabezado y la navegación de tres entradas fluyen sobre el contenido. La tabla se convierte en registros apilados con líneas, que conservan la empresa, el rol, el estado y el último acceso. Los campos del formulario/grupos de permisos se apilan. El formulario de autenticación y el pie conservan el mismo borde izquierdo. Los diálogos mantienen márgenes exteriores de 20px y relleno interior de 22px, con separaciones internas de 14px; el contenido del modal puede desplazarse en pantallas de poca altura.

Objetivos: contraste de texto WCAG 2.2 AA, límites interactivos y foco con relación 3:1, etiquetas semánticas y tablas/fieldsets, foco de teclado visible, fondo del modal inerte y restauración del foco. Los campos tienen 44px de alto; los botones, al menos 42px, con separación suficiente. Las casillas de permisos de los roles del sistema siguen marcadas visiblemente cuando están deshabilitadas. La revisión de implementación deberá verificar la conformidad completa, el uso con lectores de pantalla, el zoom y la cobertura en navegadores de producción; esta exploración no certifica esos aspectos.

## Evidencia de auditoría confiable

La primera auditoría completa midió 640 renderizados, 17,116 muestras de texto y 1,762 paradas de foco. Informó `RESULT: FAIL — alignment 2, padding 32`: la acción estrecha «Volver a roles» tenía una línea centrada aislada, y los diálogos telefónicos largos agotaban el relleno inferior. Se corrigieron ambos problemas: la acción para volver se alinea a la izquierda, se compactó el espaciado de invitación y la gestión de cuentas elimina los campos de identidad duplicados y el pie de página adicional en favor de una sola fila de acciones. Un nuevo renderizado focalizado a 390×900 no detectó problemas de alineación, relleno ni desbordamiento; los diálogos de invitación y cuenta se ajustan a su contenido (669px/683px).

La compilación sin conexión más reciente informa 757 KB y 2,292 archivos fuente. Verificación de tokens: `contrast: 158 pairs checked in light and dark, all pass`.

Auditoría completa final, después de las correcciones (código de salida 0):

```text
audit: cuentas-admin@v1.r7.dir-a.html — 640 renders (640 combinations planned), 17008 text measurements, 1771 focus stops
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Comando: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <assigned-html> --max-combos 400`. Se renderizó cada combinación planificada a 1280px y 390px en ambos temas; la auditoría también verificó el cambio de diseño durante la carga expresiva y la estabilización con movimiento reducido. No se informó ninguna advertencia de muestreo ni recorrido de foco truncado.

Las verificaciones focalizadas posteriores con Playwright pasaron: la casilla de consentimiento con nombre accesible controla la activación; recuperación idéntica para enlaces no válidos; coherencia del conteo de búsqueda y filtros; conteo de permisos de cinco roles de sistema de solo lectura (3/5/6/9/12); confirmación de eliminación mediante correo electrónico exacto; la cancelación de una invitación devuelve el foco a su elemento activador; sin desbordamiento horizontal de página a 360/390/768/1024/1280px en ambos temas; animación real del libro mayor en ejecución; `still=1` elimina las animaciones en curso; cero errores de página y cero solicitudes HTTP. Una prueba de humo inicial apuntó al campo de envío oculto de Base UI por id y agotó el tiempo de espera; al volver a ejecutarla con el rol accesible de casilla, pasó sin cambiar el artefacto del producto.

La herramienta de comparación confirmó sus 17 afirmaciones de selectores con `measure([this_direction])` (`evidence_ok: true`), incluido el movimiento real. No se realizó una comparación cruzada por pares: solo se midió la dirección asignada.

Se inspeccionaron capturas en memoria a 1280px y 390px en ambos temas: libro mayor de cuentas, activación/aviso, inicio de sesión, permisos de roles agrupados y modal de invitación. No se escribieron archivos de captura fuera de las rutas asignadas. Las verificaciones focalizadas y los conteos de la auditoría final indicados arriba corresponden al HTML compilado final.

## Impacto, preguntas y procedencia

Solo exploración; `cuentas-admin@v1.md` y `.html` canónicos permanecen intactos. Si se selecciona esta opción, la persona encargada de finalizar debe producir el borrador del contrato de doce secciones y dar cuenta de los cambios en la jerarquía, navegación y estructura adaptable. Esto sería **un cambio incompatible con una implementación del borrador anterior**, aunque se conserva el comportamiento del producto. Los consumidores pertinentes son SP-2 T2.1 (texto), T2.3 (autenticación/aviso), T2.4 (cuenta/menú), T2.5 (administración), T2.6 (integración) y T2.7 (aceptación visual); T2.8 es responsable de la aceptación independiente. No se requiere automáticamente que ningún subplan posterior adopte una exploración no aprobada.

P: Responsable/área legal de Sempertex — ¿Cuáles son el nombre legal definitivo de la entidad, la URL de la política de privacidad y el correo electrónico de contacto para asuntos de derechos? ¿El área legal de Sempertex revisó el aviso antes de invitar a usuarios reales?

La persona responsable elige la dirección en el flujo de comparación; este artefacto no solicita ni otorga aprobación.

| Entrada leída | SHA-256 |
|---|---|
| SPEC.md | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |
| design/cuentas-admin@v1.r7.behavior.md | `c665ab01443531a74cf5f1dc1cb936ab9e2d70f650308d6842f2cd4dd8072a43` |

SHA-256 del HTML final: `b75d76d3fc1749e933b2cbe580b536fd86e35f6af62894c6f72f8181cca4ac8b`.
