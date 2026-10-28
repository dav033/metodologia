# Remote laptop API contract v1

This contract covers only the laptop listener. The gateway is the sole intended caller. Every request uses the
reverse SSH forward `127.0.0.1:18765` on AdvIn to `127.0.0.1:8766` on the laptop; the laptop listener binds only to
loopback and accepts only `/api/remote/v1/`. The separate browser panel remains at `127.0.0.1:8765` and is never a
tunnel destination. `FLOW_GATEWAY_KEY` is sent as `Authorization: Bearer <key>` and compared in constant time.

All bodies and responses are UTF-8 JSON. Times are RFC 3339 UTC. IDs and cursors are opaque strings. The contract is
versioned in the URL and body; incompatible changes require `/v2/`.

## Canonical models and generated schemas

The single source of truth is the Pydantic v2 module `skill/scripts/bt_contracts/remote.py`. Every file in
[`remote/contract/`](../contract/) and the phone's `remote/web/src/contract.generated.ts` is generated from it with
`uv run python -m bt_contracts.schemas` (run from `skill/scripts`; `--check` fails on drift, and
`test_remote_contracts` fails when a generated file is stale). Never edit the generated files by hand.

| Schema | Producer → consumer |
|---|---|
| `snapshot.schema.json` | laptop `GET /snapshot` (`bt_remote_snapshot`) → gateway cache |
| `gateway-snapshot.schema.json` | gateway `GET /snapshot` and SSE `resync` frames → phone |
| `event.schema.json`, `events-page.schema.json` | laptop `GET /events` (`bt_remote_events`) → gateway → SSE `event` frames |
| `command.schema.json`, `challenge.schema.json`, `command-result.schema.json` | phone / Telegram → gateway → phone |
| `ledger-command.schema.json` | gateway (`app._ledger_command`) → laptop `POST /commands` |
| `quotas.schema.json`, `routes.schema.json`, `review.schema.json`, `command-history.schema.json` | laptop read models relayed by the gateway allow-list → phone |
| `error.schema.json` | every `application/problem+json` body |

One dialect: camelCase on every phone-facing body. The gateway → laptop ledger body is the only snake_case contract
and stays inside the tunnel. Models refuse unknown fields; stdlib producers never import pydantic — tests build their
real output over a disposable bitácora root and validate it (`skill/scripts/tests/test_remote_contracts.py`). The
fixtures the phone mock and the gateway tests read live in `remote/contract/fixtures/` and are validated the same way.

**Alias window (removed in v2).** Snapshot runs keep `status` next to the canonical `state` for gateways deployed
before this contract; the gateway and the Telegram bot read `state` first. The gateway accepts a retry route's
`route_id`/`id` next to the canonical `routeId`, and the phone accepts a laptop's `route_id` next to `routeId`, for
deployments built before the contract.

**Stream.** The gateway serves `GET /api/remote/v1/stream` (`STREAM` in the generated module) with named SSE frames:
`event` carries one feed event and an `id:` of `epoch:sequence`; `resync` carries a full gateway snapshot when the
`Last-Event-ID` is unknown or older than the backlog. Frames are sent with `Cache-Control: no-store, no-transform` so a
compressing proxy never buffers them.

## Endpoints

