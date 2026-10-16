# escritorio — Decision log

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

## D-001 — Keep launcher power controls on existing user wrappers
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** The Super launcher needed local profile, screen, idle-timeout and suspend controls without changing the existing remote-display and thermal policy.
- **Decision:** Add a Rofi Energy mode that calls `perfil` and `remote-screen-off/on`, stores timeout-disabled state and owned suspend-unit names in XDG state, and only restarts Hypridle after an explicit timeout selection.
- **Alternatives:** Duplicate low-level power/display commands — rejected because it could bypass existing lid, stream and profile handling.
- **Consequences:** + one consistent user entry point and safe targeted cancellation / − dashboard metrics are sampled only when Rofi opens.
- **Source:** [2026-10-12](../2026-10/W3/2026-10-12.md) · REQ-002

## D-002 — Keep Google Drive OAuth in Testing until real production URLs exist
- **Date:** 2026-10-16 · **Status:** Superseded by D-003
- **Context:** Google Cloud refused to publish the personal Drive OAuth app to Production without valid public homepage and privacy-policy URLs on a verified domain. The user requested completing the local installation.
- **Decision:** Complete OAuth in External/Testing with `david.theran03@gmail.com` as the only test user. Do not invent or publish policy pages. Move to Production only when genuine public URLs on a domain David controls are available.
- **Alternatives:** Leave the MCP unauthenticated — rejected because it would not access Drive; fabricate URLs or publish a site without a real owner-approved domain — rejected because the policy must be genuine and publicly accessible.
- **Consequences:** + MCP works immediately for the requested local clients / − Google expires Testing refresh tokens after seven days, so reauthorization is needed until Production is configured.
- **Source:** [2026-10-16](2026-10/W3/2026-10-16.md) · REQ-004

## D-003 — Publish genuine OAuth information pages and pursue free DNS verification
- **Date:** 2026-10-16 · **Status:** Accepted
- **Context:** David asked to try moving the personal Google Drive OAuth app to Production using a free site/domain provider. Google requires the app homepage and privacy policy to use a domain whose DNS ownership is verified; a Vercel-provided hostname does not establish that ownership.
- **Decision:** Host the genuine bilingual homepage and privacy policy as static pages on Vercel, keep the MCP itself on loopback, and evaluate a free DNS-controlled subdomain for Search Console verification and Vercel custom-domain routing. Do not mark OAuth Production-ready until Google verifies the DNS domain and the public URLs use that domain. Pause before connecting an external DNS account when its sign-in would disclose profile data.
- **Alternatives:** Use only the free `vercel.app` URL — rejected because it does not demonstrate David's domain ownership; buy a custom domain — not chosen because David asked for a free option; publish the MCP endpoint — rejected because it would expose a local service and is outside this task.
- **Consequences:** + real, accessible policy pages are ready; − free DNS subdomains may be rejected by Google, and provider account authorization is still required.
- **Source:** [2026-10-16](2026-10/W3/2026-10-16.md) · REQ-004
