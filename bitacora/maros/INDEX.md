# Index — maros

_Generated 2026-10-14 13:57 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/maros) · [graph](http://127.0.0.1:8765/p/maros/graph)  
**Last activity:** 2026-10-14

## Workspace

- **frontend** → `/home/david/dev/maros/maros-next`
- **backend** → `/home/david/dev/maros/maros-nest`

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-fix-document-scans-and-estimate-email-fl/SPEC.md) | Fix document scans and estimate email flow | `in-progress` | [in-progress](requirements/REQ-001-fix-document-scans-and-estimate-email-fl/PLAN.md) |  |
| [REQ-002](requirements/REQ-002-expose-project-linked-leads-in-the-crm/SPEC.md) | Expose project-linked leads in the CRM | `done` | [done](requirements/REQ-002-expose-project-linked-leads-in-the-crm/PLAN.md) |  |
| [REQ-003](requirements/REQ-003-adopt-bencho-interactions-across-maros-c/SPEC.md) | Adopt Bencho interactions across Maros CRM | `done` | [done](requirements/REQ-003-adopt-bencho-interactions-across-maros-c/PLAN.md) |  |
| [REQ-004](requirements/REQ-004-transversal-maros-ux-and-motion-refineme/SPEC.md) | Transversal Maros UX and motion refinement | `in-progress` | [in-progress](requirements/REQ-004-transversal-maros-ux-and-motion-refineme/PLAN.md) |  |
| [REQ-005](requirements/REQ-005-friendlier-roles-and-permissions-ux-func/SPEC.md) | Friendlier roles and permissions (UX + functionality) and full-power admin MCP | `approved` | [launched](requirements/REQ-005-friendlier-roles-and-permissions-ux-func/PLAN.md) |  |

## Top pending (urgency, then complexity)

- P-010 · Apply `db/add-role-audit-events.sql` to Supabase by hand before the REQ-005 backend is dep · high/S
- P-012 · Apply `db/add-access-requests.sql` to Supabase by hand before deploying REQ-005 backend · high/S
- P-011 · Make role write + audit insert atomic (transaction or outbox) once the SQL is applied, so  · med/M

## Recent decisions

- D-001 — Role audit events are recorded best-effort after the role write

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W3](2026-10/W3/WEEK.md): [14](2026-10/W3/2026-10-14.md), [13](2026-10/W3/2026-10-13.md), [12](2026-10/W3/2026-10-12.md)
  - [W2](2026-10/W2/WEEK.md): [11](2026-10/W2/2026-10-11.md), [10](2026-10/W2/2026-10-10.md), [08](2026-10/W2/2026-10-08.md)
