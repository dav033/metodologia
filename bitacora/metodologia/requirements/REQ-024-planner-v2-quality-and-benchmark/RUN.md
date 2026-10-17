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

## T15 — Install and smoke-test Planner across configured profiles (2026-10-16)

- Refreshed `profiles list` immediately before the smokes. The same seven profile IDs and five effective accounts from T1 remain; no newly configured profile was included. The redacted inventory is `profiles-inventory-t15.redacted.json`. No quota refresh ran.
- `install_agents.py --agent planner` exited 0 and updated five native profiles: two Claude, two Codex and one Antigravity. All five reported files carried the methodology marker; no hand-authored conflict was skipped. Redacted installation evidence: `planner-install-t15.redacted.json`.
- Prepared and invoked one short smoke per baseline effective account using the existing tier-0 model ladder (Claude `haiku`; Codex `gpt-6-luna`/`medium`; Antigravity `gemini-3.8-flash-low`). Every runtime was preflighted before the first provider call. Each request had a 120-second deadline, and each profile has exactly one durable attempt record. The prompt and returned response text were not stored; results contain only status, exit, response presence/length and elapsed time.
- Claude `claude-personal` (`haiku`): exit 0, response received. Claude `claude-work` (`haiku`): exit 0, response received. Codex `codex-1` (`gpt-6-luna`, `medium`): exit 0, response received. Codex `codex-luis` (same model/effort): exit 0, response received.
- Antigravity `antigravity` (`gemini-3.8-flash-low`): exit 3, stderr was present, no response. It was not retried and no alternate model, profile or provider was used. The redacted five-account result is `planner-smokes-t15.redacted.json`; a matching local CLI log later recovered the cause (see T15 follow-up).
- T15 remains incomplete because one effective account did not return a response. D-059 limits this account to one call; a retry would exceed that cap and requires a new bounded plan/decision. T16 was completed offline; T17–T22 remain gated by T15, so no benchmark-quality conclusion is available.

## T16 — Benchmark harness and pinned rubric (2026-10-16)

- Added the standard-library-only `skill/scripts/plan_bench/` package, `bt-plan-bench` module/entry point and hash-pinned rubric v1. The package verifies manifest bytes before pinned inputs, cells and optional blind reviews; validates the actual `bt_planner check --json` and 1.2.0 `bt_planner report` JSON shapes; verifies plan and metric-source hashes; and builds observed/judged reports without imputing missing cells or producing an aggregate score.
- Cell storage rejects symlinks, missing metadata for partial cells, unexpected files and unapproved review fields. Every measured metric carries its command, local output path and SHA-256. Complete cells require `observed.json`; incomplete cells require an explicit status/reason. The package does not call providers or execute plans.
- `cd skill/scripts && python3 -m unittest discover -s plan_bench/tests -v` — exit 0; 19 tests passed. `python3 -m unittest discover -s tests -p test_plan_bench.py -v` — exit 0; 3 tests passed, including parsing real Planner CLI output. Installed wheel suite `python3 -m unittest discover -s tests/migration -p test_package_install.py -v` — exit 0; 20 tests passed, including `python -m plan_bench`, installed package data and `bt-plan-bench` target.
- Scoped Ruff, `py_compile`, `git diff --check`, `plan-json check REQ-024` and its structural report all exited 0. REQ-024 remains 22 tasks / 6 milestones / 3,480 estimated minutes / 2,310-minute critical path. Logs: `../../artifacts/REQ-024-benchmark/t16-unit-tests.log`, `t16-planner-integration.log`, `t16-package-install.log`, and `t16-ruff.log`.
- T16 does not unblock T17: T15 remains incomplete after the one permitted Antigravity smoke returned exit 3 without a response. No retry, benchmark run, review scoring, model call, Pictures edit, new decision or pending item was made; D-059 and P-108 remain unchanged.

## T15 failure diagnosis and local correction (2026-10-16)

- The matching local Antigravity CLI 1.4.0 log shows silent authentication succeeded, then the executor failed before returning a response because `find_file` was not registered. The redacted diagnosis is `../../artifacts/REQ-024-benchmark/antigravity-planner-t15-diagnostic.redacted.json`; the raw local log was not copied or committed.
- Root cause: `install_agents.py` mapped canonical `Glob` to the SDK-style `find_file` name, but the Antigravity CLI custom-agent tool list uses `find_by_name`. The generated tool list also contained `multi_replace_file_content`, which the installed CLI logged as deprecated/no-op. Updated the adapter to use `find_by_name` and only the supported single-file write/edit tools.
- The first installed-wheel parity test exposed a second defect: package data omitted all four nested Planner skills, so `install-agents` from the wheel generated an incomplete Antigravity agent. Added an explicit nested skill package-data pattern and assertions for all four skill files. The source installer and installed-wheel installer now generate identical definitions.
- Reinstalled the marker-owned Antigravity Planner profile. Verified the generated tool list (`view_file`, `grep_search`, `find_by_name`, `run_command`, `write_to_file`, `replace_file_content`), all four skill files, the methodology resource symlink, and `agy agent` listing `planner`. No provider/model invocation ran after the correction.
- Verification: `python3 -m unittest discover -s tests/migration -p test_entrypoint_parity.py -k test_install_agents_writes_identical_definitions_through_both_entries -v` — exit 0, 1 passed; `python3 -m unittest discover -s tests/migration -p test_package_install.py -k test_resources_travel_in_the_wheel_and_tests_do_not -v` — exit 0, 1 passed. `python3 -m py_compile skill/scripts/install_agents.py tests/migration/test_entrypoint_parity.py tests/migration/test_package_install.py`, `ruff check --select E4,E7,E9,F --ignore E402 skill/scripts/install_agents.py tests/migration/test_entrypoint_parity.py tests/migration/test_package_install.py`, `agy --help` and `agy agent` (lists `planner`) passed. Full Ruff on the touched Python files reports 11 pre-existing findings (EXE001, RUF100, FURB167, SIM102 and PLW1510); the changed code introduces no finding under the targeted correctness rules. `git diff --check` is recorded after this documentation update.
- To enforce R15's no-model-substitution boundary after the recovered CLI fallback warning, the runtime now requires exactly one valid Antigravity `init` event and an exact `init.model` match before accepting a successful response. Missing, duplicate or mismatched model evidence discards the response and fails closed. Official headless-mode docs specify that the `init` payload reports the model in use when `--model` is set: https://antigravity.google/docs/cli/headless/. This checks the CLI-reported selection; it does not establish model quality.
- Regression evidence: `python3 -m unittest tests.test_planner_runtime -v` — exit 0, 14 tests passed, including missing/mismatched model rejection. `python3 -m py_compile skill/scripts/bt_planner_runtime.py skill/scripts/tests/test_planner_runtime.py`, targeted Ruff, and `git diff --check` passed. No provider/model call ran.
- The shared Planner already has four Planner-only skills covering elicitation, DAG decomposition, adversarial review and optional diagram generation. No additional skill or hook was justified by this defect.
- **Live revalidation was pending owner authorization at this point.** D-059's initial Antigravity smoke had been consumed; the later owner authorization and successful validation are recorded in the T15 follow-up below and D-062.

