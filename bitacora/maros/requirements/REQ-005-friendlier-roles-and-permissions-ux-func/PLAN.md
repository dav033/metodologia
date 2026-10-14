---
req: REQ-005
status: launched
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
- [x] T1 — Extend the permission catalog with label, description, risk and `implies` per permission, add role templates (Viewer, Sales, Finance, Project manager, Admin) and an `expandImplied()` helper; keep existing codes and exports · repo: backend · covers: R1, R2 · verify: `npx jest src/common/auth --silent`
- [x] T2 — Roles service/controller: implied expansion on save, duplicate role, impact preview endpoint (`POST /roles/impact`), guard rails for last-admin and system roles with 409 codes, richer `GET /permissions` and `GET /roles` per the contract · repo: backend · after: T1 · covers: R2, R3, R4 · verify: `npx jest src/modules/users src/common --silent`
- [x] T3 — Role audit trail: entity, idempotent `db/add-role-audit-events.sql` (not applied), recording on create/update/delete/duplicate/bulk and `GET /roles/audit` · repo: backend · after: T2 · covers: R3 · verify: `npx jest src/modules/users --silent`

### M2 — Backend: access explanation, bulk and requests
- [x] T4 — `GET /users/:id/access` (effective access with per-permission reason and sections) and `POST /users/bulk-role` honoring the guard rails and skipping deactivated users · repo: backend · after: T3 · covers: R3, R4 · verify: `npx jest src/modules/users --silent`
- [x] T5 — Access requests: entity, idempotent `db/add-access-requests.sql` (not applied), create/list/resolve endpoints, notify users with `users:write` through the notifications module · repo: backend · after: T4 · covers: R8 · verify: `npx jest src/modules/users src/modules/notifications --silent`

### M3 — MCP: every administrative power, with guard rails
- [x] T6 — MCP tools for the new capabilities (duplicate_role, role_impact, get_user_access, bulk_assign_role, list_role_audit, list_access_requests, resolve_access_request, list_role_templates, apply_role_template) built on the shared services · repo: backend · after: T5 · covers: R9, R10 · verify: `npx jest src/modules/mcp --silent`
- [x] T7 — Capability parity: compare every administrative controller route with the MCP tools, add the missing ones (user lifecycle, lead-type scope, notification preferences admin, etc.) and add `mcp_capability_report` plus a test that fails when an allowlisted route has no tool · repo: backend · after: T6 · level: architecture · covers: R9 · verify: `npx jest src/modules/mcp --silent`
- [x] T8 — Guard rails and attribution for MCP writes: `dry_run` on destructive and bulk tools, the same R4 refusals, MCP actor recorded in the role audit trail · repo: backend · after: T7 · covers: R4, R10 · verify: `npx jest src/modules/mcp src/modules/users --silent`

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
- 2026-10-14 (M3, session 13): the prior M3 candidate was rejected at `scope_unchecked` (`scope declarations are missing`), not by its tests. Restore the clean assigned branch through reviewed T7 commit 588f35b with a fast-forward, then recover unfinished T8 separately. The live supervisor now derives missing allowed paths from the candidate diff before integration; retain the assigned branch and let the supervisor integrate it. No supervisor source or live task scope is changed here.
- 2026-10-14 (M3, session 13): T8 uses the registration boundary for additive dry_run and mcp_write attribution, with real shared-service domain previews for user/role R4 operations. Generic previews explicitly identify schema_only validation; existing confirmations remain required. Keep D-001 log fallback and P-011 instead of claiming atomic delivery without the unapplied SQL (D-003).
- 2026-10-14 (M3, session 13): regression seam is the actual user/role MCP registration plus real services with repository stand-ins; it verifies both execution and preview last_admin/system_role_protected responses, zero domain writes on refusal and actor on role/MCP events. A provider error-envelope regression first failed (outcome incorrectly succeeded), then passed after correction.
- 2026-10-14 (M3, session 13): antagonist found hidden General-workspace provisioning inside get_task_workspace_options and incomplete create-from-template previews. Both fixed with initially failing tests: classify options as write, propagate provisioning actor, and reuse role creation validation for name conflicts. One re-review requested; no deferred or dropped findings.
- 2026-10-14 (M1, session 6): role audit recording is best-effort — a failed `role_audit_events` insert is logged with the full event and the already-written role change succeeds (D-001; atomicity revisited in T8, P-011).
- 2026-10-14 (M1, session 6): the update audit diff records what the role effectively grants after the save (`resultingPermissions`), so edits to the code-resolved `member` role do not claim permission changes that never take effect.
- 2026-10-14 (M1, session 6): `PATCH /roles/:id` keeps the base behaviour of clearing the description with `''`; NULL and `''` are both "no description" and moving between them is neither written nor audited.

