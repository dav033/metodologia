---
plan_id: REQ-CP1
revision: 1
status: draft
spec_ref: SPEC.md
---

# Paginated project summaries

Draft only. No files changed, tests/builds executed, external contacts made, or validation results claimed. The supplied Planner skills were applied through inspection and same-context self-review. All verification below is planned.

## Scope and evidence

Implement R1: authenticated `GET /v1/projects` returns `{ projects, nextCursor }`, with exactly five fields per project: `id`, `externalKey`, `name`, `revision`, `updatedAt`. Preserve both web consumers for R2. For R3, prepare migration guidance and require evidence of advance notice before the changed endpoint can be released.

Inspected findings, with repository-relative provenance:

- `apps/api/src/app.ts:30` wraps `repository.list()` without pagination. `apps/api/src/repositories/project-repository.ts:14-35` selects every column and parses each `data_json` into snapshot `data`; `data_json` itself is not a response field.
- `apps/api/src/db/database.ts:25-35` provides the required metadata columns. The current list orders only by `updated_at DESC`; ties have no explicit ordering. There is no matching pagination index.
- `apps/web/lib/api/client.ts:3-24` declares summary items but assumes one response contains every project.
- `apps/web/components/project-list.tsx:27` displays that entire result. `apps/web/components/project-tabs-bar.tsx:23-42` also assumes completeness and removes persisted tabs absent from it. Its picker uses the same collection.
- Project routes, `apps/web/lib/open-tabs.ts`, and `apps/web/hooks/use-project-sync.ts` were inspected. Editing and synchronization fetch full snapshots separately; their contracts must remain intact.
- `packages/contracts/src/project.ts` exports snapshot/import schemas, but no list-page schema. Its existing tests cover imports. `apps/api/test/repository.test.ts` covers revision conflicts, not listing.
- Root/workspace package scripts and TypeScript configuration were inspected. API/contracts tests use Node with `tsx`; the web has `node --test` and no existing test files found.
- `docs/architecture.md` identifies the separate MCP HTTP adapter. `docs/api-contract.md` and `apps/api/src/http/auth.ts` describe/implement cookie and bearer authentication.
- `scripts/check-contract-drift.mjs` compares only import-schema files and accesses the unavailable sibling repository. It cannot establish list-endpoint compatibility and is excluded from this cell's checks.
- Deployment documentation, Dockerfile, Compose and Netlify configuration were inspected. API and web have separate release surfaces. No applicable `AGENTS.md` was found within the supplied directories.

Excluded: changes to snapshot/import/mutation/WebSocket contracts, external repository edits, deployment, external messaging, new pagination UI, database migrations and performance guarantees. Indexing remains a follow-up if separately justified.

## Proposed decisions and gates

These are proposals, not owner decisions. T1 remains incomplete until D1–D3 are resolved through genuine supplied evidence; dependent implementation must not infer approval.

- **D1 — Pagination contract:** recommend optional `limit` and `cursor`; default limit 50, maximum 100. A supplied limit must be a single canonical positive decimal integer within range. Reject empty, repeated, malformed or oversized values with HTTP 400 `VALIDATION_ERROR`. Ignore unrelated query keys, preserving existing tolerance.
  Order by `updated_at DESC, id DESC` using SQLite's existing binary text ordering. Use a strict exclusive tuple boundary, select only summary columns, and fetch `limit + 1`. Emit a cursor from the last returned item only when the extra row exists; otherwise return `null`.
  Recommend a bounded, canonical base64url JSON cursor containing version 1, canonical UTC ISO `updatedAt`, and nonempty `id` of at most 100 characters. Reject cursors over 1024 characters, malformed encodings/payloads and unsupported versions. The cursor is position data, not authorization.
- **D2 — Web behavior and consistency:** recommend retaining the current all-projects experience by gathering pages sequentially before publishing a complete result. Pagination is a live traversal, not a database snapshot: concurrent updates can move unseen rows ahead of the boundary. Completeness is guaranteed for an unchanged dataset. Reject partial failures/repeated cursors, deduplicate by ID, retain the highest revision, and ignore superseded refresh completions. Before pruning an absent saved/active tab, confirm deletion through the detail endpoint; only HTTP 404 permits removal.
- **D3 — Migration:** recommend a coordinated API/web cutover with an explicit browser refresh policy and advance notice to external consumers. Removed snapshot fields require detail requests; consumers expecting all projects must follow cursors. MCP usage, other external consumers, notice recipients/channel/lead time, and cutover arrangements remain unknown. If compatibility requires a transition endpoint or versioning, revise this draft before implementation. Local documentation alone is not proof of notice.

## Milestones

### M1 — Resolve decisions and define the shared contract

Acceptance: D1–D3 have evidenced dispositions, and an additive shared summary/page contract expresses the selected behavior without changing imports or snapshots.

- [ ] T1 — Resolve pagination and migration decisions · repo: repository · covers: R1, R2, R3 · kind: research
  Record D1–D3, the known consumer inventory, unresolved external usage and the required notice evidence in API/migration documentation. Completion requires actual decision evidence; otherwise retain the gate. Verify manually against SPEC and inspected consumers.
