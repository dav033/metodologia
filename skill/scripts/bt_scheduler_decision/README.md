# `bt_scheduler_decision` — M2 public contract

M2 recommends a route for one READY task. M1 remains authoritative: it validates each returned `Assignment`, checks
capacity and resource claims atomically, and may refuse it. This package is standard-library-only and imports no
methodology module. `bt_scheduler_decision_adapter.py` is the sole methodology adapter; it translates the M1 port and
existing catalog, profile, quota and telemetry facts into this contract.

The frozen Python API is exported by `__init__.py`: `DecisionRequest`, `TaskFacts`, `Candidate`, `RouteHistory`,
`LayaChoice`, `DecisionRecord`, `RouteSummary`, `RouteBinding`, `Exclusion`, `Confidence`, `ValidatedRequest`,
`DecisionInputError`, `validate_request`, `candidate_route_id`, `account_reference`, `executor_reference`,
`parse_executor_reference`, `canonical_json`, `sha256_json`, `rank_candidates`, `deterministic_reference`,
`CandidateRanking`, `assess_history`, `HistoryAssessment`, `DecisionLedger`, `DecisionLedgerError`,
`idempotency_key`, `decision_id_for`, `resolve_executor_reference`, and `resolve_executor_binding`. Their normative serialized fields and enums are in
`api-contract.json`. The decision service itself is added in the next implementation milestone; callers use only this
public surface, never package internals.
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
Reason codes, factor codes and fallback codes are finite contract enums, so source explanations, task text and model
output cannot be smuggled into the audit record through those fields.
`DecisionLedger.persist()` accepts and revalidates the original `DecisionRequest`. It rejects a `ValidatedRequest`:
normalization intentionally removes evidence prose and raw references, so their input digest cannot be authenticated
again from the redacted object.

The M1 adapter receives multiple READY tasks and one shared `free_slots` budget. It considers tasks in M1 plan order,
continues past a task with no eligible route, adds at most one proposal per task, and stops after producing
`free_slots` proposals or exhausting READY tasks. Thus the batch never proposes more than M1's current capacity;
M1 still applies its own atomic checks and may refuse any proposal.

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
