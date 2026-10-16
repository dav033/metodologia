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

## Provider windows, reset rules and attribution gaps (T5)

| Cached source | Effective account | Windows exposed | Reset and freshness behavior | Strict-selection gap |
|---|---|---|---|---|
| `bt_subscriptions` / Claude OAuth usage | `bt_agents.account_key(profile)`; environment-equivalent profiles share a key; M2 persists only `account_reference(key)` | `five_hour`, `seven_day`, optional `seven_day_sonnet`, optional `seven_day_opus` | Absolute timezone-aware reset is parsed when present. Claude explicitly permits `resets_at: null`; a fresh null-reset observation remains active with unknown reset confidence. Cache TTL is 7,200 s; poll target is hourly. | `capacity()` requires fresh base 5-hour and 7-day windows for pressure but skips absent model windows, so a missing Sonnet/Opus limit can currently be mistaken for no extra limit. |
| `bt_subscriptions` / Codex rate limits | Same effective-account key and opaque M2 hash | Base `five_hour`, `seven_day`; zero or more `_model_buckets` keyed by provider `normalModelSlug`, each with 5-hour/7-day limits | Reset timestamps are required and numeric; unsupported durations and malformed/denied controls fail to unknown. TTL is 7,200 s. | The parser retains model buckets, but aggregate `capacity()` only checks a model bucket when one is present. There is no explicit inventory proving that every configured route model has a corresponding provider slug. |
| `bt_agy` / Antigravity usage report | Existing configured account identity via `bt_agents.account_key(profile, provider)` | Gemini pool `five_hour` and `seven_day`; Claude/GPT pool windows are parsed separately as informational `*_claude_gpt` values | Absolute ISO resets are required. Malformed/unknown pools are ignored; the cache TTL is 7,200 s. A known exhausted Gemini window remains exhausted until its reported reset even if the cache later becomes stale. | `capacity()` only evaluates both Gemini windows; it does not expose window records or map Claude/GPT pool limits to specific models. |

### Attribution and provenance

- Subscription polling stores account-level percentages and reset times, not task or attempt IDs. Multiple concurrent tasks, external provider usage, account aliases and a reset can all change a percentage between polls; no per-task quota delta can be inferred from the current cache.
- `bt_events.extract_usage()` records provider-reported token fields separately. Missing token fields stay `null`; token counts, quota percentages, subscription capacity and reported cost are different units and are never converted into one another.
- M2 currently receives only aggregate `quota_status`, one pressure percentage, `observed_at` and `valid_until`. Window identities and per-window status are discarded before `Candidate` construction.
- `propose()` reads current caches only. Polling/network refresh remains owned by the subscription supervisor; a source error, stale row, future observation, reset without a post-reset sample or missing required window must remain unknown in strict mode.

## T6–T7 implementation boundary

- The isolated M2 package now exposes `QuotaObservation` cache normalization with API/schema 1.2.0 and `DemandEstimate` with separate provider-token and quota-percentage-point units. Both helpers are pure and bounded; M2 still does not collect quota or refresh a provider.
- Delta attribution requires the same effective account/provider/model/window, overlapping reads, one active task, an unchanged reported reset and explicit absence of external usage. Parallel work, reset crossing, unknown reset or possible outside use returns `attribution_unknown`.
- Exact-context estimates expose empirical min/median/max, source, sample count and a maximum one-day TTL; this is not a calibrated prediction. The existing methodology adapter still consumes its current aggregate quota/history inputs; wiring per-window demand into batch decisions remains future work under T13–T18.

## M1/M5 and concurrent primary work

- Clean M2 base has M1 contract 1.1.0 with approved plan hash and READY/free-slot request. The existing M5 approval (REQ-019/D-041) targets shared M1 contract 1.2.0 with `RecoveryPort` signatures unchanged. M2 will not edit the shared M1 contract; its adapter must remain compatible with the additive 1.2.0 integration.
- Current primary worktree contains substantial uncommitted M4/M5 work, including a v1.2.0 M1 contract and M4 wiring; it remains preserved outside the M2 branch. M5 code is implemented in `/home/david/dev/metodologia-m5` (`feat/scheduler-m5-recovery-manager`): its isolated package suite passes 37/37 and its current delta stays within `skill/scripts/bt_scheduler_recovery/**`. Shared M1/M4 wiring and M1→M5 integration remain unproven.
- REQ-013 is already complete. Its Laya gate stays disabled: the measured held-out hybrid did not beat the deterministic reference (14/100 raw Laya vs 21/100 deterministic); no new inference is authorized by this plan.

## Baseline verification

- M2 package: 65/65.
- M1 core: 239/239.
- Planner: 219/219.
- M2 source/contract + M1/Planner integration: 64/64.
- Quota parser + Antigravity source: 55/55 after carrying the matching strict validation change in `bt_agy.py`; an earlier incomplete partial port failed 4 cases and was corrected before accepting this baseline.
- `git diff --check`: clean on the isolated M2 branch.
- The frozen synthetic 200-row reference baseline is in `baseline-report.json`; it validates the corpus labels and stable `(baseline_rank, route_id)` selection. Its 23.5% oracle agreement is fixture-only, not real acceptance quality or evidence of quota savings.
