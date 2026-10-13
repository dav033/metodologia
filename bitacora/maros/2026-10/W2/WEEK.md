---
status: draft
---
# maros — Week 2026-10 W2 (2026-10-05 → 2026-10-11)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Maros project guidance now points to Bitácora and metodologia as the project memory and primary development skill.
- Both CRM repositories were fast-forwarded; the cross-repository scan was started and recorded as partial.

## Done
- `maros-next` advanced to `f133834`; `maros-nest` advanced to `66b1357`; local financial changes were preserved.
- Confirmed CRM purpose and scan boundary; registered both repositories in Bitácora and documented the project-level architecture.
- Independent review examined the CORS/session-cookie configuration; owner confirmed those subdomains are trusted. P-001 recipient access and P-003 trust boundary were closed by owner confirmation.
- Proposed the P-002 fix: show request failure separately from an empty project list and provide retry.

## Decisions
- Include only `maros-next` and `maros-nest` in the scan; exclude `infra/`.

## Not done / dropped
- Lint, type checks, tests, and builds were not run. Exact user roles/journeys, quality priorities, production data operations, and rollback remain unknown.

## Carried over to next week
- P-002 remains open for a future implementation request; product and operations unknowns can be clarified when a change depends on them.
