# Index — maros-lab

_Generated 2026-10-13 02:13 by `bitacora.py index`. Do not edit by hand._

**Central:** [Summary](SUMMARY.md) · [Architecture](ARCHITECTURE.md) · [Decisions](DECISIONS.md) · [Pending](PENDING.md) · [Tools](TOOLS.md)  
**Web:** [project](http://127.0.0.1:8765/p/maros-lab) · [graph](http://127.0.0.1:8765/p/maros-lab/graph)  
**Last activity:** 2026-10-13

## Workspace

- **frontend** → `/home/david/dev/maros-lab/maros-next`

## Needs attention

- REQ-001: executor finished — review & merge

## Requirements

| ID | Title | Spec | Plan | |
|---|---|---|---|---|
| [REQ-001](requirements/REQ-001-invoice-list-filters-and-shared-element/SPEC.md) | Invoice list: filters and shared-element motion | `in-progress` | [done](requirements/REQ-001-invoice-list-filters-and-shared-element/PLAN.md) | report ✓ |

## Top pending (urgency, then complexity)

- P-005 · REQ-001/R5: see the shared-element motion once in a real browser before merging · med/S
- P-003 · Free text matches one phrase per field, so a multi-word query that spans fields ("acme 104 · low/S
- P-007 · Row links change href on every filter edit, so Next re-prefetches every visible detail lin · low/S
- P-008 · A record created from the filtered list opens its detail without the list filters · low/S
- P-013 · Amount filters: `inputMode="decimal"` hides the minus key on phone keypads and unparsable  · low/S
- P-002 · 11 tests outside invoice-scans are red on the lab baseline · low/M
- P-006 · Chip removal opens the criterion selector, also with reduced motion and never for search/r · low/M

## Recent decisions

- D-005 — Detach record row/card contents from the row's presence
- D-004 — Carry validated invoice filters through fixed detail/list destinations
- D-003 — Measurable filter options and reversible shared chip motion
- D-002 — Replace browser query state for local invoice filters
- D-001 — Date filter: issue date, else creation date, as the local calendar day

## Timeline

- **2026-10** — [month summary](2026-10/MONTH.md)
  - [W3](2026-10/W3/WEEK.md): [13](2026-10/W3/2026-10-13.md), [12](2026-10/W3/2026-10-12.md)
