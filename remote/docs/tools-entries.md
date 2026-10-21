# Flow Remote & Gateway — Tools & Infrastructure Entries

Copy these entries into `bitacora/TOOLS.md` (or the appropriate project `TOOLS.md`) at go-live.

**Never write secrets here** (the bitácora is versioned with git). Reference them instead: path to key file, `~/.ssh/config` host alias, environment variable name, password-manager entry, or "CLI already logged in".

---

### flow-gateway
- **Type:** API Gateway & Command Relay daemon (Python stdlib, systemd, Caddy reverse proxy)
- **Host / Provider:** AdvIn VPS (`ssh advin-vps`, alias in `~/.ssh/config`, key `~/.ssh/advin-vps`) · user `flow-gateway` / `root`
- **What runs here:** `flow-gateway.service` (Python stdlib HTTP daemon listening on `172.20.0.1:8790`), Caddy reverse proxy terminating TLS for `flow-api.<domain>`, SQLite state databases under `/var/lib/flow-gateway/`
- **Configuration & Secrets:**
  - Environment file: `/etc/flow-gateway.env` (permissions `0600`, owned by `root:flow-gateway`)
  - Secrets referenced by variable name:
    - `FLOW_GATEWAY_KEY`: Shared secret key matching `BITACORA_GATEWAY_KEY` on laptop
    - `SESSION_SECRET`: Random secret string for signing session cookies
    - `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: GitHub OAuth app credentials (owner restricted to `dav033`)
    - `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: Telegram Bot API token and authorized chat ID
    - `LAPTOP_ORIGIN`: Reachable loopback tunnel endpoint (default `http://127.0.0.1:8765`)
    - `GATEWAY_BIND_HOST`: Bind address (default `172.20.0.1`)
    - `GATEWAY_BIND_PORT`: Bind port (default `8790`)
    - `FLOW_GATEWAY_ORIGIN`: Public gateway origin URL (e.g. `https://flow-api.<domain>`)
- **Status / logs:**
  - Service status: `ssh advin-vps "systemctl status flow-gateway.service"`
  - Journal logs: `ssh advin-vps "journalctl -u flow-gateway.service -n 100 --no-pager"`
  - Caddy logs / validate: `ssh advin-vps "caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile"`
  - Liveness health check: `curl -fsS https://flow-api.<domain>/healthz` or `ssh advin-vps "curl -fsS http://127.0.0.1:8790/healthz"`
- **Deploy:**
  - Prepare release directory on AdvIn and run deployment script:
    `ssh advin-vps "sudo /opt/flow-gateway/current/remote/deploy/deploy.sh /path/to/checked-release"`
  - Pre-deploy offline check: `python3 -m unittest discover -s remote/deploy/tests -p test_kit.py`
- **Rollback:**
  - Restore previous release and reload configurations:
    `ssh advin-vps "sudo /opt/flow-gateway/current/remote/deploy/rollback.sh"`
- **Notes:** Reverse SSH tunnel opened from laptop (`advin-bitacora-tunnel.service`) forwards remote port 8765 to laptop `bt_server` on `127.0.0.1:8765`.

---

### flow-remote
- **Type:** Frontend PWA & Mobile Web Control Panel (Next.js 15, React, Tailwind CSS)
- **Host / Provider:** Vercel (or static Node.js hosting) · Project: `flow-remote-web`
- **Access / CLI:** `vercel` CLI, logged in; link with `vercel link --project flow-remote-web`
- **What runs here:** Next.js mobile-first PWA control panel, client-side SSE listener (`/api/stream`), state dashboard and review screen
- **Configuration & Secrets:**
  - Vercel Environment Variables:
    - `FLOW_GATEWAY_ORIGIN`: Public origin of flow-gateway (e.g. `https://flow-api.<domain>`), used by `/api/:path*` rewrite in `next.config.ts`
  - Authentication: User signs in via GitHub OAuth through the gateway; session cookies are first-party and credentials reside strictly in gateway configuration
- **Status / logs:**
  - Deployment status: `vercel ls flow-remote-web`
  - Runtime logs: `vercel inspect <deployment-url> --logs`
- **Deploy:**
  - Automatic: git push to `main` branch
  - Manual production deploy: `cd remote/web && vercel --prod`
  - Offline verification before deployment: `cd remote/web && npm run verify` (runs ESLint, TypeScript check, mock tests, and Next.js build)
- **Rollback:**
  - Promote previous instant deployment via Vercel dashboard or CLI: `vercel rollback <deployment-url>`
- **Notes:** Same-origin rewrite in `next.config.ts` proxies `/api/:path*` to `FLOW_GATEWAY_ORIGIN` so cookies and SSE streams pass without cross-origin complexity.
