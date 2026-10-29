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
