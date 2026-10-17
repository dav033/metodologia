---
req: REQ-024
status: in-progress
created: 2026-10-16
---
# Plan — REQ-024 — Planner V2 quality, provider-neutral launch and reproducible benchmark

Planner-generated plan revised by the coordinator after the owner clarified the provider-neutral launch requirement. The owner approved revision r1 on 2026-10-16; the matching PLAN.json is frozen. Implementation has not yet launched. The latest structural check and report are recorded in RUN.md.

## Approach
Evolve the existing V2 Planner instead of restoring V1, and make the same Planner role invocable through each locally configured AI runtime/account. The work proceeds in these steps:
1. Pin a measured baseline and classify all evidence.
2. Fix the contract boundary with golden hashes before any code edit.
3. Add an additive, version-gated `PLAN.json` 1.2.0 so requirement coverage and interface contracts become machine-checked rather than prose.
4. Add verification-honesty findings that match the real M6 acceptance rule.
5. Revise the Planner profile and private skills so the shared role does not pin a provider, account, model or effort.
6. Expose the shared Planner through provider-native profiles or a thin invocation adapter, passing the caller's selections through.
7. Expose observed planning history only through a read-only projection that keeps sparse data unknown.
8. Prove Planner quality changes with a pre-registered, hash-frozen, matched benchmark. Model quality is assessed on the pinned reference run only; cross-model quality parity is out of scope.

`bt_planner` stays dependency-free and reached only through `bt_plan_adapter.py`. M1 keeps state, M2 keeps route/model/account/effort/quota choices, M3 keeps processes, M4 keeps observation and M6 keeps verification.

## What was inspected
- Requirement: `SPEC.md` and the template `PLAN.md` of REQ-024.
- Planner profile and private skills: `skill/agents/planner.md`, `skill/agents/planner/skills/{socratic-elicitation,wbs-dag-decomposition,plan-mermaid-view,adversarial-plan-review}/SKILL.md`.
- Contract and module: `skill/references/plan-contract.md`, `skill/scripts/bt_planner/{README.md,contract.py,evidence.py,quality.py,sync.py (lines 110–340),markdown.py (lines 45–159),data/plan.schema.json}`, `skill/scripts/bt_planner/tests/test_scenarios.py`, `tests/scenarios/REQ-902-audit-trail/EXPECT.json`, and the listing of all `bt_planner/tests` files.
- Adapter: `skill/scripts/bt_plan_adapter.py`.
- Provider launch and account surfaces: `skill/scripts/bt_profiles.py`, `bt_agents.py`, `bt_launch.py`, and `install_agents.py`; `profiles list` currently reports Claude, Codex and Antigravity runtimes with seven profile IDs and five effective account identities after alias deduplication.
- Install and hook paths:
  - `skill/scripts/install_agents.py`, `install.py` (grep), `skill/scripts/tests/test_install.py`, `skill/scripts/bt_hooks.py` (grep: no Planner reference).
  - Installed copies: `~/.claude/agents/planner.md` present, `~/.codex/agents/planner.toml` present, `~/.claude-work/agents/` without `planner.md`; no Antigravity-native Planner profile is generated.
- Module boundaries and telemetry:
  - M1: `bt_scheduler_core/README.md`, `bt_scheduler_core/plan.py`.
  - M2: `bt_scheduler_decision/README.md` (lines 1–160), `bt_scheduler_decision_adapter.py` (function list).
  - M4: `bt_scheduler_monitor/README.md` (grep).
  - M6: `bt_scheduler_quality/README.md`.
  - Telemetry tests: `skill/scripts/tests/test_agents.py`.
- Benchmark precedent: `skill/scripts/bt_scheduler_benchmark.py`, `skill/scripts/bt_scheduler_bench_quality.py` (headers).
- REQ-017 references:
  - Pictures `requirements/REQ-017-activity-aware-guided-chat-decoration-re/PLAN.md` (V1-labelled, edited).
  - `artifacts/REQ-017-planner-rerun-opus55-high-20261016/{RUN.md,PLAN.md}` (V2 rerun).
  - Delegation records `~/bitacora/.state/delegations/D-20261016-090752-bc5d/{TASK.json,OUTCOME.json}`; `RESULT.json` was inspected only by grep.
  - Methodology log `2026-10/W3/2026-10-16.md` (lines 104–173) and `DECISIONS.md` (D-050…D-053 headings).
- Not opened (named only after Glob):
  - `prompt.txt` and `session.log` of the V1 delegation.
  - The bodies of `skill/scripts/tests/test_plan_integration.py`, `test_isolation_plan_parse.py`, `test_scheduler_*`, `bt_cli_plan.py` and `bt_events.py`.

## Findings

### Implementation facts (code read)
- F1. Schema 1.1.0 already allows extra fields except scheduling keys (`contract._scan_forbidden`, README "Extra fields are allowed"). `planner.md` nevertheless forbids adding fields the schema does not define. So requirement coverage cannot be encoded in PLAN.json today without either a versioned contract change or an instruction violation.
- F2. The PLAN.md parser keeps unknown task-line fields and silently ignores them (`markdown.parse_task_line`). The `covers:` field suggested by the requirement template is therefore read by nothing.
- F3. The key-name scanner rejects any key containing tokens such as `parallel`, `concurren…`, `agent`, `model`, `executor` or `assign` at any depth. New field names must avoid them; this plan uses `interfaces`, `producer_task` and `consumer_tasks`. Free text promising concurrency safety is also rejected (`evidence.PARALLEL_CLAIM_RE`).
- F4. `contract.canonicalize` places named keys first and sorts every other key, deep-sorted for schema ≥ 1.1.0. Extra keys can therefore have stable canonical ordering across Planner readers, but identical hashing alone does not establish execution compatibility: an old M2 adapter ignores explicit `kind`, and M6 rejects unknown verification fields. Rollback must restore a compatible approved revision and consumer set.
- F5. The current M1 loader (`bt_scheduler_core/plan.py`) accepts any `1.x.y` and validates only the fields it uses. It forwards only the current `OPAQUE_KEYS` as M2 metadata; T11 must add `kind` to that explicit allowlist, while leaving other additive fields invisible to M1/M2.
- F6. M6 checks are strict:
  - It accepts only the Planner verification shape.
  - A command covers a criterion only when its `purpose` exactly equals that criterion string.
  - Manual items are `CHECK_MANUAL`.
  - An uncovered criterion cannot PASS (the task stays NEEDS_REVIEW).
  - Commands are parsed without a shell; only a leading `cd <relative> &&` is allowed.

  `bt_planner` checks none of this.
