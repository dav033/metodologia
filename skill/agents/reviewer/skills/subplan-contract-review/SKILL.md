---
name: subplan-contract-review
description: Review the effective diff and accepted functional/interface/UI contracts of one subplan for proven fulfillment and deviations without editing or approving runtime state.
---

# Subplan contract review — Reviewer private skill

## Trigger
Activate for an independent diff review whose brief includes `subplan_id`, base and candidate SHA, contract revision and acceptance criteria. Compatible with the existing `spec` Reviewer axis; do not launch additional reviewer rounds automatically.

## Steps
1. Verify the reviewed base/target SHA and artifact revisions before trusting any implementation report. A clean diff alone is not product acceptance.
2. Trace each in-scope requirement to behavior, changed files, API/schema/event/error contract and observable acceptance check. Mark missing expected evidence explicitly.
3. Review what changed **and its direct consumers**, including public surface, negative cases, data migration, backward compatibility and maintained invariants.
4. For UI-related code, review only objective conformance to an approved Designer contract, states and accessibility requirements; aesthetic/pixel comparison belongs to independent visual QA.
5. Distinguish intentional approved evolution from undocumented semantic drift; don't report a product-choice question as a proven bug.
6. Emit each actionable finding with `semantic_fingerprint`, `severity` (`critical|high|medium|low|info`), `classification` (`defect`, `plausible_risk`, `external_block`, or `product_decision`), `criterion_id`, `contract_id@revision`, baseline/target SHA, `path:line`, trigger, consequence, confidence and suggested localized fix. Keep product decisions as questions and external blockers explicit; neither is a proven defect.

## Boundaries
Read-only, fresh context. Never modify code/tests, start implementation, freeze a version or bypass M6. Where actual integration behavior is unknown, request an explicit check from the authorized executor rather than infer success. M6 adjudicates and persists findings. Reviewer metadata supports its existing `audit-findings/1` ledger; do not create or persist another ledger or imply that the ledger accepts additional fields.
