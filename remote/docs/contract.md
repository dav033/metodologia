# Remote laptop API contract v1

This contract covers only the laptop listener. The gateway is the sole intended caller. Every request uses the
reverse SSH forward `127.0.0.1:18765` on AdvIn to `127.0.0.1:8766` on the laptop; the laptop listener binds only to
loopback and accepts only `/api/remote/v1/`. The separate browser panel remains at `127.0.0.1:8765` and is never a
tunnel destination. `FLOW_GATEWAY_KEY` is sent as `Authorization: Bearer <key>` and compared in constant time.

All bodies and responses are UTF-8 JSON. Times are RFC 3339 UTC. IDs and cursors are opaque strings. The contract is
versioned in the URL and body; incompatible changes require `/v2/`. The command request body is defined by
[`command.schema.json`](../contract/command.schema.json); feed events use
[`event.schema.json`](../contract/event.schema.json).

## Endpoints

| Method and path | Success | Errors |
|---|---|---|
| `GET /api/remote/v1/health` | `200 {"schemaVersion":1,"status":"ok","checkedAt":"…"}` | `401 UNAUTHORIZED` missing/invalid gateway key; `404 NOT_FOUND` unknown path; `503 STARTING` API dependencies unavailable. |
| `GET /api/remote/v1/snapshot` | `200` latest snapshot: runs, task states, active attempts, plans awaiting review, rounds awaiting answers, quotas, `generatedAt`, and `cursor`. | `401 UNAUTHORIZED`; `503 SNAPSHOT_UNAVAILABLE` before the shared read model is warm. |
| `GET /api/remote/v1/events?after=<cursor>&limit=<n>` | `200 {"events":[…],"nextCursor":"…","hasMore":false}`; event items conform to `event.schema.json`. `limit` defaults to 200 and is capped at 1000. | `400 INVALID_CURSOR` or `INVALID_LIMIT`; `401 UNAUTHORIZED`; `410 CURSOR_EXPIRED` when the requested cursor has been pruned. |
| `GET /api/remote/v1/attempts/{attemptId}/review` | `200` classified cause, verification command/output, changed files and diff stat, and at most the last 200 agent-log lines. | `400 INVALID_ID`; `401 UNAUTHORIZED`; `404 ATTEMPT_NOT_FOUND`; `503 REVIEW_UNAVAILABLE`. |
| `GET /api/remote/v1/quotas` | `200 {"accounts":[…],"checkedAt":"…"}` with account identifiers, remaining/reset values and source freshness. | `401 UNAUTHORIZED`; `503 QUOTAS_UNAVAILABLE`. |
| `GET /api/remote/v1/commands?after=<cursor>&limit=<n>` | `200 {"commands":[…],"nextCursor":"…"}` with command, target, submitted time, origin and result. | `400 INVALID_CURSOR` or `INVALID_LIMIT`; `401 UNAUTHORIZED`; `410 CURSOR_EXPIRED`. |
| `POST /api/remote/v1/challenges` | `201 {"challengeId":"…","target":"project/REQ-NNN","expiresIn":120}` after the signed-in owner types the target REQ id. Request: `{"target":{"project":"…","req":"REQ-NNN"},"typedReq":"REQ-NNN"}`. | `400 INVALID_CHALLENGE`; `401 UNAUTHORIZED`; `410 LAPTOP_OFFLINE`; `409` when the typed REQ does not match. |
| `POST /api/remote/v1/commands` | `202 {"commandId":"…","status":"accepted","idempotencyKey":"…"}` for a new command; `200` with the prior result when the same key is replayed. | `400 INVALID_COMMAND`; `401 UNAUTHORIZED`; `409 STALE_PRECONDITION`, `IDEMPOTENCY_CONFLICT`, `CONFIRMATION_REQUIRED`, or `CONFIRMATION_EXPIRED`; `410 LAPTOP_OFFLINE`; `413 BODY_TOO_LARGE`; `422 COMMAND_NOT_APPLICABLE`; `503 UNKNOWN_OUTCOME` when a caller timeout leaves execution uncertain (retry with the same key). |

Every endpoint returns `application/problem+json` on error with stable `code`, safe `message`, and optional `details`;
it never includes a traceback, key, filesystem path, or agent log. Gateway health probing uses the health endpoint at
5-second intervals and marks the laptop offline after three consecutive failures. Offline commands are rejected and
never queued. A command has an idempotency key and an expected target state; destructive operations additionally
carry a one-use server-issued confirmation challenge bound to the target and expiring after 120 seconds.

## Command families

The schema covers all families from REQ-027 R5 and recovery R13: `pause`, `resume`, `cancel-attempt`, `reopen`,
`retry` (optional route pin), `revise`, `approve`, `launch`, `answer-round`, `cancel-plan`, `delete-plan`,
`edit-brief`, and `note`. Each requires `schemaVersion: 1`, a unique `idempotencyKey`, a target, and a precondition.
`revise`, `approve`, `launch`, `cancel-plan`, and `delete-plan` require a confirmation challenge; the gateway issues
the challenge after the user types the target REQ id. A repeated key with a different body returns
`IDEMPOTENCY_CONFLICT`.

## Event families

Events have stable IDs and cursors. The schema includes `attempt.failed`, `attempt.blocked`, `run.finished`,
`round.waiting`, `plan.waiting`, `quota.exhausted`, `attempt.stalled`, `laptop.offline`, and `command.updated`.
Consumers persist `nextCursor` and deduplicate notifications by the stable `dedupeKey`.

## Gateway browser routes

After GitHub sign-in, the gateway serves the laptop snapshot at `GET /api/remote/v1/snapshot` with its original
`generatedAt` plus `cachedAt` and `laptopStatus`. The compatible `GET /api/remote/v1/runs` and `/plans` routes return
the corresponding arrays with the same freshness fields. These routes serve the most recently polled snapshot when
the laptop is offline; they do not trigger per-browser upstream requests.

`GET /api/remote/v1/events` and `/api/remote/v1/stream` are authenticated Server-Sent Event streams. Each `flow`
frame carries the original laptop event JSON and a gateway sequence in the SSE `id` field. Reconnect with
`Last-Event-ID` to replay events collected since that sequence. A cursor older than the in-memory replay window is
rejected with HTTP 409 instead of silently skipping events. Commands are posted to `/api/remote/v1/commands` with
the signed-in session, `Origin`, and `X-Flow-Request: 1`; the gateway relays the JSON command to the laptop API.
Browser commands use `command.schema.json` (`type`, `idempotencyKey`, and structured `target`). The gateway
translates them to the laptop ledger's internal request (`command`, `idempotency_key`, and `project/REQ-NNN` target).
Snapshots expose nested run fields in camel case, and SSE `data` uses `event.schema.json`, including when the laptop
feed supplies its legacy `kind`/`ord`/`occurred_at` fields.