- 2026-10-14 (M2, session 8): bulk role change skips the acting user always (`self_modification`), not only when their demotion would break R4; it matches PATCH /users/:id, which refuses every self role change (stricter than SPEC's wording).
- 2026-10-14 (M2, session 8): the last-admin count (`countActiveByRoleIds` and its Excluding variant) counts internal users only. External users cannot use permission-guarded routes, so counting them let the guard say yes while nobody could administer (review finding).
- 2026-10-14 (M2, session 8): `UsersRepository.findById` loads `role.permissions`. Without them `effectivePermissionsOf` returned no permissions for custom roles, so the access explanation and the guard rails were wrong for them.
- 2026-10-14 (M2, session 8): bulk assignment never gives an external user a role that grants permissions (`external_role_not_allowed`), the same rule as the invitation.
- 2026-10-14 (M2, session 8): the R4 check and the bulk UPDATE are not one transaction or row lock; the window is the same as PATCH /users/:id. Recorded as follow-up together with P-011.
- 2026-10-14 (M2, session 8): an access request approved or denied records the decision and notifies the requester; it grants nothing. The role is changed by hand, so the role audit trail stays the only place access is given.
- 2026-10-14 (M2, session 8): nobody decides their own access request (`OWN_ACCESS_REQUEST`, 422). Decisions are a conditional UPDATE on `status = 'pending'`, so two admins deciding at once cannot both win (409 `ACCESS_REQUEST_ALREADY_RESOLVED`).

- 2026-10-14 (M3, session 12): T7 inventories all 253 routes, including permission-guarded business routes. Personal session views, OAuth callbacks, public token endpoints and HTML/multipart transport are explicitly excluded. The report discovers live routes; offline parity tests use controller source and actual McpService registration (D-002).
- 2026-10-14 (M3, session 12): preserve list_permissions.permissions as codes; add permissionMetadata/templates. Notification preference tools accept explicit userId, like existing notification administration. Sharing writes retain the system user's per-note checks; no employee impersonation is added.
- 2026-10-14 (M3, session 12): Workflow is unavailable in this harness; use bounded subagents and explicit task verdicts. The offline MCP handler/registration seam catches schema/delegation/parity drift; existing domain service tests own business-rule checks.

## Progress log
- 2026-10-14: spec and plan written by the HQ session (790c0548) under the owner's "assume and go" instruction.
- 2026-10-14 11:21 plan APPROVED (terminal)
- 2026-10-14 11:21 launched marathon supervisor (pool auto, haiku) from HQ in `/home/david/dev/maros`
- 2026-10-14 12:55 M1 session 6 (4c48366e): earlier M1 failures were environmental (no node_modules in the integration worktree). Review fixes committed as 56cf2dc on wt/M1-f37f0106. T1–T3 verify commands green (48 / 215 / 126 tests) and tsc clean; D-001, P-010 and P-011 added.
- 2026-10-14 12:52 T1 done (isolated integration) — commit 4de4bcf (+ review fixes 56cf2dc) on wt/M1-f37f0106; 'npx jest src/common/auth --silent' exit 0: 5 suites, 48 tests pass; tsc --noEmit clean; eslint clean; prior failures were the integration worktree lacking node_modules (npx install prompt), now resolved — plain npx resolves local jest 30.1.3 there
- 2026-10-14 12:52 T2 done (isolated integration) — commit bfd0340 + 56cf2dc on wt/M1-f37f0106; 'npx jest src/modules/users src/common --silent' exit 0: 17 suites, 215 tests pass; tsc --noEmit clean (2 spec TS2554 errors fixed in 56cf2dc); description clearing regression fixed with tests; antagonist approved after re-review
- 2026-10-14 12:52 T3 done (isolated integration) — commit 8b46730 + 56cf2dc on wt/M1-f37f0106; 'npx jest src/modules/users --silent' exit 0: 8 suites, 126 tests pass; audit made best-effort after the committed role write (D-001), logged events carry the full payload + time (tests spy the log); db/add-role-audit-events.sql idempotent, not applied (P-010); antagonist approved after re-review
- 2026-10-14 12:56 M1-audit done (marathon) — pass: verified R1-R4 against 3a4ce7b..f574f58; npx jest auth (48) + users/common (215) + users (126) passed; tsc and eslint clean; unapplied sql db/add-role-audit-events.sql clean
- 2026-10-14 M2 session 8: T4 done — commit 06756bb on wt/M2-f2e51f10 (on top of f574f58). 'npx jest src/modules/users --silent' exit 0 on the exported index: 11 suites, 153 tests; tsc clean; three antagonist passes, last CLEAR.
- 2026-10-14 13:09 T4 done (isolated integration) — commit 06756bb on wt/M2-f2e51f10 (on top of f574f58). 'npx jest src/modules/users --silent' exit 0 on the staged index exported to a clean dir: 11 suites, 153 tests pass; tsc --noEmit clean; eslint clean on touched files (one pre-existing warning in user-invitations.service.spec.ts). Antagonist: three passes, last CLEAR. Known limit recorded as follow-up: R4 check and UPDATE are not one transaction (same window as PATCH).
- 2026-10-14 13:09 T5 done (isolated integration) — commit 8ed59b8 on wt/M2-f2e51f10: 'npx jest src/modules/users src/modules/notifications --silent' exit 0: 14 suites, 176 tests; tsc --noEmit clean; eslint clean on new files. Antagonist: first review (no blockers; fixed external-free checks, duplicate pending, whitespace reason, timestamptz), re-review CONCERNS on the race only, documented as best-effort. Follow-ups in the T4 task note.
- 2026-10-14 13:13 M2-audit done (marathon) — pass-with-fixes: T4 and T5 verified against SPEC R3, R4, R8; 15 suites, 182 tests pass; tsc and eslint clean; added missing AccessRequestsRepository unit tests; P-012 logged for manual DB migration
- 2026-10-14 13:52 T6 done (isolated integration) — commit a580d3e on wt/T6-0724f01c; npx jest src/modules/mcp --silent exit 0 (13 suites, 197 tests pass); tsc --noEmit clean; eslint clean
- 2026-10-14 M3 session 12: T7 committed as 588f35b on wt/M3-c2e32ae9. 253 routes (SSE included), 44 new tools; npx jest src/modules/mcp --silent: 16 suites/242 tests pass; tsc and touched lint/build pass. Antagonist: 3 fixed (financial trusted context, SSE inventory, regression envelope), 0 deferred, 0 dropped; one re-review. Full lint baseline has 2 unrelated errors.
- 2026-10-14 M3 session 13: T7 recovered and freshly verified; T8 committed as 383f1e4 on wt/M3-b82d588f. Final exact gates: 18 MCP suites/253 tests and 33 MCP+users suites/447 tests pass; tsc, targeted ESLint and build pass. Full lint retains 2 baseline errors/19 warnings. No task-workspaces-specific suites exist; its real assignment service is covered by MCP regressions. Antagonist: 2 fixed, 0 deferred, 0 dropped; one re-review SOUND. Logs /tmp/maros-m3-session13-t8-reviewed-*.log. Supervisor integration and independent M3 audit remain unclaimed.
- 2026-10-14 14:41 T7 done (isolated integration) — Reviewed commit 588f35b recovered by fast-forward on wt/M3-b82d588f; fresh npx jest src/modules/mcp --silent exit 0: 16 suites/242 tests; tsc and build pass. Independent T7 spec review APPROVE. Full lint has exactly 2 known baseline errors, 19 warnings. Prior rejection was scope_unchecked, live supervisor now derives missing allowed paths. Evidence /tmp/maros-m3-session13-t7-{jest,tsc,build,lint}.log. No DB or external writes.
- 2026-10-14 14:41 T8 done (isolated integration) — Commit 383f1e4 on wt/M3-b82d588f, ancestor T7 588f35b. Additive dry_run, real shared-service R4 previews, system actor in role and mcp_write audit events; provisioning and template-name regressions first red then green. Exact gates: MCP 18 suites/253 tests and MCP+users 33 suites/447 tests pass. tsc, targeted lint and build pass. Full lint retains 2 baseline errors/19 warnings; task-workspaces has no dedicated suites, real service covered in MCP tests. Antagonist 2 fixed/0 deferred/0 dropped, one re-review SOUND. D-003/docs/day/week/index updated, notes saved. Path-scope diagnostic safe for 82 paths; all jobs finished and tree clean. Evidence /tmp/maros-m3-session13-t8-reviewed-*.log. D-001/P-010/P-011/P-012 retained; no SQL, DB, push or deployment. Supervisor integration and independent M3 audit remain.
- 2026-10-14 14:49 M3-audit done (marathon) — pass: T6, T7, T8 verified against integration SHA 4a80e90; 43 suites, 540 tests pass (mcp, users, notifications, common); tsc, eslint and build clean; R10 dry-run, previews and attribution verified; P
