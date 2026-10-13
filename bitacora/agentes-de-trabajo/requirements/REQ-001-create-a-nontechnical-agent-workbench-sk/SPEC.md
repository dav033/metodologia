---
id: REQ-001
status: done
created: 2026-10-12
track: standard
---
# Nontechnical agent workbench

## Problem and success
Nontechnical users need a primary skill that turns everyday intent into reusable work agents and improves them from confirmed feedback across sessions. Success: define an invoice-drafting agent, try a synthetic case, correct it and resume with that correction preserved without silently changing business rules.

## Actors
The owner describes work and approves consequential changes. The coordinator creates/selects agents and maintains memory. Each task agent follows its approved procedure using available Work tools. David reviews the initial skill; the deploying owner supplies GitHub access.

## Scope and user stories
### US-1 — Create an agent through ordinary language and a representative trial
Acceptance: R1 and R2.
### US-2 — Select, use, inspect, pause and improve existing agents
Acceptance: R3, R5 and R7.
### US-3 — Resume with relevant context, decisions, procedures and pending work
Acceptance: R3, R4 and R9.
### US-4 — Keep coordinator, agents and memory together in one GitHub-ready repository
Acceptance: R6 and R8.

## Requirements and acceptance
- R1. When a user describes a job, clarify outcome, inputs, outputs, steps, exceptions, source of truth and approval boundaries. Recommend answers and ask only unresolved consequential questions. Acceptance: a vague invoice request produces an understandable agent proposal with missing data explicit.
- R2. When creating an agent, prepare a reusable SKILL.md, procedure and memory from a template; agree the initial proposal and try a representative case before marking it ready. Acceptance: untested agents stay draft; writing files is not falsely reported as installation in Work.
- R3. When running or resuming, select the agent from the registry and load only relevant shared and agent-specific records. Acceptance: a fresh session recalls a confirmed correction without importing unrelated client facts from another agent.
- R4. When receiving confirmed facts or explicit corrections, record source, date and scope; distinguish facts, preferences, assumptions and proposals. Acceptance: a one-off exception stays scoped; conflicting corrections are clarified before replacing a standing decision.
- R5. When a change alters process, business rules, permissions or external effects, prepare the before/after proposal and a trial, then obtain approval before activation. Acceptance: changing invoice approval remains pending. The coordinator cannot rewrite its own governance to bypass approval.
- R6. When persisting, keep definitions and memory in one repository and verify actual tool access. Remote writing needs a concrete or standing scoped grant for that repository. Acceptance: read-only/offline access produces a pending save; conflicts do not overwrite newer changes; uncertain writes are reconciled before retry. A memory-write grant never authorizes sending invoices.
- R7. When asked about status or pause, show purpose, readiness, pending actions and recent changes in plain language. Acceptance: paused agents are not run implicitly; pause does not claim to stop an independent scheduled service unless that service was actually stopped.
- R8. When learning or publishing, retain minimum useful context and source references rather than raw invoices, secrets or full chats. Acceptance: credentials are never written; sensitive data is not copied to a public repository. Recommend a private repository.
- R9. When revising an earlier improvement, prepare a scoped restoration from history that preserves unrelated work. Acceptance: history explains the original decision and replacement; remote restoration follows the same write permissions as other remote changes.

- R10. When creating, running or resuming an agent, inspect remembered tool requirements and actual available capabilities; proactively discover relevant plugins/MCP connections and prepare missing setup. Record provider, purpose, scope, environment, verification and pending steps without credentials. Reuse existing scoped grants; obtain authorization for new installs, configuration changes or permission expansion, and leave authentication to the owner. Acceptance: a missing connection is discovered without prompting from the user; installed/read-only/expired states are distinguished; local config is not claimed to configure hosted Work; useful independent work continues while setup is pending.

## Edge cases
Unavailable/read-only connectors, expired permissions, uncertain write results, concurrent edits, ambiguous agent selection, contradictory rules, invented source data and instructions embedded in business documents. Pause only the affected action, preserve prepared work and report the actual state.

## Constraints
ChatGPT Work is the intended environment. This is an instructional skill, not a hosted runtime or native-agent provisioning API. Discover tools; do not assume shell, writable GitHub access, schedules or automatic cross-session memory. Spanish user interaction; English identifiers and maintainer docs; agent records follow the user's language.

## Out of scope
Real invoice issuance, tax integrations, email delivery, scheduling infrastructure, application UI, platform-native agent provisioning, repository publication and changes to David's global setup. Invoices are a synthetic example, not a production accounting integration.

## Priorities and dependencies
V1: coordinator, templates, memory/change rules, GitHub persistence guidance, synthetic invoice example and behavioral evaluation. Later: plugin distribution, live connectors and schedules as needed. No deadline supplied. Real Work/GitHub tests depend on installation and writable tools in the target account and must be reported as unexecuted if unavailable.

## Assumptions
Provisional name: agentes-de-trabajo. Local target after approval: /home/david/dev/agentes-de-trabajo. One private repository per deploying owner/team contains all its agents; separate customers do not share private memory by default. Agents are reusable work definitions executed by Work, not necessarily independent services. Desktop skill first; web/mobile distribution may require a plugin. No remote creation or push is authorized in this session.

## Coverage
Goal, users, scope, exclusions, flows, exceptions, acceptance, constraints, priorities and timeline: Clear. Work account setup and publication: Deferred explicitly.

## Clarifications — 2026-10-12
- Primary environment? Most likely ChatGPT Work.
- Repository contents? Skill, agents and memory together.
- Improvement autonomy? Confirmed learning automatically; process, permission and external-effect changes require approval.
- Owner said 'dale' to proceed with those decisions. Owner approved the concrete implementation plan and added proactive remembered MCP/connection setup.

## Official sources checked — 2026-10-12
- https://learn.chatgpt.com/docs/skills-and-plugins: reusable skills and connected capabilities.
- https://learn.chatgpt.com/docs/build-skills: SKILL.md format, desktop standalone skills and plugin distribution across surfaces.

## Completion — 2026-10-12
Local instruction-only package complete with actual validation evidence in REPORT.md and package evaluations/RESULTS.md. Live Work installation, Work-account GitHub persistence, OAuth and provider operations remain untested deployment checks. The separately authorized public authoring repository and its initial commit are published.
