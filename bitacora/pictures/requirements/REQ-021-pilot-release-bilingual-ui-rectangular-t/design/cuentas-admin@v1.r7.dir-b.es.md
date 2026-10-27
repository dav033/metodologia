---
name: Pase al montaje
contract: cuentas-admin@v1
revision: r7
direction: b
status: draft
subplan: SP-2
requirements: [R1, R3, R16]
date: 2026-10-26
---

# Pase al montaje — exploración espacial B

Exploración de planificación independiente, **no aprobada**. Esta es una nota sobre dirección y evidencia, no el contrato canónico de doce secciones. La persona responsable elige una dirección antes de que una finalización independiente redacte el contrato compartido. No se editó ningún contrato canónico, artefacto histórico, plan, código fuente de producción ni directorio de vista previa.

## Concepto y elemento distintivo

Pictures es un espacio para armar decoraciones con globos, no un panel abstracto de organización. Su pantalla de acceso es un pase de dos hojas sobre una superficie de montaje. Una línea perforada une un soporte para globos con un formulario funcional; el soporte se asienta formando su arco mientras el pase se despliega desde su bisagra izquierda. Unas pequeñas esquinas de registro establecen el marco espacial. El pase nunca gira mientras alguien ingresa datos. El formulario, el texto complementario y el pie de página comparten el mismo borde izquierdo. La administración usa la misma superficie como una hoja de equipo abierta con renglones y un dock de herramientas inferior persistente en lugar de una barra lateral. El dock inferior incluye etiquetas de texto y botones estándar; no requiere gestos ni arrastrar elementos.

**Por qué esta no es la opción predeterminada:** la división, similar a una credencial, deriva de las invitaciones y del montaje físico; su ilustración muestra un arreglo real de globos en lugar de una forma genérica decorativa; la navegación se ubica debajo del trabajo, y el movimiento sigue una lógica de bisagra y asentamiento. La lista de cuentas sigue siendo una lista común, fácil de recorrer visualmente. La audacia se concentra en el pase de acceso y la superficie, en lugar de extenderse a controles poco familiares.

## Dos miniaturas y selección

Se crearon primero, antes del TSX completo:

1. `cuentas-admin@v1.r7.dir-b.html.candidate-1.html` — pase de acceso con bisagra, soporte para globos y dock de herramientas inferior. **Elegida.** Mantiene un eje de formulario estable, incorpora la metáfora de invitación y se adapta de forma sencilla a una disposición vertical del pase en pantallas pequeñas.
2. `cuentas-admin@v1.r7.dir-b.html.candidate-2.html` — un abanico de pases físicos para el equipo. No se eligió: sus registros inclinados aportan energía visual, pero dificultan recorrer las cuentas y leer los nombres largos, y son menos adecuados como marco común para avisos legales y edición de permisos.

Ambas miniaturas independientes usan solo HTML/CSS local y responden a la preferencia de tema claro/oscuro del sistema. El artefacto completo elegido añade controles explícitos para tema, vista, estado, escena, movimiento e idioma.

## Ocho ejes

