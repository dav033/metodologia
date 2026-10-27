---
name: Planos de consulta
status: draft
subplan: SP-14
contract: planes@v1
exploration: r3.dir-b
chosen_thumbnail: planes@v1.r3.dir-b.html.candidate-1.html
---

# Planos de consulta — Exploración espacial B

Esta es una exploración de planificación independiente, no un contrato aprobado. No reemplaza la Dirección C elegida por el responsable ni edita el par canónico planes@v1. Fuentes: planes@v1.r3.behavior.md, SPEC “Behavior — SP-14 extra view (round 13 answered)”, el PLAN.json actual de SP-14, el archivo de feedback del responsable, planes@v1 actual y los hermanos cuentas-admin@v1 / taller-esenciales@v1 / proyectos@v1. Rige esta entrega el alcance de escritura más reciente, solo de exploración.

## Enfoque y miniatura elegida

La pregunta de producto no cambia: ¿qué herramientas y qué precio mensual corresponden a cada plan? Se conservan el masthead de anillo y punto de Pictures/Sempertex, los controles compartidos de idioma/cuenta, los formularios de acceso/cuenta y el pie de página. Solo se recompone el área de trabajo de planes en un índice local junto a una única hoja de comparación reglada, dividida en cuatro cuadrantes pares. El índice se convierte en un selector de comparación temporal en la vista adicional; las cuatro listas completas de herramientas permanecen visibles.

Se dibujaron dos HTML en miniatura antes del TSX completo y se inspeccionaron en Chromium a 1280px:

- **Candidato 1 — elegido:** índice lateral de planes y hoja de comparación 2×2. Los cuatro encabezados de plan y las primeras filas de herramientas aparecen antes; el selector de comparación tiene un lugar espacial explícito junto al contenido.
- Candidato 2: índice superior y bandas horizontales largas de planes. Conserva el ritmo de consulta anterior, pero requiere más recorrido vertical antes de llegar a Master Designer y distingue con menos claridad la vista adicional.

La composición seleccionada encaja con el patrón de hoja de trabajo del producto existente y con el encabezado compacto de SP-2. Reutiliza la paleta de producción, los recursos locales de Geist, los controles semánticos tipo píldora, la marca de anillo de origen, la navegación neutral y el vocabulario de hoja redondeada; no introduce marca, paleta ni tipografía nuevas. Las paletas específicas de talleres no se importan a esta superficie pública/de cuenta. La disposición de cuadrantes de plan y la navegación local son las variables de la exploración.

## Ocho ejes

| Eje | Expresión renderizada |
|---|---|
| Concepto | Un espacio de trabajo de consulta espacial: un índice local de planes junto a una hoja de comparación continua de cuatro paneles; el selector opcional resalta solo una comparación informativa. |
| Layout | A >=1100px, un riel izquierdo de 216px queda junto a una hoja reglada de 2 por 2. De 640 a 1099px el riel se convierte en un dock superior y la hoja sigue en dos columnas. Por debajo de 640px los paneles de plan se apilan. |
| Navegación | Se conservan los enlaces de entrada de acceso/cuenta y el masthead; una regla neutral de comparación/selección dentro de la página; el índice de anclas en la comparación se convierte en botones de elección con estado presionado en la selección, con un retorno persistente a la comparación completa. |
| Tipografía | Solo Geist Sans y Geist Mono embebidas existentes. Página 24px, encabezado de plan 20px, precio mensual tabular 22px (20px en teléfono), herramientas 14px, disponibilidad 12px. Sin tipografía de display. |
| Densidad | Una hoja exterior de 32px con reglas compartidas, márgenes internos de panel par de 24px (20px en teléfono) y listas acumulativas de herramientas compactas y totalmente visibles. Un índice de catálogo estrecho mantiene diferenciada el área de trabajo principal de la navegación. |
| Componentes | Button, Input y Skeleton reales de shadcn/Base UI instalados; masthead de anillo y punto y desplegable de cuenta compatibles con el origen. Botones y anclas nativos forman el dock de planes; sin desplegable de herramientas del plan. |
| Color | Paleta semántica sin cambios de globals.css de Pictures en ambos temas; el acento de origen marca solo la selección/foco/enlaces de comparación, papel y navegación neutrales, y el token de advertencia existente etiqueta las herramientas no disponibles. |
| Movimiento | Entrada espacial opuesta: el riel se traslada desde -16px mientras los cuadrantes de plan llegan desde +22px con escalonado de 45ms; cubic-bezier(.16,1,.3,1) expresivo de 440ms. La selección tiene un marcador de resorte compartido y un breve asentamiento del subrayado. El movimiento reducido y still=1 se asientan de inmediato. |

