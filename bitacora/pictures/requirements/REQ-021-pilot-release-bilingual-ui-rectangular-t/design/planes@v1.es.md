---
contract: planes
version: 1
status: draft
artifact: ui-ux-contract
subplan: SP-14
requirements: [R17, R18, R19, R20]
owner: David
date: 2026-10-27
direction: c
name: Pliegues de consulta
source: planes@v1.r1.dir-c.tsx
mockup: planes@v1.html
---

# planes@v1 — Pliegues de consulta

## 1. Identidad y trazabilidad

**Borrador; no aprobado para implementación.** Este documento formaliza la dirección C seleccionada por el propietario en la web, Pliegues de consulta, en el par canónico de planificación `design/planes@v1.md` y `design/planes@v1.html`. La selección de dirección está confirmada; la aprobación del contrato sigue siendo una instancia de aprobación independiente del propietario/plan. El HTML se reconstruye a partir del TSX seleccionado e inmutable con el generador sin conexión actual, aplicando en memoria únicamente la corrección verificada para movimiento reducido descrita en §11. La composición, navegación, paleta, tipografías y movimiento conservan los de la dirección C. No se modifica la exploración, el código de producción, SPEC ni PLAN.

Entradas: `SPEC.md` actual (listo), esquema 1.3.0 de `PLAN.json`, revisión 1 de REQ-021, `planes@v1.r1.behavior.md` y Markdown/TSX/HTML seleccionados de r1.dir-c. Las secciones «Comportamiento — planes de acceso y sección de planes» y T1.2 de SPEC incluyen explícitamente Catálogo en el plan base; esto resuelve la pregunta de la exploración sin cambiar sus filas. La lista de disponibilidad explícita del brief R18/UI prevalece sobre el paréntesis anterior de Prioridades: el chat extendido, la detección de estructura y la detección avanzada de globos no están disponibles; la calculadora de costos sí está disponible.

Instantáneas de origen (SHA-256, al finalizar la lectura):

| Origen | SHA-256 |
|---|---|
| `SPEC.md` | `85733361b25e8b6c9ff055cde3ddee45e77d36c0326698e01cde675b44aae204` |
| `PLAN.json` | `7b33d8cb90b956bcac2fdec6603dd6ad68c69f9c156381f32567f63175a546b1` |
| `design/planes@v1.r1.behavior.md` | `15d876a533b5c4f184f022dc07071ef93bb2ca8c90e83a01a8b84961d2fbc07f` |
| `design/planes@v1.r1.dir-c.md` | `534b4fd9a0c2086af50ce661a0af21cb70ec8f7414f5fe471fc98af22e5d0c84` |
| `design/planes@v1.r1.dir-c.tsx` | `fe48f75649a2fddeb50b5bb4ed2f88e62f8aacf5f73bc54ce0ab88776776abf8` |
| `design/planes@v1.r1.dir-c.html` | `eb0fa01829d71d8100c04088ab1f17a6ef7fbb9e1f9144c8655ae83b24388e4a` |

Solo **SP-14** vincula `ui.contract=planes`, versión 1: T14.1 para el texto de diseño, T14.2 para la implementación de UI (comparación pública) y T14.3 (dos enlaces de acceso), revisión visual T14.5. **T14.4** verifica la integración en un navegador real y **T14.6** audita de forma independiente las invariantes de catálogo, rutas públicas y textos. **SP-1 T1.2** es responsable de `plan-catalogue@1`; SP-1 también proporciona `permission-map@1` y `session-guard@1`. SP-2 es responsable del comportamiento de inicio de sesión/cuenta y del menú compartido; SP-14 solo agrega el acceso a planes en cada ubicación asignada.

| Requisito | Vistas / flujos | Criterios observables |
|---|---|---|
| R17 catálogo único | V1–V2 / F1–F5; tabla en §7 | UI-AC-01, 04–10, 23; mutación del catálogo verificada por T14.2/T14.6 |
| R18 comparación pública informativa | V1–V2 / F1–F2, F4–F5 | UI-AC-01–10, 13–14, 18–19 |
| R19 dos puntos de acceso | V3–V4 / F1–F2 | UI-AC-11–12, 20 |
| R20 idioma/moneda | V1–V4 / F3 | UI-AC-04–05, 21–22 |

Registro de versión e impacto integrado (un CHANGELOG separado queda fuera de este brief de dos archivos): **2026-10-27 — planes@v1, borrador, contrato inicial; compatible con la composición e interacciones de la dirección C seleccionada por el propietario.** No existe un contrato canónico anterior de planes que deba sustituirse. En relación con el producto actual, esto agrega `/planes` y dos enlaces; no modifica los flujos de cuenta ni la propiedad del catálogo. Acción requerida: aprobación independiente antes de que T14.1 copie byte por byte la instantánea aprobada a `design/contracts/planes@v1.md`; luego T14.2/T14.3 implementan y T14.5 revisa la versión aprobada. Ningún otro subplan se convierte en consumidor solo por depender de él. Este borrador no concede aprobación.

## 2. Propósito y usuarios

Una persona visitante sin sesión o con sesión iniciada responde: ¿qué herramientas incluye cada plan y cuál es su precio mensual en el idioma de esta interfaz? El objetivo se cumple al leer los cuatro planes en el orden del catálogo, reconocer las herramientas no disponibles y volver a la superficie de origen. Las personas con roles personalizados ven la misma comparación; los permisos del personal no modifican su contenido.

