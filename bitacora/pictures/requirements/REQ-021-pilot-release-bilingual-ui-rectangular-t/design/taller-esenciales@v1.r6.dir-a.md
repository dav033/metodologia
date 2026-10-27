---
name: Corte de montaje
status: draft
kind: independent-direction-exploration
contract_target: taller-esenciales@v1
subplan: SP-3
requirements: [R9, R10, R11]
revision: r6.dir-a
owner: David
date: 2026-10-26
---

# Corte de montaje

Exploración operativa/editorial de SP-3. No es el contrato canónico ni concede aprobación. SPEC, PLAN y la fuente `taller-esenciales@v1.r6.behavior.md` siguen siendo la autoridad funcional; esta dirección termina cuando el propietario la compara y decide. No se ha modificado ningún archivo compartido, repositorio de producto o plan.

## Concepto

La mesa, sus medidas y las piezas necesarias para prepararla se leen en una sola hoja de montaje. Arriba, una escena esquemática muestra la selección; debajo, una junta de herramientas conduce a la hoja de trabajo. El formulario usa una columna deliberadamente asimétrica: título contextual a la izquierda, edición en el centro y sillas realmente colocadas a la derecha. El conteo tiene denominador explícito: 8 colocadas / 20 pedidas es información de trabajo, no un indicador decorativo.

**Gesto memorable:** una regla lavanda se registra desde la izquierda, las sillas encajan en diagonal con intervalos precisos y las medidas quedan quietas sobre su línea de trabajo. El esquema es SVG local ilustrativo, no un motor 3D ni una prueba de geometría.

**Por qué no es la composición por defecto:** no reparte herramientas en tres paneles estrechos, no usa una cuadrícula de indicadores ni un formulario centrado. Dedica una banda completa a entender la escena y otra a prepararla. Las bibliotecas son fichas con siluetas y reglas, sin cajas anidadas. La asimetría da prioridad a medidas y capacidad sin convertir el título en una portada.

## Dos miniaturas y elección

Se escribieron ambas miniaturas **antes** del TSX completo:

- [Candidato 1: escena / junta / hoja de trabajo](taller-esenciales@v1.r6.dir-a.html.candidate-1.html). **Elegido.** La escena tiene ancho suficiente; medidas y cantidad real comparten una franja. La navegación está en la junta entre representación y preparación.
- [Candidato 2: índice de piezas lateral](taller-esenciales@v1.r6.dir-a.html.candidate-2.html). Conservado como evidencia. Es más familiar, pero su índice vertical repite la lógica de registro lateral ya explorada en Cuentas y estrecha el espacio de edición.

Las miniaturas son composiciones estáticas de baja fidelidad. La propuesta completa usa los componentes reales instalados y ofrece los selectores de revisión, estados y ambos temas.

## Ocho ejes

