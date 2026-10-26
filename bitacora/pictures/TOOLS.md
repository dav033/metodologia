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
- **Model trials:** /opt/modelos-prueba (compose project `modelos-prueba`, Whisper :8610 / Laya :8611 on 127.0.0.1, stopped).
- **Notes:** never restart the ai-api without owner notice; never print env files. Values containing `$` (scrypt hashes) must be single-quoted in demo.env: Compose interpolates `$` and silently truncates them.

### req021-db (REQ-021 test Postgres)
- **Type:** Postgres 16 + pgvector/pg_trgm/unaccent in Docker on the advin VPS (`/opt/req021-db`, container `req021-db`, volume `req021-db-data`, 1 GB memory limit) · created 2026-10-26 for REQ-021's automated and local tests; meant to be replaced by a Supabase later. Not production data.
- **Access:** bound to `127.0.0.1:5433` on the VPS only; locally through the user unit `pictures-req021-db-tunnel.service` (`ssh -L 127.0.0.1:55433:127.0.0.1:5433 advin`). Connection URL: env var `PICTURES_REQ021_DATABASE_URL` in `~/.config/flow/secrets.env` (mode 600). Never print it.
- **Notes:** separate from the host Postgres on 5432 and from every other container; the migrations in `scripts/migrations/` have not been applied yet (empty database with the three extensions).
