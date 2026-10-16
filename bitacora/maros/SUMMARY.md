# maros — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._

## Current state
REQ-005 (friendlier roles and permissions UX/func + full-power admin MCP) is complete across all milestones (M1–M5). Both backend (`feat/req-005-friendlier-roles-and-permissions-ux-func` at `4a80e90`) and frontend (`feat/req-005-friendlier-roles-and-permissions-ux-func` at `8ccc2fa`) branches are fully verified with 100% passing tests (backend jest 499 tests, frontend vitest 422 tests, tsc clean, eslint clean). Final REPORT.md is generated; awaiting owner review and deployment migrations.

## Active focus
- REQ-005 closing and owner review.
- Supabase manual SQL migrations P-010 (`db/add-role-audit-events.sql`) and P-012 (`db/add-access-requests.sql`).

## Top pending (see PENDING.md)
- P-010/P-012: manual SQL before deploying REQ-005; agents never connect to the shared database.
- P-011: atomic role write + audit insert once SQL migrations are applied.
- P-013/P-014/P-015: UX and gating follow-ups.

## Recent decisions (see DECISIONS.md)
- D-004: permission model v2 metadata, templates as copies, shared guard rails.
- D-005: access requests grant nothing by themselves, single-shot resolution, self-resolution refused.
- D-006: member role code resolution, last-admin counting internal active users only.
- D-003: central MCP dry-run and attribution, shared domain previews and explicit schema-only fallback.
- D-002: explicit route/tool inventory; D-001: observable best-effort audit fallback.

## Known issues
- Backend full lint baseline: quickbooks-auth.service.spec.ts:218 unbound method; invoice-scans.service.ts:685 useless escape.

_Last updated: 2026-10-15_