- [ ] T2 — Define summary and page schemas · repo: repository · after: T1 · covers: R1, R2 · kind: implement · verify: `npm run test -w @training/contracts`
  Add exported summary/page schemas and inferred types. Require exactly the five summary fields and `nextCursor: string | null`; test rejection of snapshot extras and missing cursors. Preserve import/snapshot schemas and generated import artifacts.

### M2 — Implement bounded API pagination

Acceptance: authenticated requests return bounded summaries with deterministic continuation, correct terminal cursors and controlled validation errors.

- [ ] T3 — Implement repository keyset listing · repo: repository · after: T2 · covers: R1 · kind: implement · verify: `npm run test -w @training/api`
  Accept a validated limit and optional decoded boundary; implement D1's projection, ordering, exclusive predicate and lookahead. Do not call the snapshot mapper. Test empty, exact-boundary, multiple-page and tied-timestamp datasets, continuation after boundary-row deletion, and independence from project-data parsing.
- [ ] T4 — Expose and validate the paginated endpoint · repo: repository · after: T3 · covers: R1 · kind: implement · verify: `npm run test -w @training/api`
  Authenticate before parsing query input. Encode/decode bounded cursors, convert invalid input into the existing validation envelope, and return the shared page shape. Add real HTTP tests for cookie/bearer access, unauthorized access, validation boundaries and traversal. Preserve detail/import/mutation routes.

### M3 — Preserve web behavior and verify integration

Acceptance: both screens retain access to projects beyond the first page; partial/stale refreshes cannot erase saved tabs; actual browser/API checks cover the selected contract.

- [ ] T5 — Adapt complete-list loading and tab reconciliation · repo: repository · after: T4 · covers: R2 · kind: implement · verify: `npm run test -w @training/web`
  Consume the shared summary type while retaining `listProjects()`'s complete `{ projects }` result for existing callers. Establish the session once per load, follow encoded cursors until `null`, apply D2's deduplication/error rules, and publish only the completed collection. Guard overlapping refreshes and confirm missing tabs through detail reads. Add focused client/state tests using Node plus `tsx`; declare the web test dependency and update its script/lockfile.
- [ ] T6 — Verify pagination and screen regressions · repo: repository · after: T5 · covers: R1, R2 · kind: audit · verify: `npm run typecheck`
  Run the scoped suites and static checks after building contracts. Record actual results in a new verification document. Exercise the real web/API with at least 101 projects, tied timestamps, a saved tab and a direct link beyond page one; verify picker, detail editing, create/delete refresh, later-page failure, and superseded refresh behavior. Automated suites do not replace these product checks.

### M4 — Establish external migration notice evidence

Acceptance: migration guidance matches the verified implementation, and evidence demonstrates advance notice under D3; absent evidence keeps R3 and this milestone incomplete.

- [ ] T7 — Finalize migration guidance and audit notice evidence · repo: repository · after: T6 · covers: R3 · kind: docs
  Document the before/after envelope, removed fields, cursor iteration, validation, live consistency, detail-fetch replacement and coordinated cutover prerequisites. Audit owner-supplied evidence identifying affected consumers, delivered notice and timing before the proposed change. Do not send notices, deploy, or infer MCP compatibility. Record remaining external validation separately from notice delivery.

## Verification and traceability

All commands are planned from the repository root. `npm run build -w @training/contracts` precedes API tests because package runtime exports resolve to `dist`. Existing scripts support contracts/API tests and workspace typechecking. T5 supplies the web test harness; new tests are identified with `created_by` in JSON.

- R1: T1 → T2 → T3 → T4 → T6; schema, repository and authenticated HTTP evidence.
- R2: T1 → T2 → T3 → T4 → T5 → T6; client/state tests plus actual screen checks.
- R3: T1 → implementation/verification chain → T7; decision evidence, migration instructions and auditable advance notice.

Declared interfaces cover shared schemas, repository pagination and the HTTP page consumed by the web. Dependencies also order all shared-file changes.

## Risks and semantic self-review

- **Demonstrated defect, high:** current endpoint violates R1 by returning full snapshots (`app.ts:30`, `project-repository.ts:14-35`). Correction: metadata projection and explicit page contract.
- **Plausible risk, high:** first-page-only adaptation would prune valid saved tabs (`project-tabs-bar.tsx:23-42`). Correction: complete-load publication, failure preservation and detail-confirmed deletion.
- **Plausible risk, medium:** timestamp ties and concurrent updates can skip or duplicate entries. Correction: unique tuple ordering, fixed-dataset traversal tests, and explicitly limited live-consistency guarantees under D1/D2.
- **Product decision, high:** external consumer usage and transition arrangements are unverified (`SPEC.md`, `docs/architecture.md`). Correction: D3 and T7 remain gates; import-schema equality cannot substitute for endpoint evidence.
- **Plausible risk, medium:** gathering every page retains total client work and adds requests; missing index means bounded responses do not imply bounded database scanning. No measured scalability claim is made.

Estimates are provisional task-local judgments including verification. No comparable execution history is available; external waiting time is unknown and excluded. This is a same-context review, not independent approval. Host validation remains pending.
