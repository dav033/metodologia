---
id: REQ-013
status: ready
created: 2026-10-14
track: deep
---
# REQ-013 — Scheduler M2 Decision Engine with local Laya

## Problem & goal
M1 currently has a deterministic assignment port and a FIFO simulator. The methodology already has a configured
agent/model catalog, account profiles, quota readings, a deterministic router and attempt telemetry, but no Scheduler
module combines those sources into an auditable recommendation for an M1-ready task. M2 shall recommend an eligible
provider, model, profile/account and effort while M1 remains the authority that accepts, reserves and dispatches it.
The current M1 `AssignmentRequest` omits the approved plan hash and several planner classification fields, so the
integration requires a backward-compatible additive v1.1.0 assignment-contract extension; M1's state machine and
Planificador schema stay unchanged.

**Success looks like:** M2 is an isolated, reproducible module plugged into the versioned M1 `AssignmentPort`; simple
tasks use deterministic policy without inference; ambiguous tasks can use local Laya only when its measured decision
quality clears a documented gate; unknown quota is never treated as available; every recommendation is persisted and
replayable; benchmark results report quality, latency and memory against the existing deterministic router without
claiming unobserved counterfactual outcomes.

## Users / actors / stakeholders
- M1 Scheduler Core: supplies READY tasks and global free slots, then independently validates and reserves proposals.
- M2 Decision Engine: filters and ranks configured routes, records recommendations and returns opaque route references.
- Existing methodology routing/profile/quota/telemetry code: source of route inventory, eligibility facts and observed outcomes.
- Future M3 executor: will resolve an M2 route reference to its persisted provider/model/profile/effort. M3 is not part of this requirement.
- David: installs Laya locally and reviews the measured results and recommendation records.

## Scope (in)
### US-1 (P1, Must) — Recommend safe routes to M1
As M1, I want M2 to return proposals only for tasks in the current READY request and within `free_slots`, so M1 can
make its existing final reservation decision.
**Acceptance:** M1 can call an opt-in M2 `AssignmentPort` carrying the approved plan hash and structured task evidence;
it can refuse a proposal without M2 changing task state, capacity, plan data or run history.

### US-2 (P1, Must) — Rank existing routes with evidence
As an operator, I want each recommendation to show eligible alternatives, filtered routes, resource state, selection
factors, confidence semantics and policy/model versions, so I can audit why a route was suggested.
**Acceptance:** the saved record includes task and plan identity (including approved plan hash supplied at the M1
adapter boundary), provider, model, profile/account, effort, alternatives, exclusions, rationale and timestamp.

### US-3 (P1, Must) — Use local Laya only when justified
As an operator, I want ambiguous route choices to use a locally loaded Laya checkpoint when its measured output is
useful, with deterministic fallback on low confidence or any model/runtime failure.
**Acceptance:** an obvious low-risk task performs zero inference; an ambiguous task may invoke the selected local
checkpoint; invalid output, timeout, unavailable model, offline load failure or a failed quality gate selects the
deterministic reference policy and records the reason.

### US-4 (P1, Must) — Respect quota, account and project policies
As an operator, I want M2 to exclude routes with exhausted quota, invalid authentication, missing provider/runtime,
project-policy denial or unknown required quota, rather than treating missing information as unlimited capacity.
**Acceptance:** candidate states distinguish `available`, `unknown`, `quota_exhausted`,
`temporarily_unavailable`, `auth_invalid` and `provider_unavailable`; only eligible `available` candidates can win.

### US-5 (P1, Must) — Learn conservatively from actual outcomes
As an operator, I want recommendations to use existing success, error, duration, token and audit measurements without
confusing declared completion with verified completion or subscription usage with API billing.
**Acceptance:** observed, estimated and unknown values remain distinct; sparse data uses a prior/minimum sample rule;
no Laya score is reported as real success probability; missing historical risk/scope/coupling is never imputed.