## T16 follow-up — independent reviewer identities (2026-10-16)

- Audit found the manifest validator only required distinct `reviewer_id` values; two reviewers could share both the same profile and model while passing the gate.
- The validator now requires distinct reviewer IDs, profile IDs, and model IDs, and rejects identity strings with surrounding whitespace. Updated the public package README and added regressions for duplicate profiles/models and non-canonical values.
- Verification: `python3 -m unittest discover -s plan_bench/tests -v` — 20 passed; Planner benchmark integration — 3 passed; installed-wheel migration suite — 20 passed; `py_compile`, targeted Ruff and `git diff --check` passed. Log: `../../artifacts/REQ-024-benchmark/t16-reviewer-independence.log`.
- This tightens T16's existing two-independent-reviewer requirement; no manifest was frozen and no reviewer/provider call ran.

## T17 read-only readiness preflight (2026-10-16; T17 not started)

- No `manifest.json` exists in the benchmark store. No corpus, run configuration, or manifest has been frozen.
- Pictures is at commit `75c8749792b893f9e07cb4305d1c9ce2bbfd6a88` with 192 worktree status entries (154 tracked files changed); trainingapp is clean at `01861ad752b4d4ce4f37004df4a9c777c1bc90fe`. Methodology is at `c798a998b6cd09448ea3cfc990c069e1c9caf008` with 230 worktree status entries (112 tracked files changed).
- Future benchmark inputs must use explicitly pinned, clean read-only snapshots; do not expose the current dirty Pictures tree to a planning run. The current commits are observations only, not frozen corpus pins.
- T15 still gates T17–T22. Exact reviewer profile/model identities are an owner decision and are now tracked as P-109. This preflight made no model call, quota refresh, manifest write, or benchmark run.

## T17 read-only corpus follow-up (2026-10-16)

- Resolved the C1 source-path check: the 2026-10-16 rerun `SPEC.md` is byte-identical to the canonical Pictures REQ-017 `SPEC.md` (6,022 bytes; SHA-256 `0cf8fc835a71641004cf0e49cdf3b499fb1e1ab123fc46b089676369c1248b8c`). The canonical `rounds/round-01.json` is present (3,938 bytes; SHA-256 `b45cfb778dfc6a0630440136f8227e1b1ef7a8ad027da09725a54be758577bbf`).
- C2–C5 each have their planned `SPEC.md` and `EXPECT.json`; all eight files are Git-tracked and clean. Their current contents were hashed for later manifest creation, but are not yet frozen.
- Pictures commit `75c8749792b893f9e07cb4305d1c9ce2bbfd6a88` is available as a clean Git archive despite its dirty worktree. `git archive --format=tar` produced 81,111,040 bytes with SHA-256 `a7541074d9d8782cbfefa66a3ea4403aec9ffa21102c3ba014e2c2597f16a6ec`; this is a candidate snapshot, not an approved manifest pin.

## T15 owner-authorized Antigravity launch revalidation (2026-10-16)

- The owner authorized the necessary launch attempts and confirmed the configured accounts are authenticated. D-062 supersedes only D-059's one-call Antigravity T15 cap; benchmark caps and all other smoke records remain unchanged.
- Invoked `bitacora planner invoke` once with provider/profile `antigravity`, model `gemini-3.8-flash-low`, omitted effort, 120-second deadline, and the fixed launch-only sentinel prompt. Exit 0; response received; exact sentinel matched; 16 response characters; no stderr; elapsed 21.418 seconds. The runtime accepted the response only after validating the CLI-reported model against the requested model. No quota refresh, fallback, provider substitution or raw prompt/response storage occurred.
- Redacted attempt record: `../../artifacts/REQ-024-benchmark/antigravity-planner-t15-revalidation.redacted.json`. T15's launch/response criterion is now satisfied across the five baseline effective accounts. This proves launch behavior only; it is not evidence of planning quality. P-108 is closed. T17–T22 still require the frozen reviewer identities (P-109) and remaining task gates.
- No manifest or benchmark cell was created, and no model call or quota refresh ran. T15 and P-109 still gate T17–T22.

## T16/T17 snapshot-boundary hardening (2026-10-16)

