# maros — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-016 · GitHub Actions is blocked by an account billing lock, so the API deploy workflow does not start; fix billing, and until then deploy by SSH with `ssh advin /usr/local/sbin/gh-deploy-maros-nest <full sha>` (same script as CI, rolls back on failed health check) · urgency: high · complexity: S · added 2026-11-07 · REQ-none
  Run 42399392978 failed with "account is locked due to a billing issue". Manual deploys done: `f0a2155` and `a82d96f` (health 200). Rollback image: `maros-stack-api:previous`.
- P-017 · Enable Gmail API and Drive API in Google Cloud project `maros-423220`, add the `gmail.compose` and `drive.file` scopes to the consent screen, then have the acting person reconnect Google in Maros · urgency: high · complexity: S · added 2026-11-07 · D-007
  The console did not render (laptop network at 1.1-1.9 s RTT with packet loss), so this was not done. Until then the three Google tools return `google_reconnect_required`.
- P-018 · Live acceptance of `create_draft_with_attachment`, `save_report_to_drive`, `save_invoice_to_receipts` after P-017, and refresh the Maros connector in Claude web so it lists the new tools (`search_invoices` already deployed) · urgency: med · complexity: S · added 2026-11-07 · D-007
- P-019 · `invoice-scans.service.ts` is 1062 lines; split by responsibility (list/get, create/attach, QBO suggestions, entry to QuickBooks) · urgency: low · complexity: M · added 2026-11-07 · file guard
- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is deployed (agents never touch the shared DB) · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T3
  Until applied, role changes still work (events are only logged, D-001) but `GET /roles/audit` returns 500.
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T5
  Until applied, creating or listing access requests (`/access-requests`) fails because the `access_requests` table is missing (notifications already fail gracefully with error logging).
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so every MCP write is attributable (R10) · urgency: med · complexity: M · added 2026-10-14 · REQ-005/T3 → T8
  D-001 made the audit best-effort; a failed insert today leaves only an error log line with the event.
- P-014 · Make the duplicate-pending check race-safe for access requests: the backend already refuses a second pending request (409 `ACCESS_REQUEST_ALREADY_PENDING`), but it is check-then-insert with no unique index in `db/add-access-requests.sql`; add a partial unique index and show the 409 in NoAccessState (a reload still re-shows the form) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A5)
- P-015 · Add a server-side test for settings/users and settings/roles gating (null user → dashboard, missing users:read → NoAccessState) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A7)
- P-013 · Apply the explanatory no-access state (`NoAccessState`) to the other permission-guarded pages (finance, tasks, notes…) that still redirect to /dashboard · urgency: low · complexity: M · added 2026-10-15 · REQ-005/T12

## Blocked
_None_

## Recently closed
_None_
