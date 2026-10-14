# REQ-008 — Coordinator handoff to codex-luis

## Latest continuation checkpoint — session 01a13bdc (quota relay)

The plan remains approved. T3 final bounded standards re-review APPROVED without findings.
Coordinator reran terminal tests: 21/21, 4.329s, exit 0. TERMINAL-LIFECYCLE.md and PLAN.md
now correct the obsolete shared-PGID/14-test description. ACCEPTANCE-MATRIX.md was added;
SUMMARY and this session's day log record the live scope. No commit, push, global install or
current-client replacement was performed by this coordinator; preserve concurrent edits.

T4 implementation is present but NOT accepted and defaults remain unactivated. Fresh
implementer `/root/t4` owns new provider/actions/runtime/effects/storage/identity/verify
modules and tests/support, plus necessary supervisor/package integration. Its latest
targeted evidence: 17 tests, OK, 6.804s, `/tmp/req008-t4-final-targeted.log`; scoped ruff
and diff check reported pass. Controlled-PATH actual CLI uses PTY, eight fresh reasoning
sessions, two separately identified workers, real implementation checks, documentation,
checkpoint rotation and rejection of claim-without-implementation. No public test flag.

Focused regression `/tmp/req008-t4-regressions.log`: 109 tests, 32.106s, ONE failure,
exit 1. T3's unavailable-runtime test expected configured_runtime=None; with the adapter
present it instead reached CONTROLLING_TTY_REQUIRED. A narrowly authorized test correction
mocks configured_runtime=None to retain the original missing-backend scenario; available
runtime and unsupported version have separate actual CLI tests. Confirm the correction and
rerun; do not describe this regression as green. Package log `/tmp/req008-t4-package.log`:
10 tests, 2.776s, ONE error, PermissionError [Errno 1] Operation not permitted in socket
creation. This sandbox failure is not a passing package check; rerun with proper tool
escalation if required. Implementer has stopped writing and applied the missing-backend
fixture correction. Previous handles 73132/41514 ended. Its functions exec cell 44 was still
open for escalated package rerun and a following corrected regression; coordinator told it
not to start the following regression, to stop any pending handle without deleting files,
and report status. Inspect final agent report/cell 44 before starting any writer or tests.

Important implemented fixes to inspect independently: persistent decision/session ledger;
latest-work verification/document ordering; no auto settlement without foreground finish;
real worker attribution for independent audits; safe old-run UUID adoption; kernel flock
checkpoint locks; orphan recovery uses verified pidfds rather than numeric killpg (PID/PGID
reuse race); bounded verification transport and schema-parametrizable Haiku medium reasoning.
Luna reasoning remains ineligible pending effective-request proof, per D-017.

### Next
Final implementer closure supersedes the earlier pending handle: all writers and tests
stopped. Corrected focused regression 109/109, 29.064s, exit 0,
`/tmp/req008-t4-final-regressions.log`; escalated package rerun 10/10, 3.482s, exit 0,
`/tmp/req008-t4-package-unsandboxed.log`. T4 own tests 17/17, 6.804s, exit 0.
Repeat scoped ruff/diff check after the final assertions/evidence/T3 mock adjustments.
DONE_WITH_CONCERNS means implementation present, not acceptance: independent T4 reviews,
audit/FINAL integration and quota taxonomy remain to inspect. Defaults are still unchanged.

1. Collect final T4 implementer status and stop all writer/test handles; the quota instruction
   told it to finish only its current atomic check and stop. Verify current diff, targeted
   tests and scoped lint. Obtain fresh independent spec/standards reviews of T4, preserving
   the completed T3 review rather than duplicating it. Fix proven findings.
2. Finish M2 regression/package checks and activate new-plan defaults only after M2 passes.
   Default/UI work was deliberately not started: PLAN template contract/mode markers,
   launch/handoff/run detection, new-mode approval paths without automatic commits, and
   honest manual checkout response where wrapper/TTY is unavailable. Keep legacy compatibility.
