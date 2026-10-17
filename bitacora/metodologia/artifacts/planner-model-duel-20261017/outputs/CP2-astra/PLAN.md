# REQ-CP2 — PostgreSQL persistence migration

DRAFT · Revision 1 · Spec: SPEC.md · Repository: repository → ./repo

Apply the supplied elicitation, WBS and adversarial-review skills. This is a source-backed draft, not authorization to implement or deploy. Only file inspection was performed; tests, builds and planner validation were not run. Estimates are provisional task estimates without comparable execution history.

## Scope and evidence

Preserve all project rows, asset metadata and asset files; preserve HTTP/WebSocket contracts and revision semantics; provide verified migration, PostgreSQL backup/restore and compatible deployment rollback. Exclude frontend redesign, contract version changes, unrelated infrastructure and changes to the unavailable MCP repository.

Inspected findings:

- `apps/api/src/db/database.ts:7–58`: SQLite WAL, schema version 1, JSON validity CHECK, unique external keys and asset paths, and cascading project/asset foreign key. Readiness performs SQLite integrity/schema checks.
- `apps/api/src/repositories/project-repository.ts:52–89`: import/create/update use synchronous transactions. Revision comparison precedes no-op detection; unchanged content preserves revision and timestamps. Comparison uses serialized JSON text.
- `apps/api/src/app.ts`, `src/server.ts`, `src/ws/server.ts` and `src/services/asset-service.ts` under `apps/api/`: database calls are synchronous throughout HTTP, startup, upgrades and asset operations. Upload cleanup depends on catching metadata insertion failure.
- `apps/api/src/backup.ts:10–22`: database snapshot precedes an uncoordinated asset copy; metadata files are written after checksum enumeration.
- `ops/ec2/deploy.ps1:42–44`: candidate code performs the predeployment backup; activation checks container status, not readiness. `ops/ec2/rollback.ps1:5–6` switches code and explicitly does not restore data.
- `apps/web/lib/api/client.ts`, `apps/web/hooks/use-project-sync.ts`, project pages and `components/project-list.tsx`: browser consumers depend on snapshot fields, 409/currentRevision, asset URLs and revision/deletion events.
- `packages/contracts/src/project.ts`, `packages/contracts/test/project.test.ts`, `docs/api-contract.md`: strict import/asset schemas and existing contract tests. `apps/api/test/repository.test.ts` covers only basic revision persistence and stale writes.
- Inspected API/root/contracts/web package manifests, API/root TypeScript configuration, lockfile entries, Dockerfile, Compose, environment example, deployment/preflight scripts, Caddy snippet, auth/errors/event hub, architecture/deployment docs and ignore files.
- `scripts/check-contract-drift.mjs` requires sibling `trainingApp-mcp`, which is outside this cell. External compatibility is unverified; that command is not a local acceptance gate.
- No AGENTS.md was found in the permitted tree. The supplied schema/example were inspected for structure only.

## Decisions and proposed assumptions

T1 is an execution prerequisite, not an invented decision record. No owner answers exist.

- **D1 — Availability, blocking:** define acceptable read/write interruption, request draining, client retry/session behavior and the maximum cutover interval. Proposed bounded maintenance with a single authoritative writer simplifies migration, but is NOT accepted and does not satisfy a literal uninterrupted-availability requirement. If uninterrupted writes are mandatory, revise this draft with durable change capture/replay and routing tasks before implementation.
- **D2 — Rollback, blocking:** proposed policy permits SQLite rollback only before PostgreSQL accepts writes; afterwards rollback uses a PostgreSQL-compatible release against current data. Restores use verified database/assets bundles. If return to SQLite after new writes is required, add verified reverse migration/reconciliation before execution.
- **D3 — Recovery/environment, blocking:** establish PostgreSQL version/connectivity/TLS requirements, migration privileges, backup location/retention, recovery objectives and supported rollback releases. No hosting service or execution assignment is selected.
- **D4 — Source inventory:** production volume, encoding compatibility, all writers, actual schema versions, asset completeness and external consumers are unknown. Inventory must resolve these before operational work; no silent coercion, dropped records or claimed external compatibility.
- Proposed representation: preserve IDs, JSON text and timestamp strings exactly; retain database JSON validation and existing constraints. Avoid JSONB normalization and timestamp reformatting because they can alter hashes or no-op behavior. Validate numeric range and encoding before conversion.
- Proposed operational boundary: one serving API process, matching the inspected in-memory session/event hub. Adding replicas or zero-interruption process replacement requires additional session/event design.

