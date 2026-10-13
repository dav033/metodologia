# Audit — REQ-001 milestone M3 (T6–T7)

Auditor: claude/sonnet-5-5, marathon session 9 · Branch `feat/req-001-invoice-list-filters-and-shared-element` · Audited `55ffc40` (T6) and `b16a07f` (T7) · Added `996d87c` (presence tests) and `64cfd28` (fix + regression test).

## Verdict: pass-with-fixes

T6 and T7 deliver R5(a)–(c) and the R7 test obligations as far as jsdom can show, and every verify command of the
milestone is green. One real defect turned up in the section move (a record ticked "Entered in QuickBooks") and is
fixed here with a regression test; the rest is design/verification follow-up in PENDING.md. Nobody — builder or
auditor — has seen the motion in a real browser (P-005): this lab forbids starting the dev server.

## What I checked

- **R5(a) rows and cards.** Desktop `tr` and mobile `li` are Motion surfaces with `layout="position"`, opacity
  enter/exit, timing from `taskCardSurfaceTransition` (layout) and `routeEntranceTransition` (opacity). `AnimatePresence`
  is `mode="sync"` with `initial={false}`, so the first render and the return from a detail do not fade rows in. Both
  surfaces stay mounted at zero matches so the last record can exit; leaving records are `inert` + `aria-hidden`.
  `LayoutGroup` without an id inherits the (empty) title namespace — read in `framer-motion/.../LayoutGroup/index.mjs`:
  no id and no upstream group means no prefix, so list ↔ detail ids are unchanged.
- **R5(b) option ↔ chip.** Real Radix Popover buttons with `layoutId = maros-invoice-filter-<key>-<value>`; the selected
  option omits the id while its chip exists; chips and options are re-keyed on value/selected/reduced-motion changes
  because Motion freezes projection identity at mount (T6 review, verified there against the installed source).
  Removing a chip opens its selector to supply the reverse target (D-003) — see P-006.
- **R5(c) title and filters through the detail.** Title ids untouched (`...-desktop|mobile`); both responsive links,
  the explicit "All document scans" link, the error return and the post-delete push use one fixed destination built from
  the validated filters plus unrelated keys (D-004). No arbitrary return URL, no open redirect, both routes are
  `force-dynamic` so `useSearchParams` needs no Suspense boundary.
- **Reduced motion.** Rows, cards, chips and options carry no animation props; flipping the preference remounts the
  animated surfaces. With reduced motion filtered-out rows leave the DOM at once (new test).
- **R6/R7.** Labels, `aria-live="polite"` count, "Remove filter …" names, Escape/focus return, keyboard path — all
  asserted. The baseline tests of T1 still pass.
- **Scope and hygiene.** The branch touches only `src/features/invoice-scans/**` and `vitest.setup.ts`; no
  `console`/`debugger`/`.only`/`.skip`/TODO/`any`/`@ts-*`, no secrets, no env files, no new dependency, nothing pushed.
  `git diff --check` is clean.
- **Docs.** ARCHITECTURE lab section, D-003, D-004 and the day log match the code (checked line by line against the
  components); the T7 "update ARCHITECTURE" requirement is met.
- **Tests would fail without the change.** Mutation spot-checks on the working tree (restored afterwards): chip
  loses `layoutId` → 2 motion tests fail; detail link drops the query → both round-trip tests fail; rows ignore reduced
  motion → 2 tests fail; `initial={false}` removed → the new first-render test fails.
- **Not audited here:** M2 as a milestone (`M2-audit` is still blocked, P-004). I read its components and parser because
  M3 builds on them and the full suite below covers its 36+4 filter/URL tests; I found nothing blocking.

## Findings fixed

1. **A record moved between sections left an invisible ghost row behind** (`InvoiceScanListMotion.tsx`). Ticking
   "Entered in QuickBooks" puts the same record's title (same `layoutId`) in the leaving row of "To enter" and in the
   entering row of "Entered". Motion completes the leaving exit only after the new lead's layout animation, which does
   not run when the shared nodes measure zero boxes — jsdom, and the `display:none` responsive variant of any real
   browser. The leaving row/card then stayed mounted forever: `inert`, `aria-hidden`, opacity 0, still taking its
   height (it shows up as a blank gap when the viewport crosses the `md` breakpoint). Reproduced in a scratch test:
   ghost still there after 1.5 s with zero boxes, gone with stubbed distinct boxes. Fix (`64cfd28`, decision D-005):
   row and card children render inside a `PresenceContext.Provider` whose value is the row's own context with
   `register`/`onExitComplete` replaced by no-ops, so the nested layout nodes keep `isPresent`/`initial` but do not
   hold the row's exit. The row keeps its own fade, `inert` and `aria-hidden`; title ids are unchanged. Regression test
   "removes the leaving rows and cards when the same record enters the other section" fails on the previous code.
   The antagonist reviewed the staged first version (`null` context): no blocker, one minor — `null` hides
   `isPresent` from the title's promote/relegate — which is why the final fix derives the context instead.
