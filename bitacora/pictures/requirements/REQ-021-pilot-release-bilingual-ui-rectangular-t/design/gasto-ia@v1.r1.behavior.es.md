# Brief de interfaz — SP-6 · Gasto de IA por usuario y sesión

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Cada llamada pagada a un modelo de IA realizada correctamente por Next o services/ai-api se registra una sola vez con la cuenta autenticada, la sesión del servidor, el elemento de trabajo (proyecto, con detalles de la conversación cuando existe un contexto de proyecto; de lo contrario, conversación), herramienta, tipo de llamada (texto o imagen), proveedor/modelo, uso de tokens y costo estimado en USD. Empleado interno y Administrador pueden consultar los totales por usuario, sesión, elemento de trabajo, tipo y herramienta; las cuentas de Usuario común no pueden acceder a los datos.

## Requisitos que cubre

- R4: Cuando se completa una llamada pagada a IA, el sistema debe guardar los tokens y el costo estimado asociados al usuario y la sesión.
- R5: Con la sesión iniciada como empleado o administrador, el sistema debe mostrar los totales de gasto por sesión, tipo y usuario.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-6 (round 12 pending)»

## Criterios de producto

- Un empleado o administrador puede filtrar el uso por usuario y tipo y ver los totales por sesión y elemento de trabajo sin ver prompts, contenido generado, secretos de API ni otros datos personales innecesarios.
- Una cuenta de Usuario, un visitante con sesión cerrada o un llamador sin gasto.ver no puede acceder al panel ni a su API; la autorización se comprueba en el servidor.
- Un error del proveedor con uso facturable conocido conserva esos tokens/costos con un estado explícito de parcial/error; los campos que el proveedor no devuelve permanecen desconocidos y nunca se inventan.

## Flujos de usuario

- El Planner no los escribió: derívalos de los requisitos y de la superficie existente, sin inventar flujos.

## Pantallas y estados

- El Planner no los escribió: lista en el contrato las pantallas y estados que exigen los requisitos.

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

El Planner no nombró las pantallas actuales. No las adivines: localízalas en solo lectura en estos repositorios y basa el mockup en ellas; si no las encuentras, dilo en CONCERNS.
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`

## No debe cambiar

- El resto de la superficie existente: shell, navegación, cabecera, tokens, fuentes y componentes.

## Reglas de copy

- No inventes nombres, fechas, eslóganes, titulares ni textos de marketing: usa los textos de los requisitos o de la interfaz existente; los datos de ejemplo deben ser neutrales, realistas, claramente identificados como ejemplos y limitarse a los necesarios para los flujos.

## Tareas de interfaz

- T6.1 — Fijar el contrato aprobado de interfaz de gasto de IA
  - Objetivo: Copiar el contrato visual gasto-ia@v1 exacto y aprobado a design/contracts antes de crear el panel del personal.
- T6.4 — Crear el panel de gasto del personal y la API con filtros del servidor
  - Objetivo: Añadir una página y API protegidas por gasto.ver que filtren por usuario y tipo de llamada y agrupen los totales por sesión y elemento de trabajo, con contexto de herramienta/proveedor/modelo y fecha. Devolver solo los campos del registro necesarios para la revisión; nunca exponer cuerpos de prompts/respuestas. Usar consultas del servidor seguras para la paginación por cursor.
- T6.5 — Ejecutar comprobaciones de atribución de uso y autorización desde los puntos de entrada reales
  - Objetivo: Realizar una llamada de texto y una de imagen mediante Next y ai-api con usuarios precargados; verificar la atribución a usuario/sesión/elemento de trabajo, los totales, la idempotencia de reintentos, el comportamiento de metadatos parciales y la denegación de acceso a Usuario. Guardar la evidencia asociada a la base de datos aislada de REQ-021.
- T6.6 — Revisar el panel de gasto renderizado frente a gasto-ia@v1
  - Objetivo: Auditar la distribución adaptable, los estados de carga/vacío/error, las etiquetas de filtros, el acceso con teclado y que no se rendericen datos de prompts/cuerpos.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, sin diseño ni revisión), verificación, expected_paths, shared_resources, classification and estimates, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T6.2, T6.3, T6.7.
