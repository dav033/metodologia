# maros — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-023 · Luis must reconnect Google AGAIN (new read scopes `gmail.readonly` + `drive.readonly`): log into Maros, open /calendar and press the new "Reconnect Google" button (shown only to llozano@), approve; then verify the token scopes and run live tests of `search_drive_files`, `import_gmail_invoices_to_receipts` and any-Drive-file attachments · urgency: high · complexity: S · added 2026-11-08 · REQ-006 T4/T5
- P-024 · REQ-006 T6 (invoice index with Drive link, location state and history): owner approved a migration; agents do not touch the shared DB, so write `db/add-invoice-drive-locations.sql` + code (graceful if the table is missing) and have the owner apply it · urgency: med · complexity: M · added 2026-11-08 · REQ-006
- P-025 · QuickBooks writes: owner said yes to all; T13 acceptance says For Review stays read-only. Inventory what the API can write (bills/purchases from scans, attach files to transactions, vendors), propose concrete tools, build the ones the owner confirms · urgency: med · complexity: L · added 2026-11-08 · REQ-006
- P-021 · ANSWERED 2026-11-08 (owner: "yes to everything, as maximal as possible"): T5 -> `gmail.readonly` + `import_gmail_invoices_to_receipts` built; T4 -> `drive.readonly` built; T6 -> migration approved (P-024); QuickBooks writes -> P-025; reconnect button only for llozano@ done (`856bd877` frontend). Kept as hard guardrails, because REQ-006 sets them as acceptance criteria: no email sending, no deleting/modifying existing Drive files or mail, For Review read-only. Say so explicitly to lift any of them.
- P-022 · DONE 2026-11-08 (Luis reconnected). Still open as a UX idea: a visible "Reconnect / grant Gmail & Drive" button in maros-next (the connect button is hidden once Calendar is connected).
- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is deployed (agents never touch the shared DB) · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T3
  Until applied, role changes still work (events are only logged, D-001) but `GET /roles/audit` returns 500.
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · urgency: high · complexity: S · added 2026-10-14 · REQ-005/T5
  Until applied, creating or listing access requests (`/access-requests`) fails because the `access_requests` table is missing (notifications already fail gracefully with error logging).
- P-016 · GitHub Actions is blocked by an account billing lock, so the API deploy workflow does not start; fix billing, and until then deploy by SSH with `ssh advin /usr/local/sbin/gh-deploy-maros-nest <full sha>` (same script as CI, rolls back on failed health check) · urgency: high · complexity: S · added 2026-11-07 · REQ-none
  Likely cause (inferred, billing API not readable): the owner's `pictures` repo is private and used ~163 Quality-checks runs x 4 parallel jobs in Oct 2026 (> 2,000 free min/month); the $2.84 charge reported by the owner probably is the failed payment. Public repos (`maros-nest`) do not consume minutes. Check https://github.com/settings/billing; consider a $0 spending limit and cutting `pictures` checks (push+PR double trigger).
  Run 42399392978 failed with "account is locked due to a billing issue". Manual deploys done: `f0a2155` and `a82d96f` (health 200). Rollback image: `maros-stack-api:previous`.
  2026-11-08: owner reports billing fixed, but GitHub still returned the lock on a dispatched run (42508294800). Re-test later; if it persists, retry the pending charge at github.com/settings/billing or contact GitHub Support. Manual SSH deploys continue meanwhile.
- P-017 · DONE 2026-11-08: Gmail API + Drive API enabled and scopes saved in `maros-423220`; Luis logged into Maros and reconnected; his stored token now has `gmail.compose` and `drive.file` (verified read-only in the prod container).
- P-020 · pictures: purge of `scripts/test/` from all history is rewritten locally and being force-pushed (atomic, 42 branches + 1 tag, main tree identical before/after); VERIFY the push result, then realign local clones/worktrees (`~/dev/pictures`, `~/dev/pictures-wt/*`, the dirty WIP branch `feat/req-014-…`, and the VPS clone used by the deploy workflow) · urgency: high · complexity: M · added 2026-11-07 · owner request
  2026-11-08: the staged push was relaunched detached after the session restart (`/home/david/backups/push3.log`).
  First force-push FAILED (HTTP 408 on ~500 MB upload); being atomic it changed nothing on GitHub (main still `516de642`). Retrying with `/home/david/backups/push-staged.sh` (incremental pushes to a temp branch `zz-purge-stage`, then atomic push of all branches, then delete the temp branch); log `/home/david/backups/push2.log`. If it ends with `exit=0`, confirm `git ls-remote` equals the rewritten refs and that `zz-purge-stage` is gone.
  Backup (verified, 708 MB, 2,404 refs): `/home/david/backups/pictures-dotgit-20261107` (the first mirror-clone backup failed on a network timeout; do not trust `pictures-mirror-*`). Work repo: `/home/david/backups/pictures-purge-work.git`; push log `/home/david/backups/push.log`. 2707 -> 2624 commits; gitleaks hits 1404 -> 985 (rest are other files: snapshots/data). Old commits stay reachable by SHA on GitHub until its GC; rotate any real key from those tests regardless. Repo is still PRIVATE.
- P-018 · Live acceptance DONE 2026-11-08 (see day log). REMAINING: refresh the Maros connector in Claude web so it lists the new tools (`search_invoices`, `create_draft_with_attachment`, `save_report_to_drive`, `save_invoice_to_receipts`) and run one end-to-end request from Claude · urgency: med · complexity: S · added 2026-11-07 · D-007
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so every MCP write is attributable (R10) · urgency: med · complexity: M · added 2026-10-14 · REQ-005/T3 → T8
  D-001 made the audit best-effort; a failed insert today leaves only an error log line with the event.
- P-014 · Make the duplicate-pending check race-safe for access requests: the backend already refuses a second pending request (409 `ACCESS_REQUEST_ALREADY_PENDING`), but it is check-then-insert with no unique index in `db/add-access-requests.sql`; add a partial unique index and show the 409 in NoAccessState (a reload still re-shows the form) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A5)
- P-015 · Add a server-side test for settings/users and settings/roles gating (null user → dashboard, missing users:read → NoAccessState) · urgency: low · complexity: S · added 2026-10-15 · REQ-005/T12 (antagonist A7)
- P-013 · Apply the explanatory no-access state (`NoAccessState`) to the other permission-guarded pages (finance, tasks, notes…) that still redirect to /dashboard · urgency: low · complexity: M · added 2026-10-15 · REQ-005/T12
- P-019 · `invoice-scans.service.ts` is 1062 lines; split by responsibility (list/get, create/attach, QBO suggestions, entry to QuickBooks) · urgency: low · complexity: M · added 2026-11-07 · file guard

## Blocked
_None_

## Recently closed
_None_
