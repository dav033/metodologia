# AUDIT-M2 — Milestone M2: Backend access explanation, bulk and requests

- **Date:** 2026-10-14
- **Auditor:** gemini-3.8-flash-low (Antigravity)
- **Target branch:** `feat/req-005-friendlier-roles-and-permissions-ux-func`
- **Commits evaluated:**
  - `06756bb` (T4): `feat(users): effective access per user and bulk role assignment`
  - `8ed59b8` (T5): `feat(users): access requests with notifications to approvers`
  - `b3312af` (M2-audit fix): `test(users): add unit tests for AccessRequestsRepository`
- **Milestone Scope:** Tasks T4 and T5 (REQ-005, covering R3, R4, R8).

---

## Verdict

**PASS-WITH-FIXES**

The implementation of Milestone M2 meets all requirements defined in SPEC.md and PLAN.md:
1. `GET /users/:id/access` explains effective access per catalog permission with human readable reasons, section visibility based on read permissions, lead type scope, and proper handling for deactivated and external users.
2. `POST /users/bulk-role` safely assigns roles in bulk up to 200 users, skips deactivated, already-assigned, self-demotions, and permission-bearing assignments to external users. It enforces guard rail R4 (refusing last-admin removal with 409 `last_admin`).
3. `POST /access-requests`, `GET /access-requests`, and `PATCH /access-requests/:id` provide full access request lifecycle with validations, preventing self-resolving, race handling with conditional updates, and notifications dispatched to active internal users with `users:write`.
4. Idempotent DDL `db/add-access-requests.sql` is provided without being executed against the database.
5. Unit test coverage across modules was validated without DB dependencies.

---

## Findings Fixed

1. **Missing unit tests for `AccessRequestsRepository`**
   - **Severity:** Low
   - **Issue:** `AccessRequestsRepository` was implemented with custom query methods (`findPendingFor`, `resolvePending`, `findMany`), but lacked unit test file unlike `role-audit.repository.spec.ts` and `users.repository.spec.ts`.
   - **Fix:** Added `src/modules/users/user-management/repositories/access-requests.repository.spec.ts` covering `create`, `findById`, `findPendingFor` (verifying `IsNull()` handling), `findMany`, and `resolvePending` (success and conflict/zero affected cases). Committed as `b3312af`.

---

## Findings Deferred

1. **P-012 — Apply `db/add-access-requests.sql` to Supabase manually**
   - **Severity:** High
   - **Complexity:** S
   - **Details:** The table `access_requests` and its indexes must be created in Supabase manually before deploying the backend. Tests run completely mock-based and do not hit the database.

---

## What Was Ran

- **Test suite:**
  `npx jest src/modules/users src/modules/notifications --silent`
  -> **15 test suites passed, 182 tests passed, 0 failures.**
- **Repository spec:**
  `npx jest src/modules/users/user-management/repositories/access-requests.repository.spec.ts`
  -> **6 tests passed.**
- **TypeScript compilation & Linting:**
  `npx tsc --noEmit && npx eslint src/modules/users src/modules/notifications src/entities`
  -> **Clean (0 errors, 4 pre-existing non-blocking warnings).**
- **Git diff & log:**
  Verified commits `06756bb` and `8ed59b8`. No secret leaks, debug leftovers, or DB connections.
