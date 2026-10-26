---
id: REQ-001
status: clarifying
created: 2026-10-22
track: deep
---
# REQ-001 — Paquete de kit de interfaz personal con catálogo público

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

Inventario de fuentes (documento v4 del propietario, en español, autoritativo para la lista de componentes, las coincidencias y las reglas por fuente):
[SOURCE-INVENTORY.md](SOURCE-INVENTORY.md). Los números de sección `§N` que aparecen abajo hacen referencia a este documento.

Redirigido por el propietario el 2026-10-26 (D-003): un paquete npm más un catálogo público que lo consume, en reemplazo del registro de shadcn, el inicio de sesión del propietario, los tokens bearer y Netlify de D-001.

## Problema y objetivo
David crea varios proyectos React (maros, pictures, dav033-demos, proposal-studio, lotm, trainingapp…) y cada uno combina shadcn/ui, Animate UI y React Bits de forma improvisada, por lo que cada proyecto tiene una apariencia y un comportamiento diferentes, y los agentes vuelven a elegir componentes cada vez. Objetivo: **un paquete de componentes React reutilizable para uso personal** («david-ui», publicado como `@dav033/david-ui`) con una identidad visual única y un alto nivel de interactividad y retroalimentación, además de un **catálogo web público** que solo muestre los componentes con demos funcionales y que esté construido con el mismo paquete. No tiene fines comerciales.

**Criterios de éxito:**
- Con un token `read:packages` en `.npmrc`, `npm install @dav033/david-ui` en una aplicación Next.js 16 + Tailwind 4 recién creada, al importar cualquier entrada `implemented`/`validated` y la hoja de estilos del tema, compila sin modificaciones y se muestra con los estilos aplicados.
- Las 93 entradas candidatas del inventario (42 de shadcn + 7 capacidades de Animate UI + 12 de Bencho + 32 de React Bits Free) y las 22 mejoras de Animate UI terminan en un estado verificado y registrado (ninguna queda como `pending`).
- La aplicación del catálogo está construida al 100 % con el paquete (verificado mediante un control automatizado) y es de acceso público en Vercel, sin inicio de sesión.
- `npm run verify` y `npm run test:e2e` pasan desde la raíz del repositorio.

## Usuarios / actores / partes interesadas
- **Propietario (David):** instala el paquete en sus proyectos, explora el catálogo y aprueba las entradas.
- **Agentes de programación (Claude Code, Codex):** descubren componentes mediante el índice para agentes (en el paquete y en el catálogo) e instalan el paquete.
- **Visitantes del catálogo:** cualquier persona que tenga la URL; el catálogo es de solo lectura y no tiene cuentas.

## Alcance (incluido)

### US-1 (P1, Must) — Base del paquete
Como propietario, quiero un monorepositorio público cuyo paquete incluya tokens, tema, perfiles de movimiento y herramientas, para que todos los componentes compartan una misma identidad.
**Criterios de aceptación:**
- Dado el repositorio, cuando se ejecuta `npm run verify` desde la raíz, entonces pasan lint, la verificación de tipos, las pruebas unitarias, la comprobación exclusiva del kit, la comprobación del catálogo, la compilación del paquete y la compilación de producción del catálogo.
- Dado cualquier componente, cuando el tema cambia entre claro y oscuro o el perfil de movimiento cambia entre sutil, natural y expresivo, entonces sus colores, radios, sombras y tiempos de movimiento provienen de los tokens compartidos.

### US-2 (P1, Must) — Manifiesto del catálogo y registro de licencias
Como propietario, quiero registrar cada entrada del inventario con sus metadatos para que nada se cuente dos veces ni se olvide.
**Criterios de aceptación:**
- Dado el manifiesto, cuando se ejecuta la comprobación del catálogo, entre las entradas con `origin: inventory` encuentra exactamente 42 shadcn (30 P1 + 12 P2), 7 capacidades de Animate UI, 12 Bencho (6 de capacidad nueva + 6 variantes) y 32 React Bits (9 de texto + 12 de UI + 6 efectos + 5 fondos) = 93, además de 22 mejoras de Animate UI vinculadas a entradas shadcn existentes; falla ante cualquier otro total, un id duplicado o una mejora sin una entrada base. Las entradas con `origin: catalog-driven` u `origin: own` (R4) se enumeran por separado y nunca se cuentan entre las 93.
- Dada una entrada con estado `implemented` o `validated`, tiene URL de origen, versión/commit de origen, fecha de incorporación, licencia, resultado de compatibilidad de dependencias y una demostración; en cambio, una entrada de desarrollo independiente (`own (inspired by <source>)`) registra `upstream: n/a`, la URL y la fecha consultadas, además de una nota de revisión de licencia; una entrada `blocked`/`discarded` tiene una justificación por escrito.

