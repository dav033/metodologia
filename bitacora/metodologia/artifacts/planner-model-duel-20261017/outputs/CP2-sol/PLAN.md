# REQ-CP2 — PostgreSQL persistence migration

DRAFT, revision 1. Standard planning with data-loss and availability risks. No approval, implementation, deployment, tests, builds, or validator execution occurred. Repository role: `repository` → `./repo`. Authoritative requirement: `SPEC.md`.

## Scope and evidence

Preserve every project, asset record, asset file, revision, identifier, timestamp, and client-visible contract while moving the API store to PostgreSQL. Provide verified migration, consistent backups, restore, and rollback. Exclude frontend redesign, contract-version changes, unrelated infrastructure, and retirement of SQLite recovery artifacts before the rollback window closes.

Inspected findings:

- **Fact:** `apps/api/src/db/database.ts:7-58` uses synchronous SQLite, WAL, `user_version=1`, JSON validation, unique keys, and cascading asset metadata deletion.
- **Fact:** `apps/api/src/repositories/project-repository.ts:64-89` checks revisions before comparing serialized JSON. No-ops preserve revision/timestamps; changed writes increment once. Transactions commit before HTTP handlers publish events.
- **Fact:** `apps/api/src/app.ts`, `server.ts`, `services/asset-service.ts`, and `ws/server.ts` consume synchronous persistence. Asset insertion failures remove the newly written file; asynchronous conversion must retain that compensation.
- **Fact:** `apps/web/lib/api/client.ts` and `apps/web/hooks/use-project-sync.ts` depend on snapshot shapes, 409/currentRevision, asset URLs, and revision events. `packages/contracts/src/project.ts` defines validation and snapshot types.
- **Fact:** `apps/api/src/backup.ts` takes a consistent database copy, then separately copies assets. Its checksum list precedes writing release/schema/manifest metadata.
- **Fact:** `ops/ec2/deploy.ps1:42` invokes the incoming release's backup before switching code. `ops/ec2/rollback.ps1:5-6` switches code without restoring data. Compose mounts shared files; the Docker image lacks PostgreSQL backup utilities.
- **Fact:** Existing API tests cover one sequential revision-conflict case. Package scripts provide API test/build/typecheck and workspace typecheck commands. API TypeScript configuration excludes tests.
- **Unknown:** Live data size, corruption, traffic, database endpoint/version, recovery objectives, and external MCP compatibility. Architecture documentation describes the MCP adapter, but its source is outside this cell and was not inspected. `scripts/check-contract-drift.mjs` requires that absent sibling, so it is not a local verification gate.

Also inspected package manifests/lockfile, authentication, event hub/errors, contract tests, deployment documentation/preflight, example environment files, TypeScript configuration, and the supplied planner schema/example. No repository instructions or project decision logs were found in the cell.

## Decision gates and proposed assumptions

T1 prepares a decision packet; it cannot invent answers. Dependent work remains gated where answers affect its behavior.

- **D1 — availability:** Define read/write continuity, permitted request delay, in-flight handling, session/WebSocket continuity, and cutover/rollback thresholds. Proposed invariant: one authoritative writer and no lost acknowledged writes. A fenced snapshot alone does **not** establish uninterrupted availability. A maintenance window is not assumed acceptable. If continuous writes require change capture or durable request buffering, specify and replan that mechanism before implementing affected tasks.
- **D2 — target:** Confirm PostgreSQL version, endpoint/network/TLS requirements, capacity, credentials delivery, and migration privileges without selecting a service or account.
- **D3 — recovery:** Define RPO/RTO, retention, rollback window, and whether rollback must include returning to a SQLite-only release after PostgreSQL has accepted writes. Recommend preserving all acknowledged writes; restoring an old SQLite snapshot is insufficient. Reverse export/replay is decision-gated and requires a revised task breakdown if selected.

Proposed representation: retain JSON text and timestamp strings verbatim, with PostgreSQL JSON validity checks, rather than silently normalizing through JSONB or timestamp conversion. Preserve existing constraints and checked numeric conversions. These technical assumptions remain revisable.

## Planned milestones

### M1 — Establish migration and recovery decisions

Acceptance: a source-backed decision packet defines the execution contract or explicitly identifies unresolved gates.

- [ ] T1 — Specify availability and recovery gates · repo: repository · covers: R1, R2, R3 · kind: research · files: docs/postgresql-migration.md

Produce the D1–D3 packet, source inventory procedure, client behavior matrix, writer-fencing protocol, backup consistency boundary, and rollback state table. Record unanswered decisions as blockers; downstream implementers must not choose them implicitly.

