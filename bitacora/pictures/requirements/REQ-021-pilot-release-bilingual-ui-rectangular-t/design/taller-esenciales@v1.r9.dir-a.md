---
name: Cota viva
status: draft
kind: independent-direction-exploration
contract_ref: taller-esenciales@v1
revision: r9.dir-a
subplan: SP-3
requirements: [R9, R10, R11]
owner: David
date: 2026-10-27
approval: pending-owner-selection
chosen_thumbnail: taller-esenciales@v1.r9.dir-a.html.candidate-1.html
---

# Cota viva — dirección A

## 1. Identidad y trazabilidad

Exploración editorial/operativa **sin aprobar**. Es una nota de dirección, no el contrato canónico ni una entrada autorizada para implementación. El owner elige; una finalización posterior redacta `taller-esenciales@v1`. No se modifica SPEC, PLAN, contrato compartido, historial, repositorio ni otra dirección.

Fuentes: SPEC.md `65b1e5ecc06f20d9`, PLAN.md `cc7e53f2abf3c23c`, PLAN.json revisión 1 `7a2c833a7e711508`, comportamiento compartido r9 `4113589a9342573e` (prefijos SHA-256). SP-3 cubre R9 mesas rectangulares, R10 GLB/Blender y R11 Backing; T3.1 copia el futuro contrato aprobado, T3.2 consume mesas/inspector/lista, T3.3 Backing y T3.4 exportación. T3.5–T3.6 verifican integración/Blender, T3.7 revisa fidelidad y T3.8 audita. Ninguna referencia se cambia aquí.

Repositorios consultados en solo lectura: `t12` y `pictures` (`asesor`): `src/app/globals.css`, FondosYMuebles, EditorConjuntoMesa, tipos/valores iniciales/límites de mobiliario, catálogo de fondos/muebles y sillas, y reparto por perímetro. El runtime de diseño está fuera de git, instalado y construido: **96/96 componentes disponibles**.

## 2. Propósito, concepto y gesto memorable

**Una hoja de montaje acotada.** Quien decora necesita saber qué cabe, cuántos puestos colocó y qué piezas debe preparar. El plano domina; sus cotas se leen junto al inspector, y las cantidades viajan a la lista. El mundo material son los paneles y arcos de Backing, la mesa y las sillas, la retícula de instalación y la silueta de globos de látex. Los nombres Pictures y Sempertex, el emblema de círculos enlazados y el vocabulario Taller mantienen la identidad compartida.

**Gesto memorable:** la mesa se registra desde abajo, las sillas toman posición en intervalos y la línea de cota termina de extenderse horizontalmente mientras el inspector baja a su eje. Las piezas se alinean como al replantear un montaje. El contenido permanece opaco y legible; no se usa un fundido que borre las medidas.

**Por qué no es el SaaS por defecto:** un título de dos líneas con escala expresiva conduce a una superficie acotada y a un inspector estrecho; no hay rejilla de indicadores. El rojo señala la pieza/medida activa y la acción principal sobre papel gris frío; las divisiones y nombres resuelven la navegación. Los otros capítulos tienen composiciones propias: especímenes, lista con margen de cantidades y hoja de entrega GLB.

## 3. Dos miniaturas y ledger

Las dos miniaturas HTML se escribieron **antes** de la entrada TSX y del mockup completo, desde cero:

1. **Elegida:** `taller-esenciales@v1.r9.dir-a.html.candidate-1.html`. Plano ancho e inspector contiguo; capítulos directos; tarjetas de tipos debajo. Relaciona el campo editado con su medida y reserva el protagonismo para el trabajo.
2. `taller-esenciales@v1.r9.dir-a.html.candidate-2.html`. Gran medida tipográfica a la izquierda y dibujo al lado. Se descarta porque la cifra compite con la escena y deja menos espacio para editar sin desplazarse.

