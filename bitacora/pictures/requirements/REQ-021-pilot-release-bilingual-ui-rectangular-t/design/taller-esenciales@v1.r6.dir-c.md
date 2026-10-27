---
name: Banco de montaje
status: draft
kind: direction-exploration
contract_ref: taller-esenciales@v1
subplan: SP-3
requirements: [R9, R10, R11]
revision: r6.dir-c
owner: David
date: 2026-10-26
chosen_thumbnail: taller-esenciales@v1.r6.dir-c.html.candidate-1.html
---

# Banco de montaje — dirección C

Exploración independiente, pendiente de elección del owner. **No es el contrato canónico ni una aprobación**. Solo se escriben las seis piezas de esta dirección y el RESULT.json requerido. No se modifica el contrato compartido, otra dirección, los repositorios, SPEC, PLAN ni archivos de historial.

## Concepto y gesto memorable

El Taller trata con cosas que se colocan, miden y combinan: mesas, sillas, aros, paneles y globos. La escena ocupa un **banco de corte ancho**, con cuadrícula de puntos, regla superior y piezas seleccionables; las herramientas viven en la junta del banco. La biblioteca se abre como bandeja debajo del plano. Al seleccionar una mesa, la bandeja se convierte en una regla de trabajo con tres grupos: medidas, sillas y acabado.

El gesto memorable es **encajar la pieza y desplegar su regla**: la regla superior se desenrolla de izquierda a derecha, la pieza se asienta con un pequeño giro y la bandeja recibe los controles desde abajo. Los datos están visibles durante el movimiento. Arrastrar la mesa tiene resorte y fricción; cuatro botones y las teclas de dirección ofrecen el mismo desplazamiento ilustrativo. La reducción de movimiento conserva todas las acciones y coloca inmediatamente la geometría final.

## Dos miniaturas, antes del mockup completo

- **Candidata 1 — elegida:** [Mesa de corte](taller-esenciales@v1.r6.dir-c.html.candidate-1.html). Plano ancho, herramientas en la junta y bandeja de piezas inferior. La escena y las medidas comparten un marco; el pie sigue su eje exterior.
- [Candidata 2 — Banco lateral](taller-esenciales@v1.r6.dir-c.html.candidate-2.html). Plano y regla a la izquierda, caja de piezas lateral. Conserva una relación más convencional entre biblioteca e inspector y comprime el espacio de la escena.

Ambas miniaturas se escribieron primero. Son composiciones visuales pequeñas, con CSS inline, tema claro/oscuro según el sistema y reflujo móvil; no sustituyen el mockup completo ni son un fallback del kit. El HTML completo se construye desde el TSX con las librerías reales instaladas.

## Por qué esta composición

La superficie principal responde a «¿cómo queda mi montaje?»; la bandeja responde a «¿qué pieza añado o qué medida cambio?». No hay una tercera columna lateral, un dashboard de métricas, una portada decorativa ni un asistente de pasos inventados. La grilla se reserva para objetos pares que se añaden a la escena. Las medidas son información de trabajo y usan cifras tabulares; la navegación permanece neutral.

El feedback del owner se resuelve con un único eje exterior para cabecera, banco y pie; padding de 24 px en paneles y 20 px en teléfono; contornos interactivos contrastados en ambos temas; y el Checkbox real de Base UI/Animate UI, en lugar de un checkbox nativo dependiente del navegador. La maqueta conserva las etiquetas y los selectores nativos del runtime: **Mockup, Vista, Estado, Diálogo, Tema y Movimiento**.

### Look ledger e identidad compartida

Se leyeron las notas hermanas de SP-2: `cuentas-admin@v1.r7.dir-a.md`, `.dir-b.md` y `.dir-c.md`. A usa margen editorial y registro; B, un pase desplegable y dock inferior; C, pases perforados y alojamientos de permisos. Aquí no se repiten margen editorial, pase, perforación, registro de personas ni dock. El banco, su regla desplegable y el inspector inferior nacen del trabajo espacial de SP-3. Se comparte intencionadamente la marca de anillo/punto, la paleta Pictures, la voz española directa y el feedback al pulsar.

