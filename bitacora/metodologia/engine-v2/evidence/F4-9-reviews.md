# F4-9 independent reviews (target ev2/INT-F4b..f3b38279f), consolidated by the lead

Full reviewer reports were returned to the lead session 1fbc12c7; this file keeps the findings the repair tasks must close.
Probes used by the Antagonist: /home/david/.local/tmp/claude-1000/-home-david-dev-metodologia/1fbc12c7-f198-49e5-9f0b-4da5d5904fbf/scratchpad/probe.py, probe2.py

## Standards (CHANGES_NEEDED)
- S1 [high] `bt_scheduler_executor_wiring.py:362-370` `needs_review_handoff` calls `scheduler.handle_needs_review(...)` without `return`; `handoff_needs_review` (`bt_scheduler_quality_owner_adapter.py:19-22`) always sees None, never calls `store.retry_m5_transient`. Resume is dead; the only test installs its own returning handoff.
- S2 [medium] second resume: `retry_m5_transient` raises RETRY_EXHAUSTED after one resume, but M1 hold already set `resumed`; exception only logged (`bt_scheduler_quality_adapter.py:353-359`); attempt stays VERIFYING forever. Must end in `block`.
- S3 [low] policy parser (`bt_scheduler_verification_authority.py:36-47`): follows symlinks, unbounded read, RecursionError on deep JSON, FIFO blocks open; same size cap for secrets.env (`_declared_names:20-31`).
- S4 [info] grew over-limit files: bt_scheduler_adapter.py 664→728, bt_scheduler_quality/store.py 769→774, bt_flow_bus.py 500→506.

## Spec (CHANGES_NEEDED)
- P1 [high] = S1.
- P2 [medium] `OwnerCompositionRuntime.propagate` (`bt_scheduler_owner_composition.py:368`) has no production caller; the run loop only calls reconcile_subplans/reconcile_compositions.
- P3 [medium] an operator-resolved acceptance (`m6://resolution/<digest>`, `quality_delivery.py:181`) makes `_m6_evidence` raise in `reconcile_subplans` → run() exits 3 on every resume. Must hold-and-skip like the composition path.
- P4 [info] `authorize_environment` ignores `authorization_needed`.

## Antagonist (BLOCKING)
- A1 [blocker] `reconcile_compositions` (`:309-331`) rebuilds every completed gate's candidate each step; after C2, rebuilding C1 raises `ValueError INVALID_MEMBERS` uncaught → owner exits 3 on every resume (the C1→S1→C2 scenario). Also `subplan_publication_facts` does not filter stale versions; `engine.publish` early-returns True, then `record_composition("published")` raises NOT_ALLOWED because `subplans.py:295` checks members-current before the idempotent return at `:297` → owner deadlocks itself.
- A2 [major] any `_composition_proof` mismatch `continue`s silently; gate stays completed with no published composition and dependents advance. `build_candidate` is called 3× (`:289`, `:293`, `:311`) as a "query" with side effects.
- A3 [major] `_contract_hashes` (`:246-258`, `bt_composition_adapter.py:77-91`) only accepts exact blobs; glob/dir paths → CONTRACT_HASH_UNAVAILABLE re-raised (`:237`) kills the owner; `blob_sha256` hashes text-mode stdout (CRLF normalized, non-UTF-8 raises).
- A4 [major] `bt_scheduler_core/recovery.py:129-137` `apply_observation` never marks `budget_consumed`; lost start ack + M3 failed/running/finished → code ran but no budget spent (probe: consumed False, attempts_used 0, state failed).
- A5 [major] plans may declare gates the engine cannot compose (disjoint gates, subset after superset) → INVALID_MEMBERS at runtime disguised as COMPOSITION_BASE_UNAVAILABLE/blocked_environment; COMPOSITION_CURRENT_MOVED escapes uncaught at `:326`.
- A6 [major] SP version publishes the tip of `refs/m3/line/...` without comparing `tree_oid(line_commit)` to the verified tree; the owner rebuilds M3's ref name by hand instead of public `Line.ref()` (`bt_integration_line.py:107`); a rename silently skips publication.
- A7 [minor] authority: ignores `authorization_needed` (no REQ/task scope); empty `FOO=`/empty env var counts as available.
- A8 [minor] workspace root `/tmp/bt-composition-owner/<project>/<req>` predictable, no owner check; README vs modules.md contradict on M5 wiring.
- Design risks: blocked-environment protocol by free-text strings duplicated in `dispatch.py:129-136` and `recovery.py:83-87` (should be `Ack.classification` only); `recovery.py:79-90` forces block only for `source == "policy"` — an M5 `retry` on blocked_environment loops without spending budget; M6 FAIL never calls `engine.reject`; constant environment fingerprint `sha256(b"composition-owner-env/1")`; shared sqlite connection across threads (latent).
