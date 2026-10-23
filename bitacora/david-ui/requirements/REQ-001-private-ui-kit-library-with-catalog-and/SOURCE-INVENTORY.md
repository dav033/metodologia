# Biblioteca UI propia — Inventario de componentes v4 (shadcn/ui + Animate UI + Bencho UI + React Bits Free)

> **Estado:** Preselección documentada; componentes todavía no integrados ni probados en un proyecto de referencia.  
> **Fecha de consolidación:** 22 de octubre de 2026.  
> **Alcance de este documento:** 42 componentes de shadcn/ui, 22 mejoras propuestas con Animate UI, 7 capacidades adicionales de Animate UI, 12 componentes Bencho UI y 32 componentes gratuitos de React Bits (selección revisada).  
> **Estado de fuentes:** Las cuatro fuentes ya tienen preselección inicial. Siguiente paso: pruebas técnicas, licencias, normalización visual, API y selección definitiva.

## 1. Objetivo

Crear una **biblioteca privada y reutilizable de componentes React** con un catálogo único, una identidad visual coherente y un alto estándar de **interactividad, respuesta inmediata y feedback**. Debe poder ser utilizada por proyectos propios y por agentes de desarrollo (por ejemplo, Codex y Claude Code).

### Stack de fuentes acordado

1. **shadcn/ui** — base funcional, accesibilidad, estructura y estilos.
2. **Animate UI** — animación y feedback de controles funcionales; nuevas primitivas de movimiento.
3. **Bencho UI** — 12 componentes preseleccionados por el usuario, sometidos a auditoría comparativa inicial.
4. **React Bits Free** — tipografía reactiva, galerías, menús, tarjetas, animaciones composables y fondos; 32 candidatos del catálogo público.

**Principio central:** No mantener cuatro bibliotecas visualmente inconexas. Construir una capa propia que normalice tokens, variantes, interacciones y APIs. No duplicar un componente salvo que una alternativa aporte una experiencia o capacidad realmente distinta.

## 2. Resumen numérico

| Bloque | Cantidad | Qué representa |
|---|---:|---|
| shadcn/ui — esenciales | 30 | Primera prioridad |
| shadcn/ui — secundarios | 12 | Segunda prioridad |
| **Total de componentes base de shadcn/ui** | **42** | Catálogo funcional propuesto |
| Mejoras / integraciones con Animate UI | **22** | Se aplican sobre componentes ya incluidos en los 42; **no** suman otros 22 componentes independientes |
| Capacidades adicionales Animate UI | **7** | Funcionalidades o variantes con entrada propia en el catálogo |
| Bencho UI — capacidad diferenciada | **6** | Añaden un patrón de uso no cubierto como componente autónomo |
| Bencho UI — variantes | **6** | Experiencias alternativas de componentes existentes |
| **Total Bencho UI preseleccionado** | **12** | Candidatos adicionales; no equivalen a 12 funcionalidades únicas |
| React Bits Free — tipografía | **9** | Efectos tipográficos y numéricos |
| React Bits Free — UI, navegación y galerías | **12** | Patrones visuales, animaciones y exploración de contenido |
| React Bits Free — animaciones de interacción | **6** | Presentación visual y feedback expresivo |
| React Bits Free — fondos interactivos | **5** | Fondos para uso opcional según proyecto |
| **Total React Bits Free** | **32** | Catálogo público sin componentes exclusivos de Pro |
| **Total de entradas candidatas** | **93** | 42 + 7 + 12 + 32; no suma las 22 mejoras sobre componentes existentes |

**Importante:** Las cantidades son un inventario de decisiones de diseño, no un número de paquetes, archivos o componentes ya implementados. Las 22 mejoras son adaptaciones sobre componentes existentes. Varias entradas Bencho y React Bits son variantes especializadas o componentes de presentación y no representan categorías funcionales nuevas.

## 3. Los 42 componentes seleccionados de shadcn/ui

**Prioridad P1** = esencial para la primera versión. **Prioridad P2** = candidato para la segunda ola. En la columna «Animate UI» se indica si alguna de las 22 integraciones identificadas corresponde a ese componente.

### 3.1. Estructura visual (4 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 1 | `Button` | Acciones primarias, secundarias y destructivas | Variante animada opcional; no contado entre las 22 |
| 2 | `Card` | Contenedores de información y módulos | Conservar base; efectos avanzados después |
| 3 | `Badge` | Etiquetas, estados y categorías | Conservar base |
| 4 | `Avatar` | Usuarios, perfiles e identidades | Conservar base |

### 3.2. Formularios (7 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 5 | `Field` | Etiquetas, descripción, errores y estructura de campo | Conservar estructura |
| 6 | `Input` | Entrada de texto | Feedback mediante estados y estilos |
| 7 | `Textarea` | Entrada multilínea | Feedback mediante estados y estilos |
| 8 | `Select` | Selección simple de opciones | **Integrar** |
| 9 | `Checkbox` | Selección booleana o múltiple | **Integrar** |
| 10 | `Switch` | Activar/desactivar ajustes | **Integrar** |
| 11 | `Combobox` | Búsqueda y selección avanzada | **Integrar** |

### 3.3. Navegación (5 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 12 | `Sidebar` | Navegación lateral de aplicaciones | **Integrar manualmente** |
| 13 | `Tabs` | Alternar entre paneles de contenido | **Integrar** |
| 14 | `Dropdown Menu` | Menús de acciones | **Integrar** |
| 15 | `Breadcrumb` | Ubicación jerárquica | Conservar base |
| 16 | `Pagination` | Navegación entre páginas de datos | **Integrar manualmente** |

