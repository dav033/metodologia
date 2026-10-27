---
name: Órbita de montaje
status: draft
kind: independent-direction-exploration
contract_ref: taller-esenciales@v1
revision: r9.dir-b
subplan: SP-3
requirements: [R9, R10, R11]
date: 2026-10-27
owner: David
approval: pending-owner-selection
chosen_thumbnail: taller-esenciales@v1.r9.dir-b.html.candidate-1.html
---

# Órbita de montaje — dirección B

Exploración cinética y espacial **sin aprobar**. Este documento no es el contrato canónico de doce secciones ni autoriza implementación. El encargo de exploración sustituye la pareja canónica: se entregan solamente las dos miniaturas, TSX, HTML, esta nota, JSON de ejes y el RESULT de delegación. No se modifican planes, contratos compartidos, historia, repositorios ni otras direcciones.

## Concepto, gesto memorable y elección

El Taller es un montaje en preparación: una mesa sobre la pista elíptica del evento, el Backing al fondo, globos de látex y un volumen de foil suspendido. Las herramientas son tres **paletas orbitales** alrededor de ese montaje. La persona no entra en un panel administrativo: elige dónde trabajar sobre su instalación y encuentra un plano estable de medidas al lado.

**Gesto memorable:** el suelo elíptico gira hasta quedar registrado; la estructura corrige su inclinación; los globos tensan la composición y la mesa se asienta en diagonal. Las paletas llegan con torsión escalonada mientras el plano operativo corrige su perspectiva. El texto permanece opaco y disponible durante la coreografía. Después, únicamente el pequeño foil mantiene un balanceo lento, suspendido fuera de pantalla y en pestañas ocultas.

Las dos miniaturas originales se escribieron antes del TSX completo:

- **Elegida, candidata 1:** `taller-esenciales@v1.r9.dir-b.html.candidate-1.html`. Escenario elíptico y tres paletas en posiciones distintas; plano operativo con eje propio y pie alineado con los márgenes exteriores. Su composición fue inspeccionada en Chromium. La mesa abstracta de la miniatura se convierte en una mesa rectangular reconocible en el desarrollo completo.
- Candidata 2: `taller-esenciales@v1.r9.dir-b.html.candidate-2.html`. Pista trapezoidal y estaciones agrupadas al pie. Se conserva como boceto: la convergencia de la pista y el bloque inferior compiten por la entrada al inspector y se acercan más a una barra de herramientas convencional.

**Por qué no es el valor por defecto:** navegación repartida sobre la escena, suelo elíptico inclinado, un display cursivo expresivo, plata física y acciones cereza sobre verde frío. No hay cuadrícula de indicadores, morado genérico, crema/terracota, verde ácido sobre negro ni gradiente detrás del texto. Los degradados están dentro del dibujo SVG de látex y foil. La información de trabajo usa superficies opacas y controles conocidos.

## Look ledger e identidad compartida

Se leyeron las notas de cuentas r10 A/B/C y proyectos r8 A/B/C: registro de producción, umbral inflable, bandas de tensión, archivo, escenario frontal con cinta y muestrario. Se conserva Pictures, la marca circular, el vocabulario del decorador, las unidades físicas y la recuperación explícita. Esta propuesta evita el registro con rail, umbral de acceso, bandas de permisos, fichas archivadas, cinta de proyectos y navegación fija inferior. La barra nativa de planificación es compartida deliberadamente porque el comparador la controla.

La paleta verde/cereza y la pareja cursiva/humanista son propuestas locales para esta exploración; los valores morados actuales del producto no se presentan como cambiados. Tras la composición independiente se revisó también la nota de Taller r9 C: su bandeja moldeada y cinturón fijo inferior se diferencian de las paletas distribuidas de B. No se copió ni modificó su composición.

## Ocho ejes observables