Esta es una superficie informativa de trabajo dentro de Pictures. Las personas usuarias pueden plegar o volver a abrir listas y navegar por la comparación. Aquí no pueden comprar, pagar, suscribirse, solicitar, contactar a alguien sobre un plan, registrarse, cambiar de plan ni modificar el acceso. Un administrador asigna planes en la superficie de cuentas existente. No se agrega una insignia de plan actual, un nivel de acceso seleccionado, un límite numérico, un contador de uso ni una UI para aplicar límites.

## 3. Arquitectura de la información y jerarquía

Conservar el encabezado de Pictures/Sempertex seleccionado, el control de idioma y el desplegable de cuenta con sesión iniciada, seguidos de: H1 **Planes / Planes** con enlace contextual para volver; índice local con ajuste de línea y en el orden del catálogo; un panel de papel redondeado con cuatro bandas de planes continuas y separadas por líneas; la oración explicativa; el pie de página existente. La página no tiene un nivel promocionado ni una acción para iniciar la adquisición.

Todas las bandas empiezan expandidas. La columna izquierda de identidad contiene H2, precio mensual y el control de expansión independiente. La región derecha contiene «Herramientas incluidas / Herramientas incluidas» y la **lista acumulativa completa**, no solo las adiciones. El nombre y el precio siguen visibles al plegar; en la región que queda libre se mantiene un rótulo breve de Herramientas incluidas. Un enlace del índice local abre su destino sin cambiar las demás bandas y enfoca el H2 de ese plan. Se pueden dejar varias listas abiertas o plegadas.

Las cuatro bandas conservan el orden Entusiasta, Designer, Designer Plus, Master Designer. El nombre en inglés de Entusiasta es Enthusiast; los demás nombres no cambian. El catálogo es la fuente de todos los nombres, importes, herramientas, disponibilidad y orden. La maqueta usa un único conjunto de datos de ejemplo claramente ilustrativo; la implementación debe leer `src/lib/planes/catalogo.ts` (`plan-catalogue@1`), sin un segundo catálogo propio de la página ni reglas de precios.

## 4. Sistema de diseño y lenguaje visual

Fuentes fijas inspeccionadas en modo de solo lectura: t12 `src/app/globals.css`, `layout.tsx`, `login/page.tsx`, `login/LoginForm.tsx`, `CabeceraApp.tsx` y `MenuApp.tsx`; componentes hermanos actuales `cuentas-admin@v1` (Parte de acceso), `proyectos@v1` y `taller-esenciales@v1`. El panel de acceso centrado de SP-2, el encabezado y el vocabulario seleccionados prevalecen en los contextos de acceso sobre el inicio de sesión heredado con contraseña compartida. No se reemplaza ninguna paleta, tipografía ni identidad del producto. Se conservan la marca de Pictures con anillo y punto y el logotipo de Sempertex.

| Token de Pictures | Función en el kit / uso | Claro / oscuro |
|---|---|---|
| `--fondo` | fondo | #faf9fc / #0b0c10 |
| `--superficie` | tarjeta, ventana emergente | #ffffff / #16181f |
| `--texto` | elementos en primer plano | #1c1425 / #f4f5f7 |
| `--texto-suave` | texto atenuado | #6b6178 / #9aa1ad |
| `--superficie-2` | secundario, atenuado, estado neutral al pasar el cursor | #efe9f8 / #242733 |
| `--acento`, `--sobre-acento` | primario, primer plano sobre primario | #6d3fe0, #ffffff / #9479ff, #120b24 |
| `--acento-hover` | estado primario al pasar el cursor | #5530b8 / #a58dff |
| `--acento` | anillo de foco | #6d3fe0 / #9479ff |
| `--borde`, `--borde-suave` | borde decorativo del panel, separador de filas | #e3daef, #efe9f8 / #383c48, #2a2d38 |
| `--texto-tenue` | borde de entrada/control, alias accesible heredado de SP-2 | #766c85 / #8a91a0 |
| `--error`, `--error-suave` | texto/superficie destructivos heredados | #b23a45, #ffeaec / #ff979f, #43252a |

Usar Geist Sans para la UI y Geist Mono solo para los metadatos heredados. Los recursos WOFF2 locales existentes de Next están integrados para uso sin conexión. H1 24px/1.25 peso 600; H2 de plan 20px/1.3 peso 600; precio 22px peso 500 (20px en teléfono), cifras tabulares; herramientas 14px; disponibilidad/rótulo 12px; texto complementario 13px; cuerpo 15px/1.5. No se incorpora ninguna familia tipográfica. Conservar las funciones de forma de los componentes hermanos: `--radius-panel:32px`, `--radius-inset:24px`, `--radius-field:18px`, `--radius-pill:999px`. Margen interior del panel: 28px en escritorio / 20px en teléfono; cada banda tiene 24px de relleno vertical. Los separadores neutrales y las marcas de verificación facilitan la lectura. El acento se conserva en la marca, los enlaces, el foco y la acción del formulario existente; el estado no disponible se indica con texto, no solo con color.

Los componentes usan **origen:id variante estado**; las importaciones corresponden a componentes realmente instalados:

| Nombre | Importación / responsabilidad renderizada |
|---|---|
| `shadcn:button outline expanded\|collapsed\|hover\|focus\|pressed` | `@/components/ui/button` (shadcn 4.22.1, base-nova/Base UI); control de expansión de herramientas independiente, nombre accesible que identifica el plan, `aria-expanded`, `aria-controls` |
| `shadcn:button outline ready\|hover\|focus\|pressed` | La misma importación; acciones de reintento y de cuenta existentes |
| `shadcn:button default ready\|hover\|focus\|pressed\|disabled\|loading` | La misma importación; solo el contexto existente de formularios de acceso/cuenta |
| `shadcn:input email\|password ready\|focus\|disabled\|invalid` | `@/components/ui/input`; formularios existentes de SP-2; etiquetas y restricciones nativas |
| `shadcn:skeleton plan-band loading` | `@/components/ui/skeleton`; cuatro bandas neutrales, sin precios inventados |
| `native:details account closed\|open\|focus` | Control no modal nativo de SP-2 con un enlace de Planes agregado; sin patrón ARIA de menú incompleto |
| `native:select language ready\|focus` | Selector etiquetado de producto ES/EN |
| `native:select view\|state\|theme\|motion ready\|focus` | `mountMockup` de `@kit/mockup`; solo controles de inspección de la maqueta |
| `native:a entry\|return\|plan-index ready\|hover\|focus` | Destinos reales de `/planes`, origen y fragmento; los controladores de la maqueta simulan cambios de ruta |
| `custom:app-header compact public\|signed` | `.masthead` existente, marca y `.header-tools`; sin control de cuenta cuando no hay sesión iniciada |
| `custom:plan-band ruled expanded\|collapsed` | `article`, H2, precio, Button real y lista semántica de herramientas |
| `custom:catalogue-feedback ruled empty\|error\|partial\|offline` | Encabezado, motivo, alerta y Button real de reintento |
| `motion:tool-list spring expanded\|reopening\|reduced` | `motion/react`; `useMotionProfile` de `@kit/motion` |
| `lucide:icons outline decorative` | `lucide-react`: ArrowLeft, ArrowRight, ChevronDown, Check, UserRound; ocultos del árbol de accesibilidad cuando el texto ya nombra la acción |

No se requiere resolver carencias de componentes no disponibles, usar alternativas HTML, agregar dependencias, instalar paquetes ni cargar recursos en tiempo de ejecución. Esta tarea produce una maqueta de planificación independiente; no crea una aplicación en `design/preview`.

**Gramática de movimiento conservada:** respuesta táctil al activarse y compresión al asentarse. Al cargar, `.plan-band` se traslada Y 12px y escala Y .985, sobrepasa hasta −2px / 1.002 y luego se asienta en su posición inicial; duración expresiva 480ms, desfase de 65ms por banda, cubic-bezier(.34,1.4,.64,1). La respuesta al presionar controles dura 180ms, translateY(2px)/scale(.97); la marca de expansión gira 180°. Al volver a abrirse, la lista de herramientas usa un resorte breve de perfil desde Y 6px / escala .99 hasta su posición final; la aparición exterior alcanza opacidad 1, Y 0, escala 1 (duración nominal .24s). Natural usa 300/140ms para el CSS de bandas/controles; sutil usa 160/100ms; el resorte de Motion usa los valores reales del perfil. Son interacciones finitas, no efectos perpetuos. La activación se pausa cuando la pestaña está oculta. El movimiento reducido del sistema operativo, Quieto y `?still=1` llevan los efectos existentes a su posición final y muestran el contenido final inmediatamente; todas las acciones y los resultados del foco siguen disponibles. Las correcciones actuales del entorno de ejecución están integradas; además, un movimiento residual verificado del resorte de la lista en curso se corrige como se describe en §11, sin editar el código fuente seleccionado ni el entorno de ejecución compartido.

## 5. Navegación y modelo de interacción

La pantalla de inicio de sesión tiene exactamente un enlace **Planes / Planes**, después de las instrucciones para restablecer la contraseña, que lleva a la ruta pública `/planes`. El desplegable de cuenta existente en cada página con sesión iniciada tiene exactamente un enlace Planes entre Mi cuenta y Cerrar sesión; lleva a la misma ruta `/planes` y conserva el contenedor con sesión iniciada. La identidad real de la cuenta se obtiene de la sesión; la identidad neutral de ejemplo Cuenta Entusiasta es ilustrativa, no promociona un plan actual.

La página pública de planes omite el desplegable de cuenta y vuelve a `/login` con **Volver al acceso / Volver a iniciar sesión**. El acceso con sesión iniciada registra la página de origen y vuelve allí si pertenece al mismo origen. La maqueta usa `/cuenta` y **Volver a Mi cuenta / Volver a Mi cuenta** para mostrar ese flujo. En producción se debe recuperar el origen seguro real; si se accede directamente con sesión iniciada y sin un origen, se puede volver a Mi cuenta. No se debe aceptar una URL externa proporcionada por el cliente como destino de retorno. Los cambios de ruta enfocan el nuevo H1.

Los enlaces del índice local conservan sus destinos de fragmento. Al activarlos, solo se expande esa banda, se enfoca su H2 (`tabIndex=-1`) y se desplaza hasta ella; se debe tener en cuenta cualquier encabezado persistente de la aplicación real y la barra de inspección fija de la maqueta. El movimiento reducido usa desplazamiento inmediato. Plegar/desplegar mantiene el foco en el control y alterna **Ocultar herramientas / Ocultar herramientas** ↔ **Ver herramientas / Ver herramientas**. Las listas plegadas quedan realmente ocultas a la lectura y al foco, no solo recortadas. La activación con Enter, Espacio o puntero tiene el mismo resultado. El estado de expansión nunca representa un plan de acceso activo/asignado.