2. **Missing coverage of real presence behaviour** (`InvoiceScansPage.presence.test.tsx`, new). The contract tests
   mock `motion/react`; four tests now keep the real presence machinery: first render does not fade/hide records
   (fails without `initial={false}`), reduced motion removes filtered-out rows and cards, records that return while
   leaving become interactive again and survive past the exit duration, and no `inert` leftovers remain after a filter
   change.

## Findings deferred (PENDING.md)

- **P-005 · med · S.** R5 has never been seen in a browser; one manual pass (option → chip and back, reorder/exit on
  both widths, title → detail → back with filters, reduced-motion switch) before merge.
- **P-006 · low · M.** Chip removal opens the selector also with reduced motion, and search/range chips vanish with
  the keyboard focus falling to the body. Owner call.
- **P-007 · low · S.** Row links change href per filter edit; Next re-prefetches every visible link per keystroke in
  production. Unmeasured here.
- **P-008 · low · S.** A record created from the filtered list opens its detail without the filters.
- **P-009 · low · S.** While a record changes section, `entered-<id>` and the title layout id are duplicated for
  ~0.3 s (a `<label for>` can resolve to the inert checkbox).
- **P-011 · low · S.** A title that returns to its section within ~0.3 s of leaving it stays `visibility:hidden` in a
  zero-size (hidden responsive) variant: Motion clears `visibility` only through a projection delta. Same with the
  original M3 code and with D-005 (the antagonist found it; I reproduced it). Visible only after crossing the `md`
  breakpoint.
- **P-010 · low · S.** `bitacora.py trace` reports 14 unknown-ref errors because the SPEC writes `- **R1 — …**`;
  not edited here (approved SPEC, plan drift is tracked).

## Notes for the next session

- The trace "dangling" ids from the copied SUMMARY belong to the original Maros project, not the lab's requirement or pending namespace; they are not implementation failures. Session 11 clarifies this reference spelling without changing the audit verdict.
- Whole-suite failures are the same 11 as the M1 baseline (P-002); none is in a file this milestone touched.
- Final requirement closure (REPORT.md, PLAN `status: done`) is the supervisor's. R1–R7 are all covered by tests;
  R5's visual quality is the open point (P-005).

## What I ran

All with the plan's clean environment (`env -i … NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:9/api …`):

| Command | Result |
|---|---|
| T6 verify: `npm run typecheck`, `npx eslint src/features/invoice-scans`, `npx vitest run src/features/invoice-scans` | exit 0; 14 files / 115 tests before my changes |
| T7 verify: vitest feature suite, `npm run typecheck`, `npm run lint` | exit 0; lint 0 errors, 164 warnings (identical to HEAD, none in the feature) |
| `npx vitest run` (whole suite), before my commits | 11 failed / 5 files (StaleLeadsReport 4, PostConversionEstimateModal 3, NotesHomeView 1, ProjectCostBreakdownCard 1, ReceivablesPage 2) = M1 baseline; 430 passed |
| Mutation spot-checks (4) on chip layoutId, detail query, reduced motion, `initial={false}` | each caught by the named tests; tree restored |
| Scratch tests (removed) for the section move: zero boxes vs stubbed distinct boxes | ghost persists vs removed; basis of finding 1 |
| `bitacora.py trace --json` | 14 unknown-ref (SPEC format) + 10 dangling (copied SUMMARY): metadata only |
| Antagonist review of the staged fix (one pass) | CONCERNS, nothing blocking; minor accepted (derived context), pre-existing quirk → P-011; no re-review |
| Final: exact T6 chain and exact T7 chain after `64cfd28` | both exit 0; 15 files / 120 tests; typecheck 0; ESLint 0; lint 0 errors / 164 warnings, none in the feature |
| Final: `npx vitest run` (whole suite) after `64cfd28` | 11 failed in the same 5 files as the M1 baseline, 435 passed (446 tests); no new failure |
