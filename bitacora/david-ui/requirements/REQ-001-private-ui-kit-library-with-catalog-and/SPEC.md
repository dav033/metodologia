---
id: REQ-001
status: clarifying
created: 2026-10-22
track: deep
---
# REQ-001 — Personal UI kit package with a public catalog

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

Source inventory (owner's document v4, Spanish, authoritative for the component list, overlaps and per-source rules):
[SOURCE-INVENTORY.md](SOURCE-INVENTORY.md). Section numbers `§N` below refer to it.

Redirected by the owner on 2026-10-26 (D-003): an npm package plus a public catalog that consumes it, replacing the
shadcn registry, owner login, bearer tokens and Netlify of D-001.

## Problem & goal
David builds several React projects (maros, pictures, dav033-demos, proposal-studio, lotm, trainingapp…) and each one
assembles its UI from shadcn/ui, Animate UI and React Bits ad hoc, so every project looks and behaves differently and
agents re-pick components every time. Goal: **one reusable React component package for personal use** ("david-ui",
published as `@dav033/david-ui`) with a single visual identity and a high standard of interactivity and feedback, plus
a **public web catalog** that only shows the components with real demos and is itself built with the same package.
There is no commercial side.

**Success looks like:**
- With a `read:packages` token in `.npmrc`, `npm install @dav033/david-ui` into a fresh Next.js 16 + Tailwind 4 app,
  importing any `implemented`/`validated` entry and the theme stylesheet, builds without edits and renders styled.
- All 93 candidate entries of the inventory (42 shadcn + 7 Animate UI capabilities + 12 Bencho + 32 React Bits Free)
  and the 22 Animate UI enhancements end in a verified, recorded state (none left `pending`).
- The catalog application is built 100 % from the package (enforced by an automated check) and is publicly reachable on
  Vercel without login.
- `npm run verify` and `npm run test:e2e` pass at the repository root.

## Users / actors / stakeholders
- **Owner (David):** installs the package in his projects, browses the catalog, approves entries.
- **Coding agents (Claude Code, Codex):** discover components through the agent index (in the package and on the
  catalog) and install the package.
- **Catalog visitors:** anyone with the URL; the catalog is read-only and has no accounts.

## Scope (in)

### US-1 (P1, Must) — Package foundation
As the owner, I want one public monorepo whose package carries tokens, theme, motion profiles and tooling so that every
component shares one identity.
**Acceptance:**
- Given the repo, when `npm run verify` runs at the root, then lint, typecheck, unit tests, the kit-only check, the
  catalog check, the package build and the catalog production build all pass.
- Given any component, when the theme switches light/dark or the motion profile switches subtle/natural/expressive,
  then its colors, radii, shadows and motion timings come from the shared tokens.

### US-2 (P1, Must) — Catalog manifest and license register
As the owner, I want every inventory entry recorded with its metadata so that nothing is double-counted or forgotten.
**Acceptance:**
- Given the manifest, when the catalog check runs, then among entries with `origin: inventory` it finds exactly
  42 shadcn (30 P1 + 12 P2), 7 Animate UI capabilities, 12 Bencho (6 new-capability + 6 variant) and 32 React Bits
  (9 text + 12 ui + 6 effects + 5 backgrounds) = 93, plus 22 Animate UI enhancements linked to existing shadcn entries;
  it fails on any other count, duplicate id or enhancement without a base entry. Entries with `origin: catalog-driven`
  or `origin: own` (R4) are listed separately and never counted in the 93.
- Given an entry with status `implemented` or `validated`, then it has upstream URL, upstream version/commit,
  incorporation date, license, dependency/version-compatibility result and a demo; a clean-room entry
  (`own (inspired by <source>)`) records `upstream: n/a`, the consulted URL and date and a license-review note instead;
  a `blocked`/`discarded` entry has a written reason.

### Status semantics
- `pending` — recorded, not yet attempted (allowed only before the entry's milestone ends).
- `implemented` — code in the package, demo and unit tests exist, the package builds and exports it; some R6 check is
  still failing and the reason is written in the entry.
- `validated` — every R6 check passes. This is the target status for every entry.
- `blocked` — cannot be delivered now (license, primitive family, dependency conflict); reason and unblock condition written.
- `discarded` — deliberately not delivered (redundant per §10.2/§11.6); reason written.
- Owner production approval (§10.4 "aprobarlos para producción") is a separate manifest flag `ownerApproved`
  (default `false`), set by the owner after delivery; it never blocks this requirement.

### US-3 (P1, Must) — Build, publish and consume the package
As the owner, I want the package versioned and published to GitHub Packages so that any of my projects installs it
like a normal npm dependency.
**Acceptance:**
- Given a merged changeset on `main`, when the release workflow runs, then GitHub Actions publishes a new semver
  version of `@dav033/david-ui` to GitHub Packages.
- Given a fresh Next.js 16 + Tailwind 4 app with a `read:packages` token, when it installs the published version, imports
  `@dav033/david-ui/theme.css` and one component, then `next build` passes and the component renders with the kit tokens
  (`scripts/consume-smoke.mjs`).

### US-4 (P1, Must) — 30 P1 shadcn components with their Animate UI enhancements
As the owner, I want the essential components (§3.1–3.6) working on Base UI with their motion enhancements so that new
projects can start from the package.
**Acceptance:**
- Given the P1 milestone is done, when `npm run catalog:check` runs, then all 30 P1 entries are `validated`,
  `implemented`, `blocked` or `discarded` (with reason), and the 15 P1-related enhancements have a result
  (`compatible`, `manual`, `blocked`, `discarded`); the P1 browser tests pass for every `validated` P1 entry.

### US-5 (P1, Must) — Public catalog built with the package
As the owner, I want a public web catalog with filters, search, live demos, states, light/dark, responsive viewport
preview, motion-profile switch and install/usage snippets, built only from the package.
**Acceptance:**
- Given any visitor, when browsing the catalog without logging in, then every R9 capability works
  (`e2e/catalog-browse.spec.ts`, `e2e/catalog-entry.spec.ts`), and `npm run check:kit-only` passes.
- Given the production URL on Vercel, then a read-only smoke confirms the home page, one entry page, `/llms.txt` and
  `/index.json` answer 200.

### US-6 (P2, Must) — 12 P2 shadcn components, remaining enhancements and 7 Animate UI capabilities (§3.7, §4, §5)
**Acceptance:**
- Given the milestone is done, then the 12 P2 entries and the 7 capabilities have a final status (not `pending`), all
  22 enhancements have a result, each capability records its exposure form (component, hook or variant), API summary
  and catalog location (§9), they appear in the catalog, and their browser tests pass for `validated` entries.

### US-7 (P2, Must) — 12 Bencho UI entries (§10), clean-room where the license forbids copying
**Acceptance:**
- Given the milestone is done, then the 12 Bencho entries have a final status and origin per R10, use the §10.3 names,
  satisfy every R12 rule that applies to them, appear in the catalog, and their browser tests pass (including
  keyboard/button alternatives and mobile-emulated scroll conflicts).

### US-8 (P2, Must) — 32 React Bits Free entries (§11)
**Acceptance:**
- Given the milestone is done, then the 32 entries have a final status reached through the route chosen in their
  subplan (clean-room reimplementation or exclusion, R10), render without hydration warnings, respect reduced motion,
  backgrounds meet R13, and none of the repository's files contains copied React Bits code.

### US-9 (P2, Must) — Agent integration and final acceptance
As the owner, I want agents to discover and install kit components.
**Acceptance:**
- Given the published package, then it ships `AGENTS.md` and `llms.txt` generated from the manifest, and the catalog
  serves the same index at `/llms.txt` and `/index.json`.
- Given a fresh consuming app, when `scripts/acceptance.mjs` installs the latest version, then every `validated` entry
  imports and the app builds.

## Out of scope
- Migrating existing projects (maros, pictures, dav033-demos…) to the package — later requirements.
- Publishing to the public npm registry; any commercial use or sale.
- Login, accounts, analytics or any write feature in the catalog.
- React Bits Pro or any paid component; the real gaps (Comparison Slider, Device, Page Flip, AI Blob with states, §11.5)
  are documented, not implemented.
- Specialized editors (Notion-like, graph editors) (§7).
- Backends behind UI components (real file storage for Upload Dropzone, audio upload for Voice Note): UI + callbacks only.
- shadcn components listed in §3.8 unless the catalog app needs them (R4).
- React Bits `Count Up`, `Counter` and `Dock` (§11.6.1–2): not selected.
- The §11.5 own compositions "Modal Cards" and "Hover Preview": later; listed on the catalog gaps page with the real
  gaps.

## Requirements
- R1. The kit shall live in a new **public** GitHub repository `dav033/david-ui` (local `~/dev/david-ui`), which stays
  public. It is an npm-workspaces monorepo: `packages/ui` is the package `@dav033/david-ui`, `apps/catalog` is the Next.js
  catalog, which depends on the package through the workspace (always the current source, no publish round-trip).
- R2. The kit shall use Base UI as its single primitive family; where Animate UI has no Base UI variant, the
  enhancement shall be integrated by hand on the Base UI component (result `manual`) or recorded `blocked` with a reason.
- R3. Every component shall read colors, typography, spacing, radii and shadows from shared CSS tokens, and functional
  controls (shadcn, Animate UI, Bencho) shall also take motion timings from the active profile; React Bits graphic
  effects take tints, sizes and fonts from tokens but keep their own physics (§11.6.8). The default theme shall be
  Catppuccin Latte (light) / Mocha (dark) with mauve accent, replaceable per consuming project by overriding tokens.
- R4. The catalog application shall be built only from package components: when it needs a UI piece the package lacks,
  the executor shall add it to the package — first from shadcn/ui (recorded as a catalog-driven addition), and only if no
  shadcn component exists as an own component with motion — and use it from there in the same change; an automated
  check (`npm run check:kit-only`) shall fail when `apps/catalog` imports UI primitives/animation libraries directly or
  renders raw interactive HTML elements (`button`, `input`, `select`, `textarea`, `dialog`, `a` styled as button).
- R5. The catalog manifest shall record every entry with id (kebab-case of the name; §10.3 names for Bencho, e.g.
  `seek` → `expanding-search`, `liq-create` → `create-menu`, `picker` → `picker-wheel`, `dock` → `magnifying-dock`),
  name, source, origin (`inventory`, `catalog-driven`, `own`), category, priority (P1/P2: shadcn as listed; Alta → P1,
  Media → P2 for §5 and §11; Bencho P2) plus the raw source priority, type (`base` = shadcn, `capability` = Animate UI
  §5, `new-capability` / `variant` = Bencho §10.1, `presentation` = React Bits), exposure form (component, hook,
  variant, utility), import path, applicable states, status (`pending`, `implemented`, `validated`, `blocked`,
  `discarded`), upstream URL and version/commit, license, dependencies, public API summary, a11y and reduced-motion
  results, and demo path; the 22 enhancements shall be linked to their base entry with a test result
  (`compatible`, `manual`, `blocked`, `discarded`) and never counted as entries.
- R6. When an entry is marked `validated`, it shall have a live catalog demo with every state in its `applicableStates`
  (from hover, focus-visible, pressed, disabled, loading, success, error), keyboard operation where interactive, no axe
  violations, respected `prefers-reduced-motion`, no hydration warnings under SSR, unit tests for its behavior (for
  text effects and backgrounds: render, prop and reduced-motion/fallback tests) and an export of the built package that
  a fresh app imports and builds.
- R7. Each interactive control shall offer keyboard and touch operation; hover, drag or cursor proximity shall never be
  the only way to operate it (§11.6.7, §10.2).
- R8. The kit shall expose three motion profiles (subtle, natural default, expressive) through a provider; animations
  shall prefer `transform`/`opacity`, be interruptible, and collapse to instant/opacity-only under reduced motion.
- R9. The catalog shall offer: browse and filter by source, category, priority, status and type; command-palette search;
  an entry page with live demo, states gallery, props/API table, import/usage snippet, origin/license/version,
  light/dark toggle, viewport preview (mobile/tablet/desktop) and motion-profile switch; a gaps page listing the
  documented gaps (§11.5) and every `blocked`/`discarded` entry with its reason. Each component family milestone adds
  its entries to the catalog in the same milestone.
- R10. Because the repository and the package source are public, code shall be copied from a source only when its
  license permits redistributing it in a public package; the license is recorded in the license register before any
  copy. Otherwise (Bencho if unclear, React Bits Free whose Commons Clause forbids redistributing the components "alone,
  in a bundle, or as a ported version") the entry is reimplemented clean-room (behavior from the public description/demo,
  no copied code, origin `own (inspired by <source>)`) or excluded with a written reason; the React Bits route is decided
  when its subplan is in focus. Copied files keep their upstream license notice in a header comment (checked by
  `catalog:check`). Upstream updates are deliberate: the manifest records upstream version and incorporation date, and
  an update re-diffs upstream against the local adaptation (procedure in the repo `AGENTS.md`).
- R11. Notifications shall have exactly one engine (Sonner unless the compatibility spike rules otherwise, recorded in
  DECISIONS); Animate UI motion and Bencho Toast Stack shall be presentations on top of it (§10.2.1).
- R12. Overlapping entries shall keep one value model, each rule covered by a unit or e2e test:
  `RollingNumberInput` is an editable input and `CountingNumber` a passive display, with distinct APIs; `PickerWheel`
  emits the same value contract as `Select`; `SloshSlider` shares `value`/`onValueChange`, min/max/step and keyboard
  behavior with `Slider`; `Checklist` uses the `Checkbox` boolean model; card variants compose `Card`; `CreateMenu` and
  `ExpandingSearch` keep focus management and keyboard operation; `SlideToConfirm` only emits a confirm intent (never
  replaces server validation) and has a button/keyboard alternative; `MagnifyingDock` works by focus and touch.
- R13. WebGL/canvas backgrounds and heavy effects shall be lazy-loaded, pause when off-screen or the tab is hidden, and
  render a static CSS fallback when WebGL is unavailable or reduced motion is set. With Playwright mobile emulation
  (Pixel 7 profile, 4× CPU throttling) each background shall sustain a median ≥ 30 FPS over 5 s, otherwise it ships
  with the static fallback as mobile default and the measurement recorded.
- R14. The catalog shall be public and read-only: no login, no accounts, no write endpoints.
- R15. The package shall ship an agent index (`AGENTS.md` and `llms.txt`) generated from the manifest, listing every
  entry with variants, origin, import path, version, dependencies, license and QA status plus a short consumption and
  theming guide; the catalog shall serve the same index at `/llms.txt` and `/index.json`.
- R16. The catalog shall be deployed to Vercel from the GitHub repository, project root `apps/catalog`.
- R17. Versions shall be managed with Changesets; when a changeset is merged to `main`, a GitHub Actions workflow shall
  build and publish the package to GitHub Packages with the workflow's `GITHUB_TOKEN` (`packages: write`).
- R18. The package shall be framework-agnostic React: `react`/`react-dom` 19 as peer dependencies, no dependency on
  Next.js, compiled ESM with type declarations, per-component subpath exports, and `"use client"` preserved on client
  components. Styles reach consumers through Tailwind 4: the package exports `theme.css` (tokens as `@theme`, Catppuccin
  default) and documents the `@source` line that makes the consumer's Tailwind scan the package's compiled files.

## Edge cases & errors
- Animate UI piece exists only for Radix → manual integration on Base UI or `blocked` (R2), never a mixed primitive family.
- Upstream install command fails or pulls conflicting deps (React/Tailwind/Motion versions) → pin, adapt or `blocked` with reason.
- Two sources implement the same thing → keep one per §10.2/§11.6; the other becomes a variant or `discarded` with reason.
- License unknown, ambiguous or forbidding redistribution → clean-room or exclusion (R10), noted in the register.
- Consumer without a `read:packages` token → `npm install` fails with 401; the README and `AGENTS.md` explain the
  `.npmrc` and the Vercel env var for consuming projects.
- Consumer forgets the `@source` line or `theme.css` → components render unstyled; the consumption smoke covers the
  documented setup and the guide states it as step one.
- Consumer on Next 15 (lotm) or without Next → the package has no Next dependency (R18); only Next 16 is tested.
- No WebGL / low-end device / reduced motion → static fallback (R13).
- SSR/hydration: client-only effects guarded; no hydration warnings in the catalog build.
- Pull to Refresh vs native scroll, Magnifying Dock on touch, Slide to Confirm without drag → button/keyboard alternative (R7).
- Voice Note uses real `getUserMedia`/`MediaRecorder` (no upload backend); without microphone permission → explicit
  denied state. Upload Dropzone over size/type → rejection state.
- Page Transition depends on the router and its version: validated only against the catalog's Next App Router; other
  routers are documented as untested.

## Constraints
- Monorepo with npm workspaces, npm, Node 24, TypeScript strict. Package: React 19 peer, Base UI, Motion (`motion`),
  Tailwind 4 tokens. Catalog: Next.js 16 App Router, React 19, Tailwind 4 (precedent: `~/dev/dav033-demos`).
- Base UI as the only primitive family; Motion for animation, CSS for simple transitions.
- Tests: Vitest + Testing Library (units), Playwright + `@axe-core/playwright` (e2e/a11y), including a reduced-motion run.
- Code, comments and identifiers in English; catalog UI copy in Spanish.
- The repository is public forever: no secrets and no code whose license forbids redistribution (R10). It carries no
  open-source license (all rights reserved, personal use). Agents commit directly to `main`; CI runs verify on every push.
- Working evidence (reports, screenshots) goes to the git-ignored `.evidence/` folder and is copied to
  `~/bitacora/david-ui/artifacts/REQ-001/`; findings ledgers `.evidence/*.findings.json` are tracked (verifier snapshots
  exclude ignored files).
- Production actions authorized globally by the owner (2026-10-19): creating the GitHub repository, pushing to `main`,
  publishing to GitHub Packages through Actions, Vercel deploys.

## Priorities & phases
Must, in order: package foundation, identity and publishing (US-1, US-2, US-3) → P1 components (US-4) → public catalog
on Vercel (US-5) → P2 + capabilities (US-6) → Bencho (US-7) → React Bits (US-8) → agent index and acceptance (US-9).
Each family milestone after the catalog adds its entries to the package and the catalog together. MVP = through US-5.

## Timeline & dependencies
- No deadline. Each milestone is independently verifiable and committable.
- US-5 depends on US-4 (the catalog is built with the P1 components). US-7/US-8 depend on the license register (US-2).

## Assumptions
- Repository `dav033/david-ui`, package `@dav033/david-ui` (GitHub Packages requires the owner scope).
- Default theme Catppuccin Latte/Mocha with mauve accent (confirmed 2026-10-26, round 1 Q5).
- Sonner is the notification engine unless the spike shows the Animate UI toast primitive is a better single engine.
- Bencho licenses are unknown; clean-room reimplementation applies to all 12 entries if public redistribution is not
  clearly permitted.
- Vercel project `david-ui` with the provider-assigned domain; no custom domain.
- FPS/memory are measured with Playwright mobile emulation and CPU throttling (R13), not on real low-end phones.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear (per-subplan detail when each subplan is in focus) |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear (no deadline) |

## Clarifications
### Round 1 — 2026-10-22 (superseded in part by D-003)
- Q: Scope of this requirement? → A: (a) all 93 entries, in milestones.
- Q: Project and repo name? → A: "ui kit david o algo así" → `david-ui`.
- Q: Distribution and hosting? → A: one Next.js app = catalog + shadcn registry on Netlify — **superseded 2026-10-26**.
- Q: Primitive family? → A: Base UI.
- Q: Source license forbids copying? → A: (a) clean-room reimplementation with documented origin.
- Owner addition: the whole catalog app must be built with the kit itself; a missing piece comes from shadcn, else an
  own animated component (R4).

### Owner redirection — 2026-10-26
- The kit is an npm package for personal use (no commercial side) plus a web catalog that only displays components,
  public, no login, on Vercel. Package first, then the web; the web uses the same package, and missing components are
  added and iterated along the way. GitHub and Vercel CLIs are already logged in.

### Round 1 (planning) — 2026-10-26
- Q: Where does the package live? → A: public GitHub repository for now (registry asked in round 2).
- Q: Repo layout? → A: (a) one monorepo, `packages/ui` + `apps/catalog` via workspace.
- Q: Milestone order? → A: (a) package foundation + P1 first, then the public catalog, then each family into package
  and catalog together.
- Q: Scope of this plan? → A: (a) all 93 entries + 22 enhancements, in milestones.
- Q: Keep the rest (Base UI, React 19, Tailwind 4, Motion, Catppuccin, 3 motion profiles, Spanish catalog, kit-only
  catalog, clean-room)? → A: yes, all.

### Round 2 (planning) — 2026-10-26
- Q: npm registry? → A: (a) GitHub Packages `@dav033/david-ui`, published by Actions; consumers use a `read:packages` token.
- Q: React Bits vs public repo (license forbids redistributing its components)? → A: the repository always stays
  public; clean-room or exclusion is decided when the React Bits subplan is in focus.
- Q: Styles for consumers? → A: (a) Tailwind 4 consumers; the package exports `theme.css` + documented `@source`.
- Q: Agent integration? → A: accepted: `AGENTS.md` + `llms.txt` in the package; `/llms.txt` and `/index.json` on the catalog.
- Lead rulings (owner did not object): Changesets for versioning; React-only package without a Next dependency.

### SP-1 — 2026-10-26
- Q: License of the public repository? → A: (a) none: all rights reserved, README states personal use; copied MIT code keeps its notice.
- Q: How do agents work on the repository? → A: (a) direct commits to `main`; a CI workflow runs `npm run verify` on every push.
- Lead rulings: per-file tsc build to ESM (keeps `"use client"`, per-component imports); the manifest lives in `packages/ui`.

## Pruebas

Where the owner can try each subplan once it is built (D-131). Rows for SP-2 and SP-4 name proposed routes that are
fixed when those subplans are defined.

| Subplan | Dónde | Cómo | Qué debes ver |
|---|---|---|---|
| SP-1 | Local (`~/dev/david-ui`) + GitHub https://github.com/dav033/david-ui | `git clone https://github.com/dav033/david-ui /tmp/dui && cd /tmp/dui && npm ci && npm run verify`; then `npm run build --workspaces && npm run dev -w apps/catalog` and open http://localhost:3000/api/health; open https://github.com/dav033/david-ui/actions | verify passes (lint, typecheck, unit tests, `check:kit-only`, `catalog:check` with 42/7/12/32 entries + 22 enhancements, builds); the health route answers 200 with the package's placeholder export; the repo is public, README says personal use / all rights reserved, no LICENSE file; the latest CI run on `main` is green |
| SP-2 | Local | `npm run test -w packages/ui`; `npm run build --workspaces && npm run dev -w apps/catalog` and open the identity preview route defined with SP-2 (proposed http://localhost:3000/preview/identity) | Catppuccin Latte/Mocha tokens with mauve accent; switching light/dark and subtle/natural/expressive changes colors and motion timings; with OS reduced motion on, transitions become instant/opacity-only |
| SP-3 | GitHub Packages https://github.com/dav033/david-ui/pkgs/npm/david-ui + Local fresh app | Merge a changeset to `main` and open https://github.com/dav033/david-ui/actions (Release run); in an empty folder: `npx create-next-app@16 consumer`, add `.npmrc` with `@dav033:registry=https://npm.pkg.github.com` and `//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}` (token with `read:packages`), `npm i @dav033/david-ui`, import `@dav033/david-ui/theme.css` + the documented `@source` line + one component, `npm run build && npm start`; or `node scripts/consume-smoke.mjs` | the Release run is green and the package page lists the new version; install and build pass; the component renders with kit tokens (mauve accent); without the token `npm i` fails with 401 |
| SP-4 | Local | `npm run test -w packages/ui`; `npm run catalog:check`; `npm run test:e2e`; `npm run build --workspaces && npm run dev -w apps/catalog` and open the P1 demo route defined with SP-4 (proposed http://localhost:3000/dev/p1) | the 30 P1 entries and 15 related enhancements have a final status (`validated`/`implemented`/`blocked`/`discarded` with reason); each validated component works with keyboard and touch, shows its states and respects reduced motion |
| SP-5 | Local | `npm run build --workspaces && npm run dev -w apps/catalog`, open http://localhost:3000, http://localhost:3000/llms.txt and http://localhost:3000/index.json | no login; filters by source/category/priority/status/type, command-palette search, entry page with live demo, states gallery, props table, usage snippet, origin/license/version, light/dark, viewport preview and motion-profile switch; gaps page; the agent index answers on both routes |
| SP-6 | Producción — Vercel https://david-ui.vercel.app (provider-assigned; exact URL recorded by SP-6) | Open the URL in a private window; open one entry page, `/llms.txt` and `/index.json`; `curl -I <url>/index.json`; check the Vercel dashboard deployment | every page answers 200 without login; the deployment comes from the latest `main` commit of dav033/david-ui with root `apps/catalog` |
| SP-7 | Producción — Vercel https://david-ui.vercel.app (provider-assigned; exact URL recorded by SP-6) + GitHub Packages | In the catalog filter priority P2 and type capability; open enhanced base entries; check the new package version on https://github.com/dav033/david-ui/pkgs/npm/david-ui | 12 P2 entries and 7 capabilities listed with final status, exposure form and API; all 22 enhancements show a result on their base entries; a new package version is published |
| SP-8 | Producción — Vercel https://david-ui.vercel.app (provider-assigned; exact URL recorded by SP-6) | Filter source Bencho; open Slide to Confirm, Magnifying Dock, Picker Wheel and Pull to Refresh; use only the keyboard, then the mobile viewport preview | 12 entries with final status and origin (`own (inspired by Bencho)` when clean-room); every gesture has a button/keyboard alternative; Picker Wheel and Select share the value contract (R12) |
| SP-9 | Producción — Vercel https://david-ui.vercel.app (provider-assigned; exact URL recorded by SP-6) + GitHub https://github.com/dav033/david-ui | Filter source React Bits; open the gaps page; open a background with OS reduced motion on and in the mobile viewport; search the repo for React Bits copyright notices | each of the 32 entries is delivered clean-room or listed as excluded with its reason; backgrounds show the static fallback under reduced motion; no copied React Bits code in the repository |
| SP-10 | Local + GitHub Packages + Producción — Vercel https://david-ui.vercel.app (provider-assigned; exact URL recorded by SP-6) | `node scripts/acceptance.mjs`; open `<url>/llms.txt`; in a consumer app `ls node_modules/@dav033/david-ui` after install | the acceptance script installs the latest version and builds every validated entry; `llms.txt`, `/index.json` and the package's `AGENTS.md`/`llms.txt` list every entry with import path, origin, license and QA status |

## Inputs

Rewritten 2026-10-26 for D-003; the Netlify, login-secret and private-repository inputs of revisions 1–10 no longer
apply. Locations only, never values. Empty Subplan = plan-wide.

| Item | Subplan | Where it lives | Supplier | Status |
|---|---|---|---|---|
| Scope, inventory and naming | | SPEC.md, SOURCE-INVENTORY.md | Owner | available |
| GitHub account with repo and workflow scopes | SP-1 | `gh` CLI logged in as dav033 (scopes repo, workflow, delete_repo); `dav033/david-ui` does not exist (checked 2026-10-26) | Owner | available |
| Package publish credential | SP-3 | GitHub Actions `GITHUB_TOKEN` with `packages: write`, set in the release workflow | GitHub | available |
| Read token for the local consumption smoke | SP-3 | `gh` token after `gh auth refresh -s read:packages`, or a classic PAT with `read:packages` in `~/.npmrc` | Owner | pending: asked when SP-3 is in focus |
| Vercel account | SP-6 | `vercel` CLI logged in as dav033 | Owner | available |
| Vercel ↔ GitHub access to `dav033/david-ui` | SP-6 | Vercel GitHub integration, or fallback `vercel deploy --prod` from the checkout | Owner | pending: asked when SP-6 is in focus |
| Verification policy for the read-only production smoke | SP-6 | `~/bitacora/david-ui/verification-policy.json` (operator file) | Owner | pending: asked when SP-6 is in focus |
| Fixtures and local runtime | | Synthetic component data and disposable consumer apps authored by their tasks; no database, paid service or SSH host | Implementer | available |
| Artifact storage | | `.evidence/` (git-ignored); `~/bitacora/david-ui/artifacts/REQ-001/` | Plan | location given |