La evidencia de los selectores está en planes@v1.r3.dir-b.json. Los selectores de layout identifican el riel y la hoja, los de navegación identifican controles reales, los de tipografía identifican la jerarquía visible y los de movimiento identifican elementos con animaciones CSS o el marcador de elemento compartido de Motion. Ningún eje usa body como evidencia genérica.

## Vistas, estados y comportamiento

| Vista nativa | Propósito / contexto retenido |
|---|---|
| compare | Comparación pública de /planes, sin menú de cuenta; regreso al inicio de sesión. |
| compare-signed | La misma información pública con la divulgación de cuenta retenida; regreso al contexto de cuenta de origen en este fixture acotado. |
| select | Vista pública adicional de selección. Cuatro botones de opción única con estado presionado resaltan un plan solo para comparación. |
| select-signed | La misma selección informativa con la divulgación de la cuenta actual retenida; el plan ya asignado a la cuenta nunca cambia. |
| login | Formulario existente de inicio de sesión solo por invitación de SP-2, con exactamente una entrada a /planes después de la guía de restablecimiento. |
| menu | Superficie existente Mi cuenta de SP-2 con su divulgación de cuenta inicialmente abierta para mostrar la única entrada a /planes entre Mi cuenta y cerrar sesión. |

La barra de planificación externa conserva la etiqueta **Mockup** y los selectores nativos `view`, `state`, `theme` y `motion`, con etiquetas en español. No se declara ningún diálogo, por lo que un selector de escena no aplica. El control de idioma del producto demuestra de forma independiente el español y el inglés; el idioma del navegador define la configuración regional inicial. Estados nativos: `normal`, `selected`, `loading`, `empty`, `error`, `offline`. `selected` precarga Designer Plus solo como fixture inspeccionable cuando no existe una preferencia de comparación. Los estados del catálogo se aplican a las vistas de planes; los contextos de entrada siguen siendo demostraciones de SP-2 y no especificaciones de autenticación paralelas.

Toda vista de catálogo válida enumera todas las herramientas, sin un control Ocultar/Mostrar herramientas. Entusiasta/Enthusiast tiene Chat con límites / Chat with limits, Contador de globos / Balloon counter y Catálogo / Catalogue. Designer usa la frase de chat con límites más altos, sin límites numéricos. Designer Plus agrega la calculadora de costos y las tres herramientas no disponibles. Master Designer agrega la única línea Taller 3D / 3D workshop, incluido su explorador, sin una fila de explorador duplicada. En cada plan superior aparecen tres etiquetas de no disponible: Chat ampliado / Extended chat, detección de estructuras y detección avanzada de globos. Se leen “aún no disponible” / “not available yet”. La calculadora de costos está disponible.

Los nombres, el orden, los precios y las etiquetas se representan con un único fixture ilustrativo derivado de los requisitos. Los precios en COP son 20,000 / 45,000 / 70,000 por mes, con formato en español 20.000 / 45.000 / 70.000; los precios en USD son 7 / 14 / 25 por mes. Entusiasta es Gratis / Free. Solo aparece la moneda del idioma activo. Producción debe consumir plan-catalogue@1 de SP-1; src/lib/planes/catalogo.ts aún no está presente en ninguno de los worktrees de entrada de solo lectura, por lo que este artefacto no certifica la integración del catálogo.