### 3.4. Ventanas e interacciones (6 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 17 | `Dialog` | Modales y formularios emergentes | **Integrar** |
| 18 | `Alert Dialog` | Confirmación de operaciones importantes | **Integrar** |
| 19 | `Sheet` | Paneles laterales y auxiliares | **Integrar** |
| 20 | `Popover` | Contenido contextual flotante | **Integrar** |
| 21 | `Tooltip` | Ayuda contextual breve | **Integrar** |
| 22 | `Accordion` | Secciones expansibles | **Integrar** |

### 3.5. Feedback y estados (5 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 23 | `Alert` | Avisos informativos, preventivos y de error | Conservar base |
| 24 | `Toast` / `Sonner` | Notificaciones transitorias | **Integrar**; confirmar proveedor elegido |
| 25 | `Skeleton` | Marcadores de carga | Conservar base |
| 26 | `Spinner` | Indicación de procesamiento | Conservar base |
| 27 | `Empty` | Estados vacíos y primeros usos | Conservar base |

> **Nota sobre Toast:** En el ecosistema shadcn moderno suele utilizarse **Sonner** para notificaciones. La integración exacta de la primitiva `Toast` de Animate UI debe validarse según la base elegida (Base UI, Radix u otra) y no confundirse automáticamente con un reemplazo directo de Sonner.

### 3.6. Visualización de datos (3 — P1)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 28 | `Table` | Tablas convencionales | Conservar base |
| 29 | `Data Table` | Tablas avanzadas: filtros, ordenación, selección y paginación | Conservar patrón funcional |
| 30 | `Chart` | Gráficos, métricas y dashboards | Conservar base; animar datos puntuales cuando corresponda |

> **Nota:** `Data Table` suele implementarse como un patrón de composición (no necesariamente un control monolítico), por lo que requiere definir su API propia.

### 3.7. Secundarios (12 — P2)

| # | Componente | Uso previsto | Animate UI |
|---:|---|---|---|
| 31 | `Calendar` | Calendarios interactivos | Conservar base |
| 32 | `Date Picker` | Selección de fechas | Conservar calendario; animar el `Popover` que lo contiene |
| 33 | `Input Group` | Entradas con prefijos, iconos y botones | Conservar base |
| 34 | `Radio Group` | Opciones mutuamente excluyentes | **Integrar** |
| 35 | `Command` | Paleta de comandos y búsqueda contextual | Conservar; animar contenedor si aplica |
| 36 | `Navigation Menu` | Menús de navegación complejos | **Integrar** |
| 37 | `Drawer` | Paneles deslizantes, especialmente móviles | **Integrar** |
| 38 | `Collapsible` | Mostrar u ocultar contenido | **Integrar** |
| 39 | `Scroll Area` | Desplazamiento de contenido | Conservar; aplicar `Scroll Fade` opcional |
| 40 | `Progress` | Avance cuantitativo de procesos | **Integrar** |
| 41 | `Slider` | Control numérico mediante arrastre | **Integrar** |
| 42 | `Hover Card` | Información ampliada en hover/foco | **Integrar** |

### 3.8. Fuera de la primera selección

Estos componentes de shadcn/ui **no están incluidos en los 42** porque pueden ser más situacionales o es conveniente compararlos con Bencho/React Bits antes de elegir una implementación:

`Aspect Ratio`, `Carousel`, `Menubar`, `Resizable`, `Toggle Group`, `Input OTP`, `Context Menu`, `Kbd`.

No están prohibidos: pueden incorporarse después si algún proyecto los necesita o si superan la auditoría de valor diferencial.

## 4. Las 22 mejoras identificadas con Animate UI

**Regla de integración:** shadcn conserva la responsabilidad funcional y visual; Animate UI se utiliza para el movimiento. «Integrar» es una decisión de catálogo propuesta; **no significa que la compatibilidad esté probada o que se pueda reemplazar siempre con un único import**.

### 4.1. Formularios y controles (7)

| # | Componente base | Mejora de Animate UI | Decisión |
|---:|---|---|---|
| 1 | `Select` | Apertura/cierre animados e indicador de opción seleccionada | Integrar |
| 2 | `Checkbox` | Transición del check, dibujo o efecto de aparición | Integrar |
| 3 | `Switch` | Transición fluida entre activado y desactivado | Integrar |
| 4 | `Combobox` | Aparición animada de resultados y feedback de selección | Integrar |
| 5 | `Radio Group` | Indicador animado al cambiar de opción | Integrar |
| 6 | `Slider` | Movimiento y respuesta visual del control | Integrar |
| 7 | `Progress` | Transición animada de progreso/valor | Integrar |

### 4.2. Navegación (5)

| # | Componente base | Mejora de Animate UI | Decisión |
|---:|---|---|---|
| 8 | `Tabs` | Indicador deslizante y transiciones de paneles | Integrar |
| 9 | `Dropdown Menu` | Apertura/cierre fluidos y estados de selección | Integrar |
| 10 | `Navigation Menu` | Transición entre vistas y submenús | Integrar |
| 11 | `Pagination` | Cambio visual animado del indicador de página | **Integración manual** |
| 12 | `Sidebar` | Expansión, colapso y resaltado de navegación | **Integración manual** |

### 4.3. Ventanas y elementos emergentes (7)

