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

## Automatic count, chosen by evolution (owner goal, 2026-11-09, D-105)
Lab in `~/dev/pictures-infra/conteo/lab`: fixed score, Sonnet medium lanes over three rounds, then a genetic search (40 individuals, 40 generations, 3 seeds, bootstrap fitness).
Winner: detector t2, plain 960, isolated-box filter, NMS 0.5, confidence 0.2, ridge + GBM from box features (`scripts/conteo-vision/conteo_automatico.py`). Lab score 29.21 to 19.46; it converged and the seeds agree.
Survived: photographic-augmentation retraining, extra NMS, isolated-box filter, box-feature regression. Died: stronger degradation (t3, t4), hard negatives (t5), tile mode once retrained, nested-box and texture filters, Haiku as box reviewer, Haiku type recognition as the main path.

Reserved data, scored once:

| Set | Fixed rule | Winner |
|---|---|---|
| 12 real photos against human estimates | 34.5 % (median 29.6 %) | 25.7 % (median 19.0 %) |
| 43 3D test scenes | 16.2 % | 14.7 % |

95 % interval of the improvement: real -3.7 to +19.6 points, 3D -1.8 to +4.8. Both include zero: consistent improvement, not statistically proven with this little data. Selection optimism on the 17 dev photos was estimated at about 14 points.
Verified in the browser on port 3012: Contador and chat, automatic by default. Local only; nothing pushed or deployed.

## Generation 4 and close of the evolution (2026-11-09)
Truth fix first: three human estimates that were clear typos ([1, 121], [12, 228], [118, 1, 123]) were cleaned the same way for every set; the winner scores 17.56 on the lab after it.
Lanes (Sonnet medium): small photos (upscaling, size-dependent confidence, box fusion) died: on the cleaned truth small photos were not the weak point (14.7 % against 24.2 % for large). More renders with other rooms and lights (1,068 scenes, detectors o1 and o2) died: real photos got worse. Mapper trained on degraded boxes (HistGB) reached 16.20 in the lab, inside the noise by its own stability check.
Second and last use of the reserved data, paired, winner against that candidate: real 22.2 % against 21.2 % (difference -4.2 to +6.6 points), 3D 14.7 % against 15.9 % (-3.6 to +1.0). Not adopted. The evolution is closed with the deployed configuration as the best one found; the reserved data must not be used again for choosing.
Production: deployed to main (7b327e1aa, fbafd4955, 47f2c8926) with the detector service on the VPS; colours and sizes come from the Python service rescaled to the automatic total. Not checked with a real signed-in session.

## Pending
- Merge is the owner's decision; nothing is pushed or deployed.

## Walkthrough
See the 2026-11-09 log.
