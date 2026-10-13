---
id: REQ-008
status: clarifying (after REQ-007 D1 and the furniture branch merge)
created: 2026-10-08
track: standard
---
# REQ-008 — Complex event compositions ("I want a wedding")

## Problem & goal
Owner (2026-10-08): "with this, Gemini will create complete and complex compositions: 'I want a wedding' → a wedding
hall with balloons on the ceiling, a balloon arch somewhere, a centrepiece on every table… complex things, with punch."
Today the scene agent places pieces one by one; there is no notion of a venue layout (tables in a grid, chairs around
each table), repeated decorations per table, ceiling installations, or a plan for the whole event.

**Success looks like:** from one sentence ("boda para 120 personas, blanco y dorado, salón de 15 × 20 m"), Gemini
produces a coherent full venue: furniture layout (round tables + chairs, head table, dessert table, dance floor),
centrepiece per table (same design, instanced), ceiling balloons/garlands, entrance arch, photo backdrop — with
materials and counts from the engine, editable by zone ("change all centrepieces to gold").

## Capabilities needed (tools)
- Venue layout tool: grid/rows of tables with chairs (uses the furniture catalogue, `agregar_mobiliario` disposición),
  aisles, zones (entrance, stage, dance floor, dessert).
- "Repeat on every table" tool: one decoration design instanced on N anchors (table tops) — one definition, N copies,
  BOM × N, edits apply to all.
- Ceiling installations: balloon ceiling (`techo` exists), hanging garlands/clouds over zones.
- Event planner pass: the agent first writes a composition plan (zones → pieces → counts), then builds it; verification
  per zone with `ver_pieza`/`ver_escena`.
- Performance: hundreds of balloons × tens of tables → instancing in the viewer, BOM aggregation.

## Open questions
1. Typical event sizes to support (guests, room dims)?
2. Workshop only, or also the customer product (2D views per REQ-007)?
3. Budget-driven ("boda con 5 millones") — yes/no?
