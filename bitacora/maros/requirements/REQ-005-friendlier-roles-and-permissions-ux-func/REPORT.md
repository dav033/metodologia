# REQ-005 — Friendlier roles and permissions (UX + functionality) and full-power admin MCP

Final session 26 · 2026-10-15 · Ready for owner review.
Backend repo: `/home/david/dev/maros/maros-nest`.
Frontend repo: `/home/david/dev/maros/maros-next`.
Branches:
- Backend: `feat/req-005-friendlier-roles-and-permissions-ux-func` at commit `4a80e90` (`3a4ce7b..4a80e90`, 16 commits).
- Frontend: `feat/req-005-friendlier-roles-and-permissions-ux-func` at commit `8ccc2fa` (`b8efd6a..8ccc2fa`, 5 commits).
- Bitácora: `metodologia` repo at commit `8a6763b`.
PLAN status: done. SPEC status: in-progress until owner review/merge. Nothing merged to main, pushed, deployed or published.

---

## Built

### 1. Backend: Catalog, Role Operations, Audit and Access (M1, M2)
- **R1 Permission Catalog & Templates**: Extended the 24-code permission catalog (`src/common/auth/permissions.ts`) with labels, descriptions, risk levels (`low|medium|high`), and DAG-based `implies` graph (`expandImpliedPermissions`). Added 5 role templates: Viewer, Sales, Finance, Project Manager, and Admin.
- **R2 Implied Permission Expansion**: Roles service automatically resolves implied permissions upon creation/update and reports newly expanded permissions.
- **R3 API Capabilities**:
  - `POST /roles/:id/duplicate`: Clones an existing role cleanly without inheriting system flags.
  - `POST /roles/impact`: Previews users affected, permissions gained/lost, implied additions, sample affected users (up to 20), and safety warnings.
  - `GET /users/:id/access`: Calculates per-user effective permissions, resolution reasons (`via: 'role'|'none'`), accessible sections, and lead-type scope.
  - `POST /users/bulk-role`: Bulk role assignment skipping deactivated users and self-demotion, enforcing system role protections and last-admin guard rails.
  - `GET /roles/audit`: Lists audit trail events for role modifications.
- **R4 Guard Rails**: Centralized `RoleGuardRailsService` prevents modifying or deleting protected system roles, and prevents demoting/deactivating the last active internal user with `users:write` (returns 409 with specific error codes `last_admin` or `system_role_protected`).
- **R8 Access Requests**: Entity and endpoints (`POST /access-requests`, `GET /access-requests`, `PATCH /access-requests/:id`) allowing members to request permissions and admins to resolve them with audit logging and notifications.
- **Unapplied Database Migrations**: Idempotent SQL files `db/add-role-audit-events.sql` and `db/add-access-requests.sql` created cleanly without running against the shared database (tracked under P-010 and P-012).

### 2. Full-Power Administrative MCP (M3)
- **R9 Full Parity & Capability Report**: Added MCP tools for role and access workflows (`duplicate_role`, `role_impact`, `get_user_access`, `bulk_assign_role`, `list_role_audit`, `list_access_requests`, `resolve_access_request`, `list_role_templates`, `apply_role_template`) plus 44 new administrative tools bringing 100% parity across all 253 API routes. Added `mcp_capability_report` and offline parity suite in `capabilities.spec.ts`.
- **R10 Dry-Run & Attribution**: Central registration wrapper in `tool-registration.ts` adds optional `dry_run` simulation to destructive/bulk operations with zero database side-effects. Guard rails are enforced identically in dry-run and execution. System actor (`mcp-agent@maros.invalid`) is recorded in audit logs.

### 3. Frontend UX & Workflows (M4)
- **Data Layer (`features/users`)**: Clean architecture implementation of domain models, ports, HTTP repositories (`RolesHttpRepository`, `UsersHttpRepository`, `AccessRequestsHttpRepository`), query usecases, mutation usecases, and React Query data/mutation hooks.
- **R5 Redesigned Role Editor (`RoleEditorDialog.tsx`)**: Grouped permissions by functional area, searchable items, risk badges, role template picker, auto-selection of implied dependencies with visual locking, before/after diff review step, and impact preview modal.
- **R6 Users Page & Effective Access (`UsersTable.tsx`, `EffectiveAccessDrawer.tsx`)**: Inline role descriptions, status and role filtering, multi-user selection with bulk role assignment action bar, role impact preview in invite modal (`InviteUserDialog.tsx`), and full effective access explanation drawer.
- **R7 Explanatory No-Access State (`NoAccessState.tsx`)**: Replaces silent redirects on `/settings/users` and `/settings/roles` when lacking `users:read`, displaying missing permissions and a 1-click "Request access" form.
- **R8 Admin Inbox (`AccessRequestsInbox.tsx`)**: Dedicated inbox on the users settings page for administrators with `users:write` to view, approve, and deny pending access requests.

