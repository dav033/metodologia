# maros — Architecture

_Living document: how the thing is built (or, for business projects, how the process/organization works).
Edit in place; record the *why* of changes in DECISIONS.md._

## Overview
_One paragraph + optional diagram (mermaid)._

## Components / actors
| Name | Responsibility | Where (path / owner) |
|---|---|---|

## Data & integrations
-

## Key flows
-

## Conventions & constraints
-

_Last updated: 2026-10-08_

## MCP administrative surface (REQ-005 / T7)
- MCP remains an administrator-level shared-token integration, with no employee impersonation for user/role writes. The system identity is `mcp-agent@maros.invalid`; its SQL is never applied by tests.
- `src/modules/mcp/tools/capability-map.ts` maps every reviewed controller handler to its MCP tool(s), or a justified exclusion. `mcp_capability_report` version 1 returns live `method`, `path`, `controller`, `handler`, `tools`, coverage status, missing tools and exclusion reason. Totals include covered and excluded separately.
- `capabilities.spec.ts` scans actual controller declarations, creates the real McpService tool registrations offline, and checks no unclassified route, missing tool or stale map entry. Tests never bootstrap Nest or connect a database.
- Missing CRM tools live in `crm-admin-{leads,catalogs,projects,analytics}.ts`; preferences in `users-preferences.ts`; invoice counterparties/scans, QBO connection health and comment edits/deletes in `platform-admin.ts`; note access/grants/public links in `note-sharing.ts`. The explicit inventory is the tool list; T14 will consolidate the complete model documentation.
- `update_user.scopedLeadTypes` accepts a nonempty unique array of CONSTRUCTION/PLUMBING/ROOFING, or null to clear the scope. `list_roles` includes userCount. `list_permissions` preserves the old permissions array and adds permissionMetadata plus templates.
- Preferences take explicit userId. Note sharing writes use the system user and the existing service's owner/editor checks; being the MCP does not impersonate a note owner. Global emergency link revocation uses the administrative service operation.
- OAuth redirects/callbacks, public share/intake token routes, the HTML/multipart upload transport, personal favorites/saved views/access requests and /users/me are excluded with reasons. Personal task filtering is available through search_tasks with assigneeUserId.

## MCP write policy (REQ-005 / T8)
- The existing registerMcpTool boundary adds optional `dry_run: boolean` to writes, validates inputs with their declared Zod schema, and returns previews before any write handler. Omitted/false executes normally; existing confirm fields still apply. Read classification is explicit in mcp-write-policy.ts, and unclassified tools default to write.
- `update_user`, `update_role`, `delete_role`, `revoke_invitation`, `bulk_assign_role` and `apply_role_template` have domain previews using the same users/roles/bulk/invitation services as HTTP. Bulk user IDs are limited to 200. Refusals preserve stable API codes such as last_admin and system_role_protected. Generic previews are marked schema_only and never claim resource eligibility.
- `get_task_workspace_options` is deliberately a write: its service may provision the General workspace. Simulation never calls that service; execution passes the MCP actor ID into optional listOptions(actorId) so provisioning records createdById as well as the generic MCP audit. Existing HTTP calls without the actor argument remain compatible. New template-role previews reuse RolesService.previewCreate so occupied names are refused before mutation.
- McpService configures the system actor and audit context before registrations. Executions append action mcp_write with roleId=null, actor email and diff `{tool,target,outcome}`; target contains only bounded identifiers. Failed/refused executions and provider isError envelopes record failed. Dry runs do not audit a write. Role create/update/delete/duplicate/bulk events also carry the system actor instead of generic system attribution.
- Audit inserts preserve D-001: if storage fails after an effect, the bounded event is logged for backfill rather than returning a fabricated failure for a completed write. Durable delivery and concurrent R4 atomicity remain P-011; role_audit_events SQL must be applied manually (P-010). No DB is used in these tests.
- Offline regression tests in write-policy.spec.ts cover wrapper behavior; mcp-preview.spec.ts exercises registered MCP tools with real services and repository stand-ins. The parity gate checks dry_run on actual McpService write registrations. Contract consumers are McpServer clients and the future roles/audit UI; event action mcp_write and nullable roleId are additive.