### Semántica de los estados
- `pending` — registrado, aún no se ha intentado (permitido solo antes de que finalice el hito de la entrada).
- `implemented` — existen el código en el paquete, la demo y las pruebas unitarias; el paquete compila y lo exporta; aún falla alguna comprobación de R6 y el motivo está escrito en la entrada.
- `validated` — pasan todas las comprobaciones de R6. Este es el estado objetivo de cada entrada.
- `blocked` — no se puede entregar por ahora (licencia, familia de primitivas, conflicto de dependencias); se registran el motivo y la condición para desbloquearla.
- `discarded` — se decidió no entregar (redundante según §10.2/§11.6); se registra el motivo.
- La aprobación de producción del propietario (§10.4 «aprobarlos para producción») es una marca independiente del manifiesto, `ownerApproved` (por defecto, `false`), que establece el propietario después de la entrega; nunca bloquea este requisito.

### US-3 (P1, Must) — Compilar, publicar y usar el paquete
Como propietario, quiero que el paquete tenga versiones y se publique en GitHub Packages, para que cualquiera de mis proyectos pueda instalarlo como una dependencia npm normal.
**Criterios de aceptación:**
- Dado un changeset combinado en `main`, cuando se ejecuta el flujo de publicación, entonces GitHub Actions publica una nueva versión semver de `@dav033/david-ui` en GitHub Packages.
- Dada una aplicación Next.js 16 + Tailwind 4 recién creada con un token `read:packages`, cuando instala la versión publicada e importa `@dav033/david-ui/theme.css` y un componente, entonces `next build` pasa y el componente se muestra con los tokens del kit (`scripts/consume-smoke.mjs`).

### US-4 (P1, Must) — 30 componentes P1 de shadcn con sus mejoras de Animate UI
Como propietario, quiero que los componentes esenciales (§3.1–3.6) funcionen sobre Base UI con sus mejoras de movimiento, para que los nuevos proyectos puedan partir del paquete.
**Criterios de aceptación:**
- Dado que el hito P1 está completo, cuando se ejecuta `npm run catalog:check`, entonces las 30 entradas P1 están en estado `validated`, `implemented`, `blocked` o `discarded` (con el motivo), y las 15 mejoras relacionadas con P1 tienen un resultado (`compatible`, `manual`, `blocked`, `discarded`); las pruebas de navegador de P1 pasan para cada entrada P1 `validated`.

### US-5 (P1, Must) — Catálogo público construido con el paquete
Como propietario, quiero un catálogo web público con filtros, búsqueda, demos en vivo, estados, tema claro/oscuro, vista previa adaptable del tamaño de pantalla, selector de perfil de movimiento y fragmentos de instalación y uso, construido únicamente con el paquete.
**Criterios de aceptación:**
- Dado cualquier visitante, cuando explora el catálogo sin iniciar sesión, entonces funciona cada capacidad de R9 (`e2e/catalog-browse.spec.ts`, `e2e/catalog-entry.spec.ts`) y pasa `npm run check:kit-only`.
- Dada la URL de producción en Vercel, una comprobación de solo lectura confirma que la página de inicio, una página de entrada, `/llms.txt` e `/index.json` responden con 200.

### US-6 (P2, Must) — 12 componentes P2 de shadcn, mejoras restantes y 7 capacidades de Animate UI (§3.7, §4, §5)
**Criterios de aceptación:**
- Dado que el hito está completo, las 12 entradas P2 y las 7 capacidades tienen un estado final (no `pending`), las 22 mejoras tienen un resultado, cada capacidad registra su forma de exposición (componente, hook o variante), un resumen de la API y su ubicación en el catálogo (§9); aparecen en el catálogo y pasan las pruebas de navegador para las entradas `validated`.

### US-7 (P2, Must) — 12 entradas de Bencho UI (§10), con implementación independiente cuando la licencia prohíba copiar
**Criterios de aceptación:**
- Dado que el hito está completo, las 12 entradas de Bencho tienen un estado final y un origen según R10, usan los nombres de §10.3, cumplen todas las reglas aplicables de R12, aparecen en el catálogo y pasan las pruebas de navegador (incluidas las alternativas de teclado y botón, y los conflictos de desplazamiento emulados en móviles).

### US-8 (P2, Must) — 32 entradas de React Bits Free (§11)
**Criterios de aceptación:**
- Dado que el hito está completo, las 32 entradas tienen un estado final al que se llega mediante la ruta elegida en su subplan (reimplementación independiente o exclusión, R10), se muestran sin advertencias de hidratación, respetan la reducción de movimiento, los fondos cumplen R13 y ningún archivo del repositorio contiene código de React Bits copiado.

