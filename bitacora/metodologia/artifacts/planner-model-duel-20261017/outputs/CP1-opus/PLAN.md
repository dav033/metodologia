---
plan_id: REQ-CP1
revision: 1
status: draft
spec_ref: SPEC.md
---

# REQ-CP1 — `GET /v1/projects` returns paginated list items (DRAFT)

**Status: DRAFT for owner review.** Not approved, frozen or launched. No owner Q&A happened. Decision gates D1–D3 below are still open, and the assumptions are revisable. Provider, model, account, effort and worker assignments belong to the caller or scheduler and are not decided here.

## Scope

- **Goal:** `GET /v1/projects` returns `{ projects: ProjectListItem[], nextCursor: string | null }`. Each list item has only `id`, `externalKey`, `name`, `revision` and `updatedAt`. The endpoint uses cursor pagination (R1).
- **In scope:** a shared list contract in `@training/contracts`, a keyset-paginated repository query, the route and its HTTP test, a web client that follows the cursor so the existing screens keep working (R2), API documentation with a breaking-change notice, and a release gate for the external MCP consumer (R3).
- **Out of scope:** a pagination UI ("load more") in the web screens, a new DB index or schema migration, changes to the other `/v1/projects/*` routes, the WebSocket, auth or the import contract JSON schema, and any edit to the `trainingApp-mcp` repository (it is outside this workspace).

## Inspected findings (observed facts, with provenance)

- `apps/api/src/app.ts:30`: the route returns `{ projects: repository.list() }` behind `requireAuth`, which accepts a browser session or the MCP bearer token (`apps/api/src/http/auth.ts:66-75`).
- `apps/api/src/repositories/project-repository.ts:33-36`: `list()` runs `SELECT *` ordered by `updated_at DESC` with no tie-breaker. It maps each row through `snapshot()` (lines 14-20), which parses `data_json` into `data` and adds `description`, `schemaVersion` and `createdAt`. **Correction to SPEC:** the response carries the parsed `data` object, not the raw `data_json` column. The intent is the same.
- `list()` has exactly one caller (`app.ts:30`). `apps/api/src/ws/server.ts:14` uses only `getById`.
- `apps/web/lib/api/client.ts:4,24`: `ProjectListItem = Pick<ProjectSnapshot, id|externalKey|name|revision|updatedAt>`, and `listProjects()` is typed as `{ projects: ProjectListItem[] }`.
- Web consumers:
  - `apps/web/components/project-list.tsx:27,58-87` renders `name`, `externalKey`, `revision` and `updatedAt`.
  - `apps/web/components/project-tabs-bar.tsx:23,33-41` uses the **whole** list to prune open tabs whose project no longer exists. If the client sees only the first page (or a partial list), it will silently close tabs for projects on later pages. This is the main R2 risk.
- `apps/api/src/db/database.ts:5,17-53`: schema `user_version` 1 and no index on `updated_at`. Adding one would need a schema-version migration.
- `docs/architecture.md:5-6`: `trainingApp-mcp` is a separate HTTP-only adapter that calls the API with a bearer token. `scripts/check-contract-drift.mjs:6` reads `../trainingApp-mcp/...`, a sibling checkout that is not in this workspace. That makes `npm run contracts:check` unusable as a gate here.
- `packages/contracts/src/generate-schema.ts:7-8` generates only `ProjectImportSchema`. New list schemas do not change `contracts/project-import.v1.schema.json`.
- Existing commands:
  - `npm run test -w @training/api` (`node --import tsx --test test/*.test.ts`) and `npm run test -w @training/contracts`
  - `typecheck` in all three workspaces
  - `npm run lint -w @training/web`
  - The web workspace has no test files.
- Errors: `ZodError` maps to 400 `VALIDATION_ERROR` (`app.ts:68`).

## Unknowns, assumptions and decision gates

- **U1 (blocking for release, not for implementation):** whether `trainingApp-mcp` calls `GET /v1/projects`, and whether it reads `data`, `description`, `createdAt` or `schemaVersion` from list items. It cannot be inspected here.
- **U2:** production project count. This affects whether an index is ever needed (deferred, see A4).
- **D1 (owner decision, gates T7/release):** how to handle the external-consumer transition.
  - **Recommended:** break with notice. One shape for every caller, as R1 says, plus a documented migration path (fetch full snapshots with `GET /v1/projects/:id` or `/by-external-key/:key`) and a confirmed MCP update or notification before deploy.
  - **Alternative:** a temporary opt-in full-snapshot mode or a new endpoint. Choosing it requires **revision 2** of T3/T6.