El desplegable de cuenta sigue el comportamiento existente de SP-2; Escape lo cierra y devuelve el foco al resumen. El cambio de idioma actualiza juntos los nombres, el texto de las herramientas, los textos funcionales y la moneda, y conserva el diseño de la comparación. La maqueta conserva el idioma elegido explícitamente al cambiar la vista o el estado de inspección. Hasta SP-8, el idioma inicial se determina según el navegador/Accept-Language: inglés → EN/USD; español o idioma no admitido → ES/COP. SP-8 es responsable de la persistencia posterior de preferencias de cuenta; esta comparación no introduce un segundo mecanismo de persistencia.

Los selectores de inspección tienen los identificadores nativos `view`, `state`, `theme`, `motion` y las etiquetas Vista, Estado, Tema, Movimiento. No hay ningún diálogo, por lo que `scene` / Diálogo no corresponde. Estos selectores y las etiquetas de la maqueta no son navegación del producto ni textos de producción.

## 6. Flujos

1. **F1 — Comparación pública (V3 → V1).** Abrir `/login` → seguir su único enlace a Planes → ver cuatro secciones expandidas sin menú de cuenta → leer/plegar/volver a abrir cualquier lista → seguir Volver al inicio de sesión → regresar al contexto de inicio de sesión sin cambios. No se requiere autenticación para comparar.
2. **F2 — Comparación con sesión iniciada (V4 → V2).** Abrir el desplegable de cuenta desde una página autenticada → seguir su único enlace a Planes → ver los mismos cuatro planes junto con el desplegable de cuenta existente → leerlos → regresar al origen registrado. El entorno de prueba comienza y termina en Mi cuenta; producción también debe admitir otras páginas de entrada del mismo origen.
3. **F3 — Idioma (V1–V4).** Un navegador en inglés muestra inicialmente Entusiasta/Gratis y 7/14/25 USD por mes. Un navegador en español o con un idioma no admitido muestra Entusiasta/Gratis y 20.000/45.000/70.000 COP por mes. Cambiar el control local ES/EN actualiza la comparación visible de forma atómica; solo se muestra una moneda.
4. **F4 — Plegar y navegar (V1–V2).** Todas las secciones comienzan expandidas → activar Ocultar herramientas en cualquier sección → el nombre y el precio permanecen visibles → activar Mostrar herramientas para restaurar esa lista o usar el enlace del índice local de la sección para expandirla y enfocarla. Las demás secciones conservan su estado de presentación. No cambian los valores del catálogo ni los permisos de la cuenta.
5. **F5 — Recuperación del catálogo (V1–V2).** Catálogo ausente/incompleto/ilegible → no se muestran precios inferidos ni una comparación parcial → se muestra una explicación y Reintentar → se repite la misma lectura → se muestra la comparación completa de cuatro planes o se conserva el error. En el entorno de prueba, Reintentar restablece el estado listo de inmediato. Si el catálogo de producción se valida de forma estática, la validación de compilación/carga rechaza los datos no válidos antes; no se prescribe una solicitud innecesaria del cliente ni una demora de carga simulada.

## 7. Especificaciones de vistas

| Vista / selector | Estructura, texto y acciones | Datos / flujo |
|---|---|---|
| V1 / `public` | `/planes` con sesión cerrada; encabezado/idioma conservados, H1 Planes, enlace público para volver, índice local con ajuste de línea, un panel de comparación con separadores, oración explicativa y pie de página conservado. Sin menú de cuenta. | F1/F3/F4/F5, tabla de estados §8 |
| V2 / `signed` | `/planes` con sesión iniciada; comparación idéntica junto con el desplegable de cuenta conservado y retorno según el origen. Sin insignia de nivel asignado ni lista de roles personalizados o de personal. | F2/F3/F4/F5; identidad real de la sesión |
| V3 / `login` | Encabezado/formulario centrado de SP-2 conservado, instrucciones para acceso solo por invitación, correo electrónico/contraseña, Entrar / Iniciar sesión e instrucciones para restablecer la contraseña; se añade exactamente un enlace a Planes después de las instrucciones para restablecerla. Sin menú de cuenta ni registro abierto. | F1; solo contexto de entrada, SP-2 sigue siendo la fuente de autoridad |
| V4 / `account` | Formulario centrado de Mi cuenta y desplegable de cuenta de SP-2 conservados; único enlace añadido a Planes en el desplegable, entre Mi cuenta y cerrar sesión. Los demás campos/acciones de la cuenta conservan la semántica de SP-2. | F2; entorno de prueba de cuenta neutro, sin rediseño de cuenta |

El HTML incluye formularios de acceso/cuenta únicamente para mostrar la ubicación de los enlaces; los controladores locales simulan fallos y nunca envían credenciales ni guardan datos. El contrato vigente `cuentas-admin@v1` rige la autenticación, el cambio de contraseña, la renovación de sesión y los detalles de los avisos. SP-14 no implementa ni redefine esos mecanismos.

Presentación del catálogo, importes mensuales exactos:

| Plan (ES / EN) | Español | Inglés | Herramientas incluidas acumuladas completas |
|---|---|---|---|
| Entusiasta / Enthusiast | Gratis | Gratis | Chat con límites / Chat con límites; Contador de globos / Contador de globos; Catálogo / Catálogo |
| Designer / Designer | 20.000 COP / mes | 7 USD / mes | Chat con límites más altos / Chat con límites más altos; Contador de globos / Contador de globos; Catálogo / Catálogo |
| Designer Plus / Designer Plus | 45.000 COP / mes | 14 USD / mes | Chat con límites más altos, contador, catálogo; Calculadora de costos / Calculadora de costos; Chat ampliado / Chat ampliado; Detección de estructuras / Detección de estructuras; Detección avanzada de globos / Detección avanzada de globos |
| Master Designer / Master Designer | 70.000 COP / mes | 25 USD / mes | Todas las herramientas de Designer Plus; Taller 3D / Taller 3D |