### US-9 (P2, Must) — Integración con agentes y aceptación final
Como propietario, quiero que los agentes puedan descubrir e instalar los componentes del kit.
**Criterios de aceptación:**
- Dado el paquete publicado, este incluye `AGENTS.md` y `llms.txt` generados a partir del manifiesto, y el catálogo sirve el mismo índice en `/llms.txt` e `/index.json`.
- Dada una aplicación consumidora recién creada, cuando `scripts/acceptance.mjs` instala la versión más reciente, se importan todas las entradas `validated` y la aplicación compila.

## Fuera de alcance
- Migrar los proyectos existentes (maros, pictures, dav033-demos…) al paquete — serán requisitos posteriores.
- Publicar en el registro público de npm; cualquier uso o venta comercial.
- Inicio de sesión, cuentas, analítica o cualquier función de escritura en el catálogo.
- React Bits Pro o cualquier componente de pago; las brechas reales (Comparison Slider, Device, Page Flip, AI Blob con estados, §11.5) se documentan, no se implementan.
- Editores especializados (similares a Notion, editores de grafos) (§7).
- Servicios de backend para los componentes de interfaz (almacenamiento real de archivos para Upload Dropzone, carga de audio para Voice Note): solo interfaz y callbacks.
- Componentes de shadcn enumerados en §3.8, a menos que la aplicación del catálogo los necesite (R4).
- React Bits `Count Up`, `Counter` y `Dock` (§11.6.1–2): no seleccionados.
- Las composiciones propias de §11.5 «Modal Cards» y «Hover Preview»: para más adelante; aparecen en la página de brechas del catálogo junto con las brechas reales.

## Requisitos
- R1. El kit deberá estar alojado en un nuevo repositorio **público** de GitHub `dav033/david-ui` (local `~/dev/david-ui`), que permanecerá
  público. Es un monorepo con npm workspaces: `packages/ui` es el paquete `@dav033/david-ui`, `apps/catalog` es el catálogo de Next.js,
  que depende del paquete mediante el workspace (siempre usa la fuente actual, sin un ciclo de publicación e instalación).
- R2. El kit deberá usar Base UI como su única familia de primitivas; cuando Animate UI no tenga una variante de Base UI, la
  mejora deberá integrarse manualmente en el componente de Base UI (resultado `manual`) o registrarse como `blocked` con un motivo.
- R3. Cada componente deberá leer los colores, la tipografía, el espaciado, los radios y las sombras de tokens CSS compartidos; los controles
  funcionales (shadcn, Animate UI, Bencho) también deberán tomar los tiempos de movimiento del perfil activo; los efectos gráficos de React Bits
  tomarán de los tokens los matices, tamaños y fuentes, pero conservarán su propia física (§11.6.8). El tema predeterminado deberá ser
  Catppuccin Latte (claro) / Mocha (oscuro), con acento mauve, y los proyectos consumidores podrán reemplazarlo sobrescribiendo los tokens.
- R4. La aplicación del catálogo deberá construirse únicamente con componentes del paquete: cuando necesite una pieza de UI que el paquete no tenga,
  quien implemente deberá agregarla al paquete —primero desde shadcn/ui (registrada como una adición impulsada por el catálogo) y, solo si no
  existe un componente de shadcn, como componente propio con movimiento— y usarla desde allí en el mismo cambio; una
  comprobación automatizada (`npm run check:kit-only`) deberá fallar cuando `apps/catalog` importe primitivas de UI o bibliotecas de animación directamente, o
  renderice elementos HTML interactivos sin abstraer (`button`, `input`, `select`, `textarea`, `dialog`, `a` con estilos de botón).
- R5. El manifiesto del catálogo deberá registrar cada entrada con id (en kebab-case derivado del nombre; para Bencho, nombres de §10.3, p. ej.,
  `seek` → `expanding-search`, `liq-create` → `create-menu`, `picker` → `picker-wheel`, `dock` → `magnifying-dock`),
  name, source, origin (`inventory`, `catalog-driven`, `own`), category, priority (P1/P2: shadcn según la lista; Alta → P1,
  Media → P2 para §5 y §11; Bencho P2) más la prioridad original sin cambios, type (`base` = shadcn, `capability` = Animate UI
  §5, `new-capability` / `variant` = Bencho §10.1, `presentation` = React Bits), forma de exposición (component, hook,
  variant, utility), ruta de importación, estados aplicables, estado (`pending`, `implemented`, `validated`, `blocked`,
  `discarded`), URL y versión/commit del código fuente, licencia, dependencias, resumen de la API pública, resultados de accesibilidad y de movimiento reducido,
  y ruta de la demostración; las 22 mejoras deberán vincularse a su entrada base con un resultado de prueba
  (`compatible`, `manual`, `blocked`, `discarded`) y nunca contarse como entradas.