### US-6 (P1, Must) — Prove behavior and limits
As an operator, I want repeatable module, M1 integration, resilience and quality/resource benchmarks against the
current deterministic router.
**Acceptance:** a versioned fixture benchmark reports selection quality, hard-filter violations, agreement/regret
against its declared reference, repeatability, latency, RSS and CUDA VRAM; real measurements and their limitations
are saved; no unmeasured value is presented as fact.

## Out of scope
- Implementing M3 process/CLI execution, M4 stream monitoring or M5 retry/recovery policy.
- Changing the Planificador schema or rewriting M1 state-machine behavior. The additive M1 assignment-contract fields
  specified below are in scope.
- Training or fine-tuning Laya, or using Claude, Codex, Gemini or any hosted inference service as a decision engine.
- Backfilling telemetry, modifying existing `RUN.json`, changing completed/historical decisions, or migrating legacy runs.
- Charging a provider or invoking a paid inference API for decisions or benchmarks.
- Enabling M2 by default in existing/legacy runs; integration remains explicit and opt-in.

## Requirements
- R1. When M1 calls `AssignmentPort.propose`, M2 shall consider only tasks in that request's READY list, respect `free_slots`, and return proposals without mutating M1 state.
- R2. M1 v1.1.0 shall pass the approved `Plan.sha256` in `AssignmentRequest.plan_sha256`; each `TaskView` shall pass
  `TaskSpec.after` as `dependencies`, `acceptance_criteria`, `verification`, and opaque `meta` including the existing
  Planificador `classification_evidence` field. M2 shall validate these values at runtime; absent or malformed optional
  classification facts lower confidence or trigger conservative rules, while an absent/invalid approved hash rejects
  the recommendation request. Planificador's schema itself remains unchanged.
- R3. M2 shall obtain model/provider/effort and eligible account/profile routes from existing methodology catalogs and router rules, and shall not maintain a second hardcoded provider inventory.
- R4. M2 shall apply deterministic policy, project authorization, credential/runtime state, known quota, cooldown and capacity filters before asking Laya to compare candidates. A quota state of unknown or stale is not available.
- R5. M2 shall avoid inference for deterministic cases. For ambiguous cases, it may ask a local Laya checkpoint to compare only the remaining eligible candidate set; the decision is accepted only when output schema, a threshold calibrated against labeled local decisions, deadline and the held-out quality gate pass. Otherwise it uses the deterministic route.
- R6. M2 shall not map Laya scores or action probabilities directly to real-world success probabilities. Its confidence field shall state its source and semantics.
- R7. M2 shall consume existing `bt_events`/quality measurements and preserve source quality (`verified`, claimed, failed, estimated, unknown); it shall use sample-size safeguards and avoid direct price comparisons between subscriptions and metered APIs.
- R8. Each decision shall have a stable ID and include plan ID, revision and approved SHA-256, task ID, selected route, alternatives, exclusions, factors, rationale, confidence semantics, policy/checkpoint version, candidate/quota snapshot fingerprint and decision time.
- R9. M2 shall persist recommendation records idempotently in its own local state store, outside plan files and historical run records. The request key is SHA-256 over canonical JSON of plan ID/revision/hash, validated task input, content-addressed candidate/quota/telemetry snapshot, policy version and configured checkpoint revision (or null). An exact replay returns the same record; changed inputs produce a new linked recommendation. A unique key and transaction prevent concurrent duplicate records. Neither path creates M1 attempts or rewrites run history.
- R10. Bump the shared M1 contract constant `CONTRACT_VERSION` from 1.0.0 to 1.1.0 and additively extend `AssignmentRequest`/`TaskView` with trailing defaults preserving existing positional constructors: `plan_sha256`, `dependencies`, `acceptance_criteria` and `verification`; M1 maps planner `classification_evidence` through existing opaque `meta`. Existing 1.0.0 callers remain source-compatible, and old events remain accepted; only the default `Event.contract_version` tag changes to 1.1.0, with no event-shape change. M2 fails closed if the approved hash is absent. M1 remains the final authority for atomic reservation and global free slots. Reviewed consumers are the M1 scheduler constructor, FIFO simulator, assignment-port tests, Event serialization/parser, README and sole methodology adapter; each must be updated or verified.
- R11. The local Laya installation shall use an isolated, pinned Python environment, a pinned checkpoint revision and verified hashes where available; after download, inference shall work offline. It shall lazy-load one checkpoint, bound inference time/concurrency/memory, support CUDA when measured viable and CPU fallback when viable.
- R12. Benchmark a versioned, hash-pinned, independently labeled fixture set before inspecting model results. The calibration split must contain at least 100 cases; select the lowest `answer_confidence` cutoff whose retained top-choice accuracy has a one-sided 95% Wilson lower bound no worse than the deterministic policy's accuracy on that calibration split, with at least 50 retained cases. If none qualifies, Laya cannot make live recommendations. The separate held-out split must contain at least 100 cases (at least 20 each across quota/capacity, risk/effort, history, resource/dependency and ambiguous trade-off families). Evaluate every held-out case: the hybrid policy uses the Laya choice only when the task is ambiguous and the calibrated cutoff accepts its output; otherwise it uses the deterministic reference choice. Compare this hybrid's top-choice accuracy with the deterministic reference on the same complete held-out set. Enable Laya only if the hybrid has zero hard-filter violations and its paired accuracy improvement over the reference has a positive lower bound in a 95% paired bootstrap interval (10,000 resamples, fixed published seed). If minimum sample size, independent labels or interval condition is unmet, keep deterministic routing active. Report regret, agreement, latency and memory separately; these are fixture results, not real-world success probabilities.
- R13. The package shall pass its boundary, standalone-copy, CLI, persistence, malformed-input, concurrency, fallback and M1 integration tests, plus existing M1 and Planner regression suites and packaging checks.
- R14. Documentation shall state M1/M2/M3/M4/M5 boundaries, setup/upgrade/offline operation, checkpoint provenance, measured device results, benchmark results and remaining limitations.

