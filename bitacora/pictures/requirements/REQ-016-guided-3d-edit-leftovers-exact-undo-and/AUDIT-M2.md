# REQ-016 — Independent audit of M2

## Verdict

**reject**. Audited T2 `84fa287a` and T3 `c6dd13d4` against SPEC.md, PLAN.md, DESIGN-T2.md and D-035/D-046/D-047. Contained corrections are committed locally as `df0be2a0` on `feat/req-016-guided-3d-edit-leftovers-exact-undo-and`. P-082 still violates same-order replay protection and needs a design/implementation continuation. No push, merge, deployment, production writes or paid calls.

The existing gate passes all ten suites, but it does **not** cover P-082. The committed standalone regression fails deliberately and is not registered in the gate; its failure must be fixed and registered before approving M2. Green gate evidence must not be presented as acceptance of this milestone.

## Findings fixed

1. **Reader-before-writer compatibility (high).** `crearTokenPlan` previously emitted v3 for every 3D token in the release that introduced the v3 reader. Strict previous readers reject it. Issuance now requires `PLAN_COLOR_ORDER_V3=true`, `backend=globos3d` and explicit known colour history. `.env.example` defaults the flag to false. Readers accept v1/v2/v3 regardless of the writer flag. This implements the existing D-035/D-046 decision; no production release or flag activation was performed.
2. **Unknown legacy history became known-empty (high).** Editing size on a v2 plan carried `undefined` to the envelope, but the writer invented `lastReplacement:null`. The corrected writer leaves such tokens v2 until a successful replacement explicitly establishes history. A real-route size-edit regression proves unknown history remains unknown even with the v3 writer enabled.
3. **A different destination retained an older order (medium).** The retention branch compared only the source phrase. `azul → gris` on an arch followed by `azul → negro` on a column retained both effects, creating a replay ledger instead of the last order. Retention now checks the current effective destination against the old entry on its own piece, including unselected pieces. Incremental/expanded selections with the same effective destination remain protected.
4. **Missing behavioural test for `origen.tipo` (medium; P-081 M2 portion).** The mutation test only observed a hash. It now changes origin to `edicion` and observes a genuine legacy `rosa → blanco` clarification. Temporarily removing the resolver's origin consumption makes the test fail; the source was restored in `finally`. The independent oracle also recognizes the R4 same-colour no-op, exercised by case 15.
5. **Lifecycle assertions were missing (medium).** Added real-route idea-sum, schema roundtrip/reload, replay and undo assertions. They check the signed last-order context, prior token restoration and unchanged replayed piece. The original suite header no longer claims every design acceptance subcase is exercised.

The three new code regressions first ran against the original implementation: 16 passed, 3 failed. After correction the main last-order suite passes 20/20. T3's preserved origin, R4 no-op and resolver consumption are verified. Genuine ambiguity and partial `puede ser` audit counts remain covered by existing gate tests; durable audit stores counts rather than customer phrases.

## Findings deferred

### P-082 — Blocking same-selection replay drift (high, M)

Location: `src/lib/globos3d/motor/ediciones-color.ts:107`; regression: `scripts/test/test-ultima-orden-color-replay-selection.ts:26`.

Reproduction uses known-empty history and two columns in the same selection:

- Column 1: Fashion Rosa `011` + Azul `040`.
- Column 2: Rosado `009` + Azul `040`.
- First `rosado → rojo reflex`: exact-card priority changes only `009` in column 2 to `915`; column 1 stays intact.
- Repeat the identical order and selection using the returned editing context: column 2 is protected, but column 1 is reinterpreted and its `011` changes to `915`.

The record protects only actually changed pieces; it does not preserve how originally requested untouched pieces were resolved. `piezasSolicitadas` is stored but unused in replay recognition. Removing the original `009` changes global card-priority resolution on the next call. The existing generated legacy tests omit the returned context on replay, so they did not detect it. Expanding those tests to thread known history exposed seeded case 6 (`20261009`); the minimal committed regression preserves that counterexample without altering existing test expectations.

Independent antagonist re-review reproduced the failure and confirmed it violates the no-second-pink invariant. Resolving this safely requires deciding how to preserve original source resolution for already requested untouched pieces while allowing genuinely new selected pieces and subsequent colour changes. Do not change global exact-card priority or disable replay protection as a shortcut. Extend the context/lifecycle design if necessary, maintain reader compatibility, implement the fix and register this regression in `motor3d:test`. No speculative contract change was made during this audit.

### P-083 — Application build issues outside M2 (medium, M)

Default build fails because Turbopack rejects the worktree's external `node_modules` symlink. The documented Webpack alternative also fails on `node:crypto` through `reference-blueprint.ts → ReferenceAnalysisController.tsx → page.tsx`. Those modules were not changed by M2 or this audit. Neither build passed; no check was disabled and no unrelated configuration/boundary fix was mixed into this task.

P-081 still retains its aggregate-per-piece destination concern and readable `idea_sumada` documentation follow-up. Its mutation-coverage portion is fixed. The per-piece concern was not promoted to a confirmed production defect without a fabricable counterexample.

## What I ran

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

Start with P-082 and the committed minimal failing test. Fix source-resolution retention for unchanged pieces under the original selection, preserve exact-card priority and expanded-selection behavior, and add the regression to the gate. Rerun both milestone verify commands and the dedicated test. Keep `PLAN_COLOR_ORDER_V3=false` until a separate v3 reader release has shipped; publication remains outside this marathon's authorization. P-083 is a separate build investigation. No new architecture decision supersedes D-046 in this audit; its bounded rollout rule is now implemented, and the unresolved design gap is explicitly recorded above.
