# maros-lab — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Date filter: issue date, else creation date, as the local calendar day
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** REQ-001 R1 asks for a date range over a list of mixed records (scanned invoice files and manual transactions). Invoices carry an optional `issueDate` (date-only); every record has a `createdAt` timestamp. The list itself shows `createdAt` for pending invoice files, `issueDate` for transactions and `enteredAt` once entered.
- **Decision:** `domain/filters.ts` dates a record by its `issueDate` when valid, otherwise by `createdAt` taken as the **local** calendar day (`formatDate` does the same). A malformed or impossible date (`2026-02-30`) never matches an active range; a record with no usable date is excluded while a range is active. Amount range behaves the same way for a missing or non-finite total.
- **Alternatives:** UTC day of `createdAt` — rejected: an evening record west of UTC is filed under tomorrow while the list shows it under today (the M1 builder shipped this; the M1 audit changed it). Filtering on the column the list displays (`enteredAt` for the entered section) — rejected: it would make one control mean two different things across the two sections.
- **Consequences:** + one deterministic rule for both record types, no extra API data. − the control must say it filters the invoice date, because the pending list displays creation dates (P-001). − `createdAt` results depend on the browser's time zone, so tests that touch it force `TZ`.
- **Source:** [day log](2026-10/W3/2026-10-12.md) · REQ-001/M1

## D-002 — Replace browser query state for local invoice filters
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** REQ-001 T4 needs live client-side filters whose URL survives browser navigation without making every keystroke a separate history entry. The API already loads the entire list.
- **Decision:** Use Next's `useSearchParams` to read filters and native `history.replaceState` to write the current list URL. Merge only owned filter keys using `applyInvoiceScanFilters`, preserving unrelated parameters and the hash. Next integrates native history updates with its App Router hooks ([official documentation](https://nextjs.org/docs/app/getting-started/linking-and-navigating#native-history-api)).
- **Alternatives:** `router.replace` for every change — rejected: these local criteria need no server navigation. `pushState` per edit — rejected: browser Back would step through typed characters. Local-only filter state — rejected: it loses shareability and restoration.
- **Consequences:** + local updates retain the current list entry for browser Back from detail; + no API/transport contract change. − tests must emulate Next's history integration; − the existing in-page detail return link needs explicit query propagation in the later detail round-trip work.
- **Rollback:** replace the presentation URL hook's writer with router navigation while preserving the pure query adapter and its tests.
- **Source:** [day log](2026-10/W3/2026-10-12.md) · REQ-001/T4

## D-003 — Measurable filter options and reversible shared chip motion
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** REQ-001 R5(b) requires the actual filter option and chip to share a measurable layout element; native browser select options cannot supply that DOM surface.
- **Decision:** Use the feature's existing Radix Popover with real option buttons and stable criterion/value layout IDs shared with active chips. Only inactive options carry the shared ID, avoiding simultaneous projection targets. Removing a chip opens its criterion selector for the reverse target. Scope the filter layout group separately from unchanged list/detail title IDs. Keep the list surfaces mounted at zero matches to finish the last exit.
- **Alternatives:** Animate native option tags — rejected because browser menus are not measurable DOM layout surfaces. Add a second visual option tray beside native selects — rejected as redundant controls. Introduce another select dependency — rejected because existing Popover handles focus, dismissal and keyboard access.
- **Consequences:** + real bidirectional option/chip projection with existing dependencies; + reduced motion omits new animation props. − M2 tests must select visible buttons rather than call native selectOptions; chip removal opens a local selector.
- **Rollback:** restore native controls and the previous chip rendering, keeping the pure filter/URL domain modules and behavioral tests.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · REQ-001/T6

## D-004 — Carry validated invoice filters through fixed detail/list destinations
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** Browser Back retains the list entry (D-002), but the desktop/mobile detail links and explicit detail return link discard all filters. R5(c) requires the same filters after opening a record and coming back.
- **Decision:** A feature presentation navigation hook merges the current query with validated filters using the existing pure query adapter, then builds fixed invoice detail/list destinations. Both responsive list links carry that query; the detail's explicit BackLink and successful-delete return use the same list destination. Preserve unrelated query keys; direct visits without a query keep their original paths. Never accept an arbitrary return URL.
- **Alternatives:** Browser history only — rejected because the explicit return link and direct/shared detail visits have no list-query context. Session/local storage — rejected because the approved state lives in the URL. Arbitrary return URL parameter — rejected as unnecessary redirect input and a second state representation.
- **Consequences:** + shareable detail URLs and explicit return preserve every validated filter; + additive compatibility for existing routes, no backend/API contract. − detail URLs include list query criteria and unrelated query keys. Hash restoration remains browser-history behavior; no fragment parameter is introduced.
- **Rollback:** remove query propagation from the fixed navigation hrefs while retaining domain URL parsing and the list's native-history writer.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · REQ-001/T7

## D-005 — Detach record row/card contents from the row's presence
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** M3 audit. Ticking "Entered in QuickBooks" moves a record between the two `InvoiceScansTable` surfaces. The leaving row (inside `AnimatePresence mode="sync"`) and the entering row both hold a `SharedEntityName` title with the same `maros-invoice-title-<id>-<variant>` layout id. Motion completes the exit of a shared node only after the new lead's layout animation; hidden responsive variants (and jsdom) measure zero boxes, so the exit never finished and an inert, aria-hidden, opacity-0 row stayed in the table for good (reproduced: still mounted after 1.5 s; removed once boxes differ).
- **Decision:** `InvoiceScanAnimatedRow` and `InvoiceScanAnimatedCard` render their children inside a `PresenceContext.Provider` whose value is the row's own context with `register` and `onExitComplete` replaced by no-ops. The row keeps its own exit, `inert` and `aria-hidden`; nested layout nodes (the titles) keep `isPresent`/`initial` but no longer register with the row's exit, so removal depends only on the row's fade. Title layout ids are untouched.
- **Alternatives:** Render only the variant that matches the viewport — rejected: a media-query render switch changes what both responsive trees expose to every existing test and to SSR, and does not help the visible variant. `usePresence().safeToRemove` on the row — rejected: it completes the row's own registration only; the title's registration stays pending. Drop the title layout id while exiting — rejected: installed Motion fixes projection identity at mount, and the title glide between sections would be lost. `AnimatePresence mode="popLayout"` — rejected earlier (T6): collapses the clipped wrappers. A timer that forces removal — rejected: arbitrary, and it hides the cause. `PresenceContext` value `null` (first version of this fix) — rejected after the antagonist review: it also hides `isPresent`, so Motion's promote/relegate bookkeeping of the title would no longer follow the row.
- **Consequences:** + exits always finish, no ghost rows, same shared title glide; + the fix lives in one 30-line module. − a future animated cell inside a row will not hold the row's exit open (nothing inside the rows animates through presence today); − two rows share an element id and a title layout id for ~0.3 s while a record changes section (P-009); − in zero-size boxes a title that comes back while its other copy leaves keeps `visibility:hidden` (P-011, a Motion limitation that exists with and without this decision).
- **Rollback:** delete `DetachedFromPresence`; the regression test `InvoiceScansPage.presence.test.tsx` ("removes the leaving rows and cards when the same record enters the other section") then fails again and says why.
- **Source:** [day log](2026-10/W3/2026-10-13.md) · REQ-001/M3-audit
