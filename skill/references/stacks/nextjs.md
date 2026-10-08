# Next.js (frontend)

Only what differs from defaults. General rules: `../engineering.md`.

## Layout
```
src/
  app/                      routes only: thin pages/layouts that compose templates and fetch; no business logic
  features/<feature>/
    domain/                 types, business rules (pure TS)
    application/            use cases, query/mutation hooks (TanStack Query)
    infrastructure/         API client for this feature (fetch wrappers, DTO ↔ domain mappers)
    presentation/
      atoms/ molecules/ organisms/ templates/   feature-specific UI (Atomic Design)
      hooks/                UI state hooks
    index.ts                public surface
  shared/
    ui/atoms|molecules|organisms|templates      design system (shadcn-based)
    lib/ errors/ config/
```
Path aliases per feature (`@/features/orders`) and import only through `index.ts`. Enforce with
`eslint-plugin-boundaries`.

## Defaults
- App Router, React Server Components by default; `"use client"` only on the leaf components that need state,
  effects or browser APIs — push it down, never on a whole page.
- Server data: fetch in Server Components or via TanStack Query in client components. Mutations through Server
  Actions or the feature's API client; invalidate queries after mutating.
- Forms: react-hook-form + zod (the same zod schema validates on the server).
- UI: Tailwind + shadcn/ui as atoms/molecules. No inline styles, no ad-hoc CSS files per component.
- State: server state in TanStack Query; local UI state in components/hooks; global client state (zustand) only
  when truly shared and not server data.
- Env: validated with zod in `shared/config`; only `NEXT_PUBLIC_*` reaches the client — never secrets.
- Errors: a typed `AppError` (kind + message) mapped to user-facing text in one place; `error.tsx` per route
  segment for unexpected failures.
- Loading/empty/error states for every data view.

## Testing
Vitest + Testing Library for domain logic, hooks and organisms with behavior; Playwright for the few critical
journeys. Don't snapshot-test atoms.

## Verify
`npm run verify` = `lint && typecheck && test && build`.
