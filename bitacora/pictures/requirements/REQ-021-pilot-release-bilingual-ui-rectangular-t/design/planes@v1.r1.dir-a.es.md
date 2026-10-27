---
contract: planes
version: 1
revision: r1.dir-a
status: draft
kind: exploration
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
name: Registro de herramientas
chosen_thumbnail: planes@v1.r1.dir-a.html.candidate-1.html
---

# Registro de herramientas — dirección A

## 1. Identidad y trazabilidad

Solo exploración de planificación, **borrador sin aprobar**. Esta es evidencia específica de una dirección, no el contrato canónico `planes@v1`. No se escribió ningún contrato, plan, repositorio, vista previa ni registro de cambios compartido. El propietario elige la dirección; la finalización y la aprobación son etapas separadas.

El alcance es `planes@v1.r1.behavior.md`, R17–R20 y el SP-14 actual. SPEC.md y PLAN.json son entradas contextuales. El brief prevalece sobre el texto histórico de SPEC, que etiqueta de forma inconsistente la calculadora de costos como no disponible: el brief actual requiere que el chat extendido, la detección de estructuras y la detección avanzada de globos no estén disponibles, y que la calculadora de costos esté incluida en Designer Plus. SP-1 produce el catálogo. Los consumidores de SP-14 son T14.1 (copiar el diseño aprobado), T14.2 (planes públicos), T14.3 (enlaces de acceso) y T14.5 (revisión visual). Esta exploración no cambia esos contratos ni tareas.

## 2. Propósito y usuarios

Los visitantes comparan cuatro planes de acceso sin iniciar sesión. Las personas con sesión iniciada abren la misma información desde su menú de cuenta. El objetivo es leer el precio mensual en la moneda de la interfaz, distinguir las herramientas incluidas de las que aún no están disponibles y volver a la página de origen. Aquí nada permite comprar, solicitar, suscribirse, registrarse ni asignar un plan.

## 3. Arquitectura de información, enfoque y miniatura elegida

El área modificada se encuentra bajo el encabezado principal existente de Pictures/Sempertex. Orden: título de la página y enlace contextual de regreso → índice de anclas de planes → un registro dividido → notas sobre planes acumulativos y asignación por administrador → pie de página existente del piloto/mockup.

Cada fila contiene el nombre del plan y el precio mensual, todas las herramientas incluidas actualmente y las herramientas que aún no están disponibles. Se repiten las herramientas acumulativas disponibles para que los lectores no tengan que reconstruir los niveles anteriores. La etiqueta de chat con límites más altos sustituye a la de chat con límites más bajos, en vez de mostrar dos chats. Master Designer solo agrega la línea Taller 3D, que cubre todo el editor, incluido su explorador. No se agrega una línea separada para el explorador.

Se prepararon dos composiciones visuales antes de la entrada completa:

- **Candidato 1, seleccionado:** `planes@v1.r1.dir-a.html.candidate-1.html`, cuatro filas de planes con columnas compartidas. Mantiene el precio y la disponibilidad en el mismo grupo de lectura y se puede adaptar a una pila sin una matriz con desplazamiento horizontal.
- Candidato 2: `planes@v1.r1.dir-a.html.candidate-2.html`, herramientas en filas y planes en columnas. Comparar una sola herramienta es más rápido, pero las etiquetas de chat extensas y los estados de no disponibilidad hacen más exigente la adaptación a teléfonos. Esta miniatura es un boceto descartado, no un entregable adaptable auditado.

El mockup completo desarrolla el candidato 1. Se adapta a un producto para trabajar con herramientas de decoración: listas informativas, precios precisos, etiquetas claras repetidas y navegación habitual. No agrega jerarquía de landing, nivel destacado, insignia de recomendación ni beneficios inventados.

## 4. Sistema de diseño fijo y ocho ejes

