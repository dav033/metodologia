---
req: REQ-016
status: done
created: 2026-10-13
---
# Plan — REQ-016 — guided 3D edit leftovers

## Approach
Branch `feat/req-016-edit-leftovers` from `feat/req-015-judge-fix` (local only). Each task: reproduce with a failing test, fix the cause, run the targeted suite, antagonist review, commit. If a defect no longer reproduces, close it with evidence.

### M1 T1 ruling (2026-10-13)
- The existing server response already stores both `turno.antes.espec` and `turno.despues.espec` exactly, and `test-motor-guiada-editar-ruta.ts` asserts both snapshots. However, the guided UI has no undo action that consumes the prior snapshot; repository searches found the saved `antes` snapshot is only used for feedback. The integration suite currently demonstrates inverse-edit drift (7.2% max size drift; 9 color-code mismatches and 8 fusions) but does not model customer undo.
- The specified `test-corte-motor3d.ts` only covers cut-request parsing/auditing. No Workflow tool is available in this session. Do not invent a new undo endpoint or alter edit semantics without a design ruling; escalate T1 to standard for a clean-session design decision.

### M1 T1 ruling 2 (2026-10-13, standard tier) — supersedes the escalation above
- Design call made (D-045): the entry point is a «Deshacer» button next to «Último ajuste» on the 3D plan card; undo restores the previous plan widget kept in memory (signed espec + hash + token + quote) instead of applying an inverse edit. No new server endpoint, contract or persisted field (D-035). Files changed are client-side (`src/components/guiado/deshacer-ajuste.ts`, `usarDeshacerAjuste.ts`, `VistaGuiada.tsx`, `TarjetaPlan.tsx`), not the `editar-motor.ts` / `ediciones-pieza.ts` the plan guessed.
- Verification: `test-corte-motor3d.ts` is unrelated to undo (passes, not evidence). Evidence is `scripts/test/test-deshacer-ajuste-3d.ts` (registered in `motor3d:test`; uses the real edit route; was red before the module existed) and the new «Deshacer» case in `test-ui-plan-motor3d.ts`.

## Global constraints
AGENTS.md rules; no `any`; no paid calls; no push; `npm run gate` green before the last commit; customer copy in Spanish.

### M2 T2 design ruling (2026-10-13) — D-046
- Design audit: [DESIGN-T2.md](DESIGN-T2.md). Store the last successful colour replacement in versioned, server-signed approval context, carried explicitly through the pure edit use case. An existing destination alone never prompts with known history; a proven replay is an honest no-op without a question; genuine ambiguity still prompts. Preserve exact-card priority and per-piece effective destinations, partial/batched edits, undo and reload.
- The current verify suite passes but covers quantity/price confirmation, not A1. The audit reproduced a needless question after an actual size edit and proved identical specs can have different last-colour-order histories. Implementation must add/register `test-ultima-orden-color-motor3d.ts` and adjust the independent oracle rather than weakening replay protection.
- D-035 requires a v3-reader release before enabling v3 writers; current strict token readers would reject those tokens. This is design-ready only: T2 stays open, no code or release was performed. Existing v1/v2 history is explicitly unknown and keeps the conservative fallback until a successful colour replacement or a new plan establishes known context.

