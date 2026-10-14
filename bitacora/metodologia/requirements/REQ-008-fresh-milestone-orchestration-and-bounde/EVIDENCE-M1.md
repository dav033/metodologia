# REQ-008 — M1 evidence

## Verified behavior

- Durable requirements gate rejects drift, unresolved decisions, malformed/empty contract markers and invalid snapshots. Operational frontmatter status, task checks and progress preserve approval; business-body status changes remain material.
- Actual launch/handoff/run and dispatch-after-pause paths enforce the gate. Stop controls retain priority.
- Initial packages have aggregate UTF-8 limits and assignment-specific task/audit/FINAL contracts. Recent errors precede optional historical notes; mandatory overflow is rejected rather than silently truncated.
- Checkpoints validate identity, assigned task partition, schema and numeric budgets; writes are atomic/CAS under a strict lock. Builder and auditor checkpoints are separate.
- New-mode supervised hooks omit full skill/project history and provide bounded pointers. Legacy behavior stays explicit during bootstrap.

## Checks

| Check | Observed result |
|---|---|
| Initial legacy baseline | 639 tests, OK |
| Package regression after CLI registration fix | 10 tests, OK, exit 0 |
| Final targeted requirements gate | 13 tests, OK (implementer record) |
| Final targeted context/settlement | 15 tests, OK (implementer record) |
| Final combined migration + legacy collection | 875 tests in 176.136 seconds, OK |
| Scoped new-module/test ruff | Exit 0 |
| `git diff --check` | Exit 0 |
| Independent spec review | APPROVE after corrections |
| Independent standards review | APPROVE after corrections |

The combined suite log is `/tmp/req008-m1-final-tests.log` (summary lines 1184/1186). The runner agent exhausted its quota before returning the tool exit status; the coordinator independently observed that the original process ended and inspected its terminal unittest `OK` summary. No duplicate suite was started. This record does not invent a missing process exit code.

## Remaining acceptance work

M2/T3–T4 must enforce provider/runtime admission, fresh foreground process/session behavior, action dispatch, documentation and rotation. M3/T5–T6 must implement persisted autonomous three-agent recovery. M4 must verify the complete integrated flow and reconcile policy consumers. The design council and real capability smokes do not complete those requirements.

Known M1 groundwork limits: abandoned strict checkpoint locks currently require explicit inspection; older runs lacking `context_run_id` cannot enter new mode without migration. T4 must handle these recovery/adoption paths before final completion.

## Current owner direction

The owner approved REQ-008 and later explicitly requested continuing in the current conversation without preparing or executing a parent relay. This does not remove the requested same-terminal feature from the product scope. No parent handoff or relaunch was performed by this coordinator.
