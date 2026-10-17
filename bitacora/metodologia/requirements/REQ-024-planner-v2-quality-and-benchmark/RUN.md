---
req: REQ-024
type: planning-run
date: 2026-10-16
status: draft-reviewed
---
# Planner run — REQ-024

## Generation

- Model: Claude Opus 5.5 (`claude-opus-5-5`), effort `high`.
- Account profile: Claude Work (`CLAUDE_CONFIG_DIR=/home/david/.claude-work`).
- Agent: Planner profile generated from the methodology source; `--permission-mode plan`; tools limited to `Read`, `Grep`, and `Glob`; `--no-session-persistence`.
- Outcome: CLI exit 0, `end_turn`, no permission denials; elapsed 986.622 s; cost USD 4.6825408 (reported list-price basis).
- Usage: 86 input tokens; 190,300 cache-creation input tokens; 5,176,784 cache-read input tokens; 106,222 output tokens, including 56,790 thinking tokens.
- The result was extracted into `PLAN.md` and `PLAN.json`. No Pictures source or canonical REQ-017 file was changed.

## Structural validation

- `python3 skill/scripts/bitacora.py plan-json check REQ-024` — exit 0, `OK: PLAN.json is publishable`.
- `python3 skill/scripts/bitacora.py plan-json report REQ-024` — 21 tasks, 6 milestones, 2,820 estimated minutes, 2,040-minute critical path, widest dependency level 3.
- The report found no unordered conflicts, unordered shared resources, unconsumed results, or redundant edges. It lists T2 and T14 without command verification and T13/T16/T17/T18 with low confidence; these are recorded as manual or uncertain work, not passed checks.
- The published `PLAN.json` remains schema 1.1.0 because this requirement proposes and tests the future 1.2.0 extension. The current validator accepted the draft.

## Semantic review

- Mapped R1–R14 to tasks, milestone criteria, and evidence in the plan.
- Checked the 1.2.0 compatibility argument against `bt_planner.contract` and `bt_scheduler_core.plan`: both accept 1.x documents, the Scheduler extracts its declared task fields and does not consume the proposed traceability/interface fields, and the Planner canonicalizer preserves extra keys. T3/T5 still make the full consumer audit a precondition before contract edits.
- The benchmark separates the controlled comparison (current V2 vs improved V2) from retrospective V1 and edited REQ-017 artifacts. The SPEC permits controlled comparisons where a reproducible baseline exists; no V1 causal claim is planned.
- No actionable semantic defect found in this pass. This is the Planner skill's same-context adversarial review, not an independent approval.

## Approval items in the original reviewed draft (superseded by the scope clarification below)

1. Approve or adjust the cap of 30 benchmark runs plus the final REQ-017 run and 66 blind-review records. The 3.5-hour model-time estimate is extrapolated from one observed run, not a measured average. The planning call itself cost USD 4.6825408; future per-run cost is not fixed. The Claude Work profile showed 86% weekly usage after this call, so the full sample may need to span a quota reset or be recorded incomplete under the stated cap.
2. Approve T14's marker-protected installer writes to the configured Claude and Codex agent directories.
3. Select the two blind reviewers, or authorize the methodology to use two independent reviewers under the same rubric.
4. Pictures REQ-017 product choices q1–q5 and A6–A8 remain open and are not decided by this requirement.

No implementation, profile installation, benchmark run, plan freeze, approval, or Pictures change occurred during this planning pass.

## Follow-up contract audit (2026-10-16)

A second coordinator audit found three omissions in the first semantic pass, which had concluded "No actionable semantic defect found":

1. IF-3 omitted M2's verified quality fields (successes, failures, observed rate, uncertainty and source quality), and it named retries without requiring a correlated retry identity.
2. The contract did not explicitly carry the model-agnostic work kind even though the existing routing adapter infers it from task titles and has a supported kind vocabulary.
3. R5 named five verification levels, but the proposed schema/report had no evidence-category field; M6 rejects unknown verification fields.

Updated SPEC R9 and the REQ-024 draft to propose an explicit supported `kind`, versioned verification `category`, verified quality/uncertainty projection, correlated retry semantics, and M1/M2/M6 migration and rollback tests. Unsupported specialist capabilities remain unknown; no provider/model eligibility was added. No source code or Pictures file changed.

