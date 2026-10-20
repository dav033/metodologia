---
status: draft
execution_contract: requirements-v1
---
# REQ-029 — Autonomous recovery from repeated audit and integration failures

Candidate revision 2. Owner goal paused. This document neither approves nor freezes a plan and does not authorize a rebase, resume, activation or direct product fix.

## Scope and decisions

Preserve R1–R10 and accepted T1–T3. Add one structural mode within the existing M5 → Planner → M1 recovery path: recognize both start INTEGRATION_CONFLICT and M6 integration_gate, capture complete evidence before clipping, distinguish stale accepted descendants/carry lineage from demonstrated ownership/order defects and incompatible requirements, then execute verified convergence. No second supervisor or separate structural retry budget.

CONFLICT-EVIDENCE.json verifies the latest T15b/T15/T15a exact base-to-snapshot diffs are respectively 3/22/1 paths, all within remote/web; no scope escape is demonstrated there. Current T15 snapshot is not an ancestor of historical T15b base (git merge-base --is-ancestor exit 1).

The demonstrated REQ-027 failure is already ordered T3 → T15 → T15a → T15b → T15c (T15c also after T7). T15b att-0142 remains accepted from r7 while new T15 att-0204 and T15a redo arrive in r9. For T6+T7+T15a vs T15b, ordinary give-way chooses T15b, but max_reworks=2 and T15b reworks=2 produce `limit: T15b was already sent back 2 time(s)`. M6 discards that refusal and rejects the candidate again. This proves the missing budget-aware convergence path; it does not prove a missing dependency or product incompatibility.

Protocol decision order: honor owner stop/hold and missing authority; validate complete immutable observation and current accepted-map identity; reject scope escapes; classify lineage versus actual ownership/order defect versus semantic incompatibility; ordinary repair remains first until exhausted or two verified unchanged semantic/source/check observations; acquire the same existing case cycle; obtain one no-tools Planner diagnosis; compile bounded convergence work; independently validate the revision and verification map; wait for natural application quiescence; apply through M1 CAS/journal; execute actual convergence; independently check both sides on that same tree; re-audit and cross-check; close only from official integrated proof. Invalid evidence is a visible blocker, never an unchanged retry. A genuine incompatible product meaning asks its precise question.

One cycle per correlated run/audit-or-conflict lineage; one diagnosis; eight corrective implementation tasks including rebuild/convergence; ordinary task attempt limits; one scoped supplemental attempt per independent audit. Supplemental authority for new convergence work is explicit and counter-preserving; do not call owner=True rework, decisions.answer(by=owner), reset budget_base/waits/reworks, or relabel an exhausted audit as a fresh conflict lineage. No-progress after the cycle ends in a durable blocker. A different verifier receipt ID alone is not progress.

Affected dispatch is fenced during diagnosis; unrelated runnable work continues. Existing M1 revision application requires global quiescence: stop new admissions briefly, let all live work settle naturally, compare source/accepted-map/stop generation again, apply one revision and release the barrier. Do not cancel independent work. Bound the wait through existing leases/deadlines and show an exact quiescence blocker when it cannot settle. Stop wins before diagnosis, freeze, rebase, dispatch and closure. Interrupted prepared/frozen/rebased/committed stages adopt identical identities once; rollback disables recovery on the current schema-capable runtime, retaining authoritative state, current accepted bindings, evidence and counters.

A convergence task cannot depend on both incompatible source snapshots as ordinary ancestors, since it would fail before M3 starts. T3b produces a sealed conflict-bootstrap/1 from the exact failed merge/carry with both original source snapshots, unresolved tree and full marker paths. T4 grants only the named C order with plan/source/accepted-map/stop identities. T5 resolves this one trusted base through existing M3 base_ref wiring; ordinary tasks remain gated. T4a generates C after current nonconflicting prerequisites and supplies both sides as preservation inputs; consumers are rewired to accepted C while preserving unrelated dependencies and original behavior/check coverage. The bootstrap is never acceptance, and downstream must use C's independently verified marker-free result through normal accepted-attempt lookup. T6a proves the failing ordinary bootstrap and safe authorized path, including wrong task, moved map, tampering and stop.

