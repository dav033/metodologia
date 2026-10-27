---
contract: planes
version: 1
status: draft
artifact: ui-ux-contract
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
author: Designer
date: 2026-10-27
direction: Planos de consulta (b)
source_revision: r4.dir-b
source_behavior: planes@v1.r4.behavior.md
source: planes@v1.r4.dir-b.tsx
mockup: planes@v1.html
---

# planes@v1 — Planos de consulta

## 1. Identidad y trazabilidad

**Borrador; no aprobado para implementación.** Finalización de **Planos de consulta (b), r4**, seleccionado en la web por el propietario. La selección de dirección no implica la aprobación de este contrato. Este reemplaza el borrador canónico anterior, no aprobado, de la dirección C por la composición y el comportamiento seleccionados de B, incluida la vista de selección solo para comparación respondida en la ronda 13 y la referencia de movimiento visible inicial de r4. Conserva la composición, navegación, tipografía, paleta y movimiento seleccionados. El HTML se reconstruye directamente desde el TSX seleccionado e inmutable con el generador sin conexión actual; no se utiliza ninguna edición de exploración, parche de código fuente ni alternativa.

Insumos: SPEC.md (`status: ready`), esquema 1.3.0 de PLAN.json / revisión 2 de REQ-021, `planes@v1.r4.behavior.md` y los archivos Markdown, TSX y HTML autocontenido seleccionados de r4.dir-b. Rigen “Comportamiento — planes de acceso y sección de planes” y “Comportamiento — vista adicional de SP-14 (respuesta de la ronda 13)” de SPEC. La lista explícita de disponibilidad R18 prevalece sobre el paréntesis ambiguo anterior de Priorities: el chat extendido, la detección de estructura y la detección avanzada de globos no están disponibles; la calculadora de costos sí está disponible. Catálogo sigue siendo una herramienta del plan base, como se confirma en el comportamiento de SPEC y en el contrato del catálogo de SP-1.

| Instantánea de entrada | SHA-256 |
|---|---|
| SPEC.md | `7087fe226abd34699d6e0b5e4e4ad12c4d2cf67571e067506c38d41184f69792` |
| PLAN.json | `caa26fa2012bdf9e133483a40d6f2150f8a27ac9ed884054bdbbba134f548aa6` |
| planes@v1.r4.behavior.md | `3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239` |
| planes@v1.r4.dir-b.md | `8eb1aae36c8c2b417e7c855c0bd446fc65a28550d3ffbb9cbf6da456048c829a` |
| planes@v1.r4.dir-b.tsx | `6aa8d9aee13fd2ef7468f7d0930c4b5ca4cc9fa86a69b331f4246de47cf15ba7` |
| planes@v1.r4.dir-b.html | `174233f344c1f5c55c54a5abfae1ec89d3785a76641a65cdb2bfbfcd6eb8cb41` |

Solo SP-14 vincula `ui.contract=planes`, versión 1: T14.1 copia del diseño, T14.2 página pública y vista de selección adicional, T14.3 enlaces de entrada, T14.5 revisión visual. T14.4 verifica el comportamiento integrado en navegador y T14.6 audita las invariantes del catálogo, la ruta pública y los textos. SP-1 T1.2 es responsable de `plan-catalogue@1`; SP-1 proporciona `permission-map@1` y `session-guard@1`. SP-2 es responsable de las superficies de acceso y cuenta mediante `cuentas-admin@v1`; SP-14 agrega exactamente una entrada de planes en cada ubicación acordada. CG-4/T94 verifica la composición con el catálogo, la asignación de cuentas y la aplicación de permisos, sin convertirse en otro consumidor del contrato de interfaz.

| Requisito | Vistas / flujos | Criterios de aceptación |
|---|---|---|
| R17 catálogo único | V1–V4 / F1–F5 | UI-AC-01–08, 26; T14.2/T14.6 verifican las lecturas reales del catálogo |
| R18 sección pública e informativa | V1–V4 / F1–F5 | UI-AC-01–13, 17–22 |
| R19 enlaces de acceso/cuenta | V5–V6 / F1–F2 | UI-AC-14–16, 25 |
| R20 idioma y moneda | V1–V6 / F3 | UI-AC-03–05, 24 |

Registro integrado de versión e impacto, **2026-10-27 — planes@v1, borrador**: compatible con la exploración r4 B elegida; **incompatible con respecto al borrador C no aprobado que queda reemplazado**, porque difieren la jerarquía, la navegación local, la composición adaptable, las listas siempre visibles y la selección de comparación. Implementación afectada: planes/comparación/selección de T14.2 y composición de enlaces de entrada de T14.3; aceptación: T14.4/T14.5/T14.6. Acción requerida: aprobación independiente del propietario/plan para este par exacto; luego T14.1 copia la instantánea aprobada a `design/contracts/planes@v1.md`, T14.2/T14.3 la implementan y T14.5 compara el resultado renderizado. No se modifica ningún contrato aprobado existente ni se otorga aprobación. Un registro de cambios, historial o modificación independiente de PLAN queda fuera de esta delegación del par canónico; este registro integrado aporta la evaluación del impacto sin cambiar las referencias de los consumidores.

## 2. Propósito y usuarios

