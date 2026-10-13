---
req: REQ-016
task: T2
decision: D-046
status: design-ready
date: 2026-10-13
delegation: D-20261013-155122-0f2e
---
# T2 design audit — P-058 A1

## Outcome and scope

Design ready for implementation; T2 is **not implemented or closed** by this audit. Store the last successful colour replacement as server-signed editing context in the existing opaque approval token, with a versioned payload and reader-before-writer rollout. The pure colour resolver receives that context explicitly; `origen.tipo` remains provenance, not evidence that this colour order happened.

R2 means that an existing destination alone is not grounds to ask. A new order with one identifiable source changes that source and merges its weight into the destination. A proven repeat changes nothing and explains that it was already applied, without asking. Genuine multiple-source ambiguity still asks; destination presence does not select a source.

## Evidence at fe3e9bcbcfd1cd426d71fae974db2fc864244a71

- `color-en-pieza.ts:76-86` uses selection-wide `yaEntro` and `origen.tipo === "edicion"` to infer a possible repeat. `ediciones-comunes.ts:35-41` sets that origin for size and other successful edits as well.
- The standalone [reproduction](../../../.state/delegations/D-20261013-155122-0f2e/reproduce-t2.ts) exercises the real pure engine. A plan with `009/rosado + 005/blanco` accepts `rosa → blanco` initially. After a successful size edit, the same order returns `No pude: «rosa» puede ser Rosado en el arco; si es ese, dímelo con su nombre.` and leaves the plan unchanged.
- Two histories produce **identical specs**: replacing the first of `011/Rosa + 009/Rosado` with gray and then enlarging; starting with that gray palette and only enlarging. The next `rosa → gray` must be a repeat in the first history and a new replacement in the second. Current spec and origin cannot distinguish them.
- Step 4 also asks for a unique `640/Pastel Mate Azul` when gray is already present, even without an earlier edit. Removing only the `editada` branch will not fix A1 and the overlapping P-057(a).
- Existing N2 and two-pink tests deliberately expect a question on replay; their **no second colour change** invariant stays, but the question expectation must change for known history. The independent property oracle currently reproduces the origin heuristic too.
- All four clarification texts in the reproduction contain `puede ser`; none contains `¿` or `?`. A punctuation-only audit would count zero instead of four. This is an audit-observation requirement, not evidence of a missing production counter.
- `editar-motor.ts:208,215` already reports `hecho.noAplicadas` and its length, including these strings. No database migration or extra production count is justified by this finding.
- The historical 3.5% of 43,520 combinations in P-058 was not remeasured here.

## Authoritative state and contract

Use a small pure domain module for the colour-order model and replay matching, exported through `motor/v1.ts`. No browser cache, process-global map, DB lookup, model interpretation or network call owns this state.

The approval payload gains **v3**, retaining the existing signature, hash, browser binding, allowlist, expiry and `origenEn`. Only 3D plans write v3. Include one strict, runtime-validated `colorOrder` object with nested version `colour-order.v1` and `lastReplacement: null | record`. Existing v1/v2 tokens open as **unknown history**, distinct from a known `null` last replacement. Malformed signed context rejects the token; it must not silently become known-empty history.

A replacement record contains:

- The folded source phrase (trim, case/accents/whitespace normalization; at most the existing 80-character colour-input bound).
- Resolved selected piece IDs, including the distinction between requested pieces and pieces actually changed. Bounds reuse `MAX_PIEZAS_PLAN`; duplicate or nonexistent IDs reject at the boundary.
- For each actually changed piece: source codes consumed, effective destination codes after `colorFabricable`, and the resulting colour identities `(codigo, folded nombre)`. Destinations use the existing maximum colour bound. Identity comparison excludes weights and measurements; colour presence and labels determine whether the previous replacement still holds.

The outer signed `planHash` binds the context to the verified spec; do not duplicate a whole spec in the token. Source phrases stay inside that opaque editing context and never enter durable audit rows. No new `EspecClienteV1`, widget or saved-session field is written, so geometry/BOM hashes and the existing session schema stay unchanged.

## Resolution and state transitions

1. Validate the plan/token and edit as today. Resolve the current selection by stable IDs and the actual destination **per piece**; a destination in another piece is not evidence for this piece.
2. Before reinterpreting the source against the new palette, identify proven replay entries: same folded source phrase, same effective destination, piece selected now and changed by the stored replacement, and unchanged resulting colour identities. A changed selection suppresses only matching overlapping pieces, never newly selected pieces.
3. Proven replay entries remain byte-for-byte unchanged and produce a declarative reason such as `No pude: ese cambio de color ya estaba aplicado en el arco.` They do not prompt, count as applied or reprice by themselves. With no other actual changes, retain the current 422 `EDICION_NO_APLICADA` response and original token. No new success state is needed.
4. Resolve remaining pieces with the existing priority: exact card/code, palette synonym, unique catalogue shade, then remaining candidates. With known history, remove the single-candidate `yaEntro`/origin guess in both steps 2 and 4. Zero candidates stays an honest no-op/absence reason; more than one stays a clarification. Keep exact-card priority for a new order. Do not equate source synonyms in replay matching: `rosa` and `rosado` can intentionally address different cards.
5. After a successful replacement, replace the stored last replacement with its actual per-piece effects. For the same source/effective destination with an expanded selection, retain the selected proven-replay entries alongside newly changed entries; otherwise a third repeat could change a leftover colour in an earlier piece. Failed/ambiguous/no-op operations do not overwrite it. In partial edits record only actual effects and retained proven entries; the existing `sinHacer → noAplicadas` path retains unresolved pieces and their reasons.
6. Non-replacement edits preserve the last replacement and remove entries only if their piece disappeared or colour identities changed. Size, location, weights and flowers alone do not erase a still-effective replacement. Another successful replacement supersedes the record, even if it concerns another piece: this is last-order protection, not an unbounded replay ledger.
7. `aplicarEdiciones` threads spec **and context** sequentially within a batch; repeated operations inside one batch must see the updated state. Publish the final context only after spec validation, build, pricing and envelope creation all succeed. Rejected routes return the old plan/context without committing intermediate state.
8. A new independent plan starts known-empty. Summing an idea preserves context for unchanged existing pieces and does not claim new pieces were touched. Rebuilding a base preserves entries only where the resulting IDs and colour identities still match. Undo restores the prior widget/token (D-045), automatically restoring its corresponding colour history; reload retains it in that same token.
9. Legacy unknown history keeps the conservative existing heuristic until a successful colour replacement establishes a known last order, or the customer creates a new plan. Do not infer a known-empty history from a size edit, `idea_sumada` or token age. Removing this fallback belongs to a later migration after legacy tokens expire; it is the explicit limitation of old plans, not a solved A1 case.

