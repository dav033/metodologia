# maros — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-004 · Diagnose estimate email “service does not respond” in the live provider path · urgency: high · complexity: M · added 2026-10-10 · REQ-001 / contact chat
  - Estimate detection recognizes “Proposal”; frontend distinguishes lookup failures and keeps retries available. Tests confirm SMTP/API errors are surfaced instead of reported as successful sends. The live failure cause remains unknown without approximate send time and server/mail-provider error or correlation data; do not resend to a customer as a diagnostic.
- P-009 · Review existing production dependency advisories · urgency: high · complexity: M · added 2026-10-11 · npm audit during REQ-003
  - `npm audit --omit=dev` reports 50 findings (1 critical, 9 high, 40 moderate), including direct Next.js 16.1.3 and Axios advisories. Check reachability and available fixed versions, then plan a scoped dependency update. Do not combine unrelated upgrades with REQ-003.
- P-002 · Show project-list load failures as errors instead of an empty list · urgency: med · complexity: S · added 2026-10-10 · architecture audit
  - REQ-004 carries a retryable client error into `/projects` and completed/lost views. A failed empty SSR fallback now keeps the skeleton during the client retry; a final no-data error no longer displays the misleading “No projects found” table state, while stale rows remain visible on background refresh failure. Verify the failure/retry path in an authenticated browser before closing this item.
- P-005 · Reproduce manual transaction save report against current CRM version · urgency: med · complexity: S · added 2026-10-10 · REQ-001 / contact chat
  - Regression tests confirm a rejected create request shows an error and keeps the form open; missing payment direction is also covered. The original report still needs reproduction on the current CRM version or a captured request error. Failed optional-file uploads now leave the saved transaction retryable.
- P-007 · Verify missing payment-plan information in project details · urgency: med · complexity: S · added 2026-10-10 · 707 contact chat
  - The contact reports that information about how project payments are planned disappeared from project pages. No current-version reproduction or root cause is confirmed; inspect the affected view and preserve existing CRM data.
- P-008 · Verify invoice category and vendor association in Document Scans · urgency: med · complexity: S · added 2026-10-10 · 707 contact chat
  - The contact reports that invoice categories and vendors are not linked. The exact record and workflow are not confirmed; reproduce before changing the existing QuickBooks matching flow.

## Blocked
_None_

## Recently closed
- P-006 · DONE — Make project-linked lead 065P-0726 discoverable from Leads · urgency: high · complexity: M · added 2026-10-10 · owner request / CRM verification
  - Added a scoped `GET /leads/converted?type=...` endpoint and read-only Converted view. The existing lead and project stay linked; rows open the project, with no write actions. Backend and frontend regression tests, typecheck, and builds passed. No live CRM data was changed.
- P-001 · DONE — Confirm invoice-scan recipient access · urgency: med · complexity: M · added 2026-10-10 · owner confirmation 2026-10-10
  - Owner confirms the email recipient has permission to open invoice scans. No access change proposed.
- P-003 · CLOSED — Confirm trusted Maros subdomains for credentialed API calls · urgency: med · complexity: M · added 2026-10-10 · owner confirmation 2026-10-10
  - Owner confirms the allowed `marosconstruction.com` subdomains are trusted. The existing CORS/cookie configuration is accepted under that trust boundary; revisit if subdomain ownership or trust changes.

## Notes
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
