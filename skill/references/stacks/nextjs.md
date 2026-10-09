# Next.js (frontend)

Only what differs from defaults. General rules: `../engineering.md`.

## Layout
```
src/
  app/                      routes only: thin page/layout files that compose feature public APIs
    <route>/_components/    UI used only by this route (kebab-case files)
  features/<feature>/
    domain/                 types, business rules (pure TS: no React, Next or TanStack)
    application/            queryOptions factories, client hooks, Server Actions
    infrastructure/         Data Access Layer (server-only) and the feature's API client
    presentation/           feature components, flat (order-table.tsx); purpose-named subfolders past ~10 files
    index.ts                public API for any caller: named exports only
    index.server.ts         public API that must never reach the client (DAL functions)
  shared/
    ui/atoms|molecules|organisms   design system (shadcn-based), domain-free; no index.ts barrels
    lib/ errors/ config/
```
- Imports: `app` → `features` (only `index.ts` / `index.server.ts`) → `shared`. Features never import each other;
  combine them in the route. Inside a feature use relative imports; across slices the alias (`@/features/orders`).
- `application/` may import its own `infrastructure/` (TanStack hooks call the feature's API client): the explicit
  exception to "application doesn't depend on infrastructure". `presentation/` never imports `infrastructure/`.
- File and folder names kebab-case (`app/` route folders exempt: `[id]`, `(group)`, `_components`).
- Enforced by `templates/arch/nextjs/` (eslint-plugin-boundaries + dependency-cruiser), see `../engineering.md` §9.

## Data access
- One approach per project: a **Data Access Layer**. Each feature's DAL module in `infrastructure/` starts with
  `import "server-only"`, checks auth/authorization, calls the backend, and returns minimal DTOs (never raw API or
  DB objects). It is the only code that reads secrets from `process.env`.
- Server Components get data from the DAL through `index.server.ts`. `page.tsx` reads params/session, calls the
  feature's public API and composes; no fetching code of its own.
- Server Actions (`"use server"`) are thin: validate input with zod, re-check auth, call the DAL, return only what
  the UI needs. No mutations during render.

## Client boundary
- `"use client"` on the smallest interactive file, never a page or layout. Pass Server Components to Client
  Components as `children`/props instead of importing them.
- Providers wrap `{children}` as deep in the tree as possible.
- Modules touching secrets import `server-only`; browser-only modules import `client-only`.
- Client Component props are narrow (only the fields rendered), never whole API objects.

## Server state (TanStack Query)
- Per feature, one `application/queries.ts` exporting `queryOptions` factories (key + queryFn together; keys generic to
  specific: `['orders', 'list', filters]`). The same options feed `useQuery`, server `prefetchQuery` and
  invalidation. A `useX` wrapper only when it adds logic.
- SSR: QueryClient per request (`getQueryClient` in its own module), prefetch in the Server Component, wrap in
  `HydrationBoundary`. Default `staleTime` > 0.
- Never copy query data into `useState`; derive from it. Invalidate the feature's keys after a mutation.
- State placement: server state in TanStack Query; shareable UI state (filters, tab, page) in the URL; form state in
  react-hook-form; local UI state in the component; zustand only for truly global client state.

## Defaults
- App Router, React Server Components by default.
- Forms: react-hook-form + zod (the same zod schema validates on the server).
- UI: Tailwind + shadcn/ui as `shared/ui` atoms/molecules. No inline styles, no ad-hoc CSS files per component.
- Env: validated with zod in `shared/config`; only `NEXT_PUBLIC_*` reaches the client, never secrets.
- Errors: expected failures (validation, 4xx, not found) are return values: actions return
  `{ ok: false, error: AppError }`, consumed with `useActionState`; `notFound()` for missing resources. Bugs throw
  and land in `error.tsx` per segment (+ `global-error.tsx`). Error boundaries don't catch event-handler or async
  errors: catch those and set state. `AppError` (code + message) maps to user text in one place.
- Loading/empty/error states for every data view.

## Testing
Vitest + Testing Library: integration tests per feature (render the feature's components, mock the network with
MSW), unit tests for domain logic. Tests colocated (`order-table.test.tsx` next to the file). Playwright for the
few critical journeys. Don't snapshot-test atoms.

## Verify
`npm run verify` = `lint && typecheck && arch && test && build`, with `"arch": "depcruise src --config
.dependency-cruiser.cjs"` (eslint already runs the boundaries rules).
