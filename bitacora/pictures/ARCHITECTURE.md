# pictures — Architecture

_Living document: how the thing is built (or, for business projects, how the process/organization works).
Edit in place; record the *why* of changes in DECISIONS.md._

## Overview
Repo `dav033/pictures`, app in `demo-decoracion/` (Next 16, TypeScript strict, Tailwind tokens in
`src/app/globals.css`). Local branch `fix/color-organico-conteo`; every verified milestone is pushed to `main`
(Vercel deploys automatically). Python `plan.py` (VPS, manual deploy with prior notice to the owner) is the sole
owner of quantities for the guided assistant. The 3D workshop lives entirely in TypeScript.

## Components / actors
| Name | Responsibility | Where (path / owner) |
|---|---|---|
| Piece model | `Pieza` union → `armarPieza` → balloons, tubes, flowers, anchors, materials | `src/lib/globos3d/piezas.ts` |
| Scene | room + nodes with placements (floor, wall, ceiling, anchor, on-top, free); `armarEscena` | `src/lib/globos3d/escena.ts` |
| Library | items: scene / set / structure / decoration / props; `extraerConjunto`, `productosDe` | `src/lib/globos3d/biblioteca.ts` |
| Sempertex ideas | lazily built lots 01–30 (`IdeaDigitalizada`, mandatory lazy pattern in `tipos.ts`) | `src/lib/globos3d/ideas-sempertex/` |
| Organic engine | cluster packing along paths; parametric columns/arches; web bases | `organico.ts`, `estructuras-organicas.ts`, `bases-organicas.ts` |
| Viewer | three.js, instanced batches, incremental rebuild per node, render on demand, `window.__visor3d` (dev) | `src/components/tres-d/escena-globos.ts` |
| Editor UI | page, panels, context menu, solo editor, Library worker | `src/components/tres-d/` |
| Scene AI | Gemini text + tools (create/replace/recolor/search+insert library) | `herramientas-escena*.ts`, `src/app/api/escena-ia/route.ts` |
| Photo AI | capture → FLUX.2 `/edit` with inventory + silhouettes | `render-ia.ts`, `src/app/api/render-3d-imagen/route.ts`, `src/lib/ia/kagutsuchi/flux.ts` |

## Data & integrations
- Scraped data outside the repo: `pictures-workspace/ideas-fiesta-sempertex/` (ideas JSON, photos, `clasif/`).
- fal.ai (FLUX.2 for photos; FLUX.1 i2i/ControlNet only in `scripts/exp/render-fiel.ts`), Gemini (text only).

## Guided 3D editing context (REQ-016 M2 audit)
- `plan/aprobacion.ts` reads token v1/v2/v3; only the 3D writer with explicit known history and `PLAN_COLOR_ORDER_V3=true` emits v3. The default is reader-only/v2 (D-035/D-046). Legacy unknown history remains unknown after size/base edits. Never enable the writer before a separate reader release; rollback must retain the v3 reader.
- Last replacement context now reads both nested colour-order.v1 and v2 (D-048). V2 keeps actual effects separate from snapshots of requested resolved no-ops; ambiguity is never frozen. Same source phrase/effective per-piece destination/colour identities proves replay for either class. New selected pieces still resolve normally. Pruning may leave only untouched snapshots; add-idea/reload/undo retain the corresponding signed context. Different successful source/destination orders supersede older effects.
- P-082 is fixed locally in fb872bce; M2 passes with fixes, gate 10/10, registered replay 9/9. The reader-only release and any writer rollback target must accept both nested versions, not merely token v3. No writer enablement/publication occurred. See `requirements/REQ-016-guided-3d-edit-leftovers-exact-undo-and/AUDIT-M2.md`.

## Key flows
- Idea lot: agent digitizes 15 ideas → `lote-NN.ts` + test → verified in clean worktree `Downloads/e3-verif` → push.
- Edit: pick piece → inspector / context menu → solo editor → Listo applies as one undo step.

## Conventions & constraints
- Never print `.env*`; no client data in repo; paid runs declare a cap; Gemini never generates images.
- Do not restart :3010 / :8000 unless asked; no `next build` (15.7 GB RAM PC).
- Tests gate pushes: `npx tsc --noEmit` + relevant `scripts/test/*.ts`; `test-carga-3d` keeps imports < 500 ms.

_Last updated: 2026-10-08_
