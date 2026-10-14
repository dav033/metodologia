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