## Ocho ejes

| Eje | Expresión presente | Evidencia |
|---|---|---|
| Concepto | Banco de corte y montaje: regla, plano, piezas y bandeja de herramientas. | `.bench`, `.ruler-edge`, `.cutting-plane` |
| Composición | Plano de ancho completo sobre bandeja; inspector horizontal de tres grupos, sin inspector lateral. | `.bench`, `.pieces-grid`, `.measure-rule` |
| Navegación | Cuatro herramientas en la junta superior; lista y exportación en la cabecera; historial junto al banco. | `.tool-tabs`, `.header-actions`, `.history` |
| Tipografía | Arial/Helvetica/sans local; título 30/27 px, panel 21 px, nombres 15/14 px, etiquetas 13–14 px; medidas monospace. | `.project-line h1`, `.piece-info h3`, `.dimension-tag` |
| Densidad y forma | Banco de radio 24/18 px; piezas de radio 16 px; panel 24/20 px; controles de 44 px; plano 294 px en escritorio y 320 px en teléfono. | `.bench`, `.piece-card`, `.work-area`, `.cutting-plane` |
| Componentes | Button, Input, Textarea, Checkbox, Skeleton y Dialog reales; SVG de piezas, recibo y banco propios. | `[data-slot=button]`, `[data-slot=checkbox]`, `.receipt`, `.table-assembly` |
| Color | Tokens Pictures por tema; acento en piezas y acción primaria, navegación neutral; aviso/error/éxito con texto. | `.piece-art`, `.press[data-variant=default]`, `.feedback` |
| Movimiento | Desenrollado, asentamiento, encaje de bandeja y presión; resorte al arrastrar. Expresivo 650 ms, natural 400 ms, sutil 220 ms; desfase de piezas 40 ms; controles 180 ms. | `.ruler-edge`, `.table-assembly`, `.piece-card`, `.work-area`, `.press` |

El JSON compañero identifica selectores reales, diferenciados por eje. Los selectores de movimiento tienen keyframes o transiciones efectivos. No se usa una animación ornamental infinita: la entrada es finita; el CSS pausa en pestaña oculta. Los esqueletos permanecen estables. `prefers-reduced-motion`, Quieto y `?still=1` eliminan la coreografía y mantienen el contenido, las acciones y el arrastre voluntario.

## Sistema existente y procedencia

Lectura de ambos repositorios: `src/app/globals.css`, `FondosYMuebles.tsx`, `EditorConjuntoMesa.tsx` y los tipos/defaults compartidos de mobiliario. Los archivos de tipos y editor de mesa son idénticos entre t12 y asesor; los CSS completos difieren, por lo que no se presume identidad de ambos archivos. Se toman los tokens de marca coincidentes y el visor del Taller. También se inspeccionan asignación de fondos, nombres originales y el exportador GLB de asesor.

| Token Pictures | Rol del kit / adaptación | Claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | `#faf9fc` / `#0b0c10` |
| `--superficie` | `--card`, `--popover` | `#ffffff` / `#16181f` |
| `--texto` | foregrounds | `#1c1425` / `#f4f5f7` |
| `--texto-suave` | `--muted-foreground` | `#6b6178` / propuesta local `#adb3c0` para metadatos oscuros |
| `--superficie-2` | secondary/muted | `#efe9f8` / `#242733` |
| `--acento`, `--sobre-acento` | primary / primary-foreground / ring | `#6d3fe0`, blanco / `#9479ff`, `#120b24` |
| `--taller-visor` | `--board` de la composición | `#ebe7f1` / `#1a1722` |
| `--borde` | separadores decorativos | `#e3daef` / `#383c48` |
| `--texto-tenue` / `--texto-suave` | `--input`, borde interactivo más visible | `#766c85` / `#9aa1ad` |
| `--exito`, `--aviso`, `--error` | estados y fondos suaves correspondientes | valores Pictures por tema |

