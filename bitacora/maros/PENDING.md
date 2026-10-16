# maros — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is deployed (agents never touch the shared DB) · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T3
  Until applied, role changes still work (events are only logged, D-001) but `GET /roles/audit` returns 500.
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T5
  Until applied, creating or listing access requests (`/access-requests`) fails because the `access_requests` table is missing (notifications already fail gracefully with error logging).
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so every MCP write is attributable (R10) · urgency: med · complexity: M · added 2026-10-14 · REQ-005/T3 → T8
  D-001 made the audit best-effort; a failed insert today leaves only an error log line with the event.
- P-014 · Prevent duplicate pending access requests for the same user and permission (backend 409 + show it in NoAccessState; today a reload re-shows the form and each send adds a row) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A5)
- P-015 · Add a server-side test for settings/users and settings/roles gating (null user → dashboard, missing users:read → NoAccessState) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A7)
- P-013 · Apply the explanatory no-access state (`NoAccessState`) to the other permission-guarded pages (finance, tasks, notes…) that still redirect to /dashboard · urgency: low · complexity: M · added 2026-10-15 · REQ-005/T12

## Blocked
_None_

## Recently closed
_None_
