---
contract: chat-a-3d
version: 1
status: draft
subplan: SP-12
direction: c
revision: r1
name: Escena en el mensaje
owner: David
date: 2026-10-29
---

# Escena en el mensaje — dirección C

## 1. Identidad y alcance

Exploración **draft**, sin aprobación. Este archivo es una nota de dirección para `chat-a-3d@v1`, no el contrato canónico ni una autorización de implementación. Fuente de comportamiento: `chat-a-3d@v1.r1.behavior.md`, R13 / SP-12. Contexto leído: SPEC, PLAN.md y bloque SP-12 de PLAN.json. No se modificaron planes, contratos compartidos ni repositorios.

La exploración completa está en `chat-a-3d@v1.r1.dir-c.html`, construida desde el TSX homónimo mediante el builder real offline. El inspector conserva Mockup y selectores nativos Vista/Estado/Diálogo/Tema/Movimiento. No se instaló nada ni se descargaron recursos. React, fuentes, CSS, JS, iconos y dibujo SVG están incluidos.

## 2. Enfoque y usuarios

La persona conserva el hilo de la conversación mientras compara decoraciones existentes. La modificación de `/asistente` consiste en insertar tarjetas de recomendación en el mensaje, con ampliación local de una sola escena, y proponer un ajuste del último pedido sin abandonar ese contexto. La necesidad se define en dos mensajes de ejemplo: Cumpleaños → tamaño/colores → blanco y negro, 2 m. En producción, el chat debe conseguirlo en dos o tres mensajes; el prototipo simula el intercambio y no interpreta lenguaje natural.

Todas las cuentas ven nombre, miniatura y cantidad. Sólo `decoraciones.explorar` permite la acción de apertura. La vista sin permiso omite el botón, no reserva un hueco y no muestra planes, candados, precios ni sugerencias comerciales en las recomendaciones. La elegibilidad procede de la capacidad, no de una comparación visual de nombres de rol.

## 3. Dos miniaturas y selección

Se dibujaron y renderizaron primero:

- `chat-a-3d@v1.r1.dir-c.html.candidate-1.html`: dos bandas con miniatura lateral y controles junto al nombre.
- `chat-a-3d@v1.r1.dir-c.html.candidate-2.html`: dos tarjetas verticales en columnas, con la vista previa arriba.

**Elegida para desarrollar: candidata 1.** Su miniatura lateral mantiene el nombre y el conteo cerca del intercambio y deja un lugar claro para expandir la escena debajo de su propia tarjeta. La candidata 2 concede más área inicial al dibujo y menos continuidad a los controles. La elección es interna a esta exploración; el propietario aún debe escoger una dirección entre las exploraciones del subplan. Las candidatas son bocetos de composición, no controles funcionales ni superficies auditadas.

| Eje | Expresión visible |
|---|---|
| concept | Edición en contexto: las recomendaciones forman parte del mensaje; ampliar una escena y ajustar la necesidad ocurre en el mismo lugar. |
| layout | Columna de conversación de 880px con tarjetas en bandas apiladas; miniatura de 168px junto a nombre y cantidad; expansión debajo de su propia tarjeta. Shell ancho compartido. |
| navigation | Navegación horizontal heredada; Ver escena/Ocultar escena abre una sola vista en el mensaje; Ajustar revela el campo local; Abrir en el Taller lleva al deep link autorizado. |
| typography | Geist y Geist Mono locales del producto: título 24px, nombres 18px/16px en móvil, cantidad 18px, cuerpo 15px y metadatos 12–13px. |
| density | Bandas cerradas compactas de 176px aprox. en escritorio; una sola escena expandida, sin panel lateral permanente. Insets 24px escritorio y 20px teléfono. |
| components | Button, Input, Skeleton y AlertDialog reales; enlaces nativos para abrir, disclosure de cuenta heredado y composición propia de tarjeta/edición en sitio. |
| colour | Tokens Pictures exactos de globals.css y los alias accesibles de hermanos; acento en apertura y envío, navegación neutra, visor con taller-visor. Dos temas sin paleta nueva. |
| motion | Asentamiento táctil .975→1.006→1 en 540ms con 65ms de secuencia; expansión vertical .94→1.012→1; presión .965, hover 1.025 y spring del perfil. Reducción inmediata y pausa de animación CSS en pestaña oculta. |

## 4. Superficie existente y sistema fijo