| # | Componente base | Mejora de Animate UI | Decisión |
|---:|---|---|---|
| 13 | `Dialog` | Escala, desplazamiento, entrada/salida y overlay | Integrar |
| 14 | `Alert Dialog` | Animación de diálogos de confirmación | Integrar |
| 15 | `Sheet` | Entrada/salida de paneles laterales | Integrar |
| 16 | `Drawer` | Entrada/salida de paneles deslizantes | Integrar |
| 17 | `Popover` | Transiciones de contenido contextual | Integrar |
| 18 | `Tooltip` | Entrada suave, escala y otros efectos contextuales | Integrar |
| 19 | `Hover Card` | Aparición y desaparición de tarjeta contextual | Integrar |

### 4.4. Contenido y notificaciones (3)

| # | Componente base | Mejora de Animate UI | Decisión |
|---:|---|---|---|
| 20 | `Accordion` | Expansión y contracción del contenido | Integrar |
| 21 | `Collapsible` | Apertura y cierre fluidos | Integrar |
| 22 | `Toast` | Entrada/salida, apilamiento y transición de estados | Integrar, **sujeto a validación de compatibilidad con el proveedor de notificaciones** |

**Total: 7 + 5 + 7 + 3 = 22.**

## 5. Siete capacidades adicionales de Animate UI

Estas **sí son entradas adicionales propuestas para el catálogo**. Algunas pueden implementarse como variantes de un componente ya existente y no tienen por qué aumentar en siete el número de paquetes públicos o APIs.

| # | Capacidad | Función | Cómo exponerla en la biblioteca | Prioridad |
|---:|---|---|---|---|
| 1 | `Animated Button` | Feedback de pulsación con escala/resorte | Variante `Button` animada | Alta |
| 2 | `Copy Button` | Copiar al portapapeles con confirmación visual | Componente o variante `CopyButton` | Alta |
| 3 | `Animated Icons` | Iconos que responden a interacción/estado | Kit de iconos animados | Media |
| 4 | `Counting Number` | Transiciones numéricas para KPIs y estadísticas | Utilidad `CountingNumber` | Alta |
| 5 | `Auto Height` | Transición fluida entre alturas de contenido | Primitiva de layout | Alta |
| 6 | `Scroll Fade` | Sombra/desvanecimiento en bordes de contenedores desplazables | Mejora opcional para `Scroll Area` | Media |
| 7 | `Page Transition` | Transición entre vistas o rutas | Utilidad de navegación de nivel aplicación | Media; depende del router y versiones |

### Enlaces oficiales de referencia

- **shadcn/ui:** https://ui.shadcn.com/docs/components
- **Animate UI — documentación:** https://animate-ui.com/docs
- **Animate UI — primitivas:** https://animate-ui.com/docs/primitives
- **Animate UI — Animated Button:** https://animate-ui.com/docs/primitives/animate-ui/button
- **Animate UI — Copy Button:** https://animate-ui.com/docs/primitives/animate-ui/copy-button
- **Animate UI — Animated Icons:** https://animate-ui.com/docs/icons/lucide-icons
- **Animate UI — Counting Number:** https://animate-ui.com/docs/primitives/animate-ui/counting-number
- **Animate UI — Auto Height:** https://animate-ui.com/docs/primitives/animate-ui/auto-height
- **Animate UI — Scroll Fade:** https://animate-ui.com/docs/primitives/animate-ui/scroll-fade
- **Animate UI — Page Transition:** https://animate-ui.com/docs/primitives/animate-ui/page-transition

> **Verificación pendiente:** comprobar en la versión exacta que se instale las rutas, APIs y compatibilidad de cada primitiva; la documentación web y los paquetes pueden evolucionar.

## 6. Política de diseño y comportamiento

### 6.1. Principios obligatorios

1. **Una fuente visual de verdad:** colores, tipografía, espaciados, sombras, bordes y radios se definen mediante tokens propios compatibles con Tailwind/shadcn.
2. **Feedback inmediato:** todo control interactivo tendrá estados pertinentes de `hover`, `focus-visible`, `pressed`, `disabled`, `loading`, `success` y `error` cuando aplique.
3. **Movimiento con propósito:** animar estados, navegación, relaciones espaciales o continuidad; no añadir efectos solo por decoración.
4. **Accesibilidad y adaptación:** navegación por teclado, objetivos táctiles adecuados y respeto por `prefers-reduced-motion`.
5. **Rendimiento:** animaciones interrumpibles, preferir `transform` y `opacity` cuando sea posible, evitar trabajos costosos en tablas grandes.
6. **Variantes, no duplicaciones:** un único `Button` estándar con variantes bien justificadas es mejor que tres botones casi idénticos de tres fuentes.
7. **Selección por valor diferencial:** los candidatos de Bencho UI y React Bits Free deben aportar experiencias nuevas o variantes intencionales; evitar introducir animaciones decorativas como dependencias obligatorias de toda la aplicación.

### 6.2. Perfiles de movimiento

| Perfil | Uso preferido | Idea central |
|---|---|---|
| **Sutil** | Sistemas empresariales y pantallas densas | Animaciones discretas y rápidas |
| **Natural** | Predeterminado | Feedback claro, movimiento coherente y fluido |
| **Expresivo** | Landing pages y experiencias premium | Interacciones más visibles sin comprometer usabilidad |

## 7. Decisiones técnicas iniciales

