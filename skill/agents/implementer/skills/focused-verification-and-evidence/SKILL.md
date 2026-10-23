---
name: focused-verification-and-evidence
description: Provide task-local focused evidence for implementation changes without taking ownership of the Runner, Scheduler or independent acceptance cycle.
---

# Focused verification and evidence — Implementer private draft (not approved)

## Trigger
Use for a task that requires local red/green/regression evidence. The Implementer checks its own work; Runner executes independent long/noisy checks; M6 decides acceptance.

## Procedure
1. Map each actual acceptance criterion to the smallest existing effective test/check. Include required repo guards. Do not use file existence as behavior proof.
2. For new logic or a bug, where feasible prove the test fails against the original behavior; then implement and run targeted proof. Don't weaken/delete tests to make them pass.
3. Record command, cwd, task ID, snapshot SHA, exit code and decisive assertions. Passing local tests does **not** imply integration or production acceptance.
4. If missing credentials, a privileged environment, blocked network or unsupported permissions prevent the check, label it a blocker with required secret **names only**. Do not alter application code to satisfy a broken sandbox.
5. Leave cross-subplan smoke, full-suite scheduling, retries, verdict publication and evidence reuse policy to M1/M5/M6/Runner.

## Stop condition
End once the approved task change and required local verifications are complete, or return a precisely evidenced blocker. Do not expand to a full development cycle.