Las propuestas locales de borde interactivo y texto secundario oscuro no cambian producción. Geist usa aquí una alternativa offline Arial/Helvetica/sans; no se descarga una fuente. Los SVG de mesas y Backing son diagramas propios con los colores del producto; no son una representación del motor 3D.

Componentes: `shadcn:button` (`@/components/ui/button`, default/outline/ghost y estados); `shadcn:input`, `shadcn:textarea`; `shadcn:checkbox` (Animate UI sobre Base UI, con contorno explícito y checked/disabled); `shadcn:skeleton`; `shadcn:dialog` (Animate UI sobre Base UI, con bucle Tab/Shift+Tab explícito en la composición). `@kit/mockup` proporciona mountMockup/useMockup y selectores nativos; `@kit/motion` proporciona perfiles/reducción; `motion/react` proporciona el gesto con resorte. No se instaló ningún paquete ni se usó el fallback HTML de snippets.

## Comportamiento y trazabilidad preservados

Fuentes: SPEC/PLAN vigentes, shared behaviour con digest **f3f2ed19d4dc6d0a**, y contrato draft existente leído como referencia de comportamiento. SHA-256 abreviado de entradas: SPEC `65b1e5ecc06f20d9`, PLAN.md `cc7e53f2abf3c23c`, PLAN.json `7a2c833a7e711508`, fichero de comportamiento `4113589a9342573e`. La ronda 9 resuelve tarjetas por tipo, lista sin alquileres, traslado de siete Backing y verificación Blender portable; esas decisiones no se reabren.

| Vista / selector | Comportamiento y datos | Requisito / consumidor |
|---|---|---|
| Mesas / `tables` | Ocho tarjetas de tipos existentes; tamaños iniciales del fuente. Rectangular 240 × 90 × 75 cm; Añadir selecciona la pieza y abre el inspector, sin formulario previo. | R9 / T3.2 |
| Inspector / `table-editor` | Largo, fondo, alto con rangos del tipo; cantidad solicitada/colocada; tipo y disposición de silla; mantel, color y camino; validación conserva última geometría válida; deshacer/rehacer; lista accesible. | R9 / T3.2 |
| Backing / `backing` | Siete tarjetas una vez, con IDs originales. Se conservan Panel redondo, Media luna, Arcos chiara, Pedestales, Aro metálico, **Marco hexagonal metálico** y Arco metálico; «aro hexagonal» sigue siendo alias de búsqueda. Añadir actualiza el recibo local. | R11 / T3.3 |
| Lista / `shopping`, diálogo `shopping` | Medidas en metros y cantidades colocadas, diferenciadas por mesa y tipo de silla; Backing agrupado por ID; no precios de alquiler ni total monetario. | R9 / T3.2 |
| IA / `ai` | Propuesta local, revisión/aplicación y alternativa de edición manual; pendiente y fallo visibles; no llamada pagada. La implementación debe conservar paridad de agregar_mesas/cambiar_mesas/cambiar_sillas con operaciones manuales. | R9 / T3.2 |
| Exportación / `export`, diálogo `export` | GLB para Blender, escala 1 unidad = 1 m, instrucciones de importación, pendiente, fallo reintentable y descarga iniciada simulada; piezas incompletas bloquean exportar; PNG queda como acción hermana existente. | R10 / T3.4 |

El reagrupamiento de Backing solo afecta la presentación en Taller Fondos y muebles. No se propone duplicarlo en grupos anteriores ni modificar Shopify `/catalogo`, identidades, repositorios, escenas guardadas o descubrimiento IA/foto. Estos últimos son obligaciones de implementación, no servicios ejecutados por el mockup. La maqueta muestra el subconjunto trabajado de Fondos y muebles, no elimina otras categorías de producción.

