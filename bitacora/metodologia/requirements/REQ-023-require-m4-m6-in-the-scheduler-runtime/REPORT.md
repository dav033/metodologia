# REQ-023 — Require M4–M6 in the Scheduler runtime

Date: 2026-10-16  
Authority: David approved the plan in chat on 2026-10-16, confirming that every Scheduler-owned run requires M4–M6 and the legacy launcher stays separate.

## Built

- `scheduler-run` and `launch --scheduler` now create distinct, private, durable M4/M5/M6 stores for the stable Scheduler runtime identity and initialize the required ports before dispatch. Missing or unusable required wiring fails closed.
- The M1 owner loop drains bounded M3 stream batches into M4 and delivers M4's durable incident outbox through M1. Terminal output is revisited across bounded polls until EOF, and the owner waits for the incident outbox to empty before returning.
- M5 advises through M1's existing `RecoveryPort`; M6 verifies through `VerificationPort`. M1 remains the sole state/verdict owner, M2 routing stays deterministic, and `NEEDS_REVIEW` stays operator-owned.
- The M3→M4 FIFO bridge now walks path components relative to a trusted directory descriptor with `O_NOFOLLOW`, rejecting intermediate symlinks and replacement races before opening the FIFO.
- Added standard-owner end-to-end and backlog regressions, declared the required Scheduler modules in wheel metadata, and updated module and runtime documentation. D-052 records the activation boundary.

## Verification evidence

- Full offline Scheduler discovery: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests .venv/bin/python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_*.py' -q` — **350 tests passed, 6 skipped**, exit 0, 157.049 s. This includes the M1→M6 rejection, M5 bounded recovery, fresh M2 route and later M6 PASS path.
- FIFO path and M3 stream regressions, run after the final path-confinement change from `skill/scripts/tests`: `PYTHONPATH=.. /home/david/dev/metodologia/.venv/bin/python -m unittest test_scheduler_stream_adapter test_scheduler_m3_stream_wire -q` — **34 passed**, exit 0.
- Installed-wheel migration suite: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=skill/scripts:skill/scripts/tests /usr/bin/python3 tests/migration/test_package_install.py -q` — **19 passed**, exit 0.
- Scoped Ruff over the changed Scheduler runtime, wiring, stream adapter, tests, ledger and package-audit files — all checks passed.
- Scoped Python `compileall` and repository `git diff --check` — passed.
- Fresh independent spec review: APPROVE, no code findings. Fresh independent standards review: PASS, no new findings after the FIFO path fix.
- The first full Scheduler run had one transient failure in an existing M3 orphan-cancellation assertion. That test passed alone, then the complete suite passed on rerun; no unrelated test or implementation was changed to hide it.

## Rulings

- D-052 supersedes D-043's opt-in M6 activation clause and D-051's separately opt-in M4–M6 activation clause. The existing M1 ports, explicit `--scheduler` boundary, legacy default and operator-owned review remain in force.
- Terminal M3 streams and M4 incidents remain bounded per owner poll, but they must be requeued and drained to completion before the owner exits; otherwise large output or an outbox over one batch could be lost.
- FIFO confinement checks every path component without following symlinks; checking only the final FIFO component would leave an intermediate-directory escape.

## Needs your eyes

- Verification is offline and uses fake M3/provider processes. No real provider call, live Scheduler task, web server or autostart installation was performed.

## Proposals

- None.

## Pending

- P-042 (package coverage and FIFO path escape) and P-043 (mandatory M4–M6 runtime wiring) are closed with this acceptance. No REQ-023 implementation or verification item remains open.
- No commit or push was made; the shared worktree contains unrelated concurrent local changes that were preserved.

## Independent review

- Spec axis: approved; no implementation findings.
- Standards axis: passed after the terminal-stream/backlog and FIFO path-confinement corrections.