Una persona visitante o con sesión iniciada responde a la pregunta: ¿qué herramientas y precio mensual corresponden a cada plan de acceso? El objetivo se cumple al comparar las cuatro listas completas de herramientas, distinguir las que no están disponibles y volver a la superficie de origen. La vista de selección adicional permite resaltar un plan como preferencia temporal de comparación. Nunca asigna acceso.

La misma información de planes aparece para visitantes, cuentas con planes, cuentas con roles personalizados, empleados y administradores. En la comparación no se marca el plan actual de ninguna cuenta. La identidad de la cuenta en el encabezado heredado aporta contexto; no constituye una recomendación de comparación. Aquí no hay controles para comprar, pagar, suscribirse, solicitar, contactar, registrarse ni cambiar el acceso de una cuenta. Un administrador asigna planes desde la superficie de cuentas de SP-2. Los límites numéricos del chat, los contadores de uso y los mensajes de aplicación de límites quedan fuera de este requisito.

## 3. Arquitectura de la información y jerarquía

Conservar el encabezado circular con puntos de Pictures/Sempertex, el control de idioma, el menú de cuenta para usuarios con sesión iniciada y el pie de página. Después, incluir el H1 de la página y el enlace contextual para volver; dos enlaces de ruta neutros (“Comparar planes” y “Seleccionar para comparar”); la oración explicativa; y luego un índice local de planes junto a **una única hoja de comparación continua con bordes redondeados**. Cuatro cuadrantes del mismo nivel, separados por líneas, muestran Entusiasta, Designer, Designer Plus y Master Designer en el orden del DOM y de lectura. En escritorio se ubican, respectivamente, arriba a la izquierda, arriba a la derecha, abajo a la izquierda y abajo a la derecha. Ningún nivel se destaca como recomendado o actual.

Cada cuadrante contiene el nombre del plan como H2, el precio mensual, la etiqueta de referencia de comparación/selección cuando corresponda y, luego, “Herramientas incluidas” y su lista completa y acumulativa de herramientas. Todas las listas permanecen visibles. No hay secciones plegables, acordeones, controles para mostrar u ocultar herramientas ni una fila aparte de explorador listo para usar. El panel fijo repite el mismo nombre y precio obtenidos de los mismos datos del catálogo.

En la comparación completa, el panel fijo contiene anclas a los cuatro artículos. Inicialmente, Entusiasta lleva un marcador de verificación, una superficie resaltada sutil, una línea de acento y la etiqueta **Plan resaltado / Plan resaltado**. Esta referencia aporta la evidencia inicial de movimiento visible solicitada por el propietario; es idéntica para visitantes y personas con sesión iniciada y no inicializa una elección de comparación. En el modo de selección, el mismo panel se convierte en cuatro botones de selección única con estado presionado; debajo aparecen un resumen y un enlace para volver a la comparación completa. Los cuatro cuadrantes y sus listas permanecen presentes incluso después de elegir.

## 4. Sistema de diseño y lenguaje visual

Entradas fijas inspeccionadas en modo de solo lectura: `src/app/globals.css`, `layout.tsx`, `login/page.tsx`, `login/LoginForm.tsx`, `CabeceraApp.tsx` y `MenuApp.tsx` en t12 y asesor, además de `cuentas-admin@v1`, el proyecto hermano elegido y la procedencia de la dirección seleccionada. El shell actual del proyecto hermano “Parte de acceso” rige el contexto de acceso por invitación y cuenta, en lugar del antiguo formulario con contraseña compartida. Mantener la identidad existente de Pictures, la navegación neutral entre rutas, el vocabulario de papel y las fuentes Geist locales. No importar paletas específicas del taller en esta superficie.

| Token de Pictures | Rol / responsabilidad en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--superficie-suave` | cuadrante de comparación seleccionado | #faf8fd / #1c1e26 |
| `--superficie-2` | secundario, atenuado, estado neutral al pasar el cursor/deshabilitado | #efe9f8 / #242733 |
| `--texto` | primer plano, primer plano de tarjeta/ventana emergente/secundario | #1c1425 / #f4f5f7 |
| `--texto-suave` | primer plano atenuado, texto complementario | #6b6178 / #9aa1ad |
| `--texto-tenue` | límite de entrada/control, alias accesible heredado de SP-2 | #766c85 / #8a91a0 |
| `--acento` | primario, anillo, enlaces, marcador de comparación | #6d3fe0 / #9479ff |
| `--sobre-acento` | primer plano primario | #ffffff / #120b24 |
| `--acento-hover` | estado al pasar el cursor del primario de origen | #5530b8 / #a58dff |
| `--borde`, `--borde-suave` | contorno decorativo de hoja y reglas compartidas | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--aviso`, `--aviso-suave` | texto de estado no disponible/superficie de origen | #8f5f12, #fff3d8 / #f7c46b, #3f311c |
| `--error`, `--error-suave` | texto de error/superficie de origen | #b23a45, #ffeaec / #ff979f, #43252a |

El alias del borde de control usa el tratamiento accesible conservado del proyecto hermano, en lugar del `--borde` decorativo. Estas son correspondencias del diseño seleccionado, no una paleta nueva. Mantener los roles de radio: panel 32px, inserto 24px, campo 18px, píldora 999px. Geist Sans para el cuerpo, 15px/1.5; H1 24px/1.25 con peso 600; H2 del plan 20px/1.3 con peso 600; precio 22px con peso 600 y cifras tabulares (20px por debajo de 640px); herramientas 14px; leyendas, estado no disponible y pie de página 12px; texto complementario del formulario 13px. Geist Mono se limita al tratamiento heredado de metadatos/marca denominativa. Incluir los recursos WOFF2 locales existentes; no usar fuentes remotas.

