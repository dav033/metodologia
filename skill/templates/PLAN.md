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
- [ ] T1 — Author UI contract <contract>@v1 · kind: design · subplan: <id> · files: design/contracts/<contract>@v1.md · verify: <contract review> · covers: R1
- [ ] T2 — Implement UI behavior · kind: implement · subplan: <id> · ui: true · after: T1 · files: <paths> · verify: `<command>` · covers: R2, US-1
- [ ] T3 — Review rendered UI against <contract>@v1 · kind: audit · subplan: <id> · review_axis: visual · after: T2 · verify: <visual evidence review> · covers: R3
- [ ] T4 — <what> · kind: implement · repo: backend · verify: `npm test -- orders` · covers: R4
- [ ] T5 — <hard design problem> · level: architecture · after: T1 · verify: `<command>` · covers: R5
Plans for the scheduler also carry a classified `PLAN.json` (references/plan-contract.md): `bitacora.py plan-json init|check REQ-NNN`.
The scheduler (via `PLAN.json`) reads these lines: repo:, after: (task ids), verify: and level: are optional; verify is run by the
verifier only when it is a command inside backticks; level: architecture marks a hard task for the router (it picks the
model and effort). `kind: design` routes to Designer; every UI subplan declares its contract, version, design task and visual-review task.
Every `ui: true` task depends on the design task and reads the owner-approved contract. Owner approval is a run-time gate
between design and UI implementation, performed with `bitacora.py design approve|changes REQ-NNN <contract>@vN` or the web
requirement page; it is separate from plan approval. Keep each task to one session of work. -->

## Verification
_End-to-end check that proves the spec's acceptance criteria (tests, running the app, a dry run of the process)._

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
