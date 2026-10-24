---
name: evidence-based-findings
description: Produce verifiable actionable review findings with stable issue identity, false-positive checks, provenance and non-duplicative coverage.
---

# Evidence-based findings — Reviewer private skill

## Trigger
Load for substantive review on any axis, particularly when several related tasks, subplan revisions, or visual states could repeat the same defect. Use original adaptations of MIT `evidence-code-review` and JUNERDD `code-review`; their separate orchestration and report writers are excluded.

## Procedure
1. Freeze review scope: project, base/target SHA, changed concerns, specification and contract revisions, and the single authorized axis. Partition the diff into bounded concerns and record areas checked and gaps.
2. For each candidate, establish the trigger, observed failure mechanism, authoritative expected behavior, evidence, impact, severity, and affected criterion/contract. For code findings, include `path:line`; for visual findings, include screenshot evidence ID plus breakpoint × state.
3. Classify the observation as `defect`, `plausible_risk`, `external_block`, or `product_decision`. A product decision is a question, not a proven defect; missing external evidence is a blocker, never a pass.
4. Reject false positives by checking accepted behavior, mitigations, consumers, baseline behavior, and unsupported assumptions. Exclude style-only preferences and duplicate root causes.
5. Provide a stable `semantic_fingerprint` derived from the violated invariant, trigger, affected surface/frontier, and contract/criterion reference; do not derive identity from prose or line number alone. Link a prior finding ID when supplied, but do not resolve or persist its status.
6. On re-review, inspect the fix delta and affected paths; reopen only when changed evidence supports it. Preserve coverage gaps and distinguish executed checks from reviewer judgment.
7. Report the review evidence in the existing `AXIS` / `VERDICT` / `FINDINGS` / `CHECKED` response. Finding evidence may include `semantic_fingerprint`, `severity` (`critical|high|medium|low|info`), `classification`, criterion/contract references, SHAs, and localized remediation.

## Rule
M6 owns finding adjudication, persistence, deduplication, and history. Its current `audit-findings/1` ledger fields are `id`, `severity` (`critical|high|medium|low`), `status` (`open|fixed|accepted`), `summary`, `tasks`, and conditionally `evidence`, `accepted_by: owner`, and acceptance reason. Reviewer metadata such as `semantic_fingerprint`, `classification`, and criterion/contract references is supporting evidence, not a replacement ledger schema; do not claim M6 accepts new ledger fields or write the ledger. Do not generate a separate orchestration/review loop.

## Adaptation provenance
- `akkie76/code-review-skills` `dist/codex/evidence-code-review/SKILL.md` (MIT): scope freeze, concern coverage, evidence validation, and false-positive checks adapted here.
- `JUNERDD/skills` `skills/code-review/SKILL.md` (MIT): coverage IDs, semantic finding identity, and review lineage adapted here; delegation, report files, and re-review automation excluded.
- `trailofbits/skills` `plugins/differential-review/skills/differential-review/SKILL.md` (CC BY-SA 4.0): principles-only reference for risk-scoped changed-path/consumer analysis; no source text copied.