Designer Plus/Master marcan cada uno exactamente las tres filas de chat ampliado/estructuras/detección avanzada de globos con el texto **aún no disponible / aún no disponible** debajo del nombre de la herramienta. Las filas disponibles conservan una marca decorativa neutra; las no disponibles conservan la misma alineación del texto y no muestran acciones habilitadas que puedan inducir a error. La calculadora de costos está disponible. Master tiene una fila de Taller 3D para el editor completo, incluido el explorador de decoraciones prediseñadas; no hay una fila separada para el explorador. La fila de chat repetida usa el texto de límites más altos a partir de Designer. No se muestran cifras de límites de chat.

Gratis es la etiqueta de precio completa para Entusiasta; los importes de pago usan el formato de la configuración regional, con la moneda activa y **/ mes / / mes**. Nunca se muestran COP y USD juntos, un tipo de cambio, precios anuales ni un descuento ficticio. Todos los valores/textos de producción se obtienen del catálogo compartido; la tabla define el contenido actual esperado, no una segunda fuente de datos mantenida por separado.

Debajo del panel se conserva: **Cada plan incluye las herramientas del anterior. Un administrador asigna el plan.** No se añade ninguna acción posterior de compra/solicitud. Los encabezados complementarios son **Herramientas incluidas**. Las únicas acciones funcionales son Planes, volver, índice, desplegable y Reintentar; no se muestra ningún titular de marketing ni beneficio inventado.

## 8. Estados

Los ocho estados se pueden alcanzar mediante `#state`; los selectores de vista/tema son independientes. El idioma se puede cambiar mediante `#language`. El éxito es la comparación completa en estado listo, no una notificación de éxito de una mutación.

| Selector / condición | Comparación V1–V2 | Contexto de entrada V3–V4 / recuperación |
|---|---|---|
| `ready` | Cuatro secciones expandidas con el catálogo completo verificado. | Contexto habitual del formulario conservado. |
| `folded` | Se conservan las identidades/precios de los cuatro planes y se ocultan las listas de herramientas; cada lista se puede volver a abrir de manera independiente. | No es un estado de cuenta/formulario; el contexto de entrada permanece sin cambios. |
| `loading` | Estado **Cargando planes…**, región ocupada y cuatro secciones esqueleto neutras; no se muestran precios de comparación ni el índice local. | Campos/acción de inicio de sesión deshabilitados y etiqueta Trabajando; el formulario de cuenta se conserva como contexto, no como un nuevo flujo pendiente de SP-14. |
| `empty` | Alerta: **No pudimos cargar los planes.** Motivo: **El catálogo de planes no está disponible. Reintenta.** Botón Reintentar; no se muestra un estado de éxito con cero planes. | La identidad no puede estar «vacía»; se conserva el contexto. Reintentar restaura los cuatro planes. |
| `error` | Mismo encabezado de error; **Reintenta la operación.**, botón Reintentar, sin precios inventados. | Solo una denegación ilustrativa de credenciales/cuenta de SP-2; SP-2 vigente controla el comportamiento real del formulario. |
| `offline` | **Sin conexión**; **Revisa tu conexión y reintenta.**, botón Reintentar. No se muestra en silencio una comparación en caché que parezca actual. | Específico del catálogo; se conserva el contexto de entrada. |
| `partial` | Encabezado de error; **No se muestran datos sin confirmar. Reintenta.**, botón Reintentar; se suprime la comparación en lugar de inferir un precio o una herramienta faltante. | Específico del catálogo; se conserva el contexto de entrada. |
| `menu-open` | Desplegable de cuenta existente abierto en V2 con sesión iniciada; V1 sigue sin tenerlo. | Desplegable abierto en V4; no aplica a V3 con sesión cerrada. Escape lo cierra. |

Los controles deshabilitados/de carga son demostraciones del acceso de SP-2 que se conserva, nunca botones de selección de plan no disponibles. La validación del catálogo se realiza antes: la ausencia de nombre/precio/herramienta, un permiso desconocido o concesiones acumulativas incorrectas deben producir un error que identifique el plan/campo, no mostrarse en blanco/cero/gratis. Los datos parciales/obsoletos tienen un motivo y una opción de recuperación, en lugar de tratarse en silencio como actuales. La denegación de permisos no aplica a esta comparación pública, tampoco a visitantes con roles personalizados. No existen compra, cambio optimista de acceso, estado pendiente de mutación, diálogo destructivo ni estado modal. Reintentar varias veces no cambia los permisos de cuenta; los avisos de error de carga reales deben seguir siendo comprensibles si el siguiente intento también falla.

## 9. Comportamiento adaptable

Conservar los puntos de interrupción seleccionados de las vistas hermanas: **360–760px**, **761–1100px**, **1101px+**; 320px es un objetivo adicional para probar el ajuste del contenido. Se espera desplazamiento vertical para las listas acumuladas de herramientas; no se admite desplazamiento horizontal de página, carrusel horizontal de precios ni controles esenciales recortados en ninguno de los idiomas/temas.

