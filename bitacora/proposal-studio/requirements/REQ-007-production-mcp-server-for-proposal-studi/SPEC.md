---
id: REQ-007
status: done
created: 2026-10-11
track: deep
---
# REQ-007 — Production MCP server for Proposal Studio

## Problem & goal
David currently needs to operate Proposal Studio through its web UI or direct scripts. He wants both Claude Code and Codex on this machine to use the same supported interface to manage proposals in the production application.

**Success looks like:** a secured MCP endpoint on the production deployment is reachable from both local clients; it exposes the application's complete proposal workflow; and Claude/Codex can create and inspect the first Oraldenti draft with its three prepared captures.

## Users / actors / stakeholders
- David is the sole administrator and owner of the local MCP clients.
- Prospects are affected only after David publishes a revision and creates a share link.

## Scope (in)
### US-1 (P1, Must) — Operate proposal lifecycle over MCP
As David, I want both supported AI clients to list, inspect, create, update and archive proposals, upload current-site captures, publish revisions, and create/list/revoke temporary share links.
**Acceptance:** each operation uses the application's existing proposal/sharing services, returns a stable result, and writes existing audit events for mutations.

### US-2 (P1, Must) — Use the connected GitHub prototype workflow
As David, I want MCP tools to inspect installed repositories and trees and import a pinned static prototype revision into its proposal.
**Acceptance:** only repositories from the already installed read-only GitHub App are visible/importable; a commit SHA and safe built directory are required; no repository contents are modified.

### US-3 (P1, Must) — Connect production securely to both local clients
As David, I want Claude Code and Codex on this machine to connect to the same production MCP endpoint using a dedicated, rotatable credential.
**Acceptance:** invalid/missing credentials are rejected before tool dispatch; credentials are not committed or printed; both clients list and successfully invoke read-only tools.

### US-4 (P1, Must) — Create the first Oraldenti draft using MCP
As David, I want the first proposal draft to contain Inicio, Servicios and Contacto with their prepared source URLs and PNG captures.
**Acceptance:** all three captures are private, Servicios and Contacto are mapped to their matching prototype paths, and the record remains a draft until an Oraldenti prototype is imported and publication is explicitly requested.

## Out of scope
- Email, notification settings and email delivery tools; David explicitly removed these from the product workflow.
- Taking screenshots or crawling remote source websites inside the deployed application; captures are supplied by the user as PNGs.
- GitHub repository writes, builds, or deployment actions.
- Public proposal publication or link creation as part of the first-draft setup unless separately requested.
- Replacing Google OAuth for the app's browser administration.

## Requirements
- R1. The production app shall serve MCP using Streamable HTTP at a stable HTTPS URL supported by Claude Code and Codex.
- R2. Before executing any MCP request, the server shall validate a dedicated bearer credential using a constant-time comparison and fail closed if its secret is absent or invalid.
- R3. The server shall resolve the configured, verified `ADMIN_EMAIL` to its existing administrator record and use that user ID for all audited mutations.
- R4. The server shall expose tools for listing/reading/duplicating proposals; creating/updating/archiving drafts; uploading/reading validated PNG homepage/page captures; inspecting and disconnecting the installed GitHub App, listing allowed repositories/trees, importing a pinned prototype; publishing; and issuing/listing/revoking expiring share links. GitHub OAuth installation remains in the existing browser flow because it requires a callback cookie.
- R5. The server shall not expose email, settings, raw database, arbitrary SQL, filesystem, or Git write tools.
- R6. The server shall validate all tool inputs, cap uploaded image bytes to fit the production request limit, preserve private asset authorization, and map failures to deliberate MCP tool errors without secrets or stack traces.
- R7. The server shall rate-limit authenticated MCP operations using the existing `admin_rate_limit_bucket` Postgres table and rely on existing service audit events for mutations; no migration is required.
- R8. The local Claude Code and Codex configurations shall point to the production endpoint and obtain the bearer token through a local helper reading a user-only secret file, not from committed files or literal client config values.
- R9. When invoked through MCP, the Oraldenti creation workflow shall store the supplied home/services/contact captures and route pairs in an unpublished draft; it shall not publish or create a public link.
- R10. The endpoint shall be stateless and safe to run on Vercel across independent function instances; rate limiting reuses the existing `admin_rate_limit_bucket` table and no database migration is required.
- R11. Archive, publish, share-link creation/revocation and GitHub disconnection tools shall require `confirm: true` in their validated input in addition to client-side write approval. Read-only tools are annotated read-only; write tools are marked as mutating. The credential shall be rotated if exposure is suspected.
- R12. MCP requests shall not automatically retry mutations. Create uses a unique slug; repeated capture uploads and prototype imports reconcile against current content/revision; publish checks the current published revision before creating another. If share-link creation times out after the server may have completed it, list links and revoke any orphan before creating a replacement because the secret is returned only once.

