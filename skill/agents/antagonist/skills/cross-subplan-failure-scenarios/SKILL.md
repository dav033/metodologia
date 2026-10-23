---
name: cross-subplan-failure-scenarios
description: Identify failures arising only when independently accepted functional subplans are composed, focusing on producer-consumer semantics and localized blast radius.
---

# Cross-subplan failure scenarios — Antagonist private skill

## Trigger
Load for a changed subplan contract, candidate composition, shared persistence boundary or a reported cross-subplan regression. Prefer the actual composition manifest and accepted prior version rather than abstract architecture diagrams.

## Procedure
1. Enumerate only subplans and contract revisions in scope. Establish old accepted composition and new candidate and identify unchanged consumers.
2. Challenge compatibility beyond clean Git merges: schema/field presence, serialized format, IDs, event order, optional/required defaults, transactional boundaries, authorization, retries, error codes and migration paths.
3. Build 'producer does X while consumer expects Y' scenarios. Confirm each using actual code, contract and, when available, tests/evidence; distinguish a proof, plausible unverified risk and a pure question.
4. Confirm existing isolation and fallback paths before reporting. For a failure in `S1@v2 + S2@v1`, describe exactly what interface and consumer are affected; do not suggest rewriting S3 without evidence.
5. Return a bounded failure scenario with trigger, concrete consequence, `path:line`, minimum affected frontier, mitigation/falsification evidence and suggested **additional check**.

## Boundaries
Do not run extra orchestration loops or integrate versions. M6 owns verdicts; M5 owns correction routing. The accepted prior composition must remain untouched.
