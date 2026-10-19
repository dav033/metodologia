---
req: REQ-019
status: launched
created: 2026-10-19
---
# Plan — Taller 3D stuck viewer fix, mobile usability and React Bits UI polish

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: launched · ejecución: done · hitos 4/4 · tareas 16/16 · generado: 2026-10-19T14:39:44-05:00

**M1 — Stuck viewer** · dificultad media · 3/3

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1 | Regression harness for viewer re-entry under Activity | media | completada | gpt-6-luna | codex-luis | 3 |
| T2 | Reset viewer state on cleanup and give the camera a valid start | media | completada | gpt-6-luna | codex-luis | 2 |
| T3 | Handle WebGL context loss and free contexts on destroy | media | completada | sonnet | claude-work | 2 |

**M2 — Mobile usability** · dificultad alta · 6/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T4 | Touch audit script for the Taller at 390x844 | media | completada | sonnet | claude-work | 4 |
| T5 | First paint without the desktop flash on phones | media | completada | sonnet | claude-work | 3 |
| T6 | Draggable bottom sheet over a full-height canvas | alta | completada | sonnet | claude-personal | 1 |
| T7 | Touch targets, hover-only actions and direct touch controls | media | completada | gpt-6-luna | codex-luis | 1 |
| T16 | Phone audit proves the sheet drag, reduced motion and camera offset | media | completada | gpt-6-luna | codex-luis | 3 |
| T8 | Touch audit and cheap fixes on the assistant and shared quote | media | completada | gpt-6-luna | codex-luis | 3 |

**M3 — React Bits** · dificultad alta · 5/5

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T9 | React Bits registry setup and shortlist install | media | completada | gpt-6-luna | codex-luis | 4 |
| T10 | Apply React Bits in the Taller | media | completada | gpt-6-luna | codex-luis | 2 |
| T11 | Apply React Bits in the assistant and shared quote | media | completada | gpt-6-luna | codex-luis | 4 |
| T12 | React Bits AI-chat components on the AI surfaces | alta | completada | sonnet | claude-work | 1 |
| T13 | Measure bundle and phone interaction cost before and after | baja | completada | gpt-6-luna | codex-luis | 1 |

**M4 — Close** · dificultad baja · 2/2

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T14 | Full gate and new UI suites on the final branch | baja | completada | sonnet | claude-work | 3 |
| T15 | Rebase, push to main and update the bitácora | baja | completada | gpt-6-luna | codex-luis | 3 |
<!-- bitacora:status:end -->

## Approach
Runs through the scheduler (15 tasks). The clean start from `main` (old M0) is already done: backup branch
`backup/req-014-local-20261019` and merge `ae78a79d` on `main` (tree identical to `2d924c10`, Happie untouched).
Fix the stuck viewer at its root cause (stale framing ref + stale `visor` across Next `<Activity>` hide/show) with a
regression test first. Then rework the Taller's mobile layer (sheet, targets, first paint) with a 390×844 touch audit
as the oracle. Then add a curated React Bits set (including its AI-chat Micro components) adapted to the repo tokens
and `motion` 13. Close with the full gate and a direct push to `main` (owner authorization, round 1 Q2).

## Global constraints
- **No manual verification.** Every criterion is checked by exactly one command that the verifier runs from a clean
  snapshot of the task's work, with Node, the browsers and the task's own `node_modules`, no network. Tasks that need
  a new oracle create it and name it in `created_by`: `taller:test-reentrada-ui` (`--base`, `--listar-aserciones`),
  `taller:test-movil-ui` (`--informe`, `--autoprueba`, `--listar-checks`, `--solo <check>`, `--rutas`,
  `--validar-pendientes`), `test-medicion-reactbits`, and the package scripts `taller:test-estatico`,
  `taller:test-ui-final` (T14). The verifier builds the workspace packages (`npm run build --workspaces`) inside the
  sandbox before every check, because their `dist` is git-ignored, and runs `next typegen` (route types such as
  `LayoutProps` are generated, git-ignored output). Type errors do not accumulate: T9 clears the debt and T10-T12 keep
  `npx tsc --noEmit` clean. A phone is emulated (390x844, touch), never a person.
- **Self-contained UI oracles.** The verifier has no network, no database, no env files and no running app, so every
  UI audit or test bundles the real components with esbuild and renders them from fixtures (the way
  `taller:test-reentrada-ui` does). A script that waits for a dev server on a port is a defect, not an oracle.
- `--base` is the only mode allowed to expect the bug: it passes while the unfixed viewer stays near radius 0 and
  is used by T1 alone. Every other mode asserts the fixed behaviour.
- **One task at a time, in a straight line.** The scheduler runs one task per attempt slot and merges the snapshots of every
  same-repository ancestor; two unordered tasks that touch one file end in `INTEGRATION_CONFLICT`. Every task therefore
  depends on the previous one (T7 → T8 → T16 → T9 → T10 → T11 → T12 → T13 → T14 → T15).
