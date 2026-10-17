# `bt_scheduler_decision` — M2 public contract

M2 can recommend a route for one READY task or plan a bounded READY batch. M1 remains authoritative: it validates
each returned `Assignment`, checks capacity and resource claims atomically, and may refuse it. This package is
standard-library-only and imports no methodology module. `bt_scheduler_decision_adapter.py` is the sole methodology
adapter; it translates the M1 port and existing catalog, profile, quota and telemetry facts into this contract.

The frozen Python API is exported by `__init__.py`: `DecisionRequest`, `TaskFacts`, `Candidate`, `RouteHistory`,
`LayaChoice`, `DecisionRecord`, `RouteSummary`, `RouteBinding`, `Exclusion`, `Confidence`, `ValidatedRequest`,
`DecisionInputError`, `validate_request`, `candidate_route_id`, `account_reference`, `executor_reference`,
`parse_executor_reference`, `canonical_json`, `sha256_json`, `rank_candidates`, `deterministic_reference`,
`CandidateRanking`, `DemandEstimate`, `DemandSample`, `observed_token_usage`, `attribute_quota_delta`,
`estimate_demand`, `assess_history`, `HistoryAssessment`, `DecisionLedger`, `DecisionLedgerError`,
`RouteQuotaRequirement`, `BatchRouteQuotaAssessment`, `BatchQuotaAssessment`, `assess_batch_quota`,
`AccountConcurrency`, `BatchDecisionStore`, `BatchAssignment`, `BatchPlan`, `BatchQuotaEvidence`, `BatchRouteExclusion`, `BatchUnassignment`,
`RoutePolicyConfig`, `RoutePolicyEvidence`, `QuotaWindowPreference`, `plan_ready_batch`,
`SHADOW_POLICY_VERSION`, `ShadowAssignment`, `ShadowComparison`, `ShadowTaskComparison`, `compare_shadow_batch`,
`QuotaObservation`, `QuotaAssessment`, `normalize_cached_windows`, `assess_required_windows`,
`assess_account_windows`, `PerformanceEvent`, `PerformanceEventError`, `normalize_performance_event`,
`reduce_performance_events`, `PerformanceContext`, `PerformanceMeasurement`, `ContextualHistoryAssessment`,
`PerformanceHistoryError`, `aggregate_performance_history`, `LearningSnapshot`, `LearningSnapshotStore`,
`TemporalEvaluation`, `TemporalEvaluationError`, `evaluate_prequential_history`, `idempotency_key`,
`decision_id_for`, `resolve_executor_reference`, and `resolve_executor_binding`. Their normative serialized fields and enums are in
`api-contract.json`. Methodology callers use this public surface through `bt_scheduler_decision_adapter.py`, never package internals.
Malformed identity/route values, non-finite numbers, invalid SHA-256 values, and oversized collections are rejected.
Optional classifications and evidence are normalized to explicit unknown facts with stable warnings; the nested
classification, evidence and verification payloads share a 8,192-node and 256-KiB JSON budget before normalization.

## Request and candidate facts

`DecisionRequest` binds a single task to its `task_id`, `plan_id`, positive `revision`, the approved lowercase
SHA-256, M1's current `free_slots`, a finite request time, the policy version, and either a pinned checkpoint
revision or `null`. It includes
the complete normalized candidate snapshot, including candidates already excluded by source policy, their source
status/reason codes, quota observations, router order, and bounded history. Candidates are sorted by stable route ID
before hashing or comparison, so source enumeration order cannot change the fingerprint.

`TaskFacts.brief` is transient local input for Laya, bounded to 2,048 characters and never written to SQLite. M2 stores
only its SHA-256 plus task/plan identity, enum classifications, structural counts and the classification-evidence
summary (dimension, validity, typed reference kinds and count). It never stores task prose, evidence justifications,
acceptance text, verification command text, credentials, conversations or model output. The fingerprint includes a
digest of every validated task input, including the transient brief and evidence, so changing task content cannot
reuse a stale decision.

The route identity is SHA-256 over canonical JSON `{provider, model, profile, effort}`. A candidate also carries an
opaque `account_ref`, SHA-256 of the existing router's account key; raw account keys and profile environment are never
persisted. Provider/model/effort/profile/account facts come from the methodology adapter's current sources; this
package has no provider inventory. A candidate is eligible only when profile authorization is true, authentication is
valid, provider runtime is available, quota is known and below exhaustion, the quota freshness deadline is after
`requested_at`, and source policy has not excluded it. `unknown`, `stale`, malformed or unsupported quota is never
available. The adapter derives the freshness deadline from the quota source's own age policy; M2 checks the explicit
deadline and does not copy a second TTL. M1 `free_slots` is validated before inference; M1 still performs the final
atomic capacity check.

