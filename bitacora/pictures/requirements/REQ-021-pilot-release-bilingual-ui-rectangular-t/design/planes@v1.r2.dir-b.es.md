---
name: Paneles de consulta
contract: planes@v1
subplan: SP-14
revision: r2
direction: b
status: draft
artifact: independent-exploration
owner: David
created: 2026-10-27
---

# Paneles de consulta — exploración espacial B

## 1. Identidad y trazabilidad

Esta es una **exploración no aprobada**, no el contrato canónico `planes@v1`. La instrucción final de exploración con alcance definido sustituye la solicitud anterior de salida canónica. La selección anterior de la dirección C por parte del responsable se conserva como historial; esta nueva propuesta espacial no la reemplaza ni la aprueba. No se modifica ningún contrato compartido, elemento hermano, historial, SPEC, PLAN ni código de producción. La solicitud explícita posterior del hook Stop registra esta dirección únicamente en el registro diario existente de la sesión; no introduce ninguna decisión nueva ni elemento pendiente.

Alcance: SP-14, R17–R20 y el comportamiento de selección respondido en la ronda 13. Fuente de verdad: `planes@v1.r2.behavior.md`, SHA-256 `3f69cc0a465ac74b71a63cf247d9b1d38dbb87e0139ab13b8e52076fdf0b8239`. Contexto: SPEC actual (incluida “Behavior — SP-14 extra view”), PLAN/SP-14, `/tmp/REQ-021-planes-feedback-1.md` y los tres contratos/HTML de elementos hermanos proporcionados. La superficie de cuenta del elemento hermano seleccionado es **Parte de acceso**; la asignación de tokens de producción tiene prioridad sobre el estilo exploratorio anterior del HTML del elemento hermano.

Inspección del producto de solo lectura: variables globales/tema de ambos worktrees registrados, inicio de sesión t12/LoginForm/layout, CabeceraApp y MenuApp; superficie del menú de cuenta planificada proporcionada por SP-2. Los worktrees asignados aún no contienen el archivo del catálogo del plan. Por lo tanto, esta vista previa utiliza un único fixture explícito en memoria del catálogo que contiene los cuatro nombres, precios y listas de herramientas del requisito. Esto no demuestra que producción consuma el catálogo de SP-1.

Consumidores: SP-14 `ui.contract=planes`, versión 1, T14.1 textos del diseño, T14.2 página y T14.3 enlaces de entrada; T14.5 aceptación visual. SP-1 sigue siendo el propietario de los datos. El P-207 existente está cerrado: la fila compartida Catálogo debe aparecer en todos los planes, según lo confirmado por SPEC/T1.2 actual; esta exploración sigue esa redacción ya resuelta. SP-2 es responsable del inicio de sesión y las superficies de cuenta; esta dirección solo agrega su entrada a Planes e ilustra el contexto existente. La integración del navegador T14.4 y la auditoría T14.6 siguen siendo evidencia de ingeniería, fuera de esta tarea de diseño.

## 2. Propósito y usuarios

Los visitantes, con o sin sesión, comparan los cuatro planes de acceso acumulativos sin comprar, solicitar acceso, registrarse ni modificar ninguna cuenta. La vista adicional responde qué plan destacar durante la comparación, no cuál asignar. El uso satisfactorio consiste en consultar todas las herramientas y precios en el idioma actual, destacar opcionalmente un plan y volver a la comparación, y salir por el contexto de entrada original.

## 3. Arquitectura de información y jerarquía

Reproducir la marca Pictures compacta de anillo y punto, la etiqueta Sempertex, el control de idioma, el menú desplegable de cuenta para usuarios autenticados, el título sobrio de página, la regla horizontal de navegación y el pie del piloto de invitación establecidos por el contrato seleccionado de SP-2. Reorganizar únicamente el contenido nuevo de planes.