### M2 — Implement compatible PostgreSQL persistence

Acceptance: versioned PostgreSQL storage and all asynchronous consumers preserve the observable API and concurrency rules.

- [ ] T2 — Add versioned PostgreSQL storage · repo: repository · after: T1 · covers: R1, R2, R3 · kind: implement · verify: `npm run typecheck -w @training/api`
- [ ] T3 — Preserve repository and consumer behavior asynchronously · repo: repository · after: T2 · covers: R2, R3 · kind: implement · verify: `npm run test -w @training/api`

T2 supplies connection lifecycle, explicit schema migrations, constraints, readiness, and transactions. T3 awaits every persistence operation, including asset compensation and WebSocket authorization. Serialize competing external-key mutations, check stale revisions before no-op detection, and publish only after commit. Incorporate the D1-approved mutation-drain mechanism across database and asset mutations; do not improvise an availability solution.

### M3 — Build migration and operational recovery

Acceptance: migration, backup/restore, and deployment tooling share verified manifests and fail closed before promotion.

- [ ] T4 — Build verified SQLite data transfer · repo: repository · after: T3 · covers: R1 · kind: implement · verify: `npm run test -w @training/api`
- [ ] T5 — Implement consistent PostgreSQL backup and restore · repo: repository · after: T4 · covers: R1, R3 · kind: implement · verify: `npm run test -w @training/api`
- [ ] T6 — Integrate guarded deployment and rollback · repo: repository · after: T5 · covers: R1, R2, R3 · kind: implement · verify: `npm run build -w @training/api`

T4 reads a consistent SQLite source without auto-migrating it, imports into an isolated target, preserves every column, and compares per-table counts and SHA-256 content manifests. Use explicit column order, typed length-delimited encoding, and primary-key ordering; include raw JSON/timestamps and asset-file checksums. Reject unsupported schemas, invalid records, missing files, target collisions, and mismatches. A source snapshot must be reconciled through the D1-approved final boundary before promotion.

T5 coordinates database snapshots with asset mutation exclusion, packages dump/assets/release/schema metadata, hashes all payload files, and publishes only complete backups. Restore into an isolated destination, validate constraints/counts/hashes/files, then permit guarded promotion.

T6 updates configuration, Docker tooling, Compose, preflight, deployment, and rollback. Use the running store's compatible backup tooling before switching; validate readiness before routing changes. Distinguish compatible PostgreSQL code rollback, database restore, and cross-store rollback. Block incompatible or stale-source rollback.

### M4 — Prove compatibility and rehearse recovery

Acceptance: automated evidence and isolated rehearsals cover R1–R3; unresolved decisions or failed checks prevent any future production promotion.

- [ ] T7 — Add persistence compatibility and failure coverage · repo: repository · after: T6 · covers: R1, R2, R3 · kind: test · verify: `npm run test -w @training/api`
- [ ] T8 — Rehearse cutover and recovery acceptance · repo: repository · after: T7 · covers: R1, R2, R3 · kind: audit · verify: `npm run test -w @training/api`

T7 covers concurrent revisions/import races, no-ops, exact HTTP errors, assets, WebSocket ordering, readiness, migration corruption/restart, and recovery failures against real isolated PostgreSQL. Missing required PostgreSQL configuration must fail the dedicated acceptance run rather than silently skip it.

T8 rehearses writes during handover, interrupted transfer, backup/restore, rollback before and after PostgreSQL writes, asset upload/deletion, browser resynchronization, and database failure. Compare results with the decisions recorded in T1. Future production acceptance additionally requires the actual final-source counts/hashes, asset verification, and availability/recovery evidence; fixture success alone cannot accept R1.

## Verification, estimates, and self-review

All verification is planned. Commands run from the repository root. New tests belong to their creating tasks and are marked `created_by` in JSON. Static checks establish compilation; functional/regression/integration checks establish exercised behavior; product acceptance remains decision-gated.

Estimates are provisional minutes for focused implementation and local verification, not measured history or elapsed schedules. No comparable execution history is available. Operational estimates must be revisited after D1–D3 and source inventory.

Semantic self-review identified three plausible high-impact failure modes: lost writes after snapshot/cutover, inconsistent database/asset recovery, and promise conversion bypassing revision/error handling. The decision gates, shared interfaces, concurrency tests, and recovery rehearsals address them. This is same-context self-review, not independent approval. Structural validation is left to the host.