The subsequent adversarial pass found three further issues: the corrected history projection listed consumption coverage but not observed values or per-metric sample counts; an old T11 sentence still claimed M1/M2/M6 would behave identically on new 1.2.0 plans; and the M6 typed request currently omits unknown metadata from its input hash. IF-3 and T3/T13 now require native units and separate counts for quality, duration, retries and observed token consumption; only audited route-agnostic comparable data may be pooled, otherwise values remain unknown. T11 now includes M6 contract and compatibility tests, preserves evidence categories in the M6 typed request hash while leaving runner verdicts unchanged, and does not claim new 1.2.0 canonical bytes equal the old implementation's bytes. F4 now records that serialization stability alone does not make older consumers execution-compatible.

- `python3 skill/scripts/bitacora.py plan-json check REQ-024` — exit 0, `OK: PLAN.json is publishable`.
- `python3 skill/scripts/bitacora.py plan-json report REQ-024` — 21 tasks, 6 milestones, 3,060 estimated minutes, 2,190-minute critical path, widest level 3; no unordered conflicts/shared resources, unconsumed results or redundant edges.
- This is a coordinator correction, not an independent review or approval. The revised draft remains subject to P-103.

The updated PLAN.md has not yet been sent. Firefox BiDi timed out; `mcp-control` reported `BLOCKED (human_has_control)`. No control takeover, desktop restart/reconnect or message send was attempted.

## V1 artifact recoverability audit (2026-10-16)

- Located `~/.state/delegations/D-20261016-090752-bc5d/RESULT.json` (`status: done`); its `evidence` field contains the full raw plan (18,134 characters). The corresponding `TASK.json`, `prompt.txt`, `OUTCOME.json` and `session.log` are present.
- The task record identifies Claude Work / generic Claude / Opus high, `kind: research`, and `worktree_mode: true`, but records no repository SHA. The delegated prompt is a follow-up using pre-digested evidence from D-20261016-085733-24b5, not a clean frozen benchmark input.
- The session log identifies Claude Opus 5.5 with `bypassPermissions`; its broad tool set includes Bash, Edit and Write, and SessionStart injected Pictures/metodologia continuation context. The task itself forbade code/test changes; the result reports no changed repository files and no tests run.
- No runnable V1 Planner profile or comparable isolated execution configuration was recovered. The raw result is valid retrospective evidence, while the controlled arms remain current V2 versus improved V2. No benchmark design change is needed.

## Owner scope clarification — provider-neutral launch (2026-10-16)

- The owner clarified that the shared Planner should launch through every AI runtime and account profile already configured on this computer. Model-quality parity and cross-model comparison are not requirements now; address a model-specific quality problem when it is observed. The pinned Opus 5.5 high run remains a reproducible benchmark reference, not a runtime restriction.
- Updated SPEC R15 and the plan to inventory locally configured runtimes/accounts, keep one provider-neutral instruction source, pass caller-selected provider/account/model/effort through native profiles or a thin adapter, reject silent fallback, and smoke-test launch/response only. Current inventory is Claude, Codex and Antigravity with five effective accounts after alias deduplication; refresh it before execution.
- The current draft has 22 tasks, 6 milestones, 3,480 estimated minutes and a 2,310-minute critical path. This supersedes the earlier 21-task/3,060-minute totals for review.
- No implementation, profile installation, provider call or plan approval occurred. P-103 still gates the benchmark cap (30 matched runs plus one fixed Opus reference run; 66 blind reviews), reviewer identities, marker-protected writes to configured native profile directories and the launch-only smoke call cap. Refresh the current five-effective-account inventory before setting that cap. The WhatsApp attachment sent earlier predates this clarification; it has not been re-sent.
- Same-context adversarial review: R15 maps to inventory (T1/T3), provider-neutral profile (T12), invocation adapter (T14) and installation/smoke (T15). Fake-runtime tests verify argument/account propagation without quality scoring; live smokes prove only launch and response. Explicit errors and no silent provider/account/model substitution are required.