Comparación: título/volver → Comparar / Seleccionar para comparar → frase informativa sobre la selección → comentario opcional sobre el plan seleccionado → índice local de nombres de planes → una hoja continua con Entusiasta, Designer, Designer Plus y Master Designer. Cada fila tiene una columna de identidad/precio y la lista completa de herramientas acumuladas. No hay botones para ocultar herramientas, acordeones, listas truncadas, insignias de plan recomendado ni paneles de marketing.

Selección: el mismo marco y navegación horizontal → explicación explícita de que la selección solo sirve para comparar → resumen opcional del plan seleccionado/acción para volver → cuatro opciones nativas de radio, con todos los precios y listas de herramientas visibles → opción para volver a la comparación incluso si no se seleccionó nada. El plan seleccionado tiene un borde y un estado textual; en el fixture normal no se preselecciona un ganador. El estado del radio no representa el plan asignado a una cuenta.

### Evidencia y elección de la propuesta

Ambas composiciones en miniatura se prepararon e inspeccionaron primero a 1280px, antes de crear la vista de entrada completa:

- **Miniatura elegida:** `planes@v1.r2.dir-b.html.candidate-1.html`. Un índice local junto a filas horizontales de identidad/herramientas conserva un único orden de lectura y hace explícita la reorganización para tabletas. Las listas completas ocupan una hoja compartida en vez de cuatro columnas estrechas.
- `planes@v1.r2.dir-b.html.candidate-2.html`: paneles de planes completos en una cuadrícula de dos por dos. Se conserva como evidencia de una alternativa; la disposición de opciones equivalentes funciona bien en la vista adicional de selección por radio, mientras que la primera composición es una hoja de referencia principal más sólida.

Las miniaturas son estudios estáticos de composición, no contratos de interacción auditados. Los estados completos, temas y controles están en el TSX/HTML creado.

## 4. Sistema de diseño y lenguaje visual

La paleta y las fuentes del proyecto son fijas. Se integran las fuentes reales de producción **Geist Sans** y **Geist Mono** desde los recursos WOFF2 locales existentes de Next; no se descargan recursos ni paquetes. Geist Sans es la familia del cuerpo y los controles del producto. Mono está disponible, pero no se incorpora como una nueva jerarquía visual. La barra de inspección Mockup independiente del entorno de ejecución conserva su propia apariencia de planificación.

| Token de Pictures | Función en el kit | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta/menú emergente | #ffffff / #16181f |
| `--texto` | primeros planos | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | atenuado/secundario | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | principal / texto sobre el principal | #6d3fe0 / #ffffff; #9479ff / #120b24 |
| `--acento-suave` | acento | #ece3fb / #241f3d |
| `--borde`, `--borde-suave` | bordes decorativos / separadores de filas | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | bordes de entrada/control | #766c85 / #8a91a0 |
| `--acento` | anillo | #6d3fe0 / #9479ff |
| `--error` | destructivo | #b23a45 / #ff979f |

Las formas repiten el vocabulario seleccionado de SP-2: paneles de papel/opciones de 32px, comentario/menú de 24px, campos/elementos de índice de 18px y controles tipo píldora; márgenes internos de 28px en escritorio y 20px en teléfonos. La navegación neutra usa un subrayado del color del texto. El acento identifica el elemento de comparación seleccionado y la única acción local para volver. Los indicadores de disponibilidad de texto usan el texto atenuado existente, en vez de un estilo deshabilitado de bajo contraste.

### Tabla de ocho ejes

