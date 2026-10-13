# Maros — Architecture

**Audit date:** 2026-10-10 · **Status:** partial · **Coverage:** both registered code repositories inspected; `infra/` excluded by owner · **Independent review:** complete (one standards review raised the CORS/cookie scope; owner confirmed the allowed subdomains are trusted and P-003 was closed).
**Code baseline:** `maros-next` `f133834` and `maros-nest` `66b1357` on `main`, both aligned with `origin/main` at scan time. Each also has uncommitted local changes; see the day log. No test, lint, typecheck, or build commands were run.

## 1. Goals and quality priorities
- **Purpose (owner-confirmed 2026-10-10):** Maros is the CRM for Maros Construction. The web app describes construction project, customer, task, and meeting management (`maros-next/src/app/layout.tsx`).
- **Users (owner-confirmed 2026-10-10):** internal staff and some external users. Exact role groups, core journeys, constraints, success measures, and quality priorities remain unspecified.
- **Inferred priorities:** protect financial figures and permission boundaries; keep CRM project records usable when QuickBooks is slow; ship the web app and API independently. These are inferred from code, not owner priorities.

## 2. Constraints and conventions
- Two separately versioned Git repositories: `maros-next` (Next.js 16 / React 19) and `maros-nest` (NestJS 11 / TypeORM / PostgreSQL). The user explicitly excludes the sibling `infra/` folder from this audit; its files were not inspected or changed.
- The API config sets TypeORM `synchronize: false` and `dropSchema: false` (`maros-nest/src/config/database.config.ts`); schema changes are not auto-synchronized.
- There is no shared package between the frontend and backend. The UI permission union mirrors backend permission strings manually (`maros-next/src/shared/auth/permissions.ts`).

## 3. Context
- Internal staff and some external users access the browser CRM (owner-confirmed audience). The app calls the API over HTTP with cookie credentials; the API uses PostgreSQL and integrates with QuickBooks, S3-compatible file storage, Google services, mail, Trello, and MCP tools. Exact role groups and business handoffs remain unconfirmed.
- Frontend API default: `https://api.marosconstruction.com/api` (`maros-next/src/shared/infra/http/OptimizedApiClient.ts`). API global prefix, CORS, validation, exception filter, and Swagger are configured in `maros-nest/src/main.ts`.

## 4. Containers

| Container | Tech | Responsibility | Owns data | Talks to |
|---|---|---|---|---|
| Web CRM | Next.js 16, React 19, TypeScript | CRM screens, client-side state, auth callbacks and selected server routes | Browser/UI state; no primary CRM database evidence | API over HTTP/cookies; Google Maps; S3-compatible signed uploads |
| CRM API | NestJS 11, TypeORM | Authentication/authorization, CRM use cases, integrations, scheduled work and MCP endpoints | PostgreSQL tables represented by TypeORM entities | PostgreSQL; QuickBooks; S3-compatible storage; Google Calendar; mail; Trello; MCP clients |
| PostgreSQL | PostgreSQL via TypeORM | Persistent CRM records | Users/roles, leads, contacts, companies, projects, tasks, notes, notifications and related records (`maros-nest/src/entities/`) | CRM API |
| QuickBooks Online | External accounting service | Accounting transactions and project financial/job-cost information | Accounting source data is external | CRM API through `modules/quickbooks` |

Production hosting evidence: Netlify build/publish config in `maros-next/netlify.toml`; API deploy workflow in `maros-nest/.github/workflows/deploy.yml` builds/deploys a selected commit to a VPS through restricted SSH. Host details and rollback procedure were not verified (infra excluded).

## 5. Modules and data ownership
- **Frontend:** App Router and global providers at `maros-next/src/app/layout.tsx`; feature modules under `src/features/<feature>/` and shared HTTP/auth under `src/shared/`. Project reads and UI mapping live in `src/features/project/` (application/domain/infra/presentation). The browser does not own the CRM records.
- **Backend:** `maros-nest/src/app.module.ts` composes modules for companies, contacts, leads, projects, CRM, reports, analytics, QuickBooks, tasks, notes, users, notifications, managed files, Google Calendar, and MCP. Controllers validate/route to services; persistence entities live under `src/entities/`.
- **Data:** PostgreSQL tables/entities are declared in `maros-nest/src/entities/`; important CRM entities include `Project`, `Lead`, `Contact`, `Company`, `User`, and task/note entities. QuickBooks financial source data remains external; API enrichment is transiently joined to CRM project views.

