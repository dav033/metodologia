# eventos — Tools & infrastructure

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

**Agents treat production as read-only.** Explicit user permission is required to: deploy or restart IIS, PM2, Node or
the database; run migrations, write SQL or restores; change configuration, env vars, certificates or secrets.

### local
- **Type:** Developer machine · repos `C:/Users/davidt/Desktop/eventos/FrontSempertexEventos` and `.../ViveSempertexEventos`
- **Access:** run each command from the repo root; needs env vars and network access to MSSQL `zeus:1433`
- **What runs here:** frontend `npm run dev` (Next default dev port; PM2 config targets `http://localhost:4021`) · API `npm run dev` (`http://localhost:4022`) · optional Compose PostgreSQL on 5434 (not used by the API)
- **Status / logs:** process console (Nest logs TypeORM errors/warnings and requests > 1 s)
- **Deploy:** n/a
- **Notes:** `.env*` git-ignored, no `.env.example`; variable names are in `package.json`, `auth.config.ts`, `app.module.ts`, `jwks.config.ts`, `sharepointStorage.service.ts`. Tests: `npm test` (+ backend `npm run test:e2e`), `npm run lint`, frontend `npm run typecheck`.

### staging
- **Type:** unknown (see P-005) · **Provider:** unknown (see P-005)
- **Access:** unknown (see P-005)
- **What runs here:** unknown (see P-005)
- **Status / logs:** unknown (see P-005); only Nest/PM2 process logs are visible in code
- **Deploy:** no CI/CD or staging script declared (see P-005)
- **Notes:** secrets manager/location undocumented (see P-001)

### production (Windows/IIS server)
- **Type:** Windows server with IIS (URL Rewrite/ARR) as reverse proxy to loopback · **Provider:** unknown (see P-005)
- **Access:** unknown, read-only access not documented (see P-005)
- **What runs here:** frontend Next.js under PM2 (`ecosystem.config.js`: one instance, `fork` mode, port 4021, daily restart 23:59, 1000 MB memory limit, extra CA certificate — GoDaddy bundle per commit history) · API NestJS on port 4022 behind IIS (`web.config`), no PM2/process manager declared
- **Status / logs:** no monitoring, alerts or log path found in the repos; no health/readiness endpoint (`GET /` returns `Hello World` behind the global guard). PM2/IIS/Windows log paths unknown (see P-005). Monitoring outside the repos: open question.
- **Deploy:** frontend `npm run deploy` (= `next build` + `pm2 startOrRestart ecosystem.config.js`) · backend `npm run build` then `npm run start:prod` (`node dist/main`); who runs it and how is undocumented (see P-005)
- **Notes:** backend `web.config` mentions `asistenciab.sempertex.com`; frontend domain unknown (see P-006). TLS termination and security headers undocumented (see P-006). Request filtering allows 50 MB. Rollback: unknown (see P-005). Secrets: process/server env or an unidentified manager (see P-001).

## CLIs & services

### microsoft-entra-id
- **Type:** Identity provider (OIDC) · **Provider:** Microsoft
- **Access:** NextAuth in the frontend (`src/app/api/auth/[...nextauth]/auth.config.ts`); scopes of the API + `User.Read`; credentials from env (names in that file)
- **Notes:** API validates RS256 JWT via JWKS (`src/auth/jwks.config.ts`, `jwks.service.ts`); issuer accepted by prefix, tenant matrix undocumented (see P-006)

### face-verification-service
- **Type:** External HTTP service (`identity.sempertex.com` per the code)
- **Access:** URL and API key from env (`x-api-key` header); called by `src/asistente/face-verification.utils.ts` and Next route `src/app/api/face-verification/route.ts`
- **Notes:** synchronous, 20 s timeout, no queue/retry; depends on network and certificates

## Storage & data

### mssql-zeus
- **Type:** Microsoft SQL Server (version not declared) · host `zeus`, port 1433, schema `GESTION_HUMANA.dbo`
- **Access:** database name, user and password from env (`app.module.ts`); `trustServerCertificate:true`
- **What runs here:** all app data (events, attendees, authorization, read-only `EMPLEADO_SFSF` view)
- **Deploy:** schema changes are manual SQL outside the build (`db/2026-09-verificacion-encuesta-evidencias.sql`); no migrations (see P-003). Writes need explicit permission.
- **Notes:** backup, query access and restore procedure undocumented (see P-005); shared DB, owner of schema changes unknown (see P-003)

### sharepoint (Microsoft Graph)
- **Type:** Microsoft SharePoint via Graph SDK (client credentials)
- **Access:** `AZURE_*` / `SHAREPOINT_*` env vars (`src/azure/sharepointStorage.service.ts`)
- **What runs here:** signatures, pending-verification photos, event evidence, PDF reports (folders per event)
- **Notes:** retention/backup undocumented (see P-004, P-009); deleting SQL rows does not delete files

### compose-postgres (local only)
- **Type:** Docker Compose, PostgreSQL `latest`, host port 5434, one named volume (`ViveSempertexEventos/docker-compose.yml`)
- **Notes:** not connected to the API (see P-002); file contains plaintext DB credentials — do not copy (see P-001)

### uploads (local filesystem)
- **Type:** `uploads` directory relative to the backend build
- **Notes:** Excel/CSV temp files and some generated reports; no retention policy
