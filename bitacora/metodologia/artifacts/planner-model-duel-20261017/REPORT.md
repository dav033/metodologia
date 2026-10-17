# Native Planner comparison: Opus, Sol and Astra

## Interpretation

Astra produced the strongest plans in this three-case sample: 12/13 behavioral checklist items fully addressed, one partial. Sol addressed 11 fully/two partial at much lower measured base API-equivalent cost. Opus addressed 8 fully/five partial, with concrete migration weaknesses despite useful deployment observations. No checklist item was entirely absent; full/partial is not a planted-defect recall or intelligence score.

The decisive distinctions were concrete: Astra alone specified detail-confirmed deletion for saved tabs missing from a live paginated list; simply finishing every page does not prevent an updated existing project from moving ahead of the cursor. Sol and Astra explicitly covered absent-key import serialization, coordinated database/assets recovery and lossless post-write rollback boundaries. Opus's draft relied on existing-row FOR UPDATE, narrowed integer ranges, treated missing/mismatched assets as warnings and offered a knowingly lossy stale-SQLite rollback flag. Counterexamples and official PostgreSQL sources are retained. All three still need an availability decision/continuity design for literal uninterrupted migration; none proved zero downtime.

Only Astra's CP1 first response passed the complete structural contract; the other eight declared an integration task among its own consumer tasks, which 1.2.0 forbids. All nine returned the requested artifact blocks. These findings measure first drafts because host feedback/repair was deliberately withheld. They do not show that the ordinary Planner validation/repair loop is ineffective: the frozen gate correctly rejected the eight invalid drafts. Keep that existing loop mandatory before approval/M1; do not publish these outputs by bypassing it. Warnings also preserve manual-verification needs.

Raw total tokens alone would favor Astra over Sol by 3.9% here (895,593 versus 931,915). Yet Astra's baseline API-equivalent is 5.15x Sol's ($4.279 versus $0.831), and the observed same-account five-hour changes sum to +43pp for Astra versus +11pp for Sol. Model-specific weights and token classes matter. Opus's raw total includes especially large repeated/cache input; its baseline equivalent was $3.568. These equivalents are not subscription invoices, and quota is rounded/lagged.

Proposal only: treat Sol as the economical planning candidate and Astra as the quality candidate for difficult planning, then validate the tradeoff on further representative requirements with the normal feedback loop. This pilot does not select or configure a production Planner. These reused development cases are not an independent held-out estimate of general performance.

## Scope and controls

Nine owner-authorized fresh planning calls use three pinned code snapshots/specifications, a hash-identical improved Planner role plus four private skills/references/schema, high requested effort, maximum 8 tasks, and the same two-artifact output contract. CP1: API pagination/external consumer; CP2: SQLite→PostgreSQL migration; CP3: existing analysis in CLI/web. Inputs reuse candidate C2/C3/C4 assets outside the formal matched-arm REQ-024 experiment; no formal manifest, call cap, reviewer score or product source changed.

Claude Work runs Opus with safe/restricted mode, Read/Grep/Glob only, plan permission mode, no session persistence. Codex-2 runs Sol/Astra with ignored user config/rules, read-only sandbox, disabled web and instructed read-only file inspection. Two account lanes run concurrently, one call per account; Sol/Astra order alternates by case. Tool affordances/native hidden instructions differ, so this measures operational model+native-runtime configurations, not isolated intrinsic intelligence. Exact internal reasoning budgets and Codex effective model/service tier are not independently attested.

The host validates first responses using a frozen standalone bt_planner package, then performs semantic judgement with route labels removed case by case. Coordinator had seen some route-labeled deterministic diagnostics; style and timing can reveal identity. This is partial blinding, not independent external judging. Existing candidate oracles are draft behavior checklists; actual source/SPEC override their path hints (notably CP3 already has CLI report routing). Full/partial/missing statuses require substantive plan evidence, not just covers labels.

No automatic repair turns were allowed. This is first-draft reliability, not end-to-end performance after the normal validator/repair loop. Plans were not approved/frozen or executed; checks are structural, not passing product test suites.

