---
id: REQ-001
status: in-progress
created: 2026-10-10
track: deep
---
# REQ-001 — Prospect proposal comparison tool

## Problem & goal
David needs a lightweight way to share personalized redesign proposals with business prospects. A side-by-side explanation is less persuasive than letting prospects compare the current public website with a working prototype.

**Success looks like:** David can prepare a proposal with a public website URL and a prototype URL, generate the current-site capture, and share a public page where a prospect can compare both while viewing and interacting with the proposed site as a normal webpage.

## Users / actors / stakeholders
- David creates proposal pages and supplies the prototype.
- A prospect visits a public proposal link without signing in.

## Scope (in)
### US-1 (P1, Must) — Prepare proposal content
As David, I want to define each proposal in a small data file so that I can reuse one page design across prospects without building a CRM.
**Acceptance:** A valid proposal record renders at a stable public slug; invalid or missing content does not render a misleading proposal.

### US-2 (P1, Must) — Capture current website
As David, I want a local command to capture the first viewport of a public website so that the current-state image is easy to add to a proposal.
**Acceptance:** Given a public HTTP(S) URL, when I run the capture command, it writes an image at the requested proposal asset path; invalid URLs and navigation failures produce a clear nonzero error.

### US-3 (P1, Must) — Compare current and proposed designs
As a prospect, I want to drag a divider across the current-site capture and a navigable prototype so that I can understand the redesign quickly.
**Acceptance:** The screenshot is the base layer and the live prototype iframe is clipped above it by the draggable divider. The proposed side receives pointer input so its links and controls work while the divider remains in place. The Spanish UI labels the views “Web actual” and “Propuesta”, keeps both aligned in one viewport, and dragging reveals more of either side.

### US-4 (P1, Must) — Interact with the proposed design
As a prospect, I want to use the proposed website while comparing it so that I can inspect its links and interactions without switching views.
**Acceptance:** Visible controls in the clipped prototype work while the comparison stays on screen; only the divider handle captures pointer input for dragging. A persistent “Open prototype in new tab” link remains available because cross-origin iframe failures cannot be detected reliably.

### US-5 (P1, Must) — Share a proposal
As David, I want a public, stable link per prospect so that I can send the proposal without requiring an account or signature.
**Acceptance:** Each configured slug is publicly addressable in the static build and has no login requirement.

### US-6 (P2, Should) — Explain the proposal and contact
As a prospect, I want concise findings, project scope, estimated timeline, indicative price, optional video, and a contact action so that I know what is offered and how to respond.
**Acceptance:** Configured sections render with the prospect’s name and a working WhatsApp/contact link; optional video content can be omitted.

## Out of scope
- CRM, proposal editor/admin panel, database, account management, e-signatures, payment collection, outreach automation, or follow-up tracking.
- Recording or hosting personalized videos; the proposal may link to an externally hosted video.
- Reconstructing the current site as HTML/CSS or copying its assets. The “Current” state is a generated screenshot.
- Automatically deploying a prospect’s prototype. David provides an already-hosted prototype URL.
- Buying or configuring a custom domain or publishing/deploying to a Cloudflare account in this requirement.

## Requirements
- R1. When a proposal config has a unique slug and valid required fields, the build shall generate a public page at that slug.
- R2. When David runs the local capture command with a public HTTP(S) URL, the tool shall save a viewport screenshot with predictable dimensions and a clear output path.
- R3. When the capture URL is invalid, resolves to a local/private destination, redirects to a blocked destination, or fails to load, the capture command shall fail clearly without writing a false-success image. Public HTTP and HTTPS sites are accepted.
- R4. When a visitor opens a proposal, the page shall show a draggable before/after comparison using the stored capture and configured prototype URL; content on the proposed side shall remain interactive while the divider is in place.
- R5. The comparison divider shall capture drag input only in its narrow handle area, leaving visible prototype content available to click, tap, and scroll.
- R6. The proposal page shall always provide a direct link to open the configured prototype in a new tab; it shall not depend on detecting cross-origin iframe failures.
- R7. When optional proposal fields (video, price, timeline, findings) are absent, the page shall omit those sections cleanly.
- R8. When a proposal page is shared, it shall not expose private management controls or require a prospect account.
- R9. The comparison divider shall support keyboard adjustment, and the comparison shall fit narrow screens without horizontal page overflow.

