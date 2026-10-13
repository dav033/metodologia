# metodologia — Tools & infrastructure

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

### subscription-usage
- **Type:** hourly user-systemd metadata collector, no model sessions (D-006).
- **Access:** local user `david`; existing provider account directories selected by registered profiles. No sudo or credential refresh.
- **What runs:** `metodologia-subscription-usage.timer` starts its oneshot service, executing `python /home/david/dev/metodologia/skill/scripts/bitacora.py usage poll`.
- **Status / logs:** `python /home/david/dev/metodologia/skill/scripts/bitacora.py usage timer-status` and `usage show`; `journalctl --user -u metodologia-subscription-usage.service --since today`.
- **Control:** explicitly authorized changes use `systemctl --user stop|start metodologia-subscription-usage.timer`; disable to stop future sampling. Units live under `~/.config/systemd/user/`.
- **Notes:** latest schema-v1 snapshot and monthly metadata history are under `~/bitacora/.state/`. No secrets/raw responses. `claude-work` returned HTTP 401 on 2026-10-13; its usage is unavailable until the owner resolves its sign-in. Linux/systemd installation only; manual collector/cache routing are portable.

## Storage & data

_None registered yet._