| Eje | Dirección B |
|---|---|
| Concepto | Un pase de acceso personal se despliega sobre una superficie de montaje de decoraciones con globos. La perforación, un soporte físico sencillo y las esquinas de registro conectan la identidad con el mundo del producto. |
| Diseño / composición | Pase de acceso centrado de 950px con hojas visual/formulario de proporción aproximada 40:60; superficie de administración de 1120px con filas de equipo a modo de renglones. Los roles tienen un índice local y permisos agrupados, sin barra lateral de página. El dock inferior compacto permanece visible al desplazarse. |
| Navegación | Dock inferior de texto e iconos para Cuentas, Roles y Mi cuenta, además del menú de cuenta con nombre. El detalle de cuenta y las decisiones destructivas usan primitivas modales reales. No hay deslizamientos, zonas interactivas solo para puntero ni operaciones que requieran arrastrar elementos. |
| Tipografía / escala | Sans del sistema: títulos de página de 32px, 28px en teléfonos, peso 550 y espaciado entre letras de -1.3px; declaración de superficie física de 26/18px, peso 450. Campos de entrada de 15px, texto de trabajo de 14px, texto complementario de 13px y metadatos de ubicación/pase de 12px en monoespaciada. Sin fuentes de red. |
| Densidad / forma | Relleno del formulario de 36×40px, relleno de hoja de 32px, relleno interior del teléfono de 20px, separación entre grupos del formulario de 20px y relleno de filas de 22px. Un solo contorno contenedor, esquinas de pase de 12px, iniciales circulares y óvalos pequeños para los globos. Sin tarjetas anidadas ni recuadros de indicadores clave de rendimiento. |
| Componentes | Controles reales instalados de shadcn/Base UI y comportamiento de casilla/diálogo de Animate UI, reorganizados en un pase, soporte, lista de registros y zona de permisos personalizados. Los selectores de vista previa nativos y los selectores de idioma/rol/estado permanecen visibles. |
| Lógica de color | La paleta de Pictures de ambos repositorios se asigna a los roles del kit. El malva se usa para acciones principales y el soporte para globos; navegación y superficies neutrales. Verde indica activo/éxito; rojo, error/acción destructiva. Los bordes de controles corregidos para cumplir el contraste permanecen visibles en ambos temas. |
| Movimiento | El pase se despliega alrededor de una bisagra izquierda; tres globos se asientan en secuencias independientes de 780/920/1060ms con cubic-bezier(.22,1.3,.36,1). La superficie usa el resorte de Motion seleccionado. Las filas de la lista entran desde 18px a la derecha con desfases de 70ms. Al pasar el puntero, el dock sube 3px; al presionarlo, se comprime 1px. Solo efectos finitos de una ejecución; el movimiento reducido, Quieto y `?still=1` muestran la geometría final de inmediato. |

La evidencia de los selectores renderizados está en el JSON complementario. La evidencia de movimiento identifica elementos que se observaron animándose realmente, en lugar de limitarse a contener nombres de clase relacionados con animaciones.

## Identidad compartida y registro visual

Se leyeron la fuente compartida de comportamiento, SPEC, PLAN.md, PLAN.json, los archivos `src/app/globals.css` de ambos repositorios, la estructura de inicio de sesión existente y el armazón/la marca de Pictures. Los repositorios comparten la misma paleta clara: `--fondo #faf9fc`, `--superficie #ffffff`, `--texto #1c1425`, `--texto-suave #6b6178`, `--acento #6d3fe0`. Los valores del fondo/superficie/texto/acento del tema oscuro son `#0b0c10`, `#16181f`, `#f4f5f7`, `#9479ff`.

Al inspeccionar el árbol de diseño de requisitos proporcionado, **no había notas de dirección `*dir*.md` de proyectos hermanos**. Los borradores de contratos disponibles de SP-3 y SP-4 sirvieron como registro visual: SP-3 usa una barra de taller, una ventana gráfica y un inspector; SP-4 usa una barra de escritorio y una cuadrícula de proyectos. Esta exploración conserva su paleta, tono y semántica de controles conocidos, y utiliza un pase con bisagra, una hoja de equipo abierta y un dock inferior. No copia la composición ni el movimiento de otra dirección. La marca de la aplicación conserva la geometría existente de anillo y punto.

| Rol del kit | Token / adaptación del proyecto |
|---|---|
| fondo / tarjeta / primer plano | `--fondo` / `--superficie` / `--texto`, copiados por tema |
| primario / primer plano primario / hover primario | `--acento` / `--sobre-acento` / `--acento-hover`, copiados por tema |
| secundario / atenuado | `--superficie-2`, copiado por tema |
| borde | `--borde`, solo separadores estructurales |
| entrada | Alias propuesto de borde interactivo para `--texto-tenue` existente: #766c85 claro / #8a91a0 oscuro. `--borde` estructural no tiene suficiente contraste para los contornos de controles. |
| primer plano atenuado | `--texto-suave` #6b6178 claro; se propone #a8afbc oscuro para conservar el contraste en superficies agrupadas |
| anillo | `--acento`; contorno sólido de 2px con un desplazamiento de 2px al recibir el foco del teclado |
| destructivo / éxito / advertencia | `--error`, `--exito`, `--aviso` existentes y las superficies suaves correspondientes |

