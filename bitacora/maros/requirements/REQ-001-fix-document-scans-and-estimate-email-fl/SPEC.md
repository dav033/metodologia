---
id: REQ-001
status: in-progress
created: 2026-10-10
track: standard
---
# REQ-001 — Fix document scans and estimate email flow

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Maros users report repeated failures in financial workflows: supporting documents in Document Scans cannot be viewed or downloaded for QuickBooks, manual transactions sometimes do not save, and sending an existing estimate after converting a lead to a project can fail with a service error. These workflows already exist in both repos, so the goal is to find and correct the causes without rebuilding working capabilities.

**Success looks like:** a Document Scans record's support file can be opened/downloaded by an authorized recipient; a manual transaction submission reports success only when it is persisted and reports an actionable error otherwise; and sending an estimate from a converted project either completes with the intended attachment or returns a clear actionable error.

## Users / actors / stakeholders
- Internal Maros staff who enter transactions and attach support documents to QuickBooks.
- External CRM users, subject to their existing resource permissions.
- CRM owner/administrator who sends project estimates to customers.
- QuickBooks, object storage, and the mail provider as external dependencies.

## Scope (in)
### US-1 (P1, Must) — Open and download Document Scans support
As an authorized CRM user, I want to view and download the support file attached to a scan so that I can enter it in QuickBooks.
**Acceptance:**
- Given a scan with a stored file and sufficient permission, when I open or download its document, then the file is returned with the expected content and filename.
- Given a missing file, expired URL, or denied request, when I request it, then the UI reports a recoverable, actionable error rather than silently doing nothing.

### US-2 (P1, Must) — Persist manual transaction submissions
As a finance user, I want the Add Transaction action to save the entered transaction so that it appears in the review queue.
**Acceptance:**
- Given valid form data and an optional attachment, when I submit, then the API persists the record and the list reflects it.
- Given a validation or provider failure, when I submit, then the UI reports the failure and does not claim success.
- Given a transaction was saved but its optional file upload failed, when the user retries the attachment, then the record remains attachable and does not point to a missing object.
- The currently supported optional attachment and QuickBooks counterparties/categories remain available.

### US-3 (P1, Must) — Send a project estimate after lead conversion
As an authorized CRM user, I want to send the existing estimate for a converted project so that the customer receives the correct proposal.
**Acceptance:**
- Given a converted lead with an estimate, when I send the estimate email, then the selected file is attached and the CRM shows the actual delivery result.
- If the mail service or attachment retrieval fails, the UI shows an actionable error and does not report success.

### US-4 (P2, Should; deferred) — Find Document Scans by total
As a finance user, I want to search Document Scans by transaction total so that I can locate a support record quickly.
**Acceptance:**
- Search must match the transaction total consistently across pending and completed records.
- This enhancement is deferred until the three reported workflow failures are corrected; exact-match versus range behavior remains to be confirmed before implementation.

### US-5 (P1, Must) — Show review comments on the scan detail
As a reviewer, I want to see saved comments when I open a Document Scans record so that I can act on the reviewer's instructions without returning to the list.
**Acceptance:**
- Given a scan with a non-empty saved comment, when a reviewer opens its detail page, then the comment is visible before the review form and preserves line breaks.
- Given a scan with no comment or whitespace only, when a reviewer opens its detail page, then no empty comments panel is shown.

## Out of scope
- Creating or correcting individual CRM lead/project records mentioned in chat (including 065P-0726).
- Permit/license operational requests in the Maros group.
- Rebuilding existing scan, manual transaction, optional attachment editing, counterparties, or estimate-email features that the code already provides. Showing the existing saved comment on the scan detail is in scope under US-5.
- The historic AI-agent/plugin discussion and QuickBooks latency complaint; these need separate current evidence and scope.
- Changing user roles or weakening permissions. The owner confirmed the email recipient has access; preserve existing resource authorization and distinguish a real access failure from a file/URL failure.

## Requirements
- R1. The implementation shall preserve authentication and per-resource authorization for internal and external users.
- R2. Download and preview failures shall be observable in the UI and actionable; expired signed URLs may be refreshed through the existing API.
- R3. Manual transaction submission shall only show success after the API confirms persistence.
- R4. Estimate delivery shall accurately reflect the mail-provider result and preserve the selected estimate attachment.
- R5. Existing local edits in both repos shall be preserved; the current worktrees contain unrelated uncommitted financial-display/QBO-enrichment changes.
- R6. A scan shall only persist attachment metadata after the uploaded object is confirmed in storage; failed or interrupted uploads shall leave the record retryable.

## Edge cases & errors
- Missing/deleted object in storage; expired signed URL; unsupported file; API authorization denial.
- Double-click/retry during a slow save; network timeout where persistence outcome may be unknown.
- Estimate email without an attachment, replaced estimate, failed download, or mail-provider timeout.

## Constraints
- Frontend: `maros-next`; API: `maros-nest`; PostgreSQL/Supabase, QuickBooks, object storage, and SMTP integration.
- Do not read or expose `.env` values or secrets. No production data mutation, message sending, deployment, push, or commit.
- Plan approval is required before source-code changes. There are pre-existing local changes in both repos; implementation must work around them.

## Priorities & phases
- Phase 1 / P1: US-1, US-2, US-3 — reproduce from the UI/API, trace the failing boundary, and fix the cause.
- Phase 2 / P2: US-4 — define search semantics and implement after Phase 1.
- MoSCoW: US-1/2/3 Must; US-4 Should.

## Timeline & dependencies
- Estimate after approved scope and root-cause discovery. US-4 needs the owner's choice of exact amount versus range.
- No schema change is assumed. If discovery shows a schema or contract change is required, enumerate both-repo consumers and update the plan before that change.

## Assumptions
- “Documents Scann” refers to Document Scans / invoice-scans support-file preview/download in the CRM.
- The reported Add Transaction no-op concerns the existing manual transaction dialog and endpoint.
- The estimate issue concerns the existing post-conversion modal / project estimate email endpoint.
- The latest three failures are the immediate development scope. Search-by-total is a later enhancement because the chat does not define exact versus range behavior.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered by repeated chat reports and code-path review |
| Users / actors | Covered; internal and external users |
| Scope | Covered; three reported defects + deferred search enhancement |
| Out of scope | Covered |
| Flows & behavior | Covered at workflow level; SMTP failure still needs provider evidence |
| Edge cases | Covered |
| Acceptance criteria | Covered |
| Constraints | Covered |
| Priorities & phases | Approved by owner 2026-10-10 |
| Timeline | Estimate follows plan approval and root-cause discovery |

## Clarifications
- Source: current Firefox WhatsApp session, Maros Construction group and the contact labeled with a number beginning 707, reviewed 2026-10-10.
- Owner previously confirmed the relevant CRM users are internal and some external, the trusted subdomains are expected, and the scan notification recipient has access.
- Excerpts were paraphrased; no messages were sent.
