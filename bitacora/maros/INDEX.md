# Index — maros

_Generated 2026-10-25 16:26 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/maros) · [graph](http://127.0.0.1:8765/p/maros/graph)  
**Last activity:** 2026-10-25

## Workspace

- **frontend** → `/home/david/dev/maros/maros-next`
- **backend** → `/home/david/dev/maros/maros-nest`

## Needs attention

- REQ-005: executor finished — review & merge

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-fix-document-scans-and-estimate-email-fl/SPEC.md) | Fix document scans and estimate email flow | `in-progress` | [in-progress](requirements/REQ-001-fix-document-scans-and-estimate-email-fl/PLAN.md) |  |
| [REQ-002](requirements/REQ-002-expose-project-linked-leads-in-the-crm/SPEC.md) | Expose project-linked leads in the CRM | `done` | [done](requirements/REQ-002-expose-project-linked-leads-in-the-crm/PLAN.md) |  |
| [REQ-003](requirements/REQ-003-adopt-bencho-interactions-across-maros-c/SPEC.md) | Adopt Bencho interactions across Maros CRM | `done` | [done](requirements/REQ-003-adopt-bencho-interactions-across-maros-c/PLAN.md) |  |
| [REQ-004](requirements/REQ-004-transversal-maros-ux-and-motion-refineme/SPEC.md) | Transversal Maros UX and motion refinement | `in-progress` | [in-progress](requirements/REQ-004-transversal-maros-ux-and-motion-refineme/PLAN.md) |  |
| [REQ-005](requirements/REQ-005-friendlier-roles-and-permissions-ux-func/SPEC.md) | Friendlier roles and permissions (UX + functionality) and full-power admin MCP | `approved` | [done](requirements/REQ-005-friendlier-roles-and-permissions-ux-func/PLAN.md) | report ✓ |

## Top pending (urgency, then complexity)

- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is dep · high/S
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · high/S
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so  · med/M
- P-014 · Make the duplicate-pending check race-safe for access requests: the backend already refuse · low/S
- P-015 · Add a server-side test for settings/users and settings/roles gating (null user → dashboard · low/S
- P-013 · Apply the explanatory no-access state (`NoAccessState`) to the other permission-guarded pa · low/M

## Recent decisions

- D-006 — The `member` role is resolved in code, and last-admin counts internal users only
- D-005 — Access requests grant nothing; resolution is single-shot and self-resolution is refused
- D-004 — Permission model v2 is metadata beside the existing codes, with shared guard rails
- D-003 — Central MCP simulation and attribution with shared role guard rails
- D-002 — Explicit MCP capability inventory and system attribution

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W4](2026-10/W4/WEEK.md): [25](2026-10/W4/2026-10-25.md)
  - [W3](2026-10/W3/WEEK.md): [15](2026-10/W3/2026-10-15.md), [14](2026-10/W3/2026-10-14.md), [13](2026-10/W3/2026-10-13.md), [12](2026-10/W3/2026-10-12.md)
  - [W2](2026-10/W2/WEEK.md): [11](2026-10/W2/2026-10-11.md), [10](2026-10/W2/2026-10-10.md), [08](2026-10/W2/2026-10-08.md)