Inventario de componentes reales: `@/components/ui/button` (predeterminado, contorno, fantasma, enlace y destructivo); `input` (correo electrónico/contraseña/búsqueda/texto); `checkbox` (Animate UI sobre Base UI, marcado/sin marcar/deshabilitado); `skeleton` (carga); `dropdown-menu` (menú de cuenta); `dialog` (gestión de cuentas y enlace de un solo uso); `alert-dialog` (eliminación de cuenta/rol). Cada uno proviene del manifiesto instalado, no de una imitación escrita a mano. El diseño, la ilustración de globos, la lista y la agrupación usan CSS/HTML semántico personalizados. No se instaló ni obtuvo ningún paquete o recurso. La solicitud anterior de fragmentos alternativos queda sustituida por el encargo explícito de esta exploración, que da prioridad a las bibliotecas reales; se usó el constructor real disponible.

## Preservación del comportamiento y alcance

El archivo de comportamiento compartido sigue siendo la fuente de verdad. Todos los datos son ilustrativos y todos los enlaces `.example` son enlaces simulados inertes. Los anuncios de éxito describen transiciones simuladas de la interfaz, no escrituras en el servidor ni autenticación real. La autorización de API, la validación del mismo origen, la invalidación de enlaces, el hashing, la anonimización y el enrutamiento real siguen siendo obligaciones de implementación e integración de SP-1/SP-2.

| Vista nativa | Objetivo y comportamiento mostrado |
|---|---|
| Iniciar sesión | Correo electrónico y contraseña; sin registro. El único error genérico cubre correo desconocido, contraseña incorrecta, desactivación y bloqueo, e incluye siempre la espera de quince minutos. El mensaje de éxito explica el retorno seguro, la primera herramienta permitida o la alternativa Mi cuenta. Para recuperar el acceso, se solicita un enlace al administrador. |
| Activar invitación | Invitación para Camila Ortiz y correo electrónico; dos campos de contraseña, mínimo de ocho caracteres; aviso completo ES/EN v1 con campos legales entre corchetes; casilla de aceptación explícita, sin marcar. El enlace usado o vencido muestra un único mensaje neutral que solicita un enlace nuevo. El éxito de activación representa una cuenta Plan 2 con sesión iniciada de inmediato. |
| Restablecer contraseña | Enlace generado por el administrador, dos campos para la nueva contraseña, uso único durante 24 horas y mensaje coincidente para enlaces no válidos. El éxito vuelve al inicio de sesión en lugar de afirmar que se inició sesión automáticamente tras el restablecimiento. |
| Nuevo aviso de datos | Aviso completo con versión y aceptación obligatoria antes de continuar; se puede cerrar la sesión. No hay forma de eludirlo desde el panel de administración. El éxito muestra la versión y la fecha de aceptación. |
| Mi cuenta | Perfil propio de Ana Restrepo con sesión iniciada, rol, aviso aceptado y cambio de contraseña con la contraseña actual. El éxito explica que se terminan las demás sesiones y se renueva la sesión de este navegador. |
| Cuentas | Cuatro registros de prueba con nombre, empresa, rol/plan y estado activo/invitado/desactivado. Búsqueda por nombre o correo electrónico y filtro por estado. El menú de cuenta incluye nombre/rol, Mi cuenta y cerrar sesión. La administración permite cambiar el rol, desactivar/reactivar y regenerar el enlace de invitación/restablecimiento. |
| Invitar persona | Nombre, correo electrónico, empresa opcional y un plan de rol/acceso. Plan 2 explica que Taller 3D está excluido; Plan 3 lo incluye. Un correo duplicado genera un error claro. La generación muestra una sola vez un enlace de uso único, el resultado de copiar y una alternativa de copia manual, su vencimiento y la invalidación de enlaces anteriores sin usar del mismo tipo. No se promete el envío automático de correo electrónico. |
| Roles de sistema | Los cinco roles del sistema y sus permisos son de solo lectura. Los planes acumulan herramientas exactamente como se especifica en los requisitos aceptados. Un rol personalizado de «Diseño de eventos» muestra permisos agrupados. Se puede confirmar la eliminación de un rol personalizado sin cuentas; el estado Cuenta con trabajo/protegido incluye dos cuentas asignadas y bloquea la eliminación hasta que se reasignen. |
| Crear / editar rol | Nombre editable y casillas de permisos agrupadas por herramienta. La validación rechaza un nombre en blanco o cero permisos; el estado de validación muestra explícitamente todas las casillas sin marcar. Guardar muestra una confirmación local. |