Los enlaces del índice de comparación se mueven al plan indicado y enfocan su artículo. Los botones de selección exponen aria-pressed, mantienen el foco en la opción activada, anuncian el plan seleccionado y marcan el mismo plan en la hoja. “Volver a la comparación completa” conserva ese resaltado en memoria. Abrir cualquiera de las entradas a /planes preserva su contexto con sesión iniciada o cerrada. La selección no cambia ningún rol, campo de cuenta, permiso, almacenamiento, cookie ni dato remoto. En la sección no existe ninguna acción de compra, solicitud, contacto, registro ni asignación. La única explicación de asignación es “Un administrador asigna el plan.”

La carga presenta cuatro grupos de skeletons y un anuncio de carga en lugar de un catálogo vacío exitoso. Los estados vacío/error/sin conexión reemplazan la hoja con la explicación heredada y Reintentar. Reintentar restaura el fixture local completo. No se adivina ningún precio faltante. Los botones de elección se deshabilitan cuando los datos del catálogo no están disponibles. Los valores de catálogo faltantes no producen una comparación parcial de planes. Los formularios de contexto de entrada solo muestran una explicación de Mockup y nunca envían credenciales.

## Comportamiento responsivo y de accesibilidad

| Ancho | Composición |
|---|---|
| 320–639px | Encabezado compacto compartido con ajuste de línea; márgenes exteriores de 20px; índice/selector local 2×2; una hoja de planes apilada continua con márgenes internos de 20px; botón de regreso a la comparación de ancho completo. |
| 640–839px | Márgenes de 24px; dock local en 2×2; hoja de planes en dos columnas iguales con márgenes internos de 24px. El resumen de selección y el regreso se ajustan en el flujo normal. |
| 840–1099px | El dock pasa a cuatro columnas; la hoja sigue en dos columnas; el encabezado se ajusta donde sea necesario. Ningún riel lateral compite con el texto de los planes en anchos de tableta. |
| ≥1100px | Márgenes de 40px; riel local fijo (sticky) de 216px, separación de 28px y hoja 2×2 flexible. El desplazamiento del riel considera la barra Mockup. |

El orden de los planes es Entusiasta, Designer, Designer Plus, Master Designer en el DOM y en el orden de lectura. El texto y los controles se ajustan sin desplazamiento horizontal de la página. La divulgación de cuenta, la navegación y el regreso permanecen en el flujo normal del documento en pantallas estrechas. El estilo seleccionado agrega un estado textual, un control con estado presionado, una marca de verificación y una breve línea de acento; el color no es la única señal. Se usan enlaces/botones estándar, landmarks de header/nav y un único H1 por página. Los contornos de foco usan el acento de origen, sin acciones ocultas que dependan solo del hover. Los nuevos objetivos táctiles miden al menos 44px de alto. Escape cierra la divulgación de cuenta y devuelve el foco a su resumen. El mockup controla explícitamente el alternador del resumen para evitar una condición de carrera entre el evento toggle diferido de details del navegador y un Escape rápido.

WCAG 2.2 AA es una meta, no una declaración de conformidad. El contraste, el foco, el relleno y el reflujo se miden a continuación. La autenticación de producción, la integración del catálogo y las pruebas completas con tecnologías de asistencia siguen siendo trabajo de implementación/revisión.

## Procedencia de componentes y tokens

Inspección de código fuente de solo lectura: t12 globals.css, layout.tsx, login/page.tsx, login/LoginForm.tsx, CabeceraApp.tsx y MenuApp.tsx; las mismas fuentes de producto en asesor; contratos y HTML hermanos seleccionados. Los cambios en el repositorio de entrada se dejaron intactos.

