---
plan_id: REQ-CP2
revision: 1
status: draft
spec_ref: SPEC.md
---

# REQ-CP2 — TRAIN-6: Move Training API persistence from SQLite to PostgreSQL (DRAFT)

Draft for owner review. It is not approved, frozen or launched. Product and ops choices that the requirement leaves open are listed as decision gates, each with a recommended default. No owner answers have been recorded. Estimates are planner estimates: this sandbox has no comparable execution history. No commands were run while preparing this draft.

## Goal and scope

Move the API's persistence for `projects` and `assets` metadata from SQLite (`better-sqlite3`) to PostgreSQL. No data may be lost and availability must be preserved within the window chosen at D2.

- **R1** Every existing row is migrated and verified with row counts and content hashes.
- **R2** Clients see identical API behaviour, including revision conflicts (`409 REVISION_CONFLICT` + `currentRevision`).
- **R3** Backups and rollback keep working on the new store.

**In scope:** a PostgreSQL store module and schema migration; an async port of the repositories, asset service, HTTP handlers, WebSocket upgrade and server lifecycle; parity tests; a verified SQLite→PostgreSQL migration CLI; backup and restore on PostgreSQL; changes to compose, deploy and rollback; a guarded cutover script; a rehearsal.

**Out of scope:**
- Changes to the HTTP/WS contract, `packages/contracts`, `apps/web` or the separate MCP adapter repository.
- Persistent sessions. They stay in memory, as in `apps/api/src/http/auth.ts`.
- Moving asset files off the filesystem volume.
- Running more than one API instance.
- Removing `better-sqlite3`. It is kept for the migration tool and for SQLite rollback.
- Running the production cutover. The owner runs it after approval.

## Inspected findings (provenance)

- `apps/api/src/db/database.ts`:
  - Synchronous `better-sqlite3`; `PRAGMA user_version` migration to schema 1 inside `BEGIN IMMEDIATE`; it rejects a version newer than 1.
  - `data_json TEXT CHECK(json_valid)`; `projects.external_key UNIQUE`; `assets.project_id REFERENCES projects ON DELETE CASCADE`; `relative_path UNIQUE`.
  - `assertDatabaseReady` runs `integrity_check` and the version check.
- `apps/api/src/repositories/project-repository.ts`:
  - `mutate` runs inside `BEGIN IMMEDIATE`: it reads by `external_key`, throws `RevisionConflictError(current.revision)` on a mismatch, and sets `changed` by plain string comparison of `name`, `description` and `data_json`. The revision is bumped only when something changed.
  - Creating a duplicate key throws a plain `Error`, which becomes a 500 via `app.ts`.
  - `list` orders by `updated_at DESC`. Timestamps are ISO strings.
- `apps/api/src/repositories/asset-repository.ts` and `apps/api/src/services/asset-service.ts`: synchronous inserts, lists and deletes. A file is written with `wx` before the row is inserted and removed if the insert fails.
- `apps/api/src/app.ts`:
  - Synchronous handlers. `hub.publish` runs after a successful mutation.
  - The error middleware maps conflicts to 409, not-found to 404, Zod errors to 400, 413 to 413, and anything else to 500.
  - `/readyz` calls `assertDatabaseReady`.
- `apps/api/src/ws/server.ts`: calls `repository.getById` synchronously during upgrade and answers 404 if it fails.
- `apps/api/src/server.ts`: `db.close()` on shutdown.
- `apps/api/src/errors.ts`: the error classes.
- `apps/api/src/backup.ts`:
  - Runs `db.backup` to `training.db` and copies `assets/`. Writes `checksums.sha256`, `git-sha.txt`, `schema-version.txt` and `manifest.json`.
  - Already uses top-level await.
  - Its default backup root is `dirname(dbPath)/backups` (`/app/data/backups`), while compose mounts `/app/backups`. This only works if `api.env` sets `TRAINING_BACKUP_DIR`; that file is not in the repo.
- `ops/ec2/deploy.ps1`: runs `node apps/api/dist/backup.js` with the **new** image before activation.
- `ops/ec2/rollback.ps1`: rolls back code only and warns that the DB is not restored.
- `ops/ec2/compose.yml`: mounts `shared/data` and `shared/backups`, and uses `env_file` `shared/api.env`.
- `apps/api/Dockerfile`: `node:20-bookworm-slim` with a native build toolchain; no PostgreSQL client.
- `apps/api/src/config.ts`: `TRAINING_DB_PATH`; production guards for secrets and HTTPS.
- `.env.example`: lists the current environment variables.
- `apps/api/package.json`:
  - Scripts `test` (`node --import tsx --test test/*.test.ts`), `typecheck`, `build` and `backup`.
  - No `pg` dependency.