- R6. Cuando una entrada se marque como `validated`, deberá tener una demostración activa en el catálogo con todos los estados de `applicableStates`
  (hover, focus-visible, pressed, disabled, loading, success, error), operación con teclado cuando sea interactiva, ninguna infracción de axe,
  respeto por `prefers-reduced-motion`, ninguna advertencia de hidratación en SSR, pruebas unitarias de su comportamiento (para efectos de texto y fondos: pruebas de renderizado, props y movimiento reducido/alternativa), y una exportación del paquete compilado que una aplicación nueva pueda importar y compilar.
- R7. Cada control interactivo deberá admitir el uso con teclado y con pantalla táctil; hover, arrastre o proximidad del cursor nunca deberán ser
  la única forma de operarlo (§11.6.7, §10.2).
- R8. El kit deberá exponer tres perfiles de movimiento (sutil, natural predeterminado, expresivo) mediante un proveedor; las animaciones
  deberán priorizar `transform`/`opacity`, poder interrumpirse y reducirse a instantáneas o solo opacidad cuando se active el movimiento reducido.
- R9. El catálogo deberá ofrecer: navegación y filtrado por fuente, categoría, prioridad, estado y tipo; búsqueda mediante paleta de comandos;
  una página por entrada con demostración activa, galería de estados, tabla de props/API, fragmento de importación/uso, origen/licencia/versión,
  alternancia de tema claro/oscuro, vista previa del viewport (móvil/tableta/escritorio) y selector de perfil de movimiento; una página de brechas que enumere las
  brechas documentadas (§11.5) y cada entrada `blocked`/`discarded` con su motivo. Cada hito de una familia de componentes deberá agregar
  sus entradas al catálogo en ese mismo hito.
- R10. Dado que el repositorio y la fuente del paquete son públicos, el código solo deberá copiarse de una fuente cuando su
  licencia permita redistribuirlo en un paquete público; la licencia deberá registrarse en el registro de licencias antes de copiarlo. De lo contrario (Bencho si no está claro, React Bits Free, cuya Commons Clause prohíbe redistribuir los componentes «por sí solos,
  en un paquete o como una versión portada»), la entrada se volverá a implementar desde cero (comportamiento basado en la descripción/demostración pública,
  sin copiar código, origen `own (inspired by <source>)`) o se excluirá con un motivo por escrito; la ruta de React Bits se decidirá
  cuando su subplan esté en curso. Los archivos copiados deberán conservar el aviso de licencia del proyecto original en un comentario de encabezado (verificado por
  `catalog:check`). Las actualizaciones del código original serán deliberadas: el manifiesto registrará la versión original y la fecha de incorporación, y cada actualización volverá a comparar el código original con la adaptación local (procedimiento en el `AGENTS.md` del repositorio).
- R11. Las notificaciones deberán tener exactamente un motor (Sonner, salvo que el análisis de compatibilidad determine otra cosa, registrada en
  DECISIONS); las animaciones de Animate UI y Bencho Toast Stack serán presentaciones sobre ese motor (§10.2.1).
- R12. Las entradas que se superpongan deberán conservar un único modelo de valores, con cada regla cubierta por una prueba unitaria o e2e:
  `RollingNumberInput` es un campo editable y `CountingNumber` una visualización pasiva, con API distintas; `PickerWheel`
  emite el mismo contrato de valor que `Select`; `SloshSlider` comparte `value`/`onValueChange`, min/max/step y el comportamiento
  de teclado con `Slider`; `Checklist` usa el modelo booleano de `Checkbox`; las variantes de tarjeta componen `Card`; `CreateMenu` y `ExpandingSearch` conservan la gestión del foco y la operación con teclado; `SlideToConfirm` solo emite una intención de confirmación (nunca
  reemplaza la validación del servidor) y ofrece una alternativa con botón/teclado; `MagnifyingDock` funciona con foco y pantalla táctil.
- R13. Los fondos WebGL/canvas y los efectos pesados deberán cargarse de forma diferida, pausarse cuando estén fuera de pantalla o la pestaña esté oculta, y
  mostrar una alternativa CSS estática cuando WebGL no esté disponible o se active el movimiento reducido. Con emulación móvil de Playwright
  (perfil Pixel 7, limitación de CPU de 4×), cada fondo deberá mantener una mediana ≥ 30 FPS durante 5 s; de lo contrario, se publicará
  con la alternativa estática como opción predeterminada para móviles y se registrará la medición.
