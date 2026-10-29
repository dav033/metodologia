# Brief de interfaz — SP-7 · Chat asistido como tres herramientas y explorador de decoraciones

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

El chat asistido se convierte en tres herramientas en una página de inicio que muestra solo las herramientas del plan de la cuenta: el chat guiado como chat normal (sin precios si no se cuenta con el permiso de costos), un contador de globos por forma, frase o foto sin precios y la calculadora profesional de costos existente, con precios, mano de obra, transporte y margen editables; el gasto de IA de cada herramienta se mide por separado y las cantidades y los precios provienen solo del motor y del catálogo real; una galería de decoraciones listas para usar dentro del Taller 3D (Diseñador Maestro y personal) abre una decoración como proyecto nuevo mediante un enlace.

## Requisitos que cubre

- R13: El chat asistido debe dividirse en una calculadora de costos, un contador de globos y un chat normal; el chat normal debe conectarse al taller 3D.
- R16: Cuando un administrador asigna uno de los cuatro planes de acceso a una cuenta de Usuario, el sistema debe otorgar en el servidor exactamente las herramientas de ese plan, de forma acumulativa: Entusiasta, el chat asistido y el contador de globos; Designer, las mismas herramientas (sus límites de chat más altos quedan pendientes hasta definir los valores de los límites); Designer Plus agrega la calculadora de costos; Master Designer agrega el Taller 3D; Empleado interno y Administrador deben tener todas las herramientas de los planes (enmienda del 2026-10-27, ronda 10).

## Criterios de producto

- La página de inicio / muestra únicamente las herramientas otorgadas por el rol de la cuenta que inició sesión; cada una abre su propia página. La página del chat clásico desaparece, mientras que /api/chat sigue atendiendo el agente del plan del chat guiado.
- La página del contador de globos cuenta por formulario, frase o foto, muestra las cantidades por tamaño y color y la lista de compras sin precios, y ofrece «Calcular costo» solo a las cuentas con costos.usar.
- La página de la calculadora de costos recibe el resultado del contador o materiales ingresados manualmente, permite editar los precios de los globos y agregar mano de obra, transporte, costos indirectos y margen, y muestra precios por producto del catálogo real y los totales de la cotización profesional.
- La galería de decoraciones en /3d/decoraciones muestra todos los elementos de Ideas del asistente e Ideas Sempertex con búsqueda, filtros de ocasión y tamaño, y una vista previa; «Abrir como proyecto nuevo» abre /3d?decoracion=<id> como una escena nueva sin guardar.
- Solo se puede acceder a la galería y a su enlace directo con decoraciones.explorar; las demás cuentas reciben la página de acceso denegado, y un id de decoración desconocido muestra un mensaje de que no se encontró, sin cambiar la escena abierta.
- Las pantallas renderizadas de inicio, contador, calculadora y galería coinciden con el contrato aprobado herramientas-chat@v1 en anchos de teléfono, tableta y escritorio, y cada hallazgo se registra junto con la tarea que debe repetirse en el registro visual de SP-7.

## Flujos de usuario

1. Iniciar sesión → la página de inicio muestra solo las herramientas del rol → abrir una herramienta
2. Contador: formulario (estructura, medidas, tamaños, colores), frase o foto → cantidades por tamaño y color + lista de compras sin precios → «Calcular costo» solo con el permiso de costos
3. Calculadora: desde el resultado del contador o materiales ingresados manualmente → editar precios de globos, mano de obra, transporte, costos indirectos y margen → precios por producto y totales
4. Galería (Taller, Master Designer y personal): búsqueda, filtros de ocasión y tamaño, vista previa → «Abrir como proyecto nuevo» abre /3d?decoracion=<id>

## Pantallas y estados

