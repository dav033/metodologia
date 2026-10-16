# REQ-024 PLAN.json consumer and telemetry audit

Captured for T3 before any PLAN.json code/contract change. All findings are code observations, not product acceptance.

## Contract path and consumers

| Boundary | Current behavior | Change/compatibility constraint |
|---|---|---|
| Planner contract — `skill/scripts/bt_planner/contract.py` | Reads schema major 1; enumerates current task/verification fields and rejects scheduling/assignment keys. Canonicalization preserves named-key order and sorts additional fields; schema 1.1.0 frozen bytes must remain stable. `sync.py` compares known Markdown/JSON fields; prose `covers:` metadata is not machine-checked. | Additive 1.2.0 must be version-gated. Preserve 1.1.0 golden canonical bytes, existing frozen revisions and parser/supervisor parity. |
| Methodology adapter — `skill/scripts/bt_plan_adapter.py` | Only supported import boundary into `bt_planner`; checks publishability, binds exact frozen PLAN.json and blocks launch on drift/invalid data. | Keep dependency direction and existing launch error behavior. Do not create a second planner contract implementation. |
| M1 — `skill/scripts/bt_scheduler_core/plan.py` | Accepts major 1, validates exact approved SHA, reads execution fields, and forwards a fixed `OPAQUE_KEYS` list as task metadata. Current list omits `kind` and verification categories. | Add `kind` only through the versioned migration and preserve exact hash/rollback semantics; M1 continues to own task state and authorization. |
| M2 — `skill/scripts/bt_scheduler_decision_adapter.py` | `task_facts` currently infers kind from the task title, then sends classification to M2. REQ-025 routing reads complexity/scope/coupling/duration and account/quota evidence; it does not require Planner to choose a model or provider. | T11 must pass explicit supported kind into M2 without changing its routing/quota owner boundary. If absent on legacy plans, retain title inference. |
| M6 — `skill/scripts/bt_scheduler_quality/contracts.py`, `identity.py` | `VerifyRequest` accepts exact allowlisted root fields. `VerificationSpec` serializes only type/value/purpose/created_by/expected; `input_hash` hashes that typed serialization. A new evidence category would be rejected or dropped unless projected into the typed contract. | Add and hash category metadata while preserving the runner verdict policy and old requests. Compatibility tests must prove old 1.1.0 inputs and frozen hashes remain valid. |
| Plan parser and report — `skill/scripts/bt_planner/markdown.py`, `sync.py`, `quality.py` | Markdown task-line parsing handles current fields; unrecognized metadata such as `covers:` is not cross-checked against PLAN.json. The report checks DAG/resources, task evidence and command verification. | Add traceability/interface report fields without changing legacy task-line interpretation or the outer DAG contract. |
| Scheduler and plan lifecycle — `bt_launch.py`, `bt_runstate.py`, `bt_scheduler_core/plan.py` | Approval freezes PLAN.json hash; M1 requires that hash, and run state keeps plan identity/revision instead of copying the plan. | A new minor version needs old/new consumer matrix, reversible rollout and explicit refusal from incompatible older consumers. |
| Provider profile/install — `bt_profiles.py`, `bt_agents.py`, `bt_launch.py`, `install_agents.py`, `bt_hooks.py` | Current launcher registry has 7 profile IDs and 5 effective accounts across Claude, Codex and Antigravity. Planner is generated from one shared source for the currently configured accounts under D-055. Hooks have no Planner-specific semantic quality gate. | Use native profiles where available and a narrow adapter otherwise. Caller-selected provider/account/model/effort passes through; no fallback. Existing marker-protected installer is the only profile writer. |

## Planning history and telemetry boundary

- Local `bt_events` has a cross-project, append-only attempt log with requested route, task kind/outcome, elapsed seconds and provider-reported usage where present. The read-only T3 snapshot found 153 rows: 153 with elapsed time, 94 with token totals, 0 with a reported model, 80 verified, and 123 with unknown origin. These totals cover all projects; they are not Planner-only training evidence.
- `bt_events` distinguishes requested and reported model. This snapshot had no `reported_model`; model-attributed quality must remain unknown rather than treating requested model identity as verified. The log also mixes verified, claimed/unverified, failures, timeouts, stopped work and unknown provenance.
- M2 history in `bt_scheduler_decision/history.py` excludes synthetic events, tracks attempt/verified/claimed/failure counts, durations and token sample counts, and marks quality observed only after at least five verified samples. It provides contextual fallback levels and explicit reasons; sparse or incomparable data stays unknown.
- M4 exposes validated, bounded metric snapshots through `bt_scheduler_monitor_adapter.read_metric_snapshots`. M2 accepts only validated `MetricSample` values and filters by provider, effective profile, model, metric name, unit and exact comparability key. It is a read path; it does not refresh quota or invoke a provider.
- M2 performance events/learning snapshots are a separate deterministic history with versioned context and append-only storage. Planner T13 must consume only a read-only projection of verified comparable fields; it must not duplicate M2 route selection or infer account capacity.
- T1–T3 do not establish observed Planner quality improvements, cross-provider parity, or product acceptance. The accepted T13 fallback is an `unknown`-only projection when adequate records do not exist.

## Verification

`cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` — exit 0; 21 tests passed in 0.321 s. The suite covers the single adapter import boundary, handoff/launch freezing, run-state binding, and PLAN.md parser parity across real plans. It is integration evidence for the methodology boundary, not a model or product-quality result.

## Versioned change decision

Proceed only with the already-approved additive 1.2.0 proposal after T4 golden fixtures and T5 consumer audit are complete. Required migration tests: old plans still load unchanged; explicit kind reaches M2; evidence category survives M6's typed input hash; incompatible old readers fail closed; rollback returns to matching 1.1.0 consumers and keeps all frozen hashes unchanged. No Pictures repository source or canonical REQ-017 file was changed during this audit.