- **D2 (owner decision, does not change the graph):** page size. **A2:** default `limit` 50, maximum 100. Out-of-range or non-integer values return 400 `VALIDATION_ERROR` rather than being clamped.
- **D3 (owner decision):** whether the web gets a pagination UI. **A3:** no. The web client follows `nextCursor` to the end, so both screens keep receiving the complete list (needed by the tab pruning in `project-tabs-bar.tsx:33`).
- **A1:** the cursor is opaque to clients (for example base64url of `[updatedAt, id]`). Its validity does not depend on the referenced row still existing.
- **A4:** no new index or migration in this revision, given the current single-table SQLite deployment. Revisit if U2 shows large volumes.
- **A5:** if a project is updated while someone is paging, it can move ahead of the cursor and be missed in that traversal, but nothing is duplicated. Both web screens refetch on `PROJECTS_CHANGED_EVENT` and on navigation. This is accepted and will be documented.

## Behavior contract (fixed for implementers)

- **Request:** `GET /v1/projects?limit=<int 1..100, default 50>&cursor=<opaque, optional>`. Auth is unchanged: 401 without a session or a valid bearer token.
- **Response 200:** `{ projects, nextCursor }`.
  - Each item has exactly the keys `id`, `externalKey`, `name`, `revision`, `updatedAt`.
  - Order is `updated_at DESC, id DESC`.
  - `nextCursor` is non-null only when more rows exist.
  - An empty DB returns `{ projects: [], nextCursor: null }`.
  - Without concurrent writes, following cursors until `null` returns every project exactly once.
- **Next page condition:** `updated_at < c.updatedAt OR (updated_at = c.updatedAt AND id < c.id)`. The query fetches `limit + 1` rows and selects only the list columns, never `data_json`.
- **Errors:** a malformed cursor, bad `limit` or undecodable cursor returns 400 with `error.code = "VALIDATION_ERROR"`.
- **Web client:** `listProjects()` keeps returning `{ projects: ProjectListItem[] }` with the complete list. Any page failure, repeated cursor or page-count overrun throws. A partial list is never returned.

## Milestones and tasks

### M1 — List contract and paginated API

- [ ] T1 — Add list item and page schemas to contracts · repo: repository · verify: `npm run test -w @training/contracts` · files: packages/contracts/src/project.ts, packages/contracts/test/project.test.ts · resources: project-list-contract · covers: R1 · kind: implement
- [ ] T2 — Keyset-paginated project listing in the repository · repo: repository · after: T1 · verify: `npm run test -w @training/api` · files: apps/api/src/repositories/project-repository.ts, apps/api/test/repository.test.ts · resources: project-list-contract · covers: R1 · kind: implement
- [ ] T3 — Paginated GET /v1/projects route with HTTP test · repo: repository · after: T2 · verify: `npm run test -w @training/api` · files: apps/api/src/app.ts, apps/api/test/projects-route.test.ts · resources: project-list-contract, projects-list-http-contract · covers: R1, R3 · kind: implement

### M2 — Web screens keep working

- [ ] T4 — Web client follows nextCursor and returns the complete list · repo: repository · after: T3 · verify: `npm run typecheck -w @training/web` · files: apps/web/lib/api/client.ts · resources: projects-list-http-contract, web-project-list-screens · covers: R2 · kind: implement
- [ ] T5 — Manual multi-page regression of project list and tabs bar · repo: repository · after: T4 · resources: web-project-list-screens · covers: R2 · kind: test

### M3 — External consumer notice and release gate

- [ ] T6 — Document the list contract and breaking-change notice · repo: repository · after: T3 · files: docs/api-contract.md · resources: projects-list-http-contract · covers: R3 · kind: docs
- [ ] T7 — Decision-gated release check for trainingApp-mcp (D1) · repo: repository · after: T5, T6 · resources: projects-list-http-contract · covers: R2, R3 · kind: audit

## Task behavior and acceptance

