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

_Last updated: 2026-10-15_

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

## Permission model v2 (REQ-005 / T14)
_Documents the state after M1–M4. The 24 permission codes and their stored rows are unchanged. One API shape change is **not** additive: `GET /permissions` `permissions` is now a metadata array instead of a code array (see the contract table). The MCP `list_permissions` keeps the string array._

**Source of truth.** `src/common/auth/permissions.ts` still defines which codes exist. `permission-catalog.ts` describes each code as a total record: `label`, plain `description`, `risk` (`low|medium|high`), `group` and `implies`. `implies` is the transitive closure (e.g. `leads:delete` → `leads:write`, `leads:read`), so a client can auto-select without recursing. Adding a code without metadata is a compile error.

**Templates.** `role-templates.ts` holds Viewer, Sales, Finance, Project manager and Admin. Each template is closed under implication (spec-checked). A template is a starting point copied into a new role; later template edits never change roles already created from it.

**Guard rails (shared by HTTP and MCP).**
- Saving a role adds implied permissions automatically and reports what was added (`added`).
- A change that leaves no active internal user with `users:write` is refused with 409 `last_admin`. The count covers internal users only (external users cannot use guarded routes).
- Editing a system role in a forbidden way is refused with 409 `system_role_protected`.
- Unknown codes stored in `role_permissions` are ignored and never shown as granted.
- A duplicate of a system role is never a system role.
- Bulk role changes skip the acting user (`self_modification`) and deactivated users, reporting each skip with a reason.

**Effective access.** Each permission in `GET /users/:id/access` carries `granted` and `via` (`role` | `none`) plus a reason, so "why can't X see Finance" is answered from the server, not from the UI.

**Audit.** Role create/update/delete/duplicate/bulk write to `role_audit_events` (best-effort, D-001). `GET /roles/audit` reads them. The SQL is written under `db/add-role-audit-events.sql` and is **not applied** (P-010). Atomicity is open (P-011).

**Access requests.** Users without a permission file a request with a reason; users with `users:write` are notified and can approve or deny. Approving a request grants nothing by itself. The table SQL is `db/add-access-requests.sql`, **not applied** (P-012). The backend refuses a second pending request for the same user and permission (409), but the check is check-then-insert with no unique index in the SQL, so two concurrent requests can both pass (P-014).

### API contract v2
Additive except `GET /permissions` (breaking, see its row); the frontend and the MCP are coded against this contract, not against each other.

| Method & path | Purpose | Response / errors |
|---|---|---|
| `GET /permissions` | Catalog with metadata, groups and templates | `{permissions:[{code,group,label,description,risk,implies}], groups:[{key,label,description,permissions}], templates:[{key,label,description,permissions}]}`. **Breaking:** `permissions` was `string[]` of codes and is now the metadata array above; any consumer reading codes from it must switch to `permissions[].code`. |
| `GET /roles` | Roles | existing fields + `userCount`, `updatedAt` |
| `POST /roles` | Create | `added` (implied permissions); 422 `UNKNOWN_PERMISSION`; 409 `ROLE_NAME_CONFLICT` |
| `PATCH /roles/:id` | Update | `added`; 422 `UNKNOWN_PERMISSION`; 409 `last_admin` / `system_role_protected` / `ROLE_NAME_CONFLICT` |
| `DELETE /roles/:id` | Delete | 204; 422 `ROLE_IN_USE` (user count); 409 `system_role_protected` |
| `POST /roles/:id/duplicate` `{name}` | Copy a role | role (never system) |
| `POST /roles/impact` `{roleId?, permissions[]}` | Preview a save, nothing written | `{usersAffected, gained[], lost[], sampleUsers[≤20 {id,name,email}], added[], warnings[]}`; `gained`/`lost` = difference between the current effective permissions and the result after implication (permissions the role already has are not listed as gained); without `roleId`, `gained` is the whole expanded set and `usersAffected` is 0; 422 `UNKNOWN_PERMISSION` for unknown codes |
| `GET /roles/audit?roleId&limit` | Role audit trail | `[{id, roleId, action, actor, at, diff}]` |
| `GET /users/:id/access` | Effective access | `{userId, roleName, permissions:[{code,label,granted,via,reason}], sections:[{key,label,accessible}], leadTypeScope}` |
| `POST /users/bulk-role` `{userIds[], roleId}` | Bulk role change | `{updated, skipped:[{id, reason}]}`; skip reasons: `self_modification`, `deactivated`, `not_found`, `already_has_role`, `external_role_not_allowed`, `changed_during_batch`. 409 `last_admin` refuses the whole batch and changes nothing. |
| `POST /access-requests` `{permission?, section?, reason}` | File a request | 201; 400 when neither permission nor section; 422 `UNKNOWN_PERMISSION`; 409 `ACCESS_REQUEST_ALREADY_PENDING` |
| `GET /access-requests?status` | List requests (`users:write`) | list |
| `PATCH /access-requests/:id` `{status: approved\|denied, note?}` | Resolve (`users:write`) | updated request; 409 `ACCESS_REQUEST_ALREADY_RESOLVED`; 422 `OWN_ACCESS_REQUEST` (nobody resolves their own request); does not change roles |

Controllers: roles and users in `src/modules/users/user-management/users.controller.ts`; bulk role and effective access in `user-access.controller.ts`; `access-requests.controller.ts` in the same folder.

### MCP tool list (admin surface)
Every write accepts `dry_run: boolean` (see "MCP write policy" above). Writes run as `mcp-agent@maros.invalid` and are audited as `mcp_write`.

- **Roles and permissions:** `list_roles`, `create_role`, `update_role`, `delete_role`, `list_permissions`, `duplicate_role`, `role_impact`, `list_role_templates`, `apply_role_template`, `list_role_audit`.
- **Users:** `list_users`, `get_user`, `update_user`, `invite_user`, `resend_invitation`, `revoke_invitation`, `list_user_directory`, `check_user_access`, `get_user_access`, `bulk_assign_role`.
- **Access requests:** `list_access_requests`, `resolve_access_request`.
- **Coverage:** `mcp_capability_report` lists every API route with its tools or its justified exclusion (the offline `capabilities.spec.ts` gate fails on any unclassified route).
- Remaining CRM, catalogs, projects, notes, tasks, QBO and notifications tools are listed in `capability-map.ts` and the `mcp_capability_report` output; they are not repeated here.

### Known gaps (open in PENDING.md)
- P-010 / P-012: apply the two SQL files to Supabase by hand before deploying REQ-005 (agents never touch the shared DB).
- P-011: role write and audit insert are not atomic; a failed audit insert leaves only a log line.
- P-013: other guarded pages still redirect to /dashboard instead of showing `NoAccessState`.
- P-014 / P-015: concurrent duplicate pending requests can slip past the check (no unique index); the gating test for settings/users and settings/roles is missing.
- `GET /permissions` shape change (above): the frontend on `wt/REQ-005-integration-86795b50` reads the metadata array; any other consumer of the old string array breaks.