- **Aplicaciones destino:** React + TypeScript + Tailwind CSS.
- **Base UI / Radix / React Aria:** escoger **una** familia de primitivas predominante para mantener consistencia. La propuesta actual favorece Base UI, **pendiente de pruebas de compatibilidad** entre shadcn y Animate UI.
- **Motor de animación:** Motion cuando resulte apropiado; CSS para transiciones simples.
- **Distribución interna:** catálogo + registry propio + documentación y recetas de instalación.
- **Componentes especializados:** editores tipo Notion o grafos visuales se integrarán por proyecto cuando sean necesarios; no se incluirán por defecto.
- **Licencias:** documentar el origen y las restricciones de cada fuente antes de copiar, distribuir o publicar código. Esta fase solo fija la selección, no autoriza redistribuciones.

## 8. Pasos de implementación

- [ ] **Auditar las 42 entradas de shadcn/ui:** disponibilidad, API, dependencias y necesidades de accesibilidad.
- [ ] **Revisar las 22 mejoras de Animate UI** y comprobar compatibilidad real sobre un proyecto de prueba.
- [ ] **Probar las 7 capacidades adicionales** y decidir si se exponen como componentes, hooks o variantes.
- [ ] **Definir tokens y perfiles de movimiento** antes de modificar estilos de las fuentes.
- [ ] **Elegir y documentar los patrones de composición** (`Field`, `Data Table`, `Date Picker`, etc.).
- [ ] **Montar una galería interactiva** con estados, controles y pruebas responsive.
- [ ] **Registrar cada pieza** con categoría, origen, licencia, dependencias, API, nivel de calidad y capturas/demos.
- [x] **Preseleccionar 12 componentes de Bencho UI** y cotejarlos con la base funcional (pendiente validación de código).
- [x] **Preseleccionar 32 componentes gratuitos de React Bits** y clasificarlos por propósito (pendientes de instalación, pruebas de código y QA).

## 9. Criterios de aceptación de esta fase

- [ ] Los **42 componentes shadcn** aparecen en el inventario con categoría y prioridad.
- [ ] Las **22 integraciones Animate UI** tienen una asociación explícita a su componente base y un resultado de prueba (compatible, manual, bloqueado o descartado).
- [ ] Las **7 capacidades adicionales** cuentan con una propuesta de API y ubicación en el catálogo.
- [ ] No se cuentan las 22 integraciones como 22 componentes nuevos.
- [ ] Se identifica explícitamente la estrategia de notificaciones `Toast`/`Sonner`.
- [ ] Todos los componentes aprobados respetan tokens visuales y perfiles de movimiento.
- [ ] Se documentan permisos y restricciones de licencia antes de importar o distribuir el código.

---

## 10. Bencho UI — 12 componentes elegidos por el usuario

**Fuente:** https://bencho.dev/ — Consulta de sus páginas de bloque: 22 de octubre de 2026.  
**Decisión:** Mantener los 12 en el catálogo de candidatos. **No significa que el código esté importado ni que sus licencias, dependencias, compatibilidad, accesibilidad y rendimiento se hayan aprobado aún.**

### 10.1. Inventario normalizado y relación con nuestro stack

| # | Componente Bencho | Enlace oficial | Interacción verificada por descripción | Ubicación recomendada | Relación con shadcn / Animate UI | Tipo |
|---:|---|---|---|---|---|---|
| 1 | **Rolling Counter** | https://bencho.dev/blocks/rolling-counter | Número estilo odómetro: tocar, mantener pulsado, arrastrar y lanzar | `inputs/numeric` | **No sustituye** `Counting Number` de Animate UI (visualización de KPIs). Este controla un valor editable | **Nueva capacidad** |
| 2 | **Toast Stack** | https://bencho.dev/blocks/toast-stack | Avisos apilados que se separan con hover | `feedback/toast` | Se superpone a `Toast` / Sonner y a la animación de Animate UI; candidato a **variante de presentación**, no a segundo gestor de notificaciones | **Variante** |
| 3 | **Voice Note** | https://bencho.dev/blocks/voice-note | Mantener pulsado para grabar; deslizar para descartar; soltar y reproducir | `media/voice` | No existe equivalente directo en los 42 base | **Nueva capacidad** |
| 4 | **Upload Dropzone** | https://bencho.dev/blocks/upload-dropzone | Arrastrar archivo al área de subida; rechazo por exceso de tamaño | `forms/upload` | Complementa `Input`/`Field`; no implica backend de almacenamiento ya implementado | **Nueva capacidad** |
| 5 | **Slide to Confirm** | https://bencho.dev/blocks/slide-confirm | Deslizar hasta un umbral que completa la confirmación | `actions/confirm` | Alternativa gestual a `Alert Dialog`/`Button`; prever alternativa accesible por teclado | **Nueva capacidad** |
| 6 | **Picker Wheel** | https://bencho.dev/blocks/picker-wheel | Rueda de opciones con arrastre, desplazamiento, inercia y encaje | `forms/select` | Variante experimental de `Select`; mantener `Select` estándar para formularios densos | **Variante** |
| 7 | **Checklist** | https://bencho.dev/blocks/checklist | Marcar tareas con relleno, check dibujado y texto tachado | `tasks/checklist` | Combina `Checkbox` animado con presentación de lista de tareas | **Variante** |
| 8 | **Magnifying Dock** | https://bencho.dev/blocks/dock | Los iconos cercanos al cursor crecen según proximidad | `navigation/dock` | Nuevo patrón de navegación; **no sustituye** `Sidebar` para estructuras complejas | **Nueva capacidad** |
| 9 | **Pull to Refresh** | https://bencho.dev/blocks/pull | Tirar de una tarjeta/contenido para activar la actualización | `gestures/refresh` | Complemento para vistas móviles; manejar conflictos con scroll nativo | **Nueva capacidad** |
| 10 | **Create Menu** | https://bencho.dev/blocks/liq-create | Pastilla de acción que se transforma en menú de creación | `menus/create` | Variante expresiva de un menú de acciones / `Dropdown Menu` | **Variante** |
| 11 | **Search** (slug `seek`) | https://bencho.dev/blocks/seek | Icono de búsqueda que se expande hasta convertirse en campo | `inputs/search` | Variante de `Input` + `Command` para búsqueda compacta | **Variante** |
| 12 | **Slosh Slider** | https://bencho.dev/blocks/slosh | Relleno con sensación de peso que sobrepasa la posición al arrastrar rápidamente | `inputs/slider` | Variante visual/interactiva de `Slider`; conservar un único modelo de valor y API | **Variante** |