## Desktop recheck for the requested WhatsApp send (2026-10-16)

- The direct read-only `desktop_windows` call remained pending for more than 200 seconds and was canceled. A separate local `mcp-control` query returned `BLOCKED (human_has_control)` for `desktop_start` and `desktop_windows`; the lease file was still present. No browser interaction or WhatsApp send occurred.
- An async clarification request is waiting for the owner to release the lease or authorize a Xephyr reconnect/restart. Do not bypass the lease through another browser-control path.


## Owner approval (2026-10-16)

- The owner approved REQ-024 plan revision r1. `PLAN.json` froze as `r1@5b9f9f35` after `python3 skill/scripts/bitacora.py --project metodologia plan-json check REQ-024` returned `OK: PLAN.json is publishable`.
- Approved usage bounds: 30 matched benchmark runs plus one final Claude Opus 5.5 high REQ-017 reference run; 66 blind-review records; two independent reviewers using one hash-pinned rubric, with exact evaluator profiles/models pinned in the benchmark manifest before scoring.
- Approved T15 cap: one launch-only smoke per effective account, at most five under the current inventory. Refresh the inventory before T15; any newly configured account is outside this cap.
- Pictures q1–q5 and A6–A8 remain outside scope. No benchmark run or provider call was authorized beyond these stated bounds.


## T1 — Diagnostic baseline (2026-10-16)

- Baseline repository HEAD: `196196ef427ab1f066d22faaeece2a40f8aa182c` on `feat/scheduler-m4-agent-monitor`; the worktree was already dirty, so the Planner source snapshot and per-file SHA-256 list are preserved under `artifacts/REQ-024-benchmark/baseline/current-v2-source/`.
- The snapshot contains the shared Planner profile, its four private skills, `bt_planner` and `bt_plan_adapter.py` (103 files). The baseline is the current V2 at T1, including D-055 and Planner instruction edits made before plan approval; it is not presented as the older pre-edit V2.
- `python3 skill/scripts/bitacora.py --project metodologia profiles list` exited 0: seven registered profile IDs across Claude, Codex and Antigravity. `bt_agents.pool_for('metodologia')` resolves five effective accounts: `antigravity`, `claude-personal`, `claude-work`, `codex-1`, `codex-luis`. Account directory values are redacted in the artifact.
- Baseline command `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` exited 0: 219 tests in 18.663 s. Full output is `artifacts/REQ-024-benchmark/baseline/bt-planner-tests.log`.


## T2/T3 — Evidence and consumer diagnosis (2026-10-16)

