---
id: REQ-021
status: approved
created: 2026-10-15
track: standard
---
# REQ-021 — Scheduler M5/M6 runtime integration

## Authority and baseline

David's explicit active request is to execute `/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md` and ensure the
complete Planner-to-M6 path is wired and working. This requirement records that integration scope; it does not alter
the frozen M5 plan or claim its still-open T19/T20 are complete.

An isolated M6 implementation already exists in `/home/david/dev/metodologia-m6-quality` at base `8749e44`.
Its 66 package tests, one real-M3 E2E test, and six M1 boundary tests passed on the source tree during this session.
It is uncommitted, based before the current M4/M5 changes, and has no shared runtime wiring. The current integration
checkout is dirty with concurrent work; all changes outside this requirement must be preserved.

## Problem and goal

The shared scheduler can execute M5 recovery, but the existing complete-chain E2E uses a test verifier. The isolated
M6 package can verify real M3 snapshots and submit M1 verdicts, but no production composition connects it to the
current M1/M3/M5 runtime.

**Success looks like:** an opt-in runtime composition routes M1 `VerifyOrder` to M6; a deterministic local E2E proves
Planner → M1 → M2 → M3 → M6 rejection → M1 recovery → M5 recommendation → fresh M2 assignment → M3 snapshot
continuation → M6 acceptance → M1 completion. A failed check never completes the task, and `NEEDS_REVIEW` remains
pending in M1 until an explicit operator resolution.

## Users and actors

- Planner freezes and hashes the approved plan.
- M1 owns task, attempt, verification, recovery and completion state.
- M2 chooses each authorized assignment.
- M3 executes and preserves attempt snapshots.
- M4 observes when explicitly wired; it does not decide recovery or acceptance.
- M5 recommends bounded recovery through M1.
- M6 verifies the exact M3 snapshot and returns a correlated verdict to M1.

## Scope

- Selectively integrate the existing isolated M6 package and its tests into the current checkout, without importing
  M6 branch documentation whose REQ/D identifiers conflict with current M2 work.
- Add opt-in `quality_store_path` / `quality_policy` composition through the existing M1 `VerificationPort`; preserve
  caller-supplied verification when M6 is not selected.
- Bind M6 only after M1 and M3 objects exist, and close M6 workers/store before M3 shuts down.
- Keep the existing M1 contract at 1.2.0. M6 must use the established public core and executor adapters rather than
  importing `bt_scheduler_core` or `bt_scheduler_executor` directly.
- Prove the real M5/M6 interaction with a local fake provider and disposable repository. No provider credentials,
  paid CLI request, deployment, migration, install, push or global activation is part of this integration E2E.
- Re-run the M5 T19 fresh quota gate; launch its bounded live CLI experiment only if the approved two-route threshold
  passes. Do not claim T19/T20 completion if that gate remains unavailable.

## Out of scope

- Changing M1 state ownership, `VerifyOrder`, `Verdict`, schema or `submit_verdict` semantics.
- Enabling M6 globally or changing default verifier selection.
- Turning `NEEDS_REVIEW` into an implicit pass, fail or automatic retry.
- Modifying existing M1/M3 databases, M3 snapshots, `RUN.json`, provider profiles, or concurrent M2/M4 work.
- Push, merge to main, deployment, production migration, or installation into the live skill.

## Requirements

- R1. M6 consumes only the approved M1 verification order and the matching, validated M3 handoff; it runs checks in
  its isolated sandbox and stores durable private evidence.
- R2. M6 submits PASS/FAIL only through the existing M1 verdict contract. `Ack` is admission, not acceptance.
- R3. M6 `NEEDS_REVIEW` submits no verdict and leaves M1 verifying until explicit review resolution.
- R4. Supplying `quality_store_path` opts into M6. Supplying both a custom `verification` port and `quality_store_path`
  is rejected. Omitting it preserves the existing caller-controlled verifier path.
- R5. Adapter/store construction failures fail closed and clean up only resources created by the composition.
- R6. Runtime shutdown drains M6 work and closes its store before closing M3; M5 remains available for M1 recovery.
- R7. The integrated E2E uses real Planner contract loading, M1, M2 decision path, M3 executor, M5 adapter and M6
  verifier with deterministic local fixtures. It proves rejection cannot complete and a later accepted verdict can.
- R8. Package imports remain within the repository's module boundary and the Python wheel contains the M6 package,
  adapter and declared resources.
- R9. Live T19 evidence is reported separately from the deterministic E2E; a failed preflight never starts a provider.

## Acceptance criteria

- AC01. M1 `CONTRACT_VERSION` remains 1.2.0 and the public verification dataclasses are unchanged.
- AC02. Existing `VerificationPort` injection still works when M6 is not selected.
- AC03. Opt-in M6 wiring validates the approved plan/order and maps M3 repository and attempt evidence correctly.
- AC04. A real integrated E2E observes M6 FAIL → M1 `recovering` → M5 decision → new M2 assignment → continued M3
  snapshot → M6 PASS → M1 `completed`.
- AC05. Failed, stale, missing-evidence, sandbox-failure and review-required cases cannot falsely complete M1.
- AC06. Tests show shutdown and construction failures leave no M6 worker/store leak and do not close M3 before M6.
- AC07. M5 T19/T20 status reflects observed live-preflight results; no live behavior is inferred from local tests.
- AC08. Scoped tests, lint, packaging checks and `git diff --check` pass, except separately identified pre-existing failures.

## Constraints and assumptions

- Reuse the M6 package from the isolated worktree after revalidating its source tests; preserve that worktree untouched.
- No shared-core contract change is needed: the current 1.2.0 `VerifyOrder` and `Verdict` signatures match M6's needs.
- M6's store path is caller-supplied and opt-in. Bubblewrap is required for command execution; unavailable sandboxing
  remains `NEEDS_REVIEW`, never an unsandboxed fallback.
- Existing dirty M2/M4/M5 files are shared workspace state. Patch only the integration touchpoints and inspect each
  staged diff before final review; do not stage or commit.

## Priorities and phases

P1: import-safe M6 integration, optional runtime composition, real M5/M6 full-chain test. P2: package/install
boundary evidence and report reconciliation. M5 T19 stays its own required provider-quota gate under REQ-019.

## Clarifications

- 2026-10-15 owner ruling: the explicit request to wire all phases through M6 authorizes integration of the existing
  M6 verifier through the unchanged M1 `VerificationPort`; use explicit opt-in storage, keep `NEEDS_REVIEW` pending,
  and do not enable M6 globally.