| Eje | Expresión visualizada |
|---|---|
| concepto | Una referencia pública de planes organizada como una hoja espacial de consulta; la selección para comparar es local, reversible e independiente de la asignación a una cuenta. |
| disposición | Un índice de planes de 180px junto a una hoja redondeada con cuatro filas horizontales; cada fila empareja identidad/precio con su lista completa de herramientas. La vista adicional de selección usa cuatro opciones completas en una cuadrícula de dos por dos. |
| navegación | Encabezado Pictures/Sempertex conservado, navegación horizontal entre comparación/selección, índice de anclas por nombre de plan, enlaces existentes de inicio de sesión/cuenta y retorno explícito a la comparación completa. |
| tipografía | Geist Sans existente e integrada: título de página y precios de 24px, nombres de planes de 20px, herramientas de 14px, metadatos de disponibilidad/mensualidad de 12px; precios tabulares. Sin nuevas familias ni estilos de visualización. |
| densidad | Una superficie de comparación compartida con márgenes internos de fila de 28px y separación entre herramientas de 24px; listas completas en lugar de paneles desplegables. En tabletas se conserva una columna de identidad de 200px y una columna de herramientas; en teléfonos, cada fila se apila. |
| componentes | Button, Input y Skeleton reales de shadcn/Base UI instalados, marca de anillo y punto de producción, selector de idioma nativo, menú de cuenta basado en details y selección de radio nativa dentro de paneles redondeados del subplan. |
| color | Tokens semánticos exactos de Pictures para los modos claro/oscuro, incluidos acento/sobre-acento para controles principales y selección; navegación de secciones neutra e indicadores de disponibilidad legibles en texto-suave. Sin cambios en la paleta. |
| movimiento | Alternancia en la entrada horizontal de filas, paneles de selección que se acomodan verticalmente, entrada breve del resumen de selección y respuesta reversible al pasar el cursor/presionar. Desfase expresivo de 520ms/65ms, controles de 180ms; equivalencia entre los perfiles y los modos de movimiento reducido/sin movimiento. |

### Procedencia de componentes reales

| Componente / variantes / estados | Importación instalada |
|---|---|
| `shadcn:button default, outline default/hover/focus/pressed` | `@/components/ui/button` |
| `shadcn:input email/password default/focus` | `@/components/ui/input` |
| `shadcn:skeleton loading` | `@/components/ui/skeleton` |
| `kit:mockup native view/state/theme/motion selectors` | `@kit/mockup` → suministrado real/runtime/mockup.tsx |
| `kit:motion profile/reduced state` | `@kit/motion` → suministrado real/runtime/motion.tsx |

El índice, la hoja de planes, las opciones de radio nativas y los detalles de cuenta son composiciones semánticas personalizadas que usan el vocabulario existente del producto; no se presentan como componentes originales del kit. Lucide proporciona los iconos Check/Circle/UserRound/return. La maqueta completa no tiene una biblioteca alternativa de componentes HTML; las miniaturas son composiciones nativas deliberadamente reducidas.

El movimiento usa la curva existente `--ease-out` (.23,1,.32,1). Expresivo: entrada de filas/paneles de 520ms, desfase de 65ms, desplazamiento de 28px y controles de 180ms; natural: 300/35/14/140; sutil: 160/15/4/100. Las filas impares/pares de escritorio entran desde lados opuestos; las opciones de selección se acomodan verticalmente; los paneles de estado entran desde −8px; los bordes de selección se acomodan desde una escala de .985. El texto permanece opaco durante toda la animación. Al pasar el cursor, los elementos del índice se desplazan 3px; al presionar el botón, su escala es .98. Sin efectos decorativos perpetuos. El movimiento reducido, Quieto y `?still=1` eliminan desplazamientos/animaciones; las pestañas ocultas pausan el movimiento CSS.

## 5. Navegación y modelo de interacción

Las entradas de producción siguen siendo **`/login` → `/planes`** y el menú desplegable de cuenta existente → **`/planes`**. Los enlaces HTML conservan href reales a `/planes`, `/login`, `/cuenta`; los controladores impiden la navegación solo para operar las vistas previas sin conexión. El retorno de producción debe conservar la ruta segura de origen; esta maqueta muestra `/login` y `/cuenta` como sus dos orígenes acotados, sin imponer `/cuenta` como destino para todas las páginas del producto.

La comparación y la selección son dos modos dentro de la página `/planes`, no una ruta de marketing añadida ni otro elemento de navegación global. Los botones nativos de una navegación con etiqueta identifican el modo actual con `aria-current=page`. Los cambios de modo enfocan el encabezado de la página. El índice de nombres de planes desplaza la página hasta la sección de destino y le da el foco. En pantallas estrechas, el índice pasa por encima del contenido; nunca se convierte en un carrusel con desplazamiento horizontal.

