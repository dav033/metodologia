---
req: REQ-029
status: in-progress
created: 2026-10-20
---
# Plan — REQ-029 — Autonomous recovery from repeated audit failures

## Approach
_2–5 lines: the chosen approach and why (alternatives considered → DECISIONS.md if significant)._

## Global constraints
_Copied from the spec: things every task must respect._

## Tasks
<!-- Small, verifiable steps (one session each), in dependency order. Mark parallelizable ones with ∥.
- [ ] T1 — <what> · files: <paths> · verify: `<command>` · covers: R1, US-1
- [ ] T2 — <what> · repo: backend · after: T1 · verify: `npm test -- orders` · covers: R2
- [ ] T3 — <hard design problem> · level: architecture · after: T1 · verify: `<command>` · covers: R3
Plans for the scheduler also carry a classified `PLAN.json` (references/plan-contract.md): `bitacora.py plan-json init|check REQ-NNN`.
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
