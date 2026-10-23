---
req: REQ-001
status: launched
created: 2026-10-22
---
# Plan — Private UI kit library with catalog and registry

<!-- bitacora:status:begin -->
> Bloque generado, no editar a mano. Plan: launched · ejecución: running · hitos 4/7 · tareas 18/27 · generado: 2026-10-23T09:30:52-05:00

**M1 — Foundation: repo, tokens, manifest, licenses, registry pipeline** · dificultad alta · 6/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T1 | Scaffold `~/dev/david-ui`: Next 16 + TS strict + Tailwind 4 + shadcn init (Base UI style) + ESLint/Prettier + Vitest/Testing Library + Playwright/axe; scripts `verify`, `test`, `test:e2e`; `.gitignore` incl. `.evidence/`; `.env.example`; create private GitHub repo `dav033/david-ui` and push | alta | completada | sonnet | claude-work | 4 |
| T2 | Compatibility and license spike: per each of the 22 enhancements and 7 capabilities, whether Animate UI ships a Base UI variant and its install path; Motion/React/Tailwind version matrix; Sonner vs Animate UI toast as single engine; licenses of shadcn, Animate UI, Bencho (per block) and React Bits; write `.evidence/T2-spike.md` and record the toast-engine and primitive rulings | alta | completada | sonnet | claude-work | 1 |
| T3 | Design tokens and motion: `registry/david-ui/styles/tokens.css` (Catppuccin Latte/Mocha, mauve accent, radii, shadows, typography, spacing, motion durations/easings for subtle/natural/expressive), `ThemeProvider`, `MotionProfileProvider` (Motion `MotionConfig` + reduced motion), `useMotionProfile`; registry items for them | alta | completada | sonnet | claude-work | 1 |
| T4 | Catalog manifest and license register: zod schema (R5), `catalog/entries.ts` with all 93 entries `pending` and the 22 enhancements linked to base entries, `catalog/licenses.ts` from T2, `npm run catalog:check` asserting counts, unique ids, base links and status/metadata rules | alta | completada | sonnet | claude-work | 1 |
| T5 | Registry pipeline: `registry.json` generated from the manifest, `npm run registry:build` (`shadcn build` → `public/r/`), proof item `button`; integration script `scripts/registry-smoke.mjs` that creates a scratch Next app in a temp dir, installs `@david-ui/button` from a locally served registry and builds it | alta | completada | sonnet | claude-work | 4 |
| T6 | Kit-only guard: ESLint `no-restricted-imports` outside `registry/` + `scripts/check-kit-only.ts` (forbidden imports and raw interactive JSX in `src/app`, `src/components`), with a test that plants violations | media | completada | gpt-6-luna | codex-2 | 1 |

**M2 — 30 P1 shadcn components with their Animate UI enhancements** · dificultad alta · 5/5

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T7 | Structure + forms: Button (+ variants), Card, Badge, Avatar, Field, Input, Textarea, Select*, Checkbox*, Switch*, Combobox* (* = Animate UI enhancement), demos with all states, manifest updated | alta | completada | sonnet | claude-work | 1 |
| T8 | Navigation: Sidebar* (manual), Tabs*, Dropdown Menu*, Breadcrumb, Pagination* (manual) | alta | completada | gpt-6-luna | codex-1 | 2 |
| T9 | Overlays and disclosure: Dialog*, Alert Dialog*, Sheet*, Popover*, Tooltip*, Accordion* | alta | completada | gpt-6-luna | codex-2 | 1 |
| T10 | Feedback and data: Alert, Toast/Sonner* (single engine per T2, R11), Skeleton, Spinner, Empty, Table, Data Table (composition API: filter, sort, select, paginate), Chart | alta | completada | gpt-6-luna | codex-1 | 3 |
| T11 | P1 e2e and a11y suite: Playwright spec that opens every P1 demo, runs axe, exercises keyboard paths and repeats under `reducedMotion: 'reduce'`; promote passing entries to `validated` | alta | completada | gpt-6-luna | codex-luis | 1 |

**M3 — Private catalog application built with the kit** · dificultad alta · 3/3

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T12 | Catalog shell and browse: layout with kit Sidebar/Breadcrumb, home grid of entries, filters (source, category, priority, status, type), command-palette search (adds `Command` and any shadcn piece needed, e.g. Toggle Group, as catalog-driven additions), theme toggle | alta | completada | gpt-6-luna | codex-luis | 1 |
| T13 | Entry page: live demo, states gallery, props/API table generated from manifest, install command with Copy Button, origin/license/version panel, viewport preview (mobile/tablet/desktop iframe), motion-profile switch; code-block component created as own animated entry if shadcn has none | alta | completada | gpt-6-luna | codex-luis | 1 |
| T14 | Privacy: owner login page (kit form components), signed HttpOnly session cookie, `proxy.ts` guard for pages, bearer-token guard for `/r/*` (401 without leaking source), `components.json` consumption example with `${DAVID_UI_REGISTRY_TOKEN}` headers | alta | completada | gpt-6-luna | codex-luis | 1 |

**M4 — P2 components, remaining enhancements and the 7 Animate UI capabilities** · dificultad alta · 2/2

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T15 | P2: Calendar, Date Picker, Input Group, Radio Group*, Command (finalize), Navigation Menu*, Drawer*, Collapsible*, Scroll Area, Progress*, Slider*, Hover Card*; demos, unit tests, e2e + axe, manifest | alta | completada | gpt-6-luna | codex-1 | 1 |
| T16 | Capabilities: Animated Button (Button variant), CopyButton, Animated Icons kit, CountingNumber, AutoHeight, ScrollFade (Scroll Area option), PageTransition (validated with the Next App Router of the catalog) | alta | completada | gpt-6-luna | codex-2 | 1 |

**M5 — Bencho UI (12)** · dificultad alta · 0/2

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T17 | New capabilities: RollingNumberInput, VoiceNote (UI + callbacks, permission-denied state), UploadDropzone (size/type rejection, no backend), SlideToConfirm (keyboard/button alternative), MagnifyingDock (focus and touch), PullToRefresh (button alternative, scroll conflicts) | alta | en curso | gpt-6-luna | codex-2 | 4 |
| T18 | Variants: ToastStack presenter (on the T10 engine), PickerWheel, Checklist, CreateMenu, ExpandingSearch, SloshSlider (Slider value model) | alta | pendiente | — | — | 0 |

**M6 — React Bits Free (32)** · dificultad alta · 2/3

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T19 | Text (9): Blur Text, Decrypted Text, Text Type, Shuffle, True Focus, Text Pressure, Variable Proximity, Scroll Velocity, Split Text | alta | completada | gpt-6-luna | codex-2 | 1 |
| T20 | UI, navigation and galleries (12): Animated List, Scroll Stack, Magic Bento, Circular Gallery, Masonry, Tilted Card, Spotlight Card, Card Swap, Stack, Gooey Nav, Staggered Menu, Stepper (card variants on top of Card, R12) | alta | completada | gpt-6-luna | codex-2 | 1 |
| T21 | Interaction effects (6) and backgrounds (5): Pixel Transition, Electric Border, Animated Content, Magnet, Click Spark, Glare Hover; Aurora, Dot Grid, Orb, Silk, Iridescence with lazy loading, off-screen pause, static fallback; Playwright run with WebGL disabled and CPU throttling recording FPS evidence | alta | en curso | gpt-6-luna | codex-2 | 2 |

**M7 — Agent index, deployment and acceptance** · dificultad alta · 0/6

| Tarea | Título | Dificultad | Estado | Modelo | Cuenta | Intentos |
|---|---|---|---|---|---|---|
| T22 | Agent integration: generate `/r/index.json` and `/llms.txt` from the manifest; write repo `AGENTS.md` + `CLAUDE.md` (how to pick and install components, kit-only rule, statuses); consumption guide for other projects; entry in `~/dev/cerebro` global notes | alta | pendiente | — | — | 0 |
| T23 | Deploy: Netlify site linked to `dav033/david-ui`, env vars set, production build; smoke: login works, protected page redirects, `/r/button.json` 401 without token and 200 with it | alta | pendiente | — | — | 0 |
| T24 | Build end-to-end acceptance harness: production Next server, login and catalog flow, token-protected registry installs into scratch Next apps, final catalog checks | alta | pendiente | — | — | 0 |
| T24a | Execute the shipped production entry points and full acceptance matrix; report actual results without changing code or judging product acceptance | media | pendiente | — | — | 0 |
| T25 | Independent audit of the whole requirement against SPEC R1–R16 and the inventory rules (§6, §10.2, §11.6): read-only review, findings ledger | alta | pendiente | — | — | 0 |
| T25b | Cross-check audit of T25: Independent audit of the whole requirement against SPEC R1–R16 and the inventory rules (§6, §10.2, §11.6): read-only review, findings ledger | alta | pendiente | — | — | 0 |
<!-- bitacora:status:end -->

