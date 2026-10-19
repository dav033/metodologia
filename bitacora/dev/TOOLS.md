# dev — Tools & infrastructure

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

### bitacora-web (local user service)
- **Type:** systemd user service, enabled on `default.target` (starts at user login; no root or linger required).
- **Unit:** `/home/david/.config/systemd/user/bitacora-web.service`.
- **Runs:** `/usr/bin/python /home/david/dev/metodologia/skill/scripts/bitacora.py serve --port 8765`, with `BITACORA_ROOT=/home/david/bitacora`; restart on failure after 3 seconds.
- **URL:** http://127.0.0.1:8765/plans (loopback only).
- **Status/logs:** `systemctl --user status bitacora-web.service`; `journalctl --user -u bitacora-web.service`.
- **Reload code:** `systemctl --user restart bitacora-web.service` when authorized. Disable auto-start with `systemctl --user disable --now bitacora-web.service`.
- **Verified:** 2026-10-18, enabled/active/running, one listener on port 8765, GET /plans HTTP 200. Replaced the previous manual server at the owner's request.

## Storage & data

_None registered yet._

### advin-bitacora-tunnel (local user service)
- Reverse SSH tunnel: advin `127.0.0.1:8765` -> this machine's bitácora panel `127.0.0.1:8765`. Unit: `~/.config/systemd/user/advin-bitacora-tunnel.service` (sibling of `advin-ssh-tunnel`, port 2222).
- View from another machine: `ssh -N -L 8765:127.0.0.1:8765 advin`. The panel has no login.
