# TRAIN-1 — Browser sessions must expire on the server

The API sets `Max-Age=28800` on the `training_session` cookie but keeps the session in an in-memory `Map` forever, so a
copied cookie value stays valid after the browser dropped it. Sessions must stop being accepted 8 hours after creation
(server-side), and expired entries must not accumulate.

## Requirements
- R1. A session older than 8 h is rejected by `requireAuth`, `requireMutation` and the WebSocket upgrade.
- R2. Valid sessions and the MCP bearer token keep working unchanged.
- R3. Expired sessions are removed from memory.