| Rango | Diseño observable |
|---|---|
| 1101px+ | Ancho máximo de `.app` de 1520px, relleno lateral exterior de 40px. El encabezado y el enlace para volver comparten una fila. Panel con margen interior de 28px. Cada sección tiene 28% para la identidad (mínimo de 220px), una separación de columna de 32px y una región flexible para herramientas. Las herramientas usan dos columnas iguales, en orden de lectura por filas según el DOM. |
| 761–1100px | Márgenes exteriores de 28px; el panel conserva un margen interior de 28px. Identidad de sección de ancho mínimo de 190px / 30%, separación de 24px y una columna de herramientas. El índice de planes se ajusta a varias líneas en lugar de desbordarse. |
| 360–760px | Márgenes laterales de 20px para la aplicación/panel; los controles del encabezado se ajustan a varias líneas. El enlace para volver aparece después del H1. El índice de planes se ajusta en varias líneas encima del panel. Cada sección apila la identidad sobre una columna de herramientas; H2 ocupa todo el ancho, y el precio y el desplegable comparten la siguiente fila cuando el espacio lo permite; el texto del desplegable se ajusta dentro de su píldora y el chevrón permanece dentro. Precio de 20px; el texto/disponibilidad de las herramientas se ajusta a varias líneas. El formulario de acceso se contrae sobre su eje centrado existente de 676px. |
| Estrés de 320–360px | El bloque de identidad apila verticalmente el precio y el desplegable, conservando todo el contenido. Se mantiene el mismo orden de herramientas y márgenes de 20px; sin desplazamiento horizontal. |

Mantener un relleno vertical de sección de 24px, ajuste legible de moneda/mes, cifras tabulares y ningún elemento superpuesto fijo en la parte inferior que cubra Master/el pie de página. El menú de cuenta permanece dentro del ancho de la ventana. Toda la comparación usa el mismo eje que el contenedor seleccionado; V3/V4 conservan el diseño de formulario centrado. Puntos de revisión: 390/768/1280px, ambos idiomas/temas; comprobar también el límite de 360px y el ajuste a 320px.

## 10. Objetivos de accesibilidad

Objetivo WCAG 2.2 AA para el contenido/interacciones aplicables. Este contrato y las comprobaciones automatizadas no certifican la conformidad total. Texto ≥4.5:1 (el texto grande puede aplicar la excepción estándar de ≥3:1), bordes de controles significativos/indicador de foco ≥3:1. Conservar el anillo de foco visible de 3px / desplazamiento de 4px y altura mínima de controles principales de ≥44px; las etiquetas con ajuste de línea no deben encoger ni recortar el chevrón/área de interacción.

Usar un punto de referencia principal, un H1, H2 en orden, navegación con nombre accesible, artículos etiquetados, listas semánticas y controles nativos etiquetados. Los botones de desplegable exponen nombres específicos del plan, el estado expandido y el id de la región controlada. Las listas ocultas se excluyen de la lectura y el foco. Las marcas/chevrones decorativos no generan anuncios duplicados. La disponibilidad se expresa con texto, no solo con color o un ícono. El estado de carga tiene un indicador de estado y una región ocupada; los errores usan alertas y la recuperación es accesible mediante el teclado. El enlace para saltar al contenido lleva a este; en producción, el destino del contenido debe poder recibir el foco y tener en cuenta el espacio ocupado por el encabezado persistente.

La tecla Tab sigue el contenedor → idioma/cuenta → volver/índice → desplegables en el orden del catálogo; no se usa tabindex positivo. Al cambiar de ruta, el foco pasa al H1; los enlaces del índice enfocan H2; al activar o cerrar un desplegable se conserva el foco en el control que lo activó; Escape devuelve el foco del desplegable de cuenta al resumen. Los controles nativos mantienen el comportamiento de Enter/Espacio. El idioma del producto establece el idioma del documento y el texto visible. Los formularios conservan las etiquetas asociadas, el autocompletado y las restricciones nativas de entrada de SP-2; la validación real de cuentas queda fuera de esta comparación.

El modo silencioso, la opción de movimiento reducido del sistema operativo y `?still=1` eliminan el desplazamiento/repetición, detienen las animaciones existentes y conservan el diseño/foco/acciones finales. Sin destellos ni interacciones que dependan únicamente de arrastrar, pasar el cursor o leer dentro de un tiempo límite. Probar el ajuste del contenido/zoom y las etiquetas largas en inglés/español. Una revisión posterior del producto debe cubrir lectores de pantalla, zoom del 200%, identidad real de enrutamiento/sesión, diferencias entre navegadores y avisos de error reales; este artefacto estático no verifica esos aspectos.

## 11. Criterios de aceptación visual

Cada expectativa se puede verificar de forma independiente frente a la instantánea aprobada. A menos que se indique una excepción a continuación, los criterios se aplican a ambos temas e idiomas.

