---
status: accepted
date: 2026-10-18
requirement: REQ-014 T69 / PRO-07
---

# PRO-07 inventory architecture decision

## Decision

**Do not persist workshop stock in this iteration.** `leftoverInventory` stays quote output from `src/lib/plan/python-mapper.ts`; it is not a stock ledger. No inventory tables, migrations, browser stock store or build-deduction endpoint are added. Owner: David (instruction of 2026-10-18).

Why: the owner-isolation scope (shared workshop stock versus per-account stock) and the REQ-004 identity mapping are not defined, and the current `APP_PASSWORD` cookie identifies no person. Persisting stock before those exist would create data that cannot be safely authorized, isolated or rolled back.

Consequences:
- PRO-07 (stock add/remove, build deduction, purchase list minus stock, shortage view) is not delivered. The purchase list keeps using quote output.
- Nothing in the customer session or widget payload changes, so D-035 rollout does not apply to this decision.
- Reopening persistence requires a new REQ or an amended PRO-07 that answers the open points below.

## Evidence

- PRO-07 asks decorators to add and remove stock by product, colour and size; marking a scene as built deducts its required materials; the purchase list uses required quantity minus available stock; shortages must be visible.
- `leftoverInventory` is quote output (`src/lib/cotizacion/motor.ts`, `src/lib/plan/python-mapper.ts`), not a stock ledger.
- `/3d` auto-saves one scene in this browser's `localStorage` (`taller3d:escena:v1`). There is no server-side build operation or stock store.
- Request authentication uses one shared `APP_PASSWORD` cookie; there is no authenticated user or workshop id in the runtime or schema. D-056 removed the separate admin key, so the app session is the only gate.
- REQ-004 plans internal admin and staff accounts (`usuarios`, `sesiones`, `usuarioDeRequest`), none implemented. It defines no workshop entity or membership.

## Open points before any persistence (deferred design, not implemented)

### Owner isolation
- **Shared workshop/company stock:** all authorized members share one pool. Fits the team model of REQ-004; needs a stable workshop owner and a membership rule.
- **Per-account stock:** each user has an independent pool; needs a stable user id and an admin oversight rule.
- Whichever is chosen, derive the owner from authenticated server-side membership; never accept an owner id from the request body.

### Persistence
- Store inventory outside customer session/widget JSON and outside browser-only `localStorage`, in additive PostgreSQL tables with an explicit schema version.
- One stock line per canonical product identity plus normalized colour and size; integer units; a database constraint forbids negative balances.
- Current balance and append-only movement records written in the same transaction. Do not duplicate inventory into `leftoverInventory`.
- Only resolved catalogue variants may change stock; free-text labels must not create catalogue items.

### Scene-build deduction and idempotency
- Snapshot the material requirements and a hash of the scene/BOM when the decorator confirms a build; never re-read a mutable browser scene afterwards.
- Each explicit confirmation carries a client-generated UUID operation id, reused on retries. Store it under the server-derived owner with a hash of the request and the result. Same id and payload returns the stored result without deducting again; same id with a different payload is a conflict.
- A deliberate later build of the same scene is a new operation id; the server decides whether a request is a retry, not a scene name or client flag.
- Deduction runs in one transaction: lock and update balances, deduct no more than available, record the movement, commit atomically. On shortage, deduct what is available, leave the balance at zero and return the missing quantity as a warning. Manual reductions follow the same rule.
- The locally saved scene `clave` is not an authorization or tenant key.

### REQ-004 identity and D-035 rollout
- REQ-004 identity is a prerequisite for persistent stock. The owner mapping must be added to REQ-004 before any inventory read or write is authorized.
- Keep stock and build records in their own tables. If a later change adds a field to the strict customer session/widget payload, it must be `.optional().catch(undefined)` and deployed as a reader before any writer (D-035).
- Use additive migrations with inventory access off by default; enable the reader first and the writer only after the compatible reader is live.

### Rollback
- Disable inventory writes first, then reads. Keep the additive tables and movement history; never drop or reset stock data as a rollback shortcut.

### Acceptance gates for a future implementation
- Test owner isolation, concurrent adjustments, non-negative balances, duplicate and retried build confirmations, deliberate rebuilds of the same scene, shortage warnings and rollback gates against a disposable database.

## Alternatives rejected

- Treating `leftoverInventory` as current stock: calculated quote output with no movement history.
- Persisting stock only in browser `localStorage`: cannot be shared by a team or isolated per user.
- Adding stock quantities to the strict guided session/widget: couples stock to conversation compatibility and adds D-035 rollout risk with no benefit yet.
- Trusting a client-supplied owner or user id: the current identity boundary cannot authorize it.
