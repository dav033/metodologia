# Implementation brief — Managed Proposal Studio

Use this prompt only after REQ-003 and its plan have been approved.

## Role and mission
Act as the senior full-stack engineer responsible for finishing the existing Proposal Studio product, not merely producing a mockup. Work in `/home/david/dev/proposal-studio`. Deliver an operational, locally verifiable admin application that preserves the current prospect-facing screenshot/prototype comparison and adds secure owner administration, proposal revision management, read-only GitHub import, temporary share links, and optional update email.

The owner writes prototype code. The application imports a previously built static folder from GitHub; it does not generate, build, run, or deploy repository code. Do not silently expand this into a CRM, multi-tenant service, analytics product, payment system, or deployment platform.

## Start by understanding the workspace
1. Read the repository `AGENTS.md`/`CLAUDE.md`, `README.md`, package scripts, current routes, data validation, comparison component, capture CLI and SSRF boundary. Read `~/dev/cerebro/GLOBAL.md`, `~/dev/cerebro/proposal-studio/INDICE.md`, relevant brain notes, and this requirement/plan.
2. Inspect `git status`, `git diff`, and all untracked paths before editing. The repository currently has no commits and the existing app files are untracked; preserve them and any changes David has made since this brief.
3. Confirm Astro/Vercel/Better Auth/Neon/Blob/provider versions and compatibility using the linked official docs. If the proposed architecture cannot work on the actual pinned versions, stop before a broad rewrite and document a narrowly scoped alternative for owner review.
4. Create/update an ADR before implementing the material architecture change. Record constraints, alternatives, consequences, data migration, and rollback.

## Product contract
- Single owner at first. Sign in through Google OAuth. Server-side allowlist is the sole gate; no self-service sign-up or admin invitation flow.
- Dashboard and proposal editor are private. Prospect pages require a bearer share token that can expire or be revoked.
- Create/edit drafts without notifying anyone. Publishing freezes a revision. A prospect email is an optional side effect triggered only by publishing a new revision when both global and per-proposal notification options are enabled and an address is present.
- GitHub integration is a separate GitHub App with read-only repository metadata and contents. The owner chooses an allowed repository, ref/commit and an already-built static directory. Store the immutable snapshot and source SHA. Never write to GitHub and never execute imported code.
- Admin UI is Spanish and follows Material 3 interaction patterns with Catppuccin Mocha and mauve/lavender accents. It must be polished and fully usable rather than a landing-page illustration.
- Keep existing proposal comparison behavior and accessibility: handle supports pointer and keyboard; visible prototype elements remain interactable within safe isolation.
- Vercel Functions is the target runtime, Neon Postgres stores structured records/auth/link/outbox, and private Vercel Blob stores screenshots and immutable prototype assets. Resend is the first provider. The API key and OAuth/app secrets are platform secrets, never database records or browser values.
- David later explicitly authorized configuring his existing Vercel, Google, and GitHub accounts, provisioning free-tier Vercel/Neon/Blob resources, and deploying to a generated `vercel.app` subdomain after local checks. Do not purchase/configure a custom domain or DNS, upgrade to a paid plan, or send a real prospect email.

## Required application modules
Keep boundaries explicit and dependencies inward:
1. **Transport/UI:** Astro pages and form/API routes perform authentication, authorization, input parsing/validation, case invocation, and response translation only.
2. **Use cases/domain:** proposal lifecycle, revision publication, share-link issue/revoke/check, GitHub import rules, notification eligibility, and outbox identity/idempotency. Pure business rules should not import Astro, Vercel SDKs, auth SDK, or provider environment.
3. **Infrastructure adapters:** Postgres persistence, Vercel Blob, Better Auth, GitHub REST API, Resend. Validate provider responses from `unknown` at these boundaries. External calls have deadlines and concurrency/size limits.
4. **Configuration:** parse required runtime configuration at startup/request boundary; production fails closed for required settings. Development/test uses explicit fixtures, never permissive production fallbacks.

Do not add repositories or interfaces that only rename one implementation. Introduce adapters at the external provider boundary and at real substitution/testing seams.

## Data and state
Design/migrate normalized tables for:
- Better Auth user/account/session/verification records plus a server-enforced owner allowlist/config.
- Proposal identity and editable draft fields, including prospect name, contact/email, current URL and screenshot key, findings, deliverables, timeline, optional price/video/contact action, and lifecycle status.
- Immutable published proposal revisions, including snapshot content, selected prototype artifact revision, and `publishedAt`.
- GitHub installation/source metadata and prototype artifact revisions (repo ID, ref, commit SHA, selected path, files/manifest, timestamps; never persist raw installation tokens unnecessarily).
- Share-link records with token hash, proposal/revision policy, created/expiry/revocation timestamps and minimal creator metadata. Never persist raw token.
- Notification preferences, outbox event, provider delivery attempts/status, deduplication key, and timestamps. Avoid duplicate PII copies.
- Minimal audit events for admin security-sensitive changes, without token/secret/provider payload values.