Ledger leído: Cuentas r10 A/B/C y Proyectos r8 A/B/C. Se evita el registro de personas con anotación lateral de Cuentas A, el pórtico inflable B, las bandas anudadas C, el archivo desplegable de Proyectos A, el bastidor con cinta B y los folios C. Se comparten claridad, vocabulario, marcas y semántica de estados. Este plano técnico no repite su composición o navegación. Los nuevos valores de color y fuentes son propuestas de esta exploración, no cambios ya aprobados de Pictures.

## 4. Ocho ejes y sistema visual

| Eje | Decisión presente en el mockup | Evidencia |
|---|---|---|
| Concepto | Hoja acotada de instalación: cotas, puestos y piezas antes de entregar el archivo. | `.plan`, `.measure-x`, `.chair-report` |
| Composición | Título asimétrico; plano ancho e inspector de 318px; ocho tarjetas debajo. Backing en filas; lista con margen numérico; archivo e instrucciones contiguos. | `.intro`, `.work-grid`, `.table-types`, `.list-layout`, `.export-layout` |
| Navegación | Cuatro capítulos con nombre y regla activa; dos por fila en teléfono. Acceso directo, sin carrusel o gesto obligatorio. | `.chapters`, `.chapter[aria-current="page"]` |
| Tipografía | Syne Variable 50–80px en título, 26px en secciones; Instrument Sans Variable 13–16px en trabajo; JetBrains Mono Variable 11–13px en cotas/datos. Tres paquetes locales embebidos. | `.display-title`, `.dimension-readout`, `.scene-caption small` |
| Densidad y forma | Campos cuadrados, reglas visibles, grupos compactos con separación de 24–32px y controles de 44px. La superficie del plano recibe el espacio. | `.fields`, `.prop-row`, `.purchase-list` |
| Componentes | Button/Input/Alert/Skeleton reales; dibujo técnico, tarjetas de tipo y siluetas Backing propios. Ningún fallback de snippets HTML. | `.btn`, `.field`, `.status`, `.type-card`, `.prop-icon` |
| Color | Gris frío #e9ecee y papel #f9fafb, tinta #242a2d y rojo de registro #a81e2d. Oscuro: grafito #161c20/#20292f, texto #eef1f2, rojo pálido #ff9ba6. | `:root`, `html[data-theme="dark"]` |
| Movimiento | Registro preciso con curvas de corte, secuencias por eje y offsets medidos; scroll del catálogo, presión de botones, golpe de estado y avance GLB. | `.scene-table`, `.seat`, `.measure-x`, `.inspector`, `.type-card`, `.chapter` |

Mapeo de responsabilidades existentes al kit, realizado una vez por tema:

| Pictures | Roles del kit | Propuesta claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | #e9ecee / #161c20 |
| `--superficie` | `--card`, `--popover` | #f9fafb / #20292f |
| `--texto` | `--foreground`, `--card-foreground` | #242a2d / #eef1f2 |
| `--texto-suave` | `--muted-foreground` | #505b61 / #b6c1c7 |
| `--acento`, `--sobre-acento` | `--primary`, `--primary-foreground` | #a81e2d sobre blanco / #ff9ba6 con #281217 |
| `--borde` y borde de control | `--border`, `--input` | #7d898f y #6c787f / #86969f y #93a1aa |
| Éxito/aviso/error existentes | `--success`, `--warning`, `--destructive` | Mantienen su significado; valores por tema verificados por el checker. |

La exploración responde a la petición explícita de evitar el morado compartido. No afirma que esta paleta ya exista en producción. Los roles `--taller-*` del visor existente conservan su responsabilidad en la futura adaptación; no se retokeniza el repositorio desde este artefacto.

Inventario: `shadcn:button` variante default/outline, normal/hover/focus/disabled; import `@/components/ui/button`. `shadcn:input` numérico/búsqueda, normal/invalid/disabled; import `@/components/ui/input`. `shadcn:alert` estado inline; import `@/components/ui/alert`. `shadcn:skeleton` carga; import `@/components/ui/skeleton`. Los controles operables usan Base UI y el proveedor Motion; no se necesitan React Bits ni gestos Bencho para esta responsabilidad. La retícula, cotas y siluetas CSS son componentes propios de ilustración, sin motor WebGL.

