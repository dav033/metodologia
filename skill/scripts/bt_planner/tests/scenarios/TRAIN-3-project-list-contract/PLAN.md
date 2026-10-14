---
status: approved
---
# Plan — TRAIN-3

### M1 — Decide and specify
- [ ] T1 — Find out who consumes the list endpoint outside this repository · repo: trainingapp · files: scripts/check-contract-drift.mjs
- [ ] T2 — Define the list response schema in contracts · repo: trainingapp · after: T1 · files: packages/contracts/src/project.ts, packages/contracts/test/project.test.ts · verify: `npm run test -w @training/contracts` · resources: projects-list-response

### M2 — Implement
- [ ] T3 — Paginate and slim the list endpoint · repo: trainingapp · after: T2 · files: apps/api/src/app.ts, apps/api/src/repositories/project-repository.ts, apps/api/test/list.test.ts · verify: `npm run test -w @training/api` · resources: projects-list-response
- [ ] T4 — Consume nextCursor in the web client and its two screens · repo: trainingapp · after: T3 · files: apps/web/lib/api/client.ts, apps/web/components/project-list.tsx, apps/web/components/project-tabs-bar.tsx · verify: `npm run typecheck -w @training/web` · resources: projects-list-response
- [ ] T5 — Document the new list contract · repo: trainingapp · after: T3 · files: docs/api-contract.md
