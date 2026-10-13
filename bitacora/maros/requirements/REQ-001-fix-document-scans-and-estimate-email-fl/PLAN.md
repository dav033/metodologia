---
id: REQ-001
status: in-progress
created: 2026-10-10
---
# Plan — REQ-001

## Goal
Fix the three currently reported workflow failures in Document Scans and estimate email. Preserve existing user changes and contracts unless root-cause discovery proves a contract change is needed.

## Tasks
- [ ] T1 — Prevent Firefox from blocking invoice-scan downloads by opening the target tab synchronously before requesting a fresh signed URL; close the temporary tab and report a recoverable error if URL generation fails. Renew active detail-page signed URLs before expiry. Repo: maros-next. Code changed; automated verification not run.
- [ ] T2 — Make attachment persistence happen only after the direct-to-S3 upload succeeds. The API currently stores `fileKey` before the browser PUT, so a failed upload poisons the record and blocks retry. Update the frontend consumer and MCP tool flow to prepare → upload → finalize; verify the finalization checks the object and is retry-safe. Consumers found: `maros-next/src/features/invoice-scans/infra/invoiceScansApi.ts`, `maros-nest/src/modules/quickbooks/invoice-scans.controller.ts`, `maros-nest/src/modules/mcp/tools/invoice-scans.ts`; current service unit coverage also calls the old `attachFile`. Implementation changed in all three consumers; final verification remains pending. Repos: maros-next, maros-nest.
- [ ] T3 — Resolve estimate files named “Proposal” as estimates and distinguish file lookup failure from a genuinely missing file; keep the send button recoverable after thrown errors. Diagnose and correct the reported mail-service failure when provider/API evidence is available. Repos: maros-next, maros-nest.
- [ ] T4 — Owner review of Phase 2 search-by-total semantics (exact amount or range); if approved, extend the API list contract and UI search consistently across pending and completed records. Repos: maros-next, maros-nest.
- [ ] T5 — Review changed-file diff against REQ-001, preserve unrelated local modifications, and record completion/remaining issues in Bitácora.
- [x] T6 — Display saved reviewer comments on the invoice-scan detail page and add regression coverage for populated and blank comments. Repo: maros-next.

## Ordering and dependencies
T1–T3 are independent investigations and fixes; start with T1 because the group reports the support-file problem repeatedly. T4 is deferred pending clarification and Phase 1 completion. T5 follows the implementation tasks.

## Verification
No test or verification commands are authorized yet. After plan approval, implementation will follow the approved scope; verification commands will be proposed separately if needed.

## Risks
- Reproduction may depend on authenticated CRM/QuickBooks/storage/mail state not present in local development.
- A timed-out external call may have completed; transaction and email retries must not create duplicate effects.
- Existing unrelated local diffs in both repositories must remain untouched.

## Progress log
- 2026-10-10 — Owner approved the plan in chat. T1 code updated for popup blockers and 15-minute preview URL expiry. T2's no-attachment and visible validation paths were already present in HEAD; no reproduction evidence for the current save report. T3 file discovery/error handling updated; the reported SMTP/API “service does not respond” failure cannot be attributed from code alone and needs a request timestamp/correlation or server mail error. No tests or automated verification run per instruction.
- 2026-10-10 — Further chat/code correlation found the document upload race: `/attachment` persists the S3 key before the client PUT succeeds, causing failed uploads to be treated as attached and preventing retry. Updated T2 plan to a two-phase prepare/upload/finalize contract; consumers in frontend, REST controller, and MCP are identified. No schema migration is needed.
- 2026-10-10 — Implemented T2's two-phase attachment flow. REST and MCP prepare a scoped S3 key/URL without changing the scan; frontend/MCP upload first, then finalize; API checks key ownership, object size and MIME type, and uses a conditional update for concurrent/retried requests. The old internal `attachFile` remains deprecated for existing unit callers, but no REST/MCP consumer uses it. T1 download popup and URL refresh updates are present. T3 recognizes “Proposal” and displays estimate lookup/send errors; the provider failure still needs timestamp/correlation or a server/mail error. Manual transaction no-op remains unconfirmed against the current version. No tests, lint, build, or production email were run.
- 2026-10-10 13:36 plan APPROVED (terminal)
- 2026-10-10 — Final frontend suite after adding the manual-create failure case: 69 files / 364 tests passed; typecheck and focused lint/tests passed again. `git diff --check` passed in both repositories. No commit or push.
- 2026-10-10 — Owner requested hardening and tests. Removed the unsafe legacy `attachFile` service method. Regression coverage now includes prepare/upload/finalize, failed browser PUT, missing/mismatched S3 object, key ownership, idempotent/concurrent finalize, MCP contract, Proposal discovery/attachment, provider-failure propagation/UI retry, and manual-transaction API errors.
- 2026-10-10 — Frontend `npm run verify` passed: lint (0 errors, 183 warnings), typecheck, 69 test files / 363 tests, and build. Backend tests passed (84 suites / 1,031 tests) and build passed. Backend full lint reports five pre-existing errors: `projects.service.ts:323-327` (unnecessary assertions), `quickbooks-auth.service.spec.ts:218` (unbound method), and unchanged `invoice-scans.service.ts:685` (unnecessary escape); scoped lint for MCP, controller, DTO, and specs passed. No live email or production mutation.

- 2026-10-10 — Owner requested end-to-end verification. Re-ran frontend tests (69 files / 364 tests), backend tests (84 suites / 1,031 tests), frontend typecheck, backend build, and `git diff --check`; all passed. The API `test:e2e` script only enumerates the existing `src/**/*.spec.ts` Jest suite, and the frontend has Vitest/jsdom without Playwright/Cypress. No API/web server is running. The API `.env` targets an external database, so it was not used; no real email, storage, or CRM write was made. True UI→API→provider E2E remains unverified until an isolated test environment exists.
- 2026-10-10 — Read-only review of the 707 WhatsApp chat found the corrected one-off record request: create lead `065P-0726` (first message said `064P-0726`, then corrected). This is CRM data entry, not automatic number assignment; asked owner to clarify whether to add it as a separate task. Existing REQ-001 excludes this record.
- 2026-10-10 — Follow-up review of the latest 707 message found that reviewers need comments visible after opening a Document Scans record. Added US-5 to the spec; the detail page now displays non-empty comments above the review form, preserving line breaks. Focused test (2 cases), frontend typecheck, scoped ESLint, and `git diff --check` passed. No deployment or WhatsApp message sent yet.
- 2026-10-10 — Published US-5 as frontend commit `b8efd6aa01f53257d25a4cdd198e94f97a2f6052`. Netlify deploy `6acad4e7e0c1ac0008f035eb` reached `ready`; production `/login` returned HTTP 200. Sent the 707 contact an update on US-5 and earlier work, including the unresolved provider diagnostics, amount-search semantics, manual-save reproduction, and two older reports now tracked as P-007/P-008. The first note picked up a pre-existing draft fragment; I sent an apology. A later note about P-007/P-008 appeared garbled and then showed as deleted in the chat; sent and verified a concise correction. Firefox remained in the background.