## Milestones and tasks

### M1 — Establish the migration contract

Acceptance: decision and inventory records identify the executable migration/recovery branch, or explicitly keep dependent work blocked.

- [ ] T1 — Resolve persistence and operational gates · repo: repository · covers: R1, R2, R3 · kind: research

Produce `docs/persistence-migration.md`: D1–D4 outcomes, compatibility matrix, source inventory procedure, representation rules, cutover abort conditions and rollback boundary. Capture HTTP/import/no-op/error/event behavior from inspected sources. Do not choose downtime or recovery tolerances on the owner's behalf. If answers are unavailable, retain unresolved gates; T2–T8 cannot begin on assumptions alone.

Verification: manual product review expects explicit decisions or unresolved blockers, with affected tasks identified.

### M2 — Implement compatible PostgreSQL persistence

Acceptance: PostgreSQL preserves schema and repository invariants, and every runtime database consumer awaits completion.

- [ ] T2 — Add PostgreSQL connections and versioned schema · repo: repository · after: T1 · verify: `npm run test -w @training/api` · covers: R1, R2 · kind: implement

Add an asynchronous pool/transaction module and transactional, serialized migrations with a version ledger. Preserve text fields, uniqueness, FK cascade and JSON validity; reject newer schemas. Require explicit connection configuration without SQLite fallback; redact credentials. Add database constraint, migration rollback and repeated/concurrent initialization tests. Keep SQLite dependencies only for legacy migration/fixtures.

- [ ] T3 — Port repositories with atomic revision semantics · repo: repository · after: T2 · verify: `npm run test -w @training/api` · covers: R2 · kind: implement

Use one checked-out connection per transaction. Serialize operations on the same external key, including absent-key imports; check revision before comparing content. New projects start at revision 1; changed updates increment once; no-ops preserve timestamps/revision. Stale writes return the committed current revision. Preserve missing-record behavior, duplicate-create error mapping, import flags and descending updated-time ordering. Release connections and roll back every failure. Convert asset metadata operations and extend concurrency tests using separate connections.

- [ ] T4 — Await storage across API and asset consumers · repo: repository · after: T3 · verify: `npm run typecheck` · covers: R2, R3 · kind: implement

Await HTTP handlers, readiness, startup/shutdown, asset methods and WebSocket existence checks. Keep response/status/auth/CORS/CSRF/event shapes unchanged; publish only after commit and never on no-op/failure. Preserve failed-upload file cleanup and prevent newly asynchronous upload/delete races from leaving referenced files missing. Introduce the coordinated mutation barrier needed by T6: shared PostgreSQL advisory locking spans each mutation's SQL and filesystem work; backup takes the exclusive counterpart. Readiness returns 503 for inaccessible/unsupported storage; shutdown drains requests before closing the pool. Test rejected promises, failed commits, asset races and socket disconnects during lookup.

### M3 — Provide verified migration and recovery

Acceptance: a consistent SQLite source imports without content loss; PostgreSQL backup/restore produces matching database and asset inventories.

- [ ] T5 — Build repeatable migration and content verification · repo: repository · after: T4 · verify: `npm run test -w @training/api` · covers: R1 · kind: implement

Read a consistent SQLite backup captured after the D1-approved writer fence/drain; never copy only the live main file or migrate the source in place. Validate schema/integrity/FKs, source values and every asset's path, byte size and SHA-256. Import projects then assets into an empty isolated PostgreSQL target transaction; preserve all columns. Hash each row as a fixed-column, type-preserving JSON array encoded in UTF-8, sorted by primary-key bytes; calculate per-table counts and aggregate SHA-256. Preserve raw JSON/timestamp text. Compare source and target manifests and API snapshots; mismatch fails closed. Interrupted runs roll back or can be repeated only against an explicitly disposable target; never truncate an unknown database. Test empty, Unicode, malformed/incompatible, missing-file, interruption, duplicate-target and tampered-content cases.

- [ ] T6 — Implement consistent backup and guarded restore · repo: repository · after: T5 · verify: `npm run test -w @training/api` · covers: R1, R3 · kind: implement

