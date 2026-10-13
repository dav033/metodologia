---
id: REQ-010
status: in progress 2026-10-09
track: standard
---
# REQ-010 — AI feedback: rate every AI action and keep its full state

Owner (2026-10-09): "la IA hace una acción y luego le pregunta al usuario si está bien, con una calificación del 1 al
10, una pregunta con varias opciones de por qué, y una caja de comentario de falencias y posibles mejoras; esto nos
servirá para ver los huecos de la IA; se guarda todo el estado del render con imágenes, estados y estados previos."

## Owner answers (round 1)
- Where: everywhere, full form — Taller 3D (panel B turn cards) AND the customer chat.
- When: always visible, non-blocking (a "¿Qué tal quedó? 1–10" row on each AI turn); if the user undoes the turn or
  corrects the AI, the "why" panel opens by itself.
- Storage: data + scenes in Neon; before/after images in file storage (Garage S3 on advin-vps, dedicated bucket/key;
  fallback compressed thumbnails in Neon if S3 isn't reachable from Vercel).
- Review: admin panel (worst-rated first, before/after images, prompt, AI steps/tool calls, scene diff, filters) +
  automatic periodic analysis of recurring gaps.

## What is stored per feedback
turn id, product (taller|cliente), user, timestamp, rating 1–10, reasons (multi-select), comment (falencias/mejoras),
the user request text, AI reply, tool calls/steps (from the audit log, linked by request id), scene BEFORE and AFTER
(JSON), scene diff, before/after captures (JPEG ~1280 px), model, cost, latency, app version (commit). No audio.
Reasons (initial list, editable): no entendió lo que pedí · cambió cosas que no pedí · faltó algo · mal colocado ·
colores incorrectos · tamaños/proporciones · se ve feo/poco realista · la foto realista no coincide · muy lento · otra.

## Non-goals (now)
Training models on the feedback; public sharing.
