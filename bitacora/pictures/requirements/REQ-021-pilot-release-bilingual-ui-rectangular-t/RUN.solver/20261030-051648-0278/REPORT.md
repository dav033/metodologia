# Solver report — 20261030-051648-0278

## Trigger and origin

Run `pictures:REQ-021:r25` rejected composition CG-9/C6 at 04:38 UTC, with no task decision. Two immutable three-way text conflicts waited for a recorded resolution:

- `4378ebb94f72d6922c89d601ee5db484`: `src/components/tres-d/Biblioteca.tsx`.
- `cacb3537cd9925be000ff500ae8a572c`: `src/components/tres-d/Taller3D.tsx`.

SP-8 translated the interface and threaded language through the Taller. SP-9 additionally supplies translated product/decoration names through context, applies them to the library/products, and extends the Taller props/provider. Direct comparisons of the six exact blobs show that SP-9 retains SP-8's changes. Its replacement expression/signature lines are not a textual subsequence, so the conservative D-172 rule appropriately leaves a conflict for semantic review. Retrying an implementation task could not resolve it.

## Fix and live result

Selected the SP-9 side of every conflicting hunk while retaining all nonconflicting merged text. Asserted that both complete merged files equal the inspected SP-9 blobs, rather than discarding unexamined file-level changes. Published the complete files atomically to:

- `/home/david/bitacora/.state/durable/composition/resolutions/4378ebb94f72d6922c89d601ee5db484.resolved` (Biblioteca blob `e8730cad9bc8af6d0356dded08e957cd2de7cb3d`).
- `/home/david/bitacora/.state/durable/composition/resolutions/cacb3537cd9925be000ff500ae8a572c.resolved` (Taller blob `00a49fb94c211e83626bb1579a0bb14c7b93d35c`).

The documented `bt-durable retry-task pictures REQ-021 T99 --note ...` command (request `f07565ff9aab46a69b59168405b8aeae`) cleared the rejected gate. Telemetry confirms `gate_recompose` then `gate_composed`, candidate C7, no conflicts, commit **`8eac39c768bbf05a0afbee29270d81af508391ab`**. Both C7 files match the published resolutions byte-for-byte. T99 started as `pictures-REQ-021-r25-T99-a1-7a5a0059`; the final status has no rejected gates or open decisions.

No source edits, solver commits, main merge, deployment, or methodology integration were necessary. The product work remains in the run's candidate and its normal verification/integration lifecycle; it is not claimed to be on main. Unrelated changes in the personal pictures checkout were untouched.

## Verification and reusable rule

Evidence directory: `/home/david/.local/share/bitacora-solver/pictures/20261030-051648-0278/evidence`.

- `/home/david/dev/metodologia/.venv/bin/python /home/david/.local/share/bitacora-solver/pictures/20261030-051648-0278/verify_resolutions.py`: exit 0. Real GitSubprocessPort reproduces exactly the two conflicts without resolutions; with proposals it reports no conflicts in both side orderings, preserving the exact reviewed blobs and both translation layers. `resolution-validation.json` records the inputs and tree.
- `/home/david/dev/metodologia/.venv/bin/python -m unittest discover -s /home/david/dev/metodologia/skill/scripts/tests -p test_compose_conflicts.py -v`: 20 tests, OK, 1.517 seconds; full log in `composition-tests.log`.
- TypeScript `transpileModule` on both proposed TSX files: zero syntax error diagnostics, exit 0. This is syntax validation, not application typechecking.
- GitSubprocessPort with the live resolution directory: no conflicts, tree `42b883a6d3fa9a392df422551b3c94d51817ff0b`.
- C7 blob verification: both exact resolutions present; `candidate-validation.json`.
- Live status before/after retry and at closure saved as JSON. Inbox empty at closure.

**pictures D-077** records the reviewed semantic union and the rule: preserve both interface-language and catalog-name propagation. The existing content-keyed D-160/D-174 resolution guard reuses this fix for these exact three blob versions, including reversed sides; changed contents require review. Existing regression tests cover reuse/reverse ordering. No broader automatic merge rule was introduced.

## Decision and remaining work

There was no open decision before the retry or at closure, so no `answer` call was made. The CLI records the documented retry command as `by: owner` by default; it did not confirm a subplan, approve a stage, or accept a candidate for the owner.

T99's functional integration verification remains running under the durable engine. Full product lint, application typecheck, build and browser verification were not run in this resolution-only session; no pass is claimed for them. The run owns functional acceptance and later integration to main. No new requirement or owner question was needed.
