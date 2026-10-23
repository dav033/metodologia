---
name: contract-driven-implementation
description: Implement one approved task against exact functional, interface and optional Designer contract revisions without expanding the task scope.
---

# Contract-driven implementation — Implementer private draft (not approved)

## Trigger and inputs
Use only if this skill is explicitly approved in the master plan and activated in the installed role. Require task ID, functional subplan identity if available, contract/revision, base snapshot, owned files, acceptance criteria, commands and Designer contract/version when UI is in scope.

## Workflow
1. Read governing SPEC/PLAN, task acceptance, producer/consumer interfaces and applicable design contract before editing.
2. Confirm owned surfaces and the exact snapshot. No unapproved contract is presumed stable; report incompatibilities as a bounded `NEEDS_CONTEXT` / concern.
3. Implement the **smallest complete change**, reusing existing code, standard facilities and approved design system; don't silently simplify necessary security, validation, responsiveness or accessibility.
4. For public surface changes, record affected API/event/schema signatures, migration risk and which consumers require verification. Do not rewrite other subplans.
5. Run only the task's approved focused checks, preserve exit/evidence and report what could not be proven.
6. Hand off the diff, source SHA, contract revisions, changed interfaces and unresolved assumptions to independent Reviewer/M6. Never mark a subplan accepted, freeze refs, deploy or push.

## Output
Retain legacy `STATUS`, `SUMMARY`, `CHANGES`, `VERIFICATION`, `COMMITS`, `RULINGS`, `CONCERNS`, with additional contract identity in concise notes only until a machine schema migration is approved. A design ambiguity is escalated to Designer/Planner rather than invented in code.
