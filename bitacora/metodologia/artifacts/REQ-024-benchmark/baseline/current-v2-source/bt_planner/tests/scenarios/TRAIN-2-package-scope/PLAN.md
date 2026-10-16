---
status: approved
---
# Plan — TRAIN-2

### M1 — Rename
- [ ] T1 — Inventory every reference of the old scope · repo: trainingapp · verify: `grep -rn "@training/" . --exclude-dir=node_modules --exclude-dir=.next --exclude=package-lock.json`
- [ ] T2 — Rename the contracts package and its API consumers · repo: trainingapp · after: T1 · files: packages/contracts/package.json, apps/api/package.json, apps/api/src/app.ts, apps/api/src/repositories/project-repository.ts, apps/api/Dockerfile · resources: workspace-package-scope
- [ ] T3 — Rename the web package and its imports · repo: trainingapp · after: T2 · files: apps/web/package.json, apps/web/lib/types.ts · resources: workspace-package-scope
- [ ] T4 — Rename root scripts and the Netlify build command · repo: trainingapp · after: T3 · files: package.json, netlify.toml · resources: workspace-package-scope

### M2 — Verify
- [ ] T5 — Regenerate the lockfile and verify the whole build · repo: trainingapp · after: T4 · files: package-lock.json · verify: `npm run build`