## Approach
Greenfield repo `~/dev/david-ui` (private GitHub `dav033/david-ui`): one Next.js 16 app that is both the private catalog
and a shadcn registry. Component sources live in `registry/david-ui/<category>/<name>/` and are built with
`shadcn build` into `public/r/*.json` (namespace `@david-ui`). A typed catalog manifest (`catalog/entries.ts`, zod, assembling task-owned metadata fragments) is
the single source of truth for the 93 entries, the 22 enhancements, their status and licenses; the gallery, the agent
index and the registry metadata are all generated from it. Base UI is the only primitive family; Motion drives
animation through a motion-profile provider over CSS tokens (Catppuccin Latte/Mocha, mauve accent). The catalog app is
built only from kit components, enforced by `npm run check:kit-only` (R4). Work goes source by source, in the order of
the inventory: foundation → P1 → catalog app → P2 + capabilities → Bencho → React Bits → agents + deploy + acceptance.
A compatibility and license spike (T2) runs first because every later status depends on it.

## Global constraints
- Next.js 16 App Router, React 19, TypeScript strict, Tailwind 4, npm, Node 24; Base UI only (R2); Motion for animation.
- The final `npm run verify` pipeline includes lint, typecheck, unit tests, `check:kit-only`, `catalog:check`,
  `registry:build` and `build`. Bootstrap tasks run their available local checks; the full pipeline first runs at T7,
  after T3–T6 have authored its prerequisites. Every component producer owns its unit tests and demo; no missing check is reported as passing.
- Kit-only rule (R4): app code outside `registry/` never imports `@base-ui/react`, `motion`, Radix or upstream kits and
  never renders raw interactive HTML. Missing piece → add from shadcn (catalog-driven addition) → else own animated component.
- Before copying code from a source, its license is in `catalog/licenses.ts` (R10); unknown/forbidding → clean-room.
- An entry may be set `validated` only when R6 holds; otherwise `implemented`, `blocked` or `discarded` with a reason.
  Never leave an entry `pending` at the end of its milestone.
- Tokens only (R3); keyboard/touch alternative for every gesture (R7); reduced motion respected (R8).
- Catalog copy in Spanish; code, comments, identifiers and commits in English.
- No secrets in the repo; `.env.example` lists `DAVID_UI_PASSWORD`, `DAVID_UI_SESSION_SECRET`, `DAVID_UI_REGISTRY_TOKEN`.
- Evidence, reports and findings ledgers go to the git-ignored `.evidence/` and are copied to
  `~/bitacora/david-ui/artifacts/REQ-001/`.
- Owner-authorized production actions (2026-10-19): create the private GitHub repo `dav033/david-ui`, push to `main`,
  deploy to Netlify. Nothing is published publicly.

## Classification basis and readiness

This update preserves the approved product scope: the same 93 candidates, 22 enhancements, catalog, private registry,
agent integration and Netlify deployment. It does not approve, freeze or launch anything. PLAN.json already existed;
`plan-json init` was not run. Status/frontmatter and revision remain unchanged.

Observed: the checkout contains only .git, has no commits and no package.json, application code, tests, CI or env
example. project.json declares app and no guards. Therefore no future npm/Playwright command was executed or claimed
as existing evidence. Each planned command names its producing task through created_by. The executable node/npm/gh/
netlify tools exist; service sessions are located by TOOLS.md, not re-authenticated here. Private Planner resources
(socratic elicitation, WBS, Mermaid projection and adversarial review), the contract, schema and validator code were read.
SPEC, the full source inventory, existing PLAN files, project.json, shared tools, decisions and global brain were inspected.
There is no david-ui brain index. No external source/license assertion has been newly verified; T2 remains responsible.

Input inventory and the outstanding secrets-location question are recorded in SPEC Inputs. The classified contract may
validate structurally while these execution inputs remain unresolved; structural validity is not readiness or approval.

History was queried for implement, research, test and audit. Every response was status unknown: duration unit seconds,
source quality unknown, no verified comparable sample count/range/median; retries/quality/consumption also unknown.
The integer minute estimates below are provisional task breakdowns, including owned harness creation and local checks,
not history-calibrated performance or limits. No provider, account, model, effort or execution assignment is selected.
T2 is the bounded investigation before compatibility-dependent implementation; blocked/clean-room outcomes are explicit
approved routes, so no later task needs an owner decision about a missing upstream variant or ambiguous license.

## File ownership and execution contracts

The following map lists every declared changed path before the tasks. A directory entry owns its descendants; later
tasks import it. If an audit finds a defect in an earlier owner's file, that owner is reworked rather than assigning
an opportunistic edit to the later task. Generated public/r and llms outputs are artifacts of the owning build scripts,
not independently maintained sources. External notes/evidence use the approved existing paths, never a new brain layout.

