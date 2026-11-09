---
id: REQ-026
status: in-progress
created: 2026-11-09
track: standard
---
# REQ-026 — Balloon count training mode: visible boxes for YOLO and total inference with Haiku

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Staff need to know how many balloons a decoration has from one photo, including balloons hidden behind or under others.
A detector can only see visible balloons and only 18 real photos have human, approximate totals. The 3D pool knows its
exact counts, so it can supply labelled data.

**Success looks like:** a repeatable pipeline that produces a labelled dataset from the pool, a YOLO detector for visible
balloons, and a Haiku inference step for the total, each with its measured error on unseen scenes and compared with
simple baselines.

## Users / actors / stakeholders
- Administrators of Pictures (training mode in the Taller 3D).
- David (runs the pipeline, reads the report).

## Scope (in)
### US-1 (P1, Must) — See what the detector would be taught
As an administrator, I want a training mode in the Taller 3D that outlines each visible balloon and shows «visibles X / total Y».
**Acceptance:**
- Given a scene with balloons, when I turn the mode on, then each balloon that is at least 10 % visible has one rectangle.
- Given a balloon fully hidden from the camera, then it has no rectangle but still counts in the total.
- Given an account that is not an administrator, then the control does not appear.

### US-2 (P1, Must) — Dataset from the pool
As David, I want one image per eligible model with the neutral frontal camera, plus YOLO labels and the exact total.
**Acceptance:**
- Images never contain rectangles; boxes are only in the label files.
- Splits are per model (train/val/test) and reproducible from the model id.

### US-3 (P1, Must) — YOLO detector
As David, I want a one-class detector trained on that dataset with its counting error on the test split.

### US-4 (P1, Must) — Total inference with Haiku
As David, I want Haiku 5.5 at low effort, through the local CLI, with tools and a tuned prompt, to infer the total from
the image and YOLO's output, measured against baselines.

### US-5 (P2, Should) — Learned hidden ratio
As David, I want a model that estimates total/visible from the image, adopted only if organic error is 12 % or less.

## Out of scope
- Vertex/Gemini weight tuning (deferred by the owner, 2026-11-09).
- Multiple camera angles: the photos received are neutral and frontal (owner, 2026-11-09).
- Tubes, flowers and other non-round balloons in the first version.
- Cycles renders. Real-world accuracy claims: no real totals exist yet.
- Any production use of the models or changes to the chat.

## Requirements
- R1. While the training mode is on, the Taller shall draw one rectangle per balloon whose visible area is at least 10 % of its footprint, computed from a per-balloon ID pass, never from projecting hidden geometry.
- R2. The total shown and exported shall come from the scene's materials (`armarEscena(...).materiales`).
- R3. The dataset generator shall skip and report any model whose ID count differs from its materials total.
- R4. Exported images shall contain no overlay.
- R5. Splits shall be derived from a hash of the model id, so a model is in one split only.
- R6. YOLO training shall take the shared GPU lock (`~/.cache/presentaciones/gpu.lock`) and allow more detections per image than the highest visible count.
- R7. Haiku runs shall use `claude-haiku-5-5` at effort `low`, with an explicit allowed-tool list and a bounded number of calls.
- R8. Prompt tuning shall use the validation split only; the test split is scored once per final prompt and reported as such.
- R9. The report shall compare Haiku with a visible × per-type factor baseline on the same test scenes.

## UI / design contract (optional)
- UI scope / users: a toggle over the Taller viewer, administrators only.
- Visual direction / existing system: sober, white surfaces, no neon; thin dark rectangles with a light halo so they read over any balloon colour.
- Accessibility or interaction constraints: real button with `aria-pressed`, visible focus; overlay ignores pointer events.

## Edge cases & errors
- Scene with no balloons: counter shows 0 and no rectangles.
- Balloon cut by the image edge: both its visible pixels and its silhouette are limited to the image.
- WebGL context loss or a failed measurement: the mode shows an error and turns no data into success.

## Constraints
- The GPU is shared with the render worker; the pilot worktree and its services are not touched.
- No datasets or results in the repository (owner rule): they live in `~/dev/pictures-infra/conteo/`.
- Owner rule: tests are not run for this project unless requested; verification is by looking at the output.

## Priorities & phases
Must: US-1 to US-4. Later: more camera angles, tubes, real totals from decorators, Gemini tuning.
