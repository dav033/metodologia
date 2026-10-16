---
req: REQ-017
status: approved
created: 2026-10-16
source: Planner re-run (Opus 5.5 high, read-only); owner approved for isolated M1/M2 experiment on 2026-10-16
---
# Plan — REQ-017 — Activity-aware guided-chat decoration recommendations

## Approach
One client-safe owner maps canonical activities (reusing `eventoDeTexto`) to an ordered list of official,
3D-viewable structures. The server narrows the `proponer_composicion` schema for free complete proposals,
deterministically corrects out-of-policy provider output before `propuestaConLoPedido` (so customer-named
pieces keep precedence), and records the policy in the existing `decidir` audit trail. The client derives the
same activity at render time and shows the recommended structures as selectable cards, with «La que tú quieras»
last; unknown activities keep today's menu and proposal behaviour. No widget field, contract version, database,
pricing or 3D change.

## Working assumptions (revisable; none is an owner answer)
Round-01 q1–q5 remain open. This draft uses the recommended options as assumptions, plus three new ones (A6–A8).
- A1 (q1): curated table below; library coverage is not a source.
- A2 (q2): only inside the existing «Propónme algo» flow; no proactive turn.
- A3 (q3): an independent part = one official structure in the existing individual-piece path.
- A4 (q4): structures in `ESTRUCTURAS_SIN_VISTA_3D` are never recommended; explicit requests keep current handling.
- A5 (q5): exact event structures as selectable cards plus «La que tú quieras».
- A6 (new): `arco_asimetrico` is replaced by `arco` in the table, because its official name «Arco orgánico» collides with the
  generic «Arco orgánico» button that deliberately means `arco`.
- A7 (new): «La que tú quieras» (individual, no piece) keeps current behaviour; SPEC R2 restricts only complete proposals.
- A8 (new): «approximate» 3D structures (`bouquet`, `arco_no_denso`, `columna_no_densa`) may be recommended.

Working table (Opus table with A6 applied):
| Canonical activity | Ordered official structure IDs |
|---|---|
| cumpleaños | arco, columna, semiarco, guirnalda, bouquet, aro_circular |
| baby shower | semiarco, guirnalda, arco, bouquet, aro_circular, columna |
| XV años | arco, columna_asimetrica, semiarco, pared_densa, techo_globos, aro_circular |
| boda | arco, semiarco_asimetrico, aro_circular, guirnalda, columna, pared_densa |
| bautizo | arco_no_denso, aro_circular, columna_no_densa, guirnalda, bouquet |
| graduación | arco, columna, pared_densa, bouquet, guirnalda |
| Halloween | arco, columna_asimetrica, guirnalda, racimo_pared |
| Navidad | aro_circular, guirnalda, columna, techo_globos |
| Día de la Madre | semiarco, guirnalda, bouquet, racimo_pared, arco |
| San Valentín | aro_circular, guirnalda, bouquet, columna |
| fiesta de empresa | arco, columna, pared_densa, techo_globos, guirnalda |

## Global constraints
- Reuse the canonical event vocabulary; keep synonym order (first match wins). No fourth vocabulary.
- Client modules must not import `biblioteca.ts`, `ideas-guiadas.ts` or `decoraciones.json`.
- No change to `WidgetGuiadoSchema`, saved sessions, `AsistenteGuiadoRequestSchema`, pricing, materials, 3D, DB.
- `/happie`, library search and the carousel are out of scope. No paid model calls in any check.
- Verification commands are proposals; none was run while planning.

## Milestones and tasks

### M1 — Client-safe activity resolution and curated policy
- [ ] T1.1 — Extract client-safe text normalizer and canonical event parser · repo: pictures · verify: `npx tsc --noEmit` · files: src/lib/texto/normalizar-busqueda.ts, src/lib/biblioteca-sempertex/biblioteca.ts, src/lib/ia/guiado/eventos-conocidos.ts, src/lib/ia/guiado/ideas-guiadas.ts · resources: guided-event-vocabulary
- [ ] T1.2 — Add the curated activity-to-structure policy module · repo: pictures · after: T1.1 · verify: `npx tsx scripts/test/test-estructuras-por-evento.ts` · files: src/lib/ia/guiado/estructuras-por-evento.ts, scripts/test/test-estructuras-por-evento.ts · resources: event-structure-policy

### M2 — Server enforcement and audit for complete proposals
- [ ] T2.1 — Add pure event-policy enforcement and schema narrowing · repo: pictures · after: T1.2 · verify: `npx tsx --conditions=react-server scripts/test/test-propuesta-por-evento.ts` · files: src/lib/ia/guiado/propuesta-por-evento.ts, src/lib/ia/guiado/esquema-herramienta-propuesta.ts, scripts/test/test-propuesta-por-evento.ts · resources: event-structure-policy, proposal-tool-schema
- [ ] T2.2 — Apply the event policy in the guided-assistant route and audit it · repo: pictures · after: T2.1 · verify: `npx tsx --conditions=react-server scripts/test/test-propuesta-por-evento.ts` · files: src/app/api/asistente-guiado/route.ts, scripts/test/test-propuesta-por-evento.ts · resources: asistente-guiado-route, guided-decision-audit

### M3 — Activity-aware individual-piece menu
- [ ] T3.1 — Build activity-aware piece menu options · repo: pictures · after: T1.2 · verify: `npx tsx scripts/test/test-menu-pieza-por-evento.ts` · files: src/components/guiado/PreguntaPropuesta.tsx, scripts/test/test-menu-pieza-por-evento.ts · resources: event-structure-policy, piece-menu-cards
- [ ] T3.2 — Wire the activity menu into the guided view without changing saved widgets · repo: pictures · after: T3.1 · verify: `npx tsc --noEmit` · files: src/components/guiado/VistaGuiada.tsx · resources: guided-widget-persistence, piece-menu-cards

### M4 — Integration gate
- [ ] T4.1 — Register new regressions in guiada:test and run the full gate · repo: pictures · after: T2.2, T3.2 · verify: `npm run guiada:test` · files: package.json · resources: package-scripts

## End-to-end acceptance
- For a recognised activity, complete proposals and piece cards use the same ordered list from one module.
- No structure in `ESTRUCTURAS_SIN_VISTA_3D` is ever recommended; explicit customer requests still follow current handling.
- Unknown activities, plan edits, individual-piece turns, library search, prices and customer-named pieces behave as today.
- Every active event-policy turn leaves one `regla:estructuras_por_evento` decision, including any replacements.
- Saved sessions and the widget schema are unchanged; reverting each milestone restores the previous behaviour.

## Risks
- The table is unapproved product policy (q1, A6); it lives in one data file so corrections stay local.
- The provider schema is advisory; server enforcement (T2.1/T2.2) is the guarantee.
- Precedence errors in `route.ts` would affect every beta customer; T2.2 keeps `propuestaConLoPedido` after the policy.
- `aro_circular` lacks 3D only in its partial form (`esAroParcial`); proposals are assumed not to request it.
- No manual UI walk-through is possible without paid model turns; menu behaviour is covered by pure tests only.

## Open owner questions
q1–q5 (round-01, unanswered), plus A6 (`arco_asimetrico`), A7 («La que tú quieras»), A8 (approximate-3D structures).

## Verification
Planning only. No command, test or `bt_planner check` was executed.

## Approval record
- 2026-10-16: The owner approved this isolated Opus draft for the M1/M2 experiment. Frozen as revision 1; this does not authorize M3 implementation.