### 4. Architecture Documentation (M5)
- **R12 Bitácora & Knowledge Base**: Comprehensive documentation in `bitacora/maros/ARCHITECTURE.md` §Permission model v2, architectural decisions D-004..D-006 in `bitacora/maros/DECISIONS.md`, backlog updates in `PENDING.md`, and references in Cerebro note `~/dev/cerebro/maros/arquitectura.md`.

---

## Verification evidence

All verification commands defined in [PLAN.md](PLAN.md) were executed against the actual integrated feature commits:

| Check / Requirement | Target Worktree / Repo | Command Executed | Result |
| --- | --- | --- | --- |
| Backend Modules (`M1`, `M2`, `M3`) | `maros-nest` (`wt/REQ-005-integration-86795b50`) | `npx jest src/common/auth src/modules/users src/modules/mcp src/modules/notifications --silent` | **Exit 0** (39 suites, 499 tests passed in 5.09s) |
| Frontend Users Feature (`M4`) | `maros-next` (`wt/REQ-005-integration-768f8753`) | `npx vitest run src/features/users` | **Exit 0** (11 suites, 56 tests passed) |
| Frontend Components (`M4`) | `maros-next` (`wt/REQ-005-integration-768f8753`) | `npx vitest run src/features/users src/components` | **Exit 0** (13 suites, 62 tests passed) |
| Full Frontend Suite (`T13`) | `maros-next` (`wt/REQ-005-integration-768f8753`) | `npx vitest run` | **Exit 0** (83 suites, 422 tests passed in 25.22s) |
| Backend TypeScript | `maros-nest` (`wt/REQ-005-integration-86795b50`) | `npx tsc --noEmit` | **Exit 0** (0 errors) |
| Frontend TypeScript | `maros-next` (`wt/REQ-005-integration-768f8753`) | `npx tsc --noEmit` | **Exit 0** (0 errors) |
| Frontend ESLint | `maros-next` (`wt/REQ-005-integration-768f8753`) | `npx eslint src/features/users src/app/settings/users src/app/settings/roles` | **Exit 0** (0 errors, 0 warnings) |
| MCP Route Parity (`R9`) | `maros-nest` (`wt/REQ-005-integration-86795b50`) | `npx jest src/modules/mcp/tools/capabilities.spec.ts` | **Exit 0** (All 253 routes inventoried and covered) |
| Acceptance Stories (`US-1`..`US-6`) | Cross-repo | Unit test suites covering each story | **Exit 0** (100% covered without DB) |
| Unapplied SQL Check | `maros-nest` (`wt/REQ-005-integration-86795b50`) | `git diff 3a4ce7b -- db/` | **Verified** (`db/add-role-audit-events.sql`, `db/add-access-requests.sql` idempotent, unapplied) |
| Documentation Grep (`R12`) | `metodologia` (`bitacora`) | `grep -q "Permission model v2" ~/bitacora/maros/ARCHITECTURE.md` | **Exit 0** (Cleanly documented) |

All 5 milestone audits (`AUDIT-M1.md` through `AUDIT-M5.md`) were completed and marked **PASS**. Cross-milestone integration between the backend REST API contract and frontend data layer was validated via tests.

---

## Rulings

