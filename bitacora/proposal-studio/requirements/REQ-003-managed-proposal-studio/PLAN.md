---
req: REQ-003
status: done
created: 2026-10-10
---
# Plan — REQ-003 — Managed Proposal Studio

## Approach
Evolve the current Astro viewer into one server-rendered Vercel application while preserving the existing comparison. Use Neon Postgres for owner/auth/proposal/revision/link/outbox metadata and private Vercel Blob for screenshots and immutable prototype files. Implement auth, GitHub import, share-token access, and email delivery as explicit boundaries. Keep imported prototypes isolated from the authenticated origin. Use local/test adapters while developing, then provision free-tier integrations under the owner's existing accounts and deploy to a Vercel subdomain after local acceptance checks.

## Guardrails
- Preserve current user-created, uncommitted repo state; do not reset, delete, or overwrite unrelated work.
- Run `git status` and inspect the current source/build before editing. The workspace is tracked in private GitHub repository `https://github.com/dav033/proposal-studio` on `feat/proposal-comparison`; preserve ignored local secrets and generated state.
- Add dependencies only after checking current official documentation and runtime compatibility. Record any major dependency/architecture choice in the project ADR and brain.
- Keep strict TypeScript; no `any`, suppressions, fake-success fallbacks, or unchecked casts across provider boundaries.
- External OAuth/GitHub/Neon/Blob/Resend setup and deployment are authorized by David's active goal. Avoid paid plan upgrades and DNS/custom-domain changes; use free tiers and a Vercel subdomain. Never send a real prospect email during verification.

## Phases
### Phase 0 — Audit and architecture decision
- Verify current routes, capture protections, Astro version/adapter compatibility, and user changes.
- Confirm schema/flow; document ADR for Astro SSR/Vercel, Neon, private Blob, Better Auth, GitHub App, Postgres outbox, Resend, and prototype isolation.
- Verify supported integration versions from official docs and lock exact compatible versions.

### Phase 1 — Runtime, persistence, and design shell
- Add Astro Vercel server adapter and local Vercel preview configuration.
- Add Postgres schema/migrations, typed repository/query modules, private Blob storage boundary, and deterministic local test adapters.
- Add Spanish Material-inspired admin shell with routes for dashboard, proposals, integrations, and settings.
- Preserve existing public proposal UI and provide migrations/import path for the fictional `clinica-horizonte` record.

### Phase 2 — Authentication and admin proposal lifecycle
- Integrate Better Auth Google OAuth with strict owner allowlist and secure session settings.
- Protect every server route/API/action; implement proposal CRUD, drafts, validation, publish versions, archive, and audit events.
- Move screenshot storage behind private Blob while retaining hardened capture behavior and actionable failure states.

### Phase 3 — GitHub read-only prototype import
- Implement GitHub App connection callback/status/disconnect and authorized repository/branch/tree browsing.
- Import only selected static output under strict file/path/count/size rules; pin commit SHA and immutable revision in private Blob.
- Add admin preview and isolate rendered prototype content from parent application/session.

### Phase 4 — Temporary sharing
- Implement link create/list/revoke/replace with lifetime choices and hashed token persistence.
- Render access-gated public proposal route, redact tokens, set noindex/referrer protections, and enforce token status every request.
- Verify updated published revision behavior with old active links and revoked/expired links.

### Phase 5 — Optional email notifications
- Add global Resend configuration/status and per-proposal recipient/opt-in.
- Add Postgres outbox, Resend idempotency key by revision/recipient, bounded request timeouts, pending/failed state, admin retry action, and test-send action.
- Ensure publish commits independently of delivery success and draft changes never enqueue messages.

### Phase 6 — Verification, documentation, handoff
- Add unit, Postgres/Blob integration, auth/GitHub/email contract, and Playwright E2E tests.
- Run check, lint, format, full tests, Vercel build/preview, and browser walkthrough at desktop/mobile.
- Update README, `.env.example`/`.dev.vars.example`, setup guide, architecture, pending, daily log, and final report. Leave environment-specific account credentials and publishing for later owner setup.