## 6. Key flows
1. **Project list + financials:** frontend loads project records and separately polls `GET /projects/financials` (`maros-next/src/features/project/presentation/hooks/data/useProjectsFinancials.ts`). The API controller protects that endpoint with `finance:read` (`maros-nest/src/modules/projects/project-management/projects.controller.ts`); service enriches the rows from QuickBooks. The frontend mapper joins the separate response by project ID (`src/features/project/infra/http/mappers.ts`). Current uncommitted backend/frontend changes add `cashJobCost`, `cashProfit`, and `cashBacklog` to that response and UI mapping; compatibility is visible in both worktrees but has not been tested in this scan.
2. **Authenticated API request:** the frontend HTTP client sends credentials; Nest applies global session and permissions guards from `src/app.module.ts`, request scope, global DTO validation and exception mapping in `src/main.ts`. Frontend permission checks only control what is shown; backend route guards enforce access.
3. **Release:** frontend production build/publish is configured in `maros-next/netlify.toml`; API deployment workflow is triggered from `main` or manually in `.github/workflows/deploy.yml`. Automatic deploy coupling and rollback behavior were not exercised.

## 7. Cross-cutting concepts
- **Auth:** cookie session, global `SessionAuthGuard` and `PermissionsGuard` in `maros-nest/src/app.module.ts`; route permissions declared by decorators. UI permission list is a manually maintained mirror.
- **Validation/errors:** Nest global `ValidationPipe` strips/rejects non-whitelisted fields and transforms DTOs (`src/main.ts`); global exception filter maps API errors.
- **Configuration:** API validates environment shape in `src/config/env.validation.ts`; secrets/values were not read. Frontend API origin has an environment-configurable default.
- **Persistence:** PostgreSQL via TypeORM; synchronization and schema dropping disabled in `src/config/database.config.ts`.
- **External failures:** project list and QuickBooks financials are loaded separately so financial latency does not block project rows. API enrichment records QuickBooks errors in returned financial entries (`ProjectQboEnrichmentService` and project financials service).

## 8. Deployment
- Frontend: Netlify configuration builds with Webpack and publishes `.next`; production API base URL is set in `maros-next/netlify.toml`.
- API: GitHub Actions workflow deploys to a VPS through a restricted SSH command (`maros-nest/.github/workflows/deploy.yml`).
- Database: PostgreSQL configured via environment variables, with schema synchronization disabled. Production database host, backups, health checks, and rollback were outside this scan.
- Local `infra/` deployment/dev scripts are excluded at the owner's direction.

## 9. Data
- CRM operational data is stored in PostgreSQL tables represented by TypeORM entities. QuickBooks is the external source for accounting figures; the API joins the information to CRM project records by lead/project number before returning it to the UI.
- Retention, backup/restore objectives, and ownership of any overlapping fields are not documented in the inspected repositories.

## 10. Decisions, risks, glossary
- **Scope decision:** audit includes `maros-next` and `maros-nest`; excludes `infra/` (D-001).
- **Risk — empty project view on API failure:** `maros-next/src/features/project/presentation/data/loadProjectsData.ts` catches list errors and returns `[]`. An API/network failure can therefore render as a valid empty project list. Confidence: high for the code path; occurrence is unverified. Next action: preserve an error state and add a regression check when implementation is requested. See P-002.
- **Owner-confirmed access boundaries:** invoice email recipient can access the invoice flow (P-001 closed). Owner confirms the API's allowed Maros subdomains are trusted (P-003 closed); revisit this assumption if subdomain ownership or trust changes.
- **Improvement — permission contract maintenance:** `maros-next/src/shared/auth/permissions.ts` says its permission union mirrors `maros-nest/src/common/auth/permissions.ts` manually. Backend guards remain the enforcement point, so this is not an authorization bypass. Drift can still make the UI hide or offer actions inconsistently. Confidence: high. Next action: assess a low-cost shared contract/check only if drift becomes recurring; no shared package was introduced by this scan.
- **Glossary:** QBO = QuickBooks Online; CRM = customer relationship management.

### Audit coverage matrix

| Scope | Available | Architecture / data / flow / deployment | Checks | Independent review |
|---|---|---|---|---|
| `maros-next` | Yes; clean pull, local changes present | Inspected | `git diff --check` passed after pull; lint/tests/build not run | Reviewed |
| `maros-nest` | Yes; clean pull, local changes present | Inspected | `git diff --check` passed after pull; lint/tests/build not run | Reviewed |
| Shared workspace docs | Yes; purpose confirmed, boundary registered | Local docs and workspace inventory inspected; `infra/` excluded | Bitácora audit: both registered repos present, no candidate repositories, scan not truncated | Reviewed |

**Why partial:** independent review is complete and the owner confirmed the broad user categories, but exact roles, journeys, quality priorities, production data operations, and rollback are unknown. Next evidence: clarify those details when they affect a product change; deployment and infrastructure specifics were outside the confirmed scan boundary.
