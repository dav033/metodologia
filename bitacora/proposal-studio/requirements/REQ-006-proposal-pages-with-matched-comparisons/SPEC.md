---
id: REQ-006
status: done
created: 2026-10-11
track: standard
---
# REQ-006 — Proposal pages with matched comparisons

## Problem & goal
Una propuesta solo permite comparar la portada actual con una única portada de prototipo. David necesita mostrar páginas concretas como Servicios y Contacto, emparejando cada URL actual con su ruta equivalente del prototipo.

**Success looks like:** una propuesta admite varias vistas emparejadas; cada vista muestra la captura PNG actual y permite navegar el prototipo de esa ruta en el mismo comparador.

## Users / actors / stakeholders
- David administra propuestas; el prospecto navega las páginas publicadas desde el enlace temporal existente.

## Scope (in)
### US-1 (P1, Must) — Añadir páginas adicionales a una propuesta
Como administrador, quiero agregar una vista con nombre, URL actual, ruta del prototipo y una captura PNG para representar las páginas que deseo comparar.
**Acceptance:** el editor permite añadir y quitar páginas adicionales sin cambiar el formulario corto de creación; cada página conserva su imagen y rutas al guardar.

### US-2 (P1, Must) — Navegar comparaciones en el enlace compartido
Como prospecto, quiero seleccionar Inicio, Servicios u otra vista y usar el comparador en esa página.
**Acceptance:** cambiar de vista actualiza captura y prototipo juntos; la navegación funciona en escritorio y móvil.

## Out of scope
- Descubrir o rastrear automáticamente todas las páginas de un sitio.
- Tomar capturas remotas desde el servidor de Proposal Studio. Las capturas se producen fuera del formulario y se suben como PNG.
- Cambiar el formato de prototipos importados desde GitHub o permitir repositorios distintos por página.

## Requirements
- R1. When an administrator adds a page, the system shall store its display name, source URL, prototype path and privately stored PNG capture.
- R2. When no prototype path is supplied, the editor shall prefill it from the source URL path; the administrator may edit it.
- R3. When a proposal is published, every configured additional page shall have a PNG capture and a usable prototype route.
- R4. When a prospect opens a shared proposal, the system shall show the existing homepage comparison and controls for every additional page in that published revision.
- R5. When a prospect selects an additional page, the system shall serve only its published screenshot and matching prototype asset under the existing time-limited share session.
- R6. Existing proposals without additional pages shall continue to render as before.

## Edge cases & errors
- Reject invalid source/prototype URLs, duplicate page identifiers, more than 12 additional pages, invalid PNG files, and incomplete pages at publish time.
- A page missing its screenshot or imported prototype asset must be identified in the editor and must not publish.
- Active links keep the exact page list and captures from their published revision when later draft edits occur.

## Constraints
Use existing Astro, Postgres JSON content, private Blob storage, GitHub-imported prototype revision, and share-session authorization. Do not run database migrations against production. Keep images private and expose them only through the existing authorized share-asset endpoint.

## Priorities & phases
MVP: manually add a page and PNG, match its prototype path, publish, and navigate the comparisons. Automatic remote capture and site crawling are deferred.

## Timeline & dependencies
Depends on the current REQ-005 proposal editor, GitHub prototype import, private screenshot storage, and temporary share links. No deadline supplied.

## Assumptions
The existing homepage fields remain the homepage view; added routes are additional views. One imported prototype revision serves all routes in a proposal. The PNGs David supplied for Oraldenti are preparation artifacts; adding them to a proposal is a separate editor action.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities | Clear |
| Timeline | Clear |

## Clarifications
### Round 1 — 2026-10-11
- Q: ¿Las páginas se agregan manualmente y se emparejan por defecto con la misma ruta del prototipo? → A: Sí; URL origen manual, ruta de prototipo por defecto igual y editable.
- Q: ¿Quién toma las capturas? → A: David puede enviar las URLs al asistente para generar PNGs; la app recibe una captura subida por página.
- Q: ¿El prototipo debe tener una ruta distinta por cada página? → A: Sí, una correspondencia de ruta por vista dentro del prototipo importado.
