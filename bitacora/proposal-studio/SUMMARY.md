# proposal-studio — Summary

_Rewritten whenever the state changes._

## Purpose
Create lightweight, personalized public design proposals for prospects. David prepares the prototype and captures the prospect’s public website; prospects compare both with a draggable divider and interact with the proposed page.
Last confirmed with owner: 2026-10-10.

## Current state
Production remains on deployment `dpl_4C3sBbuMtKTNLRKHUHakGU5Xnbuv` at `https://proposal-studio-orpin.vercel.app`. Consola phases 1–2 are committed as `e99b2ff` on `feat/consola-redesign` and fast-forward pushed to `main`. Phase 3 is committed locally as `090e9b4` on the same branch; it has not been pushed or released. Neon isolated-branch migration validation is waiting for owner GitHub sign-in in the agent Firefox clone.

Consola phases 1–3 are implemented locally. Phase 3 adds bounded automatic website capture with private Blob storage and manual upload fallback; aggregate share opens throttled to one per link per 30 seconds; generic no-contact link requests serialized with link creation; and an authenticated keyboard command palette. The additive Drizzle migration is generated. Local checks and independent reviews pass after fixes. Neon CLI OAuth was started in the agent Firefox clone, but GitHub sign-in is required before isolated branch validation; no production migration/deployment or phase-3 push has happened.

Fresh phase-3 checks passed: Astro check (168 files, 0 diagnostics), ESLint, Prettier, `npm run vercel-build` including the Vercel runtime import check, `node --check scripts/safe-proxy.mjs`, and `git diff --check`. Automated tests were not run. Independent reviews found and closed two findings: an expired-link label issue and field-level server-error mapping for the new content editor. Standards review returned SOUND. No deployment command was run.

The Oraldenti proposal remains draft `oraldenti` (`083cb2df-1f95-4efd-8a04-c69bd8f7b7c9`) with three verified private captures, three page-specific findings, and three redesign deliverables. It remains unpublished until David provides the prototype repository and built output path. Do not create a share link before importing and validating the prototype.

The managed app uses Astro SSR on Vercel, Neon, private Vercel Blob, Google owner OAuth, and a read-only GitHub App. Admin routes remain protected; public share links are short-lived and revocable. Proposal revisions and audit events are persisted in Postgres.

David asked whether the existing Advin VPS PostgreSQL can serve both development and production. Read-only inspection confirmed host PostgreSQL 16.15 is active, listening only on `127.0.0.1` and Docker bridge `172.20.0.1`; it has two small databases (22 MB total), 25 GB free on root, and 15 GiB RAM. No server settings or data were changed. Production app placement is still undecided: direct Vercel access needs static egress or another secure network path; the alternative is moving Astro SSR to the VPS. Keep Neon and D-003 unchanged until David chooses the topology.

## Active focus
- Phase-3 release P-016 awaits completing GitHub sign-in in the agent Firefox clone, isolated migration validation, fast-forward push, production migration, and deployment. Local commit: `090e9b4`.
- P-012 minor MCP error-code/token-documentation/storage follow-ups remain separate.
- Import and validate the Oraldenti prototype when its repository and built output path are available (P-011).
- Keep prospect notifications disabled until a sender domain is verified.

## Top pending
- P-010: reauthenticate Claude Code and verify a read-only Proposal Studio MCP call.
- P-012: release decision and minor MCP follow-ups.
- P-011: import and share the Oraldenti proposal after David supplies its repository/output path.
- P-014: decide whether to disable SSH password authentication.
- P-007: add a custom domain after purchase.

## Recent decisions
- D-002: keep the proposed page interactive within the comparison.
- D-003–D-005: managed Astro/Vercel services, app authorization, and Postgres-backed rate limits.
- D-006: Starwind UI with a scoped, attributed 21st.dev React island.
- D-008: use the Consola direction for app UI.
- D-009: keep inactive public share links indistinguishable; show exact state only in the authenticated editor.

## Known issue
Some sites block automated capture or iframe embedding; capture failures are reported and the proposal keeps a direct prototype link.

_Last updated: 2026-10-13_
