---
status: pending-owner-choice
date: 2026-10-16
requirement: REQ-014 T69 / PRO-07
---

# PRO-07 inventory architecture decision

This is a design draft. The owner-isolation choice remains unanswered, so this is not an accepted architecture decision and T69 remains open. No inventory migration or persisted stock data has been added.

## Evidence

- PRO-07 asks decorators to add and remove stock by product, colour and size; marking a scene as built deducts its required materials; the purchase list uses required quantity minus available stock; shortages must be visible.
- `leftoverInventory` is quote output, mapped by `src/lib/plan/python-mapper.ts`; it is not a stock ledger.
- `/3d` currently auto-saves one scene in this browser's `localStorage` (`taller3d:escena:v1`). The saved `clave` is generated locally and reused for that scene; there is no server-side build operation or stock store.
- Current request authentication uses one shared `APP_PASSWORD` cookie. There is no authenticated user id or workshop id in the current runtime/schema.
- REQ-004 scopes accounts to internal admins and Sempertex staff, excludes external decorators/customers, and plans `usuarios`/`sesiones`; those accounts and `usuarioDeRequest` are not implemented. Its plan does not define a workshop entity or membership.

## Owner isolation — decision pending

Two viable scopes remain:

1. **Shared workshop/company stock:** every authorized member of the same workshop sees and changes one stock pool. This matches the internal admin/staff team model in REQ-004, but requires a stable workshop/company owner and a user-to-workshop membership rule.
2. **Per-account stock:** every user has an independent pool. This needs only a stable user id, but staff do not share stock and the admin's access/oversight must be specified.

**Recommendation for confirmation:** shared workshop/company stock. This fits a team that jointly quotes and builds Sempertex events. Do not enable it until the owner confirms the scope and REQ-004 identity mapping is specified. Derive the owner id from authenticated server-side membership; never accept a tenant/user owner id as authority from the request body.

## Persistence — proposed, not accepted

- Keep inventory outside customer session/widget JSON and outside browser-only `localStorage`; use additive PostgreSQL tables with an explicit schema version.
- Represent each stock line by canonical product identity plus normalized colour and size codes, with integer units and a database constraint preventing negative balances. Accessories without a colour/size use explicit normalized empty values rather than ambiguous client labels.
- Keep a current balance and an append-only movement/build record in the same transaction, so manual changes and scene deductions are auditable and can be reconciled. Do not duplicate inventory in `leftoverInventory`.
- Require resolved product/variant identity before changing stock. User-entered labels alone must not create duplicate catalogue items.

The owner key and foreign key cannot be finalized until the pending isolation choice is answered. If shared, REQ-004 must define workshop/company membership; if per-account, inventory must reference the authenticated `usuario_id`.

## Scene-build deduction and idempotency — proposed

- Snapshot the canonical material requirements and hash the scene/BOM when the decorator confirms a build. Do not re-read a mutable browser scene later to determine what was deducted.
- Each explicit build confirmation gets a stable UUID operation id that the client reuses for retries. Store it under the server-derived owner scope with a hash of the request and the exact result. Replaying the same id and payload returns the stored result without another deduction; reusing it with a different payload is a conflict.
- A later deliberate build of the same scene is a new operation id. The server, not a scene name or client flag, decides whether a request is a retry.
- In one database transaction, lock/update affected balance rows, subtract no more than the available quantity, record the movement and result, and commit atomically. On a shortage, deduct only available units, leave the balance at zero, and return a warning with the missing quantity. A failed transaction leaves both balance and movement unchanged.
- Manual reductions use the same atomic non-negative rule and return an explicit shortage warning; no silent negative balance.

The locally saved scene `clave` may help correlate a build to the current browser scene, but it is not an authorization or tenant key. The operation id and server-derived owner scope are the idempotency/security boundary.

## REQ-004 identity and D-035 rollout

- REQ-004 identity is a prerequisite to enabling persistent stock: current `APP_PASSWORD` does not identify a person. Add the chosen owner mapping to REQ-004 before implementation can safely authorize inventory reads/writes.
- Keep stock and build records in their own tables; do not add inventory or build-state fields to strict customer session/widget payloads. Under that design, D-035's reader-first requirement for new session/widget fields does not apply. If implementation later adds such a field, it must be `.optional().catch(undefined)` and deployed read-only before any writer.
- Use additive schema migration and default-off inventory access. If separate reader/writer rollout gates are needed, enable the reader first and the writer only after the compatible reader is deployed; do not apply a production migration as part of this architecture task.

## Rollback and acceptance gates

- Rollback disables inventory writes first and reads second; retain the additive tables and movement history. Do not drop or reset stock data as a rollback shortcut; export/retention review is separate.
- Before T69 is accepted, confirm the owner scope and finalize its REQ-004 mapping, persistence keys, shortage behavior, idempotency boundary and D-035 applicability. Record the accepted ruling in an ADR and the project brain.
- Before a later implementation is enabled, test owner isolation, concurrent adjustments, non-negative balances, duplicate/retried build confirmations, same-scene deliberate rebuilds, shortage warnings, and rollback gates with a disposable database.

## Alternatives rejected for this design

- Treating `leftoverInventory` as current stock: it is calculated quote output and loses stock movement history.
- Persisting stock in only browser `localStorage`: it cannot be shared by a team or reliably isolated across users/devices.
- Adding the stock quantity to the strict guided customer session/widget: it couples stock to conversation compatibility and invokes D-035 rollout risk without benefit.
- Trusting a client-supplied owner/user id: the current identity boundary cannot authorize it.
