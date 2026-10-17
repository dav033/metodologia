# REQ-CP1 — Paginated project list

Draft, revision 1. Planning only; no implementation, tests, builds, validator, approval or launch performed.

Scope: R1 introduces metadata-only cursor pages; R2 preserves existing project discovery, tabs and editing; R3 requires notice before an externally breaking change becomes live. External adapter implementation, deployment, authentication redesign, import-schema changes and database migrations are excluded.

## Inspected findings and provenance

Repository-relative references:

- `apps/api/src/app.ts:30` returns `{projects: repository.list()}` behind existing authentication. Lines 37–57 retain separate snapshot/detail and mutation contracts; lines 65–72 define error responses.
- `apps/api/src/repositories/project-repository.ts:14–35` selects every column, parses `data_json` into snapshot `data`, and orders only by `updated_at DESC`.
- `apps/api/src/db/database.ts:25–35` provides metadata columns and unique project IDs. No pagination index exists; this draft proposes no migration or measured performance claim.
- `apps/web/lib/api/client.ts:3–24` already defines the five-field `ProjectListItem`, but fetches a single unpaginated response.
- `apps/web/components/project-list.tsx:27–46` expects the complete list. `apps/web/components/project-tabs-bar.tsx:23–45` treats absence from that list as deletion, refreshes names, and restores directly opened tabs. Its picker also needs projects beyond page one.
- `apps/web/lib/open-tabs.ts`, project routes and `apps/web/hooks/use-project-sync.ts:24–34` show persisted tabs and separate snapshot-based editing.
- `packages/contracts/src/project.ts:60–73`, its index, generator and existing tests were inspected. The generated JSON schema describes imports, not list responses.
- `docs/architecture.md` identifies `trainingApp-mcp` as an external HTTP adapter. Its actual endpoint usage, snapshot assumptions, cursor support and contacts remain unknown.
- Root/workspace package manifests, TypeScript configuration, API repository tests, authentication/configuration, API/deployment docs and `scripts/check-contract-drift.mjs` were inspected. Commands below exist in package scripts. `contracts:check` accesses another repository and is excluded.

## Proposed assumptions and decision gates

D1 — Pagination contract, unresolved. Recommend:
- Optional `limit`: default 50, maximum 100; accept only one decimal integer string in 1–100. Reject arrays, objects, repeated values and invalid values.
- Optional `cursor`: one nonempty base64url string, maximum 2048 characters, encoding strict `{v:1, updatedAt, id}`. Validate canonical ISO timestamp and nonempty ID; reject malformed encoding, unsupported versions and extra fields.
- Authenticate first; invalid pagination returns HTTP 400 using the existing `VALIDATION_ERROR` envelope.
- Order by `updated_at DESC, id DESC` using SQLite's existing text comparison. Seek strictly below the cursor tuple, bind SQL parameters, fetch `limit + 1`, return at most `limit` items. Emit a cursor from the last returned item only when an extra row exists; otherwise `nextCursor: null`.
- Each item contains exactly `id`, `externalKey`, `name`, `revision`, `updatedAt`. Never select or parse `data_json` for listing.
- Empty results return `{projects: [], nextCursor: null}`. A deleted anchor remains usable because seeking uses values, not anchor lookup.
- Pagination is a live traversal, not a database snapshot. Concurrent updates can move rows; completeness and no duplicates are guaranteed for unchanged datasets only.
- Preserve the web helper's complete-list behavior by collecting all pages before resolving. No new pagination UI.

T1 must resolve D1 before T2–T5 begin. These are proposals, not owner decisions. A different pagination or UI policy requires revising downstream criteria.

D2 — External transition, unresolved. Recommend a documented, noticed change to the existing endpoint, with detail GETs replacing snapshot reads and cursor traversal replacing single-response enumeration. Actual audience, delivery channel, notice lead time, effective release and required acknowledgement must be established from authorized evidence. If coexistence/versioning is required instead, revise this draft before implementation; no speculative legacy mode is included.

T6 remains incomplete and R3 unaccepted without actual notice evidence satisfying D2. Draft documentation alone is not notice. This plan authorizes no external messages or release.

## Milestones and tasks

### M1 — Settle and publish the list contract

Acceptance: D1 is resolved without silently filling product gaps; the shared page contract and external transition requirements are recorded.

- [ ] T1 — Resolve pagination and transition decisions · repo: repository · covers: R1, R2, R3 · kind: research · files: docs/project-list-migration.md · resources: project-list-contract, external-list-transition

  Record D1 and D2 proposals, verified local consumers, missing external evidence and downstream gates. Obtain authorized decisions in a future workflow; do not infer external compatibility. D1 must be resolved to complete this task; unresolved D2 remains an explicit release gate. Manual product verification expects decision provenance and a named condition for every remaining gate.

- [ ] T2 — Define shared project list schemas · repo: repository · after: T1 · covers: R1, R2 · kind: implement · verify: `npm run test -w @training/contracts` · files: packages/contracts/src/project.ts, packages/contracts/test/project-list.test.ts, docs/api-contract.md · resources: project-list-contract

  Add exported strict list-item and page schemas/types through the existing index export. Preserve import/snapshot schemas and generated import artifacts. Document the resolved query, cursor, response, concurrency and error rules. New contract tests reject snapshot fields and invalid page shapes; typecheck the contracts workspace.