- R14. El catálogo deberá ser público y de solo lectura: sin inicio de sesión, sin cuentas, sin endpoints de escritura.
- R15. El paquete deberá incluir un índice para agentes (`AGENTS.md` y `llms.txt`) generado a partir del manifiesto, que enumere cada
  entrada con sus variantes, origen, ruta de importación, versión, dependencias, licencia y estado de QA, además de una guía breve de consumo y tematización; el catálogo deberá servir el mismo índice en `/llms.txt` y `/index.json`.
- R16. El catálogo deberá desplegarse en Vercel desde el repositorio de GitHub, con la raíz del proyecto en `apps/catalog`.
- R17. Las versiones deberán gestionarse con Changesets; cuando un changeset se integre a `main`, un flujo de trabajo de GitHub Actions deberá
  compilar y publicar el paquete en GitHub Packages usando el `GITHUB_TOKEN` del flujo de trabajo (`packages: write`).
- R18. El paquete deberá ser una biblioteca de React independiente del framework: `react`/`react-dom` 19 como dependencias peer, sin dependencia de
  Next.js, ESM compilado con declaraciones de tipos, exportaciones de subruta por componente y conservación de `"use client"` en componentes de cliente. Los estilos llegarán a los consumidores mediante Tailwind 4: el paquete exportará `theme.css` (tokens como `@theme`, Catppuccin
  predeterminado) y documentará la línea `@source` que hace que Tailwind del consumidor analice los archivos compilados del paquete.

## Casos límite y errores
- La pieza de Animate UI solo existe para Radix → integración manual en Base UI o `blocked` (R2), nunca una familia de primitivas mixta.
- Falla el comando de instalación del código original o incorpora dependencias incompatibles (versiones de React/Tailwind/Motion) → fijar versiones, adaptar o marcar como `blocked` con un motivo.
- Dos fuentes implementan lo mismo → conservar una según §10.2/§11.6; la otra pasa a ser una variante o queda `discarded` con un motivo.
- Licencia desconocida, ambigua o que prohíbe la redistribución → implementación desde cero o exclusión (R10), documentada en el registro.
- Consumidor sin un token `read:packages` → `npm install` falla con 401; el README y `AGENTS.md` explican el `.npmrc` y la variable de entorno de Vercel para los proyectos consumidores.
- El consumidor olvida la línea `@source` o `theme.css` → los componentes se renderizan sin estilos; la prueba de consumo verifica la configuración documentada y la guía la establece como paso uno.
- Consumidor en Next 15 (lotm) o sin Next → el paquete no tiene dependencia de Next (R18); solo se prueba Next 16.
- Sin WebGL / dispositivo de gama baja / movimiento reducido → alternativa estática (R13).
- SSR/hidratación: efectos exclusivos del cliente protegidos; ninguna advertencia de hidratación en la compilación del catálogo.
- Pull to Refresh frente al desplazamiento nativo, Magnifying Dock en pantallas táctiles, Slide to Confirm sin arrastre → alternativa con botón/teclado (R7).
- Voice Note usa `getUserMedia`/`MediaRecorder` reales (sin backend de carga); sin permiso de micrófono → estado explícito de permiso denegado. Upload Dropzone que supera el tamaño o tipo permitidos → estado de rechazo.
- Page Transition depende del enrutador y de su versión: solo se valida con el Next App Router del catálogo; los demás enrutadores se documentan como no probados.

## Restricciones
- Monorepo con npm workspaces, npm, Node 24, TypeScript strict. Paquete: React 19 como peer, Base UI, Motion (`motion`),
  tokens de Tailwind 4. Catálogo: Next.js 16 App Router, React 19, Tailwind 4 (precedente: `~/dev/dav033-demos`).
- Base UI como única familia de primitivas; Motion para animaciones, CSS para transiciones simples.
- Pruebas: Vitest + Testing Library (unitarias), Playwright + `@axe-core/playwright` (e2e/accesibilidad), incluida una ejecución con movimiento reducido.
- Código, comentarios e identificadores en inglés; textos de la interfaz del catálogo en español.
- El repositorio será público permanentemente: sin secretos ni código cuya licencia prohíba su redistribución (R10). No tendrá
  licencia de código abierto (todos los derechos reservados, uso personal). Los agentes hacen commits directamente en `main`; CI ejecuta verify en cada push.
- La evidencia de trabajo (informes, capturas de pantalla) va a la carpeta `.evidence/`, ignorada por git, y se copia a
  `~/bitacora/david-ui/artifacts/REQ-001/`; los registros de hallazgos `.evidence/*.findings.json` se rastrean (las instantáneas del verificador
  excluyen los archivos ignorados).
