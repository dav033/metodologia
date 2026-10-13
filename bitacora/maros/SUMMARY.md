# maros — Summary

## Purpose
Maros is the CRM for Maros Construction. Users are internal staff and some external users. The web app supports construction project, customer, task, and meeting management; exact user roles and business journeys are not yet confirmed.
Last confirmed with owner: 2026-10-10.

## Current state
The product is implemented across two repositories: `maros-next` (web CRM) and `maros-nest` (API). On 2026-10-10, both repositories' approved feature commits were pushed to `main` and deployed to production: frontend `6704d72`, API `003ed7a`. Later that day, frontend commit `b8efd6a` added the review-comments panel to Document Scans and reached Netlify `ready`; `/login` returned HTTP 200. REQ-003 was approved on 2026-10-11; the frontend branch `feat/req-003-bencho-interactions` now contains a 59-route interaction inventory, a shared authenticated task/note/navigation palette, a reduced-motion-aware Motion Primitives task-view animation, and an adapted Bencho Checklist subtask toggle. REQ-003 is complete locally; the changes remain uncommitted and undeployed. REQ-002 is deployed as a read-only converted-leads view. REQ-001 remains in progress while the live estimate-email provider cause (P-004), manual-transaction report (P-005), project payment visibility (P-007), and invoice category/vendor association (P-008) await evidence; amount-search semantics are still deferred. The first cross-repository architecture scan is documented as partial; `infra/` was excluded at the owner's direction.

## Active focus
- REQ-004 is in progress locally: implement and verify the cross-route UX/motion refinements in `maros-next`; keep changes uncommitted and undeployed.
- REQ-003 remains complete locally; preserve its changes while finishing REQ-004.
- Keep Bitácora as the Maros project memory and `metodologia` as the main development skill.
- Continue the remaining items in PENDING.md; clarify exact user roles and key journeys when a future change depends on them.

## Top pending (see PENDING.md)
- P-004 · Diagnose the live estimate-email provider error.
- P-009 · Review production dependency advisories found during UI dependency verification.
- P-002 · Show project-list load failures as errors instead of an empty list.
- P-005 · Reproduce the manual transaction save report.
- P-007 · Verify project payment information visibility.
- P-008 · Verify invoice category/vendor association.

## Recent decisions (see DECISIONS.md)
- D-002 · Keep converted leads in a separate read-only view.
- D-001 · Include `maros-next` and `maros-nest`; exclude `infra/` from the scan.

## Known issues
- Project-list API failures currently appear as an empty list; see P-002.
- Converted lead 065P-0726 is now available in the separate Converted view; no CRM write was needed.
- The contact's reports about project payment visibility and invoice category/vendor association still need current-version reproduction (P-007/P-008).
- Owner confirms email invoice recipients have access and the allowed Maros subdomains are trusted (P-001 and P-003 closed).

_Last updated: 2026-10-11_
