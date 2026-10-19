# Actual M1 → M2 → M3 isolated smoke

Owner request: “probemos el flujo con m3”. Decision D-074 adds explicit no-commit patch handoff; default snapshot remains compatible.

## Result
PASS. Frozen technical REQ-M3 (not the Pictures product plan), one native task and one unexecuted successor sentinel. Real M1 authorization → real M2 quota-aware assignment → actual M3 AgentExecutor, native CLI, supervisor, workspace, ledger and technical event delivery. M2 selected claude-work / Sonnet / medium; native output reports claude-sonnet-5-5. Effort is requested, not independently attested by provider output. Native exit0 after approximately20 seconds.

T1 implements tag normalization in two standalone ES-module files. Agent-authored10 tests and parent-independent7 tests pass. The 3,185-byte schema2 binary patch was reapplied to a fresh detached worktree at the pinned base; both files are byte-identical, and both suites pass there too. SHA256: `3789f0d645cab08c4ff8a872fea6378fd8adc0138180eee211ec677362e5d0fa`. Final-source recapture after the audit correction produces the same hash.

Actual external verdict applied to real M1: T1 completed/accepted, one attempt; T2 ready, zero attempts; run deliberately paused. No success was manufactured from the agent's claim.

Git HEAD unchanged at `5f9104980d31e0074c6bbb5ed16cae1e8c92a723`; reachable commit count1133 before and after. Patch capture creates no commit/ref; child hooks disabled and child Git mutations guarded. Original Pictures code was not edited. Existing source objects were cloned; no new fixture commit was created for this live smoke.

## Implementation review
Independent spec APPROVE. Standards initially found omitted ignored-but-tracked files when HEAD differs from base; fixed by seeding the isolated index from HEAD. A regression restores such a binary from base. Final standards APPROVE. Final affected tests: handoff23, README6 pass. Prior final targeted checks: contracts15, prompt1, boundaries8, hardening28 pass. Full-suite/check results are recorded separately as available; an earlier286-pass suite predates compatibility fixes and is not final-source coverage.

## Limits
This proves the isolated happy path and independently verified patch restoration. It does not implement Pictures recommendations or execute its T2, prove the full production fault matrix, or opt into M4/M5/M6. Review and verdict are caller-owned. Patch-only handoff is not automatically integrated into successors; integrate_predecessors=False is explicit. No deployment, commit or push. Global automatic VCS issue P-118 remains separate.

Runtime (including raw model output, not copied here): `/home/david/bitacora/pictures/.state/m3-flow-xm9hnyg1`.

Build: NOT PASSED. `python -m pip wheel` could not start (pip absent); `uv build --offline --no-build-isolation` failed because setuptools is absent in this interpreter. No environment/dependency changes made.

Final-source adapter integration:21 tests pass (77.038s). Scoped Ruff for config/handoff/prompt and new handoff/prompt tests passes after import ordering correction.

Expanded Ruff reports7 pre-existing findings confirmed against HEAD:3 BLE001 in settle/spawn and4 C408 in contracts tests. The sole introduced import-order finding was corrected; changed capture/config/prompt and new handoff/prompt tests pass Ruff. No checks were weakened.

Module-wide run:287 tests pass in270.627s, exit0. It started before the final HEAD-index correction; do not treat it as full final-source coverage. Final corrected capture is covered by handoff23/README6, final-source identical live recapture,21 adapter integration tests and both independent audit approvals.