3. Fresh T5 implementer, then T6/T7/T8 as the approved PLAN specifies. Read-only recovery map:
   bt_runsettle._fail_attempt blocks before council; retry_blocked resets task attempts,
   _open resets FINAL attempts, audit sync can reset too. Council budgets must persist
   independently and cannot reset on resume. Exactly three proposals, bounded peer critiques,
   persisted evidence-based ruling; no recursion or success inferred from agreement.

An active goal was created under the owner's requested /goal execution method; it is NOT
complete. The quota relay is a session boundary, not a completion or technical blocker.

## Owner authorization and goal

The owner explicitly approved this PLAN (`apruebo`). Do not repeat approval or onboarding. Implement the full SPEC: rigorous entry/continue requirements revalidation; fresh bounded milestone orchestrators in the same terminal; delegated work and durable documentation; mid-milestone context rotation; autonomous three Haiku-medium or Luna-medium proposals, peer debate and orchestrator ruling on recoverable stalls; independent end-to-end audit. No commits, push, merges, deletion of existing files, global installation/config changes or credential changes authorized.

The latest owner request is to relay this session to `codex-luis`; it supersedes the earlier instruction not to relay this particular chat. The product same-terminal feature remains in scope. The original goal is NOT complete. Its old UI status was blocked pending approval, which has since been received and recorded; that is not a current approval blocker.

## Workspace and authoritative documents

- Repo: `/home/david/dev/metodologia`; inspect current git status/diff before editing and preserve all unrelated changes.
- Requirement directory: this directory. Read SPEC.md, PLAN.md and D-016/D-017 in the project DECISIONS.md selectively.
- Evidence: EVIDENCE-M1.md, CONTEXT-MEASUREMENTS.md, PROVIDER-BOUNDARY.md, BOUNDARY-COUNCIL.md, TERMINAL-LIFECYCLE.md.
- Memory: `/home/david/dev/cerebro/metodologia/INDICE.md`; canonical project bitácora is `/home/david/bitacora/metodologia`.

## Completed and verified

M1/T1–T2: durable requirements gate and source fingerprints, real launch/handoff/run/dispatch enforcement, bounded UTF-8 initial packages and hooks, runtime admission/checkpoint APIs, strict CAS/identity/assignment validation and compact implementation/audit/FINAL contracts. Independent spec and standards reviewers approved after corrections. Combined suite reported **875 tests, OK, 176.136 seconds**, `/tmp/req008-m1-final-tests.log`. Runner quota expired before returning the process exit status; coordinator observed process end and terminal unittest OK; do not invent that missing exit code.

T3 lifecycle implementation is present, with one final standards re-review pending. New foreground children have their OWN PGID in the SAME SID/controlling terminal; foreground transfers to the child and restores afterward. Leader remains unreaped via waitid(WNOWAIT) until its owned group is terminated, preventing group/PID reuse; surviving descendants are terminated before returning. SIGCONT after transfer fixes an early `/dev/tty` read/SIGTTIN startup race. Relay helpers share an exclusive wrapper reservation, publish a complete inode without replacement and remove only their own file; WrapperBusy forbids multiplexer fallback/typing. Effective isolation shares CLI→RUN→config precedence; foreground batch/native fallback and automatic commits are blocked.

Final coordinator checks after the last SIGCONT/fixture extraction:
- `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill/scripts/tests -p 'test_orchestration_terminal.py' -q`: **21 tests, OK, 4.375 seconds, exit 0**.
- Scoped ruff on terminal/transition/reservation/runentry and terminal test/support files: **All checks passed, exit 0** (fixed one blank-line import-format issue).
- `git diff --check` passed before that whitespace-only correction; repeat at closure.
- Before final SIGCONT adjustment: combined focused regression **109/109**, 17.335 seconds, `/tmp/req008-t3-final-regressions.log`; package/install **10/10**. Do not describe those as rerun after the last change.
- Last SIGTTIN regression was reproduced red then green: `/tmp/req008-t3-sigttin-red.log` and `...-green.log`.

