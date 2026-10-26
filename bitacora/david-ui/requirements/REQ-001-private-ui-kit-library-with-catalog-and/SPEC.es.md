---
id: REQ-001
status: planned
created: 2026-10-22
track: deep
---
# REQ-001 — Biblioteca privada de componentes UI con catálogo y registro

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

Inventario de fuentes (documento v4 del propietario, en español y de referencia para la lista de componentes, las coincidencias y las reglas por fuente):
[SOURCE-INVENTORY.md](SOURCE-INVENTORY.md). Los números de sección `§N` que aparecen abajo hacen referencia a ese documento.

## Problema y objetivo
David desarrolla varios proyectos React (maros, pictures, dav033-demos, proposal-studio…) y cada uno arma su UI de forma puntual a partir de shadcn/ui, Animate UI y React Bits, por lo que cada proyecto se ve y se comporta de manera diferente, y los agentes vuelven a elegir componentes cada vez. Objetivo: **un kit privado y reutilizable de componentes React** ("david-ui") con una sola identidad visual, un alto estándar de interactividad y retroalimentación, un catálogo web privado con demostraciones reales y un registro compatible con shadcn desde el que tanto David como los agentes de programación (Claude Code, Codex) puedan instalar componentes.

**El éxito se ve así:**
- Las 93 entradas candidatas del inventario (42 shadcn + 7 capacidades de Animate UI + 12 Bencho + 32 React Bits Free) y las 22 mejoras de Animate UI terminan en un estado verificado y registrado (ninguna queda `pending`).
- `npx shadcn add @david-ui/<name>` instala cualquier entrada `implemented`/`validated` en una aplicación Next.js nueva, que luego compila sin modificaciones.
- La aplicación del catálogo está construida al 100 % con componentes del kit (verificado mediante una comprobación automatizada).
- `npm run verify` y `npm run test:e2e` pasan; el catálogo está desplegado y es privado.

## Usuarios / actores / partes interesadas
- **Propietario (David):** explora el catálogo, instala componentes en sus proyectos y aprueba entradas.
- **Agentes de programación (Claude Code, Codex):** descubren componentes mediante el índice para agentes y los instalan desde el registro.
- **Visitantes del catálogo:** solo el propietario (privado, requiere inicio de sesión).

## Alcance (incluido)

### US-1 (P1, Must) — Fundamentos del kit
Como propietario, quiero un repositorio con tokens, tema, perfiles de movimiento y herramientas para que todos los componentes compartan una identidad.
**Criterios de aceptación:**
- Dado el repositorio, cuando se ejecuta `npm run verify`, pasan lint, la comprobación de tipos, las pruebas unitarias, la comprobación de uso exclusivo del kit, la comprobación del catálogo, la compilación del registro y la compilación de producción.
- Dado cualquier componente, cuando el tema cambia entre claro y oscuro o el perfil de movimiento cambia entre sutil, natural y expresivo, sus colores, radios, sombras y tiempos de movimiento provienen de los tokens compartidos.

### US-2 (P1, Must) — Manifiesto del catálogo y registro de licencias
Como propietario, quiero registrar cada entrada del inventario con sus metadatos para que nada se cuente dos veces ni se olvide.
**Criterios de aceptación:**
- Dado el manifiesto, cuando se ejecuta la comprobación del catálogo, entre las entradas con `origin: inventory` encuentra exactamente 42 shadcn (30 P1 + 12 P2), 7 capacidades de Animate UI, 12 Bencho (6 de capacidad nueva + 6 variantes) y 32 React Bits (9 de texto + 12 de UI + 6 efectos + 5 fondos) = 93, además de 22 mejoras de Animate UI vinculadas a entradas shadcn existentes; falla ante cualquier otro total, un id duplicado o una mejora sin una entrada base. Las entradas con `origin: catalog-driven` u `origin: own` (R4) se enumeran por separado y nunca se cuentan entre las 93.
- Dada una entrada con estado `implemented` o `validated`, tiene URL de origen, versión/commit de origen, fecha de incorporación, licencia, resultado de compatibilidad de dependencias y una demostración; en cambio, una entrada de desarrollo independiente (`own (inspired by <source>)`) registra `upstream: n/a`, la URL y la fecha consultadas, además de una nota de revisión de licencia; una entrada `blocked`/`discarded` tiene una justificación por escrito.