| Eje | Expresión presente | Evidencia renderizada |
|---|---|---|
| Concepto | Escenario de evento en preparación, Backing al fondo, mesa y herramientas alrededor de la pista. | `.orbit-stage`, `.set-illustration`, `.orbit-nav` |
| Composición | Escenario de 440 px a la izquierda; plano operativo a la derecha; ocho formas o siete piezas de Backing en rieles inferiores. No hay navegación lateral fija. | `.assembly`, `.left-stage`, `.working-plane`, `.shape-grid` |
| Navegación | Mesas abajo a la izquierda, Backing arriba a la derecha y Salida GLB abajo a la derecha. Editar mesa está sobre el objeto; Lista en cabecera y en el inspector. Son botones operables con teclado. | `.orbit-nav`, `.nav-mesas`, `.nav-backing`, `.nav-export`, `.table-action` |
| Tipografía | Liberation Serif Italic local, embebida como Air: display 52–90 px, medidas 56 px. Adwaita Sans local, embebida como Workshop: datos y controles 13–24 px. Display móvil 58 px, sin forzar una sola línea. | `.display`, `.big-measure`, `.plane-title`, `.field` |
| Densidad y forma | Márgenes exteriores 40 px, plano 28 px, esquina de entrada 60 px; rieles con 12 px interiores; campos 46 px y acciones ≥44 px. Teléfono: margen 20 px y plano 22 px. | `.shell`, `.working-plane`, `.type-piece`, `.native` |
| Componentes | Button, Input y Skeleton reales; Dialog real de Animate UI; paletas, escenario SVG, rieles de formas y lista rayada propios. Se reutilizan normalización y cálculo de sillas del repositorio, en lectura. | `[data-slot=button]`, `[data-slot=input]`, `.dialog-box`, `.shopping-item` |
| Color | Verde frío claro #e3eeea y tinta #173e32; acción cereza #a51b34. Oscuro #0c2b23/#123c30, texto #f0f7f1 y acción #ff9caf. Plata y látex son materiales de escena. Estados escritos además del color. | `:root`, `[data-theme=dark]`, `.notice`, `.set-illustration` |
| Movimiento | Tensión y asentamiento: pista que gira, estructura que registra, inflación, mesa diagonal, torsión escalonada de paletas, plano en perspectiva, display que se endereza, piezas que se asientan y foil suspendido. | `.floor`, `.rig`, `.balloons`, `.table-unit`, `.nav-backing`, `.working-plane`, `.foil-shine` |

El JSON adjunto documenta exactamente ocho ejes y selectores de evidencia. Todos los selectores de B se encontraron renderizados; los de movimiento tienen animación real. Se observaron nueve nombres de animación activos durante una carga expresiva, no solamente declaraciones CSS sin uso.

## Fuentes, sistema existente y bibliotecas reales

Fuentes leídas: SPEC.md SHA-256 `65b1e5ecc06f20d9`, PLAN.md `cc7e53f2abf3c23c`, PLAN.json `7a2c833a7e711508` y comportamiento compartido r9 `4113589a9342573e` (prefijos SHA-256). SP-3 cubre R9/R10/R11, T3.1–T3.8. Se leyeron los valores, tipos, límites, editor y creación existentes, además de los tokens de `t12` y `asesor`, sin editarlos.

| Token Pictures | Rol del kit | Propuesta claro / oscuro |
|---|---|---|
| `--fondo` | `--background` | #e3eeea / #0c2b23 |
| `--superficie` | `--card`, `--popover` | #f8fbf9 / #123c30 |
| `--superficie-2` | `--secondary`, `--muted`, `--accent` | #d1e5dc / #1a483a |
| `--texto` | foregrounds | #173e32 / #f0f7f1 |
| `--texto-suave` | `--muted-foreground` | #426355 / #bad3c5 |
| `--acento`, `--sobre-acento` | primary / primary foreground | #a51b34, blanco / #ff9caf, #32101b |
| `--borde` | `--border` | #789587 / #7fa591 |
| Borde de control propuesto | `--input` | #577568 / #89b29d |
| Foco | `--ring` | #a51b34 / #ff9caf |
| Roles semánticos existentes | success / warning / destructive | #145b43 / #714500 / #a51b34; oscuro #a1e1bd / #f5d397 / #ffb2be |

Importaciones efectivas: `shadcn:button default/outline/ghost/disabled` en `@/components/ui/button`; `shadcn:input default/invalid/disabled` en `@/components/ui/input`; `shadcn:skeleton loading` en `@/components/ui/skeleton`. `@/components/ui/dialog` aporta Root/Title/Description; `@animate-ui/react/primitives/base-ui/dialog` aporta Portal/Backdrop/Popup con transiciones del perfil, fondo inerte y contención de foco. `motion/react`, `@kit/motion` y `@kit/mockup` aportan Motion, perfiles, `mountMockup` y `useMockup`. La variante se transmite también a un atributo local para restilizar correctamente el Button real. No se emplearon snippets de sustitución ni se instalaron paquetes.