- F7. `quality.py` already refuses unordered tasks that share a path or resource while one claims `coupling: low`. It warns on shared unordered pairs, unconsumed results and redundant edges, and reports critical path and widest level.
- F8. Tests and installation of the Planner profile:
  - No test covers `planner.md` or its four skills.
  - `install_agents.py` installs only `agents/*.md` and defaults to `~/.claude/agents`.
  - `install.py` targets every account directory, but `~/.claude-work/agents/planner.md` is absent: installation has drifted.
- F9. `bt_hooks.py` has no Planner-specific path. SessionStart context injection is generic. It is a benchmark confound, not a demonstrated planning defect, so no hook change is planned.
- F10. M2 history is strict:
  - It counts only verified, M1-applied PASS/FAIL results.
  - It needs 5 verified samples (`bt_agents.MIN_SAMPLES`) and is route-scoped.
  - The README states that validated M4/M6 source wiring "remains a later adapter task".
  - Comparable planning history may therefore not exist yet.
- F11. A hash-checked frozen corpus with a manifest marker set before the first model call (`frozen_before_first_laya_call`) already exists as a pattern in `bt_scheduler_benchmark.py`.
- F12. `bt_planner/tests/scenarios/` holds 9 SPEC/PLAN/EXPECT cases. They are useful benchmark inputs, but they become contamination if a benchmarked Planner can read their PLAN files.
- F13. Provider launch inventory: `bt_profiles.LAUNCHABLE`, `bt_agents.PROVIDERS` and `bt_launch.AGENTS` currently include Claude, Codex and Antigravity. `profiles list` reports seven profile IDs and five effective account identities after alias deduplication. The Planner installer generates Claude/Codex files only; Antigravity needs a runtime invocation path.
- F14. The canonical `planner.md` pins `model: opus` and `codex_effort: high`, so the profile itself is not currently model-neutral even though account/model routing exists outside the Planner.

### Configured instructions (not executed behaviour)
- The Planner profile (`model: opus`, `codex_effort: high`) and the four skills are adapted from third-party MIT sources. They require exact paths, observable acceptance, `after` edges, `bt_planner check` before returning, and no execution choices. T12 removes runtime defaults from the shared role; Opus remains only a fixed benchmark reference.
- D-053 keeps these resources exclusive to the Planner profile.

### Observed outputs (recorded by earlier sessions, not re-run here)
- V2 rerun (`RUN.md`):
  - Run conditions: Opus 5.5 high, tools Read/Grep/Glob, about 7 minutes. The model itself stated that `bt_planner check` was not run.
  - A coordinator later ran the check: exit 0, with one warning that T2.1 and T3.1 share `event-structure-policy` without an `after` edge.
  - Report: 7 tasks, 400 minutes, 295-minute critical path.
  - The rerun found the «Arco orgánico» `arco`/`arco_asimetrico` collision and reused `ESTRUCTURAS_SIN_VISTA_3D`.
  - It read the earlier PLAN.md, so it is not independent of V1.
- V1 delegation (`OUTCOME.json`): status `claimed`, `verified: null`, rc 0, 190 s. Run conditions (`TASK.json`): `kind: research`, opus/high, profile `claude-work`, worktree mode.
  - Its task text supplied pre-digested evidence from `D-20261016-085733-24b5`.
  - The raw plan is in `RESULT.json`.
  - The original 2026-10-16 log reports that this raw V1 plan's M3 only reordered existing cards and its T3.1 persisted the event on the widget. This is to be confirmed in T2.

### Later coordinator/reviewer edits and implementation activity
- The live Pictures `PLAN.md` (`status: done`) contains later material that is not model output:
  - Coordinator approvals that were later retracted.
  - The revised M3 (exact cards, no persisted field).
  - Rulings.
  - Verification results from an implementation in worktree `req-017-v2`.
  - A progress log.
- Implementation delegation `D-20261016-093409-9805` was stopped with partial changes.

### Proposed changes (this plan)
- Schema 1.2.0 (below).
- Verification-honesty findings.
- Revised provider-neutral Planner profile and skills.
- A narrow invocation adapter that exposes the shared Planner through each configured provider and preserves caller-selected account/model settings.
- Marker-protected installation and launch-only smoke checks for all configured effective account profiles; no cross-model quality scoring.
- Planning-history projection.
- Installation fix.
- Benchmark harness and matched runs.
- Final REQ-017 draft.

V1 limitation: the raw plan is recoverable in `~/.state/delegations/D-20261016-090752-bc5d/RESULT.json`, along with its delegated prompt and session log. That run used generic Claude Work with Opus 5.5 high, a follow-up prompt containing pre-digested evidence from D-20261016-085733-24b5, `bypassPermissions` and a broad tool set, plus injected SessionStart project context. No runnable V1 Planner profile or pinned repository SHA was recorded. Score the output only as retrospective evidence; do not include it as a controlled arm.

