# Audit — REQ-001 milestone M2 (T4–T5)

Auditor: claude/sonnet-5-5, marathon session 10 · Branch `feat/req-001-invoice-list-filters-and-shared-element` · Audited `7222eb6` (T4) and `5b73e77` (T5) as they stand at HEAD, i.e. after M3 replaced the native selects with Popover options · Added `c1a524d`.

## Verdict: pass-with-fixes

T4 and T5 deliver R1, R3, R4, R6 and the M2 share of R7. Every verify command of the milestone is green at HEAD and
the tests catch the behaviours they claim to cover. One small ARIA defect and one unguarded behaviour were fixed here;
three low-urgency follow-ups went to PENDING.md. No blocker. As in M3, nobody has seen this UI in a browser (P-005):
the lab forbids starting the dev server.

## What I checked

- **R1 — filter in several ways.** Free text over title, file name, counterparty, invoice number, project number and
  comments (case/accent insensitive, one test per field); record type (2 options); money direction (in/out); status
  (all four: awaiting scan, scanning, ready to enter, scan failed); category (all five); date range (issue date first,
  creation day as fallback, D-001); inclusive amount range including `0` and a negative bound. AND combination of six
  criteria plus removal of one chip. Both sections are filtered from the same `filtered` list; section counters and the
  `N of M` count use the filtered buckets (`InvoiceScansPage.tsx`).
- **R3 — state in the URL.** Reads through `useSearchParams` (validated by `parseInvoiceScanFilters`), writes with
  native `history.replaceState`, merging only the nine owned keys and keeping unrelated keys and the hash
  (`applyInvoiceScanFilters`). I checked the premise of D-002 in the installed Next (16.1.3,
  `app-router.js`): the patched `replaceState` accepts a `null` state, copies Next's internal history state and calls
  `applyUrlFromHistoryPushReplace`, so `useSearchParams` follows. The route is `force-dynamic`, so no Suspense
  boundary is needed. Tests: remount restore of all nine criteria, malformed values ignored and dropped on the next
  edit, Back/Forward `popstate`, consecutive edits while the hook has not seen the URL yet.
- **R4 — filter bar.** Search box, one labelled control per criterion, removable chips, "Clear filters" (disabled with
  no chips), live count, and a per-section "No documents match these filters" with its own clear action. Mixed
  states (one section empty, the other populated, both directions) keep independent counters. Load errors say
  "Results unavailable" and never claim a valid empty match, also with a cached list (T6 regression).
- **R6 — accessibility.** Every control has a visible `Label`; the count is `aria-live="polite"`; chips are buttons
  named "Remove filter …"; reversed date/amount ranges expose `aria-invalid`, `aria-describedby` and `role="alert"`;
  the full tab order and Enter/Space activation of chips and clear are asserted.
- **Scope and hygiene.** The branch touches only `src/features/invoice-scans/**` and `vitest.setup.ts`; no
  `console`/`debugger`/`.only`/`.skip`/TODO/`any`/`@ts-*`/eslint-disable in the diff, no secrets, no env files, no new
  dependency, `git diff --check` clean, nothing pushed. `InvoiceScansPage.test.tsx` changed by one line (the
  `useSearchParams` mock the page now needs); no assertion was weakened.
- **Docs.** ARCHITECTURE "Laboratory implementation" (draft inputs, blur normalisation, clearable empty states,
  unavailable results), D-001 and D-002 match the code. D-002's "return link needs query propagation later" is closed
  by D-004.
- **Tests would fail without the change.** Mutations on the working tree (restored after each), run against
  the M2 test files and the domain suite:

  | Mutation | Result |
  |---|---|
  | completed section not filtered | 34 fail |
  | unrelated query keys dropped by `applyInvoiceScanFilters` | 12 fail |
  | `classification` missing from the owned keys | 5 fail |
  | `aria-live` removed from the count | 30 fail |
  | chip accessible name changed | 30 fail |
  | amount-range error removed | 1 fail (the reversed-range test) |
  | filtered empty state removed from the completed section | 5 fail |
  | total shows the filtered count | 40 fail |
  | `resetKey` removed from `clearFilters` | **0 fail → gap, closed below** |

## Findings fixed (`c1a524d`)

1. **`aria-label` on a role-less `div`** (`InvoiceScanFilters.tsx`, chips container). ARIA 1.2 forbids naming a
   `generic` element, so "Active filters" was not exposed to assistive technology (axe: prohibited attribute). It is
   now `role="group"`. New test "names the active chips as a group that is absent without filters" fails without it.
2. **`resetKey` was unprotected.** "Clear filters" bumps `resetKey` to remount the draft inputs, but every existing
   test passed with that line deleted: the effect in `InvoiceScanDraftInput` already covers drafts that exist in the URL
   and the blur handler covers amounts. The one case only the remount handles is a search draft that never reached the
   URL (spaces only) while another filter keeps "Clear filters" enabled. New test "empties a search draft that never
   reached the URL when the filters are cleared" fails without `setResetKey`.

The antagonist reviewed the staged diff once: SOUND, no findings (checked `group` vs `list`/`toolbar`, Motion layout
props untouched, determinism of the new tests, and reproduced both mutations on a temp copy).

## Findings deferred (PENDING.md)

- **P-012 · low · M.** `InvoiceScanDraftInput` resets its draft when the `value` prop differs from its last write, so a
  lagging URL echo of an older keystroke would be read as an external change. Real Next delivers `replaceState`
  through a transition; the lab harness uses `useSyncExternalStore` (synchronous) and cannot show it. Possible visible
  effect: the box briefly shows older text and a character typed in that window is lost. Fix options: debounce the
  search URL write (also helps P-007) or ignore echoes of values already written. Needs the P-005 browser pass.
- **P-013 · low · S.** Amount fields use `inputMode="decimal"` (no minus key on iOS/Android numeric pads although
  negative totals are valid), and text that does not parse (`1,000`, `10,5`) is dropped silently on blur with no error.
- **P-014 · low · M.** The panel is always fully expanded (eight controls plus help text above the lists). R4 asked for
  "compact controls"; on a phone the first record starts far below the fold. Owner/design call: a "Filters" disclosure
  that keeps search, count and chips visible.

## Notes for the next session

- P-004 (the blocked M2-audit item) is closed by this audit.
- The M2 evidence in the PLAN (65 and 100 tests) is from the commits themselves; I verified HEAD, where the same
  behavioural assertions run against the Popover controls and pass (15 files / 122 tests).
- Whole-suite failures are the 11 baseline ones (P-002); none is in a file M2 or the audit touched.

## What I ran

All with the plan's clean environment (`env -i … NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:9/api …`):

| Command | Result |
|---|---|
| T4 verify: file test, `npm run typecheck`, `npx eslint src/features/invoice-scans` | exit 0 |
| T5 verify: `npx vitest run src/features/invoice-scans`, `npm run typecheck` | exit 0; 15 files / 120 tests at HEAD before my commit |
| Same chain after `c1a524d` | exit 0; typecheck 0, ESLint 0, 15 files / 122 tests |
| Nine mutation spot-checks on M2 behaviours | table above; tree restored (`git status` clean) |
| Two new tests against `role` removed and `setResetKey` removed | each fails only its own test |
| `npx vitest run` (whole suite) after `c1a524d` | 11 failed in the 5 baseline files, 437 passed (448 tests); no new failure |
| Installed Next `app-router.js` read for the `replaceState` patch | null state and URL handled |
| Antagonist, one pass on the staged diff | SOUND, 0 findings |