Los componentes se nombran **fuente:id variante estado**:

| Componente | Importación real / responsabilidad |
|---|---|
| `shadcn:button outline ready\|hover\|focus\|pressed\|disabled` | `@/components/ui/button`, shadcn/Base UI real; reintento, regreso a la comparación y acciones de cuenta heredadas |
| `shadcn:button default ready\|hover\|focus\|pressed` | La misma importación; solo fixtures heredados de acciones de inicio de sesión/contraseña |
| `shadcn:input default empty\|filled\|focus\|invalid` | `@/components/ui/input`; campos heredados de correo/contraseña con etiqueta |
| `shadcn:skeleton default loading` | `@/components/ui/skeleton`; cuatro marcadores de posición del catálogo sin pulsación |
| `custom:plan-index anchor ready\|hover\|focus\|reference\|unavailable` | Anclas nativas en `.rail-options`; destinos de fragmento y enfoque programático del artículo |
| `custom:plan-selector single-choice unselected\|selected\|hover\|focus\|disabled` | Botones nativos con nombres calificados por plan y `aria-pressed`; sin semántica de radio ni asignación |
| `custom:comparison-sheet ruled normal\|reference\|selected` | Artículos semánticos, encabezados H2/H3 y listas en `.sheets`; datos acumulados completos |
| `custom:account-disclosure details closed\|open\|focus` | Shell nativo de details/summary conservado; enlaces/acciones, cierre con Escape y al hacer clic fuera; sin afirmar que sea un menú nuevo del kit |
| `custom:language-select native es\|en\|focus` | `select#language` nativo con etiqueta, independiente de los selectores de planificación |
| `custom:catalogue-message inline empty\|error\|offline` | Encabezado, texto de recuperación y botón real de reintento |
| `custom:comparison-marker shared-layout reference\|selected\|settled` | `motion.span` de `motion/react`, layoutId `comparison-marker`, icono Check de `lucide-react`; perfil de `@kit/motion` |
| `custom:mockup-controls inspector view\|state\|theme\|motion` | `mountMockup/useMockup` de `@kit/mockup`; selectores nativos externos de planificación |

El movimiento conserva las entradas espaciales opuestas de B: la barra desde x=-16px; los cuatro cuadrantes desde x=+22px, con intervalos de 45ms; opacidad .85→1; 440ms cubic-bezier(.16,1,.3,1). El marcador de referencia/selección, la etiqueta y la regla de acento de 44px se estabilizan desde scaleX(.85), opacidad .8. Al seleccionar, se mueve el marcador compartido con resorte (rigidez expresiva 220, amortiguación 16, masa .9). La respuesta rápida de controles usa 180ms cubic-bezier(.23,1,.32,1): al pasar el cursor, la barra se desplaza +4px; los botones se elevan -2px y al presionarlos se desplazan +1px/escala(.975). Natural usa 280/140/25ms para estabilización/respuesta rápida/intervalo; sutil usa 160/100/12ms. Estos tiempos de CSS son distintos del resorte del marcador compartido de Motion. No reemplazarlos por transiciones genéricas. Quieto, `?still=1` y la reducción de movimiento del sistema operativo se estabilizan de inmediato, incluidos los seudoelementos mediante el runtime actual; las animaciones CSS se pausan cuando la pestaña está oculta. Las entradas son finitas, sin efectos continuos fuera de pantalla.

## 5. Navegación y modelo de interacción

`/planes` es público y no requiere autenticación. `/planes?vista=seleccionar` representa la vista informativa adicional de selección. Ambas comparten el mismo contexto con sesión iniciada o cerrada. La navegación entre rutas muestra el enlace activo con `aria-current=page` y un subrayado neutral. La navegación del producto enfoca el H1 (`tabIndex=-1`) y comienza en la parte superior de la vista. La vista adicional no modifica ningún rol, permiso, campo de cuenta, cookie, almacenamiento ni dato del servidor.

El índice de comparación usa `#plan-entusiasta`, `#plan-designer`, `#plan-designer-plus` y `#plan-master-designer`. La activación desplaza la vista hasta el artículo nombrado y lo enfoca sin seleccionarlo; el desplazamiento adhesivo despeja el inspector en este artefacto y el chrome persistente en producción. Los botones de elección mantienen el foco al activarse, exponen solo un `aria-pressed=true`, resaltan el cuadrante correspondiente y anuncian su nombre en el resumen de selección cortés. El regreso a la comparación completa conserva este resaltado de comparación en memoria; nunca se convierte en el “plan actual”. Al entrar a la vista adicional en una sesión nueva, no hay ninguna elección, independientemente de la referencia visual inicial de Entusiasta.

Aparece un único enlace “Planes / Plans” después de las instrucciones para restablecer el formulario de inicio de sesión. El desplegable de cuenta contiene una entrada “Planes / Plans” entre “Mi cuenta / My account” y “Cerrar sesión / Sign out.”. Si la sesión está cerrada, el regreso lleva a `/login`. Si la sesión está iniciada, el regreso lleva a la página desde la que la persona abrió la sección de planes, sin modificar la sesión ni el acceso. El fixture muestra Mi cuenta (`/cuenta`) como origen; producción debe conservar el origen interno real. El acceso directo con sesión iniciada usa el destino seguro de cuenta existente, no una URL externa. SP-2 controla la navegación de cuenta, la autenticación y el cierre de sesión; aquí solo se agregan los dos enlaces a planes.

