# REQ-014 T44 — Kontext colour fidelity — 2026-10-16

## Scope and change

The Taller and guided-photo routes share `promptFotoDeLayout`. Both the server-side guided description and the Taller's `materialesEnIngles()` adapter now send each official Sempertex colour with its balloon hex and finish. The shared prompt adds the measured, scene-specific metal-reflection wording. The offline regression exercises the real Taller material adapter and verifies idea 07, a silver-metal scene, and a scene with no metals.

## Previous paid evidence

The 2026-10-09 experiment compared the production baseline and variants a–d on guided idea 07. Its `gasto.json` records 16 attempts and **US$1.28**; the original US$0.60 cap was exceeded, so this is historical evidence and is not counted as a cap-compliant T44 run.

| Wording | Samples | Mean ΔE | Visual result |
| --- | ---: | ---: | --- |
| base | 1 | 10.4 | Gold appeared silver over most of the right column. |
| a: hex + finish beside each colour | 1 | 10.9 | Gold still turned silver; an extra window and radiator appeared. |
| b: per-column legend | 2 | 9.9 | Better lilac/pink in some seeds; a later seed added a seam and gold ring. |
| c: legend + explicit colour constraints | 2 | 12.8 | Inconsistent; seams and invented lettering appeared. |
| d: metal reflections keep their own colour | 3 | 9.5 | Gold remained visibly gold in all three; two had no silver substitution or extra objects. Mean lilac ΔE was 6.3, versus 12.9 for base; pink stayed near baseline. |

Chosen wording from variant d:

> metallic balloons whose reflections keep their own colour (chrome gold reflects gold, never silver)

The source images, per-colour scores, visual notes and the old ledger remain in `research/kontext-color/`.

## Bounded T44 rerun

- Declared cap: **US$0.60**. Image cost is reserved before each provider call, including failed attempts.
- Isolated ledger: `research/kontext-color/t44-2026-10-16/gasto.json`.
- Before the first call, the offline and dry-run modes validated the 1024×1024 JPEG, all palette hexes, and the cap. Initial ledger total was US$0.00.
- The first `base` request (seed 21) was rejected by fal.ai with HTTP 403 `saldo_agotado` / “User is locked. Reason: Exhausted balance.” No image was returned. The ledger conservatively reserves **US$0.08**; no retry was made. Current T44 ledger total is US$0.08, below the declared cap.
- This rerun produced no visual comparison. Prior d evidence selected the wording in code, but it does not validate the changed Taller prompt visually.

## Status

The prompt implementation and offline tests are complete. T44 remains open until a valid Taller comparison can run within the US$0.60 cap; T53 remains open because it depends on T44. The marathon stays at 52/70 tasks (74.3%).