Las fuentes instaladas se importan desde `/usr/share/fonts/liberation/LiberationSerif-Italic.ttf` y `/usr/share/fonts/Adwaita/AdwaitaSans-Regular.ttf`; el builder las incrusta en el HTML. El CSS del TSX se incluye también como `<style data-direction="orbit">` tras el build, para que contrast.py mida los tokens propuestos y no únicamente los valores originales del kit. El bundle es autónomo, aproximadamente 2.5 MB, sin petición HTTP ni fuente externa.

## Comportamiento, vistas y alcance real

| Vista | Resultado y límites |
|---|---|
| Mesas | Ocho tipos existentes: rectangular, redonda, cuadrada, ovalada, cóctel, media luna, serpentina y U. La tarjeta añade con sus dimensiones de partida y abre el inspector. Rectangular: 2,40 × 0,90 × 0,75 m. Sin formulario previo. Se conserva la cantidad inicial existente de ocho sillas, limitada por colocación real. Cóctel parte sin mantel; los otros tipos con mantel al piso. Las piezas Imperial fijas permanecen en su catálogo; no se inventa otro tipo paramétrico. |
| Inspector | Tipo, largo/diámetro/lado/ancho total, fondo, alto y mantel; siete tipos de silla, cinco disposiciones, cantidad solicitada 0–40 y colocadas/capacidad. Fondo derivado desactivado en los tipos que lo calculan desde el ancho. Límites del repositorio; en rectangular largo 1–6 m, fondo 0,4–1,5 m, alto 0,4–1,1 m. Validación conserva la última medida válida. Selector de mesa cuando hay más de una y Deshacer del último cambio. |
| Backing | Exactamente una tarjeta para cada ID existente: panel_redondo, media_luna, arcos_chiara, pedestales, aro_metalico, aro_hexagonal y arco_metalico. Cada pulsación añade una instancia. Búsqueda por nombre ES/EN o ID y recuperación sin resultados. No cambia IDs, propietario de repositorio, búsqueda por nombre original, escenas guardadas, descubrimiento IA/foto ni Shopify `/catalogo`. Estas compatibilidades son obligaciones de implementación; no se simula su verificación. |
| Lista | Mesa por mesa con sus dimensiones, total real de sillas colocadas y cantidades de Backing agrupadas por ID; nunca alquileres ni precios. El contador de cabecera suma mesas, sillas colocadas y Backing. |
| GLB | Objetos visibles, posiciones, tamaños en metros y colores base; advierte posibles diferencias de iluminación y acabados. Vacío desactiva exportar, hay preparación, éxito y fallo recuperable. El diálogo conserva la escena original y explica qué se exportará. **Simulación explícita**: no se genera, descarga ni valida un GLB real. |

`normalizarMesa`, `LIMITES_MESA` y `repartirSillas` se empaquetan en lectura desde `asesor`. La conversión m→cm ocurre al consultar esos cálculos; los valores del prototipo no se escriben al proyecto. La capacidad no es un límite inventado: una prueba solicitando 40 sillas sobre una rectangular de 3,20 × 0,90 m colocó 14; la lista mostró las 22 reales al sumarlas a las ocho de la primera mesa. El estado Capacidad pide 40 en la primera mesa y usa el mismo cálculo.

El SVG se etiqueta como **Montaje ilustrativo**. Es una composición dibujada, no el visor 3D real: no acredita geometría, posición mundial, todas las instancias visibles, iluminación, movimiento/rotación/duplicación conjunta ni exportación. Los controles existentes de apariencia que no se dibujan aquí no se eliminan del editor de producción. T3.2 conserva esas operaciones y la paridad de herramientas; T3.4–T3.6 deben demostrar el GLB real y su importación en Blender. No se hizo llamada IA, instalación de Blender, servidor de producto, autenticación ni integración de producción.

## Estados, reflujo y accesibilidad

La barra conserva “Mockup” y los selectores nativos `view`, `state`, `scene`, `theme`, `motion`, con etiquetas Vista, Estado, Diálogo, Tema y Movimiento. `#language` cambia la copia de trabajo ES/EN. El mockup conserva el modelo en memoria entre vistas; recargar lo reinicia. Ningún servicio ni almacenamiento persistente participa.