- The manifest now requires each case's actual `workspaces/<case>/source.tar`, with its digest matching `repository_sha256`. Large archive hashes stream in chunks; the JSON size limit no longer caps repository snapshots.
- `verify_store` inspects the pinned archive without extracting it and rejects traversal, duplicate entries, links, special files, `bitacora`, Planner scenario fixtures, and `.env` files. `.example`, `.sample`, and `.template` environment templates remain allowed. This also caught that the full methodology archive contains bitacora/oracle paths; C4 must use a sanitized snapshot.
- Verification after this change: benchmark package 23/23, Planner integration 3/3, installed-wheel suite 20/20, scoped Ruff and `py_compile` passed. Logs: `../../artifacts/REQ-024-benchmark/t16-workspace-archive-unit.log`, `t16-workspace-archive-integration.log`, and `t16-workspace-archive-wheel.log`.
- No manifest, benchmark cell, reviewer score, provider call, quota refresh or Pictures edit was created. T15 and P-109 remain gates for T17–T22; D-059 is unchanged.

## P-107 — M2 decision-source test isolation (2026-10-16)

- `M1DecisionPortTests` now injects synthetic fresh quota results and fixes the route-evaluation timestamp to each test request time. This keeps the test fixture's intentionally short quota window valid and prevents due-only preflight from polling local accounts.
- First isolation attempt still failed because its fixed `99–120` observations were compared with the wall clock; the failed output is preserved as `../../artifacts/REQ-024-benchmark/test-m2-decision-sources-p107-isolated.log`. The corrected deterministic-time run passed all 13 tests.
- Adjacent M1/M2 decision integration passed 14 tests; quota-preflight boundary tests passed 7. Targeted Ruff, `py_compile` and `git diff --check` passed. The local Antigravity usage-cache mtime remained `2026-10-16T23:29:34.461856Z`.
- P-107 is closed. No provider, quota refresh, model, benchmark, or Scheduler task ran; P-108 and P-109 remain open, and no benchmark manifest was frozen.

## T17 offline corpus candidates (2026-10-16; not frozen)

- Prepared and validated five `source.tar` candidates under `../../artifacts/REQ-024-benchmark/corpus-candidates/` from pinned repository commits. These are inputs for a future manifest, not a frozen corpus; no `manifest.json` or run cell exists.
- C1 Pictures `75c8749792b893f9e07cb4305d1c9ce2bbfd6a88`: 85,729,280 bytes, SHA-256 `fa68475660ba67d1b9f239e04404335ad9fd7b364cf46f391dd4d26b3a3ec755`.
- C2/C3 trainingapp `01861ad752b4d4ce4f37004df4a9c777c1bc90fe`: each 12,206,080 bytes, SHA-256 `6db119a8c91a562921905b9c13b504176358dc0e26e37e1f30c417c9e246c788`.
- C4 methodology `c798a998b6cd09448ea3cfc990c069e1c9caf008`, excluding all `bitacora` paths and Planner scenario fixtures: 9,523,200 bytes, SHA-256 `8c51fa66fd92fcb63512ee3a1f204a68fe06ddcf9954c61fa2ac4ae8ab82b6a2`.
- C5 combined Maros snapshots (`maros-next` `b8efd6aa01f53257d25a4cdd198e94f97a2f6052`; `maros-nest` `3a4ce7b118dec4148a88c9731e4a798020b3b5bc`): 11,335,680 bytes, SHA-256 `24f444dc5c0c7d879a1428997a0328525fea8904fbc5c483f690093abeae124f`.
- The archive validator passed for C1–C5. A C1 archive-path scan found no `REQ-017` or `PLAN.md`/`PLAN.json` paths. P-108 and P-109 still block manifest freeze and benchmark execution.

## T17 Claude Code launch-isolation research (2026-10-16; not invoked)

- Local Claude Code v2.1.301 exposes `--restricted`, `--agents`, `--settings`, `--add-dir`, `--tools`, `--permission-mode plan`, and `--no-session-persistence`. The official CLI reference says `--restricted` ignores user/project/local settings, confines file tools to the working directories, and keeps managed settings plus explicit `--settings`; this is a candidate control for user/project hook injection.
- The official subagent reference supports session-local JSON/file definitions through `--agents` and a `skills` preload field. The official headless guide documents `--bare` skills from added directories, but local CLI help says `--bare` requires API-key authentication and does not read OAuth/keychain credentials. Do not use `--bare` for the subscription-authenticated arm without separate evidence.
- The reviewed docs do not establish that `--restricted` simultaneously preserves the configured Claude account, loads only the four Planner skills, and excludes all hooks; managed policy can still apply. This combination remains a T17 preflight requirement, not an accepted control.
- Sources: https://code.claude.com/docs/en/cli-reference, https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/headless. No CLI session or model call was launched; no quota was refreshed and no manifest was frozen.

## T17 candidate oracles (2026-10-16; not frozen)

- Prepared hidden-from-planner oracle drafts under `../../artifacts/REQ-024-benchmark/oracle-candidates/`: C1 has nine known REQ-017 defects; C2 has four contract/pagination/unknown-consumer checks; C3 has five data-migration, revision, cutover, backup, and deployment checks; C4 has four adapter/UI/fallback checks; C5 has six audit-history, authorization, response, ordering, UI, and deletion-safety checks.
- The C2 cursor item asks the plan to resolve unspecified ordering and mutation semantics without inventing page size. C3–C5 items are grounded in their SPECs and the pinned source archives; C1 items come from the approved known-defect inventory.
- Validation: all five JSON files parse, all 28 IDs are unique and safe, and every source line anchor resolves in its corresponding `source.tar`. Candidate SHA-256 values: C1 `2e1ff4f1983e16dbfd6c5b2ff387e596042abea9b5ae0b887a6712037cc18a93`; C2 `aa1eaad3850b5c426645e5e31e9b59f4712aea0838e1b71c659676395d34e24b`; C3 `deb534a26c74e57d7f859fb4addcec8eb6ea228d5daa15933731d97ec31f8948`; C4 `6d322e6eb5e5a55d00b4a16470accf92e0d358a4cbb0c99423a29e96fa58945b`; C5 `fb22439f2aad985c2a72e03739ddab0d3922425200ccb78d78fdfb1fb3b89250`.
- Drafts remain outside `workspaces/` and are not included in any Planner input. No manifest, run cell, reviewer record, or provider call was created; P-108 and P-109 still gate T17–T22.