Coordinate PostgreSQL dump and asset copying under T4's exclusive mutation barrier. Include store/schema/release versions, row manifests and asset hashes; write metadata before checksums and publish a completion marker last. Failure leaves an unusable partial bundle and releases locks. Restore only to an empty isolated target, validate format/version/checksums/counts/content, then test API reads and assets before any switch. Reject corrupt/incomplete bundles and incompatible releases. Distinguish legacy SQLite bundles, PostgreSQL restores and code rollback; never restore stale SQLite after PostgreSQL writes. Recovery objectives remain D3-gated.

### M4 — Integrate deployment and demonstrate acceptance

Acceptance: reviewed deployment/recovery procedures fail closed; isolated rehearsals substantiate R1–R3 without claiming production migration or external compatibility.

- [ ] T7 — Update deployment and rollback safeguards · repo: repository · after: T6 · covers: R1, R2, R3 · kind: implement

Update Docker/Compose/env configuration and deployment/preflight/rollback scripts for explicit PostgreSQL connectivity, compatible database tools and persistent asset/backup paths. Use the currently serving store's compatible backup tool before migration, not an incompatible candidate backup. Implement the D1-approved fence/drain → snapshot → import/verify → candidate readiness/API probes → route switch → enable writes sequence. Persist cutover phase and first PostgreSQL-write boundary; failures retain the authoritative store. Verify release/store compatibility before symlink or routing changes. Document session/WebSocket effects and prohibit concurrent writers to different stores. Do not execute remote scripts as part of this task's local verification.

- [ ] T8 — Add acceptance rehearsals and consumer regressions · repo: repository · after: T7 · verify: `npm run test -w @training/api` · covers: R1, R2, R3 · kind: test

Add isolated migration/recovery and HTTP/WebSocket suites. Exercise two concurrent changed writes at one revision, concurrent imports, stale no-op requests, commit failure, assets and delete races, readiness outages, restart persistence, backup tampering and deployment-stage failure injection. Rehearse pre-write SQLite rollback and post-write PostgreSQL-compatible code rollback, preserving writes; restore a bundle into an isolated target and compare manifests. Exercise the inspected browser flows and bearer-token API contract; record the unavailable MCP consumer as unverified. Measure interruption/recovery only during the future rehearsal and compare with D1/D3; exceeding bounds blocks acceptance. Record evidence in `docs/persistence-verification.md`. No production switch is part of this draft delivery.

## Dependencies, verification and risks

Dependency chain: T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8. This orders shared persistence contracts and files. IF-1 defines asynchronous storage; IF-2 defines the mutation barrier; IF-3 defines migration/recovery manifests.

All commands are planned from the repository root. Existing package scripts support `npm run typecheck`, `npm run test -w @training/api` and `npm run test -w @training/contracts`. New tests are explicitly attributed to their creating tasks in JSON. Future tests require prepared dependencies/contracts artifacts and disposable PostgreSQL; absence must fail setup rather than silently skip. Passing tests does not resolve product decisions or prove production acceptance.

Semantic self-review, not independent approval:

- **Fact, high impact:** synchronous transaction semantics span callers; partial conversion can acknowledge before commit. Provenance: project repository lines 64–89 and app handlers. Correction: T3 → T4 plus concurrency/event tests.
- **Plausible risk, high:** deletion between database backup and asset copy can make a bundle incomplete. Provenance: backup lines 10–13 and asset deletion code. Correction: shared mutation barrier, manifest checks and restore rehearsal.
- **Demonstrated guard gap, high:** rollback accepts a release SHA without checking its storage compatibility. Provenance: rollback lines 3–6. Correction: explicit pre/post-write boundary and fail-closed compatibility checks.
- **Product decision, blocking:** availability and post-write SQLite rollback cannot be inferred from R1–R3. Correction: T1 gates and replan conditions; no claimed owner approval.
- **Plausible risk, medium:** PostgreSQL coercion or JSON normalization changes byte hashes/no-op results. Provenance: repository lines 66–79 and SQLite text schema. Correction: preserve text and reject incompatible inputs explicitly.
- **Fact, medium impact:** the supplied test coverage and unavailable MCP checkout cannot establish full compatibility. Correction: T8 adds local coverage while retaining the external evidence gap.

R1 is covered by schema preservation, verified migration, restore and rehearsal; R2 by repositories, all consumers, deployment guards and regression tests; R3 by coordinated backups, restore, compatible rollback and recovery rehearsal. None is accepted yet.
