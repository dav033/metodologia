---
contract: planes
version: 1
status: draft
artifact: direction-exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
revision: 3
direction: a
name: Pliegues de consulta · Operativa
owner: David
date: 2026-10-27
source: planes@v1.r3.dir-a.tsx
mockup: planes@v1.r3.dir-a.html
chosen_thumbnail: planes@v1.r3.dir-a.html.candidate-1.html
---

# planes@v1 — r3 dirección a: Pliegues de consulta · Operativa

## 1. Identidad y trazabilidad

**Exploración en borrador, completa para comparación; no aprobada y no es el contrato canónico.** Este artefacto específico de dirección sigue el brief de comportamiento r3, el comportamiento actual de planes de acceso de SPEC y la respuesta de la ronda 13, SP-14 en PLAN.md/PLAN.json, y la dirección C elegida por el propietario. La clave de exploración `a` es un identificador de salida, no una reversión de la elección del propietario de Pliegues de consulta. Sólo se escriben archivos específicos de la revisión. Sólo el finalizador puede actualizar el par canónico tras la selección del propietario.

El alcance modificado elimina los controles de colapso de herramientas, repara la composición en tableta y añade selección informativa de planes. Conserva las bandas continuas, las listas completas acumulativas del catálogo, el índice dentro de la página, el shell de Pictures, las rutas de entrada/retorno y el comportamiento de moneda en ambos idiomas. No hay ninguna acción de compra, solicitud, contacto, suscripción, registro ni de plan de cuenta.

Impacto en consumidores: sólo SP-14 enlaza `ui.contract=planes`, `version=1`, la copia de diseño T14.1 y la revisión visual T14.5. T14.2 consume el comportamiento de comparación/selección/responsive; T14.3 consume los dos enlaces de entrada; T14.4/T14.6 verifican el comportamiento del navegador/catálogo. Respecto al borrador anterior es un **cambio visual incompatible** para T14.2 porque cambian la interacción y la estructura en tableta; los enlaces de T14.3 siguen siendo compatibles. Los contratos de catálogo/permisos de SP-1 y el contrato de cuentas de SP-2 no cambian. No se concede aprobación ni mutación de planes.

## 2. Propósito y usuarios

Cualquier visitante, con sesión o sin ella, compara Entusiasta, Designer, Designer Plus y Master Designer. Puede seleccionar opcionalmente un plan para comparación visual, volver a la comparación completa y volver a su superficie de entrada. La selección es un estado de presentación transitorio, independiente del rol asignado, el plan de cuenta, los permisos, la autenticación y el pago. No existe guardado ni confirmación de asignación de cuenta.

## 3. Arquitectura de información y jerarquía

Cabecera conservada → título de tarea de 24px con retorno contextual → índice compacto de planes y selector de vista → un papel con cuatro bandas de plan continuas → frase explicativa → pie de página existente. Cada banda tiene identidad/precio, leyenda de herramientas incluidas y su lista completa acumulativa de herramientas. Las listas siempre están visibles en los estados listo y seleccionado en ambas vistas. Las funciones no disponibles usan una etiqueta de texto visible debajo de su nombre. No hay ningún nivel promovido ni recomendación.

**Miniatura 1 elegida:** las bandas continuas con reglas conservan el orden de lectura elegido por el propietario y la alineación de identidad y herramientas. **Miniatura 2 conservada para comparación:** una hoja de dos columnas con bloques pares pierde el eje de lectura continuo y coloca listas avanzadas largas junto a listas base cortas. El candidato 1 encaja mejor con la composición C seleccionada. Ambos archivos de miniatura se crearon antes del TSX/compilación completa y contienen composiciones en miniatura reales, no listas textuales de dirección.

## 4. Sistema de diseño y lenguaje visual

