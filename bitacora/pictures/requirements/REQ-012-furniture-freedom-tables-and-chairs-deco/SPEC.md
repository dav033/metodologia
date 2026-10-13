---
id: REQ-012
status: merged to main 2026-10-10 (78638080, 386b0cdc)
created: 2026-10-09
track: standard
---
# REQ-012 — Furniture freedom: tables and chairs decoupled

## Problem & goal
Owner (2026-10-09, after the wedding incident): «construye herramientas para tener más libertad: desacoplar número
de sillas con mesas, crear más tipos de mesa y así». Today a seated table is a fixed catalogue item
(`mesa_redonda_sillas` = 8, `mesa_imperial_sillas` = 10); the AI cannot say "6 tables of 4", "chiavari around a
square table", "only one side of the imperial", and lied when asked.

**Success looks like:** any table type × any chair type × any count × any arrangement, built and later changed by
one AI tool call, with the real counts reported back; the shopping list and the render describe what is really there.

## Scope (in)
- US-1 Table types (parametric): redonda (Ø 60–240), cuadrada, rectangular/imperial (L×W), ovalada, cóctel alta,
  media luna, serpentina/curva, banquete en U (if cheap); tablecloth on/off, colour, length (to floor / short), runner.
- US-2 Chair types: tiffany/chiavari, crossback, ghost/acrílica, plegable, moderna, banca, taburete; colour; cushion.
- US-3 Table set = table + chair group as separate composable pieces moving together: count, arrangement
  (alrededor, un lado, dos lados, cabeceras, frente a escenario), spacing derived from the table's real perimeter;
  capacity check (too many chairs for the perimeter → nearest valid count + note).
- US-4 AI tools: create a set; change chairs (count/type/arrangement) on one, several or all tables; change table
  type/size keeping chairs and centrepieces; remove chairs; summaries state real counts.
- US-5 Existing fixed items keep working (old scenes load) — they become presets of the parametric set.

## Out of scope
- Salon layout tools themselves (REQ-008 owns armar_salon/ajustar_salon; they will consume the set model).

## Requirements
- R1. Chair count and type are never inferred from a display name; the summary is built from the actual pieces.
- R2. Old scenes with `mesa_redonda_sillas` / `mesa_imperial_sillas` open unchanged (golden snapshot holds).
- R3. Centrepieces on a table stay attached when its type, size or chairs change.
- R4. Tool declarations stay under the 120 KB cap; MAX_NODOS respected (chairs may need instancing/grouping).

## Constraints
TypeScript without `any`; files < 500 lines; three.js instancing for many chairs; no paid calls in tests.

## Dependencies
- REQ-008 (e4v) adds `sillas_por_mesa` to the salon tools — to be re-based on this model when both land.
- fix/honestidad-render (e5r) lets poner_sobre accept table tops and checks names against the catalogue.

## Assumptions
- A1. Built from main in its own branch; integration with e4v/e5r at merge time (Claude merges).