Historical measurements keep verified successes, verified failures, claimed/unverified attempts, other failures,
duration coverage/median and token coverage/median separate. An absent sample remains unknown; sparse history is
shrunk to the declared prior/minimum-sample rule. Subscription quota is not a price estimate, and a model score is
never converted to real-world success probability.

`QuotaObservation` is a versioned, account-scoped record for one provider/model window. `normalize_cached_windows()`
reads only values supplied from existing subscription or Antigravity caches; it performs no collection or network I/O.
Every result retains the opaque account reference, window ID, source, observation time, validity deadline, reset
time/confidence, usage percentage, state and a finite reason code. Missing, malformed, stale, future, auth-error or
reset-expired data stays `unknown` or `stale`; all caller-required windows must be fresh before
`assess_required_windows()` reports available capacity. The pressure is the highest observed percentage among those
windows. A null reset can be marked usable only for a Claude window explicitly declared by its source; Codex and
Antigravity require a reported future reset. This status is quota telemetry, not a token or currency estimate.

`DemandEstimate` keeps provider tokens and quota percentage points in separate units. Direct token observations retain
the provider usage source. A percentage delta is observed only when both cached readings describe the same account,
provider, model and window, the reset is known and unchanged, exactly one task ran, and telemetry explicitly rules out
external usage. Parallel work, reset changes, unknown resets, stale reads, counter decreases or external usage return
`unknown` with `attribution_unknown` where attribution is unsafe. `estimate_demand()` accepts only bounded, unique,
exact-context samples of the same source and unit; it reports sample count and the empirical min/median/max range with
a maximum one-day validity. This range is not a confidence interval or a calibrated forecast. Token counts are never
converted to quota percentages, and percentages are never converted to tokens or currency.

`assess_account_windows()` checks base and model-specific scopes independently for one opaque effective account.
`assess_batch_quota()` reuses that assessment for candidate aliases that share an account, counts the account once and
marks a route eligible only when every window it requires is available. A fresh five-hour reset cannot offset an
exhausted weekly or model-specific window. This is a read-only assessment; it does not reserve capacity or change M1.

`plan_ready_batch()` is the public bounded selector over supplied `DecisionRequest`s from one plan
revision, plan hash, request time and `free_slots` snapshot. It applies `m2-route-policy-v1` after hard filters, then
matches tasks to effective accounts with a deterministic capacity-aware augmenting-path algorithm. Tasks with fewer
eligible accounts are considered first, with task ID as the stable tie-break; route order stays the route policy's
order. It emits at most `free_slots` distinct task assignments and subtracts active work from each supplied account
concurrency limit. When no account limit is supplied, it applies no inferred per-account limit and remains bounded by
the global slots. The plan contains only opaque hashes, route ranks, route exclusions and stable selection/no-assignment
reasons and a separate allowlisted quota telemetry record per considered route. That record retains only task/route
IDs, profile ID, opaque account reference, fresh/stale/missing/malformed/refresh-failed/exhausted state,
observation/validity epochs, used percentage and a stable reason code. It is not raw `RoutePolicyEvidence`; task
text, credentials and provider output remain excluded. The evidence has 128-task/4,096-route bounds and the
complete plan is limited to 2 MiB. `BatchQuotaEvidence` is an optional public input. `DecisionLedger.batch_decisions.persist()`
stores the plan append-only under its canonical input fingerprint; `get()` reads it by that fingerprint. Exact
replay returns the first stored plan and checksum failures fail closed. The M1 adapter uses this planner for its
initial full-DAG map and requests a fresh batch recommendation before READY dispatch; M1 remains the sole reservation
authority. Batch record 1.3.0 is additive and policy-versioned; the reader continues to decode 1.2.0 records without
rewriting them. Older binaries do not understand 1.3.0 rows and must not be given a v2 fingerprint; rollback keeps
the ledger and resumes v1 writes using v1 fingerprints.