Fuentes de producto de solo lectura: t12 login/page.tsx, LoginForm.tsx, globals.css, layout.tsx, CabeceraApp.tsx y MenuApp.tsx; fuente de tokens de diseño de asesor correspondiente; Markdown y HTML empaquetado de los hermanos cuentas-admin@v1, taller-esenciales@v1 y proyectos@v1. El shell de acceso seleccionado en SP-2 rige el contexto de inicio de sesión/cuenta por encima del antiguo inicio de sesión con contraseña compartida. Sus fuentes Geist de producción y los tokens generales de Pictures rigen la sección pública; los tokens específicos del taller no reemplazan los tokens públicos/de autenticación. Algunos HTML hermanos usan fuentes/diseños exploratorios anteriores; no se infiere ninguna marca nueva a partir de ellos.

| Fuente del proyecto | Rol en el kit | Claro / oscuro |
|---|---|---|
| --fondo | fondo | #faf9fc / #0b0c10 |
| --superficie | tarjeta, popover | #ffffff / #16181f |
| --texto | colores de primer plano | #1c1425 / #f4f5f7 |
| --texto-suave | muted-foreground | #6b6178 / #9aa1ad |
| --superficie-2 | secondary, muted, accent | #efe9f8 / #242733 |
| --acento | primary, ring | #6d3fe0 / #9479ff |
| --sobre-acento | primary-foreground | #ffffff / #120b24 |
| --acento-hover | primary-hover | #5530b8 / #a58dff |
| --borde, --borde-suave | bordes decorativos de paneles, separadores | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| --texto-tenue | borde de input/control, alias hermano existente | #766c85 / #8a91a0 |
| --error, --error-suave | texto/superficie destructivos | #b23a45, #ffeaec / #ff979f, #43252a |

Los archivos WOFF2 de Geist Sans/Geist Mono de producción se incrustan desde la compilación local existente de Next. Sin solicitudes de fuentes, imágenes, paquetes o recursos externos. Los roles de radio siguen SP-2: 32px papel, 24px recuadro, 18px campo, controles tipo píldora. Cuerpo 15px/1.5; título 24px/1.25/600; nombres de planes 20px/1.3/600; precios 22px/500 con cifras tabulares (20px en teléfono); herramientas 14px; texto de apoyo 12–13px. Sin nueva paleta ni familia tipográfica.

Componentes reales: `shadcn:button outline ready|pressed|focus|hover` de `@/components/ui/button` para selección/cambio de vista/reintento, `shadcn:button default ready|disabled|loading` para el contexto de formulario SP-2 conservado, `shadcn:input email|password` de `@/components/ui/input`, `shadcn:skeleton loading` de `@/components/ui/skeleton`. El Button instalado usa Base UI; sin fragmentos de respaldo. Las bandas de planes, las listas semánticas, el índice de anclas con ajuste de línea y el menú nativo con details son composiciones personalizadas del vocabulario de producto existente, no componentes nuevos de la biblioteca. Los selectores nativos de inspección los proporcionan mountMockup/useMockup de @kit/mockup; el perfil de movimiento proviene de @kit/motion.

### Tabla de dirección de ocho ejes

| Eje | Expresión renderizada |
|---|---|
| concepto | Lectura operativa de los Pliegues de consulta seleccionados por el propietario; información pública de planes sin mutación de cuenta. |
| diseño | Un papel continuo con cuatro bandas con filetes. En escritorio usa una columna de identidad de 240px; en tableta la identidad pasa sobre una lista de herramientas de dos columnas; en teléfono, una sola columna. |
| navegación | Índice de planes en la página con ajuste de línea y una vista de selección informativa separada; retorno contextual al inicio de sesión o a Mi cuenta; sin nuevo destino de aplicación en la navegación hermana. |
| tipografía | Geist Sans de producción; título de página de 24px, nombres de planes de 20px, precios tabulares de 22px (20px en teléfono), líneas de herramientas de 14px, texto de apoyo de 12–13px. |
| densidad | Lectura densa de catálogo agrupado con relleno de banda de 20px en escritorio y separación de 12px entre filas de herramientas; todas las herramientas acumulativas permanecen visibles. |
| componentes | Button, Input y Skeleton de Base UI/shadcn instalados; selector de idioma nativo y menú de cuenta desplegable conservados; bandas de planes, índice y listas de herramientas semánticos personalizados. |
| color | Tokens exactos claro/oscuro de globals.css de Pictures. Chrome y separadores neutros; el acento existente marca el resaltado de comparación y el foco de teclado. Sin nueva paleta. |
| movimiento | Registro horizontal preciso de bandas de 480ms con desfases de 35ms y ease-out (.23,1,.32,1), corte de índice en contradirección de 180ms, retroalimentación rápida al pasar el cursor y al presionar; perfiles natural/sutil y paridad con reducido/quieto. |