## T16/T17 pre-freeze runtime and profile pinning (2026-10-16)

- A contract audit found that matched arms pinned model, effort, tools, and agent configuration but omitted the configured local account profile and Claude Code runtime version. That left account/resource attribution and runtime reproducibility implicit before the manifest freeze.
- Bumped the benchmark manifest and cell metadata contracts to 1.1.0. Each arm now requires `profile_id`, `runtime_id`, and `runtime_version`; both arms must agree, and every cell must repeat the frozen values. The record stores no credential material or absolute configuration path. D-061 records the boundary.
- No benchmark manifest or cell existed, so no stored data migration was needed. T15 and P-109 still gate T17; this change did not authorize or make any provider call, quota refresh, reviewer selection, or benchmark run.
- Verification: `python3 -m unittest discover -s plan_bench/tests` — 25 passed; scoped Ruff, `py_compile`, and `git diff --check` passed.

## T17 Claude isolation follow-up (2026-10-16; candidate, no session started)

- Read only the settings structure: both local Claude profiles contain user hooks, but neither `/etc/claude-code/managed-settings.json` nor `/usr/local/etc/claude-code/managed-settings.json` exists, and `CLAUDE_CODE_MANAGED_SETTINGS_PATH` is unset. Hook command contents and credentials were not read.
- Claude Code v2.1.301 documents `--safe-mode` as disabling user/project CLAUDE.md, skills, plugins, hooks, MCP, custom agents and memory while leaving authentication/model selection available. `--restricted` loads only managed settings and explicit `--settings`, confines file tools to working directories, and refuses bypass permissions. Local `bt_planner_runtime` selects the requested profile environment without substitution.
- Candidate T17 invocation: run in the pinned cell workspace with `--safe-mode --restricted`, append a hash-pinned prompt bundle made from `agents/planner.md` plus the four canonical Planner skills via `--append-system-prompt-file`, restrict tools to `Read/Grep/Glob`, set `--permission-mode plan`, `--no-session-persistence`, `claude-opus-5-5`, and `high`. This avoids native skill discovery and does not expose the `Skill` tool; safe-mode authentication uses the selected local profile.
- Local version/flag-parser checks passed for the combined flag set using `--help` only (exit 0); no Claude session, provider call, quota refresh, prompt bundle, manifest, or benchmark cell was created. The documented combination is a viable isolation candidate, not yet a runtime-verified T17 control.
- Official references: `https://code.claude.com/docs/en/cli-reference` and `https://code.claude.com/docs/en/sub-agents`.

## T17 first paired Claude configuration candidate (superseded)

- The first paired candidates under `../../artifacts/REQ-024-benchmark-config-candidates/claude-opus-5-5-high/paired/` granted `Write/Edit` with `acceptEdits`. An audit against D-059 found this violated the approved `Read/Grep/Glob` plus `plan`-mode controls. They are retained for audit history only and must not be used. No session or model call ran.
- The initial single-arm bundle was separately marked incomplete because it omitted the role's required methodology references and did not define the read-only output protocol.

## T17 read-only matched-arm Claude configuration candidates (2026-10-16; not frozen)

- Rebuilt the current-V2 and improved-V2 candidates under `../../artifacts/REQ-024-benchmark-config-candidates/claude-opus-5-5-high/paired-readonly/`. Both now match D-059: Claude Opus 5.5 high, `Read/Grep/Glob`, permission mode `plan`, and no session persistence. They use `--safe-mode --restricted` with a hash-pinned prompt bundle; the full role, four private skills, requirements/contract references, module README and each arm's PLAN.json schema are embedded. The task-prompt template asks for labeled `PLAN.md`/`PLAN.json` response blocks, which the host can persist and validate after the model returns.
- Arm A sources the T1 current-V2 snapshot at `196196ef427ab1f066d22faaeece2a40f8aa182c`; Arm B uses the current improved worktree bytes. Each arm has nine pinned source files. After the output-protocol correction, prompt SHA-256: current V2 `fa1fa70e418e761bcec575650a7fdc61ed4da4af9a3dda23df334b8e373466f0`; improved V2 `bb8d1d2994ce4f56126e08aae00292c4fea59af0159ca27f4d465c724c56aa73`. Shared task-template SHA-256: `e25eaa86b8859753826dfdbc1d657cbc37f9710dfd766263a528ccdf712e1823`.
- Re-read and validated all 18 source hashes, both prompt/invocation hashes, and the task-template hash. Local Claude CLI `--help` accepted the exact flags for both candidates (exit 0); this proves option parsing only, not session startup, profile preservation, or tool isolation. The profile/runtime version remain unpinned; P-108 and P-109 remain open. No provider call, quota refresh, manifest, benchmark cell or score was created. D-059 caps are unchanged.
- Corrected a conflict between the Planner role's narrative closeout and the benchmark's labeled-block capture contract: both role bundles now require exactly the task-requested artifact blocks, with scope/findings/risks/assumptions inside `PLAN.md`. Prompt hashes match their invocation and candidate-summary records; the shared task-template hash is unchanged. Re-ran the exact CLI option parse for each arm with `--help`; both exited 0. This validates local parsing only. No Claude session, provider call, quota refresh, manifest, benchmark cell, reviewer record or score was created; P-108/P-109 remain open.