## Inspected evidence

Read original CONFLICT-EVIDENCE.json, CONFLICT-INVESTIGATION.md, INVESTIGATION.md, SPEC.md, PLAN.json, PLAN.md, PLAN-REVIEW.md and INDEPENDENT-REVIEW.md; methodology router, requirements and 1.2.0 contract, Planner private skills and bt_planner README. Read canonical integrator, quality/recovery/executor wiring, diagnosis/policy, core rebase/model/contracts, plan/remediation adapters, existing real-process/integration fixtures and packaging. Read official M1 databases with mode=ro and historical M3 order/manifests. Accepted REQ029 contracts were read with git show at T4 order base 0310c7dc4a78b2589fa5044476470342dd8b583d; T4's cancelled worktree is not accepted evidence. Original independent review is evidence about r1, not approval of this amendment.

- `skill/scripts/bt_scheduler_integrator.py`: _merge clips conflict paths to six and detail to 170 characters before raising; carry() records previous-base behavior and _merge_over_earlier_result tries earlier accepted lineage.
- `skill/scripts/bt_scheduler_quality_adapter.py`: _prior_clashes/_dependents_to_redo/_deliver_one use ordinary rework and reject the candidate if refused; full refusal/source identities are not retained as a typed structural recovery observation.
- `skill/scripts/bt_block_diagnosis.py`: CONFLICT matches only INTEGRATION_CONFLICT; recorded red M6 prefix reproduction returns code/retry_with_note instead of conflict.
- `skill/scripts/bt_scheduler_recovery/policy.py`: integration_conflict is permanent/unknown, while verification_rejected takes ordinary retry before semantic structural classification.
- `skill/scripts/bt_scheduler_core/rebase.py`: fingerprint uses id/after/repository/criteria/verification; ordinary rebase resets budget_base and ordinary rework resets counters. New automatic mode must use T4 scoped counter-preserving authority.
- Accepted base diagnostic_contracts.py: RecoveryProposal /1 permits retry/wait/block/rework_findings only. Add a separate validated structural envelope over accepted DiagnosticStore CAS event payloads, preserving the accepted /1 parser and historical records.

Official source details, SHA identities, known versus missing full paths, non-mutating validation and rebase delta are in REVIEW.md and DELTA.md. Unknown legacy paths are not reconstructed by guessing a truncated `remote/web/src/a` string. Implemented collection/replay must reproduce complete merge evidence from the exact sources in disposable repositories before automatic repair.

## Single writing responsibilities

Every new file has one producer. Existing accepted T2 historical adapter ownership remains in its unchanged frozen task object. T3b is the sole future writer of `bt_scheduler_quality_adapter.py` after accepted T2, explicitly ordered through T3/T3a; this is a sequential lifecycle extension, not simultaneous ownership. No four-task shared-file chain exists. T1–T3 complete JSON task objects remain identical. T3b preserves T2's prior changed-path guard and evidence behavior.


**T1 — Define durable diagnostic cases and semantic progress**: `skill/scripts/bt_scheduler_recovery/diagnostic_contracts.py`; `skill/scripts/bt_scheduler_recovery/diagnostic_store.py`; `skill/scripts/bt_scheduler_recovery/progress.py`; `skill/scripts/bt_scheduler_recovery/history.py`; `skill/scripts/bt_scheduler_recovery/__init__.py`; `skill/scripts/bt_scheduler_recovery/tests/test_diagnostic_cases.py`.

**T2 — Capture immutable full audit evidence and source identities**: `skill/scripts/bt_recovery_evidence.py`; `skill/scripts/bt_scheduler_quality_adapter.py`; `skill/scripts/bt_attempt_history.py`; `skill/scripts/tests/test_recovery_evidence.py`; `skill/scripts/tests/test_attempt_history.py`.

