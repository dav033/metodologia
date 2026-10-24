---
name: contract-driven-implementation
description: Implement one approved task against exact functional, interface and optional Designer contract revisions without expanding the task scope.
---

# Contract-driven implementation — Implementer private skill

## Trigger and inputs
Load for an assigned task with subplan or Designer contract context. Use the brief's task ID, `subplan_id`,
`subplan_revision`, functional/interface contract revisions, `base_sha`, owned files, acceptance criteria and
verification commands. For UI work, use the approved Designer contract at
`design/contracts/<id>@v<N>.md` from the project repository. Do not invent missing identity or revisions.

## Workflow
1. Read governing SPEC/PLAN, task acceptance, producer/consumer interfaces and applicable design contract before editing.
2. Confirm owned surfaces, `subplan_id@subplan_revision` and the exact base snapshot (`base_sha`). Treat the
   approved contract revision as authoritative; report contradictions or missing approval as a bounded concern.
3. Implement the **smallest complete change**, reusing existing code, standard facilities and approved design system; don't silently simplify necessary security, validation, responsiveness or accessibility.
4. For public surface changes, record affected API/event/schema signatures, migration risk and which consumers require verification. Do not rewrite other subplans.
5. Run only the task's approved focused checks, preserve exit/evidence and report what could not be proven.
6. Hand off the diff, snapshot SHA, subplan identity/revision, Designer contract path/version, changed interfaces
   and unresolved assumptions to independent Reviewer/M6. Never mark a subplan accepted, freeze refs, deploy or push.

## Output
Retain `STATUS`, `SUMMARY`, `CHANGES`, `VERIFICATION`, `COMMITS`, `RULINGS`, `CONCERNS`. Add subplan and contract
identity in concise notes only until a machine schema migration is approved. A design ambiguity is escalated to
Designer/Planner rather than invented in code.
