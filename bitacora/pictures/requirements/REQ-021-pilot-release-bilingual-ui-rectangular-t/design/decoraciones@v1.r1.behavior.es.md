# Brief de interfaz — SP-5 · Decoraciones guardadas

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Un Master Designer con sesión iniciada guarda una composición de escena con nombre o una pieza seleccionada en una biblioteca personal de decoraciones del servidor y la coloca en proyectos; los roles de empleado y administrador pueden abrir en modo de solo lectura los elementos de otra cuenta, mientras que solo el propietario puede actualizarlos o eliminarlos. Las entradas existentes de la biblioteca local del navegador siguen siendo locales y no se importan durante el piloto de preproducción.

## Requisitos que cubre

- R8: Cuando un usuario guarda una composición como decoración, el sistema debe agregarla a su biblioteca personal.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-5 (round 11 answered)»

## Criterios de producto

- Un usuario con sesión iniciada puede guardar la escena actual o la pieza seleccionada con un nombre y una ocasión, y el elemento guardado aparece en la biblioteca personal de esa cuenta después de recargar y desde otro navegador.
- Un usuario puede colocar un elemento guardado en un proyecto; los roles de empleado y administrador pueden abrir en modo de solo lectura las decoraciones guardadas de otra cuenta, pero solo la cuenta propietaria puede actualizarlas o eliminarlas, incluso mediante solicitudes directas a la API.
- Las entradas existentes en `taller3d:biblioteca-propia:v1` no se importan durante el piloto de preproducción y permanecen en su biblioteca original local del navegador.

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

- T5.1 — Copiar el contrato aprobado de interfaz para la biblioteca personal de decoraciones
  - Objetivo: El contrato exacto aprobado decoraciones@v1 queda fijado en el repositorio antes de cambiar la interfaz de la biblioteca de Taller.
- T5.3 — Conectar los flujos de guardar, colocar e importar de forma idempotente la biblioteca del navegador en Taller
  - Objetivo: Reemplazar la persistencia exclusiva en el navegador de `Biblioteca.tsx` como fuente de verdad por la API de cuenta, preservando las interacciones existentes para guardar la escena actual, guardar la pieza seleccionada, colocar, cambiar el nombre y eliminar. No importar elementos de `taller3d:biblioteca-propia:v1` durante este piloto de preproducción; conservar intactos los registros locales actuales del navegador. Mostrar un estado de solo lectura cuando el personal abra un elemento guardado de otra cuenta, mientras que los controles exclusivos del propietario siguen disponibles para este. Al cerrar sesión o cambiar de cuenta, borrar las entradas en memoria derivadas de datos remotos antes de mostrar la siguiente cuenta.
- T5.4 — Verificar la persistencia entre navegadores, la colocación y el aislamiento por propietario
  - Objetivo: Un escenario de integración con el punto de entrada real demuestra que las decoraciones personales persisten entre navegadores, se pueden colocar en proyectos, permanecen aisladas entre usuarios e importan las entradas heredadas del navegador sin pérdidas.
- T5.5 — Revisar la interfaz renderizada de la biblioteca personal frente a su contrato
  - Objetivo: Los estados renderizados de guardado, importación, biblioteca vacía, carga, reintento, éxito y error de la biblioteca personal coinciden con el contrato de interfaz aprobado en anchos de teléfono y escritorio, con nombres accesibles, navegación por teclado y un estado de guardado veraz.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, tareas que no son de diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T5.2, T5.6.
