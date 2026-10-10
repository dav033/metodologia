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
the balloons used). Over the 24 comparable ideas: **1.18 = count 1.01 × size 1.07 × colour 1.02 × packaging 1.07**.
- **Size mix (+7 %)**: the engine puts more balloons in R-18/R-24 (04: 1.32; 13: 1.30; 30: 1.30; 31: 1.50).
- **Fragmentation (+7 %)**: the engine spreads colours over more sizes, 198 → 263 size × colour lines; each extra line opens
  a closed pack that is mostly unused (11: 11 → 23 lines, packaging 1.89; 18: 1.50; 31: 1.44; 30: 1.36).
- Premium colours add 2 %; the total count is at parity. Separately, **stored Python ÷ the same counts under the chosen
  model = 1.64×** (26 ideas): that is the 50-pack allowlist, a pricing defect, not a count.

Per idea, COP, final model (Python counts and engine counts both bought with it):

| # | Python stored | Python counts | Engine | Ratio | Count | Size | Colour | Packaging | Lines Py → engine |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 52,148 | 45,889 | 34,000 | 0.74 | 0.77 | 1.00 | 1.00 | 0.96 | 2 → 2 |
| 02 | 52,148 | 47,037 | 36,066 | 0.77 | 0.78 | 1.00 | 1.00 | 0.98 | 2 → 2 |
| 03 | 178,499 | 97,127 | — centre table | — | — | — | — | — | 14 → — |
| 04 | 209,253 | 106,590 | 176,591 | 1.66 | 1.14 | 1.32 | 1.08 | 1.02 | 13 → 19 |
| 05 | 214,313 | 125,360 | 145,608 | 1.16 | 1.13 | 1.20 | 0.95 | 0.90 | 19 → 21 |
| 06 | 80,096 | 24,350 | 24,350 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 6 → 6 |
| 07 | 160,526 | 90,931 | 55,441 | 0.61 | 0.85 | 0.84 | 0.95 | 0.90 | 12 → 11 |
| 08 | 36,703 | 36,703 | 36,703 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 3 → 3 |
| 09 | 101,250 | — crema not crossed | 58,369 | — | — | — | — | — | — → 12 |
| 10 | 172,299 | 82,715 | 132,093 | 1.60 | 1.08 | 1.25 | 1.01 | 1.18 | 15 → 24 |
| 11 | 109,852 | 47,682 | 91,597 | 1.92 | 0.94 | 1.08 | 1.00 | 1.89 | 11 → 23 |
| 12 | 128,660 | 95,739 | 142,299 | 1.49 | 1.17 | 1.17 | 1.06 | 1.03 | 8 → 12 |
| 13 | 88,296 | 73,147 | 99,581 | 1.36 | 1.09 | 1.30 | 0.98 | 0.98 | 6 → 9 |
| 14 | 52,148 | 45,889 | 34,000 | 0.74 | 0.77 | 1.00 | 1.00 | 0.96 | 2 → 2 |
| 15 | 112,782 | 74,320 | 109,581 | 1.47 | 1.08 | 1.18 | 1.04 | 1.12 | 9 → 14 |
| 16 | 105,583 | 77,850 | 80,385 | 1.03 | 0.98 | 0.97 | 0.95 | 1.15 | 8 → 11 |
| 17 | 266,075 | 171,851 | 173,143 | 1.01 | 1.13 | 1.09 | 0.96 | 0.86 | 17 → 18 |
| 18 | 87,879 | 38,519 | 46,416 | 1.21 | 0.92 | 0.90 | 0.98 | 1.50 | 7 → 9 |
| 19 | 179,306 | 106,450 | 104,762 | 0.98 | 1.09 | 0.75 | 0.95 | 1.28 | 12 → 15 |
| 20 | 79,200 | 41,963 | 50,103 | 1.19 | 1.02 | 1.11 | 1.00 | 1.05 | 9 → 12 |
| 22 | 115,802 | 61,414 | 67,820 | 1.10 | 1.07 | 0.87 | 1.07 | 1.11 | 11 → 14 |
| 24 | 26,074 | 17,000 | 17,000 | 1.00 | 1.02 | 1.00 | 1.00 | 0.98 | 1 → 1 |
| 25 | 51,027 | — multicolor not crossed | 22,323 | — | — | — | — | — | — → 3 |
| 27 | 62,247 | 62,247 | — partial hoop | — | — | — | — | — | 5 → — |
| 28 | 148,746 | 108,581 | 66,834 | 0.62 | 1.12 | 0.63 | 0.95 | 0.92 | 12 → 9 |
| 29 | 13,037 | 11,889 | 11,889 | 1.00 | 1.07 | 1.00 | 1.00 | 0.94 | 1 → 1 |
| 30 | 57,603 | 23,396 | 49,488 | 2.12 | 1.20 | 1.30 | 1.00 | 1.36 | 6 → 11 |
| 31 | 57,603 | 23,565 | 71,558 | 3.04 | 1.40 | 1.50 | 1.00 | 1.44 | 6 → 14 |