Fuentes de solo lectura: `src/app/globals.css` y los archivos de layout/tema de ambos repositorios; inicio de sesión de t12, LoginForm, CabeceraApp y MenuApp; archivos Markdown/HTML relacionados de `cuentas-admin@v1`, `taller-esenciales@v1` y `proyectos@v1`. El diseño de cuenta elegido tiene prioridad sobre la pantalla de inicio de sesión anterior, que solo aceptaba contraseña. El TSX reutiliza los estilos CSS del shell de SP-2 seleccionado en `cuentas-admin@v1.amend-1.tsx`, con solo adiciones acotadas a SP-14. La fuente modificada y la fuente canónica relacionada establecen el mismo encabezado principal, control de idioma, formularios redondeados y selector de cuenta nativo.

Los tokens no se reemplazan. Fondo/primer plano del kit se asignan a `--fondo/--texto`; tarjeta/ventana emergente, a `--superficie`; primario/anillo, a `--acento`; primer plano primario, a `--sobre-acento`; atenuado, a `--superficie-2`; primer plano atenuado, a `--texto-suave`; borde, a `--borde`. Al igual que en el diseño relacionado, el control `--input` usa el token existente más intenso `--texto-tenue` y `--rule` usa `--borde-suave`. Los valores equivalentes para modo claro de lienzo/superficie/texto/acento son #faf9fc/#ffffff/#1c1425/#6d3fe0; para modo oscuro son #0b0c10/#16181f/#f4f5f7/#9479ff. El texto primario en modo oscuro es #120b24. No se agrega una nueva paleta, familia tipográfica ni identidad de marca.

Los archivos WOFF2 existentes de Geist y Geist Mono se importan desde los recursos locales de compilación de Next y se empaquetan como URI de datos; no se solicita ninguna fuente. Los radios del shell compartido, el espaciado de paneles y formularios y los selectores nativos se mantienen como en SP-2. Los repositorios de producción se consultaron en modo de solo lectura.

| Eje | Decisión específica de la dirección |
|---|---|
| concepto | Un registro operativo: compara el contenido completo de cada plan de acceso, sin jerarquía de ventas. |
| diseño | Cuatro filas horizontales de planes en un panel compartido; plan/precio, herramientas disponibles y herramientas no disponibles forman tres columnas en escritorio. Cada fila se apila en teléfonos. |
| navegación | Un índice local de cuatro anclas de planes lleva el foco al encabezado del plan elegido; un enlace contextual de regreso conduce a la pantalla de acceso o a la superficie de cuenta de origen. El selector de cuenta existente agrega un enlace a Planes. |
| tipografía | Geist y Geist Mono existentes, integradas localmente; título de página/precios de 24 px, nombres de planes de 19 px, herramientas de 14 px y etiquetas de disponibilidad de 12 px. Los precios en teléfonos son de 21 px. |
| densidad | Un registro dividido en lugar de cuatro tarjetas promocionales; todas las herramientas acumulativas se repiten explícitamente. Los grupos compactos de filas muestran tanto el precio como la disponibilidad, sin controles expandibles. |
| componentes | Button e Input reales de shadcn/Base UI, Skeleton real, selector de cuenta nativo existente de SP-2, marcas de verificación de lucide insertadas en línea y listas semánticas. La fila comparativa es una composición personalizada, no un componente de biblioteca inventado. |
| color | Los tokens semánticos de Pictures no cambian en modo claro ni oscuro; shell y filas neutrales, texto atenuado para las herramientas no disponibles y el acento existente solo para enlaces, foco y controles primarios existentes. |
| movimiento | Registro preciso: desplazamiento horizontal de 12 px para las filas durante 240 ms con Expressive, desfases de 35 ms entre filas y expansión de la línea de .65 a 1 durante 360 ms. Los subrayados del índice usan transformaciones de 150 ms. El movimiento reducido o estático muestra el estado final de inmediato; las pestañas ocultas suspenden el movimiento CSS. |

