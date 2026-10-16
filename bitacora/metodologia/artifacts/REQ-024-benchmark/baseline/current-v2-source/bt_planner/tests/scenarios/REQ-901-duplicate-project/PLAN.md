---
status: approved
plan_id: REQ-901
---

# REQ-901 — Duplicate a project

Narrative: the API grows one mutation endpoint that clones a project and its images atomically; the web list gets a
"Duplicar" button modelled on the existing "Borrar" button (commit 01861ad). One unknown shapes the backend work, the
atomicity and dangling-photo design, so a short decision task comes first. The web client is written after the endpoint (T4) exists so it targets the
implemented path, and the final verification waits for every test task (T5, T6), the docs (T7) and the button (T9).

### M1 — Decision and API implementation

- [ ] T1 — Decide duplication design (atomicity, dangling photos, key rules) · repo: trainingapp
- [ ] T2 — Add asset cloning to AssetService with its test · repo: trainingapp · after: T1 · files: apps/api/src/services/asset-service.ts, apps/api/src/repositories/asset-repository.ts, apps/api/test/asset-clone.test.ts · resources: asset-clone-contract · verify: `npm run test -w @training/api`
- [ ] T3 — Add transactional duplicate to ProjectRepository with its test · repo: trainingapp · after: T2 · files: apps/api/src/repositories/project-repository.ts, apps/api/test/project-duplicate.test.ts · resources: asset-clone-contract · verify: `npm run test -w @training/api`
- [ ] T4 — Expose POST /v1/projects/:projectId/duplicate with key and name generation · repo: trainingapp · after: T3 · files: apps/api/src/app.ts · resources: duplicate-endpoint-contract · verify: `npm run typecheck -w @training/api`

### M2 — API tests and documentation

- [ ] T5 — Test copy independence and rollback across service and repository · repo: trainingapp · after: T3 · files: apps/api/test/duplicate.test.ts · verify: `npm run test -w @training/api`
- [ ] T6 — Test the duplicate endpoint over HTTP · repo: trainingapp · after: T4 · files: apps/api/test/duplicate-route.test.ts · verify: `npm run test -w @training/api`
- [ ] T7 — Document the endpoint in the API contract · repo: trainingapp · after: T4 · files: docs/api-contract.md

### M3 — Web workspace and integration

- [ ] T8 — Add duplicateProject to the web API client · repo: trainingapp · after: T4 · files: apps/web/lib/api/client.ts · resources: duplicate-endpoint-contract · verify: `npm run typecheck -w @training/web`
- [ ] T9 — Add the Duplicar button to the project list · repo: trainingapp · after: T8 · files: apps/web/components/project-list.tsx · resources: projects-changed-event · verify: `npm run lint -w @training/web`
- [ ] T10 — Run the full workspace checks end to end · repo: trainingapp · after: T5, T6, T7, T9 · verify: `npm run typecheck`
