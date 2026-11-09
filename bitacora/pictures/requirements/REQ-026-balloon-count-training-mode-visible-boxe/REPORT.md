# REQ-026 — Report

## Built
- Taller 3D training mode, administrators only: one rectangle per really visible balloon and «visibles X / total Y».
- Per-balloon ID pass (`pasada-ids-globos.ts`) and box rule (`conteo-visibles.ts`): a balloon counts from 10 % of its silhouette.
- `npm run conteo:dataset`: 460 images, neutral frontal camera, clean, with YOLO labels and exact totals. Split 364 / 53 / 43 by model.
- `scripts/conteo-vision/`: YOLO training and prediction, Haiku 5.5 low through the local CLI with three read-only MCP tools, evaluation.
- Data and models: `~/dev/pictures-infra/conteo/` (outside the repository).

## Verification evidence
Automated tests were not run (owner rule). `tsc`, `eslint` and `ruff` pass. Boxes were viewed over exported images and the overlay in the browser (port 3012, local administrator).

Test split, 43 unseen 3D scenes, scored once:

| Method | MAE | MAPE | Median APE | Bias | within 20 % |
|---|---|---|---|---|---|
| YOLO visible count (against visible) | 3.0 | 3.5 % | | | |
| YOLO visible, no correction (against total) | 38.7 | 27.4 % | 26.6 % | -38.7 | 26 % |
| YOLO × global factor | 24.0 | 16.2 % | 14.3 % | +6.1 | 67 % |
| YOLO × per-type factor, type known | 16.2 | 13.8 % | 12.1 % | -1.3 | 77 % |
| Haiku prompt v3 | 21.3 | 17.6 % | 12.4 % | +10.4 | 72 % |

Validation (53): Haiku 17.7 %, per-type factor 17.4 %, global factor 19.1 %.

18 real photos against human estimates (orientation only, the estimates are approximate): Haiku MAPE 41.5 %, median 35.8 %, bias +33.5; the 7 fully counted ones 25.4 %. Human total / YOLO visible median 1.34 (dataset 1.45).

## Rulings
- One image per model; rooms vary per model (a third neutral). Colours as designed.
- Three prompts tried on validation. v3 chosen on the first dataset; rerun unchanged after the label fix.
- Independent Codex review found three defects (cut-out occluders, footprint estimate, relative paths). All fixed; the fixes themselves were not re-reviewed.

## Needs your eyes
- Administrator gate of the mode: only exercised as local administrator, not with a non-administrator account.

## Proposals
1. Record the balloons actually used in real set-ups (P-305); without it the real error stays unknown.
2. Let the per-type factor replace Haiku's total and keep Haiku only to recognise the structure type: on test the factor with a known type wins.
3. Look at the real photos where the detector fails (very small images, and one with 65 detected against 356 estimated).

## Follow-up: learned hidden-balloon ratio (owner approved 2026-11-09)
Ridge over DINOv2 features of the detected decoration (`proporcion_ocultos.py`), chosen on validation, test scored once.

| Scenes | Per-type factor, type known | Learned ratio |
|---|---|---|
| Organic, validation + test (47) | 16.9 % | 13.2 % |
| Organic, test (19) | 16.7 % | 12.8 % |
| All, validation + test (96) | 15.8 % | 14.1 % |
| All, test (43) | 13.8 % | 14.2 % |

The agreed goal for organic structures (12 % or less) was not met. Against the 18 human estimates the learned ratio is far worse (82.5 %, overestimating): it predicts a median ratio near 2.4 where people imply 1.34, and real photos sit outside what it learned (mean standardised distance 1.24 against 0.78 for unseen 3D). No code defect was found. Not adopted.

## Trial wiring
YOLO × 1.455 behind `CONTADOR_FOTO_YOLO_URL`, off by default. No colours or sizes in this mode.

## Per-structure formulas (owner request, 2026-11-09)
Research by four Codex tasks (`~/dev/pictures-infra/conteo/investigacion/`, codex-1 and codex-luis). Formulas in `src/lib/contador/formulas-estructura.ts`; key constants checked against the code.

3D with the structure given (validation + test, 96): general rule 17.8 %, by structure 15.4 %. Simple quartet columns: 3 unseen models 0.0 % and 17 training models 0.3 %. Single-layer walls 36.6 % to 6.1 %, figures 28.4 % to 15.4 %, link walls 11.8 % to 3.8 %.
Automatic recognition (Haiku through the local provider, with measured size spread): 3D test 15.2 % against 15.3 % for the general rule; structure right in 27 of 43. On 29 real photos against human estimates it is worse: 47.6 % against 39.1 %. So the default is the general rule; automatic detection is an option.

## Pending
- Merge is the owner's decision; nothing is pushed or deployed.

## Walkthrough
See the 2026-11-09 log.
