---
req: REQ-007 · ruling D-038 (2026-10-10) «La cotización tiene que ser la misma en todos lados; escoge la mejor.»
date: 2026-10-10 · branch feat/cotizacion-unica (worktree e7y) from origin/main e7b7aeaa · engine globos3d 1.2.3
reproduce: scripts/motor/descomponer-precio-ideas.ts, scripts/motor/paridad-ideas.ts (no network, no paid calls)
---

# One quote everywhere: analysis and choice (D-038)

## 1. Where a quote was computed (before this branch)

| Surface | Counts | Price list | Packaging | Waste | Extras |
|---|---|---|---|---|---|
| Classic chat `/api/chat` | Python resolver | Plan's snapshot (Neon) | Cheapest combination **among allowlisted variants only** = whatever the RAG search returned that turn | One plan-wide `ceil(Σ×0.08)` reserve: natural surplus, then one more cheapest pack | none |
| Guided Python «Crear mi plan» (`/api/plan-idea`) | Python resolver on the stored plan (no stored price) | Stored snapshot | Same, allowlist = stored one: **172 of 234 entries are 50-packs** | same | none |
| Guided Python card «¿cuánto cuesta?» | Curated list (`decoraciones.json`) | Current snapshot (`lista-materiales`) | Fixed curated variants, `ceil(q/units)` | **none** | none |
| Guided 3D plan + card (`cotizarBom`) | Engine BOM | Published snapshot (`lista-materiales`) | `planearCompra` policy `python`: **all** store presentations | same as classic | none |
| Taller `/3d` «Lista de compra» | `armarEscena` | none | none | none | helium litres/tanks (estimate) |

Rounding is the same everywhere: closed packs, integer COP, IVA included. One idea could show three prices in the guided
chat alone (card, Python plan, 3D plan), and the classic chat priced the same BOM by what the search returned.

## 2. The ×1.18, explained

`descomponer-precio-ideas.ts` prices both BOMs of each idea under the same rules and crosswalk and splits the ratio into
four factors whose product is exactly the ratio: **count**, **size** (reference unit price per size), **colour/finish**
(consumption value ÷ size reference) and **packaging** (purchase cost ÷ consumption value: what closed packs cost above
the balloons used). Over the 24 comparable ideas the dossier's **1.18 = count 1.01 × size 1.07 × colour 1.02 × packaging
1.07**; under the final model of §3 it is 1.19 (packaging 1.08).
- **Size mix (+7 %)**: the engine puts more balloons in R-18/R-24 (04: 1.32; 13: 1.30; 30: 1.30; 31: 1.50).
- **Fragmentation (+7–8 %)**: the engine spreads colours over more sizes, 198 → 263 size × colour lines; each extra line
  opens a closed pack that is mostly unused (11: 11 → 23 lines, packaging 1.79; 18: 1.50; 30: 1.41; 31: 1.34).
- Premium colours add 2 %; the total count is at parity. Separately, **stored Python ÷ the same counts under the final
  model = 1.58×** (26 ideas): that is the 50-pack allowlist, a pricing defect, not a count.

Per idea, COP, final model (Python counts and engine counts both bought with it):

