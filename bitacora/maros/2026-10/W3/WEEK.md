---
status: draft
---
# maros — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- REQ-004 verified motion/navigation, mobile layouts and reduced-motion using browser sessions and isolated fixtures. REQ-005 progressed through audited backend roles/access management to the reviewed M3 MCP candidate.

## Done
- REQ-004 Projects/detail loops passed at 1440/456 px; task overlays retained stable geometry. A local fixture measured card memoization reducing ScriptDuration by 77–79%; this is not a production benchmark. Frontend typecheck, lint (164 warnings, 0 errors) and isolated build passed.
- REQ-005 M1 audit PASS; M2 audit PASS-WITH-FIXES added repository regression coverage. T6 added nine role/access MCP tools.
- M3 candidate 383f1e4 contains T7's 253-route inventory/44 missing tools and T8's dry-run, shared R4 refusals and actor audit. Final planned gates pass: 253 MCP tests and 447 MCP+users tests; types, touched lint and build pass. Antagonist fixed two findings; re-review SOUND. Integration acceptance and independent M3 audit remain pending.

## Decisions
- D-001: observable best-effort role audit. D-002: explicit API/MCP capability map. D-003: centralized simulations and attribution; shared domain previews and explicitly schema-only generic previews.

## Not done / dropped
- Previous partial M3 candidate was rejected for missing integration scope declarations, not a red test. Both tasks are now committed/verified in the new assigned worktree, awaiting supervisor settlement.
- Backend global lint retains two known errors and 19 warnings. Task-workspaces has no dedicated suite; its changed assignment service is covered by the new MCP regression. No SQL applied or database contacted.

## Carried over to next week
- P-010/P-012: manual SQL before deployment. P-011: durable/atomic audit and concurrent R4 protection. Remaining REQ-005 frontend/documentation milestones follow accepted M3 integration and audit.
