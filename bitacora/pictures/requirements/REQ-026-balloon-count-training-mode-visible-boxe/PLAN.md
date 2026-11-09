---
req: REQ-026
status: done
created: 2026-11-09
---
# Plan — REQ-026 — Balloon count training mode: visible boxes for YOLO and total inference with Haiku

## Approach
Draw each balloon of the normal WebGL scene in a unique flat colour to learn which ones the camera really sees (D-102). The same pass feeds a Taller overlay and a batch generator. YOLO learns visible boxes from one neutral frontal image per pool model; Haiku 5.5 at low effort, through the local CLI with three read-only tools, infers the total from the photo and YOLO's output.

## Global constraints
Neutral frontal camera only. No datasets or results in the repository (`~/dev/pictures-infra/conteo/`). The pilot worktree and its services stay untouched (work in `~/dev/pictures-wt/conteo-entrenamiento`). GPU work under `~/.cache/presentaciones/gpu.lock`. Tests are not run in this project unless the owner asks. Prompt tuning on validation only.

## Tasks
- [x] T1 — Per-balloon ID pass and pure box rule · kind: implement · files: src/components/tres-d/pasada-ids-globos.ts, src/lib/globos3d/conteo-visibles.ts · verify: boxes drawn over exported images, viewed · covers: R1
- [x] T2 — Training mode in the Taller, administrators only · kind: implement · after: T1 · files: src/components/tres-d/ModoEntrenamiento.tsx · verify: screenshot of /3d on port 3012 · covers: US-1, R1, R2
- [x] T3 — Dataset generator · kind: implement · after: T1 · files: scripts/conteo-vision/generar-dataset*.ts · verify: `npm run conteo:dataset` · covers: US-2, R3, R4, R5
- [x] T4 — Train and run YOLO · kind: implement · after: T3 · files: scripts/conteo-vision/{entrenar,predecir}_yolo.py · verify: validation metrics · covers: US-3, R6
- [x] T5 — Haiku inference with tools and tuned prompt · kind: implement · after: T4 · files: scripts/conteo-vision/{inferir_haiku,herramientas_mcp,evaluar}.py · verify: evaluar.py on validation, then once on test · covers: US-4, R7, R8, R9

## Verification
Look at exported boxes and at the Taller overlay in the browser; `tsc`, `eslint` and `ruff`; run the dataset, YOLO and Haiku for real and read `evaluar.py`. Automated tests are not run (owner rule).

## Rulings
- T1: silhouettes are measured by drawing non-overlapping groups with nothing in front; projected bounds rejected visible flattened balloons — cost if wrong: low.
- T3: rooms vary per model (a third neutral, the rest from the existing scenarios), colours are kept as designed — one image per model, so variety has to come from the room — cost if wrong: low.
- T5: stopped at three prompts; the test split was scored once and not used to adjust anything — cost if wrong: low.

## Progress log
2026-11-09: approved in chat by the owner («procede»). First dataset 457 images. Independent review found three defects; all fixed, dataset regenerated (460 images), YOLO retrained (60 epochs, 13.9 min) and every evaluation rerun. See REPORT.md.