**Advertencia de nomenclatura:** `seek` en la URL original corresponde al componente **Search (expanding search bar)**, **no** a `Time Scrubber` ni a un reproductor multimedia. El componente `liq-create` se muestra como **Create Menu**, `picker` como **Picker Wheel** y `dock` como **Magnifying Dock**.

### 10.2. Decisiones para evitar duplicaciones

1. **Toast Stack:** conservar **un solo sistema de notificaciones**. Elegir un motor/estado (`Sonner`, primitiva Animate UI u otra opción probada) y adaptar el diseño Bencho como presentación opcional si es técnicamente compatible.
2. **Rolling Counter vs Counting Number:** exponer APIs distintas: `RollingNumberInput` cambia el valor y `CountingNumber` muestra una animación pasiva de cifras.
3. **Picker Wheel vs Select:** el primero será un selector especial para experiencias táctiles; el segundo sigue siendo el predeterminado para formularios accesibles.
4. **Checklist vs Checkbox:** `Checklist` es una composición para tareas; no debe introducir un nuevo tipo de dato booleano incompatible.
5. **Create Menu y Search:** implementar como recetas o variantes de componentes propios del sistema, manteniendo interacciones de foco y teclado.
6. **Slosh Slider vs Slider:** compartir semántica, límites, escalas, `onValueChange` y alternativa de teclado; el efecto de fluido es un skin, no un contrato de valor nuevo.
7. **Voice Note y Upload Dropzone:** separar los componentes de interfaz de los servicios reales (micrófono, permisos, subida, errores, seguridad, cancelación).
8. **Slide to Confirm:** no reemplazar una validación del lado del servidor ni imponer el gesto de arrastre como única forma de confirmar.
9. **Pull to Refresh:** dar alternativa de actualización por botón/teclado; probar móviles y scroll.
10. **Magnifying Dock:** definir interacción por foco y tacto, no exclusivamente hover.

### 10.3. Identificadores propuestos para el catálogo propio

```text
@my-ui/rolling-number-input
@my-ui/toast-stack        # Variante/presentador, no un segundo motor de toast
@my-ui/voice-note
@my-ui/upload-dropzone
@my-ui/slide-to-confirm
@my-ui/picker-wheel
@my-ui/checklist
@my-ui/magnifying-dock
@my-ui/pull-to-refresh
@my-ui/create-menu
@my-ui/expanding-search
@my-ui/slosh-slider
```

Los nombres anteriores **son propuestas de API propia**, no nombres de paquetes publicados por Bencho.

### 10.4. Trabajo pendiente de aceptación Bencho

- [x] Identificar los 12 componentes exactos y obtener enlaces canónicos.
- [x] Clasificar 6 capacidades nuevas y 6 variantes de patrones existentes.
- [ ] Leer implementación fuente y confirmar licencia de cada bloque, avisos y restricciones de redistribución.
- [ ] Evaluar dependencias, versiones de React y compatibilidad con Tailwind / sistema de tokens.
- [ ] Hacer pruebas de accesibilidad: teclado, `aria`, foco, táctil y `prefers-reduced-motion`.
- [ ] Validar rendimiento en móviles y scroll, especialmente Dock, Picker Wheel y Slosh Slider.
- [ ] Probar integración real sin duplicar el motor de toasts ni los modelos de estado.
- [ ] Incorporar los 12 candidatos como demos en la galería antes de aprobarlos para producción.

## 11. React Bits FREE — 32 componentes seleccionados (sin acceso Pro)

**Fuente oficial:** https://reactbits.dev/ — **verificación de catálogo: 22 de octubre de 2026.**  
**Alcance:** únicamente entradas con ficha pública del catálogo **React Bits gratuito** y opción de instalar/copiar fuente. Las 17 referencias a `pro.reactbits.dev` de la selección anterior **no forman parte de esta versión**.  
**Estado:** selección recomendada para pruebas e integración, **no significa implementación instalada o validación de QA**.

La selección prioriza la filosofía que buscamos: movimiento interactivo y feedback visual útil, amplia cobertura y mínima redundancia frente a shadcn/ui, Animate UI y Bencho UI. Se incluyen algunas variantes intencionales (por ejemplo, Tilted Card y Spotlight Card) porque tienen comportamientos distintos.

### 11.1. Tipografía e interacción textual (9)