## Aggregate results

| Route | Behavioral checklist full / partial / missing | Schema valid | Publishable first draft | Correct output blocks | Total tokens | Output incl. thinking | Native time sum | Read tool calls | Base API-equivalent USD* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Opus 5.5 high | 8 / 5 / 0 (13) | 0/3 | 0/3 | 3/3 | 1,831,268 | 82,627 | 785.768s | 91 | $3.568 |
| GPT-6.1 Sol high | 11 / 2 / 0 (13) | 0/3 | 0/3 | 3/3 | 931,915 | 37,907 | 825.387s | 44 | $0.831 |
| GPT-6 Astra high | 12 / 1 / 0 (13) | 1/3 | 1/3 | 3/3 | 895,593 | 36,240 | 954.910s | 40 | $4.279 |

*Illustrative baseline Standard API equivalent computed from recorded uncached/cache-read/cache-write-TTL/output classes and researched rates, not a subscription invoice. Aggregate usage does not reveal every per-request long-context/speed/tool modifier; none is fabricated. Codex credit billing has different cache-write rules. Actual account telemetry is reported separately.

Total input includes repeated/cache input across tool turns; output already includes thinking. Never add thinking twice. Time is the sum of native call wall times, not total parallel experiment elapsed time. Tokenizers, tool batching, hidden context and cache differ. Schema validity, substantive coverage and operational readiness are distinct.

## Per-case outcomes

| Case | Route | Checklist full / partial / missing | Validate / check / report exit | Tokens | Native seconds |
|---|---|---:|---|---:|---:|
| CP1 | [Opus 5.5 high](outputs/CP1-opus/PLAN.md) | 3 / 1 / 0 | 2/2/2 | 565,113 | 236.474 |
| CP1 | [GPT-6.1 Sol high](outputs/CP1-sol/PLAN.md) | 3 / 1 / 0 | 2/2/2 | 208,695 | 212.573 |
| CP1 | [GPT-6 Astra high](outputs/CP1-astra/PLAN.md) | 4 / 0 / 0 | 0/0/0 | 216,862 | 381.585 |
| CP2 | [Opus 5.5 high](outputs/CP2-opus/PLAN.md) | 1 / 4 / 0 | 2/2/2 | 416,335 | 351.594 |
| CP2 | [GPT-6.1 Sol high](outputs/CP2-sol/PLAN.md) | 4 / 1 / 0 | 2/2/2 | 279,454 | 363.348 |
| CP2 | [GPT-6 Astra high](outputs/CP2-astra/PLAN.md) | 4 / 1 / 0 | 2/2/2 | 301,835 | 363.838 |
| CP3 | [Opus 5.5 high](outputs/CP3-opus/PLAN.md) | 4 / 0 / 0 | 2/2/2 | 849,820 | 197.700 |
| CP3 | [GPT-6.1 Sol high](outputs/CP3-sol/PLAN.md) | 4 / 0 / 0 | 2/2/2 | 443,766 | 249.466 |
| CP3 | [GPT-6 Astra high](outputs/CP3-astra/PLAN.md) | 4 / 0 / 0 | 2/2/2 | 376,896 | 209.487 |

## Structural failures and warnings

- **CP1 / GPT-6 Astra high:** 0 error(s), 47 warning(s). No publishability errors.
- **CP1 / Opus 5.5 high:** 1 error(s), 32 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks
- **CP1 / GPT-6.1 Sol high:** 2 error(s), 39 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks interfaces[1].integration_task: cannot be one of the consumer tasks
- **CP2 / GPT-6 Astra high:** 3 error(s), 63 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks interfaces[1].integration_task: cannot be one of the consumer tasks interfaces[2].integration_task: cannot be one of the consumer tasks
- **CP2 / Opus 5.5 high:** 2 error(s), 44 warning(s). interfaces[1].integration_task: cannot be one of the consumer tasks interfaces[2].integration_task: cannot be one of the consumer tasks
- **CP2 / GPT-6.1 Sol high:** 3 error(s), 65 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks interfaces[1].integration_task: cannot be one of the consumer tasks interfaces[2].integration_task: cannot be one of the consumer tasks
- **CP3 / GPT-6 Astra high:** 1 error(s), 23 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks
- **CP3 / Opus 5.5 high:** 1 error(s), 22 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks
- **CP3 / GPT-6.1 Sol high:** 1 error(s), 28 warning(s). interfaces[0].integration_task: cannot be one of the consumer tasks

