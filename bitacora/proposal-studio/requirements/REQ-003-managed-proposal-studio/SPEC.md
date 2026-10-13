---
id: REQ-003
status: done
created: 2026-10-10
track: deep
---
# REQ-003 — Managed Proposal Studio

## Problem and goal
The current product is a static proposal viewer. Preparing and sharing a real proposal has no managed lifecycle, access control, persistence, or revision notifications. Build a serious, low-volume admin application that lets David author proposals, import his own static prototype from GitHub, create controlled prospect links, and optionally notify the prospect when a revised proposal is published.

**Success:** David signs in, manages a proposal in an administration panel, selects a static prototype folder from a connected GitHub repository, previews the existing-versus-proposed comparison, issues a revocable expiring link, and can opt the prospect into an email when a new published revision is ready.

## Users and actors
- David: sole administrator and proposal author for the first release.
- Prospect: opens a bearer link without creating an account.
- Google OAuth: authenticates the administrator.
- GitHub App: provides narrowly scoped read-only repository access.
- Resend: sends optional transactional update emails.
- Vercel Functions, Neon Postgres, Vercel Blob: application runtime, relational data, and private assets/prototype snapshots.

## In scope
### US-1 — Secure admin access (P1, Must)
Google OAuth login for one explicitly allowlisted admin email. There is no public registration. All admin HTML routes, API routes, server actions, and asset mutations enforce the same authenticated owner check server-side. Add logout and session revocation.

### US-2 — Proposal administration (P1, Must)
An admin dashboard lists proposals, status, last update, prospect contact, and active share links. Create, edit, preview, publish, archive, and duplicate a proposal. Store draft changes separately from the last published revision. Preserve current capture, findings, offer, timeline, price, optional owner-recorded video URL, contact CTA, slug, and the draggable interactive screenshot/prototype comparison.

### US-3 — GitHub prototype source (P1, Must)
Connect a GitHub App installation; browse only repositories granted to that installation, choose branch/commit and a folder containing the already-built static prototype, preview it, then import a pinned snapshot. Start with `contents:read` and repository metadata read only. Do not push, create commits, run Actions, install dependencies, or execute imported build scripts. Record repository ID, path, branch, commit SHA, and import time. Manual re-import creates a new immutable prototype revision.

### US-4 — Protected share links (P1, Must)
Create one or more prospect links with configurable expiration (1, 7, or 30 days; default 7 days), revoke immediately, and issue a replacement. Generate high-entropy random bearer tokens; store only a cryptographic hash; show the raw URL once. Enforce expiry/revocation at request time, return a neutral unavailable page, and mark pages `noindex`. Do not add e-signature, prospect accounts, or view analytics.

### US-5 — Optional update emails (P1, Must)
Global mail settings show whether the provider is configured and allow sender name/address and a test message. The Resend API key stays in platform secrets, never in the database or UI. On each published revision, optionally create one durable outbox event and attempt delivery to the proposal's explicitly entered prospect address with a short change note and that proposal's active share link. The feature is opt-in globally and per proposal. Draft autosaves do not send mail. Record delivery state, prevent duplicate sends per revision/recipient, and surface failures for manual retry. If Resend is not configured, publication still succeeds and the notification is visibly marked as not sent. Use Resend's idempotency key for safe retries during its documented 24-hour retention window.

### US-6 — Material administration experience (P1, Must)
Build a polished, responsive Spanish admin UI using Material 3 interaction and component conventions, themed with the existing Catppuccin Mocha mauve/lavender preference. Include dashboard, proposal list/detail/editor, share-link controls, GitHub connection, email settings, validation feedback, empty/loading/error states, and keyboard/accessibility support. Keep the prospect proposal page focused on the proposal, not admin implementation details.

## Out of scope
- Multi-user organizations, roles, public registration, CRM/outreach pipeline, prospect analytics, e-signature, billing/payments, automatic website reconstruction, domain purchase, custom-domain DNS, GitHub write access, automatic build/execution of repository code, and automatic deployment of prototypes.
- Replacing David's authorship of prototype code; this requirement only imports a built static directory.

## Architecture decision
- Retain Astro and use its official Vercel adapter with SSR/serverless routes.
- Better Auth for Google OAuth/session lifecycle, Drizzle ORM, and Neon Postgres installed through Vercel Marketplace.
- Private Vercel Blob for screenshots and immutable static prototype snapshots. Never serve imported HTML/JS in the authenticated app's parent context; load it inside a restrictive sandboxed iframe (`allow-scripts` only plus explicitly justified capabilities, never combine `allow-scripts` and `allow-same-origin`).
- GitHub App installation with repository contents read-only; pin imports to a commit SHA and validate tree entries, file count/size, paths, and content types. Do not fetch arbitrary URLs from user input.
- Resend behind a mail-provider adapter. Persist publish notifications in a Postgres outbox in the same transaction as the published revision; attempt delivery after commit with a provider idempotency key and expose pending/failed events for manual retry.
- Material 3-inspired UI built with the existing Astro approach; avoid a framework migration unless the implementation audit proves it necessary.

