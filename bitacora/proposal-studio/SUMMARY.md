# proposal-studio — Summary

_Rewritten whenever the state changes._

## Purpose
Create lightweight, personalized public design proposals for prospects. David prepares the prototype and captures the prospect’s public website; prospects compare both with a draggable divider and interact with the proposed page.
Last confirmed with owner: 2026-10-10.

## Current state
Production remains on deployment `dpl_4C3sBbuMtKTNLRKHUHakGU5Xnbuv` at `https://proposal-studio-orpin.vercel.app`. Consola phases 1–2 are committed as `e99b2ff` on `feat/consola-redesign` and fast-forward pushed to `main`. A read-only Vercel listing showed no new deployment after the push; no deployment command was run.

Consola phases 1–2 are implemented locally. Phase 1 applies the selected graphite/amber/Geist direction across the approved existing views. Phase 2 adds in-app proposal content editing, published-version and activity history, explicit active/expired/revoked link states, a generic public unavailable-link page, and proposal search/status filters. The private preview copy no longer makes a claim about visit tracking. Phase 3 (auto-capture, link-open tracking, request-new-link, and ⌘K) remains unapproved.

Fresh checks passed: Astro check (160 files, 0 diagnostics), ESLint, targeted Prettier, `npm run vercel-build` including the Vercel runtime import check, and `git diff --check`. Automated tests were not run. Independent reviews found and closed two findings: an expired-link label issue and field-level server-error mapping for the new content editor. Standards review returned SOUND. No deployment command was run.

The Oraldenti proposal remains draft `oraldenti` (`083cb2df-1f95-4efd-8a04-c69bd8f7b7c9`) with three verified private captures, three page-specific findings, and three redesign deliverables. It remains unpublished until David provides the prototype repository and built output path. Do not create a share link before importing and validating the prototype.

The managed app uses Astro SSR on Vercel, Neon, private Vercel Blob, Google owner OAuth, and a read-only GitHub App. Admin routes remain protected; public share links are short-lived and revocable. Proposal revisions and audit events are persisted in Postgres.

## Active focus
- The owner decides whether and when to release the local Consola changes (P-012).
- Phase 3 backend features require a separate approval.
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