Warnings include verification-purpose/acceptance mismatches requiring M6 manual review; a publishable structure alone does not mean automatic execution acceptance. The legacy collector field format_valid checks a review JSON shape and is unused here; block_contract_valid is the Planner capture metric. Full diagnostics are in deterministic-checks.json.

## Semantic judgements and counterexamples

### CP1 — GPT-6 Astra high

- **C2-01 full:** Metadata-only five-field projection and strict page schemas are specified; snapshot/detail contracts remain separate.
- **C2-02 full:** Draft states ordering with a unique tuple tie-break, exclusive cursor boundaries, lookahead/terminal behavior, proposed page bounds and live-not-snapshot semantics; owner assumptions are visible.
- **C2-03 full:** External MCP usage is explicitly unknown; notice/compatibility decisions and a release gate are required without claiming local tests prove external compatibility.
- **C2-04 full:** D2/T5 require complete-load publication, deduplication, stale-refresh guards and detail-confirmed deletion (only404 removes missing saved/active tabs). T4 HTTP, T5 client/state tests and T6 real screen scenarios cover progression, terminal null and later-page failure.
- Note: Addresses the important live-pagination/tab-pruning interaction explicitly, rather than treating all-pages completion as a snapshot.
- Note: T5 introduces a scoped web tsx test dependency/script/lockfile change instead of asserting a nonexistent baseline test harness; planned work is labeled created_by.
- Note: External notice and coordinated cutover remain gated draft decisions. First-response structural checks are evaluated separately from these semantic notes.

### CP1 — Opus 5.5 high

- **C2-01 full:** Metadata-only five-field projection and strict page schemas are specified; snapshot/detail contracts remain separate.
- **C2-02 full:** Draft states ordering with a unique tuple tie-break, exclusive cursor boundaries, lookahead/terminal behavior, proposed page bounds and live-not-snapshot semantics; owner assumptions are visible.
- **C2-03 full:** External MCP usage is explicitly unknown; notice/compatibility decisions and a release gate are required without claiming local tests prove external compatibility.
- **C2-04 partial:** T3 adds server HTTP checks and T5 manual multi-page screen checks, but T4 is checked only by lint/types and keeps tab call sites unchanged. Completed live traversal omissions still trigger legacy absence-based tab removal; no runtime helper negative-path test or deletion confirmation is specified.
- Note: Recognizes unknown MCP consumer and stale SPEC wording about data_json versus parsed data. Proposed contract decisions are visible as revisable assumptions.
- Note: The live-pagination missing-project trace also applies here; A5 explicitly permits missed rows while the unchanged tabs consumer treats absence as deletion.
- Note: T4 introduces an unspecified page-count-overrun guard; the bound and behavior for a legitimate larger dataset are left to implementation. It needs a defined, justified policy or a non-arbitrary liveness strategy.
- Note: A5 says the live limitation is accepted, although no owner Q&A occurred. Read this only as an unapproved proposed assumption, consistent with the draft preface, not an actual owner decision.

### CP1 — GPT-6.1 Sol high

