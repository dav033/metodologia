# maros — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is deployed (agents never touch the shared DB) · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T3
  Until applied, role changes still work (events are only logged, D-001) but `GET /roles/audit` returns 500.
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so every MCP write is attributable (R10) · urgency: med · complexity: M · added 2026-10-14 · REQ-005/T3 → T8
  D-001 made the audit best-effort; a failed insert today leaves only an error log line with the event.
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T5
  Until applied, creating or listing access requests (`/access-requests`) fails because the `access_requests` table is missing (notifications already fail gracefully with error logging).

## Blocked
_None_

## Recently closed
_None_
