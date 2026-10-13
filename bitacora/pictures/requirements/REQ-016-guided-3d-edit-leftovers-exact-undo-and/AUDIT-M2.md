# REQ-016 — Independent audit of M2

## Verdict

**pass-with-fixes**. Audited T2 `84fa287a` and T3 `c6dd13d4` against SPEC.md, PLAN.md, DESIGN-T2.md and D-035/D-046/D-047. Contained corrections are committed locally as `df0be2a0` and `fb872bce` on `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`. Session 12 resolves P-082 with D-048's versioned untouched-resolution history. No push, merge, deployment, production writes or paid calls.

The current gate passes all ten suites and now includes P-082's nine-case regression in `motor3d:test`. Main last-order tests pass 20/20; generated colour properties also verify replay with returned known history. Lint/types/workspace builds pass. The application build still fails on the unrelated, pre-existing P-083 worktree symlink; it is not claimed passing. Writer issuance remains disabled by default pending a separate reader release that accepts both nested colour-order versions.

## Findings fixed

1. **Reader-before-writer compatibility (high).** `crearTokenPlan` previously emitted v3 for every 3D token in the release that introduced the v3 reader. Strict previous readers reject it. Issuance now requires `PLAN_COLOR_ORDER_V3=true`, `backend=globos3d` and explicit known colour history. `.env.example` defaults the flag to false. Readers accept v1/v2/v3 regardless of the writer flag. This implements the existing D-035/D-046 decision; no production release or flag activation was performed.
2. **Unknown legacy history became known-empty (high).** Editing size on a v2 plan carried `undefined` to the envelope, but the writer invented `lastReplacement:null`. The corrected writer leaves such tokens v2 until a successful replacement explicitly establishes history. A real-route size-edit regression proves unknown history remains unknown even with the v3 writer enabled.
3. **A different destination retained an older order (medium).** The retention branch compared only the source phrase. `azul → gris` on an arch followed by `azul → negro` on a column retained both effects, creating a replay ledger instead of the last order. Retention now checks the current effective destination against the old entry on its own piece, including unselected pieces. Incremental/expanded selections with the same effective destination remain protected.
4. **Missing behavioural test for `origen.tipo` (medium; P-081 M2 portion).** The mutation test only observed a hash. It now changes origin to `edicion` and observes a genuine legacy `rosa → blanco` clarification. Temporarily removing the resolver's origin consumption makes the test fail; the source was restored in `finally`. The independent oracle also recognizes the R4 same-colour no-op, exercised by case 15.
5. **Lifecycle assertions were missing (medium).** Added real-route idea-sum, schema roundtrip/reload, replay and undo assertions. They check the signed last-order context, prior token restoration and unchanged replayed piece. The original suite header no longer claims every design acceptance subcase is exercised.

The three new code regressions first ran against the original implementation: 16 passed, 3 failed. After correction the main last-order suite passes 20/20. T3's preserved origin, R4 no-op and resolver consumption are verified. Genuine ambiguity and partial `puede ser` audit counts remain covered by existing gate tests; durable audit stores counts rather than customer phrases.

### 6. P-082 — Same-selection replay drift fixed (high, M)

Location: `src/lib/globos3d/motor/ediciones-color.ts`, `motor/orden-color.ts`, `plan/orden-color.ts`; regression: `scripts/test/test-ultima-orden-color-replay-selection.ts`.

Reproduction uses known-empty history and two columns in the same selection:

- Column 1: Fashion Rosa `011` + Azul `040`.
- Column 2: Rosado `009` + Azul `040`.
- First `rosado → rojo reflex`: exact-card priority changes only `009` in column 2 to `915`; column 1 stays intact.
- Repeat the identical order and selection using the returned editing context: column 2 is protected, but column 1 is reinterpreted and its `011` changes to `915`.

At `df0be2a0`, the record protected only actually changed pieces; it did not preserve how originally requested untouched pieces were resolved. `piezasSolicitadas` was stored but unused in replay recognition. Removing the original `009` changed global card-priority resolution on the next call. The existing generated legacy tests omitted the returned context on replay, so they did not detect it. Threading known history exposed seeded case 6 (`20261009`). Session 12 first reproduced the committed minimal test failing, then corrected the cause without changing exact-card priority.

D-048 adds separate `resolucionesSinCambio` snapshots inside nested `colour-order.v2`, read alongside strict v1. Matching source phrase, effective per-piece destination and unchanged identities protects originally resolved no-ops. Ambiguous pieces are not frozen. New selected pieces remain eligible; incremental orders retain earlier snapshots even when unselected. Colour mutations invalidate affected entries; pruning can retain only untouched snapshots when the last actual effect disappears. Honest output distinguishes a prior applied effect from a prior untouched resolution. The signed token and saved-widget outer contract remain unchanged, and the writer flag stays false. Missing v1 snapshots are never invented; the future rollback target must accept both nested versions.

Independent bounded design review identified the prune-only-snapshots edge case, which received its own regression. The staged antagonist approved the final fix and independently ran replay 9/9, main 20/20, signed context, confirmation, frontiers and consumption (29 leaves). The property generator now retains its old unknown-history assertion and adds one using returned history; seed 20261009 / 40 passes with 306 applied, 3 absent, and 15 each questions/options/replays/unedited cases.

## Findings deferred

### P-083 — Application build issues outside M2 (medium, M)

