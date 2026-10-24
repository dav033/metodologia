---
req: {{id}}
status: in-progress
created: {{date}}
---
# Plan — {{title}}

## Approach
_2–5 lines: the chosen approach and why (alternatives considered → DECISIONS.md if significant)._

## Global constraints
_Copied from the spec: things every task must respect._

## Tasks
<!-- Small, verifiable steps (one session each), in dependency order. Mark parallelizable ones with ∥.
- [ ] T1 — Define UI contract · kind: design · subplan: <id> · files: design/contracts/<name>@v1.md · verify: review the versioned contract · covers: R1
- [ ] T2 — Implement UI · kind: implement · subplan: <id> · ui: true · after: T1 · files: <paths> · verify: `<command>` · covers: R2, US-1
- [ ] T3 — Visual review · kind: audit · subplan: <id> · after: T2 · verify: inspect captured UI evidence · covers: R3
- [ ] T4 — <hard design problem> · level: architecture · after: T2 · verify: `<command>` · covers: R4
Plans for the scheduler also carry a classified `PLAN.json` (references/plan-contract.md): `bitacora.py plan-json init|check REQ-NNN`.
UI subplans declare `ui {contract, version, design_task, visual_review_task}`; the owner separately approves each exact contract version
before any `ui: true` task starts.
The scheduler (via `PLAN.json`) reads these lines: repo:, after: (task ids), verify: and level: are optional; verify is run by the
verifier only when it is a command inside backticks; level: architecture marks a hard task for the router (it picks the
model and effort). Keep each task to one session of work. -->

## Verification
_End-to-end check that proves the spec's acceptance criteria (tests, running the app, a dry run of the process)._

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
