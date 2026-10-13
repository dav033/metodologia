# proposal-studio — Architecture

**Last verified:** 2026-10-11 against `~/dev/proposal-studio`, Neon production migrations, Vercel deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4`, and production HTTP/share-route/UI checks.
**Audit status:** partial · **Coverage:** app source, 85 unit/integration tests, 11 browser tests, Vercel runtime, Neon/Blob provisioning, production routes, owner login, production GitHub import/preview, temporary share-link verification with cleanup, and compact-width admin CTA rendering · **Gap:** additional authenticated journeys and failure branches remain; the default branch has no built static HTML artifact; Resend sender is not configured.
Re-check against the code and update both whenever you edit this file.

_Living document: the current truth, edited in place (C4 levels 1–2 + a lean arc42). The *why* of changes lives in
DECISIONS.md, risks and debt in PENDING.md. Keep it under 150 lines; delete sections that don't apply. For business
projects, sections 3–6 describe actors, steps, systems, documents and handoffs instead of containers and modules._

_Update it in the same commit when a container, a module's public API, an owned table, an external integration or
a key flow changes._

## 1. Goals and quality priorities
- Purpose: let David send prospects a public proposal page that compares their existing website with David’s working redesign prototype.
- Users: David authors proposal data; prospects view public links without signing in.
- Last confirmed with owner: 2026-10-10.
- Priorities: simple authoring and low operating cost; visual clarity of the comparison; no account or backend setup for prospects.

## 2. Constraints and conventions
- Standalone application repo: `~/dev/proposal-studio` (registered as workspace role `app`).
- David authors proposals; prospects use time-limited public share URLs without signing in.
- Google OAuth allowlists one verified owner. Production credentials are configured and the owner login was verified; Google consent remains External/Testing.
- The `vercel.app` deployment is public at the platform layer; app routes own authorization.

## 3. Context (C4 level 1)
- David uses authenticated Astro routes to edit drafts, upload private captures, optionally import a static prototype, then publish an immutable revision.
- Publishing may create an idempotent mail outbox record when notifications are configured and opted in.
- A prospect exchanges a high-entropy share token for a scoped HttpOnly asset cookie; each private asset read rechecks link expiry/revocation.

## 4. Containers (C4 level 2)
One Astro SSR app is deployed to Vercel Functions. Neon stores auth, proposal, revision, link, integration, settings, outbox, and audit schema. Private Vercel Blob stores captures and immutable prototype files. The local Playwright capture CLI retains its DNS-pinning and SSRF protections.

| Container | Tech | Responsibility | Owns data | Talks to (protocol) |
|---|---|---|---|---|
| app | Astro 7, TypeScript, Vercel adapter 11.0.12 | Admin SSR, proposal/share rendering, JSON APIs | Neon Postgres and private Blob | Browser, Neon WebSocket, Vercel Blob, Google OAuth, GitHub App, Resend |

## 5. Modules
| Module | Responsibility | Public API (facade / events) | Tables it owns | Depends on |
|---|---|---|---|---|
| `src/features/auth` | Google OAuth and owner allowlist | `getAuth` | Better Auth tables | Better Auth, Drizzle, Google |
| `src/features/proposals` | Draft lifecycle, immutable revisions, publish/outbox transaction, race-safe private capture persistence | proposal services/contracts/capture | proposal, proposal_revision | Drizzle, Blob, notifications |
| `src/features/sharing` | Token issue/revoke/check and scoped asset session | share services/token utilities | share_link | Web Crypto, Drizzle |
| `src/features/github` | Installation verification and static tree import validation | GitHub services/client/contracts | github_installation, prototype revisions | GitHub REST, Blob |
| `src/features/notifications` | Mail settings, encrypted outbox fields, delivery and retry | notification services | mail settings/outbox | Resend HTTP API |
| `src/features/security` | Atomic per-owner request limits for sensitive admin operations | route policy and limiter | admin_rate_limit_bucket | Drizzle, Neon |
| `src/pages/api/admin` | Owner-authorized transport, input validation, response mapping | HTTP routes | none | feature services |
| `scripts/verify-vercel-runtime.mjs` | Ensure the built serverless entry imports without build-only Rolldown | `npm run vercel-build` | none | Vercel function output |

The Astro UI uses a small, project-owned set of Starwind UI Button, Card, and Badge components. Tailwind v4 is available for these components without replacing the existing CSS token system or applying Tailwind Preflight. React is hydrated only for the 21st.dev-derived Spotlight cards on both static proposal previews and prospect-facing `/s/[token]` share pages. Motion's `inView` powers short section reveals; reduced-motion users see static content and no pointer-tracking glow.

## 6. Key flows (max 3)
1. Owner edits a draft, compares its saved state in the divider preview, captures/uploads the current-site image, optionally imports static output pinned to the inspected Git commit, and publishes a frozen revision.
2. Owner issues an expiring one-time-visible token. The prospect route validates it and grants scoped asset access; revocation/expiry are checked on later reads.
3. Publish may enqueue an opted-in update email. Delivery follows commit, is idempotent, visible, and manually retryable.

## 7. Cross-cutting concepts
Strict schema validation, bounded JSON/multipart stream reading with deliberate input errors, malformed-Origin rejection, token hashing, private asset authorization, migrations, GitHub path checks, inspected-commit pinning, mail idempotency, atomic PostgreSQL rate limits, and transactional audit events exist. The current suite has 85 unit/integration tests and 11 browser tests, including public-proposal Starwind components, Spotlight pointer treatment, reduced-motion behavior, mobile overflow, comparison controls, admin component rendering, and compact-width CTA wrapping. The suite also covers proposal lifecycle/immutable revisions, share issue/revoke/expiry, installed-repository enforcement and partial import cleanup, notification success/idempotency/retry after timeout/provider rejection, rate-limit windows/concurrency/policy matching, owner allowlist, migration constraints, direct transport for authenticated proposal/GitHub/email operations, concurrent draft edits during capture/import, commit mismatch and incomplete cleanup, comparison/login UI, responsive layout, prototype sandbox, and Vercel runtime startup. A production share smoke also verified accessible named summary markup and cleanup after revocation/archive. Remaining quality gaps are additional authenticated browser journeys (for example, integrations and notification settings) and additional failure branches. GitHub API HTTP/error-boundary cases have deterministic mocked tests.

## 8. Deployment
Production is `https://proposal-studio-orpin.vercel.app` (project `proposal-studio`, team `dav033s-projects`, region `iad1`), currently on READY deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4`. Production migrations, including the atomic rate-limit bucket, are applied; Neon and private Blob are free-tier. `npm run vercel-build` includes an isolated runtime import regression check. Adapter is pinned to 11.0.12 because 11.0.13 imports Rolldown at runtime and fails on Vercel. Google credentials are configured and owner sign-in remains valid after this deployment. GitHub App `creative-tech-proposal-studio` is installed only on `dav033/maros-construction-web` with metadata/contents read-only; imports now use the exact SHA returned by inspection. The repository has only a `public/` directory and no HTML entry document, so no built static output is importable yet. Resend sender verification and custom domain are deferred.

## 9. Data (if non-trivial)
_Main entities and relationships, owning module, retention._

## 10. Decisions, risks, glossary
- D-002: keep the user-supplied prototype interactive beside the current-site screenshot.
- Risks and deferred items: PENDING.md.
- Audit status: partial while additional authenticated journeys and failure branches remain; the authorized GitHub fixture import/preview is complete, though the prototype repository default branch still has no built static HTML artifact.

_For a workspace audit, set status to `complete` or `partial` and summarize coverage here: every confirmed repo,
shared workspace docs, local checks, and independent review. Explain any gap and the next evidence needed. If the
owner confirms that no implementation repo exists yet, keep code analysis `not started` and audit status `partial`;
document only confirmed intent/process context. Keep the per-repo coverage matrix and detailed finding evidence in
the audit notes or report; this document remains the concise product-level current truth._