## Requirements and invariants
- R1. Enforce the owner allowlist and authorization server-side on every administrative operation; UI hiding is not authorization.
- R2. Validate all external input as `unknown`, including OAuth profile data, webhook/request bodies, GitHub API responses, configuration, and email provider responses.
- R3. Store OAuth/GitHub credentials and Resend API keys only as encrypted platform secrets; minimize scopes and allow explicit disconnect/revocation.
- R4. Hash share tokens at rest with a modern cryptographic hash; use cryptographically secure random values; compare safely; enforce expiry/revocation on every share request; redact bearer tokens from application logs.
- R5. Use secure, HttpOnly, SameSite cookies; CSRF protection for state-changing browser operations; rate-limit login/callback, share-link creation, and provider-backed endpoints.
- R6. Preserve the screenshot capture's existing DNS-pinning and SSRF protections. Any capture request remains server-side and uses that boundary; no arbitrary network fetch from the Worker.
- R7. Pin each GitHub-imported artifact set to a repository and commit. Reject symlinks, traversal paths, submodules, oversized files/trees, unsupported MIME types, and missing entry documents. Never evaluate/build repository code.
- R8. Serve prototype content in an isolated browsing context. The admin session/cookies/storage must not be accessible to imported content. Set strict CSP, `Referrer-Policy: no-referrer`, and appropriate `X-Robots-Tag`/robots metadata on private share pages.
- R9. Publish revision and outbox message atomically where supported; queue delivery is idempotent and notification failure cannot roll back a published proposal.
- R10. Add schema migrations with rollback/recovery notes; do not put proposal PII, bearer tokens, OAuth secrets, or full GitHub payloads in logs.
- R11. Admin/prospect interfaces, emails, and validation errors are in Spanish; source code, identifiers, and comments remain in English.
- R12. David explicitly authorized configuring integrations with his existing Vercel, Google, and GitHub accounts and deploying to a free `vercel.app` subdomain after local checks. Do not buy a domain, change DNS, upgrade plans, or send a real prospect email without a later explicit instruction.

## Acceptance criteria
1. An unlisted Google account cannot create a session or read/administer any proposal; the allowlisted owner can log in and log out.
2. Proposal drafts survive reload/restart; publishing creates an immutable revision and the comparison still works at desktop and mobile sizes.
3. GitHub repository browsing exposes only installation-authorized repos. A selected static folder imports at a pinned SHA; traversal, symlink, oversized, missing-index, and API-error cases fail without partial activation.
4. A valid share token renders only its proposal; expired, revoked, malformed, and unknown tokens disclose no proposal data. Revocation takes effect on the next request.
5. Update email is sent at most once per published revision/address, only when opted in and provider config is present. Provider failure is visible/retryable and does not undo publication.
6. No secrets, admin-only data, raw share tokens, local paths, or unpublished drafts leak into public proposal output, HTML metadata, client bundles, or logs.
7. Existing slider remains keyboard and pointer operable; imported prototype interaction does not allow access to the parent/admin origin.
8. `npm run check`, `npm run lint`, `npm run format:check`, unit tests, Postgres integration tests, and browser end-to-end tests pass. Build/Vercel preview runs locally without production credentials.

## Edge cases
- OAuth callback mismatch, denied consent, disabled/deleted allowlisted account, expired session, duplicate account link.
- GitHub revoked/suspended installation, inaccessible repository, branch moved during import, API rate limit/timeout, incomplete recursive tree, binary/large asset, no `index.html`, MIME confusion.
- Simultaneous edits/publish, slug collision, unpublished edits after publish, historical link after revision update, multiple links, repeated revocation, clock boundary at expiry.
- Resend timeout after provider accepted, transient/permanent rejection, duplicate queue delivery, missing verified sender, changed prospect address, absent notification consent.
- Prototype attempts top navigation, forms/popups, storage or parent access; ensure sandbox permissions stay least-privilege while normal proposal navigation remains usable.
- Capture redirect, private/reserved IP, DNS rebinding, timeout, browser failure; no false-success asset.

## Confirmed execution assumptions
- Scope update 2026-10-10: the original no-deploy/no-app-registration constraint was superseded by David's explicit authorization to finish the implementation, configure the existing accounts, provision free-tier Vercel/Neon/Blob resources, and deploy after verification. No custom-domain purchase/DNS or real prospect email is authorized.
- Google is the OAuth identity provider; only David's allowlisted email can administer.
- GitHub means read-only access to private/public repos and import of a built static folder. It does not mean GitHub login or publish/deploy-to-GitHub.
- Prospects receive optional update emails; emails are tied to publishing, not draft edits. Resend is the initial provider, credentials configured later.
- Vercel is the target runtime and storage provider; use a stable `vercel.app` URL before the custom `.dev` domain exists.
- Default share-link lifetime is 7 days; admins can choose 1 or 30 days.
- No deadline has been provided.

## Coverage
| Topic | State |
|---|---|
| Goal and actors | Proposed |
| Admin/OAuth | Defined with Google and owner allowlist assumption |
| Proposal lifecycle | Defined; draft and immutable published revision |
| GitHub access | Defined as read-only import of built static folder |
| Share security | Defined; hash, expiry, revocation, request-time enforcement |
| Email behavior | Defined; opt-in per proposal/publish and durable queue |
| Design | Defined; Material 3 patterns and existing accent palette |
| Cloud architecture | Approved; Astro/Vercel + Neon + private Blob |
| Tests and acceptance | Defined |
