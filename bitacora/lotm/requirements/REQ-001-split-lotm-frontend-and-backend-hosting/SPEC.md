---
id: REQ-001
status: in-progress
created: 2026-10-13
track: standard
---
# REQ-001 — Split LOTM frontend and backend hosting

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The LOTM public hostname currently resolves directly to AdvIn and Caddy serves the game, Card Studio, APIs, downloads, and MCP from one monorepo deployment. The owner wants a separate Vercel frontend and AdvIn backend, distinct GitHub repositories, and a safe migration of the existing hostname, MCP clients, and deployment automation.

**Success looks like:** the existing public hostname serves the frontend through Vercel; backend services and MCP continue on AdvIn with persistent data intact; each side deploys from its own GitHub repository; routing, certificates, MCP requests, and automated deployments pass production checks; rollback to the current VPS route remains available.

## Users / actors / stakeholders
- David — owns the GitHub, Vercel, DNS, and AdvIn configuration.
- LOTM visitors and editor users — continue using the existing public routes.
- Configured MCP clients — continue connecting to the Card Studio MCP contract.

## Scope (in)
### US-1 (P1, Must) — Separate frontend and backend repositories
As the owner, I want independently deployable frontend and backend repositories so that Vercel serves the frontend and AdvIn serves backend APIs and MCP.
**Acceptance:** the front and back have separate GitHub repositories and build/deploy workflows; the front does not connect directly to production PostgreSQL or own backend business rules.

### US-2 (P1, Must) — Move the public hostname to Vercel
As a visitor, I want `lotm.marosconstruction.com` to keep working while the frontend moves to Vercel.
**Acceptance:** the hostname is attached to the Vercel project with the provider-recommended DNS record and valid TLS; public routes resolve to their intended frontend or backend.

### US-3 (P1, Must) — Preserve backend and MCP services on AdvIn
As an editor/MCP client, I want Card Studio APIs, downloads, and MCP to stay on AdvIn with their existing data and protocol.
**Acceptance:** `/cartas*`, `/api/cards*`, TikTok callback routes, `/downloads/*`, and `/mcp` reach AdvIn; the `lotm_lotm_data` volume and MCP schemas/tool names remain intact.

### US-4 (P1, Must) — Reliable automatic deployments
As the owner, I want the frontend and backend to deploy from their own repositories after checks pass.
**Acceptance:** Vercel's GitHub integration deploys frontend changes; a verified push for the backend repository's `main` deploys the checked commit on AdvIn; unrelated repositories, branches, and invalid signatures cannot trigger deployment.

### US-5 (P1, Must) — Safe cutover and rollback
As the owner, I want the hostname and routes moved only after both deployments are healthy, with the old service available for rollback.
**Acceptance:** a backup of the Caddy/compose configuration and persistent Card Studio data exists; the old route is retained until end-to-end checks pass; rollback steps are recorded.

## Out of scope
- Changing game/card business behavior, authentication policy, database schema, or MCP tool contracts.
- Deleting persistent content, exports, images, backups, or old GitHub repositories.
- Pushing changes to the existing `lotm-workspace` repository's `main` branch.

## Requirements
- R1. When a visitor opens `https://lotm.marosconstruction.com`, the frontend shall be served by the Vercel project with valid TLS.
- R2. When a request targets a backend-owned public path, Vercel shall forward it to AdvIn without changing the browser-visible hostname or dropping the path/query.
- R3. When an MCP client connects to `/mcp`, AdvIn shall preserve the current Streamable HTTP transport, unauthenticated client compatibility, tool names, and schemas. Do not require a Bearer token until every remote client has been reconfigured and verified.
- R4. When a GitHub push is eligible for backend deployment, the deployment system shall verify repository, branch, signature/credentials, and successful CI before deploying that commit.
- R5. Before replacing production containers or routing, the operator shall preserve a restorable copy of the Caddy/compose configuration and existing Card Studio volume.
- R6. If Vercel, backend health, DNS, or MCP verification fails, the operator shall be able to restore the prior AdvIn hostname route without changing application data.
- R7. The new GitHub repositories shall contain the latest intended source without including secrets, local environment files, or generated `data/` contents.

## Edge cases & errors
- DNS provider requires browser login or domain ownership verification; keep the current A record until Vercel verifies its target.
- DNS propagation can leave visitors on either old or new routing during cutover; both routes must remain healthy during the transition.
- Card Studio stores 1.1 GB in the existing external Docker volume; changing Compose project/volume names must not create an empty production store.
- The currently registered GitHub webhook returns 404, while the latest successful production deployment used a GitHub Actions SSH workflow; replace stale automation only after the new flow is verified.
- Frontend and backend commits may arrive concurrently; deployment must use the exact CI-checked commit and avoid overlapping VPS releases.
- MCP clients may send initialize, notifications, and session headers; proxying must preserve methods, headers, response bodies, and streaming behavior.
- TikTok callback URLs and public links must retain their current hostname/path behavior after the DNS move.

## Constraints
- Frontend: Vercel; backend: AdvIn (`ssh advin`, host alias in `~/.ssh/config`); GitHub account: `dav033`.
- DNS is authoritative at IBM NS1 (`DNS1..4.P01.NSONE.NET`); no local NS1 CLI credential was found, and the portal currently presents a login page.
- Existing production uses Caddy, Docker Compose, the `stack_web` network, and external volume `lotm_lotm_data`.
- Current public route map: game at `/`; Card Studio at `/cartas*`; Card Studio APIs at `/api/cards*`; MCP at `/mcp`; downloads at `/downloads/*`; TikTok callback at `/auth/tiktok*` and `/api/tiktok*`.
- Preserve the disabled-authentication decision and public MCP compatibility documented in the project instructions/ADR.
- Do not expose secret values in logs, browser output, or bitácora.

## Priorities & phases
- Must: determine/implement the agreed frontend/backend boundary; create independent repositories and automated deploys; stage and verify backend/MCP; attach Vercel domain and migrate DNS; remove the old hostname route from AdvIn only after validation.
- Should: register the new repository roles and hosting access in the LOTM workspace/bitácora.

## Timeline & dependencies
- One migration, staged by dependency: repository/contract split → preview deployments → backend deployment → Vercel domain/routing → DNS cutover → post-cutover verification and cleanup.
- DNS cutover depends on Vercel project verification and an authenticated NS1 session.

## Assumptions
Selected to match the owner's request: “frontend” means browser-facing game and Card Studio UI hosted on Vercel; “backend” means game APIs/domain/Prisma, Card Studio APIs/storage/MCP, and deployment receiver on AdvIn. This requires extracting server-side game behavior from the current full-stack Next.js app; it is not equivalent to moving the current `apps/game` project unchanged.

The current local worktree includes 75 changed/untracked paths. GitHub `origin/main` is one commit ahead of the local branch; use the fetched production commit as the migration base and carry the existing worktree changes forward deliberately.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear — all browser-facing LOTM UI on Vercel; APIs, persistence, and MCP on AdvIn |
| Out of scope | Clear |
| Flows & behavior | Clear — preserve existing public paths and forward backend-owned requests to AdvIn |
| Edge cases | Clear |
| Acceptance criteria | Clear except final DNS write, which requires an authenticated NS1 session |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
### Round 1 — 2026-10-13
- Q: `@lotm/game` mixes UI, Server Actions, API routes, and Prisma; should its game API move to AdvIn while UI (including Card Studio UI) runs on Vercel? → No reply before work continued autonomously. Selected the recommended scope: all browser UI on Vercel and backend behavior on AdvIn.