| Estado nativo | Presentación y recuperación |
|---|---|
| Normal | Datos y acciones disponibles en las cinco vistas. |
| Cargando | Esqueletos con nombre accesible; acciones del plano suspendidas. |
| Vacío | Escenario vacío; inspector pide añadir mesa, lista explica que no hay objetos; exportación desactivada. Los catálogos siguen ofreciendo piezas. |
| Error | Mensaje visible, conservación del montaje y Reintentar. En GLB nombra el fallo de exportación. |
| Capacidad | En inspector y lista: 40 solicitadas en la primera mesa, colocadas y capacidad calculadas; aviso explícito. No cambia permanentemente el modelo. |
| Validación | En inspector: campo largo marcado, límites y conservación del valor válido. Los otros planos no tienen formulario dimensional. |
| Límite de objetos | No añade piezas; tarjetas y creación desactivadas con explicación para quitar objetos y reintentar. No representa una inserción parcial. |
| Exportando | En GLB: preparación, nombre de acción estable y acción desactivada. Sin significado adicional en los otros planos. |
| Éxito | Confirmación escrita; GLB identifica el ejemplo como tal. La simulación interactiva declara que no se creó archivo. |
| Sin permiso | Explicación de acceso y solicitud al administrador; el plano de trabajo queda indisponible. No acredita protección de API. |
| Sin conexión | Informa que se puede trabajar con la escena local y exportarla. No afirma guardado en servidor. |
| Diálogo Confirmar GLB | Disponible desde `scene` o botón; Cancelar/Escape lo cierran, devuelve foco al botón Exportar GLB; acción de simulación desactivada si no procede. |

≥1001 px: margen 40 px, escenario/plano en proporción 1,35:1, separación 40 px, catálogo a cuatro columnas. 761–1000 px: margen 24 px, separación 24 px, escenario de 380 px, catálogo a tres columnas. ≤760 px: margen 20 px, escenario de 340 px antes del plano, paletas conservadas sin barra fija, catálogo a dos columnas, pie apilado. La jerarquía se mantiene a 360 px y con etiquetas inglesas. Ninguna lectura exige arrastrar.

Objetivo WCAG 2.2 AA: texto ≥4,5:1, bordes y foco ≥3:1, foco de 3 px con separación de 4 px, nombres de campos y regiones, avisos `status`/`alert`, diálogo titulado y descripción, botones ≥44 px. No hay checkbox nativo que genere bordes distintos en oscuro. Los títulos de plano reciben foco tras navegación voluntaria. El audit automatizado no equivale a una declaración completa de conformidad WCAG.

Movimiento expresivo por defecto: curva `cubic-bezier(.22,1.35,.45,1)`, secuencia base 760 ms, controles 180 ms y desfases de paleta 70/140 ms. Natural 460/150 ms; sutil 240/110 ms. El perfil alimenta también las transiciones del diálogo. Foil con ciclo 7 s, sin cambiar opacidad de texto. `prefers-reduced-motion`, Quieto y `?still=1` quitan viajes y bucles mostrando el mismo contenido y acciones. Observador de intersección y visibilidad de documento suspenden la animación ambiental; no hay scroll obligatorio ni gesto imprescindible.

### Criterios observables para esta exploración

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| B-01 | 1001–1440 px | Normal | Mesas, Backing y Salida GLB están en tres posiciones distintas alrededor de la pista, al lado del plano operativo. |
| B-02 | 360–760 px | Normal | Escenario y plano se apilan sin desplazamiento horizontal, con 20 px exteriores. |
| B-03 | 360–1440 px | Normal | Añadir rectangular abre el inspector con 2,40 × 0,90 × 0,75 m. |
| B-04 | 360–1440 px | Capacidad | El aviso distingue solicitadas de colocadas y la lista usa las colocadas. |
| B-05 | 360–1440 px | Normal | Backing tiene exactamente siete tarjetas, cada una con nombre y acción Añadir. |
| B-06 | 360–1440 px | Error | Reintentar tiene borde y texto legibles en claro y oscuro y el montaje permanece visible. |
| B-07 | 360–1440 px | Vacío | Exportar GLB está desactivado y explica añadir objetos. |
| B-08 | 360–1440 px | Diálogo | Escape cierra la confirmación y devuelve foco al botón Exportar GLB. |
| B-09 | 360–1440 px | Normal / movimiento reducido | El foil no se balancea y no queda animación activa; herramientas y datos permanecen disponibles. |
| B-10 | 360 / 768 / 1280 px | Normal, EN | Las cinco vistas y ambos temas no provocan desbordamiento horizontal de la página. |

