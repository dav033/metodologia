---
req: REQ-002
status: done
created: 2026-10-10
---
# Plan — REQ-002 — Expose project-linked leads in the CRM

## Approach
Add a separate, read-only converted-leads view for the selected lead type. Add a backward-compatible API read for leads that already have a project, preserving existing authentication and lead-type scope. Keep the current pipeline query unchanged; converted rows link to their existing project.

## Global constraints
- Do not create duplicate lead/project records or call the destructive project-to-lead revert action.
- Preserve the current pipeline behavior and unrelated worktree changes in both repositories.
- Require existing `leads:read` permission and apply the current per-user lead-type scope.
- No schema migration, production data mutation, deployment, push, or commit.

## Tasks
- [x] T1 — Add a typed API read for leads with an associated project; preserve lead-type and request scope. Add repository/service/controller regression coverage. · repo: backend · verify: `npm test -- --runInBand modules/leads/lead-management/repositories/leads.repository.scope.spec.ts modules/leads/lead-management/leads.controller.spec.ts` · covers: R1, R2
- [x] T2 — Add a separate converted-leads view in the frontend. Reuse the selected lead type and search; make rows read-only and link to their existing project. Add UI/adapter tests. · repo: frontend · after: T1 · verify: `npm test -- --run src/features/leads/presentation` · covers: R3, R4, R5
- [x] T3 — Review both repository diffs, run applicable typecheck/build/tests, update pending/summary/day log, and mark REQ-002 complete if all checks pass. · repo: backend · after: T1, T2 · verify: `npm run build` · covers: R1, R2, R3, R4, R5

## Verification
- Backend targeted tests prove the converted query returns only project-linked leads for the requested type and respects request lead-type scope; controller test proves the route remains behind `leads:read`.
- Frontend tests prove the new view can search and open the linked project, exposes no mutating actions, and leaves the existing pipeline mode unchanged.
- Run frontend typecheck, relevant test files, and build; run backend targeted tests and build. Review `git diff --check` and ensure unrelated existing edits remain intact.
- Live CRM data remains unchanged; confirm behavior only through tests/local code, not a production write.

## Rulings
- Use a separate converted-leads view instead of adding converted records to the active pipeline — source code explicitly excludes project-linked leads from that pipeline; a separate view preserves that intent and avoids changing existing row actions — cost if wrong: med.
- Render converted leads as read-only and link to the project — this request is about discoverability, and changing a converted lead's status could leave its active project inconsistent — cost if wrong: low.
- No new database relation or duplicate lead is needed — the CRM project already points to the original lead record — cost if wrong: high; verified by the project relation and detail screen.

## Progress log
- 2026-10-10 — Owner approved designing and implementing a non-destructive resolution. CRM verification found the Lead already exists and `findByLeadType` hides project-linked leads. Chose a separate read-only converted-leads view as the recommended assumption after offering the owner the presentation choice and allowing 30 seconds for a reply. No source code or CRM data changed yet.
- 2026-10-10 — T1 complete: added the scoped converted-lead query, service method, and `GET /leads/converted?type=...`; kept existing lead pipeline reads unchanged.
- 2026-10-10 — T2 complete: added the Converted view with retryable load errors, a converted-specific empty state, read-only rows, and project navigation; added frontend contract/UI tests.
- 2026-10-10 — T3 complete: backend tests (25 passed), backend build passed, frontend tests (4 passed), frontend typecheck and build passed, and `git diff --check` passed. Backend full lint remains red from five errors in pre-existing changes outside this requirement; targeted lint on changed backend files had no errors (two pre-existing warnings). No CRM data was modified or deployed.
