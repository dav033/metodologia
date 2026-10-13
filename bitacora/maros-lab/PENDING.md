# maros-lab — Pending

_Sorted automatically by `bitacora.py pending` (urgency high → low, then complexity S → L: quick urgent wins first).
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._

## Open
- P-005 · REQ-001/R5: see the shared-element motion once in a real browser before merging · urgency: med · complexity: S · added 2026-10-13 · REQ-001/M3-audit
  jsdom has no layout, so every check of R5 is a contract on props, ids and presence; no test (and no session of this lab) has seen a pixel move. Look at: option → chip and back (Popover closing while the chip mounts), rows/cards reordering and leaving on desktop and mobile widths, title → detail → back with filters, and the `prefers-reduced-motion` switch. Needs the owner (or a session allowed to run the dev server).
- P-003 · Free text matches one phrase per field, so a multi-word query that spans fields ("acme 1042") matches nothing · urgency: low · complexity: S · added 2026-10-12 · REQ-001/M1-audit
  Proposal, not a defect: split the text into tokens and require every token to appear in some field. It is a superset of today's behaviour and the unit tests would stay valid. Left as is because the spec does not define multi-word semantics.
- P-007 · Row links change href on every filter edit, so Next re-prefetches every visible detail link per keystroke · urgency: low · complexity: S · added 2026-10-13 · REQ-001/M3-audit
  `useInvoiceScanNavigation` appends the query to every `Link` (D-004) and the search box writes the URL per character. Next prefetches a `Link` again when its href changes: with ~30 visible rows that is ~30 partial RSC requests per character in production. Unmeasured in the lab (no server). Options: `prefetch={false}` on the row links, or debounce the URL write of the search box.
- P-008 · A record created from the filtered list opens its detail without the list filters · urgency: low · complexity: S · added 2026-10-13 · REQ-001/M3-audit
  `NewTransactionDialog` pushes `/finance/invoices/<id>` (also after a scan upload), so "All document scans" there returns an unfiltered list. Probably fine for a brand-new record; decide whether `detailHref` should be used.
- P-013 · Amount filters: `inputMode="decimal"` hides the minus key on phone keypads and unparsable text is dropped silently on blur · urgency: low · complexity: S · added 2026-10-13 · REQ-001/M2-audit
  Negative totals are valid (a refund is `-25` in the fixtures) but iOS/Android decimal keypads have no minus. Text such as `1,000` or `10,5` does not parse, shows no error and the field empties on blur. Options: `inputMode="text"` plus a hint, or accept thousands separators and flag unparsable text through `aria-invalid` and a message like the reversed-range ones. Not verified on a device.
- P-002 · 11 tests outside invoice-scans are red on the lab baseline · urgency: low · complexity: M · added 2026-10-12 · REQ-001/M1-audit
  All 11 are also red at `3ea1a97`, unrelated to REQ-001: StaleLeadsReport (4) fails reading `get` of a null `useSearchParams()`; PostConversionEstimateModal (3) with "invariant expected app router to be mounted"; NotesHomeView (1) on `toHaveClass("italic")`; ProjectCostBreakdownCard (1) on the "sin pronóstico" placeholder; ReceivablesPage (2) cannot find the "Roof tear-off" link. The matchMedia stub took the suite from 37 failures to 11.
- P-006 · Chip removal opens the criterion selector, also with reduced motion and never for search/range chips · urgency: low · complexity: M · added 2026-10-13 · REQ-001/M3-audit
  D-003 opens the selector so the removed chip has a reverse target. Under `prefers-reduced-motion` there is no target and the popup is pure surprise; search and range chips (no option) vanish and keyboard focus falls to the body. Owner call: keep as is, skip the popup when motion is reduced and move focus to the criterion control, or render the options inline so chip and option always coexist.
- P-012 · The search draft can be reverted by a lagging URL echo while typing fast on a long list · urgency: low · complexity: M · added 2026-10-13 · REQ-001/M2-audit
  `InvoiceScanDraftInput` resets its draft whenever the `value` prop (from `useSearchParams`) differs from the last value it wrote, so a stale echo of an older keystroke reads as an external change. Real Next delivers `history.replaceState` through a transition; the lab harness uses `useSyncExternalStore` (synchronous) and cannot show it. Possible effect: the box briefly shows older text and a character typed in that window is lost (the URL converges). Options: debounce the search URL write (also reduces P-007), or remember the values written and ignore their echoes (clear that list when the prop catches up, or chip removal / Back would be swallowed). Check it in the P-005 browser pass: type quickly on a list of ~100 records.
- P-014 · The filter panel is always fully expanded: eight controls plus date help text sit above the lists · urgency: low · complexity: M · added 2026-10-13 · REQ-001/M2-audit
  R4 asked for "compact controls"; below 640 px the four range inputs stack in one column and the first record starts far below the fold. Owner/design call: a "Filters" disclosure that keeps the search box, the count and the chips visible and folds the criterion controls (the option/chip shared-element pair keeps working because chips stay outside). Minor, same area: the Popover trigger buttons carry a `value` attribute only so tests can assert `toHaveValue`.

## Blocked
_None_

## Recently closed
- P-009 · CLOSED: checkbox labels resolve to their own responsive/exiting instance · urgency: low · complexity: S · added 2026-10-13 · REQ-001/FINAL-session12
  Whole-branch reviewers correctly classified the duplicate DOM IDs as a correctness defect. EnteredCheckbox now includes React useId per instance; the real-Motion regression checks all four overlapping instances, htmlFor and getElementById. The shared title layout IDs intentionally remain equal for animation; DOM checkbox IDs no longer collide. Fresh final Verification: 125 tests, typecheck and lint pass.
- P-011 · CLOSED: revived responsive titles recover visibility after rapid section reversal · urgency: low · complexity: S · added 2026-10-13 · REQ-001/FINAL-session12
  InvoiceScanAnimatedTitle remounts only the title projection on recovered presence, retaining exact list/detail layout IDs and surviving title nodes. Real-Motion regressions reverse both directions with active filters, then assert both responsive titles remain visible after 800 ms and no inert rows remain. Fresh final Verification: 125 tests, typecheck and lint pass. Pixel-level browser confirmation remains P-005.
- P-010 · CLOSED: REQ-001 trace unknown-ref metadata diagnostics · urgency: low · complexity: S · added 2026-10-13 · FINAL/session11
  The installed parser already supports the bold requirement form; no SPEC/tool edits were needed. Session 11 replaced inherited real-project SUMMARY state and clarified the historical audit's external references. Fresh `bitacora.py --project maros-lab trace`: 7 R, 7 T, 1 REQ; lint clean.
- P-004 · CLOSED: REQ-001 M2-audit (blocked twice by usage limits) · urgency: high · complexity: ? · added 2026-10-13 · marathon
  Done in marathon session 10: pass-with-fixes, see `requirements/REQ-001-invoice-list-filters-and-shared-element/AUDIT-M2.md`; follow-ups P-012…P-014.
- P-001 · CLOSED: REQ-001/T4 date semantics, query merging and reversed-range feedback · urgency: med · complexity: S · added 2026-10-12 · REQ-001/M2
  Explicit invoice-date labels/help describe issue date or local creation day when absent (D-001). The query adapter preserves unrelated keys/hash; reversed date and amount bounds expose associated errors. Verified by five page filter regressions, query-helper unit tests, typecheck and feature ESLint.

## Notes
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
One line per item: `P-012 · <task> · urgency: high|med|low · complexity: S|M|L · added YYYY-MM-DD · <source>`.
Indented lines under an item are its details and move with it. Get IDs with `bitacora.py id P`._
