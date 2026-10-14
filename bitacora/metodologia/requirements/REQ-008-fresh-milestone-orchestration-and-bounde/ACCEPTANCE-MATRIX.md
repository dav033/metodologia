# REQ-008 — Acceptance evidence matrix

This is a live coverage map, not a completion claim. Commands and outcomes are recorded
in PLAN.md and milestone evidence documents; an existing fixture is not a passing run.

Owner paused execution after T4 corrections. Final focused evidence is 139 affected tests
and 10 wheel/install tests, all exit 0, plus scoped ruff; see REPORT.md. Defaults remain
unchanged. Earlier T4 review gaps below were corrected with regression evidence, but final
coordinator acceptance, M3/M4 and the full completion audit remain pending.

| Requirement | Behavioral evidence | Status / remaining acceptance |
| --- | --- | --- |
| R1 entry and continuation | `test_requirements_gate.py`: retained approval, drift/unresolved decisions, removed marker, launch/force/run guards and pause/dispatch revalidation | M1 independently approved; default policy reconciliation remains M2/M4. |
| R2 same terminal | `test_orchestration_terminal.py`: real PTY, own foreground PGID in same SID/TTY, planning exit, SIGTTIN, interruption, descendants and restoration | T3 final 21/21, exit 0, standards approved; production reasoning integration remains T4. |
| R3 bounded milestone scope | `test_orchestration_context.py`: mandatory authority, aggregate UTF-8 receipts, oversized rejection and bounded hooks/history | M1 APIs verified; actual runtime reads/results require T4 proof. |
| R4 delegation and documentation | `test_orchestration_context.py`: supervised task/audit/FINAL contracts; T4 controlled-PATH CLI with real implementation checks | T4 review requires FINAL crash settlement and legitimate worker early-exit coverage before acceptance. |
| R5 pressure and rotation | `test_orchestration_context.py`: checkpoint CAS, identity, task partition; T4 actual CLI generation/session rotation | T4 review requires finish invalidation after settlement failure and recovery of real worker identity; debate pressure remains T5/T6. |
| R6 three proposals, peer debate, ruling | Planned `test_recovery_council.py` | T5 pending. No council fixture is claimed complete. |
| R7 durable bounded recovery | Planned `test_recovery_integration.py` | T6 pending; legacy retry counters can reset, so recovery budgets must be independently durable. |
| R8 preserved scheduling and permissions | M1 regression, T3 controlled supervisor/relay/package fixtures | T4 review identified native worker hook auto commit/push; fix before accepting M2. M3 controls and default activation pending. |
| R9 whole-flow audit | M1 independent spec/standards reviews; T3 final bounded standards review; planned `test_fresh_orchestration_e2e.py` | T7/T8 pending; full final regression and release limits required. |

Provider capability evidence is separate from acceptance: Claude inventory smoke supports
the initial boundary; constrained Luna reasoning remains ineligible until effective-request
proof. Codex worker routing is separate. No live terminal transition or installation has
been performed by this continuation.
