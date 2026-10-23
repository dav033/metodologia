---
name: adversarial-contract-breakage
description: Stress accepted functional and technical contracts against concretely evidenced negative cases, abuse paths and invariant violations without duplicating normal spec review.
---

# Adversarial contract breakage — Antagonist private skill

## Trigger
Use when the changed scope crosses a public API, event, DB schema, auth boundary, idempotent operation, migration or versioned subplan contract. Do not activate on ordinary style-only changes.

## Procedure
1. Establish the approved invariant, producer and consumers, versioned contract and exact diff baseline. Do not invent undocumented intent.
2. Generate a short set of concrete counterexamples for empty/boundary/malformed inputs, replay, stale version, concurrent calls, partial failures, authorization order and rollback.
3. **Falsify your own suspicion:** inspect checks, callers, existing mitigations and tests; discard any scenario already prevented. The words 'could' or 'maybe' without a path to failure are insufficient.
4. Report only demonstrated/credible paths with triggering preconditions, path:line evidence, affected contract/revision and minimal correction. Include security consequences where supported.
5. Prefer showing one public contract violation that invalidates a real consumer over dozens of generic best practices.

## Boundaries
Read-only, no delegate or writes. Antagonist does not adjudicate product intent, approve/reject a version, mandate broad redesign or start rework. Respect the parent role's one-pass and maximum-eight-findings limits.