Se inspeccionaron en sólo lectura ambos repositorios y, específicamente, `src/app/globals.css`, `/asistente/page.tsx`, `VistaGuiada.tsx`, `Burbujas.tsx`, `Compositor.tsx`, `CabeceraApp.tsx`, `IdeasDelAsistente.tsx` y las fuentes de galería/motor. `/asistente` usa `VistaGuiada`; `asesor/ChatView.tsx` pertenece a otra superficie y no se traslada su identidad.

Se leyeron los tres contratos/HTML hermanos: cuentas-admin@v1, planes@v1 y proyectos@v1. La cabecera Pictures/Sempertex con anillo y punto, controles de idioma/cuenta, navegación horizontal neutra, footer y vocabulario de componentes proceden de esos hermanos. El código fuente `proyectos@v1.r12.dir-c.tsx` permite conservar su mapeo de tokens y shell. Las rutas Herramientas/Chat normal se componen con ese patrón; la disponibilidad final de cada ruta la gobierna SP-7. Este subplan no diseña la calculadora, el contador, la galería ni el guardado.

| Token Pictures | Rol kit / uso | Claro / oscuro |
|---|---|---|
| `--fondo` | background | #faf9fc / #0b0c10 |
| `--superficie` | card, popover | #ffffff / #16181f |
| `--superficie-suave` | miniatura neutra | #faf8fd / #1c1e26 |
| `--superficie-2` | secondary, muted, accent | #efe9f8 / #242733 |
| `--texto` | foreground | #1c1425 / #f4f5f7 |
| `--texto-suave` | muted-foreground | #6b6178 / #9aa1ad |
| `--texto-tenue` | input, borde de control accesible heredado | #766c85 / #8a91a0 |
| `--acento` / `--sobre-acento` | primary / primary-foreground | #6d3fe0 / #ffffff; oscuro #9479ff / #120b24 |
| `--acento-hover` | primary-hover | #5530b8 / #a58dff |
| `--borde` / `--borde-suave` | tarjeta / divisor | #e3daef / #efe9f8; oscuro #383c48 / #2a2d38 |
| `--error` | destructive | #b23a45 / #ff979f |
| `--taller-visor` | vista de escena desplegada | #ebe7f1 / #1a1722 |

Geist y Geist Mono se incluyen desde las mismas WOFF2 locales del hermano elegido. Radios heredados: panel 32px, inset 24px, campo 18px y controles pill. No hay paleta ni fuentes nuevas. El SVG es un esquema neutral que usa roles existentes; su geometría y cantidad de círculos no constituyen un render fiel ni el cálculo del motor.

| Componente y estados | Import / procedencia real |
|---|---|
| `shadcn:button default/outline normal/hover/focus/pressed/disabled` | `@/components/ui/button`, Base UI |
| `shadcn:input text empty/filled/focus/disabled` | `@/components/ui/input` |
| `shadcn:skeleton recommendation loading` | `@/components/ui/skeleton` |
| `shadcn:alert-dialog restart open/closed` | `@/components/ui/alert-dialog`, implementación Animate UI/Base UI instalada |
| `custom:recommendation-band collapsed/expanded` | article, h3, miniatura y botones semánticos; no se atribuye a otra librería |
| `custom:open-decoration link permitted/opening` | enlace nativo con destino y nombre accesible específico |
| `custom:account-menu closed/open` | details/summary compartido, cierre exterior/Escape |
| `custom:inline-adjust closed/editing/empty/ready` | Input real y acciones Enviar mensaje/Cancelar |
| `kit:mockup native` | mountMockup/useMockup de `@kit/mockup` |
| `kit:motion expressive/natural/subtle/reduced` | `useMotionProfile` de `@kit/motion`, `motion.div` de motion/react |

## 5. Navegación e interacción

La conversación continúa en `/asistente`. Ver escena/Ocultar escena expande en sitio; una segunda ampliación cierra la anterior. El foco permanece en el control y `aria-expanded`/`aria-controls` reflejan el estado. Ajustar muestra un campo bajo el último pedido, lo enfoca y ofrece Enviar mensaje/Cancelar; el texto vacío desactiva el envío. Esta edición en contexto es una propuesta de dirección pendiente de la decisión Q1.

