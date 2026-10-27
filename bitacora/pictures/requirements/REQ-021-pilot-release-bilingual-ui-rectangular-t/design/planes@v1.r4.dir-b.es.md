---
name: Planos de consulta
status: draft
subplan: SP-14
contract: planes@v1
exploration: r4.dir-b
chosen_thumbnail: planes@v1.r3.dir-b.html.candidate-1.html
---

# Planos de consulta — Exploración espacial B

Esta es la revisión 4 de la misma Dirección B, no una nueva exploración ni un contrato aprobado. No reemplaza la Dirección C seleccionada por el propietario ni edita el par canónico planes@v1. Fuentes: planes@v1.r4.behavior.md, SPEC “Behavior — SP-14 extra view (round 13 answered)”, PLAN.json actual de SP-14, archivo de comentarios del propietario, planes@v1 actual y sus pares cuentas-admin@v1 / taller-esenciales@v1 / proyectos@v1. La lista de escritura de la iteración r4 acotada rige esta entrega. Solo los comentarios del 2026-10-27T16:16 sobre la Dirección B modifican la composición anterior.

## Enfoque preservado y miniatura histórica seleccionada

La pregunta del producto no cambia: ¿qué herramientas y precio mensual corresponden a cada plan? Se conservan el encabezado gráfico de anillo y puntos de Pictures/Sempertex, los controles compartidos de idioma y cuenta, los formularios de acceso y cuenta, y el pie de página. Solo se recompone el área de planes, como un índice local junto a una única hoja comparativa con líneas divisorias, organizada en cuatro cuadrantes equivalentes. En la vista adicional, el índice se convierte en un selector temporal de comparación; las cuatro listas completas de herramientas permanecen visibles.

En la revisión 3, se dibujaron dos archivos HTML de miniaturas antes del TSX completo y se inspeccionaron en Chromium a 1280px:

- **Candidato 1 — seleccionado:** índice lateral de planes y hoja comparativa de 2×2. Los encabezados de los cuatro planes y las primeras filas de herramientas aparecen antes; el selector de comparación tiene una ubicación espacial explícita junto al contenido.
- Candidato 2: índice superior y bandas de planes horizontales largas. Conserva el ritmo de consulta anterior, pero requiere más desplazamiento vertical antes de llegar a Master Designer y distingue la vista adicional con menos claridad.

La composición seleccionada se ajusta al patrón de documentos de trabajo del producto existente y al encabezado compacto de SP-2. Reutiliza la paleta de producción, los recursos locales de Geist, los controles semánticos tipo píldora, la marca de anillo de origen, la navegación neutral y el lenguaje visual de papel redondeado; no incorpora ninguna marca, paleta ni fuente nueva. No se importan las paletas específicas de talleres a esta superficie de cuenta/pública. La disposición de los cuadrantes de planes y la navegación local son las variables de exploración.

## Ocho ejes

| Eje | Expresión renderizada |
|---|---|
| Concepto | Un espacio de trabajo para consultas espaciales: un índice local de planes junto a una hoja comparativa continua de cuatro paneles; el selector opcional solo resalta una comparación informativa. |
| Diseño | En >=1100px, una barra lateral de 216px se ubica junto a una hoja con divisiones de 2 por 2. Entre 640 y 1099px, la barra se convierte en un panel superior y la hoja mantiene dos columnas. Por debajo de 640px, los paneles de planes se apilan. |
| Navegación | Se conservan los enlaces de acceso y cuenta y el encabezado gráfico; una regla neutral de comparación/selección dentro de la página; el índice de anclas de la comparación cambia a botones de elección con estado presionado en la vista de selección, con un retorno persistente a la comparación completa. |
| Tipografía | Solo se usan Geist Sans y Geist Mono integradas existentes. Página: 24px; encabezado de plan: 20px; precio mensual tabular: 22px (20px en teléfono); herramientas: 14px; disponibilidad: 12px. Sin tipografía de exhibición. |
| Densidad | Una hoja exterior de 32px con líneas divisorias compartidas, márgenes interiores de 24px en paneles equivalentes (20px en teléfono) y listas compactas, acumulativas y completamente visibles de herramientas. Un índice de catálogo estrecho mantiene diferenciada el área de trabajo principal de la navegación. |
| Componentes | Button, Input y Skeleton reales de shadcn/Base UI instalados; encabezado gráfico de anillo y puntos compatible con el original y detalle desplegable de cuenta. Botones/anclas nativos forman el panel de planes; no hay control desplegable para las herramientas de los planes. |
| Color | Paleta semántica de Pictures globals.css sin cambios en ambos temas; el color de acento del original solo marca la selección/comparación, el foco y los enlaces; papel y navegación neutrales; las herramientas no disponibles usan las etiquetas del token de advertencia existente. |
| Movimiento | Entrada espacial en direcciones opuestas: la barra se desplaza desde -16px mientras los cuadrantes de planes entran desde +22px, con intervalos de 45ms; movimiento expresivo de 440ms con cubic-bezier(.16,1,.3,1). La selección tiene un marcador compartido con resorte y un breve ajuste de subrayado. La comparación inicial también muestra un marcador de referencia animado y la etiqueta de plan resaltado sobre Entusiasta, sin realizar una elección. El movimiento reducido y still=1 se establecen de inmediato. |

