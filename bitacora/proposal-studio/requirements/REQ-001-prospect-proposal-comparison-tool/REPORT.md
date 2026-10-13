# Execution report — REQ-001

## Built

- Static Astro proposal pages at one route per configured prospect, with findings, deliverables, optional video/timeline/price, and a contact action.
- A draggable comparison between the saved first-viewport PNG of the prospect's current website and the prototype supplied by David.
- An interactive prototype on the proposed side of the divider and a link to open it separately.
- A local Playwright CLI that captures public HTTP(S) sites. A short-lived loopback proxy validates and pins the resolved public IP for each HTTP request and HTTPS tunnel, with DNS and connection timeouts.
- Validation for required proposal copy, deliverables, links, slugs, and screenshots; recognized anti-bot challenges return instructions for a manual capture.
- README instructions and a fictional example for local preview and static Cloudflare Pages output.

## Verification evidence

- `npm run format:check` — passed.
- `npm run build` — passed: Astro type check, ESLint, and static generation of `/` and `/clinica-horizonte/`.
- Capture of `https://www.iana.org/domains/reserved` — saved and visually inspected a 1440×900 PNG at `/tmp/proposal-studio-verified.png`.
- Invalid URL — failed with a clear validation error and exit code 1.
- Loopback URL — rejected as non-public with exit code 1.
- Public redirect to `127.0.0.1` — proxy rejected the redirected request with HTTP 403; the CLI exited 1 rather than saving an image.
- Firefox walkthrough (previous version) — opened the sample route; found and fixed the prototype route to use `index.html`; confirmed the comparison image, slider drag, keyboard adjustment, Explore mode, and 320×480 responsive emulation without visible horizontal overflow.
- No automated test suite was added or run.

### Follow-up verification for D-002

- `npm run format:check` — passed.
- `npm run build` — passed: Astro check reported 13 files with no errors, warnings, or hints; ESLint and static route generation passed.
- Manual Chromium walkthrough — clicked the prototype's visible navigation while comparison remained visible; dragged the divider from 50% to 68%; keyboard-adjusted it to 67%. The prototype remained loaded behind the divider.
- Captured and visually inspected `/tmp/proposal-studio-interactive-comparison.png` at 1440×1100.
- Owner feedback said the screen still looked the same; expanded the comparison to the full viewport width and compacted the intro so the comparison appears much earlier.
- Follow-up Chromium walkthrough after the visual revision — dragged the divider across the iframe from 50% to 68%, used the keyboard to reach 67%, clicked the proposed-site navigation, and confirmed a 320px viewport has no horizontal overflow.
- Captured and visually inspected `/tmp/proposal-studio-fullwidth-comparison.png` at 1440×900.

## Rulings

- D-001 — The “current” side is a screenshot, not a generated HTML/CSS reconstruction. This keeps the prospect's existing side faithful and the workflow simple.
- D-002 — Keep the prototype interactive on its side of the divider; remove the separate Explore mode. The owner clarified this preference after reviewing the first version.
- The capture proxy pins each DNS resolution at connection time so the browser cannot perform a second, unvalidated lookup; unresolved DNS work is cancelled at its deadline.
- “CREATIVE TECHNOLOGY” is provisional English studio branding, reflecting the owner's stated preference; the proposal interface and actions remain in Spanish.

## Needs your eyes

- Review `scripts/safe-proxy.mjs` before relying on arbitrary URLs; it is the network security boundary for local website capture.
- Review the prospect data in `src/data/proposals/` before publishing a real proposal, especially contact links and pricing.

## Proposals

1. If “small clone” means an interactive reconstruction of the old website, define it as a separate requirement. This MVP captures the current site as a visual PNG and uses the actual new prototype for interaction.
2. Configure a domain and publish the static site after David chooses the domain and hosting setup.

## Pending

- No implementation tasks remain in REQ-001. Domain setup, public deployment, and the first real prospect are deferred.

## Walkthrough

1. Copy `src/data/proposals/clinica-horizonte.ts` to a new slug and add the record to `src/data/proposals/index.ts`.
2. Run `npm run capture` with the prospect's public website URL and save the PNG under `public/proposals/<slug>/`.
3. Set the capture path, current-site URL, prototype URL, offer details, and contact URL in the proposal record.
4. Run `npm run dev` and review `/<slug>/`; the public build includes the same route.
5. The current PNG is the base and the proposed iframe is clipped by the divider; the prototype remains interactive on its visible side.
6. The separate prototype link remains available if embedding is blocked.
7. If the site blocks automation or returns a recognized anti-bot challenge, use a manual screenshot. The old site is not cloned into functional HTML.