La selección por radio solo cambia el resaltado local de comparación. Las teclas de flecha permiten elegir otro radio del grupo; Tab permite salir del grupo. Al volver, se conserva el resaltado elegido; «Quitar selección» lo elimina. Ni seleccionar ni quitar la selección modifica la identidad de la persona autenticada, los datos de cuenta, las herramientas concedidas ni los permisos. No se representa ninguna API de asignación a cuentas. El menú de cuenta conserva Mi cuenta / Cerrar sesión y agrega Planes una sola vez; Escape lo cierra y devuelve el foco al resumen. En la sección pública de planes no aparece ningún rol de personal ni clave de permiso.

## 6. Flujos

1. **Comparación pública:** Iniciar sesión → Planes → cuatro planes/herramientas completas → Volver a iniciar sesión. No se requiere autenticación.
2. **Comparación con sesión iniciada:** menú desplegable existente de Mi cuenta → Planes → comparación → volver a Mi cuenta. En producción, la misma entrada funciona desde cualquier marco existente de sesión iniciada y vuelve al origen.
3. **Solo destacar:** Seleccionar para comparar → elegir cualquier opción de radio → estado textual «Seleccionado para comparar» → Volver a la comparación → fila correspondiente con borde y etiqueta → Quitar selección restaura la hoja completa sin resaltados. No hay pasos de registro, compra, solicitud ni asignación.
4. **Inglés:** usar el selector de idioma existente en el fixture de inspección → todo el contenido de los planes cambia a inglés, Entusiasta pasa a ser Enthusiast y los precios se muestran solo en USD; se conservan el modo y la selección. El idioma inicial de producción sigue al navegador según R20.
5. **Recuperación del catálogo:** marcadores de posición de carga → catálogo normal, o explicación de error/vacío/sin conexión con Reintentar → fixture normal. Esta acción simula la recuperación; la política real de red/caché sigue siendo responsabilidad de la implementación.

## 7. Especificaciones de vistas

| `view` nativa | Estructura y acciones | Requisito |
|---|---|---|
| `comparison` | Comparación pública, sin menú de cuenta, retorno al inicio de sesión, cuatro filas completas de planes, índice y modo de selección | R17/R18/R20 |
| `comparison-account` | El mismo contenido de referencia con el menú desplegable de cuenta y retorno a su origen de cuenta ilustrado | R18/R19/R20 |
| `selection` | Vista pública de cuatro opciones con botones de selección, todas las listas completas de herramientas, confirmación de selección y retorno a la comparación completa | Ronda 13 respondida |
| `selection-account` | La misma selección limitada a la comparación con la interfaz de sesión iniciada; el plan asignado a la cuenta sigue siendo Entusiasta | Ronda 13 respondida |
| `login` | Formulario de acceso centrado de 676 px de SP-2, etiquetas/ayuda/pie existentes, un enlace agregado a Planes | R19 |
| `account` | Contexto de la propia cuenta de SP-2, estructura existente de identidad/contraseña/ayuda/aviso y menú desplegable de cuenta que incluye Planes | R19 |

Los formularios de inicio de sesión y de la propia cuenta son ilustraciones contextuales de los puntos de entrada, no un rediseño ni una implementación del comportamiento de autenticación/contraseña de SP-2. Sus flujos independientes de error/éxito/aviso siguen siendo responsabilidad exclusiva del contrato de SP-2; las opciones de estado globales del catálogo no modifican estos formularios contextuales. La identidad del fixture es neutra y está marcada explícitamente como simulada. La página completa de planes es pública para todas las cuentas; nunca filtra la comparación según los derechos de acceso.