| Eje | Decisión observable |
|---|---|
| concept | La escena se lee como una hoja de montaje: medidas de una mesa, sillas que realmente caben y piezas que hay que preparar, ligadas por una línea de registro. Mantiene el mundo material de Pictures sin tomar la composición del registro de Cuentas. |
| layout | Dos bandas horizontales: escenario de 250 px de índice de objetos más esquema amplio, y franja de trabajo asimétrica 218 px / fluida / 264 px. La biblioteca ocupa dos columnas mayores, mientras que el inspector mantiene medidas y cantidades en el mismo renglón. Debajo de 1024 px se simplifica a una zona activa; debajo de 768 px se apila. |
| navigation | Barra de seis herramientas integrada en la junta entre escena y hoja de trabajo. Etiquetas completas con numeración de secuencia de trabajo en escritorio; rejilla 3 por 2 bajo 1024 px. Selección neutra con línea inferior. Exportar y lista de compra se conservan en la cabecera; no hay sidebar ni dock fijo. |
| typography | Arial/sistema, título de objeto 30 px en dos líneas con tracking -1.1 px, sección 20 px, datos editables 24 px y conteo real 64 px con denominador de 18 px. Metadatos de 12–13 px y cifras tabulares; monospace solo para índices de navegación y extensión GLB. |
| density | Información de trabajo compacta y agrupada por reglas: medidas simultáneas, sillas y materiales en secciones de 16–24 px de separación; márgenes de 32/24/20 px y controles de al menos 40–44 px. Catálogo de cuatro columnas a partir de 1280 px, tres en tablet y una bajo 480 px. No hay tarjetas de indicadores. |
| components | Button/Input/Field/Textarea/Alert/Skeleton reales shadcn/Base UI; Popover y Dialog reales con primitivas Animate UI. Composiciones propias: esquema isométrico SVG, regla de registro, fichas de catálogo sin caja y resumen numerador/denominador. Sin checkbox nativo ni componente sustituto no declarado. |
| colour | Tokens --taller-* del producto: fondo #faf9fc/#16131d, tarjeta #ffffff/#1d1926, texto #1c1425/#f2eff7. Primario claro #6d3fe0 y pareja existente de acento oscuro #b9a4ff/#120b24. Bordes de controles toman --taller-medio (#5a5168/#a59db5); borde decorativo conserva el original. Lavanda representa tela de la escena; éxito/error tienen color semántico. |
| motion | Registro preciso con cubic-bezier(.8,0,.2,1): título se alinea 7 px, hoja entra 8 px conservando opacidad mínima .75, línea se extiende desde la izquierda, sillas se registran diagonalmente con stagger 28 ms y fichas con 24 ms. Escena usa Motion con 5 px y duración del perfil. Duraciones natural 220/320 ms, expresiva 340/520 ms, sutil 140/200 ms; pulsación 2 px/160 ms. Movimiento reducido y still=1 muestran contenido final y mantienen overlays en su posición; animaciones finitas se pausan con pestaña oculta. |

## Identidad compartida y look ledger

Se leyeron las notas JSON de `cuentas-admin@v1.r7.dir-a`, `dir-b` y `dir-c`. Se preservan Pictures, lenguaje de montaje, marca geométrica, acciones moradas y superficies neutras. El Taller usa sus tokens locales, no los del fondo general de Cuentas. Evitamos su margen editorial con registro de personas, el pase centrado de dos hojas y el dock inferior. Esta dirección usa una junta horizontal dentro de una escena de trabajo, tipos orientados a medidas y un registro cinético diagonal, sin pliegue ni rebote.

## Fuentes y piezas reales

Lectura read-only: SPEC.md, PLAN.md, PLAN.json SP-3/T3.1–T3.8, comportamiento compartido, borrador previo; `globals.css`, clases `ui-taller.ts`, catálogo y tipos de mesa en t12 y pictures/asesor; exportador UI existente en pictures. El proyecto prevalece sobre el kit.

- `shadcn:button` — `@/components/ui/button`, default/outline/ghost, normal/disabled/focus; Base UI real.
- `shadcn:input`, `shadcn:textarea`, `shadcn:field` — imports de `@/components/ui/input`, `textarea`, `field`; rangos y errores por campo. Campos y ayudas comparten el mismo eje.
- `shadcn:alert`, `shadcn:skeleton` — `@/components/ui/alert`, `skeleton`; feedback semántico y carga sin spinner central.
- `shadcn:popover`, `shadcn:dialog` — `@/components/ui/popover`, `dialog`, instalados con primitivas Animate UI. Exportación no modal; lista modal con Escape y foco. Se amplía el inset a 24–28 px sin cambiar sus primitivas.
- Motion real — `motion/react` y `useMotionProfile` de `@kit/motion`; perfiles también gobiernan la secuencia CSS. `mountMockup/useMockup` conservan Vista, Estado, Diálogo, Tema y Movimiento nativos.
- Composiciones propias declaradas: SVG isométrico, miniaturas de piezas, franja asimétrica, regla de registro y tabla semántica de cantidades. El kit no incluye un editor 3D. No se añadió checkbox; no hay cuadros nativos blancos en oscuro.