## P-109 three-profile same-task review pilot (2026-10-16; outside formal benchmark)

- The owner authorized one bounded review by each of three candidate reviewer profiles. All received the exact same 47,346-character prompt (SHA-256 `cef4b5bb1e04da115502199763e8c64612905f35d58c6bf448531a267f44f32a`): frozen Opus REQ-017 `SPEC.md`, `PLAN.md`, `PLAN.json`, rubric v1, and the same deterministic-check summary. Source SHA-256 values: SPEC `0cf8fc835a71641004cf0e49cdf3b499fb1e1ab123fc46b089676369c1248b8c`; PLAN.md `78af6ea550fedaff732831f36beb82793bd0ce310999dbcaea69886fb23eda8a`; PLAN.json `724e90831fb356800d0fc122cd9468b85abd3e6376fb2c8ba0ace6639983210e`; rubric `519cf844f79c1aa8b395ef6b08157db803e38abfa2dc29ad6ee6f020bd357885`.
- One initial Codex CLI attempt failed locally because `--ignore-user-config` was placed before `exec`; exit 2 and no provider call. The successful retry used the same prompt hash and is the only Codex usage recorded below.
- Calls ran sequentially from `/tmp` with a JSON response cap of eight findings/900 words. Codex used CLI 0.163.0, profile `codex-2`, requested GPT-6.1 Sol high, read-only sandbox and ephemeral session. Elapsed 53.381 s; usage 26,448 input tokens (12,288 cached) and 2,728 output tokens (1,034 reasoning tokens). Account quota used: 5 h 0% → 1%; 7 d 0% → 0%.
- Claude Code 2.1.301 used profile `claude-work`, requested Sonnet 5.5 high, `--safe-mode --restricted --tools "" --no-session-persistence`, plan permission mode. Elapsed 72.816 s; usage was 22,583 input tokens (2 uncached + 22,581 cache-creation; zero cache-read) and 10,361 output tokens (6,481 thinking tokens). Account quota used: 5 h 0% → 2%; 7 d 87% → 87%.
- Antigravity CLI 1.4.0 used profile `antigravity`, model `gemini-3.8-flash-high` (CLI-reported exact model), plan mode. Elapsed 85.921 s; usage 26,526 input and 11,503 output tokens (9,693 thinking tokens). Gemini quota reported 100% remaining in both 5 h and weekly windows before and after; its separate Claude/GPT pool also remained at 100%.
- The strongest shared finding was missing behavior when the allowed structure list is exhausted, matching SPEC.md's explicit “Too few recommended structures” edge case and PLAN.json's “first unused allowed one” replacement rule. Sonnet and Gemini also questioned the lack of a T3.2 UI-behavior assertion; Codex instead flagged T2.2's source-text assertion as insufficient to prove runtime enforcement/audit. Codex uniquely caught that T4.1's `&&` command chain conflicts with the acceptance criterion requiring every check's exit status. Sonnet produced eight findings, Codex five, and Gemini four; several additional findings remain risks/questions rather than adjudicated defects. Gemini marked the plan `acceptable` while still recommending a fix for the saturation gap, and its suggested duplicate fallback conflicts with PLAN.json's no-duplicate invariant.
- Reported token fields include provider-specific cached-input/thinking categories; wall time includes CLI startup and provider latency. The identical user prompt does not make each CLI's hidden system context or tokenizer identical. Quota percentages are coarse and provider-specific: unchanged weekly/Antigravity readings do not mean zero token use, and these one-call samples do not establish cross-provider quota parity or reviewer superiority. Codex and Claude output metadata did not echo their effective model IDs; their requested IDs were explicit and no fallback model was configured.
- This pilot created no manifest, formal review record, or persistent raw prompt/response artifact, and made no Pictures edits. It is excluded from T19's 66 reviews and does not select the official pair; P-109 remains open.

## Original mission cross-check (2026-10-16)

- Re-read the source mission and checked the current Planner role, its four private skills, and `bt_planner` validation. The existing resources cover algorithmic detail and error behavior, requirement/task traceability, categorized verification, interface ownership, safe dependency edges, risk/assumption provenance and adversarial plan review. This is implementation evidence, not proof of improved generated-plan quality.
- No separate Planner skill or hook change is indicated by the inspected evidence: the four Planner resources already own these planning behaviors, and no reproducible hook-induced planning defect was found. Deterministic checks remain in `bt_planner`.
- The approved D-059 experiment controls current V2 versus improved V2. V1 remains retrospective because its recovered output came from a generic Claude Work delegation with pre-digested evidence, broad session permissions and no pinned repository SHA or runnable V1 Planner profile. The current benchmark cannot establish systematic superiority over V1; report that claim as unproven. D-059 is unchanged.
- T17–T22 remain incomplete behind T15/P-108 and the reviewer-identity gate P-109. No model call, manifest freeze or benchmark cell was created during this cross-check.

## Read-only profile registry recheck (2026-10-16)

- The local registry currently has 8 profile IDs; the read-only methodology routing pool returns 6 account identities. `codex-2` is absent from the T15 captured baseline, which had 7 profile IDs and 5 eligible effective accounts. Its configured home and CLI are present, but the account auth state and model/quota availability were not checked.
- This registry observation does not change D-059: the T15 smoke set remains limited to its approved five accounts. P-109 still requires the owner to choose two distinct reviewer profiles and model IDs before T17; no reviewer was selected and no provider, quota or auth query ran.