El movimiento es finito: band-cut traslada 10px a cero en 480ms con desfases de 35ms; index-cut se traslada 8px en sentido contrario en 180ms. El perfil natural usa 300/140ms, el sutil 160/100ms. La retroalimentación de los botones es rápida e interrumpible. Los grupos de herramientas conservan el resorte de Motion existente que depende del perfil. Las pestañas ocultas pausan las animaciones CSS. El movimiento reducido, Quieto y ?still=1 eliminan el desplazamiento y las transiciones, asientan las animaciones existentes y conservan toda la información/selección. Sin animaciones ornamentales en bucle.

## 5. Modelo de navegación e interacción

- El inicio de sesión contiene exactamente un enlace Planes/Plans con destino /planes. La vista previa estática abre la comparación sin sesión iniciada.
- El menú de cuenta desplegable con sesión iniciada contiene exactamente un enlace Planes/Plans con destino /planes, junto con las acciones conservadas Mi cuenta y cerrar sesión. Las variantes públicas no tienen menú de cuenta.
- El índice de planes enfoca el H2 de destino y desplaza su banda a la vista. Nunca cambia la selección ni oculta otras herramientas.
- Elegir para comparar / Choose for comparison cambia a la vista adicional. Cada plan tiene Seleccionar para comparar / Select for comparison, con un nombre accesible calificado por plan y aria-pressed. Seleccionar reemplaza solo el resaltado de comparación local; expone de inmediato una marca de verificación, un texto explicativo y un anuncio de estado.
- Volver a la comparación / Return to comparison conserva el resaltado elegido y muestra la comparación completa de cuatro planes, con todas las listas visibles. Una nueva carga de página borra la selección transitoria. El mockup usa memoria de módulo para conservarla entre cambios de vista de la vista previa; no se escribe ningún estado de cuenta ni de servidor.
- El enlace contextual de retorno regresa al inicio de sesión o a la misma superficie de entrada validada con sesión iniciada. Mi cuenta es el ejemplo estático con sesión iniciada; producción debe restaurar un destino seguro del mismo origen. Seleccionar un plan no cambia ese origen.
- El menú de cuenta se cierra con Escape y devuelve el foco a su resumen. Los cambios de vista enfocan el H1. Los enlaces son anclas reales con destinos de ruta/hash; la interceptación de clics estática evita solicitudes de red en el artefacto.

## 6. Flujos

F1: Inicio de sesión → Planes → leer cuatro planes ordenados y todas las herramientas → retorno contextual al inicio de sesión.

F2: Mi cuenta → menú de cuenta desplegable → Planes → leer la comparación → retorno contextual a Mi cuenta. Producción conserva la ruta de origen permitida real.

F3: Comparación → Elegir para comparar → seleccionar cualquier plan → aparecen el contorno/marca/estado de seleccionado → Volver a la comparación → los cuatro planes permanecen, con el elegido resaltado. No cambia ningún plan asignado, rol, permiso ni campo de cuenta.