- `artifacts/REQ-024-benchmark/DIAGNOSIS.md` fingerprints recovered V1 output/prompt/session evidence, the controlled V2 rerun artifacts, Pictures' later-edited live plan, and scenario oracles. It labels V1 retrospective only and separates model output from coordinator edits, implementation and tests. `OUTCOME.json` says `claimed` while `RESULT.json` is `done`; the returned RESULT is the raw plan source, not an execution-success verdict.
- `artifacts/REQ-024-benchmark/CONSUMER_AUDIT.md` maps `bt_planner` → the sole methodology adapter → M1 → M2 and M6. It confirms M1 does not pass explicit `kind`, M2 infers it from task title, M6's typed verifier hash omits a future evidence category, and 1.1.0 frozen bytes must remain unchanged. It also records provider profiles, installers, general hooks and the missing generic `bt_planner_runtime` invocation adapter.
- Read-only local telemetry snapshot: 153 cross-project attempts; 153 elapsed-time values, 94 token totals, 80 verified outcomes, 123 unknown origins and 0 reported-model identities. It is not Planner-only evidence; no route-quality or cross-provider estimate is inferred. M4 metric use remains exact-match by provider/profile/model/name/unit/comparability key.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` exited 0: 21 tests in 0.321 s. It verifies methodology integration and parser parity, not model or Pictures acceptance. No Pictures product source changed.

## T4 — Golden canonicalization fixtures (2026-10-16)

- Added exact input and canonical-output fixtures for schema 1.0.0, 1.1.0 and a 1.2.0-labelled plan carrying the proposed `requirements`, `covers`, `kind`, `interfaces` and verification `category` keys.
- The T1 snapshot's `bt_planner/contract.py` SHA-256 is `2ed0e93371ec68dcbe6bed5a3cc90ad49fad971e866a3bf12f1be88bfa80cbe2`; the working file matched and had no Git diff when generated. Provenance is recorded beside the fixtures in `skill/scripts/bt_planner/tests/golden/GENERATION.md`.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_contract_golden.py` — exit 0; 3 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-contract-golden.log`.
- No contract or Pictures source changed. The 1.2.0 fixture pins only the old serializer's bytes; it does not claim that the old validator implements 1.2.0 semantics.

## T5 — Contract compatibility record (2026-10-16)

- Added `CONTRACT-1.2.0.md` by comparing the approved additive proposal with every consumer in `../../artifacts/REQ-024-benchmark/CONSUMER_AUDIT.md`. The plan's verification item referred to `CONSUMERS.md`; T3's actual audit file is `CONSUMER_AUDIT.md`, so no duplicate inventory was created.
- `cd skill/scripts && python3 -m unittest discover -s bt_scheduler_core/tests -p test_plan.py` — exit 0; 23 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-plan-loader.log`.
- Direct read-only probes: current M1 accepts the 1.2.0 fixture but its metadata allowlist drops `kind`; current M6 rejects a verification `category` with `ORDER_INVALID`. Current M2 therefore still infers kind from title. This confirms T11 must update M1/M2/M6 and add a fail-closed capability gate before any 1.2.0 approval or execution.
- A source scan found no direct `PLAN.json`/`bt_planner` consumer in Pictures, Maros, LOTM or Training App and no direct review-UI reader in methodology source.
- T5 disposition: proceed to T6 under the approved migration plan; legacy plans remain supported, and a 1.2.0 plan cannot be approved, handed off, launched or resumed until the updated Planner, M1, M2 and M6 compatibility checks pass. No contract code or Pictures source changed.

## T6 — Version-gated validator extension points (2026-10-16)

- Added `EXTENSIONS_SINCE = (1, 2, 0)` and wired `traceability.check(plan, spec_ids)`, `interfaces.check(plan, ancestors)` and `quality.verification_findings(plan)` only for supported schema-1 documents at 1.2.0 or later. Added the pure module boundaries; T7–T9 implement their semantic checks. `SCHEMA_VERSION` remains 1.1.0 pending T10, and no 1.2.0 rollout is enabled by this task.
- Before editing `contract.py`, froze exact baseline error/warning reports for the T4 1.0.0/1.1.0 inputs. Their hashes are pinned in `test_extensions.py`; the T1 `contract.py` source hash remained `2ed0e93371ec68dcbe6bed5a3cc90ad49fad971e866a3bf12f1be88bfa80cbe2`.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` — exit 0; 225 tests passed. Focused `test_extensions.py` passed 3 tests and `test_contract_golden.py` passed 3 tests. Logs: `../../artifacts/REQ-024-benchmark/test-bt-planner-t6.log`, `test-extensions-t6.log` and `test-contract-golden-t6.log`.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` — exit 0; 21 tests passed. `python3 skill/scripts/bitacora.py --project metodologia plan-json check REQ-024` returned `OK: PLAN.json is publishable`. Scoped Ruff, `py_compile` and `git diff --check` passed.
- The extension hooks are intentionally incomplete until T7–T9. The existing T4 hashes remain unchanged, 1.0.0/1.1.0 reports match their pinned baseline, and no Pictures file changed.

## T7 — Requirement traceability checks (2026-10-16)