## Global constraints
- No change to Pictures source, its canonical REQ-017 files, approval state or revisions. REQ-017 is a benchmark input only.
- `bt_planner` stays standard-library only and isolated (`tests/test_boundaries.py`, `tests/test_isolation.py`). Only `bt_plan_adapter.py` imports it (`tests/test_plan_integration.py`).
- The caller/local launcher selects provider, account, model and effort; the Planner never chooses them or worker count, quota or run state. The Opus 5.5 high condition in T18/T21 is the fixed quality-benchmark reference from SPEC R14/R11, not a runtime requirement. Record it in run metadata, never in PLAN.json.
- No new third-party dependency. No global hook or settings change. No commit, push or merge without a separate request. Never discard local edits.
- Benchmark records store hashes, identifiers, bounded evidence and metrics. They never store raw conversation prompts, private messages or secrets.
- Planned tests are work (`created_by`) until they exist and pass. Passing tests are not product acceptance.

## Contract 1.2.0 proposal (R3, R5, R7, R8, R9)

### Fields (additive)
| Field | Where | Shape | Rule (1.2.0 only) |
|---|---|---|---|
| `requirements` | top level | `["R1", …]`, ids `^[A-Z][A-Z0-9]{0,7}-?[0-9]{1,4}$`, unique | must equal the ids listed under the `Requirements` heading of `spec_ref` (list items starting with `<id>.` or `<id>:`); a SPEC without that heading gives a warning, not an error |
| `covers` | task | non-empty list of ids from `requirements` | unknown id → error; empty → orphan work error |
| `kind` | task | enum from the current M2 `bt_agents.KINDS` vocabulary (`implement`, `test`, `docs`, `audit`, `research`) | declares the work kind M2 already routes; when absent in legacy 1.0.0/1.1.0 plans, retain title inference; no provider/model or specialist-tool eligibility is inferred |
| `interfaces` | top level, optional | `[{id: "IF-n", title, owner, producer_task, consumer_tasks[], integration_task?, inputs[], outputs[], invariants[], integration_criteria[]}]` | tasks exist; producer ∉ consumers; each consumer has the producer as a transitive `after` ancestor, or `integration_task` exists and has the producer and every unordered consumer as ancestors; all text lists non-empty; key names pass the scheduling-token scan |
| `category` | verification item | enum `static`, `functional`, `integration`, `regression`, `product` | required for each verification item in 1.2.0; describes what the evidence demonstrates, separately from `type` (`command`/`manual`); M6 accepts it as metadata without changing its execution verdict |

Derived and reported, but not stored:
- Requirement → tasks → milestones → verification mechanisms (`command` existing, `command` with `created_by`, `manual`) and categories (`static`, `functional`, `integration`, `regression`, `product`).
- A warning for a requirement whose covering tasks have only manual verification.
- Report the categories used for each requirement; the Planner review flags product claims supported only by lower-level checks.

### Consumers and compatibility
| Consumer | Uses | Effect of 1.2.0 |
|---|---|---|
| `bt_planner` validate/check/report/init/compat | all | new checks only when `schema_version ≥ 1.2.0`; 1.0.0/1.1.0 results unchanged |
| `bt_plan_adapter.py` (approve, handoff, launch, resume) | `check`, `bind_approved` | pass-through; gate behaviour unchanged |
| M1 `bt_scheduler_core/plan.py` | ids, after, repository, paths, resources, criteria, verification, opaque task metadata | accepts `kind` as opaque task metadata; run state and ordering remain unchanged |
| M2 `bt_scheduler_decision_adapter.py` | task title and current classification metadata | uses valid explicit `kind`; legacy plans keep title inference; tier, candidate eligibility, route and quota policy remain M2-owned |
| M6 `VerifyOrder` | acceptance criteria, verification | validates and preserves the 1.2.0 `category` enum in its typed request and input hash; command execution and PASS/NEEDS_REVIEW behavior remain unchanged |
| Supervisor PLAN.md parser (`bt_runstate`) | task-line grammar | `covers:` already tolerated; parser parity test must stay green |
| Frozen `plan-revisions/` | canonical bytes, sha256 | existing 1.0.0/1.1.0 revisions remain byte-identical; new 1.2.0 revisions get their own canonical hash |

T3 must confirm this table, including any web review UI reader. T5 records the confirmed version.

### Migration
Existing 1.0.0/1.1.0 plans and frozen revisions keep working with title-based kind inference and no verification category. New 1.2.0 plans require updated M1/M2/M6 consumers: T11 must prove the explicit `kind` reaches M2 and the `category` survives M6 contract validation. `init` emits 1.2.0 with `requirements` derived from the SPEC and empty `covers` reported as gaps. `compat` reports whether the installed Planner and Scheduler/M6 consumers support 1.2.0; launch fails closed when they do not.

### Rollback
Rollback selects the last compatible approved 1.1.0 revision and restores the matching Scheduler/M6 consumer set. Do not load a 1.2.0 revision with an older M2/M6 adapter: it would lose explicit kind routing or reject verification metadata. Down-conversion is allowed only when the explicit kind matches legacy title inference and dropping categories is recorded; otherwise retain the updated consumers or stop the run. Existing frozen revisions and their hashes are never rewritten.

## Tasks

### M1 — Diagnostic baseline and evidence classification
- [x] T1 — Record the pre-change baseline and inventory local AI profiles · repo: skill · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` · resources: req024-baseline-record · covers: R1, R2, R13, R15
- [x] T2 — Classify Planner sources and REQ-017 artifacts by evidence type · repo: skill · after: T1 · resources: req024-diagnosis-record · covers: R1, R2, R11
- [x] T3 — Audit PLAN.json consumers, planning telemetry and local Planner launch interfaces · repo: skill · after: T1 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` · resources: req024-consumer-audit · covers: R2, R8, R9, R15

### M2 — Versioned contract decision and compatibility fixtures
- [x] T4 — Freeze golden canonical serialisation fixtures before contract edits · repo: skill · after: T1 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_contract_golden.py` · files: skill/scripts/bt_planner/tests/test_contract_golden.py, skill/scripts/bt_planner/tests/golden · resources: plan-canonical-serialisation · covers: R8, R13
- [x] T5 — Confirm the versioned 1.2.0 contract change record against the audit · repo: skill · after: T2, T3 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_scheduler_core/tests -p test_plan.py` · resources: plan-json-contract · covers: R8