F4: Navegador/ES seleccionado → COP / mes y Gratis; EN → USD / month y Free, con Entusiasta convirtiéndose en Enthusiast. Los demás nombres de planes se mantienen. Ninguna vista muestra ambas monedas. Un idioma distinto de ES/EN recurre a ES; la persistencia del idioma de la cuenta pertenece a SP-8.

F5: Cargando → bandas skeleton; vacío/error/sin conexión/incompleto → sin precios autoritativos parciales → reintentar → comparación/selección lista. El reintento estático simula un catálogo válido, no una respuesta de API en vivo.

## 7. Especificaciones de vistas

| Vista nativa | Superficie | Estructura visible y acciones |
|---|---|---|
| public | /planes sin sesión | Cabecera/idioma, Planes, retorno al inicio de sesión, índice, botón de vista adicional, cuatro bandas completas, explicación/pie de página |
| signed | /planes con sesión | Mismo contenido público, menú de cuenta desplegable, retorno contextual con sesión iniciada |
| choose | Subvista informativa de /planes sin sesión | Mismo shell/índice/bandas, título Elegir para comparar, explicación explícita de no mutación, un control de selección por plan, volver a la comparación |
| choose-signed | Subvista informativa con sesión | Mismo comportamiento de selección; la cuenta sigue igual y solo difieren el menú desplegable y el retorno |
| login | Contexto de entrada SP-2 | Papel de acceso centrado de 676px conservado, correo/contraseña/Entrar/indicación de restablecimiento; un enlace Planes. La autenticación sigue en el alcance de SP-2 |
| account | Contexto de entrada SP-2 | Papel de cuenta conservado y contexto de identidad personal/contraseña con menú de cuenta desplegable; un enlace Planes en el menú. Sin campo de plan editable |

Un único fixture de catálogo ilustrativo, claramente identificado por el pie de página del Mockup. La implementación lee SP-1 plan-catalogue@1; no debe copiar este fixture en un segundo catálogo de producción. Ninguna de las dos rutas de repositorio inspeccionadas contiene aún src/lib/planes/catalogo.ts; este es un productor futuro declarado, no una fuente de datos en vivo verificada.

| Plan ES / EN | Mensual ES | Mensual EN | Herramientas acumulativas completas |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Free | Chat con límites / Chat with limits; Contador de globos / Balloon counter; Catálogo / Catalogue |
| Designer | 20.000 COP / mes | 7 USD / month | Chat con límites más altos / Chat with higher limits; balloon counter; catalogue |
| Designer Plus | 45.000 COP / mes | 14 USD / month | Lista de Designer; Calculadora de costos / Cost calculator; Chat ampliado / Extended chat; Detección de estructuras / Structure detection; Detección avanzada de globos / Advanced balloon detection |
| Master Designer | 70.000 COP / mes | 25 USD / month | Lista de Designer Plus; Taller 3D / 3D workshop |

Chat ampliado, detección de estructuras y detección avanzada de globos muestran cada uno aún no disponible / not available yet bajo ambos planes superiores. La calculadora de costos está disponible. Taller 3D representa todo el editor de globos, incluido el explorador de decoraciones prediseñadas; no hay una línea separada para el explorador. Entusiasta/Designer difieren solo en la redacción cualitativa del chat; sin valor numérico de límite ni contador. Hay 21 filas de herramientas acumulativas y seis anotaciones de no disponible en cada vista completa. Texto explicativo: Cada plan incluye las herramientas del anterior. Un administrador asigna el plan. / Each plan includes the tools of the previous plan. An administrator assigns the plan.

## 8. Estados

El selector nativo visible Estado expone ready, highlighted, loading, empty, error, offline, partial y menu-open.