**T3 — Add read-only structured diagnostic transport**: `skill/scripts/bt_block_agent.py`; `skill/scripts/tests/test_recovery_diagnosis.py`; `skill/scripts/bt_planner_runtime.py`.

**T3a — Define structural conflict envelope and bounded decision policy**: `skill/scripts/bt_scheduler_recovery/conflict_contracts.py`; `skill/scripts/bt_scheduler_recovery/conflict_policy.py`; `skill/scripts/bt_scheduler_recovery/tests/test_conflict_policy.py`.

**T3b — Publish full integration evidence before clipping and retain refusal reasons**: `skill/scripts/bt_recovery_conflicts.py`; `skill/scripts/bt_scheduler_integrator.py`; `skill/scripts/bt_scheduler_quality_adapter.py`; `skill/scripts/tests/test_recovery_conflicts.py`.

**T4 — Compile and apply constrained recovery revisions through M1**: `skill/scripts/bt_recovery_apply.py`; `skill/scripts/bt_remediation.py`; `skill/scripts/bt_plan_adapter.py`; `skill/scripts/bt_scheduler_adapter.py`; `skill/scripts/bt_scheduler_core/diagnostic_recovery.py`; `skill/scripts/bt_scheduler_core/model.py`; `skill/scripts/bt_scheduler_core/rebase.py`; `skill/scripts/bt_scheduler_core/recovery.py`; `skill/scripts/bt_scheduler_core/reservation.py`; `skill/scripts/bt_scheduler_core/__init__.py`; `skill/scripts/bt_scheduler_core/tests/test_diagnostic_recovery.py`; `skill/scripts/tests/test_recovery_apply.py`.

**T4a — Build provenance-preserving executable convergence strategy**: `skill/scripts/bt_recovery_convergence.py`; `skill/scripts/tests/test_recovery_convergence.py`.

**T5 — Wire bounded recovery into existing owner and watch lifecycle**: `skill/scripts/bt_scheduler_recovery_adapter.py`; `skill/scripts/bt_scheduler_executor_wiring.py`; `skill/scripts/bt_scheduler_run.py`; `skill/scripts/bt_scheduler_watch.py`; `skill/scripts/bt_scheduler_ops.py`; `skill/scripts/bt_scheduler_decisions.py`; `skill/scripts/bt_cli_scheduler_ops.py`; `skill/scripts/bt_config.py`; `skill/scripts/tests/test_recovery_runtime.py`.

**T5a — Implement pinned runtime staging and conditional host activation**: `skill/scripts/bt_recovery_rollout.py`; `skill/scripts/tests/test_recovery_rollout.py`.

**T6 — Author offline real CLI recovery integration harness**: `skill/scripts/tests/recovery_process_support.py`; `skill/scripts/tests/test_recovery_entrypoints.py`; `skill/scripts/tests/recovery_acceptance.py`; `skill/scripts/tests/fixtures/recovery_req027.json`; `pyproject.toml`; `tests/migration/test_package_install.py`.

**T6a — Author REQ027 structural conflict replay through shipped entrypoints**: `skill/scripts/tests/test_recovery_conflict_e2e.py`; `skill/scripts/tests/recovery_conflict_support.py`; `skill/scripts/tests/fixtures/recovery_req027_conflicts.json`.

**T7 — Run backend regression and entrypoint acceptance**: `skill/scripts/bt_scheduler_recovery/reviews/req029-m1-checks.md`.

**T8 — Audit backend recovery authority and evidence**: `skill/scripts/bt_scheduler_recovery/reviews/req029-m1-audit.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-m1-audit.findings.json`.

**T9 — Cross-check backend recovery independently**: `skill/scripts/bt_scheduler_recovery/reviews/req029-m1-crosscheck.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-m1-crosscheck.findings.json`.

