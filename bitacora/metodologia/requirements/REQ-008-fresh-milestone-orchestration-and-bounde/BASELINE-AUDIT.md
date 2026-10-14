# REQ-008 — Verified baseline and acceptance evidence gaps

## Review scope
Read-only inspection of current entry, run/session prompt, provider driver and relay paths. Two independent locator audits and a fresh spec review supplement direct code inspection. No runtime implementation or tests have been executed for REQ-008. PLAN remains review; product clarification answers are recorded separately from plan approval.

## Concrete baseline
| Requirement | Existing seam | Missing proof/behavior |
|---|---|---|
| R1 | bt_continuation resolves a project and recovers live pointers | Required entry revalidation gate with drift handling; unchanged approval must survive |
| R2 | relay_run.run preserves the foreground terminal for quota successors | Approved planning-to-execution transition and milestone supervisor handoff; no wrong-process signalling |
| R3 | bt_runprompt._bundle limits graph nodes and recent log count | Aggregate context cap, all-notes growth control and mandatory-context overflow behavior |
| R4 | bt_runprompt._duties assigns docs and verification | Bounded orchestrator delegation as enforced behavior, ownership receipts and durable closing documentation |
| R5 | bt_runsession.run_session polls timeouts/verdicts/stop | Live context pressure observation, checkpoint handshake and rotation without duplicate effects |
| R6 | bt_delegate plus bt_agents routing | Three proposals, peer critiques, orchestrator decision and persisted state machine |
| R7 | bt_runsettle retries/escalates and records blocked tasks | Council budgets, interruption recovery, missing-member handling and nonrecursive recovery |
| R8 | Existing dependency/audit/lock/worktree/approval controls | Regression evidence proving these survive the orchestration transition |
| R9 | Current policy/reference files and planned audit passes | Reconciled policies, independent implementation audits and requirement-to-test evidence |

## Context telemetry limitation
bt_runprompt.agent_argv currently invokes Codex exec in text mode, without a structured streaming switch. CodexDriver._usage extracts the closing `tokens used` total. ClaudeDriver._usage reads terminal-event usage. bt_runsession.run_session currently writes output to a file and polls timeout, task verdict and stop; it does not enforce live context pressure.

Consequently, closing totals are insufficient evidence for a preventive in-session token threshold. Implementation must demonstrate live observable bounded behavior. If token context telemetry cannot be established, SPEC R5 requires an explicitly labelled conservative observable budget; reported usage totals must never be called current context occupancy.

## Additional acceptance scenarios
- Distinguish child prompts from actual provider session identity; tests must reject accidental `resume`/conversation reuse.
- A fake child must share the terminal identity, not merely inherit stdout in a non-TTY test.
- At rotation, reap or reconcile owned delegates before the successor can write; verify no completed external effect is replayed.
- Fail visibly if mandatory constraints cannot fit; do not silently truncate approval/security/acceptance text.
- Three completed proposal roles are required before a normal ruling; quota/missing proposals cannot be filled with invented answers.
- Safe blocked states are valid for unavailable capacity or absent authorization, not proof of successful recovery.

## Current status
Planning evidence only. No passing check is claimed. Live installation, provider validation and implementation remain pending under the concrete plan approval gate.
