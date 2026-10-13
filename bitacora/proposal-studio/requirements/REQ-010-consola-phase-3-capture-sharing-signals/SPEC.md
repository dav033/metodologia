---
id: REQ-010
status: planned
created: 2026-10-13
track: deep
---
# REQ-010 — Consola phase 3: capture, sharing signals, and command navigation

## Problem & goal
The owner currently has to capture and upload the prospect's existing website manually, cannot see whether a shared proposal was opened, and has no in-app path for a recipient with an inactive link to request an updated one. Admin navigation also requires returning to the proposal list.

**Success looks like:** saving a proposal can produce its private current-site screenshot automatically; the owner can see approximate open counts and pending link requests; an unavailable-link visitor can leave a no-email request without learning whether a token exists; and Cmd/Ctrl+K opens a keyboard-accessible admin command palette.

## Users / actors / stakeholders
- David, the sole authenticated owner and admin.
- Prospects opening public share links.

## Scope (in)
### US-1 (P1, Must) — Automatic current-site capture
As the owner, I want the editor to capture the current site while saving so I can prepare a proposal without manually running a separate command or uploading a screenshot.
**Acceptance:** When a valid public HTTP(S) site URL is saved without a newly selected screenshot, the system attempts a bounded capture and stores it in private Blob storage. Browser startup is limited to 10 seconds, navigation to 25 seconds, output to 8 MiB, and the Vercel function to 60 seconds. Existing manual PNG upload remains available. Capture failure is visible and leaves the saved proposal editable; it never reports a successful capture.

### US-2 (P1, Must) — Approximate share opens
As the owner, I want a per-link open count and last-opened time so I can tell whether a recipient likely viewed a proposal.
**Acceptance:** After each share page load in a browser with JavaScript enabled, the client sends one open signal for the active link. The signal is not retried or deduplicated across reloads, so the aggregate is approximate and may overcount. The authenticated share view shows the count and last-opened time. No IP address, user agent, or visitor identity is persisted; the UI describes the count as approximate and warns that scanners/prefetch may affect it.

### US-3 (P1, Must) — Request an updated link
As a recipient who reaches an unavailable link, I want to request an updated link so the owner can follow up.
**Acceptance:** The generic unavailable page includes a request action. Submitting it returns the same generic accepted response whether the token is unknown, malformed, expired, revoked, or archived. A request tied to a known expired/revoked link for a non-archived proposal is visible in the owner's authenticated UI; unknown, malformed, active, and archived links do not create a row. There is at most one request row per inactive link, and duplicate submissions do not create more rows. Creating any replacement link for that proposal resolves all pending request rows atomically. The app does not send email or collect visitor contact information.

### US-4 (P1, Must) — Admin command palette
As the owner, I want Cmd/Ctrl+K to open a command palette for navigating to proposals, integrations, and matching proposals.
**Acceptance:** The shortcut works on admin pages, does not intercept typing inside editable controls, supports keyboard navigation/escape, and uses existing authenticated proposal data.

## Out of scope
- Prospect email, SMS, or any other outbound notification; email remains disabled per P-006.
- Tracking IP addresses, user-agent strings, named visitors, or analytics beyond per-link aggregate opens.
- Automated capture of extra proposal pages; manual page captures remain unchanged.
- Publicly distinguishing unknown, expired, revoked, archived, or malformed link tokens.
- Changes to production beyond the approved additive migration and deployment needed to ship this scope.

## Requirements
- R1. When the owner saves a public current-site URL without selecting a replacement screenshot, the system shall attempt to capture the site's viewport and upload a valid PNG to private storage.
- R2. If the capture runtime is unavailable, the URL is unsafe, the site fails, or an anti-bot challenge is detected, the system shall report a specific failure and preserve manual upload as a recovery path.
- R3. When an active share page renders, the browser shall submit an idempotent open signal; the system shall atomically update only aggregate count and last-opened fields for that link.
- R4. The owner shall see open count and last-opened time in the authenticated share-link list, labeled approximate.
- R5. When any unavailable-link page is viewed, it shall offer the same request-link action and generic copy.
- R6. When a request is submitted for a known expired/revoked link on a non-archived proposal, the system shall retain a single pending request without storing the raw token, visitor identity, IP, or user agent; unknown, malformed, active, and archived links shall receive the same public response and create no row.
- R7. Creating any replacement share link shall atomically resolve all pending requests for the proposal without changing the public response behavior.
- R8. Cmd/Ctrl+K shall open an accessible command palette throughout the admin shell; Escape closes it, arrow keys move selection, Enter navigates, and focus remains managed within the dialog.
- R9. All database schema changes shall be represented by Drizzle migrations and validated on an isolated Neon branch before production migration.
- R10. Every new API write shall enforce origin/authentication or bearer-session validation as applicable, bounded input, deliberate error mapping, and rate limiting where public abuse could cause persistent writes.

## Edge cases & errors
- Unknown, malformed, expired, revoked, and archived share tokens render equivalent unavailable content and return equivalent request-submission status/body.
- A site may resolve to a private, loopback, link-local, or otherwise prohibited address, redirect to one, exceed deadlines, or return an anti-bot challenge; capture must fail closed.
- Capture can succeed while a later draft save/upload fails; UI must not claim the screenshot is persisted until the upload API confirms it.
- Concurrent open signals must not lose increments. The client sends one signal per rendered page load, without retry or deduplication across reloads.
- Requests for a known inactive link share one persistent request row; duplicate submits do not add rows. Unknown, active, or archived requests create no rows. Creating any replacement link resolves every pending request for its proposal atomically.
- Admin command search with no matches shows an empty state; commands never navigate to unauthenticated write endpoints.

## Constraints
- Astro SSR on Vercel, Neon Postgres with Drizzle, private Vercel Blob, existing same-origin/admin auth, and existing safe capture proxy are retained.
- No new third-party capture service or email service is authorized.
- Capture duration and concurrency must be bounded; public share events must not disclose internal identifiers or persist personal data.
- Project owner rule: complete and verify each milestone, then commit and fast-forward push to `main`; do not force-push.

## Priorities & phases
- Must: US-1, US-2, US-3, US-4.
- One release milestone: additive schema + service/API + UI + verification, followed by approved migration and production deployment.

## Timeline & dependencies
- Depends on Consola phases 1–2 at `e99b2ff` and existing capture, share-link, and admin-shell flows.
- Release after local checks, independent review, isolated Neon migration validation, and production migration/deployment.

## Assumptions
- “Automatic capture” means capture the current URL when saving the proposal, with manual PNG upload kept as fallback. No external capture provider is added.
- “Request a new link” means a private owner-visible request flag on the inactive link; David manually creates/shares the replacement. No contact details or automatic notification are collected.
- Opens are approximate browser-render signals, not verified unique human visits; each rendered page sends one signal, with no retry or deduplication across reloads.
- Request submissions always receive the same generic 202 response. Only known expired/revoked links on non-archived proposals persist one request row; active, unknown, malformed, and archived tokens do not persist requests.
- Automatic capture is bounded to 10 seconds for browser startup, 25 seconds for navigation, an 8 MiB PNG, and a 60-second Vercel function duration. On capture failure, the saved draft remains editable and the UI reports that its screenshot was not updated.
- The prior explicit approval “continúa aprobado todo” includes this full phase-3 scope, additive schema migration, production migration, commit/push to main, and production deployment.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- Q: Which pending items are approved? → A: David said “continúa aprobado todo”; all phase-3 items and deployment are approved.
- Q: Should new-link requests send email? → A: No; existing P-006 decision excludes prospect email. Requests are owner-visible only.
