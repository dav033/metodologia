---
req: REQ-002
status: superseded
created: 2026-10-10
---
# Plan — REQ-002 — Local proposal authoring workflow

> Superseded by REQ-003. Do not implement this local-only architecture.

## Approach
Turn the current code-edited sample into a local-only authoring tool backed by project files. David creates/edits a prospect record, captures its public site, places the generated prototype under that prospect's folder, and reviews the result locally. Astro remains responsible for static public output; no admin API or filesystem access ships in `dist/`. No CRM, database, domain, or deployment flow is introduced.

## Global constraints
- Bind every authoring endpoint to loopback and keep it out of production/static output.
- Persist each record as JSON and validate external input as `unknown` before writing or rendering.
- Keep the public capture on the existing DNS-pinning/SSRF-protected CLI path.
- Confine prototype and screenshot paths to that proposal's own directory; reject traversal and missing entry files.
- Keep the draggable comparison interactive and static export compatible with Cloudflare Pages.
- Do not deploy, buy/configure a domain, commit, push, or add CRM features.

## Tasks
- [ ] T1 — Define the local authoring server boundary, persisted JSON schema, and source-folder layout; migrate the fictional example without changing its public route · files: `src/data/proposals/`, `src/types/`, `scripts/`, `docs/` or brain ADR · verify: `npm run build` · covers: R1, R2, R3, US-1
- [ ] T2 — Build the local proposal dashboard to list, create, edit, validate, and preview proposal records · after: T1 · verify: manual authoring walkthrough · covers: R1, R2, R3, R8, US-1, US-5
- [ ] T3 — Integrate safe site capture into the authoring flow with clear in-progress/success/failure states · after: T2 · verify: public URL succeeds; invalid/private URL fails without an image · covers: R4, US-2
- [ ] T4 — Associate a proposal with its static prototype folder and verify entry/assets stay within that proposal · after: T1 · verify: local nested-asset/link walkthrough and negative path checks · covers: R3, R5, US-3
- [ ] T5 — Generate local preview and static public output with no authoring controls; document the real authoring workflow · after: T2, T3, T4 · verify: `npm run format:check`, `npm run build`, manual responsive comparison walkthrough · covers: R6, R7, R8, US-4, US-5

## Verification
Create a fresh proposal using only the local authoring UI and one prototype folder; capture a public sample website; verify incomplete/duplicate data is rejected; inspect that capture failures produce no asset; interact with the prototype while dragging/keyboard-adjusting the divider; run the static build and inspect that the public output contains the proposal and prototype but no Studio route/API; verify narrow viewport behavior. No cloud deployment is part of this plan.

## Rulings
- Proposed MVP uses per-proposal JSON plus `public/prototypes/<slug>/` so the owner's code stays ordinary static web code and the shareable output needs no runtime server — pending approval; cost if wrong: medium.
- Proposed Studio API runs as a separate loopback-only process beside Astro dev so filesystem operations cannot leak into the static public site — pending architecture review; cost if wrong: medium.

## Progress log
- 2026-10-10 — Drafted after owner clarified that the complaint was about the software solution itself, not the visual quality of the fictional prospect proposal. Waiting for scope/plan approval before implementation.