- Implemented 1.2.0-only validation for a non-empty unique `requirements` ID list, each task's non-empty `covers` list, invalid/duplicate/unknown IDs, orphan tasks, SPEC/plan ID-set differences and requirements without a covering task. Findings name the requirement or task instead of aggregating IDs.
- Added a pure SPEC parser for IDs at the start of bullet or ordered list items inside the `Requirements` heading. It stops at the next same-level or higher heading, ignores fenced code, and distinguishes a missing heading from an empty section. `sync.check` passes extracted IDs only for supported schema 1.2.0+ plans; unresolved SPEC context becomes a warning. Legacy versions do not read or validate the new fields.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_traceability.py` — exit 0; 10 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-traceability-t7.log`.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` — exit 0; 235 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-bt-planner-t7.log`.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` — exit 0; 21 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-plan-integration-t7.log`.
- `py_compile`, `plan-json check REQ-024` and scoped `git diff --check` passed. Ruff passed on the touched implementation/test files when excluding the existing `FURB167` and `ISC004` findings in `sync.py`; a plain file-wide Ruff run reports those three pre-existing findings at the module front-matter and freeze error-message strings. No unrelated lint cleanup or Pictures source change was made.

## T8 — Interface contract checks (2026-10-16)

- Implemented schema 1.2.0 checks for unique `IF-n` IDs, non-empty title/owner and text lists, existing distinct producer/consumer tasks, duplicate consumers, and dependency proof. A producer must be an ancestor of each consumer or a declared integration task must depend on the producer and every unordered consumer; the integration task cannot itself be a consumer.
- Interface text uses the existing `evidence.PARALLEL_CLAIM_RE` rule, and the contract's recursive key scanner rejects scheduling keys inside interface objects. The top-level `interfaces` field remains optional; malformed lists and entries return field-path errors.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_interfaces.py` — exit 0; 14 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-interfaces-t8.log`.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` — exit 0; 249 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-bt-planner-t8.log`.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` — exit 0; 21 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-plan-integration-t8.log`.
- `py_compile`, `plan-json check REQ-024`, scoped Ruff (excluding the two pre-existing Ruff rule codes in `sync.py`) and scoped `git diff --check` passed. No Pictures source changed.

## T9 — Verification categories and M6 coverage findings (2026-10-16)