## 5. Navegación, comportamiento conservado e impacto

La entrada es Taller → Fondos y muebles. Dentro de la exploración, Mesas, Backing, Lista de compra y Exportar GLB son capítulos directos. El idioma Español/English cambia el contenido de las cuatro vistas y se conserva al cambiar de capítulo dentro del mockup. La detección inicial y persistencia por cuenta pertenecen a SP-6; no se simula una cuenta real.

R9: ocho tarjetas de tipos existentes —redonda, cuadrada, rectangular, ovalada, cóctel, media luna, serpentina y U— añaden con tamaño inicial y seleccionan el inspector. Rectangular empieza en **240 × 90 × 75cm**. Largo, fondo, alto y sillas permiten ver el flujo de edición; aplicar actualiza el registro de ejemplo y la lista; deshacer recupera el último registro. Las piezas Imperial fijas siguen indicadas. La implementación conserva el inspector completo existente, sus tipos de silla, mantel/colores, disposiciones, piezas fijas y herramientas `agregar_mesas`, `cambiar_mesas`, `cambiar_sillas`. Esta exploración no elimina opciones existentes por mostrar solo los controles esenciales.

R11: un grupo Backing, una tarjeta por `panel_redondo`, `media_luna`, `arcos_chiara`, `pedestales`, `aro_metalico`, `aro_hexagonal` y `arco_metalico`. Conserva los nombres originales; «Marco hexagonal metálico» sigue encontrándose por ese nombre o por su ID. Añadir actualiza la cantidad del ejemplo. En el producto se mueven las tarjetas desde sus grupos visuales anteriores, sin duplicar, cambiar IDs/repositorios, romper escenas ni cambiar descubrimiento por IA/foto. Shopify `/catalogo` queda fuera del cambio.

R10: exportación de GLB del montaje, preparación, éxito y error recuperable; medidas en metros, transformaciones y colores base, sin alterar la escena ni llamar a la red. Las instrucciones de importación aclaran diferencias de luz/efectos. La provisión de Blender LTS oficial y su verificación de checksum, prueba real de importación y apertura del owner son tareas del plan; el mockup no ejecuta ni acredita esas pruebas.

Impacto visual propuesto: T3.2–T3.4 y revisión T3.7. La composición necesita adaptación de vistas, navegación, tokens, foco y breakpoints si se elige. **Compatibilidad visual: undetermined** hasta selección/finalización; no hay autorización para que una implementación consuma este borrador. Las pruebas T3.5–T3.6 y la auditoría T3.8 siguen siendo independientes.

## 6. Lenguaje de movimiento

Se lee `useMotionProfile()` y se usa su duración/reduced en Motion. Expresivo es el valor inicial. Curvas propias: registro `cubic-bezier(.76,0,.24,1)` y asentado `cubic-bezier(.16,1,.3,1)`; no se reutiliza el rebote inflable de otras direcciones.

| Comportamiento | Disparador y tiempo expresivo |
|---|---|
| Registro del capítulo | Montaje/cambio de vista o estado: desplazamiento horizontal corto, CSS 520ms y Motion según perfil. |
| Mesa | Traslación vertical de 18px y corrección de −1.4°, 650ms. |
| Sillas | Registro de 10px en 440ms, 45ms entre puestos. |
| Cota | Extensión horizontal desde .55 a 1, 820ms; texto opaco durante el recorrido. |
| Inspector | Entrada vertical desde arriba, 600ms. |
| Látex ilustrado | Giro inicial −23° a −12° y asentado lateral, 750ms; sin bucle decorativo permanente. |
| Tipos de mesa | Registro horizontal, 450ms con intervalos de 32ms; el catálogo también se registra al entrar en el viewport. |
| Navegación y botones | Regla horizontal activa y flecha; elevación de 2px al hover y presión de 1px; duración rápida del perfil, 200ms expresivo. Foco inmediato. |
| Estado | Golpe lateral corto, 350ms; el texto no desaparece. |
| Archivo | Corrección vertical y de inclinación, 800ms; avance GLB de 1.5s mientras prepara. |