### Semántica de estados
- `pending` — registrada, aún no evaluada (permitido solo antes de que termine el hito de la entrada).
- `implemented` — el código está en el registro, existen una demostración y pruebas unitarias, y la instalación funciona; alguna comprobación R6 sigue fallando y la justificación está escrita en la entrada.
- `validated` — todas las comprobaciones R6 pasan. Este es el estado objetivo para cada entrada.
- `blocked` — no se puede entregar por ahora (licencia, familia de primitivas, conflicto de dependencias); se documentan la justificación y la condición para desbloquearla.
- `discarded` — no se entrega de forma deliberada (redundante según §10.2/§11.6); se documenta la justificación.
- La aprobación de producción del propietario (§10.4 "aprobarlos para producción") es una marca independiente del manifiesto, `ownerApproved` (valor predeterminado `false`), que el propietario establece en el catálogo después de la entrega; nunca bloquea este requisito.

### US-3 (P1, Must) — 30 componentes shadcn P1 con sus mejoras de Animate UI
Como propietario, quiero que los componentes esenciales (§3.1–3.6) funcionen sobre Base UI con sus mejoras de movimiento para que los nuevos proyectos puedan comenzar con el kit.
**Criterios de aceptación:**
- Dado que M2 está terminado, cuando se ejecuta `npm run catalog:check`, las 30 entradas P1 tienen estado `validated`, `implemented`, `blocked` o `discarded` (con justificación), y las 15 mejoras relacionadas con P1 tienen un resultado (`compatible`, `manual`, `blocked`, `discarded`); `npx playwright test e2e/p1.spec.ts` pasa para cada entrada P1 `validated`.

### US-4 (P1, Must) — Catálogo privado creado con el kit
Como propietario, quiero un catálogo web privado con filtros, búsqueda, demostraciones en vivo, estados, tema claro/oscuro, vista previa adaptable del tamaño de pantalla, selector de perfil de movimiento y comandos de instalación, creado solo con componentes del kit.
**Criterios de aceptación:**
- Dada la sesión iniciada del propietario, al explorar el catálogo, funcionan todas las capacidades R9 (`e2e/catalog-browse.spec.ts`, `e2e/catalog-entry.spec.ts`) y pasa `npm run check:kit-only`.
- Dada una solicitud sin sesión ni token, las páginas redirigen al inicio de sesión y `/r/*` devuelve 401 (`e2e/auth.spec.ts`).

### US-5 (P2, Must) — 12 componentes shadcn P2, mejoras restantes y 7 capacidades de Animate UI (§3.7, §4, §5)
**Criterios de aceptación:**
- Dado que M4 está terminado, las 12 entradas P2 y las 7 capacidades tienen un estado final (no `pending`), las 22 mejoras tienen un resultado y cada capacidad registra su forma de exposición (componente, hook o variante), un resumen de API y su ubicación en el catálogo (§9); `e2e/p2.spec.ts` y `e2e/capabilities.spec.ts` pasan para las entradas `validated`.

### US-6 (P2, Must) — 12 entradas de Bencho UI (§10), con desarrollo independiente cuando la licencia prohíbe copiar
**Criterios de aceptación:**
- Dado que M5 está terminado, las 12 entradas de Bencho tienen un estado final y un origen según R10, usan los slugs de §10.3 en `@david-ui`, cumplen todas las reglas R12 aplicables y pasa `e2e/bencho.spec.ts` (incluidas las alternativas de teclado/botón y los conflictos de desplazamiento emulados en móviles).

### US-7 (P2, Must) — 32 entradas de React Bits Free (§11)
**Criterios de aceptación:**
- Dado que M6 está terminado, las 32 entradas tienen un estado final, conservan en el encabezado del código el aviso de licencia de origen, se muestran sin advertencias de hidratación, respetan el movimiento reducido y los fondos cumplen R13 (`e2e/reactbits-*.spec.ts`).

### US-8 (P2, Must) — Integración de agentes y despliegue
Como propietario, quiero que los agentes puedan descubrir e instalar componentes del kit y que el catálogo esté desplegado de forma privada.
**Criterios de aceptación:**
- Dada una aplicación Next que consume el kit y está configurada con el token, cuando un agente lee `/r/index.json` y ejecuta `npx shadcn add @david-ui/<slug>`, el componente se instala y la aplicación compila (`scripts/acceptance.mjs`).
- Dada la URL de producción, `scripts/prod-smoke.mjs` confirma el inicio de sesión, la protección de páginas y la aplicación del token.

