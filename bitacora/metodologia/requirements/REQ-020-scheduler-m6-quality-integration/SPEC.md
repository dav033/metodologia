---
id: REQ-020
status: done
created: 2026-10-15
track: standard
---
# REQ-020 — Scheduler M6 Quality & Integration

## Authority and baseline

David explicitly requested implementation and independent verification of the complete proposal in
`/home/david/PLAN-FASE-6-M6-QUALITY-INTEGRATION-PROPUESTO.md` on 2026-10-15. This is the approval gate for this
scope. The proposal remains the source for T01–T20, Q01–Q20 and M6-AC01–M6-AC13; no item is removed here.

The implementation is isolated on `feat/scheduler-m6-quality`, based on `8749e44`. The authoring worktree has
uncommitted M4/M5 changes and is outside this requirement. Reference suites passed: M1 239/239 and M3 272/272.
The final implementation evidence is recorded in [`REPORT.md`](REPORT.md).

## Problem & goal

M1 correctly keeps an attempt in `VERIFYING` after M3 reports `execution_finished`, but the independent
`VerificationPort` has no M6 implementation. Build that verifier as an isolated module that checks the exact
approved order against M3's preserved snapshot, returns durable evidence and submits a correlated M1 verdict only
when the evidence supports PASS or FAIL.

**Success looks like:** no agent exit status or report can complete a task; an executed mandatory check failure
cannot pass; insufficient or unavailable evidence stays pending for explicit review; recovery after restart is
idempotent; the source checkout, M1/M3 stores, unrelated attempts and production systems remain untouched.

## Users / actors / stakeholders

- M1 Scheduler Core: owns state and accepts only its existing `Verdict` contract.
- M3 executor: owns execution, handoff snapshots and repository/base provenance.
- M6 operator: inspects durable results and resolves `NEEDS_REVIEW` explicitly.
- M5: may later consume an M1 rejection; M6 does not request recovery or retry work.

## Scope (in)

### US-1 — Verify the exact attempt independently

Validate plan/revision/task/attempt/token, idempotency key, approved criteria and checks; resolve only the matching
captured M3 handoff; verify its snapshot and base provenance; never treat `report.json` or exit code 0 as proof.

### US-2 — Run deterministic checks safely

Run only checks carried by the M1-approved `VerifyOrder` or an explicit project policy. Use an ephemeral copy of the
snapshot, no shell, no host home, no inherited secrets and no network. Require an effective OS sandbox; if bubblewrap
is unavailable or cannot isolate the process, record `NEEDS_REVIEW` without running the check. Bound wall time,
concurrency and captured output; terminate timed-out process trees.

### US-3 — Evaluate criteria conservatively

Use the approved verification `purpose` as the explicit mapping to an acceptance criterion; the purpose must equal
the criterion text. A missing mapping, a `manual` check, an ambiguous result or an unavailable resource is
`NEEDS_REVIEW`. A completed command with a non-zero exit is `FAIL`; timeout or sandbox/setup failure is
`NEEDS_REVIEW`. PASS requires every criterion to be covered and every mandatory check and integration guard to pass.

### US-4 — Keep evidence durable and deliver verdicts safely

Persist orders, results, review items and verdict outbox entries in an M6-owned SQLite WAL ledger. Use a stable
verdict ID and replay the stored result on duplicate requests. Evidence manifests and bounded logs are private
local artifacts with hashes, snapshot/base SHA, criteria/check hashes, verifier/policy version, timestamps and real
exit codes. Redact explicitly configured secret values before storing output. Submit the verdict only through
M1's existing `submit_verdict` path; `Ack` means the request was durably accepted, never that it passed.

### US-5 — Exercise integration and restart behavior

Use M3's public attempt description and handoff. Check that the captured handoff's `base_sha` matches M3's pinned
workspace base and is an ancestor of the handoff snapshot. M3's `PredecessorIntegrator` remains the sole owner of
predecessor composition and conflict detection; M6 does not recompute or write its refs. Provide deterministic
end-to-end tests with M1, M3 fixtures and a simulated M5 recovery port.

## Out of scope

- Changing M1 states, DAG, persistence, `VerifyOrder`, `Verdict`, or ownership; adding a third M1 verdict state.
- Launching work, changing plans, recovering/retrying, resolving merge conflicts, or modifying M3 snapshots.
- Automatic AI audit, live provider calls, paid evaluation, deployment, production migrations, push or merge.
- A dashboard or a second general defect/telemetry system.

## Requirements

- R1. A valid request is bound to its exact plan, revision, task, attempt, token and idempotency key. Reuse of a key
  with different content is rejected without executing checks.
- R2. The verifier resolves a captured M3 handoff whose attempt ID, repository, snapshot SHA and base SHA validate;
  missing, malformed, stale or substituted provenance cannot PASS.
- R3. Verification runs on a copied immutable Git snapshot in an OS sandbox. It cannot access the source checkout,
  host home, network or unapproved environment variables. Sandbox failure prevents command execution.
- R4. Commands come only from the approved order/policy, are parsed to validated `argv` and a workspace-contained
  `cwd`, and run with bounded wall time, process cleanup and output/disk limits.
- R5. Every acceptance criterion has explicit evidence coverage. `purpose` equals the exact criterion text; manual,
  uncovered or ambiguous criteria are unknown, never PASS.
