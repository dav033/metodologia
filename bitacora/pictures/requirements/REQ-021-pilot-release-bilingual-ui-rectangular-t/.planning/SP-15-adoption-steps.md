# pictures — adopting `@bitacora/ui` (D-280): ordered steps for a REQ-021 subplan

Source: metodologia main `621bf4d4d` (merge of `ui-pool`). Owner: «Todo ya, dentro de REQ-021», «gana el pool»,
«Directo». Place the subplan (draft: `.planning/SP-15-ui-pool-skeleton.md`) after SP-2 and SP-14: step 1 waits for
T14.6 and T10.6 so no step edits files under an active SP-2/SP-14/SP-10 task. Each step is one task; each ends green.

Facts that shape the steps (read 2026-11-01, read-only):
- pictures `package.json` already has `"workspaces": ["packages/*"]`; React 19.2, Next 16.3, Tailwind 4, motion 13,
  lucide-react 1.x — all within the pool's peer ranges. The pool imports `cn` (shadcn's package), not clsx/twMerge.
- The pool package exports raw `.tsx`/`.ts`/`.css` (no build step): Next needs `transpilePackages`.
- `src/app/globals.css` owns the Sempertex tokens (`--fondo`, `--acento`, `--taller-*`, …), the shadcn role aliases
  (`--background: var(--fondo)`, …) and an `@theme inline` that maps roles to `--color-*`; the pool's `styles.css`
  carries the same role → `--color-*` mapping. `layout.tsx` sets `data-theme` before hydration, which the pool's dark
  variant (`.dark *, [data-theme="dark"] *`) relies on; the `prefers-color-scheme` block is only the no-JS fallback.
- Local duplicates: `src/components/ui/{checkbox,select,tabs,tooltip}.tsx`, `Ayuda.tsx`, `interruptor-tema.tsx`,
  `foco-retorno.ts`, `shell/*` (≈38 importers on origin/main per SP-15).

## 1. Opt in and first sync (operator action in metodologia, not a pictures task)
In `~/bitacora/pictures/project.json` add `"ui": {"sync": true, "repo": "pictures"}` (role `pictures`, default
branch `main`; `"push": false` unless the owner wants the sync commit pushed). Then from `~/dev/metodologia`:
`.venv/bin/python skill/scripts/bitacora.py components sync pictures`. It writes `packages/bitacora-ui/`
(package.json, LICENSES.md, `src/**`, `themes/pictures.css`, `SYNC.json` with version/digest/source commit) and
commits only that path on pictures `main`. From then on every metodologia merge that changes `skill/ui/` re-syncs it
(bt_integrate, after the smoke). Done when: pictures `main` has the sync commit; REQ-021's line merges `main`.

