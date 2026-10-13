---
req: REQ-001
status: done
created: 2026-10-10
---
# Plan — REQ-001 — Prospect proposal comparison tool

## Approach
Build a standalone Astro + TypeScript static site with one shared proposal template and one data file per prospect. Use a local Playwright capture command for the current site's first viewport; this keeps the public site static and avoids a server-side browser service or API secret. Embed each user-hosted prototype in an iframe, keep its visible side interactive, and let the prospect compare it through a draggable divider.

## Global constraints
- No CRM, database, admin UI, signature/payment, outreach automation, video recording/hosting, or custom domain in this MVP.
- Store proposal data and generated screenshots in the project; expose no private management controls.
- Validate external URLs, restrict screenshot navigation to public HTTP(S) destinations, and return clear capture errors.
- Prototype pages need iframe permission; keep a new-tab fallback.
- Public proposal routes must work in static output and on Cloudflare Pages.
- Do not deploy or publish during this requirement.

## Tasks
- [x] T1 — Create standalone Astro/TypeScript app with static proposal routes and sample data · files: `package.json`, `astro.config.mjs`, `src/` · verify: `npm run build` · covers: R1, R7, R8, US-1
- [x] T2 — Implement public proposal layout with editable findings, scope, estimate, optional video, and contact CTA · after: T1 · verify: `npm run build` · covers: R1, R7, US-6
- [x] T3 — Add before/after draggable comparison with a keyboard-adjustable handle, interactive prototype clipping, and persistent new-tab link · after: T1 · verify: manual browser walkthrough · covers: R4, R5, R6, R9, US-3, US-4
- [x] T4 — Add local Playwright screenshot command for public site URLs, predictable viewport output, redirect/network validation, and actionable errors · after: T1 · verify: capture a public sample page and an invalid URL · covers: R2, R3, US-2
- [x] T5 — Add responsive styling and concise authoring/development/Cloudflare Pages build instructions · after: T2, T3, T4 · verify: `npm run build` and manual browser walkthrough · covers: R8, US-5

## Verification
Run the production static build. Open the sample proposal locally and manually exercise: route loading; dragging the comparison handle; keyboard-adjusting it; clicking a prototype interaction while comparison remains visible; mobile layout without horizontal overflow; optional sections; persistent new-tab link. Run the capture command against one public URL, one invalid URL, and one private URL and inspect that only the successful public capture writes an image. No automated test suite is planned in this requirement.

## Rulings
- Capture only the first viewport at a fixed desktop size for MVP — it aligns directly with the prototype viewport; full-page comparisons would need coordinated scrolling and are deferred — cost if wrong: medium.
- Use a local capture command rather than a hosted capture endpoint — keeps the proposal site static and avoids a browser API token/service dependency — cost if wrong: low.
- Use a config file per proposal rather than an admin UI — lowest-maintenance flow for the expected small volume — cost if wrong: medium.
- Treat the project as a standalone folder under `~/dev/proposal-studio`; no existing repo appears to match — cost if wrong: low.
- Use a supplied prototype URL rather than package/upload arbitrary code — the owner builds and hosts prototypes separately — cost if wrong: low.

## Progress log
- 2026-10-10 — Plan approved; implemented the Astro proposal viewer, local capture CLI, comparison interaction, sample prototype, and authoring guide.
- 2026-10-10 — Verified `npm run format:check`, `npm run build`, public capture, invalid/private URL rejection, a redirect-to-loopback block, and manual comparison/Explore walkthrough.
- 2026-10-10 — Fresh-eyes reviews found required-field validation gaps, DNS rebinding exposure, and no DNS deadline; added content validation and a local proxy that pins resolved IPs, rejects known challenge pages, and cancels timed-out DNS requests.
- 2026-10-10 — Owner clarified the comparison UX: keep the prototype as a normal, interactive webpage on its side of the divider. Removed the separate Explore mode and limited pointer capture to the divider handle.
- 2026-10-10 — Re-ran `npm run format:check` and `npm run build`; both pass. Manual Chromium walkthrough clicked the visible prototype navigation link while the divider remained visible, dragged the divider from 50% to 68%, and adjusted it by keyboard to 67%.
- 2026-10-10 — After the owner said the comparison still looked the same, expanded it to full viewport width and made the introduction more compact. Added a temporary drag surface because pointer capture is lost when a drag crosses into an iframe; verified the divider now tracks across the full comparison.