| # | Python stored | Python counts | Engine | Ratio | Count | Size | Colour | Packaging | Lines Py → engine |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 52,148 | 46,058 | 34,000 | 0.74 | 0.77 | 1.00 | 1.00 | 0.96 | 2 → 2 |
| 02 | 52,148 | 48,124 | 38,132 | 0.79 | 0.78 | 1.00 | 1.00 | 1.01 | 2 → 2 |
| 03 | 178,499 | 101,090 | — centre table | — | — | — | — | — | 14 → — |
| 04 | 209,253 | 117,655 | 176,591 | 1.50 | 1.14 | 1.32 | 1.08 | 0.92 | 13 → 19 |
| 05 | 214,313 | 134,192 | 145,608 | 1.09 | 1.13 | 1.20 | 0.95 | 0.85 | 19 → 21 |
| 06 | 80,096 | 26,416 | 24,350 | 0.92 | 1.00 | 1.00 | 1.00 | 0.92 | 6 → 6 |
| 07 | 160,526 | 90,931 | 59,404 | 0.65 | 0.85 | 0.84 | 0.95 | 0.96 | 12 → 11 |
| 08 | 36,703 | 46,522 | 46,522 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 3 → 3 |
| 09 | 101,250 | — crema not crossed | 58,369 | — | — | — | — | — | — → 12 |
| 10 | 172,299 | 84,948 | 132,093 | 1.55 | 1.08 | 1.25 | 1.01 | 1.15 | 15 → 24 |
| 11 | 109,852 | 51,476 | 93,663 | 1.82 | 0.94 | 1.08 | 1.00 | 1.79 | 11 → 23 |
| 12 | 128,660 | 95,739 | 151,131 | 1.58 | 1.17 | 1.17 | 1.06 | 1.09 | 8 → 12 |
| 13 | 88,296 | 73,147 | 133,205 | 1.82 | 1.09 | 1.30 | 0.98 | 1.31 | 6 → 9 |
| 14 | 52,148 | 46,058 | 34,000 | 0.74 | 0.77 | 1.00 | 1.00 | 0.96 | 2 → 2 |
| 15 | 112,782 | 80,180 | 110,792 | 1.38 | 1.08 | 1.18 | 1.04 | 1.05 | 9 → 14 |
| 16 | 105,583 | 78,019 | 80,385 | 1.03 | 0.98 | 0.97 | 0.95 | 1.14 | 8 → 11 |
| 17 | 266,075 | 171,851 | 181,975 | 1.06 | 1.13 | 1.09 | 0.96 | 0.90 | 17 → 18 |
| 18 | 87,879 | 38,519 | 46,416 | 1.21 | 0.92 | 0.90 | 0.98 | 1.50 | 7 → 9 |
| 19 | 179,306 | 108,516 | 104,762 | 0.97 | 1.09 | 0.75 | 0.95 | 1.25 | 12 → 15 |
| 20 | 79,200 | 41,963 | 50,103 | 1.19 | 1.02 | 1.11 | 1.00 | 1.05 | 9 → 12 |
| 22 | 115,802 | 61,414 | 67,820 | 1.10 | 1.07 | 0.87 | 1.07 | 1.11 | 11 → 14 |
| 24 | 26,074 | 17,000 | 17,000 | 1.00 | 1.02 | 1.00 | 1.00 | 0.98 | 1 → 1 |
| 25 | 51,027 | — multicolor not crossed | 22,323 | — | — | — | — | — | — → 3 |
| 27 | 62,247 | 73,519 | — partial hoop | — | — | — | — | — | 5 → — |
| 28 | 148,746 | 108,581 | 66,834 | 0.62 | 1.12 | 0.63 | 0.95 | 0.92 | 12 → 9 |
| 29 | 13,037 | 11,889 | 11,889 | 1.00 | 1.07 | 1.00 | 1.00 | 0.94 | 1 → 1 |
| 30 | 57,603 | 23,396 | 51,554 | 2.20 | 1.20 | 1.30 | 1.00 | 1.41 | 6 → 11 |
| 31 | 57,603 | 25,462 | 71,558 | 2.81 | 1.40 | 1.50 | 1.00 | 1.34 | 6 → 14 |

## 3. The model chosen: standard presentations, each balloon with its own reserve (after the review)

1. **One need per product and size for the whole plan** (pieces consolidated).
2. **Right presentations:** every closed pack the store sells of that same balloon (×3 … ×80), never a subset chosen by a
   search ranking or a curated list.
3. **Reserve per balloon (size and colour):** `ceil(n × 0.08)` of that same balloon: a decorator who pops a red 12″ needs
   a red 12″. The first version kept one plan-wide reserve, which could be all 5″ whites for a red arch.