| ID | Punto de interrupción | Estado | Expectativa observable |
|---|---|---|---|
| UI-AC-01 | 1101px+ | ready | Hay cuatro franjas continuas con líneas, en el orden del catálogo, dentro de una hoja; la identidad y el precio están junto a la región de herramientas. |
| UI-AC-02 | 360–760px | ready | Cada franja muestra su identidad sobre una columna de herramientas, sin desplazamiento horizontal de la página. |
| UI-AC-03 | 761–1100px | ready | Cada lista de herramientas tiene una columna junto a la identidad del plan. |
| UI-AC-04 | 320–1280px | ready ES | Aparecen Gratis y 20.000 / 45.000 / 70.000 COP al mes, sin precio en USD. |
| UI-AC-05 | 320–1280px | ready EN | Aparecen Enthusiast / Free y 7 / 14 / 25 USD al mes, sin precio en COP. |
| UI-AC-06 | 320–1280px | ready | Exactamente las filas de chat extendido, estructura y globos avanzados muestran texto de no disponibilidad en Plus/Master. |
| UI-AC-07 | 320–1280px | ready | El chat de Entusiasta indica «con límites» y el chat de Designer o superior indica «con límites más altos», sin incluir una cifra. |
| UI-AC-08 | 320–1280px | ready | Solo Master tiene la única fila de Taller 3D; no hay una fila independiente para el explorador de decoración. |
| UI-AC-09 | 320–1280px | folded | Todos los nombres y precios permanecen visibles mientras las listas están ocultas. |
| UI-AC-10 | 320–1280px | folded → expanded | Al activar un enlace del índice local de planes, se abre y enfoca el H2 de destino con espacio libre para el encabezado. |
| UI-AC-11 | 360–1280px | login | Un único enlace Planes aparece después de las instrucciones para restablecer la contraseña y abre la comparación para usuarios sin sesión. |
| UI-AC-12 | 360–1280px | account/menu-open | Un único enlace Planes en el desplegable abre la comparación para usuarios con sesión. |
| UI-AC-13 | 360–1280px | loading | Cuatro franjas esqueleto y un estado de carga reemplazan los precios de la comparación. |
| UI-AC-14 | 360–1280px | empty/error/partial/offline | Un motivo y la opción Reintentar reemplazan la comparación; al reintentar se pueden recuperar las cuatro franjas. |
| UI-AC-15 | 360–1280px | focus | El foco del teclado muestra un anillo visible en enlaces, controles de expansión y selectores. |
| UI-AC-16 | 360–1280px | quiet/reduced/still | Las transformaciones de franjas y listas aparecen asentadas de inmediato, y las acciones de expansión siguen funcionando. |
| UI-AC-17 | 360–760px | ready/folded | La etiqueta y el chevrón del control de expansión permanecen dentro de la píldora con ambas longitudes de etiqueta. |
| UI-AC-18 | 360–1280px | ready | La comparación no tiene controles para comprar, solicitar, registrarse, contactar ni cambiar de acceso. |
| UI-AC-19 | 360–1280px | public/signed | La vista pública omite el desplegable de cuenta; la vista con sesión lo conserva sin cambiar el contenido de la comparación. |
| UI-AC-20 | 360–1280px | return navigation | El botón Atrás de la vista pública restablece el inicio de sesión; el de la vista con sesión restablece la página de origen (Mi cuenta en el entorno de prueba). |
| UI-AC-21 | 360–1280px | language change | Los nombres, las herramientas, la disponibilidad y la moneda cambian en conjunto, mientras se conserva la composición de cuatro franjas. |
| UI-AC-22 | 390/1280px | first visit | Un navegador en inglés selecciona EN/USD; uno en español o con un idioma no admitido selecciona ES/COP. |
| UI-AC-23 | 360–1280px | ready | Catálogo aparece una vez en la lista acumulativa completa de herramientas de cada plan. |
| UI-AC-24 | 1280px | expressive | Al cargar, las franjas realizan el asentamiento escalonado finito seleccionado; al volver a abrir una lista, se reproduce su animación de entrada con efecto elástico. |

### Corrección de comportamiento verificada y reproducibilidad

La reconstrucción directa reprodujo un defecto acotado al cambiar a Quieto **durante** una animación de entrada expresiva: se detenía el registro de franjas de CSS, pero Motion reemplazaba los efectos WAAPI de la lista de herramientas después del intervalo de asentamiento de dos fotogramas del entorno de ejecución, lo que dejaba unos 300 ms de desplazamiento en la lista. Las cargas iniciales con movimiento reducido ya pasaban. Una reproducción enfocada en el navegador observó que esos efectos de `.tool-list` seguían activos; se trata de un defecto real de transición, no de un fallo en la auditoría de contraste.

La compilación canónica corrige únicamente ese defecto: asigna una clave al subárbol `motion.ul` según el estado de movimiento reducido, para que al cambiar el modo de movimiento se cancele la animación de lista en curso y se monte la lista reducida ya asentada. Se conservan el estado de App y el de expansión. La transformación exacta de origen es:

```tsx
// Marcador seleccionado en el código fuente:
<motion.ul className="tool-list" initial=
// Reemplazo canónico en memoria:
<motion.ul className="tool-list" key={profile.reduced ? "still" : "motion"} initial=
```

La reproducción usa el `real/build.mjs` actual en memoria: reemplaza su única llamada `b = await bundle("", "", "", abs);` por `bundle(transformedSource, path.dirname(abs), abs)`, conserva el resto del código del generador, los alias, el procesamiento de CSS y fuentes y las dependencias sin conexión; establece la ubicación del módulo en la ruta del generador instalado. TSX transformado existe solo en memoria y escribe únicamente `planes@v1.html`. No se modifica manualmente ningún HTML generado o minificado; tampoco se editan el código fuente de exploración, el generador compartido ni el entorno de ejecución, ni se crea otro archivo fuente. El SHA del código fuente seleccionado que figura arriba permanece sin cambios. El CSS y la coreografía expresiva permanecen sin cambios. Una comprobación final enfocada observó cuatro animaciones expresivas de franjas y, 70 ms después de seleccionar Quieto, cero animaciones activas; una franja que ya estaba plegada permaneció plegada.

### Verificación canónica

Resultados recientes para el HTML canónico final, 2026-10-27:

- Constructor sin conexión actual: **APROBADO**, 559 KB, 2.031 archivos fuente incluidos en el paquete. A la compilación directa mediante CLI le siguió la corrección documentada de un marcador en memoria con el mismo constructor actual. Sin alternativa ni instalación. Los hashes de TSX/HTML seleccionados permanecen sin cambios.
- `python3 <kit>/kit/contrast.py design/planes@v1.html` (código de salida 0): **contraste: 158 pares verificados en modo claro y oscuro; todos aprobados**.
- `UV_OFFLINE=1 uv run --offline --with playwright python <kit>/kit/audit_mockup.py design/planes@v1.html` (código de salida 0): **128 representaciones / 128 combinaciones planificadas**, **3.300 mediciones de texto**, **402 paradas de foco** a 1280/390px, ambos temas, las cuatro vistas/ocho estados, sin advertencias de muestreo.
- **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento**
- Ejecución complementaria de Playwright en memoria (código de salida 0): **446 aserciones APROBADAS**, **56 casos expandidos/plegados** en 320/360/390/760/768/1100/1280px, ambos temas/idiomas. Se verificaron el orden del catálogo y los precios, las listas acumulativas, las seis filas no disponibles, el taller exclusivo de Master, la contención de los controles de expansión y las flechas, la expansión del índice y el foco programado, Enter/Space, ambas rutas de entrada y regreso, Escape/regreso del foco, los cuatro estados de error/reintento, la alternativa inicial en-US/es-CO/fr-FR a 390/1280px, la secuencia de movimiento expresiva y el cambio durante la ejecución a Quieto conservando los elementos plegados. Los contextos monitoreados registraron **0 errores de página y 0 solicitudes HTTP externas**.
- Se inspeccionaron en memoria las capturas finales estabilizadas a 1280/390px en ambos temas. El HTML de exploración seleccionado y el HTML canónico produjeron **vistas PNG idénticas píxel por píxel en las cuatro comparaciones ES listas**. No se escribieron archivos de captura. El movimiento expresivo se verificó por separado; no se dedujo de las capturas estabilizadas.
- Las pruebas complementarias iniciales detectaron (a) una aserción de foco inmediata que competía con el requestAnimationFrame especificado, corregida al esperar el foco real, y (b) el defecto real en la transición a Quieto, corregido arriba. Las verificaciones de la instantánea final indicadas arriba se aprobaron; ninguna verificación fallida se presenta como aprobada.

`<kit>` es `/home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit`. Estos resultados evalúan únicamente el artefacto de planificación. No se ejecutaron lint, verificación de tipos, pruebas ni compilación de producción del producto: no se modificó ningún archivo de producción y la implementación del catálogo/autenticación/navegación queda fuera de esta tarea. La modificación del catálogo real, la restauración segura del origen, la autorización y la aceptación completa de accesibilidad siguen siendo trabajo de T14.2–T14.6. Los totales históricos de pruebas de exploración no se consideran evidencia reciente.

## 12. Preguntas abiertas y supuestos

**No hay preguntas materiales abiertas sobre la composición y el comportamiento seleccionados de SP-14.** La pregunta anterior sobre el Catálogo se resuelve con el comportamiento actual de planes de acceso de SPEC y T1.2; se conserva la fila existente de la fixture. El propietario aplaza explícitamente los límites numéricos del chat y estos no deben bloquear ni aparecer en este contrato. La pertenencia a Explorer y las tres funciones no disponibles se confirman según lo indicado en §7.

Decisiones confirmadas por el propietario: cuatro nombres/orden/precios de planes, regla de moneda por idioma, sin flujo de adquisición/cambio, redacción cualitativa sobre límites de chat, acceso público informativo, única línea de Taller/explorador de Master, dos enlaces de entrada, selección de dirección C. Decisiones de presentación: listas acumulativas completas, todas las secciones abiertas inicialmente, secciones plegables independientes e índice envolvente en la página, conservación de la estructura y los tokens de Pictures y del movimiento.

Supuestos sobre los límites de implementación: se puede leer estáticamente el catálogo compartido actual; los estados de error/carga describen superficies excepcionales veraces sin requerir una nueva API del cliente. La navegación de regreso en producción conserva una ruta de entrada validada del mismo origen; solo se simula el ejemplo de Mi cuenta. La persistencia del idioma entre cuentas corresponde a SP-8. Los datos neutrales de cuenta y todas las operaciones se etiquetan como simulación; los formularios del contexto de entrada no implementan autenticación ni contraseñas/sesiones. El contrato actual de SP-2 sigue siendo la referencia para esos detalles. Aquí no se certifican un catálogo activo, la aplicación de permisos, una API de producción, la restauración real del origen, la conformidad total con WCAG ni la compilación del producto.

Aprobación y entrega: David/la aprobación independiente del plan debe aprobar este borrador exacto antes de que T14.1 lo copie para la implementación. Este proceso de cierre no lo aprueba. La exploración/el historial permanecen inmutables. El RESULTADO requerido para la tarea registra su finalización; un registro de cambios aparte, una entrada en la memoria del proyecto, una actualización de la bitácora compartida y una vista previa de producción quedan fuera de las rutas de salida explícitamente permitidas.


**INQUIETUDES:** No hay preguntas materiales de diseño ni faltan herramientas sin conexión. **RESULTADO: APROBADO — sin problemas de contraste, elementos no textuales, foco, alineación, relleno ni desbordamiento.** El contrato sigue siendo un borrador sin aprobar; esta maqueta no demuestra el backend/enrutamiento/autorización reales, las comprobaciones con lector de pantalla/zoom/navegadores distintos ni el lint, la verificación de tipos, las pruebas o la compilación del producto. El problema de Quieto durante la ejecución en el entorno compartido debe corregirse por separado en el código de origen; este HTML canónico ya incluye la corrección acotada y su reproducción indicada arriba.