- **C2-01 full:** Metadata-only five-field projection and strict page schemas are specified; snapshot/detail contracts remain separate.
- **C2-02 full:** Draft states ordering with a unique tuple tie-break, exclusive cursor boundaries, lookahead/terminal behavior, proposed page bounds and live-not-snapshot semantics; owner assumptions are visible.
- **C2-03 full:** External MCP usage is explicitly unknown; notice/compatibility decisions and a release gate are required without claiming local tests prove external compatibility.
- **C2-04 partial:** T4 adds real helper tests and T5 HTTP/browser coverage, but successful live pagination can still omit an updated existing project. T4 only prevents deletion inference from failed/partial traversal, not a completed non-snapshot traversal; legacy tabs pruning can close a valid tab.
- Note: Strong source/consumer inspection and explicit D1/D2 gates. No false command success or external compatibility claim observed.
- Note: Concrete remaining R2 regression: fetch default first page of 50 from 51 projects, then update the unseen saved-tab project so its updated_at moves above the anchor. The final successful page is empty and nextCursor null; existing tab filtering removes that still-existing project. Rejecting partial failures and deduplication do not address this; a snapshot or authoritative detail-confirmed deletion is needed.

### CP2 — GPT-6 Astra high

- **C3-01 full:** Tasks preserve project/asset data and raw JSON/timestamps, constraints, counts and explicit content-hash encoding; inventories and conversion failures are gated rather than silently coercing data.
- **C3-02 full:** Async conversion covers repositories and HTTP/WS/assets; revision-before-no-op behavior, absent-key import serialization, concurrent writes/imports and commit-before-event behavior are explicitly required and tested.
- **C3-03 partial:** A single-writer fence/final reconciliation and fail-closed promotion are addressed, but uninterrupted availability remains a blocking product/architecture gate. The current draft still needs a revised continuity mechanism if the literal no-availability-loss condition applies.
- **C3-04 full:** Coordinated database/assets backup, checksummed complete bundles, isolated verified restore and rollback after PostgreSQL writes are planned; stale SQLite rollback is blocked and compatible PG release rollback is distinguished from restore.
- **C3-05 full:** Docker/Compose/env and EC2 preflight/deploy/rollback are covered, including compatible backup tools, explicit DB connectivity, readiness, credential handling and storage compatibility checks.
- Note: Particularly concrete conditional cutover sequence: fence/drain, consistent source backup, empty isolated target import/typed hashes, candidate probes, route switch, then writes. Maintains raw JSON/timestamp representations and includes an explicit shared/exclusive mutation barrier for database/assets backups.
- Note: D1 honestly says the proposed maintenance branch does not satisfy literal uninterrupted availability and requires a replan with durable capture/replay if uninterrupted writes are mandatory. No owner acceptance was invented; this remains a blocked draft, not a zero-downtime proof.

### CP2 — Opus 5.5 high

- **C3-01 partial:** T5 preserves rows/counts/hashes, but resolved design rule1 narrows SQLite integers to PG int4 without a verified bound (e.g. revision2^31), and T5 step7 treats missing/mismatched asset files as warnings instead of blocking verified migration.
- **C3-02 partial:** Existing-row FOR UPDATE and parallel PUT tests cover updates, but do not serialize concurrent absent-key imports. Unique violations mapped to plain create Error can return500 for a racing import where baseline serialized semantics return409.
- **C3-03 partial:** T7 defines stop-API/final-backup/import/activate and failure restart, but D2 explicitly needs a maintenance outage; no continuous-availability branch exists without new tasks. D2 is unapproved, so the literal availability condition remains unresolved.
- **C3-04 partial:** PG dump/isolated restore/checksums are planned, but database snapshot and asset copy lack an explicit common mutation fence. The proposed AllowSqliteRollback escape knowingly allows stale-source data loss after PG writes instead of preserving those writes.
- **C3-05 full:** Compose/EC2 configuration, matching PostgreSQL client, credentials outside argv/logs, readiness and incoming-release backup/cutover hazards are concretely addressed.
- Note: Permitted-input witness: SQLite can round-trip revision2147483648, which exceeds PostgreSQL int4. A checked wider representation/conversion or an actually established source bound is needed; no production overflow was observed.
- Note: FOR UPDATE locks retrieved rows, not a missing external key. Explicit absent-key serialization, an appropriate retry/upsert protocol, or another sound concurrency design must preserve import semantics. See migration-counterexamples.json and official PostgreSQL references.
- Note: A checksum-valid copied directory can still lack a file referenced by the database dump if deletion occurs between snapshot and copy. The plan needs coordinated asset retention/quiescence and fail-closed completeness verification.
- Note: An explicit flag plus data-loss warning does not meet the stated preservation requirement after PostgreSQL has accepted writes. That would require a separately approved scope change or verified reverse reconciliation; the current owner has approved neither.

