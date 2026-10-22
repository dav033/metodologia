# Go-live runbook

Kit files live in `remote/deploy/`. Each step ends with its own **Rollback**. Never write secret values in this file or in git.

## OAuth callback rule (read first)

Register the GitHub OAuth App callback as `<FLOW_FRONTEND_ORIGIN>/api/auth/callback` (the `*.vercel.app` origin the owner opens).
Do **not** register the API host: the state cookie (`SameSite=Lax`) and the session cookie (`SameSite=Strict`) are host-only
cookies of the frontend host, so an API-host callback never receives them. Vercel's same-origin `/api/*` rewrite forwards
the callback to the gateway with the browser's `Cookie` header. The browser-level check is
`cd remote/web && npm run verify` (headless Chromium, `web/tests/oauth-browser.test.mjs`); run it before step 5.

## Step 1: Prepare the AdvIn service account and directories

Create the no-login account `flow`, `/opt/flow-gateway/releases`, `/opt/flow-gateway/current`, `/var/lib/flow-gateway`, and `/etc/flow-gateway`. Releases and configuration are root-owned; SQLite state is owned by `flow` and mode 0700.

Rollback: remove only the directories created by this deployment and delete `flow` if no files or processes remain owned by it.

## Step 2: Install the empty environment skeleton

Install `remote/deploy/flow-gateway.env.example` as `/etc/flow-gateway/env` with owner root and mode 0600. It contains no credentials. Keep both services stopped until T23 supplies the deployment values. Do not read or copy any secret values through a command line.

Rollback: remove the new environment file; restore a timestamped backup if one existed.

## Step 3: Install the release and stopped service units

Install the checked gateway release under `/opt/flow-gateway/releases/<timestamp>`, point `/opt/flow-gateway/current` to it, and install `flow-gateway.service` and `flow-bot.service` under `/etc/systemd/system/`. Run `systemd-analyze verify` on both units and `systemctl daemon-reload`. Do not enable or start either unit until T23.

Rollback: remove the two unit files, reload systemd, and restore the previous `current` symlink.

## Step 4: Publish the API host through Caddy

Back up `/opt/edge-proxy/Caddyfile` with a timestamped name, then add `remote/deploy/Caddyfile` for `flow-api.185-147-157-25.sslip.io`. Validate and reload the Docker container, not a host systemd unit: `docker exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then `docker exec caddy caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile`. Caddy proxies to `172.20.0.1:8790` with streaming flush enabled. Compare every existing hostname's HTTP status, TLS subject, and first-byte time to the pre-change receipt snapshot.

Rollback: restore the timestamped Caddyfile backup, validate and reload it in the `caddy` container, then verify the existing host snapshot again. The services remain stopped until T23.

## Step 5: Start services and connect the frontend (T23 only)

T23 supplies the real environment values, enables `flow-gateway.service` and `flow-bot.service`, and checks `/healthz`. Point the Vercel `FLOW_GATEWAY_ORIGIN` at the API host and redeploy the frontend only as part of that authorized task. Register the GitHub callback per the rule above.

Rollback: stop and disable both units, restore the timestamped Caddyfile backup, validate and reload the `caddy` container, and restore the previous frontend origin.

## Step 6: Start the laptop listener and tunnel

Create `~/.config/bitacora/remote.env` with mode `0600` holding the same `FLOW_GATEWAY_KEY` as the gateway (`install -m 600 /dev/null ~/.config/bitacora/remote.env`, then edit; never `cat` it). Install `remote/deploy/bitacora-remote-api.service` into `~/.config/systemd/user/` and start it before the tunnel so the forward never points at a closed port; without the key the listener answers 401 to everything.
Check `stat -c %a ~/.config/bitacora/remote.env` prints `600`.

`systemctl --user enable --now bitacora-remote-api.service advin-bitacora-tunnel.service` (units in `remote/deploy/`).

Rollback: `systemctl --user disable --now advin-bitacora-tunnel.service bitacora-remote-api.service`; the gateway then reports the laptop as offline.

## Step 7: Smoke test

Open the frontend origin, sign in as the allowed GitHub account, confirm the snapshot loads and `GET /api/auth/session` returns 200.
Check `journalctl -u bitacora-gateway -n 50`.

Rollback: run the rollbacks of steps 6 to 3 in order if sign-in or the snapshot fail.

## Full panel in production (panel parity)

`https://flow-remote.vercel.app/` serves the same pages and actions as the local panel (`/`, `/p/<project>/...`, `/flow`,
`/plans`, `/metrics`, `/learnings`, `/now`, `/live`, `/go/...`), behind the `dav033` GitHub login. The remote control
stays at `/remote`; the panel pages carry a fixed "Remoto" link and the remote page has a "Panel" link.

Path of a request: browser → Vercel (rewrites the panel paths to the gateway when `PANEL_PROXY=1`) → gateway
(`panel_proxy.py`: session, rate limits, redaction, shim injection) → laptop listener `/api/remote/v1/panel/<path>`
(`bt_remote_panel.py`: allow-list of GET pages and POST actions, then the panel's own handlers) → response.

Guards, in order: no session → 302 to login (HTML) or 401; writes need the `X-Flow-Request` header, the frontend
Origin and a typed `CONFIRMAR` bound to session, URL and body (single use, 120 s; 428 returns the challenge; the shim
shows the prompt); the laptop only runs allow-listed routes, rejects traversal, caps POST bodies at 1 MB, keeps the
panel's own token check and appends one line per action to `STATE/remote-panel-audit.jsonl`; responses go through a
secret redactor. `tests/test_remote_panel.py` fails when a top-level route of `bt_server.py` has no entry in the
allow-list, so a new panel page cannot ship without its production counterpart.

Operate: `PANEL_PROXY=1` is a Vercel production env var (remove it and redeploy to return to the remote control only).
Rollback of the gateway is the usual `previous` symlink; the laptop listener runs a pinned copy chosen in the
`bitacora-remote-api.service.d/exec.conf` drop-in.
