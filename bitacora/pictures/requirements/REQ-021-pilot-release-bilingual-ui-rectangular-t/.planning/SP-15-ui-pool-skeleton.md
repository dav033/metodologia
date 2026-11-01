# SP-15 draft skeleton — adopt metodologia's UI pool as `@bitacora/ui` (D-280)

Status: implemented outside the run by owner order; to record in PLAN as done. Landed on pictures local `main` at `516e3f7ab` (metodologia D-292), not pushed to origin. Draft task ids below are history. Previous status: DRAFT, not in PLAN.json. Owner decision 2026-10-31 relayed by the operator (metodologia D-280). Waiting for
the exact adoption steps from metodologia (package + sync are being built there). Nothing frozen, no stage change.
Why outside PLAN.json for now: adding a subplan reopens the skeleton confirmation, which would block the pending
SP-3 re-confirmation and stage freeze (T3.121 withdrawal).

## Outcome (proposed)

Pictures renders its shared UI controls from metodologia's component pool, consumed as the npm workspace
`@bitacora/ui` synced into `packages/bitacora-ui`, with a pictures theme that keeps the Sempertex colours and fonts;
pictures' own duplicates in `src/components/ui` are removed («gana el pool») and every existing UI regression still
passes.

## Scope

In:
- `packages/bitacora-ui` workspace (root `package.json` already declares `workspaces: ["packages/*"]`); sync step as
  metodologia defines it (pinned source revision, no hand edits inside the synced package).
- Pictures theme: map Sempertex colour and font tokens onto the pool's theme tokens (light and dark), no visual change
  beyond what the pool's components impose.
- Replace with pool components and switch imports: `checkbox`, `select`, `tabs`, `tooltip`, `Ayuda`,
  `interruptor-tema`, `foco-retorno`, `shell/*` (CabeceraApp, MenuApp, Compositor, HojaSeleccion, …). On origin/main
  these are imported by ≈38 files under `src` (foco-retorno 12, Ayuda 10, interruptor-tema 9, select 3, checkbox 2,
  tabs 1, tooltip 1, shell 2+).
- Delete the replaced pictures files once no import remains.
- Keep every existing UI regression green (accounts, plans, language, Taller panels, chat tools); bilingual strings
  (SP-8/SP-10 dictionaries) keep working through the pool components.

Out: `src/components/ui/reactbits/*` and `icon-button.css` unless the pool ships equivalents (to confirm with the
adoption steps); any redesign; new screens; changes to permissions or data.

## Draft tasks (ids provisional, estimates in agent minutes)

| Id | Kind | What | After | Est. |
|---|---|---|---|---|
| T15.1 | implement | Add `packages/bitacora-ui` via the metodologia sync at a pinned revision; build and type-check the workspace | T14.6, T10.6 | 45 |
| T15.2 | implement | Pictures theme: Sempertex tokens mapped to the pool theme (light/dark), loaded in the root layout | T15.1 | 60 |
| T15.3 | implement | Replace checkbox, select, tabs, tooltip, Ayuda, interruptor-tema, foco-retorno; switch imports; delete old files | T15.2 | 120 |
| T15.4 | implement | Replace the app shell (`shell/*`: CabeceraApp, MenuApp, …) keeping account menu, plans links and language switch | T15.3 | 120 |
| T15.5 | test | Full existing UI regression suite + production build smoke across signed-in entry points, both languages | T15.4 | 75 |
| T15.6 | audit | Visual review against the pool's contract and pictures' approved contracts (cuentas-admin@v2, planes@v2, …) | T15.5 | 45 |
| T15.7 | audit | Independent audit: no leftover duplicate components, no regression, theme fidelity, sync pinned | T15.6 | 55 |

Gate: a new composition check after CG-12 and before CG-13 (pilot candidate), so the release rehearsal (SP-13) runs on
the adopted UI.

## Ordering and conflicts

- Shell files are also written by T2.55 (done), T7.5, T8.2 (done) and `src/app/layout.tsx` by T2.4/T8.1 (done).
  Running/pending UI work: T14.5 (in progress), T14.6, T10.5, T10.6. T15.1 waits for T14.6 and T10.6 (their audits)
  so SP-15 never edits files under an active SP-2/SP-14/SP-10 task.
- Milestone: M5 with SP-13, before T13.1.
- Cut order: not in the owner's cut list; owner asked for it NOW inside REQ-021 — to confirm whether it may be cut if
  late (it is not in the never-cut list).

## Open points for the owner (when steps land)

1. Can SP-15 be cut before the pilot if late, or is it never-cut?
2. Does the pool replace `reactbits/*` and `icon-button.css` too, or do they stay?
3. Designer involvement: visual review only against the pool's own contract (proposed), no new direction choice.
4. `## Pruebas` row (D-131): pending; written when the subplan enters the plan.