## 3. The model chosen: standard presentations, bought once per plan

The most correct model for a decorator buying Sempertex online is the engine's (D-026, policy `python`), on every pack:
1. **One need per product and size for the whole plan** (pieces consolidated).
2. **Right presentations:** every closed pack the store sells of that same balloon (×3 … ×80), never a subset chosen by a
   search ranking or a curated list. Cheapest combination; ties → less surplus → fewer packs → variant id.
3. **No overbuying:** one plan-wide reserve `ceil(Σ × 0.08)` covered by the surplus the packs already leave. If it falls
   short, the one line whose cheapest cover of (its packs + what is missing) costs least extra is bought again
   (`cubrirReserva`): a loose extra pack was dearer when the exact cover left no surplus (2×50 + 3×12 + one ×12 against
   3×50). It moves 4 of the 52 library BOMs (02: −5 % engine, −2 % Python; 29: −15 % both) and Python vector 16 (−3 %);
   without it, offering every pack made idea 29 dearer than its 50-pack-only price (13,955 against 13,037; now 11,889).
4. **Price:** packs × catalogue pack price, integer COP, IVA included; Python owns prices (`lista-materiales`, resolver).
5. **Extras:** the online store sells no helium, so no surface can price it; quotes say "no incluye helio ni montaje" and the
   Taller keeps its litres/tanks estimate. Non-balloon catalogue items in a Python plan are bought as declared. Labour
   and margin stay in the professional quote (business mode).
Rejected: the stored allowlist (1.64× for the same balloons), the curated card list (no reserve, fixed packs) and
`mas_barato` (reserve per line): dearer than the chosen model in 13 of 26 ideas, never cheaper.

## 4. One source of truth, and why it is the least fragile

- **The pricer is TS `cotizarBom`** (BOM → `planearCompra` → Python `lista-materiales`): the 3D plan, the 3D card and now
  the Taller (`POST /api/taller/cotizacion`, «Precio en la tienda») call it with their BOM.
- **Python prices its own plans with the identical rules** (`app/presentaciones.py`, `plan.py` `_buy`): its algorithm was
  already the original of `planearCompra`; only the candidate set differed. The allowlist still decides products and sizes.
- **Pinned by one shared fixture** (`contracts/domain/v1/golden/cotizacion-unica/`, 19 BOMs: 3 synthetic, 8 engine, 8
  Python): `test-cotizacion-unica` runs every TS surface on it; pytest runs the resolver's purchase path on the same BOMs
  with the allowlist cut to one pack per balloon. Both give the same packs, reserve and total.
- Not a new Python endpoint: it would need a new contract, a VPS deploy before the Taller or the 3D path could quote at all,
  and an offline replica for the golden tests anyway. The fixture gives the guarantee with no new network dependency.
- **One decoration, one price:** the idea card quotes the plan the customer gets. Flag `3d`: engine BOM; if the engine
  cannot build or price the idea, the stored idea's Python plan (where the plan falls back). Flag `python`: that Python
  plan, requested exactly as «Crear mi plan» does (`pedidoDeIdeaSola`). The curated list stays only for ideas with no stored
  plan (figures). If Python cannot price it, the card shows no price rather than another number.

## 5. Before → after, five sample ideas (COP)

| # | Classic chat / guided Python plan | Guided Python card | Guided 3D plan and card | Taller list (same BOM as 3D) |
|---|---|---|---|---|
| 01 | 52,148 → 45,889 | 52,148 → 45,889 | 34,000 → 34,000 | none → 34,000 |
| 04 | 209,253 → 106,590 | 209,253 → 106,590 | 176,591 → 176,591 | none → 176,591 |
| 08 | 36,703 → 36,703 | 36,703 → 36,703 | 36,703 → 36,703 | none → 36,703 |
| 11 | 109,852 → 47,682 | 109,852 → 47,682 | 91,597 → 91,597 | none → 91,597 |
| 28 | 148,746 → 108,581 | 172,179 → 108,581 | 66,834 → 66,834 | none → 66,834 |

"Before" for the classic chat is the stored-allowlist price (live it varied with the search). "After" for Python is the
rule on Python's stored counts, pinned by the fixture; live it needs the Python change deployed on the VPS.

## 6. Open points

- Until the VPS runs the new Python, classic and guided-Python prices stay as before (the card then shows that price).
- A stored plan resolves against its stored snapshot, the 3D path against the published one: equal only while they match.
- Ideas 30/31 share a stored price; 09/25 have Python lines the crosswalk lacks. Classic-chat "Otras opciones de precio"
  still uses allowlisted packs and no reserve (another plan; proposal).
