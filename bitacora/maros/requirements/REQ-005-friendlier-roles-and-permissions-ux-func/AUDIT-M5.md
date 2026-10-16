# Audit M5 — REQ-005 Friendlier roles and permissions (UX + functionality)

- **Requirement:** REQ-005
- **Milestone:** M5 (Task T14)
- **Auditor:** Gemini 3.8 Flash low (Antigravity)
- **Base commit:** `3a4ce7b` (origin/feat/req-001-fix-document-scans-and-estimate-email)
- **Audit Target:** T14 documentation changes in bitácora (`ARCHITECTURE.md`, `DECISIONS.md`, `PENDING.md`) and Cerebro note (`~/dev/cerebro/maros/arquitectura.md`)
- **Date:** 2026-10-15
- **Verdict:** PASS

---

## 1. Scope & Commits Audited

The audit inspected all changes introduced in milestone M5 for task T14:
- Commit `e8c750c` and `4a1248c` (wt/T14-4ec8b9d4, integrated to HEAD `9fb38cf` on metodologia/bitácora):
  - `bitacora/maros/ARCHITECTURE.md` §Permission model v2: comprehensive documentation of the catalog and metadata, templates, guard rails (HTTP/MCP shared), effective access calculation, audit logging (`role_audit_events`), access requests model, detailed API contract v2 table, complete MCP admin tool list, and known gaps.
  - `bitacora/maros/DECISIONS.md`: Recorded formal architectural decisions D-004 (permission model v2 metadata, templates as copies, shared guard rails), D-005 (access requests grant nothing by themselves, single-shot resolution, self-resolution refused), and D-006 (member role code resolution, last-admin counting internal active users only).
  - `bitacora/maros/PENDING.md`: Clarified P-014 wording to accurately reflect check-then-insert race condition vs index presence.
  - Cerebro note `~/dev/cerebro/maros/arquitectura.md`: Added section referencing the permission model v2 bitácora documentation and summarizing shared guard rails and pending migrations.

### Requirements checked
- **R12**: Permission model v2, API contract v2, and MCP administrative tool list are properly documented in the maros bitácora (`ARCHITECTURE.md`, `DECISIONS.md`) and Cerebro note; no loose documentation files created inside the code repositories.
- **Accuracy**: Checked API contract table against the implemented endpoints and controllers in `wt/REQ-005-integration-86795b50` (`users.controller.ts`, `user-access.controller.ts`, `access-requests.controller.ts`), verifying error codes (409, 422, 400), breaking change notes (`GET /permissions` `permissions` shape), and MCP tools coverage.
- **Safety**: No code files modified, no database migrations executed against live databases, no secrets, no debug leftovers.

---

## 2. Verification Executed

1. **Verify Command**:
   - `grep -q "Permission model v2" "$BITACORA_ROOT/maros/ARCHITECTURE.md" || grep -q "Permission model v2" ~/bitacora/maros/ARCHITECTURE.md`: PASSED (exit code 0).
2. **Decisions Check**:
   - D-004, D-005, and D-006 verified present in `/home/david/bitacora/maros/DECISIONS.md`.
3. **Cerebro Note Check**:
   - Verified section `## Permisos v2 y MCP administrativo (REQ-005)` in `/home/david/dev/cerebro/maros/arquitectura.md`.
4. **Clean Worktree Check**:
   - Working tree clean, zero uncommitted or loose files in repos.

---

## 3. Findings

### Findings Fixed
- None required during the audit session. Two rounds of antagonist review during T14 addressed all discrepancies (error codes, 24-code catalog size, breaking array-to-object change in `GET /permissions`) prior to milestone sign-off.

### Findings Deferred
- None from M5 itself. Existing deferred backlog items remain tracked in `PENDING.md`:
  - **P-010**: Apply `db/add-role-audit-events.sql` to Supabase by hand before deploying REQ-005.
  - **P-011**: Make role write + audit insert atomic once SQL is applied.
  - **P-012**: Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005.
  - **P-013**: Apply explanatory no-access state to remaining guarded pages.
  - **P-014**: Make duplicate-pending check race-safe via partial unique index.
  - **P-015**: Add server-side gating tests for settings/users and settings/roles.

---

## 4. Final Assessment

Milestone M5 satisfies R12 completely and faithfully reflects the implementation delivered across M1–M4. Documentation is clear, accurate, and properly placed.

**Verdict:** PASS