Default build fails because Turbopack rejects the worktree's external `node_modules` symlink. The documented Webpack alternative also fails on `node:crypto` through `reference-blueprint.ts → ReferenceAnalysisController.tsx → page.tsx`. Those modules were not changed by M2 or this audit. Neither build passed; no check was disabled and no unrelated configuration/boundary fix was mixed into this task.

P-081 still retains its aggregate-per-piece destination concern and readable `idea_sumada` documentation follow-up. Its mutation-coverage portion is fixed. The per-piece concern was not promoted to a confirmed production defect without a fabricable counterexample.

P-084 (low, S) records a future split of the existing 542-line main last-order suite into pure-domain and signed-route responsibilities. This session only changed one version expectation there; all new replay cases live in their own regression module.

## What I ran

### Session 12 — current acceptance evidence

| Check | Actual result |
|---|---|
| Initial committed P-082 regression at df0be2a0 | Exit 1; untouched 011 incorrectly became 915 |
| Dedicated replay regression after fixing | Exit 0, 9/9; identical/narrowed/expanded selections, size edits, colour mutation, prune-only snapshots, explicit new orders, v1 reader and signed reload/writer gate |
| Main last-order suite | Exit 0, 20/20 |
| Returned-history colour properties, seed 20261009 / 40 | Exit 0; 306 applied, 3 absent, 15 questions/options/replay/unedited cases each |
| `npm run gate` | Exit 0, `GATE OK`, 10/10 suites, including the registered P-082 regression; 559.14 seconds |
| `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` | Exit 0 in independent pre-commit review and guiada:test gate |
| Independent staged antagonist | SOUND; actual context/confirmation/frontiers/consumption/replay checks pass, no confirmed introduced defect |
| `npm run lint` | Exit 0, 0 errors / 50 pre-existing warnings |
| ESLint on seven staged TS files | Exit 0, no diagnostics |
| `npm run build --workspaces --if-present` | Exit 0, both packages built |
| `npx tsc --noEmit` and final recheck after property addition | Exit 0 |
| `npm run build` | Exit 1, `Symlink [project]/node_modules is invalid, it points out of the filesystem root` (P-083) |
| Final staged whitespace check / pre-commit secret scanner | Passed; no leaks found; commit fb872bce |

Complete logs: `/tmp/req016-m2-session12-{replay,main,properties-final,gate,lint,workspace-build,types,types-final,build,lint-staged}.log`. Every started verification/subagent completed; no background work remains.

### Session 11 — historical evidence before P-082 was corrected

| Check | Actual result |
|---|---|
| `git log`, `git diff fe3e9bcb..c6dd13d4`, consumer/schema inspection | T2/T3 reviewed; token consumer review independently corroborated compatibility/history findings |
| New rollout, legacy-history and different-destination regressions before fixing | Exit 1, 16/19 passed; three regressions failed |
| `npx tsx --conditions=react-server scripts/test/test-confirmacion-color-motor3d.ts` | Exit 0, `ok` |
| `npx tsx --conditions=react-server scripts/test/test-ultima-orden-color-motor3d.ts` | Exit 0, 20/20 passed after fixes |
| `npx tsx --conditions=react-server scripts/test/test-plan-contexto.ts` | Exit 0, signed context/Python mapping OK |
| `npx tsx --conditions=react-server scripts/test/test-motor-guiada-consumo.ts` | Exit 0, 29 leaves checked |
| Consumption mutation: temporarily replace `plan.origen.tipo === "edicion"` with `false` | Exit 1, `the legacy resolver must observe the edited origin`; source restored |
| Existing colour property generator, seed `20261009`, 40 cases plus deterministic pink matrix | Exit 0; 306 applied, 3 absent, 15 questions, 15 options, 15 replay cases, 15 unedited cases |
| Exploratory full property run threading returned known history | Exit 1 on colour case 6; minimized to P-082, not classified as a passing check |
| `npx tsx --conditions=react-server scripts/test/test-ultima-orden-color-replay-selection.ts` | **Exit 1, P-082: identical replay changes untouched `011` to `915`** |
| `npm run gate` | Exit 0, `GATE OK`, all 10 suites passed; standalone P-082 regression not included |
| `npm run lint` | Exit 0, 0 errors / 50 existing warnings |
| ESLint on all changed TS files after final test additions | Exit 0, no diagnostics |
| `npm run build --workspaces --if-present` | Exit 0, both workspace packages built |
| `npx tsc --noEmit` before and after application build attempts | Exit 0 |
| `npm run build` | Exit 1, Turbopack external symlink error |
| `npm run build -- --webpack` | Exit 1, client import of `node:crypto` |
| Staged diff review / `git diff --check` / pre-commit secret scanner | Passed; scanner found no leaks |

Evidence logs for this session: `/tmp/req016-m2-{red,green,gate,blocker,consumo-mutant,properties,color-properties-final,lint,lint-final,types-final,build,build-webpack}.log`.

## Continuation

M2 is approved locally with fixes in df0be2a0 and fb872bce. Keep `PLAN_COLOR_ORDER_V3=false` until a separate release has shipped a reader accepting both `colour-order.v1` and `colour-order.v2` inside token v3. D-048 extends D-046's original contract and rollback requirement. Publication remains outside this marathon's authorization. Investigate P-083 separately; P-081 and P-084 are deferred follow-ups. P-058 and P-082 are closed locally by the implementation and registered acceptance evidence.