- `shadcn:button` real instalado outline/default: @/components/ui/button; `shadcn:input`: @/components/ui/input; `shadcn:skeleton`: @/components/ui/skeleton. ButtonPrimitive es Base UI. El builder real empaqueta React, Motion y los recursos de fuentes locales sin conexión.
- Composición personalizada específica de la aplicación: cabecera/marca de anillo y divulgación de detalles de cuenta heredadas del contexto SP-2 del borrador anterior de planes; regla de ruta neutral; índice nativo de planes/dock de elección; hoja de comparación compartida con artículos semánticos y listas. Esto no es un nuevo componente del kit ni una implementación de producción.
- `--background`←`--fondo` (#faf9fc / #0b0c10); `--card`, `--popover`←`--superficie` (#ffffff / #16181f); primeros planos←`--texto` (#1c1425 / #f4f5f7); texto atenuado←`--texto-suave` (#6b6178 / #9aa1ad); secundario←`--superficie-2` (#efe9f8 / #242733).
- Primario/ring←`--acento` (#6d3fe0 / #9479ff); primer plano del primario←`--sobre-acento` (#ffffff / #120b24). El `--aviso` de origen etiqueta las herramientas no disponibles; el `--error` de origen etiqueta el fallo de carga. Los bordes de los inputs usan el alias `--texto-tenue` existente del hermano (#766c85 / #8a91a0), mientras que los bordes decorativos conservan `--borde`/`--borde-suave`.
- Se incrustaron los recursos WOFF2 locales existentes de Geist Sans/Geist Mono, sin solicitudes de fuentes. Roles de radio del hermano: panel 32px, inset 24px, campo 18px y pastilla 999px. No falta ninguna fuente de tokens y no se propone ningún color nuevo.

## Detalle de interacción y movimiento

El área modificada usa llegadas espaciales opuestas: el riel local se asienta desde -16px y los cuadrantes de planes desde +22px con escalonado de 45ms; la opacidad se mantiene en al menos .85. Duración expresiva de 440ms con cubic-bezier(.16,1,.3,1), natural de 280ms, sutil de 160ms. Al seleccionar un plan, un marcador de verificación compartido se mueve con el spring de Motion instalado y una breve línea de acento se asienta en el panel correspondiente. Los controles repetidos de origen conservan una respuesta rápida de 180/140/100ms. No existe animación decorativa continua ni temporizador fuera de pantalla; las animaciones CSS se pausan cuando el documento está oculto. Las preferencias de movimiento reducido, el selector Quieto y ?still=1 asientan todo el contenido de inmediato sin eliminar información ni respuesta visual.

## Verificaciones de revisión observables

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-01 | ≥1100px | normal | Un índice local de 216px se sitúa a la izquierda de la hoja de comparación de dos columnas. |
| B-02 | 640–839px | normal / selected | Las opciones del índice forman dos columnas sobre una hoja de planes de dos columnas, con todas las listas de herramientas visibles. |
| B-03 | 840–1099px | normal | Cuatro opciones del índice comparten una fila sobre la hoja de dos columnas sin desplazamiento horizontal de la página. |
| B-04 | 320–639px | normal / selected | Los paneles se apilan en el orden del catálogo y cada herramienta se ajusta dentro del viewport. |
| B-05 | 320–1280px | normal / selected | Cuatro listas completas contienen 3, 3, 7 y 8 herramientas; no existe control para ocultar herramientas. |
| B-06 | 320–1280px | ES / EN | Se muestra exactamente una moneda en los precios; Entusiasta es Gratis / Enthusiast es Free. |
| B-07 | 320–1280px | selected | Exactamente una opción tiene aria-pressed=true y su plan se marca para comparación. |
| B-08 | 320–1280px | selection → comparison | Al regresar se conserva el resaltado y la identidad de la cuenta y el almacenamiento permanecen sin cambios. |
| B-09 | 320–1280px | normal | Ambos planes superiores marcan exactamente las tres herramientas no disponibles en texto visible. |
| B-10 | 390–1280px | loading / empty / error / offline | No se muestra ninguna comparación exitosa incompleta; los estados de fallo exponen Reintentar. |
| B-11 | 390–1280px | login / menu | Un enlace a /planes en cada entrada asignada abre el contexto público/con sesión iniciada correspondiente. |
| B-12 | all | reduced / still | El contenido y la respuesta de selección siguen disponibles sin ninguna animación finita en ejecución. |

## Evidencia de auditoría

- Builder real sin conexión: APROBADO. El workspace instalado reportó 96/96 entradas de componentes disponibles. El HTML final empaqueta 2,031 archivos fuente en aproximadamente 553 KB, incluidas las fuentes de origen; no se usó instalación de paquetes ni descarga de recursos.
- Contraste estático: **158 pares verificados en claro y oscuro, todos aprueban**.
- Comando renderizado final: `UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py planes@v1.r3.dir-b.html --widths 1280,390,768,1024 --max-combos 100`.
- **288 renders / 288 combinaciones planificadas**, 9,120 mediciones de texto y 560 paradas de foco por teclado. Las seis vistas, los seis estados y ambos temas se midieron en los cuatro anchos; no fue necesario muestrear.

RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

- Verificación final complementaria con Playwright: **141 escenarios aprobados**, incluidos **128 casos responsivos** en 320/390/640/768/840/1024/1100/1280px, ES/EN, ambos temas y las cuatro vistas de comparación/selección. Las aserciones cubrieron cuatro listas completas con 3/3/7/8 herramientas, seis etiquetas de no disponible, moneda/nombre gratuito específicos del idioma, cada una de las cuatro opciones locales, retención del resaltado, ambos enlaces de entrada a /planes, regreso contextual, cierre con Escape, recuperación del estado del catálogo, ausencia de solicitudes externas, ausencia de excepciones del navegador y almacenamiento local/de sesión sin cambios.
- Las miniaturas 1 y 2 se inspeccionaron visualmente a 1280px antes de elegir. Las capturas completas del mockup se inspeccionaron en memoria a 1280/390 en ambos temas, además de la selección en tableta a 768px y la comparación a 1024px. No se escribieron archivos de captura ni otros artefactos fuera de la lista de salida asignada.
- La primera auditoría renderizada encontró un inset del botón seleccionado en teléfono de 11px; se corrigió a al menos 13px. La comprobación inicial de interacción con Escape inmediato expuso una condición de carrera del toggle nativo diferido; el alternador del mockup se reparó sin cambiar el diseño de la entrada. La auditoría final de 288 renders y la verificación de 141 escenarios anteriores cubren el artefacto reconstruido tras ambas correcciones.
- Verificación de evidencia de selectores/movimiento: cada selector de evidencia JSON coincidió con elementos renderizados; se observaron en ejecución railArrive y cuatro animaciones paperArrive, y Quieto no dejó ninguna animación finita en ejecución.
- Estas son verificaciones de artefactos de planificación, no lint/typecheck/build de producción, permisos de backend, autenticación en vivo ni integración real del catálogo. No se declara ninguna verificación del producto.

## Impacto, preocupaciones y preguntas abiertas

Solo SP-14 consume planes@v1 (T14.1 texto, T14.2 área de planes/selección adicional, T14.3 enlaces de entrada, T14.5 revisión visual; T14.4 integra el comportamiento del navegador y T14.6 audita). Esta exploración es una **alternativa visual con cambios incompatibles** en diseño/navegación local/disposición responsiva si se elige; es compatible en comportamiento con el brief r3 compartido. No cambia ningún contrato aprobado ni referencia de consumidor. Los contratos de datos de SP-1 y el contrato de acceso/cuenta seleccionado de SP-2 permanecen intactos; no se propone ninguna entrada adicional de navegación global.

Preguntas abiertas para el responsable: **ninguna**. El comportamiento de solo comparación de la ronda 13 está resuelto. Los límites numéricos de chat siguen explícitamente diferidos y ausentes, en lugar de convertirse en una pregunta repetida. La selección de esta dirección y la aprobación del plan/diseño siguen siendo decisiones del responsable. El diseño C canónico elegido por el responsable sigue siendo la referencia hasta una finalización separada. Este trabajo, que es solo de diseño, no certifica ninguna compilación de producción, lint, autorización, persistencia de red ni verificación del catálogo en vivo.