- Added 1.2.0 verification-category validation for exactly one string in `static`, `functional`, `integration`, `regression` or `product`. Findings remain warnings; the validator does not turn plan quality into an M6 acceptance verdict.
- Added a deterministic per-requirement category projection, criterion-to-purpose coverage with `M6 NEEDS_REVIEW` findings, manual-only requirement warnings and explicit `planned_work` entries for verification items with `created_by`. The report does not expose a product-acceptance boolean; lower-level categories and planned checks are not acceptance evidence.
- T9's approved confidence assumption said M6 trims purpose/criterion whitespace. Reading the M6 implementation (`bt_scheduler_quality/criteria.py`) disproved it: the runtime uses exact string equality. The Planner still checks the approved trim-normalized relationship and adds an explicit warning when M6's exact comparison would leave the criterion NEEDS_REVIEW. No M6 behavior or verdict policy changed.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests -p test_verification_quality.py` — exit 0; 10 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-verification-quality-t9.log`.
- `cd skill/scripts && python3 -m unittest discover -s bt_planner/tests` — exit 0; 259 tests passed, including unchanged legacy golden reports. Output: `../../artifacts/REQ-024-benchmark/test-bt-planner-t9.log`.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_integration.py` — exit 0; 21 tests passed. Output: `../../artifacts/REQ-024-benchmark/test-plan-integration-t9.log`.
- `py_compile`, `plan-json check REQ-024`, scoped Ruff (excluding the two pre-existing Ruff rule codes in `sync.py`) and scoped `git diff --check` passed. No Pictures source changed.

## T10 — Schema 1.2.0 integration (2026-10-16)

- Published the 1.2.0 JSON Schema and example. The version-gated contract now requires top-level `requirements`, per-task `covers` and `kind`, and a `category` on every verification. `kind` uses the existing M2 vocabulary; interfaces remain optional. Missing/invalid categories and kinds are contract errors for 1.2.0 while 1.0.0/1.1.0 validation results remain pinned.
- `init` extracts requirement IDs from an in-directory SPEC `Requirements` section and emits empty `covers` for undeclared task mappings; the existing gap summary reports those fields without guessing `kind` or verification `category`. The SPEC reader lives in the traceability module, keeping `sync.py` below 500 lines.
- PLAN.md Planner sync parses explicit `covers:` and `kind:` values and, for 1.2.0 only, reports contradictions with PLAN.json. The Scheduler parser and M1 runtime were not changed. The quality report adds version-gated `coverage`, declared `interfaces`, `verification_categories` and `criteria_without_command`; 1.0.0/1.1.0 report shapes remain unchanged. Documentation explains the fields and the pending T11 M1/M2/M6 gate.
- Updated Planner and methodology integration fixtures to provide SPEC requirement IDs and valid 1.2.0 classification metadata. No Pictures source or approved REQ-024 `PLAN.json` changed.
- Verification: `cd skill/scripts && python3 -I -m unittest discover -s bt_planner/tests` — exit 0, 269 tests; `test_contract.py` 43; `test_md_sync.py` 30; scenarios 8; report 2; canonical golden 3. Methodology `test_plan_integration.py` — exit 0, 21; `test_isolation_plan_parse.py` — exit 0, 4.
- Scoped Ruff (ignoring the two pre-existing `FURB167`/`ISC004` codes in `sync.py`), `py_compile`, JSON parsing, `git diff --check` and `python3 skill/scripts/bitacora.py --project metodologia plan-json check REQ-024` all passed (`OK: PLAN.json is publishable`). Logs: `test-bt-planner-t10.log`, `test-contract-t10.log`, `test-md-sync-t10.log`, `test-scenarios-t10.log`, `test-report-t10.log`, `test-contract-golden-t10.log`, `test-plan-integration-t10.log`, and `test-isolation-plan-parse-t10.log`.
- No provider/model call, benchmark run, 1.2.0 approval/launch or Pictures edit occurred. T11 remains required before 1.2.0 plans can be used with M1/M2/M6.

## T11 — M1/M2/M6 schema 1.2.0 compatibility (2026-10-16)

- M1 now forwards validated task `kind` to M2. M2 prefers the explicit kind and retains title inference for legacy plans. M6 validates and preserves verification `category` in typed serialization and the input hash; absent legacy categories remain omitted, preserving old hashes and runner/verdict behavior.
- Added provider-neutral consumer capability reporting for Planner/M1/M2/M6. Approval, handoff, launch, resume and Scheduler loading of the exact frozen revision fail closed for missing, unknown, malformed, unsupported or mismatched capabilities. The gate stays in the M1 Scheduler adapter; `bt_plan_adapter` does not import downstream consumers directly. A mixed valid/malformed capability marker now returns `unknown`.
- Focused compatibility regression suite: 9 passed. Other recorded T11 suites: M1 loader 23; launch paths 23; plan adapter evidence 5; plan integration 21; Scheduler integration 30; M6 package 67; installed wheel 19. Scoped Ruff, `py_compile` and `git diff --check` passed. Logs are in `../../artifacts/REQ-024-benchmark/` (`test-plan-contract-compat-t11-review-fix.log`, `ruff-plan-contract-compat-t11-review-fix.log`, and the `*-t11.log` files).
- `plan-json check REQ-024` passed; the compatibility CLI reports the current schema 1.1.0 plan supported by Planner/M1/M2/M6. Independent spec and standards reviews approved after the malformed-marker fix. The exact T11 change preserves 1.0.0/1.1.0 compatibility and frozen rollback bytes.
- An expanded Ruff run across already-dirty caller modules exited 1 with 52 findings in pre-existing locations; focused Ruff on T11 implementation and regression files passed. Do not treat the expanded run as green or fold unrelated lint cleanup into T11.
- The broader `test_scheduler_decision_sources.py` suite was run once and exited 1 (3/13 assignment tests failed) after its due-only preflight read live quota and invoked `agy --print=/usage`, updating the local Antigravity usage cache. P-107 records the isolation work required; do not rerun until the preflight is synthetic. No model-generation task ran.
- No provider/model generation, benchmark, 1.2.0 approval/freeze/launch, or Pictures edit occurred. T12–T22 remain.

## T13 — Read-only planning-history projection (2026-10-16)

- Added `bt_plan_history.project_history()` and `bitacora.py plan-json history --kind ...` with validated task/context inputs and a versioned JSON projection. Output excludes route/provider/model/account/effort/quota fields and never converts token units.
- The projection currently returns unknown for all four metrics, with separate stable reasons and null sample counts: T3 found no public cross-route M6 quality aggregate; elapsed time is not proven comparable across routes; retry identity is not correlated; and provider token conventions are not comparable. This is the approved sparse-history behavior, not evidence that observed rates or durations are zero. Missing or unreadable history cannot produce a fabricated value.
- Registered `bt_plan_history.py` in the installed module list so the existing `bitacora` entry point can import the projection from a wheel.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_plan_history.py` — exit 0; 5 tests passed. `test_plan_integration.py` — 21 passed. Installed-package migration suite — 19 passed. Scoped Ruff, CLI JSON smoke, `plan-json check REQ-024` and `git diff --check` passed. Logs: `test-plan-history-t13.log`, `test-plan-integration-t13.log`, `test-package-install-t12-t13.log`, `ruff-t12-t13.log`, `plan-history-cli-t13.log`, `plan-json-check-t12-t13.log` and `diff-check-t12-t13.log`.
- One initial grouped discovery command used `-s tests` from the repository root and exited 5 with zero tests discovered. The same focused commands were rerun from `skill/scripts`; the successful totals above are from those runs.
- After adding history-only parser fields, a compatibility rerun initially found that existing direct `bt_cli_plan.dispatch` callers construct a legacy `Namespace` without those fields. The dispatcher now treats new options as optional for older callers; the 21-test integration suite and 19-test installed-package suite passed on rerun. Preserved the original diagnostic in `test-plan-integration-t13-namespace-failure.log`.

