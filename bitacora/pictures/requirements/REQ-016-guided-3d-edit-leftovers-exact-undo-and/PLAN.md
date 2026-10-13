---
req: REQ-016
status: launched
created: 2026-10-13
---
# Plan — REQ-016 — guided 3D edit leftovers

## Approach
Branch `feat/req-016-edit-leftovers` from `feat/req-015-judge-fix` (local only). Each task: reproduce with a failing test, fix the cause, run the targeted suite, antagonist review, commit. If a defect no longer reproduces, close it with evidence.

### M1 T1 ruling (2026-10-13)
- The existing server response already stores both `turno.antes.espec` and `turno.despues.espec` exactly, and `test-motor-guiada-editar-ruta.ts` asserts both snapshots. However, the guided UI has no undo action that consumes the prior snapshot; repository searches found the saved `antes` snapshot is only used for feedback. The integration suite currently demonstrates inverse-edit drift (7.2% max size drift; 9 color-code mismatches and 8 fusions) but does not model customer undo.
- The specified `test-corte-motor3d.ts` only covers cut-request parsing/auditing. No Workflow tool is available in this session. Do not invent a new undo endpoint or alter edit semantics without a design ruling; escalate T1 to standard for a clean-session design decision.

## Global constraints
AGENTS.md rules; no `any`; no paid calls; no push; `npm run gate` green before the last commit; customer copy in Spanish.

## Tasks
### M1 — Exact undo
- [ ] T1 — Reproduce P-042 (enlarge-then-shrink drift, name-based colour return changing the code) with a failing test; make undo restore the stored previous spec instead of applying an inverse edit · files: src/lib/guiada-motor/editar-motor.ts, src/lib/globos3d/motor/ediciones-pieza.ts · verify: `npx tsx --conditions=react-server scripts/test/test-corte-motor3d.ts` · covers: R1, US-1
### M2 — Colour resolver
- [ ] T2 — Store the last colour order; no ask when the destination is already selected; count «puede ser» in no_aplicadas audit (A1) · after: T1 · verify: `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` · covers: R2
- [ ] T3 — A2 keep `origen` in sumarIdeaAEspec; A3 `!entran.includes(codigo)` for «rosa → rosado»; A4 origen.tipo in consumo · after: T2 · verify: `npm run gate` · covers: R3, R4
## Verification
`npm run gate`; `npx tsc --noEmit`; `npm run lint`.
- 2026-10-13 14:56 plan APPROVED (terminal)
- 2026-10-13 14:56 launched marathon supervisor (pool auto, haiku) from HQ in `/home/david/dev/pictures-wt`
- 2026-10-13 M1/T1 investigation: requested Workflow tool is unavailable. Existing editor route returns and tests exact before/after specs; no UI undo consumer exists. `test-motor-guiada-integracion.ts` confirms the inverse-edit symptoms (size drift 7.2%, color codes differ in 9 cases and fuse in 8). The required cut test passes but does not exercise undo. Escalating before speculative implementation.