Abrir en el Taller es un enlace real `/3d?decoracion=<id codificado>`; cada nombre accesible incluye el nombre de la decoración. En el mockup se intercepta para mostrar una transición local de destino como proyecto nuevo **Sin guardar**. El contenedor del destino y la escena reutilizan proyectos@v1; guardado/edición reales quedan en ese contrato. No se modifica una escena previa ni se afirma que se haya guardado. El destino de fixture usa los IDs de biblioteca `asistente:...`; el catálogo futuro conserva autoridad sobre el ID definitivo.

Empezar de nuevo conserva una confirmación con AlertDialog real, que también puede abrirse con Diálogo. Cancelar retorna foco a su disparador; confirmar vuelve al inicio y al campo de mensaje. Los controles existentes de foto/voz, cuenta y rutas ajenas al alcance devuelven feedback explícito Mockup en vez de simular servicios externos.

## 6. Flujos

1. Inicio: saludo existente, pregunta de celebración y compositor. Primer envío muestra la pregunta de tamaño aproximado/colores; segundo envío presenta las recomendaciones. Son fixtures locales, no una integración IA.
2. Recomendación: dos tarjetas con ID, nombre de galería, vista y cantidad. Abrir una vista previa no navega ni altera la selección de otra cuenta.
3. Ajuste propuesto: Ajustar → edición local → Enviar mensaje → las tarjetas de fixture permanecen y el feedback anuncia la simulación. Producción debe recalcular las recomendaciones con la herramienta; no reutilizar resultados por simple edición de texto.
4. Cuenta con capacidad: Abrir en el Taller → nuevo proyecto sin guardar. Volver al chat recupera las recomendaciones de ejemplo.
5. Cuenta sin capacidad: mismas tarjetas y ampliación, sin enlace de apertura ni copy de plan.
6. Error/sin coincidencias: conservar conversación; reintentar el resultado fallido o continuar escribiendo. No inventar nombre o conteo para llenar tarjetas vacías.

## 7. Vistas, datos y límites

Vista `explorer`: capacidad `decoraciones.explorar` presente. Vista `viewer`: capacidad ausente. Son selectores de fixture, no controles del producto. Cada vista comparte shell, idioma, necesidad y recomendaciones. El estado opened de explorer muestra sólo la recepción del nuevo proyecto; en viewer conserva el resultado sin ofrecer acceso Taller.

Datos de galería reales leídos de `src/lib/globos3d/ideas-asistente/escenas.json`:

| ID de biblioteca local | Nombre ES | Total del motor |
|---|---|---|
| asistente:deco-real-01-305 | Arco de entrada en blanco y negro | 112 |
| asistente:deco-real-14-images-29 | Arco de entrada blanco y negro | 112 |

Se ejecutó `armarEscena(escena).materiales` localmente mediante `node_modules/.bin/tsx --conditions=react-server -e ...`: cada escena devolvió R-12/080=56 y R-12/005=56. La UI usa una variable `count` por tarjeta para chat y destino. No hay estimación del modelo. La pareja es dato de ejemplo, no una validación de ranking ni una afirmación de diversidad visual: las dos escenas locales comparten geometría.

Los nombres ES vienen literalmente de la galería; los EN son traducciones draft para probar ajuste de texto, no un segundo catálogo aprobado. El texto libre del usuario permanece en su idioma original cuando se cambia de idioma. Las imágenes de producción deben venir de la galería; el HTML incluye esquemas inline explícitamente marcados Mockup para no descargar assets ni fingir miniaturas definitivas.

## 8. Estados alcanzables

| Estado nativo | Contenido y recuperación |
|---|---|
| recommendations | Dos recomendaciones completas y ampliables; apertura condicionada a capacidad. |
| start | Saludo/pregunta existente y campo vacío; enviar desactivado sin texto. |
| clarify | Primer pedido y pregunta de tamaño aproximado/colores; compositor disponible. |
| loading | Dos skeletons y Estoy pensando…; se puede escribir y detener la respuesta. |
| empty | Sin coincidencias y siguiente paso por conversación; no tarjetas ficticias. |
| error | No se pudieron cargar las decoraciones; conversación conservada y Reintentar. |
| partial | Aviso de que no se pudieron cargar todas; una tarjeta válida y Reintentar. No representa un resultado completo de dos o tres recomendaciones. |
| preview-error | Primera miniatura sustituida por aviso accesible; nombre y cantidad conocidos se conservan, con recuperación. |
| opening | Enlaces Abriendo… con aria-disabled y controlador que impide apertura repetida; sin número/porcentaje de progreso ficticio. |
| unavailable | Decoración no disponible, conversación conservada y Reintentar. |
| opened | En explorer: recepción Taller como nuevo proyecto sin guardar. En viewer: mantiene recomendaciones sin acceso. |
| scene=restart | Confirmación heredada de reinicio, Cancelar y Empezar de nuevo. |

