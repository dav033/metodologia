# REQ-021 on the durable runtime: two verifier defects found live (2026-10-28 22:39–23:40, session metodologia-6d)

## T2.7 (SP-2 visual audit): the engine-owned ledger check ran in the product sandbox

- Live: T2.7 a1 escalated `BLOCKED_EXTERNAL` ("a declared resource or tool is missing"); M6 verdict `NEEDS_REVIEW`
  `CHECK_UNAVAILABLE`, output `M6_SETUP_ERROR:EXEC` for `bitacora.py audit-ledger check .evidence/REQ-021/SP-2.visual.findings.json`.
- Cause: the legacy owner wraps its sandbox runner in `quality_audit_evidence.EvidenceRunner`, which answers that
  command from the engine (`bitacora_platform.quality_ledger_command`); the durable verifier ran it in the product's
  sandbox, where no bitácora code exists. Every audit of REQ-021 (T1.8, T1.8b, T2.7, T2.8, T3.15, T14.5, T14.6) uses it.
- Fix `992d1706d`: `adapters/m6.EngineCommands`. Test `test_the_audit_check_is_the_engine_owned_ledger_contract`: red
  on `main` (the run waits on a decision), green with the fix.
- Separate from the fix: the auditor itself reported "BLOCKED, not a pass" (no candidate runtime, no screenshot
  mechanism) with an empty ledger; the gate reads only the ledger, so a `reverify` would have passed an audit that
  audited nothing. Owner answer chosen: `retry_with_note` authorizing the repository's own UI harness as the candidate
  runtime and Playwright Chromium for captures (note text: scratchpad `T2.7-note.txt`, copied into the answer).

## T3.11: Chromium's software WebGL could not start in the sandbox (every attempt, both runtimes)

- Live: legacy att-0094 and durable a1–a4 all failed `npx tsx scripts/test/test-glb-todos-los-tipos.ts` with
  `THREE.WebGLRenderer: A WebGL context could not be created ... BindToCurrentSequence failed`; owner `reverify` of a4
  failed the same way (deterministic). The agent's own runs passed.
- Bisection (all real, read-only for the bitácora):
  1. an M6-like `bwrap` (same flags, same rlimits: data 12 GiB, nofile 1024, nproc 4096) with the same snapshot and
     Chromium flags: WebGL works, the real check passes;
  2. the real M6 `SandboxRunner` with the live operator policy: fails; Chromium's stderr (`DEBUG=pw:browser`) shows
     `eglInitialize SwANGLE failed ... Internal Vulkan error (-3)` and "Exiting GPU process";
  3. inside the real M6 the environment carried the operator's session (`verifier.inherit_env: ['*']`), including
     `VK_DRIVER_FILES=/usr/share/vulkan/icd.d/intel_icd.json` from the Hyprland session: the Vulkan loader loads only
     the host's Intel driver (no `/dev/dri` in the sandbox) and never SwiftShader;
  4. the M6-like `bwrap` with only `--setenv VK_DRIVER_FILES …` added: `NO WEBGL`; without it: `WebGL 2.0`.
- Found on the way: the same inheritance put the engine's `BT_DURABLE_DATABASE_URL` (with its password) into every
  product check of the durable runtime.
- Fix `a6174efa7`: `adapters/m6.sandbox_policy` drops `BT_DURABLE_*`/`DBOS_*`, the service manager's per-unit names and
  the host session's device/socket names from the inherited environment (explicit operator variables kept).
  `test_durable_m6_env` (real sandbox, with a negative control). With the fix the real T3.11 check on the a4 snapshot
  (`1906e83b`) passes through the real M6 runner (exit 0, 314 s, every element `[PASS]`).
- Not changed: the legacy runtime's verifier (`bt_verifier_env.ambient_for_run`) inherits the same names; its WebGL
  checks fail the same way (att-0094). Proposal for the owner: the same filter there, or narrow `verifier.inherit_env`.

## T3.12: a cross-subplan conflict on the run line that no retry could fix (00:16)

- Live: T3.12 (SP-3) a1 passed its checks, then `INTEGRATION_CONFLICT` "conflicts with accepted work in: package.json";
  the single attempt had used the task's token budget (8.8 M input tokens, mostly cached), so the runtime asked the owner.
- Both sides appended npm scripts at the end of `scripts`: T3.12 the `taller:*` entries (on the SP-3 line), SP-2's
  T2.x the `cuentas:*` entries (on the run line). A retry starts from the SP-3 line again, so it would conflict again.
- Reference: in a 1.3.0 legacy run the integration line IS `bt_integration_line.SubplanLineRouter` (wired in
  `bt_scheduler_executor_wiring`): a member goes only into its subplan line and subplans meet at a composition gate.
  The durable integrator (item 1) also merged every member into the run line and failed on that merge.
- Fix `ae9665a76`: a member counts once its subplan lines take it (one transaction, as before); the run line takes it
  when it merges cleanly, otherwise the `run_line_conflict` event is emitted inside the `bt.integrate` step (no change
  to any workflow's step sequence). Tasks without subplan lines keep the fatal conflict. E2e
  `MembersAcrossSubplans`: red on `main` (the run waits on a decision), green with the fix; `test_durable_subplans` 9/9.

## SP-3 completed, and a run that ended blocked could not be continued (00:53–01:01)

- T3.12 a2, retried with the operator's note to restore its own a1 work, was accepted in one minute (SP-3, with the
  `run_line_conflict` event for package.json); T3.13 likewise; T3.15, the SP-3 audit, was judged by the gate and
  passed (`audit_passed`, 01:00). Every remaining task depends on T2.7.
- With only blocked work left the run workflow ended (`SUCCESS`, summary `blocked`). A `retry-task` sent to it would
  never be read: the procedure given to the owner for T2.7 could not continue the run (in the legacy runtime a blocked
  run stays open for the owner).
- Fix `f0df69300`: `Client.reopen` forks the ended incarnation at its last summary event into `bt:<run>@N` (DBOS
  `fork_workflow` with a chosen id); the fork replays the history and, behind `DBOS.patch("bt-run-reopened")`, waits
  for the owner's command instead of ending; `Client.command` reopens before a `retry_task`; status, commands and the
  panels' projection follow the current incarnation. E2e `test_durable_reopen` (2).