### M2 — Implement and verify both sides

Acceptance: bounded metadata pages work through authenticated HTTP; both screens retain complete-list behavior and snapshot editing remains intact.

- [ ] T3 — Implement metadata keyset pagination · repo: repository · after: T2 · covers: R1 · kind: implement · verify: `npm run build -w @training/contracts && npm run test -w @training/api` · files: apps/api/src/repositories/project-repository.ts, apps/api/src/app.ts, apps/api/test/projects-pagination.test.ts · resources: project-list-contract

  Implement D1's explicit column projection, tuple seek, lookahead and cursor validation. Preserve authentication precedence, detail snapshots and mutation behavior. New repository/route cases cover empty lists, page boundaries, tied timestamps, deleted anchors, invalid queries and metadata-only output. No offset pagination or full-snapshot mapping.

- [ ] T4 — Preserve complete web project discovery · repo: repository · after: T3 · covers: R2 · kind: implement · verify: `npm run build -w @training/contracts && npm run test -w @training/api` · files: apps/web/lib/api/client.ts, apps/web/components/project-list.tsx, apps/web/components/project-tabs-bar.tsx, apps/api/test/projects-client.test.ts · resources: project-list-contract, web-complete-project-list

  Keep `listProjects()` returning `{projects}` to both consumers. Establish a session once per traversal, validate each page and encode cursors in requests. Accumulate privately until explicit null; reject page errors, malformed pages and repeated cursors without publishing partial state. Deduplicate by ID, retaining the higher revision and first encounter position. Only the latest refresh may update a component. Preserve previous list/tabs on failure; partial enumeration must never imply deletion. Test the real web helper with controlled fetch responses using the existing API TypeScript test runner, without new test dependencies.

- [ ] T5 — Verify HTTP and screen integration · repo: repository · after: T4 · covers: R1, R2 · kind: test · verify: `npm run build -w @training/contracts && npm run test -w @training/api` · files: apps/api/test/projects-http.test.ts · resources: project-list-contract, web-complete-project-list

  Add real HTTP tests using isolated temporary SQLite and an ephemeral local server, with cleanup. Exercise browser-cookie and bearer authentication, unauthorized requests, complete multi-page traversal and unchanged detail/revision behavior. Plan static checks with `npm run typecheck` and `npm run lint -w @training/web`.

  Product verification uses more than 100 projects, tied timestamps, and a saved/directly opened tab outside page one: every project remains discoverable, the picker opens later projects, names refresh, real deletions remove tabs, and later-page failure retains prior state. Verify create/open/edit/save/delete flows. Automated success does not substitute for these screen checks.

### M3 — Establish external transition readiness

Acceptance: migration guidance matches verified behavior; R3 has actual notice evidence or remains explicitly blocked.

- [ ] T6 — Document migration and verify notice evidence · repo: repository · after: T5 · covers: R3 · kind: docs · files: docs/api-contract.md, docs/project-list-migration.md · resources: external-list-transition, project-list-contract

  Document removed snapshot fields, bounded default results, cursor traversal, terminal null, error handling, live-list limits and detail-fetch migration. Record actual D2 decisions and notice evidence before any future release changes the endpoint. Notice must identify the breaking behavior and effective transition; evidence must satisfy the agreed recipient/channel/timing conditions. Missing external access or delivery evidence keeps this task incomplete. Preparing guidance does not authorize sending it.

## Coverage, dependencies and verification

R1: T1 → T2 → T3 → T5. R2: T1 → T2 → T4 → T5. R3: T1 → T6, with D2 and actual notice as explicit gates. Task order also prevents overlapping contract/document changes. IF-1 owns the page contract; IF-2 owns the complete-list web adapter.

All checks are planned. New tests are identified by `created_by` in JSON and are not existing evidence. Commands run from the repository root in future implementation. No comparable execution history is available; minute values are provisional task estimates, excluding external waiting.

## Risks and semantic self-review

- Fact: tabs infer deletion from list absence (`project-tabs-bar.tsx:31–35`). Correction: publish only a complete successful traversal.
- Plausible risk, high: external consumers depend on snapshots or exhaustive single responses (`SPEC.md`, `docs/architecture.md`). Correction: D2 plus T6 notice evidence; no compatibility claim from local tests.
- Product decision: page sizes, cursor format, concurrency guarantee and transition strategy are unresolved. Correction: D1/D2 gates, not implementer discretion.
- Plausible risk, medium: concurrent writes move rows across cursors. Correction: document live traversal and test stable datasets separately; deduplication cannot prove snapshot completeness.
- Plausible risk, medium: collecting all pages preserves behavior but keeps total browser memory and traversal work proportional to project count. This is a revisable preservation strategy, not a performance measurement.
- Fact: current tests cover revision conflicts and import validation, not pagination or browser behavior. Correction: T2–T5 add focused coverage and explicit product checks.

Same-context semantic self-review checked requirement coverage, contract ownership, dependency order and evidence provenance. It is not independent approval; deterministic validation is left to the host.
