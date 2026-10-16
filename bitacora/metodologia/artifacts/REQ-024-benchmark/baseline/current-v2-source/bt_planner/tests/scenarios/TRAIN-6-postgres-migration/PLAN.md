---
status: approved
---
# Plan — TRAIN-6

### M1 — Decide and prepare
- [ ] T1 — Write the persistence port and decide the driver and migration strategy · repo: trainingapp · files: apps/api/src/repositories/project-repository.ts, apps/api/src/repositories/asset-repository.ts, apps/api/src/db/database.ts · resources: persistence-port
- [ ] T2 — Move repositories behind the port without changing storage · repo: trainingapp · after: T1 · files: apps/api/src/repositories/project-repository.ts, apps/api/src/repositories/asset-repository.ts, apps/api/src/services/asset-service.ts, apps/api/src/app.ts · verify: `npm run test -w @training/api` · resources: persistence-port

### M2 — Postgres implementation
- [ ] T3 — Implement the PostgreSQL schema and repositories · repo: trainingapp · after: T2 · files: apps/api/src/db/postgres.ts, apps/api/test/postgres-repository.test.ts · verify: `npm run test -w @training/api` · resources: persistence-port, database-schema
- [ ] T4 — Build the data migration and verification tool · repo: trainingapp · after: T2 · files: apps/api/src/migrate-sqlite-to-postgres.ts · resources: database-schema

### M3 — Cutover
- [ ] T5 — Adapt backup, compose and deployment scripts · repo: trainingapp · after: T3 · files: apps/api/src/backup.ts, ops/ec2/compose.yml, ops/ec2/deploy.ps1, ops/ec2/rollback.ps1, apps/api/Dockerfile · resources: deployment-contract
- [ ] T6 — Rehearse the migration on a copy and write the cutover runbook · repo: trainingapp · after: T4, T5 · files: docs/deployment.md
