---
status: approved
execution_contract: requirements-v1
---
# REQ-029 — Autonomous recovery from repeated audit failures

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: approved · ejecución: running · hitos 0/3 · tareas 1/20 · generado: 2026-10-20T15:40:46-05:00

**M1 — Bounded evidence-driven recovery runtime** · dificultad alta · 1/10

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1 | Define durable diagnostic cases and semantic progress | alta | completada | gpt-6-luna | codex-1 | 1 |
| T2 | Capture immutable full audit evidence and source identities | alta | en curso | gpt-6-luna | codex-1 | 1 |
| T3 | Add read-only structured diagnostic transport | alta | pendiente | — | — | 0 |
| T4 | Compile and apply constrained recovery revisions through M1 | alta | pendiente | — | — | 0 |
| T5 | Wire bounded recovery into existing owner and watch lifecycle | alta | pendiente | — | — | 0 |
| T5a | Implement pinned runtime staging and conditional host activation | alta | pendiente | — | — | 0 |
| T6 | Author offline real CLI recovery integration harness | alta | pendiente | — | — | 0 |
| T7 | Run backend regression and entrypoint acceptance | media | pendiente | — | — | 0 |
| T8 | Audit backend recovery authority and evidence | alta | pendiente | — | — | 0 |
| T9 | Cross-check backend recovery independently | alta | pendiente | — | — | 0 |

**M2 — Visual supervision and read-only rollout preview** · dificultad alta · 0/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T10 | Show and control recovery from flow and plan views | alta | pendiente | — | — | 0 |
| T11 | Author visual integration and historical recovery preview checks | alta | pendiente | — | — | 0 |
| T12 | Document approved recovery boundary and rollout rollback | media | pendiente | — | — | 0 |
| T13 | Run full recovery supervision and preview acceptance | media | pendiente | — | — | 0 |
| T14 | Audit complete autonomous recovery and rollout | alta | pendiente | — | — | 0 |
| T15 | Cross-check final acceptance independently | alta | pendiente | — | — | 0 |

**M3 — Conditionally activate and observe one REQ027 recovery** · dificultad alta · 0/4

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T16 | Activate the tested runtime and observe bounded REQ027 recovery | alta | pendiente | — | — | 0 |
| T17 | Verify rollout receipts and staged runtime integration | media | pendiente | — | — | 0 |
| T18 | Audit conditional rollout and real outcome | alta | pendiente | — | — | 0 |
| T19 | Cross-check conditional rollout independently | alta | pendiente | — | — | 0 |
<!-- bitacora:status:end -->

**Draft: one owner approval authorizes the system upgrade and conditional REQ-027 recovery below.** Full algorithms, classifications, R1–R10 coverage, interfaces and commands are in PLAN.json. Role `skill` = whole `/home/david/dev/metodologia` repository.

## Design to approve

Extend existing M5 adapter, Planner/M2 routing, revision application and watcher; M1 owns state, M4 observes. No new supervisor. One cycle/run/audit lineage, one diagnostic invocation, eight correction tasks maximum, one supplemental attempt per independent audit. Preserve ordinary counters. New runs record this automatic policy at launch; only REQ-027 is conditionally enabled among existing runs. No second confirmation is required; genuine missing permissions/product choices still block.

Bind complete findings/checks to immutable run/plan/attempt/base/snapshot. Ledger-local IDs identify occurrences; semantic owner/path/symptom relations identify recurrence, with uncertainty explicit. Counts/signatures cannot prove progress. Two unchanged verified semantic/source/check observations may trigger diagnosis. Independent integrated checks alone establish fixed/regressed/resolved.

Causal planning uses a verified authorized Planner-role route from existing M2/caller policy, never fixed card-advice defaults. No-tools allowlist, isolated configuration and MCP/app denial are mandatory; unsupported enforcement blocks. Proposals permit only scoped correction, additive verification repair or refreshed integrated audit. Preserve frozen criteria/checks; new symptom tests must be red for the real bug on captured broken source and green after correction. No raw model shell/state actions.

