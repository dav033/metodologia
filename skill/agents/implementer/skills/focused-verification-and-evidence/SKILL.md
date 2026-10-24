---
name: focused-verification-and-evidence
description: Provide task-local focused evidence for implementation changes without taking ownership of the Runner, Scheduler or independent acceptance cycle.
---

# Focused verification and evidence — Implementer private skill

## Trigger
Use for a task that requires local red/green/regression evidence. The Implementer checks its own work; Runner executes independent long/noisy checks; M6 decides acceptance.

## Procedure
1. Map each actual acceptance criterion to the smallest existing effective test/check. Include required repo guards. Do not use file existence as behavior proof.
2. For new logic or a bug, where feasible prove the test fails against the original behavior; then implement and run targeted proof. Don't weaken/delete tests to make them pass.
3. Record exact command, cwd, task ID, `subplan_id`, `subplan_revision`, `base_sha`, snapshot SHA, verification ID,
   exit code and decisive assertions when supplied by the brief. Passing local tests does **not** imply integration
   or production acceptance.
4. If missing credentials, a privileged environment, blocked network or unsupported permissions prevent the check, label it a blocker with required secret **names only**. Do not alter application code to satisfy a broken sandbox.
5. Leave cross-subplan smoke, full-suite scheduling, retries, verdict publication and evidence reuse policy to M1/M5/M6/Runner.

Until the result schema migrates, keep the existing `STATUS` vocabulary. Put reason labels such as
`BLOCKED_EXTERNAL`, `BLOCKED_ENV`, `FAIL_CODE`, `FAIL_INFRA_UNCONFIRMED`, `TIMEOUT`, `FLAKY_SUSPECTED` and
`NOT_RUN` in notes only; they are evidence reasons, not statuses or verdicts.

## Stop condition
End once the approved task change and required local verifications are complete, or return a precisely evidenced blocker. Do not expand to a full development cycle.