| Plan | Precio mensual ES | Precio mensual EN | Herramientas acumuladas visibles |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Gratis | Chat con límites / Chat con límites; Contador básico de globos / Contador básico de globos; Catálogo / Catálogo |
| Designer | 20.000 COP por mes | 7 USD por mes | Chat con límites más altos / Chat con límites más altos; el mismo contador básico y catálogo |
| Designer Plus | 45.000 COP por mes | 14 USD por mes | Herramientas de Designer más Chat extendido / Chat extendido, Calculadora de costos / Calculadora de costos, Detección de estructuras / Detección de estructuras, Detección avanzada de globos / Detección avanzada de globos |
| Master Designer | 70.000 COP por mes | 25 USD por mes | Todas las herramientas de Designer Plus más Taller 3D / Taller 3D |

Chat extendido, detección de estructuras y detección avanzada de globos tienen cada uno **“aún no disponible” / “aún no disponible”** debajo, en ambos planes superiores. La calculadora de costos está disponible; no se muestra ningún valor numérico de límite de chat. Taller 3D incluye el editor completo y el explorador de decoraciones listas para usar; no hay una línea adicional para el explorador. La tabla anterior documenta ambos idiomas; el producto renderizado muestra un solo idioma/moneda a la vez. El fixture está centralizado y se reutiliza entre modos; los datos de producción deben provenir del catálogo de SP-1, en lugar de copiar este fixture en una página.

## 8. Estados

| `state` nativo | Contenido aplicable | Comportamiento observable |
|---|---|---|
| `normal` | Cuatro modos de planes | Las cuatro listas completas de herramientas; no se resalta inicialmente ningún plan en una página nueva; la selección se puede cambiar de forma interactiva |
| `selected` | Cuatro modos de planes | El ejemplo de inspección resalta Designer Plus e indica que la selección es solo para comparar; no afirma que sea el plan de la cuenta |
| `loading` | Cuatro modos de planes | Cuatro filas de esqueleto para nombres/precios/herramientas y el estado etiquetado Cargando planes; no se inventan precios ni herramientas desconocidos |
| `empty` | Cuatro modos de planes | No hay planes disponibles, explicación de que el catálogo no está disponible y Reintentar; sin acción de asignación/compra |
| `error` | Cuatro modos de planes | No pudimos cargar los planes en una alerta, explicación de recuperación y Reintentar; no se muestra como actual ningún precio factual obsoleto |
| `offline` | Cuatro modos de planes | Sin conexión, explicación para conectarse y consultar, y Reintentar; no se inventan precios almacenados en caché |

Cada estado declarado tiene un control nativo de inspección. Las vistas con contexto de autenticación permanecen en estado normal cuando se inspeccionan estados no relacionados del catálogo. No corresponden estados independientes de éxito “guardado”, permiso denegado, pago, validación, asignación pendiente ni actualización de cuenta: la superficie pública no realiza mutaciones ni acepta datos personales enviados. La confirmación de selección es su único estado de finalización. Las herramientas no disponibles siguen siendo información legible, no controles de compra deshabilitados. No se muestra un conjunto parcial/obsoleto de planes como si fuera un catálogo completo; los datos del catálogo inutilizables siguen el flujo de recuperación de error/vacío.

## 9. Comportamiento adaptable

Ancho mínimo admitido: **360px**, en consonancia con SP-2 seleccionado. Anchos probados: 360, 390, 768, 1024 y 1280px. Ambos idiomas y temas se reorganizan sin desplazamiento horizontal de toda la página; el desplazamiento vertical es intencional para mostrar las listas completas.

| Rango | Comparación | Selección / estructura compartida |
|---|---|---|
| 1101px+ | Márgenes exteriores de 40px; índice local fijo de 180px + área de contenido flexible, con separación de 32px; identidad de cada fila de 180–220px y herramientas en dos columnas | Dos paneles de opciones de planes completos por fila, herramientas en dos columnas; márgenes internos de panel de 28px; encabezado compacto del producto |
| 761–1100px | Márgenes de 28px; el índice pasa a mostrar controles con nombres que se ajustan en cuatro columnas sobre un área de contenido de ancho completo; identidad de 200px junto a **una** columna de herramientas | Dos opciones por fila, con herramientas en una sola columna; márgenes internos de opción de 24px; el encabezado se ajusta según sea necesario |
| 360–760px | Márgenes de 20px; índice en dos columnas, identidad de cada plan sobre una lista completa de herramientas en una sola columna; márgenes internos del área de contenido de 20px | Una opción de radio completa por fila; confirmación/acción apiladas; encabezado del producto y controles de idioma/cuenta se ajustan; paneles de 20px; sin pie de página flotante fijo |

