---
req: REQ-005
status: approved
created: 2026-10-14
---
# Plan — REQ-005 Friendlier roles and permissions and full-power admin MCP

## Approach
Contract-first and additive. Backend first (catalog metadata, role operations, guard rails, audit, access explanation,
bulk, access requests), then the MCP surface on top of the same services (so API and MCP share one set of guard
rails), then the frontend against the API contract in SPEC.md. Everything is unit-tested without a database. SQL is
written as idempotent files under `db/` and never applied. Alternatives (a permission DSL, a separate policy service,
row-level security) were rejected as out of scope.

## Global constraints
- Never connect to or modify the shared database; do not run the API, typeorm or psql. No `.env` is available in worktrees.
- Work in the assigned worktree on the feature branch; commit locally, never push, merge or delete.
- Additive changes only; existing endpoints, tools and permission codes keep working.
- Closest repo conventions; files under ~300 lines; one responsibility per file; tests next to the code.
- Install dependencies in the worktree with `npm ci` if `node_modules` is absent (offline cache first).

## Tasks

### M1 — Backend: catalog and role operations
- [ ] T1 — Extend the permission catalog with label, description, risk and `implies` per permission, add role templates (Viewer, Sales, Finance, Project manager, Admin) and an `expandImplied()` helper; keep existing codes and exports · repo: backend · covers: R1, R2 · verify: `npx jest src/common/auth --silent`
- [ ] T2 — Roles service/controller: implied expansion on save, duplicate role, impact preview endpoint (`POST /roles/impact`), guard rails for last-admin and system roles with 409 codes, richer `GET /permissions` and `GET /roles` per the contract · repo: backend · after: T1 · covers: R2, R3, R4 · verify: `npx jest src/modules/users src/common --silent`
- [ ] T3 — Role audit trail: entity, idempotent `db/add-role-audit-events.sql` (not applied), recording on create/update/delete/duplicate/bulk and `GET /roles/audit` · repo: backend · after: T2 · covers: R3 · verify: `npx jest src/modules/users --silent`

### M2 — Backend: access explanation, bulk and requests
- [ ] T4 — `GET /users/:id/access` (effective access with per-permission reason and sections) and `POST /users/bulk-role` honoring the guard rails and skipping deactivated users · repo: backend · after: T3 · covers: R3, R4 · verify: `npx jest src/modules/users --silent`
- [ ] T5 — Access requests: entity, idempotent `db/add-access-requests.sql` (not applied), create/list/resolve endpoints, notify users with `users:write` through the notifications module · repo: backend · after: T4 · covers: R8 · verify: `npx jest src/modules/users src/modules/notifications --silent`

### M3 — MCP: every administrative power, with guard rails
- [ ] T6 — MCP tools for the new capabilities (duplicate_role, role_impact, get_user_access, bulk_assign_role, list_role_audit, list_access_requests, resolve_access_request, list_role_templates, apply_role_template) built on the shared services · repo: backend · after: T5 · covers: R9, R10 · verify: `npx jest src/modules/mcp --silent`
- [ ] T7 — Capability parity: compare every administrative controller route with the MCP tools, add the missing ones (user lifecycle, lead-type scope, notification preferences admin, etc.) and add `mcp_capability_report` plus a test that fails when an allowlisted route has no tool · repo: backend · after: T6 · level: architecture · covers: R9 · verify: `npx jest src/modules/mcp --silent`
- [ ] T8 — Guard rails and attribution for MCP writes: `dry_run` on destructive and bulk tools, the same R4 refusals, MCP actor recorded in the role audit trail · repo: backend · after: T7 · covers: R4, R10 · verify: `npx jest src/modules/mcp src/modules/users --silent`

### M4 — Frontend: friendlier roles, users and access
- [ ] T9 — Data layer in `features/users`: models, ports, HTTP repositories, usecases and hooks for permissions v2, impact preview, effective access, bulk role, audit and access requests, with mapper/usecase tests · repo: frontend · after: T5 · covers: R5, R6, R8, R11 · verify: `npx vitest run src/features/users`
- [ ] T10 — Role editor redesign: grouped permissions with descriptions and risk badges, search, template picker, implied auto-select, before/after diff and impact preview before confirming, duplicate role · repo: frontend · after: T9 · covers: R5 · verify: `npx vitest run src/features/users`
- [ ] T11 — Users page: inline role descriptions, role preview in the invite dialog, bulk role change, role/status filters and the effective-access drawer · repo: frontend · after: T10 · covers: R6 · verify: `npx vitest run src/features/users`
- [ ] T12 — Permission-aware UX: explanatory no-access state with "request access", hidden or explained navigation, and the admin inbox for access requests · repo: frontend · after: T11 · covers: R7, R8 · verify: `npx vitest run src/features/users src/components`
- [ ] T13 — Frontend consistency pass: run typecheck and lint, compare with the baseline errors of the base commit, fix only what this requirement introduced, and run the whole vitest suite · repo: frontend · after: T12 · covers: R11 · verify: `npx vitest run`

### M5 — Documentation
- [ ] T14 — Document permission model v2, the API contract and the MCP tool list in the maros bitácora (ARCHITECTURE.md, DECISIONS.md) and the cerebro note, nothing new in the repos · repo: backend · after: T8, T13 · kind: docs · covers: R12 · verify: `grep -q "Permission model v2" "$BITACORA_ROOT/maros/ARCHITECTURE.md" || grep -q "Permission model v2" ~/bitacora/maros/ARCHITECTURE.md`

## Verification
Backend `npx jest` for the touched modules and frontend `npx vitest run` pass; no file under `db/` was executed; the
MCP capability report lists no administrative route without a tool; each acceptance story US-1..US-6 is covered by a test.

## Rulings
<!-- Judgment calls made during execution without asking. -->

## Progress log
- 2026-10-14: spec and plan written by the HQ session (790c0548) under the owner's "assume and go" instruction.
- 2026-10-14 11:21 plan APPROVED (terminal)