## 6. Flujos

**F1 — Comparación de visitante.** Abrir el inicio de sesión → seguir el único enlace a planes → leer los cuatro planes y las listas completas de herramientas → usar opcionalmente un ancla de plan → volver al inicio de sesión. Ni el acceso ni la lectura requieren credenciales.

**F2 — Comparación con sesión iniciada.** Abrir el desplegable de cuenta heredado → seguir su única entrada a planes → mantener la cabecera con sesión iniciada → comparar los mismos datos públicos → volver a la página interna de origen. Escape cierra el desplegable y devuelve el foco a su resumen; un clic fuera lo cierra.

**F3 — Idioma.** En la visita inicial, si el idioma del navegador es inglés, se muestra EN/USD; si es español o un idioma no compatible, se muestra ES/COP. Hasta SP-8, rige la regla de idioma del navegador; el fixture usa `navigator.language`, mientras que producción sigue su política establecida para Accept-Language/avisos sobre datos. El control visible ES/EN cambia todo el texto del producto y los precios a la vez, sin cambiar la vista, la preferencia de comparación ni la asignación de cuenta. Este fixture conserva el idioma solo en memoria; SP-8 controla la persistencia del idioma en toda la cuenta. Nunca mostrar ambas monedas a la vez.

**F4 — Elección solo para comparar.** Desde cualquiera de los contextos de comparación, seguir “Seleccionar para comparar / Select to compare” → leer la explicación explícita de que la cuenta no cambia → inicialmente no ver ninguna elección → activar cualquiera de los cuatro botones de plan → ver su estado presionado, marcador, etiqueta del cuadrante y resumen → elegir otro si se desea → “Volver a la comparación completa / Back to full comparison.”. Todas las listas permanecen visibles en todo momento. Al volver, se conserva la preferencia de comparación en memoria; la carga de un documento nuevo la restablece. El estado simulado `selected` puede precargar Designer Plus solo para inspección.

**F5 — Fallo y recuperación del catálogo.** Durante la carga se muestran esqueletos y se anuncia el progreso. Si el catálogo está vacío, malformado, produce un error o está sin conexión, la hoja se reemplaza con la explicación correspondiente y Retry. Los controles de elección se deshabilitan mientras los datos no estén disponibles y las anclas del índice no desplazan el foco a artículos inexistentes. Retry vuelve a cargar el catálogo completo; el mock restaura su fixture local completo. Nunca inferir un precio faltante, mostrar una comparación parcial engañosa ni tratar datos no disponibles como una lista vacía cargada correctamente.

## 7. Especificaciones de vistas

| ID / vista nativa | Estructura, acciones y alcance |
|---|---|
| V1 `compare` | `/planes` público con sesión cerrada: cabecera sin desplegable de cuenta; H1 Planes/Plans y regreso al acceso; dos enlaces de ruta; “Un administrador asigna el plan. / An administrator assigns the plan.”; barra de anclas; hoja de cuatro cuadrantes; pie de página heredado. La referencia inicial de Entusiasta es solo visual. F1, F3, F5. |
| V2 `compare-signed` | Los mismos datos y composición que V1, con el desplegable de cuenta heredado y el regreso contextual para sesión iniciada. Sin insignia de plan actual ni información adicional del personal. F2, F3, F5. |
| V3 `select` | Vista adicional con sesión cerrada; H1 “Seleccionar para comparar / Select to compare”; enlace de ruta activo; “La selección solo resalta un plan para comparar. No cambia el plan de tu cuenta. / Selection only highlights a plan for comparison. It does not change your account plan.”; barra con estado presionado; hoja completa; resumen dinámico; regreso a la comparación completa. F3–F5. |
| V4 `select-signed` | Igual que V3, con el desplegable/contexto de cuenta conservado. Seleccionar Master Designer nunca modifica la identidad Entusiasta del fixture ni la asignación/acceso de la cuenta real. F2–F5. |
| V5 `login` | Papel de acceso SP-2 centrado y conservado, campos de correo/contraseña, instrucciones de acceso solo por invitación/restablecimiento y acción; exactamente un enlace agregado a Planes después de las instrucciones. Los envíos del formulario muestran una explicación simulada y no envían credenciales. SP-2 rige los estados reales de inicio de sesión. F1. |
| V6 `menu` | Papel de Mi cuenta de SP-2 y desplegable de cuenta conservados, abierto inicialmente para inspeccionar la entrada; la identidad y el fixture de contraseña siguen siendo contextuales. La única entrada a Planes se ubica entre Mi cuenta y el cierre de sesión. El formulario de contraseña es simulado; SP-2 rige el comportamiento real de la cuenta. F2. |

Un catálogo simulado derivado de los requisitos proporciona tanto la barra como la hoja. En producción, nombres, traducciones, orden, precios, herramientas y disponibilidad se leen exclusivamente de `src/lib/planes/catalogo.ts` (`plan-catalogue@1`), no de un segundo arreglo propio de la página. Al finalizar, ese archivo no está presente en ninguno de los worktrees de entrada; este artefacto estático no demuestra la integración del catálogo.

