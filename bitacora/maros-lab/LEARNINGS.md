# Learnings

## Confirmed

- **L-001 · tooling** In this lab repo, global Vitest setup changes must be checked against the whole suite, not only the feature folder: compare the failing set with the baseline snapshot (git archive of the baseline commit plus a node_modules symlink in /tmp) to prove no regression.
  - 2026-10-12T23:27:53.571969-05:00 · REQ-001/M1-audit: Full suite went 37 failed (9 files) at 3ea1a97 to 11 failed (5 files) after the matchMedia stub; all 11 are in the baseline failing set.

- **L-002 · pitfall** Date-only filter inputs are local calendar days: compare timestamps by their local day (as formatDate renders them) and force process.env.TZ in tests that touch that path.
  - 2026-10-12T23:27:53.706732-05:00 · REQ-001/M1-audit: createdAt 2026-10-02T03:30:00Z is Oct 1 22:30 in America/Bogota; the UTC-day implementation excluded it from a range ending Oct 1 and the TZ-forced test reproduced it.

- **L-003 · convention** filterParams serialize returns only the filter keys: any page that writes it to the URL must merge it into the existing query string.
  - 2026-10-12T23:27:53.830116-05:00 · REQ-001/M1-audit: serializeInvoiceScanFilters builds a fresh URLSearchParams from the filter object and ignores everything else in the query.

- **L-004 · pitfall** Native Next App Router query updates must call history.replaceState with null data; passing history.state can bypass hook synchronization because it contains __NA.
  - 2026-10-12T23:37:05.783752-05:00 · REQ-001/T4: Installed node_modules/next/dist/client/components/app-router.js:256-263 returns early for data.__NA or data._N before applyUrlFromHistoryPushReplace.

- **L-005 · pitfall** Invoice filter component tests need asymmetric section fixtures and mixed empty/populated states; mirrored fixtures can hide swapped counters and omitted empty sections.
  - 2026-10-13T00:09:32.379178-05:00 · REQ-001/T5: T5 antagonist D-20261012-235900-e244 identified mirrored fixtures with identical counters; added two asymmetric cases with anchored section counts and scoped identities, and the full feature suite passes 100 tests.

- **L-006 · pitfall** Installed Motion fixes layoutId in its projection node at mount, so shared filter chips/options must remount when their identity or selected state changes.
  - 2026-10-13T00:32:30.523359-05:00 · REQ-001/T6: Both T6 reviewers confirmed createProjectionNode setOptions at mount; a real Motion/jsdom probe kept projection.options.layoutId=invoice after props changed to transaction, while the replacement-node regression now covers the fix.

- **L-007 · pitfall** jsdom measures every box as zero, exactly like a display:none responsive variant, so a Motion exit that waits for a shared-layoutId layout animation never completes there: test list presence with real Motion, not only mocked props.
  - 2026-10-13T01:09:32.302349-05:00 · REQ-001/M3-audit: A record moved between 'To enter' and 'Entered' kept its leaving row mounted, inert and at opacity 0 after 1.5 s with zero rects, and was removed with stubbed distinct rects (M3 audit scratch tests).

- **L-008 · convention** In invoice-scans page tests import InvoiceScansPage.filters.test-support before any module that imports the API layer (hooks/useInvoiceScans), otherwise the real API module is cached unmocked and the page renders its error state.
  - 2026-10-13T01:09:32.423750-05:00 · REQ-001/M3-audit: Importing invoiceScanKeys from ../hooks/useInvoiceScans above the support module made every test fail with 'Unable to find an element with the text: 2 of 2' (M3 audit).

## Candidates

- **L-009 · pitfall** In the lab's Vitest page tests useSearchParams is mocked with useSyncExternalStore (synchronous), but real Next 16 delivers history.replaceState URL changes through a transition, so echo/lag races of URL-synced draft inputs cannot be reproduced in jsdom and belong in the real-browser pass.
  - 2026-10-13T01:46:04.013193-05:00 · REQ-001/M2-audit: Read node_modules/next/dist/client/components/app-router.js (applyUrlFromHistoryPushReplace dispatches ACTION_RESTORE inside startTransition) against InvoiceScansPage.filters.test-support.tsx (uSES-based mock); the harness cannot produce a stale intermediate query.

- **L-010 · convention** A mutation spot-check that survives the whole suite marks an unprotected line: removing setResetKey from clearFilters kept all 120 invoice-scans tests green until a test of a search draft that never reached the URL was added.
  - 2026-10-13T01:46:04.135624-05:00 · REQ-001/M2-audit: Nine mutations on M2 behaviours: eight were caught by 1-40 tests, the resetKey one by none; the new test fails only without it.

- **L-011 · tooling** In headless Bash calls, a backgrounded subshell started with ( ... ) & is killed when the outer call's shell exits and leaves a truncated log; put the commands in a script outside the repo and run it in the foreground or with run_in_background.
  - 2026-10-13T01:46:04.255465-05:00 · REQ-001/M2-audit: First verify run wrote only the typecheck banner and no exit lines; the script file run in the foreground produced the full log.

## Rejected

_None._
