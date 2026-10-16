# TRAIN-2 — Rename the npm scope `@training/*` to `@trainingapp/*`

Workspace packages are named `@training/web`, `@training/api` and `@training/contracts`. Rename the scope everywhere it
is referenced (manifests, imports, scripts, deployment files) without changing behaviour.

## Requirements
- R1. No file outside node_modules and lockfile history references `@training/`.
- R2. `npm run build`, `npm run typecheck` and `npm test` succeed from the repository root.
- R3. The Docker build of the API and the Netlify build command keep working.