Compile all affected owner checks plus symptom oracle, then compare actual snapshot changes before PASS. Uncovered authorized surfaces require verification replanning/rerun in the same case; other edits reject. Backend-only checks cannot accept web changes. Corrections→integration→independent audit/cross-check. M1 scoped grants, hash/generation fencing and prepared/frozen/rebased/committed journal preserve budgets and prevent duplicate/stale application. Stop wins every race.

After accepted upgrade audits/offline proof/fresh REQ-027 preview, stage exactly the tested accepted snapshot in a private runtime, quiesce/back up only REQ-027 and restart its watcher via the new absolute entrypoint. No dirty-tree sweep/global install/handwritten product fixes. Observe system-generated corrections through independent re-audit; record resolution or a specific genuine blocker. Live evidence becomes a captured, offline-validated receipt, never an M6 dependency on private .state.

## Evidence

INVESTIGATION.md/EVIDENCE.json: 11 attempts, 10 snapshots, 9 finding sets, 2 rounds. Caddy fixed; E2E persists; build/OAuth new. Inspected `skill/scripts/bt_attempt_history.py:23` number stripping, `bt_remediation.py:165` first-owner-check selection, att-0196 web diff with backend-only checks, M1 `rebase.py:126` counter resets, full M5/runtime/Planner/flow consumers and tests. Root pyproject omits four existing diagnostic/history modules; T6 repairs packaging alongside new modules. Installed-wheel and actual entrypoint tests are explicit.

## Single file owners

Prefixes are inherited within each group. Each path has one writing task; proposed new reports directory is `skill/scripts/bt_scheduler_recovery/reviews/`.