**Estado** nativo ofrece Normal, Cargando, Vacío, Error, Éxito, Validación, Enlace usado/vencido, Sin permiso, Sin conexión, Cuenta con trabajo. **Diálogo** nativo ofrece Ninguno, Gestionar cuenta, Eliminar cuenta (también para eliminar roles en las vistas de roles) y Enlace único. Los estados se aplican cuando corresponde: colecciones vacías de cuentas/roles, enlaces de invitación/restablecimiento no válidos, validación del formulario actual, denegación de permisos a usuarios autenticados y recuperación de escrituras sin conexión. Las combinaciones de estado y vista que no correspondan conservan la vista base en lugar de inventar resultados del dominio.

En **Gestionar cuenta**, el selector de registros de prueba, etiquetado explícitamente como Maqueta, muestra a Pedro (sin trabajo guardado; se puede reactivar/eliminar), Camila (con trabajo guardado; se bloquea la eliminación) y Ana (última administradora; se bloquean la eliminación, desactivación y degradación de rol). Para eliminar, se exige el correo electrónico exacto y se explica que el uso anonimizado de IA se conserva. El estado protegido inicializa a Camila; al abrir Eliminar desde ese estado, se muestra la denegación sin confirmar ninguna acción destructiva. En las vistas de roles, la misma escena destructiva se refiere a un rol, no a una cuenta.

Invariantes importantes de implementación: `ROL_SIN_PERMISOS`, `CUENTA_CON_TRABAJO` y `LINK_INVALIDO` son resultados del servidor con texto de recuperación para las personas; ninguna cadena de código es la única explicación para el usuario. Las API de cuentas/roles aplican los permisos de forma independiente de esta representación. Una actualización de rol afecta a la siguiente solicitud, no solo a la visibilidad de la navegación. El aprovisionamiento inicial del administrador en producción y la gestión real de invitaciones no se simulan mediante una omisión en el frontend.

## Objetivos de diseño adaptable y accesibilidad

- **360–767px:** 20px de margen exterior e interior en el pase; la hoja física se convierte en una franja superior compacta; los campos se apilan; los registros de cuenta conservan nombre/correo electrónico, rol, estado y acción; la empresa queda fuera de la fila de escaneo. El índice de roles y los grupos de permisos se apilan. El panel inferior cabe dentro de los mismos márgenes laterales de 20px. Se mantiene el desplazamiento por todo el documento; la reserva inferior de 110px despeja el panel fijo.
- **768–1023px:** pase de dos hojas, 24px de espacio en el mundo y la hoja; la tabla omite la empresa, no el rol/estado de acceso; los grupos de permisos usan una columna.
- **1024px en adelante:** pase de acceso de 950px y escenario administrativo de 1120px, cinco columnas en la lista, permisos agrupados en dos columnas. El panel fijo reserva 120px al pie del documento.
- Los rótulos visibles, la semántica real de los campos, los objetivos de acción de 44px, las casillas con nombre, los anuncios de estado/error, texto con contraste ≥4.5:1 y bordes de controles/foco con contraste ≥3:1 son objetivos que se comprueban en la auditoría de la interfaz renderizada cuando corresponde. Las casillas de roles del sistema están desactivadas y acompañadas de un texto explícito de solo lectura. Los diálogos vuelven inerte el fondo y restauran el foco al cerrarse. No se usan datos personales reales ni recursos externos.
- Todos los efectos son animaciones finitas de transformación, no procesos en segundo plano perpetuos. Una pestaña oculta pausa la animación CSS. El proveedor de movimiento recibe el perfil seleccionado real y el estado de movimiento reducido; `prefers-reduced-motion`, Quieto y `?still=1` eliminan el desplazamiento y mantienen disponibles todos los estados.