## Tasks
- [x] T1 — Implement allowlisted Google OAuth, owner authorization, and persistent application schema · files: `src/features/auth/`, `src/db/`, `src/middleware.ts` · verify: `npm run build` and production owner login · covers: R1, R3, R10, US-1
- [x] T2 — Implement proposal drafts, validation, revisions, publication, archival, and audit history · files: `src/features/proposals/`, `src/pages/api/admin/proposals/` · verify: proposal service integration tests · covers: R1, R2, R10, R11, US-2
- [x] T3 — Implement read-only GitHub browsing and safe, pinned static snapshot import · files: `src/features/github/`, `src/pages/api/admin/github/` · verify: GitHub boundary and import integration tests · covers: R2, R3, R7, US-3
- [x] T4 — Implement hashed expiring share tokens, revocation, and isolated public asset access · files: `src/features/sharing/`, `src/pages/s/`, `src/pages/api/share-assets/` · verify: share lifecycle tests and browser sandbox tests · covers: R4, R8, US-4
- [x] T5 — Implement opt-in publication notifications with transactional outbox, idempotent delivery, and manual retry · files: `src/features/notifications/`, `src/pages/api/admin/notifications/` · verify: notification service integration tests · covers: R3, R9, US-5
- [x] T6 — Deliver Spanish responsive admin/prospect UI, comparison, protected capture, and runtime validation · files: `src/pages/`, `src/components/`, `src/styles/`, `scripts/` · verify: `npm run build`, E2E, and production browser walkthrough · covers: R6, R8, R11, US-2, US-6
- [x] T7 — Enforce shared per-owner limits for sensitive authenticated operations · files: `src/features/security/`, `src/middleware.ts`, `drizzle/0004_next_thing.sql` · verify: rate-limit atomicity/concurrency tests and production migration · covers: R5, R10
- [x] T8 — Verify service boundaries, HTTP input handling, direct route transport, and browser journeys · files: `src/**/*.test.ts`, `e2e/` · verify: `npm run build`, `npm run test:e2e`, `npm run vercel-build`, `npm audit --omit=dev` · covers: R1, R2, R4, R5, R7, R8, R9, US-1, US-2, US-3, US-4, US-5, US-6
- [x] T9 — Provision authorized free-tier services, configure OAuth/GitHub, apply migrations, and deploy to Vercel · files: `TOOLS.md`, deployment and migration records · verify: production smoke routes and authenticated Firefox walkthrough · covers: R3, R10, R12, US-1
- [x] T10 — Import and preview an owner-supplied built prototype from the authorized repository · files: authorized GitHub repository · verify: successful production import and preview · covers: R2, R7, US-3
- [x] T11 — Keep the dashboard primary action readable at compact desktop widths · files: `src/styles/admin.css`, `e2e/admin-proposal-workflow.spec.ts` · verify: compact-width label and overflow assertion plus production Firefox check · covers: R6, US-6

