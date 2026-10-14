---
id: REQ-005
status: approved
created: 2026-10-14
track: standard
---
# REQ-005 — Friendlier roles and permissions (UX + functionality) and full-power admin MCP

## Problem & goal
Roles and permissions work but are hard to use. The catalog is 21 bare codes (`finance:read`...), the role editor is a
flat checkbox list per group, inviting a user shows no consequence of the chosen role, nobody can answer "why can't X
see Finance?", and an admin cannot compare, duplicate or safely change roles. The MCP exposes basic user/role tools but
the agent that will administer Maros through it ("Sami") needs the full set of powers, with guard rails.

**Success looks like:** an admin can create a role from a template, understand each permission in plain words, see who is
affected before saving, explain any user's effective access in one click, and do all of it (and every other
administrative action the API offers) through MCP tools; no change can lock everyone out of user administration.

## Users / actors / stakeholders
- Admin / office manager (roles and users), members (see friendly "no access" with a way to ask), the MCP agent "Sami"
  (acts through the system user `mcp-agent@maros.invalid`), David (owner).

## Scope (in) — cross-cutting: API, MCP and UI
### US-1 (P1) — Understand permissions
As an admin, I want each permission described in plain words with a risk level and what it implies, so that I grant the
right access without reading code.
### US-2 (P1) — Build roles quickly and safely
As an admin, I want templates, duplication, a diff before saving and an impact preview (who gains/loses what), so that
a role change is never a surprise.
### US-3 (P1) — Explain a user's access
As an admin, I want a per-user "effective access" view ("Finance: no, because role Member lacks finance:read") so that
support questions are answered in seconds.
### US-4 (P2) — Manage users in bulk
As an admin, I want to change the role of several users at once and see the role consequence in the invite dialog.
### US-5 (P2) — Ask for access instead of hitting a wall
As a member, I want a friendly "you don't have access" state with a "request access" action that notifies admins.
### US-6 (P1) — Full-power MCP
As the Sami agent, I want MCP tools for every administrative capability of the API (roles, permissions, templates,
impact, effective access, bulk role changes, access requests, audit trail, user lifecycle) with dry-run and guard rails.

## Out of scope
- Row-level scoping beyond the existing lead-type scope; new auth providers; external-user model changes; billing.
- Applying any SQL to the shared database (migrations are written as files only).

## Requirements
- R1. The permission catalog shall carry per permission: label, plain description, risk (`low|medium|high`) and `implies`
  (e.g. `leads:write` implies `leads:read`), and shall expose role templates (Viewer, Sales, Finance, Project manager,
  Admin). Existing permission codes and stored rows stay valid.
- R2. When a role is saved, the system shall add implied permissions automatically and report what it added.
- R3. The API shall offer: duplicate role; role impact preview (users affected, permissions gained/lost, sample users,
  warnings); per-user effective access with the reason per permission; bulk role assignment; role audit events.
- R4. If a change would leave no active user with `users:write`, or would edit a system role in a forbidden way, then the
  system shall refuse it with a clear 409/400 message and change nothing.
- R5. The role editor shall group permissions by area with descriptions, risk badges, search, template picker, implied
  auto-selection, a before/after diff and the impact preview before confirming.
- R6. The users page shall show role descriptions inline, support bulk role change, filters by role/status, and an
  "effective access" drawer per user.
- R7. When a signed-in user lacks a permission for a page or action, then the UI shall show an explanatory state with
  who can grant it and a "request access" action; navigation items they cannot use shall be hidden or explained.
- R8. The API shall store access requests and notify users with `users:write`; admins can list and resolve them.
- R9. The MCP shall expose a tool for each new API capability (R3, R8) plus tools for any existing administrative API
  route that has no MCP tool today, and a `mcp_capability_report` tool listing API routes versus tools.
- R10. Destructive or bulk MCP tools shall support `dry_run` and shall be refused by the same guard rails as the API
  (R4); every MCP write shall be attributable to the MCP actor in the audit trail.
- R11. All new behaviour shall have unit tests (backend jest, frontend vitest); no test shall need a database.
- R12. The permission model v2, the API contract and the MCP tool list shall be documented in the maros bitácora
  (ARCHITECTURE.md, DECISIONS.md) and the cerebro note, never as new loose docs inside the repos.

## API contract v2 (additive; the frontend and the MCP code against this, not against each other)
- `GET /permissions` → `{ permissions: [{code, group, label, description, risk, implies: string[]}], groups: [{key,
  label, description, permissions: string[]}], templates: [{key, label, description, permissions: string[]}] }`
  (existing fields stay).
- `GET /roles` → existing fields + `userCount`, `updatedAt`.
- `POST /roles/:id/duplicate` `{name}` → role.
- `POST /roles/impact` `{roleId?: number, permissions: string[]}` → `{ usersAffected, gained: string[], lost: string[],
  sampleUsers: [{id,name,email}] (≤20), added: string[] (implied), warnings: string[] }`.
- `GET /users/:id/access` → `{ userId, roleName, permissions: [{code,label,granted,via: 'role'|'none',reason}],
  sections: [{key,label,accessible}], leadTypeScope }`.
- `POST /users/bulk-role` `{userIds: number[], roleId}` → `{ updated: number, skipped: [{id, reason}] }`.
- `GET /roles/audit?roleId&limit` → `[{id, roleId, action, actor, at, diff}]`.
- `POST /access-requests` `{permission?, section?, reason}` → 201; `GET /access-requests?status` (users:write);
  `PATCH /access-requests/:id` `{status: 'approved'|'denied', note?}`.
- Errors: 409 `{code: 'last_admin' | 'system_role_protected', message}`.

## Edge cases & errors
- Unknown permission codes stored in `role_permissions` are ignored (existing behaviour) and never shown as granted.
- Duplicating a system role yields a non-system role. Deleting a role with users is refused with the user count.
- Bulk assignment skips deactivated users and the acting user's own demotion if it would violate R4.
- Impact preview for a new role (no id) compares against nothing: `gained` = all, `usersAffected` = 0.

## Constraints
- **Never touch the shared database**: the local `.env` of maros-nest points to production (Supabase). Do not run the API,
  `typeorm`, `psql`, `docker` DB commands or any script that connects to it; write SQL under `db/` in the existing
  `add-*.sql` idempotent style and do not apply it. Tests must not need a DB.
- Work only in the assigned worktrees on a feature branch; commits stay local; never push, merge or delete branches.
- Follow the closest repo instructions and existing structure (backend `modules/`, `common/`; frontend `features/users`
  ports/usecases/infra/presentation, Atomic Design, files under ~300 lines, one responsibility each).
- Preserve behaviour of existing endpoints and tools (additive changes only).