Edición y expansión se alcanzan con sus controles visibles; diálogos con el selector nativo scene. No se diseña otro sistema de sesiones, cola offline o acceso al chat: lo gobiernan los hermanos y la implementación existente. Offline de la recomendación comparte el fallo recuperable y conserva conversación; no se simula sincronización. Permiso de apertura ausente no es un error. Datos desconocidos/obsoletos no se convierten en cantidades válidas; eliminar o recuperar la tarjeta debe seguir el estado de disponibilidad recibido.

## 9. Responsive

- 1024px o más: shell con insets de 40px, conversación centrada hasta 880px, bandas con miniatura de 168px, nombre/conteo y acciones al lado. El header/footer mantienen el ancho del shell heredado.
- 768–1023px: insets de 24px; mismo orden y bandas, sin overflow. Destino Taller pasa el inspector debajo.
- 360–767px: insets de 20px; header y navegación refluyen, sin scroll horizontal. Miniatura de 100px junto a nombre de 16px; acciones debajo a todo el ancho disponible. La apertura se estira si hace falta. Compositor conserva foto/voz/envío y los reordena en dos filas. Vista ampliada queda bajo su propia tarjeta.

Verificado visualmente a 1280 y 390px en ambos temas; comprobación adicional de reflow EN a 768px. No se añaden carruseles con scroll lateral ni gestos obligatorios.

## 10. Accesibilidad y movimiento

Objetivo WCAG 2.2 AA: controles de 44px, foco de 3px en acento con offset de 4px, etiquetas específicas, encabezados ordenados, mensajes de error con alert y feedback con status, enlaces reales y botones teclado. Diálogo Base UI limita foco; Escape/cancelación y retorno de foco conservan su origen. La ampliación usa aria-expanded y aria-controls; las imágenes tienen descripción y el SVG interior es decorativo. No se afirma conformidad integral sólo por este diseño.

Movimiento propio: `card-seat` comprime .975, sobrepasa 1.006 y asienta a 1; 540ms expresivo, 320ms natural, 160ms sutil; offsets 65/30/12ms. `preview-seat` expande .94→1.012→1 sobre eje Y; `field-seat` asienta el editor .98→1. Controles 170/140/100ms, hover 1.025, presión .965; `.open-control` usa el spring del perfil. La carga usa un punto discreto junto al texto. Todo permanece legible durante la entrada. Animaciones finitas no se repiten al hacer scroll; CSS se pausa al ocultar la pestaña.

OS reduced motion, selector Quieto y `?still=1` muestran el estado final sin desplazamiento ni pulsación continua; se comprobó ausencia de animaciones activas. No existen animaciones pesadas/integraciones WebGL que suspender fuera de pantalla.

## 11. Aceptación visual y evidencia

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| C-AC-01 | 1280 / 390px | recommendations | Shell Pictures/Sempertex, idioma, cuenta, navegación horizontal y footer conservan tokens/fuentes hermanos. |
| C-AC-02 | 360–1520px | recommendations | Cada tarjeta muestra miniatura, nombre y cantidad; no se calcula un conteo con texto del modelo. |
| C-AC-03 | 1280 / 390px | viewer | Hay las mismas dos tarjetas, sin apertura ni mención de planes en la conversación. |
| C-AC-04 | 1280 / 390px | explorer | Abrir en el Taller tiene href /3d?decoracion=<id> y nombre accesible que identifica la decoración. |
| C-AC-05 | 1280 / 390px | expanded | Sólo una escena ampliada aparece debajo de su tarjeta, sin panel nuevo ni navegación. |
| C-AC-06 | 1280 / 390px | editing | Ajustar revela el Input local y Enviar mensaje/Cancelar; vacío desactiva enviar. |
| C-AC-07 | 1280 / 390px | loading | Skeletons sustituyen las tarjetas; el campo sigue disponible y hay Detener respuesta. |
| C-AC-08 | 1280 / 390px | empty/error | La conversación permanece, sin tarjetas de relleno; recuperación visible donde corresponde. |
| C-AC-09 | 1280 / 390px | preview-error | La miniatura fallida no sigue representándose como disponible; nombre/conteo conocidos permanecen. |
| C-AC-10 | 1280 / 390px | opened | Un nuevo proyecto indica Sin guardar y la decoración elegida; no indica guardado ni modifica un proyecto anterior. |
| C-AC-11 | 390 / 768 / 1280px | EN light/dark | No hay scroll horizontal; nombres y controles se reacomodan sin truncar el texto de acción. |
| C-AC-12 | todos | reduced/still | Se ven los mismos contenidos y funciones sin animaciones activas. |
| C-AC-13 | 1280 / 390px | restart | Cancelar preserva la conversación; confirmar vuelve a inicio; foco se devuelve al origen adecuado. |

