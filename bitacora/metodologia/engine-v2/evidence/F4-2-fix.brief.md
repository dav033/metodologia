# Task F4-2-fix — TIMEOUT handling and frontier/evidence bounds in M5

Read first: `/home/david/dev/.engine-v2-wt/RULES.md` (binding). Worktree `ev2/F4-2` at `26e7c7476`; commit on top.
Context: `/home/david/dev/.engine-v2-wt/F4-2.brief.md`, ENGINE-F4.md §§0–3 in
`/home/david/dev/metodologia/bitacora/metodologia/engine-v2/`. Own the same files as F4-2.

## Findings (independent Claude reviews, reproduced) — write each failing test first
1. [high, spec] TIMEOUT "at most one retry, then block" fails on the verification path (`policy.py:82-86`, `:103-106`):
   with `core_cause=technical_cause=verification_rejected`, `execution_state=finished`, `reason_code=TIMEOUT`, `propose`
   returns `retry` for both `HistorySummary(0)` and `HistorySummary(1)` because the `verification_rejected` branch
   matches before the `timeout_repeated` check.
2. [medium, standards] `reason_code == "TIMEOUT"` overrides the technical cause for any case: with
   `transient_confirmed=False`, technical causes `killed`, `artifact_error`, `start_failed`, `quota_exhausted`, `clean`,
   `unknown` all return `retry transient_ready`, bypassing permanent-cause blocks, the quota wait and transience
   confirmation.
   [Lead ruling for 1+2: TIMEOUT is a verification reason. Apply it only when the case comes from M6 verification
   (`core_cause == "verification_rejected"`): decide it BEFORE the generic verification branch — retry once if the
   task's history holds no earlier TIMEOUT decision (count prior TIMEOUT decisions by reason, independent of
   technical_cause), otherwise block `timeout_repeated`. For any other core cause, ignore the M6 reason for cause
   mapping and keep the existing technical-cause policy unchanged (permanent blocks, quota wait, transience).]
3. [low] Frontier ids are not checked: `frontier=["T1","ZZ"]` with `source_task_id="T1"` is accepted
   (`adapter.py:229-239`, `propagation.py:31-35`). Validate in the adapter against the current scheduler state's task
   ids and reject the source task in its own frontier.
4. [low] M6 evidence bytes are unbounded (`adapter.py:~144-150`): reject more than 1 MiB before hashing/parsing.
5. [low] A v1 wire case carrying a `reason_code` key is silently overwritten with UNCLASSIFIED: refuse it with
   `SCHEMA_MISMATCH` (v1 has no reason field) — legacy stored v1 rows without the key must still load.
6. [low, spec] Tree identity check is format-only: document in README/modules.md that `snapshot_sha` is the binding
   identity and the tree digests are informational, unless a tree id is available from the facts — then compare.

Then: M5 module suite, `tests/test_scheduler_recovery*.py`, full root suite per RULES.md.
