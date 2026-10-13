# maros — Tools & infrastructure

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

### api-production
- **Type:** VPS · **Service:** Maros Nest API
- **Access:** GitHub Actions deploy workflow; restricted SSH deploy command. Do not use or expose the deploy key.
- **Status / health:** `GET https://api.marosconstruction.com/api` · deployment workflow runs health checks and rolls back the API image on failure.
- **Deploy:** push `main` in `maros-nest`; workflow `.github/workflows/deploy.yml` deploys the exact commit SHA.
- **Last verified:** 2026-10-10 · workflow succeeded for `003ed7a091e601d58c3a2b777f1f2108361b7915`; public health endpoint returned HTTP 200.

## CLIs & services

### netlify
- **Type:** Frontend hosting · **Site:** `maros-app` (`app.marosconstruction.com`)
- **Access:** Netlify CLI, already authenticated as `dav033`; site is connected to `dav033/maros-next`.
- **Status:** `netlify sites:list --json`; deploy details: `netlify api listSiteDeploys --data '{"site_id":"63ef3d08-bcdc-4fd8-8d32-e180a5d97e05"}'`.
- **Deploy:** push `main` in `maros-next`; Netlify builds and publishes production automatically.
- **Last verified:** 2026-10-10 · deploy `6acaa0972043370008c1b743` is current/ready for `6704d72f52980e0b351b84807d4eff13d5167bc3`.

## Storage & data

_None registered yet._
