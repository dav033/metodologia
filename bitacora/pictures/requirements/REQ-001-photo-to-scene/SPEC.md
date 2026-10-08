# REQ-001 — Photo to scene (Pinterest → 3D) + flexible organic structures

Status: approved by mission (owner's /loop 2026-10-08: "no hay ningún tipo de prisa"; autonomy per memory
feedback-autonomia-total). Questions of the previous round (organic column types) answered with the recommended
defaults (D-007).

## Why
The owner notices that many decoration types and specific structures have little flexibility and control. He
handed 13 reference photos (Pinterest-like; kept outside the repo in
`pictures-workspace/referencias-usuario/lote-01/`) and wants:
1. Every individual decoration (and the scene, where it matters) in the system, with the tools to build them.
2. The AI, given a decoration photo, recreates it autonomously — possibly on top of existing structure templates.

## Gap analysis (photos → what is missing)
| Seen in photos | Today | Needed |
|---|---|---|
| Organic garland with any silhouette: swag (12), arc (7, 9, 11), corner drape (8), half arch down a side (2, 10, 13), asymmetric arch (3), top + side (1) | `guirnalda_organica` = width/drop/thickness only; `organico` tramos only by code | **Organic stroke** ("trazo orgánico"): a path drawn on the wall (points + thickness at each point), size mix, colour weights, giant accents |
| Irregular vs strange-shape organic columns (4, 5) | one "Orgánica" with mixed params | **Column type**: classic / irregular (straight silhouette) / freeform (clusters stacked off-axis, bulges) |
| Leaves inside garlands: monstera (7, 9), palm (8), fern/eucalyptus (1), dried gold leaves (3) | flowers only (hortensia, rose, gypsophila) | **Foliage** types in the flower system + renderer |
| R-5 "grape" clusters (4), gold collar on orbz (6) | modules only | **Cluster decoration** (racimo de uvas) placeable `sobre` a structure |
| Orbz with fringe tail (6), foil script "love" (7), foil letters (11) | foil numbers/letters/shapes | foil **sphere (orbz)** + fringe tail prop |
| Round backdrop + half moon (2), chiara arches (5), shimmer wall (3, 4), fluted pedestals (2), curtain with lights (1), signs (1, 10) | panels, boxes, cylinders, sequin wall | **Backdrop catalog**: round, chiara set, half moon, pedestal set, curtain with fairy lights, sign board |

## Photo → scene (AI)
- The owner attaches a photo in the AI bar (button, paste or drop). Gemini **reads** it (vision, text out —
  never generates images) into a structured *reading*: pieces from our catalog (type, position and size in the
  image, silhouette path for organic strokes, colours sampled as hex → nearest official Sempertex colour in that
  format, size mix, accents), backdrop and props, plus a scale reference (table ≈ 75 cm, door ≈ 200 cm, wall ≈
  250 cm…).
- A **deterministic compiler** turns the reading into an `Escena` with the parametric generators (testable, no
  model in the loop). Library bases can be used as starting templates when the reading names one.
- **Refinement (autonomous)**: the client captures the 3D view; photo + capture go back to the scene agent, which
  fixes differences with the normal CRUD tools (≤ 2 rounds, each logged).
- Every model decision is logged on the server (`decidir`), cost estimated per call; hourly cap shared with the
  scene AI.

## Acceptance
- The 13 photos are in the Library (source "Referencias del dueño"), each with fidelity score and honest note.
- From the AI bar, each of the 13 photos produces a scene whose silhouette, colours and piece inventory match
  (judged side by side; target fidelity ≥ 3/5 on average, no invented pieces).
- New structures are editable in the solo editor and creatable by the AI by name.
- `tsc` clean, tests green (except P-006), no file grows past 500 lines without a PENDING entry.

## Constraints
Paid runs declare their cap (dev cap for this REQ: US$1.50 in Gemini reads). No FLUX. Gemini never generates
images. No customer data in the repo (photos stay outside). Never restart :3010/:8000; no `next build`.