| Orden / nombre ES → EN | Precio mensual ES / EN | Lista completa visible de herramientas en orden |
|---|---|---|
| 1 Entusiasta → Enthusiast | Gratis / Free | Chat con límites; Contador de globos; Catálogo |
| 2 Designer | 20.000 COP / mes; 7 USD / month | Chat con límites más altos; Contador de globos; Catálogo |
| 3 Designer Plus | 45.000 COP / mes; 14 USD / month | Chat con límites más altos; Contador de globos; Catálogo; Calculadora de costos; Chat ampliado; Detección de estructuras; Detección avanzada de globos |
| 4 Master Designer | 70.000 COP / mes; 25 USD / month | Las mismas siete entradas que Designer Plus, seguidas de Taller 3D |

La tabla documenta ambos idiomas; la interfaz renderizada muestra solo el idioma activo. Gratis no tiene un monto cobrado. Los montos pagados usan los separadores del idioma activo y el sufijo explícito de moneda/mes. Las etiquetas en inglés de las herramientas son “Chat con límites”, “Chat con límites más altos”, “Contador de globos”, “Catálogo”, “Calculadora de costos”, “Chat ampliado”, “Detección de estructuras”, “Detección avanzada de globos” y “Taller 3D”. Cada una de las tres herramientas no disponibles lleva la etiqueta **aún no disponible / not available yet** en ambos planes superiores, seis etiquetas de estado en total. No tienen controles de activación. La calculadora de costos está disponible. Taller 3D incluye el explorador de decoraciones listas para usar sin una fila aparte. No se muestran números de límites.

## 8. Estados

| Estado nativo / aplicabilidad | Resultado visible, acciones y transición |
|---|---|
| `normal`, V1–V4 | Listas completas de herramientas 3/3/7/8 y cuatro precios. Una comparación nueva muestra Entusiasta como referencia; una selección nueva no tiene ninguna opción activada y el resumen dice “Ningún plan seleccionado”. |
| `selected`, V1–V4 | Preferencia de comparación inspeccionable: Designer Plus si no existe ninguna; de lo contrario, se conserva la preferencia elegida. En producción se llega aquí mediante F4. La etiqueta es “Seleccionado para comparar”, nunca una asignación a la cuenta. |
| `loading`, V1–V4 | Cuatro grupos de esqueletos reemplazan los datos; estado `aria-busy=true` y mensaje “Cargando planes…”. No se muestra ningún precio estimado ni una opción activa. |
| `empty`, V1–V4 | “No hay planes disponibles”; “Vuelve a intentarlo para consultar los planes.”; “Reintentar.” |
| `error`, V1–V4 | Alerta: “No se pudieron cargar los planes”; mensaje de recuperación y Reintentar. Si faltan campos obligatorios del catálogo o tienen un formato incorrecto, se muestra un error y nunca un resultado parcial. |
| `offline`, V1–V4 | “Sin conexión”; “Conéctate y vuelve a cargar los planes.”; Reintentar. No se muestran precios desactualizados como si fueran actuales. |
| Opción deshabilitada, estados con datos no disponibles de V3–V4 | Los botones exponen la semántica nativa de deshabilitado, con superficie neutra y texto legible, sin acción de selección. Siguen disponibles el regreso y la navegación contextual. |
| Hover/foco/activado, controles interactivos | Contorno de foco de acento visible, movimiento breve que se mantiene y respuesta al estado activado; ninguna información ni acción depende únicamente del hover. |
| Recuperación/éxito, V1–V4 | Un reintento exitoso vuelve a `normal` con todos los datos. Una opción anuncia su nombre sin notificación emergente ni afirmar que se asignó. |
| Validación/permiso denegado | No hay formularios de planes ni requisitos de permisos en una sección pública de solo lectura; no aplican aquí. La validación heredada de autenticación/cuenta corresponde a SP-2; V5/V6 no implementan su backend. |
| Escritura parcial/desactualizada/pendiente | No se admite deliberadamente mostrar un catálogo parcial o desactualizado: se usa la recuperación de error/sin conexión. No se inicia ninguna escritura en la cuenta, por lo que los estados de escritura pendiente, confirmación de asignación y asignación denegada no aplican. |

Inspector externo: los selectores nativos `view`, `state`, `theme`, `motion` tienen las etiquetas Vista, Estado, Tema y Movimiento; los valores de tema son light/dark y los perfiles son expressive/natural/subtle/still. No se declara ningún diálogo, así que no se necesita un selector `scene`. Los seis estados del catálogo se pueden alcanzar desde el inspector; en V5/V6, el selector de estado no inventa estados paralelos de autenticación. El inspector, el título de revisión de origen y el pie “Mockup · Datos y operaciones simulados” establecen que se trata de una fixture y no son nuevos flujos de producción.

## 9. Comportamiento adaptable