## T17/T19 reviewer cost and capability research (2026-10-16; proposal only)

- Read official OpenAI, Anthropic, and Google pricing/model pages and Artificial Analysis Intelligence Index v4.3.2, which combines ten independent evaluations. At `high`, GPT-6.1 Sol scored 50, Claude Sonnet 5.5 scored 47, and Gemini 3.8 Flash scored 41. Their API list rates are respectively $2/$10, $2/$10, and introductory $0.75/$3.75 per million input/output tokens (Gemini rate through 2026-12-31).
- Artificial Analysis measured average Index-task costs of $0.32 for GPT-6.1 Sol high, $0.88 for Sonnet 5.5 high, and $1.24 for Gemini 3.8 Flash high. Total output across that Index was 25M, 52M, and 170M tokens respectively. These are broad benchmark references, not forecasts for the 33 T19 reviews. They show that lower unit pricing does not imply lower token use or lower cost per task.
- Recommended reviewer pair when capability parity and token-rate parity both matter: `codex-1` / GPT-6.1 Sol high plus `claude-work` / Claude Sonnet 5.5 high. Their Index scores differ by 3 points (50/47), and both list at $2/$10 per million input/output tokens. Use the same review prompt, evidence, effort, response schema, and explicit output ceiling; capture per-model usage so observed consumption is reported rather than assumed. This does not guarantee equal task cost: Artificial Analysis measured $0.32/$0.88 per Index task (2.75x), reflecting different token usage on its broad benchmark suite.
- Alternative if matching observed task cost is weighted more heavily: `claude-work` / Sonnet high plus `antigravity` / Gemini 3.8 Flash high. Their Index task costs are closer ($0.88/$1.24, 1.41x), but scores differ by 6 points (47/41), list token rates differ by 2.67x, and Gemini generated 170M versus Sonnet's 52M output tokens on the Index. Neither pair establishes parity in local subscription quota. GPT-6.1 Sol high plus Gemini 3.8 Flash high is the least aligned of these three (score gap 9; task-cost ratio 3.88x).
- API list prices do not predict local Codex, Claude, or Antigravity subscription quota burn; no comparable per-review account telemetry has been measured. P-109 remains an owner choice. No pair was selected, no manifest was frozen, and no reviewer/model call ran.
- Sources: OpenAI model and Codex rate card (`https://developers.openai.com/api/docs/models/gpt-6.1-sol`, `https://help.openai.com/en/articles/11481834-chatgpt-rate-card-business-enterpriseedu-credit-based-pricing`); Anthropic Sonnet 5.5 model/pricing (`https://platform.claude.com/docs/en/models/sonnet-5-5/overview`, `https://platform.claude.com/docs/en/about-claude/pricing`); Google Gemini 3.8 Flash (`https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash`, `https://ai.google.dev/gemini-api/docs/pricing`); Artificial Analysis model evaluations (`https://artificialanalysis.ai/models/gpt-6-1-sol-high`, `https://artificialanalysis.ai/models/claude-sonnet-5-5-high`, `https://artificialanalysis.ai/models/gemini-3-8-flash`).


## P-109 five-model synthetic review ladder (2026-10-16; outside formal benchmark)

- Owner explicitly requested five more reviews in ascending complexity, then added Haiku and GPT-6 Luna at maximum effort. Designed five self-contained requirement/plan cases with 2/3/4/5/6 independent planted defects (20 total): filtering; DAG/ownership/checks; tenant migration/rollback; payment retries/crashes; durable M1/M2 routing. The hidden oracle and input were frozen before calls. Every model received identical input per case, with eight findings/900 words as the common ceiling.
- Completed 25 target calls: `codex-2` GPT-6.1 Sol high and GPT-6 Luna max; `claude-work` Sonnet 5.5 high and explicit `claude-haiku-5-5` max; `antigravity` Gemini 3.8 Flash high. Same-account calls did not overlap within this experiment. Runtime versions: Codex 0.163.0, Claude 2.1.301, Antigravity 1.4.0. No fallback was configured. The collector confirms Claude assistant model metadata; Codex/Gemini effective model IDs were not retained separately from the explicit request.
- All five found 20/20 predeclared roots under explicit coordinator adjudication. Sol, Luna, Gemini and Haiku produced 5/5 usable responses. Sonnet C5 emitted two JSON objects plus prose and 1,105 words: its content contains all six roots but requires manual recovery, so it remains a failed machine-output contract. Duplicate test comments count once; unconfirmed additional concerns and inaccurate auxiliary claims are documented separately, with descriptive precision/F1 bounds rather than unsupported false-positive claims.
- Five-call time sums / total tokens (including cached input) / output tokens (thinking included): Sol 110.326 s / 81,478 / 4,576; Sonnet 115.391 s / 40,845 / 14,864; Gemini 236.387 s / 93,794 / 30,572; Luna 101.768 s / 85,654 / 11,248; Haiku 893.081 s / 254,463 / 224,598. Haiku output includes 215,254 thinking tokens. Different hidden contexts/tokenizers and cache accounting prevent interpreting totals as equal monetary costs.
- Model-identity incident: two preliminary `haiku` alias/max calls on C1/C2 reported `claude-sonnet-5-5`. Both finished and their measurements are preserved, but neither counts toward Haiku or Sonnet-high results. Coordinator interruption prevented a third alias call. Full identifier `claude-haiku-5-5` fixed this pilot's selection; an effective-model guard checked every replacement. Thus 27 actual calls produced 25 target cells. Cause of the alias behavior remains unconfirmed; account defaults were inspected, not changed. Official Haiku ID/max support is linked in the report.
- Quota was read before/after every call and again after completion. These are rounded account observations with reporting lag; the excluded alias calls can affect Claude's account-level delta. The full time/reset/status samples, immediate and delayed account snapshots, exact prompt hashes, final responses, frozen oracle, invocation scripts and adjudication are in [the ladder report](../../artifacts/P109-review-ladder/REPORT.md).
- No Pictures/source implementation, Scheduler dispatch, benchmark manifest, official reviewer pair, approval or frozen plan changed. This synthetic ladder is separate from the formal C1–C5 corpus and T19's 66 records. P-109 remains open; T17 still needs exact reviewer identities and the exact Claude Planner isolation check. One seeded run per cell does not establish general model superiority.