La solución para tabletas nunca comprime cuatro columnas completas de herramientas en una sola vista. El índice no oculta planes ni reemplaza las listas completas. Los precios y Master Designer se ajustan al espacio disponible en lugar de truncarse. Los formularios de cuenta/inicio de sesión conservan el ancho máximo centrado de 676px y el eje interno existente de 620px cuando hay espacio; en teléfonos se contraen dentro de márgenes de 20px.

## 10. Objetivos de accesibilidad

Objetivo: WCAG 2.2 AA para la superficie implementada; esta exploración no es un certificado de conformidad. La estructura semántica de navegación/sección/encabezados/listas, los selectores nativos etiquetados, el grupo de opciones de radio con leyenda, el estado marcado visible y el texto de estado de selección proporcionan estructura para el teclado y las tecnologías de asistencia. Las actualizaciones de estado usan role=status; los errores de carga usan role=alert. Los controles suelen tener una altura ≥44px; las etiquetas de radio abarcan las áreas completas de nombre/precio alrededor del control de radio visual de 22px. El color se complementa con el estado del control de radio y el texto de selección. El foco del teclado usa un contorno de énfasis de 2px con un desplazamiento de 3px; las secciones/encabezados de destino reciben foco programático tras la navegación. No hay gestos obligatorios de arrastre, divulgación de contenido de herramientas solo al pasar el cursor, carrusel horizontal ni acción de selección oculta.

El texto y los controles se midieron en ambos temas. Se verificó la reorganización completa entre 360 y 1280px, en ES/EN. Con el movimiento reducido se conserva el mismo contenido/controles y no hay animaciones en curso. Los anuncios reales de lectores de pantalla, la restauración del origen/al volver atrás en el navegador, los ajustes de zoom, el comportamiento del foco en distintos navegadores y los errores impulsados por el servicio requieren verificación durante la implementación.

## 11. Criterios de aceptación visual y verificación transparente