| Owner | Paths to create or modify | Single responsibility |
|---|---|---|
| T1 | `package.json`, `package-lock.json`, `tsconfig.json`, `components.json`, `next.config.ts`, `eslint.config.mjs`, `vitest.config.mts`, `playwright.config.ts`, `.env.example`, `.gitignore`, `src/app/layout.tsx`, `src/app/not-found.tsx`, `scripts/check-spike.mjs`, `scripts/check-audit-ledger.mjs`, `scripts/check-planning-tools.test.ts` | A private greenfield checkout has the approved toolchain and named package scripts ready for the later producers, plus fail-closed report validators. |
| T2 | `.evidence/T2-spike.md`, `.evidence/T2-spike.json` | A reproducible compatibility matrix and license record give every enhancement and capability a supported route or an explicit blocked result before source adoption. |
| T3 | `registry/david-ui/styles/tokens.css`, `registry/david-ui/lib/theme-provider.tsx`, `registry/david-ui/lib/motion-profile.tsx`, `registry/david-ui/lib/motion-profile.test.tsx` | Consumers share one theme and motion contract, including a natural default and an overriding reduced-motion policy. |
| T4 | `catalog/schema.ts`, `catalog/entries.ts`, `catalog/licenses.ts`, `catalog/check.ts`, `catalog/check.test.ts` | One validated aggregate exposes the 93 inventory candidates and 22 linked enhancements, with deterministic owned metadata updates and license provenance. |
| T5 | `registry.json`, `scripts/build-registry.ts`, `scripts/registry-smoke.mjs`, `registry/david-ui/structure/button.tsx` | The generated shadcn registry installs its Button proof and dependencies into a fresh Next application that builds. |
| T6 | `scripts/check-kit-only.ts`, `scripts/check-kit-only.test.ts` | The kit-only guard rejects forbidden primitive imports and raw interactive JSX while accepting kit consumers. |
| T7 | `registry/david-ui/structure/card.tsx`, `registry/david-ui/structure/badge.tsx`, `registry/david-ui/structure/avatar.tsx`, `registry/david-ui/structure/button-variants.tsx`, `registry/david-ui/structure/button.test.tsx`, `registry/david-ui/forms`, `src/demos/structure`, `src/demos/forms`, `catalog/updates/p1-structure-forms.ts` | The eleven structure/form candidates and their linked enhancements have tokenized demos, behavior tests and recorded implementation outcomes. |
| T8 | `registry/david-ui/navigation`, `src/demos/navigation`, `catalog/updates/p1-navigation.ts` | The five navigation candidates keep keyboard and touch navigation intact through their approved animation enhancements. |
| T9 | `registry/david-ui/overlays`, `src/demos/overlays`, `catalog/updates/p1-overlays.ts` | The six overlay/disclosure candidates preserve focus return, dismissal and keyboard operation during animated transitions. |
| T10 | `registry/david-ui/feedback`, `registry/david-ui/data`, `src/demos/feedback`, `src/demos/data`, `catalog/updates/p1-feedback-data.ts` | The nine feedback/data candidates provide tested feedback states and composable data operations on one notification engine. |
| T11 | `e2e/p1.spec.ts`, `e2e/helpers.ts`, `src/app/demos/[...slug]/page.tsx`, `catalog/qa/p1.ts` | A real P1 demo route and browser suite establish the exact evidence required before any P1 entry becomes validated. |
| T12 | `src/app/(catalog)/layout.tsx`, `src/app/(catalog)/page.tsx`, `src/components/catalog/browse`, `registry/david-ui/catalog/command.tsx`, `registry/david-ui/catalog/browse-controls`, `src/demos/catalog/browse`, `e2e/catalog-browse.spec.ts`, `catalog/updates/catalog-browse.ts` | The catalog shell browses the aggregate with five independent filters, command search and theme controls made from kit entries. |
| T13 | `src/app/(catalog)/components/[slug]/page.tsx`, `src/components/catalog/entry`, `registry/david-ui/catalog/copy-button.tsx`, `registry/david-ui/catalog/entry-controls`, `src/demos/catalog/entry`, `e2e/catalog-entry.spec.ts`, `catalog/updates/catalog-entry.ts` | An entry view renders the selected entry demo, state/API metadata and install information with viewport and motion controls made from the kit. |
| T14 | `src/lib/auth`, `src/proxy.ts`, `src/app/login/page.tsx`, `src/app/api/session/route.ts`, `e2e/auth.spec.ts` | Owner sessions and registry bearer authorization prevent unauthenticated access and source leakage, with explicit invalid-configuration failures. |
| T15 | `registry/david-ui/p2`, `src/demos/p2`, `e2e/p2.spec.ts`, `catalog/updates/p2.ts`, `catalog/qa/p2.ts` | The twelve P2 inventory entries and the remaining seven enhancement outcomes satisfy the established status and interaction contracts. |
| T16 | `registry/david-ui/motion`, `src/demos/motion`, `e2e/capabilities.spec.ts`, `catalog/updates/capabilities.ts`, `catalog/qa/capabilities.ts` | Seven Animate UI capabilities expose their documented APIs while reusing the existing Button, CopyButton and Scroll Area contracts. |
| T17 | `registry/david-ui/bencho/capabilities`, `src/demos/bencho/capabilities`, `e2e/bencho-capabilities.spec.ts`, `catalog/updates/bencho-capabilities.ts` | Six Bencho capabilities have clean-room-safe origins, explicit failure states and operable keyboard/touch alternatives. |
| T18 | `registry/david-ui/bencho/variants`, `src/demos/bencho/variants`, `e2e/bencho-variants.spec.ts`, `catalog/updates/bencho-variants.ts` | Six Bencho variants preserve the established boolean, selection, numeric and notification models without adding a second engine. |
| T19 | `registry/david-ui/text`, `src/demos/text`, `e2e/reactbits-text.spec.ts`, `catalog/updates/reactbits-text.ts` | Nine React Bits text effects retain readable SSR content, license notices, token wiring and deterministic reduced-motion behavior. |
| T20 | `registry/david-ui/showcase`, `src/demos/showcase`, `e2e/reactbits-ui.spec.ts`, `catalog/updates/reactbits-ui.ts` | Twelve React Bits interface and gallery entries preserve Card semantics and usable keyboard/touch navigation. |
| T21 | `registry/david-ui/effects`, `registry/david-ui/backgrounds`, `src/demos/effects`, `src/demos/backgrounds`, `e2e/reactbits-effects.spec.ts`, `catalog/updates/reactbits-effects.ts` | Six interaction effects and five backgrounds obey lifecycle suspension and static-fallback rules with measured performance evidence. |
| T22 | `scripts/agent-index.ts`, `scripts/agent-index.test.ts`, `AGENTS.md`, `CLAUDE.md`, `docs/consumption.md` | Manifest-generated agent metadata and consumption guidance agree with installable registry entries and QA states. |
| T23 | `netlify.toml`, `scripts/prod-smoke.mjs`, `scripts/prod-smoke.test.mjs` | The linked private production catalog enforces both authorization boundaries and passes a reproducible deployed smoke check. |
| T24 | `scripts/acceptance.mjs`, `scripts/acceptance.test.mjs`, `e2e/acceptance.spec.ts` | A self-contained acceptance harness starts the built application and validates login, discovery and isolated registry consumption without shell secrets. |
| T24a | `.evidence/T24-run.md` | The finished acceptance commands run unchanged against real production entry points and retain exit codes and flow evidence for the audit. |
| T25 | `.evidence/T25.md`, `.evidence/T25.findings.json` | A read-only review maps the integrated outcome to R1–R16 and records every confirmed defect in a valid blocking-findings ledger. |

T1 owns package scripts, bootstrap ESLint restrictions, tool configs, and the two report validators. T6 owns the AST
kit-only scanner and negative fixtures; it does not edit T1's ESLint config. npm scripts point at the declared producer
paths; bootstrap verification deliberately excludes commands whose implementation has not been produced yet.
check-spike.mjs validates the structured spike's complete named matrix, versions, probe outcomes, license provenance
and engine ruling; the manual source review establishes the meaning of that evidence. check-audit-ledger.mjs implements
the inspected audit-findings/1 gate: malformed JSON/schema, duplicate finding IDs, invalid severity/status/task names,
fixed without evidence and accepted without owner provenance fail; an open critical/high finding fails. Its fixtures
prove these rejection cases. Its known task-ID list matches this contract. Neither validator treats file existence as QA.

T4 alone owns catalog/entries.ts: it seeds the 93 candidates and deterministically assembles catalog/updates and
catalog/qa contributions. Seed completion is keyed by the existing inventory ID, not an added duplicate entry. Each ID
has one owning metadata fragment; unknown IDs, duplicate update ownership and broken references fail. QA fragments
can promote status only with all R6 evidence. The final assembled list is what consumers see. Additions needed by the
catalog are tagged separately so the fixed 93-candidate counts stay exact. Every component task records a non-pending
result for its candidates, including blocked/discarded reasons, and may only mark validated when R6 is complete.

T5 owns the proof Button implementation; T7 owns additional variants, tests and demos on that API. T11 creates the
kit-based demo dispatcher and P1 QA/browser harness before the catalog shell exists. T12 owns Command and any required
browse controls added early; T15 finalizes their QA without introducing another Command or editing T12's files.
T13 similarly owns the early CopyButton and entry controls; T16 reuses them. T17 and T18 have separate source/demo/
browser files. P2 occupies its own module subtree rather than claiming the entire registry. All source families retain
license notices, tokens, browser-safe imports and truthful final statuses. Resources on task lines identify bounded coordination contracts; they are exclusive scheduling resources, not promises about concurrency. The five cross-task contracts are IF-1 to
IF-5 in PLAN.json; their producers, consumers, invariants and integration criteria are authoritative there.

All browser specifications start real Next routes using the T1 Playwright webServer configuration. e2e/helpers.ts
(T11) supplies synthetic server-side credentials and authenticates through the public login flow once T14 exists;
it never bypasses guards. Tests do not require an ignored .env, inherited shell variables or a .git directory.
T24 constructs isolated fixtures, builds and starts next start on an available loopback port, polls readiness with a
deadline, drives browser login → filters/search → entry → install copy, and invokes the real shadcn CLI against the
bearer-protected registry in fresh Next consumers. It covers one installable item per source and the complete set of
implemented/validated entries; an absent source representative fails instead of being silently skipped. Each child has
explicit synthetic environment, bounded concurrency and deadlines. Failed startup, install/build errors and timeouts
return nonzero; teardown touches only owned temporary processes/directories. T24a only executes these finished commands
and records actual outcomes; failures return to the producer, and product judgment belongs to T25.

Production smoke is distinct from local fixtures: T23 resolves the new site URL by its dav033/david-ui linkage using
the existing authenticated Netlify CLI and reads required production credentials through that authenticated service
boundary, without printing them. No verification relies on ignored .netlify/state.json or the shell environment.
A missing identity, URL or secret produces a deliberate failure. Missing/wrong bearer tests must exercise actual static
/r delivery on Netlify, including JSON indexes, not only Next handler imports. The unresolved secret locations must
be resolved before T14/T23 execution; this classification session performs no production action.