## Edge cases & errors
- The target site denies automated browsing, times out, redirects to a blocked destination, or renders a challenge page; report failure and allow David to supply a screenshot manually. Public HTTP-only sites may be captured, but HTTPS is preferred.
- The prototype URL blocks iframe embedding or is offline; keep the always-visible fallback link to open it in a new tab.
- Unknown slug, malformed configuration, or missing screenshot; render a deliberate not-found/error state rather than blank content.
- Long business names and copy, small mobile viewport, keyboard-only slider use, and reduced-motion preference.
- Capture must reject localhost/private network targets and validate redirects to reduce SSRF exposure.

## Constraints
- New standalone workspace at `~/dev/proposal-studio` (assumption pending correction).
- Use a static-first TypeScript site (Astro recommended) suitable for Cloudflare Pages; initial URLs can use the host’s free subdomain.
- Proposal-specific data stays in versioned local files; no database or secrets are needed for public rendering.
- Website capture runs locally with a headless browser so server-side Cloudflare credentials are not exposed or required.
- The prototype is hosted separately and must permit iframe embedding; provide a new-tab fallback.
- Keep costs and setup low; no paid SaaS dependency for the MVP.

## Priorities & phases
- MVP: proposal template, per-prospect config, local website screenshot capture, interactive comparison slider, responsive public routes, Cloudflare Pages build output.
- Later: capture from an in-app admin UI, multiple viewport captures, password-protected draft previews, custom domain, analytics.

## Timeline & dependencies
- No deadline given. The first usable local MVP is the goal.
- Requires Node.js/npm and a locally installed Playwright browser for capture; prototype URLs need to be publicly reachable and embeddable.

## Assumptions
- Use a dedicated project folder at `~/dev/proposal-studio`; the user has not selected a different existing repo.
- Keep the initial wordmark in English as provisional studio branding, based on the owner's preference for an English technology-focused brand; product controls and copy are in Spanish.
- Capture the public website’s first viewport (desktop default) rather than crawling/rebuilding the full site; public HTTP and HTTPS are accepted, with HTTPS preferred; manual screenshot fallback handles blocked sites.
- Proposal records are edited as JSON/TypeScript data and each update is deployed through the static site build; an admin UI is deferred to avoid backend/auth scope.
- The proposal template includes editable findings, deliverables, timeline, optional estimated price, optional external video, and WhatsApp CTA, based on the previously discussed proposal structure.
- Initial deployment is not performed as part of implementation; Cloudflare Pages configuration/build compatibility is included, and deployment requires a separate explicit go-ahead.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear (assumptions listed) |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear (capture failure fallback) |
| Acceptance criteria | Clear |
| Constraints | Clear (project path assumed) |
| Priorities & phases | Clear |
| Timeline | Clear (no deadline) |

## Clarifications
- Q: Compare the old public website with a screenshot or a generated HTML clone? → A: Use automatic screenshot capture.
- Q: Should the proposed side remain navigable? → A: Yes, use the actual hosted prototype.
- Q: Which hosting/domain for the first version? → A: No custom domain yet; prepare for a free public host subdomain, with Cloudflare Pages assumed.
- Q: How does the live prototype behave in comparison mode and when is it interactive? → A: Earlier preference was to use a non-interactive comparison and separate Explore mode; superseded by the updated clarification below.
- Q: Should the prototype be presented in a separate Explore mode? → A: No; show it as a normal webpage on its side of the divider and keep it interactive while comparing. This supersedes the earlier Explore-mode preference.
- Q: What if the prototype cannot be embedded? → A: Keep an always-visible link to open it separately; do not rely on detecting cross-origin failures.
- Q: Are HTTP-only public sites supported for capture? → A: Yes; the capture tool accepts public HTTP and HTTPS URLs, preferring HTTPS.