La evidencia de selectores está en planes@v1.r4.dir-b.json. Los selectores de diseño identifican la barra y la hoja; los de navegación, controles reales; los de tipografía, la jerarquía visible; y los de movimiento, los elementos con animaciones CSS o el marcador compartido de Motion. Ningún eje usa body como evidencia genérica.

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

## Revisión 4: evidencia de la comparación inicial

Los comentarios del propietario del 2026-10-27T16:16 solo señalan la falta de evidencia visible de movimiento. Las vistas iniciales `compare` y `compare-signed` normales ahora muestran el `.rail-mark` existente sobre Entusiasta y `.selected-label` con el texto **Plan resaltado / Plan resaltado** en su cuadrante de la hoja. Esto es una referencia visual, no una elección del visitante ni un plan asignado a la cuenta. La preferencia de comparación permanece vacía hasta que se realiza una elección en la vista adicional. Esa vista sigue iniciando con **Ningún plan seleccionado / Ningún plan seleccionado**, sin ninguna opción presionada ni marcador si no existe una elección previa de comparación. Una vez que se elige un plan, se mantienen sin cambios el comportamiento existente de la etiqueta seleccionada, el marcador con resorte, el cuadrante resaltado y el retorno a la comparación completa. El resaltado inicial de Entusiasta es igual para visitantes con y sin sesión iniciada y nunca se deriva de la asignación de cuenta ni la modifica.

El marcador de referencia reutiliza la animación `selectionLine` existente, los tokens de duración/perfil y la función de aceleración, de modo que todos los selectores de movimiento declarados se muestran y animan en la comparación predeterminada. No se introduce ningún control, selector desplegable de herramientas de planes, paleta, fuente, destino, permiso ni modificación de cuenta nuevos. El marcador y la etiqueta iniciales se establecen con movimiento reducido/Quieto/still; todas las herramientas permanecen visibles.

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| B-13 | 320–1280px | comparación inicial / normal | Entusiasta tiene un marcador de barra visible y una etiqueta Plan resaltado / Plan resaltado sin intervención del visitante. |
| B-14 | 320–1280px | selección inicial / normal | No hay ninguna elección de plan presionada; Ningún plan seleccionado / Ningún plan seleccionado permanece visible hasta que se elige un plan. |
| B-15 | 1280px | comparación expresiva inicial | `.comparison-rail`, `.plan-sheet`, `.rail-mark` y `.selected-label` muestran evidencia visible de animación. |

## Evidencia de auditoría

Verificación reciente del artefacto reconstruido de revisión 4, al 2026-10-27; no se heredan los totales históricos de la revisión 3:

- Generador sin conexión actual: **APROBADO**, 553 KB / 2,031 archivos de origen incluidos. Comando: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/planes@v1.r4.dir-b.tsx --out <design>/planes@v1.r4.dir-b.html`. Sin alternativa, instalación ni descarga de recursos.
- `python3 <kit>/kit/contrast.py <design>/planes@v1.r4.dir-b.html`: **contraste: 158 pares verificados en los temas claro y oscuro; todos aprobados** (código de salida 0).
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.r4.dir-b.html --widths 1280,390,768,1024`: **288 renderizados (288 combinaciones planificadas), 9136 mediciones de texto, 560 paradas de foco** (código de salida 0). Las seis vistas y los seis estados, ambos temas y cuatro anchos; sin advertencias de muestreo.

RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, espaciado interno ni desbordamiento

