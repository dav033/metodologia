---
status: approved
---
# Plan — TRAIN-1

### M1 — Server-side session expiry
- [ ] T1 — Add auth session tests · repo: trainingapp · files: apps/api/test/auth.test.ts · verify: `npm run test -w @training/api`
- [ ] T2 — Expire sessions after eight hours · repo: trainingapp · after: T1 · files: apps/api/src/http/auth.ts · verify: `npm run test -w @training/api`
- [ ] T3 — Document the session lifetime · repo: trainingapp · after: T2 · files: docs/api-contract.md
