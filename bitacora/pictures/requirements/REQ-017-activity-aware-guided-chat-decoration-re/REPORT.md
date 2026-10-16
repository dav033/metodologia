# REQ-017 implementation report

## Built
- Extracted the existing event vocabulary and pure search normalizer into client-safe modules while retaining current exports.
- Added a curated ordered map from 11 canonical activities to supported official structure IDs.
- Restricted free-composition tool schemas and deterministically enforced the same event policy on provider output, with audit only when enforcement changes the proposal.
- Added event-specific exact-ID options to the individual-piece menu and retained «La que tú quieras»; unknown events keep the existing menu and schema.
- Preserved explicit customer choices, existing-plan edits and the saved widget schema. Event and menu position use the existing analytics action.

## Verification evidence
- `npm run guiada:test` — passed, including the three REQ-017 mapping, proposal-policy/audit and menu/session regression scripts.
- `npm run test-propiedades-herramientas` — passed; 45 tools checked and 1,720 invalid calls rejected.
- `npx tsc --noEmit` — passed.
- `npm run lint` — passed with 0 errors and 50 warnings, matching the existing warning count.
- `npm run build --workspaces --if-present` — passed for `@sempertex/agente-core` and `@sempertex/happie-package-ia`.
- `npm run build -- --webpack` — passed; Next compiled successfully, completed TypeScript validation and generated 83/83 static pages. The default Turbopack build failed before compilation because the isolated worktree's `node_modules` symlink points outside its filesystem root. The successful standalone trace generated 27 untracked files under `pictures/node_modules/**`; they are excluded from source changes and preserved.
- `git diff --check` — passed.
- Independent spec review — approved after the reviewer confirmed the generated build artifacts were excluded from the implementation diff and withdrew that finding.
- Independent standards review — approved with no confirmed findings.
- `bitacora.py trace --node REQ-017` — no uncovered, unknown-ref or dangling references.

## Rulings
- D-052: the owner asked to continue using the proposed defaults as revisable assumptions; this is not five item-by-item product approvals.
- Existing-plan edits and explicit customer-named structures retain precedence. Unknown events preserve prior behavior. No event data is added to persisted widget state.
- The curated table is policy owned by the product, while catalogue/library coverage is informational.

## Needs your eyes
- Review the provisional mapping and event recommendation policy in [estructuras-por-evento.ts](/home/david/dev/pictures-wt/req-017-v2/src/lib/plan/estructuras-por-evento.ts) and [politica-propuesta-evento.ts](/home/david/dev/pictures-wt/req-017-v2/src/lib/ia/guiado/politica-propuesta-evento.ts). P-101 and round-01 remain open for changes.

## Proposals
- None.

## Pending
- P-101: owner review or revision of the provisional event-to-structure mapping and related assumptions.
- The source changes remain isolated in `/home/david/dev/pictures-wt/req-017-v2` on `feat/req-017-activity-aware-v2`. Nothing was integrated, committed, pushed or deployed.

## Walkthrough
- `VistaGuiada` derives the canonical event from the current brief or customer messages without persisting a new field.
- `eventos-conocidos.ts` keeps the current event vocabulary client-safe; the curated map is shared by the menu and API.
- The individual-piece menu renders mapped official IDs in order and preserves a free-choice option.
- The API narrows the free-composition tool schema and enforces the same mapping against provider output.
- If enforcement changes a proposal, the existing audit trail records the adjustment; no decision is recorded when output already complies.
- Existing plan edits and explicit named structures keep priority, while unknown events use existing behavior.
- If P-101 changes product policy, update the curated map and its regression tests together.