### CP2 — GPT-6.1 Sol high

- **C3-01 full:** Tasks preserve project/asset data and raw JSON/timestamps, constraints, counts and explicit content-hash encoding; inventories and conversion failures are gated rather than silently coercing data.
- **C3-02 full:** Async conversion covers repositories and HTTP/WS/assets; revision-before-no-op behavior, absent-key import serialization, concurrent writes/imports and commit-before-event behavior are explicitly required and tested.
- **C3-03 partial:** A single-writer fence/final reconciliation and fail-closed promotion are addressed, but uninterrupted availability remains a blocking product/architecture gate. The current draft still needs a revised continuity mechanism if the literal no-availability-loss condition applies.
- **C3-04 full:** Coordinated database/assets backup, checksummed complete bundles, isolated verified restore and rollback after PostgreSQL writes are planned; stale SQLite rollback is blocked and compatible PG release rollback is distinguished from restore.
- **C3-05 full:** Docker/Compose/env and EC2 preflight/deploy/rollback are covered, including compatible backup tools, explicit DB connectivity, readiness, credential handling and storage compatibility checks.
- Note: Strong explicit provenance and no-op/import/revision invariants. Hashes use typed length-delimited row encoding; backup/recovery and incoming-release backup hazards are addressed.
- Note: The final source boundary and continuous-write solution remain future D1/T1 decisions; the draft does not supply an executable no-interruption handover protocol. It correctly refuses to assume a maintenance outage is accepted, but more planning is still required for that requirement.

### CP3 — GPT-6 Astra high

- **C4-01 full:** Recognizes the existing CLI report→adapter→Planner route, preserves its output/exit contract and adds content-level regression proof. Web access remains through a structured adapter helper; analysis is reused, not duplicated.
- **C4-02 full:** Targets bt_page_req.plan_panel on the actual owner approval Plan tab, not the later code-merge review tab. Displays critical-path IDs/minutes, widest level and low-confidence tasks using the existing report semantics.
- **C4-03 full:** Explicit missing-file branch preserves complete legacy panel HTML with no extra wrapper/notice. Planned characterization and actual page/adapter checks cover absent PLAN.json and status-dependent controls.
- **C4-04 full:** Separates CLI/adapter checks from renderer/real-page integration, legacy regression and product inspection; present, absent and invalid cases and import-boundary safety are explicitly addressed.
- Note: Explicitly protects actual req_page integration, hostile diagnostics, artifact immutability and missing-PLAN.md behavior. Branching fixture values and output ordering are concrete; current CLI shape and approval semantics remain unchanged.

### CP3 — Opus 5.5 high

- **C4-01 full:** Recognizes the existing CLI report→adapter→Planner route, preserves its output/exit contract and adds content-level regression proof. Web access remains through a structured adapter helper; analysis is reused, not duplicated.
- **C4-02 full:** Targets bt_page_req.plan_panel on the actual owner approval Plan tab, not the later code-merge review tab. Displays critical-path IDs/minutes, widest level and low-confidence tasks using the existing report semantics.
- **C4-03 full:** Explicit missing-file branch preserves complete legacy panel HTML with no extra wrapper/notice. Planned characterization and actual page/adapter checks cover absent PLAN.json and status-dependent controls.
- **C4-04 full:** Separates CLI/adapter checks from renderer/real-page integration, legacy regression and product inspection; present, absent and invalid cases and import-boundary safety are explicitly addressed.
- Note: Adds no unnecessary CLI feature when R1 already exists; separates the Plan approval tab from the Revisar code-review tab. Unexpected adapter errors return an explicit unavailable result rather than fabricated metrics; diagnostic presentation should remain sanitized/observable.

### CP3 — GPT-6.1 Sol high

