# lotm — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._
Last confirmed with owner: not yet confirmed.

## Current state
The split source lives in private local repos `~/dev/lotm-frontend` and `~/dev/lotm-backend`. Backend commit `95e9c786a0053a5f30d478c391f7fa627c805c09` is deployed on AdvIn and all three Compose services are healthy; the external `lotm_lotm_data` volume and Caddy route remain intact. Vercel project `lotm-frontend` has a READY production deployment at `https://lotm-frontend.vercel.app`; `/`, `/cartas`, game/card APIs, and MCP initialize/tools-list pass. `lotm.marosconstruction.com` remains on its old A record because NS1 needs a browser login. GitHub pushes are blocked until the CLI OAuth token gains `workflow` scope; the original webhook is retained until Actions deploy verification.

## Active focus
- Complete GitHub and NS1 access gates, activate both repository deployment paths, cut over DNS, verify same-host routes/TLS, then remove the old Caddy hostname and stale webhook.

## Top pending (see PENDING.md)
- P-001 · GitHub `workflow` scope and repo pushes
- P-002 · NS1 sign-in and Vercel CNAME cutover

## Recent decisions (see DECISIONS.md)
- D-001 · Keep the public hostname and MCP path; Vercel serves the migrated game/Card Studio UI and proxies backend paths to AdvIn.

## Known issues
- `npm audit --omit=dev` reports 9 production dependency findings (5 high, 4 moderate); compatible fixes for the remaining Prisma/Next tree require major-version changes and were not applied.
- Vercel Preview uses `.invalid` backend origins until isolated staging exists. Legacy `/admin`, `/coleccion`, and `/logros` routes continue through Vercel's fallback to the AdvIn app during incremental UI migration.

_Last updated: 2026-10-13_