## Fuera de alcance
- Migrar proyectos existentes (maros, pictures, dav033-demos…) al kit: se abordará en requisitos posteriores.
- React Bits Pro o cualquier componente de pago; las brechas reales (Comparison Slider, Device, Page Flip, AI Blob con estados, §11.5) se documentan, pero no se implementan.
- Editores especializados (similares a Notion, editores de grafos) (§7).
- Publicar el kit de forma pública o en npm; cualquier redistribución a terceros.
- Backends detrás de componentes UI (almacenamiento real de archivos para Upload Dropzone, carga de audio para Voice Note): solo UI + callbacks.
- Componentes shadcn enumerados en §3.8, salvo que la aplicación del catálogo los necesite (R4).
- React Bits `Count Up`, `Counter` y `Dock` (§11.6.1–2): no seleccionados.
- Las composiciones propias de §11.5 "Modal Cards" y "Hover Preview": para más adelante; se enumeran en la página de brechas del catálogo junto con las brechas reales (Comparison Slider, Device, Page Flip, AI Blob con estados).

## Requisitos
- R1. El kit deberá alojarse en un nuevo repositorio privado `~/dev/david-ui` (GitHub `dav033/david-ui`) como una sola
  aplicación Next.js que funcione a la vez como catálogo y registro de shadcn; las fuentes de los componentes estarán en
  `registry/david-ui/` y se publicarán bajo el espacio de nombres `@david-ui`.
- R2. El kit deberá usar Base UI como única familia de primitivas; cuando Animate UI no tenga una variante para Base UI, la
  mejora deberá integrarse manualmente en el componente de Base UI (resultado `manual`) o registrarse como `blocked` con un motivo.
- R3. Cada componente deberá leer los colores, la tipografía, el espaciado, los radios y las sombras de tokens CSS compartidos, y los controles funcionales (shadcn, Animate UI, Bencho) también deberán tomar los tiempos de movimiento del perfil activo; los efectos gráficos de React Bits tomarán los tonos, tamaños y fuentes de los tokens, pero conservarán su propia física (§11.6.8). El tema predeterminado deberá ser Catppuccin Latte (claro) / Mocha (oscuro), con acento mauve, reemplazable por cada proyecto consumidor.
- R4. La aplicación del catálogo deberá construirse exclusivamente con componentes del kit: cuando necesite una pieza de UI que el kit no incluya, el ejecutor deberá agregarla primero desde shadcn/ui (registrada como una adición impulsada por el catálogo) y solo si no existe un componente de shadcn deberá crear un componente propio con movimiento; una comprobación automatizada (`npm run check:kit-only`) deberá fallar cuando el código de la aplicación fuera de `registry/` importe directamente primitivas de UI o bibliotecas de animación, o renderice elementos HTML interactivos sin procesar
  (`button`, `input`, `select`, `textarea`, `dialog`, `a` con estilo de botón).
- R5. El manifiesto del catálogo deberá registrar cada entrada con id (versión kebab-case del nombre; slugs de §10.3 para Bencho, p. ej.,
  `seek` → `expanding-search`, `liq-create` → `create-menu`, `picker` → `picker-wheel`, `dock` → `magnifying-dock`),
  nombre, fuente, origen (`inventory`, `catalog-driven`, `own`), categoría, prioridad (P1/P2: shadcn según la lista; Alta → P1,
  Media → P2 para §5 y §11; Bencho P2), además de la prioridad original, tipo (`base` = shadcn, `capability` = Animate UI
  §5, `new-capability` / `variant` = Bencho §10.1, `presentation` = React Bits), forma de exposición (componente, hook,
  variante, utilidad), estados aplicables, estado (`pending`, `implemented`, `validated`, `blocked`,
  `discarded`), URL y versión/commit de origen, licencia, dependencias, resumen de la API pública, resultados de a11y y movimiento reducido, y ruta de la demo; las 22 mejoras deberán vincularse a su entrada base con un resultado de prueba
  (`compatible`, `manual`, `blocked`, `discarded`) y nunca contabilizarse como entradas.
- R6. Cuando una entrada se marque como `validated`, deberá contar con una demo en vivo con todos los estados de `applicableStates`
  (hover, focus-visible, pressed, disabled, loading, success, error), operación con teclado cuando sea interactiva, ninguna
  infracción de axe, respeto por `prefers-reduced-motion`, ninguna advertencia de hidratación con SSR, pruebas unitarias de su comportamiento (para efectos de texto y fondos: pruebas de renderizado, props y movimiento reducido/respaldo) y un elemento del registro que se instale en una aplicación nueva.