- Work in a worktree from `origin/main` (`ae78a79d` or later); never touch the owner's tree `~/dev/pictures`.
- AGENTS.md: TS strict, no `any`/`@ts-ignore`, `npm run lint`, `npm run build --workspaces --if-present`,
  `npx tsc --noEmit`, affected test scripts; report baseline failures separately from regressions.
- React Bits: TS+TW variants only, copied to `src/components/ui/reactbits/`, repo tokens, one `motion` version, live
  `prefers-reduced-motion`, no WebGL/canvas backgrounds on `/3d`, `@hugeicons` replaced by `lucide-react`, license
  notice kept (MIT + Commons Clause).
- Push to `main` only in T15, after T14's gate (owner authorization, round 1 Q2). `checks.yml` runs on push; Vercel likely builds Production from
  `main`; the VPS deploy (`deploy.yml`) is manual and is not run.
- Happie code stays unchanged.

## Tasks

### M1 — Stuck viewer
- [ ] T1 — Regression harness for viewer re-entry under Activity · verify: `npm run taller:test-reentrada-ui -- --base` · files: scripts/test/test-ui-taller-reentrada.ts, scripts/test/fixtures/taller-reentrada/arnes.tsx, src/components/tres-d/medicion-visor.ts · resources: package.json scripts · covers: R1, R2 · kind: test
- [ ] T2 — Reset viewer state on cleanup and give the camera a valid start · after: T1 · verify: `npm run taller:test-reentrada-ui` · files: src/components/tres-d/Taller3D.tsx, src/components/tres-d/escena-globos.ts · covers: R1, R2 · kind: implement
- [ ] T3 — Handle WebGL context loss and free contexts on destroy · after: T2 · verify: `npm run taller:test-reentrada-ui` · files: src/components/tres-d/Taller3D.tsx, src/components/tres-d/escena-globos.ts · covers: R3 · kind: implement

### M2 — Mobile usability
- [ ] T4 — Touch audit script for the Taller at 390x844 · after: T1 · verify: `npm run taller:test-movil-ui -- --informe` · files: scripts/test/test-ui-taller-movil.ts · resources: package.json scripts · covers: R5 · kind: test
- [ ] T5 — First paint without the desktop flash on phones · after: T3, T4 · verify: `npm run taller:test-movil-ui -- --solo primer-render` · files: src/components/tres-d/Taller3D.tsx · covers: R4 · kind: implement
- [ ] T6 — Draggable bottom sheet over a full-height canvas · after: T5 · verify: `npm run taller:test-movil-ui -- --solo hoja` · files: src/components/tres-d/HojaMovil.tsx, src/components/tres-d/Taller3D.tsx · covers: R6, R7 · kind: implement
- [ ] T7 — Touch targets, hover-only actions and direct touch controls · after: T6 · verify: `npm run taller:test-movil-ui` · files: src/components/tres-d/PanelPiezas.tsx, src/components/tres-d/MenuMas.tsx, src/components/tres-d/Inspector.tsx, src/components/tres-d/ControlesTactiles.tsx · covers: R5 · kind: implement
- [ ] T16 — Phone audit proves the sheet drag, reduced motion and camera offset · after: T8 · verify: `npm run taller:test-movil-ui -- --solo arrastre` · files: scripts/test/test-ui-taller-movil.ts, src/components/tres-d/HojaMovil.tsx, src/components/tres-d/Taller3D.tsx · resources: scripts/test/test-ui-taller-movil.ts · covers: R6, R7 · kind: test
- [ ] T8 — Touch audit and cheap fixes on the assistant and shared quote · after: T4, T7 · verify: `npm run taller:test-movil-ui -- --rutas asistente,cotizacion` · files: scripts/test/test-ui-taller-movil.ts, scripts/test/fixtures/movil-pendientes.json · covers: R10 · kind: implement

### M3 — React Bits
- [ ] T9 — React Bits registry setup and shortlist install · after: T16 · verify: `npx tsx scripts/test/test-reactbits-registro.ts` · files: components.json, src/components/ui/reactbits, package.json, package-lock.json · resources: package.json dependencies · covers: R7, R8 · kind: implement
- [ ] T10 — Apply React Bits in the Taller · after: T9 · verify: `npm run taller:test-movil-ui` · files: scripts/test/test-ui-reactbits-taller.ts, src/components/tres-d/PanelPiezas.tsx, src/components/tres-d/Biblioteca.tsx, src/components/tres-d/DialogoCompra.tsx · covers: R8 · kind: implement
- [ ] T11 — Apply React Bits in the assistant and shared quote · after: T10 · verify: `npx tsx scripts/test/test-reactbits-registro.ts` · files: scripts/test/test-ui-reactbits-cliente.ts, src/components/guiado/VistaGuiada.tsx, src/app/cotizacion-compartida · covers: R8 · kind: implement
- [ ] T12 — React Bits AI-chat components on the AI surfaces · after: T10, T11 · verify: `npx tsx scripts/test/test-ui-chat-ia-estados.ts` · files: src/components/ui/shell/EsperaAsistente.tsx, src/components/ui/shell/Compositor.tsx, src/components/tres-d/ia/TarjetaEnCurso.tsx, src/components/tres-d/GeneradorIA.tsx · covers: R9 · kind: implement
- [ ] T13 — Measure bundle and phone interaction cost before and after · after: T12 · verify: `npx tsx scripts/test/test-medicion-reactbits.ts` · files: scripts/test/test-medicion-reactbits.ts, scripts/test/fixtures/medicion-reactbits.json, package.json · resources: package.json scripts · covers: R8 · kind: test

