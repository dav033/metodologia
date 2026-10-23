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
- Given the manifest, when the catalog check runs, then it finds exactly 42 shadcn, 7 Animate UI capabilities,
  12 Bencho, 32 React Bits entries (93) plus 22 Animate UI enhancements linked to existing shadcn entries, and fails on
  any other count, duplicate id or enhancement without a base entry.
- Given an entry with status `implemented` or `validated`, then it has origin, upstream URL, upstream version/commit,
  license, dependencies and a demo; a `blocked`/`discarded` entry has a written reason.

### US-3 (P1, Must) — 30 P1 shadcn components with their Animate UI enhancements
As the owner, I want the essential components (§3.1–3.6) working on Base UI with their motion enhancements so that new
projects can start from the kit.

### US-4 (P1, Must) — Private catalog built with the kit
As the owner, I want a private web catalog with filters, search, live demos, states, light/dark, responsive viewport
preview, motion-profile switch and install commands, built only from kit components.

### US-5 (P2, Must) — 12 P2 shadcn components, remaining enhancements and 7 Animate UI capabilities (§3.7, §4, §5)

### US-6 (P2, Must) — 12 Bencho UI entries (§10), clean-room where the license forbids copying

### US-7 (P2, Must) — 32 React Bits Free entries (§11)

### US-8 (P2, Must) — Agent integration and deployment
As the owner, I want agents to discover and install kit components, and the catalog deployed privately.

## Out of scope
- Migrating existing projects (maros, pictures, dav033-demos…) to the kit — later requirements.
- React Bits Pro or any paid component; the real gaps (Comparison Slider, Device, Page Flip, AI Blob with states, §11.5)
  are documented, not implemented.
- Specialized editors (Notion-like, graph editors) (§7).
- Publishing the kit publicly or to npm; any redistribution to third parties.
- Backends behind UI components (real file storage for Upload Dropzone, audio upload for Voice Note): UI + callbacks only.
- shadcn components listed in §3.8 unless the catalog app needs them (R4).

## Requirements
- R1. The kit shall live in a new private repository `~/dev/david-ui` (GitHub `dav033/david-ui`) as one Next.js
  application that is at the same time the catalog and the shadcn registry; component sources live under
  `registry/david-ui/` and are published under the namespace `@david-ui`.
- R2. The kit shall use Base UI as its single primitive family; where Animate UI has no Base UI variant, the
  enhancement shall be integrated by hand on the Base UI component (result `manual`) or recorded `blocked` with a reason.
- R3. Every component shall read colors, typography, spacing, radii, shadows and motion timings from shared CSS tokens;
  the default theme shall be Catppuccin Latte (light) / Mocha (dark) with mauve accent, replaceable per consuming project.
- R4. The catalog application shall be built only from kit components: when it needs a UI piece the kit lacks, the
  executor shall first add it from shadcn/ui (recorded as a catalog-driven addition), and only if no shadcn component
  exists shall create an own component with motion; an automated check (`npm run check:kit-only`) shall fail when app
  code outside `registry/` imports UI primitives/animation libraries directly or renders raw interactive HTML elements
  (`button`, `input`, `select`, `textarea`, `dialog`, `a` styled as button).
- R5. The catalog manifest shall record every entry with id, name, source, category, priority, type
  (base/capability/variant/new-capability/presentation), status (`pending`, `implemented`, `validated`, `blocked`,
  `discarded`), upstream URL and version/commit, license, dependencies, public API summary, a11y and reduced-motion
  results, and demo path; the 22 enhancements shall be linked to their base entry with a test result
  (`compatible`, `manual`, `blocked`, `discarded`) and never counted as entries.
- R6. When an entry is marked `validated`, it shall have a live demo with all applicable states (hover, focus-visible,
  pressed, disabled, loading, success, error), keyboard operation, no axe violations, respected
  `prefers-reduced-motion`, unit tests for its behavior and a registry item that installs into a fresh app.
- R7. Each interactive control shall offer keyboard and touch operation; hover, drag or cursor proximity shall never be
  the only way to operate it (§11.6.7, §10.2).
- R8. The kit shall expose three motion profiles (subtle, natural default, expressive) through a provider; animations
  shall prefer `transform`/`opacity`, be interruptible, and collapse to instant/opacity-only under reduced motion.
- R9. The catalog shall offer: browse and filter by source, category, priority, status and type; command-palette search;
  an entry page with live demo, states gallery, props/API table, install command, origin/license/version, light/dark
  toggle, viewport preview (mobile/tablet/desktop) and motion-profile switch.
- R10. Before copying code from a source, the executor shall record that source's license in the license register; if
  a license forbids copying (expected for some Bencho blocks), the entry shall be reimplemented clean-room (behavior from
  the public description/demo, no copied code) and marked origin `own (inspired by <source>)`.
- R11. Notifications shall have exactly one engine (Sonner unless the compatibility spike rules otherwise, recorded in
  DECISIONS); Animate UI motion and Bencho Toast Stack shall be presentations on top of it (§10.2.1).
- R12. Overlapping entries shall keep one value model: Rolling Number Input vs Counting Number, Picker Wheel vs Select,
  Slosh Slider vs Slider, Checklist vs Checkbox, card variants vs Card follow §10.2 and §11.6.
- R13. WebGL/canvas backgrounds and heavy effects shall be lazy-loaded, pause when off-screen or the tab is hidden, and
  render a static CSS fallback when WebGL is unavailable or reduced motion is set.
- R14. The catalog shall be private: pages require an owner login (password + signed session cookie), and registry
  endpoints `/r/*` require a bearer token that consuming projects send through `components.json` registry headers.
- R15. The kit shall publish an agent index (`AGENTS.md`/`CLAUDE.md` in the repo plus a machine-readable index at
  `/r/index.json` and `/llms.txt`) listing every entry with variants, origin, install command, version, dependencies,
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
- Voice Note without microphone permission → explicit denied state; Upload Dropzone over size/type → rejection state.

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
- FPS/memory measurements for backgrounds are recorded with Playwright traces on the dev machine with CPU throttling,
  not on real low-end phones.

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
