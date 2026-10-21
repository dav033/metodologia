# Go-live runbook

Kit files live in `remote/deploy/`. Each step ends with its own **Rollback**. Never write secret values in this file or in git.

## OAuth callback rule (read first)

Register the GitHub OAuth App callback as `<FLOW_FRONTEND_ORIGIN>/api/auth/callback` (the `*.vercel.app` origin the owner opens).
Do **not** register the API host: the state cookie (`SameSite=Lax`) and the session cookie (`SameSite=Strict`) are host-only
cookies of the frontend host, so an API-host callback never receives them. Vercel's same-origin `/api/*` rewrite forwards
the callback to the gateway with the browser's `Cookie` header. The browser-level check is
`cd remote/web && npm run verify` (headless Chromium, `web/tests/oauth-browser.test.mjs`); run it before step 5.

## Step 1: Prepare the host account and directories

`sudo useradd --system --home /var/lib/bitacora-gateway --shell /usr/sbin/nologin bitacora; sudo install -d -o root -g root /etc/bitacora-gateway /opt/bitacora-gateway/releases`

Rollback: `sudo rm -r /etc/bitacora-gateway /opt/bitacora-gateway` (empty at this point) and `sudo userdel bitacora`.

## Step 2: Fill the environment file

`sudo install -m 0600 -o root -g root remote/deploy/gateway.env.example /etc/bitacora-gateway/gateway.env`, then fill every uncommented key.
`FLOW_GATEWAY_KEY` must be random and at least 24 characters (`openssl rand -hex 32`); the gateway refuses shorter ones.
`FLOW_FRONTEND_ORIGIN` is the Vercel origin; `LAPTOP_ORIGIN` is `http://127.0.0.1:18765` (the reverse tunnel). Set `GATEWAY_BIND=172.20.0.1` so Docker-hosted Caddy can reach the gateway on the host bridge.

Rollback: `sudo rm /etc/bitacora-gateway/gateway.env` (keep a copy of the previous file as `gateway.env.bak` before editing an existing one and restore it).

## Step 3: Deploy the gateway release

`sudo remote/deploy/deploy.sh remote/gateway` (use `--dry-run` first). It checks required keys, installs a timestamped release,
records the previous one in `previous`, switches `current` and restarts the service.

Rollback: `sudo remote/deploy/rollback.sh` returns `current` to the previous release and restarts.

## Step 4: Install and start the systemd unit

`sudo install -m 0644 remote/deploy/bitacora-gateway.service /etc/systemd/system/; sudo systemctl daemon-reload; sudo systemctl enable --now bitacora-gateway`

Rollback: `sudo systemctl disable --now bitacora-gateway; sudo rm /etc/systemd/system/bitacora-gateway.service; sudo systemctl daemon-reload`.

## Step 5: Publish the API host through Caddy

Set `GATEWAY_API_HOST` for Caddy and add `remote/deploy/Caddyfile` as a site block in the existing `/opt/edge-proxy/Caddyfile`. Back up that file before editing. Validate and reload the Docker container, not a host systemd unit: `docker exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then `docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`. Caddy proxies to `172.20.0.1:8790` on the host; keep the gateway bound to that address as configured in step 2. Confirm every existing hostname still returns its recorded status and TLS subject after reload.
Point the Vercel `FLOW_GATEWAY_ORIGIN` at `https://<api host>` and redeploy the frontend. Register the GitHub callback per the rule above.

Rollback: restore the timestamped Caddyfile backup, validate and reload it with `docker exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` and `docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`; restore the previous Vercel `FLOW_GATEWAY_ORIGIN` and redeploy it.

## Step 6: Start the laptop listener and tunnel

Create `~/.config/bitacora/remote.env` with mode `0600` holding the same `FLOW_GATEWAY_KEY` as the gateway (`install -m 600 /dev/null ~/.config/bitacora/remote.env`, then edit; never `cat` it). Install `remote/deploy/bitacora-remote-api.service` into `~/.config/systemd/user/` and start it before the tunnel so the forward never points at a closed port; without the key the listener answers 401 to everything.
Check `stat -c %a ~/.config/bitacora/remote.env` prints `600`.

`systemctl --user enable --now bitacora-remote-api.service advin-bitacora-tunnel.service` (units in `remote/deploy/`).

Rollback: `systemctl --user disable --now advin-bitacora-tunnel.service bitacora-remote-api.service`; the gateway then reports the laptop as offline.

## Step 7: Smoke test

Open the frontend origin, sign in as the allowed GitHub account, confirm the snapshot loads and `GET /api/auth/session` returns 200.
Check `journalctl -u bitacora-gateway -n 50`.

Rollback: run the rollbacks of steps 6 to 3 in order if sign-in or the snapshot fail.
