# REQ-020 live inventory

Inspected 2026-10-15. M2 worktree starts at commit `27ba48f2cb1e8e6d262a9eeb9b9df84904eee94f` (`feat/scheduler-m2-learning-quota`), the current primary branch tip at worktree creation. The branch is isolated from the uncommitted M4/M5 primary work.

## Existing M2

- `skill/scripts/bt_scheduler_decision/` is the existing standard-library package; deterministic hard filters and reference ranker precede optional Laya. Current committed API is 1.0.0. Existing primary-worktree quota-evidence changes were selectively carried into this branch: API/records 1.1.0 retain observation time, measured usage and expiry; legacy 1.0.0 decisions remain readable.
- `skill/scripts/bt_scheduler_decision_adapter.py` builds one candidate row per configured eligible profile from `bt_agents.candidates`, project/profile policy, cached quota and existing `bt_events` history. It derives the model/effort from the current tier rather than enumerating all supported configurations.
- `bt_scheduler_adapter.DecisionAssignmentPort.propose()` calls the per-task decision engine in READY plan order until `free_slots` are filled. It does not compare a joint task×route matrix or model shared-account pressure across the batch.
- `Candidate` carries one aggregate quota status, observation timestamp, expiry and usage percentage. The source caches preserve 5-hour, weekly and Codex model-specific windows, but M2 does not retain each window in its record.
- `_history_snapshot()` groups coarse `(provider, model, profile, effort, kind)` rows and counts verified, failed and claimed events separately. It has duration/token coverage but does not associate every observation with the complete plan/revision/task/attempt/decision/route/verdict identity required by this SPEC; those rows cannot all be learning labels.
- `bt_events.read_all()` and `bt_quality` are existing read-only telemetry sources. Legacy event success is not enough to train on unless independent verification and the same attempt are correlated.

## Existing quota/account sources

- `bt_agents.account_key()` resolves configured provider/profile account identity; M2 hashes it to `account_ref`.
- `bt_subscription_sources` parses subscription cache inputs; `bt_subscriptions.capacity(row, model, now)` currently reduces several windows to aggregate pressure/exhaustion. Current dirty-primary parser changes for Codex model buckets, Claude null reset and strict Antigravity numbers were copied selectively and verified here.
- `bt_agy.capacity()` remains read-only in M2. No M2 selection path refreshes OAuth or makes provider network calls.

## M1/M5 and concurrent primary work

- Clean M2 base has M1 contract 1.1.0 with approved plan hash and READY/free-slot request. The existing M5 approval (REQ-019/D-041) targets shared M1 contract 1.2.0 with `RecoveryPort` signatures unchanged. M2 will not edit the shared M1 contract; its adapter must remain compatible with the additive 1.2.0 integration.
- Current primary worktree contains substantial uncommitted M4/M5 work, including a v1.2.0 M1 contract, M4 wiring and an untracked M5 module. It is preserved and outside this branch. M5 recovery unit tests in that tree passed 33/33, but there is no M5 `RUN.json`, no live subagent, and the listed `/tmp/metodologia-m5-module` worktree is absent. Therefore M5 integration is not yet proven.
- REQ-013 is already complete. Its Laya gate stays disabled: the measured held-out hybrid did not beat the deterministic reference (14/100 raw Laya vs 21/100 deterministic); no new inference is authorized by this plan.

## Baseline verification

- M2 package: 65/65.
- M1 core: 239/239.
- Planner: 219/219.
- M2 source/contract + M1/Planner integration: 64/64.
- Quota parser + Antigravity source: 55/55 after carrying the matching strict validation change in `bt_agy.py`; an earlier incomplete partial port failed 4 cases and was corrected before accepting this baseline.
- `git diff --check`: clean on the isolated M2 branch.
- The frozen synthetic 200-row reference baseline is in `baseline-report.json`; it validates the corpus labels and stable `(baseline_rank, route_id)` selection. Its 23.5% oracle agreement is fixture-only, not real acceptance quality or evidence of quota savings.