### M3 — Deterministic plan-quality gate (schema 1.2.0)
- [x] T6 — Add version-gated 1.2.0 validator extension points for traceability, interfaces and evidence labels · repo: skill · after: T4, T5 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` · files: skill/scripts/bt_planner/contract.py, skill/scripts/bt_planner/traceability.py, skill/scripts/bt_planner/interfaces.py · resources: plan-json-contract, plan-canonical-serialisation · covers: R3, R7, R8, R9, R10
- [x] T7 — Implement requirement traceability checks for schema 1.2.0 · repo: skill · after: T6 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_traceability.py` · files: skill/scripts/bt_planner/traceability.py, skill/scripts/bt_planner/sync.py · covers: R3, R6
- [x] T8 — Implement interface contract checks for schema 1.2.0 · repo: skill · after: T6 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_interfaces.py` · files: skill/scripts/bt_planner/interfaces.py · covers: R6, R7
- [x] T9 — Add verification-category, honesty and M6 criterion-coverage findings · repo: skill · after: T6 · verify: `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_verification_quality.py` · files: skill/scripts/bt_planner/quality.py · covers: R5, R6, R10
- [x] T10 — Integrate 1.2.0 fields into schema, example, report, PLAN.md sync and docs · repo: skill · after: T7, T8, T9 · verify: `cd skill/scripts && python3 -I -m unittest discover -s bt_planner/tests` · files: skill/scripts/bt_planner/data/plan.schema.json, skill/scripts/bt_planner/markdown.py, skill/references/plan-contract.md · resources: plan-json-contract, plan-md-grammar · covers: R3, R5, R7, R8, R9
- [x] T11 — Integrate 1.2.0 task kinds and verification categories across M1/M2/M6 · repo: skill · after: T10 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_contract_compat.py` · files: skill/scripts/bt_scheduler_core/plan.py, skill/scripts/bt_plan_adapter.py, skill/scripts/bt_scheduler_decision_adapter.py, skill/scripts/bt_scheduler_quality/contracts.py, skill/scripts/bt_scheduler_quality/README.md, skill/scripts/bt_scheduler_quality/tests/test_contracts.py, skill/scripts/tests/test_plan_contract_compat.py · resources: plan-json-contract · covers: R8, R9, R13

### M4 — Provider-neutral Planner invocation, history and installation
- [x] T12 — Update the Planner profile and private skills for the new gates and provider neutrality · repo: skill · after: T10, T13 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_planner_profile.py` · files: skill/agents/planner.md, skill/agents/planner/skills · resources: planner-profile · covers: R3, R4, R5, R6, R7, R9, R10, R15
- [x] T13 — Add a read-only planning-history projection that keeps sparse data unknown · repo: skill · after: T3 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_history.py` · files: skill/scripts/bt_plan_history.py · resources: planning-history-projection · covers: R9
- [x] T14 — Add a provider-neutral Planner invocation adapter · repo: skill · after: T12 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_planner_runtime.py` · files: skill/scripts/bt_planner_runtime.py, skill/scripts/tests/test_planner_runtime.py · resources: planner-profile, planner-runtime · covers: R15
- [ ] T15 — Install and smoke-test Planner across configured local AI profiles · repo: skill · after: T14 · verify: `python3 skill/scripts/bitacora.py profiles list` · files: ~/.claude/agents/planner.md, ~/.claude-work/agents/planner.md, ~/.codex/agents/planner.toml, ~/.codex-luis/agents/planner.toml · resources: planner-profile, planner-runtime, configured-ai-accounts · covers: R2, R14, R15

### M5 — Reproducible planning benchmark
- [ ] T16 — Build the planning benchmark harness and pinned rubric · repo: skill · after: T11 · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_bench.py` · files: skill/scripts/bt_plan_bench.py, skill/scripts/plan_bench · resources: benchmark-store · covers: R10, R11, R12
- [ ] T17 — Freeze the benchmark corpus, oracles and matched run configurations · repo: skill · after: T15, T16 · verify: `python3 skill/scripts/bt_plan_bench.py verify /home/david/bitacora/metodologia/artifacts/REQ-024-benchmark` · resources: benchmark-store · covers: R11
- [ ] T18 — Execute the matched benchmark runs within the resource cap · repo: skill · after: T17 · verify: `python3 skill/scripts/bt_plan_bench.py score /home/david/bitacora/metodologia/artifacts/REQ-024-benchmark` · resources: benchmark-store · covers: R11, R12
- [ ] T19 — Collect blind reviews and score historical REQ-017 outputs retrospectively · repo: skill · after: T18 · verify: `python3 skill/scripts/bt_plan_bench.py verify --reviews /home/david/bitacora/metodologia/artifacts/REQ-024-benchmark` · resources: benchmark-store · covers: R1, R10, R11, R12
- [ ] T20 — Publish the benchmark report under the no-superiority rule · repo: skill · after: T19 · verify: `python3 skill/scripts/bt_plan_bench.py report /home/david/bitacora/metodologia/artifacts/REQ-024-benchmark` · resources: benchmark-store · covers: R12, R13

### M6 — Final REQ-017 draft and closure
- [ ] T21 — Generate the fresh Pictures REQ-017 draft with the improved Planner · repo: skill · after: T20 · verify: `cd skill/scripts && python3 -m bt_planner check /home/david/bitacora/metodologia/artifacts/REQ-017-planner-v2-final-opus55-high --repo pictures=/home/david/dev/pictures` · resources: pictures-req017-draft · covers: R14
- [ ] T22 — Run closing regression gates and record limitations · repo: skill · after: T21 · verify: `cd skill/scripts && python3 -m unittest discover -s tests` · covers: R5, R13