Inventario de componentes reales: `shadcn:button` default/outline de `@/components/ui/button`; `shadcn:input` de correo electrónico/contraseña de `@/components/ui/input`; `shadcn:skeleton` de carga de `@/components/ui/skeleton`. `mountMockup/useMockup` provienen de `@kit/mockup`; el perfil/el estado de movimiento reducido, de `@kit/motion`. No se necesitó una alternativa de HTML-kit, instalar paquetes ni obtener recursos externos. El registro, las anclas nativas y el selector de cuenta existente son composiciones personalizadas explícitas.

## 5. Navegación e interacción

Los selectores nativos de inspección son Vista (`view`), Estado (`state`), Tema (`theme`) y Movimiento (`motion`); no hay ningún diálogo en este alcance. Se mantiene la etiqueta visible Mockup. El selector de idioma del encabezado es el control existente del producto, no un selector de moneda adicional. Las vistas de planes exponen explícitamente las combinaciones ES/EN y con/sin sesión iniciada.

El índice local desplaza la página hasta un plan y lleva el foco a su encabezado; no cambia ningún derecho de acceso. En este prototipo, el enlace de regreso restablece la superficie de acceso/cuenta. En producción, se conserva la superficie de origen segura del mismo dominio y se desplaza la página y enfoca el contenido si esta se abrió desde el sitio; las cargas directas vuelven a `/login` sin sesión iniciada o a `/cuenta` con sesión iniciada. No se debe usar una URL de retorno externa arbitraria. El mockup muestra `/cuenta` como origen con sesión iniciada; no se simulan otros destinos de herramientas.

El selector de cuenta nativo conserva la semántica de SP-2 en lugar de simular un menú ARIA. Incluye Mi cuenta, el enlace agregado a Planes y Cerrar sesión. Escape lo cierra y devuelve el foco a su elemento de resumen; un clic fuera también lo cierra. No aparece si no hay sesión iniciada. La sección pública no muestra nombres de roles del personal o personalizados ni claves de permisos. La cuenta de ejemplo es Cuenta Entusiasta, no una persona real.

## 6. Flujos

1. Pantalla de acceso → su único enlace a Planes → registro de cuatro planes sin sesión iniciada → volver al acceso.
2. Mi cuenta → abrir el selector de cuenta existente → su única entrada a Planes → el mismo registro con el selector de cuenta → volver a Mi cuenta.
3. Vista de planes en inglés → nombres, herramientas y estados en inglés, y solo precios en USD → cambiar el idioma a ES → mismo orden y herramientas, y solo precios en COP.
4. Índice local de planes → el encabezado seleccionado recibe el foco y se desplaza para quedar despejado de la barra de herramientas del mockup. El teclado y el puntero usan el mismo destino.
5. Catálogo cargando, con error, vacío o incompleto → estado veraz y acotado → Reintentar restablece el ejemplo completo. Ningún dato de plan se inventa para completar una respuesta faltante.

Los cambios de inicio de sesión/contraseña se heredan del contexto de SP-2. Los controles de formulario solo simulan el flujo del ejemplo; este diseño no redefine la autenticación, las reglas de contraseña, la aceptación de avisos ni la seguridad de sesión. El mockup independiente no afirma usar autenticación, almacenamiento ni red.

## 7. Especificaciones de las vistas y contenido exacto

| Vista nativa | Superficie | Contenido |
|---|---|---|
| planes-es | Pública `/planes`, sin iniciar sesión | Entusiasta, Designer, Designer Plus, Master Designer; Gratis, COP 20.000, COP 45.000, COP 70.000; por mes. |
| planes-en | La misma, en inglés | Enthusiast, Designer, Designer Plus, Master Designer; Free, USD 7, USD 14, USD 25; por mes. |
| planes-es-cuenta | `/planes` con sesión iniciada | El mismo registro en español, con el aviso de cuenta existente. |
| planes-en-cuenta | La misma, en inglés | El mismo registro en inglés, con el aviso de cuenta existente. |
| login | Superficie de acceso existente de SP-2 | Encabezado existente, texto de acceso solo por invitación, campos de correo electrónico/contraseña e instrucciones para iniciar sesión y restablecer la contraseña; un enlace añadido a Planes. |
| account | Superficie existente de la cuenta propia | Fixture neutral `entusiasta@prueba.local`, formulario y aviso de cuenta existentes con un enlace a Planes. |

