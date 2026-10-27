# Brief de interfaz — SP-2 · Sign-in, invitation and administration screens

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A person signs in with email and password, activates an invitation link and accepts the data notice; an administrator invites people, assigns role or access plan, creates roles by choosing permissions, and deactivates or deletes accounts.

## Requisitos que cubre

- R1: When an administrator invites an email, the system shall let that person create a password and sign in; open registration shall not exist.
- R3: When an administrator creates a role, the system shall let them choose its permissions from a defined list; the three initial roles shall exist.
- R16: When an administrator assigns an access plan to an external account, the system shall grant exactly that plan's tools: Plan 1 the assisted chat and the balloon counter; Plan 2 adds the cost calculator and the ready-made decorations explorer; Plan 3 adds the Taller 3D.

Secciones de SPEC.md que nombran este subplan (léelas): «Data-processing notice (v1, SP-2)»

## Criterios de producto

- On /login a person signs in with email and password; a wrong password, an unknown email, a deactivated account and a locked email all show the same message, which always adds that after several failures one must wait fifteen minutes, and success returns to the requested page or the first area the role allows, or Mi cuenta when the role has none of them.
- Opening an invitation link shows the invited name and email, asks for a password of at least eight characters twice and shows the data notice in the browser language with an accept checkbox, activation is impossible without accepting, and after activating the person lands signed in on the first tool their role allows; a used or expired link shows a message to ask the administrator for a new one.
- When the notice version changes, a signed-in person must accept the new version before any other page opens.
- Every signed-in page shows an account menu with the person's name and role, Mi cuenta and sign out, and Mi cuenta changes the password by asking for the current one.
- An administrator invites a person by name, email, optional company and role, and gets the single-use link once with a copy button; an email already registered is refused with a clear message.
- An administrator changes an account's role, deactivates and reactivates it, generates a reset link and deletes an account without saved work after typing its email, and the screen explains why the last administrator or an account with saved work cannot be deleted.
- An administrator creates and edits a custom role by name and permission checkboxes grouped by tool, sees the five system roles read-only with their permissions, and cannot delete a role that still has accounts.
- The rendered sign-in, activation, account and administration screens match the approved cuentas-admin@v1 contract at phone, tablet and desktop widths, and every finding is recorded with the task to redo in the SP-2 visual ledger.

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

- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T2.1 — Copy the owner-approved cuentas-admin@v1 contract into the repository
  - Objetivo: The repository holds the exact owner-approved visual contract for the sign-in, activation, account and administration screens before any of them is built.
- T2.3 — Sign-in, invitation activation, password reset and notice re-acceptance screens
  - Objetivo: A person signs in, activates an invitation accepting the data notice, resets a password from an administrator's link and re-accepts a new notice version, with the states the contract defines.
- T2.4 — Account menu on every signed-in page and the Mi cuenta page
  - Objetivo: Every signed-in person sees who they are and their role, signs out, and changes their own password from Mi cuenta.
- T2.5 — Administration screens: accounts list, invitations, account actions and the role editor
  - Objetivo: An administrator manages every account and custom role from two screens that show exactly what each action will do and why one is refused.
- T2.7 — SP-2 visual review against the cuentas-admin@v1 contract
  - Objetivo: A fresh reviewer compares the rendered screens with the approved contract at three widths and records every mismatch with the task to redo.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T2.2, T2.6, T2.8.