Natural reduce entradas de página/mesa/inspector a 320ms; sutil a 180ms; los controles toman los tokens rápidos del perfil. El resto conserva su secuencia característica. No se promete que todo efecto cambie de escala por perfil. `prefers-reduced-motion`, «Quieto» y `?still=1` desactivan viajes, keyframes y transiciones y mantienen contenido/acciones. El avance tiene texto y finalización manual equivalente. Las animaciones CSS se pausan con pestaña oculta; el pequeño movimiento de scroll se dispara una vez al entrar, sin trabajo continuo fuera de pantalla. No hay flash ni cambios de opacidad del texto para lograr movimiento.

## 7. Vistas y datos de ejemplo

- **Mesas:** plano superior e inspector; cuenta colocadas/solicitadas; tarjetas con tamaño inicial y acción Añadir; piezas Imperial indicadas. La escena es un **esquema fijo de ocho puestos**, rotulado como tal; no pretende mostrar la geometría total ni recalcular el motor 3D.
- **Backing:** buscador por nombre original/ID, siete filas con silueta y acción; cuenta por pieza en el montaje; nota/plano auxiliar en escritorio. El contenido de trabajo sigue disponible cuando esa ilustración auxiliar se omite en pantallas pequeñas.
- **Lista:** cantidades realmente registradas en el ejemplo y dimensiones de mesa/silla/Backing, sin precios de alquiler. Mesa 240 × 90 × 75cm, Tiffany 45 × 45 × 90cm; panel Ø150cm; Arcos Chiara 120 × 210 / 105 × 190 / 80 × 165cm. Las medidas de piezas provienen de los catálogos inspeccionados. No se presentan costes, totales comerciales ni consumos de IA inventados.
- **Exportar:** hoja `.glb`, nombre `lucia-andres.glb`, escala 1:1 en metros, piezas visibles y colores base; acción y pasos para Blender. Exportar → Preparando → «Completar simulación» → éxito. El mockup no descarga un archivo falso.

Lucía & Andrés y la fecha son datos ilustrativos. La capacidad de los otros tipos de mesa está simplificada en esta simulación; la rectangular usa el caso de Tiffany de 45cm + 6cm de aire para demostrar 300 × 100cm/12 sillas. **El motor existente, no esta aritmética de mockup, determina las posiciones y cantidades reales en producción**. El escenario de capacidad predefinido representa 240 × 90cm, dos lados largos, 8 colocadas de 12 solicitadas. No se usa como prueba de integración o equivalencia con herramientas IA.

## 8. Estados y recuperación

Los selectores nativos `view`, `state`, `scene`, `theme` y `motion` del runtime permanecen visibles; etiquetas «Vista», «Estado», «Diálogo», «Tema», «Movimiento». «Mockup» permanece. No hay modal en esta dirección: Diálogo tiene «Sin diálogo»; la ayuda Blender está en flujo.

| Estado | Presentación y acción |
|---|---|
| normal | Contenido de ejemplo y acciones disponibles. |
| cargando | Skeleton con forma de líneas, explicación y controles esenciales de modificación desactivados. La navegación sigue disponible. |
| vacio | Explicación y acción para empezar; en Backing significa búsqueda sin coincidencias. Exportar queda desactivado. |
| error | Montaje preservado, error con instrucción y Reintentar. En exportación nombra GLB. |
| exito | Confirmación inline; en exportación dice explícitamente «simulación». |
| capacidad | 8/12, cuatro sin colocar, distribución de dos lados largos; lista cuenta ocho y Ajustar mesa vuelve al inspector. |
| validacion | Medida 720cm inválida, campo marcado y límite 100–600cm; valor inválido no aplicado. |
| exportando | Texto de preparación y avance, CTA exportar desactivado, botón para completar la simulación. Este estado se demuestra en el capítulo Exportar; las demás vistas conservan su contenido. |

