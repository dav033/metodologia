---
id: REQ-002
status: done
created: 2026-10-10
track: standard
---
# REQ-002 — Expose project-linked leads in the CRM

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The CRM associates project 065P-0726 with an existing Lead record, but the Leads page does not show it. The typed leads endpoint intentionally excludes every lead that already has a project, so users cannot find converted records in the Leads workflow. The goal is to make converted leads discoverable without duplicating records or deleting their projects.

**Success looks like:** an authorized Plumbing user can find 065P-0726 in a converted-leads view and open its existing project; the active lead pipeline keeps its current behavior and no CRM data is duplicated or removed.

## Users / actors / stakeholders
- Internal and external CRM users with `leads:read` permission and visibility to Plumbing leads.
- CRM administrators responsible for project and lead records.

## Scope (in)
### US-1 (P1, Must) — Find leads already converted to projects
As an authorized CRM user, I want a separate converted-leads view so that I can find the lead record behind an existing project.
**Acceptance:**
- Given a user with `leads:read` access to Plumbing, when they open the converted-leads view for Plumbing, then project-linked Plumbing leads are returned and unconverted leads are excluded.
- Given the user searches for `065P-0726`, when the converted-leads view is active, then the existing lead and its project are findable without creating another record.
- Given a converted lead is selected, when the user opens it from this view, then the existing associated project opens; no create, delete, status-change, or conversion mutation is offered from the read-only view.
- Given the current Leads pipeline is opened, then its current behavior and results remain unchanged.
- Given a user lacks access to the lead type, then the converted-leads response respects the same lead-number scope as existing lead reads.

## Out of scope
- Creating a duplicate lead or changing CRM records for 065P-0726.
- Reverting a project to a lead; that operation deletes the project.
- Changing the active pipeline's inclusion rules or conversion/status semantics.
- Adding new project or lead fields, database migrations, deployment, or production data repair.

## Requirements
- R1. When a user requests converted leads by type, the API shall return only leads with an associated project and matching that type.
- R2. The converted-leads API shall enforce existing authentication, `leads:read` authorization, and per-user lead-type scope.
- R3. When a user opens a converted lead from the converted-leads view, the UI shall navigate to its associated project and expose no lead/project mutation from that view.
- R4. The default Leads pipeline shall keep excluding project-linked leads unless the user explicitly opens the converted-leads view.
- R5. The UI shall display an actionable error if converted leads fail to load; it shall not present a failed request as an empty successful result.

## Edge cases & errors
- No converted leads for the selected type: show an empty state.
- Converted lead lacks a project relation: exclude it from the converted endpoint and view.
- Lead number belongs to a different type or falls outside the user's scope: do not expose it.
- Project relation or API read fails: show a recoverable error and preserve the active pipeline.
- Lead points to a deleted project: omit it from the converted view; do not recreate data automatically.

## Constraints
- Implement in `maros-nest` and `maros-next` with no schema change.
- Preserve existing local worktree changes in both repositories.
- Do not mutate live CRM data, send messages, deploy, push, or commit.
- Keep the existing endpoint behavior backward-compatible; converted reads use a separate API contract.

## Priorities & phases
- Phase 1 / P1: add a scoped, read-only API query for converted leads and a separate frontend view that links to projects.
- MoSCoW: US-1 Must.

## Timeline & dependencies
- One short cross-repository implementation phase; frontend consumption depends on the API contract.
- No migration or external provider is required.

## Assumptions
- A separate converted-leads view is the preferred presentation, preserving the current active pipeline. The owner was offered this choice versus including converted leads in the main list; no response arrived within 30 seconds, so this recommended option is used and can be adjusted if the owner responds.
- The existing project/lead association is the source of truth; the fix is discoverability, not data restoration.
- The converted view is read-only and opens the associated project because editing the converted lead from a pipeline could change its status while the project remains active.

## Implementation result
- Added `GET /leads/converted?type=...` with required type validation, `leads:read`, project relation filtering, lead-type filtering, and request-scope filtering.
- Added a Converted mode inside the existing Leads page. It loads through a separate query key, reports retryable errors, shows an explicit empty state, disables mutation controls, and navigates rows to their linked project.
- Regression coverage verifies query filters, permission metadata, route validation, DTO/project mapping, project navigation, read-only behavior, and retry action.
- Verification: backend targeted tests (25 passed), backend build passed; frontend targeted tests (4 passed), typecheck and production build passed. Full backend lint still reports five errors in pre-existing edits in `projects.service.ts`, `quickbooks-auth.service.spec.ts`, and `invoice-scans.service.ts`; no errors in the changed lead files.
- No live CRM data, deployment, commit, or push was changed.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered by CRM verification and source query behavior |
| Users / actors | Covered by owner-confirmed internal and external CRM users |
| Scope | Covered; separate converted-leads view |
| Out of scope | Covered |
| Flows & behavior | Covered at API and UI level |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| Priorities & phases | Covered; P1 |
| Timeline | Covered; one cross-repository phase |

## Clarifications
- Q: Create a missing lead or expose the existing project-linked lead? → A: Source inspection found the project already references the lead; do not create a duplicate or revert the project.
- Q: How should converted leads appear? → A: No response within 30 seconds; proceed with the recommended separate, read-only converted-leads view. Revise if the owner steers the choice during implementation.