## Edge cases & errors
- Reject missing/malformed/oversized bearer credentials without revealing whether a token prefix is valid; compare fixed-length digests in constant time.
- Missing production MCP secret or admin account must fail closed.
- Oversized, malformed, or invalid PNG input must be rejected before storage; partial capture failure must report the proposal ID and failing capture so the draft can be resumed.
- Invalid repository/ref/SHA/directory or unavailable GitHub installation must return a bounded, actionable error.
- Publishing incomplete pages must use existing publish validation; no public link is returned before successful publication.
- Duplicate MCP initialization, read calls and tool discovery must not write records or audit events.
- A repeated create with an existing slug must return a conflict and an instruction to inspect that proposal rather than silently creating another record.
- A repeated upload/import/publish must not create duplicate state; ambiguous share-link creation is reconciled by listing and revoking the orphan before a replacement is created.

## Constraints
Use Astro/Vercel, current Postgres and private Blob services, current proposal/GitHub/sharing feature services, existing admin allowlist, and MCP TypeScript SDK. Production has no schema changes. Keep email absent. Only configure Claude/Codex on this Linux machine. Use a dedicated high-entropy secret delivered to Vercel Production and stored in a mode-600 file under `~/.config/proposal-studio/`; a local helper returns request headers to each client. The MCP endpoint is internet-reachable and can mutate production proposal data, so authenticate before parsing/dispatch, rate-limit, audit, and require `confirm: true` plus client-side approval for publishing, archiving, revocation, link creation and GitHub disconnection. Reuse the already-migrated `admin_rate_limit_bucket` table.

## Priorities & phases
MVP: protected production endpoint, full proposal/GitHub/share workflow, both local clients connected, and Oraldenti saved as a draft. OAuth authorization-server registration, email, bulk operations and autonomous scraping are out of scope.

## Timeline & dependencies
Depends on REQ-006's multi-page comparison behavior and prepared Oraldenti PNGs. First-draft setup is expected to complete in this task; publish/share waits for an Oraldenti prototype.

## Assumptions
The remote token is a single admin credential managed in Vercel and this machine, with rotation documented; implementing OAuth 2.1 now would add a separate identity-provider and client-registration system not otherwise needed for one owner. “Everything” means all proposal lifecycle, capture, GitHub prototype import, and share-link capabilities. App authentication/email configuration and email sending remain outside MCP because previous scope explicitly removed them. The first Oraldenti record is a draft because no matching prototype repository was supplied in this thread.

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
| Priorities | Clear |
| Timeline | Clear |

## Clarifications
### Round 1 — 2026-10-11
- Q: ¿Dónde debe ejecutarse el MCP? → A: En producción; conectarlo a Claude y Codex de esta máquina.
- Q: ¿Qué amplitud debe tener? → A: “Básicamente todo”. Se interpreta como flujo de propuestas, capturas, GitHub/prototipos y enlaces; se conserva fuera el correo conforme al alcance anterior.
- Q: ¿Se puede iniciar con el borrador de Oraldenti usando las tres capturas? → A: Aprobado junto con el plan; se deja sin publicar.
