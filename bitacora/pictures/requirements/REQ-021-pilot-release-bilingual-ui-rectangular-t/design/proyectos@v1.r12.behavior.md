# Brief de interfaz — SP-4 · Saved projects

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

A user saves, lists, reopens and continues Taller projects stored under their account; employees and administrators open anyone's; a later save never silently overwrites an earlier one; scenes saved in the browser are offered for import on first sign-in without loss.

## Requisitos que cubre

- R6: When a user saves a project, the system shall store it server-side under their account; employees and administrators shall be able to open any project.
- R7: When a user first signs in with browser-saved scenes, the system shall offer to import them without data loss.

Secciones de SPEC.md que nombran este subplan (léelas): «Behavior — SP-3 and SP-4 (round 9 answered)»

## Criterios de producto

- The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response.
- Two open copies cannot silently overwrite each other: a 409 stops autosaving, keeps the unsent local scene and offers loading the server version or saving a new owned copy; staff/admin read foreign originals without write access and may save an owned copy only with taller.usar.
- The first named save is explicit and later edits autosave; a project list search finds authorized matches beyond the first loaded page, filter changes reset pagination and obsolete query responses cannot replace current results.
- A signed-in account with a legacy browser scene is offered an explicit import; acceptance creates exactly one owned project even after retry, refusal or validation failure preserves raw local data, and no account receives a legacy scene automatically.
- Project list, saving/offline/conflict states, foreign read-only view and import prompt match approved proyectos@v1 at phone, tablet and desktop widths with keyboard and focus behavior verified.
- «Escena nueva», a template or «Abrir en Escena» start a new unsaved project: the open project keeps its last saved revision (its pending edits are saved first, or the user is asked before a never-saved scene is discarded), the new scene is linked to no project and nothing reaches the server until its first named save.

## Flujos de usuario

1. First save and autosave
   1. Builds a scene in the Taller 3D
   2. Saves it with a name the first time
   3. Keeps editing; later changes save automatically with a visible status and a Save now control
2. Start a new project
   1. From an open project, chooses «Escena nueva», a template, or «Abrir en Escena» on a library item
   2. Pending edits of the open project are saved first; a never-saved scene asks before being discarded
   3. Gets a new unsaved project named «Escena nueva», linked to no saved project
   4. Saves it with a name the first time; autosave starts after that
3. Reopen in another browser
   1. Opens /proyectos in another browser signed in as the same account
   2. Searches or browses the list
   3. Opens the project and gets the complete scene and its name
4. Competing save
   1. Two open copies of the same project save from the same revision
   2. The later save shows a conflict, stops autosaving and keeps the local draft
   3. Chooses to load the server version or save an own copy
5. Offline
   1. Edits while the connection is lost
   2. Sees the work is not saved yet
   3. Retries when back online
6. Staff opens someone else's project
   1. Employee or administrator filters the list by owner
   2. Opens the project read-only
   3. Saves an own copy (only with the Taller permission)
7. Import a scene saved in the browser
   1. Signs in with a legacy taller3d:escena:v1 scene in this browser
   2. Is asked whether to import it into this account
   3. Accepts (one project is created even after retries) or refuses (the local data stays)
   4. With invalid data, sees why and can download the original

## Pantallas y estados

- /proyectos list: empty, loading, results, search with no match, next page, next-page failure with retry
- Owner filter for employees and administrators
- First named save dialog
- New unsaved project after «Escena nueva», a template or «Abrir en Escena»: name «Escena nueva», status not saved yet, the first save asks for the name
- Save status in the Taller header (extends today's «Guardado» / «Guardando…» / «Sin guardar» text next to the scene name): saving, saved to the account, not saved (offline), error, conflict
- Conflict panel: load the server version or save an own copy; the local draft is kept
- Read-only view of another owner's project with the Save copy action
- Legacy import prompt: accept, refuse, invalid data with explanation and download
- Phone, tablet and desktop widths

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/3d`, `/proyectos (new)`, `/proyectos/[id] (new)`
- paths: `src/app/3d/page.tsx`, `src/components/tres-d/Taller3D.tsx`, `src/components/tres-d/guardado-escena.ts`, `src/components/tres-d/guardado-conversacion.ts`, `src/components/tres-d/imagenes-guardadas.ts`, `src/app/api/decoraciones/route.ts`
- components: `Taller3D`, `ExportarEscenaTaller`, `MenuCuenta (planned by SP-2 T2.4)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: Read on origin/main a9f3d6e5. Already there: the Taller header has an inline-editable scene name («Escena nueva» by default, renamed in place) and a save status text «Guardado» / «Guardando…» / «Sin guardar (el navegador no deja)», which today means browser storage: one scene per browser in localStorage key taller3d:escena:v1, written 500 ms after the last change (guardado-escena.ts; invalid or old input silently discarded). Templates, «Sala vacía» and opening a library item replace that single scene. The AI conversation is a separate localStorage entry and generated images live in IndexedDB. Not there: any server storage of scenes, any project list or /proyectos route, project identity, conflicts, import or a read-only view; /api/decoraciones is the global decorations library of the admin screens (SP-5 territory), not projects. So the save status and the scene name are existing elements SP-4 extends to server projects; the list, the first-save dialog, the conflict panel, the read-only view and the import prompt are new. Owner-confirmed 2026-10-27: «Escena nueva», a template or «Abrir en Escena» (Biblioteca.tsx) start a new unsaved project; pending edits of the open project are saved first and a never-saved scene asks before being discarded. No screenshots are stored in the repository.

## No debe cambiar

- Only the project name and the complete scene travel between browsers; the AI conversation and generated images stay in the browser
- The original browser data is never erased or changed by an import, a refusal or a failure
- No delete, transfer or version-history interface
- The Taller editing tools, shell, navigation and design tokens outside the save status, project list and import prompt
- A staff member never edits another owner's original

## Reglas de copy

- Spanish interface; every new string in src/components/proyectos/textos-proyectos.ts for later translation
- No invented copy: status words describe only the real state (saved, saving, not saved, conflict)
- Never label work as saved before the server confirmed that revision
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T4.1 — Copy the approved saved-projects design contract
- T4.4 — Implement the project list and conflict-safe Taller saving
  - Objetivo: The user names, saves, lists and reopens projects with their complete scene unchanged across browsers; pending edits are never labelled saved by an obsolete response. Owner 2026-10-27: «Escena nueva», a template or «Abrir en Escena» from the library start a new unsaved project named «Escena nueva».
- T4.5 — Implement a lossless and idempotent legacy-scene import
- T4.8 — Review the rendered project and import interfaces

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tasks outside the UI (ui:false, non-design/non-review), verification, expected_paths, shared_resources, classification and estimates, digest, engineering-only acceptance criteria. Tareas omitidas: T4.2, T4.3, T4.6, T4.7, T4.9, T4.31.
