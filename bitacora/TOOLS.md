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

### advin (VPS)
- **Type:** VPS · **Access:** `ssh advin` (alias also `advin-kind-cat`, in `~/.ssh/config`; key `~/.ssh/id_ed25519_advin`), user `root`
- **Status:** verified reachable 2026-10-19 · **Authority:** agents may deploy and restart here on their own (owner decision 2026-10-19)
- **Notes:** before a risky change (migration, config edit) take a backup or note the current version to roll back to

### marketplace (AWS EC2)
- **Type:** EC2 instance · **Access:** `ssh marketplace` (key `~/.ssh/marketplace-eventos`), user `ec2-user`
- **Status:** verified reachable 2026-10-19 · **Authority:** as above

## CLIs & services

_Agents run without permission prompts and may ship to production with these on their own (owner decision
2026-10-19, `DECISIONS.md` of metodologia). Check the output, verify the deploy afterwards, and say what was done._

### github (`gh`)
- **Access:** `gh`, logged in as `dav033` (scopes `repo`, `workflow`, `read:org`, `gist`); orgs `davTHer`, `Sempertex-de-Colombia`
- **Use:** `git push`, PRs (`gh pr create/merge`), Actions (`gh run list/view --log`), releases. Several repos deploy automatically from `main`.

### vercel
- **Access:** `vercel` CLI, logged in as `dav033`; link a repo with `vercel link`
- **Use:** `vercel ls` · `vercel inspect <url> --logs` · `vercel --prod` · `vercel env ls` (never print values)

### netlify
- **Access:** `netlify` CLI, logged in (team "dav033's team"); `netlify link` in the repo
- **Use:** `netlify status` · `netlify deploy` (draft) · `netlify deploy --prod` · `netlify logs`

### ssh
- Hosts above (`advin`, `marketplace`); non-interactive: `ssh -o BatchMode=yes <alias> '<command>'`

## Storage & data

_None registered yet._
