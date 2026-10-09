---
id: REQ-005
status: clarifying
created: 2026-10-08
track: standard
---
# REQ-005 — Decorations from scratch (compose anything) + photo → model → library

## Problem & goal
Owner (2026-10-08, /loop, reference `refs/colombia-wall.jpg`): "the system must be able to do things like this
FROM ZERO, creating everything needed; and given a photo of a balloon decoration, model it and add it (to the
library)". Today the AI composes from fixed generators; anything without a generator (a coffee-cup sculpture, a
pixel map of a country) cannot be built, and photo → scene (REQ-001) does not save the result as a reusable item.

**Success looks like:** the reference wall is rebuilt by the AI from a text request or from the photo, with
recognisable parts, correct products/counts, and saved to the Library as a new item searchable by the RAG.

## What the reference contains (→ capability)
| In the photo | Exists today | Missing |
|---|---|---|
| White balloon wall with a pixel map of Colombia in flag stripes (yellow/blue/red) | `mural` (cell matrix in R-5/R-9/R-12 or LOL mesh) | **Mural from a shape or image**: rasterise an outline/photo/emoji/flag into the cell grid, quantised to Sempertex colours made in that format |
| Big 5-petal flowers of round/260 balloons with centres, pinned on the wall | twisting flowers, `flor5`, decorations `sobre`/wall | placement in bulk along a wall border (frame of flowers) |
| Green swirls of 260 (curls) | `rizos` | scatter rule ("curls between flowers") |
| Coffee cup with foam held by a person (sculpture) | figures from a fixed list | **Free sculpture** from primitives (cluster, braid, sphere, tube along a path, stacked rings) authored by the AI as data |
| Lime-green hedge/mound of R-12/R-18 along the floor with small 260 flowers on stems | organic stroke (floor silhouette), flowers | stems + small flowers sprouting from an organic piece |

## Scope (in)
- US-1 Mural from shape/image: `mural_desde_imagen` (upload, flag, emoji, outline drawn by the AI as polygon) →
  grid in the chosen format, colour quantisation to the official palette, editable cells.
- US-2 Free sculpture ("figura libre"): a JSON grammar of primitives with parts (cuerpo, asa, espuma…), built by the
  engine, products/counts from the leaves, editable by `editar_globos`; the AI writes it with a tool + validator
  (sizes, colours in format, physical sanity).
- US-3 Bulk placement rules: border/frame of decorations, scatter with spacing, sprouts on organic pieces.
- US-4 Photo → model → **save to Library** (extends REQ-001 steps 7–10): reading → compiler → refinement → "Guardar
  en biblioteca" with source photo, fidelity note and RAG indexing (REQ-002).
- US-5 "From zero" agent plan: for a request with no template, the agent first writes a build plan (pieces, parts,
  products) then builds piece by piece, verifying each with `ver_pieza`.

## Out of scope (for now)
Exact photogrammetry of a decoration; licensed characters.

## Open questions (round 1 — to ask the owner)
1. Free sculptures: AI-authored only, or also an editor for people to compose primitives by hand? (rec: AI first,
   editor later)
2. Mural from image: allow any uploaded image (logos, faces) or only shapes/flags/emojis? (rec: any image, owner's
   responsibility for rights)
3. Should photo-modelled items enter the shared Library automatically or as "pending review"? (rec: pending review)

## Dependencies
REQ-002 (RAG: find closest templates first), REQ-001 (photo reading), REQ-003 (parts contract, editing).
