---
req: REQ-009
status: done
created: 2026-10-11
---

# Plan — REQ-009 — Material 3 redesign for complete proposal workflows

## Approach

Use Material 3's adaptive layout, clear surface hierarchy, field-state and motion patterns, with form accessibility and error-summary practices from W3C/GOV.UK. Keep the existing Astro/CSS stack and Catppuccin palette. Improve shared navigation and the proposal workflow itself, not only surface decoration.

## Global constraints

- Preserve existing API, auth, proposal-data, capture, publish, archive, and share contracts.
- No new dependency; keep existing Catppuccin Mocha/lavender accents.
- No commit, push, or deployment.
- Protect unrelated pre-existing work in the shared worktree.

## Tasks

- [x] T1 — Record Material/W3C/GOV.UK guidance and audit the current design/task flows · files: `research.md`, app UI · verify: source-backed review notes · covers: R1-R8
- [x] T2 — Establish consistent adaptive admin shell and route hierarchy · files: `src/components/admin/*`, `src/pages/admin/*`, `src/styles/admin.css` · verify: desktop/tablet/mobile browser review · covers: R1, R7
- [x] T3 — Redesign create/edit flow, field grouping, labels, capture state, and page management · files: `src/pages/admin/proposals/*`, `src/scripts/editor-client.ts`, `src/styles/admin.css` · verify: focused create/edit browser flow · covers: R2, R5, R6, R9
- [x] T4 — Add field-level error summary and clear pending/success/failure states to mutation actions · files: editor/integration/share scripts and markup · verify: invalid, repeated, and network-failure browser scenarios · covers: R3, R4
- [x] T5 — Apply the same system to dashboard, login, GitHub integration, and public proposal surfaces · files: admin/public Astro and styles · verify: route-by-route viewport review · covers: R1, R7, R8
- [x] T6 — Run two fresh antagonistic audits, plus accessibility/spec review; fix major/high issues and repeat audits · files: audited scope · verify: written audit verdicts · covers: R1-R9
- [x] T7 — Run check, lint, targeted formatting, automated tests, build and diff checks; update bitácora and brain · files: documentation + changed source · verify: actual command outcomes · covers: R1-R9

## Verification

- Sign-in feedback and public home at narrow and desktop widths.
- Authenticated proposal creation with missing/invalid inputs, save, capture upload, and navigation to editing.
- Edit pages: update inputs, add/remove pages, preserve state after errors, upload captures, save and preview.
- Publish action is disabled until a saved draft exists, blocks duplicates, communicates completion/failure.
- GitHub import workflow labels, pending/error/ready states remain visible and clear.
- Temporary-link duration/create/revoke actions remain understandable and responsive.
- Public proposal page selection, divider drag/range, keyboard, reduced motion.
- 320, 390, 681, 850, 1024, 1440 px no horizontal overflow; contrast/focus labels reviewed.

## Rulings

- Retain dark Catppuccin styling because global workspace preferences require it; Material 3 informs hierarchy, spacing, field states, navigation and feedback rather than theme colors.
- Use static labels with compact one-line hints; avoid placeholder-as-label and avoid explanatory paragraphs inside fields.
- Keep this workflow on one page but chunk it by the actual task sequence; the user asked for a compact proposal tool, and splitting into multiple route steps would add complexity.

## Progress log

- 2026-10-11: David explicitly asked for a whole-product and form usability redesign based on Material guidance, plus proactive adversarial audits. Scope confirmed from current routes and existing field/API contracts.
- 2026-10-12: All tasks completed. `npm run build` passed Astro check (126 files, zero diagnostics), ESLint, Prettier, 84 Vitest tests, and Vercel production build. `npm run test:e2e` passed all 11 Playwright tests, including proposal workflow/recovery, comparison keyboard behavior, reduced motion, and responsive dashboard. Updated stale E2E assertions for the redesigned dashboard title and finding-card component. Final antagonistic reviews: SOUND. No commit, push, or deployment.
