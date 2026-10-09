---
id: REQ-007
status: draft v2 — rewritten after the antagonistic architecture panel (3 reviewers: boundaries, contracts/truth,
  ops/separation); awaiting owner decisions D1–D5, then a second panel pass before any code
---
# REQ-007 — Plan v2

## What the panel changed (v1 → v2)
- **v1 was built on a wrong "current state".** The customer ALREADY has a geometry engine: the designer engine
  (`clasificador-decoraciones`), ported 1:1 to Python with golden vectors (`armado_arco.py`, `armado_columna_organica.py`,
  216 vectors), which also draws the SVG the customer approves ("el que se ve es el que se cobra"), plus customer
  2D (`GraficaMotorGuiada` → `VistaMotor`) and 14 plan edits (`plan_edicion.py`). There are already ≥ 4 owners of
  quantities. Putting globos3d behind the customer without deciding this would create a 5th owner and the split
  "what is drawn ≠ what is charged".
- **v1's API exported the workshop's own model** (`Escena`/`Pieza`: ~17 shapes, ~135 organic options) → freezes the
  workshop or makes versioning fiction. And `editar(escena)` would itself create orphan properties (edits lost on the
  next plan→scene rebuild). Removed.
- **The engine is not pure** (17 files import `@/lib/plan/referencia-sempertex` → RAG/colour code; `taller ↔ globos3d`
  cycle; an 18-file cycle around `piezas.ts`): a package move is expensive and buys little in one app.
- **Separation was cosmetic**: one password for both products, one build, one Python worker with a global engine mutex,
  flags read from env (rollback = redeploy, not instant), telemetry can't see route groups.
- **Shadow in the request path is unsafe**: measured `armarOrganico` 0.19 s (72 balloons) → 9.3 s (1 483 balloons),
  synchronous.
- **The "sensitivity test" is not a guard** (only perturbs present leaves; seeded engine changes anyway; misses array
  lengths — a live bug was found: a classic garland read with 3 colours compiles to `un_color` and drops 2).

## Owner decisions needed BEFORE any code (batched)
- **D1 — Canonical geometry/quantity engine for the customer** (the core question).
  (a) globos3d becomes canonical: it must accept the customer `armado-*.v1` contracts unchanged and pass the same golden
  vectors the Python ports pass; the designer/Python ports are retired per structure type, row by row.
  (b) The designer engine (Python) stays canonical for customer structures; globos3d is used for the customer only
  where it adds what the designer engine lacks (photo → decoration, organic garlands of any silhouette, complex
  compositions), and it must emit the same `armado` contracts so the customer still sees what is charged.
  **Recommendation: (b) now, converge to (a) structure by structure only where golden vectors prove parity.**
- **D2 — Separation depth**: two Vercel projects from the same repo (path-filtered builds, own env/flags/domain), a
  separate workshop credential, separate Python worker pools/semaphores per product. Rec: yes, all three.
- **D3 — 2D style for customers**: technical (discs + legend + counts) and/or illustrative. Rec: both, illustrative
  first.
- **D4 — Basic edits list**: reuse the 14 existing plan edits; which ones are exposed to customers.
- **D5 — Quotes already shown/approved**: honoured as approved (pinned engine version) — rec yes.

## Phases (after D1–D5)
- **Phase −1 — ADR**: canonical engine per structure type (D1), quantity-owner table (structure × armado present → owner),
  deletion dates for superseded paths.
- **Phase 0 — Real separation & guardrails**: two Vercel projects (or at least separate deploy gating/env), workshop
  credential, per-product Python worker pool; runtime flag store (Edge Config or Neon table, 30 s TTL) with a rollback
  drill; `producto` stamped via AsyncLocalStorage in the route wrapper (`withProducto`), reconciled with `superficie`,
  fail-closed; verify fal spend is logged.
- **Phase 0.5 — Engine hygiene**: shared colour kernel (`tabla-color`, `similitud-color`) out of `lib/plan`; break the
  `piezas` and `taller↔globos3d` cycles; dependency-cruiser on resolved paths (incl. `import type`) failing CI; I/O files
  (`*-ia*.ts`, cupo, biblioteca) stay in the app.
- **Phase 1 — Customer facade, not a package**: `src/lib/globos3d/motor/v1.ts` exposing only
  `armarDesdeEspec(EspecClienteV1) → { bom, vista2d, avisos }`; `EspecClienteV1` and the BOM registered in
  `contracts/domain/v1` (same `contracts:check` that guards Python); converting spec → Escena is private. No semver;
  compatibility = contracts check + structural golden fixtures (counts, colours, boxes — not SVG hashes).
- **Phase 2 — Orphan-property ledger (all contracts on the path)**: `CONSUMO satisfies Record<RutaHoja<Contrato>,
  Destino>` with `Destino = escena(path) | bom | flux_prompt | cotizacion | ui | ignorado{razon, adr}` → a new field fails
  compilation; value checks (colour share in BOM ± tol, measures in box ± tol); fast-check generators from zod incl.
  optional fields and array lengths; per-enum distinct-output check; plan→spec→plan round-trip identity for editable
  fields; runtime read-tracking proxy in shadow (unread field → `orphan` telemetry); unknown-key telemetry where zod
  strips. Fix the live bug in `compilar-lectura.ts` (classic garland colours).
- **Phase 3 — Material crosswalk**: versioned `(formato, codigo, acabado) → variant_id` per catalogue snapshot, coverage
  test; gaps → explicit `sin_cobertura`.
- **Phase 4 — Shadow, offline**: replay logged plans (no customer request path), or ≤ 10 % sampled in `after()` inside
  a worker thread; persistent geometry cache keyed `(engine_version, spec_hash)`; balloon cap; `armar` budget (p95 < 1 s
  for ≤ 500 balloons); durable `motor_shadow_diff` table (migration) with retention, a named owner, weekly review and a
  numeric exit gate (e.g. ≥ 95 % of structures within ±5 % count and identical colour sets over ≥ 500 plans per type).
- **Phase 5 — Customer 2D from the canonical engine** (per D1/D3), flags per product; FLUX guide from the same
  geometry; edits stay plan operations (existing `plan_edicion`), the engine has no `editar`; deprecate the lossy
  `planActualDesdePlan` projection.
- **Phase 6 — Versioned approval**: `motor:{id,version}` inside the signed plan, `plan_hash` and approval token; resolve
  with the signed version or force re-approval; shadow never touches the hash; upcast/reject for every stored client
  shape (sessionStorage `demo_guiado_v2`, approvals by hash, IndexedDB images) with old-payload fixtures; Python checks
  `plan_version`; decide Plan 1.1.
- **Phase 7 — Switch row by row + runbook**: SLOs (plan card 2D, edit round-trip, generate), k6 load test (~20 guided
  sessions + workshop traffic), retention TTLs for logs/diffs, privacy (no customer photos or raw readings persisted;
  hashes/counts only).

## Review gates
CI does most of it (boundaries, cycles, contracts check, ledger compile, perf bench, bundle budget per route). Human
antagonistic panels at Phase −1 (ADR), Phase 2 (ledger), Phase 5 (customer-visible) and Phase 7 (switch).

## Owner rulings 2026-10-09 (see D-019)
- D1: (a) as the target, via (b) — Python engine stays for the customer chat until per-structure parity, then globos3d.
- D3: the customer 2D is the plan's 3D render lightly modified.
- Products: Taller 3D pro (full control) vs customer chat (engine hidden, point edits only). D4 list pending.
- D4 (D-020): customer edits = AI requests + colour references + colour proportions + size proportions; no direct
  manipulation in the viewer. Customer-AI capability limits: later.