## Spec review amendments (2026-10-22)
An independent spec review tightened SPEC.md after classification; task scope is unchanged, these details bind them:
- T4: manifest fields `origin` (inventory / catalog-driven / own), normalized priority + raw source priority, type
  enum, exposure form, `applicableStates`, incorporation date, dependency-compatibility result, `ownerApproved`;
  `catalog:check` counts only `origin: inventory` (30/12 shadcn, 7, 6+6 Bencho, 9/12/6/5 React Bits) and verifies
  license header notices on copied files. Status semantics are in SPEC "Status semantics".
- T12/T13: inventory entries the catalog needs early (Command, Scroll Area, Drawer…) are built there and stay inventory
  entries; T13 also adds the gaps page (R9).
- T14/T22: the agent index is served at `/r/index.json` and `/r/llms.txt`, both behind the registry token (R14).
- T16: Page Transition validated only on the Next App Router.
- T17/T18: §10.3 slugs; each R12 rule has its own test.
- T21: backgrounds measured with Pixel 7 emulation + 4× CPU throttle, median ≥ 30 FPS or static fallback by default on mobile (R13).
- T22: `AGENTS.md` documents the deliberate upstream-update procedure (R10).
## Tasks

### M1 — Foundation: repo, tokens, manifest, licenses, registry pipeline
Acceptance: `npm run verify` passes on a fresh clone; the manifest check counts exactly 42/7/12/32 entries and 22 linked enhancements; the license register covers the four sources; `npx shadcn add` of a proof item from the local registry installs into a scratch Next app that builds; the kit-only check fails on a planted violation.

- [ ] T1 — Scaffold `~/dev/david-ui`: Next 16 + TS strict + Tailwind 4 + shadcn init (Base UI style) + ESLint/Prettier + Vitest/Testing Library + Playwright/axe; scripts `verify`, `test`, `test:e2e`; `.gitignore` incl. `.evidence/`; `.env.example`; create private GitHub repo `dav033/david-ui` and push · repo: app · verify: `npm run build` · files: package.json, package-lock.json, tsconfig.json, components.json, next.config.ts, eslint.config.mjs, vitest.config.mts, playwright.config.ts, .env.example, .gitignore, src/app/layout.tsx, src/app/not-found.tsx, scripts/check-spike.mjs, scripts/check-audit-ledger.mjs, scripts/check-planning-tools.test.ts · resources: contract:verification-tools · covers: R1, R16 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 240 minutes.

  Objective: A private greenfield checkout has the approved toolchain and named package scripts ready for the later producers, plus fail-closed report validators.

  Estimate: Provisional engineering estimate in minutes: 150 scaffold and configurations + 50 checker fixtures + 40 bootstrap verification = 240. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / static: The bootstrap production build compiles the Next 16 strict-TypeScript scaffold with the approved React and Tailwind versions. Check: `npm run build` (authored by T1)
  - Acceptance / functional: Bootstrap unit fixtures reject malformed compatibility reports and malformed or blocking audit ledgers. Check: `npm run test` (authored by T1)
  - Acceptance / static: The scaffold lint rules accept the bootstrap files with no disabled rules. Check: `npx eslint .` (authored by T1)
  - Acceptance / product: The GitHub repository dav033/david-ui is private and the scaffold is pushed using the authorized owner account. Check: manual: Outside the snapshot verifier, inspect gh repository visibility and the pushed commit with the existing authenticated CLI. Expected: Private visibility and the scaffold commit are confirmed; no secrets appear in tracked files.

- [ ] T2 — Compatibility and license spike: per each of the 22 enhancements and 7 capabilities, whether Animate UI ships a Base UI variant and its install path; Motion/React/Tailwind version matrix; Sonner vs Animate UI toast as single engine; licenses of shadcn, Animate UI, Bencho (per block) and React Bits; write `.evidence/T2-spike.md` and record the toast-engine and primitive rulings · repo: app · after: T1 · verify: `node scripts/check-spike.mjs .evidence/T2-spike.json` · files: .evidence/T2-spike.md, .evidence/T2-spike.json · resources: contract:upstream-compatibility-licenses · covers: R2, R10, R11 · kind: research

  Classification: complexity high; scope small_change; risk high; coupling high; confidence low; estimate 240 minutes.

  Objective: A reproducible compatibility matrix and license record give every enhancement and capability a supported route or an explicit blocked result before source adoption.

  Estimate: Provisional engineering estimate in minutes: 120 version/install experiments + 90 source/license evidence + 30 matrix checks = 240. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed. Confidence is low specifically because the actual upstream license and compatibility outcomes are the research deliverable, not inspected implementation evidence.

  - Acceptance / functional: The spike records all 22 enhancement routes, seven capability routes, pinned version probes and source licenses with evidence and one notification-engine ruling. Check: `node scripts/check-spike.mjs .evidence/T2-spike.json` (authored by T1)
  - Acceptance / product: The spike conclusions are backed by primary-source license text and reproducible compatibility probes, applying clean-room whenever copying is not clearly allowed. Check: manual: Review the spike source references, pinned versions and probe outcomes before their adoption. Expected: Every source has license provenance; all enhancements/capabilities have a compatible, manual or explicitly blocked route; exactly one engine is chosen.

- [ ] T3 — Design tokens and motion: `registry/david-ui/styles/tokens.css` (Catppuccin Latte/Mocha, mauve accent, radii, shadows, typography, spacing, motion durations/easings for subtle/natural/expressive), `ThemeProvider`, `MotionProfileProvider` (Motion `MotionConfig` + reduced motion), `useMotionProfile`; registry items for them · repo: app · after: T2 · verify: `npx vitest run registry/david-ui/lib` · files: registry/david-ui/styles/tokens.css, registry/david-ui/lib/theme-provider.tsx, registry/david-ui/lib/motion-profile.tsx, registry/david-ui/lib/motion-profile.test.tsx · resources: contract:motion-profile · covers: R3, R8 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 180 minutes.

  Objective: Consumers share one theme and motion contract, including a natural default and an overriding reduced-motion policy.

  Estimate: Provisional engineering estimate in minutes: 60 tokens + 70 providers and SSR behavior + 50 behavior checks = 180. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Theme and motion tests cover light/dark, natural default, all three profiles, reduced-motion precedence and SSR-safe rendering. Check: `npx vitest run registry/david-ui/lib` (authored by T3)

- [ ] T4 — Catalog manifest and license register: zod schema (R5), `catalog/entries.ts` with all 93 entries `pending` and the 22 enhancements linked to base entries, `catalog/licenses.ts` from T2, `npm run catalog:check` asserting counts, unique ids, base links and status/metadata rules · repo: app · after: T2 · verify: `npm run catalog:check` · files: catalog/schema.ts, catalog/entries.ts, catalog/licenses.ts, catalog/check.ts, catalog/check.test.ts · resources: contract:upstream-compatibility-licenses, contract:catalog-schema · covers: R5, R10 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 240 minutes.

  Objective: One validated aggregate exposes the 93 inventory candidates and 22 linked enhancements, with deterministic owned metadata updates and license provenance.

  Estimate: Provisional engineering estimate in minutes: 100 typed schema and aggregation + 70 catalog rules + 70 invalid-data tests = 240. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / static: Catalog checks accept exactly the 93 baseline candidates and 22 linked enhancements, counting catalog-driven additions separately. Check: `npm run catalog:check` (authored by T4)
  - Acceptance / functional: Catalog tests reject duplicate IDs or updates, broken enhancement links, missing metadata, invalid QA promotion and unlicensed copying routes. Check: `npx vitest run catalog/check.test.ts` (authored by T4)

- [ ] T5 — Registry pipeline: `registry.json` generated from the manifest, `npm run registry:build` (`shadcn build` → `public/r/`), proof item `button`; integration script `scripts/registry-smoke.mjs` that creates a scratch Next app in a temp dir, installs `@david-ui/button` from a locally served registry and builds it · repo: app · after: T3, T4 · verify: `npm run registry:build` · files: registry.json, scripts/build-registry.ts, scripts/registry-smoke.mjs, registry/david-ui/structure/button.tsx · resources: contract:registry-button · covers: R1 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 210 minutes.

  Objective: The generated shadcn registry installs its Button proof and dependencies into a fresh Next application that builds.

  Estimate: Provisional engineering estimate in minutes: 90 registry generation + 50 proof Button + 70 isolated consumer smoke = 210. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / static: Registry generation emits shadcn-compatible items with complete source and dependency references. Check: `npm run registry:build` (authored by T5)
  - Acceptance / integration: The Button proof installs through the locally served registry into a fresh Next app whose production build succeeds. Check: `node scripts/registry-smoke.mjs` (authored by T5)