- Acciones de producción autorizadas globalmente por el propietario (2026-10-19): crear el repositorio de GitHub, hacer push a `main`,
  publicar en GitHub Packages mediante Actions y realizar despliegues en Vercel.

## Prioridades y fases
Obligatorio, en este orden: base del paquete, identidad y publicación (US-1, US-2, US-3) → componentes P1 (US-4) → catálogo
público en Vercel (US-5) → P2 + capacidades (US-6) → Bencho (US-7) → React Bits (US-8) → índice para agentes y aceptación (US-9).
Cada hito de una familia posterior al catálogo agrega sus entradas al paquete y al catálogo conjuntamente. MVP = hasta US-5.

## Cronograma y dependencias
- Sin fecha límite. Cada hito se puede verificar y confirmar mediante un commit de forma independiente.
- US-5 depende de US-4 (el catálogo se construye con los componentes P1). US-7/US-8 dependen del registro de licencias (US-2).

## Supuestos
- Repositorio `dav033/david-ui`, paquete `@dav033/david-ui` (GitHub Packages requiere el ámbito del propietario).
- Tema predeterminado Catppuccin Latte/Mocha con acento mauve (confirmado el 2026-10-26, ronda 1 Q5).
- Sonner es el motor de notificaciones, salvo que el análisis muestre que la primitiva de notificaciones de Animate UI es un mejor motor único.
- Las licencias de Bencho son desconocidas; se aplica la reimplementación desde cero a las 12 entradas si no se permite claramente la redistribución pública.
- Proyecto de Vercel `david-ui` con el dominio asignado por el proveedor; sin dominio personalizado.
- FPS/memoria se miden con emulación móvil de Playwright y limitación de CPU (R13), no en teléfonos reales de gama baja.

## Cobertura
| Tema | Estado |
|---|---|
| Objetivo y problema | Claro |
| Usuarios / actores | Claro |
| Alcance | Claro |
| Fuera de alcance | Claro |
| Flujos y comportamiento | Claro (detalle por subplan cuando cada subplan esté en curso) |
| Casos límite | Claro |
| Criterios de aceptación | Claro |
| Restricciones | Claro |
| Prioridades y fases | Claro |
| Cronograma | Claro (sin fecha límite) |

## Aclaraciones
### Ronda 1 — 2026-10-22 (reemplazada en parte por D-003)
- P: ¿Alcance de este requisito? → R: (a) las 93 entradas, en hitos.
- P: ¿Nombre del proyecto y del repositorio? → R: «ui kit david o algo así» → `david-ui`.
- P: ¿Distribución y alojamiento? → R: una aplicación de Next.js = catálogo + registro de shadcn en Netlify — **reemplazado el 2026-10-26**.
- P: ¿Familia de primitivas? → R: Base UI.
- P: ¿La licencia de una fuente prohíbe copiarla? → R: (a) reimplementación desde cero con el origen documentado.
- Adición del propietario: toda la aplicación del catálogo debe construirse con el propio kit; si falta una pieza, se obtiene de shadcn; de lo contrario, se crea
  un componente animado propio (R4).

### Redirección del propietario — 2026-10-26
- El kit es un paquete npm para uso personal (sin fines comerciales), además de un catálogo web público en Vercel que solo muestra componentes y no tiene inicio de sesión. Primero el paquete y luego la web; la web usa el mismo paquete, y los componentes que falten se agregan y se iteran durante el proceso. Las CLI de GitHub y Vercel ya tienen la sesión iniciada.

### Ronda 1 (planificación) — 2026-10-26
- P: ¿Dónde se aloja el paquete? → R: repositorio público de GitHub por ahora (el registro se consultó en la ronda 2).
- P: ¿Diseño del repositorio? → R: (a) un monorepo, `packages/ui` + `apps/catalog` mediante workspace.
- P: ¿Orden de los hitos? → R: (a) primero la base del paquete + P1, luego el catálogo público y después cada familia se agrega conjuntamente al paquete y al catálogo.
- P: ¿Alcance de este plan? → R: (a) las 93 entradas + 22 mejoras, en hitos.
- P: ¿Conservar el resto (Base UI, React 19, Tailwind 4, Motion, Catppuccin, 3 perfiles de movimiento, catálogo en español, catálogo hecho solo con el kit, implementación desde cero)? → R: sí, todo.

### Ronda 2 (planificación) — 2026-10-26
- P: ¿Registro de npm? → R: (a) GitHub Packages `@dav033/david-ui`, publicado por Actions; los consumidores usan un token `read:packages`.
- P: ¿React Bits o repositorio público (la licencia prohíbe redistribuir sus componentes)? → R: el repositorio siempre permanece
  público; la implementación independiente o exclusión se decide cuando el subplan de React Bits sea el tema principal.