**T10 — Show and control recovery from flow and plan views**: `skill/scripts/bt_flow_bus.py`; `skill/scripts/bt_live_api.py`; `skill/scripts/bt_planstatus.py`; `skill/scripts/bt_page_flow.py`; `skill/scripts/bt_page_plans.py`; `skill/scripts/bt_page_run.py`; `skill/scripts/bt_server.py`; `skill/assets/flow-core.js`; `skill/assets/flow-decisions.js`; `skill/assets/flow.css`; `skill/scripts/tests/test_recovery_views.py`; `skill/scripts/bt_block_diagnosis.py`; `skill/scripts/bt_page_diagnosis.py`; `skill/scripts/tests/test_block_diagnosis.py`.

**T11 — Author visual integration and historical recovery preview checks**: `skill/scripts/tests/test_recovery_supervision_e2e.py`; `skill/scripts/tests/test_recovery_req027_preview.py`; `skill/scripts/tests/recovery_preview_support.py`; `skill/scripts/tests/test_recovery_rollout_receipt.py`.

**T12 — Document approved recovery boundary and rollout rollback**: `skill/scripts/bt_scheduler_recovery/README.md`; `skill/references/modules.md`; `skill/references/plan-contract.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout.md`.

**T13 — Run full recovery supervision and preview acceptance**: `skill/scripts/bt_scheduler_recovery/reviews/req029-final-checks.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-req027-preview.json`.

**T14 — Audit complete autonomous recovery and rollout**: `skill/scripts/bt_scheduler_recovery/reviews/req029-final-audit.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-final-audit.findings.json`.

**T15 — Cross-check final acceptance independently**: `skill/scripts/bt_scheduler_recovery/reviews/req029-final-crosscheck.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-final-crosscheck.findings.json`.

**T16 — Activate the tested runtime and observe bounded REQ027 recovery**: `skill/scripts/bt_scheduler_recovery/reviews/req029-live-rollout.json`; `skill/scripts/bt_scheduler_recovery/reviews/req029-live-rollout.md`.

**T17 — Verify rollout receipts and staged runtime integration**: `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-checks.md`.

**T18 — Audit conditional rollout and real outcome**: `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-audit.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-audit.findings.json`.

**T19 — Cross-check conditional rollout independently**: `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-crosscheck.md`; `skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-crosscheck.findings.json`.


## Interfaces and dependency shape

IF-1–IF-6 retain inherited domain/evidence/transport/application/status/rollout contracts. IF-7 defines structural envelopes and one-cycle correlation; IF-8 publishes complete source-bound observations before clipping; IF-9 defines executable convergence plus an M1 accepted-lineage receipt. IF-10 defines the M1-authorized unresolved bootstrap over the existing M3 base_ref callable. T4 establishes generic application APIs before T4a builds a convergence strategy; T5 consumes both and calls T4 application with T4a output, avoiding a compiler dependency cycle. The producer/consumer interface is data-only across isolated module boundaries.

Main extension: accepted T1 → T2 → T3 → T3a → T3b → T4 → T4a → T5 → T5a → T6 → T6a → T7 → T8 → T9; then existing visual/final and conditional rollout milestones. The runtime's target-plan strategy leaves unaffected work eligible; this implementation-plan order is not an instruction to serialize all future target work. Full graph is derived from `after` below.

## Milestones and tasks

Commands below are planned verification, not passing evidence. Test tasks execute established checks and record failures; implement tasks author harnesses and tests; audits read only and own exactly one findings ledger each. Full task algorithms, source references and classified verification are in PLAN.json.


### M1 — Bounded evidence-driven recovery runtime

Acceptance: Real CLI integration generates scoped corrections after exhausted ordinary budgets, preserves counters and accepted work, verifies the integrated tree and passes two independent audits. Both start and M6 conflicts converge through one existing recovery cycle with complete source evidence and independent preserved behavior on both sides; unchanged retries and edge-only repair are rejected.

- [ ] T1 — Define durable diagnostic cases and semantic progress · repo: skill · covers: R1, R2, R3, R4, R6, R9, R10 · kind: implement · verify: `cd skill/scripts && python3 -m unittest bt_scheduler_recovery.tests.test_diagnostic_cases`
  Extend isolated M5 with recovery-case/1, recovery-proposal/1 and recovery-progress/1 contracts and a durable append-only case/event store.