## T12 — Provider-neutral Planner profile and private skills (2026-10-16)

- Updated the shared profile and exactly four Planner-only skills to schema 1.2.0 (`covers`, `interfaces`, task `kind`, verification `category`), the history command, explicit evidence provenance for review findings, and a hard boundary against Planner choosing or ranking providers/services, accounts, models, effort, worker count or quota.
- Added structural checks for the private-skill boundary, routing neutrality, schema fields, history command and review finding labels. No other role references a private Planner skill.
- `cd skill/scripts && python3 -m unittest discover -s tests -p test_planner_profile.py` — exit 0; 5 tests passed. Scoped Ruff passed. No profile installation, model call, quota query, benchmark run or Pictures edit occurred; T14/T15 remain.

## T14 — Provider-neutral Planner invocation adapter (2026-10-16)

- Added `bt_planner_runtime.py` and the public command `bitacora planner invoke`. Provider, account profile and model are explicit; caller-supplied effort passes through unchanged, and omission retains the provider default. The adapter never substitutes a provider, profile, model or effort.
- Claude and Antigravity select their generated native `planner` role. Codex's root CLI has no agent selector, so the adapter supplies the same canonical Planner body and all four private skills through root `developer_instructions`. Task text travels on stdin, not argv. Claude/Antigravity native files must carry the installer marker; hand-authored files fail closed and remain untouched.
- `--req REQ-NNN` resolves the requirement directory; repeatable `--repo ROLE=PATH` supplies workspace mappings. Work-only profile authorization and cwd gates run before prompt construction. Provider subprocesses use argument arrays, a bounded timeout and captured errors; no retry or fallback occurs.
- Fake provider executables cover every `bt_profiles.LAUNCHABLE` runtime. They assert exact account selectors and model/effort, role/skill delivery, REQ/repository context, response parsing, error preservation, timeout handling and one-call/no-fallback behavior. These are local test fixtures; T14 made no real provider or model call.
- Verification: runtime 12 tests; Planner profile 5; installed-package migration 19; scoped Ruff; `py_compile`; CLI help; `plan-json check REQ-024` (`OK: PLAN.json is publishable`); and `git diff --check` all passed. Logs: `test-planner-runtime-t14.log`, `test-planner-profile-t14.log`, `test-package-install-t14.log`, `ruff-t14.log`, `py-compile-t14.log`, `planner-invoke-help-t14.log`, `plan-json-check-t14.log` and `diff-check-t14.log`.
- The first test draft imported `contextlib.redirect_stdin`, which Python 3.14 does not provide; the test now patches `sys.stdin`. This did not affect runtime code or provider selection. T15 remains subject to a refreshed inventory and D-059's existing smoke cap.