- Inicio: de una a cinco tarjetas de herramientas según el rol; el estado vacío es imposible (todos los roles tienen al menos una herramienta)
- Contador: inactivo, pregunta por medidas faltantes, contando, resultado, foto demasiado grande o que no es una imagen, error del motor
- Calculadora: vacía, importada del contador, editando, calculando, totales, error de cotización
- Galería: cargando, resultados, no hay resultados para un filtro, enlace a decoración desconocida, al abrir hay trabajo sin guardar en el Taller

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- components: `VistaGuiada (/asistente, mantiene el chat normal)`, `CotizacionProfesional (materiales, mano de obra, equipos y transporte, costos indirectos, margen)`, `IdeasDelAsistente y Biblioteca en el Taller`, `CabeceraApp / MenuApp shell`, `MenuCuenta (SP-2)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Leído en origin/main a9f3d6e5. La página del chat clásico en / (src/app/page.tsx) está retirada; / se convierte en la página de inicio de herramientas. La cotización profesional ya existe dentro del chat guiado y del Taller; la página de la calculadora la reutiliza.

## No debe cambiar

- El flujo de conversación del chat guiado, excepto por quitar los precios a las cuentas sin permiso de costos
- El editor del Taller y su panel de biblioteca existente
- El cálculo de la cotización profesional (Python es responsable de los totales)

## Reglas de copy

- Interfaz en español; cada cadena nueva debe estar en un módulo textos-*.ts por pantalla para la traducción de SP-10
- Nunca mostrar un precio, total o cotización a una cuenta sin permiso de costos, ni indicar qué plan tiene una herramienta bloqueada
- Las cantidades y los precios son los valores del motor; la cantidad calculada a partir de una foto debe etiquetarse como estimación e indicar su tolerancia
- Los nombres de las herramientas provienen de plan-catalogue@1 (Chat con límites / con límites más altos, Contador de globos, Calculadora de costos)
- Sin nombres, fechas, eslóganes, titulares ni textos de marketing inventados: usa los textos de los requisitos o de la interfaz existente; los datos de ejemplo deben ser neutrales, realistas, claramente identificados como ejemplos y solo incluirse cuando los flujos los necesiten.

## Tareas de interfaz

- T7.1 — Copiar al repositorio el contrato herramientas-chat@v1 aprobado por el propietario
  - Objetivo: El repositorio contiene el contrato visual exacto aprobado por el propietario para la página de inicio de herramientas, el contador, la calculadora y la galería de decoraciones antes de construir cualquiera de estas pantallas.
- T7.5 — Página de inicio de herramientas en / y retiro de la página del chat clásico
  - Objetivo: Al iniciar sesión se llega a una página de inicio que muestra solo las herramientas otorgadas por el rol, y la antigua página del chat clásico deja de existir.
- T7.6 — Página del contador de globos: formulario, frase y foto con resultados sin precios
  - Objetivo: Una persona cuenta los globos de una decoración por formulario, frase o foto y ve las cantidades por tamaño y color y la lista de compras, nunca un precio.
- T7.7 — Página de la calculadora de costos basada en la cotización profesional existente, con datos del contador o ingresados manualmente
  - Objetivo: Una persona con permiso de costos calcula el precio de una decoración en su propia página, con precios editables de globos, mano de obra, transporte, costos indirectos y margen.
- T7.8 — Galería de decoraciones listas para usar en el Taller con un enlace para abrirlas como proyectos nuevos
  - Objetivo: Un Master Designer o un miembro del personal explora las decoraciones 3D listas para usar, las filtra y abre una como una escena nueva sin guardar, mediante un enlace que el chat puede reutilizar.
- T7.10 — Revisión visual de SP-7 según el contrato herramientas-chat@v1
  - Objetivo: Una persona revisora sin participación previa compara las pantallas renderizadas de inicio, contador, calculadora y galería con el contrato aprobado en tres anchos y registra cada discrepancia junto con la tarea que debe repetirse.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, que no sean de diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest, criterios de aceptación exclusivos de ingeniería. Tareas omitidas: T7.2, T7.3, T7.4, T7.9, T7.11.