| Ancho | Diseño y adaptaciones |
|---|---|
| 320–639px, incluido el valor requerido de 390px | Márgenes exteriores de 20px; el encabezado principal se ajusta en varias líneas y las herramientas de idioma/cuenta pasan a la fila siguiente si es necesario; el encabezado y el botón de regreso se apilan; los enlaces de ruta se ajustan; panel de navegación en cuadrícula de 2×2; panel continuo de planes en una columna y en orden de catálogo; relleno interior de panel de 20px y precios de 20px. El resumen de selección se apila y el botón de regreso ocupa todo el ancho. Sin desplazamiento horizontal de página. |
| 640–839px, incluido el valor de 768px | Márgenes de 24px; panel de navegación en cuadrícula de 2×2 encima del panel de planes; panel en dos columnas iguales, con relleno interior de 24px; el resumen y el botón de regreso se ajustan dentro del flujo normal. Sin barra lateral de ancho fijo. |
| 840–1099px, incluido el valor de 1024px | Panel de navegación de cuatro columnas encima del panel de planes; panel en dos columnas; márgenes de 24px. El resumen queda junto al botón de regreso cuando hay espacio; el encabezado se ajusta. |
| ≥1100px, incluido el valor requerido de 1280px | Ancho máximo de la aplicación de 1520px; márgenes exteriores de 40px; barra lateral fija de 216px, espacio de 28px y panel flexible de planes en cuadrícula de 2×2. La parte superior de la barra queda a la altura del chrome persistente +20px. Relleno interior de los cuadrantes de 24px. |

Los nombres, las etiquetas de estado, el texto traducido y los precios se ajustan dentro de las pistas de cuadrícula con min-width:0. El panel de cuenta permanece dentro del ancho de la ventana; flota desde el encabezado principal sin comportamiento modal. Los controles nuevos tienen una altura mínima de 44px; los elementos del panel de navegación son más altos para mostrar el nombre y el precio. En escritorio, los cuatro encabezados y las primeras filas aparecen en la primera vista; las listas largas siguen disponibles mediante el desplazamiento vertical normal. El reajuste a 320px y la ampliación del texto deben conservar todo el contenido y los controles; ninguna altura fija recorta una lista de herramientas.

## 10. Objetivos de accesibilidad

Se busca un comportamiento aplicable conforme a WCAG 2.2 AA; este borrador y las comprobaciones automatizadas no certifican la conformidad. En producción se usan las regiones de encabezado/navegación/contenido principal/pie de página, un H1, un H2 por plan con nombre, un H3 para las herramientas y listas semánticas. El generador sin conexión actual proporciona `main#app` alrededor de la composición `.app` seleccionada; esta región principal se verificó en el DOM renderizado canónico. Los iconos decorativos de anillo, marca y flecha tienen `aria-hidden=true`; el texto visible comunica el significado del plan y su disponibilidad.

El orden del teclado sigue el DOM: controles compartidos, regreso contextual, navegación de rutas, panel de navegación, contenido, regreso de selección y controles de pie de página/entrada, según corresponda. Los enlaces se activan con Enter; los botones de opción, con Enter/Espacio; el resumen desplegable, con Enter/Espacio. Los destinos programáticos H1/artículo usan `tabIndex=-1`. Al elegir una opción, el foco se conserva; Escape cierra el panel de cuenta y devuelve el foco a su resumen. No se aplica una trampa de foco modal. Las acciones de divulgación son controles alcanzables con Tab en el orden normal; no se deben asignar roles de menú sin implementar su patrón de teclado.

El foco es un contorno de 3px de color de acento, con un desplazamiento de 4px, visible en enlaces/botones/campos de entrada/selectores/resúmenes. Asegúrate de que el foco de los destinos de índice no quede recortado ni oculto debajo del chrome. El objetivo de contraste del texto es ≥4.5:1; los bordes esenciales de controles y los indicadores de foco/selección, ≥3:1. Las líneas decorativas del papel no son el único límite de un control. La selección de comparación tiene un estado activado, una marca, una etiqueta explícita y un resumen dinámico, en lugar de depender solo del color. La carga/el estado/la recuperación se anuncian de forma cortés; los errores usan `role=alert`. Los controles nativos deshabilitados comunican que los datos no están disponibles. Los objetivos táctiles tienen al menos 44px de alto, por encima del mínimo aplicable de 24px; debe haber separación adecuada y ajuste de texto.

Los modos de movimiento reducido/Quieto/still deben detener las animaciones CSS, de pseudoelementos y de Motion, y conservar los mismos datos visibles, la selección y el foco. Ninguna animación condiciona el acceso al texto. Durante la implementación, comprueba el reajuste, la ampliación del texto al 200%, el teclado y el comportamiento de lectura/anuncios del lector de pantalla; los formularios estáticos de la fixture no demuestran la conformidad de la autenticación accesible.

## 11. Criterios de aceptación visual y evidencia de verificación