- R7. Cada control interactivo deberá permitir la operación con teclado y con pantalla táctil; hover, arrastre o proximidad del cursor nunca deberán ser la única forma de operarlo (§11.6.7, §10.2).
- R8. El kit deberá ofrecer tres perfiles de movimiento (sutil, natural predeterminado, expresivo) mediante un provider; las animaciones deberán preferir `transform`/`opacity`, poder interrumpirse y reducirse a instantáneas o solo opacidad cuando se active el movimiento reducido.
- R9. El catálogo deberá ofrecer: exploración y filtrado por fuente, categoría, prioridad, estado y tipo; búsqueda con paleta de comandos;
  una página por entrada con demo en vivo, galería de estados, tabla de props/API, comando de instalación, origen/licencia/versión, alternancia entre modo claro y oscuro, vista previa del viewport (móvil/tablet/escritorio) y selector de perfil de movimiento; una página de brechas que enumere las brechas documentadas
  (§11.5) y cada entrada `blocked`/`discarded` con su motivo. Las entradas del inventario que el catálogo necesite pronto (p. ej.,
  `Command`, `Scroll Area`, `Drawer`) se construirán durante el hito del catálogo y seguirán contando como entradas del inventario.
- R10. Antes de copiar código de una fuente, el ejecutor deberá registrar la licencia de esa fuente en el registro de licencias; si
  una licencia prohíbe copiar (algo previsto para algunos bloques de Bencho), la entrada deberá reimplementarse desde cero (a partir del comportamiento descrito/demostrado públicamente, sin copiar código) y marcarse con el origen `own (inspired by <source>)`. Los archivos copiados deberán conservar el aviso de licencia original en un comentario de encabezado (verificado por `catalog:check`). Las actualizaciones de upstream serán deliberadas: el manifiesto registrará la versión de upstream y la fecha de incorporación, y cada actualización comparará los cambios de upstream con la adaptación local en lugar de sobrescribirla (procedimiento en el `AGENTS.md` del repositorio).
- R11. Las notificaciones deberán tener exactamente un motor (Sonner, salvo que el análisis de compatibilidad indique otra opción, registrada en DECISIONS); el movimiento de Animate UI y Bencho Toast Stack serán presentaciones sobre ese motor (§10.2.1).
- R12. Las entradas que se solapen deberán mantener un único modelo de valores, con cada regla cubierta por una prueba unitaria o e2e:
  `RollingNumberInput` será una entrada editable y `CountingNumber` una visualización pasiva, con API distintas; `PickerWheel`
  emitirá el mismo contrato de valores que `Select`; `SloshSlider` compartirá `value`/`onValueChange`, min/max/step y el comportamiento del teclado con `Slider`; `Checklist` usará el modelo booleano de `Checkbox`; las variantes de tarjetas compondrán `Card`; `CreateMenu` y `ExpandingSearch` conservarán la gestión del foco y la operación con teclado; `SlideToConfirm` solo emitirá una intención de confirmación (nunca reemplazará la validación del servidor) y ofrecerá una alternativa con botón/teclado; `MagnifyingDock` funcionará con foco y pantalla táctil.
- R13. Los fondos WebGL/canvas y los efectos pesados deberán cargarse de forma diferida, pausarse cuando queden fuera de pantalla o la pestaña esté oculta, y mostrar un respaldo CSS estático cuando WebGL no esté disponible o se active el movimiento reducido. Con la emulación móvil de Playwright (perfil Pixel 7, limitación de CPU de 4×), cada fondo deberá mantener una mediana de ≥ 30 FPS durante 5 s; de lo contrario, se publicará con el respaldo estático como predeterminado en móviles y se registrará la medición.
- R14. El catálogo deberá ser privado: las páginas requerirán el inicio de sesión del propietario (contraseña + cookie de sesión firmada), y los endpoints del registro `/r/*` (incluidos `/r/index.json` y `/r/llms.txt`) requerirán un token bearer que los proyectos consumidores y los agentes enviarán mediante los encabezados del registro en `components.json` o un encabezado `Authorization`.
- R15. El kit deberá publicar un índice para agentes (`AGENTS.md`/`CLAUDE.md` en el repositorio, además de un índice legible por máquina en
  `/r/index.json` y `/r/llms.txt`, protegido con token según R14) que enumere cada entrada con sus variantes, origen, comando de instalación, versión, dependencias,
  licencia y estado de QA, junto con una guía breve de consumo para otros proyectos.