Entusiasta: Chat con límites / Chat with limits; Contador de globos / Balloon counter. Designer: Chat con límites más altos / Chat with higher limits; el mismo contador. Designer Plus: esas herramientas de Designer más Calculadora de costos / Cost calculator; Chat extendido / Extended chat, Detección de estructuras / Structure detection y Detección avanzada de globos / Advanced balloon detection indican cada uno **aún no disponible / not available yet**. Master Designer repite esas herramientas y estados, y agrega Taller 3D / 3D workshop. No se indican límites numéricos de chat, un beneficio separado de explorador ni promesas de servicio inventadas.

El registro es una instantánea de datos del informe, solo para el mockup. `src/lib/planes/catalogo.ts` no existe en el checkout t12 inspeccionado: producción debe consumir el catálogo de SP-1 en lugar de copiar constantes del fixture o codificar precios/disponibilidad de forma independiente. Las actualizaciones basadas en el catálogo deben cambiar los nombres, precios, nombres de herramientas y estados de manera conjunta, sin editar las páginas. Esta integración de datos no queda demostrada con un mockup estático.

## 8. Estados

- **normal / Disponible:** los cuatro planes y las listas completas de herramientas; sin acciones de conversión.
- **cargando / Cargando:** cuatro grupos de componentes Skeleton reales, etiqueta accesible de carga, sin precios ni controles de compra/asignación. El índice no aparece mientras los encabezados no estén disponibles.
- **vacio / Catálogo vacío:** “No hay planes disponibles.” / “No hay planes disponibles.” con Reintentar y retorno contextual. Nunca interpreta que la ausencia del catálogo concede acceso gratuito.
- **error / Error:** falla al cargar el catálogo, Reintentar y retorno contextual. Sin precios supuestos.
- **parcial / Catálogo incompleto:** se mantienen las dos filas recibidas, con una advertencia explícita de que el catálogo está incompleto y Reintentar. El índice incluye solo los encabezados recibidos; al completar la carga se muestran las cuatro filas.

Los estados del fixture se aplican a las vistas del catálogo; el contexto de acceso/cuenta conserva su contrato complementario y no constituye un diseño nuevo de estados de SP-2. Reintentar es una simulación local. Las herramientas no disponibles se muestran como texto informativo, no como botones de activación deshabilitados. No corresponde una confirmación de éxito separada para la sección informativa; la lectura completa es el estado normal. Los estados de validación/permiso denegado no aplican a los datos públicos de planes, que son de solo lectura. Si no hay conexión durante la carga inicial, se muestra el error del catálogo; los datos recibidos parcialmente usan el estado incompleto. No se presentan precios desactualizados como si fueran actuales.

## 9. Comportamiento adaptable

Rango de inspección compatible: 320–1280px y superior. Por encima de 1100px, la estructura usa los márgenes laterales existentes de 40px; las columnas del registro son de 220px / flexible / flexible, con separaciones de 28px. Entre 761px y 1100px se usan los márgenes laterales existentes de 28px, una primera columna de 190px y separaciones de 24px. En ≤760px, la estructura existente usa márgenes laterales de 20px, los controles del encabezado se ajustan a varias líneas, el índice local de planes se ajusta a varias líneas, desaparece el encabezado de columnas y cada plan pasa a ser una sección vertical. El orden se mantiene: nombre → precio/período → herramientas incluidas → herramientas no disponibles. En teléfonos, el grupo de precio/período comparte una línea base izquierda. No hay desplazamiento horizontal para comparar, carrusel, planes ocultos ni listas de herramientas contraídas.

El panel compartido mantiene 28px de relleno interior lateral en escritorio y 20px en teléfonos. Los nombres largos en inglés/español se ajustan a varias líneas. El aviso de cuenta permanece dentro del área visible del teléfono. La altura de la barra del mockup se mide en tiempo de ejecución; el espacio libre sobre el encabezado sigue esa medida.

