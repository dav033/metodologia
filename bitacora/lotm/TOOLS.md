# lotm — Tools & infrastructure

_How to reach everything this project runs on or depends on: servers, hosting, CLIs, storage, databases,
external services. The agent reads this before any "check the deploy / connect to X / do Y on Z" request._

**Never write secrets here** (the bitácora is versioned with git). Reference them instead: the path to a key file,
an `~/.ssh/config` host alias, an env var name, a password-manager entry, or "CLI already logged in".

<!-- One `###` block per environment / tool. Example:

### vps-prod
- **Type:** VPS (Ubuntu 22.04) · **Provider:** Hetzner
- **Access:** `ssh advin-vps` (alias in ~/.ssh/config, key `~/.ssh/advin-vps`) · user `deploy`
- **What runs here:** API (docker compose in `/srv/app`), Postgres 16, nginx
- **Status / logs:** `docker compose -f /srv/app/docker-compose.yml ps` · `docker compose logs -f api --tail 200`
- **Deploy:** `cd /srv/app && git pull && docker compose up -d --build`
- **Notes:** backups nightly at 03:00 to S3 bucket `x-backups`

### vercel
- **Type:** Hosting (frontend) · **Project:** `my-app` (team `acme`)
- **Access:** `vercel` CLI, already logged in; link with `vercel link --project my-app`
- **Status / logs:** `vercel ls my-app` · `vercel inspect <url> --logs`
- **Deploy:** push to `main` (auto) · manual: `vercel --prod`
-->

## Environments

### AdvIn production
- **Type:** Linux VPS · public IP `185.147.157.25`
- **Access:** `ssh advin` (root; alias in `~/.ssh/config`). CI deploy uses the restricted `lotm-deploy` account and repository secret `ADVIN_DEPLOY_KEY`.
- **What runs here:** Game API/domain/Prisma, Card Studio API/SQLite, MCP, Caddy, Docker Compose. The external volume is `lotm_lotm_data`; the public route is still enabled in Caddy for rollback.
- **Status / logs:** `ssh advin 'docker compose -p lotm -f /opt/deployments/lotm/current/ops/compose.vps.yml ps'` · `ssh advin 'docker logs --tail 100 lotm-app'`
- **Deploy:** GitHub Actions in `dav033/lotm-backend` should deploy the checked `main` commit after CI. Active release is `95e9c786a0053a5f30d478c391f7fa627c805c09`; local repo HEAD is `a490495` with tooling/worklog follow-ups. Repository push and Action verification are pending GitHub OAuth `workflow` scope.
- **Rollback:** Previous release/image tags are retained. See `lotm-backend/ops/DEPLOYMENT.md` and root-only backup `/opt/backups/lotm/pre-split-20261013/`.

### Vercel
- **Type:** Frontend hosting · **Project:** `lotm-frontend` · team `dav033s-projects` · root `apps/site` · Node `24.x`.
- **Access:** `vercel` CLI, logged in as `dav033`.
- **Status / logs:** `vercel project inspect lotm-frontend --scope dav033s-projects` · `vercel logs --project lotm-frontend --since 1h`.
- **Deploy:** GitHub integration on `dav033/lotm-frontend` main; bootstrap production deployment is `https://lotm-frontend.vercel.app` and is `READY`.
- **Domain:** `lotm.marosconstruction.com` is attached but DNS still points to AdvIn. NS1 should set CNAME `lotm` → `88811a8d305d8f0a.vercel-dns-017.com.`; verify with `vercel domains verify lotm.marosconstruction.com --scope dav033s-projects`.
- **Environment variable names:** `LOTM_BACKEND_ORIGIN`, `LOTM_CARDS_ORIGIN`, `LOTM_MCP_ORIGIN`; production targets the AdvIn SSLIP HTTPS origin. Preview targets a reserved `.invalid` origin until staging exists.

### GitHub and DNS
- **GitHub:** Private repos `dav033/lotm-frontend` and `dav033/lotm-backend`; local commits are ready but pushes need the authenticated CLI token to gain `workflow` scope. Do not change `dav033/lotm-workspace` main.
- **Stale webhook:** `dav033/lotm-workspace`, hook `660396468`, sends `push` to `/deploy/github` (404); remove after the new backend Actions deploy succeeds.
- **DNS provider:** IBM NS1 at `https://my.nsone.net/`; agent Firefox clone currently needs David's login. Keep the current A record and old Caddy alias until Vercel verifies the CNAME and route checks pass.

### MCP
- **Public endpoint:** `https://lotm.marosconstruction.com/mcp`; Vercel rewrites it to AdvIn. `initialize` and `tools/list` were verified through both Vercel and the current public hostname (15 tools).
- **Project client:** root `opencode.json` now uses the public endpoint. `.mcp.json` uses local Card Studio stdio and remains unchanged.

## CLIs & services

GitHub CLI is authenticated as `dav033` with `repo`, `gist`, and `read:org`; an OAuth refresh for the `workflow` scope is required to push workflow files.

## Storage & data

The persistent Card Studio store is the external Docker volume `lotm_lotm_data`. The pre-split backup is root-only on AdvIn at `/opt/backups/lotm/pre-split-20261013/`; its checksum and SQLite integrity checks passed before deployment.