- `apps/api/test/repository.test.ts`: the only API test, against a temporary SQLite file.
- Client consumers: `apps/web/lib/api/client.ts` reads `status` and `currentRevision`; `apps/web/hooks/use-project-sync.ts` handles conflicts. The snapshot shape is `packages/contracts/src/project.ts` (`revision` int, `createdAt`/`updatedAt` strings).
- `docs/architecture.md` and `docs/api-contract.md`: single API instance, in-memory hub, the commit-then-publish rule, and the 409 contract.

## Resolved design rules (evidence-backed, not owner choices)

1. **Column types.** Use `TEXT` for ids, `external_key`, `name`, `description`, `field`, `relative_path`, `mime_type`, `sha256`, `created_at`, `updated_at` and `data_json`. Use `INTEGER` for `schema_version`, `revision` and `byte_size`.
   - `data_json` stays `TEXT` with a JSON validity check (cast to `jsonb` in a CHECK). It must **not** be JSONB, so that the `changed` string comparison, the exact payload bytes and the content hashes are preserved.
   - Timestamps stay ISO `TEXT`, so API strings are unchanged.
   - No `BIGINT` and no uncast `COUNT(*)`, because `pg` returns int8 as a string.
2. **Concurrency.** Use one transaction per mutation with `SELECT … WHERE external_key = $1 FOR UPDATE`. This replaces `BEGIN IMMEDIATE`.
   - A unique-violation on `external_key` during create maps to the same plain `Error("El externalKey ya existe.")`, so the client still gets a 500.
   - On any error: rollback, release the client, rethrow.
3. **Schema versioning.** A `schema_migrations` table is written under a PostgreSQL advisory lock. A recorded version above 1 throws `Unsupported database schema N`. Readiness means the server is reachable and the version is exactly 1.
4. **Request ordering.** The ordering inside each request stays the same: delete asset files before deleting the row (the cascade is kept); publish only after commit; in the WS upgrade, await the project lookup before `handleUpgrade`.

## Decision gates (owner; recommended default in brackets)

