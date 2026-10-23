# REQ-020 — M6 baseline inventory

Audited on 2026-10-15 in the clean `feat/scheduler-m6-quality` worktree at base `8749e44`.

## M1 contract and authority

- `skill/scripts/bt_scheduler_core/contracts.py`: `VerifyOrder` carries idempotency key, plan/revision/task/attempt,
  fencing token, approved acceptance strings and approved verification mappings. `Verdict` carries the same
  identity, `accepted`, verifier, evidence and token. `verdict_problem()` validates the external shape.
- `skill/scripts/bt_scheduler_core/contracts.py`: `VerificationPort.request(VerifyOrder) -> Ack` is only the request
  direction. `Ack` is `accepted|duplicate|rejected`; the verdict returns through M1's
  `SchedulerCore.submit_verdict(Verdict)`.
- `skill/scripts/bt_scheduler_core/dispatch.py`: sends the verify order after M1 has moved the attempt to
  `VERIFYING`, outside a transaction. An accepted Ack marks only the verify request as delivered.
- `skill/scripts/bt_scheduler_core/events.py`: a task reaches `COMPLETED` only after a current-attempt,
  non-empty, independently labelled accepted verdict. A rejected verdict goes to M1 recovery. `execution_finished`
  only queues verification.
- M1 contract at this clean base is `1.1.0`. The author's dirty M4/M5 worktree has a separate `1.2.0` diff; M6 does
  not read or edit that worktree and does not require changing either contract.

## M3 handoff and integration

- `skill/scripts/bt_scheduler_executor/handoff.py`: M3 writes a bounded `handoff/manifest.json` with
  `attempt_id`, trusted `repository`, `base_sha`, `head_sha`, `snapshot_sha`, dirty/untracked metadata and refs. It
  builds the snapshot tree from a temporary index, so committed, modified and untracked non-ignored files are
  preserved without changing the user's index or worktree.
- `skill/scripts/bt_scheduler_executor/settle.py` and `executor.py`: handoff status and artifact paths are exposed
  through the executor's public attempt description.
- `skill/scripts/bt_scheduler_integrator.py`: `PredecessorIntegrator.base_ref(task_id)` composes only accepted
  same-repository ancestor snapshots, detects conflicts/missing snapshots and records its base before M3 starts.
  It writes an integration ref; M6 must not call it against the live repository or duplicate its algorithm.
- M6 can validate the M3-pinned `base_sha` against the attempt description and handoff manifest, then prove it is an
  ancestor of `snapshot_sha` and execute the archived snapshot in its own isolated filesystem.

## Existing related capability

- `bt_scheduler_adapter.py` is the existing M1 boundary; `bt_scheduler_executor_adapter.py` adapts M3. M6 will be a
  sibling adapter and will not wire or edit shared core/executor files in this branch.
- Existing audit, quality and review helpers are present in `skill/scripts`; their applicable APIs will be inspected
  for T10/T12 before adapting them. No new general audit or defect counter is authorized.
- There is no `bt_scheduler_quality` package or quality adapter at this base.

## Baseline evidence

- M1 core: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s bt_scheduler_core/tests -q`
  from `skill/scripts` — **239 tests, OK**.
- M3 executor: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts python3 -m unittest discover -s
  skill/scripts/bt_scheduler_executor/tests -q` from the repository root — **272 tests, OK**.
- Host capability: `/usr/bin/bwrap --unshare-all ...` ran a temporary Python probe; `/home/david` was not visible
  and a connect attempt returned errno 101 (no route) — **sandbox preflight OK**.
- These are base/reference checks only, not evidence that M6 is implemented.

## Worktree and ownership

- M6 branch/worktree: `/home/david/dev/metodologia-m6-quality`, `feat/scheduler-m6-quality`.
- The existing author worktree `/home/david/dev/metodologia` contains unrelated uncommitted M4/M5 edits. It remains
  untouched.
- M6-only code owner: new `skill/scripts/bt_scheduler_quality/**` and
  `skill/scripts/bt_scheduler_quality_adapter.py`. No changes to M1/M3/M5 contracts, shared wiring or legacy run
  records.