- R16. El catálogo deberá desplegarse en Netlify desde el repositorio privado de GitHub, con los secretos únicamente en las variables de entorno de Netlify.

## Casos límite y errores
- La pieza de Animate UI solo existe para Radix → integración manual en Base UI o `blocked` (R2); nunca se usará una familia mixta de primitivas.
- Falla el comando de instalación de upstream o incorpora dependencias incompatibles (versiones de React/Tailwind/Motion) → fijar versiones, adaptar o marcar `blocked` con un motivo.
- Dos fuentes implementan lo mismo → conservar una según §10.2/§11.6; la otra pasa a ser una variante o se marca `discarded` con un motivo.
- Licencia desconocida o ambigua → tratarla como una prohibición de copia (reimplementación desde cero) y dejar constancia.
- Sin WebGL / dispositivo de gama baja / movimiento reducido → respaldo estático (R13).
- SSR/hidratación: efectos exclusivos del cliente protegidos; ninguna advertencia de hidratación en la compilación del catálogo.
- Solicitud al registro sin token o con un token incorrecto → 401, sin filtrar el código fuente de los componentes.
- Pull to Refresh frente al desplazamiento nativo, Magnifying Dock en pantallas táctiles, Slide to Confirm sin arrastre → alternativa con botón/teclado (R7).
- Voice Note usa `getUserMedia`/`MediaRecorder` reales (sin backend de carga); sin permiso para el micrófono → estado explícito de permiso denegado. Upload Dropzone por encima del tamaño/tipo permitido → estado de rechazo.
- Page Transition depende del router y de su versión: solo se validará con Next App Router del catálogo; los demás routers se documentarán como no probados.

## Restricciones
- Next.js 16 App Router, React 19, TypeScript strict, Tailwind CSS 4, npm, Node 24 (precedente: `~/dev/dav033-demos`).
- CLI de shadcn con estilo Base UI; Motion (`motion`) para animaciones, CSS para transiciones simples.
- Pruebas: Vitest + Testing Library (unitarias), Playwright + `@axe-core/playwright` (e2e/a11y), incluida una ejecución con movimiento reducido.
- Código, comentarios e identificadores en inglés; textos de la interfaz del catálogo en español.
- Licencias: React Bits Free tiene licencia MIT + Commons Clause (solo para uso propio privado; conservar los avisos); el kit seguirá siendo privado (§11.7).
- No incluir secretos en el repositorio; `.env.example` documenta `DAVID_UI_PASSWORD`, `DAVID_UI_SESSION_SECRET`, `DAVID_UI_REGISTRY_TOKEN`.
- La evidencia de trabajo (informes, registros de hallazgos) irá en la carpeta `.evidence/`, ignorada por git, y se copiará a
  `~/bitacora/david-ui/artifacts/REQ-001/`.
- Acciones de producción autorizadas globalmente por el propietario (2026-10-19): crear el repositorio privado de GitHub, enviar cambios a
  `main` y desplegar en Netlify.

## Prioridades y fases
Obligatorio, en este orden: cimientos + manifiesto + registro (US-1, US-2) → componentes P1 (US-3) → aplicación del catálogo (US-4) → P2 +
capacidades (US-5) → Bencho (US-6) → React Bits (US-7) → índice de agentes + despliegue + aceptación (US-8). MVP = hasta US-4.

## Cronograma y dependencias
- Sin fecha límite. Cada hito se puede verificar y confirmar mediante un commit de forma independiente.
- US-4 depende de US-3 (el catálogo se construye con los componentes P1). US-6/US-7 dependen del registro de licencias (US-2).

## Supuestos
- Nombre del proyecto/repositorio: `david-ui`; espacio de nombres del registro: `@david-ui` (el propietario dijo «ui kit david o algo así»).
- Tema predeterminado Catppuccin Latte/Mocha con acento mauve (estética del escritorio del propietario; no se confirmó explícitamente).
- Sonner será el motor de notificaciones, salvo que el análisis determine que la primitiva de notificaciones de Animate UI es un mejor motor único.
- El inicio de sesión del propietario usa una sola contraseña (sin cuentas de usuario); suficiente para un catálogo privado de un propietario.
- Las licencias de Bencho son desconocidas; la decisión del propietario de reimplementar desde cero (ronda 1, Q5) se aplica a las 12 entradas si no se permite copiar de forma clara.
- FPS/memoria se medirán con la emulación móvil de Playwright y limitación de CPU (R13), no en teléfonos reales de gama baja; una desviación deliberada de §11.6.6 «dispositivos modestos»; las comprobaciones en dispositivos reales se harán con el primer proyecto consumidor.

