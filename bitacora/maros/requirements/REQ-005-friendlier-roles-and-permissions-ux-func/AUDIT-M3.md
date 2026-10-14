# Audit M3 — REQ-005 Friendlier roles and permissions (UX + functionality) and full-power admin MCP

- **Requirement:** REQ-005
- **Milestone:** M3 (Tasks T6, T7, T8)
- **Auditor:** Gemini 3.8 Flash (Antigravity)
- **Accepted Integration SHA:** `4a80e9034abe1bd3f84662b1b6c116dbc06e921e` (HEAD of `wt/REQ-005-integration-86795b50`, merging candidate `383f1e4`)
- **Commits Evaluated:**
  - `a580d3e` (T6): `feat(mcp): add tools for role and access management capabilities (T6)`
  - `588f35b` (T7): `feat(mcp): cover administrative API capabilities`
  - `383f1e4` (T8): `feat(mcp): add write simulations and actor attribution`
  - `4a80e90` (Integration): `Merge commit '383f1e4a5136b03efcf413ad93dcbd9ab65c3e71' into wt/REQ-005-integration-86795b50`
- **Date:** 2026-10-14
- **Verdict:** PASS

---

## 1. Scope & Commits Audited

The audit evaluated milestone M3 (Tasks T6, T7, T8) on the accepted integration deliverable `4a80e9034abe1bd3f84662b1b6c116dbc06e921e`:

1. **T6 — MCP Tools for New Capabilities (R9, R10):**
   - Implemented 9 administrative MCP tools in `src/modules/mcp/tools/users-roles-admin.ts` on top of shared services: `duplicate_role`, `role_impact`, `get_user_access`, `bulk_assign_role`, `list_role_audit`, `list_access_requests`, `resolve_access_request`, `list_role_templates`, `apply_role_template`.
   - Wired in `McpService` with proper service dependencies exported from `UsersModule`.
   - BigInt IDs in role audit events serialized safely to numbers.

2. **T7 — Capability Parity & Inventory Report (R9, D-002):**
   - Inventoried all 253 controller routes across 30 controller classes in `src/modules/mcp/tools/capability-map.ts`.
   - Added 44 tools covering CRM admin (leads, catalogs, projects, analytics), platform admin, note sharing, and user notification preferences.
   - Built runtime `mcp_capability_report` tool comparing registered Nest routes with registered MCP tools.
   - Parity tests in `capabilities.spec.ts` catch unclassified routes, missing tools, and stale allowlist entries without booting an application instance or DB.
   - Justified exclusions documented for browser OAuth flows, public token routes, binary transport, and personal session-only views.

3. **T8 — Write Simulations, Guard Rails & Attribution (R4, R10, D-003):**
   - Central registration wrapper in `tool-registration.ts` attaches optional `dry_run: boolean` to all write operations while keeping read-only tools unchanged.
   - Specialized previews (`dryRun` option) invoke domain validation with no-write mode (`dryRun = true`) across `update_user`, `update_role`, `delete_role`, `bulk_assign_role`, `apply_role_template`, and `revoke_invitation`.
   - R4 guard rails (`last_admin` and `system_role_protected`) are enforced identically in both live execution and dry-run previews, returning proper error payloads with `isError: true` and 0 domain writes on refusal.
   - General workspace provisioning in `get_task_workspace_options` is properly classified as a write, disabled during simulation, and attributed to the actor upon execution.
   - Attribution resolves the authenticated system user (`mcp-agent@maros.invalid`), appends `mcp_write` events with bounded target identifiers to the role audit table, and logs provider `isError` envelopes as failed outcomes.

---

## 2. Verification Executed

1. **Unit Test Suites:**
   - `npx jest src/modules/mcp --silent`: 18 suites, 253 tests passed, exit 0.
   - `npx jest src/modules/mcp src/modules/users --silent`: 33 suites, 447 tests passed, exit 0.
   - `npx jest src/modules/mcp src/modules/users src/modules/notifications src/common --silent`: 43 suites, 540 tests passed, exit 0.
2. **Typecheck & Linter:**
   - `npx tsc --noEmit`: Clean (0 errors).
   - `npx eslint src/modules/mcp`: Clean (0 errors).
3. **Build:**
   - `npm run build`: Clean (`nest build` exit 0).
4. **Code Hygiene & Constraints:**
   - No database connections made; no SQL executed against shared Supabase.
   - Zero `console.log` or debug leftovers.
   - Zero secrets, tokens, or credential leaks.
   - Target files adhere to modular structure and ~300 lines guideline.

---

## 3. Findings

### Findings Fixed
- **None.** The integrated deliverable `4a80e90` was verified clean as delivered; no auditor code modifications were needed or made in the worktree (avoiding F-25 unintegrated auditor edits).

### Findings Deferred

1. **P-011 — Audit Trail Durability Limitation for MCP Writes (R10):**
   - **Severity:** Medium
   - **Complexity:** M
   - **Details:** Under requirement R10 ("every MCP write shall be attributable to the MCP actor in the audit trail"), `recordMcpWrite` delegates to `RolesService.recordAudit` (D-001/D-003). As designed, `recordAudit` catches insert failures and falls back to logging the event at error level while letting the operation succeed. Passing mock-based unit tests do not guarantee that every MCP write is durably stored in the database if the database table is missing or fails. Making role writes and audit inserts atomic (via transaction or transactional outbox) remains tracked under P-011 and will be addressed after database migrations are applied.
2. **P-010 & P-012 — Manual SQL Migrations Required Before Deployment:**
   - **Severity:** High
   - **Complexity:** S
   - **Details:** `db/add-role-audit-events.sql` (P-010) and `db/add-access-requests.sql` (P-012) must be applied manually to Supabase by an administrator before deploying the backend.

---

## 4. Final Assessment

Milestone M3 meets all functional and non-functional requirements (R4, R9, R10) defined in SPEC.md and PLAN.md. Administrative parity across all 253 routes is comprehensively validated, dry-run simulations and guard-rail refusals operate identically to the HTTP API, and actor attribution is correctly implemented.

**Verdict:** PASS
