# REQ-020 contract and ownership freeze

Status: frozen for independent M2 and M5 module work on 2026-10-15, with approved additive T16/T17 API amendments recorded in D-047/D-048 and T20's optional metric-source clarification. The source authority is REQ-020/SPEC and David's approved `SOURCE-PLAN.md`; M5's existing authority is REQ-019/SPEC and D-041.

## Public boundaries

| Boundary | Frozen contract | Owner |
|---|---|---|
| M1 ↔ M2 | Existing `AssignmentPort.propose(AssignmentRequest) -> Sequence[Assignment]`, approved `plan_sha256`, READY tasks and global `free_slots`; M1 validates every proposal. No new M1 retry field is required for baseline quota rerouting. | M1 integrator |
| M2 public API | Preserve per-task `DecisionRequest`/`DecisionRecord`; evolve M2 additively to 1.2.0 for quota windows, correlated performance events, temporal evaluation and batch decisions. Read legacy decision records 1.0.0 and 1.1.0. Expose typed batch planner inputs/results and the ledger's batch-decision store. | M2 |
| M2 local persistence | Current decision-ledger schema 3 includes immutable learning snapshots (introduced in schema 2) and batch decisions. Writable schema-1 files migrate additively through 2 to 3; writable schema-2 files add only the batch table. Read-only schema-1/2 files remain readable at their existing capability. No existing decision or snapshot row is rewritten. | M2 |
| M1 ↔ M5 | Preserve M5 D-041 `RecoveryPort`, `FailureContext`, `RecoveryProposal` and M1 authority. M5 returns retry/wait/block plus advisory rationale; M1 verifies termination and authorizes any retry. | M5 module; M1 integrator for shared wiring |
| M1 retry → M2 | M1 requests a fresh assignment after an approved retry; M2 re-reads current cached quota and normal eligibility. No RPC/import from M5 to M2. Route-avoid/retry context is unsupported unless M1 adds a separately approved, versioned field; no hint is inferred from free text. | M1 integrator |
| M2 ↔ M4/M6 | Optional validated observation inputs only. M2 package and M1/M2 adapters stay importable and deterministic when these modules or quality verdicts are absent; absent or unknown measurements remain unavailable. | M2 adapter owner |

## Data invariants

