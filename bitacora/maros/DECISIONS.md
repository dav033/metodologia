# maros — Decision log

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

## D-001 — Limit the architecture scan to the two CRM repositories
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** A product-level architecture scan needed a confirmed boundary; the parent workspace also contains a sibling `infra/` folder.
- **Decision:** Include `maros-next` (frontend) and `maros-nest` (backend); exclude `infra/` from this scan and leave its files untouched.
- **Alternatives:** Include `infra/` — excluded at the owner's direction.
- **Consequences:** + focused audit across the two app repositories / − local infrastructure and production operations remain unverified.
- **Source:** [day log](2026-10/W2/2026-10-10.md)

## D-002 — Keep converted leads in a separate read-only view
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** Converted leads are related to projects and are intentionally excluded from the active lead pipeline. Users need to find a lead after conversion without duplicating it or removing its project.
- **Decision:** Add a separate, read-only converted-leads view backed by an additive typed API read. Keep the existing pipeline endpoint and mutation behavior unchanged; open the associated project from a converted row.
- **Alternatives:** Include project-linked leads in the main pipeline — would change existing pipeline semantics and expose current mutation actions to converted records; create a second lead — duplicates the existing CRM record; revert the project — deletes the project.
- **Consequences:** + Converted records become discoverable while the project and active pipeline remain intact / − Adds one read endpoint and a small frontend mode with additional code to maintain.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-002

## D-003 — Keep shadcn/Radix core and source motion blocks selectively
- **Date:** 2026-10-11 · **Status:** Accepted
- **Context:** The owner asked to adopt Bencho interactions, add animations, and research a separate component source for Maros. The frontend already uses shadcn/Radix with Next.js 16, React 19, and Tailwind 4.
- **Decision:** Retain shadcn/Radix for core controls. Use Motion Primitives as a supplemental copyable source for selected workflow animations; audit each block because its upstream project declares beta status. Add the `motion` runtime only when an accepted block requires it. Preserve `prefers-reduced-motion`, keyboard/touch access, and existing control semantics.
- **Alternatives:** Replace shadcn/Radix with Base UI — no functional reason to migrate an existing system; add Magic UI broadly — its documentation primarily targets landing pages and marketing material, while this scope is an internal CRM.
- **Consequences:** + Adds reusable motion patterns while retaining the existing component base / − Each copied block and any added dependency needs maintenance and per-route review.
- **Source:** [day log](2026-10/W2/2026-10-11.md) · REQ-003

## D-004 — Reuse cached project list data for project detail navigation
- **Date:** 2026-10-11 · **Status:** Accepted
- **Context:** `/projects` already has the selected project row, but `/project/[id]` independently fetched `/projects/:id/details`, delaying the detail surface and preventing a clean shared-name transition.
- **Decision:** On warm client navigation, build the detail view from the existing TanStack Query project-list cache and cached financial summary, with no list or detail refetch. Add `/projects/v2/all` for detail-only lead/contact/company read fields while retaining `/projects/all` unchanged. A cold direct link may fetch the v2 list as fallback.
- **Alternatives:** Keep the details request — duplicates the row handoff and blocks the transition; expand `/projects/all` in place — changes the existing unversioned read contract; pass ad hoc router state — does not cover direct links or share typed cache state.
- **Consequences:** + Warm navigation can render from current client data and the matching project-name element can transition between routes / − Adds a read-only v2 API contract and requires browser verification of warm-cache network behavior.
- **Source:** [day log](2026-10/W2/2026-10-11.md) · REQ-004

## D-005 — Share navigation animation and complete-detail cache reuse
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** Owner requested the accepted project handoff for all remaining navigable tables, with reusable shared-element animations and no redundant fetch on entry. Owner confirmed that missing relations/content may load and cold direct links must still work.
- **Decision:** Share directional Motion tokens and a navigation detail-query policy that reuses complete cached records on mount but respects invalidations. Keep feature-owned list→detail adapters, explicitly distinguish summaries/placeholders from complete records, and use separate `detail/id/view` keys where CRUD caches hold base records. Do not retain mutable App Router outlets during exit. Document URLs retain expiry renewal.
- **Alternatives:** A generic cross-domain repository/model would mix contracts; treating summaries as complete would silently fabricate missing relationships; suppressing all fetching would break direct links and detail-only content.
- **Consequences:** + Shared animation/cache mechanics and feature-specific completeness rules / − Each feature still owns its projection and detail-only load, and source lists use mutation invalidation rather than stale mount refetch; explicit refresh and necessary URL renewal remain available.
- **Rollback:** Restore per-feature query/transition settings and SSR detail loaders; no data migration or API contract removal is involved.
- **Source:** REQ-004 extension, owner confirmation in current session.