## 2. Wire the package (T: install + build config)
- `npm install` at the root so the workspace links `@bitacora/ui` and installs its dependencies (@base-ui/react,
  @animate-ui/react, cmdk, sonner, recharts, react-day-picker, gsap, @hugeicons/*, cn, …); commit `package-lock.json`.
- `next.config.ts`: `transpilePackages: ["@bitacora/ui"]`.
- No tsconfig alias: pool imports are package-relative (`@bitacora/ui/components/ui/button`), never pictures' `@/`.
Done when: `npm run build` and the type-check pass with nothing imported from the pool yet.

## 3. Theme: Sempertex tokens on the pool roles (T: globals.css)
pictures' `globals.css` stays the owner of the values; the pool brings structure.
- After `@import "tailwindcss";` add `@import "@bitacora/ui/styles.css";` (do NOT import the pool's `theme.css` —
  that is the Catppuccin default — nor `themes/pictures.css`, which metodologia generates FROM this file).
- Keep the role aliases (`--background: var(--fondo)`, `--primary: var(--acento)`, …) in light, explicit dark and
  the `prefers-color-scheme` fallback block; add the roles the pool needs that pictures lacks: `--ui-font-sans`,
  `--ui-font-mono` (Geist / JetBrains Mono), and the Bencho triplet roles `--foreground-rgb`, `--card-rgb`,
  `--muted-rgb`, `--primary-foreground-rgb` (light `28, 20, 37` / `255, 255, 255` / `239, 233, 248` /
  `255, 255, 255`; dark `244, 245, 247` / `22, 24, 31` / `36, 39, 51` / `18, 11, 36`; repeat dark in the fallback
  block), plus `--success`, `--warning`, `--info` and their `-soft` pairs, `--primary-hover`, `--primary-soft`,
  `--destructive-soft`, `--destructive-hover` mapped to `--exito`, `--aviso`, `--acento-hover`, `--acento-suave`,
  `--error-suave`, …
- Remove from pictures' `@theme inline` only the shadcn-role lines `styles.css` already maps (`--color-background`,
  `--color-primary`, …); keep every pictures-specific `--color-fondo`, `--color-taller-*`, `--font-*`, `--radius-*`.
- Then, in metodologia: `bitacora.py components theme import pictures --from <pictures>/src/app/globals.css
  --mockup-fonts @fontsource-variable/geist,@fontsource-variable/jetbrains-mono` so mockups match (the next sync
  carries it).
Done when: contrast check passes for both themes, and a page with no pool component looks pixel-identical
(screenshot diff of the Taller, Cuentas and Planes entry points, ES/EN, light/dark).

## 4. Replace the leaf controls with pool components (T: checkbox, select, tabs, tooltip, Ayuda, interruptor-tema, foco-retorno)
Import from `@bitacora/ui/components/ui/<name>` (and Animate UI / Bencho where the approved contracts name them);
pictures-only behaviour (bilingual labels from the SP-8/SP-10 dictionaries, focus return) stays in pictures as thin
composition over the pool component, never as a modified copy. Switch every importer (≈38 files on origin/main). Bencho blocks go
inside `<div className="bencho">`. Done when: no importer of the old files remains (`rg "components/ui/(checkbox|
select|tabs|tooltip|Ayuda|interruptor-tema|foco-retorno)" src` empty) and the affected UI tests pass.

## 5. Replace the shell (T: `src/components/ui/shell/*`)
CabeceraApp, MenuApp, HojaSeleccion, Compositor, … rebuilt from pool primitives (sheet, dropdown-menu, sidebar,
navigation-menu, …), keeping the account menu, plan links and language switch exactly as the approved contracts
(cuentas-admin@v2, planes@v2, …) state. Implementers START FROM the approved TSX when the contract has one
(`design/<ref>/approved.tsx`). Done when: shell UI tests + visual review against the contracts pass.

## 6. Tests and guards (T: test)
- Full existing UI regression (accounts, plans, language, Taller panels, chat tools) + `npm run build` +
  production smoke over signed-in entry points, ES and EN, light and dark.
- Add one guard test in pictures: no file under `src/` re-declares a component the pool exports (by name under
  `src/components/ui/`) and nothing edits `packages/bitacora-ui/` (its tree must equal `SYNC.json`'s digest — the
  sync owns it).
Done when: all green; evidence in the subplan's `## Pruebas` row (D-131).

## 7. Remove the duplicates and close (T: cleanup + audit)
Delete the replaced files (`src/components/ui/{checkbox,select,tabs,tooltip}.tsx`, `Ayuda.tsx`,
`interruptor-tema.tsx`, `foco-retorno.ts`, `shell/*` replaced in step 5) and pictures' now-unused dependencies
(e.g. `clsx`/`tailwind-merge` only if nothing else imports them). Decide with the owner whether
`src/components/ui/reactbits/*` and `icon-button.css` move to the pool (then delete) or stay. Independent audit: no
duplicate component, sync pinned (`SYNC.json` = current pool), theme fidelity, no regression.

## Open points for the owner
1. Is the subplan cuttable before the pilot if late, or never-cut?
2. `reactbits/*` and `icon-button.css`: into the pool or stay in pictures?
3. `push` of the sync commit to `origin/main` (default off).