- **D-001 (Audit Logging Fallback)**: Role audit inserts are best-effort. If the `role_audit_events` table is unavailable, the error is logged with the full event details and the committed role change succeeds without failing user operations.
- **D-002 (MCP Route Inventory)**: Parity testing inventories all 253 Nest routes. Public OAuth callbacks, token routes, multipart uploads, and personal session routes are explicitly excluded with documented rationales.
- **D-003 (MCP Dry-Run & Previews)**: Dry-run simulations for destructive tools invoke real domain validation with `dryRun = true`, guaranteeing identical guard-rail enforcement to live API calls.
- **D-004 (Permission Catalog & Templates)**: The catalog is defined in code with rich metadata; templates are copies applied at role creation rather than mutable foreign links.
- **D-005 (Access Requests Single-Shot Resolution)**: Resolving an access request records approval/denial and notifies the requester but does not automatically alter permissions. Access is granted manually by an admin to keep the role audit trail authoritative. Self-resolution is strictly forbidden (422 `OWN_ACCESS_REQUEST`).
- **D-006 (Last-Admin Calculation)**: The last-admin count specifically evaluates active, internal users. External users cannot access administrative endpoints and are excluded from the safety quorum.

---

## Needs your eyes

1. **Manual Supabase Migrations (P-010, P-012)**:
   - Before deploying the backend, run `db/add-role-audit-events.sql` and `db/add-access-requests.sql` in Supabase.
   - The application handles missing tables gracefully (role writes succeed with error logging; access request operations will fail with a 500 until tables exist).
2. **`GET /permissions` Response Shape**:
   - The endpoint previously returned an array of permission codes and now returns `{ permissions: PermissionMeta[], groups: [...], templates: [...] }`. Checked and verified that frontend consumers now use the v2 contract.

---

## Proposals

1. **P-011**: Implement transactional atomicity (or an outbox pattern) between role updates and audit event inserts once database migrations are applied.
2. **P-013**: Extend the explanatory `NoAccessState` component to other permission-guarded routes (e.g. `/finance`, `/tasks`) that currently redirect to `/dashboard`.
3. **P-014**: Add a partial unique index on `(user_id, permission_code)` where `status = 'pending'` in `access_requests` to prevent check-then-insert race conditions on concurrent requests.
4. **P-015**: Add automated end-to-end server-side gating tests for `/settings/users` and `/settings/roles`.

---

## Pending

- **High Urgency**:
  - `P-010`: Apply `db/add-role-audit-events.sql` manually to Supabase.
  - `P-012`: Apply `db/add-access-requests.sql` manually to Supabase.
- **Medium Urgency**:
  - `P-011`: Atomic role write + audit insert.
- **Low Urgency**:
  - `P-013`: Apply `NoAccessState` to remaining guarded routes.
  - `P-014`: Add partial unique index for pending access requests.
  - `P-015`: Add server-side gating tests for settings pages.

---

## Walkthrough

1. **Exploring Permissions & Building Roles**:
   - Navigate to `/settings/roles`. The table displays existing roles with user counts and last updated dates.
   - Click **Create Role**: Choose a starting template (e.g., *Sales* or *Finance*). Grouped permissions are displayed with descriptive labels and risk badges (`low`, `medium`, `high`).
   - Selecting a high-level permission (such as `leads:write`) automatically checks and visually locks implied dependencies (`leads:read`).
   - Proceed to the **Review & Diff** tab to see exactly what permissions are added/removed and review the **Impact Preview** before confirming.
2. **Managing Users & Explaining Effective Access**:
   - Navigate to `/settings/users`. Roles display inline descriptions under the dropdown selector.
   - Filter users by role or account status. Select multiple users via checkboxes to open the floating **Bulk Role Change** bar.
   - Click the **View Access** button on any user row to open the `EffectiveAccessDrawer`: inspect exactly which sections are accessible, active lead-type scopes, and the reason each permission is granted (`via: 'role'`).
3. **Graceful Access Requests**:
   - If a member navigates to `/settings/users` or `/settings/roles` without `users:read`, they are greeted by `NoAccessState` detailing the required permissions and an admin contact list.
   - Submitting the "Request access" form dispatches a notification to all administrators with `users:write`.
   - Administrators see pending requests in the `AccessRequestsInbox` at the top of the users page, with quick **Approve** and **Deny** actions.
4. **Agentic Administration via MCP**:
   - The Sami agent interacts using tools such as `role_impact`, `duplicate_role`, and `bulk_assign_role`.
   - Passing `dry_run: true` returns exact simulation previews without altering data.
   - Any attempt to demote the last remaining admin or alter system roles is blocked with code `last_admin` or `system_role_protected`. All actions are attributed to `mcp-agent@maros.invalid` in the audit log.
