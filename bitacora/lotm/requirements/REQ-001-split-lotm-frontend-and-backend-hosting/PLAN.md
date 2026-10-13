---
req: REQ-001
status: approved
created: 2026-10-13
---
# Plan — REQ-001 — Split LOTM frontend and backend hosting

## Approach
Extract the public game shell, Card Studio UI, and legal pages into `lotm-frontend`; keep game API/domain/Prisma, Card Studio API/storage/MCP, and deployment integration in `lotm-backend`. Keep versioned game API endpoints behind same-host Vercel rewrites; preserve existing public paths and MCP tool contracts. Legacy `/admin`, `/coleccion`, and `/logros` remain on the backend fallback during incremental UI migration. Build both repos from the latest production commit plus the owner’s local changes, without pushing to the existing repository.
Stage the AdvIn backend first, reusing the existing `stack_web` network and `lotm_lotm_data` volume. Deploy Vercel previews and verify rewrite behavior before assigning the custom domain and changing DNS. Disable stale deployment paths only after the split paths pass.

## Global constraints
- Preserve routes, database schema/migrations, disabled game auth decision, MCP tool names/schemas, ZIP manifest v3, and all persistent content.
- Keep production rollback available; back up Caddy/compose configuration and the 1.1 GB Card Studio volume before replacing services.
- Never transfer or print secrets into repository files or bitácora. Update every MCP client before enforcing Bearer auth.
- DNS authority is IBM NS1. Its browser session is logged out; do all independent work before requesting owner sign-in.
- Never push to or merge into `dav033/lotm-workspace` main. Create the requested new repos without overwriting the existing `lotm-game` or `lotm-cards` repositories.
- Source base is fetched `d37cc8c`; carry the local working-tree patch and 15 untracked project files forward explicitly.

## Tasks
- [x] T1 — Inventory current code, hosting, DNS, MCP, webhook, source drift, and persistent data; prepare isolated worktree · files: `/tmp/lotm-migration`, REQ-001/SPEC.md · verify: `git apply --check /tmp/lotm-local-working-tree.patch` · covers: R3, R4, R5, R7
- [x] T2 — Extract game server-rendered data and Server Actions behind AdvIn HTTP contracts; keep API/domain/Prisma and Card Studio server/MCP on AdvIn · repo: backend · level: architecture · after: T1 · verify: backend lint/typecheck/tests/build, VPS health, `/api/v1/admin/session` via Vercel · covers: R2, R3, R4
- [x] T3 — Move the public game shell, Card Studio UI, and legal pages into `lotm-frontend`; replace direct DB/server-action usage with validated API clients; leave legacy UI routes behind the backend fallback during incremental migration · repo: frontend · level: architecture · after: T2 · verify: frontend lint/typecheck/tests/build, Vercel deployment and public routes · covers: R1, R2, R7
- [ ] T4 — Add independent CI/deploy flows, Vercel Git integration, API rewrites, and MCP client configuration · repos: frontend, backend · after: T2, T3 · verify: `git diff --check` · covers: R2, R3, R4
- [x] T5 — Back up and stage backend on AdvIn without changing the active route or volume identity · repo: backend · after: T4 · verify: pre-split backup checksums, Compose health, original Caddy route, existing volume retained · covers: R3, R5, R6
- [ ] T6 — Create/verify the two GitHub repositories and Vercel projects; deploy preview builds and exercise APIs, cards, MCP, and downloads · repos: frontend, backend · after: T4, T5 · verify: `gh run list --repo dav033/lotm-backend --limit 1` · covers: R1, R2, R3, R4, R7
- [ ] T7 — Attach `lotm.marosconstruction.com` to Vercel, configure provider-required NS1 DNS, then verify TLS and same-host rewrites · after: T6 · verify: `curl --fail https://lotm.marosconstruction.com/` · covers: R1, R2, R6
- [ ] T8 — Update MCP clients/auth, remove the stale GitHub webhook and old monorepo auto-deploy only after replacement checks pass; update workspace/docs/bitácora · after: T6, T7 · verify: `curl --fail https://lotm.marosconstruction.com/mcp` · covers: R3, R4, R5, R6

## Verification
- Frontend and backend CI: lint, TypeScript, behavior tests, and production builds for each new repo.
- Vercel preview: root, Card Studio routes, API rewrites, TikTok callback routing, and same-host URLs.
- AdvIn: health checks for game API, Card Studio API/MCP, current persistent volume identity, and download endpoint.
- MCP: bearer-authenticated initialize/list-tools against the deployed server and read-only tool call through the existing Codex connector; preserve all 15 existing tool contracts.
- Automation: a successful backend CI run triggers one deploy for its exact commit; wrong repo/branch and failed CI do not deploy. Vercel GitHub integration creates a production deployment on frontend main.
- Cutover: resolve the custom hostname to Vercel, verify TLS and all preserved routes, verify AdvIn MCP and files, and retain rollback instructions.
- Run `npm run brain:record` and `npm run brain:check` from the resulting workspace before close.

## Rulings
- Keep the existing `lotm.marosconstruction.com` URL as the public browser origin; use Vercel rewrites to hide the backend origin and avoid changing browser-facing paths — this also preserves current MCP connector URLs. Cost if wrong: medium (Vercel rewrite/protocol constraints).
- Use the current workspace app boundary to extract game APIs to AdvIn and put both app UIs on Vercel; Vercel can use separate project roots from one frontend repo. Cost if wrong: high (requires substantial app extraction).
- The current public MCP has no token and the available Codex connector succeeds unauthenticated. Do not rotate/require a token until the connector configuration can be updated and verified. Cost if wrong: medium (temporary public MCP access remains).
- The manual GitHub webhook at `/deploy/github` is stale (404); use GitHub Actions after successful CI for backend deployment and Vercel’s GitHub integration for the frontend, then remove the stale hook. Cost if wrong: low (one redundant webhook is retained until replacement verification).
- New GitHub repositories will use `lotm-frontend` and `lotm-backend`; leave existing `lotm-game`, `lotm-cards`, and `lotm-workspace` intact. Cost if wrong: low (names can be renamed before code push, never force-overwrite).

## Progress log
- 2026-10-13 — Discovery complete: production domain is on AdvIn/Caddy; Vercel has no LOTM project; NS1 portal is logged out; current remote deploy is GitHub Actions/SSH; manual webhook returns 404; MCP connector works but public HTTP MCP is unauthenticated; local source changes were preserved in an isolated worktree from current production commit.
- 2026-10-13 — Created private `dav033/lotm-frontend` and `dav033/lotm-backend` repositories with local commits `b679935`, `95e9c78`, `499d299`, and `a490495`; no push to the original `lotm-workspace` repo. Vercel project `lotm-frontend` is linked to GitHub, root `apps/site`, Node 24.x, and has a READY production deployment. Git push is waiting for OAuth `workflow` scope.
- 2026-10-13 — Created and verified a root-only AdvIn backup, kept the existing Compose volume, deployed backend commit `95e9c78` through the restricted server script, and confirmed all three containers healthy. Frontend and backend routes respond through Vercel; `/mcp` initialize and tools/list pass with 15 tools. DNS still points to AdvIn; NS1 login is required for cutover.
- 2026-10-13 — Updated the local OpenCode remote MCP URL to `https://lotm.marosconstruction.com/mcp`. The stale webhook `660396468` on `lotm-workspace` remains until the new GitHub Actions deploy flow runs successfully.