| Estado | Salida / recuperación |
|---|---|
| ready | Cuatro bandas y todas las listas acumulativas; la vista de selección adicional comienza sin selección en una carga nueva |
| highlighted | Designer Plus es una selección neutra del fixture; mismas herramientas, marca/estado en la vista de selección, contorno/etiqueta en la comparación; se puede seleccionar cualquier otro plan |
| loading | Región de catálogo con aria-busy, estado Cargando planes / Loading plans y cuatro skeletons de banda; sin precios inventados ni acción de selección habilitada |
| empty | Sin tarjetas de plan ni precios. Mensaje de catálogo no disponible y Reintentar/Try again; la ausencia es una condición de recuperación, no un quinto plan |
| error | Sin catálogo no confirmado. Encabezado de error, reintento y retorno contextual conservado |
| offline | Sin conexión/Offline e instrucción de conexión/reintento; sin precios obsoletos presentados como vigentes |
| partial | Sin datos no confirmados; reintento explícito, sin comparación de planes incompleta |
| menu-open | Menú de cuenta desplegable abierto con sesión iniciada; ausente en las variantes públicas; Escape lo cierra y devuelve el foco al resumen |

Los estados empty/error/offline/partial/loading aplican tanto a la comparación como a la selección. Los formularios de entrada son ilustraciones de contexto; solo se simula su contexto heredado de carga/error. La denegación de permisos, el éxito de compra, el registro, la asignación pendiente y la validación de mutación de cuenta no aplican a una sección pública informativa. El éxito de la selección se representa con el estado highlighted y el estado de status, no con una pantalla de compra exitosa. No existe ningún estado de herramienta colapsable.

## 9. Comportamiento responsivo

| Ancho | Diseño observable |
|---|---|
| 1101px+; verificado a 1280px | Márgenes externos de 40px; recuadro del papel de 28px. Columna de identidad de banda de 240px junto a una región de herramientas fluida de dos columnas. El índice de la barra de herramientas y el cambio de vista comparten una fila |
| 761–1100px; verificado a 768/820/1024px | Márgenes externos de 28px; recuadro del papel de 24px. La identidad/precio/control de selección opcional se ajustan por encima de la lista de herramientas de dos columnas. Sin columna lateral comprimida. La acción de la barra de herramientas pasa debajo del índice con ajuste de línea. Los cuatro planes mantienen el orden del documento |
| 360–760px; verificado a 390px | Márgenes externos/del papel de 20px. Los controles de cabecera se ajustan; el título y el retorno se apilan. El índice se convierte en un grupo de enlaces de dos columnas, los botones de cambio de vista y selección ocupan el ancho disponible. Cada plan apila nombre, precio, retroalimentación de selección opcional y herramientas completas en una columna. Sin carrusel ni tabla de comparación horizontal |

Sin desplazamiento horizontal de la página, precios recortados, controles de selección fuera de pantalla ni paneles de herramientas de altura fija. Las etiquetas se ajustan de forma natural en ES/EN. Se espera desplazamiento vertical para leer las listas acumulativas largas. La barra de planificación se ajusta independientemente del shell del producto.

## 10. Objetivos de accesibilidad

Objetivo WCAG 2.2 AA para el contenido aplicable. Semántica real de botones, orden de encabezados H1/H2, herramientas en ul/li, etiquetas de formulario asociadas, selects nativos etiquetados, enlace de salto, retorno de contexto y navegación de planes etiquetada. Los botones de selección exponen aria-pressed; el texto/marca/contorno de seleccionado no depende solo del color. Cambiar la selección anuncia su plan mediante role=status. Los errores usan role=alert; la carga usa aria-busy y status.

Teclado: Tab/Shift+Tab, Enter/Espacio en botones y en el menú desplegable, operación nativa de select, cierre del menú de cuenta con Escape, foco del índice de planes en el H2 de destino, foco al H1 en cambios de vista. Las acciones tienen una altura mínima de 44px; anillo de foco de 3px con desplazamiento de 4px. Texto objetivo ≥4.5:1, bordes de identificación de controles/foco ≥3:1. Los filetes decorativos de fila no necesitan identificar controles. El foco del teclado y el contenido permanecen visibles cuando el movimiento está reducido. La aceptación completa con lectores de pantalla, en distintos navegadores y con zoom de 200–400 % sigue siendo verificación de implementación, no una afirmación de conformidad del diseño.