Dependency shape: T1 inventories the local runtime/account matrix and fans out to T2, T3 and T4. T5 waits for T2 and T3. T6 waits for T4 and T5 and produces IF-1. T7, T8 and T9 are mutually unordered, with disjoint paths and no shared resource. T10 integrates them. T11 proves contract compatibility. T13 runs after T3, independent of M3. T12 waits for T10 and T13; T14 adapts the shared Planner to the inventoried providers; T15 installs and smoke-tests the configured effective accounts. The benchmark corpus cannot freeze until T15 and T16 finish. M5 is then a strict chain because every step writes the same benchmark store. M6 follows M5. The Scheduler, not this plan, decides any concurrency.

## Interface contracts for dependent and unordered work (R7)

| ID | Producer → consumers | Owner | Inputs | Outputs | Invariants | Integration criteria |
|---|---|---|---|---|---|---|
| IF-1 validator extension API | T6 → T7, T8, T9; integrated by T10 | `bt_planner` contract layer | parsed plan `dict`; `schema_tuple(plan)`; resolved spec path (sync layer only) | `traceability.check(plan, spec_ids) -> (errors, warnings)`, `interfaces.check(plan, ancestors) -> (errors, warnings)`, `quality.verification_findings(plan) -> warnings` | called only for `≥ 1.2.0`; pure, no I/O except `sync` reading `spec_ref`; messages start with the task or field path; never raise on malformed input | T10 full isolated suite green; 1.1.0 outputs identical (T6 test); golden bytes identical |
| IF-2 published 1.2.0 shape and report fields | T10 → T11, T12, T16 | `bt_planner` | IF-1 results | schema JSON, example plan, `report --json` keys `coverage`, `interfaces`, `verification_categories`, `criteria_without_command` | `kind` uses only the existing M2 enum; each 1.2.0 verification has one evidence category; new reports do not alter 1.0.0/1.1.0 results | T11 contract test; T12 profile test names the fields; T16 parses `report --json` |
| IF-3 planning-history projection | T13 → T12 (and Planner runs) | methodology side, read-only | source selected by T3 through its public adapter; explicit task kind and classification bucket | route-agnostic comparable bucket: quality `{samples, successes, failures, observed_rate, uncertainty_interval_95}`, duration `{samples, unit, median, range?}`, retries `{samples, count}`, consumption `{samples, unit, median, range?, coverage}`, per-metric `source_quality` and `comparability_key`, or `unknown` + reason | T3 must validate a pooled task-kind/context summary across routes; never expose per-route rows or ranking, and use `unknown` if cross-route comparability is unsupported. Each metric carries its own sample count and source quality; only publish ranges or uncertainty where the source provides them, otherwise mark them unknown. Preserve native units; do not convert tokens to quota/currency. Success/failure require correlated M1-applied M6 outcomes; retries require correlated retry identity, never infer them from attempts. The quality interval is descriptive, not future-success probability. Sparse, synthetic, claimed-only, cancelled, infrastructure, missing-context or incomparable samples stay unknown or separately counted. No provider/model/account/effort/quota fields | T12 cites the command; T13 tests quality, duration, retry and consumption coverage plus sparse/unknown cases; `test_plan_integration.py` still green |
| IF-4 benchmark record schema | T16 → T17, T18, T19, T20 | benchmark harness | manifest, run outputs, reviews | `manifest.json` (frozen hash), `runs/<case>/<arm>/<n>/` raw files + `meta.json`, `observed.json`, `reviews/<id>.json`, `report.json` | manifest frozen before first model call; observed and judged records separate; no raw prompts or secrets | `bt_plan_bench.py verify` passes at each step |
| IF-5 Planner runtime invocation | T12 → T14 → T15 | methodology invocation adapter | canonical Planner profile and four private skills; caller-selected provider/account/model/effort; project path | provider-native role invocation or the same instructions injected through the selected runtime; exit status and response metadata | One instruction source; caller choices pass through; no model/account default in the shared profile; no silent fallback; no credentials in records | Fake-runtime tests cover every registered provider; a live launch-only smoke runs once per effective account within an approved cap; no quality score is produced |

## Task contracts for non-trivial logic (R4)
- **T7 traceability.**
  - Inputs: the plan and the SPEC `Requirements` section.
  - Precedence:
    1. Schema-version gate.
    2. Id syntax.
    3. SPEC↔plan set equality.
    4. Per-task `covers`.
    5. Per-requirement coverage.
  - Algorithm: compute the coverage map `requirement → [task ids]`; uncovered = ids with an empty list.
  - Errors are reported per id and per task, never aggregated.
  - Unresolved decision for T5: whether ids other than `R<n>` (for example `US-1`) are extracted. Default: any id matching the pattern at the start of a list item under that heading.
- **T8 interfaces.**
  - Ancestors come from the existing `quality.ancestors`.
  - A consumer is satisfied if the producer is its ancestor. Otherwise `integration_task` must exist and have the producer and that consumer as ancestors.
  - An interface whose `integration_task` is itself a consumer is an error.
  - Missing list fields are errors.
  - Free text in interfaces is scanned with the same concurrency-claim rule as tasks.
- **T9 verification honesty.**
  - Validate that every 1.2.0 verification has exactly one allowed `category`; `type` remains the command/manual execution mechanism.
  - Report the categories that cover each requirement. For each task criterion, find evidence whose `purpose` equals it after whitespace trim; if none exists, emit a warning that names M6 NEEDS_REVIEW.
  - A test category alone is never reported as product acceptance; the Planner review flags user-visible requirements without product-level evidence.
  - List `created_by` items as planned work.
  - Severity is a warning at every version (no error), because M6 owns acceptance.
- **T13 projection.**
  - Bucket key: explicit task `kind` plus only the context dimensions that T3 confirms are supported and comparable (`complexity`, `scope`, `risk`, `coupling`). Missing dimensions or telemetry mapping remain unknown rather than being guessed.
  - Pool across routes only if T3 proves that the source supports a route-agnostic aggregate for the same work context; otherwise the projection returns unknown instead of hiding per-route differences.
  - Report separate sample counts, source quality and native units for quality, duration, retry and observed token-consumption metrics. Read thresholds from the corresponding public source; never redeclare M2 routing or eligibility thresholds or convert tokens to quota/currency.
  - Output shape: see IF-3.
  - Errors: an unreadable or missing store gives `unknown` with a reason, never an exception to the Planner.
