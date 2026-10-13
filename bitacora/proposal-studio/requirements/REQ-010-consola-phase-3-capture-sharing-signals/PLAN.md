---
req: REQ-010
status: in-progress
created: 2026-10-13
---
# Plan — REQ-010 — Consola phase 3: capture, sharing signals, and command navigation

## Approach
Add a production-compatible Chromium runtime for the existing safe capture flow and invoke it from the authenticated editor save path. Add only aggregate open fields and one pending-request row per inactive share link; keep unknown-token responses indistinguishable and email disabled. Add a small accessible command dialog to the shared admin shell using existing proposal data. Ship behind the already-approved additive migration, validate it on an isolated Neon branch, then migrate and deploy.

## Global constraints
- Keep Astro SSR, Drizzle/Neon, private Blob, same-origin admin auth, existing safe proxy, and public inactive-link indistinguishability.
- Do not add a remote capture service, email, visitor identity, IP, or user-agent storage.
- Bound capture time, dimensions, output size, and concurrent browser work; fail closed on private or reserved network destinations and anti-bot challenges.
- Every new API write validates its external input and returns deliberate errors; public request submissions must not reveal token state.
- No force-push; commit a verified milestone and fast-forward push to `main` per the owner's project rule.

## Tasks
- [ ] T1 — Add the SSRF-safe serverless capture adapter and editor auto-capture flow while retaining manual PNG upload · files: `scripts/safe-proxy.mjs`, `src/features/proposals/capture*`, `src/pages/api/admin/proposals/[id]/capture.ts`, `src/scripts/editor-save.ts`, `src/components/admin/SiteSection.astro`, `package.json`, `package-lock.json` · verify: `npm run check && npm run lint && npm run vercel-build` · covers: R1, R2, US-1
- [ ] T2 — Add share-open aggregates and inactive-link request persistence/APIs/UI, with migration and generic public behavior · files: `src/db/schema.ts`, `drizzle/*`, `src/features/sharing/*`, `src/pages/s/[token].astro`, `src/pages/api/*share*`, `src/components/admin/ShareSection.astro`, `src/scripts/share-client.ts` · verify: `npm run check && npm run lint && npm run vercel-build` · covers: R3–R7, R9–R10, US-2, US-3
- [ ] T3 — Add the accessible global Cmd/Ctrl+K command palette and authenticated proposal search · files: `src/components/admin/AdminShell.astro`, `src/pages/admin/index.astro`, `src/scripts/admin-command-palette.ts`, `src/styles/admin.css` · verify: `npm run check && npm run lint && npm run vercel-build` · covers: R8, US-4
- [ ] T4 — Validate migration on an isolated Neon branch, complete repository checks and independent audits, deploy production migration and app, and verify production health · repo: app · after: T1, T2, T3 · verify: `npm run check && npm run lint && npm run format:check && npm run vercel-build && git diff --check` · covers: R1–R10

## Verification
- Local: `npm run check`, `npm run lint`, `npm run format:check`, `npm run vercel-build`, and `git diff --check`.
- Database: apply the generated Drizzle migration to an isolated branch cloned from production using its direct connection URL; verify the expected tables/columns, then apply the same migration to production through the established migration command after local checks.
- Browser: use the local admin editor to save a public URL without a file and confirm the private screenshot is stored; verify manual upload remains available, inactive-link request renders the generic accepted response and appears in admin, active link open updates only count/time, and Cmd/Ctrl+K keyboard navigation works.
- Production: deploy the built app, confirm the deployment is Ready, `/login` responds, `/admin` redirects without auth, and public link behavior remains reachable.

## Rulings
- T1: Use `@sparticuz/chromium` with `playwright-core` in Node runtime — the current app's local Playwright CLI cannot execute on the remote Vercel function; the existing safe proxy still mediates every destination. Cost if wrong: med (bundle/runtime incompatibility; detected by Vercel build and production capture check).
- T1: Re-capture only when the source URL changes or no screenshot exists, unless the owner selects a manual PNG — avoids needless browser work and preserves explicit screenshots. Cost if wrong: low.
- T2: Count rendered-browser open signals; do not attempt unique-human identification — respects privacy and avoids prefetch from many non-JS scanners, though some automated browsers may count. Cost if wrong: low.
- T2: Keep one owner-visible pending request per inactive link; replacement link creation resolves all outstanding requests for that proposal atomically. Cost if wrong: low.
- T3: Search proposal names/slugs from the existing authenticated list, and include fixed navigation commands for Proposals and GitHub — no new endpoint or authorization boundary. Cost if wrong: low.
- Release: Owner's “continúa aprobado todo” authorizes the specified migration, commit/fast-forward push, and production deployment. Cost if wrong: none; this is the explicit approval recorded in SPEC.md.

## Progress log
- 2026-10-13: Scope approval recorded; inspected current capture, share-link, admin, migration, and production tool contracts. Official Vercel runtime limits and `@sparticuz/chromium` usage checked. Implementation starts with T1.
