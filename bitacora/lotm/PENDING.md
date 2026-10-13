# lotm — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-NNN · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`.
Move items between sections as they change; closed items keep 14 days in "Recently closed", then go to the
month summary._

## Open
- P-001 · Approve GitHub CLI `workflow` scope and push the frontend/backend repos · urgency: high · complexity: M · added 2026-10-13 · REQ-001
  Backend and frontend local commits are ready; GitHub rejected both pushes because the CLI OAuth token lacks `workflow`. Then verify Vercel Git deployment and the backend Actions deploy.
- P-002 · Sign in to NS1 in the agent Firefox session and cut over the LOTM DNS record · urgency: high · complexity: M · added 2026-10-13 · REQ-001
  Vercel recommends a CNAME for `lotm` to `88811a8d305d8f0a.vercel-dns-017.com.`. Keep the current A record and Caddy alias until the domain verifies and same-host routes pass.

## Blocked
_None_

## Recently closed
_None_
