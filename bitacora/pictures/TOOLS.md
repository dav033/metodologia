# pictures — Tools & infrastructure

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

_None registered yet._

## Storage & data

_None registered yet._

### advin-vps (production VPS)
- **Type:** VPS (8 vCPU AMD EPYC, 15 GB RAM, no GPU) · **Access:** `ssh advin` (alias in ~/.ssh/config, host 185.147.157.25, key id_ed25519_advin; `advin-vps` does NOT resolve)
- **What runs here:** Docker: demo-decoracion (Next, env /etc/demo-decoracion/demo.env) + demo-decoracion-ai-api (Python,
  /etc/demo-decoracion-ai/ai.env), other projects (maros, lotm, trainingapp, fichas-fotos); Caddy edge proxy
  (/opt/edge-proxy/Caddyfile): web https://185-147-157-25.sslip.io, ai-api https://api-decoracion.185-147-157-25.sslip.io.
- **Releases:** /opt/deployments/pictures/releases/<sha> (compose.vps.yml); recreate web only:
  `docker compose -p demo-decoracion -f <release>/compose.vps.yml up -d --no-deps --no-build web`.
- **Model trials:** removed 2026-11-02 at owner request (containers, /opt/modelos-prueba with its 4.4 GB HF cache, audio, scripts, results). Benchmark conclusions remain in 2026-10/W2/2026-10-09.md; the raw results were not kept.
- **Notes:** never restart the ai-api without owner notice; never print env files. Values containing `$` (scrypt hashes) must be single-quoted in demo.env: Compose interpolates `$` and silently truncates them.

### req021-db (REQ-021 test Postgres)
- **Type:** Postgres 16 + pgvector/pg_trgm/unaccent in Docker on the advin VPS (`/opt/req021-db`, container `req021-db`, volume `req021-db-data`, 1 GB memory limit) · created 2026-10-26 for REQ-021's automated and local tests; meant to be replaced by a Supabase later. Not production data.
- **Access:** bound to `127.0.0.1:5433` on the VPS only; locally through the user unit `pictures-req021-db-tunnel.service` (`ssh -L 127.0.0.1:55433:127.0.0.1:5433 advin`). Connection URL: env var `PICTURES_REQ021_DATABASE_URL` in `~/.config/flow/secrets.env` (mode 600). Never print it.
- **Notes:** separate from the host Postgres on 5432 and from every other container; the migrations in `scripts/migrations/` have not been applied yet (empty database with the three extensions).

### Single database and pool curator (D-091, 2026-11-02)
- **DB:** container `req021-db` (pg16 + pgvector), database `pictures`; roles `pictures_owner` (DDL/tests), `pictures_app` (app + ai-api DML), `pictures_curator` (pool_* DML + own schema `curador`). Secrets: VPS `/root/secrets/pictures-db.env`, local `~/.config/metodologia/pictures-db.env` (600). Local access via the user service `pictures-req021-db-tunnel` (127.0.0.1:55433). Daily dump + nonce purge: `/usr/local/sbin/pictures-db-backup` (cron 08:17 UTC, 14 kept, `/root/backups/pictures/daily`).
- **Gateway:** `/opt/pictures-db-gateway` (container `pictures-db-gateway`, wsproxy, only `req021-db:5432`), Caddy `api-decoracion…/db/v1` with header `X-Db-Gateway-Key`; Vercel uses it through `DB_GATEWAY_URL`/`DB_GATEWAY_KEY`.
- **Curator:** https://curador.185-147-157-25.sslip.io (Caddy basic auth, user `david`, password `CURATOR_WEB_PASSWORD` in the VPS secrets file); `/opt/pictures-curador/current` → releases/<sha>, compose project `pictures-curador`, env `/etc/pictures-curador/curador.env`, re-embeds edited items (cap CURATOR_EMBED_MAX_USD=1). Deploy: `git archive HEAD` → releases/<sha>, `docker compose -p pictures-curador -f compose.vps.yml up -d --build`.

### Reference images read token (2026-11-04)
- `REFERENCIAS_DECORACIONES_TOKEN` in Vercel production and in `~/.config/metodologia/pictures-referencias.env` (600). Read-only; usage in `docs/referencias-decoraciones.md`.

### whatsapp-webhook (Meta webhook receiver, 2026-11-09)
- **What:** container `pictures-whatsapp-webhook` (node:24-alpine, no deps, 96 MB) on the advin VPS, dir `/opt/pictures-whatsapp-webhook` (compose + `.env` mode 600 + `app/`), network `stack_web`. Caddy block `whatsapp.185-147-157-25.sslip.io` → `/webhook` only (1 MB cap, rest 404); Caddyfile backup `/opt/edge-proxy/Caddyfile.bak.20261109T154603Z-whatsapp`.
- **Meta callback URL:** `https://whatsapp.185-147-157-25.sslip.io/webhook`; verify token = `META_VERIFY_TOKEN` (never written here; `~/.config/metodologia/pictures-meta.env`).
- **Deploy:** `services/whatsapp-webhook/deploy.sh advin`. **App secret:** add `META_APP_SECRET` to the VPS `.env` and recreate the container.
- The Vercel route `/api/whatsapp/webhook` still exists (owner asked not to link Meta to Vercel); remove it if unwanted.

### pictures-conteo (automatic balloon count, REQ-026)
- **Type:** CPU detector service on the advin VPS, container `pictures-conteo`, compose in `/opt/pictures-conteo`, weights in `/opt/pictures-conteo/modelo`, network `stack_web`. Since 2026-11-09 (D-108) image `pictures-conteo:2` with CountGD (weights `/opt/pictures-conteo/modelo/countgd/`, cpus 6, mem 6g, ~15-20 s/photo); rollback `compose.yml.bak-1-20261110T031805` (image :1). Image built on the VPS from `/opt/pictures-conteo/build` (`Dockerfile.countgd`).
- **Access:** Caddy route `https://api-decoracion.185-147-157-25.sslip.io/conteo/*`; `/contar` needs header `x-conteo-token`. Token: `/opt/pictures-conteo/.env` on the VPS, `~/.config/metodologia/pictures-conteo-prod.env` locally. Vercel: `CONTADOR_FOTO_YOLO_URL`, `CONTADOR_FOTO_YOLO_TOKEN`.
- **Rollback:** remove `CONTADOR_FOTO_YOLO_URL` from Vercel and redeploy: the Contador returns to the Python count with colours. Caddy backup: `/opt/edge-proxy/Caddyfile.bak.20261109T211929Z-conteo`.