- **D1 Hosting and version:** where PostgreSQL runs and which major version. [A compose `postgres:16` service on the EC2 `stack_web` host, data volume under `shared/`, and a matching `postgresql-client`.] This affects T6, T7 and T8.
- **D2 Availability:** the acceptable write-freeze or downtime at cutover. [A short maintenance window: stop the API, take the final SQLite backup, migrate and verify, then activate. Zero-downtime dual-write is excluded; requiring it would mean new tasks.] This affects T7 and T8.
- **D3 Post-cutover rollback policy:** [Forward-only once verified. Recovery is via a PostgreSQL restore, plus code rollback between PostgreSQL releases. Rolling back to a SQLite release needs an explicit flag and an acknowledgement that writes made after cutover will be lost. A reverse PG→SQLite export is a new task only if the owner requires it.] This affects T7.
- **D4 Backups:** retention and off-host copies. [Keep today's local layout; off-host copies are out of scope.]
- **D5 Test database:** how a PostgreSQL instance is provided for `npm test`. [`TRAINING_TEST_DATABASE_URL` pointing at a disposable local instance. The test helper fails rather than skipping when it is unset.]

## Assumptions (revisable)

- **A1** PostgreSQL ≥ 14 is available for arm64 (`uname -m` = aarch64 in `deploy.ps1`).
- **A2** The API remains a single instance.
- **A3** Asset files stay on the `/app/data/assets` volume; only metadata rows move.
- **A4** Express 5 forwards rejected promises from async handlers to the error middleware. T4 tests verify this.
- **A5** Production data size fits the 4 GB free-disk preflight. T1 checks this.

## Risks

- JSONB or `timestamptz` would silently change `changed` detection, output strings and hashes. Mitigation: rule 1.
- Lock semantics differ between `BEGIN IMMEDIATE` and `FOR UPDATE`. Mitigation: T4 concurrency tests.
- The first PostgreSQL deploy through `deploy.ps1` would run the new backup against an empty or unreachable PostgreSQL and take no SQLite backup. Mitigation: the T7 cutover script and a deploy guard.
- A `pg_dump` version different from the server's breaks backups. Mitigation: D1 and T6.
- The existing backup-directory mismatch, if `api.env` lacks `TRAINING_BACKUP_DIR`. Mitigation: T1 verifies it; T6 makes the directory explicit.
- Rolling back to a SQLite release loses post-cutover writes. Mitigation: D3 and the T7 guard.
- Rehearsal copies contain personal data (names, emails, ages). They must stay on controlled hosts and be deleted after T8.
- Credential exposure. `TRAINING_DATABASE_URL` lives only in `api.env` (chmod 600 already enforced). It is never logged and never passed in argv to `pg_dump`/`pg_restore`.
- Tie order in `list` for equal `updated_at` values is unspecified in both stores.

## Milestones and tasks

### M1 — PostgreSQL runtime with identical API behaviour
Acceptance: the API runs entirely on PostgreSQL, with typecheck clean and the parity and concurrency tests green. The decision record exists.

- [ ] T1 — Record PostgreSQL hosting, cutover window and rollback decisions · repo: repository · covers: R1, R3 · kind: research
- [ ] T2 — Add PostgreSQL store module with schema migration and readiness · repo: repository · verify: `npm test -w @training/api` · covers: R1, R2 · kind: implement
- [ ] T3 — Port repositories, asset service, HTTP and WebSocket callers to PostgreSQL · repo: repository · after: T2 · verify: `npm test -w @training/api` · covers: R2 · kind: implement
- [ ] T4 — Add HTTP parity and concurrency regression tests on PostgreSQL · repo: repository · after: T3 · verify: `npm test -w @training/api` · covers: R2 · kind: test

### M2 — Verified data migration
Acceptance: a SQLite snapshot migrates into an empty PostgreSQL database, and the commit happens only when counts and hashes match.

- [ ] T5 — Build verified SQLite-to-PostgreSQL data migration tool · repo: repository · after: T2 · verify: `npm test -w @training/api` · covers: R1 · kind: implement

### M3 — Backup, rollback and cutover readiness
Acceptance: PostgreSQL backups restore and verify. Deployment, cutover and rollback scripts are guarded. A rehearsal proves R1–R3 on a production-like copy.

- [ ] T6 — Replace SQLite backup with PostgreSQL dump and verified restore · repo: repository · after: T1, T5 · verify: `npm test -w @training/api` · covers: R3, R1 · kind: implement
- [ ] T7 — Update deployment, cutover script and rollback guards for PostgreSQL · repo: repository · after: T3, T6 · covers: R3, R1 · kind: implement
- [ ] T8 — Rehearse cutover, restore and rollback on a production-like copy · repo: repository · after: T4, T7 · verify: `npm run typecheck -w @training/api` · covers: R1, R2, R3 · kind: audit

## Task behaviour

### T1 — Decision record
- Writes `docs/decisions/TRAIN-6-postgres.md` covering D1–D5: options, the recommended default, and owner status (`pending` until the owner answers).
- Records verified environment facts with read-only checks: the PostgreSQL target, whether `api.env` sets `TRAINING_BACKUP_DIR`, the current DB and asset sizes, and free disk.
- It does not approve anything on the owner's behalf.

### T2 — PostgreSQL store module
- New file `apps/api/src/db/postgres.ts` exposes:
  - `openPostgres(url)`: returns a migrated `pg.Pool`.
  - `withTransaction(pool, fn)`.
  - `assertPostgresReady(pool)`.
  - Schema 1 exactly per design rules 1 and 3.
- `database.ts` (SQLite) stays untouched, because it is the migration source, and typecheck stays green.
- `config.databaseUrl` reads `TRAINING_DATABASE_URL`; production throws if it is missing. Add it to `.env.example`.
- Add the `pg` dependency.
- Add the test helper `apps/api/test/helpers/pg.ts`. It creates an isolated schema or database per test from `TRAINING_TEST_DATABASE_URL` and fails explicitly when that is unset.

### T3 — Async port
All of the following become async on the T2 pool: the `ProjectRepository` methods, `AssetRepository`, `AssetService`, the `app.ts` handlers, the `ws/server.ts` upgrade and `server.ts` (top-level `await openPostgres`, `pool.end()` on shutdown). Behaviour must be preserved exactly:

- `create` → revision 1.
- `update`/`upsertImport` with a stale `expectedRevision` → `RevisionConflictError(stored revision)`.
- Import of a missing key with `expectedRevision ≠ 0` → `RevisionConflictError(0)`.
- An unchanged payload → `changed=false`, same revision and `updatedAt`, no event.
- A duplicate key on create → 500.
- An asset insert failure deletes the written file. An unknown project in an asset upload → 500, as today.
- Delete removes the files, then the row; the DB cascade removes asset rows.
- Response bodies and status codes are unchanged.

`repository.test.ts` is ported to async and PostgreSQL. `better-sqlite3` imports remain only in the SQLite source code (`db/database.ts`, and later the migration tool).

### T4 — Parity tests
The tests start `createApp` with a test config that has an MCP bearer token, on an ephemeral port. They assert:

- create 201;
- GET by id and by external key, and 404 bodies;
- PUT stale → 409 `{error.code: REVISION_CONFLICT, currentRevision}`;
- import create, import with `expectedRevision≠0` on a missing key → 409 with `currentRevision 0`, and import unchanged → `changed:false`;
- DELETE 204 cascades asset rows;
- `/readyz` 200, and 503 after the version row is altered;
- Zod 400.

A concurrency test fires N parallel PUTs carrying the same `expectedRevision`: exactly one succeeds, the others get 409, and the final revision is +1.

### T5 — Migration CLI
`apps/api/src/migration/sqlite-to-postgres.ts`, run as an npm script:

1. Open the source read-only (`fileMustExist`). Abort unless `integrity_check` is `ok` and `user_version` is 1.
2. The target must be at schema 1 with both tables empty; otherwise abort. No merging.
3. In a single PostgreSQL transaction, insert `projects` and then `assets`, copying every column verbatim.
4. Compute counts and SHA-256 hashes on both sides with `row-hash.ts`:
   - rows are sorted by `id` using JavaScript code-point order, not DB collation;
   - each row is serialized as a JSON array of the columns in schema order.
5. On any mismatch: ROLLBACK, exit non-zero, write the report. Otherwise COMMIT and write a report JSON (counts, hashes, source file SHA-256, timestamps).
6. `--verify-only` compares without writing.
7. Missing or mismatched asset files are reported as warnings only; they do not block.

### T6 — Backup and restore
- `backup.ts` keeps the existing directory layout but replaces `training.db` with `training.pgdump` (`pg_dump --format=custom --no-owner`).
  - Credentials are passed via `PG*` environment variables derived from the URL, never in argv.
  - It also writes `verification.json`, the T5 hash report taken from the backup's own snapshot.
  - `schema-version.txt` comes from `schema_migrations`. `manifest.json` gains `store: "postgresql"` and is written last.
  - Any failure exits non-zero.
- New `restore.ts`:
  1. Verify `checksums.sha256`.
  2. Refuse a non-empty target.
  3. Run `pg_restore --exit-on-error --single-transaction`.
  4. Recompute hashes and compare them with `verification.json`.
  5. Restore assets only into an empty, explicit directory.
- The Dockerfile installs a PostgreSQL client that matches D1.

### T7 — Deployment, cutover and rollback scripts
- `compose.yml`: implements D1 (a PostgreSQL service with a healthcheck and a volume under `shared/`, or an external URL in `api.env`). Keeps the `/app/data` (assets) and `/app/backups` mounts.
- `deploy.ps1`: refuses to activate if PostgreSQL is unreachable or not at schema 1, then checks `/readyz` after activation.
- New `cutover.ps1`, a guarded one-time script:
  1. Stop the API.
  2. Run the current (SQLite) release's `backup.js`.
  3. Run the T5 CLI from the new image against that backup's `training.db`.
  4. On failure: restart the old release and do not activate.
  5. On success: activate, check `/readyz`, and take the first PostgreSQL backup.
- `rollback.ps1`: code rollback between PostgreSQL releases is unchanged. Rolling back to a release without `apps/api/src/db/postgres.ts` requires `-AllowSqliteRollback` and prints the D3 data-loss warning.
- `docs/deployment.md` and `docs/architecture.md` describe the runbook and the restore procedure.

### T8 — Rehearsal
On a controlled non-production host, using a copy of a real backup:

- run the cutover, the T5 verification, the T4 suite, a backup, a restore into a fresh database with hash match, and both rollback paths;
- record the measured downtime for D2 and every deviation in `docs/runbooks/TRAIN-6-rehearsal.md`;
- delete the data copies afterwards.

## Interfaces

- **IF-1 PostgreSQL store module.** T2 produces it; T3, T5 and T6 consume it; T4 is the integration test.
- **IF-2 Row-hash verification report.** T5 produces it; T6 and T8 consume it; T6 integrates it.
- **IF-3 Async repository/HTTP contract.** T3 produces it; T4, T7 and T8 consume it; T4 integrates it.

## Verification (planned; nothing has been run)

- **Static:** `npm run typecheck -w @training/api`
- **Functional / regression / integration:** `npm test -w @training/api`, which needs `TRAINING_TEST_DATABASE_URL`. New test files are created by T2–T6 and are not existing evidence.
- **Product:** the T8 manual rehearsal. Green tests show only the behaviour they exercise; production acceptance needs the T8 record and owner sign-off.

## Requirement traceability

- **R1:** T1, T2, T5, T6, T7, T8
- **R2:** T2, T3, T4, T8
- **R3:** T1, T6, T7, T8