Define status transitions and conflict behavior before handlers. Publishing must make a stable version. State the rule for an existing active link after a new revision (recommended: link resolves to the latest published revision while active; store an optional pin only if product acceptance requires it). Apply schema migrations with a documented backup/rollback procedure.

## Security requirements — release blockers
- Enforce exact owner allowlist on every protected server path and mutation, including imported assets and APIs. Check authorization server-side, not just in navigation.
- OAuth uses state/nonce/PKCE and exact callbacks. Set secure `HttpOnly`, `SameSite`, path/domain-aware session cookies and CSRF protection for state-changing requests. Deny if account email/verification/allowlist data is absent or ambiguous.
- Use secure random share secrets with sufficient entropy; persist only a cryptographic hash. Return raw link once. Check token, proposal state, revocation, and expiry on every request. Rate-limit guessing. Never write bearer secrets in logs, analytics, exceptions, page source beyond the link, or referrers. Use noindex and `Referrer-Policy: no-referrer`.
- GitHub App permissions are minimum read-only. Restrict to installed repositories and validate every returned API object. Pin import to immutable commit SHA. Do not accept arbitrary host URLs for GitHub, archives, captures or assets. Use provider API base allowlist, deadlines, response byte caps, pagination caps, and rate-limit handling.
- For Git tree import, reject absolute/traversal names, symlinks, submodules, duplicate normalized paths, unsupported/ambiguous content types, too many files, too many bytes, and an absent valid entry point. Stage in temporary keys; activate only after the full manifest passes. Clean failed staging artifacts. Never execute package scripts or build tools.
- Serve imported HTML/JS in a sandboxed iframe with no `allow-same-origin`. Add only individually justified capabilities; validate whether forms/popups are necessary. A prototype must never read or mutate admin DOM, cookies, local storage, or authenticated APIs. Test the actual browser boundary, not only attributes in a snapshot.
- Preserve the existing SSRF-resistant capture proxy with public-address validation, DNS pinning, redirect revalidation, bounded deadline, and no false-success output. Do not make a new remote-fetch endpoint to support GitHub.
- Secrets in Worker secrets/`.dev.vars` (ignored); add safe `.dev.vars.example`. Never print them. Add security headers and restrictive CSP; document unavoidable iframe policy choices.
- Resend delivery occurs from a durable Postgres outbox after the publish transaction. Use a deterministic Resend idempotency key by revision + normalized recipient. Bound timeouts, persist pending/failed state, and allow explicit admin retry. Account for Resend's 24-hour idempotency retention window. A notification failure is observable and does not undo a published proposal.

## User experience
Implement Material 3 patterns with restrained, consistent visual hierarchy and accessible focus/contrast. Use Spanish labels, empty states, inline validation, confirmation for publish/revoke, clear notification status, GitHub connection status, and useful error recovery. Required views:
- Login and access-denied state.
- Admin dashboard (proposal counts by lifecycle and recent updates, no fake analytics).
- Proposal list/search and create/edit/detail workflow.
- Comparison preview using actual stored screenshot and prototype snapshot.
- Share link issue/list/copy/revoke/expiration controls.
- GitHub connection/repository/ref/static-folder picker with commit provenance.
- Email settings: provider status, sender fields, global opt-in, test-send to admin, and per-proposal prospect recipient/preference/history.
- Responsive layouts and keyboard/screen-reader operation.

Do not expose admin navigation, edit forms, draft-only values, filesystem keys, repository credentials, access token or raw source tree metadata on the prospect route.

## Execution sequence
Work phase by phase. At each phase: update plan progress, implement the smallest vertical slice, run the relevant checks, review the diff, and fix regressions before moving on.
1. Audit + ADR + domain contracts and migrations.
2. Astro SSR Vercel adapter setup, Neon/Postgres and private Blob integrations, runtime config, test harness.
3. Better Auth Google OAuth, owner allowlist, login/logout, authorization tests.
4. Proposal draft CRUD, validation, publication/revision history, dashboard/editor, preserve comparison.
5. GitHub App install/read-only repo browsing and safe static snapshot import/preview.
6. Share token create/list/revoke/expiry and protected proposal rendering.
7. Notification preference UI, Postgres outbox, idempotent Resend adapter and admin retry flow.
8. Responsive/accessibility polish, docs, full audit and handoff.