`compare_shadow_batch(..., enabled=True)` returns a content-addressed `ShadowComparison`; with `enabled=False` it
returns `None` before validating or traversing inputs. The deterministic baseline uses router order in the supplied
READY order, while the proposed result uses the batch policy. Both receive the same normalized task requests,
route-policy evidence, `free_slots` and explicit account-concurrency snapshot. The result contains each side's
assignments, exclusions and no-assignment reasons plus stable per-task difference codes. It is a replayable in-memory
record: T17 does not write the ledger, dispatch, reserve capacity, call a provider or change task state.

## Selection and confidence

Deterministic filters run before Laya. The deterministic reference is the existing `bt_agents.candidates` router
order (provided as an explicit `baseline_rank`), followed by stable route ID for any tie. Tasks that are unambiguous,
have insufficient classification evidence, have fewer than two eligible candidates, exceed the supported candidate
count, or lack a calibrated enabled checkpoint do not invoke Laya. Laya receives only eligible candidates. Its answer
must name an eligible route and pass the locally measured `answer_confidence` cutoff; otherwise M2 records the fallback
reason and selects the deterministic reference. A circuit breaker, timeout, malformed output, worker error or missing
checkpoint has the same bounded fallback behavior.

`rank_candidates()` revalidates the request, rejects any route without explicit profile authorization, an available
source, valid authentication, available runtime and fresh known quota, and returns stable reason codes for each
excluded route. Eligible candidates retain the existing router's `baseline_rank`; rank ties and absent ranks are
ordered by stable route ID, never by input order. `deterministic_reference()` returns the first eligible route or
`None`. The methodology adapter supplies this rank from `bt_agents.candidates`; M2 maintains no second provider
catalog. A source may set `source_status="available"` only after establishing route capacity; `capacity_unknown`,
`capacity_exhausted`, and `cooldown_active` are reserved blocking source reason codes that M2 filters even if a
contradictory `source_status="available"` is supplied. M1 `free_slots` remains a separate global bound.

`assess_history(request, route_id)` revalidates the request, then counts only verified successes and failures as judged outcomes. Claimed attempts never become
successes. It preserves the source tag (`observed`, `sparse`, `estimated` or `unknown`) and never promotes estimated
duration/token values to verified outcomes. It exposes the raw measured rate separately from a Beta(2, 2)-shrunk routing feature; the feature's prior
strength is four observations and history is considered sufficiently sampled at five verified outcomes, matching
`bt_agents.MIN_SAMPLES`. With no verified outcomes, both values stay `null`; duration and token medians keep their own
sample counts and are not imputed. This historical feature is not a calibrated prediction of future task success and
does not override the deterministic router's explicit baseline rank.

`normalize_performance_event()` joins bounded M1 attempt, M2 decision and M1-applied verdict projections by exact
plan/revision/task/attempt/decision/route identities. Only an applied independent PASS or FAIL with explicit event
time recorded by M1 and non-synthetic sources enters verified history. Claims, cancellations, infrastructure failures, stale or
uncorrelated verdicts, PASS rows without required acceptance evidence and synthetic rows remain non-learning outcomes. The output is
replayable by `(attempt_id, verdict_id)`, omits verifier labels and evidence text, and never writes M1 or M6 state.
`reduce_performance_events()` removes identical replays, lets a later M1 application supersede an earlier stale
delivery of that verdict, and demotes conflicting applied or multiple-applied verdict identities for the same
plan/revision/task/attempt to `unknown` without depending on arrival order.

`aggregate_performance_history()` consumes only eligible T9 events and a separate allowlisted context map. It reports
unique attempt counts, PASS/FAIL sample counts, non-quality outcomes, coverage, the observed rate and a descriptive
Wilson 95% interval. It searches exact context, complexity class, task family and route; a level informs the ranking
feature only after five verified samples. If the route bucket is still sparse, the selected feature stays `null` and
the caller retains the existing deterministic baseline. The Beta(2,2)-shrunk value is a ranking feature, not a
forecast or calibrated success probability. Legacy aggregate telemetry is not converted into correlated events here;
validated M4/M6 source wiring remains a later adapter task.

`evaluate_prequential_history()` assigns cutoffs only from M1-applied events with a valid timezone-aware
`applied_at`; stale, invalid and noop deliveries cannot make an outcome appear available. It partitions raw events
across all routes before replay reduction, then aggregates the selected route so conflicting route projections stay
unknown. Facts at the cutoff are training; later facts are evaluation, and an attempt already known at the cutoff
cannot reappear as a future sample. Attempts without a valid M1-applied timestamp are excluded from both sets and
reported separately. Each source fingerprint contains only pre-cutoff reduced events. Historical ranking features and future observed counts/rates are
separate descriptive values; future rates are not success probabilities or calibration results.

