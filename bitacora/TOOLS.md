# Shared (all projects) — Tools & infrastructure

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

_None registered yet._

## CLIs & services

### Cloudflare CLI (`cf`)
- **Type:** Cloudflare API and Workers CLI · **Status:** beta (`1.0.0-beta.14`)
- **Access:** Global npm install under fnm Node.js 24.21.0; commands: `cf` and `cloudflare`. Requires Node.js 22.18+.
- **Authentication:** Not logged in yet; start with `cf auth login` and check with `cf auth whoami`.
- **Status:** `cf --version` · `cf auth whoami`
- **Notes:** `cf` can manage Cloudflare resources and Workers projects. Existing Wrangler projects keep using Wrangler unless migrated with `cf migrate`. `cf` is beta and its commands/configuration may change.

## Storage & data

_None registered yet._