- [ ] T6 — Kit-only guard: ESLint `no-restricted-imports` outside `registry/` + `scripts/check-kit-only.ts` (forbidden imports and raw interactive JSX in `src/app`, `src/components`), with a test that plants violations · repo: app · after: T1 · verify: `npm run check:kit-only` · files: scripts/check-kit-only.ts, scripts/check-kit-only.test.ts · resources: contract:verification-tools · covers: R4 · kind: implement

  Classification: complexity medium; scope small_change; risk medium; coupling medium; confidence medium; estimate 120 minutes.

  Objective: The kit-only guard rejects forbidden primitive imports and raw interactive JSX while accepting kit consumers.

  Estimate: Provisional engineering estimate in minutes: 60 source analysis + 40 planted violations + 20 clean-tree checks = 120. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / static: The kit-only guard accepts the current catalog and never scans generated artifacts as source. Check: `npm run check:kit-only` (authored by T6)
  - Acceptance / functional: Guard fixtures reject forbidden primitive imports and raw interactive JSX, including aliases and a styled as a button, while allowing kit components. Check: `npx vitest run scripts/check-kit-only.test.ts` (authored by T6)

### M2 — 30 P1 shadcn components with their Animate UI enhancements
Acceptance: the 30 P1 entries (§3.1–3.6) are `validated` or `implemented`/`blocked` with reason; each of the P1-related enhancements (Select, Checkbox, Switch, Combobox, Sidebar, Tabs, Dropdown Menu, Pagination, Dialog, Alert Dialog, Sheet, Popover, Tooltip, Accordion, Toast) has a result; each validated entry has a demo, unit tests, an axe-clean e2e and a reduced-motion e2e; one notification engine.

- [ ] T7 — Structure + forms: Button (+ variants), Card, Badge, Avatar, Field, Input, Textarea, Select*, Checkbox*, Switch*, Combobox* (* = Animate UI enhancement), demos with all states, manifest updated · repo: app · after: T5, T6 · verify: `npx vitest run registry/david-ui/structure registry/david-ui/forms` · files: registry/david-ui/structure/card.tsx, registry/david-ui/structure/badge.tsx, registry/david-ui/structure/avatar.tsx, registry/david-ui/structure/button-variants.tsx, registry/david-ui/structure/button.test.tsx, registry/david-ui/forms, src/demos/structure, src/demos/forms, catalog/updates/p1-structure-forms.ts · resources: contract:registry-button, contract:motion-profile · covers: R2, R3, R6, R7, R8 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 420 minutes.

  Objective: The eleven structure/form candidates and their linked enhancements have tokenized demos, behavior tests and recorded implementation outcomes.

  Estimate: Provisional engineering estimate in minutes: 220 component adaptations + 100 demos and metadata + 100 state and interaction tests = 420. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Structure and form tests cover all eleven candidates, applicable states, controlled values, keyboard/touch inputs and reduced-motion interruption. Check: `npx vitest run registry/david-ui/structure registry/david-ui/forms` (authored by T7)
  - Acceptance / regression: The assembled P1 foundation passes lint, types, units, kit-only checks, catalog checks, registry generation and production build. Check: `npm run verify` (authored by T1)

- [ ] T8 — Navigation: Sidebar* (manual), Tabs*, Dropdown Menu*, Breadcrumb, Pagination* (manual) · repo: app · after: T7 · verify: `npx vitest run registry/david-ui/navigation` · files: registry/david-ui/navigation, src/demos/navigation, catalog/updates/p1-navigation.ts · resources: contract:navigation-browse · covers: R2, R6, R7, R8 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 300 minutes.

  Objective: The five navigation candidates keep keyboard and touch navigation intact through their approved animation enhancements.

  Estimate: Provisional engineering estimate in minutes: 150 navigation adapters + 70 demos/metadata + 80 keyboard and routing tests = 300. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: All five navigation candidates preserve active selection, focus movement and keyboard/touch navigation with their documented enhancement results. Check: `npx vitest run registry/david-ui/navigation` (authored by T8)
  - Acceptance / regression: Navigation integration preserves the full foundation verification pipeline. Check: `npm run verify` (authored by T1)

- [ ] T9 — Overlays and disclosure: Dialog*, Alert Dialog*, Sheet*, Popover*, Tooltip*, Accordion* · repo: app · after: T7 · verify: `npx vitest run registry/david-ui/overlays` · files: registry/david-ui/overlays, src/demos/overlays, catalog/updates/p1-overlays.ts · resources: contract:overlays-entry · covers: R2, R6, R7, R8 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 330 minutes.

  Objective: The six overlay/disclosure candidates preserve focus return, dismissal and keyboard operation during animated transitions.

  Estimate: Provisional engineering estimate in minutes: 170 animated overlays + 70 demos/metadata + 90 focus/dismissal tests = 330. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: All six overlay candidates handle opening, interrupted closing, Escape, focus return and nested dismissal without keyboard traps. Check: `npx vitest run registry/david-ui/overlays` (authored by T9)
  - Acceptance / regression: Overlay integration preserves the full foundation verification pipeline. Check: `npm run verify` (authored by T1)

- [ ] T10 — Feedback and data: Alert, Toast/Sonner* (single engine per T2, R11), Skeleton, Spinner, Empty, Table, Data Table (composition API: filter, sort, select, paginate), Chart · repo: app · after: T7 · verify: `npx vitest run registry/david-ui/feedback registry/david-ui/data` · files: registry/david-ui/feedback, registry/david-ui/data, src/demos/feedback, src/demos/data, catalog/updates/p1-feedback-data.ts · resources: contract:notification-values · covers: R6, R11 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 420 minutes.

  Objective: The nine feedback/data candidates provide tested feedback states and composable data operations on one notification engine.

  Estimate: Provisional engineering estimate in minutes: 220 feedback/data APIs + 90 demos/metadata + 110 behavior tests = 420. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Feedback and data tests cover nine candidates, notification deduplication and Data Table filter, sort, select and paginate composition. Check: `npx vitest run registry/david-ui/feedback registry/david-ui/data` (authored by T10)
  - Acceptance / regression: Feedback and data integration preserves the full foundation verification pipeline. Check: `npm run verify` (authored by T1)

- [ ] T11 — P1 e2e and a11y suite: Playwright spec that opens every P1 demo, runs axe, exercises keyboard paths and repeats under `reducedMotion: 'reduce'`; promote passing entries to `validated` · repo: app · after: T8, T9, T10 · verify: `npx playwright test e2e/p1.spec.ts` · files: e2e/p1.spec.ts, e2e/helpers.ts, src/app/demos/[...slug]/page.tsx, catalog/qa/p1.ts · resources: contract:demo-dispatch · covers: R6, R7, R8 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 240 minutes.

  Objective: A real P1 demo route and browser suite establish the exact evidence required before any P1 entry becomes validated.

  Estimate: Provisional engineering estimate in minutes: 90 demo dispatch and browser helpers + 100 state/a11y cases + 50 QA promotion checks = 240. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / integration: Every P1 demo runs in a real browser with applicable states, keyboard/touch paths, zero axe violations and reduced-motion checks; QA promotion requires every R6 field. Check: `npx playwright test e2e/p1.spec.ts` (authored by T11)

### M3 — Private catalog application built with the kit
Acceptance: the catalog lists all entries from the manifest with filters by source, category, priority, status and type, command-palette search, entry pages with live demo, states, props table, install command, origin/license/version, light/dark, viewport preview and motion-profile switch; login protects pages and a bearer token protects `/r/*`; `check:kit-only` passes; every UI piece the app needed is a kit entry (catalog-driven additions recorded).

- [ ] T12 — Catalog shell and browse: layout with kit Sidebar/Breadcrumb, home grid of entries, filters (source, category, priority, status, type), command-palette search (adds `Command` and any shadcn piece needed, e.g. Toggle Group, as catalog-driven additions), theme toggle · repo: app · after: T11 · verify: `npx playwright test e2e/catalog-browse.spec.ts` · files: src/app/(catalog)/layout.tsx, src/app/(catalog)/page.tsx, src/components/catalog/browse, registry/david-ui/catalog/command.tsx, registry/david-ui/catalog/browse-controls, src/demos/catalog/browse, e2e/catalog-browse.spec.ts, catalog/updates/catalog-browse.ts · resources: contract:navigation-browse, contract:demo-dispatch · covers: R4, R9 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 300 minutes.

  Objective: The catalog shell browses the aggregate with five independent filters, command search and theme controls made from kit entries.

  Estimate: Provisional engineering estimate in minutes: 140 kit composition and early Command + 70 browse behavior + 90 e2e = 300. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / integration: Browse tests drive all five filters, empty results, command search, theme switching and keyboard navigation against the manifest. Check: `npx playwright test e2e/catalog-browse.spec.ts` (authored by T12)
  - Acceptance / static: Catalog browsing uses only kit components and records all needed additions without changing baseline counts. Check: `npm run check:kit-only` (authored by T6)