| ID | Punto de quiebre | Estado | Expectativa observable |
|---|---|---|---|
| B-AC-01 | 360px+ | normal, público | Se conservan el encabezado de Pictures con anillo y punto, la etiqueta Sempertex y el control de idioma existente; no aparece la divulgación de cuenta |
| B-AC-02 | 360px+ | normal, sesión iniciada | La divulgación de cuenta existente contiene Mi cuenta, exactamente un enlace a Planes y Cerrar sesión |
| B-AC-03 | 360px+ | comparación | Los cuatro encabezados aparecen en el orden del catálogo y todas las listas completas de herramientas están visibles sin activar divulgaciones |
| B-AC-04 | 360px+ | ES | Se muestran Gratis y 20.000/45.000/70.000 COP por mes; USD no aparece |
| B-AC-05 | 360px+ | EN | Se muestran Enthusiast/Gratis y 7/14/25 USD por mes; COP no aparece |
| B-AC-06 | 360px+ | normal | Cada uno de los dos planes superiores marca tres herramientas no disponibles; la calculadora y Taller no se marcan como no disponibles |
| B-AC-07 | 1101px+ | comparación | Un índice de nombres de planes de 180px aparece junto a una hoja redondeada con cuatro filas horizontales de planes |
| B-AC-08 | 761–1100px | comparación | El índice aparece sobre la hoja; cada fila tiene una columna de identidad de 200px y una columna de herramientas legible |
| B-AC-09 | 360–760px | comparación | La identidad/precio antecede a cada lista de herramientas en una columna; el índice local tiene dos columnas |
| B-AC-10 | 761px+ | selección | Cuatro opciones de radio forman dos columnas, cada una con su lista acumulativa completa de herramientas |
| B-AC-11 | 360–760px | selección | Las cuatro opciones completas se apilan en el orden del catálogo y ninguna acción se extiende fuera de la vista |
| B-AC-12 | 360px+ | al seleccionar | La opción de radio solo añade un borde/estado de comparación; al volver, se resalta la misma fila en la comparación completa |
| B-AC-13 | 360px+ | selected | Quitar selección elimina el resaltado mientras las cuatro listas siguen visibles |
| B-AC-14 | 360px+ | loading | Cuatro grupos de esqueleto y un estado de carga reemplazan los nombres/precios/herramientas que aún no se han resuelto |
| B-AC-15 | 360px+ | empty/error/offline | Aparecen la explicación del catálogo y Reintentar, sin precios inventados ni acciones de cuenta |
| B-AC-16 | 360px+ | enlaces de entrada | El enlace Plans del inicio de sesión y la opción Planes del menú de sesión iniciada tienen hrefs /planes y abren la comparación en la vista previa |
| B-AC-17 | 360px+ | teclado | El índice de planes lleva el foco a su destino; la operación de flechas de las opciones de radio, volver y borrar funcionan sin puntero |
| B-AC-18 | 360px+ | ambos temas | El borde de selección, el texto, los campos nativos y el indicador de foco se distinguen del fondo real |
| B-AC-19 | 360px+ | expresivo | La entrada de filas/opciones/estados realmente se anima con el tiempo documentado; los selectores de evidencia de movimiento identifican estos elementos |
| B-AC-20 | 360px+ | reducido/sin movimiento | El contenido llega a la misma posición final sin animaciones en curso y con controles utilizables |
| B-AC-21 | 360px+ | todas las vistas de planes | No aparecen controles de compra/solicitud/registro/asignación, límites numéricos de chat ni controles para ocultar herramientas |

### Comandos y resultados observados

Raíz de la herramienta: `/home/david/dev/metodologia/skill`; raíz del kit: `<tool>/agents/designer/skills/david-ui-kit`. Todos los comandos se ejecutaron sobre **la salida final de esta dirección**. No se instalaron paquetes, no hubo descargas ni se inició ningún servidor.

1. `python3 <tool>/scripts/bitacora.py components status` → installed=True, built=True, **96/96 entradas correctas**.
2. `python3 <tool>/scripts/bitacora.py components mockup build <design>/planes@v1.r2.dir-b.tsx --out <design>/planes@v1.r2.dir-b.html` → **413 KB, 2031 archivos fuente, sin conexión**, código de salida 0.
3. `python3 <kit>/kit/contrast.py <design>/planes@v1.r2.dir-b.html` → **contraste: 158 pares comprobados en modo claro y oscuro, todos aprobados**, código de salida 0.
4. `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.r2.dir-b.html --max-combos 100` → **144 renderizados (144 combinaciones planificadas), 3896 mediciones de texto, 448 paradas de foco**, código de salida 0. Esta es la matriz completa de 6 vistas × 6 estados × 2 temas × 2 anchos, no un muestreo.

**RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**

Comprobación complementaria en caché con Playwright/Chromium sobre el HTML final: **120 casos de reflujo APROBADOS** (6 vistas × 5 anchos × 2 temas × 2 idiomas), orden exacto de los cuatro planes, cuatro listas completas y seis etiquetas de indisponibilidad en los modos de planes, moneda exclusiva, cuatro flujos de selección/retorno, operación de flechas de botones de selección nativos, comportamiento de borrar selección, enlaces href de entrada a /planes, identidad/rol Entusiasta simulado sin cambios, foco del índice y paridad de movimiento reducido. **0 solicitudes HTTP(S) y 0 errores de página.** Esto solo demuestra el comportamiento de la vista simulada; no se implementa la autorización/persistencia de cuentas.

