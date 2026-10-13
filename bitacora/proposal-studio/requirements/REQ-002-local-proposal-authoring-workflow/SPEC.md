---
id: REQ-002
status: superseded
created: 2026-10-10
track: deep
---
# REQ-002 — Local proposal authoring workflow (superseded)

> Superseded by REQ-003 on 2026-10-10 after David expanded the product request to include hosted administration, OAuth, expiring share links, GitHub integration, and optional email notifications. This draft was never approved or implemented; retained for traceability.

## Problem & goal
REQ-001 produced a static example, but preparing a real prospect currently requires editing TypeScript source, running a separate capture command, and supplying an already hosted prototype URL. That does not yet give David a serious, repeatable tool for presenting prototypes he creates with code.

**Success looks like:** David can use a local authoring tool to prepare a proposal from a prospect's public website and his own prototype code, preview the working comparison, and generate a static proposal page ready for later hosting.

## Users / actors / stakeholders
- David authors proposals and supplies the coded prototype.
- Prospects view the generated public proposal page without signing in.

## Scope (in)
### US-1 (P1, Must) — Prepare a proposal without editing source code
As David, I want to enter proposal details in a local form so that preparing a prospect page does not require changing application code.
**Acceptance:** The local tool creates and edits proposal records stored as validated project files; each proposal has a unique slug and preview route.

### US-2 (P1, Must) — Capture the prospect's public website
As David, I want to enter a public website URL and capture its current appearance from the authoring flow.
**Acceptance:** The tool uses the existing hardened local capture boundary, saves the screenshot under the selected proposal, and reports actionable errors without false success.

### US-3 (P1, Must) — Show code-generated prototypes
As David, I want to place my built prototype in the project and associate its entry page with a proposal so that the tool can serve it as a normal webpage.
**Acceptance:** A prototype's HTML, styles, scripts, and local assets are available at a stable proposal-specific route and can be loaded by the comparison iframe.

### US-4 (P1, Must) — Preview and build shareable proposals
As David, I want to preview the proposal locally and generate static output so that I can review it before choosing hosting.
**Acceptance:** The proposal route displays the current-site capture and interactive prototype with the draggable divider; the production build emits the route and its prototype assets into `dist/`.

### US-5 (P2, Should) — Edit the offer and contact details
As David, I want to set findings, deliverables, timeline, optional price/video, and contact action for each prospect.
**Acceptance:** Configured values appear only in that proposal, optional fields are omitted when blank, and inputs are validated before saving/building.

## Out of scope
- CRM, lead pipeline, outreach, analytics, accounts, e-signatures, payment collection, and hosted database.
- Automatic deployment, domain purchase, and publishing to Cloudflare before David chooses the domain and hosting.
- Reconstructing the prospect's current website as HTML. The current side remains a screenshot.
- Generating the prototype code; David supplies it.
- Multi-user access or exposing the authoring interface publicly.

## Requirements
- R1. The authoring interface shall bind only to loopback and shall not be included in public static output.
- R2. Proposal records shall persist in project files and pass the same runtime/build validation before being saved or rendered.
- R3. Proposal slugs and prototype paths shall be unique, normalized, and confined to their proposal directories.
- R4. Website capture shall call the existing local capture flow and retain its public-address, redirect, deadline, and clear-error protections.
- R5. Prototype files shall be served below a stable proposal-specific path; the request shall not read outside the selected prototype directory.
- R6. The comparison shall show the saved current-site screenshot and the interactive prototype together, with working pointer and keyboard divider controls.
- R7. `npm run build` shall emit self-contained static proposal pages and supplied prototype files under `dist/`.
- R8. The public proposal page shall not contain authoring controls, local filesystem paths, or other private management data.

## Edge cases & errors
- Duplicate or malformed slugs; incomplete proposal data; failed screenshot capture.
- Missing prototype entry file, malformed asset path, or prototype asset outside its own directory.
- Prototype with nested routes or local asset references; preserve relative paths under its proposal route.
- Attempt to access authoring route/API through a non-loopback interface; fail closed.
- A prototype disallows iframe embedding or fails at runtime; retain the direct link and explain the issue in preview.
- Restart the local tool without losing saved proposal data.

## Constraints
- Continue using Astro and static output for public proposal pages.
- Keep the authoring utility local-only and file-backed; no CRM or hosted database.
- Reuse the existing capture CLI and SSRF-resistant proxy rather than creating a second network path.
- Validate all form/API inputs and prototype paths at runtime; the authoring server binds to `127.0.0.1` only.
- Do not publish or configure a domain in this requirement.

## Priorities & phases
- MVP: local proposal form, file-backed save/edit, current-site capture, code prototype placement/association, local preview, static build.
- Later: deploy action, custom domain, multiple viewport captures, protected preview links, analytics.

## Timeline & dependencies
- No deadline given. Requires the existing Node/npm environment, local Chromium for capture, and a prototype that builds to static HTML/CSS/JS/assets.

## Assumptions
- **Pending owner approval:** “Serious software implementation” means a local authoring workflow rather than manually editing TypeScript files or only polishing the sample proposal.
- **Pending owner approval:** Keep the website capture local and let David place prototype files inside the project; no arbitrary public URL upload or external source control import.
- **Pending owner approval:** Save records/assets in the repository and produce public static output, while leaving domain and deployment for a later step.
- Preserve the previously requested draggable comparison and keep the proposed side interactive.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Proposed; confirm authoring workflow |
| Users / actors | Clear |
| Scope | Proposed; confirm form and prototype input |
| Flows & behavior | Proposed |
| Edge cases | Clear for proposed file-backed local flow |
| Acceptance criteria | Proposed |
| Constraints | Proposed |
| Priorities & phases | Proposed |
| Timeline | No deadline given |

## Clarifications
- Waiting for David to confirm whether he wants a local form, where the prototype code lives, and whether this tool should only generate local/static output or also publish.
