---
req: REQ-004
status: done
created: 2026-10-11
---
# Plan — REQ-004 — Proposal Studio visual system and motion

## Approach
Keep Astro as the primary framework. Add Starwind UI as the separately requested Astro-native component library and add only the button/card/badge source needed by the proposal and admin overview. Add one React integration island using a MIT-licensed 21st.dev Spotlight component for finding cards, and use Motion's small HTML API for page-section reveals. Preserve server-rendered content, existing comparison behavior, product colors, and reduced-motion accessibility.

## Global constraints
- Touch only public proposal presentation and the main admin overview; preserve existing features and form behavior.
- Spanish UI; retain Catppuccin Mocha mauve/lavender palette.
- Keep the iframe and comparison pointer interaction unchanged.
- No autoplay, WebGL, or hidden content requiring JavaScript.
- Preserve the user's two existing unstaged changes in `editor-client.ts` and `admin-proposal-workflow.spec.ts`.
- No prospect email or production notification changes.

## Tasks
- [x] T1 — Confirm library and animation compatibility and record the visual-system decision · files: REQ-004/SPEC.md, REQ-004/PLAN.md · verify: official Astro, Starwind UI, Motion and 21st.dev documentation · covers: R1–R7
- [x] T2 — Integrate Starwind, React, Motion, and 21st.dev source attribution · files: package.json, package-lock.json, astro.config.mjs, src/components/react/SpotlightCards.tsx, src/styles/starwind.css · verify: `npm run check` · covers: R2, R3, R7
- [x] T3 — Refine public proposal and comparison visual system using Starwind and 21st.dev Spotlight · files: src/pages/[slug].astro, src/components/ProposalComparison.astro, src/styles/global.css · after: T2 · verify: `npm run build` · covers: R1–R4, R6
- [x] T4 — Refine admin overview using themed Starwind components and motion · files: src/pages/admin/index.astro, src/styles/admin.css · after: T2 · verify: `npm run build` · covers: R5–R6
- [x] T5 — Verify responsive, comparison, accessibility, motion preferences, and complete quality suite; update project memory · files: e2e/proposal-viewer.spec.ts, e2e/admin-proposal-workflow.spec.ts, bitácora · after: T3, T4 · verify: full quality suite below · covers: R1–R7

## Verification
- Run Astro check, ESLint, Prettier check, Vitest, Astro production build, and Playwright E2E.
- Inspect screenshots of the public proposal and admin dashboard at desktop and mobile sizes, including reduced-motion mode.
- Confirm the public comparison's pointer and keyboard interaction and the prototype iframe are unchanged.
- Run the Vercel runtime build verifier because the app uses SSR on Vercel.

## Rulings
- T2: Select Starwind UI rather than Web Awesome because Astro-native source components preserve the product rendering model and avoid custom-element hydration for its shared UI. Add Tailwind v4 alongside existing CSS without replacing it.
- T2: Integrate React only for a single 21st.dev-derived Spotlight island; Astro remains responsible for all other screens.
- T3: Keep transition entrances short and nonessential; server-rendered content is visible before hydration.

## Progress log
- 2026-10-11: Explored current Astro UI and dependency graph; identified clean public/admin boundaries and preserved unrelated editor validation changes.
- 2026-10-11: Researched official library docs; chose Starwind UI, Motion, and 21st.dev Spotlight (MIT).
- 2026-10-11: Recorded assumed Round 1 recommendations under David's blanket authorization to proceed autonomously.
- 2026-10-11 13:05 plan APPROVED (terminal)
- 2026-10-11: Implemented Starwind UI Button/Card/Badge source components, one 21st.dev Spotlight React island, and Motion entry reveals. Added browser assertions for reduced motion, comparison interaction, mobile overflow, and admin component use. All checks passed as recorded in the session log.

- 2026-10-11: Final route audit found the real prospect URL is `/s/[token]`; applied the same Starwind, Spotlight, and Motion presentation there and extended the authenticated share workflow E2E assertions. Production deploy `dpl_7uE9nLRXy448y9Q2nJcY7KJfJT6d` is READY. Smoke checks: `/` 200, `/login` 200, anonymous `/admin` 302, anonymous `/api/admin/proposals` 401. The authenticated production share flow was not mutated for QA; the share route is covered by the local E2E workflow.
- 2026-10-11 final audit: verified a production QA share end to end: Starwind card and badge present, one Spotlight card hydrated, Motion enabled, proposal content visible; revoked token returned 404; archived proposal left 0 active proposals and no QA slug. Full suite re-run passed: 113-file Astro check (0 diagnostics), lint, format, 85 Vitest tests, 9 Chromium E2E, Astro build, Vercel runtime import, and 0 production dependency vulnerabilities.
- 2026-10-11 persistence and latest-deploy audit: committed and pushed source as `abab5c9` on `feat/proposal-comparison`; production deployment `dpl_Ed7uyJjvtnxgGbwQSyXvud8skRkc` is READY. A fresh production QA share confirmed the accessible named summary region plus Starwind, one Spotlight card, Motion, and visible content; revocation returned 404, archival succeeded, and authenticated proposals API reported 0 active rows / no QA slug. Latest checks: 85 Vitest tests, 10 Chromium E2E tests, Astro production build, and Vercel runtime build passed.
- 2026-10-11: audited the original Material 3-inspired admin requirement against the production UI, found the create-proposal CTA wrapped at a compact desktop width, and fixed it in T11 under REQ-003. Latest full checks pass with 11 Chromium E2E tests; deployment `dpl_25cmW7m9EKumzLVxNjpq7kFg5mm4` confirms the CTA stays on one line without overflow.