## 11. Criterios de aceptación visual y verificación

| ID | Breakpoint | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 390/768/820/1024/1280px | listo | Las cuatro bandas están ordenadas Entusiasta, Designer, Designer Plus, Master Designer |
| UI-AC-02 | todos los soportados | listo/resaltado | Se ven las 21 filas acumulativas de herramientas; no hay control para ocultar/mostrar herramientas |
| UI-AC-03 | todos los soportados | listo ES | Los precios son Gratis, 20.000/45.000/70.000 COP por mes; sin USD |
| UI-AC-04 | todos los soportados | listo EN | El primer plan es Enthusiast/Free; los valores de pago son 7/14/25 USD por mes; sin COP |
| UI-AC-05 | todos los soportados | listo/resaltado | Ambos planes superiores muestran las tres anotaciones de no disponibilidad en el idioma activo |
| UI-AC-06 | todos los soportados | listo | El chat usa una redacción cualitativa del límite y no muestra ninguna cuota numérica |
| UI-AC-07 | todos los soportados | elegir | Cada plan tiene un botón de selección de comparación calificado con el plan |
| UI-AC-08 | todos los soportados | elegir resaltado | El botón seleccionado tiene aria-pressed=true, marca de verificación y estado con nombre |
| UI-AC-09 | todos los soportados | volver desde elegir | La comparación completa conserva exactamente un contorno/etiqueta de elegido y todas las filas de herramientas |
| UI-AC-10 | todos los soportados | cualquier plan | No existe ningún control de compra, solicitud, contacto, registro o asignación de cuenta |
| UI-AC-11 | 761–1100px | listo/elegir | La identidad queda sobre dos columnas fluidas de herramientas, sin una barra lateral estrecha de identidad |
| UI-AC-12 | 390px | listo/elegir ES/EN | Las listas de herramientas son de una sola columna y el ancho del documento no excede el viewport |
| UI-AC-13 | 1280px | listo | La identidad mide 240px junto a herramientas en dos columnas, en una sola hoja continua |
| UI-AC-14 | todos los soportados | inicio de sesión | Un enlace Planes abre la comparación sin sesión; al volver se regresa al inicio de sesión |
| UI-AC-15 | todos los soportados | cuenta/menú abierto | Un enlace Planes del menú abre la comparación con sesión; al volver se restaura el contexto de entrada |
| UI-AC-16 | todos los soportados | público/elegir | No se muestra ningún desplegable de cuenta con sesión iniciada |
| UI-AC-17 | todos los soportados | cargando | Cuatro bandas skeleton y una presentación de ocupado/estado reemplazan los precios/la selección |
| UI-AC-18 | todos los soportados | vacío/error/sin conexión/parcial | No se muestran precios de plan sin confirmar; reintentar restaura el contenido listo |
| UI-AC-19 | todos los soportados | índice por teclado | Activar un enlace del índice enfoca el H2 de ese plan sin ocultar herramientas |
| UI-AC-20 | todos los soportados | movimiento reducido/estático | No hay animación de desplazamiento continua; las herramientas y la selección de comparación siguen siendo utilizables |
| UI-AC-21 | todos los soportados | ambos temas | Se mantienen la paleta/Geist existentes de Pictures, el encabezado, el radio y el vocabulario del pie de página |
| UI-AC-22 | todos los soportados | listo | Master tiene una sola línea de Taller 3D, sin una línea separada de explorador |

### Evidencia offline real