- [ ] T13 — Entry page: live demo, states gallery, props/API table generated from manifest, install command with Copy Button, origin/license/version panel, viewport preview (mobile/tablet/desktop iframe), motion-profile switch; code-block component created as own animated entry if shadcn has none · repo: app · after: T12 · verify: `npx playwright test e2e/catalog-entry.spec.ts` · files: src/app/(catalog)/components/[slug]/page.tsx, src/components/catalog/entry, registry/david-ui/catalog/copy-button.tsx, registry/david-ui/catalog/entry-controls, src/demos/catalog/entry, e2e/catalog-entry.spec.ts, catalog/updates/catalog-entry.ts · resources: contract:overlays-entry, contract:demo-dispatch · covers: R4, R9 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 300 minutes.

  Objective: An entry view renders the selected entry demo, state/API metadata and install information with viewport and motion controls made from the kit.

  Estimate: Provisional engineering estimate in minutes: 140 entry/demos and early CopyButton + 70 metadata controls + 90 e2e = 300. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / integration: Entry tests verify live demo and states, API/license/version metadata, install copy success/failure, three viewports, motion switching and a deliberate missing-slug result. Check: `npx playwright test e2e/catalog-entry.spec.ts` (authored by T13)
  - Acceptance / static: Entry controls and any code-block implementation come through recorded kit entries. Check: `npm run check:kit-only` (authored by T6)

- [ ] T14 — Privacy: owner login page (kit form components), signed HttpOnly session cookie, `proxy.ts` guard for pages, bearer-token guard for `/r/*` (401 without leaking source), `components.json` consumption example with `${DAVID_UI_REGISTRY_TOKEN}` headers · repo: app · after: T12 · verify: `npx vitest run src/lib/auth` · files: src/lib/auth, src/proxy.ts, src/app/login/page.tsx, src/app/api/session/route.ts, e2e/auth.spec.ts · resources: contract:owner-authorization · covers: R14 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 300 minutes.

  Objective: Owner sessions and registry bearer authorization prevent unauthenticated access and source leakage, with explicit invalid-configuration failures.

  Estimate: Provisional engineering estimate in minutes: 140 session and bearer boundary + 70 login/proxy + 90 rejection/e2e cases = 300. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Authentication units reject missing configuration, incorrect passwords, invalid or expired sessions and incorrect registry tokens without exposing secrets. Check: `npx vitest run src/lib/auth` (authored by T14)
  - Acceptance / integration: Browser authorization tests cover owner login, protected-page redirects, signed HttpOnly sessions and registry 401/200 outcomes without source leakage. Check: `npx playwright test e2e/auth.spec.ts` (authored by T14)

### M4 — P2 components, remaining enhancements and the 7 Animate UI capabilities
Acceptance: the 12 P2 entries (§3.7) and the 7 capabilities (§5) have a final status; the remaining enhancements (Radio Group, Navigation Menu, Drawer, Collapsible, Progress, Slider, Hover Card) have a result, so all 22 are resolved; each capability has its API decision (component, hook or variant) recorded in the manifest.

- [ ] T15 — P2: Calendar, Date Picker, Input Group, Radio Group*, Command (finalize), Navigation Menu*, Drawer*, Collapsible*, Scroll Area, Progress*, Slider*, Hover Card*; demos, unit tests, e2e + axe, manifest · repo: app · after: T13, T14 · verify: `npx vitest run registry/david-ui/p2` · files: registry/david-ui/p2, src/demos/p2, e2e/p2.spec.ts, catalog/updates/p2.ts, catalog/qa/p2.ts · resources: contract:p2-capability-composition · covers: R2, R6, R7, R8 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 480 minutes.

  Objective: The twelve P2 inventory entries and the remaining seven enhancement outcomes satisfy the established status and interaction contracts.

  Estimate: Provisional engineering estimate in minutes: 280 P2 adaptations + 90 demos/metadata + 110 keyboard/a11y tests = 480. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: The twelve P2 entries preserve controlled values and composition APIs and leave all remaining enhancements with a recorded result. Check: `npx vitest run registry/david-ui/p2` (authored by T15)
  - Acceptance / integration: P2 demos support keyboard/touch operation, have no axe violations and obey reduced motion, including the existing Command entry. Check: `npx playwright test e2e/p2.spec.ts` (authored by T15)

- [ ] T16 — Capabilities: Animated Button (Button variant), CopyButton, Animated Icons kit, CountingNumber, AutoHeight, ScrollFade (Scroll Area option), PageTransition (validated with the Next App Router of the catalog) · repo: app · after: T15 · verify: `npx vitest run registry/david-ui/motion` · files: registry/david-ui/motion, src/demos/motion, e2e/capabilities.spec.ts, catalog/updates/capabilities.ts, catalog/qa/capabilities.ts · resources: contract:p2-capability-composition, contract:registry-button · covers: R5, R6, R8 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 330 minutes.

  Objective: Seven Animate UI capabilities expose their documented APIs while reusing the existing Button, CopyButton and Scroll Area contracts.

  Estimate: Provisional engineering estimate in minutes: 170 capability adapters + 70 demos/metadata + 90 router and motion tests = 330. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: All seven capability APIs reuse established value and provider contracts without duplicating Button, CopyButton or Scroll Area implementations. Check: `npx vitest run registry/david-ui/motion` (authored by T16)
  - Acceptance / integration: Capability demos include App Router navigation and interrupted or reduced-motion behavior without hydration warnings. Check: `npx playwright test e2e/capabilities.spec.ts` (authored by T16)

### M5 — Bencho UI (12)
Acceptance: the 12 Bencho entries have a final status with origin (`bencho` or `own (inspired by bencho)` per license); APIs follow §10.2/§10.3 (one value model with Slider/Select/Checkbox/Counting Number, Toast Stack is a presenter on the single engine); every gesture has a keyboard/button alternative; mobile scroll conflicts tested.

- [ ] T17 — New capabilities: RollingNumberInput, VoiceNote (UI + callbacks, permission-denied state), UploadDropzone (size/type rejection, no backend), SlideToConfirm (keyboard/button alternative), MagnifyingDock (focus and touch), PullToRefresh (button alternative, scroll conflicts) · repo: app · after: T16 · verify: `npx vitest run registry/david-ui/bencho/capabilities` · files: registry/david-ui/bencho/capabilities, src/demos/bencho/capabilities, e2e/bencho-capabilities.spec.ts, catalog/updates/bencho-capabilities.ts · resources: contract:bencho-controlled-inputs · covers: R6, R7, R10, R12 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 480 minutes.

  Objective: Six Bencho capabilities have clean-room-safe origins, explicit failure states and operable keyboard/touch alternatives.

  Estimate: Provisional engineering estimate in minutes: 270 capability implementations + 90 demos/metadata + 120 permission/file/gesture tests = 480. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: The six Bencho capability units cover denied microphone permission, rejected file size/type, numeric bounds and exactly-once alternative confirmation. Check: `npx vitest run registry/david-ui/bencho/capabilities` (authored by T17)
  - Acceptance / integration: Bencho capability demos include accessible button/keyboard alternatives, touch/focus Dock operation and PullToRefresh native-scroll conflicts with recorded origins. Check: `npx playwright test e2e/bencho-capabilities.spec.ts` (authored by T17)