| # | Componente | Documentación gratuita | Interacción / efecto | Uso sugerido | Solapamientos y criterio | Prioridad |
|---:|---|---|---|---|---|---|
| 1 | **Blur Text** | https://reactbits.dev/text-animations/blur-text | Revelado progresivo de texto desde desenfoque | Revelados suaves en heroes, titulares y secciones | Blur Highlight: parecido solo en el desenfoque; no resalta semánticamente palabras | Alta |
| 2 | **Decrypted Text** | https://reactbits.dev/text-animations/decrypted-text | Caracteres cifrados que se convierten en texto legible | Titulares tecnológicos y estados visuales de procesamiento | Alternativa de efecto a Cipher Reveal, no réplica | Alta |
| 3 | **Text Type** | https://reactbits.dev/text-animations/text-type | Efecto de escritura con cursor y cadencia configurable | Mensajes narrativos, chat, hero de IA | Alternativa parcial a Ghost Type, sin autocompletado fantasma equivalente | Alta |
| 4 | **Shuffle** | https://reactbits.dev/text-animations/shuffle | Revelado donde los caracteres se mezclan antes de asentarse | Titulares y cambios de copy | Se aproxima a Glyph Lottery, con otra mecánica | Media |
| 5 | **True Focus** | https://reactbits.dev/text-animations/true-focus | Transición de nitidez/desenfoque entre palabras | Enfatizar fragmentos de texto | Alternativa conceptual a Blur Highlight | Alta |
| 6 | **Text Pressure** | https://reactbits.dev/text-animations/text-pressure | Tipografía que se deforma según posición/presión del puntero | Hero expresivo con interacción directa | Sustituto creativo, no físico idéntico a Mesh Lettering | Alta |
| 7 | **Variable Proximity** | https://reactbits.dev/text-animations/variable-proximity | Letras alteran sus rasgos según la cercanía del cursor | Tipografía interactiva sutil o expresiva | Complementa Text Pressure; seleccionar variante según interacción | Media |
| 8 | **Scroll Velocity** | https://reactbits.dev/text-animations/scroll-velocity | Marquesina tipográfica cuya velocidad reacciona al scroll | Secciones de presentación y storytelling | Alternativa de ritmo a Speeding Text; no contador numérico | Alta |
| 9 | **Split Text** | https://reactbits.dev/text-animations/split-text | Revela caracteres/palabras por grupos con tiempos escalonados | Animación tipográfica general reutilizable | Base de animación; no reproduce Typographic Wall | Alta |

### 11.2. Componentes de interfaz, navegación y galerías (12)

| # | Componente | Documentación gratuita | Interacción / efecto | Uso sugerido | Solapamientos y criterio | Prioridad |
|---:|---|---|---|---|---|---|
| 1 | **Animated List** | https://reactbits.dev/components/animated-list | Lista con entrada animada y navegación por teclado | Feeds, historiales y listas de actividad | Coincide funcionalmente con Animated List del catálogo Pro | Alta |
| 2 | **Scroll Stack** | https://reactbits.dev/components/scroll-stack | Tarjetas que se fijan/apilan durante scroll | Narrativas, casos de uso, portfolios | Está disponible también en el catálogo gratuito | Alta |
| 3 | **Magic Bento** | https://reactbits.dev/components/magic-bento | Cuadrícula de tarjetas con luz y feedback al cursor | Secciones de funciones y landing premium | Composición sobre Card; no sustituye Card base | Alta |
| 4 | **Circular Gallery** | https://reactbits.dev/components/circular-gallery | Galería curva con drag, scroll, teclado y expansión de imágenes | Portfolios y exploración visual | Nueva experiencia de galería, no equivalente directo a Page Flip | Alta |
| 5 | **Masonry** | https://reactbits.dev/components/masonry | Galería masonry con reorganización animada y lightbox | Portfolios, colecciones y medios | Patrón especializado, no duplica Table | Alta |
| 6 | **Tilted Card** | https://reactbits.dev/components/tilted-card | Tarjeta 3D con tilt, glare, sombras y reverso | Fichas visuales y landing pages | Variante premium de Card, no reemplazo estándar | Media |
| 7 | **Spotlight Card** | https://reactbits.dev/components/spotlight-card | Card con iluminación que responde al cursor | Dashboards premium, features y CTAs | Variante visual sobre Card, ligera en alcance conceptual | Alta |
| 8 | **Card Swap** | https://reactbits.dev/components/card-swap | Pila de tarjetas 3D que rota con tiempo o gesto | Showcases, testimonios y presentaciones | Diferente de Scroll Stack; animación temporal/gestual | Media |
| 9 | **Stack** | https://reactbits.dev/components/stack | Pila de tarjetas que se arrastran o lanzan | Historias y galerías táctiles | Alternativa gestual, NO sustituto exacto de Page Flip | Media |
| 10 | **Gooey Nav** | https://reactbits.dev/components/gooey-nav | Navegación con indicador líquido entre destinos | Navegación corta y landing premium | Variante de Navigation Menu/Tabs, no sustituye navegación compleja | Alta |
| 11 | **Staggered Menu** | https://reactbits.dev/components/staggered-menu | Menú desplegable con entrada escalonada | Menús de campaña y navegación premium | Complementa Dropdown Menu estándar y Create Menu Bencho | Media |
| 12 | **Stepper** | https://reactbits.dev/components/stepper | Flujo por pasos con indicador y transiciones de resorte | Onboarding, asistentes y formularios largos | Patrón nuevo encima de Field/Form, no sustituye formulario | Alta |

### 11.3. Animaciones de interacción y composición (6)

