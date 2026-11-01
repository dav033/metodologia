# Solver 20261101-013124-d75b — pictures REQ-021 r35

## Trigger
`pictures:REQ-021:r35:T3.15:blocked:366499d7c41fad72`: T3.15 (audit of SP-3) held blocked after 2 remediation rounds; round 2
was rejected with "the audit changed 6632 file(s) it did not declare: .verification-snapshot/...".

## Origin
Engine restart at 00:39:52 SIGKILLed `git worktree add` of attempt a201; `allocate` reused the registered, half-built
worktree (index missing: every tracked file `D ` + `??` for the 1933 files that were written). The auditor audited a shell and
the attempt snapshot 3485dbb holds 1933 of the base's 8564 files. Same root cause as D-283 (operator metodologia-97, main
00c3b93c8); I found it independently (telemetry + a201 `output.log` first `git status`) and did NOT integrate a duplicate.

## What I did
- `bt-durable retry-task pictures REQ-021 T3.15 --by solver` (request e7ede9fc...), as the operator asked.
- Unintegrated branch `solver/20261101-013124-d75b` (commit 675e8e13b, test red without fix): the same rebuild for
  `_allocate_snapshot` (composition/integration/subplan worktrees), which D-283 does not cover. Left for the owner/operator.

## Verification failed: the retry did not start clean
Attempt a301 (`...T3-15-a301-61efbc56...`) has HEAD = 3485dbb, the POISONED snapshot of a201 (1933 tracked files, base was
860f035 with 8564). `bt_scheduler_retry._plan` continues "from the previous attempt's snapshot" for any retry, audits included,
so the audit again sees an incomplete tree; and its snapshot is a diff against 3485dbb, so integrating it onto the line risks
deleting ~6631 files. D-283 fixes new allocations only, not the inherited damaged snapshot.

## Not done
- Did not stop a301, edit refs/DB state or integrate (operator/engine told me not to integrate).
- Needed: stop a301 and retry T3.15 from the clean base 860f035. Needs either a code fix (retry must not continue from a snapshot
  whose tree dropped most of its base's files) or an owner/operator-approved manual reset of T3.15's recorded snapshot.
