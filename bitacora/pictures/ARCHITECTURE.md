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

## Key flows
- Idea lot: agent digitizes 15 ideas → `lote-NN.ts` + test → verified in clean worktree `Downloads/e3-verif` → push.
- Edit: pick piece → inspector / context menu → solo editor → Listo applies as one undo step.

## Conventions & constraints
- Never print `.env*`; no client data in repo; paid runs declare a cap; Gemini never generates images.
- Do not restart :3010 / :8000 unless asked; no `next build` (15.7 GB RAM PC).
- Tests gate pushes: `npx tsc --noEmit` + relevant `scripts/test/*.ts`; `test-carga-3d` keeps imports < 500 ms.

_Last updated: 2026-10-08_