- **C4-01 full:** Recognizes the existing CLI report→adapter→Planner route, preserves its output/exit contract and adds content-level regression proof. Web access remains through a structured adapter helper; analysis is reused, not duplicated.
- **C4-02 full:** Targets bt_page_req.plan_panel on the actual owner approval Plan tab, not the later code-merge review tab. Displays critical-path IDs/minutes, widest level and low-confidence tasks using the existing report semantics.
- **C4-03 full:** Explicit missing-file branch preserves complete legacy panel HTML with no extra wrapper/notice. Planned characterization and actual page/adapter checks cover absent PLAN.json and status-dependent controls.
- **C4-04 full:** Separates CLI/adapter checks from renderer/real-page integration, legacy regression and product inspection; present, absent and invalid cases and import-boundary safety are explicitly addressed.
- Note: Particularly explicit absent/available/unavailable contract, real branching fixture values, legacy status coverage and no side effects. Correctly distinguishes the source product schema1.1.0 from the supplied1.2.0 planning-output contract; no product schema upgrade is proposed.

## Input/cache/output breakdown

| Route | Input incl. cache | Cache-read subset | Cache-write subset | Output incl. thinking | Thinking subset |
|---|---:|---:|---:|---:|---:|
| Opus 5.5 high | 1,748,641 | 1,547,863 | 200,712 | 82,627 | 30,085 |
| GPT-6.1 Sol high | 894,008 | 703,232 | 0 | 37,907 | 8,284 |
| GPT-6 Astra high | 859,353 | 680,704 | 0 | 36,240 | 6,384 |

## Quota observations

Percentages are USED. First-before failures remain unknown; no nearby/cached value is relabeled as a baseline. Codex-2 serves both models serially, and subscription readings are rounded/lagged, so even per-cell deltas cannot establish an exact stable per-model quota price.

| Account | First-before status | 5h used before → delayed after | Weekly used before → delayed after | Final status |
|---|---|---:|---:|---|
| codex-2 | ok | 0% → 54% | 1% → 10% | ok |
| claude-work | http_401 | unknown → 17% | unknown → 90% | ok |

Observed within-cell deltas (percentage points, rounded and lagged):
- Opus 5.5 high: 5h known sum 0pp (3 unknown cells); weekly known sum 0pp (3 unknown cells).
- GPT-6.1 Sol high: 5h known sum 8pp (1 unknown cells); weekly known sum 2pp (0 unknown cells).
- GPT-6 Astra high: 5h known sum 14pp (2 unknown cells); weekly known sum 7pp (0 unknown cells).

For Codex-2, all six readings have matching reset windows: Sol cells sum +11pp/2pp (5h/weekly), Astra +43pp/7pp. These add to the observed account change, but are not an exact stable model price. Claude has one unknown first-before reading; its last immediate 5h reading was15%, delayed17%, so the extra delayed2pp is not assigned to a particular call.

Non-ok quota reads: `[{"cell": "CP1-opus", "side": "quota_before", "status": "http_401"}]`.

## Evidence and limitations

PLAN.md fixes scope/controls. cases.json pins source archive/spec/oracle bytes; source-hashes.json pins the shared bundle. protocol.json pins the task/runner/base collector. runtime-versions.json records CLI versions; validator-hashes.json pins the host validator. Each native record retains the final answer, tool names/read arguments, numeric usage and quota. Per-cell files-before manifests and workspace_changes document net source integrity; these are before/after checks, not proof against transient reverted edits or unseen out-of-scope reads. No raw private thinking text or full raw streams are retained.

Outputs are preserved under outputs/<case>-<route>/PLAN.md and PLAN.json. blind-plans.json, blind-judgements.json and blind-key.json expose the route-hidden judgement/unblinding trail. Metrics and structural diagnostics remain separate from semantic judgements. The scratch workspace is retained outside the repository and can be reconstructed from pinned archives.

Three heterogeneous cases and one response per cell do not estimate general failure probability, guarantee production readiness or measure quality after feedback/repair. This pilot does not resolve formal T17 account/isolation gates or select a production Planner. No change to the D-063 reviewer policy, no product implementation, no Scheduler dispatch, no provider fallback or additional review-model calls occurred.