Se inspeccionaron visualmente capturas de pantalla en memoria sin escribir archivos de imagen adicionales: ambas propuestas; comparación de escritorio de 1280 px en modo claro y selección con sesión iniciada en modo oscuro; comparación de tableta de 768 px en modo oscuro; selección EN en modo claro y comparación ES en modo oscuro en teléfono de 390 px. La tableta muestra cuatro filas completas y legibles, sin desbordamiento. En dispositivos móviles, las listas se apilan, las etiquetas traducidas se ajustan a varias líneas y ambos temas conservan la jerarquía de precios/herramientas. Las capturas son evidencia de la vista previa, no aceptación de producción.

Una inspección inicial de solo lectura de la vista de cuenta del elemento hermano utilizó una opción de selector incorrecta y agotó el tiempo de espera; la lectura de la lista real de opciones identificó `cuenta`, y la inspección se completó correctamente. Fue un error del comando de inspección de la fuente, no un fallo de la dirección ni de sus auditorías. La primera auditoría completa de la dirección fue aprobada; la auditoría final anterior se volvió a ejecutar después de alinear el texto del contexto de cuenta y las rutas href con SP-2. Las estadísticas de auditorías anteriores no se presentan como evidencia final. La auditoría final de filas del catálogo también incluye la línea Catálogo compartida de P-207, ya resuelta, en los cuatro planes; esto corrige la omisión inicial del fixture de exploración sin reabrir la decisión del responsable.

No se ejecutaron lint, comprobaciones de tipos, pruebas ni compilación de producción, ni pruebas de enrutamiento/catálogo en vivo, porque el código de producción es de solo lectura y no se modificó. Esta vista previa estática no permite afirmar que la mutación de cuentas sea segura en un servicio real.

## 12. Preguntas abiertas, supuestos e impacto

**Preguntas abiertas de producto para la persona responsable: ninguna.** La ronda 13 resolvió la ambigüedad sobre selección/asignación. La decisión de diseño y la eventual aprobación del contrato/plan siguen siendo una instancia de aprobación independiente de la persona responsable; completar esta exploración no implica ninguna aprobación.

Confirmado: cuatro planes/precios/orden; herramientas visibles acumulativas; tres herramientas no disponibles en ambos planes superiores; comportamiento bilingüe de moneda/nombre; sin límites numéricos; Taller/editor/explorador completos bajo Master Designer; sin compra/solicitud/registro ni modificaciones de cuenta; sin controles para ocultar herramientas; y una disposición legible específica para tabletas.

Supuestos limitados al artefacto: una única fixture centralizada del catálogo; el resaltado/idioma local se conserva entre modos de maqueta, pero no tras recargar el navegador; el estado de inspección seleccionado inicializa Designer Plus únicamente para la revisión; los estados de error/vacío/sin conexión son simulaciones seleccionables; los controles de autenticación/contraseña son ilustraciones contextuales de SP-2. Producción debe usar el catálogo autoritativo, el idioma del navegador y el origen de retorno real seguro. No se introduce ninguna divulgación pública de claves de permisos/roles de personal ni ninguna operación oculta del servidor.

La compatibilidad queda **sin determinar hasta que se elija una dirección**. Si se adopta, la jerarquía de comparación/selección y la estructura para tabletas/teléfonos requieren la implementación de SP-14 T14.2 y la revisión renderizada T14.5; T14.3 solo agrega los enlaces ya requeridos. SP-1 no cambia, y esta exploración no modifica los contratos seleccionados de SP-2 ni los de sus pares SP-3/SP-4. Este es un borrador listo para comparar y alineado con el comportamiento; el contrato canónico de planes permanece intacto.

PREOCUPACIONES: siguen pendientes la elección/aprobación de la persona responsable y la integración en producción. No quedan ambigüedades materiales de comportamiento sin resolver, fuentes de tokens faltantes, constructores no disponibles, dependencias de respaldo ni auditorías de maqueta sin ejecutar. El artefacto estático no demuestra la sincronización del catálogo, los permisos del servidor, la restauración del historial del navegador, la autenticación activa ni el cumplimiento completo de WCAG.
