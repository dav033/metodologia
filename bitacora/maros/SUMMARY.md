# maros — Summary

_Rewritten (not appended) whenever the state changes. Keep it under ~60 lines._

## Purpose
_What this project is and who it is for._

## Current state
REQ-005 backend T1–T6 are integrated. M3 session 13 recovered reviewed T7 and completed the T8 candidate: administrative MCP parity, additive dry-run and shared R4 guard rails, and MCP actor attribution. Both planned MCP gates, TypeScript and build pass; full lint has two pre-existing errors. Final M3 integration and independent audit still belong to the supervisor.

## Active focus
- REQ-005 M3: review/commit T8, supervisor integration and independent audit before frontend milestones.

## Top pending (see PENDING.md)
- P-010/P-012: manual SQL before deploying REQ-005; agents never connect to the shared database.
- P-011: audit durability/atomicity and concurrent R4 protection remain deferred.

## Recent decisions (see DECISIONS.md)
- D-003: central MCP dry-run and attribution, shared domain previews and explicit schema-only fallback.
- D-002: explicit route/tool inventory; D-001: observable best-effort audit fallback.

## Known issues
- Backend full lint: quickbooks-auth.service.spec.ts:218 unbound method; invoice-scans.service.ts:685 useless escape.

_Last updated: 2026-10-14_
