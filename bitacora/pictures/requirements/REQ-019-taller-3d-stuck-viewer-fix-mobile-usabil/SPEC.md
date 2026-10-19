---
id: REQ-019
status: in-progress
created: 2026-10-19
track: standard
---
# REQ-019 — Taller 3D stuck viewer fix, mobile usability and React Bits UI polish

<!-- status: ready → ready → planned → in-progress → done | dropped -->

## Problem & goal
Three owner requests (2026-10-19):
1. **Bug:** sometimes, on entering the 3D editor (`/3d`), the viewer is "stuck" (cannot orbit/zoom, scene does not
   frame); only choosing another template fixes it.
2. **Mobile usability** of the Taller 3D (and the main flows) is weak.
3. **Design polish:** add components from reactbits.dev to improve design, animation and usability.

Plus a precondition from the owner: start clean from `main`, with the current local state committed and pushed.

**Success looks like:** the stuck viewer cannot be reproduced on route re-entry (automated regression test); the
Taller passes a 390×844 touch audit (targets ≥ 44 px, no hover-only actions, canvas visible while editing); a small,
curated set of React Bits components is in use with reduced-motion respected and no WebGL backgrounds.

## Users / actors / stakeholders
- Decorators/pros using the Taller 3D (desktop and phone/tablet), customers in `/asistente` and shared quotes.
- Owner (David) approves visuals.

## Findings from exploration (evidence)
- **Root cause of the stuck viewer (high confidence, H1):** `next.config.ts:16` sets `cacheComponents: true`, so
  Next keeps visited routes inside `<Activity mode="hidden">`. Leaving `/3d` runs effect cleanups —
  `Taller3D.tsx:234-239` destroys the viewer — but React keeps state and refs. On return the mount effect
  (`Taller3D.tsx:218`) creates a new viewer, yet `encuadradoRef.current` still equals `vueltaEncuadre`, so
  `Taller3D.tsx:313` computes `encuadrar = false`; the new viewer never frames and the camera stays at the origin
  looking at the origin (OrbitControls radius 0). `plantilla()` (`Taller3D.tsx:577-582`) bumps `vueltaEncuadre`,
  which is exactly why changing template fixes it. Aggravating: the `visor` state still points at the destroyed
  viewer until the dynamic import resolves, and the draw effect runs against it. `crearEscena` never sets an initial
  camera position. No WebGL context-loss handling exists (secondary risk, H2).
- **Mobile:** layout switches by JS (`Taller3D.tsx:80-89`, server default = wide → desktop flash on phones);
  `HojaMovil.tsx` sheet jumps between 3 heights with no drag-follow (handle `h-6`, 24 px); hover-only eye button
  (`PanelPiezas.tsx:84`); 36 px menu items (`MenuMas.tsx:16`); `min-h-7/8` in `Inspector.tsx`; 42 uses of 9–11 px
  text in `tres-d`; canvas shrinks to 56 % and the 78dvh sheet hides most of the scene; touch controls emit synthetic
  `KeyboardEvent`s (`ControlesTactiles.tsx:11-13`).
- **Design stack:** Tailwind v4 tokens in `globals.css` (light + dark, `taller-*` palette), `motion` 13 in 80 files
  with `useReducedMotion`, Radix primitives, `cn()`, CVA; no `components.json` (shadcn not set up).
- **React Bits:** install via shadcn registry `@react-bits/<Name>-TS-TW` (code copied into the repo); MIT + Commons
  Clause (commercial use in this app allowed; no resale/redistribution of the components). Some manifests pin
  `motion` ^12 (repo has 13) and some pull `@hugeicons/*` or `gsap`.
- **Git state:** branch `feat/req-014-…` has 0 commits not in `origin/main` (18 behind). The 197 dirty files are the
  REQ-014 payload already shipped in `origin/main` `6649f75a`; versus `origin/main` `2d924c10` the tree is
  +286/−9134 lines (it lacks the Happie merges and later quality fixes). Committing it and pushing to `main` as-is
  would revert that work.

## Scope (in)
### US-1 (P1, Must) — Viewer never gets stuck
As a Taller user, when I return to `/3d` (link navigation, back button, Fast Refresh, sheet open/close), the scene is
framed and orbit/zoom work, without changing template.
**Acceptance:**
- Given `/3d` was visited, when I navigate away with a `<Link>` and come back, then the camera is framed on the scene
  and orbit/zoom respond (regression test with `<Activity>` hidden→visible and a Playwright route round-trip).
- Given the WebGL context is lost, then the viewer shows a recoverable message/rebuilds instead of freezing silently.

### US-2 (P1, Must) — Taller usable on a phone
As a decorator on a phone (390×844, touch), I can select, edit, hide/show and reorder pieces and reach every action
with targets ≥ 44 px, while still seeing the scene.
**Acceptance:**
- No hover-only action in the mobile tree; all interactive targets ≥ 44 px (automated check at 390×844).
- Bottom sheet follows the finger with snap points and momentum, and respects `prefers-reduced-motion`.
- No desktop-layout flash on phone first paint.
- Canvas remains visible (≥ 40 % of the viewport) at the sheet's middle height; the top floating bar never overlaps
  the safe area.
- Text in the mobile tree ≥ 12 px except decorative labels.