La escena de ejemplo comienza con una mesa rectangular, ocho sillas y un panel redondo. Las mesas añadidas conservan por separado medidas y cantidades en el recibo; cambiar el tipo de silla actualiza también su nombre y cantidad allí. El plano es esquemático: enfatiza la selección activa, no dibuja todas las instancias de cada Backing ni calcula el perímetro real. La capacidad ilustrativa es 8, o 12 con largo de al menos 300 cm; se etiqueta expresamente como ejemplo y **no se transfiere al motor**. La producción continúa usando repartirSillas y los defaults/rangos del fuente. El mockup no serializa GLB, no valida Blender, no persiste en servidor, no llama IA y no prueba permisos del backend.

## Estados, reflujo y accesibilidad

Los once estados son accesibles desde Estado: `ready`, `loading`, `empty`, `error`, `success`, `validation`, `disabled`, `partial`, `permission-denied`, `offline`, `pending`. El runtime conserva los ejes independientes para inspección; validación se aplica a inspector/IA, parcial a capacidad/propuesta/exportación y pendiente a IA/exportación. En otras vistas no se inventa un fallo específico de campo. Cargando conserva el plano y usa esqueletos; Vacío explica cómo continuar; Error ofrece Reintentar; Éxito anuncia resultado; Deshabilitado explica el límite; Sin permiso oculta escena y diálogos. Sin conexión conserva el trabajo local y bloquea IA remota; catálogo ya cargado, lista derivada y GLB con todos los assets disponibles pueden seguir siendo locales. La persistencia de SP-4 y el cambio de idioma de SP-8 quedan en sus subplanes.

- **1024 px y más:** plano sobre bandeja; biblioteca en cuatro columnas, inspector en tres grupos. Contenedor máximo 1440 px; padding exterior 32 px, 40 px en la anchura mayor.
- **768–1023 px:** biblioteca de tres columnas; medidas/sillas en dos grupos y acabado en una fila inferior; padding exterior 24 px.
- **360–767 px:** herramientas en 2 × 2; plano de 320 px con zonas separadas para pieza, medidas y flechas; biblioteca de dos columnas; inspector de una columna; padding exterior/interior 20 px. Scroll vertical del documento.
- **320–359 px:** biblioteca y campos numéricos en una columna. Ningún control requiere scroll horizontal.
- **Apaisado de altura ≤540 px y ancho <1024 px:** plano y área activa se disponen al lado; herramientas e indicadores conservan una fila propia. Se mantiene el patrón landscape del producto.

Diálogos con 20 px de margen exterior, máximo 640 px y altura acotada con scroll interno. Campos/botones de 44 px; flechas repetidas de 40 px escritorio y 38 px móvil con separación. Contraste objetivo 4.5:1 para texto, 3:1 para límites y foco; anillo visible de 3 px. El arrastre tiene flechas de teclado y botones con nombre accesible. La lista usa tabla semántica, los errores se vinculan al campo, los resultados usan status y los fallos alert. El diálogo mantiene Tab/Shift+Tab dentro, cierra con Escape y devuelve el foco al origen. Estas son metas y evidencia de la maqueta; no una certificación de accesibilidad de producción.

## Impacto y preguntas

Cambio **breaking visual respecto al draft anterior**: la jerarquía de plano/bandeja y el inspector horizontal requieren adaptación de composición y responsive; no se cambian las decisiones de producto de R9–R11. SP-3 conserva taller-esenciales@v1 como referencia futura. T3.1 copiará el contrato que el owner finalmente apruebe; T3.2 consume mesas/inspector/lista/IA, T3.3 Backing y T3.4 exportación. T3.7 deberá revisar la composición elegida; T3.5/T3.6 mantienen sus pruebas reales y T3.8 su auditoría. No hay aprobación ni actualización de consumidores en esta exploración.

**Q:** ¿Quieres adoptar «Banco de montaje», con biblioteca e inspector debajo del plano, como dirección de SP-3? Responsable: David, en la comparación de direcciones. No queda otra decisión funcional de SP-3 abierta en las fuentes leídas.