| Method and path | Success | Errors |
|---|---|---|
| `GET /api/remote/v1/health` | `200 {"schemaVersion":1,"status":"ok","checkedAt":"…"}` | `401 UNAUTHORIZED` missing/invalid gateway key; `404 NOT_FOUND` unknown path; `503 STARTING` API dependencies unavailable. |
| `GET /api/remote/v1/snapshot` | `200` latest snapshot: runs, task states, active attempts, plans awaiting review, rounds awaiting answers, quotas, `generatedAt`, and `cursor`. | `401 UNAUTHORIZED`; `503 SNAPSHOT_UNAVAILABLE` before the shared read model is warm. |
| `GET /api/remote/v1/events?after=<cursor>&limit=<n>` | `200 {"events":[…],"nextCursor":"…","hasMore":false}`; event items conform to `event.schema.json`. `limit` defaults to 200 and is capped at 1000. | `400 INVALID_CURSOR` or `INVALID_LIMIT`; `401 UNAUTHORIZED`; `410 CURSOR_EXPIRED` when the requested cursor has been pruned. |
| `GET /api/remote/v1/attempts/{attemptId}/review` | `200` classified cause, verification command/output, changed files and diff stat, and at most the last 200 agent-log lines. | `400 INVALID_ID`; `401 UNAUTHORIZED`; `404 ATTEMPT_NOT_FOUND`; `503 REVIEW_UNAVAILABLE`. |
| `GET /api/remote/v1/quotas` | `200 {"accounts":[…],"checkedAt":"…"}` with account identifiers, remaining/reset values and source freshness. | `401 UNAUTHORIZED`; `503 QUOTAS_UNAVAILABLE`. |
| `GET /api/remote/v1/commands?after=<cursor>&limit=<n>` | `200 {"commands":[…],"nextCursor":"…"}` with command, target, submitted time, origin and result. | `400 INVALID_CURSOR` or `INVALID_LIMIT`; `401 UNAUTHORIZED`; `410 CURSOR_EXPIRED`. |
| `POST /api/remote/v1/challenges` | `201 {"challengeId":"…","target":"…","expiresIn":120}` after the caller types the target's exact `REQ-NNN` id. The challenge is one-use and bound to that target. | `400 INVALID_CHALLENGE`; `401 UNAUTHORIZED`; `413 BODY_TOO_LARGE`. |
| `POST /api/remote/v1/commands` | `202 {"commandId":"…","status":"accepted","idempotencyKey":"…"}` for a new command; `200` with the prior result when the same key is replayed. | `400 INVALID_COMMAND`; `401 UNAUTHORIZED`; `409 STALE_PRECONDITION`, `IDEMPOTENCY_CONFLICT`, `CONFIRMATION_REQUIRED`, or `CONFIRMATION_EXPIRED`; `410 LAPTOP_OFFLINE`; `413 BODY_TOO_LARGE`; `422 COMMAND_NOT_APPLICABLE`; `503 UNKNOWN_OUTCOME` when a caller timeout leaves execution uncertain (retry with the same key). |

Every endpoint returns `application/problem+json` on error with stable `code`, safe `message`, and optional `details`;
it never includes a traceback, key, filesystem path, or agent log. Gateway health probing uses the health endpoint at
5-second intervals and marks the laptop offline after three consecutive failures. Offline commands are rejected and
never queued. A command has an idempotency key and an expected target state; destructive operations additionally
carry a one-use server-issued confirmation challenge bound to the target and expiring after 120 seconds.

## Command families

The schema covers all families from REQ-027 R5 and recovery R13: `pause`, `resume`, `cancel-attempt`, `reopen`,
`retry` (optional route pin `{routeId, provider, model, account}`), `revise`, `approve`, `launch`, `answer-decision`,
`answer-round`, `cancel-plan`, `delete-plan`, `edit-brief` (`field` + `value`), and `note`. Each requires
`schemaVersion: 1`, a unique `idempotencyKey` (16–120 characters of `[A-Za-z0-9._:-]`; the ledger caps keys at 120),
a target, and a precondition. `reopen`, `retry` and `edit-brief` target `{kind: "task", taskId}` and their
precondition is that task's state; `cancel-attempt` names its `attemptId`. A route pin is persisted only after the
Scheduler accepted the retry's task state, and a refused retry leaves the previous pin untouched. Route listings and
pinned retries share one availability rule (`bt_route_pins.usable`: unknown quota is unavailable).
`revise`, `approve`, `launch`, `cancel-plan`, `delete-plan`, and `edit-brief` require a confirmation challenge; the
gateway issues the challenge after the user types the target REQ id. `edit-brief` creates and freezes an
owner-approved revision, then invokes destructive `revise`, so `confirmation.typedReq` MUST exactly equal
`target.req` and the same one-use challenge must remain bound to that target through the entire operation. The
command dispatcher MUST validate this cross-field equality before either freezing the revision or invoking `revise`.
A repeated key with a different body returns
`IDEMPOTENCY_CONFLICT`.

## Event families

Events have stable IDs and cursors. The schema includes `attempt.failed`, `attempt.blocked`, `run.finished`,
`round.waiting`, `plan.waiting`, `quota.exhausted`, `attempt.stalled`, `laptop.offline`, and `command.updated`.
`occurredAt` is RFC 3339 UTC (`Z`); legacy naive laptop timestamps are interpreted in the laptop's local timezone
before conversion. Consumers persist `nextCursor` and deduplicate notifications by the stable `dedupeKey`.