- **T14 provider-neutral Planner invocation.**
  - Inputs: the canonical Planner profile and its four private skills, a configured provider/account profile, caller-selected model/effort, requirement directory and repository mappings.
  - Resolve provider and account through the existing local profile registry. Reuse the current runtime entrypoints; do not add a second routing/account-selection policy.
  - For a runtime with native agent definitions, invoke its generated representation. Otherwise, inject the canonical Planner instructions and skill references through a narrow adapter.
  - Pass provider, account, model and effort through unchanged. Unsupported provider, unavailable executable, invalid account or model rejection returns its original cause; never switch provider/account/model.
  - Use fake provider executables to verify command arguments, account environment and shared instruction delivery for each registered provider. These tests do not call paid models or assess plan quality.
- **T15 installation and launch smoke.**
  - Install only generated, marker-owned role files in every configured native agent directory; never overwrite hand-authored files. Runtimes without a native profile use T14's invocation adapter.
  - Enumerate profile IDs from T1 and use the existing effective-account identity to deduplicate aliases for live smoke count. The current profile list has five effective accounts; refresh before execution.
  - For each effective account within the owner-approved cap, make one short launch-only invocation and record provider, profile, selected model, exit status and response received. Do not retain credentials or prompts, score the resulting plan, or compare providers.
  - If auth/quota/runtime prevents launch, record that exact profile as blocked; do not silently substitute another subscription.
- **T16 harness.**
  - Precedence: verify the manifest hash first, then the cells, then the reviews.
  - Each metric names its source command.
  - The report refuses aggregates (see the no-superiority rule below).

## Proposed matched benchmark design (R11, R12)

**Scenario set** (pinned in T17; a case is excluded, with its reason, if its repository snapshot is unavailable):

| Case | Source | Intent | Oracle source |
|---|---|---|---|
| C1 | Pictures REQ-017 (SPEC copy from the 2026-10-16 rerun artifact + `rounds/round-01.json`), `pictures` at a pinned SHA | event policy across client/server, shared data | 9 known defects (below) |
| C2 | `bt_planner/tests/scenarios/TRAIN-3-project-list-contract/SPEC.md` | cross-contract with an unknown consumer | EXPECT.json plus pre-registered reviewer oracle |
| C3 | `…/TRAIN-6-postgres-migration/SPEC.md` | full-system decomposition, persistence compatibility | same |
| C4 | `…/METH-4-plan-quality-in-review/SPEC.md` | methodology, review UI | same |
| C5 | `…/REQ-902-audit-trail/SPEC.md` | independent new feature | same |

The C1 oracle (known V1/V2 REQ-017 failure cases) has nine items:
1. The «Arco orgánico» `arco`/`arco_asimetrico` label collision.
2. Curated IDs absent from the static piece menu (V1 M3 only reordered existing cards).
3. A persisted widget field breaking rollback of `WidgetGuiadoSchema.strict()`.
4. `guiada:test` not running the new tests.
5. `test-propiedades-herramientas` not exercising `proponer_composicion`.
6. Reuse of `ESTRUCTURAS_SIN_VISTA_3D` instead of a copied list.
7. Event policy applied before `propuestaConLoPedido`, with existing-plan bypass.
8. Unnormalised `briefVigente().evento`.
9. Unordered tasks sharing `event-structure-policy`.

**Arms.**
- A = current V2: profile, skills and `bt_planner` at the T1 commit.
- B = improved V2: after T15 confirms every configured provider/account can launch the shared Planner.
- No V1 arm.
- Retrospective set, scored by the same rubric but never compared causally:
  - The raw V1 `RESULT.json`.
  - The edited Pictures PLAN.md, labelled "V1 + coordinator edits".
  - The 2026-10-16 rerun, labelled retrospective because it read the earlier plan.

**Controls** (identical for A and B, recorded per run):
- Model identifier `claude-opus-5-5`, effort `high`, tools `Read Grep Glob`, permission mode `plan`, `--no-session-persistence`, 1,800 s timeout.
- Same prompt template (hash stored).
- Same case input bytes (hash stored); same repository SHA in a read-only worktree.
- An isolated config directory per arm with only the planner agent, its skill root and no SessionStart hook injection.
- No access to the bitácora, the scenario PLAN/EXPECT files or earlier REQ-017 plans.
- Equal review opportunities: no in-run reviewer, and the same post-run `bt_planner check` and `report` executed by the harness for both arms.

**Repeated-run method.**
- Three fresh sessions per arm per case.
- Run order within each case comes from a seeded shuffle; the seed is in the manifest.
- Manifest and oracles are frozen and hashed before the first model call.

**Resource cap.**
- At most 30 Planner runs (5 cases × 2 arms × 3), each ≤ 1,800 s. About 3.5 h of model time is expected from the observed ~7-minute rerun; this is not a measured average.
- Plus one T21 run.
- Reviews: exactly 2 per output (60 benchmark reviews + 6 retrospective).
- If quota or time ends, the remaining cells are recorded as incomplete. Model, effort, tools or review count are never substituted. Exceeding the cap needs the owner.

**Review count.**
- Two independent reviewers per output, blind to the arm (metadata stripped).
- Disagreement greater than one rubric point gets one adjudication, applied identically to both arms.
- Reviewer identities are an owner decision.

**Observed metrics** (deterministic, from harness commands):
- O1 check errors and warnings by family.
- O2 requirement coverage and uncovered ids.
- O3 orphan tasks.
- O4 invalid task, spec or file references against the pinned snapshot.
- O5 verification commands whose executable or path exists in the snapshot.
- O6 tasks without command verification, and criteria without a matching command purpose.
- O7 planned tests labelled `created_by` versus cited as existing.
- O8 graph shape: tasks, critical-path minutes, widest level, unordered shared pairs, declared interfaces.
- O9 efficiency: wall seconds, exit code, and tokens or cost only if the CLI reports them (else `unknown`).
- O10 between-run stability: per case and arm, the range of O1–O8 and per-requirement coverage agreement.
- Observed execution and rework: not measurable for unexecuted benchmark plans (`not measured`). Only the REQ-017 edited plan's recorded post-implementation corrections are reported, labelled retrospective.

