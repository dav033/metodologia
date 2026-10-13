---
status: in-progress
---
# REQ-001 — Invoice list: filters and shared-element motion

Implementation and automated closure are complete on the local feature branch at `d9b92ff` (FINAL/session 12).
Pending owner review/merge and P-005's browser motion pass; PLAN is done. See REPORT.md for evidence and limitations.

Requested by the owner on 2026-10-12 as the real-codebase proof of the automatic milestone flow: "que la cuestión de
las facturas se pueda filtrar de varias maneras y en la misma vista aplicar shared elements con animaciones".
The owner was away: there was no interview. Every decision below marked **Assumption** was taken from the code and
is his to overturn when he reviews the result.

## Context (explored in the code)

- View: `/finance/invoices` → `src/features/invoice-scans/presentation/pages/InvoiceScansPage.tsx`. It loads every
  record once (`useInvoiceScansList`), splits it with `partitionInvoiceScans` into "To enter" and "Entered in
  QuickBooks", and renders each with `InvoiceScansTable` (table on desktop, cards on mobile).
- A record (`domain/models.ts` `InvoiceScan`) is an invoice file or a manual transaction: status, money direction
  (`moneyFlow` in `domain/labels.ts`), classification/category, counterparty, project number, total, dates.
- Shared-element infrastructure already exists in the work in progress: `SharedEntityName` (layoutId shared between the
  row title and the detail page), `usePrefersReducedMotion`, `src/shared/presentation/motionTransitions.ts`, library
  `motion` (`motion/react`). The row title already uses `layoutId="maros-invoice-title-<id>-desktop"`.
- Baseline defect found before starting: 15 tests of `InvoiceScansPage.test.tsx` / `InvoiceScanDetailPage.test.tsx`
  fail with `window.matchMedia is not a function` (the motion hooks run under jsdom without a matchMedia stub).

## Requirements

- **R1 — Filter in several ways.** The list can be narrowed by: free text (document title, counterparty, invoice
  number, project number, comments); record type (invoice file / manual transaction); money direction (in / out);
  status (awaiting scan, scanning, ready to enter, scan failed); category (classification); date range; amount range.
  Filters combine with AND. They apply to both sections ("To enter" and "Entered in QuickBooks").
- **R2 — Pure and tested.** Filtering is a pure domain function (`domain/filters.ts`) with unit tests for each
  criterion, combinations and edge cases (missing extracted data, null totals, invalid dates, case and accents).
- **R3 — State in the URL.** Active filters live in the query string (shareable; they survive opening a record and
  coming back). Parsing and serializing are pure, tested functions; unknown or malformed values are ignored.
- **R4 — Filter bar.** Above the sections: a search box, compact controls for the other criteria, the active filters
  shown as removable chips, a "Clear filters" action, and a live result count ("12 of 40"). When nothing matches, each
  section says so and offers to clear the filters. Section counters show the filtered count.
- **R5 — Shared elements with animation, in the same view.**
  (a) Rows and cards animate their layout when the filtered set changes (enter, exit, reorder) instead of jumping.
  (b) A filter option and its active chip are one shared element (`layoutId`): choosing it moves it into the
  active-filters row, removing it sends it back.
  (c) The existing row-title → detail shared transition keeps working with filters applied (the `layoutId` of the
  title is unchanged), and returning from the detail restores the same filters.
  Motion uses the tokens of `motionTransitions.ts`; with `prefers-reduced-motion` there is no layout animation.
- **R6 — Accessible.** Every control has a label, works with the keyboard, the result count is announced
  (`aria-live="polite"`), chips are buttons with an accessible "Remove filter …" name.
- **R7 — Tests stay green.** The 15 failing baseline tests pass, and new tests cover the filter bar interactions,
  the URL round trip, the empty state and the reduced-motion path.

## Assumptions

- Filtering is client-side over the list already loaded (the API returns the whole list today); no API change.
- Interface text in English, like the rest of this view.
- No new dependency: `motion`, the existing UI primitives (`components/ui`) and Next's `useSearchParams`/router.
- Mobile cards get the same filters and the same motion.

## Out of scope

- The backend (`maros-nest`) and any API contract. Saved filter presets. Server-side pagination. Sorting changes.

## Constraints

- This is a laboratory clone. Work only inside `~/dev/maros-lab/maros-next`. There is no git remote.
- Never start the Next dev server, the API, workers or migrations; never call the real API. Tests mock their data,
  as the existing tests of this feature do. There are no env files and none may be created.
- Run checks only through the commands of the plan (they force a loopback API address).
- Create files only where the feature needs them (`src/features/invoice-scans/…`, shared presentation helpers if
  justified, the test setup). No notes, reports or scratch files inside the repository: those go to the bitácora.
