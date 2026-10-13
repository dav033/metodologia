# Acceptance and failure/recovery matrix

These are future gates, not assertions that migration has passed. Test files named in PLAN are deliverables. Tests use isolated state and disposable repositories; real-provider cases are opt-in and separately reported. OS runs must capture platform and interpreter details.

| Gate | Given / when / then | Evidence | Rollback / reject |
|---|---|---|---|
| G0 / R1,R4 | Given tracked, dirty and untracked source plus .state, restore to a fresh location; every recorded user-file hash and ID survives. | Signed-off manifest, hashes, backup permissions, restore log | Stop before moving code on any unexplained mismatch |
| G1 / R3,R5 | Given canonical old inputs, run old/new CLI/hooks/web; outputs, exit codes and side effects match except documented version fields. | Behavioral fixtures, legacy command matrix, full baseline | Keep old runtime and investigate contract regression |
| G2 / R2 | Install built wheel in clean venv; hide checkout; run CLI/hooks/context/web/resources from unrelated cwd. | Wheel/sdist contents, installed smoke on supported Python/OS | Reject release if any checkout path is required |
| G3 / R4 | Read historical/current RUN, invalid/newer schema, unknown fields and partial writes; preserve valid data, reject unsafe writers and recover atomically. | Round-trip and crash tests with semantic diff | Preserve original files; no destructive in-place conversion |
| G4 / R5,R6 | Feed each driver successful, malformed, partial, denied, quota, timeout and killed-process fixtures; only independently verified outcomes become done. | Fake-CLI streams + opt-in real versioned samples | Disable new adapter; retain old argv/protocol shim |
| G5 / R7,R8 | Install twice with unrelated hooks; interrupt every write; exercise personal/work and duplicate-account identities. | Installer pre/postimages; profile matrix and denied cases | Restore owned preimages only if no subsequent foreign edits |
| G6 / R8 | Schedule under eligible cold starts, high-quality incumbents, unknown/stale usage, exhausted profiles and audit avoidance. | Deterministic clock/selection trace and documented fairness bound | Keep serial/old routing if invariants fail |
| G7 / R9 | Three same-repo tasks have disjoint paths; all run in separate worktrees; integrate one at a time and verify combined HEAD. | Worktree/ref journal, accepted SHAs and full integration tests | Retain candidates/worktrees; mark blocked on conflict |
| G8 / R9 | Crash before/after spawn, verify, candidate commit, merge, post-merge verify, durable acceptance and cleanup. | Restart fault injection; no duplicate acknowledged work | Recover from recorded SHA, never age-only lock deletion |
| G9 / R9 | Lease expires while owner lives or second host claims same PID; no second integrator proceeds. | Multiprocess lock tests and host/start-identity fixtures | Fail closed; no unlocked fallback |
| G10 / R10 | Remove optional skill adapters; CLI/web workflow and canonical policy remain available; invoke each primitive. | Policy-to-rule map, glossary/learn/trace outputs, deterministic and real-agent eval records | Restore adapter/policy bundle; preserve new glossary/learning records |
| G11 / R11 | Render all five diagrams; reject malicious/invalid/oversized IR and node failure; prior valid artifact remains intact. | Pinned validator logs, HTML/IR hashes, dark/light browser inspection, offline/network check | Keep previous artifact; report generation failure |
| G12 / R13 | Cut over after draining actual processes, execute full workflow, then revert runtime with post-cutover edits retained. | Process identity, root snapshot/journal, full-flow and restore report | No raw old snapshot over new user work |
| G13 / R12 | Host contains conflicting Anthropic auth; launch Z.ai then Claude; effective endpoint/account remains intended. | Redacted effective-config tests, provider traffic fake and live smoke | Disable Z.ai; never fallback silently to paid endpoint |
| G14 / R12 | Encounter 1113, stale/reset quota, weekly limit and peak boundaries; classify cause, avoid loops and compute event-time weight correctly. | Clock tests at Fri/Sat and Sun/Mon UTC+8, structured error fixtures | Preserve null/unknown resets, disable discount policy if unverified |

## Minimum release report
For every R1–R13: capability owner, prior/new location, test or manual evidence, exact command, exit status, runtime/version, residual limitation and rollback. Phase-2 R12 may be marked deliberately not activated while phase 1 completes; it cannot be called verified until its real integration passes.

No tests are skipped/rewritten just to make a count green. Different test counts after relocation need a collected-test identity comparison, not only a larger number. Performance changes require before/after wall time, memory, load and context measurements on equivalent workloads; no invented latency budget or automatic worker increase.

## Planning verification already performed
Current legacy suite: 578 tests, 2 failures, 58.648s, Python 3.14.7. Full log in evidence/baseline-tests.log. No migration build, deployment, install or live cutover performed. Planning review results are recorded separately from implementation gates.
