# REQ-007 switch dossier: GUIADA_MOTOR `python` → `3d` (draft for the owner)

Date: 2026-10-09 · Branch: `feat/dossier-guiada` @ e08dcb43 (origin/main merged, engine globos3d 1.2.2) · Status: **draft, nothing switched.**
`GUIADA_MOTOR` stays `python` everywhere. Evidence: `PARIDAD-2026-10-09b.md` (+ csv), `scripts/test/test-motor-guiada-integracion.ts`.

## 1. Decision asked

Whether the guided customer chat (`/asistente`, guided path) creates new plans with the 3D engine (`3d`) instead of
the Python resolver (`python`), under D-024 and D-026.

**Blocker: graceful rollback does not exist yet (§4).** Until it does, the switch cannot be reverted without breaking
open customer plans. This blocks the switch on its own, whatever the evidence in §2 says.

## 2. What switching changes for customers

- **Counts, in total and per idea.** On the 26 ideas the engine fully builds, the total is 2,173 against Python's 2,170
  (×1.00). That total hides offsetting errors: 18 of 26 ideas are within ±15 % of Python, and 8 are not: classic arches
  01, 02, 14 (−22 %), 09 (−17 %), 25 (−19 %), 12 (+17 %), 30 (+20 %) and 31 (+40 %). Organic pieces keep 20–28 % of
  balloons in R-5, as Python does. Classic arches follow the official 5 quartets per metre (owner question, §5).
  Customers see "cantidades del motor" (owner ruling Q2).
- **Prices (D-026, Sempertex standard presentations, `python` policy).** Over the 26 ideas with a stored price, the
  engine's bill is 0.70 of the stored Python price in total (median 0.68). 21 ideas get cheaper; 5 cost the same or
  more (08 = 1.00, 29 = 1.07, 12 = 1.11, 13 = 1.13, 31 = 1.24). Most of the drop is packaging: the stored plans buy
  50-packs. Priced with Python's own counts under the same policy, the engine is 1.18× dearer. **The cause of that 1.18×
  is not verified** (the likely candidate is the size mix, but the material-value column was not recomputed). The owner
  must accept the price movement explicitly before customers see it.
- **Views.** (a) Read-only 3D render of the plan, "lightly modified" from the customer's 2D (Phase 3, D-019).
  (b) Realistic FLUX image from the same geometry (Phase 4). (c) Customer edits (Phase 5, D-020): AI requests, colour
  references, colour proportions, size proportions. No drag, create or select in the viewer.
- **Built as approximations (`aproximada`; the customer is told the difference).** Classic rings with more colours
  than the trenza takes (up to 4 per weave band), `arco_no_denso` and `columna_no_densa` (built organic with fewer
  balloons), and a wall with more than four colours (`pared_densa`), which keeps only the first four.
- **Not built (falls back to Python per plan):** figure, centre table, partial hoop, organic wall (`pared_organica`),
  light wall (`pared_no_densa`). Photo-inspired plans stay on Python.

## 3. Failure modes and where the text goes

When the 3D path fails, the server returns a typed failure (`fallback.razon`) and the view resolves the plan with
Python. **The customer does not see the sentences below.** They go to the failure log and the audit trail
(`registrarFallo`, `regla:motor_guiada`). The customer gets the Python plan silently, with its usual price.

| Reason | Log / audit sentence | Customer sees | Path afterwards |
|---|---|---|---|
| `bandera_python` | "Este plan se arma con el motor de siempre." | the Python plan | Python |
| `no_representable` | "Alguna pieza de este plan todavía no la arma el motor 3D." | the Python plan | Python |
| `sin_cobertura` | "La tienda no vende algún globo de este plan en esa talla o color." | the Python plan | Python |
| `precio_fallido` | "No pude cotizar los materiales de este plan." | the Python plan | Python |
| `sin_plan_guardado` | "Esa idea no tiene un plan guardado." | the Python plan | Python |
| `tope_de_piezas` | "Sumar esa idea pasaría del máximo de piezas de un plan." | the Python plan | Python |
| `sobre_invalido` | "No pude armar el plan con el motor 3D." | the Python plan | Python |

Edits are different: a refused edit is shown to the customer as `No pude: …`, translated from the engine reason. Size
over the piece's limit → "esa pieza quedaría demasiado grande para el plan"; colour not made in that piece → "ese color
no se puede armar en esa pieza"; measure → "esa medida no se puede armar"; anything else → "esa pieza no se puede
armar con ese cambio". Limit: 60 edits per hour per browser (429 `LIMITE_EDICIONES`).

**Known gaps found by the integration test (46 cases, 3 edits each; counts are per piece):**
- Enlarging a piece 10 % and then shrinking it 10 % does not return the same size: largest drift 7.2 %, which is inside
  one step (the test fails above one step, so a doubled step would be caught). An "undo" built as the inverse edit moves
  the piece.
