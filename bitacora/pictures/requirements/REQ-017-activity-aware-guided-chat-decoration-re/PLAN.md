---
req: REQ-017
status: done
created: 2026-10-16
source: D-20261016-090752-bc5d (Claude Work, Opus 5.5 high; read-only)
---
# Plan — REQ-017 — Activity-aware guided-chat decoration recommendations

## Approach
Use one curated, client-safe mapping from canonical activity names to supported official structures. Reuse `eventoDeTexto`; narrow and enforce the server's free-composition choice, record any adjustment in the existing decision trail, and show the exact recommended official structures as selectable options in the existing individual-piece flow. Unknown activities and explicit customer choices retain current behavior.

## Product assumptions from Opus (revisable)
- Apply recommendations only in the existing “Propónme algo” flow: complete composition and the existing individual-piece menu. Do not add a proactive chat turn.
- “Independent part” means one official structure in the existing individual-piece path, not extracting a component from a library idea.
- Exclude structures without 3D support from recommendation lists, but preserve explicit customer requests for them.
- Keep current behavior for unknown activities. For known activities, show the event's exact official structure IDs as selectable cards and keep «La que tú quieras» available; do not add a chat turn.
- Q1 (requires David's approval): use a curated event-to-structure table; use library coverage as an informational report, not as its source of truth.

Mapping used for this implementation under the owner's 2026-10-16 instruction to continue:
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
- Do not add a new persisted widget field when the event can be derived from the current brief and customer messages; preserve compatibility with saved conversations on rollback.
- The commands below define implementation checks. Planning had no checks; implementation evidence is recorded under Verification.

## Milestones and tasks

### M1 — Client-safe event mapping
Depends on: approval of the mapping and no-3D policy.

- [x] T1.1 — Extract the pure text normalizer and canonical event parser · files: `src/lib/texto/normalizar-busqueda.ts`, `src/lib/biblioteca-sempertex/biblioteca.ts`, `src/lib/ia/guiado/eventos-conocidos.ts`, `src/lib/ia/guiado/ideas-guiadas.ts` · verify: `npx tsc --noEmit` · covers: R1, R5
  - Move the pure `normalizarBusqueda` implementation out of `biblioteca.ts` and re-export it to preserve the current API.
  - Move `EVENTOS_CONOCIDOS`, `eventoDeTexto`, and `eventoDeMensajes` to a client-safe module; re-export the functions from `ideas-guiadas.ts` for existing consumers.
  - Acceptance: `eventos-conocidos.ts` imports no catalogue, React, provider, environment, or server-only modules; existing event consumers keep their imports; `eventoDeTexto("es para la boda de mi hermana")` returns `boda`.
- [x] T1.2 — Add pure curated mapping and accessors for selectable event structures · file: `src/lib/plan/estructuras-por-evento.ts` · after: T1.1 · verify: `npx tsc --noEmit` · covers: R1, R2, R4, R5
  - Export an exhaustive `Readonly<Record<EventoCanonico, readonly EstructuraOficialId[]>>`, `recomendadasParaEvento(evento)`, and `opcionesPiezaParaEvento(evento)`.
  - Acceptance: all IDs are official and unique; each recognized event has at least three; no unsupported 3D IDs occur; unknown events return no mapping; each returned card retains the exact official ID.
- [x] T1.3 — Add mapping behavior and coverage-report checks · file: `scripts/test/test-estructuras-por-evento.ts` · after: T1.2 · verify: `npx tsx --conditions=react-server scripts/test/test-estructuras-por-evento.ts` · covers: R1, R4, R5
  - Check canonicalization, table invariants, menu ordering, and print (without failing on) library support for each curated ID.
  - Acceptance: the check passes and reports thin support (including bautizo → `aro_circular`) as information.

### M2 — Server event-grounded proposal and audit
Depends on: M1.

- [x] T2.1 — Resolve the event and recommended IDs once per turn · file: `src/app/api/asistente-guiado/route.ts` · after: T1.2 · verify: `npx tsc --noEmit` · covers: R2, R3, R5
  - Prefer the normalized confirmed brief event, then the event inferred from customer facts. Compute the recommended IDs only for the “Propónme algo” choice.
- [x] T2.2 — Narrow and enforce the proposal schema · files: `src/lib/ia/guiado/esquema-herramienta-propuesta.ts`, `src/lib/ia/guiado/propuesta-composicion.ts`, `src/lib/ia/guiado/politica-propuesta-evento.ts`, `src/app/api/asistente-guiado/route.ts` · after: T2.1 · verify: `npm run test-propiedades-herramientas` · covers: R2, R3, R5
  - Restrict the schema enum to the event list for free composition. Do not narrow plan edits, customer-named structures, or unknown activities.
  - Enforce the same rule server-side for provider outputs outside the list: prefer a recommended structure of the same base type when available, else the first unused recommended structure; keep quantities unchanged and avoid duplicates.
  - Explicit customer wording takes precedence. Record an audit decision only if the server adjusts model output.
- [x] T2.3 — Add server rule regressions · file: `scripts/test/test-propuesta-por-evento.ts` · after: T2.2 · verify: `npx tsx --conditions=react-server scripts/test/test-propuesta-por-evento.ts` · covers: R2, R3, R5, R6
  - Acceptance: recognized event narrows the tool enum; invalid provider structures are replaced with distinct allowed IDs and audited; explicit customer requests and existing-plan edits remain unchanged; unknown event leaves all 18 IDs and emits no event-policy decision.

### M3 — Activity-specific selectable structures in the individual-piece menu
Depends on: M1; independent of M2 after M1.

- [x] T3.1 — Derive the menu event without changing the persisted widget schema · file: `src/components/guiado/VistaGuiada.tsx` · after: T1.1 · verify: `npx tsc --noEmit` · covers: R1, R5
  - Derive the event from the confirmed brief or the customer's messages at render time; do not add a field to `WidgetGuiadoSchema` or saved conversations.
- [x] T3.2 — Show exact event structures as selectable cards · files: `src/components/guiado/PreguntaPropuesta.tsx`, `src/components/guiado/VistaGuiada.tsx` · after: T1.2, T3.1 · verify: `npx tsc --noEmit` · covers: R1, R5
  - For known events, show cards built from the event's exact official IDs and official names, plus «La que tú quieras»; ensure selection sends that exact structure ID. For unknown events, retain the current menu unchanged.
  - Record activity and displayed position with the existing `propuesta.pieza` action for later analysis.
- [x] T3.3 — Verify exact selectable structures and saved-session compatibility · files: `scripts/test/test-estructuras-por-evento.ts`, `scripts/test/test-propuesta-por-evento.ts`, `scripts/test/test-menu-pieza-evento.ts` · after: T3.2 · verify: `npm run guiada:test` · covers: R1, R5
  - Acceptance: every event card sends the exact official ID in its mapping; «La que tú quieras» remains available; an unknown event shows the exact current menu; saved widgets retain their existing schema.

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

## Assumptions used for implementation
The owner requested continuing development on 2026-10-16. The following Opus recommendations are used as revisable assumptions; no item-by-item owner approval is recorded.
1. Use the curated mapping above; the library provides informational support evidence only.
2. Recommend only through the existing “Propónme algo” flow; do not add a proactive chat turn.
3. Define an independent part as one official structure in the existing individual-piece path.
4. Exclude structures without 3D support from recommendations; preserve explicit customer requests and current unknown-event behavior.
5. Show exact event-specific structure IDs as selectable cards for known activities, with «La que tú quieras» retained; no additional chat turn or persisted widget field.

## Rulings
- The owner's request to continue authorizes implementation using the proposed defaults as revisable assumptions; it does not answer the five product questions individually (D-052). Cost if wrong: the owner may revise the mapping or recommendation surface before integration.
- Event enforcement is limited to free proposals without an existing plan or explicit customer-named structure. This preserves existing-plan edits and explicit choices; customer requests remain authoritative even when their structure is outside the curated list.
- A provider structure outside the event list is replaced by an unused recommendation of the same base type where possible, otherwise by the first unused recommendation. When the list is exhausted, the excess piece is omitted; quantities and the remaining piece attributes are retained.

## Verification
- `npm run guiada:test`: exit 0, including the event mapping, server enforcement/audit, menu selection and saved-schema regressions.
- `npm run test-propiedades-herramientas`: exit 0; 45 tools checked and 1,720 invalid calls rejected.
- `npx tsc --noEmit`: exit 0.
- `npm run lint`: exit 0, 0 errors and 50 warnings, matching the existing warning count.
- `npm run build --workspaces --if-present`: exit 0; `@sempertex/agente-core` and `@sempertex/happie-package-ia` built.
- `npm run build -- --webpack`: exit 0; Next compiled successfully, completed TypeScript validation and generated all 83 static pages. The default Turbopack attempt failed before compilation because the worktree's `node_modules` symlink points outside its filesystem root. The successful standalone trace left 27 untracked generated files under `pictures/node_modules/**`; these remain outside the source changes and were preserved.
- `git diff --check`: exit 0.
- Independent spec and standards reviews: both approved. The spec reviewer withdrew the generated-artifact finding after confirming the files remain excluded from the change.
- `python /home/david/dev/metodologia/skill/scripts/bitacora.py --project pictures trace --node REQ-017`: exit 0; no uncovered, unknown-ref or dangling references.

## Progress log
- 2026-10-16: Opus completed read-only analysis and drafted this plan in delegation `D-20261016-090752-bc5d`. David's direct implementation request authorizes an isolated draft using these defaults; owner review remains open before integration.
- 2026-10-16 09:21 review comments (terminal): Owner's direct implementation request authorizes an isolated draft with Opus 5.5 high's recommended defaults; round-01 stays open for changes before integration.
- 2026-10-16 09:21 plan APPROVED (terminal)
- 2026-10-16: post-implementation review found that several recommended IDs had no selectable menu card and the optional persisted widget field could drop saved conversations after rollback. Revised M3 to show exact event structures and derive the event without changing the saved widget schema.
- 2026-10-16 09:32 review comments (terminal): Scope refined during read-only review to make every curated structure selectable and avoid a persisted widget-schema change. The owner's direct implementation request authorizes the isolated draft; round-01 remains open for changes before integration.
- 2026-10-16 09:32 plan APPROVED (terminal)
- 2026-10-16 owner scope correction: the task was read-only Planner review; earlier coordinator approvals were mistaken and did not represent owner approval. Implementation delegation `D-20261016-093409-9805` was stopped, with partial source changes preserved in its isolated worktree.
- 2026-10-16 owner requested continuing development: use the recommended defaults above as revisable assumptions. The five individual product choices remain open for correction; approval to proceed is not logged as item-by-item answers.
- 2026-10-16 implementation continued in isolated worktree `req-017-v2`. Extracted the client-safe event vocabulary and search normalizer, added the exhaustive curated map, narrowed and deterministically enforced free proposals with audit, and added exact-ID event cards without changing saved widget schema. `planActual` bypasses event policy to preserve existing-plan behavior (spec review finding fixed).
- 2026-10-16 independent spec and standards reviews: spec finding about existing-plan edits fixed and rechecked; standards review found automated regression coverage still pending. No code was committed or integrated.
- 2026-10-16: Added and passed mapping, proposal-policy/audit and menu/session regression tests; `guiada:test`, tool property tests, lint, TypeScript, workspace builds and the Webpack app build all passed. Both independent review axes approved. The app build left 27 untracked standalone trace files under `pictures/node_modules`; they are excluded from the source change and preserved. No integration, commit, push or deployment occurred. P-101 remains open for owner review of the provisional mapping and assumptions.