Todos los criterios se aplican a ambos temas y ambos idiomas, salvo que el estado indique lo contrario. “Todos los anchos admitidos” significa 320px en adelante, con las adaptaciones de §9; los anchos principales para la comprobación renderizada son 390/768/1024/1280px.

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| UI-AC-01 | Todos los anchos admitidos | V1–V4 normal/selected | Los cuatro artículos aparecen en el orden DOM Entusiasta/Enthusiast, Designer, Designer Plus, Master Designer. |
| UI-AC-02 | Todos los anchos admitidos | V1–V4 normal/selected | Las listas completas de herramientas 3/3/7/8 permanecen visibles sin un control para mostrar/ocultar herramientas. |
| UI-AC-03 | Todos los anchos admitidos | ES normal/selected | Los planes pagos muestran 20.000, 45.000 y 70.000 con COP / mes, y ningún valor en USD. |
| UI-AC-04 | Todos los anchos admitidos | EN normal/selected | Los planes pagos muestran 7, 14 y 25 con USD / mes, y ningún valor en COP. |
| UI-AC-05 | Todos los anchos admitidos | ES/EN normal | El primer plan es Entusiasta/Enthusiast y muestra Gratis/Gratis, respectivamente. |
| UI-AC-06 | Todos los anchos admitidos | V1–V4 normal/selected | Cada plan superior tiene tres etiquetas de no disponible para chat extendido, detección de estructura y detección avanzada de globos. |
| UI-AC-07 | Todos los anchos admitidos | V1–V4 normal/selected | Entusiasta usa la frase con límites y Designer, la frase con límites más amplios, sin cifras de límites. |
| UI-AC-08 | Todos los anchos admitidos | V1–V4 normal/selected | Solo Master Designer incluye Taller 3D/3D workshop, sin una fila independiente para explorador. |
| UI-AC-09 | Todos los anchos admitidos | Comparación nueva normal | Entusiasta muestra un marcador en la barra lateral y la etiqueta Plan resaltado/Plan destacado antes de que el visitante interactúe. |
| UI-AC-10 | Todos los anchos admitidos | Selección nueva normal | Ningún botón está activado y el resumen dice Ningún plan seleccionado. |
| UI-AC-11 | Todos los anchos admitidos | Selección después de elegir | Solo está activado el botón del plan elegido y su nombre aparece en el resumen cortés y en el cuadrante resaltado. |
| UI-AC-12 | Todos los anchos admitidos | Regreso después de elegir | La comparación completa conserva el resaltado y todas las listas de herramientas. |
| UI-AC-13 | Todos los anchos admitidos | V1–V4 todos los estados | No aparece ningún control de compra, solicitud, contacto, registro o cambio de plan de cuenta. |
| UI-AC-14 | 390/1280px | V5 inicio de sesión | Aparece exactamente un enlace a Planes después de las instrucciones para restablecer la cuenta y abre la comparación con la sesión cerrada. |
| UI-AC-15 | 390/1280px | V6 panel de cuenta abierto | Aparece exactamente una opción Planes entre Mi cuenta y Cerrar sesión y abre la comparación con la sesión iniciada. |
| UI-AC-16 | Todos los anchos admitidos | Regreso con sesión iniciada/cerrada | El botón de regreso conserva el contexto: inicio de sesión para visitantes y la página interna de origen para personas con sesión iniciada. |
| UI-AC-17 | 1280px | V1–V4 normal | Una barra lateral de 216px y un espacio de 28px preceden a un panel redondeado único, dividido en cuadrícula de 2×2. |
| UI-AC-18 | 768px | V1–V4 normal | Un panel de navegación superior de 2×2 precede a un panel de dos columnas sin desbordamiento horizontal de página. |
| UI-AC-19 | 1024px | V1–V4 normal | Un panel de navegación superior de cuatro columnas precede a un panel de dos columnas. |
| UI-AC-20 | 320/390px | V1–V4 normal/selected | El panel de navegación tiene dos columnas y los artículos de planes se apilan en una columna sin desbordamiento horizontal de página. |
| UI-AC-21 | Todos los anchos admitidos | loading | Cuatro grupos de esqueletos reemplazan los datos disponibles y se anuncia el estado de carga. |
| UI-AC-22 | Todos los anchos admitidos | empty/error/offline | El encabezado y el texto de recuperación, junto con Reintentar, reemplazan el panel y los controles de selección de planes están deshabilitados. |
| UI-AC-23 | Todos los anchos admitidos | Foco del teclado | Cada control interactivo tiene un contorno visible; la activación del ancla de comparación enfoca el artículo de destino. |
| UI-AC-24 | Todos los anchos admitidos | Cambio de idioma | El texto del producto y la moneda cambian juntos mientras se conserva la opción de comparación. |
| UI-AC-25 | 390/1280px | Panel de cuenta abierto | Escape cierra el panel y devuelve el foco a su resumen. |
| UI-AC-26 | Todos los anchos admitidos | Implementación basada en catálogo | Al cambiar el precio de un elemento del catálogo, se actualizan tanto el panel de navegación como el panel de planes, sin editar los datos de la página. |
| UI-AC-27 | 1280px | Comparación expressive inicial | La barra lateral, los cuadrantes, el marcador de referencia y la etiqueta resaltada se animan visiblemente con la gramática de entrada opuesta conservada. |
| UI-AC-28 | 390/1280px | Quieto / still / movimiento reducido del SO | No queda ningún movimiento activo de entrada, marcador o pseudoelemento; los datos y la comparación elegida siguen visibles. |
| UI-AC-29 | Todos los anchos admitidos | Elección en V4 y luego regreso | La opción de comparación no cambia la identidad de la cuenta, el plan asignado ni los permisos de la siguiente solicitud. |

Verificación reciente del artefacto canónico al 2026-10-27:

- Compilación sin conexión actual: `python3 /home/david/.agents/skills/metodologia/scripts/bitacora.py components mockup build <design>/planes@v1.r4.dir-b.tsx --out <design>/planes@v1.html` — **APROBADO**, 553 KB, 2,031 archivos fuente incluidos en el paquete. El código fuente exacto no tuvo cambios. No se instalaron paquetes, no se descargaron recursos de red, no se usaron alternativas ni se modificó el HTML generado.
- `python3 <kit>/kit/contrast.py <design>/planes@v1.html` — **contraste: se comprobaron 158 pares en temas claro y oscuro; todos aprobaron**, código de salida 0.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.html --widths 1280,390,768,1024` — **288 renderizados (se planificaron 288 combinaciones), 9136 mediciones de texto, 560 paradas de foco**, código de salida 0. Las seis vistas y los seis estados, ambos temas y los cuatro anchos; sin advertencias de muestreo.

**RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**

- Pruebas complementarias en caché con Playwright contra el HTML canónico — **144 escenarios APROBADOS**, incluidas 128 combinaciones adaptables en 320/390/640/768/840/1024/1100/1280px, ES/EN, ambos temas y los cuatro contextos de comparación/selección. Se verificaron las listas 3/3/7/8, seis etiquetas de no disponible, moneda, composición en los puntos de quiebre, selección inicialmente vacía, las cuatro rutas de elección/regreso, identidad y almacenamiento de la cuenta sin cambios, recuperación de errores, ambos enlaces de entrada y regresos contextuales, foco en artículos, selección con Espacio, Escape/cambio de foco de la cuenta, Quieto, `?still=1` y movimiento reducido del SO. No hubo errores de página ni solicitudes HTTP externas. Esto establece el comportamiento de la fixture; no demuestra la asignación real de cuentas ni los permisos del servidor.
- Una nueva prueba de primera carga expressive encontró en ejecución `railArrive` en la barra lateral, cuatro efectos `paperArrive` en los cuadrantes y `selectionLine` tanto en el marcador de referencia inicial como en su etiqueta, sin intervención del visitante. Los modos reducidos no tenían animaciones en ejecución, incluidos los efectos de pseudoelementos en el entorno de ejecución actual.
- Se inspeccionaron en memoria capturas de pantalla estabilizadas a **1280/390px en ambos temas**: comparación ES clara y selección con sesión iniciada EN oscura. Conservan la disposición elegida de barra lateral/panel, los planes apilados en teléfono, el encabezado principal compartido, las listas completas legibles y el resumen/botón de regreso de selección. No se guardaron archivos de capturas ni se creó una vista previa independiente.
- SHA-256 del HTML canónico: `418c789b8994b99a38cffae95326087d7ad72210026299054993fccd3c7bd58d`. El inspector incluido en el paquete del documento conserva el título del código fuente seleccionado r4/B/Draft; el documento es el artefacto canónico recompilado. Ningún defecto de comportamiento verificado requirió modificar localmente el código fuente o el HTML.

`<design>` es el directorio de diseño de este requisito; `<kit>` es `/home/david/.agents/skills/metodologia/agents/designer/skills/david-ui-kit`. La verificación del catálogo de producción, la autenticación/permisos, las tecnologías de asistencia y la conformidad completa con WCAG siguen pendientes en T14.2–T14.6.

## 12. Preguntas abiertas y supuestos

**Preguntas abiertas para el responsable: ninguna.** La ronda 13 resolvió la decisión de comparación únicamente, las herramientas siempre visibles y el comportamiento en tabletas. El brief delegado registra B como la nueva dirección seleccionada; las referencias a la antigua selección C dentro del historial inmutable de exploración son históricas. Ni la selección ni este borrador constituyen una aprobación.

Límites confirmados o diferidos: no hay valores numéricos de límites ni mecanismos para aplicarlos; no hay marcador del plan actual; no se puede comprar, solicitar, contactar ni registrar; Master Designer es responsable de todo el conjunto de herramientas 3D; SP-2 conserva el comportamiento de cuenta y acceso; SP-1 es responsable del catálogo. La persistencia del idioma para toda la cuenta sigue asignada a SP-8. Estos no son preguntas nuevas.

Supuestos y límites de los datos de prueba: las identidades neutrales `@prueba.local` y los valores del catálogo son datos simulados; la comparación y el idioma se mantienen en memoria; la recuperación restaura los datos de prueba locales; Mi cuenta es el origen demostrado con sesión iniciada; los formularios nunca envían credenciales. El HTML final conserva intencionalmente la etiqueta del inspector de la fuente seleccionada r4/B/Draft. No se crea una vista previa aparte porque la vista previa está sin configurar o desactivada y solo está asignado el par canónico. La falta de integración con el catálogo en producción es trabajo de implementación previsto, no evidencia de un backend funcional. T14.4/T94 deben verificar en producción el comportamiento completo de retorno al origen y las invariantes de sesión y permisos.

**INQUIETUDES:** El borrador sigue sin aprobar; todavía se requiere aprobación independiente. Auditoría real sin conexión: **RESULTADO: APROBADA — no se encontraron problemas de contraste, contenido no textual, foco, alineación, relleno ni desbordamiento** (288 renderizaciones, código de salida 0); contraste: 158 pares, todos aprobados. No quedan inquietudes sobre alternativas ni sobre la cadena de herramientas. La integración real del catálogo, el retorno a cualquier página de origen, la autenticación, los permisos del servidor y la conformidad con tecnologías de asistencia no quedan demostrados con esta maqueta estática y siguen asignados como verificaciones de implementación e integración. No quedan preguntas de diseño importantes sin resolver.
