# Rollback drill — guided engine flags, production, 2026-10-11

Target `https://demo-decoracion.vercel.app` (app version `6274a079ca55`), owner-approved (D-037, D-039). Flags are rows of Neon
`ajustes_runtime`, read with a 30 s per-instance cache. Run A (07:04–07:08 UTC) = full drill with 2 chat turns. Run B
(07:11–07:14 UTC) = chat-free repeat that primes every instance cache right before each write (worst case) and re-checks the
steps run A could not judge. Drivers: scratchpad `simulacro/simulacro.mts` and `simulacro2.mts` (Playwright, system Chrome,
e2e spend guard imported from `scripts/e2e/humo/`); not in the repo. "Seconds" = write finished → first read / all 3 parallel reads
(polled every 5 s) show the new value.

**Before:** `catalogo_repos_rag=sempertex,mobiliario,escenografia`, `guiada_motor=3d`, `taller_hoja_armado=activo`; no `guiada_motor_corte` row.

| Step | UTC | Action | Observed | Seconds (first / all) |
|---|---|---|---|---|
| 1 Baseline (A) | 07:04:43–07:05:07 | chat turn 1/2, idea #1 → "Crear mi plan" | `GET /api/guiada/motor` 3d/ajuste; `POST /guiada/motor/plan` 200, $176,591, 115 balloons; edit via `/editar` 200 | — |
| 2 python (A) | 07:05:15 | `guiada_motor=python` | new tab: flag read python/ajuste, plan from `/api/plan-idea` $117,655; old 3D tab edit `/editar` 200, messages 6→6, 0 page errors | 0 / 0 (stale caches) |
| 2 python (B) | 07:11:45 | same, caches primed | old tab edit 200; audit row `bandera=python, efectivo=3d` | 10 / 30 |
| 3 back to 3d (A) | 07:05:45 | `guiada_motor=3d` | new tab: `POST /guiada/motor/plan` 200 $176,591 | 0 / 10 |
| 3 back to 3d (B) | 07:12:28 | same, caches primed | old tab edit 200 | 5 / 20 |
| 4 kill ON (A) | 07:06:27 | `guiada_motor_corte=activo` | flag python/corte; armada, imagen (empty body) and plan: 409 `MOTOR_3D_CORTADO`; old tab edit 409 + "No pude… Tu plan sigue como estaba"; reload: banner + "Recalcular mi plan"; new plan via Python $117,655 | 0 / 5 |
| 4 kill ON (B) | 07:13:12 | same, caches primed | edit 409 + notice; reload banner (screenshot B-05) | 15 / 30 |
| 5 kill OFF (A) | 07:07:15 | delete the corte row (it did not exist before) | flag 3d/ajuste again | 10 / 30 |
| 5 kill OFF (B) | 07:13:59 | same, caches primed | old tab edit 200 | 0 / 15 |
| 6 Final | 07:08:09, 07:14:32 | `ajustes_runtime`, flag, fresh quote | rows equal "before"; 3d/ajuste; chat quote $176,591 (`COTIZACION_IDEA_3D`) | — |

Flip windows: python 31 s (A) / 43 s (B); kill 48 s (A) / 47 s (B). Instances disagree inside the window (mixed python/3d reads for up to 30 s): expected from the per-instance cache.

## Verdicts
- PASS python flag reaches new requests within the 30 s cache bound (worst case 30 s at 5 s resolution).
- PASS a NEW plan after the flip is built by Python (flag read `?para=plan_nuevo` → python; no `/guiada/motor/plan` call).
- PASS P-045: the open 3D plan keeps editing in 3D under `python` (A and B), no crash, conversation intact; no notice, none is due (it appears only with the kill or after 24 h).
- PASS restore: new plans 3D (A), open plan editable (B). Run A's last "más grandes" got 422 `EDICION_NO_ARMABLE` (third bigger-step in a row hit the size cap, test artefact); run B repeated it with alternating steps: 200.
- PASS kill switch, P-049: armada/imagen/plan 409 `MOTOR_3D_CORTADO` before any spend; open plan edit refused honestly; reload shows "Tu plan necesita recalcularse" + "Recalcular mi plan" (not clicked: it calls paid `/api/chat`); new plans use Python.
- PASS release of the kill: 3d/ajuste in 15–30 s; open plan editable again.
- PASS spend: guard counted 2 chat turns in run A (ideas, "Cuánto cuesta"), 0 in run B, 0 blocked paid calls, FLUX 0. Gemini not metered on this path; ≈ US$0.002–0.01 per Flash turn, so ≤ US$0.02, under the US$0.05 cap.

## Restore confirmation
After run B, `ajustes_runtime` read at 07:15:45 UTC: `catalogo_repos_rag=sempertex,mobiliario,escenografia`, `guiada_motor=3d` (last written 07:12:28Z), `taller_hoja_armado=activo`; no `guiada_motor_corte` row. Same keys and values as "before". GET flag 3d/ajuste at 07:14:32.

## Findings
1. Client flag read gives up after 1 s (`src/components/guiado/usarMotorGuiada.ts:16` `TIMEOUT_BANDERA_MS`, catch at :35 → `sinLectura` python at :27) while the server may wait 1.5 s on Neon (`src/lib/ajustes/ajustes-runtime.ts:20`). Seen once on prod, 07:04:50: the read was aborted and a new plan with flag `3d` came from Python ($117,655 instead of $176,591 for the same idea). A customer can silently get the cheaper Python price.
2. Python vs 3D price for the same idea, same conversation: $117,655 vs $176,591 (+50 %), known from the dossier §2.
3. `/api/guiada/motor/editar` validates the body (400) before the kill check (`editar-motor.ts:123-147`); armada and imagen check the kill first. Harmless.
4. Side effect: my local rehearsals (dev server on :3010 shares the prod Neon) wrote about 21 `plan_audit_log` rows, 06:52–07:03 UTC. Real-run rows: 07:04:48–07:14:32.

Screenshots (same folder, `SIMULACRO-ROLLBACK-2026-10-11-*`): `01-baseline-plan-3d`, `02-python-plan-nuevo`, `03-python-pestana-vieja-3d`, `04-restaurado-plan-nuevo-3d`, `07-corte-plan-nuevo-python`, `09-final-cotizacion-idea-3d`, `B-04-corte-cambio-rechazado`, `B-05-corte-aviso-proactivo`.
