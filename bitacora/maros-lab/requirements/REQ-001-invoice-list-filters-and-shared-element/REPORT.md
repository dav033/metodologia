# REQ-001 — Invoice list filters and shared-element motion

Final session 12 · 2026-10-13 · Ready for owner review.
Frontend: `/home/david/dev/maros-lab/maros-next`.
Branch: `feat/req-001-invoice-list-filters-and-shared-element`.
Reviewed range: `3ea1a97..d9b92ff` (23 files, 2128 insertions / 29 deletions); frontend tree clean.
PLAN status: done. SPEC status: in-progress until owner review/merge. Nothing merged, pushed, deployed or published.

## Built

- AND-combined client-side filters for search, record type, money direction, status, category, invoice date range and amount range. Pure domain and query adapters validate malformed URL values and have deterministic tests.
- URL-driven controls, removable active chips, clear actions, announced live totals and filtered counts/empty states in both sections. The nine query keys preserve unrelated parameters; list edits replace the current history entry.
- Desktop rows/mobile cards animate entry, exit and layout; measurable Popover options share projection IDs with their chips. Existing list/detail title IDs and filtered returns are preserved, including detail error/delete return paths. New animation props are omitted under reduced motion.
- Baseline invoice-page matchMedia failures corrected without weakening assertions. All T1–T7 and M1/M2/M3 audits are complete.
- Final correctness fixes committed in `d9b92ff`: unique checkbox DOM IDs per responsive/exiting instance (P-009), and title-only projection remount when a departing record recovers presence (P-011). Three real-Motion regressions cover overlapping labels and reversal in both directions; surviving title nodes and exact layout IDs remain stable.
- No backend/API contract, dependency, environment, server or production change. Query consumers and list/detail/error/delete destinations were reviewed; existing direct-detail paths remain compatible.

## Verification evidence

The runner executed the exact chained **Verification** in [PLAN.md](PLAN.md), from the frontend repo, using `env -i` and the approved loopback API/webhook addresses. It read the complete output. Tests use mocked data; no real API was called.

| Check | Actual result |
| --- | --- |
| `npx vitest run src/features/invoice-scans` | Exit 0; 15 files, 125 tests passed |
| `npm run typecheck` | Exit 0 |
| `npm run lint` | Exit 0; 0 errors, 164 existing warnings in 74 files; 0 invoice-scans warnings |
| Exact three-command chain | Exit 0 in 48.599 seconds |
| `git diff --check` and full committed feature diff check | Exit 0 |
| Closing `bitacora.py --project maros-lab trace` | Exit 0; lint clean; all 7 requirements and 7 tasks recognized, no uncovered/unknown-ref/dangling diagnostics |
| Whole-branch fresh spec + standards reviewers | Both APPROVE after correctness fixes; static reviews |
| Staged final correction antagonist | SOUND; 0 fixed, 0 deferred, 0 dropped |

Full passing output: [post-fix verification log](../../artifacts/REQ-001-final-session12-postfix-verification.log).
Initial red evidence: [first verification log](../../artifacts/REQ-001-final-session12-verification.log): 122 passed / 3 failed, exit 1; typecheck/lint were not reached. Those inherited regressions were fixed, not skipped or weakened.
Closing trace: [trace log](../../artifacts/REQ-001-final-session12-closing-trace.log).
Review details: [REVIEW-FINAL.md](REVIEW-FINAL.md).

Lint warnings are existing debt: 103 explicit-any, 31 unused-vars, 28 unused-imports and 2 unnecessary directives. CounterpartySelect emitted 43 React warnings (42 updates outside act, 1 unawaited act); none was suppressed.

Build, full-project tests and live-browser checks **were not executed**: the approved laboratory constraints allow only the plan checks and forbid starting servers. P-002 records 11 unrelated failures reproduced by earlier audits on the baseline; this report does not claim that suite is green. jsdom proves contracts and real Motion presence, not pixel movement.

## Rulings

