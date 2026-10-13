---
id: REQ-006
status: clarifying
created: 2026-10-08
track: standard
---
# REQ-006 — Venue photo → 3D space

## Problem & goal
Owner (2026-10-08): "we want to put a photo of the space and somehow turn it into 3D, I don't know, and support it".
Decorators sell by showing the decoration in the customer's real venue. Today the 3D room is a parametric box
(width/depth/height, wall/floor tones); FLUX renders a generic room.

**Success looks like:** from one photo of the venue, the workshop shows the decoration in that space — right
proportions, perspective and colours — and the FLUX render keeps the real venue.

## Options (cheapest → richest)
1. **Room from photo (reading)**: Gemini vision reads the photo → room dims (from reference objects: doors ≈ 2 m,
   tables ≈ 75 cm), wall/floor colours and materials, openings (windows/doors) → sets `Sala`. Cheap, approximate.
2. **Photo backdrop with matched camera (recommended MVP)**: the photo is the background; the user marks the floor
   corners/wall line (4 clicks) or vanishing lines → camera calibration (homography, focal length) → the 3D
   decoration renders in correct perspective over the real photo, with contact shadows; FLUX refines the composite
   (image-to-image, low strength) keeping the venue.
3. **Monocular depth** (Depth Anything / similar, CPU or fal.ai): depth map → occlusion and a coarse mesh so pieces
   can sit behind furniture; better relighting.
4. **Full 3D reconstruction** (multi-photo / video → Gaussian splats or mesh): orbit around the real venue. Heavy;
   later.

## Open questions (round 1 — to ask the owner)
1. One photo or several/video? (rec: one photo for MVP)
2. Is a "fixed camera = the photo's viewpoint" result enough at first, or must the user orbit freely? (rec: fixed
   camera MVP, option 2; orbit later)
3. Paid steps allowed (fal.ai depth or i2i ≈ US$0.01–0.05 each)? (rec: yes with per-run cap and the REQ-004 ledger)

## Dependencies
REQ-004 (spend ledger for paid steps), render pipeline (`render-ia.ts`), REQ-001 vision reading patterns.