4. **No overbuying:** the cheapest combination that covers `n + reserve` in one search (`comprarGlobo` / `comprar_globo`).
   It is never dearer than covering the design and adding loose packs for that balloon's reserve, nor than `mas_barato`
   (2,000 random catalogue BOMs, 0 exceptions; `mas_barato` is dearer in 6 of 26 ideas, never cheaper). Every pack bought
   carries design balloons (each variant gets one first), so no line is skipped and no pack is reserve-only.
5. **Price:** packs × catalogue pack price, integer COP, IVA included; Python owns prices (`lista-materiales`, resolver).
6. **Extras:** the online store sells no helium; every quote says "no incluye helio ni montaje"; the Taller keeps its
   litres/tanks estimate. Labour and margin stay in the professional quote.
Review case (146 R-5 green 826 + 39 R-24 white 005): first version 200,047; old plan-wide loose pack 168,864 (15 spares, any
colour); final 183,110 (12 green R-5 + 4 white R-24 spares). Cost of the rule: with large packs one colour's spares can
cost a whole pack (vector 24: 140,000 → 220,000, a second ×25 R-24 gold for 2 spares).

## 4. One source of truth, and why it is the least fragile

- **The pricer is TS `cotizarBom`** (BOM → `planearCompra` → Python `lista-materiales`): the 3D plan, the 3D card and the
  Taller (`POST /api/taller/cotizacion`, priced partially when the store lacks a balloon) call it with their BOM.
- **Python prices its own plans with the identical rules** (`app/presentaciones.py`, `plan.py` `_buy`). The allowlist still
  decides products and sizes; packs and reserve are purchase decisions.
- **Pinned by one shared fixture** (`contracts/domain/v1/golden/cotizacion-unica/`, 40 BOMs: 3 synthetic, the review case,
  20 seeded random catalogue BOMs, 8 engine and 8 Python ideas): `test-cotizacion-unica` runs every TS surface on it;
  pytest runs the resolver's purchase path with the allowlist cut to one pack per balloon. The real-Python oracle of
  `test-motor-guiada-precio` agrees on 39 plans.
- Not a new Python endpoint: it would need a contract, a VPS deploy before the Taller or the 3D path could quote at all,
  and an offline replica for the golden tests anyway.
- **One decoration, one price:** the card quotes the plan the customer gets. Flag `3d`: engine BOM; if the engine cannot
  build the idea or the store lacks a balloon, the stored idea's Python plan (where the plan falls back); a transient price
  or engine failure gives no price. Flag `python`: that Python plan, requested as «Crear mi plan» does
  (`pedidoDeIdeaSola`), resolved once per process and reused by the plan. Curated list only for figures.

## 5. Before → after, five sample ideas (COP)

| # | Classic chat / guided Python plan | Guided Python card | Guided 3D plan and card | Taller list (same BOM as 3D) |
|---|---|---|---|---|
| 01 | 52,148 → 46,058 | 52,148 → 46,058 | 34,000 → 34,000 | none → 34,000 |
| 04 | 209,253 → 117,655 | 209,253 → 117,655 | 176,591 → 176,591 | none → 176,591 |
| 08 | 36,703 → 46,522 | 36,703 → 46,522 | 36,703 → 46,522 | none → 46,522 |
| 11 | 109,852 → 51,476 | 109,852 → 51,476 | 91,597 → 93,663 | none → 93,663 |
| 28 | 148,746 → 108,581 | 172,179 → 108,581 | 66,834 → 66,834 | none → 66,834 |

"Before" for the classic chat is the stored-allowlist price (live it varied with the search). Python "after" needs the VPS.
Other 3D movements from the per-balloon reserve: 02 +6 %, 07 +7 %, 12 +6 %, 13 +34 %, 17 +5 %, 30 +4 %.