## Cobertura
| Tema | Estado |
|---|---|
| Objetivo y problema | Claro |
| Usuarios / actores | Claro |
| Alcance | Claro |
| Fuera de alcance | Claro |
| Flujos y comportamiento | Claro |
| Casos límite | Claro |
| Criterios de aceptación | Claro |
| Restricciones | Claro |
| Prioridades y fases | Claro |
| Cronograma | Claro (sin fecha límite) |

## Aclaraciones
### Ronda 1 — 2026-10-22
- Q: ¿Cuál es el alcance de este requisito? → A: (a) las 93 entradas, en hitos.
- Q: ¿Nombre del proyecto y del repositorio? → A: «ui kit david o algo así» → `david-ui`.
- Q: ¿Distribución y alojamiento? → A: (a) una aplicación Next.js = catálogo + registro de shadcn, Netlify, galería detrás de inicio de sesión, registro protegido con token.
- Q: ¿Familia de primitivas? → A: Base UI.
- Q: ¿La licencia de la fuente prohíbe copiar? → A: (a) reimplementación desde cero con origen documentado.
- Adición del propietario: toda la aplicación de catálogo Next.js deberá construirse con el propio kit; ningún componente quedará fuera del kit. Si el kit no incluye un componente necesario, buscarlo en shadcn; si no existe allí, crearlo y animarlo (R4).
- Revisión de la especificación (revisor independiente, 2026-10-22): se aplicaron 15 hallazgos: conteo por origen, semántica de estados, criterios de aceptación para US-3..US-8, reglas de R12 convertidas en pruebas, vocabulario, página de brechas, token en el índice de agentes, umbral de FPS, procedimiento de actualización de upstream, estados aplicables y SSR. Se aplazaron las composiciones Modal Cards / Hover Preview.

## Entradas

Actualización solo de clasificación: el alcance del producto aprobado arriba no ha cambiado. No se leyeron ni registraron valores de credenciales.

| Elemento | Ubicación | Proveedor | Estado |
|---|---|---|---|
| Alcance aprobado, inventario y nomenclatura | SPEC.md, PLAN.md, SOURCE-INVENTORY.md; solicitud del propietario en esta sesión | Propietario | disponible |
| Repositorio y directorio de requisitos | app = /home/david/dev/david-ui; directorio de requisitos proporcionado en esta sesión | Propietario / project.json | disponible |
| Cuenta / remoto de GitHub | Inicio de sesión existente en gh como dav033; repositorio privado de destino dav033/david-ui; ~/bitacora/TOOLS.md | Propietario | ubicación indicada |
| Cuenta de Netlify / entorno de destino | Inicio de sesión existente en la CLI de netlify, equipo dav033's team; nuevo sitio vinculado a dav033/david-ui; URL HTTPS asignada por el proveedor y registrada por T23 | Propietario / Netlify | ubicación indicada |
| Autorización para acciones en producción | Las restricciones de SPEC aprobada y las restricciones globales de PLAN registran la autorización del 2026-10-19; la clasificación no incluye acciones en producción | Propietario | disponible |
| URL de origen, listas de candidatos y alternativa de licencia | Secciones 3–5 y 10–11 de SOURCE-INVENTORY.md; SPEC R2/R10; T2 resuelve la compatibilidad técnica y registra pruebas de licencia de fuentes primarias antes de copiar | Propietario / upstream | disponible |
| Decisiones de stack, diseño y producto | Restricciones / requisitos / supuestos de SPEC; el propietario aprobó explícitamente estos documentos como alcance | Propietario | disponible |
| Datos de prueba y entorno de ejecución local | Datos sintéticos de componentes y aplicaciones Next desechables, creados por las tareas que los producen; no se requieren datos de clientes, base de datos, servicio de pago, webhook ni host SSH | Implementador | disponible |
| Puertos locales y verificación aislada | El entorno de pruebas usa un puerto de loopback disponible, pasa explícitamente las variables de entorno al proceso hijo y cierra sus propios procesos; no se requiere .env ni variables heredadas del shell | Implementador | disponible |
| Almacenamiento de artefactos | .evidence/ (ignorado); ~/bitacora/david-ui/artifacts/REQ-001/ | PLAN aprobado | ubicación indicada |

