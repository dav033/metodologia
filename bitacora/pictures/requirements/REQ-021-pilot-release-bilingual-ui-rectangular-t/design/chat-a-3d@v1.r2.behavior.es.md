# Brief de interfaz — SP-12 · El chat normal recomienda decoraciones 3D listas para usar

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

En dos o tres mensajes, el chat guiado define la necesidad y muestra a cada plan dos o tres decoraciones 3D listas para usar de la galería, con vista previa, nombre y cantidad de globos; Master Designer y el personal pueden abrir una en el Taller 3D como proyecto nuevo, y los demás planes ven la recomendación sin el botón. Los nombres y las cantidades provienen únicamente de la galería y del motor.

## Requisitos que cubre

- R13: El chat asistido debe dividirse en una calculadora de costos, un contador de globos y un chat normal; el chat normal debe conectarse al taller 3D.

## Criterios de producto

- El chat muestra cada recomendación como una tarjeta con vista previa, nombre en el idioma de la sesión y cantidad de globos; «Abrir en el Taller» aparece solo para las cuentas con decoraciones.explorar y abre /3d?decoracion=<id> como proyecto nuevo. Las demás cuentas ven la tarjeta sin el botón y sin menciones a ningún plan.

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

- T12.1 — Copiar el contrato chat-a-3d@v1 aprobado por el propietario al repositorio
  - Objetivo: El repositorio contiene el contrato chat-a-3d@v1 exacto aprobado por el propietario antes de que se creen las tarjetas de recomendación.
- T12.3 — Tarjetas de recomendación en el chat guiado con un botón para abrir, habilitado según el plan
  - Objetivo: Todos los planes ven las decoraciones recomendadas como tarjetas, y solo las cuentas con explorer pueden abrirlas en el Taller. Crear y registrar aquí scripts/test/test-integracion-recomendaciones-3d.ts, con los modos SP-12 y CG-12, fixtures deterministas del proveedor y la base de datos local REQ-021; sin llamadas pagadas a IA. Probar Entusiasta, Master Designer y personal, tarjetas en inglés, apertura de proyectos nuevos sin guardar, guardado, casos sin coincidencias y de permiso denegado mediante puntos de entrada reales.
- T12.5 — Revisión visual de SP-12 según el contrato chat-a-3d@v1
  - Objetivo: Un revisor independiente compara las tarjetas de recomendación renderizadas con el contrato aprobado y registra cada discrepancia junto con la tarea que debe rehacerse.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, no son de diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest, criterios de aceptación exclusivos de ingeniería. Tareas omitidas: T12.2, T12.4, T12.6.
