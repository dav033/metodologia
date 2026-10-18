# dav033-demos — Decision log

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

## D-001 — Parent owns private delivery and access
- **Date:** 2026-10-18 · **Status:** Accepted
- **Context:** Owner needs expiring sales demos without modifying child projects or leaving public child URLs accessible.
- **Decision:** Next.js parent imports static builds through GitHub Actions, stores artifacts privately and checks signed per-demo bearer tokens, enabled state and expiry on every viewer/asset request. Opaque iframe owns device previews. Single owner uses server-side GitHub credentials.
- **Alternatives:** Public child deployments with a visual wrapper permit direct access and do not enforce expiry. Multi-user OAuth is outside this single-owner MVP.
- **Consequences:** Rotation invalidates shared links; pause and expiry block new requests. Downloaded content cannot be erased. Static exports must honor their base path.
- **Source:** [day log](2026-10/W3/2026-10-18.md) · REQ-001; owner approval in chat.
