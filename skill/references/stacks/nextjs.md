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
    ui/atoms|molecules|organisms   project compositions over `@bitacora/ui`, domain-free; no index.ts barrels
    lib/ errors/ config/
  mocks/ test/ types/       MSW handlers, test setup, global *.d.ts
```
- A feature always uses the layer folders, even with one file each; its root holds only `index.ts` and
  `index.server.ts`.
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
- UI: Tailwind + the component pool `@bitacora/ui` (D-280, see §Component pool). `shared/ui` only composes pool
  components; never a local copy of one and no `npx shadcn add`. No inline styles, no ad-hoc CSS files per component.
- Env: validated with zod in `shared/config`; only `NEXT_PUBLIC_*` reaches the client, never secrets.
- Errors: expected failures (validation, 4xx, not found) are return values: actions return
  `{ ok: false, error: AppError }`, consumed with `useActionState`; `notFound()` for missing resources. Bugs throw
  and land in `error.tsx` per segment (+ `global-error.tsx`). Error boundaries don't catch event-handler or async
  errors: catch those and set state. `AppError` (code + message) maps to user text in one place.
- Loading/empty/error states for every data view.

## Component pool (`@bitacora/ui`, D-280/D-290)
A project with a UI opts in during the requirements interview (`bitacora.py components adopt <project> --role <ui
repo role> [--from <tokens.css>]`); the sync writes the package into `packages/bitacora-ui` (+ `SYNC.json`) on the
default branch and keeps it current. Never edit that folder: change the pool in metodologia. The plan's first task in
a repo without the wiring is «wire @bitacora/ui»:
- root `package.json`: `"workspaces": ["packages/*"]` and `"@bitacora/ui": "*"` in `dependencies`; `npm install`
  links it and installs its dependencies (peers: react/react-dom ≥ 19, motion ≥ 12, lucide-react ≥ 1); commit the
  lockfile.
- `next.config.ts`: `transpilePackages: ["@bitacora/ui"]` (the package ships `.tsx`/`.css`, no build).
- global CSS: `@import "tailwindcss"; @import "@bitacora/ui/styles.css";` then the look:
  `@import "@bitacora/ui/themes/<project>.css";` when the project has a theme (imported from its tokens), else
  `@import "@bitacora/ui/theme.css";` (Catppuccin default). A project that keeps its tokens in its own CSS defines
  the same roles after `styles.css` instead, and re-imports the theme so mockups match.
- dark mode: `.dark` or `data-theme="dark"` on `<html>` set before hydration.
- imports are package paths (`@bitacora/ui/components/ui/button`), never the project's `@/` alias.
- verify: type-check + `next build` pass with one pool component rendered; `packages/bitacora-ui/SYNC.json` exists.

Developing a pool change, the two-step loop (D-293/D-295):
1. Run `npm run dev` in the project checkout and, beside it, `bitacora.py components dev <project>` (target: the main
   checkout of the project's UI repo, or `--into <tree>`; source: the live `skill/ui` with uncommitted edits, or
   `--from <wt>/skill/ui`). It refuses a branch without `@bitacora/ui` and anyone's edits in `packages/bitacora-ui`.
2. Edit the pool: each save (stable ~2 s) is written into `packages/bitacora-ui`, uncommitted, and every page using
   it hot-reloads — no commit, no integration, no restart.
The copy's `SYNC.json` says `"dev": true` (`pool: dev-<digest>`), so the project's guard fails on it: never commit it
(no `git commit -a` there). Ctrl-C (or a closed terminal) restores the committed package (`--keep` leaves it;
`components dev <project> --restore` later). Then commit/integrate the pool: the merge syncs every opted-in project.
`components watch --from <wt> --into <tree>` is the same without the defaults. The user unit `bitacora-ui-watch.service`
(installed by `install.py`, `systemctl --user enable --now bitacora-ui-watch`) runs the default mode on the live
pool: a committed change there is synced like the integrate trigger does; uncommitted edits under `skill/ui` wait.

## Testing
Vitest + Testing Library: integration tests per feature (render the feature's components, mock the network with
MSW), unit tests for domain logic. Tests colocated (`order-table.test.tsx` next to the file). Playwright for the
few critical journeys. Don't snapshot-test atoms.

## Verify
`npm run verify` = `lint && typecheck && arch && test && build`, with `"arch": "depcruise src --config
.dependency-cruiser.cjs"` (eslint already runs the boundaries rules).
