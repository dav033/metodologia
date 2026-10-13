---
id: REQ-001
status: in-progress
created: 2026-10-10
track: deep
---
# REQ-001 — Deep workspace onboarding and architecture assessment

## Problem & goal
The skill's `bitacora.py init` prepares files but does not interview the owner or examine the workspace before architecture is written. The user wants project onboarding to learn what the application is for, scan the whole product workspace, map its architecture, and identify architectural failures and improvements.

**Success looks like:** Every owner-confirmed, accessible repository is analyzed and represented in one product-level architecture; each finding is classified and has traceable evidence, impact, confidence and a recommendation; skipped areas and checks are visible; the audit never claims full coverage when a repository is missing or inaccessible.

## Users / actors / stakeholders
- David, the solo developer and product owner, works across all repositories that make up one product workspace (for example, frontend and backend).
- The AI agent conducts discovery and prepares the bitácora; an independent reviewer checks the synthesized architecture.

## Scope (in)
### US-1 (P1, Must) — Initialize a project architecture baseline
As a project owner, I want the bitácora setup to interview me and analyze the whole product workspace so that its architecture reflects both business intent and implementation.
**Acceptance:**
- Given a new project bitácora, when onboarding starts, then the agent asks about purpose, users, workflows, constraints and success before scanning.
- After inspecting the workspace, the agent asks follow-up questions when evidence exposes gaps or contradictions; initial product-purpose answers are persisted in `SUMMARY.md` with a last-confirmed date, reused on re-audit, and the owner is asked what changed.
- Given an owner-confirmed workspace with multiple repositories, when the scan completes, then `ARCHITECTURE.md` describes one product, including cross-repository contracts and end-to-end flows.
- If the owner confirms that no implementation repositories exist yet, then the agent records the purpose and intended architecture from the interview, labels code analysis as not started and the audit as partial.
### US-2 (P1, Must) — Re-run the architecture audit
As a project owner, I want an explicit way to rerun the same audit for an existing project so that the architecture stays useful as the product changes.
**Acceptance:**
- Given an existing project, when the owner explicitly invokes `bitacora.py audit`, then the CLI prepares deterministic workspace inventory/context and the AI agent runs the same interview, analysis, independent review and documentation flow.
- The inventory begins with the workspace registry and configured root. The agent verifies registered paths and checks for likely unregistered repositories only within that configured root; it asks the owner to confirm candidates before including them. It never scans arbitrary sibling folders or the home directory.
### US-3 (P1, Must) — Produce traceable findings and coverage
As a project owner, I want failures, risks and improvement opportunities separated and prioritized so that I can decide what to address.
**Acceptance:**
- Every finding identifies its class, priority, impact, confidence, evidence (repository and path/line or check output) and suggested remediation.
- A finding is called a confirmed failure only when evidence supports that conclusion; uncertainty is labeled as a risk or hypothesis.
- A coverage matrix records each confirmed repository and shared workspace document as present/accessed/analyzed/reviewed or the reason a stage could not complete, and each relevant check as passed/failed/skipped/not-applicable with a reason.
- The audit is complete only when every owner-confirmed repository is accessible, analyzed and independently reviewed. Missing or inaccessible repositories make it partial. Checks that are not applicable or unsafe may be skipped with a reason and do not by themselves invalidate repository coverage.
- A separate reviewer agent invocation, in an independent context and read-only, checks the cross-repository synthesis once against the evidence and a checklist (contracts, ownership, dependencies, flows, security/configuration and deployment). If reviewer and author disagree, the final record labels the disputed conclusion uncertain and includes both evidence-based views; the process does not loop indefinitely. If a separate reviewer is unavailable, the audit is marked partial.
- On completion, the agent updates project-level `ARCHITECTURE.md`, records actionable findings in `PENDING.md` (unique existing P IDs are updated instead of duplicated), and puts the run's coverage matrix and check results in the current session's day log.

## Out of scope
- Automatically run a deep audit at the start of every session.
- Modify product source code, deploy, commit or push as part of the audit.
- Scan repositories outside the configured project workspace or read secret values.
- Run networked or state-changing checks by default.

