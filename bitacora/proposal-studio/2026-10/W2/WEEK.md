---
status: final
---
# proposal-studio — Week 2026-10 W2 (2026-10-05 → 2026-10-11)

## Highlights
- Implemented and deployed the managed proposal workflow and polished public/admin visual system.
- Completed the Oraldenti production draft with three verified page captures, specific findings, and redesign deliverables; prototype import remains pending.
- Added capture thumbnails and full-size links to the admin editor; production deployment `dpl_4C3sBbuMtKTNLRKHUHakGU5Xnbuv` is READY.

## Done
- Implemented REQ-001 and REQ-003, including Google owner authentication, proposal lifecycle, expiring links, isolated prototype preview, read-only GitHub import, optional Resend notifications, durable rate limits, audit events, and recovery guidance.
- Deployed to Vercel with Neon and private Blob; verified route authorization and health checks.
- Imported and previewed the authorized P-008 static fixture in production, then archived its QA draft.
- Added Starwind UI, a licensed 21st.dev Spotlight island, and reduced-motion-aware Motion reveals across the public share page and admin overview; deployed REQ-004.
- Verified the production `/s/[token]` presentation with a temporary QA proposal, then revoked the token and archived the proposal. Production admin list returned to zero active records; no prospect email was sent.
- Passed Astro check (113 files / 0 diagnostics), lint, format, 25 Vitest files / 85 tests, 11 Chromium E2E tests, Vercel runtime import, and production dependency audit (0 vulnerabilities).
- Committed and pushed the visual-system implementation and responsive CTA fix through `7ed2d7c` to `feat/proposal-comparison`; latest Vercel deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4` is READY.

## Decisions
- D-001: capture the first viewport as an image; leave HTML reconstruction out of the MVP.
- D-006: use Starwind UI with one scoped, attributed 21st.dev Spotlight React island.
- Use an isolated static fixture branch to verify the importer without changing the prototype repository default branch.

## Not done / carried over
- P-006: verify a sender domain before enabling prospect notifications.
- P-007: add a custom domain after David purchases one.