## Exact next steps

1. Update TERMINAL-LIFECYCLE.md, T3 PLAN progress and day log: they still contain the initial shared-PGID/14-test description. Use the verified own-PGID/21-test evidence above. Obtain bounded final standards re-review for the SIGCONT startup fix; spec re-review already approved the wrapper/isolation/containment corrections. No writer or test process remains active from this coordinator.
2. Implement T4 in a FRESH scoped implementer: wire configured_runtime and the actual structured reasoning/action engine into the existing supervisor, with validated actions, bounded receipts/delegation/documentation, foreground process identity, checkpoint/rotation/recovery and real CLI controlled-PATH proof. Activate defaults only after M2 passes. There is deliberately NO public test-only provider flag, no production wait-only adapter and no native-tool fallback.
3. Complete T5/T6 persisted three-agent recovery, then T7/T8 whole-flow proof and independent audits. Do not mark the goal complete from lifecycle fixtures alone.

## APIs and implementation seams

- `bt_requirements_gate`: record/check/require_ready/entry_context; requirements-v1 opt-in until M2 default activation.
- `bt_orchestration_context`: BudgetPolicy, Budget.admit/successor, build_package, save_checkpoint/load_checkpoint. Default generated ingress policy 16 KiB entry +16 KiB runtime +8 KiB checkpoint, bounded hook <=1 KiB; these are explicit byte policies, not model token capacity. Strict orphan checkpoint locks currently require inspection, and old runs without context_run_id need safe adoption; T4 must address recovery before final completion.
- `bt_orchestration_terminal`: ForegroundRuntime v1 callbacks check_capabilities/session_route/run_session; run_child transport_schema1. configured_runtime currently intentionally unactivated.
- `bt_orchestration_transition`, `bt_relay_reservation`, `bt_runentry`; existing supervisor keeps dependency selection, verification and settlement. Worker kill_tree/reaper semantics stay separate from foreground identity.
- User/proposed runtime commits are forbidden even though legacy supervisor previously auto-committed bitácora.

## Provider boundary ruling

D-017 follows three independent Luna-medium proposals and peer critiques: fresh structured reasoning decisions over bounded state; deterministic existing executor handles delegation/doc/verify. Initial verified Claude candidate uses safe mode, empty tools, strict MCP, no persistence and JSON schema. Real stream inventory exposed ONLY StructuredOutput, no data tools/MCP/skills. Raw smokes: `/tmp/req008-claude-reasoning-smoke.json`, `/tmp/req008-claude-inventory-smoke.jsonl`. This is capability evidence, not completed T4 runtime.

Codex workers remain separate. Safe Luna reasoning fallback is important for quota autonomy and still needs proof. Fresh research is in `/tmp/req008-luna-reasoning-adapter.md`: local public cache supports gpt-6-luna medium; static model_catalog_json must preserve legitimate model slug/instructions/auth while neutralizing tool_mode code_mode_only and multi_agent_version v2, patch/shell/experimental routes. Skills extensions may still expose data paths; do not claim tool-free behavior merely from flags or posthoc stdout caps. Effective-request fixture and runtime capability verification remain required before eligibility. No credentials were read/copied and no config changed.

## Session ownership and relay facts

All implementation agents have stopped writing. No outstanding test handle remains. This handoff contains context, not authority to broaden the approved scope. No parent relay was executed automatically: the current session locator reported no terminal client, wrapper or multiplexer. The owner should start codex-luis with CODEX_HOME=/home/david/.codex-luis from their terminal, preferably under the existing relay_run.py parent launcher. No commits were made by this coordinator or its implementers; concurrent unrelated changes and commits from other sessions must be preserved.