- [ ] T2 — Capture immutable full audit evidence and source identities · repo: skill · after: T1 · covers: R1, R2, R3, R8, R9, R10 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_evidence.py`
  Create collect_recovery_evidence(rdir, audit, attempt) returning a plain recovery-evidence/1 mapping from official M1 attempts, frozen plan, M3 manifest/base/snapshot, complete validated snapshot ledger, M6 command results and remediation history.

- [ ] T3 — Add read-only structured diagnostic transport · repo: skill · after: T2 · covers: R3, R4, R6, R10 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_diagnosis.py`
  Add diagnose_recovery(project,evidence,request_identity,route) as a separate mode using a verified authorized Planner-role route supplied by existing M2/caller role policy.

- [ ] T3a — Define structural conflict envelope and bounded decision policy · repo: skill · after: T3 · covers: R11, R12, R13, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest bt_scheduler_recovery.tests.test_conflict_policy`
  Validate complete observation/strategy schemas, pure causal classification and one existing-cycle correlation without changing accepted /1 contracts.

- [ ] T3b — Publish full integration evidence before clipping and retain refusal reasons · repo: skill · after: T3a · covers: R11, R12, R13, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_conflicts.py`
  Capture exact paths/sides/source hashes and rework refusal before clipping for both entry points; missing historical evidence blocks recovery.

- [ ] T4 — Compile and apply constrained recovery revisions through M1 · repo: skill · after: T3b · covers: R4, R5, R6, R8, R9, R10, R12, R13, R15 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_apply.py`
  Compile/apply authorized scoped revisions through M1, preserve all ordinary counters and independent checks, and journal stop/CAS/crash-safe application.

- [ ] T4a — Build provenance-preserving executable convergence strategy · repo: skill · after: T4 · covers: R11, R12, R13, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_convergence.py`
  Generate scoped stale-descendant rebuild or owned convergence work with both accepted behaviors, union checks and a real selected converged base.

- [ ] T5 — Wire bounded recovery into existing owner and watch lifecycle · repo: skill · after: T4a · covers: R1, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_runtime.py`
  Route both structural sources into the same durable bounded case, allow unrelated progress and reject unchanged retries or second-cycle relabeling.

- [ ] T5a — Implement pinned runtime staging and conditional host activation · repo: skill · after: T5 · covers: R5, R6, R7, R8, R9, R10 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_rollout.py`
  Implement prepare_recovery_runtime and activate_recovery_runtime in bt_recovery_rollout.py as a bounded host adapter: resolve the accepted upgrade integrated snapshot and M6/audit receipts, archive exactly that tree using existing safe snapshot extraction, stage a private runtime under .state/recovery-runtimes/<source-digest>, run isolated startup/import smoke and never install globally or sweep the local dirty tree.

- [ ] T6 — Author offline real CLI recovery integration harness · repo: skill · after: T5a · covers: R1, R2, R3, R4, R5, R6, R8, R9, R10, R11, R13, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_entrypoints.py`
  Author subprocess-based offline harness using temporary BITACORA_ROOT/config/home, disposable git repositories, fixture provider binaries and existing authorization/routing interfaces.

- [ ] T6a — Author REQ027 structural conflict replay through shipped entrypoints · repo: skill · after: T6 · covers: R11, R12, R13, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_conflict_e2e.py`
  Author offline historical dual-source real-process replay and negative cases; only external providers are fixtures.

- [ ] T7 — Run backend regression and entrypoint acceptance · repo: skill · after: T6a · covers: R1, R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: test · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_entrypoints.py`
  Run established targeted module and methodology regression checks and the T6 process harness.

- [ ] T8 — Audit backend recovery authority and evidence · repo: skill · after: T7 · covers: R1, R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-m1-audit.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T3a,T3b,T4a,T6a`
  Read-only independent review of T1-T7 evidence identity, M1 budget preservation, stale/stop fencing, transport isolation, atomic revision recovery and true entrypoint integration.