La correspondencia de tokens está en `STYLES` del TSX y se duplica literalmente en un `<style data-direction>` del HTML tras el builder para que el analizador estático mida la paleta real. No se modifica el kit. Se usa la pareja ya existente `--taller-acento/--taller-sobre-acento` en oscuro; `--taller-medio` da bordes de controles ≥3:1. Los colores de tela son datos ilustrativos, no nuevos tokens de producto.

## Comportamiento conservado y límites

| Vista | Comportamiento de esta exploración |
|---|---|
| `tables` | Ocho tipos existentes, sus medidas iniciales leídas de `PARTIDA_MESA`, añadir sin formulario previo y abrir inspector. Rectangular: 2,40 × 0,90 × 0,75 m. |
| `table-editor` | Medidas, sillas, tipo, distribución y mantel/color; validación mantiene la última medida válida; deshacer/rehacer; advertencia pedidas/colocadas y acceso a lista. |
| `backing` | Siete IDs canónicos una vez cada uno; nombre original y alias hexagonal; filtro, sin resultados, recuperación y añadir. No cambia Shopify ni las identidades guardadas. |
| `shopping` | Modal existente con tabla de cantidades reales ilustradas y medidas, agrupada por Mobiliario/Escenografía. Mantiene los tipos y dimensiones de mesas añadidas previamente. Sin precio ni stock inventados. |
| `ai` | Prompt, validación, espera, propuesta ilustrativa y aplicar; enlace de edición manual. No invoca proveedor ni comprueba herramientas de IA. |
| `export` | Popover con PNG existente como contexto y GLB para Blender; preparar, impedir duplicado, error/reintentar, parcial bloqueado e inicio de descarga simulado. Ayuda de importación en metros; sin afirmación de verificación. |

Estados visibles: ready, loading, empty, error, success, validation (editor/IA), disabled, partial (editor/IA/exportación), permission-denied, offline y pending (IA/exportación). Los estados no aplicables quedan deshabilitados por vista, sin inventar otro flujo. Los selectores Diálogo abren lista y exportación desde cualquier contexto autorizado. Sin permiso se ocultan escena, nombre del proyecto y lista; no se simula un sistema de cuentas. Sin conexión se conservan datos locales y se ofrece reintento; añadir biblioteca/IA requieren conexión. Exportar solo representa una escena previamente completa y cargada.

La capacidad del mockup es **una fixture de ocho sillas por mesa**, rotulada como ejemplo; no sustituye `repartirSillas`. La ilustración representa la pieza seleccionada, sin reconstruir todos los sólidos ni el motor de cada tipo. El selector de tela cambia la muestra ilustrativa; no prueba materiales exportados. La lista local mantiene una fuente común para objetos añadidos, medidas y cantidades. No existe archivo GLB real, guardado de proyecto, backend, llamada de IA ni prueba de importación Blender.

## Reflow y accesibilidad

- ≥1280 px: índice 250 px y escena flexible; hoja 218 px / fluida / 264 px. Fichas de biblioteca en cuatro columnas.
- 1024–1279 px: márgenes 24 px, índice 218 px, hoja 186 px / fluida / 220 px; biblioteca en tres columnas.
- 768–1023 px: título contextual arriba y una única hoja activa; navegación 3 × 2 y catálogo de tres columnas.
- 480–767 px: escena y hoja apiladas, márgenes 20 px, catálogo de dos columnas. Ninguna barra inferior fija.
- 320–479 px: campos y fichas en una columna, títulos y acciones pueden envolver. Lista y exportación conservan 20 px de margen y scroll interno acotado.
- Paisaje 640–1023 px con altura ≤540 px: esquema se compacta a 210 px; documento y modal mantienen desplazamiento vertical.

