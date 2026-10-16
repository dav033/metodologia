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
5. Challenge scope boundaries, migration/compatibility behavior, failure cases, security/privacy, reversibility, task sizing, safe parallelism and unnecessary coordination. Distinguish demonstrated defects, plausible risks, assumptions and product decisions. Use costs or execution history only when verified and comparable; otherwise retain unknowns. Do not move model/account/quota choices from M2 into the plan.
6. Inspect `after` edges for missing prerequisites and cycles. Run `bt_planner check` for the deterministic schema, evidence, conflict and graph checks it implements; fix errors in the draft and rerun it before returning.
7. Report only actionable findings with severity, trigger, evidence, and bounded correction. Distinguish a passed structural check from semantic self-review; this pass is not an independent approval.

Do not freeze, approve, launch, or implement the plan as part of this review.