## 10. Accesibilidad y objetivos de movimiento

Objetivo WCAG 2.2 AA; las comprobaciones automatizadas aportan evidencia, pero no demuestran conformidad. Usar encabezados semánticos, artículos, listas, selectores nativos con etiquetas y enlaces. Todos los controles modificados tienen al menos 44px de altura, foco de teclado visible y etiquetas legibles. Objetivo de contraste del texto ≥4.5:1 y de controles/foco ≥3:1. La falta de disponibilidad se indica con texto explícito, nunca solo con color; los símbolos decorativos de verificación se ocultan de la tecnología de asistencia. La carga usa aria-busy y los fallos usan semántica de alerta. El orden del teclado sigue: estructura → retorno → índice de planes → contenido/pie de página; el aviso con sesión iniciada agrega su recorrido de interacción habitual.

Las filas permanecen legibles durante su animación de registro de 12px. Sus líneas divisorias pasan de escala .65 a 1, y el desfase entre filas produce un barrido rápido y ordenado. La animación es finita; no hay animación de fondo continua. Los controles de perfil existentes, prefers-reduced-motion y `?still=1` eliminan el desplazamiento y muestran el contenido final de inmediato. Se suprime el movimiento CSS de pestañas ocultas. La respuesta visual al pasar el cursor o enfocar el índice, y su navegación, siguen disponibles cuando se usa still.

## 11. Criterios de aceptación observables y verificación

| ID | Punto de quiebre | Estado | Resultado observable esperado |
|---|---|---|---|
| A-01 | 1280px | normal ES | Aparecen los encabezados de los cuatro artículos en el orden requerido del catálogo, solo con precios en COP. |
| A-02 | 390px | normal EN | Enthusiast muestra Free; los precios de pago son USD 7, USD 14 y USD 25, por mes. |
| A-03 | 390/1280px | normal | Cada plan superior repite su lista completa de herramientas; Master Designer tiene una línea de Taller 3D. |
| A-04 | 390/1280px | normal | Las tres etiquetas de no disponibilidad aparecen en Designer Plus y nuevamente en Master Designer. |
| A-05 | 390/1280px | normal | La sección de planes no tiene controles de compra, solicitud, contacto, suscripción, registro ni asignación. |
| A-06 | 390/1280px | acceso | Un enlace a Planes abre el fixture público de planes sin iniciar sesión. |
| A-07 | 390/1280px | con sesión iniciada | El aviso de cuenta contiene un enlace a Planes y permanece visible en la vista de planes. |
| A-08 | 390px | normal | Cada fila del registro se apila, muestra todas las herramientas y no produce desbordamiento de página. |
| A-09 | 1280px | normal | Las columnas compartidas del registro alinean el plan/precio, las herramientas disponibles y las no disponibles. |
| A-10 | 390/1280px | cargando | Cuatro grupos de skeleton reservan el espacio del registro de planes y anuncian el estado de carga. |
| A-11 | 390/1280px | vacío/error | Aparecen un mensaje contextual y Reintentar; no aparecen precios inventados. |
| A-12 | 390/1280px | parcial | Se mantienen los dos planes recibidos y la advertencia de catálogo incompleto hasta que Reintentar restaure los cuatro. |
| A-13 | 390/1280px | teclado | El índice local enfoca el encabezado elegido; Escape cierra el aviso y devuelve el foco. |
| A-14 | 390/1280px | movimiento reducido/still | Las listas finales permanecen visibles sin ejecutar la animación de entrada. |
| A-15 | 390/1280px | claro/oscuro | Ambos temas conservan los tokens de Pictures y los límites visibles de foco/controles. |

Los comandos de verificación se ejecutaron sobre **planes@v1.r1.dir-a.html**, generado a partir de su TSX mediante la CLI absoluta y sin conexión `components mockup build`. Compilación final: **425 KB, 2031 archivos fuente, código de salida 0**. Sin instalación, descarga de recursos ni alternativa de respaldo.