- Final reviews correctly treated P-009/P-011 as correctness defects despite their earlier low-priority deferral. Fix those; retain design and unmeasured performance proposals in PENDING.
- Checkbox identity belongs to the DOM instance. Shared title identity remains the exact record/viewport layout ID; only a revived title projection remounts, because zero-size boxes cannot clear stale visibility through a layout delta. D-005's exit handling is retained.
- The reversal fixture uses an active search filter to keep both sections mounted under R5. The unfiltered empty-completed-section teardown predates this feature and remains unchanged. Visibility, interaction and both reversal assertions remain intact.
- Workflow/ultracode is not callable in this harness; native bounded reviewer/runner agents completed the work. Initial spec/antagonist capacity errors each needed one successful retry. All started agents and jobs finished.
- Headless decisions followed the explicit no-questions/no-Aye instruction. Local fixes were committed as authorized; no push, merge, deploy or publication.
- Date/source, history replacement, option/chip target and fixed return-route choices remain D-001–D-005. Their business assumptions are for the owner's review, not silently changed at closure.

## Needs your eyes

- **P-005, before merge:** see actual desktop/mobile row exits/reorders, option → chip → option, title → detail → filtered return and reduced-motion switching. No lab session has verified a moving pixel. Include fast typing with a larger list and delayed Next URL propagation (P-012).
- Review date/money/search assumptions in `src/features/invoice-scans/domain/filters.ts` and URL handling in `domain/filterParams.ts`: issue date first, otherwise local creation day; finite numeric totals; phrase matching per field.
- Review fixed return links in `presentation/hooks/useInvoiceScanNavigation.ts` and Motion presence/identity in `presentation/components/InvoiceScanListMotion.tsx`. No new auth, payment execution, migration or security-sensitive backend code was introduced.

## Proposals

These are deferred owner choices, not additional implementation in this session.

1. P-006: decide chip-removal focus and selector behavior, including reduced motion and non-option chips.
2. P-007/P-012: measure Next prefetch and delayed URL typing before choosing debounce, echo handling or link-prefetch changes.
3. P-008: decide whether a newly created/uploaded record should inherit list filters on its return.
4. P-013: decide phone negative-number entry and feedback for unparsable amount drafts.
5. P-014: consider a compact mobile filter disclosure; retain search/count/chips visibly.
6. P-003: consider multi-word search across fields if the current phrase-per-field rule is insufficient.

## Pending

Closed: P-009 and P-011 with final regressions; P-004/P-010 were already closed by earlier audit/metadata work.
Open: P-005 browser evidence; P-003/P-006/P-007/P-008/P-012/P-013/P-014 proposals above; P-002 unrelated baseline tests. No new unreviewed implementation or background job remains.
Owner review and merge remain. The plan is done; the spec intentionally awaits that review. Current state is in [SUMMARY](../../SUMMARY.md), backlog in [PENDING](../../PENDING.md), and this session's evidence/walkthrough in [the day log](../../2026-10/W3/2026-10-13.md).

## Walkthrough

1. `/finance/invoices` renders InvoiceScansPage and loads the existing list through its query hook.
2. `useInvoiceScanFilters` reads validated URL criteria; the pure filter function narrows the list before pending/entered partitioning.
3. Controls write only the nine owned keys through replaceState; other query state/hash survives, and Back does not traverse every keystroke.
4. The filter bar supplies labeled criteria, chips, live totals and clear actions; reversed ranges expose associated feedback.
5. Popover option/chip pairs use scoped shared IDs. Motion tokens drive rows/cards; outgoing records are inert and aria-hidden until removal.
6. D-005 detaches nested title exit registrations so hidden responsive copies cannot retain a ghost row. Checkbox useId isolates overlapping instances; recovered titles remount only their projection.
7. Navigation carries validated query state into fixed detail/list destinations. Both responsive title IDs stay unchanged for shared transitions and tested returns.
8. Domain tests cover invalid/missing values; page and real-Motion tests cover filters, clearing, URL round trips, presence and reduced motion. Actual layout/motion and delayed Next rendering remain the browser review boundary.