**Judged metrics** (rubric v1, anchored 0–3, every score needs a quoted location):
- J1 technical precision (R4 elements).
- J2 verifiability level distinction.
- J3 architecture and module ownership (including M2 ownership).
- J4 parallelism and interface quality.
- J5 risk detection: each oracle item detected yes/no with a quote, plus new valid risks.
- J6 ambiguity handling.
- J7 scope discipline and unnecessary work.
- J8 semantic-review value: each review finding judged as a demonstrated defect, a plausible risk or false. This informs R10: if B's semantic pass adds no demonstrated defect beyond `bt_planner`, the report recommends making it optional.

**No-superiority rule.**
- No aggregate cross-metric score and no overall "better/superior" statement.
- A directional statement for one metric is allowed only if all of these hold:
  - Both arms are complete in ≥ 4 of the 5 cases.
  - B's per-case median is better in ≥ 4 complete cases.
  - No case shows B worse than A's worst run.
  - For judged metrics, both reviewers agree on the direction in those cases.
- Otherwise the report says "no supported difference".
- With n = 3, results are descriptive only.
- Retrospective artifacts never enter directional statements.
- Missing cells are never imputed.

## Requirement coverage (R1–R15)
PLAN.json 1.1.0 cannot encode this table; the `covers:` fields above are prose that `bt_planner` ignores today. T7 and T10 make it machine-checked for future plans.

| Req | Tasks | Milestone acceptance | Evidence (existing / created / manual) |
|---|---|---|---|
| R1 | T1, T2, T19 | M1, M5 | manual review of DIAGNOSIS.md; bench verify (created by T16) |
| R2 | T1, T2, T3, T15 | M1, M4 | existing module and methodology suites; `test_plan_integration.py`; manual audit |
| R3 | T6, T7, T10, T12 | M3, M4 | created `test_traceability.py`, `test_planner_profile.py` |
| R4 | T12, T19 | M4, M5 | created profile test (presence of rules); judged J1 (semantic, not deterministic) |
| R5 | T9, T10, T12, T22 | M3, M4, M6 | created `test_verification_quality.py`; existing suites |
| R6 | T7, T8, T9, T12 | M3, M4 | created tests; review-skill test |
| R7 | T6, T8, T10, T12 | M3, M4 | created `test_interfaces.py` |
| R8 | T3, T4, T5, T6, T10, T11 | M2, M3 | created golden and compat tests; existing `bt_scheduler_core` `test_plan.py`, `test_plan_launch_paths.py`, `test_scheduler_integration.py`, `test_scheduler_m1_m6_e2e.py` |
| R9 | T3, T6, T10, T11, T12, T13 | M1, M3, M4 | created contract, compatibility and history tests; manual audit |
| R10 | T6, T9, T12, T16, T19 | M3, M4, M5 | created tests; judged J8 |
| R11 | T2, T16, T17, T18, T19 | M5 | bench verify and score (created by T16); manual |
| R12 | T16, T18, T19, T20 | M5 | bench report (created by T16); manual |
| R13 | T1, T4, T11, T20, T22 | M2, M3, M6 | existing suites before and after; created tests |
| R14 | T15, T21 | M4, M6 | existing `bt_planner check` with `--repo pictures=…`; manual no-change check |
| R15 | T1, T3, T12, T14, T15 | M1, M4 | local runtime/profile inventory; fake-runtime selection tests; launch-only smoke results per effective account; no model-quality scoring |

## Risks and assumptions
- Assumption: the T3 audit confirms the consumer table. If a consumer breaks, T5 stops for the owner before T6.
- Risk: adding `covers` to `markdown.parse_task_line` output could break the supervisor-parser parity test. T10 keeps the shared parse output stable or runs `test_isolation_plan_parse.py`.
- Risk: verified planning history may be empty (F10). T13 then ships an `unknown`-only projection; no estimate becomes numeric without verified data.
- Risk: benchmark contamination or confounds (hooks, prior plans, fixture PLAN files). T17 controls them; any leak voids the cell.
- Risk: some non-Pictures repositories (trainingapp) may not be checked out at a usable SHA. Such cases are excluded and reported.
- Risk: configured runtimes may not support a native Planner profile file. T14 must deliver the canonical instructions through that runtime's invocation path; T15 records an explicit failure if the runtime or account cannot launch, without substitution.
- Risk: live launch-only smokes consume provider usage and can be blocked by stale authentication or quota. T15 runs only within a separately approved call cap and does not rank model quality.
- Assumption: estimates come from inspected code size and the 7-minute observed rerun. No comparable verified planning-history samples were available while planning.
- Cost: T15 launch-only smokes, T18/T19 benchmark runs and T21's Opus reference run consume provider usage. Plan approval authorises only the explicitly stated caps.

## Owner decisions resolved by approval
1. Use two independent reviewers under one hash-pinned rubric; pin their exact profiles/models in T17 before scoring.
2. Permit one launch-only smoke per effective account, with a current hard cap of five; refresh inventory before T15 and do not add newly configured accounts.
3. Cap the benchmark at 30 matched runs plus one final Opus 5.5 high reference run and 66 blind-review records.
4. Pictures REQ-017 q1–q5 and A6–A8 remain unanswered and outside this requirement.

## Verification
End to end, the requirement is met when all of the following hold:
1. The T22 suites pass with totals recorded next to the T1 baseline.
2. T11 proves explicit kind reaches M2, M6 accepts evidence categories without changing runner verdicts, old consumers cannot launch 1.2.0 plans, and rollback restores an existing compatible revision without rewriting its hash.
3. The T20 report passes `bt_plan_bench.py report`, with observed and judged sections separated and no unsupported claim.
4. T21's draft has a recorded real `bt_planner check` result, and Pictures is untouched.
5. T14 fake-runtime tests cover all registered providers, and T15 records a successful launch/response for each approved effective account without grading plan quality or silently switching accounts.

