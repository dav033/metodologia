---
id: REQ-001
status: planned
created: 2026-10-22
track: deep
---
# REQ-001 — Private UI kit library with catalog and registry

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

Source inventory (owner's document v4, Spanish, authoritative for the component list, overlaps and per-source rules):
[SOURCE-INVENTORY.md](SOURCE-INVENTORY.md). Section numbers `§N` below refer to it.

## Problem & goal
David builds several React projects (maros, pictures, dav033-demos, proposal-studio…) and each one assembles its UI
from shadcn/ui, Animate UI and React Bits ad hoc, so every project looks and behaves differently and agents re-pick
components every time. Goal: **one private, reusable React component kit** ("david-ui") with a single visual identity,
a high standard of interactivity and feedback, a private web catalog with real demos, and a shadcn-compatible registry
that both David and coding agents (Claude Code, Codex) install from.

**Success looks like:**
- All 93 candidate entries of the inventory (42 shadcn + 7 Animate UI capabilities + 12 Bencho + 32 React Bits Free)
  and the 22 Animate UI enhancements end in a verified, recorded state (none left `pending`).
- `npx shadcn add @david-ui/<name>` installs any `implemented`/`validated` entry into a fresh Next.js app that then
  builds without edits.
- The catalog application itself is built 100 % from kit components (enforced by an automated check).
- `npm run verify` and `npm run test:e2e` pass; the catalog is deployed and private.

## Users / actors / stakeholders
- **Owner (David):** browses the catalog, installs components in his projects, approves entries.
- **Coding agents (Claude Code, Codex):** discover components through the agent index and install them from the registry.
- **Catalog visitors:** only the owner (private, login required).

## Scope (in)

### US-1 (P1, Must) — Kit foundation
As the owner, I want one repo with tokens, theme, motion profiles and tooling so that every component shares one identity.
**Acceptance:**
- Given the repo, when `npm run verify` runs, then lint, typecheck, unit tests, the kit-only check, the catalog check,
  the registry build and the production build all pass.
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
- `implemented` — code in the registry, demo and unit tests exist, install works; some R6 check is still failing and
  the reason is written in the entry.
- `validated` — every R6 check passes. This is the target status for every entry.
- `blocked` — cannot be delivered now (license, primitive family, dependency conflict); reason and unblock condition written.
- `discarded` — deliberately not delivered (redundant per §10.2/§11.6); reason written.
- Owner production approval (§10.4 "aprobarlos para producción") is a separate manifest flag `ownerApproved`
  (default `false`), set by the owner from the catalog after delivery; it never blocks this requirement.

### US-3 (P1, Must) — 30 P1 shadcn components with their Animate UI enhancements
As the owner, I want the essential components (§3.1–3.6) working on Base UI with their motion enhancements so that new
projects can start from the kit.
**Acceptance:**
- Given M2 is done, when `npm run catalog:check` runs, then all 30 P1 entries are `validated`, `implemented`, `blocked`
  or `discarded` (with reason), and the 15 P1-related enhancements have a result (`compatible`, `manual`, `blocked`,
  `discarded`); `npx playwright test e2e/p1.spec.ts` passes for every `validated` P1 entry.

### US-4 (P1, Must) — Private catalog built with the kit
As the owner, I want a private web catalog with filters, search, live demos, states, light/dark, responsive viewport
preview, motion-profile switch and install commands, built only from kit components.
**Acceptance:**
- Given the logged-in owner, when browsing the catalog, then every R9 capability works
  (`e2e/catalog-browse.spec.ts`, `e2e/catalog-entry.spec.ts`), and `npm run check:kit-only` passes.
- Given a request without session or token, then pages redirect to login and `/r/*` returns 401 (`e2e/auth.spec.ts`).

### US-5 (P2, Must) — 12 P2 shadcn components, remaining enhancements and 7 Animate UI capabilities (§3.7, §4, §5)
**Acceptance:**
- Given M4 is done, then the 12 P2 entries and the 7 capabilities have a final status (not `pending`), all 22
  enhancements have a result, and each capability records its exposure form (component, hook or variant), API summary
  and catalog location (§9); `e2e/p2.spec.ts` and `e2e/capabilities.spec.ts` pass for `validated` entries.

### US-6 (P2, Must) — 12 Bencho UI entries (§10), clean-room where the license forbids copying
**Acceptance:**
- Given M5 is done, then the 12 Bencho entries have a final status and origin per R10, use the §10.3 slugs under
  `@david-ui`, satisfy every R12 rule that applies to them, and `e2e/bencho.spec.ts` passes (including keyboard/button
  alternatives and mobile-emulated scroll conflicts).

### US-7 (P2, Must) — 32 React Bits Free entries (§11)
**Acceptance:**
- Given M6 is done, then the 32 entries have a final status, keep their upstream license notice in the source header,
  render without hydration warnings, respect reduced motion, and backgrounds meet R13 (`e2e/reactbits-*.spec.ts`).

### US-8 (P2, Must) — Agent integration and deployment
As the owner, I want agents to discover and install kit components, and the catalog deployed privately.
**Acceptance:**
- Given a consuming Next app configured with the token, when an agent reads `/r/index.json` and runs
  `npx shadcn add @david-ui/<slug>`, then the component installs and the app builds (`scripts/acceptance.mjs`).
- Given the production URL, then `scripts/prod-smoke.mjs` confirms login, page protection and token enforcement.

## Out of scope
- Migrating existing projects (maros, pictures, dav033-demos…) to the kit — later requirements.
- React Bits Pro or any paid component; the real gaps (Comparison Slider, Device, Page Flip, AI Blob with states, §11.5)
  are documented, not implemented.
- Specialized editors (Notion-like, graph editors) (§7).
- Publishing the kit publicly or to npm; any redistribution to third parties.
- Backends behind UI components (real file storage for Upload Dropzone, audio upload for Voice Note): UI + callbacks only.
- shadcn components listed in §3.8 unless the catalog app needs them (R4).
- React Bits `Count Up`, `Counter` and `Dock` (§11.6.1–2): not selected.
- The §11.5 own compositions "Modal Cards" and "Hover Preview": later; listed on the catalog gaps page with the real
  gaps (Comparison Slider, Device, Page Flip, AI Blob with states).

## Requirements
- R1. The kit shall live in a new private repository `~/dev/david-ui` (GitHub `dav033/david-ui`) as one Next.js
  application that is at the same time the catalog and the shadcn registry; component sources live under
  `registry/david-ui/` and are published under the namespace `@david-ui`.
- R2. The kit shall use Base UI as its single primitive family; where Animate UI has no Base UI variant, the
  enhancement shall be integrated by hand on the Base UI component (result `manual`) or recorded `blocked` with a reason.
- R3. Every component shall read colors, typography, spacing, radii and shadows from shared CSS tokens, and functional
  controls (shadcn, Animate UI, Bencho) shall also take motion timings from the active profile; React Bits graphic
  effects take tints, sizes and fonts from tokens but keep their own physics (§11.6.8). The default theme shall be
  Catppuccin Latte (light) / Mocha (dark) with mauve accent, replaceable per consuming project.
- R4. The catalog application shall be built only from kit components: when it needs a UI piece the kit lacks, the
  executor shall first add it from shadcn/ui (recorded as a catalog-driven addition), and only if no shadcn component
  exists shall create an own component with motion; an automated check (`npm run check:kit-only`) shall fail when app
  code outside `registry/` imports UI primitives/animation libraries directly or renders raw interactive HTML elements
  (`button`, `input`, `select`, `textarea`, `dialog`, `a` styled as button).
- R5. The catalog manifest shall record every entry with id (kebab-case of the name; §10.3 slugs for Bencho, e.g.
  `seek` → `expanding-search`, `liq-create` → `create-menu`, `picker` → `picker-wheel`, `dock` → `magnifying-dock`),
  name, source, origin (`inventory`, `catalog-driven`, `own`), category, priority (P1/P2: shadcn as listed; Alta → P1,
  Media → P2 for §5 and §11; Bencho P2) plus the raw source priority, type (`base` = shadcn, `capability` = Animate UI
  §5, `new-capability` / `variant` = Bencho §10.1, `presentation` = React Bits), exposure form (component, hook,
  variant, utility), applicable states, status (`pending`, `implemented`, `validated`, `blocked`,
  `discarded`), upstream URL and version/commit, license, dependencies, public API summary, a11y and reduced-motion
  results, and demo path; the 22 enhancements shall be linked to their base entry with a test result
  (`compatible`, `manual`, `blocked`, `discarded`) and never counted as entries.
- R6. When an entry is marked `validated`, it shall have a live demo with every state in its `applicableStates`
  (from hover, focus-visible, pressed, disabled, loading, success, error), keyboard operation where interactive, no axe
  violations, respected `prefers-reduced-motion`, no hydration warnings under SSR, unit tests for its behavior (for
  text effects and backgrounds: render, prop and reduced-motion/fallback tests) and a registry item that installs into
  a fresh app.
- R7. Each interactive control shall offer keyboard and touch operation; hover, drag or cursor proximity shall never be
  the only way to operate it (§11.6.7, §10.2).
- R8. The kit shall expose three motion profiles (subtle, natural default, expressive) through a provider; animations
  shall prefer `transform`/`opacity`, be interruptible, and collapse to instant/opacity-only under reduced motion.
- R9. The catalog shall offer: browse and filter by source, category, priority, status and type; command-palette search;
  an entry page with live demo, states gallery, props/API table, install command, origin/license/version, light/dark
  toggle, viewport preview (mobile/tablet/desktop) and motion-profile switch; a gaps page listing the documented gaps
  (§11.5) and every `blocked`/`discarded` entry with its reason. Inventory entries the catalog needs early (e.g.
  `Command`, `Scroll Area`, `Drawer`) are built in the catalog milestone and still count as inventory entries.
- R10. Before copying code from a source, the executor shall record that source's license in the license register; if
  a license forbids copying (expected for some Bencho blocks), the entry shall be reimplemented clean-room (behavior from
  the public description/demo, no copied code) and marked origin `own (inspired by <source>)`. Copied files shall keep
  their upstream license notice in a header comment (checked by `catalog:check`). Upstream updates are deliberate: the
  manifest records upstream version and incorporation date, and an update re-diffs upstream against the local
  adaptation instead of overwriting it (procedure in the repo `AGENTS.md`).
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
- R14. The catalog shall be private: pages require an owner login (password + signed session cookie), and registry
  endpoints `/r/*` (including `/r/index.json` and `/r/llms.txt`) require a bearer token that consuming projects and
  agents send through `components.json` registry headers or an `Authorization` header.
- R15. The kit shall publish an agent index (`AGENTS.md`/`CLAUDE.md` in the repo plus a machine-readable index at
  `/r/index.json` and `/r/llms.txt`, token-protected per R14) listing every entry with variants, origin, install command, version, dependencies,
  license and QA status, and a short consumption guide for other projects.
- R16. The catalog shall be deployed to Netlify from the private GitHub repo, with secrets only in Netlify env vars.

## Edge cases & errors
- Animate UI piece exists only for Radix → manual integration on Base UI or `blocked` (R2), never a mixed primitive family.
- Upstream install command fails or pulls conflicting deps (React/Tailwind/Motion versions) → pin, adapt or `blocked` with reason.
- Two sources implement the same thing → keep one per §10.2/§11.6; the other becomes a variant or `discarded` with reason.
- License unknown or ambiguous → treat as forbidding copy (clean-room) and note it.
- No WebGL / low-end device / reduced motion → static fallback (R13).
- SSR/hydration: client-only effects guarded; no hydration warnings in the catalog build.
- Registry request without or with a wrong token → 401, no component source leaked.
- Pull to Refresh vs native scroll, Magnifying Dock on touch, Slide to Confirm without drag → button/keyboard alternative (R7).
- Voice Note uses real `getUserMedia`/`MediaRecorder` (no upload backend); without microphone permission → explicit
  denied state. Upload Dropzone over size/type → rejection state.
- Page Transition depends on the router and its version: validated only against the catalog's Next App Router; other
  routers are documented as untested.

## Constraints
- Next.js 16 App Router, React 19, TypeScript strict, Tailwind CSS 4, npm, Node 24 (precedent: `~/dev/dav033-demos`).
- shadcn CLI with Base UI style; Motion (`motion`) for animation, CSS for simple transitions.
- Tests: Vitest + Testing Library (units), Playwright + `@axe-core/playwright` (e2e/a11y), including a reduced-motion run.
- Code, comments and identifiers in English; catalog UI copy in Spanish.
- Licenses: React Bits Free is MIT + Commons Clause (private own use only; keep notices); the kit stays private (§11.7).
- No secrets in the repo; `.env.example` documents `DAVID_UI_PASSWORD`, `DAVID_UI_SESSION_SECRET`, `DAVID_UI_REGISTRY_TOKEN`.
- Working evidence (reports, findings ledgers) goes to the git-ignored `.evidence/` folder and is copied to
  `~/bitacora/david-ui/artifacts/REQ-001/`.
- Production actions authorized globally by the owner (2026-10-19): creating the private GitHub repo, pushing to
  `main`, Netlify deploys.

## Priorities & phases
Must, in order: foundation + manifest + registry (US-1, US-2) → P1 components (US-3) → catalog app (US-4) → P2 +
capabilities (US-5) → Bencho (US-6) → React Bits (US-7) → agent index + deploy + acceptance (US-8). MVP = through US-4.

## Timeline & dependencies
- No deadline. Each milestone is independently verifiable and committable.
- US-4 depends on US-3 (the catalog is built with the P1 components). US-6/US-7 depend on the license register (US-2).

## Assumptions
- Project/repo name `david-ui`, registry namespace `@david-ui` (owner said "ui kit david o algo así").
- Default theme Catppuccin Latte/Mocha with mauve accent (owner's desktop aesthetic; not explicitly answered).
- Sonner is the notification engine unless the spike shows the Animate UI toast primitive is a better single engine.
- Owner login is a single password (no user accounts); enough for a private catalog of one owner.
- Bencho licenses are unknown; clean-room reimplementation (owner ruling, round 1 Q5) applies to all 12 entries if
  copying is not clearly permitted.
- FPS/memory are measured with Playwright mobile emulation and CPU throttling (R13), not on real low-end phones — a
  deliberate deviation from §11.6.6 "dispositivos modestos"; real-device checks come with the first consuming project.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear (no deadline) |

## Clarifications
### Round 1 — 2026-10-22
- Q: Scope of this requirement? → A: (a) all 93 entries, in milestones.
- Q: Project and repo name? → A: "ui kit david o algo así" → `david-ui`.
- Q: Distribution and hosting? → A: (a) one Next.js app = catalog + shadcn registry, Netlify, gallery behind login, registry behind token.
- Q: Primitive family? → A: Base UI.
- Q: Source license forbids copying? → A: (a) clean-room reimplementation with documented origin.
- Owner addition: the whole Next.js catalog app must be built with the kit itself; no component outside the kit. If a
  needed component does not exist in the kit, look for it in shadcn; if it exists nowhere, create it and animate it (R4).
- Spec review (independent reviewer, 2026-10-22): 15 findings applied — counting by origin, status semantics,
  acceptance for US-3..US-8, R12 rules made testable, vocabulary, gaps page, token on the agent index, FPS threshold,
  upstream-update procedure, applicable states and SSR. Modal Cards / Hover Preview compositions deferred.

## Inputs

Classification-only update: the approved product scope above is unchanged. No credential values were read or recorded.

| Item | Where it lives | Supplier | Status |
|---|---|---|---|
| Approved scope, inventory and naming | SPEC.md, PLAN.md, SOURCE-INVENTORY.md; owner request in this session | Owner | available |
| Repository and requirement directory | app = /home/david/dev/david-ui; requirement directory supplied in this session | Owner / project.json | available |
| GitHub account / remote | Existing gh login as dav033; target private repository dav033/david-ui; ~/bitacora/TOOLS.md | Owner | location given |
| Netlify account / target environment | Existing netlify CLI login, team dav033's team; new site linked to dav033/david-ui; provider-assigned HTTPS URL recorded by T23 | Owner / Netlify | location given |
| Production-action authority | Approved SPEC Constraints and PLAN Global constraints record the 2026-10-19 authorization; no production action is part of classification | Owner | available |
| Source URLs, candidate lists, licensing fallback | SOURCE-INVENTORY.md sections 3–5, 10–11; SPEC R2/R10; T2 resolves technical compatibility and records primary-source license evidence before copying | Owner / upstream | available |
| Stack, design and product decisions | SPEC Constraints / Requirements / Assumptions; owner explicitly approved these documents as the scope | Owner | available |
| Fixtures and local runtime | Synthetic component data and disposable Next apps authored by their producing tasks; no customer data, database, paid service, webhook or SSH host required | Implementer | available |
| Local ports and isolated verification | Test harness binds an available loopback port, passes child-process environment explicitly and shuts down its own processes; no .env or inherited shell variables required | Implementer | available |
| Artifact storage | .evidence/ (ignored); ~/bitacora/david-ui/artifacts/REQ-001/ | Approved PLAN | location given |

Unresolved input 1 (asked together at the start of classification): the locations of DAVID_UI_PASSWORD,
DAVID_UI_SESSION_SECRET and DAVID_UI_REGISTRY_TOKEN. Alternatively the owner can explicitly defer each named secret
with the fallback: securely generate during execution, store outside Git and load into Netlify. No values are requested.
These three inputs are not yet claimed available or deferred; the plan cannot be declared ready while they remain unresolved.

### Revision 10 note — 2026-10-24 reset (factual; scope and acceptance unchanged)

The owner wiped all execution of revisions 1–9 on 2026-10-24: the run state, the local checkout `/home/david/dev/david-ui`,
the Netlify site `david-ui-private` and `~/.config/david-ui/prod.env`. Rows above that call the repository directory
"available" or point at the old site no longer hold; PLAN revision 10 recreates everything from zero. Observed on
2026-10-24 by the planner: `/home/david/dev/david-ui` is absent, `netlify api listSites` lists no david site, and
`gh repo view dav033/david-ui` still returns a private, non-empty repository (created 2026-10-23T11:18Z). No secret value
was read or recorded.

| # | Item | Where it lives | Supplier | Status |
|---|---|---|---|---|
| 1 | GitHub repository `dav033/david-ui` | Still exists on GitHub (private, non-empty); T1 must create it fresh | Owner | pending: delete it, or authorize T1 to reuse it with a new root history (force-push), or name another repository |
| 2 | DAVID_UI_PASSWORD, DAVID_UI_SESSION_SECRET, DAVID_UI_REGISTRY_TOKEN, DAVID_UI_PROD_URL | Previously `~/.config/david-ui/prod.env` (deleted). The production check reads names from `~/.config/flow/secrets.env` or the owner process environment | Owner | pending: give the location, or defer by name with the fallback "T59 generates the three secrets with a CSPRNG, writes them and DAVID_UI_PROD_URL to `~/.config/flow/secrets.env` (mode 600) and sets them as Netlify env vars" |
| 3 | Operator verification policy for the production smoke (T60) | `/home/david/dev/metodologia/bitacora/david-ui/verification-policy.json` (absent); entry `environment: production`, `authorization` exactly "Owner authorizes read-only HTTPS smoke requests against the david-ui Netlify production site for REQ-001", `requirements: ["REQ-001"]` | Owner (operator file; the plan cannot grant it) | pending: create it, or accept that T60 ends BLOCKED_EXTERNAL until it exists |
| 4 | Netlify site name | Team "dav033's team" (netlify CLI logged in) | Owner | pending: confirm `david-ui-private` (fallback: provider-assigned name if taken) |
| 5 | Netlify GitHub app access to `dav033/david-ui` | Netlify team settings | Owner | pending: confirm access, or accept the fallback `netlify deploy --prod --build` from the checkout with the site still recording the repository |
| 6 | Local repository path | `/home/david/dev/david-ui` (project.json role `app`) | Owner / project.json | location given; created by T1 |
| 7 | Design contract approvals | `bitacora.py design approve REQ-001 <contract>@v1` or the web requirement page; six contracts in two rounds | Owner | expected during the run (D-127), not before approval |
