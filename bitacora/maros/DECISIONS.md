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