- Effective provider account is represented by an opaque `account_ref`; aliases do not multiply quota.
- The methodology adapter enumerates distinct `(model, effort)` routes from `bt_agents.model_for` at the task's minimum tier and every stronger supported rung. The existing `bt_agents.pool_for` remains the authority for project/work-only/runtime eligibility and effective-account alias deduplication; quota and history are then read for each exact route. Only an exact `(profile, provider, model, effort)` match to `bt_agents.candidates` receives a baseline rank.
- `m2-route-policy-v1` applies lexicographic objectives only after `rank_candidates()` has removed hard-ineligible routes. A configured risk quality floor requires a matching T10 `ContextualHistoryAssessment` with at least five correlated verified samples; its Wilson lower bound and interval width remain descriptive, never a future-success probability. No numeric risk floors are enabled by default, and absent quality retains the existing baseline. Remaining order is maximum pressure across required windows, measured duration, relative cost only when every eligible route reports the same comparable scale, risk reserve, an upcoming reset within 30 minutes only when it belongs to the most restrictive window, then router rank and route ID. The policy version and order are immutable for this policy version; no weighted sum may override hard filters.
- Preserve each provider- and model-scoped window independently. All relevant fresh windows must permit selection; an imminent short reset cannot override an exhausted weekly/model window.
- Use cached observations only. `observed_at <= now < valid_until` is necessary for fresh evidence. Missing reset metadata remains unknown unless that source explicitly permits an unknown reset while the observation TTL is still fresh.
- M2 1.2.0 quota demand keeps provider-reported tokens and quota percentage points as separate units. Attribute account-window deltas only for one known active task, a known unchanged reset, and explicit evidence that no external usage occurred; otherwise return `attribution_unknown`. Estimates match exact account/route/context/source/unit, expose sample count and empirical bounds, and carry a bounded TTL without claiming calibrated confidence.
- Batch quota assessment groups candidate aliases by `(provider, account_ref)`, requires every declared base and model-specific window, and reports route eligibility read-only. A missing, stale, unknown or exhausted required window excludes that route; profile aliases never sum or reserve account capacity, and M1 remains the final authority.
- Never convert usage percentages to tokens or dollars. Quota deltas are assigned to a task only with comparable before/after observations and no concurrent external use or reset; otherwise attribution is unknown.
- A verified outcome requires the independent acceptance evidence and matching plan/revision/task/attempt/decision/route identities. Claims and uncorrelated historical rows are not positive training labels.
- The M2 `PerformanceEvent` normalizer reads minimal M1 attempt, M2 decision and M1-applied verdict projections. M1 must report `applied` or `duplicate`, an independent verifier, non-synthetic sources and the M1-recorded application timestamp; only exact PASS/FAIL identity matches are history-eligible, and PASS requires its acceptance evidence. Stale/invalid claims, cancellations, infrastructure failures and conflicts stay unknown or non-learning outcomes. The event contract is additive under API 1.2.0 and writes neither M1 nor M6 state.
- Contextual history consumes those correlated events plus a separate allowlisted context map. It reports unique attempts, verified PASS/FAIL samples, non-quality outcomes, coverage and a descriptive Wilson interval at exact-context, complexity-class, task-family and route levels. The first level with at least five verified samples exposes a Beta(2,2)-shrunk ranking feature; otherwise M2 retains the existing deterministic baseline. Infrastructure failures do not become quality failures, and the interval or shrunk value is not a future-success probability or calibration claim. Coarse legacy `bt_events` remain outside correlated quality history; T20's validated M4 metrics are measurements, not inferred PASS/FAIL labels.
- Temporal evaluation uses only records with `application_status=applied` and a valid M1 `applied_at`. It partitions and replay-reduces source records across all routes before filtering the selected route, so conflicting route projections cannot become verified outcomes. Records without a valid M1-applied timestamp do not enter training/evaluation; future counts and rates remain descriptive, and the source fingerprint contains only reduced pre-cutoff events and contexts.
- Persisted learning snapshots bind normalized event and context-identity hashes, route, target context, aggregate, policy version and learning cutoff. They store no raw event projections or task identities, allow up to 10,000 rows of at most 32 KiB each, and reject updates, deletes or writes at capacity. Exact fingerprint replay returns the original payload/timestamp; schema-1 read-only ledger access remains available after schema-2 code ships.
- The schema-3 batch-decision table is append-only and content-addressed by normalized task requests, route-policy evidence/configuration, explicit account-concurrency rows and the algorithm version. It retains the selected assignments/reasons, route exclusions and stable unassignment reasons, but not task prose, raw policy evidence or provider output. It allows at most 10,000 plans of 2 MiB each; exact replay returns the first checksum-verified plan, and changed inputs create a new record. Updates, deletes and pruning are rejected.
- M2 may persist redacted batch-decision evidence but cannot reserve capacity durably or change M1/M3 state.
- T17's `compare_shadow_batch()` is opt-in and returns an immutable in-memory comparison of the deterministic READY-order baseline and T15 batch planner over the same normalized requests, evidence, policy and capacity. Its stable difference codes and SHA-256 fingerprints make the result replayable; disabled mode returns before inspecting comparison inputs. The comparison is not written to the schema-3 ledger and performs no dispatch, reservation, task-state change or provider call; M1 remains final authority.
- T20 consumes only validated M4 `MetricSample` records whose provider, profile, model, metric name, unit and comparability key match exactly. The M2 adapter imports the optional M4 contract lazily only when a non-empty metric collection is supplied; no M4 module is required for M1/M2 import or the empty-evidence path. Provenance is preserved, unknown quota values stay `None`, and metrics do not become quality verdicts.

## File ownership

| Files / area | M2 | M5 | Single integrator |
|---|---|---|---|
| `skill/scripts/bt_scheduler_decision/**` | Write | Read only | No concurrent edits |
| `skill/scripts/bt_scheduler_decision_adapter.py` | Write | Read only | No concurrent edits |
| `skill/scripts/bt_scheduler_recovery/**` | Read only | Write | No concurrent edits |
| `skill/scripts/bt_scheduler_recovery_adapter.py` | Read only | Write | No concurrent edits |
| `bt_scheduler_core/**`, `bt_scheduler_adapter.py`, `bt_scheduler_executor_adapter.py`, shared schemas, M4 wiring, `pyproject.toml` | Propose only | Propose only | Write once after both module contracts pass |
| M2/M5 package tests | Own suite | Own suite | No cross-edits |
| M1–M5 E2E, shared packaging tests and shared requirement log/decision files | No concurrent edits | No concurrent edits | Integrator |

M2 implementation lives in `/home/david/dev/metodologia-m2` on `feat/scheduler-m2-learning-quota`. M5 implementation lives in `/home/david/dev/metodologia-m5` on `feat/scheduler-m5-recovery-manager`; its isolated package baseline passed 33 tests before implementation started. Existing dirty M4/M5 files in the primary worktree remain preserved. No shared files are to be copied or merged early.

## Integration gates

- P0: inventories, this ownership matrix and module contracts are frozen before parallel implementation.
- P1: isolated M2 and M5 unit/contract suites pass without importing the sibling module.
- P2: one integrator applies only necessary shared wiring, preserving M1 ownership and M3 compatibility.
- P3: fake-backed M1/M2/M3/M5 E2E covers exhausted A → eligible B, no capacity, duplicate/tardy evidence and wait/block.
- P4: accepted metrics use real correlated verification; unknown/ambiguous usage remains explicitly uncovered.

## Experiment gate

The real-provider experiment is not part of offline tests. Do not start provider agents or consume subscription quota until David explicitly authorizes the bounded run (8–12 tasks, 2–3 agents, 2–4 hours at most, controlled failures without intentional exhaustion). A missing authorization leaves T24 and dependent closeout evidence pending.
