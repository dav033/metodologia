# maros — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Role audit events are recorded best-effort after the role write
- **Date:** 2026-10-14 · **Status:** Accepted
- **Context:** REQ-005/T3 records an audit row per role create/update/delete/duplicate/bulk in `role_audit_events`,
  whose SQL (`db/add-role-audit-events.sql`) is written but not applied, while CI deploys `main` automatically. Role
  writes (`rolesRepo.save` + `replacePermissions` / `delete`) are not transactional and commit before the audit
  insert, so a failing insert turned a completed role change into a 500 that invites a retry.
- **Decision:** `RolesService.recordAudit` catches a failed insert and logs the whole event (with an ISO `at`) at
  error level; the role change succeeds. `GET /roles/audit` still fails until the SQL is applied.
- **Alternatives:** one transaction around role writes + audit — every role edit would fail until the SQL is applied,
  and it needs EntityManager plumbing through `RolesRepository`; outbox table — same migration dependency, more moving
  parts than M1 needs.
- **Consequences:** + a missing table or a transient DB error never breaks role administration; + the log line is
  enough to backfill. − R10 ("every MCP write attributable in the audit trail") is not guaranteed: a failed insert
  leaves only a log line. Revisit in REQ-005/T8 (transaction or outbox once the SQL is applied).
- **Source:** [day log](2026-10/W3/2026-10-14.md) · REQ-005

## D-002 — Explicit MCP capability inventory and system attribution
- **Date:** 2026-10-14 · **Status:** Accepted
- **Context:** REQ-005/T7 found 253 API routes and gaps across CRM, projects, catalogs, users and sharing. Matching tool names alone hid partial coverage.
- **Decision:** Map controller/handler pairs explicitly to tool names; build the runtime report from live Nest route metadata and the actual per-server registrations. An offline source inventory test rejects unclassified routes, missing tools and stale entries. OAuth callbacks, public token routes, binary transport and personal session-only views carry explicit exclusions.
- **Alternatives:** Hand-maintained report detached from registration — could claim nonexistent tools; automatically infer parity from similar service calls — conflates variants and composite operations; impersonate employees for note sharing — loses attribution and bypasses ownership.
- **Consequences:** + New routes fail the parity gate until reviewed. + Notification preferences use explicit userId, like existing notification tools. + Sharing writes name the system actor and retain note access checks; an ungranted system user may be refused. + Existing list_permissions.permissions stays a string array; additive permissionMetadata and templates carry v2 metadata. − Inventory requires review when route semantics change. − Personal/OAuth/transport exclusions are reported, not silently counted as covered.
- **Rollback:** Revert the T7 commit; existing tool names and input fields are unchanged.
- **Source:** [day log](2026-10/W3/2026-10-14.md) · REQ-005/T7

## D-003 — Central MCP simulation and attribution with shared role guard rails
- **Date:** 2026-10-14 · **Status:** Accepted
- **Context:** REQ-005/T8 spans destructive/bulk tools across many modules. Per-handler flags or actor logging would leave future tools unprotected; user/role changes must share R4 with HTTP.
- **Decision:** The existing MCP registration boundary validates input and adds optional boolean `dry_run` to every write; reviewed read tools are explicitly classified and unknown tools default to write. Simulation returns before execution/audit. User/role update, role deletion, invitation revocation, bulk assignment and template application reuse the service validations with a no-write mode. Other tools label simulations `schema_only`, report bounded target identifiers and explicitly state resource eligibility is checked only when executed. Existing required confirmations still apply.
- **Attribution:** Actual MCP operations resolve the system actor before execution and append `mcp_write` to the existing role audit table with nullable roleId, tool, identifiers and succeeded/failed outcome. Role domain events also receive the actor email. Provider `isError` envelopes count as failed. Neither arguments containing passwords/body content nor full tool results are copied into the audit row. Simulations create no write event; refused execution creates only a failed operation event.
- **Alternatives:** A flag and audit call in every handler — duplicates policy and misses future tools; invoking destructive handlers to calculate previews — risks effects; a new audit table/outbox — needs another migration and does not make remote effects atomic; global transactions — cannot roll back provider operations.
- **Consequences:** + Existing calls without dry_run retain execution behavior. + HTTP and MCP share last-admin/system-role refusals. + Audit failure keeps D-001's observable event log fallback. − Generic simulations do not guarantee resource eligibility. − Durable/atomic auditing remains P-010/P-011; no DB migration is applied by agents.
- **Rollback:** Revert the T8 commit; no schema change beyond a SQL comment. Existing audit rows remain readable and tool inputs without dry_run remain compatible.
- **Source:** [day log](2026-10/W3/2026-10-14.md) · REQ-005/T8
- **Implementation refinement:** Classify get_task_workspace_options as a write because it provisions the General workspace; its optional service actor argument preserves HTTP compatibility. Template creation simulations reuse the role creation validation, including occupied names. Both refinements confirmed by offline regression tests after antagonist findings.