Builder real offline: **PASS**, 632KB, 2132 source files. `contrast.py`: **158 pairs checked in light and dark, all pass**. Playwright audit final: **96 renders / 96 combinations planned**, 2140 medidas de texto y 442 paradas de foco.

**RESULT: FAIL — alignment 4**

Los cuatro hallazgos corresponden exclusivamente al H1, Empezar de nuevo y las dos leyendas del footer, anclados al shell heredado (x=40 / extremo derecho) mientras la conversación mide x=200–1080 en 1280px. El heurístico global de columna centrada en `audit_probes.js` líneas 154–164 trata esos bloques del shell como contenido desalineado de la conversación. Inspección visual: son los mismos ejes del header/footer de proyectos@v1; se preservan por el mandato de no rediseñar shell. Esto es una interpretación documentada del Designer, no una excepción automática ni un PASS. No hay hallazgos finales de contraste, foco, bordes, padding, overflow, motion, network ni layout shift en esta ejecución. El borde propio del Input del compositor se corrigió tras el primer audit (que marcaba 1:1). No se alteró el auditor ni se ocultaron elementos para aprobarlo.

Capturas examinadas en memoria, sin crear archivos fuera del alcance: candidatas a 1280px; normal a 1280 claro/390 oscuro; expansión a 1280 oscuro en EN y edición a 390 claro en EN. Comprobaciones funcionales finales: PASS para tarjetas/conteos, ampliación única, ajuste local, enlaces por capacidad, proyecto nuevo sin guardar, omisión de copy de plan, EN a 390/768/1280 en ambos temas, miniatura fallida, cancelación de reinicio, ausencia de animación activa tras asentar reducción, ausencia de red/errores de consola y presencia real de card-seat en modo expresivo. Se usaron selectores de formulario específicos para desambiguar dos controles Enviar mensaje y se esperó al cierre real del diálogo. No prueban API, IA, ranking ni persistencia.

## 12. Preguntas, supuestos e impacto

**Q1 — David:** ¿Confirmamos Ajustar como edición en contexto del último pedido con nuevo envío a recomendaciones, o la única corrección debe hacerse con otro mensaje en el compositor? La propuesta visual está implementada sólo como fixture y requiere decidir semántica de historial antes de finalizar.

**Q2 — David / catálogo SP-7 / textos SP-9:** ¿El índice de galería entregará directamente el nombre ES/EN y el ID final para el enlace? Los nombres ES y las cantidades vienen de fuentes locales reales; los nombres EN son traducción draft y los IDs `asistente:` corresponden a la biblioteca actual, pendientes de confirmar contra galeria-index@1.

**Q3 — David:** ¿Aceptamos que el título y el footer conserven el ancho heredado del shell mientras el chat queda en una columna de 880px? El audit informa cuatro desalineaciones globales por esa composición; se necesita resolver su criterio antes de declarar aceptación visual completa.

Supuestos explícitos: el saludo y los controles foto/voz existentes se preservan; el resto de rutas depende de capacidades según SP-7; un resultado parcial de infraestructura puede mostrar una tarjeta válida con recuperación, pero no reemplaza el objetivo de dos o tres. El mockup usa una pareja existente de geometría igual y no valida su ranking. El guardado real, proyectos y el resultado de abrir una decoración no crean una segunda especificación de SP-4.

Impacto: sólo SP-12, R13, vistas `/asistente` y handoff `/3d?decoracion=<id>`. Futuros consumidores: T12.1 copia del contrato aprobado, T12.3 tarjetas y T12.5 revisión visual. Compatibilidad: **undetermined**, primera exploración sin contrato previo; la edición en contexto se propone, no se impone. No se cambian los contratos hermanos, changelog compartido, PLAN ni repositorios. El contrato canónico queda pendiente del proceso de selección/finalización y de la aprobación independiente del propietario.
