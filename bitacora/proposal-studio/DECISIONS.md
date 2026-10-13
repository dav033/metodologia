# proposal-studio — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Compare a captured current site with a live prototype
- **Date:** 2026-10-10 · **Status:** Superseded by D-002
- **Context:** Prospects need to understand the redesign proposal quickly and be able to try it.
- **Decision:** Capture the first viewport of the prospect’s public website locally, then compare that image with the user-hosted prototype through a draggable divider. The prototype becomes interactive in a separate Explore mode.
- **Alternatives:** Rebuild the current site in HTML/CSS — unnecessary for a visual before/after comparison and adds brittle duplicated markup; screenshot upload only — does not automate the chosen flow.
- **Consequences:** + Simple static proposal pages and no public browser-service secret; − capture command requires a local Playwright browser and some blocked sites need a manual screenshot.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-001.

## D-002 — Keep the prototype interactive beside the divider
- **Date:** 2026-10-10 · **Status:** Accepted
- **Supersedes:** D-001's separate Explore mode interaction.
- **Context:** The first version required prospects to leave the comparison to explore the new design.
- **Decision:** Show the supplied prototype as a normal webpage on its side of the divider and keep visible elements interactive while comparing.
- **Alternatives:** Separate Explore mode — adds a step and removes the visual comparison during interaction.
- **Consequences:** + Prospect can inspect the proposed site without losing the comparison; − only the divider handle can be used to drag so prototype controls remain clickable.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-001.

## D-003 — Use Vercel-hosted Astro SSR for the managed studio
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** REQ-003 adds authenticated administration, persistent data, private assets, GitHub import, temporary share links, and email. David authorized using his existing Vercel, GitHub, and Google Cloud accounts.
- **Decision:** Keep Astro and use its Vercel server adapter; use Neon Postgres through Vercel Marketplace, private Vercel Blob, Better Auth with Google OAuth, a read-only GitHub App, and Resend with a Postgres outbox/idempotency key. Use a Vercel subdomain until David owns a custom domain.
- **Alternatives:** Cloudflare Workers/D1/R2 — technically viable but introduces another provider not named in the current account authorization; Next.js rewrite — unnecessary since Astro has supported SSR on Vercel.
- **Consequences:** + Reuses the current framework and user's authenticated hosting account; + supports relational revision/outbox data and private assets; − Neon/Blob marketplace resources and OAuth/GitHub app setup are external configuration; − real prospect email requires a verified sender domain.
- **Rollback:** Export Postgres data and Blob manifest/files, then restore static Astro output if the managed app is abandoned; no destructive static-page migration is needed.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-003.

## D-004 — Keep the Vercel hostname public and authorize administration in the app
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** Prospects must open expiring share links without owning a Vercel account; the Vercel project initially applied authentication to the whole deployment.
- **Decision:** Disable Vercel SSO deployment protection for this project. Keep `/admin` and `/api/admin` gated by the application’s Better Auth owner allowlist; private assets continue to require an active share-link cookie.
- **Alternatives:** Keep platform protection — prospects cannot open links; publish an auth-bypass token — leaks a platform credential and is unsafe.
- **Consequences:** + Generated `vercel.app` links work for prospects; − every public route relies on application authorization, which must remain fail-closed and tested.
- **Rollback:** Re-enable SSO protection with `vercel project protection enable proposal-studio --sso --scope dav033s-projects`; this will block prospect access until a custom domain is added.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-003.

## D-005 — Enforce sensitive admin request limits in Postgres
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** REQ-003 R5 requires throttling share creation and provider-backed administrative requests. Vercel Functions are stateless and may handle requests in separate instances, so a process-local counter cannot enforce a shared limit.
- **Decision:** After the admin allowlist check, the Astro middleware applies per-owner, per-operation windows using an atomic Postgres upsert. Sensitive routes have explicit limits; a database failure returns 503 (fail closed), and an exceeded window returns 429 with `Retry-After`.
- **Alternatives:** In-memory counters — not shared across instances; introduce Redis/KV — adds a provider and operational setup for one admin; throttle every admin request — would interfere with ordinary low-volume editing.
- **Consequences:** + Counters are atomic across app instances and provider calls are bounded; − adds one small table and a database write on each protected sensitive route.
- **Rollback:** Revert the middleware policy and limiter module; the additive `admin_rate_limit_bucket` table can remain unused or be dropped manually after confirming it holds no needed data.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-003 R5.

## D-006 — Use Starwind UI with a scoped 21st.dev React island
- **Date:** 2026-10-11 · **Status:** Accepted
- **Context:** Public proposals and the admin overview needed a coherent component system and restrained motion while the app remains Astro SSR.
- **Decision:** Use editable Starwind UI Button/Card/Badge components with the existing CSS tokens; add one React island for the MIT-licensed 21st.dev Spotlight treatment on proposal findings, and use Motion `inView` for short entry reveals. Respect reduced-motion preferences and keep content server-rendered.
- **Alternatives:** Web Awesome — rejected because Astro-native source components fit the existing rendering model and avoid custom-element hydration for shared UI; React throughout — unnecessary hydration and a framework rewrite; install all library components — adds unused code.
- **Consequences:** + Consistent public/admin styling with a small interactive island; + reduced motion and no-JS keep content usable; − Tailwind v4 build tooling is added for Starwind component source while the existing CSS remains in place.
- **Rollback:** Remove the Starwind source components and Tailwind integration, restore the previous proposal/admin markup and CSS, then remove the Spotlight island and Motion reveal script with their dependencies. No database or public API migration is involved.
- **Source:** [day log](2026-10/W2/2026-10-11.md) · REQ-004.

## D-007 — Render the draft preview through the shared proposal component
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** The owner could not see what a recipient sees without publishing and creating a share link.
- **Decision:** Extract the proposal body into `ProposalView.astro`, used by `/s/[token]` and an admin-only draft preview with device simulation.
- **Alternatives:** Separate copy of the markup for the editor — rejected, it would diverge; side panel only — less faithful.
- **Consequences:** + Preview equals the real page; − the frame shows the draft while the client sees the published revision (stated in the UI).
- **Rollback:** Revert ProposalView extraction and delete the preview routes; no data migration.
- **Source:** [day log](2026-10/W3/2026-10-13.md).

## D-008 — Adopt the Consola visual direction for the app UI
- **Date:** 2026-10-13 · **Status:** Accepted (owner choice)
- **Context:** The owner found the current design poor and was shown three directions (A Mocha ordenado, B Estudio claro, C Consola) on the same editor screen.
- **Decision:** Use C · Consola: graphite background, amber accent `#ffb224`, Geist and Geist Mono, dense tool-like layouts with a top tab bar.
- **Alternatives:** A keeps the desktop's Catppuccin identity at lower cost; B is lighter and more product-like but breaks the owner's aesthetic.
- **Consequences:** + distinct, fast-feeling tool; − departs from the Catppuccin rule in the owner's global instructions, so it applies to this product only; − less friendly for non-technical viewers on the admin side.
- **Rollback:** keep the design tokens centralized so A or B can replace them; no data changes.
- **Source:** [day log](2026-10/W3/2026-10-13.md); canvas https://claude.ai/artifact/B9GwtvtHwFSNioDxCVvZ79.