`DecisionRecord.confidence` is a tagged value. Laya confidence means only “this choice score passed the local
chooser-calibration cutoff”; it is not a probability of task success. Deterministic confidence means only a policy
margin/tie description. If no meaningful margin exists, its numeric value is `null`. The record's rationale is
rendered from bounded stable factor codes and measured facts; arbitrary Laya explanations are not persisted.

## Persistence and M1 reference

The idempotency key is lowercase SHA-256 of UTF-8 canonical JSON (`sort_keys`, compact separators, Unicode NFC,
finite numbers only) over: M2 contract version; plan ID/revision/hash; the validated task input digest; the full
content-addressed candidate/quota/telemetry snapshot; policy version; and configured checkpoint revision or `null`.
Request time is recorded but excluded from the key. Exact replay returns the original record and timestamp. A changed
task, route, quota, telemetry, policy or checkpoint snapshot creates a new record linked to the latest decision for
the same plan/task. `DecisionLedger` owns a separately selected SQLite file, verifies its application/schema IDs
before writing, uses WAL plus `BEGIN IMMEDIATE`, and serializes duplicate writers across threads/processes. It accepts
at most 100,000 records of at most 128 KiB each, failing closed at the bound; it never deletes older records. The
record rationale is the joined set of stable factor codes, not free text. The database file is set to mode `0600`.
`resolve_executor_reference()` returns a route only when its IDs match the persisted record's selected route.
Selected and alternative route summaries retain the quota sample time, measured usage percentage and validity deadline.
Records written under 1.0.0 and 1.1.0 remain readable, but any missing quota facts cannot be launched through M3.
Reason codes, factor codes and fallback codes are finite contract enums, so source explanations, task text and model
output cannot be smuggled into the audit record through those fields.
`DecisionLedger.persist()` accepts and revalidates the original `DecisionRequest`. It rejects a `ValidatedRequest`:
normalization intentionally removes evidence prose and raw references, so their input digest cannot be authenticated
again from the redacted object.

`DecisionLedger.learning_snapshots.persist()` stores the contextual aggregate, policy version and learning cutoff in
the same SQLite ledger. Its SHA-256 source fingerprint binds the normalized T9 event projections, hashed context
identities, route, target context, cutoff, policy and aggregate. Raw event/task identities are never stored. Exact
replays return the first immutable snapshot and timestamp; conflicting content, oversized snapshots and capacity
exhaustion fail closed. `learning_snapshots.get()` reads by fingerprint. Writable schema-1 ledgers migrate additively
through schema 2 to schema 3; writable schema-2 ledgers add only the immutable `batch_decisions` table. Read-only
schema-1 consumers remain able to read decisions and report no snapshots or batch rows; schema-2 consumers can read
decisions and snapshots and report no batch rows. Batch rows store no task prose, raw route-policy evidence,
credentials or provider output; the version-1.3 quota telemetry exception is restricted to the allowlist documented
above. They are append-only, capped at 10,000 rows and 2 MiB per plan, and fail closed at capacity. Callers
must build the learning aggregate only from facts available at its declared cutoff; T12 validates temporal use.

The M1 adapter receives multiple READY tasks and one shared `free_slots` budget. It considers tasks in M1 plan order,
continues past a task with no eligible route, adds at most one proposal per task, and stops after producing
`free_slots` proposals or exhausting READY tasks. Thus the batch never proposes more than M1's current capacity;
M1 still applies its own atomic checks and may refuse any proposal.

At Scheduler run creation the methodology adapter also implements M1's versioned `PlanRoutingPort`. It receives every
task in the approved DAG, including tasks blocked on prerequisites, and stores one independent M2 recommendation per
task before dispatch. These are route recommendations only: they do not reserve M1 capacity or M2 account concurrency.
When a task becomes READY, the existing bounded batch path makes a fresh decision using current quota and eligibility
facts; M1 persists that route with the reservation. The run projection therefore shows the up-front model for future
tasks and the refreshed route for tasks already dispatched.