Las mutaciones locales del ejemplo emiten confirmación con Deshacer. No se inventa un permiso específico de exportación ni un guardado cloud para SP-3. Offline no bloquea la operación GLB local; la política de acceso y guardado/conflictos se consume de SP-1/SP-4. Los estados de esos otros subplanes no se duplican aquí.

## 9. Reflujo

- **Más de 1050px:** padding lateral 36px, plano/inspector de 318px, catálogo de cuatro columnas, Backing con margen ilustrado y lista con margen numérico. A partir de 1600px el padding es 48px y el ancho total se limita a 1500px.
- **761–1050px:** padding 24px, inspector 280px, plano flexible; Backing usa todo el ancho y omite solo la ilustración auxiliar. Lista conserva margen de 180px.
- **Hasta 760px:** padding 20px; navegación 2×2; título y contexto se apilan; plano antes del inspector; tarjetas 2 columnas; Backing una columna; filas de compra se convierten en pieza, medida y cantidad derecha; exportación e instrucciones se apilan. No se requiere deslizar horizontalmente ni abrir un menú para llegar a las cuatro secciones.

Auditoría completa a 1280/390px; comprobación adicional de inglés a 390/768/1280px, ambos temas. Los breakpoints son una propuesta explícita de esta dirección, no una afirmación sobre el producto implementado.

## 10. Accesibilidad y verificación honesta

Objetivo WCAG 2.2 AA: texto ≥4.5:1, bordes/foco ≥3:1; controles principales de 44px; labels vinculados; `aria-current` en capítulo, `aria-pressed` en tarjetas; foco de 3px con separación de 4px; avisos `status` y errores `alert`; tabla con caption, encabezados y números tabulares; dibujo con descripción textual. Color no es la única señal de selección/estado. No hay checkbox/radio nativo de contraste incierto.

Herramientas ejecutadas offline por ruta absoluta:

- Builder real `components mockup build` sobre la entrada y HTML **r9.dir-a**: exit 0, **744KB, 2032 fuentes empaquetadas**. El HTML final incluye además el mismo CSS de dirección en `<head>` para que el checker estático lea los valores realmente aplicados; no se usa fallback. Tamaño final 780057 bytes.
- `contrast.py` sobre el HTML final: **158 pares, claro y oscuro, all pass**.
- `UV_OFFLINE=1 uv run --offline --with playwright .../audit_mockup.py` sobre el HTML final: **128 renders de 128 combinaciones, 5654 medidas de texto, 622 paradas de foco**, exit 0.

**RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems**

- Capturas inspeccionadas en memoria: Mesas 1280 claro/390 oscuro, Backing 1280 oscuro, Lista 390 oscuro y Exportar 390 claro; sin escribir imágenes adicionales. Revisión de medidas, márgenes, fuentes, lectura oscura y pies alineados.
- Smoke del mockup: 300 × 100 × 75cm y 12 sillas, actualización de lista, siete nombres Backing, búsqueda «Marco hexagonal metálico», añadir pieza y preparación/éxito de exportación: PASS. Primer intento del script encontró dos botones llamados Exportar GLB; el locator se acotó a la hoja de exportación y la prueba pasó, sin cambiar el producto por ese error del script.
- Inglés: **24 combinaciones** vista/tema/ancho a 390/768/1280px sin overflow; cero errores de runtime y cero peticiones HTTP. `?still=1`: cero animaciones en ejecución.
- `compare_directions.py A.html B.html C.html --json`: exit 0, **ok=true, evidence_ok=true**, sin selectores ausentes. Similitud geométrica A/B **0.006**, A/C **0.019**, B/C **0.024**; en ningún par coincidieron tipografía, navegación o movimiento. El primer chequeo parcial A/C detectó que `.chapter` no animaba directamente: se corrigió la evidencia a `.chapter svg`, la flecha que sí tiene transición, y la comparación completa pasó. Un resultado mecánico no implica aprobación o preferencia del owner.