- [ ] T9 — Cross-check backend recovery independently · repo: skill · after: T8 · covers: R1, R2, R3, R4, R5, R6, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-m1-crosscheck.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T8,T3a,T3b,T4a,T6a`
  Read-only independent review of the same T1-T7 scope, independently including migration/rollback and falsely green integrations.


### M2 — Visual supervision and read-only rollout preview

Acceptance: Flow and plan supervision and offline REQ027 preview pass with two independent system audits; the tested accepted runtime is ready for conditionally authorized rollout. Flow and plan cards classify structural versus semantic blockers truthfully, and REQ027 dual-source replay demonstrates stop and no manual decision workarounds.

- [ ] T10 — Show and control recovery from flow and plan views · repo: skill · after: T9 · covers: R6, R7, R8, R9, R11, R12, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_views.py`
  Display truthful structural, semantic and missing-evidence states for both prefixes; authenticated stop fences application and dispatch.

- [ ] T11 — Author visual integration and historical recovery preview checks · repo: skill · after: T10 · covers: R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: implement · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_supervision_e2e.py`
  Author tests starting actual bitacora.py web server and scheduler-watch/owner/executor subprocesses together with external-agent fixture binaries from T6.

- [ ] T12 — Document approved recovery boundary and rollout rollback · repo: skill · after: T11 · covers: R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: docs · verify: `test -s skill/scripts/bt_scheduler_recovery/reviews/req029-rollout.md`
  Document architectural rationale and version/migration contracts, initial preview mode for existing runs, proposed one-cycle/eight-correction-task policy, exact blockers and unchanged ordinary budgets.

- [ ] T13 — Run full recovery supervision and preview acceptance · repo: skill · after: T12 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: test · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_supervision_e2e.py`
  Execute T11 real server/watch integration and historical replay, existing module/methodology suites, and disposable official-store CLI preview acceptance.

- [ ] T14 — Audit complete autonomous recovery and rollout · repo: skill · after: T13 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-final-audit.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T8,T9,T10,T11,T12,T13,T3a,T3b,T4a,T6a`
  Read-only independent review of all R1-R10 contracts, real integrated flow, visual stop, historical REQ027 preview and absence of active-run changes.

- [ ] T15 — Cross-check final acceptance independently · repo: skill · after: T14 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-final-crosscheck.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T8,T9,T10,T11,T12,T13,T14,T3a,T3b,T4a,T6a`
  Read-only independent review of the full feature independently, especially adversarial evidence identity, supplemental budgets, restart races and UI versus authority.


### M3 — Conditionally activate and observe one REQ027 recovery

Acceptance: After accepted upgrade audits offline proof and fresh preview, the pinned tested runtime drives one authorized REQ027 recovery to independently verified resolution or a specific genuine blocker, with preserved budgets and independently reviewed receipts. One conditional REQ027 case accounts jointly for audit and structural lineage and proves real convergence or a specific permitted blocker without a second cycle.

- [ ] T16 — Activate the tested runtime and observe bounded REQ027 recovery · repo: skill · after: T15 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: implement · verify: `python3 skill/scripts/tests/recovery_acceptance.py rollout --receipt skill/scripts/bt_scheduler_recovery/reviews/req029-live-rollout.json`
  Operational implementation, conditionally authorized by approval of this plan.

- [ ] T17 — Verify rollout receipts and staged runtime integration · repo: skill · after: T16 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: test · verify: `cd skill/scripts && python3 -m unittest discover -s tests -p test_recovery_rollout_receipt.py`
  Run the T11 established receipt validation plus staged-runtime fixture integration against the integrated T16 receipt artifact.