The stable selected-route reference placed in M1's opaque `Assignment.executor` is
`m2:v1:<decision_sha256>:<route_sha256>`. It contains no credentials or profile environment. The public
`resolve_executor_reference()` resolves only the selected route of that persisted decision and returns `None` for an
unknown, malformed, excluded or non-selected route. `resolve_executor_binding()` answers the same question and adds the
decision's plan/revision/task and `superseded_by` (the id of a later decision for the same plan/task, if any): an executor
uses it to refuse a decision made for another task or already replaced. This gives an executor a lookup seam without
implementing M3 here. A ledger file is per project (plan ids are unique only within a project): never share one file
across projects, or one project's decision for `REQ-042/T1` would supersede another's. A recommendation is not evidence that M1 accepted or dispatched it.

The decision record includes the selected provider/model/profile/effort, eligible alternatives, filtered candidates and
stable reasons, baseline rank, selection factors, confidence semantics, policy/checkpoint versions, quota and source
snapshot hashes, fallback reason, plan/task identity and timestamp. It is bounded and stored in M2's own SQLite file;
it never writes plan files, M1 state, RUN.json or historical telemetry.

## Runtime configuration and rollback

Integrate M2 by supplying `DecisionAssignmentPort(project, ledger_path, laya_root=...)` as both M1's assignment and
full-plan routing ports. Use a
separate persistent ledger file per project; the ledger stores redacted decision evidence and is not shared across
projects. `propose()` reads local cached quota and telemetry facts only. M1 continues to validate proposals and own
reservations, task state and dispatch.

The optional `quality_artifacts` parameter enables Laya only when the frozen corpus, benchmark evidence, checkpoint
revision and code-reviewed allowlist all pass. Omitting it keeps the deterministic route reference active; the current
approved-evidence allowlist is empty. A real-provider experiment is separately authorized and is not a configuration
or activation gate by itself.

To roll back the M2 integration, wire M1 to the caller's prior `AssignmentPort` instead of `DecisionAssignmentPort`.
Keep the M2 ledger as audit evidence; no M1 state, plan or provider cache needs migration or deletion. To disable only
Laya, omit `quality_artifacts` and retain the deterministic M2 assignment flow.

## Reproducible local Laya runtime

Install the isolated CUDA environment and the three published checkpoints with
`python skill/scripts/setup_bt_scheduler_laya.py --install`; verify it later without network access using
`HF_HUB_OFFLINE=1 python skill/scripts/setup_bt_scheduler_laya.py --check`. The installer uses the checked-in
`laya-requirements.lock`, Python 3.12.14, Laya 0.4.7 at upstream commit
`432312b36714d8889eba405507b37eda25257d9c`, and PyTorch 2.14.0+cu132. It stores the environment below
`~/.local/share/bt-scheduler-laya` and hash-verified model files in its private `checkpoints/` directory. Set
`BT_SCHEDULER_LAYA_HOME` before installation to select another dedicated user-local directory.

The official English, multilingual and typed-decisions checkpoints are each pinned to their upstream Hugging Face
revision and verified by the published `model.safetensors` SHA-256 before inference. All three checkpoint cards and
the upstream Laya source declare Apache-2.0. Downloads require network access once; after that M2 loads local files
and can run with `HF_HUB_OFFLINE=1`. The pinned CUDA build also runs the same model on CPU when CUDA is unavailable;
the setup check reports the detected device without loading a checkpoint into VRAM. This installer is separate from
the standard-library-only `bt_scheduler_decision` core and does not change the methodology Python environment.

## Laya activation gate

Laya is advisory and can be active only after both benchmark gates pass. `DecisionAssignmentPort` accepts exactly five
quality artifact paths: frozen calibration decision, raw calibration results, held-out results, canonical fixture
corpus, and fixture manifest. The loader pins the corpus version and both hashes from `api-contract.json`, verifies all
100 case IDs and 20-per-family strata against that corpus, recalculates each checkpoint's calibration/Wilson gate, and
recalculates the production hybrid's paired bootstrap from the held-out rows. Missing, malformed, incomplete, or
inconsistent evidence leaves the deterministic policy active. The current measured calibration artifact has no passing
checkpoint, so production remains on the deterministic reference. Laya action scores are never success probabilities.

The evidence gate is an additional runtime check, not a benchmark generator: synthetic test outputs cannot replace the
canonical corpus or manifest. The corpus and manifest digests are pinned in `laya_quality_gate.frozen_dataset` and must
be deliberately updated alongside a new independently frozen benchmark protocol. Passing measurements must also match
an exact digest in `laya_quality_gate.approved_evidence_sha256`, a code-reviewed allowlist. The current allowlist is
empty because the measured CUDA hybrid did not beat the deterministic reference; synthetic or edited metrics cannot
self-authorize Laya.
