---
req: REQ-016
status: approved
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

## Tasks
### M1 — Exact undo
- [x] T1 — Reproduce P-042 (enlarge-then-shrink drift, name-based colour return changing the code) with a failing test; make undo restore the stored previous spec instead of applying an inverse edit · files: src/lib/guiada-motor/editar-motor.ts, src/lib/globos3d/motor/ediciones-pieza.ts · repo: t12 · verify: `npx tsx --conditions=react-server scripts/test/test-deshacer-ajuste-3d.ts` · covers: R1, US-1
### M2 — Colour resolver
- [ ] T2 — Store the last colour order; no ask when the destination is already selected; count «puede ser» in no_aplicadas audit (A1) · repo: t12 · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` · covers: R2
- [ ] T3 — A2 keep `origen` in sumarIdeaAEspec; A3 `!entran.includes(codigo)` for «rosa → rosado»; A4 origen.tipo in consumo · repo: t12 · after: T2 · verify: `npm run gate` · covers: R3, R4
## Verification
`npm run gate`; `npx tsc --noEmit`; `npm run lint`.
- 2026-10-13 14:56 plan APPROVED (terminal)
- 2026-10-13 14:56 launched marathon supervisor (pool auto, haiku) from HQ in `/home/david/dev/pictures-wt`
- 2026-10-13 M1/T1 investigation: requested Workflow tool is unavailable. Existing editor route returns and tests exact before/after specs; no UI undo consumer exists. `test-motor-guiada-integracion.ts` confirms the inverse-edit symptoms (size drift 7.2%, color codes differ in 9 cases and fuse in 8). The required cut test passes but does not exercise undo. Escalating before speculative implementation.
- 2026-10-13 15:3x M1/T1 done (standard tier): «Deshacer» restores the stored previous widget in memory (D-045), commit 58f10c04 in t12 on `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`. test-deshacer-ajuste-3d (8 cases, real edit route) + UI case green; motor3d:test and guiada:test green; 2 antagonist passes, no blockers, minors fixed or filed as P-078..P-080.
- 2026-10-13 15:26 plan APPROVED (terminal)
- 2026-10-13 15:3x M1/T1 session 5 (top tier): verify re-run green (8/8) from t12; session 3's verify_failed came from the old verify command (tsx resolve error, not reproducible). Strengthened the colour case to reproduce the name-based return changing the codes (fusion 040+970 → 040), commit fe3e9bcb; motor3d:test green, antagonist sound.
