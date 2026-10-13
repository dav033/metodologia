# proposal-studio — Tools & infrastructure

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

### vercel
- **Type:** Hosting · **Account:** `dav033`
- **Access:** `vercel` CLI already authenticated; existing Firefox session available for dashboard.
- **Status:** Project `proposal-studio` in `dav033s-projects`, production alias `proposal-studio-orpin.vercel.app`; latest deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4` is Ready. Platform SSO protection is disabled for public proposal links; app-level admin routes remain protected by Better Auth and sensitive operations use Postgres-backed rate limits.
- **Commands:** `vercel project ls` · `vercel ls` · `vercel inspect <deployment-url> --logs`.
- **Deploy:** `vercel deploy --prod --yes --scope dav033s-projects` after local verification. Migrate production with `vercel env run --environment production -- npm run db:migrate`.
- **Notes:** Use a free plan and the generated `vercel.app` subdomain until a custom domain exists.
- **Proposal Studio MCP:** `https://proposal-studio-orpin.vercel.app/api/mcp` (Streamable HTTP). Production secret env var: `PROPOSAL_MCP_TOKEN`; on this machine the value is in `~/.config/proposal-studio/mcp-token` (mode 600). Claude Code and Codex use `/home/david/.local/bin/proposal-studio-mcp-headers`; never copy the value into client config, logs, or bitácora. Rotate by replacing the Vercel Production secret, deploying, then replacing the local token file (mode 600); reconnect Claude and let Codex refresh after a 401.
- **MCP operations:** proposal list/read/create/update/duplicate/archive/publish; private PNG capture read/upload; connected GitHub status/repository/ref/import/disconnect; temporary share link list/create/revoke. Archive, publish, share creation/revocation and GitHub disconnect require `confirm=true`; Codex prompts for writes. Shared per-minute limits use existing Postgres buckets: overall requests 120, captures 3, GitHub reads 30, GitHub imports/disconnect 3, shares 10. GitHub App installation still uses the browser OAuth callback in the admin UI. Email is excluded.
- **Local migration config:** `.env.production.local` is git-ignored and mode 600; it was used for the production migration because `vercel env run` refused to pull Secret values. Do not copy or print its contents; it includes production database configuration.
- **Local development:** `.env.development.local` is git-ignored and mode 600. By David's explicit instruction it uses the production `DATABASE_URL` with `BETTER_AUTH_URL=http://localhost:4321`; do not run migrations from local development. Local Google OAuth is configured through a separate `Proposal Studio Local` web client with callback `http://localhost:4321/api/auth/callback/google`; its credentials live only in `.env.development.local`. The local app uses the production database as requested; do not run local migrations.

## CLIs & services

### github
- **Access:** `gh` CLI already authenticated as `dav033`; HTTPS Git operations.
- **Workspace repository:** [dav033/proposal-studio](https://github.com/dav033/proposal-studio), private; local workspace `~/dev/proposal-studio`; remote `origin`; default/tracking branch `feat/proposal-comparison`. Latest source commit: `7ed2d7c` (`fix(admin): keep proposal action on one line`).
- **Status:** GitHub App `Creative Tech Proposal Studio` (`creative-tech-proposal-studio`, app ID `5268438`) is installed for `dav033` and restricted to `dav033/maros-construction-web`. App permissions are repository metadata and contents read-only; production callback and repository listing were verified. The production importer successfully previewed fixture `proposal-studio-import-demo` from branch `proposal-studio/p008-import-smoke` at `cb10529f6642a980f967e13d3cc0d7f160158508`; that QA draft was archived. The default branch still has no built static output folder with `index.html`.
- **Commands:** `gh auth status` · `gh repo list dav033` · `gh api`.

### google-cloud
- **Access:** Existing authenticated Firefox profile is available on the real Hyprland desktop; Google Cloud Console can be opened there. Do not create a separate browser profile.
- **Status:** Dedicated project `proposal-studio-511223` has an External/Testing OAuth consent screen and one owner tester. The production web client remains unchanged and has the production callback/origin. Production auth secrets are configured in Vercel; owner login verified at `https://proposal-studio-orpin.vercel.app`. Local development uses its own OAuth client and callback, stored in the ignored local env file. Vercel CLI does not expose Secret values to local pulls.

### email
- **Provider:** Resend.
- **Status:** Production `RESEND_API_KEY` is configured as a Vercel Production secret with Sending access. Admin settings save `Proposal Studio <onboarding@resend.dev>` as a test-only sender; an owner-only test email succeeded. Global notifications remain disabled. The test sender is restricted in the application to the owner and cannot enable prospect notifications; a verified sender domain is still required. Do not send real prospect mail during setup.

## Storage & data

### neon-postgres
- **Provider:** Neon through Vercel Marketplace.
- **Status:** Free-tier resource `proposal-studio-db` is connected to Vercel in `iad1`; production migrations applied successfully.
- **Secrets:** Vercel injects `DATABASE_URL`/provider environment variables; never record values here.

### vercel-blob
- **Provider:** Vercel Blob, private access.
- **Status:** Private store `proposal-studio-media` is connected to the Vercel project in `iad1`. Object reads pass through app authorization.
- **Secrets:** `BLOB_READ_WRITE_TOKEN` remains in Vercel environment settings, never in files or logs.
