# Brief de interfaz — SP-12 · Normal chat recommends ready-made 3D decorations

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

In two or three messages the guided chat defines the need and shows two or three ready-made 3D decorations from the gallery with preview, name and balloon count to every plan; Master Designer and staff can open one in the Taller 3D as a new project, other plans see the recommendation without the button; names and counts come only from the gallery and the engine.

## Requisitos que cubre

- R13: The assisted chat shall be split into a cost calculator, a balloon counter and a normal chat, and the normal chat shall connect to the 3D workshop.

## Criterios de producto

- The chat shows each recommendation as a card with preview, name in the session's language and balloon count; «Abrir en el Taller» appears only for accounts with decoraciones.explorar and opens /3d?decoracion=<id> as a new project, and other accounts see the card without the button and without any mention of a plan.

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

- T12.1 — Copy the owner-approved chat-a-3d@v1 contract into the repository
  - Objetivo: The repository holds the exact owner-approved chat-a-3d@v1 contract before the recommendation cards are built.
- T12.3 — Recommendation cards in the guided chat with a plan-gated open button
  - Objetivo: Every plan sees the recommended decorations as cards, and only accounts with the explorer open them in the Taller.
- T12.5 — SP-12 visual review against the chat-a-3d@v1 contract
  - Objetivo: A fresh reviewer compares the rendered recommendation cards with the approved contract and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T12.2, T12.4, T12.6.
