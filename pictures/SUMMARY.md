# pictures — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
Sempertex balloon-decoration demo (`demo-decoracion`, Next 16 on Vercel + Python `plan.py` on a VPS). The active
product is the **3D workshop** at `/3d`: a parametric three.js editor (balloon → module → structure → hanging
decorations) whose shopping list comes from the leaves, plus a FLUX photo render of the 3D view and a Gemini
text agent that builds scenes with tools. Users: Sempertex staff and decorators.

## Current state
- Library: 26 lots of Sempertex «ideas de fiesta» digitized (~423 of 987 ideas) + 20 organic bases from web photos,
  modular (scene → set → structure → decoration → props) with exact store products. In main.
- Performance: `/3d` loads in ~2 s (lazy ideas, Library in a Web Worker); the editor redraws only on change
  (36 draw calls instead of 536, select 60–90 ms instead of ~800 ms).
- AI: scene agent can create any structure, recolor everything and insert Library items as bases; FLUX render
  gets a closed inventory and organic silhouettes (no more invented pieces; colors still drift).
- Context menu + solo editor of a structure: in main (`6b2a4391`).
- **In progress:** full UI/UX redesign of the editor (approved mockups:
  https://claude.ai/artifact/2JLXNGsiCaEukgh5KV3Scq), implemented by an agent, not yet committed.

## Active focus
- Redesign of the 3D editor (top bar, icon rail + panels, full viewer, right inspector, solo editor, phone sheet).

## Top pending (see PENDING.md)
- P-001 redesign implementation · P-002 FLUX color fidelity · P-003 resume idea digitization loop

## Recent decisions (see DECISIONS.md)
- D-001..D-006 (2026-10-08): lazy ideas, render on demand, FLUX.2 kept for photos, redesign layout, loop paused.

## Known issues
- FLUX.2 render shifts colors (ΔE ~23) and room tone.
- Selecting a piece still costs 60–90 ms in dev (side-panel React re-render).

_Last updated: 2026-10-08_