## Trazabilidad y comprobaciones visuales

SP-2 cubre **R1, R3, R16**. Esta exploración puede orientar T2.1 (copiar el artefacto aprobado), T2.3 (acceso/activación/restablecimiento/aviso), T2.4 (menú de cuenta/Mi cuenta), T2.5 (administración y roles), T2.7 (revisión visual), T2.8 (auditoría independiente); T2.2 es responsable del comportamiento de API y T2.6 de la integración real entre navegadores. **Compatibilidad: indeterminada hasta que el owner seleccione una dirección; los cambios de composición/navegación requieren adaptar esas tareas de interfaz.** No se modificó ningún consumidor del plan ni estado de aprobación.

| ID | Punto de quiebre | Estado | Comportamiento observable esperado |
|---|---|---|---|
| B-AC-01 | 1024px+ | login/normal | La marca, el pase y el pie se alinean deliberadamente sobre ejes comunes; los rótulos del formulario, los campos, la recuperación y el pie comparten el mismo borde izquierdo. |
| B-AC-02 | 360–767px | all | El documento no se desplaza horizontalmente; el panel inferior deja el último control accesible por encima del espacio inferior reservado. |
| B-AC-03 | all | activar/normal | La activación permanece deshabilitada hasta que se marca la casilla del aviso etiquetada. |
| B-AC-04 | all | login/error | Un mensaje genérico incluye una espera de quince minutos sin revelar si la cuenta existe ni su estado. |
| B-AC-05 | all | activar or restablecer/enlace-invalido | Un único mensaje de enlace usado/vencido solicita un nuevo enlace del administrador. |
| B-AC-06 | all | gestionar/protegido | La eliminación de una cuenta con trabajo guardado está deshabilitada y se explica la desactivación como alternativa de recuperación. |
| B-AC-07 | all | gestionar/Ana fixture | Los controles de rol de la última administradora, desactivación y eliminación están deshabilitados con un motivo visible. |
| B-AC-08 | all | roles/normal | Los conjuntos de permisos de los cinco roles del sistema son de solo lectura; el rol personalizado se puede editar por separado. |
| B-AC-09 | all | rol/validacion | Todas las casillas de permisos están sin marcar y se muestra la explicación de que no hay permisos. |
| B-AC-10 | all | roles/protegido | No se puede eliminar un rol personalizado seleccionado que tiene cuentas asignadas; el siguiente paso es reasignarlas. |
| B-AC-11 | all | enlace dialog | El enlace se identifica como ilustrativo; se indican explícitamente el vencimiento y la presentación por única vez, y si falla la copia se ofrece una alternativa manual. |
| B-AC-12 | all | dark/all | Los campos de entrada, selectores, casillas sin marcar y el foco del teclado tienen bordes visibles sobre sus superficies. |
| B-AC-13 | all | reduced / still | El escenario, el pase, los globos y la lista quedan inmóviles, sin animaciones en curso; todos los controles siguen funcionando. |

Instantáneas de las fuentes consultadas para esta exploración:

| Entrada | SHA-256 |
|---|---|
| SPEC.md | `65b1e5ecc06f20d97fe6151dacc30d0bec0d7d0736aaa95db7a1c9af1b44f5e4` |
| PLAN.md | `cc7e53f2abf3c23c1bb8cde797cabf6005719d2dd8183295595a0a2bf5c18ca3` |
| PLAN.json | `7a2c833a7e711508d0a3bc96edb2d3f0d42ff6fe57a6370f62ce0d438338ffc8` |
| Shared r7 behavior | `c665ab01443531a74cf5f1dc1cb936ab9e2d70f650308d6842f2cd4dd8072a43` |

## Evidencia de auditoría