## Tasks
### M1 — Exact undo
- [x] T1 — Reproduce P-042 (enlarge-then-shrink drift, name-based colour return changing the code) with a failing test; make undo restore the stored previous spec instead of applying an inverse edit · files: src/lib/guiada-motor/editar-motor.ts, src/lib/globos3d/motor/ediciones-pieza.ts · repo: t12 · verify: `npx tsx --conditions=react-server scripts/test/test-deshacer-ajuste-3d.ts` · covers: R1, US-1
### M2 — Colour resolver
- [x] T2 — Store the last colour order; no ask when the destination is already selected; count «puede ser» in no_aplicadas audit (A1) · repo: t12 · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` · covers: R2
- [x] T3 — A2 keep `origen` in sumarIdeaAEspec; A3 `!entran.includes(codigo)` for «rosa → rosado»; A4 origen.tipo in consumo · repo: t12 · after: T2 · verify: `npm run gate` · covers: R3, R4
## Verification
`npm run gate`; `npx tsc --noEmit`; `npm run lint`.
- 2026-10-13 14:56 plan APPROVED (terminal)
- 2026-10-13 14:56 launched marathon supervisor (pool auto, haiku) from HQ in `/home/david/dev/pictures-wt`
- 2026-10-13 M1/T1 investigation: requested Workflow tool is unavailable. Existing editor route returns and tests exact before/after specs; no UI undo consumer exists. `test-motor-guiada-integracion.ts` confirms the inverse-edit symptoms (size drift 7.2%, color codes differ in 9 cases and fuse in 8). The required cut test passes but does not exercise undo. Escalating before speculative implementation.
- 2026-10-13 15:3x M1/T1 done (standard tier): «Deshacer» restores the stored previous widget in memory (D-045), commit 58f10c04 in t12 on `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`. test-deshacer-ajuste-3d (8 cases, real edit route) + UI case green; motor3d:test and guiada:test green; 2 antagonist passes, no blockers, minors fixed or filed as P-078..P-080.
- 2026-10-13 15:26 plan APPROVED (terminal)
- 2026-10-13 15:3x M1/T1 session 5 (top tier): verify re-run green (8/8) from t12; session 3's verify_failed came from the old verify command (tsx resolve error, not reproducible). Strengthened the colour case to reproduce the name-based return changing the codes (fusion 040+970 → 040), commit fe3e9bcb; motor3d:test green, antagonist sound.
- 2026-10-13 15:32 T1 done (marathon) — t12 branch feat/req-016-guided-3d-edit-leftovers-exact-undo-and: 58f10c04 («Deshacer» restores the stored previous plan widget — signed espec, hash, token, quote — never an inverse edit, D-045) + fe3e
- 2026-10-13 15:42 M1-audit done (marathon) — PASS: test-deshacer-ajuste-3d 8/8, test-ui-plan-motor3d 16/16, motor3d:test 27/27, guiada:test 14 suites pass; D-045 and P-042 verified byte-for-byte; AUDIT-M1.md written
- 2026-10-13 17:55 T2 done (marathon, top tier) — t12 branch feat/req-016-guided-3d-edit-leftovers-exact-undo-and: 84fa287a (almacenar última orden de color en payload v3 y evitar aclaración si destino ya está seleccionado, P-058 A1, D-046); test-confirmacion-color-motor3d green, test-ultima-orden-color-motor3d (14 cases) green, test-motor-guiada-fronteras green, gate OK; antagonist: 3 fixed (A1 circular import/boundary via src/lib/plan/orden-color.ts, A2 accent folding with plegar, A3 incremental selection retention), 1 triaged (A4 quizaRepetida tuned per D-046), 1 dropped (A5 piezasSolicitadas required by contract).
- 2026-10-13 17:56 T2 done (marathon) — Commit 84fa287a on feat/req-016-guided-3d-edit-leftovers-exact-undo-and in t12. test-confirmacion-color-motor3d ok, test-ultima-orden-color-motor3d 14/14 pass, test-motor-guiada-fronteras ok, full npm
- 2026-10-13 18:21 T3 done (marathon) — commit c6dd13d4 on feat/req-016-guided-3d-edit-leftovers-exact-undo-and; npm run gate GATE_EXIT=0; tsc --noEmit clean; Caso 15-16 (test-ultima-orden-color-motor3d) fail without the fix; antagonist A1 

### M2 audit ruling (2026-10-13)
- REJECTED, P-082 (high/M): exact same selection/order first removes Rosado 009 in one piece, then Fashion Rosa 011 in another originally selected untouched piece. The existing record cannot preserve that piece's original resolution; do not redefine exact-card priority or apply a speculative signed-state change during the audit.
- Audit corrections committed as `df0be2a0`: opt-in v3 writer for D-035/D-046, unknown legacy history stays v2, another effective destination supersedes old effects, resolver-consumption mutation coverage and lifecycle/oracle tests. No publication.
- Verification: gate 10/10, main last-order 20/20, confirmation/context/consumption and final types pass; lint 0 errors (50 existing warnings). The committed standalone same-selection replay regression fails and is not in the gate. Application builds fail separately (P-083); neither is called passing.
- Antagonist: initial contained fixes SOUND; one re-review confirmed P-082 blocking, no further defects in the contained corrections. P-081 mutation portion fixed, remaining follow-ups deferred. Full evidence and continuation: AUDIT-M2.md.
- 2026-10-13 19:01 M2-audit done (marathon) — PASS-WITH-FIXES: audited T2 84fa287a and T3 c6dd13d4; prior fixes df0be2a0 plus P-082 fix fb872bce committed on feature branch, clean tree. Registered replay 9/9, main last-order 20/20, returned-history properties green, gate 10/10 green.
- 2026-10-13 19:14 FINAL closing session 13 done — Evidence consolidated across AUDIT-M1.md and AUDIT-M2.md; plan verification run for real: `npm run gate` (10/10 suites, GATE OK), `test-deshacer-ajuste-3d.ts` (8/8 pass), `test-confirmacion-color-motor3d.ts` (ok), `test-ultima-orden-color-motor3d.ts` (20/20 pass), `test-ultima-orden-color-replay-selection.ts` (9/9 pass), `npx tsc --noEmit` (0 errors), `npm run lint` (0 errors, 50 warnings). REPORT.md written; bitácora updated; status: done.