- R6. PASS requires every required check and provenance/integration guard to pass. A completed non-zero check is
  FAIL. An unrun, timed-out or inconclusive check is NEEDS_REVIEW.
- R7. M6 maps only PASS to `Verdict(accepted=True, evidence!="")` and FAIL to `accepted=False`. NEEDS_REVIEW does
  not emit a verdict or change M1; it remains in M1 `VERIFYING` until an explicit operator resolution.
- R8. A review resolution records the operator identity, decision and rationale, creates an idempotent verdict, and
  enters the same durable delivery outbox. No timeout silently accepts, rejects or consumes M5 retries.
- R9. Crash after result persistence or after M1 submission can be reconciled by replaying the same verdict ID;
  duplicate requests do not execute the checks twice.
- R10. The evidence manifest survives restart, is hash-verifiable and correlates to the exact M1/M3 attempt. Logs
  and storage are private; secrets are not written to normal logs or manifests.
- R11. Integration verification uses M3's recorded base and snapshot; predecessor conflicts remain M3/M1 failures.
  M6 never updates source refs, merges, pushes or modifies an author checkout.
- R12. Independent attempts use unique ephemeral paths and bounded concurrency; one failure does not block unrelated
  DAG branches.
- R13. Optional independent human/agent review must be explicit and use a separately identified reviewer. It is
  disabled by default; absent identity/evidence remains NEEDS_REVIEW. No provider is invoked implicitly.
- R14. Missing audit/defect counts are `unknown`, not zero. M6 reuses existing quality/audit surfaces where they fit
  and does not duplicate the global metric or defect system.
- R15. M6 has no import dependency on M1, M3, M5 or legacy Bitácora modules. Only its adapter translates existing
  external contracts. M5 remains independently usable through its simulated recovery port.

## Edge cases & errors

- Obsolete plan/revision/token or replaced attempt: do not run against another attempt; retain a stale result and do
  not submit it as the current attempt's verdict.
- M3 handoff missing, snapshot absent, invalid SHA, corrupted artifact or source repository unavailable:
  NEEDS_REVIEW with a stable diagnostic; never infer success from an agent report.
- Same idempotency key/same canonical input: replay stored state. Same key/different input: reject.
- Required binary/dependency missing, bubblewrap unavailable, command timeout, evidence-store failure or process
  output cap reached: record the operational fact; do not fabricate PASS. Storage failures remain retryable and do
  not emit a verdict.
- M1 unavailable after a verdict is persisted: retain the outbox row and retry on explicit reconciliation.
- M1 says duplicate: mark delivered. M1 says stale/invalid: record the response and do not rewrite M1 state.
- A task whose criteria require a live deployment or production migration cannot be verified here; no production
  credential, socket or network is exposed. Require explicit human review.

## Constraints

- Preserve `bt_scheduler_core` contract 1.1.0 at the M6 branch base and the eventual shared M1 contract unchanged.
- Keep `bt_scheduler_quality` standard-library-only; bubblewrap is an existing optional OS executable required for
  actual command execution, not a Python dependency. Default failure mode is closed.
- Run M6 in a separate Git worktree from the current dirty M4/M5 work. Do not alter user changes, M1/M3 data,
  snapshots, branches, production state or installed skill files.
- Use no real provider credentials, network, deployments, production database or migrations in verification.
- The M6 branch remains local and uncommitted; no push or merge is authorized.

## Priorities & phases

All M6-H0 through M6-H4 tasks and Q01–Q20 from the source proposal are in scope. H0 freezes the observed contract
and the policies above; H1 builds the deterministic core; H2 builds integration/evidence; H3 adapts M1 and crash
recovery; H4 proves the package end to end and reports actual results. No lower-priority proposal is silently
substituted for a required task.

## Timeline & dependencies

M1 and M3 are required and present at the branch base. M5 is not required; use a RecoveryPort simulator. The work is
sequential within this branch because it must preserve a single-owner boundary and this session has no authorized
delegation. M6 package implementation can be reviewed independently before any later common wiring.

## Assumptions

- David's direct implementation request approves the complete referenced proposal despite its original `PROPUESTO`
  label. This records approval; it does not authorize push, merge, deployment, external provider use or production
  changes.
- Bubblewrap user namespaces are available locally. If the preflight contradicts this, keep code fail-closed and
  report actual command verification as blocked/NEEDS_REVIEW rather than claiming isolation.
- The M1 plan's `verification` object is the authority for command and purpose. Existing orders without exact
  criterion mapping conservatively remain in review until a compatible, approved plan is authored.

## Coverage

| Topic | State |
|---|---|
| Goal & problem | Agreed by explicit implementation request |
| Users / actors | M1, M3, M6 operator; M5 via M1 |
| Scope | Complete M6 proposal, T01–T20 and Q01–Q20 |
| Out of scope | M1 contract changes, M5 recovery, AI-by-default, production actions |
| Flows & behavior | PASS/FAIL submit M1 verdict; NEEDS_REVIEW remains VERIFYING |
| Edge cases | Explicit in R1–R15 and error cases |
| Acceptance criteria | M6-AC01–AC13 in source proposal; mapped in PLAN.md |
| Constraints | Isolated worktree, bubblewrap, no credentials/network or production state |
| Priorities & phases | H0–H4 in order; no scope reduction |

## Clarifications

No additional owner round is needed: the referenced proposal and the explicit implementation request define the scope.
Conservative operational rulings are recorded in REQ-020 PLAN.md before the code that depends on them.