Do not skip a phase to make a visual demo look complete. If a dependency or platform limitation blocks a phase, preserve working code, report exact evidence, and ask only for the external fact/decision needed.

## Test plan and required commands
Use deterministic tests, a disposable local Postgres database, and Blob fakes. Never use real OAuth/GitHub/Resend secrets in CI. Do not assert implementation details or weaken checks to get green.

### Unit tests
- Proposal parse/validation, slug uniqueness, draft/publish transitions, immutable snapshot behavior, expiry boundary, token hash generation/compare, revoke behavior, notification eligibility, normalized dedupe identity, GitHub tree path validation and byte/count limits.
- Include regression cases for the iframe divider pointer capture and keyboard controls.

### Integration tests
- Run against a disposable local Postgres database and a Blob test adapter; never against production records.
- Verify protected routes, owner allowlist, proposal writes/reload, publish+outbox transaction, link access statuses, import staging/activation, email idempotency/retries, and redacted responses/logging.
- Stub Google OAuth, GitHub API, and Resend at their HTTP boundary. Cover success, denial, malformed payload, 401/403, timeout, rate limit, provider rejection, and timeout-after-accept.

### Browser end-to-end tests
- Locally authenticate as a deterministic test owner (test-only fixture; no production bypass).
- Create/edit/publish proposal; import a fixture repository directory; open a valid prospect link; test unknown/expired/revoked link; publish another revision; verify notification preferences and delivery history; test failed email handling.
- Check comparison at desktop and narrow mobile widths, pointer drag including crossing prototype area, keyboard movement, link interaction, and iframe isolation attempts against `window.parent`, top navigation, storage, and admin cookies/API.
- Check keyboard focus, labels, error/loading/empty states and no horizontal overflow.

### Quality gates
Add and execute coherent scripts for formatting, lint, type-check, unit/integration tests, Playwright E2E, production build, and Vercel local preview. At minimum run:
`npm run format:check`
`npm run lint`
`npm run check`
`npm test`
`npm run build`
the documented `vercel dev` preview + Playwright E2E command.

If the repository uses different exact names, keep one canonical full-suite command and document it. Record actual commands, outcomes, and known limitations. A command not executed is `not run`, never `passed`.

## Definition of done
- All acceptance criteria in REQ-003 are demonstrated locally.
- All user-visible workflows work beyond a static mockup; data is durable in Postgres and assets use private Blob storage.
- Full tests, type-check, lint, formatting and build/preview pass, or precise failures are documented without concealing them.
- Security and API contracts have dedicated regression tests; imported code is isolated in browser tests.
- README/setup guide explain local bindings, Google OAuth/GitHub App/Resend credentials, Worker secrets, migrations, test commands, and later manual production setup. No secrets are checked in.
- Update architecture, ADR, brain summary/index, pending list, session log, and implementation report. Review `git status`/`git diff`; preserve unrelated and untracked work. Do not commit or push. Deploy only the authorized free-tier app to its generated Vercel subdomain after checks; do not buy/configure a custom domain or DNS.

## Official references to verify during implementation
- Astro Vercel adapter: https://docs.astro.build/en/guides/integrations-guide/vercel/
- Better Auth Astro integration: https://better-auth.com/docs/integrations/astro
- Better Auth Drizzle/PostgreSQL adapter: https://better-auth.com/docs/adapters/drizzle
- Neon Marketplace integration: https://vercel.com/marketplace/neon
- Vercel Postgres Marketplace guidance: https://vercel.com/docs/postgres
- Vercel Blob private storage: https://vercel.com/docs/vercel-blob/private-storage
- Resend idempotency keys: https://resend.com/changelog/idempotency-keys
- Resend sender setup: https://resend.com/docs/dashboard/domains/introduction
- GitHub Apps vs OAuth scope minimization: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/deciding-when-to-build-a-github-app
- Vercel Functions runtime: https://vercel.com/docs/functions/runtimes
- Material UI's Material Design version note (if considering its React package): https://mui.com/material-ui/getting-started/

## Final report format
In Spanish, tell David what is operational, what tests ran with actual outcomes, which external setup remains for him (OAuth registration, GitHub App installation, Resend sender/domain, later domain/deploy), whether any risk remains, and explicitly invite him to try the admin flow and report what to adjust. Keep it direct and lightly informal; do not imitate errors so heavily that instructions become unclear.