- P: ¿Estilos para los consumidores? → R: (a) consumidores de Tailwind 4; el paquete exporta `theme.css` + `@source` documentado.
- P: ¿Integración con agentes? → R: aceptado: `AGENTS.md` + `llms.txt` en el paquete; `/llms.txt` y `/index.json` en el catálogo.
- Decisiones del responsable (el propietario no objetó): Changesets para el versionado; paquete exclusivo de React, sin dependencia de Next.

### SP-1 — 2026-10-26
- P: ¿Licencia del repositorio público? → R: (a) ninguna: todos los derechos reservados; el README indica uso personal; el código MIT copiado conserva su aviso.
- P: ¿Cómo trabajan los agentes en el repositorio? → R: (a) commits directos a `main`; un flujo de CI ejecuta `npm run verify` en cada push.
- Resoluciones principales: compilación de tsc por archivo a ESM (conserva `"use client"`, importaciones por componente); el manifiesto está en `packages/ui`.

## Pruebas

Dónde puede probar el propietario cada subplan una vez construido (D-131). Las filas de SP-2 y SP-4 indican rutas propuestas que
se fijan cuando se definen esos subplanes.

| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local (`~/dev/david-ui`) + GitHub https://github.com/dav033/david-ui | `git clone https://github.com/dav033/david-ui /tmp/dui && cd /tmp/dui && npm ci && npm run verify`; luego `npm run build --workspaces && npm run dev -w apps/catalog` y abre http://localhost:3000/api/health; abre https://github.com/dav033/david-ui/actions | verify pasa (lint, verificación de tipos, pruebas unitarias, `check:kit-only`, `catalog:check` con 42/7/12/32 entradas + 22 mejoras, builds); la ruta de health responde 200 con la exportación provisional del paquete; el repositorio es público, el README indica uso personal / todos los derechos reservados y no hay archivo LICENSE; la ejecución más reciente de CI en `main` está en verde |
| SP-2 | Local | `npm run test -w packages/ui`; `npm run build --workspaces && npm run dev -w apps/catalog` y abre la ruta de vista previa de identidad definida con SP-2 (propuesta: http://localhost:3000/preview/identity) | tokens Catppuccin Latte/Mocha con acento mauve; cambiar entre claro/oscuro y sutil/natural/expresivo modifica los colores y la duración de las animaciones; con la opción de movimiento reducido del sistema operativo activada, las transiciones pasan a ser instantáneas o solo de opacidad |
| SP-3 | GitHub Packages https://github.com/dav033/david-ui/pkgs/npm/david-ui + aplicación local nueva | Fusiona un changeset en `main` y abre https://github.com/dav033/david-ui/actions (ejecución de Release); en una carpeta vacía: `npx create-next-app@16 consumer`, agrega `.npmrc` con `@dav033:registry=https://npm.pkg.github.com` y `//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}` (token con `read:packages`), `npm i @dav033/david-ui`, importa `@dav033/david-ui/theme.css` + la línea `@source` documentada + un componente, `npm run build && npm start`; o `node scripts/consume-smoke.mjs` | la ejecución de Release está en verde y la página del paquete muestra la nueva versión; la instalación y la compilación pasan; el componente se renderiza con los tokens del kit (acento mauve); sin el token, `npm i` falla con 401 |
| SP-4 | Local | `npm run test -w packages/ui`; `npm run catalog:check`; `npm run test:e2e`; `npm run build --workspaces && npm run dev -w apps/catalog` y abre la ruta de demostración P1 definida con SP-4 (propuesta: http://localhost:3000/dev/p1) | las 30 entradas P1 y las 15 mejoras relacionadas tienen un estado final (`validated`/`implemented`/`blocked`/`discarded` con motivo); cada componente validado funciona con teclado y pantalla táctil, muestra sus estados y respeta la opción de movimiento reducido |
| SP-5 | Local | `npm run build --workspaces && npm run dev -w apps/catalog`, abre http://localhost:3000, http://localhost:3000/llms.txt y http://localhost:3000/index.json | no requiere inicio de sesión; filtros por fuente/categoría/prioridad/estado/tipo, búsqueda con paleta de comandos, ficha de entrada con demostración en vivo, galería de estados, tabla de props, fragmento de uso, origen/licencia/versión, tema claro/oscuro, vista previa del viewport y selector de perfil de movimiento; página de brechas; el índice para agentes responde en ambas rutas |
| SP-6 | Producción — Vercel https://david-ui.vercel.app (asignada por el proveedor; URL exacta registrada por SP-6) | Abre la URL en una ventana privada; abre una ficha de entrada, `/llms.txt` e `/index.json`; `curl -I <url>/index.json`; revisa el despliegue en el panel de Vercel | todas las páginas responden 200 sin inicio de sesión; el despliegue corresponde al commit más reciente de `main` de dav033/david-ui y usa `apps/catalog` como raíz |
| SP-7 | Producción — Vercel https://david-ui.vercel.app (asignada por el proveedor; URL exacta registrada por SP-6) + GitHub Packages | En el catálogo, filtra por prioridad P2 y tipo capability; abre las entradas base mejoradas; revisa la nueva versión del paquete en https://github.com/dav033/david-ui/pkgs/npm/david-ui | hay 12 entradas P2 y 7 capabilities con estado final, forma de exposición y API; las 22 mejoras muestran un resultado en sus entradas base; se publica una nueva versión del paquete |
| SP-8 | Producción — Vercel https://david-ui.vercel.app (asignada por el proveedor; URL exacta registrada por SP-6) + GitHub Packages | Filtra por fuente Bencho; abre Slide to Confirm, Magnifying Dock, Picker Wheel y Pull to Refresh; usa solo el teclado y luego la vista previa para viewport móvil | 12 entradas con estado final y origen (`own (inspired by Bencho)` cuando se implementen desde cero); cada gesto tiene una alternativa con botón o teclado; Picker Wheel y Select comparten el contrato de valor (R12) |
| SP-9 | Producción — Vercel https://david-ui.vercel.app (asignada por el proveedor; URL exacta registrada por SP-6) + GitHub https://github.com/dav033/david-ui | Filtra por fuente React Bits; abre la página de brechas; abre un fondo con la opción de movimiento reducido del sistema operativo activada y en el viewport móvil; busca avisos de derechos de autor de React Bits en el repositorio | cada una de las 32 entradas se entrega con una implementación independiente o figura como excluida con su motivo; los fondos muestran la alternativa estática cuando el movimiento reducido está activado; no hay código de React Bits copiado en el repositorio |
| SP-10 | Local + GitHub Packages + Producción — Vercel https://david-ui.vercel.app (asignada por el proveedor; URL exacta registrada por SP-6) | `node scripts/acceptance.mjs`; abre `<url>/llms.txt`; en una aplicación consumidora, ejecuta `ls node_modules/@dav033/david-ui` después de la instalación | el script de aceptación instala la versión más reciente y compila cada entrada validada; `llms.txt`, `/index.json` y `AGENTS.md`/`llms.txt` del paquete enumeran cada entrada con su ruta de importación, origen, licencia y estado de QA |

## Entradas

Reescrito el 2026-10-26 para D-003; las entradas de Netlify, secreto de inicio de sesión y repositorio privado de las revisiones 1–10 ya no
aplican. Solo ubicaciones, nunca valores. Subplan vacío = todo el plan.

| Elemento | Subplan | Ubicación | Proveedor | Estado |
|---|---|---|---|---|
| Alcance, inventario y nomenclatura | | SPEC.md, SOURCE-INVENTORY.md | Propietario | disponible |
| Cuenta de GitHub con permisos de repositorio y flujos de trabajo | SP-1 | CLI `gh` con sesión iniciada como dav033 (permisos repo, workflow, delete_repo); `dav033/david-ui` no existe (verificado el 2026-10-26) | Propietario | disponible |
| Credencial de publicación del paquete | SP-3 | `GITHUB_TOKEN` de GitHub Actions con `packages: write`, configurado en el flujo de publicación | GitHub | disponible |
| Token de lectura para la prueba local de consumo | SP-3 | Token de `gh` tras `gh auth refresh -s read:packages`, o un PAT clásico con `read:packages` en `~/.npmrc` | Propietario | pendiente: se solicitará cuando SP-3 sea el tema principal |
| Cuenta de Vercel | SP-6 | CLI `vercel` con sesión iniciada como dav033 | Propietario | disponible |
| Acceso de Vercel ↔ GitHub a `dav033/david-ui` | SP-6 | Integración de GitHub con Vercel, o como alternativa `vercel deploy --prod` desde el checkout | Propietario | pendiente: se solicitará cuando SP-6 sea el tema principal |
| Política de verificación para la prueba de solo lectura en producción | SP-6 | `~/bitacora/david-ui/verification-policy.json` (archivo del operador) | Propietario | pendiente: se solicitará cuando SP-6 sea el tema principal |
| Datos de prueba y entorno de ejecución local | | Datos sintéticos de componentes y aplicaciones de consumo desechables creados por sus tareas; sin base de datos, servicio de pago ni host SSH | Implementador | disponible |
| Almacenamiento de artefactos | | `.evidence/` (ignorado por Git); `~/bitacora/david-ui/artifacts/REQ-001/` | Plan | ubicación indicada |