- [ ] T18 — Variants: ToastStack presenter (on the T10 engine), PickerWheel, Checklist, CreateMenu, ExpandingSearch, SloshSlider (Slider value model) · repo: app · after: T17 · verify: `npx vitest run registry/david-ui/bencho/variants` · files: registry/david-ui/bencho/variants, src/demos/bencho/variants, e2e/bencho-variants.spec.ts, catalog/updates/bencho-variants.ts · resources: contract:bencho-controlled-inputs, contract:notification-values · covers: R6, R7, R11, R12 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 420 minutes.

  Objective: Six Bencho variants preserve the established boolean, selection, numeric and notification models without adding a second engine.

  Estimate: Provisional engineering estimate in minutes: 230 variant implementations + 80 demos/metadata + 110 semantic/gesture tests = 420. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: The six Bencho variant units share Select, Checkbox and Slider value/event semantics and reuse the single notification engine. Check: `npx vitest run registry/david-ui/bencho/variants` (authored by T18)
  - Acceptance / integration: Bencho variant demos verify wheel/slider bounds, focus and keyboard/touch alternatives, zero axe violations and reduced motion. Check: `npx playwright test e2e/bencho-variants.spec.ts` (authored by T18)

### M6 — React Bits Free (32)
Acceptance: the 32 entries (§11.1–11.4) have a final status, Commons Clause notices kept, tokens wired (tints, sizes, fonts), SSR/hydration clean, reduced-motion respected; backgrounds lazy-load, pause off-screen and fall back without WebGL.

- [ ] T19 — Text (9): Blur Text, Decrypted Text, Text Type, Shuffle, True Focus, Text Pressure, Variable Proximity, Scroll Velocity, Split Text · repo: app · after: T16 · verify: `npx vitest run registry/david-ui/text` · files: registry/david-ui/text, src/demos/text, e2e/reactbits-text.spec.ts, catalog/updates/reactbits-text.ts · resources: contract:text-hydration · covers: R3, R6, R8, R10 · kind: implement

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 420 minutes.

  Objective: Nine React Bits text effects retain readable SSR content, license notices, token wiring and deterministic reduced-motion behavior.

  Estimate: Provisional engineering estimate in minutes: 230 text adaptations + 80 demos/metadata + 110 hydration and accessibility tests = 420. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: All nine text effects keep original readable text, shared tokens and pinned source notices through motion state changes. Check: `npx vitest run registry/david-ui/text` (authored by T19)
  - Acceptance / integration: Text demos render without SSR hydration warnings and preserve accessible content under reduced motion and pointer-free input. Check: `npx playwright test e2e/reactbits-text.spec.ts` (authored by T19)

- [ ] T20 — UI, navigation and galleries (12): Animated List, Scroll Stack, Magic Bento, Circular Gallery, Masonry, Tilted Card, Spotlight Card, Card Swap, Stack, Gooey Nav, Staggered Menu, Stepper (card variants on top of Card, R12) · repo: app · after: T19 · verify: `npx vitest run registry/david-ui/showcase` · files: registry/david-ui/showcase, src/demos/showcase, e2e/reactbits-ui.spec.ts, catalog/updates/reactbits-ui.ts · resources: contract:card-semantics · covers: R6, R7, R12 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 480 minutes.

  Objective: Twelve React Bits interface and gallery entries preserve Card semantics and usable keyboard/touch navigation.

  Estimate: Provisional engineering estimate in minutes: 280 gallery/navigation implementations + 90 demos/metadata + 110 alternative-input tests = 480. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: All twelve showcase entries preserve their documented state and compose shared Card and navigation semantics. Check: `npx vitest run registry/david-ui/showcase` (authored by T20)
  - Acceptance / integration: Showcase demos operate by keyboard and touch, pass axe and reduced-motion checks and have no hydration warnings. Check: `npx playwright test e2e/reactbits-ui.spec.ts` (authored by T20)

- [ ] T21 — Interaction effects (6) and backgrounds (5): Pixel Transition, Electric Border, Animated Content, Magnet, Click Spark, Glare Hover; Aurora, Dot Grid, Orb, Silk, Iridescence with lazy loading, off-screen pause, static fallback; Playwright run with WebGL disabled and CPU throttling recording FPS evidence · repo: app · after: T19 · verify: `npx vitest run registry/david-ui/effects registry/david-ui/backgrounds` · files: registry/david-ui/effects, registry/david-ui/backgrounds, src/demos/effects, src/demos/backgrounds, e2e/reactbits-effects.spec.ts, catalog/updates/reactbits-effects.ts · resources: contract:motion-profile · covers: R6, R8, R13 · kind: implement

  Classification: complexity high; scope large_change; risk medium; coupling high; confidence medium; estimate 480 minutes.

  Objective: Six interaction effects and five backgrounds obey lifecycle suspension and static-fallback rules with measured performance evidence.

  Estimate: Provisional engineering estimate in minutes: 250 effects/background adaptations + 100 lifecycle fallbacks + 130 traces/e2e = 480. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: The six effects and five backgrounds release render resources when hidden or unmounted and keep a static fallback for unavailable WebGL or reduced motion. Check: `npx vitest run registry/david-ui/effects registry/david-ui/backgrounds` (authored by T21)
  - Acceptance / integration: Effect demos run with WebGL disabled, off-screen and hidden-tab transitions and CPU throttling, recording FPS and memory without an invented performance threshold. Check: `npx playwright test e2e/reactbits-effects.spec.ts` (authored by T21)

### M7 — Agent index, deployment and acceptance
Acceptance: `/r/index.json`, `/llms.txt` and repo `AGENTS.md`/`CLAUDE.md` list every entry with install command, origin, version, dependencies, license and QA status; the catalog is live on Netlify behind login, `/r/*` answers 401 without token; the end-to-end flow passes against the built app; the independent audit ledger has no open blocking finding.

- [ ] T22 — Agent integration: generate `/r/index.json` and `/llms.txt` from the manifest; write repo `AGENTS.md` + `CLAUDE.md` (how to pick and install components, kit-only rule, statuses); consumption guide for other projects; entry in `~/dev/cerebro` global notes · repo: app · after: T18, T20, T21 · verify: `npx vitest run scripts/agent-index.test.ts` · files: scripts/agent-index.ts, scripts/agent-index.test.ts, AGENTS.md, CLAUDE.md, docs/consumption.md · resources: contract:catalog-schema · covers: R15 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 210 minutes.

  Objective: Manifest-generated agent metadata and consumption guidance agree with installable registry entries and QA states.

  Estimate: Provisional engineering estimate in minutes: 100 generated indexes + 50 consumption docs + 60 drift tests = 210. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Agent-index tests compare every aggregate entry and variant against both generated endpoints for install command, origin, version, dependencies, license and QA status. Check: `npx vitest run scripts/agent-index.test.ts` (authored by T22)
  - Acceptance / regression: Agent-index generation and documentation integration preserve the complete verification pipeline. Check: `npm run verify` (authored by T1)
  - Acceptance / product: The consumption guide and shared brain note explain discovery, private install headers, statuses and kit-only usage. Check: manual: Review docs/consumption.md, AGENTS.md and CLAUDE.md; add the approved global brain note at its existing location. Expected: The instructions agree with generated indexes and contain variable names only, with no secret values.

- [ ] T23 — Deploy: Netlify site linked to `dav033/david-ui`, env vars set, production build; smoke: login works, protected page redirects, `/r/button.json` 401 without token and 200 with it · repo: app · after: T22 · verify: `node --test scripts/prod-smoke.test.mjs` · files: netlify.toml, scripts/prod-smoke.mjs, scripts/prod-smoke.test.mjs · resources: contract:owner-authorization, netlify:private-david-ui-production · covers: R14, R16 · kind: implement

  Classification: complexity high; scope full_feature; risk high; coupling high; confidence medium; estimate 210 minutes.

  Objective: The linked private production catalog enforces both authorization boundaries and passes a reproducible deployed smoke check.

  Estimate: Provisional engineering estimate in minutes: 80 deployment configuration + 70 smoke harness + 60 production verification = 210. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Production-smoke unit fixtures reject login, redirect, token and static-registry bypass failures and missing deployment configuration. Check: `node --test scripts/prod-smoke.test.mjs` (authored by T23)
  - Acceptance / product: The Netlify production smoke confirms successful login, protected-page redirects and registry denial without or with an incorrect token and success with the valid token. Check: `node scripts/prod-smoke.mjs` (authored by T23)

