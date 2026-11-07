---
id: REQ-025
status: ready
created: 2026-11-07
track: standard
---
# REQ-025 — GPU render service: 14 views and colour layers for any chosen scene, internal staff only

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Today the 14 pre-rendered Cycles views (and the colour layers that let the chat recolour them) exist only for base templates, and
only when the coordinator runs the kit scripts by hand on David's laptop (the only GPU). A scene edited in the chat or the Taller 3D
falls back to the live 3D viewer. Internal staff want to pick a scene, press one button, and get the same presentation quality,
rendered on this laptop's GPU, with no agent in the loop.

**Success looks like:** an internal employee or administrator chooses a scene (chat, Taller 3D or base template), sees whether it
already has its 14 views, requests a render with a colour setting, follows its progress, and when it finishes the chat shows that
exact scene with the 14 views and working colour change, as Feliz Año does today. No manual step on the laptop.

## Users / actors / stakeholders
- Requesters: accounts with role `empleado_interno` or `administrador` (and the local administrator in development).
- Render worker: a service on David's laptop (RTX A3000, Blender 4.5 + presentacion-kit), the only GPU.
- Viewers: every chat user who later opens that scene (they see the views; they cannot request renders).
- Owner: David (approves visual quality; laptop availability).

## Scope (in)
### US-1 (P1, Must) — Know whether a scene already has its views
As a requester, I want to see, for the scene I chose, whether its 14 views (and layers) already exist, are queued/rendering, or are missing, so I do not render twice.
**Acceptance:**
- Given a scene whose exact content was rendered before, when I open the render control, then it says «Ya tiene sus 14 vistas» (with date and colour setting) and offers «Volver a renderizar» only explicitly.
- Given a scene edited after its render, then it shows as missing (the views belong to the old content).

### US-2 (P1, Must) — Request a render of the chosen scene
As a requester, I want a «Renderizar 14 vistas» action on the chat scene, the Taller 3D scene and each base template, with a colour setting choice (catalogue colour = final setting, default; or the template's original colour), so the GPU renders it.
**Acceptance:**
- Given my role is allowed, when I request, then a job is queued and I see its position; the same scene content requested twice does not create a second job.
- Given a non-internal account, then the action is not shown and the API refuses (403).

### US-3 (P1, Must) — Follow the job and see the laptop's state
As a requester, I want a jobs page with state (en cola, renderizando vista n/14, capas n/14, listo, falló, cancelado) and whether the render machine is online, so I know when it will be ready.

### US-4 (P1, Must) — Result attached to the scene
As any chat user, I want a scene that has a finished render to open with its 14 views and colour layers in the chat (rotate, zoom, tap structures, change colours), exactly like a published template.
**Acceptance:**
- A base-template job, if the template recipe is unchanged, also writes `recipe.presentacion` (+ capas) so the template page and chat use it.
- A chat/Taller scene job is found by the scene's content fingerprint whenever that exact scene is shown.

### US-5 (P2, Should) — Cancel and retry
As a requester, I can cancel a queued job and retry a failed one.

## Out of scope
- Extra views beyond 14, «quitar estructura» cut-outs (recortes), cameras chosen by hand in the UI.
- Any GPU other than this laptop; cloud GPUs (separate strategy conversation).
- Rendering for non-internal customers; billing.

## Requirements
- R1. The system shall allow requesting, cancelling and listing render jobs only to authenticated accounts with role `empleado_interno` or `administrador` (server-side check; browser ids never trusted).
- R2. When a render is requested, the system shall validate the scene (scene schema, catalogue-only balloons, size limits) and store an immutable snapshot plus its content fingerprint (normalized JSON, Postgres key order) and the chosen colour setting (`final` | `original`).
- R3. If a finished render or an active job exists for the same fingerprint and colour setting, then the system shall return it instead of creating a new job (unless «volver a renderizar» is explicit).
- R4. The worker on the laptop shall pull jobs from the database (no inbound connection to the laptop), claim one at a time atomically, and keep a heartbeat; it shall share the existing GPU lock with the kit scripts and take priority over batch queues.
- R5. The worker shall produce: camera grid framed on the decoration (encuadre), 14 Cycles views at the published resolution, depth, colour layers with the calibrated model, upload to the shared image store, and a validated `presentacion` + `capas` result, reporting progress per view.
- R6. While the laptop is off or the worker is down (stale heartbeat), the system shall keep jobs queued and show «Equipo de render apagado».
- R7. If a job's worker dies mid-run (stale heartbeat), then the system shall return it to the queue once; a second failure marks it failed with the reason. A job is never silently reported done.
- R8. When a job finishes, the chat shall show its views for any scene with that fingerprint; a base-template job shall write the template recipe only if the recipe still matches the snapshot (otherwise only the fingerprint result is kept).
- R9. The system shall log job id, requester, fingerprint, colour setting, timings and errors; never full scenes in logs.

## UI / design contract
- UI scope / users: internal staff. (a) Render control in the chat scene panel (next to the admin «referencia de escena»), in the Taller 3D and on each card of `/3d/decoraciones/plantillas`: state chip + «Renderizar 14 vistas» + colour choice. (b) New page `/3d/render` (jobs list, machine state, cancel/retry, open the scene).
- Visual direction: existing Pictures UI, white background, sober colours (memory: Pictures UI sobria); components from `@bitacora/ui`.
- Accessibility: semantic buttons, labelled selects, live region for job progress.

## Edge cases & errors
- Scene edited while its job is rendering: the job finishes for the old fingerprint; the new content shows as missing.
- Template changed between request and finish: result kept by fingerprint, recipe not overwritten (R8).
- Very large scenes (Casa de Navidad, 830+ balloons; Muro azul 826): must still fit time and memory; per-job timeout with clear error.
- Scenes without a framed camera grid in big halls (Viaje en globo lila): grid computed from the balloons (encuadre.ts).
- Network/DB tunnel drops (seen today): worker retries DB writes; uploads are content-addressed (idempotent).
- Two requests at the same time for the same scene: one job (unique fingerprint+setting among active jobs).

## Constraints
- Single production DB on the advin VPS (laptop reaches it through the existing tunnel service); app on Vercel; images in the shared store (`guardarMiniaturaPlantilla`).
- GPU: one RTX A3000; ~35 s per view at 1280×1024/256 samples; layers ~3–4× the views → roughly 30–45 min per job. One job at a time.
- Pictures rules (AGENTS.md): validate at boundaries, authorize per resource, deadlines, durable state, no fabricated success, no secrets in client bundles. No test-suite runs unless David asks (memory); check in the app.
- Colour layers are calibrated for the final setting (model `fisico`); with `original` they are only approximate (see plan decision).

## Priorities & phases
- MVP (Must): US-1..US-4 with the final colour setting and layers; original setting with views (+ layers per the plan decision).
- Should: US-5 cancel/retry. Later: recortes, extra views, cloud GPU.

## Timeline & dependencies
- Depends on the presentacion-kit scripts (vistas14.sh, encuadre.ts, capas4/capas3 pipeline) being made non-interactive and parameterized by job folder.
- Laptop must be on with the worker service enabled.
