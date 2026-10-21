# Flow Remote Control & Gateway

Mobile and remote flow control infrastructure for bitácora and task execution (REQ-027). This directory contains the remote gateway service, deployment kits, Next.js web application, contract schemas, and documentation.

## Architecture Overview

```
Mobile Phone ──> Vercel (Next.js PWA) ── rewrite /api/* ──> Caddy (AdvIn VPS, TLS) ──> flow-gateway (Python stdlib)
                                                                                            │ (172.20.0.1:8790)
Telegram App <── flow-gateway (long polling)                                                │
                                                                                            ▼
Laptop (bt_server on 127.0.0.1:8765) <── reverse SSH tunnel 127.0.0.1:8765 <───────────────┘
```

- **Laptop**: Single source of truth and only task executor. Runs `bt_server` on `127.0.0.1:8765`. Holds all API credentials for LLM providers (Claude, Codex). Outbound SSH reverse tunnel connects to AdvIn VPS.
- **Gateway (`remote/gateway`)**: Python stdlib daemon running on AdvIn VPS under systemd (`flow-gateway.service`). Handles GitHub OAuth (restricted to user `dav033`), session management, snapshot caching, SSE fan-out, command relay with idempotency, event notifications, and Telegram bot.
- **Web App (`remote/web`)**: Next.js 15 PWA mobile-first dashboard. Uses same-origin rewrites (`/api/:path*`) targeting the gateway origin, allowing first-party session cookies and SSE event streaming.
- **Contract (`remote/contract`)**: JSON Schema definitions (`command.schema.json`, `event.schema.json`, `error.schema.json`) governing interaction between laptop, gateway, and clients.

## Running & Operating

### 1. Gateway (`remote/gateway`)

- **Local Development / Offline Run:**
  ```sh
  # Run gateway unit tests
  python3 -m unittest discover -s remote/gateway/tests -p "test_*.py"
  ```
- **Starting on AdvIn VPS:**
  The gateway runs as a systemd service:
  ```sh
  sudo systemctl start flow-gateway.service
  sudo systemctl status flow-gateway.service
  journalctl -u flow-gateway.service -f
  ```
- **Configuration & Secrets:**
  Configuration is loaded from `/etc/flow-gateway.env` (mode `0600`, owned by `root:flow-gateway`). Keys:
  - `FLOW_GATEWAY_KEY`: Secret shared with laptop (`BITACORA_GATEWAY_KEY`).
  - `SESSION_SECRET`: Key for HMAC session cookies.
  - `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: GitHub OAuth application credentials.
  - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: Telegram bot authentication.
  - `GATEWAY_BIND_HOST`: Bind address (default `172.20.0.1`).
  - `GATEWAY_BIND_PORT`: Port (default `8790`).
  - `LAPTOP_ORIGIN`: Reachable tunnel address (default `http://127.0.0.1:8765`).

### 2. Web App (`remote/web`)

- **Local Development:**
  ```sh
  cd remote/web
  npm ci
  npm run mock   # starts mock gateway fixture server on :8790
  npm run dev    # runs Next.js dev server on :3000
  ```
- **Production Build & Verification:**
  ```sh
  cd remote/web
  npm run verify # lints, type-checks, runs mock tests, and builds production bundle
  ```
- **Hosting:**
  Hosted on Vercel with `FLOW_GATEWAY_ORIGIN` pointing to the public gateway origin.

### 3. Telegram Bot

Operated as part of `flow-gateway.service` via outbound long-polling (no public webhook).
- Responds only to `TELEGRAM_CHAT_ID`.
- Command `/estado` shows active runs.
- Interactive inline buttons provide `Ver`, `Pausar`, `Reanudar`, and `Reintentar`.

---

## Testing & Verification

All automated tests run entirely offline with mock fixtures and loopback sockets:

1. **Deploy Kit Tests:**
   ```sh
   python3 -m unittest discover -s remote/deploy/tests -p test_kit.py
   ```
   Validates systemd service file, Caddy configuration, and env template integrity.

2. **Gateway Unit Tests:**
   ```sh
   python3 -m unittest discover -s remote/gateway/tests -p "test_*.py"
   ```
   Tests auth, command dispatch, guardrails, SSE streaming, liveness, and Telegram bot handling.

3. **End-to-End Loopback Tests:**
   ```sh
   python3 -m unittest discover -s remote/e2e/tests -p "test_*.py"
   ```
   Executes full offline integration stack with simulated GitHub OAuth, Telegram API, SSH tunnel, and laptop server.

4. **Web Frontend Tests:**
   ```sh
   cd remote/web && npm test
   ```
   Tests responsive UI components, mock gateway contracts, and review screen formatting.

---

## Deployment & Rollback

### Deploying the Gateway

Deployment uses the validated script in `remote/deploy/deploy.sh` on AdvIn VPS:
```sh
# Step 1: Pre-flight check
python3 -m unittest discover -s remote/deploy/tests -p test_kit.py

# Step 2: Deploy release directory
sudo remote/deploy/deploy.sh /path/to/checked-release
```
The script updates `/opt/flow-gateway/current`, installs systemd service and Caddy config, reloads daemons, and validates `/healthz`.

### Rollback the Gateway

If a deployment fails or unexpected issues occur post go-live:
```sh
sudo remote/deploy/rollback.sh
```
This restores the previous release symlink and previous systemd and Caddy configurations from `/var/lib/flow-gateway/deploy-state`, reloads services, and checks the health endpoint.

Detailed operational steps and step-by-step failure recovery are documented in `remote/docs/runbook.md`.

---

## Go-Live Checklist & Reference

- **TOOLS Entries**: Pre-formatted entries for `TOOLS.md` are available in [`remote/docs/tools-entries.md`](docs/tools-entries.md).
- **Runbook**: Deployment prerequisites, step-by-step execution, and rollbacks in [`remote/docs/runbook.md`](docs/runbook.md).
- **Contract & Schemas**: Detailed endpoint schemas and error codes in [`remote/docs/contract.md`](docs/contract.md).
- **Architecture**: Architectural rationale and decisions in [`remote/docs/architecture.md`](docs/architecture.md).
