# Audit M1 — REQ-005 Friendlier roles and permissions (UX + functionality)

- **Requirement:** REQ-005
- **Milestone:** M1 (Tasks T1, T2, T3)
- **Auditor:** Gemini 3.8 Flash low (Antigravity)
- **Base commit:** `3a4ce7b` (origin/feat/req-001-fix-document-scans-and-estimate-email)
- **Audit HEAD:** `f574f58` (merging `56cf2dc` on `wt/M1-f37f0106`)
- **Date:** 2026-10-14
- **Verdict:** PASS

---

## 1. Scope & Commits Audited

The audit inspected all changes introduced in milestone M1 across tasks T1, T2, and T3:
- `4de4bcf`: feat(auth): describe permissions with label, risk and implications, add role templates (T1)
- `bfd0340`: feat(users): guard rails, impact preview, role duplication and rich catalog API (T2)
- `8b46730`: feat(users): role audit events entity, migration script, and recording (T3)
- `56cf2dc`: fix(users): keep role changes when the audit insert fails, clear role descriptions again (M1 review fixes)

### Requirements checked
- **R1**: Permission catalog carries label, plain description, risk (`low|medium|high`), and transitive `implies`. Exposes 5 role templates (Viewer, Sales, Finance, Project manager, Admin). Verified against `src/common/auth/permission-catalog.ts`, `src/common/auth/role-templates.ts`, and `src/common/auth/permissions.ts`.
- **R2**: Automatic implied permissions expansion on role save/update (`expandImplied()`), returning both full permissions and the `added` list. Verified in `RolesService.create`, `RolesService.update`, `RolesService.duplicate`.
- **R3**: API endpoints:
  - `POST /roles/:id/duplicate`: duplicates role with effective permissions; duplicated role is custom (`isSystem: false`).
  - `POST /roles/impact`: previews `usersAffected`, `gained`, `lost`, `sampleUsers` (up to 20), `added`, and `warnings`.
  - `GET /roles/audit`: returns audit trail filtered by `roleId` and `limit`.
  - Richer `GET /permissions` and `GET /roles` contracts matching SPEC §API contract v2.
- **R4**: Guard rails:
  - Last-admin protection: prevents removing `users:write` or deactivating/reassigning the last active admin, responding with HTTP 409 and code `'last_admin'`.
  - System role protection: prevents renaming, deleting, or altering permissions of system roles (e.g. `admin`), responding with HTTP 409 and code `'system_role_protected'`.
- **Database constraints**: No migrations executed against the shared database. `db/add-role-audit-events.sql` is idempotent (`IF NOT EXISTS`) and left unapplied as required.

---

## 2. Verification Executed

1. **Test Suites**:
   - `npx jest src/common/auth --silent`: 5 suites, 48 tests passed (T1).
   - `npx jest src/modules/users src/common --silent`: 17 suites, 215 tests passed (T2).
   - `npx jest src/modules/users --silent`: 8 suites, 126 tests passed (T3).
2. **Typecheck & Linter**:
   - `npx tsc --noEmit`: Clean, 0 errors.
   - `npx eslint src/common/auth src/modules/users`: 0 errors, 1 pre-existing warning in unmodified test file.
3. **Database & Side Effects**:
   - Verified no database connection or commands executed.
   - Verified no secrets or debug statements left behind in diff.

---

## 3. Findings

### Findings Fixed
- None required in this audit session. All findings noted during the implementer's antagonist review (best-effort audit insert on unapplied table D-001, empty string description clearing, effective permission diffs for member roles) were cleanly fixed and tested in commit `56cf2dc`.

### Findings Deferred
- **P-010** (Urgency: High, Complexity: S): Apply `db/add-role-audit-events.sql` to Supabase before deploying the backend.
- **P-011** (Urgency: Med, Complexity: M): Make role write and audit recording atomic (transaction or transactional outbox) once `db/add-role-audit-events.sql` is applied. Scheduled for T8.

---

## 4. Final Assessment

Milestone M1 satisfies all specification requirements (R1–R4, additive API contract v2, unit testing without a database, idempotent SQL script). Tests are comprehensive, unit tests pass cleanly, and the type checker is satisfied.

**Verdict:** PASS