| # | Componente | Documentación gratuita | Interacción / efecto | Uso sugerido | Solapamientos y criterio | Prioridad |
|---:|---|---|---|---|---|---|
| 1 | **Pixel Transition** | https://reactbits.dev/animations/pixel-transition | Reemplaza contenido mediante disolución de píxeles | Cambios de tarjeta, comparativas y galerías | No reemplaza Magic Transform ni Comparison Slider | Alta |
| 2 | **Electric Border** | https://reactbits.dev/animations/electric-border | Borde eléctrico que reacciona a la proximidad del cursor | Énfasis opcional sobre contenedores o CTAs | Variante de efecto, no nuevo Button | Media |
| 3 | **Animated Content** | https://reactbits.dev/animations/animated-content | Revelado de contenido al entrar en viewport | Secciones y bloques de landing | Usar como wrapper sobre componentes propios | Alta |
| 4 | **Magnet** | https://reactbits.dev/animations/magnet | Atracción magnética al puntero con retorno elástico | Botones CTA y objetos aislados | Efecto composable; no envolver formularios enteros | Alta |
| 5 | **Click Spark** | https://reactbits.dev/animations/click-spark | Feedback de partículas al hacer clic | Acciones celebratorias y microfeedback | Decorativo; no sustituye estados reales de éxito/error | Media |
| 6 | **Glare Hover** | https://reactbits.dev/animations/glare-hover | Reflejo que atraviesa superficies siguiendo el cursor | Tarjetas e imágenes premium | Variante de hover; evitar duplicarlo con Tilted Card | Media |

### 11.4. Fondos interactivos (5)

| # | Componente | Documentación gratuita | Interacción / efecto | Uso sugerido | Solapamientos y criterio | Prioridad |
|---:|---|---|---|---|---|---|
| 1 | **Aurora** | https://reactbits.dev/backgrounds/aurora | Fondo aurora suave que responde al cursor | Fondos de hero elegantes | Priorizar rendimiento y contraste | Alta |
| 2 | **Dot Grid** | https://reactbits.dev/backgrounds/dot-grid | Rejilla de puntos elástica con feedback al cursor/clic | Fondos técnicos y dashboards | Identidad dinámica sin sustituir contenido | Alta |
| 3 | **Orb** | https://reactbits.dev/backgrounds/orb | Orbe luminoso que reacciona a proximidad | Visual de IA, hero y fondos localizados | NO equivale al AI Blob Pro: no asume estados listen/think/speak | Alta |
| 4 | **Silk** | https://reactbits.dev/backgrounds/silk | Ondas satinadas que giran con el puntero | Héroes, portadas y showcases | Preferir solo un fondo costoso por vista | Media |
| 5 | **Iridescence** | https://reactbits.dev/backgrounds/iridescence | Superficie iridiscente líquida interactiva | Landing premium y experiencias inmersivas | Evaluar fallback estático de WebGL y reduced-motion | Media |

### 11.5. Relación con los componentes Pro originalmente propuestos

La lista anterior era una **preselección basada en demos Pro**, no una dependencia que debamos instalar. Esta versión la reemplaza por alternativas libres y mantenibles; los efectos no deben presentarse como equivalentes exactos.

| Necesidad planteada originalmente | Alternativa gratuita seleccionada | Cobertura real |
|---|---|---|
| Blur Highlight | True Focus + Blur Text | Similar en foco/desenfoque; no idéntico |
| Cipher Reveal | Decrypted Text | Revelado críptico similar |
| Ghost Type | Text Type | Escritura simulada; **no** sugiere texto fantasma |
| Glyph Lottery | Shuffle | Mezcla de letras; diferente física |
| Mesh Lettering | Text Pressure + Variable Proximity | Tipografía sensible al cursor; diferente modelado |
| Speeding Text | Scroll Velocity | Velocidad reactiva al scroll; **no** sustituto de contador |
| Typographic Wall | Split Text | Animación escalonada; **no** muro tipográfico |
| Scroll Stack | Scroll Stack | Mismo nombre y patrón disponible gratuitamente; revisar diferencias de versión |
| Animated List | Animated List | Patrón gratuito con navegación por teclado |
| Modal Cards | shadcn Dialog + Animate UI + Tilted Card | **Composición propia por implementar**, no un reemplazo gratuito 1:1 |
| Magic Transform | Pixel Transition | Solo transición visual; no visualización de pipeline documental |
| Hover Preview | shadcn Hover Card + Spotlight Card | **Composición propia** para previsualización, no componente idéntico |
| Comparison Slider | Sin equivalente incluido | **Brecha real:** implementar aparte al surgir necesidad |
| Page Flip | Stack / Card Swap | Movimiento de tarjetas, **no** páginas de libro |
| Frame Border | Electric Border | Borde animado con estilo diferente |
| Device | Sin equivalente incluido | **Brecha real:** mockup 3D especializado no seleccionado |
| AI Blob | Orb | Visual orgánico; estados de voz/IA por implementar aparte |

### 11.6. Duplicidades, API y rendimiento

1. **Counters:** `CountingNumber` de Animate UI sigue siendo contador pasivo y `RollingNumberInput` de Bencho es un input editable; no agregar `Count Up` o `Counter` de React Bits inicialmente por redundancia.
2. **Docks:** mantener como preselección principal `Magnifying Dock` de Bencho. El `Dock` gratuito de React Bits existe, pero **no se selecciona** para no mantener dos dársenas muy similares sin evaluación adicional.
3. **Cards:** exponer `Card` shadcn estándar y variantes visuales (`MagicBento`, `TiltedCard`, `SpotlightCard`), sin replicar semántica ni implementar un segundo sistema de tarjetas.
4. **Menús:** `Gooey Nav` y `Staggered Menu` son experiencias distintas, mientras `Create Menu` de Bencho es una acción contextual. No reemplazar `Navigation Menu`/`Dropdown Menu` accesibles.
5. **Listas y toasts:** `Animated List` representa contenido persistente en pantalla; `Toast Stack` de Bencho y Animate UI gestionan notificaciones efímeras. Evitar motores de notificaciones múltiples.
6. **Fondos/GPU:** cargar perezosamente shaders, detener render cuando no se ven, prever fallback estático o CSS, respetar `prefers-reduced-motion` y medir FPS y memoria en dispositivos modestos.
7. **Entrada alternativa:** hover, drag y cursor nunca deben ser el único medio de interacción: garantizar teclado, táctil y foco visibles en controles funcionales.
8. **Estilo unificado:** conectar tintes, colores, tamaño, espacios y tipos de letra a tokens; no forzar el mismo resorte a cada efecto gráfico de React Bits.

