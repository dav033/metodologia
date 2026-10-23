---
name: functional-subplan-decomposition
description: Divide a validated master plan into coherent versionable functional subplans, maintaining contracts, audit gates and traceability without choosing providers or executing work.
---

# Functional subplan decomposition — Planner private skill

## Trigger and authority
Load after validating the overarching requirement and inspecting the repository, **before** decomposing the plan into execution tasks. This skill specifies planned outcomes only. Planner never changes product code, approves plans, launches workers, chooses models/accounts or mutates scheduler state.

## Procedure
1. **Preserve the general plan first.** Derive objective, scope, exclusions, requirement IDs, actors, current architecture, external inputs, risks and acceptance; do not replace the main plan with a loose list of subplans.
2. **Choose functional seams.** Each candidate subplan represents an externally observable behavior of roughly medium user-story scale, not an arbitrary directory, technical layer or large epic. State inputs, outputs, invariants, negative cases and independently observable acceptance.
3. **Map owners and contracts.** Identify producer and consumer for every public API, schema, event, UI contract and shared resource. Distinguish dependency on a frozen **contract** from dependency on a completed **implementation**. A consumer can work against a validated contract, but must not treat unaudited implementation as accepted.
4. **Build subplan graph.** Assign stable IDs, requirement coverage, interface versions and bounded dependencies. Detect cycles and mutually-owned files; propose scope/contract correction when a purportedly independent subplan cannot stand alone.
5. **Plan verification borders.** Every subplan gets task-level checks, a real-entrypoint integration test, independent audit, findings ledger and acceptance identity. For risky/large subplans add internal checkpoints early; do not defer all adversarial review to the final milestone.
6. **Plan composition.** Define what will be tested with real producer/consumer implementations together, what can be reused by evidence and which conditions trigger reverify, reintegrate, change contract, rework or actual reimplementation.
7. **Recognize UI.** For a subplan that creates or significantly changes UI, declare a prerequisite Designer contract, approved version, responsive/state/flow coverage and independent visual QA. Preview is configurable and optional; **design contract is not**.
8. **Classify external checks.** Inventory needed environments and secret **names/locations only**, distinguish local/authorized external/manual evidence, and plan a recoverable blocked result when permission/environment is missing.
9. **Challenge completeness.** Use existing WBS and adversarial-plan-review skills: trace every requirement → subplan → task → acceptance → evidence; identify orphan work and unresolved conflicts. Treat examples as **conceptual** until a new contract is implemented.

## Contract compatibility
- `PLAN.json` schema 1.2.0 has **no native subplan object**. Never insert `subplans`, `parent_id`, nested tasks or new status fields into that version.
- Until a compatible schema revision or atomically frozen auxiliary manifest is implemented, express the design as a **non-executable proposed artifact** and retain all approved legacy PLAN.json rules.
- The schema choice (new version vs separate SUBPLANS.json) remains an open architecture decision; do not resolve it by silently forging accepted plan data.
- The Planner does not decide which previously accepted subplan versions become invalid: it plans impact criteria for independent review.

## Output
Return a human-readable subplan table with ID, bounded objective, requirements, produced/consumed contracts, dependent IDs, internal task owners, testing/checkpoints, version gate and UI dependency. Add explicit unresolved contracts, proposed manifest migration, graph validation limits and an example P-177-style late-finding scenario. Mark *planned* tests as planned, not passing.