La compilación real sin conexión se completó correctamente (aproximadamente 760 KB, 2292 archivos de origen). El TSX es autónomo; contiene CSS personalizado en una cadena sin procesar que React representa. Tras la compilación, ese CSS exacto también se copia en una etiqueta `<style data-direction="b">` estática en el mismo HTML de salida para que el comprobador de tokens sin navegador evalúe las personalizaciones del proyecto. Al volver a compilar, se debe repetir esa extracción; no se requiere ni se autoriza ningún archivo CSS adicional.

Patrón de comandos:

```sh
python3 /home/david/dev/metodologia/skill/scripts/bitacora.py components mockup build /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.tsx --out /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html
python3 /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/contrast.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html
UV_OFFLINE=1 uv run --offline --with playwright python /home/david/dev/metodologia/skill/agents/designer/skills/david-ui-kit/kit/audit_mockup.py /home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/design/cuentas-admin@v1.r7.dir-b.html --max-combos 300
```

Contraste de tokens: `contrast: 158 pairs checked in light and dark, all pass`.

Primera auditoría completa de la interfaz renderizada: 468 renderizados / 468 combinaciones planificadas, 9798 mediciones de texto, 1563 paradas de foco; `RESULT: FAIL — contrast 1, alignment 1`. Se corrigió el enlace oscuro sin conexión para reintentar (el texto destructivo heredado ahora cumple el contraste) y la acción aislada centrada para cerrar sesión al aceptar el aviso (ahora es una acción secundaria estándar con contorno). Una ejecución preliminar anterior se interrumpió mientras se refinaba la composición; no se afirma que haya aprobado.

Auditoría final de la interfaz renderizada: **468 renderizados (468 combinaciones planificadas), 9806 mediciones de texto, 1554 paradas de foco**.

`RESULT: PASS — no contrast, non-text, focus, alignment, padding or overflow problems`

Se inspeccionaron visualmente capturas de pantalla en memoria a 1280 y 390 en ambos temas; no se crearon archivos de captura fuera de la lista permitida. Las comprobaciones interactivas con Playwright aprobaron el control de aceptación, la escritura ininterrumpida de contraseñas/búsquedas y la conservación del foco, la activación correcta, las restricciones para eliminar cuentas con trabajo guardado y a la última administradora, Escape y el retorno del foco, la validación de cero permisos, los marcadores de posición del aviso en inglés y `?still=1`. Otras comprobaciones aprobaron la eliminación de un rol personalizado sin cuentas asignadas (el índice se actualiza), el bloqueo de la eliminación de un rol asignado, la evidencia del selector en las vistas de cuentas/roles/activación y la ausencia de desbordamiento horizontal a 390, 768 y 1280px; el borde inferior del panel se midió en 888/880/880px en una ventana gráfica de 900px. No se observaron errores de JavaScript ni solicitudes HTTP(S) durante ese recorrido. La inspección del movimiento en vivo confirmó el movimiento del pase, los tres globos y el escenario a los 180ms del montaje. Estas comprobaciones demuestran el comportamiento del prototipo, no la seguridad de producción ni la aprobación legal.

## Preguntas abiertas

P: Legal del owner / Sempertex: ¿qué nombre de entidad legal, correo electrónico de contacto para derechos y URL de política deben sustituir los campos entre corchetes del aviso aceptado, y quién confirmará la revisión legal antes de enviar invitaciones reales?
P: Owner: ¿se debe elegir «Pase al montaje» y su panel inferior persistente para finalizar, o debería otra dirección de r7 definir el contrato compartido final?

Confirmado, no reabierto: un rol por cuenta; los planes son roles del sistema; contraseñas de mínimo ocho caracteres; invitaciones de siete días; restablecimientos de 24 horas; la regeneración de enlaces invalida los enlaces anteriores sin usar del mismo tipo; persistencia de la versión/fecha de aceptación; rechazo de la eliminación de cuentas con trabajo guardado; conservación del gasto en IA sin datos personales; roles del sistema de solo lectura. Estos comportamientos no son alternativas de diseño.