Product-level acceptance of REQ-017 is explicitly not part of this requirement.

## Rulings

## Progress log
- 2026-10-16: Planner draft written from read-only inspection. Post-draft `bt_planner check` passed; awaiting owner review.
- 2026-10-16 17:38 review comments (owner via Codex conversation): Owner approved the REQ-024 plan as presented, including the cap of 30 matched benchmark runs plus one final Opus 5.5 high reference run, 66 blind-review records, and two independent reviewers under the same rubric. Pictures q1–q5 and A6–A8 remain outside scope.
- 2026-10-16 17:38 plan APPROVED (owner via Codex conversation)

- 2026-10-16: T1 complete. Captured current-V2 source snapshot and hashes, seven registered profiles/five effective accounts, and the baseline Planner suite result (219 tests, 18.663 s, exit 0); see `../../artifacts/REQ-024-benchmark/baseline/`. This baseline includes the D-055 rollout and Planner instruction edits made before approval; it is not the historical pre-edit V2 state.
- 2026-10-16: T2/T3 complete. `DIAGNOSIS.md` classifies implementation, instructions, raw V1/V2 output, coordinator edits, product implementation, deterministic tests, synthetic oracles and owner decisions. `CONSUMER_AUDIT.md` records M1/M2/M6 compatibility and telemetry boundaries; the integration suite passed 21 tests. No code or Pictures file changed.
- 2026-10-16: T4 complete. Pinned exact input and canonical bytes/hashes for 1.0.0, 1.1.0 and a proposed-key 1.2.0 plan. The fixtures were generated against the T1 snapshot's unchanged `contract.py` SHA-256 `2ed0e93371ec68dcbe6bed5a3cc90ad49fad971e866a3bf12f1be88bfa80cbe2`; the focused suite passed 3 tests. See `skill/scripts/bt_planner/tests/golden/GENERATION.md` and `../../artifacts/REQ-024-benchmark/test-contract-golden.log`.
- 2026-10-16: T5 complete. `CONTRACT-1.2.0.md` maps every audited consumer, migration gate and rollback; M1 plan-loader tests passed 23/23. Direct probes confirm current M1 drops `kind` and current M6 rejects `category`, so T11 must implement the planned fail-closed upgrade before any 1.2.0 approval or launch. No contract code changed.
- 2026-10-16: T6 complete. Added the `(1, 2, 0)` extension gate and pure traceability/interface/verification hooks; 1.0.0 and 1.1.0 validation reports are pinned to pre-change bytes. Planner suite: 225 passed; `test_plan_integration.py`: 21 passed; scoped Ruff, `py_compile`, golden hashes and `plan-json check REQ-024` passed. No Pictures files changed.
- 2026-10-16: T7 complete. Schema 1.2.0 now validates unique requirement IDs, per-task `covers`, SPEC/plan set equality, orphan tasks and uncovered requirements. `sync.check` reads IDs only from an in-directory SPEC `Requirements` section for schema 1.2.0+. Traceability tests: 10 passed; full Planner suite: 235 passed; M1 integration: 21 passed. `py_compile`, scoped Ruff, `git diff --check` and `plan-json check REQ-024` passed; no Pictures source changed.
- 2026-10-16: T8 complete. Schema 1.2.0 interfaces now validate stable IDs, producer/consumer references, dependency ordering or an integration task, required text fields and lists, and reject scheduling keys/concurrency promises. Interface tests: 14 passed; full Planner suite: 249 passed; M1 integration: 21 passed. `py_compile`, scoped Ruff, `git diff --check` and `plan-json check REQ-024` passed; no Pictures source changed.
- 2026-10-16: T9 complete. Added 1.2.0 category warnings, per-requirement category coverage, manual-only and product-level review findings, M6 criterion-purpose coverage, and explicit planned-work reporting for `created_by`. M6 currently matches purpose exactly (no whitespace trim); the Planner reports whitespace-only matches as needing M6 review without changing M6 behavior. T9 tests: 10 passed; full Planner suite: 259 passed; M1 integration: 21 passed. `py_compile`, scoped Ruff, `git diff --check` and `plan-json check REQ-024` passed; legacy golden reports remain unchanged.
- 2026-10-16 18:23: T10 complete. Published schema/example 1.2.0, made task `kind` and verification `category` required for 1.2.0, derived SPEC requirement IDs in `init`, and left undeclared task `covers` empty for explicit gap reporting. Added version-gated PLAN.md contradiction checks and report projections for coverage, interfaces, verification categories and criteria without a unique M6 command; 1.0.0/1.1.0 canonical bytes and report shape remain pinned. Planner suite: 269 passed; methodology integration: 21; isolated parser: 4; scenarios: 8; focused schema: 43; PLAN.md sync: 30; report: 2; golden: 3. Scoped Ruff, `py_compile`, JSON parsing, `git diff --check` and `plan-json check REQ-024` passed. Updated test SPEC fixtures; no M1 runtime/parser or Pictures source changed. T11 remains the compatibility gate before approving or running 1.2.0.
- 2026-10-16: T11 complete. M1 forwards validated `kind`; M2 consumes explicit kind with legacy title inference preserved; M6 validates, serializes and hashes optional `category` while retaining legacy hashes. Capability checks fail closed across approval, handoff, launch, resume and exact frozen-revision loading; malformed markers report unknown. Focused compatibility test: 9 passed; M1 loader: 23; launch paths: 23; adapter evidence: 5; plan integration: 21; Scheduler integration: 30; M6 package: 67; wheel install: 19. Scoped Ruff, compilation and diff checks passed; both independent reviews approved. P-107 remains open for the live-quota decision-source suite; see RUN.md. No provider/model generation, benchmark or 1.2.0 plan approval/launch occurred.