## Evidencia y auditoría honesta

La compilación offline real produjo un HTML autónomo de aproximadamente 600 KB y 2142 archivos fuente empaquetados. Sin red, fuente externa, imagen remota, instalación ni fallback. No se creó un preview de repositorio.

El primer audit completo informó `RESULT: FAIL — alignment 216`: el wrapper de la mesa tenía un botón interno y el auditor lo interpretaba como una columna de formulario centrada. Se convirtió en un único motion.button semántico; las verificaciones siguientes pasaron. Las etiquetas sobre el plano recibieron fondo sólido para que el contraste fuese medible. Una prueba rápida de teclado detectó escape a los guards externos del componente; el diálogo incluye ahora un bucle explícito para Tab/Shift+Tab. La revisión visual móvil detectó la cinta de medidas superpuesta a las sillas inferiores; se reservan zonas distintas en el plano de 320 px y se elimina un aviso de capacidad duplicado.

Comandos ejecutados contra el HTML de esta dirección:

```text
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <r6.dir-c.tsx> --out <r6.dir-c.html>
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py <r6.dir-c.html>
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py <r6.dir-c.html>
```

Resultado final del auditor, exit 0, sobre la compilación final:

```text
audit: taller-esenciales@v1.r6.dir-c.html — 312 renders (312 combinations planned), 9864 text measurements, 1552 focus stops
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Sin muestreo ni avisos de contraste no medido. El auditor recorre los seis views, once estados, ambos temas y los dos diálogos en 1280/390 px; también comprueba carga expresiva y asentamiento bajo reduced motion. El CLI de contraste informa `contrast: 158 pairs checked in light and dark, all pass`. Como los tokens Pictures se inyectan desde el TSX, se ejecutó además `contrast.check` sobre el CSS del kit más el CSS de esta dirección: **158 pares con el mapping Pictures, PASS**; el auditor renderizado comprueba los colores efectivos.

Pruebas focalizadas finales: nueve grupos de interacción pasan (selectores/tipos, añadir rectangular e inspector, capacidad/validación/recuperación, recibo coherente sin precios, bucle de foco/Escape/regreso al origen, undo/redo del tipo de silla, siete Backing/alias/añadir/lista, GLB pendiente/instrucciones/simulación, denegación sin escena ni diálogo). La primera versión del smoke comprobaba `is_visible()` inmediatamente después de Escape y falló mientras el nodo saliente ya transparente aguardaba su desmontaje; el smoke final espera el cierre del componente antes de verificar el foco. No se ocultó ese resultado como un pase.

La comprobación focalizada recorre **60 layouts** (seis vistas × cinco anchos 320/390/768/1024/1280 × dos temas) y **120 encajes de diálogo**, sin scroll horizontal ni diálogos fuera de sus márgenes. Cero errores de página y cero solicitudes HTTP/HTTPS en el recorrido. La comprobación de evidencia de compare_directions sobre esta dirección confirma **15 selectores, todos válidos**, sin evidencia ausente; no se ejecutó una comparación por pares con las otras exploraciones. Se observaron **12 animaciones reales activas** al cargar con movimiento expresivo; `?still=1` produce cero animaciones activas y conserva las ocho tarjetas.

Se inspeccionaron capturas en memoria: mesas en escritorio claro, inspector en escritorio oscuro, Backing en teléfono claro e inspector/capacidad en teléfono oscuro. La captura final del plano móvil confirma que la pieza, la cinta de medidas y las flechas tienen zonas separadas. No se escribieron capturas ni logs adicionales.

La evidencia corresponde exclusivamente a la maqueta. Geometría real, paridad de herramientas IA, autorización del servidor, GLB válido, importación automática en Blender LTS y apertura manual del owner quedan a T3.2–T3.8. El artefacto continúa **draft y sin aprobar**.

