---
id: REQ-025
status: proposed
created: 2026-11-07
---
# REQ-025 — Plan

Architecture in one line: the app (Vercel) writes jobs to a `render_jobs` table in the VPS Postgres; a worker service on the laptop
pulls them through the existing DB tunnel, runs the presentacion-kit pipeline under the shared GPU lock, uploads images to the shared
store and writes a validated `presentacion` + `capas` result; the chat finds results by scene fingerprint.

Why pull and not push: the laptop is behind NAT and sleeps; pulling needs no open port, survives reboots and tunnel drops (seen today),
and the queue is durable in Postgres. Rollback: disable the worker service and hide the UI flag; the table is additive.

## M1 — Contract and storage (repo)
- T1. Migration `render_jobs` (id, requester account id, origin {kind: template|chat|taller, template id?}, scene snapshot jsonb, fingerprint, colour setting, state, progress {views, layers}, attempts, worker id, heartbeat_at, error code/message, result jsonb, timestamps); unique active job per (fingerprint, setting); index by fingerprint where state = done. Versioned contract module `src/lib/render/contrato.ts` (zod: job, progress, result = PresentacionSchema + CapasSchema).
- T2. Scene fingerprint: normalized JSON (Postgres key order, same as validar --normalizar) + sha256; one owner in `src/lib/render/huella.ts`, used by API, chat and worker.
## M2 — API and permissions (repo)
- T3. Routes: POST `/api/render/trabajos` (role empleado_interno|administrador, validate scene with EscenaSchema + catalogue check + size limits, dedupe R3), GET list/one, POST cancel/retry; GET `/api/render/estado?huella=` (has views / active job / missing). Stable error codes.
- T4. Template origin: snapshot = current recipe; on finish, write `recipe.presentacion`/`capas` only if recipe still matches (R8), with VPS backup of the previous recipe.
## M3 — Worker on the laptop (pictures-infra + systemd user service)
- T5. `render-worker` (Node/TS, runs from the pilot checkout with the :3010-like env): claim with `FOR UPDATE SKIP LOCKED`, heartbeat every 20 s, stale-job requeue once (R7), DB writes retried across tunnel drops, per-job deadline.
- T6. Pipeline per job folder (no hand steps): export GLB → `encuadre.ts` grid → 14 views (`final`: ajuste-final; `original`: template render.py/luz.env or kit default) → `capas-globos.ts` + estructuras metadata → capas4-variantes/capas3-post/LUT/empacar/categorías → upload (subir.ts/final-subir.ts logic) → result JSON validated against the contract. Progress written per view/layer. Shares `gpu.lock`; batch queues yield (gpu-baja).
- T7. systemd user unit `pictures-render-worker.service` (Restart=always), logs to journal; documented start/stop.
## M4 — UI (repo; Designer contract first)
- T8. Render control component (state chip, «Renderizar 14 vistas», colour select, «Volver a renderizar», progress) in the chat scene panel, Taller 3D and template cards; only for internal roles.
- T9. Page `/3d/render`: jobs list, machine online/offline (heartbeat), cancel/retry, open scene.
- T10. Chat: when an ensamble has no template presentation, look up a finished render by fingerprint and feed it through `presentacionDe` (views + capas + structures), so rotate/zoom/tap/recolour work unchanged.
## M5 — End-to-end check and release
- T11. On :3010: a base template (Comunión, original setting), a chat-edited scene (final setting), a large scene (Casa de Navidad); check views + colour change in the chat; kill the worker mid-job and see requeue. No test suites (memory); visual checks.
- T12. Push to main + Vercel deploy (authorized 2026-10-19), migration applied with a DB backup first; enable the worker service; bitácora entry.

## Delegation
- Codex Terra medium (codex-1/2/luis): T1–T3 (contract, migration, API), T9 page, T7 unit. Exact, bounded tasks.
- Sonnet high (claude-personal / claude-work): T6 pipeline (Blender kit glue), T10 chat integration, T8 UI after the Designer contract.
- Coordinator (this session): T2 fingerprint owner, T4/T5 review, M5 checks, merges and deploy; independent review of each milestone.

## Decision needed from the owner
- Colour layers are calibrated for the catalogue colour setting (final). With «color original» they would not match the render 1:1. Proposal: «original» renders the 14 views and SKIPS layers (the chat then offers colour change by re-rendering with the final setting), unless you prefer approximate layers.

## Estimates
- M1–M2: ~0.5 day agents. M3: ~1 day (the pipeline is the risk). M4: ~1 day. M5: ~0.5 day + GPU time (~30–45 min per job).