For direct domain callers, an explicitly supplied known-empty context means no prior order. Omitted legacy context must remain unknown; silently treating it as empty would break replay tests and old callers.

## Consumer map, rollout and rollback

Implementation owners: `color-en-pieza.ts`, `ediciones-color.ts`, `ediciones-espec.ts` and a focused context module; token boundary `plan/aprobacion.ts`; `guiada-motor/verificar-plan.ts`, `editar-motor.ts`, `plan-motor.ts`; existing envelope `motor/plan-guiado-desde-motor.ts`. All three request forms (`ops`, chat `pedido`, panel `cambio`) converge on the same context-aware use case. No UI-specific colour rule is added.

Other token consumers to verify: `plan/token-motor.ts`, `guiada-motor/continuidad.ts`, `plan/aplicar-edicion.ts`, `plan/edicion-python.ts`, `plan/plan-desde-idea.ts`, `plan/ajuste-plan-entero.ts`, `/api/generate`, and `ia/herramientas/registro-herramientas.ts`. Python receives mapped commercial context, not the opaque token; its transport and prices need no change. The saved-session reader and the undo expiry reader must also be exercised with v3.

D-035 applies to compatibility even though the state lives inside an existing token string: current token readers use `.strict()` and reject v3. Ship/verify v3 readers while still writing v2 first; only a later approved release enables the 3D v3 writer. Do not enable it in the same first release or silently downgrade on rejection. Production publication is outside this task's authorization.

Rollback the writer/colour policy to a **v3-capable reader**; the preceding reader release continues to accept all issued tokens. Keep readers until every v3 token has expired (24 hours after the last issuance; stop v3 issuance/refresh first). Rolling back directly to the current pre-reader build would refuse still-valid tokens, so it is not a compatible rollback.

## Implementation acceptance tests

| Case | Required result |
|---|---|
| Size/location/flower edit, then `rosa → blanco` with one source and blanco selected | Apply without clarification; merge weights; other pieces unchanged. |
| Unique catalogue fallback with destination already present, known-empty history | Apply without clarification (covers the A1 overlap with P-057(a)). |
| `Rosa(011)` and `Rosado(009)`, repeat the same replacement | First changes only its exact card; second changes nothing and does not ask. |
| `azul` plus `Pastel Mate Azul`, repeat after a size/weight edit | No change to the remaining blue and no clarification. |
| Explicit remaining card name or a different destination | New order; not suppressed as a replay. |
| Destination only in another selected piece; narrowed/expanded selection | Resolve per piece; do not use another piece's destination to ask or suppress new work. |
| Same order expanded to another piece, then repeated a third time | Retain the earlier proven effects alongside the new ones; neither piece's remaining shade changes. |
| Two genuinely plausible source shades | Ask with usable catalogue names; responding once does not loop. |
| Effective destination substitution, partial edit and duplicate ops in one batch | Track actual changed pieces and bought codes; no second substitution/change; retain unresolved reasons. |
| Build/price/schema failure after a tentative edit | Original spec, token and context remain authoritative. |
| New plan, add idea, rebuild base, undo and reload | State follows the stated lifecycle; new/changed colour identities never inherit an unrelated effect. |
| v1/v2/v3, malformed context, wrong hash/browser and expired token | Runtime validation/authentication remain intact; unknown history remains distinguishable. |
| Clarification text containing `puede ser` without punctuation | Audit observes it in `noAplicadas` (total and partial), including durable count; no text is added to durable rows. |

Add a dedicated `test-ultima-orden-color-motor3d.ts` using real domain transitions and real-route integration with the existing pricing double. Register it in `motor3d:test`; extend `test-plan-contexto.ts`, `test-motor-guiada-color-dicho.ts`, `test-motor-guiada-auditoria-plan.ts` and the independent property generator/oracle for **known-empty, known-order and legacy-unknown** histories. Preserve the old confirmation test as a regression check; it is not sufficient as T2's acceptance test. Update the PLAN verify command only when the new suite exists.

## Audit checks actually executed

- Standalone reproduction: exit 0; confirms the defect, identical-state/different-history proof, existing replay protection and the question-audit blind spot. This is a characterization, **not a passing test of the future fix**.
- `test-confirmacion-color-motor3d.ts`: exit 0 (`ok`); baseline only.
- `test-motor-guiada-color-dicho.ts`: 21/21 pass; includes the question expectations that need deliberate updates.
- `test-plan-contexto.ts`: exit 0; baseline signed-context/Python mapping.
- No implementation, lint/typecheck/build/full gate or publication was performed by this design-only task. Implementation must execute the meaningful new tests, repository lint/types and `npm run gate`.
