# Remote flow architecture decision

## Decision

Keep execution and the source of truth on the laptop. AdvIn runs a small control-plane gateway, and the Vercel app
talks only to that gateway. Connect AdvIn to the laptop through the already-running reverse SSH tunnel; do not expose
the laptop panel or remote API to the public internet. The tunnel is the only network path from gateway to laptop.

The gateway authenticates the owner with GitHub, restricts the account to `dav033`, holds the session and Telegram
integration, caches the last laptop snapshot, relays commands, and sends notifications. It does not run agents, hold
Claude/Codex credentials, or become an alternate scheduler. The laptop's `/api/remote/v1/` API is reachable only with
the gateway key and records command idempotency, preconditions and outcomes before acknowledging a command.

The Vercel frontend uses same-origin rewrites to reach the gateway. This keeps the session cookie first-party and
allows SSE without browser CORS access to the gateway hostname. The rewrite spike confirmed cookies and incremental
SSE delivery; clients reconnect using stable event IDs and the gateway ends streams before the documented rewrite
limit.

## Alternatives considered

| Option | Decision | Reason |
|---|---|---|
| Run the scheduler on AdvIn | Rejected | Execution must remain on the laptop, and AdvIn must not contain agent credentials. |
| Expose the laptop directly to the internet | Rejected | Violates the laptop isolation requirement and makes the control surface public-facing. |
| Poll the laptop over a new public VPN or tunnel | Rejected | The existing reverse SSH tunnel already provides the required private route and keeps laptop reachability narrow. |
| Put login, state and command execution in Vercel functions | Rejected | The persistent gateway needs a durable command ledger, event cursor, Telegram delivery retries and a connection to the private tunnel. |
| Use a Cloudflare quick tunnel for gateway-to-laptop transport | Rejected | It is not the established route and the spike showed it buffered SSE; it is not a suitable substitute for the reverse SSH tunnel. |
| Keep the Vercel app as a static observer with no gateway | Rejected | It cannot safely authenticate commands, track laptop liveness, deduplicate notifications or provide a durable ledger. |

## Boundaries and failure behavior

- Laptop `bt_server` owns run state and invokes existing scheduler/plan/round operations. The existing loopback UI
  stays at `127.0.0.1:8765` with its current behavior.
- Gateway owns the GitHub session, bounded snapshot cache, command ledger, event cursor and Telegram outbox. Gateway
  storage contains no model credentials.
- Frontend owns presentation and submits intent with an idempotency key, expected-state precondition and, for
  destructive actions, the server-issued typed-REQ challenge.
- If the laptop misses three health probes spaced five seconds apart, the gateway serves the last cached snapshot
  with its timestamp and rejects commands. It never queues an offline command.
- If a command times out after 15 seconds, the result is `UNKNOWN_OUTCOME`; retrying its same idempotency key safely
  resolves the existing ledger entry.
- Laptop API errors use a stable problem response with a request ID; secrets and stack traces are excluded from logs
  and responses.

## Evidence and follow-up

The contract is in [`contract.md`](contract.md). The same-origin cookie and streaming behavior was checked in the
[Vercel rewrite spike](spike-rewrite-sse.md). The tunnel endpoint is already managed by
`advin-bitacora-tunnel.service`; deployment work must preserve that service and add only the gateway-side route and
key configuration. Secrets remain in protected environment files or platform environment settings, never in git.
