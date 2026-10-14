---
req: REQ-008
status: approved
created: 2026-10-14
---
# Plan — REQ-008 — Fresh milestone orchestration and bounded context execution

## Approach
Reuse durable marathon scheduling, delegation/router and relay parent lifecycle. Replace the persistent control-tower policy with requirements revalidation followed by fresh, bounded milestone orchestration in the foreground terminal. Add explicit checkpoint rotation and a persisted three-agent recovery protocol. Record the architecture decision before implementation; do not create an unrelated scheduler.

## Bootstrap and activation
M1/M2 must use the existing bounded delegation path while the new launcher is being built. This is a scoped bootstrap exception for implementing the tool itself, not the final user workflow. After real-subprocess PTY checks pass, prepare the concrete checkout command and validate existing-wrapper preconditions. A live client without a compatible parent needs a manual entry command; do not signal it or claim retroactive attachment. Installation stays separately authorized.

## Global constraints
SPEC R1–R9 govern. No commits/push/merge/deletions/global install. Preserve unrelated edits and current runs. One writer, bounded delegates, explicit permissions and verified completion. Numeric policy defaults require telemetry/measurement evidence. Owner approved the concrete plan in chat; execute autonomously within its scope.

## Tasks
### M1 — Entry contract, architecture and context boundaries
- [ ] T1 — Record ADR, update entry/continue/planning policy and implement durable revalidation gate · repo: skill · level: architecture · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_requirements_gate.py' -v` · covers: R1, R8, R9
- [ ] T2 — Implement validated milestone context package and bounded checkpoint contracts with measured defaults, aggregate runtime tool-result budgets and checkpoint reserve · repo: skill · after: T1 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_orchestration_context.py' -v` · covers: R3, R5, R8

### M2 — Same-terminal orchestrator lifecycle
- [ ] T3 — Wire approved planning transition into foreground supervisor and fresh milestone orchestrators, preserving controlling TTY, foreground process group, termios and stop semantics using real-subprocess PTY tests · repo: skill · after: T2 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_orchestration_terminal.py' -v` · covers: R2, R8
- [ ] T4 — Enforce bounded delegation, documentation checkpoint and in-milestone context rotation/resume · repo: skill · after: T3 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_orchestration_rotation.py' -v` · covers: R3, R4, R5, R8

### M3 — Autonomous three-agent recovery
- [ ] T5 — Add persisted proposal/debate/ruling protocol with cheap medium routes and bounded artifacts · repo: skill · after: T4 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_recovery_council.py' -v` · covers: R6, R7
- [ ] T6 — Integrate validated stall taxonomy, council resumption, quota waits, durable nonresetting budgets and incomplete-panel/permission boundaries · repo: skill · after: T5 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_recovery_integration.py' -v` · covers: R5, R6, R7, R8

### M4 — Adversarial end-to-end proof and documentation
- [ ] T7 — Exercise planning-to-terminal rotation, delegation, stall debate, interruption and closing with controlled providers; reconcile all policy and UI consumers · repo: skill · after: T6 · verify: `python -m unittest discover -s skill/scripts/tests -p 'test_fresh_orchestration_e2e.py' -v` · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9
- [ ] T8 — Independent spec/standards audits, regression checks, evidence matrix and owner-facing release limitations · repo: skill · after: T7 · verify: `python -m unittest discover -s skill/scripts/tests -v` · covers: R8, R9

## Verification
Each command names a planned behavioral test, not an existing passing check. Run relevant targeted tests, full regression suite, Python lint and CLI/package checks required by current repo configuration. Controlled-provider tests must prove process/session identity, TTY, bounded inputs, exactly three proposal roles, exchange of critiques, durable ruling, crash recovery and unchanged permissions. Real-provider smoke is separate and cannot replace deterministic evidence; live installation and terminal replacement require the agreed concrete launch path.

## Progress log
- 2026-10-14: Read current code and collected two independent read-only audits. Confirmed missing continuation gate, foreground orchestration transition, aggregate note limits, context-pressure rotation and three-agent debate. Owner confirmed same-terminal replacement, continuation revalidation and context-limit rotation. No production code changed; no tests executed yet.
- 2026-10-14: Continuation revalidated PLAN review status. Added BASELINE-AUDIT.md with concrete acceptance gaps; closing token totals do not prove live context control. Fresh spec review requested before implementation.
- 2026-10-14: Fresh spec review CHANGES_NEEDED: incorporated bootstrap/activation contract, real PTY proof, runtime context reserve and explicit stall/budget semantics. Implementation remains gated on plan approval.
- 2026-10-14: Third consecutive goal-turn approval check: PLAN still review, no owner approval recorded. Planning audits are complete; execution is blocked pending explicit plan approval, not a technical failure. No runtime edits or tests performed.
- 2026-10-14 13:23 review comments (chat): Owner explicitly said apruebo in the conversation.
- 2026-10-14 13:23 plan APPROVED (chat)