## Edge cases & errors
- No eligible candidates: return no assignment and a persisted reason; do not fabricate a route.
- Unknown/stale quota, unreadable quota source, unsupported provider quota, invalid credentials, missing executable or work-only profile denied: filter with a stable status/reason.
- Laya checkpoint absent, download unavailable, offline cache missing, load/OOM/runtime error, invalid output, timeout, low confidence or circuit open: bounded deterministic fallback; never retry in a hot loop.
- Missing/invalid classification evidence, very high risk with small scope, missing historical sample or inconsistent telemetry: retain hard risk floors and mark evidence limitations.
- Candidate count above Laya's supported useful choice range: use a deterministic, order-neutral shortlist/tournament or skip Laya; never silently truncate by candidate position.
- Exact duplicate request/restart: return the record keyed by the canonical input fingerprint. Changed quota, candidate inventory, policy or checkpoint snapshot: persist a new recommendation linked to the same task. Concurrent identical calls: one unique record. An M1 refusal never means M2 changes state or claims dispatch.
- CUDA unavailable/occupied/insufficient memory: choose CPU only if measured viable; otherwise disable inference and use deterministic routing.
- Task text or evidence may contain secrets: persist only bounded, redacted decision context and factor references; never store prompts, credentials, full conversations or raw tool output.

