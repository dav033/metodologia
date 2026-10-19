# Spike — Vercel external rewrites: cookies and SSE (REQ-027, old T1)

Run by the coordinator on 2026-10-19, before the scheduler run resumes. Throwaway setup, removed afterwards (stub process and file deleted on AdvIn, Vercel project `flow-spike` removed):
a stdlib stub (`/api/login` sets a cookie, `/api/me` echoes `Cookie` and `Last-Event-ID`, `/api/sse` sends one event
per second with chunked transfer encoding) on AdvIn `0.0.0.0:18899` (plain HTTP, no Caddy change), and a Vercel project
`flow-spike` whose `vercel.json` rewrites `/api/:path*` to `http://185.147.157.25:18899/api/:path*`.

## Results

| Check | Result |
|---|---|
| `Set-Cookie` from the origin reaches the browser through the rewrite | yes: `flow_s=…; HttpOnly; Secure; SameSite=Strict; Path=/` arrives on `flow-spike.vercel.app` |
| `Cookie` and `Last-Event-ID` request headers reach the origin | yes: the origin echoed both |
| SSE events stream incrementally (no buffering) | yes: first event at 0.4 s, then one per second (10 events in 9.4 s) |
| Maximum stream duration through the rewrite | not cut: 330 events over 329.6 s, until the client stopped at 330 s |

## Consequences for the design

- Same-origin rewrites work for the session cookie: the gateway can set it and it stays first-party on the Vercel host.
- The gateway must send SSE with **chunked transfer encoding** (or HTTP/1.0 close-delimited) and flush per event.
  A response with `HTTP/1.1` + `Connection: close` and no length/chunking was held back by the Cloudflare quick tunnel
  used first; Vercel itself streamed once the origin used chunking.
- Clients reconnect with `Last-Event-ID` (EventSource does it automatically); the gateway resumes from that id and
  should still end each stream itself after about 110 s, sending `retry: 1000`: Vercel documents a 120 s limit for
  external rewrites (`lotm` decision 2026-10-13) even though this test was not cut, and a cycle below it costs nothing.
- A Cloudflare quick tunnel is not a valid stand-in for SSE tests: it buffered the stream even with chunking.