## Requirements
- R1. When a new project bitácora is initialized, the agent shall interview the owner about purpose, users, workflows, constraints and success before inspecting implementation.
- R2. After the initial scan, the agent shall ask follow-ups only for material gaps or contradictions. It shall persist owner-confirmed purpose/workflow/constraint facts in `SUMMARY.md` with a last-confirmed date, reuse them during re-audits, and ask what changed.
- R3. The CLI shall expose `bitacora.py audit` to prepare deterministic inventory/context for an existing project; the AI agent shall perform the same interview, analysis, independent review and documentation workflow.
- R4. The agent shall resolve the workspace from the project registry and configured root, verify registered paths, and ask the owner to confirm likely unregistered repositories found within that root.
- R5. The agent shall analyze all owner-confirmed repositories and shared workspace documents as one product, including API/DTO contracts, authentication, data ownership, configuration, deployment and end-to-end user flows.
- R6. The agent shall inspect documentation, source, manifests, schemas/migrations, tests, integrations, infrastructure and deployment configuration, and may run safe local lint/type/test/build checks.
- R7. Before running a check, the agent shall inspect the relevant command definition sufficiently to rule out network access, credentials, persistent-data writes and environment changes. If behavior remains unclear or unsafe, it shall skip the check and record why rather than ask for blanket permission.
- R8. The agent shall exclude secret files and values, generated/vendor/dependency files and binaries from source analysis; it may inspect configuration schemas or example files without exposing secret values.
- R9. The agent shall perform inventory, per-repository analysis, cross-repository synthesis and one review by a separate read-only reviewer agent invocation using an architecture checklist. Unresolved disagreement is recorded as uncertainty rather than retried indefinitely. If no independent reviewer is available, mark the audit partial.
- R10. The agent shall separate confirmed failures, risks and improvement opportunities and provide priority, impact, confidence, evidence and remediation for each finding.
- R11. The agent shall update project-level `ARCHITECTURE.md`, record/update findings in `PENDING.md` without duplicates, and record repository, shared-document and check coverage/results in the current day log.
- R12. If an owner-confirmed repository is missing or inaccessible, or no independent reviewer is available, the agent shall continue where possible, mark coverage partial and shall not claim a complete audit. If the owner confirms there is no implementation repository yet, record interview-based intent only and mark implementation analysis not started.
- R13. The default audit shall not modify product code, use networked checks, change environment state, commit or push.

## Edge cases & errors
- Stale or absent workspace registration: present the configured root and candidate repositories to the owner and ask for confirmation/registration; do not infer complete scope.
- Multiple repositories with overlapping or mismatched contracts: analyze and cite the cross-repository boundary.
- Existing architecture docs conflict with source or tests: preserve the discrepancy and evidence instead of silently choosing one.
- A lint/test/build command needs credentials, network, a live service or persistent database writes: mark it skipped and why.
- Generated, vendored, dependency, binary and secret files: exclude from source analysis; never read secret values.
- A reviewer disagrees with the analysis: record both evidence-backed views and reduce confidence; do not loop.

## Constraints
- Safe local lint, type, test and build checks are preferred only after their scripts are inspected for network and state changes.
- Product repositories are read-only during the audit; only bitácora documentation is updated.
- Preserve unrelated local modifications. Do not commit or push.
- The project can contain multiple repositories under one product/workspace identity.

## Priorities & phases
- Must: owner interview, workspace inventory/confirmation, per-repository analysis, product-level synthesis, independent review, coverage matrix, persistent architecture and findings.
- Should: safe local lint/type/test/build evidence where available.
- Out of default scope: product-code remediation, network checks and environment-changing commands.

## Timeline & dependencies
- No deadline supplied.
- Requires registered workspace metadata or owner confirmation of candidate repositories and AI-agent access to accessible repos. Missing paths are reported, not silently skipped.

## Assumptions
- The project workspace registry and configured root are the source of scan boundaries; likely additional repositories under that root are candidates, not automatically included. A dedicated `bitacora.py audit` command prepares deterministic workspace context while the AI handles architectural judgment. Initial purpose, users, flows and constraints are persisted in `SUMMARY.md` with a confirmation date.
- The owner wants the scan to proceed partially when a repo is unavailable, with explicit coverage limits.
- Safe-check review means inspecting command scripts and direct local effects before execution; unclear commands are skipped.
- Findings use existing PENDING IDs/priority conventions; supporting evidence is an indented detail under each item.
- This requirement covers architecture onboarding only. Proactive explanations and self-improvement of the skill are tracked separately in REQ-002.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
### Round 1 — 2026-10-10
- Q: When does the audit run? → A: During initial setup of a new project bitácora and by explicit request for an existing project.
- Q: What is a project/workspace? → A: One product may span multiple repositories (e.g. frontend and backend) that David works on together; analyze it as one product workspace.
- Q: Interview and scan sequence? → A: Ask purpose, users, workflows, constraints and success first; inspect code afterward and follow up on gaps or contradictions. Persist confirmed facts with a date for later audits.
- Q: Analysis depth? → A: Deep review of docs, source, manifests, data/migrations, integrations, infrastructure and deployment; map modules/dependencies/data/flows; run safe local lint/type/test/build checks when available.
- Q: Output and code changes? → A: Update architecture and record prioritized findings with evidence, impact, confidence and remediation; do not change product code.
### Round 2 — 2026-10-10
- Q: Analyze frontend and backend as one product? → A: Yes; synthesize cross-repository contracts and flows.
- Q: Distinguish failure from improvement? → A: Yes; separate confirmed issues, risks and opportunities with evidence, impact, confidence and recommendation.
- Q: Review process? → A: Inventory, analyze each repo, synthesize the product and run one independent, read-only reviewer-agent invocation; unresolved disagreement is marked as uncertainty.
- Q: Missing repositories/checks? → A: Continue with a coverage matrix and limitations; never claim full completion.
- Q: Invocation? → A: Start the workflow during new bitácora setup and provide a dedicated `bitacora.py audit` entrypoint for reruns; the CLI orchestrates deterministic workspace context while the AI performs architectural judgment.

## Implementation status
The approved plan is implemented and verified in the methodology working tree. The changes remain uncommitted for owner review; no merge or publication has occurred.
