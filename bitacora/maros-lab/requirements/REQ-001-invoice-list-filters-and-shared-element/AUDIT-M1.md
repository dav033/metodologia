# Audit — REQ-001 milestone M1 (T1–T3)

Auditor: claude/sonnet-5-5, marathon session 2 · Branch `feat/req-001-invoice-list-filters-and-shared-element` · Audited `ccd2376`, `073c7d5`, `f3fcd8e` · Fix committed as `b85a7ca`.

## Verdict: pass-with-fixes

M1 does what R2 and R3 ask and the baseline of R7 is restored. One real defect in T2 was fixed here; the rest
of what I found is design follow-up for M2 and goes to PENDING.md.

## What I checked

- **T1 (matchMedia).** Only `vitest.setup.ts` changed; no test or assertion was touched. The stub is guarded with
  `typeof window` (the Node-environment suites `devMode.test.ts` and `openaiApiKey.test.ts` would crash without it).
  The two invoice page files pass (21 tests). Against the baseline snapshot the stub took the whole suite from 37 to
  11 failing tests with no new failure, and `usePrefersReducedMotion.test.tsx`, which uses `vi.stubGlobal`, still passes.
- **T2 (filters).** R1 criteria are all present and AND-combined: free text over title, file name, counterparty,
  invoice number, project number and comments (case and accent insensitive); record type with an omitted
  `recordType` read as invoice; money direction through `moneyFlow` (so `unknown` never matches in/out); status;
  classification; date range; amount range. Missing totals, non-finite totals, impossible calendar dates and
  records with no extracted data never match an active range. The input list is not mutated.
- **T3 (URL state).** Unknown keys and malformed values are ignored; dates are validated as real calendar days;
  amounts accept the exponent form `String()` produces, so finite bounds round-trip; serialization of `{}` is `""`.
- **Hygiene.** Working tree clean (only the ignored `tsconfig.tsbuildinfo`), no files created outside the feature
  and setup, no `console`, `debugger`, `.only`/`.skip`, TODO or secrets in the diff. Nothing was pushed or started.

## Findings fixed (commit `b85a7ca`)

1. **Creation-date fallback used the UTC day, not the day the list shows** (`domain/filters.ts`, `scanDate`).
   `createdAt: 2026-10-02T03:30:00Z` is Oct 1, 22:30 in Bogota, and `formatDate` renders it as Oct 1, but the filter
   filed it under Oct 2, so a range ending Oct 1 dropped a record the user sees on Oct 1 (every evening, for any user
   west of UTC). It now uses the local calendar day. New test forces `TZ=America/Bogota`, asserts its own
   precondition, and fails on the previous code (verified by restoring the old source). Recorded as D-001.
2. **R2's "missing extracted data" edge case had no test.** Added a test for a scan with `extractedData: null`
   against every criterion (text via project number, file name and comments; status; date via `createdAt`; and the
   classification, money direction and amount filters that must exclude it). Its date range is wide enough to be
   time-zone independent.
3. **The matchMedia stub was non-configurable**, so a test redefining it with `Object.defineProperty(..., { configurable: true })`
   would throw. T7 needs to simulate `prefers-reduced-motion`; the stub is now `configurable: true`.

## Findings deferred (PENDING.md)

- **P-001 · T4 · urgency med · complexity S.** The pending list shows the creation date for invoice files and the
  issue date only for transactions, while the filter prefers the issue date: the control must be labelled for what it
  does (the T2 antagonist and the builder both flagged this). Same task: `serializeInvoiceScanFilters` emits only
  filter keys, so the page has to merge it into the existing query string; `dateFrom > dateTo` and
  `amountMin > amountMax` silently match nothing and should be flagged in the controls.
- **P-003 · low · S.** Free text is one phrase per field; a multi-word query spanning fields ("acme 1042") matches
  nothing. Not a defect against the spec (it does not define it); a token-AND search would be a strict superset.
- **P-002 · low · M.** 11 tests outside invoice-scans are red on the lab baseline and unrelated to REQ-001
  (StaleLeadsReport 4, PostConversionEstimateModal 3, NotesHomeView 1, ProjectCostBreakdownCard 1, ReceivablesPage 2).

## Notes for the next session

- M1's own acceptance (R2, R3) is complete; R1/R4/R6 are not user-visible until T4.
- The plan's verify commands for T4–T7 run `npx eslint src/features/invoice-scans` and `npm run lint`; both pass
  today (`npm run lint`: 0 errors, 164 warnings, all outside this feature), so they are usable as gates.
- The SUMMARY.md "Top pending" list still names the real project's P-004…P-009, copied into the lab; the lab's
  own IDs start at P-001 and the next free one is P-004.

## What I ran

All with the plan's clean environment (`env -i … NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:9/api …`):

| Command | Result |
|---|---|
| `npx vitest run src/features/invoice-scans/presentation/pages` (T1) | 2 files, 21 tests passed |
| `npx vitest run src/features/invoice-scans/domain` (T2, T3) | 4 files, 16 tests passed (was 14; +2 added here) |
| `npm run typecheck` | exit 0 |
| `npx eslint src/features/invoice-scans vitest.setup.ts` | exit 0, no output |
| `npm run lint` | exit 0, 0 errors, 164 warnings (none in the files of this milestone) |
| `npx vitest run` (whole suite) on the branch, before and after the fix | 11 failed / 5 files; 369 → 371 passed |
| `npx vitest run` on a `git archive 3ea1a97` snapshot with the repo's `node_modules` linked | 37 failed / 9 files |
| Failing set of the branch minus the baseline's | empty |
| Same domain test against the previous `filters.ts` | the new TZ test fails (`expected [] to deeply equal [...]`) |
