# Remote control architecture decision

**Status:** selected for REQ-027. **Scope:** control-plane connectivity between the laptop, AdvIn gateway and Vercel
frontend. The laptop remains the sole scheduler and agent executor. AdvIn has no agent credentials.

## Decision

Keep the browser panel on its existing loopback listener, `127.0.0.1:8765`. Run a separate laptop listener on
`127.0.0.1:8766` with a remote-only handler that accepts only `/api/remote/v1/`. The gateway key authenticates each
request; the listener does not serve the panel, project pages, static assets, plan launch forms, or any other local
web route. The gateway reaches it through one reverse SSH forward:

```text
AdvIn 127.0.0.1:18765  --SSH reverse forward-->  laptop 127.0.0.1:8766
```

The tracked user unit `remote/deploy/advin-bitacora-tunnel.service` makes that destination explicit. AdvIn's gateway
uses `http://127.0.0.1:18765` as its laptop origin. Caddy and Vercel never connect to the laptop. Vercel rewrites
same-origin `/api/*` requests to the gateway over HTTPS. The gateway owns GitHub login, session cookies, offline
state, caching, command relay and Telegram delivery. The laptop API owns command preconditions, idempotency, dispatch
to existing operations, and the event cursor.

This split preserves local panel behavior while the tunnel exposes only a narrow, authenticated machine API. The
remote listener binds to loopback on the laptop, and the SSH remote bind is also loopback on AdvIn; neither adds a
public laptop or VPS port.

## Alternatives considered

| Option | Decision | Reason |
|---|---|---|
| Forward the existing panel at `127.0.0.1:8765` | Rejected | The panel has unauthenticated GET pages and plan-launch controls. Any process on AdvIn that can reach the forward would gain the full panel. A gateway key on selected API routes does not protect the rest of that listener. |
| Expose a dedicated remote-only laptop listener through the reverse tunnel | **Selected** | Separates the trust boundary at the socket and HTTP handler. Only versioned API paths are routed; every API call also requires the gateway key. |
| Expose the laptop directly to the internet | Rejected | Conflicts with the requirement that the laptop is never internet-reachable and adds inbound firewall and TLS exposure. |
| Run an outbound WebSocket agent from laptop to gateway | Rejected | The reverse tunnel already provides a simple, reconnectable path without maintaining a second command transport. |
| Auth.js in the Vercel frontend as the gateway's trust boundary | Rejected | The gateway still needs its own verified caller session; frontend authentication alone does not secure gateway-to-laptop commands. |
| Starlette/uvicorn for the gateway | Rejected | The single-owner gateway has no async requirement, and the verifier is offline and cannot install third-party dependencies. Use Python 3.12 standard library and SQLite. |
| Queue commands while laptop is offline | Rejected | The owner explicitly requires offline commands to fail immediately so stale actions do not run later. |

## Consequences and rollback

The local panel remains independently available on port 8765. The API and tunnel use separate ports and handlers; a
gateway outage cannot expose the local panel through the API listener. The tunnel unit must be installed or updated
alongside the listener, and the gateway upstream must use port 18765. During rollout, verify both that the panel still
works locally and that requests through the tunnel cannot load `/`, `/plans`, or `/p/*`.

Rollback stops and disables `advin-bitacora-tunnel.service`, removes the gateway's upstream reference to port 18765,
and stops the remote listener. The loopback panel remains on port 8765 throughout. Do not retarget the tunnel back to
the panel as a rollback: disable remote access until the remote-only listener is restored.
