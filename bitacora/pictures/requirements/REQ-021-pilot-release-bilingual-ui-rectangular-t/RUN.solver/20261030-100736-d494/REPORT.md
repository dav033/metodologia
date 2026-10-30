# Solver 20261030-100736-d494 — integrated repair, late conflicts handed off

## Original trigger and origin

The original trigger was pictures:REQ-021:r26:T10.45:T10.45:d1@k1 after the cheap diagnosis failed JSON parsing. Direct read-only M6 evidence proves the underlying result had sole issue ENGINE_INTERRUPTED, aggregated as BLOCKED_ENV. Journal: startup requeued it at 09:53:19; another restart exhausted once-per-request recovery at 10:06:03. No missing resource was established. The classifier discarded the concrete cause.

## Fix and integration

D-203 preserves a pure ENGINE_INTERRUPTED review and uses existing bounded same-snapshot recovery, without another coding-agent attempt. Mixed issues, permissions and manual evidence retain their guards. Execution recovery_policy.py gates the changed workflow branch with DBOS.patch(bt-task-interrupted-reverify), preserving old history's escalation path.

D-208 supplies m6.snapshot-context/1 at read-only /run/bt-m6/snapshot.json outside writable source, generated after handoff/commit/tree validation. It contains exact snapshot/base SHAs, handoff manifest digest, canonical per-file SHA256/link records and content digest. A command can bind evidence without trusting agent HEAD or an environment/repository-provided identity. The actual attempt's legacy Git-mount lookup returned empty. Existing result schemas, cache semantics and authorization are unchanged; fresh candidate checks already declare resources and bypass pass reuse.

Only the solver worktree was edited. Code commits: 5c7d4b3e3a3c427d1c729d32e6f1a26574c03979, 3961266ef12d8272541edf7264d8cb0e02af9108, b6411acc57a731f6cb2de058de84930c4ac09d83, 5a52e556dc5f260f5a06b9b48ecae5199284c1d0. Integration exclusively through bt_integrate --staged: merge fff622890f28b8093a9a0afda9c4077d056bea1b on main, push, DBOS backup, 40-second verifier drain, engine/web restarts and passing smoke; integrator exited 0 and removed the clean solver worktree/branch. No manual integration or product repository commit.

## Checks actually run

- Store-backed two-interruption regression: red before fix, green afterward; seven restart/guard/patch tests pass.
- Control tests: 17 pass; real engine-kill restart scenarios: two pass, including two cuts with one agent launch and one additional M6 request.
- Quality module: 189 tests pass. Snapshot-context tests reproduce missing input before fix and pass afterward, including real read-only bubblewrap and workspace-spoof rejection; both rerun after number correction.
- Ruff and whitespace checks pass on changed files. Pre-integration sdist/wheel build passes; both new modules verified in wheel. No Python mypy/pyright/ty configuration found; no separate static typecheck executed.
- Final full regression: 303 files, no failures; first26 3m05s, rest277 24m56s. First earlier regression was deliberately stopped before merge for numbering correction and is INCOMPLETE, never counted as passing.
- Complete integration evidence: /home/david/.local/share/bitacora-solver/pictures/20261030-100736-d494/integration-d208.log; /home/david/.local/share/bitacora-integrate/regress/solver-20261030-100736-d494-20261030-113052/results.txt.

## Plan and original decision

The original harness had complete negative machinery but genuine Spanish guided-chat literals, oracle/readiness ambiguities and Git-only binding; identity checks also ran after fixture allocation outside cleanup. One bounded Planner amendment, with contract/cleanup clarifications, prepared T10.44 producer repairs and T10.45 identity/oracle/cleanup repairs. Roles, full coverage, captured Spanish catalogue arguments and manual NOT_RUN were preserved.

While this session waited for integration, the owner reconfirmed SP-2/SP-10 via the operator. Planner's normal freeze/join adopted r27 (hash 63de418caf9df477ccdb4bb9764577abe68985e3e10e24d522141ae48af02acf) at 11:18:57. Direct durable pointer/status confirm it. The original r26 decision was superseded; no stale answer or duplicate owner approval was sent. D-205 in frozen r27's envelope prose is explicitly corrected to D-208 in editable narrative; frozen task bytes were preserved.

## Late inbox: account-menu conflict

At 12:00 the engine queued historical and current resolution requests against r27 T2.55. Its live failure named MenuCuenta.tsx and textos-cuenta.ts on the SP-14 line. Reviewed and published eight exact recorded unions, preserving plans/ES-EN keys, language selection and permission-gated administration/roles entries. D-080 in pictures records their exact keys. resolve_additive.py reads all three blobs, reproduces the conflicted additions with git merge-file, requires empty-base independent additions and proves both sides retained. All eight TS/TSX files parse without syntax diagnostics. No generalized unsafe merge rule was introduced.

Checked current r27 T2.55:d1@k1 offered reverify; answered exactly once by solver, exit0, same snapshot. This is not a manual/provider attestation. Fresh status is now {'task_id': 'T2.55', 'state': 'needs_decision', 'request_id': 'T2.55:d2'} with reason: still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14). Its acceptance is NOT claimed.

## Remaining and continuation

There are 18 late queued triggers left UNHANDLED in deferred-triggers.json, including any newly queued d2 decision. They arrived close to the 120-minute session limit and require further causal/blob review. They are intentionally omitted from result.json handled so the engine can start the next session. Do not blindly resolve every old request: resolutions.target also falls back to the single open INTEGRATION_CONFLICT task, which can associate historical requests whose paths are absent from the current failure. That routing concern is evidenced but not repaired here.

The system repair is integrated and smoke-verified; r27 continues product acceptance. Manual configured-provider EN/ES observation remains NOT_RUN. No paid call, owner confirmation, fabricated receipt, permission/secret-scanning change or deletion of user data was performed.