### M4 — Close
- [ ] T14 — Full gate and new UI suites on the final branch · after: T13, T16 · verify: `npm run gate` · files: package.json · resources: package.json scripts · covers: R11 · kind: test
- [ ] T15 — Rebase, push to main and update the bitácora · after: T14 · verify: `git merge-base --is-ancestor HEAD origin/main` · covers: R11 · kind: implement

## Verification
- `taller:test-reentrada-ui -- --base` reproduces the near-zero camera radius on unfixed code (T1); the plain run
  passes on the branch for desktop and for 390x844 touch emulation (T2, T3, T14).
- `taller:test-movil-ui`: 0 targets < 44 px, 0 hover-only controls, 0 horizontal overflow, canvas ≥ 40 % at the
  medium sheet height, text ≥ 12 px; screenshots saved by the audit. Remaining issues on the assistant and shared
  quote live in `scripts/test/fixtures/movil-pendientes.json` with urgency and complexity.
- Reduced-motion runs of the UI suites show no animation; `test-reactbits-registro` passes.
- `npm run gate`, `taller:test-estatico` and `taller:test-ui-final` pass from a clean snapshot; bundle numbers
  before/after are in `scripts/test/fixtures/medicion-reactbits.json`.
- After the push (T15) the executor watches `checks.yml` and writes REPORT.md, SUMMARY, PENDING and DECISIONS in the
  bitácora; those two follow-ups are performed and logged, not machine-verified.

## Rulings
<!-- Judgment calls made during execution without asking. -->

## Progress log
- 2026-10-19 Draft from exploration (root cause H1 verified in code at `Taller3D.tsx:218-239,313`, `next.config.ts:16`).
- 2026-10-19 Owner approved the first (unclassified) draft; execution started in-session by mistake.
- 2026-10-19 Paused by the owner after old T1 (backup branch pushed) and old T2 (merge ae78a79d pushed to main, tree identical to 2d924c10); agents stopped before writing files.
- 2026-10-19 Owner: plans of this size run through the scheduler with classified tasks. Rewritten for PLAN.json 1.2.0 (old M0 done; tasks renumbered T1–T15).
- 2026-10-19 06:32 plan APPROVED (terminal)
- 2026-10-19 06:38 launched Scheduler supervisor from HQ in `/home/david/dev`
- 2026-10-19 Revision 2 (owner instruction in session 8eef50ee: nothing manual, the system must run without a human):
  every `manual` check became a command, T1/T4 no longer verify a command that fails by design (`--base`,
  `--autoprueba`, `--solo`), T5-T7 use targeted audit checks, T13 verifies a measurement fixture, T14 composes
  clean-snapshot checks, T15 keeps the push and checks it with git. T7 raised from low to medium.
- 2026-10-19 Revision 3 (found when T5's check hit `ERR_CONNECTION_REFUSED` on 127.0.0.1:3012): T4's audit must be
  self-contained; T4 is redone, T1-T3 are kept.
- 2026-10-19 Revision 4: T6 was accepted on `--solo hoja`, which moves the sheet with the keyboard and asserts three heights; it never
  drags with touch, never checks velocity snapping, live reduced motion or the camera offset. T16 adds those checks (and fixes what they
  expose) before the gate; T14 now waits for T16.
- 2026-10-19 Revision 5: T16 could not start (`INTEGRATION_CONFLICT` on `test-ui-taller-movil.ts`, edited by T7 and T8 from parallel branches).
  The remaining DAG is a single chain; T8 is redone on top of T7.
- 2026-10-19 Revision 6: T9's `npx tsc --noEmit` failed on errors the earlier tasks left in test files plus a missing generated
  `LayoutProps` (verifier now runs `next typegen`). T9 owns the clean-up; T10-T12 re-run the type check.
- 2026-10-19 Revision 7: T11 failed twice only because its agent never wrote `test-ui-reactbits-cliente.ts`, a script its own
  verification runs and no expected path named. T10-T12 now list their test script and T11/T12 say they create it; every agent prompt now
  says a named script that does not exist yet is the agent's to create.
