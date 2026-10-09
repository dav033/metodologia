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
- [ ] T1 — <what> · files: <paths> · verify: `<command>` · covers: R1, US-1
- [ ] T2 — <what> · repo: backend · after: T1 · verify: `npm test -- orders` · covers: R2
Marathon mode parses these lines: repo:, after: (task ids) and verify: are optional; verify is run by the
supervisor only when it is a command inside backticks. Keep each task to one session of work. -->

## Verification
_End-to-end check that proves the spec's acceptance criteria (tests, running the app, a dry run of the process)._

## Rulings
<!-- Judgment calls made during execution without asking:
- T3: <what I decided> — <why> — cost if wrong: <low/med/high> -->

## Progress log
<!-- One line per meaningful step, so work survives a context reset. -->