## Current execution status (2026-10-11)
- **Local app:** proposal/auth/sharing/GitHub/email UI and service workflows implemented; latest full run passed Astro check (113 files, 0 diagnostics), lint, format, 25 Vitest files (85 tests), 11 Chromium E2E tests, Vercel serverless runtime import, and `npm audit --omit=dev` (0 vulnerabilities). E2E uses an ephemeral PGlite database and signed local owner session, and covers the owner proposal lifecycle, share revoke failure/retry, email sender safeguards, mobile admin, prototype isolation, comparison pointer/keyboard controls, anonymous access, logout failure/success, and single-line primary action at compact desktop width. Proposal editor includes a saved-draft comparison; inspected GitHub SHA is sent and validated at import; capture/import metadata merges into the latest locked draft state.
- **Hosting/data:** Vercel production `https://proposal-studio-orpin.vercel.app` is Ready at `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4`; Neon free-tier and private Blob are connected; production migrations, including rate-limit buckets, applied.
- **Production smoke check (2026-10-11):** `/` and `/login` return 200; anonymous `/admin` redirects 302 to login and anonymous `/api/admin/proposals` returns 401. The allowlisted Google session opened `/admin/settings`; it displays Resend configured, the test-only sender warning, and leaves global notifications disabled.
- **OAuth/GitHub:** Google consent is External/Testing and only the owner account is a tester. The production OAuth client and secrets are configured in Vercel; allowlisted owner sign-in was verified. GitHub App `creative-tech-proposal-studio` is installed only on `dav033/maros-construction-web` with metadata/contents read-only. Production callback succeeded and the repository picker lists that sole authorized repository. A self-contained static import fixture was imported and previewed successfully from `proposal-studio/p008-import-smoke`, pinned to commit `cb10529f6642a980f967e13d3cc0d7f160158508`.
- **Notifications:** Resend production key is configured with Sending access. The owner-only test flow succeeded using `onboarding@resend.dev`; the global notification toggle remains off and the application rejects enabling prospect mail with this test-only sender. A verified sender domain is required before enabling prospect notifications.
- **Coverage:** 25 Vitest files / 85 tests include direct transport for proposal create/edit/archive/duplicate/publish/share/capture, GitHub install/import, email settings and notification retry; race regressions cover concurrent draft edits during capture and import. The latest local authenticated browser suite passes 11/11 Chromium tests. Production GitHub import/preview was verified against the owner-installed repository and the QA proposal was archived afterward.
- **T10 completion (2026-10-11):** production admin imported `proposal-studio-import-demo` from `proposal-studio/p008-import-smoke`, pinned to `cb10529f6642a980f967e13d3cc0d7f160158508`. Both the integration sandbox preview and proposal editor comparison rendered the imported fixture. QA draft `ad95dbbb-85e4-4742-a68c-5e53edcf19f3` was archived without publishing; DELETE returned 200 and the workspace returned to zero proposals.
- **HTTP smoke check:** `/` and `/login` returned 200; anonymous `/admin` redirected 302 to login; anonymous capture and GitHub import APIs returned 401.
- **Audit:** proposal create/update/publish/archive, share issue/revoke and GitHub connect/import/disconnect events now persist in their mutation transactions. Sensitive admin routes use Postgres-backed per-owner limits; migration and middleware are deployed. Request JSON is bounded by actual stream bytes, even without `Content-Length`, and maps media-type/size/JSON failures to 415/413/400. Malformed `Origin` is rejected safely; concurrent uploads/imports preserve the latest draft content.
- **Deployment fix:** `@astrojs/vercel` is pinned to 11.0.12 and `vercel-build` imports the generated function to prevent the upstream 11.0.13 Rolldown runtime regression from returning.
- **T11 completion (2026-10-11):** Firefox production inspection measured the compact desktop CTA wrapping onto two lines at 745 CSS px. The dashboard action now uses `white-space: nowrap` and does not shrink; its E2E assertion checks one line and no horizontal overflow. Commit `7ed2d7c` is pushed, and deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4` is READY. Production Firefox confirms one line / no overflow.

Migration backup, rollback, and recovery steps are documented in the workspace at `docs/database-recovery.md`, linked from its README, addressing R10.

## Test matrix
| Area | Verification |
|---|---|
| Domain validation | slug uniqueness, revision transitions, notification opt-in and outbox idempotency |
| Auth | allowlisted OAuth success; non-allowlisted rejection; CSRF/state mismatch; session expiry/revocation |
| Admin API | unauthenticated and malformed input rejected; all write endpoints authorize; no private fields exposed |
| Postgres/Blob | migrations apply; draft/revision persistence; atomic publish/outbox; private access; partial import cleanup |
| GitHub adapter | mocked valid installation plus revocation, 401/403/404, rate-limit, timeout, invalid tree, symlink and size/path limits |
| Share links | valid, malformed, unknown, expired, revoked; token hash only in DB; next-request revocation |
| Email | provider stub success/rejection/timeout-after-accept; duplicate queue delivery; opt-out; missing config; retry/manual state |
| Prototype isolation | browser checks parent access/top navigation restrictions, admin cookie isolation, CSP and normal allowed interactions |
| UI/E2E | authenticated create/edit/publish, share/revoke failure and retry, optional email unavailable state, slider pointer/keyboard, responsive layout, prototype isolation, anonymous access, logout failure/success |
| Quality | `npm run check`, `npm run lint`, `npm run format:check`, `npm test`, local Worker build/preview |

## Verification policy
No check is reported as passing unless it actually ran. External provider tests use deterministic fixtures/adapters and do not need real secrets or send real email. Browser tests use local app routes and imported fixtures. After local verification, deploy the authorized free-tier app to its generated Vercel subdomain; custom domains and real prospect email remain out of scope.

## Implementation prompt
See [`IMPLEMENTATION_PROMPT.md`](IMPLEMENTATION_PROMPT.md), intended to be handed to the implementation session after approval.

## Approved rulings
- Keep Astro and add Vercel SSR rather than rewrite the viewer into another framework.
- Use Google OAuth for owner sign-in; use a separate GitHub App for scoped repository access.
- GitHub source is a built static folder, not arbitrary source execution/build.
- Prospects get optional publish-update emails through Resend.
- Use Neon Postgres and private Vercel Blob, deployed first to a Vercel subdomain; custom domain setup comes later.