Objetivo WCAG 2.2 AA: etiquetas visibles, nombres de acciones, estado actual semántico, errores relacionados con campos, anuncios de resultado y foco de 2 px. Los botones permiten seleccionar/añadir sin arrastrar. No se afirma conformidad completa. Reduced-motion y `?still=1` conservan contenido y foco sin viaje; no se elimina el transform de posicionamiento de ventanas flotantes. Los efectos son finitos, no hay animación ambiental continua.

## Auditoría y evidencia honesta

Builder real ejecutado offline por ruta absoluta: **655 KB, 2.193 archivos fuente** incorporados. Sin instalación, CDN, fuente o imagen externa. Se usa el builder real; no hizo falta fallback ni `kit/inline.py` de snippets.

`contrast.py` en el HTML final, con correspondencia de tokens inline: **158 pares en claro/oscuro, todos pasan**.

`UV_OFFLINE=1 uv run --offline --with playwright python …/kit/audit_mockup.py …/taller-esenciales@v1.r6.dir-a.html`: **288/288 renders a 1280/390 px, 11.496 mediciones de texto, 1.454 paradas de foco**. Sin advertencia de muestreo.

> RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems

La primera pasada falló con 70 avisos de alineación: una coincidencia geométrica hacía que el centro interpretara la composición como una única columna centrada. Se hizo más explícita la asimetría de la hoja. También se corrigió una regla de reducción de movimiento que anulaba el posicionamiento transformado del popover. Las pasadas completas posteriores, incluida la del HTML final, pasan. Una prueba adicional detectó que el centinela del Dialog instalado permitía llegar a la barra de revisión al pulsar Tab; la composición conserva el Dialog real y añade un ciclo explícito y acotado de Tab/Shift+Tab, junto a aria-modal. Las 24 comprobaciones de teclado posteriores pasan. No se modificó ni silenció el auditor.

Inspección visual en memoria: editor claro y oscuro de escritorio, editor oscuro móvil, biblioteca Backing oscura de escritorio y exportación con error en móvil claro. La suite enfocada verifica 106 aserciones, incluidas 72 combinaciones de reflow en seis tamaños y dos temas, sin errores JavaScript ni peticiones HTTP. Una aserción inicial de rehacer se hizo antes del efecto de React que actualiza el campo; se corrigió la espera de la prueba y la suite pasó, sin cambiar el comportamiento para ocultar el fallo. Se comprobaron además 24 ciclos Tab/Shift+Tab dentro del modal, Escape/restauración de foco, todos los selectores JSON y animación real de la regla (rule-register, 520 ms). Con still=1 no quedan animaciones en ejecución. No se escriben capturas ni archivos de prueba fuera del alcance autorizado. El propio auditor comprueba reduced-motion y desplazamiento acumulado durante la entrada. No se ejecutaron pruebas de producto, exportación real, Blender, proveedor de IA o conformidad completa de lectores de pantalla.

## Impacto y preguntas

**Compatibilidad:** breaking visual respecto del borrador previo (composición, navegación y jerarquía cambian); intención funcional/datos conservada. Si se elige esta dirección, la finalización deberá reconciliar los criterios visuales de `taller-esenciales@v1` sin mover requisitos o inventar comportamiento. Consumidores afectados: T3.1 copia exacta; T3.2 mesas/IA/lista; T3.3 Backing; T3.4 exportación; T3.7 revisión visual. T3.5/T3.6/T3.8 mantienen verificación funcional, Blender y auditoría. No cambia contratos de otros subplanes.

Q: ¿Adoptamos «Corte de montaje», con la escena sobre una hoja de trabajo asimétrica y navegación en su junta, como dirección visual para SP-3? Decisión de David en la comparación; no bloquea esta exploración.

Las cuatro decisiones funcionales de la ronda 9 permanecen resueltas. No se plantea una nueva alternativa de precios, IDs, formato de exportación o provisión de Blender. El contrato canónico conserva su estado draft; esta exploración no lo escribe ni aprueba.