- [ ] T24 — Build end-to-end acceptance harness: production Next server, login and catalog flow, token-protected registry installs into scratch Next apps, final catalog checks · repo: app · after: T23 · verify: `node --test scripts/acceptance.test.mjs` · files: scripts/acceptance.mjs, scripts/acceptance.test.mjs, e2e/acceptance.spec.ts · resources: contract:acceptance-flow · covers: R1, R4, R5, R6, R9, R14, R15 · kind: implement

  Classification: complexity high; scope full_feature; risk medium; coupling high; confidence medium; estimate 270 minutes.

  Objective: A self-contained acceptance harness starts the built application and validates login, discovery and isolated registry consumption without shell secrets.

  Estimate: Provisional engineering estimate in minutes: 130 process/fixture orchestration + 80 scratch-app matrix + 60 fault injection = 270. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / functional: Acceptance harness fault injection fails on server startup exit, timeout, authorization failure and consumer build failure and cleans up only its own resources. Check: `node --test scripts/acceptance.test.mjs` (authored by T24)
  - Acceptance / integration: The authored production-flow browser spec drives login, browse, filter, search, entry metadata and install-command copy through real routes. Check: `npx playwright test e2e/acceptance.spec.ts` (authored by T24)

- [ ] T24a — Execute the shipped production entry points and full acceptance matrix; report actual results without changing code or judging product acceptance · repo: app · after: T24 · verify: `npm run test:e2e` · files: .evidence/T24-run.md · resources: contract:acceptance-flow · covers: R1, R4, R5, R6, R9, R14, R15 · kind: test

  Classification: complexity medium; scope large_change; risk medium; coupling medium; confidence medium; estimate 240 minutes.

  Objective: The finished acceptance commands run unchanged against real production entry points and retain exit codes and flow evidence for the audit.

  Estimate: Provisional engineering estimate in minutes: 180 full browser/installation runs + 60 outcome and trace capture = 240. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / regression: The complete browser matrix passes keyboard/touch, axe and reduced-motion checks against the built application. Check: `npm run test:e2e` (authored by T1)
  - Acceptance / integration: The harness starts next start and the shadcn CLI, drives the authenticated catalog flow and installs at least one entry per source plus every installable entry into isolated Next consumers that build. Check: `node scripts/acceptance.mjs` (authored by T24)
  - Acceptance / static: The final aggregate has no pending baseline candidate, all 22 enhancements resolved and complete required metadata and QA evidence for every validated entry. Check: `npm run catalog:check -- --final` (authored by T4)

- [ ] T25 — Independent audit of the whole requirement against SPEC R1–R16 and the inventory rules (§6, §10.2, §11.6): read-only review, findings ledger · repo: app · after: T24a · verify: `node scripts/check-audit-ledger.mjs .evidence/T25.findings.json` · files: .evidence/T25.md, .evidence/T25.findings.json · resources: contract:acceptance-flow · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit
- [ ] T25b — Cross-check audit of T25: Independent audit of the whole requirement against SPEC R1–R16 and the inventory rules (§6, §10.2, §11.6): read-only review, findings ledger · repo: app · after: T24a · verify: `node scripts/check-audit-ledger.mjs .evidence/T25-crosscheck.findings.json` · files: .evidence/T25-crosscheck.md, .evidence/T25-crosscheck.findings.json · resources: contract:acceptance-flow · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16 · kind: audit

  Classification: complexity high; scope large_change; risk high; coupling high; confidence medium; estimate 300 minutes.

  Objective: A read-only review maps the integrated outcome to R1–R16 and records every confirmed defect in a valid blocking-findings ledger.

  Estimate: Provisional engineering estimate in minutes: 210 requirement/inventory review + 60 reproduction + 30 ledger validation = 300. Includes authoring and local checks where owned. History for this kind returned status unknown, no comparable sample count or measured duration; no empirical calibration is claimed.

  - Acceptance / product: The audit ledger conforms to audit-findings/1, names valid responsible plan tasks and has no open critical or high finding. Check: `node scripts/check-audit-ledger.mjs .evidence/T25-crosscheck.findings.json` (authored by T1)

## Review focus

1. Wrong primitive family, ambiguous license or incompatible versions: T2's full structured matrix and manual primary-source review, then T4's invalid license/status fixtures.
2. Controlled values, focus traps and interrupted animation: T7/T9/T10 units, T11 keyboard/touch browser paths and T18 shared-model tests.
3. Malformed credentials, forged/expired cookies, missing config and public static-file bypass: T14 auth units/browser suite and T23 deployed smoke (wrong as well as missing bearer).
4. Browser capability and lifecycle gaps: T17 denied-permission/type/size cases; T19 hydration checks; T21 WebGL-disabled, reduced-motion, hidden-tab and off-screen tests with FPS/memory evidence.
5. Registry metadata drift, missing transitive dependencies, startup exit and consumer build failure: T4 invalid manifest tests, T22 index comparisons, T24 fault injection and T24a isolated installs through real entry points.

## Semantic self-review

This is same-context adversarial self-review, not independent approval. Deterministic validation is reported separately.

- Demonstrated defect, high: original T11 authored a Playwright harness and promoted metadata while kind test; T22 generated TypeScript while kind docs; T24 authored the acceptance scripts while kind test. Corrected T11/T22/T24 to implement and isolated the existing final command execution as T24a (test). No component or feature was added.
- Demonstrated defect, high: original T25 used test -s on a ledger and T2 used the same existence-only pattern for research. Replaced them with behavior-validating report checks; T25 still declares exactly one findings ledger and owns only report/ledger files. T24a is its real integration-test predecessor. A blocking finding sends named producing tasks back; the audit never repairs code.
- Demonstrated defect, medium: catalog/entries.ts was declared by most component tasks. Kept T4 as its one owner and partitioned contributions by responsibility, including early Command/CopyButton ownership and separate QA evidence. Directory-level claims were narrowed; downstream consumers import existing APIs.
- Demonstrated defect, medium: the bootstrap promised full verify before its own future commands existed. Bootstrap now runs actual available build/lint/unit checks; the final pipeline is first executed after M1 closes. This changes verification timing, not final required behavior.
- Plausible risk, high: Netlify may serve generated static files outside the tested Next authorization path (SPEC R14/R16, original T14/T23). T23 must prove deployed source denial or correct the deployment boundary; local mocks cannot establish privacy.
- Plausible risk, medium: CopyButton and Command are consumed before their source-family milestone. Explicit producer ownership and later QA-only reuse remove a backward dependency; T13 and T12 respectively own those early kit entries.
- Fact: no application consumers, package commands, browser harness or source implementations exist in the checkout. Complexity is high where the work crosses state/lifecycle/security/contracts or creates an integration harness; T6 and T24a stay medium because their bounded responsibilities exclude those implementation decisions. No task needs extreme complexity or full_system scope. Estimates include missing harness work, remain provisional and use no unavailable history metrics.
- Product decision retained: the approved scope has one independent final audit. The validator may recommend a second audit; this classification does not expand the approved review scope or assign its execution.
- Fact: automated checks cannot establish the meaning of primary-source licenses, externally pushed GitHub state in an isolated snapshot. Independent product review is performed by T25 and accepted through its findings ledger, not through an additional report-attestation criterion. The three manual criteria explicitly state expected evidence and require coordinated attestation. Planned created_by warnings disclose unfinished work rather than pretending tests already exist.

## Deterministic validation

`python3 /home/david/dev/metodologia/skill/scripts/bitacora.py --project david-ui plan-json check REQ-001`
returned exit 0 and `OK: PLAN.json is publishable`. The final run is repeated after this record is written.
Final checker disclosures: 64 warnings. Fifty created_by checks refer to future producer work; three manual criteria
require attestation (GitHub external state, primary-source spike review and consumption documentation/brain note); ten
requirement-level product warnings distinguish planned checks from actual product acceptance; one recommends another audit. The approved single-audit scope is retained. There are no unmapped purposes, criteria without
checks, ownership hotspots, missing classifications or structural errors. Structural publication is distinct from input
readiness and scope approval. No product lint, typecheck, build or behavior test ran because no application exists yet.

## Rulings
- Retain all approved naming, theme, Base UI, single-engine and clean-room rulings from SPEC and the original plan.
- No approval, freeze, handoff, launch, implementation, revision or runtime-state operation is authorized by this classification update.

## Progress log
- 2026-10-22: spec and plan written from the owner's inventory v4 and interview round 1.
- Classification update: completed task metadata, traceability, typed evidence, owned paths and categorized exact-purpose verification; deterministic check exit 0, no errors; product checks remain planned and secret locations remain unresolved.
- 2026-10-23 06:07 plan APPROVED (terminal)
- 2026-10-23 06:07 launched Scheduler supervisor from HQ in `/home/david/dev/david-ui`
