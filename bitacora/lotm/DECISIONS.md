# lotm — Decision log

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

## D-001 — Vercel public ingress with AdvIn backend
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** LOTM's game and Card Studio are Next.js applications that combine UI and backend behavior; the requested frontend/backend split needs to keep paths, MCP clients, and persistent data working through migration.
- **Decision:** Keep `lotm.marosconstruction.com` as the public URL on Vercel; deploy UI to `dav033/lotm-frontend`, APIs/data/MCP to `dav033/lotm-backend` on AdvIn, and use a temporary Vercel fallback to the AdvIn SSLIP origin for UI paths not migrated yet.
- **Alternatives:** Keep AdvIn as public ingress (would not move the hostname to Vercel); switch all paths at once (would break pages and Server Actions not yet extracted).
- **Consequences:** Vercel external proxy requests have a 120-second maximum; MCP streaming and exports need direct verification. The current unauthenticated MCP connector stays compatible until all clients are updated. Rollback is the prior DNS record plus Caddy route.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · REQ-001