La auditoría no equivale a una certificación AA completa, no verifica lectores de pantalla ni la aplicación desplegada. No se ejecutaron pruebas del repositorio, llamadas IA pagadas, exportación GLB real ni Blender. No se reportan como aprobadas.

## 11. Criterios visuales para la futura finalización

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| A-01 | 1060–1500px | normal / Mesas | El plano y el inspector están contiguos; las cotas usan cm y el inspector muestra 240 × 90 × 75cm. |
| A-02 | 390px | normal / Mesas | La navegación contiene cuatro capítulos en dos filas, sin desplazamiento horizontal. |
| A-03 | 390/1280px | normal / Mesas | Hay ocho tarjetas de tipos, cada una con nombre, dimensiones y Añadir. |
| A-04 | 390/1280px | capacidad | El aviso muestra 8 colocadas de 12 solicitadas y explica cuatro sin colocar en los dos lados largos. |
| A-05 | 390/1280px | normal / Backing | Los siete nombres aparecen una vez; cada uno tiene su acción Añadir. |
| A-06 | 390/1280px | normal / Lista | Las piezas muestran cantidades y medidas; no hay columna o precio de alquiler. |
| A-07 | 390/1280px | exportando | Preparando GLB y la acción desactivada son visibles; el mockup ofrece completar la simulación. |
| A-08 | 390/1280px | error / Exportar | Reintentar aparece junto a una explicación y no se afirma que el montaje se haya alterado. |
| A-09 | 390/1280px | validacion | El campo largo se marca inválido y el texto muestra el límite 100–600cm. |
| A-10 | 390/1280px | cargando | Hay skeleton y texto de carga; el inspector no permite aplicar un cambio. |
| A-11 | 390/1280px | vacio | La explicación y siguiente acción son legibles; exportación vacía no se puede iniciar. |
| A-12 | 390/1280px, ambos temas | normal | El foco es visible, separado del borde, sin recortes; pie y contenido respetan el mismo padding exterior. |
| A-13 | 390/1280px | reduced / still | El contenido y las acciones coinciden con el estado asentado; no hay animaciones corriendo. |
| A-14 | 390/768/1280px | normal / English | Los cuatro capítulos y medidas refluyen sin overflow y la elección de idioma sigue activa al cambiar de vista. |

## 12. Preguntas y supuestos

Decisiones ya confirmadas: tarjetas por tipo, rectangular inicial 240 × 90 × 75cm, cantidades reales sin precios de alquiler, siete Backing movidos sin duplicar, GLB existente y verificación real con Blender LTS. No se reabren como preguntas.

Q: ¿El owner elige la dirección Cota viva, con rojo de registro, gris frío y la combinación Syne/Instrument Sans/JetBrains Mono, para la finalización? Paleta y fuentes siguen siendo propuestas.
Q: ¿Se conserva «Cota viva» como título expresivo de Mesas, o se usa «Mesas» y se reserva el nombre para la dirección? Recomendación: «Mesas» en el producto final para hacer explícito el destino.
Q: ¿Se aprueba la navegación de cuatro capítulos dentro de Fondos y muebles o debe adaptarse al panel existente conservando la misma jerarquía? Recomendación: revisar esta composición junto al shell completo de Taller antes de congelar el contrato.

Supuestos de exploración: cuenta autorizada a usar Taller, datos locales ilustrativos y vista del mobiliario; no se implementan persistencia cloud, motor 3D, límites exactos de todas las geometrías, herramientas IA ni exportador. Estos límites del artefacto no recortan los requisitos del producto.