### 11.7. Instalación y licencia de React Bits gratuito

Documentación oficial:
- Catálogo general: https://reactbits.dev/get-started/index
- Catálogo de componentes: https://reactbits.dev/c/components
- Texto: https://reactbits.dev/c/text-animations
- Efectos: https://reactbits.dev/c/animations
- Fondos: https://reactbits.dev/c/backgrounds
- Instalación: https://reactbits.dev/get-started/installation
- Código fuente: https://github.com/DavidHDev/react-bits
- Licencia: https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md

**Importante:** "gratuito" no significa de dominio público ni libre de condiciones. El código fuente público utiliza **MIT + Commons Clause**: admite uso en aplicaciones personales/comerciales y adaptación, pero restringe redistribuir los componentes como producto/biblioteca para terceros; conservar los avisos. Nuestra biblioteca es **privada y de uso propio**. Si se llegase a publicar un registro de descarga o comercializar un UI kit, exigir revisión de licencia.

El sitio facilita componentes en variantes JavaScript o TypeScript y CSS o Tailwind. Por ejemplo, un componente gratuito verificable puede instalarse usando:

```bash
npx shadcn@latest add @react-bits/ScrollStack-TS-TW
npx shadcn@latest add @react-bits/AnimatedList-TS-TW
npx shadcn@latest add @react-bits/MagicBento-TS-TW
```

**No ejecutar estos comandos sin revisar dependencias y versiones del proyecto.** El código podrá personalizarse y documentarse para uso propio. Mantener referencia upstream y revisión/versión de incorporación para actualizarlo deliberadamente.

### 11.8. Pruebas pendientes de aceptación React Bits Free

- [x] Verificar en el catálogo oficial **32 componentes gratuitos** con categorías y links canónicos.
- [x] Descartar los **17 enlaces Pro** de la lista de implementación (2 nombres reaparecen como versiones gratuitas disponibles).
- [x] Documentar solapamientos con las otras tres bibliotecas y brechas que aún no cubrimos.
- [ ] Instalar las 32 entradas seleccionadas (o registrarlas inicialmente como `pending` si no están instaladas).
- [ ] Verificar APIs reales, dependencias, tokenización y licencias por versión/código fuente.
- [ ] Probar comportamientos con datos reales, teclado, móvil, reduced-motion y SSR/hidratación.
- [ ] Probar coste de efectos y fondos en móviles y navegadores sin WebGL.
- [ ] Integrar las piezas sin duplicar sistemas de navegación, notificación o estilos globales.
- [ ] Publicar las demos REALES en el servicio web privado con estado de implementación verificado.

## 12. Consolidación de las cuatro fuentes

| Fuente | Componentes o capacidades candidatas | Relación y alcance |
|---|---:|---|
| shadcn/ui | **42** | Componentes/patrones funcionales de base |
| Animate UI | **22 mejoras** | Se aplican sobre los 42 anteriores (**no** se cuentan como piezas nuevas) |
| Animate UI | **7 adicionales** | Capacidades/variantes propias |
| Bencho UI | **12** | Seis capacidades diferenciadas y seis variantes relacionadas con la base |
| React Bits **gratuito** | **32** | 9 texto + 12 UI/galerías + 6 efectos + 5 fondos |
| **Entradas candidatas, sin sumar mejoras** | **93** | 42 + 7 + 12 + 32 |

Las **93 entradas** constituyen un inventario preliminar, no 93 componentes ya implementados ni 93 APIs públicas independientes. Algunas serán variantes o wrappers de una API existente. Se mantienen **22 integraciones Animate UI** como mejoras asociadas, no nuevas entradas.

### Próximas decisiones

1. **Instalar y probar las 93 entradas candidatas** por fases, con demos reales y estados (`pending`, `implemented`, `validated`, `blocked`) verificables; no instalar todas en cada aplicación cliente.
2. **Definir tokens y APIs públicas** sobre shadcn, con perfiles de movimiento y reglas de accesibilidad/rendimiento.
3. **Construir el catálogo web privado** con demos, filtros, modo oscuro/claro, vista responsive, componentes reales y HMR en desarrollo.
4. **No depender de React Bits Pro**: ningún componente seleccionado necesita comprar una licencia Pro. Las brechas reales (Comparison Slider, Device, Page Flip, AI Blob con estados) se documentan; no fingir que están resueltas.
5. **Actualizar desde upstream mediante revisión controlada** de versiones y cambios, no sobreescribir adaptaciones locales automáticamente.
6. **Integración de agentes con el registro**: indexar variantes, origen, instalación, versiones, dependencias, licencia y cumplimiento de QA.

### Estado final del documento

- **Completado:** selección de 42 shadcn, 22 mejoras Animate UI, 7 adicionales, 12 Bencho y 32 React Bits gratuitos; enlaces a documentación y comparación conceptual.
- **No completado:** instalaciones reales, validación de compatibilidad, auditoría de código fuente, pruebas de rendimiento, adaptación visual y pruebas de integración.