## P-109 three difficult analyses (2026-10-16; outside formal benchmark)

- Completed 15 authorized attempts across the same five routes/accounts: three cross-layer dossiers covering accounting replay, durable scheduling and encrypted export. The hidden oracle froze 24 roots before calls (SHA-256 `89191bd81ed11151889cd62d5dfcc94111be3cbf5a281af869889c3558853e15`); 24 deterministic witness checks passed. Common ceiling: 12 findings/1,800 words; deadline 900s plus 30s watchdog allowance.
- Sonnet high: 24/24 roots, 3/3 valid JSON, 44,821 total tokens, 161.529s summed call time. Sol high: 24/24, 3/3, 61,308 tokens, 192.415s. Luna max: 24/24, 3/3, 79,772 tokens, 247.120s. Haiku max: 24/24, 3/3, 312,867 tokens, 1161.174s. Gemini high: 16/16 roots in its two completed cases, 2/3 valid JSON, 76,708 known tokens plus unknown timeout usage, 1246.805s including H3's 930.118s timeout. No retry, fallback or excluded alias call occurred. Input totals include cache; output includes thinking, never counted twice.
- Sonnet leads raw total tokens and latency in this batch (26.9% fewer tokens and 16.1% less time than Sol). Correction adjudication found Gemini's lease-expiry main fix unsafe and its hash-only evidence alternative insufficient; Sonnet's primary reconciliation fix is sound but its lease-only alternative needs the same safeguard. Luna/Haiku additionally supplied independently verified finite-precision witnesses, kept separate from the frozen denominator. Haiku asserted one unsupported page-cache finding and had a unit slip; details and counterexamples are retained.
- Used quota before→delayed after, 5h/weekly: Codex-2 2%/0%→4%/1%; Claude Work 7%/87%→10%/88%; Gemini 2%/1%→2%/1%. Claude boundary reads returned HTTP429, preventing an exact Sonnet/Haiku split. All three final reads succeeded >120s after the last call. Rounded unchanged quota is not zero cost, including the Gemini timeout.
- Closing evidence checks: 25 assertions passed; 25 JSON files parsed before validation.json creation and four Python artifacts AST-parsed; frozen input/executable hashes, six effective Claude IDs, 14 valid tool-free returned streams and usage subsets verified. Timeout stream/tools/usage remain unknown. No product suite ran; source code was not changed for this pilot. See [full report](../../artifacts/P109-hard-analysis/REPORT.md) and validation.json. P-109 selection and exact T17 isolation remain pending; no formal benchmark manifest, reviewer pair or Scheduler dispatch changed.


## P-109 matched Sol/Sonnet medium-high duel (2026-10-16; outside formal benchmark)

- Owner requested three new extremely difficult cases, comparing GPT-6.1 Sol medium/high with Sonnet 5.5 medium/high. Completed all 12 authorized native calls on Codex-2/Claude Work, one per account at a time, fresh sessions, alternating effort order. Identical prompt per case; 12 findings/1,800 words; 900s plus 30s watchdog. Frozen expected roots: 31 (11/10/10), oracle hash `a3d9f7b9386ec04c4918d2f993db71d6fcd9ff477d9b8e05834d840ec3c14902`; pre-call arithmetic/modeled witnesses passed 31/31.
- All four routes detected 31/31 and returned 3/3 valid JSON. Raw total/output tokens and summed time: Sol medium 58,840/7,000/124.927s; Sol high 61,491/10,122/193.713s; Sonnet medium 41,002/16,868/128.546s; Sonnet high 45,530/21,395/166.021s. High vs medium: Sol +4.5% total/+44.6% output/+55.1% time; Sonnet +11.0%/+26.8%/+29.2%. Input includes cache; output includes thinking.
- Coordinator saved shuffled route-hidden findings/repair judgements before unblinding. Both Sol efforts found an additional supported remote-worker epoch-fencing root and a suitable fix; both Sonnet efforts left it as uncertainty and proposed convergence/epoch-key measures that do not prevent the concrete stale-command trace. Sonnet medium offered an insufficient source-dedup-only retention alternative (primary permanent transfer record is sound); Sonnet high added an unsupported cheapest-first cardinality aside. Both Sonnet variants conflated monetary reservation with resource capacity in an auxiliary witness. High improved some detail but did not add seeded coverage or a verified extra; this sample favors medium, not a general superiority claim. No routing policy or reviewer pair changed.
- Used quota before→delayed after, 5h/weekly: Codex-2 4%/1%→7%/1%; Claude Work 10%/88%→14%/88%. All 24 cell-boundary reads and both delayed account reads succeeded. Efforts share/interleave an account; rounded/lagged quota cannot isolate exact medium/high spend. Final reads were >120s after the last call.
- Closing evidence checks passed 28 assertions; 23 existing JSON artifacts parsed before validation.json creation, seven Python artifacts AST-parsed. Confirmed frozen oracle/runner/base hashes, per-case prompt equality, native call success, six Claude effective IDs, zero observed tools, requested effort order, no within-account call overlap, and usage subsets. Requested effort/Codex effective identity are not independently attested by returned metadata. No product suite or implementation ran. See [full report](../../artifacts/P109-effort-duel/REPORT.md), the saved blind judgements and correction-checks.json. P-109 and exact T17 isolation remain pending.


