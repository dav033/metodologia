---
name: integration-compatibility-review
description: Examine factual semantic compatibility of accepted subplan revisions and a candidate composition, separating Git conflicts from API and runtime incompatibilities.
---

# Integration compatibility review — Reviewer private skill

## Trigger
Use for candidate `S1@v2 + S2@v1 ...` or a changed public contract. Prefer inspecting the exact composition manifest and candidate Git snapshot; do not reconstruct a different combination silently.

## Steps
1. Record candidate composition ID, all subplan versions/contract hashes and the prior accepted composition. Confirm the diff baseline matches the manifest.
2. Record the observation classification (`defect`, `plausible_risk`, `external_block`, or `product_decision`) separately from its compatibility category: `git_text_conflict`, `contract_change`, `behavioral_incompatibility`, `environment_block`, `missing_integration_evidence`, or `unrelated`. Treat merge success only as syntactic evidence.
3. Identify concrete producer/consumer pairs via contract and code references. Verify migration/serialization, ordering, side effects, API/DB/event schemas, feature flags and deployment config at their actual boundaries.
4. Compare failed verification to actual acceptance criterion and identify the **smallest affected frontier**. Separate `needs_reverification`, `needs_reintegration`, `needs_adaptation` and `proven_reimplementation`; only the coordination engine authorizes action.
5. Report each finding with a stable `semantic_fingerprint`, `severity` (`critical|high|medium|low|info`), classification, affected criterion and contract revision, composition identities, root evidence, confirmed consumers, and bounded follow-up verification. State what evidence is missing when appropriate. Never infer that all descendants must be rewritten because an ancestor changed.

## Output
Include affected composition and contract identities, root evidence, confirmed consumers and bounded follow-up verification. Read-only; M6 adjudicates, deduplicates, and persists findings in its existing `audit-findings/1` ledger, and M5 plans rework. Reviewer-only identity, classification, and criterion/contract metadata are evidence, not an alternate ledger schema or adjudication.
