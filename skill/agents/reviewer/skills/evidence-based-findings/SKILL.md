---
name: evidence-based-findings
description: Produce verifiable actionable review findings with stable issue identity, false-positive checks, provenance and non-duplicative coverage.
---

# Evidence-based findings — Reviewer private skill

## Trigger
Load for substantive `spec`/`standards` review, particularly when several related tasks or subplan revisions could repeat the same defect. Borrow techniques from MIT `evidence-code-review` and JUNERDD `code-review`, not their additional orchestrators.

## Procedure
1. Freeze review scope: `project`, base/target SHA, changed concerns, spec/contract IDs and authorized review axis.
2. Build a bounded coverage map: paths/behaviors inspected, call paths followed, tests/guards inspected and unknown impact areas. No obligation to spawn additional agents.
3. For each candidate issue identify trigger, actual observed failure mechanism, authoritative expected behavior, `path:line`, impact and severity. Read mitigations and consumers before claiming a defect.
4. Reject false positives: accepted behavior changes, already fixed paths, mitigated consumers, assumptions unsupported by evidence or 'style nits'. Distinguish questions from defects.
5. Deduplicate semantically using `contract_id + failure_mechanism + triggering_condition + affected_frontier`; preserve independent evidence and link to prior finding IDs instead of emitting copies.
6. On a re-review, check prior findings against the **fix diff and affected call chains**, not the entire original search frontier; reopen only if changed evidence justifies it.
7. Report findings with IDs (when supplied by runtime), status, confidence, severity, affected criterion, source SHA and local remediation; include coverage gaps without falsely approving unverified areas.

## Rule
The current Reviewer output is `AXIS`, `VERDICT`, `FINDINGS`, `CHECKED`. Preserve it until the schema/ledger integration is approved. Do not generate a separate orchestration/review loop or persist findings directly; M6 owns adjudication and history.