## Owner reviewer selection (2026-10-17; documentation only)

D-063 records the owner's selection of GPT-6.1 Sol medium and Claude Sonnet 5.5 medium as reviewers, using their own high variants when the work is more difficult. Earlier candidate-pair proposals are superseded as proposals. Exact accounts/profiles remain to be pinned for T17; no difficulty threshold was invented. The owner requested documentation only: no routing/configuration, manifest, approved plan or provider session changed. P-109 remains only for exact formal identities; the isolation check remains pending.


## Planner model research (2026-10-17; no execution)

Researched official API/Codex/Claude prices, capacity, effort and subscription limits, plus Artificial Analysis high-effort configurations. Standard input/output per MTok: Sol 6.1 $2/$10, Opus 5.5 $4/$20, Astra $10/$50. AA v4.3.2 high scores/task costs: Sol50/$0.32, Opus54/$1.82 (default fallback), Astra51/$1.73. This is not a Planner benchmark or quota parity. Opus default effort is medium. Proposed prioritizing Opus-versus-Sol for local cost/quality evidence; no model choice, benchmark scope/configuration or provider call changed. Sources/caveats: `artifacts/planner-model-research-20261017.md`.


## Native Planner model pilot (2026-10-17; in progress, separate authorization)

The owner approved the proposed Opus/Sol/Astra comparison. Nine target calls use existing pinned C2/C3/C4 source/spec/oracle candidate copies, high effort, a verified shared improved-V2 bundle, fresh sessions and isolated read-only workspaces. Host validation is frozen; first-response format/structural failures are preserved without a repair turn. Native tools differ and semantic coordinator grading is only partially blinded. This pilot does not consume or change the formal D-059 matched-arm manifest, reviewer records or approved experiment. Durable protocol, calls and source-backed grading notes are in `artifacts/planner-model-duel-20261017/`; completion will be recorded below.


## Native Planner model pilot completed (2026-10-17; outside formal benchmark)

- All nine authorized calls completed: Opus 5.5 high/Claude Work, Sol 6.1 high and Astra high/Codex-2, three pinned source-backed cases. Same Planner instructions and initial per-case workspace hashes, fresh native sessions, no source changes, no repair/fallback/review-model calls. Host uses 16 frozen validator files. All nine artifact-block captures are valid.
- Numeric totals (input incl.cache + output incl.thinking) / summed native time / illustrative Standard API equivalent: Opus 1,831,268 / 785.768s / $3.568073; Sol 931,915 / 825.387s / $0.830945; Astra 895,593 / 954.910s / $4.279194. These are not subscription invoices; modifiers not established by aggregate telemetry are not inferred.
- Coordinator saved case-batched route-hidden judgements before final unblinding; earlier model-labeled diagnostics/style make this only partial blinding, not independent judging. Behavioral checklist full/partial/missing: Opus 8/5/0; Sol 11/2/0; Astra 12/1/0 of 13. Draft corpus path hints were reconciled with real source: CP3 CLI reporting already exists, and the correct target is the Plan approval tab. All three retain an unresolved uninterrupted-availability design/decision for migration.
- Astra alone protects saved tabs from completed live-pagination omissions by confirming deletion via detail GET. Sol/Opus all-page aggregation does not close that race. Opus migration also leaves absent-key import races, narrows integer ranges, treats missing asset files as warnings and proposes a stale-SQLite data-loss escape. SQLite arithmetic/model traces and official PostgreSQL references are in pagination-counterexample.json/migration-counterexamples.json. No production data loss or PostgreSQL integration execution was observed.
- First-response publication: Astra 1/3; Sol 0/3; Opus 0/3. Eight drafts name integration_task among the same interface's consumer_tasks, forbidden by 1.2.0. The frozen gate rejects them correctly; this does not test or disprove the normal validation-feedback repair loop. Verification-purpose/M6 warnings are also preserved. No bypass, auto-repair, approval or freeze occurred.
- Quota, USED: Codex-2 fresh 0%/1% (5h/weekly) → delayed 54%/10%. Same-window observed per-cell sums: Sol +11pp/+2pp, Astra +43pp/+7pp; these are rounded/lagged observations, not exact causal model prices. Claude first-before returned HTTP401; subsequent cell reads succeeded. After first Opus: 4%/88%; last immediate 15%/90%, delayed 17%/90%; initial usage and delayed 2pp attribution remain unknown.
- Closing evidence checks: 36 passed; 49 JSONs parsed before validation write, 21 Python files AST-parsed. Confirmed frozen cases/bundle/runner/collector/validator, prompt equality, source equivalence/no net changes, three effective Opus IDs, read-tool observations, no native overlap, usage subsets and delayed successful quota reads. The prototype USD output scaling error was corrected before reporting and checked with independent arithmetic. All evaluation failures remain failures in validation.json. No product suite, implementation, Scheduler dispatch, formal manifest/reviewer record or Planner selection changed. Full report: `artifacts/planner-model-duel-20261017/REPORT.md`.


### Owner Planner selection (2026-10-17; D-064)
- Default Astra high; fallback Opus 5.5 xhigh. The owner explicitly corrected the default effort to high. The pilot measured high for all candidates, not Opus xhigh. Documentation only: no runtime/account/manifest changes; account pinning and fallback activation conditions remain unspecified. D-054's explicit selection boundary and the validation gate remain in force.
