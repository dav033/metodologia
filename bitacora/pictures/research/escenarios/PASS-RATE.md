# Scenario matrix pass rate

Offline sweep: `NODE_OPTIONS=--use-system-ca npx tsx --conditions=react-server scripts/escenarios/correr.ts --n 2000 --semilla <seed>`.
No paid calls, no network, no DB. A scenario passes when it clears all 7 invariants (no_lanza, banda_conteo, sin_solapes,
dentro_sala, determinismo, tiempo, avisos_honestos).

| Date | Run | Main sha | n | Seed | Pass rate | Top failing invariants |
|---|---|---|---|---|---|---|
| 2026-10-14 | REQ-014 T22 (fixed seed) | 6e1388af (branch feat/req-015-judge-fix; main is 65edd83b) | 2000 | 1 | 98.5% (1970/2000) | banda_conteo 30 (only invariant failing); the other 6 at 100% |
| 2026-10-14 | REQ-014 T22 (random seed, logged) | 6e1388af | 2000 | 259600 | 98.0% (1959/2000) | banda_conteo 41 (only invariant failing); the other 6 at 100% |

Facade time (budget 1500 ms): seed 1 p50 37 / p95 261 / max 671 ms; seed 259600 p50 41 / p95 258 / max 767 ms.
Schema rejections: 0 in both runs. Duration about 156 s per run. Details: [FALLOS-2026-10-14.md](FALLOS-2026-10-14.md).
