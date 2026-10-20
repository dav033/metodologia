# Laptop remote API contract v1

Base path: `/api/remote/v1`. The laptop is the source of truth and accepts requests only from the AdvIn gateway over
the existing reverse SSH tunnel. The laptop API requires `Authorization: Bearer <gateway-key>` on every endpoint;
missing or invalid credentials return `401 UNAUTHORIZED`. The key is compared in constant time and never appears in
logs or responses.

JSON requests and responses use UTF-8. State changing requests also require a unique `Idempotency-Key` header and a
`precondition` in the body. Reusing a key with the same body returns the first result; reusing it with a different body
returns `422 IDEMPOTENCY_KEY_REUSED`. A mismatched target state returns `409 STALE_PRECONDITION`; no operation is
applied. The command body is defined by [`../contract/command.schema.json`](../contract/command.schema.json). Events
are defined by [`../contract/event.schema.json`](../contract/event.schema.json).

Errors use `application/problem+json` with `{ "type", "title", "status", "detail", "code", "requestId" }`.
`code` is stable and machine-readable. Unknown failures return `500 INTERNAL_ERROR`; responses never include stack
traces. `requestId` is present on every error.

## Endpoints

| Method and path | Purpose and success response | Errors |
|---|---|---|
| `GET /health` | Laptop reachability and contract version: `{ version, timestamp }`. Does not expose run data. | `401 UNAUTHORIZED`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /runs?cursor=&limit=` | Cursor-paginated run summaries: `{ items, nextCursor }`. Default limit 50, maximum 200. | `400 INVALID_CURSOR`, `401 UNAUTHORIZED`, `422 INVALID_LIMIT`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /runs/{project}/{req}` | Current run and plan summary. | `401 UNAUTHORIZED`, `404 NOT_FOUND`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /runs/{project}/{req}/events?after=&limit=` | Cursor-paginated event history for one run. | `400 INVALID_CURSOR`, `401 UNAUTHORIZED`, `404 NOT_FOUND`, `422 INVALID_LIMIT`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /events?after=` | Server-sent event stream. Event IDs are stable; reconnect with `Last-Event-ID`. Laptop closes a stream after at most 110 seconds and clients reconnect. | `401 UNAUTHORIZED`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /attempts/{project}/{req}/{attempt}` | Failure detail: classified cause, verification command/output, changed-file summary and last 200 log lines. | `401 UNAUTHORIZED`, `404 NOT_FOUND`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /plans?cursor=&limit=` | Cursor-paginated plans awaiting review or launch: `{ items, nextCursor }`. Default limit 50, maximum 200. | `400 INVALID_CURSOR`, `401 UNAUTHORIZED`, `422 INVALID_LIMIT`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /plans/{project}/{req}` | Plan status, task briefs, frozen revision and available questions. | `401 UNAUTHORIZED`, `404 NOT_FOUND`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /quotas` | Current account quota snapshot and observation timestamp. | `401 UNAUTHORIZED`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `GET /commands?cursor=&limit=` | Cursor-paginated command ledger: command, target, timestamp, origin and outcome. Default limit 50, maximum 200. | `400 INVALID_CURSOR`, `401 UNAUTHORIZED`, `422 INVALID_LIMIT`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `POST /confirmations` | Issues a one-use challenge for a destructive command. Request: `{ action, target: { project, req } }`; response: `{ challengeId, action, targetReq, expiresAt }`. Challenge expires after 120 seconds and is bound to action, target and gateway session. | `400 INVALID_REQUEST`, `401 UNAUTHORIZED`, `404 NOT_FOUND`, `409 INVALID_TARGET_STATE`, `422 UNSUPPORTED_ACTION`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR` |
| `POST /commands` | Applies one command from `command.schema.json`; response: `{ commandId, status, result, completedAt }`. A command result is persisted before it is returned. | `400 INVALID_COMMAND`, `401 UNAUTHORIZED`, `404 NOT_FOUND`, `409 STALE_PRECONDITION`, `409 INVALID_CHALLENGE`, `409 LAPTOP_OFFLINE`, `409 COMMAND_IN_PROGRESS`, `422 IDEMPOTENCY_KEY_REUSED`, `422 INVALID_TARGET_STATE`, `429 RATE_LIMITED`, `500 INTERNAL_ERROR`, `504 UNKNOWN_OUTCOME` |

### Command families

`pause`, `resume`, `cancel-attempt`, `reopen`, `retry`, `retry-route`, `revise`, `approve`, `launch`, `answer-round`,
`cancel-plan`, `delete-plan`, `edit-brief` and `note` are represented in the command schema. All commands carry an
idempotency key, target and expected-state precondition. The remote dispatcher calls the existing laptop operations
(`bt_scheduler_ops`, `bt_plans_api`, round handling and plan approval/launch); it does not implement a second scheduler.

`approve`, `launch`, `revise`, `cancel-plan` and `delete-plan` require `confirmation.challengeId` and `confirmation.typedReq`.
`edit-brief` requires a confirmation challenge because it freezes a new owner-approved plan revision and then invokes
the destructive `revise` operation. Its challenge is issued for action `revise` and the target REQ, even though the
outer command type is `edit-brief`; this preserves the confirmation required by the operation it calls. For other
destructive commands the challenge action matches the command type. In all cases the challenge must match the action
and target, remain unexpired and unused, and `typedReq` must exactly match the target REQ id. A missing, mismatched,
expired or reused challenge returns `409 INVALID_CHALLENGE`; neither the plan revision nor the run changes. A challenge
is consumed only when the command is accepted for application. The command's idempotency record prevents a retry after
an unknown network outcome from applying the edit or rebase twice.

`UNKNOWN_OUTCOME` includes the idempotency key and means the laptop did not return a definitive response within 15
seconds. The caller must retry the same body with the same key. It must not mint a second command. If the laptop is
known offline, the command is rejected as `LAPTOP_OFFLINE` and is never queued for later execution.

## Event kinds

| Kind | When emitted |
|---|---|
| `run.updated` | Run, task or attempt state changes. |
| `task.failed` | A task fails, including classified cause and retry availability. |
| `task.blocked` | A task cannot proceed without owner input. |
| `run.finished` | A run reaches a terminal state. |
| `question.waiting` | An answer round is open. |
| `plan.review` | A plan awaits approval or launch. |
| `quota.exhausted` | Every eligible account is out of quota. |
| `attempt.stale` | An attempt has had no sign of life for over ten minutes. |
| `laptop.offline` | The gateway has missed three consecutive five-second health probes. |
| `command.completed` | A ledger command reached a terminal outcome. |

Event IDs remain stable across replay and gateway restarts. The gateway uses the event ID as the notification dedupe
key; re-reading the feed cannot send a duplicate Telegram alert.
