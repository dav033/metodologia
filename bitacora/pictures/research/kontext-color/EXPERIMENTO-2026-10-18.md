# REQ-014 T44 — Kontext colour fidelity, paid pass — 2026-10-18

## Result: blocked, no new visual comparison

- Declared cap: **US$0.60** (isolated ledger `t44-2026-10-16/gasto.json`, run with `KONTEXT_COLOR_TOPE_USD=0.60`). Ledger before this pass: US$0.08 (one rejected call on 2026-10-16).
- Dry run (`seco base 07`) passed: 1024x1024 JPEG, all hex values present in the prompt, cap not exceeded.
- First paid call (`pagar base 21 07`) was rejected by fal.ai with HTTP 403 `saldo_agotado` ("User is locked. Reason: Exhausted balance"). No image returned. Per the rule, the pass stopped there: no retry, no further calls.
- Real spend this pass: **US$0.08 reserved (1 call, failed)**; ledger total US$0.16 of US$0.60. Note: failed calls are reserved conservatively; fal.ai most likely did not bill a rejected request.
- Resume once the fal.ai balance is topped up: `seco`/`pagar` base 21 and d 21 on scene 07, then base/d on scene 10 (Taller-like silver chrome), same env vars.

## Chosen wording (from prior evidence, not revalidated)

The 2026-10-09 study (see EXPERIMENTO-2026-10-16.md; US$1.28, cap exceeded, historical only) favoured variant d: exact balloon hex + finish per colour plus

> metallic balloons whose reflections keep their own colour (chrome gold reflects gold, never silver)

d kept chrome gold gold in 3/3 seeds and halved lilac ΔE (6.3 vs 12.9 base). This wording is already in code (`promptFotoDeLayout`). It is **chosen** provisionally; visual validation of the Taller prompt remains pending, so T44 stays open.

## Update 2026-10-18 (later): paid pass completed

- **Key:** the local `FAL_KEY` belongs to a locked account. The owner authorized using the key from the production env file on the VPS; it was passed only to the run through a temporary env file in the scratchpad (mode 600, deleted afterwards). Not stored in the repo or the bitácora.
- **Calls:** 4 successful (`base 21 07`, `d 21 07`, `base 21 10`, `d 21 10`). Ledger `t44-2026-10-16/gasto.json`: total US$0.48 of the US$0.60 cap, counting the 2 earlier failed calls at US$0.08 each (reserved; real billing unverified).
- **Metrics (`puntuar`, scene 07, seed 21, ΔE vs the Taller capture; lower is better):**

| | mean | matte light pink | pale lilac | chrome gold |
|---|---|---|---|---|
| base | 12.9 | 17.3 | 10.9 | 10.5 |
| d | 14.5 | 18.3 | 17.3 | 7.8 |

- **Scene 10 (`hoja-comparativa-idea10.png`, Taller-like silver chrome):** d renders visible silver chrome spheres; base has few. d also shifts the room framing (a chair enters the frame). Not measured with ΔE.
- **Reading:** d fixes the stated defect (chrome) and worsens the lilac and the mean on one seed. Not a validated win.

## Chosen wording (provisional)

**d**, provisionally: the task's stated defect is chrome fidelity, and d is the only variant that fixes it. Known costs: lilac regresses (ΔE 10.9 → 17.3) and the room framing can drift. Evidence is one seed on two scenes; the budget left (US$0.12) cannot fund a second seed. Revisit with the owner's top-up or revert to base if lilac matters more.
