---
req: REQ-017
status: approved
created: 2026-10-16
source: D-20261016-090752-bc5d (Claude Work, Opus 5.5 high; read-only)
---
# Plan — REQ-017 — Activity-aware guided-chat decoration recommendations

## Approach
Use one curated, client-safe mapping from canonical activity names to supported official structures. Reuse `eventoDeTexto`; narrow and enforce the server's free-composition choice, record any adjustment in the existing decision trail, and order the existing individual-piece menu by the same mapping. Unknown activities and explicit customer choices retain current behavior.

## Scope and decisions proposed by Opus
- Apply recommendations only in the existing “Propónme algo” flow: complete composition and the existing individual-piece menu. Do not add a proactive chat turn.
- “Independent part” means one official structure in the existing individual-piece path, not extracting a component from a library idea.
- Exclude structures without 3D support from recommendation lists, but preserve explicit customer requests for them.
- Keep current behavior for unknown activities. Keep the existing menu cards and order the matching cards; no event badge by default.
- Q1 (requires David's approval): use a curated event-to-structure table; use library coverage as an informational report, not as its source of truth.

Draft mapping (all entries must be confirmed or edited before implementation):
| Canonical activity | Ordered official structure IDs |
|---|---|
| cumpleaños | arco_asimetrico, columna, semiarco, guirnalda, bouquet, aro_circular |
| baby shower | semiarco, guirnalda, arco_asimetrico, bouquet, aro_circular, columna |
| XV años | arco_asimetrico, columna_asimetrica, semiarco, pared_densa, techo_globos, aro_circular |
| boda | arco, semiarco_asimetrico, aro_circular, guirnalda, columna, pared_densa |
| bautizo | arco_no_denso, aro_circular, columna_no_densa, guirnalda, bouquet |
| graduación | arco, columna, pared_densa, bouquet, guirnalda |
| Halloween | arco_asimetrico, columna_asimetrica, guirnalda, racimo_pared |
| Navidad | aro_circular, guirnalda, columna, techo_globos |
| Día de la Madre | semiarco, guirnalda, bouquet, racimo_pared, arco_asimetrico |
| San Valentín | aro_circular, guirnalda, bouquet, columna |
| fiesta de empresa | arco, columna, pared_densa, techo_globos, guirnalda |

Every table must contain at least three distinct official IDs and exclude `figura`, `centro_mesa`, `pared_organica`, and `pared_no_densa`, which lack 3D support. The current catalogue has only 31 visible reference ideas and sparse coverage for bautizo, Navidad, and empresa; that is why the plan proposes owner-curated policy instead of deriving it from the catalogue.

## Global constraints
- No code, test, package, catalogue, pricing, materials, 3D, database, contract-version, deployment, or migration changes outside the approved scope.
- Do not add a new event vocabulary or import `decoraciones.json` into the client bundle.
- `/happie` and `recomendarPaquetes` remain out of scope.
- Existing explicit customer choices and edits to an existing plan keep precedence.
- Verification commands below are proposed for a later approved implementation; none were run during planning.

## Milestones and tasks

### M1 — Client-safe event mapping
Depends on: approval of the mapping and no-3D policy.

- [ ] T1.1 — Extract the pure text normalizer and canonical event parser · files: `src/lib/texto/normalizar-busqueda.ts`, `src/lib/biblioteca-sempertex/biblioteca.ts`, `src/lib/ia/guiado/eventos-conocidos.ts`, `src/lib/ia/guiado/ideas-guiadas.ts` · verify: `npx tsc --noEmit` · covers: R1, R5
  - Move the pure `normalizarBusqueda` implementation out of `biblioteca.ts` and re-export it to preserve the current API.
  - Move `EVENTOS_CONOCIDOS`, `eventoDeTexto`, and `eventoDeMensajes` to a client-safe module; re-export the functions from `ideas-guiadas.ts` for existing consumers.
  - Acceptance: `eventos-conocidos.ts` imports no catalogue, React, provider, environment, or server-only modules; existing event consumers keep their imports; `eventoDeTexto("es para la boda de mi hermana")` returns `boda`.
- [ ] T1.2 — Add pure curated mapping and menu ordering helpers · file: `src/lib/plan/estructuras-por-evento.ts` · after: T1.1 · verify: `npx tsc --noEmit` · covers: R1, R2, R4, R5
  - Export an exhaustive `Readonly<Record<EventoCanonico, readonly EstructuraOficialId[]>>`, `recomendadasParaEvento(evento)`, and `ordenarPiezasIndividuales(piezas, recomendadas)`.
  - Acceptance: all IDs are official and unique; each recognized event has at least three; no unsupported 3D IDs occur; unknown events return no mapping; “La que tú quieras” stays last; unknown events preserve current menu order.
- [ ] T1.3 — Add mapping behavior and coverage-report checks · file: `scripts/test/test-estructuras-por-evento.ts` · after: T1.2 · verify: `npx tsx --conditions=react-server scripts/test/test-estructuras-por-evento.ts` · covers: R1, R4, R5
  - Check canonicalization, table invariants, menu ordering, and print (without failing on) library support for each curated ID.
  - Acceptance: the check passes and reports thin support (including bautizo → `aro_circular`) as information.

### M2 — Server event-grounded proposal and audit
Depends on: M1.

- [ ] T2.1 — Resolve the event and recommended IDs once per turn · file: `src/app/api/asistente-guiado/route.ts` · after: T1.2 · verify: `npx tsc --noEmit` · covers: R2, R3, R5
  - Prefer the normalized confirmed brief event, then the event inferred from customer facts. Compute the recommended IDs only for the “Propónme algo” choice.
- [ ] T2.2 — Narrow and enforce the proposal schema · files: `src/lib/ia/guiado/esquema-herramienta-propuesta.ts`, `src/lib/ia/guiado/propuesta-composicion.ts`, `src/app/api/asistente-guiado/route.ts` · after: T2.1 · verify: `npm run test-propiedades-herramientas` · covers: R2, R3, R5
  - Restrict the schema enum to the event list for free composition. Do not narrow plan edits, customer-named structures, or unknown activities.
  - Enforce the same rule server-side for provider outputs outside the list: prefer a recommended structure of the same base type when available, else the first unused recommended structure; keep quantities unchanged and avoid duplicates.
  - Explicit customer wording takes precedence. Record an audit decision only if the server adjusts model output.
- [ ] T2.3 — Add server rule regressions · file: `scripts/test/test-propuesta-por-evento.ts` · after: T2.2 · verify: `npx tsx --conditions=react-server scripts/test/test-propuesta-por-evento.ts` · covers: R2, R3, R5, R6
  - Acceptance: recognized event narrows the tool enum; invalid provider structures are replaced with distinct allowed IDs and audited; explicit customer requests and existing-plan edits remain unchanged; unknown event leaves all 18 IDs and emits no event-policy decision.

### M3 — Event-ordered individual-piece menu
Depends on: M1; independent of M2 after M1.

- [ ] T3.1 — Carry the optional event in the proposal widget · files: `src/lib/ia/guiado/widgets.ts`, `src/components/guiado/VistaGuiada.tsx` · after: T1.1 · verify: `npx tsc --noEmit` · covers: R1, R5
  - Add an optional bounded event field to the strict widget schema; derive it from the confirmed brief or customer messages. Old stored widgets without the field remain valid.
- [ ] T3.2 — Order existing menu cards by the shared mapping · files: `src/components/guiado/PreguntaPropuesta.tsx`, `src/components/guiado/VistaGuiada.tsx` · after: T1.2, T3.1 · verify: `npx tsc --noEmit` · covers: R1, R5
  - Order only the existing cards, keep the free-choice card last, and retain the current order for unknown events. Do not add a badge or new cards unless David approves them.
  - Record activity and displayed position with the existing `propuesta.pieza` action for later analysis.
- [ ] T3.3 — Verify menu ordering and compatibility · files: `scripts/test/test-estructuras-por-evento.ts`, `src/lib/ia/guiado/widgets.ts` · after: T3.2 · verify: `npm run guiada:test` · covers: R1, R5
  - Acceptance: baby shower shows Semiarco and Guirnalda first; an unknown event shows the exact current order; an old widget without `evento` parses.

## End-to-end acceptance
- For a recognized activity, complete proposals and individual-piece choices use the same approved ordered mapping.
- Unsupported 3D structures are never recommended; explicit customer requests for them still follow existing handling.
- Unknown activities, existing-plan edits, library search, prices, and customer-named choices retain current behavior.
- The audit trail records an event-policy adjustment only when enforcement changed the provider output.
- Proposed final checks after implementation: `npm run guiada:test`, `npx tsc --noEmit`, `npm run lint`, `npm run build --workspaces --if-present`, and `npm run build`; targeted checks are listed on each task. These are not run at planning time.

## Risks and rollback
- The table is product policy, not catalogue truth; review all lists before approval.
- An unknown free-text activity falls back to current behavior.
- The provider schema is advisory, so deterministic server enforcement is required.
- The event vocabulary is reused, not unified; a later requirement may consolidate the three existing event vocabularies.
- Each milestone is reversible by reverting its own changes; no database or external state changes are planned.

## Provisional defaults for the isolated implementation
David explicitly asked Claude Work to implement this feature and specified Opus 5.5 high. Use the recommendations below as the implementation defaults in the isolated worktree; the REQ-017 round remains open for David to revise them before integration.
1. Use the curated mapping above; the library provides informational support evidence only.
2. Recommend only through the existing “Propónme algo” flow; do not add a proactive chat turn.
3. Define an independent part as one official structure in the existing individual-piece path.
4. Exclude structures without 3D support from recommendations; preserve explicit customer requests and current unknown-event behavior.
5. Reorder existing menu cards only, without badges or new event-specific cards.

## Verification
No checks were run. This is the planning-only deliverable from Claude Work / Opus 5.5 high. The commands above define proposed verification for an approved implementation.

## Progress log
- 2026-10-16: Opus completed read-only analysis and drafted this plan in delegation `D-20261016-090752-bc5d`. David's direct implementation request authorizes an isolated draft using these defaults; owner review remains open before integration.
- 2026-10-16 09:21 review comments (terminal): Owner's direct implementation request authorizes an isolated draft with Opus 5.5 high's recommended defaults; round-01 stays open for changes before integration.
- 2026-10-16 09:21 plan APPROVED (terminal)
