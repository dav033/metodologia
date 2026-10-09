---
id: REQ-008
status: in progress 2026-10-09 — owner asked to build it now ("Gemini only put a table and a chair on the existing
  decoration; I want the whole hall modelled, centrepieces, things like that")
---
# REQ-008 — Plan

## Defaults (owner can override)
Workshop (pro) first; customer chat later. Events of 50–200 guests, halls up to ~20 × 30 m. No budget-driven
planning yet (guests + style + colours).

## Why Gemini fails today (explorer map, 2026-10-09)
- Room max 12 × 10 × 6 m (`RANGOS.sala`, herramientas-escena.ts:87) — too small for a 120-guest hall.
- 12 tool rounds per request (route.ts:41) and only piece-by-piece tools → it places one table and runs out.
- No "same centrepiece on every table" (bases exist: colocacion `sobre`/`ancla` with `cada`, `copias`).
- MAX_NODOS 150 per scene; balloons are instanced (InstancedMesh); no perf bench for ~2 000+ balloons.

## Phases (two parallel worktrees, hostile review after each)
1. **Hall-scale room** (W1): Sala up to 3000 × 3000 × 1000 cm; camera/framing, shadows, floor/wall/ceiling at that
   scale; perf bench (armarEscena + viewer) for ~2 500 balloons / 60 nodes with a budget.
2. **`armar_salon` layout tool** (W1): pure `distribuirSalon({invitados, mesa: redonda8|redonda10|imperial, sala,
   zonas})` → round tables with chairs in a grid with aisles, head table, dessert table, dance floor, stage/backdrop
   wall, entrance; returns node ids by zone. Tests: counts (tables ≥ ceil(guests/seats)), no overlaps, aisles ≥ 90 cm,
   inside the room.
3. **`decorar_mesas` (centrepiece on every table)** (W2): one design (library item, small column, helium bouquet,
   R-5 cluster…) placed on every table top (`sobre` the table) as linked copies; editing one design updates all;
   BOM × N comes from real nodes. Tool to change/remove all centrepieces.
4. **Ceiling by zone** (W2): `techo` over the dance floor / head table (festones, red, helio) positioned by zone.
5. **`planificar_evento` composite tool** (W1, after 2–4): from a brief (tipo, invitados, colores, estilo, medidas) builds
   the whole venue in one call (layout + centrepieces + ceiling + entrance arch + photo backdrop), so Gemini plans and
   refines instead of placing piece by piece; system-prompt rule for event requests.
6. **Eval bank**: event prompts ("boda 120 blanco y dorado, salón 20×30", "XV años 80 rosa", "baby shower 40 safari")
   with structural checks (tables, centrepieces = tables, ceiling, arch, backdrop, all inside the room); free run with
   the composite tool, then a paid run (cap US$0.30).

## Owner scope update 2026-10-09
"Necesitamos una cantidad de herramientas, un hardware de herramientas bastante intenso… no es solo salón gigante de 35
mesas: que tenga posibilidades de reducirlo, ajustarlo, hacer solo la decoración." → the toolset scales both ways and is
composable: `alcance` solo_decoracion | rincon | salon; small orthogonal adjust tools (change guests, change table type,
resize hall, move/remove a zone; decorate some/all/alternating tables, change/remove/resize all, fill new tables; ceiling
by rectangle / node / whole room, any density). Never rebuild or delete user pieces implicitly.
