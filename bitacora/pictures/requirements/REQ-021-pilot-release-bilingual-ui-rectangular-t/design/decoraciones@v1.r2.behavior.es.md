# Brief de interfaz — SP-5 · Decoraciones guardadas

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Un Diseñador Maestro con sesión iniciada (y el personal) guarda una composición de escena con nombre o una pieza seleccionada en una biblioteca personal de decoraciones del lado del servidor y la coloca en proyectos desde cualquier navegador; Empleado interno y Administrador abren en modo de solo lectura los elementos de otra cuenta, y solo el propietario los actualiza o elimina; una cuenta con decoraciones guardadas no se puede eliminar, solo desactivar; las entradas existentes de la biblioteca local del navegador permanecen locales y no se importan durante el piloto.

## Requisitos que cubre

- R8: Cuando un usuario guarda una composición como decoración, el sistema debe agregarla a su biblioteca personal.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-5 (round 11 answered)»

## Criterios de producto

- Desde el Taller, una persona guarda la escena actual o la pieza seleccionada con un nombre y una ocasión, ve la confirmación de guardado solo después de que el servidor lo confirme, y encuentra el elemento después de recargar y en otro navegador de la misma cuenta.
- Se puede buscar un elemento guardado y colocarlo en el proyecto abierto; los controles existentes de nombre, ocasión, miniatura y filtro siguen funcionando.
- Cuando el personal abre un elemento de otra cuenta, queda claramente en modo de solo lectura: no aparecen controles para cambiar el nombre, editar ni eliminar, y al colocarlo se añade una copia al proyecto propio del miembro del personal.
- Las entradas que ya están en la clave del navegador taller3d:biblioteca-propia:v1 permanecen intactas en la lista local de ese navegador, no se importa nada y, al cambiar de cuenta o cerrar sesión, nunca se muestran los elementos del servidor de la cuenta anterior.
- Los estados renderizados de guardar en la biblioteca personal, lista, solo lectura, vacío, carga, reintento y error coinciden con el contrato aprobado decoraciones@v1 en los anchos de teléfono y escritorio; cada hallazgo se registra junto con la tarea que debe rehacerse en el registro visual de SP-5.

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
  - Objetivo: El repositorio contiene el contrato decoraciones@v1 exacto y aprobado por el propietario antes de que cambie la biblioteca del Taller.
- T5.3 — Biblioteca personal del Taller con la API de cuenta: guardar, colocar, solo lectura para el personal y cambio de cuenta
  - Objetivo: La biblioteca personal del Taller guarda y lee mediante la API de cuenta, mantiene locales las entradas antiguas del navegador y nunca muestra los elementos de una cuenta a otra.
- T5.5 — Revisión visual de SP-5 frente al contrato decoraciones@v1
  - Objetivo: Un revisor nuevo compara la biblioteca personal renderizada con el contrato aprobado y registra cada discrepancia junto con la tarea que debe rehacerse.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, sin diseño ni revisión), verificación, expected_paths, shared_resources, classification and estimates, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T5.2, T5.4, T5.6.