Entrada sin resolver 1 (consultada al inicio de la clasificación): las ubicaciones de DAVID_UI_PASSWORD,
DAVID_UI_SESSION_SECRET y DAVID_UI_REGISTRY_TOKEN. Como alternativa, el propietario puede aplazar explícitamente cada secreto indicado
con la siguiente alternativa: generarlo de forma segura durante la ejecución, almacenarlo fuera de Git y cargarlo en Netlify. No se solicitan valores.
Aún no se ha confirmado que estas tres entradas estén disponibles ni que se hayan aplazado; el plan no puede declararse listo mientras sigan sin resolverse.

### Nota de la revisión 10 — reinicio del 2026-10-24 (factual; el alcance y la aceptación no han cambiado)

El propietario eliminó toda la ejecución de las revisiones 1–9 el 2026-10-24: el estado de ejecución, la copia de trabajo local `/home/david/dev/david-ui`,
el sitio de Netlify `david-ui-private` y `~/.config/david-ui/prod.env`. Las filas anteriores que indican que el directorio del repositorio está «disponible» o señalan el sitio antiguo ya no son válidas; la revisión 10 de PLAN recrea todo desde cero. El planificador observó el 2026-10-24 que `/home/david/dev/david-ui` no existe, que `netlify api listSites` no muestra ningún sitio de david y que `gh repo view dav033/david-ui` sigue devolviendo un repositorio privado y no vacío (creado el 2026-10-23T11:18Z). No se leyó ni registró ningún valor secreto.

| # | Elemento | Ubicación | Proveedor | Estado |
|---|---|---|---|---|
| 1 | Repositorio de GitHub `dav033/david-ui` | Todavía existe en GitHub (privado y no vacío); T1 debe crearlo desde cero | Propietario | pendiente: eliminarlo, o autorizar a T1 a reutilizarlo con un nuevo historial raíz (force-push), o indicar otro repositorio |
| 2 | DAVID_UI_PASSWORD, DAVID_UI_SESSION_SECRET, DAVID_UI_REGISTRY_TOKEN, DAVID_UI_PROD_URL | Antes estaban en `~/.config/david-ui/prod.env` (eliminado). La comprobación de producción lee los nombres de `~/.config/flow/secrets.env` o del entorno del proceso del propietario | Propietario | pendiente: indicar la ubicación o aplazar cada secreto por nombre con esta alternativa: «T59 genera los tres secretos con un CSPRNG, los escribe junto con DAVID_UI_PROD_URL en `~/.config/flow/secrets.env` (modo 600) y los configura como variables de entorno de Netlify» |
| 3 | Política de verificación del operador para la prueba de humo en producción (T60) | `/home/david/dev/metodologia/bitacora/david-ui/verification-policy.json` (no existe); entrada `environment: production`, `authorization` exactamente "Owner authorizes read-only HTTPS smoke requests against the david-ui Netlify production site for REQ-001", `requirements: ["REQ-001"]` | Propietario (archivo del operador; el plan no puede autorizarlo) | pendiente: crearla o aceptar que T60 termine como BLOCKED_EXTERNAL hasta que exista |
| 4 | Nombre del sitio de Netlify | Equipo "dav033's team" (sesión iniciada en la CLI de netlify) | Propietario | pendiente: confirmar `david-ui-private` (alternativa: nombre asignado por el proveedor si ya está en uso) |
| 5 | Acceso de la aplicación de GitHub de Netlify a `dav033/david-ui` | Configuración del equipo de Netlify | Propietario | pendiente: confirmar el acceso o aceptar la alternativa `netlify deploy --prod --build` desde la copia de trabajo, manteniendo el repositorio registrado en el sitio |
| 6 | Ruta del repositorio local | `/home/david/dev/david-ui` (rol `app` de project.json) | Propietario / project.json | ubicación indicada; T1 la crea |
| 7 | Aprobaciones del contrato de diseño | `bitacora.py design approve REQ-001 <contract>@v1` o la página web del requisito; seis contratos en dos rondas | Propietario | previstas durante la ejecución (D-127), no antes de la aprobación |