- Constructor offline: `python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build <design>/planes@v1.r3.dir-a.tsx --out <design>/planes@v1.r3.dir-a.html` → exit 0, 562 KB, 2031 archivos fuente; React/Base UI/shadcn/Motion reales instalados, empaquetados localmente.
- Contraste: `python3 <kit>/kit/contrast.py <design>/planes@v1.r3.dir-a.html` → exit 0, 158 pares verificados en claro y oscuro, todos aprueban.
- Auditoría final del snapshot: `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py <design>/planes@v1.r3.dir-a.html --widths 1280,1024,820,768,390 --max-combos 192` → exit 0, **480 renders / 480 combinaciones planificadas**, 14.260 mediciones de texto, 608 paradas de foco. Sin muestreo.
- **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- Sonda complementaria de comportamiento con Playwright: **80 layouts listos** = cuatro vistas de plan × cinco anchos × ambos temas × ES/EN. Cada caso tiene cuatro planes, las 21 filas de herramientas, seis etiquetas de no disponibilidad, la única moneda correcta, la presencia correcta del menú de cuenta y ningún desplazamiento horizontal de la página. La selección real y la selección preestablecida persisten al volver; ambos enlaces de entrada/retorno, cinco estados de fallo/carga, el reintento y el foco del índice H2 aprueban. Páginas monitoreadas: cero errores de página y cero solicitudes HTTP.
- Inspección de capturas en memoria: escritorio 1280px claro/oscuro, teléfono 390px claro/oscuro y selección en tablet 820px oscuro. Se inspeccionaron visualmente la hoja final renderizada, las columnas de herramientas responsivas, los bordes de los botones y la retroalimentación de selección; no se escribieron archivos de captura. Los selectores nativos siguen visibles fuera del contenido del producto.

`<kit>` es `/home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit`. La auditoría inicial exitosa midió el snapshot previo al refinamiento de bordes (14.204 mediciones de texto); la evidencia final anterior proviene de una auditoría completa nueva tras reconstruir los bordes mejorados de los botones claros y la persistencia de la selección preestablecida. Ningún resultado anterior sustituye al snapshot final.

El alcance de construcción/auditoría es solo el artefacto estático. No se ejecutó lint, typecheck, pruebas ni build de aplicación de producción porque no se cambiaron archivos de producción. Un mockup no establece autenticación real, mutación de catálogo, permisos, solicitudes al servidor ni integración de rutas de origen seguro. T14.2–T14.6 conservan esas responsabilidades.

## 12. Preguntas abiertas y supuestos

**Preguntas abiertas para el responsable: ninguna para este comportamiento acotado.** La pregunta q1 de la ronda 13 está respondida: la selección solo resalta la comparación y nunca asigna un plan de cuenta. La frase de asignación por parte del administrador, el nivel base gratuito, la redacción cualitativa del chat, el trío de no disponibles y la línea única de Master 3D/explorador están confirmados. No se difiere ninguna decisión al implementador.

Supuestos: la vista adicional es local a /planes y no necesita una nueva entrada de menú de nivel superior ni una API de persistencia. La selección es transitoria entre cambios de vista y se borra en una carga nueva; nunca se obtiene de la cuenta ni se guarda en ella. Mi cuenta es el ejemplo explícito de retorno seguro; producción valida el origen real. El fixture estático de cuenta sigue siendo Entusiasta mientras se selecciona cualquier plan de comparación. El idioma del navegador inicia el producto; cambiar el selector de idioma visible es una vista previa del control de idioma existente. No se inventa nuevo texto legal/de marketing, cliente con nombre, fecha ni promoción.

CONCERNS: la aprobación del responsable/del plan sigue pendiente. El fixture estático de catálogo y los formularios de entrada son ilustrativos; la ruta de catálogo de producción está planificada, no presente en los worktrees inspeccionados. Todos los artefactos canónicos y hermanos, los repositorios de proyecto y los planes permanecen intactos. La única escritura adicional fuera de los seis artefactos de exploración es el RESULT.json de delegación explícitamente requerido. Esta exploración debe ser seleccionada/finalizada antes de que T14.1 consuma un snapshot canónico aprobado.
