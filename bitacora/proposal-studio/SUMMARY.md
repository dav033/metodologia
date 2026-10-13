# proposal-studio — Summary

_Rewritten whenever the state changes._

## Purpose
Create lightweight, personalized public design proposals for prospects. David prepares the prototype and captures the prospect’s public website; prospects compare both with a draggable divider and interact with the proposed page.
Last confirmed with owner: 2026-10-10.

## Current state
The latest production deployment is `dpl_4C3sBbuMtKTNLRKHUHakGU5Xnbuv` (READY) at `https://proposal-studio-orpin.vercel.app`; it adds visible capture thumbnails and full-size links to the private proposal editor. Production `/login` responds 200, `/admin/...` correctly redirects anonymous visitors to login, and unauthenticated capture reads return 401. No tests were run for this UI fix.

REQ-008 is implemented locally: admin, sign-in, entry, and shared proposal styling is quieter and more consistent; reveals and hover motion are restrained; the comparison has a synchronized keyboard/touch range alternative; and the proposal overview uses semantic table markup. The local development server needed a forced dependency re-optimization to restore React hydration; browser verification then passed at 320, 390, 681, 850, and 1440 px without horizontal overflow. Astro check, lint, targeted formatting, build, and diff checks passed. Automated tests were not run. Changes remain uncommitted and undeployed.

REQ-007 adds the production MCP at `/api/mcp`. The first Oraldenti proposal is draft `oraldenti` (`083cb2df-1f95-4efd-8a04-c69bd8f7b7c9`) with three verified private captures, three page-specific findings, and three redesign deliverables. It remains unpublished until David provides the prototype repository and built output path. Do not create a share link before importing and validating the prototype.

REQ-003 and REQ-004 are implemented in the local Astro SSR workspace `~/dev/proposal-studio`, tracked in private GitHub repo `dav033/proposal-studio` on `feat/proposal-comparison` at commit `7ed2d7c`. The source is committed and pushed. Production `https://proposal-studio-orpin.vercel.app` is READY at deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4`; it uses Neon and private Vercel Blob with migrations applied. Google owner OAuth and GitHub read-only import are configured. The P-008 fixture was imported and previewed from its authorized branch; its temporary draft was archived. A clearly labeled temporary QA proposal verified that `/s/[token]` renders Starwind, the 21st.dev Spotlight island, Motion, and the named summary region; its token was revoked (404), the proposal archived, and the admin list returned HTTP 200 with zero active proposals. No prospect email was sent.

The visual system uses source-owned Starwind Button/Card/Badge components, one attributed MIT 21st.dev React island, and Motion reveals respecting reduced-motion preferences. Admin auth remains protected while share links are public. The latest full suite passes 85 Vitest tests and 11 Chromium E2E tests; Vercel runtime build passes and production dependency audit reports zero vulnerabilities. The compact dashboard CTA stays on one line without horizontal overflow.

## Active focus
- Keep prospect notifications disabled until a sender domain is verified. The current Resend sender is test-only.
- Add a custom application domain after David purchases one.
- Keep the visual system as implemented; extend it to editor/settings only if a later requirement calls for it.

## Top pending
- P-006: verify a sender domain before enabling prospect notifications.
- P-007: add the custom domain after purchase.
- The default branch of `dav033/maros-construction-web` has no built static `index.html`; the separate P-008 fixture branch has already proven import and preview.

## Recent decisions
- D-002: keep the proposed page interactive within the comparison.
- D-003–D-005: managed Astro/Vercel services, app authorization, and Postgres-backed rate limits.
- D-006: Starwind UI with a scoped, attributed 21st.dev Spotlight React island.

## Known issue
Some sites block automated capture or iframe embedding; capture failures are reported and the proposal keeps a direct prototype link.

_Last updated: 2026-10-11_