## D-004 — Permission model v2 is metadata beside the existing codes, with shared guard rails
- **Date:** 2026-10-15 · **Status:** Accepted
- **Context:** REQ-005/M1–M4 must make 24 bare permission codes understandable, let admins build roles from templates with a preview, explain any user's access, and expose every administrative power through MCP with the same refusals as the API. Existing codes, stored `role_permissions` rows and endpoints must keep working.
- **Decision:** `permissions.ts` stays the only list of codes. `permission-catalog.ts` adds label, description, risk and a transitive `implies` closure as a total record (a missing description is a compile error). Templates (Viewer, Sales, Finance, Project manager, Admin) are closed under implication and are copied into a role, never linked. The R4 guard rails (`last_admin`, `system_role_protected`) live in the users/roles services, so HTTP and MCP refuse the same changes. The effective-access reason is computed on the server.
- **Alternatives:** a permission DSL or policy engine — a second source of truth and more code than the 24-code problem needs; row-level security — out of scope (the row scope stays the existing lead-type scope); live-linked templates — a template edit would silently change roles that already exist; a separate MCP-only policy — the API and MCP could disagree about what is refused.
- **Consequences:** + Adding a permission without metadata fails the build. + One set of refusals for both surfaces. + Effective access and impact previews answer "why" and "who is affected" before a save. − Metadata must be kept in step with the codes by hand (the compile-time record guards only the presence, not the wording). − The migrations for `role_audit_events` and `access_requests` are written but not applied (P-010, P-012); role write and audit insert are not atomic (P-011).
- **Source:** [day log](2026-10/W3/2026-10-15.md) · REQ-005 (M1–M4); documented in ARCHITECTURE.md §Permission model v2 (REQ-005/T14).

## D-005 — Access requests grant nothing; resolution is single-shot and self-resolution is refused
- **Date:** 2026-10-15 · **Status:** Accepted
- **Context:** REQ-005/M2 (T5) added access requests that notify `users:write` holders. The question was whether an approval should grant the requested permission, and how to stop concurrent or self resolutions.
- **Decision:** Approving or denying a request only changes the request's status; the admin grants access by changing the role (through the normal guarded role flow). A request resolves once: a second resolution is refused with 409 `ACCESS_REQUEST_ALREADY_RESOLVED`, and resolving your own request is refused with 422 `OWN_ACCESS_REQUEST`. A request is also refused (409 `ACCESS_REQUEST_ALREADY_PENDING`) if the same user already has a pending one for the same permission or section.
- **Alternatives:** approve = auto-grant a role or permission — bypasses the R4 guard rails and the audit trail of role changes; allow self-resolution — an admin could grant themselves access through the request path; rely on a unique index for pending duplicates — the SQL is written but not applied, and the index is not yet in `db/add-access-requests.sql`.
- **Consequences:** + Granting always goes through the role flow, so R4 and `role_audit_events` apply. − The duplicate check is check-then-insert: two concurrent requests can both pass until a partial unique index is added (P-014). − Resolution is a conditional update, so a race between two admins yields a 409 for the loser, not a double resolution.
- **Source:** [day log](2026-10/W3/2026-10-15.md) · REQ-005 (M2/T5, T14 review)

## D-006 — The `member` role is resolved in code, and last-admin counts internal users only
- **Date:** 2026-10-15 · **Status:** Accepted
- **Context:** M1 found that editing the code-resolved `member` role did not change stored rows, and M2 found that counting external users let the last-admin guard pass while nobody could administer.
- **Decision:** The `member` role's effective permissions come from `effective-permissions.ts` in code, not from `role_permissions`; the role audit diff records the resulting grants, not the stored rows. The last-admin count (`countActiveByRoleIds` and its excluding variant) counts active internal users only, because external users cannot use permission-guarded routes.
- **Alternatives:** store `member` permissions in the DB — a migration for a role that is code-defined by design; count all active users — the guard would allow a change that leaves no operational admin.
- **Consequences:** + Audit diffs describe what really changes. − Changing `member` needs a code change and a deploy, not an admin action. − The bulk and role-write window is not transactional, so two concurrent demotions can still race past the count (P-011).
- **Source:** [day log](2026-10/W3/2026-10-15.md) · REQ-005 (M1 s6, M2 s8)
