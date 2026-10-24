---
name: adversarial-plan-review
description: Challenges a draft plan against the requirement and inspected code before it is returned. Use for every non-trivial Planner output.
---

Source: ctxr-dev/agent-plan-reviewer@2cff4fe (MIT), repository README. Adapted: read-only claims checked against concrete code evidence, with actionable findings. Original: the methodology's `bt_planner` is the deterministic contract and DAG gate; this is a semantic pass by the same planner, not an independent audit.

# Adversarial plan review

Try to find a concrete way the plan could miss the requested outcome, exceed scope, mislead its executor, or fail its stated acceptance criteria.

1. Trace every requirement to one or more task and milestone criteria; identify missing or contradictory coverage.
2. Check each named file, symbol, consumer, command, and precedent against the inspected repository. Mark unverified claims as assumptions or lower confidence; remove invented evidence.
3. For non-trivial task behavior, check that inputs/outputs, decision precedence or algorithm, invariants, preserved contracts, error cases and acceptance are precise enough to prevent the implementer from inventing domain rules. Flag both underspecification and irrelevant implementation detail.
4. Verify requirement-to-task-to-dependency-to-acceptance-to-evidence traceability, including orphan work, shared interfaces and integration ownership. Check that verification distinguishes static, functional, integration, regression and product evidence where applicable; a green test is not automatically product proof.
5. Challenge scope boundaries, migration/compatibility behavior, failure cases, security/privacy, reversibility, task sizing, safe parallelism and unnecessary coordination. Label every finding as a **demonstrated defect**, **plausible risk**, **fact** or **product decision**, and attach provenance: reproducible behavior or command, triggering condition and source, exact file/line reference, or owner decision/decision ID, respectively. Keep assumptions separate from findings. Use costs or execution history only when verified and comparable; otherwise retain unknowns.
6. Check the selected schema's fields (`covers`, `interfaces`, task `kind`, verification `category`, and for 1.3.0 the subplan/composition/UI/external-verification fields) against the requirement and contract. Flag any Planner output that chooses or ranks a provider/service, account, model, effort, worker count or quota; those choices belong to the caller or M2/Scheduler.
7. Inspect `after` edges for missing prerequisites and cycles. Run `bt_planner check` for the deterministic schema, evidence, conflict and graph checks it implements; fix errors in the draft and rerun it before returning.
8. Report only actionable findings with category, severity, trigger, provenance and bounded correction. Distinguish a passed structural check from semantic self-review; this pass is not an independent approval.

## Functional subplan and early-audit challenges

- Challenge fake independence: identify shared mutable files, unfinished implementation reliance, unstated producer contracts and reciprocal implementation/publication dependencies. Merge coupled work or repair the contract/dependency model when two subplans need each other's unfinished code.
- For each likely defect (P-177), identify the introducing task and the **first barrier that can actually observe it**. Count downstream non-barrier tasks before that barrier; reject a terminal-only audit or any chain over six tasks. Add a checkpoint at the earliest useful boundary and ensure later dependent work follows it.
- Verify file claims against repository evidence. A named `expected_paths` entry or a file's existence does not prove behavior; command checks must exercise the criterion, and file references must be real inspected evidence.
- Challenge rework scope: a finding returns only tasks whose result is wrong plus necessary dependents. Do not blanket-rework consumers, infer contract breakage from an implementation change, or call reimplementation without evidence that targeted verification, reintegration, contract change or rework cannot preserve the result.
- For every UI task, require its subplan's `ui {contract, version, design_task, visual_review_task}`, a preceding `kind: design` task, `ui: true`, and Reviewer visual-axis review before the subplan audit. Challenge missing contracts and unjustified `ui: false`; preview remains a project setting, not a plan field.

Also hunt the green-but-hollow plan: a verification that only checks a file exists (`test -s`, `ls`) outside `docs`; an `integration` check that imports modules instead of starting the real entry points together; an `audit` without a findings ledger or without an integration test among the tasks it follows; the same name or signature spelled two ways across tasks; placeholders; a Review focus whose input classes have no owning test. Each is a demonstrated defect when you can point at the line.

Apply the WBS responsibility and calibration checks explicitly. Look for a `test` task that secretly authors tests/configuration, diagnoses/fixes failures or approves the feature; require separate implementation/execution/review outputs where those responsibilities differ. Challenge medium classifications spanning streaming and final responses, persisted/restored UI state or unknown browser harnesses against inspected boundaries, rather than accepting "existing code" as evidence of low reasoning demand. Record why the retained level is defensible or how decomposition removes the uncertainty. Reject unmeasured estimates presented as calibrated and simulation success presented as difficulty/model-quality validation. Report these semantic results separately from `bt_planner check`.

Do not freeze, approve, launch, or implement the plan as part of this review.