- **T1**
  - Add `ProjectListItemSchema`, a strict object with exactly the five list fields, and `ProjectListPageSchema` (`{ projects, nextCursor: string|null }`, strict), with their inferred types. Export them through `packages/contracts/src/index.ts` (already `export *`).
  - The generated import JSON schema must not change.
  - New tests reject an item that carries `data`.
- **T2**
  - Add `listPage({ limit, cursor })`, which returns `{ projects, nextCursor }` per the contract above. It selects only the list columns and uses deterministic ordering with an `id` tie-breaker.
  - A cursor decode failure raises an error that T3 maps to 400.
  - `list()` may be removed once T3 no longer calls it; there is no other caller.
  - Tests cover: an empty DB, an exact page boundary, equal `updated_at` values, a cursor pointing to a deleted row, and a full traversal visiting every project once.
- **T3**
  - Validate the query and call `listPage`. Respond with the page shape.
  - The new HTTP test starts `createApp` on port 0 with a test config (including `mcpToken`) and checks:
    - the bearer and anonymous (401) paths
    - item keys
    - `nextCursor` chaining
    - 400 `VALIDATION_ERROR` for a bad `limit` or cursor
  - The existing repository test must still pass.
- **T4**
  - Loop `/v1/projects` and then `?cursor=` until `null`, and aggregate the results.
  - Guard against a repeated cursor and a page-count overrun by throwing.
  - Keep the call sites in `project-list.tsx:27` and `project-tabs-bar.tsx:23` unchanged.
  - Lint and typecheck must pass.
- **T5**
  - With more projects than one page (create them, or temporarily use a small `limit` in the client), the `/projects` list shows all of them with name, key, revision and relative time.
  - Open tabs for projects that are not on the first page stay open after a refresh.
  - Deleting a project removes its tab.
- **T6**
  - `docs/api-contract.md` describes the query parameters, response shape, ordering, cursor opacity, errors, the A5 limitation, and a breaking-change notice with the full-snapshot migration path for MCP callers.
- **T7**
  - Gate: the owner records the D1 choice.
  - Before deploy, either `trainingApp-mcp` usage of `GET /v1/projects` is confirmed compatible or updated, or its owner has acknowledged the notice in T6.
  - If D1 is not "break with notice", stop and open revision 2. Nothing is deployed by this plan.

## Interfaces

- **IF-1 Project list contract schemas.** Producer T1. Consumers T2, T3, T4. Integration task T3.
- **IF-2 HTTP `GET /v1/projects` page response.** Producer T3. Consumers T4, T6, T7. Integration task T5.

## Verification (planned, none executed)

- **Static:**
  - `npm run typecheck -w @training/contracts`
  - `npm run typecheck -w @training/api`
  - `npm run typecheck -w @training/web`
  - `npm run lint -w @training/web`
- **Functional:**
  - `npm run test -w @training/contracts` (new cases created by T1)
  - `npm run test -w @training/api` (repository cases created by T2)
- **Integration:** `npm run test -w @training/api`, including `apps/api/test/projects-route.test.ts` created by T3.
- **Regression:**
  - the existing `apps/api/test/repository.test.ts` keeps passing
  - the import JSON schema and its sha256 sidecar are unchanged
  - T5 manual web checks
- **Product:** T5 (web) and T7 (external consumer gate) are manual checks. A green test does not prove that R3 is accepted.
- `npm run contracts:check` is not used, because it needs the absent sibling `../trainingApp-mcp`.

## Risks

- **Plausible risk:** tab pruning closes tabs if the client returns only a first or partial page (`project-tabs-bar.tsx:33`). Mitigated by T4's all-or-throw behavior and checked in T5.
- **Plausible risk:** the external MCP consumer breaks silently (U1). Mitigated by T6 and T7 and gated by D1.
- **Plausible risk:** full traversal costs N/limit requests and still has no index (A4). Acceptable for the current scale, which is unverified (U2).
- **Fact:** the current list order has no tie-breaker (`project-repository.ts:34`). Fixed by T2's ordering.

## Self-review note

This is a same-context semantic self-review, not an independent approval. Every requirement is covered: R1 by T1–T3, R2 by T4, T5 and T7, and R3 by T3, T6 and T7. All `after` edges point to earlier or same-milestone tasks, and the graph has no cycles. Estimates are unverified guesses; no comparable execution history was available.