- Replacing a colour by name is not always reversible: 15 piece-level round trips return another code (530 "Metal
  Verde" comes back as 030), and 12 piece-level round trips merge two colours into one. An undo should restore the stored
  spec, not apply the inverse edit.
- Ideas that fall back today are pinned by name in the test: a new fallback fails the test.

## 4. Rollback: graceful (P-045, branch `feat/guiada-rollback-ordenado` @ bf4a6c62 — in review, not on main yet)

Flag priority: cookie `guiada_motor` (admin only) > kill switch `guiada_motor_corte` (row in `ajustes_runtime`, else env
`GUIADA_MOTOR_CORTE`; `activo|inactivo`) > row `guiada_motor` > env `GUIADA_MOTOR` > `python`; rows cached 30 s per
instance. **The flag decides only new plans.** A plan carries its engine in its signed token, so an open 3D plan keeps
being edited, extended with ideas and redone by the 3D engine at the same price until the conversation ends (token lifetime
24 h), even if the flag returns to `python` or flips mid-conversation; the audit records `bandera: python, efectivo: 3d,
conserva_motor: plan_3d_abierto`. **Normal rollback = flag to `python`**: no customer sees a price change. **Emergency kill
= `guiada_motor_corte = 'activo'`** (an engine that counts or prices wrongly): every plan goes to Python; the server never
touches or quotes an open 3D plan (409 `MOTOR_3D_CORTADO`). An edit is refused with a plain-Spanish «No pude: … tengo que
volver a calcular tu plan completo… las cantidades y el precio pueden cambiar»; a redo or added idea first shows the same
notice and keeps the plan, and only when the customer asks again is the plan recalculated with Python. The admin cookie
still overrides the kill. Known gaps: the reverse switch (an open Python plan redone after a python→3d flip becomes a 3D
plan without notice, ≈×0.7 price), and non-kill 3D failures on a redo are told after the recalculation, not before.
Verify the kill: `GET /api/guiada/motor` returns `{motor: "python", fuente: "corte"}`. A Neon read error keeps each instance's last good value; to survive restarts during a database outage also set `GUIADA_MOTOR_CORTE=activo` in the env. 3D plans older than 24 h (from the first plan, `origenEn`) are not honoured while the flag is python (409 `PLAN_3D_VENCIDO`, customer told first). **Roll back with the flag or the kill switch, never with a code revert** (the token schema is strict and saved sessions with new states would be dropped). Notices are shown in a visible banner («Antes de cambiar tu plan» → «Recalcular mi plan») and a line on the recalculated plan card.

Flip steps (work for new plans; open plans keep their engine once P-045 is merged):

1. **Owner, one browser (no customers).** Signed in as admin on the site, DevTools console:
   `fetch('/api/guiada/motor', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({motor: '3d'})})`.
   This sets `guiada_motor` (HttpOnly, 7 days, SameSite=Strict, same origin). `{motor: 'defecto'}` clears it. Other
   visitors never read it.
2. **All customers.** Neon SQL console:
   `INSERT INTO ajustes_runtime (clave, valor, actualizado_por) VALUES ('guiada_motor', '3d', 'dueño') ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, actualizado_en = now(), actualizado_por = EXCLUDED.actualizado_por;`
   Back to `python`: the same statement with `'python'`, or `DELETE FROM ajustes_runtime WHERE clave = 'guiada_motor';`
   (then the env var decides). Kill switch: the same statement with `('guiada_motor_corte', 'activo', 'dueño')`; release with `'inactivo'` or `DELETE`. Each instance picks it up within 30 s. A row that says `3d` overrides the env var, so
   changing the env var alone does not roll back.
3. **Env var (default when no row exists).** On the VPS, set `GUIADA_MOTOR=python` in `/etc/demo-decoracion/demo.env`
   (the `web` service's `env_file`). Then recreate the container with `docker compose -f compose.vps.yml up -d web`.
   **A plain restart does not reread `env_file`.** `.env.example` documents the variable.
4. **Verify.** `GET /api/guiada/motor` shows the effective motor and its source (cookie, ajuste, env or defecto). In a
   private window, a new guided plan must show the Python plan. The audit line `regla:motor_guiada` records `bandera`,
   `fuente` and `efectivo`.
5. **No schema rollback is needed.** Migration 032 only creates the table; the app tolerates its absence.

**Drill status: not done.** Steps 2 and 4 have not been run on the deployed app.

## 5. Evidence still missing

- **Graceful rollback** (§4), built and tested. This is the blocker.
- **Product judge (D-028/D-030).** Desktop and phone screenshots of the guided plan on 3D, scored ≥ 8. Customer-visible,
  so before the switch, not after.
- **Live Python price check.** This dossier uses an offline replica (`planearCompra`, `python` policy). Needed: one live
  `lista-materiales` call per idea on the current catalogue snapshot, compared with the replica. The owner confirms the
  Python service call.
- **Rollback drill** (§4, steps 2 and 4) on the deployed app, with timing.
- **Owner cookie test** (PLAN Phase 7, first step), including the classic arch inflation question: R-12 in classic arches
  at 25 cm gives 5 quartets per metre (engine); 6.6 per metre would need about 19 cm. The engine is about 22 % under Python here.
- **Cause of the 1.18× counting effect** on prices (§2): recompute the material-value column before attributing it.
- **Stored price check** for ideas 30 and 31, which both carry $57,603 (see PARIDAD-2026-10-09b §5).
- **Undo semantics** for customer edits (§3 gaps): decide between stored-spec undo and inverse edits.
- **Visual review.** No dev server was run, so the look of lujosa and sencilla pieces has not been seen in the browser.
- **One-week watch after the switch:** fallback rate per reason, `armar` p95, 422s from pricing, image failures and cost
  per plan, edits rejected.

## 6. Recommendation

**Do not switch yet.** Switch only when the blocker and the four items pass: (0) graceful rollback, with the flag governing
only new plans and open 3D plans still editable; (a) product judge ≥ 8 on desktop and phone; (b) live Python price check
on the 26 ideas with the deviation agreed in writing; (c) rollback drill with timing ≤ 30 s; (d) owner cookie test, plus
the owner's explicit acceptance of the price movement in §2. The total count is at parity, but the per-idea errors in §2
are real and the owner should see them. The decisions left are prices and the classic arch size. Then switch with the
one-week watch in §5, and keep `python` as the one-step rollback for new plans.

Automated verification for this draft: `test-motor-guiada-integracion` (46 cases; four independent categories: build,
price, counts, edits), `-golden`, `-fronteras`, `-precio` pass; full typecheck shows only the known `LayoutProps` artefact
in `src/app/layout.tsx`.
