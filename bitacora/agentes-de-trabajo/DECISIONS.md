# agentes-de-trabajo — Decisions

## D-001 — One repository and bounded automatic improvement
- Date: 2026-10-12. Status: Accepted.
- Context: Nontechnical owners need a primary way to create and maintain useful agents without losing decisions between sessions.
- Decision: Target ChatGPT Work; keep skill, agents and scoped memory in one owner/team repository. Automatically preserve confirmed learning; require approval for process, permission and external-effect changes.
- Alternatives: Separate skill/memory repos were proposed; owner selected one repo. Fully automatic process changes were rejected in favor of bounded learning.
- Consequences: Simple ownership and traceability; every repository reader can access its tracked memory. Runtime capabilities and actual GitHub saves must be verified.
- Rollback: Introduce a superseding decision; export agent records to a new agreed layout while retaining history. Do not delete or publish records automatically.
- Source: REQ-001 and owner answers on 2026-10-12.

## D-002 — Proactive remembered connection setup
- Date: 2026-10-12. Status: Accepted.
- Context: The owner explicitly added remembering and proactively configuring MCP/connections to the approved plan.
- Decision: Check needed versus available capabilities at creation/resume/failure, prefer existing tools, discover relevant plugins/MCP when a concrete gap exists, prepare scoped setup, apply within existing explicit grants and verify actual environment/account/capability state. Store safe connection records in the same repo.
- Alternatives: Wait for the nontechnical owner to name integrations; rejected because they may not know the missing capability. Unbounded installation/permission changes are excluded by the approved autonomy boundary.
- Consequences: Fewer repeated setup questions; hosted Work and local MCP configs must remain distinct. Live setup is not part of authoring this package.
- Rollback: Supersede this policy, preserve records/history, and disable only specifically authorized integrations if requested.
- Source: Owner approval and extension, 2026-10-12; R10.

## D-003 — Public initial distribution
- Date: 2026-10-12. Status: Accepted.
- Context: After reviewing the local package, the owner explicitly requested public visibility for now and upload to their GitHub account.
- Decision: Create dav033/agentes-de-trabajo as a public repository and publish the prepared initial package. This supersedes the proposed private visibility for this distribution artifact only, not the recommendation for private deployments carrying real business memory.
- Alternatives: Private distribution was proposed; owner selected public for now.
- Consequences: Only reusable instructions and synthetic data are included. The one-time commit/publication grant is not a standing remote-memory-write grant.
- Rollback: Owner can authorize a later visibility change. Public clones may remain outside the owner's control; do not publish real business data or credentials.
- Source: Owner message: 'hazlo publico por el momento y subilo a mi repositorio'.
