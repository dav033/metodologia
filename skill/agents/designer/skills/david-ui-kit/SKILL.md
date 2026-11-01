---
name: david-ui-kit
description: Build planning mockups of changes to the existing product from real shadcn/Base UI, Animate UI, Bencho and React Bits; explore directions inside the project's design system, build offline and verify rendered accessibility.
---

# Real components and design directions

Use for every planning mockup. The project's SPEC and the owner's words win. The mockup changes an existing product
surface: reproduce its shell/navigation/header and change only what the UI brief demands. Components come only from
the pool `@bitacora/ui` (metodologia's `skill/ui`, D-280): the single source for every project and every mockup; the
project's own UI components lose to it. The look is the project's theme, `skill/ui/themes/<project>.css` (its tokens
and fonts mapped onto the shadcn roles); no new palette, fonts or brand. No invented copy or names. Paths below are
relative to this skill; the delegation brief provides the absolute skill root.

1. Read `real/manifest.json` for installed components and imports, `directions.md` for creative exploration,
   and `../../references/mockup-craft.md` for layout and content. Prefer real libraries; the plain HTML `kit/`
   is an explicitly reported fallback when the toolchain cannot run. Never call that fallback shadcn itself.
2. Compose the TSX entry the brief names under the assigned `design/` directory. Start from
   `real/reference/acceso.tsx`, `cuentas.tsx` or `invitar.tsx`, not from their visual layout: take the composition
   from the existing screens. Import `mountMockup, useMockup` from `@kit/mockup`, every control from
   `@bitacora/ui/components/…` (the manifest's import paths), motion helpers from `@kit/motion`. The builder
   resolves these. The TSX is THE screen: the panel renders it live against the current pool and theme (an old
   mockup restyles when the pool changes), the implementer starts from it, the visual review compares against it. Keep native selects
   `view`, `state`, `scene` (when dialogs exist), `theme`, with Spanish labels. Every declared state is reachable.
3. Operate screens: shadcn + Animate UI feedback. Marketing: React Bits sparingly. Bencho gestures:
   supply button/keyboard alternatives. Recompose components to serve the flows; restyle only toward the
   project's own tokens and components. The kit is a toolbox, not a fixed layout. Name each in the contract as `source:id variant state`,
   with the manifest import path. Document custom components and gaps honestly.
4. Base UI gotchas: Select needs `items` for labels; use its `render` prop instead of Radix `asChild`.
   For destructive actions use AlertDialog. Modal background is inert; focus returns on dismissal.
   Read the actual installed component export before using it.
5. Never redefine tokens, fonts or pool component styles in the TSX (no `:root` token blocks, no `!important`
   restyling of `data-slot` components): the roles (`skill/ui/src/theme.css` names) come from the project theme.
   A missing or wrong project theme is the operator's to fix (`components theme import <project> --from <tokens>`);
   say so in CONCERNS. The pool's Catppuccin defaults apply only when the project has no theme. Text ≥4.5:1,
   control edges ≥3:1, visible keyboard focus. Keep meaningful groups
   aligned, common baselines, generous container padding (24px desktop, 20px phone), no clipped controls.
6. Motion is expected: expressive is the mockup default. Give each direction its own easing, timing and
   choreography; a memorable move is an interaction/motion detail inside the existing surface, never a new identity. Use load, state/view transitions, press/hover/focus, scroll and feedback.
   Repeated controls stay quick. Transform/opacity first; content stays visible and legible mid-animation.
   Read `useMotionProfile()` and pass its duration/spring/reduced state to Motion/GSAP. Three profiles:
   subtle/natural/expressive. Respect reduced motion, `?still=1`, offscreen and hidden-tab suspension.
7. Build the export OFFLINE with the preinstalled toolchain:
   `python3 <skill-root>/scripts/bitacora.py --project <project> components mockup build ENTRY.tsx --out OUTPUT.html`.
   This inlines React, the pool, the project theme, fonts, Motion/GSAP and assets into ONE HTML (the export and audit
   copy). No CDN or runtime fetch.
   Inspect `components status`; installation is the operator's job, never fetch packages in a design delegation.
8. Run `python3 kit/contrast.py OUTPUT.html` (both themes) and
   `UV_OFFLINE=1 uv run --no-project --offline --with playwright python kit/audit_mockup.py OUTPUT.html`.
   Fix findings, then inspect screenshots at 1280/390 in both themes. Copy the actual RESULT into the note/report.
   Exit 2 or missing tooling means `AUDIT NOT RUN: <reason>` in CONCERNS. Never invent a pass.
9. Exploration: write ONLY your assigned revision-specific TSX, HTML, two candidate thumbnails, Markdown note
   and JSON axis evidence. Do not write the canonical contract. The system compares directions; the owner picks;
   a finalization delegation then writes the one twelve-section contract and chosen HTML.
10. `--fresh` means start from requirements and unresolved feedback; do not patch the previous visual draft.
    History and other directions are immutable. Never approve a contract.

The toolchain workspace is `~/.local/share/bitacora/kit-workspace` (override `BITACORA_KIT_WORKSPACE`); the
component sources live in `skill/ui` (`components pool import-sources` copies an upstream install into it).
Operator setup: `components install` uses official installers; `components build` rebuilds the gallery offline.
Designer delegations use the configured unrestricted provider CLI; scope is enforced by the task contract,
not by claiming an OS sandbox exists. Builder writes only its chosen output. Audit uses cached Playwright/Chromium.