- **T1** M5 facts/store/progress: `skill/scripts/bt_scheduler_recovery/`: `diagnostic_contracts.py`, `diagnostic_store.py`, `progress.py`, `history.py`, `__init__.py`; `skill/scripts/bt_scheduler_recovery/tests/`: `test_diagnostic_cases.py`.
- **T2** evidence/coverage guard: `skill/scripts/`: `bt_recovery_evidence.py`, `bt_scheduler_quality_adapter.py`, `bt_attempt_history.py`; `skill/scripts/tests/`: `test_recovery_evidence.py`, `test_attempt_history.py`.
- **T3** Planner diagnosis transport: `skill/scripts/`: `bt_block_agent.py`, `bt_planner_runtime.py`; `skill/scripts/tests/`: `test_recovery_diagnosis.py`.
- **T4** compiler/M1 grants: `skill/scripts/`: `bt_recovery_apply.py`, `bt_remediation.py`, `bt_plan_adapter.py`, `bt_scheduler_adapter.py`; `skill/scripts/bt_scheduler_core/`: `diagnostic_recovery.py`, `model.py`, `rebase.py`, `recovery.py`, `reservation.py`, `__init__.py`; `skill/scripts/bt_scheduler_core/tests/`: `test_diagnostic_recovery.py`; `skill/scripts/tests/`: `test_recovery_apply.py`.
- **T5** runtime/policy wiring: `skill/scripts/`: `bt_scheduler_recovery_adapter.py`, `bt_scheduler_executor_wiring.py`, `bt_scheduler_run.py`, `bt_scheduler_watch.py`, `bt_scheduler_ops.py`, `bt_scheduler_decisions.py`, `bt_cli_scheduler_ops.py`, `bt_config.py`; `skill/scripts/tests/`: `test_recovery_runtime.py`.
- **T5a** pinned host activation: `skill/scripts/`: `bt_recovery_rollout.py`; `skill/scripts/tests/`: `test_recovery_rollout.py`.
- **T6** harness/package metadata: `skill/scripts/tests/`: `recovery_process_support.py`, `test_recovery_entrypoints.py`, `recovery_acceptance.py`; `skill/scripts/tests/fixtures/`: `recovery_req027.json`; `./`: `pyproject.toml`; `tests/migration/`: `test_package_install.py`.
- **T7** run checks: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-m1-checks.md`.
- **T8** audit: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-m1-audit.md`, `req029-m1-audit.findings.json`.
- **T9** cross-check: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-m1-crosscheck.md`, `req029-m1-crosscheck.findings.json`.
- **T10** visual supervision: `skill/scripts/`: `bt_flow_bus.py`, `bt_live_api.py`, `bt_planstatus.py`, `bt_page_flow.py`, `bt_page_plans.py`, `bt_page_run.py`, `bt_server.py`; `skill/assets/`: `flow-core.js`, `flow-decisions.js`, `flow.css`; `skill/scripts/tests/`: `test_recovery_views.py`.
- **T11** HTTP/preview/receipt harness: `skill/scripts/tests/`: `test_recovery_supervision_e2e.py`, `test_recovery_req027_preview.py`, `recovery_preview_support.py`, `test_recovery_rollout_receipt.py`.
- **T12** rollout docs: `skill/scripts/bt_scheduler_recovery/`: `README.md`; `skill/references/`: `modules.md`, `plan-contract.md`; `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-rollout.md`.
- **T13** run final checks: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-final-checks.md`, `req029-req027-preview.json`.
- **T14** audit: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-final-audit.md`, `req029-final-audit.findings.json`.
- **T15** cross-check: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-final-crosscheck.md`, `req029-final-crosscheck.findings.json`.
- **T16** conditional host rollout: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-live-rollout.json`, `req029-live-rollout.md`.
- **T17** run receipt checks: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-rollout-checks.md`.
- **T18** audit: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-rollout-audit.md`, `req029-rollout-audit.findings.json`.
- **T19** cross-check: `skill/scripts/bt_scheduler_recovery/reviews/`: `req029-rollout-crosscheck.md`, `req029-rollout-crosscheck.findings.json`.

## Milestones and tasks

IF-1–IF-6 define domain, evidence, transport, application, supervision and host-receipt contracts in PLAN.json. Every audit follows real-entrypoint integration and has one findings ledger. Commands are planned, not passing evidence.

### M1 — Bounded evidence-driven recovery runtime

Acceptance: Budget-preserving automatic recovery passes real CLI/package proof and both reviews.

- [ ] T1 — Define durable diagnostic cases and semantic progress · kind: implement
  Deduplicate cases; preserve recurrence/uncertainty and legacy records.
- [ ] T2 — Capture immutable full audit evidence and source identities · after: T1 · kind: implement
  Full immutable evidence; uncovered actual changes block PASS.
- [ ] T3 — Add read-only structured diagnostic transport · after: T2 · kind: implement
  Authorized Planner route; no tools/MCP; failures block.
- [ ] T4 — Compile and apply constrained recovery revisions through M1 · after: T3 · kind: implement
  Atomic revision; preserved counters; full nonweakening red/green proof.
- [ ] T5 — Wire bounded recovery into existing owner and watch lifecycle · after: T4 · kind: implement
  One automatic cycle; restart/stop/no-repeat policy; legacy decisions retained.
- [ ] T5a — Implement pinned runtime staging and conditional host activation · after: T5 · kind: implement
  Stage pinned code; ownership/backup/stop/idempotent activation guards.
- [ ] T6 — Author offline real CLI recovery integration harness · after: T5a · kind: implement
  Author CLI crash/false-green tests; register/import all packaged modules.
- [ ] T7 — Run backend regression and entrypoint acceptance · after: T6 · kind: test
  Execute backend, installed-wheel and real entrypoint checks only.
- [ ] T8 — Audit backend recovery authority and evidence · after: T7 · kind: audit
  Independent backend ledger: no open critical/high.
- [ ] T9 — Cross-check backend recovery independently · after: T8 · kind: audit
  Own full backend assessment: no open critical/high.
### M2 — Visual supervision and read-only rollout preview

Acceptance: Visual stop and offline preview pass real server/runtime proof and both reviews.

- [ ] T10 — Show and control recovery from flow and plan views · after: T9 · kind: implement
  Truthful status/evidence and working authenticated stop.
- [ ] T11 — Author visual integration and historical recovery preview checks · after: T10 · kind: implement
  Author real HTTP/runtime, preview and receipt-provenance tests.
- [ ] T12 — Document approved recovery boundary and rollout rollback · after: T11 · kind: docs
  Version/migration/rollback and conditional rollout instructions.
- [ ] T13 — Run full recovery supervision and preview acceptance · after: T12 · kind: test
  Execute full integration/package/preview checks; report results only.
- [ ] T14 — Audit complete autonomous recovery and rollout · after: T13 · kind: audit
  Independent system ledger: no open critical/high.
- [ ] T15 — Cross-check final acceptance independently · after: T14 · kind: audit
  Own complete system assessment: no open critical/high.
### M3 — Conditionally activate and observe one REQ027 recovery

Acceptance: One authorized pinned-runtime REQ027 recovery reaches independent resolution or a genuine blocker; both receipt reviews pass.

- [ ] T16 — Activate the tested runtime and observe bounded REQ027 recovery · after: T15 · kind: implement
  Use tested staged runtime; one system-generated REQ027 recovery; truthful outcome receipt.
- [ ] T17 — Verify rollout receipts and staged runtime integration · after: T16 · kind: test
  Execute staged integration and captured receipt checks, no live sandbox access.
- [ ] T18 — Audit conditional rollout and real outcome · after: T17 · kind: audit
  Independent rollout/outcome ledger: no open critical/high.
- [ ] T19 — Cross-check conditional rollout independently · after: T18 · kind: audit
  Own rollout assessment: no unsupported success or open critical/high.

## Review focus and limits

1. Renumber/count/split-merge: T1/T2 and T11 historical replay.
2. Stale base/build-blocked E2E: T2/T4/T6 snapshot and not_run tests.
3. Duplicate/lease/freeze/rebase/takeover: T1/T4/T5a/T6 process tests.
4. Unsafe/no-tools/routing/nonreproducible oracle/exhaustion: T3–T6 negative tests.
5. Uncovered web paths/stop/old decisions/wrong runtime: T2/T4/T6/T10/T11/T17 coverage, HTTP and receipt tests.

Implement tasks author tests; T7/T13/T17 only execute/report; auditors only write their report/ledger. Harnesses start shipped watcher/owner/executor/verifier/server; only external agents are fixtures. Disposable roots supply their own config/history; M6 never needs ignored env or checkout .git. Host T16 acts outside its subsequent sandbox verification under the approval's explicit authorization.

History metrics for implement/test/audit are unknown (duration seconds; null sample counts). Minutes are provisional allowances. M1 migration/application and process/host integration remain high complexity; no execution resources are selected. Rollback holds recovery and preserves journals/evidence/outcomes; rollback disables recovery on the same tested schema-capable runtime; no authoritative DB restore, counter reset or older binary without proven schema compatibility. T12 documents the ADR substance for normal execution publication.

## Validation

`python3 /home/david/dev/metodologia/skill/scripts/bitacora.py --project metodologia plan-json check REQ-029`: **exit 0, OK: PLAN.json is publishable** (34 warnings: 24 newly planned checks and 10 unexecuted product-evidence notices). Remaining planned-check/product-evidence warnings are not implementation passes. No approval/freeze/launch, host activation or code implementation has occurred. PLAN-REVIEW.md is semantic self-review, not independent approval.
- 2026-10-20 15:35 review comments (chat): Owner explicitly approved: “ejecuta el req 29”.
- 2026-10-20 15:35 plan APPROVED (chat)