- Contraste: **158 pares comprobados en temas claro y oscuro; todos aprobados**.
- Primera auditoría: 120 renderizados, 4 hallazgos de alineación y 2 de relleno. Se corrigieron en el TSX la línea base de precio/período en teléfono y el margen superior del panel de carga; luego se volvió a generar el mockup.
- Auditoría final: **120 renderizados / 120 combinaciones previstas**, 2960 mediciones de texto y 292 paradas de foco; ambos temas y las seis combinaciones de vista/cinco estados en 1280/390px. No se omitieron muestras.

RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento

- Pruebas complementarias con Playwright: **62 aserciones aprobadas**, incluidas el orden/precios/estados requeridos de los planes, los recuentos acumulados de herramientas, la ausencia de acciones de planes, las dos rutas de entrada/retorno, Escape del aviso/restauración del foco, foco en el ancla, todos los reintentos, semántica de carga, estado final con movimiento reducido y nombres de animación reales `ledger-register`/`ledger-rule`.
- Evidencia de selectores: **12 selectores se resuelven en la vista renderizada predeterminada**; el selector de movimiento tiene la animación real `ledger-register`.
- **12 casos complementarios de reflujo/tema**: 320/390/760/768/1024/1280px × claro/oscuro, sin desbordamiento horizontal. Cero solicitudes HTTP(S) y cero excepciones de página durante la ejecución de interacciones.
- Inspección de capturas de pantalla en memoria: escritorio en ambos temas, teléfono en ambos temas, teléfono en inglés con sesión iniciada y aviso de cuenta abierto, y superficie de acceso existente con el enlace añadido. No se escribieron archivos de captura adicionales.

La matriz de auditoría mide el aviso contraído; la disposición abierta y el cierre se inspeccionaron/probaron por separado. No se ejecutaron lint/tipos/pruebas/compilación del producto, actualizaciones del catálogo en vivo, autenticación del servidor, inicialización del idioma del navegador en producción ni pruebas completas con tecnología de asistencia. Esta tarea no modifica código de producción.

## 12. Decisiones pendientes, supuestos e impacto

P: ¿La lista pública de herramientas debería incluir explícitamente “Catálogo / Catalogue” o mantener las herramientas de chat/contador enumeradas en este informe de UI? La descripción de permisos de SP-1 incluye acceso al catálogo, mientras que el informe y las descripciones públicas actuales de planes no mencionan un beneficio de catálogo por separado. Responsable de la decisión: David con el Planner; la exploración actual sigue el informe público y no muestra una línea adicional de catálogo.

Confirmado: cuatro planes con nombre y orden definidos; la moneda depende del idioma de la interfaz; Enthusiast es el nombre en inglés; las tres herramientas futuras siguen marcadas como no disponibles; no se indican límites numéricos de chat; el explorador está cubierto por la línea Taller 3D de Master Designer; el administrador asigna el plan. No se inventa ninguna decisión sobre precios ni disponibilidad.

Supuestos para revisión: listas completas de herramientas repetidas, división del grupo de herramientas no disponibles, índice de anclas ajustable a varias líneas, un enlace de retorno y recuperación ante catálogo incompleto son propuestas de diseño. Las etiquetas en inglés son traducciones literales de la terminología proporcionada y están sujetas al catálogo bilingüe compartido del proyecto. El idioma inicial seleccionado por el navegador es un requisito de implementación; el control de idioma visible y las vistas explícitas permiten inspeccionarlo aquí.

Impacto: exploración aditiva para SP-14 T14.1/T14.2/T14.3/T14.5. Los dos enlaces de entrada amplían las superficies de acceso/cuenta de SP-2 sin cambiar sus contratos. SP-1 proporciona los datos. No se rediseñan los tokens ni la estructura general; no se ha reemplazado ningún contrato canónico. La compatibilidad sigue sin determinarse hasta que el responsable elija una dirección y el finalizador produzca la instantánea aprobada. La integración en producción y la aprobación del responsable están pendientes fuera de esta exploración delegada.
