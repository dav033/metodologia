# Solver 20261030-120814-28ad — same-snapshot integration and recorded unions

## Trigger and decisive origin

The session received 17 resolution triggers and the T2.55:d2@k1 decision of pictures:REQ-021:r27. The inexpensive diagnosis failed JSON parsing; the actual open failure is INTEGRATION_CONFLICT on MenuCuenta.tsx/textos-cuenta.ts against SP-14. The prior solver published eight exact menu resolutions and answered d1 with reverify; d2 nevertheless repeated the same integration failure.

Direct object-only replay through the real GitLineIntegrator now merges the SP-14 line ca9858eedfca88c04c63fa0ce179e5233f98bbfa and snapshot e3dfac3eea2f350c12d5e22981e3189361214203 without conflict. The workflow's _evaluate always enqueued bt:<attempt>:integrate, including owner re-verification. DBOS returned the completed failing child's stored result instead of observing integration again. An agent retry could not change that observation.

The operator separately notified this session about methodology D-213: own-subplan acceptance must defer foreign-line conflicts to the composition gate. No retry or further SP-14 menu resolution was issued here. D-221 fixes the separate stale-child problem required for reverify to observe either a recorded resolution or the D-213 repair.

## System fix

Only solver/20261030-120814-28ad in the session's private worktree was edited. Commit 88a7fd02 adds execution/integration_policy.py and changes _evaluate to use its profile-bound integration child identity. DBOS.patch(bt-task-reverify-reintegrates) preserves old histories; the standard profile keeps its old ID, and repeated replay of the same profile keeps the same child. Failed verification cannot invoke integration. projection.py selects the newest integration observation regardless of database row order. README records the behavior.

New regression test_durable_reintegrate: the cached-conflict test was red before the fix (3 tests, 1 failure, exit 1). A separate projection regression was red for reverse database order and passed after newest-observation selection. Five final tests pass, including a real DBOS engine kill/restart, two unresolved conflict decisions, a recorded resolution, acceptance of the same snapshot, exactly one observed agent launch in this laboratory, and retention of another accepted file. The initial E2E fixture mistakenly permitted the ordinary integration retry; the final fixture sets max_same_signature=1. An initial assertion used a run prefix rather than the attempt prefix and was corrected.

Focused control/composition suites: 37 tests pass. Ruff passes on new/workflow/test files; projection has two pre-existing S110 warnings (unchanged except/pass at lines 394/440); its remaining lint passes. Whitespace checks pass. sdist/wheel build passes and integration_policy.py is present in the wheel. No configured standalone Python static type checker was found or claimed. Self-review was performed by the solver; the user explicitly required working alone.

Additional history-compatibility proof: verify_legacy_upgrade.py starts the real pre-fix engine at ce5c591ed, records two conflict decisions with its old cached integration, kills it, publishes the resolution, and recovers that same history under the patched engine. It passes (19.770s), without history rewriting or another agent launch.

Full integration, main merge SHA, smoke and decision receipt: PENDING.

## Exact recorded resolutions and rule

Project D-081 records the 17 exact unions in resolution-evidence.json, published atomically into the existing composition/resolutions store. No product source was committed. The unions preserve the T7.5 role-gated home and retired classic chat, T2.55 shared session resolution and permission gates, bilingual language propagation, decoration input/authorization, the NODE_ENV correction, library selectors and working-copy handling, and refusal to delete an account with a saved project. The obsolete getAccountLanguage helper remains deleted as on the bilingual side.

The historical CG-2 document remains blocked and preserves both observations separately: the real failed-build document at the top and the self-test document under previousObservations. No passing evidence or manual attestation was fabricated.

verify_resolutions.py replays immutable commits using a disposable shared bare clone and real GitSubprocessPort. Without the new resolutions it reproduces every assigned conflict (exit 1). With them it verifies the exact reviewed contents in both orientations (exit 0). The two T2.55/bilingual folds have zero conflicts. The old SP-7/SP-8 fold still has seven other conflicting paths outside the assigned requests; the oracle proves those match the baseline and never claims that historical full tree is clean. validate_resolutions.cjs parses all 16 TS/TSX resolutions with zero syntax diagnostics and both blocked observations; verify_intent.py verifies the declared conservation invariants.

Rule: reusing an observation reuses its durable result; explicitly re-verifying a snapshot must observe integration afresh. Reuse full-file resolutions only for their exact base/ours/theirs blobs, in either orientation (methodology D-174); changed blobs require review. A later accepted surface must not be replaced by its earlier producer. Functional acceptance remains with the run's checks and composition gates.

## Decision and limitations

PENDING: recheck the live decision and answer the exact open round once, only after the system fix is integrated. No owner stage/subplan approval, product deployment, paid call or manual-provider attestation was made. No secrets were printed.

## Resolution type-check addendum

A disposable materialization of the current bilingual/T2.55 merge exposed a real additional boundary mismatch: TS2322, the synthetic local account lacked the required OwnAccountRecord.language field. Both account resolutions now set language:null, preserving cookie/browser fallback and ordinary account language preferences. The exact previous published hashes were checked before atomically refining those two resolutions; resolution-evidence.json records previous and final digests. All 17 orientation checks, syntax checks and conservation checks pass again. After materializing the required configuration, package source and JSON data inputs, the whole disposable tree passes `node .../typescript/bin/tsc --project candidate-check/tsconfig.json --noEmit --incremental false` (exit 0, candidate-typecheck-green.log empty). The earlier red check also lacked several archive inputs, separately identified as TS2307; none was hidden or treated as passing.

## Integration-regression repair (D-228)

The preceding audit-metamorfosis-2 integration was refused after its full regression, including a persistent failure of test_terminal_read_before_json_resumes_after_forced_background_stop. The same 18-test terminal suite passed in this solver's invocation context. Re-running the exact failing case with SIGTTIN inherited as SIG_IGN deterministically reproduced the prior error (terminal-ignored-red.log, exit 1). The new explicit ignored-caller regression also failed before repair (terminal-regression-red.log, exit 1).

Commit df426432 resets SIGTTIN to SIG_DFL only in the fixture child before it opens/reads the controlling terminal and covers the caller's ignored disposition, restoring it afterward. All original real stopped-state, resumed input, timeout and success assertions remain unchanged; no timeout increased and no production signal or permission policy changed. All 19 terminal tests pass (4.074s), Ruff and whitespace checks pass. Methodology D-228 records the cause and rule. The separate stage-join regression's prepared correction 82be089d7 is on the pending shutdown-race branch; this solver did not edit that worktree or silently import that unintegrated change.

Administrative trail: D-226 was allocated while checking the newly deployed reservation CLI and is unused; its reservation is retained. D-221 and D-228 identify the actual system changes.
