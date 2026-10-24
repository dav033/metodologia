---
name: design-contract-versioning-and-impact
description: Version UI contracts immutably, record changes and analyze the exact PLAN.json consumers affected by a visual change before implementation proceeds.
---

# Design contract versioning and impact — Designer private skill

Use this skill whenever a design contract is created, approved, changed or consumed. The subplan's `ui.contract` and `ui.version` identify the version used by the plan; project paths follow `design/contracts/<contract-id>@v<N>.md`.

## Version rules

- Create numbered contract files: `design/contracts/<contract-id>@v1.md`, then `@v2.md`, and so on.
- Once approved, a contract file is immutable. Preserve its contents and approval state as an auditable snapshot.
- Any change to an approved contract, including a visually compatible adjustment, creates the next numbered file. Update references only through the plan's approved change process; do not silently redirect consumers.
- Keep drafts clearly marked as drafts. An unapproved draft is not an implementer input.
- The project preview, if enabled, identifies the exact contract id and version it represents. A preview change that changes contract behavior or appearance must be analyzed with the same rules.

## Changelog

Maintain `design/contracts/CHANGELOG.md`. For every new version, record:

```markdown
## <contract-id>@v<N> — <date>
- Status: draft | approved
- Change: <specific visual or interaction change>
- Compatibility: compatible | breaking | undetermined
- Reason: <requirement or decision reference>
- Impact: <subplans, views, flows and PLAN.json tasks consuming the prior version>
- Required action: <review, re-render, adaptation or implementation>
```

Do not overwrite or erase older entries. A missing impact assessment is `undetermined`, not evidence of compatibility.

## Analyze consumers and impact

1. Search the supplied PLAN.json for every `ui` block whose `contract` id matches. Record each consumer by subplan id, `version`, `design_task`, `visual_review_task`, and its UI implementation tasks (`ui: true`).
2. Compare the proposed version with the exact version each consumer uses. Trace affected views, shared components, flows, states, breakpoints, tokens and acceptance criteria to their consuming tasks.
3. Classify each change:
   - **Compatible visual change:** preserves the same interaction, information meaning, navigation and required state behavior; consumers may retain their implementation only after the required visual review verifies the rendered result against the new contract.
   - **Breaking visual change:** alters hierarchy or content, interaction, navigation, flow, state behavior, responsive structure, accessibility behavior or another expectation that requires consumer adaptation or implementation.
   - **Undetermined:** available evidence cannot establish whether consumers remain conformant. Request targeted review or more information.
4. List only affected consumers and the evidence for the impact. A changed contract ancestor does not by itself imply that every downstream subplan must be reimplemented.
5. Record the classification, affected tasks/views and required actions in the changelog and Designer report.

## Implementer approval gate

Implementers consume only the exact contract version recorded in the approved plan and independently approved for use. Designer does not grant that approval. Before work begins, check that the version exists, is approved and matches the plan's contract id/version. If the plan and approved artifact disagree, or approval is absent, stop and report the mismatch for resolution. Never instruct an implementer to use “latest” or a draft.

An approved new version does not automatically update consumers. The plan owner must approve changes to consumer references and tasks. Compatible changes still require the planned visual review to confirm the rendered UI; breaking changes require an explicit adaptation or implementation task for each affected consumer.