- Ejecución real de `compare_directions.measure()` con A/C sin cambios de r3 y B reconstruida de r4: **ok=true, evidence_ok=true, missing_evidence=[]**. Similitud de diseño de B/A: **0.221**; de B/C: **0.199**; ambos pares se aprueban con navegación, movimiento y densidad diferenciados. Todos los selectores de evidencia de B se aprueban. La evidencia adicional del resumen de selección sigue siendo accesible en la vista de selección, como antes.
- Una prueba independiente de la carga inicial confirmó que los cuatro selectores de movimiento están presentes y en ejecución en la **comparación inicial**, sin seleccionar ninguna vista, estado ni plan: `railArrive` en `.comparison-rail`, cuatro efectos `paperArrive` en `.plan-sheet`, `selectionLine` en `.rail-mark` y `.selected-label`.
- Pruebas complementarias con Playwright: **141 escenarios APROBADOS**, incluidas **128 combinaciones adaptables** en 320/390/640/768/840/1024/1100/1280px, ES/EN, ambos temas y las cuatro vistas de comparación/selección. Se verificaron las listas completas de herramientas 3/3/7/8, seis etiquetas de no disponibilidad, moneda, referencia visible predeterminada, vista de elección inicial vacía, cuatro rutas de elección y retorno, identidad/almacenamiento de cuenta sin cambios, recuperación del estado de error, Quieto, `?still=1`, movimiento reducido del sistema operativo, cero errores de página y cero solicitudes HTTP externas.
- Verificación específica de entrada/teclado: **APROBADA** para el único enlace /planes en cada entrada, ambos retornos contextuales, Escape y restauración del foco en la cuenta, foco del índice al plan nombrado y selección con la barra espaciadora.
- Se inspeccionaron en memoria capturas estabilizadas de **1280/390px en ambos temas** y **768px en tema claro**. Se conservan la composición existente de riel/hoja, el marcador y la etiqueta visibles, el panel fijo para tabletas, el contenedor compartido y los controles con ajuste de línea. Los búferes de capturas permanecieron en memoria; no se guardaron archivos de captura. Un primer intento de devolver cuatro capturas juntas superó los límites de salida de la herramienta; luego se inspeccionaron correctamente capturas individuales. Esto fue un problema de transferencia de evidencia, no un fallo de la maqueta o del renderizado.

`<kit>` = `/home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit`; `<design>` = el directorio de diseño asignado a este requisito. Estas verificaciones validan el artefacto de planificación, no el catálogo, la autenticación ni los permisos de producción, ni la conformidad plena con WCAG.

SHA-256 del artefacto: `planes@v1.r4.dir-b.tsx` = `6aa8d9aee13fd2ef7468f7d0930c4b5ca4cc9fa86a69b331f4246de47cf15ba7`; `planes@v1.r4.dir-b.html` = `174233f344c1f5c55c54a5abfae1ec89d3785a76641a65cdb2bfbfcd6eb8cb41`.

## Impacto, inquietudes y preguntas abiertas

Solo SP-14 consume planes@v1 (texto de T14.1, área de planes/vista de selección adicional de T14.2, enlaces de entrada de T14.3, revisión visual de T14.5; T14.4 integra el comportamiento del navegador y T14.6 realiza auditorías). Esta exploración es una **alternativa visual incompatible** en cuanto al diseño, la navegación local y la disposición adaptable si se elige; el cambio de r4 es una **corrección visual compatible** de B que conserva el comportamiento compartido de r4. Acción requerida: revisión del borrador por el propietario y una nueva revisión visual si se elige. No cambia ningún contrato aprobado ni referencia de consumidor. Los contratos de datos de SP-1 y el contrato de acceso/cuenta seleccionado de SP-2 permanecen intactos; no se propone ninguna entrada adicional en la navegación global.

Preguntas abiertas para el propietario: **ninguna**. No se implica aprobación; esto sigue siendo un borrador. El comportamiento exclusivo de comparación de la ronda 13 está resuelto. Los límites numéricos de chat siguen expresamente aplazados y no se incluyen, en lugar de convertirse en una pregunta repetida. La selección de esta dirección y la aprobación del plan/diseño siguen siendo decisiones del propietario. El diseño C canónico seleccionado por el propietario sigue siendo la autoridad hasta que se realice una finalización por separado. Este trabajo de diseño únicamente no certifica una compilación de producción, lint, autorización, persistencia de red ni una verificación del catálogo activo.