### US-3 (P2, Should) — Curated React Bits polish
As a user, the app feels more polished: animated counters/totals, list entrances, step indicators and card hover
effects, consistent with the existing tokens (light/dark) and Spanish copy.
**Acceptance:**
- Only components from the approved shortlist are added, in `src/components/ui/reactbits/`, typed (TS strict, no
  `any`), using repo tokens, and each honors `prefers-reduced-motion`.
- No React Bits WebGL/canvas background is mounted on `/3d`.
- Single `motion` version in the lockfile; bundle size of `/3d` and `/asistente` measured before/after.

## Out of scope
- Rewriting the three.js engine or moving to react-three-fiber.
- Splitting `Taller3D.tsx` (P-007) beyond what the fixes need.
- `/happie` and admin/lab pages (its chat may reuse the AI components later; proposal only).
- React Bits Pro (paid) components.

## Requirements
- R1. When `Taller3D` unmounts its effects (Activity hidden, route change), the system shall reset the viewer state
  (`visor` → null) and the framing ref so the next viewer frames on first draw.
- R2. `crearEscena` shall set a valid initial camera position/target so a viewer is never at radius 0.
- R3. If the WebGL context is lost, the system shall surface it and recreate the viewer when restored.
- R4. The mobile layout decision shall not render the desktop tree on a phone's first paint.
- R5. While on a touch/coarse-pointer device, every interactive control in the Taller shall be ≥ 44×44 px and
  visible without hover.
- R6. The mobile sheet shall support drag-follow with snap points (closed / medium / tall) and keyboard/a11y
  equivalents.
- R7. Animated components shall honor `prefers-reduced-motion` (live, not only at mount).
- R8. Added React Bits components shall come only from the approved shortlist, live in
  `src/components/ui/reactbits/`, use the repo tokens (light/dark), keep one `motion` version and no WebGL/canvas
  background on `/3d`, and keep the license notice.
- R9. The AI chat surfaces (assistant waiting state, scene-AI steps, "Foto realista" generation, composer) shall use
  the approved React Bits AI components, adapted to the existing logic.
- R10. `/asistente` and `/cotizacion-compartida/[token]` shall pass the same touch audit as the Taller, or list each
  remaining issue as a pending item.
- R11. Changes shall reach `main` only after the local gate passes (owner authorized a direct push, round 1 Q2).

## Edge cases & errors
- Back/forward cache, Fast Refresh, StrictMode double mount, dynamic import resolving after unmount.
- Too many WebGL contexts (Biblioteca thumbnails, captures) on low-end phones.
- iOS keyboard over the sheet (`useInsetTeclado`), landscape phones (`apaisado` variant), tablets with coarse pointer
  at ≥ 1024 px.
- Reduced motion; dark theme; Spanish strings longer than English demos.

## Constraints
- Next 16.3 App Router with `cacheComponents`, React 19.2, TS strict, Tailwind v4, `motion` 13, three 0.180.
- Repo rules in `AGENTS.md` (lint, `npm run build --workspaces --if-present`, `npx tsc --noEmit`, affected tests).
- Catppuccin is the desktop aesthetic, but the app keeps its own tokens (`globals.css`); React Bits must adapt to them.
- Commons Clause: do not publish the copied components as a standalone package.
- Never discard owner worktree changes; feature work happens in a worktree from `origin/main`.

## Priorities & phases
- M0 (Must, DONE 2026-10-19 before the scheduler): clean start from `main` (backup branch + merge `ae78a79d`).
- M1 (Must): stuck-viewer fix + regression tests.
- M2 (Must): mobile usability of the Taller.
- M3 (Should): React Bits setup + curated components.
- M4 (Must): independent audit, gate, PR.

## Timeline & dependencies
- No deadline given. M1 is independent of M2/M3; M3 setup can run parallel to M2.

## Assumptions
- A1. "Edición 3D" = the Taller at `/3d` (not the guided 3D in `/asistente`).
- A2. Mobile scope = Taller 3D first, plus touch-target fixes in `/asistente` and the shared quote if cheap.
- A3. Superseded by Q2: direct push to `main` after the local gate.

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
| Timeline | Clear (n/a) |

## Clarifications
### Round 1 — 2026-10-19
- Q1 local state → A: (a) snapshot to a backup branch and start clean from `origin/main`, BUT every local change must
  end up in `main` without overwriting Happie. Evidence (2026-10-19 preview with a temp index + `git merge-tree`):
  snapshot `f03b3dbf` (parent `HEAD` `5f910498`) merges into `origin/main` `2d924c10` keeping all Happie work; only 5
  add/add conflicts in shared-quote routes/page, where `main` holds the newer Quality fix (`connection()` instead of
  `force-dynamic`, required by `cacheComponents`). Resolved to `main`, the merged tree equals `origin/main`.
- Q2 → A: (b) push directly to `main` after the local gate (owner authorization for this plan).
- Q3 → A: (b) Taller 3D + cheap fixes in `/asistente` and the shared quote.
- Q4 → A: shortlist approved, plus React Bits AI-chat components (owner: "revisa la documentación"). Found in the
  Micro category: Prompt Bar (composer), Thought Line (reasoning trace), Status Mark (agent task status), Lattice
  Loader (waiting row + stopwatch), Refine Frame (image generation stages), Swipe Toast; Text Type (gsap) as text.
- Q5 → A: approved: full-height canvas, draggable sheet over it with snaps 15 / 45 / 85 %, camera recentred.
