# Solver report — 20261030-183605-d727

## Outcome

**asked_owner**. The origin is identified and reproduced. A bounded, validated SP-10 repair draft is ready, but the required owner reconfirmation has not been supplied. No product fix is implemented or integrated. The solver must not confirm a subplan or approve a stage for the owner.

## Trigger and decisive evidence

- Trigger: `pictures:REQ-021:r28:T10.45:T10.45:d1@k1`, exhausted browser-harness implementation attempts.
- Last captured candidate: `681bdc1f5368cfa18223a828e39087b1b532c9b9`, attempt `pictures-REQ-021-r28-T10.45-a4-44248b1b`. The manifest records no new changes.
- Independent verification `m6://result/dc9c39d204d16307c2a49b5ee629ab6929f259b0ac0fd4fe268b32e4d71e61e9` fails with `product_translation_failure` on `/asistente`. The attempt's actual browser evidence identifies the Spanish phrase `o prueba con una de nuestras fotos` among 39 visible strings for the English Designer Plus account. Mutation tests pass.
- `src/components/guiado/FotosEjemploGuiada.tsx:11` defines that fixed Spanish string; the idle button renders it directly at line 90 despite already using the shared language hook for other strings. `VistaGuiada.tsx:2017` mounts this component. The product repair regression omits the photo control.
- My read-only render of the real component under the real `IdiomaProvider` produces that same Spanish label for ES and EN. Its English assertion fails, exit 1. This proves a product translation defect, not a reason to exempt UI from scanning.
- T10.44 is inherited; its repair ownership omits this component. T10.45 owns only the two harness scripts and package wiring. A retry on the same producer cannot fix this defect.
- A separate proposed legacy check has a preexisting stale source oracle: `test-pulido-presentacion-guiada.ts:189` expects a spread guarded only by `esDev` followed by a newline; the actual `CabeceraApp.tsx:65,77` requires `esDev && puedeVerAdministracion`, with the permission bound to `PERMISOS.herramientas_internas`. Product authorization must remain unchanged.

## Concrete repair prepared by the Planner

Sent one bounded repair request through `tell-planner`, then supplied the newly observed legacy-test prerequisite and corrected one inaccurate illustrative permission expression with exact source lines. The Planner independently checked the source and amended the same request.

The draft adds **T10.441**, after accepted T10.44 and before T10.45:

- Translate the idle photo-control label through the existing guided-chat dictionary, keeping exact Spanish text and an English `or try one of our photos` label.
- Preserve `TEXTO_FOTOS_EJEMPLO` as a Spanish dictionary-derived compatibility export for the existing consumer.
- Add a real rendered EN/ES regression with enabled/disabled variants; dictionary-only assertions are insufficient.
- Explicitly own the narrowly proven obsolete test oracle, retain every legacy case, and prove negatives for missing development/permission guards. Do not change CabeceraApp product code or permission policy.
- Keep all frozen roles/routes, provider-call capture, scanner behavior, SP-9 data/fallback and manual real-provider NOT_RUN boundary.

Only existing-task change: `T10.45.after = [T10.441]`. Existing T10.44 and all existing acceptance criteria/checks remain equal to frozen r28. Existing frozen composition gates and the entire pre-amendment draft gate list remain equal. The existing T10.5 integration is explicitly declared as checkpoint because SP-10 now has nine tasks. Previously drafted SP-13 content is unrelated and was not attributed to this repair.

**Only SP-10 needs owner reconfirmation.** No new revision was frozen or joined. Live run remains `pictures:REQ-021:r28`; SP-11/SP-12 retain their independent T99 entrypoints.

## Verification actually executed

| Check | Result |
| --- | --- |
| Real FotosEjemploGuiada ES/EN server render on unchanged candidate | Exit 1 as intended: both languages render the Spanish literal; ES assertion passes and EN assertion fails. |
| `npm run idioma:test-reparacion-productores` | Exit 0; proves the current regression omits this defective control. |
| `npx --no-install tsx scripts/test/test-pulido-presentacion-guiada.ts` | Exit 1 preexisting: first seven cases pass; obsolete source regex fails at line 189. |
| Diagnostic legacy suite with only that regex corrected in memory, no repository write | Exit 0, eight cases. This isolates the oracle defect; it is not a passing unchanged-suite result or an implemented fix. |
| `bitacora.py --project pictures plan-json check REQ-021` | Exit 0, PLAN.json publishable. |
| `bitacora.py --project pictures plan-json stages REQ-021` | Exit 0. |
| Scoped documentation `git diff --check` | Exit 0. |
| Independent semantic diff against frozen r28 and Planner's pre-amendment draft | Pass: one new task, only T10.45 dependency changes among old tasks, existing criteria/checks/gates conserved. |
| Final `bt-durable status pictures REQ-021` | r28 still running; T10.45 still needs decision T10.45:d1, round k1. |

No fresh full browser run, application lint/types/build, methodology regression or integration was executed by this solver: no product/runtime code was changed. Historical browser results are labeled as evidence from the attempt and independent verifier. No paid provider call or manual attestation occurred.

## Rule and decision disposition

Recorded **pictures D-082**: a translation harness that finds a concrete producer defect must route repair to that producer's declared owner, with a real EN/ES component regression; never hide the control or repeatedly retry an incapable consumer. A newly required legacy check must first be checked on the accepted candidate; correct proven obsolete oracles within declared scope while preserving real authorization and all checks.

`T10.45:d1@k1` remains **unanswered**, deliberately. No retry, reverify, stop, runtime receipt, owner confirmation or stage approval was submitted. After owner reconfirmation, the authorized operator must freeze/join the bounded revision, inspect current task/decision state, and allow the run to produce and verify the correction before resuming its dependent harness. Do not blindly answer a superseded round.

## Owner question

¿Reconfirmas SP-10 con la reparación acotada T10.441 —traducción del control de fotos, regresión EN/ES y corrección del oráculo obsoleto— para congelar e incorporar la revisión y ejecutar el productor antes de T10.45? Con sí se continúa por ese flujo; con no se mantiene r28 y el bloqueo actual.

This confirmation is required by the explicit solver instruction: “never confirm a subplan or approve a stage for the owner.” The validated draft is in the requirement's PLAN.md/PLAN.json; it is not approval.

## Evidence files and changes

Working evidence directory: `/home/david/.local/share/bitacora-solver/pictures/20261030-183605-d727/`:
`producer-repro.json`, `producer-repro.log`, `attempt-evidence.json`, `legacy-oracle-probe.json`, `plan-validation.json`, `plan-validation-{0,1,2}.log`, `final-status.json`.

Documentation: this report, NOTES.md, pictures D-082, one English line in the run's day log, and the Planner's bounded draft/notes. **Commits: none. Main merge: none.** Existing dirty user checkouts were left untouched. No methodology worktree was created because no methodology code defect was demonstrated.