## Constraints
- Existing code inspected: `PLAN-SCHEDULER-CORE-M1.md`, `bt_scheduler_core`, `bt_scheduler_adapter.py`, `bt_planner`, `bt_agents`, `bt_profiles`, `bt_profile_matrix`, `bt_quota_live`, `bt_subscriptions`, `bt_events`, `bt_agy` and `references/agents.md`.
- Shared M1 contract is currently `CONTRACT_VERSION=1.0.0`: `AssignmentRequest` carries plan ID/revision, READY `TaskView`s, global `free_slots` and time; `TaskView` omits plan hash, dependencies, acceptance criteria, verification and `classification_evidence`. M1 enforces free slots and atomic resource claims. The planned common contract v1.1.0 change is additive: append defaulted request/view fields, populate them from the already validated frozen Plan, preserve old positional callers, and leave the state machine and Event wire shape unchanged. Event defaults will advertise v1.1.0; the existing parser continues accepting v1.0.0 events. M2 returns a reference to its persisted route record through the opaque executor label; full details remain in M2.
- Existing profile policy comes from `bt_profiles`/`bt_agents`; live quota reads are available for Claude and Codex, while Antigravity uses the existing `bt_agy` capacity source. M2 will fail closed when a source cannot establish availability.
- Existing attempt telemetry currently contains 137 rows: 95 verified (`done`/`verified`), 16 claimed, 7 verification failures, 7 usage-limit events, 3 failures, 2 escalations, 2 stopped, 1 timeout, 2 partial and 2 integration failures. All 137 have duration; 85 expose tokens. 106 include complexity; none include risk/scope/coupling. These are a baseline snapshot, not a claim of representative or causal model performance.
- Official Laya repository inspected at commit `432312b36714d8889eba405507b37eda25257d9c`; repository license is Apache-2.0 and the current package source identifies version 0.4.7. Its README documents typed `choice`/`score`/`noul` predictions and English, multilingual and typed-decisions checkpoints (421M, 322M and 421M parameters respectively). Its benchmark notes warn that zero-shot typed decisions can be near chance and checkpoints can be over-confident; model scores therefore require local validation.
- Official upstream: [NandhaKishorM/laya](https://github.com/NandhaKishorM/laya); the inspected commit and source files are recorded above so setup and benchmark artifacts can pin the exact provenance.
- Host observed: Arch Linux, Python 3.14.7, NVIDIA RTX A3000 Laptop GPU with 6144 MiB VRAM and driver 615.71.09; measured free memory at inspection was 5857 MiB. No Laya weights or inference were installed/run at spec time.
- All hosted model inference is prohibited for this work. Existing usage/quota readers may query non-inference subscription-usage endpoints only as needed to honor the explicit quota requirement; tests/benchmarks use fixtures and no paid inference.
- Existing unrelated live Maros `RUN.json` is modified by another run and shall remain untouched. No push, deploy, commit or historical run mutation.

## Priorities & phases
- Must: deterministic safe selection/fallback; current catalog/profile/quota integration; auditable persistence; local Laya installation and measurements; M1 port integration; regression suites and honest benchmark.
- Should: use bounded historical quality/latency/token data and document cold-start limitations.
- Won't: M3–M5, Laya training, hosted inference, default activation for legacy runs.

## Timeline & dependencies
- One approved-plan execution in milestones: contract/module → deterministic policy and telemetry → local Laya runtime → M1 adapter → benchmarks/audits/final regressions.
- Local Laya installation and checkpoint downloads begin only after the plan gate. They are user-authorized within the stated no-paid-inference constraint.
- Depends on the current M1 contract and methodology routing/profile/quota/telemetry sources; no external service is required for normal inference after checkpoint download.

## Assumptions
- The explicit `/goal` and detailed prompt settle product scope, actors, limitations and acceptance; no further requirements interview is needed.
- The existing M1 1.0.0 contract cannot satisfy the required evidence and approved-hash audit trail. An additive common contract v1.1.0 is necessary and keeps existing positional construction compatible; the Event payload shape remains unchanged and prior 1.0.0 events remain readable. Contract consumers are enumerated above and validated before integration.
- M1 `free_slots` is the only presently authorized global concurrency capacity exposed to M2. M2 will propose no more than that count; any profile-specific capacity absent from existing contracts remains unknown and cannot be represented as unlimited.
- An M2 route reference in `Assignment.executor` is an acceptable use of the existing opaque field; future M3 must resolve it through M2's public lookup API.
- The model value gate is an evaluation gate, not an assumption that Laya will outperform the existing router. If evidence is insufficient or negative, deterministic policy remains active and the report says so.
- A separately managed local Laya worker process is acceptable if Python/torch isolation makes in-process import incompatible with the methodology runtime; it remains local, bounded and persistent for the Scheduler process lifetime.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- Owner's supplied M2 prompt defines scope, no-paid-inference rule, M1 authority and acceptance; no unresolved product decision remains.