- [ ] T18 — Audit conditional rollout and real outcome · repo: skill · after: T17 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-audit.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T8,T9,T10,T11,T12,T13,T14,T15,T16,T17,T3a,T3b,T4a,T6a`
  Independent read-only review of the staged-runtime rollout and official captured evidence, complete R1-R10 outcome and true blocker versus fabricated success.

- [ ] T19 — Cross-check conditional rollout independently · repo: skill · after: T18 · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit · verify: `python3 skill/scripts/tests/recovery_acceptance.py audit --ledger skill/scripts/bt_scheduler_recovery/reviews/req029-rollout-crosscheck.findings.json --tasks T1,T2,T3,T4,T5,T5a,T6,T7,T8,T9,T10,T11,T12,T13,T14,T15,T16,T17,T18,T3a,T3b,T4a,T6a`
  Independent read-only review of the staged-runtime rollout and official captured evidence, complete R1-R10 outcome and true blocker versus fabricated success.


## Requirement traceability

R1–R10 remain covered by inherited tasks and checks. R11: T3a/T3b evidence → T5 triggers → T10 views → T6a/T7/T11/T13 replay. R12: T3a classification → T4 permission checks → T4a convergence → T5/T10 blockers → integration/reviews. R13: T4/T4a → T5 → T6/T6a/T7 and T11/T13 prove the actual combined base and both sides. R14: T3a/T5 → T6a/T7/T11/T13 prove the single shared cycle. R15: T4/T5/T5a → T6a/T7/T11/T13 prove stop, CAS, counters and rollback. R16: T6a/T7/T10/T11/T12/T13 and each independent audit. T16–T19 carry the same invariants into future conditionally authorized live receipts. No orphan requirement or unrelated work is intended; validator checks structural coverage only.

## Review focus

1. Already ordered but stale accepted descendant, including the unchanged att-0207 snapshot: T3b tests full lineage, T4a tests real rebuilding and both-side preservation, T6a drives the actual shipped flow. An added edge without a converged tree fails.
2. More than six paths, long names, renamed/deleted files or historical clipping: T3b test_recovery_conflicts verifies complete pre-clipping evidence and safe-path/digest validation; T6a proves incomplete old evidence blocks rather than guessing.
3. Scope escape or incompatible product meaning behind a textual conflict: T3a test_conflict_policy and T4a test_recovery_convergence reject retroactive permission widening, fabricated semantic agreement and first-side-only proof; T6a shows targeted blockers.
4. Exhausted descendant reworks plus duplicate/moved identities across stop/crash/restart: T4 test_recovery_apply and T5 test_recovery_runtime preserve counters/CAS; T6a real-process injection proves one cycle, natural quiescence and rollback without owner rework/notes/card answers.
5. Candidate passes its own checks but breaks an accepted side, or web changes have backend-only proof: T4a tests union coverage, T6/T6a exercise false-green and omitted paths; T11 UI/receipt tests reject premature resolved or stale cached diagnosis.

## Calibration, risks and approval checkpoint

New contract, evidence and convergence tasks are high complexity because they cross state, lineage and independent verification. T3a remains high despite pure functions because action authority and durable audit/conflict correlation are new; medium would omit that unresolved integration contract. T6a is high because it authors actual process orchestration and crash replay, not merely runs tests. T7/T13/T17 remain medium command execution only; audit tasks retain independent evidence interpretation and cannot fix code. Test authoring and running/auditing have distinct files and responsibilities.

History queries for implement/test/audit returned status unknown for duration, consumption, quality and retries; comparable sample counts and estimates of provider quality remain unknown. Numeric task estimates are provisional decomposition allowances, not observed calibrated duration or quota. Structural schema success cannot establish causal correctness or behavioral preservation.

Material assumptions: historical full conflict evidence can be reconstructed from surviving official source objects; otherwise the correct outcome is an evidence blocker. A clean textual merge is insufficient to establish product compatibility. Natural global quiescence can temporarily delay unrelated new dispatch at apply time; it never cancels accepted work or resets budgets. Current owner pause overrides all candidate future activation text. Only the owner/workflow may approve and apply revision 2; this draft does neither.