## Evidencia y resultados honestos

Builder ejecutado offline por ruta absoluta: `bitacora.py components mockup build taller-esenciales@v1.r9.dir-b.tsx --out taller-esenciales@v1.r9.dir-b.html`. Compilación real, 2212 archivos fuente procesados; sin instalación ni alternativa de respaldo. CSS del entry incluido también estáticamente para revisar los tokens efectivos.

`contrast.py`: **158 pares, claro y oscuro, todos pasan**.

`audit_mockup.py`: 240 renderizados de 240 combinaciones planificadas a 1280/390 px, 8935 mediciones de texto y 1301 paradas de foco. Se corrigieron el contraste de Reintentar, la alineación de avisos/insignia GLB y el relleno de tarjetas desactivadas. Resultado final real:

```text
RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems
```

Inspección visual en Chromium: miniatura elegida; Mesas claro en 1280; Mesas oscuro en 390; inspector claro en 390; exportación oscura en 1280. Capturas inspeccionadas en sesión, sin escribir imágenes fuera del alcance. Prueba adicional: **30 renderizados en inglés** (360/768/1280 × dos temas × cinco vistas), sin desbordamiento. Se comprobó el retorno del foco a Exportar GLB tras Escape, cero animaciones activas en modo reducido y nueve nombres de animación activos durante la entrada expresiva.

Prueba interactiva: crear rectangular → inspector → largo 3,20 m → 40 sillas solicitadas/14 colocadas → lista con 22 sillas totales → siete Backing → filtrar hexagonal → añadir aro → diálogo GLB → Escape → simulación explícita. Cero errores JavaScript y cero peticiones HTTP en esa prueba. La lista refleja cálculos del modelo; la escena sigue siendo ilustrativa.

`compare_directions.py A B C --json`, offline, ejecutado sobre las tres salidas r9: **B/A compatible para comparación**, similitud de geometría 0,006; **B/C compatible**, 0,024. Tipografía, navegación y movimiento distintos en ambos pares. Todos los selectores de B tienen evidencia. **Resultado global final: PASS** (`ok: true`, `evidence_ok: true`, sin evidencia ausente). La primera ejecución detectó `.chapter` ausente en A; una segunda ejecución sobre las salidas disponibles verificó que ya estaba corregido. Esta delegación no modificó A. Estos números documentan diferencia estructural, no una aprobación de gusto ni del producto.

## Impacto, preguntas y límites

Impacto si se elige: SP-3 `taller-esenciales@v1`, T3.1 copia futura; T3.2 creación/inspector/lista, T3.3 Backing y T3.4 exportación. T3.5/T3.6 mantienen su evidencia funcional independiente; T3.7 revisa el resultado renderizado y T3.8 audita. La composición, navegación y redistribución del contenido exigirían adaptación respecto al editor actual: cambio visual **incompatible si se adopta**, aprobación pendiente. No se redirigió ningún consumidor ni se escribió CHANGELOG canónico. La compatibilidad de artefactos de escena, IDs y GLB permanece en los contratos de implementación existentes.

Confirmado: creación directa sin formulario previo, ocho tipos existentes y límites, dimensiones rectangulares iniciales, lista sin alquileres, siete IDs Backing y GLB existente. No se introduce guardado, IA, nuevos formatos ni instalación de software en esta tarea.

P: ¿Debe mantenerse la confirmación antes de exportar GLB o el botón debe iniciar la exportación directamente? David decide antes de finalizar el contrato; esta exploración muestra la confirmación.
P: ¿Se aprueba la paleta verde/cereza y el par serif cursiva/Adwaita para el Taller, o debe ajustarse su relación con la dirección elegida de cuentas? David decide al elegir el conjunto visual.

PREOCUPACIONES: exploración sin aprobar; no hay GLB ni importación real en Blender, visor 3D exacto, autorización o validación de compatibilidad de escenas en este mockup. Ninguna de esas comprobaciones pendientes se informa como aprobada.
